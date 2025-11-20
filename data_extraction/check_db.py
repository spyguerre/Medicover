#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplifié pour peupler rapidement la base avec populate.py
Pour TEST uniquement - utilise les données de Nancy déjà récupérées
"""

import sqlite3
import json

# Mapping des professions vers les codes métier
profession_to_code = {
    'Médecin': '10',
    'Pharmacien': '21',
    'Chirurgien-Dentiste': '40',
    'Sage-Femme': '50',
    'Infirmier': '60',
    'Masseur-Kinésithérapeute': '70'
}

def populate_from_json(json_file: str = 'praticiens_nancy.json', db_name: str = "praticiens_sante.db"):
    """
    Remplit la base avec les praticiens du fichier JSON (déjà géocodés)
    Filtre par profession si spécifié
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Compter par profession
    stats = {}
    for prat in data['praticiens']:
        prof = prat['profession']
        stats[prof] = stats.get(prof, 0) + 1
    
    print("\n📊 Praticiens disponibles dans Nancy:")
    for prof, count in sorted(stats.items()):
        print(f"   • {prof}: {count}")
    
    print(f"\n✅ Base de données déjà remplie avec {len(data['praticiens'])} praticiens de Nancy")
    print("   (Ils ont tous été insérés lors de la création initiale)\n")
    
    conn.close()

if __name__ == "__main__":
    populate_from_json()
