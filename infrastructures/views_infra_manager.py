"""
Vues pour le Gestionnaire d'Infrastructure (rôle INFRA_MANAGER).
Accès aux tableaux de bord, maintenance, réservations et photos de l'infrastructure assignée.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import get_messages

from core.permissions import require_role
from .models import Infrastructure, PhotoInfrastructure, MaintenanceLog, ZoneStade, Evenement


def _get_infrastructure_for_manager(request):
    """Retourne l'infrastructure associée au profil INFRA_MANAGER ou None."""
    try:
        profil = request.user.profil_sisep
        if profil.role != 'INFRA_MANAGER' or not profil.actif:
            return None
        return profil.infrastructure
    except Exception:
        return None


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_dashboard(request):
    """Tableau de bord du gestionnaire d'infrastructure."""
    # Ne pas afficher sur le dashboard les messages des autres interfaces
    list(get_messages(request))
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        messages.error(request, "Aucune infrastructure n'est associée à votre compte.")
        return redirect('core:home')
    context = {
        'infrastructure': infrastructure,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_dashboard.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_maintenance(request):
    """Journal de maintenance de l'infrastructure."""
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        messages.error(request, "Aucune infrastructure n'est associée à votre compte.")
        return redirect('core:home')
    maintenance_logs = list(infrastructure.maintenance_logs.all().order_by('-date_intervention'))
    context = {
        'infrastructure': infrastructure,
        'maintenance_logs': maintenance_logs,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_maintenance.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_reservations(request):
    """Réservations / planning de l'infrastructure (placeholder)."""
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        messages.error(request, "Aucune infrastructure n'est associée à votre compte.")
        return redirect('core:home')
    context = {
        'infrastructure': infrastructure,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_reservations.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_photos(request):
    """Galerie photos de l'infrastructure."""
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        messages.error(request, "Aucune infrastructure n'est associée à votre compte.")
        return redirect('core:home')
    photos = list(infrastructure.photos.all().order_by('date_upload'))
    context = {
        'infrastructure': infrastructure,
        'photos': photos,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_photos.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_zones(request):
    """Zones du stade (Tribune d'honneur, Latérale, Pourtour, etc.) pour la billetterie."""
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        messages.error(request, "Aucune infrastructure n'est associée à votre compte.")
        return redirect('core:home')

    zones = infrastructure.zones.all().order_by('ordre', 'nom')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            nom = (request.POST.get('nom') or '').strip()
            if not nom:
                messages.error(request, "Le nom de la zone est obligatoire.")
            else:
                ordre = request.POST.get('ordre')
                try:
                    ordre = int(ordre) if ordre not in (None, '') else zones.count()
                except (ValueError, TypeError):
                    ordre = zones.count()
                if ZoneStade.objects.filter(infrastructure=infrastructure, nom__iexact=nom).exists():
                    messages.error(request, f"Une zone nommée « {nom} » existe déjà pour ce stade.")
                else:
                    ZoneStade.objects.create(infrastructure=infrastructure, nom=nom, ordre=ordre)
                    messages.success(request, f"Zone « {nom} » créée avec succès.")
            return redirect('infrastructures:infra_manager_zones')
        if action == 'delete':
            zone_uid = request.POST.get('zone_uid')
            try:
                zone = ZoneStade.objects.get(uid=zone_uid, infrastructure=infrastructure)
                nom = zone.nom
                if zone.evenements_tarifs.exists():
                    messages.error(
                        request,
                        f"Impossible de supprimer la zone « {nom} » : elle est utilisée par des événements (tarifs)."
                    )
                else:
                    zone.delete()
                    messages.success(request, f"Zone « {nom} » supprimée.")
            except ZoneStade.DoesNotExist:
                messages.error(request, "Zone introuvable.")
            return redirect('infrastructures:infra_manager_zones')

    context = {
        'infrastructure': infrastructure,
        'zones': zones,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_zones.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_evenements(request):
    """
    Rencontres / événements prévus dans l'infrastructure.
    Liste avec colonne Compétition, barre de recherche et filtre par compétition.
    """
    from gouvernance.models import Competition
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        messages.error(request, "Aucune infrastructure n'est associée à votre compte.")
        return redirect('core:home')
    evenements = Evenement.objects.filter(
        infrastructure=infrastructure,
        actif=True
    ).select_related('organisateur', 'rencontre__journee__competition').order_by('date_evenement', 'heure_debut')
    q = (request.GET.get('q') or '').strip()
    if q:
        evenements = evenements.filter(titre__icontains=q)
    competition_uid = request.GET.get('competition')
    if competition_uid:
        evenements = evenements.filter(rencontre__journee__competition__uid=competition_uid)
    competitions_list = Competition.objects.filter(
        journees__rencontres__evenement__infrastructure=infrastructure,
        journees__rencontres__evenement__actif=True
    ).distinct().order_by('-saison', 'titre')
    context = {
        'infrastructure': infrastructure,
        'evenements': evenements,
        'competitions_list': competitions_list,
        'q': q,
        'competition_filter': competition_uid,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_evenements.html', context)
