#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Vente
from django.utils import timezone
from datetime import timedelta

# Ventes des 10 dernières minutes
recent = timezone.now() - timedelta(minutes=10)
ventes = Vente.objects.filter(date_vente__gte=recent).order_by('-date_vente')

print(f"📊 Ventes récentes (10 dernières minutes): {ventes.count()}\n")

for i, v in enumerate(ventes[:5], 1):
    notes = json.loads(v.notes) if v.notes else {}
    statut = notes.get('statut_paiement', 'N/A')
    
    print(f"{i}. {v.reference_paiement}")
    print(f"   Statut: {statut}")
    print(f"   Acheteur: {v.acheteur_nom} ({v.acheteur_telephone})")
    print(f"   Montant: {v.montant_total} CDF")
    print(f"   Date: {v.date_vente}")
    
    if 'raison_echec' in notes:
        print(f"   ⚠️  Raison échec: {notes['raison_echec']}")
    if 'message_erreur' in notes:
        print(f"   ⚠️  Message: {notes['message_erreur']}")
    
    print()
