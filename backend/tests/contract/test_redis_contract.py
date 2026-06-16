from __future__ import annotations

import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INFRA_TESTS") != "1",
    reason="Redis contract is deferred unless RUN_INFRA_TESTS=1",
)


def test_redis_contract_placeholder() -> None:
    # Task 19 会把这个入口接到真实 Redis 集群。
    assert True
