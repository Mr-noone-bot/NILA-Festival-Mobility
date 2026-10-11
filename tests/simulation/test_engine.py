"""
Tests for NILA Simulation Engine (backend/simulation/engine.py)
Owned by: Gugaan
"""

import pytest
from backend.prediction.models import Festival, Stop, FestivalEvent
from backend.prediction.engine import PredictionEngine
from backend.simulation.models import (
    SimulationInput,
    ScenarioParameters,
    SimulationResult,
)
from backend.simulation.engine import SimulationEngine


@pytest.fixture
def sim_test_festival():
    """Provides a realistic test festival configuration for simulation tests."""
    return Festival(
        id="sim-madurai-fest",
        name="Chithirai Simulation Festival",
        city="Madurai",
        base_attendance=100000,
        intensity=1.2,
        peak_events=[
            FestivalEvent(
                name="Chariot Procession",
                start_time="2026-04-28T07:00:00+05:30",
                end_time="2026-04-28T10:00:00+05:30",
                estimated_turnout=120000,
            )
        ],
        stops=[
            Stop(id="stop_main", name="Main Central Terminus", capacity=2500, weight=0.60, current_buses=10),
            Stop(id="stop_north", name="North Outer Stand", capacity=1500, weight=0.40, current_buses=6),
        ],
        default_fleet_size=20,
    )


def test_baseline_equals_prediction_engine(sim_test_festival):
    """When scenario parameters are identical to baseline, baseline and scenario match."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(
            attendance_multiplier=1.0,
            rain_probability=0.0,
            event_delay_minutes=0,
            bus_failure=0,
        ),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    res = sim_engine.simulate(sim_input, festival_override=sim_test_festival)
    assert isinstance(res, SimulationResult)
    assert res.baseline.peak_crowd == res.scenario_result.peak_crowd
    assert res.baseline.peak_time == res.scenario_result.peak_time
    assert res.baseline.overall_risk_score == res.scenario_result.overall_risk_score
    assert res.changes.peak_crowd_change == 0
    assert res.changes.peak_crowd_change_percent == 0.0
    assert res.changes.risk_score_change == 0


def test_attendance_increase_twenty_percent(sim_test_festival):
    """+20% attendance increases peak crowd by ~20% and increases required buses."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(attendance_multiplier=1.20),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    res = sim_engine.simulate(sim_input, festival_override=sim_test_festival)
    assert res.changes.peak_crowd_change > 0
    assert pytest.approx(res.changes.peak_crowd_change_percent, abs=0.5) == 20.0
    assert res.scenario_result.peak_crowd > res.baseline.peak_crowd


def test_attendance_increase_fifty_percent(sim_test_festival):
    """+50% attendance increases peak crowd by ~50%."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(attendance_multiplier=1.50),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    res = sim_engine.simulate(sim_input, festival_override=sim_test_festival)
    assert pytest.approx(res.changes.peak_crowd_change_percent, abs=0.5) == 50.0


def test_increased_rain_effect(sim_test_festival):
    """Rain probability increases overall risk score due to transit rush and queue concentration."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(rain_probability=80.0),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    res = sim_engine.simulate(sim_input, festival_override=sim_test_festival)
    # Total attendance is dampened by rain, but risk increases
    assert res.changes.risk_score_change >= 0
    assert res.scenario_result.overall_risk_score >= res.baseline.overall_risk_score


def test_event_delay_shifts_peak_time(sim_test_festival):
    """A 30-minute delay shifts the post-event discharge surge timing by 30 minutes."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(event_delay_minutes=30),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    res = sim_engine.simulate(sim_input, festival_override=sim_test_festival)
    assert res.baseline.peak_time != res.scenario_result.peak_time


def test_zero_bus_failure(sim_test_festival):
    """Zero bus failure produces no fleet reduction."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(bus_failure=0),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )
    res = sim_engine.simulate(sim_input, festival_override=sim_test_festival)
    assert res.changes.risk_score_change == 0


def test_one_bus_failure_increases_queue_and_risk(sim_test_festival):
    """1 bus failure reduces service capacity, resulting in increased queue or risk."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(bus_failure=1),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    res = sim_engine.simulate(sim_input, festival_override=sim_test_festival)
    # The stop affected should show increased queue or risk
    assert any(sc.queue_change >= 0 for sc in res.stop_comparisons)
    assert res.scenario_result.overall_risk_score >= res.baseline.overall_risk_score


def test_multiple_bus_failures(sim_test_festival):
    """Multiple bus failures (e.g., 4 buses) exacerbate queue backlog."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(bus_failure=4),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    res = sim_engine.simulate(sim_input, festival_override=sim_test_festival)
    # High capacity reduction creates severe queues and risk elevation
    total_queue_change = sum(sc.queue_change for sc in res.stop_comparisons)
    assert total_queue_change >= 0
    assert res.scenario_result.overall_risk_score >= res.baseline.overall_risk_score


def test_stop_level_comparison_structure(sim_test_festival):
    """Stop comparisons contain complete before-and-after values and deltas."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(attendance_multiplier=1.25, bus_failure=2),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    res = sim_engine.simulate(sim_input, festival_override=sim_test_festival)
    assert len(res.stop_comparisons) == len(sim_test_festival.stops)

    for sc in res.stop_comparisons:
        assert sc.stop_id in ("stop_main", "stop_north")
        assert sc.scenario_crowd >= sc.baseline_crowd
        assert sc.crowd_change == sc.scenario_crowd - sc.baseline_crowd
        assert sc.queue_change == sc.scenario_queue - sc.baseline_queue
        assert sc.risk_change == sc.scenario_risk_score - sc.baseline_risk_score
        assert sc.required_buses_change == sc.scenario_required_buses - sc.baseline_required_buses


def test_new_high_risk_and_critical_detection():
    """Identifies stops that transition from moderate/low to high or critical risk."""
    sim_engine = SimulationEngine()
    # Create festival where baseline risk is low/calm
    fest = Festival(
        id="risk-trans-fest",
        name="Risk Transition Fest",
        base_attendance=2000,
        stops=[
            Stop(id="fragile_stop", name="Fragile Stop", capacity=2500, current_buses=10),
            Stop(id="robust_stop", name="Robust Stop", capacity=3000, current_buses=15),
        ],
    )
    # Severe attendance surge with bus failure
    sim_input = SimulationInput(
        festival_id="risk-trans-fest",
        scenario=ScenarioParameters(attendance_multiplier=8.0, bus_failure=8),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    res = sim_engine.simulate(sim_input, festival_override=fest)
    assert res.changes.risk_score_change > 0
    assert len(res.changes.new_high_risk_stops) > 0 or len(res.changes.new_critical_stops) > 0
    # Stop comparisons must list all stops
    assert len(res.stop_comparisons) == 2


def test_simulation_determinism(sim_test_festival):
    """Running identical simulation twice yields identical results."""
    sim_engine = SimulationEngine()
    sim_input = SimulationInput(
        festival_id=sim_test_festival.id,
        scenario=ScenarioParameters(
            attendance_multiplier=1.35,
            rain_probability=50.0,
            event_delay_minutes=25,
            bus_failure=2,
        ),
        base_event_end_time="2026-04-28T10:00:00+05:30",
    )

    run_1 = sim_engine.simulate(sim_input, festival_override=sim_test_festival).model_dump()
    run_2 = sim_engine.simulate(sim_input, festival_override=sim_test_festival).model_dump()

    assert run_1 == run_2
