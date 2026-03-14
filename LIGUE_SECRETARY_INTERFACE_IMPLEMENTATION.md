# Interface du Secrétaire de la Ligue Provinciale

**Status**: ✅ FULLY IMPLEMENTED

**Date**: March 4, 2026

---

## Overview

L'interface du Secrétaire de la Ligue Provinciale est le dernier maillon de la chaîne administrative avant le terrain (les clubs). Si la Fédération gère la stratégie nationale, la Ligue gère l'exécution locale.

---

## Architecture

### Vues Implémentées

**Fichier**: `gouvernance/views_ligue_secretary.py`

1. **ligue_secretary_dashboard** - Tableau de bord principal
2. **ligue_clubs_list** - Liste des clubs affiliés
3. **ligue_club_detail** - Détail d'un club
4. **ligue_profile** - Profil de la ligue
5. **ligue_communications** - Messagerie et communications

### Templates Implémentés

1. `templates/gouvernance/ligue_secretary_dashboard.html` - Dashboard
2. `templates/gouvernance/ligue_clubs_list.html` - Liste des clubs
3. `templates/gouvernance/ligue_club_detail.html` - Détail club
4. `templates/gouvernance/ligue_profile.html` - Profil ligue
5. `templates/gouvernance/ligue_communications.html` - Communications

### URLs Configurées

```python
# Secrétaire de Ligue Provinciale
path('ligue/dashboard/', views_ligue_secretary.ligue_secretary_dashboard, name='ligue_secretary_dashboard'),
path('ligue/clubs/', views_ligue_secretary.ligue_clubs_list, name='ligue_clubs_list'),
path('ligue/clubs/<uuid:club_id>/', views_ligue_secretary.ligue_club_detail, name='ligue_club_detail'),
path('ligue/profil/', views_ligue_secretary.ligue_profile, name='ligue_profile'),
path('ligue/communications/', views_ligue_secretary.ligue_communications, name='ligue_communications'),
```

---

## 1. Tableau de Bord (Dashboard)

### URL
`/gouvernance/ligue/dashboard/`

### Contenu

#### Header
- Nom de la ligue
- Province
- Code de la ligue

#### Attestation d'Homologation
- Numéro d'attestation
- Statut (APPROUVEE)
- Date d'approbation
- Date de validité
- Bouton de téléchargement du PDF

#### Statistiques Provinciales (Compteurs)
- **Clubs Affiliés**: Nombre de clubs dans la province
- **Athlètes Licenciés**: Nombre d'athlètes licenciés localement
- **Arbitres & Entraîneurs**: Nombre de certifiés dans la province
- **Disciplines**: Nombre de disciplines pratiquées

#### Disciplines Pratiquées
- Liste des disciplines avec badges

#### Missions Principales
- Affiliation des Clubs (Fiche F09)
- Gestion des Licences Locales
- Organisation des Compétitions Provinciales
- Rapport de Viabilité

#### Outils Rapides
- Bouton: Annuaire des Clubs
- Bouton: Profil de la Ligue
- Bouton: Communications
- Bouton: Mon Profil

---

## 2. Annuaire des Clubs

### URL
`/gouvernance/ligue/clubs/`

### Fonctionnalités

#### Filtrage
- Filtrer par commune/ville
- Dropdown avec liste des communes uniques

#### Affichage
- Carte pour chaque club avec:
  - Nom officiel
  - Sigle
  - Code
  - Email (cliquable)
  - Téléphone
  - Adresse et commune
  - Disciplines pratiquées (badges)
  - Bouton "Voir Détails"

#### Statistiques
- Nombre de clubs trouvés
- Indication du filtre appliqué

---

## 3. Détail d'un Club

### URL
`/gouvernance/ligue/clubs/<club_id>/`

### Contenu

#### Informations Générales
- Nom officiel
- Sigle
- Code
- Type d'institution
- Statut

#### Coordonnées
- Email officiel
- Téléphone
- Adresse complète

#### Disciplines Pratiquées
- Liste des disciplines avec badges

#### Dates Importantes
- Date de création
- Dernière modification

---

## 4. Profil de la Ligue

### URL
`/gouvernance/ligue/profil/`

### Contenu

#### Informations Générales
- Nom officiel
- Sigle
- Code
- Province
- Statut d'activation

#### Coordonnées
- Email officiel
- Téléphone
- Adresse

#### Attestation d'Homologation
- Numéro
- Statut
- Date d'approbation
- Validité
- Téléchargement du PDF

#### Disciplines Pratiquées
- Liste complète avec badges

#### Fédération Parente
- Nom de la fédération
- Sigle
- Email

---

## 5. Communications

