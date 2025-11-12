"""
DFU (Device Functional Unit) Plotting Module

Handles plotting of metrics (droplet size, frequency) vs DFU row number
for microfluidic device analysis. Provides context-aware plotting that
automatically detects varying parameters and includes them in legends.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DFUPlotter:
    """
    Specialized plotter for DFU-based analysis.

    Creates multi-line plots showing how metrics change across DFU rows
    for different devices, with context-aware legends and titles.
    """

    def __init__(self, csv_manager=None):
        """
        Initialize DFU plotter.

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
            raise ValueError("No CSVManager provided to DFUPlotter")
        return self.manager.df

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
        # Filter data based on criteria
        result = self.df.copy()

        filter_desc = []
        if device_type:
            result = result[result['device_type'] == device_type]
            filter_desc.append(f"device_type={device_type}")

        if aqueous_flowrate is not None:
            result = result[result['aqueous_flowrate'] == aqueous_flowrate]
            filter_desc.append(f"flowrate={aqueous_flowrate}ml/hr")

        if oil_pressure is not None:
            result = result[result['oil_pressure'] == oil_pressure]
            filter_desc.append(f"pressure={oil_pressure}mbar")

        if len(result) == 0:
            raise ValueError(
                f"No devices found with specified criteria ({', '.join(filter_desc)})"
            )

        # Filter to rows with DFU data and the requested metric
        dfu_data = result[result['dfu_row'].notna() & result[metric].notna()].copy()

        if len(dfu_data) == 0:
            raise ValueError(
                f"No DFU data available for metric '{metric}' with criteria: {', '.join(filter_desc)}"
            )

        # Get unique devices
        unique_devices = dfu_data['device_id'].unique()
        logger.info(f"Found {len(unique_devices)} devices with DFU data")

        # =====================================================================
        # CONTEXT-AWARE PARAMETER DETECTION
        # =====================================================================
        # Detect which parameters vary across the filtered dataset
        varying_params = self._detect_varying_parameters(dfu_data, query_text)

        logger.info(f"Detected varying parameters: {varying_params}")

        # Create the plot
        fig, ax = plt.subplots(figsize=(14, 8))

        # Plot each device as a separate line
        for device_id in unique_devices:
            device_data = dfu_data[dfu_data['device_id'] == device_id]

            # Group by DFU row and calculate statistics
            dfu_stats = device_data.groupby('dfu_row')[metric].agg(['mean', 'std', 'min', 'max']).reset_index()

            # Generate context-aware label
            label = self._generate_context_label(device_id, device_data, varying_params)

            # Plot line with markers
            ax.plot(
                dfu_stats['dfu_row'],
                dfu_stats['mean'],
                marker='o',
                markersize=8,
                linewidth=2,
                label=label,
                alpha=0.8
            )

            # Add error bars (using std dev)
            ax.errorbar(
                dfu_stats['dfu_row'],
                dfu_stats['mean'],
                yerr=dfu_stats['std'],
                fmt='none',
                alpha=0.3,
                capsize=5
            )

        # Formatting
        ax.set_xlabel('DFU Row Number', fontsize=12, fontweight='bold')

        # Set appropriate y-axis label based on metric
        if metric == 'droplet_size_mean':
            ylabel = 'Droplet Size Mean (µm)'
        elif metric == 'frequency_mean':
            ylabel = 'Frequency Mean (Hz)'
        else:
            ylabel = metric.replace('_', ' ').title()

        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')

        # Create enhanced title with context
        title = self._generate_context_title(ylabel, filter_desc, varying_params, device_type)
        ax.set_title(title, fontsize=14, fontweight='bold')

        # Configure x-axis to show only integer DFU values
        dfu_rows = sorted(dfu_data['dfu_row'].unique())
        ax.set_xticks(dfu_rows)
        ax.set_xlim(min(dfu_rows) - 0.5, max(dfu_rows) + 0.5)

        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')

        # Add legend with appropriate title
        legend_title = 'Device ID' if not varying_params else 'Device ID (Conditions)'
        ax.legend(
            title=legend_title,
            loc='best',
            framealpha=0.9,
            fontsize=9
        )

        plt.tight_layout()

        # Handle live preview vs immediate save
        if live_preview:
            # Enable interactive mode
            plt.ion()
            plt.show(block=False)

            # Collect device-specific metadata for editor
            devices_with_dates = {}
            devices_with_bond_dates = {}
            for device_id in unique_devices:
                device_data = dfu_data[dfu_data['device_id'] == device_id]
                if 'testing_date' in device_data.columns:
                    test_date = device_data['testing_date'].mode()[0] if len(device_data['testing_date'].mode()) > 0 else device_data['testing_date'].iloc[0]
                    if pd.notna(test_date):
                        devices_with_dates[device_id] = test_date
                if 'bond_date' in device_data.columns:
                    bond_date = device_data['bond_date'].mode()[0] if len(device_data['bond_date'].mode()) > 0 else device_data['bond_date'].iloc[0]
                    if pd.notna(bond_date):
                        devices_with_bond_dates[device_id] = bond_date

            # Create plot editor
            try:
                from ..plot_editor import create_live_plot_editor

                plot_data = {
                    'devices_with_dates': devices_with_dates,
                    'devices_with_bond_dates': devices_with_bond_dates,
                    'dfu_data': dfu_data,
                }

                metadata_dict = {
                    'metric': metric,
                    'filters': filter_desc,
                    'num_devices': len(unique_devices),
                    'devices': list(unique_devices),
                    'dfu_rows_measured': sorted(dfu_rows),
                    'total_measurements': len(dfu_data),
                    'varying_parameters': varying_params,
                    'device_type': device_type,
                }

                editor = create_live_plot_editor(fig, ax, plot_data, metadata_dict)

                summary = {
                    'plot_path': None,  # No path yet - not saved
                    'metric': metric,
                    'filters': filter_desc,
                    'num_devices': len(unique_devices),
                    'devices': list(unique_devices),
                    'dfu_rows_measured': sorted(dfu_rows),
                    'total_measurements': len(dfu_data),
                    'varying_parameters': varying_params,
                    'live_preview': True,
                    'editor': editor,
                    'fig': fig,
                    'ax': ax,
                }

                logger.info(f"Live plot preview created: {len(unique_devices)} devices across {len(dfu_rows)} DFU rows")

            except ImportError:
                logger.warning("PlotEditor not available, falling back to static plot")
                live_preview = False
                # Fall through to static plot creation

        if not live_preview:
            # Save plot immediately
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, bbox_inches='tight')
            logger.info(f"DFU analysis plot saved: {output_path}")
            plt.close()

            summary = {
                'plot_path': output_path,
                'metric': metric,
                'filters': filter_desc,
                'num_devices': len(unique_devices),
                'devices': list(unique_devices),
                'dfu_rows_measured': sorted(dfu_rows),
                'total_measurements': len(dfu_data),
                'varying_parameters': varying_params,
                'live_preview': False,
            }

            logger.info(f"DFU analysis complete: {len(unique_devices)} devices across {len(dfu_rows)} DFU rows")

        return summary

    def _detect_varying_parameters(self, data: pd.DataFrame, query_text: Optional[str] = None) -> List[str]:
        """
        Detect which parameters vary in the filtered dataset.

        Args:
            data: Filtered DataFrame
            query_text: Original query text for detecting user preferences

        Returns:
            List of parameter names that vary (e.g., ['oil_pressure', 'aqueous_fluid'])
        """
        varying_params = []

        # Parameters to always check (core operational parameters)
        always_check = {
            'oil_pressure': 'pressure',
            'aqueous_flowrate': 'flowrate',
            'device_type': 'device_type',
            'aqueous_fluid': 'aqueous',
            'oil_fluid': 'oil'
        }

        # Parameters to check only if mentioned in query (metadata)
        query_dependent = {
            'testing_date': ['test date', 'date', 'when tested', 'testing'],
            'bond_date': ['bond', 'bonding', 'bonded'],
            'wafer': ['wafer'],
            'shim': ['shim']
        }

        # Check always-check parameters
        for param, short_name in always_check.items():
            if param in data.columns:
                unique_vals = data[param].dropna().unique()
                if len(unique_vals) > 1:
                    varying_params.append(param)
                    logger.debug(f"Parameter '{param}' varies: {len(unique_vals)} unique values")

        # Check query-dependent parameters if query provided
        if query_text:
            query_lower = query_text.lower()
            for param, keywords in query_dependent.items():
                if param in data.columns and any(kw in query_lower for kw in keywords):
                    unique_vals = data[param].dropna().unique()
                    if len(unique_vals) > 1:
                        varying_params.append(param)
                        logger.debug(f"Parameter '{param}' varies (query-requested): {len(unique_vals)} unique values")

        return varying_params

    def _generate_context_label(self, device_id: str, device_data: pd.DataFrame, varying_params: List[str]) -> str:
        """
        Generate context-aware label for legend entry.

        Args:
            device_id: Device ID (e.g., W13_S1_R1)
            device_data: Data for this specific device
            varying_params: List of parameters that vary in dataset

        Returns:
            Formatted label string (e.g., "W13_S1_R1 (200mbar, NaCas+SO)")
        """
        label_parts = [device_id]

        # Build context info from varying parameters
        context_info = []

        for param in varying_params:
            if param in device_data.columns:
                # Get the most common value for this device (should be consistent)
                value = device_data[param].mode()[0] if len(device_data[param].mode()) > 0 else device_data[param].iloc[0]

                if pd.notna(value):
                    # Format based on parameter type
                    if param == 'oil_pressure':
                        context_info.append(f"{int(value)}mbar")
                    elif param == 'aqueous_flowrate':
                        context_info.append(f"{int(value)}ml/hr")
                    elif param == 'aqueous_fluid' or param == 'oil_fluid':
                        # Combine fluids into single entry if both vary
                        if 'aqueous_fluid' in varying_params and 'oil_fluid' in varying_params:
                            if param == 'aqueous_fluid':
                                aq_fluid = value
                                oil_fluid = device_data['oil_fluid'].mode()[0] if len(device_data['oil_fluid'].mode()) > 0 else device_data['oil_fluid'].iloc[0]
                                if pd.notna(aq_fluid) and pd.notna(oil_fluid):
                                    context_info.append(f"{aq_fluid}+{oil_fluid}")
                        elif param == 'aqueous_fluid':
                            context_info.append(str(value))
                        elif param == 'oil_fluid' and 'aqueous_fluid' not in varying_params:
                            context_info.append(str(value))
                    elif param == 'testing_date':
                        # Format date nicely
                        date_str = pd.to_datetime(value, errors='coerce')
                        if pd.notna(date_str):
                            context_info.append(date_str.strftime('%Y-%m-%d'))
                        else:
                            context_info.append(str(value))
                    elif param == 'device_type':
                        # Usually won't vary if filtered, but include if it does
                        context_info.append(str(value))
                    else:
                        # Generic formatting for other parameters
                        context_info.append(f"{param}={value}")

        # Combine into final label
        if context_info:
            label = f"{device_id} ({', '.join(context_info)})"
        else:
            label = device_id

        return label

    def _generate_context_title(self, ylabel: str, filter_desc: List[str], varying_params: List[str], device_type: Optional[str]) -> str:
        """
        Generate context-aware plot title.

        Args:
            ylabel: Y-axis label (metric name)
            filter_desc: List of filter descriptions
            varying_params: List of varying parameters
            device_type: Device type if filtered

        Returns:
            Formatted title string
        """
        # Base title
        title_parts = [f'{ylabel} vs DFU Row']

        # Add device type and highlight variations
        if device_type:
            if varying_params:
                # Identify what varies
                varying_names = []
                if 'oil_pressure' in varying_params:
                    varying_names.append('Multiple Pressures')
                if 'aqueous_flowrate' in varying_params:
                    varying_names.append('Multiple Flowrates')
                if 'aqueous_fluid' in varying_params or 'oil_fluid' in varying_params:
                    varying_names.append('Multiple Fluids')
                if 'testing_date' in varying_params:
                    varying_names.append('Multiple Dates')

                if varying_names:
                    title_parts.append(f"for {device_type} devices ({', '.join(varying_names)})")
                else:
                    title_parts.append(f"for {device_type} devices")
            else:
                # Add specific conditions if available from filters
                conditions = []
                for desc in filter_desc:
                    if 'flowrate=' in desc:
                        conditions.append(desc.split('=')[1])
                    elif 'pressure=' in desc:
                        conditions.append(desc.split('=')[1])

                if conditions:
                    title_parts.append(f"for {device_type} devices ({', '.join(conditions)})")
                else:
                    title_parts.append(f"for {device_type} devices")

        return '\n'.join(title_parts)


def create_dfu_plotter(csv_manager=None):
    """
    Factory function to create a DFUPlotter instance.

    Args:
        csv_manager: CSVManager instance

    Returns:
        Configured DFUPlotter instance
    """
    return DFUPlotter(csv_manager)