# Ligue Status Consolidation - Single Status Display

## Overview
Updated the ligue status display to show a single consolidated status instead of separate inspection and signature statuses. The status now clearly shows the ligue's position in the validation workflow.

## Status Workflow

### 1. **Inspection** (Yellow)
```
Ligue Created
    ↓
statut_inspection = 'EN_INSPECTION'
statut_signature = 'ATTENTE_SIGNATURE'
    ↓
Display: "Inspection"
```
- Ligue is waiting for Division Provinciale validation
- Division must validate the ligue before it can proceed to SG

### 2. **Attente SG** (Orange)
```
Division Validates
    ↓
statut_inspection = 'INSPECTION_VALIDEE'
statut_signature = 'ATTENTE_SIGNATURE'
    ↓
Display: "Attente SG"
```
- Division Provinciale has validated the ligue
- Ligue is now waiting for Secrétaire Général approval
- SG must approve before ligue becomes active

### 3. **Validée** (Green)
```
SG Approves
    ↓
statut_inspection = 'INSPECTION_VALIDEE'
statut_signature = 'SIGNE'
statut_activation = 'ACTIVE'
    ↓
Display: "Validée"
```
- Both Division Provinciale AND Secrétaire Général have validated
- Ligue is now officially recognized
- Ligue becomes ACTIVE and can operate normally

### 4. **Rejetée** (Red)
```
Division OR SG Rejects
    ↓
statut_inspection = 'INSPECTION_REJETEE' OR statut_signature = 'REFUSE'
    ↓
Display: "Rejetée"
```
- Either Division Provinciale or Secrétaire Général rejected the ligue
- Ligue cannot proceed further
- Federation Secretary must address issues and resubmit

## Changes Made

### 1. Template Update (`templates/gouvernance/federation_ligues_list.html`)

**Removed:**
- Separate "Validation" column showing inspection and signature separately
- Separate "Statut" column showing activation status

**Added:**
- Single consolidated "Statut" column showing the ligue's current position in workflow

**Status Display Logic:**
```django
{% if ligue.statut_signature == 'SIGNE' %}
    → "Validée" (Green)
{% elif ligue.statut_signature == 'ATTENTE_SIGNATURE' %}
    → "Attente SG" (Orange)
{% elif ligue.statut_inspection == 'EN_INSPECTION' %}
    → "Inspection" (Yellow)
{% elif ligue.statut_inspection == 'INSPECTION_REJETEE' or ligue.statut_signature == 'REFUSE' %}
    → "Rejetée" (Red)
{% else %}
    → "Inconnu" (Gray)
{% endif %}
```

### 2. Model Update (`gouvernance/models/validation_ligue.py`)

**Updated `AttestationReconnaissance.approuver()` method:**
- Now sets `statut_activation = 'ACTIVE'` when ligue is approved
- This ensures the ligue becomes active only after full validation

```python
def approuver(self, numero_attestation):
    # ... existing code ...
    self.ligue.statut_activation = 'ACTIVE'  # ← NEW
    self.ligue.save()
```

## User Experience

### For Federation Secretary
When viewing the ligues list:
1. See federation's validation status at the top
2. See each ligue's single consolidated status
3. Understand exactly where each ligue is in the workflow
4. Know what action is needed next for each ligue

### Status Progression
```
Ligue Created
    ↓
[Inspection] ← Waiting for Division
    ↓
[Attente SG] ← Waiting for SG (after Division approves)
    ↓
[Validée] ← Fully approved, now ACTIVE
```

### Visual Indicators
- **Yellow** = Waiting for Division Provinciale
- **Orange** = Waiting for Secrétaire Général
- **Green** = Fully validated and active
- **Red** = Rejected

## Database Impact

### Ligue Status Fields
```
statut_inspection:
  - EN_INSPECTION (initial)
  - INSPECTION_VALIDEE (after Division approves)
  - INSPECTION_REJETEE (if Division rejects)

statut_signature:
  - ATTENTE_SIGNATURE (initial)
  - SIGNE (after SG approves)
  - REFUSE (if SG rejects)

statut_activation:
  - ACTIVE (after SG approves)
  - INACTIF (default or if rejected)
```

## Workflow Validation

### Division Provinciale Validation
- Checks: clubs_existent, structure_valide, dirigeants_credibles
- Updates: statut_inspection = 'INSPECTION_VALIDEE'
- Ligue moves to "Attente SG" status

### Secrétaire Général Approval
- Reviews Division's validation
- Generates attestation number
- Updates: statut_signature = 'SIGNE'
- Updates: statut_activation = 'ACTIVE'
- Ligue moves to "Validée" status

## Testing Checklist

✅ Ligue created shows "Inspection" status
✅ After Division validates, shows "Attente SG" status
✅ After SG approves, shows "Validée" status
✅ Rejected ligues show "Rejetée" status
✅ Federation status badge displays correctly
✅ Colors match RDC color scheme
✅ Icons are appropriate for each status
✅ Layout is responsive on mobile
✅ statut_activation is set to ACTIVE when approved

## Files Modified

1. `templates/gouvernance/federation_ligues_list.html`
   - Consolidated status column
   - Single status display logic
   - Removed separate validation/activation columns

2. `gouvernance/models/validation_ligue.py`
   - Updated `approuver()` method to set `statut_activation = 'ACTIVE'`

## Future Enhancements

- Add filtering by status (Inspection, Attente SG, Validée, Rejetée)
- Add sorting by status
- Add bulk actions for ligues with same status
- Add status change notifications
- Add audit trail for status changes
- Add estimated time to next status

---

**Status**: ✅ IMPLEMENTED
**Date**: March 3, 2026
**Version**: 1.0

## Summary

The ligue status system now shows a single, clear status that represents the ligue's position in the validation workflow:
- **Inspection** → Waiting for Division Provinciale
- **Attente SG** → Waiting for Secrétaire Général
- **Validée** → Fully approved and ACTIVE
- **Rejetée** → Rejected

This makes it much easier for Federation Secretaries to understand the status of their ligues at a glance.
