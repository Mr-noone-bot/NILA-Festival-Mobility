"""
NILA Trade-off Engine
Calculates explicit before-and-after consequences of bus repositioning decisions.
Enforces that every bus movement transparently balances source loss vs destination relief.
Distinguishes mathematically observed throughput differences from modeled headway assumptions.
"""

from typing import Dict, Tuple
from backend.core.constants import DEFAULT_BUS_CAPACITY


def calculate_stop_unserved_demand(demand: int, allocated_buses: int, bus_capacity: int = DEFAULT_BUS_CAPACITY) -> int:
    """Calculate passenger queue exceeding vehicle boarding capacity."""
    service_capacity = allocated_buses * bus_capacity
    return max(0, demand - service_capacity)


def calculate_stop_wait_time_minutes(allocated_buses: int, nominal_cycle_minutes: float = 60.0) -> float:
    """Estimated passenger waiting time based on half-headway rule (H / 2)."""
    buses = max(1, allocated_buses)
    headway = nominal_cycle_minutes / buses
    return round(headway / 2.0, 2)


def calculate_wait_times_and_tradeoff(
    source_buses_before: int,
    source_buses_after: int,
    dest_buses_before: int,
    dest_buses_after: int,
    nominal_cycle_minutes: float = 60.0,
) -> Dict[str, float]:
    """
    Explicitly calculates BEFORE vs AFTER waiting times and verifies delta = after - before.
    """
    dest_wait_before = calculate_stop_wait_time_minutes(dest_buses_before, nominal_cycle_minutes)
    dest_wait_after = calculate_stop_wait_time_minutes(dest_buses_after, nominal_cycle_minutes)
    dest_delta = round(dest_wait_after - dest_wait_before, 2)

    source_wait_before = calculate_stop_wait_time_minutes(source_buses_before, nominal_cycle_minutes)
    source_wait_after = calculate_stop_wait_time_minutes(source_buses_after, nominal_cycle_minutes)
    source_delta = round(source_wait_after - source_wait_before, 2)

    # Net waiting delta across affected stops: after - before
    reported_delta = round((dest_wait_after + source_wait_after) - (dest_wait_before + source_wait_before), 2)

    return {
        "dest_wait_before": dest_wait_before,
        "dest_wait_after": dest_wait_after,
        "dest_delta": dest_delta,
        "source_wait_before": source_wait_before,
        "source_wait_after": source_wait_after,
        "source_delta": source_delta,
        "reported_delta": reported_delta,
    }


def evaluate_movement_consequences(
    source_stop: str,
    dest_stop: str,
    buses_to_transfer: int,
    source_demand: int,
    dest_demand: int,
    source_buses_before: int,
    dest_buses_before: int,
    travel_time_minutes: int,
    bus_capacity: int = DEFAULT_BUS_CAPACITY,
) -> Tuple[str, str, str]:
    """
    Computes human-readable source service loss, expected destination benefit,
    and network throughput impact with explicit distinction between calculated facts
    and modeled headway estimates.
    """
    source_buses_after = source_buses_before - buses_to_transfer
    dest_buses_after = dest_buses_before + buses_to_transfer

    source_cap_before = source_buses_before * bus_capacity
    source_cap_after = source_buses_after * bus_capacity

    dest_cap_before = dest_buses_before * bus_capacity
    dest_cap_after = dest_buses_after * bus_capacity

    # 1. Source Service Loss Evaluation
    if source_cap_after >= source_demand:
        source_loss = (
            f"Capacity reduced by {buses_to_transfer * bus_capacity} pax ({source_buses_before} -> {source_buses_after} buses); "
            f"remaining capacity ({source_cap_after} pax) continues to satisfy local demand ({source_demand} pax)."
        )
    else:
        headway_increase = round(60.0 / max(1, source_buses_after) - 60.0 / max(1, source_buses_before))
        source_loss = (
            f"Boarding capacity reduced by {buses_to_transfer * bus_capacity} pax ({source_buses_before} -> {source_buses_after} buses); "
            f"[MODELED ESTIMATE: ~+{max(1, headway_increase)} min headway under nominal 60-min loop cycle]."
        )

    # 2. Destination Benefit Evaluation
    dest_unserved_before = max(0, dest_demand - dest_cap_before)
    dest_unserved_after = max(0, dest_demand - dest_cap_after)
    cleared_passengers = dest_unserved_before - dest_unserved_after

    if dest_unserved_before > 0:
        relief_pct = round((cleared_passengers / dest_unserved_before) * 100, 1)
        expected_benefit = (
            f"+{buses_to_transfer * bus_capacity} boarding capacity added ({dest_buses_before} -> {dest_buses_after} buses); "
            f"reduces unserved queue by -{relief_pct}% (-{cleared_passengers:,} waiting passengers cleared)."
        )
    else:
        expected_benefit = (
            f"Strengthens service buffer at {dest_stop} by +{buses_to_transfer * bus_capacity} pax capacity."
        )

    # 3. Network Effect
    net_cleared = (dest_unserved_before - dest_unserved_after) - (
        max(0, source_demand - source_cap_after) - max(0, source_demand - source_cap_before)
    )
    if net_cleared > 0:
        network_effect = (
            f"+{net_cleared:,} net passengers cleared across network; "
            f"transfer completes in {travel_time_minutes} mins via road corridor."
        )
    else:
        network_effect = (
            f"Rebalanced fleet distribution across corridors; "
            f"transfer transit duration is {travel_time_minutes} mins."
        )

    return source_loss, expected_benefit, network_effect


def calculate_network_queue_reduction(
    demand_by_stop: Dict[str, int],
    allocation_before: Dict[str, int],
    allocation_after: Dict[str, int],
    bus_capacity: int = DEFAULT_BUS_CAPACITY,
) -> Tuple[float, int, int]:
    """
    Computes overall network queue reduction percentage and total unserved before and after.
    Returns (reduction_pct, total_unserved_before, total_unserved_after).
    """
    total_unserved_before = 0
    total_unserved_after = 0

    all_stops = set(demand_by_stop.keys()).union(allocation_before.keys()).union(allocation_after.keys())

    for stop in all_stops:
        dem = demand_by_stop.get(stop, 0)
        buses_before = allocation_before.get(stop, 0)
        buses_after = allocation_after.get(stop, 0)

        total_unserved_before += calculate_stop_unserved_demand(dem, buses_before, bus_capacity)
        total_unserved_after += calculate_stop_unserved_demand(dem, buses_after, bus_capacity)

    if total_unserved_before == 0:
        reduction_pct = 0.0
    else:
        reduction = max(0, total_unserved_before - total_unserved_after)
        reduction_pct = round((reduction / total_unserved_before) * 100.0, 1)

    return reduction_pct, total_unserved_before, total_unserved_after
