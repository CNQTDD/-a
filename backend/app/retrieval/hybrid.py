from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.contracts import RetrievalHit


@dataclass(frozen=True)
class RetrievalStrategy:
    mode: str
    keyword_weight: float
    semantic_weight: float


@dataclass(frozen=True)
class HybridRetrievalResult:
    hits: list[RetrievalHit]
    degraded_sources: list[str]
    retrieval_mode: str


def choose_strategy(query: str) -> RetrievalStrategy:
    keyword_signals = ("第", "条", "套餐", "规则", "退费", "账单", "扣费")
    semantic_signals = ("影响", "导致", "造成", "经济损失", "赔偿", "经营")

    keyword_score = sum(1 for signal in keyword_signals if signal in query)
    semantic_score = sum(1 for signal in semantic_signals if signal in query)

    if keyword_score >= 2 and semantic_score <= 1:
        return RetrievalStrategy(
            mode="hybrid-keyword-heavy",
            keyword_weight=0.7,
            semantic_weight=0.3,
        )
    if semantic_score >= 2 and len(query) >= 16:
        return RetrievalStrategy(
            mode="hybrid-semantic-heavy",
            keyword_weight=0.3,
            semantic_weight=0.7,
        )
    return RetrievalStrategy(
        mode="hybrid-balanced",
        keyword_weight=0.5,
        semantic_weight=0.5,
    )


class HybridRetriever:
    def __init__(self, *, elastic_store: object, milvus_store: object) -> None:
        self._elastic_store = elastic_store
        self._milvus_store = milvus_store

    def retrieve(
        self,
        *,
        query: str,
        embedding: list[float],
        limit: int,
        filters: dict[str, object] | None = None,
    ) -> HybridRetrievalResult:
        strategy = choose_strategy(query)
        degraded_sources: list[str] = []
        elastic_hits: list[RetrievalHit] = []
        milvus_hits: list[RetrievalHit] = []

        try:
            elastic_hits = self._elastic_store.search(
                query=query, limit=limit, filters=filters
            )
        except Exception:
            degraded_sources.append("elasticsearch")

        try:
            milvus_hits = self._milvus_store.search(
                vector=embedding, limit=limit, filters=filters
            )
        except Exception:
            degraded_sources.append("milvus")

        if elastic_hits and not milvus_hits:
            return HybridRetrievalResult(
                hits=elastic_hits[:limit],
                degraded_sources=degraded_sources,
                retrieval_mode="elasticsearch-only",
            )
        if milvus_hits and not elastic_hits:
            return HybridRetrievalResult(
                hits=milvus_hits[:limit],
                degraded_sources=degraded_sources,
                retrieval_mode="milvus-only",
            )

        merged = self._merge_hits(
            elastic_hits=elastic_hits,
            milvus_hits=milvus_hits,
            keyword_weight=strategy.keyword_weight,
            semantic_weight=strategy.semantic_weight,
        )
        return HybridRetrievalResult(
            hits=merged[:limit],
            degraded_sources=degraded_sources,
            retrieval_mode=strategy.mode,
        )

    def _merge_hits(
        self,
        *,
        elastic_hits: list[RetrievalHit],
        milvus_hits: list[RetrievalHit],
        keyword_weight: float,
        semantic_weight: float,
    ) -> list[RetrievalHit]:
        weighted: dict[str, tuple[RetrievalHit, float]] = {}

        for rank, hit in enumerate(elastic_hits, start=1):
            score = keyword_weight * (1.0 / rank)
            existing = weighted.get(hit.evidence_id)
            if existing is None or existing[1] < score:
                weighted[hit.evidence_id] = (hit, score)

        for rank, hit in enumerate(milvus_hits, start=1):
            score = semantic_weight * (1.0 / rank)
            existing = weighted.get(hit.evidence_id)
            if existing is None:
                weighted[hit.evidence_id] = (hit, score)
            else:
                weighted[hit.evidence_id] = (existing[0], existing[1] + score)

        ordered = sorted(
            weighted.values(),
            key=lambda item: (-item[1], item[0].source_id),
        )
        return [item[0] for item in ordered]
