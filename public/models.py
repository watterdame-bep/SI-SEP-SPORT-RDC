# -*- coding: utf-8 -*-
"""
Modèles supplémentaires pour la billetterie SI-SEP Sport RDC
Extension des modèles existants pour le paiement Mobile Money
"""
from django.db import models
import uuid


# Extension du modèle Vente avec champs de paiement
# Note: Ces champs seront ajoutés via une migration
class VenteExtension(models.Model):
    """
    Extension pour ajouter les champs de paiement Mobile Money au modèle Vente existant
    """
    # Champs de paiement Mobile Money
    reference_interne = models.CharField(max_length=255, blank=True, help_text="Référence interne pour le paiement")
    order_number = models.CharField(max_length=255, blank=True, help_text="Numéro de commande FlexPay")
    methode_paiement = models.CharField(
        max_length=20,
        choices=[
            ('MPESA', 'M-Pesa'),
            ('ORANGE_MONEY', 'Orange Money'),
            ('AIRTEL_MONEY', 'Airtel Money'),
            ('GUICHET', 'Guichet'),
            ('EN_LIGNE', 'En ligne'),
        ],
        blank=True,
        help_text="Méthode de paiement utilisée"
    )
    telephone_payeur = models.CharField(max_length=20, blank=True, help_text="Téléphone du payeur")
    statut_paiement = models.CharField(
        max_length=20,
        choices=[
            ('INITIE', 'Initié'),
            ('EN_ATTENTE', 'En attente'),
            ('VALIDE', 'Validé'),
            ('ECHOUE', 'Échoué'),
            ('ANNULE', 'Annulé'),
        ],
        default='EN_ATTENTE',
        help_text="Statut du paiement"
    )
    date_validation = models.DateTimeField(null=True, blank=True, help_text="Date de validation du paiement")
    reference_operateur = models.CharField(max_length=255, blank=True, help_text="Référence de l'opérateur")
    detail_callback = models.JSONField(blank=True, null=True, help_text="Détails du callback de paiement")
    erreur_paiement = models.TextField(blank=True, help_text="Message d'erreur si paiement échoué")
    
    class Meta:
        db_table = 'vente_extension'
        verbose_name = 'Extension Vente'
        verbose_name_plural = 'Extensions Ventes'


# Extension du modèle Ticket avec QR code
# Note: Le champ qr_code sera ajouté via une migration
class TicketExtension(models.Model):
    """
    Extension pour ajouter le champ QR code au modèle Ticket existant
    """
    # Champ QR code
    qr_code = models.ImageField(
        upload_to='qr_codes/tickets/',
        null=True,
        blank=True,
        help_text="Image du QR code pour vérification"
    )
    
    class Meta:
        db_table = 'ticket_extension'
        verbose_name = 'Extension Ticket'
        verbose_name_plural = 'Extensions Tickets'


class VerificationQR(models.Model):
    """
    Modèle pour stocker les informations de vérification QR
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.OneToOneField(
        'infrastructures.Ticket',
        on_delete=models.CASCADE,
        related_name='verification_qr'
    )
    hash_verification = models.CharField(max_length=64, unique=True, help_text="Hash de vérification unique")
    date_generation = models.DateTimeField(auto_now_add=True)
    url_verification = models.URLField(help_text="URL de vérification publique")
    
    class Meta:
        db_table = 'verification_qr'
        verbose_name = 'Vérification QR'
        verbose_name_plural = 'Vérifications QR'
    
    def __str__(self):
        return f"QR {self.ticket.uid[:8]}…"
    
    @classmethod
    def generer_pour_ticket(cls, ticket):
        """
        Génère une entrée de vérification QR pour un ticket
        """
        import hashlib
        import json
        
        # Générer le hash de vérification
        data = {
            'ticket_uid': str(ticket.uid),
            'vente_uid': str(ticket.vente.uid) if ticket.vente else None,
            'evenement_uid': str(ticket.evenement_zone.evenement.uid),
            'zone_uid': str(ticket.evenement_zone.zone_stade.uid),
            'timestamp': ticket.date_creation.isoformat()
        }
        
        hash_string = json.dumps(data, sort_keys=True)
        hash_verification = hashlib.sha256(hash_string.encode()).hexdigest()
        
        # Créer l'entrée
        from django.conf import settings
        url_verification = f"{settings.SITE_URL}/api/billetterie/verifier-qr/{hash_verification}/"
        
        return cls.objects.create(
            ticket=ticket,
            hash_verification=hash_verification,
            url_verification=url_verification
        )


class TransactionMobileMoney(models.Model):
    """
    Historique des transactions Mobile Money pour audit
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vente = models.ForeignKey(
        'infrastructures.Vente',
        on_delete=models.CASCADE,
        related_name='transactions_mm'
    )
    operateur = models.CharField(
        max_length=20,
        choices=[
            ('MPESA', 'M-Pesa'),
            ('ORANGE_MONEY', 'Orange Money'),
            ('AIRTEL_MONEY', 'Airtel Money'),
        ]
    )
    reference_operateur = models.CharField(max_length=255, help_text="Référence transaction opérateur")
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    devise = models.CharField(max_length=3, default='CDF')
    statut = models.CharField(
        max_length=20,
        choices=[
            ('INITIE', 'Initié'),
            ('EN_COURS', 'En cours'),
            ('VALIDE', 'Validé'),
            ('ECHOUE', 'Échoué'),
            ('ANNULE', 'Annulé'),
        ]
    )
    date_initiation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    reponse_api = models.JSONField(blank=True, null=True, help_text="Réponse de l'API FlexPay")
    
    class Meta:
        db_table = 'transaction_mobile_money'
        verbose_name = 'Transaction Mobile Money'
        verbose_name_plural = 'Transactions Mobile Money'
        ordering = ['-date_initiation']
    
    def __str__(self):
        return f"{self.operateur} - {self.reference_operateur} - {self.montant} {self.devise}"
