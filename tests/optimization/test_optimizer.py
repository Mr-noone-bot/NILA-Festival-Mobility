"""
NILA Optimization Engine Tests
Verifies the Fixed-Fleet Invariant, non-negativity, capacity constraints,
Gugaan singular stop_forecast schema, multi-interval scheduling, staging limits,
individual vehicle inventory status handling, and explicit capacity provenance.
"""

import pytest
from datetime import datetime, timezone, timedelta
from backend.optimization.engine import FixedFleetOptimizer
from backend.api.schemas import OptimizeRequest, BusInventoryItem
from backend.optimization.models import BusEntity
from backend.core.constants import BusStatus


@pytest.fixture
def optimizer():
    return FixedFleetOptimizer()


def test_fixed_fleet_conservation_invariant(optimizer):
    """
    Core Invariant: Fleet size is conserved.
    Initial: 20 buses across 3 stops.
    Final: Exactly 20 buses across 3 stops.
    """
    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=20,
        current_allocation={
            "stop-periyar": 5,
            "stop-aarapalayam": 5,
            "stop-mattuthavani": 10,
        },
        predicted_demand_profile={
            "stop-periyar": 4200,      # High demand
            "stop-aarapalayam": 1800,  # Medium demand
            "stop-mattuthavani": 200,  # Surplus stop
        },
        time_horizon_minutes=120,
        departure_timestamp="2026-10-10T20:15:00+05:30",
        use_synthetic_capacity_fallback=True,
    )

    res = optimizer.optimize(req)

    assert res.fleet_conserved is True
    assert res.total_fleet_size == 20
    assert sum(res.final_allocation.values()) == 20
    assert all(count >= 0 for count in res.final_allocation.values())
    assert len(res.repositioning_moves) > 0
    assert res.final_allocation["stop-periyar"] > 5
    assert res.final_allocation["stop-mattuthavani"] < 10
    assert res.overall_queue_reduction_percentage > 0.0
    assert "SYNTHETIC_FALLBACK" in res.capacity_provenance
    assert len(res.warnings) > 0


def test_gugaan_singular_stop_forecast_schema(optimizer):
    """Verify optimizer accepts Gugaan's exact singular stop_forecast field name."""
    gugaan_forecast = [
        {
            "timestamp": "2026-10-10T20:15:00+05:30",
            "stop_id": "stop_main",
            "predicted_crowd": 6500,
            "arrivals": 1200,
            "departures": 1050,
            "queue": 150,
            "required_buses": 29,
            "crowd_pressure": 0.92,
            "risk_score": 91.0,
            "risk_level": "CRITICAL",
        },
        {
            "timestamp": "2026-10-10T20:15:00+05:30",
            "stop_id": "stop_north",
            "predicted_crowd": 300,
            "arrivals": 50,
            "departures": 150,
            "queue": 0,
            "required_buses": 2,
            "crowd_pressure": 0.15,
            "risk_score": 12.0,
            "risk_level": "LOW",
        },
    ]

    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=15,
        current_allocation={
            "stop_main": 5,
            "stop_north": 10,
        },
        stop_forecast=gugaan_forecast,  # Singular contract field
        time_horizon_minutes=120,
        departure_timestamp="2026-10-10T20:15:00+05:30",
        use_synthetic_capacity_fallback=True,
    )

    res = optimizer.optimize(req)

    assert res.fleet_conserved is True
    assert sum(res.final_allocation.values()) == 15
    assert len(res.repositioning_moves) > 0
    move = res.repositioning_moves[0]
    assert move.source_stop == "stop_north"
    assert move.destination_stop == "stop_main"
    assert move.interval_timestamp == "2026-10-10T20:15:00+05:30"


