"""
Vues lecture seule pour le Ministre — Athlètes, Médecins, Entraîneurs, Arbitres.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from core.permissions import require_role
from gouvernance.models.athlete import Athlete
from gouvernance.models.medecin_ligue import MedecinLigue
from gouvernance.models.localisation import ProvAdmin


@login_required
@require_role('INSTITUTION_ADMIN', 'MINISTRE')
def ministre_athletes_list(request):
    """Liste nationale des athlètes certifiés — lecture seule pour le Ministre."""
    athletes = Athlete.objects.select_related(
        'personne', 'club', 'club__province_admin', 'discipline'
    ).order_by('personne__nom')

    # Filtres
    q = request.GET.get('q', '').strip()
    province_id = request.GET.get('province', '').strip()
    statut = request.GET.get('statut', '').strip()
    is_ministre = request.user.profil_sisep.role == 'MINISTRE'

    # Le ministre ne voit que les athlètes certifiés nationalement
    # SG et Ministre voient uniquement les athlètes certifiés nationalement
    athletes = athletes.filter(statut_certification='CERTIFIE_NATIONAL')

    if q:
        athletes = athletes.filter(
            Q(personne__nom__icontains=q) |
            Q(personne__postnom__icontains=q) |
            Q(personne__prenom__icontains=q) |
            Q(numero_licence__icontains=q)
        )
    if province_id:
        athletes = athletes.filter(club__province_admin__uid=province_id)
    if statut:
        athletes = athletes.filter(statut_certification=statut)

    certifies_national = Athlete.objects.filter(statut_certification='CERTIFIE_NATIONAL')
    stats = {
        'total': certifies_national.count(),
        'hommes': certifies_national.filter(personne__sexe='M').count(),
        'femmes': certifies_national.filter(personne__sexe='F').count(),
        'provinces': certifies_national.values('club__province_admin').distinct().count(),
    }

    provinces = ProvAdmin.objects.order_by('designation')
    from gouvernance.models.discipline import DisciplineSport
    disciplines = DisciplineSport.objects.order_by('designation')

    return render(request, 'gouvernance/ministre_athletes_list.html', {
        'athletes': athletes,
        'stats': stats,
        'provinces': provinces,
        'q': q,
        'province_id': province_id,
        'statut': statut,
        'is_ministre': is_ministre,
        'statut_choices': Athlete.STATUT_CERTIFICATION_CHOICES,
    })


@login_required
@require_role('INSTITUTION_ADMIN', 'MINISTRE')
def ministre_medecins_list(request):
    """Liste nationale des médecins des ligues — lecture seule pour le Ministre."""
    medecins = MedecinLigue.objects.select_related(
        'agent__personne', 'ligue', 'ligue__province_admin'
    ).order_by('ligue__province_admin__designation', 'agent__personne__nom')

    q = request.GET.get('q', '').strip()
    province_id = request.GET.get('province', '').strip()

    if q:
        medecins = medecins.filter(
            Q(agent__personne__nom__icontains=q) |
            Q(agent__personne__prenom__icontains=q) |
            Q(numero_ordre_medecins__icontains=q)
        )
    if province_id:
        medecins = medecins.filter(ligue__province_admin__uid=province_id)

    provinces = ProvAdmin.objects.order_by('designation')
    stats = {
        'total': MedecinLigue.objects.count(),
        'avec_compte': MedecinLigue.objects.filter(profil_utilisateur__isnull=False).count(),
    }
    total = stats['total']
    avec_compte = stats['avec_compte']
    stats['sans_compte'] = total - avec_compte

    return render(request, 'gouvernance/ministre_medecins_list.html', {
        'medecins': medecins,
        'stats': stats,
        'provinces': provinces,
        'q': q,
        'province_id': province_id,
        'is_ministre': request.user.profil_sisep.role == 'MINISTRE',
    })


@login_required
@require_role('INSTITUTION_ADMIN', 'MINISTRE')
def ministre_entraineurs_list(request):
    """Entraîneurs — fonctionnalité à venir."""
    return render(request, 'gouvernance/ministre_entraineurs_list.html', {
        'is_ministre': request.user.profil_sisep.role == 'MINISTRE',
    })


@login_required
@require_role('INSTITUTION_ADMIN', 'MINISTRE', 'FEDERATION_SECRETARY', 'LIGUE_SECRETARY')
def ministre_arbitres_list(request):
    """Arbitres — liste avec stats réelles."""
    from gouvernance.models.arbitre import Arbitre
    from gouvernance.models.discipline import DisciplineSport

    role = request.user.profil_sisep.role
    institution = None
    try:
        institution = request.user.profil_sisep.institution
    except Exception:
        pass

    is_ministre = role == 'MINISTRE'

    if is_ministre:
        arbitres = Arbitre.objects.select_related('personne', 'discipline', 'institution').order_by('personne__nom')
    elif role == 'FEDERATION_SECRETARY' and institution:
        arbitres = Arbitre.objects.select_related('personne', 'discipline', 'institution').filter(
            institution__institution_tutelle=institution
        ).order_by('personne__nom')
    elif role in ('LIGUE_SECRETARY', 'INSTITUTION_ADMIN') and institution:
        arbitres = Arbitre.objects.select_related('personne', 'discipline', 'institution').filter(
            institution=institution
        ).order_by('personne__nom')
    else:
        arbitres = Arbitre.objects.none()

    stats = {
        'total': arbitres.count(),
        'national': arbitres.filter(niveau='NATIONAL').count(),
        'provincial': arbitres.filter(niveau='PROVINCIAL').count(),
        'provinces': arbitres.values('institution__province_admin').distinct().count(),
    }

    disciplines = DisciplineSport.objects.filter(actif=True).order_by('designation')

    return render(request, 'gouvernance/ministre_arbitres_list.html', {
        'arbitres': arbitres,
        'stats': stats,
        'disciplines': disciplines,
        'is_ministre': is_ministre,
    })
