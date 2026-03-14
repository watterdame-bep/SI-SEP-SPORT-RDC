# SI-SEP Sport RDC - Rôles et Permissions Système

## Vue d'ensemble

Le système SI-SEP Sport RDC utilise 8 rôles distincts avec des permissions spécifiques. Chaque rôle a accès à des fonctionnalités et des données différentes selon sa responsabilité dans la hiérarchie sportive congolaise.

---

## 1. SYSTEM_SUPER_ADMIN (Super Admin Développeur)

**Code**: `SYSTEM_SUPER_ADMIN`  
**Désignation**: Super Admin (Développeur)  
**Niveau d'accès**: Système complet  
**Portée des données**: Nationale (toutes les données)

### Permissions

| Permission | Description |
|-----------|-------------|
| **Initialisation du système** | Accès à la page `setup_sisep` pour initialiser le ministère et créer les 3 comptes clés (Ministre, SG, Inspecteur) |
| **Accès complet** | Accès à toutes les fonctionnalités du système sans restriction |
| **Gestion des données** | Peut créer, modifier, supprimer toutes les données du système |

### Vues accessibles

- `core:setup_sisep` - Initialisation du système (formulaire Ministère + 3 comptes)

### Cas d'usage

- Développeur/Administrateur système
- Configuration initiale du SI-SEP
- Maintenance et support technique

---

## 2. INSTITUTION_ADMIN (Secrétaire Général - SG)

**Code**: `INSTITUTION_ADMIN`  
**Désignation**: Admin Institution (Secrétaire Général — gestionnaire de données)  
**Niveau d'accès**: Ministère (institution racine)  
**Portée des données**: Nationale (toutes les fédérations, ligues, clubs)

### Permissions

| Permission | Description |
|-----------|-------------|
| **Gestion administrative** | Enregistrement des fédérations nationales (F03) |
| **Validation des ligues** | Approbation ou rejet des demandes de création de ligues provinciales |
| **Transfert de ligues** | Transfert des ligues validées vers les divisions provinciales |
| **Gestion des agents** | Création, modification, suppression des agents du Cabinet ministériel |
| **Gestion des comptes** | Création de comptes utilisateur pour les agents, activation/désactivation |
| **Gestion des mandats** | Création et gestion des mandats des agents |
| **Paramètres géographiques** | Gestion complète des provinces, territoires, secteurs, groupements |
| **Paramètres des fonctions** | Gestion des fonctions du ministère (ajout, modification, suppression) |
| **Gestion des disciplines** | Création et gestion des disciplines sportives |
| **Inspection** | Consultation des inspections à transférer aux divisions |
| **Profil SG** | Gestion du profil du Secrétaire Général (signature, cachet, documents) |

### Vues accessibles

**Dashboards**
- `gouvernance:sg_dashboard` - Tableau de bord SG avec statistiques nationales

**Gestion administrative**
- `core:gestion_administrative` - Enregistrement des fédérations
- `core:gerer_comptes` - Gestion des comptes (lecture seule)
- `core:parametres_fonctions` - Gestion des fonctions du ministère
- `referentiel_geo:parametres_geographiques` - Gestion des paramètres géographiques

**Gestion des agents**
- `gouvernance:personnel_ministere` - Liste des agents du Cabinet
- `gouvernance:enregistrer_agent` - Enregistrement d'un nouvel agent
- `gouvernance:detail_agent` - Détail d'un agent et gestion des mandats
- `gouvernance:modifier_agent` - Modification des informations d'un agent
- `gouvernance:creer_acces_systeme` - Création d'accès système pour un agent
- `gouvernance:desactiver_compte` - Désactivation d'un compte
- `gouvernance:reactiver_compte` - Réactivation d'un compte
- `gouvernance:creer_mandat` - Création d'un mandat pour un agent

**Gestion des fédérations**
- `gouvernance:federations_nationales` - Liste des fédérations nationales
- `gouvernance:federation_create` - Création d'une fédération
- `gouvernance:federation_detail` - Détail d'une fédération
- `gouvernance:federation_delete` - Suppression d'une fédération

