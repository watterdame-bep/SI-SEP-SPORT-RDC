# Correction du Contexte user_role pour le Secrétaire Général

## Problème Identifié

Lorsque l'utilisateur SG cliquait sur un menu du sidebar, le sidebar affiché était celui du superadministrateur (avec uniquement le menu "Configuration initiale"). Cela était dû au fait que plusieurs vues SG ne passaient pas la variable `user_role: 'sg'` au contexte du template.

## Solution Appliquée

Ajout de `'user_role': 'sg'` dans le contexte de toutes les vues accessibles au Secrétaire Général.

## Fichiers Modifiés

### 1. core/views.py
- ✅ `gerer_comptes()` - Ajout de `'user_role': 'sg'`
- ✅ `parametres_fonctions()` - Déjà présent
- ✅ `gestion_administrative()` - Déjà présent

### 2. gouvernance/views_federations.py
- ✅ `federations_nationales()` - Ajout de `'user_role': 'sg'`
- ✅ `federation_create()` - Ajout de `'user_role': 'sg'`
- ✅ `federation_detail()` - Ajout de `'user_role': 'sg'`

### 3. gouvernance/views_personnel.py
- ✅ `personnel_ministere()` - Ajout de `'user_role': 'sg'`
- ✅ `enregistrer_agent()` - Ajout de `'user_role': 'sg'`
- ✅ `detail_agent()` - Ajout de `'user_role': 'sg'`
- ✅ `modifier_agent()` - Ajout de `'user_role': 'sg'`

### 4. gouvernance/views_disciplines.py
- ✅ `parametres_disciplines()` - Ajout de `'user_role': 'sg'`

### 5. gouvernance/views_sg_ligues.py
- ✅ `sg_ligues_en_attente()` - Correction de `'secretaire_general'` → `'sg'`
- ✅ `sg_ligue_detail()` - Correction de `'secretaire_general'` → `'sg'`

### 6. gouvernance/views_divisions.py
- ✅ `divisions_provinciales()` - Déjà présent
- ✅ `division_detail()` - Déjà présent

### 7. gouvernance/views_dashboards.py
- ✅ `sg_dashboard()` - Déjà présent
- ✅ `inspections_a_transferer()` - Déjà présent

### 8. gouvernance/views_validation_federation.py
- ✅ `validation_detail()` - Ajout de `'user_role': 'directeur_provincial'`

### 9. infrastructures/views_sg_validation.py
- ✅ `infrastructure_validation_list()` - Ajout de `'user_role': 'sg'`
- ✅ `infrastructure_validation_detail()` - Ajout de `'user_role': 'sg'`

### 10. infrastructures/views.py
- ✅ `infrastructure_list()` - Déjà présent
- ✅ `infrastructure_create()` - Déjà présent
- ✅ `infrastructure_edit()` - Déjà présent
- ✅ `infrastructure_detail()` - Ajout de `'user_role': 'sg' if is_sg else 'directeur_provincial'`

### 11. infrastructures/views_types.py
- ✅ `type_infrastructure_list()` - Déjà présent
- ✅ `type_infrastructure_create()` - Déjà présent
- ✅ `type_infrastructure_edit()` - Déjà présent

## Vérification du Context Processor

Le context processor `core/context_processors.py` fonctionne correctement et détecte automatiquement le rôle `'sg'` pour les utilisateurs avec:
- `role == RoleUtilisateur.INSTITUTION_ADMIN`
- `institution.institution_tutelle_id is None` (Ministère racine)

## Résultat

Maintenant, lorsque le SG clique sur n'importe quel menu du sidebar, le bon sidebar (avec tous les menus SG) s'affiche correctement au lieu du sidebar du superadministrateur.

## Tests Recommandés

1. Se connecter en tant que SG
2. Cliquer sur chaque menu du sidebar:
   - ✅ Tableau de bord
   - ✅ Gestion Administrative
   - ✅ Gérer comptes
   - ✅ Personnel du Ministère
   - ✅ Paramètres → Disciplines
   - ✅ Paramètres → Géographiques
   - ✅ Paramètres → Fonctions
   - ✅ Paramètres → Types d'Infrastructure
   - ✅ Mon Profil
   - ✅ Institutions Sportives → Fédérations Nationales
   - ✅ Institutions Sportives → Divisions Provinciales
   - ✅ Institutions Sportives → Ligues Provinciales
   - ✅ Institutions Sportives → Infrastructures Sportives

3. Vérifier que le sidebar reste cohérent sur toutes les pages

## Date de Correction
9 mars 2026
