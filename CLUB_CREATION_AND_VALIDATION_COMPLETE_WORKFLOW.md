# Club Creation and Validation Complete Workflow

## Overview
This document describes the complete workflow for creating and validating clubs in the SI-SEP Sport system.

## Workflow Stages

### Stage 1: Club Creation by Ligue Secretary

**User Role:** `FEDERATION_SECRETARY` (Ligue Secretary)

**Process:**
1. Ligue Secretary logs in
2. Navigates to "Mes Clubs Affiliés"
3. Clicks "Nouveau Club"
4. Fills 3-step form:
   - **Step 1:** Basic info (name, sigle, code, dates, personnel, athletes)
   - **Step 2:** Address, president info, agrément details
   - **Step 3:** Disciplines and documents

**Data Saved:**
```python
Club (Institution) created with:
- nom_officiel: Club name
- sigle: Club abbreviation
- code: Auto-generated (SIGLE-TIMESTAMP)
- institution_tutelle: The ligue
- province_admin: Ligue's province
- statut_validation_club: 'EN_ATTENTE_VALIDATION'
- statut_activation: 'ACTIVE'

ClubValidation record created with:
- club: The newly created club
- division_provinciale: Provincial division Institution
- statut: 'EN_ATTENTE'
- date_demande: Current timestamp
```

**Success Message:**
```
✓ Club 'Club Name' créé avec succès! 
En attente de validation par la direction provinciale.
```

**Club appears in:**
- "Mes Clubs Affiliés" interface (status: "En attente")

---

### Stage 2: Club Validation by Provincial Director

**User Role:** `directeur_provincial` (Provincial Director)

**Process:**
1. Provincial Director logs in
2. Navigates to "Clubs en Attente de Validation"
3. Sees all clubs in their province awaiting validation
4. Clicks "Valider" on a club
5. Reviews club details:
   - Basic information
   - Address
   - President information
   - Disciplines
   - Documents
6. Chooses action:
   - **Accept:** Confirms physical existence
   - **Reject:** Provides rejection reason

**If Accepted:**
```python
ClubValidation updated:
- statut: 'ACCEPTEE'
- existence_physique_confirmee: True/False
- date_validation: Current timestamp
- validee_par: Provincial director's profile

Club (Institution) updated:
- statut_validation_club: 'VALIDEE_PROVINCIALE'
- existence_physique_confirmee: True/False
```

**If Rejected:**
```python
ClubValidation updated:
- statut: 'REJETEE'
- motif_rejet: Rejection reason
- date_validation: Current timestamp
- validee_par: Provincial director's profile

Club (Institution) updated:
- statut_validation_club: 'REJETEE_PROVINCIALE'
```

**Success Messages:**
- Accept: `✓ Club 'Club Name' validé avec succès!`
- Reject: `✓ Club 'Club Name' rejeté.`

**Club appears in:**
- "Mes Clubs Affiliés" interface (status: "Validé" or "Rejeté")

---

### Stage 3: Club Affiliation by Ligue Secretary

**User Role:** `FEDERATION_SECRETARY` (Ligue Secretary)

**Process:**
1. Ligue Secretary logs in
2. Navigates to "Mes Clubs Affiliés"
3. Sees validated clubs with "Affilier" button
4. Clicks "Affilier" on a validated club
5. Confirms affiliation

**Data Updated:**
```python
Club (Institution) updated:
- statut_validation_club: 'AFFILIEE'

ClubValidation updated:
- statut: 'AFFILIEE'
```

**Success Message:**
```
✓ Club 'Club Name' affilié avec succès!
```

**Club appears in:**
- "Mes Clubs Affiliés" interface (status: "Affilié")

---

## Status Progression

```
EN_ATTENTE_VALIDATION
    ↓
    ├─→ VALIDEE_PROVINCIALE (if accepted by provincial director)
    │       ↓
    │       └─→ AFFILIEE (if affiliated by ligue secretary)
    │
    └─→ REJETEE_PROVINCIALE (if rejected by provincial director)
```

## Database Schema

### Institution Model (Club)
```python
code: CharField (unique)
nom_officiel: CharField
sigle: CharField
institution_tutelle: ForeignKey (Ligue)
niveau_territorial: CharField = 'CLUB'
province_admin: ForeignKey (Province)
statut_activation: CharField = 'ACTIVE'
statut_validation_club: CharField (EN_ATTENTE_VALIDATION, VALIDEE_PROVINCIALE, REJETEE_PROVINCIALE, AFFILIEE)
existence_physique_confirmee: BooleanField = False
```

