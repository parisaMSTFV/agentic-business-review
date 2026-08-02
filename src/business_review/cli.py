"""Command-line interface for the synthetic business-review workflow."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from business_review.config import PROJECT_ROOT
from business_review.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    reproduce = subparsers.add_parser("reproduce", help="regenerate all checked-in artifacts")
    reproduce.add_argument("--output-root", type=Path, default=PROJECT_ROOT)
    reproduce.add_argument("--seed", type=int, default=42)
    reproduce.add_argument("--periods", type=int, default=64)
    subparsers.add_parser("smoke", help="run the complete pipeline in a temporary directory")
    args = parser.parse_args()

    if args.command == "smoke":
        with tempfile.TemporaryDirectory(prefix="business-review-") as directory:
            metrics = run_pipeline(Path(directory))
    else:
        metrics = run_pipeline(args.output_root, seed=args.seed, periods=args.periods)
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
