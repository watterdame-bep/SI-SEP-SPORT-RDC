"""
Signaux Django pour gouvernance.
Crée automatiquement une Division Provinciale quand une Province est ajoutée.
Crée automatiquement les validations provinciales quand une fédération est créée.
Crée automatiquement un compte pour le secrétaire de fédération quand une fédération est agréée.
"""
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from gouvernance.models import ProvAdmin, DivisionProvinciale, Institution, ValidationFederation

User = get_user_model()


@receiver(post_save, sender=ProvAdmin)
def creer_division_provinciale(sender, instance, created, **kwargs):
    """
    Signal: Quand une ProvAdmin est créée, crée automatiquement une DivisionProvinciale.
    """
    if not created:
        return  # Ne faire quelque chose que si c'est une nouvelle province
    
    try:
        with transaction.atomic():
            # Vérifier qu'une division n'existe pas déjà pour cette province
            if DivisionProvinciale.objects.filter(province=instance).exists():
                return  # Division existe déjà
            
            # Générer le code de la Division
            code = f"DIV-{instance.code or instance.designation[:10].upper()}"
            n = 0
            while DivisionProvinciale.objects.filter(code=code).exists():
                n += 1
                code = f"DIV-{instance.code or instance.designation[:10].upper()}-{n}"
            
            # Créer la DivisionProvinciale avec statut INACTIVE par défaut
            DivisionProvinciale.objects.create(
                province=instance,
                code=code,
                nom_officiel=f"Division Provinciale du Sport - {instance.designation}",
                statut='INACTIVE',  # Sera activée par le SG
                chef=None,  # Sera assigné manuellement
            )
    except Exception as e:
        # Silencieusement ignorer les erreurs pour ne pas bloquer la création de la province
        pass


@receiver(m2m_changed, sender=Institution.provinces_implantation.through)
def creer_validations_federation(sender, instance, action, pk_set, **kwargs):
    """
    Signal: Quand les provinces d'implantation d'une fédération sont modifiées,
    crée automatiquement les validations pour les Chefs de Division.
    """
    if action != 'post_add':
        return  # Ne faire quelque chose que quand on ajoute des provinces
    
    try:
        with transaction.atomic():
            # Vérifier que c'est une fédération (pas une division ou autre)
            if instance.niveau_territorial != 'FEDERATION':
                return
            
            # Pour chaque province ajoutée
            for province_id in pk_set:
                # Vérifier qu'une validation n'existe pas déjà
                if ValidationFederation.objects.filter(
                    federation=instance,
                    province_id=province_id
                ).exists():
                    continue  # Validation existe déjà
                
                # Créer la validation
                validation = ValidationFederation.objects.create(
                    federation=instance,
                    province_id=province_id,
                    statut='EN_ATTENTE',
                )
                
                # TODO: Envoyer une notification au Chef de Division
                # notifier_chef_division(validation)
    
    except Exception as e:
        # Silencieusement ignorer les erreurs
        pass


