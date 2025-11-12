"""
Compare Query Handler

Handles "compare" intent queries for device comparisons and analysis.
"""

from typing import Dict
from datetime import datetime
from .base_handler import QueryHandler
import logging

logger = logging.getLogger(__name__)


class CompareQueryHandler(QueryHandler):
    """
    Handler for compare-type queries.

    Processes queries like:
    - "compare W13 devices"
    - "compare devices at same parameters"
    - "compare W13 and W14 performance"
    """

    def handle(self, intent) -> Dict:
        """
        Handle 'compare' intent queries.

        Args:
            intent: QueryIntent object with parsed query and entities

        Returns:
            Dictionary with comparison results and plot path
        """
        try:
            # Generate output path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"outputs/analyst/plots/nl_query_compare_{timestamp}.png"

            # Extract parameters from entities
            device_type = intent.entities.get('device_type')
            flowrate = intent.entities.get('flowrate')
            pressure = intent.entities.get('pressure')

            # Call appropriate comparison method
            result = self.analyst.compare_devices_at_same_parameters(
                device_type=device_type,
                aqueous_flowrate=flowrate,
                oil_pressure=pressure,
                output_path=output_path
            )

            # Format the message
            message = f"Comparison complete! Found {len(result)} devices.\n\n"
            if device_type:
                message += f"Device type: {device_type}\n"
            if flowrate:
                message += f"Flowrate: {flowrate} ml/hr\n"
            if pressure:
                message += f"Pressure: {pressure} mbar\n"

            return self._format_success(
                message=message,
                result=result,
                intent=intent,
                plot_path=output_path,
                devices_compared=len(result),
                device_type=device_type,
                flowrate=flowrate,
                pressure=pressure
            )

        except Exception as e:
            return self._format_error(
                message="Failed to perform device comparison.",
                error=e,
                intent=intent
            )