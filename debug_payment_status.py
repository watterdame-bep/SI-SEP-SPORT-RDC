import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Vente, Ticket
import json

ventes = Vente.objects.filter(canal='MOBILE_MONEY').order_by('-date_vente')[:5]
for v in ventes:
    notes = json.loads(v.notes) if v.notes else {}
    statut = notes.get('statut_paiement', 'N/A')
    tickets_total = Ticket.objects.filter(vente=v).count()
    tickets_vendu = Ticket.objects.filter(vente=v, statut='VENDU').count()
    tickets_reserve = Ticket.objects.filter(vente=v, statut='EN_RESERVATION').count()
    tickets_reserves_uids = notes.get('tickets_reserves', [])
    purchase_data = notes.get('purchase_data', {})
    order_number = notes.get('order_number', 'N/A')
    print(f"--- Vente {v.uid} ---")
    print(f"  Date: {v.date_vente}")
    print(f"  Ref: {v.reference_paiement}")
    print(f"  Order number: {order_number}")
    print(f"  Statut notes: {statut}")
    print(f"  Tickets total: {tickets_total}, VENDU: {tickets_vendu}, EN_RESERVATION: {tickets_reserve}")
    print(f"  tickets_reserves dans notes: {len(tickets_reserves_uids)} UIDs")
    print(f"  purchase_data keys: {list(purchase_data.keys())}")
    email = purchase_data.get('email', 'ABSENT')
    print(f"  Email acheteur: {email}")
    print()
