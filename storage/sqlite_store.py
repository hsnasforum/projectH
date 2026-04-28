"""SQLite-backed unified storage layer.

Drop-in replacement for JSON file-based stores. Each store class wraps the
same SQLite database and exposes the same public interface as its JSON
counterpart.

Schema version is tracked in a metadata table for future migrations.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.contracts import (
    CandidateFamily,
    CORRECTION_STATUS_TRANSITIONS,
    CorrectionRecord,
    CorrectionStatus,
    PreferenceRecord,
    PreferenceStatus,
)

try:
    from storage.preference_store import (
        AUTO_ACTIVATE_CROSS_SESSION_THRESHOLD as _SQLITE_AUTO_ACTIVATE_THRESHOLD,
    )
except ImportError:
    _SQLITE_AUTO_ACTIVATE_THRESHOLD = 3

SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT PRIMARY KEY,
    title       TEXT NOT NULL DEFAULT '',
    data        TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    _version    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id      TEXT PRIMARY KEY,
    artifact_kind    TEXT NOT NULL,
    session_id       TEXT NOT NULL,
    source_message_id TEXT NOT NULL,
    data             TEXT NOT NULL DEFAULT '{}',
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_artifacts_session ON artifacts(session_id);

CREATE TABLE IF NOT EXISTS corrections (
    correction_id     TEXT PRIMARY KEY,
    artifact_id       TEXT NOT NULL,
    session_id        TEXT NOT NULL,
    delta_fingerprint TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'recorded',
    data              TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_corrections_fingerprint ON corrections(delta_fingerprint);
CREATE INDEX IF NOT EXISTS idx_corrections_session ON corrections(session_id);
CREATE INDEX IF NOT EXISTS idx_corrections_artifact ON corrections(artifact_id);

CREATE TABLE IF NOT EXISTS preferences (
    preference_id     TEXT PRIMARY KEY,
    delta_fingerprint TEXT NOT NULL UNIQUE,
    description       TEXT NOT NULL DEFAULT '',
    status            TEXT NOT NULL DEFAULT 'candidate',
    data              TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    activated_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_preferences_status ON preferences(status);

CREATE TABLE IF NOT EXISTS task_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    action     TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT '{}',
    logged_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_task_log_session ON task_log(session_id);

-- web_search_records: deferred — WebSearchStore stays JSON-based for now.
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid4().hex[:12]


class SQLiteDatabase:
    """Thread-safe SQLite connection manager using per-thread connections.

    Each thread gets its own connection via threading.local(), avoiding lock
    contention under concurrent web requests. WAL mode allows concurrent readers.
    """

    def __init__(self, db_path: str = "data/projecth.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        conn: sqlite3.Connection | None = getattr(self._local, "conn", None)
        if conn is not None:
            # Health check: verify connection is still usable
            try:
                conn.execute("SELECT 1")
                return conn
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        self._local.conn = conn
        return conn

    def _init_schema(self) -> None:
        conn = self._get_conn()
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._get_conn().execute(sql, params)

    def executemany(self, sql: str, params_list: list[tuple]) -> sqlite3.Cursor:
        return self._get_conn().executemany(sql, params_list)

    def commit(self) -> None:
        self._get_conn().commit()

    def fetchone(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        row = self._get_conn().execute(sql, params).fetchone()
        return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        rows = self._get_conn().execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        conn: sqlite3.Connection | None = getattr(self._local, "conn", None)
        if conn:
            conn.close()
            self._local.conn = None


# ── SQLite Session Store ──────────────────────────────────────────

class SQLiteSessionStore:
    """Drop-in replacement for SessionStore, backed by SQLite."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db
        self._lock = threading.RLock()

    def _now(self) -> str:
        return _now_iso()

    def _load(self, session_id: str) -> dict[str, Any]:
        row = self._db.fetchone("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        if row:
            data = json.loads(row["data"])
            data["session_id"] = row["session_id"]
            data["title"] = row["title"]
            data["created_at"] = row["created_at"]
            data["updated_at"] = row["updated_at"]
            data["_version"] = row["_version"]
            from storage.session_store import SessionStore as _SS
            _SS._backfill_active_context_summary_hint_basis(data)
            return data
        # Auto-create
        now = _now_iso()
        data = {
            "session_id": session_id,
            "title": session_id,
            "messages": [],
            "pending_approvals": [],
            "permissions": {"web_search": "disabled"},
            "active_context": None,
            "created_at": now,
            "updated_at": now,
            "_version": 0,
        }
        self._save(session_id, data)
        return data

    def _save(self, session_id: str, data: dict[str, Any]) -> None:
        now = _now_iso()
        data["updated_at"] = now
        data["_version"] = data.get("_version", 0) + 1
        title = data.get("title", session_id)
        blob = json.dumps(data, ensure_ascii=False, default=str)
        self._db.execute(
            """INSERT INTO sessions (session_id, title, data, created_at, updated_at, _version)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
                 title=excluded.title, data=excluded.data,
                 updated_at=excluded.updated_at, _version=excluded._version""",
            (session_id, title, blob, data.get("created_at", now), now, data["_version"]),
        )
        self._db.commit()

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._load(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        rows = self._db.fetchall("SELECT session_id, title, data, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
        results = []
        for row in rows:
            data = json.loads(row["data"])
            messages = data.get("messages", [])
            results.append({
                "session_id": row["session_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "message_count": len(messages),
                "pending_approval_count": len(data.get("pending_approvals", [])),
                "last_message_preview": messages[-1].get("text", "")[:80] if messages else "",
            })
        return results

    def delete_session(self, session_id: str) -> bool:
        cursor = self._db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        self._db.commit()
        return cursor.rowcount > 0

    def delete_all_sessions(self) -> int:
        cursor = self._db.execute("DELETE FROM sessions")
        self._db.commit()
        return cursor.rowcount

    def append_message(self, session_id: str, message: dict[str, Any]) -> dict[str, Any]:
        data = self._load(session_id)
        normalized_message = self._normalize_message(message)
        data.setdefault("messages", []).append(normalized_message)
        # Auto-title from first user message
        if len(data["messages"]) == 1 and normalized_message.get("role") == "user":
            data["title"] = normalized_message.get("text", "")[:40] or session_id
        self._save(session_id, data)
        return dict(normalized_message)

    def update_last_message(self, session_id: str, updates: dict[str, Any]) -> None:
        data = self._load(session_id)
        messages = data.get("messages", [])
        if messages:
            last_message = dict(messages[-1])
            last_message.update(updates)
            messages[-1] = self._normalize_message(last_message)
            self._save(session_id, data)

    def update_message(self, session_id: str, message_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        data = self._load(session_id)
        for i, msg in enumerate(data.get("messages", [])):
            if msg.get("message_id") == message_id:
                patched = dict(msg)
                patched.update(updates)
                normalized = self._normalize_message(patched)
                data["messages"][i] = normalized
                self._save(session_id, data)
                return dict(normalized)
        return None

    def add_pending_approval(self, session_id: str, approval: dict[str, Any]) -> None:
        data = self._load(session_id)
        data.setdefault("pending_approvals", []).append(approval)
        self._save(session_id, data)

    def get_pending_approval(self, session_id: str, approval_id: str) -> dict[str, Any] | None:
        data = self._load(session_id)
        for a in data.get("pending_approvals", []):
            if a.get("approval_id") == approval_id:
                return a
        return None

    def pop_pending_approval(self, session_id: str, approval_id: str) -> dict[str, Any] | None:
        data = self._load(session_id)
        approvals = data.get("pending_approvals", [])
        for i, a in enumerate(approvals):
            if a.get("approval_id") == approval_id:
                popped = approvals.pop(i)
                self._save(session_id, data)
                return popped
        return None

    def set_active_context(self, session_id: str, context: dict[str, Any] | None) -> None:
        data = self._load(session_id)
        data["active_context"] = context
        self._save(session_id, data)

    def get_active_context(self, session_id: str) -> dict[str, Any] | None:
        data = self._load(session_id)
        return data.get("active_context")

    def set_permissions(self, session_id: str, permissions: dict[str, Any]) -> None:
        data = self._load(session_id)
        data["permissions"] = permissions
        self._save(session_id, data)

    def get_permissions(self, session_id: str) -> dict[str, Any]:
        data = self._load(session_id)
        return data.get("permissions", {"web_search": "disabled"})

    # ── Data-processing parity with SessionStore ─────────────────
    # Reuse logic from the JSON SessionStore rather than maintaining
    # divergent simplified implementations.  All methods below operate
    # on the same session-dict shape; they rely on _now(), _lock,
    # get_session(), and _save() which this class provides.
    from storage.session_store import SessionStore as _SS
    # Normalization helpers
    _normalize_multiline_text = _SS._normalize_multiline_text
    _normalize_text_list = _SS._normalize_text_list
    _normalize_dict_list = _SS._normalize_dict_list
    _normalize_original_response_snapshot = _SS._normalize_original_response_snapshot
    _normalize_approval_record = _SS._normalize_approval_record
    _normalize_corrected_outcome = _SS._normalize_corrected_outcome
    _normalize_content_reason_record = _SS._normalize_content_reason_record
    _normalize_candidate_confirmation_record = _SS._normalize_candidate_confirmation_record
    _normalize_candidate_review_record = _SS._normalize_candidate_review_record
    _build_original_response_snapshot_from_message = _SS._build_original_response_snapshot_from_message
    _build_artifact_source_message_ids = _SS._build_artifact_source_message_ids
    _find_artifact_source_message_in_messages = _SS._find_artifact_source_message_in_messages
    _normalize_source_message_anchor = _SS._normalize_source_message_anchor
    _is_matching_anchor = _SS._is_matching_anchor
    _latest_approval_reason_record_for_anchor = _SS._latest_approval_reason_record_for_anchor
    _latest_save_signal_for_anchor = _SS._latest_save_signal_for_anchor
    _normalize_message = _SS._normalize_message
    _current_correctable_text = _SS._current_correctable_text
    _compact_summary_hint_for_persist = staticmethod(_SS._compact_summary_hint_for_persist)
    # Public session-data methods
    build_session_local_memory_signal = _SS.build_session_local_memory_signal
    find_artifact_source_message = _SS.find_artifact_source_message
    record_correction_for_message = _SS.record_correction_for_message
    record_corrected_outcome_for_artifact = _SS.record_corrected_outcome_for_artifact
    record_candidate_confirmation_for_message = _SS.record_candidate_confirmation_for_message
    record_candidate_review_for_message = _SS.record_candidate_review_for_message
    record_rejected_content_verdict_for_message = _SS.record_rejected_content_verdict_for_message
    record_content_reason_note_for_message = _SS.record_content_reason_note_for_message
    add_pending_approval = _SS.add_pending_approval
    del _SS


# ── SQLite Task Logger ────────────────────────────────────────────

class SQLiteTaskLogger:
    """Drop-in replacement for TaskLogger, backed by SQLite."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def log(self, *, session_id: str, action: str, detail: dict[str, Any]) -> None:
        self._db.execute(
            "INSERT INTO task_log (session_id, action, detail, logged_at) VALUES (?, ?, ?, ?)",
            (session_id, action, json.dumps(detail, ensure_ascii=False, default=str), _now_iso()),
        )
        self._db.commit()

    def iter_session_records(self, session_id: str) -> list[dict[str, Any]]:
        normalized = (session_id or "").strip() or None
        if normalized is None:
            return []
        rows = self._db.execute(
            "SELECT session_id, action, detail, logged_at FROM task_log WHERE session_id = ? ORDER BY rowid",
            (normalized,),
        ).fetchall()
        records: list[dict[str, Any]] = []
        for row in rows:
            detail = row[2]
            try:
                parsed_detail = json.loads(detail) if isinstance(detail, str) else detail
            except (json.JSONDecodeError, TypeError):
                parsed_detail = {}
            records.append({
                "session_id": row[0],
                "action": row[1],
                "detail": parsed_detail,
                "ts": row[3],
            })
        return records


# ── SQLite Artifact Store ─────────────────────────────────────────

class SQLiteArtifactStore:
    """Drop-in replacement for ArtifactStore, backed by SQLite."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def create(self, *, artifact_id: str, artifact_kind: str, session_id: str,
               source_message_id: str, draft_text: str, source_paths: list[str] | None = None,
               response_origin: dict[str, Any] | None = None,
               summary_chunks: list[dict[str, Any]] | None = None,
               evidence: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        now = _now_iso()
        data = {
            "draft_text": draft_text,
            "source_paths": source_paths or [],
            "response_origin": response_origin,
            "summary_chunks": summary_chunks or [],
            "evidence": evidence or [],
            "corrections": [],
            "saves": [],
            "outcome": None,
        }
        self._db.execute(
            "INSERT INTO artifacts (artifact_id, artifact_kind, session_id, source_message_id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (artifact_id, artifact_kind, session_id, source_message_id, json.dumps(data, ensure_ascii=False, default=str), now, now),
        )
        self._db.commit()
        return {"artifact_id": artifact_id, "artifact_kind": artifact_kind, "session_id": session_id, **data, "created_at": now}

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        row = self._db.fetchone("SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,))
        if not row:
            return None
        data = json.loads(row["data"])
        data.update({"artifact_id": row["artifact_id"], "artifact_kind": row["artifact_kind"], "session_id": row["session_id"], "created_at": row["created_at"], "updated_at": row["updated_at"]})
        return data

    def list_by_session(self, session_id: str) -> list[dict[str, Any]]:
        rows = self._db.fetchall("SELECT * FROM artifacts WHERE session_id = ? ORDER BY created_at DESC", (session_id,))
        return [{"artifact_id": r["artifact_id"], **json.loads(r["data"]), "created_at": r["created_at"]} for r in rows]

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._db.fetchall("SELECT * FROM artifacts ORDER BY created_at DESC LIMIT ?", (limit,))
        return [{"artifact_id": r["artifact_id"], **json.loads(r["data"]), "created_at": r["created_at"]} for r in rows]


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
        return [{"preference_id": r["preference_id"], "description": r["description"], "status": r["status"], **json.loads(r["data"])} for r in rows]

    def list_all(self, limit: int = 50) -> list[PreferenceRecord]:
        rows = self._db.fetchall("SELECT * FROM preferences ORDER BY updated_at DESC LIMIT ?", (limit,))
        results = []
        for r in rows:
            data = json.loads(r["data"])
            data.update({"preference_id": r["preference_id"], "description": r["description"], "status": r["status"], "delta_fingerprint": r["delta_fingerprint"], "created_at": r["created_at"], "updated_at": r["updated_at"], "activated_at": r["activated_at"]})
            results.append(data)
        return results

    def activate_preference(self, preference_id: str) -> PreferenceRecord | None:
        return self._update_status(preference_id, "active")

    def pause_preference(self, preference_id: str) -> PreferenceRecord | None:
        return self._update_status(preference_id, "paused")

    def reject_preference(self, preference_id: str) -> PreferenceRecord | None:
        return self._update_status(preference_id, "rejected")

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


# ── SQLite Correction Store ───────────────────────────────────────

class SQLiteCorrectionStore:
    """Core CorrectionStore lookup parity, backed by SQLite."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db
        self._lock = threading.RLock()

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
    ) -> CorrectionRecord | None:
        """Record a correction and compute its delta. Returns None if no delta."""
        from core.delta_analysis import compute_correction_delta

        delta = compute_correction_delta(original_text, corrected_text)
        if delta is None:
            return None

        with self._lock:
            duplicate_rows = self._db.fetchall(
                "SELECT * FROM corrections WHERE delta_fingerprint = ? AND artifact_id = ? AND session_id = ?",
                (delta.delta_fingerprint, artifact_id, session_id),
            )
            for row in duplicate_rows:
                existing = self._row_to_dict(row)
                if existing.get("source_message_id") == source_message_id:
                    return existing

            existing_rows = self._db.fetchall(
                "SELECT * FROM corrections WHERE delta_fingerprint = ? ORDER BY created_at",
                (delta.delta_fingerprint,),
            )
            recurrence_count = len(existing_rows) + 1
            now = _now_iso()

            for row in existing_rows:
                existing = self._row_to_dict(row)
                existing["recurrence_count"] = recurrence_count
                existing["last_seen_at"] = now
                existing["updated_at"] = now
                self._db.execute(
                    "UPDATE corrections SET data = ?, updated_at = ? WHERE correction_id = ?",
                    (
                        json.dumps(existing, ensure_ascii=False, default=str),
                        now,
                        row["correction_id"],
                    ),
                )

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
            self._db.execute(
                "INSERT INTO corrections "
                "(correction_id, artifact_id, session_id, delta_fingerprint, status, data, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    correction_id,
                    artifact_id,
                    session_id,
                    delta.delta_fingerprint,
                    record["status"],
                    json.dumps(record, ensure_ascii=False, default=str),
                    record["created_at"],
                    record["updated_at"],
                ),
            )
            self._db.commit()
            return record

    def get(self, correction_id: str) -> CorrectionRecord | None:
        row = self._db.fetchone("SELECT * FROM corrections WHERE correction_id = ?", (correction_id,))
        if not row:
            return None
        return self._row_to_dict(row)

    def find_by_fingerprint(self, delta_fingerprint: str) -> list[CorrectionRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM corrections WHERE delta_fingerprint = ? ORDER BY created_at",
            (delta_fingerprint,),
        )
        return [self._row_to_dict(row) for row in rows]

    def find_by_artifact(self, artifact_id: str) -> list[CorrectionRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM corrections WHERE artifact_id = ? ORDER BY created_at",
            (artifact_id,),
        )
        return [self._row_to_dict(row) for row in rows]

    def find_by_session(self, session_id: str) -> list[CorrectionRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM corrections WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        )
        return [self._row_to_dict(row) for row in rows]

    def list_recent(self, limit: int = 20) -> list[CorrectionRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM corrections ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_dict(row) for row in rows]

    def list_incomplete_corrections(self) -> list[CorrectionRecord]:
        with self._lock:
            rows = self._db.fetchall(
                "SELECT * FROM corrections WHERE status IN (?, ?, ?) ORDER BY created_at ASC",
                (
                    CorrectionStatus.RECORDED,
                    CorrectionStatus.CONFIRMED,
                    CorrectionStatus.PROMOTED,
                ),
            )
            return [self._row_to_dict(row) for row in rows]

    def find_adopted_corrections(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._db.fetchall(
                "SELECT * FROM corrections WHERE status = ?",
                (CorrectionStatus.ACTIVE,),
            )
            records = [self._row_to_dict(row) for row in rows]
            records.sort(key=lambda r: r.get("activated_at") or "")
            return records

    def find_recurring_patterns(self, *, session_id: str | None = None) -> list[dict[str, Any]]:
        """Return correction groups with recurrence_count >= 2, matching CorrectionStore contract."""
        if session_id:
            fp_rows = self._db.fetchall(
                "SELECT delta_fingerprint FROM corrections WHERE session_id = ? "
                "GROUP BY delta_fingerprint HAVING COUNT(*) >= 2",
                (session_id,),
            )
        else:
            fp_rows = self._db.fetchall(
                "SELECT delta_fingerprint FROM corrections "
                "GROUP BY delta_fingerprint HAVING COUNT(DISTINCT session_id) >= 2"
            )

        patterns: list[dict[str, Any]] = []
        for fp_row in fp_rows:
            fp = fp_row["delta_fingerprint"]
            if not fp:
                continue
            if session_id:
                rows = self._db.fetchall(
                    "SELECT * FROM corrections WHERE delta_fingerprint = ? AND session_id = ? "
                    "ORDER BY created_at",
                    (fp, session_id),
                )
            else:
                rows = self._db.fetchall(
                    "SELECT * FROM corrections WHERE delta_fingerprint = ? ORDER BY created_at",
                    (fp,),
                )
            records = [self._row_to_dict(row) for row in rows]
            if len(records) < 2:
                continue
            patterns.append({
                "delta_fingerprint": fp,
                "pattern_family": records[0].get("pattern_family", ""),
                "recurrence_count": len(records),
                "corrections": records,
                "first_seen_at": min(
                    (record.get("first_seen_at") or record.get("created_at") or "")
                    for record in records
                ),
                "last_seen_at": max(
                    (record.get("last_seen_at") or record.get("updated_at") or "")
                    for record in records
                ),
            })
        return patterns

    def _row_to_dict(self, row: dict[str, Any]) -> dict[str, Any]:
        data = json.loads(row["data"]) if isinstance(row.get("data"), str) else {}
        data.update({
            "correction_id": row["correction_id"],
            "artifact_id": row["artifact_id"],
            "session_id": row["session_id"],
            "delta_fingerprint": row["delta_fingerprint"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        })
        return data

    def _transition(self, correction_id: str, status: str, timestamp_field: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.fetchone("SELECT * FROM corrections WHERE correction_id = ?", (correction_id,))
            if not row:
                return None
            record = self._row_to_dict(row)
            current_status = record.get("status")
            allowed = CORRECTION_STATUS_TRANSITIONS.get(current_status, ())
            if status not in allowed:
                return None
            now = _now_iso()
            record["status"] = status
            record[timestamp_field] = now
            record["updated_at"] = now
            self._db.execute(
                "UPDATE corrections SET status = ?, data = ?, updated_at = ? WHERE correction_id = ?",
                (
                    status,
                    json.dumps(record, ensure_ascii=False, default=str),
                    now,
                    correction_id,
                ),
            )
            self._db.commit()
            return record

    def confirm_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.CONFIRMED, "confirmed_at")

    def promote_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.PROMOTED, "promoted_at")

    def activate_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.ACTIVE, "activated_at")

    def stop_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.STOPPED, "stopped_at")


# ── Migration utility ─────────────────────────────────────────────

def migrate_json_to_sqlite(
    *,
    sessions_dir: str | None = "data/sessions",
    artifacts_dir: str | None = "data/artifacts",
    corrections_dir: str = "data/corrections",
    preferences_dir: str | None = "data/preferences",
    db_path: str = "data/projecth.db",
) -> dict[str, int]:
    """Migrate JSON file stores to SQLite. Returns counts per table.

    Pass None for an optional directory to skip that table family.
    """
    db = SQLiteDatabase(db_path)
    counts: dict[str, int] = {}
    errors: list[str] = []

    # Corrections
    corrections_path = Path(corrections_dir)
    count = 0
    if corrections_path.is_dir():
        for f in corrections_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                now = data.get("created_at", _now_iso())
                cursor = db.execute(
                    "INSERT OR IGNORE INTO corrections "
                    "(correction_id, artifact_id, session_id, delta_fingerprint, status, data, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        data["correction_id"],
                        data.get("artifact_id", ""),
                        data.get("session_id", ""),
                        data.get("delta_fingerprint", ""),
                        data.get("status", "recorded"),
                        json.dumps(data, ensure_ascii=False, default=str),
                        now,
                        data.get("updated_at", now),
                    ),
                )
                count += max(cursor.rowcount, 0)
            except Exception as exc:
                errors.append(f"correction {f.name}: {exc}")
                continue
    db.commit()
    counts["corrections"] = count

    # Sessions
    count = 0
    if sessions_dir is not None and (sessions_path := Path(sessions_dir)).is_dir():
        for f in sessions_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sid = data.get("session_id", f.stem)
                store = SQLiteSessionStore(db)
                store._save(sid, data)
                count += 1
            except Exception as exc:
                errors.append(f"session {f.name}: {exc}")
                continue
    counts["sessions"] = count

    # Artifacts
    count = 0
    if artifacts_dir is not None and (artifacts_path := Path(artifacts_dir)).is_dir():
        for f in artifacts_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                now = data.get("created_at", _now_iso())
                db.execute(
                    "INSERT OR IGNORE INTO artifacts (artifact_id, artifact_kind, session_id, source_message_id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (data["artifact_id"], data.get("artifact_kind", "grounded_brief"), data.get("session_id", ""), data.get("source_message_id", ""), json.dumps(data, ensure_ascii=False, default=str), now, now),
                )
                count += 1
            except Exception as exc:
                errors.append(f"artifact {f.name}: {exc}")
                continue
    db.commit()
    counts["artifacts"] = count

    # Preferences
    count = 0
    if preferences_dir is not None and (prefs_path := Path(preferences_dir)).is_dir():
        for f in prefs_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                now = data.get("created_at", _now_iso())
                db.execute(
                    "INSERT OR IGNORE INTO preferences (preference_id, delta_fingerprint, description, status, data, created_at, updated_at, activated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (data["preference_id"], data.get("delta_fingerprint", ""), data.get("description", ""), data.get("status", "candidate"), json.dumps(data, ensure_ascii=False, default=str), now, now, data.get("activated_at")),
                )
                count += 1
            except Exception as exc:
                errors.append(f"preference {f.name}: {exc}")
                continue
    db.commit()
    counts["preferences"] = count

    if errors:
        counts["_errors"] = errors  # type: ignore[assignment]

    db.close()
    return counts