### URL
`/gouvernance/ligue/communications/`

### Contenu

#### Chef de Division Provinciale
- Nom complet
- Email (cliquable)
- Téléphone
- Rôle et province

#### Secrétaire de la Fédération
- Fédération
- Email (cliquable)
- Téléphone
- Discipline

#### Directives de Communication
- Rapports de viabilité mensuels
- Demandes d'affiliation
- Problèmes administratifs
- Urgences

#### Modèles de Rapports
- Rapport de Viabilité Mensuel
- Rapport de Compétitions

---

## Redirection Automatique

### Logique de Redirection

Quand un utilisateur avec le rôle `FEDERATION_SECRETARY` se connecte:

```python
if profil.institution and profil.institution.niveau_territorial == 'LIGUE':
    # Secrétaire de Ligue → Dashboard Ligue
    return redirect('gouvernance:ligue_secretary_dashboard')
else:
    # Secrétaire de Fédération → Dashboard Fédération
    return redirect('gouvernance:federation_secretary_dashboard')
```

**Fichier modifié**: `core/views.py` → fonction `home()`

---

## Permissions

### Rôle Requis
- `FEDERATION_SECRETARY` avec institution de type `LIGUE`

### Décorateur
```python
@login_required
@require_role('FEDERATION_SECRETARY')
```

### Vérification Supplémentaire
Chaque vue vérifie que:
1. L'utilisateur a un profil
2. L'institution est une LIGUE
3. L'utilisateur ne voit que les données de sa ligue

---

## Données Affichées

### Isolation des Données
- Le secrétaire ne voit que les données de sa province
- Clubs: Uniquement ceux affiliés à sa ligue
- Disciplines: Uniquement celles de sa ligue
- Contacts: Chef de Division et Secrétaire de Fédération

### Statistiques Dynamiques
- Compteurs calculés en temps réel
- Basés sur les données actuelles de la base de données

---

## Design & Charte Graphique

### Couleurs (RDC Royal)
- **Bleu Royal**: `#0036ca` - Éléments principaux
- **Gris clair**: `#f8f9fa` - Fonds
- **Blanc**: Cartes et conteneurs

### Composants
- Cards avec ombres subtiles
- Badges pour les disciplines
- Icônes Font Awesome
- Boutons cohérents avec la charte

### Responsive
- Layout mobile-friendly
- Grille Bootstrap
- Adaptation des colonnes

---

## Fonctionnalités Futures

### Phase 2
1. **Affiliation des Clubs** (Fiche F09)
   - Formulaire de demande d'affiliation
   - Validation des dossiers
   - Approbation/Rejet

2. **Gestion des Licences**
   - Liste des demandes de licences
   - Validation des athlètes
   - Historique des licences

3. **Compétitions Provinciales**
   - Calendrier des matchs
   - Enregistrement des résultats
   - Classements

4. **Messagerie Intégrée**
   - Chat avec Chef de Division
   - Chat avec Secrétaire de Fédération
   - Historique des messages

5. **Rapports**
   - Génération de rapports de viabilité
   - Export en PDF
   - Envoi automatique

---

## Fichiers Créés

1. `gouvernance/views_ligue_secretary.py` - Vues
2. `templates/gouvernance/ligue_secretary_dashboard.html` - Dashboard
3. `templates/gouvernance/ligue_clubs_list.html` - Liste clubs
4. `templates/gouvernance/ligue_club_detail.html` - Détail club
5. `templates/gouvernance/ligue_profile.html` - Profil ligue
6. `templates/gouvernance/ligue_communications.html` - Communications

## Fichiers Modifiés

1. `gouvernance/urls.py` - Ajout des URLs
2. `core/views.py` - Redirection automatique

---

## Testing Checklist

- ✅ Vues créées et fonctionnelles
- ✅ Templates créés avec design cohérent
- ✅ URLs configurées
- ✅ Redirection automatique implémentée
- ✅ Permissions appliquées
- ✅ Isolation des données
- ✅ Design RDC Royal appliqué
- ⏳ Tester avec un compte secrétaire de ligue

---

## Accès

### Pour Tester
1. Approuver une ligue (crée un compte secrétaire)
2. Se connecter avec le compte du secrétaire
3. Accès automatique au dashboard de la ligue

### URLs Directes
- Dashboard: `/gouvernance/ligue/dashboard/`
- Clubs: `/gouvernance/ligue/clubs/`
- Profil: `/gouvernance/ligue/profil/`
- Communications: `/gouvernance/ligue/communications/`

---

**Implementation Complete**: March 4, 2026
**Status**: Ready for Testing
**Next Phase**: Affiliation des Clubs & Gestion des Licences
