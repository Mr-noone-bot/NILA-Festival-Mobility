"""
Tests for NILA Prediction Engine (backend/prediction/engine.py)
Owned by: Gugaan
"""

import pytest
from backend.prediction.models import (
    PredictionInput,
    PredictionResult,
    Festival,
    Stop,
    FestivalEvent,
)
from backend.prediction.engine import PredictionEngine
from backend.prediction.data_loader import FestivalNotFoundError


@pytest.fixture
def test_festival():
    """Provides a realistic test festival configuration."""
    return Festival(
        id="test-madurai-fest",
        name="Chithirai Test Festival",
        city="Madurai",
        base_attendance=100000,
        intensity=1.2,
        peak_events=[
            FestivalEvent(
                name="Chariot Climax",
                start_time="2026-04-28T08:00:00+05:30",
                end_time="2026-04-28T10:00:00+05:30",
                estimated_turnout=120000,
            )
        ],
        stops=[
            Stop(id="stop_main", name="Main Terminus", capacity=2000, weight=0.60, current_buses=10),
            Stop(id="stop_north", name="North Gate Stand", capacity=1200, weight=0.40, current_buses=6),
        ],
        default_fleet_size=20,
    )


def test_prediction_engine_valid_run(test_festival):
    """Executes prediction and validates the full output contract structure."""
    engine = PredictionEngine()
    config = PredictionInput(
        festival_id=test_festival.id,
        time_window_start="2026-04-28T07:00:00+05:30",
        time_window_end="2026-04-28T13:00:00+05:30",
        attendance_multiplier=1.0,
        rain_probability=0.0,
        event_end_time="2026-04-28T10:00:00+05:30",
    )

    result = engine.predict(config, festival_override=test_festival)

    assert isinstance(result, PredictionResult)
    assert result.festival_id == test_festival.id
    assert result.timezone == "Asia/Kolkata"
    assert result.interval_minutes == 15
    assert result.peak_crowd > 0
    assert result.peak_time is not None

    # Timeline assertions
    assert len(result.timeline) > 0
    for point in result.timeline:
        assert point.total_crowd >= 0
        assert point.event_status in ("pre_event", "event_active", "post_event")
        assert "+05:30" in point.timestamp

    # Stop forecast assertions
    assert len(result.stop_forecast) > 0
    for sf in result.stop_forecast:
        assert sf.stop_id in ("stop_main", "stop_north")
        assert sf.predicted_crowd >= 0
        assert sf.arrivals >= 0
        assert sf.departures >= 0
        assert sf.queue >= 0  # Queue never negative
        assert sf.required_buses >= 0
        assert 0.0 <= sf.crowd_pressure <= 1.0
        assert 0 <= sf.risk_score <= 100
        assert sf.risk_level in ("LOW", "MODERATE", "HIGH", "CRITICAL")

    # Risk summary assertions
    assert 0 <= result.risk_summary.overall_risk_score <= 100
    assert result.risk_summary.overall_risk_level in ("LOW", "MODERATE", "HIGH", "CRITICAL")


def test_prediction_determinism(test_festival):
    """Two identical prediction runs produce 100% bit-for-bit identical results."""
    engine = PredictionEngine()
    config = PredictionInput(
        festival_id=test_festival.id,
        time_window_start="2026-04-28T08:00:00+05:30",
        time_window_end="2026-04-28T12:00:00+05:30",
        attendance_multiplier=1.15,
        rain_probability=35.0,
        event_end_time="2026-04-28T10:00:00+05:30",
    )

    run_1 = engine.predict(config, festival_override=test_festival).model_dump()
    run_2 = engine.predict(config, festival_override=test_festival).model_dump()

    assert run_1 == run_2


