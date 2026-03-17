#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de l'API de statut de paiement en temps réel
"""

import os
import sys
import django

# Ajouter le projet au path Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Vente
import json

def test_payment_status_api():
    """Test de l'API de statut de paiement"""
    print("🧪 TEST DE L'API STATUT PAIEMENT")
    print("=" * 40)
    
    # Récupérer toutes les ventes
    ventes = Vente.objects.all().order_by('-date_vente')[:5]
    
    if not ventes:
        print("❌ Aucune vente trouvée dans la base de données")
        return
    
    print(f"📊 {ventes.count()} vente(s) trouvée(s)")
    print()
    
    for vente in ventes:
        print(f"🎫 VENTE: {vente.reference_paiement}")
        print(f"   UID: {vente.uid}")
        print(f"   Date: {vente.date_vente}")
        print(f"   Montant: {vente.montant_total} CDF")
        
        # Analyser les notes
        if vente.notes:
            try:
                notes_data = json.loads(vente.notes)
                statut_paiement = notes_data.get('statut_paiement', 'INITIE')
                raison_echec = notes_data.get('raison_echec', '')
                message_erreur = notes_data.get('message_erreur', '')
                
                print(f"   Statut: {statut_paiement}")
                if raison_echec:
                    print(f"   Raison échec: {raison_echec}")
                if message_erreur:
                    print(f"   Message erreur: {message_erreur}")
                    
                # Simuler la réponse de l'API
                api_response = {
                    'success': True,
                    'status': statut_paiement,
                    'reference': vente.reference_paiement
                }
                
                if statut_paiement in ['ECHOUE', 'SOLDE_INSUFFISANT']:
                    api_response['reason'] = raison_echec or 'autre_erreur'
                    api_response['detail'] = message_erreur or 'Paiement échoué'
                
                print(f"   🔗 Réponse API: {json.dumps(api_response, indent=6)}")
                
            except json.JSONDecodeError:
                print("   ⚠️ Erreur de parsing des notes (JSON invalide)")
        else:
            print("   📝 Aucune notes enregistrées")
        
        print("-" * 40)

if __name__ == '__main__':
    test_payment_status_api()
