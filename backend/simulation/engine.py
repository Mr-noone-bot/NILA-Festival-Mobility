"""
NILA Simulation Engine
Orchestrates comparative what-if scenario simulations wrapping the Prediction Engine.
Owned by: Gugaan
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from zoneinfo import ZoneInfo

from backend.prediction.models import Festival, PredictionInput, PredictionResult
from backend.prediction.engine import PredictionEngine, KOLKATA_TZ
from backend.prediction.data_loader import get_festival
from backend.prediction.risk import risk_level_from_score
from backend.simulation.models import (
    SimulationInput,
    SimulationResult,
    BaselineSummary,
    ScenarioSummary,
    ChangeMetrics,
    StopComparison,
)


def _shift_event_time(
    base_time_str: Optional[str],
    festival: Festival,
    delay_minutes: int
) -> str:
    """
    Shifts the major event end time forward by delay_minutes,
    returning an ISO-8601 string.
    """
    ref_date = datetime(2026, 4, 28, tzinfo=KOLKATA_TZ)

    # 1. Determine base datetime
    if base_time_str:
        try:
            dt = datetime.fromisoformat(base_time_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=KOLKATA_TZ)
            else:
                dt = dt.astimezone(KOLKATA_TZ)
        except ValueError:
            parts = base_time_str.strip().split(":")
            dt = ref_date.replace(hour=int(parts[0]), minute=int(parts[1]) if len(parts) > 1 else 0)
    elif festival.peak_events and festival.peak_events[0].end_time:
        try:
            dt = datetime.fromisoformat(festival.peak_events[0].end_time)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=KOLKATA_TZ)
            else:
                dt = dt.astimezone(KOLKATA_TZ)
        except ValueError:
            parts = festival.peak_events[0].end_time.strip().split(":")
            dt = ref_date.replace(hour=int(parts[0]), minute=int(parts[1]) if len(parts) > 1 else 0)
    else:
        dt = ref_date.replace(hour=10, minute=0, second=0, microsecond=0)

    # 2. Apply delay
    delayed_dt = dt + timedelta(minutes=delay_minutes)
    return delayed_dt.isoformat()


def _apply_bus_failure(
    festival: Festival,
    bus_failure: int,
    failed_stop_id: Optional[str] = None
) -> Festival:
    """
    Creates a deep copy of festival with reduced available buses
    to simulate mechanical breakdown or route blockage.
    
    Preserves fixed-fleet principle: does not move or invent buses.
    """
    cloned_festival = festival.model_copy(deep=True)
    if bus_failure <= 0 or not cloned_festival.stops:
        return cloned_festival

    if failed_stop_id:
        # Deduct from specific requested stop
        target_stop = next((s for s in cloned_festival.stops if s.id == failed_stop_id), None)
        if target_stop:
            target_stop.current_buses = max(0, target_stop.current_buses - bus_failure)
    else:
        # Deduct fleet-wide starting from stop with highest available buses
        remaining_to_deduct = bus_failure
        # Sort stops deterministically by available buses descending, then by ID
        sorted_stops = sorted(
            cloned_festival.stops,
            key=lambda s: (s.current_buses, s.id),
            reverse=True
        )
        for stop in sorted_stops:
            if remaining_to_deduct <= 0:
                break
            deduct = min(stop.current_buses, remaining_to_deduct)
            stop.current_buses -= deduct
            remaining_to_deduct -= deduct

    # Update default fleet size to reflect failure
    cloned_festival.default_fleet_size = max(
        0, cloned_festival.default_fleet_size - bus_failure
    )
    return cloned_festival


class SimulationEngine:
    """
    Evaluates what-if operational scenarios against baseline predictions.
    Reuses PredictionEngine without duplicating prediction mathematics.
    """

    def __init__(self, prediction_engine: Optional[PredictionEngine] = None):
        self.prediction_engine = prediction_engine if prediction_engine else PredictionEngine()

    def simulate(
        self,
        sim_input: SimulationInput,
        festival_override: Optional[Festival] = None
    ) -> SimulationResult:
        """
        Executes comparative simulation:
        1. Run baseline prediction.
        2. Run scenario prediction with modified inputs.
        3. Compare peak crowd, risk, queues, and stop-level deltas.
        """
        # 1. Resolve festival
        base_festival = (
            festival_override if festival_override else get_festival(sim_input.festival_id)
        )
        scenario = sim_input.scenario

        # 2. Run Baseline Prediction
        baseline_input = PredictionInput(
            festival_id=base_festival.id,
            time_window_start=sim_input.time_window_start,
            time_window_end=sim_input.time_window_end,
            attendance_multiplier=1.0,
            rain_probability=0.0,
            event_end_time=sim_input.base_event_end_time,
        )
        baseline_pred = self.prediction_engine.predict(
            baseline_input, festival_override=base_festival
        )

        # 3. Prepare Scenario Inputs & Modifications
        # A. Event delay
        scenario_event_end = _shift_event_time(
            sim_input.base_event_end_time,
            base_festival,
            scenario.event_delay_minutes
        )

        # B. Bus failure (capacity reduction)
        scenario_festival = _apply_bus_failure(
            base_festival,
            scenario.bus_failure,
            scenario.failed_stop_id
        )

        # C. Scenario prediction input
        scenario_pred_input = PredictionInput(
            festival_id=base_festival.id,
            time_window_start=sim_input.time_window_start,
            time_window_end=sim_input.time_window_end,
            attendance_multiplier=scenario.attendance_multiplier,
            rain_probability=scenario.rain_probability,
            event_end_time=scenario_event_end,
        )
        scenario_pred = self.prediction_engine.predict(
            scenario_pred_input, festival_override=scenario_festival
        )

        # 4. Compute Aggregate Changes
        peak_crowd_change = scenario_pred.peak_crowd - baseline_pred.peak_crowd
        peak_change_pct = round(
            (peak_crowd_change / max(1, baseline_pred.peak_crowd)) * 100.0, 2
        )
        risk_score_change = (
            scenario_pred.risk_summary.overall_risk_score
            - baseline_pred.risk_summary.overall_risk_score
        )

        # 5. Stop-Level Comparisons
        stop_comparisons: List[StopComparison] = []
        new_high_risk: List[str] = []
        new_critical: List[str] = []

        # Map stop forecast points by stop_id
        base_by_stop: Dict[str, List] = {}
        for pt in baseline_pred.stop_forecast:
            base_by_stop.setdefault(pt.stop_id, []).append(pt)

        scen_by_stop: Dict[str, List] = {}
        for pt in scenario_pred.stop_forecast:
            scen_by_stop.setdefault(pt.stop_id, []).append(pt)

        for stop in base_festival.stops:
            s_id = stop.id
            b_pts = base_by_stop.get(s_id, [])
            sc_pts = scen_by_stop.get(s_id, [])

            # Extract peak metrics for the stop
            b_crowd = max((p.predicted_crowd for p in b_pts), default=0)
            sc_crowd = max((p.predicted_crowd for p in sc_pts), default=0)

            b_queue = max((p.queue for p in b_pts), default=0)
            sc_queue = max((p.queue for p in sc_pts), default=0)

            b_risk = max((p.risk_score for p in b_pts), default=0)
            sc_risk = max((p.risk_score for p in sc_pts), default=0)

            b_buses = max((p.required_buses for p in b_pts), default=0)
            sc_buses = max((p.required_buses for p in sc_pts), default=0)

            b_level = risk_level_from_score(b_risk).value
            sc_level = risk_level_from_score(sc_risk).value

            # Identify newly elevated risk categories
            if b_risk < 61 and sc_risk >= 61:
                new_high_risk.append(s_id)
            if b_risk < 81 and sc_risk >= 81:
                new_critical.append(s_id)

            stop_comparisons.append(
                StopComparison(
                    stop_id=s_id,
                    baseline_crowd=b_crowd,
                    scenario_crowd=sc_crowd,
                    crowd_change=sc_crowd - b_crowd,
                    baseline_queue=b_queue,
                    scenario_queue=sc_queue,
                    queue_change=sc_queue - b_queue,
                    baseline_risk_score=b_risk,
                    scenario_risk_score=sc_risk,
                    risk_change=sc_risk - b_risk,
                    baseline_risk_level=b_level,
                    scenario_risk_level=sc_level,
                    baseline_required_buses=b_buses,
                    scenario_required_buses=sc_buses,
                    required_buses_change=sc_buses - b_buses,
                )
            )

        # Sort stop comparisons deterministically by ID
        stop_comparisons.sort(key=lambda sc: sc.stop_id)

        # 6. Assemble Result
        return SimulationResult(
            festival_id=base_festival.id,
            scenario=scenario,
            baseline=BaselineSummary(
                peak_time=baseline_pred.peak_time,
                peak_crowd=baseline_pred.peak_crowd,
                overall_risk_score=baseline_pred.risk_summary.overall_risk_score,
                overall_risk_level=baseline_pred.risk_summary.overall_risk_level,
            ),
            scenario_result=ScenarioSummary(
                peak_time=scenario_pred.peak_time,
                peak_crowd=scenario_pred.peak_crowd,
                overall_risk_score=scenario_pred.risk_summary.overall_risk_score,
                overall_risk_level=scenario_pred.risk_summary.overall_risk_level,
            ),
            changes=ChangeMetrics(
                peak_crowd_change=peak_crowd_change,
                peak_crowd_change_percent=peak_change_pct,
                risk_score_change=risk_score_change,
                new_high_risk_stops=sorted(new_high_risk),
                new_critical_stops=sorted(new_critical),
            ),
            stop_comparisons=stop_comparisons,
        )