**Gestion des ligues (SG)**
- `gouvernance:sg_ligues_en_attente` - Ligues en attente de validation
- `gouvernance:sg_ligue_detail` - Détail d'une ligue en attente
- `gouvernance:sg_approuver_ligue` - Approbation d'une ligue
- `gouvernance:sg_rejeter_ligue` - Rejet d'une ligue
- `gouvernance:sg_transferer_ligue_division` - Transfert d'une ligue à la division

**Profil**
- `gouvernance:profil_sg` - Profil du Secrétaire Général

### Cas d'usage

- Secrétaire Général du Ministère des Sports
- Gestion centralisée de toutes les fédérations et ligues
- Validation des demandes de création de ligues
- Gestion du personnel du Cabinet ministériel

---

## 3. MINISTRE

**Code**: `MINISTRE`  
**Désignation**: Ministre  
**Niveau d'accès**: Ministère (validation et signature)  
**Portée des données**: Nationale (documents en attente de signature)

### Permissions

| Permission | Description |
|-----------|-------------|
| **Validation des fédérations** | Approbation ou rejet des demandes d'agrément de fédérations |
| **Signature des arrêtés** | Signature des arrêtés de création de fédérations |
| **Gestion des courriers** | Consultation et signature des courriers officiels (parapheur) |
| **Refus de courriers** | Refus de courriers avec justification |
| **Profil Ministre** | Gestion du profil du Ministre (signature, cachet, documents) |

### Vues accessibles

**Dashboards**
- `gouvernance:minister_dashboard` - Tableau de bord Ministre avec validations en attente

**Validation des fédérations**
- `gouvernance:validation_federation_detail` - Détail d'une fédération en attente de validation
- `gouvernance:validation_submit` - Soumission de l'avis technique (validation/rejet)
- `gouvernance:validation_transfer_to_minister` - Transfert de la validation au Ministre

**Gestion des courriers**
- `gouvernance:minister_courriers` - Liste des courriers en attente de signature
- `gouvernance:parapheur_detail` - Détail d'un courrier
- `gouvernance:signer_courrier` - Signature d'un courrier
- `gouvernance:refuser_courrier` - Refus d'un courrier

**Arrêtés**
- `gouvernance:minister_arretes` - Liste des arrêtés en attente de signature
- `gouvernance:verifier_arrete` - Vérification et signature d'un arrêté

**Profil**
- `gouvernance:profil_ministre` - Profil du Ministre

### Cas d'usage

- Ministre des Sports et Loisirs
- Validation finale des fédérations
- Signature des documents officiels (arrêtés, courriers)
- Approbation des décisions administratives

---

## 4. DIRECTEUR_CABINET

**Code**: `DIRECTEUR_CABINET`  
**Désignation**: Directeur de Cabinet  
**Niveau d'accès**: Cabinet ministériel  
**Portée des données**: Documents du Cabinet

### Permissions

*À définir selon les besoins spécifiques du Cabinet*

### Cas d'usage

- Directeur du Cabinet du Ministre
- Gestion administrative du Cabinet

---

## 5. DIRECTEUR_PROVINCIAL (Secrétaire Direction Provinciale)

**Code**: `DIRECTEUR_PROVINCIAL`  
**Désignation**: Directeur (Direction provinciale)  
**Niveau d'accès**: Province administrative  
**Portée des données**: Provinciale (sa province uniquement)

### Permissions

| Permission | Description |
|-----------|-------------|
| **Validation des clubs** | Examen et validation des demandes de création de clubs |
| **Avis technique** | Émission d'avis technique favorable/défavorable sur les clubs |
| **Validation des fédérations** | Examen des demandes d'agrément de fédérations provinciales |
| **Gestion des ligues** | Consultation et validation des ligues provinciales |
| **Gestion des infrastructures** | CRUD complet sur les infrastructures de sa province |
| **Enquêtes de viabilité** | Consultation des enquêtes de viabilité des infrastructures |
| **Filtrage provincial** | Accès limité aux données de sa province uniquement (filtrage serveur) |

### Vues accessibles

