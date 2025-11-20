#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour interroger et vérifier la base de données praticiens_sante.db
Usage: python3 query_db.py
"""

import sqlite3
import json


def connect_db(db_name: str = "praticiens_sante.db"):
    """Connexion à la base de données"""
    return sqlite3.connect(db_name)


def print_stats(conn):
    """Affiche les statistiques générales de la base"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 STATISTIQUES GÉNÉRALES")
    print("="*80)
    
    # Nombre total de praticiens
    cursor.execute("SELECT COUNT(*) FROM Praticien")
    total_prat = cursor.fetchone()[0]
    print(f"\n   Total praticiens: {total_prat}")
    
    # Nombre d'adresses
    cursor.execute("SELECT COUNT(*) FROM Adresse")
    total_addr = cursor.fetchone()[0]
    print(f"   Total adresses: {total_addr}")
    
    # Adresses avec coordonnées GPS
    cursor.execute("SELECT COUNT(*) FROM Adresse WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    addr_geocoded = cursor.fetchone()[0]
    pct = (addr_geocoded / total_addr * 100) if total_addr > 0 else 0
    print(f"   Adresses géocodées: {addr_geocoded} ({pct:.1f}%)")
    
    # Nombre de spécialités
    cursor.execute("SELECT COUNT(*) FROM Specialite")
    total_spe = cursor.fetchone()[0]
    print(f"   Total spécialités: {total_spe}")
    
    # Nombre de métiers
    cursor.execute("SELECT COUNT(*) FROM Metier")
    total_metier = cursor.fetchone()[0]
    print(f"   Total métiers: {total_metier}")


def print_by_profession(conn):
    """Affiche la répartition par profession"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("👥 RÉPARTITION PAR PROFESSION")
    print("="*80 + "\n")
    
    cursor.execute("""
        SELECT m.profession, COUNT(p.rpps) as count
        FROM Metier m
        LEFT JOIN Praticien p ON m.metier_id = p.metier_id
        GROUP BY m.metier_id, m.profession
        HAVING COUNT(p.rpps) > 0
        ORDER BY count DESC
    """)
    
    for profession, count in cursor.fetchall():
        print(f"   • {profession}: {count}")


def print_by_city(conn):
    """Affiche la répartition par ville"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("🏙️  RÉPARTITION PAR VILLE")
    print("="*80 + "\n")
    
    cursor.execute("""
        SELECT a.ville, COUNT(p.rpps) as count
        FROM Adresse a
        JOIN Praticien p ON a.adresse_id = p.adresse_id
        GROUP BY a.ville
        ORDER BY count DESC
        LIMIT 10
    """)
    
    for ville, count in cursor.fetchall():
        print(f"   • {ville}: {count} praticiens")


def print_top_specialties(conn):
    """Affiche les spécialités les plus représentées"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("🏥 TOP 10 SPÉCIALITÉS")
    print("="*80 + "\n")
    
    cursor.execute("""
        SELECT s.libelle, COUNT(p.rpps) as count
        FROM Specialite s
        LEFT JOIN Praticien p ON s.spe_id = p.spe_id
        WHERE s.spe_id != '0'
        GROUP BY s.spe_id, s.libelle
        HAVING COUNT(p.rpps) > 0
        ORDER BY count DESC
        LIMIT 10
    """)
    
    for libelle, count in cursor.fetchall():
        print(f"   • {libelle}: {count}")


def show_sample_practitioners(conn, limit: int = 5):
    """Affiche quelques exemples de praticiens complets"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print(f"👤 EXEMPLES DE PRATICIENS (les {limit} premiers)")
    print("="*80 + "\n")
    
    cursor.execute("""
        SELECT 
            p.rpps, p.nom, p.prenom, p.civilite,
            m.profession,
            s.libelle as specialite,
            a.ligne, a.code_postal, a.ville,
            a.latitude, a.longitude
        FROM Praticien p
        JOIN Metier m ON p.metier_id = m.metier_id
        JOIN Specialite s ON p.spe_id = s.spe_id
        JOIN Adresse a ON p.adresse_id = a.adresse_id
        LIMIT ?
    """, (limit,))
    
    for row in cursor.fetchall():
        rpps, nom, prenom, civilite, profession, specialite, ligne, postal, ville, lat, lon = row
        
        print(f"   📋 {civilite} {prenom} {nom}")
        print(f"      RPPS: {rpps}")
        print(f"      Profession: {profession}")
        print(f"      Spécialité: {specialite}")
        print(f"      Adresse: {ligne}, {postal} {ville}")
        if lat and lon:
            print(f"      GPS: {lat}, {lon}")
        else:
            print(f"      GPS: Non géocodé")
        print()


def search_by_name(conn, nom: str):
    """Recherche un praticien par nom"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print(f"🔍 RECHERCHE: '{nom}'")
    print("="*80 + "\n")
    
    cursor.execute("""
        SELECT 
            p.rpps, p.nom, p.prenom, p.civilite,
            m.profession,
            s.libelle as specialite,
            a.complete
        FROM Praticien p
        JOIN Metier m ON p.metier_id = m.metier_id
        JOIN Specialite s ON p.spe_id = s.spe_id
        JOIN Adresse a ON p.adresse_id = a.adresse_id
        WHERE UPPER(p.nom) LIKE UPPER(?)
        LIMIT 20
    """, (f'%{nom}%',))
    
    results = cursor.fetchall()
    
    if not results:
        print(f"   ❌ Aucun praticien trouvé avec le nom '{nom}'\n")
        return
    
    print(f"   ✅ {len(results)} praticien(s) trouvé(s):\n")
    
    for rpps, nom, prenom, civilite, profession, specialite, adresse in results:
        print(f"   • {civilite} {prenom} {nom}")
        print(f"     {profession} - {specialite}")
        print(f"     {adresse}")
        print(f"     RPPS: {rpps}")
        print()


def get_practitioners_by_profession_and_city(conn, profession: str, ville: str):
    """Récupère les praticiens d'une profession dans une ville"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print(f"🔍 {profession.upper()}S À {ville.upper()}")
    print("="*80 + "\n")
    
    cursor.execute("""
        SELECT 
            p.rpps, p.nom, p.prenom,
            a.ligne, a.code_postal,
            a.latitude, a.longitude
        FROM Praticien p
        JOIN Metier m ON p.metier_id = m.metier_id
        JOIN Adresse a ON p.adresse_id = a.adresse_id
        WHERE m.profession = ? AND UPPER(a.ville) = UPPER(?)
        ORDER BY p.nom
    """, (profession, ville))
    
    results = cursor.fetchall()
    
    if not results:
        print(f"   ❌ Aucun {profession} trouvé à {ville}\n")
        return
    
    print(f"   ✅ {len(results)} {profession}(s) trouvé(s):\n")
    
    for rpps, nom, prenom, ligne, postal, lat, lon in results[:10]:  # Limiter à 10 pour l'affichage
        gps = f"GPS: {lat}, {lon}" if lat and lon else "GPS: Non géocodé"
        print(f"   • {prenom} {nom} - {ligne}, {postal} - {gps}")
    
    if len(results) > 10:
        print(f"\n   ... et {len(results) - 10} autre(s)")
    
    print()


def export_to_json(conn, profession: str, ville: str, filename: str):
    """Exporte les praticiens d'une profession/ville en JSON"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.rpps, p.nom, p.prenom, p.civilite,
            m.profession,
            s.libelle as specialite,
            a.ligne, a.code_postal, a.ville,
            a.complete, a.latitude, a.longitude
        FROM Praticien p
        JOIN Metier m ON p.metier_id = m.metier_id
        JOIN Specialite s ON p.spe_id = s.spe_id
        JOIN Adresse a ON p.adresse_id = a.adresse_id
        WHERE m.profession = ? AND UPPER(a.ville) = UPPER(?)
        ORDER BY p.nom
    """, (profession, ville))
    
    praticiens = []
    for row in cursor.fetchall():
        rpps, nom, prenom, civilite, prof, spe, ligne, postal, ville_res, complete, lat, lon = row
        praticiens.append({
            'rpps': rpps,
            'nom': nom,
            'prenom': prenom,
            'civilite': civilite,
            'profession': prof,
            'specialite': spe,
            'adresse': {
                'ligne': ligne,
                'code_postal': postal,
                'ville': ville_res,
                'complete': complete,
                'latitude': lat,
                'longitude': lon
            }
        })
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'profession': profession,
            'ville': ville,
            'total': len(praticiens),
            'praticiens': praticiens
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(praticiens)} praticiens exportés dans {filename}\n")


def main():
    """Point d'entrée principal"""
    print("\n" + "="*80)
    print("🗄️  INTERROGATION DE LA BASE DE DONNÉES")
    print("="*80)
    
    conn = connect_db()
    
    # Statistiques générales
    print_stats(conn)
    
    # Répartition par profession
    print_by_profession(conn)
    
    # Répartition par ville
    print_by_city(conn)
    
    # Top spécialités
    print_top_specialties(conn)
    
    # Exemples de praticiens
    show_sample_practitioners(conn, limit=3)
    
    # Exemples de requêtes spécifiques
    print("\n" + "="*80)
    print("📝 EXEMPLES DE REQUÊTES SPÉCIFIQUES")
    print("="*80)
    
    # Recherche par nom
    search_by_name(conn, "MULLER")
    
    # Praticiens par profession et ville
    get_practitioners_by_profession_and_city(conn, "Infirmier", "Nancy")
    
    # Export JSON
    # export_to_json(conn, "Médecin", "Nancy", "medecins_nancy.json")
    
    conn.close()
    
    print("="*80)
    print("✅ Interrogation terminée")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
