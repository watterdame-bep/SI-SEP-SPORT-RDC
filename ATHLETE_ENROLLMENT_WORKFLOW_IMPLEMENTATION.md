# Implémentation du Workflow d'Enrôlement des Athlètes

## Vue d'ensemble

Le workflow de certification des athlètes a été modifié pour inclure une étape d'enrôlement physique à la ligue provinciale avant la validation.

## Nouveau Workflow

### 1. Enregistrement par le Club (Statut: PROVISOIRE)
- Le secrétaire du club enregistre l'athlète dans le système
- Statut initial: `PROVISOIRE`
- L'athlète reçoit un numéro sportif unique

### 2. Enrôlement à la Ligue (Statut: EN_ATTENTE_VALIDATION_LIGUE)
- **L'athlète se présente physiquement** au bureau de la ligue provinciale
- Le secrétaire de la ligue effectue:
  - **Test médical** (résultat: APTE / INAPTE)
  - **Relevé des empreintes digitales**
  - Upload du certificat médical
  - Observations éventuelles
- Statut après enrôlement: `EN_ATTENTE_VALIDATION_LIGUE`

### 3. Validation par la Ligue (Statut: CERTIFIE_PROVINCIAL)
- Le secrétaire de la ligue valide l'athlète enrôlé
- Vérification anti-fraude (doublons dans la province)
- Statut après validation: `CERTIFIE_PROVINCIAL`

### 4. Certification par la Fédération (Statut: CERTIFIE_NATIONAL)
- Le secrétaire de la fédération certifie l'athlète
- Vérification anti-fraude (doublons au niveau national)
- Statut final: `CERTIFIE_NATIONAL`
- Génération des informations de licence (numéro, dates)

## Modifications Techniques

### Migration 0036_athlete_enrollment_workflow.py
Ajout des champs suivants au modèle `Athlete`:

```python
# Enrôlement
- date_enrolement: DateTimeField
- agent_enrolement: ForeignKey(ProfilUtilisateur)
- certificat_medical_enrolement: FileField
- date_test_medical: DateField
- resultat_test_medical: CharField (APTE/INAPTE/EN_ATTENTE)
- empreinte_digitale: FileField
- observations_enrolement: TextField

# Nouveau statut
- EN_ATTENTE_VALIDATION_LIGUE: Ajouté aux choix de statut_certification
```

### Vues Ajoutées

#### `ligue_athletes_enrollment_list`
- **URL**: `/gouvernance/ligue/athletes/enrollment/`
- **Rôle**: LIGUE_SECRETARY
- **Description**: Liste des athlètes PROVISOIRE en attente d'enrôlement
- **Template**: `gouvernance/ligue_athletes_enrollment_list.html` (à créer)

#### `ligue_athlete_enroll`
- **URL**: `/gouvernance/ligue/athletes/<uuid>/enroll/`
- **Rôle**: LIGUE_SECRETARY
- **Description**: Formulaire d'enrôlement (test médical + empreintes)
- **Template**: `gouvernance/ligue_athletes_enrollment.html` (à créer)
- **Validation**:
  - Résultat médical obligatoire (APTE requis)
  - Empreintes digitales obligatoires
  - Certificat médical optionnel

### Vues Modifiées

#### `ligue_athletes_validation_list`
- Affiche maintenant les athlètes `EN_ATTENTE_VALIDATION_LIGUE` (enrôlés)
- Correction du rôle: `LIGUE_SECRETARY` (était `FEDERATION_SECRETARY`)

#### `ligue_athlete_validate`
- Valide uniquement les athlètes `EN_ATTENTE_VALIDATION_LIGUE`
- Correction du rôle: `LIGUE_SECRETARY`

## Statuts de Certification

| Statut | Description | Qui peut agir |
|--------|-------------|---------------|
| `PROVISOIRE` | Enregistré par le club, en attente d'enrôlement | Ligue (enrôlement) |
| `EN_ATTENTE_VALIDATION_LIGUE` | Enrôlé à la ligue, en attente de validation | Ligue (validation) |
| `CERTIFIE_PROVINCIAL` | Validé par la ligue, en attente de certification nationale | Fédération (certification) |
| `CERTIFIE_NATIONAL` | Certifié nationalement, licence active | - |
| `REJETE_LIGUE` | Rejeté par la ligue | - |
| `REJETE_FEDERATION` | Rejeté par la fédération | - |

