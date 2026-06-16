from __future__ import annotations

import argparse
from pathlib import Path

from app.evaluation.runner import run_evaluation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an offline evaluation")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--mode", choices=["smoke", "acceptance"], required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts") / "evaluation")
    args = parser.parse_args()

    summary = run_evaluation(args.dataset, mode=args.mode, output_dir=args.output_dir)
    print(
        f"Wrote {args.mode} evaluation for {summary['case_count']} cases to {args.output_dir}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
