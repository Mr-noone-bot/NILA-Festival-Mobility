"""
NILA API Tests — Optimize Endpoint
Verifies POST /api/optimize contract compliance, Fixed Fleet conservation,
singular stop_forecast schema, staging capacity, and capacity provenance.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_optimize_endpoint_success():
    """Verify POST /api/optimize succeeds with valid contract payload."""
    payload = {
        "festival_id": "madurai-chithirai-2026",
        "total_fleet_size": 20,
        "current_allocation": {
            "stop-periyar": 5,
            "stop-aarapalayam": 5,
            "stop-mattuthavani": 10,
        },
        "predicted_demand_profile": {
            "stop-periyar": 4200,
            "stop-aarapalayam": 1800,
            "stop-mattuthavani": 600,
        },
        "time_horizon_minutes": 120,
        "use_synthetic_capacity_fallback": True,
    }

    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "plan_id" in data
    assert data["total_fleet_size"] == 20
    assert data["fleet_conserved"] is True
    assert "repositioning_moves" in data
    assert isinstance(data["repositioning_moves"], list)
    assert "final_allocation" in data
    assert sum(data["final_allocation"].values()) == 20
    assert data["overall_queue_reduction_percentage"] > 0
    assert "SYNTHETIC_FALLBACK" in data["capacity_provenance"]


def test_optimize_endpoint_fleet_mismatch_422():
    """Verify POST /api/optimize rejects fleet mismatch with 422."""
    payload = {
        "festival_id": "madurai-chithirai-2026",
        "total_fleet_size": 30,  # Sum is 20, declared is 30
        "current_allocation": {
            "stop-periyar": 5,
            "stop-aarapalayam": 5,
            "stop-mattuthavani": 10,
        },
        "predicted_demand_profile": {
            "stop-periyar": 1000,
        },
        "use_synthetic_capacity_fallback": True,
    }

    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "Fixed Fleet Invariant Violation" in data["detail"]


def test_optimize_endpoint_with_gugaan_singular_stop_forecast():
    """Verify POST /api/optimize works with Gugaan's exact singular stop_forecast array."""
    payload = {
        "festival_id": "madurai-chithirai-2026",
        "total_fleet_size": 15,
        "current_allocation": {
            "stop-mattuthavani": 10,
            "stop-periyar": 5,
        },
        "stop_forecast": [
            {
                "timestamp": "2026-10-10T20:15:00+05:30",
                "stop_id": "stop-periyar",
                "predicted_crowd": 5000,
                "arrivals": 1000,
                "departures": 800,
                "queue": 200,
                "required_buses": 25,
                "crowd_pressure": 0.85,
                "risk_score": 88.0,
                "risk_level": "CRITICAL",
            },
            {
                "timestamp": "2026-10-10T20:15:00+05:30",
                "stop_id": "stop-mattuthavani",
                "predicted_crowd": 100,
                "arrivals": 20,
                "departures": 50,
                "queue": 0,
                "required_buses": 1,
                "crowd_pressure": 0.1,
                "risk_score": 10.0,
                "risk_level": "LOW",
            },
        ],
        "time_horizon_minutes": 120,
        "departure_timestamp": "2026-10-10T20:15:00+05:30",
        "use_synthetic_capacity_fallback": True,
    }

    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["fleet_conserved"] is True
    assert sum(data["final_allocation"].values()) == 15
    assert len(data["repositioning_moves"]) > 0
    move = data["repositioning_moves"][0]
    assert move["source_stop"] == "stop-mattuthavani"
    assert move["destination_stop"] == "stop-periyar"


def test_optimize_endpoint_with_staging_limit():
    """Verify POST /api/optimize respects max_staging_capacity."""
    payload = {
        "festival_id": "madurai-chithirai-2026",
        "total_fleet_size": 20,
        "current_allocation": {
            "stop-mattuthavani": 15,
            "stop-periyar": 5,
        },
        "predicted_demand_profile": {
            "stop-mattuthavani": 0,
            "stop-periyar": 6000,
        },
        "max_staging_capacity": {
            "stop-periyar": 7,  # Maximum staging limit
        },
        "time_horizon_minutes": 120,
        "use_synthetic_capacity_fallback": True,
    }

    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["final_allocation"]["stop-periyar"] <= 7
