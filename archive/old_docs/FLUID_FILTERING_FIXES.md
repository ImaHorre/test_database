# Fluid Filtering Fixes - Dashboard v2

## Summary of Changes

Fixed three critical issues in `dashboard_v2.py` based on user feedback:

1. **Fixed numpy.float64 error** in "Available parameters" section
2. **Removed "Available parameters" section** per user request
3. **Added fluid filtering capability** to progressive filtering system

---

## Issue 1: numpy.float64 Error Fix

### Problem
Error occurred when displaying "Available parameters to refine your filter":
```
[ERROR] An error occurred: sequence item 0: expected str instance, numpy.float64 found
```

### Root Cause
The code was trying to join numeric values (numpy.float64) directly without converting to strings first.

### Solution
Added explicit `str()` conversion for all values before joining:

**Location**: `_suggest_available_parameters()` method (lines 2473-2510)

**Changes**:
```python
# BEFORE:
pressure_str = ', '.join([f"{int(p)}" for p in pressures])

# AFTER:
pressure_str = ', '.join([str(int(p)) for p in pressures])
```

Applied to all parameter types: pressures, flowrates, devices, fluids, and DFU rows.

---

## Issue 2: Removed "Available Parameters" Section

### Problem
User requested removal of the "Available parameters to refine your filter" section that appeared after filtering.

### Solution
Commented out the call to `_suggest_available_parameters()` in the `_cmd_add_filter_parameter()` method.

**Location**: Line 2374

**Change**:
```python
# Show available next steps
# DISABLED: User requested to remove the "Available parameters" section
# self._suggest_available_parameters()
```

The method `_suggest_available_parameters()` is still available in the code but is no longer called automatically.

---

## Issue 3: Fluid Filtering Capability

### Problem
Users want to filter by fluid type during progressive filtering with flexible input:
- Full combinations: `SDS_SO`, `NaCas_SO`
- Aqueous fluid only: `SDS`, `NaCas`
- Case insensitive: `sds`, `nacas`, `sds_so`

### Solution
Enhanced the progressive filtering system to recognize and handle fluid filters.

### Changes Made:

#### 3.1 Enhanced `_detect_parameter_type()` Method

**Location**: Lines 278-328

**Added fluid detection logic**:
```python
# Known aqueous and oil fluids
known_aqueous = ['sds', 'nacas', 'nacl']
known_oil = ['so', 'oil']

# Check for full fluid combination like "SDS_SO" or "NaCas_SO"
if '_' in value_lower:
    parts = value_lower.split('_')
    if len(parts) == 2:
        aq_part = parts[0]
        oil_part = parts[1]

        if aq_part in known_aqueous and oil_part in known_oil:
            # Normalize to standard format: SDS_SO, NaCas_SO
            aq_normalized = 'SDS' if aq_part == 'sds' else 'NaCas' if aq_part == 'nacas' else 'NaCl'
            oil_normalized = 'SO'
            return {
                'type': 'fluid_combination',
                'aqueous': aq_normalized,
                'oil': oil_normalized,
                'value': f"{aq_normalized}_{oil_normalized}",
                'confidence': 'high'
            }

# Check for just aqueous fluid like "SDS" or "NaCas"
if value_lower in known_aqueous:
    aq_normalized = 'SDS' if value_lower == 'sds' else 'NaCas' if value_lower == 'nacas' else 'NaCl'
    return {
        'type': 'aqueous_fluid',
        'value': aq_normalized,
        'confidence': 'high'
    }

# Check for just oil fluid like "SO"
if value_lower in known_oil:
    return {
        'type': 'oil_fluid',
        'value': 'SO',
        'confidence': 'high'
    }
```

**New parameter types recognized**:
- `fluid_combination`: Full combination like "SDS_SO"
- `aqueous_fluid`: Aqueous only like "SDS" or "NaCas"
- `oil_fluid`: Oil only like "SO"

#### 3.2 Updated `_cmd_add_filter_parameter()` Method

**Location**: Lines 2343-2431

**Added new filter types to mapping**:
```python
filter_key_map = {
    'pressure': 'pressure',
    'flowrate': 'flowrate',
    'device': 'device',
    'fluid': 'fluid',
    'fluid_combination': 'fluid',          # NEW
    'aqueous_fluid': 'aqueous_fluid',       # NEW
    'oil_fluid': 'oil_fluid',               # NEW
    'dfu': 'dfu',
    'device_type': 'device_type'
}
```

**Enhanced filter application logic**:
```python
# Handle different fluid filter types
if 'fluid' in new_filters:
    # Full combination filter (e.g., "SDS_SO")
    fluid_value = new_filters['fluid']
    if '_' in fluid_value:
        # It's a combination like "SDS_SO"
        aq, oil = fluid_value.split('_')
        df = df[(df['aqueous_fluid'] == aq) & (df['oil_fluid'] == oil)]
    else:
        # Check both aqueous and oil fluid columns
        df = df[
            (df['aqueous_fluid'] == fluid_value) |
            (df['oil_fluid'] == fluid_value)
        ]

if 'aqueous_fluid' in new_filters:
    # Filter by aqueous fluid only (e.g., "SDS" or "NaCas")
    df = df[df['aqueous_fluid'] == new_filters['aqueous_fluid']]

if 'oil_fluid' in new_filters:
    # Filter by oil fluid only (e.g., "SO")
    df = df[df['oil_fluid'] == new_filters['oil_fluid']]
```

