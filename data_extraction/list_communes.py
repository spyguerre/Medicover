#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour lister toutes les communes d'une région
Usage: python3 list_communes.py "Grand Est"
"""

import requests
import sys

# Codes région INSEE
REGIONS = {
    'Auvergne-Rhône-Alpes': '84',
    'Bourgogne-Franche-Comté': '27',
    'Bretagne': '53',
    'Centre-Val de Loire': '24',
    'Corse': '94',
    'Grand Est': '44',
    'Hauts-de-France': '32',
    'Île-de-France': '11',
    'Normandie': '28',
    'Nouvelle-Aquitaine': '75',
    'Occitanie': '76',
    'Pays de la Loire': '52',
    'Provence-Alpes-Côte d\'Azur': '93'
}


def list_communes_in_region(region_name: str):
    """
    Liste TOUTES les communes d'une région via l'API geo.api.gouv.fr
    """
    region_code = REGIONS.get(region_name)
    
    if not region_code:
        print(f"\n❌ Région '{region_name}' non reconnue")
        print(f"\n📋 Régions disponibles:")
        for r in sorted(REGIONS.keys()):
            print(f"   - {r}")
        return
    
    print(f"\n{'='*80}")
    print(f"🗺️  COMMUNES DE LA RÉGION: {region_name.upper()}")
    print(f"{'='*80}\n")
    print(f"🔍 Récupération des données via geo.api.gouv.fr...\n")
    
    try:
        # Étape 1 : Récupérer les départements de la région
        print(f"   1️⃣ Récupération des départements...")
        response_depts = requests.get(
            f"https://geo.api.gouv.fr/departements",
            params={'codeRegion': region_code},
            timeout=30
        )
        response_depts.raise_for_status()
        departements = response_depts.json()
        
        print(f"      ✅ {len(departements)} départements trouvés\n")
        
        # Étape 2 : Récupérer les communes de chaque département
        print(f"   2️⃣ Récupération des communes par département...")
        communes = []
        
        for i, dept in enumerate(departements, 1):
            dept_code = dept['code']
            dept_nom = dept['nom']
            print(f"      [{i}/{len(departements)}] {dept_nom} ({dept_code})...", end=' ')
            
            try:
                response = requests.get(
                    f"https://geo.api.gouv.fr/departements/{dept_code}/communes",
                    params={'fields': 'nom,code,codesPostaux,codeDepartement,population'},
                    timeout=30
                )
                response.raise_for_status()
                communes_dept = response.json()
                communes.extend(communes_dept)
                print(f"{len(communes_dept)} communes")
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        print(f"\n      ✅ Total: {len(communes)} communes récupérées\n")
        
        # Trier par population (les plus grandes en premier)
        communes_sorted = sorted(communes, key=lambda x: x.get('population', 0), reverse=True)
        
        # Grouper par département
        by_dept = {}
        for commune in communes_sorted:
            dept = commune.get('codeDepartement', 'Inconnu')
            if dept not in by_dept:
                by_dept[dept] = []
            by_dept[dept].append(commune)
        
        print(f"✅ {len(communes)} communes trouvées\n")
        print(f"📊 Répartition par département:")
        for dept in sorted(by_dept.keys()):
            print(f"   - Département {dept}: {len(by_dept[dept])} communes")
        
        print(f"\n{'='*80}")
        print(f"🏘️  TOP 50 COMMUNES PAR POPULATION")
        print(f"{'='*80}\n")
        
        for i, commune in enumerate(communes_sorted[:50], 1):
            nom = commune.get('nom', 'N/A')
            population = commune.get('population', 0)
            code_postal = commune.get('codesPostaux', ['N/A'])[0]
            dept = commune.get('codeDepartement', '??')
            
            print(f"{i:3d}. {nom:40s} ({dept}) - {population:>8,} hab. - CP: {code_postal}")
        
        print(f"\n{'='*80}")
        print(f"📋 LISTE COMPLÈTE PAR DÉPARTEMENT")
        print(f"{'='*80}\n")
        
        for dept in sorted(by_dept.keys()):
            print(f"\n🏛️  Département {dept} ({len(by_dept[dept])} communes):")
            print("-" * 80)
            
            for i, commune in enumerate(by_dept[dept], 1):
                nom = commune.get('nom', 'N/A')
                population = commune.get('population', 0)
                code_postal = commune.get('codesPostaux', ['N/A'])[0]
                
                if i <= 20:  # Afficher les 20 premières par département
                    print(f"   {i:3d}. {nom:35s} - {population:>8,} hab. - CP: {code_postal}")
                elif i == 21:
                    print(f"   ... ({len(by_dept[dept]) - 20} autres communes)")
                    break
        
        # Statistiques finales
        total_pop = sum(c.get('population', 0) for c in communes)
        pop_min = min(c.get('population', 0) for c in communes)
        pop_max = max(c.get('population', 0) for c in communes)
        pop_avg = total_pop / len(communes) if communes else 0
        
        print(f"\n{'='*80}")
        print(f"📊 STATISTIQUES")
        print(f"{'='*80}")
        print(f"   Nombre total de communes: {len(communes)}")
        print(f"   Population totale: {total_pop:,} habitants")
        print(f"   Population moyenne par commune: {pop_avg:.0f} habitants")
        print(f"   Plus petite commune: {pop_min:,} habitants")
        print(f"   Plus grande commune: {pop_max:,} habitants")
        print(f"   Nombre de départements: {len(by_dept)}")
        print(f"{'='*80}\n")
        
        # Demander si on veut exporter
        print("💾 Export disponible:")
        print("   Pour exporter toutes les communes: python3 list_communes.py \"" + region_name + "\" export")
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des communes: {e}")


def export_communes_to_file(region_name: str):
    """
    Exporte toutes les communes dans un fichier texte
    """
    region_code = REGIONS.get(region_name)
    
    if not region_code:
        return
    
    try:
        response = requests.get(
            f"https://geo.api.gouv.fr/regions/{region_code}/communes",
            params={'fields': 'nom,code,population'},
            timeout=60
        )
        response.raise_for_status()
        communes = response.json()
        
        communes_sorted = sorted(communes, key=lambda x: x.get('population', 0), reverse=True)
        
        filename = f"communes_{region_name.lower().replace(' ', '_').replace('-', '_')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Communes de la région: {region_name}\n")
            f.write(f"Total: {len(communes)} communes\n")
            f.write(f"{'='*80}\n\n")
            
            for i, commune in enumerate(communes_sorted, 1):
                nom = commune.get('nom', 'N/A')
                population = commune.get('population', 0)
                f.write(f"{i:4d}. {nom:50s} - {population:>8,} hab.\n")
        
        print(f"✅ Export réussi: {filename}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {e}")


def main():
    if len(sys.argv) < 2:
        print("\n❌ Usage: python3 list_communes.py <RÉGION> [export]")
        print("\nExemples:")
        print('  python3 list_communes.py "Grand Est"')
        print('  python3 list_communes.py "Grand Est" export')
        print("\n📋 Régions disponibles:")
        for region in sorted(REGIONS.keys()):
            print(f"   - {region}")
        sys.exit(1)
    
    region_name = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == "export":
        export_communes_to_file(region_name)
    else:
        list_communes_in_region(region_name)


if __name__ == "__main__":
    main()
