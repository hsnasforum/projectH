#!/usr/bin/env python3
"""Audit local session traces for Milestone 12 precondition assessment."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage.correction_store import CorrectionStore
from storage.preference_store import PreferenceStore
from storage.session_store import SessionStore


def main() -> None:
    store = SessionStore()
    summary = store.get_global_audit_summary()
    pref_store = PreferenceStore()
    correction_store = CorrectionStore()
    candidates = pref_store.get_candidates()
    active_prefs = pref_store.get_active_preferences()
    incomplete = correction_store.list_incomplete_corrections()

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    total_feedback = summary["feedback_like_count"] + summary["feedback_dislike_count"]
    personalized_total = summary["personalized_response_count"]
    personalized_corrected = summary["personalized_correction_count"]
    correction_rate = (
        f"{personalized_corrected / personalized_total:.1%}"
        if personalized_total > 0
        else "N/A (no personalized responses yet)"
    )
    print(
        f"\nSummary:\n"
        f"  Sessions:          {summary['session_count']}\n"
        f"  Correction pairs:  {summary['correction_pair_count']}\n"
        f"  Feedback signals:  {total_feedback} "
        f"(like={summary['feedback_like_count']}, dislike={summary['feedback_dislike_count']})\n"
        f"  Operator actions:  "
        f"executed={summary['operator_executed_count']}, "
        f"rolled_back={summary['operator_rolled_back_count']}, "
        f"failed={summary['operator_failed_count']}\n"
        f"  Preferences:       candidate={len(candidates)}, active={len(active_prefs)}\n"
        f"  Personalized responses:   {personalized_total}\n"
        f"  Personalized corrections: {personalized_corrected}\n"
        f"  Personalization correction rate: {correction_rate}"
    )
    print(
        f"\nIncomplete corrections (RECORDED/CONFIRMED/PROMOTED): {len(incomplete)}"
    )
    if incomplete:
        for rec in incomplete[:5]:
            print(
                f"  correction_id={rec.get('correction_id', '?')[:16]}…  "
                f"status={rec.get('status')}  "
                f"created={rec.get('created_at', '?')[:10]}"
            )
        if len(incomplete) > 5:
            print(f"  … and {len(incomplete) - 5} more")
    per_pref = summary.get("per_preference_stats", {})
    if per_pref:
        sorted_prefs = sorted(
            per_pref.items(),
            key=lambda x: x[1]["corrected_count"] / x[1]["applied_count"]
            if x[1]["applied_count"] > 0 else 0,
            reverse=True,
        )
        print("\nPer-preference reliability:")
        for pref_id, pstats in sorted_prefs:
            rate = (
                f"{pstats['corrected_count'] / pstats['applied_count']:.1%}"
                if pstats["applied_count"] > 0 else "N/A"
            )
            print(
                f"  {pref_id}: applied={pstats['applied_count']}, "
                f"corrected={pstats['corrected_count']}, correction_rate={rate}"
            )
    else:
        print("\nPer-preference reliability: N/A (no personalized responses yet)")


if __name__ == "__main__":
    sys.exit(main())
