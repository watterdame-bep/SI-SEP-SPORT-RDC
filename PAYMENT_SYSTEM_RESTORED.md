# Restauration du Système de Paiement - Version Simplifiée

## Problème Identifié

Le système de paiement Mobile Money via FlexPay rencontre des problèmes systématiques :

1. **Timeouts constants** : L'API FlexPay prend plus de 60 secondes pour répondre
2. **Callbacks non reçus** : FlexPay n'envoie pas les callbacks de validation
3. **Order_number jamais enregistré** : À cause des timeouts, le `order_number` n'est jamais sauvegardé
4. **Utilisateurs bloqués** : Les paiements sont validés sur le téléphone mais le système reste en attente

## Solution Implémentée

### 1. Suppression du Threading

**Avant** : Appel asynchrone à FlexPay dans un thread séparé
**Après** : Appel synchrone avec gestion explicite des timeouts

**Avantages** :
- Plus simple à déboguer
- Meilleur contrôle des erreurs
- Pas de problèmes de synchronisation

### 2. Gestion Améliorée des Timeouts

```python
if resultat.get('timeout'):
    # Timeout - garder INITIE et rediriger quand même
    notes_data['timeout_initiation'] = resultat.get('error', 'Timeout')
    vente.notes = json.dumps(notes_data)
    vente.save()
    
    # Rediriger vers la page d'attente même sans order_number
    request.session['vente_uid'] = str(vente.uid)
    request.session['order_number'] = vente.reference_paiement
    return redirect('public:payment_waiting')
```

### 3. Scripts de Validation Manuelle

Créés deux scripts pour valider manuellement les paiements bloqués :

- `fix_payment_auto.py` : Valide un paiement spécifique
- `fix_current_payment.py` : Valide le dernier paiement en cours

**Usage** :
```bash
python fix_current_payment.py
```

## Paiements Validés Manuellement

1. **PAY-60D44BFE315D** : Validé ✅
   - Acheteur: TSHIABULANDA MWELA
   - Montant: 100 CDF
   - 1 ticket généré

2. **PAY-5448045EBF82** : Validé ✅
   - Acheteur: Eraste Butela
   - Montant: 100 CDF
   - 1 ticket généré

## Recommandations Urgentes

### Court Terme (Immédiat)

1. **Contacter FlexPay** pour signaler :
   - Timeouts systématiques (>60s)
   - Callbacks non reçus
   - Demander des logs de leur côté

2. **Validation manuelle** :
   - Créer un dashboard admin pour voir les paiements en attente
   - Permettre la validation manuelle par un administrateur
   - Envoyer les SMS/emails après validation manuelle

3. **Monitoring** :
   - Logger tous les appels FlexPay avec timestamps
   - Alerter l'équipe technique en cas de timeout
   - Créer un rapport quotidien des paiements bloqués

### Moyen Terme

1. **Système de Retry** :
   - Réessayer l'appel FlexPay 3 fois avec délai exponentiel
   - Vérifier le statut toutes les 30 secondes pendant 5 minutes

2. **Webhook Alternatif** :
   - Implémenter une vérification proactive côté serveur
   - Interroger FlexPay toutes les 10 secondes pour les paiements en attente

3. **Interface Admin** :
   - Dashboard pour voir tous les paiements en attente
   - Bouton "Vérifier auprès de FlexPay"
   - Bouton "Valider manuellement"

### Long Terme

1. **Provider Alternatif** :
   - Évaluer d'autres providers Mobile Money (Monetbil, etc.)
   - Implémenter un système multi-provider avec fallback

2. **Mode Dégradé** :
   - Permettre les paiements "à la caisse" avec validation manuelle
   - Système de réservation avec paiement différé

3. **Tests de Charge** :
   - Tester la performance de FlexPay en conditions réelles
   - Négocier un SLA avec FlexPay

## Workflow Actuel (Simplifié)

```
1. Utilisateur clique "Confirmer paiement"
2. ⏳ Appel synchrone à FlexPay (60s timeout)
3. ⚠️  Si timeout → Redirection vers page d'attente quand même
4. 📱 Utilisateur valide sur téléphone
5. ❌ Callback FlexPay non reçu (problème FlexPay)
6. 🔧 Admin valide manuellement avec script
7. ✅ Utilisateur recharge la page → Voit ses billets
```

## Workflow Idéal (À Implémenter)

```
1. Utilisateur clique "Confirmer paiement"
2. ⏳ Appel à FlexPay avec retry (3 tentatives)
3. ✅ Order_number reçu et enregistré
4. 📱 Utilisateur valide sur téléphone
5. 🔔 Callback FlexPay reçu → Validation automatique
6. ✅ Redirection automatique vers page de succès
7. 📧 SMS/Email envoyé avec les billets
```

## Actions Immédiates Requises

1. ✅ Valider les paiements bloqués (fait)
2. ⏳ Contacter FlexPay pour signaler les problèmes
3. ⏳ Créer un dashboard admin pour la validation manuelle
4. ⏳ Implémenter un système de notification pour les paiements bloqués
5. ⏳ Documenter la procédure de validation manuelle pour l'équipe

## Fichiers Modifiés

- `public/views.py` : Suppression du threading, appel synchrone
- `fix_payment_auto.py` : Script de validation manuelle (nouveau)
- `fix_current_payment.py` : Script de validation du paiement actuel (nouveau)

## Notes Importantes

⚠️  **Le système actuel nécessite une intervention manuelle pour chaque paiement**

Tant que FlexPay ne fonctionne pas correctement, chaque paiement devra être validé manuellement avec le script `fix_current_payment.py`.

**Procédure de validation manuelle** :
1. L'utilisateur signale que son paiement est bloqué
2. Vérifier que l'argent a bien été débité
3. Exécuter `python fix_current_payment.py`
4. Demander à l'utilisateur de recharger la page

Cette situation n'est pas viable en production. Il faut absolument :
- Résoudre les problèmes avec FlexPay
- OU changer de provider Mobile Money
- OU implémenter un système de validation manuelle dans l'interface admin
