#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de l'API de nettoyage de session de paiement
"""

import os
import sys
import django

# Ajouter le projet au path Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.sessions.models import Session

def test_clear_payment_session():
    """Test de l'API de nettoyage de session"""
    print("🧪 TEST DE L'API NETTOYAGE SESSION")
    print("=" * 40)
    
    # Créer un client de test
    client = Client()
    
    # Simuler une session avec des données de paiement
    session = client.session
    session['vente_uid'] = 'test-vente-uid'
    session['order_number'] = 'test-order-123'
    session['payment_method'] = 'MOBILE_MONEY'
    session['purchase_data'] = {'test': 'data'}
    session['payment_pending'] = True
    session.save()
    
    print("📝 Session avant nettoyage:")
    print(f"   vente_uid: {session.get('vente_uid')}")
    print(f"   order_number: {session.get('order_number')}")
    print(f"   payment_method: {session.get('payment_method')}")
    print(f"   purchase_data: {session.get('purchase_data')}")
    print(f"   payment_pending: {session.get('payment_pending')}")
    
    # Tester l'API POST
    print("\n🔄 Appel de l'API /api/clear-payment-session/ (POST)...")
    response = client.post('/api/clear-payment-session/', 
                         content_type='application/json',
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    print(f"   Status code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Vérifier que la session a été nettoyée
    session_after = client.session
    print("\n✅ Session après nettoyage:")
    print(f"   vente_uid: {session_after.get('vente_uid')}")
    print(f"   order_number: {session_after.get('order_number')}")
    print(f"   payment_method: {session_after.get('payment_method')}")
    print(f"   purchase_data: {session_after.get('purchase_data')}")
    print(f"   payment_pending: {session_after.get('payment_pending')}")
    
    # Tester avec mauvaise méthode
    print("\n❌ Test avec mauvaise méthode (GET)...")
    response_get = client.get('/api/clear-payment-session/')
    print(f"   Status code: {response_get.status_code}")
    print(f"   Response: {response_get.json()}")
    
    # Vérifications
    success_conditions = [
        response.status_code == 200,
        response.json().get('success') == True,
        session_after.get('vente_uid') is None,
        session_after.get('order_number') is None,
        session_after.get('payment_method') is None,
        session_after.get('purchase_data') is None,
        session_after.get('payment_pending') is None,
        response_get.status_code == 405,
        not response_get.json().get('success')
    ]
    
    print(f"\n🎯 Résultats: {sum(success_conditions)}/{len(success_conditions)} tests passés")
    
    if all(success_conditions):
        print("✅ Tous les tests passés ! L'API de nettoyage fonctionne correctement.")
    else:
        print("❌ Certains tests ont échoué. Vérifiez l'implémentation.")
        
        for i, condition in enumerate(success_conditions, 1):
            status = "✅" if condition else "❌"
            print(f"   Test {i}: {status}")

if __name__ == '__main__':
    test_clear_payment_session()
