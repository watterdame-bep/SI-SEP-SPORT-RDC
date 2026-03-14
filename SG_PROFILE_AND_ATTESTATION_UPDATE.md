# SG Profile & Attestation Update - Implementation Summary

**Date**: March 4, 2026  
**Status**: ✅ COMPLETED

---

## Overview

This update implements two major features for the Secrétaire Général (SG) role:

1. **Updated Attestation d'Homologation Provinciale** - Official RDC text format with legal compliance
2. **SG Profile Interface** - Signature and seal management (identical to Minister profile)

---

## Changes Made

### 1. Updated Attestation PDF Generator

**File**: `gouvernance/certificate_generator.py`

**Function**: `generer_attestation_homologation_ligue()`

**Key Updates**:
- ✅ Official RDC header: "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO"
- ✅ Ministry branding: "MINISTÈRE DES SPORTS ET LOISIRS"
- ✅ Official title: "ATTESTATION D'HOMOLOGATION PROVINCIALE"
- ✅ Numbering format: `N° MSL/SG/{{ID_UNIQUE}}/2026`
- ✅ Legal references:
  - VU la Loi n°11/023 du 24 décembre 2011
  - VU l'Arrêté Ministériel portant agrément de la Fédération
  - VU le rapport de viabilité favorable
- ✅ "ATTESTE PAR LA PRÉSENTE" section
- ✅ Executive board member names (from ligue organigramme)
- ✅ Province and discipline information
- ✅ Validity statement for current season
- ✅ Signature space with title: "Le Secrétaire Général aux Sports et Loisirs"
- ✅ QR code for verification (bottom left)
- ✅ RDC color scheme (Bleu Royal, Jaune Drapeau, Rouge Drapeau)

**Technical Details**:
- Uses ReportLab for PDF generation
- A4 format with professional borders
- Proper spacing and typography
- Handles long text wrapping
- Includes QR code for document verification

---

### 2. SG Profile Interface

**New Files Created**:
- `templates/gouvernance/profil_sg.html` - SG profile template

**Files Modified**:
- `gouvernance/views_courriers.py` - Added `profil_sg()` view
- `gouvernance/urls.py` - Added SG profile URL route
- `templates/core/base.html` - Added SG profile menu links

**Features**:
- ✅ Identical layout to Minister profile
- ✅ Signature upload (PNG transparent, max 5MB)
- ✅ Seal upload (PNG transparent, max 5MB)
- ✅ Password-protected modifications
- ✅ File validation (PNG format, size limits)
- ✅ User-friendly upload interface
- ✅ Current file display with preview
- ✅ Modal dialogs for security confirmation
- ✅ Success/error messages

**Access Points**:
1. **Sidebar Menu** (for SG role):
   - "Paramètres" section → "Mon Profil"
   
2. **User Dropdown Menu** (top-right):
   - "Mon Profil (Signature & Sceau)"

**URL Route**:
- `gouvernance:profil_sg` → `/gouvernance/profil/sg/`

---

## Implementation Details

### Attestation Document Structure

```
┌─────────────────────────────────────────┐
│  BORDURE BLEU ROYAL (2pt)               │
│  ┌───────────────────────────────────┐  │
│  │ BORDURE JAUNE DRAPEAU (1pt)       │  │
│  │                                   │  │
│  │ RÉPUBLIQUE DÉMOCRATIQUE DU CONGO  │  │
│  │ MINISTÈRE DES SPORTS ET LOISIRS   │  │
│  │ Secrétariat Général aux Sports    │  │
│  │                                   │  │
│  │ ATTESTATION D'HOMOLOGATION        │  │
│  │ PROVINCIALE                       │  │
│  │ N° MSL/SG/{{ID}}/2026             │  │
│  │                                   │  │
│  │ [VU CLAUSES]                      │  │
│  │ [ATTESTE PAR LA PRÉSENTE]         │  │
│  │ [LIGUE DETAILS]                   │  │
│  │ [EXECUTIVE BOARD]                 │  │
│  │ [VALIDITY STATEMENT]              │  │
│  │                                   │  │
│  │ [QR CODE]  [SIGNATURE SPACE]      │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### SG Profile View Logic

```python
@login_required
@require_role('INSTITUTION_ADMIN')  # SG role
def profil_sg(request):
    # GET: Display profile form
    # POST: Handle file uploads with password verification
    # - Validate PNG format
    # - Check file size (max 5MB)
    # - Verify user password
    # - Save to profil.signature_image or profil.sceau_image
