"""
Specialized agents for local and cloud file system scanning and analysis.

Agents communicate with each other to create a complete data pipeline:
- LocalScanner: Discovers files and folders in local directories
- CloudScanner: Discovers files and folders in OneDrive cloud storage
- Extractor: Parses folder/file names to extract structured data
- CSVManager: Maintains the CSV database
- Analyst: Processes queries and generates insights
"""

from .scanner import LocalScanner
from .cloud_scanner import CloudScanner
from .extractor import MetadataExtractor
from .csv_manager import CSVManager
from .analyst import DataAnalyst

__all__ = [
    'LocalScanner',
    'CloudScanner',
    'MetadataExtractor',
    'CSVManager',
    'DataAnalyst',
]
