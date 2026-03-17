"""
Script de test pour la génération de licence sportive avec templates
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gouvernance.models import Athlete
from gouvernance.licence_generator import generer_licence_sportive_id1


def test_licence_generation():
    """
    Test de génération de licence avec les templates recto/verso
    """
    print("=" * 60)
    print("TEST DE GÉNÉRATION DE LICENCE SPORTIVE")
    print("=" * 60)
    
    # Vérifier que les templates existent
    from django.conf import settings
    base_dir = settings.BASE_DIR
    recto_path = os.path.join(base_dir, 'licence_fichier', 'recto.png')
    verso_path = os.path.join(base_dir, 'licence_fichier', 'verso.png')
    
    print("\n1. Vérification des templates:")
    print(f"   - Recto: {recto_path}")
    print(f"     Existe: {'✓' if os.path.exists(recto_path) else '✗'}")
    print(f"   - Verso: {verso_path}")
    print(f"     Existe: {'✓' if os.path.exists(verso_path) else '✗'}")
    
    # Récupérer un athlète certifié
    print("\n2. Recherche d'un athlète certifié:")
    athletes = Athlete.objects.filter(
        statut_certification='CERTIFIE_NATIONAL'
    ).select_related('personne', 'club', 'discipline')
    
    if not athletes.exists():
        print("   ✗ Aucun athlète certifié trouvé")
        print("   Recherche d'un athlète quelconque...")
        athletes = Athlete.objects.all().select_related('personne', 'club', 'discipline')
    
    if not athletes.exists():
        print("   ✗ Aucun athlète trouvé dans la base de données")
        return
    
    athlete = athletes.first()
    print(f"   ✓ Athlète trouvé: {athlete.nom_complet}")
    print(f"     - Numéro sportif: {athlete.numero_sportif}")
    print(f"     - Discipline: {athlete.discipline.designation if athlete.discipline else 'N/A'}")
    print(f"     - Club: {athlete.club.nom_officiel if athlete.club else 'N/A'}")
    print(f"     - Photo: {'✓' if athlete.personne and athlete.personne.photo else '✗'}")
    
    # Générer la licence
    print("\n3. Génération de la licence:")
    try:
        licence_pdf = generer_licence_sportive_id1(athlete, base_url='http://127.0.0.1:8000')
        print(f"   ✓ Licence générée avec succès")
        print(f"     - Nom fichier: {licence_pdf.name}")
        print(f"     - Taille: {len(licence_pdf.read())} bytes")
        
        # Sauvegarder la licence
        athlete.licence_pdf = licence_pdf
        athlete.save()
        print(f"   ✓ Licence sauvegardée dans le modèle")
        print(f"     - Chemin: {athlete.licence_pdf.path if athlete.licence_pdf else 'N/A'}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors de la génération: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("TEST TERMINÉ AVEC SUCCÈS")
    print("=" * 60)


if __name__ == '__main__':
    test_licence_generation()
