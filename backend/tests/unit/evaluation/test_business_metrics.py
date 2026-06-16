from __future__ import annotations

import pytest


def test_adoption_rate_counts_accepted_workflows() -> None:
    from app.evaluation.business_metrics import adoption_rate

    assert adoption_rate(["accept", "edited", "rejected"]) == pytest.approx(2 / 3)


def test_average_handling_time_returns_mean_seconds() -> None:
    from app.evaluation.business_metrics import average_handling_time

    assert average_handling_time([30, 60, 90]) == pytest.approx(60.0)
