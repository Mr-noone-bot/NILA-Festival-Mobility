"""
NILA Data Loader Module
Safely loads festival and spatial configurations from project-relative data files.
Owned by: Gugaan
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.prediction.models import Festival, Stop, FestivalEvent


class DataLoaderError(Exception):
    """Base exception for data loading errors."""
    pass


class FestivalNotFoundError(DataLoaderError):
    """Raised when a requested festival is not found in data or fallback."""
    pass


class StopNotFoundError(DataLoaderError):
    """Raised when a requested stop is not found."""
    pass


def get_data_dir() -> Path:
    """Returns project-relative Path to data/ directory."""
    return Path(__file__).resolve().parent.parent.parent / "data"


def load_json_file(filename: str, required: bool = True) -> Any:
    """
    Safely reads a JSON file from the data/ directory.
    Handles missing file and malformed JSON.
    """
    file_path = get_data_dir() / filename
    if not file_path.exists():
        if required:
            raise DataLoaderError(f"Required data file '{filename}' not found at {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise DataLoaderError(f"Malformed JSON in '{filename}': {str(e)}") from e
    except Exception as e:
        raise DataLoaderError(f"Failed to read '{filename}': {str(e)}") from e


# Default fallback templates for known festival profiles
# Used when data/ files only contain empty schemas ("items": [])
DEFAULT_FALLBACK_FESTIVALS: Dict[str, Festival] = {
    "madurai-chithirai-2026": Festival(
        id="madurai-chithirai-2026",
        name="Chithirai Thiruvizha",
        city="Madurai",
        base_attendance=100000,
        intensity=1.2,
        peak_events=[
            FestivalEvent(
                name="Chariot Procession (Ther)",
                start_time="2026-04-28T06:00:00+05:30",
                end_time="2026-04-28T10:00:00+05:30",
                estimated_turnout=120000
            )
        ],
        stops=[
            Stop(id="stop-periyar", name="Periyar Bus Stand", capacity=1500, weight=0.45, current_buses=5),
            Stop(id="stop-aarapalayam", name="Aarapalayam Bus Stand", capacity=1200, weight=0.35, current_buses=5),
            Stop(id="stop-mattuthavani", name="Mattuthavani (MIBT)", capacity=3000, weight=0.20, current_buses=10),
        ],
        default_fleet_size=20
    ),
    "tiruvannamalai-deepam-2026": Festival(
        id="tiruvannamalai-deepam-2026",
        name="Karthigai Deepam",
        city="Tiruvannamalai",
        base_attendance=150000,
        intensity=1.4,
        peak_events=[
            FestivalEvent(
                name="Maha Deepam Lighting",
                start_time="2026-11-23T16:00:00+05:30",
                end_time="2026-11-23T18:00:00+05:30",
                estimated_turnout=180000
            )
        ],
        stops=[
            Stop(id="stop-girivalam-north", name="North Girivalam Stand", capacity=2000, weight=0.40, current_buses=8),
            Stop(id="stop-central-busstand", name="Central Bus Stand", capacity=2500, weight=0.40, current_buses=8),
            Stop(id="stop-temple-east", name="East Gopuram Terminus", capacity=1200, weight=0.20, current_buses=4),
        ],
        default_fleet_size=20
    )
}


def load_festivals() -> List[Festival]:
    """
    Loads festivals from data/festivals.json or fallback definitions.
    """
    raw_data = load_json_file("festivals.json", required=False)
    festivals: List[Festival] = []

    if raw_data and isinstance(raw_data, dict):
        items = raw_data.get("records") or raw_data.get("items", [])
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                fest_id = item.get("id")
                # If festival is known in our operational templates, use configured stops and baseline
                if fest_id in DEFAULT_FALLBACK_FESTIVALS:
                    festivals.append(DEFAULT_FALLBACK_FESTIVALS[fest_id])
                else:
                    festivals.append(Festival.model_validate(item))
            except Exception:
                continue

    # If data file has no items yet, expose fallback definitions
    if not festivals:
        festivals = list(DEFAULT_FALLBACK_FESTIVALS.values())

    return festivals


def load_stops(city: Optional[str] = None) -> List[Stop]:
    """
    Loads stops from data/stops.json, optionally filtered by city.
    """
    raw_data = load_json_file("stops.json", required=False)
    stops: List[Stop] = []

    if raw_data and isinstance(raw_data, dict):
        items = raw_data.get("records") or raw_data.get("items", [])
        for item in items:
            if not isinstance(item, dict):
                continue
            if city and item.get("city", "").lower() != city.lower():
                continue
            try:
                coords = item.get("coordinates")
                if not coords and "latitude" in item and "longitude" in item:
                    coords = {"lat": item["latitude"], "lng": item["longitude"]}
                stop_obj = Stop(
                    id=item.get("id") or item.get("stop_id", ""),
                    name=item.get("name", ""),
                    capacity=item.get("passenger_capacity") or item.get("capacity", 1500),
                    weight=item.get("weight"),
                    current_buses=item.get("current_buses", 0),
                    coordinates=coords,
                )
                stops.append(stop_obj)
            except Exception:
                continue

    return stops


def load_buses() -> Dict[str, Any]:
    """
    Loads fixed fleet inventory from data/buses.json.
    """
    data = load_json_file("buses.json", required=False)
    if not data or not isinstance(data, dict):
        return {"records": [], "fleet_metadata": {"total_fleet_size": 20, "initial_allocation": {}}}
    return data


def load_crowd_profiles() -> List[Dict[str, Any]]:
    """
    Loads crowd profiles from data/crowd_profiles.json.
    """
    data = load_json_file("crowd_profiles.json", required=False)
    if data and isinstance(data, dict):
        return data.get("records", [])
    return []


def get_crowd_profile(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Finds a crowd profile by profile_id or label.
    """
    slug = identifier.lower().strip()
    for profile in load_crowd_profiles():
        if profile.get("profile_id", "").lower() == slug or profile.get("label", "").lower() == slug:
            return profile
    return None


