# SG Ligue Status Display Fix

## Problem
The SG ligue list (`sg_ligues_en_attente.html`) had confusing status display logic that didn't clearly reflect the ligue's position in the workflow.

## Root Cause
The status display logic was checking multiple overlapping conditions in the wrong order, causing incorrect status labels to be shown.

## Solution
Simplified and reordered the status display logic to follow the workflow priority:

### Status Display Logic (Priority Order)
1. **Validée** - When `statut_signature == 'SIGNE'` (SG approved)
2. **Rejetée SG** - When `statut_signature == 'REFUSE'` (SG rejected)
3. **En Inspection** - When `statut_inspection == 'EN_INSPECTION'` (Currently with Division)
4. **Attente SG** - When `statut_inspection == 'INSPECTION_VALIDEE'` (Division validated, waiting for SG)
5. **Rejetée Division** - When `statut_inspection == 'INSPECTION_REJETEE'` (Division rejected)
6. **Attente SG** (default) - For any other state (newly created ligues)

### Workflow States
```
Ligue Created
    ↓
    statut_inspection = '' (empty)
    statut_signature = 'ATTENTE_SIGNATURE'
    Display: "Attente SG"
    ↓
SG Transfers to Division
    ↓
    statut_inspection = 'EN_INSPECTION'
    Display: "En Inspection"
    ↓
Division Validates/Rejects
    ↓
    statut_inspection = 'INSPECTION_VALIDEE' or 'INSPECTION_REJETEE'
    Display: "Attente SG" or "Rejetée Division"
    ↓
SG Approves/Rejects
    ↓
    statut_signature = 'SIGNE' or 'REFUSE'
    Display: "Validée" or "Rejetée SG"
```

## Changes Made

### File: `templates/gouvernance/sg_ligues_en_attente.html`

1. **Updated data-statut attribute** (line ~105)
   - Simplified logic to check conditions in priority order
   - Removed redundant `statut_signature == 'ATTENTE_SIGNATURE'` checks
   - Added default "Attente SG" for new ligues

2. **Updated status badge display** (lines ~170-195)
   - Reordered conditions to match priority
   - Clearer status labels:
     - "En Inspection" (yellow) - Division is inspecting
     - "Attente SG" (orange) - Waiting for SG decision
     - "Validée" (green) - SG approved
     - "Rejetée SG" (red) - SG rejected
     - "Rejetée Division" (red) - Division rejected

3. **Updated filter options** (lines ~85-91)
   - Changed "Inspection" to "En Inspection"
   - Added "Rejetée SG" and "Rejetée Division" as separate options
   - Removed generic "Rejetée" option

## Testing Checklist
- [ ] Create a new ligue → Should show "Attente SG"
- [ ] Transfer ligue to Division → Should show "En Inspection"
- [ ] Division validates → Should show "Attente SG"
- [ ] Division rejects → Should show "Rejetée Division"
- [ ] SG approves → Should show "Validée"
- [ ] SG rejects → Should show "Rejetée SG"
- [ ] Filter by status works correctly for all statuses
- [ ] Statistics in header update correctly

## Related Files
- `gouvernance/views_sg_ligues.py` - View that fetches ligues and calculates statistics
- `gouvernance/models/validation_ligue.py` - ValidationLigue model with statut field
- `gouvernance/views_division_ligues.py` - Division validation views that update statut_inspection
