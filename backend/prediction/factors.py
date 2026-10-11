"""
NILA Prediction Factors
Deterministic, explainable behavioral and environmental factors for crowd prediction.
Owned by: Gugaan
"""

from datetime import datetime, date
import math
from typing import Tuple
from backend.prediction.models import EventStatus


def festival_intensity_factor(intensity: float = 1.0) -> float:
    """
    Returns bounded festival intensity multiplier.
    Baseline is 1.0 (standard festival day).
    Major sacred days (e.g., Chariot, Theerthavari) can be 1.2 - 2.0.
    """
    return max(0.1, float(intensity))


def day_factor(event_date: date) -> float:
    """
    Computes day-of-week multiplier.
    Weekend days experience higher regional pilgrim inflows.
    """
    weekday = event_date.weekday()  # Monday = 0, Sunday = 6
    if weekday in (5, 6):  # Saturday, Sunday
        return 1.20
    elif weekday == 4:     # Friday
        return 1.10
    else:                  # Monday - Thursday
        return 1.00


def time_of_day_factor(dt: datetime) -> float:
    """
    Diurnal temple festival activity curve based on traditional rituals.
    Returns value bounded between 0.1 and 1.0.
    
    Schedule profile:
    - 00:00 - 05:00: Night lull (0.15 - 0.25)
    - 05:00 - 09:00: Morning puja rush (0.35 -> 0.85)
    - 09:00 - 13:00: Midday darshan & offerings (0.85 -> 0.70)
    - 13:00 - 16:00: Afternoon rest period (0.45 - 0.55)
    - 16:00 - 20:30: Evening grand procession / deepam / arti (0.75 -> 1.00)
    - 20:30 - 24:00: Night departure winding down (0.80 -> 0.30)
    """
    hour = dt.hour + (dt.minute / 60.0)

    if hour < 5.0:
        return 0.15 + (hour / 5.0) * 0.10
    elif 5.0 <= hour < 9.0:
        progress = (hour - 5.0) / 4.0
        return 0.25 + progress * 0.60
    elif 9.0 <= hour < 13.0:
        progress = (hour - 9.0) / 4.0
        return 0.85 - progress * 0.15
    elif 13.0 <= hour < 16.0:
        progress = (hour - 13.0) / 3.0
        return 0.70 - progress * 0.20
    elif 16.0 <= hour < 20.5:
        progress = (hour - 16.0) / 4.5
        return 0.50 + progress * 0.50
    else:
        progress = (hour - 20.5) / 3.5
        return 1.00 - progress * 0.70


def compute_event_timing(
    current_time: datetime,
    event_end_time: datetime,
    event_active_duration_minutes: int = 120
) -> Tuple[EventStatus, int]:
    """
    Computes event status and minutes relative to major festival event end.
    
    Returns:
    - event_status: 'pre_event' | 'event_active' | 'post_event'
    - minutes_since_event_end: int (negative before event end, positive after)
    """
    delta_seconds = (current_time - event_end_time).total_seconds()
    minutes_since_end = int(round(delta_seconds / 60.0))

    if minutes_since_end < -event_active_duration_minutes:
        status = EventStatus.PRE_EVENT
    elif -event_active_duration_minutes <= minutes_since_end < 0:
        status = EventStatus.EVENT_ACTIVE
    else:
        status = EventStatus.POST_EVENT

    return status, minutes_since_end


def event_end_factor(minutes_since_event_end: int) -> float:
    """
    Deterministic multiplier representing presence around the festival grounds
    relative to the major event conclusion.
    
    Before event ends (m < 0):
      Crowd accumulates towards climax. Peaks as ritual reaches conclusion.
    Immediately after event ends (m >= 0):
      Ritual concludes; attendees gradually clear the temple perimeter.
    """
    if minutes_since_event_end < 0:
        # Buildup towards climax: rises from 0.70 at -180m to 1.15 at 0m
        lead_time = max(-180, minutes_since_event_end)
        progress = (lead_time + 180) / 180.0
        return 0.70 + 0.45 * progress
    else:
        # Post-event clearance: decays from 1.15 down to 0.20 as pilgrims disperse
        m = minutes_since_event_end
        decay = math.exp(-0.015 * m)
        return max(0.15, 0.20 + 0.95 * decay)


def event_outbound_rate(minutes_since_event_end: int) -> float:
    """
    Fraction of active local crowd attempting to board outbound transit
    in the current 15-minute interval.
    
    - Pre-event / Active (m < 0): steady, low-to-moderate turnover (5% - 8% per interval).
    - Immediately post-event (m = 0 to 45 min): mass egress surge (25% - 32% per interval).
    - Later post-event (m > 60 min): trailing clearance rate (10% - 15%).
    """
    if minutes_since_event_end < -30:
        return 0.06
    elif -30 <= minutes_since_event_end < 0:
        # Pre-exit restlessness before official finish
        progress = (minutes_since_event_end + 30) / 30.0
        return 0.06 + progress * 0.06
    elif 0 <= minutes_since_event_end <= 45:
        # Peak discharge surge immediately upon event completion
        progress = minutes_since_event_end / 45.0
        return 0.30 - progress * 0.10
    elif 45 < minutes_since_event_end <= 120:
        # Secondary wave
        progress = (minutes_since_event_end - 45) / 75.0
        return 0.20 - progress * 0.08
    else:
        # Residual clearance
        return 0.10


def weather_factor(rain_probability: float, weather_condition: str = "clear") -> float:
    """
    Deterministic multiplier on total attendance based on weather conditions.
    Rain suppresses discretionary outdoor foot traffic.
    """
    rain = max(0.0, min(100.0, float(rain_probability)))
    
    # Rain dampening factor
    rain_effect = 1.0 - (rain / 100.0) * 0.22  # at 100% rain, 78% attendance

    condition = weather_condition.lower().strip()
    condition_multiplier = 1.0
    if condition == "heavy_rain":
        condition_multiplier = 0.85
    elif condition == "extreme_heat":
        condition_multiplier = 0.92
    elif condition == "moderate_rain":
        condition_multiplier = 0.95

    return round(rain_effect * condition_multiplier, 4)


def weather_transit_rush_multiplier(rain_probability: float) -> float:
    """
    Multiplier on the transit arrival rate during rain.
    When rain threatens or falls, devotees abandon open-air temple plazas
    and rush to sheltered bus terminals.
    """
    rain = max(0.0, min(100.0, float(rain_probability)))
    return round(1.0 + (rain / 100.0) * 0.35, 4)
