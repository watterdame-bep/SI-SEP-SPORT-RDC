#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test pour vérifier ce que FlexPay retourne comme statut
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from public.mobile_money_integration import MobileMoneyPaymentProcessor
from infrastructures.models import Vente
from django.utils import timezone
from datetime import timedelta

# Récupérer les ventes récentes avec order_number
recent = timezone.now() - timedelta(hours=1)
ventes = Vente.objects.filter(date_vente__gte=recent).order_by('-date_vente')

print("🔍 Recherche de ventes avec order_number...\n")

processor = MobileMoneyPaymentProcessor()

for vente in ventes[:5]:
    notes = json.loads(vente.notes) if vente.notes else {}
    order_number = notes.get('order_number')
    statut_local = notes.get('statut_paiement', 'N/A')
    
    print(f"📦 Vente: {vente.reference_paiement}")
    print(f"   Statut local: {statut_local}")
    print(f"   Order number: {order_number}")
    
    if order_number and order_number != vente.reference_paiement:
        print(f"   🔄 Vérification auprès de FlexPay...")
        
        try:
            resultat = processor.verifier_paiement(order_number)
            print(f"   📊 Résultat FlexPay:")
            print(f"      Success: {resultat.get('success')}")
            print(f"      Status: {resultat.get('status')}")
            print(f"      Message: {resultat.get('message', 'N/A')}")
            
            if resultat.get('transaction'):
                print(f"      Transaction: {json.dumps(resultat['transaction'], indent=8)}")
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
    else:
        print(f"   ⚠️  Pas d'order_number valide")
    
    print()
