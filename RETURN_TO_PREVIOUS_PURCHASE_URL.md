# Retour vers l'URL d'Achat Précédente

## 🎯 Objectif
Permettre à l'utilisateur de retourner exactement à la page d'achat où il se trouvait avant de commencer le processus de paiement.

## 🔄 Fonctionnement

### 1. Stockage de l'URL d'Origine
```
Page d'achat → Stockage URL dans session → Page confirmation
```

### 2. Échec de Paiement
```
Détection échec → Modal → Bouton "Retour à l'achat"
```

### 3. Retour Intelligent
```
Nettoyage session → Récupération URL → Redirection exacte
```

## 🛠️ Implémentation Technique

### Étape 1: Stockage URL (zone_purchase)
```python
def zone_purchase(request, uid, zone_uid):
    # ... traitement de l'achat ...
    
    # Stocker l'URL de retour pour le cas d'échec de paiement
    request.session['purchase_return_url'] = request.build_absolute_uri()
    
    return redirect('public:payment_confirmation')
```

### Étape 2: API de Nettoyage (clear_payment_session)
```python
def clear_payment_session(request):
    if request.method == 'POST':
        # Récupérer l'URL de retour AVANT de nettoyer
        return_url = request.session.get('purchase_return_url', '/billets/acheter/')
        
        # Nettoyer toutes les données SAUF l'URL de retour
        payment_keys = [
            'vente_uid', 'order_number', 'payment_method',
            'purchase_data', 'payment_pending', 'payment_success'
        ]
        
        for key in payment_keys:
            if key in request.session:
                del request.session[key]
        
        return JsonResponse({
            'success': True,
            'return_url': return_url  # URL préservée
        })
```

### Étape 3: Redirection Intelligente (returnToPurchase)
```javascript
function returnToPurchase() {
    // Nettoyer la session et récupérer l'URL de retour
    fetch('/api/clear-payment-session/', {
        method: 'POST',
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.return_url) {
            // Rediriger vers la page d'achat PRÉCÉDENTE
            window.location.href = data.return_url;
        } else {
            // Fallback: page générale
            window.location.href = '/billets/acheter/';
        }
    });
}
```

## 📋 Exemples Concrets

### Cas 1: Achat depuis Page Match
```
URL d'origine: http://127.0.0.1:8000/match/f9079180-b687-4675-9275-1f6e0e02564b/acheter/

Processus:
1. Utilisateur choisit billets sur cette page
2. URL stockée: "http://127.0.0.1:8000/match/f9079180-b687-4675-9275-1f6e0e02564b/acheter/"
3. Paiement échoue
4. Clique "Retour à l'achat"
5. Redirection vers: "http://127.0.0.1:8000/match/f9079180-b687-4675-9275-1f6e0e02564b/acheter/"
```

### Cas 2: Achat depuis Page Zone Spécifique
```
URL d'origine: http://127.0.0.1:8000/match/f9079180-b687-4675-9275-1f6e0e02564b/zone/abc123/acheter/

Processus:
1. Utilisateur choisit billets sur cette page
2. URL stockée: "http://127.0.0.1:8000/match/f9079180-b687-4675-9275-1f6e0e02564b/zone/abc123/acheter/"
3. Paiement échoue
4. Clique "Retour à l'achat"
5. Redirection vers: "http://127.0.0.1:8000/match/f9079180-b687-4675-9275-1f6e0e02564b/zone/abc123/acheter/"
```

### Cas 3: Pas d'URL Stockée (Fallback)
```
URL d'origine: Non disponible (accès direct)

Processus:
1. Utilisateur arrive sur page de paiement sans URL d'origine
2. Pas de stockage d'URL
3. Paiement échoue
4. Clique "Retour à l'achat"
5. Redirection vers: "/billets/acheter/" (page générale)
```

## 🚀 Avantages

### Pour l'Utilisateur
- ✅ **Retour exact** : Revient précisément où il était
- ✅ **Pas de perte** : Conserve le contexte (match, zone, etc.)
- ✅ **Navigation fluide** : Un seul clic pour revenir
- ✅ **Expérience intuitive** : Comportement attendu par l'utilisateur

### Pour l'Administration
- ✅ **Flexibilité** : Fonctionne avec n'importe quelle URL d'achat
- ✅ **Robustesse** : Fallback si URL non disponible
- ✅ **Session propre** : Nettoyage approprié des données
- ✅ **Debug facile** : URL visible dans les logs

## 🔄 Flux Complet

### Scénario Idéal
```
1. Page d'achat spécifique
   ↓
2. Choix des billets
   ↓
3. Page de confirmation
   ↓
4. Paiement échoue
   ↓
5. Modal d'échec
   ↓
6. Clique "Retour à l'achat"
   ↓
7. Retour EXACT à la page d'origine
```

## 🎯 Résultat Final

L'utilisateur qui subit un échec de paiement et clique sur "Retour à l'achat" :

1. **Retourne exactement** à la page où il était ✅
2. **Avec toutes les données** préservées (match, zone, etc.) ✅
3. **Sans perdre le contexte** de sa navigation ✅
4. **Peut immédiatement** refaire sa sélection ✅

**Retour intelligent et contextuel !** 🎯🔙✨
