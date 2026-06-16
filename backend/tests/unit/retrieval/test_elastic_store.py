from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FakeElasticClient:
    # 这个假客户端只记录索引文档和最后一次查询体，便于单测断言。
    indexed_docs: list[dict] = field(default_factory=list)
    last_query: dict | None = None

    def ensure_index(self, index_name: str, mapping: dict) -> None:
        self.index_name = index_name
        self.mapping = mapping

    def index(self, index_name: str, document: dict) -> None:
        self.indexed_docs.append(document)

    def search(self, index_name: str, body: dict) -> dict:
        self.last_query = body
        query_text = body["query"]["bool"]["must"][0]["multi_match"]["query"]
        filters = body["query"]["bool"]["filter"]
        source_version = next(
            item["term"]["source_version"]
            for item in filters
            if "term" in item and "source_version" in item["term"]
        )
        business_type = next(
            item["term"]["business_type"]
            for item in filters
            if "term" in item and "business_type" in item["term"]
        )

        hits = []
        for doc in self.indexed_docs:
            if doc["source_version"] != source_version:
                continue
            if doc["business_type"] != business_type:
                continue
            if (
                doc["expired_at"] is not None
                and body["query"]["bool"]["filter"][-1]["range"]["expired_at"]["gt"]
                is not None
            ):
                pass
            score = _bm25_like_score(query_text, doc["full_text"])
            if score > 0:
                hits.append({"_source": doc, "_score": score})

        hits.sort(key=lambda item: (-item["_score"], item["_source"]["source_id"]))
        return {"hits": {"hits": hits[: body["size"]]}}


def _bm25_like_score(query: str, document: str) -> float:
    # 这里用简化的词项命中计分来模拟 BM25 的词面偏好，足以验证排序方向。
    score = 0.0
    for term in query.split():
        if term and term in document:
            score += 1.0
    # 再补一点中文关键词重合分，避免“套餐”这种短词被切分后完全丢分。
    for keyword in ("套餐", "退费", "规则", "费用", "故障"):
        if keyword in query and keyword in document:
            score += 0.5
    return score


def build_store(client: FakeElasticClient):
    from app.retrieval.elastic_store import ElasticStore

    return ElasticStore(index_name="complaint_rules", client=client)


def _document(
    *,
    chunk_id: str,
    source_id: str,
    full_text: str,
    evidence_id: str | None = None,
    source_version: str = "2026-06-demo",
    business_type: str = "billing",
    article_number: str = "1",
    effective_at: datetime | None = None,
    expired_at: datetime | None = None,
):
    return {
        "evidence_id": evidence_id or f"evidence-{chunk_id}",
        "chunk_id": chunk_id,
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
        "article_number": article_number,
        "full_text": full_text,
    }


def test_store_builds_index_and_saves_documents() -> None:
    client = FakeElasticClient()
    store = build_store(client)

    store.ensure_index()
    store.upsert(
        [
            _document(
                chunk_id="chunk-1",
                source_id="rule-1",
                full_text="第1条 用户可退费",
            )
        ]
    )

    assert client.index_name == "complaint_rules"
    assert len(client.indexed_docs) == 1
    assert client.indexed_docs[0]["chunk_id"] == "chunk-1"


def test_bm25_prefers_exact_rule_terms() -> None:
    client = FakeElasticClient()
    store = build_store(client)
    store.upsert(
        [
            _document(
                chunk_id="chunk-1",
                source_id="rule-101",
                full_text="第101条 5G套餐退费按照合同约定处理",
            ),
            _document(
                chunk_id="chunk-2",
                source_id="rule-102",
                full_text="套餐优惠活动会在系统中自动显示",
            ),
            _document(
                chunk_id="chunk-3",
                source_id="rule-103",
                full_text="宽带故障由维护人员处理",
                source_version="2026-05-demo",
            ),
        ]
    )

    results = store.search(
        query="第101条 5G套餐 退费",
        limit=5,
        filters={
            "source_version": "2026-06-demo",
            "business_type": "billing",
            "as_of": datetime(2026, 6, 15),
        },
    )

    assert [item.source_id for item in results] == ["rule-101", "rule-102"]


def test_search_builds_bool_query_with_registry_filters() -> None:
    client = FakeElasticClient()
    store = build_store(client)
    store.upsert(
        [
            _document(
                chunk_id="chunk-1",
                source_id="rule-1",
                full_text="第1条 退费标准",
                effective_at=datetime(2026, 1, 1),
                expired_at=datetime(2026, 12, 31),
            )
        ]
    )

    store.search(
        query="退费标准",
        limit=3,
        filters={
            "source_version": "2026-06-demo",
            "business_type": "billing",
            "effective_at": datetime(2026, 1, 1),
            "as_of": datetime(2026, 6, 15),
        },
    )

    assert client.last_query is not None
    bool_query = client.last_query["query"]["bool"]
    assert bool_query["must"][0]["multi_match"]["query"] == "退费标准"
    assert any(
        item.get("term", {}).get("source_version") == "2026-06-demo"
        for item in bool_query["filter"]
    )
    assert any(
        item.get("term", {}).get("business_type") == "billing"
        for item in bool_query["filter"]
    )
    assert any("range" in item for item in bool_query["filter"])
