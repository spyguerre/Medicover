import { NextResponse } from "next/server";
import { exec } from "child_process";
import util from "util";
import { constants } from "fs";
import { access } from "fs/promises";

const execPromise = util.promisify(exec);

export async function POST(req: Request) {
  try {
    const url = new URL(req.url);
    const professions = url.searchParams.get("professions")?.split(",") ?? [];

    async function fileExists(path: string): Promise<boolean> {
      try {
        await access(path, constants.F_OK);
        return true;   // File exists
      } catch {
        return false;  // File does NOT exist
      }
    }

    // Ensure map image doesn't already exist, if it's the case no need to generate it again
    if (await fileExists("public/generatedImages/" + professions.join(",") + ".png")) {
      return NextResponse.json({
        success: true,
      });
    }

    // Command to run
    const cmd = `. .venv/bin/activate && python3 backend/compute_regions.py --db data_extraction/GrandEst.db --regions data/regions.zip --metier `
    + professions.join(" ") +
    ` --out data/voronoi_clipped.gpkg && mkdir public/generatedImages && mv data/voronoi_plot.png public/generatedImages/` + professions.join(",") + `.png`;

    // Execute on server
    const { stdout, stderr } = await execPromise(cmd);

    return NextResponse.json({
      success: true,
      stdout,
      stderr
    });
  } catch (e: any) {
    return NextResponse.json(
      { success: false, error: e.message },
      { status: 500 }
    );
  }
}
