"""
ComputeRegions.py

Usage example:
    python backend/ComputeRegions.py --db data/praticiens.db --regions data/regions.zip --metier n --out data/voronoi_clipped.gpkg


"""

import sqlite3
from typing import Optional, List, Tuple
import argparse
from matplotlib import pyplot as plt

# Try to import GIS/geometry libraries; if not installed, error messages will guide the user.
try:
    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import Point, Polygon, MultiPolygon
    from shapely.ops import unary_union
    import numpy as np
    from scipy.spatial import Voronoi
except Exception as e:
    raise ImportError(
        "Required libraries missing. Install with:\n"
        "    pip install pandas geopandas shapely scipy numpy\n"
        "or use conda:\n"
        "    conda install -c conda-forge geopandas scipy shapely numpy pandas\n\n"
        f"Original error: {e}"
    )


def read_praticiens_and_adresses(db_path: str, metier_ids: list) -> pd.DataFrame:
    """
    Connect to the sqlite db, find praticiens with any of the metier_ids, 
    then get their adresse coords.
    Returns a DataFrame with columns: praticien_id, adresse_id, latitude, longitude
    """
    if not metier_ids:
        raise ValueError("metier_ids list cannot be empty.")

    con = sqlite3.connect(db_path)
    try:
        # fetch praticien ids and adresse_ids
        placeholders = ','.join(['?']*len(metier_ids))
        q = f"SELECT rpps AS praticien_id, adresse_id FROM Praticien WHERE metier_id IN ({placeholders})"
        praticien_df = pd.read_sql_query(q, con, params=metier_ids)
        
        if praticien_df.empty:
            raise ValueError(f"No praticien found for metier_ids={metier_ids}")

        # make sure adresse_id list is unique and not null
        adresse_ids = praticien_df['adresse_id'].dropna().unique().tolist()
        if not adresse_ids:
            raise ValueError("No adresse_id values found for selected praticiens.")

        # fetch addresses
        q2 = f"SELECT adresse_id AS adresse_id, latitude, longitude FROM adresse WHERE adresse_id IN ({','.join(['?']*len(adresse_ids))})"
        adresse_df = pd.read_sql_query(q2, con, params=adresse_ids)

        if adresse_df.empty:
            raise ValueError("No adresse rows found for the adresse_ids retrieved.")

        # merge so each praticien has lat/lon
        merged = praticien_df.merge(adresse_df, on='adresse_id', how='left')
        # drop praticiens without coordinates
        merged = merged.dropna(subset=['latitude', 'longitude'])
        if merged.empty:
            raise ValueError("All matched praticiens are missing latitude/longitude.")

        # ensure numeric
        merged['latitude'] = pd.to_numeric(merged['latitude'], errors='coerce')
        merged['longitude'] = pd.to_numeric(merged['longitude'], errors='coerce')
        merged = merged.dropna(subset=['latitude', 'longitude'])

        return merged[['praticien_id', 'adresse_id', 'latitude', 'longitude']]

    finally:
        con.close()


def voronoi_finite_polygons_2d(vor: Voronoi, radius: float = 1e6) -> Tuple[List[np.ndarray], np.ndarray]:
    """
    Reconstruct finite Voronoi polygons for 2D Voronoi computed by scipy.spatial.Voronoi.
    Returns (polygons as list of coordinate arrays, region indices for each input point).
    The 'radius' parameter is used to cap infinite regions (must be large enough for projected CRS).
    Code adapted from common solutions for finite Voronoi polygons.
    """
    # Based on https://stackoverflow.com/a/20678647/ and other common snippets
    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    # use a large bounding box radius (in same units as points)
    if radius is None:
        radius = max(vor.points.ptp(axis=0)) * 100  # fallback

    all_ridges = {}
    # map each point to its ridges
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    for p_idx, region_index in enumerate(vor.point_region):
        vertices = vor.regions[region_index]
        if -1 not in vertices:
            # finite region
            new_regions.append(np.asarray([vor.vertices[v] for v in vertices]))
            continue

        # reconstruct a non-finite region
        ridges = all_ridges[p_idx]
        pts = []
        for p2, v1, v2 in ridges:
            if v2 < 0 or v1 < 0:
                v = v1 if v1 >= 0 else v2
                t = vor.points[p2] - vor.points[p_idx]  # tangent
                t = t / np.linalg.norm(t)
                # normal
                n = np.array([-t[1], t[0]])
                # midpoint between points
                midpoint = vor.points[[p_idx, p2]].mean(axis=0)
                # direction: sign of dot product with (midpoint - center)
                direction = np.sign(np.dot(midpoint - center, n))
                far_point = vor.vertices[v] + direction * n * radius
                new_vertices.append(far_point.tolist())
                pts.append(v)
                pts.append(len(new_vertices) - 1)
            else:
                pts.append(v1)
                pts.append(v2)
        # take unique vertex indices in order (simple approach)
        uniq = []
        for v in pts:
            if v not in uniq:
                uniq.append(v)
        poly = np.asarray([new_vertices[v] for v in uniq])
        new_regions.append(poly)

    return new_regions, np.asarray(new_vertices)


