# Test Instructions - Fluid Filter Fix

## Quick Test

Run the basic test to verify the fix:

```bash
python test_fluid_filter_fix.py
```

**Expected output:** "ALL TESTS PASSED!"

## Comprehensive Test

Run the full test suite with 4 scenarios:

```bash
python test_comprehensive_filters.py
```

**Expected output:** "ALL COMPREHENSIVE TESTS PASSED!"

## Manual Demonstration

Run the manual demo to see the fix in action:

```bash
python manual_test_fluid_filter.py
```

This will show you the full output before and after adding the fluid filter.

## Test Scenarios Covered

### Test 1: Basic Fluid Filter
1. Query: `show w13 at 5mlhr 300mbar`
2. Add filter: `SDS_SO`
3. Verify: Only SDS_SO devices appear

### Test 2: Change Fluid Filter
1. Query: `show w13 at 5mlhr 300mbar`
2. Add filter: `SDS_SO`
3. Change filter: `NaCas_SO`
4. Verify: Only NaCas_SO devices appear

### Test 3: Fluid Filter + Pressure
1. Query: `show w13 at 5mlhr`
2. Add filter: `SDS_SO`
3. Add filter: `300mbar`
4. Verify: Only SDS_SO devices at 300mbar appear

### Test 4: Device Filter + Fluid Filter
1. Query: `show w13 at 5mlhr 300mbar`
2. Add filter: `SDS_SO`
3. Add filter: `W13_S4_R12`
4. Verify: Only W13_S4_R12 with SDS_SO appears

## What to Look For

### Correct Behavior ✓

1. **Filter line includes fluid filters:**
   ```
   Filter: device_type=W13, flowrate=5mlhr, pressure=300mbar, aqueous_fluid=SDS, oil_fluid=SO
   ```

2. **Matching Devices section shows only filtered devices:**
   ```
   Matching Devices:
     1. W13_S4_R12:
        • 5.0ml/hr + 300.0mbar (SDS_SO): 6 DFU rows, 22 frequency measurements
     2. W13_S5_R11:
        • 5.0ml/hr + 300.0mbar (SDS_SO): 3 DFU rows
   ```

3. **Statistics calculated on filtered data only:**
   ```
   Overall Average:
     Droplet Size: 20.83 ± 3.90 µm (n=10)
     [NOT 23.54 µm which includes NaCas_SO devices]
   ```

### Incorrect Behavior ✗ (if bug not fixed)

1. **Filter line missing fluid filters:**
   ```
   Filter: device_type=W13, flowrate=5mlhr, pressure=300mbar
   ```

2. **Matching Devices shows non-filtered devices:**
   ```
   Matching Devices:
     1. W13_S1_R2:
        • 5.0ml/hr + 300.0mbar (NaCas_SO): ...
     [Should NOT appear after SDS_SO filter!]
   ```

3. **Statistics include filtered-out devices:**
   ```
   Overall Average:
     Droplet Size: 23.54 ± 4.35 µm (n=18)
     [Incorrectly includes NaCas_SO devices]
   ```

## Interactive Test

You can also test interactively in the dashboard:

```bash
python dashboard_v2.py
```

Then run:
```
>>> show w13 at 5mlhr 300mbar
>>> SDS_SO
```

Verify that W13_S1_R2 (NaCas_SO) does NOT appear after adding SDS_SO filter.

## Troubleshooting

If tests fail:

1. **Check file location:** Tests must be run from the project root directory
2. **Verify database exists:** Ensure `data/database.csv` is present
3. **Check imports:** Ensure `dashboard_v2.py` is in the same directory
4. **Python version:** Tests require Python 3.7+

## Test Files

- `test_fluid_filter_fix.py` - Basic verification test
- `test_comprehensive_filters.py` - Full test suite (4 scenarios)
- `manual_test_fluid_filter.py` - Manual demonstration
- `test_device_filtering.py` - Additional device filter tests
- `test_fluid_filtering.py` - Additional fluid filter tests
- `test_progressive_filter.py` - Progressive filtering tests

All tests are located in: `C:\Users\conor\Documents\Code Projects\test_database\`
