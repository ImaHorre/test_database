#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUI Validation Test Suite

Tests the terminal UI functionality programmatically before deployment.
This test can be run by Claude to validate fixes without user interaction.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
from io import StringIO
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard_v2 import SimpleDashboard


def capture_command_output(dashboard, command):
    """Execute a command and capture output."""
    # Save original stdout
    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        # Execute command
        dashboard._process_query(command)

        # Get output
        output = sys.stdout.getvalue()

        return output
    finally:
        # Restore stdout
        sys.stdout = old_stdout


class TUIValidator:
    """Validates TUI functionality programmatically."""

    def __init__(self):
        self.dashboard = SimpleDashboard()
        self.test_results = []

    def test_simple_command_parsing(self):
        """Test that simple commands parse correctly."""
        print("\n[TEST] Simple Command Parsing")
        print("-" * 60)

        test_cases = [
            ("show w13", "show", True),
            ("show w13 at 5mlhr", "filter", True),
            ("show w13 at 5mlhr 200mbar", "filter", True),
            ("list devices", "list", True),
            ("stats w13", "stats", True),
            ("stats w13 at 5mlhr", "stats", True),
            ("show filters", "show_filters", True),
            ("clear filters", "clear_filters", True),
            ("history", "show_history", True),
        ]

        passed = 0
        failed = 0

        for command, expected_type, should_parse in test_cases:
            parsed = self.dashboard.parse_command(command)

            if should_parse:
                if parsed and parsed['type'] == expected_type:
                    print(f"  ✓ '{command}' -> {expected_type}")
                    passed += 1
                else:
                    print(f"  ✗ '{command}' failed (expected {expected_type}, got {parsed})")
                    failed += 1
            else:
                if not parsed:
                    print(f"  ✓ '{command}' correctly rejected")
                    passed += 1
                else:
                    print(f"  ✗ '{command}' should not have parsed")
                    failed += 1

        print(f"\nResults: {passed} passed, {failed} failed")
        self.test_results.append(("Simple Command Parsing", passed, failed))
        return failed == 0

    def test_session_state_management(self):
        """Test that session state is tracked correctly."""
        print("\n[TEST] Session State Management")
        print("-" * 60)

        # Clear any existing state
        self.dashboard.session_state['current_filters'] = {}

        # Execute filter command
        parsed = self.dashboard.parse_command("show w13 at 5mlhr")
        if parsed:
            self.dashboard.execute_command(parsed)

        # Check filters were set
        filters = self.dashboard.session_state['current_filters']

        tests_passed = 0
        tests_failed = 0

        # Test 1: Device type filter
        if filters.get('device_type') == 'W13':
            print("  ✓ Device type filter set correctly")
            tests_passed += 1
        else:
            print(f"  ✗ Device type filter incorrect: {filters.get('device_type')}")
            tests_failed += 1

        # Test 2: Flowrate filter
        if filters.get('flowrate') == 5:
            print("  ✓ Flowrate filter set correctly")
            tests_passed += 1
        else:
            print(f"  ✗ Flowrate filter incorrect: {filters.get('flowrate')}")
            tests_failed += 1

        # Test 3: Prompt shows filters
        prompt = self.dashboard._get_prompt()
        if "W13" in prompt and "5mlhr" in prompt:
            print(f"  ✓ Prompt shows active filters: {prompt.strip()}")
            tests_passed += 1
        else:
            print(f"  ✗ Prompt doesn't show filters: {prompt.strip()}")
            tests_failed += 1

        # Test 4: Clear filters
        parsed_clear = self.dashboard.parse_command("clear filters")
        if parsed_clear:
            self.dashboard.execute_command(parsed_clear)

        if len(self.dashboard.session_state['current_filters']) == 0:
            print("  ✓ Filters cleared successfully")
            tests_passed += 1
        else:
            print("  ✗ Filters not cleared")
            tests_failed += 1

        print(f"\nResults: {tests_passed} passed, {tests_failed} failed")
        self.test_results.append(("Session State Management", tests_passed, tests_failed))
        return tests_failed == 0

    def test_analysis_counting(self):
        """Test that analysis counting shows meaningful counts."""
        print("\n[TEST] Analysis Counting Logic")
        print("-" * 60)

        # Get sample data
        df = self.dashboard.df

        # Filter to specific device
        device_data = df[df['device_id'] == 'W13_S1_R1'].head(10)

        if len(device_data) == 0:
            print("  ⚠ No test data available for analysis counting")
            self.test_results.append(("Analysis Counting", 0, 1))
            return False

        # Run analysis count
        counts = self.dashboard._count_complete_analyses(device_data)

        tests_passed = 0
        tests_failed = 0

        # Test 1: Returns correct structure
        required_keys = ['complete_droplet', 'complete_freq', 'partial', 'details']
        if all(key in counts for key in required_keys):
            print("  ✓ Analysis counts structure correct")
            tests_passed += 1
        else:
            print(f"  ✗ Missing keys in counts: {counts.keys()}")
            tests_failed += 1

        # Test 2: Details list is populated
        if 'details' in counts and isinstance(counts['details'], list):
            print(f"  ✓ Analysis details available ({len(counts['details'])} conditions)")
            tests_passed += 1
        else:
            print("  ✗ Analysis details not generated")
            tests_failed += 1

        # Test 3: Counts are numeric
        for key in ['complete_droplet', 'complete_freq', 'partial']:
            if key in counts and isinstance(counts[key], int):
                print(f"  ✓ {key}: {counts[key]}")
                tests_passed += 1
            else:
                print(f"  ✗ {key} is not an integer")
                tests_failed += 1

        print(f"\nResults: {tests_passed} passed, {tests_failed} failed")
        self.test_results.append(("Analysis Counting", tests_passed, tests_failed))
        return tests_failed == 0

    def test_data_availability(self):
        """Test that database has data and key columns exist."""
        print("\n[TEST] Data Availability")
        print("-" * 60)

        df = self.dashboard.df

        tests_passed = 0
        tests_failed = 0

        # Test 1: Data loaded
        if len(df) > 0:
            print(f"  ✓ Database loaded: {len(df)} records")
            tests_passed += 1
        else:
            print("  ✗ No data in database")
            tests_failed += 1

        # Test 2: Required columns exist
        required_columns = [
            'device_type', 'device_id', 'aqueous_flowrate',
            'oil_pressure', 'dfu_row', 'measurement_type'
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]

        if not missing_columns:
            print(f"  ✓ All required columns present")
            tests_passed += 1
        else:
            print(f"  ✗ Missing columns: {missing_columns}")
            tests_failed += 1

        # Test 3: Device types available
        device_types = df['device_type'].unique()
        if len(device_types) > 0:
            print(f"  ✓ Device types available: {', '.join(device_types)}")
            tests_passed += 1
        else:
            print("  ✗ No device types found")
            tests_failed += 1

        # Test 4: Flow parameters available
        flowrates = df['aqueous_flowrate'].dropna().unique()
        if len(flowrates) > 0:
            print(f"  ✓ Flow rates available: {len(flowrates)} unique values")
            tests_passed += 1
        else:
            print("  ✗ No flow rates found")
            tests_failed += 1

        print(f"\nResults: {tests_passed} passed, {tests_failed} failed")
        self.test_results.append(("Data Availability", tests_passed, tests_failed))
        return tests_failed == 0

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        print("\n[TEST] Error Handling")
        print("-" * 60)

        tests_passed = 0
        tests_failed = 0

        # Test 1: Invalid device type
        parsed = self.dashboard.parse_command("show w99 at 5mlhr")
        if parsed:
            # Execute and check for error handling
            try:
                # This should trigger validation error
                self.dashboard.execute_command(parsed)
                print("  ✓ Invalid device type handled (no crash)")
                tests_passed += 1
            except Exception as e:
                print(f"  ✗ Crashed on invalid device: {e}")
                tests_failed += 1
        else:
            print("  ⚠ Command didn't parse (expected)")
            tests_passed += 1

        # Test 2: Invalid command
        parsed = self.dashboard.parse_command("invalid command xyz")
        if not parsed:
            print("  ✓ Invalid command rejected correctly")
            tests_passed += 1
        else:
            print(f"  ✗ Invalid command accepted: {parsed}")
            tests_failed += 1

        print(f"\nResults: {tests_passed} passed, {tests_failed} failed")
        self.test_results.append(("Error Handling", tests_passed, tests_failed))
        return tests_failed == 0

    def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 70)
        print("TUI VALIDATION TEST SUITE")
        print("=" * 70)

        all_tests = [
            self.test_data_availability,
            self.test_simple_command_parsing,
            self.test_session_state_management,
            self.test_analysis_counting,
            self.test_error_handling,
        ]

        for test_func in all_tests:
            try:
                test_func()
            except Exception as e:
                print(f"\n[ERROR] Test {test_func.__name__} crashed: {e}")
                import traceback
                traceback.print_exc()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        total_passed = 0
        total_failed = 0

        for test_name, passed, failed in self.test_results:
            status = "✓ PASS" if failed == 0 else "✗ FAIL"
            print(f"{status} {test_name}: {passed} passed, {failed} failed")
            total_passed += passed
            total_failed += failed

        print("-" * 70)
        print(f"TOTAL: {total_passed} passed, {total_failed} failed")
        print("=" * 70)

        return total_failed == 0


def main():
    """Run validation suite."""
    validator = TUIValidator()
    success = validator.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