def test_multi_interval_discrete_scheduling(optimizer):
    """Verify optimization schedules across multiple 15-minute forecast intervals without collapsing."""
    multi_interval_forecast = [
        # Interval 1: 20:00
        {
            "timestamp": "2026-10-10T20:00:00+05:30",
            "stop_id": "stop-mattuthavani",
            "predicted_crowd": 100,
            "arrivals": 20,
            "departures": 50,
            "queue": 0,
            "required_buses": 1,
            "crowd_pressure": 0.1,
            "risk_score": 10.0,
            "risk_level": "LOW",
        },
        {
            "timestamp": "2026-10-10T20:00:00+05:30",
            "stop_id": "stop-periyar",
            "predicted_crowd": 2500,
            "arrivals": 600,
            "departures": 300,
            "queue": 100,
            "required_buses": 15,
            "crowd_pressure": 0.8,
            "risk_score": 75.0,
            "risk_level": "HIGH",
        },
        # Interval 2: 20:15
        {
            "timestamp": "2026-10-10T20:15:00+05:30",
            "stop_id": "stop-mattuthavani",
            "predicted_crowd": 150,
            "arrivals": 30,
            "departures": 60,
            "queue": 0,
            "required_buses": 1,
            "crowd_pressure": 0.1,
            "risk_score": 10.0,
            "risk_level": "LOW",
        },
        {
            "timestamp": "2026-10-10T20:15:00+05:30",
            "stop_id": "stop-periyar",
            "predicted_crowd": 4500,
            "arrivals": 1200,
            "departures": 400,
            "queue": 400,
            "required_buses": 25,
            "crowd_pressure": 0.95,
            "risk_score": 92.0,
            "risk_level": "CRITICAL",
        },
    ]

    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=20,
        current_allocation={
            "stop-mattuthavani": 12,
            "stop-periyar": 8,
        },
        stop_forecast=multi_interval_forecast,
        time_horizon_minutes=120,
        interval_minutes=15,
        use_synthetic_capacity_fallback=True,
    )

    res = optimizer.optimize(req)

    assert res.fleet_conserved is True
    assert sum(res.final_allocation.values()) == 20
    assert len(res.repositioning_moves) > 0
    # Verify departure times align with actual interval timestamps
    dep_times = [m.departure_time for m in res.repositioning_moves]
    assert any("20:00:00" in t for t in dep_times)


def test_vehicle_status_and_in_transit_handling(optimizer):
    """Verify OUT_OF_SERVICE and IN_TRANSIT buses cannot be moved, and IDs are assigned without overlap."""
    inventory = [
        # 3 buses at Mattuthavani: 1 active, 1 out of service, 1 in transit
        BusEntity(vehicle_id="BUS-M1", current_stop_id="stop-mattuthavani", status=BusStatus.ACTIVE, capacity=50),
        BusEntity(vehicle_id="BUS-M2", current_stop_id="stop-mattuthavani", status=BusStatus.OUT_OF_SERVICE, capacity=50),
        BusEntity(vehicle_id="BUS-M3", current_stop_id="stop-mattuthavani", status=BusStatus.IN_TRANSIT, capacity=50),
        # 2 buses at Periyar
        BusEntity(vehicle_id="BUS-P1", current_stop_id="stop-periyar", status=BusStatus.ACTIVE, capacity=50),
        BusEntity(vehicle_id="BUS-P2", current_stop_id="stop-periyar", status=BusStatus.ACTIVE, capacity=50),
    ]

    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=5,
        current_allocation={
            "stop-mattuthavani": 3,
            "stop-periyar": 2,
        },
        predicted_demand_profile={
            "stop-mattuthavani": 0,
            "stop-periyar": 2000,
        },
        bus_inventory=[BusInventoryItem(**b.model_dump()) for b in inventory],
        time_horizon_minutes=120,
    )

    res = optimizer.optimize(req)

    assert res.fleet_conserved is True
    assert sum(res.final_allocation.values()) == 5
    # Only BUS-M1 is ACTIVE at Mattuthavani, so only at most 1 bus can be transferred
    if len(res.repositioning_moves) > 0:
        move = res.repositioning_moves[0]
        assert "BUS-M1" in move.assigned_vehicle_ids
        assert "BUS-M2" not in move.assigned_vehicle_ids  # OUT_OF_SERVICE must NOT move
        assert "BUS-M3" not in move.assigned_vehicle_ids  # IN_TRANSIT must NOT move


def test_staging_capacity_limits_enforced(optimizer):
    """Verify destination stops cannot exceed their maximum staging capacity."""
    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=20,
        current_allocation={
            "stop-mattuthavani": 15,
            "stop-periyar": 5,
        },
        predicted_demand_profile={
            "stop-mattuthavani": 0,
            "stop-periyar": 5000,  # Enormous demand
        },
        max_staging_capacity={
            "stop-periyar": 8,  # Hard limit: Periyar can stage AT MOST 8 buses
        },
        time_horizon_minutes=120,
        use_synthetic_capacity_fallback=True,
    )

    res = optimizer.optimize(req)

    assert res.fleet_conserved is True
    assert sum(res.final_allocation.values()) == 20
    # Final allocation at Periyar must NEVER exceed max_staging_capacity of 8
    assert res.final_allocation["stop-periyar"] <= 8


