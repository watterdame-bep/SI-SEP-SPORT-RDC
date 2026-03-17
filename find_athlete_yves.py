"""
Script pour trouver l'athlète LUTU MULUMBA Yves
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gouvernance.models import Athlete

# Rechercher l'athlète
athletes = Athlete.objects.filter(
    personne__nom__icontains='LUTU',
    personne__postnom__icontains='MULUMBA',
    personne__prenom__icontains='Yves'
).select_related('personne', 'club', 'discipline')

print(f"Athlètes trouvés: {athletes.count()}\n")

for athlete in athletes:
    print(f"UID: {athlete.uid}")
    print(f"Nom complet: {athlete.nom_complet}")
    print(f"Numéro sportif: {athlete.numero_sportif}")
    print(f"Discipline: {athlete.discipline.designation if athlete.discipline else 'N/A'}")
    print(f"Club: {athlete.club.nom_officiel if athlete.club else 'N/A'}")
    print(f"Statut: {athlete.get_statut_certification_display()}")
    print("-" * 70)
