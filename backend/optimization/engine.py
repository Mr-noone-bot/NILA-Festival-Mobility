"""
NILA Fixed-Fleet Bus Optimization Engine
Solves constrained bus repositioning under the Fixed Fleet Invariant.
Conservation Rule: sum(Final Allocation) == sum(Initial Allocation) == F_total
Enforces vehicle status availability, staging limits, multi-interval scheduling,
and explicit capacity provenance.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Set
import logging

from backend.core.config import settings
from backend.core.constants import (
    BusStatus,
    DEFAULT_BUS_CAPACITY,
    TAMIL_NADU_TIMEZONE,
)
from backend.api.schemas import (
    OptimizeRequest,
    OptimizeResponse,
    RepositioningMove,
    BusInventoryItem,
    TradeoffDetail,
)
from backend.optimization.models import (
    StopForecastRecord,
    GugaanForecastPayload,
    BusEntity,
)
from backend.optimization.tradeoffs import (
    evaluate_movement_consequences,
    calculate_network_queue_reduction,
    calculate_wait_times_and_tradeoff,
)
from backend.routing.service import haversine_distance_meters

logger = logging.getLogger(__name__)


# Default known Madurai stop coordinates for travel time estimation
DEFAULT_STOP_COORDINATES: Dict[str, Tuple[float, float]] = {
    "stop-periyar": (9.9167, 78.1132),
    "stop-aarapalayam": (9.9326, 78.1064),
    "stop-mattuthavani": (9.9482, 78.1561),
    "stop_main": (9.9195, 78.1193),
    "stop_north": (9.9350, 78.1250),
    "stop_south": (9.9050, 78.1100),
    "stop_east": (9.9200, 78.1400),
}


def estimate_transit_time_minutes(
    source_stop: str,
    dest_stop: str,
    congestion_factor: float = 1.2,
) -> int:
    """
    Computes road transit time in minutes between two festival stops.
    Uses stop coordinates if known, or defaults to 20 minutes corridor average.
    """
    if source_stop == dest_stop:
        return 0

    src_coord = DEFAULT_STOP_COORDINATES.get(source_stop)
    dst_coord = DEFAULT_STOP_COORDINATES.get(dest_stop)

    if src_coord and dst_coord:
        dist_m = haversine_distance_meters(src_coord[0], src_coord[1], dst_coord[0], dst_coord[1]) * 1.35
        # Assume 20 km/h in festival traffic = 5.56 m/s
        speed_mps = 5.556
        duration_sec = (dist_m / speed_mps) * congestion_factor
        return max(5, int(round(duration_sec / 60.0)))

    return 20


class FixedFleetOptimizer:
    """
    Deterministic Constrained Optimizer for Festival Fleet Relocation.
    Enforces:
    1. Fixed Fleet Invariant: sum(Final) == sum(Initial) == F_total
    2. Non-negative stop allocations.
    3. Vehicle status availability (no moving IN_TRANSIT or OUT_OF_SERVICE buses).
    4. Vehicle assignment exclusivity (no duplicate overlapping moves).
    5. Maximum staging capacity constraints per stop.
    6. Minimum service floor per stop.
    7. Multi-interval discrete time scheduling based on 15-minute forecast intervals.
    8. Explicit capacity provenance tagging.
    """

    def resolve_capacity_and_provenance(
        self,
        request: OptimizeRequest,
    ) -> Tuple[int, str, List[str]]:
        """
        Determines effective bus capacity and explicit provenance label.
        Never silently substitutes unverified default without explicit documentation.
        """
        warnings: List[str] = []

        if request.bus_capacity is not None:
            return request.bus_capacity, "CONFIGURED_OVERRIDE", warnings

        if request.bus_inventory:
            capacities = [b.capacity for b in request.bus_inventory if b.capacity is not None]
            if capacities:
                avg_cap = int(round(sum(capacities) / len(capacities)))
                return avg_cap, "VERIFIED_INVENTORY_CAPACITY", warnings

        # Fallback handling
        if request.use_synthetic_capacity_fallback or settings.ALLOW_SYNTHETIC_CAPACITY_FALLBACK:
            warnings.append(
                "Operating under synthetic capacity fallback (50 passengers/bus). "
                "Official vehicle capacity data is unverified."
            )
            return settings.DEFAULT_BUS_CAPACITY, "SYNTHETIC_FALLBACK (50 pax/bus)", warnings

        raise ValueError(
            "Bus capacity is missing and unverified. "
            "Set use_synthetic_capacity_fallback=True or configure bus_capacity to run under simulation."
        )

    def extract_forecast_records(self, request: OptimizeRequest) -> List[StopForecastRecord]:
        """
        Extracts and validates StopForecastRecords from singular stop_forecast,
        backward-compatible stop_forecasts, or full forecast_payload.
        """
        raw_list = None
        if request.stop_forecast is not None:
            raw_list = request.stop_forecast
        elif request.stop_forecasts is not None:
            raw_list = request.stop_forecasts
        elif request.forecast_payload and "stop_forecast" in request.forecast_payload:
            raw_list = request.forecast_payload["stop_forecast"]

        if not raw_list:
            return []

        records: List[StopForecastRecord] = []
        for raw in raw_list:
            records.append(StopForecastRecord.model_validate(raw))
        return records

    def optimize(
        self,
        request: OptimizeRequest,
        max_moves_per_interval: int = 3,
    ) -> OptimizeResponse:
        """
        Compute optimal repositioning moves and final allocation conserving the fixed fleet.
        """
        current_alloc = dict(request.current_allocation)
        f_total = request.total_fleet_size
        warnings: List[str] = []
        modeled_assumptions: List[str] = [
            "Assumed nominal 60-minute loop cycle for headway variation estimates.",
            f"Assumed nominal 30-minute shuttle loop cycle for {request.time_horizon_minutes}-minute horizon throughput.",
        ]

        # Invariant 1: Total initial allocation must match total_fleet_size
        actual_initial_sum = sum(current_alloc.values())
        if actual_initial_sum != f_total:
            raise ValueError(
                f"Fixed Fleet Invariant Violation: Total allocated buses ({actual_initial_sum}) "
                f"does not match declared total fleet size ({f_total})."
            )

        # Invariant 2: Non-negative allocations
        for stop, count in current_alloc.items():
            if count < 0:
                raise ValueError(f"Allocation for stop '{stop}' cannot be negative ({count}).")

        # Resolve capacity provenance
        bus_cap, cap_provenance, cap_warnings = self.resolve_capacity_and_provenance(request)
        warnings.extend(cap_warnings)

        # Calculate effective loop capacity over horizon
        trips_per_bus = max(1, round(request.time_horizon_minutes / 30.0))
        effective_capacity = bus_cap * trips_per_bus

        # Vehicle inventory tracking
        available_vehicles_by_stop: Dict[str, List[str]] = {s: [] for s in current_alloc.keys()}
        vehicle_commitments: Dict[str, datetime] = {}  # vehicle_id -> available_after_dt

        if request.bus_inventory:
            for b in request.bus_inventory:
                if b.status == BusStatus.OUT_OF_SERVICE:
                    # Vehicle is unavailable for active demand
                    continue
                if b.status == BusStatus.IN_TRANSIT:
                    # Vehicle cannot be relocated immediately
                    continue
                if b.current_stop_id in available_vehicles_by_stop:
                    available_vehicles_by_stop[b.current_stop_id].append(b.vehicle_id)

        # Setup reference base timestamp
        now_dt = datetime.now(timezone(timedelta(hours=5, minutes=30)))
        if request.departure_timestamp:
            try:
                base_dt = datetime.fromisoformat(request.departure_timestamp)
            except Exception:
                base_dt = now_dt
        else:
            base_dt = now_dt

        # Parse forecast timeline records
        forecast_records = self.extract_forecast_records(request)

        # Group forecast records by discrete interval timestamp
        intervals_map: Dict[str, Dict[str, int]] = {}
        if forecast_records:
            # Sort records chronologically
            sorted_records = sorted(forecast_records, key=lambda r: r.timestamp)
            for rec in sorted_records:
                ts = rec.timestamp
                if ts not in intervals_map:
                    intervals_map[ts] = {}
                # Passenger demand is queue + arrivals, or predicted crowd
                dem = max(rec.predicted_crowd, rec.queue + rec.arrivals)
                intervals_map[ts][rec.stop_id] = dem
        elif request.predicted_demand_profile:
            # Single static profile
            ts_key = base_dt.isoformat()
            intervals_map[ts_key] = {s: max(0, d) for s, d in request.predicted_demand_profile.items()}
        else:
            # Zero demand profile
            ts_key = base_dt.isoformat()
            intervals_map[ts_key] = {s: 0 for s in current_alloc.keys()}

        # Staging constraints map
        max_staging = request.max_staging_capacity or {}

        # Working allocation state
        working_alloc = dict(current_alloc)
        repositioning_moves: List[RepositioningMove] = []
        in_transit_arrivals: List[Tuple[datetime, str, int, List[str]]] = []  # (arr_dt, dest_stop, qty, vehicle_ids)

        # Iterate through discrete 15-minute intervals chronologically
        interval_keys = sorted(intervals_map.keys())
        cumulative_demand_snapshot: Dict[str, int] = {s: 0 for s in current_alloc.keys()}

        for interval_idx, interval_ts in enumerate(interval_keys):
            try:
                interval_dt = datetime.fromisoformat(interval_ts)
            except Exception:
                interval_dt = base_dt + timedelta(minutes=interval_idx * request.interval_minutes)

            # Process in-transit arrivals that reached destination by or at this interval
            still_in_transit = []
            for arr_dt, dest_stop, qty, v_ids in in_transit_arrivals:
                if arr_dt <= interval_dt:
                    working_alloc[dest_stop] += qty
                    if dest_stop in available_vehicles_by_stop:
                        available_vehicles_by_stop[dest_stop].extend(v_ids)
                else:
                    still_in_transit.append((arr_dt, dest_stop, qty, v_ids))
            in_transit_arrivals = still_in_transit

            interval_demand = intervals_map[interval_ts]
            for s, d in interval_demand.items():
                cumulative_demand_snapshot[s] = max(cumulative_demand_snapshot.get(s, 0), d)

            # Optimize for current interval
            for _ in range(max_moves_per_interval):
                surpluses: Dict[str, int] = {}
                deficits: Dict[str, int] = {}

                for stop, buses in working_alloc.items():
                    dem = interval_demand.get(stop, 0)
                    needed_buses = math.ceil(dem / float(effective_capacity))
                    min_floor = min(buses, request.min_service_per_stop)

                    # Available surplus considers inventory if present
                    if request.bus_inventory and stop in available_vehicles_by_stop:
                        movable_buses = len(available_vehicles_by_stop[stop])
                    else:
                        movable_buses = buses

                    if movable_buses > needed_buses and movable_buses > min_floor:
                        surpluses[stop] = movable_buses - max(needed_buses, min_floor)

                    incoming_to_stop = sum(qty for _, dst, qty, _ in in_transit_arrivals if dst == stop)
                    effective_staged = buses + incoming_to_stop
                    if stop in max_staging and effective_staged >= max_staging[stop]:
                        # Stop is already at or will reach maximum staging capacity
                        pass
                    elif (effective_staged * effective_capacity) < dem:
                        deficit_pax = dem - (effective_staged * effective_capacity)
                        deficits[stop] = math.ceil(deficit_pax / float(effective_capacity))

                if not surpluses or not deficits:
                    break

                best_source = max(surpluses.keys(), key=lambda s: surpluses[s])
                best_dest = max(deficits.keys(), key=lambda s: deficits[s])

                if best_source == best_dest:
                    break

                # Enforce Staging Capacity Limit at destination
                if best_dest in max_staging:
                    dest_limit = max_staging[best_dest]
                    incoming_buses = sum(qty for _, dst, qty, _ in in_transit_arrivals if dst == best_dest)
                    projected_dest = working_alloc[best_dest] + incoming_buses
                    space_left = dest_limit - projected_dest
                    if space_left <= 0:
                        deficits.pop(best_dest, None)
                        continue
                else:
                    space_left = 9999

                # Calculate road travel time
                travel_time_min = estimate_transit_time_minutes(best_source, best_dest)
                if travel_time_min > request.time_horizon_minutes:
                    break

                # Transfer quantity bounded by surplus, deficit, and staging space
                transfer_qty = min(surpluses[best_source], deficits[best_dest], space_left)
                if transfer_qty <= 0:
                    break

                dep_dt = interval_dt
                arr_dt = dep_dt + timedelta(minutes=travel_time_min)

                # Assign physical vehicle IDs if inventory is tracked
                assigned_v_ids: List[str] = []
                if request.bus_inventory and best_source in available_vehicles_by_stop:
                    src_pool = available_vehicles_by_stop[best_source]
                    assigned_v_ids = src_pool[:transfer_qty]
                    available_vehicles_by_stop[best_source] = src_pool[transfer_qty:]
                    for vid in assigned_v_ids:
                        vehicle_commitments[vid] = arr_dt

                # Evaluate trade-offs
                source_loss, expected_benefit, network_effect = evaluate_movement_consequences(
                    source_stop=best_source,
                    dest_stop=best_dest,
                    buses_to_transfer=transfer_qty,
                    source_demand=interval_demand.get(best_source, 0),
                    dest_demand=interval_demand.get(best_dest, 0),
                    source_buses_before=working_alloc[best_source],
                    dest_buses_before=working_alloc[best_dest],
                    travel_time_minutes=travel_time_min,
                    bus_capacity=effective_capacity,
                )

                # Explicit before vs after wait times and deltas
                wt = calculate_wait_times_and_tradeoff(
                    source_buses_before=working_alloc[best_source],
                    source_buses_after=working_alloc[best_source] - transfer_qty,
                    dest_buses_before=working_alloc[best_dest],
                    dest_buses_after=working_alloc[best_dest] + transfer_qty,
                    nominal_cycle_minutes=60.0,
                )
                dest_unserved_b = max(0, interval_demand.get(best_dest, 0) - working_alloc[best_dest] * effective_capacity)
                dest_unserved_a = max(0, interval_demand.get(best_dest, 0) - (working_alloc[best_dest] + transfer_qty) * effective_capacity)
                cleared_pax = dest_unserved_b - dest_unserved_a
                rel_pct = round((cleared_pax / dest_unserved_b) * 100, 1) if dest_unserved_b > 0 else 0.0

                tradeoff_obj = TradeoffDetail(
                    destination_waiting_reduction_minutes=round(abs(wt["dest_delta"]), 2),
                    source_waiting_increase_minutes=round(abs(wt["source_delta"]), 2),
                    reported_delta_minutes=wt["reported_delta"],
                    destination_queue_reduction_percentage=rel_pct,
                    cleared_passengers=cleared_pax,
                    net_passengers_cleared=cleared_pax,
                )

                # Apply state changes
                working_alloc[best_source] -= transfer_qty
                # Move is in-transit until arrival time
                in_transit_arrivals.append((arr_dt, best_dest, transfer_qty, assigned_v_ids))

                repositioning_moves.append(
                    RepositioningMove(
                        source_stop=best_source,
                        destination_stop=best_dest,
                        buses_to_transfer=transfer_qty,
                        from_stop=best_source,
                        to_stop=best_dest,
                        buses_to_move=transfer_qty,
                        assigned_vehicle_ids=assigned_v_ids,
                        departure_time=dep_dt.isoformat(),
                        arrival_time=arr_dt.isoformat(),
                        travel_time_minutes=travel_time_min,
                        interval_timestamp=interval_ts,
                        tradeoff=tradeoff_obj,
                        source_service_loss=source_loss,
                        expected_benefit=expected_benefit,
                        network_effect=network_effect,
                    )
                )

        # Resolve all remaining in-transit arrivals into final allocation
        for _, dest_stop, qty, _ in in_transit_arrivals:
            working_alloc[dest_stop] += qty

        # Invariant Check: Strict Fixed Fleet Conservation
        final_fleet_sum = sum(working_alloc.values())
        if final_fleet_sum != f_total:
            raise RuntimeError(
                f"Fleet Conservation Invariant Violated! "
                f"Initial fleet: {f_total}, Final fleet: {final_fleet_sum}"
            )

        # Calculate network queue reduction
        reduction_pct, unserved_before, unserved_after = calculate_network_queue_reduction(
            demand_by_stop=cumulative_demand_snapshot,
            allocation_before=current_alloc,
            allocation_after=working_alloc,
            bus_capacity=effective_capacity,
        )

        plan_id = f"opt-plan-{int(base_dt.timestamp()) % 10000:04d}"

        return OptimizeResponse(
            plan_id=plan_id,
            total_fleet_size=f_total,
            fleet_conserved=True,
            repositioning_moves=repositioning_moves,
            final_allocation=working_alloc,
            overall_queue_reduction_percentage=reduction_pct,
            unserved_demand_before=unserved_before,
            unserved_demand_after=unserved_after,
            capacity_provenance=cap_provenance,
            warnings=warnings,
            modeled_assumptions=modeled_assumptions,
            status="SUCCESS",
            message=(
                f"Optimal plan generated with {len(repositioning_moves)} vehicle movements "
                f"conserving {f_total} buses across {len(interval_keys)} forecast intervals."
            ),
        )


# Global optimizer instance
optimizer = FixedFleetOptimizer()


def optimize_transport(
    festival_id: str,
    total_fleet_size: int,
    current_allocation: Dict[str, int],
    predicted_demand_profile: Optional[Dict[str, int]] = None,
    stop_forecast: Optional[List[Dict[str, Any]]] = None,
    bus_inventory: Optional[List[Dict[str, Any]]] = None,
    max_staging_capacity: Optional[Dict[str, int]] = None,
    min_service_per_stop: int = 1,
    time_horizon_minutes: int = 120,
    interval_minutes: int = 15,
    departure_timestamp: Optional[str] = None,
    use_synthetic_capacity_fallback: bool = True,
    bus_capacity: Optional[int] = None,
) -> OptimizeResponse:
    """
    Public importable function exposed for Gugaan's AI Copilot and external modules.
    Accepts raw dictionaries or values, executes deterministic optimization,
    and returns a structured OptimizeResponse.
    """
    inventory_items = None
    if bus_inventory:
        inventory_items = [BusInventoryItem(**b) for b in bus_inventory]

    request = OptimizeRequest(
        festival_id=festival_id,
        total_fleet_size=total_fleet_size,
        current_allocation=current_allocation,
        predicted_demand_profile=predicted_demand_profile,
        stop_forecast=stop_forecast,
        bus_inventory=inventory_items,
        max_staging_capacity=max_staging_capacity,
        min_service_per_stop=min_service_per_stop,
        time_horizon_minutes=time_horizon_minutes,
        interval_minutes=interval_minutes,
        departure_timestamp=departure_timestamp,
        use_synthetic_capacity_fallback=use_synthetic_capacity_fallback,
        bus_capacity=bus_capacity,
    )
    return optimizer.optimize(request)


def get_plan_tradeoffs(plan: OptimizeResponse) -> Dict[str, Any]:
    """
    Structured trade-off retrieval interface compatible with Gugaan's AI tools (get_tradeoffs).
    Provides structured before/after metrics and text explanations for LLM consumption.
    """
    moves_tradeoffs = []
    for move in plan.repositioning_moves:
        moves_tradeoffs.append({
            "source_stop": move.source_stop,
            "destination_stop": move.destination_stop,
            "buses_to_transfer": move.buses_to_transfer,
            "departure_time": move.departure_time,
            "arrival_time": move.arrival_time,
            "travel_time_minutes": move.travel_time_minutes,
            "source_service_loss": move.source_service_loss,
            "expected_benefit": move.expected_benefit,
            "network_effect": move.network_effect,
        })

    return {
        "plan_id": plan.plan_id,
        "total_fleet_size": plan.total_fleet_size,
        "fleet_conserved": plan.fleet_conserved,
        "overall_queue_reduction_percentage": plan.overall_queue_reduction_percentage,
        "unserved_demand_before": plan.unserved_demand_before,
        "unserved_demand_after": plan.unserved_demand_after,
        "capacity_provenance": plan.capacity_provenance,
        "modeled_assumptions": plan.modeled_assumptions,
        "moves": moves_tradeoffs,
    }
