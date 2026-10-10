"""
NILA Festival Catalog API Endpoints
Provides metadata for Tamil Nadu temple festivals, sacred perimeter zones, and transit stops.
Adheres to contracts defined in docs/api/contracts.md and enforces strict data provenance.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.core.config import settings
from backend.api.schemas import (
    FestivalSummary,
    FestivalDetail,
    PeakEvent,
    TempleDetail,
    TempleCoordinates,
    StopDetail,
    StopCoordinate,
)

router = APIRouter(tags=["Festivals"])


# Synthetic Simulation Catalog for Madurai Chithirai Thiruvizha
# Clearly marked as unverified development fixture
SYNTHETIC_FESTIVALS: Dict[str, Dict[str, Any]] = {
    "madurai-chithirai-2026": {
        "id": "madurai-chithirai-2026",
        "name": "Chithirai Thiruvizha",
        "city": "Madurai",
        "temple_id": "meenakshi-amman",
        "start_date": "2026-04-20",
        "end_date": "2026-05-01",
        "expected_peak_day": "2026-04-28",
        "peak_events": [
            {
                "name": "Chariot Procession (Ther)",
                "timestamp": "2026-04-28T08:00:00+05:30",
                "estimated_turnout": 500000,
            }
        ],
        "temple": {
            "id": "meenakshi-amman",
            "name": "Meenakshi Sundareswarar Temple",
            "coordinates": {"latitude": 9.9195, "longitude": 78.1193},
            "gates": ["East Tower", "West Tower", "North Tower", "South Tower"],
        },
        "stops": [
            {
                "id": "stop-periyar",
                "name": "Periyar Bus Stand",
                "capacity": 1500,
                "coordinates": {"lat": 9.9167, "lng": 78.1132},
            },
            {
                "id": "stop-aarapalayam",
                "name": "Aarapalayam Bus Stand",
                "capacity": 1200,
                "coordinates": {"lat": 9.9326, "lng": 78.1064},
            },
            {
                "id": "stop-mattuthavani",
                "name": "Mattuthavani (MIBT)",
                "capacity": 3000,
                "coordinates": {"lat": 9.9482, "lng": 78.1561},
            },
        ],
        "default_fleet_size": 25,
        "is_verified": False,
        "provenance": "SYNTHETIC_FIXTURE",
    }
}


def load_verified_festivals_from_disk() -> Dict[str, Dict[str, Any]]:
    """
    Reads verified festival catalog from data/festivals.json.
    Returns empty dict if data file contains only schema stubs.
    """
    data_path = Path(settings.DATA_DIR) / "festivals.json"
    catalog: Dict[str, Dict[str, Any]] = {}

    if data_path.exists():
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                items = content.get("items", [])
                if isinstance(items, list) and len(items) > 0:
                    for item in items:
                        if isinstance(item, dict) and "id" in item:
                            item_copy = dict(item)
                            item_copy["is_verified"] = True
                            item_copy["provenance"] = "OFFICIAL_DATA"
                            catalog[item["id"]] = item_copy
        except Exception:
            pass

    return catalog


@router.get("/festivals", response_model=List[FestivalSummary], status_code=status.HTTP_200_OK)
async def list_festivals(
    include_synthetic: bool = Query(
        default=False,
        description="Explicitly include synthetic demo fixtures when official data is unpopulated"
    )
) -> List[FestivalSummary]:
    """
    Retrieves the list of supported Tamil Nadu temple festivals.
    Returns verified official data by default; returns empty list if unpopulated.
    """
    verified_catalog = load_verified_festivals_from_disk()
    catalog = dict(verified_catalog)

    if include_synthetic:
        # Merge synthetic fixtures for items not present in verified catalog
        for k, v in SYNTHETIC_FESTIVALS.items():
            if k not in catalog:
                catalog[k] = v

    summaries: List[FestivalSummary] = []
    for item in catalog.values():
        peak_events = [
            PeakEvent(
                name=e.get("name", ""),
                timestamp=e.get("timestamp", ""),
                estimated_turnout=e.get("estimated_turnout", 0),
            )
            for e in item.get("peak_events", [])
        ]
        summaries.append(
            FestivalSummary(
                id=item["id"],
                name=item["name"],
                city=item["city"],
                temple_id=item.get("temple_id", item.get("temple", {}).get("id", "")),
                start_date=item.get("start_date", ""),
                end_date=item.get("end_date", ""),
                expected_peak_day=item.get("expected_peak_day", ""),
                peak_events=peak_events,
                is_verified=item.get("is_verified", False),
                provenance=item.get("provenance", "OFFICIAL_DATA" if item.get("is_verified") else "SYNTHETIC_FIXTURE"),
            )
        )
    return summaries


@router.get("/festivals/{festival_id}", response_model=FestivalDetail, status_code=status.HTTP_200_OK)
async def get_festival_details(
    festival_id: str,
    include_synthetic: bool = Query(
        default=False,
        description="Explicitly allow returning synthetic demo fixtures for development testing"
    ),
) -> FestivalDetail:
    """
    Retrieves detailed metadata, zones, nearby bus stops, and routes for a specific festival.
    Returns HTTP 404 if verified record does not exist and include_synthetic is False.
    """
    verified_catalog = load_verified_festivals_from_disk()
    item = verified_catalog.get(festival_id)

    if not item and include_synthetic:
        item = SYNTHETIC_FESTIVALS.get(festival_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Festival with ID '{festival_id}' not found in verified official data. "
                f"Official catalog in data/festivals.json is currently unpopulated."
            ),
        )

    temple_raw = item.get("temple", {})
    temple_coords = temple_raw.get("coordinates", {"latitude": 9.9195, "longitude": 78.1193})
    temple = TempleDetail(
        id=temple_raw.get("id", item.get("temple_id", "")),
        name=temple_raw.get("name", "Temple"),
        coordinates=TempleCoordinates(
            latitude=temple_coords.get("latitude", 9.9195),
            longitude=temple_coords.get("longitude", 78.1193),
        ),
        gates=temple_raw.get("gates", []),
    )

    stops: List[StopDetail] = []
    for s in item.get("stops", []):
        s_coords = s.get("coordinates", {"lat": 9.9167, "lng": 78.1132})
        stops.append(
            StopDetail(
                id=s["id"],
                name=s["name"],
                capacity=s.get("capacity", 1000),
                coordinates=StopCoordinate(
                    lat=s_coords.get("lat", 9.9167),
                    lng=s_coords.get("lng", 78.1132),
                ),
            )
        )

    return FestivalDetail(
        id=item["id"],
        name=item["name"],
        city=item["city"],
        temple=temple,
        stops=stops,
        default_fleet_size=item.get("default_fleet_size", 20),
        is_verified=item.get("is_verified", False),
        provenance=item.get("provenance", "OFFICIAL_DATA" if item.get("is_verified") else "SYNTHETIC_FIXTURE"),
    )
