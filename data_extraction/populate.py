#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour peupler la base de données avec les praticiens d'une ville
Usage: python3 populate.py <code_profession> <ville>
Exemples:
  - python3 populate.py 60 Nancy    # Infirmiers de Nancy
  - python3 populate.py 10 Paris    # Médecins de Paris
"""

import requests
import json
import sys
import time
import sqlite3
from typing import List, Dict, Optional
from sm import get_spe

# Configuration API
API_URL = "https://gateway.api.esante.gouv.fr/fhir"
API_KEY = "93f55893-96fa-4364-b558-9396fa2364d7"
HEADERS = {
    "ESANTE-API-KEY": API_KEY,
    "Accept": "application/json"
}

# API de géocodage
GEOCODING_API = "https://api-adresse.data.gouv.fr/search/"

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


def geocode_address(address_complete: str) -> Dict[str, Optional[float]]:
    """Géocode une adresse pour obtenir latitude/longitude"""
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
            return {
                'longitude': coords[0],
                'latitude': coords[1]
            }
    except Exception:
        pass
    
    return {'longitude': None, 'latitude': None}


def get_full_address(addresses: List[Dict]) -> Optional[Dict]:
    """Extrait l'adresse complète depuis les données FHIR avec géocodage"""
    if not addresses:
        return None
    
    addr = addresses[0]
    
    # Extraire les lignes d'adresse depuis les extensions FHIR
    lines = []
    address_line_extensions = addr.get('_line', [])
    
    for line_ext in address_line_extensions:
        if not line_ext or not isinstance(line_ext, dict):
            continue
            
        extensions = line_ext.get('extension', [])
        house_number = None
        street_name = None
        
        for ext in extensions:
            url = ext.get('url', '')
            if 'iso21090-ADXP-houseNumber' in url:
                house_number = ext.get('valueString')
            elif 'iso21090-ADXP-streetNameBase' in url:
                street_name = ext.get('valueString')
        
        if house_number and street_name:
            lines.append(f"{house_number} {street_name}")
        elif street_name:
            lines.append(street_name)
        elif house_number:
            lines.append(house_number)
    
    # Si pas d'extensions, essayer le champ 'line' classique
    if not lines and 'line' in addr:
        lines = [line for line in addr['line'] if line is not None]
    
    if not lines:
        return None
    
    postal = addr.get('postalCode', '')
    city = addr.get('city', '')
    
    if not postal or not city:
        return None
    
    # Construire l'adresse complète
    parts = []
    parts.extend(lines)
    parts.append(f"{postal} {city}".strip())
    
    address_complete = ', '.join(parts)
    
    # Géocoder l'adresse
    geocode_query = f"{' '.join(lines)} {postal} {city}"
    coords = geocode_address(geocode_query)
    time.sleep(0.05)  # Petit délai pour ne pas surcharger l'API
    
    return {
        'ligne': ', '.join(lines),
        'code_postal': postal,
        'ville': city,
        'complete': address_complete,
        'latitude': coords['latitude'],
        'longitude': coords['longitude']
    }


def extract_codes(code_list: List[Dict]) -> List[Dict]:
    """Extrait les codes et leurs systèmes"""
    codes = []
    for code_item in code_list:
        for coding in code_item.get('coding', []):
            codes.append({
                'code': coding.get('code'),
                'display': coding.get('display', 'N/A'),
                'system': coding.get('system', '').split('/')[-1]
            })
    return codes


