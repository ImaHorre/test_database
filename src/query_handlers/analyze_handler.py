"""
Analyze Query Handler

Handles "analyze" intent queries for flow parameter effects and correlations.
"""

from typing import Dict
from datetime import datetime
from .base_handler import QueryHandler
import logging

logger = logging.getLogger(__name__)


class AnalyzeQueryHandler(QueryHandler):
    """
    Handler for analyze-type queries.

    Processes queries like:
    - "analyze flow parameter effects for W13"
    - "analyze correlation between pressure and droplet size"
    - "analyze W14 device performance"
    """

    def handle(self, intent) -> Dict:
        """
        Handle 'analyze' intent queries.

        Args:
            intent: QueryIntent object with parsed query and entities

        Returns:
            Dictionary with analysis results and plot path
        """
        try:
            device_type = intent.entities.get('device_type')
            if not device_type:
                return {
                    'status': 'clarification_needed',
                    'intent': 'analyze',
                    'message': "Which device type would you like to analyze? (W13 or W14)",
                    'clarification': "Please specify a device type",
                    'result': None
                }

            # Determine parameter to analyze (flowrate or pressure)
            parameter = 'aqueous_flowrate' if 'flowrate' in intent.entities else 'oil_pressure'
            metric = intent.entities.get('metric', 'droplet_size_mean')

            # Generate output path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"outputs/analyst/plots/nl_query_analysis_{timestamp}.png"

            result = self.analyst.analyze_flow_parameter_effects(
                device_type=device_type,
                parameter=parameter,
                metric=metric,
                output_path=output_path
            )

            message = f"Analysis complete for {device_type}!\n\n"
            message += f"Parameter: {parameter}\n"
            message += f"Metric: {metric}\n"
            message += f"Correlation: {result['correlation']:.3f}\n"
            message += f"Total measurements: {result['total_measurements']}\n"

            return self._format_success(
                message=message,
                result=result,
                intent=intent,
                plot_path=output_path,
                device_type=device_type,
                parameter=parameter,
                metric=metric,
                correlation=result['correlation']
            )

        except Exception as e:
            return self._format_error(
                message="Failed to perform flow parameter analysis.",
                error=e,
                intent=intent
            )