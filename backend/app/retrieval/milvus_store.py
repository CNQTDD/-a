from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime
from math import fsum
from typing import Any

from app.retrieval.contracts import RetrievalHit, VectorRecord


class MilvusStore:
    """面向业务的 Milvus 适配器，默认可使用内存集合做单测。"""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    def ensure_collection(self) -> None:
        # 单测用的内存集合会暴露 ensure_initialized；真实 Milvus 后续可在这里接入。
        if hasattr(self._collection, "ensure_initialized"):
            self._collection.ensure_initialized()

    def upsert(self, records: Iterable[dict[str, Any] | VectorRecord]) -> None:
        # 以 evidence_id 作为稳定主键，重复写入会覆盖旧记录。
        for record in records:
            payload = (
                asdict(record) if isinstance(record, VectorRecord) else dict(record)
            )
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

    def _iter_records(self) -> Iterable[dict[str, Any]]:
        if hasattr(self._collection, "records"):
            return self._collection.records.values()
        if hasattr(self._collection, "all_records"):
            return self._collection.all_records()
        raise TypeError("collection does not expose records")

    def _matches_filters(self, record: dict[str, Any], filters: dict[str, Any]) -> bool:
        # 版本、业务类型和生效/失效时间都必须精确匹配，避免检索层漂移。
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
        return float(
            fsum(left * right for left, right in zip(query_vector, record_vector))
        )

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
