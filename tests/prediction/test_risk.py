"""
Tests for NILA Risk Module (backend/prediction/risk.py)
Owned by: Gugaan
"""

import pytest
from backend.prediction.models import RiskLevel
from backend.prediction.risk import (
    calculate_crowd_pressure,
    risk_level_from_score,
    calculate_risk_score,
    calculate_network_risk,
)


def test_crowd_pressure_bounds():
    """Crowd pressure must always be clamped between 0.0 and 1.0."""
    # Zero load
    zero_p = calculate_crowd_pressure(queue=0, stop_capacity=1000, arrivals=0, service_capacity=200)
    assert zero_p == 0.0

    # Normal moderate load
    mod_p = calculate_crowd_pressure(queue=300, stop_capacity=1000, arrivals=150, service_capacity=200)
    assert 0.0 <= mod_p <= 1.0

    # Massive overload clamped at 1.0
    over_p = calculate_crowd_pressure(queue=50000, stop_capacity=1000, arrivals=20000, service_capacity=100)
    assert over_p == 1.0


def test_risk_level_thresholds():
    """Risk scores map precisely to designated categorical levels."""
    # 0 - 30: LOW
    assert risk_level_from_score(0) == RiskLevel.LOW
    assert risk_level_from_score(15) == RiskLevel.LOW
    assert risk_level_from_score(30) == RiskLevel.LOW

    # 31 - 60: MODERATE
    assert risk_level_from_score(31) == RiskLevel.MODERATE
    assert risk_level_from_score(45) == RiskLevel.MODERATE
    assert risk_level_from_score(60) == RiskLevel.MODERATE

    # 61 - 80: HIGH
    assert risk_level_from_score(61) == RiskLevel.HIGH
    assert risk_level_from_score(70) == RiskLevel.HIGH
    assert risk_level_from_score(80) == RiskLevel.HIGH

    # 81 - 100: CRITICAL
    assert risk_level_from_score(81) == RiskLevel.CRITICAL
    assert risk_level_from_score(95) == RiskLevel.CRITICAL
    assert risk_level_from_score(100) == RiskLevel.CRITICAL

    # Clamping extreme inputs
    assert risk_level_from_score(-10) == RiskLevel.LOW
    assert risk_level_from_score(150) == RiskLevel.CRITICAL


def test_risk_score_bounds_and_effects():
    """Risk score integrates pressure, queue hazard, post-event surge, and weather."""
    # Baseline calm condition
    score_calm = calculate_risk_score(
        crowd_pressure=0.1,
        queue=50,
        stop_capacity=1500,
        minutes_since_event_end=-120,
        rain_probability=0.0
    )
    assert 0 <= score_calm <= 30

    # Active post-event discharge surge (m = 15 min) increases risk
    score_surge = calculate_risk_score(
        crowd_pressure=0.85,
        queue=1200,
        stop_capacity=1500,
        minutes_since_event_end=15,
        rain_probability=80.0
    )
    assert score_surge >= 70
    assert score_surge <= 100


def test_network_risk_calculation():
    """Network risk combines worst-case stop crisis with average and identifies high-risk stops."""
    stop_scores = {
        "stop_A": 85,  # CRITICAL
        "stop_B": 65,  # HIGH
        "stop_C": 25,  # LOW
    }
    net_score, net_level, high_risk_stops = calculate_network_risk(stop_scores)

    assert 0 <= net_score <= 100
    assert net_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert "stop_A" in high_risk_stops
    assert "stop_B" in high_risk_stops
    assert "stop_C" not in high_risk_stops


def test_network_risk_empty():
    """Empty stops gracefully return zero LOW risk."""
    score, level, high_stops = calculate_network_risk({})
    assert score == 0
    assert level == RiskLevel.LOW
    assert high_stops == []
