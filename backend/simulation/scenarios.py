"""
NILA Predefined Scenarios Catalog
Preset what-if configurations for festival simulation analysis.
Owned by: Gugaan
"""

from typing import Dict
from backend.simulation.models import ScenarioParameters

PRESET_SCENARIOS: Dict[str, ScenarioParameters] = {
    "super_peak_attendance": ScenarioParameters(
        attendance_multiplier=1.40,
        rain_probability=0.0,
        event_delay_minutes=0,
        bus_failure=0,
    ),
    "monsoon_rain_surge": ScenarioParameters(
        attendance_multiplier=0.90,
        rain_probability=80.0,
        event_delay_minutes=0,
        bus_failure=0,
    ),
    "chariot_procession_delay": ScenarioParameters(
        attendance_multiplier=1.10,
        rain_probability=10.0,
        event_delay_minutes=30,
        bus_failure=0,
    ),
    "transit_depot_breakdown": ScenarioParameters(
        attendance_multiplier=1.0,
        rain_probability=0.0,
        event_delay_minutes=0,
        bus_failure=3,
    ),
    "compound_weather_delay_crisis": ScenarioParameters(
        attendance_multiplier=1.30,
        rain_probability=65.0,
        event_delay_minutes=45,
        bus_failure=2,
    ),
}


def get_preset_scenario(name: str) -> ScenarioParameters:
    """Retrieves a predefined scenario by name or raises KeyError."""
    slug = name.lower().strip().replace("-", "_").replace(" ", "_")
    if slug not in PRESET_SCENARIOS:
        raise KeyError(
            f"Scenario '{name}' not found. Available presets: {list(PRESET_SCENARIOS.keys())}"
        )
    return PRESET_SCENARIOS[slug].model_copy(deep=True)


def list_presets() -> Dict[str, ScenarioParameters]:
    """Returns a dictionary of all available scenario presets."""
    return {k: v.model_copy(deep=True) for k, v in PRESET_SCENARIOS.items()}
