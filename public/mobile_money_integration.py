# -*- coding: utf-8 -*-
"""
Intégration Mobile Money pour la billetterie SI-SEP Sport RDC
Basé sur le système FlexPay existant
"""
import requests
import time
import threading
import hashlib
import qrcode
from io import BytesIO
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction

from infrastructures.models import Vente, Ticket


class MobileMoneyPaymentProcessor:
    """
    Processeur de paiement Mobile Money pour la billetterie
    Utilise l'API FlexPay pour M-Pesa, Orange Money, Airtel Money
    """
    
    def __init__(self):
        self.api_url = getattr(settings, 'FLEXPAY_API_URL', 'https://backend.flexpay.cd/api/rest/v1/paymentService')
        self.check_url = getattr(settings, 'FLEXPAY_CHECK_URL', 'https://backend.flexpay.cd/api/rest/v1/check/')
        self.bearer_token = getattr(settings, 'FLEXPAY_BEARER_TOKEN', '')
        self.merchant = getattr(settings, 'FLEXPAY_MERCHANT', 'SISEP-SPORT')
        self.site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    
    def initier_paiement(self, vente, methode, telephone_payeur):
        """
        Initialise une transaction Mobile Money pour une vente de billets
        
        Args:
            vente: Instance Vente
            methode: 'MPESA', 'ORANGE_MONEY', ou 'AIRTEL_MONEY'
            telephone_payeur: Numéro de téléphone du payeur
            
        Returns:
            dict: Résultat de l'initiation avec order_number
        """
        try:
            # Créer une référence unique
            reference_interne = f"SISEP-{vente.uid}-{int(time.time())}"
            
            # Préparer le payload pour FlexPay
            payload = {
                "merchant": self.merchant,
                "reference": reference_interne,
                "amount": str(int(vente.montant_total)),
                "currency": "CDF",
                "phone": telephone_payeur,
                "description": f"Billets match - {vente.reference_paiement}",
                "callbackUrl": f"{self.site_url}/api/billetterie/callback/mmo/",
                "approve_url": f"{self.site_url}/api/billetterie/callback/mmo/",
                "cancel_url": f"{self.site_url}/api/billetterie/callback/mmo/",
                "decline_url": f"{self.site_url}/api/billetterie/callback/mmo/",
                "type": 1
            }
            
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            # Appel à l'API FlexPay
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            
            if response_data.get('code') != '0':
                raise Exception(f"FlexPay API error: {response_data}")
            
            order_number = response_data.get('orderNumber')
            if not order_number:
                raise Exception("FlexPay API did not return orderNumber")
            
            # Mettre à jour la vente avec les informations de paiement
            vente.reference_interne = reference_interne
            vente.order_number = order_number
            vente.methode_paiement = methode
            vente.telephone_payeur = telephone_payeur
            vente.statut_paiement = 'INITIE'
            vente.save()
            
            # Lancer la vérification en arrière-plan
            self._lancer_verification_background(vente.id)
            
            return {
                'success': True,
                'order_number': order_number,
                'reference_interne': reference_interne,
                'message': 'Paiement initié avec succès'
            }
            
        except Exception as e:
            # Marquer la vente comme échouée
            vente.statut_paiement = 'ECHOUE'
            vente.erreur_paiement = str(e)
            vente.save()
            
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de l\'initialisation du paiement'
            }
    
    def verifier_paiement(self, order_number):
        """
        Vérifie le statut d'un paiement auprès de FlexPay
        
        Args:
            order_number: Numéro de commande FlexPay
            
        Returns:
            dict: Statut du paiement
        """
        try:
            url = f"{self.check_url}{order_number}"
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == '0' and data.get('transaction'):
                transaction = data.get('transaction')
                return {
                    'success': True,
                    'status': transaction.get('status'),
                    'transaction': transaction
                }
            else:
                return {
                    'success': False,
                    'status': 'NOT_FOUND',
                    'message': 'Transaction non trouvée'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la vérification'
            }
    
    def _lancer_verification_background(self, vente_id):
        """
        Lance la vérification en arrière-plan avec retry
        """
        def _verify_payment_background():
            try:
                from infrastructures.models import Vente
                vente = Vente.objects.get(id=vente_id)
                
                # Vérifier pendant 10 minutes (120 tentatives x 5 secondes)
                for attempt in range(1, 121):
                    if not vente.order_number:
                        break
                        
                    verification = self.verifier_paiement(vente.order_number)
                    
                    if verification['success']:
                        status = verification['status']
                        
                        if status == '0':  # Paiement validé
                            self._valider_paiement(vente)
                            break
                        elif status == '1':  # Paiement échoué
                            self._echouer_paiement(vente)
                            break
                        # status == '2' = en attente, continuer
                    
                    if attempt < 120:
                        time.sleep(5)
                        
            except Exception as e:
                print(f"Erreur dans vérification background: {e}")
        
        # Lancer dans un thread daemon
        thread = threading.Thread(target=_verify_payment_background, daemon=True)
        thread.start()
    
    def _valider_paiement(self, vente):
        """
        Valide le paiement et génère les QR codes
        """
        with transaction.atomic():
            vente.statut_paiement = 'VALIDE'
            vente.date_validation = timezone.now()
            vente.save()
            
            # Générer les QR codes pour tous les tickets de la vente
            self._generer_qr_codes_tickets(vente)
    
    def _echouer_paiement(self, vente):
        """
        Marque le paiement comme échoué et libère les tickets
        """
        with transaction.atomic():
            vente.statut_paiement = 'ECHOUE'
            vente.save()
            
            # Libérer les tickets
            vente.tickets.update(
                statut='DISPONIBLE',
                vente=None
            )
    
    def _generer_qr_codes_tickets(self, vente):
        """
        Génère les QR codes pour tous les tickets de la vente
        """
        for ticket in vente.tickets.all():
            qr_data = self._generer_donnees_qr(ticket)
            qr_image = self._creer_qr_image(qr_data)
            
            # Sauvegarder l'image QR code
            filename = f"qr_ticket_{ticket.uid}.png"
            ticket.qr_code.save(filename, ContentFile(qr_image), save=True)
    
    def _generer_donnees_qr(self, ticket):
        """
        Génère les données pour le QR code d'un ticket
        """
        data = {
            'ticket_uid': str(ticket.uid),
            'vente_uid': str(ticket.vente.uid),
            'evenement': ticket.evenement_zone.evenement.titre,
            'zone': ticket.evenement_zone.zone_stade.nom,
            'date_evenement': ticket.evenement_zone.evenement.date_evenement.isoformat(),
            'prix': str(ticket.evenement_zone.prix_unitaire),
            'statut': ticket.statut,
            'hash_verification': self._generer_hash_ticket(ticket)
        }
        return data
    
    def _generer_hash_ticket(self, ticket):
        """
        Génère un hash de vérification pour le ticket
        """
        data = f"{ticket.uid}-{ticket.vente.uid}-{ticket.evenement_zone.evenement.uid}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _creer_qr_image(self, data):
        """
        Crée une image QR code à partir des données
        """
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
            error_correction=qrcode.constants.ERROR_CORRECT_L
        )
        
        # Convertir les données en chaîne JSON
        import json
        qr.add_data(json.dumps(data))
        qr.make(fit=True)
        
        # Créer l'image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir en bytes
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()


