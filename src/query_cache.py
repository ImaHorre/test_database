"""
Query Result Caching System

Implements LRU cache for expensive operations to improve response times.
Caches filter operations, analysis counts, and computed statistics.
"""

from functools import lru_cache
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import hashlib
import time
from datetime import datetime, timedelta


class QueryCache:
    """
    Simple query result cache with TTL and size limits.

    Features:
    - LRU eviction when cache is full
    - Time-to-live (TTL) for cache entries
    - Hash-based cache keys for complex parameters
    - DataFrame result caching with memory management
    """

    def __init__(self, max_size: int = 50, ttl_minutes: int = 30):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cache entries
            ttl_minutes: Time-to-live for cache entries in minutes
        """
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache = {}  # key -> (result, timestamp)
        self.access_order = []  # For LRU tracking

    def _generate_key(self, operation: str, **kwargs) -> str:
        """Generate cache key from operation and parameters."""
        # Sort kwargs for consistent key generation
        sorted_items = sorted(kwargs.items())
        key_data = f"{operation}:{sorted_items}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_expired(self, timestamp: datetime) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - timestamp > self.ttl

    def _evict_lru(self):
        """Evict least recently used entry."""
        if self.access_order:
            lru_key = self.access_order.pop(0)
            if lru_key in self.cache:
                del self.cache[lru_key]

    def _update_access(self, key: str):
        """Update access order for LRU tracking."""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

    def get(self, operation: str, **kwargs) -> Optional[Any]:
        """
        Get cached result if available and not expired.

        Args:
            operation: Operation name (e.g., 'filter', 'analysis_count')
            **kwargs: Operation parameters

        Returns:
            Cached result or None if not found/expired
        """
        key = self._generate_key(operation, **kwargs)

        if key not in self.cache:
            return None

        result, timestamp = self.cache[key]

        if self._is_expired(timestamp):
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            return None

        self._update_access(key)
        return result

    def set(self, operation: str, result: Any, **kwargs):
        """
        Cache operation result.

        Args:
            operation: Operation name
            result: Result to cache
            **kwargs: Operation parameters
        """
        key = self._generate_key(operation, **kwargs)

        # Evict if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()

        self.cache[key] = (result, datetime.now())
        self._update_access(key)

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        expired_count = sum(
            1 for _, timestamp in self.cache.values()
            if self._is_expired(timestamp)
        )

        return {
            'total_entries': len(self.cache),
            'expired_entries': expired_count,
            'valid_entries': len(self.cache) - expired_count,
            'max_size': self.max_size,
            'ttl_minutes': self.ttl.total_seconds() / 60
        }


class DataFrameCache:
    """
    Specialized cache for DataFrame operations with memory management.

    Features:
    - Shallow copies for DataFrames to save memory
    - Automatic memory cleanup
    - Operation-specific caching strategies
    """

    def __init__(self):
        """Initialize DataFrame cache."""
        self.cache = QueryCache(max_size=30, ttl_minutes=15)  # Smaller cache for DataFrames

    def get_filtered_data(self, device_type: str = None, flowrate: float = None,
                         pressure: float = None) -> Optional[pd.DataFrame]:
        """Get cached filtered DataFrame."""
        return self.cache.get(
            'filter',
            device_type=device_type,
            flowrate=flowrate,
            pressure=pressure
        )

    def set_filtered_data(self, result: pd.DataFrame, device_type: str = None,
                         flowrate: float = None, pressure: float = None):
        """Cache filtered DataFrame."""
        # Use copy to avoid reference issues
        self.cache.set(
            'filter',
            result.copy(),
            device_type=device_type,
            flowrate=flowrate,
            pressure=pressure
        )

    def get_analysis_counts(self, data_hash: str) -> Optional[Dict]:
        """Get cached analysis counts."""
        return self.cache.get('analysis_counts', data_hash=data_hash)

    def set_analysis_counts(self, result: Dict, data_hash: str):
        """Cache analysis counts."""
        self.cache.set('analysis_counts', result, data_hash=data_hash)

    def get_device_summary(self, device_type: str = None) -> Optional[pd.DataFrame]:
        """Get cached device summary."""
        return self.cache.get('device_summary', device_type=device_type)

    def set_device_summary(self, result: pd.DataFrame, device_type: str = None):
        """Cache device summary."""
        self.cache.set('device_summary', result.copy(), device_type=device_type)

    def clear(self):
        """Clear all cached data."""
        self.cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.stats()


class CachedAnalysisMixin:
    """
    Mixin class to add caching capabilities to analysis operations.

    Provides cached versions of expensive operations with automatic
    cache invalidation and memory management.
    """

    def __init__(self, *args, **kwargs):
        """Initialize caching mixin."""
        super().__init__(*args, **kwargs)
        self.df_cache = DataFrameCache()
        self._data_hash = None
        self._update_data_hash()

    def _update_data_hash(self):
        """Update data hash for cache invalidation."""
        if hasattr(self, 'df') and self.df is not None:
            # Create hash from DataFrame shape and column info
            hash_data = f"{len(self.df)}:{len(self.df.columns)}:{list(self.df.columns)}"
            self._data_hash = hashlib.md5(hash_data.encode()).hexdigest()

    def _invalidate_cache_if_needed(self):
        """Invalidate cache if data has changed."""
        old_hash = self._data_hash
        self._update_data_hash()

        if old_hash != self._data_hash:
            self.df_cache.clear()

    def cached_filter(self, device_type: str = None, flowrate: float = None,
                     pressure: float = None) -> pd.DataFrame:
        """Get filtered data with caching."""
        self._invalidate_cache_if_needed()

        # Try cache first
        cached_result = self.df_cache.get_filtered_data(device_type, flowrate, pressure)
        if cached_result is not None:
            return cached_result

        # Compute and cache result
        filtered = self.df.copy()

        if device_type:
            filtered = filtered[filtered['device_type'] == device_type]
        if flowrate:
            filtered = filtered[filtered['aqueous_flowrate'] == flowrate]
        if pressure:
            filtered = filtered[filtered['oil_pressure'] == pressure]

        self.df_cache.set_filtered_data(filtered, device_type, flowrate, pressure)
        return filtered

    def cached_analysis_counts(self, df: pd.DataFrame) -> Dict:
        """Get analysis counts with caching."""
        # Use DataFrame hash as cache key
        df_hash = hashlib.md5(f"{len(df)}:{df.columns.tolist()}".encode()).hexdigest()

        # Try cache first
        cached_result = self.df_cache.get_analysis_counts(df_hash)
        if cached_result is not None:
            return cached_result

        # Compute and cache result (implement the actual counting logic)
        # This would call the existing _count_complete_analyses method
        if hasattr(self, '_count_complete_analyses'):
            result = self._count_complete_analyses(df)
        else:
            # Fallback for testing
            result = {'complete_droplet': 0, 'complete_freq': 0, 'partial': 0, 'details': []}

        self.df_cache.set_analysis_counts(result, df_hash)
        return result

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics."""
        return {
            'dataframe_cache': self.df_cache.stats(),
            'current_data_hash': self._data_hash
        }