"""
Data Analyst Agent

Processes queries, generates insights, and creates visualizations.
Provides interactive guidance and dynamic plotting capabilities.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
import logging
from pathlib import Path

from .csv_manager import CSVManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataAnalyst:
    """
    Analyzes measurement data and generates reports/visualizations.

    Supports:
    - Device type comparisons (W13 vs W14)
    - Flow parameter analysis
    - Individual device tracking
    - Interactive query processing
    """

    def __init__(self, csv_manager: CSVManager = None):
        """
        Initialize Data Analyst.

        Args:
            csv_manager: CSVManager instance (creates new if None)
        """
        self.manager = csv_manager or CSVManager()
        # Note: Always access data via self.manager.df to avoid stale references

        # Set up plotting style
        sns.set_style("whitegrid")
        plt.rcParams['figure.dpi'] = 300

    @property
    def df(self) -> pd.DataFrame:
        """
        Get current DataFrame from CSVManager.

        This property ensures we always access fresh data from the manager,
        preventing stale reference issues.

        Returns:
            Current DataFrame from CSVManager
        """
        return self.manager.df

    def refresh_data(self):
        """
        Reload data from CSV Manager.

        Natural language: "Refresh the data" or "Reload the database"
        """
        self.manager.df = self.manager._load_or_create_database()
        logger.info(f"Data refreshed: {len(self.df)} records")

    def filter_by_device_type(self, device_type: str) -> pd.DataFrame:
        """
        Filter data by device type (W13, W14, etc.).

        Natural language: "Show me all W13 devices" or "Filter by device type W14"

        Args:
            device_type: Device type string (e.g., 'W13', 'W14')

        Returns:
            Filtered DataFrame

        Raises:
            ValueError: If device_type is invalid or not found in database
        """
        # Input validation
        if not device_type or not isinstance(device_type, str):
            raise ValueError(f"Invalid device_type: must be a non-empty string")

        device_type = device_type.strip().upper()

        # Check if device type exists in database
        available_types = self.df['device_type'].unique()
        if len(available_types) > 0 and device_type not in available_types:
            logger.warning(
                f"Device type '{device_type}' not found. Available types: {list(available_types)}"
            )
            raise ValueError(
                f"Device type '{device_type}' not found. Available: {list(available_types)}"
            )

        result = self.df[self.df['device_type'] == device_type].copy()
        logger.info(f"Filtered to {device_type}: {len(result)} records")
        return result

    def filter_by_flow_parameters(
        self,
        aqueous_flowrate: Optional[int] = None,
        oil_pressure: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Filter data by flow parameters.

        Natural language: "Show me devices with 5 ml/hr flowrate and 150 mbar pressure"
        or "Filter by flowrate 5" or "Show 500 mbar pressure tests"

        Args:
            aqueous_flowrate: Flowrate in ml/hr (e.g., 5)
            oil_pressure: Pressure in mbar (e.g., 150)

        Returns:
            Filtered DataFrame

        Raises:
            ValueError: If parameters are invalid (negative or non-numeric)
        """
        result = self.df.copy()

        # Input validation for aqueous_flowrate
        if aqueous_flowrate is not None:
            if not isinstance(aqueous_flowrate, (int, float)) or aqueous_flowrate < 0:
                raise ValueError(
                    f"Invalid aqueous_flowrate: must be a non-negative number, got {aqueous_flowrate}"
                )
            result = result[result['aqueous_flowrate'] == aqueous_flowrate]

        # Input validation for oil_pressure
        if oil_pressure is not None:
            if not isinstance(oil_pressure, (int, float)) or oil_pressure < 0:
                raise ValueError(
                    f"Invalid oil_pressure: must be a non-negative number, got {oil_pressure}"
                )
            result = result[result['oil_pressure'] == oil_pressure]

        logger.info(
            f"Filtered by flow params (flowrate={aqueous_flowrate}, "
            f"pressure={oil_pressure}): {len(result)} records"
        )
        return result

    def compare_device_types(
        self,
        device_types: List[str],
        metric: str = 'count'
    ) -> pd.DataFrame:
        """
        Compare different device types side-by-side.

        Natural language: "Compare W13 and W14 devices" or "Show me comparison of device types"

        Args:
            device_types: List of device types (e.g., ['W13', 'W14'])
            metric: What to compare ('count', 'unique_tests', etc.)

        Returns:
            Comparison DataFrame with metrics for each device type

        Raises:
            ValueError: If device_types is empty or invalid
        """
        if not device_types or not isinstance(device_types, list):
            raise ValueError("device_types must be a non-empty list of strings")

        results = []

        for device_type in device_types:
            try:
                filtered = self.filter_by_device_type(device_type)

                comparison = {
                    'device_type': device_type,
                    'total_measurements': len(filtered),
                    'unique_devices': filtered['device_id'].nunique(),
                    'unique_tests': filtered.groupby([
                        'device_id', 'testing_date', 'aqueous_flowrate', 'oil_pressure'
                    ]).ngroups if len(filtered) > 0 else 0,
                    'date_range': f"{filtered['testing_date'].min()} to {filtered['testing_date'].max()}" if len(filtered) > 0 else 'N/A'
                }
                results.append(comparison)
            except ValueError as e:
                logger.warning(f"Skipping device type {device_type}: {e}")
                continue

        if not results:
            raise ValueError(f"No valid device types found in: {device_types}")

        comparison_df = pd.DataFrame(results)
        logger.info(f"Compared {len(device_types)} device types")
        return comparison_df

    def get_device_history(self, device_id: str) -> pd.DataFrame:
        """
        Get all tests for a specific device over time, sorted chronologically.

        Natural language: "Show me the history of device W13_S1_R2" or
        "What tests were run on W13_S1_R2 over time?"

        Args:
            device_id: Full device ID (e.g., 'W13_S1_R2')

        Returns:
            DataFrame of device history sorted by testing date

        Raises:
            ValueError: If device_id is invalid or not found
        """
        if not device_id or not isinstance(device_id, str):
            raise ValueError("device_id must be a non-empty string")

        device_id = device_id.strip().upper()

        result = self.df[self.df['device_id'] == device_id].copy()

        if len(result) == 0:
            available_devices = self.df['device_id'].unique()
            logger.warning(f"Device {device_id} not found in database")
            raise ValueError(
                f"Device '{device_id}' not found. Available devices: {list(available_devices)[:10]}"
            )

        result = result.sort_values('testing_date')
        logger.info(f"Device {device_id} history: {len(result)} records")
        return result

    def plot_device_type_comparison(
        self,
        device_types: List[str],
        output_path: str = 'outputs/device_comparison.png'
    ):
        """
        Create bar plot comparing device types.

        Natural language: "Plot comparison of W13 and W14 devices" or
        "Create a chart comparing device types"

        Args:
            device_types: List of device types to compare
            output_path: Where to save the plot

        Raises:
            ValueError: If comparison fails or no valid data
            IOError: If plot cannot be saved
        """
        try:
            comparison = self.compare_device_types(device_types)

            if len(comparison) == 0:
                raise ValueError("No data available to plot")

            fig, axes = plt.subplots(1, 2, figsize=(14, 6))

            # Plot 1: Total measurements
            axes[0].bar(comparison['device_type'], comparison['total_measurements'])
            axes[0].set_title('Total Measurements by Device Type', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Device Type', fontsize=10, fontweight='bold')
            axes[0].set_ylabel('Number of Measurements', fontsize=10, fontweight='bold')
            axes[0].grid(True, alpha=0.3)

            # Plot 2: Unique devices tested
            axes[1].bar(comparison['device_type'], comparison['unique_devices'], color='green')
            axes[1].set_title('Unique Devices Tested', fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Device Type', fontsize=10, fontweight='bold')
            axes[1].set_ylabel('Number of Unique Devices', fontsize=10, fontweight='bold')
            axes[1].grid(True, alpha=0.3)

            plt.tight_layout()

            # Save plot
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, bbox_inches='tight')
            logger.info(f"Plot saved: {output_path}")
            plt.close()

        except Exception as e:
            plt.close('all')  # Clean up any open figures
            logger.error(f"Failed to create device comparison plot: {e}")
            raise

    def plot_flow_parameter_analysis(
        self,
        device_type: str,
        output_path: str = 'outputs/flow_parameter_analysis.png'
    ):
        """
        Analyze and plot flow parameter distribution for a device type.

        Natural language: "Plot flow parameters for W13 devices" or
        "Show me flowrate vs pressure distribution for W14"

        Args:
            device_type: Device type to analyze
            output_path: Where to save the plot

        Raises:
            ValueError: If no data for device type or plotting fails
            IOError: If plot cannot be saved
        """
        try:
            data = self.filter_by_device_type(device_type)

            if len(data) == 0:
                logger.warning(f"No data for device type: {device_type}")
                raise ValueError(f"No data available for device type: {device_type}")

            # Group by flow parameters and count tests
            flow_summary = data.groupby(['aqueous_flowrate', 'oil_pressure']).size().reset_index(name='count')

            if len(flow_summary) == 0:
                raise ValueError(f"No flow parameter data available for {device_type}")

            fig, ax = plt.subplots(figsize=(12, 8))

            # Create scatter plot with size representing count
            scatter = ax.scatter(
                flow_summary['aqueous_flowrate'],
                flow_summary['oil_pressure'],
                s=flow_summary['count'] * 50,  # Size based on count
                alpha=0.6,
                c=flow_summary['count'],
                cmap='viridis'
            )

            # Add labels for each point
            for idx, row in flow_summary.iterrows():
                ax.annotate(
                    f"n={row['count']}",
                    (row['aqueous_flowrate'], row['oil_pressure']),
                    fontsize=8,
                    ha='center'
                )

            ax.set_title(
                f'Flow Parameter Distribution - {device_type}\n(Size = number of tests)',
                fontsize=12,
                fontweight='bold'
            )
            ax.set_xlabel('Aqueous Flowrate (ml/hr)', fontsize=10, fontweight='bold')
            ax.set_ylabel('Oil Pressure (mbar)', fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3)

            plt.colorbar(scatter, label='Number of Tests')
            plt.tight_layout()

            # Save plot
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, bbox_inches='tight')
            logger.info(f"Plot saved: {output_path}")
            plt.close()

        except Exception as e:
            plt.close('all')  # Clean up any open figures
            logger.error(f"Failed to create flow parameter plot: {e}")
            raise

    def generate_summary_report(self, output_path: str = 'outputs/summary_report.txt'):
        """
        Generate a text summary report of all data.

        Natural language: "Generate a summary report" or "Show me an overview of all data"

        Args:
            output_path: Where to save the report

        Raises:
            IOError: If report cannot be saved
        """
        try:
            summary = self.manager.get_summary()

            report_lines = [
                "="*70,
                "ONEDRIVE DATABASE SCANNER - SUMMARY REPORT",
                "="*70,
                f"Generated: {pd.Timestamp.now()}",
                "",
                "OVERVIEW",
                "-" * 70,
                f"Total Records: {summary['total_records']}",
                f"Device Types: {summary['device_types']}",
                f"Unique Devices: {summary['unique_devices']}",
                "",
                "DATE RANGE",
                "-" * 70,
                f"Earliest Test: {summary['date_range']['earliest']}",
                f"Latest Test: {summary['date_range']['latest']}",
                "",
                "MEASUREMENT FILES",
                "-" * 70,
                f"CSV Files (DFU measurements): {summary['measurement_files']['csv']}",
                f"TXT Files (Frequency data): {summary['measurement_files']['txt']}",
                "",
                "DATA QUALITY",
                "-" * 70,
            ]

            for quality, count in summary['parse_quality'].items():
                report_lines.append(f"{quality.capitalize()}: {count}")

            report_lines.extend([
                "",
                "DEVICE BREAKDOWN",
                "-" * 70,
            ])

            # Device breakdown
            if len(self.df) > 0:
                device_counts = self.df['device_type'].value_counts()
                for device, count in device_counts.items():
                    report_lines.append(f"{device}: {count} measurements")

            report_lines.append("="*70)

            # Write report
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write('\n'.join(report_lines))

            logger.info(f"Report saved: {output_path}")

            # Also print to console
            print('\n'.join(report_lines))

        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            raise

    def process_natural_language_query(self, query: str) -> Dict:
        """
        Process natural language queries and route to appropriate analysis methods.

        This is a placeholder for future NLP integration with Claude Code.
        The method will interpret user queries in natural language and automatically
        call the appropriate analysis methods with correct parameters.

        Natural language examples:
        - "Compare W13 and W14 devices"
        - "Show me flow parameters for W13 at 5 ml/hr"
        - "Plot device history for W13_S1_R2"
        - "Generate a summary report"

        Args:
            query: Natural language query string

        Returns:
            Dictionary containing:
            - 'method': Name of method that should be called
            - 'params': Dictionary of parameters for that method
            - 'result': Actual result (when implemented)

        TODO: Implement NLP parsing logic
        TODO: Map query intents to method calls
        TODO: Extract parameters from natural language
        TODO: Handle ambiguous queries with clarifying questions
        TODO: Support multi-step analysis workflows

        Example implementation approach:
        1. Parse query to identify intent (compare, filter, plot, report)
        2. Extract entities (device types, flow params, device IDs)
        3. Map to appropriate method with parameters
        4. Execute and return results
        5. For unclear queries, use AskUserQuestion tool

        Integration notes:
        - This method will be called from main Claude Code chat
        - Results can be DataFrames, plot paths, or formatted text
        - Error messages should be user-friendly
        - Support chaining multiple operations
        """
        # Placeholder implementation
        logger.info(f"Processing natural language query: {query}")

        # TODO: Implement actual NLP processing
        # For now, return structure showing what will be implemented
        return {
            'status': 'not_implemented',
            'query': query,
            'message': 'NLP integration coming soon. Use direct method calls for now.',
            'available_methods': [
                'filter_by_device_type(device_type)',
                'filter_by_flow_parameters(aqueous_flowrate, oil_pressure)',
                'compare_device_types(device_types)',
                'get_device_history(device_id)',
                'plot_device_type_comparison(device_types, output_path)',
                'plot_flow_parameter_analysis(device_type, output_path)',
                'generate_summary_report(output_path)'
            ]
        }


# Example usage
if __name__ == "__main__":
    analyst = DataAnalyst()

    # Generate summary report
    analyst.generate_summary_report()

    # Compare device types (if data exists)
    if len(analyst.df) > 0:
        device_types = analyst.df['device_type'].unique().tolist()
        if device_types:
            analyst.plot_device_type_comparison(device_types)
            print(f"\nAnalyzed {len(device_types)} device types")
