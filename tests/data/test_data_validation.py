"""
NILA Dataset Integrity & Validation Test Suite
Owner: MADHU (Data Engineer / Data Validation)

Verifies:
- JSON parsing and UTF-8 encoding
- Required fields and schema conformance
- ID uniqueness and conventions
- Provenance and data_type taxonomy
- Referential integrity across datasets
- Geospatial coordinate validity within Tamil Nadu bounding box
- Invariant conservation: Fixed Fleet Invariant (SUM(allocated) == F_total)
- Non-negative numerical constraints
"""

import json
from pathlib import Path
import pytest

DATA_DIR = Path(__file__).parent.parent.parent / "data"
FIXTURE_PATH = Path(__file__).parent / "validation_fixture.json"

REQUIRED_FILES = [
    "festivals.json",
    "temples.json",
    "stops.json",
    "routes.json",
    "buses.json",
    "crowd_profiles.json",
    "weather_profiles.json",
    "scenarios.json",
]

ALLOWED_DATA_TYPES = {"OFFICIAL", "DERIVED", "SIMULATION", "OPERATIONAL_ESTIMATE"}
TAMIL_NADU_BBOX = {"min_lat": 8.0, "max_lat": 13.5, "min_lng": 76.2, "max_lng": 80.4}


def load_dataset(filename: str):
    path = DATA_DIR / filename
    assert path.exists(), f"Missing required data file: {filename}"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict), f"Root of {filename} must be a JSON object"
    assert "records" in data, f"{filename} missing top-level 'records' array"
    assert isinstance(data["records"], list), f"'records' in {filename} must be a list"
    return data


@pytest.fixture(scope="session")
def all_datasets():
    return {fname: load_dataset(fname) for fname in REQUIRED_FILES}


def test_all_required_files_exist():
    """Verify that all 8 required dataset files exist in data/."""
    for fname in REQUIRED_FILES:
        path = DATA_DIR / fname
        assert path.is_file(), f"Dataset file {fname} not found in {DATA_DIR}"


def test_json_parseability_and_utf8(all_datasets):
    """Verify each file is valid UTF-8 JSON with records."""
    for fname, data in all_datasets.items():
        assert len(data["records"]) > 0, f"Dataset {fname} must not be empty"


def test_unique_record_ids(all_datasets):
    """Verify that IDs are unique within each dataset."""
    id_field_map = {
        "festivals.json": "id",
        "temples.json": "temple_id",
        "stops.json": "id",
        "routes.json": "route_id",
        "buses.json": "bus_id",
        "crowd_profiles.json": "profile_id",
        "weather_profiles.json": "profile_id",
        "scenarios.json": "scenario_id",
    }
    for fname, id_field in id_field_map.items():
        records = all_datasets[fname]["records"]
        ids = [r[id_field] for r in records if id_field in r]
        assert len(ids) == len(records), f"Missing {id_field} in some records of {fname}"
        assert len(ids) == len(set(ids)), f"Duplicate IDs detected in {fname}"


def test_provenance_data_types(all_datasets):
    """Verify all records use recognized provenance tags."""
    for fname, data in all_datasets.items():
        for record in data["records"]:
            data_type = record.get("data_type")
            assert data_type is not None, f"Record in {fname} missing 'data_type' tag"
            assert data_type in ALLOWED_DATA_TYPES, (
                f"Record in {fname} has invalid data_type '{data_type}'. "
                f"Allowed: {ALLOWED_DATA_TYPES}"
            )


def test_temple_coordinates_and_gates(all_datasets):
    """Verify temples have valid coordinates and gates in Tamil Nadu."""
    records = all_datasets["temples.json"]["records"]
    assert len(records) >= 3, "Temples dataset must contain at least 3 priority temples"

    for temple in records:
        lat = temple.get("latitude")
        lng = temple.get("longitude")
        assert lat is not None and lng is not None, f"Temple {temple['temple_id']} missing coordinates"
        assert TAMIL_NADU_BBOX["min_lat"] <= lat <= TAMIL_NADU_BBOX["max_lat"], (
            f"Temple {temple['temple_id']} latitude {lat} outside Tamil Nadu bounds"
        )
        assert TAMIL_NADU_BBOX["min_lng"] <= lng <= TAMIL_NADU_BBOX["max_lng"], (
            f"Temple {temple['temple_id']} longitude {lng} outside Tamil Nadu bounds"
        )

        gates = temple.get("gates", [])
        assert len(gates) > 0, f"Temple {temple['temple_id']} must define entrance/exit gates"
        for gate in gates:
            coords = gate["coordinates"]
            assert len(coords) == 2, f"Gate {gate['gate_id']} invalid coordinates"
            assert TAMIL_NADU_BBOX["min_lat"] <= coords[0] <= TAMIL_NADU_BBOX["max_lat"]
            assert TAMIL_NADU_BBOX["min_lng"] <= coords[1] <= TAMIL_NADU_BBOX["max_lng"]
            assert gate["max_flow_per_minute"] > 0, "Gate throughput must be positive"


def test_stop_coordinates_and_capacities(all_datasets):
    """Verify stop locations within Tamil Nadu and positive capacities."""
    records = all_datasets["stops.json"]["records"]
    assert len(records) >= 6, "Stops dataset must contain candidate stops for target cities"

    for stop in records:
        lat = stop["latitude"]
        lng = stop["longitude"]
        assert TAMIL_NADU_BBOX["min_lat"] <= lat <= TAMIL_NADU_BBOX["max_lat"], (
            f"Stop {stop['id']} latitude {lat} out of bounds"
        )
        assert TAMIL_NADU_BBOX["min_lng"] <= lng <= TAMIL_NADU_BBOX["max_lng"], (
            f"Stop {stop['id']} longitude {lng} out of bounds"
        )
        assert stop["passenger_capacity"] > 0, f"Stop {stop['id']} passenger_capacity must be positive"
        assert stop["staging_capacity"] > 0, f"Stop {stop['id']} staging_capacity must be positive"
        assert "attribution" in stop, f"Stop {stop['id']} missing map attribution"


