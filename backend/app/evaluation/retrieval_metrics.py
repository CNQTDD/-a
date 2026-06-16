from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence


def recall_at_k(
    relevant: Sequence[str],
    retrieved: Sequence[str],
    *,
    k: int,
) -> float:
    if not relevant:
        return 0.0
    top_k = set(retrieved[:k])
    return len(set(relevant) & top_k) / len(set(relevant))


def top_k_hit_rate(
    queries: Iterable[Mapping[str, Sequence[str]]],
    *,
    k: int,
) -> float:
    queries = list(queries)
    if not queries:
        return 0.0

    hits = 0
    for query in queries:
      relevant = set(query.get("relevant", []))
      retrieved = list(query.get("retrieved", []))[:k]
      if relevant.intersection(retrieved):
          hits += 1
    return hits / len(queries)


def citation_completeness(required_evidence_ids: Sequence[str], cited_evidence_ids: Sequence[str]) -> float:
    if not required_evidence_ids:
        return 1.0
    required = set(required_evidence_ids)
    cited = set(cited_evidence_ids)
    return len(required & cited) / len(required)
