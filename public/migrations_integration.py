# -*- coding: utf-8 -*-
"""
Migrations pour l'intégration Mobile Money dans la billetterie SI-SEP Sport RDC
Fichier de configuration pour les migrations à créer
"""

# MIGRATION 1: Ajouter les champs Mobile Money au modèle Vente
"""
python manage.py makemigrations public --name add_mobile_money_fields_to_vente

# Dans le fichier de migration généré:
migrations.AddField(
    model_name='vente',
    name='reference_interne',
    field=models.CharField(blank=True, max_length=255, help_text='Référence interne pour le paiement'),
)
migrations.AddField(
    model_name='vente',
    name='order_number',
    field=models.CharField(blank=True, max_length=255, help_text='Numéro de commande FlexPay'),
)
migrations.AddField(
    model_name='vente',
    name='methode_paiement',
    field=models.CharField(
        blank=True,
        max_length=20,
        choices=[
            ('MPESA', 'M-Pesa'),
            ('ORANGE_MONEY', 'Orange Money'),
            ('AIRTEL_MONEY', 'Airtel Money'),
            ('GUICHET', 'Guichet'),
            ('EN_LIGNE', 'En ligne'),
        ],
        help_text='Méthode de paiement utilisée'
    ),
)
migrations.AddField(
    model_name='vente',
    name='telephone_payeur',
    field=models.CharField(blank=True, max_length=20, help_text='Téléphone du payeur'),
)
migrations.AddField(
    model_name='vente',
    name='statut_paiement',
    field=models.CharField(
        default='EN_ATTENTE',
        max_length=20,
        choices=[
            ('INITIE', 'Initié'),
            ('EN_ATTENTE', 'En attente'),
            ('VALIDE', 'Validé'),
            ('ECHOUE', 'Échoué'),
            ('ANNULE', 'Annulé'),
        ],
        help_text='Statut du paiement'
    ),
)
migrations.AddField(
    model_name='vente',
    name='date_validation',
    field=models.DateTimeField(
        blank=True,
        null=True,
        help_text='Date de validation du paiement'
    ),
)
migrations.AddField(
    model_name='vente',
    name='reference_operateur',
    field=models.CharField(blank=True, max_length=255, help_text='Référence de l\'opérateur'),
)
migrations.AddField(
    model_name='vente',
    name='detail_callback',
    field=models.JSONField(blank=True, null=True, help_text='Détails du callback de paiement'),
)
migrations.AddField(
    model_name='vente',
    name='erreur_paiement',
    field=models.TextField(blank=True, help_text='Message d\'erreur si paiement échoué'),
)
"""

# MIGRATION 2: Ajouter le champ QR code au modèle Ticket
"""
python manage.py makemigrations public --name add_qr_code_to_ticket

# Dans le fichier de migration généré:
migrations.AddField(
    model_name='ticket',
    name='qr_code',
    field=models.ImageField(
        blank=True,
        null=True,
        upload_to='qr_codes/tickets/',
        help_text='Image du QR code pour vérification'
    ),
)
"""

# MIGRATION 3: Créer les nouveaux modèles
"""
python manage.py makemigrations public

# Créera automatiquement les modèles:
# - VerificationQR
# - TransactionMobileMoney
"""

# COMMANDES COMPLÈTES À EXÉCUTER:
"""
# 1. Créer les migrations
python manage.py makemigrations public --name add_mobile_money_fields_to_vente
python manage.py makemigrations public --name add_qr_code_to_ticket
python manage.py makemigrations public

# 2. Appliquer les migrations
python manage.py migrate

# 3. Créer les répertoires pour les QR codes
mkdir -p media/qr_codes/tickets/
"""
