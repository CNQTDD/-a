from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INFRA_TESTS") != "1",
    reason="Elasticsearch contract requires RUN_INFRA_TESTS=1",
)


def test_elasticsearch_cluster_is_queryable_from_api_runtime() -> None:
    result = _run_api_python(
        """
from elasticsearch import Elasticsearch
import json

client = Elasticsearch("http://elasticsearch:9200")
payload = {
    "health": client.cluster.health().body,
    "index_exists": bool(client.indices.exists(index="suzhida-knowledge-sample")),
}
print(json.dumps(payload))
"""
    )

    payload = json.loads(result.stdout.strip())
    assert payload["health"]["status"] in {"green", "yellow"}
    assert payload["index_exists"] is True


def test_seeded_knowledge_is_searchable_for_runtime_queries() -> None:
    result = _run_api_python(
        """
from app.core.config import Settings
from app.workflow.service import ComplaintWorkflowService
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import json

engine = create_engine(Settings().database_url, future=True)
with Session(engine) as db:
    service = ComplaintWorkflowService(db, settings=Settings())
    hits = service._search_elasticsearch_knowledge(
        query="我的套餐费用和账单不一致，请帮我核实",
        embedding=[0.1, 0.2, 0.3, 0.4],
        intent={"intent": "billing_dispute"},
    )
    print(json.dumps({
        "count": len(hits),
        "titles": [str((hit.metadata or {}).get("title") or hit.source_id) for hit in hits],
    }, ensure_ascii=False))
"""
    )

    payload = json.loads(result.stdout.strip())
    assert payload["count"] >= 1


def _run_api_python(source: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "api",
            "python",
            "-c",
            source,
        ],
        cwd=Path(__file__).parents[3],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result
