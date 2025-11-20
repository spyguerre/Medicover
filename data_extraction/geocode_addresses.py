#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour géocoder toutes les adresses de la base de données
Usage: python3 geocode_addresses.py
"""

import sqlite3
import requests
import time
from typing import Optional, Tuple

# API de géocodage du gouvernement français
GEOCODING_API = "https://api-adresse.data.gouv.fr/search/"


def geocode_address(address_complete: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Géocode une adresse pour obtenir (latitude, longitude)
    """
    try:
        response = requests.get(
            GEOCODING_API,
            params={'q': address_complete, 'limit': 1},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('features') and len(data['features']) > 0:
            coords = data['features'][0]['geometry']['coordinates']
            return (coords[1], coords[0])  # (latitude, longitude)
    except Exception as e:
        pass
    
    return (None, None)


def geocode_all_addresses(db_name: str = "praticiens_sante.db"):
    """
    Géocode toutes les adresses de la base qui n'ont pas encore de coordonnées
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Compter les adresses sans coordonnées
    cursor.execute("""
        SELECT COUNT(*) 
        FROM Adresse 
        WHERE latitude IS NULL OR longitude IS NULL
    """)
    total_to_geocode = cursor.fetchone()[0]
    
    if total_to_geocode == 0:
        print("\n✅ Toutes les adresses sont déjà géocodées !\n")
        conn.close()
        return
    
    print(f"\n{'='*80}")
    print(f"🗺️  GÉOCODAGE DES ADRESSES")
    print(f"{'='*80}")
    print(f"   📍 {total_to_geocode} adresses à géocoder\n")
    
    # Récupérer toutes les adresses sans coordonnées
    cursor.execute("""
        SELECT adresse_id, ligne, code_postal, ville, complete
        FROM Adresse
        WHERE latitude IS NULL OR longitude IS NULL
    """)
    
    addresses = cursor.fetchall()
    
    geocoded_count = 0
    failed_count = 0
    
    for i, (addr_id, ligne, postal, ville, complete) in enumerate(addresses, 1):
        if i % 50 == 0:
            print(f"   [{i}/{total_to_geocode}] {geocoded_count} géocodées, {failed_count} échecs")
            conn.commit()  # Commit régulier
        
        # Construire la requête de géocodage
        if ligne and postal and ville:
            query = f"{ligne} {postal} {ville}"
        else:
            query = complete
        
        # Géocoder
        latitude, longitude = geocode_address(query)
        
        if latitude and longitude:
            # Mettre à jour la base
            cursor.execute("""
                UPDATE Adresse
                SET latitude = ?, longitude = ?
                WHERE adresse_id = ?
            """, (latitude, longitude, addr_id))
            geocoded_count += 1
        else:
            failed_count += 1
        
        # Délai pour ne pas surcharger l'API
        time.sleep(0.05)  # 50ms entre chaque requête
    
    # Dernier commit
    conn.commit()
    
    print(f"\n{'='*80}")
    print(f"📊 RÉSULTATS")
    print(f"{'='*80}")
    print(f"   ✅ {geocoded_count} adresses géocodées")
    print(f"   ❌ {failed_count} échecs")
    print(f"{'='*80}\n")
    
    # Statistiques finales
    cursor.execute("SELECT COUNT(*) FROM Adresse WHERE latitude IS NOT NULL")
    total_geocoded = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Adresse")
    total_addresses = cursor.fetchone()[0]
    
    percentage = (total_geocoded / total_addresses * 100) if total_addresses > 0 else 0
    print(f"📈 Base de données: {total_geocoded}/{total_addresses} adresses géocodées ({percentage:.1f}%)\n")
    
    conn.close()


def main():
    """Point d'entrée principal"""
    print("\n🗺️  Géocodage de toutes les adresses de la base de données...")
    print("   (Utilise l'API Adresse du gouvernement français)\n")
    
    geocode_all_addresses()


if __name__ == "__main__":
    main()
