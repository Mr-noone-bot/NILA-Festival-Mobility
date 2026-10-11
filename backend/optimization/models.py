"""
NILA Optimization Domain Models
Defines domain structures for buses, stops, candidate moves, and Gugaan forecast records.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from backend.core.constants import BusStatus, RiskLevel, DEFAULT_BUS_CAPACITY, TAMIL_NADU_TIMEZONE


class StopForecastRecord(BaseModel):
    """
    Gugaan's Confirmed Phase 3 Per-Stop Forecast Record.
    """
    timestamp: str = Field(..., description="ISO-8601 with offset (e.g. 2026-10-10T20:15:00+05:30)")
    stop_id: str
    predicted_crowd: int = Field(ge=0)
    arrivals: int = Field(ge=0)
    departures: int = Field(ge=0)
    queue: int = Field(ge=0)
    required_buses: int = Field(ge=0, description="Theoretical bus demand, NOT allocated fleet")
    crowd_pressure: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_offset(cls, v: str) -> str:
        try:
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                raise ValueError(f"Timestamp '{v}' must include explicit timezone offset (e.g. +05:30)")
        except Exception as exc:
            raise ValueError(f"Invalid ISO-8601 timestamp with offset '{v}': {exc}")
        return v


class GugaanForecastPayload(BaseModel):
    """
    Top-level prediction response container from Gugaan's prediction module.
    """
    festival_id: str
    timezone: str = Field(default=TAMIL_NADU_TIMEZONE)
    interval_minutes: int = Field(default=15, ge=1)
    peak_time: Optional[str] = None
    peak_crowd: Optional[int] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    stop_forecast: List[StopForecastRecord] = Field(
        ...,
        description="Gugaan's confirmed stop-level forecast array"
    )
    risk_summary: Optional[Dict[str, Any]] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if v not in (TAMIL_NADU_TIMEZONE, "UTC+05:30", "+05:30"):
            raise ValueError(f"Timezone must be '{TAMIL_NADU_TIMEZONE}', got '{v}'")
        return v


class BusEntity(BaseModel):
    """Represents a physical vehicle in the transit authority inventory."""
    vehicle_id: str
    current_stop_id: str
    status: BusStatus = BusStatus.ACTIVE
    capacity: Optional[int] = Field(default=None, ge=10, le=150)
    assigned_until: Optional[str] = None  # ISO-8601 timestamp for active commitment


class StopOperationalState(BaseModel):
    """Represents the operational state of a single bus terminal."""
    stop_id: str
    name: Optional[str] = None
    allocated_buses: int = Field(ge=0)
    demand_passengers: int = Field(ge=0)
    min_service_buses: int = Field(default=1, ge=0)
    max_staging_buses: Optional[int] = Field(default=None, ge=1)
    lat: Optional[float] = None
    lng: Optional[float] = None
