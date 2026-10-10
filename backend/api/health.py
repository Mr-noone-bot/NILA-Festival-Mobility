"""
NILA Health API Endpoint
Foundation health check router.
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Service health check endpoint.
    Returns HTTP 200 with service status.
    """
    return {
        "status": "healthy",
        "service": "nila-backend",
        "version": "0.1.0",
        "environment": "foundation"
    }
