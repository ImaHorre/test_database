"""
Query Router

Coordinates routing of natural language queries to appropriate handler classes.
"""

from typing import Dict, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from ..analyst import DataAnalyst

from .list_handler import ListQueryHandler
from .filter_handler import FilterQueryHandler
from .compare_handler import CompareQueryHandler
from .analyze_handler import AnalyzeQueryHandler
from .track_handler import TrackQueryHandler
from .plot_handler import PlotQueryHandler
from .dfu_handler import DFUQueryHandler
from .report_handler import ReportQueryHandler

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Routes natural language query intents to appropriate handler classes.

    Maintains a registry of handler instances and delegates query processing
    based on the detected intent type.
    """

    def __init__(self, analyst: 'DataAnalyst'):
        """
        Initialize query router with handler instances.

        Args:
            analyst: DataAnalyst instance to pass to handlers
        """
        self.analyst = analyst

        # Initialize all handlers
        self.handlers = {
            'list': ListQueryHandler(analyst),
            'filter': FilterQueryHandler(analyst),
            'compare': CompareQueryHandler(analyst),
            'analyze': AnalyzeQueryHandler(analyst),
            'track': TrackQueryHandler(analyst),
            'plot': PlotQueryHandler(analyst),
            'plot_dfu': DFUQueryHandler(analyst),
            'report': ReportQueryHandler(analyst),
        }

        logger.debug(f"QueryRouter initialized with {len(self.handlers)} handlers")

    def route(self, intent, **kwargs) -> Dict:
        """
        Route a query intent to the appropriate handler.

        Args:
            intent: QueryIntent object with parsed query information
            **kwargs: Additional parameters to pass to handlers (e.g., live_preview)

        Returns:
            Dictionary with query results from the appropriate handler

        Raises:
            ValueError: If intent type is not recognized
        """
        intent_type = getattr(intent, 'intent_type', None)

        if not intent_type:
            logger.error("Intent object missing intent_type attribute")
            return self._format_router_error("Invalid intent: missing intent type")

        if intent_type not in self.handlers:
            logger.warning(f"Unknown intent type: {intent_type}")
            return self._format_router_error(
                f"Unknown query type '{intent_type}'. "
                f"Available types: {', '.join(self.handlers.keys())}"
            )

        handler = self.handlers[intent_type]
        logger.debug(f"Routing {intent_type} query to {handler.__class__.__name__}")

        try:
            # Handle special case for DFU handler which takes additional parameters
            if intent_type == 'plot_dfu':
                live_preview = kwargs.get('live_preview', True)
                return handler.handle(intent, live_preview=live_preview)
            else:
                return handler.handle(intent)

        except Exception as e:
            logger.error(f"Handler {handler.__class__.__name__} failed", exc_info=e)
            return self._format_router_error(
                f"Query processing failed: {str(e)}",
                intent_type=intent_type
            )

    def get_available_intents(self) -> list:
        """
        Get list of available intent types.

        Returns:
            List of supported intent type strings
        """
        return list(self.handlers.keys())

    def get_handler(self, intent_type: str):
        """
        Get handler instance for a specific intent type.

        Args:
            intent_type: The intent type string

        Returns:
            Handler instance or None if not found
        """
        return self.handlers.get(intent_type)

    def _format_router_error(self, message: str, **kwargs) -> Dict:
        """
        Format error responses from the router level.

        Args:
            message: Error message
            **kwargs: Additional context fields

        Returns:
            Formatted error dictionary
        """
        response = {
            'status': 'error',
            'intent': kwargs.get('intent_type', 'unknown'),
            'message': message,
            'router_error': True
        }

        for key, value in kwargs.items():
            if key not in response:
                response[key] = value

        return response