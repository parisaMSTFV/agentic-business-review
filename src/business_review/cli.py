"""Command-line interface for the synthetic business-review workflow."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from business_review.config import DEFAULT_OUTPUT_ROOT
from business_review.review import apply_review_decisions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    reproduce = subparsers.add_parser("reproduce", help="regenerate all checked-in artifacts")
    reproduce.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Output directory; defaults to an ignored local-run path.",
    )
    reproduce.add_argument("--seed", type=int, default=42)
    reproduce.add_argument("--periods", type=int, default=64)
    supplied = subparsers.add_parser("run", help="review a supplied weekly KPI CSV")
    supplied.add_argument("--input-weekly-kpis", type=Path, required=True)
    supplied.add_argument("--output-root", type=Path, required=True)
    decisions = subparsers.add_parser(
        "apply-decisions", help="apply validated human decisions to a claim queue"
    )
    decisions.add_argument("--claims", type=Path, required=True)
    decisions.add_argument("--decisions", type=Path, required=True)
    decisions.add_argument("--output", type=Path, required=True)
    subparsers.add_parser("smoke", help="run the complete pipeline in a temporary directory")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "apply-decisions":
        summary = apply_review_decisions(args.claims, args.decisions, args.output)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    from business_review.pipeline import run_pipeline

    if args.command == "smoke":
        with tempfile.TemporaryDirectory(prefix="business-review-") as directory:
            metrics = run_pipeline(Path(directory))
    elif args.command == "run":
        metrics = run_pipeline(args.output_root, input_path=args.input_weekly_kpis)
    else:
        metrics = run_pipeline(args.output_root, seed=args.seed, periods=args.periods)
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
