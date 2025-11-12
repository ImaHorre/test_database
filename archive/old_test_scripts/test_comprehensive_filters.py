"""Comprehensive test of progressive filtering with various filter types"""

import sys
from dashboard_v2 import SimpleDashboard

def test_scenario(db, scenario_name, queries, expected_result):
    """Test a filtering scenario"""
    print("=" * 80)
    print(f"TEST: {scenario_name}")
    print("=" * 80)

    for idx, query in enumerate(queries, 1):
        print(f"\nStep {idx}: {query}")
        print("-" * 80)
        db._process_query(query)

    # Check results
    df = db.session_state.get('last_filtered_df')
    if df is None:
        print("\nFAIL: No filtered dataframe")
        return False

    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("-" * 80)

    # Check expected result
    success = True
    for check_name, check_fn in expected_result.items():
        result = check_fn(df, db)
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {check_name}")
        if not result:
            success = False

    print("=" * 80)
    print()
    return success

def main():
    print("=" * 80)
    print("COMPREHENSIVE PROGRESSIVE FILTERING TESTS")
    print("=" * 80)
    print()

    all_passed = True

    # Test 1: Fluid filter after device+flow+pressure
    print("\n\n")
    db = SimpleDashboard()
    result = test_scenario(
        db,
        "Fluid filter after device+flow+pressure",
        [
            "show w13 at 5mlhr 300mbar",
            "SDS_SO"
        ],
        {
            "Only SDS_SO devices": lambda df, db: all(
                (df['aqueous_fluid'] == 'SDS') & (df['oil_fluid'] == 'SO')
            ),
            "No NaCas_SO devices": lambda df, db: len(
                df[(df['aqueous_fluid'] == 'NaCas') & (df['oil_fluid'] == 'SO')]
            ) == 0,
            "Filter description includes fluid": lambda df, db:
                'aqueous_fluid' in str(db.session_state.get('last_query', ''))
        }
    )
    all_passed = all_passed and result

    # Test 2: Multiple fluid filters (change fluid)
    print("\n\n")
    db = SimpleDashboard()
    result = test_scenario(
        db,
        "Change fluid filter",
        [
            "show w13 at 5mlhr 300mbar",
            "SDS_SO",
            "NaCas_SO"  # Should replace SDS_SO
        ],
        {
            "Only NaCas_SO devices": lambda df, db: all(
                (df['aqueous_fluid'] == 'NaCas') & (df['oil_fluid'] == 'SO')
            ),
            "No SDS_SO devices": lambda df, db: len(
                df[(df['aqueous_fluid'] == 'SDS') & (df['oil_fluid'] == 'SO')]
            ) == 0
        }
    )
    all_passed = all_passed and result

    # Test 3: Fluid filter then pressure change
    print("\n\n")
    db = SimpleDashboard()
    result = test_scenario(
        db,
        "Fluid filter then pressure change",
        [
            "show w13 at 5mlhr",
            "SDS_SO",
            "300mbar"  # Add pressure filter
        ],
        {
            "Only SDS_SO devices": lambda df, db: all(
                (df['aqueous_fluid'] == 'SDS') & (df['oil_fluid'] == 'SO')
            ),
            "Only 300mbar pressure": lambda df, db: all(df['oil_pressure'] == 300.0),
            "Filter includes both fluid and pressure": lambda df, db:
                'aqueous_fluid' in str(db.session_state.get('last_query', '')) and
                'pressure' in str(db.session_state.get('last_query', ''))
        }
    )
    all_passed = all_passed and result

    # Test 4: Device filter after fluid filter
    print("\n\n")
    db = SimpleDashboard()
    result = test_scenario(
        db,
        "Device filter after fluid filter",
        [
            "show w13 at 5mlhr 300mbar",
            "SDS_SO",
            "W13_S4_R12"  # Filter to specific device
        ],
        {
            "Only W13_S4_R12": lambda df, db: all(df['device_id'] == 'W13_S4_R12'),
            "Only SDS_SO": lambda df, db: all(
                (df['aqueous_fluid'] == 'SDS') & (df['oil_fluid'] == 'SO')
            ),
            "Filter includes device and fluid": lambda df, db:
                'device' in str(db.session_state.get('current_filters', {})) and
                'fluid' in str(db.session_state.get('current_filters', {}))
        }
    )
    all_passed = all_passed and result

    # Final summary
    print("\n" + "=" * 80)
    if all_passed:
        print("ALL COMPREHENSIVE TESTS PASSED!")
        print("=" * 80)
        return 0
    else:
        print("SOME TESTS FAILED!")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
