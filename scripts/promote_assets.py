#!/usr/bin/env python3
"""Promote high-quality correction pairs into CorrectionStore as personalization assets."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage.correction_store import CorrectionStore

HQ_PATH = Path("data/high_quality_traces.jsonl")


def promote_from_jsonl(hq_path: Path, store: CorrectionStore) -> tuple[int, int]:
    """Return (promoted, skipped) counts."""
    promoted = 0
    skipped = 0
    with hq_path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            result = store.record_correction(
                artifact_id=rec["message_id"],
                session_id=rec["session_id"],
                source_message_id=rec["message_id"],
                original_text=rec["prompt"],
                corrected_text=rec["completion"],
            )
            if result is None:
                skipped += 1
                continue
            store.promote_correction(result["correction_id"])
            promoted += 1
    return promoted, skipped


def main() -> None:
    if not HQ_PATH.exists():
        print(f"No high-quality traces at {HQ_PATH} — run export_traces.py first.")
        return
    store = CorrectionStore()
    promoted, skipped = promote_from_jsonl(HQ_PATH, store)
    print(f"Promoted {promoted} correction pairs → data/corrections/ ({skipped} skipped)")


if __name__ == "__main__":
    sys.exit(main())
