"""
Commande Django pour renvoyer l'email d'approbation d'une ligue avec l'attestation.
Usage: python manage.py resend_ligue_approval_email "LIGUE PROVINCIALE ATHLETISME DE KINSHASA"
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from gouvernance.models import Institution, AttestationReconnaissance


class Command(BaseCommand):
    help = 'Renvoie l\'email d\'approbation d\'une ligue avec l\'attestation en pièce jointe'

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
        
        # Vérifier que la ligue est approuvée
        if ligue.statut_signature != 'SIGNE':
            raise CommandError(
                f'La ligue "{ligue.nom_officiel}" n\'est pas approuvée. '
                f'Statut actuel: {ligue.statut_signature}'
            )
        
        # Récupérer l'attestation
        attestation = AttestationReconnaissance.objects.filter(ligue=ligue).first()
        if not attestation:
            raise CommandError(f'Aucune attestation trouvée pour la ligue "{ligue.nom_officiel}"')
        
        # Récupérer la fédération
        federation = ligue.institution_tutelle
        
        # Préparer les destinataires (uniquement la ligue)
        recipients = []
        if ligue.email_officiel:
            recipients.append(ligue.email_officiel)
        
        if not recipients:
            raise CommandError(
                f'Aucune adresse email trouvée pour la ligue "{ligue.nom_officiel}"'
            )
        
        # Préparer le contexte de l'email
        context = {
            'ligue': ligue,
            'federation': federation,
            'numero_attestation': attestation.numero_attestation,
            'observations': attestation.observations_sg,
            'decision': 'APPROUVEE'
        }
        
        # Créer l'email
        subject = f"Approbation de la Ligue Provinciale - {ligue.nom_officiel}"
        html_message = render_to_string('emails/ligue_decision.html', context)
        
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sisep-sport.rdc'),
            to=recipients
        )
        email.content_subtype = 'html'
        
        # Attacher le PDF si disponible
        if attestation.document_attestation:
            try:
                with attestation.document_attestation.open('rb') as pdf_file:
                    email.attach(
                        f'Attestation_Homologation_{attestation.numero_attestation}.pdf',
                        pdf_file.read(),
                        'application/pdf'
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Attestation attachée: {attestation.document_attestation.name}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Impossible d\'attacher l\'attestation: {str(e)}'
                    )
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '⚠ Aucun fichier d\'attestation trouvé'
                )
            )
        
        # Envoyer l'email
        try:
            email.send(fail_silently=False)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Email envoyé avec succès à {", ".join(recipients)}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Ligue: {ligue.nom_officiel}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Numéro d\'attestation: {attestation.numero_attestation}'
                )
            )
        except Exception as e:
            raise CommandError(f'Erreur lors de l\'envoi de l\'email: {str(e)}')
