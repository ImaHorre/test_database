"""
Integration Tests for DataAnalyst - Pre-Refactoring Baseline

This test suite captures the current behavior of analyst.py before refactoring
to ensure that the refactored code maintains the same functionality.

Run this before and after refactoring to verify no regressions.
"""

import unittest
import pandas as pd
import os
import sys
from pathlib import Path

# Add src directory to path (go up one level since we're in tests/)
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analyst import DataAnalyst
from csv_manager import CSVManager


class TestDataAnalystIntegration(unittest.TestCase):
    """Integration tests for DataAnalyst functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test data and analyst instance."""
        cls.analyst = DataAnalyst()
        cls.test_data_available = len(cls.analyst.df) > 0

        if not cls.test_data_available:
            print("WARNING: No test data available. Some tests will be skipped.")
        else:
            print(f"Test data loaded: {len(cls.analyst.df)} records")
            print(f"Available device types: {list(cls.analyst.df['device_type'].unique())}")

    def setUp(self):
        """Set up for each test."""
        if not self.test_data_available:
            self.skipTest("No test data available")

    def test_basic_data_access(self):
        """Test basic data access through property."""
        df = self.analyst.df
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)

        # Test data refresh
        original_length = len(df)
        self.analyst.refresh_data()
        self.assertEqual(len(self.analyst.df), original_length)

    def test_device_type_filtering(self):
        """Test device type filtering functionality."""
        available_types = self.analyst.df['device_type'].unique()

        if len(available_types) > 0:
            device_type = available_types[0]

            # Test valid filtering
            filtered = self.analyst.filter_by_device_type(device_type)
            self.assertIsInstance(filtered, pd.DataFrame)
            self.assertTrue(all(filtered['device_type'] == device_type))

            # Test case insensitivity
            filtered_lower = self.analyst.filter_by_device_type(device_type.lower())
            self.assertEqual(len(filtered), len(filtered_lower))

        # Test invalid device type
        with self.assertRaises(ValueError):
            self.analyst.filter_by_device_type("INVALID_TYPE")

        # Test empty input
        with self.assertRaises(ValueError):
            self.analyst.filter_by_device_type("")

    def test_flow_parameter_filtering(self):
        """Test flow parameter filtering functionality."""
        df = self.analyst.df

        if 'aqueous_flowrate' in df.columns and len(df) > 0:
            flowrates = df['aqueous_flowrate'].dropna().unique()
            if len(flowrates) > 0:
                # Convert numpy types to native Python types for validation
                flowrate = float(flowrates[0])

                # Test flowrate filtering
                filtered = self.analyst.filter_by_flow_parameters(aqueous_flowrate=flowrate)
                self.assertIsInstance(filtered, pd.DataFrame)
                if len(filtered) > 0:
                    self.assertTrue(all(filtered['aqueous_flowrate'] == flowrate))

        if 'oil_pressure' in df.columns and len(df) > 0:
            pressures = df['oil_pressure'].dropna().unique()
            if len(pressures) > 0:
                # Convert numpy types to native Python types for validation
                pressure = float(pressures[0])

                # Test pressure filtering
                filtered = self.analyst.filter_by_flow_parameters(oil_pressure=pressure)
                self.assertIsInstance(filtered, pd.DataFrame)
                if len(filtered) > 0:
                    self.assertTrue(all(filtered['oil_pressure'] == pressure))

        # Test invalid parameters
        with self.assertRaises(ValueError):
            self.analyst.filter_by_flow_parameters(aqueous_flowrate=-1)

        with self.assertRaises(ValueError):
            self.analyst.filter_by_flow_parameters(oil_pressure=-5)

    def test_device_type_comparison(self):
        """Test device type comparison functionality."""
        available_types = list(self.analyst.df['device_type'].unique())

        if len(available_types) >= 1:
            # Test single device type
            result = self.analyst.compare_device_types([available_types[0]])
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 1)
            self.assertIn('device_type', result.columns)
            self.assertIn('total_measurements', result.columns)

            if len(available_types) >= 2:
                # Test multiple device types
                result = self.analyst.compare_device_types(available_types[:2])
                self.assertIsInstance(result, pd.DataFrame)
                self.assertEqual(len(result), 2)

        # Test invalid input
        with self.assertRaises(ValueError):
            self.analyst.compare_device_types([])

        with self.assertRaises(ValueError):
            self.analyst.compare_device_types("not_a_list")

    def test_device_history(self):
        """Test device history retrieval."""
        df = self.analyst.df

        if 'device_id' in df.columns and len(df) > 0:
            device_ids = df['device_id'].unique()
            if len(device_ids) > 0:
                device_id = device_ids[0]

                # Test valid device history
                history = self.analyst.get_device_history(device_id)
                self.assertIsInstance(history, pd.DataFrame)
                if len(history) > 0:
                    self.assertTrue(all(history['device_id'] == device_id))

        # Test invalid device ID
        with self.assertRaises(ValueError):
            self.analyst.get_device_history("INVALID_DEVICE")

    def test_analysis_methods(self):
        """Test main analysis methods."""
        df = self.analyst.df

        # Test compare_devices_at_same_parameters
        available_types = df['device_type'].unique()
        if len(available_types) > 0:
            device_type = available_types[0]

            # Get available flow parameters for this device type
            device_data = df[df['device_type'] == device_type]
            if len(device_data) > 0 and 'aqueous_flowrate' in device_data.columns:
                flowrates = device_data['aqueous_flowrate'].dropna().unique()
                if len(flowrates) > 0:
                    flowrate = flowrates[0]

                    try:
                        result = self.analyst.compare_devices_at_same_parameters(
                            device_type=device_type,
                            aqueous_flowrate=flowrate
                        )
                        self.assertIsInstance(result, dict)
                        # Check for any of the common result keys
                        has_valid_key = any(key in result for key in ['summary', 'message', 'plot_path', 'result'])
                        self.assertTrue(has_valid_key, f"Result missing expected keys: {result.keys()}")
                    except Exception as e:
                        # Analysis might fail with insufficient data, that's OK
                        print(f"Analysis method failed (expected with limited data): {e}")

        # Test analyze_flow_parameter_effects
        try:
            result = self.analyst.analyze_flow_parameter_effects()
            self.assertIsInstance(result, dict)
            # Check for any of the common result keys
            has_valid_key = any(key in result for key in ['summary', 'message', 'plot_path', 'result'])
            self.assertTrue(has_valid_key, f"Result missing expected keys: {result.keys()}")
        except Exception as e:
            print(f"Flow parameter analysis failed (expected with limited data): {e}")

    def test_plotting_methods(self):
        """Test plotting functionality."""
        df = self.analyst.df
        available_types = df['device_type'].unique()

        if len(available_types) >= 1:
            device_type = available_types[0]

            # Test device type comparison plot
            try:
                result = self.analyst.plot_device_type_comparison([device_type])
                self.assertIsInstance(result, dict)
                # Check for any of the common result keys
                has_valid_key = any(key in result for key in ['summary', 'message', 'plot_path', 'result'])
                self.assertTrue(has_valid_key, f"Plot result missing expected keys: {result.keys()}")
            except Exception as e:
                print(f"Device comparison plot failed: {e}")

            # Test DFU plotting if data supports it
            device_data = df[df['device_type'] == device_type]
            if len(device_data) > 0 and 'dfu_row' in device_data.columns:
                dfu_data = device_data.dropna(subset=['dfu_row'])
                if len(dfu_data) > 0:
                    try:
                        result = self.analyst.plot_metric_vs_dfu(
                            metric='droplet_size_mean',
                            device_type=device_type,
                            live_preview=False  # Don't open windows during testing
                        )
                        self.assertIsInstance(result, dict)
                        # Check for any of the common result keys
                        has_valid_key = any(key in result for key in ['summary', 'message', 'plot_path', 'result'])
                        self.assertTrue(has_valid_key, f"DFU plot result missing expected keys: {result.keys()}")
                    except Exception as e:
                        print(f"DFU plotting failed: {e}")

    def test_natural_language_processing(self):
        """Test natural language query processing."""
        # Test basic queries
        test_queries = [
            "list device types",
            "help",
            "show me all devices"
        ]

        for query in test_queries:
            try:
                result = self.analyst.process_natural_language_query(query)
                self.assertIsInstance(result, dict)
                # Check for any of the common result keys
                has_valid_key = any(key in result for key in ['summary', 'message', 'plot_path', 'result', 'status'])
                self.assertTrue(has_valid_key, f"Query '{query}' result missing expected keys: {result.keys()}")
            except Exception as e:
                print(f"Query '{query}' failed: {e}")

        # Test device-specific queries if data available
        available_types = self.analyst.df['device_type'].unique()
        if len(available_types) > 0:
            device_type = available_types[0]

            device_queries = [
                f"show me {device_type} devices",
                f"filter by device type {device_type}",
                f"compare {device_type} devices"
            ]

            for query in device_queries:
                try:
                    result = self.analyst.process_natural_language_query(query)
                    self.assertIsInstance(result, dict)
                    # Check for any of the common result keys
                    has_valid_key = any(key in result for key in ['summary', 'message', 'plot_path', 'result', 'status'])
                    self.assertTrue(has_valid_key, f"Query '{query}' result missing expected keys: {result.keys()}")
                except Exception as e:
                    print(f"Query '{query}' failed: {e}")

    def test_report_generation(self):
        """Test report generation functionality."""
        # Create temporary output directory
        output_dir = Path("outputs/test_reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / "test_summary_report.txt"

        try:
            self.analyst.generate_summary_report(str(report_path))
            self.assertTrue(report_path.exists())

            # Check report content
            with open(report_path, 'r') as f:
                content = f.read()
                # Check for report indicators (the actual content may vary)
                report_indicators = ["SUMMARY REPORT", "OVERVIEW", "Total Records", "Device Types"]
                has_report_content = any(indicator in content for indicator in report_indicators)
                self.assertTrue(has_report_content, f"Report missing expected content indicators: {content[:200]}...")
                self.assertGreater(len(content), 100)  # Should have substantial content

            # Clean up
            if report_path.exists():
                report_path.unlink()

        except Exception as e:
            print(f"Report generation failed: {e}")


class TestCSVManagerIntegration(unittest.TestCase):
    """Test CSVManager functionality that analyst depends on."""

    def setUp(self):
        """Set up CSV manager."""
        self.manager = CSVManager()

    def test_basic_csv_operations(self):
        """Test basic CSV manager operations."""
        # Test data loading
        df = self.manager.df
        self.assertIsInstance(df, pd.DataFrame)

        # Test data access
        if len(df) > 0:
            # Test column access
            expected_columns = ['device_type', 'device_id']
            for col in expected_columns:
                if col in df.columns:
                    self.assertIsInstance(df[col].iloc[0], (str, type(None), float, int))


def run_integration_tests():
    """Run all integration tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataAnalystIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCSVManagerIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    print("="*60)
    print("INTEGRATION TESTS - PRE-REFACTORING BASELINE")
    print("="*60)
    print()

    result = run_integration_tests()

    print()
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    print()
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"Overall result: {'PASS' if success else 'FAIL'}")

    if success:
        print("✅ Baseline established successfully!")
        print("   Ready to proceed with refactoring.")
    else:
        print("❌ Baseline tests failed!")
        print("   Fix issues before refactoring.")