def build_voronoi_gdf(points_gdf: gpd.GeoDataFrame, clip_extent_geom: Optional[Polygon] = None, buffer: float = 10000.0) -> gpd.GeoDataFrame:
    """
    Given a GeoDataFrame of points (projected CRS), compute Voronoi polygons and return a GeoDataFrame
    with one polygon per input point. If clip_extent_geom is provided (a shapely Polygon or MultiPolygon),
    Voronoi polygons will be intersected with a bounding polygon that is clip_extent_geom buffered by `buffer`.
    """

    if points_gdf.empty:
        raise ValueError("points_gdf is empty")

    # extract coordinates in numpy array
    coords = np.array([[geom.x, geom.y] for geom in points_gdf.geometry])
    if coords.shape[0] < 2:
        raise ValueError("At least two distinct points are required to build a Voronoi diagram.")

    # Build bounding mask: bounding box of clip_extent_geom (or points) with buffer
    if clip_extent_geom is not None:
        bbox = clip_extent_geom.bounds  # (minx, miny, maxx, maxy)
        minx, miny, maxx, maxy = bbox
    else:
        minx, miny = coords.min(axis=0) - buffer
        maxx, maxy = coords.max(axis=0) + buffer

    # Use a radius large enough to cap infinite regions — here chosen from bbox size
    diag = np.hypot(maxx - minx, maxy - miny)
    radius = diag * 10.0

    vor = Voronoi(coords)
    regions, vertices = voronoi_finite_polygons_2d(vor, radius=radius)

    polys = []
    for region in regions:
        try:
            poly = Polygon(region)
            if not poly.is_valid:
                poly = poly.buffer(0)
            polys.append(poly)
        except Exception:
            # fallback: try to create polygon from convex hull of region points
            poly = Polygon(np.array(region).convex_hull) if len(region) > 2 else None
            polys.append(poly)

    vor_gdf = gpd.GeoDataFrame(
        points_gdf.reset_index(drop=True)[['praticien_id', 'adresse_id']].copy(),
        geometry=polys,
        crs=points_gdf.crs
    )

    # Clip to extent geometry if provided
    if clip_extent_geom is not None:
        # buffer to ensure coverage for infinite regions
        clip_buffered = clip_extent_geom.buffer(buffer)
        # intersection for each polygon
        vor_gdf['geometry'] = vor_gdf.geometry.intersection(clip_buffered)
        # drop empty geometries
        vor_gdf = vor_gdf[~vor_gdf.is_empty].copy()
        vor_gdf = vor_gdf[vor_gdf.geometry.notna()]

    return vor_gdf


