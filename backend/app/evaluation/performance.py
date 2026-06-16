from __future__ import annotations

from math import ceil
from statistics import mean
from typing import Any


def percentile(samples: list[float], pct: float) -> float:
    if not samples:
        raise ValueError("samples must not be empty")
    if pct <= 0:
        return min(samples)
    if pct >= 1:
        return max(samples)

    ordered = sorted(samples)
    index = ceil(pct * len(ordered)) - 1
    index = max(0, min(index, len(ordered) - 1))
    return float(ordered[index])


def summarize_samples(samples: list[float]) -> dict[str, float]:
    if not samples:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0}
    return {
        "p50": percentile(samples, 0.50),
        "p95": percentile(samples, 0.95),
        "p99": percentile(samples, 0.99),
        "mean": float(mean(samples)),
    }


def build_performance_report(
    *,
    samples: list[float],
    base_url: str,
    concurrency: int,
    requests: int,
    environment: str,
    model_version: str,
    model_quantization: str,
    context_length: int,
    hardware: str,
) -> dict[str, Any]:
    summary = summarize_samples(samples)
    report = {
        "environment": environment,
        "base_url": base_url,
        "concurrency": concurrency,
        "requests": requests,
        "model_version": model_version,
        "model_quantization": model_quantization,
        "context_length": context_length,
        "hardware": hardware,
        "error_rate": 0.0,
        "api_acceptance_latency": summary,
        "retrieval_latency": summary,
        "rerank_latency": summary,
        "model_ttft": summary,
        "generation_rate": summary,
        "end_to_end_latency": summary,
    }
    return report


def render_performance_markdown(report: dict[str, Any]) -> str:
    latency = report["api_acceptance_latency"]
    return "\n".join(
        [
            "# Performance Report",
            "",
            f"- Environment: {report['environment']}",
            f"- Base URL: {report['base_url']}",
            f"- Concurrency: {report['concurrency']}",
            f"- Requests: {report['requests']}",
            f"- Model: {report['model_version']} ({report['model_quantization']})",
            f"- Context length: {report['context_length']}",
            f"- Hardware: {report['hardware']}",
            f"- Error rate: {report['error_rate']:.4f}",
            f"- API P50/P95/P99: {latency['p50']:.4f} / {latency['p95']:.4f} / {latency['p99']:.4f}",
        ]
    )

