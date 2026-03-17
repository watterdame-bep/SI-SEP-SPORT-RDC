# Système Complet de Billets - SI-SEP Sport RDC

## 🎯 Objectif
Permettre aux utilisateurs de visualiser, imprimer et partager leurs billets électroniques avec QR code, et recevoir les informations par SMS.

## 🏗️ Architecture Complète

### 1. Modèle de Données
```python
class Ticket(models.Model):
    uid = UUIDField(primary_key=True)                    # Identifiant unique
    numero_billet = CharField(max_length=12, unique=True) # Numéro visible TKT12345678
    evenement_zone = ForeignKey(EvenementZone)             # Zone et événement
    vente = ForeignKey(Vente)                            # Vente associée
    statut = CharField(choices=[                          # DISPONIBLE, VENDU, UTILISE, ANNULE
        ('DISPONIBLE', 'Disponible'),
        ('VENDU', 'Vendu'),
        ('UTILISE', 'Utilisé (scanné à l\'entrée)'),
        ('ANNULE', 'Annulé'),
    ])
    date_utilisation = DateTimeField(null=True)            # Scan à l'entrée
    date_creation = DateTimeField(auto_now_add=True)       # Date de création
```

### 2. URLs Disponibles
```
/ticket/<uuid>/                    → Vue détaillée d'un billet
/mes-tickets/                      → Liste des billets de l'utilisateur
/ticket/<uuid>/imprimer/           → Version imprimable
```

### 3. Templates
- `ticket_view.html` → Affichage complet avec QR code
- `my_tickets.html` → Liste avec filtres et recherche
- `ticket_print.html` → Version optimisée pour impression
- `ticket_not_found.html` → Page d'erreur 404

## 🎨 Interface Utilisateur

### Page de Billet Détaillé
```
┌─────────────────────────────────────────┐
│  SI-SEP Sport RDC - Billet d'Entrée     │
├─────────────────────────────────────────┤
│  Match: TP Mazembe vs AS Vita Club     │
│  Date: 15/03/2026 15:00                │
│  Lieu: Stade des Martyrs                │
│  Zone: Tribune VIP                      │
│  Prix: 5,000 CDF                       │
│                                         │
│  [QR Code]                             │
│  Numéro: TKT12345678                   │
│                                         │
│  [Voir] [Imprimer] [Partager]           │
└─────────────────────────────────────────┘
```

### Liste des Billets
```
┌─────────────────────────────────────────┐
│  Mes Billets (5)                        │
├─────────────────────────────────────────┤
│  🔍 [Recherche...]  [Filtre] [Tri]     │
│                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │TKT123456│ │TKT123457│ │TKT123458│    │
│  │Match 1  │ │Match 2  │ │Match 3  │    │
│  │15/03    │ │20/03    │ │25/03    │    │
│  │[Voir][Impr]│ │[Voir][Impr]│ │[Voir][Impr]│    │
│  └─────────┘ └─────────┘ └─────────┘    │
└─────────────────────────────────────────┘
```

## 📱 Système SMS

### Message SMS pour 1 Billet
```
SI-SEP Sport RDC - BILLET VALIDÉ

Match: TP Mazembe vs AS Vita Club
Date: 15/03/2026 15:00
Lieu: Stade des Martyrs
Zone: Tribune VIP
Prix: 5,000 CDF

N° Billet: TKT12345678
Lien: https://sisep-rdc.cd/ticket/uuid/

Presentez ce N° ou scannez le QR code à l'entrée.
Merci pour votre achat!
```

### Message SMS pour Plusieurs Billets
```
SI-SEP Sport RDC - BILLETS VALIDÉS (3)

Match: TP Mazembe vs AS Vita Club
Date: 15/03/2026 15:00
Lieu: Stade des Martyrs
Zone: Tribune VIP
Total: 15,000 CDF

N° Billets: TKT12345678, TKT12345679, TKT12345680

Consultez vos billets complets sur notre site.
Presentez ces N° à l'entrée.
Merci pour votre achat!
```

## 🔧 Fonctionnalités Techniques

### 1. Génération QR Code
```python
def generer_qr_code(self):
    qr_data = {
        'ticket_uid': str(self.uid),
        'numero_billet': self.numero_billet,
        'evenement': self.evenement_zone.evenement.nom,
        'date_evenement': self.evenement_zone.evenement.date_evenement,
        'zone': self.evenement_zone.zone_stade.nom,
        'stade': self.evenement_zone.evenement.stade.nom
    }
    # Génère l'image QR code en base64
```

