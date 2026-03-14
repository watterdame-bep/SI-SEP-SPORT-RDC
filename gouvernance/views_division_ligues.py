"""
Vues pour la Division Provinciale - Gestion des Ligues Provinciales.
Inspection et validation des ligues transférées par le SG.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from core.permissions import require_role
from gouvernance.models import ValidationLigue


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def division_ligue_detail(request, validation_id):
    """
    Détail d'une ligue pour inspection par la Division Provinciale.
    """
    validation_ligue = get_object_or_404(
        ValidationLigue,
        uid=validation_id,
        statut__in=['EN_INSPECTION', 'INSPECTION_VALIDEE', 'INSPECTION_REJETEE']
    )
    
    ligue = validation_ligue.ligue
    federation = ligue.institution_tutelle
    disciplines = ligue.disciplines.all()
    
    context = {
        'validation_ligue': validation_ligue,
        'ligue': ligue,
        'federation': federation,
        'disciplines': disciplines,
        'user_role': 'directeur_provincial',
    }
    
    return render(request, 'gouvernance/division_ligue_detail.html', context)


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
@require_http_methods(["POST"])
def division_valider_ligue(request, validation_id):
    """
    Valider une ligue après inspection par la Division Provinciale.
    """
    validation_ligue = get_object_or_404(
        ValidationLigue,
        uid=validation_id,
        statut='EN_INSPECTION'
    )
    
    # Récupérer les critères d'inspection du formulaire
    conformite_mandat = request.POST.get('conformite_mandat') == 'on'
    siege_social_provincial = request.POST.get('siege_social_provincial') == 'on'
    existence_clubs = request.POST.get('existence_clubs') == 'on'
    observations = request.POST.get('observations', '').strip()
    rapport_inspection = request.FILES.get('rapport_inspection')
    
    # Vérifier que tous les critères sont cochés
    if not (conformite_mandat and siege_social_provincial and existence_clubs):
        messages.error(
            request,
            "Tous les critères d'inspection doivent être validés pour approuver la ligue."
        )
        return redirect('gouvernance:division_ligue_detail', validation_id=validation_id)
    
    # Mettre à jour la validation
    validation_ligue.conformite_mandat = conformite_mandat
    validation_ligue.siege_social_provincial = siege_social_provincial
    validation_ligue.existence_clubs = existence_clubs
    validation_ligue.observations = observations
    if rapport_inspection:
        validation_ligue.rapport_inspection = rapport_inspection
    validation_ligue.chef_division = request.user.profil_sisep.agent if hasattr(request.user.profil_sisep, 'agent') else None
    validation_ligue.statut = 'INSPECTION_VALIDEE'
    validation_ligue.date_validation = timezone.now()
    validation_ligue.save()
    
    # Mettre à jour le statut d'inspection de la ligue
    validation_ligue.ligue.statut_inspection = 'INSPECTION_VALIDEE'
    validation_ligue.ligue.save()
    
    messages.success(
        request,
        f"Ligue '{validation_ligue.ligue.nom_officiel}' validée avec succès. "
        f"Le dossier a été retourné au Secrétaire Général."
    )
    
    return redirect('gouvernance:enquetes_viabilite')


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
@require_http_methods(["POST"])
def division_rejeter_ligue(request, validation_id):
    """
    Rejeter une ligue après inspection par la Division Provinciale.
    """
    validation_ligue = get_object_or_404(
        ValidationLigue,
        uid=validation_id,
        statut='EN_INSPECTION'
    )
    
    # Récupérer les observations du formulaire
    observations = request.POST.get('observations', '').strip()
    
    # Mettre à jour la validation
    validation_ligue.observations = observations
    validation_ligue.chef_division = request.user.profil_sisep.agent if hasattr(request.user.profil_sisep, 'agent') else None
    validation_ligue.statut = 'INSPECTION_REJETEE'
    validation_ligue.date_validation = timezone.now()
    validation_ligue.save()
    
    # Mettre à jour le statut d'inspection de la ligue
    validation_ligue.ligue.statut_inspection = 'INSPECTION_REJETEE'
    validation_ligue.ligue.save()
    
    messages.warning(
        request,
        f"Ligue '{validation_ligue.ligue.nom_officiel}' rejetée. "
        f"Le dossier a été retourné au Secrétaire Général."
    )
    
    return redirect('gouvernance:enquetes_viabilite')
