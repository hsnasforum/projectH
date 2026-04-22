#!/usr/bin/env python3
"""Evaluate correction trace quality and produce a model-layer justification report."""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ALL_PATH = Path("data/all_traces.jsonl")

MIN_PAIRS = 100
MIN_HQ_PAIRS = 50


def evaluate(records: list[dict]) -> None:
    n = len(records)
    if n == 0:
        print("No correction pairs found. Run export_traces.py first.")
        return

    scores = [r["similarity_score"] for r in records]
    hq_count = sum(1 for r in records if r.get("is_high_quality"))
    feedback_enriched = sum(1 for r in records if r.get("feedback"))
    prompt_lens = [len(r.get("prompt", "")) for r in records]
    completion_lens = [len(r.get("completion", "")) for r in records]
    length_deltas = [
        len(r.get("completion", "")) - len(r.get("prompt", "")) for r in records
    ]

    print("=== Milestone 12 Metric Baseline Report ===")
    print(f"Correction pairs:    {n}")
    print(f"High-quality:        {hq_count} ({100 * hq_count // n}%)")
    print(f"Feedback-enriched:   {feedback_enriched}")
    print(
        f"Similarity score:    min={min(scores):.3f}  max={max(scores):.3f}"
        f"  mean={statistics.mean(scores):.3f}  median={statistics.median(scores):.3f}"
    )
    print(f"Prompt length:       mean={statistics.mean(prompt_lens):.0f} chars")
    print(f"Completion length:   mean={statistics.mean(completion_lens):.0f} chars")
    print(
        f"Length delta:        mean={statistics.mean(length_deltas):+.0f} chars"
        f"  (positive = completions are longer)"
    )

    justified = n >= MIN_PAIRS and hq_count >= MIN_HQ_PAIRS
    verdict = "JUSTIFIED" if justified else "INSUFFICIENT DATA"
    print(f"\nModel layer justification: {verdict}")
    print(
        f"  → {n} correction pairs (threshold: ≥{MIN_PAIRS}),"
        f" {hq_count} high-quality (threshold: ≥{MIN_HQ_PAIRS})"
    )


def main() -> None:
    if not ALL_PATH.exists():
        print(f"No traces at {ALL_PATH} — run export_traces.py first.")
        return
    records = [
        json.loads(line)
        for line in ALL_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    evaluate(records)


if __name__ == "__main__":
    sys.exit(main())