**Dashboards**
- `gouvernance:directeur_provincial_dashboard` - Tableau de bord du Directeur Provincial

**Validation des clubs**
- `gouvernance:clubs_en_attente_validation` - Liste des clubs en attente de validation
- `gouvernance:club_validation_detail` - Détail d'un club en attente de validation

**Validation des fédérations**
- `gouvernance:validation_federation_detail` - Détail d'une fédération en attente
- `gouvernance:validation_submit` - Soumission de l'avis technique
- `gouvernance:validation_transfer_to_minister` - Transfert au Ministre

**Gestion des ligues**
- `gouvernance:division_ligue_detail` - Détail d'une ligue en attente
- `gouvernance:division_valider_ligue` - Validation d'une ligue
- `gouvernance:division_rejeter_ligue` - Rejet d'une ligue

**Gestion des infrastructures**
- `infrastructures:infrastructure_list` - Liste des infrastructures de la province
- `infrastructures:infrastructure_create` - Création d'une infrastructure
- `infrastructures:infrastructure_edit` - Modification d'une infrastructure
- `infrastructures:infrastructure_delete` - Suppression d'une infrastructure

**Enquêtes**
- `gouvernance:enquetes_viabilite` - Consultation des enquêtes de viabilité

### Cas d'usage

- Directeur de la Division Provinciale des Sports
- Validation des clubs au niveau provincial
- Émission d'avis techniques sur les demandes d'agrément
- Gestion des infrastructures sportives provinciales
- Validation des ligues provinciales

### Sécurité

- **Filtrage provincial obligatoire**: Toutes les vues vérifient que l'utilisateur accède uniquement aux données de sa province
- **Vérification serveur**: Les permissions sont vérifiées au niveau du serveur, pas du frontend
- **Isolation des données**: Un Directeur Provincial ne peut pas accéder aux données d'une autre province

---

## 6. INSPECTEUR_GENERAL

**Code**: `INSPECTEUR_GENERAL`  
**Désignation**: Inspection générale  
**Niveau d'accès**: Système complet  
**Portée des données**: Nationale (inspection)

### Permissions

*À définir selon les besoins spécifiques de l'Inspection Générale*

### Cas d'usage

- Inspecteur Général du Ministère
- Inspection et audit des institutions sportives

---

## 7. FEDERATION_SECRETARY (Secrétaire de Fédération / Ligue Provinciale)

**Code**: `FEDERATION_SECRETARY`  
**Désignation**: Secrétaire de Fédération  
**Niveau d'accès**: Fédération ou Ligue Provinciale  
**Portée des données**: Institutionnelle (sa fédération/ligue uniquement)

### Permissions

#### Pour Secrétaire de Fédération Nationale

| Permission | Description |
|-----------|-------------|
| **Gestion des clubs** | Consultation de la liste des clubs affiliés |
| **Gestion des ligues** | Consultation de la liste des ligues provinciales |
| **Gestion des documents** | Gestion des documents officiels de la fédération |
| **Gestion des athlètes** | Consultation de la liste des athlètes |
| **Gestion des compétitions** | Gestion du calendrier des compétitions |
| **Ordres de mission** | Gestion des ordres de mission |
| **Profil fédération** | Gestion du profil de la fédération |

#### Pour Secrétaire de Ligue Provinciale

| Permission | Description |
|-----------|-------------|
| **Création de clubs** | Création de clubs affiliés à la ligue (F07) |
| **Affiliation de clubs** | Affiliation des clubs à la ligue (génération d'Acte d'Affiliation) |
| **Gestion des clubs** | Consultation et gestion des clubs affiliés |
| **Gestion des documents** | Gestion des documents officiels de la ligue |
| **Gestion des communications** | Gestion des communications officielles |
| **Profil ligue** | Gestion du profil de la ligue (signature, cachet, documents) |
| **Renvoi d'emails** | Renvoi des emails d'activation aux clubs |

### Vues accessibles

**Dashboards**
- `gouvernance:ligue_secretary_dashboard` - Tableau de bord du Secrétaire de Ligue
- `gouvernance:federation_secretary_dashboard` - Tableau de bord du Secrétaire de Fédération

