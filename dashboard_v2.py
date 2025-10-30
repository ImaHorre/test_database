"""
Simple Terminal Dashboard for Microfluidic Device Analysis
No fancy UI - just clean, line-by-line terminal output
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import sys
import re

from src import DataAnalyst


class SimpleDashboard:
    """Simple terminal-based dashboard with command parsing."""

    def __init__(self):
        """Initialize dashboard and load data."""
        print("Loading database...")
        self.analyst = DataAnalyst()
        self.df = self.analyst.df
        print(f"[OK] Loaded {len(self.df)} measurements\n")

        # Plot editing state
        self.plot_editor = None
        self.in_plot_editing_mode = False

    def show_startup_info(self):
        """Display at-a-glance info on startup."""
        df = self.df

        # Calculate statistics
        total_records = len(df)
        device_types = df['device_type'].value_counts().to_dict()
        unique_devices = df['device_id'].nunique()

        # Handle date range
        date_col = pd.to_datetime(df['testing_date'], errors='coerce')
        date_col_clean = date_col.dropna()
        if len(date_col_clean) > 0:
            date_range = f"{date_col_clean.min().strftime('%Y-%m-%d')} to {date_col_clean.max().strftime('%Y-%m-%d')}"
        else:
            date_range = "N/A"

        # Count measurement types
        csv_files = len(df[df['file_type'] == 'csv'])
        txt_files = len(df[df['file_type'] == 'txt'])

        # Display
        print("=" * 70)
        print("MICROFLUIDIC DEVICE ANALYSIS DASHBOARD")
        print("=" * 70)
        print()
        print(f"Total Records:     {total_records}")
        print(f"Unique Devices:    {unique_devices}")
        print()
        print("Device Types:")
        for dtype, count in device_types.items():
            print(f"  • {dtype}: {count} measurements")
        print()
        print("Measurement Files:")
        print(f"  • CSV (droplet data):    {csv_files}")
        print(f"  • TXT (frequency data):  {txt_files}")
        print()
        print(f"Date Range:        {date_range}")
        print()
        print(f"Last updated:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

    def show_menu(self):
        """Display quick action menu."""
        print("QUICK ACTIONS:")
        print("  [1] Compare Devices at Same Parameters")
        print("  [2] Analyze Flow Parameter Effects")
        print("  [3] Track Device Over Time")
        print("  [4] Compare DFU Row Performance")
        print("  [5] Compare Fluid Types")
        print("  [6] View All Available Devices")
        print()
        print("  [R] Refresh Database")
        print("  [H] Help - Show all commands")
        print("  [Q] Quit")
        print()
        print("Or type a command/query (e.g., 'show w13 at 5mlhr 200mbar')")
        print("-" * 70)

    def show_help(self):
        """Display help and command reference."""
        print()
        print("=" * 70)
        print("COMMAND REFERENCE")
        print("=" * 70)
        print()
        print("QUICK COMMANDS:")
        print("  show [device_type]                 - Show all records for device type")
        print("    Example: show w13")
        print()
        print("  show [device_type] at [params]     - Filter by flow parameters")
        print("    Example: show w13 at 5mlhr 200mbar")
        print("    Example: show w14 at 5mlhr")
        print()
        print("  show params for [device_type]      - Show all parameter combinations")
        print("    Example: show params for w13")
        print()
        print("  list devices                       - List all devices")
        print("  list types                         - List all device types")
        print("  list params                        - List all flow parameters")
        print()
        print("  count [device_type]                - Count records")
        print("    Example: count w13")
        print()
        print("  stats [device_type]                - Show statistics")
        print("    Example: stats w13")
        print()
        print("NATURAL LANGUAGE:")
        print("  You can also use natural language queries:")
        print("    - Compare W13 and W14 devices")
        print("    - Track W13_S1_R1 over time")
        print("    - Analyze flowrate effects for W13")
        print()
        print("NUMBERED ACTIONS:")
        print("  Type 1-6 to run quick actions from the menu")
        print()
        print("=" * 70)
        print()

    def parse_command(self, cmd: str) -> Optional[Dict]:
        """
        Parse simple command syntax.

        Returns parsed command dict or None if not recognized.
        """
        cmd = cmd.strip().lower()

        # Pattern: show w13 at 5mlhr 200mbar
        match = re.match(r'show\s+(w1[34]|all)\s+at\s+(\d+)\s*mlhr\s+(\d+)\s*mbar', cmd)
        if match:
            return {
                'type': 'filter',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None,
                'flowrate': int(match.group(2)),
                'pressure': int(match.group(3))
            }

        # Pattern: show w13 at 5mlhr
        match = re.match(r'show\s+(w1[34]|all)\s+at\s+(\d+)\s*mlhr', cmd)
        if match:
            return {
                'type': 'filter',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None,
                'flowrate': int(match.group(2)),
                'pressure': None
            }

        # Pattern: show w13 at 200mbar
        match = re.match(r'show\s+(w1[34]|all)\s+at\s+(\d+)\s*mbar', cmd)
        if match:
            return {
                'type': 'filter',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None,
                'flowrate': None,
                'pressure': int(match.group(2))
            }

        # Pattern: show w13
        match = re.match(r'show\s+(w1[34])', cmd)
        if match:
            return {
                'type': 'show',
                'device_type': match.group(1).upper()
            }

        # Pattern: show params for w13
        match = re.match(r'show\s+params\s+for\s+(w1[34])', cmd)
        if match:
            return {
                'type': 'show_params',
                'device_type': match.group(1).upper()
            }

        # Pattern: show all flow parameter combinations
        match = re.match(r'show\s+all\s+(?:flow\s+)?param(?:eter)?\s+combinations?(?:\s+for\s+(w1[34]))?', cmd)
        if match:
            return {
                'type': 'show_params',
                'device_type': match.group(1).upper() if match.group(1) else None
            }

        # Pattern: list devices/types/params
        match = re.match(r'list\s+(devices|types|params)', cmd)
        if match:
            return {
                'type': 'list',
                'what': match.group(1)
            }

        # Pattern: count w13
        match = re.match(r'count\s+(w1[34]|all)', cmd)
        if match:
            return {
                'type': 'count',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None
            }

        # Pattern: stats w13
        match = re.match(r'stats\s+(w1[34])', cmd)
        if match:
            return {
                'type': 'stats',
                'device_type': match.group(1).upper()
            }

        return None

    def execute_command(self, parsed: Dict):
        """Execute a parsed command."""
        cmd_type = parsed['type']

        if cmd_type == 'show':
            self._cmd_show(parsed)
        elif cmd_type == 'filter':
            self._cmd_filter(parsed)
        elif cmd_type == 'show_params':
            self._cmd_show_params(parsed)
        elif cmd_type == 'list':
            self._cmd_list(parsed)
        elif cmd_type == 'count':
            self._cmd_count(parsed)
        elif cmd_type == 'stats':
            self._cmd_stats(parsed)

    def _cmd_show(self, parsed: Dict):
        """Show all records for a device type."""
        device_type = parsed['device_type']
        filtered = self.df[self.df['device_type'] == device_type]

        print()
        print(f"Records for {device_type}:")
        print(f"Total: {len(filtered)} measurements")
        print()

        # Show unique devices
        devices = filtered['device_id'].unique()
        print(f"Devices ({len(devices)}):")
        for device in sorted(devices):
            count = len(filtered[filtered['device_id'] == device])
            print(f"  • {device}: {count} measurements")
        print()

    def _cmd_filter(self, parsed: Dict):
        """Filter records by device type and/or flow parameters."""
        device_type = parsed.get('device_type')
        flowrate = parsed.get('flowrate')
        pressure = parsed.get('pressure')

        filtered = self.df.copy()

        # Apply filters
        filter_desc = []
        if device_type:
            filtered = filtered[filtered['device_type'] == device_type]
            filter_desc.append(f"device_type={device_type}")
        if flowrate:
            filtered = filtered[filtered['aqueous_flowrate'] == flowrate]
            filter_desc.append(f"flowrate={flowrate}mlhr")
        if pressure:
            filtered = filtered[filtered['oil_pressure'] == pressure]
            filter_desc.append(f"pressure={pressure}mbar")

        print()
        print(f"Filter: {', '.join(filter_desc)}")
        print(f"Found: {len(filtered)} measurements")
        print()

        if len(filtered) == 0:
            print("No results found.")
            print()
            return

        # Show devices that match
        devices = filtered.groupby('device_id').agg({
            'testing_date': ['min', 'max'],
            'droplet_size_mean': 'count'
        })

        print("Matching Devices:")
        for idx, device_id in enumerate(devices.index, 1):
            count = devices.loc[device_id, ('droplet_size_mean', 'count')]
            date_min = devices.loc[device_id, ('testing_date', 'min')]
            date_max = devices.loc[device_id, ('testing_date', 'max')]
            print(f"  {idx}. {device_id}: {count} measurements ({date_min} to {date_max})")

        print()

        # Show summary statistics
        if 'droplet_size_mean' in filtered.columns:
            droplet_mean = filtered['droplet_size_mean'].mean()
            droplet_std = filtered['droplet_size_mean'].std()
            if pd.notna(droplet_mean):
                print(f"Droplet Size: {droplet_mean:.2f} ± {droplet_std:.2f} µm")

        if 'frequency_mean' in filtered.columns:
            freq_data = filtered['frequency_mean'].dropna()
            if len(freq_data) > 0:
                freq_mean = freq_data.mean()
                freq_std = freq_data.std()
                print(f"Frequency:    {freq_mean:.2f} ± {freq_std:.2f} Hz")

        print()

    def _cmd_show_params(self, parsed: Dict):
        """Show all flow parameter combinations."""
        device_type = parsed.get('device_type')

        filtered = self.df.copy()
        if device_type:
            filtered = filtered[filtered['device_type'] == device_type]

        print()
        if device_type:
            print(f"Flow Parameter Combinations for {device_type}:")
        else:
            print("All Flow Parameter Combinations:")
        print()

        # Group by flow parameters
        param_groups = filtered.groupby(['aqueous_flowrate', 'oil_pressure'])

        for idx, ((flowrate, pressure), group) in enumerate(param_groups, 1):
            measurements = len(group)
            unique_devices = group['device_id'].nunique()
            print(f"  {idx}. {flowrate}ml/hr + {pressure}mbar: {measurements} measurements, {unique_devices} devices")

        print()

    def _cmd_list(self, parsed: Dict):
        """List devices, types, or parameters."""
        what = parsed['what']

        print()

        if what == 'devices':
            devices = self.df.groupby('device_id').agg({
                'device_type': 'first',
                'testing_date': ['min', 'max'],
                'droplet_size_mean': 'count'
            })

            print(f"All Devices ({len(devices)}):")
            print()
            for idx, device_id in enumerate(sorted(devices.index), 1):
                dtype = devices.loc[device_id, ('device_type', 'first')]
                count = devices.loc[device_id, ('droplet_size_mean', 'count')]
                print(f"  {idx:2d}. {device_id} ({dtype}): {count} measurements")

        elif what == 'types':
            types = self.df['device_type'].value_counts()
            print("Device Types:")
            print()
            for dtype, count in types.items():
                print(f"  • {dtype}: {count} measurements")

        elif what == 'params':
            params = self.df.groupby(['aqueous_flowrate', 'oil_pressure']).size().reset_index(name='count')
            print("Flow Parameters:")
            print()
            for idx, row in params.iterrows():
                print(f"  • {row['aqueous_flowrate']}ml/hr + {row['oil_pressure']}mbar: {row['count']} measurements")

        print()

    def _cmd_count(self, parsed: Dict):
        """Count records."""
        device_type = parsed.get('device_type')

        if device_type:
            count = len(self.df[self.df['device_type'] == device_type])
            print()
            print(f"{device_type}: {count} measurements")
        else:
            count = len(self.df)
            print()
            print(f"Total: {count} measurements")
        print()

    def _cmd_stats(self, parsed: Dict):
        """Show statistics for a device type."""
        device_type = parsed['device_type']
        filtered = self.df[self.df['device_type'] == device_type]

        print()
        print(f"Statistics for {device_type}:")
        print("-" * 50)
        print(f"Total Measurements:    {len(filtered)}")
        print(f"Unique Devices:        {filtered['device_id'].nunique()}")
        print()

        # Droplet size stats
        droplet_data = filtered['droplet_size_mean'].dropna()
        if len(droplet_data) > 0:
            print("Droplet Size:")
            print(f"  Mean:    {droplet_data.mean():.2f} µm")
            print(f"  Std:     {droplet_data.std():.2f} µm")
            print(f"  Min:     {droplet_data.min():.2f} µm")
            print(f"  Max:     {droplet_data.max():.2f} µm")
            print()

        # Frequency stats
        freq_data = filtered['frequency_mean'].dropna()
        if len(freq_data) > 0:
            print("Frequency:")
            print(f"  Mean:    {freq_data.mean():.2f} Hz")
            print(f"  Std:     {freq_data.std():.2f} Hz")
            print(f"  Min:     {freq_data.min():.2f} Hz")
            print(f"  Max:     {freq_data.max():.2f} Hz")
            print()

        # Flow parameters tested
        params = filtered.groupby(['aqueous_flowrate', 'oil_pressure']).size()
        print(f"Flow Parameters Tested: {len(params)}")
        for (flowrate, pressure), count in params.items():
            print(f"  • {flowrate}ml/hr + {pressure}mbar: {count} measurements")

        print()

    def execute_natural_language(self, query: str):
        """Execute natural language query using existing analyst."""
        print()
        print("Processing query...")
        result = self.analyst.process_natural_language_query(query)

        print()
        status = result.get('status', 'unknown')
        message = result.get('message', '')

        # Display status
        if status == 'success':
            print("[Success]")
        elif status == 'clarification_needed':
            print("[Clarification Needed]")
        elif status == 'error':
            print("[Error]")

        print()
        print(message)
        print()

        # Show data preview if available
        data = result.get('result')
        if data is not None and isinstance(data, pd.DataFrame) and len(data) > 0:
            print("Data preview (first 10 rows):")
            print()
            print(data.head(10).to_string())
            if len(data) > 10:
                print(f"\n... {len(data)} total rows")
            print()

        # Check if live preview mode was activated
        if isinstance(result.get('result'), dict) and result['result'].get('live_preview'):
            self.enter_plot_editing_mode(result['result'])
            return

        # Show plot/report paths
        plot_path = result.get('plot_path')
        if plot_path:
            print(f"Plot saved: {plot_path}")
            print()

        report_path = result.get('report_path')
        if report_path:
            print(f"Report saved: {report_path}")
            print()

    def enter_plot_editing_mode(self, plot_result: dict):
        """Enter plot editing mode with live preview."""
        self.in_plot_editing_mode = True
        self.plot_editor = plot_result.get('editor')

        print("=" * 70)
        print("PLOT EDITING MODE ACTIVE")
        print("=" * 70)
        print()
        print("Plot window opened. Type 'help' for editing options.")
        print("Commands: help, save, discard, change colors, add test date, etc.")
        print()
        print("-" * 70)
        print()

    def exit_plot_editing_mode(self):
        """Exit plot editing mode."""
        self.in_plot_editing_mode = False
        self.plot_editor = None
        print()
        print("Plot editing completed.")
        print()
        print("-" * 70)
        print()

    def handle_plot_editing_command(self, command: str) -> bool:
        """
        Handle plot editing commands.

        Returns:
            True if should exit editing mode, False otherwise
        """
        if not self.plot_editor:
            print("Error: No active plot editor")
            return True

        # Check if plot window is still open
        if not self.plot_editor.is_plot_open():
            print("Plot window was closed.")
            return True

        # Process the command
        result = self.plot_editor.process_command(command)

        status = result.get('status', 'unknown')
        message = result.get('message', '')
        action = result.get('action', 'none')

        # Display result
        if status == 'success':
            if action == 'help':
                print(message)
            else:
                print(f"[OK] {message}")
        elif status == 'error':
            print(f"[Error] {message}")

        # Check if we should exit editing mode
        if action in ['save', 'discard']:
            if action == 'save':
                file_path = result.get('file_path', 'unknown')
                print(f"\nPlot saved to: {file_path}")
            return True

        print("Plot updated. Continue editing or type 'save' to finish.")
        print()

        return False

    def refresh(self):
        """Refresh database."""
        print()
        print("Refreshing database...")
        self.analyst.refresh_data()
        self.df = self.analyst.df
        print(f"[OK] Reloaded {len(self.df)} measurements")
        print()

    def run(self):
        """Main loop."""
        # Startup
        self.show_startup_info()
        self.show_menu()

        # Main loop
        while True:
            try:
                # Check if in plot editing mode
                if self.in_plot_editing_mode:
                    # Special prompt for plot editing
                    user_input = input("plot> ").strip()

                    if not user_input:
                        continue

                    # Handle plot editing commands
                    should_exit = self.handle_plot_editing_command(user_input)
                    if should_exit:
                        self.exit_plot_editing_mode()
                    continue

                # Normal mode
                # Get input
                user_input = input(">>> ").strip()

                if not user_input:
                    continue

                # Handle special commands
                cmd_lower = user_input.lower()

                if cmd_lower in ['q', 'quit', 'exit']:
                    print()
                    print("Goodbye!")
                    print()
                    break

                elif cmd_lower in ['h', 'help']:
                    self.show_help()
                    continue

                elif cmd_lower in ['r', 'refresh']:
                    self.refresh()
                    continue

                elif cmd_lower == 'm' or cmd_lower == 'menu':
                    self.show_menu()
                    continue

                # Handle numbered menu options
                elif user_input in ['1', '2', '3', '4', '5', '6']:
                    menu_actions = {
                        '1': "compare devices at 5mlhr 200mbar",
                        '2': "analyze flowrate effects for W13",
                        '3': "track W13_S1_R1 over time",
                        '4': "compare DFU row performance",
                        '5': "compare fluid types",
                        '6': "list devices"
                    }
                    query = menu_actions[user_input]
                    print(f"Executing: {query}")

                    # Try simple command first, then natural language
                    parsed = self.parse_command(query)
                    if parsed:
                        self.execute_command(parsed)
                    else:
                        self.execute_natural_language(query)
                    continue

                # Try simple command parser
                parsed = self.parse_command(user_input)
                if parsed:
                    self.execute_command(parsed)
                else:
                    # Fall back to natural language
                    self.execute_natural_language(user_input)

            except KeyboardInterrupt:
                print()
                print()
                if self.in_plot_editing_mode:
                    print("Interrupted. Type 'discard' to close plot or continue editing.")
                else:
                    print("Interrupted. Type 'q' to quit or continue entering commands.")
                print()

            except Exception as e:
                print()
                print(f"Error: {str(e)}")
                print()


def main():
    """Run the dashboard."""
    dashboard = SimpleDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
