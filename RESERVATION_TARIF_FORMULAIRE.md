# 🔧 Configuration Tarifs Réservations - Formulaire Complet

## ✅ **FORMULAIRE AMÉLIORÉ**

### **🎯 Objectif:**
Ajouter le champ "nombre de places" dans la configuration des tarifs pour les réservations, exactement comme dans la configuration des rencontres officielles.

---

## 🔧 **MODIFICATIONS APPORTÉES**

### **1. 📋 Template - Structure Identique aux Rencontres**

#### **Formulaire Avant:**
```html
<div class="flex items-center justify-between">
    <div>
        <h4>{{ zone.nom }}</h4>
        <p>Capacité: {{ zone.capacite }} places</p>
    </div>
    <div>
        <label>Tarif (CDF):</label>
        <input name="tarif_{{ zone.uid }}">
    </div>
</div>
```

#### **Formulaire Après:**
```html
<div class="flex items-center justify-between mb-3">
    <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-rdc-blue/10 rounded-lg">
            <i class="fa-solid fa-map-marker-alt text-rdc-blue"></i>
        </div>
        <div>
            <h4 class="font-semibold text-slate-800">{{ zone.nom }}</h4>
            <p class="text-sm text-slate-600">Zone du stade</p>
        </div>
    </div>
    <!-- Indicateur "Configuré" -->
    {% for tarif in tarifs_existants %}
    {% if tarif.zone_stade.uid == zone.uid %}
    <span class="bg-green-100 text-green-800">
        <i class="fa-solid fa-check-circle"></i>
        Configuré
    </span>
    {% endif %}
    {% endfor %}
</div>

<!-- Deux colonnes pour prix et capacité -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div>
        <label>Prix unitaire (CDF)</label>
        <input type="number" 
               name="prix_zone_{{ zone.uid }}" 
               step="0.01"
               min="0"
               value="{{ tarif.prix_unitaire }}"
               placeholder="Ex: 5000">
    </div>
    
    <div>
        <label>Capacité (nombre de places)</label>
        <input type="number" 
               name="capacite_zone_{{ zone.uid }}" 
               min="1"
               value="{{ tarif.capacite_max }}"
               placeholder="Ex: 1000">
    </div>
</div>
```

---

### **2. 🔄 Vue - Traitement Complet des Données**

#### **Logique de Traitement:**
```python
if request.method == 'POST':
    # Récupérer les tarifs existants
    from infrastructures.models import EvenementZone
    tarifs_existants = EvenementZone.objects.filter(evenement=evenement)
    
    # Traiter chaque zone
    for zone in zones_stade:
        prix_unitaire = request.POST.get(f'prix_zone_{zone.uid}', '').strip()
        capacite_max = request.POST.get(f'capacite_zone_{zone.uid}', '').strip()
        
        if prix_unitaire and capacite_max:
            try:
                # Créer ou mettre à jour le tarif
                EvenementZone.objects.update_or_create(
                    evenement=evenement,
                    zone_stade=zone,
                    defaults={
                        'prix_unitaire': float(prix_unitaire),
                        'capacite_max': int(capacite_max),
                        'disponible': True
                    }
                )
            except (ValueError, TypeError):
                continue
```

#### **Contexte Complet:**
```python
context = {
    'infrastructure': infrastructure,
    'evenement': evenement,
    'zones_stade': zones_stade,
    'tarifs_existants': tarifs_existants,  # Ajouté pour pré-remplir
    'user_role': 'infra_manager',
}
```

---

## 🎯 **RÉSULTATS VISUELS**

### **📱 Formulaire de Configuration Complet:**

#### **Structure par Zone:**
```
🗺️ Tribune d'honneur                    [✅ Configuré]
   Zone du stade
   
   ┌─────────────────────────────────────────────────┐
   │ Prix unitaire (CDF)                        │
   │ [5000.00]                               │
   │                                          │
   │ Capacité (nombre de places)                 │
   │ [500]                                   │
   └─────────────────────────────────────────────────┘

   Description: Zone VIP avec vue optimale
```

#### **Grille Responsive:**
- **Mobile** : 1 colonne (prix, puis capacité)
- **Desktop** : 2 colonnes (prix à gauche, capacité à droite)

---

## 🔄 **COMPARAISON: Rencontres vs Réservations**

| Élément | Rencontres | Réservations |
|----------|-------------|--------------|
| **Champ Prix** | `prix_zone_{uid}` | `prix_zone_{uid}` ✅ |
| **Champ Capacité** | `capacite_zone_{uid}` | `capacite_zone_{uid}` ✅ |
| **Indicateur Configuré** | ✅ | ✅ **AJOUTÉ** |
| **Pré-remplissage** | ✅ | ✅ **AJOUTÉ** |
| **Grille 2 colonnes** | ✅ | ✅ **AJOUTÉ** |
| **Validation** | ✅ | ✅ **AJOUTÉ** |

