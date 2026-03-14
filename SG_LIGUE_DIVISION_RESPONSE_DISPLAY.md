# SG Ligue Detail - Division Response Display

## Overview
Enhanced the SG ligue detail interface to display the Division Provinciale's inspection response with all criteria details, observations, and inspection report.

## Changes Made

### Updated Section: "Validation de la Division Provinciale"

The section now displays:

#### 1. Basic Information
- Division Provinciale name
- Validation status (with color-coded badges)
- Date of validation
- Date of transfer to Division

#### 2. Inspection Criteria (When Division has responded)
Shows three criteria with status badges:

**Conformité du Mandat**
- Question: "Les délégués provinciaux sont-ils reconnus par la Fédération Nationale ?"
- Status: ✓ Validé (green) | ✗ Rejeté (red) | ? Non évalué (gray)

**Siège Social Provincial**
- Question: "L'adresse physique dans la province est-elle vérifiée et fonctionnelle ?"
- Status: ✓ Validé (green) | ✗ Rejeté (red) | ? Non évalué (gray)

**Existence des Clubs**
- Question: "La ligue dispose-t-elle du nombre minimum de clubs actifs requis ?"
- Status: ✓ Validé (green) | ✗ Rejeté (red) | ? Non évalué (gray)

#### 3. Observations
Displays the Division's observations in a highlighted box with:
- Icon: Pen to square
- Title: "Observations de la Division"
- Full text of observations

#### 4. Inspection Report
If the Division uploaded a report:
- Icon: File download
- Title: "Rapport d'Inspection Signé"
- Download button to access the PDF

## Display Logic

### When to Show Inspection Criteria
The criteria section only displays when:
- `validation_division.statut` is either `INSPECTION_VALIDEE` or `INSPECTION_REJETEE`
- This means the Division has completed their inspection

### Status Badges
Each criterion shows:
- **Green badge** if `True` (validated)
- **Red badge** if `False` (rejected)
- **Gray badge** if `None` (not evaluated)

### Conditional Display
- Observations box: Only shows if observations exist
- Report section: Only shows if report file exists
- Criteria section: Only shows if Division has responded

## User Experience

### For SG When Division Validates
1. SG sees "Inspection Validée" status (blue badge)
2. All three criteria show green checkmarks
3. Observations from Division are visible
4. Report can be downloaded
5. "Approuver" button appears to approve the ligue

### For SG When Division Rejects
1. SG sees "Inspection Rejetée" status (red badge)
2. One or more criteria show red X marks
3. Observations explain the rejection reasons
4. Report can be downloaded
5. "Rejeter" button appears to reject the ligue

### For SG While Division is Inspecting
1. SG sees "En inspection" status (yellow badge)
2. No criteria section displayed
3. No observations or report yet
4. "Transférer à Division" button is hidden
5. SG waits for Division response

## HTML Structure

```html
<!-- Criteria Section -->
<div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid #e2e8f0;">
    <h3>Critères d'Inspection</h3>
    <div class="info-row">
        <!-- Three criteria fields with badges -->
    </div>
</div>

<!-- Observations Box -->
<div class="observation-box">
    <p><strong>Observations de la Division:</strong></p>
    <p>{{ validation_division.observations }}</p>
</div>

<!-- Report Section -->
<div style="margin-top: 1rem; padding: 1rem; background: #f0f9ff; border-radius: 0.375rem; border-left: 4px solid #0036ca;">
    <p>Rapport d'Inspection Signé</p>
    <a href="{{ validation_division.rapport_inspection.url }}">Télécharger le rapport</a>
</div>
```

## Styling

### Criteria Section
- Separated from basic info with top border
- Icon: List check (blue)
- Three columns on desktop, responsive on mobile

### Observation Box
- Background: Light blue (#f0f9ff)
- Left border: 4px solid blue (#0036ca)
- Padding: 1rem
- Font: 0.9rem, line-height 1.5

### Report Section
- Background: Light blue (#f0f9ff)
- Left border: 4px solid blue (#0036ca)
- Download button: Blue background with white text
- Icon: File download

## Status Badges

### Validation Status
- **Validée** (green): All criteria passed
- **Inspection Validée** (blue): Division validated, awaiting SG approval
- **Inspection Rejetée** (red): Division rejected
- **En inspection** (yellow): Currently being inspected
- **En attente - SG doit transférer** (yellow): Waiting for SG to transfer

### Criteria Status
- **Validé** (green): Criterion passed
- **Rejeté** (red): Criterion failed
- **Non évalué** (gray): Not yet evaluated

## Files Modified

- `templates/gouvernance/sg_ligue_detail.html`

## Testing Checklist

- [ ] View ligue when Division is inspecting (no criteria shown)
- [ ] View ligue when Division validates (all criteria green)
- [ ] View ligue when Division rejects (some criteria red)
- [ ] Verify observations display correctly
- [ ] Verify report download link works
- [ ] Verify status badges display correctly
- [ ] Verify criteria section only shows when needed
- [ ] Test on mobile and desktop
- [ ] Verify all icons display correctly
- [ ] Verify colors match RDC theme

## Related Features

- Division inspection interface: `templates/gouvernance/division_ligue_detail.html`
- Division validation views: `gouvernance/views_division_ligues.py`
- ValidationLigue model: `gouvernance/models/validation_ligue.py`
- SG ligue list: `templates/gouvernance/sg_ligues_en_attente.html`

## Future Enhancements

- Add timeline showing inspection progress
- Add ability to request additional information from Division
- Add email notification when Division responds
- Add comparison view between SG and Division assessments
- Add ability to add SG observations before approval
