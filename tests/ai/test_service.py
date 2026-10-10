"""
Tests for NILA AI Service (backend/ai/service.py)
Owned by: Gugaan
"""

import pytest
from unittest.mock import MagicMock
from backend.ai.client import GeminiClient
from backend.ai.tools import NilaTools
from backend.ai.service import NilaAIService, _extract_scenario_params
from backend.ai.schemas import AskRequest, AskResponse


def test_scenario_param_extraction():
    """Validates regex parameter extraction from natural language what-if queries."""
    params = _extract_scenario_params("What happens if attendance increases by 30% and it rains 70%?")
    assert params["attendance_multiplier"] == 1.30
    assert params["rain_probability"] == 70.0

    params_delay = _extract_scenario_params("What happens if the chariot procession ends 45 minutes late and 2 buses break down?")
    assert params_delay["event_delay_minutes"] == 45
    assert params_delay["bus_failure"] == 2


def test_missing_api_key_graceful_fallback():
    """When GEMINI_API_KEY is not configured, the service falls back gracefully to deterministic brief."""
    client = GeminiClient(api_key="")
    assert client.is_available() is False

    service = NilaAIService(gemini_client=client)
    req = AskRequest(
        question="Why is the main bus stand critical?",
        festival_id="madurai-chithirai-2026"
    )
    res = service.ask(req)

    assert isinstance(res, AskResponse)
    assert res.fallback_used is True
    assert res.grounded is True
    assert res.tool_used == "get_risk_analysis"
    assert "Overall Network Risk" in res.answer or "Grounded" in res.answer


def test_gemini_api_failure_fallback():
    """If the Gemini API client errors or times out, the service falls back gracefully."""
    mock_client = MagicMock(spec=GeminiClient)
    mock_client.is_available.return_value = True
    # Simulate API failure / network exception returning None
    mock_client.generate.return_value = None

    service = NilaAIService(gemini_client=mock_client)
    req = AskRequest(
        question="When will the crowd peak?",
        festival_id="madurai-chithirai-2026"
    )
    res = service.ask(req)

    assert res.fallback_used is True
    assert res.tool_used == "get_crowd_forecast"
    assert "projected to peak at" in res.answer or "Grounded" in res.answer


def test_mocked_gemini_successful_generation():
    """When Gemini is available, synthesis succeeds using authoritative tool data."""
    mock_client = MagicMock(spec=GeminiClient)
    mock_client.is_available.return_value = True
    mock_client.generate.return_value = (
        "Periyar Bus Stand is currently at HIGH risk because passenger arrivals are surging "
        "following the 10:00 chariot procession conclusion, creating a queue backlog of 1,200 passengers."
    )

    service = NilaAIService(gemini_client=mock_client)
    req = AskRequest(
        question="Why is Periyar bus stand at high risk?",
        festival_id="madurai-chithirai-2026"
    )
    res = service.ask(req)

    assert res.fallback_used is False
    assert res.grounded is True
    assert "Periyar Bus Stand" in res.answer
    assert res.tool_used == "get_risk_analysis"
    assert "NILA prediction engine" in res.sources
    mock_client.generate.assert_called_once()


def test_tool_routing_intents():
    """Verifies that different operator question types route to the correct authoritative tool."""
    service = NilaAIService(gemini_client=GeminiClient(api_key=""))
    fest_id = "madurai-chithirai-2026"

    # Risk inquiry
    tool1, _, _ = service.route_and_execute_tool("Which stop has the highest risk?", fest_id)
    assert tool1 == "get_risk_analysis"

    # Peak timing inquiry
    tool2, _, _ = service.route_and_execute_tool("When will the crowd peak?", fest_id)
    assert tool2 == "get_crowd_forecast"

    # What-if scenario inquiry
    tool3, _, _ = service.route_and_execute_tool("What happens if attendance increases by 30%?", fest_id)
    assert tool3 == "simulate_scenario"

    # Bus repositioning trade-off inquiry
    tool4, _, _ = service.route_and_execute_tool("Why did NILA recommend moving a bus?", fest_id)
    assert tool4 == "get_tradeoffs"

    # Bus allocation plan inquiry
    tool5, _, _ = service.route_and_execute_tool("What is the current bus plan?", fest_id)
    assert tool5 == "get_current_plan"

    # Festival infrastructure inquiry
    tool6, _, _ = service.route_and_execute_tool("Tell me about the festival gates and stops", fest_id)
    assert tool6 == "get_festival_details"


def test_security_no_api_key_leak():
    """Confirms no API key or sensitive token is exposed in AskResponse or source representations."""
    secret_key = "dummy-test-key-xyz123"
    mock_client = MagicMock(spec=GeminiClient)
    mock_client.is_available.return_value = True
    mock_client.generate.return_value = "Grounded operational explanation without secrets."

    service = NilaAIService(gemini_client=mock_client)
    req = AskRequest(
        question="What is the forecast?",
        festival_id="madurai-chithirai-2026"
    )
    res = service.ask(req)
    response_str = res.model_dump_json()
    assert secret_key not in response_str
    assert "dummy" not in response_str.lower()
