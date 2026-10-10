"""
NILA AI Package
Grounded Gemini AI Copilot layer for operator explanations and decision support.
Owned by: Gugaan
"""

from backend.ai.schemas import (
    AskRequest,
    AskResponse,
    ToolExecutionResult,
)
from backend.ai.client import GeminiClient
from backend.ai.tools import NilaTools
from backend.ai.service import NilaAIService
from backend.ai.prompts import SYSTEM_PROMPT

__all__ = [
    "NilaAIService",
    "GeminiClient",
    "NilaTools",
    "AskRequest",
    "AskResponse",
    "ToolExecutionResult",
    "SYSTEM_PROMPT",
]
