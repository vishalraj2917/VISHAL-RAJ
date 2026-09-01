import time
from typing import Dict, Any, Optional, Tuple


class LiveDataCache:
    """
    Simple in-memory TTL cache for live weather and air quality observations.
    Prevents duplicate external API calls within the cache TTL window (e.g., 300s).
    """

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def _make_key(self, latitude: float, longitude: float, service: str) -> str:
        # Round coordinates to 3 decimals (~110 meters) for spatial caching
        return f"{service}:{round(latitude, 3)}:{round(longitude, 3)}"

    def get(self, latitude: float, longitude: float, service: str) -> Optional[Any]:
        key = self._make_key(latitude, longitude, service)
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return data
            else:
                del self._cache[key]
        return None

    def set(self, latitude: float, longitude: float, service: str, data: Any) -> None:
        key = self._make_key(latitude, longitude, service)
        self._cache[key] = (time.time(), data)

    def clear(self) -> None:
        self._cache.clear()


# Global singleton cache instance
live_data_cache = LiveDataCache(ttl_seconds=300)
