from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INFRA_TESTS") != "1",
    reason="Milvus contract requires RUN_INFRA_TESTS=1",
)


def test_milvus_collection_is_available_from_api_runtime() -> None:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "api",
            "python",
            "-c",
            (
                "from pymilvus import MilvusClient; "
                "client = MilvusClient(uri='http://milvus:19530'); "
                "print(client.has_collection('suzhida_knowledge_sample'))"
            ),
        ],
        cwd=Path(__file__).parents[3],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip() == "True"
