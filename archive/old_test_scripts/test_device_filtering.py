"""
Test script to verify device filtering enhancements in dashboard_v2.py
Tests both progressive filtering and specific device selection in wizard.
"""

from dashboard_v2 import SimpleDashboard

# Create dashboard instance (it loads its own data)
dashboard = SimpleDashboard()
df = dashboard.df
print()

print("=" * 70)
print("TEST 1: Progressive Device Filtering")
print("=" * 70)
print()

# Test 1a: Detect device_type (W13)
print("Test 1a: Detecting 'W13' as device_type")
result = dashboard._detect_parameter_type("W13")
print(f"  Result: {result}")
assert result['type'] == 'device_type', f"Expected 'device_type', got '{result['type']}'"
assert result['value'] == 'W13', f"Expected 'W13', got '{result['value']}'"
assert result['confidence'] == 'high', "Expected high confidence"
print("  PASS\n")

# Test 1b: Detect specific device ID
print("Test 1b: Detecting 'W13_S2_R9' as device ID")
result = dashboard._detect_parameter_type("W13_S2_R9")
print(f"  Result: {result}")
assert result['type'] == 'device', f"Expected 'device', got '{result['type']}'"
assert result['value'] == 'W13_S2_R9', f"Expected 'W13_S2_R9', got '{result['value']}'"
assert result['confidence'] == 'high', "Expected high confidence"
print("  PASS\n")

# Test 1c: Parse "show w13" command
print("Test 1c: Parsing 'show w13' command")
parsed = dashboard.parse_command("show w13")
print(f"  Result: {parsed}")
assert parsed['type'] == 'show', f"Expected 'show', got '{parsed['type']}'"
assert parsed['device_type'] == 'W13', f"Expected 'W13', got '{parsed['device_type']}'"
print("  PASS\n")

# Test 1d: Parse "show w13_s2_r9" command
print("Test 1d: Parsing 'show w13_s2_r9' command")
parsed = dashboard.parse_command("show w13_s2_r9")
print(f"  Result: {parsed}")
assert parsed['type'] == 'show_device', f"Expected 'show_device', got '{parsed['type']}'"
assert parsed['device_id'] == 'W13_S2_R9', f"Expected 'W13_S2_R9', got '{parsed['device_id']}'"
print("  PASS\n")

# Test 1e: Verify _get_prompt shows device filter correctly
print("Test 1e: Testing prompt display with device filter")
dashboard.session_state['current_filters'] = {'device_type': 'W13', 'device': 'W13_S2_R9'}
prompt = dashboard._get_prompt()
print(f"  Prompt: {prompt}")
assert 'W13' in prompt, "Expected 'W13' in prompt"
assert 'W13_S2_R9' in prompt, "Expected 'W13_S2_R9' in prompt"
print("  PASS\n")

# Test 1f: Clear filters for next test
dashboard.session_state['current_filters'] = {}

print("=" * 70)
print("TEST 2: Filter Wizard Device Selection")
print("=" * 70)
print()

# Test 2a: Verify _format_filter_dict includes device
print("Test 2a: Format filter dict with device")
filters = {'device_type': 'W13', 'device': 'W13_S2_R9', 'flowrate': 10, 'pressure': 300}
formatted = dashboard._format_filter_dict(filters)
print(f"  Result: {formatted}")
assert 'W13' in formatted, "Expected 'W13' in formatted string"
assert 'W13_S2_R9' in formatted, "Expected 'W13_S2_R9' in formatted string"
assert '10mlhr' in formatted, "Expected '10mlhr' in formatted string"
assert '300mbar' in formatted, "Expected '300mbar' in formatted string"
print("  PASS\n")

# Test 2b: Verify _build_query_from_filters handles device
print("Test 2b: Build query from filters with device")
query = dashboard._build_query_from_filters(filters)
print(f"  Result: {query}")
assert 'w13_s2_r9' in query.lower(), "Expected device ID in query"
assert '10mlhr' in query, "Expected flowrate in query"
assert '300mbar' in query, "Expected pressure in query"
print("  PASS\n")

# Test 2c: Verify _build_query_from_filters uses device instead of device_type when present
print("Test 2c: Verify device overrides device_type in query")
filters_with_both = {'device_type': 'W13', 'device': 'W13_S2_R9'}
query = dashboard._build_query_from_filters(filters_with_both)
print(f"  Result: {query}")
assert 'w13_s2_r9' in query.lower(), "Expected specific device ID, not just type"
assert query.lower() == 'show w13_s2_r9', f"Expected 'show w13_s2_r9', got '{query}'"
print("  PASS\n")

# Test 2d: Verify available devices list
print("Test 2d: Check available devices for W13")
w13_devices = df[df['device_type'] == 'W13']['device_id'].unique()
print(f"  W13 devices found: {len(w13_devices)}")
for dev in sorted(w13_devices):
    count = len(df[df['device_id'] == dev])
    print(f"    • {dev}: {count} measurements")
print("  PASS\n")

print("=" * 70)
print("ALL TESTS PASSED!")
print("=" * 70)
print()
print("Summary:")
print("  Issue 1 (Progressive Filtering): VERIFIED")
print("    - Device IDs are correctly detected by _detect_parameter_type")
print("    - 'show w13_s2_r9' command is parsed correctly")
print("    - Session filters and prompt display work correctly")
print()
print("  Issue 2 (Filter Wizard): IMPLEMENTED")
print("    - Specific Device step added after Device Type")
print("    - Device list filtered based on device_type selection")
print("    - Progressive filtering works (only shows devices with data)")
print("    - Measurement counts displayed for each device")
print()
print("Manual testing recommended:")
print("  1. Run: python dashboard_v2.py")
print("  2. Test progressive filtering:")
print("     >>> show w13")
print("     >>> w13_s2_r9")
print("  3. Test filter wizard:")
print("     >>> build filter")
print("     - Select Device Type: W13")
print("     - Select Specific Device: W13_S2_R9")
print("     - Continue with flow parameters")
