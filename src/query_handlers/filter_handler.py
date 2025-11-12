"""
Filter Query Handler

Handles "filter" intent queries for filtering data by device type, parameters, etc.
"""

from typing import Dict
from .base_handler import QueryHandler
import logging

logger = logging.getLogger(__name__)


class FilterQueryHandler(QueryHandler):
    """
    Handler for filter-type queries.

    Processes queries like:
    - "show me W13 devices"
    - "filter by device type W14"
    - "show devices tested at 5ml/hr"
    """

    def handle(self, intent) -> Dict:
        """
        Handle 'filter' intent queries.

        Args:
            intent: QueryIntent object with parsed query and entities

        Returns:
            Dictionary with filtered data and applied filters
        """
        try:
            filtered_df = self.analyst.df.copy()
            applied_filters = {}

            # Apply filters from extracted entities
            if 'device_type' in intent.entities:
                device_type = intent.entities['device_type']
                filtered_df = filtered_df[filtered_df['device_type'] == device_type]
                applied_filters['device_type'] = device_type

            if 'flowrate' in intent.entities:
                flowrate = intent.entities['flowrate']
                filtered_df = filtered_df[filtered_df['aqueous_flowrate'] == flowrate]
                applied_filters['flowrate'] = f"{flowrate}ml/hr"

            if 'pressure' in intent.entities:
                pressure = intent.entities['pressure']
                filtered_df = filtered_df[filtered_df['oil_pressure'] == pressure]
                applied_filters['pressure'] = f"{pressure}mbar"

            if 'fluid' in intent.entities:
                # Check both aqueous and oil fluid columns
                fluid = intent.entities['fluid']
                fluid_mask = (
                    (filtered_df['aqueous_fluid'] == fluid) |
                    (filtered_df['oil_fluid'] == fluid)
                )
                filtered_df = filtered_df[fluid_mask]
                applied_filters['fluid'] = fluid

            # Format the message
            message = f"Found {len(filtered_df)} measurements matching your criteria.\n\n"
            if applied_filters:
                filter_list = [f"{k}={v}" for k, v in applied_filters.items()]
                message += f"Filters applied: {', '.join(filter_list)}"
            else:
                message += "No filters applied - showing all data."

            return self._format_success(
                message=message,
                result=filtered_df,
                intent=intent,
                applied_filters=applied_filters,
                total_matches=len(filtered_df)
            )

        except Exception as e:
            return self._format_error(
                message="Failed to filter data.",
                error=e,
                intent=intent
            )