from __future__ import annotations

import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INFRA_TESTS") != "1",
    reason="Elasticsearch contract is deferred unless RUN_INFRA_TESTS=1",
)


def test_elasticsearch_contract_placeholder() -> None:
    # Task 19 会把这个入口接到真实 Elasticsearch 集群。
    assert True