class MobileMoneyCallbackHandler:
    """
    Gestionnaire des callbacks/webhooks Mobile Money
    """
    
    def __init__(self):
        self.processor = MobileMoneyPaymentProcessor()
    
    def handle_callback(self, data):
        """
        Traite un callback de FlexPay
        
        Args:
            data: Données du callback
            
        Returns:
            dict: Résultat du traitement
        """
        try:
            # Extraire les informations du callback
            reference_interne = data.get('snel_reference', data.get('merchant_ref'))
            operateur_status = data.get('status', data.get('transaction_status'))
            reference_operateur = data.get('transaction_id', data.get('provider_id'))
            montant_paye = data.get('amount')
            
            if not reference_interne:
                return {'success': False, 'error': 'Référence manquante'}
            
            # Trouver la vente
            from infrastructures.models import Vente
            vente = Vente.objects.get(reference_interne=reference_interne)
            
            # Mettre à jour les détails
            vente.reference_operateur = reference_operateur
            vente.detail_callback = data
            
            # Vérifier le statut
            if operateur_status == 'SUCCESS' and self._verifier_montant(montant_paye, vente.montant_total):
                self.processor._valider_paiement(vente)
                return {'success': True, 'message': 'Paiement validé'}
            else:
                self.processor._echouer_paiement(vente)
                return {'success': True, 'message': 'Paiement échoué'}
                
        except Vente.DoesNotExist:
            return {'success': False, 'error': 'Vente non trouvée'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _verifier_montant(self, montant_paye, montant_attendu):
        """
        Vérifie que le montant payé correspond au montant attendu
        """
        if montant_paye is None:
            return False
        try:
            return float(montant_paye) >= float(montant_attendu)
        except (ValueError, TypeError):
            return False
