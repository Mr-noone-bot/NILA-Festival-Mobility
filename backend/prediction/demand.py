"""
NILA Demand & Passenger Capacity Module
Calculates theoretical passenger arrivals, departures, and required vehicle counts.
Does NOT allocate or move vehicles (Allocation is strictly owned by the Optimizer).
Owned by: Gugaan
"""

import math


def calculate_effective_bus_capacity(
    bus_capacity: int = 50,
    load_factor: float = 0.85
) -> float:
    """
    Computes effective passenger throughput per bus:
    effective_bus_capacity = bus_capacity * load_factor
    
    Default: 50 * 0.85 = 42.5 passengers/bus.
    """
    nom_cap = max(1, int(bus_capacity))
    l_factor = max(0.1, float(load_factor))
    return round(nom_cap * l_factor, 2)


def calculate_passenger_arrivals(
    predicted_crowd: int,
    outbound_rate: float,
    weather_rush_multiplier: float = 1.0
) -> int:
    """
    Computes passengers arriving at a specific stop during the 15-minute interval.
    
    Distinguishes active zone crowd from transit arrivals.
    """
    if predicted_crowd <= 0:
        return 0

    rate = max(0.0, min(1.0, float(outbound_rate)))
    rush = max(0.5, float(weather_rush_multiplier))

    effective_rate = min(1.0, rate * rush)
    arrivals = int(round(predicted_crowd * effective_rate))
    return max(0, min(predicted_crowd, arrivals))


def calculate_service_capacity(
    available_buses: int,
    effective_bus_capacity: float,
    trips_per_interval: float = 1.0
) -> int:
    """
    Calculates theoretical passenger clearance capacity for a stop
    given baseline stationed buses in that 15-minute interval.
    """
    if available_buses <= 0 or effective_bus_capacity <= 0:
        return 0

    trips = max(0.1, float(trips_per_interval))
    capacity = int(math.floor(available_buses * effective_bus_capacity * trips))
    return max(0, capacity)


def calculate_actual_departures(
    pending_demand: int,
    service_capacity: int
) -> int:
    """
    Passenger departures cannot exceed pending passengers (queue + arrivals)
    or available service capacity.
    """
    demand = max(0, int(pending_demand))
    cap = max(0, int(service_capacity))
    return min(demand, cap)


def calculate_required_buses(
    passenger_demand: int,
    effective_bus_capacity: float
) -> int:
    """
    Computes theoretical buses needed to serve passenger demand:
    required_buses = ceil(passenger_demand / effective_bus_capacity)
    
    NOTE: This is THEORETICAL DEMAND, not an actual bus allocation.
    The prediction engine never moves or creates fleet vehicles.
    """
    if passenger_demand <= 0:
        return 0

    eff_cap = max(1.0, float(effective_bus_capacity))
    return int(math.ceil(passenger_demand / eff_cap))
