"""
Régénère le certificat d'aptitude (F72) PDF pour un athlète, avec QR code.
Usage:
  python manage.py regenerer_certificat_aptitude "Mulamba lumanisha pascal"
  python manage.py regenerer_certificat_aptitude --uid=<athlete_uid>
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.conf import settings

from gouvernance.models import Athlete, VisiteMedicale


class Command(BaseCommand):
    help = "Régénère le certificat médical d'aptitude (F72) pour un athlète — avec QR code de vérification"

    def add_arguments(self, parser):
        parser.add_argument(
            'nom_athlete',
            nargs='?',
            type=str,
            help='Nom de l\'athlète (ex: "Mulamba lumanisha pascal")',
        )
        parser.add_argument(
            '--uid',
            type=str,
            help='UID de l\'athlète (prioritaire sur le nom)',
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default=None,
            help='URL de base du site pour le lien de vérification du QR code (défaut: depuis settings)',
        )

    def handle(self, *args, **options):
        base_url = options.get('base_url')
        if not base_url:
            base_url = getattr(settings, 'SITE_URL', None) or getattr(settings, 'SISEP_PUBLIC_URL', 'http://127.0.0.1:8000')
        base_url = base_url.rstrip('/')

        if options.get('uid'):
            try:
                athlete = Athlete.objects.select_related('personne', 'club', 'discipline').get(uid=options['uid'], actif=True)
            except Athlete.DoesNotExist:
                raise CommandError(f'Aucun athlète actif avec l\'UID {options["uid"]}.')
        elif options.get('nom_athlete'):
            name = options['nom_athlete'].strip()
            parts = [p for p in name.split() if p]
            if not parts:
                raise CommandError('Indiquez le nom de l\'athlète ou --uid=...')
            from django.db.models import Q
            # Recherche : nom ou prénom contient au moins le premier terme, puis affiner par les autres
            q = Q(personne__nom__icontains=parts[0]) | Q(personne__prenom__icontains=parts[0])
            for p in parts[1:]:
                q &= (Q(personne__nom__icontains=p) | Q(personne__prenom__icontains=p))
            athletes = list(Athlete.objects.filter(q, actif=True).select_related('personne', 'club', 'discipline')[:10])
            if not athletes and len(parts) >= 1:
                # Fallback : uniquement le premier mot (ex. "Mulamba")
                athletes = list(Athlete.objects.filter(
                    Q(personne__nom__icontains=parts[0]) | Q(personne__prenom__icontains=parts[0]),
                    actif=True
                ).select_related('personne', 'club', 'discipline')[:10])
            if not athletes:
                raise CommandError(f'Aucun athlète actif trouvé pour "{name}".')
            if len(athletes) > 1:
                self.stdout.write(self.style.WARNING(f'Plusieurs athlètes trouvés pour "{name}", on prend le premier.'))
            athlete = athletes[0]
        else:
            raise CommandError('Indiquez le nom de l\'athlète ou --uid=...')

        visite = athlete.visites_medicales.order_by('-date_visite').first()
        if not visite:
            raise CommandError(f'Aucune visite médicale (F67) pour l\'athlète {athlete.personne.nom_complet}. Impossible de générer le certificat.')

        self.stdout.write(f'Athlète: {athlete.personne.nom_complet} (n° {athlete.numero_sportif})')
        self.stdout.write(f'Visite: {visite.date_visite.date()}')

        try:
            from gouvernance.certificat_aptitude_generator import generer_certificat_aptitude_pdf
            pdf_buffer = generer_certificat_aptitude_pdf(visite, base_url=base_url)
            filename = f"Certificat_Aptitude_F72_{athlete.numero_sportif}_{visite.date_visite.strftime('%Y%m%d')}.pdf"
            visite.certificat_aptitude_joint.save(filename, ContentFile(pdf_buffer.getvalue()), save=True)
            athlete.certificat_medical_enrolement = visite.certificat_aptitude_joint
            athlete.save(update_fields=['certificat_medical_enrolement'])
            self.stdout.write(self.style.SUCCESS(
                f'Certificat F72 régénéré avec succès (avec QR code). Fichier: {visite.certificat_aptitude_joint.name}'
            ))
        except Exception as e:
            raise CommandError(f'Erreur lors de la génération du PDF: {e}') from e
