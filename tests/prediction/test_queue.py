"""
Tests for NILA Queue Module (backend/prediction/queue.py)
Owned by: Gugaan
"""

import pytest
from backend.prediction.queue import calculate_next_queue, StopQueueTracker


def test_queue_arrivals_greater_than_departures():
    """When arrivals exceed departures, queue grows by difference."""
    # initial queue = 50, arrivals = 100, departures = 60 -> next = 50 + 100 - 60 = 90
    next_q = calculate_next_queue(previous_queue=50, arrivals=100, departures=60)
    assert next_q == 90


def test_queue_arrivals_less_than_departures():
    """When departures exceed arrivals, existing queue decreases."""
    # initial queue = 80, arrivals = 20, departures = 50 -> next = 80 + 20 - 50 = 50
    next_q = calculate_next_queue(previous_queue=80, arrivals=20, departures=50)
    assert next_q == 50


def test_queue_arrivals_equal_departures():
    """When arrivals equal departures, queue remains stable."""
    # initial queue = 40, arrivals = 30, departures = 30 -> next = 40
    next_q = calculate_next_queue(previous_queue=40, arrivals=30, departures=30)
    assert next_q == 40


def test_queue_complete_clearing():
    """When departures exceed queue + arrivals, queue clears to exactly 0."""
    # initial queue = 30, arrivals = 10, departures = 100 -> next = max(0, 40 - 100) = 0
    next_q = calculate_next_queue(previous_queue=30, arrivals=10, departures=100)
    assert next_q == 0


def test_queue_never_negative():
    """Queue must never become negative under any conditions."""
    assert calculate_next_queue(previous_queue=0, arrivals=0, departures=50) == 0
    assert calculate_next_queue(previous_queue=10, arrivals=5, departures=999) == 0
    assert calculate_next_queue(previous_queue=-10, arrivals=-5, departures=10) == 0


def test_stop_queue_tracker_multistep():
    """StopQueueTracker maintains state across multiple intervals independently."""
    tracker = StopQueueTracker({"stop_A": 100, "stop_B": 0})

    # Step 1: stop_A arrivals=50, departures=80 -> 100 + 50 - 80 = 70
    q_a1 = tracker.step("stop_A", arrivals=50, departures=80)
    assert q_a1 == 70
    assert tracker.get_queue("stop_A") == 70

    # Step 2: stop_A arrivals=10, departures=100 -> 70 + 10 - 100 = 0
    q_a2 = tracker.step("stop_A", arrivals=10, departures=100)
    assert q_a2 == 0

    # stop_B remains 0 until stepped
    assert tracker.get_queue("stop_B") == 0
    q_b1 = tracker.step("stop_B", arrivals=40, departures=10)
    assert q_b1 == 30
    assert tracker.get_queue("stop_B") == 30
