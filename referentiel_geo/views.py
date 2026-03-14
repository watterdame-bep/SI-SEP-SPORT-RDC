"""
Vues du référentiel géographique : paramètres Province → Territoire → Secteur → Groupement.
Réservé au Secrétaire Général.
Architecture Hybride : Onglets + Drill-down hiérarchique
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Count

from gouvernance.models import (
    ProvAdmin,
    TerritoireVille,
    SecteurCommune,
    GroupementQuartier,
    AdresseContact,
)
from core.models import ProfilUtilisateur
from core.permissions import est_secretaire_general_ministere

from .forms import (
    ProvAdminForm,
    TerritoireVilleForm,
    SecteurCommuneForm,
    GroupementQuartierForm,
)


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
def parametres_geographiques(request):
    """
    Page principale avec onglets et navigation hiérarchique.
    Interface Hybride moderne.
    """
    # Statistiques globales
    stats = {
        'provinces': ProvAdmin.objects.count(),
        'territoires': TerritoireVille.objects.count(),
        'secteurs': SecteurCommune.objects.count(),
        'groupements': GroupementQuartier.objects.count(),
    }
    
    # Récupérer toutes les données pour l'affichage initial
    provinces = ProvAdmin.objects.annotate(
        nb_territoires=Count('territoires_villes')
    ).order_by('designation')
    
    return render(request, 'referentiel_geo/parametres_geographiques.html', {
        'stats': stats,
        'provinces': provinces,
    })


# ============= API ENDPOINTS (AJAX) =============

@login_required(login_url='/login/')
def api_provinces(request):
    """API: Liste des provinces avec statistiques - Accessible à tous les utilisateurs connectés"""
    try:
        provinces = ProvAdmin.objects.annotate(
            nb_territoires=Count('territoires_villes')
        ).order_by('designation')
        
        data = [{
            'uid': str(p.uid),
            'designation': p.designation,
            'nb_territoires': p.nb_territoires,
        } for p in provinces]
        
        return JsonResponse({'provinces': data})
    except Exception as e:
        import traceback
        print(f"Erreur dans api_provinces: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e), 'provinces': []}, status=500)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def api_territoires(request, province_id):
    """API: Liste des territoires d'une province"""
    territoires = TerritoireVille.objects.filter(
        province_admin_id=province_id
    ).annotate(
        nb_secteurs=Count('secteurs_communes')
    ).order_by('designation')
    
    data = [{
        'id': str(t.uid),
        'uid': str(t.uid),
        'designation': t.designation,
        'nb_secteurs': t.nb_secteurs,
        'province_id': str(t.province_admin_id) if t.province_admin_id else None,
    } for t in territoires]
    
    return JsonResponse({'territoires': data})


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def api_secteurs(request, territoire_id):
    """API: Liste des secteurs d'un territoire"""
    secteurs = SecteurCommune.objects.filter(
        territoire_id=territoire_id
    ).annotate(
        nb_groupements=Count('groupements_quartiers')
    ).order_by('designation')
    
    data = [{
        'id': str(s.uid),
        'uid': str(s.uid),
        'designation': s.designation,
        'nb_groupements': s.nb_groupements,
        'territoire_id': str(s.territoire_id) if s.territoire_id else None,
    } for s in secteurs]
    
    return JsonResponse({'secteurs': data})


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def api_groupements(request, secteur_id):
    """API: Liste des groupements d'un secteur"""
    groupements = GroupementQuartier.objects.filter(
        secteur_id=secteur_id
    ).order_by('designation')
    
    data = [{
        'id': str(g.uid),
        'uid': str(g.uid),
        'designation': g.designation,
        'secteur_id': str(g.secteur_id) if g.secteur_id else None,
    } for g in groupements]
    
    return JsonResponse({'groupements': data})


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def territoire_detail(request, pk):
    """API: Détails d'un territoire"""
    territoire = get_object_or_404(TerritoireVille, pk=pk)
    return JsonResponse({
        'id': str(territoire.uid),
        'uid': str(territoire.uid),
        'designation': territoire.designation,
        'code': territoire.code or '',
        'description': territoire.description or '',
        'province_id': str(territoire.province_admin_id) if territoire.province_admin_id else None,
    })


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def secteur_detail(request, pk):
    """API: Détails d'un secteur"""
    secteur = get_object_or_404(SecteurCommune, pk=pk)
    return JsonResponse({
        'id': str(secteur.uid),
        'uid': str(secteur.uid),
        'designation': secteur.designation,
        'description': secteur.description or '',
        'territoire_id': str(secteur.territoire_id) if secteur.territoire_id else None,
    })


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def groupement_detail(request, pk):
    """API: Détails d'un groupement"""
    groupement = get_object_or_404(GroupementQuartier, pk=pk)
    return JsonResponse({
        'id': str(groupement.uid),
        'uid': str(groupement.uid),
        'designation': groupement.designation,
        'description': groupement.description or '',
        'secteur_id': str(groupement.secteur_id) if groupement.secteur_id else None,
    })


