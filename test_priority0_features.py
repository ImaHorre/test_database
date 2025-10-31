#!/usr/bin/env python3
"""
Automated tests for Priority 0 features implementation.
Run this to validate core functionality before user testing.
"""

import sys
from dashboard_v2 import SimpleDashboard
import pandas as pd

def test_session_state():
    """Test session state management functionality."""
    print("Testing Session State Management...")

    dashboard = SimpleDashboard()

    # Test 1: Session state initialization
    assert 'current_filters' in dashboard.session_state
    assert 'query_history' in dashboard.session_state
    print("  [OK] Session state initialized correctly")

    # Test 2: Prompt generation
    empty_prompt = dashboard._get_prompt()
    assert empty_prompt == ">>> "
    print("  ✅ Empty prompt generated correctly")

    # Test 3: Filter prompt
    dashboard.session_state['current_filters'] = {'device_type': 'W13', 'flowrate': 5}
    filtered_prompt = dashboard._get_prompt()
    assert "[W13@5mlhr]" in filtered_prompt
    print("  ✅ Filtered prompt generated correctly")

    # Test 4: Session update
    dashboard._update_session_state("test query", "test_type", {'test': 'value'})
    assert len(dashboard.session_state['query_history']) == 1
    print("  ✅ Session state updates correctly")

    print("✅ Session State Management: PASSED\n")
    return True

def test_analysis_counting():
    """Test meaningful analysis counting logic."""
    print("🧪 Testing Analysis Counting Logic...")

    dashboard = SimpleDashboard()
    df = dashboard.df

    # Test 1: Basic analysis counting
    test_data = df.head(100)  # Use subset for faster testing
    counts = dashboard._count_complete_analyses(test_data)

    assert isinstance(counts, dict)
    assert 'complete_droplet' in counts
    assert 'complete_freq' in counts
    assert 'details' in counts
    print("  ✅ Analysis counting returns correct structure")

    # Test 2: Details contain required fields
    if counts['details']:
        detail = counts['details'][0]
        assert 'condition' in detail
        assert 'status' in detail
        print("  ✅ Analysis details contain required fields")

    print("✅ Analysis Counting Logic: PASSED\n")
    return True

def test_plot_confirmation():
    """Test plot confirmation and preview functionality."""
    print("🧪 Testing Plot Confirmation...")

    dashboard = SimpleDashboard()

    # Test 1: Plot command detection
    plot_queries = ['plot w13', 'graph devices', 'chart data']
    non_plot_queries = ['show w13', 'stats w13', 'filter data']

    for query in plot_queries:
        assert dashboard._is_plot_command(query), f"Failed to detect plot command: {query}"

    for query in non_plot_queries:
        assert not dashboard._is_plot_command(query), f"False positive for plot command: {query}"

    print("  ✅ Plot command detection working correctly")

    # Test 2: Entity extraction
    query = "plot w13 at 5mlhr 200mbar"
    entities = dashboard._extract_plot_entities(query)

    assert entities.get('device_type') == 'W13'
    assert entities.get('flowrate') == 5
    assert entities.get('pressure') == 200
    print("  ✅ Entity extraction working correctly")

    # Test 3: Preview data generation
    preview_data = dashboard._get_plot_preview_data(entities)
    assert isinstance(preview_data, pd.DataFrame)
    print("  ✅ Preview data generation working correctly")

    print("✅ Plot Confirmation: PASSED\n")
    return True

def test_command_parsing():
    """Test enhanced command parsing functionality."""
    print("🧪 Testing Enhanced Command Parsing...")

    dashboard = SimpleDashboard()

    # Test 1: Session commands
    session_commands = [
        ('show filters', 'show_filters'),
        ('clear filters', 'clear_filters'),
        ('history', 'show_history'),
        ('repeat last', 'repeat_last')
    ]

    for cmd, expected_type in session_commands:
        parsed = dashboard.parse_command(cmd)
        assert parsed is not None, f"Failed to parse: {cmd}"
        assert parsed['type'] == expected_type, f"Wrong type for {cmd}: {parsed['type']}"

    print("  ✅ Session commands parsed correctly")

    # Test 2: Enhanced stats commands
    stats_commands = [
        ('stats w13', {'type': 'stats', 'device_type': 'W13'}),
        ('stats w13 at 5mlhr', {'type': 'stats', 'device_type': 'W13', 'flowrate': 5, 'pressure': None}),
        ('stats w13 at 5mlhr 200mbar', {'type': 'stats', 'device_type': 'W13', 'flowrate': 5, 'pressure': 200})
    ]

    for cmd, expected in stats_commands:
        parsed = dashboard.parse_command(cmd)
        assert parsed is not None, f"Failed to parse: {cmd}"
        for key, value in expected.items():
            assert parsed.get(key) == value, f"Wrong {key} for {cmd}: {parsed.get(key)} != {value}"

    print("  ✅ Enhanced stats commands parsed correctly")

    print("✅ Enhanced Command Parsing: PASSED\n")
    return True

def run_all_tests():
    """Run all automated tests."""
    print("🚀 Running Priority 0 Feature Tests\n")
    print("=" * 50)

    tests = [
        test_session_state,
        test_analysis_counting,
        test_plot_confirmation,
        test_command_parsing
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}\n")

    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All automated tests PASSED!")
        print("\n🎯 Ready for user testing!")
        print("\nNext steps:")
        print("1. Run the dashboard: python dashboard_v2.py")
        print("2. Test the workflows outlined above")
        print("3. Report back on user experience")
        return True
    else:
        print("⚠️  Some tests failed - review implementations")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)