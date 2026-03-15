# -*- coding: utf-8 -*-
"""
Vues billetterie numérique — Événements, zones, tickets, ventes.
Vérification ticket (QR/UUID) pour lutte anti-fraude à l'entrée des stades.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Count, Sum

from .models import Ticket, Evenement, ZoneStade, EvenementZone, Vente, Infrastructure
from gouvernance.models import Rencontre
from core.permissions import require_role


def verifier_ticket(request, ticket_uid):
    """
    Vérification d'un ticket par UUID (scan QR à l'entrée).
    GET : affiche le statut (valide / déjà utilisé / invalide).
    POST : marque le ticket comme utilisé (réservé au personnel autorisé).
    """
    ticket = None
    try:
        ticket = Ticket.objects.select_related(
            'evenement_zone__evenement__infrastructure',
            'evenement_zone__zone_stade',
            'vente',
        ).get(uid=ticket_uid)
    except Ticket.DoesNotExist:
        return render(request, 'infrastructures/verifier_ticket.html', {
            'ticket': None,
            'valide': False,
            'message': 'Ticket introuvable ou code invalide.',
        })

    evenement = ticket.evenement_zone.evenement
    zone = ticket.evenement_zone.zone_stade
    infras = evenement.infrastructure

    if request.method == 'POST':
        # Marquer comme utilisé (anti-fraude : un seul passage)
        if not request.user.is_authenticated:
            from django.urls import reverse
            from urllib.parse import quote
            messages.error(request, 'Vous devez être connecté pour enregistrer l\'entrée.')
            next_url = quote(request.build_absolute_uri(request.get_full_path()))
            return redirect(reverse('core:login') + '?next=' + next_url)
        try:
            profil = request.user.profil_sisep
            if profil.role not in ('INFRA_MANAGER', 'INSTITUTION_ADMIN', 'DIRECTEUR_PROVINCIAL'):
                messages.error(request, 'Seul le personnel autorisé peut enregistrer l\'entrée.')
        except Exception:
            messages.error(request, 'Profil utilisateur introuvable.')
            return render(request, 'infrastructures/verifier_ticket.html', {
                'ticket': ticket,
                'evenement': evenement,
                'zone': zone,
                'infrastructure': infras,
                'valide': ticket.statut == 'VENDU',
                'deja_utilise': ticket.statut == 'UTILISE',
            })

        if ticket.statut != 'VENDU':
            messages.warning(request, f'Ce ticket n\'est pas en état « Vendu » (statut: {ticket.get_statut_display()}). Entrée non enregistrée.')
        else:
            ticket.statut = 'UTILISE'
            ticket.date_utilisation = timezone.now()
            ticket.save(update_fields=['statut', 'date_utilisation'])
            messages.success(request, 'Entrée enregistrée. Bon match !')
        return redirect('infrastructures:verifier_ticket', ticket_uid=ticket_uid)

    # GET : affichage du statut
    valide = ticket.statut == 'VENDU'
    deja_utilise = ticket.statut == 'UTILISE'
    if ticket.statut == 'DISPONIBLE':
        message = 'Ce ticket n\'a pas été vendu. Présentez un ticket acheté officiellement.'
    elif deja_utilise:
        message = 'Ce ticket a déjà été utilisé à l\'entrée. Double utilisation impossible.'
    elif valide:
        message = 'Ticket valide. Présentez ce ticket au contrôle.'
    else:
        message = f'Statut du ticket : {ticket.get_statut_display()}.'

    return render(request, 'infrastructures/verifier_ticket.html', {
        'ticket': ticket,
        'evenement': evenement,
        'zone': zone,
        'infrastructure': infras,
        'valide': valide,
        'deja_utilise': deja_utilise,
        'message': message,
    })



@login_required
@require_role('INFRA_MANAGER')
def infra_manager_rencontres_list(request):
    """
    Liste des rencontres programmées dans l'infrastructure du gestionnaire.
    Avec recherche et filtres.
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
    
    # Récupérer toutes les rencontres dans ce stade
    rencontres = Rencontre.objects.filter(
        stade=infrastructure
    ).select_related(
        'journee__competition__organisateur',
        'equipe_a',
        'equipe_b',
        'evenement'
    ).prefetch_related(
        'evenement__zones_tarifs__zone_stade'
    ).order_by('-date_heure')
    
    # Recherche
    search_query = request.GET.get('search', '').strip()
    if search_query:
        rencontres = rencontres.filter(
            Q(equipe_a__nom_officiel__icontains=search_query) |
            Q(equipe_b__nom_officiel__icontains=search_query) |
            Q(journee__competition__titre__icontains=search_query)
        )
    
    # Filtre par statut
    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        rencontres = rencontres.filter(statut=statut_filter)
    
    # Filtre par période
    periode_filter = request.GET.get('periode', '')
    if periode_filter == 'a_venir':
        rencontres = rencontres.filter(date_heure__gte=timezone.now())
    elif periode_filter == 'passees':
        rencontres = rencontres.filter(date_heure__lt=timezone.now())
    
    # Ajouter des statistiques pour chaque rencontre
    for rencontre in rencontres:
        if rencontre.evenement:
            rencontre.billetterie_configuree = rencontre.evenement.zones_tarifs.exists()
            rencontre.tickets_vendus = Ticket.objects.filter(
                evenement_zone__evenement=rencontre.evenement,
                statut='VENDU'
            ).count()
            rencontre.total_ventes = Vente.objects.filter(
                evenement=rencontre.evenement
            ).aggregate(total=Sum('montant_total'))['total'] or 0
        else:
            rencontre.billetterie_configuree = False
            rencontre.tickets_vendus = 0
            rencontre.total_ventes = 0
    
    # Statistiques globales
    stats = {
        'total': rencontres.count(),
        'a_venir': Rencontre.objects.filter(stade=infrastructure, date_heure__gte=timezone.now()).count(),
        'passees': Rencontre.objects.filter(stade=infrastructure, date_heure__lt=timezone.now()).count(),
        'configurees': Rencontre.objects.filter(
            stade=infrastructure,
            evenement__zones_tarifs__isnull=False
        ).distinct().count(),
    }
    
    context = {
        'infrastructure': infrastructure,
        'rencontres': rencontres,
        'stats': stats,
        'search_query': search_query,
        'statut_filter': statut_filter,
        'periode_filter': periode_filter,
        'statut_choices': Rencontre.STATUT_CHOICES,
        'user_role': 'infra_manager',
    }
    
    return render(request, 'infrastructures/infra_manager_rencontres_list.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_rencontre_configurer_billetterie(request, rencontre_uid):
    """
    Configuration de la billetterie pour une rencontre spécifique.
    Définir les tarifs par zone et générer les billets.
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
    
    rencontre = get_object_or_404(
        Rencontre,
        uid=rencontre_uid,
        stade=infrastructure
    )
    
    if not rencontre.evenement:
        messages.error(request, "L'événement billetterie n'a pas été créé pour cette rencontre.")
        return redirect('infrastructures:infra_manager_rencontres_list')
    
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
                        
                        # Vérifier que la capacité ne dépasse pas la capacité de la zone
                        if zone.capacite and capacite_int > zone.capacite:
                            messages.warning(request, f"La capacité pour {zone.nom} dépasse la capacité de la zone ({zone.capacite} places).")
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
            return redirect('infrastructures:infra_manager_rencontre_configurer_billetterie', rencontre_uid=rencontre_uid)
        
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
            
            return redirect('infrastructures:infra_manager_rencontre_configurer_billetterie', rencontre_uid=rencontre_uid)
    
    context = {
        'infrastructure': infrastructure,
        'rencontre': rencontre,
        'evenement': evenement,
        'zones_stade': zones_stade,
        'tarifs_existants': tarifs_existants,
        'user_role': 'infra_manager',
    }
    
    return render(request, 'infrastructures/infra_manager_rencontre_configurer_billetterie.html', context)



@login_required
@require_role('INFRA_MANAGER')
def infra_manager_rencontre_statistiques(request, rencontre_uid):
    """
    Statistiques et graphiques de vente pour une rencontre.
    Affiche les zones configurées avec possibilité d'accéder au détail de chaque zone.
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
    
    rencontre = get_object_or_404(
        Rencontre,
        uid=rencontre_uid,
        stade=infrastructure
    )
    
    if not rencontre.evenement:
        messages.error(request, "L'événement billetterie n'existe pas pour cette rencontre.")
        return redirect('infrastructures:infra_manager_rencontres_list')
    
    evenement = rencontre.evenement
    
    # Vérifier si la billetterie est configurée
    zones_configurees = EvenementZone.objects.filter(
        evenement=evenement
    ).select_related('zone_stade').order_by('zone_stade__ordre', 'zone_stade__nom')
    
    if not zones_configurees.exists():
        messages.warning(request, "La billetterie n'a pas encore été configurée pour cette rencontre.")
        return redirect('infrastructures:infra_manager_rencontre_configurer_billetterie', rencontre_uid=rencontre_uid)
    
    # Statistiques globales
    total_tickets = Ticket.objects.filter(evenement_zone__evenement=evenement).count()
    tickets_vendus = Ticket.objects.filter(evenement_zone__evenement=evenement, statut='VENDU').count()
    tickets_utilises = Ticket.objects.filter(evenement_zone__evenement=evenement, statut='UTILISE').count()
    tickets_disponibles = Ticket.objects.filter(evenement_zone__evenement=evenement, statut='DISPONIBLE').count()
    
    # Montant total des ventes
    total_ventes = Vente.objects.filter(evenement=evenement).aggregate(
        total=Sum('montant_total')
    )['total'] or 0
    
    # Nombre de ventes
    nb_ventes = Vente.objects.filter(evenement=evenement).count()
    
    # Ventes par canal
    ventes_par_canal = Vente.objects.filter(evenement=evenement).values('canal').annotate(
        count=Count('uid'),
        montant=Sum('montant_total')
    ).order_by('-montant')
    
    # Statistiques par zone
    for zone in zones_configurees:
        zone.tickets_total = zone.tickets.count()
        zone.tickets_vendus_count = zone.tickets.filter(statut='VENDU').count()
        zone.tickets_utilises_count = zone.tickets.filter(statut='UTILISE').count()
        zone.tickets_disponibles_count = zone.tickets.filter(statut='DISPONIBLE').count()
        
        # Pourcentage de vente
        if zone.tickets_total > 0:
            zone.pourcentage_vente = round((zone.tickets_vendus_count / zone.tickets_total) * 100, 1)
        else:
            zone.pourcentage_vente = 0
        
        # Montant des ventes pour cette zone
        zone.montant_ventes = Vente.objects.filter(
            tickets__evenement_zone=zone
        ).aggregate(total=Sum('montant_total'))['total'] or 0
    
    # Ventes récentes (dernières 10)
    ventes_recentes = Vente.objects.filter(
        evenement=evenement
    ).select_related('caissier').order_by('-date_vente')[:10]
    
    # Données pour les graphiques (format JSON)
    import json
    
    # Graphique par zone (ventes)
    zones_labels = [z.zone_stade.nom for z in zones_configurees]
    zones_vendus = [z.tickets_vendus_count for z in zones_configurees]
    zones_disponibles = [z.tickets_disponibles_count for z in zones_configurees]
    
    graphique_zones = {
        'labels': zones_labels,
        'vendus': zones_vendus,
        'disponibles': zones_disponibles,
    }
    
    # Graphique par canal
    canaux_labels = [v['canal'] for v in ventes_par_canal]
    canaux_montants = [float(v['montant']) for v in ventes_par_canal]
    
    graphique_canaux = {
        'labels': canaux_labels,
        'montants': canaux_montants,
    }
    
    context = {
        'infrastructure': infrastructure,
        'rencontre': rencontre,
        'evenement': evenement,
        'zones_configurees': zones_configurees,
        'total_tickets': total_tickets,
        'tickets_vendus': tickets_vendus,
        'tickets_utilises': tickets_utilises,
        'tickets_disponibles': tickets_disponibles,
        'total_ventes': total_ventes,
        'nb_ventes': nb_ventes,
        'ventes_par_canal': ventes_par_canal,
        'ventes_recentes': ventes_recentes,
        'graphique_zones_json': json.dumps(graphique_zones),
        'graphique_canaux_json': json.dumps(graphique_canaux),
        'user_role': 'infra_manager',
    }
    
    return render(request, 'infrastructures/infra_manager_rencontre_statistiques.html', context)


@login_required
@require_role('INFRA_MANAGER')
def infra_manager_zone_detail(request, zone_evenement_uid):
    """
    Détail d'une zone spécifique: statistiques et liste des ventes.
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
    
    zone_evenement = get_object_or_404(
        EvenementZone,
        uid=zone_evenement_uid,
        evenement__infrastructure=infrastructure
    )
    
    evenement = zone_evenement.evenement
    zone_stade = zone_evenement.zone_stade
    
    # Récupérer la rencontre associée
    try:
        rencontre = Rencontre.objects.get(evenement=evenement)
    except Rencontre.DoesNotExist:
        rencontre = None
    
    # Statistiques de la zone
    tickets_total = zone_evenement.tickets.count()
    tickets_vendus = zone_evenement.tickets.filter(statut='VENDU').count()
    tickets_utilises = zone_evenement.tickets.filter(statut='UTILISE').count()
    tickets_disponibles = zone_evenement.tickets.filter(statut='DISPONIBLE').count()
    
    # Pourcentage
    if tickets_total > 0:
        pourcentage_vente = round((tickets_vendus / tickets_total) * 100, 1)
        pourcentage_utilisation = round((tickets_utilises / tickets_total) * 100, 1)
    else:
        pourcentage_vente = 0
        pourcentage_utilisation = 0
    
    # Montant total des ventes pour cette zone
    montant_total = Vente.objects.filter(
        tickets__evenement_zone=zone_evenement
    ).aggregate(total=Sum('montant_total'))['total'] or 0
    
    # Liste des ventes pour cette zone
    ventes = Vente.objects.filter(
        tickets__evenement_zone=zone_evenement
    ).select_related('caissier').prefetch_related('tickets').distinct().order_by('-date_vente')
    
    # Ajouter le nombre de tickets par vente
    for vente in ventes:
        vente.nb_tickets_zone = vente.tickets.filter(evenement_zone=zone_evenement).count()
    
    context = {
        'infrastructure': infrastructure,
        'zone_evenement': zone_evenement,
        'zone_stade': zone_stade,
        'evenement': evenement,
        'rencontre': rencontre,
        'tickets_total': tickets_total,
        'tickets_vendus': tickets_vendus,
        'tickets_utilises': tickets_utilises,
        'tickets_disponibles': tickets_disponibles,
        'pourcentage_vente': pourcentage_vente,
        'pourcentage_utilisation': pourcentage_utilisation,
        'montant_total': montant_total,
        'ventes': ventes,
        'user_role': 'infra_manager',
    }
    
    return render(request, 'infrastructures/infra_manager_zone_detail.html', context)