# ============= CRUD PROVINCES =============

@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def province_create(request):
    """Créer une province"""
    if request.method == 'POST':
        form = ProvAdminForm(request.POST)
        if form.is_valid():
            province = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Province « {province.designation} » créée avec succès.',
                'province': {
                    'id': str(province.uid),
                    'uid': str(province.uid),
                    'designation': province.designation,
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def province_update(request, pk):
    """Modifier une province"""
    province = get_object_or_404(ProvAdmin, pk=pk)
    if request.method == 'POST':
        form = ProvAdminForm(request.POST, instance=province)
        if form.is_valid():
            province = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Province « {province.designation} » modifiée avec succès.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def province_delete(request, pk):
    """Supprimer une province"""
    province = get_object_or_404(ProvAdmin, pk=pk)
    if request.method == 'POST':
        force_delete = request.POST.get('force_delete', 'false') == 'true'
        nb_territoires = TerritoireVille.objects.filter(province_admin=province).count()
        
        if nb_territoires > 0 and not force_delete:
            return JsonResponse({
                'success': False,
                'has_children': True,
                'children_count': nb_territoires,
                'message': f'Cette province contient {nb_territoires} territoire(s). Voulez-vous supprimer la province et tous ses territoires (et leurs secteurs/groupements) ?'
            }, status=200)
        
        # Vérifier les comptes utilisateurs
        if ProfilUtilisateur.objects.filter(province_admin=province).exists():
            return JsonResponse({
                'success': False,
                'message': 'Impossible de supprimer : des comptes utilisateurs sont rattachés à cette province.'
            }, status=400)
        
        designation = province.designation
        # Supprimer en cascade
        if force_delete:
            TerritoireVille.objects.filter(province_admin=province).delete()
        province.delete()
        return JsonResponse({
            'success': True,
            'message': f'Province « {designation} » supprimée avec succès.'
        })
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


# ============= CRUD TERRITOIRES =============

@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def territoire_create(request):
    """Créer un territoire"""
    if request.method == 'POST':
        form = TerritoireVilleForm(request.POST)
        if form.is_valid():
            territoire = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Territoire « {territoire.designation} » créé avec succès.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def territoire_update(request, pk):
    """Modifier un territoire"""
    territoire = get_object_or_404(TerritoireVille, pk=pk)
    if request.method == 'POST':
        form = TerritoireVilleForm(request.POST, instance=territoire)
        if form.is_valid():
            territoire = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Territoire « {territoire.designation} » modifié avec succès.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def territoire_delete(request, pk):
    """Supprimer un territoire"""
    territoire = get_object_or_404(TerritoireVille, pk=pk)
    if request.method == 'POST':
        force_delete = request.POST.get('force_delete', 'false') == 'true'
        nb_secteurs = SecteurCommune.objects.filter(territoire=territoire).count()
        
        if nb_secteurs > 0 and not force_delete:
            return JsonResponse({
                'success': False,
                'has_children': True,
                'children_count': nb_secteurs,
                'message': f'Ce territoire contient {nb_secteurs} secteur(s). Voulez-vous supprimer le territoire et tous ses secteurs ?'
            }, status=200)
        
        designation = territoire.designation
        # Supprimer en cascade
        if force_delete:
            SecteurCommune.objects.filter(territoire=territoire).delete()
        territoire.delete()
        return JsonResponse({
            'success': True,
            'message': f'Territoire « {designation} » supprimé avec succès.'
        })
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


# ============= CRUD SECTEURS =============

@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def secteur_create(request):
    """Créer un secteur"""
    if request.method == 'POST':
        form = SecteurCommuneForm(request.POST)
        if form.is_valid():
            secteur = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Secteur « {secteur.designation} » créé avec succès.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def secteur_update(request, pk):
    """Modifier un secteur"""
    secteur = get_object_or_404(SecteurCommune, pk=pk)
    if request.method == 'POST':
        form = SecteurCommuneForm(request.POST, instance=secteur)
        if form.is_valid():
            secteur = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Secteur « {secteur.designation} » modifié avec succès.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def secteur_delete(request, pk):
    """Supprimer un secteur"""
    secteur = get_object_or_404(SecteurCommune, pk=pk)
    if request.method == 'POST':
        force_delete = request.POST.get('force_delete', 'false') == 'true'
        nb_groupements = GroupementQuartier.objects.filter(secteur=secteur).count()
        
        if nb_groupements > 0 and not force_delete:
            return JsonResponse({
                'success': False,
                'has_children': True,
                'children_count': nb_groupements,
                'message': f'Ce secteur contient {nb_groupements} groupement(s). Voulez-vous supprimer le secteur et tous ses groupements ?'
            }, status=200)
        
        designation = secteur.designation
        # Supprimer en cascade
        if force_delete:
            GroupementQuartier.objects.filter(secteur=secteur).delete()
        secteur.delete()
        return JsonResponse({
            'success': True,
            'message': f'Secteur « {designation} » supprimé avec succès.'
        })
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


# ============= CRUD GROUPEMENTS =============

@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def groupement_create(request):
    """Créer un groupement"""
    if request.method == 'POST':
        form = GroupementQuartierForm(request.POST)
        if form.is_valid():
            groupement = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Groupement « {groupement.designation} » créé avec succès.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def groupement_update(request, pk):
    """Modifier un groupement"""
    groupement = get_object_or_404(GroupementQuartier, pk=pk)
    if request.method == 'POST':
        form = GroupementQuartierForm(request.POST, instance=groupement)
        if form.is_valid():
            groupement = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Groupement « {groupement.designation} » modifié avec succès.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def groupement_delete(request, pk):
    """Supprimer un groupement"""
    groupement = get_object_or_404(GroupementQuartier, pk=pk)
    if request.method == 'POST':
        if AdresseContact.objects.filter(groupement_quartier=groupement).exists():
            return JsonResponse({
                'success': False,
                'message': 'Impossible de supprimer : ce groupement est utilisé dans des adresses.'
            }, status=400)
        
        designation = groupement.designation
        groupement.delete()
        return JsonResponse({
            'success': True,
            'message': f'Groupement « {designation} » supprimé avec succès.'
        })
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/login/')
def api_territoires_by_province(request):
    """API: Liste des territoires d'une province (via query parameter) - Accessible à tous"""
    try:
        province_id = request.GET.get('province')
        if not province_id:
            return JsonResponse([], safe=False)
        
        territoires = TerritoireVille.objects.filter(
            province_admin_id=province_id
        ).values('uid', 'designation', 'code').order_by('designation')
        
        return JsonResponse(list(territoires), safe=False)
    except Exception as e:
        import traceback
        print(f"Erreur dans api_territoires_by_province: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required(login_url='/login/')
def api_secteurs_by_territoire(request):
    """API: Liste des secteurs d'un territoire (via query parameter) - Accessible à tous"""
    try:
        territoire_id = request.GET.get('territoire')
        if not territoire_id:
            return JsonResponse([], safe=False)
        
        secteurs = SecteurCommune.objects.filter(
            territoire_id=territoire_id
        ).values('uid', 'designation').order_by('designation')
        
        return JsonResponse(list(secteurs), safe=False)
    except Exception as e:
        import traceback
        print(f"Erreur dans api_secteurs_by_territoire: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required(login_url='/login/')
def api_groupements_by_secteur(request):
    """API: Liste des groupements d'un secteur (via query parameter) - Accessible à tous"""
    try:
        secteur_id = request.GET.get('secteur')
        if not secteur_id:
            return JsonResponse([], safe=False)
        
        groupements = GroupementQuartier.objects.filter(
            secteur_id=secteur_id
        ).values('uid', 'designation').order_by('designation')
        
        return JsonResponse(list(groupements), safe=False)
    except Exception as e:
        import traceback
        print(f"Erreur dans api_groupements_by_secteur: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
