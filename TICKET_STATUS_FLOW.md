# Flux de Statut des Billets - Système Corrigé

## 🔄 Flux Actuel (CORRIGÉ)

### 1. Initialisation
```
Création des tickets → statut = 'DISPONIBLE'
```

### 2. Processus d'Achat
```
Utilisateur choisit billets
    ↓
Création vente → tickets = 'RESERVE'
    ↓
Paiement initié (FlexPay)
    ↓
Callback FlexPay (paiment validé)
    ↓
tickets = 'VENDU' + SMS envoyé
```

### 3. Utilisation
```
Scan à l'entrée
    ↓
ticket = 'UTILISE'
```

## 📊 Tables de Calcul des Montants

### 1. Table `Vente`
```sql
SELECT SUM(montant_total) 
FROM vente 
WHERE date_vente >= '2026-01-01' 
  AND JSON_EXTRACT(notes, '$.statut_paiement') = 'VALIDE';
```

### 2. Table `Ticket`
```sql
SELECT COUNT(*) 
FROM ticket 
WHERE statut = 'VENDU';
```

### 3. Dashboard Ministre
```python
# Dans gouvernance/views_dashboards.py
recette_totale_annee = 0
for vente in ventes_annee:
    if vente.notes and json.loads(vente.notes).get('statut_paiement') == 'VALIDE':
        recette_totale_annee += float(vente.montant_total)
```

## 🎯 Modifications à Apporter

### 1. Modifier le statut initial
Dans `public/views.py` et `public/views_callbacks.py` :
- Remplacer `statut='VENDU'` par `statut='RESERVE'` lors de l'achat

### 2. Ajouter confirmation SMS
Dans le callback FlexPay :
- Marquer tickets comme 'VENDU' seulement après `statut_paiement == 'VALIDE'`
- Envoyer SMS après cette validation

### 3. Mettre à jour les statistiques
Toutes les requêtes comptent les tickets `VENDU` uniquement

## 🔍 Points Clés

1. **DISPONIBLE** : Ticket créé, pas encore réservé
2. **RESERVE** : Ticket réservé pendant le paiement
3. **VENDU** : Paiement confirmé, SMS envoyé
4. **UTILISE** : Ticket scanné à l'entrée

## 📱 SMS Confirmation
Le SMS est envoyé SEULEMENT quand le ticket passe en statut 'VENDU'
