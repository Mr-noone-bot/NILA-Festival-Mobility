"""
Tests for NILA AI Tools Module (backend/ai/tools.py)
Owned by: Gugaan
"""

import pytest
from backend.ai.tools import NilaTools
from backend.ai.schemas import ToolExecutionResult


@pytest.fixture
def nila_tools():
    return NilaTools()


def test_tool_get_festival_details(nila_tools):
    """Tool returns authoritative festival details without fabricating facts."""
    res = nila_tools.get_festival_details("madurai-chithirai-2026")
    assert isinstance(res, ToolExecutionResult)
    assert res.tool_name == "get_festival_details"
    assert res.status == "success"
    assert res.data["id"] == "madurai-chithirai-2026"
    assert "stops" in res.data
    assert len(res.data["stops"]) > 0


def test_tool_get_festival_details_invalid(nila_tools):
    """Invalid festival returns structured error rather than throwing an unhandled exception."""
    res = nila_tools.get_festival_details("non-existent-fest-xyz")
    assert res.status == "error"
    assert "not found" in res.error.lower()


def test_tool_get_crowd_forecast(nila_tools):
    """Tool calls PredictionEngine and returns grounded forecast metrics."""
    res = nila_tools.get_crowd_forecast("madurai-chithirai-2026", attendance_multiplier=1.2)
    assert res.status == "success"
    assert res.data["peak_crowd"] > 0
    assert res.data["peak_time"] is not None
    assert "timeline_samples" in res.data


def test_tool_get_risk_analysis(nila_tools):
    """Tool extracts overall network risk, critical stops, and stop-level queue metrics."""
    res = nila_tools.get_risk_analysis("madurai-chithirai-2026")
    assert res.status == "success"
    assert "overall_risk_score" in res.data
    assert "overall_risk_level" in res.data
    assert "stops" in res.data
    assert len(res.data["stops"]) > 0


def test_tool_simulate_scenario(nila_tools):
    """Tool executes what-if simulation comparing baseline against modified parameters."""
    res = nila_tools.simulate_scenario(
        festival_id="madurai-chithirai-2026",
        attendance_multiplier=1.30,
        rain_probability=50.0,
        event_delay_minutes=30,
        bus_failure=1
    )
    assert res.status == "success"
    assert "baseline" in res.data
    assert "scenario_result" in res.data
    assert "changes" in res.data
    assert res.data["changes"]["peak_crowd_change"] > 0


def test_tool_get_current_plan_unavailable(nila_tools):
    """Optimizer plan tool returns clean unavailable status without fabricating recommendations."""
    res = nila_tools.get_current_plan("madurai-chithirai-2026")
    assert res.status == "unavailable"
    assert res.data["plan_available"] is False
    assert "optimization" in res.data["message"].lower()


def test_tool_get_tradeoffs_unavailable(nila_tools):
    """Trade-off tool returns clean unavailable status without fabricating vehicle transfers."""
    res = nila_tools.get_tradeoffs("madurai-chithirai-2026")
    assert res.status == "unavailable"
    assert res.data["tradeoffs_available"] is False
    assert "trade-off" in res.data["message"].lower()


def test_tool_outputs_are_deterministic(nila_tools):
    """Calling tools with identical arguments returns identical data."""
    run1 = nila_tools.get_risk_analysis("madurai-chithirai-2026").data
    run2 = nila_tools.get_risk_analysis("madurai-chithirai-2026").data
    assert run1 == run2
