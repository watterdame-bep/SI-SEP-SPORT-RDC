#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug spécifique pour le formatage FlexPay avec le numéro exact qui pose problème
"""

import os
import sys
import django

# Ajouter le projet au path Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from public.mobile_money_integration import MobileMoneyPaymentProcessor

def debug_flexpay_format():
    """Debug spécifique pour le numéro 0840690816"""
    processor = MobileMoneyPaymentProcessor()
    
    # Test avec le numéro exact qui pose problème
    telephone_test = "0840690816"
    
    print("🔍 DEBUG SPÉCIFIQUE FLEXPAY")
    print("=" * 40)
    print(f"Numéro testé: {telephone_test}")
    print(f"Longueur: {len(telephone_test)}")
    
    # Test du formatage
    resultat = processor.formater_telephone(telephone_test)
    print(f"Résultat formatage: {resultat}")
    print(f"Longueur formaté: {len(resultat) if resultat else 'None'}")
    
    # Test des différents formats possibles
    formats_test = [
        telephone_test,           # 0840690816 (10 chiffres)
        telephone_test[1:],       # 840690816 (9 chiffres)
        "243" + telephone_test[1:], # 243840690816 (12 chiffres)
        "+243" + telephone_test[1:], # +243840690816 (13 chiffres)
    ]
    
    print("\n🧪 TEST DES DIFFÉRENTS FORMATS:")
    for i, format_test in enumerate(formats_test, 1):
        print(f"\nFormat {i}: {format_test}")
        try:
            format_result = processor.formater_telephone(format_test)
            print(f"  → Résultat: {format_result} (longueur: {len(format_result) if format_result else 'None'})")
        except Exception as e:
            print(f"  → Erreur: {e}")
    
    print("\n📋 RECOMMANDATION:")
    print("Si FlexPay rejette encore, essayer avec:")
    print("1. Format 9 chiffres: 840690816")
    print("2. Format 10 chiffres sans 0: 840690816")
    print("3. Vérifier la documentation FlexPay pour RDC")

if __name__ == '__main__':
    debug_flexpay_format()