def test_capacity_provenance_labelling(optimizer):
    """Verify synthetic fallback is explicitly labelled and warned."""
    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=10,
        current_allocation={"stop-periyar": 5, "stop-mattuthavani": 5},
        predicted_demand_profile={"stop-periyar": 500, "stop-mattuthavani": 500},
        use_synthetic_capacity_fallback=True,
    )

    res = optimizer.optimize(req)
    assert res.capacity_provenance == "SYNTHETIC_FALLBACK (50 pax/bus)"
    assert any("synthetic capacity fallback" in w.lower() for w in res.warnings)


def test_minimum_service_constraint_respected(optimizer):
    """Ensure that stops are not stripped below min_service_per_stop."""
    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=10,
        current_allocation={
            "stop-mattuthavani": 5,
            "stop-periyar": 5,
        },
        predicted_demand_profile={
            "stop-mattuthavani": 0,    # Zero demand
            "stop-periyar": 5000,      # Extreme demand
        },
        min_service_per_stop=2,        # Minimum floor 2 buses
        time_horizon_minutes=120,
        use_synthetic_capacity_fallback=True,
    )

    res = optimizer.optimize(req)

    assert res.final_allocation["stop-mattuthavani"] >= 2
    assert sum(res.final_allocation.values()) == 10


def test_fleet_mismatch_raises_error(optimizer):
    """Verify that an initial allocation sum not matching total_fleet_size is rejected."""
    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=25,
        current_allocation={
            "stop-periyar": 5,
            "stop-aarapalayam": 5,
            "stop-mattuthavani": 10,
        },
        predicted_demand_profile={"stop-periyar": 1000},
        use_synthetic_capacity_fallback=True,
    )

    with pytest.raises(ValueError, match="Fixed Fleet Invariant Violation"):
        optimizer.optimize(req)


def test_deterministic_repeatability(optimizer):
    """Running optimizer on identical inputs yields identical plans."""
    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=20,
        current_allocation={
            "stop-periyar": 5,
            "stop-aarapalayam": 5,
            "stop-mattuthavani": 10,
        },
        predicted_demand_profile={
            "stop-periyar": 3000,
            "stop-aarapalayam": 1000,
            "stop-mattuthavani": 200,
        },
        time_horizon_minutes=120,
        departure_timestamp="2026-10-10T20:00:00+05:30",
        use_synthetic_capacity_fallback=True,
    )

    res1 = optimizer.optimize(req)
    res2 = optimizer.optimize(req)

    assert res1.final_allocation == res2.final_allocation
    assert len(res1.repositioning_moves) == len(res2.repositioning_moves)


def test_overlapping_assignment_prevention(optimizer):
    """Verify a vehicle cannot be assigned to overlapping simultaneous moves."""
    inventory = [
        BusEntity(vehicle_id="BUS-UNIQUE-1", current_stop_id="stop-mattuthavani", status=BusStatus.ACTIVE, capacity=50),
        BusEntity(vehicle_id="BUS-UNIQUE-2", current_stop_id="stop-mattuthavani", status=BusStatus.ACTIVE, capacity=50),
    ]

    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=2,
        current_allocation={"stop-mattuthavani": 2},
        predicted_demand_profile={"stop-mattuthavani": 0, "stop-periyar": 2000},
        bus_inventory=[BusInventoryItem(**b.model_dump()) for b in inventory],
        time_horizon_minutes=120,
    )

    res = optimizer.optimize(req)
    all_assigned_ids = []
    for move in res.repositioning_moves:
        all_assigned_ids.extend(move.assigned_vehicle_ids)

    # Every vehicle should be assigned at most once per departure
    assert len(all_assigned_ids) == len(set(all_assigned_ids))


