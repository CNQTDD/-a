from __future__ import annotations

import pytest


def test_recall_at_k_counts_any_relevant_item_in_top_k() -> None:
    from app.evaluation.retrieval_metrics import recall_at_k

    assert recall_at_k(["a", "b"], ["x", "b", "y"], k=2) == pytest.approx(0.5)


def test_top_k_hit_rate_requires_a_relevant_item_per_query() -> None:
    from app.evaluation.retrieval_metrics import top_k_hit_rate

    assert top_k_hit_rate(
        [
            {"relevant": ["a"], "retrieved": ["a", "x"]},
            {"relevant": ["b"], "retrieved": ["x", "y"]},
        ],
        k=1,
    ) == pytest.approx(0.5)


def test_citation_completeness_uses_all_required_evidence_ids() -> None:
    from app.evaluation.retrieval_metrics import citation_completeness

    assert citation_completeness(["e1", "e2"], ["e1"]) == pytest.approx(0.5)
