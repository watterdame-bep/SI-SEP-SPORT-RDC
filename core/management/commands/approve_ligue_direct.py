"""
Commande Django pour approuver directement une ligue (pour les tests).
Usage: python manage.py approve_ligue_direct "LIGUE PROVINCIALE ATHLETISME DE KINSHASA"
"""
from django.core.management.base import BaseCommand, CommandError
from gouvernance.models import Institution, AttestationReconnaissance


class Command(BaseCommand):
    help = 'Approuve directement une ligue pour les tests'

    def add_arguments(self, parser):
        parser.add_argument(
            'ligue_name',
            type=str,
            help='Nom officiel de la ligue'
        )

    def handle(self, *args, **options):
        ligue_name = options['ligue_name']
        
        # Chercher la ligue
        try:
            ligue = Institution.objects.get(
                nom_officiel__iexact=ligue_name,
                niveau_territorial='LIGUE'
            )
        except Institution.DoesNotExist:
            raise CommandError(f'Ligue "{ligue_name}" non trouvée')
        
        # Mettre à jour le statut
        ligue.statut_signature = 'SIGNE'
        ligue.statut_activation = 'ACTIVE'
        ligue.save()
        
        # Récupérer l'attestation
        attestation = AttestationReconnaissance.objects.filter(ligue=ligue).first()
        if attestation:
            attestation.statut = 'APPROUVEE'
            attestation.save()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Ligue approuvée: {ligue.nom_officiel}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Attestation: {attestation.numero_attestation}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Aucune attestation trouvée')
            )