def clip_voronoi_to_regions(voronoi_gdf: gpd.GeoDataFrame, regions_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Intersect the voronoi polygons with the regions layer.
    Returns a GeoDataFrame with geometry = intersection and attributes from voronoi_gdf (praticien_id, adresse_id)
    plus optionally region attributes (keeps region index under 'region_index' if present).
    """

    # Ensure both are in same CRS
    if voronoi_gdf.crs != regions_gdf.crs:
        regions_gdf = regions_gdf.to_crs(voronoi_gdf.crs)

    # Option 1: overlay intersection (will create one row per voronoi-region intersection).
    result = gpd.overlay(voronoi_gdf, regions_gdf, how='intersection')

    # Keep praticien_id as main identifier; optionally drop columns from regions if you want less clutter
    return result


def generate_voronoi_clipped(
    db_path: str,
    metier_id: int,
    regions_zip: str,
    output_path: str,
    image_path: str = "data/voronoi_plot.png",
    points_crs: str = "EPSG:4326",
    voronoi_buffer: float = 10000.0,
    dissolve_regions: bool = False
) -> gpd.GeoDataFrame:
    """
    Full pipeline: read DB, make points GeoDataFrame, build Voronoi, clip to regions, save result.
    Returns the clipped GeoDataFrame (but also writes to disk).
    """
    # 1) read praticien + adresse
    df = read_praticiens_and_adresses(db_path, metier_id)

    # 2) create points GeoDataFrame (assume adresse longitude, latitude)
    # If your DB saved lat/lon in other order, swap accordingly
    pts = gpd.GeoDataFrame(
        df[['praticien_id', 'adresse_id']].copy(),
        geometry=[Point(xy) for xy in zip(df['longitude'].astype(float), df['latitude'].astype(float))],
        crs=points_crs
    )

    # 3) read regions shapefile (zip)
    regions = gpd.read_file(f"zip://{regions_zip}")

    # 4) project points to regions CRS (so Voronoi computed in same linear units)
    if regions.crs is None:
        raise ValueError("Regions shapefile has no CRS. Set a CRS on the shapefile or pass points_crs matching it.")
    pts = pts.to_crs(regions.crs)

    # Remove duplicate coordinates (critical!)
    pts = pts.drop_duplicates(subset=['geometry'])

    # Ensure at least 3 non-colinear points
    if len(pts) < 3:
        raise ValueError(
            f"Voronoi requires at least 3 unique non-colinear points. "
            f"Only {len(pts)} unique points after deduplication."
        )

    # 5) build a unified geometry to use as clipping extent (could also use regions.unary_union)
    unified_regions = unary_union(regions.geometry)

    voronoi_gdf = build_voronoi_gdf(pts, clip_extent_geom=unified_regions, buffer=voronoi_buffer)

    # 6) clip voronoi onto regions (gets intersections per region)
    clipped = clip_voronoi_to_regions(voronoi_gdf, regions)

    # Optionally dissolve by praticien_id so each praticien has a single geometry (if intersections split across multiple region polygons)
    if dissolve_regions:
        clipped = (clipped.dissolve(by='praticien_id', as_index=False)[['praticien_id', 'geometry']])
        # reattach adresse_id if needed (this may require aggregating — here we keep the first)
        # NOTE: if multiple adresse_id per praticien, adjust accordingly

    # 7) save
    if output_path.lower().endswith('.gpkg'):
        clipped.to_file(output_path, layer='voronoi_clipped', driver='GPKG')
    elif output_path.lower().endswith('.shp'):
        clipped.to_file(output_path)
    else:
        # default to geopackage
        clipped.to_file(output_path, layer='voronoi_clipped', driver='GPKG')

    # --- PLOTTING INSTEAD OF SAVING GPKG ---
    plot_voronoi_result(regions, voronoi_gdf, clipped, output_image=image_path)

    return clipped


def plot_voronoi_result(regions_gdf, voronoi_gdf, clipped_gdf, output_image=None):
    """
    Plot regions, voronoi cells and clipped results.
    Saves to output_image if provided.
    """
    fig, ax = plt.subplots(figsize=(100, 100))

    # Base layer: regions
    regions_gdf.boundary.plot(ax=ax, color="black", linewidth=1.0, alpha=0.7)
    regions_gdf.plot(ax=ax, color="white", edgecolor="black", alpha=0.3)

    # Voronoi polygons (before clipping)
    voronoi_gdf.plot(ax=ax, facecolor="none", edgecolor="blue", linewidth=1.0, alpha=0.8)

    # Clipped Voronoi (final desired shapes)
    clipped_gdf.plot(ax=ax, cmap="tab20", alpha=0.65, edgecolor="black", linewidth=1.0)

    # Practitioner points
    pts = voronoi_gdf.copy()
    pts["geometry"] = pts.geometry.centroid
    pts.plot(ax=ax, color="red", markersize=0.1, label="Praticiens")

    ax.set_title("Voronoi Regions Clipped to Map", fontsize=16)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend()

    plt.tight_layout()

    if output_image is not None:
        plt.savefig(output_image, dpi=300)
        print(f"Saved plot to: {output_image}")

    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Voronoi for praticiens of a given metier and clip to regions shapefile (zip).")
    parser.add_argument("--db", required=True, help="Path to sqlite database (e.g., database.db)")
    parser.add_argument("--regions", required=True, help="Path to zipped shapefile (e.g., regions.zip)")
    parser.add_argument("--metier", required=True, type=int,nargs="+", help="metier_id to filter praticiens")
    parser.add_argument("--out", required=False, default="voronoi_clipped.gpkg", help="Output path (.gpkg or .shp recommended)")
    parser.add_argument("--buffer", required=False, type=float, default=10000.0, help="Buffer distance (same units as regions CRS) used when capping infinite Voronoi faces")
    parser.add_argument("--dissolve", action='store_true', help="Dissolve intersections so result has one geometry per praticien_id")
    args = parser.parse_args()

    clipped_gdf = generate_voronoi_clipped(
        db_path=args.db,
        metier_id=args.metier,
        regions_zip=args.regions,
        output_path=args.out,
        voronoi_buffer=args.buffer,
        dissolve_regions=args.dissolve
    )
    print(f"Wrote {len(clipped_gdf)} clipped Voronoi features to {args.out}")

    