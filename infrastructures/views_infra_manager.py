"""
Vues pour le Gestionnaire d'Infrastructure (rôle INFRA_MANAGER).
Accès aux tableaux de bord, maintenance, réservations et photos de l'infrastructure assignée.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import get_messages
from django.utils import timezone

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
    
    # Importer les modèles nécessaires
    from infrastructures.models import Vente, Ticket, EvenementZone
    from django.db.models import Sum, Count, Q
    from datetime import datetime, timedelta
    import json
    
    # Calculer la recette du mois (seulement paiements validés)
    now = timezone.now()
    first_day_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    recette_mois = 0
    ventes_mois = 0
    tickets_vendus_mois = 0
    
    # Parcourir toutes les ventes du mois pour les infrastructures
    from gouvernance.models import Rencontre
    rencontres_infra = Rencontre.objects.filter(stade=infrastructure)
    
    for rencontre in rencontres_infra:
        if rencontre.evenement:
            ventes_rencontre = Vente.objects.filter(
                evenement=rencontre.evenement,
                date_vente__gte=first_day_month,
                date_vente__lte=now
            )
            
            for vente in ventes_rencontre:
                try:
                    if vente.notes:
                        notes_data = json.loads(vente.notes)
                        statut = notes_data.get('statut_paiement', 'INITIE')
                        if statut == 'VALIDE':
                            recette_mois += float(vente.montant_total)
                            ventes_mois += 1
                except (json.JSONDecodeError, TypeError):
                    continue
    
    # Calculer les tickets vendus du mois
    for rencontre in rencontres_infra:
        if rencontre.evenement:
            tickets_vendus_mois += Ticket.objects.filter(
                evenement_zone__evenement=rencontre.evenement,
                statut='VENDU',
                date_creation__gte=first_day_month,
                date_creation__lte=now
            ).count()
    
    # Calculer les réservations du mois (rencontres programmées)
    reservations_mois = 0
    for rencontre in rencontres_infra:
        if rencontre.date_heure and rencontre.date_heure >= first_day_month and rencontre.date_heure <= now:
            reservations_mois += 1
    
    # Réservations de la semaine (placeholder - données factices)
    reservations_week = 12
    
    # Taux de présence (placeholder - calcul basé sur les maintenances)
    taux_presence = 85
    
    # Maintenances récentes
    recent_maintenance = list(infrastructure.maintenance_logs.all().order_by('-date_intervention')[:5])
    
    # Photos (pour la card galerie)
    photos_count = infrastructure.photos.count()
    
    # Réservations aujourd'hui (placeholder - données factices)
    from datetime import date
    today = date.today()
    reservations_today = []  # Placeholder
    
    # Calculer les événements à venir
    evenements_a_venir = []
    # Utiliser la relation correcte: infrastructure.rencontres (pas infrastructure.stade.rencontres)
    evenements_a_venir = list(
        infrastructure.rencontres.filter(
            date_heure__gte=now
        ).order_by('date_heure')[:3]
    )
    
    context = {
        'infrastructure': infrastructure,
        'user_role': 'infra_manager',
        # Données réelles
        'recette_mois': recette_mois,
        'ventes_mois': ventes_mois,
        'tickets_vendus_mois': tickets_vendus_mois,
        # Données existantes
        'reservations_week': reservations_week,
        'reservations_mois': reservations_mois,
        'taux_presence': taux_presence,
        'recent_maintenance': recent_maintenance,
        'photos_count': photos_count,
        'reservations_today': reservations_today,
        # Événements à venir
        'evenements_a_venir': evenements_a_venir,
        # Ajouter now pour le template
        'now': now,
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
    Le gestionnaire voit les matchs planifiés par la ligue et les réservations privées.
    """
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        messages.error(request, "Aucune infrastructure n'est associée à votre compte.")
        return redirect('core:home')
    
    # Événements officiels (matchs) - exclure les réservations
    evenements = Evenement.objects.filter(
        infrastructure=infrastructure,
        actif=True
    ).exclude(type_evenement='RESERVATION').select_related('organisateur').order_by('date_evenement', 'heure_debut')
    
    # Réservations privées (non officielles)
    reservations = Evenement.objects.filter(
        infrastructure=infrastructure,
        actif=True,
        type_evenement='RESERVATION'
    ).select_related('organisateur').order_by('date_evenement', 'heure_debut')
    
    context = {
        'infrastructure': infrastructure,
        'evenements': evenements,
        'reservations': reservations,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_evenements.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_create_reservation(request):
    """
    Créer une réservation privée pour l'infrastructure.
    Événements non officiels (activités privées, événements spéciaux, etc.).
    """
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        messages.error(request, "Aucune infrastructure n'est associée à votre compte.")
        return redirect('core:home')
    
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        date_evenement = request.POST.get('date_evenement', '')
        heure_debut = request.POST.get('heure_debut', '')
        description = request.POST.get('description', '').strip()
        
        # Validation
        if not titre or not date_evenement or not heure_debut:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
        else:
            try:
                from datetime import datetime
                from django.utils import timezone
                
                # Créer l'événement de réservation
                reservation = Evenement.objects.create(
                    titre=titre,
                    infrastructure=infrastructure,
                    type_evenement='RESERVATION',  # Type pour réservations privées
                    date_evenement=date_evenement,
                    heure_debut=heure_debut,
                    description=description,
                    organisateur=None,  # Pas d'institution obligatoire pour les réservations privées
                    actif=True,
                    date_creation=timezone.now()
                )
                
                messages.success(request, f"Réservation '{titre}' créée avec succès!")
                return redirect('infrastructures:infra_manager_evenements')
                
            except Exception as e:
                messages.error(request, f"Erreur lors de la création: {str(e)}")
    
    context = {
        'infrastructure': infrastructure,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_create_reservation.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_reservation_configurer_billetterie(request, evenement_uid):
    """
    Configuration de la billetterie pour une réservation privée.
    Définir les tarifs par zone et générer les billets.
    """
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        messages.error(request, "Aucune infrastructure n'est associée à votre compte.")
        return redirect('core:home')
    
    # Récupérer l'événement de réservation
    from infrastructures.models import Evenement
    evenement = get_object_or_404(
        Evenement,
        uid=evenement_uid,
        infrastructure=infrastructure,
        type_evenement='RESERVATION'
    )
    
    # Récupérer les zones du stade
    zones_stade = infrastructure.zones.all().order_by('ordre', 'nom')
    
    # Récupérer les tarifs existants pour cet événement
    from infrastructures.models import EvenementZone
    tarifs_existants = EvenementZone.objects.filter(evenement=evenement).select_related('zone_stade')
    
    if request.method == 'POST':
        # Traiter la configuration des tarifs pour chaque zone
        from infrastructures.models import EvenementZone
        
        for zone in zones_stade:
            prix_unitaire = request.POST.get(f'prix_zone_{zone.uid}', '').strip()
            capacite_max = request.POST.get(f'capacite_zone_{zone.uid}', '').strip()
            
            if prix_unitaire and capacite_max:
                try:
                    # Créer ou mettre à jour le tarif pour cette zone
                    EvenementZone.objects.update_or_create(
                        evenement=evenement,
                        zone_stade=zone,
                        defaults={
                            'prix_unitaire': float(prix_unitaire),
                            'capacite_max': int(capacite_max),
                            'disponible': True
                        }
                    )
                except (ValueError, TypeError):
                    continue
        
        messages.success(request, f"Billetterie pour '{evenement.titre}' configurée avec succès!")
        return redirect('infrastructures:infra_manager_rencontres_list')
    
    context = {
        'infrastructure': infrastructure,
        'evenement': evenement,
        'zones_stade': zones_stade,
        'tarifs_existants': tarifs_existants,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_reservation_configurer_billetterie.html', context)
