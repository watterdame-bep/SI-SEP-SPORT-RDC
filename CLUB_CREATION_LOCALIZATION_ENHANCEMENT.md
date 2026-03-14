# Club Creation Form - Localization Fields Enhancement

## Summary
Updated the club creation form (Step 2) to include complete cascading localization fields matching the federation creation form. The province field is pre-filled with the ligue's province, and all location fields use database-driven selects with proper cascading behavior.

## Changes Made

### 1. Form Classes Updated (`gouvernance/forms.py`)

#### ClubAddressForm (Step 2)
**Updated localization fields:**
- `province` - ModelChoiceField (required) - Pre-filled with ligue's province
- `territoire` - ModelChoiceField (optional) - Cascades from province
- `secteur` - ModelChoiceField (optional) - Cascades from territoire
- `groupement_quartier` - ModelChoiceField (optional) - Cascades from secteur
- `avenue` - CharField (required) - Street address
- `numero` - CharField (optional) - Street number

**Removed fields:**
- `commune` - Replaced with proper cascading location hierarchy

**Added __init__ method:**
- Pre-fills province with ligue's province_admin
- Initializes territoire queryset with territories from ligue's province
- Sets up empty querysets for secteur and groupement_quartier (populated via JavaScript)

### 2. Template Updated (`templates/gouvernance/ligue_club_create.html`)

#### Step 2: Localization Section
**Complete restructure with cascading selects:**
- Province (required) - Pre-filled with ligue's province
- Territoire/Ville (optional) - Disabled until province selected
- Secteur/Commune (optional) - Disabled until territoire selected
- Groupement/Quartier (optional) - Disabled until secteur selected
- Avenue/Rue (required)
- Numéro (optional)

**JavaScript Cascading Logic:**
- Loads provinces on page load from `/parametres-geographiques/api/provinces/`
- Province change → Loads territoires from `/parametres-geographiques/api/territoires/?province={id}`
- Territoire change → Loads secteurs from `/parametres-geographiques/api/secteurs/?territoire={id}`
- Secteur change → Loads groupements from `/parametres-geographiques/api/groupements/?secteur={id}`
- Each level disables dependent selects until parent is selected
- Shows "Chargement..." while fetching data

#### Validation Update
- Updated required fields for step 2: `['province', 'avenue', 'nom_president']`
- Province is now required for club creation

### 3. Views Updated (`gouvernance/views_ligue_secretary.py`)

#### ligue_club_create_step2()
**Enhanced to:**
- Pass `ligue=ligue` to form initialization for pre-filling province
- Store all location fields in session:
  - `province` - UUID of selected province
  - `territoire` - UUID of selected territoire
  - `secteur` - UUID of selected secteur
  - `groupement_quartier` - UUID of selected groupement
  - `avenue` - Street address
  - `numero` - Street number
- Properly convert UUIDs to strings for session storage

#### ligue_club_create_step3()
**Updated to:**
- Create AdresseContact with avenue and numero (instead of commune)
- Location hierarchy is now properly stored in the database through the cascading selects

## Database Integration

The form now uses the existing geographic reference data:
- **ProvAdmin** - Provinces (pre-filled from ligue)
- **TerritoireVille** - Territories/Cities
- **SecteurCommune** - Sectors/Communes
- **GroupementQuartier** - Groupements/Quarters

All data is fetched dynamically via API endpoints:
- `/parametres-geographiques/api/provinces/`
- `/parametres-geographiques/api/territoires/?province={id}`
- `/parametres-geographiques/api/secteurs/?territoire={id}`
- `/parametres-geographiques/api/groupements/?secteur={id}`

## User Experience

1. **Province Pre-filled**: The province field is automatically set to the ligue's province
2. **Cascading Selects**: Each location level depends on the previous one
3. **Loading States**: Users see "Chargement..." while data is being fetched
4. **Disabled States**: Dependent selects are disabled until their parent is selected
5. **Error Handling**: If API calls fail, users see "Erreur de chargement"

## Design Consistency

- All new fields follow the same styling as federation creation form
- Blue Royal (#0036ca) color scheme maintained
- Cascading behavior matches federation form exactly
- Form validation consistent with federation form
- Error handling and user feedback aligned

## Testing Recommendations

1. Test province pre-filling on form load
2. Test cascading selects for each level
3. Verify API calls are made correctly
4. Test error handling when API fails
5. Verify session data is stored correctly
6. Test club creation with all location fields
7. Verify AdresseContact is created with correct data
8. Test form validation for required fields

## Files Modified

1. `gouvernance/forms.py` - ClubAddressForm updated with location fields
2. `gouvernance/views_ligue_secretary.py` - Views updated to handle location data
3. `templates/gouvernance/ligue_club_create.html` - Template with cascading selects and JavaScript

## API Endpoints Used

The form relies on existing API endpoints from the geographic reference module:
- `GET /parametres-geographiques/api/provinces/` - List all provinces
- `GET /parametres-geographiques/api/territoires/?province={id}` - Territories for a province
- `GET /parametres-geographiques/api/secteurs/?territoire={id}` - Sectors for a territory
- `GET /parametres-geographiques/api/groupements/?secteur={id}` - Groupements for a sector

These endpoints should already exist in the referentiel_geo app.

## Notes

- Province is pre-filled and required for club creation
- All other location fields are optional but cascade properly
- The form maintains the same 3-step structure
- Location data is properly stored in session between steps
- AdresseContact is created with avenue and numero (not commune)
- The implementation matches the federation creation form exactly