def load_weather_profiles() -> List[Dict[str, Any]]:
    """
    Loads weather profiles from data/weather_profiles.json.
    """
    data = load_json_file("weather_profiles.json", required=False)
    if data and isinstance(data, dict):
        return data.get("records", [])
    return []


def get_weather_profile(condition: str) -> Optional[Dict[str, Any]]:
    """
    Finds a weather profile by profile_id or condition name.
    """
    slug = condition.lower().strip()
    for profile in load_weather_profiles():
        if profile.get("profile_id", "").lower() == slug or profile.get("condition", "").lower() == slug:
            return profile
    return None


def load_scenarios() -> List[Dict[str, Any]]:
    """
    Loads simulation scenarios from data/scenarios.json.
    """
    data = load_json_file("scenarios.json", required=False)
    if data and isinstance(data, dict):
        return data.get("records", [])
    return []


def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    """
    Finds a simulation scenario by scenario_id.
    """
    slug = scenario_id.lower().strip().replace("-", "_")
    for sc in load_scenarios():
        if sc.get("scenario_id", "").lower().replace("-", "_") == slug:
            return sc
    return None


def load_temples() -> List[Dict[str, Any]]:
    """
    Loads temple definitions from data/temples.json.
    """
    data = load_json_file("temples.json", required=False)
    if data and isinstance(data, dict):
        return data.get("records", [])
    return []


def load_routes() -> List[Dict[str, Any]]:
    """
    Loads transport routes from data/routes.json.
    """
    data = load_json_file("routes.json", required=False)
    if data and isinstance(data, dict):
        return data.get("records", [])
    return []


def get_festival(festival_id: str) -> Festival:
    """
    Retrieves a specific festival by ID.
    Raises FestivalNotFoundError if not found.
    """
    if not festival_id:
        raise FestivalNotFoundError("Festival ID cannot be empty.")

    # 1. Search in data/festivals.json
    all_festivals = load_festivals()
    for f in all_festivals:
        if f.id == festival_id:
            return f

    # 2. Check default fallback dictionary
    if festival_id in DEFAULT_FALLBACK_FESTIVALS:
        return DEFAULT_FALLBACK_FESTIVALS[festival_id]

    raise FestivalNotFoundError(f"Festival with ID '{festival_id}' was not found.")
