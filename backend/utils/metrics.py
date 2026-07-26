"""Metrics collector.

In-memory request metrics for monitoring and diagnostics.
Exposes a snapshot via the /metrics endpoint.
"""

import time
from collections import defaultdict
from threading import Lock


class MetricsCollector:
    """Thread-safe in-memory metrics collector."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._start_time: float = time.time()
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._total_latency: float = 0.0
        self._requests_by_path: dict[str, int] = defaultdict(int)
        self._requests_by_status: dict[int, int] = defaultdict(int)

    def record_request(self, path: str, status_code: int, latency: float) -> None:
        with self._lock:
            self._total_requests += 1
            self._total_latency += latency
            self._requests_by_path[path] += 1
            self._requests_by_status[status_code] += 1
            if status_code >= 500:
                self._total_errors += 1

    def snapshot(self) -> dict:
        with self._lock:
            avg_latency = (
                (self._total_latency / self._total_requests)
                if self._total_requests > 0
                else 0.0
            )
            return {
                "uptime_seconds": int(time.time() - self._start_time),
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "avg_latency_seconds": round(avg_latency, 4),
                "requests_by_path": dict(self._requests_by_path),
                "requests_by_status": {
                    str(k): v for k, v in sorted(self._requests_by_status.items())
                },
            }


metrics_collector = MetricsCollector()
