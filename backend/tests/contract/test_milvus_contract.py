from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INFRA_TESTS") != "1",
    reason="Milvus contract is deferred unless RUN_INFRA_TESTS=1",
)


def test_milvus_contract_placeholder() -> None:
    # 这里先保留一个合约测试入口，等 Task 19 再接真实 Milvus。
    assert True
