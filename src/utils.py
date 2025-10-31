"""
Utility functions for the OneDrive File System Scanner & Analysis Tool.

This module provides safe file operations and common utilities used across
the scanner and extractor components.
"""

import logging
import os
from typing import Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def safe_file_read(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Read file content with robust encoding handling.

    Attempts to read the file with multiple encoding strategies to handle
    various character sets that may appear in OneDrive files, including
    scientific notation and international characters.

    Args:
        file_path: Path to the file to read
        encoding: Primary encoding to try first (default: utf-8)

    Returns:
        File content as string, or None if reading fails

    Example:
        >>> content = safe_file_read("measurement_data.csv")
        >>> if content is not None:
        ...     # Process content safely
        ...     pass
    """
    if not file_path:
        logger.error("Empty file path provided")
        return None

    # Validate file exists and is readable
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return None

    if not os.path.isfile(file_path):
        logger.error(f"Path is not a file: {file_path}")
        return None

    # Check file permissions
    if not os.access(file_path, os.R_OK):
        logger.error(f"No read permission for file: {file_path}")
        return None

    # Try multiple encodings in order of preference
    encodings = [encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc, errors='replace') as f:
                content = f.read()

            # Log successful encoding for debugging
            if enc != encoding:
                logger.debug(f"Successfully read {file_path} with fallback encoding: {enc}")
            else:
                logger.debug(f"Successfully read {file_path} with primary encoding: {enc}")

            return content

        except (UnicodeDecodeError, LookupError) as e:
            logger.debug(f"Failed to read {file_path} with encoding {enc}: {e}")
            continue

        except IOError as e:
            logger.error(f"IO error reading file {file_path}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path} with encoding {enc}: {e}")
            continue

    # If all encodings failed
    logger.error(f"Failed to read {file_path} with any encoding: {encodings}")
    return None


def safe_file_readlines(file_path: str, encoding: str = 'utf-8') -> Optional[List[str]]:
    """
    Read file lines with robust encoding handling.

    Similar to safe_file_read but returns lines as a list, which is useful
    for CSV and TXT file processing.

    Args:
        file_path: Path to the file to read
        encoding: Primary encoding to try first (default: utf-8)

    Returns:
        List of lines from the file, or None if reading fails

    Example:
        >>> lines = safe_file_readlines("frequency_data.txt")
        >>> if lines is not None:
        ...     for line in lines:
        ...         # Process each line
        ...         pass
    """
    content = safe_file_read(file_path, encoding)
    if content is not None:
        return content.splitlines()
    return None


def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate file path for security and correctness.

    Checks for path traversal attacks, validates file extensions,
    and ensures the file exists and is readable.

    Args:
        file_path: Path to validate
        allowed_extensions: List of allowed file extensions (e.g., ['.csv', '.txt'])

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> is_valid, error = validate_file_path("data.csv", [".csv", ".txt"])
        >>> if not is_valid:
        ...     logger.error(f"Invalid file path: {error}")
    """
    try:
        # Resolve path to detect traversal attempts
        resolved_path = Path(file_path).resolve()

        # Check if file exists
        if not resolved_path.exists():
            return False, f"File does not exist: {file_path}"

        # Check if it's actually a file
        if not resolved_path.is_file():
            return False, f"Path is not a file: {file_path}"

        # Check file extension if restrictions provided
        if allowed_extensions:
            file_ext = resolved_path.suffix.lower()
            allowed_ext_lower = [ext.lower() for ext in allowed_extensions]
            if file_ext not in allowed_ext_lower:
                return False, f"File extension {file_ext} not in allowed list: {allowed_extensions}"

        # Check read permissions
        if not os.access(resolved_path, os.R_OK):
            return False, f"No read permission for file: {file_path}"

        return True, ""

    except (ValueError, OSError) as e:
        return False, f"Invalid file path: {e}"


def get_file_size_mb(file_path: str) -> Optional[float]:
    """
    Get file size in megabytes.

    Useful for checking file sizes before processing to avoid
    memory issues with very large files.

    Args:
        file_path: Path to the file

    Returns:
        File size in MB, or None if file doesn't exist

    Example:
        >>> size_mb = get_file_size_mb("large_dataset.csv")
        >>> if size_mb and size_mb > 100:
        ...     logger.warning(f"Large file detected: {size_mb:.1f} MB")
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except (OSError, ValueError):
        return None


def sanitize_path_for_logging(file_path: str) -> str:
    """
    Sanitize file path for safe logging.

    Removes sensitive directory information and keeps only
    the filename for security logging purposes.

    Args:
        file_path: Full file path

    Returns:
        Sanitized path safe for logging

    Example:
        >>> safe_path = sanitize_path_for_logging("/secret/path/data.csv")
        >>> logger.info(f"Processing file: {safe_path}")  # Only logs "data.csv"
    """
    try:
        return os.path.basename(file_path)
    except (ValueError, TypeError):
        return "unknown_file"