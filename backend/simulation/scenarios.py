"""
NILA Predefined Scenarios Catalog
Preset what-if configurations for festival simulation analysis.
Owned by: Gugaan
"""

from typing import Dict
from backend.simulation.models import ScenarioParameters

from typing import Dict
from backend.simulation.models import ScenarioParameters
from backend.prediction.data_loader import load_scenarios

# Core presets loaded dynamically from data/scenarios.json
def _build_scenario_catalog() -> Dict[str, ScenarioParameters]:
    catalog: Dict[str, ScenarioParameters] = {}
    
    # 1. Load from data/scenarios.json
    records = load_scenarios()
    for rec in records:
        sc_id = rec.get("scenario_id")
        if sc_id:
            slug = sc_id.lower().strip().replace("-", "_")
            catalog[slug] = ScenarioParameters(
                attendance_multiplier=float(rec.get("attendance_multiplier", 1.0)),
                rain_probability=float(rec.get("rain_probability", 0.0)),
                event_delay_minutes=int(rec.get("event_delay_minutes", 0)),
                bus_failure=int(rec.get("bus_failure_count", 0)),
            )

    # 2. Add fallback/legacy aliases if not already defined
    legacy_presets = {
        "normal": ScenarioParameters(
            attendance_multiplier=1.0,
            rain_probability=5.0,
            event_delay_minutes=0,
            bus_failure=0,
        ),
        "attendance_120": ScenarioParameters(
            attendance_multiplier=1.20,
            rain_probability=5.0,
            event_delay_minutes=0,
            bus_failure=0,
        ),
        "attendance_150": ScenarioParameters(
            attendance_multiplier=1.50,
            rain_probability=5.0,
            event_delay_minutes=0,
            bus_failure=0,
        ),
        "rain": ScenarioParameters(
            attendance_multiplier=0.95,
            rain_probability=95.0,
            event_delay_minutes=15,
            bus_failure=0,
        ),
        "event_delay_30": ScenarioParameters(
            attendance_multiplier=1.15,
            rain_probability=10.0,
            event_delay_minutes=30,
            bus_failure=0,
        ),
        "bus_failure_1": ScenarioParameters(
            attendance_multiplier=1.0,
            rain_probability=5.0,
            event_delay_minutes=0,
            bus_failure=1,
        ),
        "combined_stress": ScenarioParameters(
            attendance_multiplier=1.35,
            rain_probability=90.0,
            event_delay_minutes=30,
            bus_failure=1,
        ),
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

    for k, v in legacy_presets.items():
        if k not in catalog:
            catalog[k] = v

    return catalog


PRESET_SCENARIOS: Dict[str, ScenarioParameters] = _build_scenario_catalog()


def get_preset_scenario(name: str) -> ScenarioParameters:
    """Retrieves a predefined scenario by name or raises KeyError."""
    slug = name.lower().strip().replace("-", "_").replace(" ", "_")
    # Refresh catalog if needed
    current_catalog = _build_scenario_catalog()
    if slug not in current_catalog:
        raise KeyError(
            f"Scenario '{name}' not found. Available presets: {list(current_catalog.keys())}"
        )
    return current_catalog[slug].model_copy(deep=True)


def list_presets() -> Dict[str, ScenarioParameters]:
    """Returns a dictionary of all available scenario presets."""
    return {k: v.model_copy(deep=True) for k, v in _build_scenario_catalog().items()}
