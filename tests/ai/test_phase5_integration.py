"""
Phase 5 Integration Tests
Verifies that the Gemini AI layer is fully connected to the real Phase 4
FixedFleetOptimizer and TradeOff engine.

All numbers must originate from deterministic backend engines.
Gemini must never invent bus counts, waiting times, or risk scores.

Owned by: Gugaan
"""

import pytest
from unittest.mock import MagicMock
from backend.ai.tools import NilaTools
from backend.ai.service import NilaAIService
from backend.ai.client import GeminiClient
from backend.ai.schemas import AskRequest, AskResponse
from backend.optimization.engine import optimize_transport, get_plan_tradeoffs


# ============================================================
# 1. Optimizer Integration in NilaTools
# ============================================================

class TestOptimizerIntegrationInTools:
    """Verifies that NilaTools.get_current_plan and get_tradeoffs call the real optimizer."""

    def test_plan_calls_real_optimizer_not_stub(self):
        tools = NilaTools()
        res = tools.get_current_plan("madurai-chithirai-2026")
        assert res.status == "success", f"Expected success, got: {res.status}, error: {res.error}"
        assert res.data["plan_id"].startswith("opt-plan-")

    def test_plan_fleet_size_matches_festival_definition(self):
        tools = NilaTools()
        res = tools.get_current_plan("madurai-chithirai-2026")
        assert res.status == "success"
        assert res.data["total_fleet_size"] == 20

    def test_plan_fleet_conserved_invariant(self):
        tools = NilaTools()
        res = tools.get_current_plan("madurai-chithirai-2026")
        assert res.status == "success"
        assert res.data["fleet_conserved"] is True
        final_sum = sum(res.data["final_allocation"].values())
        assert final_sum == res.data["total_fleet_size"]

    def test_plan_moves_have_valid_stop_ids(self):
        tools = NilaTools()
        res = tools.get_current_plan("madurai-chithirai-2026")
        assert res.status == "success"
        known_stops = {"stop-periyar", "stop-aarapalayam", "stop-mattuthavani"}
        for move in res.data["repositioning_moves"]:
            assert move["source_stop"] in known_stops
            assert move["destination_stop"] in known_stops

    def test_plan_moves_have_real_travel_times(self):
        tools = NilaTools()
        res = tools.get_current_plan("madurai-chithirai-2026")
        assert res.status == "success"
        for move in res.data["repositioning_moves"]:
            assert move["travel_time_minutes"] > 0

    def test_plan_has_human_readable_service_loss_text(self):
        tools = NilaTools()
        res = tools.get_current_plan("madurai-chithirai-2026")
        assert res.status == "success"
        for move in res.data["repositioning_moves"]:
            loss = move["source_service_loss"]
            assert isinstance(loss, str) and len(loss) > 10

    def test_tradeoffs_structure_matches_optimizer_output(self):
        tools = NilaTools()
        res = tools.get_tradeoffs("madurai-chithirai-2026")
        assert res.status == "success"
        data = res.data
        assert "plan_id" in data
        assert "total_fleet_size" in data
        assert "fleet_conserved" in data
        assert "overall_queue_reduction_percentage" in data
        assert "unserved_demand_before" in data
        assert "unserved_demand_after" in data
        assert "moves" in data
        assert "modeled_assumptions" in data

    def test_tradeoffs_moves_contain_benefit_text(self):
        tools = NilaTools()
        res = tools.get_tradeoffs("madurai-chithirai-2026")
        assert res.status == "success"
        for move in res.data["moves"]:
            assert "expected_benefit" in move
            assert isinstance(move["expected_benefit"], str)
            assert len(move["expected_benefit"]) > 10


# ============================================================
# 2. Grounding: Gemini Receives Real Data
# ============================================================