def get_practitioner_details(practitioner_id: str) -> Optional[Dict]:
    """Récupère les détails d'un praticien"""
    try:
        response = requests.get(
            f"{API_URL}/v2/Practitioner/{practitioner_id}",
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        practitioner = response.json()
        
        # Extraire les informations de base
        names = practitioner.get('name', [])
        name_info = names[0] if names else {}
        
        # Extraire le RPPS
        rpps = None
        for identifier in practitioner.get('identifier', []):
            id_type = identifier.get('type', {}).get('coding', [])
            if id_type and id_type[0].get('code') == 'RPPS':
                rpps = identifier.get('value')
                break
        
        if not rpps:
            return None
        
        # Extraire profession et spécialités
        profession_code = None
        specialites_sm = []
        
        for qual in practitioner.get('qualification', []):
            qual_code = qual.get('code', {})
            qual_codes = extract_codes([qual_code])
            
            for code in qual_codes:
                if code['code'] and code['system'] == 'TRE-G15-ProfessionSante':
                    profession_code = code['code']
                
                if code['code'] and code['code'].startswith('SM') and code['system'] == 'TRE-R38-SpecialiteOrdinale':
                    specialites_sm.append(code['code'])
        
        return {
            'family': name_info.get('family', 'N/A'),
            'given': ' '.join(name_info.get('given', [])),
            'prefix': ' '.join(name_info.get('prefix', [])),
            'rpps': rpps,
            'profession_code': profession_code,
            'specialites_sm': specialites_sm
        }
        
    except Exception:
        return None


def get_organization_address(org_ref: str) -> Optional[Dict]:
    """Récupère l'adresse d'une organisation"""
    if not org_ref:
        return None
    
    org_id = org_ref.split('/')[-1]
    
    try:
        response = requests.get(
            f"{API_URL}/v2/Organization/{org_id}",
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        org = response.json()
        
        return get_full_address(org.get('address', []))
        
    except Exception:
        return None


def get_practitioners_in_city(city: str, profession_code: str) -> List[Dict]:
    """Récupère tous les praticiens d'une profession dans une ville"""
    profession_name = PROFESSIONS.get(profession_code, f"Profession {profession_code}")
    
    print(f"\n{'='*80}")
    print(f"🔍 RÉCUPÉRATION DES {profession_name.upper()}S DE {city.upper()}")
    print(f"{'='*80}\n")
    
    # Étape 1: Récupérer les organisations de la ville
    print(f"📍 Recherche des organisations à {city}...")
    
    try:
        response = requests.get(
            f"{API_URL}/v2/Organization",
            headers=HEADERS,
            params={
                'address-city': city,
                '_count': 500
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        orgs = []
        for entry in data.get('entry', []):
            org = entry.get('resource', {})
            orgs.append({
                'id': org.get('id'),
                'name': org.get('name', 'N/A'),
                'ref': f"Organization/{org.get('id')}"
            })
        
        print(f"   ✅ {len(orgs)} organisations trouvées\n")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return []
    
    # Étape 2: Pour chaque organisation, récupérer les praticiens
    print(f"🔄 Récupération des praticiens...\n")
    
    all_practitioners = {}  # {pract_id: [org_refs]}
    
    for i, org in enumerate(orgs, 1):
        if i % 10 == 0:
            print(f"   [{i}/{len(orgs)}] organisations traitées - {len(all_practitioners)} praticiens uniques")
        
        try:
            response = requests.get(
                f"{API_URL}/v2/PractitionerRole",
                headers=HEADERS,
                params={
                    'organization': org['id'],
                    '_count': 100
                },
                timeout=30
            )
            response.raise_for_status()
            role_data = response.json()
            
            for entry in role_data.get('entry', []):
                role = entry.get('resource', {})
                pract_ref = role.get('practitioner', {}).get('reference')
                
                if pract_ref:
                    pract_id = pract_ref.split('/')[-1]
                    
                    if pract_id not in all_practitioners:
                        all_practitioners[pract_id] = []
                    all_practitioners[pract_id].append(org['ref'])
            
            time.sleep(0.05)
            
        except Exception:
            pass
    
    print(f"\n   ✅ {len(all_practitioners)} praticiens uniques trouvés\n")
    
    # Convertir en liste
    result = []
    for pract_id, org_refs in all_practitioners.items():
        result.append({
            'practitioner_id': pract_id,
            'organization_refs': org_refs
        })
    
    return result


def populate_database(profession_code: str, city: str, db_name: str = "praticiens_sante.db"):
    """Remplit la base de données avec les praticiens d'une profession dans une ville"""
    profession_name = PROFESSIONS.get(profession_code, f"Profession {profession_code}")
    
    # Récupérer tous les praticiens
    practitioners_data = get_practitioners_in_city(city, profession_code)
    
    if not practitioners_data:
        print("❌ Aucun praticien trouvé")
        return
    
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
    
    print(f"🔄 Traitement des praticiens (détails + adresses + géocodage)...\n")
    
    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    no_address_count = 0
    wrong_profession_count = 0
    
    total = len(practitioners_data)
    
    for i, pr_data in enumerate(practitioners_data, 1):
        if i % 10 == 0:
            print(f"   [{i}/{total}] {inserted_count} insérés, {duplicate_count} doublons, {no_address_count} sans adresse")
            conn.commit()
        
        pract_id = pr_data['practitioner_id']
        org_refs = pr_data['organization_refs']
        
        # Récupérer les détails du praticien
        practitioner = get_practitioner_details(pract_id)
        
        if not practitioner:
            error_count += 1
            continue
        
        # Filtrer par profession
        if practitioner['profession_code'] != profession_code:
            wrong_profession_count += 1
            continue
        
        # Trouver une adresse valide
        valid_address = None
        for org_ref in org_refs:
            addr = get_organization_address(org_ref)
            if addr and addr['ligne']:
                valid_address = addr
                break
        
        if not valid_address:
            no_address_count += 1
            continue
        
        # Déterminer la spécialité
        spe_id = '0'
        if practitioner['specialites_sm'] and len(practitioner['specialites_sm']) > 0:
            code = practitioner['specialites_sm'][0]
            spe_id = code[2:] if code.startswith('SM') else code
            
            # Ajouter la spécialité
            try:
                spe_label = get_spe(spe_id)
                cursor.execute(
                    "INSERT OR IGNORE INTO Specialite (spe_id, libelle) VALUES (?, ?)",
                    (spe_id, spe_label)
                )
            except Exception:
                pass
        
        # Insérer dans la base
        try:
            # Insérer l'adresse
            cursor.execute("""
                INSERT INTO Adresse (ligne, code_postal, ville, complete, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                valid_address['ligne'],
                valid_address['code_postal'],
                valid_address['ville'],
                valid_address['complete'],
                valid_address['latitude'],
                valid_address['longitude']
            ))
            adresse_id = cursor.lastrowid
            
            # Insérer le praticien
            cursor.execute("""
                INSERT INTO Praticien (rpps, nom, prenom, civilite, metier_id, spe_id, adresse_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                practitioner['rpps'],
                practitioner['family'],
                practitioner['given'],
                practitioner['prefix'],
                profession_code,
                spe_id,
                adresse_id
            ))
            inserted_count += 1
        except sqlite3.IntegrityError:
            duplicate_count += 1
        except Exception:
            error_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"📊 RÉSULTATS")
    print(f"{'='*80}")
    print(f"   ✅ {inserted_count} {profession_name}s insérés")
    print(f"   ⚠️  {duplicate_count} doublons ignorés")
    print(f"   ⚠️  {no_address_count} sans adresse valide")
    print(f"   ⚠️  {wrong_profession_count} autre profession")
    print(f"   ❌ {error_count} erreurs")
    print(f"{'='*80}\n")


def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 3:
        print("\n❌ Usage: python3 populate.py <code_profession> <ville>")
        print("\nCodes disponibles:")
        for code, name in PROFESSIONS.items():
            print(f"   {code} - {name}")
        print("\nExemple: python3 populate.py 60 Nancy  # Infirmiers de Nancy\n")
        sys.exit(1)
    
    profession_code = sys.argv[1]
    city = sys.argv[2]
    
    if profession_code not in PROFESSIONS:
        print(f"\n⚠️  Code profession '{profession_code}' non reconnu")
        print("\nCodes disponibles:")
        for code, name in PROFESSIONS.items():
            print(f"   {code} - {name}")
        sys.exit(1)
    
    populate_database(profession_code, city)


if __name__ == "__main__":
    main()
