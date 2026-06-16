from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.retrieval.metrics import record_degradation


class TemplateStore:
    """Redis 模板存储。

    设计上保留版本化 key 和 catalog 索引，方便后续扩展到真实 Redis。
    """

    def __init__(self, client: Any, namespace: str = "template") -> None:
        self._client = client
        self._namespace = namespace
        self.degraded_sources: list[str] = []

    def _template_key(self, template_id: str, version: str) -> str:
        return f"{self._namespace}:{template_id}:{version}"

    def _catalog_key(self) -> str:
        return f"{self._namespace}:catalog"

    def put(self, template: dict[str, Any]) -> None:
        # 模板写入时保留一份 catalog，便于后续按条件扫描命中。
        version = str(template.get("version") or "v1")
        key = self._template_key(str(template["template_id"]), version)
        raw = json.dumps(template, ensure_ascii=False, default=str)

        self._client.set(key, raw)

        catalog = self._load_catalog()
        if key not in catalog:
            catalog.append(key)
            self._client.set(
                self._catalog_key(), json.dumps(catalog, ensure_ascii=False)
            )

    def get(
        self,
        *,
        intent: str,
        business_type: str,
        confidence: float,
        as_of: datetime,
    ) -> dict[str, Any] | None:
        try:
            for key in self._load_catalog():
                raw = self._client.get(key)
                if raw is None:
                    continue
                template = json.loads(raw)
                if self._matches(template, intent, business_type, confidence, as_of):
                    return template
            return None
        except Exception:
            # Redis 失效时不要让主流程崩掉，直接记录一次降级并当作缓存未命中。
            self._mark_degraded()
            return None

    def _load_catalog(self) -> list[str]:
        raw = self._client.get(self._catalog_key())
        if not raw:
            return []
        catalog = json.loads(raw)
        if not isinstance(catalog, list):
            return []
        return [str(item) for item in catalog]

    def _matches(
        self,
        template: dict[str, Any],
        intent: str,
        business_type: str,
        confidence: float,
        as_of: datetime,
    ) -> bool:
        if template.get("intent") != intent:
            return False
        if template.get("business_type") != business_type:
            return False
        if template.get("status", "active") != "active":
            return False

        minimum_confidence = float(template.get("minimum_confidence", 0.0))
        if confidence < minimum_confidence:
            return False

        effective_at = self._parse_datetime(template.get("effective_at"))
        expired_at = self._parse_datetime(template.get("expired_at"))
        if effective_at is not None and as_of < effective_at:
            return False
        if expired_at is not None and as_of >= expired_at:
            return False
        return True

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    def _mark_degraded(self) -> None:
        if "redis" not in self.degraded_sources:
            self.degraded_sources.append("redis")
        record_degradation("redis")
