"""
NILA Simulation Package
What-if operational scenario simulation and comparative risk evaluation.
Owned by: Gugaan
"""

from backend.simulation.models import (
    ScenarioParameters,
    SimulationInput,
    BaselineSummary,
    ScenarioSummary,
    ChangeMetrics,
    StopComparison,
    SimulationResult,
)
from backend.simulation.scenarios import get_preset_scenario, list_presets, PRESET_SCENARIOS
from backend.simulation.engine import SimulationEngine

__all__ = [
    "SimulationEngine",
    "ScenarioParameters",
    "SimulationInput",
    "BaselineSummary",
    "ScenarioSummary",
    "ChangeMetrics",
    "StopComparison",
    "SimulationResult",
    "get_preset_scenario",
    "list_presets",
    "PRESET_SCENARIOS",
]
