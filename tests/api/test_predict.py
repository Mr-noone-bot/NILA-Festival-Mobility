"""
Tests for POST /api/predict crowd prediction endpoint
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_predict_endpoint_success():
    payload = {
        "festival_id": "madurai-chithirai-2026",
        "time_window_start": "2026-04-28T06:00:00+05:30",
        "time_window_end": "2026-04-28T18:00:00+05:30",
        "weather_condition": "extreme_heat",
        "surge_multiplier": 1.15,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["festival_id"] == "madurai-chithirai-2026"
    assert "timeline" in data
    assert len(data["timeline"]) > 0
    assert "peak_surge_time" in data
    assert "highest_demand_stops" in data
    assert isinstance(data["highest_demand_stops"], list)
    assert "stop_forecasts" in data
    assert len(data["stop_forecasts"]) > 0


def test_predict_endpoint_unknown_festival():
    payload = {
        "festival_id": "non-existent-festival-xyz",
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code in [400, 500]
