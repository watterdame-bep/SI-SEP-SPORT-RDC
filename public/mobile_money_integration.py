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
import json
from io import BytesIO
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction

from infrastructures.models import Vente, Ticket, EvenementZone


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
    
    def formater_telephone(self, telephone):
        """
        Formate le numéro de téléphone pour FlexPay
        Format spécifique pour RDC: 243XXXXXXXXX (12 chiffres avec indicatif)
        """
        if not telephone:
            return None
            
        # Supprimer tous les caractères non numériques
        telephone_nettoye = ''.join(filter(str.isdigit, telephone))
        
        print(f"DEBUG FLEXPAY: Formatage téléphone - Format 243XXXXXXXXX")
        print(f"  - Original: {telephone}")
        print(f"  - Nettoyé: {telephone_nettoye} (longueur: {len(telephone_nettoye)})")
        
        # Format spécifique pour FlexPay RDC: 243 + 9 chiffres = 12 chiffres
        if len(telephone_nettoye) >= 9:
            # Prendre les 9 derniers chiffres et ajouter 243 au début
            format_9 = telephone_nettoye[-9:]
            format_243 = "243" + format_9
            print(f"  - Format 243XXXXXXXXX (FlexPay RDC): {format_243}")
            return format_243
        else:
            # Numéro trop court, retourner tel quel
            print(f"  - Format tel quel (court): {telephone_nettoye}")
            return telephone_nettoye
    
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
            # Créer une référence unique COURTE (max 50 caractères pour FlexPay)
            # Format: SISEP-{8 premiers chars UUID}-{timestamp}
            vente_short_id = str(vente.uid).split('-')[0]  # 8 caractères
            timestamp = int(time.time())
            reference_interne = f"SISEP-{vente_short_id}-{timestamp}"
            
            # Formater le numéro de téléphone pour FlexPay
            telephone_formate = self.formater_telephone(telephone_payeur)
            if not telephone_formate:
                raise Exception("Numéro de téléphone invalide")
            
            print(f"DEBUG FLEXPAY: Initialisation paiement")
            print(f"  - Vente UID: {vente.uid}")
            print(f"  - Montant: {vente.montant_total}")
            print(f"  - Méthode: {methode}")
            print(f"  - Téléphone original: {telephone_payeur}")
            print(f"  - Téléphone formatté: {telephone_formate}")
            print(f"  - Référence: {reference_interne} (longueur: {len(reference_interne)})")
            
            # Préparer le payload pour FlexPay
            payload = {
                "merchant": self.merchant,
                "reference": reference_interne,
                "amount": str(int(vente.montant_total)),
                "currency": "CDF",
                "phone": telephone_formate,
                "description": f"Billets match - {vente.reference_paiement}",
                "callbackUrl": f"{self.site_url}/api/callback/mmo/",
                "approve_url": f"{self.site_url}/api/callback/mmo/",
                "cancel_url": f"{self.site_url}/api/callback/mmo/",
                "decline_url": f"{self.site_url}/api/callback/mmo/",
                "type": 1
            }
            
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            print(f"DEBUG FLEXPAY: Payload préparé")
            print(f"  - API URL: {self.api_url}")
            print(f"  - Merchant: {self.merchant}")
            print(f"  - Bearer token présent: {bool(self.bearer_token)}")
            print(f"  - Payload: {json.dumps(payload, indent=2)}")
            
            # Appel à l'API FlexPay
            print(f"DEBUG FLEXPAY: Envoi requête à FlexPay...")
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)  # 60 secondes au lieu de 30
            
            print(f"DEBUG FLEXPAY: Réponse reçue")
            print(f"  - Status code: {response.status_code}")
            print(f"  - Contenu: {response.text}")
            
            response.raise_for_status()
            
            response_data = response.json()
            
            if response_data.get('code') != '0':
                error_msg = f"FlexPay API error: code={response_data.get('code')}, message={response_data.get('message', 'Unknown')}"
                print(f"DEBUG FLEXPAY: ERREUR - {error_msg}")
                raise Exception(error_msg)
            
            order_number = response_data.get('orderNumber')
            if not order_number:
                error_msg = f"FlexPay API did not return orderNumber: {response_data}"
                print(f"DEBUG FLEXPAY: ERREUR - {error_msg}")
                raise Exception(error_msg)
            
            print(f"DEBUG FLEXPAY: Succès! Order number: {order_number}")
            
            # Mettre à jour la vente avec les informations de paiement
            # Stocker order_number dans notes (JSON) car pas de champ dédié
            vente.notes = json.dumps({
                'reference_interne': reference_interne,
                'order_number': order_number,
                'methode_paiement': methode,
                'telephone_payeur': telephone_payeur,
                'statut_paiement': 'INITIE'
            })
            vente.reference_paiement = f"{order_number}-{reference_interne}"
            vente.save()
            
            # Lancer la vérification en arrière-plan
            self._lancer_verification_background(str(vente.uid))
            
            return {
                'success': True,
                'order_number': order_number,
                'reference_interne': reference_interne,
                'message': 'Paiement initié avec succès'
            }
            
        except requests.exceptions.Timeout as e:
            error_msg = f"Timeout lors de l'appel FlexPay: {str(e)}"
            print(f"DEBUG FLEXPAY: ERREUR TIMEOUT - {error_msg}")
            print(f"  → Le paiement peut quand même être validé par FlexPay")
            print(f"  → On garde le statut INITIE et on attend le callback")
            
            # NE PAS marquer comme échoué! Le paiement peut quand même réussir
            # On laisse le statut INITIE et on attend le callback FlexPay
            notes_data = json.loads(vente.notes) if vente.notes else {}
            notes_data['timeout_initiation'] = error_msg
            notes_data['timeout_at'] = timezone.now().isoformat()
            # Garder statut_paiement = 'INITIE'
            vente.notes = json.dumps(notes_data)
            vente.save()
            
            return {
                'success': True,  # On considère que c'est un succès partiel
                'timeout': True,
                'error': error_msg,
                'message': 'Paiement en cours de traitement. Veuillez patienter.'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur réseau FlexPay: {str(e)}"
            print(f"DEBUG FLEXPAY: ERREUR RESEAU - {error_msg}")
            notes_data = json.loads(vente.notes) if vente.notes else {}
            notes_data['statut_paiement'] = 'ECHOUE'
            notes_data['erreur_paiement'] = error_msg
            vente.notes = json.dumps(notes_data)
            vente.save()
            
            return {
                'success': False,
                'error': error_msg,
                'message': 'Erreur de connexion à FlexPay. Veuillez réessayer.'
            }
            
        except Exception as e:
            error_msg = f"Erreur inattendue: {str(e)}"
            print(f"DEBUG FLEXPAY: ERREUR GENERALE - {error_msg}")
            import traceback
            print(traceback.format_exc())
            
            notes_data = json.loads(vente.notes) if vente.notes else {}
            notes_data['statut_paiement'] = 'ECHOUE'
            notes_data['erreur_paiement'] = error_msg
            vente.notes = json.dumps(notes_data)
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
            
            print(f"DEBUG FLEXPAY CHECK: Vérification du paiement {order_number}")
            print(f"  - URL: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            print(f"DEBUG FLEXPAY CHECK: Réponse reçue")
            print(f"  - Code: {data.get('code')}")
            print(f"  - Data complète: {json.dumps(data, indent=2)}")
            
            if data.get('code') == '0' and data.get('transaction'):
                transaction = data.get('transaction')
                status = transaction.get('status')
                
                print(f"DEBUG FLEXPAY CHECK: Transaction trouvée")
                print(f"  - Statut: {status}")
                print(f"  - Transaction: {json.dumps(transaction, indent=2)}")
                
                return {
                    'success': True,
                    'status': status,
                    'transaction': transaction,
                    'message': transaction.get('message', '')
                }
            else:
                print(f"DEBUG FLEXPAY CHECK: Transaction non trouvée ou code != 0")
                return {
                    'success': False,
                    'status': 'NOT_FOUND',
                    'message': 'Transaction non trouvée'
                }
                
        except Exception as e:
            print(f"DEBUG FLEXPAY CHECK: ERREUR - {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la vérification'
            }
    
    def verifier_paiement_par_reference(self, reference_interne):
        """
        Vérifie le statut d'un paiement auprès de FlexPay en utilisant la référence interne
        Utile quand le order_number n'a pas été enregistré à cause d'un timeout
        
        Args:
            reference_interne: Référence interne (format SISEP-XXX-timestamp)
            
        Returns:
            dict: Statut du paiement
        """
        try:
            # FlexPay n'a pas d'API pour chercher par référence merchant
            # On va essayer de récupérer toutes les transactions récentes et chercher
            # Mais pour l'instant, on retourne NOT_FOUND
            print(f"DEBUG FLEXPAY CHECK REF: Vérification par référence {reference_interne}")
            print(f"  - FlexPay n'a pas d'API de recherche par référence merchant")
            print(f"  - Il faut utiliser le order_number retourné lors de l'initiation")
            
            return {
                'success': False,
                'status': 'NOT_FOUND',
                'message': 'Impossible de vérifier sans order_number'
            }
                
        except Exception as e:
            print(f"DEBUG FLEXPAY CHECK REF: ERREUR - {str(e)}")
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
                vente = Vente.objects.get(uid=vente_id)
                
                # Extraire order_number depuis notes
                notes_data = json.loads(vente.notes) if vente.notes else {}
                order_number = notes_data.get('order_number')
                
                if not order_number:
                    print(f"Pas d'order_number pour vente {vente_id}")
                    return
                
                # Vérifier pendant 10 minutes (120 tentatives x 5 secondes)
                for attempt in range(1, 121):
                    verification = self.verifier_paiement(order_number)
                    
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
            # Mettre à jour le statut dans notes
            notes_data = json.loads(vente.notes) if vente.notes else {}
            notes_data['statut_paiement'] = 'VALIDE'
            notes_data['date_validation'] = timezone.now().isoformat()
            vente.notes = json.dumps(notes_data)
            vente.save()
            
            # Générer les QR codes pour tous les tickets de la vente
            self._generer_qr_codes_tickets(vente)
    
    def _echouer_paiement(self, vente):
        """
        Marque le paiement comme échoué et libère les tickets
        """
        with transaction.atomic():
            # Mettre à jour le statut dans notes
            notes_data = json.loads(vente.notes) if vente.notes else {}
            notes_data['statut_paiement'] = 'ECHOUE'
            vente.notes = json.dumps(notes_data)
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
            # Générer URL de vérification
            verification_url = f"{self.site_url}/verify/ticket/{ticket.uid}/"
            
            # Créer QR code simple avec l'URL
            qr_image = self._creer_qr_image(verification_url)
            
            # Sauvegarder l'image QR code si le modèle a ce champ
            # Sinon, on peut le stocker dans notes ou l'ignorer
            try:
                filename = f"qr_ticket_{ticket.uid}.png"
                if hasattr(ticket, 'qr_code'):
                    ticket.qr_code.save(filename, ContentFile(qr_image), save=True)
            except Exception as e:
                print(f"Impossible de sauvegarder QR code: {e}")
    
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
        Crée une image QR code à partir des données (URL ou dict)
        """
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
            error_correction=qrcode.constants.ERROR_CORRECT_L
        )
        
        # Si data est un dict, le convertir en JSON, sinon utiliser tel quel
        if isinstance(data, dict):
            qr.add_data(json.dumps(data))
        else:
            qr.add_data(str(data))
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
            
            # Trouver la vente par reference_interne dans notes
            from infrastructures.models import Vente
            ventes = Vente.objects.filter(notes__contains=reference_interne)
            if not ventes.exists():
                return {'success': False, 'error': 'Vente non trouvée'}
            vente = ventes.first()
            
            # Mettre à jour les détails dans notes
            notes_data = json.loads(vente.notes) if vente.notes else {}
            notes_data['reference_operateur'] = reference_operateur
            notes_data['detail_callback'] = data
            
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
