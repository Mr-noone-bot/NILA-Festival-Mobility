"""
NILA Routing Service Tests
Verifies OSRM proxy, coordinate validation, GeoJSON geometry ordering,
in-memory caching, disaster recovery, and haversine fallback approximation.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from backend.routing.service import (
    RoutingService,
    RoutingCache,
    haversine_distance_meters,
    format_duration,
)
from backend.core.constants import RouteProvenance


# Sample Madurai Coordinates
# Mattuthavani: 9.9482, 78.1561
# Periyar: 9.9167, 78.1132
MATTUTHAVANI = (9.9482, 78.1561)
PERIYAR = (9.9167, 78.1132)


MOCK_OSRM_SUCCESS_PAYLOAD = {
    "code": "Ok",
    "routes": [
        {
            "distance": 6800.4,
            "duration": 1500.0,
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [78.1561, 9.9482],
                    [78.1350, 9.9320],
                    [78.1132, 9.9167],
                ],
            },
        }
    ],
    "waypoints": [],
}


@pytest.fixture
def mock_cache():
    return RoutingCache(ttl_seconds=3600)


@pytest.mark.asyncio
async def test_valid_osrm_response(mock_cache):
    """Verify successful route parsing with distance_meters, duration, and GeoJSON [lon, lat]."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_OSRM_SUCCESS_PAYLOAD
    mock_client.get.return_value = mock_response

    service = RoutingService(cache=mock_cache, http_client=mock_client)
    res = await service.get_route(
        origin_lat=MATTUTHAVANI[0],
        origin_lng=MATTUTHAVANI[1],
        dest_lat=PERIYAR[0],
        dest_lng=PERIYAR[1],
        congestion_factor=1.0,
    )

    assert res.distance_meters == 6800
    assert res.duration_seconds == 1500
    assert res.duration_formatted == "25 mins"
    assert res.provenance == RouteProvenance.LIVE_OSRM
    assert res.fallback_warning is None
    assert res.geometry.type == "LineString"
    assert len(res.geometry.coordinates) == 3
    # Check [longitude, latitude] ordering
    assert res.geometry.coordinates[0] == [78.1561, 9.9482]
    assert res.geometry.coordinates[2] == [78.1132, 9.9167]


@pytest.mark.asyncio
async def test_osrm_with_congestion_factor(mock_cache):
    """Verify duration scales with congestion_factor."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_OSRM_SUCCESS_PAYLOAD
    mock_client.get.return_value = mock_response

    service = RoutingService(cache=mock_cache, http_client=mock_client)
    res = await service.get_route(
        origin_lat=MATTUTHAVANI[0],
        origin_lng=MATTUTHAVANI[1],
        dest_lat=PERIYAR[0],
        dest_lng=PERIYAR[1],
        congestion_factor=1.5,
    )

    # 1500 * 1.5 = 2250 seconds = 38 mins
    assert res.duration_seconds == 2250
    assert res.duration_formatted == "38 mins"


@pytest.mark.asyncio
async def test_successful_caching_and_cache_recovery(mock_cache):
    """Verify that a successful OSRM route is cached and recovered upon subsequent OSRM failure."""
    # Step 1: Live call succeeds and writes to cache
    mock_client_success = AsyncMock(spec=httpx.AsyncClient)
    mock_resp_success = MagicMock()
    mock_resp_success.status_code = 200
    mock_resp_success.json.return_value = MOCK_OSRM_SUCCESS_PAYLOAD
    mock_client_success.get.return_value = mock_resp_success

    service1 = RoutingService(cache=mock_cache, http_client=mock_client_success)
    await service1.get_route(
        origin_lat=MATTUTHAVANI[0],
        origin_lng=MATTUTHAVANI[1],
        dest_lat=PERIYAR[0],
        dest_lng=PERIYAR[1],
    )

    # Step 2: Live call now fails (503 Service Unavailable)
    mock_client_fail = AsyncMock(spec=httpx.AsyncClient)
    mock_resp_fail = MagicMock()
    mock_resp_fail.status_code = 503
    mock_client_fail.get.return_value = mock_resp_fail

    service2 = RoutingService(cache=mock_cache, http_client=mock_client_fail)
    recovered = await service2.get_route(
        origin_lat=MATTUTHAVANI[0],
        origin_lng=MATTUTHAVANI[1],
        dest_lat=PERIYAR[0],
        dest_lng=PERIYAR[1],
    )

    assert recovered.distance_meters == 6800
    assert recovered.duration_seconds == 1500
    assert recovered.provenance == RouteProvenance.CACHED_OSRM
    assert "historical cache" in recovered.fallback_warning


@pytest.mark.asyncio
async def test_fallback_when_no_cache_and_osrm_fails():
    """Verify haversine approximation fallback when OSRM fails and cache is empty."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.ConnectTimeout("OSRM connection timed out")

    empty_cache = RoutingCache()
    service = RoutingService(cache=empty_cache, http_client=mock_client)

    res = await service.get_route(
        origin_lat=MATTUTHAVANI[0],
        origin_lng=MATTUTHAVANI[1],
        dest_lat=PERIYAR[0],
        dest_lng=PERIYAR[1],
        congestion_factor=1.2,
    )

    assert res.provenance == RouteProvenance.FALLBACK_ESTIMATE
    assert res.fallback_warning is not None
    assert "haversine geodesic approximation" in res.fallback_warning
    assert res.distance_meters > 0
    assert res.duration_seconds > 0
    # Coordinates in fallback LineString must be [lon, lat]
    assert res.geometry.coordinates[0] == [MATTUTHAVANI[1], MATTUTHAVANI[0]]
    assert res.geometry.coordinates[1] == [PERIYAR[1], PERIYAR[0]]


@pytest.mark.asyncio
async def test_malformed_osrm_response_triggers_fallback():
    """Verify that a 200 response with invalid structure safely falls back."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": "NoRoute", "routes": []}
    mock_client.get.return_value = mock_response

    service = RoutingService(cache=RoutingCache(), http_client=mock_client)
    res = await service.get_route(
        origin_lat=MATTUTHAVANI[0],
        origin_lng=MATTUTHAVANI[1],
        dest_lat=PERIYAR[0],
        dest_lng=PERIYAR[1],
    )

    assert res.provenance == RouteProvenance.FALLBACK_ESTIMATE


@pytest.mark.asyncio
async def test_same_origin_and_destination():
    """Verify zero distance/duration when origin matches destination."""
    service = RoutingService()
    res = await service.get_route(
        origin_lat=MATTUTHAVANI[0],
        origin_lng=MATTUTHAVANI[1],
        dest_lat=MATTUTHAVANI[0],
        dest_lng=MATTUTHAVANI[1],
    )

    assert res.distance_meters == 0
    assert res.duration_seconds == 0
    assert res.duration_formatted == "0 mins"


def test_coordinate_validation():
    """Verify bounds validation on coordinates."""
    service = RoutingService()
    with pytest.raises(ValueError, match="Invalid origin latitude"):
        service.validate_coordinates(95.0, 78.0, label="origin")

    with pytest.raises(ValueError, match="Invalid destination longitude"):
        service.validate_coordinates(9.0, 190.0, label="destination")


def test_duration_formatter():
    assert format_duration(30) == "30 secs"
    assert format_duration(300) == "5 mins"
    assert format_duration(3600) == "1 hr"
    assert format_duration(3900) == "1 hr 5 mins"
    assert format_duration(7200) == "2 hrs"
