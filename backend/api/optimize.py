"""
NILA Fixed-Fleet Optimization API Endpoint
Computes optimal bus repositioning schedules under the Fixed Fleet Invariant.
"""

from fastapi import APIRouter, HTTPException, status
from backend.api.schemas import OptimizeRequest, OptimizeResponse
from backend.optimization.engine import optimizer

router = APIRouter(tags=["Optimization"])


@router.post("/optimize", response_model=OptimizeResponse, status_code=status.HTTP_200_OK)
async def optimize_fleet(request: OptimizeRequest) -> OptimizeResponse:
    """
    Computes optimal vehicle repositioning schedules subject to the Fixed Fleet Invariant.
    Conserves total fleet size and computes source service loss vs destination queue relief.
    """
    try:
        response = optimizer.optimize(request)
        return response
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization solver failed: {exc}",
        )
