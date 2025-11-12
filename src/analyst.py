"""
Data Analyst Agent

Processes queries, generates insights, and creates visualizations.
Provides interactive guidance and dynamic plotting capabilities.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
import logging
from pathlib import Path

from .csv_manager import CSVManager
from .query_processor import QueryProcessor, format_query_help
from .plotting import DFUPlotter, DeviceComparisonPlotter
from .query_handlers import QueryRouter

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

        # Initialize query processor for natural language queries
        self.query_processor = QueryProcessor()

        # Initialize query router for handling different intent types
        self.query_router = QueryRouter(self)

        # Initialize specialized plotters
        self.dfu_plotter = DFUPlotter(self.manager)
        self.device_plotter = DeviceComparisonPlotter(self.manager)

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

                # Get date range, handling potential NaN or mixed types
                date_col = pd.to_datetime(filtered['testing_date'], errors='coerce')
                date_col_clean = date_col.dropna()
                date_range_str = 'N/A'
                if len(date_col_clean) > 0:
                    date_range_str = f"{date_col_clean.min().strftime('%Y-%m-%d')} to {date_col_clean.max().strftime('%Y-%m-%d')}"

                comparison = {
                    'device_type': device_type,
                    'total_measurements': len(filtered),
                    'unique_devices': filtered['device_id'].nunique(),
                    'unique_tests': filtered.groupby([
                        'device_id', 'testing_date', 'aqueous_flowrate', 'oil_pressure'
                    ]).ngroups if len(filtered) > 0 else 0,
                    'date_range': date_range_str
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
    ) -> Dict:
        """
        Create bar plot comparing device types.

        Natural language: "Plot comparison of W13 and W14 devices" or
        "Create a chart comparing device types"

        Args:
            device_types: List of device types to compare
            output_path: Where to save the plot

        Returns:
            Dictionary with plot metadata and summary

        Raises:
            ValueError: If comparison fails or no valid data
            IOError: If plot cannot be saved
        """
        # Delegate to device comparison plotter
        return self.device_plotter.plot_device_type_comparison(device_types, output_path)

    def plot_flow_parameter_analysis(
        self,
        device_type: str,
        output_path: str = 'outputs/flow_parameter_analysis.png'
    ) -> Dict:
        """
        Analyze and plot flow parameter distribution for a device type.

        Natural language: "Plot flow parameters for W13 devices" or
        "Show me flowrate vs pressure distribution for W14"

        Args:
            device_type: Device type to analyze
            output_path: Where to save the plot

        Returns:
            Dictionary with plot metadata and flow parameter statistics

        Raises:
            ValueError: If no data for device type or plotting fails
            IOError: If plot cannot be saved
        """
        # Delegate to device comparison plotter
        return self.device_plotter.plot_flow_parameter_analysis(device_type, output_path)

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

    # ========================================================================
    # COMMON ANALYSIS METHODS - Phase 1
    # ========================================================================

    def compare_devices_at_same_parameters(
        self,
        device_type: Optional[str] = None,
        aqueous_flowrate: Optional[int] = None,
        oil_pressure: Optional[int] = None,
        output_path: str = 'outputs/device_comparison_same_params.png'
    ) -> pd.DataFrame:
        """
        Compare all devices tested at the same flow parameters.

        Use Case: "Show me all W13 devices tested at 5ml/hr and 200mbar"
        or "Compare all devices at 30ml/hr regardless of pressure"

        Args:
            device_type: Optional filter to specific device type (W13, W14)
            aqueous_flowrate: Aqueous flowrate in ml/hr
            oil_pressure: Oil pressure in mbar
            output_path: Where to save comparison plot

        Returns:
            DataFrame with comparison statistics

        Raises:
            ValueError: If no devices found at specified parameters
        """
        # Filter data
        result = self.df.copy()

        if device_type:
            result = result[result['device_type'] == device_type]

        if aqueous_flowrate is not None:
            result = result[result['aqueous_flowrate'] == aqueous_flowrate]

        if oil_pressure is not None:
            result = result[result['oil_pressure'] == oil_pressure]

        if len(result) == 0:
            raise ValueError(
                f"No devices found with specified parameters "
                f"(type={device_type}, flowrate={aqueous_flowrate}, pressure={oil_pressure})"
            )

        # Group by device and calculate statistics
        comparison = result.groupby('device_id').agg({
            'droplet_size_mean': ['mean', 'std', 'count'],
            'frequency_mean': ['mean', 'std', 'count'],
            'testing_date': ['min', 'max']
        }).round(3)

        comparison.columns = ['_'.join(col).strip() for col in comparison.columns.values]

        logger.info(f"Compared {len(comparison)} devices at specified parameters")

        # Create visualization
        self.device_plotter.plot_device_comparison_boxplot(result, output_path)

        return comparison

    def analyze_flow_parameter_effects(
        self,
        device_type: str,
        parameter: str = 'aqueous_flowrate',
        metric: str = 'droplet_size_mean',
        output_path: str = 'outputs/parameter_effects.png'
    ) -> Dict:
        """
        Analyze how flow parameters affect measurement metrics.

        Use Case: "How does aqueous flowrate affect droplet size in W13 devices?"
        or "What's the relationship between oil pressure and droplet frequency?"

        Args:
            device_type: Device type to analyze (W13, W14)
            parameter: 'aqueous_flowrate' or 'oil_pressure'
            metric: 'droplet_size_mean', 'frequency_mean', etc.
            output_path: Where to save analysis plot

        Returns:
            Dictionary with correlation statistics and summary

        Raises:
            ValueError: If invalid parameter or metric specified
        """
        valid_parameters = ['aqueous_flowrate', 'oil_pressure']
        valid_metrics = ['droplet_size_mean', 'droplet_size_std', 'frequency_mean']

        if parameter not in valid_parameters:
            raise ValueError(f"Parameter must be one of {valid_parameters}")

        if metric not in valid_metrics:
            raise ValueError(f"Metric must be one of {valid_metrics}")

        # Filter to device type
        data = self.filter_by_device_type(device_type)

        # Remove NaN values
        clean_data = data[[parameter, metric]].dropna()

        if len(clean_data) == 0:
            raise ValueError(f"No data available for {parameter} vs {metric}")

        # Calculate correlation
        correlation = clean_data[parameter].corr(clean_data[metric])

        # Group by parameter values and calculate statistics
        grouped = data.groupby(parameter)[metric].agg(['mean', 'std', 'count']).round(3)

        # Create visualization
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Scatter plot with trend line
        axes[0].scatter(clean_data[parameter], clean_data[metric], alpha=0.6)
        z = np.polyfit(clean_data[parameter], clean_data[metric], 1)
        p = np.poly1d(z)
        axes[0].plot(clean_data[parameter], p(clean_data[parameter]), "r--", alpha=0.8)
        axes[0].set_xlabel(parameter.replace('_', ' ').title(), fontweight='bold')
        axes[0].set_ylabel(metric.replace('_', ' ').title(), fontweight='bold')
        axes[0].set_title(f'{device_type}: {parameter} vs {metric}\nCorrelation: {correlation:.3f}',
                         fontweight='bold')
        axes[0].grid(True, alpha=0.3)

        # Box plot by parameter value
        data.boxplot(column=metric, by=parameter, ax=axes[1])
        axes[1].set_xlabel(parameter.replace('_', ' ').title(), fontweight='bold')
        axes[1].set_ylabel(metric.replace('_', ' ').title(), fontweight='bold')
        axes[1].set_title(f'{device_type}: {metric} Distribution', fontweight='bold')
        plt.suptitle('')  # Remove default title

        plt.tight_layout()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, bbox_inches='tight')
        logger.info(f"Parameter effect plot saved: {output_path}")
        plt.close()

        analysis = {
            'device_type': device_type,
            'parameter': parameter,
            'metric': metric,
            'correlation': round(correlation, 3),
            'grouped_stats': grouped,
            'total_measurements': len(clean_data),
            'plot_path': output_path
        }

        logger.info(f"Parameter effect analysis complete: correlation = {correlation:.3f}")

        return analysis

    def track_device_over_time(
        self,
        device_id: str,
        output_path: str = 'outputs/device_temporal_tracking.png'
    ) -> pd.DataFrame:
        """
        Track how a specific device performs across different test dates and conditions.

        Use Case: "Show me how W13_S1_R1 performed over time"
        or "Did W13_S1_R1 improve or degrade across test dates?"

        Args:
            device_id: Full device ID (e.g., 'W13_S1_R1')
            output_path: Where to save tracking plot

        Returns:
            DataFrame with temporal tracking data sorted by date

        Raises:
            ValueError: If device not found
        """
        history = self.get_device_history(device_id)

        if len(history) == 0:
            raise ValueError(f"No data found for device {device_id}")

        # Convert testing_date to datetime for proper sorting
        history['testing_date_dt'] = pd.to_datetime(history['testing_date'], errors='coerce')
        history_sorted = history.sort_values('testing_date_dt')

        # Create comprehensive temporal plot
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Plot 1: Droplet size over time
        for idx, row in history_sorted.iterrows():
            label = f"{row['aqueous_flowrate']}ml/hr, {row['oil_pressure']}mbar"
            axes[0, 0].scatter(row['testing_date_dt'], row['droplet_size_mean'],
                             s=100, alpha=0.7, label=label)

        axes[0, 0].set_xlabel('Test Date', fontweight='bold')
        axes[0, 0].set_ylabel('Droplet Size Mean (µm)', fontweight='bold')
        axes[0, 0].set_title(f'{device_id}: Droplet Size Over Time', fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].tick_params(axis='x', rotation=45)

        # Plot 2: Frequency over time
        freq_data = history_sorted.dropna(subset=['frequency_mean'])
        if len(freq_data) > 0:
            for idx, row in freq_data.iterrows():
                label = f"{row['aqueous_flowrate']}ml/hr, {row['oil_pressure']}mbar"
                axes[0, 1].scatter(row['testing_date_dt'], row['frequency_mean'],
                                 s=100, alpha=0.7, label=label)

            axes[0, 1].set_xlabel('Test Date', fontweight='bold')
            axes[0, 1].set_ylabel('Frequency Mean (Hz)', fontweight='bold')
            axes[0, 1].set_title(f'{device_id}: Frequency Over Time', fontweight='bold')
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis='x', rotation=45)

        # Plot 3: Flow parameters tested
        param_counts = history_sorted.groupby(['aqueous_flowrate', 'oil_pressure']).size()
        param_labels = [f"{fr}ml/hr\n{pr}mbar" for fr, pr in param_counts.index]
        axes[1, 0].bar(range(len(param_counts)), param_counts.values)
        axes[1, 0].set_xticks(range(len(param_counts)))
        axes[1, 0].set_xticklabels(param_labels, rotation=45, ha='right')
        axes[1, 0].set_ylabel('Number of Tests', fontweight='bold')
        axes[1, 0].set_title(f'{device_id}: Flow Parameters Tested', fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3, axis='y')

        # Plot 4: Summary statistics table
        axes[1, 1].axis('off')
        summary_text = f"""
        Device: {device_id}
        Device Type: {history['device_type'].iloc[0]}

        Total Tests: {len(history)}
        Date Range: {history_sorted['testing_date'].min()} to {history_sorted['testing_date'].max()}

        Droplet Size:
          Mean: {history['droplet_size_mean'].mean():.2f} µm
          Std: {history['droplet_size_mean'].std():.2f} µm
          Range: {history['droplet_size_mean'].min():.2f} - {history['droplet_size_mean'].max():.2f} µm

        Flow Conditions Tested: {len(param_counts)}
        """
        axes[1, 1].text(0.1, 0.5, summary_text, fontsize=12, family='monospace',
                       verticalalignment='center')

        plt.tight_layout()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, bbox_inches='tight')
        logger.info(f"Temporal tracking plot saved: {output_path}")
        plt.close()

        logger.info(f"Device {device_id} tracked across {len(history)} tests")

        return history_sorted

    def compare_dfu_row_performance(
        self,
        device_type: Optional[str] = None,
        metric: str = 'droplet_size_mean',
        output_path: str = 'outputs/dfu_row_comparison.png'
    ) -> pd.DataFrame:
        """
        Compare performance across different DFU rows.

        Use Case: "Which DFU rows perform best for W13 devices?"
        or "Is there variation between DFU rows?"

        Args:
            device_type: Optional filter to specific device type
            metric: Metric to compare ('droplet_size_mean', 'frequency_mean', etc.)
            output_path: Where to save comparison plot

        Returns:
            DataFrame with DFU row statistics

        Raises:
            ValueError: If no DFU data available
        """
        data = self.df.copy()

        if device_type:
            data = data[data['device_type'] == device_type]

        if len(data) == 0:
            raise ValueError(f"No data found for device type {device_type}")

        # Filter to rows with DFU data
        dfu_data = data.dropna(subset=['dfu_row', metric])

        if len(dfu_data) == 0:
            raise ValueError(f"No DFU row data available for metric {metric}")

        # Calculate statistics by DFU row
        dfu_stats = dfu_data.groupby('dfu_row')[metric].agg([
            'mean', 'std', 'min', 'max', 'count'
        ]).round(3)

        # Create visualization
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Box plot
        dfu_data.boxplot(column=metric, by='dfu_row', ax=axes[0])
        axes[0].set_xlabel('DFU Row', fontweight='bold')
        axes[0].set_ylabel(metric.replace('_', ' ').title(), fontweight='bold')
        title_suffix = f' ({device_type})' if device_type else ''
        axes[0].set_title(f'DFU Row Performance{title_suffix}', fontweight='bold')
        plt.suptitle('')

        # Bar plot of means with error bars
        dfu_rows = dfu_stats.index
        means = dfu_stats['mean']
        stds = dfu_stats['std']

        axes[1].bar(dfu_rows, means, yerr=stds, capsize=5, alpha=0.7)
        axes[1].set_xlabel('DFU Row', fontweight='bold')
        axes[1].set_ylabel(f'{metric.replace("_", " ").title()} (Mean ± Std)', fontweight='bold')
        axes[1].set_title(f'DFU Row Averages{title_suffix}', fontweight='bold')
        axes[1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, bbox_inches='tight')
        logger.info(f"DFU comparison plot saved: {output_path}")
        plt.close()

        logger.info(f"Compared {len(dfu_stats)} DFU rows")

        return dfu_stats

    def compare_fluid_types(
        self,
        device_type: Optional[str] = None,
        output_path: str = 'outputs/fluid_comparison.png'
    ) -> pd.DataFrame:
        """
        Compare device performance across different fluid combinations.

        Use Case: "Does SDS or NaCas perform better?"
        or "How do fluid types affect droplet formation?"

        Args:
            device_type: Optional filter to specific device type
            output_path: Where to save comparison plot

        Returns:
            DataFrame with fluid type statistics

        Raises:
            ValueError: If insufficient fluid data
        """
        data = self.df.copy()

        if device_type:
            data = data[data['device_type'] == device_type]

        # Create fluid combination column
        data['fluid_combo'] = data['aqueous_fluid'].fillna('Unknown') + '_' + data['oil_fluid'].fillna('Unknown')

        # Remove rows with unknown fluids
        fluid_data = data[data['fluid_combo'] != 'Unknown_Unknown']

        if len(fluid_data) == 0:
            raise ValueError("No fluid type data available")

        # Calculate statistics by fluid type
        fluid_stats = fluid_data.groupby('fluid_combo').agg({
            'droplet_size_mean': ['mean', 'std', 'count'],
            'frequency_mean': ['mean', 'std', 'count']
        }).round(3)

        fluid_stats.columns = ['_'.join(col).strip() for col in fluid_stats.columns.values]

        # Create visualization
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Droplet size comparison
        droplet_data = fluid_data.dropna(subset=['droplet_size_mean'])
        if len(droplet_data) > 0:
            droplet_data.boxplot(column='droplet_size_mean', by='fluid_combo', ax=axes[0])
            axes[0].set_xlabel('Fluid Combination', fontweight='bold')
            axes[0].set_ylabel('Droplet Size Mean (µm)', fontweight='bold')
            title_suffix = f' ({device_type})' if device_type else ''
            axes[0].set_title(f'Droplet Size by Fluid{title_suffix}', fontweight='bold')
            axes[0].tick_params(axis='x', rotation=45)
            plt.suptitle('')

        # Frequency comparison
        freq_data = fluid_data.dropna(subset=['frequency_mean'])
        if len(freq_data) > 0:
            freq_data.boxplot(column='frequency_mean', by='fluid_combo', ax=axes[1])
            axes[1].set_xlabel('Fluid Combination', fontweight='bold')
            axes[1].set_ylabel('Frequency Mean (Hz)', fontweight='bold')
            axes[1].set_title(f'Frequency by Fluid{title_suffix}', fontweight='bold')
            axes[1].tick_params(axis='x', rotation=45)
            plt.suptitle('')

        plt.tight_layout()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, bbox_inches='tight')
        logger.info(f"Fluid comparison plot saved: {output_path}")
        plt.close()

        logger.info(f"Compared {len(fluid_stats)} fluid combinations")

        return fluid_stats


    def plot_metric_vs_dfu(
        self,
        metric: str = 'droplet_size_mean',
        device_type: Optional[str] = None,
        aqueous_flowrate: Optional[int] = None,
        oil_pressure: Optional[int] = None,
        output_path: str = 'outputs/dfu_analysis.png',
        query_text: Optional[str] = None,
        live_preview: bool = False
    ) -> Dict:
        """
        Plot a metric across all DFU rows for each device matching the criteria.

        CONTEXT-AWARE PLOTTING: Automatically detects which parameters vary in the
        filtered dataset and includes them in the legend for clarity.

        Use Case: "Show me the droplet size across all measured DFUs for each W13 device
                   that was tested at 5mlhr200mbar"

        Creates a multi-line plot with:
        - X-axis: DFU row number (1-6)
        - Y-axis: Specified metric (droplet size or frequency)
        - Multiple lines: One per device that matches the criteria
        - Error bars: Standard deviation or min/max range for each DFU point
        - Legend: Device IDs + varying parameters (pressure, fluids, dates, etc.)

        Args:
            metric: 'droplet_size_mean' or 'frequency_mean'
            device_type: Optional filter to specific device type (W13, W14)
            aqueous_flowrate: Optional flowrate filter in ml/hr
            oil_pressure: Optional pressure filter in mbar
            output_path: Where to save the plot
            query_text: Original query text for detecting metadata preferences
            live_preview: If True, opens interactive plot editor

        Returns:
            Dictionary with plot metadata and summary statistics

        Raises:
            ValueError: If no devices found matching criteria or no DFU data
        """
        # Delegate to DFU plotter
        return self.dfu_plotter.plot_metric_vs_dfu(
            metric=metric,
            device_type=device_type,
            aqueous_flowrate=aqueous_flowrate,
            oil_pressure=oil_pressure,
            output_path=output_path,
            query_text=query_text,
            live_preview=live_preview
        )


    # ========================================================================
    # END COMMON ANALYSIS METHODS
    # ========================================================================

    def process_natural_language_query(self, query: str) -> Dict:
        """
        Process natural language queries and route to appropriate analysis methods.

        Natural language examples:
        - "Compare W13 and W14 devices"
        - "Show me flow parameters for W13 at 5 ml/hr"
        - "Track device W13_S1_R2 over time"
        - "Generate a summary report"
        - "Analyze flowrate effects for W13"

        Args:
            query: Natural language query string

        Returns:
            Dictionary containing:
            - 'status': 'success', 'clarification_needed', or 'error'
            - 'intent': Detected intent type
            - 'result': Analysis result (DataFrame, plot path, or text)
            - 'message': Human-readable message
            - 'clarification': Optional clarifying question
            - 'plot_path': Path to generated plot (if applicable)
        """
        from datetime import datetime

        logger.info(f"Processing natural language query: {query}")

        # Handle help queries
        if query.lower().strip() in ['help', '?', 'how', 'what can i ask']:
            return {
                'status': 'success',
                'intent': 'help',
                'message': format_query_help(),
                'result': None
            }

        # Process the query to get intent and entities
        intent = self.query_processor.process_query(query)

        # Check if clarification is needed
        # Using 0.85 threshold to reduce misinterpretations and ask for clarification more often
        clarification = self.query_processor.suggest_clarification(intent)
        if clarification and intent.confidence < 0.85:
            return {
                'status': 'clarification_needed',
                'intent': intent.intent_type,
                'message': clarification,
                'clarification': clarification,
                'result': None
            }

        # Route to appropriate handler using the query router
        try:
            return self.query_router.route(intent)

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                'status': 'error',
                'intent': intent.intent_type,
                'message': f"An error occurred: {str(e)}",
                'result': None
            }


# ========================================================================
# QUERY HANDLERS EXTRACTED TO DEDICATED MODULES
# ========================================================================
# All natural language query handlers have been moved to src/query_handlers/
# and are accessed through the QueryRouter instance (self.query_router)


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
