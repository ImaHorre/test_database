"""
Test script for DFU-based plotting functionality
"""
from src import DataAnalyst

def test_dfu_query():
    """Test the specific DFU query from the user."""

    # Initialize analyst
    print("Initializing DataAnalyst...")
    analyst = DataAnalyst()
    print(f"Loaded {len(analyst.df)} measurements\n")

    # Test query 1: The exact user query
    query1 = "show me the droplet size across all measured DFUs for each w13 device that was tested at 5mlhr200mbar"
    print("=" * 80)
    print(f"Testing Query 1: {query1}")
    print("=" * 80)

    result1 = analyst.process_natural_language_query(query1)

    print(f"\nStatus: {result1['status']}")
    print(f"Intent: {result1['intent']}")
    print(f"\nMessage:\n{result1['message']}")

    if result1.get('plot_path'):
        print(f"\nPlot saved to: {result1['plot_path']}")

    print("\n")

    # Test query 2: Frequency instead of droplet size
    query2 = "show me the frequency across all measured DFUs for each w13 device that was tested at 5mlhr200mbar"
    print("=" * 80)
    print(f"Testing Query 2: {query2}")
    print("=" * 80)

    result2 = analyst.process_natural_language_query(query2)

    print(f"\nStatus: {result2['status']}")
    print(f"Intent: {result2['intent']}")
    print(f"\nMessage:\n{result2['message']}")

    if result2.get('plot_path'):
        print(f"\nPlot saved to: {result2['plot_path']}")

    print("\n")

    # Test query 3: All W13 devices (no parameter filter)
    query3 = "show droplet size across all measured DFUs for w13 devices"
    print("=" * 80)
    print(f"Testing Query 3: {query3}")
    print("=" * 80)

    result3 = analyst.process_natural_language_query(query3)

    print(f"\nStatus: {result3['status']}")
    print(f"Intent: {result3['intent']}")
    print(f"\nMessage:\n{result3['message']}")

    if result3.get('plot_path'):
        print(f"\nPlot saved to: {result3['plot_path']}")

    print("\n")

    # Direct method call test
    print("=" * 80)
    print("Testing Direct Method Call")
    print("=" * 80)

    try:
        result4 = analyst.plot_metric_vs_dfu(
            metric='droplet_size_mean',
            device_type='W13',
            aqueous_flowrate=5,
            oil_pressure=200,
            output_path='outputs/test_dfu_direct_call.png'
        )

        print(f"\nDirect method call successful!")
        print(f"Found {result4['num_devices']} device(s): {', '.join(result4['devices'])}")
        print(f"DFU rows: {result4['dfu_rows_measured']}")
        print(f"Total measurements: {result4['total_measurements']}")
        print(f"Plot saved to: {result4['plot_path']}")
    except Exception as e:
        print(f"\nDirect method call failed: {e}")

    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)

if __name__ == "__main__":
    test_dfu_query()
