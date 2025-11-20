#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer la base de données SQLite des praticiens de santé
"""

import sqlite3
import json

def create_database(db_name: str = "praticiens_sante.db"):
    """
    Crée la base de données avec les 4 tables
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Table Metier
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Metier (
            metier_id TEXT PRIMARY KEY,
            profession TEXT NOT NULL
        )
    """)
    
    # Table Specialite
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Specialite (
            spe_id TEXT PRIMARY KEY,
            libelle TEXT NOT NULL
        )
    """)
    
    # Table Adresse
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Adresse (
            adresse_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ligne TEXT,
            code_postal TEXT,
            ville TEXT,
            complete TEXT,
            latitude REAL,
            longitude REAL
        )
    """)
    
    # Table Praticien
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Praticien (
            rpps TEXT PRIMARY KEY,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            civilite TEXT,
            metier_id TEXT NOT NULL,
            spe_id TEXT,
            adresse_id INTEGER,
            FOREIGN KEY (metier_id) REFERENCES Metier(metier_id),
            FOREIGN KEY (spe_id) REFERENCES Specialite(spe_id),
            FOREIGN KEY (adresse_id) REFERENCES Adresse(adresse_id)
        )
    """)
    
    # Créer des index pour améliorer les performances
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_praticien_metier ON Praticien(metier_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_praticien_spe ON Praticien(spe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_praticien_adresse ON Praticien(adresse_id)")
    
    conn.commit()
    print(f"✅ Base de données '{db_name}' créée avec succès!")
    print(f"   📋 Table Metier")
    print(f"   📋 Table Specialite")
    print(f"   📋 Table Adresse")
    print(f"   📋 Table Praticien")
    
    return conn


def load_metiers(cursor):
    """
    Charge les métiers depuis professions_a_filtrer.txt
    """
    print("\n🔄 Chargement des métiers...")
    
    with open('professions_a_filtrer.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '|' in line:
                metier_id, profession = line.split('|', 1)
                cursor.execute(
                    "INSERT OR IGNORE INTO Metier (metier_id, profession) VALUES (?, ?)",
                    (metier_id, profession)
                )
    
    # Compter les métiers insérés
    cursor.execute("SELECT COUNT(*) FROM Metier")
    count = cursor.fetchone()[0]
    print(f"✅ {count} métiers chargés")


def load_specialites_from_nancy(cursor):
    """
    Charge les spécialités depuis le fichier praticiens_nancy.json
    et ajoute la spécialité '0' pour 'Aucune spécialité'
    """
    print("\n🔄 Chargement des spécialités...")
    
    # Ajouter la spécialité '0' pour les non-médecins
    cursor.execute(
        "INSERT OR IGNORE INTO Specialite (spe_id, libelle) VALUES (?, ?)",
        ('0', 'Aucune spécialité')
    )
    
    # Charger les spécialités depuis le fichier Nancy
    with open('praticiens_nancy.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for praticien in data['praticiens']:
        if praticien.get('specialites'):
            for spe in praticien['specialites']:
                # Extraire juste le numéro du code (SM08 -> 08)
                code = spe['code']
                spe_id = code[2:] if code.startswith('SM') else code
                libelle = spe['libelle']
                
                cursor.execute(
                    "INSERT OR IGNORE INTO Specialite (spe_id, libelle) VALUES (?, ?)",
                    (spe_id, libelle)
                )
    
    # Compter les spécialités insérées
    cursor.execute("SELECT COUNT(*) FROM Specialite")
    count = cursor.fetchone()[0]
    print(f"✅ {count} spécialités chargées (dont '0' pour aucune spécialité)")


def insert_praticiens_from_json(cursor, json_file: str = 'praticiens_nancy.json'):
    """
    Insère les praticiens depuis le fichier JSON
    """
    print(f"\n🔄 Chargement des praticiens depuis {json_file}...")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    praticiens_inserted = 0
    adresses_inserted = 0
    
    # Mapping des professions vers les codes métier
    profession_to_code = {
        'Médecin': '10',
        'Pharmacien': '21',
        'Chirurgien-Dentiste': '40',
        'Sage-Femme': '50',
        'Infirmier': '60',
        'Masseur-Kinésithérapeute': '70'
    }
    
    for prat in data['praticiens']:
        # Récupérer le code métier
        metier_id = profession_to_code.get(prat['profession'], '99')  # 99 = Autre
        
        # Insérer l'adresse et récupérer l'ID
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
        adresses_inserted += 1
        
        # Déterminer la spécialité
        spe_id = '0'  # Par défaut : aucune spécialité
        if prat.get('specialites') and len(prat['specialites']) > 0:
            # Prendre la première spécialité
            code = prat['specialites'][0]['code']
            spe_id = code[2:] if code.startswith('SM') else code
        
        # Insérer le praticien
        try:
            cursor.execute("""
                INSERT INTO Praticien (rpps, nom, prenom, civilite, metier_id, spe_id, adresse_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                prat['rpps'],
                prat['nom'],
                prat['prenom'],
                prat['civilite'],
                metier_id,
                spe_id,
                adresse_id
            ))
            praticiens_inserted += 1
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️ Doublon ignoré: {prat['rpps']} - {prat['nom']} {prat['prenom']}")
    
    print(f"✅ {praticiens_inserted} praticiens insérés")
    print(f"✅ {adresses_inserted} adresses insérées")


def display_stats(cursor):
    """
    Affiche les statistiques de la base de données
    """
    print("\n" + "="*80)
    print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
    print("="*80)
    
    # Nombre de métiers
    cursor.execute("SELECT COUNT(*) FROM Metier")
    print(f"   Métiers: {cursor.fetchone()[0]}")
    
    # Nombre de spécialités
    cursor.execute("SELECT COUNT(*) FROM Specialite")
    print(f"   Spécialités: {cursor.fetchone()[0]}")
    
    # Nombre d'adresses
    cursor.execute("SELECT COUNT(*) FROM Adresse")
    print(f"   Adresses: {cursor.fetchone()[0]}")
    
    # Nombre de praticiens
    cursor.execute("SELECT COUNT(*) FROM Praticien")
    print(f"   Praticiens: {cursor.fetchone()[0]}")
    
    # Répartition par métier
    print("\n📋 Répartition par métier:")
    cursor.execute("""
        SELECT m.profession, COUNT(p.rpps) as count
        FROM Metier m
        LEFT JOIN Praticien p ON m.metier_id = p.metier_id
        GROUP BY m.metier_id, m.profession
        HAVING COUNT(p.rpps) > 0
        ORDER BY count DESC
    """)
    
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]}")
    
    # Top 5 spécialités
    print("\n🏥 Top 5 spécialités:")
    cursor.execute("""
        SELECT s.libelle, COUNT(p.rpps) as count
        FROM Specialite s
        LEFT JOIN Praticien p ON s.spe_id = p.spe_id
        WHERE s.spe_id != '0'
        GROUP BY s.spe_id, s.libelle
        HAVING COUNT(p.rpps) > 0
        ORDER BY count DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]}")
    
    print("="*80)


def main():
    """
    Point d'entrée principal
    """
    print("\n" + "="*80)
    print("🏥 CRÉATION DE LA BASE DE DONNÉES PRATICIENS DE SANTÉ")
    print("="*80)
    
    # Créer la base de données
    conn = create_database()
    cursor = conn.cursor()
    
    # Charger les métiers
    load_metiers(cursor)
    
    # Charger les spécialités
    load_specialites_from_nancy(cursor)
    
    # Insérer les praticiens de Nancy
    insert_praticiens_from_json(cursor)
    
    # Commit et afficher les stats
    conn.commit()
    display_stats(cursor)
    
    conn.close()
    print("\n✅ Base de données créée et remplie avec succès!")
    print(f"📁 Fichier: praticiens_sante.db\n")


if __name__ == "__main__":
    main()
