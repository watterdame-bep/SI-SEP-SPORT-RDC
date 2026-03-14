# Club Validation - Provincial Director Interface

## Implementation Complete

### Files Created

1. **gouvernance/views_club_validation.py**
   - `clubs_en_attente_validation()`: List clubs awaiting validation
   - `club_validation_detail()`: View and validate/reject a club

2. **templates/gouvernance/clubs_en_attente_validation.html**
   - List view of clubs awaiting validation
   - Filter by status (EN_ATTENTE, ACCEPTEE, REJETEE)
   - Quick action buttons

3. **templates/gouvernance/club_validation_detail.html**
   - Detailed club information
   - Club address and president details
   - Validation form with physical existence checkbox
   - Accept/Reject buttons
   - Timeline of validation history
   - Reject modal with reason input

4. **Updated gouvernance/urls.py**
   - Added import for views_club_validation
   - Added two new routes:
     - `/directeur-provincial/clubs-en-attente/` - List view
     - `/directeur-provincial/clubs/<id>/valider/` - Detail view

## Features

### Provincial Director Interface

**List View** (`clubs_en_attente_validation`)
- Shows all clubs awaiting validation for the provincial division
- Filter by status: All, En Attente, Acceptés, Rejetés
- Quick view of club info (name, sigle, code, date, ligue)
- Action button to validate

**Detail View** (`club_validation_detail`)
- Full club information display
- Address and president details
- Validation form with:
  - Checkbox for "Existence physique confirmée"
  - Accept button (green)
  - Reject button (red)
- Reject modal with reason textarea
- Timeline showing validation history

### Validation Actions

**Accept Club**
```python
POST /directeur-provincial/clubs/<id>/valider/
- action: accepter
- existence_physique_confirmee: on/off
- Updates ClubValidation.statut = 'ACCEPTEE'
- Updates Institution.statut_validation_club = 'VALIDEE_PROVINCIALE'
- Records validator and timestamp
```

**Reject Club**
```python
POST /directeur-provincial/clubs/<id>/valider/
- action: rejeter
- motif_rejet: reason text
- Updates ClubValidation.statut = 'REJETEE'
- Updates Institution.statut_validation_club = 'REJETEE_PROVINCIALE'
- Records validator, timestamp, and rejection reason
```

## Next Steps

1. **Update Ligue Secretary Interface**
   - Show club validation status in clubs list
   - Display "Affilier" button when status is VALIDEE_PROVINCIALE
   - Show rejection reason if status is REJETEE_PROVINCIALE
   - Implement affiliate action to set status to AFFILIEE

2. **Add to Sidebar Navigation**
   - Add link to "Clubs en Attente" in provincial director sidebar
   - Show badge with count of pending clubs

3. **Email Notifications**
   - Notify provincial director when new club created
   - Notify ligue secretary when club validated/rejected

4. **Admin Interface**
   - Register ClubValidation in Django admin
   - Add filters and search