def test_route_referential_integrity_and_metrics(all_datasets):
    """Verify routes reference existing stops and have non-negative distances/durations."""
    valid_stop_ids = {s["id"] for s in all_datasets["stops.json"]["records"]}
    routes = all_datasets["routes.json"]["records"]
    assert len(routes) > 0, "Routes dataset must not be empty"

    for route in routes:
        origin = route.get("origin_id") or route.get("from_stop_id")
        dest = route.get("destination_id") or route.get("to_stop_id")
        assert origin in valid_stop_ids, f"Route {route['route_id']} origin '{origin}' not found in stops.json"
        assert dest in valid_stop_ids, f"Route {route['route_id']} destination '{dest}' not found in stops.json"
        assert route["distance_km"] >= 0, f"Route {route['route_id']} distance cannot be negative"
        assert route["nominal_duration_min"] > 0, f"Route {route['route_id']} duration must be positive"
        assert route["congestion_sensitivity"] >= 1.0, "Congestion multiplier must be at least 1.0"


def test_fixed_fleet_invariant(all_datasets):
    """
    CRITICAL INVARIANT TEST:
    Total fleet size is fixed.
    SUM(allocated buses across all stops) == total_fleet_size
    """
    buses_data = all_datasets["buses.json"]
    fleet_meta = buses_data.get("fleet_metadata", {})
    total_fleet_size = fleet_meta.get("total_fleet_size", 20)
    records = buses_data["records"]

    assert len(records) == total_fleet_size, (
        f"Bus records count ({len(records)}) must match total_fleet_size ({total_fleet_size})"
    )

    initial_alloc = fleet_meta.get("initial_allocation", {})
    allocated_sum = sum(initial_alloc.values())
    assert allocated_sum == total_fleet_size, (
        f"Sum of allocated buses ({allocated_sum}) does not equal total fleet ({total_fleet_size})"
    )

    valid_stop_ids = {s["id"] for s in all_datasets["stops.json"]["records"]}
    for bus in records:
        assert bus["capacity"] > 0, f"Bus {bus['bus_id']} capacity must be positive"
        assert bus["current_stop_id"] in valid_stop_ids, (
            f"Bus {bus['bus_id']} assigned to unknown stop '{bus['current_stop_id']}'"
        )


def test_festival_to_temple_referential_integrity(all_datasets):
    """Verify that each festival references a valid temple in temples.json."""
    temple_ids = {t["temple_id"] for t in all_datasets["temples.json"]["records"]}
    temple_slugs = {t["slug"] for t in all_datasets["temples.json"]["records"]}

    for fest in all_datasets["festivals.json"]["records"]:
        t_id = fest.get("temple_id")
        t_slug = fest.get("temple_slug")
        assert (t_id in temple_ids) or (t_slug in temple_slugs), (
            f"Festival {fest['id']} references unknown temple id '{t_id}' / slug '{t_slug}'"
        )
        assert fest.get("expected_attendance", 0) > 0, "Attendance estimate must be positive"


def test_scenario_referential_integrity_and_inputs(all_datasets):
    """Verify that all scenarios reference valid festivals, profiles, and stops."""
    valid_festivals = {f["id"] for f in all_datasets["festivals.json"]["records"]}
    valid_crowds = {c["profile_id"] for c in all_datasets["crowd_profiles.json"]["records"]}
    valid_weathers = {w["profile_id"] for w in all_datasets["weather_profiles.json"]["records"]}
    valid_stops = {s["id"] for s in all_datasets["stops.json"]["records"]}

    scenarios = all_datasets["scenarios.json"]["records"]
    expected_scenario_ids = {
        "normal",
        "attendance_120",
        "attendance_150",
        "rain",
        "event_delay_30",
        "bus_failure_1",
        "combined_stress",
    }

    found_ids = {s["scenario_id"] for s in scenarios}
    assert expected_scenario_ids.issubset(found_ids), (
        f"Missing standard scenarios: {expected_scenario_ids - found_ids}"
    )

    for sc in scenarios:
        assert sc["festival_id"] in valid_festivals, f"Scenario {sc['scenario_id']} unknown festival"
        assert sc["crowd_profile_id"] in valid_crowds, f"Scenario {sc['scenario_id']} unknown crowd profile"
        assert sc["weather_profile_id"] in valid_weathers, f"Scenario {sc['scenario_id']} unknown weather profile"
        assert sc["attendance_multiplier"] > 0, "Attendance multiplier must be positive"
        assert 0 <= sc["rain_probability"] <= 100, "Rain probability must be 0-100%"
        assert sc["event_delay_minutes"] >= 0, "Delay minutes must be non-negative"
        assert sc["bus_failure_count"] >= 0, "Bus failure count must be non-negative"

        alloc = sc.get("initial_fleet_allocation", {})
        for stop_id, count in alloc.items():
            assert stop_id in valid_stops, f"Scenario {sc['scenario_id']} references unknown stop '{stop_id}'"
            assert count >= 0, "Allocated bus count cannot be negative"
        assert sum(alloc.values()) == sc["total_fleet_size"], "Scenario fleet sum must equal total_fleet_size"
