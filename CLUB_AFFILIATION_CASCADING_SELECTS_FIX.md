# Club Affiliation - Cascading Selects Fix

## Problem Statement
The club creation form (Step 2) had the following issues:
1. Province field was clickable when it should be disabled and read-only
2. Territories, sectors, and groupements were not loading automatically
3. Form submission was failing because disabled fields don't submit their values
4. JavaScript syntax error due to duplicate code

## Solution Implemented

### 1. Province Field - Read-Only Display
**File**: `templates/gouvernance/ligue_club_create.html`

- Added `disabled` attribute to the province select to prevent user interaction
- Added visual feedback with `bg-slate-100 cursor-not-allowed` classes
- Added helper text: "Province de la ligue (non modifiable)"

### 2. Hidden Input for Form Submission
**File**: `templates/gouvernance/ligue_club_create.html`

Since disabled form fields don't submit their values, we added:
```html
<input type="hidden" id="province-hidden" name="province">
```

This hidden input receives the province value from JavaScript and ensures it's submitted with the form.

### 3. JavaScript Initialization
**File**: `templates/gouvernance/ligue_club_create.html`

Updated the JavaScript to:
1. Pre-fill the province select with the ligue's province (from template context)
2. Populate the hidden input field with the province ID
3. Automatically load territories on page load (no manual selection needed)
4. Enable cascading selects: territoire → secteur → groupement

```javascript
// Pre-fill province and hidden input
if (liueProvinceId && liueProvinceId.trim() !== '') {
    // Create option for province
    provinceSelect.innerHTML = '';
    const option = document.createElement('option');
    option.value = liueProvinceId;
    option.textContent = liueProvinceName;
    option.selected = true;
    provinceSelect.appendChild(option);
    
    // Fill hidden input for form submission
    if (provinceHidden) {
        provinceHidden.value = liueProvinceId;
    }
    
    // Trigger territories loading immediately
    setTimeout(() => {
        loadTerritoires(liueProvinceId);
    }, 100);
}
```

### 4. Fixed Duplicate Code
**File**: `templates/gouvernance/ligue_club_create.html`

Removed duplicate cascading select code that was causing JavaScript syntax error:
- Removed duplicate `loadTerritoires()` function definition
- Removed duplicate event listeners for territoire, secteur, and groupement selects
- Kept only one clean implementation of the cascading logic

### 5. API Endpoints
**File**: `referentiel_geo/views.py`

The following API endpoints are already implemented and accessible to all logged-in users:
- `/parametres-geographiques/api/territoires/?province={province_id}` - Returns territories for a province
- `/parametres-geographiques/api/secteurs/?territoire={territoire_id}` - Returns sectors for a territory
- `/parametres-geographiques/api/groupements/?secteur={secteur_id}` - Returns groupements for a sector

These endpoints return data in the format:
```json
[
  {"uid": "uuid", "designation": "name"},
  ...
]
```

### 6. Form Handling
**File**: `gouvernance/forms.py`

The `ClubAddressForm` correctly:
- Pre-fills the province field with the ligue's province in `__init__`
- Accepts the cascading select values (territoire, secteur, groupement_quartier) as CharField inputs
- Validates all required fields

### 7. View Context
**File**: `gouvernance/views_ligue_secretary.py`

The `ligue_club_create_step2` view passes:
- `province_id`: UUID of the ligue's province
- `province_name`: Name of the ligue's province

These are used by JavaScript to pre-fill and initialize the cascading selects.

## User Experience Flow

1. **Page Load (Step 2)**:
   - Province select is pre-filled with ligue's province (disabled, not clickable)
   - Territories automatically load for that province
   - Sectors and groupements remain disabled until user selects a territory

2. **User Interaction**:
   - User selects a territory → sectors load automatically
   - User selects a sector → groupements load automatically
   - User selects a groupement → form is ready to submit

3. **Form Submission**:
   - Province value is submitted via hidden input
   - All cascading select values are submitted
   - Form validation passes and club is created

## Testing Checklist

- [x] JavaScript syntax error fixed (removed duplicate code)
- [ ] Province field displays correctly and is not clickable
- [ ] Province field shows the ligue's province name
- [ ] Territories load automatically on page load
- [ ] Cascading selects work: territoire → secteur → groupement
- [ ] Form submission includes all required fields
- [ ] Club is created successfully with correct localization data
- [ ] Browser console shows no errors

## Files Modified

1. `templates/gouvernance/ligue_club_create.html`
   - Added hidden input for province: `<input type="hidden" id="province-hidden" name="province">`
   - Updated JavaScript initialization to populate hidden input
   - Ensured cascading selects work properly
   - Fixed duplicate code that was causing JavaScript syntax error

2. No changes needed to:
   - `gouvernance/views_ligue_secretary.py` (already correct)
   - `gouvernance/forms.py` (already correct)
   - `referentiel_geo/views.py` (already correct)
   - `referentiel_geo/urls.py` (already correct)

## Notes

- The implementation uses UUID as the primary key for geographic entities (ProvAdmin, TerritoireVille, etc.)
- API endpoints are accessible to all logged-in users (not just SG)
- The cascading selects use query parameters for API calls: `?province=...`, `?territoire=...`, `?secteur=...`
- The form uses session storage to persist data across the 3-step creation process
- The hidden input ensures the province value is submitted even though the select is disabled
