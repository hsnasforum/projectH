"""SQLite-backed preference store."""

from __future__ import annotations

import json
from typing import Any

from core.contracts import PreferenceRecord, PreferenceStatus
from storage.preference_store import (
    _is_valid_preference_record,
)
from storage.sqlite.database import SQLiteDatabase, _new_id, _now_iso

try:
    from storage.preference_store import (
        AUTO_ACTIVATE_CROSS_SESSION_THRESHOLD as _SQLITE_AUTO_ACTIVATE_THRESHOLD,
    )
except ImportError:
    _SQLITE_AUTO_ACTIVATE_THRESHOLD = 3


# ── SQLite Preference Store ───────────────────────────────────────

class SQLitePreferenceStore:
    """Drop-in replacement for PreferenceStore, backed by SQLite."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def get(self, preference_id: str) -> PreferenceRecord | None:
        row = self._db.fetchone("SELECT * FROM preferences WHERE preference_id = ?", (preference_id,))
        if not row:
            return None
        data = json.loads(row["data"])
        data.update({"preference_id": row["preference_id"], "description": row["description"], "status": row["status"], "created_at": row["created_at"], "updated_at": row["updated_at"], "activated_at": row["activated_at"]})
        return data

    def get_active_preferences(self) -> list[PreferenceRecord]:
        rows = self._db.fetchall("SELECT * FROM preferences WHERE status = 'active' ORDER BY activated_at DESC LIMIT 10")
        return [
            record
            for record in (
                {
                    "preference_id": r["preference_id"],
                    "description": r["description"],
                    "status": r["status"],
                    **json.loads(r["data"]),
                }
                for r in rows
            )
            if _is_valid_preference_record(record)
        ]

    def _record_from_row(self, row: dict[str, Any]) -> PreferenceRecord | None:
        data = json.loads(row["data"])
        data.update({
            "preference_id": row["preference_id"],
            "description": row["description"],
            "status": row["status"],
            "delta_fingerprint": row["delta_fingerprint"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "activated_at": row["activated_at"],
        })
        return data if _is_valid_preference_record(data) else None

    def get_candidates(self, limit: int = 50) -> list[PreferenceRecord]:
        """Return candidate preferences, most recently updated first."""
        rows = self._db.fetchall(
            "SELECT * FROM preferences WHERE status = 'candidate' ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        )
        results = []
        for row in rows:
            record = self._record_from_row(row)
            if record is not None:
                results.append(record)
        return results

    def find_by_fingerprint(self, delta_fingerprint: str) -> PreferenceRecord | None:
        """Return the preference matching delta_fingerprint, or None."""
        row = self._db.fetchone(
            "SELECT * FROM preferences WHERE delta_fingerprint = ?",
            (delta_fingerprint,),
        )
        if row is None:
            return None
        return self._record_from_row(row)

    def list_all(self, limit: int = 50, offset: int = 0) -> list[PreferenceRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM preferences ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (max(0, limit), max(0, offset)),
        )
        results = []
        for r in rows:
            record = self._record_from_row(r)
            if record is not None:
                results.append(record)
        return results

    def activate_preference(self, preference_id: str) -> PreferenceRecord | None:
        now = _now_iso()
        row = self._db.fetchone(
            "SELECT * FROM preferences WHERE preference_id = ?",
            (preference_id,),
        )
        if row is None:
            return None
        data = json.loads(row["data"])
        data["is_highly_reliable"] = True
        data["status"] = "active"
        data["activated_at"] = now
        data["updated_at"] = now
        self._db.execute(
            "UPDATE preferences SET status = ?, updated_at = ?, activated_at = ?, data = ? WHERE preference_id = ?",
            (
                "active",
                now,
                now,
                json.dumps(data, ensure_ascii=False, default=str),
                preference_id,
            ),
        )
        self._db.commit()
        return self.get(preference_id)

    def pause_preference(self, preference_id: str) -> PreferenceRecord | None:
        return self._update_status(preference_id, "paused")

    def reject_preference(self, preference_id: str) -> PreferenceRecord | None:
        return self._update_status(preference_id, "rejected")

    def delete(self, preference_id: str) -> PreferenceRecord | None:
        row = self._db.fetchone("SELECT * FROM preferences WHERE preference_id = ?", (preference_id,))
        if row is None:
            return None
        record = self._record_from_row(row)
        self._db.execute("DELETE FROM preferences WHERE preference_id = ?", (preference_id,))
        self._db.commit()
        return record

    def update(self, preference_id: str, updates: dict[str, Any]) -> PreferenceRecord | None:
        row = self._db.fetchone("SELECT * FROM preferences WHERE preference_id = ?", (preference_id,))
        if row is None:
            return None
        now = _now_iso()
        data = json.loads(row["data"])
        data.update(updates)
        data["preference_id"] = preference_id
        data.setdefault("delta_fingerprint", row["delta_fingerprint"])
        data.setdefault("created_at", row["created_at"])
        data.setdefault("activated_at", row["activated_at"])
        data["description"] = str(data.get("description", row["description"]) or "")
        data["status"] = str(data.get("status", row["status"]) or row["status"])
        data["updated_at"] = now
        self._db.execute(
            "UPDATE preferences SET description = ?, status = ?, activated_at = ?, data = ?, updated_at = ? WHERE preference_id = ?",
            (
                data["description"],
                data["status"],
                data.get("activated_at"),
                json.dumps(data, ensure_ascii=False, default=str),
                now,
                preference_id,
            ),
        )
        self._db.commit()
        return self.get(preference_id)

    def update_description(self, preference_id: str, description: str) -> PreferenceRecord | None:
        """Update the description of an existing preference. Returns None if not found."""
        now = _now_iso()
        row = self._db.fetchone("SELECT * FROM preferences WHERE preference_id = ?", (preference_id,))
        if not row:
            return None
        data = json.loads(row["data"])
        data["description"] = description
        data["updated_at"] = now
        self._db.execute(
            "UPDATE preferences SET description = ?, data = ?, updated_at = ? WHERE preference_id = ?",
            (description, json.dumps(data, ensure_ascii=False, default=str), now, preference_id),
        )
        self._db.commit()
        return self.get(preference_id)

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
        status: str | None = None,
        initial_reliability_stats: dict[str, Any] | None = None,
    ) -> PreferenceRecord:
        """Persist one local preference candidate from an accepted reviewed candidate."""
        row = self._db.fetchone(
            "SELECT * FROM preferences WHERE delta_fingerprint = ?", (delta_fingerprint,)
        )
        now = _now_iso()
        if row:
            data = json.loads(row["data"])
            data.update({
                "preference_id": row["preference_id"],
                "description": row["description"],
                "status": row["status"],
                "delta_fingerprint": row["delta_fingerprint"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "activated_at": row["activated_at"],
            })
            data.setdefault("reviewed_candidate_source_refs", [])
            existing_ref_ids = {
                str(ref.get("candidate_id") or "")
                for ref in data["reviewed_candidate_source_refs"]
                if isinstance(ref, dict)
            }
            if str(source_refs.get("candidate_id") or "") not in existing_ref_ids:
                data["reviewed_candidate_source_refs"].append(source_refs)
                try:
                    cross_session_count = int(data.get("cross_session_count") or 0)
                except (TypeError, ValueError):
                    cross_session_count = 0
                data["cross_session_count"] = cross_session_count + 1
            if avg_similarity_score is not None:
                data["avg_similarity_score"] = avg_similarity_score
            if original_snippet is not None:
                data["original_snippet"] = original_snippet
            if corrected_snippet is not None:
                data["corrected_snippet"] = corrected_snippet
            if status is not None and data.get("status") != status:
                data["status"] = status
                if status == PreferenceStatus.REJECTED:
                    data["rejected_at"] = now
            data["updated_at"] = now
            self._auto_activate_candidate_if_ready(data, now)
            blob = json.dumps(data, ensure_ascii=False, default=str)
            self._db.execute(
                "UPDATE preferences SET status = ?, activated_at = ?, data = ?, updated_at = ? WHERE preference_id = ?",
                (
                    data.get("status", row["status"]),
                    data.get("activated_at"),
                    blob,
                    data.get("updated_at", now),
                    data["preference_id"],
                ),
            )
            self._db.commit()
            return data

        preference_id = f"pref-{_new_id()}"
        data: dict[str, Any] = {
            "preference_id": preference_id,
            "delta_fingerprint": delta_fingerprint,
            "pattern_family": candidate_family,
            "description": description,
            "source_corrections": [],
            "reviewed_candidate_source_refs": [source_refs],
            "evidence_count": 1,
            "cross_session_count": 0,
            "avg_similarity_score": avg_similarity_score,
            "reliability_stats": (
                dict(initial_reliability_stats)
                if initial_reliability_stats
                else {"applied_count": 0, "corrected_count": 0}
            ),
            "original_snippet": original_snippet,
            "corrected_snippet": corrected_snippet,
            "delta_summary": {},
            "status": status if status is not None else "candidate",
            "activated_at": None,
            "paused_at": None,
            "rejected_at": now if status == PreferenceStatus.REJECTED else None,
            "created_at": now,
            "updated_at": now,
        }
        self._auto_activate_candidate_if_ready(data, now)
        blob = json.dumps(data, ensure_ascii=False, default=str)
        self._db.execute(
            "INSERT INTO preferences (preference_id, delta_fingerprint, description, status, data, created_at, updated_at, activated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                preference_id,
                delta_fingerprint,
                description,
                data["status"],
                blob,
                data["created_at"],
                data["updated_at"],
                data["activated_at"],
            ),
        )
        self._db.commit()
        return data

    def _auto_activate_candidate_if_ready(self, preference: dict[str, Any], now: str) -> None:
        if preference.get("status") != "candidate":
            return
        try:
            cross_session_count = int(preference.get("cross_session_count") or 0)
        except (TypeError, ValueError):
            return
        if cross_session_count < _SQLITE_AUTO_ACTIVATE_THRESHOLD:
            return

        preference["status"] = "active"
        preference["activated_at"] = now
        preference["updated_at"] = now
        blob = json.dumps(preference, ensure_ascii=False, default=str)
        self._db.execute(
            "UPDATE preferences SET status = ?, activated_at = ?, data = ?, updated_at = ? WHERE preference_id = ?",
            ("active", now, blob, now, preference["preference_id"]),
        )

    def _update_status(self, preference_id: str, new_status: str) -> PreferenceRecord | None:
        now = _now_iso()
        activated = now if new_status == "active" else None
        cursor = self._db.execute(
            "UPDATE preferences SET status = ?, updated_at = ?, activated_at = COALESCE(?, activated_at) WHERE preference_id = ?",
            (new_status, now, activated, preference_id),
        )
        self._db.commit()
        if cursor.rowcount == 0:
            return None
        return self.get(preference_id)
