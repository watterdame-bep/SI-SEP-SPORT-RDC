# Club Validation Workflow Implementation

## Overview
Implemented a two-step validation workflow for club creation:
1. **Ligue Secretary** creates a club (status: EN_ATTENTE_VALIDATION)
2. **Provincial Director** validates physical existence
3. **Ligue Secretary** affiliates the club (status: AFFILIEE)

## Database Changes

### Migration: 0030_club_validation_workflow
Added to Institution model:
- `statut_validation_club`: CharField with choices
  - EN_ATTENTE_VALIDATION: Awaiting provincial validation
  - VALIDEE_PROVINCIALE: Validated by provincial director
  - REJETEE_PROVINCIALE: Rejected by provincial director
  - AFFILIEE: Officially affiliated

- `existence_physique_confirmee`: BooleanField
  - Tracks if physical existence was confirmed by provincial director

### New Model: ClubValidation
Created `gouvernance/models/club_validation.py` with:
- `club`: OneToOneField to Institution (the club being validated)
- `division_provinciale`: ForeignKey to Institution (provincial director's division)
- `date_demande`: DateTimeField (auto_now_add)
- `date_validation`: DateTimeField (when validated)
- `existence_physique_confirmee`: BooleanField
- `statut`: CharField with choices (EN_ATTENTE, ACCEPTEE, REJETEE)
- `motif_rejet`: TextField (rejection reason)
- `validee_par`: ForeignKey to ProfilUtilisateur (who validated)

Methods:
- `accepter(user)`: Accept validation and update club status
- `rejeter(user, motif)`: Reject validation with reason

## Code Changes

### views_ligue_secretary.py
Updated `ligue_club_create_step3` view:
- Club now created with `statut_validation_club='EN_ATTENTE_VALIDATION'`
- ClubValidation record automatically created after club creation
- Links club to its provincial division for validation
- Success message updated to indicate waiting for provincial validation

## Workflow Steps

### Step 1: Ligue Secretary Creates Club
```
POST /ligue/club/create/step3/
- Form submitted with all club data
- Club created with status: EN_ATTENTE_VALIDATION
- ClubValidation record created
- Redirects to ligue_clubs_affiliation
```

### Step 2: Provincial Director Validates (TO BE IMPLEMENTED)
```
GET /directeur-provincial/clubs-en-attente/
- Shows list of clubs awaiting validation
- Can view club details
- Can confirm physical existence
- Can accept or reject

POST /directeur-provincial/clubs/{id}/valider/
- Updates ClubValidation record
- Sets existence_physique_confirmee
- Updates club status to VALIDEE_PROVINCIALE or REJETEE_PROVINCIALE
```

### Step 3: Ligue Secretary Affiliates Club (TO BE IMPLEMENTED)
```
POST /ligue/clubs/{id}/affilier/
- Only available if club status is VALIDEE_PROVINCIALE
- Updates club status to AFFILIEE
- Club becomes officially active
```

## Next Steps

1. Create views for Provincial Director:
   - List clubs awaiting validation
   - View club details
   - Validate/reject clubs

2. Update Ligue Secretary interface:
   - Show club validation status
   - Display "Affilier" button when validated
   - Show rejection reason if rejected

3. Add admin interface for ClubValidation model

4. Create email notifications:
   - Notify provincial director when club created
   - Notify ligue secretary when club validated/rejected
