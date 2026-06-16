from __future__ import annotations

from typing import Any

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.retrieval.metrics import get_degradation_counts

REQUEST_LATENCY = Histogram(
    "suzhida_request_latency_seconds",
    "API request latency in seconds",
    ["route", "method", "status"],
)
WORKFLOW_NODE_DURATION = Histogram(
    "suzhida_workflow_node_duration_seconds",
    "Workflow node duration in seconds",
    ["node"],
)
RETRY_COUNT = Counter(
    "suzhida_retry_count_total",
    "Workflow retries",
    ["node"],
)
DEGRADATION_COUNT = Counter(
    "suzhida_degradation_count_total",
    "Retrieval degradations",
    ["source"],
)
MODEL_TIME_TO_FIRST_TOKEN = Histogram(
    "suzhida_model_time_to_first_token_seconds",
    "Model time to first token in seconds",
)
FEEDBACK_ACTIONS = Counter(
    "suzhida_feedback_actions_total",
    "Human feedback actions",
    ["action"],
)

_EVALUATION_SUMMARY: dict[str, Any] = {
    "mode": "smoke",
    "dataset_version": "unknown",
    "case_count": 0,
    "metrics": {},
}


def record_degradation(source: str) -> None:
    DEGRADATION_COUNT.labels(source=source).inc()


def set_evaluation_summary(summary: dict[str, Any]) -> None:
    global _EVALUATION_SUMMARY
    _EVALUATION_SUMMARY = summary


def get_evaluation_summary() -> dict[str, Any]:
    return _EVALUATION_SUMMARY


def build_metrics_summary(service_name: str) -> dict[str, Any]:
    return {
        "service": service_name,
        "retrieval": {
            "degradation_counts": get_degradation_counts(),
        },
        "evaluation": _EVALUATION_SUMMARY,
    }


def render_prometheus_metrics() -> str:
    return generate_latest().decode("utf-8")


__all__ = [
    "REQUEST_LATENCY",
    "WORKFLOW_NODE_DURATION",
    "RETRY_COUNT",
    "DEGRADATION_COUNT",
    "MODEL_TIME_TO_FIRST_TOKEN",
    "FEEDBACK_ACTIONS",
    "record_degradation",
    "set_evaluation_summary",
    "get_evaluation_summary",
    "build_metrics_summary",
    "render_prometheus_metrics",
    "CONTENT_TYPE_LATEST",
]

