#!/usr/bin/env python3
"""Audit local session traces for Milestone 12 precondition assessment."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage.session_store import SessionStore


def main() -> None:
    store = SessionStore()
    summary = store.get_global_audit_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    total_feedback = summary["feedback_like_count"] + summary["feedback_dislike_count"]
    print(
        f"\nSummary:\n"
        f"  Sessions:          {summary['session_count']}\n"
        f"  Correction pairs:  {summary['correction_pair_count']}\n"
        f"  Feedback signals:  {total_feedback} "
        f"(like={summary['feedback_like_count']}, dislike={summary['feedback_dislike_count']})\n"
        f"  Operator actions:  "
        f"executed={summary['operator_executed_count']}, "
        f"rolled_back={summary['operator_rolled_back_count']}, "
        f"failed={summary['operator_failed_count']}"
    )


if __name__ == "__main__":
    sys.exit(main())
