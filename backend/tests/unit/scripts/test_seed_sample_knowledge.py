from __future__ import annotations

from datetime import datetime

from scripts.seed_sample_knowledge import _build_documents, _seed_elasticsearch


class FakeIndices:
    def __init__(self) -> None:
        self.created_mapping: dict | None = None

    def exists(self, *, index: str) -> bool:
        del index
        return False

    def create(self, *, index: str, mappings: dict) -> None:
        del index
        self.created_mapping = mappings


class FakeElasticsearch:
    def __init__(self) -> None:
        self.indices = FakeIndices()
        self.indexed_documents: list[dict] = []

    def index(self, *, index: str, id: str, document: dict) -> None:
        del index, id
        self.indexed_documents.append(document)


def test_seed_elasticsearch_preserves_runtime_search_fields() -> None:
    client = FakeElasticsearch()
    documents = [
        {
            "source_id": "rule-001",
            "source_type": "business_rule",
            "source_version": "sample-1",
            "business_type": "billing",
            "status": "active",
            "import_batch_id": "sample-batch",
            "effective_at": datetime(2026, 6, 17, 12, 0, 0),
            "expired_at": None,
            "full_text": "套餐费用核查规则",
            "metadata": {"title": "套餐变更规则"},
        }
    ]

    _seed_elasticsearch.__globals__["Elasticsearch"] = lambda _url: client
    _seed_elasticsearch("http://example.invalid:9200", documents)

    assert client.indices.created_mapping is not None
    properties = client.indices.created_mapping["properties"]
    assert "effective_at" in properties
    assert "expired_at" in properties
    assert client.indexed_documents == [
        {
            "source_id": "rule-001",
            "source_type": "business_rule",
            "source_version": "sample-1",
            "business_type": "billing",
            "status": "active",
            "source_at": "2026-06-17T12:00:00+00:00",
            "effective_at": "2026-06-17T12:00:00+00:00",
            "expired_at": None,
            "chunk_id": "rule-001-chunk-1",
            "article_number": "1",
            "region": "全国",
            "product": "通用投诉",
            "full_text": "套餐费用核查规则",
            "metadata": {"title": "套餐变更规则"},
        }
    ]


def test_build_documents_maps_network_loss_rules_to_service(tmp_path) -> None:
    rules_path = tmp_path / "rules.md"
    complaints_path = tmp_path / "complaints.jsonl"
    rules_path.write_text(
        "# 业务规则\n\n"
        "## 网络异常损失处置规则\n\n"
        "第一条：不得直接承诺证券交易损失赔偿。\n",
        encoding="utf-8",
    )
    complaints_path.write_text(
        '{"complaint_id":"c-1","text":"网络异常","category":"service"}\n',
        encoding="utf-8",
    )

    documents = _build_documents(rules_path, complaints_path)

    rule_document = next(item for item in documents if item["source_id"] == "rule-001")
    assert rule_document["business_type"] == "service"
    assert "网络异常损失处置规则" in str(rule_document["full_text"])
