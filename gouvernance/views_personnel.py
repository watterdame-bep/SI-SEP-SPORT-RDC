"""
Vues pour la gestion du personnel du Cabinet (SG).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from datetime import datetime

from core.models import ProfilUtilisateur, RoleUtilisateur
from core.permissions import require_role
from gouvernance.models import Agent, Personne, Membre, Mandat, Fonction, Institution
from gouvernance.forms import EnregistrerAgentForm, ModifierAgentForm


@login_required
@require_role('INSTITUTION_ADMIN')
def personnel_ministere(request):
    """Liste des agents du Cabinet (SG)."""
    institution = request.user.profil_sisep.institution
    
    # Récupérer tous les agents de l'institution avec leurs fonctions
    agents = Agent.objects.filter(institution=institution).select_related(
        'personne'
    ).prefetch_related('personne__membres__fonction')
    
    # Statistiques
    stats = {
        'total_agents': agents.count(),
        'comptes_actifs': ProfilUtilisateur.objects.filter(
            personne__agent__institution=institution,
            actif=True
        ).count(),
        'ministres': ProfilUtilisateur.objects.filter(
            personne__agent__institution=institution,
            role=RoleUtilisateur.MINISTRE,
            actif=True
        ).count(),
    }
    
    context = {
        'agents': agents,
        'stats': stats,
        'institution': institution,
        'user_role': 'sg',
    }
    return render(request, 'gouvernance/personnel_ministere.html', context)


@login_required
@require_role('INSTITUTION_ADMIN')
def enregistrer_agent(request):
    """Enregistrer un nouvel agent du Cabinet."""
    institution = request.user.profil_sisep.institution
    
    if request.method == 'POST':
        form = EnregistrerAgentForm(request.POST, request.FILES, institution=institution)
        if form.is_valid():
            agent = form.save(institution)
            return redirect('gouvernance:personnel_ministere')
    else:
        form = EnregistrerAgentForm(institution=institution)
    
    context = {
        'form': form,
        'institution': institution,
        'user_role': 'sg',
    }
    return render(request, 'gouvernance/enregistrer_agent.html', context)


@login_required
@require_role('INSTITUTION_ADMIN')
def detail_agent(request, agent_id):
    """Détail d'un agent et gestion de ses mandats."""
    institution = request.user.profil_sisep.institution
    agent = get_object_or_404(Agent, uid=agent_id, institution=institution)
    
    # Récupérer les mandats de l'agent
    mandats = Mandat.objects.filter(
        membre__personne=agent.personne,
        membre__institution=institution
    ).select_related('membre__fonction')
    
    # Récupérer le compte utilisateur s'il existe
    profil = ProfilUtilisateur.objects.filter(personne=agent.personne).first()
    
    context = {
        'agent': agent,
        'mandats': mandats,
        'profil': profil,
        'institution': institution,
        'user_role': 'sg',
    }
    return render(request, 'gouvernance/detail_agent.html', context)


