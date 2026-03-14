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
            
            # Vérifier que l'agent existe et appartient au ministère
            try:
                agent = Agent.objects.get(uid=agent_id, institution=ministere)
            except Agent.DoesNotExist:
                messages.error(request, "Agent non trouvé ou n'appartient pas au ministère.")
                return redirect('gouvernance:divisions_provinciales')
            
            # Vérifier que l'agent n'a pas un rôle restreint (Ministre ou Secrétaire Général)
            from core.models import RoleUtilisateur
            restricted_roles = [RoleUtilisateur.MINISTRE, RoleUtilisateur.INSTITUTION_ADMIN]
            profil_agent = ProfilUtilisateur.objects.filter(
                personne=agent.personne,
                role__in=restricted_roles
            ).first()
            
            if profil_agent:
                role_label = 'Ministre' if profil_agent.role == RoleUtilisateur.MINISTRE else 'Secrétaire Général'
                messages.error(request, f"Un {role_label} ne peut pas être assigné comme Chef de Division.")
                return redirect('gouvernance:divisions_provinciales')
            
            try:
                with transaction.atomic():
                    # Assigner le chef à la division
                    division.chef = agent
                    division.save()
                    
                    messages.success(request, f"Chef de Division assigné avec succès: {agent.personne.nom_complet}")
            
            except Exception as e:
                messages.error(request, f"Erreur lors de l'assignation : {e}")
        
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
