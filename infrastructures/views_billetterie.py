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

from .models import Ticket, Evenement, ZoneStade, EvenementZone, Vente


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