def test_unverified_capacity_error_when_fallback_disabled(optimizer):
    """Verify error raised when capacity is unverified and synthetic fallback is disabled."""
    from backend.core.config import settings
    original_setting = settings.ALLOW_SYNTHETIC_CAPACITY_FALLBACK
    settings.ALLOW_SYNTHETIC_CAPACITY_FALLBACK = False

    try:
        req = OptimizeRequest(
            festival_id="madurai-chithirai-2026",
            total_fleet_size=10,
            current_allocation={"stop-periyar": 5, "stop-mattuthavani": 5},
            predicted_demand_profile={"stop-periyar": 500, "stop-mattuthavani": 500},
            use_synthetic_capacity_fallback=False,  # Fallback explicitly disallowed
        )

        with pytest.raises(ValueError, match="Bus capacity is missing and unverified"):
            optimizer.optimize(req)
    finally:
        settings.ALLOW_SYNTHETIC_CAPACITY_FALLBACK = original_setting


def test_negative_allocation_rejected():
    """Verify that negative allocation is rejected by validator."""
    with pytest.raises(ValueError, match="cannot be negative"):
        OptimizeRequest(
            festival_id="madurai-chithirai-2026",
            total_fleet_size=10,
            current_allocation={
                "stop-periyar": -1,
                "stop-mattuthavani": 11,
            },
        )


def test_zero_movements_when_demand_balanced(optimizer):
    """When demand is already balanced across stops, zero moves are made."""
    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=15,
        current_allocation={
            "stop-periyar": 5,
            "stop-aarapalayam": 5,
            "stop-mattuthavani": 5,
        },
        predicted_demand_profile={
            "stop-periyar": 1000,
            "stop-aarapalayam": 1000,
            "stop-mattuthavani": 1000,
        },
        time_horizon_minutes=120,
        use_synthetic_capacity_fallback=True,
    )

    res = optimizer.optimize(req)
    assert len(res.repositioning_moves) == 0
    assert res.final_allocation == req.current_allocation
    assert res.fleet_conserved is True


def test_tradeoff_calculated_from_before_vs_after_and_all_move_fields(optimizer):
    """
    Phase 4 Check 2 & 3:
    Explicitly verify:
      - destination_wait_after < destination_wait_before
      - source_wait_after >= source_wait_before
      - reported_delta == after - before
      - All required move fields: from_stop, to_stop, buses_to_move, departure_time,
        arrival_time, travel_time_minutes, tradeoff, source service loss, destination benefit, network effect.
    """
    from datetime import datetime, timedelta
    from backend.optimization.tradeoffs import calculate_wait_times_and_tradeoff

    # Calculate directly with tradeoff function
    wt = calculate_wait_times_and_tradeoff(
        source_buses_before=8,
        source_buses_after=7,
        dest_buses_before=2,
        dest_buses_after=3,
        nominal_cycle_minutes=60.0,
    )
    assert wt["dest_wait_after"] < wt["dest_wait_before"]
    assert wt["source_wait_after"] >= wt["source_wait_before"]
    assert wt["reported_delta"] == round((wt["dest_wait_after"] + wt["source_wait_after"]) - (wt["dest_wait_before"] + wt["source_wait_before"]), 2)

    # Now verify on optimizer execution
    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=10,
        current_allocation={"stop-mattuthavani": 8, "stop-periyar": 2},
        predicted_demand_profile={"stop-mattuthavani": 50, "stop-periyar": 1000},
        time_horizon_minutes=120,
        use_synthetic_capacity_fallback=True,
    )
    res = optimizer.optimize(req)
    assert len(res.repositioning_moves) > 0
    move = res.repositioning_moves[0]

    # Verify all required fields in the relocation record
    assert move.from_stop is not None and move.from_stop == "stop-mattuthavani"
    assert move.to_stop is not None and move.to_stop == "stop-periyar"
    assert move.buses_to_move is not None and move.buses_to_move > 0
    assert move.departure_time is not None
    assert move.arrival_time is not None
    assert move.travel_time_minutes is not None and move.travel_time_minutes > 0
    assert move.tradeoff is not None
    assert move.source_service_loss != ""
    assert move.expected_benefit != ""
    assert move.network_effect != ""

    # Phase 4 Check 4: Verify departure + travel time = arrival time
    dep_dt = datetime.fromisoformat(move.departure_time)
    arr_dt = datetime.fromisoformat(move.arrival_time)
    expected_arr = dep_dt + timedelta(minutes=move.travel_time_minutes)
    assert arr_dt == expected_arr


