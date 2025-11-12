"""
Base Query Handler Interface

Defines the abstract interface that all query handlers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from ..analyst import DataAnalyst

logger = logging.getLogger(__name__)


class QueryHandler(ABC):
    """
    Abstract base class for all query handlers.

    Each handler is responsible for processing a specific type of natural
    language query intent and returning structured results.
    """

    def __init__(self, analyst: 'DataAnalyst'):
        """
        Initialize query handler with analyst reference.

        Args:
            analyst: DataAnalyst instance for data access and operations
        """
        self.analyst = analyst

    @abstractmethod
    def handle(self, intent) -> Dict:
        """
        Process a query intent and return results.

        Args:
            intent: QueryIntent object with parsed query information

        Returns:
            Dictionary with query results, status, and metadata

        The returned dictionary should contain:
        - status: 'success' or 'error'
        - message: Human-readable result description
        - result: The actual data/analysis result (optional)
        - plot_path: Path to generated plot (if applicable)
        - metadata: Additional context information (optional)
        """
        pass

    def _format_success(self, message: str, result=None, **kwargs) -> Dict:
        """
        Helper to format successful query results.

        Args:
            message: Success message to display
            result: Data result (optional)
            **kwargs: Additional metadata fields

        Returns:
            Formatted success dictionary
        """
        response = {
            'status': 'success',
            'intent': getattr(kwargs.get('intent'), 'intent_type', 'unknown'),
            'message': message
        }

        if result is not None:
            response['result'] = result

        # Add any additional metadata
        for key, value in kwargs.items():
            if key not in response:
                response[key] = value

        return response

    def _format_error(self, message: str, error: Exception = None, **kwargs) -> Dict:
        """
        Helper to format error query results.

        Args:
            message: Error message to display
            error: Original exception (optional)
            **kwargs: Additional context fields

        Returns:
            Formatted error dictionary
        """
        response = {
            'status': 'error',
            'intent': getattr(kwargs.get('intent'), 'intent_type', 'unknown'),
            'message': message
        }

        if error:
            logger.error(f"Query handler error: {message}", exc_info=error)
            response['error_type'] = type(error).__name__

        # Add any additional context
        for key, value in kwargs.items():
            if key not in response:
                response[key] = value

        return response

    def _validate_entities(self, intent, required_entities: list) -> bool:
        """
        Validate that required entities are present in the intent.

        Args:
            intent: QueryIntent object
            required_entities: List of required entity names

        Returns:
            True if all required entities are present
        """
        entities = getattr(intent, 'entities', {})
        missing = [entity for entity in required_entities if entity not in entities]

        if missing:
            logger.warning(f"Missing required entities: {missing}")
            return False

        return True