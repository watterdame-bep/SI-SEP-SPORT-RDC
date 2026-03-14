# SI-SEP Sport RDC

**Système Intégré de Suivi-Évaluation et Pilotage du Sport en RD Congo**

Backend Django — Base de données et API pour les modules **Gouvernance** et **Infrastructures**.

## Hiérarchie du mouvement sportif

- **État** (Ministère / Division Provinciale) → **Fédérations** → **Ligues** → **Clubs**
- Chaque institution peut avoir une **Institution Parente** (tutelle) — relation auto-référente.
- Validation à double niveau : **Sportif** (Ligue/Fédération) et **Administratif** (Division Provinciale).

## Prérequis

- Python 3.10+
- MySQL 8+ (ou MariaDB 10.3+)

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` en `.env` et renseigner les variables (notamment la base MySQL).

```bash
copy .env.example .env   # Windows
```

## Base de données MySQL « si-sep sport »

1. **Créer la base** (si elle n’existe pas) :

```sql
CREATE DATABASE `si-sep sport` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. **Variables dans `.env`** : `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT=3306`.

3. **Créer les migrations** (après modification des modèles) :

```bash
python manage.py makemigrations gouvernance infrastructures
```

4. **Appliquer les migrations** :

```bash
python manage.py migrate
```

5. **Créer un superutilisateur** (admin Django) :

```bash
python manage.py createsuperuser
```

## Lancer le serveur

```bash
python manage.py runserver
```

- Admin Django : http://127.0.0.1:8000/admin/
- API : http://127.0.0.1:8000/api/gouvernance/ et /api/infrastructures/

## Modules

### 1. Gouvernance

- **Institutions** : code, nom officiel, sigle, type, **institution_tutelle** (parent), agrément.
- **Référentiel géographique** : Territoire/Ville, Division Provinciale, Secteur/Commune, Groupement/Quartier, Village/Quartier.
- **Agréments** : état d’agrément, agrément administratif (validation_admin, valid_tec_sportive).
- **Organigramme** : Fonction, Membre (Personne + Institution + Fonction), Mandat (dates, statut, document).

### 2. Infrastructures

- **Infrastructure** : code d’homologation unique, nom, type, **géolocalisation** (latitude, longitude), territoire, gestionnaire.
- **Suivi technique** : date, état général, capacité, observations.
- **Revenus** : date, type, montant, devise (CDF).

## Contraintes techniques

- Base **MySQL** (« si-sep sport »).
- **Souveraineté des données** : coordonnées GPS et codes d’homologation gérés en base.
- Clés primaires **UUID** pour les entités métier (UID/UniqueID du MLD).
