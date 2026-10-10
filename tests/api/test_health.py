"""
NILA Foundation Tests — Health Check
Verifies that FastAPI backend initializes and GET /api/health returns HTTP 200.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check_status_code():
    """Verify that the health check endpoint returns HTTP 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_check_payload():
    """Verify that the health check payload contains the expected service info."""
    response = client.get("/api/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "nila-backend"
    assert "version" in data


def test_root_endpoint():
    """Verify that the root endpoint responds with basic system info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "health" in data
