"""
NILA Queue Module
Models discrete passenger queue evolution at transport stops.
Owned by: Gugaan
"""

from typing import Dict


def calculate_next_queue(previous_queue: int, arrivals: int, departures: int) -> int:
    """
    Computes passenger queue accumulation for the next time interval:
    queue(t+1) = max(0, queue(t) + arrivals(t) - departures(t))
    
    Guarantees:
    - Queue is never negative.
    - Non-negative input clamping.
    """
    prev = max(0, int(previous_queue))
    arr = max(0, int(arrivals))
    dep = max(0, int(departures))
    
    return max(0, prev + arr - dep)


class StopQueueTracker:
    """
    Maintains independent queue state across multiple transport stops
    as intervals progress.
    """
    def __init__(self, initial_queues: Dict[str, int] = None):
        self._queues: Dict[str, int] = {}
        if initial_queues:
            for s_id, q in initial_queues.items():
                self._queues[s_id] = max(0, int(q))

    def get_queue(self, stop_id: str) -> int:
        """Returns current waiting queue for a stop."""
        return self._queues.get(stop_id, 0)

    def step(self, stop_id: str, arrivals: int, departures: int) -> int:
        """
        Advances queue state for a stop by one interval and returns new queue length.
        """
        current_q = self.get_queue(stop_id)
        next_q = calculate_next_queue(current_q, arrivals, departures)
        self._queues[stop_id] = next_q
        return next_q

    def reset(self):
        """Resets all tracked queues to zero."""
        self._queues.clear()
