"""
NILA Risk Evaluation Module
Deterministic scoring for stop-level crowd pressure and network-wide risk.
Owned by: Gugaan
"""

from typing import List, Dict, Tuple
from backend.prediction.models import RiskLevel


def calculate_crowd_pressure(
    queue: int,
    stop_capacity: int,
    arrivals: int,
    service_capacity: int
) -> float:
    """
    Computes normalized crowd pressure at a transport stop: [0.0, 1.0].
    
    Formula components:
    1. Queue ratio: queue / safe_holding_capacity
    2. Capacity stress: pending_demand / service_throughput
    """
    safe_cap = max(1, int(stop_capacity))
    serv_cap = max(1, int(service_capacity))
    
    # Queue saturation ratio
    queue_ratio = min(1.0, max(0.0, float(queue) / safe_cap))
    
    # Demand-to-service ratio
    total_pending = max(0, arrivals + queue)
    demand_ratio = min(1.0, max(0.0, float(total_pending) / (serv_cap * 2.0)))
    
    # Weighted composite pressure
    raw_pressure = (0.60 * queue_ratio) + (0.40 * demand_ratio)
    clamped = max(0.0, min(1.0, raw_pressure))
    return round(clamped, 2)


def risk_level_from_score(score: int) -> RiskLevel:
    """
    Maps 0-100 risk score to standardized RiskLevel:
    0–30:   LOW
    31–60:  MODERATE
    61–80:  HIGH
    81–100: CRITICAL
    """
    clamped_score = max(0, min(100, int(score)))
    if clamped_score <= 30:
        return RiskLevel.LOW
    elif clamped_score <= 60:
        return RiskLevel.MODERATE
    elif clamped_score <= 80:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def calculate_risk_score(
    crowd_pressure: float,
    queue: int,
    stop_capacity: int,
    minutes_since_event_end: int = -999,
    rain_probability: float = 0.0
) -> int:
    """
    Computes deterministic risk score between 0 and 100.
    
    Formula:
    - Crowd pressure weight: up to 55 points
    - Physical queue overflow weight: up to 25 points
    - Active post-event discharge surge: up to 12 points
    - Weather / rain disruption: up to 8 points
    """
    # 1. Base pressure contribution (0 to 55)
    pressure = max(0.0, min(1.0, float(crowd_pressure)))
    pressure_pts = pressure * 55.0

    # 2. Queue overflow contribution (0 to 25)
    safe_cap = max(1, int(stop_capacity))
    queue_ratio = min(1.0, max(0.0, float(queue) / safe_cap))
    queue_pts = queue_ratio * 25.0

    # 3. Post-event surge volatility (0 to 12)
    surge_pts = 0.0
    if 0 <= minutes_since_event_end <= 60:
        # Acute surge window immediately post-event
        fraction = 1.0 - (minutes_since_event_end / 60.0)
        surge_pts = 12.0 * fraction
    elif -30 <= minutes_since_event_end < 0:
        # Pre-event anticipation
        surge_pts = 5.0

    # 4. Weather disruption (0 to 8)
    rain = max(0.0, min(100.0, float(rain_probability)))
    weather_pts = (rain / 100.0) * 8.0

    total_score = int(round(pressure_pts + queue_pts + surge_pts + weather_pts))
    return max(0, min(100, total_score))


def calculate_network_risk(
    stop_risk_scores: Dict[str, int]
) -> Tuple[int, RiskLevel, List[str]]:
    """
    Derives overall network risk from all stop-level risk scores.
    
    Returns:
    - overall_risk_score (0-100)
    - overall_risk_level (RiskLevel)
    - high_risk_stops (list of stop_ids in HIGH or CRITICAL risk)
    """
    if not stop_risk_scores:
        return 0, RiskLevel.LOW, []

    scores = list(stop_risk_scores.values())
    max_score = max(scores)
    avg_score = sum(scores) / len(scores)

    # Network risk reflects both peak bottleneck crisis (65%) and network average (35%)
    network_score = int(round((0.65 * max_score) + (0.35 * avg_score)))
    network_score = max(0, min(100, network_score))
    
    network_level = risk_level_from_score(network_score)
    
    # High risk stops are those with score >= 61 (HIGH or CRITICAL)
    high_risk_stops = sorted(
        [s_id for s_id, score in stop_risk_scores.items() if score >= 61]
    )

    return network_score, network_level, high_risk_stops
