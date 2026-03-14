"""
Vues pour la gestion des Paramètres Disciplines
Réservé au Secrétaire Général
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from gouvernance.models.discipline import DisciplineSport
from core.permissions import est_secretaire_general_ministere


def _user_passes_test(test_func, login_url=None):
    from django.contrib.auth.views import redirect_to_login
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return redirect_to_login(request.get_full_path(), login_url=login_url)
        return wrapper
    return decorator


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def parametres_disciplines(request):
    """
    Page de gestion des disciplines sportives
    """
    disciplines = DisciplineSport.objects.all().order_by('ordre', 'designation')
    
    # Calculer les statistiques
    total_disciplines = disciplines.count()
    disciplines_actives = disciplines.filter(actif=True).count()
    total_federations = sum(d.federations.count() for d in disciplines)
    
    context = {
        'disciplines': disciplines,
        'total_disciplines': total_disciplines,
        'disciplines_actives': disciplines_actives,
        'total_federations': total_federations,
        'user_role': 'sg',
    }
    
    return render(request, 'gouvernance/parametres_disciplines.html', context)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
@require_http_methods(["POST"])
def discipline_create(request):
    """
    Créer une nouvelle discipline
    """
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().upper()
        designation = data.get('designation', '').strip()
        ordre = int(data.get('ordre', 0))
        
        if not code or not designation:
            return JsonResponse({
                'success': False,
                'message': 'Le code et la désignation sont obligatoires'
            }, status=400)
        
        # Vérifier si le code existe déjà
        if DisciplineSport.objects.filter(code=code).exists():
            return JsonResponse({
                'success': False,
                'message': f'Une discipline avec le code "{code}" existe déjà'
            }, status=400)
        
        discipline = DisciplineSport.objects.create(
            code=code,
            designation=designation,
            ordre=ordre,
            actif=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Discipline "{designation}" créée avec succès',
            'discipline': {
                'uid': str(discipline.uid),
                'code': discipline.code,
                'designation': discipline.designation,
                'ordre': discipline.ordre,
                'actif': discipline.actif
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
@require_http_methods(["PUT"])
def discipline_update(request, uid):
    """
    Modifier une discipline existante
    """
    try:
        discipline = get_object_or_404(DisciplineSport, uid=uid)
        data = json.loads(request.body)
        
        code = data.get('code', '').strip().upper()
        designation = data.get('designation', '').strip()
        ordre = int(data.get('ordre', 0))
        
        if not code or not designation:
            return JsonResponse({
                'success': False,
                'message': 'Le code et la désignation sont obligatoires'
            }, status=400)
        
        # Vérifier si le code existe déjà (sauf pour cette discipline)
        if DisciplineSport.objects.filter(code=code).exclude(uid=uid).exists():
            return JsonResponse({
                'success': False,
                'message': f'Une autre discipline avec le code "{code}" existe déjà'
            }, status=400)
        
        discipline.code = code
        discipline.designation = designation
        discipline.ordre = ordre
        discipline.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Discipline "{designation}" modifiée avec succès',
            'discipline': {
                'uid': str(discipline.uid),
                'code': discipline.code,
                'designation': discipline.designation,
                'ordre': discipline.ordre,
                'actif': discipline.actif
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
@require_http_methods(["DELETE"])
def discipline_delete(request, uid):
    """
    Supprimer une discipline
    """
    try:
        discipline = get_object_or_404(DisciplineSport, uid=uid)
        
        # Vérifier si la discipline est utilisée par des fédérations
        nb_federations = discipline.federations.count()
        if nb_federations > 0:
            return JsonResponse({
                'success': False,
                'message': f'Impossible de supprimer: {nb_federations} fédération(s) utilisent cette discipline'
            }, status=400)
        
        designation = discipline.designation
        discipline.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Discipline "{designation}" supprimée avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
@require_http_methods(["POST"])
def discipline_toggle_actif(request, uid):
    """
    Activer/Désactiver une discipline
    """
    try:
        discipline = get_object_or_404(DisciplineSport, uid=uid)
        discipline.actif = not discipline.actif
        discipline.save()
        
        statut = "activée" if discipline.actif else "désactivée"
        
        return JsonResponse({
            'success': True,
            'message': f'Discipline "{discipline.designation}" {statut}',
            'actif': discipline.actif
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)
