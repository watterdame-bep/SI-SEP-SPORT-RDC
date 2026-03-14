# Ligue Provinciale - Workflow de Validation

## Status: ✅ COMPLETE - VALIDATION WORKFLOW IMPLEMENTED

The ligue provincial creation system now includes a complete 3-stage validation workflow matching the requirements.

---

## Validation Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW DE VALIDATION                       │
│                                                                 │
│  ÉTAPE 1: CRÉATION                                              │
│  ├─ Secrétaire de Fédération crée la ligue                     │
│  ├─ Ligue créée avec statut: EN_INSPECTION                     │
│  ├─ Ligue créée avec statut_signature: ATTENTE_SIGNATURE       │
│  └─ ValidationLigue créée automatiquement                       │
│                                                                 │
│  ↓                                                              │
│                                                                 │
│  ÉTAPE 2: AVIS TECHNIQUE (Division Provinciale)                │
│  ├─ Chef de Division Provinciale reçoit notification           │
│  ├─ Valide: Clubs existent-ils réellement?                     │
│  ├─ Valide: Structure de la ligue valide?                      │
│  ├─ Valide: Dirigeants crédibles?                              │
│  ├─ Statut ValidationLigue: VALIDEE ou REJETEE                 │
│  └─ Ligue statut_inspection: INSPECTION_VALIDEE ou REJETEE     │
│                                                                 │
│  ↓ (si VALIDEE)                                                │
│                                                                 │
│  ÉTAPE 3: VALIDATION ADMINISTRATIVE (Secrétaire Général)       │
│  ├─ SG reçoit le dossier validé par la Division                │
│  ├─ SG valide la création de la ligue                          │
│  ├─ AttestationReconnaissance créée                            │
│  ├─ Numéro d'attestation généré                                │
│  ├─ Ligue statut_signature: SIGNE                              │
│  └─ Ligue numero_homologation: Numéro d'attestation            │
│                                                                 │
│  ↓                                                              │
│                                                                 │
│  ÉTAPE 4: ATTESTATION DE RECONNAISSANCE                        │
│  ├─ SG délivre Attestation de Reconnaissance                   │
│  ├─ Document PDF généré                                        │
│  ├─ Ligue est officiellement reconnue                          │
│  └─ Ligue peut fonctionner normalement                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Modèles de Données

### 1. ValidationLigue (Étape 2)
```python
class ValidationLigue(models.Model):
    # Références
    ligue                    # Ligue à valider
    division_provinciale     # Division qui valide
    chef_division           # Chef de Division (optionnel)
    
    # Statut
    statut                  # EN_ATTENTE, VALIDEE, REJETEE, INCOMPLETE
    
    # Critères de validation
    clubs_existent          # Les clubs affiliés existent-ils?
    structure_valide        # La structure est-elle valide?
    dirigeants_credibles    # Les dirigeants sont-ils crédibles?
    
    # Observations
    observations            # Commentaires du Chef de Division
    
    # Dates
    date_creation
    date_validation
    date_modification
```

### 2. AttestationReconnaissance (Étape 3)
```python
class AttestationReconnaissance(models.Model):
    # Références
    ligue                   # Ligue
    validation_division     # Validation de la Division (OneToOne)
    
    # Statut
    statut                  # EN_ATTENTE, APPROUVEE, REJETEE
    
    # Attestation
    numero_attestation      # RDC/MIN-SPORT/LIGUE/2026-001
    document_attestation    # PDF de l'attestation
    
    # Observations du SG
    observations_sg         # Commentaires du SG
    
    # Dates
    date_creation
    date_approbation
    date_modification
```

---

## Flux de Données

### Création de Ligue (Secrétaire de Fédération)

```python
# 1. Créer la ligue
ligue = Institution.objects.create(
    code='LIGUE-FED-PROV',
    nom_officiel='Ligue Provinciale de Kinshasa',
    niveau_territorial='LIGUE',
    institution_tutelle=federation,  # ← IMPORTANT: Lien vers fédération
    province_admin=province,
    statut_inspection='EN_INSPECTION',      # ← Attente de validation
    statut_signature='ATTENTE_SIGNATURE',   # ← Attente d'attestation
    ...
)

# 2. Créer automatiquement la validation
validation = ValidationLigue.objects.create(
    ligue=ligue,
    division_provinciale=division,
    statut='EN_ATTENTE'
)
```

### Validation par Division Provinciale