**Gestion des clubs (Ligue)**
- `gouvernance:ligue_clubs_affiliation` - Liste des clubs en attente d'affiliation
- `gouvernance:ligue_club_detail` - Détail d'un club
- `gouvernance:ligue_club_create_step1` - Création d'un club - Étape 1 (Identité)
- `gouvernance:ligue_club_create_step2` - Création d'un club - Étape 2 (Adresse)
- `gouvernance:ligue_club_create_step3` - Création d'un club - Étape 3 (Confirmation)
- `gouvernance:ligue_club_affiliate` - Affiliation d'un club (génération PDF)
- `gouvernance:ligue_club_resend_activation` - Renvoi de l'email d'activation

**Gestion des clubs (Fédération)**
- `gouvernance:federation_clubs_list` - Liste des clubs de la fédération

**Gestion des ligues (Fédération)**
- `gouvernance:federation_ligues_list` - Liste des ligues de la fédération
- `gouvernance:create_ligue_provincial` - Création d'une ligue provinciale

**Gestion des documents**
- `gouvernance:ligue_documents` - Documents de la ligue
- `gouvernance:federation_documents` - Documents de la fédération

**Gestion des communications**
- `gouvernance:ligue_communications` - Communications de la ligue

**Gestion des athlètes (Fédération)**
- `gouvernance:federation_athletes` - Liste des athlètes de la fédération

**Gestion des compétitions (Fédération)**
- `gouvernance:federation_competitions` - Calendrier des compétitions

**Ordres de mission (Fédération)**
- `gouvernance:federation_ordre_mission` - Gestion des ordres de mission

**Profil**
- `gouvernance:ligue_profile` - Profil de la ligue
- `gouvernance:federation_secretary_dashboard` - Profil du secrétaire de fédération

### Cas d'usage

**Secrétaire de Fédération Nationale**
- Gestion administrative d'une fédération nationale
- Supervision des ligues provinciales
- Gestion des documents et communications

**Secrétaire de Ligue Provinciale**
- Création et affiliation des clubs
- Gestion des clubs affiliés
- Génération des documents d'affiliation
- Gestion des communications avec les clubs

### Sécurité

- **Isolation institutionnelle**: Chaque secrétaire ne voit que les données de sa fédération/ligue
- **Vérification serveur**: Les permissions sont vérifiées au niveau du serveur
- **Génération de documents**: Les PDF d'affiliation sont générés automatiquement avec numéro unique et QR Code

---

## 8. CLUB_SECRETARY (Secrétaire de Club)

**Code**: `CLUB_SECRETARY`  
**Désignation**: Secrétaire de Club  
**Niveau d'accès**: Club  
**Portée des données**: Institutionnelle (son club uniquement)

### Permissions

