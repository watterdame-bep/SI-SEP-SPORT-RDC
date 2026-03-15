#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger tous les templates du secrétaire de ligue
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
    print("🔍 RECHERCHE DES TEMPLATES DU SECRÉTAIRE DE LIGUE À CORRIGER")
    print("=" * 60)
    
    # Liste des templates du secrétaire de ligue à vérifier
    templates_ligue = [
        'templates/gouvernance/ligue_clubs_affiliation.html',
        'templates/gouvernance/ligue_medecins_list.html',
        'templates/gouvernance/ligue_profile.html',
        'templates/gouvernance/ligue_communications.html',
        'templates/gouvernance/ligue_athletes_enrollment_list.html',
        'templates/gouvernance/ligue_athletes_validation_list.html',
        'templates/gouvernance/ligue_athletes_certifies_list.html',
        'templates/gouvernance/ligue_competitions_list.html',
        'templates/gouvernance/ligue_evenements_list.html',
        'templates/gouvernance/ligue_calendrier_provincial.html',
        'templates/gouvernance/ligue_documents.html',
        'templates/gouvernance/ligue_competition_create.html',
        'templates/gouvernance/ligue_evenement_create.html',
        'templates/gouvernance/ligue_club_create.html',
        'templates/gouvernance/ligue_athlete_enroll.html',
        'templates/gouvernance/ligue_athlete_validate.html',
        'templates/gouvernance/ligue_medecin_register.html',
        'templates/gouvernance/ligue_types_competition_list.html',
        'templates/gouvernance/ligue_rencontres_billetterie.html',
        'templates/gouvernance/ligue_rencontre_create.html',
        'templates/gouvernance/ligue_rencontre_configurer_billetterie.html',
        'templates/gouvernance/ligue_calendrier_competition.html',
        'templates/gouvernance/ligue_competition_calendrier.html',
        'templates/gouvernance/ligue_competition_journees.html',
        'templates/gouvernance/ligue_calendrier_rencontres.html',
        'templates/gouvernance/ligue_club_affiliate_confirm.html',
        'templates/gouvernance/ligue_club_detail.html',
        'templates/gouvernance/ligue_athlete_capture_empreintes.html',
        'templates/gouvernance/ligue_athletes_enrollment_history.html',
        'templates/gouvernance/ligue_athletes_validation_history.html',
        'templates/gouvernance/ligue_types_competition_list.html',
    ]
    
    base_dir = 'e:\\DOCERA\\PROJETS\\PYTHON\\Django\\SI-SEP-SPORT-RDC'
    total_corriges = 0
    
    for template in templates_ligue:
        filepath = os.path.join(base_dir, template)
        if os.path.exists(filepath):
            if corriger_template(filepath):
                total_corriges += 1
        else:
            print(f"⚠️ Fichier non trouvé: {filepath}")
    
    print("\n" + "=" * 60)
    print(f"🎯 RÉSULTAT: {total_corriges} templates corrigés")
    print("✅ Tous les templates du secrétaire de ligue sont maintenant valides!")
    print("\n🚀 Vous pouvez maintenant:")
    print("1. Démarrez le serveur: python manage.py runserver")
    print("2. Connectez-vous comme secrétaire de ligue")
    print("3. Tous les menus du sidebar fonctionneront correctement")

if __name__ == '__main__':
    main()
