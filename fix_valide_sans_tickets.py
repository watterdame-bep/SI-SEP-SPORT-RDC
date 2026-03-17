"""
Corrige les ventes VALIDE qui n'ont pas de tickets VENDU.
Utilise la même logique que _creer_tickets_depuis_purchase_data dans views.py.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Vente, Ticket, EvenementZone
from django.db import transaction
import json

ventes = Vente.objects.filter(canal='MOBILE_MONEY').order_by('-date_vente')
fixed = 0

for v in ventes:
    notes = json.loads(v.notes) if v.notes else {}
    statut = notes.get('statut_paiement', 'N/A')
    if statut != 'VALIDE':
        continue

    tickets_vendu = Ticket.objects.filter(vente=v, statut='VENDU').count()
    if tickets_vendu > 0:
        print(f"OK: Vente {v.uid} - {tickets_vendu} tickets VENDU")
        continue

    print(f"FIX: Vente {v.uid} - aucun ticket VENDU")

    purchase_data = notes.get('purchase_data', {})
    zone_uid = purchase_data.get('zone_tarif_uid')
    quantity = int(purchase_data.get('quantity', 1))
    zone = None

    # Essai 1: via purchase_data
    if zone_uid:
        try:
            zone = EvenementZone.objects.get(uid=zone_uid)
            print(f"  Zone via purchase_data: {zone.zone_stade.nom}")
        except EvenementZone.DoesNotExist:
            zone = None

    # Essai 2: via l'evenement de la vente
    if zone is None:
        zones = EvenementZone.objects.filter(evenement=v.evenement)
        if zones.exists():
            zone = zones.first()
            if zone.prix_unitaire and zone.prix_unitaire > 0:
                quantity = max(1, int(float(v.montant_total) / float(zone.prix_unitaire)))
            print(f"  Zone via evenement: {zone.zone_stade.nom}, quantité estimée: {quantity}")

    if zone is None:
        print(f"  SKIP: Impossible de trouver une zone")
        continue

    with transaction.atomic():
        # Chercher tickets EN_RESERVATION liés à cette vente
        tickets_reserve = list(Ticket.objects.filter(vente=v, statut='EN_RESERVATION').select_for_update()[:quantity])
        if tickets_reserve:
            for t in tickets_reserve:
                t.statut = 'VENDU'
                t.save()
            print(f"  -> {len(tickets_reserve)} tickets EN_RESERVATION → VENDU")
        else:
            # Chercher tickets DISPONIBLE dans la zone
            tickets_dispo = list(Ticket.objects.filter(evenement_zone=zone, statut='DISPONIBLE').select_for_update()[:quantity])
            if tickets_dispo:
                for t in tickets_dispo:
                    t.statut = 'VENDU'
                    t.vente = v
                    t.save()
                print(f"  -> {len(tickets_dispo)} tickets DISPONIBLE → VENDU")
            else:
                # Créer de nouveaux tickets
                for _ in range(quantity):
                    t = Ticket.objects.create(evenement_zone=zone, vente=v, statut='VENDU')
                    print(f"  -> Nouveau ticket créé: {t.numero_billet}")

    fixed += 1

print(f"\nTotal ventes corrigées: {fixed}")
