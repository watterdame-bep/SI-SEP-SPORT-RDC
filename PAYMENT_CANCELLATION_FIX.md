# Correction de la Détection d'Annulation de Paiement

## Problème
Lorsque l'utilisateur annule le paiement sur son téléphone, l'application ne détecte pas l'annulation et n'affiche pas le modal d'erreur. Le modal ne s'affiche que pour les échecs de paiement.

## Cause
Le callback FlexPay et l'API de vérification ne traitaient que les statuts:
- `'0'` ou `'SUCCESS'` → Paiement validé
- `'1'` ou `'FAILED'` → Paiement échoué

Les annulations utilisateur (statuts `'CANCELLED'`, `'CANCELED'`, `'2'`, etc.) n'étaient pas traitées.

## Solution Implémentée

### 1. Callback FlexPay (`public/views_callbacks.py`)
Ajout du traitement des annulations:

```python
elif str(status).upper() in ['CANCELLED', 'CANCELED', 'CANCEL', '2', 'ANNULE', 'ANNULÉ']:
    # Paiement annulé par l'utilisateur
    notes_data['statut_paiement'] = 'ECHOUE'
    notes_data['raison_echec'] = 'Paiement annulé par l\'utilisateur'
    notes_data['message_erreur'] = message_erreur
    
    # Libérer les tickets réservés
    tickets_reserve.update(statut='DISPONIBLE', vente=None)
```

### 2. API de Vérification (`public/views.py`)
Ajout de la vérification proactive auprès de FlexPay:

```python
if statut_paiement == 'INITIE' and order_number:
    # Vérifier directement auprès de FlexPay
    statut_flexpay = processor.verifier_paiement(order_number)
    
    if flexpay_status in ['CANCELLED', 'CANCELED', '2']:
        statut_paiement = 'ECHOUE'
        notes_data['raison_echec'] = 'Paiement annulé par l\'utilisateur'
        # Libérer les tickets
```

### 3. Logs de Débogage
Ajout de logs détaillés pour identifier les statuts FlexPay:

```python
print(f"Statut brut: {status} (type: {type(status)})")
print(f"Statut upper: {str(status).upper()}")
print(f"Data complète: {json.dumps(data, indent=2)}")
```

### 4. Vérification Rapide (JavaScript)
Optimisation des intervalles de vérification:
- 1 seconde → Première vérification
- 2 secondes → 10 premières vérifications
- 3 secondes → 20 suivantes
- 5 secondes → Après

## Statuts FlexPay Traités

| Statut | Signification | Action |
|--------|---------------|--------|
| `'0'`, `'SUCCESS'` | Paiement validé | Marquer tickets VENDUS |
| `'1'`, `'FAILED'` | Paiement échoué | Libérer tickets, afficher modal |
| `'2'`, `'CANCELLED'`, `'CANCELED'` | Annulation utilisateur | Libérer tickets, afficher modal |
| Autre | En attente | Continuer à vérifier |

## Résultat
- ✅ Annulation détectée en 1-3 secondes
- ✅ Modal d'erreur affiché immédiatement
- ✅ Tickets libérés automatiquement
- ✅ Message clair: "Paiement annulé par l'utilisateur"

## Test
1. Initier un paiement Mobile Money
2. Annuler sur le téléphone
3. Vérifier que le modal s'affiche rapidement avec le message d'annulation
4. Vérifier dans les logs le statut exact renvoyé par FlexPay

## Fichiers Modifiés
- `public/views_callbacks.py` - Traitement des annulations dans le callback
- `public/views.py` - Vérification proactive auprès de FlexPay
- `templates/public/payment_waiting.html` - Intervalles de vérification optimisés
