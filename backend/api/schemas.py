"""
NILA API Request and Response Schemas
Implements contracts defined in docs/api/contracts.md with rigorous Pydantic v2 validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from backend.core.constants import RouteProvenance, BusStatus, RiskLevel


# ==========================================
# 1. Health Schemas
# ==========================================
class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "nila-backend"
    version: str = "0.1.0"
    environment: str = "foundation"


# ==========================================
# 2. Festival Schemas
# ==========================================
class PeakEvent(BaseModel):
    name: str
    timestamp: str
    estimated_turnout: int = Field(ge=0)


class FestivalSummary(BaseModel):
    id: str
    name: str
    city: str
    temple_id: str
    start_date: str
    end_date: str
    expected_peak_day: str
    peak_events: List[PeakEvent] = Field(default_factory=list)
    is_verified: bool = Field(default=True, description="True if loaded from verified official data")
    provenance: str = Field(default="OFFICIAL_DATA", description="OFFICIAL_DATA or SYNTHETIC_FIXTURE")


class TempleCoordinates(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)


class TempleDetail(BaseModel):
    id: str
    name: str
    coordinates: TempleCoordinates
    gates: List[str] = Field(default_factory=list)


class StopCoordinate(BaseModel):
    lat: float = Field(ge=-90.0, le=90.0)
    lng: float = Field(ge=-180.0, le=180.0)


class StopDetail(BaseModel):
    id: str
    name: str
    capacity: int = Field(ge=0)
    coordinates: StopCoordinate


class FestivalDetail(BaseModel):
    id: str
    name: str
    city: str
    temple: TempleDetail
    stops: List[StopDetail] = Field(default_factory=list)
    default_fleet_size: int = Field(ge=1, default=20)
    is_verified: bool = Field(default=True, description="True if loaded from verified official data")
    provenance: str = Field(default="OFFICIAL_DATA", description="OFFICIAL_DATA or SYNTHETIC_FIXTURE")


# ==========================================
# 3. Routing Schemas
# ==========================================
class CoordinateInput(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")


class RouteRequest(BaseModel):
    origin: CoordinateInput
    destination: CoordinateInput
    congestion_factor: float = Field(default=1.0, ge=0.5, le=5.0, description="Multiplier under pedestrian spillover")


class GeoJSONGeometry(BaseModel):
    type: str = "LineString"
    coordinates: List[List[float]] = Field(
        ...,
        description="GeoJSON coordinates array in [longitude, latitude] order"
    )

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v: List[List[float]]) -> List[List[float]]:
        for point in v:
            if len(point) != 2:
                raise ValueError(f"Each coordinate must be a [longitude, latitude] pair, got {point}")
            lon, lat = point
            if not (-180.0 <= lon <= 180.0):
                raise ValueError(f"Longitude {lon} out of bounds [-180, 180]")
            if not (-90.0 <= lat <= 90.0):
                raise ValueError(f"Latitude {lat} out of bounds [-90, 90]")
        return v


class RouteResponse(BaseModel):
    distance_meters: int = Field(..., ge=0, description="Total route distance in metres")
    duration_seconds: int = Field(..., ge=0, description="Travel duration in seconds")
    duration_formatted: str = Field(..., description="Human-readable duration (e.g., '25 mins')")
    geometry: GeoJSONGeometry
    provenance: RouteProvenance = Field(
        default=RouteProvenance.LIVE_OSRM,
        description="Origin of routing data: LIVE_OSRM, CACHED_OSRM, or FALLBACK_ESTIMATE"
    )
    fallback_warning: Optional[str] = Field(
        default=None,
        description="Explicit limitation details when fallback approximation is used"
    )


# ==========================================
# 4. Fixed-Fleet Optimization Schemas
# ==========================================
class BusInventoryItem(BaseModel):
    vehicle_id: str
    current_stop_id: str
    status: BusStatus = BusStatus.ACTIVE
    capacity: Optional[int] = Field(default=None, ge=10, le=150)
    assigned_until: Optional[str] = None


class TradeoffDetail(BaseModel):
    destination_waiting_reduction_minutes: float = Field(default=0.0, description="Estimated wait reduction at destination (min)")
    source_waiting_increase_minutes: float = Field(default=0.0, description="Estimated wait increase at source (min)")
    reported_delta_minutes: float = Field(default=0.0, description="Net waiting delta: after - before")
    destination_queue_reduction_percentage: float = 0.0
    cleared_passengers: int = 0
    net_passengers_cleared: int = 0


class RepositioningMove(BaseModel):
    source_stop: str
    destination_stop: str
    buses_to_transfer: int = Field(..., gt=0)
    # Aliases for Chandhana / teammate frontend consistency
    from_stop: Optional[str] = None
    to_stop: Optional[str] = None
    buses_to_move: Optional[int] = None
    assigned_vehicle_ids: List[str] = Field(
        default_factory=list,
        description="Specific physical bus IDs assigned to this transfer"
    )
    departure_time: str
    arrival_time: str
    travel_time_minutes: int = Field(..., ge=0)
    interval_timestamp: Optional[str] = Field(
        default=None,
        description="Reference 15-minute forecast interval timestamp"
    )
    tradeoff: Optional[TradeoffDetail] = None
    source_service_loss: str
    expected_benefit: str
    network_effect: str


class OptimizeRequest(BaseModel):
    festival_id: str
    total_fleet_size: int = Field(..., gt=0, description="Fixed total fleet size F_total")
    current_allocation: Dict[str, int] = Field(
        ...,
        description="Mapping of stop_id to current allocated buses count"
    )
    predicted_demand_profile: Optional[Dict[str, int]] = Field(
        default=None,
        description="Mapping of stop_id to predicted crowd demand (passengers)"
    )
    # Gugaan's documented singular contract field
    stop_forecast: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Gugaan's Phase 3 stop-level forecast array"
    )
    # Deprecated backward-compatibility alias
    stop_forecasts: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Deprecated alias for stop_forecast"
    )
    forecast_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Full top-level Gugaan prediction response container"
    )
    bus_inventory: Optional[List[BusInventoryItem]] = Field(
        default=None,
        description="Optional detailed vehicle fleet inventory with statuses and IDs"
    )
    max_staging_capacity: Optional[Dict[str, int]] = Field(
        default=None,
        description="Maximum simultaneous bus parking/staging limit per stop"
    )
    min_service_per_stop: int = Field(
        default=1,
        ge=0,
        description="Configurable minimum operational service floor per stop"
    )
    time_horizon_minutes: int = Field(default=120, ge=15, le=720)
    interval_minutes: int = Field(default=15, ge=1, le=60)
    departure_timestamp: Optional[str] = Field(
        default=None,
        description="Reference departure timestamp in ISO-8601 with offset (e.g., 2026-10-10T20:15:00+05:30)"
    )
    use_synthetic_capacity_fallback: bool = Field(
        default=False,
        description="Explicit flag permitting 50 pax/bus synthetic fallback when official capacity is missing"
    )
    bus_capacity: Optional[int] = Field(
        default=None,
        ge=10,
        le=150,
        description="Explicit uniform bus capacity override if official per-vehicle capacity is absent"
    )

    @field_validator("current_allocation")
    @classmethod
    def validate_non_negative_allocation(cls, v: Dict[str, int]) -> Dict[str, int]:
        for stop, count in v.items():
            if count < 0:
                raise ValueError(f"Allocation for stop '{stop}' cannot be negative (got {count})")
        return v


class OptimizeResponse(BaseModel):
    plan_id: str
    total_fleet_size: int
    fleet_conserved: bool = True
    repositioning_moves: List[RepositioningMove] = Field(default_factory=list)
    final_allocation: Dict[str, int]
    overall_queue_reduction_percentage: float = 0.0
    unserved_demand_before: Optional[int] = None
    unserved_demand_after: Optional[int] = None
    capacity_provenance: str = Field(
        default="VERIFIED_DATA",
        description="Indicates whether bus capacity was derived from verified data or explicitly synthetic fallback"
    )
    warnings: List[str] = Field(default_factory=list)
    modeled_assumptions: List[str] = Field(default_factory=list)
    status: str = "SUCCESS"
    message: Optional[str] = None


# ==========================================
# 5. Crowd Prediction Schemas
# ==========================================
class PredictionRequest(BaseModel):
    festival_id: str
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    weather_condition: str = "clear"
    surge_multiplier: float = 1.0
    attendance_multiplier: Optional[float] = None
    rain_probability: Optional[float] = 0.0
    event_end_time: Optional[str] = None
    bus_capacity: Optional[int] = 50
    load_factor: Optional[float] = 0.85
    interval_minutes: Optional[int] = 15


class TimelineStep(BaseModel):
    timestamp: str
    total_crowd_estimate: int
    discharge_rate_per_hour: int
    surge_alert_level: str


class StopForecast(BaseModel):
    stop_id: str
    predicted_demand: int
    waiting_minutes: float
    risk_level: str
    queue: Optional[int] = None
    required_buses: Optional[int] = None
    crowd_pressure: Optional[float] = None
    risk_score: Optional[int] = None


class PredictionResponse(BaseModel):
    festival_id: str
    timeline: List[TimelineStep]
    peak_surge_time: str
    peak_crowd: Optional[int] = None
    highest_demand_stops: List[str]
    stop_forecasts: List[StopForecast] = Field(default_factory=list)
    stop_forecast: Optional[List[Dict[str, Any]]] = None


# ==========================================
# 6. Scenario Simulation Schemas
# ==========================================
class SimulationRequest(BaseModel):
    festival_id: str
    prediction_timeline_id: Optional[str] = None
    simulation_step_minutes: Optional[int] = 15
    crowd_exit_speed_kmh: Optional[float] = 2.5
    attendance_multiplier: Optional[float] = 1.0
    rain_probability: Optional[float] = 0.0
    event_delay_minutes: Optional[int] = 0
    bus_failures: Optional[int] = 0
    failed_stop_id: Optional[str] = None


class StopQueueStatus(BaseModel):
    waiting_passengers: int
    queue_risk: str


class SimulationDensityPoint(BaseModel):
    latitude: float
    longitude: float
    weight: float


class SimulationStep(BaseModel):
    step_time: str
    stop_queues: Dict[str, StopQueueStatus]
    density_grid: List[SimulationDensityPoint] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    simulation_id: str
    steps: List[SimulationStep]
    baseline: Optional[Dict[str, Any]] = None
    scenario: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None
    stop_comparisons: Optional[List[Dict[str, Any]]] = None

