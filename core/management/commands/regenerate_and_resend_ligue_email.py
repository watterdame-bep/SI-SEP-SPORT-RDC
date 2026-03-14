"""
Commande Django pour régénérer l'attestation d'une ligue et renvoyer l'email avec pièce jointe.
Usage: python manage.py regenerate_and_resend_ligue_email "LIGUE PROVINCIALE ATHLETISME DE KINSHASA"
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
from core.models import EmailVerificationToken
from gouvernance.models import Institution, AttestationReconnaissance

User = get_user_model()


class Command(BaseCommand):
    help = 'Régénère l\'attestation d\'une ligue et renvoie l\'email avec pièce jointe'

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
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Ligue trouvée: {ligue.nom_officiel}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'✓ Attestation: {attestation.numero_attestation}')
        )
        
        # Régénérer le PDF
        try:
            from gouvernance.certificate_generator import generer_attestation_homologation_ligue
            attestation_pdf = generer_attestation_homologation_ligue(ligue)
            
            # Sauvegarder le PDF
            pdf_filename = f"institutions/attestations/Attestation_Homologation_Ligue_{attestation.numero_attestation}.pdf"
            attestation.document_attestation = default_storage.save(pdf_filename, attestation_pdf)
            attestation.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Attestation régénérée: {attestation.document_attestation.name}')
            )
        except Exception as e:
            raise CommandError(f'Erreur lors de la génération de l\'attestation: {str(e)}')
        
        # Récupérer la fédération (pour le contexte email)
        federation = ligue.institution_tutelle
        
        # Préparer les destinataires (uniquement la ligue)
        recipients = []
        if ligue.email_officiel:
            recipients.append(ligue.email_officiel)
        
        if not recipients:
            raise CommandError(
                f'Aucune adresse email trouvée pour la ligue "{ligue.nom_officiel}"'
            )
        
        # Récupérer le token de vérification email si le compte existe
        verification_token = None
        user_created = False
        
        try:
            user = User.objects.get(email=ligue.email_officiel)
            if hasattr(user, 'email_verification_token'):
                verification_token = user.email_verification_token
            self.stdout.write(
                self.style.SUCCESS(f'✓ Compte trouvé: {user.username}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'⚠ Aucun compte trouvé pour: {ligue.email_officiel}')
            )
        
        # Préparer le contexte de l'email
        context = {
            'ligue': ligue,
            'federation': federation,
            'numero_attestation': attestation.numero_attestation,
            'observations': attestation.observations_sg,
            'decision': 'APPROUVEE',
            'verification_token': verification_token.token if verification_token else None,
            'user_created': user_created,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
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
        
        # Attacher le PDF
        try:
            with attestation.document_attestation.open('rb') as pdf_file:
                email.attach(
                    f'Attestation_Homologation_{attestation.numero_attestation}.pdf',
                    pdf_file.read(),
                    'application/pdf'
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Attestation attachée au email'
                )
            )
        except Exception as e:
            raise CommandError(f'Erreur lors de l\'attachement du PDF: {str(e)}')
        
        # Envoyer l'email
        try:
            email.send(fail_silently=False)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Email envoyé avec succès à:'
                )
            )
            for recipient in recipients:
                self.stdout.write(
                    self.style.SUCCESS(f'  • {recipient}')
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Détails:'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(f'  • Ligue: {ligue.nom_officiel}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  • Numéro: {attestation.numero_attestation}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  • Fichier: {attestation.document_attestation.name}')
            )
            if verification_token:
                self.stdout.write(
                    self.style.SUCCESS(f'  • Token: {verification_token.token[:20]}...')
                )
        except Exception as e:
            raise CommandError(f'Erreur lors de l\'envoi de l\'email: {str(e)}')
