"""
Tests for NILA AI Tools Module (backend/ai/tools.py)
Owned by: Gugaan — updated for Phase 5 integration.
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


def test_tool_get_current_plan_phase5(nila_tools):
    """Phase 5: get_current_plan runs the real FixedFleetOptimizer grounded on prediction data.
    Verifies plan is available, fleet is conserved, and no numbers are fabricated."""
    res = nila_tools.get_current_plan("madurai-chithirai-2026")
    assert isinstance(res, ToolExecutionResult)
    assert res.tool_name == "get_current_plan"
    # Phase 5: returns real optimizer output
    assert res.status == "success"
    assert res.data["plan_available"] is True
    assert res.data["fleet_conserved"] is True
    # Fixed-fleet invariant: total_fleet_size in response matches festival default
    assert res.data["total_fleet_size"] == 20
    assert "repositioning_moves" in res.data
    assert "final_allocation" in res.data
    assert "overall_queue_reduction_percentage" in res.data
    # Final allocation sums to fleet total
    alloc_sum = sum(res.data["final_allocation"].values())
    assert alloc_sum == res.data["total_fleet_size"]


def test_tool_get_current_plan_fleet_conservation(nila_tools):
    """Phase 5: Fleet conservation invariant holds across all repositioning moves."""
    res = nila_tools.get_current_plan("tiruvannamalai-deepam-2026")
    assert res.status == "success"
    alloc_sum = sum(res.data["final_allocation"].values())
    assert alloc_sum == res.data["total_fleet_size"]
    assert res.data["fleet_conserved"] is True


def test_tool_get_tradeoffs_phase5(nila_tools):
    """Phase 5: get_tradeoffs returns real before/after trade-off data from the optimizer.
    Verifies structured output without any fabricated numbers."""
    res = nila_tools.get_tradeoffs("madurai-chithirai-2026")
    assert isinstance(res, ToolExecutionResult)
    assert res.tool_name == "get_tradeoffs"
    # Phase 5: returns real optimizer output
    assert res.status == "success"
    assert "tradeoffs_available" in res.data
    assert "plan_id" in res.data
    assert "total_fleet_size" in res.data
    assert "fleet_conserved" in res.data
    assert res.data["fleet_conserved"] is True
    assert "moves" in res.data
    # moves list contains structured trade-off data
    for move in res.data["moves"]:
        assert "source_stop" in move
        assert "destination_stop" in move
        assert "buses_to_transfer" in move
        assert "source_service_loss" in move
        assert "expected_benefit" in move
        assert "network_effect" in move


def test_tool_get_tradeoffs_invalid_festival(nila_tools):
    """Phase 5: Invalid festival returns structured error for trade-off tool."""
    res = nila_tools.get_tradeoffs("non-existent-fest-xyz")
    assert res.status == "error"
    assert res.error is not None


def test_tool_get_current_plan_invalid_festival(nila_tools):
    """Phase 5: Invalid festival returns structured error for plan tool."""
    res = nila_tools.get_current_plan("non-existent-fest-xyz")
    assert res.status == "error"
    assert res.error is not None


def test_tool_outputs_are_deterministic(nila_tools):
    """Calling tools with identical arguments returns identical data."""
    run1 = nila_tools.get_risk_analysis("madurai-chithirai-2026").data
    run2 = nila_tools.get_risk_analysis("madurai-chithirai-2026").data
    assert run1 == run2


def test_tool_plan_determinism(nila_tools):
    """Phase 5: Plan generation is deterministic — identical inputs produce identical allocations."""
    res1 = nila_tools.get_current_plan("madurai-chithirai-2026")
    res2 = nila_tools.get_current_plan("madurai-chithirai-2026")
    assert res1.status == "success"
    assert res2.status == "success"
    # Final allocations must be identical
    assert res1.data["final_allocation"] == res2.data["final_allocation"]
    assert res1.data["total_fleet_size"] == res2.data["total_fleet_size"]
