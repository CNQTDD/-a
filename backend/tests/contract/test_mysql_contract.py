from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INFRA_TESTS") != "1",
    reason="MySQL contract requires RUN_INFRA_TESTS=1",
)


def test_retrieved_evidence_uses_session_scoped_unique_constraint() -> None:
    result = _run_api_python(
        """
from sqlalchemy import create_engine, text
from app.core.config import Settings
import json

engine = create_engine(Settings().database_url, future=True)
with engine.connect() as conn:
    rows = conn.execute(
        text(
            '''
            SELECT index_name, non_unique, GROUP_CONCAT(column_name ORDER BY seq_in_index) AS columns_csv
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'retrieved_evidence'
            GROUP BY index_name, non_unique
            ORDER BY index_name
            '''
        )
    ).mappings().all()
    print(json.dumps([dict(row) for row in rows]))
"""
    )

    indexes = json.loads(result.stdout.strip())
    unique_indexes = {
        row["INDEX_NAME"]: row["columns_csv"]
        for row in indexes
        if int(row["NON_UNIQUE"]) == 0
    }

    assert unique_indexes.get("uq_session_evidence") == "session_id,evidence_id"
    assert all(columns != "evidence_id" for columns in unique_indexes.values())


def _run_api_python(source: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("DOCKER_CONFIG", str(Path(tempfile.gettempdir()) / "docker-config-codex"))
    Path(env["DOCKER_CONFIG"]).mkdir(parents=True, exist_ok=True)

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
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result
