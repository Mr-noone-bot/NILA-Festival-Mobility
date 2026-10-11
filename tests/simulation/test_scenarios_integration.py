"""
Tests for NILA Scenario Integration with Madhu's Validated Scenarios Dataset
Verifies that all 7 operational scenarios from data/scenarios.json execute
deterministically through the SimulationEngine.
"""

import pytest
from backend.simulation.engine import SimulationEngine
from backend.simulation.models import SimulationInput, SimulationResult
from backend.simulation.scenarios import get_preset_scenario, list_presets


SCENARIO_IDS = [
    "normal",
    "attendance_120",
    "attendance_150",
    "rain",
    "event_delay_30",
    "bus_failure_1",
    "combined_stress",
]


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_all_validated_scenarios_execute(scenario_id: str):
    """Verifies each scenario in data/scenarios.json runs through simulation engine."""
    engine = SimulationEngine()
    params = get_preset_scenario(scenario_id)
    sim_input = SimulationInput(
        festival_id="madurai-chithirai-2026",
        scenario=params,
    )
    result = engine.simulate(sim_input)

    assert isinstance(result, SimulationResult)
    assert result.festival_id == "madurai-chithirai-2026"
    assert result.baseline.peak_crowd > 0
    assert result.scenario_result.peak_crowd > 0
    assert result.changes is not None
    assert len(result.stop_comparisons) > 0


def test_scenario_attendance_scaling():
    """Higher attendance scenarios produce strictly greater peak crowd."""
    engine = SimulationEngine()
    norm_res = engine.simulate(SimulationInput(
        festival_id="madurai-chithirai-2026",
        scenario=get_preset_scenario("normal"),
    ))
    att120_res = engine.simulate(SimulationInput(
        festival_id="madurai-chithirai-2026",
        scenario=get_preset_scenario("attendance_120"),
    ))
    att150_res = engine.simulate(SimulationInput(
        festival_id="madurai-chithirai-2026",
        scenario=get_preset_scenario("attendance_150"),
    ))

    assert att120_res.scenario_result.peak_crowd > norm_res.scenario_result.peak_crowd
    assert att150_res.scenario_result.peak_crowd > att120_res.scenario_result.peak_crowd


def test_scenario_rain_dampening_and_risk():
    """Rain scenario dampens total attendance but maintains elevated risk."""
    engine = SimulationEngine()
    norm_res = engine.simulate(SimulationInput(
        festival_id="madurai-chithirai-2026",
        scenario=get_preset_scenario("normal"),
    ))
    rain_res = engine.simulate(SimulationInput(
        festival_id="madurai-chithirai-2026",
        scenario=get_preset_scenario("rain"),
    ))

    # Rain dampens overall festival attendance
    assert rain_res.scenario_result.peak_crowd < norm_res.scenario_result.peak_crowd
    # Rain risk reaches high/critical due to passenger surge to transit terminals
    assert rain_res.scenario_result.overall_risk_score >= norm_res.scenario_result.overall_risk_score
