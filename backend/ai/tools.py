"""
NILA AI Tools Module
Authoritative backend tool registry providing ground truth data to Gemini.
Reuses PredictionEngine and SimulationEngine. Never invents numbers.
Owned by: Gugaan
"""

from typing import Optional, Dict, Any
from backend.prediction.models import PredictionInput
from backend.prediction.engine import PredictionEngine
from backend.prediction.data_loader import get_festival, DataLoaderError
from backend.simulation.models import SimulationInput, ScenarioParameters
from backend.simulation.engine import SimulationEngine
from backend.ai.schemas import ToolExecutionResult


class NilaTools:
    """
    Authoritative backend execution tools for NILA.
    """

    def __init__(
        self,
        prediction_engine: Optional[PredictionEngine] = None,
        simulation_engine: Optional[SimulationEngine] = None
    ):
        self.prediction_engine = prediction_engine if prediction_engine else PredictionEngine()
        self.simulation_engine = simulation_engine if simulation_engine else SimulationEngine(self.prediction_engine)

    def get_festival_details(self, festival_id: str) -> ToolExecutionResult:
        """
        Retrieves authoritative festival and transport infrastructure details.
        """
        try:
            festival = get_festival(festival_id)
            data = {
                "id": festival.id,
                "name": festival.name,
                "city": festival.city,
                "base_attendance": festival.base_attendance,
                "intensity": festival.intensity,
                "default_fleet_size": festival.default_fleet_size,
                "stops": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "capacity": s.capacity,
                        "current_buses": s.current_buses,
                    }
                    for s in festival.stops
                ],
                "peak_events": [
                    {
                        "name": pe.name,
                        "start_time": pe.start_time,
                        "end_time": pe.end_time,
                        "estimated_turnout": pe.estimated_turnout,
                    }
                    for pe in festival.peak_events
                ],
            }
            return ToolExecutionResult(
                tool_name="get_festival_details",
                status="success",
                data=data
            )
        except DataLoaderError as e:
            return ToolExecutionResult(
                tool_name="get_festival_details",
                status="error",
                error=f"Festival not found: {str(e)}"
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name="get_festival_details",
                status="error",
                error=f"Error retrieving festival: {str(e)}"
            )

    def get_crowd_forecast(
        self,
        festival_id: str,
        attendance_multiplier: float = 1.0,
        rain_probability: float = 0.0,
        event_end_time: Optional[str] = None
    ) -> ToolExecutionResult:
        """
        Runs the deterministic PredictionEngine and returns crowd surge forecast.
        """
        try:
            config = PredictionInput(
                festival_id=festival_id,
                attendance_multiplier=max(0.1, float(attendance_multiplier)),
                rain_probability=max(0.0, min(100.0, float(rain_probability))),
                event_end_time=event_end_time
            )
            result = self.prediction_engine.predict(config)
            
            data = {
                "festival_id": result.festival_id,
                "peak_time": result.peak_time,
                "peak_crowd": result.peak_crowd,
                "interval_minutes": result.interval_minutes,
                "overall_risk_score": result.risk_summary.overall_risk_score,
                "overall_risk_level": result.risk_summary.overall_risk_level,
                "timeline_samples": [
                    {
                        "timestamp": pt.timestamp,
                        "total_crowd": pt.total_crowd,
                        "event_status": pt.event_status,
                        "minutes_since_event_end": pt.minutes_since_event_end,
                    }
                    for pt in result.timeline[::2]  # sample every 30m for conciseness
                ],
            }
            return ToolExecutionResult(
                tool_name="get_crowd_forecast",
                status="success",
                data=data
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name="get_crowd_forecast",
                status="error",
                error=f"Prediction error: {str(e)}"
            )

    def get_risk_analysis(self, festival_id: str) -> ToolExecutionResult:
        """
        Evaluates stop-level queues, crowd pressure, and network bottleneck risk.
        """
        try:
            config = PredictionInput(festival_id=festival_id)
            result = self.prediction_engine.predict(config)
            
            # Group peak metrics by stop
            stop_summary: Dict[str, Dict[str, Any]] = {}
            for sf in result.stop_forecast:
                s_id = sf.stop_id
                if s_id not in stop_summary or sf.risk_score > stop_summary[s_id]["peak_risk_score"]:
                    stop_summary[s_id] = {
                        "stop_id": s_id,
                        "peak_risk_score": sf.risk_score,
                        "peak_risk_level": sf.risk_level,
                        "peak_queue": sf.queue,
                        "peak_crowd_pressure": sf.crowd_pressure,
                        "peak_required_buses": sf.required_buses,
                        "peak_arrivals": sf.arrivals,
                        "timestamp_at_peak": sf.timestamp
                    }

            critical_stops = [
                s_id for s_id, s in stop_summary.items() if s["peak_risk_level"] == "CRITICAL"
            ]

            data = {
                "festival_id": result.festival_id,
                "peak_time": result.peak_time,
                "peak_crowd": result.peak_crowd,
                "overall_risk_score": result.risk_summary.overall_risk_score,
                "overall_risk_level": result.risk_summary.overall_risk_level,
                "high_risk_stops": result.risk_summary.high_risk_stops,
                "critical_stops": critical_stops,
                "stops": list(stop_summary.values())
            }
            return ToolExecutionResult(
                tool_name="get_risk_analysis",
                status="success",
                data=data
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name="get_risk_analysis",
                status="error",
                error=f"Risk analysis error: {str(e)}"
            )

    def simulate_scenario(
        self,
        festival_id: str,
        attendance_multiplier: float = 1.0,
        rain_probability: float = 0.0,
        event_delay_minutes: int = 0,
        bus_failure: int = 0,
        failed_stop_id: Optional[str] = None
    ) -> ToolExecutionResult:
        """
        Evaluates a what-if scenario comparison against baseline using SimulationEngine.
        """
        try:
            scenario_params = ScenarioParameters(
                attendance_multiplier=max(0.1, float(attendance_multiplier)),
                rain_probability=max(0.0, min(100.0, float(rain_probability))),
                event_delay_minutes=max(0, int(event_delay_minutes)),
                bus_failure=max(0, int(bus_failure)),
                failed_stop_id=failed_stop_id
            )
            sim_input = SimulationInput(
                festival_id=festival_id,
                scenario=scenario_params
            )
            res = self.simulation_engine.simulate(sim_input)

            data = {
                "festival_id": res.festival_id,
                "scenario": res.scenario.model_dump(),
                "baseline": res.baseline.model_dump(),
                "scenario_result": res.scenario_result.model_dump(),
                "changes": res.changes.model_dump(),
                "stop_comparisons": [sc.model_dump() for sc in res.stop_comparisons]
            }
            return ToolExecutionResult(
                tool_name="simulate_scenario",
                status="success",
                data=data
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name="simulate_scenario",
                status="error",
                error=f"Simulation error: {str(e)}"
            )

    def get_current_plan(self, festival_id: str) -> ToolExecutionResult:
        """
        Adapter interface for the upcoming OptimizationEngine.
        Does NOT invent fake optimization schedules.
        """
        return ToolExecutionResult(
            tool_name="get_current_plan",
            status="unavailable",
            data={
                "festival_id": festival_id,
                "plan_available": False,
                "message": (
                    "No active bus redistribution plan computed. The optimization engine "
                    "(Phase 4 / Sanjay) enforces the fixed-fleet constraint to schedule bus movements."
                )
            }
        )

    def get_tradeoffs(self, festival_id: str, plan_id: Optional[str] = None) -> ToolExecutionResult:
        """
        Adapter interface for vehicle repositioning trade-offs.
        Does NOT invent fake vehicle transfers.
        """
        return ToolExecutionResult(
            tool_name="get_tradeoffs",
            status="unavailable",
            data={
                "festival_id": festival_id,
                "plan_id": plan_id,
                "tradeoffs_available": False,
                "message": (
                    "Fleet movement trade-off data is currently unavailable. "
                    "When an optimization plan is generated, trade-offs between source service loss "
                    "and destination queue relief will be reported."
                )
            }
        )
