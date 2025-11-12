# Quick Test Guide - Fluid Filtering Fixes

## Overview

Three issues have been fixed in dashboard_v2.py:
1. Fixed numpy.float64 error
2. Removed "Available parameters" section (per your request)
3. Added fluid filtering capability

## Quick Test Procedure

### Test 1: Basic Fluid Filtering

```bash
python dashboard_v2.py
```

Then in the dashboard:

```
>>> show w13 at 5mlhr 300mbar
```

**Expected**: Should show all W13 devices at 5mlhr/300mbar with both NaCas_SO and SDS_SO (if available)

**Check**:
- No error about numpy.float64
- No "Available parameters to refine your filter" section displayed

### Test 2: Filter by Full Fluid Combination

```
>>> [W13@5mlhr@300mbar] SDS_SO
```

**Expected**:
- Filters to only SDS_SO devices
- Prompt shows: `>>> [W13@5mlhr@300mbar | SDS_SO]`
- No "Available parameters" section

### Test 3: Filter by Aqueous Fluid Only

Reset and try:
```
>>> show w13 at 5mlhr 300mbar
>>> SDS
```

**Expected**:
- Filters to only devices with SDS aqueous fluid (any oil)
- Prompt shows: `>>> [W13@5mlhr@300mbar | SDS]`

### Test 4: Case Insensitive Input

```
>>> show w13 at 5mlhr 300mbar
>>> nacas
```

**Expected**:
- Recognizes "nacas" as "NaCas"
- Filters correctly
- Prompt normalizes to: `>>> [W13@5mlhr@300mbar | NaCas]`

### Test 5: Progressive Filtering

```
>>> show w13
>>> 5mlhr
>>> 300mbar
>>> SDS
```

**Expected**:
- Each step progressively narrows results
- Final prompt: `>>> [W13@5mlhr@300mbar | SDS]`
- No "Available parameters" section after each filter

### Test 6: Remove Fluid Filter

```
>>> show w13 at 5mlhr 300mbar
>>> SDS_SO
>>> -SDS_SO
```

**Expected**:
- Removes the SDS_SO filter
- Returns to showing all fluids at W13@5mlhr@300mbar
- Prompt updates: `>>> [W13@5mlhr@300mbar]`

### Test 7: Check Filter Display

```
>>> show w13 at 5mlhr 300mbar
>>> SDS
>>> filters
```

**Expected**:
Shows active filters including:
```
Active filters:
  • device_type: W13
  • flowrate: 5
  • pressure: 300
  • aqueous_fluid: SDS
```

## Automated Test

Run the automated test script to verify all detection logic:

```bash
python test_fluid_filtering.py
```

**Expected output**: All tests should show [PASS]

## Known Fluids

The system recognizes these fluids:

**Aqueous**: SDS, NaCas, NaCl
**Oil**: SO, oil
**Combinations**: SDS_SO, NaCas_SO, NaCl_SO

Input is case-insensitive: `sds`, `SDS`, `Sds` all work.

## What Changed

1. **No more numpy.float64 error** - All numeric values converted to strings before display
2. **No more "Available parameters" section** - Disabled as requested
3. **Fluid filtering works** - Can filter by SDS, NaCas, SDS_SO, etc.

## If Something Doesn't Work

Check:
1. Database loaded correctly (should show "Loaded X measurements")
2. Database contains fluid columns: `aqueous_fluid` and `oil_fluid`
3. Fluid values in database match known fluids (SDS, NaCas, SO)

Run with verbose error messages:
```bash
python dashboard_v2.py
```

Any errors will be displayed with details.

## Files to Review

- `FLUID_FILTERING_FIXES.md` - Detailed technical documentation
- `test_fluid_filtering.py` - Automated test script
- `dashboard_v2.py` - Updated implementation

## User Scenario Test

Your exact scenario from the request:

```
>>> show w13 at 5mlhr 300mbar
[Shows devices with both NaCas_SO and SDS_SO]

>>> SDS_SO
[Filters to only SDS_SO devices]

OR:

>>> SDS
[Filters to only devices with SDS aqueous fluid]
```

This should now work perfectly!
