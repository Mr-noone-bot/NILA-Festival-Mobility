"""
NILA Health API Endpoint
Foundation health check router.
"""

from fastapi import APIRouter
from backend.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Service health check endpoint.
    Returns HTTP 200 with service status.
    """
    return HealthResponse(
        status="healthy",
        service="nila-backend",
        version="0.1.0",
        environment="foundation",
    )
