# SG Role Permission Fix

## Problem
When trying to access the Ligues Provinciales interface, users were getting:
```
Accès refusé. Rôle requis: SECRETAIRE_GENERAL
```

Even though they had the correct SG role assigned.

## Root Cause
The views were checking for the role string `'SECRETAIRE_GENERAL'`, but the actual role value in the system is `'INSTITUTION_ADMIN'`.

### Role Mapping
```
Role Display Name: "Admin Institution (Secrétaire Général — gestionnaire de données)"
Role Value: "INSTITUTION_ADMIN"
```

The `require_role` decorator checks the actual role value, not the display name.

## Solution
Updated all SG ligue views to use the correct role value: `'INSTITUTION_ADMIN'`

### Files Modified
- `gouvernance/views_sg_ligues.py`

### Changes Made

#### Before (Incorrect)
```python
@require_role('SECRETAIRE_GENERAL')
def sg_ligues_en_attente(request):
    ...
```

#### After (Correct)
```python
@require_role('INSTITUTION_ADMIN')
def sg_ligues_en_attente(request):
    ...
```

### Views Updated
1. `sg_ligues_en_attente()` - List pending ligues
2. `sg_ligue_detail()` - View ligue details
3. `sg_approuver_ligue()` - Approve ligue
4. `sg_rejeter_ligue()` - Reject ligue

## Role System

### Available Roles
```python
class RoleUtilisateur(models.TextChoices):
    SYSTEM_SUPER_ADMIN = 'SYSTEM_SUPER_ADMIN'
    INSTITUTION_ADMIN = 'INSTITUTION_ADMIN'  # ← Secrétaire Général
    MINISTRE = 'MINISTRE'
    DIRECTEUR_CABINET = 'DIRECTEUR_CABINET'
    DIRECTEUR_PROVINCIAL = 'DIRECTEUR_PROVINCIAL'
    FEDERATION_SECRETARY = 'FEDERATION_SECRETARY'
```

### Role Permissions
- **INSTITUTION_ADMIN**: Secrétaire Général (SG)
  - Access: Gestion Administrative, Institutions Sportives, Ligues Provinciales
  - Can: Create federations, manage divisions, validate ligues

- **MINISTRE**: Minister
  - Access: Parapheur Électronique, Arrêtés Signés
  - Can: Sign documents, approve federations

- **DIRECTEUR_PROVINCIAL**: Provincial Director
  - Access: Opérations Terrain, Enquêtes de Viabilité
  - Can: Validate federations at provincial level

- **FEDERATION_SECRETARY**: Federation Secretary
  - Access: Gestion Fédération, Ligues Provinciales
  - Can: Create ligues, manage federation

## Testing

### Before Fix
```
User: SG Account
Role: INSTITUTION_ADMIN
Access: Ligues Provinciales
Result: ❌ Accès refusé. Rôle requis: SECRETAIRE_GENERAL
```

### After Fix
```
User: SG Account
Role: INSTITUTION_ADMIN
Access: Ligues Provinciales
Result: ✅ Access granted
```

## Verification Checklist

✅ All SG views use `@require_role('INSTITUTION_ADMIN')`
✅ Role value matches RoleUtilisateur.INSTITUTION_ADMIN
✅ SG users can now access ligues interface
✅ Other roles still blocked correctly
✅ No other views affected

## How to Verify

1. Log in as SG user
2. Navigate to: Institutions Sportives → Ligues Provinciales
3. Should see list of pending ligues
4. Should be able to view, approve, or reject ligues

## Related Documentation

- `core/permissions.py` - Permission decorators
- `core/models.py` - RoleUtilisateur choices
- `gouvernance/views_sg_ligues.py` - SG ligue views

---

**Status**: ✅ FIXED
**Date**: March 3, 2026
**Version**: 1.0

## Summary

Fixed the role permission issue by updating all SG ligue views to use the correct role value `'INSTITUTION_ADMIN'` instead of `'SECRETAIRE_GENERAL'`. SG users can now access the Ligues Provinciales interface.
