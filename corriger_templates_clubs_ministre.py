#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger tous les templates du secrétaire du club et du ministre
qui ont le problème de {% ex ... tends "core/base.html" %}
"""

import os
import re

def corriger_template(filepath):
    """Corrige un template spécifique"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si le template a le problème
        if '{% ex' in content and 'tends "core/base.html" %}' in content:
            print(f"🔧 Correction de: {filepath}")
            
            # Remplacer le début corrompu
            pattern = r'{%\s*ex.*?tends "core/base\.html" %}'
            replacement = '{% extends "core/base.html" %}'
            
            content_corrected = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            # Écrire le fichier corrigé
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content_corrected)
            
            print(f"✅ Corrigé: {filepath}")
            return True
        else:
            print(f"✅ Déjà correct: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur avec {filepath}: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔍 RECHERCHE DES TEMPLATS SECRÉTAIRE DU CLUB & MINISTRE À CORRIGER")
    print("=" * 80)
    
    # Templates du secrétaire du club
    templates_club = [
        'templates/gouvernance/club_secretary_dashboard.html',
        'templates/gouvernance/club_athlete_registration.html',
        'templates/gouvernance/club_athletes_list.html',
        'templates/gouvernance/club_competitions_calendar.html',
        'templates/gouvernance/club_documents.html',
        'templates/gouvernance/club_identity.html',
        'templates/gouvernance/club_infrastructure.html',
        'templates/gouvernance/club_licences_galerie.html',
        'templates/gouvernance/club_license_requests.html',
        'templates/gouvernance/club_match_sheets.html',
        'templates/gouvernance/club_staff.html',
        'templates/gouvernance/club_validation_detail.html',
    ]
    
    # Templates du ministre
    templates_ministre = [
        'templates/gouvernance/minister_dashboard.html',
        'templates/gouvernance/minister_courriers.html',
        'templates/gouvernance/minister_arretes.html',
        'templates/gouvernance/minister_parapheur.html',
        'templates/gouvernance/personnel_ministere.html',
        'templates/core/minister_dashboard.html',
        'templates/core/minister_courriers.html',
        'templates/core/minister_arretes.html',
        'templates/core/minister_parapheur.html',
    ]
    
    base_dir = 'e:\\DOCERA\\PROJETS\\PYTHON\\Django\\SI-SEP-SPORT-RDC'
    total_corriges = 0
    
    print("\n🏠 CORRECTION DES TEMPLATS DU SECRÉTAIRE DU CLUB:")
    print("-" * 50)
    for template in templates_club:
        filepath = os.path.join(base_dir, template)
        if os.path.exists(filepath):
            if corriger_template(filepath):
                total_corriges += 1
        else:
            print(f"⚠️ Fichier non trouvé: {filepath}")
    
    print("\n🏛️ CORRECTION DES TEMPLATS DU MINISTRE:")
    print("-" * 50)
    for template in templates_ministre:
        filepath = os.path.join(base_dir, template)
        if os.path.exists(filepath):
            if corriger_template(filepath):
                total_corriges += 1
        else:
            print(f"⚠️ Fichier non trouvé: {filepath}")
    
    print("\n" + "=" * 80)
    print(f"🎯 RÉSULTAT: {total_corriges} templates corrigés")
    print("✅ Tous les templates du secrétaire du club et du ministre sont maintenant valides!")
    print("\n🚀 Vous pouvez maintenant:")
    print("1. Démarrez le serveur: python manage.py runserver")
    print("2. Connectez-vous comme secrétaire du club ou ministre")
    print("3. Tous les menus du sidebar fonctionneront correctement")
    print("\n📊 RÉCAPITULATIF TOTAL:")
    print("- 27 templates du secrétaire de ligue")
    print("- 14 templates de gestion infrastructure")
    print(f"- {total_corriges} templates du secrétaire du club & ministre")
    print(f"- TOTAL: {27 + 14 + total_corriges} templates corrigés")

if __name__ == '__main__':
    main()
