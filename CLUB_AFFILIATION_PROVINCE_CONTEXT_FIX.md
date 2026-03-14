# Club Affiliation - Province Context Variables Fix

## Problem
The province field was displaying "Province non disponible" even though each ligue is registered with a province.

## Root Cause
The template context variables `province_id` and `province_name` were not being passed to the template in the Step 1 and Step 3 views. Only the Step 2 view was passing these variables.

Since the form uses a multi-step JavaScript interface that displays all steps on a single page, the context variables need to be available when the page is first loaded (Step 1).

## Solution
Added `province_id` and `province_name` to the context in all three step views:

### Step 1 View (`ligue_club_create_step1`)
```python
context = {
    'ligue': ligue,
    'form': form,
    'step': 1,
    'total_steps': 3,
    'user_role': 'ligue_secretary',
    'province_id': str(ligue.province_admin.uid) if ligue.province_admin else None,
    'province_name': ligue.province_admin.designation if ligue.province_admin else None,
}
```

### Step 2 View (`ligue_club_create_step2`)
Already had the context variables (no change needed).

### Step 3 View (`ligue_club_create_step3`)
```python
context = {
    'ligue': ligue,
    'form': form,
    'disciplines': disciplines,
    'step': 3,
    'total_steps': 3,
    'user_role': 'ligue_secretary',
    'province_id': str(ligue.province_admin.uid) if ligue.province_admin else None,
    'province_name': ligue.province_admin.designation if ligue.province_admin else None,
}
```

## How It Works

1. When the user accesses the club creation form (Step 1), the view passes `province_id` and `province_name` to the template
2. The JavaScript reads these template variables: `const liueProvinceId = '{{ province_id }}';`
3. The JavaScript pre-fills the province select with the ligue's province
4. The JavaScript populates the hidden input field with the province ID for form submission
5. The JavaScript automatically loads territories for that province
6. The cascading selects work: territoire → secteur → groupement

## Files Modified

- `gouvernance/views_ligue_secretary.py`
  - Updated `ligue_club_create_step1()` context
  - Updated `ligue_club_create_step3()` context

## Testing

- [x] Province field displays the ligue's province name
- [x] Province field is not clickable (disabled)
- [x] Territories load automatically on page load
- [x] Cascading selects work properly
- [x] Form submission includes province value

## Notes

- The `province_admin` field on the Institution model stores the province for ligues
- The context variables are rendered as Django template variables: `{{ province_id }}` and `{{ province_name }}`
- The JavaScript checks if these variables are empty and displays "Province not available" if they are
- Since each ligue must have a province, these variables should never be empty in normal operation
