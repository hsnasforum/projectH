#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline_gui.token_queries import (
    get_link_method_summaries,
    get_link_samples,
    get_unlinked_usage_counts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect token job-link confidence and unlinked usage.")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--day")
    parser.add_argument("--source", choices=("claude", "codex", "gemini"))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-confidence", type=float)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.6)
    args = parser.parse_args(argv)

    db_path = Path(args.db_path)
    sources = (args.source,) if args.source else None
    summaries = get_link_method_summaries(
        db_path,
        day=args.day,
        sources=sources,
        low_confidence_threshold=args.low_confidence_threshold,
    )
    samples = get_link_samples(
        db_path,
        day=args.day,
        source=args.source,
        max_confidence=args.max_confidence,
        limit=args.limit,
    )
    unlinked = get_unlinked_usage_counts(db_path, day=args.day, sources=sources)

    print("== Link method summary ==")
    if not summaries:
        print("(none)")
    for item in summaries:
        print(
            f"{item.source:7s}  {item.link_method:32s}  events={item.events:4d}  jobs={item.jobs:3d}  "
            f"avg={item.avg_confidence:.2f}  max={item.max_confidence:.2f}  low={item.low_confidence_events:3d}"
        )

    print("\n== Low-confidence samples ==")
    if not samples:
        print("(none)")
    for item in samples:
        print(
            f"{item.source:7s}  c={item.confidence:.2f}  {item.link_method:32s}  "
            f"{item.job_id}  {item.ts}  tok={item.total_tokens:5d}  cost=${item.total_cost_usd:.2f}"
        )
        if item.note:
            print(f"  note: {item.note}")
        if item.raw_path:
            print(f"  raw:  {item.raw_path}")

    print("\n== Unlinked usage ==")
    if not unlinked:
        print("(none)")
    for item in unlinked:
        print(
            f"{item.source:7s}  events={item.events:4d}  tok={item.total_tokens:6d}  cost=${item.total_cost_usd:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
