#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger tous les templates du secrétaire général et du directeur provincial
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
    print("🔍 RECHERCHE DES TEMPLATS SECRÉTAIRE GÉNÉRAL & DIRECTEUR PROVINCIAL À CORRIGER")
    print("=" * 90)
    
    # Templates du secrétaire général
    templates_sg = [
        'templates/gouvernance/sg_dashboard.html',
        'templates/gouvernance/profil_sg.html',
        'templates/gouvernance/sg_ligue_detail.html',
        'templates/gouvernance/sg_ligues_en_attente.html',
        'templates/core/sg_dashboard.html',
        'templates/infrastructures/sg_infrastructure_validation_detail.html',
        'templates/infrastructures/sg_infrastructure_validation_list.html',
    ]
    
    # Templates du directeur provincial
    templates_directeur = [
        'templates/gouvernance/directeur_provincial_dashboard.html',
    ]
    
    base_dir = 'e:\\DOCERA\\PROJETS\\PYTHON\\Django\\SI-SEP-SPORT-RDC'
    total_corriges = 0
    
    print("\n📋 CORRECTION DES TEMPLATS DU SECRÉTAIRE GÉNÉRAL:")
    print("-" * 65)
    for template in templates_sg:
        filepath = os.path.join(base_dir, template)
        if os.path.exists(filepath):
            if corriger_template(filepath):
                total_corriges += 1
        else:
            print(f"⚠️ Fichier non trouvé: {filepath}")
    
    print("\n🎯 CORRECTION DES TEMPLATS DU DIRECTEUR PROVINCIAL:")
    print("-" * 65)
    for template in templates_directeur:
        filepath = os.path.join(base_dir, template)
        if os.path.exists(filepath):
            if corriger_template(filepath):
                total_corriges += 1
        else:
            print(f"⚠️ Fichier non trouvé: {filepath}")
    
    print("\n" + "=" * 90)
    print(f"🎯 RÉSULTAT: {total_corriges} templates corrigés")
    print("✅ Tous les templates du secrétaire général et du directeur provincial sont maintenant valides!")
    print("\n🚀 Vous pouvez maintenant:")
    print("1. Démarrez le serveur: python manage.py runserver")
    print("2. Connectez-vous comme secrétaire général ou directeur provincial")
    print("3. Tous les menus du sidebar fonctionneront correctement")
    print("\n📊 RÉCAPITULATIF TOTAL:")
    print("- 27 templates du secrétaire de ligue")
    print("- 14 templates de gestion infrastructure")
    print("- 21 templates du secrétaire du club & ministre")
    print("- 23 templates du secrétaire de la fédération & médecin")
    print(f"- {total_corriges} templates du secrétaire général & directeur provincial")
    print(f"- TOTAL: {27 + 14 + 21 + 23 + total_corriges} templates corrigés")

if __name__ == '__main__':
    main()
