from __future__ import annotations

from statistics import mean


def adoption_rate(actions: list[str]) -> float:
    if not actions:
        return 0.0
    accepted = sum(1 for action in actions if action in {"accept", "edited"})
    return accepted / len(actions)


def average_handling_time(durations_seconds: list[float]) -> float:
    if not durations_seconds:
        return 0.0
    return float(mean(durations_seconds))
