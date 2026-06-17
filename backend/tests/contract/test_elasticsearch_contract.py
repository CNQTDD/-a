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
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result
