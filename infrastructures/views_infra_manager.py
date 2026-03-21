# -*- coding: utf-8 -*-
"""
Vues pour le gestionnaire d'infrastructure (INFRA_MANAGER).
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from core.permissions import require_role
from infrastructures.models import Infrastructure, MaintenanceLog, StateChangeLog, ReservationSlot, PhotoInfrastructure


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_dashboard(request):
    """Tableau de bord du gestionnaire d'infrastructure."""
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    infrastructure = profil.infrastructure
    if not infrastructure:
        messages.error(request, "Vous n'êtes pas associé à une infrastructure.")
        return redirect('core:home')
    
    today = timezone.now().date()
    reservations_today = ReservationSlot.objects.filter(infrastructure=infrastructure, date_reservation=today).select_related('club').order_by('heure_debut')
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    reservations_week = ReservationSlot.objects.filter(infrastructure=infrastructure, date_reservation__range=[week_start, week_end]).count()
    recent_maintenance = MaintenanceLog.objects.filter(infrastructure=infrastructure).order_by('-date_intervention')[:5]
    recent_state_changes = StateChangeLog.objects.filter(infrastructure=infrastructure).order_by('-date_creation')[:5]
    seven_days_ago = today - timedelta(days=7)
    total_reservations = ReservationSlot.objects.filter(infrastructure=infrastructure, date_reservation__gte=seven_days_ago).count()
    present_reservations = ReservationSlot.objects.filter(infrastructure=infrastructure, date_reservation__gte=seven_days_ago, present=True).count()
    taux_presence = round((present_reservations / total_reservations * 100), 1) if total_reservations > 0 else 0
    photos_count = PhotoInfrastructure.objects.filter(infrastructure=infrastructure).count()
    
    context = {
        'infrastructure': infrastructure,
        'reservations_today': reservations_today,
        'reservations_week': reservations_week,
        'recent_maintenance': recent_maintenance,
        'recent_state_changes': recent_state_changes,
        'taux_presence': taux_presence,
        'photos_count': photos_count,
        'user_role': 'infra_manager',
    }
    return render(request, 'infrastructures/infra_manager_dashboard.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_maintenance(request):
    """Journal de maintenance de l'infrastructure."""
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    infrastructure = profil.infrastructure
    if not infrastructure:
        messages.error(request, "Vous n'êtes pas associé à une infrastructure.")
        return redirect('core:home')
    
    maintenance_logs = MaintenanceLog.objects.filter(infrastructure=infrastructure).order_by('-date_intervention')
    context = {'infrastructure': infrastructure, 'maintenance_logs': maintenance_logs, 'user_role': 'infra_manager'}
    return render(request, 'infrastructures/infra_manager_maintenance.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_reservations(request):
    """Gestion des réservations de l'infrastructure."""
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    infrastructure = profil.infrastructure
    if not infrastructure:
        messages.error(request, "Vous n'êtes pas associé à une infrastructure.")
        return redirect('core:home')
    
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    reservations = ReservationSlot.objects.filter(infrastructure=infrastructure, date_reservation__range=[today, next_week]).select_related('club').order_by('date_reservation', 'heure_debut')
    context = {'infrastructure': infrastructure, 'reservations': reservations, 'user_role': 'infra_manager'}
    return render(request, 'infrastructures/infra_manager_reservations.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_photos(request):
    """Galerie photos de l'infrastructure."""
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    infrastructure = profil.infrastructure
    if not infrastructure:
        messages.error(request, "Vous n'êtes pas associé à une infrastructure.")
        return redirect('core:home')
    
    photos = PhotoInfrastructure.objects.filter(infrastructure=infrastructure).order_by('-date_upload')
    context = {'infrastructure': infrastructure, 'photos': photos, 'user_role': 'infra_manager'}
    return render(request, 'infrastructures/infra_manager_photos.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_evenements(request):
    """
    Liste des rencontres programmées dans l'infrastructure du gestionnaire.
    Permet de gérer la billetterie.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    infrastructure = profil.infrastructure
    if not infrastructure:
        messages.error(request, "Vous n'êtes pas associé à une infrastructure.")
        return redirect('core:home')
    
    # Importer les modèles nécessaires
    from gouvernance.models import Rencontre
    
    # Récupérer les rencontres à venir dans ce stade
    rencontres = Rencontre.objects.filter(
        stade=infrastructure,
        date_heure__gte=timezone.now()
    ).select_related(
        'journee__competition',
        'equipe_a',
        'equipe_b',
        'evenement'
    ).prefetch_related(
        'evenement__zones_tarifs__zone_stade'
    ).order_by('date_heure')
    
    context = {
        'infrastructure': infrastructure,
        'rencontres': rencontres,
        'user_role': 'infra_manager',
    }
    
    return render(request, 'infrastructures/infra_manager_evenements.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_evenement_billetterie(request, rencontre_uid):
    """
    Configuration de la billetterie pour une rencontre spécifique.
    """
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        return redirect('infrastructures:infra_manager_dashboard')
    
    # Importer les modèles nécessaires
    from gouvernance.models import Rencontre
    from infrastructures.models import Evenement, EvenementZone
    from django.shortcuts import get_object_or_404
    
    rencontre = get_object_or_404(
        Rencontre,
        uid=rencontre_uid,
        stade=infrastructure
    )
    
    if not rencontre.evenement:
        messages.error(request, "L'événement billetterie n'a pas été créé pour cette rencontre.")
        return redirect('infrastructures:infra_manager_evenements')
    
    evenement = rencontre.evenement
    
    # Récupérer les zones du stade
    zones_stade = infrastructure.zones.all().order_by('ordre', 'nom')
    
    # Récupérer les tarifs déjà configurés
    tarifs_existants = EvenementZone.objects.filter(
        evenement=evenement
    ).select_related('zone_stade')
    
    # Ajouter les compteurs de tickets à chaque tarif
    for tarif in tarifs_existants:
        tarif.tickets_vendus_count = tarif.tickets.filter(statut='VENDU').count()
        tarif.tickets_utilises_count = tarif.tickets.filter(statut='UTILISE').count()
        tarif.tickets_disponibles_count = tarif.tickets.filter(statut='DISPONIBLE').count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'configurer_tarifs':
            # Sauvegarder les tarifs pour chaque zone
            for zone in zones_stade:
                prix_key = f'prix_zone_{zone.uid}'
                capacite_key = f'capacite_zone_{zone.uid}'
                
                prix = request.POST.get(prix_key)
                capacite = request.POST.get(capacite_key)
                
                if prix and capacite:
                    try:
                        prix_decimal = float(prix)
                        capacite_int = int(capacite)
                        
                        # Vérifier que la capacité ne dépasse pas la capacité du stade
                        if infrastructure.capacite_spectateurs and capacite_int > infrastructure.capacite_spectateurs:
                            messages.warning(request, f"La capacité pour {zone.nom} dépasse la capacité totale du stade ({infrastructure.capacite_spectateurs} places).")
                            continue
                        
                        # Créer ou mettre à jour le tarif
                        EvenementZone.objects.update_or_create(
                            evenement=evenement,
                            zone_stade=zone,
                            defaults={
                                'prix_unitaire': prix_decimal,
                                'capacite_max': capacite_int,
                                'devise': 'CDF'
                            }
                        )
                    except (ValueError, TypeError):
                        messages.error(request, f"Valeurs invalides pour {zone.nom}")
                        continue
            
            messages.success(request, "Tarifs configurés avec succès!")
            return redirect('infrastructures:infra_manager_evenement_billetterie', rencontre_uid=rencontre_uid)
        
        elif action == 'generer_billets':
            # Générer les billets pour toutes les zones configurées
            total_generes = 0
            for tarif in tarifs_existants:
                nb_generes = tarif.generer_tickets()
                total_generes += nb_generes
            
            if total_generes > 0:
                messages.success(request, f"{total_generes} billets générés avec succès!")
            else:
                messages.info(request, "Tous les billets ont déjà été générés.")
            
            return redirect('infrastructures:infra_manager_evenement_billetterie', rencontre_uid=rencontre_uid)
    
    context = {
        'infrastructure': infrastructure,
        'rencontre': rencontre,
        'evenement': evenement,
        'zones_stade': zones_stade,
        'tarifs_existants': tarifs_existants,
        'user_role': 'infra_manager',
    }
    
    return render(request, 'infrastructures/infra_manager_evenement_billetterie.html', context)
def infra_manager_evenement_billetterie(request, rencontre_uid):
    """
    Configuration de la billetterie pour une rencontre spécifique.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    infrastructure = profil.infrastructure
    if not infrastructure:
        messages.error(request, "Vous n'êtes pas associé à une infrastructure.")
        return redirect('core:home')
    
    # Importer les modèles nécessaires
    from gouvernance.models import Rencontre
    from infrastructures.models import Evenement, EvenementZone
    from django.shortcuts import get_object_or_404
    
    rencontre = get_object_or_404(
        Rencontre,
        uid=rencontre_uid,
        stade=infrastructure
    )
    
    if not rencontre.evenement:
        messages.error(request, "L'événement billetterie n'a pas été créé pour cette rencontre.")
        return redirect('infrastructures:infra_manager_evenements')
    
    evenement = rencontre.evenement
    
    # Récupérer les zones du stade
    zones_stade = infrastructure.zones.all().order_by('ordre', 'nom')
    
    # Récupérer les tarifs déjà configurés
    tarifs_existants = EvenementZone.objects.filter(
        evenement=evenement
    ).select_related('zone_stade')
    
    # Ajouter les compteurs de tickets à chaque tarif
    for tarif in tarifs_existants:
        tarif.tickets_vendus_count = tarif.tickets.filter(statut='VENDU').count()
        tarif.tickets_utilises_count = tarif.tickets.filter(statut='UTILISE').count()
        tarif.tickets_disponibles_count = tarif.tickets.filter(statut='DISPONIBLE').count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'configurer_tarifs':
            # Sauvegarder les tarifs pour chaque zone
            for zone in zones_stade:
                prix_key = f'prix_zone_{zone.uid}'
                capacite_key = f'capacite_zone_{zone.uid}'
                
                prix = request.POST.get(prix_key)
                capacite = request.POST.get(capacite_key)
                
                if prix and capacite:
                    try:
                        prix_decimal = float(prix)
                        capacite_int = int(capacite)
                        
                        # Vérifier que la capacité ne dépasse pas la capacité du stade
                        if infrastructure.capacite_spectateurs and capacite_int > infrastructure.capacite_spectateurs:
                            messages.warning(request, f"La capacité pour {zone.nom} dépasse la capacité totale du stade ({infrastructure.capacite_spectateurs} places).")
                            continue
                        
                        # Créer ou mettre à jour le tarif
                        EvenementZone.objects.update_or_create(
                            evenement=evenement,
                            zone_stade=zone,
                            defaults={
                                'prix_unitaire': prix_decimal,
                                'capacite_max': capacite_int,
                                'devise': 'CDF'
                            }
                        )
                    except (ValueError, TypeError):
                        messages.error(request, f"Valeurs invalides pour {zone.nom}")
                        continue
            
            messages.success(request, "Tarifs configurés avec succès!")
            return redirect('infrastructures:infra_manager_evenement_billetterie', rencontre_uid=rencontre_uid)
        
        elif action == 'generer_billets':
            # Générer les billets pour toutes les zones configurées
            total_generes = 0
            for tarif in tarifs_existants:
                nb_generes = tarif.generer_tickets()
                total_generes += nb_generes
            
            if total_generes > 0:
                messages.success(request, f"{total_generes} billets générés avec succès!")
            else:
                messages.info(request, "Tous les billets ont déjà été générés.")
            
            return redirect('infrastructures:infra_manager_evenement_billetterie', rencontre_uid=rencontre_uid)
    
    context = {
        'infrastructure': infrastructure,
        'rencontre': rencontre,
        'evenement': evenement,
        'zones_stade': zones_stade,
        'tarifs_existants': tarifs_existants,
        'user_role': 'infra_manager',
    }
    
    return render(request, 'infrastructures/infra_manager_evenement_billetterie.html', context)
def infra_manager_evenement_billetterie(request, rencontre_uid):
    """
    Configuration de la billetterie pour une rencontre spécifique.
    """
    infrastructure = _get_infrastructure_for_manager(request)
    if not infrastructure:
        return redirect('infrastructures:infra_manager_dashboard')
    
    # Importer les modèles nécessaires
    from gouvernance.models import Rencontre
    from infrastructures.models import Evenement, EvenementZone
    from django.shortcuts import get_object_or_404
    
    rencontre = get_object_or_404(
        Rencontre,
        uid=rencontre_uid,
        stade=infrastructure
    )
    
    if not rencontre.evenement:
        messages.error(request, "L'événement billetterie n'a pas été créé pour cette rencontre.")
        return redirect('infrastructures:infra_manager_evenements')
    
    evenement = rencontre.evenement
    
    # Récupérer les zones du stade
    zones_stade = infrastructure.zones.all().order_by('ordre', 'nom')
    
    # Récupérer les tarifs déjà configurés
    tarifs_existants = EvenementZone.objects.filter(
        evenement=evenement
    ).select_related('zone_stade')
    
    # Ajouter les compteurs de tickets à chaque tarif
    for tarif in tarifs_existants:
        tarif.tickets_vendus_count = tarif.tickets.filter(statut='VENDU').count()
        tarif.tickets_utilises_count = tarif.tickets.filter(statut='UTILISE').count()
        tarif.tickets_disponibles_count = tarif.tickets.filter(statut='DISPONIBLE').count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'configurer_tarifs':
            # Sauvegarder les tarifs pour chaque zone
            for zone in zones_stade:
                prix_key = f'prix_zone_{zone.uid}'
                capacite_key = f'capacite_zone_{zone.uid}'
                
                prix = request.POST.get(prix_key)
                capacite = request.POST.get(capacite_key)
                
                if prix and capacite:
                    try:
                        prix_decimal = float(prix)
                        capacite_int = int(capacite)
                        
                        # Vérifier que la capacité ne dépasse pas la capacité du stade
                        if infrastructure.capacite_spectateurs and capacite_int > infrastructure.capacite_spectateurs:
                            messages.warning(request, f"La capacité pour {zone.nom} dépasse la capacité totale du stade ({infrastructure.capacite_spectateurs} places).")
                            continue
                        
                        # Créer ou mettre à jour le tarif
                        EvenementZone.objects.update_or_create(
                            evenement=evenement,
                            zone_stade=zone,
                            defaults={
                                'prix_unitaire': prix_decimal,
                                'capacite_max': capacite_int,
                                'devise': 'CDF'
                            }
                        )
                    except (ValueError, TypeError):
                        messages.error(request, f"Valeurs invalides pour {zone.nom}")
                        continue
            
            messages.success(request, "Tarifs configurés avec succès!")
            return redirect('infrastructures:infra_manager_evenement_billetterie', rencontre_uid=rencontre_uid)
        
        elif action == 'generer_billets':
            # Générer les billets pour toutes les zones configurées
            total_generes = 0
            for tarif in tarifs_existants:
                nb_generes = tarif.generer_tickets()
                total_generes += nb_generes
            
            if total_generes > 0:
                messages.success(request, f"{total_generes} billets générés avec succès!")
            else:
                messages.info(request, "Tous les billets ont déjà été générés.")
            
            return redirect('infrastructures:infra_manager_evenement_billetterie', rencontre_uid=rencontre_uid)
    
    context = {
        'infrastructure': infrastructure,
        'rencontre': rencontre,
        'evenement': evenement,
        'zones_stade': zones_stade,
        'tarifs_existants': tarifs_existants,
        'user_role': 'infra_manager',
    }
    
    return render(request, 'infrastructures/infra_manager_evenement_billetterie.html', context)
