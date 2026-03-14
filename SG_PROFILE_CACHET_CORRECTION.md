# SG Profile - Cachet Correction

**Date**: March 4, 2026  
**Status**: ✅ UPDATED

---

## Correction Applied

### Issue
The SG profile template incorrectly labeled the second upload section as "Sceau du Ministère" (Ministry Seal). However, the SG should upload their **personal cachet** (not the ministry seal).

### Clarification
- **Ministry Seal**: Used on all official documents (shared resource)
- **SG Personal Cachet**: Uploaded by SG to identify their signatures
- **Signature**: SG's handwritten signature

### Changes Made

**File**: `templates/gouvernance/profil_sg.html`

1. **Section Title**:
   - Changed from: "Sceau du Ministère"
   - Changed to: "Cachet Personnel"

2. **Section Description**:
   - Added: "Votre cachet personnel pour identifier vos signatures officielles"
   - Added info box explaining the purpose

3. **Page Header**:
   - Changed from: "Gestion de votre signature et sceau du ministère"
   - Changed to: "Gestion de votre signature et cachet personnel"

4. **Button Label**:
   - Changed from: "Mettre à jour le sceau"
   - Changed to: "Mettre à jour le cachet"

---

## How It Works

### SG Profile Upload
```
SG Profile Page
├── Signature (PNG)
│   └── SG's handwritten signature
└── Cachet Personnel (PNG)
    └── SG's personal seal/stamp
```

### Document Generation
```
Attestation d'Homologation
├── Ministry Seal (fixed on all documents)
├── SG Signature (from profile)
└── SG Cachet (from profile)
```

---

## Technical Details

### Fields Used
- `profil.signature_image` - SG's signature
- `profil.sceau_image` - SG's personal cachet

### Storage
- Both stored in media/signatures/ folder
- PNG format, max 5MB each
- Password-protected uploads

### Usage in Attestation
- Signature displayed near SG title
- Cachet displayed next to signature
- Both identify the SG who approved the ligue

---

## Workflow

1. **SG uploads profile**:
   - Signature: Personal handwritten signature
   - Cachet: Personal seal/stamp

2. **SG approves ligue**:
   - System generates attestation PDF
   - Includes ministry seal (fixed)
   - Includes SG signature (from profile)
   - Includes SG cachet (from profile)

3. **Ligue receives attestation**:
   - Document shows who approved it
   - SG's signature and cachet visible
   - Ministry seal present

4. **Public verification**:
   - QR code links to verification page
   - Shows attestation details
   - Confirms authenticity

---

## Security

✅ Password-protected uploads  
✅ PNG format validation  
✅ File size limits (5MB)  
✅ Role-based access  
✅ Unique identification of SG  

---

## Summary

The SG profile now correctly handles:
- **Signature**: Personal handwritten signature
- **Cachet**: Personal seal/stamp for identification

Both are used to identify the SG who approved official documents.

---

**Correction completed successfully!** ✅
