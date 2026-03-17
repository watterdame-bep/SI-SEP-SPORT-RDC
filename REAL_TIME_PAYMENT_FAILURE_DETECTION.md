# Détection en Temps Réel des Échecs de Paiement

## 🎯 Objectif
Permettre à l'utilisateur de savoir immédiatement quand son paiement Mobile Money échoue (solde insuffisant, timeout, etc.) directement depuis l'interface d'attente, sans avoir à attendre.

## 🔄 Fonctionnement Complet

### 1. Initialisation du Paiement
```
Utilisateur → Formulaire → FlexPay API → USSD → Validation téléphone
```

### 2. Page d'Attente Intelligente
```
/payment/attente/ → Vérification toutes les 3 secondes
```

### 3. Détection en Temps Réel
```javascript
// API endpoint: /api/payment/status/
{
  "success": true,
  "status": "SOLDE_INSUFFISANT",
  "reference": "OZZv8gklFJpd243840690816-SISEP-b4b1b0c4-1773646551",
  "reason": "solde_insuffisant",
  "detail": "Solde insuffisant pour cette transaction"
}
```

### 4. Affichage du Modal d'Échec
```
Détection → Modal rouge → Message spécifique → Actions
```

## 📱 Scénarios Gérés

### Scénario 1: Solde Insuffisant
- **Détection**: `status: 'SOLDE_INSUFFISANT'`
- **Message**: "Solde insuffisant. Votre solde Mobile Money est insuffisant..."
- **Actions**: Réessayer / Retour à l'achat

### Scénario 2: Autre Échec
- **Détection**: `status: 'ECHOUE'`
- **Message**: "Échec du paiement. Une erreur est survenue..."
- **Actions**: Réessayer / Retour à l'achat

### Scénario 3: Timeout
- **Détection**: Après 10 minutes (200 vérifications)
- **Message**: "Délai d'attente dépassé. Veuillez réessayer."
- **Actions**: Réessayer / Retour à l'achat

## 🛠️ Architecture Technique

### Frontend (payment_waiting.html)
```javascript
// Vérification principale
function checkPaymentStatus() {
    fetch('/api/payment/status/', {...})
    .then(data => {
        if (data.status === 'SOLDE_INSUFFISANT') {
            showPaymentFailure('solde_insuffisant', data.detail);
        }
    });
}

// Modal d'échec
function showPaymentFailure(reason, detail) {
    // Affiche le modal avec le message approprié
}
```

### Backend (API Endpoint)
```python
# URL: /api/payment/status/
def payment_status_api(request):
    vente = Vente.objects.get(uid=vente_uid)
    notes_data = json.loads(vente.notes)
    statut = notes_data.get('statut_paiement')
    
    return JsonResponse({
        'success': True,
        'status': statut,
        'reason': notes_data.get('raison_echec'),
        'detail': notes_data.get('message_erreur')
    })
```

### Callback FlexPay
```python
# views_callbacks.py
def mobile_money_callback(request):
    if 'solde' in message_erreur.lower():
        notes_data['statut_paiement'] = 'SOLDE_INSUFFISANT'
        notes_data['raison_echec'] = 'Solde insuffisant'
```

## 🎨 Interface Utilisateur

### Modal d'Échec
- **Design**: Rouge/blanc pour alerter
- **Icône**: ❌ `fa-times`
- **Titre**: "Paiement échoué"
- **Message**: Spécifique selon la raison
- **Boutons**: Réessayer / Retour à l'achat

### Messages Spécifiques
```
Solde insuffisant:
"Votre solde Mobile Money est insuffisant pour cette transaction.
Veuillez recharger votre compte et réessayer."

Autre échec:
"Une erreur est survenue lors du traitement de votre paiement.
Veuillez réessayer ou contacter votre opérateur."
```

## 🔄 Flux Complet

### Cas Normal (Succès)
1. Utilisateur valide sur téléphone ✅
2. FlexPay callback `VALIDE`
3. Page d'attente → Redirection vers succès
4. Billets générés et envoyés

### Cas Échec (Solde Insuffisant)
1. Utilisateur valide sur téléphone ❌ (solde insuffisant)
2. FlexPay callback `FAILED` + message "solde insuffisant"
3. Backend met `statut: 'SOLDE_INSUFFISANT'`
4. API `/api/payment/status/` retourne le statut
5. JavaScript détecte l'échec
6. Modal rouge s'affiche immédiatement
7. Utilisateur choisit: Réessayer ou Retour

### Cas Échec (Autre)
1. Utilisateur valide sur téléphone ❌ (autre erreur)
2. FlexPay callback `FAILED` + message d'erreur
3. Backend met `statut: 'ECHOUE'`
4. API détecte l'échec
5. Modal s'affiche avec message générique

## 🚀 Avantages

### Pour l'Utilisateur
- **Feedback immédiat** Plus d'attente inutile
- **Messages clairs** Compréhension du problème
- **Actions rapides** Réessayer ou abandonner
- **Pas de confusion** Savoir exactement ce qui se passe

### Pour l'Administration
- **Meilleure UX** Réduction des abandons
- **Support efficace** Utilisateurs informés
- **Statistiques précises** Suivi des échecs
- **Automatisation** Moins d'interventions manuelles

## 📊 Monitoring

### Logs de Détection
```javascript
console.log('Payment status check:', data.status);
console.log('Failure reason:', reason);
console.log('Failure detail:', detail);
```

### Métriques
- Taux de détection d'échec
- Temps moyen de détection
- Types d'échecs les plus fréquents
- Actions utilisateurs (réessayer vs abandonner)

## 🔧 Tests

### Scénario 1: Solde Insuffisant
```bash
# Simuler un callback avec solde insuffisant
curl -X POST http://127.0.0.1:8000/api/callback/mmo/ \
  -d "status=1&message=Solde insuffisant"
```

### Scénario 2: API Status
```bash
# Tester l'API de statut
curl http://127.0.0.1:8000/api/payment/status/
```

### Scénario 3: Timeout
```javascript
// Simuler un timeout (attendre 10 minutes)
maxChecks = 1; // Force le timeout après 3 secondes
```

## 🎯 Résultat

L'utilisateur sait **immédiatement** si son paiement échoue et peut **agir** sans attendre inutilement.
