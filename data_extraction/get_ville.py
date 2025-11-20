#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour récupérer les praticiens d'une ville avec toutes leurs informations
Usage: python3 get_ville.py Nancy
"""

import requests
import json
import sys
import time
from typing import List, Dict, Optional

# Configuration API
API_URL = "https://gateway.api.esante.gouv.fr/fhir"
API_KEY = "93f55893-96fa-4364-b558-9396fa2364d7"
HEADERS = {
    "ESANTE-API-KEY": API_KEY,
    "Accept": "application/json"
}

# API de géocodage du gouvernement français
GEOCODING_API = "https://api-adresse.data.gouv.fr/search/"

# Import de la fonction pour récupérer les spécialités
from sm import get_spe


def geocode_address(address_complete: str) -> Dict[str, Optional[float]]:
    """
    Géocode une adresse française pour obtenir latitude et longitude
    Utilise l'API Adresse du gouvernement français (gratuite)
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
            return {
                'longitude': coords[0],
                'latitude': coords[1]
            }
    except Exception as e:
        print(f"   ⚠️ Erreur géocodage: {e}")
    
    return {
        'longitude': None,
        'latitude': None
    }


def get_organizations_by_city(city: str, max_results: int = 500) -> List[Dict]:
    """
    Récupère toutes les organisations d'une ville donnée
    """
    print(f"\n🔍 Recherche des organisations à {city}...")
    
    organizations = []
    
    params = {
        'address-city': city,
        '_count': max_results
    }
    
    try:
        response = requests.get(
            f"{API_URL}/v2/Organization",
            headers=HEADERS,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        entries = data.get('entry', [])
        
        for entry in entries:
            org = entry.get('resource', {})
            organizations.append({
                'id': org.get('id'),
                'name': org.get('name', 'N/A'),
                'address': get_full_address(org.get('address', [])),
                'reference': f"Organization/{org.get('id')}"
            })
        
        print(f"   📦 {len(organizations)} organisations trouvées...")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la récupération: {e}")
    
    print(f"✅ Total: {len(organizations)} organisations à {city}\n")
    return organizations


def get_full_address(addresses: List[Dict]) -> Dict:
    """
    Extrait l'adresse complète d'une liste d'adresses FHIR
    Retourne un dict avec les champs séparés
    Gère les extensions FHIR pour les numéros de rue et noms de voie
    """
    if not addresses:
        return {
            'ligne': None,
            'code_postal': None,
            'ville': None,
            'pays': None,
            'complete': "Adresse non disponible"
        }
    
    addr = addresses[0]  # Prendre la première adresse
    
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
        
        # Construire la ligne d'adresse
        if house_number and street_name:
            lines.append(f"{house_number} {street_name}")
        elif street_name:
            lines.append(street_name)
        elif house_number:
            lines.append(house_number)
    
    # Si pas d'extensions, essayer le champ 'line' classique
    if not lines and 'line' in addr:
        lines = [line for line in addr['line'] if line is not None]
    
    # Code postal et ville
    postal = addr.get('postalCode', '')
    city = addr.get('city', '')
    country = addr.get('country', '')
    
    # Adresse complète
    parts = []
    parts.extend(lines)
    if postal or city:
        parts.append(f"{postal} {city}".strip())
    if country:
        parts.append(country)
    
    address_complete = ', '.join(parts) if parts else "Adresse non disponible"
    
    # Géocoder l'adresse pour obtenir latitude/longitude
    coords = {'longitude': None, 'latitude': None}
    if lines and postal and city:  # Seulement si on a une adresse complète
        # Construire une requête propre pour le géocodage
        geocode_query = f"{' '.join(lines)} {postal} {city}"
        coords = geocode_address(geocode_query)
        # Petit délai pour ne pas surcharger l'API
        time.sleep(0.1)
    
    return {
        'ligne': ', '.join(lines) if lines else None,
        'code_postal': postal if postal else None,
        'ville': city if city else None,
        'pays': country if country else None,
        'complete': address_complete,
        'latitude': coords['latitude'],
        'longitude': coords['longitude']
    }


def get_practitioner_roles_by_organization(org_reference: str) -> List[Dict]:
    """
    Récupère tous les PractitionerRole liés à une organisation
    """
    params = {
        'organization': org_reference,
        '_count': 100
    }
    
    try:
        response = requests.get(
            f"{API_URL}/v2/PractitionerRole",
            headers=HEADERS,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        roles = []
        for entry in data.get('entry', []):
            role = entry.get('resource', {})
            roles.append({
                'id': role.get('id'),
                'practitioner_ref': role.get('practitioner', {}).get('reference'),
                'codes': extract_codes(role.get('code', [])),
                'specialty': extract_codes(role.get('specialty', []))
            })
        
        return roles
        
    except Exception as e:
        return []


def extract_codes(code_list: List[Dict]) -> List[Dict]:
    """
    Extrait les codes et leurs systèmes d'une liste de CodeableConcept
    """
    codes = []
    for code_item in code_list:
        for coding in code_item.get('coding', []):
            codes.append({
                'code': coding.get('code'),
                'display': coding.get('display', 'N/A'),
                'system': coding.get('system', '').split('/')[-1]  # Garder juste le nom
            })
    return codes


def get_practitioner_details(practitioner_ref: str) -> Optional[Dict]:
    """
    Récupère les détails d'un praticien à partir de sa référence
    """
    # Extraire l'ID de la référence (format: "Practitioner/003-3014698-3057235")
    practitioner_id = practitioner_ref.split('/')[-1]
    
    try:
        response = requests.get(
            f"{API_URL}/v2/Practitioner/{practitioner_id}",
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        practitioner = response.json()
        
        # Extraire les informations
        names = practitioner.get('name', [])
        name_info = names[0] if names else {}
        
        # Extraire le RPPS
        rpps = None
        for identifier in practitioner.get('identifier', []):
            id_type = identifier.get('type', {}).get('coding', [])
            if id_type and id_type[0].get('code') == 'RPPS':
                rpps = identifier.get('value')
                break
        
        # Extraire les qualifications
        profession_code = None  # Code profession (10=Médecin, etc.)
        specialites_sm = []  # Codes SM bruts
        
        for qual in practitioner.get('qualification', []):
            qual_code = qual.get('code', {})
            qual_codes = extract_codes([qual_code])
            
            for code in qual_codes:
                # Profession (10, 21, etc.)
                if code['code'] and code['system'] == 'TRE-G15-ProfessionSante':
                    profession_code = code['code']
                
                # Spécialités SM
                if code['code'] and code['code'].startswith('SM') and code['system'] == 'TRE-R38-SpecialiteOrdinale':
                    specialites_sm.append(code['code'])
        
        return {
            'family': name_info.get('family', 'N/A'),
            'given': ' '.join(name_info.get('given', [])),
            'prefix': ' '.join(name_info.get('prefix', [])),
            'rpps': rpps or 'N/A',
            'profession_code': profession_code,  # Code brut (10, 21, etc.)
            'specialites_sm': specialites_sm  # Liste des codes SM bruts
        }
        
    except Exception as e:
        return None


def get_practitioners_in_city(city: str, max_orgs: int = 100) -> List[Dict]:
    """
    Fonction principale : récupère tous les praticiens d'une ville
    """
    print(f"\n{'='*80}")
    print(f"🏥 RECHERCHE DES PRATICIENS À {city.upper()}")
    print(f"{'='*80}\n")
    
    # Étape 1 : Récupérer les organisations de la ville
    organizations = get_organizations_by_city(city, max_orgs)
    
    if not organizations:
        print(f"❌ Aucune organisation trouvée à {city}")
        return []
    
    # Créer un dictionnaire des organisations pour un accès rapide
    orgs_dict = {org['reference']: org for org in organizations}
    
    # Étape 2 : Pour chaque organisation, récupérer les praticiens
    # On va stocker les praticiens avec TOUTES leurs organisations
    practitioners_orgs = {}  # {pract_ref: [org1, org2, ...]}
    
    print(f"🔄 Récupération des praticiens pour {len(organizations)} organisations...\n")
    
    for i, org in enumerate(organizations, 1):
        print(f"   [{i}/{len(organizations)}] {org['name'][:60]}...", end=" ")
        
        # Récupérer les PractitionerRole de cette organisation
        roles = get_practitioner_roles_by_organization(org['reference'])
        
        if not roles:
            print("(aucun praticien)")
            continue
        
        print(f"({len(roles)} praticien(s))")
        
        # Pour chaque rôle, stocker l'association praticien-organisation
        for role in roles:
            pract_ref = role.get('practitioner_ref')
            if not pract_ref:
                continue
            
            if pract_ref not in practitioners_orgs:
                practitioners_orgs[pract_ref] = []
            practitioners_orgs[pract_ref].append(org)
    
    # Étape 3 : Construire la liste finale des praticiens
    all_practitioners = []
    
    print(f"\n🔄 Construction des profils praticiens...\n")
    
    for pract_ref, orgs in practitioners_orgs.items():
        # Récupérer les détails du praticien
        practitioner = get_practitioner_details(pract_ref)
        
        if not practitioner:
            continue
        
        # Trouver la première adresse valide parmi toutes les organisations
        valid_address = None
        valid_org_name = None
        
        for org in orgs:
            if org['address']['ligne']:  # Si l'adresse a une ligne (rue)
                valid_address = org['address']
                valid_org_name = org['name']
                break
        
        # Si aucune adresse valide trouvée, on skip ce praticien
        if not valid_address:
            continue
        
        # Déterminer la profession
        profession_label = "Autre"
        if practitioner['profession_code'] == '10':
            profession_label = "Médecin"
        elif practitioner['profession_code'] == '21':
            profession_label = "Pharmacien"
        elif practitioner['profession_code'] == '40':
            profession_label = "Chirurgien-Dentiste"
        elif practitioner['profession_code'] == '50':
            profession_label = "Sage-Femme"
        elif practitioner['profession_code'] == '60':
            profession_label = "Infirmier"
        elif practitioner['profession_code'] == '70':
            profession_label = "Masseur-Kinésithérapeute"
        
        # Récupérer les spécialités avec get_spe()
        specialites = []
        if practitioner['profession_code'] == '10':  # Seulement pour les médecins
            for sm_code in practitioner['specialites_sm']:
                # Enlever le "SM" pour avoir juste le numéro
                code_num = sm_code[2:] if sm_code.startswith('SM') else sm_code
                spe_label = get_spe(code_num)
                specialites.append({
                    'code': sm_code,
                    'libelle': spe_label
                })
        
        all_practitioners.append({
            'nom': practitioner['family'],
            'prenom': practitioner['given'],
            'civilite': practitioner['prefix'],
            'rpps': practitioner['rpps'],
            'profession': profession_label,
            'specialites': specialites if specialites else None,
            'organisation': valid_org_name,
            'adresse': valid_address
        })
    
    print(f"\n✅ Total: {len(all_practitioners)} praticiens avec adresse valide\n")
    return all_practitioners


def display_results(practitioners: List[Dict], city: str):
    """
    Affiche les résultats de manière formatée
    """
    print(f"\n{'='*80}")
    print(f"📊 RÉSULTATS POUR {city.upper()} - {len(practitioners)} PRATICIENS")
    print(f"{'='*80}\n")
    
    for i, p in enumerate(practitioners, 1):
        print(f"\n{'─'*80}")
        print(f"👤 PRATICIEN #{i}")
        print(f"{'─'*80}")
        print(f"Nom:          {p['civilite']} {p['prenom']} {p['nom']}")
        print(f"RPPS:         {p['rpps']}")
        print(f"Profession:   {p['profession']}")
        
        if p.get('specialites'):
            print(f"\n🏥 Spécialités:")
            for spec in p['specialites']:
                print(f"   • {spec['code']} : {spec['libelle']}")
        
        print(f"\nOrganisation: {p['organisation']}")
        addr = p['adresse']
        if addr['ligne']:
            print(f"Adresse:      {addr['ligne']}")
        if addr['code_postal'] and addr['ville']:
            print(f"              {addr['code_postal']} {addr['ville']}")
        if addr['pays']:
            print(f"              {addr['pays']}")


def save_to_json(practitioners: List[Dict], city: str):
    """
    Sauvegarde les résultats dans un fichier JSON
    """
    filename = f"praticiens_{city.lower()}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'ville': city,
            'date': '2025-11-18',
            'total': len(practitioners),
            'praticiens': practitioners
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans: {filename}")


def main():
    """
    Point d'entrée du script
    """
    # Récupérer la ville depuis les arguments ou utiliser Nancy par défaut
    city = sys.argv[1] if len(sys.argv) > 1 else "Nancy"
    
    # Récupérer les praticiens
    practitioners = get_practitioners_in_city(city, max_orgs=100)
    
    if practitioners:
        # Afficher les résultats
        display_results(practitioners, city)
        
        # Sauvegarder dans un fichier JSON
        save_to_json(practitioners, city)
    else:
        print(f"\n❌ Aucun praticien trouvé à {city}")


if __name__ == "__main__":
    main()
