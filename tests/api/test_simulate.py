"""
Tests for POST /api/simulate scenario simulation endpoint
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_simulate_endpoint_success():
    payload = {
        "festival_id": "madurai-chithirai-2026",
        "attendance_multiplier": 1.25,
        "rain_probability": 40.0,
        "event_delay_minutes": 30,
        "bus_failures": 2,
    }
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "simulation_id" in data
    assert "steps" in data
    assert len(data["steps"]) > 0
    assert "baseline" in data
    assert "scenario" in data
    assert "changes" in data
    assert "stop_comparisons" in data
    # Verify density grid points exist for spatial rendering
    first_step = data["steps"][0]
    assert "stop_queues" in first_step
    assert "density_grid" in first_step
    assert len(first_step["density_grid"]) > 0


def test_simulate_endpoint_unknown_festival():
    payload = {
        "festival_id": "invalid-festival-abc",
    }
    response = client.post("/api/simulate", json=payload)
    assert response.status_code in [400, 500]