class TestGeminiReceivesGroundedOptimizerData:

    def test_plan_prompt_contains_real_plan_data(self):
        mock_client = MagicMock(spec=GeminiClient)
        mock_client.is_available.return_value = True
        mock_client.generate.return_value = "Grounded optimizer answer."

        service = NilaAIService(gemini_client=mock_client)
        req = AskRequest(
            question="What is the current bus allocation plan?",
            festival_id="madurai-chithirai-2026"
        )
        service.ask(req)

        call_args = mock_client.generate.call_args
        prompt = call_args[1].get("prompt", "") if call_args[1] else call_args[0][0]
        assert "opt-plan" in prompt, "Gemini must receive real plan_id from optimizer, not stub"
        assert "fleet_conserved" in prompt, "Gemini must see fleet conservation status"

    def test_tradeoffs_prompt_contains_real_optimizer_data(self):
        """Gemini must receive real optimizer plan_id and fleet data in the prompt (not Phase 3 stubs)."""
        mock_client = MagicMock(spec=GeminiClient)
        mock_client.is_available.return_value = True
        mock_client.generate.return_value = "Grounded tradeoff answer."

        service = NilaAIService(gemini_client=mock_client)
        req = AskRequest(
            question="Why did NILA recommend moving a bus?",
            festival_id="madurai-chithirai-2026"
        )
        service.ask(req)

        call_args = mock_client.generate.call_args
        prompt = call_args[1].get("prompt", "") if call_args[1] else call_args[0][0]
        # Real optimizer always produces plan_id and fleet_conserved, even with 0 moves
        assert "opt-plan" in prompt, "Gemini must receive real plan_id from optimizer"
        assert "fleet_conserved" in prompt, "Gemini must see fleet conservation status"
        assert "festival_id" in prompt, "Gemini must see festival context"

    def test_plan_prompt_does_not_contain_phase3_stub_message(self):
        """Gemini prompt must NOT contain the old Phase 3 stub message; must contain real plan_id."""
        mock_client = MagicMock(spec=GeminiClient)
        mock_client.is_available.return_value = True
        mock_client.generate.return_value = "Answer."

        service = NilaAIService(gemini_client=mock_client)
        req = AskRequest(
            question="What is the current bus allocation plan?",
            festival_id="madurai-chithirai-2026"
        )
        service.ask(req)

        call_args = mock_client.generate.call_args
        prompt = call_args[1].get("prompt", "") if call_args[1] else call_args[0][0]
        # The Phase 3 stub contained this specific message — must be gone in Phase 5
        assert "No active bus redistribution plan computed" not in prompt, (
            "Gemini must NOT receive Phase 3 stub message. Phase 5 provides real optimizer data."
        )
        # Real Phase 5 optimizer data must be present
        assert "opt-plan" in prompt, "Real plan_id must be present in Gemini prompt"


# ============================================================
# 3. Non-Fabrication Guarantees
# ============================================================

class TestNonFabricationGuarantees:

    def test_plan_allocation_values_are_non_negative(self):
        tools = NilaTools()
        res = tools.get_current_plan("madurai-chithirai-2026")
        assert res.status == "success"
        for stop, count in res.data["final_allocation"].items():
            assert count >= 0, f"Stop {stop} has negative allocation: {count}"

    def test_plan_queue_reduction_is_bounded(self):
        tools = NilaTools()
        res = tools.get_current_plan("madurai-chithirai-2026")
        assert res.status == "success"
        pct = res.data["overall_queue_reduction_percentage"]
        assert 0.0 <= pct <= 100.0, f"Queue reduction out of bounds: {pct}"

    def test_tradeoffs_unserved_demand_does_not_increase(self):
        tools = NilaTools()
        res = tools.get_tradeoffs("madurai-chithirai-2026")
        assert res.status == "success"
        unserved_after = res.data.get("unserved_demand_after", 0)
        unserved_before = res.data.get("unserved_demand_before", 0)
        assert unserved_after <= unserved_before

    def test_plan_for_second_festival(self):
        tools = NilaTools()
        res = tools.get_current_plan("tiruvannamalai-deepam-2026")
        assert res.status == "success"
        assert res.data["total_fleet_size"] == 20
        assert res.data["fleet_conserved"] is True
        final_sum = sum(res.data["final_allocation"].values())
        assert final_sum == 20

    def test_error_handling_no_crash_on_invalid_festival(self):
        tools = NilaTools()
        plan_res = tools.get_current_plan("fake-festival-2099")
        tradeoff_res = tools.get_tradeoffs("fake-festival-2099")
        assert plan_res.status == "error"
        assert tradeoff_res.status == "error"
        assert plan_res.error is not None
        assert tradeoff_res.error is not None


# ============================================================
# 4. Optimizer Direct Integration (smoke tests)
# ============================================================

class TestOptimizerDirectIntegration:

    def test_optimize_transport_importable(self):
        assert callable(optimize_transport)

    def test_get_plan_tradeoffs_importable(self):
        assert callable(get_plan_tradeoffs)

    def test_direct_optimizer_run_returns_plan(self):
        plan = optimize_transport(
            festival_id="madurai-chithirai-2026",
            total_fleet_size=20,
            current_allocation={"stop-periyar": 8, "stop-aarapalayam": 6, "stop-mattuthavani": 6},
            predicted_demand_profile={"stop-periyar": 500, "stop-aarapalayam": 200, "stop-mattuthavani": 800},
            use_synthetic_capacity_fallback=True,
        )
        assert plan.fleet_conserved is True
        assert sum(plan.final_allocation.values()) == 20
        assert plan.status == "SUCCESS"

    def test_get_plan_tradeoffs_matches_optimizer_moves(self):
        plan = optimize_transport(
            festival_id="madurai-chithirai-2026",
            total_fleet_size=20,
            current_allocation={"stop-periyar": 8, "stop-aarapalayam": 6, "stop-mattuthavani": 6},
            predicted_demand_profile={"stop-periyar": 500, "stop-aarapalayam": 200, "stop-mattuthavani": 800},
            use_synthetic_capacity_fallback=True,
        )
        tradeoffs = get_plan_tradeoffs(plan)
        assert len(tradeoffs["moves"]) == len(plan.repositioning_moves)

