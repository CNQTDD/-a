from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class VectorRecord:
    """Milvus 里一条可检索的向量记录。"""

    evidence_id: str
    chunk_id: str
    source_id: str
    source_type: str
    business_type: str
    region: str
    product: str
    source_version: str
    status: str
    source_at: datetime | None
    effective_at: datetime | None
    expired_at: datetime | None
    article_number: str | None
    content_snapshot: str
    vector: list[float]
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class RetrievalHit:
    """检索返回的命中结果，保留前端/后续融合需要的最小字段。"""

    evidence_id: str
    chunk_id: str
    source_id: str
    source_type: str
    business_type: str
    region: str
    product: str
    source_version: str
    status: str
    source_at: datetime | None
    effective_at: datetime | None
    expired_at: datetime | None
    article_number: str | None
    content_snapshot: str
    score: float
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class TemplateRecord:
    """Redis 里保存的模板记录。"""

    template_id: str
    intent: str
    business_type: str
    minimum_confidence: float
    payload: str
    status: str
    effective_at: datetime | None = None
    expired_at: datetime | None = None
    version: str = "v1"
