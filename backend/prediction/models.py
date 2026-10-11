"""
NILA Prediction Models
Data models and typed schemas for the crowd prediction engine.
Owned by: Gugaan
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventStatus(str, Enum):
    PRE_EVENT = "pre_event"
    EVENT_ACTIVE = "event_active"
    POST_EVENT = "post_event"


class Stop(BaseModel):
    """Transport stop definition."""
    id: str
    name: str
    capacity: int = Field(default=1500, description="Safe passenger holding capacity")
    weight: Optional[float] = Field(default=None, description="Spatial catchment distribution weight")
    current_buses: int = Field(default=0, description="Baseline stationed buses at stop")
    coordinates: Optional[Dict[str, float]] = None


class FestivalEvent(BaseModel):
    """Key ritual or festival milestone event."""
    name: str
    start_time: Optional[str] = None
    end_time: str
    estimated_turnout: int = Field(default=100000, gt=0)


class Festival(BaseModel):
    """Festival configuration and metadata."""
    id: str
    name: str
    city: str = "Tamil Nadu"
    base_attendance: int = Field(default=100000, gt=0)
    intensity: float = Field(default=1.0, gt=0)
    peak_events: List[FestivalEvent] = Field(default_factory=list)
    stops: List[Stop] = Field(default_factory=list)
    default_fleet_size: int = Field(default=20, gt=0)


class PredictionInput(BaseModel):
    """Configuration input for running crowd prediction."""
    festival_id: str
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    attendance_multiplier: float = Field(default=1.0, gt=0.0, description="Multiplier for crowd scale (> 0)")
    rain_probability: float = Field(default=0.0, ge=0.0, le=100.0, description="Rain percentage [0, 100]")
    weather_condition: str = Field(default="clear", description="clear | moderate_rain | heavy_rain | extreme_heat")
    event_end_time: Optional[str] = Field(default=None, description="ISO timestamp or HH:MM for main event end")
    bus_capacity: int = Field(default=50, gt=0, description="Nominal bus passenger capacity")
    load_factor: float = Field(default=0.85, gt=0.0, le=1.5, description="Effective load factor")
    interval_minutes: int = Field(default=15, gt=0, description="Timeline discretization step")

    @field_validator("attendance_multiplier")
    @classmethod
    def validate_attendance_multiplier(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("attendance_multiplier must be strictly positive")
        return v

    @field_validator("rain_probability")
    @classmethod
    def validate_rain_probability(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError("rain_probability must be between 0.0 and 100.0")
        return v


class TimelinePoint(BaseModel):
    """Total crowd estimate at a single 15-minute interval."""
    timestamp: str
    total_crowd: int
    event_status: str
    minutes_since_event_end: int


class StopForecastPoint(BaseModel):
    """Detailed forecast metrics for a specific transport stop at a 15-minute interval."""
    timestamp: str
    stop_id: str
    predicted_crowd: int
    arrivals: int
    departures: int
    queue: int
    required_buses: int
    crowd_pressure: float
    risk_score: int
    risk_level: str


class RiskSummary(BaseModel):
    """Network-wide risk roll-up summary."""
    overall_risk_score: int
    overall_risk_level: str
    high_risk_stops: List[str]


class PredictionResult(BaseModel):
    """Output contract produced by the NILA Prediction Engine."""
    festival_id: str
    timezone: str = "Asia/Kolkata"
    interval_minutes: int = 15
    peak_time: str
    peak_crowd: int
    timeline: List[TimelinePoint]
    stop_forecast: List[StopForecastPoint]
    risk_summary: RiskSummary
