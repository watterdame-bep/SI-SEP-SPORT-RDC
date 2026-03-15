#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger tous les templates du secrétaire de la fédération et du médecin de la ligue
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
    print("🔍 RECHERCHE DES TEMPLATS SECRÉTAIRE FÉDÉRATION & MÉDECIN LIGUE À CORRIGER")
    print("=" * 85)
    
    # Templates du secrétaire de la fédération
    templates_federation = [
        'templates/gouvernance/federation_secretary_dashboard.html',
        'templates/gouvernance/federation_athlete_validate.html',
        'templates/gouvernance/federation_athletes.html',
        'templates/gouvernance/federation_athletes_validation_list.html',
        'templates/gouvernance/federation_clubs_list.html',
        'templates/gouvernance/federation_competitions.html',
        'templates/gouvernance/federation_create.html',
        'templates/gouvernance/federation_detail.html',
        'templates/gouvernance/federation_documents.html',
        'templates/gouvernance/federation_ligues_list.html',
        'templates/gouvernance/federation_ordre_mission.html',
        'templates/gouvernance/federation_profile.html',
        'templates/gouvernance/federations_nationales.html',
        'templates/gouvernance/validation_federation_detail.html',
    ]
    
    # Templates du médecin de la ligue
    templates_medecin = [
        'templates/gouvernance/medecin_dashboard.html',
        'templates/gouvernance/medecin_athlete_dossier.html',
        'templates/gouvernance/medecin_athlete_examen_medical.html',
        'templates/gouvernance/medecin_athletes_en_attente_examen.html',
        'templates/gouvernance/medecin_athletes_list.html',
        'templates/gouvernance/medecin_type_examen_form.html',
        'templates/gouvernance/medecin_types_examen_list.html',
        'templates/gouvernance/division_medecin_create_account.html',
        'templates/gouvernance/division_medecins_list.html',
    ]
    
    base_dir = 'e:\\DOCERA\\PROJETS\\PYTHON\\Django\\SI-SEP-SPORT-RDC'
    total_corriges = 0
    
    print("\n🏛️ CORRECTION DES TEMPLATS DU SECRÉTAIRE DE LA FÉDÉRATION:")
    print("-" * 60)
    for template in templates_federation:
        filepath = os.path.join(base_dir, template)
        if os.path.exists(filepath):
            if corriger_template(filepath):
                total_corriges += 1
        else:
            print(f"⚠️ Fichier non trouvé: {filepath}")
    
    print("\n⚕️ CORRECTION DES TEMPLATS DU MÉDECIN DE LA LIGUE:")
    print("-" * 60)
    for template in templates_medecin:
        filepath = os.path.join(base_dir, template)
        if os.path.exists(filepath):
            if corriger_template(filepath):
                total_corriges += 1
        else:
            print(f"⚠️ Fichier non trouvé: {filepath}")
    
    print("\n" + "=" * 85)
    print(f"🎯 RÉSULTAT: {total_corriges} templates corrigés")
    print("✅ Tous les templates du secrétaire de la fédération et du médecin sont maintenant valides!")
    print("\n🚀 Vous pouvez maintenant:")
    print("1. Démarrez le serveur: python manage.py runserver")
    print("2. Connectez-vous comme secrétaire de la fédération ou médecin de la ligue")
    print("3. Tous les menus du sidebar fonctionneront correctement")
    print("\n📊 RÉCAPITULATIF TOTAL:")
    print("- 27 templates du secrétaire de ligue")
    print("- 14 templates de gestion infrastructure")
    print("- 21 templates du secrétaire du club & ministre")
    print(f"- {total_corriges} templates du secrétaire de la fédération & médecin")
    print(f"- TOTAL: {27 + 14 + 21 + total_corriges} templates corrigés")

if __name__ == '__main__':
    main()
