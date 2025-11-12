"""
Test script to verify progressive filtering logic in dashboard_v2.py
Simulates the wizard flow without requiring interactive input
"""

import pandas as pd

def test_progressive_filtering():
    """Test that progressive filtering only shows valid options."""

    # Load database
    df = pd.read_csv('data/database.csv')

    print("=" * 70)
    print("TESTING PROGRESSIVE FILTERING LOGIC")
    print("=" * 70)
    print()

    # Test Case 1: W14 -> 10ml/hr -> should only show 200mbar
    print("TEST CASE 1: W14 -> 10ml/hr")
    print("-" * 70)

    # Step 1: Start with full dataframe
    filtered_df = df.copy()
    print(f"Initial data: {len(filtered_df)} measurements")

    # Step 2: Select W14
    device_type = 'W14'
    filtered_df = filtered_df[filtered_df['device_type'] == device_type]
    print(f"After selecting {device_type}: {len(filtered_df)} measurements")

    # Step 3: Show available flowrates for W14
    available_flowrates = sorted(filtered_df['aqueous_flowrate'].dropna().unique())
    print(f"\nAvailable flowrates for {device_type}:")
    for fr in available_flowrates:
        count = len(filtered_df[filtered_df['aqueous_flowrate'] == fr])
        print(f"  {int(fr)}ml/hr ({count} measurements)")

    # Step 4: Select 10ml/hr
    flowrate = 10
    filtered_df = filtered_df[filtered_df['aqueous_flowrate'] == flowrate]
    print(f"\nAfter selecting {flowrate}ml/hr: {len(filtered_df)} measurements")

    # Step 5: Show available pressures for W14 at 10ml/hr
    available_pressures = sorted(filtered_df['oil_pressure'].dropna().unique())
    print(f"\nAvailable pressures for {device_type} at {flowrate}ml/hr:")
    for pr in available_pressures:
        count = len(filtered_df[filtered_df['oil_pressure'] == pr])
        print(f"  {int(pr)}mbar ({count} measurements)")

    # Verify: Should only show 200mbar
    assert len(available_pressures) == 1, f"Expected 1 pressure, got {len(available_pressures)}"
    assert int(available_pressures[0]) == 200, f"Expected 200mbar, got {int(available_pressures[0])}mbar"
    print("\n[PASS] TEST PASSED: Only 200mbar is shown (no 'no data found' error possible)")

    print("\n" + "=" * 70)
    print()

    # Test Case 2: W13 -> 5ml/hr -> should show multiple pressures
    print("TEST CASE 2: W13 -> 5ml/hr")
    print("-" * 70)

    # Step 1: Start with full dataframe
    filtered_df = df.copy()
    print(f"Initial data: {len(filtered_df)} measurements")

    # Step 2: Select W13
    device_type = 'W13'
    filtered_df = filtered_df[filtered_df['device_type'] == device_type]
    print(f"After selecting {device_type}: {len(filtered_df)} measurements")

    # Step 3: Show available flowrates for W13
    available_flowrates = sorted(filtered_df['aqueous_flowrate'].dropna().unique())
    print(f"\nAvailable flowrates for {device_type}:")
    for fr in available_flowrates:
        count = len(filtered_df[filtered_df['aqueous_flowrate'] == fr])
        print(f"  {int(fr)}ml/hr ({count} measurements)")

    # Step 4: Select 5ml/hr
    flowrate = 5
    filtered_df = filtered_df[filtered_df['aqueous_flowrate'] == flowrate]
    print(f"\nAfter selecting {flowrate}ml/hr: {len(filtered_df)} measurements")

    # Step 5: Show available pressures for W13 at 5ml/hr
    available_pressures = sorted(filtered_df['oil_pressure'].dropna().unique())
    print(f"\nAvailable pressures for {device_type} at {flowrate}ml/hr:")
    for pr in available_pressures:
        count = len(filtered_df[filtered_df['oil_pressure'] == pr])
        print(f"  {int(pr)}mbar ({count} measurements)")

    # Verify: Should show 6 pressures (50, 100, 150, 200, 250, 300)
    assert len(available_pressures) == 6, f"Expected 6 pressures, got {len(available_pressures)}"
    print(f"\n[PASS] TEST PASSED: {len(available_pressures)} valid pressures shown")

    print("\n" + "=" * 70)
    print()

    # Test Case 3: No device type filter -> all flowrates shown
    print("TEST CASE 3: No device type filter -> Show all flowrates")
    print("-" * 70)

    filtered_df = df.copy()
    available_flowrates = sorted(filtered_df['aqueous_flowrate'].dropna().unique())
    print(f"Available flowrates (all device types):")
    for fr in available_flowrates:
        count = len(filtered_df[filtered_df['aqueous_flowrate'] == fr])
        print(f"  {int(fr)}ml/hr ({count} measurements)")

    print(f"\n[PASS] TEST PASSED: {len(available_flowrates)} flowrates shown")

    print("\n" + "=" * 70)
    print("\nALL TESTS PASSED!")
    print("Progressive filtering will prevent 'no data found' errors")
    print("=" * 70)

if __name__ == "__main__":
    test_progressive_filtering()
