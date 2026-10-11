"""
NILA Routing Service
Proxy service for OSRM route computation with in-memory caching,
cache recovery, and deterministic haversine fallback approximation.
"""

import math
import time
import logging
from typing import Dict, Tuple, Optional, List
import httpx

from backend.core.config import settings
from backend.core.constants import RouteProvenance
from backend.api.schemas import RouteResponse, GeoJSONGeometry

logger = logging.getLogger(__name__)


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two GPS coordinates using the Haversine formula.
    Returns distance in metres.
    """
    R = 6371000.0  # Earth's mean radius in metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def format_duration(seconds: int) -> str:
    """Convert travel duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds} secs"
    minutes = round(seconds / 60)
    if minutes < 60:
        return f"{minutes} mins"
    hours = minutes // 60
    remaining_mins = minutes % 60
    if remaining_mins == 0:
        return f"{hours} hr" if hours == 1 else f"{hours} hrs"
    return f"{hours} hr {remaining_mins} mins"


class RoutingCache:
    """In-memory cache with TTL for OSRM responses."""

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 500):
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._cache: Dict[str, Tuple[dict, float]] = {}

    def _make_key(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> str:
        return f"{origin_lat:.5f},{origin_lng:.5f}->{dest_lat:.5f},{dest_lng:.5f}"

    def get(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> Optional[dict]:
        key = self._make_key(origin_lat, origin_lng, dest_lat, dest_lng)
        entry = self._cache.get(key)
        if not entry:
            return None
        data, timestamp = entry
        # Valid even after TTL for disaster recovery, but let caller know
        return data

    def put(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, data: dict) -> None:
        if len(self._cache) >= self._max_size:
            # Evict oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            self._cache.pop(oldest_key, None)
        key = self._make_key(origin_lat, origin_lng, dest_lat, dest_lng)
        self._cache[key] = (data, time.time())

    def clear(self) -> None:
        self._cache.clear()


class RoutingService:
    """
    High-availability routing proxy for festival bus mobility.
    Adheres to the strict boundary: Frontend -> NILA Backend -> OSRM.
    """

    def __init__(self, cache: Optional[RoutingCache] = None, http_client: Optional[httpx.AsyncClient] = None):
        self.cache = cache or RoutingCache(ttl_seconds=settings.ROUTE_CACHE_TTL_SECONDS)
        self._client = http_client

    def validate_coordinates(self, lat: float, lng: float, label: str = "coordinate") -> None:
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Invalid {label} latitude: {lat}. Must be within [-90.0, 90.0].")
        if not (-180.0 <= lng <= 180.0):
            raise ValueError(f"Invalid {label} longitude: {lng}. Must be within [-180.0, 180.0].")

    async def get_route(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        congestion_factor: float = 1.0,
    ) -> RouteResponse:
        """
        Compute road transit duration and GeoJSON geometry between two stops.
        Tries Live OSRM -> Cached OSRM -> Haversine Fallback.
        """
        self.validate_coordinates(origin_lat, origin_lng, label="origin")
        self.validate_coordinates(dest_lat, dest_lng, label="destination")

        if congestion_factor < 0.5:
            congestion_factor = 0.5

        # Check identical origin and destination
        if math.isclose(origin_lat, dest_lat, abs_tol=1e-6) and math.isclose(origin_lng, dest_lng, abs_tol=1e-6):
            return RouteResponse(
                distance_meters=0,
                duration_seconds=0,
                duration_formatted="0 mins",
                geometry=GeoJSONGeometry(
                    type="LineString",
                    coordinates=[[origin_lng, origin_lat], [dest_lng, dest_lat]],
                ),
                provenance=RouteProvenance.LIVE_OSRM,
                fallback_warning=None,
            )

        # 1. Attempt Live OSRM Call
        # Note: OSRM format is {longitude},{latitude};{longitude},{latitude}
        osrm_url = (
            f"{settings.OSRM_BACKEND_URL.rstrip('/')}/route/v1/driving/"
            f"{origin_lng:.6f},{origin_lat:.6f};{dest_lng:.6f},{dest_lat:.6f}"
            f"?overview=full&geometries=geojson"
        )

        try:
            client = self._client or httpx.AsyncClient(timeout=settings.OSRM_TIMEOUT_SECONDS)
            should_close = self._client is None
            try:
                response = await client.get(osrm_url)
            finally:
                if should_close:
                    await client.aclose()

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "Ok" and "routes" in data and len(data["routes"]) > 0:
                    primary_route = data["routes"][0]
                    raw_distance = int(round(primary_route["distance"]))
                    raw_duration = primary_route["duration"]
                    adjusted_duration = int(round(raw_duration * congestion_factor))
                    raw_coords = primary_route["geometry"]["coordinates"]

                    # Cache successful raw OSRM result
                    self.cache.put(
                        origin_lat, origin_lng, dest_lat, dest_lng,
                        {
                            "distance_meters": raw_distance,
                            "raw_duration": raw_duration,
                            "coordinates": raw_coords,
                        }
                    )

                    return RouteResponse(
                        distance_meters=raw_distance,
                        duration_seconds=adjusted_duration,
                        duration_formatted=format_duration(adjusted_duration),
                        geometry=GeoJSONGeometry(
                            type="LineString",
                            coordinates=raw_coords,
                        ),
                        provenance=RouteProvenance.LIVE_OSRM,
                        fallback_warning=None,
                    )
                else:
                    logger.warning(f"OSRM returned non-OK response code: {data.get('code')}")
            else:
                logger.warning(f"OSRM HTTP error: {response.status_code}")

        except Exception as exc:
            logger.warning(f"OSRM service request failed ({type(exc).__name__}): {exc}")

        # 2. Attempt Recovery from Cached Route
        cached = self.cache.get(origin_lat, origin_lng, dest_lat, dest_lng)
        if cached:
            raw_distance = cached["distance_meters"]
            adjusted_duration = int(round(cached["raw_duration"] * congestion_factor))
            return RouteResponse(
                distance_meters=raw_distance,
                duration_seconds=adjusted_duration,
                duration_formatted=format_duration(adjusted_duration),
                geometry=GeoJSONGeometry(
                    type="LineString",
                    coordinates=cached["coordinates"],
                ),
                provenance=RouteProvenance.CACHED_OSRM,
                fallback_warning="Live OSRM routing was unreachable. Route recovered from historical cache.",
            )

        # 3. Configured Fallback Approximation
        # Calculate Haversine distance with road tortuosity factor (1.35x for Tamil Nadu temple town grids)
        straight_distance = haversine_distance_meters(origin_lat, origin_lng, dest_lat, dest_lng)
        estimated_distance = int(round(straight_distance * 1.35))
        
        # Speed in m/s (20 km/h = 5.556 m/s)
        speed_mps = (settings.FALLBACK_AVERAGE_SPEED_KMH * 1000.0) / 3600.0
        base_duration = estimated_distance / speed_mps
        adjusted_duration = int(round(base_duration * congestion_factor))

        # Fallback GeoJSON geometry: straight line [origin, dest] in [lon, lat] order
        fallback_coordinates = [
            [origin_lng, origin_lat],
            [dest_lng, dest_lat],
        ]

        return RouteResponse(
            distance_meters=estimated_distance,
            duration_seconds=adjusted_duration,
            duration_formatted=format_duration(adjusted_duration),
            geometry=GeoJSONGeometry(
                type="LineString",
                coordinates=fallback_coordinates,
            ),
            provenance=RouteProvenance.FALLBACK_ESTIMATE,
            fallback_warning=(
                f"OSRM routing engine offline. Distance and travel duration calculated using "
                f"haversine geodesic approximation (tortuosity=1.35, base speed={settings.FALLBACK_AVERAGE_SPEED_KMH} km/h, "
                f"congestion factor={congestion_factor:.1f}). Road geometries are direct corridors."
            ),
        )


# Global singleton service
routing_service = RoutingService()
