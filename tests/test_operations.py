"""
Unit tests for NILA Operations API Endpoints
Verifies fleet ledger, decisions queue, dispatch orders, crowd reports, and handover briefs.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_fleet_ledger():
    response = client.get("/api/operations/fleet")
    assert response.status_code == 200
    data = response.json()
    assert data["total_fleet"] == 25
    assert "available" in data
    assert "in_service" in data
    assert len(data["buses"]) == 25
    assert data["provenance"] == "SIMULATED_TELEMETRY"


def test_get_bus_details():
    response = client.get("/api/operations/fleet/BUS-12")
    assert response.status_code == 200
    data = response.json()
    assert data["bus_id"] == "BUS-12"
    assert data["capacity"] == 51
    assert data["occupancy_band"] in ["EMPTY", "SEATS_FREE", "STANDING", "CROWDED"]


def test_update_bus_occupancy():
    response = client.post(
        "/api/operations/fleet/BUS-12/occupancy",
        json={"occupancy_band": "CROWDED", "current_load": 51},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["occupancy_band"] == "CROWDED"
    assert data["current_load"] == 51
    assert data["confidence"] == "HIGH"


def test_decision_queue_workflow():
    # 1. Fetch decisions
    res_dec = client.get("/api/operations/decisions")
    assert res_dec.status_code == 200
    decisions = res_dec.json()
    assert len(decisions) >= 1
    target = decisions[0]
    dec_id = target["id"]

    # 2. Approve decision -> creates order
    res_appr = client.post(f"/api/operations/decisions/{dec_id}/approve")
    assert res_appr.status_code == 200
    order = res_appr.json()
    assert order["decision_id"] == dec_id
    assert order["status"] == "DISPATCH_PENDING"
    assert "ORDER-" in order["id"]

    # 3. Acknowledge order
    res_ack = client.post(f"/api/operations/orders/{order['id']}/acknowledge")
    assert res_ack.status_code == 200
    ack_data = res_ack.json()
    assert ack_data["status"] == "ACKNOWLEDGED"

    # 4. Cannot comply with alternative
    res_cc = client.post(
        f"/api/operations/orders/{order['id']}/cannot-comply",
        json={"reason": "Driver mechanical failure report"},
    )
    assert res_cc.status_code == 200
    cc_data = res_cc.json()
    assert cc_data["status"] == "CANNOT_COMPLY"
    assert cc_data["cannot_comply_reason"] == "Driver mechanical failure report"
    assert cc_data["alternative_bus_id"] is not None


def test_field_marshal_crowd_report():
    response = client.post(
        "/api/operations/stops/stop-periyar/crowd-report",
        json={"stop_id": "stop-periyar", "level": "HEAVY", "notes": "Temple gate procession surge"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stop_id"] == "stop-periyar"
    assert data["level"] == "HEAVY"
    assert data["status"] == "RECORDED"


def test_ai_handover_brief():
    response = client.post("/api/operations/ai/handover")
    assert response.status_code == 200
    data = response.json()
    assert data["network_risk"] == "CRITICAL"
    assert "peak_window" in data
    assert "active_fleet_summary" in data
    assert data["active_fleet_summary"]["total"] == 25
