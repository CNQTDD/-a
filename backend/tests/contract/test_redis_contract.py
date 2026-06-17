from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INFRA_TESTS") != "1",
    reason="Redis contract requires RUN_INFRA_TESTS=1",
)


def test_redis_round_trip_from_api_runtime() -> None:
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
                "import redis; "
                "client = redis.Redis.from_url('redis://redis:6379/0'); "
                "client.set('contract:ping', 'pong', ex=30); "
                "print(client.get('contract:ping').decode())"
            ),
        ],
        cwd=Path(__file__).parents[3],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip() == "pong"
