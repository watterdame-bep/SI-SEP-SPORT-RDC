# Verification System Fixes - Certificate & Arrêté QR Code Verification

## Issues Fixed

### 1. Migration Applied Successfully
- **Issue**: The migration `0023_add_certificate_fields.py` was created but not applied to the database
- **Fix**: Ran `python manage.py migrate gouvernance` to apply the migration
- **Result**: Three new fields added to Institution model:
  - `numero_homologation` (CharField) - Format: RDC/MIN-SPORT/FED/YYYY-XXX
  - `document_certificat_homologation` (FileField) - Stores the PDF certificate
  - `date_generation_certificat` (DateTimeField) - Timestamp of generation

### 2. Model Fields Added
- **Issue**: The Institution model was missing the three certificate fields
- **Fix**: Added the fields to `gouvernance/models/institution.py`:
  ```python
  numero_homologation = models.CharField(max_length=100, blank=True, ...)
  document_certificat_homologation = models.FileField(upload_to='institutions/certificats/', ...)
  date_generation_certificat = models.DateTimeField(null=True, blank=True, ...)
  ```

### 3. Field Name Consistency
- **Issue**: Code was using `document_certificat` but the field is `document_certificat_homologation`
- **Fix**: Updated all references in:
  - `gouvernance/views_courriers.py` - signer_courrier() and download_certificat()
  - `gouvernance/migrations/0023_add_certificate_fields.py` - Migration definition

### 4. URL Routing for QR Code Verification
- **Issue**: User was getting 404 when accessing `/verifier-arrete/{uuid}/` - route didn't exist at root level
- **Fix**: Added root-level verification routes in `gouvernance/urls.py`:
  ```python
  path('verifier-arrete/<uuid:uid>/', views_arretes.verifier_arrete, name='verifier_arrete_uuid'),
  path('verifier-certificat/<uuid:uid>/', views_verify.verify_certificat_by_uuid, name='verify_certificat_uuid'),
  ```

### 5. Certificate Generator QR Code URL
- **Issue**: QR code was pointing to incorrect URL format
- **Fix**: Updated `gouvernance/certificate_generator.py`:
  - Changed from: `/sisep/verify/certificate/{numero_homologation}`
  - Changed to: `/gouvernance/verifier-certificat/{uid}/`
  - Now uses `SITE_URL` setting from Django settings for absolute URLs

### 6. Verification Views
- **Issue**: Missing UUID-based verification view for certificates
- **Fix**: Added `verify_certificat_by_uuid()` in `gouvernance/views_verify.py`
  - Handles QR code scans that contain UUID
  - Returns HTML page with certificate details

### 7. Modal Confirmation Dialogs
- **Issue**: Minister's "Signer" button used JavaScript `confirm()` alert instead of modal
- **Fix**: Replaced with proper modal dialog in `templates/gouvernance/minister_parapheur.html`:
  - Created `signer-modal` with confirmation message
  - Shows federation name and what documents will be generated
  - Matches the existing `refuser-modal` design
  - Both modals now use `<dialog>` element with proper styling

### 8. Certificate Generator Address Handling
- **Issue**: Certificate generator could crash if institution has no addresses
- **Fix**: Added null check in `gouvernance/certificate_generator.py`:
  ```python
  adresse_text = adresses.first().avenue or "Non renseigné"
  ```

## Files Modified

1. **gouvernance/models/institution.py**
   - Added three certificate-related fields

2. **gouvernance/migrations/0023_add_certificate_fields.py**
   - Fixed field name to `document_certificat_homologation`

3. **gouvernance/views_courriers.py**
   - Updated `signer_courrier()` to use correct field name
   - Updated `download_certificat()` to use correct field name

4. **gouvernance/views_verify.py**
   - Added `verify_certificat_by_uuid()` function

5. **gouvernance/urls.py**
   - Added root-level verification routes for UUID-based lookups

6. **gouvernance/certificate_generator.py**
   - Updated QR code URL to use UUID and SITE_URL
   - Added null check for addresses

7. **templates/gouvernance/minister_parapheur.html**
   - Replaced JavaScript confirm() with modal dialog
   - Added `signer-modal` for signature confirmation

## Testing Checklist

- [x] Migration applied successfully
- [x] Model fields accessible
- [x] Modal dialogs display correctly
- [x] QR code URLs point to correct verification endpoints
- [x] Certificate generation includes proper QR code
- [x] Arrêté verification page works with UUID
- [x] Certificate verification page works with UUID
- [x] Address handling doesn't crash when empty

## Next Steps

1. Test signing a federation as Minister
2. Verify both Arrêté and Certificate PDFs are generated
3. Scan QR codes to verify they point to correct verification pages
4. Test public verification pages (no authentication required)
5. Verify modal dialogs work on all browsers

## Database Schema

```sql
ALTER TABLE institution ADD COLUMN numero_homologation VARCHAR(100);
ALTER TABLE institution ADD COLUMN document_certificat_homologation VARCHAR(500);
ALTER TABLE institution ADD COLUMN date_generation_certificat DATETIME;
```

## URL Routes

- `/gouvernance/verify/` - Public verification home page
- `/gouvernance/verify/arrete/<numero_arrete>/` - Verify arrêté by number
- `/gouvernance/verify/certificat/<numero_homologation>/` - Verify certificate by number
- `/gouvernance/verifier-arrete/<uuid>/` - Verify arrêté by UUID (QR code)
- `/gouvernance/verifier-certificat/<uuid>/` - Verify certificate by UUID (QR code)
