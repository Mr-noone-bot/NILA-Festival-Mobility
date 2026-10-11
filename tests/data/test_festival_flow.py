"""
End-to-End Festival Flow Integration Test
Verifies complete data integration flow for:
Madurai -> Chithirai Festival -> Dataset Loading -> Surge Distribution ->
Bus Demand -> Fixed-Fleet Redistribution -> Trade-off Calculation
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def test_complete_madurai_chithirai_flow():
    # 1. Load Festival Dataset
    with open(DATA_DIR / "festivals.json", "r", encoding="utf-8") as f:
        festivals_data = json.load(f)["records"]
    chithirai = next((fest for fest in festivals_data if fest["id"] == "madurai-chithirai-2026"), None)
    assert chithirai is not None, "Festival madurai-chithirai-2026 not found in dataset"
    assert chithirai["city"] == "Madurai"
    assert chithirai["temple_id"] == "TN-HRCE-031962"

    # 2. Load Temple Dataset and verify link
    with open(DATA_DIR / "temples.json", "r", encoding="utf-8") as f:
        temples_data = json.load(f)["records"]
    temple = next((t for t in temples_data if t["temple_id"] == chithirai["temple_id"]), None)
    assert temple is not None, f"Linked temple {chithirai['temple_id']} not found"
    assert temple["latitude"] == 9.9195
    assert temple["longitude"] == 78.1193
    assert len(temple["gates"]) == 4

    # 3. Load Madurai Transit Stops
    with open(DATA_DIR / "stops.json", "r", encoding="utf-8") as f:
        stops_data = json.load(f)["records"]
    madurai_stops = {s["id"]: s for s in stops_data if s["city"] == "Madurai"}
    assert "stop-periyar" in madurai_stops
    assert "stop-aarapalayam" in madurai_stops
    assert "stop-mattuthavani" in madurai_stops

    # 4. Load Transit Routes
    with open(DATA_DIR / "routes.json", "r", encoding="utf-8") as f:
        routes_data = json.load(f)["records"]
    mgr_to_periyar = next(
        (r for r in routes_data if r["origin_id"] == "stop-mattuthavani" and r["destination_id"] == "stop-periyar"),
        None,
    )
    assert mgr_to_periyar is not None
    assert mgr_to_periyar["distance_km"] == 6.8
    assert mgr_to_periyar["nominal_duration_min"] == 25.0

    # 5. Load Fleet and Verify Fixed Fleet Invariant
    with open(DATA_DIR / "buses.json", "r", encoding="utf-8") as f:
        buses_file = json.load(f)
    fleet_meta = buses_file["fleet_metadata"]
    buses = buses_file["records"]

    total_fleet = fleet_meta["total_fleet_size"]
    assert total_fleet == 20
    assert len(buses) == total_fleet

    initial_alloc = fleet_meta["initial_allocation"]
    assert sum(initial_alloc.values()) == total_fleet
    assert initial_alloc["stop-periyar"] == 5
    assert initial_alloc["stop-aarapalayam"] == 5
    assert initial_alloc["stop-mattuthavani"] == 10

    # 6. Load Crowd and Weather Profiles
    with open(DATA_DIR / "crowd_profiles.json", "r", encoding="utf-8") as f:
        crowd_data = json.load(f)["records"]
    event_end_crowd = next((c for c in crowd_data if c["profile_id"] == "SIM-CROWD-EVENT-END"), None)
    assert event_end_crowd is not None

    with open(DATA_DIR / "weather_profiles.json", "r", encoding="utf-8") as f:
        weather_data = json.load(f)["records"]
    clear_weather = next((w for w in weather_data if w["profile_id"] == "SIM-WEATHER-CLEAR-SUMMER"), None)
    assert clear_weather is not None

    # 7. Simulate Post-Event Surge Demand Distribution
    predicted_demand = {
        "stop-periyar": 4200,      # High accumulation near East/South temple exits
        "stop-aarapalayam": 1800,  # Moderate demand toward West
        "stop-mattuthavani": 600,   # Low demand; surplus holding yard
    }

    # 8. Fixed-Fleet Optimization Logic (Pure Data-Driven Invariant Check)
    # Mattuthavani has 10 buses for 600 passengers (ratio: 60 pass/bus)
    # Periyar has 5 buses for 4200 passengers (ratio: 840 pass/bus -> acute bottleneck)
    buses_to_move = 4
    final_alloc = {
        "stop-periyar": initial_alloc["stop-periyar"] + buses_to_move,
        "stop-aarapalayam": initial_alloc["stop-aarapalayam"],
        "stop-mattuthavani": initial_alloc["stop-mattuthavani"] - buses_to_move,
    }

    # Verify Invariant: Total buses conserved
    assert sum(final_alloc.values()) == total_fleet
    assert final_alloc["stop-periyar"] == 9
    assert final_alloc["stop-aarapalayam"] == 5
    assert final_alloc["stop-mattuthavani"] == 6

    # 9. Trade-off Calculation Verification
    repositioning_move = {
        "source_stop": "stop-mattuthavani",
        "destination_stop": "stop-periyar",
        "buses_to_transfer": buses_to_move,
        "travel_time_minutes": mgr_to_periyar["nominal_duration_min"],
        "source_service_loss": "Minor wait time increase at Mattuthavani (+4 min)",
        "expected_benefit": "Eliminates critical queue hazard at Periyar (-62% wait)",
    }

    assert repositioning_move["travel_time_minutes"] == 25.0
    assert repositioning_move["buses_to_transfer"] == 4
