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
            Stop(id="stop-periyar", name="Periyar Bus Stand", capacity=1500, weight=0.45, current_buses=8),
            Stop(id="stop-aarapalayam", name="Aarapalayam Bus Stand", capacity=1200, weight=0.35, current_buses=6),
            Stop(id="stop-mattuthavani", name="Mattuthavani (MIBT)", capacity=3000, weight=0.20, current_buses=6),
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

    if raw_data and isinstance(raw_data, dict) and "items" in raw_data:
        items = raw_data["items"]
        for item in items:
            try:
                festivals.append(Festival.model_validate(item))
            except Exception:
                continue

    # If data file has no items yet, expose fallback definitions
    if not festivals:
        festivals = list(DEFAULT_FALLBACK_FESTIVALS.values())

    return festivals


def load_stops() -> List[Stop]:
    """
    Loads stops from data/stops.json.
    """
    raw_data = load_json_file("stops.json", required=False)
    stops: List[Stop] = []

    if raw_data and isinstance(raw_data, dict) and "items" in raw_data:
        for item in raw_data["items"]:
            try:
                stops.append(Stop.model_validate(item))
            except Exception:
                continue

    return stops


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
