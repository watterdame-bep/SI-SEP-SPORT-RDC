#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour tester la redirection vers la page de succès après paiement validé
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Vente, Ticket
from gouvernance.models import Rencontre
from infrastructures.models import EvenementZone
import json

def test_payment_redirect():
    """Tester la redirection pour le paiement validé récent"""
    
    # Récupérer le paiement validé récent
    reference = '94qotgMn36g5243840690816-SISEP-ecf3fac4-1773727207'
    
    try:
        vente = Vente.objects.get(reference_paiement=reference)
        print(f"✅ Vente trouvée: {vente.uid}")
        print(f"   Référence: {vente.reference_paiement}")
        print(f"   Acheteur: {vente.acheteur_nom} ({vente.acheteur_telephone})")
        print(f"   Montant: {vente.montant_total} {vente.devise}")
        print(f"   Date: {vente.date_vente}")
        
        # Vérifier les notes
        notes_data = json.loads(vente.notes) if vente.notes else {}
        statut_paiement = notes_data.get('statut_paiement', 'INITIE')
        print(f"\n📊 Statut paiement: {statut_paiement}")
        
        # Vérifier les tickets
        tickets_vendus = vente.tickets.filter(statut='VENDU')
        print(f"🎫 Tickets VENDU: {tickets_vendus.count()}")
        
        for ticket in tickets_vendus:
            print(f"   - Ticket {ticket.uid}: {ticket.evenement_zone.zone_stade.nom}")
        
        # Vérifier les données d'achat
        purchase_data = notes_data.get('purchase_data', {})
        print(f"\n📦 Purchase data présent: {'Oui' if purchase_data else 'Non'}")
        
        if purchase_data:
            print(f"   - rencontre_uid: {purchase_data.get('rencontre_uid', 'N/A')}")
            print(f"   - zone_tarif_uid: {purchase_data.get('zone_tarif_uid', 'N/A')}")
            print(f"   - quantity: {purchase_data.get('quantity', 'N/A')}")
            print(f"   - nom: {purchase_data.get('nom', 'N/A')}")
            print(f"   - telephone: {purchase_data.get('telephone', 'N/A')}")
            print(f"   - email: {purchase_data.get('email', 'N/A')}")
            print(f"   - total: {purchase_data.get('total', 'N/A')}")
            
            # Vérifier que les objets existent
            try:
                rencontre = Rencontre.objects.get(uid=purchase_data['rencontre_uid'])
                print(f"\n✅ Rencontre trouvée: {rencontre.equipe_a.nom_officiel} vs {rencontre.equipe_b.nom_officiel}")
                print(f"   Date: {rencontre.date_heure}")
                print(f"   Stade: {rencontre.stade.nom}")
            except Exception as e:
                print(f"\n❌ Erreur rencontre: {e}")
            
            try:
                zone = EvenementZone.objects.get(uid=purchase_data['zone_tarif_uid'])
                print(f"✅ Zone trouvée: {zone.zone_stade.nom}")
                print(f"   Prix: {zone.prix_unitaire} CDF")
            except Exception as e:
                print(f"❌ Erreur zone: {e}")
        
        # Simuler la création de session payment_success
        print(f"\n🔄 Simulation de la session payment_success:")
        
        if statut_paiement == 'VALIDE' and purchase_data and tickets_vendus.count() > 0:
            rencontre = Rencontre.objects.get(uid=purchase_data['rencontre_uid'])
            zone = EvenementZone.objects.get(uid=purchase_data['zone_tarif_uid'])
            tickets_list = list(tickets_vendus)
            
            session_data = {
                'vente_uid': str(vente.uid),
                'reference': vente.reference_paiement,
                'nom': purchase_data['nom'],
                'telephone': purchase_data['telephone'],
                'email': purchase_data.get('email', ''),
                'quantity': purchase_data['quantity'],
                'total': float(purchase_data['total']),
                'payment_method': notes_data.get('methode_paiement', 'Mobile Money'),
                'zone_nom': zone.zone_stade.nom,
                'rencontre': f"{rencontre.equipe_a.nom_officiel} vs {rencontre.equipe_b.nom_officiel}",
                'date_match': rencontre.date_heure.strftime('%d/%m/%Y à %H:%M'),
                'stade': rencontre.stade.nom,
                'tickets': [
                    {
                        'uid': str(ticket.uid),
                        'numero': ticket.numero_billet or str(ticket.uid)[:8],
                        'qr_url': f"/verify/ticket/{ticket.uid}/"
                    }
                    for ticket in tickets_list
                ]
            }
            
            print(f"✅ Session payment_success créée avec succès:")
            print(f"   - Référence: {session_data['reference']}")
            print(f"   - Rencontre: {session_data['rencontre']}")
            print(f"   - Zone: {session_data['zone_nom']}")
            print(f"   - Tickets: {len(session_data['tickets'])}")
            print(f"\n✅ La redirection vers /paiement/succes/ devrait fonctionner!")
        else:
            print(f"❌ Impossible de créer la session:")
            print(f"   - Statut: {statut_paiement}")
            print(f"   - Purchase data: {'Oui' if purchase_data else 'Non'}")
            print(f"   - Tickets: {tickets_vendus.count()}")
        
    except Vente.DoesNotExist:
        print(f"❌ Vente non trouvée: {reference}")
    except Exception as e:
        import traceback
        print(f"❌ Erreur: {e}")
        print(traceback.format_exc())

if __name__ == '__main__':
    test_payment_redirect()
