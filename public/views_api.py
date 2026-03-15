# -*- coding: utf-8 -*-
"""
Vues API pour la billetterie Mobile Money SI-SEP Sport RDC
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from infrastructures.models import Vente, Ticket
from .mobile_money_integration import MobileMoneyPaymentProcessor, MobileMoneyCallbackHandler
from .models import VerificationQR, TransactionMobileMoney


class InitierPaiementView(APIView):
    """
    POST /api/billetterie/initier-paiement/
    Initialise une transaction Mobile Money pour une vente
    """
    
    def post(self, request):
        try:
            vente_uid = request.data.get('vente_uid')
            methode = request.data.get('methode')  # MPESA, ORANGE_MONEY, AIRTEL_MONEY
            telephone_payeur = request.data.get('telephone_payeur')
            
            if not all([vente_uid, methode, telephone_payeur]):
                return Response({
                    'success': False,
                    'error': 'Paramètres manquants',
                    'message': 'vente_uid, methode et telephone_payeur sont requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer la vente
            vente = get_object_or_404(Vente, uid=vente_uid)
            
            # Vérifier que la vente n'a pas déjà été payée
            if hasattr(vente, 'statut_paiement') and vente.statut_paiement == 'VALIDE':
                return Response({
                    'success': False,
                    'error': 'Vente déjà payée',
                    'message': 'Cette vente a déjà été validée'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialiser le paiement
            processor = MobileMoneyPaymentProcessor()
            resultat = processor.initier_paiement(vente, methode, telephone_payeur)
            
            if resultat['success']:
                # Créer l'historique de transaction
                TransactionMobileMoney.objects.create(
                    vente=vente,
                    operateur=methode,
                    reference_operateur=resultat.get('order_number', ''),
                    montant=vente.montant_total,
                    devise='CDF',
                    statut='INITIE'
                )
                
                return Response(resultat, status=status.HTTP_202_ACCEPTED)
            else:
                return Response(resultat, status=status.HTTP_400_BAD_REQUEST)
                
        except Vente.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Vente non trouvée',
                'message': 'La vente spécifiée n\'existe pas'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de l\'initialisation du paiement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifierPaiementView(APIView):
    """
    GET /api/billetterie/verifier-paiement/<order_number>/
    Vérifie le statut d'un paiement Mobile Money
    """
    
    def get(self, request, order_number):
        try:
            # Récupérer la vente
            vente = get_object_or_404(Vente, order_number=order_number)
            
            # Vérifier le paiement
            processor = MobileMoneyPaymentProcessor()
            resultat = processor.verifier_paiement(order_number)
            
            if resultat['success']:
                return Response({
                    'success': True,
                    'statut': resultat['status'],
                    'vente_uid': str(vente.uid),
                    'montant': str(vente.montant_total),
                    'date_validation': vente.date_validation.isoformat() if vente.date_validation else None
                })
            else:
                return Response(resultat, status=status.HTTP_404_NOT_FOUND)
                
        except Vente.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Vente non trouvée',
                'message': 'Aucune vente trouvée pour ce numéro de commande'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la vérification du paiement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class MobileMoneyCallbackView(APIView):
    """
    POST /api/billetterie/callback/mmo/
    Webhook pour les callbacks Mobile Money de FlexPay
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body) if request.body else {}
            
            # Traiter le callback
            handler = MobileMoneyCallbackHandler()
            resultat = handler.handle_callback(data)
            
            return Response(resultat, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'error': 'JSON invalide',
                'message': 'Le corps de la requête n\'est pas un JSON valide'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors du traitement du callback'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifierQRView(APIView):
    """
    GET /api/billetterie/verifier-qr/<hash_verification>/
    Vérifie l'authenticité d'un billet via son QR code
    """
    
    def get(self, request, hash_verification):
        try:
            verification = get_object_or_404(VerificationQR, hash_verification=hash_verification)
            ticket = verification.ticket
            
            # Retourner les informations du ticket
            return Response({
                'valid': True,
                'message': 'Billet authentique',
                'ticket': {
                    'uid': str(ticket.uid),
                    'evenement': ticket.evenement_zone.evenement.titre,
                    'date_evenement': ticket.evenement_zone.evenement.date_evenement.isoformat(),
                    'zone': ticket.evenement_zone.zone_stade.nom,
                    'prix': str(ticket.evenement_zone.prix_unitaire),
                    'statut': ticket.statut,
                    'date_utilisation': ticket.date_utilisation.isoformat() if ticket.date_utilisation else None,
                    'date_achat': ticket.vente.date_vente.isoformat() if ticket.vente else None
                },
                'verification': {
                    'date_generation': verification.date_generation.isoformat(),
                    'url_verification': verification.url_verification
                }
            })
            
        except VerificationQR.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'Billet invalide ou inconnu',
                'error': 'Ce QR code n\'existe pas dans notre système'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'valid': False,
                'error': str(e),
                'message': 'Erreur lors de la vérification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TicketQRView(APIView):
    """
    GET /api/billetterie/ticket/<ticket_uid>/qr/
    Retourne l'image QR code d'un ticket spécifique
    """
    
    def get(self, request, ticket_uid):
        try:
            ticket = get_object_or_404(Ticket, uid=ticket_uid)
            
            # Vérifier si le QR code existe
            if not hasattr(ticket, 'qr_code') or not ticket.qr_code:
                return Response({
                    'error': 'QR code non disponible',
                    'message': 'Le QR code n\'a pas encore été généré pour ce billet'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Retourner l'image
            with open(ticket.qr_code.path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='image/png')
                response['Content-Disposition'] = f'inline; filename="qr_ticket_{ticket_uid}.png"'
                return response
                
        except Ticket.DoesNotExist:
            return Response({
                'error': 'Billet non trouvé',
                'message': 'Le billet spécifié n\'existe pas'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Erreur lors de la récupération du QR code'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatistiquesBilletterieView(APIView):
    """
    GET /api/billetterie/statistiques/
    Statistiques de la billetterie
    """
    
    def get(self, request):
        try:
            # Statistiques générales
            total_ventes = Vente.objects.count()
            total_recettes = Vente.objects.aggregate(
                total=models.Sum('montant_total')
            )['total'] or 0
            
            # Statistiques par statut de paiement
            stats_paiement = {}
            for statut, label in [('VALIDE', 'Validés'), ('EN_ATTENTE', 'En attente'), ('ECHOUE', 'Échoués')]:
                count = Vente.objects.filter(statut_paiement=statut).count()
                stats_paiement[statut] = {'count': count, 'label': label}
            
            # Statistiques par opérateur
            stats_operateurs = {}
            for operateur, label in [('MPESA', 'M-Pesa'), ('ORANGE_MONEY', 'Orange Money'), ('AIRTEL_MONEY', 'Airtel Money')]:
                count = Vente.objects.filter(methode_paiement=operateur).count()
                stats_operateurs[operateur] = {'count': count, 'label': label}
            
            # Tickets vendus
            tickets_vendus = Ticket.objects.filter(statut='VENDU').count()
            tickets_utilises = Ticket.objects.filter(statut='UTILISE').count()
            
            return Response({
                'total_ventes': total_ventes,
                'total_recettes': str(total_recettes),
                'stats_paiement': stats_paiement,
                'stats_operateurs': stats_operateurs,
                'tickets': {
                    'vendus': tickets_vendus,
                    'utilises': tickets_utilises,
                    'disponibles': Ticket.objects.filter(statut='DISPONIBLE').count()
                }
            })
            
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Erreur lors de la récupération des statistiques'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
