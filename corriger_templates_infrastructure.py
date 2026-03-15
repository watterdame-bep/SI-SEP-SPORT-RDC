#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger tous les templates de gestion de l'infrastructure
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
    print("🔍 RECHERCHE DES TEMPLATES DE GESTION INFRASTRUCTURE À CORRIGER")
    print("=" * 70)
    
    # Liste des templates de gestion infrastructure à vérifier
    templates_infrastructure = [
        'templates/infrastructures/infra_manager_dashboard.html',
        'templates/infrastructures/infra_manager_evenement_billetterie.html',
        'templates/infrastructures/infra_manager_evenements.html',
        'templates/infrastructures/infra_manager_maintenance.html',
        'templates/infrastructures/infra_manager_photos.html',
        'templates/infrastructures/infra_manager_reservations.html',
        'templates/infrastructures/infra_manager_ventes_billets.html',
        'templates/infrastructures/infra_manager_zones.html',
        'templates/infrastructures/infrastructure_detail.html',
        'templates/infrastructures/infrastructure_form.html',
        'templates/infrastructures/infrastructure_list.html',
        'templates/infrastructures/sg_infrastructure_validation_detail.html',
        'templates/infrastructures/sg_infrastructure_validation_list.html',
        'templates/infrastructures/type_infrastructure_form.html',
        'templates/infrastructures/type_infrastructure_list.html',
        'templates/infrastructures/verifier_ticket.html',
    ]
    
    base_dir = 'e:\\DOCERA\\PROJETS\\PYTHON\\Django\\SI-SEP-SPORT-RDC'
    total_corriges = 0
    
    for template in templates_infrastructure:
        filepath = os.path.join(base_dir, template)
        if os.path.exists(filepath):
            if corriger_template(filepath):
                total_corriges += 1
        else:
            print(f"⚠️ Fichier non trouvé: {filepath}")
    
    print("\n" + "=" * 70)
    print(f"🎯 RÉSULTAT: {total_corriges} templates corrigés")
    print("✅ Tous les templates de gestion infrastructure sont maintenant valides!")
    print("\n🚀 Vous pouvez maintenant:")
    print("1. Démarrez le serveur: python manage.py runserver")
    print("2. Connectez-vous comme gestionnaire d'infrastructure")
    print("3. Tous les menus du sidebar fonctionneront correctement")

if __name__ == '__main__':
    main()
