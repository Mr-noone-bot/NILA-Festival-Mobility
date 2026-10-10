"""
NILA Core Constants
Domain enums and operational invariants for festival mobility.
"""

from enum import Enum


class BusStatus(str, Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RouteProvenance(str, Enum):
    LIVE_OSRM = "LIVE_OSRM"
    CACHED_OSRM = "CACHED_OSRM"
    FALLBACK_ESTIMATE = "FALLBACK_ESTIMATE"


# Time & Regional Constants
TAMIL_NADU_TIMEZONE = "Asia/Kolkata"
DEFAULT_INTERVAL_MINUTES = 15
DEFAULT_BUS_CAPACITY = 50
