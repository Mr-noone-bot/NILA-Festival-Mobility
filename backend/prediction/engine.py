"""
NILA Prediction Engine
Core orchestrator for deterministic crowd prediction, stop distributions,
queue accumulation, and risk evaluation.
Owned by: Gugaan
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

from backend.prediction.models import (
    PredictionInput,
    PredictionResult,
    TimelinePoint,
    StopForecastPoint,
    RiskSummary,
    Festival,
    Stop,
)
from backend.prediction.data_loader import get_festival
from backend.prediction.factors import (
    festival_intensity_factor,
    day_factor,
    time_of_day_factor,
    compute_event_timing,
    event_end_factor,
    event_outbound_rate,
    weather_factor,
    weather_transit_rush_multiplier,
)
from backend.prediction.distribution import distribute_crowd_to_stops
from backend.prediction.queue import StopQueueTracker
from backend.prediction.demand import (
    calculate_effective_bus_capacity,
    calculate_passenger_arrivals,
    calculate_service_capacity,
    calculate_actual_departures,
    calculate_required_buses,
)
from backend.prediction.risk import (
    calculate_crowd_pressure,
    calculate_risk_score,
    risk_level_from_score,
    calculate_network_risk,
)

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


def _parse_or_default_time(
    iso_or_time_str: Optional[str],
    reference_date: datetime,
    default_hour: int,
    default_minute: int
) -> datetime:
    """
    Parses an ISO-8601 string or HH:MM string into a timezone-aware datetime in Asia/Kolkata.
    """
    if not iso_or_time_str:
        return reference_date.replace(
            hour=default_hour,
            minute=default_minute,
            second=0,
            microsecond=0,
            tzinfo=KOLKATA_TZ
        )

    try:
        # Try full ISO-8601 format
        dt = datetime.fromisoformat(iso_or_time_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=KOLKATA_TZ)
        return dt.astimezone(KOLKATA_TZ)
    except ValueError:
        # Try HH:MM format
        parts = iso_or_time_str.strip().split(":")
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return reference_date.replace(
            hour=h,
            minute=m,
            second=0,
            microsecond=0,
            tzinfo=KOLKATA_TZ
        )


def generate_time_intervals(
    start_time: datetime,
    end_time: datetime,
    step_minutes: int = 15
) -> List[datetime]:
    """Generates continuous 15-minute interval datetimes between start and end."""
    intervals: List[datetime] = []
    current = start_time
    delta = timedelta(minutes=step_minutes)
    while current <= end_time:
        intervals.append(current)
        current += delta
    return intervals


class PredictionEngine:
    """
    Deterministic crowd prediction engine for festival mobility management.
    """

    def predict(
        self,
        config: PredictionInput,
        festival_override: Optional[Festival] = None
    ) -> PredictionResult:
        """
        Executes full deterministic crowd prediction pipeline.
        
        Args:
            config: User-provided PredictionInput configuration.
            festival_override: Optional in-memory Festival model for testing.
            
        Returns:
            PredictionResult matching the shared NILA API contract.
        """
        # 1. Load Festival
        festival = festival_override if festival_override else get_festival(config.festival_id)
        if not festival.stops:
            raise ValueError(f"Festival '{festival.id}' has no configured transport stops.")

        # 2. Establish Reference & Event Timings
        # Default reference date: 2026-04-28 (Chithirai / SAKTHI HACKFEST reference window)
        ref_date = datetime(2026, 4, 28, tzinfo=KOLKATA_TZ)
        
        # Primary event end time determination
        event_end_dt: datetime
        if config.event_end_time:
            event_end_dt = _parse_or_default_time(config.event_end_time, ref_date, 10, 0)
        elif festival.peak_events:
            event_end_dt = _parse_or_default_time(festival.peak_events[0].end_time, ref_date, 10, 0)
        else:
            event_end_dt = ref_date.replace(hour=10, minute=0, second=0, microsecond=0)

        # Time window determination
        window_start_dt = _parse_or_default_time(
            config.time_window_start,
            event_end_dt - timedelta(hours=3),
            event_end_dt.hour - 3,
            0
        )
        window_end_dt = _parse_or_default_time(
            config.time_window_end,
            event_end_dt + timedelta(hours=5),
            event_end_dt.hour + 5,
            0
        )

        if window_start_dt >= window_end_dt:
            raise ValueError("time_window_start must be strictly earlier than time_window_end.")

        intervals = generate_time_intervals(
            window_start_dt,
            window_end_dt,
            step_minutes=config.interval_minutes
        )

        # 3. Static Multipliers
        intensity = festival_intensity_factor(festival.intensity)
        w_factor = weather_factor(config.rain_probability, config.weather_condition)
        w_rush = weather_transit_rush_multiplier(config.rain_probability)
        att_multiplier = config.attendance_multiplier
        eff_bus_cap = calculate_effective_bus_capacity(config.bus_capacity, config.load_factor)

        # Initialize tracking structures
        timeline: List[TimelinePoint] = []
        stop_forecasts: List[StopForecastPoint] = []
        queue_tracker = StopQueueTracker()
        
        # Track max risk score per stop to calculate overall network risk
        stop_peak_risks: Dict[str, int] = {s.id: 0 for s in festival.stops}

        # 4. Generate 15-Minute Timeline Calculations
        for interval_dt in intervals:
            iso_timestamp = interval_dt.isoformat()
            
            # Event timing & status
            event_status, minutes_since_end = compute_event_timing(interval_dt, event_end_dt)

            # Factors
            d_factor = day_factor(interval_dt.date())
            t_factor = time_of_day_factor(interval_dt)
            e_factor = event_end_factor(minutes_since_end)

            # Total network crowd formula
            total_crowd_float = (
                festival.base_attendance
                * intensity
                * d_factor
                * t_factor
                * e_factor
                * w_factor
                * att_multiplier
            )
            total_crowd = max(0, int(round(total_crowd_float)))

            # Append timeline point
            timeline.append(
                TimelinePoint(
                    timestamp=iso_timestamp,
                    total_crowd=total_crowd,
                    event_status=event_status.value,
                    minutes_since_event_end=minutes_since_end
                )
            )

            # 5. Stop-Level Distribution & Transit Queues
            distributed_crowds = distribute_crowd_to_stops(total_crowd, festival.stops)
            outbound_rate = event_outbound_rate(minutes_since_end)

            for stop in festival.stops:
                pred_crowd = distributed_crowds.get(stop.id, 0)
                
                # Passenger arrivals entering the transit queue in this interval
                arrivals = calculate_passenger_arrivals(
                    predicted_crowd=pred_crowd,
                    outbound_rate=outbound_rate,
                    weather_rush_multiplier=w_rush
                )

                # Prior queue accumulated at stop
                prev_queue = queue_tracker.get_queue(stop.id)
                pending_demand = prev_queue + arrivals

                # Baseline service throughput from stationed vehicles
                serv_cap = calculate_service_capacity(stop.current_buses, eff_bus_cap)
                departures = calculate_actual_departures(pending_demand, serv_cap)

                # Queue evolution: queue(t+1) = max(0, queue(t) + arrivals - departures)
                new_queue = queue_tracker.step(stop.id, arrivals, departures)

                # Theoretical required buses (demand only, no allocation movement)
                req_buses = calculate_required_buses(pending_demand, eff_bus_cap)

                # Pressure & Risk evaluation
                crowd_press = calculate_crowd_pressure(
                    queue=new_queue,
                    stop_capacity=stop.capacity,
                    arrivals=arrivals,
                    service_capacity=serv_cap
                )

                risk_score = calculate_risk_score(
                    crowd_pressure=crowd_press,
                    queue=new_queue,
                    stop_capacity=stop.capacity,
                    minutes_since_event_end=minutes_since_end,
                    rain_probability=config.rain_probability
                )
                risk_lvl = risk_level_from_score(risk_score)

                # Track peak risk for network summary
                if risk_score > stop_peak_risks[stop.id]:
                    stop_peak_risks[stop.id] = risk_score

                stop_forecasts.append(
                    StopForecastPoint(
                        timestamp=iso_timestamp,
                        stop_id=stop.id,
                        predicted_crowd=pred_crowd,
                        arrivals=arrivals,
                        departures=departures,
                        queue=new_queue,
                        required_buses=req_buses,
                        crowd_pressure=crowd_press,
                        risk_score=risk_score,
                        risk_level=risk_lvl.value
                    )
                )

        # 6. Peak Crowd Determination
        peak_point = max(timeline, key=lambda p: p.total_crowd)
        peak_time = peak_point.timestamp
        peak_crowd = peak_point.total_crowd

        # 7. Network-wide Risk Rollup
        net_score, net_level, high_risk_stops = calculate_network_risk(stop_peak_risks)
        risk_summary = RiskSummary(
            overall_risk_score=net_score,
            overall_risk_level=net_level.value,
            high_risk_stops=high_risk_stops
        )

        return PredictionResult(
            festival_id=festival.id,
            timezone="Asia/Kolkata",
            interval_minutes=config.interval_minutes,
            peak_time=peak_time,
            peak_crowd=peak_crowd,
            timeline=timeline,
            stop_forecast=stop_forecasts,
            risk_summary=risk_summary
        )
