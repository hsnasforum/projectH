"""Cross-session preference memory store.

Persists durable user preferences derived from recurring correction patterns.
Unlike session-scoped reviewed_memory, these persist across sessions and
influence all future responses.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
import threading
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from core.contracts import CandidateFamily, PreferenceStatus

if TYPE_CHECKING:
    from storage.correction_store import CorrectionStore


class PreferenceStore:
    def __init__(self, base_dir: str = "data/preferences") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, preference_id: str) -> Path:
        safe_id = preference_id.replace("/", "-").replace("\\", "-").strip()
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
            if data and isinstance(data.get("preference_id"), str):
                results.append(data)
        return results

    # -- Core operations --

    def promote_from_corrections(
        self,
        delta_fingerprint: str,
        correction_store: CorrectionStore,
    ) -> dict[str, Any] | None:
        """Create a preference candidate from a recurring correction pattern.

        Returns None if fewer than 2 distinct sessions have this fingerprint.
        Idempotent: returns existing preference if already created.
        """
        with self._lock:
            # Check if preference already exists for this fingerprint
            existing = self.find_by_fingerprint(delta_fingerprint)
            if existing is not None:
                return self._refresh_evidence(existing, delta_fingerprint, correction_store)

            corrections = correction_store.find_by_fingerprint(delta_fingerprint)
            if len(corrections) < 2:
                return None

            session_ids = {c.get("session_id") for c in corrections if c.get("session_id")}
            if len(session_ids) < 2:
                return None

            # Use the delta_summary from the first correction
            delta_summary = corrections[0].get("delta_summary", {})
            description = self._generate_description(delta_summary)

            source_corrections = [
                {
                    "correction_id": c["correction_id"],
                    "session_id": c.get("session_id", ""),
                    "artifact_id": c.get("artifact_id", ""),
                }
                for c in corrections
            ]

            now = self._now()
            preference_id = f"pref-{uuid4().hex[:12]}"
            record: dict[str, Any] = {
                "preference_id": preference_id,
                "delta_fingerprint": delta_fingerprint,
                "pattern_family": corrections[0].get("pattern_family", CandidateFamily.CORRECTION_REWRITE),
                "description": description,
                "source_corrections": source_corrections,
                "evidence_count": len(corrections),
                "cross_session_count": len(session_ids),
                "delta_summary": delta_summary,
                "status": PreferenceStatus.CANDIDATE,
                "activated_at": None,
                "paused_at": None,
                "rejected_at": None,
                "created_at": now,
                "updated_at": now,
            }
            self._atomic_write(self._path(preference_id), record)
            return record

    def _refresh_evidence(
        self,
        preference: dict[str, Any],
        delta_fingerprint: str,
        correction_store: CorrectionStore,
    ) -> dict[str, Any]:
        """Update evidence counts on an existing preference."""
        corrections = correction_store.find_by_fingerprint(delta_fingerprint)
        session_ids = {c.get("session_id") for c in corrections if c.get("session_id")}

        existing_ids = {
            c.get("correction_id") for c in preference.get("source_corrections", [])
        }
        for c in corrections:
            if c["correction_id"] not in existing_ids:
                preference.setdefault("source_corrections", []).append({
                    "correction_id": c["correction_id"],
                    "session_id": c.get("session_id", ""),
                    "artifact_id": c.get("artifact_id", ""),
                })

        preference["evidence_count"] = len(corrections)
        preference["cross_session_count"] = len(session_ids)
        preference["updated_at"] = self._now()
        self._atomic_write(self._path(preference["preference_id"]), preference)
        return preference

    def _generate_description(self, delta_summary: dict[str, Any]) -> str:
        """Generate a human-readable Korean description from delta summary."""
        parts: list[str] = []

        replacements = delta_summary.get("replacements", [])
        if replacements:
            for r in replacements[:3]:
                fr = str(r.get("from", "")).strip()
                to = str(r.get("to", "")).strip()
                if fr and to:
                    parts.append(f"'{fr}' → '{to}'")
            if parts:
                return "교정 패턴: " + ", ".join(parts)

        additions = delta_summary.get("additions", [])
        if additions:
            added = additions[0][:30] if additions[0] else ""
            if added:
                parts.append(f"'{added}' 추가 선호")

        removals = delta_summary.get("removals", [])
        if removals:
            removed = removals[0][:30] if removals[0] else ""
            if removed:
                parts.append(f"'{removed}' 제거 선호")

        if parts:
            return "교정 패턴: " + ", ".join(parts)
        return "반복 교정 패턴"

    # -- CRUD --

    def get(self, preference_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._read(self._path(preference_id))

    def find_by_fingerprint(self, delta_fingerprint: str) -> dict[str, Any] | None:
        with self._lock:
            for r in self._scan_all():
                if r.get("delta_fingerprint") == delta_fingerprint:
                    return r
            return None

    def get_active_preferences(self) -> list[dict[str, Any]]:
        with self._lock:
            active = [
                r for r in self._scan_all()
                if r.get("status") == PreferenceStatus.ACTIVE
            ]
            return sorted(active, key=lambda d: d.get("activated_at", ""))

    def get_candidates(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                r for r in self._scan_all()
                if r.get("status") == PreferenceStatus.CANDIDATE
            ]

    # -- Lifecycle transitions --

    def _transition(self, preference_id: str, status: str, ts_field: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._read(self._path(preference_id))
            if record is None:
                return None
            now = self._now()
            record["status"] = status
            record[ts_field] = now
            record["updated_at"] = now
            self._atomic_write(self._path(preference_id), record)
            return record

    def activate_preference(self, preference_id: str) -> dict[str, Any] | None:
        return self._transition(preference_id, PreferenceStatus.ACTIVE, "activated_at")

    def pause_preference(self, preference_id: str) -> dict[str, Any] | None:
        return self._transition(preference_id, PreferenceStatus.PAUSED, "paused_at")

    def reject_preference(self, preference_id: str) -> dict[str, Any] | None:
        return self._transition(preference_id, PreferenceStatus.REJECTED, "rejected_at")

    def list_all(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            all_records = self._scan_all()
            all_records.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
            return all_records[:limit]
