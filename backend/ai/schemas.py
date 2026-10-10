"""
NILA AI Schemas
Data schemas for the grounded Gemini AI assistant.
Owned by: Gugaan
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """User inquiry request to the NILA AI Copilot."""
    question: str = Field(..., description="Natural language operator question")
    festival_id: str = Field(default="madurai-chithirai-2026", description="Target festival ID")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional caller context")


class ToolExecutionResult(BaseModel):
    """Encapsulates the structured output from a deterministic backend tool."""
    tool_name: str
    status: str = Field(default="success", description="success | error | unavailable")
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class AskResponse(BaseModel):
    """Grounded AI response returned to the operator."""
    answer: str
    tool_used: Optional[str] = None
    tool_calls: List[str] = Field(default_factory=list)
    grounded: bool = True
    sources: List[str] = Field(default_factory=list)
    fallback_used: bool = False
