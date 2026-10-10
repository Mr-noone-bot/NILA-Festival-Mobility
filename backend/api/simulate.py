"""
NILA Scenario Simulation API Endpoint
POST /api/simulate — Executes what-if scenario simulation engine.
"""

import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status

from backend.api.schemas import (
    SimulationRequest,
    SimulationResponse,
    SimulationStep,
    StopQueueStatus,
    SimulationDensityPoint,
)
from backend.simulation.engine import SimulationEngine
from backend.simulation.models import SimulationInput, ScenarioParameters
from backend.prediction.engine import PredictionEngine
from backend.prediction.data_loader import get_festival

router = APIRouter(tags=["Scenario Simulation"])
_prediction_engine = PredictionEngine()
_simulation_engine = SimulationEngine(prediction_engine=_prediction_engine)


@router.post("/simulate", response_model=SimulationResponse, status_code=status.HTTP_200_OK)
async def simulate_scenario(request: SimulationRequest) -> SimulationResponse:
    """
    Simulates spatial crowd distribution across gates, walking corridors,
    and bus stop accumulation over time under what-if operational parameters.
    """
    try:
        scenario_params = ScenarioParameters(
            attendance_multiplier=request.attendance_multiplier if request.attendance_multiplier else 1.0,
            rain_probability=request.rain_probability if request.rain_probability is not None else 0.0,
            event_delay_minutes=request.event_delay_minutes if request.event_delay_minutes is not None else 0,
            bus_failure=request.bus_failures if request.bus_failures is not None else 0,
            failed_stop_id=request.failed_stop_id,
        )

        sim_input = SimulationInput(
            festival_id=request.festival_id,
            scenario=scenario_params,
        )

        sim_result = _simulation_engine.simulate(sim_input)

        # Retrieve festival metadata for spatial density calculation
        try:
            festival = get_festival(request.festival_id)
        except Exception:
            festival = None

        # Build steps from the scenario prediction
        # To get the timeline steps, re-run or inspect scenario prediction
        from backend.prediction.models import PredictionInput
        from backend.simulation.engine import _shift_event_time, _apply_bus_failure

        base_festival = festival
        if base_festival:
            delayed_event_end = _shift_event_time(
                None, base_festival, scenario_params.event_delay_minutes
            )
            scenario_fest = _apply_bus_failure(
                base_festival, scenario_params.bus_failure, scenario_params.failed_stop_id
            )
            scenario_pred_input = PredictionInput(
                festival_id=base_festival.id,
                attendance_multiplier=scenario_params.attendance_multiplier,
                rain_probability=scenario_params.rain_probability,
                event_end_time=delayed_event_end,
            )
            scenario_pred = _prediction_engine.predict(
                scenario_pred_input, festival_override=scenario_fest
            )
        else:
            scenario_pred = None

        steps: List[SimulationStep] = []
        sim_id = request.prediction_timeline_id or f"sim-{uuid.uuid4().hex[:8]}"

        if scenario_pred:
            # Group stop forecast by timestamp
            sf_by_time: Dict[str, List[Any]] = {}
            for sf in scenario_pred.stop_forecast:
                sf_by_time.setdefault(sf.timestamp, []).append(sf)

            for tp in scenario_pred.timeline:
                stop_forecasts_at_t = sf_by_time.get(tp.timestamp, [])
                stop_queues: Dict[str, StopQueueStatus] = {}

                # Calculate spatial density points for heatmap
                density_points: List[SimulationDensityPoint] = []

                # Core temple centroid (Meenakshi Amman coordinates)
                temple_lat, temple_lng = 9.9195, 78.1193
                base_weight = min(1.0, max(0.1, round(tp.total_crowd / max(1, scenario_pred.peak_crowd), 2)))
                density_points.append(
                    SimulationDensityPoint(latitude=temple_lat, longitude=temple_lng, weight=base_weight)
                )
                # Gates surrounding temple
                density_points.append(SimulationDensityPoint(latitude=temple_lat + 0.002, longitude=temple_lng, weight=round(base_weight * 0.9, 2)))
                density_points.append(SimulationDensityPoint(latitude=temple_lat - 0.002, longitude=temple_lng, weight=round(base_weight * 0.85, 2)))
                density_points.append(SimulationDensityPoint(latitude=temple_lat, longitude=temple_lng + 0.002, weight=round(base_weight * 0.8, 2)))
                density_points.append(SimulationDensityPoint(latitude=temple_lat, longitude=temple_lng - 0.002, weight=round(base_weight * 0.75, 2)))

                for sf in stop_forecasts_at_t:
                    stop_queues[sf.stop_id] = StopQueueStatus(
                        waiting_passengers=sf.queue,
                        queue_risk=sf.risk_level,
                    )
                    # Add density points at stops if coordinates available
                    if base_festival:
                        stop_obj = next((s for s in base_festival.stops if s.id == sf.stop_id), None)
                        if stop_obj and stop_obj.coordinates:
                            s_lat = stop_obj.coordinates.get("lat") or stop_obj.coordinates.get("latitude")
                            s_lng = stop_obj.coordinates.get("lng") or stop_obj.coordinates.get("longitude")
                            if s_lat and s_lng:
                                stop_weight = min(1.0, max(0.1, round(sf.crowd_pressure, 2)))
                                density_points.append(
                                    SimulationDensityPoint(latitude=s_lat, longitude=s_lng, weight=stop_weight)
                                )

                steps.append(
                    SimulationStep(
                        step_time=tp.timestamp,
                        stop_queues=stop_queues,
                        density_grid=density_points,
                    )
                )

        return SimulationResponse(
            simulation_id=sim_id,
            steps=steps,
            baseline=sim_result.baseline.model_dump(),
            scenario=sim_result.scenario_result.model_dump(),
            changes=sim_result.changes.model_dump(),
            stop_comparisons=[sc.model_dump() for sc in sim_result.stop_comparisons],
        )

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario simulation error: {exc}",
        ) from exc
