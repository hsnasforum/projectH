#!/usr/bin/env python3
"""Export grounded-brief correction pairs as JSONL for Milestone 12 personalization."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage.session_store import SessionStore

OUTPUT_PATH = Path("data/export_traces.jsonl")


def main() -> None:
    store = SessionStore()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with OUTPUT_PATH.open("w", encoding="utf-8") as out:
        for pair in store.stream_trace_pairs():
            out.write(json.dumps(pair, ensure_ascii=False) + "\n")
            count += 1
    print(f"Exported {count} correction pairs → {OUTPUT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