| Permission | Description |
|-----------|-------------|
| **Gestion de l'identité** | Gestion des informations générales du club (nom, logo, couleurs) |
| **Gestion des documents** | Consultation des documents officiels du club (Acte d'Affiliation, Statuts) |
| **Gestion des athlètes** | Gestion de la liste des athlètes du club |
| **Demandes de licences** | Suivi des demandes de licences (Provisoire, Enrôlé, Homologué) |
| **Inscription d'athlètes** | Inscription de nouveaux athlètes (F08) |
| **Gestion du staff** | Gestion du staff technique (Entraîneurs, Médecins) |
| **Gestion des infrastructures** | Consultation des détails du stade/centre d'entraînement |
| **Calendrier des compétitions** | Consultation du calendrier des compétitions |
| **Feuilles de match** | Consultation des feuilles de match (historique des rencontres) |

### Vues accessibles

**Dashboards**
- `gouvernance:club_secretary_dashboard` - Tableau de bord du Secrétaire de Club

**Gestion de l'identité**
- `gouvernance:club_identity` - Identité du club (informations générales, logo, couleurs)

**Gestion des documents**
- `gouvernance:club_documents` - Documents officiels du club

**Gestion des athlètes**
- `gouvernance:club_athletes_list` - Liste de tous les athlètes du club
- `gouvernance:club_athlete_registration` - Inscription d'un nouvel athlète (F08)

**Gestion des licences**
- `gouvernance:club_license_requests` - Suivi des demandes de licences

**Gestion du staff**
- `gouvernance:club_staff` - Gestion du staff technique

**Gestion des infrastructures**
- `gouvernance:club_infrastructure` - Détails du stade/centre d'entraînement

**Gestion des compétitions**
- `gouvernance:club_competitions_calendar` - Calendrier des compétitions
- `gouvernance:club_match_sheets` - Feuilles de match

### Cas d'usage

- Secrétaire d'un club sportif
- Gestion administrative du club
- Gestion des athlètes et du staff
- Suivi des licences et des compétitions

### Sécurité

- **Isolation du club**: Chaque secrétaire ne voit que les données de son club
- **Accès en lecture seule**: Certaines données (documents, calendrier) sont en lecture seule
- **Vérification serveur**: Les permissions sont vérifiées au niveau du serveur

---

## Matrice de Permissions Résumée

| Fonctionnalité | SUPER_ADMIN | SG | MINISTRE | DIR_PROV | FED_SEC | CLUB_SEC |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Initialisation système** | ✓ | - | - | - | - | - |
| **Gestion fédérations** | ✓ | ✓ | ✓ | - | - | - |
| **Validation fédérations** | ✓ | ✓ | ✓ | ✓ | - | - |
| **Gestion ligues** | ✓ | ✓ | - | ✓ | ✓ | - |
| **Création clubs** | ✓ | ✓ | - | - | ✓ | - |
| **Validation clubs** | ✓ | ✓ | - | ✓ | - | - |
| **Affiliation clubs** | ✓ | ✓ | - | - | ✓ | - |
| **Gestion agents** | ✓ | ✓ | - | - | - | - |
| **Gestion infrastructures** | ✓ | ✓ | - | ✓ | - | - |
| **Gestion athlètes** | ✓ | ✓ | - | - | ✓ | ✓ |
| **Signature documents** | ✓ | - | ✓ | - | - | - |
| **Consultation documents** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Flux de Validation Typique

### Création d'une Fédération

1. **SG** enregistre une nouvelle fédération (F03)
2. **Directeur Provincial** examine et émet un avis technique
3. **Ministre** valide et signe l'arrêté
4. **SG** active la fédération

### Création d'une Ligue Provinciale

1. **Secrétaire Fédération** crée une ligue provinciale
2. **SG** valide la ligue
3. **SG** transfère la ligue à la Division Provinciale
4. **Directeur Provincial** valide la ligue

### Création d'un Club

1. **Secrétaire Ligue** crée un club (F07)
2. **Directeur Provincial** valide le club
3. **Secrétaire Ligue** affilie le club (génération Acte d'Affiliation)
4. **Secrétaire Club** reçoit l'email avec le PDF d'affiliation

---

## Sécurité et Bonnes Pratiques

### Vérification des Permissions

- **Toujours vérifier au niveau du serveur**: Utiliser les décorateurs `@require_role()` et les fonctions de permission
- **Jamais faire confiance au frontend**: Les filtres frontend ne suffisent pas
- **Isolation des données**: Chaque rôle ne voit que les données autorisées

### Filtrage Provincial

Pour les rôles provinciaux (DIRECTEUR_PROVINCIAL):
- Vérifier que `profil.province_admin` correspond à la province des données
- Filtrer les requêtes au niveau de la base de données
- Rejeter les accès non autorisés avec `HttpResponseForbidden`

### Gestion des Comptes

- Les comptes sont créés avec un token de vérification par email
- L'utilisateur doit cliquer sur le lien pour activer son compte
- Les mots de passe temporaires ne sont jamais stockés en clair
- Les comptes peuvent être désactivés/réactivés par le SG

---

## Évolution Future

Les rôles suivants sont définis mais pas encore implémentés:
- **DIRECTEUR_CABINET**: Gestion du Cabinet ministériel
- **INSPECTEUR_GENERAL**: Inspection et audit des institutions

Ces rôles pourront être implémentés selon les besoins spécifiques du Ministère.
