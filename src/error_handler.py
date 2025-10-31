"""
Context-Aware Error Message Builder

Provides actionable error messages with suggestions and context.
Helps users understand what went wrong and how to fix it.
"""

from typing import List, Dict, Set, Optional
import difflib
import pandas as pd


class ErrorMessageBuilder:
    """
    Builds context-aware error messages with actionable suggestions.

    Features:
    - Fuzzy matching for typos (Levenshtein distance)
    - Show available options for each entity type
    - Explain what was attempted and why it failed
    - Provide specific correction suggestions
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with current data for context.

        Args:
            df: Current DataFrame to extract valid options from
        """
        self.df = df
        self._cache_valid_options()

    def _cache_valid_options(self):
        """Cache valid options for quick lookup."""
        self.valid_device_types = set(self.df['device_type'].dropna().unique())
        self.valid_device_ids = set(self.df['device_id'].dropna().unique())
        self.valid_flowrates = set(self.df['aqueous_flowrate'].dropna().unique())
        self.valid_pressures = set(self.df['oil_pressure'].dropna().unique())
        self.valid_fluids = set()

        # Collect all fluid combinations
        for col in ['aqueous_fluid', 'oil_fluid']:
            if col in self.df.columns:
                self.valid_fluids.update(self.df[col].dropna().unique())

    def suggest_similar(self, query_value: str, available_options: List[str], max_suggestions: int = 3) -> List[str]:
        """
        Find similar options using fuzzy matching.

        Args:
            query_value: What user entered
            available_options: Valid options to match against
            max_suggestions: Maximum suggestions to return

        Returns:
            List of similar options, sorted by similarity
        """
        if not available_options:
            return []

        # Convert to strings and lowercase for comparison
        query_lower = str(query_value).lower()
        options_str = [str(opt) for opt in available_options]

        # Use difflib for fuzzy matching
        matches = difflib.get_close_matches(
            query_lower,
            [opt.lower() for opt in options_str],
            n=max_suggestions,
            cutoff=0.4  # 40% similarity threshold
        )

        # Map back to original case
        suggestions = []
        for match in matches:
            for original in options_str:
                if original.lower() == match:
                    suggestions.append(original)
                    break

        return suggestions

    def get_device_type_error(self, invalid_device_type: str) -> str:
        """Generate error message for invalid device type."""
        suggestions = self.suggest_similar(invalid_device_type, list(self.valid_device_types))

        message = f"Device type '{invalid_device_type}' not found."

        if suggestions:
            message += f" Did you mean: {', '.join(suggestions)}?"

        message += f"\n\nAvailable device types: {', '.join(sorted(self.valid_device_types))}"

        return message

    def get_device_id_error(self, invalid_device_id: str) -> str:
        """Generate error message for invalid device ID."""
        suggestions = self.suggest_similar(invalid_device_id, list(self.valid_device_ids))

        message = f"Device ID '{invalid_device_id}' not found."

        if suggestions:
            message += f" Did you mean: {', '.join(suggestions)}?"

        # Group device IDs by type for better organization
        device_groups = {}
        for device_id in self.valid_device_ids:
            device_type = device_id.split('_')[0] if '_' in device_id else 'Unknown'
            if device_type not in device_groups:
                device_groups[device_type] = []
            device_groups[device_type].append(device_id)

        message += "\n\nAvailable devices:"
        for device_type, devices in sorted(device_groups.items()):
            message += f"\n  {device_type}: {', '.join(sorted(devices))}"

        return message

    def get_flowrate_error(self, invalid_flowrate: str, device_type: str = None) -> str:
        """Generate error message for invalid flow rate."""
        available_flowrates = list(self.valid_flowrates)

        # If device type specified, show only flowrates tested for that device type
        if device_type:
            device_data = self.df[self.df['device_type'] == device_type]
            available_flowrates = list(device_data['aqueous_flowrate'].dropna().unique())

        suggestions = self.suggest_similar(str(invalid_flowrate), [str(f) for f in available_flowrates])

        context = f" for {device_type}" if device_type else ""
        message = f"Flow rate '{invalid_flowrate}ml/hr' not found{context}."

        if suggestions:
            suggestion_str = ', '.join([f"{s}ml/hr" for s in suggestions])
            message += f" Did you mean: {suggestion_str}?"

        flowrate_str = ', '.join([f"{f}ml/hr" for f in sorted(available_flowrates)])
        message += f"\n\nAvailable flow rates{context}: {flowrate_str}"

        return message

    def get_pressure_error(self, invalid_pressure: str, device_type: str = None) -> str:
        """Generate error message for invalid pressure."""
        available_pressures = list(self.valid_pressures)

        # If device type specified, show only pressures tested for that device type
        if device_type:
            device_data = self.df[self.df['device_type'] == device_type]
            available_pressures = list(device_data['oil_pressure'].dropna().unique())

        suggestions = self.suggest_similar(str(invalid_pressure), [str(p) for p in available_pressures])

        context = f" for {device_type}" if device_type else ""
        message = f"Pressure '{invalid_pressure}mbar' not found{context}."

        if suggestions:
            suggestion_str = ', '.join([f"{s}mbar" for s in suggestions])
            message += f" Did you mean: {suggestion_str}?"

        pressure_str = ', '.join([f"{p}mbar" for p in sorted(available_pressures)])
        message += f"\n\nAvailable pressures{context}: {pressure_str}"

        return message

    def get_no_data_error(self, filters: Dict) -> str:
        """Generate error message when no data matches filters."""
        message = "No data found matching your criteria."

        # Explain what was searched for
        filter_parts = []
        if 'device_type' in filters:
            filter_parts.append(f"device type '{filters['device_type']}'")
        if 'flowrate' in filters:
            filter_parts.append(f"flow rate {filters['flowrate']}ml/hr")
        if 'pressure' in filters:
            filter_parts.append(f"pressure {filters['pressure']}mbar")

        if filter_parts:
            message += f"\n\nSearched for: {', '.join(filter_parts)}"

        # Suggest alternatives
        message += "\n\nSuggestions:"

        # Check what's available for partial matches
        if 'device_type' in filters:
            device_type = filters['device_type']
            device_data = self.df[self.df['device_type'] == device_type]

            if len(device_data) == 0:
                message += f"\n  • No data found for {device_type} devices"
                message += f"\n  • Available device types: {', '.join(sorted(self.valid_device_types))}"
            else:
                # Show what parameters are available for this device type
                available_flowrates = sorted(device_data['aqueous_flowrate'].dropna().unique())
                available_pressures = sorted(device_data['oil_pressure'].dropna().unique())

                if 'flowrate' in filters and filters['flowrate'] not in available_flowrates:
                    flowrate_str = ', '.join([f"{f}ml/hr" for f in available_flowrates])
                    message += f"\n  • {device_type} available at: {flowrate_str}"

                if 'pressure' in filters and filters['pressure'] not in available_pressures:
                    pressure_str = ', '.join([f"{p}mbar" for p in available_pressures])
                    message += f"\n  • {device_type} tested at: {pressure_str}"

        return message

    def get_command_not_found_error(self, command: str) -> str:
        """Generate error message for unrecognized commands."""
        # Common command patterns
        common_commands = [
            'show w13', 'show w14', 'show w13 at 5mlhr',
            'stats w13', 'list devices', 'list params',
            'plot w13', 'graph w13', 'clear filters'
        ]

        suggestions = self.suggest_similar(command, common_commands)

        message = f"Command '{command}' not recognized."

        if suggestions:
            message += f" Did you mean:\n"
            for suggestion in suggestions:
                message += f"  • {suggestion}\n"

        message += "\nType 'help' for available commands or try natural language like:"
        message += "\n  • Compare W13 and W14 devices"
        message += "\n  • Show me W13 devices at 5ml/hr"
        message += "\n  • Plot droplet sizes for W13"

        return message

    def format_error_with_context(self, error_type: str, details: Dict) -> str:
        """
        Format error message with full context and recovery suggestions.

        Args:
            error_type: Type of error (device_type, flowrate, no_data, etc.)
            details: Error details and context

        Returns:
            Formatted error message
        """
        if error_type == 'device_type':
            return self.get_device_type_error(details['value'])

        elif error_type == 'device_id':
            return self.get_device_id_error(details['value'])

        elif error_type == 'flowrate':
            return self.get_flowrate_error(
                details['value'],
                details.get('device_type')
            )

        elif error_type == 'pressure':
            return self.get_pressure_error(
                details['value'],
                details.get('device_type')
            )

        elif error_type == 'no_data':
            return self.get_no_data_error(details.get('filters', {}))

        elif error_type == 'command_not_found':
            return self.get_command_not_found_error(details['command'])

        else:
            return f"An error occurred: {details.get('message', 'Unknown error')}"

    def get_recovery_suggestions(self, error_type: str, context: Dict) -> List[str]:
        """
        Get specific recovery suggestions based on error context.

        Returns:
            List of actionable suggestions
        """
        suggestions = []

        if error_type == 'no_data':
            suggestions.extend([
                "Try removing some filters with 'clear filters'",
                "Check available devices with 'list devices'",
                "View all parameters with 'list params'",
                "Use 'show filters' to see current active filters"
            ])

        elif error_type in ['device_type', 'device_id']:
            suggestions.extend([
                "Use 'list devices' to see all available devices",
                "Try 'show w13' or 'show w14' for common device types"
            ])

        elif error_type in ['flowrate', 'pressure']:
            suggestions.extend([
                "Use 'list params' to see all tested parameters",
                "Try common values like 5mlhr, 15mlhr, 200mbar, 300mbar"
            ])

        return suggestions