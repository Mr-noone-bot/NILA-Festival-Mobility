"""
Tests for NILA Stop Crowd Distribution Module (backend/prediction/distribution.py)
Owned by: Gugaan
"""

import pytest
from backend.prediction.models import Stop
from backend.prediction.distribution import compute_stop_weights, distribute_crowd_to_stops


def test_distribution_multiple_stops_with_weights():
    """Stops with explicit weights are normalized properly."""
    stops = [
        Stop(id="s1", name="Stop 1", capacity=1000, weight=0.50),
        Stop(id="s2", name="Stop 2", capacity=1000, weight=0.30),
        Stop(id="s3", name="Stop 3", capacity=1000, weight=0.20),
    ]
    weights = compute_stop_weights(stops)
    assert pytest.approx(sum(weights.values()), 1e-6) == 1.0
    assert weights["s1"] == 0.50
    assert weights["s2"] == 0.30
    assert weights["s3"] == 0.20

    total_crowd = 10000
    distributed = distribute_crowd_to_stops(total_crowd, stops)
    assert sum(distributed.values()) == total_crowd
    assert distributed["s1"] == 5000
    assert distributed["s2"] == 3000
    assert distributed["s3"] == 2000


def test_distribution_single_stop():
    """Single stop receives 100% of the crowd."""
    stops = [Stop(id="single", name="Only Stop", capacity=2000)]
    weights = compute_stop_weights(stops)
    assert weights["single"] == 1.0

    distributed = distribute_crowd_to_stops(8500, stops)
    assert distributed["single"] == 8500


def test_distribution_missing_weights_fallback_to_capacity():
    """When weights are None, distribution falls back to relative stop capacities."""
    stops = [
        Stop(id="sA", name="Small Stop", capacity=1000, weight=None),
        Stop(id="sB", name="Large Stop", capacity=3000, weight=None),
    ]
    weights = compute_stop_weights(stops)
    assert pytest.approx(weights["sA"], 1e-4) == 0.25
    assert pytest.approx(weights["sB"], 1e-4) == 0.75

    distributed = distribute_crowd_to_stops(12000, stops)
    assert distributed["sA"] == 3000
    assert distributed["sB"] == 9000
    assert sum(distributed.values()) == 12000


def test_distribution_sum_equals_total_crowd_with_odd_numbers():
    """Rounding reconciliation guarantees exact total conservation."""
    stops = [
        Stop(id="s1", name="Stop 1", capacity=1000, weight=0.333),
        Stop(id="s2", name="Stop 2", capacity=1000, weight=0.333),
        Stop(id="s3", name="Stop 3", capacity=1000, weight=0.334),
    ]
    odd_total = 10001
    distributed = distribute_crowd_to_stops(odd_total, stops)
    assert sum(distributed.values()) == odd_total
    assert all(count >= 0 for count in distributed.values())


def test_distribution_zero_or_negative_crowd():
    """Zero or negative total crowd produces zero for all stops."""
    stops = [Stop(id="s1", name="Stop 1", capacity=1000), Stop(id="s2", name="Stop 2", capacity=1000)]
    dist_zero = distribute_crowd_to_stops(0, stops)
    assert dist_zero == {"s1": 0, "s2": 0}

    dist_neg = distribute_crowd_to_stops(-500, stops)
    assert dist_neg == {"s1": 0, "s2": 0}


def test_distribution_deterministic_repeated_calls():
    """Repeated calls with identical inputs yield identical outputs."""
    stops = [
        Stop(id="s1", name="Stop 1", capacity=1200, weight=0.6),
        Stop(id="s2", name="Stop 2", capacity=800, weight=0.4),
    ]
    total = 7432
    run1 = distribute_crowd_to_stops(total, stops)
    run2 = distribute_crowd_to_stops(total, stops)
    assert run1 == run2
