#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test du formatage des numéros de téléphone pour FlexPay
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

def test_formatage_telephone():
    """Teste le formatage des numéros de téléphone"""
    processor = MobileMoneyPaymentProcessor()
    
    # Cas de test
    tests = [
        "+243840690816",  # Numéro international avec +
        "243840690816",   # Numéro international sans +
        "0840690816",     # Numéro local correct
        "840690816",      # Numéro local sans 0
        "+243 840 690 816",  # Numéro avec espaces
        "+243-840-690-816",  # Numéro avec tirets
        "123456789012345",  # Numéro trop long
    ]
    
    print("🧪 TEST DU FORMATAGE DES NUMÉROS DE TÉLÉPHONE")
    print("=" * 50)
    
    for telephone in tests:
        try:
            resultat = processor.formater_telephone(telephone)
            print(f"✅ {telephone} → {resultat}")
        except Exception as e:
            print(f"❌ {telephone} → ERREUR: {e}")
    
    print("\n🎯 RÉSULTAT:")
    print("Tous les numéros devraient être formatés en 0XXXXXXXXX (10 chiffres max)")

if __name__ == '__main__':
    test_formatage_telephone()
