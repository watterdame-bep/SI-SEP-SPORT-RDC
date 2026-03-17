"""
Script pour régénérer la licence d'un athlète spécifique
Usage: python regenerer_licence_athlete.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gouvernance.models import Athlete
from gouvernance.licence_generator_final import generer_licence_sportive_id1
from datetime import datetime, timedelta


def regenerer_licence_athlete(athlete_uid):
    """
    Régénère la licence pour un athlète spécifique
    """
    print("=" * 70)
    print("RÉGÉNÉRATION DE LICENCE SPORTIVE")
    print("=" * 70)
    
    try:
        # Récupérer l'athlète
        athlete = Athlete.objects.select_related(
            'personne', 'club', 'discipline'
        ).get(uid=athlete_uid)
        
        print(f"\n✓ Athlète trouvé:")
        print(f"  - UID: {athlete.uid}")
        print(f"  - Nom: {athlete.nom_complet}")
        print(f"  - Numéro sportif: {athlete.numero_sportif}")
        print(f"  - Discipline: {athlete.discipline.designation if athlete.discipline else 'N/A'}")
        print(f"  - Club: {athlete.club.nom_officiel if athlete.club else 'N/A'}")
        print(f"  - Statut: {athlete.get_statut_certification_display()}")
        
        if athlete.personne:
            print(f"  - Photo: {'✓ Présente' if athlete.personne.photo else '✗ Absente'}")
            if athlete.personne.date_naissance:
                print(f"  - Date naissance: {athlete.personne.date_naissance.strftime('%d/%m/%Y')}")
        
        # Vérifier/définir les dates de licence
        if not athlete.date_emission_licence:
            athlete.date_emission_licence = datetime.now().date()
            print(f"\n  → Date d'émission définie: {athlete.date_emission_licence}")
        
        if not athlete.date_expiration_licence:
            athlete.date_expiration_licence = athlete.date_emission_licence + timedelta(days=365)
            print(f"  → Date d'expiration définie: {athlete.date_expiration_licence}")
        
        if not athlete.numero_licence:
            athlete.numero_licence = athlete.numero_sportif
            print(f"  → Numéro de licence défini: {athlete.numero_licence}")
        
        athlete.save()
        
        # Générer la licence
        print(f"\n⏳ Génération de la licence en cours...")
        licence_pdf = generer_licence_sportive_id1(athlete, base_url='http://127.0.0.1:8000')
        
        print(f"✓ Licence générée avec succès!")
        print(f"  - Nom fichier: {licence_pdf.name}")
        print(f"  - Taille: {len(licence_pdf.read())} bytes")
        
        # Sauvegarder la licence
        athlete.licence_pdf = licence_pdf
        athlete.save()
        
        print(f"\n✓ Licence sauvegardée dans le modèle")
        if athlete.licence_pdf:
            print(f"  - Chemin: {athlete.licence_pdf.path}")
            print(f"  - URL: {athlete.licence_pdf.url}")
        
        print("\n" + "=" * 70)
        print("✓ RÉGÉNÉRATION TERMINÉE AVEC SUCCÈS")
        print("=" * 70)
        print(f"\nVous pouvez maintenant télécharger la licence depuis:")
        print(f"http://127.0.0.1:8000{athlete.licence_pdf.url}")
        
    except Athlete.DoesNotExist:
        print(f"\n✗ ERREUR: Aucun athlète trouvé avec l'UID: {athlete_uid}")
        print("\nVérifiez que l'UID est correct (format: 05e81e43d1024e69bf60f247eb732244)")
        
    except Exception as e:
        print(f"\n✗ ERREUR lors de la génération: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # UID de l'athlète à régénérer
    athlete_uid = "79327360-e89f-4ee0-ade6-f4bf2dae0331"  # LUTU MULUMBA Yves
    
    print(f"\nRégénération de la licence pour l'athlète: {athlete_uid}\n")
    regenerer_licence_athlete(athlete_uid)
