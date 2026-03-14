"""
Commande Django pour réinitialiser le statut d'une ligue à "EN_ATTENTE_SG".
Permet de tester le workflow complet d'approbation.
Usage: python manage.py reset_ligue_status "LIGUE PROVINCIALE ATHLETISME DE KINSHASA"
"""
from django.core.management.base import BaseCommand, CommandError
from gouvernance.models import Institution, AttestationReconnaissance


class Command(BaseCommand):
    help = 'Réinitialise le statut d\'une ligue à EN_ATTENTE_SG pour tester le workflow d\'approbation'

    def add_arguments(self, parser):
        parser.add_argument(
            'ligue_name',
            type=str,
            help='Nom officiel de la ligue (ex: "LIGUE PROVINCIALE ATHLETISME DE KINSHASA")'
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
        except Institution.MultipleObjectsReturned:
            raise CommandError(f'Plusieurs ligues trouvées avec le nom "{ligue_name}". Soyez plus spécifique.')
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Ligue trouvée: {ligue.nom_officiel}')
        )
        self.stdout.write(
            self.style.WARNING(f'Statut actuel: {ligue.statut_signature}')
        )
        
        # Réinitialiser les statuts
        old_signature_status = ligue.statut_signature
        old_inspection_status = ligue.statut_inspection
        
        ligue.statut_signature = 'ATTENTE_SIGNATURE'
        ligue.statut_inspection = 'INSPECTION_VALIDEE'
        ligue.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Statuts réinitialisés:')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  • Ancien statut signature: {old_signature_status}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  • Nouveau statut signature: {ligue.statut_signature}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  • Ancien statut inspection: {old_inspection_status}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  • Nouveau statut inspection: {ligue.statut_inspection}')
        )
        
        # Récupérer l'attestation
        attestation = AttestationReconnaissance.objects.filter(ligue=ligue).first()
        if attestation:
            self.stdout.write(
                self.style.WARNING(f'\n⚠ Attestation trouvée: {attestation.numero_attestation}')
            )
            self.stdout.write(
                self.style.WARNING(f'  • Statut: {attestation.statut}')
            )
            self.stdout.write(
                self.style.WARNING(f'  • Document: {attestation.document_attestation.name if attestation.document_attestation else "Aucun"}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ La ligue est maintenant prête pour l\'approbation du SG')
        )
        self.stdout.write(
            self.style.SUCCESS(f'✓ Accédez à: /gouvernance/sg-ligues-en-attente/')
        )
