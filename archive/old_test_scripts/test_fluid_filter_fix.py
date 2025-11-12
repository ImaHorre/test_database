"""Test script to verify fluid filter fix in dashboard_v2.py"""

import sys
import pandas as pd

# Test the fix by simulating the user's exact scenario
def test_fluid_filter():
    print("=" * 80)
    print("TESTING FLUID FILTER FIX")
    print("=" * 80)
    print()

    # Import the dashboard
    from dashboard_v2 import SimpleDashboard

    # Create dashboard instance (no arguments needed)
    db = SimpleDashboard()

    print("Step 1: Show W13 devices at 5mlhr 300mbar")
    print("-" * 80)

    # Simulate: show w13 at 5mlhr 300mbar
    db._process_query("show w13 at 5mlhr 300mbar")

    print()
    print()
    print("Step 2: Add SDS_SO fluid filter")
    print("-" * 80)

    # Simulate: SDS_SO (add filter)
    db._process_query("SDS_SO")

    print()
    print()
    print("VERIFICATION:")
    print("-" * 80)

    # Check the filtered dataframe
    if db.session_state.get('last_filtered_df') is not None:
        df = db.session_state['last_filtered_df']

        print(f"Total measurements after filter: {len(df)}")
        print()

        # Show unique devices
        unique_devices = df['device_id'].unique()
        print(f"Unique devices in results: {len(unique_devices)}")
        for device in sorted(unique_devices):
            print(f"  - {device}")
        print()

        # Show fluids in results
        fluid_combos = df[['aqueous_fluid', 'oil_fluid']].drop_duplicates()
        print("Fluid combinations in results:")
        for _, row in fluid_combos.iterrows():
            print(f"  - {row['aqueous_fluid']}_{row['oil_fluid']}")
        print()

        # Check if W13_S1_R2 with NaCas_SO appears (it shouldn't!)
        w13_s1_r2_nacas = df[
            (df['device_id'] == 'W13_S1_R2') &
            (df['aqueous_fluid'] == 'NaCas') &
            (df['oil_fluid'] == 'SO')
        ]

        if len(w13_s1_r2_nacas) > 0:
            print("FAIL: W13_S1_R2 with NaCas_SO should NOT appear!")
            print(f"  Found {len(w13_s1_r2_nacas)} measurements")
            return False
        else:
            print("SUCCESS: W13_S1_R2 with NaCas_SO correctly filtered out!")

        # Check if only SDS_SO appears
        non_sds_so = df[
            (df['aqueous_fluid'] != 'SDS') |
            (df['oil_fluid'] != 'SO')
        ]

        if len(non_sds_so) > 0:
            print("FAIL: Found non-SDS_SO measurements!")
            print(f"  Found {len(non_sds_so)} non-SDS_SO measurements")
            return False
        else:
            print("SUCCESS: All measurements are SDS_SO!")

        print()
        print("=" * 80)
        print("ALL TESTS PASSED!")
        print("=" * 80)
        return True
    else:
        print("FAIL: No filtered dataframe found in session state")
        return False

if __name__ == "__main__":
    try:
        success = test_fluid_filter()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
