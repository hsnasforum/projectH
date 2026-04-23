"""Cross-session preference memory store.

Persists durable user preferences derived from recurring correction patterns.
Unlike session-scoped reviewed_memory, these persist across sessions and
influence all future responses.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from core.contracts import CandidateFamily, PreferenceStatus

from .json_store_base import utc_now_iso, json_path, atomic_write, read_json, scan_json_dir

if TYPE_CHECKING:
    from storage.correction_store import CorrectionStore


AUTO_ACTIVATE_CROSS_SESSION_THRESHOLD = 3


def _average_similarity_score(corrections: list[dict[str, Any]]) -> float | None:
    scores = [
        float(c["similarity_score"])
        for c in corrections
        if isinstance(c.get("similarity_score"), (int, float))
    ]
    return round(sum(scores) / len(scores), 4) if scores else None


def _first_correction_snippets(corrections: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for correction in corrections:
        original_text = correction.get("original_text") or ""
        corrected_text = correction.get("corrected_text") or ""
        if original_text and corrected_text:
            return str(original_text)[:400], str(corrected_text)[:400]
    return None, None


class PreferenceStore:
    def __init__(self, base_dir: str = "data/preferences") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, preference_id: str) -> Path:
        return json_path(self.base_dir, preference_id)

    def _scan_all(self) -> list[dict[str, Any]]:
        return [d for d in scan_json_dir(self.base_dir) if isinstance(d.get("preference_id"), str)]

    # -- Core operations --

    def promote_from_corrections(
        self,
        delta_fingerprint: str,
        correction_store: CorrectionStore,
    ) -> dict[str, Any] | None:
        with self._lock:
            existing = self.find_by_fingerprint(delta_fingerprint)
            if existing is not None:
                return self._refresh_evidence(existing, delta_fingerprint, correction_store)

            corrections = correction_store.find_by_fingerprint(delta_fingerprint)
            if len(corrections) < 2:
                return None

            session_ids = {c.get("session_id") for c in corrections if c.get("session_id")}
            if len(session_ids) < 2:
                return None

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
            avg_similarity_score = _average_similarity_score(corrections)
            original_snippet, corrected_snippet = _first_correction_snippets(corrections)

            now = utc_now_iso()
            preference_id = f"pref-{uuid4().hex[:12]}"
            record: dict[str, Any] = {
                "preference_id": preference_id,
                "delta_fingerprint": delta_fingerprint,
                "pattern_family": corrections[0].get("pattern_family", CandidateFamily.CORRECTION_REWRITE),
                "description": description,
                "source_corrections": source_corrections,
                "evidence_count": len(corrections),
                "cross_session_count": len(session_ids),
                "avg_similarity_score": avg_similarity_score,
                "original_snippet": original_snippet,
                "corrected_snippet": corrected_snippet,
                "delta_summary": delta_summary,
                "status": PreferenceStatus.CANDIDATE,
                "activated_at": None,
                "paused_at": None,
                "rejected_at": None,
                "created_at": now,
                "updated_at": now,
            }
            self._auto_activate_candidate_if_ready(record, now)
            atomic_write(self._path(preference_id), record)
            return record

    def _refresh_evidence(
        self,
        preference: dict[str, Any],
        delta_fingerprint: str,
        correction_store: CorrectionStore,
    ) -> dict[str, Any]:
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
        preference["avg_similarity_score"] = _average_similarity_score(corrections)
        original_snippet, corrected_snippet = _first_correction_snippets(corrections)
        if original_snippet is not None:
            preference["original_snippet"] = original_snippet
        if corrected_snippet is not None:
            preference["corrected_snippet"] = corrected_snippet
        now = utc_now_iso()
        preference["updated_at"] = now
        self._auto_activate_candidate_if_ready(preference, now)
        atomic_write(self._path(preference["preference_id"]), preference)
        return preference

    def _auto_activate_candidate_if_ready(self, preference: dict[str, Any], now: str) -> None:
        if preference.get("status") != PreferenceStatus.CANDIDATE:
            return
        try:
            cross_session_count = int(preference.get("cross_session_count") or 0)
        except (TypeError, ValueError):
            return
        if cross_session_count < AUTO_ACTIVATE_CROSS_SESSION_THRESHOLD:
            return
        preference["status"] = PreferenceStatus.ACTIVE
        preference["activated_at"] = now
        preference["updated_at"] = now

    def _generate_description(self, delta_summary: dict[str, Any]) -> str:
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
            return read_json(self._path(preference_id))

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
            record = read_json(self._path(preference_id))
            if record is None:
                return None
            now = utc_now_iso()
            record["status"] = status
            record[ts_field] = now
            record["updated_at"] = now
            atomic_write(self._path(preference_id), record)
            return record

    def activate_preference(self, preference_id: str) -> dict[str, Any] | None:
        return self._transition(preference_id, PreferenceStatus.ACTIVE, "activated_at")

    def pause_preference(self, preference_id: str) -> dict[str, Any] | None:
        return self._transition(preference_id, PreferenceStatus.PAUSED, "paused_at")

    def reject_preference(self, preference_id: str) -> dict[str, Any] | None:
        return self._transition(preference_id, PreferenceStatus.REJECTED, "rejected_at")

    def record_reviewed_candidate_preference(
        self,
        *,
        delta_fingerprint: str,
        candidate_family: str,
        description: str,
        source_refs: dict[str, Any],
        avg_similarity_score: float | None = None,
        original_snippet: str | None = None,
        corrected_snippet: str | None = None,
    ) -> dict[str, Any]:
        """Persist one local preference candidate from an accepted reviewed candidate.

        Idempotent on *delta_fingerprint*: refreshes timestamps and source_refs
        instead of creating a duplicate record.
        """
        with self._lock:
            existing = self.find_by_fingerprint(delta_fingerprint)
            if existing is not None:
                now = utc_now_iso()
                existing["updated_at"] = now
                existing.setdefault("reviewed_candidate_source_refs", [])
                existing_ref_ids = {
                    str(ref.get("candidate_id") or "")
                    for ref in existing["reviewed_candidate_source_refs"]
                    if isinstance(ref, dict)
                }
                if str(source_refs.get("candidate_id") or "") not in existing_ref_ids:
                    existing["reviewed_candidate_source_refs"].append(source_refs)
                if avg_similarity_score is not None:
                    existing["avg_similarity_score"] = avg_similarity_score
                if original_snippet is not None:
                    existing["original_snippet"] = original_snippet
                if corrected_snippet is not None:
                    existing["corrected_snippet"] = corrected_snippet
                atomic_write(self._path(existing["preference_id"]), existing)
                return existing

            now = utc_now_iso()
            preference_id = f"pref-{uuid4().hex[:12]}"
            record: dict[str, Any] = {
                "preference_id": preference_id,
                "delta_fingerprint": delta_fingerprint,
                "pattern_family": candidate_family,
                "description": description,
                "source_corrections": [],
                "reviewed_candidate_source_refs": [source_refs],
                "evidence_count": 1,
                "cross_session_count": 0,
                "avg_similarity_score": avg_similarity_score,
                "original_snippet": original_snippet,
                "corrected_snippet": corrected_snippet,
                "delta_summary": {},
                "status": PreferenceStatus.CANDIDATE,
                "activated_at": None,
                "paused_at": None,
                "rejected_at": None,
                "created_at": now,
                "updated_at": now,
            }
            atomic_write(self._path(preference_id), record)
            return record

    def list_all(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            all_records = self._scan_all()
            all_records.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
            return all_records[:limit]
