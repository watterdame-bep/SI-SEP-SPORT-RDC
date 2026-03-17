# 🎫 Système Corrigé de Statut des Billets

## 🔄 NOUVEAU FLUX DE STATUT

### 1. Cycle de Vie Complet d'un Billet
```
DISPONIBLE → RESERVE → VENDU → UTILISE
     ↓           ↓        ↓       ↓
   Création    Achat   Paiement  Scan
```

### 2. Description des Statuts

#### **DISPONIBLE**
- **Quand** : Ticket créé, disponible à l'achat
- **Action** : Peut être réservé
- **Visible** : Oui, dans les places disponibles

#### **RESERVE** ⭐ **NOUVEAU**
- **Quand** : Utilisateur choisit le billet, paiement initié
- **Action** : En attente de confirmation paiement
- **Visible** : Non, plus dans les places disponibles
- **SMS** : Pas encore envoyé

#### **VENDU**
- **Quand** : Paiement confirmé (callback FlexPay)
- **Action** : SMS envoyé, billet valide
- **Visible** : Non, vendu
- **SMS** : ✅ Envoyé avec lien et numéro

#### **UTILISE**
- **Quand** : Scan à l'entrée du stade
- **Action** : Billet consommé
- **Visible** : Non, utilisé
- **SMS** : Déjà envoyé

#### **ANNULE**
- **Quand** : Paiement échoué ou annulation
- **Action** : Retour au stock (DISPONIBLE)
- **Visible** : Oui, remis en vente

## 📱 CONFIRMATION SMS

### Moment d'Envoi
```
✅ SEULEMENT quand statut passe à 'VENDU'
❌ PAS à 'RESERVE' (attente paiement)
❌ PAS à 'DISPONIBLE' (création)
```

### Message SMS
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

## 📊 CALCUL DES MONTANTS

### Table Principale : `Vente`
```sql
-- Requête pour la recette totale
SELECT 
    SUM(montant_total) as recette_totale,
    COUNT(*) as nombre_ventes
FROM vente 
WHERE date_vente >= '2026-01-01' 
  AND JSON_EXTRACT(notes, '$.statut_paiement') = 'VALIDE';
```

### Table Secondaire : `Ticket`
```sql
-- Requête pour les tickets vendus
SELECT 
    COUNT(*) as tickets_vendus,
    SUM(evenement_zone.prix_unitaire) as montant_tickets
FROM ticket 
WHERE statut = 'VENDU'
GROUP BY evenement_zone;
```

### Code Python (Dashboard Ministre)
```python
# Dans gouvernance/views_dashboards.py
recette_totale_annee = 0
for vente in ventes_annee:
    try:
        if vente.notes:
            notes_data = json.loads(vente.notes)
            statut = notes_data.get('statut_paiement', 'INITIE')
            if statut == 'VALIDE':  # Seulement les paiements confirmés
                recette_totale_annee += float(vente.montant_total)
    except (json.JSONDecodeError, TypeError):
        continue  # Ignorer les ventes invalides
```

## 🔧 Modifications Techniques

### 1. Callback FlexPay (`views_callbacks.py`)
```python
if status == '0' or status == 'SUCCESS':
    # Paiement validé
    notes_data['statut_paiement'] = 'VALIDE'
    vente.notes = json.dumps(notes_data)
    vente.save()
    
    # Marquer les tickets RESERVE → VENDU
    tickets_reserve = Ticket.objects.filter(vente=vente, statut='RESERVE')
    count_updated = tickets_reserve.update(statut='VENDU')
    
    # Envoyer les SMS (maintenant seulement pour VENDU)
    sms_service.envoyer_sms_confirmation_paiement(vente.acheteur_telephone, vente)
```

### 2. Processus d'Achat (`views.py`)
```python
# Avant : ticket.statut = 'VENDU'
# Après : ticket.statut = 'RESERVE'
for ticket in tickets_disponibles:
    ticket.statut = 'RESERVE'  # En attente de paiement
    ticket.vente = vente
    ticket.save()
```