def test_event_end_effect_surge(test_festival):
    """Post-event discharge produces significantly higher passenger arrivals than pre-event intervals."""
    engine = PredictionEngine()
    config = PredictionInput(
        festival_id=test_festival.id,
        time_window_start="2026-04-28T08:30:00+05:30",
        time_window_end="2026-04-28T11:30:00+05:30",
        event_end_time="2026-04-28T10:00:00+05:30",
    )

    result = engine.predict(config, festival_override=test_festival)

    # Locate arrivals right before event end vs arrivals at 10:00 and 10:15
    pre_event_arrivals = [
        sf.arrivals for sf in result.stop_forecast
        if sf.timestamp == "2026-04-28T09:00:00+05:30"
    ]
    post_event_arrivals = [
        sf.arrivals for sf in result.stop_forecast
        if sf.timestamp == "2026-04-28T10:15:00+05:30"
    ]

    # Post-event mass discharge must exceed active sitting pre-event arrivals
    assert sum(post_event_arrivals) > sum(pre_event_arrivals)


def test_weather_effect_rain_surge(test_festival):
    """Rain probability dampens outdoor attendance and elevates transit rush multiplier."""
    engine = PredictionEngine()
    config_clear = PredictionInput(
        festival_id=test_festival.id,
        rain_probability=0.0,
        event_end_time="2026-04-28T10:00:00+05:30",
    )
    config_rain = PredictionInput(
        festival_id=test_festival.id,
        rain_probability=80.0,
        event_end_time="2026-04-28T10:00:00+05:30",
    )

    res_clear = engine.predict(config_clear, festival_override=test_festival)
    res_rain = engine.predict(config_rain, festival_override=test_festival)

    # Rain dampens overall peak attendance
    assert res_rain.peak_crowd < res_clear.peak_crowd
    # Weather increases risk score
    assert res_rain.risk_summary.overall_risk_score >= res_clear.risk_summary.overall_risk_score


def test_attendance_multipliers(test_festival):
    """Attendance multipliers (+20%, +50%) scale crowd and bus demand proportionately."""
    engine = PredictionEngine()
    config_base = PredictionInput(festival_id=test_festival.id, attendance_multiplier=1.0)
    config_plus20 = PredictionInput(festival_id=test_festival.id, attendance_multiplier=1.2)
    config_plus50 = PredictionInput(festival_id=test_festival.id, attendance_multiplier=1.5)

    res_base = engine.predict(config_base, festival_override=test_festival)
    res_20 = engine.predict(config_plus20, festival_override=test_festival)
    res_50 = engine.predict(config_plus50, festival_override=test_festival)

    assert res_20.peak_crowd > res_base.peak_crowd
    assert res_50.peak_crowd > res_20.peak_crowd


def test_delayed_event_timeline(test_festival):
    """Changing event end time properly shifts peak surge timing."""
    engine = PredictionEngine()
    config_early = PredictionInput(
        festival_id=test_festival.id,
        event_end_time="2026-04-28T09:00:00+05:30",
    )
    config_late = PredictionInput(
        festival_id=test_festival.id,
        event_end_time="2026-04-28T12:00:00+05:30",
    )

    res_early = engine.predict(config_early, festival_override=test_festival)
    res_late = engine.predict(config_late, festival_override=test_festival)

    assert res_early.peak_time != res_late.peak_time


def test_edge_case_single_stop():
    """Prediction executes successfully with a single stop."""
    engine = PredictionEngine()
    single_stop_fest = Festival(
        id="single-stop-fest",
        name="Single Stop Fest",
        base_attendance=25000,
        stops=[Stop(id="solo_stop", name="Only Stand", capacity=1500, current_buses=5)],
    )
    config = PredictionInput(festival_id="single-stop-fest")
    res = engine.predict(config, festival_override=single_stop_fest)
    assert len(res.stop_forecast) > 0
    assert all(sf.stop_id == "solo_stop" for sf in res.stop_forecast)


def test_input_validation_errors():
    """Invalid input values are rejected with clear ValidationError."""
    with pytest.raises(ValueError):
        PredictionInput(festival_id="fest1", attendance_multiplier=-0.5)

    with pytest.raises(ValueError):
        PredictionInput(festival_id="fest1", rain_probability=150.0)


def test_festival_not_found_error():
    """Querying an unknown festival raises FestivalNotFoundError."""
    engine = PredictionEngine()
    config = PredictionInput(festival_id="non-existent-festival-xyz")
    with pytest.raises(FestivalNotFoundError):
        engine.predict(config)
