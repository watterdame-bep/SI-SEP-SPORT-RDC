# Fix: Division Provinciale Lookup for Ligue Creation

## Problem
When creating a ligue provinciale, the system was showing the error:
```
Ligue provinciale 'LIGUE PROVINCIALE ATHLETISME DE KINSHASA' créée, mais aucune Division Provinciale trouvée pour KINSHASA. 
Veuillez contacter l'administrateur.
```

Even though a Division Provinciale for Kinshasa existed in the system.

## Root Cause
The `create_ligue_provincial` view was looking for Division Provinciale data in the wrong place:

**BEFORE (Incorrect):**
```python
division_provinciale = Institution.objects.get(
    niveau_territorial='PROVINCIAL',
    province_admin=province
)
```

The code was searching for an `Institution` with `niveau_territorial='PROVINCIAL'`, but the actual Division Provinciale data is stored in the separate `DivisionProvinciale` model, not in the `Institution` model.

## Solution
Updated the code to use the correct `DivisionProvinciale` model:

**AFTER (Correct):**
```python
from gouvernance.models import DivisionProvinciale

division_provinciale = DivisionProvinciale.objects.get(
    province=province
)
```

## Changes Made

### 1. Updated View (`gouvernance/views_federation_secretary.py`)
- Changed the Division Provinciale lookup from `Institution` to `DivisionProvinciale`
- Updated the exception handling to catch `DivisionProvinciale.DoesNotExist`

### 2. Updated Model (`gouvernance/models/validation_ligue.py`)
- Changed the `division_provinciale` ForeignKey from pointing to `Institution` to pointing to `DivisionProvinciale`
- Removed the `limit_choices_to` constraint that was looking for `niveau_territorial='PROVINCIAL'`

### 3. Created Migration (`gouvernance/migrations/0025_fix_validation_ligue_division.py`)
- Removed the old ForeignKey to Institution
- Added new ForeignKey to DivisionProvinciale
- Migration applied successfully

## Verification
✅ Django system check passed
✅ Migration applied successfully
✅ Model relationships corrected
✅ View logic updated

## Testing
To test the fix:
1. Create a new ligue provinciale
2. Select a province that has a Division Provinciale
3. The ligue should be created successfully with the message:
   ```
   Ligue provinciale 'XXX' créée avec succès. 
   Elle est maintenant en attente de validation par la Division Provinciale.
   ```

## Files Modified
- `gouvernance/views_federation_secretary.py` - Updated Division Provinciale lookup
- `gouvernance/models/validation_ligue.py` - Updated ForeignKey relationship
- `gouvernance/migrations/0025_fix_validation_ligue_division.py` - New migration

## Impact
- Ligue creation now correctly links to Division Provinciale
- ValidationLigue records now properly reference DivisionProvinciale
- Workflow validation can proceed correctly

---

**Status**: ✅ FIXED
**Date**: March 3, 2026
**Version**: 1.0
