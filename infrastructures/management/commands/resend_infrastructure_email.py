"""
Commande pour renvoyer l'email de notification d'infrastructure.
Usage: python manage.py resend_infrastructure_email <infrastructure_name>
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from infrastructures.models import Infrastructure


class Command(BaseCommand):
    help = 'Renvoie l\'email de notification pour une infrastructure validée'

    def add_arguments(self, parser):
        parser.add_argument(
            'infrastructure_name',
            type=str,
            help='Nom de l\'infrastructure'
        )

    def handle(self, *args, **options):
        infrastructure_name = options['infrastructure_name']
        
        try:
            infrastructure = Infrastructure.objects.get(nom__iexact=infrastructure_name)
        except Infrastructure.DoesNotExist:
            raise CommandError(f'Infrastructure "{infrastructure_name}" non trouvée')
        
        # Vérifier que l'infrastructure est validée
        if infrastructure.statut != 'VALIDEE':
            raise CommandError(f'L\'infrastructure "{infrastructure.nom}" n\'est pas validée (statut: {infrastructure.statut})')
        
        # Vérifier que le gestionnaire a un email
        if not infrastructure.email_gestionnaire:
            raise CommandError(f'L\'infrastructure "{infrastructure.nom}" n\'a pas d\'email gestionnaire')
        
        try:
            # Récupérer ou créer le token de vérification
            from core.models import EmailVerificationToken
            from django.contrib.auth.models import User
            
            # Trouver l'utilisateur associé à cette infrastructure
            try:
                from core.models import ProfilUtilisateur
                profil = ProfilUtilisateur.objects.get(infrastructure=infrastructure)
                user = profil.user
                
                # Récupérer ou créer le token
                token, created = EmailVerificationToken.objects.get_or_create(user=user)
            except:
                raise CommandError(f'Aucun utilisateur trouvé pour l\'infrastructure "{infrastructure.nom}"')
            
            verification_url = f"{settings.SITE_URL}/verify-email/{token.token}/"
            
            # Préparer le contexte pour le template
            context = {
                'infrastructure_nom': infrastructure.nom,
                'code_homologation': infrastructure.code_homologation,
                'province': infrastructure.province_admin.designation if infrastructure.province_admin else 'N/A',
                'type_infrastructure': infrastructure.type_infrastructure.designation if infrastructure.type_infrastructure else 'N/A',
                'gestionnaire_nom': infrastructure.gestionnaire_nom,
                'gestionnaire_prenom': infrastructure.gestionnaire_prenom,
                'verification_url': verification_url,
                'token': token.token,
            }
            
            # Rendre le template HTML
            html_message = render_to_string(
                'emails/infrastructure_manager_activation.html',
                context
            )
            
            # Envoyer l'email
            send_mail(
                subject=f"Activation de votre compte - Gestionnaire Infrastructure {infrastructure.nom}",
                message=f"Votre infrastructure '{infrastructure.nom}' a été validée avec succès. Cliquez sur le lien pour activer votre compte.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[infrastructure.email_gestionnaire],
                html_message=html_message,
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Email envoyé avec succès à {infrastructure.email_gestionnaire}'
                )
            )
        except Exception as e:
            raise CommandError(f'Erreur lors de l\'envoi de l\'email: {str(e)}')
