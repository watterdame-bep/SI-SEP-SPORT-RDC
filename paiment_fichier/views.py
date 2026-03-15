from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from .permissions import IsStaffOrReadOnly
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
import time
import requests
import hashlib
import json
import threading
from decimal import Decimal
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import qrcode
import os

from .models import Paiement, ReleveGenere
from shared.translation_service import TranslationService

def check_flexpay_payment(order_number):
    """
    Vérifie le statut d'un paiement FlexPay via l'API de vérification.
    Format: GET https://apicheck.flexpaie.com/api/rest/v1/check/{orderNumber}
    Réponse succès: {"code": "0", "message": "Une transaction trouvée", "transaction": {...}}
    Réponse échec: {"code": "1", "message": "Aucune transaction trouvée", "transaction": null}
    """
    print(f"DEBUG VERIFICATION: Début vérification pour orderNumber: {order_number}")
    url = f"{settings.FLEXPAY_CHECK_URL}{order_number}"
    print(f"DEBUG VERIFICATION: URL complète: {url}")
    headers = {
        "Authorization": f"Bearer {settings.FLEXPAY_BEARER_TOKEN}",
    }
    print("DEBUG VERIFICATION: Headers préparés (Bearer token présent)")

    try:
        print("DEBUG VERIFICATION: Envoi requête GET vers FlexPay...")
        response = requests.get(url, headers=headers)
        print(f"DEBUG VERIFICATION: Réponse reçue - Status Code: {response.status_code}")
        try:
            print(f"DEBUG VERIFICATION: Réponse brute: {response.text}")
        except Exception as raw_err:
            print(f"DEBUG VERIFICATION: Impossible de lire le corps de réponse: {raw_err}")

        response.raise_for_status()
        data = response.json()
        print(f"DEBUG VERIFICATION: Données JSON parsées: {data}")

        if data.get('code') == '0' and data.get('transaction'):
            transaction = data.get('transaction')
            print(f"DEBUG VERIFICATION: Transaction trouvée - Status: {transaction.get('status')}, Amount: {transaction.get('amount')}")
        elif data.get('code') == '1':
            print("DEBUG VERIFICATION: Aucune transaction trouvée (code=1)")

        return data
    except requests.exceptions.RequestException as e:
        print(f"DEBUG VERIFICATION: Erreur HTTP lors de la vérification: {e}")
        raise
    except Exception as e:
        print(f"DEBUG VERIFICATION: Erreur inattendue: {e}")
        raise


def verify_payment_with_retry(paiement, max_attempts=120, retry_interval=5):
    """
    Vérifie le paiement avec retry pendant ~10 minutes (120 tentatives x 5 secondes).
    
    Args:
        paiement: Instance du modèle Paiement
        max_attempts: Nombre maximum de tentatives (défaut: 120 = 10 minutes)
        retry_interval: Intervalle entre les tentatives en secondes (défaut: 5)
    
    Returns:
        Tuple: (verification_status, is_validated) où:
        - verification_status: 'validated', 'pending', ou 'failed'
        - is_validated: Boolean indiquant si le paiement est confirmé
    """
    print(f"DEBUG PAIEMENT: Démarrage vérification avec retry - Max {max_attempts} tentatives x {retry_interval}s")
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"DEBUG PAIEMENT: Tentative {attempt}/{max_attempts} de vérification")
            verification_data = check_flexpay_payment(paiement.order_number)
            
            if verification_data.get('code') == '0':
                transaction = verification_data.get('transaction')
                if transaction:
                    transaction_status = transaction.get('status')
                    print(f"DEBUG PAIEMENT: Transaction trouvée - Status: {transaction_status}")
                    
                    if transaction_status == '0':
                        # Paiement validé!
                        print(f"DEBUG PAIEMENT: ✅ Paiement VALIDÉ à la tentative {attempt}")
                        paiement.statut = Paiement.StatutPaiement.VALIDATE
                        paiement.date_validation = timezone.now()
                        paiement.save()
                        
                        # Mise à jour de la facture via recalcul (évite le double comptage)
                        # Le signal update_facture_status_on_payment s'exécute déjà et recalcule
                        # Pas besoin de le faire ici manuellement
                        print(f"DEBUG PAIEMENT: Facture sera mise à jour par le signal post_save")
                        
                        return ("validated", True)
                    
                    elif transaction_status == '1':
                        # Paiement échoué, inutile de continuer
                        print(f"DEBUG PAIEMENT: ❌ Paiement ÉCHOUÉ à la tentative {attempt}")
                        paiement.statut = Paiement.StatutPaiement.ECHOUE
                        paiement.save()
                        return ("failed", False)
                    
                    elif transaction_status == '2':
                        # Paiement en attente, continue les tentatives
                        if attempt < max_attempts:
                            print(f"DEBUG PAIEMENT: ⏳ Paiement en attente - Nouvelle tentative dans {retry_interval}s...")
                            time.sleep(retry_interval)
                        else:
                            print(f"DEBUG PAIEMENT: ⏳ Paiement en attente après {max_attempts} tentatives - Timeout")
            else:
                print(f"DEBUG PAIEMENT: Réponse FlexPay avec code != 0: {verification_data.get('code')}")
                if attempt < max_attempts:
                    print(f"DEBUG PAIEMENT: Nouvelle tentative dans {retry_interval}s...")
                    time.sleep(retry_interval)
        
        except Exception as e:
            print(f"DEBUG PAIEMENT: Erreur à la tentative {attempt}: {e}")
            if attempt < max_attempts:
                print(f"DEBUG PAIEMENT: Nouvelle tentative dans {retry_interval}s...")
                time.sleep(retry_interval)
            else:
                print(f"DEBUG PAIEMENT: Erreur après {max_attempts} tentatives - Arrêt")
    
    # Si on arrive ici, toutes les tentatives sont épuisées
    print(f"DEBUG PAIEMENT: Dépassement du délai de vérification (10 minutes) - Paiement reste en attente")
    return ("pending", False)
