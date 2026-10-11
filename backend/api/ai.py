"""
NILA AI API Routes

HTTP boundary for the grounded NilaAIService.
"""

from fastapi import APIRouter, HTTPException

from backend.ai.schemas import AskRequest, AskResponse
from backend.ai.service import NilaAIService


router = APIRouter(prefix="/ai", tags=["AI"])

_ai_service = NilaAIService()


@router.post("/ask", response_model=AskResponse)
def ask_nila(request: AskRequest) -> AskResponse:
    """
    Answer a user question using grounded NILA tools and Gemini.
    """
    try:
        return _ai_service.ask(request)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"NILA AI request failed: {exc}",
        ) from exc
