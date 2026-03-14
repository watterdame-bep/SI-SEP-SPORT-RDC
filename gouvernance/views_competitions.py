# -*- coding: utf-8 -*-
"""
Vues pour la gestion des compétitions provinciales par la ligue.
Calendrier, rencontres, billetterie.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from core.permissions import require_role
from gouvernance.models import Institution, Competition, TypeCompetition, Journee, Rencontre
from infrastructures.models import Infrastructure, Evenement, EvenementZone, ZoneStade


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_competitions_list(request):
    """
    Liste des compétitions organisées par la ligue.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer toutes les compétitions de la ligue
    competitions = Competition.objects.filter(
        organisateur=ligue
    ).select_related('type_competition').annotate(
        nb_journees=Count('journees'),
        nb_rencontres=Count('journees__rencontres')
    ).order_by('-saison', 'titre')
    
    # Statistiques
    stats = {
        'total': competitions.count(),
        'actives': competitions.filter(actif=True).count(),
        'saison_actuelle': competitions.filter(saison=f"{timezone.now().year}-{timezone.now().year+1}").count(),
    }
    
    context = {
        'ligue': ligue,
        'competitions': competitions,
        'stats': stats,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_competitions_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_competition_detail(request, competition_uid):
    """
    Détail d'une compétition avec ses journées et rencontres.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    competition = get_object_or_404(
        Competition,
        uid=competition_uid,
        organisateur=ligue
    )
    
    # Récupérer les journées avec leurs rencontres
    journees = competition.journees.prefetch_related(
        'rencontres__equipe_a',
        'rencontres__equipe_b',
        'rencontres__stade'
    ).annotate(
        nb_rencontres=Count('rencontres')
    ).order_by('ordre', 'libelle')
    
    context = {
        'ligue': ligue,
        'competition': competition,
        'journees': journees,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_competition_detail.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_calendrier_competition(request):
    """
    Redirige vers le calendrier de la première compétition active,
    ou affiche une liste de compétitions si plusieurs existent.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer les compétitions actives
    competitions = Competition.objects.filter(
        organisateur=ligue,
        actif=True
    ).select_related('type_competition').order_by('-saison', 'titre')
    
    if competitions.count() == 0:
        messages.warning(request, "Aucune compétition active. Veuillez d'abord créer une compétition.")
        return redirect('gouvernance:ligue_competitions_list')
    
    # Si une seule compétition, rediriger directement vers son calendrier
    if competitions.count() == 1:
        return redirect('gouvernance:ligue_calendrier_rencontres', competition_uid=competitions.first().uid)
    
    # Sinon, afficher la liste des compétitions pour choisir
    context = {
        'ligue': ligue,
        'competitions': competitions,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_calendrier_competition.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_rencontres_billetterie(request):
    """
    Interface de gestion des rencontres et billetterie.
    Le gestionnaire peut définir les tarifs et générer les billets.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer les rencontres à venir avec leurs événements
    rencontres = Rencontre.objects.filter(
        journee__competition__organisateur=ligue,
        date_heure__gte=timezone.now()
    ).select_related(
        'journee__competition',
        'equipe_a',
        'equipe_b',
        'stade',
        'evenement'
    ).prefetch_related(
        'evenement__zones_tarifs__zone_stade'
    ).order_by('date_heure')
    
    context = {
        'ligue': ligue,
        'rencontres': rencontres,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_rencontres_billetterie.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_rencontre_configurer_billetterie(request, rencontre_uid):
    """
    Configuration de la billetterie pour une rencontre spécifique.
    Définir les tarifs par zone et générer les billets.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    rencontre = get_object_or_404(
        Rencontre,
        uid=rencontre_uid,
        journee__competition__organisateur=ligue
    )
    
    if not rencontre.stade:
        messages.error(request, "Cette rencontre n'a pas de stade assigné.")
        return redirect('gouvernance:ligue_rencontres_billetterie')
    
    # Récupérer ou créer l'événement billetterie
    if not rencontre.evenement:
        messages.error(request, "L'événement billetterie n'a pas été créé pour cette rencontre.")
        return redirect('gouvernance:ligue_rencontres_billetterie')
    
    evenement = rencontre.evenement
    
    # Récupérer les zones du stade
    zones_stade = rencontre.stade.zones.all().order_by('ordre', 'nom')
    
    # Récupérer les tarifs déjà configurés
    tarifs_existants = EvenementZone.objects.filter(
        evenement=evenement
    ).select_related('zone_stade')
    
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
                        if rencontre.stade.capacite_spectateurs and capacite_int > rencontre.stade.capacite_spectateurs:
                            messages.warning(request, f"La capacité pour {zone.nom} dépasse la capacité totale du stade ({rencontre.stade.capacite_spectateurs} places).")
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
            return redirect('gouvernance:ligue_rencontre_configurer_billetterie', rencontre_uid=rencontre_uid)
        
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
            
            return redirect('gouvernance:ligue_rencontre_configurer_billetterie', rencontre_uid=rencontre_uid)
    
    # Calculer les statistiques de billetterie
    stats = {}
    for tarif in tarifs_existants:
        nb_tickets = tarif.tickets.count()
        nb_vendus = tarif.tickets.filter(statut='VENDU').count()
        nb_utilises = tarif.tickets.filter(statut='UTILISE').count()
        
        stats[str(tarif.zone_stade.uid)] = {
            'total': nb_tickets,
            'vendus': nb_vendus,
            'utilises': nb_utilises,
            'disponibles': nb_tickets - nb_vendus - nb_utilises,
        }
    
    context = {
        'ligue': ligue,
        'rencontre': rencontre,
        'evenement': evenement,
        'zones_stade': zones_stade,
        'tarifs_existants': tarifs_existants,
        'stats': stats,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_rencontre_configurer_billetterie.html', context)
