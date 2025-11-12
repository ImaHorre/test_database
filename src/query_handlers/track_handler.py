"""
Track Query Handler

Handles "track" intent queries for device history tracking over time.
"""

from typing import Dict
from datetime import datetime
from .base_handler import QueryHandler
import logging

logger = logging.getLogger(__name__)


class TrackQueryHandler(QueryHandler):
    """
    Handler for track-type queries.

    Processes queries like:
    - "track device W13_S1_R1 over time"
    - "track performance of W14_S2_R1"
    - "show device history for W13_S1_R2"
    """

    def handle(self, intent) -> Dict:
        """
        Handle 'track' intent queries.

        Args:
            intent: QueryIntent object with parsed query and entities

        Returns:
            Dictionary with tracking results and plot path
        """
        try:
            device_id = intent.entities.get('device_id')
            if not device_id:
                return {
                    'status': 'clarification_needed',
                    'intent': 'track',
                    'message': "Which device would you like to track? (e.g., W13_S1_R1)",
                    'clarification': "Please specify a device ID",
                    'result': None
                }

            # Generate output path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"outputs/analyst/plots/nl_query_track_{timestamp}.png"

            result = self.analyst.track_device_over_time(
                device_id=device_id,
                output_path=output_path
            )

            if len(result) == 0:
                return self._format_error(
                    message=f"No data found for device {device_id}",
                    intent=intent
                )

            message = f"Tracking results for {device_id}:\n\n"
            message += f"Total tests: {len(result)}\n"
            message += f"Date range: {result['testing_date'].min()} to {result['testing_date'].max()}\n"
            message += f"Mean droplet size: {result['droplet_size_mean'].mean():.2f} µm\n"

            return self._format_success(
                message=message,
                result=result,
                intent=intent,
                plot_path=output_path,
                device_id=device_id,
                total_tests=len(result),
                mean_droplet_size=float(result['droplet_size_mean'].mean())
            )

        except Exception as e:
            return self._format_error(
                message="Failed to track device over time.",
                error=e,
                intent=intent
            )