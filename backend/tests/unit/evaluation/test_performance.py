from __future__ import annotations

import pytest


def test_percentile_handles_sorted_latency_samples() -> None:
    from app.evaluation.performance import percentile

    assert percentile([10.0, 20.0, 30.0, 40.0], 0.95) == pytest.approx(40.0)


def test_percentile_rejects_empty_samples() -> None:
    from app.evaluation.performance import percentile

    with pytest.raises(ValueError):
        percentile([], 0.5)
