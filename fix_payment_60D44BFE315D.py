#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger manuellement le paiement PAY-60D44BFE315D
qui a été validé sur FlexPay mais marqué comme échoué à cause d'un timeout
"""

import os
import sys
import django
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Vente, Ticket
from django.db import transaction
from django.utils import timezone

def fix_payment():
    """Corriger le paiement et valider les tickets"""
    
    # Trouver la vente
    vente = Vente.objects.filter(reference_paiement__contains='PAY-60D44BFE315D').first()
    
    if not vente:
        print("❌ Vente non trouvée")
        return
    
    print(f"✓ Vente trouvée: {vente.uid}")
    print(f"  - Référence: {vente.reference_paiement}")
    print(f"  - Montant: {vente.montant_total} CDF")
    print(f"  - Acheteur: {vente.acheteur_nom} ({vente.acheteur_telephone})")
    
    # Récupérer les notes
    notes_data = json.loads(vente.notes) if vente.notes else {}
    print(f"\n📋 Statut actuel: {notes_data.get('statut_paiement', 'INCONNU')}")
    
    # Récupérer les tickets réservés
    tickets_reserves_uids = notes_data.get('tickets_reserves', [])
    print(f"🎫 Tickets réservés: {len(tickets_reserves_uids)}")
    
    if not tickets_reserves_uids:
        print("❌ Aucun ticket réservé trouvé dans les notes")
        return
    
    # Vérifier l'état des tickets
    tickets = Ticket.objects.filter(uid__in=tickets_reserves_uids)
    print(f"\n📊 État des tickets:")
    for ticket in tickets:
        print(f"  - {ticket.uid}: {ticket.statut}")
    
    # Demander confirmation
    print(f"\n⚠️  ATTENTION: Cette opération va:")
    print(f"  1. Marquer le paiement comme VALIDE")
    print(f"  2. Convertir {len(tickets_reserves_uids)} ticket(s) de EN_RESERVATION vers VENDU")
    print(f"  3. Lier les tickets à la vente")
    
    confirmation = input("\n❓ Confirmer la validation du paiement? (oui/non): ")
    
    if confirmation.lower() != 'oui':
        print("❌ Opération annulée")
        return
    
    # Valider le paiement
    with transaction.atomic():
        # Mettre à jour le statut du paiement
        notes_data['statut_paiement'] = 'VALIDE'
        notes_data['date_validation'] = timezone.now().isoformat()
        notes_data['validation_manuelle'] = True
        notes_data['validation_manuelle_raison'] = 'Timeout FlexPay mais paiement réussi'
        vente.notes = json.dumps(notes_data)
        vente.save()
        
        print(f"\n✓ Statut de la vente mis à jour: VALIDE")
        
        # Mettre à jour les tickets
        count_updated = 0
        for ticket_uid in tickets_reserves_uids:
            try:
                ticket = Ticket.objects.get(uid=ticket_uid)
                if ticket.statut == 'EN_RESERVATION':
                    ticket.statut = 'VENDU'
                    ticket.vente = vente
                    ticket.save()
                    count_updated += 1
                    print(f"  ✓ Ticket {ticket.uid}: EN_RESERVATION → VENDU")
                elif ticket.statut == 'DISPONIBLE':
                    ticket.statut = 'VENDU'
                    ticket.vente = vente
                    ticket.save()
                    count_updated += 1
                    print(f"  ✓ Ticket {ticket.uid}: DISPONIBLE → VENDU")
                else:
                    print(f"  ⚠️  Ticket {ticket.uid}: déjà {ticket.statut}")
            except Ticket.DoesNotExist:
                print(f"  ❌ Ticket {ticket_uid} non trouvé")
        
        print(f"\n✅ {count_updated} ticket(s) validé(s)")
    
    # Afficher le résumé
    print(f"\n" + "="*60)
    print(f"✅ PAIEMENT VALIDÉ AVEC SUCCÈS")
    print(f"="*60)
    print(f"Vente UID: {vente.uid}")
    print(f"Référence: {vente.reference_paiement}")
    print(f"Montant: {vente.montant_total} CDF")
    print(f"Tickets vendus: {count_updated}")
    print(f"\n💡 L'utilisateur peut maintenant accéder à ses billets")
    print(f"   via la page de succès ou en rechargeant la page d'attente")

if __name__ == '__main__':
    fix_payment()
