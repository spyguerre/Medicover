#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour récupérer toutes les communes d'une région en mode RAW
Usage: python3 get_villes_raw.py "Grand Est"
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


def get_communes_raw(region_name: str):
    """
    Récupère toutes les communes d'une région et les affiche en RAW
    """
    region_code = REGIONS.get(region_name)
    
    if not region_code:
        print(f"Région '{region_name}' non reconnue")
        print("Régions disponibles:", ', '.join(REGIONS.keys()))
        return
    
    # Récupérer les départements
    response_depts = requests.get(
        f"https://geo.api.gouv.fr/departements",
        params={'codeRegion': region_code},
        timeout=30
    )
    departements = response_depts.json()
    
    # Récupérer toutes les communes
    all_communes = []
    
    for dept in departements:
        dept_code = dept['code']
        response = requests.get(
            f"https://geo.api.gouv.fr/departements/{dept_code}/communes",
            params={'fields': 'nom'},
            timeout=30
        )
        communes = response.json()
        all_communes.extend([c['nom'] for c in communes])
    
    # Afficher en RAW
    for ville in sorted(all_communes):
        print(ville)
    
    print(f"\n# Total: {len(all_communes)} communes")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 get_villes_raw.py <RÉGION>")
        print('Exemple: python3 get_villes_raw.py "Grand Est"')
        sys.exit(1)
    
    get_communes_raw(sys.argv[1])
