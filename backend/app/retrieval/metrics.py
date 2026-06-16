from __future__ import annotations

from collections import Counter

_DEGRADATION_COUNTS: Counter[str] = Counter()


def record_degradation(source: str) -> None:
    """Record one degraded retrieval source."""
    _DEGRADATION_COUNTS[source] += 1
    from app.observability.metrics import record_degradation as record_prometheus_degradation

    record_prometheus_degradation(source)


def get_degradation_counts() -> dict[str, int]:
    """Return the current degradation counters."""
    return dict(_DEGRADATION_COUNTS)