@login_required
@require_role('INSTITUTION_ADMIN')
@require_http_methods(["POST"])
def creer_acces_systeme(request, agent_id):
    """Créer un compte utilisateur pour un agent."""
    institution = request.user.profil_sisep.institution
    agent = get_object_or_404(Agent, uid=agent_id, institution=institution)
    
    role = request.POST.get('role', RoleUtilisateur.INSTITUTION_ADMIN)
    
    # Vérifier qu'un compte n'existe pas déjà
    if ProfilUtilisateur.objects.filter(personne=agent.personne).exists():
        return JsonResponse({'success': False, 'error': 'Un compte existe déjà pour cet agent.'})
    
    try:
        with transaction.atomic():
            # Créer l'utilisateur Django
            username = f"{agent.personne.nom.lower()}.{agent.personne.postnom.lower()}".replace(' ', '_')
            
            # Vérifier l'unicité du username
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            # Générer un mot de passe temporaire
            temp_password = User.objects.make_random_password(length=12)
            
            user = User.objects.create_user(
                username=username,
                email=agent.personne.email,
                password=temp_password,
                first_name=agent.personne.prenom,
                last_name=agent.personne.nom,
            )
            
            # Créer le profil utilisateur
            profil = ProfilUtilisateur.objects.create(
                user=user,
                personne=agent.personne,
                institution=institution,
                role=role,
                actif=True,
            )
            
            # Si c'est un Ministre, désactiver l'ancien Ministre
            if role == RoleUtilisateur.MINISTRE:
                ancien_ministre = ProfilUtilisateur.objects.filter(
                    institution=institution,
                    role=RoleUtilisateur.MINISTRE,
                    actif=True
                ).exclude(user=user).first()
                
                if ancien_ministre:
                    ancien_ministre.actif = False
                    ancien_ministre.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Compte créé avec succès. Username: {username}',
                'username': username,
                'temp_password': temp_password,
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_role('INSTITUTION_ADMIN')
@require_http_methods(["POST"])
def desactiver_compte(request, agent_id):
    """Désactiver le compte d'un agent."""
    institution = request.user.profil_sisep.institution
    agent = get_object_or_404(Agent, uid=agent_id, institution=institution)
    
    profil = ProfilUtilisateur.objects.filter(personne=agent.personne).first()
    
    if not profil:
        return JsonResponse({'success': False, 'error': 'Aucun compte trouvé.'})
    
    profil.actif = False
    profil.save()
    
    return JsonResponse({'success': True, 'message': 'Compte désactivé.'})


@login_required
@require_role('INSTITUTION_ADMIN')
@require_http_methods(["POST"])
def reactiver_compte(request, agent_id):
    """Réactiver le compte d'un agent."""
    institution = request.user.profil_sisep.institution
    agent = get_object_or_404(Agent, uid=agent_id, institution=institution)
    
    profil = ProfilUtilisateur.objects.filter(personne=agent.personne).first()
    
    if not profil:
        return JsonResponse({'success': False, 'error': 'Aucun compte trouvé.'})
    
    profil.actif = True
    profil.save()
    
    return JsonResponse({'success': True, 'message': 'Compte réactivé.'})


@login_required
@require_role('INSTITUTION_ADMIN')
@require_http_methods(["POST"])
def creer_mandat(request, agent_id):
    """Créer un mandat pour un agent."""
    institution = request.user.profil_sisep.institution
    agent = get_object_or_404(Agent, uid=agent_id, institution=institution)
    
    fonction_id = request.POST.get('fonction_id')
    date_debut = request.POST.get('date_debut')
    date_fin = request.POST.get('date_fin')
    
    try:
        fonction = Fonction.objects.get(uid=fonction_id)
        
        # Créer ou récupérer le Membre
        membre, created = Membre.objects.get_or_create(
            personne=agent.personne,
            institution=institution,
            fonction=fonction
        )
        
        # Créer le Mandat
        mandat = Mandat.objects.create(
            membre=membre,
            date_debut=datetime.strptime(date_debut, '%Y-%m-%d').date(),
            date_fin=datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None,
            statut_mandat='En cours'
        )
        
        return JsonResponse({'success': True, 'message': 'Mandat créé avec succès.'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_role('INSTITUTION_ADMIN')
def modifier_agent(request, agent_id):
    """Modifier les informations d'un agent."""
    institution = request.user.profil_sisep.institution
    agent = get_object_or_404(Agent, uid=agent_id, institution=institution)
    
    if request.method == 'POST':
        form = ModifierAgentForm(request.POST, agent=agent)
        if form.is_valid():
            form.save()
            return redirect('gouvernance:detail_agent', agent_id=agent.uid)
    else:
        form = ModifierAgentForm(agent=agent)
    
    context = {
        'form': form,
        'agent': agent,
        'institution': institution,
        'user_role': 'sg',
    }
    return render(request, 'gouvernance/modifier_agent.html', context)
