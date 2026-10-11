"""
NILA Stop Crowd Distribution Module
Distributes total network crowd across transport stops deterministically.
Owned by: Gugaan
"""

from typing import List, Dict
from backend.prediction.models import Stop


def compute_stop_weights(stops: List[Stop]) -> Dict[str, float]:
    """
    Computes normalized spatial catchment distribution weights for a list of stops.
    
    Rules:
    - If explicit positive weights are configured, normalize by sum(weights).
    - If weights are missing/zero, use stop holding capacities as a proxy.
    - If capacities are also missing or non-positive, distribute uniformly.
    - Resulting weights strictly sum to 1.0 (within float precision).
    """
    if not stops:
        raise ValueError("Cannot compute weights for an empty stop list.")

    if len(stops) == 1:
        return {stops[0].id: 1.0}

    # Check for explicit weights
    has_explicit_weights = all(s.weight is not None and s.weight > 0 for s in stops)
    if has_explicit_weights:
        raw_weights = {s.id: float(s.weight) for s in stops}
    else:
        # Fallback to capacity-weighted distribution
        capacities = [max(1, s.capacity) for s in stops]
        raw_weights = {s.id: float(cap) for s, cap in zip(stops, capacities)}

    total_weight = sum(raw_weights.values())
    if total_weight <= 0:
        uniform_val = 1.0 / len(stops)
        return {s.id: uniform_val for s in stops}

    normalized = {s_id: w / total_weight for s_id, w in raw_weights.items()}
    return normalized


def distribute_crowd_to_stops(total_crowd: int, stops: List[Stop]) -> Dict[str, int]:
    """
    Distributes an integer total crowd across stops.
    
    Guarantees:
    - Deterministic output.
    - No negative crowd values.
    - Sum of distributed stop crowds exactly equals total_crowd (reconciling integer rounding).
    """
    if not stops:
        raise ValueError("At least one stop is required for crowd distribution.")

    if total_crowd <= 0:
        return {s.id: 0 for s in stops}

    if len(stops) == 1:
        return {stops[0].id: total_crowd}

    weights = compute_stop_weights(stops)
    
    distributed: Dict[str, int] = {}
    total_assigned = 0

    # Sort stops deterministically by ID to ensure absolute reproducibility
    sorted_stops = sorted(stops, key=lambda s: s.id)

    for s in sorted_stops:
        assigned = int(round(total_crowd * weights[s.id]))
        distributed[s.id] = max(0, assigned)
        total_assigned += distributed[s.id]

    # Reconcile any rounding discrepancy against the highest-weighted stop
    discrepancy = total_crowd - total_assigned
    if discrepancy != 0:
        top_stop = max(sorted_stops, key=lambda s: weights[s.id])
        distributed[top_stop.id] = max(0, distributed[top_stop.id] + discrepancy)

    return distributed