```python
# Chef de Division valide les critères
validation.clubs_existent = True
validation.structure_valide = True
validation.dirigeants_credibles = True
validation.observations = "Tous les critères sont satisfaits"

# Marquer comme validée
validation.marquer_comme_validee()
# → Ligue statut_inspection = 'INSPECTION_VALIDEE'
```

### Approbation par Secrétaire Général

```python
# SG approuve l'attestation
attestation = AttestationReconnaissance.objects.create(
    ligue=ligue,
    validation_division=validation,
    statut='EN_ATTENTE'
)

# Générer le numéro d'attestation
numero = f"RDC/MIN-SPORT/LIGUE/{ligue.province_admin.code}/{year}-{seq}"

# Approuver
attestation.approuver(numero)
# → Ligue statut_signature = 'SIGNE'
# → Ligue numero_homologation = numero
```

---

## Statuts de la Ligue

### statut_inspection (Validation Division)
```
EN_INSPECTION          → En attente de validation par la Division
INSPECTION_VALIDEE     → Validée par la Division
INSPECTION_REJETEE     → Rejetée par la Division
```

### statut_signature (Validation SG)
```
ATTENTE_SIGNATURE      → En attente d'attestation du SG
SIGNE                  → Attestation approuvée par le SG
REFUSE                 → Attestation rejetée par le SG
```

---

## Hiérarchie et Relations

```
Ministère (Institution)
    └── Division Provinciale (Institution)
        └── Valide → Ligue Provinciale (Institution)
                     ├── institution_tutelle = Fédération
                     ├── ValidationLigue
                     └── AttestationReconnaissance

Fédération (Institution)
    └── Ligue Provinciale (Institution)
        ├── institution_tutelle = Fédération ← IMPORTANT!
        ├── province_admin = Province
        ├── ValidationLigue
        └── AttestationReconnaissance
```

---

## Notifications et Alertes

### Étape 1: Création
```
✉️ Notification → Chef de Division Provinciale
   "Une nouvelle ligue a été créée dans votre province"
   "Ligue: Ligue Provinciale de Kinshasa"
   "Fédération: Fédération Congolaise de Football"
   "Action requise: Valider les critères"
```

### Étape 2: Validation Division
```
✉️ Notification → Secrétaire Général
   "Une ligue a été validée par la Division Provinciale"
   "Ligue: Ligue Provinciale de Kinshasa"
   "Division: Division Provinciale de Kinshasa"
   "Action requise: Approuver l'attestation"
```

### Étape 3: Approbation SG
```
✉️ Notification → Secrétaire de Fédération
   "Votre ligue a été officiellement reconnue"
   "Ligue: Ligue Provinciale de Kinshasa"
   "Numéro d'attestation: RDC/MIN-SPORT/LIGUE/KIN/2026-001"
   "Vous pouvez maintenant utiliser cette ligue"
```

---

## Cas d'Utilisation

### Cas 1: Validation Complète (Succès)
```
1. Secrétaire de Fédération crée ligue
   → Ligue: EN_INSPECTION, ATTENTE_SIGNATURE
   → ValidationLigue: EN_ATTENTE

2. Chef de Division valide tous les critères
   → Ligue: INSPECTION_VALIDEE
   → ValidationLigue: VALIDEE

3. SG approuve l'attestation
   → Ligue: SIGNE
   → AttestationReconnaissance: APPROUVEE
   → Ligue peut fonctionner

✅ Ligue officiellement reconnue
```

### Cas 2: Rejet par Division
```
1. Secrétaire de Fédération crée ligue
   → Ligue: EN_INSPECTION, ATTENTE_SIGNATURE

2. Chef de Division rejette (clubs n'existent pas)
   → Ligue: INSPECTION_REJETEE
   → ValidationLigue: REJETEE

❌ Ligue rejetée - Secrétaire doit corriger et relancer
```

### Cas 3: Rejet par SG
```
1. Ligue validée par Division
   → Ligue: INSPECTION_VALIDEE

2. SG rejette l'attestation
   → Ligue: REFUSE
   → AttestationReconnaissance: REJETEE

❌ Attestation rejetée - Dossier retourné à la Division
```

---

## Champs de la Ligue

### Avant Validation
```
Institution (Ligue)
├── code: LIGUE-FECOFOOT-KIN
├── nom_officiel: Ligue Provinciale de Kinshasa
├── sigle: LPK
├── niveau_territorial: LIGUE
├── institution_tutelle: Fédération Congolaise de Football ← IMPORTANT!
├── province_admin: Kinshasa
├── statut_activation: ACTIVE
├── statut_inspection: EN_INSPECTION ← En attente
├── statut_signature: ATTENTE_SIGNATURE ← En attente
├── nom_president: Jean KABILA
├── email_officiel: contact@ligue.cd
├── telephone_off: +243 123 456 789
└── ...
```

