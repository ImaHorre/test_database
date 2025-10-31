"""
List Query Handler

Handles "list" intent queries for displaying available devices, device types, etc.
"""

from typing import Dict
from .base_handler import QueryHandler
import logging

logger = logging.getLogger(__name__)


class ListQueryHandler(QueryHandler):
    """
    Handler for list-type queries.

    Processes queries like:
    - "list all devices"
    - "show me device types"
    - "what devices are available"
    """

    def handle(self, intent) -> Dict:
        """
        Handle 'list' intent queries.

        Args:
            intent: QueryIntent object with parsed query

        Returns:
            Dictionary with list of available devices and metadata
        """
        try:
            # Group devices and get summary statistics
            devices = self.analyst.df.groupby('device_id').agg({
                'device_type': 'first',
                'testing_date': ['min', 'max'],
                'droplet_size_mean': 'count'
            }).reset_index()

            # Format the message
            message = "Available devices:\n\n"
            for _, row in devices.iterrows():
                device_id = row[('device_id', '')]
                device_type = row[('device_type', 'first')]
                count = row[('droplet_size_mean', 'count')]
                message += f"  - {device_id} ({device_type}) - {count} measurements\n"

            return self._format_success(
                message=message,
                result=devices,
                intent=intent,
                total_devices=len(devices),
                total_measurements=int(devices[('droplet_size_mean', 'count')].sum())
            )

        except Exception as e:
            return self._format_error(
                message="Failed to retrieve device list.",
                error=e,
                intent=intent
            )