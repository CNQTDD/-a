from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_jsonl_dataset(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        record = json.loads(stripped)
        if not isinstance(record, dict):
            raise ValueError("dataset rows must be JSON objects")
        records.append(record)
    return records
