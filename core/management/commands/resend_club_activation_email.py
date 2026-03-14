"""
Commande pour renvoyer l'email d'activation au secrétaire d'un club avec l'Acte d'Affiliation en pièce jointe.
Usage: python manage.py resend_club_activation_email --club-sigle FCO
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from core.models import ProfilUtilisateur, EmailVerificationToken
from gouvernance.models import Institution


class Command(BaseCommand):
    help = 'Renvoie l\'email d\'activation au secrétaire d\'un club avec l\'Acte d\'Affiliation en pièce jointe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--club-sigle',
            type=str,
            help='Sigle du club (ex: FCO)',
            required=True,
        )

    def handle(self, *args, **options):
        club_sigle = options['club_sigle'].upper()
        
        # Trouver le club
        try:
            club = Institution.objects.get(
                sigle=club_sigle,
                niveau_territorial='CLUB'
            )
        except Institution.DoesNotExist:
            raise CommandError(f'Club avec le sigle "{club_sigle}" non trouvé')
        
        # Vérifier que le club est affilié
        if club.statut_validation_club != 'AFFILIEE':
            raise CommandError(f'Le club "{club.nom_officiel}" n\'est pas affilié (statut: {club.statut_validation_club})')
        
        # Vérifier que le club a un acte d'affiliation
        if not club.document_acte_affiliation:
            raise CommandError(f'Le club "{club.nom_officiel}" n\'a pas d\'Acte d\'Affiliation généré')
        
        # Récupérer l'email du club
        club_email = club.email_officiel
        if not club_email:
            raise CommandError(f'Le club "{club.nom_officiel}" n\'a pas d\'email officiel')
        
        # Récupérer ou créer le compte utilisateur
        user = User.objects.filter(email=club_email).first()
        if not user:
            raise CommandError(f'Aucun compte utilisateur trouvé pour l\'email "{club_email}"')
        
        # Récupérer la ligue parente
        ligue = club.institution_tutelle
        if not ligue:
            raise CommandError(f'Le club "{club.nom_officiel}" n\'a pas de ligue parente')
        
        # Créer ou récupérer le token de vérification
        token_obj, created = EmailVerificationToken.objects.get_or_create(user=user)
        
        # Générer l'URL d'activation
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_HOST'] = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'
        request.META['wsgi.url_scheme'] = 'https' if not settings.DEBUG else 'http'
        
        activation_url = f"{'https' if not settings.DEBUG else 'http'}://{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'}{reverse('core:verify_email', kwargs={'token': token_obj.token})}"
        
        # Préparer le contexte de l'email
        context = {
            'club_name': club.sigle,
            'club_nom_officiel': club.nom_officiel,
            'club_sigle': club.sigle,
            'club_code': club.code,
            'ligue_name': ligue.nom_officiel,
            'user_email': club_email,
            'activation_url': activation_url,
        }
        
        # Générer le HTML de l'email
        email_html = render_to_string('emails/club_secretary_account_activation.html', context)
        
        # Créer et envoyer l'email avec pièce jointe
        try:
            email = EmailMultiAlternatives(
                subject=f"Activation de votre compte - Club {club.nom_officiel}",
                body="Veuillez consulter la version HTML de cet email.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[club_email],
            )
            email.attach_alternative(email_html, "text/html")
            
            # Attacher le PDF de l'Acte d'Affiliation
            if club.document_acte_affiliation:
                try:
                    pdf_file = club.document_acte_affiliation.open('rb')
                    pdf_content = pdf_file.read()
                    pdf_file.close()
                    
                    filename = f"Acte_Affiliation_{club.numero_affiliation}.pdf"
                    email.attach(filename, pdf_content, 'application/pdf')
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ PDF attaché: {filename}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Erreur lors de l\'attachement du PDF: {e}')
                    )
            
            # Envoyer l'email
            email.send(fail_silently=False)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Email d\'activation renvoyé avec succès au club "{club.nom_officiel}"'
                )
            )
            self.stdout.write(f'  Email: {club_email}')
            self.stdout.write(f'  Numéro d\'affiliation: {club.numero_affiliation}')
            self.stdout.write(f'  Lien d\'activation: {activation_url}')
            self.stdout.write(f'  Validité du lien: 7 jours\n')
            
        except Exception as e:
            raise CommandError(f'Erreur lors de l\'envoi de l\'email: {str(e)}')
