from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pytest


@dataclass
class FakeRedisClient:
    # 用内存字典模拟 Redis，方便验证 key 命名、过期过滤和降级路径。
    data: dict[str, str] = field(default_factory=dict)
    fail_on_get: bool = False

    def get(self, key: str) -> str | None:
        if self.fail_on_get:
            raise TimeoutError("redis unavailable")
        return self.data.get(key)

    def set(self, key: str, value: str) -> None:
        self.data[key] = value


def build_store(client: FakeRedisClient):
    from app.retrieval.template_store import TemplateStore

    return TemplateStore(client=client, namespace="template")


def _template(
    *,
    template_id: str,
    intent: str,
    business_type: str,
    minimum_confidence: float,
    payload: str = "模板内容",
    status: str = "active",
    effective_at: datetime | None = None,
    expired_at: datetime | None = None,
):
    return {
        "template_id": template_id,
        "intent": intent,
        "business_type": business_type,
        "minimum_confidence": minimum_confidence,
        "payload": payload,
        "status": status,
        "effective_at": effective_at,
        "expired_at": expired_at,
    }


def test_template_returns_only_when_all_conditions_match() -> None:
    client = FakeRedisClient()
    store = build_store(client)

    store.put(
        _template(
            template_id="tpl-1",
            intent="billing",
            business_type="refund",
            minimum_confidence=0.8,
            effective_at=datetime(2026, 1, 1),
        )
    )

    hit = store.get(
        intent="billing",
        business_type="refund",
        confidence=0.85,
        as_of=datetime(2026, 6, 15),
    )

    assert hit is not None
    assert hit["template_id"] == "tpl-1"
    assert hit["payload"] == "模板内容"


def test_template_rejects_low_confidence_or_wrong_intent() -> None:
    client = FakeRedisClient()
    store = build_store(client)
    store.put(
        _template(
            template_id="tpl-1",
            intent="billing",
            business_type="refund",
            minimum_confidence=0.8,
        )
    )

    assert (
        store.get(
            intent="billing",
            business_type="refund",
            confidence=0.6,
            as_of=datetime(2026, 6, 15),
        )
        is None
    )
    assert (
        store.get(
            intent="service",
            business_type="refund",
            confidence=0.95,
            as_of=datetime(2026, 6, 15),
        )
        is None
    )


def test_template_ignores_expired_entries() -> None:
    client = FakeRedisClient()
    store = build_store(client)
    store.put(
        _template(
            template_id="tpl-1",
            intent="billing",
            business_type="refund",
            minimum_confidence=0.5,
            effective_at=datetime(2026, 1, 1),
            expired_at=datetime(2026, 6, 1),
        )
    )

    assert (
        store.get(
            intent="billing",
            business_type="refund",
            confidence=0.9,
            as_of=datetime(2026, 6, 15),
        )
        is None
    )


def test_redis_failure_is_reported_as_degradation() -> None:
    client = FakeRedisClient(fail_on_get=True)
    store = build_store(client)

    hit = store.get(
        intent="billing",
        business_type="refund",
        confidence=0.9,
        as_of=datetime(2026, 6, 15),
    )

    assert hit is None
    assert store.degraded_sources == ["redis"]
