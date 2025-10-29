"""
Specialized agents for OneDrive file system scanning and analysis.

Agents communicate with each other to create a complete data pipeline:
- Scanner: Discovers files and folders in SharePoint
- Extractor: Parses folder/file names to extract structured data
- CSVManager: Maintains the CSV database
- Analyst: Processes queries and generates insights
"""

from .scanner import SharePointScanner
from .extractor import MetadataExtractor
from .csv_manager import CSVManager
from .analyst import DataAnalyst

__all__ = [
    'SharePointScanner',
    'MetadataExtractor',
    'CSVManager',
    'DataAnalyst',
]
