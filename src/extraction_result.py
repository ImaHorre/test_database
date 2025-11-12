"""
Structured result objects for metadata extraction operations.

This module provides consistent result handling for the extractor component,
eliminating silent failures and providing detailed feedback to users.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """
    Structured result from metadata extraction operations.

    Replaces simple Dict/None returns with rich result information
    that includes success status, error details, and user feedback.
    """

    success: bool
    metadata: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    parse_quality: str = 'unknown'
    file_path: Optional[str] = None

    def add_warning(self, message: str, context: Optional[str] = None):
        """
        Add a warning message.

        Args:
            message: Warning description
            context: Optional additional context
        """
        full_message = f"{message}"
        if context:
            full_message += f" ({context})"
        self.warnings.append(full_message)
        logger.warning(full_message)

    def add_error(self, message: str, context: Optional[str] = None):
        """
        Add an error message and mark result as failed.

        Args:
            message: Error description
            context: Optional additional context
        """
        full_message = f"{message}"
        if context:
            full_message += f" ({context})"
        self.errors.append(full_message)
        self.success = False
        logger.error(full_message)

    def set_quality(self, quality: str):
        """
        Set the parse quality level.

        Args:
            quality: One of 'complete', 'partial', 'minimal', 'failed'
        """
        valid_qualities = ['complete', 'partial', 'minimal', 'failed']
        if quality not in valid_qualities:
            self.add_warning(f"Invalid quality level '{quality}', using 'unknown'")
            quality = 'unknown'
        self.parse_quality = quality

    def get_user_message(self) -> str:
        """
        Generate user-friendly feedback message.

        Returns:
            Formatted message suitable for display to users
        """
        messages = []

        if self.success:
            # Success message with quality indicator
            quality_icons = {
                'complete': '✓',
                'partial': '⚠',
                'minimal': '⚠',
                'unknown': '?'
            }
            icon = quality_icons.get(self.parse_quality, '?')

            quality_descriptions = {
                'complete': 'All metadata extracted successfully',
                'partial': 'Some metadata missing but usable',
                'minimal': 'Limited metadata available - check file naming',
                'unknown': 'Extraction completed with unknown quality'
            }
            desc = quality_descriptions.get(self.parse_quality, 'Extraction completed')

            messages.append(f"{icon} {desc}")

            # Add warnings if any
            if self.warnings:
                messages.append("\nWarnings:")
                for warning in self.warnings:
                    messages.append(f"  • {warning}")

        else:
            # Failure message
            messages.append("❌ Extraction failed")

            if self.errors:
                messages.append("\nErrors:")
                for error in self.errors:
                    messages.append(f"  • {error}")

            if self.warnings:
                messages.append("\nWarnings:")
                for warning in self.warnings:
                    messages.append(f"  • {warning}")

            # Add context-specific suggestions
            suggestions = self._generate_suggestions()
            if suggestions:
                messages.append("\nSuggestions:")
                for suggestion in suggestions:
                    messages.append(f"  • {suggestion}")

        return "\n".join(messages)

    def _generate_suggestions(self) -> List[str]:
        """
        Generate context-specific suggestions based on errors.

        Returns:
            List of helpful suggestions for the user
        """
        suggestions = []
        error_text = " ".join(self.errors).lower()

        if 'device' in error_text or 'device_id' in error_text:
            suggestions.append("Check device ID format: W13_S1_R4 (Wafer_Shim_Replica)")

        if 'date' in error_text:
            suggestions.append("Check date format: DDMMYYYY (25092025) or DDMM (2509)")

        if 'fluid' in error_text:
            suggestions.append("Check fluid format: AqueousFluid_OilFluid (SDS_SO, NaCas_SO)")

        if 'flow' in error_text or 'parameter' in error_text:
            suggestions.append("Check flow format: XmlhrYmbar (5mlhr500mbar)")

        if 'encoding' in error_text or 'unicode' in error_text:
            suggestions.append("File may contain special characters - check file encoding")

        if 'permission' in error_text or 'access' in error_text:
            suggestions.append("Check file permissions and OneDrive sync status")

        if not suggestions and self.errors:
            suggestions.append("Check file/folder naming follows expected conventions")

        return suggestions

    def get_metadata_or_empty(self) -> Dict[str, Any]:
        """
        Get metadata dict, returning empty dict if None.

        Useful for safe access when partial results are acceptable.

        Returns:
            Metadata dict or empty dict if extraction failed
        """
        return self.metadata if self.metadata is not None else {}

    def is_usable(self) -> bool:
        """
        Check if result is usable despite warnings.

        Returns True if either:
        - Completely successful
        - Partial success with some metadata extracted

        Returns:
            True if result can be used, False if it should be discarded
        """
        return self.success and self.metadata is not None and bool(self.metadata)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary for logging/serialization.

        Returns:
            Dictionary representation of the result
        """
        return {
            'success': self.success,
            'metadata': self.metadata,
            'warnings': self.warnings,
            'errors': self.errors,
            'parse_quality': self.parse_quality,
            'file_path': self.file_path,
            'usable': self.is_usable()
        }

    @classmethod
    def success_result(cls, metadata: Dict[str, Any], quality: str = 'complete',
                      file_path: Optional[str] = None) -> 'ExtractionResult':
        """
        Create a successful extraction result.

        Args:
            metadata: Extracted metadata dictionary
            quality: Parse quality level
            file_path: Optional file path for context

        Returns:
            ExtractionResult with success=True
        """
        result = cls(success=True, metadata=metadata, file_path=file_path)
        result.set_quality(quality)
        return result

    @classmethod
    def failure_result(cls, error_message: str, file_path: Optional[str] = None) -> 'ExtractionResult':
        """
        Create a failed extraction result.

        Args:
            error_message: Description of the failure
            file_path: Optional file path for context

        Returns:
            ExtractionResult with success=False
        """
        result = cls(success=False, file_path=file_path)
        result.add_error(error_message)
        result.set_quality('failed')
        return result

    @classmethod
    def partial_result(cls, metadata: Dict[str, Any], warnings: List[str],
                      quality: str = 'partial', file_path: Optional[str] = None) -> 'ExtractionResult':
        """
        Create a partial success result.

        Args:
            metadata: Partially extracted metadata
            warnings: List of warning messages
            quality: Parse quality level
            file_path: Optional file path for context

        Returns:
            ExtractionResult with partial success
        """
        result = cls(success=True, metadata=metadata, file_path=file_path)
        result.warnings.extend(warnings)
        result.set_quality(quality)
        return result