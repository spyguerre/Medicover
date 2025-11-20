#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour dumper TOUTES les infos d'un praticien depuis l'API
Usage: python3 dump_practitioner.py <RPPS>
"""

import requests
import json
import sys

# Configuration API
API_URL = "https://gateway.api.esante.gouv.fr/fhir"
API_KEY = "93f55893-96fa-4364-b558-9396fa2364d7"
HEADERS = {
    "ESANTE-API-KEY": API_KEY,
    "Accept": "application/json"
}


def dump_practitioner(rpps: str):
    """
    Récupère et affiche TOUTES les données d'un praticien
    """
    print(f"\n{'='*80}")
    print(f"🔍 DUMP COMPLET - RPPS: {rpps}")
    print(f"{'='*80}\n")
    
    all_data = {}
    
    # 1. Practitioner
    print("📋 Requête 1: GET /v2/Practitioner/{rpps}")
    print("-" * 80)
    
    try:
        response = requests.get(
            f"{API_URL}/v2/Practitioner/{rpps}",
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            practitioner_data = response.json()
            all_data['practitioner'] = practitioner_data
            print("✅ Succès")
            print(f"URL: {response.url}")
            print(f"\nRéponse JSON:")
            print(json.dumps(practitioner_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Code HTTP: {response.status_code}")
            print(f"Réponse: {response.text}")
            all_data['practitioner'] = None
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        all_data['practitioner'] = None
    
    
    # 2. PractitionerRole
    print(f"\n\n{'='*80}")
    print(f"📋 Requête 2: GET /v2/PractitionerRole?practitioner=Practitioner/{rpps}")
    print("-" * 80)
    
    try:
        response = requests.get(
            f"{API_URL}/v2/PractitionerRole",
            headers=HEADERS,
            params={'practitioner': f'Practitioner/{rpps}', '_count': 100},
            timeout=30
        )
        
        if response.status_code == 200:
            role_data = response.json()
            all_data['practitionerRole'] = role_data
            print("✅ Succès")
            print(f"URL: {response.url}")
            print(f"\nRéponse JSON:")
            print(json.dumps(role_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Code HTTP: {response.status_code}")
            print(f"Réponse: {response.text}")
            all_data['practitionerRole'] = None
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        all_data['practitionerRole'] = None
    
    
    # 3. Sauvegarder
    print(f"\n\n{'='*80}")
    print("💾 SAUVEGARDE")
    print("-" * 80)
    
    filename = f"dump_{rpps}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Toutes les données sauvegardées dans: {filename}")
    print(f"   Taille: {len(json.dumps(all_data))} caractères")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        rpps = "10001757037"  # Valeur par défaut
        print(f"⚠️  Pas de RPPS fourni, utilisation de: {rpps}")
    else:
        rpps = sys.argv[1]
    
    dump_practitioner(rpps)
