"""
NILA Routing API Endpoint
Proxies route duration, distance, and road geometry requests to the RoutingService.
"""

from fastapi import APIRouter, HTTPException, status
from backend.api.schemas import RouteRequest, RouteResponse
from backend.routing.service import routing_service

router = APIRouter(tags=["Routing"])


@router.post("/routes", response_model=RouteResponse, status_code=status.HTTP_200_OK)
async def calculate_route(request: RouteRequest) -> RouteResponse:
    """
    Calculate road transit duration and GeoJSON LineString between two festival stops.
    Queries OSRM backend with in-memory caching and haversine disaster-recovery fallback.
    """
    try:
        response = await routing_service.get_route(
            origin_lat=request.origin.lat,
            origin_lng=request.origin.lng,
            dest_lat=request.destination.lat,
            dest_lng=request.destination.lng,
            congestion_factor=request.congestion_factor,
        )
        return response
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing service failure: {exc}",
        )