## Templates à Créer

### 1. `templates/gouvernance/ligue_athletes_enrollment_list.html`
Liste des athlètes en attente d'enrôlement avec:
- Photo, nom, club
- Bouton "Enrôler" pour chaque athlète

### 2. `templates/gouvernance/ligue_athlete_enroll.html`
Formulaire d'enrôlement avec:
- Informations de l'athlète (lecture seule)
- Section Test Médical:
  - Date du test
  - Résultat (APTE/INAPTE)
  - Upload certificat médical
- Section Empreintes:
  - Upload fichier empreintes digitales
- Observations
- Bouton "Enrôler"

## Mise à Jour du Menu Sidebar

Dans `templates/core/base.html`, ajouter pour le rôle LIGUE_SECRETARY:

```html
<!-- Enrôlement Athlètes -->
<a href="{% url 'gouvernance:ligue_athletes_enrollment_list' %}" 
   class="sidebar-link {% if request.resolver_match.url_name == 'ligue_athletes_enrollment_list' %}active{% endif %}">
    <i class="fa-solid fa-user-plus"></i>
    <span>Enrôlement Athlètes</span>
    {% if athletes_enrollment_count > 0 %}
    <span class="badge bg-warning">{{ athletes_enrollment_count }}</span>
    {% endif %}
</a>

<!-- Validation Athlètes -->
<a href="{% url 'gouvernance:ligue_athletes_validation_list' %}" 
   class="sidebar-link {% if request.resolver_match.url_name == 'ligue_athletes_validation_list' %}active{% endif %}">
    <i class="fa-solid fa-user-check"></i>
    <span>Validation Athlètes</span>
    {% if athletes_validation_count > 0 %}
    <span class="badge bg-info">{{ athletes_validation_count }}</span>
    {% endif %}
</a>
```

## Context Processor à Mettre à Jour

Dans `core/context_processors.py`, fonction `athletes_counts()`:

```python
if user_role == 'ligue_secretary':
    ligue = profil.institution
    # Athlètes en attente d'enrôlement
    enrollment_count = Athlete.objects.filter(
        club__institution_tutelle=ligue,
        statut_certification='PROVISOIRE',
        actif=True
    ).count()
    
    # Athlètes en attente de validation
    validation_count = Athlete.objects.filter(
        club__institution_tutelle=ligue,
        statut_certification='EN_ATTENTE_VALIDATION_LIGUE',
        actif=True
    ).count()
    
    return {
        'athletes_enrollment_count': enrollment_count,
        'athletes_validation_count': validation_count,
    }
```

## Badges dans la Liste des Athlètes du Club

Mettre à jour `templates/gouvernance/club_athletes_list.html`:

```html
{% elif athlete.statut_certification == 'EN_ATTENTE_VALIDATION_LIGUE' %}
<span class="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
    <i class="fa-solid fa-hourglass text-blue-500 text-xs mr-1"></i> Enrôlé
</span>
```

## Prochaines Étapes

1. ✅ Migration appliquée
2. ✅ Modèle Athlete mis à jour
3. ✅ Vues d'enrôlement créées
4. ✅ URLs ajoutées
5. ⏳ Créer template `ligue_athletes_enrollment_list.html`
6. ⏳ Créer template `ligue_athlete_enroll.html`
7. ⏳ Mettre à jour le context processor
8. ⏳ Mettre à jour le sidebar
9. ⏳ Mettre à jour les badges dans la liste des athlètes du club

## Notes Importantes

- **Présence physique obligatoire**: L'athlète doit se présenter à la ligue pour l'enrôlement
- **Test médical obligatoire**: Résultat APTE requis pour continuer
- **Empreintes obligatoires**: Fichier d'empreintes digitales requis
- **Pas de génération automatique de documents**: Les licences ne sont plus générées automatiquement en PDF
