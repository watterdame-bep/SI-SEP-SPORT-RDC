#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour valider le paiement en cours PAY-5448045EBF82
"""

import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Vente, Ticket
from django.db import transaction
from django.utils import timezone

# Trouver la vente
vente = Vente.objects.filter(reference_paiement__contains='PAY-5448045EBF82').first()

if not vente:
    print("❌ Vente non trouvée")
    sys.exit(1)

print(f"✓ Vente trouvée: {vente.uid}")
print(f"  Référence: {vente.reference_paiement}")
print(f"  Acheteur: {vente.acheteur_nom} ({vente.acheteur_telephone})")

# Récupérer les notes
notes_data = json.loads(vente.notes) if vente.notes else {}
tickets_reserves_uids = notes_data.get('tickets_reserves', [])

print(f"\n📋 Statut actuel: {notes_data.get('statut_paiement')}")
print(f"🎫 Tickets réservés: {len(tickets_reserves_uids)}")

# Valider le paiement
with transaction.atomic():
    # Mettre à jour le statut
    notes_data['statut_paiement'] = 'VALIDE'
    notes_data['date_validation'] = timezone.now().isoformat()
    notes_data['validation_manuelle'] = True
    notes_data['validation_manuelle_raison'] = 'Callback FlexPay non reçu - validation manuelle'
    vente.notes = json.dumps(notes_data)
    vente.save()
    
    print(f"\n✓ Statut mis à jour: VALIDE")
    
    # Mettre à jour les tickets
    count_updated = 0
    for ticket_uid in tickets_reserves_uids:
        try:
            ticket = Ticket.objects.get(uid=ticket_uid)
            ticket.statut = 'VENDU'
            ticket.vente = vente
            ticket.save()
            count_updated += 1
            print(f"  ✓ Ticket {ticket.uid}: VENDU")
        except Ticket.DoesNotExist:
            print(f"  ❌ Ticket {ticket_uid} non trouvé")
    
    print(f"\n✅ {count_updated} ticket(s) validé(s)")
    print(f"✅ PAIEMENT VALIDÉ")
    print(f"\n💡 L'utilisateur doit recharger la page d'attente pour voir ses billets")
