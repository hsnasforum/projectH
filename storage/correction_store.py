"""Correction pattern store.

Persists structured correction records as individual JSON files under
data/corrections/. Each record captures an original→corrected transformation
with delta analysis, fingerprint, and lifecycle status.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
import threading
from typing import Any
from uuid import uuid4

from core.contracts import CandidateFamily, CorrectionStatus
from core.delta_analysis import compute_correction_delta


class CorrectionStore:
    def __init__(self, base_dir: str = "data/corrections") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, correction_id: str) -> Path:
        safe_id = correction_id.replace("/", "-").replace("\\", "-").strip()
        return self.base_dir / f"{safe_id}.json"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _atomic_write(self, path: Path, data: dict[str, Any]) -> None:
        temp_path = path.with_name(f"{path.name}.{uuid4().hex[:8]}.tmp")
        encoded = json.dumps(data, ensure_ascii=False, indent=2)
        try:
            temp_path.write_text(encoded, encoding="utf-8")
            temp_path.replace(path)
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise

    def _read(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (JSONDecodeError, OSError):
            return None

    def _scan_all(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for p in self.base_dir.glob("*.json"):
            data = self._read(p)
            if data and isinstance(data.get("correction_id"), str):
                results.append(data)
        return results

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
    ) -> dict[str, Any] | None:
        """Record a correction and compute its delta. Returns None if no delta."""
        delta = compute_correction_delta(original_text, corrected_text)
        if delta is None:
            return None

        with self._lock:
            # Check for existing corrections with same fingerprint to get recurrence count
            existing = self._find_by_fingerprint_unlocked(delta.delta_fingerprint)

            # Deduplicate: don't record same (artifact_id, source_message_id, fingerprint) twice
            for ex in existing:
                if (
                    ex.get("artifact_id") == artifact_id
                    and ex.get("source_message_id") == source_message_id
                    and ex.get("delta_fingerprint") == delta.delta_fingerprint
                ):
                    return ex

            recurrence_count = len(existing) + 1
            now = self._now()

            # Update existing records' recurrence count and last_seen_at
            for ex in existing:
                ex["recurrence_count"] = recurrence_count
                ex["last_seen_at"] = now
                ex["updated_at"] = now
                self._atomic_write(self._path(ex["correction_id"]), ex)

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
            self._atomic_write(self._path(correction_id), record)
            return record

    def get(self, correction_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._read(self._path(correction_id))

    # -- Lifecycle transitions --

    def _transition(self, correction_id: str, status: str, timestamp_field: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._read(self._path(correction_id))
            if record is None:
                return None
            now = self._now()
            record["status"] = status
            record[timestamp_field] = now
            record["updated_at"] = now
            self._atomic_write(self._path(correction_id), record)
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
        """Return pattern groups with 2+ corrections sharing the same fingerprint."""
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
