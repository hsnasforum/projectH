#!/usr/bin/env python3
"""Export grounded-brief correction pairs as JSONL for Milestone 12 personalization."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.delta_analysis import compute_correction_delta
from storage.session_store import SessionStore

ALL_PATH = Path("data/all_traces.jsonl")
HQ_PATH = Path("data/high_quality_traces.jsonl")


def _is_high_quality(similarity_score: float) -> bool:
    return 0.05 <= similarity_score <= 0.98


def main() -> None:
    store = SessionStore()
    ALL_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_count = 0
    hq_count = 0
    with ALL_PATH.open("w", encoding="utf-8") as all_out, \
            HQ_PATH.open("w", encoding="utf-8") as hq_out:
        for pair in store.stream_trace_pairs():
            delta = compute_correction_delta(pair["prompt"], pair["completion"])
            if delta is None:
                continue
            record = {
                **pair,
                "similarity_score": delta.similarity_score,
                "change_types": delta.rewrite_dimensions.get("change_types", []),
                "is_high_quality": _is_high_quality(delta.similarity_score),
            }
            all_out.write(json.dumps(record, ensure_ascii=False) + "\n")
            all_count += 1
            if record["is_high_quality"]:
                hq_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                hq_count += 1
    print(f"Exported {all_count} correction pairs → {ALL_PATH}")
    print(f"High-quality pairs: {hq_count} → {HQ_PATH}")


if __name__ == "__main__":
    sys.exit(main())
