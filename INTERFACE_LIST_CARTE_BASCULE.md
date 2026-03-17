# 🗺️ Interface Liste - Carte avec Bascule

## 🎯 **Objectif Atteint**

**Ajouter le bouton de bascule vers la carte dans l'URL `/api/infrastructures/list/`**

---

## 📍 **Localisation de l'Interface**

### **🔗 URL d'Accès:**
```
http://127.0.0.1:8000/api/infrastructures/list/
```

### **📁 Template Modifié:**
```
templates/infrastructures/infrastructure_list.html
```

---

## 🎨 **Modifications Effectuées**

### **🔧 En-tête Amélioré:**
- **Bouton vert** : Lien direct vers `/api/infrastructures/list-with-map/`
- **Bouton jaune** : Bascule locale liste ↔ carte
- **Design cohérent** : Mêmes styles que le reste de l'interface
- **Positionnement** : Après la cloche SG, avant "Nouvelle Infrastructure"

### **🔄 Vue Liste et Carte:**
- **ID ajoutés** : `list-view` et `map-view` pour le JavaScript
- **Vue carte cachée** : `hidden` par défaut
- **Iframe intégré** : Même carte que dashboard ministre
- **Hauteur optimisée** : 800px pour bonne visibilité

---

## 🎯 **Interface Complète**

### **📋 Vue Liste (par défaut):**
```
┌─────────────────────────────────────────────────┐
│  Infrastructures Sportives                        │
│  Vue nationale — Consultation                    │
│                                             │
│  🔔  🟢 [Voir la carte]  🟡 [Voir la carte]  ➕   │
│  (SG)   (lien direct)      (bascule)    (créer) │
│                                             │
│  📊 STATISTIQUES                               │
│  🔍 FILTRES ET RECHERCHE                       │
│  📋 TABLEAU DES INFRASTRUCTURES                │
└─────────────────────────────────────────────────────────┘
```

### **🗺️ Vue Carte (basculée):**
```
┌─────────────────────────────────────────────────┐
│  🗺️ CARTOGRAPHIE DES INFRASTRUCTURES SPORTIVES   │
│                                             │
│  🔔  🟢 [Voir la carte]  🟡 [Voir la liste]  ➕   │
│  (SG)   (lien direct)      (bascule)    (créer) │
│                                             │
│  ┌─────────────────────────────────────────────┐   │
│  │                                         │   │
│  │         🗺️ CARTE INTÉGRÉE            │   │
│  │                                         │   │
│  │   📍📍📍📍                           │   │
│  │   📍  📍📍                           │   │
│  │   📍📍📍📍                           │   │
│  │   📍  📍📍                           │   │
│  │   [800px HAUTEUR]                       │   │
│  │                                         │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 **Fonctionnalités Implémentées**

### **✅ Deux Boutons Disponibles:**

#### **🟢 Bouton "Voir la carte" (Lien direct):**
- **Couleur** : Vert (rdc-green)
- **Action** : Navigation vers `/api/infrastructures/list-with-map/`
- **Usage** : Accès direct à l'interface complète
- **Icône** : 🗺️ (fa-solid fa-map)

#### **🟡 Bouton "Voir la carte" (Bascule):**
- **Couleur** : Jaune (rdc-yellow)
- **Action** : Bascule entre liste et carte dans la même page
- **Usage** : Vue rapide sans quitter la page actuelle
- **Icône** : 🗺️ ↔ 📋 selon l'état

### **✅ JavaScript de Bascule:**
```javascript
function toggleView() {
    const listView = document.getElementById('list-view');
    const mapView = document.getElementById('map-view');
    const toggleIcon = document.getElementById('toggle-icon');
    const toggleText = document.getElementById('toggle-text');
    
    if (listView.classList.contains('hidden')) {
        // Afficher la liste
        listView.classList.remove('hidden');
        mapView.classList.add('hidden');
        toggleIcon.className = 'fa-solid fa-map';
        toggleText.textContent = 'Voir la carte';
    } else {
        // Afficher la carte
        listView.classList.add('hidden');
        mapView.classList.remove('hidden');
        toggleIcon.className = 'fa-solid fa-list';
        toggleText.textContent = 'Voir la liste';
    }
}
```

---

## 📝 **Instructions d'Utilisation:**

### **🔗 Accès à l'Interface:**
```
http://127.0.0.1:8000/api/infrastructures/list/
```

### **🗺️ Options pour Voir la Carte:**
- **Option A** : Bouton vert "Voir la carte" → interface complète
- **Option B** : Bouton jaune "Voir la carte" → bascule locale

### **🔄 Utilisation de la Bascule:**
- **Vue liste** : Clic sur bouton jaune "Voir la carte"
- **Vue carte** : Clic sur bouton jaune "Voir la liste"
- **État visible** : Icône et texte indiquent l'action disponible

---

## 🎉 **Résultats Attendus:**

### **✅ Objectif Atteint:**
- **Bouton vert** : Lien direct vers interface complète
- **Bouton jaune** : Bascule locale dans la même page
- **Vue liste** : Tableau avec filtres et recherche
- **Vue carte** : Iframe avec carte intégrée
- **JavaScript** : Fonction toggleView() opérationnelle

### **🎯 Bénéfices:**
- **Flexibilité** : Deux façons d'accéder à la carte
- **Rapidité** : Bascule instantanée sans rechargement
- **Contexte** : Maintien des filtres et recherche
- **Expérience** : Interface intuitive et moderne

---

## 📝 **Conclusion:**

**L'interface `/api/infrastructures/list/` dispose maintenant du bouton de bascule vers la carte !**

- 🗺️ **URL** : `http://127.0.0.1:8000/api/infrastructures/list/`
- 🟢 **Bouton vert** : Lien direct vers interface complète
- 🟡 **Bouton jaune** : Bascule locale liste ↔ carte
- 📋 **Vue liste** : Tableau avec filtres et recherche
- 🗺️ **Vue carte** : Iframe avec points bleus BDD
- 🔄 **JavaScript** : toggleView() intégré

**L'utilisateur dispose maintenant de l'interface complète avec bascule vers la carte dans la bonne URL !** 🗺️✅
