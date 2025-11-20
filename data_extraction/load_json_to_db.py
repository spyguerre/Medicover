#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour alimenter la base de données depuis un JSON de ville
Usage: python3 load_json_to_db.py <fichier_json>
Exemple: python3 load_json_to_db.py praticiens_nancy_complet.json
"""

import sqlite3
import json
import sys
import os
from sm import get_spe

# Mapping des codes profession
PROFESSIONS = {
    '10': 'Médecin',
    '21': 'Pharmacien',
    '40': 'Chirurgien-Dentiste',
    '50': 'Sage-Femme',
    '60': 'Infirmier',
    '70': 'Masseur-Kinésithérapeute',
    '80': 'Pédicure-Podologue',
    '91': 'Orthophoniste',
    '86': 'Psychomotricien',
    '96': 'Orthoptiste',
    '94': 'Ergothérapeute'
}


def load_json_to_database(json_file: str, db_name: str = "praticiens_sante.db"):
    """Charge les praticiens depuis un JSON dans la base de données"""
    
    print(f"\n{'='*80}")
    print(f"📂 CHARGEMENT DEPUIS JSON VERS BASE DE DONNÉES")
    print(f"{'='*80}\n")
    
    # Charger le JSON
    print(f"📖 Lecture de {json_file}...")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        return
    
    ville = data.get('ville', 'Inconnu')
    praticiens = data.get('praticiens', [])
    
    print(f"   ✅ {len(praticiens)} praticiens à insérer pour {ville}\n")
    
    # Connexion à la base
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Vérifier que les tables existent
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    if 'Praticien' not in tables:
        print("❌ La base de données n'existe pas. Lancez d'abord create_database.py")
        conn.close()
        return
    
    print(f"🔄 Insertion dans la base de données...\n")
    
    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    
    # Statistiques par profession
    stats_by_profession = {}
    
    for i, prat in enumerate(praticiens, 1):
        if i % 50 == 0:
            print(f"   [{i}/{len(praticiens)}] {inserted_count} insérés, {duplicate_count} doublons")
            conn.commit()
        
        try:
            profession_code = prat.get('profession_code')
            
            if not profession_code:
                error_count += 1
                continue
            
            # Compter par profession
            profession_name = PROFESSIONS.get(profession_code, 'Autre')
            stats_by_profession[profession_name] = stats_by_profession.get(profession_name, 0) + 1
            
            # Insérer l'adresse
            addr = prat['adresse']
            cursor.execute("""
                INSERT INTO Adresse (ligne, code_postal, ville, complete, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                addr.get('ligne'),
                addr.get('code_postal'),
                addr.get('ville'),
                addr.get('complete'),
                addr.get('latitude'),
                addr.get('longitude')
            ))
            adresse_id = cursor.lastrowid
            
            # Déterminer la spécialité
            spe_id = '0'  # Par défaut : aucune spécialité
            if prat.get('specialites') and len(prat['specialites']) > 0:
                spe_code = prat['specialites'][0]['code']
                spe_id = spe_code[2:] if spe_code.startswith('SM') else spe_code
                spe_libelle = prat['specialites'][0]['libelle']
                
                # Ajouter la spécialité si elle n'existe pas
                cursor.execute(
                    "INSERT OR IGNORE INTO Specialite (spe_id, libelle) VALUES (?, ?)",
                    (spe_id, spe_libelle)
                )
            
            # Insérer le praticien
            cursor.execute("""
                INSERT INTO Praticien (rpps, nom, prenom, civilite, metier_id, spe_id, adresse_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                prat['rpps'],
                prat['nom'],
                prat['prenom'],
                prat['civilite'],
                profession_code,
                spe_id,
                adresse_id
            ))
            inserted_count += 1
            
        except sqlite3.IntegrityError:
            duplicate_count += 1
        except Exception as e:
            error_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"📊 RÉSULTATS")
    print(f"{'='*80}")
    print(f"   ✅ {inserted_count} praticiens insérés")
    print(f"   ⚠️  {duplicate_count} doublons ignorés")
    print(f"   ❌ {error_count} erreurs")
    
    print(f"\n📋 Répartition par profession:")
    for profession, count in sorted(stats_by_profession.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {profession}: {count}")
    
    print(f"{'='*80}\n")
    
    return inserted_count


def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        print("\n❌ Usage: python3 load_json_to_db.py <fichier_json>")
        print("\nExemple: python3 load_json_to_db.py praticiens_nancy_complet.json\n")
        sys.exit(1)
    
    json_file = sys.argv[1]
    inserted = load_json_to_database(json_file)
    
    # Supprimer le fichier JSON après insertion réussie
    if inserted > 0:
        try:
            os.remove(json_file)
            print(f"🗑️  Fichier JSON supprimé: {json_file}\n")
        except Exception as e:
            print(f"⚠️  Impossible de supprimer le fichier: {e}\n")


if __name__ == "__main__":
    main()
