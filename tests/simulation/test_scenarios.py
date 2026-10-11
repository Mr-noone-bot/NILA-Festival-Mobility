"""
Tests for NILA Simulation Scenarios Module (backend/simulation/scenarios.py)
Owned by: Gugaan
"""

import pytest
from backend.simulation.models import ScenarioParameters
from backend.simulation.scenarios import get_preset_scenario, list_presets, PRESET_SCENARIOS


def test_list_presets():
    """Verify that all preset scenarios are listed and valid."""
    presets = list_presets()
    assert len(presets) >= 4
    assert "super_peak_attendance" in presets
    assert "monsoon_rain_surge" in presets
    assert "chariot_procession_delay" in presets
    assert "transit_depot_breakdown" in presets


def test_get_preset_scenario():
    """Verify retrieval of specific preset scenarios with case/separator tolerance."""
    preset = get_preset_scenario("monsoon-rain-surge")
    assert preset.rain_probability == 80.0

    preset_upper = get_preset_scenario("SUPER PEAK ATTENDANCE")
    assert preset_upper.attendance_multiplier == 1.40


def test_get_preset_invalid_name():
    """Non-existent scenario name raises KeyError."""
    with pytest.raises(KeyError):
        get_preset_scenario("invalid_scenario_xyz")


def test_scenario_validation_attendance():
    """attendance_multiplier must be strictly positive."""
    ScenarioParameters(attendance_multiplier=0.1)
    ScenarioParameters(attendance_multiplier=2.5)

    with pytest.raises(ValueError):
        ScenarioParameters(attendance_multiplier=0.0)

    with pytest.raises(ValueError):
        ScenarioParameters(attendance_multiplier=-1.0)


def test_scenario_validation_rain():
    """rain_probability must be between 0.0 and 100.0."""
    ScenarioParameters(rain_probability=0.0)
    ScenarioParameters(rain_probability=100.0)

    with pytest.raises(ValueError):
        ScenarioParameters(rain_probability=-5.0)

    with pytest.raises(ValueError):
        ScenarioParameters(rain_probability=105.0)


def test_scenario_validation_delay():
    """event_delay_minutes cannot be negative."""
    ScenarioParameters(event_delay_minutes=0)
    ScenarioParameters(event_delay_minutes=60)

    with pytest.raises(ValueError):
        ScenarioParameters(event_delay_minutes=-15)


def test_scenario_validation_bus_failure():
    """bus_failure cannot be negative."""
    ScenarioParameters(bus_failure=0)
    ScenarioParameters(bus_failure=5)

    with pytest.raises(ValueError):
        ScenarioParameters(bus_failure=-1)
