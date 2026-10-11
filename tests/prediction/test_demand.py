"""
Tests for NILA Demand Module (backend/prediction/demand.py)
Owned by: Gugaan
"""

import pytest
from backend.prediction.demand import (
    calculate_effective_bus_capacity,
    calculate_passenger_arrivals,
    calculate_service_capacity,
    calculate_actual_departures,
    calculate_required_buses,
)


def test_effective_bus_capacity_default():
    """Default 50-seater bus at 0.85 load factor gives 42.5 passengers."""
    cap = calculate_effective_bus_capacity(bus_capacity=50, load_factor=0.85)
    assert cap == 42.5


def test_effective_bus_capacity_custom():
    """Custom vehicle capacity and load factor."""
    cap = calculate_effective_bus_capacity(bus_capacity=60, load_factor=1.0)
    assert cap == 60.0
    # Minimum bounds
    assert calculate_effective_bus_capacity(bus_capacity=0, load_factor=0.0) >= 0.1


def test_passenger_arrivals():
    """Arrivals calculation scales with predicted crowd and outbound rate."""
    crowd = 10000
    outbound = 0.20
    arrivals = calculate_passenger_arrivals(crowd, outbound)
    assert arrivals == 2000

    # Arrival with weather rush multiplier
    arrivals_rain = calculate_passenger_arrivals(crowd, outbound, weather_rush_multiplier=1.25)
    assert arrivals_rain == 2500

    # Never exceeds total predicted crowd
    assert calculate_passenger_arrivals(500, 1.5) == 500
    assert calculate_passenger_arrivals(0, 0.20) == 0


def test_service_capacity_calculation():
    """Available buses multiplied by effective capacity and trips."""
    # 5 buses, 40 passengers/bus, 1 trip per 15-min interval = 200 capacity
    cap = calculate_service_capacity(available_buses=5, effective_bus_capacity=40.0)
    assert cap == 200

    # 0 buses gives 0 capacity
    assert calculate_service_capacity(available_buses=0, effective_bus_capacity=40.0) == 0


def test_actual_departures_bounded():
    """Departures cannot exceed pending demand or available capacity."""
    # Capacity is 200, demand is 150 -> departs 150
    assert calculate_actual_departures(pending_demand=150, service_capacity=200) == 150
    # Capacity is 200, demand is 300 -> departs 200
    assert calculate_actual_departures(pending_demand=300, service_capacity=200) == 200
    # Zero demand
    assert calculate_actual_departures(pending_demand=0, service_capacity=200) == 0


def test_required_buses_calculation():
    """Required buses is ceil(passenger_demand / effective_bus_capacity)."""
    # 100 passengers / 42.5 cap = ceil(2.35) = 3 buses
    assert calculate_required_buses(passenger_demand=100, effective_bus_capacity=42.5) == 3

    # Exact multiple: 85 passengers / 42.5 = 2 buses
    assert calculate_required_buses(passenger_demand=85, effective_bus_capacity=42.5) == 2

    # High demand: 4250 passengers / 42.5 = 100 buses
    assert calculate_required_buses(passenger_demand=4250, effective_bus_capacity=42.5) == 100

    # Zero passengers -> 0 buses
    assert calculate_required_buses(passenger_demand=0, effective_bus_capacity=42.5) == 0
    assert calculate_required_buses(passenger_demand=-10, effective_bus_capacity=42.5) == 0
