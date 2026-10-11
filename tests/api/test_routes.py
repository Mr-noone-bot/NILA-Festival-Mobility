"""
NILA API Tests — Routes Endpoint
Verifies POST /api/routes contract compliance and HTTP behavior.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
from backend.routing.service import routing_service

client = TestClient(app)


def test_routes_endpoint_success_live():
    """Verify POST /api/routes returns expected response fields."""
    routing_service.cache.clear()
    mock_osrm = {
        "code": "Ok",
        "routes": [
            {
                "distance": 6800.0,
                "duration": 1500.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [78.1561, 9.9482],
                        [78.1132, 9.9167],
                    ],
                },
            }
        ],
    }

    payload = {
        "origin": {"lat": 9.9482, "lng": 78.1561},
        "destination": {"lat": 9.9167, "lng": 78.1132},
        "congestion_factor": 1.4,
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_osrm

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        response = client.post("/api/routes", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["distance_meters"] == 6800
        assert data["duration_seconds"] == int(round(1500 * 1.4))
        assert "geometry" in data
        assert data["geometry"]["type"] == "LineString"
        assert len(data["geometry"]["coordinates"]) == 2
        # Verify GeoJSON [lon, lat] ordering
        assert data["geometry"]["coordinates"][0] == [78.1561, 9.9482]
        assert data["geometry"]["coordinates"][1] == [78.1132, 9.9167]
        assert data["provenance"] == "LIVE_OSRM"


def test_routes_endpoint_cached_recovery_on_failure():
    """Verify POST /api/routes recovers from cache if external OSRM fails."""
    # Note: previous test already cached MATTUTHAVANI -> PERIYAR
    payload = {
        "origin": {"lat": 9.9482, "lng": 78.1561},
        "destination": {"lat": 9.9167, "lng": 78.1132},
    }

    with patch("httpx.AsyncClient.get", side_effect=Exception("Network failure")):
        response = client.post("/api/routes", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["provenance"] == "CACHED_OSRM"
        assert data["distance_meters"] == 6800
        assert "historical cache" in data["fallback_warning"]


def test_routes_endpoint_cold_fallback():
    """Verify POST /api/routes returns fallback when external service fails and cache is empty."""
    routing_service.cache.clear()
    payload = {
        "origin": {"lat": 9.9482, "lng": 78.1561},
        "destination": {"lat": 9.9167, "lng": 78.1132},
    }

    with patch("httpx.AsyncClient.get", side_effect=Exception("Network down")):
        response = client.post("/api/routes", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["provenance"] == "FALLBACK_ESTIMATE"
        assert data["fallback_warning"] is not None
        assert data["distance_meters"] > 0
        assert data["duration_seconds"] > 0


def test_routes_endpoint_invalid_coordinates():
    """Verify POST /api/routes rejects out-of-range coordinates with 422."""
    payload = {
        "origin": {"lat": 95.0, "lng": 78.1561},
        "destination": {"lat": 9.9167, "lng": 78.1132},
    }
    response = client.post("/api/routes", json=payload)
    assert response.status_code == 422
