# Before/After Comparison - Fluid Filter Bug Fix

## User Scenario

User queries W13 devices at 5ml/hr and 300mbar, then adds SDS_SO fluid filter.

## Commands
```
>>> show w13 at 5mlhr 300mbar
>>> SDS_SO
```

---

## BEFORE FIX ✗

### Output After Adding SDS_SO Filter

```
Filter: device_type=W13, flowrate=5mlhr, pressure=300mbar

Matching Devices:
  1. W13_S1_R2:
     • 5.0ml/hr + 300.0mbar (NaCas_SO): 6 DFU rows, 29 frequency measurements
  2. W13_S4_R12:
     • 5.0ml/hr + 300.0mbar (SDS_SO): 6 DFU rows, 22 frequency measurements
  3. W13_S5_R11:
     • 5.0ml/hr + 300.0mbar (SDS_SO): 3 DFU rows
  4. W13_S5_R14:
     • 5.0ml/hr + 300.0mbar (SDS_SO): no data

Flow Parameter Combinations in Results:
  1. 5.0ml/hr + 300.0mbar (NaCas_SO): 1 devices
  2. 5.0ml/hr + 300.0mbar (SDS_SO): 3 devices

Per-Device Statistics:
  W13_S1_R2:
    • Droplet Size: 26.92 ± 1.71 µm (n=8)
    • Frequency:    2.61 ± 0.55 Hz (n=29)
  W13_S4_R12:
    • Droplet Size: 20.54 ± 4.68 µm (n=7)
    • Frequency:    6.15 ± 1.94 Hz (n=22)
  W13_S5_R11:
    • Droplet Size: 21.52 ± 1.28 µm (n=3)

Overall Average:
  Droplet Size: 23.54 ± 4.35 µm (n=18)
  Frequency:    4.14 ± 2.21 Hz (n=51)

Progressive filter applied: 74 -> 37 measurements
```

### Problems ✗

1. **Filter line missing fluid filters**
   - Shows: `device_type=W13, flowrate=5mlhr, pressure=300mbar`
   - Missing: `aqueous_fluid=SDS, oil_fluid=SO`

2. **W13_S1_R2 with NaCas_SO still appears**
   - Device #1 in "Matching Devices" should NOT be there
   - Has wrong fluid combination (NaCas_SO instead of SDS_SO)

3. **Flow Parameter Combinations shows both fluids**
   - Lists "NaCas_SO: 1 devices" - should NOT appear
   - Lists "SDS_SO: 3 devices" - correct

4. **Statistics include filtered-out device**
   - W13_S1_R2 statistics shown (should be excluded)
   - Overall average includes NaCas_SO device
   - Droplet size: 23.54 µm (incorrect - includes filtered data)
   - Frequency includes 29 measurements from W13_S1_R2

5. **"Progressive filter applied" appears AFTER wrong display**
   - Message confirms filter was applied to dataframe
   - But display shown before filter took effect

---

## AFTER FIX ✓

### Output After Adding SDS_SO Filter

```
Filter: device_type=W13, flowrate=5mlhr, pressure=300mbar, aqueous_fluid=SDS, oil_fluid=SO
Found: 1 complete droplet analysis, 1 complete frequency analysis, 2 partial analyses

Matching Devices:
  1. W13_S4_R12:
     • 5.0ml/hr + 300.0mbar (SDS_SO): 6 DFU rows, 22 frequency measurements
  2. W13_S5_R11:
     • 5.0ml/hr + 300.0mbar (SDS_SO): 3 DFU rows
  3. W13_S5_R14:
     • 5.0ml/hr + 300.0mbar (SDS_SO): no data

Flow Parameter Combinations in Results:
  1. 5.0ml/hr + 300.0mbar (SDS_SO): 3 devices

Per-Device Statistics:
  W13_S4_R12:
    • Droplet Size: 20.54 ± 4.68 µm (n=7)
    • Frequency:    6.15 ± 1.94 Hz (n=22)
  W13_S5_R11:
    • Droplet Size: 21.52 ± 1.28 µm (n=3)

Overall Average:
  Droplet Size: 20.83 ± 3.90 µm (n=10)
  Frequency:    6.15 ± 1.94 Hz (n=22)

Progressive filter applied: 74 -> 37 measurements
```

### Improvements ✓

1. **Filter line includes fluid filters**
   - Shows: `device_type=W13, flowrate=5mlhr, pressure=300mbar, aqueous_fluid=SDS, oil_fluid=SO`
   - ✓ All active filters displayed

2. **W13_S1_R2 correctly excluded**
   - Device no longer appears in "Matching Devices"
   - ✓ Only SDS_SO devices shown

3. **Flow Parameter Combinations shows only SDS_SO**
   - Lists "SDS_SO: 3 devices" only
   - ✓ No NaCas_SO devices

4. **Statistics calculated on filtered data only**
   - W13_S1_R2 statistics NOT shown
   - Overall average excludes NaCas_SO device
   - Droplet size: 20.83 µm (correct - SDS_SO only)
   - Frequency: 22 measurements (correct - excludes W13_S1_R2's 29)

5. **Found count updated correctly**
   - Shows "1 complete droplet analysis" (was 2 before filter)
   - Shows "1 complete frequency analysis" (was 2 before filter)
   - ✓ Counts reflect filtered data

---

## Key Differences Summary

| Aspect | Before Fix ✗ | After Fix ✓ |
|--------|-------------|------------|
| Filter description | Missing fluid filters | Includes `aqueous_fluid=SDS, oil_fluid=SO` |
| W13_S1_R2 (NaCas_SO) | Appears in output | Correctly excluded |
| Flow combinations | Shows both NaCas_SO and SDS_SO | Shows only SDS_SO |
| Device count | 4 devices | 3 devices (correct) |
| Droplet size avg | 23.54 µm (includes NaCas) | 20.83 µm (SDS only) |
| Frequency measurements | 51 (includes 29 from NaCas) | 22 (SDS only) |
| User experience | Confusing, incorrect | Clear, correct |

---

## Technical Root Cause

**Problem:** `_cmd_add_filter_parameter()` added fluid filters to session state AFTER calling `_cmd_filter()` to display results.

**Solution:**
1. Update session state BEFORE calling `_cmd_filter()`
2. Make `_cmd_filter()` check session state for additional filters
3. Display session state filters in output

**Files Modified:** `dashboard_v2.py` (Lines 1060-1091, 1117-1140, 2434-2456)

---

## Test Verification

Run: `python test_fluid_filter_fix.py`

Expected: "ALL TESTS PASSED!"

✓ W13_S1_R2 with NaCas_SO correctly filtered out
✓ All measurements are SDS_SO
✓ Statistics calculated on filtered data only
