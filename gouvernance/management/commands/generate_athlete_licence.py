"""
Commande pour générer la licence PDF d'un athlète certifié national.
Usage: python manage.py generate_athlete_licence "Lumanisha pascal"
       python manage.py generate_athlete_licence "Lumanisha" --format a4
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db.models import Q
from gouvernance.models import Athlete
from gouvernance.licence_generator import generer_licence_sportive, generer_licence_sportive_id1


class Command(BaseCommand):
    help = "Génère la licence PDF pour un athlète certifié national (ID-1 par défaut, A4 en option)"

    def add_arguments(self, parser):
        parser.add_argument(
            'athlete_name',
            type=str,
            help='Nom ou partie du nom (ex: "Lumanisha pascal", "Mulamba")'
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://127.0.0.1:8000',
            help='URL de base du site pour le QR code'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['id1', 'a4'],
            default='id1',
            help='Format du PDF: id1 (carte badge) ou a4'
        )

    def handle(self, *args, **options):
        athlete_name = (options['athlete_name'] or '').strip()
        base_url = (options['base_url'] or 'http://127.0.0.1:8000').rstrip('/')
        fmt = options['format']
        
        if not athlete_name:
            self.stdout.write(self.style.ERROR("Indiquez le nom de l'athlète."))
            return
        
        self.stdout.write(f"Recherche de l'athlète: {athlete_name}...")
        
        mots = [m for m in athlete_name.split() if m]
        if not mots:
            self.stdout.write(self.style.ERROR("Nom invalide."))
            return
        q = Q()
        for mot in mots:
            q &= (Q(personne__nom__icontains=mot) | Q(personne__prenom__icontains=mot))
        athletes = Athlete.objects.filter(q, actif=True).select_related('personne', 'club', 'discipline')
        
        if not athletes.exists():
            athletes = Athlete.objects.filter(
                Q(personne__nom__icontains=mots[0]) | Q(personne__prenom__icontains=mots[0]),
                actif=True
            ).select_related('personne', 'club', 'discipline')
        
        if not athletes.exists():
            self.stdout.write(self.style.ERROR(f"Aucun athlète trouvé avec le nom '{athlete_name}'"))
            return
        
        if athletes.count() > 1:
            self.stdout.write(self.style.WARNING(f"Plusieurs athlètes trouvés ({athletes.count()}):"))
            for idx, a in enumerate(athletes, 1):
                self.stdout.write(f"  {idx}. {a.personne.nom_complet} - {a.numero_sportif} - {a.club.nom_officiel if a.club else 'N/A'}")
            athlete = athletes.first()
            self.stdout.write(self.style.WARNING(f"Utilisation du premier: {athlete.personne.nom_complet}"))
        else:
            athlete = athletes.first()
        
        self.stdout.write(self.style.SUCCESS(f"Athlète: {athlete.personne.nom_complet}"))
        self.stdout.write(f"  - N° Sportif: {athlete.numero_sportif}")
        self.stdout.write(f"  - Club: {athlete.club.nom_officiel if athlete.club else 'N/A'}")
        self.stdout.write(f"  - Statut: {athlete.get_statut_certification_display()}")
        
        if athlete.statut_certification != 'CERTIFIE_NATIONAL':
            self.stdout.write(self.style.ERROR(f"L'athlète n'est pas certifié national (statut: {athlete.get_statut_certification_display()})"))
            return
        
        if not athlete.numero_licence:
            athlete.numero_licence = athlete.numero_sportif
        if not athlete.date_emission_licence:
            athlete.date_emission_licence = timezone.now().date()
        if not athlete.date_expiration_licence:
            athlete.date_expiration_licence = athlete.date_emission_licence + timedelta(days=365)
        athlete.save(update_fields=['numero_licence', 'date_emission_licence', 'date_expiration_licence'])
        
        self.stdout.write(f"  - N° Licence: {athlete.numero_licence}")
        self.stdout.write(f"  - Valide: {athlete.date_emission_licence} → {athlete.date_expiration_licence}")
        self.stdout.write(f"\nGénération PDF (format {fmt.upper()})...")
        
        try:
            if fmt == 'id1':
                pdf_buffer = generer_licence_sportive_id1(athlete, base_url=base_url)
                if pdf_buffer:
                    filename = f"Licence_ID1_{athlete.numero_licence}.pdf"
                    athlete.licence_pdf.save(filename, ContentFile(pdf_buffer.getvalue()), save=True)
            else:
                licence_content_file = generer_licence_sportive(athlete, base_url=base_url)
                athlete.licence_pdf.save(licence_content_file.name, licence_content_file, save=True)
            
            self.stdout.write(self.style.SUCCESS("✓ Licence PDF générée avec succès."))
            self.stdout.write(f"  Fichier: {athlete.licence_pdf.name}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erreur: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
