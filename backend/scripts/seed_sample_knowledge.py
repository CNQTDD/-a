from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from elasticsearch import Elasticsearch
from pymilvus import DataType, MilvusClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.complaint import KnowledgeDocument, User


DEMO_USER_ID = "11111111-1111-4111-8111-111111111111"


def _parse_rules(path: Path) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    title: str | None = None
    body: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            if title is not None:
                sections.append({"title": title, "body": "\n".join(body).strip()})
            title = line[3:].strip()
            body = []
            continue
        if title is not None:
            body.append(raw_line)

    if title is not None:
        sections.append({"title": title, "body": "\n".join(body).strip()})
    return sections


def _load_complaints(path: Path) -> list[dict[str, str]]:
    complaints: list[dict[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line.strip():
            complaints.append(json.loads(raw_line))
    return complaints


def _vector(seed_text: str) -> list[float]:
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    return [
        round(int.from_bytes(digest[i : i + 4], "big") / 2**32, 6)
        for i in range(0, 16, 4)
    ]


def _rule_business_type(title: str) -> str:
    if "套餐变更规则" in title:
        return "billing"
    if "退费规则" in title:
        return "refund"
    if (
        "宽带服务时限规则" in title
        or "网络异常损失处置规则" in title
        or "服务影响生产经营与经济损失处置规则" in title
    ):
        return "service"
    return "billing"


def _build_documents(rules_path: Path, complaints_path: Path) -> list[dict[str, object]]:
    docs: list[dict[str, object]] = []
    batch_id = f"sample-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    for complaint in _load_complaints(complaints_path):
        docs.append(
            {
                "source_id": complaint["complaint_id"],
                "source_type": "sample_complaint",
                "source_version": "sample-1",
                "business_type": complaint.get("category", "billing"),
                "status": "active",
                "import_batch_id": batch_id,
                "effective_at": datetime.now(timezone.utc),
                "expired_at": None,
                "full_text": complaint["text"],
                "metadata": {
                    "region": complaint.get("region"),
                    "resolution": complaint.get("resolution"),
                },
            }
        )

    for index, rule in enumerate(_parse_rules(rules_path), start=1):
        docs.append(
            {
                "source_id": f"rule-{index:03d}",
                "source_type": "business_rule",
                "source_version": "sample-1",
                "business_type": _rule_business_type(rule["title"]),
                "status": "active",
                "import_batch_id": batch_id,
                "effective_at": datetime.now(timezone.utc),
                "expired_at": None,
                "full_text": f"{rule['title']}\n{rule['body']}",
                "metadata": {"title": rule["title"]},
            }
        )

    return docs


def _seed_sqlalchemy(database_url: str, documents: list[dict[str, object]]) -> None:
    engine = create_engine(database_url, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    with session_factory() as session:
        demo_user = session.get(User, DEMO_USER_ID)
        if demo_user is None:
            session.add(User(id=DEMO_USER_ID, name="Demo Agent", role="agent"))

        for document in documents:
            existing = (
                session.query(KnowledgeDocument)
                .filter_by(
                    source_id=document["source_id"],
                    source_type=document["source_type"],
                    source_version=document["source_version"],
                )
                .one_or_none()
            )
            if existing is None:
                session.add(
                    KnowledgeDocument(
                        **{k: v for k, v in document.items() if k != "full_text"}
                    )
                )
            else:
                existing.business_type = str(document["business_type"])
                existing.status = str(document["status"])
                existing.import_batch_id = str(document["import_batch_id"])
                existing.effective_at = document["effective_at"]  # type: ignore[assignment]
                existing.expired_at = document["expired_at"]  # type: ignore[assignment]
        session.commit()


def _serialize_datetime(value: object) -> str | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _seed_elasticsearch(elasticsearch_url: str, documents: list[dict[str, object]]) -> None:
    client = Elasticsearch(elasticsearch_url)
    index_name = "suzhida-knowledge-sample"
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
    client.indices.create(
        index=index_name,
        mappings={
            "properties": {
                "chunk_id": {"type": "keyword"},
                "source_id": {"type": "keyword"},
                "source_type": {"type": "keyword"},
                "source_version": {"type": "keyword"},
                "business_type": {"type": "keyword"},
                "region": {"type": "keyword"},
                "product": {"type": "keyword"},
                "status": {"type": "keyword"},
                "source_at": {"type": "date"},
                "effective_at": {"type": "date"},
                "expired_at": {"type": "date"},
                "article_number": {"type": "keyword"},
                "full_text": {"type": "text"},
                "metadata": {"type": "object"},
            }
        },
    )

    for index, document in enumerate(documents, start=1):
        metadata = dict(document.get("metadata", {}))
        effective_at = _serialize_datetime(document.get("effective_at"))
        expired_at = _serialize_datetime(document.get("expired_at"))
        client.index(
            index=index_name,
            id=str(document["source_id"]),
            document={
                "chunk_id": f"{document['source_id']}-chunk-{index}",
                "source_id": document["source_id"],
                "source_type": document["source_type"],
                "source_version": document["source_version"],
                "business_type": document["business_type"],
                "region": metadata.get("region", "全国"),
                "product": metadata.get("product", "通用投诉"),
                "status": document["status"],
                "source_at": effective_at,
                "effective_at": effective_at,
                "expired_at": expired_at,
                "article_number": metadata.get("article_number", "1"),
                "full_text": document["full_text"],
                "metadata": metadata,
            },
        )


def _seed_milvus(milvus_uri: str, documents: list[dict[str, object]]) -> None:
    client = MilvusClient(uri=milvus_uri)
    collection_name = "suzhida_knowledge_sample"
    if client.has_collection(collection_name):
        client.drop_collection(collection_name)

    schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=True)
    schema.add_field(
        field_name="evidence_id",
        datatype=DataType.VARCHAR,
        is_primary=True,
        max_length=100,
    )
    schema.add_field(field_name="source_id", datatype=DataType.VARCHAR, max_length=200)
    schema.add_field(field_name="chunk_id", datatype=DataType.VARCHAR, max_length=200)
    schema.add_field(field_name="source_type", datatype=DataType.VARCHAR, max_length=30)
    schema.add_field(
        field_name="business_type", datatype=DataType.VARCHAR, max_length=100
    )
    schema.add_field(field_name="status", datatype=DataType.VARCHAR, max_length=20)
    schema.add_field(
        field_name="content_snapshot", datatype=DataType.VARCHAR, max_length=2048
    )
    schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=4)

    client.create_collection(collection_name=collection_name, schema=schema)
    rows = [
        {
            "evidence_id": str(document["source_id"]),
            "source_id": str(document["source_id"]),
            "chunk_id": f"{document['source_id']}-chunk-{index}",
            "source_type": str(document["source_type"]),
            "business_type": str(document["business_type"]),
            "status": str(document["status"]),
            "content_snapshot": str(document["full_text"])[:2048],
            "vector": _vector(str(document["full_text"])),
        }
        for index, document in enumerate(documents, start=1)
    ]
    client.insert(collection_name=collection_name, data=rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed sample knowledge data.")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--elasticsearch-url", required=True)
    parser.add_argument("--milvus-uri", required=True)
    parser.add_argument(
        "--rules-file",
        type=Path,
        default=Path("..") / "data" / "samples" / "rules.md",
    )
    parser.add_argument(
        "--complaints-file",
        type=Path,
        default=Path("..") / "data" / "samples" / "complaints.jsonl",
    )
    args = parser.parse_args()

    documents = _build_documents(args.rules_file, args.complaints_file)
    _seed_sqlalchemy(args.database_url, documents)
    _seed_elasticsearch(args.elasticsearch_url, documents)
    _seed_milvus(args.milvus_uri, documents)
    print(f"Seeded {len(documents)} sample knowledge documents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
