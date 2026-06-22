from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.retrieval.contracts import RetrievalHit
from app.retrieval.hybrid import HybridRetriever


@dataclass
class FakeElasticStore:
    hits: list[RetrievalHit]
    calls: list[tuple[str, int, dict[str, object] | None]]

    def search(
        self, *, query: str, limit: int, filters: dict[str, object] | None = None
    ) -> list[RetrievalHit]:
        self.calls.append((query, limit, filters))
        return self.hits


@dataclass
class FakeMilvusStore:
    hits: list[RetrievalHit]
    calls: list[tuple[list[float], int, dict[str, object] | None]]

    def search(
        self, *, vector: list[float], limit: int, filters: dict[str, object] | None = None
    ) -> list[RetrievalHit]:
        self.calls.append((vector, limit, filters))
        return self.hits


class BrokenElasticStore:
    def search(self, *, query: str, limit: int, filters: dict[str, object] | None = None):
        del query, limit, filters
        raise RuntimeError("elasticsearch unavailable")


def _hit(
    evidence_id: str,
    source_id: str,
    score: float,
    *,
    business_type: str = "billing",
    content: str = "rule content",
) -> RetrievalHit:
    return RetrievalHit(
        evidence_id=evidence_id,
        chunk_id=f"{evidence_id}-chunk",
        source_id=source_id,
        source_type="business_rule",
        business_type=business_type,
        region="yunnan",
        product="generic",
        source_version="sample-1",
        status="active",
        source_at=datetime(2026, 1, 1),
        effective_at=datetime(2026, 1, 1),
        expired_at=None,
        article_number="1",
        content_snapshot=content,
        score=score,
        metadata={"title": source_id},
    )


def test_keyword_heavy_queries_favor_elasticsearch_results() -> None:
    retriever = HybridRetriever(
        elastic_store=FakeElasticStore(
            hits=[
                _hit("e-1", "rule-article", 10.0, content="第101条 5G套餐退费规则"),
                _hit("e-2", "rule-billing", 7.0, content="套餐扣费核查"),
            ],
            calls=[],
        ),
        milvus_store=FakeMilvusStore(
            hits=[_hit("e-3", "semantic-related", 0.8, content="相似语义规则")],
            calls=[],
        ),
    )

    result = retriever.retrieve(
        query="第101条 5G套餐 退费规则",
        embedding=[0.1, 0.2, 0.3, 0.4],
        limit=5,
        filters={"source_version": "sample-1", "business_type": "billing"},
    )

    assert result.retrieval_mode == "hybrid-keyword-heavy"
    assert result.degraded_sources == []
    assert [item.source_id for item in result.hits][:2] == ["rule-article", "rule-billing"]


def test_semantic_heavy_queries_favor_milvus_results() -> None:
    retriever = HybridRetriever(
        elastic_store=FakeElasticStore(
            hits=[_hit("e-1", "literal-match", 5.0, business_type="service")],
            calls=[],
        ),
        milvus_store=FakeMilvusStore(
            hits=[
                _hit(
                    "e-2",
                    "economic-loss-rule",
                    0.95,
                    business_type="service",
                    content="服务影响生产经营并引发经济损失",
                )
            ],
            calls=[],
        ),
    )

    result = retriever.retrieve(
        query="网络异常影响用户经营并造成经济损失要求赔偿",
        embedding=[0.4, 0.3, 0.2, 0.1],
        limit=5,
        filters={"source_version": "sample-1", "business_type": "service"},
    )

    assert result.retrieval_mode == "hybrid-semantic-heavy"
    assert result.degraded_sources == []
    assert result.hits[0].source_id == "economic-loss-rule"


def test_retriever_falls_back_to_milvus_when_elasticsearch_is_unavailable() -> None:
    retriever = HybridRetriever(
        elastic_store=BrokenElasticStore(),
        milvus_store=FakeMilvusStore(
            hits=[_hit("e-2", "economic-loss-rule", 0.95, business_type="service")],
            calls=[],
        ),
    )

    result = retriever.retrieve(
        query="网络异常影响用户经营并造成经济损失要求赔偿",
        embedding=[0.4, 0.3, 0.2, 0.1],
        limit=5,
        filters={"source_version": "sample-1", "business_type": "service"},
    )

    assert result.retrieval_mode == "milvus-only"
    assert result.degraded_sources == ["elasticsearch"]
    assert [item.source_id for item in result.hits] == ["economic-loss-rule"]