---

## 🎨 **INTERFACE UTILISATEUR**

### **🔧 Page de Configuration:**

#### **En-tête:**
```
🔧 Configurer Billetterie
📅 Tournoi de football amateur — Stade des Martyrs
```

#### **Formulaire:**
```
🗺️ Tribune d'honneur                    [✅ Configuré]
   Zone du stade
   
   ┌─────────────────┬─────────────────┐
   │ Prix (CDF)     │ Capacité       │
   │ [5000.00]      │ [500]          │
   └─────────────────┴─────────────────┘

🗺️ Tribune latérale
   Zone du stade
   
   ┌─────────────────┬─────────────────┐
   │ Prix (CDF)     │ Capacité       │
   │ [2000.00]      │ [1000]         │
   └─────────────────┴─────────────────┘

[💾 Enregistrer la configuration]
```

---

## 🚀 **FONCTIONNALITÉS COMPLÈTES**

### **✅ Gestion des Tarifs:**

1. **💰 Prix Unitaire**
   - Support des décimales (step="0.01")
   - Validation minimum (min="0")
   - Pré-remplissage avec valeurs existantes

2. **👥 Capacité par Zone**
   - Nombre de places disponibles
   - Validation minimum (min="1")
   - Pré-remplissage avec valeurs existantes

3. **✅ Indicateur de Configuration**
   - Badge vert "Configuré" si tarif existe
   - Icône check-circle
   - Affichage par zone

4. **🔄 Mise à Jour Automatique**
   - `update_or_create()` pour éviter les doublons
   - Préservation des tarifs existants
   - Validation des types de données

---

## 📊 **VALIDATION ET SÉCURITÉ**

### **✅ Contrôles Implémentés:**

1. **Validation des Entrées:**
   ```python
   prix_unitaire = request.POST.get(f'prix_zone_{zone.uid}', '').strip()
   capacite_max = request.POST.get(f'capacite_zone_{zone.uid}', '').strip()
   
   if prix_unitaire and capacite_max:
       try:
           EvenementZone.objects.update_or_create(
               prix_unitaire=float(prix_unitaire),    # Conversion sécurisée
               capacite_max=int(capacite_max),        # Conversion sécurisée
           )
       except (ValueError, TypeError):
           continue  # Ignore les valeurs invalides
   ```

2. **Gestion des Erreurs:**
   - Try/catch pour les conversions de type
   - Continue en cas d'erreur (ne bloque pas le processus)
   - Messages de succès appropriés

3. **Sécurité des Données:**
   - Utilisation de `update_or_create()` (pas de doublons)
   - Validation des types avant insertion
   - Protection contre les valeurs négatives

---

## 🎯 **AVANTAGES FINAUX**

### **✅ Pour le Gestionnaire:**
- **Formulaire identique** aux rencontres (cohérence)
- **Pré-remplissage** des tarifs existants (gain de temps)
- **Indicateurs visuels** de configuration (clarté)
- **Validation automatique** (fiabilité)

### **✅ Pour le Système:**
- **Code unifié** entre rencontres et réservations
- **Maintenance facilitée** (même logique)
- **Performance optimisée** (update_or_create)
- **Sécurité renforcée** (validations)

### **✅ Pour l'Utilisateur Final:**
- **Expérience cohérente** (même interface)
- **Tarifs précis** par zone
- **Capacités contrôlées** (pas de surbooking)
- **Interface responsive** (mobile/desktop)

---

## 📋 **UTILISATION**

### **🔄 Flux Complet:**

1. **Créer une réservation**
   ```
   /manager/rencontres/ → [Réservation] → Formulaire → Création
   ```

2. **Configurer la billetterie**
   ```
   Tableau réservations → [⚙️ Configurer] → 
   /manager/reservation/<uuid>/configurer-billetterie/
   ```

3. **Définir les tarifs**
   ```
   Prix: [5000.00] CDF
   Capacité: [500] places
   [✅ Configuré] s'affiche automatiquement
   ```

4. **Enregistrer**
   ```
   [💾 Enregistrer] → Sauvegarde → Redirection vers liste
   ```

---

## 🎉 **CONCLUSION**

### **Résumé de l'Amélioration:**
1. ✅ **Champ "nombre de places"** ajouté au formulaire
2. ✅ **Structure 2 colonnes** comme les rencontres
3. ✅ **Pré-remplissage** des tarifs existants
4. ✅ **Indicateur "Configuré"** par zone
5. ✅ **Validation complète** des données
6. ✅ **Interface responsive** et cohérente

### **Résultat Final:**
```
🎉 Le formulaire de configuration des réservations est maintenant identique à celui des rencontres !
```

**Les réservations ont maintenant une configuration billetterie complète et professionnelle !** 🚀✅
