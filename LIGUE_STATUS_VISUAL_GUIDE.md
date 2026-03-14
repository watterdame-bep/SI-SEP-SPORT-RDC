# Ligue Status - Visual Guide

## Status Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIGUE CREATION WORKFLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. LIGUE CREATED
   ├─ statut_inspection: EN_INSPECTION
   ├─ statut_signature: ATTENTE_SIGNATURE
   ├─ statut_activation: ACTIVE (initially)
   └─ Display: 🔍 Inspection (Yellow)
      └─ Waiting for Division Provinciale validation

2. DIVISION VALIDATES ✓
   ├─ statut_inspection: INSPECTION_VALIDEE
   ├─ statut_signature: ATTENTE_SIGNATURE
   ├─ statut_activation: ACTIVE
   └─ Display: ⏳ Attente SG (Orange)
      └─ Waiting for Secrétaire Général approval

3. SG APPROVES ✓
   ├─ statut_inspection: INSPECTION_VALIDEE
   ├─ statut_signature: SIGNE
   ├─ statut_activation: ACTIVE ← SET HERE
   └─ Display: ✅ Validée (Green)
      └─ Fully approved and operational

4. REJECTED (at any stage)
   ├─ statut_inspection: INSPECTION_REJETEE OR
   ├─ statut_signature: REFUSE
   ├─ statut_activation: INACTIF
   └─ Display: ❌ Rejetée (Red)
      └─ Needs correction and resubmission
```

## Status Display in Ligues List

```
┌──────────────────────────────────────────────────────────────────────┐
│ Ligues Provinciales                    [Federation: Validée ✅]      │
│ Federation Name                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Ligue | Province | Contact | Responsable | Statut                   │
├──────────────────────────────────────────────────────────────────────┤
│ Ligue 1 │ Kinshasa │ ... │ ... │ 🔍 Inspection (Yellow)            │
│ Ligue 2 │ Kasai    │ ... │ ... │ ⏳ Attente SG (Orange)            │
│ Ligue 3 │ Katanga  │ ... │ ... │ ✅ Validée (Green)               │
│ Ligue 4 │ Kinshasa │ ... │ ... │ ❌ Rejetée (Red)                 │
└──────────────────────────────────────────────────────────────────────┘
```

## Color Coding

| Status | Color | Icon | Meaning |
|--------|-------|------|---------|
| Inspection | 🟨 Yellow | 🔍 | Waiting for Division Provinciale |
| Attente SG | 🟧 Orange | ⏳ | Waiting for Secrétaire Général |
| Validée | 🟩 Green | ✅ | Fully approved and ACTIVE |
| Rejetée | 🟥 Red | ❌ | Rejected, needs correction |

## Status Transitions

### Happy Path (Successful Validation)
```
Created
  ↓
Inspection (Yellow)
  ↓ [Division approves]
Attente SG (Orange)
  ↓ [SG approves]
Validée (Green) ← statut_activation = ACTIVE
```

### Rejection Path
```
Created
  ↓
Inspection (Yellow)
  ↓ [Division rejects]
Rejetée (Red) ← statut_activation = INACTIF
  ↓ [Federation corrects and resubmits]
Inspection (Yellow) [again]
```

## Key Points

### When Ligue Becomes ACTIVE
- **Before**: Ligue is created with `statut_activation = ACTIVE` (for display purposes)
- **After SG Approval**: Explicitly set to `ACTIVE` when fully validated
- **On Rejection**: Set to `INACTIF` if rejected

### Status Display Priority
1. Check `statut_signature` first (highest priority)
   - If `SIGNE` → "Validée"
   - If `ATTENTE_SIGNATURE` → Check inspection status
   - If `REFUSE` → "Rejetée"

2. Check `statut_inspection` second
   - If `EN_INSPECTION` → "Inspection"
   - If `INSPECTION_REJETEE` → "Rejetée"

3. Default → "Inconnu"

## Federation Status Context

The federation's status is displayed at the top of the page:

```
Federation Status:
├─ Validée (Green) ✅ → Can create and validate ligues
├─ En attente (Yellow) ⏳ → Can create ligues, validation pending
├─ Rejetée (Red) ❌ → Cannot validate ligues
└─ Non validée (Gray) ❓ → Not yet submitted
```

## User Actions by Status

### Inspection Status
- **Federation Secretary**: Can view, edit, delete ligue
- **Division Provinciale**: Must validate or reject
- **SG**: Cannot act yet

### Attente SG Status
- **Federation Secretary**: Can view ligue
- **Division Provinciale**: Cannot act
- **SG**: Must approve or reject

### Validée Status
- **Federation Secretary**: Can view, use ligue
- **Division Provinciale**: Cannot act
- **SG**: Cannot act (already approved)

### Rejetée Status
- **Federation Secretary**: Must correct and resubmit
- **Division Provinciale**: Cannot act
- **SG**: Cannot act

---

**Visual Guide Version**: 1.0
**Date**: March 3, 2026
