from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_run_evaluation_writes_json_and_markdown_reports(tmp_path: Path) -> None:
    from app.evaluation.runner import run_evaluation

    dataset = tmp_path / "smoke.jsonl"
    dataset.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "case-1",
                        "dataset_version": "smoke-v1",
                        "relevant_evidence_ids": ["e1"],
                        "retrieved_evidence_ids": ["e1"],
                        "adopted": True,
                        "handling_seconds": 42,
                    }
                )
            ]
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "artifacts"
    summary = run_evaluation(dataset, mode="smoke", output_dir=output_dir)

    assert summary["case_count"] == 1
    assert (output_dir / "smoke-summary.json").exists()
    assert (output_dir / "smoke-summary.md").exists()


def test_acceptance_mode_requires_120_cases(tmp_path: Path) -> None:
    from app.evaluation.runner import run_evaluation

    dataset = tmp_path / "acceptance.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "case-1",
                "dataset_version": "acceptance-v1",
                "relevant_evidence_ids": ["e1"],
                "retrieved_evidence_ids": ["e1"],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="120"):
        run_evaluation(dataset, mode="acceptance", output_dir=tmp_path / "artifacts")
