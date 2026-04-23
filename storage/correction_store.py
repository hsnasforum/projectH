"""Correction pattern store.

Persists structured correction records as individual JSON files under
data/corrections/. Each record captures an original→corrected transformation
with delta analysis, fingerprint, and lifecycle status.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.contracts import CandidateFamily, CORRECTION_STATUS_TRANSITIONS, CorrectionStatus
from core.delta_analysis import compute_correction_delta

from .json_store_base import utc_now_iso, json_path, atomic_write, read_json, scan_json_dir


class CorrectionStore:
    def __init__(self, base_dir: str = "data/corrections") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, correction_id: str) -> Path:
        return json_path(self.base_dir, correction_id)

    def _scan_all(self) -> list[dict[str, Any]]:
        return [d for d in scan_json_dir(self.base_dir) if isinstance(d.get("correction_id"), str)]

    # -- Core operations --

    def record_correction(
        self,
        *,
        artifact_id: str,
        session_id: str,
        source_message_id: str,
        original_text: str,
        corrected_text: str,
        pattern_family: str = CandidateFamily.CORRECTION_REWRITE,
        applied_preference_ids: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Record a correction and compute its delta. Returns None if no delta."""
        delta = compute_correction_delta(original_text, corrected_text)
        if delta is None:
            return None

        with self._lock:
            existing = self._find_by_fingerprint_unlocked(delta.delta_fingerprint)

            for ex in existing:
                if (
                    ex.get("artifact_id") == artifact_id
                    and ex.get("source_message_id") == source_message_id
                    and ex.get("delta_fingerprint") == delta.delta_fingerprint
                ):
                    return ex

            recurrence_count = len(existing) + 1
            now = utc_now_iso()

            for ex in existing:
                ex["recurrence_count"] = recurrence_count
                ex["last_seen_at"] = now
                ex["updated_at"] = now
                atomic_write(self._path(ex["correction_id"]), ex)

            correction_id = f"correction-{uuid4().hex[:12]}"
            record: dict[str, Any] = {
                "correction_id": correction_id,
                "artifact_id": artifact_id,
                "session_id": session_id,
                "source_message_id": source_message_id,
                "original_text": original_text,
                "corrected_text": corrected_text,
                "delta_fingerprint": delta.delta_fingerprint,
                "delta_summary": delta.delta_summary,
                "similarity_score": delta.similarity_score,
                "rewrite_dimensions": delta.rewrite_dimensions,
                "pattern_family": pattern_family,
                "applied_preference_ids": applied_preference_ids,
                "recurrence_count": recurrence_count,
                "first_seen_at": now,
                "last_seen_at": now,
                "status": CorrectionStatus.RECORDED,
                "confirmed_at": None,
                "promoted_at": None,
                "activated_at": None,
                "stopped_at": None,
                "created_at": now,
                "updated_at": now,
            }
            atomic_write(self._path(correction_id), record)
            return record

    def get(self, correction_id: str) -> dict[str, Any] | None:
        with self._lock:
            return read_json(self._path(correction_id))

    # -- Lifecycle transitions --

    def _transition(self, correction_id: str, status: str, timestamp_field: str) -> dict[str, Any] | None:
        with self._lock:
            record = read_json(self._path(correction_id))
            if record is None:
                return None
            current_status = record.get("status")
            allowed = CORRECTION_STATUS_TRANSITIONS.get(current_status, ())
            if status not in allowed:
                return None
            now = utc_now_iso()
            record["status"] = status
            record[timestamp_field] = now
            record["updated_at"] = now
            atomic_write(self._path(correction_id), record)
            return record

    def confirm_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.CONFIRMED, "confirmed_at")

    def promote_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.PROMOTED, "promoted_at")

    def activate_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.ACTIVE, "activated_at")

    def stop_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.STOPPED, "stopped_at")

    # -- Queries --

    def _find_by_fingerprint_unlocked(self, delta_fingerprint: str) -> list[dict[str, Any]]:
        return [r for r in self._scan_all() if r.get("delta_fingerprint") == delta_fingerprint]

    def find_by_fingerprint(self, delta_fingerprint: str) -> list[dict[str, Any]]:
        with self._lock:
            return self._find_by_fingerprint_unlocked(delta_fingerprint)

    def find_by_artifact(self, artifact_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [r for r in self._scan_all() if r.get("artifact_id") == artifact_id]

    def find_by_session(self, session_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [r for r in self._scan_all() if r.get("session_id") == session_id]

    def find_recurring_patterns(self, *, session_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            all_records = self._scan_all()
            if session_id:
                all_records = [r for r in all_records if r.get("session_id") == session_id]

            groups: dict[str, list[dict[str, Any]]] = {}
            for r in all_records:
                fp = r.get("delta_fingerprint", "")
                if fp:
                    groups.setdefault(fp, []).append(r)

            return [
                {
                    "delta_fingerprint": fp,
                    "pattern_family": records[0].get("pattern_family", ""),
                    "recurrence_count": len(records),
                    "corrections": sorted(records, key=lambda x: x.get("created_at", "")),
                    "first_seen_at": min(r.get("first_seen_at", "") for r in records),
                    "last_seen_at": max(r.get("last_seen_at", "") for r in records),
                }
                for fp, records in groups.items()
                if len(records) >= 2
            ]

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            all_records = self._scan_all()
            all_records.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
            return all_records[:limit]

    def list_incomplete_corrections(self) -> list[dict[str, Any]]:
        _INCOMPLETE = {
            CorrectionStatus.RECORDED,
            CorrectionStatus.CONFIRMED,
            CorrectionStatus.PROMOTED,
        }
        with self._lock:
            return [r for r in self._scan_all() if r.get("status") in _INCOMPLETE]
