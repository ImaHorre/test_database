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
from src.error_handler import ErrorMessageBuilder
from src.query_cache import CachedAnalysisMixin


class SimpleDashboard(CachedAnalysisMixin):
    """Simple terminal-based dashboard with command parsing and caching."""

    def __init__(self):
        """Initialize dashboard and load data."""
        print("Loading database...")
        self.analyst = DataAnalyst()
        self.df = self.analyst.df
        print(f"[OK] Loaded {len(self.df)} measurements\n")

        # Plot editing state
        self.plot_editor = None
        self.in_plot_editing_mode = False

        # Session state management
        self.session_state = {
            'last_query': None,
            'current_filters': {},
            'last_result': None,
            'last_filtered_df': None,
            'query_history': []
        }

        # Error message builder for context-aware errors
        self.error_builder = ErrorMessageBuilder(self.df)

        # Initialize caching mixin
        super().__init__()

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

    def _update_session_state(self, query: str, query_type: str, filters: Dict = None, result = None):
        """Update session state after successful command execution."""
        self.session_state['last_query'] = query
        self.session_state['last_result'] = result

        # Update current filters if this was a filter command
        if query_type == 'filter' and filters:
            self.session_state['current_filters'].update(filters)
        elif query_type == 'clear_filters':
            self.session_state['current_filters'] = {}

        # Add to history
        self.session_state['query_history'].append({
            'query': query,
            'type': query_type,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'filters': filters.copy() if filters else None
        })

        # Keep only last 50 queries in history
        if len(self.session_state['query_history']) > 50:
            self.session_state['query_history'] = self.session_state['query_history'][-50:]

    def _get_prompt(self) -> str:
        """Get current prompt showing active filters."""
        filters = self.session_state['current_filters']
        if not filters:
            return ">>> "

        # Build filter display
        filter_parts = []
        if 'device_type' in filters:
            filter_parts.append(filters['device_type'])
        if 'flowrate' in filters:
            filter_parts.append(f"{filters['flowrate']}mlhr")
        if 'pressure' in filters:
            filter_parts.append(f"{filters['pressure']}mbar")

        filter_str = "@".join(filter_parts)
        return f">>> [{filter_str}] "

    def _cmd_show_filters(self):
        """Show current active filters."""
        filters = self.session_state['current_filters']
        print()
        if not filters:
            print("No active filters.")
        else:
            print("Active filters:")
            for key, value in filters.items():
                print(f"  • {key}: {value}")
        print()

    def _cmd_clear_filters(self):
        """Clear all active filters."""
        self.session_state['current_filters'] = {}
        self._update_session_state("clear filters", "clear_filters")
        print()
        print("All filters cleared.")
        print()

    def _cmd_show_history(self):
        """Show recent query history."""
        history = self.session_state['query_history']
        print()
        if not history:
            print("No query history.")
        else:
            print("Recent queries:")
            # Show last 10 queries
            for i, entry in enumerate(history[-10:], 1):
                timestamp = entry['timestamp']
                query = entry['query']
                print(f"  {i:2d}. [{timestamp}] {query}")
        print()

    def _cmd_repeat_last(self):
        """Repeat the last query."""
        last_query = self.session_state['last_query']
        if not last_query:
            print()
            print("No previous query to repeat.")
            print()
            return

        print()
        print(f"Repeating: {last_query}")
        self._process_query(last_query)

    def _cmd_cache_stats(self):
        """Show cache statistics."""
        print()
        if hasattr(self, 'df_cache'):
            stats = self.get_cache_stats()
            print("Cache Statistics:")
            print(f"  • DataFrame cache entries: {stats['dataframe_cache']['valid_entries']}")
            print(f"  • Cache size limit: {stats['dataframe_cache']['max_size']}")
            print(f"  • TTL: {stats['dataframe_cache']['ttl_minutes']:.1f} minutes")
            print(f"  • Current data hash: {stats['current_data_hash'][:8]}...")
        else:
            print("Caching not available.")
        print()

    def _cmd_clear_cache(self):
        """Clear query cache."""
        print()
        if hasattr(self, 'df_cache'):
            self.df_cache.clear()
            print("Query cache cleared.")
        else:
            print("No cache to clear.")
        print()

    def _process_query(self, query: str):
        """Process a query (handles both simple commands and natural language)."""
        # Try simple command parser first
        parsed = self.parse_command(query)
        if parsed:
            self.execute_command(parsed)
        else:
            # Check if it looks like a command that failed to parse
            if self._looks_like_failed_command(query):
                # Provide helpful error message for unrecognized commands
                error_msg = self.error_builder.get_command_not_found_error(query)
                print()
                print(f"[ERROR] {error_msg}")
                print()
            else:
                # Fall back to natural language
                self.execute_natural_language(query)

    def _looks_like_failed_command(self, query: str) -> bool:
        """Check if query looks like a command that failed to parse."""
        query_lower = query.lower().strip()

        # Check for command-like patterns
        command_indicators = [
            query_lower.startswith(('show ', 'list ', 'stats ', 'count ')),
            query_lower.startswith(('filter ', 'find ', 'search ')),
            ' at ' in query_lower and any(word in query_lower for word in ['mlhr', 'mbar']),
            query_lower in ['show', 'list', 'stats', 'count', 'filter']  # incomplete commands
        ]

        return any(command_indicators)

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
        print("SESSION COMMANDS:")
        print("  show filters, clear filters, history, repeat last")
        print("  cache stats, clear cache (performance monitoring)")
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
        print("  stats [device_type] at [params]    - Show filtered statistics")
        print("    Example: stats w13 at 5mlhr 200mbar")
        print()
        print("SESSION MANAGEMENT:")
        print("  show filters                       - Display active filters")
        print("  clear filters                      - Clear all active filters")
        print("  history                            - Show recent query history")
        print("  repeat last                        - Repeat the last query")
        print()
        print("PERFORMANCE:")
        print("  cache stats                        - Show query cache statistics")
        print("  clear cache                        - Clear query cache (debug)")
        print()
        print("  NOTE: Filter commands set active filters shown in prompt")
        print("  Example: 'show w13 at 5mlhr' sets [W13@5mlhr] filters")
        print()
        print("NATURAL LANGUAGE:")
        print("  You can also use natural language queries:")
        print("    - Compare W13 and W14 devices")
        print("    - Track W13_S1_R1 over time")
        print("    - Analyze flowrate effects for W13")
        print()
        print("PLOT COMMANDS:")
        print("  All plot commands now show preview and ask for confirmation")
        print("  Add --preview flag for dry-run mode (no plot generation)")
        print("    Example: plot W13 droplet sizes --preview")
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

        # Pattern: stats w13 at 5mlhr 200mbar
        match = re.match(r'stats\s+(w1[34]|all)\s+at\s+(\d+)\s*mlhr\s+(\d+)\s*mbar', cmd)
        if match:
            return {
                'type': 'stats',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None,
                'flowrate': int(match.group(2)),
                'pressure': int(match.group(3))
            }

        # Pattern: stats w13 at 5mlhr
        match = re.match(r'stats\s+(w1[34]|all)\s+at\s+(\d+)\s*mlhr', cmd)
        if match:
            return {
                'type': 'stats',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None,
                'flowrate': int(match.group(2)),
                'pressure': None
            }

        # Pattern: stats w13 at 200mbar
        match = re.match(r'stats\s+(w1[34]|all)\s+at\s+(\d+)\s*mbar', cmd)
        if match:
            return {
                'type': 'stats',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None,
                'flowrate': None,
                'pressure': int(match.group(2))
            }

        # Pattern: stats w13 (original pattern)
        match = re.match(r'stats\s+(w1[34])', cmd)
        if match:
            return {
                'type': 'stats',
                'device_type': match.group(1).upper()
            }

        # Session management commands
        if cmd == 'show filters':
            return {'type': 'show_filters'}

        if cmd == 'clear filters':
            return {'type': 'clear_filters'}

        if cmd == 'history':
            return {'type': 'show_history'}

        if cmd in ['repeat last', 'repeat']:
            return {'type': 'repeat_last'}

        # Cache management commands (for debugging)
        if cmd == 'cache stats':
            return {'type': 'cache_stats'}

        if cmd == 'clear cache':
            return {'type': 'clear_cache'}

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
        elif cmd_type == 'show_filters':
            self._cmd_show_filters()
        elif cmd_type == 'clear_filters':
            self._cmd_clear_filters()
        elif cmd_type == 'show_history':
            self._cmd_show_history()
        elif cmd_type == 'repeat_last':
            self._cmd_repeat_last()
        elif cmd_type == 'cache_stats':
            self._cmd_cache_stats()
        elif cmd_type == 'clear_cache':
            self._cmd_clear_cache()

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

        # Update session state
        query_str = f"show {device_type}"
        self._update_session_state(query_str, "show", {'device_type': device_type}, filtered)

        print()

    def _cmd_filter(self, parsed: Dict):
        """Filter records by device type and/or flow parameters."""
        device_type = parsed.get('device_type')
        flowrate = parsed.get('flowrate')
        pressure = parsed.get('pressure')

        # Validate inputs before filtering
        validation_errors = []

        if device_type and device_type not in self.error_builder.valid_device_types:
            validation_errors.append(('device_type', device_type))

        if flowrate and flowrate not in self.error_builder.valid_flowrates:
            validation_errors.append(('flowrate', flowrate))

        if pressure and pressure not in self.error_builder.valid_pressures:
            validation_errors.append(('pressure', pressure))

        # Show validation errors with helpful suggestions
        if validation_errors:
            print()
            for error_type, value in validation_errors:
                if error_type == 'device_type':
                    error_msg = self.error_builder.get_device_type_error(value)
                elif error_type == 'flowrate':
                    error_msg = self.error_builder.get_flowrate_error(value, device_type)
                elif error_type == 'pressure':
                    error_msg = self.error_builder.get_pressure_error(value, device_type)

                print(f"[ERROR] {error_msg}")
                print()
            return

        # Use cached filtering for better performance
        filtered = self.cached_filter(device_type, flowrate, pressure)

        # Build filters dict for session state
        current_filters = {}

        # Build filter description
        filter_desc = []
        if device_type:
            filter_desc.append(f"device_type={device_type}")
            current_filters['device_type'] = device_type
        if flowrate:
            filter_desc.append(f"flowrate={flowrate}mlhr")
            current_filters['flowrate'] = flowrate
        if pressure:
            filter_desc.append(f"pressure={pressure}mbar")
            current_filters['pressure'] = pressure

        print()
        print(f"Filter: {', '.join(filter_desc)}")

        if len(filtered) == 0:
            # Use context-aware error message for no data found
            filters_dict = {k: v for k, v in [
                ('device_type', device_type),
                ('flowrate', flowrate),
                ('pressure', pressure)
            ] if v is not None}

            error_msg = self.error_builder.get_no_data_error(filters_dict)
            print(f"[ERROR] {error_msg}")
            print()
            return

        # Count complete analyses instead of raw measurements (with caching)
        analysis_counts = self.cached_analysis_counts(filtered)

        # Display meaningful counts
        count_parts = []
        if analysis_counts['complete_droplet'] > 0:
            count_parts.append(f"{analysis_counts['complete_droplet']} complete droplet analysis" + ("es" if analysis_counts['complete_droplet'] > 1 else ""))
        if analysis_counts['complete_freq'] > 0:
            count_parts.append(f"{analysis_counts['complete_freq']} complete frequency analysis" + ("es" if analysis_counts['complete_freq'] > 1 else ""))
        if analysis_counts['partial'] > 0:
            count_parts.append(f"{analysis_counts['partial']} partial analysis" + ("es" if analysis_counts['partial'] > 1 else ""))

        if count_parts:
            print(f"Found: {', '.join(count_parts)}")
        else:
            print("Found: No complete analyses")
        print()

        # Show detailed breakdown by device with full experimental context
        devices_shown = set()
        print("Matching Devices:")
        for idx, detail in enumerate(analysis_counts['details'], 1):
            device_id = detail['condition'].split(' at ')[0]
            if device_id not in devices_shown:
                devices_shown.add(device_id)
                device_details = [d for d in analysis_counts['details'] if d['condition'].startswith(device_id)]

                # Build comprehensive condition summary for this device
                conditions = []
                for d in device_details:
                    condition_part = d['condition'].split(' at ', 1)[1]
                    conditions.append(condition_part)

                print(f"  {idx}. {device_id}: {', '.join(conditions)}")

                # Show status for each condition
                for d in device_details:
                    condition_part = d['condition'].split(' at ', 1)[1]
                    print(f"     • {condition_part}: {d['status']}")

        print()

        # Show flow parameter combinations tested summary
        print("Flow Parameter Combinations in Results:")
        param_groups = filtered.groupby(['aqueous_flowrate', 'oil_pressure', 'aqueous_fluid', 'oil_fluid'])
        for idx, ((flowrate, pressure, aq_fluid, oil_fluid), group) in enumerate(param_groups, 1):
            device_count = group['device_id'].nunique()

            # Build fluid info string
            fluid_info = ""
            if pd.notna(aq_fluid) and pd.notna(oil_fluid):
                fluid_info = f" ({aq_fluid}_{oil_fluid})"
            elif pd.notna(aq_fluid):
                fluid_info = f" ({aq_fluid})"

            print(f"  {idx}. {flowrate}ml/hr + {pressure}mbar{fluid_info}: {device_count} devices")

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

        # Update session state
        query_str = f"show {' '.join(filter_desc)}"
        self._update_session_state(query_str, "filter", current_filters, filtered)
        self.session_state['last_filtered_df'] = filtered

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

        # Group by flow parameters and count complete analyses
        param_groups = filtered.groupby(['aqueous_flowrate', 'oil_pressure'])

        for idx, ((flowrate, pressure), group) in enumerate(param_groups, 1):
            analysis_counts = self._count_complete_analyses(group)
            unique_devices = group['device_id'].nunique()

            # Build analysis summary
            analysis_parts = []
            if analysis_counts['complete_droplet'] > 0:
                analysis_parts.append(f"{analysis_counts['complete_droplet']} complete droplet")
            if analysis_counts['complete_freq'] > 0:
                analysis_parts.append(f"{analysis_counts['complete_freq']} complete frequency")
            if analysis_counts['partial'] > 0:
                analysis_parts.append(f"{analysis_counts['partial']} partial")

            analysis_summary = ", ".join(analysis_parts) if analysis_parts else "no complete analyses"

            print(f"  {idx}. {flowrate}ml/hr + {pressure}mbar: {analysis_summary}, {unique_devices} devices")

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
        """Show statistics with optional filtering by flow parameters."""
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
        if filter_desc:
            print(f"Statistics for {', '.join(filter_desc)}:")
        else:
            print("Statistics for all data:")
        print("-" * 50)

        if len(filtered) == 0:
            print("No data found matching criteria.")
            print()
            return

        # Count complete analyses
        analysis_counts = self._count_complete_analyses(filtered)

        # Display analysis counts
        print("Analysis Summary:")
        if analysis_counts['complete_droplet'] > 0:
            print(f"  Complete Droplet Analyses:    {analysis_counts['complete_droplet']}")
        if analysis_counts['complete_freq'] > 0:
            print(f"  Complete Frequency Analyses:  {analysis_counts['complete_freq']}")
        if analysis_counts['partial'] > 0:
            print(f"  Partial Analyses:             {analysis_counts['partial']}")
        print(f"  Total Raw Measurements:       {len(filtered)}")
        print(f"  Unique Devices:               {filtered['device_id'].nunique()}")
        print()

        # Device-level breakdown
        if analysis_counts['details']:
            devices_shown = set()
            print("Device Breakdown:")
            for detail in analysis_counts['details']:
                device_id = detail['condition'].split(' at ')[0]
                if device_id not in devices_shown:
                    devices_shown.add(device_id)
                    device_details = [d for d in analysis_counts['details'] if d['condition'].startswith(device_id)]
                    print(f"  {device_id}:")
                    for d in device_details:
                        condition_part = d['condition'].split(' at ', 1)[1]  # Get everything after device_id
                        print(f"    • {condition_part}: {d['status']}")
            print()

        # Droplet size stats
        droplet_data = filtered['droplet_size_mean'].dropna()
        if len(droplet_data) > 0:
            print("Droplet Size Statistics:")
            print(f"  Mean:    {droplet_data.mean():.2f} µm")
            print(f"  Std:     {droplet_data.std():.2f} µm")
            print(f"  Min:     {droplet_data.min():.2f} µm")
            print(f"  Max:     {droplet_data.max():.2f} µm")
            print()

        # Frequency stats
        freq_data = filtered['frequency_mean'].dropna()
        if len(freq_data) > 0:
            print("Frequency Statistics:")
            print(f"  Mean:    {freq_data.mean():.2f} Hz")
            print(f"  Std:     {freq_data.std():.2f} Hz")
            print(f"  Min:     {freq_data.min():.2f} Hz")
            print(f"  Max:     {freq_data.max():.2f} Hz")
            print()

        # Flow parameters tested (only if not already filtered by specific parameters)
        if not flowrate and not pressure:
            params = filtered.groupby(['aqueous_flowrate', 'oil_pressure']).size()
            print(f"Flow Parameters Tested: {len(params)}")
            for (flow, press), count in params.items():
                print(f"  • {flow}ml/hr + {press}mbar: {count} raw measurements")
            print()

        print()

    def execute_natural_language(self, query: str):
        """Execute natural language query using existing analyst."""
        print()
        print("Processing query...")

        # Check if query might be a plot command and we have active filters
        if any(word in query.lower() for word in ['plot', 'graph', 'chart']) and self.session_state['current_filters']:
            print(f"Using active filters: {self.session_state['current_filters']}")

        # Check if this is a plot command and provide preview/confirmation
        if self._is_plot_command(query):
            # Check for --preview flag (dry-run mode)
            if '--preview' in query:
                self._show_plot_preview_only(query)
                return

            if not self._confirm_plot_generation(query):
                print("Plot generation cancelled.")
                print()
                return

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

        # Update session state for natural language queries
        self._update_session_state(query, "natural_language", result=data)

    def _is_plot_command(self, query: str) -> bool:
        """Check if a query is requesting plot generation."""
        plot_keywords = ['plot', 'graph', 'chart', 'visualize', 'show plot', 'create plot']
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in plot_keywords)

    def _confirm_plot_generation(self, query: str) -> bool:
        """
        Show data preview and ask for user confirmation before plot generation.

        Returns:
            True if user confirms, False if cancelled
        """
        print()
        print("=" * 60)
        print("PLOT GENERATION PREVIEW")
        print("=" * 60)

        # Try to extract entities from the query to understand what will be plotted
        entities = self._extract_plot_entities(query)

        # Get filtered data based on entities and current session filters
        preview_data = self._get_plot_preview_data(entities)

        if preview_data is None or len(preview_data) == 0:
            print("No data found for plotting with current criteria.")
            print("Please check your filters and query.")
            print()
            response = input("Continue anyway? (y/n): ").strip().lower()
            return response in ['y', 'yes']

        # Show data preview
        print(f"Query: {query}")
        print()

        analysis_counts = self._count_complete_analyses(preview_data)

        print("Data to be plotted:")
        print(f"  • {len(preview_data)} total measurements")
        print(f"  • {preview_data['device_id'].nunique()} unique devices")

        if analysis_counts['complete_droplet'] > 0:
            print(f"  • {analysis_counts['complete_droplet']} complete droplet analyses")
        if analysis_counts['complete_freq'] > 0:
            print(f"  • {analysis_counts['complete_freq']} complete frequency analyses")

        print()

        # Show device breakdown
        devices = preview_data['device_id'].unique()
        if len(devices) > 0:
            print("Devices to be included:")
            for device in sorted(devices)[:5]:  # Show first 5 devices
                device_data = preview_data[preview_data['device_id'] == device]
                conditions = []
                for _, group in device_data.groupby(['aqueous_flowrate', 'oil_pressure']):
                    flowrate = group['aqueous_flowrate'].iloc[0]
                    pressure = group['oil_pressure'].iloc[0]
                    conditions.append(f"{flowrate}ml/hr+{pressure}mbar")
                conditions_str = ", ".join(set(conditions))
                print(f"  • {device}: {conditions_str}")

            if len(devices) > 5:
                print(f"  ... and {len(devices) - 5} more devices")

        print()

        # Check for potential issues
        issues = self._check_plot_feasibility(preview_data, entities)
        if issues:
            print("⚠️  Potential issues:")
            for issue in issues:
                print(f"  • {issue}")
            print()

        print("=" * 60)
        print()

        # Ask for confirmation
        response = input("Generate plot? (y/n): ").strip().lower()
        return response in ['y', 'yes']

    def _extract_plot_entities(self, query: str) -> Dict:
        """Extract plotting entities from query (simple extraction)."""
        entities = {}
        query_lower = query.lower()

        # Device type
        if 'w13' in query_lower:
            entities['device_type'] = 'W13'
        elif 'w14' in query_lower:
            entities['device_type'] = 'W14'

        # Flow rate (simple regex)
        import re
        flowrate_match = re.search(r'(\d+)\s*ml', query_lower)
        if flowrate_match:
            entities['flowrate'] = int(flowrate_match.group(1))

        # Pressure
        pressure_match = re.search(r'(\d+)\s*mbar', query_lower)
        if pressure_match:
            entities['pressure'] = int(pressure_match.group(1))

        return entities

    def _show_plot_preview_only(self, query: str):
        """Show plot preview without generating plot (dry-run mode)."""
        # Remove --preview flag from query for entity extraction
        clean_query = query.replace('--preview', '').strip()

        print()
        print("=" * 60)
        print("PLOT PREVIEW (DRY-RUN MODE)")
        print("=" * 60)

        entities = self._extract_plot_entities(clean_query)
        preview_data = self._get_plot_preview_data(entities)

        if preview_data is None or len(preview_data) == 0:
            print("No data found for plotting with current criteria.")
            print("Please adjust your filters or query.")
            print()
            return

        print(f"Query: {clean_query}")
        print()

        analysis_counts = self._count_complete_analyses(preview_data)

        print("Data that would be plotted:")
        print(f"  • {len(preview_data)} total measurements")
        print(f"  • {preview_data['device_id'].nunique()} unique devices")

        if analysis_counts['complete_droplet'] > 0:
            print(f"  • {analysis_counts['complete_droplet']} complete droplet analyses")
        if analysis_counts['complete_freq'] > 0:
            print(f"  • {analysis_counts['complete_freq']} complete frequency analyses")

        print()

        # Show device breakdown
        devices = preview_data['device_id'].unique()
        if len(devices) > 0:
            print("Devices that would be included:")
            for device in sorted(devices):
                device_data = preview_data[preview_data['device_id'] == device]
                conditions = []
                for _, group in device_data.groupby(['aqueous_flowrate', 'oil_pressure']):
                    flowrate = group['aqueous_flowrate'].iloc[0]
                    pressure = group['oil_pressure'].iloc[0]
                    conditions.append(f"{flowrate}ml/hr+{pressure}mbar")
                conditions_str = ", ".join(set(conditions))
                print(f"  • {device}: {conditions_str}")

        print()

        # Check for potential issues
        issues = self._check_plot_feasibility(preview_data, entities)
        if issues:
            print("⚠️  Potential issues:")
            for issue in issues:
                print(f"  • {issue}")
            print()
        else:
            print("✅ No issues detected - plot should generate successfully")
            print()

        print("=" * 60)
        print("To generate this plot, run the same command without --preview")
        print()

    def _get_plot_preview_data(self, entities: Dict) -> pd.DataFrame:
        """Get filtered data for plot preview based on entities and session filters."""
        filtered = self.df.copy()

        # Apply session filters first
        session_filters = self.session_state['current_filters']
        if 'device_type' in session_filters:
            filtered = filtered[filtered['device_type'] == session_filters['device_type']]
        if 'flowrate' in session_filters:
            filtered = filtered[filtered['aqueous_flowrate'] == session_filters['flowrate']]
        if 'pressure' in session_filters:
            filtered = filtered[filtered['oil_pressure'] == session_filters['pressure']]

        # Apply entities from query (override session filters if specified)
        if 'device_type' in entities:
            filtered = filtered[filtered['device_type'] == entities['device_type']]
        if 'flowrate' in entities:
            filtered = filtered[filtered['aqueous_flowrate'] == entities['flowrate']]
        if 'pressure' in entities:
            filtered = filtered[filtered['oil_pressure'] == entities['pressure']]

        return filtered

    def _check_plot_feasibility(self, data: pd.DataFrame, entities: Dict) -> List[str]:
        """Check for potential plotting issues."""
        issues = []

        if len(data) == 0:
            issues.append("No data found matching criteria")
            return issues

        # Check for sufficient data points
        if len(data) < 2:
            issues.append("Very few data points - plot may not be meaningful")

        # Check for varying parameters
        device_count = data['device_id'].nunique()
        if device_count == 1:
            issues.append("Only one device - comparison plots may not be useful")

        # Check for missing droplet size data
        droplet_data = data['droplet_size_mean'].dropna()
        if len(droplet_data) == 0:
            issues.append("No droplet size data available")
        elif len(droplet_data) < len(data) * 0.5:
            issues.append("More than 50% of measurements missing droplet size data")

        # Check for missing frequency data
        freq_data = data['frequency_mean'].dropna()
        if len(freq_data) == 0 and 'frequency' in str(entities).lower():
            issues.append("No frequency data available for frequency plot")

        return issues

    def _count_complete_analyses(self, df: pd.DataFrame) -> Dict:
        """
        Count complete vs partial analyses by experimental condition.

        Args:
            df: DataFrame to analyze

        Returns:
            Dict with counts: {complete_droplet: N, complete_freq: N, partial: N, details: List}
        """
        # Group by experimental condition (device_id, testing_date, flow parameters, fluids)
        condition_groups = df.groupby([
            'device_id', 'testing_date', 'aqueous_flowrate', 'oil_pressure',
            'aqueous_fluid', 'oil_fluid'
        ])

        complete_droplet = 0
        complete_freq = 0
        partial = 0
        analysis_details = []

        for condition, group in condition_groups:
            device_id, test_date, flowrate, pressure, aq_fluid, oil_fluid = condition

            # Count droplet analyses (CSV files with DFU measurements)
            droplet_files = group[
                (group['measurement_type'] == 'droplet') &
                (group['file_type'] == 'csv') &
                (pd.notna(group['dfu_row']))
            ]
            unique_dfu_rows = droplet_files['dfu_row'].nunique()

            # Count frequency analyses (TXT files)
            freq_files = group[
                (group['measurement_type'] == 'frequency') &
                (group['file_type'] == 'txt')
            ]
            has_freq_data = len(freq_files) > 0

            # Determine completeness
            is_complete_droplet = unique_dfu_rows >= 4
            is_complete_freq = has_freq_data

            if is_complete_droplet:
                complete_droplet += 1
            if is_complete_freq:
                complete_freq += 1
            if not (is_complete_droplet or is_complete_freq):
                partial += 1

            # Build detail string
            condition_str = f"{device_id} at {flowrate}ml/hr + {pressure}mbar"
            if pd.notna(aq_fluid) and pd.notna(oil_fluid):
                condition_str += f" ({aq_fluid}_{oil_fluid})"

            status_parts = []
            if is_complete_droplet:
                status_parts.append(f"{unique_dfu_rows} DFU rows (complete droplet)")
            elif unique_dfu_rows > 0:
                status_parts.append(f"{unique_dfu_rows} DFU rows (partial)")

            if is_complete_freq:
                status_parts.append("frequency data")

            status = ", ".join(status_parts) if status_parts else "no data"

            analysis_details.append({
                'condition': condition_str,
                'status': status,
                'dfu_rows': unique_dfu_rows,
                'has_freq': has_freq_data,
                'complete_droplet': is_complete_droplet,
                'complete_freq': is_complete_freq
            })

        return {
            'complete_droplet': complete_droplet,
            'complete_freq': complete_freq,
            'partial': partial,
            'details': analysis_details
        }

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

        # Refresh error builder cache with new data
        self.error_builder = ErrorMessageBuilder(self.df)

        # Invalidate query cache due to data change
        if hasattr(self, 'df_cache'):
            self.df_cache.clear()
            self._update_data_hash()

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
                # Get input with dynamic prompt
                prompt = self._get_prompt()
                user_input = input(prompt).strip()

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

                    # Execute the menu action query
                    self._process_query(query)
                    continue

                # Process the user input with error handling
                try:
                    self._process_query(user_input)
                except Exception as e:
                    # Handle unexpected errors gracefully
                    print()
                    print(f"[ERROR] An error occurred: {str(e)}")
                    print("\nIf this continues, try:")
                    print("  • Simplify your query")
                    print("  • Use 'help' to see available commands")
                    print("  • Check 'list devices' and 'list params' for valid options")
                    print()

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
