# Flux de Réessai de Paiement

## 🎯 Objectif
Lorsqu'un paiement échoue, permettre à l'utilisateur de recommencer un nouvel achat proprement sans être bloqué sur la page de confirmation.

## 🔄 Flux Complet

### 1. Échec de Paiement Détecté
```
Paiement échoué → Modal s'affiche → 2 options disponibles
```

### 2. Option 1: "Nouvel achat" (Réessayer)
```
Bouton "Nouvel achat" → Nettoyage session → Redirection page d'achat
```

### 3. Option 2: "Retour à l'achat"
```
Bouton "Retour à l'achat" → Redirection directe page d'achat
```

## 🛠️ Implémentation Technique

### Frontend (JavaScript)
```javascript
function retryPayment() {
    // Masquer le modal
    const modal = document.getElementById('paymentFailedModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    
    // Nettoyer la session de paiement échoué
    fetch('/api/clear-payment-session/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    }).then(() => {
        // Rediriger vers la page d'achat de billets
        window.location.href = '/billets/acheter/';
    });
}
```

### Backend (API Endpoint)
```python
def clear_payment_session(request):
    """Nettoyer toutes les données de paiement de la session"""
    if request.method == 'POST':
        payment_keys = [
            'vente_uid',
            'order_number', 
            'payment_method',
            'purchase_data',
            'payment_pending',
            'payment_success'
        ]
        
        for key in payment_keys:
            if key in request.session:
                del request.session[key]
        
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': 'Session de paiement nettoyée'
        })
```

## 🎨 Interface Utilisateur

### Modal d'Échec
```
┌─────────────────────────────────────┐
│        ❌ Paiement échoué        │
│                                 │
│  [Message spécifique d'erreur]    │
│                                 │
│  [🔄 Nouvel achat] [🏠 Retour]  │
└─────────────────────────────────────┘
```

### Boutons
- **"Nouvel achat"**: Icône 🔄, Bleu, Nettoie la session
- **"Retour à l'achat"**: Icône 🏠, Gris, Redirection directe

## 📋 Messages Spécifiques

### Solde Insuffisant
```
❌ Paiement échoué

Solde insuffisant
Votre solde Mobile Money est insuffisant pour cette transaction.
Veuillez recharger votre compte et réessayer.

[🔄 Nouvel achat] [🏠 Retour à l'achat]
```

### Autre Erreur
```
❌ Paiement échoué

Échec du paiement
Une erreur est survenue lors du traitement de votre paiement.
Veuillez réessayer ou contacter votre opérateur.

[🔄 Nouvel achat] [🏠 Retour à l'achat]
```

## 🔄 Différence entre les 2 Options

### "Nouvel achat" (Réessayer)
- ✅ Nettoie complètement la session
- ✅ Supprime les données de paiement échoué
- ✅ Permet de commencer un achat neuf
- ✅ Évite les conflits de session

### "Retour à l'achat"
- ✅ Redirection immédiate
- ⚠️ Garde les données en session
- ⚠️ Peut causer des conflits
- ✅ Option rapide si l'utilisateur veut juste quitter

## 🚀 Avantages

### Pour l'Utilisateur
- **Pas de blocage**: Plus besoin de revenir en arrière manuellement
- **Session propre**: Nouvel achat sans données résiduelles
- **Choix clair**: 2 options avec actions différentes
- **Feedback immédiat**: sait exactement ce qui se passe

### Pour l'Administration
- **Sessions propres**: Moins de conflits de données
- **Meilleure UX**: Réduction des abandons
- **Statistiques précises**: Suivi des réessais
- **Débogage facile**: Logs clairs des actions

## 📊 Scénarios d'Usage

### Scénario 1: Solde Insuffisant
1. Utilisateur essaie de payer → Solde insuffisant
2. Modal s'affiche avec message spécifique
3. Utilisateur clique "Nouvel achat"
4. Session nettoyée → Redirection page d'achat
5. Utilisateur peut recharger et réessayer

### Scénario 2: Erreur Réseau
1. Utilisateur essaie de payer → Erreur réseau
2. Modal s'affiche avec message générique
3. Utilisateur clique "Retour à l'achat"
4. Redirection directe page d'achat
5. Utilisateur peut réessayer plus tard

### Scénario 3: Changement d'avis
1. Utilisateur commence un paiement → Change d'avis
2. Ferme la page ou clique "Retour"
3. Retour page d'achat
4. Peut choisir un autre match ou modifier

## 🎯 Résultat Final

L'utilisateur a **le choix** entre:
- **Recommencer proprement** avec nettoyage de session
- **Quitter rapidement** vers la page d'achat

**Plus de blocage** sur les pages de paiement ! 🎉
