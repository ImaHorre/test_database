"""
Specialized agents for local file system scanning and analysis.

Agents communicate with each other to create a complete data pipeline:
- Scanner: Discovers files and folders in local directories
- Extractor: Parses folder/file names to extract structured data
- CSVManager: Maintains the CSV database
- Analyst: Processes queries and generates insights
"""

from .scanner import LocalScanner
from .extractor import MetadataExtractor
from .csv_manager import CSVManager
from .analyst import DataAnalyst

__all__ = [
    'LocalScanner',
    'MetadataExtractor',
    'CSVManager',
    'DataAnalyst',
]
