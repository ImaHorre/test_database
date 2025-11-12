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
import json
import numpy as np


class OutlierDetector:
    """
    Outlier detection for droplet size and frequency measurements (Feature 2).

    Uses Modified Z-Score method (Iglewicz and Hoaglin, 1993):
    - More robust than standard z-score
    - Uses median and MAD (Median Absolute Deviation) instead of mean and std
    - Threshold: |Modified Z-Score| > 3.5 indicates outlier
    """

    def __init__(self, threshold=3.5):
        """
        Initialize outlier detector.

        Args:
            threshold: Modified Z-score threshold (default 3.5, standard in literature)
        """
        self.threshold = threshold

    def detect_outliers(self, data: pd.Series) -> pd.Series:
        """
        Detect outliers using Modified Z-Score method.

        Args:
            data: pandas Series of numerical values

        Returns:
            Boolean Series where True indicates outlier
        """
        if len(data) < 4:
            # Need at least 4 data points for meaningful outlier detection
            return pd.Series([False] * len(data), index=data.index)

        # Calculate median
        median = data.median()

        # Calculate MAD (Median Absolute Deviation)
        mad = np.median(np.abs(data - median))

        # Handle case where MAD = 0 (all values identical)
        if mad == 0:
            return pd.Series([False] * len(data), index=data.index)

        # Calculate Modified Z-Score
        # Formula: M_i = 0.6745 * (x_i - median) / MAD
        # The constant 0.6745 makes the MAD comparable to standard deviation for normal distributions
        modified_z_scores = 0.6745 * (data - median) / mad

        # Flag outliers
        is_outlier = np.abs(modified_z_scores) > self.threshold

        return pd.Series(is_outlier, index=data.index)

    def get_outlier_summary(self, df: pd.DataFrame, outlier_mask: pd.Series, metric_name: str) -> Dict:
        """
        Generate detailed summary of detected outliers for display.

        Args:
            df: Original DataFrame
            outlier_mask: Boolean series indicating outliers
            metric_name: Name of metric ('droplet_size_mean' or 'frequency_mean')

        Returns:
            Dict with outlier details
        """
        outlier_rows = df[outlier_mask]
        total_count = len(df)
        outlier_count = outlier_mask.sum()

        details = []
        for idx, row in outlier_rows.iterrows():
            device_id = row['device_id']
            dfu_row = row.get('dfu_row', 'N/A')
            value = row[metric_name]
            details.append({
                'device_id': device_id,
                'dfu_row': dfu_row,
                'value': value,
                'index': idx
            })

        return {
            'total_count': total_count,
            'outlier_count': outlier_count,
            'outlier_percentage': (outlier_count / total_count * 100) if total_count > 0 else 0,
            'details': details
        }


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
            'query_history': [],
            'outlier_detection_enabled': False,  # Feature 2
            'manual_exclusions': [],  # Feature 2: List of exclusion criteria
            'last_removed_by_outlier': [],  # Feature 2: Track last outlier removals
            'last_removed_by_manual': [],  # Feature 2: Track last manual removals
            'last_exported_csv': None  # Track last CSV export for plotws command
        }

        # Error message builder for context-aware errors
        self.error_builder = ErrorMessageBuilder(self.df)

        # Filter presets (Feature 3)
        self.presets_file = Path(__file__).parent / 'filter_presets.json'
        self.filter_presets = self._load_presets()

        # Outlier detector (Feature 2)
        self.outlier_detector = OutlierDetector(threshold=3.5)

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

    def _detect_parameter_type(self, value: str) -> Dict:
        """
        Detect what type of parameter a value represents.

        Args:
            value: Raw string value to analyze

        Returns:
            {
                'type': 'pressure' | 'flowrate' | 'device' | 'fluid' | 'dfu' | 'device_type' | 'unknown',
                'value': parsed_value,
                'confidence': 'high' | 'low'
            }
        """
        value_lower = value.lower().strip()

        # Check for explicit units
        if 'mbar' in value_lower:
            try:
                pressure = int(value_lower.replace('mbar', '').strip())
                return {
                    'type': 'pressure',
                    'value': pressure,
                    'confidence': 'high'
                }
            except ValueError:
                pass

        if 'mlhr' in value_lower or 'ml/hr' in value_lower:
            try:
                flowrate = int(value_lower.replace('mlhr', '').replace('ml/hr', '').strip())
                return {
                    'type': 'flowrate',
                    'value': flowrate,
                    'confidence': 'high'
                }
            except ValueError:
                pass

        # Check for device type pattern (W13, W14)
        if re.match(r'^w1[34]$', value_lower):
            return {
                'type': 'device_type',
                'value': value_lower.upper(),
                'confidence': 'high'
            }

        # Check for device ID pattern (W13_S1_R1, etc.)
        if re.match(r'^w1[34]_s\d+_r\d+$', value_lower):
            return {
                'type': 'device',
                'value': value_lower.upper(),
                'confidence': 'high'
            }

        # Check for DFU row pattern
        if re.match(r'^dfu[1-4](_[a-z])?$', value_lower):
            return {
                'type': 'dfu',
                'value': value_lower.upper(),
                'confidence': 'high'
            }

        # Check for fluid types with enhanced detection
        # Known aqueous and oil fluids
        known_aqueous = ['sds', 'nacas', 'nacl']
        known_oil = ['so', 'oil']

        # Check for full fluid combination like "SDS_SO" or "NaCas_SO"
        if '_' in value_lower:
            parts = value_lower.split('_')
            if len(parts) == 2:
                aq_part = parts[0]
                oil_part = parts[1]

                if aq_part in known_aqueous and oil_part in known_oil:
                    # Normalize to standard format: SDS_SO, NaCas_SO
                    aq_normalized = 'SDS' if aq_part == 'sds' else 'NaCas' if aq_part == 'nacas' else 'NaCl'
                    oil_normalized = 'SO'
                    return {
                        'type': 'fluid_combination',
                        'aqueous': aq_normalized,
                        'oil': oil_normalized,
                        'value': f"{aq_normalized}_{oil_normalized}",
                        'confidence': 'high'
                    }

        # Check for just aqueous fluid like "SDS" or "NaCas"
        if value_lower in known_aqueous:
            aq_normalized = 'SDS' if value_lower == 'sds' else 'NaCas' if value_lower == 'nacas' else 'NaCl'
            return {
                'type': 'aqueous_fluid',
                'value': aq_normalized,
                'confidence': 'high'
            }

        # Check for just oil fluid like "SO"
        if value_lower in known_oil:
            return {
                'type': 'oil_fluid',
                'value': 'SO',
                'confidence': 'high'
            }

        # Fallback: Check against known fluids from database (for backward compatibility)
        if value_lower in [fluid.lower() for fluid in self.error_builder.valid_fluids]:
            # Find original case version
            for fluid in self.error_builder.valid_fluids:
                if fluid.lower() == value_lower:
                    return {
                        'type': 'fluid',
                        'value': fluid,
                        'confidence': 'high'
                    }

        # Try to infer from number alone
        try:
            num = int(value_lower)

            # Check if it matches a pressure value
            if num in self.error_builder.valid_pressures:
                return {
                    'type': 'pressure',
                    'value': num,
                    'confidence': 'high'
                }

            # Check if it matches a flowrate value
            if num in self.error_builder.valid_flowrates:
                return {
                    'type': 'flowrate',
                    'value': num,
                    'confidence': 'high'
                }

            # Infer based on typical ranges
            if 50 <= num <= 1000:  # Pressure range
                if num in self.error_builder.valid_pressures:
                    return {
                        'type': 'pressure',
                        'value': num,
                        'confidence': 'high'
                    }
                else:
                    return {
                        'type': 'pressure',
                        'value': num,
                        'confidence': 'low'
                    }
            elif 1 <= num <= 50:  # Flowrate range
                if num in self.error_builder.valid_flowrates:
                    return {
                        'type': 'flowrate',
                        'value': num,
                        'confidence': 'high'
                    }
                else:
                    return {
                        'type': 'flowrate',
                        'value': num,
                        'confidence': 'low'
                    }
        except ValueError:
            pass

        return {
            'type': 'unknown',
            'value': value,
            'confidence': 'low'
        }

    def _get_prompt(self) -> str:
        """Get current prompt showing active filters."""
        filters = self.session_state['current_filters']
        if not filters:
            return ">>> "

        # Build filter display with progressive indicators
        # Primary filters (device_type, flowrate, pressure) use @
        # Additional filters (device, fluid, dfu) use |
        primary_parts = []
        additional_parts = []

        if 'device_type' in filters:
            primary_parts.append(filters['device_type'])
        if 'flowrate' in filters:
            primary_parts.append(f"{filters['flowrate']}mlhr")
        if 'pressure' in filters:
            primary_parts.append(f"{filters['pressure']}mbar")

        if 'device' in filters:
            additional_parts.append(filters['device'])
        if 'fluid' in filters:
            additional_parts.append(filters['fluid'])
        if 'aqueous_fluid' in filters:
            additional_parts.append(filters['aqueous_fluid'])
        if 'oil_fluid' in filters:
            additional_parts.append(filters['oil_fluid'])
        if 'dfu' in filters:
            additional_parts.append(filters['dfu'])

        # Build the full filter string
        filter_str = "@".join(primary_parts) if primary_parts else ""

        if additional_parts:
            additional_str = ",".join(additional_parts)
            if filter_str:
                filter_str = f"{filter_str} | {additional_str}"
            else:
                filter_str = additional_str

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
        print("  export (save filtered data to CSV)")
        print("  plotws list, plotws <config> (generate plots)")
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
        print("    NOTE: Now shows per-device breakdown before overall average")
        print()
        print("  show params for [device_type]      - Show all parameter combinations")
        print("    Example: show params for w13")
        print()
        print("  list devices                       - List all devices")
        print("  list types                         - List all device types")
        print("  list params                        - List flow parameters (context-aware)")
        print("  list params all                    - List all parameters (ignore filters)")
        print("    NOTE: list commands respect active filters unless 'all' is used")
        print()
        print("  count [device_type]                - Count records")
        print("    Example: count w13")
        print()
        print("  stats [device_type]                - Show statistics")
        print("    Example: stats w13")
        print("  stats [device_type] at [params]    - Show filtered statistics")
        print("    Example: stats w13 at 5mlhr 200mbar")
        print("  stats                              - Show stats using active filters")
        print("    Example: show w13 at 5mlhr, then: stats")
        print()
        print("INTERACTIVE FILTERING (NEW):")
        print("  filter                             - Launch interactive filter builder")
        print("  presets                            - Manage saved filter presets")
        print("    NOTE: After building a custom filter, you'll be prompted to save it")
        print()
        print("OUTLIER DETECTION & EXCLUSIONS (NEW):")
        print("  -outliers                          - Toggle outlier detection on/off")
        print("  -remove <criteria>                 - Add manual exclusion (space-separated)")
        print("    Examples:")
        print("      -remove W13_S5_R14 DFU1        (exclude device + DFU row)")
        print("      -remove DFU1                   (exclude all DFU1 measurements)")
        print("      -remove SDS_SO                 (exclude by fluid type)")
        print("  -clear-exclusions                  - Clear all manual exclusions")
        print("  -show-exclusions                   - Show current exclusion settings")
        print("    NOTE: Outlier detection uses Modified Z-Score method (threshold=3.5)")
        print("    See OUTLIER_DETECTION_EXPLAINED.md for detailed methodology")
        print()
        print("PROGRESSIVE FILTERING (NEW):")
        print("  After setting initial filters, continue refining:")
        print("    300mbar or show 300mbar          - Add pressure filter")
        print("    W13_S2_R9 or show W13_S2_R9      - Add device filter")
        print("    SDS_SO or show SDS_SO            - Add fluid filter")
        print("    DFU1 or show DFU1                - Add DFU row filter")
        print("  Remove filters:")
        print("    remove 300mbar                   - Remove specific filter")
        print("    undo or back                     - Remove last filter added")
        print("  Examples:")
        print("    >>> show w13 at 10mlhr           [Sets W13@10mlhr]")
        print("    >>> [W13@10mlhr] 300             [Adds 300mbar -> W13@10mlhr@300mbar]")
        print("    >>> [W13@10mlhr@300mbar] W13_S2_R9  [Adds device -> W13@10mlhr@300mbar | W13_S2_R9]")
        print()
        print("SESSION MANAGEMENT:")
        print("  show filters                       - Display active filters")
        print("  clear filters (or just: clear)     - Clear all active filters")
        print("  history                            - Show recent query history")
        print("  repeat last (or just: repeat)      - Repeat the last query")
        print()
        print("DATA EXPORT:")
        print("  export (or: export csv, save, save csv)")
        print("    - Export currently filtered data to CSV file")
        print("    - Applies all active filters and exclusions")
        print("    - Saves to outputs/ directory with descriptive timestamp filename")
        print("    - Example workflow:")
        print("      >>> show w13 at 5mlhr 200mbar")
        print("      >>> export                     (saves W13_5mlhr_200mbar_export_[timestamp].csv)")
        print("      >>> show w13                   (sets W13 filter)")
        print("      >>> export                     (saves W13_export_[timestamp].csv)")
        print("    NOTE: With no filters active, exports entire database as 'all_data_export_[timestamp].csv'")
        print()
        print("PLOTTING:")
        print("  plotws list                        - Show available plot configurations")
        print("  plotws <config_name>               - Generate plot from last export")
        print("    - Must export data first (see DATA EXPORT above)")
        print("    - Uses JSON plot config from configs/plots/")
        print("    - Saves plot to outputs/plots/ directory")
        print("    - Example workflow:")
        print("      >>> filter device_type W13")
        print("      >>> filter flowrate 5")
        print("      >>> export                     (save filtered data)")
        print("      >>> plotws dfu_sweep           (generate DFU sweep plot)")
        print("    Available configs: dfu_sweep, pressure_vs_droplet, flowrate_vs_droplet,")
        print("                       frequency_vs_pressure, stability_over_time, device_type_comparison")
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

        # FUZZY PATTERNS: Handle missing 'at' keyword (user-friendly)
        # Pattern: show w13 5mlhr 200mbar (without 'at')
        match = re.match(r'show\s+(w1[34]|all)\s+(\d+)\s*mlhr\s+(\d+)\s*mbar', cmd)
        if match:
            return {
                'type': 'filter',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None,
                'flowrate': int(match.group(2)),
                'pressure': int(match.group(3)),
                '_interpreted': f"show {match.group(1)} at {match.group(2)}mlhr {match.group(3)}mbar"
            }

        # Pattern: show w13 5mlhr (without 'at')
        match = re.match(r'show\s+(w1[34]|all)\s+(\d+)\s*mlhr', cmd)
        if match:
            return {
                'type': 'filter',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None,
                'flowrate': int(match.group(2)),
                'pressure': None,
                '_interpreted': f"show {match.group(1)} at {match.group(2)}mlhr"
            }

        # Pattern: show w13 200mbar (without 'at')
        match = re.match(r'show\s+(w1[34]|all)\s+(\d+)\s*mbar', cmd)
        if match:
            return {
                'type': 'filter',
                'device_type': match.group(1).upper() if match.group(1) != 'all' else None,
                'flowrate': None,
                'pressure': int(match.group(2)),
                '_interpreted': f"show {match.group(1)} at {match.group(2)}mbar"
            }

        # Pattern: show w13_s1_r2 (specific device ID)
        match = re.match(r'show\s+(w1[34]_s\d+_r\d+)$', cmd)
        if match:
            device_id = match.group(1).upper()
            return {
                'type': 'show_device',
                'device_id': device_id
            }

        # Pattern: show w13 (device type only, not device ID)
        match = re.match(r'show\s+(w1[34])$', cmd)
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

        # Pattern: list params all (unfiltered)
        match = re.match(r'list\s+params\s+all', cmd)
        if match:
            return {
                'type': 'list',
                'what': 'params',
                'ignore_filters': True
            }

        # Pattern: list devices/types/params
        match = re.match(r'list\s+(devices|types|params)', cmd)
        if match:
            return {
                'type': 'list',
                'what': match.group(1),
                'ignore_filters': False
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

        # Pattern: stats (use session filters)
        if cmd == 'stats':
            return {
                'type': 'stats',
                'use_session_filters': True
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

        if cmd in ['clear filters', 'clear', 'clearfilters']:
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

        # Filter builder and presets (Feature 3)
        if cmd == 'filter':
            return {'type': 'build_filter'}

        if cmd in ['presets', 'manage presets', 'show presets']:
            return {'type': 'manage_presets'}

        # Outlier detection and exclusions (Feature 2)
        if cmd in ['-outliers', 'toggle outliers', 'outliers']:
            return {'type': 'toggle_outliers'}

        # Pattern: -remove <exclusion criteria>
        match = re.match(r'-remove\s+(.+)', cmd)
        if match:
            return {
                'type': 'add_exclusion',
                'criteria': match.group(1)
            }

        if cmd in ['-clear-exclusions', 'clear exclusions']:
            return {'type': 'clear_exclusions'}

        if cmd in ['-show-exclusions', 'show exclusions']:
            return {'type': 'show_exclusions'}

        # CSV Export
        if cmd in ['export', 'export csv', 'save csv', 'save']:
            return {'type': 'export_csv'}

        # Plotting from config (plotws command)
        if cmd == 'plotws':
            return {'type': 'plotws_interactive'}

        if cmd == 'plotws list':
            return {'type': 'plotws_list'}

        match = re.match(r'plotws\s+(.+)', cmd)
        if match:
            config_name = match.group(1).strip()
            return {
                'type': 'plotws',
                'config_name': config_name
            }

        # PROGRESSIVE FILTERING: Check if this is an attempt to add a filter parameter
        # Only trigger if we have active filters
        if self.session_state['current_filters']:
            # Pattern: show <value> (e.g., "show 300mbar", "show W13_S2_R9")
            match = re.match(r'show\s+(.+)', cmd)
            if match:
                value = match.group(1)
                return {
                    'type': 'add_filter_parameter',
                    'value': value
                }

            # Pattern: remove <value> or -<value> (e.g., "remove 300mbar", "-300mbar")
            match = re.match(r'(?:remove\s+|-)(.+)', cmd)
            if match:
                value = match.group(1)
                return {
                    'type': 'remove_filter_parameter',
                    'value': value
                }

            # Pattern: undo or back (remove last filter)
            if cmd in ['undo', 'back', 'undo last']:
                return {'type': 'undo_filter'}

            # Pattern: bare value (shorthand for "show <value>")
            # Only if it looks like a parameter value and not a command
            detected = self._detect_parameter_type(cmd)
            if detected['type'] != 'unknown' and detected['confidence'] == 'high':
                return {
                    'type': 'add_filter_parameter',
                    'value': cmd,
                    '_interpreted': f"show {cmd}"
                }

        return None

    def execute_command(self, parsed: Dict):
        """Execute a parsed command."""
        # Show interpretation message if command was fuzzy-matched
        if '_interpreted' in parsed:
            print(f">> Interpreted as: {parsed['_interpreted']}")
            print()

        cmd_type = parsed['type']

        if cmd_type == 'show':
            self._cmd_show(parsed)
        elif cmd_type == 'show_device':
            self._cmd_show_device(parsed)
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
        elif cmd_type == 'build_filter':
            self._cmd_build_filter()
        elif cmd_type == 'manage_presets':
            self._cmd_manage_presets()
        elif cmd_type == 'toggle_outliers':
            self._cmd_toggle_outliers()
        elif cmd_type == 'add_exclusion':
            self._cmd_add_exclusion(parsed['criteria'])
        elif cmd_type == 'clear_exclusions':
            self._cmd_clear_exclusions()
        elif cmd_type == 'show_exclusions':
            self._cmd_show_exclusions()
        elif cmd_type == 'add_filter_parameter':
            self._cmd_add_filter_parameter(parsed)
        elif cmd_type == 'remove_filter_parameter':
            self._cmd_remove_filter_parameter(parsed)
        elif cmd_type == 'undo_filter':
            self._cmd_undo_filter()
        elif cmd_type == 'export_csv':
            self._cmd_export_csv()
        elif cmd_type == 'plotws_interactive':
            self._cmd_plotws_interactive()
        elif cmd_type == 'plotws_list':
            self._cmd_plotws_list()
        elif cmd_type == 'plotws':
            self._cmd_plotws(parsed['config_name'])

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

    def _cmd_show_device(self, parsed: Dict):
        """Show all records for a specific device ID."""
        device_id = parsed['device_id']
        filtered = self.df[self.df['device_id'] == device_id]

        if len(filtered) == 0:
            print()
            print(f"[ERROR] No measurements found for device {device_id}")
            print()
            return

        print()
        print(f"Records for {device_id}:")
        print(f"Total: {len(filtered)} measurements")
        print()

        # Show flow parameter combinations
        flow_params = filtered[['aqueous_flowrate', 'oil_pressure']].drop_duplicates()
        print(f"Flow parameter combinations ({len(flow_params)}):")
        for _, row in flow_params.iterrows():
            fr = int(row['aqueous_flowrate'])
            pr = int(row['oil_pressure'])
            count = len(filtered[
                (filtered['aqueous_flowrate'] == row['aqueous_flowrate']) &
                (filtered['oil_pressure'] == row['oil_pressure'])
            ])
            print(f"  • {fr}ml/hr @ {pr}mbar: {count} measurements")

        # Update session state - add device filter to current filters
        query_str = f"show {device_id.lower()}"
        current_filters = {'device': device_id}

        # Extract device_type from device_id
        device_type = device_id.split('_')[0]
        current_filters['device_type'] = device_type

        self._update_session_state(query_str, "show_device", current_filters, filtered)

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

        # Apply additional filters from session state (fluid, device, dfu)
        # This ensures progressive filtering works correctly when adding parameters
        if hasattr(self, 'session_state') and self.session_state.get('current_filters'):
            session_filters = self.session_state['current_filters']

            # Apply device filter
            if 'device' in session_filters:
                filtered = filtered[filtered['device_id'] == session_filters['device']]

            # Apply fluid filters
            if 'fluid' in session_filters:
                fluid_value = session_filters['fluid']
                if '_' in fluid_value:
                    # It's a combination like "SDS_SO"
                    aq, oil = fluid_value.split('_')
                    filtered = filtered[(filtered['aqueous_fluid'] == aq) & (filtered['oil_fluid'] == oil)]
                else:
                    # Check both aqueous and oil fluid columns
                    filtered = filtered[
                        (filtered['aqueous_fluid'] == fluid_value) |
                        (filtered['oil_fluid'] == fluid_value)
                    ]

            if 'aqueous_fluid' in session_filters:
                filtered = filtered[filtered['aqueous_fluid'] == session_filters['aqueous_fluid']]

            if 'oil_fluid' in session_filters:
                filtered = filtered[filtered['oil_fluid'] == session_filters['oil_fluid']]

            # Apply DFU filter
            if 'dfu' in session_filters:
                filtered = filtered[filtered['dfu_row'] == session_filters['dfu']]

        # Apply exclusions and outlier detection (Feature 2)
        original_count = len(filtered)
        filtered, removal_info = self._apply_exclusions(filtered)
        final_count = len(filtered)

        # Display removal info if any removals occurred
        if removal_info['outlier_count'] > 0 or removal_info['manual_count'] > 0:
            self._display_removal_info(removal_info, original_count, final_count)

        # Build filters dict for session state
        current_filters = {}

        # Build filter description (include session state filters)
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

        # Add session state filters to description
        if hasattr(self, 'session_state') and self.session_state.get('current_filters'):
            session_filters = self.session_state['current_filters']

            if 'device' in session_filters:
                filter_desc.append(f"device={session_filters['device']}")

            if 'fluid' in session_filters:
                fluid_value = session_filters['fluid']
                if '_' in fluid_value:
                    aq, oil = fluid_value.split('_')
                    filter_desc.append(f"aqueous_fluid={aq}")
                    filter_desc.append(f"oil_fluid={oil}")
                else:
                    filter_desc.append(f"fluid={fluid_value}")

            if 'aqueous_fluid' in session_filters:
                filter_desc.append(f"aqueous_fluid={session_filters['aqueous_fluid']}")

            if 'oil_fluid' in session_filters:
                filter_desc.append(f"oil_fluid={session_filters['oil_fluid']}")

            if 'dfu' in session_filters:
                filter_desc.append(f"dfu={session_filters['dfu']}")

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
            count_parts.append(f"{analysis_counts['complete_droplet']} complete droplet analys" + ("es" if analysis_counts['complete_droplet'] > 1 else "is"))
        if analysis_counts['complete_freq'] > 0:
            count_parts.append(f"{analysis_counts['complete_freq']} complete frequency analys" + ("es" if analysis_counts['complete_freq'] > 1 else "is"))
        if analysis_counts['partial'] > 0:
            count_parts.append(f"{analysis_counts['partial']} partial analys" + ("es" if analysis_counts['partial'] > 1 else "is"))

        if count_parts:
            print(f"Found: {', '.join(count_parts)}")
        else:
            print("Found: No complete analyses")
        print()

        # Show detailed breakdown by device with full experimental context
        print("Matching Devices:")

        # Get unique device IDs first
        unique_devices = sorted(set([
            detail['condition'].split(' at ')[0]
            for detail in analysis_counts['details']
        ]))

        # Show each device with ALL its conditions
        for idx, device_id in enumerate(unique_devices, 1):
            # Get all conditions for this device
            device_details = [
                d for d in analysis_counts['details']
                if d['condition'].startswith(device_id)
            ]

            print(f"  {idx}. {device_id}:")

            # Show ALL conditions tested for this device
            for d in device_details:
                condition_part = d['condition'].split(' at ', 1)[1]
                # Use the pre-calculated status from _count_complete_analyses
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

        # Show per-device breakdown statistics (Feature 1)
        device_stats = self._calculate_device_level_stats(filtered)
        if device_stats:
            print("Per-Device Statistics:")
            for device_id, stats in device_stats.items():
                print(f"  {device_id}:")
                if 'droplet_size' in stats and pd.notna(stats['droplet_size']['mean']):
                    mean = stats['droplet_size']['mean']
                    std = stats['droplet_size']['std']
                    n = stats['droplet_size']['count']
                    print(f"    • Droplet Size: {mean:.2f} ± {std:.2f} µm (n={n})")
                if 'frequency' in stats and pd.notna(stats['frequency']['mean']):
                    mean = stats['frequency']['mean']
                    std = stats['frequency']['std']
                    n = stats['frequency']['count']
                    print(f"    • Frequency:    {mean:.2f} ± {std:.2f} Hz (n={n})")
            print()

        # Show summary statistics (overall average)
        print("Overall Average:")
        if 'droplet_size_mean' in filtered.columns:
            droplet_mean = filtered['droplet_size_mean'].mean()
            droplet_std = filtered['droplet_size_mean'].std()
            droplet_count = filtered['droplet_size_mean'].notna().sum()
            if pd.notna(droplet_mean):
                print(f"  Droplet Size: {droplet_mean:.2f} ± {droplet_std:.2f} µm (n={droplet_count})")

        if 'frequency_mean' in filtered.columns:
            freq_data = filtered['frequency_mean'].dropna()
            if len(freq_data) > 0:
                freq_mean = freq_data.mean()
                freq_std = freq_data.std()
                print(f"  Frequency:    {freq_mean:.2f} ± {freq_std:.2f} Hz (n={len(freq_data)})")

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

            # Build analysis summary - show both droplet and frequency status explicitly
            analysis_parts = []

            # Show droplet status explicitly
            csv_data = group[group['file_type'] == 'csv']
            if len(csv_data) > 0:
                dfu_counts = csv_data['dfu_row'].nunique()
                analysis_parts.append(f"Droplet ({dfu_counts} DFU rows measured)")
            else:
                analysis_parts.append(f"Droplet (none)")

            # Show frequency status explicitly
            txt_data = group[group['file_type'] == 'txt']
            if len(txt_data) > 0:
                freq_count = len(txt_data)
                analysis_parts.append(f"Frequency ({freq_count} measurements)")
            else:
                analysis_parts.append(f"Frequency (none)")

            analysis_summary = ", ".join(analysis_parts)

            print(f"  {idx}. {flowrate}ml/hr + {pressure}mbar: {analysis_summary} - {unique_devices} device{'s' if unique_devices != 1 else ''}")

        print()

    def _cmd_list(self, parsed: Dict):
        """List devices, types, or parameters (Feature 4: Context-aware)."""
        what = parsed['what']
        ignore_filters = parsed.get('ignore_filters', False)

        # Apply session filters unless explicitly ignored (Feature 4)
        filtered = self.df.copy()
        filters_applied = []

        if not ignore_filters:
            session_filters = self.session_state['current_filters']
            if 'device_type' in session_filters:
                filtered = filtered[filtered['device_type'] == session_filters['device_type']]
                filters_applied.append(f"device_type={session_filters['device_type']}")
            if 'flowrate' in session_filters:
                filtered = filtered[filtered['aqueous_flowrate'] == session_filters['flowrate']]
                filters_applied.append(f"flowrate={session_filters['flowrate']}mlhr")
            if 'pressure' in session_filters:
                filtered = filtered[filtered['oil_pressure'] == session_filters['pressure']]
                filters_applied.append(f"pressure={session_filters['pressure']}mbar")

        print()

        # Show filter context
        if filters_applied:
            print(f"Context: {', '.join(filters_applied)}")
            print(f"(Use 'list {what} all' to see all data)")
            print()
        elif not ignore_filters and what == 'params':
            print("Showing all parameters (no filters active)")
            print()

        if what == 'devices':
            devices = filtered.groupby('device_id').agg({
                'device_type': 'first',
                'testing_date': ['min', 'max'],
                'droplet_size_mean': 'count'
            })

            if filters_applied:
                print(f"Devices in Current Context ({len(devices)}):")
            else:
                print(f"All Devices ({len(devices)}):")
            print()
            for idx, device_id in enumerate(sorted(devices.index), 1):
                dtype = devices.loc[device_id, ('device_type', 'first')]
                count = devices.loc[device_id, ('droplet_size_mean', 'count')]
                print(f"  {idx:2d}. {device_id} ({dtype}): {count} measurements")

        elif what == 'types':
            types = filtered['device_type'].value_counts()
            print("Device Types:")
            print()
            for dtype, count in types.items():
                print(f"  • {dtype}: {count} measurements")

        elif what == 'params':
            params = filtered.groupby(['aqueous_flowrate', 'oil_pressure']).size().reset_index(name='count')
            if filters_applied:
                print("Flow Parameters in Current Context:")
            else:
                print("All Flow Parameters:")
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
        # Check if should use session filters
        if parsed.get('use_session_filters'):
            session_filters = self.session_state['current_filters']

            if not session_filters:
                print()
                print("[ERROR] No active filters set.")
                print("Either set filters first ('show w13 at 5mlhr') or specify device type ('stats w13')")
                print()
                return

            device_type = session_filters.get('device_type')
            flowrate = session_filters.get('flowrate')
            pressure = session_filters.get('pressure')
        else:
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
            print("Device Breakdown:")

            # Get unique device IDs first
            unique_devices = sorted(set([
                detail['condition'].split(' at ')[0]
                for detail in analysis_counts['details']
            ]))

            # Show each device with ALL its conditions
            for device_id in unique_devices:
                # Get all conditions for this device
                device_details = [
                    d for d in analysis_counts['details']
                    if d['condition'].startswith(device_id)
                ]

                print(f"  {device_id}:")
                for d in device_details:
                    condition_part = d['condition'].split(' at ', 1)[1]  # Get everything after device_id
                    # Use the pre-calculated status from _count_complete_analyses
                    print(f"    • {condition_part}: {d['status']}")
            print()

        # Droplet size stats
        droplet_data = filtered['droplet_size_mean'].dropna()
        if len(droplet_data) > 0:
            print("Droplet Size Statistics:")
            print(f"  Mean:    {droplet_data.mean():.2f} µm")
            print(f"  Std:     {droplet_data.std():.2f} µm")

            # Find min value with source
            min_idx = droplet_data.idxmin()
            min_row = filtered.loc[min_idx]
            min_val = droplet_data.min()
            print(f"  Min:     {min_val:.2f} µm")
            print(f"           → {min_row['device_id']} at {min_row['aqueous_flowrate']}ml/hr + {min_row['oil_pressure']}mbar")
            print(f"           → File: {min_row['file_name']}")

            # Find max value with source
            max_idx = droplet_data.idxmax()
            max_row = filtered.loc[max_idx]
            max_val = droplet_data.max()
            print(f"  Max:     {max_val:.2f} µm")
            print(f"           → {max_row['device_id']} at {max_row['aqueous_flowrate']}ml/hr + {max_row['oil_pressure']}mbar")
            print(f"           → File: {max_row['file_name']}")
            print()

        # Frequency stats
        freq_data = filtered['frequency_mean'].dropna()
        if len(freq_data) > 0:
            print("Frequency Statistics:")
            print(f"  Mean:    {freq_data.mean():.2f} Hz")
            print(f"  Std:     {freq_data.std():.2f} Hz")

            # Find min value with source
            min_idx = freq_data.idxmin()
            min_row = filtered.loc[min_idx]
            min_val = freq_data.min()
            print(f"  Min:     {min_val:.2f} Hz")
            print(f"           → {min_row['device_id']} at {min_row['aqueous_flowrate']}ml/hr + {min_row['oil_pressure']}mbar")
            print(f"           → File: {min_row['file_name']}")

            # Find max value with source
            max_idx = freq_data.idxmax()
            max_row = filtered.loc[max_idx]
            max_val = freq_data.max()
            print(f"  Max:     {max_val:.2f} Hz")
            print(f"           → {max_row['device_id']} at {max_row['aqueous_flowrate']}ml/hr + {max_row['oil_pressure']}mbar")
            print(f"           → File: {max_row['file_name']}")
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

        # Check if this is a simple "plot" command with active filters - show interactive menu
        if self._is_plot_command(query) and query.lower().strip() in ['plot', 'graph', 'chart']:
            if self.session_state['current_filters']:
                self._show_interactive_plot_menu()
                return
            else:
                print("No active filters set. Please filter data first.")
                print("Example: show w13 at 5mlhr")
                print()
                return

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

    def _show_interactive_plot_menu(self):
        """Show interactive menu for plot options based on current filters."""
        print()
        print("=" * 70)
        print("PLOT OPTIONS")
        print("=" * 70)
        print()

        # Get current filtered data
        filters = self.session_state['current_filters']
        filtered = self.df.copy()

        if filters.get('device_type'):
            filtered = filtered[filtered['device_type'] == filters['device_type']]
        if filters.get('flowrate'):
            filtered = filtered[filtered['aqueous_flowrate'] == filters['flowrate']]
        if filters.get('pressure'):
            filtered = filtered[filtered['oil_pressure'] == filters['pressure']]

        if len(filtered) == 0:
            print("No data available with current filters.")
            print()
            return

        # Analyze available data
        devices = sorted(filtered['device_id'].unique())
        has_droplet = len(filtered[filtered['file_type'] == 'csv']) > 0
        has_freq = len(filtered[filtered['file_type'] == 'txt']) > 0

        # Show current context
        print(f"Current filters: {filters}")
        print(f"Data available: {len(filtered)} measurements, {len(devices)} device(s)")
        print()

        # Build menu options
        options = {}
        option_key = 'A'

        print("What would you like to plot?")
        print()

        # Droplet options
        if has_droplet:
            print("DROPLET MEASUREMENTS:")

            if len(devices) > 1:
                options[option_key] = ('plot_compare_droplet', devices, 'all')
                print(f"  {option_key}. Compare droplet sizes between all devices")
                option_key = chr(ord(option_key) + 1)

            for device in devices:
                options[option_key] = ('plot_droplet_dist', [device], device)
                print(f"  {option_key}. Droplet size distribution for {device}")
                option_key = chr(ord(option_key) + 1)

            print()

        # Frequency options
        if has_freq:
            print("FREQUENCY MEASUREMENTS:")

            if len(devices) > 1:
                options[option_key] = ('plot_compare_freq', devices, 'all')
                print(f"  {option_key}. Compare frequencies between all devices")
                option_key = chr(ord(option_key) + 1)

            for device in devices:
                options[option_key] = ('plot_freq_dist', [device], device)
                print(f"  {option_key}. Frequency distribution for {device}")
                option_key = chr(ord(option_key) + 1)

            print()

        # Combined options
        if has_droplet and has_freq:
            print("COMBINED PLOTS:")
            for device in devices:
                options[option_key] = ('plot_combined', [device], device)
                print(f"  {option_key}. Both droplet and frequency for {device}")
                option_key = chr(ord(option_key) + 1)
            print()

        # Get user choice
        print("=" * 70)
        choice = input("\nSelect option (letter) or 'cancel': ").strip().upper()
        print()

        if choice == 'CANCEL':
            print("Plot cancelled.")
            print()
            return

        if choice not in options:
            print(f"Invalid option '{choice}'. Plot cancelled.")
            print()
            return

        # Execute the chosen plot
        plot_type, device_list, device_label = options[choice]
        self._execute_plot_option(plot_type, device_list, device_label, filtered)

    def _execute_plot_option(self, plot_type: str, devices: list, label: str, data: pd.DataFrame):
        """Execute a specific plot option."""
        print(f"Generating {plot_type} for {label}...")
        print()

        # Build appropriate query based on plot type
        filters = self.session_state['current_filters']
        device_type = filters.get('device_type', 'W13')
        flowrate = filters.get('flowrate', '')

        if plot_type == 'plot_compare_droplet':
            query = f"plot {device_type} droplet sizes"
            if flowrate:
                query += f" at {flowrate}mlhr"

        elif plot_type == 'plot_droplet_dist':
            query = f"plot droplet size distribution for {devices[0]}"

        elif plot_type == 'plot_compare_freq':
            query = f"plot {device_type} frequency"
            if flowrate:
                query += f" at {flowrate}mlhr"

        elif plot_type == 'plot_freq_dist':
            query = f"plot frequency distribution for {devices[0]}"

        elif plot_type == 'plot_combined':
            query = f"plot {devices[0]} droplet and frequency"

        else:
            print(f"Plot type '{plot_type}' not yet implemented.")
            print()
            return

        # Execute through natural language processor
        print(f"Executing: {query}")
        print()
        result = self.analyst.process_natural_language_query(query)

        # Show results
        status = result.get('status', 'unknown')
        message = result.get('message', '')

        if status == 'success':
            print("[Success]")
            print()
            print(message)

            plot_path = result.get('plot_path')
            if plot_path:
                print(f"\nPlot saved: {plot_path}")
        else:
            print(f"[{status.title()}]")
            print()
            print(message)

        print()

    def _load_presets(self) -> Dict:
        """Load filter presets from JSON file."""
        if self.presets_file.exists():
            try:
                with open(self.presets_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_presets(self):
        """Save filter presets to JSON file."""
        try:
            with open(self.presets_file, 'w') as f:
                json.dump(self.filter_presets, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving presets: {e}")
            return False

    def _prompt_save_preset(self, filters: Dict):
        """Prompt user to save current filter as preset (Feature 3)."""
        print()
        print("-" * 70)
        response = input("Save this filter as a preset? (y/n): ").strip().lower()

        if response not in ['y', 'yes']:
            return

        # Get preset name
        preset_name = input("Enter preset name: ").strip()
        if not preset_name:
            print("Preset not saved (empty name).")
            return

        # Save preset
        self.filter_presets[preset_name] = filters.copy()
        if self._save_presets():
            print(f"Preset '{preset_name}' saved successfully.")
        print("-" * 70)
        print()

    def _cmd_build_filter(self):
        """Interactive filter builder with progressive filtering (Feature 3)."""
        print()
        print("=" * 70)
        print("INTERACTIVE FILTER BUILDER")
        print("=" * 70)
        print()

        # Show available presets
        if self.filter_presets:
            print("Saved Presets:")
            for idx, (name, filters) in enumerate(self.filter_presets.items(), 1):
                filter_str = self._format_filter_dict(filters)
                print(f"  {idx}. {name}: {filter_str}")
            print()

            load_preset = input("Load a preset? (number or 'n'): ").strip().lower()
            if load_preset.isdigit():
                preset_idx = int(load_preset) - 1
                preset_list = list(self.filter_presets.items())
                if 0 <= preset_idx < len(preset_list):
                    preset_name, filters = preset_list[preset_idx]
                    print(f"\nLoaded preset: {preset_name}")
                    query_str = self._build_query_from_filters(filters)
                    print(f"Executing: {query_str}\n")
                    self._process_query(query_str)
                    return

        print("Build Custom Filter:")
        print()

        # Start with full dataframe
        filtered_df = self.df.copy()

        # Device type
        print("Device Type:")
        device_counts = filtered_df['device_type'].value_counts()
        device_options = []
        for idx, device_type in enumerate(['W13', 'W14'], 1):
            count = device_counts.get(device_type, 0)
            print(f"  {idx}. {device_type} ({count} measurements)")
            device_options.append((device_type, count))
        print(f"  3. Both (no filter)")
        device_choice = input("Select (1-3): ").strip()

        device_type = None
        if device_choice == '1':
            device_type = 'W13'
            filtered_df = filtered_df[filtered_df['device_type'] == 'W13']
        elif device_choice == '2':
            device_type = 'W14'
            filtered_df = filtered_df[filtered_df['device_type'] == 'W14']

        # Specific Device - show all devices based on device_type filter
        print("\nSpecific Device:")
        if device_type:
            print(f"  (Available for {device_type})")

        # Get unique devices from filtered data, sorted
        available_devices = sorted(filtered_df['device_id'].unique())
        device_id_options = []

        # Display devices with measurement counts
        for idx, dev_id in enumerate(available_devices, 1):
            count = len(filtered_df[filtered_df['device_id'] == dev_id])
            print(f"  {idx}. {dev_id} ({count} measurements)")
            device_id_options.append((dev_id, count))

        print(f"  {len(available_devices) + 1}. All devices (no filter)")

        device_id_choice = input(f"Select (1-{len(available_devices) + 1}) or press Enter for all: ").strip()
        device_id = None

        if device_id_choice.isdigit():
            idx = int(device_id_choice) - 1
            if 0 <= idx < len(available_devices):
                device_id = available_devices[idx]
                # Apply device_id filter
                filtered_df = filtered_df[filtered_df['device_id'] == device_id]

        # Flow rate - only show options that exist in filtered data
        print("\nFlow Rate:")
        filter_desc = []
        if device_type:
            filter_desc.append(device_type)
        if device_id:
            filter_desc.append(device_id)
        if filter_desc:
            print(f"  (Available for {' > '.join(filter_desc)})")
        available_flowrates = sorted(filtered_df['aqueous_flowrate'].dropna().unique())
        flowrate_options = []
        for idx, fr in enumerate(available_flowrates, 1):
            # Count measurements for this flowrate in currently filtered data
            count = len(filtered_df[filtered_df['aqueous_flowrate'] == fr])
            print(f"  {idx}. {int(fr)}ml/hr ({count} measurements)")
            flowrate_options.append((int(fr), count))
        print(f"  {len(available_flowrates) + 1}. Any (no filter)")

        flowrate_choice = input(f"Select (1-{len(available_flowrates) + 1}): ").strip()
        flowrate = None
        if flowrate_choice.isdigit():
            idx = int(flowrate_choice) - 1
            if 0 <= idx < len(available_flowrates):
                flowrate = int(available_flowrates[idx])
                # Apply flowrate filter
                filtered_df = filtered_df[filtered_df['aqueous_flowrate'] == flowrate]

        # Pressure - only show options that exist in currently filtered data
        print("\nPressure:")
        filter_desc = []
        if device_type:
            filter_desc.append(device_type)
        if device_id:
            filter_desc.append(device_id)
        if flowrate:
            filter_desc.append(f"{flowrate}ml/hr")
        if filter_desc:
            print(f"  (Available for {' > '.join(filter_desc) if device_id else ' at '.join(filter_desc)})")

        available_pressures = sorted(filtered_df['oil_pressure'].dropna().unique())
        pressure_options = []
        for idx, pr in enumerate(available_pressures, 1):
            # Count measurements for this pressure in currently filtered data
            count = len(filtered_df[filtered_df['oil_pressure'] == pr])
            print(f"  {idx}. {int(pr)}mbar ({count} measurements)")
            pressure_options.append((int(pr), count))
        print(f"  {len(available_pressures) + 1}. Any (no filter)")

        pressure_choice = input(f"Select (1-{len(available_pressures) + 1}): ").strip()
        pressure = None
        if pressure_choice.isdigit():
            idx = int(pressure_choice) - 1
            if 0 <= idx < len(available_pressures):
                pressure = int(available_pressures[idx])

        # Build and execute query
        filters = {}
        if device_type:
            filters['device_type'] = device_type
        if device_id:
            filters['device'] = device_id
        if flowrate:
            filters['flowrate'] = flowrate
        if pressure:
            filters['pressure'] = pressure

        if not filters:
            print("\nNo filters selected. Cancelled.")
            print()
            return

        query_str = self._build_query_from_filters(filters)
        print(f"\nExecuting: {query_str}\n")
        print("=" * 70)
        print()

        self._process_query(query_str)

        # Prompt to save as preset (Feature 3)
        self._prompt_save_preset(filters)

    def _format_filter_dict(self, filters: Dict) -> str:
        """Format filter dictionary for display."""
        parts = []
        if 'device_type' in filters:
            parts.append(filters['device_type'])
        if 'device' in filters:
            parts.append(filters['device'])
        if 'flowrate' in filters:
            parts.append(f"{filters['flowrate']}mlhr")
        if 'pressure' in filters:
            parts.append(f"{filters['pressure']}mbar")
        return " @ ".join(parts) if parts else "No filters"

    def _build_query_from_filters(self, filters: Dict) -> str:
        """Build a query string from filter dictionary."""
        parts = []

        # Start with device_type or device (specific device overrides device_type)
        if 'device' in filters:
            # If specific device is selected, use it directly
            parts.append(f"show {filters['device'].lower()}")
        else:
            device_type = filters.get('device_type', 'all')
            parts.append(f"show {device_type.lower()}")

        param_parts = []
        if 'flowrate' in filters:
            param_parts.append(f"{filters['flowrate']}mlhr")
        if 'pressure' in filters:
            param_parts.append(f"{filters['pressure']}mbar")

        if param_parts:
            parts.append("at")
            parts.extend(param_parts)

        return " ".join(parts)

    def _cmd_manage_presets(self):
        """Manage saved filter presets (Feature 3)."""
        print()
        print("=" * 70)
        print("FILTER PRESETS")
        print("=" * 70)
        print()

        if not self.filter_presets:
            print("No saved presets.")
            print()
            return

        print("Saved Presets:")
        for idx, (name, filters) in enumerate(self.filter_presets.items(), 1):
            filter_str = self._format_filter_dict(filters)
            print(f"  {idx}. {name}: {filter_str}")
        print()

        print("Actions:")
        print("  [L] Load preset")
        print("  [D] Delete preset")
        print("  [C] Cancel")
        print()

        action = input("Select action: ").strip().upper()

        if action == 'L':
            preset_num = input("Enter preset number to load: ").strip()
            if preset_num.isdigit():
                idx = int(preset_num) - 1
                preset_list = list(self.filter_presets.items())
                if 0 <= idx < len(preset_list):
                    name, filters = preset_list[idx]
                    query_str = self._build_query_from_filters(filters)
                    print(f"\nLoading preset: {name}")
                    print(f"Executing: {query_str}\n")
                    self._process_query(query_str)

        elif action == 'D':
            preset_num = input("Enter preset number to delete: ").strip()
            if preset_num.isdigit():
                idx = int(preset_num) - 1
                preset_list = list(self.filter_presets.keys())
                if 0 <= idx < len(preset_list):
                    name = preset_list[idx]
                    del self.filter_presets[name]
                    if self._save_presets():
                        print(f"\nPreset '{name}' deleted.")
                    print()

        print()

    def _cmd_toggle_outliers(self):
        """Toggle outlier detection on/off (Feature 2)."""
        self.session_state['outlier_detection_enabled'] = not self.session_state['outlier_detection_enabled']
        status = "enabled" if self.session_state['outlier_detection_enabled'] else "disabled"
        print()
        print(f"Outlier detection {status}.")
        if self.session_state['outlier_detection_enabled']:
            print("Using Modified Z-Score method (threshold=3.5)")
            print("Outliers will be removed from query results.")
        print()

        # Auto-refresh results if there are active filters
        if self.session_state['current_filters']:
            print("Refreshing results with updated outlier detection...")
            print()
            self._cmd_filter(self.session_state['current_filters'])

    def _cmd_add_exclusion(self, criteria: str):
        """Add manual exclusion criteria (Feature 2)."""
        self.session_state['manual_exclusions'].append(criteria)
        print()
        print(f"Added exclusion: {criteria}")
        print(f"Total exclusions: {len(self.session_state['manual_exclusions'])}")
        print()

        # Auto-refresh results if there are active filters
        if self.session_state['current_filters']:
            print("Refreshing results with exclusion applied...")
            print()
            self._cmd_filter(self.session_state['current_filters'])

    def _cmd_clear_exclusions(self):
        """Clear all manual exclusions (Feature 2)."""
        count = len(self.session_state['manual_exclusions'])
        self.session_state['manual_exclusions'] = []
        print()
        print(f"Cleared {count} exclusion(s).")
        print()

        # Auto-refresh results if there are active filters
        if self.session_state['current_filters']:
            print("Refreshing results with exclusions cleared...")
            print()
            self._cmd_filter(self.session_state['current_filters'])

    def _cmd_show_exclusions(self):
        """Show current exclusions and outlier detection status (Feature 2)."""
        print()
        print("=" * 70)
        print("EXCLUSION SETTINGS")
        print("=" * 70)
        print()

        # Outlier detection status
        print("Outlier Detection:")
        if self.session_state['outlier_detection_enabled']:
            print("  Status: ENABLED")
            print("  Method: Modified Z-Score (threshold=3.5)")
            if self.session_state['last_removed_by_outlier']:
                print(f"  Last run removed: {len(self.session_state['last_removed_by_outlier'])} measurements")
        else:
            print("  Status: DISABLED")
        print()

        # Manual exclusions
        print("Manual Exclusions:")
        if self.session_state['manual_exclusions']:
            for idx, exclusion in enumerate(self.session_state['manual_exclusions'], 1):
                print(f"  {idx}. {exclusion}")
            if self.session_state['last_removed_by_manual']:
                print(f"\n  Last run removed: {len(self.session_state['last_removed_by_manual'])} measurements")
        else:
            print("  None")
        print()

        print("Commands:")
        print("  -outliers              Toggle outlier detection")
        print("  -remove <criteria>     Add exclusion (space-separated)")
        print("  -clear-exclusions      Clear all exclusions")
        print()
        print("Example exclusion syntax:")
        print("  -remove W13_S5_R14 DFU1    (exclude specific device and DFU row)")
        print("  -remove DFU1               (exclude all DFU1 measurements)")
        print("  -remove SDS_SO             (exclude specific fluid combination)")
        print("=" * 70)
        print()

    def _cmd_add_filter_parameter(self, parsed: Dict):
        """Add a parameter to existing session filters (progressive filtering)."""
        value = parsed['value']

        # Detect parameter type
        detected = self._detect_parameter_type(value)

        if detected['type'] == 'unknown':
            print()
            print(f"[ERROR] Cannot determine parameter type for '{value}'")
            print("Please specify units (e.g., '300mbar', '10mlhr') or use recognizable format")
            print()
            return

        # Show interpretation if low confidence
        if detected['confidence'] == 'low':
            param_type_name = detected['type'].replace('_', ' ')
            user_input = input(f"Interpret '{value}' as {param_type_name} '{detected['value']}'? (y/n): ").strip().lower()
            if user_input not in ['y', 'yes']:
                print("Filter not applied.")
                return

        # Check if this would conflict with existing filters
        param_type = detected['type']
        param_value = detected['value']

        # Map parameter types to filter keys
        filter_key_map = {
            'pressure': 'pressure',
            'flowrate': 'flowrate',
            'device': 'device',
            'fluid': 'fluid',
            'fluid_combination': 'fluid',
            'aqueous_fluid': 'aqueous_fluid',
            'oil_fluid': 'oil_fluid',
            'dfu': 'dfu',
            'device_type': 'device_type'
        }

        filter_key = filter_key_map.get(param_type)
        if not filter_key:
            print(f"[ERROR] Cannot apply parameter type: {param_type}")
            return

        # Check if we're overwriting an existing filter
        if filter_key in self.session_state['current_filters']:
            old_value = self.session_state['current_filters'][filter_key]
            print()
            print(f"[WARNING] Replacing existing {param_type} filter: {old_value} -> {param_value}")
            print()

        # Build new filters dict by adding this parameter
        new_filters = self.session_state['current_filters'].copy()
        new_filters[filter_key] = param_value

        # Add the additional filters to session state BEFORE calling _cmd_filter
        # so that _cmd_filter can access them when filtering
        if 'device' in new_filters:
            self.session_state['current_filters']['device'] = new_filters['device']
        if 'fluid' in new_filters:
            self.session_state['current_filters']['fluid'] = new_filters['fluid']
        if 'aqueous_fluid' in new_filters:
            self.session_state['current_filters']['aqueous_fluid'] = new_filters['aqueous_fluid']
        if 'oil_fluid' in new_filters:
            self.session_state['current_filters']['oil_fluid'] = new_filters['oil_fluid']
        if 'dfu' in new_filters:
            self.session_state['current_filters']['dfu'] = new_filters['dfu']

        # Try to apply the filter
        # Build a parsed dict for _cmd_filter
        filter_parsed = {
            'device_type': new_filters.get('device_type'),
            'flowrate': new_filters.get('flowrate'),
            'pressure': new_filters.get('pressure')
        }

        # Apply the filter (will now pick up fluid filters from session state)
        self._cmd_filter(filter_parsed)

        # Apply additional filters to the last result if needed
        if self.session_state['last_filtered_df'] is not None:
            df = self.session_state['last_filtered_df']
            original_count = len(df)

            if 'device' in new_filters:
                df = df[df['device_id'] == new_filters['device']]

            # Handle different fluid filter types
            if 'fluid' in new_filters:
                # Full combination filter (e.g., "SDS_SO")
                # This might be a combination or a single fluid from old-style detection
                fluid_value = new_filters['fluid']
                if '_' in fluid_value:
                    # It's a combination like "SDS_SO"
                    aq, oil = fluid_value.split('_')
                    df = df[(df['aqueous_fluid'] == aq) & (df['oil_fluid'] == oil)]
                else:
                    # Check both aqueous and oil fluid columns
                    df = df[
                        (df['aqueous_fluid'] == fluid_value) |
                        (df['oil_fluid'] == fluid_value)
                    ]

            if 'aqueous_fluid' in new_filters:
                # Filter by aqueous fluid only (e.g., "SDS" or "NaCas")
                df = df[df['aqueous_fluid'] == new_filters['aqueous_fluid']]

            if 'oil_fluid' in new_filters:
                # Filter by oil fluid only (e.g., "SO")
                df = df[df['oil_fluid'] == new_filters['oil_fluid']]

            if 'dfu' in new_filters:
                df = df[df['dfu_row'] == new_filters['dfu']]

            self.session_state['last_filtered_df'] = df
            new_count = len(df)

            # Show filtering effect
            if new_count < original_count:
                print()
                print(f"Progressive filter applied: {original_count} -> {new_count} measurements")
                print()

        # Show available next steps
        # DISABLED: User requested to remove the "Available parameters" section
        # self._suggest_available_parameters()

    def _cmd_remove_filter_parameter(self, parsed: Dict):
        """Remove a parameter from existing session filters."""
        value = parsed['value']

        # Detect what type of parameter to remove
        detected = self._detect_parameter_type(value)

        if detected['type'] == 'unknown':
            print()
            print(f"[ERROR] Cannot determine parameter type for '{value}'")
            print()
            return

        # Map parameter types to filter keys
        filter_key_map = {
            'pressure': 'pressure',
            'flowrate': 'flowrate',
            'device': 'device',
            'fluid': 'fluid',
            'fluid_combination': 'fluid',
            'aqueous_fluid': 'aqueous_fluid',
            'oil_fluid': 'oil_fluid',
            'dfu': 'dfu',
            'device_type': 'device_type'
        }

        filter_key = filter_key_map.get(detected['type'])
        if not filter_key:
            print(f"[ERROR] Cannot remove parameter type: {detected['type']}")
            return

        # Check if this filter exists
        if filter_key not in self.session_state['current_filters']:
            print()
            print(f"[ERROR] No {detected['type']} filter is currently active")
            print()
            return

        # Remove the filter
        old_value = self.session_state['current_filters'].pop(filter_key)
        print()
        print(f"Removed {detected['type']} filter: {old_value}")
        print()

        # Re-run filter with remaining filters
        if self.session_state['current_filters']:
            filter_parsed = {
                'device_type': self.session_state['current_filters'].get('device_type'),
                'flowrate': self.session_state['current_filters'].get('flowrate'),
                'pressure': self.session_state['current_filters'].get('pressure')
            }
            self._cmd_filter(filter_parsed)
        else:
            print("All filters cleared.")
            print()

    def _cmd_undo_filter(self):
        """Remove the most recently added filter parameter."""
        if not self.session_state['current_filters']:
            print()
            print("No active filters to undo.")
            print()
            return

        # Remove the last added filter (based on order of addition)
        # Since dicts maintain insertion order in Python 3.7+, we can pop the last item
        if self.session_state['current_filters']:
            last_key = list(self.session_state['current_filters'].keys())[-1]
            last_value = self.session_state['current_filters'].pop(last_key)
            print()
            print(f"Removed last filter: {last_key} = {last_value}")
            print()

            # Re-run filter with remaining filters
            if self.session_state['current_filters']:
                filter_parsed = {
                    'device_type': self.session_state['current_filters'].get('device_type'),
                    'flowrate': self.session_state['current_filters'].get('flowrate'),
                    'pressure': self.session_state['current_filters'].get('pressure')
                }
                self._cmd_filter(filter_parsed)
            else:
                print("All filters cleared.")
                print()

    def _cmd_export_csv(self):
        """Export currently filtered data to CSV."""
        # Start with full dataset
        filtered = self.df.copy()

        # Apply session state filters
        filters = self.session_state['current_filters']

        # Apply device_type filter
        if 'device_type' in filters:
            filtered = filtered[filtered['device_type'] == filters['device_type']]

        # Apply flowrate filter
        if 'flowrate' in filters:
            filtered = filtered[filtered['aqueous_flowrate'] == filters['flowrate']]

        # Apply pressure filter
        if 'pressure' in filters:
            filtered = filtered[filtered['oil_pressure'] == filters['pressure']]

        # Apply device filter
        if 'device' in filters:
            filtered = filtered[filtered['device_id'] == filters['device']]

        # Apply fluid filters
        if 'fluid' in filters:
            fluid_value = filters['fluid']
            if '_' in fluid_value:
                # It's a combination like "SDS_SO"
                aq, oil = fluid_value.split('_')
                filtered = filtered[(filtered['aqueous_fluid'] == aq) & (filtered['oil_fluid'] == oil)]
            else:
                # Check both aqueous and oil fluid columns
                filtered = filtered[
                    (filtered['aqueous_fluid'] == fluid_value) |
                    (filtered['oil_fluid'] == fluid_value)
                ]

        if 'aqueous_fluid' in filters:
            filtered = filtered[filtered['aqueous_fluid'] == filters['aqueous_fluid']]

        if 'oil_fluid' in filters:
            filtered = filtered[filtered['oil_fluid'] == filters['oil_fluid']]

        # Apply DFU filter
        if 'dfu' in filters:
            filtered = filtered[filtered['dfu_row'] == filters['dfu']]

        # Apply exclusions and outlier detection
        filtered, removal_info = self._apply_exclusions(filtered)

        # Check if there's data to export
        if len(filtered) == 0:
            print()
            print("[ERROR] No data to export. Current filters return 0 measurements.")
            print()
            return

        # Generate filename
        filename = self._generate_export_filename()

        # Ensure outputs directory exists
        output_dir = Path('outputs')
        output_dir.mkdir(exist_ok=True)

        # Save to CSV
        output_path = output_dir / filename
        filtered.to_csv(output_path, index=False)

        # Store in session state for plotws command
        self.session_state['last_exported_csv'] = str(output_path)

        # User feedback
        print()
        print(f"[OK] Exported {len(filtered)} measurements to:")
        print(f"  {output_path.absolute()}")
        print()

        # Column summary
        unique_devices = filtered['device_id'].nunique()
        flow_params = filtered[['aqueous_flowrate', 'oil_pressure']].drop_duplicates()

        # Handle date range
        date_col = pd.to_datetime(filtered['testing_date'], errors='coerce')
        date_col_clean = date_col.dropna()
        if len(date_col_clean) > 0:
            date_range = f"{date_col_clean.min().strftime('%Y-%m-%d')} to {date_col_clean.max().strftime('%Y-%m-%d')}"
        else:
            date_range = "N/A"

        print("Export summary:")
        print(f"  • {len(filtered)} measurements")
        print(f"  • {unique_devices} devices")
        print(f"  • {len(flow_params)} flow/pressure combinations")
        print(f"  • Date range: {date_range}")
        print()

    def _generate_export_filename(self) -> str:
        """Generate descriptive filename based on current filters."""
        filters = self.session_state['current_filters']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        parts = []
        if 'device_type' in filters:
            parts.append(filters['device_type'])
        if 'flowrate' in filters:
            parts.append(f"{filters['flowrate']}mlhr")
        if 'pressure' in filters:
            parts.append(f"{filters['pressure']}mbar")
        if 'aqueous_fluid' in filters:
            parts.append(filters['aqueous_fluid'])
        if 'fluid' in filters:
            parts.append(filters['fluid'])
        if 'device' in filters:
            parts.append(filters['device'])
        if 'dfu' in filters:
            parts.append(f"DFU{filters['dfu']}")

        if not parts:
            parts.append('all_data')

        return f"{'_'.join(parts)}_export_{timestamp}.csv"

    def _cmd_plotws_interactive(self):
        """Interactive plot config selection menu."""
        configs_dir = Path('configs/plots')

        if not configs_dir.exists():
            print()
            print("[ERROR] Plot configs directory not found: configs/plots/")
            print()
            return

        # Get all .json files
        config_files = list(configs_dir.glob('*.json'))

        if not config_files:
            print()
            print("[ERROR] No plot configurations found in configs/plots/")
            print()
            return

        # Check if we have a last exported CSV
        last_csv = self.session_state.get('last_exported_csv')
        if not last_csv:
            print()
            print("[ERROR] No exported CSV found. Please export data first:")
            print("  1. Apply filters")
            print("  2. Run 'export' command")
            print("  3. Then run 'plotws' to select a plot")
            print()
            return

        # Load config details
        configs = []
        for config_file in sorted(config_files):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    configs.append({
                        'name': config_file.stem,
                        'description': config.get('description', 'No description'),
                        'path': config_file
                    })
            except Exception:
                configs.append({
                    'name': config_file.stem,
                    'description': '(error loading config)',
                    'path': config_file
                })

        # Display menu
        print()
        print("=" * 70)
        print("SELECT PLOT TYPE")
        print("=" * 70)
        print()
        print(f"Using data: {Path(last_csv).name}")
        print()

        for idx, cfg in enumerate(configs, 1):
            print(f"  [{idx}] {cfg['name']}")
            print(f"      {cfg['description']}")
            print()

        print("  [0] Cancel")
        print()

        # Get user selection
        try:
            choice = input("Select plot [1-{}]: ".format(len(configs)))
            choice_num = int(choice)

            if choice_num == 0:
                print()
                print("Cancelled.")
                print()
                return

            if 1 <= choice_num <= len(configs):
                selected_config = configs[choice_num - 1]['name']
                print()
                self._cmd_plotws(selected_config)
            else:
                print()
                print("[ERROR] Invalid selection. Please choose 1-{}.".format(len(configs)))
                print()

        except (ValueError, EOFError):
            print()
            print("[ERROR] Invalid input.")
            print()

    def _cmd_plotws_list(self):
        """List available plot configurations."""
        configs_dir = Path('configs/plots')

        if not configs_dir.exists():
            print()
            print("[ERROR] Plot configs directory not found: configs/plots/")
            print()
            return

        # Get all .json files
        config_files = list(configs_dir.glob('*.json'))

        if not config_files:
            print()
            print("[ERROR] No plot configurations found in configs/plots/")
            print()
            return

        print()
        print("Available plot configurations:")
        print("-" * 70)

        for config_file in sorted(config_files):
            config_name = config_file.stem

            # Try to load and get description
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    description = config.get('description', 'No description')
                    print(f"  {config_name:30s} - {description}")
            except Exception:
                print(f"  {config_name:30s} - (error loading config)")

        print()
        print("Usage:")
        print("  plotws                - Interactive menu to select plot")
        print("  plotws <config_name>  - Generate plot using last exported CSV")
        print()
        print("Example workflow:")
        print("  1. export                    (export filtered data)")
        print("  2. plotws                    (opens menu)")
        print("  3. Select plot number")
        print()

    def _cmd_plotws(self, config_name: str):
        """Generate plot from config using last exported CSV."""
        from src.plot_from_config import plot_from_config, PlotConfigError

        # Check if we have a last exported CSV
        last_csv = self.session_state.get('last_exported_csv')

        if not last_csv:
            print()
            print("[ERROR] No exported CSV found. Please export data first:")
            print("  1. Apply filters (e.g., 'filter device_type W13')")
            print("  2. Run 'export' command")
            print("  3. Then run 'plotws <config_name>'")
            print()
            return

        csv_path = Path(last_csv)
        if not csv_path.exists():
            print()
            print(f"[ERROR] Last exported CSV no longer exists: {csv_path}")
            print("Please export data again with 'export' command.")
            print()
            return

        # Build config path
        config_path = Path(f'configs/plots/{config_name}.json')

        if not config_path.exists():
            print()
            print(f"[ERROR] Plot config not found: {config_name}")
            print()
            print("Available configs (run 'plotws list'):")

            configs_dir = Path('configs/plots')
            if configs_dir.exists():
                config_files = list(configs_dir.glob('*.json'))
                for cf in sorted(config_files):
                    print(f"  - {cf.stem}")
            print()
            return

        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_stem = csv_path.stem.replace('_export_', '_')  # Clean up export suffix
        output_filename = f"{config_name}_{csv_stem}_{timestamp}.png"
        output_path = Path('outputs/plots') / output_filename

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print()
        print(f"Generating plot...")
        print(f"  Config: {config_name}")
        print(f"  Data:   {csv_path.name}")

        try:
            # Generate plot
            plot_from_config(
                csv_path=str(csv_path),
                config_path=str(config_path),
                output_path=str(output_path)
            )

            print()
            print(f"[OK] Plot saved to:")
            print(f"  {output_path.absolute()}")
            print()
            print("To view the plot:")
            print(f"  start {output_path}")
            print()

        except PlotConfigError as e:
            print()
            print(f"[ERROR] Plot generation failed:")
            print(f"  {e}")
            print()

        except Exception as e:
            print()
            print(f"[ERROR] Unexpected error during plot generation:")
            print(f"  {e}")
            print()

    def _suggest_available_parameters(self):
        """Suggest available parameters that could be added to refine the current filter."""
        if self.session_state['last_filtered_df'] is None:
            return

        df = self.session_state['last_filtered_df']
        if len(df) == 0:
            return

        filters = self.session_state['current_filters']

        print()
        print("-" * 70)
        print("Available parameters to refine your filter:")
        print()

        # Show available pressures if not filtered
        if 'pressure' not in filters:
            pressures = sorted(df['oil_pressure'].dropna().unique())
            if len(pressures) > 1:
                pressure_str = ', '.join([str(int(p)) for p in pressures])
                print(f"  Pressures: {pressure_str}")

        # Show available flowrates if not filtered
        if 'flowrate' not in filters:
            flowrates = sorted(df['aqueous_flowrate'].dropna().unique())
            if len(flowrates) > 1:
                flowrate_str = ', '.join([str(int(f)) for f in flowrates])
                print(f"  Flowrates: {flowrate_str}")

        # Show available devices if not filtered
        if 'device' not in filters:
            devices = sorted(df['device_id'].dropna().unique())
            if len(devices) > 1:
                device_str = ', '.join([str(d) for d in devices[:10]])  # Limit to first 10
                if len(devices) > 10:
                    device_str += f" ... ({len(devices)} total)"
                print(f"  Devices: {device_str}")

        # Show available fluids if not filtered
        if 'fluid' not in filters:
            fluids = set()
            fluids.update(df['aqueous_fluid'].dropna().unique())
            fluids.update(df['oil_fluid'].dropna().unique())
            if len(fluids) > 1:
                fluid_str = ', '.join([str(f) for f in sorted(fluids)])
                print(f"  Fluids: {fluid_str}")

        # Show available DFU rows if not filtered
        if 'dfu' not in filters:
            dfus = sorted(df['dfu_row'].dropna().unique())
            if len(dfus) > 1:
                dfu_str = ', '.join([str(d) for d in dfus])
                print(f"  DFU rows: {dfu_str}")

        print()
        print("Type a value to add it as a filter (e.g., '300', 'W13_S2_R9', 'DFU1')")
        print("Or use 'show <value>' for explicit filtering")
        print("-" * 70)
        print()

    def _parse_exclusion_args(self, args_string: str) -> List[str]:
        """
        Parse space-separated exclusion arguments (Feature 2).

        Examples:
            "W13_S5_R14 DFU1" -> ['W13_S5_R14', 'DFU1']
            "DFU1" -> ['DFU1']
            "SDS_SO" -> ['SDS_SO']

        Args:
            args_string: Space-separated exclusion criteria

        Returns:
            List of exclusion terms
        """
        return args_string.strip().split()

    def _apply_exclusions(self, df: pd.DataFrame) -> tuple:
        """
        Apply outlier detection and manual exclusions (Feature 2).

        Returns:
            (filtered_df, removal_info_dict)
        """
        removal_info = {
            'outlier_removed': [],
            'manual_removed': [],
            'outlier_count': 0,
            'manual_count': 0
        }

        filtered = df.copy()
        original_count = len(filtered)

        # Apply outlier detection if enabled
        if self.session_state['outlier_detection_enabled']:
            # Only apply to droplet measurements (CSV files)
            droplet_mask = (filtered['file_type'] == 'csv') & (filtered['measurement_type'] == 'dfu_measure')
            droplet_data = filtered[droplet_mask]

            if len(droplet_data) > 0:
                # Detect outliers in droplet size
                outlier_mask = self.outlier_detector.detect_outliers(droplet_data['droplet_size_mean'].dropna())

                # Get summary
                outlier_summary = self.outlier_detector.get_outlier_summary(
                    droplet_data,
                    outlier_mask,
                    'droplet_size_mean'
                )

                # Track removals
                removal_info['outlier_removed'] = outlier_summary['details']
                removal_info['outlier_count'] = outlier_summary['outlier_count']

                # Remove outliers
                outlier_indices = [d['index'] for d in outlier_summary['details']]
                filtered = filtered.drop(outlier_indices)

        # Apply manual exclusions
        manual_removed_indices = []

        for exclusion in self.session_state['manual_exclusions']:
            terms = self._parse_exclusion_args(exclusion)

            for term in terms:
                term_upper = term.upper()

                # Check if it's a device ID pattern (contains underscore)
                if '_' in term:
                    # Device-specific exclusion
                    parts = term_upper.split('_')
                    if len(parts) >= 3:  # Full device ID like W13_S5_R14
                        # Exact match
                        mask = filtered['device_id'] == term_upper
                        manual_removed_indices.extend(filtered[mask].index.tolist())

                # Check if it's a DFU row pattern
                elif term_upper.startswith('DFU'):
                    try:
                        dfu_num = int(term_upper[3:])  # Extract number from DFU1, DFU2, etc.
                        mask = filtered['dfu_row'] == dfu_num
                        manual_removed_indices.extend(filtered[mask].index.tolist())
                    except:
                        pass

                # Check if it's a fluid type
                elif term_upper in ['SDS', 'NACAS', 'SO', 'SDS_SO', 'NACAS_SO']:
                    # Match against fluid columns
                    mask = (
                        (filtered['aqueous_fluid'] == term_upper) |
                        (filtered['oil_fluid'] == term_upper) |
                        (filtered['aqueous_fluid'].fillna('') + '_' + filtered['oil_fluid'].fillna('') == term_upper)
                    )
                    manual_removed_indices.extend(filtered[mask].index.tolist())

        # Remove duplicates and apply
        manual_removed_indices = list(set(manual_removed_indices))
        if manual_removed_indices:
            removal_info['manual_count'] = len(manual_removed_indices)
            # Get details before removing
            for idx in manual_removed_indices:
                if idx in filtered.index:
                    row = filtered.loc[idx]
                    removal_info['manual_removed'].append({
                        'device_id': row['device_id'],
                        'dfu_row': row.get('dfu_row', 'N/A'),
                        'value': row.get('droplet_size_mean', row.get('frequency_mean', 'N/A')),
                        'index': idx
                    })
            filtered = filtered.drop(manual_removed_indices, errors='ignore')

        # Store in session
        self.session_state['last_removed_by_outlier'] = removal_info['outlier_removed']
        self.session_state['last_removed_by_manual'] = removal_info['manual_removed']

        return filtered, removal_info

    def _display_removal_info(self, removal_info: Dict, original_count: int, final_count: int):
        """Display detailed removal information (Feature 2 - Critical TUI requirement)."""
        print()
        print("Data Filtering Summary:")
        print(f"  Original measurements: {original_count}")

        if removal_info['outlier_count'] > 0:
            pct = (removal_info['outlier_count'] / original_count * 100) if original_count > 0 else 0
            print(f"  Removed by outlier detection: {removal_info['outlier_count']} ({pct:.1f}%)")
            print(f"  Removed measurements:")
            for item in removal_info['outlier_removed'][:10]:  # Show first 10
                dfu_str = f"DFU{item['dfu_row']}" if item['dfu_row'] != 'N/A' else 'N/A'
                value = item['value']
                if pd.notna(value):
                    print(f"    • {item['device_id']} {dfu_str} ({value:.2f} µm)")
                else:
                    print(f"    • {item['device_id']} {dfu_str}")
            if len(removal_info['outlier_removed']) > 10:
                print(f"    ... and {len(removal_info['outlier_removed']) - 10} more")

        if removal_info['manual_count'] > 0:
            pct = (removal_info['manual_count'] / original_count * 100) if original_count > 0 else 0
            print(f"  Removed by manual exclusions: {removal_info['manual_count']} ({pct:.1f}%)")
            print(f"  Removed measurements:")
            for item in removal_info['manual_removed'][:10]:  # Show first 10
                dfu_str = f"DFU{item['dfu_row']}" if item['dfu_row'] != 'N/A' else 'N/A'
                value = item['value']
                if pd.notna(value):
                    print(f"    • {item['device_id']} {dfu_str} ({value:.2f} µm)")
                else:
                    print(f"    • {item['device_id']} {dfu_str}")
            if len(removal_info['manual_removed']) > 10:
                print(f"    ... and {len(removal_info['manual_removed']) - 10} more")

        print(f"  Final measurements: {final_count}")
        print()

    def _calculate_device_level_stats(self, df: pd.DataFrame) -> Dict:
        """
        Calculate per-device statistics for droplet size and frequency.

        Args:
            df: Filtered DataFrame

        Returns:
            Dict mapping device_id to stats: {device_id: {droplet_size: {mean, std, count}, frequency: {...}}}
        """
        device_stats = {}

        for device_id in sorted(df['device_id'].unique()):
            device_data = df[df['device_id'] == device_id]
            stats = {}

            # Droplet size stats
            droplet_data = device_data['droplet_size_mean'].dropna()
            if len(droplet_data) > 0:
                stats['droplet_size'] = {
                    'mean': droplet_data.mean(),
                    'std': droplet_data.std(),
                    'count': len(droplet_data)
                }

            # Frequency stats
            freq_data = device_data['frequency_mean'].dropna()
            if len(freq_data) > 0:
                stats['frequency'] = {
                    'mean': freq_data.mean(),
                    'std': freq_data.std(),
                    'count': len(freq_data)
                }

            if stats:  # Only add if we have at least one type of data
                device_stats[device_id] = stats

        return device_stats

    def _count_complete_analyses(self, df: pd.DataFrame) -> Dict:
        """
        Count complete vs partial analyses by experimental condition.

        Args:
            df: DataFrame to analyze

        Returns:
            Dict with counts: {complete_droplet: N, complete_freq: N, partial: N, details: List}
        """
        # Group by experimental condition (device_id, testing_date, flow parameters, fluids)
        # dropna=False ensures devices with missing testing_date are included
        condition_groups = df.groupby([
            'device_id', 'testing_date', 'aqueous_flowrate', 'oil_pressure',
            'aqueous_fluid', 'oil_fluid'
        ], dropna=False)

        complete_droplet = 0
        complete_freq = 0
        partial = 0
        analysis_details = []

        for condition, group in condition_groups:
            device_id, test_date, flowrate, pressure, aq_fluid, oil_fluid = condition

            # Count droplet analyses (CSV files with DFU measurements)
            droplet_files = group[
                (group['measurement_type'] == 'dfu_measure') &
                (group['file_type'] == 'csv') &
                (pd.notna(group['dfu_row']))
            ]
            unique_dfu_rows = droplet_files['dfu_row'].nunique()

            # Count frequency analyses (TXT files)
            freq_files = group[
                (group['measurement_type'] == 'freq_analysis') &
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
            if unique_dfu_rows > 0:
                status_parts.append(f"{unique_dfu_rows} DFU rows")

            if has_freq_data:
                freq_count = len(freq_files)
                status_parts.append(f"{freq_count} frequency measurements")

            status = ", ".join(status_parts) if status_parts else "no data"

            analysis_details.append({
                'condition': condition_str,
                'status': status,
                'dfu_rows': unique_dfu_rows,
                'has_freq': has_freq_data,
                'freq_count': len(freq_files) if has_freq_data else 0,
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
