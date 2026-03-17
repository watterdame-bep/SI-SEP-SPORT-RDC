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
from django.db import transaction
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
            data = json.loads(request.body) if request.body else {}
        else:
            data = dict(request.GET)
        
        logger.info(f"Callback FlexPay reçu: {data}")
        
        # Extraire les informations du callback
        reference_interne = data.get('reference', data.get('merchant_ref'))
        order_number = data.get('orderNumber', data.get('order_number'))
        status = data.get('status', data.get('transaction_status'))
        
        # LOG DÉTAILLÉ pour déboguer les annulations
        print(f"=" * 80)
        print(f"CALLBACK FLEXPAY REÇU")
        print(f"=" * 80)
        print(f"Référence interne: {reference_interne}")
        print(f"Order Number: {order_number}")
        print(f"Statut brut: {status} (type: {type(status)})")
        print(f"Statut upper: {str(status).upper()}")
        print(f"Message: {data.get('message', data.get('error_message', 'N/A'))}")
        print(f"Data complète: {json.dumps(data, indent=2)}")
        print(f"=" * 80)
        
        if not reference_interne and not order_number:
            logger.error("Callback sans référence ni order_number")
            return JsonResponse({'error': 'Référence manquante'}, status=400)
        
        # Trouver la vente - AMÉLIORATION: chercher aussi par référence interne
        vente = None
        
        # 1. Chercher par order_number dans notes
        if order_number:
            ventes = Vente.objects.filter(notes__contains=order_number)
            if ventes.exists():
                vente = ventes.first()
                print(f"✓ Vente trouvée par order_number: {vente.uid}")
        
        # 2. Si pas trouvé, chercher par référence interne dans notes
        if not vente and reference_interne:
            ventes = Vente.objects.filter(notes__contains=reference_interne)
            if ventes.exists():
                vente = ventes.first()
                print(f"✓ Vente trouvée par référence interne: {vente.uid}")
        
        # 3. Si toujours pas trouvé, chercher par référence de paiement
        if not vente and reference_interne:
            # La référence peut être dans reference_paiement
            ventes = Vente.objects.filter(reference_paiement__contains=reference_interne)
            if ventes.exists():
                vente = ventes.first()
                print(f"✓ Vente trouvée par reference_paiement: {vente.uid}")
        
        if not vente:
            logger.error(f"Vente non trouvée pour référence: {reference_interne} ou order: {order_number}")
            return JsonResponse({'error': 'Vente non trouvée'}, status=404)
        
        # Mettre à jour les notes avec les détails du callback
        notes_data = json.loads(vente.notes) if vente.notes else {}
        notes_data['callback_data'] = data
        notes_data['callback_received_at'] = timezone.now().isoformat()
        
        # Traiter selon le statut
        if status == '0' or status == 'SUCCESS' or str(status).upper() == 'SUCCESS':
            # Paiement validé - marquer les tickets comme VENDUS
            notes_data['statut_paiement'] = 'VALIDE'
            notes_data['date_validation'] = timezone.now().isoformat()
            vente.notes = json.dumps(notes_data)
            vente.save()
            
            # Récupérer les tickets réservés depuis les notes
            tickets_reserves_uids = notes_data.get('tickets_reserves', [])
            
            tickets_trouves = []
            if tickets_reserves_uids:
                # Marquer les tickets comme VENDUS et les lier à la vente
                with transaction.atomic():
                    from infrastructures.models import Ticket
                    tickets_reserve = Ticket.objects.filter(uid__in=tickets_reserves_uids, statut='EN_RESERVATION')
                    count_updated = tickets_reserve.update(statut='VENDU', vente=vente)
                    tickets_trouves = list(tickets_reserve)
                
                logger.info(f"Paiement validé pour vente: {vente.uid} - {count_updated} billets marqués VENDUS (via notes)")
            
            # SI aucun ticket trouvé via les notes, chercher tous les tickets EN_RESERVATION non associés
            if not tickets_trouves:
                logger.warning(f"Aucun ticket réservé trouvé dans notes pour vente: {vente.uid}, recherche globale...")
                
                # Récupérer les données d'achat depuis les notes
                purchase_data = notes_data.get('purchase_data', {})
                quantity = purchase_data.get('quantity', 1)
                
                with transaction.atomic():
                    from infrastructures.models import Ticket
                    # Chercher les tickets EN_RESERVATION les plus anciens non associés
                    tickets_disponibles = Ticket.objects.filter(
                        statut='EN_RESERVATION',
                        vente__isnull=True
                    ).order_by('date_creation')[:quantity]
                    
                    if tickets_disponibles.exists():
                        count_updated = tickets_disponibles.update(statut='VENDU', vente=vente)
                        tickets_trouves = list(tickets_disponibles)
                        logger.info(f"Paiement validé pour vente: {vente.uid} - {count_updated} billets trouvés globalement et marqués VENDUS")
                    else:
                        # En dernier recours, créer les billets depuis DISPONIBLE
                        logger.warning(f"Aucun ticket EN_RESERVATION trouvé, création depuis DISPONIBLE pour vente: {vente.uid}")
                        try:
                            if purchase_data:
                                from gouvernance.models import Rencontre
                                from infrastructures.models import EvenementZone
                                
                                rencontre = Rencontre.objects.get(uid=purchase_data['rencontre_uid'])
                                zone = EvenementZone.objects.get(uid=purchase_data['zone_tarif_uid'])
                                
                                # Créer les billets maintenant
                                tickets_disponibles = list(zone.tickets.filter(
                                    statut='DISPONIBLE'
                                )[:purchase_data['quantity']])
                                
                                tickets_list = []
                                for ticket in tickets_disponibles:
                                    ticket.statut = 'VENDU'
                                    ticket.vente = vente
                                    ticket.save()
                                    tickets_list.append(ticket)
                                
                                tickets_trouves = tickets_list
                                logger.info(f"Création de {len(tickets_list)} billets pour vente: {vente.uid}")
                        except Exception as e:
                            logger.error(f"Erreur lors de la création des billets: {str(e)}")
            
            # Envoyer les SMS avec les billets
            try:
                from .sms_service import sms_service
                from .email_service import email_service
                
                if tickets_trouves:
                    # Envoyer SMS
                    sms_result = sms_service.envoyer_sms_confirmation_paiement(
                        vente.acheteur_telephone, 
                        vente
                    )
                    print(f"SMS envoyé: {sms_result}")
                    
                    # Envoyer e-mail avec les billets si l'adresse e-mail est fournie
                    email_acheteur = notes_data.get('purchase_data', {}).get('email', '').strip()
                    if email_acheteur and '@' in email_acheteur:
                        print(f"Envoi des billets par e-mail à: {email_acheteur}")
                        email_result = email_service.envoyer_billet_email(
                            email_acheteur,
                            vente.acheteur_nom,
                            vente,
                            tickets_trouves
                        )
                        print(f"E-mail envoyé: {email_result}")
                        
                        # Mettre à jour les notes avec le statut d'envoi e-mail
                        notes_data['email_envoye'] = email_result.get('success', False)
                        notes_data['email_envoye_at'] = timezone.now().isoformat()
                        notes_data['email_destinataire'] = email_acheteur
                        vente.notes = json.dumps(notes_data)
                        vente.save()
                    else:
                        print(f"Pas d'adresse e-mail fournie pour: {vente.acheteur_nom}")
                        notes_data['email_non_fourni'] = True
                        vente.notes = json.dumps(notes_data)
                        vente.save()
                else:
                    logger.error(f"Aucun ticket trouvé pour l'envoi SMS/Email - vente: {vente.uid}")
            except Exception as e:
                print(f"Erreur SMS/Email: {str(e)}")
                import traceback
                traceback.print_exc()
                # Enregistrer l'erreur mais ne pas échouer le paiement
                try:
                    notes_data['erreur_email_sms'] = str(e)
                    vente.notes = json.dumps(notes_data)
                    vente.save()
                except:
                    pass
            
            return JsonResponse({'status': 'success', 'message': 'Paiement validé'})
            
        elif status == '1' or status == 'FAILED' or str(status).upper() == 'FAILED':
            # Paiement échoué - vérifier la raison
            message_erreur = data.get('message', data.get('error_message', 'Paiement échoué'))
            
            # Cas spécifique : solde insuffisant
            if 'solde' in message_erreur.lower() or 'insuffisant' in message_erreur.lower() or 'balance' in message_erreur.lower():
                notes_data['statut_paiement'] = 'SOLDE_INSUFFISANT'
                notes_data['raison_echec'] = 'Solde insuffisant'
                notes_data['message_erreur'] = message_erreur
                vente.notes = json.dumps(notes_data)
                vente.save()
                
                # REMBOURSER LES TICKETS : EN_RESERVATION → DISPONIBLE
                tickets_reserves_uids = notes_data.get('tickets_reserves', [])
                if tickets_reserves_uids:
                    with transaction.atomic():
                        from infrastructures.models import Ticket
                        tickets_reserve = Ticket.objects.filter(uid__in=tickets_reserves_uids, statut='EN_RESERVATION')
                        count_rembourse = tickets_reserve.update(statut='DISPONIBLE', vente=None)
                    
                    logger.warning(f"Solde insuffisant pour vente: {vente.uid} - {count_rembourse} tickets remboursés")
                
                return JsonResponse({
                    'status': 'failed', 
                    'message': 'Solde insuffisant',
                    'reason': 'solde_insuffisant',
                    'detail': message_erreur
                })
            else:
                # Autre raison d'échec - RETOUR AU STATUT INITIAL
                notes_data['statut_paiement'] = 'ECHOUE'
                notes_data['raison_echec'] = message_erreur
                notes_data['message_erreur'] = message_erreur
                vente.notes = json.dumps(notes_data)
                vente.save()
                
                # LIBÉRER LES TICKETS : EN_RESERVATION → DISPONIBLE (retour au statut initial)
                tickets_reserves_uids = notes_data.get('tickets_reserves', [])
                if tickets_reserves_uids:
                    with transaction.atomic():
                        from infrastructures.models import Ticket
                        tickets_reserve = Ticket.objects.filter(uid__in=tickets_reserves_uids, statut='EN_RESERVATION')
                        count_rembourse = tickets_reserve.update(statut='DISPONIBLE', vente=None)
                    
                    logger.warning(f"Paiement échoué pour vente: {vente.uid} - {count_rembourse} tickets retournés à DISPONIBLE")
                else:
                    # Si aucun ticket réservé trouvé dans les notes, chercher globalement
                    logger.warning(f"Aucun ticket réservé dans notes pour vente: {vente.uid}, recherche globale pour libération")
                    with transaction.atomic():
                        from infrastructures.models import Ticket
                        # Chercher tous les tickets EN_RESERVATION non associés à une vente
                        tickets_reserve_globaux = Ticket.objects.filter(
                            statut='EN_RESERVATION',
                            vente__isnull=True
                        )
                        
                        # Libérer tous les tickets EN_RESERVATION orphelins (sécurité)
                        count_rembourse = tickets_reserve_globaux.update(statut='DISPONIBLE')
                        logger.info(f"Libération globale de {count_rembourse} tickets EN_RESERVATION orphelins")
                
                return JsonResponse({
                    'status': 'failed', 
                    'message': 'Paiement échoué',
                    'reason': 'autre_erreur',
                    'detail': message_erreur
                })
        
        elif str(status).upper() in ['CANCELLED', 'CANCELED', 'CANCEL', '2', 'ANNULE', 'ANNULÉ']:
            # Paiement annulé par l'utilisateur
            message_erreur = data.get('message', data.get('error_message', 'Paiement annulé par l\'utilisateur'))
            
            notes_data['statut_paiement'] = 'ECHOUE'
            notes_data['raison_echec'] = 'Paiement annulé par l\'utilisateur'
            notes_data['message_erreur'] = message_erreur
            vente.notes = json.dumps(notes_data)
            vente.save()
            
            # LIBÉRER LES TICKETS : EN_RESERVATION → DISPONIBLE
            tickets_reserves_uids = notes_data.get('tickets_reserves', [])
            if tickets_reserves_uids:
                with transaction.atomic():
                    from infrastructures.models import Ticket
                    tickets_reserve = Ticket.objects.filter(uid__in=tickets_reserves_uids, statut='EN_RESERVATION')
                    count_rembourse = tickets_reserve.update(statut='DISPONIBLE', vente=None)
                
                logger.warning(f"Paiement annulé pour vente: {vente.uid} - {count_rembourse} tickets libérés")
            else:
                # Si aucun ticket réservé trouvé dans les notes, chercher globalement
                logger.warning(f"Aucun ticket réservé dans notes pour vente annulée: {vente.uid}, recherche globale")
                with transaction.atomic():
                    from infrastructures.models import Ticket
                    tickets_reserve_globaux = Ticket.objects.filter(
                        statut='EN_RESERVATION',
                        vente__isnull=True
                    )
                    count_rembourse = tickets_reserve_globaux.update(statut='DISPONIBLE')
                    logger.info(f"Libération globale de {count_rembourse} tickets EN_RESERVATION orphelins (annulation)")
            
            return JsonResponse({
                'status': 'cancelled', 
                'message': 'Paiement annulé',
                'reason': 'annulation_utilisateur',
                'detail': message_erreur
            })
        
        else:
            # Statut en attente ou inconnu
            logger.warning(f"Statut inconnu reçu: {status} pour vente: {vente.uid}")
            notes_data['statut_paiement'] = 'EN_ATTENTE'
            notes_data['statut_inconnu'] = str(status)
            vente.notes = json.dumps(notes_data)
            vente.save()
            
            logger.info(f"Paiement en attente pour vente: {vente.uid}")
            return JsonResponse({'status': 'pending', 'message': 'Paiement en attente'})
        
    except Exception as e:
        logger.error(f"Erreur callback: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Erreur serveur'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def verifier_statut_paiement(request, order_number):
    """
    Vérifie le statut d'un paiement via l'API FlexPay
    """
    try:
        from public.mobile_money_integration import MobileMoneyPaymentProcessor
        
        processor = MobileMoneyPaymentProcessor()
        statut = processor.verifier_paiement(order_number)
        
        return JsonResponse(statut)
        
    except Exception as e:
        logger.error(f"Erreur vérification statut: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Erreur serveur'}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def valider_paiement_simplifie(request, vente_uid):
    """
    Valide un paiement et crée les billets
    Utilisé pour les tests ou validation manuelle
    """
    try:
        vente = Vente.objects.get(uid=vente_uid)
        
        # Vérifier si les billets existent déjà
        if vente.tickets.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Billets déjà créés'
            })
        
        # Récupérer les données de la commande depuis notes
        notes_data = json.loads(vente.notes) if vente.notes else {}
        purchase_data = notes_data.get('purchase_data', {})
        quantity = purchase_data.get('quantity', 1)
        zone_uid = purchase_data.get('zone_tarif_uid')
        
        if not zone_uid:
            return JsonResponse({
                'status': 'error',
                'message': 'Informations de zone manquantes'
            })
        
        # Récupérer la zone
        zone = EvenementZone.objects.get(uid=zone_uid)
        
        # Créer les billets
        with transaction.atomic():
            tickets_disponibles = list(zone.tickets.filter(
                statut='DISPONIBLE'
            ).select_for_update()[:quantity])
            
            if len(tickets_disponibles) < quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Places insuffisantes'
                })
            
            tickets_list = []
            for ticket in tickets_disponibles:
                ticket.statut = 'RESERVE'  # RESERVE au lieu de VENDU
                ticket.vente = vente
                ticket.save()
                tickets_list.append(ticket)
            
            # Mettre à jour le statut dans notes
            notes_data['statut_paiement'] = 'VALIDE'
            notes_data['date_validation'] = timezone.now().isoformat()
            vente.notes = json.dumps(notes_data)
            vente.save()
        
        logger.info(f"{len(tickets_list)} billets créés pour vente: {vente.uid}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'{len(tickets_list)} billets créés et vendus',
            'tickets': [{'uid': str(t.uid)} for t in tickets_list]
        })
        
    except Vente.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Vente non trouvée'
        }, status=404)
    except EvenementZone.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Zone non trouvée'
        }, status=404)
    except Exception as e:
        logger.error(f"Erreur validation: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