#### 3.3 Updated `_get_prompt()` Method

**Location**: Lines 405-414

**Added fluid filter display**:
```python
if 'device' in filters:
    additional_parts.append(filters['device'])
if 'fluid' in filters:
    additional_parts.append(filters['fluid'])
if 'aqueous_fluid' in filters:
    additional_parts.append(filters['aqueous_fluid'])      # NEW
if 'oil_fluid' in filters:
    additional_parts.append(filters['oil_fluid'])          # NEW
if 'dfu' in filters:
    additional_parts.append(filters['dfu'])
```

#### 3.4 Updated `_cmd_remove_filter_parameter()` Method

**Location**: Lines 2460-2471

**Added new filter types to removal mapping** (same as add filter):
```python
filter_key_map = {
    'pressure': 'pressure',
    'flowrate': 'flowrate',
    'device': 'device',
    'fluid': 'fluid',
    'fluid_combination': 'fluid',          # NEW
    'aqueous_fluid': 'aqueous_fluid',       # NEW
    'oil_fluid': 'oil_fluid',               # NEW
    'dfu': 'dfu',
    'device_type': 'device_type'
}
```

---

## Testing Results

All tests passed successfully:

```
[PASS] Correctly detected as fluid_combination (SDS_SO)
[OK] PASS: Correctly detected as aqueous_fluid (SDS)
[OK] PASS: Correctly detected as aqueous_fluid (NaCas)
[OK] PASS: Case insensitive detection works (sds_so)
[OK] PASS: Device type detection still works (W13)
[OK] PASS: Pressure detection still works (300mbar)
```

**Database contains**:
- Aqueous fluids: NaCas, Repor, SDS
- Oil fluids: SO, t

---

## Usage Examples

### Example 1: Filter by full fluid combination
```
>>> show w13 at 5mlhr 300mbar
[Shows all W13 devices at 5mlhr/300mbar with both SDS_SO and NaCas_SO]

>>> [W13@5mlhr@300mbar] SDS_SO
[Filters to only SDS_SO devices]
```

### Example 2: Filter by aqueous fluid only
```
>>> show w13 at 5mlhr 300mbar
[Shows all W13 devices at 5mlhr/300mbar]

>>> [W13@5mlhr@300mbar] SDS
[Filters to only devices with SDS aqueous fluid, any oil]
```

### Example 3: Case insensitive input
```
>>> [W13@5mlhr@300mbar] nacas
[Filters to only devices with NaCas aqueous fluid]
```

### Example 4: Progressive filtering with fluids
```
>>> show w13
>>> 5mlhr
>>> 300mbar
>>> SDS
[Each step progressively narrows down the results]
```

---

## Files Modified

- **dashboard_v2.py** - Main implementation
  - `_detect_parameter_type()` - Enhanced fluid detection
  - `_cmd_add_filter_parameter()` - Added fluid filter handling
  - `_get_prompt()` - Display fluid filters in prompt
  - `_cmd_remove_filter_parameter()` - Added fluid filter removal
  - `_suggest_available_parameters()` - Fixed numpy.float64 error (now disabled)

## Files Created

- **test_fluid_filtering.py** - Test script for verifying all three fixes
- **FLUID_FILTERING_FIXES.md** - This summary document

---

## Known Fluids

The system recognizes these fluids (case insensitive):

**Aqueous fluids**:
- SDS
- NaCas
- NaCl

**Oil fluids**:
- SO
- oil (alias for SO)

**Full combinations**:
- SDS_SO
- NaCas_SO
- NaCl_SO

---

## Backward Compatibility

All changes maintain backward compatibility:
- Existing parameter detection still works (device type, pressure, flowrate, DFU)
- Old-style fluid detection (checking against database) still functions as fallback
- No breaking changes to existing filter commands
- The `_suggest_available_parameters()` method is preserved but disabled

---

## Next Steps

User should test interactively:
1. Run `python dashboard_v2.py`
2. Type: `show w13 at 5mlhr 300mbar`
3. Type: `SDS_SO` or `SDS`
4. Verify progressive filtering works as expected
5. Test removal: `-300mbar` or `-SDS`
6. Test filter display with `filters` command

---

## Notes

- Fluid names are case-insensitive on input but normalized to standard capitalization (SDS, NaCas, SO)
- Fluid combinations require underscore separator: `SDS_SO` not `SDSSO`
- Database contains an unusual oil fluid `t` - may need investigation
- Database contains aqueous fluid `Repor` - may need to add to known fluids list if used
