#!/usr/bin/env python
"""Script de diagnostic pour vérifier les fédérations"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gouvernance.models import Institution

print("=== DIAGNOSTIC DES FÉDÉRATIONS ===\n")

# Toutes les fédérations
feds = Institution.objects.filter(niveau_territorial='FEDERATION')
print(f"Total fédérations: {feds.count()}")

# Fédérations avec statut_signature='SIGNE'
feds_signe = feds.filter(statut_signature='SIGNE')
print(f"Fédérations SIGNE: {feds_signe.count()}")

# Fédérations avec statut_activation='ACTIVE'
feds_active = feds.filter(statut_activation='ACTIVE')
print(f"Fédérations ACTIVE: {feds_active.count()}")

# Fédérations SIGNE + ACTIVE
feds_signe_active = feds.filter(statut_signature='SIGNE', statut_activation='ACTIVE')
print(f"Fédérations SIGNE + ACTIVE: {feds_signe_active.count()}")

print("\n=== DÉTAILS DES FÉDÉRATIONS ===")
for f in feds:
    print(f"\n{f.nom_officiel} ({f.code})")
    print(f"  - statut_signature: '{f.statut_signature}'")
    print(f"  - statut_activation: '{f.statut_activation}'")
    print(f"  - type_institution.code: '{f.type_institution.code}'")
    print(f"  - institution_tutelle: {f.institution_tutelle}")

# Vérifier le ministère
ministere = Institution.objects.filter(institution_tutelle__isnull=True).first()
if ministere:
    print(f"\n=== MINISTÈRE ===")
    print(f"Nom: {ministere.nom_officiel}")
    print(f"UID: {ministere.uid}")
    
    # Fédérations enfants du ministère
    feds_ministere = Institution.objects.filter(
        institution_tutelle=ministere,
        type_institution__code='FEDERATION'
    )
    print(f"\nFédérations enfants du ministère: {feds_ministere.count()}")
    
    feds_ministere_signe = feds_ministere.filter(
        statut_signature='SIGNE',
        statut_activation='ACTIVE'
    )
    print(f"Fédérations enfants SIGNE + ACTIVE: {feds_ministere_signe.count()}")
