# -*- coding: utf-8 -*-
"""
Service d'envoi de SMS pour les billets
"""

import requests
import json
from django.conf import settings
from django.urls import reverse
from infrastructures.models import Ticket


class SMSService:
    """Service pour l'envoi de SMS contenant les billets"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'SMS_API_URL', 'https://api.sms-service.com/send')
        self.api_key = getattr(settings, 'SMS_API_KEY', 'your_sms_api_key')
        self.sender_name = getattr(settings, 'SMS_SENDER_NAME', 'SISEPRDC')
    
    def envoyer_billet_sms(self, telephone, ticket):
        """
        Envoie un SMS contenant les informations du billet
        """
        try:
            # Générer l'URL du billet
            ticket_url = f"{settings.SITE_URL}{reverse('public:view_ticket', args=[ticket.uid])}"
            
            # Construire le message SMS
            message = self._construire_message_billet(ticket, ticket_url)
            
            # Préparer les données pour l'API SMS
            sms_data = {
                'api_key': self.api_key,
                'sender': self.sender_name,
                'to': self._formater_telephone(telephone),
                'message': message
            }
            
            # Envoyer le SMS
            response = requests.post(self.api_url, json=sms_data, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'SMS envoyé avec succès',
                    'response': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': f'Erreur API SMS: {response.status_code}',
                    'response': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Erreur de connexion SMS: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur inattendue: {str(e)}'
            }
    
    def envoyer_plusieurs_billets_sms(self, telephone, tickets):
        """
        Envoie un SMS contenant plusieurs billets
        """
        try:
            # Construire le message pour plusieurs billets
            message = self._construire_message_plusieurs_billets(tickets, telephone)
            
            # Préparer les données pour l'API SMS
            sms_data = {
                'api_key': self.api_key,
                'sender': self.sender_name,
                'to': self._formater_telephone(telephone),
                'message': message
            }
            
            # Envoyer le SMS
            response = requests.post(self.api_url, json=sms_data, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'SMS envoyé avec succès',
                    'response': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': f'Erreur API SMS: {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur: {str(e)}'
            }
    
    def _construire_message_billet(self, ticket, ticket_url):
        """
        Construit le message SMS pour un billet
        """
        evenement = ticket.evenement_zone.evenement
        zone = ticket.evenement_zone.zone_stade
        stade = evenement.stade
        
        message = f"""SI-SEP Sport RDC - BILLET VALIDÉ
        
Match: {evenement.nom}
Date: {evenement.date_evenement.strftime('%d/%m/%Y %H:%M')}
Lieu: {stade.nom}
Zone: {zone.nom}
Prix: {ticket.evenement_zone.prix_unitaire} CDF

N° Billet: {ticket.numero_billet}
Lien: {ticket_url}

Presentez ce N° ou scannez le QR code à l'entrée.
Merci pour votre achat!"""
        
        return message
    
    def _construire_message_plusieurs_billets(self, tickets, telephone):
        """
        Construit le message SMS pour plusieurs billets
        """
        if not tickets:
            return ""
        
        # Prendre le premier ticket pour les infos de l'événement
        premier_ticket = tickets[0]
        evenement = premier_ticket.evenement_zone.evenement
        zone = premier_ticket.evenement_zone.zone_stade
        stade = evenement.stade
        
        # Construire la liste des numéros de billets
        numeros_billets = []
        for ticket in tickets:
            numeros_billets.append(ticket.numero_billet)
        
        message = f"""SI-SEP Sport RDC - BILLETS VALIDÉS ({len(tickets)})
        
Match: {evenement.nom}
Date: {evenement.date_evenement.strftime('%d/%m/%Y %H:%M')}
Lieu: {stade.nom}
Zone: {zone.nom}
Total: {sum(ticket.evenement_zone.prix_unitaire for ticket in tickets)} CDF

N° Billets: {', '.join(numeros_billets[:3])}"""
        
        if len(numeros_billets) > 3:
            message += f" +{len(numeros_billets) - 3} autre(s)"
        
        message += """

Consultez vos billets complets sur notre site.
Presentez ces N° à l'entrée.
Merci pour votre achat!"""
        
        return message
    
    def _formater_telephone(self, telephone):
        """
        Formate le numéro de téléphone pour l'API SMS
        """
        # Nettoyer le numéro
        telephone = telephone.replace(' ', '').replace('+', '').replace('-', '')
        
        # Ajouter le préfixe international si nécessaire
        if not telephone.startswith('243'):
            telephone = '243' + telephone[-9:]  # Garder seulement les 9 derniers chiffres
        
        return telephone
    
    def envoyer_sms_confirmation_paiement(self, telephone, vente):
        """
        Envoie un SMS de confirmation de paiement
        """
        try:
            tickets = Ticket.objects.filter(vente=vente)
            
            if tickets.count() == 1:
                return self.envoyer_billet_sms(telephone, tickets.first())
            else:
                return self.envoyer_plusieurs_billets_sms(telephone, tickets)
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors de l\'envoi SMS: {str(e)}'
            }


# Instance globale du service SMS
sms_service = SMSService()