@receiver(post_save, sender=Institution)
def creer_compte_secretaire_federation(sender, instance, created, update_fields, **kwargs):
    """
    Signal: Quand une fédération passe au statut SIGNE (agréée par le Ministre),
    crée automatiquement un compte pour le secrétaire de la fédération.
    
    Le compte est créé SANS mot de passe. L'utilisateur reçoit un email avec un lien
    d'activation qui le dirige vers une page pour définir son propre mot de passe.
    """
    # Vérifier que c'est une fédération
    if instance.niveau_territorial != 'FEDERATION':
        return
    
    # Vérifier que le statut a changé vers SIGNE
    if update_fields and 'statut_signature' not in update_fields:
        return
    
    if instance.statut_signature != 'SIGNE':
        return
    
    # Vérifier qu'un compte n'existe pas déjà pour cette fédération
    from core.models import ProfilUtilisateur, RoleUtilisateur
    
    if ProfilUtilisateur.objects.filter(
        institution=instance,
        role=RoleUtilisateur.FEDERATION_SECRETARY
    ).exists():
        return  # Compte existe déjà
    
    # Vérifier qu'il y a un email officiel
    if not instance.email_officiel:
        return  # Pas d'email, impossible de créer un compte
    
    try:
        with transaction.atomic():
            # Créer l'utilisateur SANS mot de passe
            username = instance.email_officiel.split('@')[0]
            # Assurer l'unicité du username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=instance.email_officiel,
                first_name=instance.nom_officiel[:30],
                last_name=instance.sigle[:30] if instance.sigle else '',
                is_active=False,  # Compte inactif jusqu'à activation par email
            )
            # Ne pas définir de mot de passe - l'utilisateur le définira via le lien d'activation
            user.set_unusable_password()
            user.save()
            
            # Créer le profil utilisateur
            profil = ProfilUtilisateur.objects.create(
                user=user,
                institution=instance,
                role=RoleUtilisateur.FEDERATION_SECRETARY,
                actif=True,
            )
            
            # Créer un token de vérification email
            from core.models import EmailVerificationToken
            from django.utils import timezone
            from datetime import timedelta
            
            token_obj = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(days=7)  # Token valide 7 jours
            )
            
            # Envoyer l'email de notification avec les documents
            # Utiliser delay() si Celery est disponible, sinon envoyer directement
            try:
                from gouvernance.tasks import envoyer_email_agrement_federation_task
                envoyer_email_agrement_federation_task.delay(instance.uid, user.id, token_obj.token)
            except ImportError:
                # Celery non disponible, envoyer directement
                envoyer_email_agrement_federation(instance, user, token_obj.token)
    
    except Exception as e:
        # Silencieusement ignorer les erreurs pour ne pas bloquer la signature
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la création du compte secrétaire pour {instance.nom_officiel}: {str(e)}")


def envoyer_email_agrement_federation(federation, user, token):
    """
    Envoie un email de notification d'agrément à la fédération avec les documents.
    L'email contient un lien d'activation pour que l'utilisateur définisse son mot de passe.
    """
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings
    import os
    
    try:
        # Construire l'URL d'activation
        activation_url = f"{settings.SITE_URL}/verify-email/{token}/"
        
        # Préparer le contexte
        context = {
            'federation_name': federation.nom_officiel,
            'federation_sigle': federation.sigle,
            'email': user.email,
            'activation_url': activation_url,
            'site_url': settings.SITE_URL,
        }
        
        # Rendre les templates
        text_message = render_to_string('emails/agrement_federation.txt', context)
        html_message = render_to_string('emails/agrement_federation.html', context)
        
        # Créer l'email avec support HTML
        email = EmailMultiAlternatives(
            subject=f"Félicitations - Agrément de la Fédération {federation.sigle} - Vos accès SI-SEP SPORT",
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[federation.email_officiel],
        )
        
        # Ajouter la version HTML
        email.attach_alternative(html_message, "text/html")
        
        # Joindre les documents PDF si disponibles et accessibles
        if federation.document_arrete:
            try:
                # Vérifier que le fichier existe sur le disque
                if hasattr(federation.document_arrete, 'path') and os.path.exists(federation.document_arrete.path):
                    email.attach_file(federation.document_arrete.path)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Impossible de joindre l'arrêté pour {federation.nom_officiel}: {str(e)}")
        
        if federation.document_certificat_homologation:
            try:
                # Vérifier que le fichier existe sur le disque
                if hasattr(federation.document_certificat_homologation, 'path') and os.path.exists(federation.document_certificat_homologation.path):
                    email.attach_file(federation.document_certificat_homologation.path)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Impossible de joindre le certificat pour {federation.nom_officiel}: {str(e)}")
        
        # Envoyer l'email
        email.send(fail_silently=False)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de l'envoi de l'email d'agrément pour {federation.nom_officiel}: {str(e)}")
