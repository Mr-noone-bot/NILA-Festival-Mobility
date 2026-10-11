"""
NILA Simulation Models
Typed Pydantic schemas for what-if scenario simulations and comparative analysis.
Owned by: Gugaan
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


class ScenarioParameters(BaseModel):
    """Parameters defining a what-if operational scenario."""
    attendance_multiplier: float = Field(
        default=1.0,
        gt=0.0,
        description="Attendance multiplier relative to baseline (> 0)"
    )
    rain_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Rain probability percentage [0, 100]"
    )
    event_delay_minutes: int = Field(
        default=0,
        ge=0,
        description="Delay in minutes for the primary ritual/event conclusion (>= 0)"
    )
    bus_failure: int = Field(
        default=0,
        ge=0,
        description="Number of buses rendered unavailable due to breakdown or obstruction (>= 0)"
    )
    failed_stop_id: Optional[str] = Field(
        default=None,
        description="Optional stop ID where vehicle failure specifically occurs"
    )

    @field_validator("attendance_multiplier")
    @classmethod
    def validate_attendance(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("attendance_multiplier must be strictly positive.")
        return v

    @field_validator("rain_probability")
    @classmethod
    def validate_rain(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError("rain_probability must be between 0.0 and 100.0.")
        return v

    @field_validator("event_delay_minutes")
    @classmethod
    def validate_delay(cls, v: int) -> int:
        if v < 0:
            raise ValueError("event_delay_minutes cannot be negative.")
        return v

    @field_validator("bus_failure")
    @classmethod
    def validate_failure(cls, v: int) -> int:
        if v < 0:
            raise ValueError("bus_failure cannot be negative.")
        return v


class SimulationInput(BaseModel):
    """Input configuration for running a comparative simulation."""
    festival_id: str
    scenario: ScenarioParameters = Field(default_factory=ScenarioParameters)
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    base_event_end_time: Optional[str] = None


class BaselineSummary(BaseModel):
    """Summary of baseline prediction metrics."""
    peak_time: str
    peak_crowd: int
    overall_risk_score: int
    overall_risk_level: str


class ScenarioSummary(BaseModel):
    """Summary of simulated scenario prediction metrics."""
    peak_time: str
    peak_crowd: int
    overall_risk_score: int
    overall_risk_level: str


class ChangeMetrics(BaseModel):
    """Comparative changes between baseline and scenario."""
    peak_crowd_change: int
    peak_crowd_change_percent: float
    risk_score_change: int
    new_high_risk_stops: List[str] = Field(default_factory=list)
    new_critical_stops: List[str] = Field(default_factory=list)


class StopComparison(BaseModel):
    """Detailed stop-level metrics comparison between baseline and scenario."""
    stop_id: str
    baseline_crowd: int
    scenario_crowd: int
    crowd_change: int
    baseline_queue: int
    scenario_queue: int
    queue_change: int
    baseline_risk_score: int
    scenario_risk_score: int
    risk_change: int
    baseline_risk_level: str
    scenario_risk_level: str
    baseline_required_buses: int
    scenario_required_buses: int
    required_buses_change: int


class SimulationResult(BaseModel):
    """Full comparative simulation output contract."""
    festival_id: str
    scenario: ScenarioParameters
    baseline: BaselineSummary
    scenario_result: ScenarioSummary
    changes: ChangeMetrics
    stop_comparisons: List[StopComparison] = Field(default_factory=list)