def test_fixed_fleet_after_multiple_sequential_moves(optimizer):
    """Phase 4 Check 5: Verify fixed fleet conservation after multiple sequential moves."""
    multi_step_forecast = [
        # Interval 1: 18:00
        {"timestamp": "2026-04-20T18:00:00+05:30", "stop_id": "stop-mattuthavani", "predicted_crowd": 50, "required_buses": 1, "queue": 10, "arrivals": 10, "departures": 5, "crowd_pressure": 0.1, "risk_level": "LOW", "risk_score": 0.1},
        {"timestamp": "2026-04-20T18:00:00+05:30", "stop_id": "stop-periyar", "predicted_crowd": 800, "required_buses": 10, "queue": 300, "arrivals": 150, "departures": 20, "crowd_pressure": 0.9, "risk_level": "HIGH", "risk_score": 0.9},
        {"timestamp": "2026-04-20T18:00:00+05:30", "stop_id": "stop-aarapalayam", "predicted_crowd": 50, "required_buses": 1, "queue": 10, "arrivals": 10, "departures": 5, "crowd_pressure": 0.1, "risk_level": "LOW", "risk_score": 0.1},
        # Interval 2: 18:30 (Aarapalyam surges)
        {"timestamp": "2026-04-20T18:30:00+05:30", "stop_id": "stop-mattuthavani", "predicted_crowd": 50, "required_buses": 1, "queue": 10, "arrivals": 10, "departures": 5, "crowd_pressure": 0.1, "risk_level": "LOW", "risk_score": 0.1},
        {"timestamp": "2026-04-20T18:30:00+05:30", "stop_id": "stop-periyar", "predicted_crowd": 100, "required_buses": 2, "queue": 20, "arrivals": 20, "departures": 10, "crowd_pressure": 0.2, "risk_level": "LOW", "risk_score": 0.2},
        {"timestamp": "2026-04-20T18:30:00+05:30", "stop_id": "stop-aarapalayam", "predicted_crowd": 900, "required_buses": 12, "queue": 400, "arrivals": 200, "departures": 20, "crowd_pressure": 0.95, "risk_level": "HIGH", "risk_score": 0.95},
    ]

    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=15,
        current_allocation={"stop-mattuthavani": 9, "stop-periyar": 3, "stop-aarapalayam": 3},
        stop_forecast=multi_step_forecast,
        time_horizon_minutes=120,
        interval_minutes=15,
        use_synthetic_capacity_fallback=True,
    )

    res = optimizer.optimize(req)
    assert res.fleet_conserved is True
    assert sum(res.final_allocation.values()) == 15
    assert len(res.repositioning_moves) >= 2
    for move in res.repositioning_moves:
        assert move.buses_to_move > 0
        assert move.from_stop in req.current_allocation
        assert move.to_stop in req.current_allocation


def test_no_bus_moved_while_in_transit(optimizer):
    """Phase 4 Check 6: Verify no bus can be moved while already IN_TRANSIT."""
    inventory = [
        BusEntity(vehicle_id="BUS-ACTIVE-1", current_stop_id="stop-mattuthavani", status=BusStatus.ACTIVE, capacity=50),
        BusEntity(vehicle_id="BUS-TRANSIT-1", current_stop_id="stop-mattuthavani", status=BusStatus.IN_TRANSIT, capacity=50),
        BusEntity(vehicle_id="BUS-TRANSIT-2", current_stop_id="stop-mattuthavani", status=BusStatus.IN_TRANSIT, capacity=50),
        BusEntity(vehicle_id="BUS-PERIYAR-1", current_stop_id="stop-periyar", status=BusStatus.ACTIVE, capacity=50),
    ]

    req = OptimizeRequest(
        festival_id="madurai-chithirai-2026",
        total_fleet_size=4,
        current_allocation={"stop-mattuthavani": 3, "stop-periyar": 1},
        predicted_demand_profile={"stop-mattuthavani": 0, "stop-periyar": 1500},
        bus_inventory=[BusInventoryItem(**b.model_dump()) for b in inventory],
        time_horizon_minutes=120,
    )

    res = optimizer.optimize(req)
    assert res.fleet_conserved is True
    assert sum(res.final_allocation.values()) == 4
    for move in res.repositioning_moves:
        assert "BUS-TRANSIT-1" not in move.assigned_vehicle_ids
        assert "BUS-TRANSIT-2" not in move.assigned_vehicle_ids