### 3. Modèle Ticket (`models.py`)
```python
statut = models.CharField(
    max_length=20,
    choices=[
        ('DISPONIBLE', 'Disponible'),
        ('RESERVE', 'Réservé (en attente de paiement)'),  # ⭐ NOUVEAU
        ('VENDU', 'Vendu'),
        ('UTILISE', 'Utilisé (scanné à l\'entrée)'),
        ('ANNULE', 'Annulé'),
    ],
    default='DISPONIBLE',
)
```

## 🎯 Avantages du Nouveau Système

### 1. ✅ **Précision des Statistiques**
- **Ventes réelles** : Seuls les paiements confirmés
- **Stock disponible** : Places vraiment disponibles
- **Prévisions fiables** : Basées sur les VENDU, pas les RESERVE

### 2. 📱 **SMS au Bon Moment**
- **Confirmation reçue** → SMS envoyé
- **Paiement en attente** → Pas de SMS
- **Paiement échoué** → Tickets retournés au stock

### 3. 🔄 **Gestion des Stocks**
- **RESERVE** : Bloque la place pendant paiement
- **Échec paiement** : Retour automatique à DISPONIBLE
- **Double réservation** : Évitée par le statut RESERVE

### 4. 🎫 **Expérience Utilisateur**
- **Clarté** : SMS = confirmation de paiement
- **Sécurité** : Pas de billet sans paiement
- **Fiabilité** : Statut exact en temps réel

## 📋 Cas d'Usage

### Cas 1 : Paiement Réussi
```
1. Utilisateur choisit billet
2. Ticket passe DISPONIBLE → RESERVE
3. Paiement Mobile Money initié
4. Callback FlexPay : SUCCESS
5. Ticket passe RESERVE → VENDU
6. SMS envoyé avec lien + numéro
7. Utilisateur reçoit confirmation
```

### Cas 2 : Paiement Échoué
```
1. Utilisateur choisit billet
2. Ticket passe DISPONIBLE → RESERVE
3. Paiement Mobile Money échoue
4. Callback FlexPay : FAILED
5. Ticket passe RESERVE → DISPONIBLE
6. Pas de SMS envoyé
7. Place remise en vente
```

### Cas 3 : Timeout Paiement
```
1. Utilisateur choisit billet
2. Ticket passe DISPONIBLE → RESERVE
3. Paiement timeout (pas de callback)
4. Système détecte l'absence de callback
5. Ticket passe RESERVE → DISPONIBLE (après timeout)
6. Pas de SMS envoyé
7. Place remise en vente
```

## 🔍 Vérification et Monitoring

### 1. Dashboard en Temps Réel
```python
# Tickets par statut
stats = {
    'disponibles': Ticket.objects.filter(statut='DISPONIBLE').count(),
    'reserves': Ticket.objects.filter(statut='RESERVE').count(),
    'vendus': Ticket.objects.filter(statut='VENDU').count(),
    'utilises': Ticket.objects.filter(statut='UTILISE').count(),
}
```

### 2. Alertes
- **RESERVE > 10 minutes** : Vérifier paiement en cours
- **RESERVE sans vente** : Nettoyage automatique
- **VENDU sans SMS** : Renvoi automatique

### 3. Logs
- Chaque changement de statut loggé
- SMS envoyés/échoués tracés
- Performances du système monitorées

## 🎉 Résultat Final

Un système de billetterie **précis et fiable** où :

1. ✅ **Les statistiques sont exactes** (seuls les VENDU comptent)
2. ✅ **Les SMS sont envoyés au bon moment** (confirmation paiement)
3. ✅ **Le stock est géré correctement** (RESERVE bloque, DISPONIBLE libère)
4. ✅ **L'utilisateur reçoit une confirmation claire** (SMS = paiement validé)

**Le système de billets est maintenant cohérent et précis !** 🎫📱✅
