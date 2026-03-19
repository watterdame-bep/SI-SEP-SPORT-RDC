"""
Gestion des Divisions Provinciales (déconcentrations de l'État).
"""
import secrets
from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from core.models import ProfilUtilisateur, RoleUtilisateur
from core.permissions import est_secretaire_general_ministere
from gouvernance.models import (
    Institution,
    Agent,
    DivisionProvinciale,
)
from gouvernance.forms import CreerDivisionProvincialForm

User = get_user_model()


def _user_passes_test(test_func, login_url=None):
    """Décorateur pour vérifier les permissions."""
    from django.contrib.auth.views import redirect_to_login
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return redirect_to_login(request.get_full_path(), login_url=login_url)
        return wrapper
    return decorator


def _get_ministere_racine():
    """Retourne l'institution Ministère (racine)."""
    return Institution.objects.filter(institution_tutelle__isnull=True).first()


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def divisions_provinciales(request):
    """
    Liste des Divisions Provinciales avec option de créer/modifier le Chef de Division.
    Accessible uniquement au Secrétaire Général.
    """
    ministere = _get_ministere_racine()
    if not ministere:
        messages.error(request, "Aucun ministère trouvé. Effectuez d'abord l'initialisation du système.")
        return redirect('core:home')
    
    # Récupérer toutes les Divisions Provinciales
    divisions = DivisionProvinciale.objects.select_related('province', 'chef__personne').order_by('province__designation')
    
    if request.method == 'POST':
        action = request.POST.get('action', 'assign_chef')
        division_id = request.POST.get('division_id')
        
        try:
            division = DivisionProvinciale.objects.get(uid=division_id)
        except DivisionProvinciale.DoesNotExist:
            messages.error(request, "Division non trouvée.")
            return redirect('gouvernance:divisions_provinciales')
        
        # Action: Assigner un chef
        if action == 'assign_chef':
            agent_id = request.POST.get('agent_id', '').strip()
            
            # Validations
            if not agent_id:
                messages.error(request, "Veuillez sélectionner un agent.")
                return redirect('gouvernance:divisions_provinciales')
            
            # Vérifier que l'agent existe
            try:
                agent = Agent.objects.get(uid=agent_id)
            except Agent.DoesNotExist:
                messages.error(request, "Agent non trouvé.")
                return redirect('gouvernance:divisions_provinciales')

            # Vérifier si l'agent a déjà un compte avec un rôle incompatible
            from core.models import RoleUtilisateur
            profil_existant = ProfilUtilisateur.objects.filter(agent=agent).select_related('user').first()
            if profil_existant:
                incompatible_roles = [
                    RoleUtilisateur.MINISTRE,
                    RoleUtilisateur.INSTITUTION_ADMIN,
                    RoleUtilisateur.LIGUE_SECRETARY,
                    RoleUtilisateur.FEDERATION_SECRETARY,
                    RoleUtilisateur.CLUB_SECRETARY,
                    RoleUtilisateur.MEDECIN_INSPECTEUR,
                ]
                if profil_existant.role in incompatible_roles or profil_existant.role != RoleUtilisateur.DIRECTEUR_PROVINCIAL:
                    role_label = dict(RoleUtilisateur.choices).get(profil_existant.role, profil_existant.role)
                    messages.error(
                        request,
                        f"Cet agent possède déjà un compte avec le rôle « {role_label} ». "
                        f"Il ne peut pas être assigné comme Chef de Division. "
                        f"Veuillez choisir un autre agent."
                    )
                    return redirect('gouvernance:divisions_provinciales')

            # Vérifier que l'agent n'est pas déjà chef d'une autre division
            autre_division = DivisionProvinciale.objects.filter(chef=agent).exclude(uid=division.uid).first()
            if autre_division:
                messages.error(
                    request,
                    f"Cet agent est déjà Chef de Division pour « {autre_division.nom_officiel} » "
                    f"({autre_division.province.designation}). Un agent ne peut diriger qu'une seule division à la fois."
                )
                return redirect('gouvernance:divisions_provinciales')

            try:
                with transaction.atomic():
                    # Assigner le chef à la division
                    division.chef = agent
                    division.save()
                    
                    messages.success(request, f"Chef de Division assigné avec succès: {agent.personne.nom_complet}")
            
            except Exception as e:
                messages.error(request, f"Erreur lors de l'assignation : {e}")

        # Action: Transférer le chef (réassigne le compte existant au nouvel agent)
        elif action == 'transfer_chef':
            agent_id = request.POST.get('agent_id', '').strip()

            if not agent_id:
                messages.error(request, "Veuillez sélectionner un agent.")
                return redirect('gouvernance:divisions_provinciales')

            try:
                agent = Agent.objects.get(uid=agent_id)
            except Agent.DoesNotExist:
                messages.error(request, "Agent non trouvé.")
                return redirect('gouvernance:divisions_provinciales')

            profil_existant_check = ProfilUtilisateur.objects.filter(agent=agent).select_related('user').first()
            if profil_existant_check and profil_existant_check.role != RoleUtilisateur.DIRECTEUR_PROVINCIAL:
                role_label = dict(RoleUtilisateur.choices).get(profil_existant_check.role, profil_existant_check.role)
                messages.error(
                    request,
                    f"Cet agent possède déjà un compte avec le rôle « {role_label} ». "
                    f"Veuillez choisir un autre agent."
                )
                return redirect('gouvernance:divisions_provinciales')

            try:
                with transaction.atomic():
                    # Récupérer le compte directeur existant de la division
                    profil_existant = None
                    if division.chef:
                        profil_existant = ProfilUtilisateur.objects.filter(
                            agent=division.chef,
                            role=RoleUtilisateur.DIRECTEUR_PROVINCIAL
                        ).select_related('user').first()

                    if profil_existant:
                        # Réassigner le compte existant au nouvel agent
                        user = profil_existant.user
                        profil_existant.agent = agent
                        profil_existant.province_admin = division.province
                        profil_existant.actif = False  # Désactivé jusqu'à définition du mot de passe
                        profil_existant.save()

                        # Désactiver temporairement le compte Django
                        user.is_active = False
                        user.save()

                        # Générer un token de reset de mot de passe
                        from core.models import EmailVerificationToken
                        from django.utils import timezone
                        from datetime import timedelta

                        # Supprimer les anciens tokens de cet utilisateur
                        EmailVerificationToken.objects.filter(user=user).delete()

                        token_obj = EmailVerificationToken.objects.create(
                            user=user,
                            expires_at=timezone.now() + timedelta(days=3),
                        )
                        set_password_url = request.build_absolute_uri(
                            f"/auth/set-password/{token_obj.token}/"
                        )

                        # Envoyer l'email au nouvel agent
                        email_dest = (
                            agent.personne.email
                            if hasattr(agent.personne, 'email') and agent.personne.email
                            else user.email
                        )
                        try:
                            from django.core.mail import EmailMultiAlternatives
                            from django.template.loader import render_to_string
                            from django.conf import settings

                            context = {
                                'nom_complet': agent.personne.nom_complet,
                                'division': division.nom_officiel,
                                'set_password_url': set_password_url,
                                'username': user.username,
                            }
                            subject = 'Votre accès SI-SEP Sport RDC — Définissez votre mot de passe'
                            html_body = render_to_string('emails/transfer_set_password.html', context)
                            text_body = (
                                f"Bonjour {agent.personne.nom_complet},\n\n"
                                f"Vous avez été désigné(e) comme Directeur Provincial pour {division.nom_officiel}.\n"
                                f"Cliquez sur ce lien pour définir votre mot de passe (valable 3 jours) :\n{set_password_url}\n\n"
                                f"Identifiant : {user.username}\n"
                            )
                            email = EmailMultiAlternatives(
                                subject, text_body,
                                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sisep-sport.gouv.cd'),
                                [email_dest],
                            )
                            email.attach_alternative(html_body, 'text/html')
                            email.send(fail_silently=True)
                        except Exception as email_err:
                            import logging
                            logging.getLogger(__name__).warning(f"Email transfert non envoyé: {email_err}")

                        messages.success(
                            request,
                            f"Compte transféré à {agent.personne.nom_complet}. "
                            f"Un email a été envoyé à {email_dest} pour définir le mot de passe."
                        )
                    else:
                        # Pas de compte existant, juste réassigner le chef
                        messages.info(request, "Aucun compte actif trouvé. Chef réassigné sans transfert de compte.")

                    # Réassigner le chef dans tous les cas
                    division.chef = agent
                    division.save()

            except Exception as e:
                messages.error(request, f"Erreur lors du transfert : {e}")
        
        # Action: Activer/Désactiver une division
        elif action == 'toggle_status':
            try:
                with transaction.atomic():
                    new_status = 'ACTIVE' if division.statut == 'INACTIVE' else 'INACTIVE'
                    division.statut = new_status
                    division.save()
                    
                    status_label = 'activée' if new_status == 'ACTIVE' else 'désactivée'
                    messages.success(request, f"Division {status_label} avec succès.")
            
            except Exception as e:
                messages.error(request, f"Erreur lors de la modification du statut : {e}")
        
        return redirect('gouvernance:divisions_provinciales')
    
    return render(request, 'gouvernance/divisions_provinciales.html', {
        'ministere': ministere,
        'divisions': divisions,
        'user_role': 'sg',
    })


@login_required(login_url='/login/')
def division_detail(request, division_id):
    """
    Affiche les détails d'une Division Provinciale.
    """
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    division = get_object_or_404(DivisionProvinciale, uid=division_id)
    
    return render(request, 'gouvernance/division_detail.html', {
        'division': division,
        'user_role': 'sg' if profil.role == RoleUtilisateur.INSTITUTION_ADMIN else 'ministre',
    })
