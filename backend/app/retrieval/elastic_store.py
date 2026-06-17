from __future__ import annotations

from datetime import datetime
from typing import Any

from app.retrieval.contracts import RetrievalHit


class ElasticStore:
    """Elasticsearch 检索适配器。

    这个实现保留了清晰的查询构造逻辑，方便后续接入真实 Elasticsearch
    时只替换 client，不改业务层接口。
    """

    def __init__(self, index_name: str, client: Any) -> None:
        self._index_name = index_name
        self._client = client

    def ensure_index(self) -> None:
        # 索引映射只描述字段能力，不掺业务逻辑。
        mapping = {
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "source_id": {"type": "keyword"},
                    "source_type": {"type": "keyword"},
                    "business_type": {"type": "keyword"},
                    "region": {"type": "keyword"},
                    "product": {"type": "keyword"},
                    "source_version": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "source_at": {"type": "date"},
                    "effective_at": {"type": "date"},
                    "expired_at": {"type": "date"},
                    "article_number": {"type": "keyword"},
                    "full_text": {"type": "text"},
                }
            }
        }
        if hasattr(self._client, "ensure_index"):
            self._client.ensure_index(self._index_name, mapping)
            return
        indices = getattr(self._client, "indices", None)
        if indices is not None and hasattr(indices, "exists") and hasattr(indices, "create"):
            exists = indices.exists(index=self._index_name)
            exists_value = bool(getattr(exists, "body", exists))
            if not exists_value:
                indices.create(index=self._index_name, **mapping)
            return
        raise TypeError("client does not support ensure_index")

    def upsert(self, documents: list[dict[str, Any]]) -> None:
        # 按 chunk_id 幂等覆盖，避免同一来源重复写入造成脏数据。
        for document in documents:
            if hasattr(self._client, "index"):
                try:
                    self._client.index(self._index_name, document)
                except TypeError:
                    self._client.index(index=self._index_name, document=document)
                continue
            raise TypeError("client does not support index")

    def build_query(
        self,
        *,
        query: str,
        limit: int,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        filters = filters or {}
        must = [
            {
                "multi_match": {
                    # 词面优先：文章编号、套餐名、全文都参与检索。
                    "query": query,
                    "fields": [
                        "article_number^5",
                        "product^4",
                        "full_text^3",
                        "source_id^2",
                    ],
                    "type": "best_fields",
                }
            }
        ]

        query_filters: list[dict[str, Any]] = []
        for key in ("source_version", "business_type", "region", "product"):
            value = filters.get(key)
            if value is not None:
                query_filters.append({"term": {key: value}})

        as_of = filters.get("as_of")
        if isinstance(as_of, datetime):
            # 生效时间和失效时间都按 as_of 精确切片，保证只命中当前版本。
            query_filters.append(
                {"range": {"effective_at": {"lte": as_of.isoformat()}}}
            )
            query_filters.append({"range": {"expired_at": {"gt": as_of.isoformat()}}})

        return {
            "size": limit,
            "query": {
                "bool": {
                    "must": must,
                    "filter": query_filters,
                }
            },
        }

    def search(
        self,
        *,
        query: str,
        limit: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalHit]:
        body = self.build_query(query=query, limit=limit, filters=filters)
        try:
            response = self._client.search(self._index_name, body)
        except TypeError:
            response = self._client.search(index=self._index_name, body=body)
        if hasattr(response, "body"):
            response = response.body
        hits = response.get("hits", {}).get("hits", [])
        results: list[RetrievalHit] = []
        for item in hits:
            source = item.get("_source", {})
            evidence_id = source.get("evidence_id") or source["chunk_id"]
            results.append(
                RetrievalHit(
                    evidence_id=evidence_id,
                    chunk_id=source["chunk_id"],
                    source_id=source["source_id"],
                    source_type=source["source_type"],
                    business_type=source["business_type"],
                    region=source["region"],
                    product=source["product"],
                    source_version=source["source_version"],
                    status=source["status"],
                    source_at=source.get("source_at"),
                    effective_at=source.get("effective_at"),
                    expired_at=source.get("expired_at"),
                    article_number=source.get("article_number"),
                    content_snapshot=source["full_text"],
                    score=float(item.get("_score", 0.0)),
                    metadata=source.get("metadata"),
                )
            )
        return results