### 2. Génération Numéro Billet
```python
def generer_numero_billet(self):
    # Format: TKT + 8 chiffres aléatoires
    # Exemple: TKT12345678
    numero = 'TKT' + ''.join(random.choices(string.digits, k=8))
    return numero
```

### 3. Service SMS
```python
class SMSService:
    def envoyer_billet_sms(self, telephone, ticket):
        # Envoie SMS avec lien et numéro de billet
        
    def envoyer_plusieurs_billets_sms(self, telephone, tickets):
        # Gère plusieurs billets dans un seul SMS
```

## 🔄 Flux Complet

### 1. Processus d'Achat
```
1. Utilisateur choisit billets
2. Paiement validé → Callback FlexPay
3. Création des tickets avec numéros uniques
4. Génération QR codes
5. Envoi SMS automatique
6. Redirection vers page de succès
```

### 2. Visualisation
```
1. SMS reçu avec lien
2. Clique sur lien → Page détaillée du billet
3. QR code visible et scannable
4. Options: Imprimer, Partager, Retour liste
```

### 3. Vérification à l'Entrée
```
1. Scan QR code → Vérification instantanée
2. OU saisie manuelle numéro TKT12345678
3. Validation du statut (VENDU/UTILISÉ)
4. Marquage comme UTILISÉ si valide
```

## 🎯 Cas d'Usage

### Cas 1: Utilisateur avec Smartphone
```
1. Reçoit SMS avec lien
2. Clique sur lien
3. Affiche billet avec QR code
4. Présente QR code à l'entrée
5. Scan → Validation réussie
```

### Cas 2: Utilisateur sans Smartphone
```
1. Reçoit SMS avec numéro TKT12345678
2. Note le numéro sur papier
3. Présente numéro à l'entrée
4. Saisie manuelle → Validation
```

### Cas 3: Plusieurs Billets
```
1. Achète 3 billets pour amis/famille
2. Reçoit SMS avec 3 numéros
3. Partage les numéros avec chaque personne
4. Chaque personne présente son numéro
```

## 📊 Statistiques et Monitoring

### Métriques Disponibles
- Nombre total de billets générés
- Billets utilisés vs non utilisés
- Taux de conversion (achats → utilisations)
- Événements les plus populaires
- Zones les plus demandées

### Logs de Sécurité
- Tentatives de scan invalides
- Billets utilisés plusieurs fois (fraude)
- Erreurs de validation
- SMS non délivrés

## 🔒 Sécurité et Anti-Fraude

### 1. Unicité
- Chaque billet a un UUID unique
- Numéro de billet unique (TKTxxxxxxxx)
- QR code contient toutes les données de validation

### 2. Validation
- Statut tracké: DISPONIBLE → VENDU → UTILISÉ
- Date/heure d'utilisation enregistrée
- Impossible d'utiliser un billet déjà scanné

### 3. Vérification
- QR code scanneable avec données cryptées
- Numéro manuel vérifiable en base de données
- Double validation possible (QR + numéro)

## 🚀 Avantages

### Pour l'Utilisateur
- ✅ **Accès instantané** via SMS
- ✅ **Pas de papier** nécessaire (optionnel)
- ✅ **Partage facile** avec amis/famille
- ✅ **Vérification simple** (QR ou numéro)
- ✅ **Historique complet** des billets

### Pour l'Administration
- ✅ **Anti-fraude** robuste
- ✅ **Suivi en temps réel**
- ✅ **Statistiques détaillées**
- ✅ **Coût réduit** (pas d'impression systématique)
- ✅ **Écologie** (moins de papier)

### Pour le Stade
- ✅ **Entrée rapide** (scan QR)
- ✅ **Validation fiable**
- ✅ **Pas de files d'attente**
- ✅ **Contrôle total** des accès

## 📋 Configuration Requise

### 1. Dépendances Python
```bash
pip install qrcode[pil] requests django
```

### 2. Settings Django
```python
# SMS Configuration
SMS_API_URL = 'https://api.sms-service.com/send'
SMS_API_KEY = 'your_api_key'
SMS_SENDER_NAME = 'SISEPRDC'

# Site Configuration
SITE_URL = 'https://sisep-rdc.cd'
```

### 3. Migration Base de Données
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🎯 Résultat Final

Un système complet de billetterie électronique qui permet:

1. **Achat en ligne** → Paiement → Billets générés
2. **SMS automatique** → Lien + numéro de billet
3. **Visualisation web** → QR code + détails
4. **Impression optionnelle** → Version papier
5. **Validation à l'entrée** → Scan ou saisie manuelle
6. **Anti-fraude** → Suivi complet et sécurisé

**Solution moderne, écologique et sécurisée pour la billetterie sportive !** 🎉🎫📱
