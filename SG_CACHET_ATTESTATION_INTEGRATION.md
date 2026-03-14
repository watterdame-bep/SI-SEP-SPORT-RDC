# SG Cachet Integration in Attestation PDF

**Date**: March 4, 2026  
**Status**: ✅ IMPLEMENTED

---

## What Was Done

### Feature: Display SG Cachet in Attestation PDF

The attestation d'homologation now displays the SG's personal cachet (seal) on the document.

**File Modified**: `gouvernance/certificate_generator.py`

**Function**: `generer_attestation_homologation_ligue()`

---

## How It Works

### Attestation Signature Section

```
Fait à Kinshasa, le DD/MM/YYYY

Le Secrétaire Général aux Sports
et Loisirs,

[SG CACHET IMAGE]
_____________________
Signature & Cachet
```

### Process

1. **SG uploads cachet** in profile page
   - File: `profil.sceau_image`
   - Format: PNG transparent
   - Max size: 5MB

2. **Attestation generation** (when SG approves ligue)
   - System retrieves SG profile
   - Loads cachet image from `profil.sceau_image`
   - Embeds cachet in PDF (1.5cm x 1.5cm)
   - Positions cachet above signature line

3. **Document displays**
   - Cachet shows who approved the ligue
   - Signature line for manual signature
   - Professional appearance

---

## Technical Implementation

### Code Changes

```python
# Load SG profile and cachet
sg_profil = ProfilUtilisateur.objects.filter(role='INSTITUTION_ADMIN').first()

if sg_profil and sg_profil.sceau_image:
    # Draw cachet image on PDF
    c.drawImage(
        sg_profil.sceau_image.path,
        cachet_x,
        cachet_y,
        width=1.5*cm,
        height=1.5*cm
    )
```

### Error Handling

- If SG has no cachet uploaded: Document generates without cachet
- If cachet file not found: Warning logged, document continues
- If image loading fails: Warning logged, document continues

### Positioning

- **X Position**: Right side of page (sig_x + 0.3cm)
- **Y Position**: Below SG title (sig_y - 1.2cm)
- **Size**: 1.5cm x 1.5cm (square format)
- **Spacing**: 1.8cm below cachet for signature line

---

## Visual Layout

```
┌─────────────────────────────────────────┐
│                                         │
│  [ATTESTATION CONTENT]                  │
│                                         │
│  Fait à Kinshasa, le 04/03/2026        │
│                                         │
│  Le Secrétaire Général aux Sports      │
│  et Loisirs,                           │
│                                         │
│  ┌─────────────┐                       │
│  │   CACHET    │                       │
│  │   IMAGE     │                       │
│  │  (1.5x1.5)  │                       │
│  └─────────────┘                       │
│  _____________________                 │
│  Signature & Cachet                    │
│                                         │
└─────────────────────────────────────────┘
```

---

## Requirements

### For SG
1. Must upload cachet in profile page
2. Cachet must be PNG format
3. Cachet must be transparent background
4. File size max 5MB

### For System
1. SG profile must exist
2. SG role must be INSTITUTION_ADMIN
3. Cachet image file must be accessible
4. ReportLab must support image drawing

---

## Testing Checklist

- [x] SG can upload cachet in profile
- [x] Cachet file is stored correctly
- [x] Attestation PDF generates
- [x] Cachet displays on PDF
- [x] Cachet positioned correctly
- [x] Signature line displays below cachet
- [x] Error handling works (no cachet)
- [x] Error handling works (file not found)
- [x] PDF quality is professional

---

## Workflow

### Before Approval
```
SG Profile
└── Upload Cachet (PNG)
    └── Stored in media/signatures/
```

### During Approval
```
SG clicks "Approuver"
└── System generates attestation PDF
    ├── Loads SG profile
    ├── Retrieves cachet image
    ├── Embeds cachet in PDF
    └── Saves PDF to media/institutions/attestations/
```

### After Approval
```
Attestation PDF
├── Contains SG cachet
├── Shows who approved
└── Ready for distribution
```

---

## Security Features

✅ Cachet only from authenticated SG  
✅ Password-protected cachet upload  
✅ File format validation (PNG only)  
✅ File size limits (5MB max)  
✅ Error handling prevents crashes  

---

## Fallback Behavior

If SG has not uploaded a cachet:
- Attestation still generates
- Signature line displays
- No cachet image shown
- Document remains valid
- Warning logged for admin

---

## Future Enhancements

1. **Multiple SG Support**: Handle multiple SG profiles
2. **Signature Integration**: Add SG signature image
3. **Timestamp**: Add digital timestamp
4. **QR Code**: Link to verification page
5. **Audit Trail**: Log all document generations

---

## Deployment

### Files Modified
- `gouvernance/certificate_generator.py`

### No Database Changes Required
- Uses existing `profil.sceau_image` field
- No new migrations needed

### Testing Steps
1. Login as SG
2. Go to profile page
3. Upload cachet (PNG file)
4. Approve a ligue
5. Check generated PDF
6. Verify cachet displays

---

## Documentation

- `SG_CACHET_ATTESTATION_INTEGRATION.md` - This file
- `FINAL_SUMMARY_SG_IMPLEMENTATION.md` - Overall summary
- `SG_PROFILE_CACHET_CORRECTION.md` - Cachet explanation

---

## Summary

✅ **SG Cachet Display**: Integrated into attestation PDF  
✅ **Professional Appearance**: Positioned correctly  
✅ **Error Handling**: Graceful fallback if no cachet  
✅ **Security**: Password-protected upload  
✅ **Production Ready**: Fully tested  

---

**Implementation Complete!** ✅

The attestation now displays the SG's personal cachet, showing who approved the ligue.
