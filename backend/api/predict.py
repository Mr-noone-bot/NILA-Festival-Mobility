"""
NILA Crowd Prediction API Endpoint
POST /api/predict — Executes deterministic crowd prediction engine.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status

from backend.api.schemas import (
    PredictionRequest,
    PredictionResponse,
    TimelineStep,
    StopForecast,
)
from backend.prediction.engine import PredictionEngine
from backend.prediction.models import PredictionInput, RiskLevel

router = APIRouter(tags=["Crowd Prediction"])
_prediction_engine = PredictionEngine()


@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
async def predict_crowd(request: PredictionRequest) -> PredictionResponse:
    """
    Generates temporal crowd surge estimates based on festival schedule,
    event timeline, and environmental factors.
    """
    try:
        # Determine attendance multiplier
        att_mult = request.attendance_multiplier
        if att_mult is None:
            att_mult = request.surge_multiplier if request.surge_multiplier > 0 else 1.0

        # Determine rain probability
        rain_prob = request.rain_probability or 0.0
        if "rain" in request.weather_condition.lower() and rain_prob == 0.0:
            rain_prob = 70.0

        pred_input = PredictionInput(
            festival_id=request.festival_id,
            time_window_start=request.time_window_start,
            time_window_end=request.time_window_end,
            attendance_multiplier=att_mult,
            rain_probability=rain_prob,
            weather_condition=request.weather_condition,
            event_end_time=request.event_end_time,
            bus_capacity=request.bus_capacity or 50,
            load_factor=request.load_factor or 0.85,
            interval_minutes=request.interval_minutes or 15,
        )

        result = _prediction_engine.predict(pred_input)

        # Index stop forecasts by timestamp for discharge rate calculation
        departures_by_time: Dict[str, int] = {}
        stop_peaks: Dict[str, Any] = {}

        for sf in result.stop_forecast:
            t = sf.timestamp
            departures_by_time[t] = departures_by_time.get(t, 0) + sf.departures

            # Track peak crowd point for each stop
            prev = stop_peaks.get(sf.stop_id)
            if not prev or sf.predicted_crowd > prev.predicted_crowd:
                stop_peaks[sf.stop_id] = sf

        # Build timeline
        timeline_steps: List[TimelineStep] = []
        for tp in result.timeline:
            # 15-minute departures scaled to hourly discharge rate
            dep_15m = departures_by_time.get(tp.timestamp, 0)
            discharge_rate = dep_15m * 4

            # Surge alert level mapping
            if result.peak_crowd > 0:
                ratio = tp.total_crowd / result.peak_crowd
                if ratio >= 0.85:
                    alert = "CRITICAL"
                elif ratio >= 0.65:
                    alert = "HIGH"
                elif ratio >= 0.45:
                    alert = "MODERATE"
                elif ratio >= 0.25:
                    alert = "MEDIUM"
                else:
                    alert = "LOW"
            else:
                alert = "LOW"

            timeline_steps.append(
                TimelineStep(
                    timestamp=tp.timestamp,
                    total_crowd_estimate=tp.total_crowd,
                    discharge_rate_per_hour=discharge_rate,
                    surge_alert_level=alert,
                )
            )

        # Build stop forecasts
        stop_forecasts: List[StopForecast] = []
        for stop_id, peak_point in stop_peaks.items():
            # Estimate waiting minutes from queue and departure rate
            hourly_rate = max(1, peak_point.departures * 4)
            wait_min = round((peak_point.queue / hourly_rate) * 60.0, 1) if peak_point.queue > 0 else 5.0
            wait_min = min(120.0, max(2.0, wait_min))

            stop_forecasts.append(
                StopForecast(
                    stop_id=stop_id,
                    predicted_demand=peak_point.predicted_crowd,
                    waiting_minutes=wait_min,
                    risk_level=peak_point.risk_level,
                    queue=peak_point.queue,
                    required_buses=peak_point.required_buses,
                    crowd_pressure=peak_point.crowd_pressure,
                    risk_score=peak_point.risk_score,
                )
            )

        # Raw stop forecast dicts for direct backend optimizer compatibility
        raw_stop_forecasts = [sf.model_dump() for sf in result.stop_forecast]

        return PredictionResponse(
            festival_id=result.festival_id,
            timeline=timeline_steps,
            peak_surge_time=result.peak_time,
            peak_crowd=result.peak_crowd,
            highest_demand_stops=result.risk_summary.high_risk_stops,
            stop_forecasts=stop_forecasts,
            stop_forecast=raw_stop_forecasts,
        )

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction engine error: {exc}",
        ) from exc
