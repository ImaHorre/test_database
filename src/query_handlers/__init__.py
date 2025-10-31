"""
Query Handlers module for natural language query processing.

Contains specialized handler classes for different types of queries:
- ListQueryHandler: Handle "list" queries (devices, device types, etc.)
- FilterQueryHandler: Handle "filter" queries (by device type, parameters)
- CompareQueryHandler: Handle "compare" queries (device comparisons)
- AnalyzeQueryHandler: Handle "analyze" queries (flow parameter effects)
- TrackQueryHandler: Handle "track" queries (device history tracking)
- PlotQueryHandler: Handle "plot" queries (general plotting)
- DFUQueryHandler: Handle "plot_dfu" queries (DFU-specific plotting)
- ReportQueryHandler: Handle "report" queries (summary reports)

Each handler follows the same interface with a handle() method that takes
an intent object and returns a dictionary result.
"""

from .base_handler import QueryHandler
from .list_handler import ListQueryHandler
from .filter_handler import FilterQueryHandler
from .compare_handler import CompareQueryHandler
from .analyze_handler import AnalyzeQueryHandler
from .track_handler import TrackQueryHandler
from .plot_handler import PlotQueryHandler
from .dfu_handler import DFUQueryHandler
from .report_handler import ReportQueryHandler
from .router import QueryRouter

__all__ = [
    'QueryHandler',
    'ListQueryHandler',
    'FilterQueryHandler',
    'CompareQueryHandler',
    'AnalyzeQueryHandler',
    'TrackQueryHandler',
    'PlotQueryHandler',
    'DFUQueryHandler',
    'ReportQueryHandler',
    'QueryRouter'
]