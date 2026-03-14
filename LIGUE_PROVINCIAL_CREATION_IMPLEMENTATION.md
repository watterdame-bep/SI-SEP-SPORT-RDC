# Ligue Provinciale Creation Implementation

## Overview
Implemented a complete system for federation secretaries to create provincial ligues (sub-organizations) within their federation.

## Key Features

### 1. Form (`CreerLigueProvincialForm`)
Located in: `gouvernance/forms.py`

**Fields:**
- **Province Administrative**: Dropdown selection from 26 provinces
- **Nom de la Ligue**: Name of the provincial league
- **Sigle**: Optional abbreviation (auto-generated if not provided)
- **Nom du Président Provincial**: Name of the provincial president
- **Email de contact**: Contact email (validated for uniqueness)
- **Téléphone**: Optional phone number

**Styling:**
- Tailwind CSS classes for consistency
- RDC color scheme (Bleu Royal focus)
- Responsive design

### 2. View (`create_ligue_provincial`)
Located in: `gouvernance/views_federation_secretary.py`

**Functionality:**
- Requires FEDERATION_SECRETARY role
- Validates federation association
- Creates Institution object with:
  - `niveau_territorial='LIGUE'`
  - `institution_tutelle=federation` (establishes parent-child relationship)
  - `province_admin=selected_province`
  - `statut_activation='ACTIVE'` by default
  - Auto-generated unique code: `LIGUE-{FEDERATION_SIGLE}-{PROVINCE_CODE}`

**Data Mapping:**
- Form field → Institution model field
- `nom_ligue` → `nom_officiel`
- `sigle_ligue` → `sigle`
- `nom_president` → `nom_president`
- `email_contact` → `email_officiel`
- `telephone_contact` → `telephone_off`

### 3. Template (`create_ligue_provincial.html`)
Located in: `templates/gouvernance/create_ligue_provincial.html`

**Design:**
- Professional gradient header with RDC colors
- Icon-based field labels
- Consistent with federation secretary interface
- Responsive layout (mobile-first)
- Helpful information box with key points

**User Experience:**
- Clear form structure
- Error messages for each field
- Cancel and Submit buttons
- Informational sidebar explaining the process

### 4. URL Route
Added to: `gouvernance/urls.py`

```python
path('federation/ligues/create/', views_federation_secretary.create_ligue_provincial, name='create_ligue_provincial'),
```

### 5. Integration with Ligues List
Updated: `templates/gouvernance/federation_ligues_list.html`

- "Nouvelle Ligue" button now redirects to creation form
- Button styling: Bleu Royal with hover effect
- Responsive design (full width on mobile, auto on desktop)

## Database Structure

### Institution Model Relationships
```
Federation (parent)
    ↓ institution_tutelle
Ligue (child)
    - niveau_territorial: 'LIGUE'
    - province_admin: ProvAdmin (26 provinces)
    - institution_tutelle: Federation (FK)
    - statut_activation: 'ACTIVE'
```

### Key Fields
- `code`: Auto-generated unique identifier (LIGUE-{FED_SIGLE}-{PROV_CODE})
- `nom_officiel`: League name
- `sigle`: Optional abbreviation
- `institution_tutelle`: Reference to parent federation
- `province_admin`: Reference to province
- `nom_president`: Provincial president name
- `email_officiel`: Contact email
- `telephone_off`: Contact phone

## Validation

### Form Validation
1. **Province**: Required, must exist in database
2. **Nom de la Ligue**: Required, max 255 characters
3. **Nom du Président**: Required, max 255 characters
4. **Email**: Required, must be unique (not already in User table)
5. **Sigle**: Optional, max 50 characters
6. **Téléphone**: Optional, max 50 characters

### Business Logic Validation
1. User must be FEDERATION_SECRETARY
2. User must be associated with a federation
3. Code uniqueness check (prevents duplicate ligues for same province)
4. Email uniqueness check (prevents duplicate user accounts)

## Error Handling

### User-Friendly Messages
- Success: "Ligue provinciale '{nom}' créée avec succès."
- Error: Specific field errors displayed inline
- Validation errors: Clear messages for each constraint

### Redirect Behavior
- Success: Redirects to federation ligues list
- Error: Stays on form with error messages

## Security

### Access Control
- `@login_required`: User must be authenticated
- `@require_role('FEDERATION_SECRETARY')`: Only federation secretaries can create ligues
- Federation validation: Ensures user is associated with a federation

### Data Protection
- CSRF token required for form submission
- Email uniqueness validation prevents account conflicts
- Code uniqueness prevents duplicate ligues

## Files Modified/Created

### Created
1. `templates/gouvernance/create_ligue_provincial.html` - Creation form template
2. `LIGUE_PROVINCIAL_CREATION_IMPLEMENTATION.md` - This documentation

### Modified
1. `gouvernance/forms.py` - Added `CreerLigueProvincialForm`
2. `gouvernance/views_federation_secretary.py` - Added `create_ligue_provincial` view
3. `gouvernance/urls.py` - Added URL route
4. `templates/gouvernance/federation_ligues_list.html` - Updated button to link to form

## Usage Flow

1. Federation secretary clicks "Nouvelle Ligue" button on ligues list
2. Redirected to creation form
3. Selects province from dropdown (26 options)
4. Enters ligue name, president name, and contact email
5. Optionally enters sigle and phone number
6. Submits form
7. System validates all fields
8. Creates Institution object with federation as parent
9. Redirects to ligues list with success message
10. New ligue appears in the list

## Future Enhancements

- Edit ligue functionality
- Delete ligue functionality
- Bulk import of ligues
- Ligue detail view
- Ligue member management
- Ligue document uploads
- Ligue status management (activate/deactivate)

## Color Scheme (RDC Compliant)

- **Bleu Royal (#0036ca)**: Primary color for headers, buttons, icons
- **Jaune Drapeau (#FDE015)**: Accent color (used sparingly)
- **Green**: Success messages and badges
- **Red**: Error messages and delete actions
- **Gray**: Neutral elements and inactive states
