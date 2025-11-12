"""
Device Comparison Plotting Module

Handles plotting for device type comparisons and flow parameter analysis
for microfluidic device testing. Provides bar charts, scatter plots, and
box plots for comparing device performance.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DeviceComparisonPlotter:
    """
    Specialized plotter for device comparison analysis.

    Creates bar charts, scatter plots, and box plots for comparing
    device types and analyzing flow parameter distributions.
    """

    def __init__(self, csv_manager=None):
        """
        Initialize device comparison plotter.

        Args:
            csv_manager: CSVManager instance for data access
        """
        self.manager = csv_manager

        # Set up plotting style
        sns.set_style("whitegrid")
        plt.rcParams['figure.dpi'] = 300

    @property
    def df(self) -> pd.DataFrame:
        """Get current DataFrame from CSVManager."""
        if self.manager is None:
            raise ValueError("No CSVManager provided to DeviceComparisonPlotter")
        return self.manager.df

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
        try:
            # Get comparison data using the analysis method
            comparison = self._get_device_type_comparison(device_types)

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

            # Return summary
            summary = {
                'plot_path': output_path,
                'device_types': device_types,
                'total_measurements': int(comparison['total_measurements'].sum()),
                'total_unique_devices': int(comparison['unique_devices'].sum()),
                'comparison_data': comparison.to_dict('records')
            }

            return summary

        except Exception as e:
            plt.close('all')  # Clean up any open figures
            logger.error(f"Failed to create device comparison plot: {e}")
            raise

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
        try:
            data = self._filter_by_device_type(device_type)

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

            # Calculate statistics
            total_tests = flow_summary['count'].sum()
            unique_conditions = len(flow_summary)
            flowrate_range = (flow_summary['aqueous_flowrate'].min(), flow_summary['aqueous_flowrate'].max())
            pressure_range = (flow_summary['oil_pressure'].min(), flow_summary['oil_pressure'].max())

            summary = {
                'plot_path': output_path,
                'device_type': device_type,
                'total_tests': int(total_tests),
                'unique_conditions': unique_conditions,
                'flowrate_range': flowrate_range,
                'pressure_range': pressure_range,
                'flow_conditions': flow_summary.to_dict('records')
            }

            return summary

        except Exception as e:
            plt.close('all')  # Clean up any open figures
            logger.error(f"Failed to create flow parameter plot: {e}")
            raise

    def plot_device_comparison_boxplot(self, data: pd.DataFrame, output_path: str) -> Dict:
        """
        Create device comparison box plots for droplet size and frequency.

        Args:
            data: DataFrame with device data
            output_path: Where to save the plot

        Returns:
            Dictionary with plot metadata

        Raises:
            ValueError: If no data available for plotting
            IOError: If plot cannot be saved
        """
        if len(data) == 0:
            raise ValueError("No data provided for box plot comparison")

        try:
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))

            # Droplet size comparison
            droplet_data = data.dropna(subset=['droplet_size_mean'])
            if len(droplet_data) > 0:
                droplet_data.boxplot(column='droplet_size_mean', by='device_id', ax=axes[0])
                axes[0].set_xlabel('Device ID', fontweight='bold')
                axes[0].set_ylabel('Droplet Size Mean (µm)', fontweight='bold')
                axes[0].set_title('Droplet Size Comparison', fontweight='bold')
                axes[0].tick_params(axis='x', rotation=45)
                plt.suptitle('')

            # Frequency comparison
            freq_data = data.dropna(subset=['frequency_mean'])
            if len(freq_data) > 0:
                freq_data.boxplot(column='frequency_mean', by='device_id', ax=axes[1])
                axes[1].set_xlabel('Device ID', fontweight='bold')
                axes[1].set_ylabel('Frequency Mean (Hz)', fontweight='bold')
                axes[1].set_title('Frequency Comparison', fontweight='bold')
                axes[1].tick_params(axis='x', rotation=45)
                plt.suptitle('')

            plt.tight_layout()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, bbox_inches='tight')
            logger.info(f"Device comparison plot saved: {output_path}")
            plt.close()

            # Generate summary statistics
            unique_devices = data['device_id'].nunique()
            droplet_devices = droplet_data['device_id'].nunique() if len(droplet_data) > 0 else 0
            freq_devices = freq_data['device_id'].nunique() if len(freq_data) > 0 else 0

            summary = {
                'plot_path': output_path,
                'total_devices': unique_devices,
                'devices_with_droplet_data': droplet_devices,
                'devices_with_frequency_data': freq_devices,
                'total_measurements': len(data)
            }

            return summary

        except Exception as e:
            plt.close('all')  # Clean up any open figures
            logger.error(f"Failed to create device comparison box plot: {e}")
            raise

    def _filter_by_device_type(self, device_type: str) -> pd.DataFrame:
        """
        Filter data by device type (W13, W14, etc.).

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

    def _get_device_type_comparison(self, device_types: List[str]) -> pd.DataFrame:
        """
        Compare different device types side-by-side.

        Args:
            device_types: List of device types (e.g., ['W13', 'W14'])

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
                filtered = self._filter_by_device_type(device_type)

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
                logger.warning(f"Failed to analyze device type {device_type}: {e}")
                # Add empty entry for this device type
                results.append({
                    'device_type': device_type,
                    'total_measurements': 0,
                    'unique_devices': 0,
                    'unique_tests': 0,
                    'date_range': 'N/A'
                })

        comparison_df = pd.DataFrame(results)
        logger.info(f"Compared {len(device_types)} device types")
        return comparison_df


def create_device_comparison_plotter(csv_manager=None):
    """
    Factory function to create a DeviceComparisonPlotter instance.

    Args:
        csv_manager: CSVManager instance

    Returns:
        Configured DeviceComparisonPlotter instance
    """
    return DeviceComparisonPlotter(csv_manager)