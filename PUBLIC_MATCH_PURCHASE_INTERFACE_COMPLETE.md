# Interface d'Achat de Billets - Style FC Barcelona (Complète)

## Résumé
Interface professionnelle d'achat de billets inspirée du site FC Barcelona, adaptée à la charte graphique RDC (Bleu #0036ca, Jaune #FDE015, Rouge #ED1C24).

## Fichiers Créés/Modifiés

### Template Principal
- **`templates/public/match_purchase.html`** - Interface complète d'achat de billets

## Caractéristiques de l'Interface

### 1. Navigation (Navbar)
- **Position**: Fixed en haut de page
- **Comportement au scroll**: 
  - Transparent avec fond bleu au départ
  - Devient blanc avec ombre au scroll
- **Contenu**:
  - Logo RDC + titre SI-SEP SPORT
  - Liens centrés (Matchs, Stars, Actualités)
  - Bouton "Se connecter" ou "Mon Portail" selon l'authentification
- **Responsive**: Menu hamburger sur mobile

### 2. Section Hero (Bannière)
- **Fond**: Dégradé bleu (#0036ca → #002a9e) avec motifs sportifs subtils
  - Ballons de football
  - Étoiles sportives
  - Trophées
  - Médailles
- **Contenu centré**:
  - Titre de la compétition et journée (en jaune)
  - Logos des deux équipes face à face
  - **Countdown timer centré** avec 4 boîtes (Jours, Heures, Minutes, Secondes)
  - Date et lieu du match

### 3. Section Sélection de Billets
- **Titre**: "Choisissez votre tribune"
- **Cartes de zones** (grid responsive):
  - En-tête avec dégradé bleu
  - Prix en grand format
  - Liste des avantages (accès garanti, vue dégagée, billet numérique)
  - Places disponibles affichées
  - Bouton "Sélectionner" en jaune
  - **Effet hover**: Élévation de la carte
  - **État sélectionné**: Bordure bleue + icône check

### 4. Formulaire d'Achat (Affiché après sélection)
- **Informations personnelles**:
  - Nom complet (requis)
  - Téléphone (requis)
  - Email (optionnel)
- **Sélection quantité**:
  - Boutons +/- pour ajuster
  - Affichage du nombre de places disponibles
  - Validation automatique (ne peut pas dépasser le max)
- **Récapitulatif**:
  - Tribune sélectionnée
  - Quantité
  - Total en CDF (calculé dynamiquement)
- **Bouton**: "Procéder au paiement" (bleu)

### 5. Footer
- **Fond**: Gris foncé (#1e293b)
- **Contenu**: 4 colonnes
  - À propos SI-SEP SPORT
  - Liens rapides
  - Contact
  - Réseaux sociaux
- **Copyright**: Centré en bas

## Fonctionnalités JavaScript

### Countdown Timer
```javascript
- Calcul en temps réel jusqu'à la date du match
- Mise à jour chaque seconde
- Affichage "MATCH EN COURS" si la date est passée
```

### Sélection de Billets
```javascript
- Désélection automatique des autres cartes
- Récupération des données (zone, prix, places disponibles)
- Affichage du formulaire avec scroll automatique
- Mise à jour du récapitulatif
```

### Gestion de la Quantité
```javascript
- Incrémentation/décrémentation avec validation
- Ne peut pas dépasser le nombre de places disponibles
- Calcul automatique du total
- Synchronisation avec tous les champs
```

### Navbar Scroll Effect
```javascript
- Détection du scroll (seuil: 50px)
- Transition fluide entre transparent et blanc
- Changement de couleur des liens et du bouton
```

## Design Principles

### Couleurs RDC (Strictement Respectées)
- **Bleu Royal**: `#0036ca` - Navbar, boutons primaires, en-têtes
- **Jaune Drapeau**: `#FDE015` - Accents, boutons d'action
- **Rouge Drapeau**: `#ED1C24` - Champs requis (*)
- **Gris clair**: `#f8f9fa` - Fond de page

### Typographie
- **Police**: Inter (Google Fonts)
- **Poids**: 300 à 900 (emphasis sur 700-900 pour les titres)
- **Style**: UPPERCASE pour les titres et boutons

### Pas de Border-Radius
- Tous les éléments ont `border-radius: 0 !important;`
- Style officiel gouvernemental

### Motifs Sportifs
- Intégrés en SVG dans le CSS
- Opacité très faible (0.03-0.06)
- Positionnement stratégique pour ne pas surcharger

## Workflow Utilisateur

1. **Arrivée sur la page**
   - Voir le match avec countdown
   - Parcourir les zones disponibles

2. **Sélection d'une zone**
   - Cliquer sur une carte de zone
   - La carte se met en surbrillance
   - Le formulaire apparaît en dessous

3. **Remplissage du formulaire**
   - Entrer nom, téléphone, email
   - Ajuster la quantité avec +/-
   - Voir le total se mettre à jour

4. **Validation**
   - Cliquer sur "Procéder au paiement"
   - Redirection vers la page de confirmation de paiement

## Responsive Design

### Desktop (≥768px)
- Grid 3 colonnes pour les cartes de zones
- Navbar avec liens centrés
- Formulaire en 2 colonnes

### Mobile (<768px)
- Grid 1 colonne pour les cartes
- Menu hamburger
- Formulaire en 1 colonne
- Countdown adapté

## Intégration avec le Backend

### Données Reçues du View
```python
context = {
    'rencontre': rencontre,  # Objet Rencontre avec relations
    'zones_disponibles': [
        {
            'zone': 'Tribune d\'honneur',
            'prix_unitaire': 50000,
            'places_disponibles': 150,
            'zone_obj': zone_tarif_object
        },
        ...
    ]
}
```

### Données Envoyées au Backend (POST)
```python
{
    'zone': 'Tribune d\'honneur',
    'quantity': 2,
    'nom': 'Jean Kabongo',
    'telephone': '+243 XXX XXX XXX',
    'email': 'jean@example.com'  # optionnel
}
```

## Améliorations Futures Possibles

1. **Photos des zones**: Ajouter des images réelles des tribunes
2. **Plan du stade**: Vue interactive pour choisir sa place
3. **Paiement en ligne**: Intégration API Mobile Money
4. **Historique d'achats**: Pour les utilisateurs connectés
5. **Notifications SMS**: Confirmation d'achat automatique
6. **QR Code**: Génération et envoi automatique

## Notes Techniques

- Template utilise Tailwind CDN pour le styling
- Font Awesome 6.4.0 pour les icônes
- Compatible avec Django 6.0.3
- Aucune dépendance JavaScript externe (vanilla JS)
- Performance optimisée (pas de librairies lourdes)

## Conformité Charte Graphique

✅ Couleurs RDC strictement respectées
✅ Pas de border-radius
✅ Police Inter avec poids forts
✅ Motifs sportifs subtils
✅ Style officiel gouvernemental
✅ Navbar avec transition au scroll
✅ Footer complet et professionnel

---

**Statut**: ✅ COMPLET ET FONCTIONNEL
**Date**: 14 Mars 2026
**Inspiré de**: FC Barcelona Ticketing Interface
**Adapté pour**: SI-SEP Sport RDC
