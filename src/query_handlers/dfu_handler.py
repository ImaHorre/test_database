"""
DFU Query Handler

Handles "plot_dfu" intent queries for DFU-specific plotting (metric vs DFU row).
"""

from typing import Dict
from datetime import datetime
from .base_handler import QueryHandler
import logging

logger = logging.getLogger(__name__)


class DFUQueryHandler(QueryHandler):
    """
    Handler for DFU-specific plot queries.

    Processes queries like:
    - "show droplet size across all DFUs for W13 devices"
    - "plot DFU performance"
    - "across all measured DFUs"
    """

    def handle(self, intent, live_preview: bool = True) -> Dict:
        """
        Handle 'plot_dfu' intent queries - plot metric vs DFU rows.

        Args:
            intent: QueryIntent object with parsed query and entities
            live_preview: Whether to open interactive plot editor

        Returns:
            Dictionary with DFU plot results and metadata
        """
        try:
            # Extract parameters from intent
            device_type = intent.entities.get('device_type')
            flowrate = intent.entities.get('flowrate')
            pressure = intent.entities.get('pressure')
            metric = intent.entities.get('metric', 'droplet_size_mean')

            # Generate output path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"outputs/analyst/plots/nl_query_dfu_{timestamp}.png"

            # Call the DFU plotting method with query text for context detection
            result = self.analyst.plot_metric_vs_dfu(
                metric=metric,
                device_type=device_type,
                aqueous_flowrate=flowrate,
                oil_pressure=pressure,
                output_path=output_path,
                query_text=intent.raw_query,  # Pass original query for context detection
                live_preview=live_preview  # Enable live preview
            )

            # Build success message with varying parameters info
            message = f"DFU analysis complete!\n\n"
            message += f"Metric: {metric}\n"
            message += f"Found {result['num_devices']} device(s):\n"
            for device in result['devices']:
                message += f"  - {device}\n"
            message += f"\nDFU rows measured: {', '.join(map(str, result['dfu_rows_measured']))}\n"
            message += f"Total measurements: {result['total_measurements']}\n"

            # Show varying parameters if detected
            if result.get('varying_parameters'):
                message += f"\nVarying parameters detected: {', '.join(result['varying_parameters'])}\n"
                message += "(Legend includes context for differentiating devices)\n"

            message += f"\nFilters applied: {', '.join(result['filters'])}" if result['filters'] else ""

            return self._format_success(
                message=message,
                result=result,
                intent=intent,
                plot_path=output_path,
                metric=metric,
                device_type=device_type,
                flowrate=flowrate,
                pressure=pressure,
                num_devices=result['num_devices'],
                dfu_rows=result['dfu_rows_measured'],
                varying_parameters=result.get('varying_parameters', [])
            )

        except ValueError as e:
            # Handle case where no data found
            return self._format_error(
                message=f"Could not generate DFU plot: {str(e)}",
                error=e,
                intent=intent
            )
        except Exception as e:
            return self._format_error(
                message="Failed to create DFU plot.",
                error=e,
                intent=intent
            )