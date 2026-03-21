"""
Vue pour le Secrétaire Général - Liste nationale des clubs.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from core.permissions import require_role
from gouvernance.models import Institution
from gouvernance.models.localisation import ProvAdmin


@login_required
@require_role('INSTITUTION_ADMIN', 'MINISTRE')
def sg_clubs_list(request):
    """
    Liste nationale de tous les clubs pour le SG.
    """
    clubs = Institution.objects.filter(
        niveau_territorial='CLUB'
    ).select_related(
        'institution_tutelle',
        'province_admin',
    ).order_by('province_admin__designation', 'nom_officiel')

    is_ministre = request.user.profil_sisep.role == 'MINISTRE'

    # Le ministre ne voit que les clubs officiellement affiliés
    if is_ministre:
        clubs = clubs.filter(statut_validation_club='AFFILIEE')

    # Filtres
    q = request.GET.get('q', '').strip()
    province_id = request.GET.get('province', '').strip()
    statut = request.GET.get('statut', '').strip()

    if q:
        clubs = clubs.filter(
            Q(nom_officiel__icontains=q) | Q(sigle__icontains=q) | Q(code__icontains=q)
        )
    if province_id:
        clubs = clubs.filter(province_admin__uid=province_id)
    if statut:
        clubs = clubs.filter(statut_validation_club=statut)

    clubs = list(clubs)

    # Stats globales (indépendantes des filtres)
    all_clubs = Institution.objects.filter(niveau_territorial='CLUB')
    stats = {
        'total': all_clubs.count(),
        'affilies': all_clubs.filter(statut_validation_club='AFFILIEE').count(),
        'valides': all_clubs.filter(statut_validation_club='VALIDEE_PROVINCIALE').count(),
        'en_attente': all_clubs.filter(statut_validation_club='EN_ATTENTE_VALIDATION').count(),
    }

    provinces = ProvAdmin.objects.order_by('designation')

    return render(request, 'gouvernance/sg_clubs_list.html', {
        'clubs': clubs,
        'stats': stats,
        'provinces': provinces,
        'q': q,
        'province_id': province_id,
        'statut': statut,
        'is_ministre': is_ministre,
    })
