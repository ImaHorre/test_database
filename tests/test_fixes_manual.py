"""Manual test script to verify all 4 priority fixes."""
from dashboard_v2 import SimpleDashboard
import sys

def test_fix_1_device_breakdown():
    """Test Fix #1: Device breakdown shows all conditions."""
    print("\n" + "="*70)
    print("TEST FIX #1: Device Breakdown Shows All Conditions")
    print("="*70)
    print("Command: show w13 at 5mlhr")
    print()

    dashboard = SimpleDashboard()
    parsed = dashboard.parse_command("show w13 at 5mlhr")
    if parsed:
        dashboard.execute_command(parsed)

    print("\n✓ Check: All W13 devices at 5mlhr should be listed")
    print("✓ Check: Each device should show ALL pressure values tested")
    print()

def test_fix_2_stats_breakdown():
    """Test Fix #2: Stats command shows all devices."""
    print("\n" + "="*70)
    print("TEST FIX #2: Stats Command Shows All Devices")
    print("="*70)
    print("Command: stats w13")
    print()

    dashboard = SimpleDashboard()
    parsed = dashboard.parse_command("stats w13")
    if parsed:
        dashboard.execute_command(parsed)

    print("\n✓ Check: Device breakdown should show all W13 devices")
    print("✓ Check: Each device should show all test conditions")
    print()

def test_fix_3_stats_with_session():
    """Test Fix #3: Stats command accepts session filters."""
    print("\n" + "="*70)
    print("TEST FIX #3: Stats Command Uses Session Filters")
    print("="*70)
    print("Commands: show w13 at 5mlhr, then stats")
    print()

    dashboard = SimpleDashboard()

    # Set filters
    parsed = dashboard.parse_command("show w13 at 5mlhr")
    if parsed:
        dashboard.execute_command(parsed)

    print("\n--- Now testing 'stats' command with active filters ---\n")

    # Use stats without parameters
    parsed = dashboard.parse_command("stats")
    if parsed:
        dashboard.execute_command(parsed)
    else:
        print("❌ FAILED: 'stats' command was not recognized")

    print("\n✓ Check: 'stats' should work without error")
    print("✓ Check: Should show stats filtered to W13 at 5mlhr")
    print()

def test_fix_3_stats_without_filters():
    """Test Fix #3: Stats without filters shows helpful error."""
    print("\n" + "="*70)
    print("TEST FIX #3b: Stats Without Filters Shows Error")
    print("="*70)
    print("Commands: clear filters, then stats")
    print()

    dashboard = SimpleDashboard()

    # Clear filters
    parsed = dashboard.parse_command("clear filters")
    if parsed:
        dashboard.execute_command(parsed)

    # Try stats without filters
    parsed = dashboard.parse_command("stats")
    if parsed:
        dashboard.execute_command(parsed)
    else:
        print("❌ FAILED: 'stats' command was not recognized")

    print("\n✓ Check: Should show helpful error message")
    print("✓ Check: Should suggest setting filters or providing device type")
    print()

def test_fix_4_analysis_status():
    """Test Fix #4: Clarify analysis status."""
    print("\n" + "="*70)
    print("TEST FIX #4: Clear Analysis Status (Droplet + Frequency)")
    print("="*70)
    print("Command: show params for w13")
    print()

    dashboard = SimpleDashboard()
    parsed = dashboard.parse_command("show params for w13")
    if parsed:
        dashboard.execute_command(parsed)

    print("\n✓ Check: Each line should show BOTH 'Droplet (X)' AND 'Frequency (Y)'")
    print("✓ Check: Should be clear what data exists vs what's missing")
    print()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("MANUAL TEST SUITE FOR 4 PRIORITY FIXES")
    print("="*70)

    try:
        test_fix_1_device_breakdown()
        test_fix_2_stats_breakdown()
        test_fix_3_stats_with_session()
        test_fix_3_stats_without_filters()
        test_fix_4_analysis_status()

        print("\n" + "="*70)
        print("ALL MANUAL TESTS COMPLETED")
        print("="*70)
        print("\nReview the output above to verify:")
        print("  1. Device breakdowns show all conditions")
        print("  2. Stats shows all devices")
        print("  3. Stats works with session filters")
        print("  4. Analysis status is clear (Droplet + Frequency)")
        print()

    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
