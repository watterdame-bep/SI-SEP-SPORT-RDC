# Guide d'Intégration Mobile Money - SI-SEP Sport RDC

## 🎯 Objectif

Intégrer le système de paiement Mobile Money (M-Pesa, Orange Money, Airtel Money) dans la billetterie SI-SEP Sport RDC, basé sur l'API FlexPay existante.

## 📋 Prérequis

1. **Compte FlexPay** actif avec token d'API
2. **Configuration Django** existante
3. **Modèles de billetterie** déjà créés

## 🚀 Étapes d'Intégration

### 1. Configuration des Paramètres

Ajouter dans `config/settings.py`:

```python
# Importer la configuration Mobile Money
from .settings_mobile_money import *

# Ou ajouter directement:
FLEXPAY_API_URL = 'https://backend.flexpay.cd/api/rest/v1/paymentService'
FLEXPAY_CHECK_URL = 'https://backend.flexpay.cd/api/rest/v1/check/'
FLEXPAY_BEARER_TOKEN = 'votre_token_flexpay'
FLEXPAY_MERCHANT = 'SISEP-SPORT'
SITE_URL = 'http://127.0.0.1:8000'  # URL de votre site
```

### 2. Création des Migrations

Exécuter les commandes suivantes:

```bash
# 1. Ajouter les champs Mobile Money au modèle Vente
python manage.py makemigrations public --name add_mobile_money_fields_to_vente

# 2. Ajouter le champ QR code au modèle Ticket  
python manage.py makemigrations public --name add_qr_code_to_ticket

# 3. Créer les nouveaux modèles
python manage.py makemigrations public

# 4. Appliquer toutes les migrations
python manage.py migrate

# 5. Créer les répertoires pour les QR codes
mkdir -p media/qr_codes/tickets/
```

### 3. Configuration des URLs

Ajouter dans `config/urls.py`:

```python
urlpatterns = [
    # URLs existantes...
    path('api/billetterie/', include('public.urls_api')),
]
```

### 4. Installation des Dépendances

Ajouter dans `requirements.txt`:

```
requests>=2.31.0
qrcode[pil]>=7.4.0
Pillow>=10.0.0
```

Installer avec:
```bash
pip install requests qrcode[pil] Pillow
```

## 🔄 Flux de Paiement Mobile Money

### Étape 1: Sélection du Mode de Paiement
- Utilisateur choisit M-Pesa, Orange Money ou Airtel Money
- Saisit son numéro de téléphone

### Étape 2: Initialisation du Paiement
```python
# La vue process_payment détecte le paiement Mobile Money
if payment_method in ['MPESA', 'ORANGE_MONEY', 'AIRTEL_MONEY']:
    processor = MobileMoneyPaymentProcessor()
    resultat = processor.initier_paiement(vente, payment_method, telephone)
```

### Étape 3: Traitement par FlexPay
- Envoi de la requête à l'API FlexPay
- Réception du `order_number`
- Lancement de la vérification en arrière-plan

### Étape 4: Vérification Automatisée
- Vérification toutes les 5 secondes pendant 10 minutes
- Mise à jour automatique du statut du paiement
- Génération des QR codes après validation

### Étape 5: Webhook/Callback
- Réception des notifications de FlexPay
- Validation instantanée du paiement
- Envoi des SMS de confirmation

## 📱 Interface Utilisateur

### Page de Confirmation de Paiement
- Affiche les 3 opérateurs Mobile Money
- Instructions USSD pour chaque opérateur
- Formulaire de numéro de téléphone

### Page de Succès
- Affiche le statut du paiement (INITIE/VALIDE)
- QR codes générés après validation
- Références de transaction
- Instructions pour l'utilisateur

## 🔧 Fonnalités Techniques

### Génération QR Codes
```python
# Les QR codes contiennent:
{
    'ticket_uid': str(ticket.uid),
    'vente_uid': str(ticket.vente.uid),
    'evenement': ticket.evenement_zone.evenement.titre,
    'zone': ticket.evenement_zone.zone_stade.nom,
    'date_evenement': ticket.evenement_zone.evenement.date_evenement.isoformat(),
    'prix': str(ticket.evenement_zone.prix_unitaire),
    'statut': ticket.statut,
    'hash_verification': hash_unique
}
```

### Vérification QR Codes
- URL publique: `/api/billetterie/verifier-qr/{hash}/`
- API REST pour validation instantanée
- Page HTML de vérification

### API Mobile Money
Endpoints disponibles:
- `POST /api/billetterie/initier-paiement/` - Initialiser un paiement
- `GET /api/billetterie/verifier-paiement/{order_number}/` - Vérifier statut
- `POST /api/billetterie/callback/mmo/` - Webhook FlexPay
- `GET /api/billetterie/verifier-qr/{hash}/` - Vérifier QR code
- `GET /api/billetterie/ticket/{uid}/qr/` - Obtenir image QR

## 🛡️ Sécurité

### Tokens et Clés
- Token FlexPay stocké en variable d'environnement
- Hash SHA-256 pour vérification QR codes
- Validation des montants avant confirmation

### Validation Paiement
- Vérification du montant payé vs montant attendu
- Double vérification (callback + polling)
- Logs complets pour audit

## 📊 Monitoring et Logs

### Logs Mobile Money
- Fichier: `logs/mobile_money.log`
- Niveaux: INFO, WARNING, ERROR
- Contenu: Requêtes API, réponses, erreurs

### Statistiques
- API: `/api/billetterie/statistiques/`
- Métriques: Total ventes, recettes, statut paiements, opérateurs

## 🧪 Tests

### Test Local
```bash
# Démarrer le serveur
python manage.py runserver

# Tester le flux complet:
# 1. Acheter un billet
# 2. Choisir Mobile Money
# 3. Vérifier les logs
# 4. Simuler callback
```

### Test Production
- Utiliser les URLs de production FlexPay
- Configurer les callbacks HTTPS
- Tester avec vrais numéros Mobile Money

## 🔧 Dépannage

### Problèmes Communs

1. **Token FlexPay invalide**
   - Vérifier la variable `FLEXPAY_BEARER_TOKEN`
   - Regénérer le token depuis FlexPay

2. **QR codes non générés**
   - Vérifier les permissions dossier `media/`
   - Installer `Pillow` et `qrcode`

3. **Callback non reçu**
   - Vérifier que `SITE_URL` est accessible
   - Configurer HTTPS en production

4. **Paiement en attente**
   - Vérifier les logs pour erreurs
   - Confirmer le statut via API FlexPay

### Logs Utiles
```bash
# Voir les logs Mobile Money
tail -f logs/mobile_money.log

# Vérifier les erreurs Django
python manage.py check
```

## 📈 Évolutions Possibles

1. **Notifications SMS** - Intégration avec opérateurs SMS
2. **Application Mobile** - App native pour billetterie
3. **Wallet Interne** - Portefeuille virtuel SI-SEP
4. **Promotions** - Codes de réduction et offres spéciales
5. **Abonnements** - Pass saison et abonnements

## 📞 Support

Pour toute question sur l'intégration:
- Documentation FlexPay: https://docs.flexpay.cd
- Support technique SI-SEP Sport RDC
- Logs détaillés dans `logs/mobile_money.log`

---

**Note importante**: Ce système est basé sur l'architecture FlexPay existante et a été adapté pour les besoins spécifiques de la billetterie sportive SI-SEP Sport RDC.
