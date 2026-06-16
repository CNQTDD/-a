from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.evaluation.business_metrics import adoption_rate, average_handling_time
from app.evaluation.dataset import load_jsonl_dataset
from app.evaluation.retrieval_metrics import (
    citation_completeness,
    recall_at_k,
    top_k_hit_rate,
)
from app.observability.metrics import set_evaluation_summary


def run_evaluation(
    dataset_path: Path,
    *,
    mode: str,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    cases = load_jsonl_dataset(dataset_path)
    if mode == "acceptance" and len(cases) != 120:
        raise ValueError("acceptance datasets must contain exactly 120 cases")

    output_dir = output_dir or Path("artifacts") / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_version = _dataset_version(cases)
    retrieval_scores = [
        recall_at_k(
            case.get("relevant_evidence_ids", []),
            case.get("retrieved_evidence_ids", []),
            k=5,
        )
        for case in cases
    ]
    hit_rate = top_k_hit_rate(
        (
            {
                "relevant": case.get("relevant_evidence_ids", []),
                "retrieved": case.get("retrieved_evidence_ids", []),
            }
            for case in cases
        ),
        k=5,
    )
    citation_scores = [
        citation_completeness(
            case.get("relevant_evidence_ids", []),
            case.get("cited_evidence_ids", case.get("retrieved_evidence_ids", [])),
        )
        for case in cases
    ]
    adoption_scores = adoption_rate(
        [str(case.get("feedback_action", "accept")) for case in cases]
    )
    handling_times = average_handling_time(
        [float(case.get("handling_seconds", 0.0)) for case in cases]
    )

    summary: dict[str, Any] = {
        "mode": mode,
        "dataset_version": dataset_version,
        "case_count": len(cases),
        "metrics": {
            "recall_at_5": _mean(retrieval_scores),
            "top_k_hit_rate": hit_rate,
            "citation_completeness": _mean(citation_scores),
            "adoption_rate": adoption_scores,
            "average_handling_time": handling_times,
        },
    }

    json_path = output_dir / f"{mode}-summary.json"
    md_path = output_dir / f"{mode}-summary.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(summary), encoding="utf-8")
    set_evaluation_summary(summary)
    return summary


def _dataset_version(cases: list[dict[str, Any]]) -> str:
    versions = {str(case.get("dataset_version", "unknown")) for case in cases}
    return versions.pop() if len(versions) == 1 else "mixed"


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _render_markdown(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    return "\n".join(
        [
            f"# {summary['mode'].title()} Evaluation",
            "",
            f"- Dataset version: {summary['dataset_version']}",
            f"- Case count: {summary['case_count']}",
            f"- Recall@5: {metrics['recall_at_5']:.4f}",
            f"- Top-k hit rate: {metrics['top_k_hit_rate']:.4f}",
            f"- Citation completeness: {metrics['citation_completeness']:.4f}",
            f"- Adoption rate: {metrics['adoption_rate']:.4f}",
            f"- Average handling time: {metrics['average_handling_time']:.2f}",
        ]
    )