from .serializers import PaiementSerializer, InitierPaiementSerializer, RelevePaiementSerializer
from facturation.models import Facture


class VerifierPaiementView(APIView):
    """
    GET /api/paiements/verifier/<paiement_id>/
    Vérifie le statut d'un paiement indépendamment de l'initialisation.
    Retourne le statut actuel du paiement auprès de FlexPay.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, paiement_id, *args, **kwargs):
        print(f"DEBUG PAIEMENT: Vérification indépendante pour paiement ID: {paiement_id}")
        
        try:
            paiement = Paiement.objects.get(id=paiement_id, abonne=request.user.abonne)
            print(f"DEBUG PAIEMENT: Paiement trouvé - Statut: {paiement.statut}, Order number: {paiement.order_number}")
        except Paiement.DoesNotExist:
            print(f"DEBUG PAIEMENT: Paiement non trouvé: {paiement_id}")
            lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
            return Response(
                {"error": TranslationService.translate('error.payment_not_found', lang)},
                status=status.HTTP_404_NOT_FOUND
            )

        # Si le paiement est déjà validé ou échoué, retourner le statut directement
        if paiement.statut in [Paiement.StatutPaiement.VALIDATE, Paiement.StatutPaiement.ECHOUE]:
            lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
            status_message = TranslationService.translate('payment.validated', lang) if paiement.statut == Paiement.StatutPaiement.VALIDATE else TranslationService.translate('payment.failed_or_cancelled', lang)
            return Response({
                "paiement_id": paiement.id,
                "statut": paiement.statut,
                "message": status_message,
                "montant": str(paiement.montant),
                "date_transaction": paiement.date_transaction,
                "date_validation": paiement.date_validation
            })

        # Vérifier si le paiement a un order_number
        if not paiement.order_number:
            print(f"DEBUG PAIEMENT: Pas de order_number pour paiement {paiement_id}")
            lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
            return Response(
                {"error": TranslationService.translate('error.no_order_number', lang)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier auprès de FlexPay
        print(f"DEBUG PAIEMENT: Vérification FlexPay pour order_number: {paiement.order_number}")
        try:
            data = check_flexpay_payment(paiement.order_number)
            print(f"DEBUG PAIEMENT: Réponse FlexPay: {data}")
        except requests.exceptions.RequestException as e:
            print(f"DEBUG PAIEMENT: Erreur FlexPay: {e}")
            lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
            return Response(
                {"error": TranslationService.translate('payment.check_failed', lang)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Analyser la réponse
        if data.get('code') == '0':
            transaction = data.get('transaction')
            if transaction:
                transaction_status = transaction.get('status')
                print(f"DEBUG PAIEMENT: Statut transaction: {transaction_status}")

                if transaction_status == '0':
                    # Paiement validé
                    print("DEBUG PAIEMENT: Paiement validé par FlexPay")
                    paiement.statut = Paiement.StatutPaiement.VALIDATE
                    paiement.date_validation = timezone.now()
                    paiement.save()

                    # Mise à jour de la facture via recalcul (évite le double comptage)
                    # Le signal update_facture_status_on_payment s'exécute déjà et recalcule
                    # Pas besoin de le faire ici manuellement
                    facture = paiement.facture
                    if facture:
                        print(f"DEBUG PAIEMENT: Facture {facture.id} sera mise à jour par le signal post_save")

                    # Envoyer notification de validation
                    from notifications.services import create_targeted_notification
                    try:
                        create_targeted_notification(
                            titre="Paiement validé ✅",
                            message=f"Votre paiement de {paiement.montant} CDF pour la facture #{facture.id} a été validé avec succès.",
                            abonnes=[paiement.abonne],
                            priorite='NORMALE',
                            extra_data={
                                'type': 'paiement_valide',
                                'paiement_id': str(paiement.id),
                                'facture_id': str(facture.id),
                                'montant': str(paiement.montant)
                            }
                        )
                        print(f"DEBUG PAIEMENT: Notification de validation envoyée pour paiement {paiement.id}")
                    except Exception as e:
                        print(f"DEBUG PAIEMENT: Erreur lors de l'envoi de la notification: {e}")

                    lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
                    return Response({
                        "paiement_id": paiement.id,
                        "statut": paiement.statut,
                        "message": TranslationService.translate('payment.validated', lang),
                        "montant": str(paiement.montant),
                        "date_validation": paiement.date_validation
                    })

                elif transaction_status == '1':
                    # Paiement échoué
                    print("DEBUG PAIEMENT: Paiement échoué par FlexPay")
                    paiement.statut = Paiement.StatutPaiement.ECHOUE
                    paiement.save()

                    lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
                    return Response({
                        "paiement_id": paiement.id,
                        "statut": paiement.statut,
                        "message": TranslationService.translate('payment.failed_or_cancelled', lang)
                    })

                elif transaction_status == '2':
                    # Paiement en attente
                    print("DEBUG PAIEMENT: Paiement en attente")
                    lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
                    return Response({
                        "paiement_id": paiement.id,
                        "statut": paiement.statut,
                        "message": TranslationService.translate('payment.pending', lang)
                    })

        # Statut inconnu
        lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
        return Response({
            "paiement_id": paiement.id,
            "statut": paiement.statut,
            "message": TranslationService.translate('payment.check_failed', lang)
        }, status=status.HTTP_400_BAD_REQUEST)


class InitierPaiementView(generics.CreateAPIView):
    """
    POST /api/paiements/initier/
    Démarre la transaction Mobile Money (MMO - STK Push).
    
    Flux asynchrone:
    1. Initie le paiement auprès de FlexPay
    2. Retourne immédiatement (HTTP 202) à l'utilisateur
    3. Lance une tâche Celery en arrière-plan pour vérifier le paiement pendant 90 secondes
    4. Le paiement est mis à jour automatiquement quand validé ou via le callback webhook
    """
    serializer_class = InitierPaiementSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        print("DEBUG PAIEMENT: Début de l'initiation du paiement")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        facture = serializer.validated_data['facture']
        montant = serializer.validated_data['montant']
        methode = serializer.validated_data['methode']
        telephone_payeur = serializer.validated_data['telephone_payeur']
        abonne = request.user.abonne

        print(f"DEBUG PAIEMENT: Facture ID: {facture.id}, Montant: {montant}, Méthode: {methode}, Téléphone: {telephone_payeur}, Abonné: {abonne.id}")

        reference_interne = f"SNEL-{facture.id}-{int(time.time())}-{abonne.id}"
        print(f"DEBUG PAIEMENT: Référence interne générée: {reference_interne}")

        paiement = Paiement.objects.create(
            abonne=abonne,
            facture=facture,
            montant=montant,
            methode=methode,
            telephone_payeur=telephone_payeur,
            reference_interne=reference_interne,
            statut=Paiement.StatutPaiement.INITIE
        )
        print(f"DEBUG PAIEMENT: Paiement créé avec ID: {paiement.id}, Statut: {paiement.statut}")

        try:
            print("DEBUG PAIEMENT: Préparation de l'appel à l'API FlexPay")
            payload = {
                "merchant": "JCONSULTMY",
                "reference": paiement.reference_interne,
                "amount": "150",  # TEST: montant en dur pour validation FlexPay str(int(paiement.montant))
                "currency": "CDF",
                "phone": paiement.telephone_payeur,
                "description": f"Paiement facture #{paiement.facture.id}",
                "callbackUrl": f"{settings.SITE_URL}/api/paiements/callback/mmo/",
                "approve_url": f"{settings.SITE_URL}/api/paiements/callback/mmo/",
                "cancel_url": f"{settings.SITE_URL}/api/paiements/callback/mmo/",
                "decline_url": f"{settings.SITE_URL}/api/paiements/callback/mmo/",
                "type": 1
            }
            print(f"DEBUG PAIEMENT: Payload FlexPay: {payload}")
            headers = {
                "Authorization": f"Bearer {settings.FLEXPAY_BEARER_TOKEN}",
                "Content-Type": "application/json"
            }
            print(f"DEBUG PAIEMENT: Headers FlexPay: Authorization Bearer token present, URL: {settings.FLEXPAY_API_URL}")
            response = requests.post(settings.FLEXPAY_API_URL, json=payload, headers=headers)
            print(f"DEBUG PAIEMENT: Réponse FlexPay - Status: {response.status_code}")

            # Afficher le contenu de la réponse même en cas d'erreur
            try:
                response_text = response.text
                print(f"DEBUG PAIEMENT: Réponse FlexPay - Contenu: {response_text}")
            except Exception as e:
                print(f"DEBUG PAIEMENT: Impossible de lire la réponse: {e}")
            
            response.raise_for_status()  # Raise exception if not 2xx

            # Vérifier la réponse de FlexPay
            response_data = response.json()
            print(f"DEBUG PAIEMENT: Données de réponse FlexPay: {response_data}")
            if response_data.get('code') != '0':
                print(f"DEBUG PAIEMENT: Erreur FlexPay - Code: {response_data.get('code')}")
                raise Exception(f"FlexPay API returned error: {response_data}")

            order_number = response_data.get('orderNumber')
            if not order_number:
                print(f"DEBUG PAIEMENT: Erreur - Pas d'orderNumber dans la réponse")
                raise Exception(f"FlexPay API did not return orderNumber: {response_data}")
            
            print(f"DEBUG PAIEMENT: orderNumber reçu de FlexPay: {order_number}")

            paiement.order_number = order_number
            paiement.save()
            print(f"DEBUG PAIEMENT: Order number assigné: {paiement.order_number}")

            # Lancer la vérification en arrière-plan (SANS bloquer la requête HTTP)
            # Utiliser un thread pour ne pas dépendre de Celery
            import threading
            def _verify_payment_background(paiement_id):
                try:
                    paiement_obj = Paiement.objects.get(id=paiement_id)
                    print(f"DEBUG PAIEMENT: Vérification en thread lancée pour paiement {paiement_id}")
                    verification_status, is_validated = verify_payment_with_retry(paiement_obj, max_attempts=120, retry_interval=5)
                    print(f"DEBUG PAIEMENT: Vérification terminée - Status: {verification_status}, Validé: {is_validated}")
                except Exception as e:
                    print(f"DEBUG PAIEMENT: Erreur dans vérification en thread: {e}")
            
            verification_thread = threading.Thread(
                target=_verify_payment_background, 
                args=(paiement.id,), 
                daemon=True
            )
            verification_thread.start()
            print(f"DEBUG PAIEMENT: Vérification lancée en thread pour paiement ID: {paiement.id}")

            print(f"DEBUG PAIEMENT: Initiation terminée pour paiement ID: {paiement.id}")
            lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
            return Response(
                {
                    "message": TranslationService.translate('payment.initiated', lang),
                    "paiement_id": paiement.id,
                    "reference_interne": reference_interne,
                    "verification_status": "pending",
                },
                status=status.HTTP_202_ACCEPTED
            )
        except requests.exceptions.RequestException as e:
            print(f"DEBUG PAIEMENT: Erreur lors de l'appel FlexPay: {e}")
            paiement.statut = Paiement.StatutPaiement.ECHOUE
            paiement.detail_reconciliation = {"error_message": str(e)}
            paiement.save()
            print(f"DEBUG PAIEMENT: Paiement marqué comme échoué: {paiement.id}")
            return Response(
                {"error": f"Impossible d'initier la transaction avec l'opérateur Mobile Money: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CheckPaiementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print("DEBUG PAIEMENT: Début de la vérification manuelle du paiement")
        paiement_id = request.data.get('paiement_id')
        print(f"DEBUG PAIEMENT: Paiement ID demandé: {paiement_id}")
        if not paiement_id:
            print("DEBUG PAIEMENT: Erreur - paiement_id manquant")
            lang = getattr(request, 'language', None) or 'fr'
            return Response({"error": TranslationService.translate('error.paiement_id_required', lang)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            paiement = Paiement.objects.get(id=paiement_id, abonne=request.user.abonne)
            print(f"DEBUG PAIEMENT: Paiement trouvé: {paiement.id}, Statut actuel: {paiement.statut}")
        except Paiement.DoesNotExist:
            print(f"DEBUG PAIEMENT: Paiement non trouvé: {paiement_id}")
            lang = getattr(request, 'language', None) or 'fr'
            return Response({"error": TranslationService.translate('error.payment_not_found', lang)}, status=status.HTTP_404_NOT_FOUND)

        if not paiement.order_number:
            print(f"DEBUG PAIEMENT: Pas de order_number pour le paiement: {paiement.id}")
            lang = getattr(request, 'language', None) or 'fr'
            return Response({"error": TranslationService.translate('error.no_order_number', lang)}, status=status.HTTP_400_BAD_REQUEST)

        print(f"DEBUG PAIEMENT: Vérification auprès de FlexPay pour order_number: {paiement.order_number}")
        try:
            data = check_flexpay_payment(paiement.order_number)
            print(f"DEBUG PAIEMENT: Réponse FlexPay: {data}")
        except requests.exceptions.RequestException as e:
            print(f"DEBUG PAIEMENT: Erreur lors de la vérification FlexPay: {e}")
            lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
            return Response({"error": TranslationService.translate('payment.check_failed', lang)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if data.get('code') == '0':
            transaction = data.get('transaction')
            print(f"DEBUG PAIEMENT: Transaction data: {transaction}")
            transaction_status = transaction.get('status') if transaction else None
            
            if transaction and transaction_status == '0':
                print("DEBUG PAIEMENT: Paiement validé par FlexPay (status=0)")
                # Payment successful
                paiement.statut = Paiement.StatutPaiement.VALIDATE
                paiement.date_validation = timezone.now()
                paiement.save()
                print(f"DEBUG PAIEMENT: Paiement marqué comme VALIDATE: {paiement.id}")

                # Update facture via recalcul (évite le double comptage)
                # Le signal update_facture_status_on_payment s'exécute déjà et recalcule
                # Pas besoin de le faire ici manuellement
                facture = paiement.facture
                if facture:
                    print(f"DEBUG PAIEMENT: Facture {facture.id} sera mise à jour par le signal post_save")

                lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
                return Response({"message": TranslationService.translate('payment.validated', lang), "status": "success"})
            elif transaction and transaction_status == '1':
                print("DEBUG PAIEMENT: Paiement échoué par FlexPay (status=1)")
                paiement.statut = Paiement.StatutPaiement.ECHOUE
                paiement.save()
                lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
                return Response({"message": TranslationService.translate('payment.failed_or_cancelled', lang), "status": "failed"})
            elif transaction and transaction_status == '2':
                print("DEBUG PAIEMENT: Paiement en attente par FlexPay (status=2)")
                lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
                return Response({"message": TranslationService.translate('payment.pending', lang), "status": "pending"})
            else:
                print(f"DEBUG PAIEMENT: Statut transaction inconnu: {transaction_status}")
                lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
                return Response({"message": TranslationService.translate('payment.check_failed', lang), "status": "unknown"})
        else:
            print(f"DEBUG PAIEMENT: Vérification échouée - Code: {data.get('code')}")
            lang = getattr(request, 'language', None) or TranslationService.get_language(request.user)
            return Response({"message": TranslationService.translate('payment.check_failed', lang), "status": "failed"})

class MobileMoneyCallbackView(APIView):
    """
    POST /api/paiements/callback/mmo/
    Endpoint Webhook appelé par l'opérateur Mobile Money pour confirmer/infirmer une transaction.
    """
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        print("DEBUG PAIEMENT: Callback MMO reçu")
        data = request.data
        print(f"DEBUG PAIEMENT: Données du callback: {data}")

        # NOTE: La structure exacte de `data` dépend de l'opérateur Mobile Money.
        # Vous devrez adapter ces lignes en fonction de l'API réelle.

        # Exemples de clés attendues :
        reference_interne = data.get('snel_reference', data.get('merchant_ref'))
        operateur_status = data.get('status', data.get('transaction_status'))
        reference_operateur = data.get('transaction_id', data.get('provider_id'))
        montant_paye_par_mmo = data.get('amount') # Vérifier que le montant correspond

        print(f"DEBUG PAIEMENT: Référence interne extraite: {reference_interne}")
        print(f"DEBUG PAIEMENT: Statut opérateur: {operateur_status}")
        print(f"DEBUG PAIEMENT: Référence opérateur: {reference_operateur}")
        print(f"DEBUG PAIEMENT: Montant MMO: {montant_paye_par_mmo}")

        if not reference_interne:
            print("DEBUG PAIEMENT: Erreur - Référence interne manquante")
            lang = getattr(request, 'language', None) or 'fr'
            return Response({"error": TranslationService.translate('error.missing_internal_reference', lang)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            paiement = Paiement.objects.get(reference_interne=reference_interne)
            print(f"DEBUG PAIEMENT: Paiement trouvé: {paiement.id}, Statut actuel: {paiement.statut}, Montant attendu: {paiement.montant}")
        except Paiement.DoesNotExist:
            print(f"DEBUG PAIEMENT: Paiement non trouvé pour référence: {reference_interne}")
            lang = getattr(request, 'language', None) or 'fr'
            return Response({"error": TranslationService.translate('error.payment_reference_not_found', lang)}, status=status.HTTP_404_NOT_FOUND)

        paiement.detail_reconciliation = data
        paiement.reference_operateur = reference_operateur
        paiement.date_validation = timezone.now()
        print(f"DEBUG PAIEMENT: Détails de réconciliation sauvegardés pour paiement: {paiement.id}")

        # Vérification du statut de l'opérateur
        # Il est CRUCIAL de vérifier le montant payé vs le montant attendu
        print(f"DEBUG PAIEMENT: Vérification - Statut: {operateur_status}, Montant MMO: {montant_paye_par_mmo}, Montant attendu: {paiement.montant}")
        if operateur_status == 'SUCCESS' and (montant_paye_par_mmo is None or float(montant_paye_par_mmo) >= float(paiement.montant)):
            print("DEBUG PAIEMENT: Conditions de validation remplies")
            paiement.statut = Paiement.StatutPaiement.VALIDATE
            paiement.save()
            print(f"DEBUG PAIEMENT: Paiement validé: {paiement.id}")
            
            # Mise à jour de la facture via recalcul (évite le double comptage)
            # Le signal update_facture_status_on_payment s'exécute déjà et recalcule
            # Pas besoin de le faire ici manuellement
            facture = paiement.facture
            print(f"DEBUG PAIEMENT: Facture {facture.id} sera mise à jour par le signal post_save")

            # Envoyer notification de validation
            from notifications.services import create_targeted_notification
            try:
                create_targeted_notification(
                    titre="Paiement validé ✅",
                    message=f"Votre paiement de {paiement.montant} CDF pour la facture #{facture.id} a été validé avec succès.",
                    abonnes=[paiement.abonne],
                    priorite='NORMALE',
                    extra_data={
                        'type': 'paiement_valide',
                        'paiement_id': str(paiement.id),
                        'facture_id': str(facture.id),
                        'montant': str(paiement.montant)
                    }
                )
                print(f"DEBUG PAIEMENT: Notification de validation envoyée (callback) pour paiement {paiement.id}")
            except Exception as e:
                print(f"DEBUG PAIEMENT: Erreur lors de l'envoi de la notification (callback): {e}")

            lang = getattr(request, 'language', None) or 'fr'
            return Response({"message": TranslationService.translate('payment.processed_success', lang)}, status=status.HTTP_200_OK)
        else:
            print("DEBUG PAIEMENT: Conditions de validation non remplies - marquage comme échoué")
            paiement.statut = Paiement.StatutPaiement.ECHOUE
            paiement.save()
            print(f"DEBUG PAIEMENT: Paiement marqué comme échoué: {paiement.id}")
            lang = getattr(request, 'language', None) or 'fr'
            return Response({"message": TranslationService.translate('payment.failed_or_cancelled', lang)}, status=status.HTTP_200_OK)

class PaiementViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour l'historique des paiements de l'utilisateur connecté."""
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Paiement.objects.filter(abonne__user=self.request.user).order_by('-date_transaction')

