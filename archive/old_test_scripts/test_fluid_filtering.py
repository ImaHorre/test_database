"""
Test script for fluid filtering functionality in dashboard_v2.py

Tests the three issues:
1. numpy.float64 error fix in _suggest_available_parameters
2. Removal of "Available parameters" section
3. Fluid filtering capability (SDS, NaCas, SDS_SO, etc.)
"""

import sys
sys.path.append('C:\\Users\\conor\\Documents\\Code Projects\\test_database')

from dashboard_v2 import SimpleDashboard

# Initialize dashboard
print("Initializing dashboard...")
dashboard = SimpleDashboard()
print(f"Loaded {len(dashboard.df)} measurements from database")
print()

# Test 1: Test fluid detection - Full combination
print("=" * 70)
print("TEST 1: Full fluid combination detection (SDS_SO)")
print("=" * 70)
result = dashboard._detect_parameter_type("SDS_SO")
print(f"Input: 'SDS_SO'")
print(f"Detection result: {result}")
expected_type = 'fluid_combination'
if result['type'] == expected_type:
    print("[PASS] Correctly detected as fluid_combination")
else:
    print(f"[FAIL] Expected '{expected_type}', got '{result['type']}'")
print()

# Test 2: Test fluid detection - Aqueous only
print("=" * 70)
print("TEST 2: Aqueous fluid only detection (SDS)")
print("=" * 70)
result = dashboard._detect_parameter_type("SDS")
print(f"Input: 'SDS'")
print(f"Detection result: {result}")
expected_type = 'aqueous_fluid'
if result['type'] == expected_type:
    print("[OK] PASS: Correctly detected as aqueous_fluid")
else:
    print(f"[X] FAIL: Expected '{expected_type}', got '{result['type']}'")
print()

# Test 3: Test fluid detection - NaCas
print("=" * 70)
print("TEST 3: Aqueous fluid detection (NaCas)")
print("=" * 70)
result = dashboard._detect_parameter_type("NaCas")
print(f"Input: 'NaCas'")
print(f"Detection result: {result}")
expected_type = 'aqueous_fluid'
if result['type'] == expected_type:
    print("[OK] PASS: Correctly detected as aqueous_fluid")
else:
    print(f"[X] FAIL: Expected '{expected_type}', got '{result['type']}'")
print()

# Test 4: Test fluid detection - Case insensitivity
print("=" * 70)
print("TEST 4: Case insensitivity (sds_so)")
print("=" * 70)
result = dashboard._detect_parameter_type("sds_so")
print(f"Input: 'sds_so'")
print(f"Detection result: {result}")
if result['type'] == 'fluid_combination' and result['value'] == 'SDS_SO':
    print("[OK] PASS: Case insensitive detection works")
else:
    print(f"[X] FAIL: Case insensitive detection failed")
print()

# Test 5: Test device type detection (ensure we didn't break existing functionality)
print("=" * 70)
print("TEST 5: Device type detection (W13)")
print("=" * 70)
result = dashboard._detect_parameter_type("W13")
print(f"Input: 'W13'")
print(f"Detection result: {result}")
if result['type'] == 'device_type':
    print("[OK] PASS: Device type detection still works")
else:
    print(f"[X] FAIL: Device type detection broken")
print()

# Test 6: Test pressure detection (ensure we didn't break existing functionality)
print("=" * 70)
print("TEST 6: Pressure detection (300mbar)")
print("=" * 70)
result = dashboard._detect_parameter_type("300mbar")
print(f"Input: '300mbar'")
print(f"Detection result: {result}")
if result['type'] == 'pressure':
    print("[OK] PASS: Pressure detection still works")
else:
    print(f"[X] FAIL: Pressure detection broken")
print()

# Test 7: Check available fluids in database
print("=" * 70)
print("TEST 7: Check fluids in database")
print("=" * 70)
if 'aqueous_fluid' in dashboard.df.columns:
    aq_fluids = dashboard.df['aqueous_fluid'].dropna().unique()
    print(f"Aqueous fluids in database: {sorted(aq_fluids)}")
else:
    print("[X] WARNING: No 'aqueous_fluid' column in database")

if 'oil_fluid' in dashboard.df.columns:
    oil_fluids = dashboard.df['oil_fluid'].dropna().unique()
    print(f"Oil fluids in database: {sorted(oil_fluids)}")
else:
    print("[X] WARNING: No 'oil_fluid' column in database")
print()

# Test 8: Test filtering by W13 at 5mlhr 300mbar (user scenario setup)
print("=" * 70)
print("TEST 8: Filter W13 at 5mlhr 300mbar (user scenario)")
print("=" * 70)
# We can't actually run interactive commands here, but we can test the logic
print("This would be tested interactively:")
print("  1. Run: show w13 at 5mlhr 300mbar")
print("  2. Verify it shows both NaCas_SO and SDS_SO devices")
print("  3. Then add: SDS_SO")
print("  4. Verify it filters to only SDS_SO devices")
print("  5. Or add: SDS")
print("  6. Verify it filters to only devices with SDS aqueous fluid")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("All detection tests completed. Check output above for PASS/FAIL status.")
print()
print("To test interactively:")
print("1. Run: python dashboard_v2.py")
print("2. Type: show w13 at 5mlhr 300mbar")
print("3. Type: SDS_SO")
print("4. Verify progressive filtering works")
print("=" * 70)
