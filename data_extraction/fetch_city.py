#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour récupérer TOUS les praticiens d'une ville et les sauvegarder en JSON
Usage: python3 fetch_city.py <ville>
Exemple: python3 fetch_city.py Nancy
"""

import requests
import json
import sys
import time
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
        
        # Convertir les spécialités en libellés
        specialites = []
        for sm_code in specialites_sm:
            code_num = sm_code[2:] if sm_code.startswith('SM') else sm_code
            try:
                spe_label = get_spe(code_num)
                specialites.append({
                    'code': sm_code,
                    'libelle': spe_label
                })
            except Exception:
                pass
        
        return {
            'family': name_info.get('family', 'N/A'),
            'given': ' '.join(name_info.get('given', [])),
            'prefix': ' '.join(name_info.get('prefix', [])),
            'rpps': rpps,
            'profession_code': profession_code,
            'specialites': specialites
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


def fetch_all_practitioners_from_city(city: str) -> List[Dict]:
    """Récupère TOUS les praticiens d'une ville (toutes professions)"""
    print(f"\n{'='*80}")
    print(f"🔍 RÉCUPÉRATION DE TOUS LES PRATICIENS DE {city.upper()}")
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
    
    # Étape 3: Récupérer les détails de chaque praticien
    print(f"🔄 Récupération des détails (informations + adresses + géocodage)...\n")
    
    result = []
    total = len(all_practitioners)
    processed = 0
    
    for pract_id, org_refs in all_practitioners.items():
        processed += 1
        
        if processed % 20 == 0:
            print(f"   [{processed}/{total}] praticiens traités - {len(result)} avec adresse valide")
        
        # Récupérer les détails du praticien
        practitioner = get_practitioner_details(pract_id)
        
        if not practitioner:
            continue
        
        # Trouver une adresse valide
        valid_address = None
        for org_ref in org_refs:
            addr = get_organization_address(org_ref)
            if addr and addr['ligne']:
                valid_address = addr
                break
        
        if not valid_address:
            continue
        
        # Ajouter à la liste
        result.append({
            'rpps': practitioner['rpps'],
            'nom': practitioner['family'],
            'prenom': practitioner['given'],
            'civilite': practitioner['prefix'],
            'profession_code': practitioner['profession_code'],
            'specialites': practitioner['specialites'],
            'adresse': valid_address
        })
    
    print(f"\n   ✅ {len(result)} praticiens avec adresse valide\n")
    
    return result


def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        print("\n❌ Usage: python3 fetch_city.py <ville>")
        print("\nExemple: python3 fetch_city.py Nancy\n")
        sys.exit(1)
    
    city = sys.argv[1]
    
    # Récupérer tous les praticiens
    praticiens = fetch_all_practitioners_from_city(city)
    
    if not praticiens:
        print("❌ Aucun praticien trouvé")
        return
    
    # Sauvegarder en JSON
    filename = f"praticiens_{city.lower()}_complet.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'ville': city,
            'date': '2025-11-19',
            'total': len(praticiens),
            'praticiens': praticiens
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"💾 SAUVEGARDE")
    print(f"{'='*80}")
    print(f"   ✅ {len(praticiens)} praticiens sauvegardés dans {filename}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