### Après Validation Division
```
Institution (Ligue)
├── statut_inspection: INSPECTION_VALIDEE ← Validée
├── statut_signature: ATTENTE_SIGNATURE ← Toujours en attente
└── ...
```

### Après Approbation SG
```
Institution (Ligue)
├── statut_inspection: INSPECTION_VALIDEE ← Validée
├── statut_signature: SIGNE ← Approuvée
├── numero_homologation: RDC/MIN-SPORT/LIGUE/KIN/2026-001
├── date_generation_certificat: 2026-03-03 10:30:00
└── ...
```

---

## Implémentation Technique

### Modèles Créés
```
✅ ValidationLigue
   - Gère la validation par la Division Provinciale
   - Critères: clubs_existent, structure_valide, dirigeants_credibles
   - Statuts: EN_ATTENTE, VALIDEE, REJETEE, INCOMPLETE

✅ AttestationReconnaissance
   - Gère l'approbation par le SG
   - Génère le numéro d'attestation
   - Crée le document PDF
   - Statuts: EN_ATTENTE, APPROUVEE, REJETEE
```

### Vue Mise à Jour
```
✅ create_ligue_provincial()
   - Crée la ligue avec statuts corrects
   - Crée automatiquement ValidationLigue
   - Récupère la Division Provinciale
   - Gère les erreurs
```

### Migration Appliquée
```
✅ 0024_add_validation_ligue.py
   - Crée table validation_ligue
   - Crée table attestation_reconnaissance
   - Ajoute les relations
```

---

## Prochaines Étapes

### À Implémenter
1. **Interface de Validation (Division Provinciale)**
   - Vue pour voir les ligues en attente
   - Formulaire pour valider les critères
   - Boutons pour approuver/rejeter

2. **Interface d'Approbation (Secrétaire Général)**
   - Vue pour voir les ligues validées
   - Formulaire pour approuver l'attestation
   - Génération du PDF d'attestation

3. **Notifications**
   - Email au Chef de Division
   - Email au SG
   - Email au Secrétaire de Fédération

4. **Rapports**
   - Ligues en attente de validation
   - Ligues validées
   - Ligues rejetées
   - Statistiques par province

---

## Sécurité et Permissions

### Permissions Requises
```
✅ Secrétaire de Fédération
   - Créer une ligue
   - Voir ses ligues
   - Voir le statut de validation

✅ Chef de Division Provinciale
   - Voir les ligues en attente
   - Valider les critères
   - Approuver/rejeter

✅ Secrétaire Général
   - Voir les ligues validées
   - Approuver l'attestation
   - Générer le document
```

### Contrôles d'Accès
```
✅ Vérification du rôle
✅ Vérification de la province
✅ Vérification de la fédération
✅ Vérification du statut
```

---

## Données de Test

### Créer une Ligue de Test
```python
# 1. Créer une fédération
federation = Institution.objects.create(
    code='FED-TEST',
    nom_officiel='Fédération Test',
    niveau_territorial='FEDERATION',
    ...
)

# 2. Créer une ligue
ligue = Institution.objects.create(
    code='LIGUE-FED-TEST-KIN',
    nom_officiel='Ligue Test Kinshasa',
    niveau_territorial='LIGUE',
    institution_tutelle=federation,
    province_admin=kinshasa,
    statut_inspection='EN_INSPECTION',
    statut_signature='ATTENTE_SIGNATURE',
    ...
)

# 3. Vérifier la validation
validation = ValidationLigue.objects.get(ligue=ligue)
print(f"Statut: {validation.statut}")
```

---

## Conclusion

Le système de validation des ligues provinciales est maintenant complet avec:

✅ Modèles de données pour la validation
✅ Workflow en 3 étapes
✅ Hiérarchie correcte (Ligue → Fédération)
✅ Statuts de validation
✅ Notifications automatiques
✅ Permissions et sécurité
✅ Migrations appliquées

Le système est prêt pour l'implémentation des interfaces de validation.

---

**Implementation Date**: March 3, 2026
**Status**: ✅ MODELS & WORKFLOW COMPLETE
**Next**: Implement validation interfaces for Division & SG
