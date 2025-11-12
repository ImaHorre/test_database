"""Test the critical measurement_type fix."""
from dashboard_v2 import SimpleDashboard

print("\n" + "="*70)
print("TESTING CRITICAL FIX: measurement_type values")
print("="*70)

dashboard = SimpleDashboard()

print("\n### TEST 1: show w13 at 5mlhr")
print("Expected: Should show devices W13_S1_R1 and W13_S2_R2 with actual data\n")
parsed = dashboard.parse_command("show w13 at 5mlhr")
if parsed:
    dashboard.execute_command(parsed)

print("\n" + "="*70)
print("\n### TEST 2: stats w13")
print("Expected: Should show all 3 W13 devices with proper status (not 'no data')\n")
parsed = dashboard.parse_command("stats w13")
if parsed:
    dashboard.execute_command(parsed)

print("\n" + "="*70)
print("\n### TEST 3: show params for w13")
print("Expected: Should show Frequency (available) where frequency data exists\n")
parsed = dashboard.parse_command("show params for w13")
if parsed:
    dashboard.execute_command(parsed)

print("\n" + "="*70)
print("\n### TEST 4: 'clear' command")
print("Expected: Should work as alias for 'clear filters'\n")

# Set filters first
parsed = dashboard.parse_command("show w13")
if parsed:
    dashboard.execute_command(parsed)

# Test 'clear'
print("\nNow testing 'clear' command:")
parsed = dashboard.parse_command("clear")
if parsed:
    dashboard.execute_command(parsed)
else:
    print("❌ FAILED: 'clear' not recognized")

print("\n" + "="*70)
print("TESTS COMPLETED")
print("="*70)