```

---

## Security Features

1. **Password Protection**:
   - All signature/seal modifications require password confirmation
   - Password verified against user account

2. **File Validation**:
   - PNG format only (transparent background)
   - Maximum 5MB file size
   - Content-type verification

3. **Access Control**:
   - SG profile only accessible to INSTITUTION_ADMIN role
   - Login required
   - Role-based access enforcement

---

## Color Scheme (RDC Compliance)

| Element | Color | Code |
|---------|-------|------|
| Primary Borders | Bleu Royal | #0036ca |
| Accent Borders | Jaune Drapeau | #FDE015 |
| Error/Danger | Rouge Drapeau | #ED1C24 |
| Text | Noir | #000000 |
| Background | Gris clair | #f8f9fa |

---

## Testing Checklist

- [ ] SG can access profile page via sidebar menu
- [ ] SG can access profile page via user dropdown menu
- [ ] Signature upload works (PNG format)
- [ ] Seal upload works (PNG format)
- [ ] File size validation works (reject > 5MB)
- [ ] Format validation works (reject non-PNG)
- [ ] Password verification works
- [ ] Attestation PDF generates with official text
- [ ] Attestation includes all required legal clauses
- [ ] Attestation displays ligue details correctly
- [ ] Attestation displays executive board members
- [ ] QR code generates and displays
- [ ] Document numbering format is correct
- [ ] RDC colors are applied correctly

---

## Files Modified

1. **gouvernance/certificate_generator.py**
   - Updated `generer_attestation_homologation_ligue()` function
   - Removed duplicate function definition

2. **gouvernance/views_courriers.py**
   - Added `profil_sg()` view function

3. **gouvernance/urls.py**
   - Added URL route: `path('profil/sg/', views_courriers.profil_sg, name='profil_sg')`

4. **templates/core/base.html**
   - Added SG profile menu in sidebar (Paramètres section)
   - Added SG profile link in user dropdown menu

5. **templates/gouvernance/profil_sg.html** (NEW)
   - Complete SG profile interface template
   - Identical to minister profile template
   - Signature and seal upload forms
   - Password confirmation modal
   - File preview and validation

---

## Next Steps (Optional Enhancements)

1. **Integrate Ministry Seal into Attestation PDF**:
   - Load seal image from profil.sceau_image
   - Display seal image on attestation document
   - Position seal near signature area

2. **Add SG Signature to Attestation**:
   - Load signature image from profil.signature_image
   - Display signature on attestation document
   - Position signature in designated area

3. **Email Notifications**:
   - Send attestation to ligue email
   - Include PDF attachment
   - Confirmation message to SG

4. **Document Verification**:
   - Implement QR code verification page
   - Display attestation details
   - Verify document authenticity

---

## Notes

- The attestation PDF now follows official RDC administrative format
- All legal references are included as per user requirements
- SG profile interface is identical to Minister profile for consistency
- Both signature and seal are stored in the same profil_sisep model
- Password protection ensures only authorized personnel can modify official documents
- The implementation maintains RDC color scheme throughout

---

## Deployment Instructions

1. Run migrations (if any new fields were added to models)
2. Restart Django application
3. Test SG profile access
4. Test attestation PDF generation
5. Verify all URLs are accessible
6. Check sidebar menu displays correctly for SG role

---

**Implementation completed successfully!** ✅
