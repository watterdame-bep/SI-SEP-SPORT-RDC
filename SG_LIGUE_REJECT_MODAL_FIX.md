# Fix: SG Ligue Detail - Reject Modal Removal & Single Textarea Implementation

**Date**: March 4, 2026  
**Status**: ✅ COMPLETED  
**User Issue**: When clicking "Rejeter" button, a separate modal was appearing instead of using the single textarea from "Décision du Secrétaire Général" section.

---

## Problem Statement

The SG ligue detail interface had two separate workflows for observations:
1. **Approve button**: Used textarea from "Décision du Secrétaire Général" section
2. **Reject button**: Opened a separate modal with its own textarea

This created confusion and inconsistency. User requirement was to have both buttons use the same textarea.

---

## Solution Implemented

### 1. Template Changes (`templates/gouvernance/sg_ligue_detail.html`)

#### Removed:
- **Reject Modal HTML** (lines ~850-900): Completely removed the `id="rejectModal"` div and all associated modal markup
- **Modal Functions**: Removed `openRejectModal()` and `closeRejectModal()` JavaScript functions

#### Updated:
- **Reject Button (Division validated case)**: Converted from button that opens modal to form that captures observations
  ```html
  <!-- Before: -->
  <button type="button" class="btn btn-danger" onclick="openRejectModal()">
  
  <!-- After: -->
  <form method="post" action="{% url 'gouvernance:sg_rejeter_ligue' ligue.uid %}" style="display: inline;">
      {% csrf_token %}
      <input type="hidden" name="observations_sg" id="observations-sg-input-reject">
      <button type="submit" class="btn btn-danger" onclick="captureObservationsReject(); return confirm(...)">
  ```

- **Reject Button (Division rejected case)**: Same treatment with separate hidden input ID
  ```html
  <form method="post" action="{% url 'gouvernance:sg_rejeter_ligue' ligue.uid %}" style="display: inline;">
      {% csrf_token %}
      <input type="hidden" name="observations_sg" id="observations-sg-input-reject-2">
      <button type="submit" class="btn btn-danger" onclick="captureObservationsRejectAlt(); ...">
  ```

#### JavaScript Functions:
- **`captureObservations()`**: Captures textarea value for Approve button
- **`captureObservationsReject()`**: Captures textarea value for Reject button (Division validated)
- **`captureObservationsRejectAlt()`**: Captures textarea value for Reject button (Division rejected)

All three functions read from the same textarea: `#observations-sg-display`

### 2. View Changes (`gouvernance/views_sg_ligues.py`)

#### `sg_approuver_ligue()` view:
- **Added**: Capture observations from POST request
  ```python
  observations_sg = request.POST.get('observations_sg', '').strip()
  ```
- **Added**: Store observations in attestation before approval
  ```python
  attestation.observations_sg = observations_sg
  attestation.approuver(numero_attestation)
  ```
- **Added**: Pass observations to email context
  ```python
  context = {
      'ligue': ligue,
      'federation': federation,
      'numero_attestation': numero_attestation,
      'observations': observations_sg,  # NEW
      'decision': 'APPROUVEE'
  }
  ```

#### `sg_rejeter_ligue()` view:
- **Already implemented**: Captures observations and sends email
- **No changes needed**: Already working correctly

### 3. Email Template (`templates/emails/ligue_decision.html`)

- **Already supports**: Displaying observations for both approval and rejection
- **No changes needed**: Template already handles both cases

### 4. Federation Interface (`templates/gouvernance/federation_ligues_list.html`)

- **Already displays**: SG observations in the ligue list
- **Format**: Truncated to 10 words with full text in tooltip
- **No changes needed**: Already working correctly

---

## Workflow After Fix

### For SG Approving a Ligue:
1. SG navigates to ligue detail
2. SG sees "Décision du Secrétaire Général" section with textarea
3. SG types observations (optional)
4. SG clicks "Approuver" button
5. JavaScript captures textarea value
6. Form submits with observations
7. Email sent to federation with observations
8. Federation sees observations in their ligue list

### For SG Rejecting a Ligue:
1. SG navigates to ligue detail
2. SG sees "Décision du Secrétaire Général" section with textarea
3. SG types observations (required for rejection context)
4. SG clicks "Rejeter" button
5. JavaScript captures textarea value
6. Confirmation dialog appears
7. Form submits with observations
8. Email sent to federation with observations
9. Federation sees observations in their ligue list

---

## Key Features

✅ **Single Textarea**: Both Approve and Reject use same textarea  
✅ **No Modal**: Reject button no longer opens separate modal  
✅ **Observations Captured**: Both actions capture and store observations  
✅ **Email Notifications**: Observations included in email to federation  
✅ **Federation Visibility**: Federation sees SG observations in their interface  
✅ **Confirmation Dialogs**: Both actions show confirmation before submission  
✅ **Clean UI**: Removed unnecessary modal markup for cleaner interface  

---

## Files Modified

1. **`templates/gouvernance/sg_ligue_detail.html`**
   - Removed reject modal HTML
   - Updated reject buttons to use forms
   - Updated JavaScript functions to capture from single textarea

2. **`gouvernance/views_sg_ligues.py`**
   - Updated `sg_approuver_ligue()` to capture and store observations
   - Updated email context to include observations

---

## Testing Checklist

- [x] Reject modal no longer appears when clicking "Rejeter"
- [x] Both Approve and Reject buttons use same textarea
- [x] Observations are captured from textarea
- [x] Observations are stored in attestation
- [x] Email notifications include observations
- [x] Federation sees observations in their interface
- [x] Confirmation dialogs work correctly
- [x] No syntax errors in template or views
- [x] No JavaScript errors in browser console

---

## User Experience Improvement

**Before**: Confusing dual-textarea system with separate modal  
**After**: Intuitive single-textarea system with consistent workflow

The SG now has a clear, unified interface for making decisions on ligues with observations that are immediately visible to the federation.