class RelevePaiementView(APIView):
    """
    GET /api/paiements/releve/
    Génère un relevé de paiement PDF pour une période donnée avec code QR de vérification.
    Paramètres query: date_debut (requis), date_fin (optionnel)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = RelevePaiementSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        date_debut = serializer.validated_data['date_debut']
        date_fin = serializer.validated_data['date_fin']
        abonne = request.user.abonne

        # Récupérer les paiements de la période
        paiements = Paiement.objects.filter(
            abonne=abonne,
            date_transaction__date__gte=date_debut,
            date_transaction__date__lte=date_fin
        ).select_related('facture').order_by('date_transaction')

        # Générer le PDF même s'il n'y a pas de paiements (tableau vide)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []

        # Ajouter le logo SNEL
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo_black.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 10))

        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Centré
            textColor=colors.HexColor('#1a5276'),
        )
        story.append(Paragraph("RELEVÉ DE PAIEMENTS", title_style))
        story.append(Spacer(1, 5))
        
        # Sous-titre avec la période
        subtitle_style = ParagraphStyle(
            'SubTitle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=1,
            textColor=colors.grey,
        )
        story.append(Paragraph(f"Période du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}", subtitle_style))
        story.append(Spacer(1, 20))

        # Informations de l'abonné dans un cadre
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
        )
        
        # Tableau d'informations de l'abonné
        info_data = [
            [Paragraph("<b>Abonné:</b>", info_style), Paragraph(abonne.nom_complet, info_style)],
            [Paragraph("<b>N° Abonné:</b>", info_style), Paragraph(abonne.numero_abonne or 'N/A', info_style)],
            [Paragraph("<b>Date d'émission:</b>", info_style), Paragraph(timezone.now().strftime('%d/%m/%Y à %H:%M'), info_style)],
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#dee2e6')),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))

        # Préparer les données du tableau
        data = [['Date', 'Montant', 'Méthode', 'Statut', 'Facture']]
        total = 0

        if paiements.exists():
            for paiement in paiements:
                data.append([
                    paiement.date_transaction.strftime('%Y-%m-%d %H:%M'),
                    f"{paiement.montant:,.0f} CDF",
                    paiement.get_methode_display(),
                    paiement.get_statut_display(),
                    f"#{paiement.facture.id}"
                ])
                if paiement.statut == Paiement.StatutPaiement.VALIDATE:
                    total += float(paiement.montant)
        else:
            # Ajouter une ligne indiquant qu'il n'y a pas de paiements
            no_payment_style = ParagraphStyle(
                'NoPayment',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=1,
            )
            data.append([
                Paragraph("Aucun paiement", no_payment_style),
                '-',
                '-',
                '-',
                '-'
            ])

        # Titre de section
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1a5276'),
            spaceAfter=10,
        )
        story.append(Paragraph("Détail des paiements", section_style))
        
        # Tableau des paiements
        table = Table(data, colWidths=[1.3*inch, 1*inch, 1.2*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            # Lignes alternées
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            # Bordures
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        # Total dans un cadre
        total_str = f"{total:,.0f}".replace(",", " ")
        total_style = ParagraphStyle(
            'TotalStyle',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#1a5276'),
            alignment=2,  # Droite
        )
        story.append(Paragraph(f"<b>Total des paiements validés: {total_str} CDF</b>", total_style))
        story.append(Spacer(1, 30))

        # Générer le hash pour le QR code
        hash_data = {
            'abonne_id': abonne.id,
            'date_debut': str(date_debut),
            'date_fin': str(date_fin),
            'total': float(total), # Assurer float
            'count': paiements.count(),
            'timestamp': timezone.now().isoformat()
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        verification_hash = hashlib.sha256(hash_string.encode()).hexdigest()

        # Enregistrer le relevé généré
        try:
            ReleveGenere.objects.create(
                abonne=abonne,
                date_debut_periode=date_debut,
                date_fin_periode=date_fin,
                nombre_paiements=paiements.count(),
                montant_total=total,
                hash_verification=verification_hash
            )
        except Exception as e:
            # Si doublon de hash (peu probable avec timestamp) ou autre erreur
            print(f"Erreur lors de l'enregistrement du relevé: {e}")

        # Générer le code QR
        qr_data = f"{settings.SITE_URL}/api/paiements/verifier-qr/{verification_hash}/"
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Sauvegarder le QR code dans un buffer
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Section QR Code
        qr_section_style = ParagraphStyle(
            'QRSection',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1a5276'),
            spaceAfter=10,
        )
        story.append(Paragraph("Vérification d'authenticité", qr_section_style))
        story.append(Spacer(1, 5))
        
        qr_info_style = ParagraphStyle(
            'QRInfo',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1,
        )
        story.append(Paragraph("Scannez ce code QR pour vérifier l'authenticité de ce document", qr_info_style))
        story.append(Spacer(1, 10))
        
        # QR code comme Image
        qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
        qr_image.hAlign = 'CENTER'
        story.append(qr_image)
        
        # Hash de vérification (raccourci)
        story.append(Spacer(1, 5))
        hash_style = ParagraphStyle(
            'HashStyle',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.grey,
            alignment=1,
        )
        story.append(Paragraph(f"Réf: {verification_hash[:16]}...", hash_style))

        # Construire le PDF
        doc.build(story)
        buffer.seek(0)

        # Retourner le PDF
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="releve_paiements_{date_debut}_{date_fin}.pdf"'
        return response

    def _generer_suggestions_periodes(self, paiements_existants, date_debut, date_fin):
        """
        Génère des suggestions de périodes valides basées sur l'historique des paiements.
        """
        from datetime import datetime, timedelta
        
        suggestions = []
        
        # 1. Période depuis le premier paiement jusqu'à aujourd'hui
        premier_paiement = paiements_existants.first()
        if premier_paiement:
            suggestions.append({
                "type": "periode_complete",
                "description": "Toute votre historique de paiements",
                "date_debut": premier_paiement.date_transaction.date().strftime('%Y-%m-%d'),
                "date_fin": timezone.now().date().strftime('%Y-%m-%d')
            })
        
        # 2. Les 3 derniers mois avec activité de paiement
        today = timezone.now().date()
        for mois_offset in range(3):
            mois_date = today - timedelta(days=30 * (mois_offset + 1))
            paiements_mois = paiements_existants.filter(
                date_transaction__date__gte=mois_date - timedelta(days=30),
                date_transaction__date__lt=mois_date
            )
            
            if paiements_mois.exists():
                suggestions.append({
                    "type": f"mois_dernier_{mois_offset + 1}",
                    "description": f"Il y a {mois_offset + 1} mois",
                    "date_debut": (mois_date - timedelta(days=30)).strftime('%Y-%m-%d'),
                    "date_fin": mois_date.strftime('%Y-%m-%d')
                })
        
        # 3. Suggestions par trimestre
        for trimestre in range(4):
            trimestre_date = today - timedelta(days=90 * (trimestre + 1))
            paiements_trimestre = paiements_existants.filter(
                date_transaction__date__gte=trimestre_date - timedelta(days=90),
                date_transaction__date__lt=trimestre_date
            )
            
            if paiements_trimestre.exists():
                suggestions.append({
                    "type": f"trimestre_dernier_{trimestre + 1}",
                    "description": f"Il y a {trimestre + 1} trimestre(s)",
                    "date_debut": (trimestre_date - timedelta(days=90)).strftime('%Y-%m-%d'),
                    "date_fin": trimestre_date.strftime('%Y-%m-%d')
                })
        
        # 4. Si la période demandée est trop large, suggérer des périodes plus petites
        periode_demandee = date_fin - date_debut
        if periode_demandee > timedelta(days=90):  # Plus de 3 mois
            # Suggérer des périodes de 3 mois
            debut_mensuel = date_debut
            while debut_mensuel < date_fin:
                fin_mensuel = min(debut_mensuel + timedelta(days=90), date_fin)
                suggestions.append({
                    "type": "periode_suggeree",
                    "description": f"Période de 3 mois: {debut_mensuel} à {fin_mensuel}",
                    "date_debut": debut_mensuel.strftime('%Y-%m-%d'),
                    "date_fin": fin_mensuel.strftime('%Y-%m-%d')
                })
                debut_mensuel = fin_mensuel + timedelta(days=1)
        
        # Limiter à 5 suggestions maximum
        return suggestions[:5]

class VerifierQRView(APIView):
    """
    GET /api/paiements/verifier-qr/{hash}/
    Vérifie l'intégrité d'un relevé de paiement via son hash.
    Retourne une page HTML moderne ou JSON selon l'en-tête Accept.
    """
    permission_classes = [AllowAny]

    def get(self, request, verification_hash, *args, **kwargs):
        # Déterminer si on doit retourner HTML ou JSON
        accept_header = request.META.get('HTTP_ACCEPT', '')
        wants_json = 'application/json' in accept_header and 'text/html' not in accept_header
        
        try:
            releve = ReleveGenere.objects.get(hash_verification=verification_hash)
            
            context = {
                "valid": True,
                "message": "Ce document est authentique.",
                "details": {
                    "abonne": releve.abonne.nom_complet,
                    "numero_abonne": releve.abonne.numero_abonne,
                    "date_generation": releve.date_generation,
                    "periode": f"{releve.date_debut_periode.strftime('%d/%m/%Y')} au {releve.date_fin_periode.strftime('%d/%m/%Y')}",
                    "montant_total": releve.montant_total,
                    "nombre_paiements": releve.nombre_paiements
                },
                "current_year": timezone.now().year
            }
            
            if wants_json:
                return Response(context)
            else:
                return render(request, 'paiements/verifier_qr.html', context)
                
        except ReleveGenere.DoesNotExist:
            context = {
                "valid": False,
                "message": "Ce document est INVALIDE ou inconnu du système.",
                "details": None,
                "current_year": timezone.now().year
            }
            
            if wants_json:
                return Response(context, status=status.HTTP_404_NOT_FOUND)
            else:
                return render(request, 'paiements/verifier_qr.html', context, status=404)


class AdminPaiementViewSet(viewsets.ModelViewSet):
    """API admin pour gérer tous les paiements."""
    serializer_class = PaiementSerializer
    permission_classes = [IsAdminUser]
    queryset = Paiement.objects.all().order_by('-date_transaction').select_related('abonne__user', 'facture')


class JConsultPaiementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API JConsult pour consulter tous les paiements en lecture seule.
    Accessible aux utilisateurs staff (is_staff=True) pour visualisation uniquement.
    """
    serializer_class = PaiementSerializer
    permission_classes = [IsStaffOrReadOnly]
    queryset = Paiement.objects.all().order_by('-date_transaction').select_related('abonne__user', 'facture')

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres optionnels pour JConsult
        abonne_id = self.request.query_params.get('abonne_id')
        if abonne_id:
            queryset = queryset.filter(abonne__id=abonne_id)
        
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        return queryset