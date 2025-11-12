"""
Test script for Phase 1 Common Analysis Methods
Tests all new analysis capabilities with real data
"""

from src import DataAnalyst

def test_all_phase1_methods():
    """Test all Phase 1 common analysis methods."""

    print("="*70)
    print("PHASE 1 ANALYSIS METHODS - TEST SUITE")
    print("="*70)

    analyst = DataAnalyst()

    print(f"\nDatabase loaded: {len(analyst.df)} records")
    print(f"Device types: {analyst.df['device_type'].unique()}")
    print(f"Devices: {analyst.df['device_id'].unique()}")

    # Test 1: Compare devices at same parameters
    print("\n" + "="*70)
    print("TEST 1: Compare devices at same flow parameters")
    print("="*70)
    try:
        result = analyst.compare_devices_at_same_parameters(
            device_type='W13',
            aqueous_flowrate=30,
            output_path='outputs/test_device_comparison_30mlhr.png'
        )
        print("\n[SUCCESS] Device comparison at 30ml/hr")
        print(f"  Found {len(result)} devices")
        print("\nResults:")
        print(result)
    except Exception as e:
        print(f"[FAILED] {e}")

    # Test 2: Analyze flow parameter effects
    print("\n" + "="*70)
    print("TEST 2: Analyze flow parameter effects")
    print("="*70)
    try:
        result = analyst.analyze_flow_parameter_effects(
            device_type='W13',
            parameter='aqueous_flowrate',
            metric='droplet_size_mean',
            output_path='outputs/test_flowrate_effect.png'
        )
        print("\n[SUCCESS] Flow parameter effect analysis")
        print(f"  Correlation: {result['correlation']}")
        print(f"  Total measurements: {result['total_measurements']}")
        print("\nGrouped Statistics:")
        print(result['grouped_stats'])
    except Exception as e:
        print(f"[FAILED] {e}")

    # Test 3: Track device over time
    print("\n" + "="*70)
    print("TEST 3: Track device over time")
    print("="*70)
    try:
        result = analyst.track_device_over_time(
            device_id='W13_S1_R1',
            output_path='outputs/test_temporal_tracking.png'
        )
        print("\n[SUCCESS] Device temporal tracking")
        print(f"  Tracked {len(result)} tests")
        print(f"  Date range: {result['testing_date'].min()} to {result['testing_date'].max()}")
        print("\nFirst 5 tests:")
        print(result[['testing_date', 'aqueous_flowrate', 'oil_pressure', 'droplet_size_mean']].head())
    except Exception as e:
        print(f"[FAILED] {e}")

    # Test 4: Compare DFU row performance
    print("\n" + "="*70)
    print("TEST 4: Compare DFU row performance")
    print("="*70)
    try:
        result = analyst.compare_dfu_row_performance(
            device_type='W13',
            metric='droplet_size_mean',
            output_path='outputs/test_dfu_comparison.png'
        )
        print("\n[SUCCESS] DFU row comparison")
        print(f"  Compared {len(result)} DFU rows")
        print("\nResults:")
        print(result)
    except Exception as e:
        print(f"[FAILED] {e}")

    # Test 5: Compare fluid types
    print("\n" + "="*70)
    print("TEST 5: Compare fluid types")
    print("="*70)
    try:
        result = analyst.compare_fluid_types(
            device_type='W13',
            output_path='outputs/test_fluid_comparison.png'
        )
        print("\n[SUCCESS] Fluid type comparison")
        print(f"  Compared {len(result)} fluid combinations")
        print("\nResults:")
        print(result)
    except Exception as e:
        print(f"[FAILED] {e}")

    # Test 6: Oil pressure effect
    print("\n" + "="*70)
    print("TEST 6: Oil pressure effect on frequency")
    print("="*70)
    try:
        result = analyst.analyze_flow_parameter_effects(
            device_type='W14',
            parameter='oil_pressure',
            metric='frequency_mean',
            output_path='outputs/test_pressure_effect.png'
        )
        print("\n[SUCCESS] Oil pressure effect analysis")
        print(f"  Correlation: {result['correlation']}")
        print(f"  Total measurements: {result['total_measurements']}")
    except Exception as e:
        print(f"[FAILED] {e}")

    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print("\nCheck the 'outputs/' directory for generated plots")


if __name__ == "__main__":
    test_all_phase1_methods()
