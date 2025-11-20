#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour alimenter la base de données avec TOUTES les communes d'une région
Usage: python3 load_region_to_db.py "Grand Est"
"""

import requests
import subprocess
import sys
import time
import os
from datetime import datetime

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


def get_all_communes(region_name: str):
    """
    Récupère toutes les communes d'une région
    """
    region_code = REGIONS.get(region_name)
    
    if not region_code:
        print(f"❌ Région '{region_name}' non reconnue")
        print(f"Régions disponibles: {', '.join(REGIONS.keys())}")
        return []
    
    print(f"🔍 Récupération des communes de {region_name}...")
    
    # Récupérer les départements
    response_depts = requests.get(
        f"https://geo.api.gouv.fr/departements",
        params={'codeRegion': region_code},
        timeout=30
    )
    departements = response_depts.json()
    
    print(f"   ✅ {len(departements)} départements trouvés")
    
    # Récupérer toutes les communes
    all_communes = []
    
    for dept in departements:
        dept_code = dept['code']
        dept_nom = dept['nom']
        
        response = requests.get(
            f"https://geo.api.gouv.fr/departements/{dept_code}/communes",
            params={'fields': 'nom,population'},
            timeout=30
        )
        communes = response.json()
        all_communes.extend(communes)
        print(f"   ✅ {dept_nom} ({dept_code}): {len(communes)} communes")
    
    # Trier par ordre alphabétique
    all_communes_sorted = sorted(all_communes, key=lambda x: x.get('nom', ''))
    
    print(f"\n✅ Total: {len(all_communes_sorted)} communes récupérées\n")
    
    return all_communes_sorted


def process_ville(ville_name: str, index: int, total: int):
    """
    Traite une ville : fetch + load
    
    Returns:
        tuple: (success: bool, praticiens_count: int, message: str)
    """
    print(f"\n{'='*80}")
    print(f"[{index}/{total}] 🏘️  {ville_name}")
    print(f"{'='*80}")
    
    # Générer le nom du fichier JSON (normaliser les caractères spéciaux)
    ville_normalized = ville_name.lower()
    ville_normalized = ville_normalized.replace(' ', '_').replace('-', '_')
    ville_normalized = ville_normalized.replace('œ', 'oe').replace('æ', 'ae')
    ville_normalized = ville_normalized.replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('ë', 'e')
    ville_normalized = ville_normalized.replace('à', 'a').replace('â', 'a').replace('ä', 'a')
    ville_normalized = ville_normalized.replace('ô', 'o').replace('ö', 'o')
    ville_normalized = ville_normalized.replace('û', 'u').replace('ù', 'u').replace('ü', 'u')
    ville_normalized = ville_normalized.replace('î', 'i').replace('ï', 'i')
    ville_normalized = ville_normalized.replace('ç', 'c').replace("'", '_')
    json_filename = f"praticiens_{ville_normalized}_complet.json"
    
    start_time = time.time()
    
    # Étape 1 : Fetch
    print(f"   1️⃣  Récupération des praticiens via API (peut prendre plusieurs minutes pour les grandes villes)...")
    try:
        result_fetch = subprocess.run(
            ['python3', 'fetch_city.py', ville_name],
            capture_output=False,  # Afficher la sortie en temps réel
            text=True,
            timeout=1800  # 30 minutes max pour les très grandes villes
        )
        
        if result_fetch.returncode != 0:
            print(f"   ⚠️  Échec du fetch")
            return (False, 0, "Échec fetch")
        
        # Vérifier si le JSON existe
        if not os.path.exists(json_filename):
            print(f"   ℹ️  Aucun praticien trouvé")
            return (True, 0, "Aucun praticien")
        
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  Timeout fetch")
        if os.path.exists(json_filename):
            os.remove(json_filename)
        return (False, 0, "Timeout fetch")
    except Exception as e:
        print(f"   ❌ Erreur fetch: {e}")
        return (False, 0, f"Erreur: {e}")
    
    # Étape 2 : Load
    print(f"   2️⃣  Chargement dans la base de données...")
    try:
        result_load = subprocess.run(
            ['python3', 'load_json_to_db.py', json_filename],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max
        )
        
        if result_load.returncode != 0:
            print(f"   ⚠️  Échec du chargement")
            # Supprimer le JSON en cas d'erreur
            if os.path.exists(json_filename):
                os.remove(json_filename)
            return (False, 0, "Échec load")
        
        # Extraire le nombre de praticiens insérés depuis la sortie
        output = result_load.stdout
        praticiens_count = 0
        
        # Chercher "✅ X praticiens insérés"
        for line in output.split('\n'):
            if 'praticiens insérés' in line or 'praticien inséré' in line:
                try:
                    praticiens_count = int(line.split()[1])
                except:
                    pass
        
        elapsed = time.time() - start_time
        print(f"   ✅ Terminé en {elapsed:.1f}s - {praticiens_count} praticiens ajoutés")
        
        return (True, praticiens_count, "Succès")
        
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  Timeout load")
        if os.path.exists(json_filename):
            os.remove(json_filename)
        return (False, 0, "Timeout load")
    except Exception as e:
        print(f"   ❌ Erreur load: {e}")
        if os.path.exists(json_filename):
            os.remove(json_filename)
        return (False, 0, f"Erreur: {e}")


def load_region_to_db(region_name: str, start_from: int = 0, limit: int = None):
    """
    Charge toutes les communes d'une région dans la base de données
    
    Args:
        region_name: Nom de la région
        start_from: Commencer à partir de la Nième commune (pour reprendre)
        limit: Limiter au N premières communes (None = toutes)
    """
    print("\n" + "="*80)
    print(f"🌍 ALIMENTATION DE LA BASE POUR LA RÉGION: {region_name.upper()}")
    print("="*80 + "\n")
    
    # Récupérer toutes les communes
    communes = get_all_communes(region_name)
    
    if not communes:
        return
    
    # Appliquer start_from et limit
    if start_from > 0:
        print(f"⏭️  Démarrage à partir de la commune #{start_from + 1}")
        communes = communes[start_from:]
    
    if limit:
        print(f"🔢 Limitation à {limit} communes")
        communes = communes[:limit]
    
    total = len(communes)
    
    # Statistiques
    success_count = 0
    empty_count = 0
    error_count = 0
    total_praticiens = 0
    
    start_time = time.time()
    
    print(f"\n🚀 Traitement de {total} communes...\n")
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Traiter chaque commune
    for i, commune in enumerate(communes, 1):
        ville_name = commune['nom']
        population = commune.get('population', 0)
        
        success, prat_count, message = process_ville(ville_name, i + start_from, len(communes) + start_from)
        
        if success:
            if prat_count > 0:
                success_count += 1
                total_praticiens += prat_count
            else:
                empty_count += 1
        else:
            error_count += 1
        
        # Statistiques intermédiaires tous les 10 communes
        if i % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = avg_time * (total - i)
            
            print(f"\n📊 PROGRESSION")
            print(f"   Communes traitées: {i}/{total}")
            print(f"   ✅ Succès: {success_count} ({total_praticiens} praticiens)")
            print(f"   ℹ️  Vides: {empty_count}")
            print(f"   ❌ Erreurs: {error_count}")
            print(f"   ⏱️  Temps écoulé: {elapsed/60:.1f} min")
            print(f"   ⏳ Temps restant estimé: {remaining/60:.1f} min")
            print(f"   ⚡ Vitesse moyenne: {avg_time:.1f}s par commune\n")
    
    # Statistiques finales
    elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("🎉 TRAITEMENT TERMINÉ")
    print("="*80)
    print(f"\nRégion: {region_name}")
    print(f"Communes traitées: {total}")
    print(f"   ✅ Succès: {success_count} ({total_praticiens} praticiens ajoutés)")
    print(f"   ℹ️  Vides (aucun praticien): {empty_count}")
    print(f"   ❌ Erreurs: {error_count}")
    print(f"\n⏱️  Temps total: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} heures)")
    print(f"⚡ Vitesse moyenne: {elapsed/total:.1f}s par commune")
    print(f"📊 Taux de succès: {(success_count + empty_count) / total * 100:.1f}%")
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Afficher les stats de la base
    print("📊 Vérification de la base de données...")
    subprocess.run(['python3', 'query_db.py'])


def main():
    if len(sys.argv) < 2:
        print("\n❌ Usage: python3 load_region_to_db.py <RÉGION> [start_from] [limit]")
        print("\nExemples:")
        print('  python3 load_region_to_db.py "Grand Est"')
        print('  python3 load_region_to_db.py "Grand Est" 100        # Reprendre à partir de la 100ème commune')
        print('  python3 load_region_to_db.py "Grand Est" 0 50       # Limiter aux 50 premières communes')
        print("\nRégions disponibles:")
        for region in sorted(REGIONS.keys()):
            print(f"  - {region}")
        print("\nATTENTION: Ce script peut prendre plusieurs heures pour une grande région !")
        print("           Utilisez 'nohup' pour lancer en arrière-plan:")
        print('           nohup python3 load_region_to_db.py "Grand Est" > grand_est.log 2>&1 &')
        sys.exit(1)
    
    region_name = sys.argv[1]
    start_from = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    load_region_to_db(region_name, start_from, limit)


if __name__ == "__main__":
    main()
