from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime
from math import fsum
from typing import Any

from app.retrieval.contracts import RetrievalHit, VectorRecord


class MilvusStore:
    """面向业务的 Milvus 适配器，兼容真实 MilvusClient 与单测内存集合。"""

    def __init__(self, collection: Any, collection_name: str | None = None) -> None:
        self._collection = collection
        self._collection_name = collection_name

    def ensure_collection(self) -> None:
        if hasattr(self._collection, "ensure_initialized"):
            self._collection.ensure_initialized()

    def upsert(self, records: Iterable[dict[str, Any] | VectorRecord]) -> None:
        for record in records:
            payload = asdict(record) if isinstance(record, VectorRecord) else dict(record)
            if hasattr(self._collection, "upsert"):
                self._collection.upsert(payload)
                continue
            raise TypeError("collection does not support upsert")

    def search(
        self,
        *,
        vector: list[float],
        limit: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalHit]:
        filters = filters or {}
        if hasattr(self._collection, "records") or hasattr(self._collection, "all_records"):
            return self._search_fake_collection(vector=vector, limit=limit, filters=filters)
        if self._collection_name is None or not hasattr(self._collection, "search"):
            raise TypeError("collection does not expose a searchable Milvus interface")
        self._ensure_loaded()
        return self._search_milvus_client(vector=vector, limit=limit, filters=filters)

    def _ensure_loaded(self) -> None:
        if not hasattr(self._collection, "load_collection") or self._collection_name is None:
            return
        try:
            self._collection.load_collection(self._collection_name)
        except TypeError:
            self._collection.load_collection(collection_name=self._collection_name)

    def _search_fake_collection(
        self,
        *,
        vector: list[float],
        limit: int,
        filters: dict[str, Any],
    ) -> list[RetrievalHit]:
        all_records = list(self._iter_records())
        filtered = [
            record for record in all_records if self._matches_filters(record, filters)
        ]
        scored = sorted(
            (
                self._to_hit(record, self._score(vector, record.get("vector", [])))
                for record in filtered
            ),
            key=lambda item: (-item.score, item.source_id),
        )
        return scored[:limit]

    def _search_milvus_client(
        self,
        *,
        vector: list[float],
        limit: int,
        filters: dict[str, Any],
    ) -> list[RetrievalHit]:
        expr = self._build_filter_expr(filters)
        results = self._collection.search(
            self._collection_name,
            data=[vector],
            filter=expr,
            limit=limit,
            output_fields=[
                "evidence_id",
                "chunk_id",
                "source_id",
                "source_type",
                "business_type",
                "status",
                "content_snapshot",
            ],
            anns_field="vector",
        )
        rows = results[0] if results else []
        hits: list[RetrievalHit] = []
        for row in rows:
            entity = row.get("entity", row)
            hits.append(
                RetrievalHit(
                    evidence_id=str(entity["evidence_id"]),
                    chunk_id=str(entity["chunk_id"]),
                    source_id=str(entity["source_id"]),
                    source_type=str(entity["source_type"]),
                    business_type=str(entity["business_type"]),
                    region="全国",
                    product="通用投诉",
                    source_version=str(filters.get("source_version", "sample-1")),
                    status=str(entity.get("status", "active")),
                    source_at=None,
                    effective_at=None,
                    expired_at=None,
                    article_number=None,
                    content_snapshot=str(entity["content_snapshot"]),
                    score=float(row.get("distance", row.get("score", 0.0))),
                    metadata={"title": str(entity["source_id"])},
                )
            )
        return hits

    def _build_filter_expr(self, filters: dict[str, Any]) -> str:
        expressions: list[str] = ['status == "active"']
        for key in ("source_version", "business_type"):
            value = filters.get(key)
            if value is not None:
                expressions.append(f'{key} == "{value}"')
        return " and ".join(expressions)

    def _iter_records(self) -> Iterable[dict[str, Any]]:
        if hasattr(self._collection, "records"):
            return self._collection.records.values()
        if hasattr(self._collection, "all_records"):
            return self._collection.all_records()
        raise TypeError("collection does not expose records")

    def _matches_filters(self, record: dict[str, Any], filters: dict[str, Any]) -> bool:
        for key in ("source_version", "business_type"):
            expected = filters.get(key)
            if expected is not None and record.get(key) != expected:
                return False

        as_of = filters.get("as_of")
        if isinstance(as_of, datetime):
            effective_at = record.get("effective_at")
            expired_at = record.get("expired_at")
            if isinstance(effective_at, datetime) and as_of < effective_at:
                return False
            if isinstance(expired_at, datetime) and as_of >= expired_at:
                return False
        return True

    def _score(self, query_vector: list[float], record_vector: list[float]) -> float:
        if not query_vector or not record_vector:
            return 0.0
        return float(fsum(left * right for left, right in zip(query_vector, record_vector)))

    def _to_hit(self, record: dict[str, Any], score: float) -> RetrievalHit:
        return RetrievalHit(
            evidence_id=record["evidence_id"],
            chunk_id=record["chunk_id"],
            source_id=record["source_id"],
            source_type=record["source_type"],
            business_type=record["business_type"],
            region=record["region"],
            product=record["product"],
            source_version=record["source_version"],
            status=record["status"],
            source_at=record.get("source_at"),
            effective_at=record.get("effective_at"),
            expired_at=record.get("expired_at"),
            article_number=record.get("article_number"),
            content_snapshot=record["content_snapshot"],
            score=score,
            metadata=record.get("metadata"),
        )