### ClubValidation Model
```python
club: OneToOneField (Institution)
division_provinciale: ForeignKey (Institution - Provincial Division)
statut: CharField (EN_ATTENTE, ACCEPTEE, REJETEE)
date_demande: DateTimeField (auto_now_add)
date_validation: DateTimeField (nullable)
existence_physique_confirmee: BooleanField = False
motif_rejet: TextField (nullable)
validee_par: ForeignKey (ProfilUtilisateur, nullable)
```

## User Interfaces

### 1. Ligue Secretary - "Mes Clubs Affiliés"
**URL:** `/gouvernance/ligue/clubs/affiliation/`

**Features:**
- Statistics cards (Total, En Attente, Validés, Affiliés, Rejetés)
- Search by club name/sigle
- Filter by status
- Table with club information
- Action buttons (View, Affiliate if validated)
- "Nouveau Club" button

**Status Badges:**
- En attente: Yellow
- Validé: Green
- Affilié: Blue
- Rejeté: Red

### 2. Provincial Director - "Clubs en Attente de Validation"
**URL:** `/gouvernance/directeur-provincial/clubs-en-attente/`

**Features:**
- Filter by status (All, En Attente, Acceptés, Rejetés)
- List of clubs awaiting validation
- Club information (name, sigle, code, date requested, ligue)
- "Valider" button for pending clubs
- "Voir" button for processed clubs

### 3. Provincial Director - Club Validation Detail
**URL:** `/gouvernance/directeur-provincial/clubs/<validation_id>/valider/`

**Features:**
- Full club details
- Address information
- President information
- Disciplines
- Documents
- Accept/Reject actions
- Physical existence confirmation checkbox
- Rejection reason textarea

## API Endpoints

### Club Creation
- **POST** `/gouvernance/ligue/clubs/create/step1/` - Step 1
- **POST** `/gouvernance/ligue/clubs/create/step2/` - Step 2
- **POST** `/gouvernance/ligue/clubs/create/step3/` - Step 3 (creates club)

### Club Validation
- **GET** `/gouvernance/directeur-provincial/clubs-en-attente/` - List clubs
- **GET** `/gouvernance/directeur-provincial/clubs/<validation_id>/valider/` - View club
- **POST** `/gouvernance/directeur-provincial/clubs/<validation_id>/valider/` - Accept/Reject

### Club Affiliation
- **GET** `/gouvernance/ligue/clubs/<club_id>/affiliate/` - Confirm affiliation
- **POST** `/gouvernance/ligue/clubs/<club_id>/affiliate/` - Affiliate club

## Error Handling

### Club Creation Errors
- Missing required fields → Form validation error
- Invalid date format → Date parsing error
- Duplicate club code → IntegrityError
- Missing TypeInstitution 'CLUB' → TypeInstitution.DoesNotExist
- Missing provincial division → ClubValidation not created (but club still created)

### Club Validation Errors
- Provincial director not assigned to province → Error message
- Club not found → 404 error
- Unauthorized access → Error message
- Missing rejection reason → Form validation error

## Permissions

### Ligue Secretary
- Can create clubs
- Can view their clubs
- Can affiliate validated clubs
- Cannot validate clubs
- Cannot see other ligues' clubs

### Provincial Director
- Can validate clubs in their province
- Can reject clubs with reason
- Can view club details
- Cannot create clubs
- Cannot affiliate clubs

### SG (Secrétaire Général)
- Can view all clubs
- Can view all validations
- Cannot validate clubs
- Cannot create clubs

## Testing Checklist

- [ ] Ligue secretary can create club
- [ ] Club appears in "Mes Clubs Affiliés" with "En attente" status
- [ ] ClubValidation record created
- [ ] Provincial director can see club in validation list
- [ ] Provincial director can accept club
- [ ] Club status changes to "Validé"
- [ ] Ligue secretary sees "Affilier" button
- [ ] Ligue secretary can affiliate club
- [ ] Club status changes to "Affilié"
- [ ] Provincial director can reject club
- [ ] Club status changes to "Rejeté"
- [ ] Search and filter work correctly
- [ ] Statistics update correctly

## Deployment Checklist

- [ ] Database migrations applied
- [ ] Views updated
- [ ] Templates updated
- [ ] URL routes configured
- [ ] Permissions configured
- [ ] Test data created
- [ ] Provincial directors assigned to provinces
- [ ] Provincial division Institutions created
- [ ] Tested with real users

## Future Enhancements

- [ ] Email notifications on status changes
- [ ] SMS notifications
- [ ] Bulk club import
- [ ] Club status history/timeline
- [ ] Comments/notes on validation
- [ ] Audit trail
- [ ] Export to CSV/Excel
- [ ] Integration with external systems
- [ ] Automated validation rules
- [ ] Document verification
