# -*- coding: utf-8 -*-
"""
Vues pour les callbacks et validation des paiements Mobile Money
"""

import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from infrastructures.models import Vente, Ticket, EvenementZone
import uuid

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST", "GET"])
def mobile_money_callback(request):
    """
    Callback pour recevoir les notifications de FlexPay
    """
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
        else:
            data = request.GET
        
        logger.info(f"Callback FlexPay reçu: {data}")
        
        # Traiter les données du callback
        order_number = data.get('order_number')
        status = data.get('status')
        
        if order_number and status == 'SUCCESS':
            # Valider le paiement
            return valider_paiement_callback(order_number)
        
        return JsonResponse({'status': 'received'})
        
    except Exception as e:
        logger.error(f"Erreur callback: {str(e)}")
        return JsonResponse({'error': 'Erreur serveur'}, status=500)

def valider_paiement_callback(order_number):
    """
    Valide un paiement via callback
    """
    try:
        # Trouver la vente par order_number
        vente = Vente.objects.filter(reference_paiement__contains=order_number).first()
        if not vente:
            logger.error(f"Vente non trouvée pour order_number: {order_number}")
            return JsonResponse({'error': 'Vente non trouvée'}, status=404)
        
        # Vérifier si les billets existent déjà
        if vente.tickets.exists():
            logger.info(f"Billets déjà créés pour la vente: {vente.uid}")
            return JsonResponse({'status': 'already_processed'})
        
        # Créer les billets
        zone = EvenementZone.objects.filter(evenement=vente.evenement).first()
        if not zone:
            logger.error(f"Zone non trouvée pour l'événement: {vente.evenement}")
            return JsonResponse({'error': 'Zone non trouvée'}, status=404)
        
        tickets = []
        for i in range(1):  # 1 billet par défaut
            ticket = Ticket.objects.create(
                uid=uuid.uuid4(),
                evenement_zone=zone,
                vente=vente,
                statut='VENDU',
                date_creation=timezone.now()
            )
            tickets.append(ticket)
        
        logger.info(f"{len(tickets)} billets créés pour la vente: {vente.uid}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'{len(tickets)} billets créés',
            'tickets': [{'uid': str(t.uid)} for t in tickets]
        })
        
    except Exception as e:
        logger.error(f"Erreur validation callback: {str(e)}")
        return JsonResponse({'error': 'Erreur validation'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def verifier_statut_paiement(request, order_number):
    """
    Vérifie le statut d'un paiement
    """
    try:
        from public.mobile_money_integration import MobileMoneyPaymentProcessor
        
        processor = MobileMoneyPaymentProcessor()
        statut = processor.verifier_paiement(order_number)
        
        return JsonResponse(statut)
        
    except Exception as e:
        logger.error(f"Erreur vérification statut: {str(e)}")
        return JsonResponse({'error': 'Erreur serveur'}, status=500)

def valider_paiement_simplifie(request, vente_uid):
    """
    Callback qui CRÉE les billets après paiement confirmé
    """
    try:
        vente = Vente.objects.get(uid=vente_uid)
        
        # Vérifier si les billets existent déjà
        if vente.tickets.exists():
            return JsonResponse({'status': 'error', 'message': 'Billets déjà créés'})
        
        # Récupérer la zone (première zone disponible)
        zone = EvenementZone.objects.filter(evenement=vente.evenement).first()
        if not zone:
            return JsonResponse({'status': 'error', 'message': 'Zone non trouvée'})
        
        # Créer les billets EN VENDU (paiement confirmé)
        tickets = []
        for i in range(1):  # 1 billet par défaut
            ticket = Ticket.objects.create(
                uid=uuid.uuid4(),
                evenement_zone=zone,
                vente=vente,
                statut='VENDU',  # Directement VENDU après paiement confirmé
                date_creation=timezone.now()
            )
            tickets.append(ticket)
        
        return JsonResponse({
            'status': 'success',
            'message': f'{len(tickets)} billets créés et vendus',
            'tickets': [{'uid': str(t.uid)} for t in tickets]
        })
        
    except Vente.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vente non trouvée'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# Ajouter les décorateurs
valider_paiement_simplifie = csrf_exempt(require_http_methods(["GET", "POST"])(valider_paiement_simplifie))
