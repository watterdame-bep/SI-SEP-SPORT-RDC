"""
Commande pour régénérer le certificat médical (F72) d'un athlète.
Usage: python manage.py regenerate_athlete_certificate "Nom de l'athlète"
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from gouvernance.models import Athlete, VisiteMedicale
from gouvernance.certificat_aptitude_generator import generer_certificat_aptitude_pdf


class Command(BaseCommand):
    help = "Régénère le certificat médical (F72) pour un athlète spécifique"

    def add_arguments(self, parser):
        parser.add_argument(
            'athlete_name',
            type=str,
            help='Nom complet de l\'athlète (ex: "Mulamba Lumanisha Pascal")'
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://127.0.0.1:8000',
            help='URL de base du site pour le QR code'
        )

    def handle(self, *args, **options):
        athlete_name = options['athlete_name']
        base_url = options['base_url']
        
        self.stdout.write(f"Recherche de l'athlète: {athlete_name}...")
        
        # Rechercher l'athlète par nom
        athletes = Athlete.objects.filter(
            personne__nom__icontains=athlete_name.split()[0]
        ).select_related('personne', 'club', 'discipline')
        
        if not athletes.exists():
            self.stdout.write(self.style.ERROR(f"Aucun athlète trouvé avec le nom '{athlete_name}'"))
            return
        
        # Si plusieurs résultats, afficher la liste
        if athletes.count() > 1:
            self.stdout.write(self.style.WARNING(f"Plusieurs athlètes trouvés ({athletes.count()}):"))
            for idx, athlete in enumerate(athletes, 1):
                self.stdout.write(f"  {idx}. {athlete.personne.nom_complet} - {athlete.numero_sportif} - {athlete.club.nom_officiel if athlete.club else 'Sans club'}")
            
            # Filtrer plus précisément
            athletes = athletes.filter(personne__nom__iexact=athlete_name.split()[0])
            if athletes.count() == 1:
                athlete = athletes.first()
            else:
                self.stdout.write(self.style.ERROR("Veuillez être plus précis dans le nom"))
                return
        else:
            athlete = athletes.first()
        
        self.stdout.write(self.style.SUCCESS(f"Athlète trouvé: {athlete.personne.nom_complet}"))
        self.stdout.write(f"  - ID Sportif: {athlete.numero_sportif}")
        self.stdout.write(f"  - Club: {athlete.club.nom_officiel if athlete.club else 'N/A'}")
        self.stdout.write(f"  - Statut: {athlete.get_statut_certification_display()}")
        
        # Rechercher la dernière visite médicale
        visite = VisiteMedicale.objects.filter(athlete=athlete).order_by('-date_visite').first()
        
        if not visite:
            self.stdout.write(self.style.ERROR("Aucune visite médicale trouvée pour cet athlète"))
            return
        
        self.stdout.write(f"\nVisite médicale trouvée:")
        self.stdout.write(f"  - Date: {visite.date_visite.strftime('%d/%m/%Y')}")
        self.stdout.write(f"  - Médecin: {visite.medecin_nom}")
        self.stdout.write(f"  - Résultat: {visite.get_resultat_global_display()}")
        
        # Régénérer le certificat
        self.stdout.write(f"\nRégénération du certificat F72...")
        
        try:
            pdf_buffer = generer_certificat_aptitude_pdf(visite, base_url=base_url)
            filename = f"Certificat_Aptitude_F72_{athlete.numero_sportif}_{visite.date_visite.strftime('%Y%m%d')}.pdf"
            
            # Sauvegarder dans la visite médicale
            visite.certificat_aptitude_joint.save(filename, ContentFile(pdf_buffer.getvalue()), save=True)
            
            # Copier aussi dans l'athlète
            pdf_buffer.seek(0)
            athlete.certificat_medical_enrolement.save(filename, ContentFile(pdf_buffer.getvalue()), save=True)
            
            self.stdout.write(self.style.SUCCESS(f"\n✓ Certificat régénéré avec succès!"))
            self.stdout.write(f"  - Fichier: {filename}")
            self.stdout.write(f"  - Chemin visite: {visite.certificat_aptitude_joint.url if visite.certificat_aptitude_joint else 'N/A'}")
            self.stdout.write(f"  - Chemin athlète: {athlete.certificat_medical_enrolement.url if athlete.certificat_medical_enrolement else 'N/A'}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Erreur lors de la génération du certificat: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
