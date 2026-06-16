from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FakeMilvusCollection:
    # 用一个内存字典模拟 Milvus 集合，方便验证 upsert 和过滤逻辑。
    records: dict[str, dict] = field(default_factory=dict)
    initialized: bool = False

    def ensure_initialized(self) -> None:
        self.initialized = True

    def upsert(self, record: dict) -> None:
        self.records[record["evidence_id"]] = record


def build_store(collection: FakeMilvusCollection):
    from app.retrieval.milvus_store import MilvusStore

    return MilvusStore(collection=collection)


def _record(
    *,
    evidence_id: str,
    source_id: str,
    score: float,
    source_version: str = "2026-06-demo",
    business_type: str = "billing",
    effective_at: datetime | None = None,
    expired_at: datetime | None = None,
):
    return {
        "evidence_id": evidence_id,
        "chunk_id": f"chunk-{evidence_id}",
        "source_id": source_id,
        "source_type": "business_rule",
        "business_type": business_type,
        "region": "云南",
        "product": "4G套餐",
        "source_version": source_version,
        "status": "active",
        "source_at": datetime(2026, 1, 1),
        "effective_at": effective_at,
        "expired_at": expired_at,
        "article_number": "1",
        "content_snapshot": f"内容 {source_id}",
        "vector": [score, score / 10],
    }


def test_store_initializes_collection() -> None:
    collection = FakeMilvusCollection()
    store = build_store(collection)

    store.ensure_collection()

    assert collection.initialized is True


def test_upsert_is_idempotent() -> None:
    collection = FakeMilvusCollection()
    store = build_store(collection)

    store.upsert([_record(evidence_id="e-1", source_id="rule-1", score=0.1)])
    store.upsert([_record(evidence_id="e-1", source_id="rule-1", score=0.9)])

    assert len(collection.records) == 1
    assert collection.records["e-1"]["vector"] == [0.9, 0.09]


def test_search_filters_and_orders_top_k() -> None:
    collection = FakeMilvusCollection()
    store = build_store(collection)
    store.upsert(
        [
            _record(
                evidence_id="e-1",
                source_id="rule-1",
                score=0.3,
                source_version="2026-05-demo",
            ),
            _record(
                evidence_id="e-2",
                source_id="rule-2",
                score=0.9,
                source_version="2026-06-demo",
            ),
            _record(
                evidence_id="e-3",
                source_id="case-7",
                score=0.8,
                source_version="2026-06-demo",
                effective_at=datetime(2026, 1, 1),
                expired_at=datetime(2026, 12, 31),
            ),
            _record(
                evidence_id="e-4",
                source_id="expired",
                score=1.0,
                source_version="2026-06-demo",
                expired_at=datetime(2026, 1, 1),
            ),
        ]
    )

    results = store.search(
        vector=[0.1, 0.2],
        limit=5,
        filters={
            "source_version": "2026-06-demo",
            "business_type": "billing",
            "as_of": datetime(2026, 6, 15),
        },
    )

    assert [item.source_id for item in results] == ["rule-2", "case-7"]
