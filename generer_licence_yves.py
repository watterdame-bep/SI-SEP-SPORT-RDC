"""
Script pour générer la licence de LUTU MULUMBA Yves
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gouvernance.models import Athlete
from gouvernance.licence_generator_final import generer_licence_sportive_id1
from datetime import datetime, timedelta


def generer_licence_yves():
    """
    Génère la licence pour LUTU MULUMBA Yves
    """
    print("=" * 70)
    print("GÉNÉRATION DE LICENCE SPORTIVE - LUTU MULUMBA Yves")
    print("=" * 70)
    
    try:
        # Rechercher l'athlète par nom
        athletes = Athlete.objects.filter(
            personne__nom__icontains='LUTU',
            personne__prenom__icontains='Yves'
        ).select_related('personne', 'club', 'discipline')
        
        if not athletes.exists():
            # Essayer avec MULUMBA
            athletes = Athlete.objects.filter(
                personne__postnom__icontains='MULUMBA',
                personne__prenom__icontains='Yves'
            ).select_related('personne', 'club', 'discipline')
        
        if not athletes.exists():
            print("\n✗ Aucun athlète trouvé avec le nom LUTU MULUMBA Yves")
            print("\nRecherche de tous les athlètes avec 'Yves'...")
            athletes = Athlete.objects.filter(
                personne__prenom__icontains='Yves'
            ).select_related('personne', 'club', 'discipline')
            
            if athletes.exists():
                print(f"\n{athletes.count()} athlète(s) trouvé(s) avec 'Yves':")
                for idx, a in enumerate(athletes, 1):
                    print(f"  {idx}. {a.nom_complet} - {a.numero_sportif}")
                athlete = athletes.first()
                print(f"\nUtilisation du premier: {athlete.nom_complet}")
            else:
                print("\n✗ Aucun athlète trouvé")
                return
        else:
            athlete = athletes.first()
        
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
        print("✓ GÉNÉRATION TERMINÉE AVEC SUCCÈS")
        print("=" * 70)
        print(f"\nVous pouvez maintenant télécharger la licence depuis:")
        print(f"http://127.0.0.1:8000{athlete.licence_pdf.url}")
        
    except Exception as e:
        print(f"\n✗ ERREUR lors de la génération: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    generer_licence_yves()
