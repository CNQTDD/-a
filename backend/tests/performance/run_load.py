from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from time import perf_counter

import httpx

from app.evaluation.performance import build_performance_report, render_performance_markdown


async def _measure_health(base_url: str, requests: int, concurrency: int) -> list[float]:
    semaphore = asyncio.Semaphore(concurrency)
    samples: list[float] = []

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
      async def one_request() -> None:
          async with semaphore:
              start = perf_counter()
              response = await client.get("/health")
              response.raise_for_status()
              samples.append(perf_counter() - start)

      await asyncio.gather(*(one_request() for _ in range(requests)))

    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a repeatable load test")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--requests", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--environment", default="local")
    parser.add_argument("--model-version", default="unknown")
    parser.add_argument("--model-quantization", default="unknown")
    parser.add_argument("--context-length", type=int, default=0)
    parser.add_argument("--hardware", default="unknown")
    args = parser.parse_args()

    samples = asyncio.run(_measure_health(args.base_url, args.requests, args.concurrency))
    report = build_performance_report(
        samples=samples,
        base_url=args.base_url,
        concurrency=args.concurrency,
        requests=args.requests,
        environment=args.environment,
        model_version=args.model_version,
        model_quantization=args.model_quantization,
        context_length=args.context_length,
        hardware=args.hardware,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    json_path = args.output / "performance.json"
    md_path = args.output / "performance.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_performance_markdown(report), encoding="utf-8")
    print(f"Wrote performance report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
