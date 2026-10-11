"""
NILA AI Tools Module
Authoritative backend tool registry providing ground truth data to Gemini.
Reuses PredictionEngine, SimulationEngine, and the Phase 4 FixedFleetOptimizer.
Never invents numbers. All data originates from deterministic backend engines.
Owned by: Gugaan
"""

from typing import Optional, Dict, Any
from backend.prediction.models import PredictionInput
from backend.prediction.engine import PredictionEngine
from backend.prediction.data_loader import get_festival, DataLoaderError
from backend.simulation.models import SimulationInput, ScenarioParameters
from backend.simulation.engine import SimulationEngine
from backend.optimization.engine import optimize_transport, get_plan_tradeoffs
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
        Runs the Phase 4 FixedFleetOptimizer using real prediction data for the festival.
        Returns the authoritative bus redistribution plan.
        Never invents bus counts, departure times, or allocation figures.
        """
        try:
            festival = get_festival(festival_id)

            # Build current allocation from festival stop definitions
            current_allocation: Dict[str, int] = {
                s.id: s.current_buses for s in festival.stops
            }
            total_fleet = festival.default_fleet_size

            # Run prediction to get per-stop demand forecast
            pred_config = PredictionInput(festival_id=festival_id)
            pred_result = self.prediction_engine.predict(pred_config)

            # Build per-stop peak demand for the optimizer
            stop_demand: Dict[str, int] = {}
            for sf in pred_result.stop_forecast:
                s_id = sf.stop_id
                if s_id not in stop_demand or sf.arrivals > stop_demand[s_id]:
                    stop_demand[s_id] = sf.arrivals

            # Run the deterministic optimizer — no numbers invented
            plan = optimize_transport(
                festival_id=festival_id,
                total_fleet_size=total_fleet,
                current_allocation=current_allocation,
                predicted_demand_profile=stop_demand,
                use_synthetic_capacity_fallback=True,
            )

            moves_summary = [
                {
                    "source_stop": m.source_stop,
                    "destination_stop": m.destination_stop,
                    "buses_to_transfer": m.buses_to_transfer,
                    "departure_time": m.departure_time,
                    "arrival_time": m.arrival_time,
                    "travel_time_minutes": m.travel_time_minutes,
                    "source_service_loss": m.source_service_loss,
                    "expected_benefit": m.expected_benefit,
                    "network_effect": m.network_effect,
                }
                for m in plan.repositioning_moves
            ]

            data: Dict[str, Any] = {
                "festival_id": festival_id,
                "plan_id": plan.plan_id,
                "plan_available": True,
                "total_fleet_size": plan.total_fleet_size,
                "fleet_conserved": plan.fleet_conserved,
                "repositioning_moves": moves_summary,
                "final_allocation": plan.final_allocation,
                "overall_queue_reduction_percentage": plan.overall_queue_reduction_percentage,
                "unserved_demand_before": plan.unserved_demand_before,
                "unserved_demand_after": plan.unserved_demand_after,
                "capacity_provenance": plan.capacity_provenance,
                "warnings": plan.warnings,
                "modeled_assumptions": plan.modeled_assumptions,
                "status": plan.status,
                "message": plan.message,
            }
            return ToolExecutionResult(
                tool_name="get_current_plan",
                status="success",
                data=data
            )
        except DataLoaderError as e:
            return ToolExecutionResult(
                tool_name="get_current_plan",
                status="error",
                error=f"Festival not found: {str(e)}"
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name="get_current_plan",
                status="error",
                error=f"Optimization engine error: {str(e)}"
            )

    def get_tradeoffs(self, festival_id: str, plan_id: Optional[str] = None) -> ToolExecutionResult:
        """
        Runs the Phase 4 optimizer and extracts structured before/after trade-off data
        for every vehicle repositioning decision.
        Never invents wait times, queue figures, or vehicle transfers.
        """
        try:
            festival = get_festival(festival_id)

            current_allocation: Dict[str, int] = {
                s.id: s.current_buses for s in festival.stops
            }
            total_fleet = festival.default_fleet_size

            pred_config = PredictionInput(festival_id=festival_id)
            pred_result = self.prediction_engine.predict(pred_config)

            stop_demand: Dict[str, int] = {}
            for sf in pred_result.stop_forecast:
                s_id = sf.stop_id
                if s_id not in stop_demand or sf.arrivals > stop_demand[s_id]:
                    stop_demand[s_id] = sf.arrivals

            plan = optimize_transport(
                festival_id=festival_id,
                total_fleet_size=total_fleet,
                current_allocation=current_allocation,
                predicted_demand_profile=stop_demand,
                use_synthetic_capacity_fallback=True,
            )

            tradeoff_data = get_plan_tradeoffs(plan)
            tradeoff_data["festival_id"] = festival_id
            tradeoff_data["tradeoffs_available"] = len(plan.repositioning_moves) > 0

            return ToolExecutionResult(
                tool_name="get_tradeoffs",
                status="success",
                data=tradeoff_data
            )
        except DataLoaderError as e:
            return ToolExecutionResult(
                tool_name="get_tradeoffs",
                status="error",
                error=f"Festival not found: {str(e)}"
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name="get_tradeoffs",
                status="error",
                error=f"Trade-off computation error: {str(e)}"
            )
