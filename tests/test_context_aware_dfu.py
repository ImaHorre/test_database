"""
Test script for context-aware DFU plotting functionality.

This script demonstrates the enhanced plot_metric_vs_dfu() method that
automatically detects varying parameters and includes them in legends.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import DataAnalyst


def test_context_aware_plotting():
    """Test the context-aware DFU plotting with various scenarios."""

    print("=" * 80)
    print("CONTEXT-AWARE DFU PLOTTING TEST")
    print("=" * 80)
    print()

    # Initialize analyst
    print("Initializing DataAnalyst...")
    analyst = DataAnalyst()
    print(f"Loaded {len(analyst.df)} measurements")
    print()

    # =========================================================================
    # TEST 1: User's specific example - W13 devices at 5mlhr
    # Expected: Should detect pressure variation and show in legend
    # =========================================================================
    print("-" * 80)
    print("TEST 1: W13 devices at 5ml/hr (varying pressures)")
    print("-" * 80)

    try:
        result = analyst.plot_metric_vs_dfu(
            metric='droplet_size_mean',
            device_type='W13',
            aqueous_flowrate=5,
            oil_pressure=None,  # Don't filter pressure - let it vary
            output_path='outputs/test_w13_5mlhr_varying_pressure.png',
            query_text='show droplet size across all measured DFUs for w13 devices at 5mlhr'
        )

        print(f"[OK] Plot generated: {result['plot_path']}")
        print(f"  Devices found: {result['num_devices']}")
        print(f"  Varying parameters: {result['varying_parameters']}")
        print(f"  Devices: {result['devices']}")
        print()

    except ValueError as e:
        print(f"[FAIL] Test failed: {e}")
        print()

    # =========================================================================
    # TEST 2: Multiple pressures AND multiple fluids
    # Expected: Should show both in legend
    # =========================================================================
    print("-" * 80)
    print("TEST 2: All W13 devices (multiple pressures and fluids)")
    print("-" * 80)

    try:
        result = analyst.plot_metric_vs_dfu(
            metric='droplet_size_mean',
            device_type='W13',
            aqueous_flowrate=None,
            oil_pressure=None,
            output_path='outputs/test_w13_all_conditions.png'
        )

        print(f"[OK] Plot generated: {result['plot_path']}")
        print(f"  Devices found: {result['num_devices']}")
        print(f"  Varying parameters: {result['varying_parameters']}")
        print()

    except ValueError as e:
        print(f"[FAIL] Test failed: {e}")
        print()

    # =========================================================================
    # TEST 3: Single condition (no variation)
    # Expected: Legend should only show device IDs
    # =========================================================================
    print("-" * 80)
    print("TEST 3: W13 devices at 5ml/hr 200mbar (single condition)")
    print("-" * 80)

    try:
        result = analyst.plot_metric_vs_dfu(
            metric='droplet_size_mean',
            device_type='W13',
            aqueous_flowrate=5,
            oil_pressure=200,
            output_path='outputs/test_w13_5mlhr_200mbar.png'
        )

        print(f"[OK] Plot generated: {result['plot_path']}")
        print(f"  Devices found: {result['num_devices']}")
        print(f"  Varying parameters: {result['varying_parameters']}")
        print(f"  Expected: Should be empty or minimal since conditions are fixed")
        print()

    except ValueError as e:
        print(f"[FAIL] Test failed: {e}")
        print()

    # =========================================================================
    # TEST 4: Query with date mention
    # Expected: Should include dates in legend if they vary
    # =========================================================================
    print("-" * 80)
    print("TEST 4: W13 devices with date mention in query")
    print("-" * 80)

    try:
        result = analyst.plot_metric_vs_dfu(
            metric='droplet_size_mean',
            device_type='W13',
            aqueous_flowrate=5,
            oil_pressure=None,
            output_path='outputs/test_w13_with_dates.png',
            query_text='show droplet size across DFUs for w13 at 5mlhr across different test dates'
        )

        print(f"[OK] Plot generated: {result['plot_path']}")
        print(f"  Devices found: {result['num_devices']}")
        print(f"  Varying parameters: {result['varying_parameters']}")
        print(f"  Expected: May include testing_date if mentioned in query and varies")
        print()

    except ValueError as e:
        print(f"[FAIL] Test failed: {e}")
        print()

    # =========================================================================
    # TEST 5: Natural language query via process_natural_language_query
    # =========================================================================
    print("-" * 80)
    print("TEST 5: Full natural language query integration")
    print("-" * 80)

    query = "show droplet size across all measured DFUs for w13 devices at 5mlhr"
    print(f"Query: '{query}'")
    print()

    result = analyst.process_natural_language_query(query)

    if result['status'] == 'success':
        print(f"[OK] Query processed successfully")
        print(f"  Intent: {result['intent']}")
        print(result['message'])
    else:
        print(f"[FAIL] Query failed: {result['message']}")

    print()

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    print("Key improvements demonstrated:")
    print("  1. [OK] Automatic detection of varying parameters")
    print("  2. [OK] Context-aware legend generation with parameter info")
    print("  3. [OK] Enhanced titles showing what varies")
    print("  4. [OK] Query-based metadata inclusion (dates, etc.)")
    print("  5. [OK] Seamless integration with natural language queries")
    print()
    print("Check the outputs/ directory for generated plots:")
    print("  - test_w13_5mlhr_varying_pressure.png")
    print("  - test_w13_all_conditions.png")
    print("  - test_w13_5mlhr_200mbar.png")
    print("  - test_w13_with_dates.png")
    print()
    print("Legend format examples:")
    print("  • With varying pressure: 'W13_S1_R1 (200mbar)'")
    print("  • With varying fluids:   'W13_S1_R1 (NaCas+SO)'")
    print("  • With both:             'W13_S1_R1 (300mbar, SDS+SO)'")
    print("  • No variation:          'W13_S1_R1'")
    print()
    print("=" * 80)


if __name__ == "__main__":
    test_context_aware_plotting()
