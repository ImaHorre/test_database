"""
Plot Query Handler

Handles general "plot" intent queries and routes to appropriate plotting handlers.
"""

from typing import Dict
from .base_handler import QueryHandler
import logging

logger = logging.getLogger(__name__)


class PlotQueryHandler(QueryHandler):
    """
    Handler for general plot-type queries.

    Processes queries like:
    - "plot device performance"
    - "create a chart"
    - "visualize the data"

    Routes to more specific plotting handlers based on entities.
    """

    def handle(self, intent) -> Dict:
        """
        Handle 'plot' intent queries by routing to appropriate specific handlers.

        Args:
            intent: QueryIntent object with parsed query and entities

        Returns:
            Dictionary with plot results or clarification request
        """
        try:
            # Import other handlers for routing
            from .track_handler import TrackQueryHandler
            from .analyze_handler import AnalyzeQueryHandler
            from .compare_handler import CompareQueryHandler

            # Route to appropriate plot based on entities
            if 'device_id' in intent.entities:
                # Plot specific device over time
                track_handler = TrackQueryHandler(self.analyst)
                return track_handler.handle(intent)

            elif 'device_type' in intent.entities:
                if 'flowrate' in intent.entities or 'pressure' in intent.entities:
                    # Analyze flow parameter effects
                    analyze_handler = AnalyzeQueryHandler(self.analyst)
                    return analyze_handler.handle(intent)
                else:
                    # Compare devices of same type
                    compare_handler = CompareQueryHandler(self.analyst)
                    return compare_handler.handle(intent)

            else:
                return {
                    'status': 'clarification_needed',
                    'intent': 'plot',
                    'message': "What would you like to plot? Try specifying a device type, device ID, or parameters.",
                    'clarification': "Please provide more details for the plot",
                    'result': None
                }

        except Exception as e:
            return self._format_error(
                message="Failed to route plot query.",
                error=e,
                intent=intent
            )