"""
Report Query Handler

Handles "report" intent queries for generating summary reports.
"""

from typing import Dict
from datetime import datetime
from .base_handler import QueryHandler
import logging

logger = logging.getLogger(__name__)


class ReportQueryHandler(QueryHandler):
    """
    Handler for report-type queries.

    Processes queries like:
    - "generate summary report"
    - "create a report"
    - "summarize the data"
    """

    def handle(self, intent) -> Dict:
        """
        Handle 'report' intent queries.

        Args:
            intent: QueryIntent object with parsed query

        Returns:
            Dictionary with report generation results and file path
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"outputs/nl_query_report_{timestamp}.txt"

            self.analyst.generate_summary_report(output_path=output_path)

            message = f"Summary report generated!\n\nSaved to: {output_path}"

            return self._format_success(
                message=message,
                intent=intent,
                report_path=output_path,
                timestamp=timestamp
            )

        except Exception as e:
            return self._format_error(
                message="Failed to generate summary report.",
                error=e,
                intent=intent
            )