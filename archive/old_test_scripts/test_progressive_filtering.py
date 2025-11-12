"""
Test script for progressive filtering feature.
"""

from dashboard_v2 import SimpleDashboard

def test_parameter_detection():
    """Test the parameter type detection."""
    print("Testing parameter type detection...")
    print("=" * 70)

    dashboard = SimpleDashboard()

    test_values = [
        "300mbar",
        "300",
        "10mlhr",
        "10",
        "W13",
        "W14",
        "W13_S1_R1",
        "DFU1",
        "SDS_SO",
        "NaCas_SO",
        "unknown_value"
    ]

    for value in test_values:
        result = dashboard._detect_parameter_type(value)
        print(f"{value:20s} -> Type: {result['type']:15s} | Value: {str(result['value']):15s} | Confidence: {result['confidence']}")

    print()
    print("=" * 70)
    print()

def test_prompt_formatting():
    """Test prompt formatting with different filter combinations."""
    print("Testing prompt formatting...")
    print("=" * 70)

    dashboard = SimpleDashboard()

    # Test different filter combinations
    test_cases = [
        {},
        {'device_type': 'W13'},
        {'device_type': 'W13', 'flowrate': 10},
        {'device_type': 'W13', 'flowrate': 10, 'pressure': 300},
        {'device_type': 'W13', 'flowrate': 10, 'pressure': 300, 'device': 'W13_S1_R1'},
        {'device_type': 'W13', 'flowrate': 10, 'pressure': 300, 'device': 'W13_S1_R1', 'fluid': 'SDS_SO'},
        {'device_type': 'W13', 'flowrate': 10, 'pressure': 300, 'device': 'W13_S1_R1', 'fluid': 'SDS_SO', 'dfu': 'DFU1'},
    ]

    for filters in test_cases:
        dashboard.session_state['current_filters'] = filters
        prompt = dashboard._get_prompt()
        filter_desc = str(filters) if filters else "No filters"
        print(f"{filter_desc:80s} -> {prompt}")

    print()
    print("=" * 70)
    print()

def test_command_parsing():
    """Test command parsing for progressive filtering."""
    print("Testing command parsing for progressive filtering...")
    print("=" * 70)

    dashboard = SimpleDashboard()

    # First set an initial filter
    dashboard.session_state['current_filters'] = {'device_type': 'W13', 'flowrate': 10}

    test_commands = [
        "300mbar",
        "show 300mbar",
        "show W13_S1_R1",
        "W13_S1_R1",
        "show SDS_SO",
        "DFU1",
        "remove 300mbar",
        "undo",
        "back",
    ]

    for cmd in test_commands:
        result = dashboard.parse_command(cmd)
        if result:
            print(f"{cmd:30s} -> Type: {result['type']:25s} | Value: {result.get('value', 'N/A')}")
        else:
            print(f"{cmd:30s} -> Not recognized")

    print()
    print("=" * 70)
    print()

if __name__ == "__main__":
    print("\n")
    print("PROGRESSIVE FILTERING FEATURE TEST")
    print("=" * 70)
    print()

    test_parameter_detection()
    test_prompt_formatting()
    test_command_parsing()

    print("\nAll tests completed!")
