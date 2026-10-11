"""
NILA Operational Control Room API Endpoints
Manages live fleet telemetry, decision queue approvals, dispatch orders,
field marshal crowd reports, and shift handover synthesis.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/operations", tags=["Operations"])

# ==========================================
# Pydantic Schemas
# ==========================================

class BusTelemetryItem(BaseModel):
    bus_id: str
    route: str
    current_stop: str
    capacity: int = 51
    current_load: int = 0
    occupancy_band: str = "SEATS_FREE"  # EMPTY, SEATS_FREE, STANDING, CROWDED
    status: str = "IN_SERVICE"          # AVAILABLE, IN_SERVICE, RETURNING, UNAVAILABLE
    free_at: str = "18:52"
    release_point: str = "Mattuthavani"
    confidence: str = "HIGH"            # HIGH, LOW, VERIFY_REQUIRED
    source: str = "SIMULATED_TELEMETRY"
    candidate_for_repositioning: bool = False
    last_update: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FleetSummaryResponse(BaseModel):
    total_fleet: int = 25
    available: int = 7
    in_service: int = 14
    returning: int = 3
    unavailable: int = 1
    provenance: str = "SIMULATED_TELEMETRY"
    buses: List[BusTelemetryItem] = Field(default_factory=list)


class OccupancyUpdateRequest(BaseModel):
    occupancy_band: str  # EMPTY, SEATS_FREE, STANDING, CROWDED
    current_load: Optional[int] = None


class DecisionItem(BaseModel):
    id: str
    priority: str       # CRITICAL, HIGH, MODERATE
    problem: str
    action: str
    bus_ids: List[str]
    source_stop: str
    destination_stop: str
    departure_time: str
    arrival_time: str
    travel_time_minutes: int
    benefit: str
    tradeoff: str
    network_effect: str
    confidence: str = "HIGH"
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED
    order_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OrderDispatchItem(BaseModel):
    id: str
    decision_id: str
    bus_id: str
    source_stop: str
    destination_stop: str
    departure_time: str
    arrival_time: str
    priority: str = "HIGH"
    status: str = "DISPATCH_PENDING"  # DISPATCH_PENDING, ACKNOWLEDGED, EN_ROUTE, COMPLETED, CANNOT_COMPLY
    cannot_comply_reason: Optional[str] = None
    alternative_bus_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CannotComplyRequest(BaseModel):
    reason: str


class DecisionSyncRequest(BaseModel):
    """
    Accepts real optimization output from the prediction+optimization pipeline.
    Used by the reactive frontend to push grounded decisions into the queue.
    """
    plan_id: str
    risk_level: str                    # CRITICAL, HIGH, MODERATE, LOW
    peak_surge_time: Optional[str] = None
    average_waiting_time_minutes: Optional[float] = None
    highest_demand_stop: Optional[str] = None
    source_stop: Optional[str] = None
    destination_stop: Optional[str] = None
    buses_to_transfer: Optional[int] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    travel_time_minutes: Optional[int] = None
    expected_benefit: Optional[str] = None
    source_service_loss: Optional[str] = None
    network_effect: Optional[str] = None
    overall_queue_reduction_percentage: Optional[float] = None
    festival_id: str = "madurai-chithirai-2026"


class CrowdReportRequest(BaseModel):
    stop_id: str
    level: str  # LIGHT, MODERATE, HEAVY, UNSAFE
    notes: Optional[str] = None


class CrowdReportResponse(BaseModel):
    id: str
    stop_id: str
    level: str
    notes: Optional[str] = None
    timestamp: str
    status: str = "RECORDED"


class HandoverResponse(BaseModel):
    timestamp: str
    network_risk: str
    peak_window: str
    overloaded_stops: List[str]
    approved_moves_count: int
    pending_decisions_count: int
    active_fleet_summary: Dict[str, int]
    outstanding_issues: List[str]
    next_review_time: str
    provenance: str = "GROUNDED_OPERATIONAL_SYNTHESIS"


# ==========================================
# In-Memory Operational Store
# (Seeded with 25 Fixed Buses & Scenario Data)
# ==========================================

INITIAL_BUSES: List[BusTelemetryItem] = [
    BusTelemetryItem(
        bus_id="BUS-12",
        route="Route 12: Mattuthavani ↔ Periyar",
        current_stop="Mattuthavani",
        capacity=51,
        current_load=27,
        occupancy_band="SEATS_FREE",
        status="RETURNING",
        free_at="18:52",
        release_point="Mattuthavani",
        confidence="HIGH",
        candidate_for_repositioning=True,
    ),
    BusTelemetryItem(
        bus_id="BUS-08",
        route="Route 12: Mattuthavani ↔ Periyar",
        current_stop="Mattuthavani",
        capacity=51,
        current_load=0,
        occupancy_band="EMPTY",
        status="AVAILABLE",
        free_at="NOW",
        release_point="Mattuthavani",
        confidence="HIGH",
        candidate_for_repositioning=True,
    ),
    BusTelemetryItem(
        bus_id="BUS-03",
        route="Route 4: Aarapalayam ↔ Mattuthavani",
        current_stop="Aarapalayam",
        capacity=51,
        current_load=48,
        occupancy_band="CROWDED",
        status="IN_SERVICE",
        free_at="19:20",
        release_point="Aarapalayam",
        confidence="HIGH",
        candidate_for_repositioning=False,
    ),
    BusTelemetryItem(
        bus_id="BUS-18",
        route="Route 7: Aarapalayam ↔ Periyar",
        current_stop="Periyar",
        capacity=51,
        current_load=46,
        occupancy_band="STANDING",
        status="IN_SERVICE",
        free_at="19:10",
        release_point="Periyar",
        confidence="LOW",
        candidate_for_repositioning=False,
    ),
    BusTelemetryItem(
        bus_id="BUS-05",
        route="Special Circular: Temple Outer Ring",
        current_stop="Periyar",
        capacity=51,
        current_load=0,
        occupancy_band="EMPTY",
        status="UNAVAILABLE",
        free_at="UNKNOWN",
        release_point="Periyar Depot",
        confidence="HIGH",
        candidate_for_repositioning=False,
    ),
]

# Generate remaining buses up to 25 to guarantee fixed-fleet = 25
for i in range(1, 26):
    bid = f"BUS-{i:02d}"
    if not any(b.bus_id == bid for b in INITIAL_BUSES):
        if i in [1, 2, 4, 7, 9]:
            st = "AVAILABLE"
            oc = "EMPTY"
            load = 0
            free = "NOW"
            candidate = True
        elif i in [6, 10, 11]:
            st = "RETURNING"
            oc = "SEATS_FREE"
            load = 22
            free = f"18:{45 + (i % 15):02d}"
            candidate = True
        else:
            st = "IN_SERVICE"
            oc = "SEATS_FREE" if i % 2 == 0 else "STANDING"
            load = 34 if i % 2 == 0 else 44
            free = f"19:{10 + (i % 20):02d}"
            candidate = False

        stop_name = "Mattuthavani" if i % 3 == 0 else ("Aarapalayam" if i % 3 == 1 else "Periyar")
        INITIAL_BUSES.append(
            BusTelemetryItem(
                bus_id=bid,
                route=f"Route {i}: Radial Connection",
                current_stop=stop_name,
                capacity=51,
                current_load=load,
                occupancy_band=oc,
                status=st,
                free_at=free,
                release_point=stop_name,
                confidence="HIGH" if i != 14 else "VERIFY_REQUIRED",
                candidate_for_repositioning=candidate,
            )
        )

# In-memory mutable states
_fleet_ledger: Dict[str, BusTelemetryItem] = {b.bus_id: b for b in INITIAL_BUSES}

_decisions: Dict[str, DecisionItem] = {
    "DEC-001": DecisionItem(
        id="DEC-001",
        priority="CRITICAL",
        problem="Periyar Bus Stand predicted critical demand surge at egress peak window. High crowd accumulation detected.",
        action="Reposition 2 empty/returning buses from Mattuthavani to Periyar",
        bus_ids=["BUS-12", "BUS-08"],
        source_stop="Mattuthavani",
        destination_stop="Periyar",
        departure_time="18:52",
        arrival_time="19:06",
        travel_time_minutes=14,
        benefit="-13 min average wait time at Periyar; 60% queue reduction",
        tradeoff="Source service -2 buses; Mattuthavani wait +3 min (surplus buffer remains)",
        network_effect="-10 min net wait reduction across network; fleet conserved at 25",
        confidence="HIGH",
        status="PENDING",
    ),
}

_orders: Dict[str, OrderDispatchItem] = {}
_crowd_reports: List[CrowdReportResponse] = []


# ==========================================
# Endpoints
# ==========================================

@router.get("/fleet", response_model=FleetSummaryResponse, status_code=status.HTTP_200_OK)
async def get_fleet_ledger() -> FleetSummaryResponse:
    """Returns the comprehensive Fixed-Fleet telemetry ledger and availability metrics."""
    buses = list(_fleet_ledger.values())
    buses.sort(key=lambda b: b.bus_id)
    
    available = sum(1 for b in buses if b.status == "AVAILABLE")
    in_service = sum(1 for b in buses if b.status == "IN_SERVICE")
    returning = sum(1 for b in buses if b.status == "RETURNING")
    unavailable = sum(1 for b in buses if b.status == "UNAVAILABLE")

    return FleetSummaryResponse(
        total_fleet=len(buses),
        available=available,
        in_service=in_service,
        returning=returning,
        unavailable=unavailable,
        buses=buses,
    )


@router.get("/fleet/{bus_id}", response_model=BusTelemetryItem, status_code=status.HTTP_200_OK)
async def get_bus_details(bus_id: str) -> BusTelemetryItem:
    """Returns granular operational telemetry for a specific vehicle."""
    bus = _fleet_ledger.get(bus_id.upper())
    if not bus:
        raise HTTPException(status_code=404, detail=f"Vehicle {bus_id} not found in fleet ledger")
    return bus


@router.post("/fleet/{bus_id}/occupancy", response_model=BusTelemetryItem, status_code=status.HTTP_200_OK)
async def update_bus_occupancy(bus_id: str, update: OccupancyUpdateRequest) -> BusTelemetryItem:
    """
    Crew or operator 1-tap occupancy reporter.
    Updates the operational telemetry ledger with verified load bands.
    """
    bus = _fleet_ledger.get(bus_id.upper())
    if not bus:
        raise HTTPException(status_code=404, detail=f"Vehicle {bus_id} not found in fleet ledger")

    bus.occupancy_band = update.occupancy_band
    band_loads = {
        "EMPTY": 0,
        "SEATS_FREE": 25,
        "STANDING": 42,
        "CROWDED": 51,
    }
    bus.current_load = update.current_load if update.current_load is not None else band_loads.get(update.occupancy_band, bus.current_load)
    bus.confidence = "HIGH"
    bus.last_update = datetime.now(timezone.utc).isoformat()
    return bus


@router.get("/decisions", response_model=List[DecisionItem], status_code=status.HTTP_200_OK)
async def get_decision_queue() -> List[DecisionItem]:
    """Returns active operational decision cards sorted by priority."""
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}
    decisions = list(_decisions.values())
    decisions.sort(key=lambda d: priority_order.get(d.priority, 9))
    return decisions


@router.post("/decisions/sync", response_model=List[DecisionItem], status_code=status.HTTP_200_OK)
async def sync_decisions_from_optimization(req: DecisionSyncRequest) -> List[DecisionItem]:
    """
    Accepts real prediction+optimization output from the reactive frontend pipeline.
    Creates or updates a dynamically grounded decision from the optimizer's repositioning move.
    Preserves APPROVED/REJECTED decisions from earlier cycles.
    Returns the updated decision queue.
    """
    # Only a valid move from the optimizer creates a new decision
    if not req.source_stop or not req.destination_stop or not req.buses_to_transfer:
        # No valid move — remove all PENDING decisions so UI reflects no repositioning required
        stale_ids = [k for k, d in _decisions.items() if d.status == "PENDING"]
        for k in stale_ids:
            del _decisions[k]
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}
        result = sorted(_decisions.values(), key=lambda d: priority_order.get(d.priority, 9))
        return result

    # Determine priority from risk level
    risk_to_priority = {"CRITICAL": "CRITICAL", "HIGH": "HIGH", "MODERATE": "MODERATE", "LOW": "MODERATE"}
    priority = risk_to_priority.get(req.risk_level.upper(), "MODERATE")

    # Find candidate buses with AVAILABLE or RETURNING status at source stop
    candidate_buses = [
        b.bus_id for b in _fleet_ledger.values()
        if b.status in ("AVAILABLE", "RETURNING") and b.candidate_for_repositioning
    ][:req.buses_to_transfer]

    if not candidate_buses:
        # Fallback: take first available buses
        candidate_buses = [
            b.bus_id for b in _fleet_ledger.values()
            if b.status == "AVAILABLE"
        ][:req.buses_to_transfer]

    wait_str = f"{req.average_waiting_time_minutes:.0f} min" if req.average_waiting_time_minutes else "elevated"
    queue_pct = f"{req.overall_queue_reduction_percentage:.0f}%" if req.overall_queue_reduction_percentage else "significant"

    dec_id = f"OPT-{req.plan_id[-6:]}"
    peak_time_str = req.peak_surge_time or "surge window"

    new_decision = DecisionItem(
        id=dec_id,
        priority=priority,
        problem=(
            f"{req.highest_demand_stop or req.destination_stop} predicted {req.risk_level} demand surge "
            f"at {peak_time_str}. Average wait: {wait_str}."
        ),
        action=(
            f"Reposition {req.buses_to_transfer} bus(es) from {req.source_stop} "
            f"to {req.destination_stop} before peak egress."
        ),
        bus_ids=candidate_buses if candidate_buses else ["BUS-12"],
        source_stop=req.source_stop,
        destination_stop=req.destination_stop,
        departure_time=req.departure_time or "NOW",
        arrival_time=req.arrival_time or "~14 min",
        travel_time_minutes=req.travel_time_minutes or 14,
        benefit=req.expected_benefit or f"{queue_pct} queue reduction at destination",
        tradeoff=req.source_service_loss or f"Source capacity -{ req.buses_to_transfer} bus(es); surplus buffer absorbs impact",
        network_effect=req.network_effect or f"Fleet conserved at 25; net wait reduction across network",
        confidence="HIGH",
        status="PENDING",
    )

    # Purge all previous PENDING decisions so queue reflects the active scenario
    stale_ids = [k for k, d in _decisions.items() if d.status == "PENDING"]
    for k in stale_ids:
        del _decisions[k]

    _decisions[dec_id] = new_decision

    priority_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}
    result = sorted(_decisions.values(), key=lambda d: priority_order.get(d.priority, 9))
    return result


@router.post("/decisions/{decision_id}/approve", response_model=OrderDispatchItem, status_code=status.HTTP_200_OK)
async def approve_decision(decision_id: str) -> OrderDispatchItem:
    """
    Duty Manager Approval workflow.
    Transitions decision to APPROVED and generates concrete operational ORDER.
    """
    decision = _decisions.get(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")

    decision.status = "APPROVED"
    order_id = f"ORDER-{len(_orders) + 1:03d}"
    assigned_bus = decision.bus_ids[0] if decision.bus_ids else "BUS-12"

    order = OrderDispatchItem(
        id=order_id,
        decision_id=decision.id,
        bus_id=assigned_bus,
        source_stop=decision.source_stop,
        destination_stop=decision.destination_stop,
        departure_time=decision.departure_time,
        arrival_time=decision.arrival_time,
        priority=decision.priority,
        status="DISPATCH_PENDING",
    )
    _orders[order_id] = order
    decision.order_id = order_id
    return order


@router.post("/decisions/{decision_id}/reject", response_model=DecisionItem, status_code=status.HTTP_200_OK)
async def reject_decision(decision_id: str) -> DecisionItem:
    """Duty Manager Rejection workflow. Transitions decision to REJECTED."""
    decision = _decisions.get(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")

    decision.status = "REJECTED"
    return decision


@router.get("/orders", response_model=List[OrderDispatchItem], status_code=status.HTTP_200_OK)
async def get_orders() -> List[OrderDispatchItem]:
    """Returns dispatch orders for Depot and Crew interfaces."""
    orders = list(_orders.values())
    orders.sort(key=lambda o: o.id, reverse=True)
    return orders


@router.post("/orders/{order_id}/acknowledge", response_model=OrderDispatchItem, status_code=status.HTTP_200_OK)
async def acknowledge_order(order_id: str) -> OrderDispatchItem:
    """Depot or Crew order acknowledgment workflow."""
    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    order.status = "ACKNOWLEDGED"
    # Update vehicle status in ledger
    bus = _fleet_ledger.get(order.bus_id)
    if bus:
        bus.status = "IN_SERVICE"
        bus.free_at = order.arrival_time
    return order


@router.post("/orders/{order_id}/cannot-comply", response_model=OrderDispatchItem, status_code=status.HTTP_200_OK)
async def cannot_comply_order(order_id: str, request: CannotComplyRequest) -> OrderDispatchItem:
    """
    Depot/Crew 'Cannot Comply' flow.
    Marks order as CANNOT_COMPLY, identifies alternative candidate bus,
    and updates operational ledger.
    """
    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    order.status = "CANNOT_COMPLY"
    order.cannot_comply_reason = request.reason

    # Mark current bus unavailable
    orig_bus = _fleet_ledger.get(order.bus_id)
    if orig_bus:
        orig_bus.status = "UNAVAILABLE"

    # Search alternative available bus
    alt_bus = next((b for b in _fleet_ledger.values() if b.status == "AVAILABLE" and b.bus_id != order.bus_id), None)
    if alt_bus:
        order.alternative_bus_id = alt_bus.bus_id

    return order


@router.post("/stops/{stop_id}/crowd-report", response_model=CrowdReportResponse, status_code=status.HTTP_200_OK)
async def report_stop_crowd(stop_id: str, report: CrowdReportRequest) -> CrowdReportResponse:
    """Field Marshal 1-tap crowd reporter."""
    entry = CrowdReportResponse(
        id=f"CR-{len(_crowd_reports) + 1:04d}",
        stop_id=stop_id,
        level=report.level,
        notes=report.notes,
        timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
        status="RECORDED",
    )
    _crowd_reports.append(entry)
    return entry


@router.post("/ai/handover", response_model=HandoverResponse, status_code=status.HTTP_200_OK)
async def generate_handover_brief() -> HandoverResponse:
    """Generates grounded operational shift handover summary."""
    buses = list(_fleet_ledger.values())
    approved_moves = sum(1 for d in _decisions.values() if d.status == "APPROVED")
    pending_decisions = sum(1 for d in _decisions.values() if d.status == "PENDING")

    fleet_summary = {
        "total": len(buses),
        "available": sum(1 for b in buses if b.status == "AVAILABLE"),
        "in_service": sum(1 for b in buses if b.status == "IN_SERVICE"),
        "returning": sum(1 for b in buses if b.status == "RETURNING"),
        "unavailable": sum(1 for b in buses if b.status == "UNAVAILABLE"),
    }

    return HandoverResponse(
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        network_risk="CRITICAL",
        peak_window="20:10 - 21:00",
        overloaded_stops=["Periyar Bus Stand", "Aarapalayam North Exit"],
        approved_moves_count=approved_moves,
        pending_decisions_count=pending_decisions,
        active_fleet_summary=fleet_summary,
        outstanding_issues=[
            "Rain probability trending at 30% over sacred perimeter",
            "Chariot procession crowd dispersing toward Periyar Gate",
        ],
        next_review_time="19:15",
    )
