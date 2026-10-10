"""
NILA API Tests — Festivals Endpoints
Verifies GET /api/festivals and GET /api/festivals/{festival_id} with strict data provenance.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_list_festivals_default_empty_when_official_data_unpopulated():
    """Verify GET /api/festivals returns empty list when official data is unpopulated."""
    response = client.get("/api/festivals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_festivals_with_synthetic_fixture():
    """Verify GET /api/festivals?include_synthetic=true returns clearly flagged fixtures."""
    response = client.get("/api/festivals?include_synthetic=true")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert item["id"] == "madurai-chithirai-2026"
    assert item["is_verified"] is False
    assert item["provenance"] == "SYNTHETIC_FIXTURE"


def test_get_festival_details_default_404_when_unpopulated():
    """Verify GET /api/festivals/{id} returns 404 when official data is unpopulated."""
    response = client.get("/api/festivals/madurai-chithirai-2026")
    assert response.status_code == 404
    data = response.json()
    assert "not found in verified official data" in data["detail"].lower()


def test_get_festival_details_with_synthetic_flag():
    """Verify GET /api/festivals/{id}?include_synthetic=true returns marked synthetic detail."""
    response = client.get("/api/festivals/madurai-chithirai-2026?include_synthetic=true")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "madurai-chithirai-2026"
    assert data["is_verified"] is False
    assert data["provenance"] == "SYNTHETIC_FIXTURE"
    assert data["temple"]["name"] == "Meenakshi Sundareswarar Temple"
    assert len(data["stops"]) == 3


def test_get_unknown_festival_returns_404():
    """Verify unknown festival ID returns 404 even with include_synthetic=true."""
    response = client.get("/api/festivals/unknown-festival-999?include_synthetic=true")
    assert response.status_code == 404
