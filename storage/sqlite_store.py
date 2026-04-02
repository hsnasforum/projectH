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

CREATE TABLE IF NOT EXISTS web_search_records (
    record_id   TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    query       TEXT NOT NULL,
    data        TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_web_search_session ON web_search_records(session_id);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid4().hex[:12]


class SQLiteDatabase:
    """Shared SQLite connection manager with thread-safe access."""

    def __init__(self, db_path: str = "data/projecth.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_schema(self) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.executescript(_SCHEMA_SQL)
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )
            conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._get_conn().execute(sql, params)

    def executemany(self, sql: str, params_list: list[tuple]) -> sqlite3.Cursor:
        with self._lock:
            return self._get_conn().executemany(sql, params_list)

    def commit(self) -> None:
        with self._lock:
            self._get_conn().commit()

    def fetchone(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        with self._lock:
            row = self._get_conn().execute(sql, params).fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._get_conn().execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None


# ── SQLite Session Store ──────────────────────────────────────────

class SQLiteSessionStore:
    """Drop-in replacement for SessionStore, backed by SQLite."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def _load(self, session_id: str) -> dict[str, Any]:
        row = self._db.fetchone("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        if row:
            data = json.loads(row["data"])
            data["session_id"] = row["session_id"]
            data["title"] = row["title"]
            data["created_at"] = row["created_at"]
            data["updated_at"] = row["updated_at"]
            data["_version"] = row["_version"]
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
        if "message_id" not in message:
            message["message_id"] = f"msg-{_new_id()}"
        if "timestamp" not in message:
            message["timestamp"] = _now_iso()
        data.setdefault("messages", []).append(message)
        # Auto-title from first user message
        if len(data["messages"]) == 1 and message.get("role") == "user":
            data["title"] = message.get("text", "")[:40] or session_id
        self._save(session_id, data)
        return message

    def update_last_message(self, session_id: str, updates: dict[str, Any]) -> None:
        data = self._load(session_id)
        messages = data.get("messages", [])
        if messages:
            messages[-1].update(updates)
            self._save(session_id, data)

    def update_message(self, session_id: str, message_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        data = self._load(session_id)
        for msg in data.get("messages", []):
            if msg.get("message_id") == message_id:
                msg.update(updates)
                self._save(session_id, data)
                return msg
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

    # Passthrough methods that delegate to the full data blob
    def find_artifact_source_message(self, session_id: str, artifact_id: str) -> dict[str, Any] | None:
        data = self._load(session_id)
        for msg in data.get("messages", []):
            if msg.get("artifact_id") == artifact_id:
                return msg
        return None

    def record_correction_for_message(self, session_id: str, *, message_id: str, corrected_text: str) -> dict[str, Any] | None:
        return self.update_message(session_id, message_id, {"corrected_text": corrected_text})

    def record_corrected_outcome_for_artifact(self, session_id: str, *, artifact_id: str | None, outcome: str, approval_id: str | None = None, saved_note_path: str | None = None, preserve_existing: bool = False) -> dict[str, Any] | None:
        data = self._load(session_id)
        for msg in data.get("messages", []):
            if msg.get("artifact_id") == artifact_id:
                if preserve_existing and msg.get("corrected_outcome"):
                    return msg
                msg["corrected_outcome"] = {"outcome": outcome, "approval_id": approval_id, "saved_note_path": saved_note_path}
                self._save(session_id, data)
                return msg
        return None


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

    def get(self, preference_id: str) -> dict[str, Any] | None:
        row = self._db.fetchone("SELECT * FROM preferences WHERE preference_id = ?", (preference_id,))
        if not row:
            return None
        data = json.loads(row["data"])
        data.update({"preference_id": row["preference_id"], "description": row["description"], "status": row["status"], "created_at": row["created_at"], "updated_at": row["updated_at"], "activated_at": row["activated_at"]})
        return data

    def get_active_preferences(self) -> list[dict[str, Any]]:
        rows = self._db.fetchall("SELECT * FROM preferences WHERE status = 'active' ORDER BY activated_at DESC LIMIT 10")
        return [{"preference_id": r["preference_id"], "description": r["description"], "status": r["status"], **json.loads(r["data"])} for r in rows]

    def list_all(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._db.fetchall("SELECT * FROM preferences ORDER BY updated_at DESC LIMIT ?", (limit,))
        results = []
        for r in rows:
            data = json.loads(r["data"])
            data.update({"preference_id": r["preference_id"], "description": r["description"], "status": r["status"], "delta_fingerprint": r["delta_fingerprint"], "created_at": r["created_at"], "updated_at": r["updated_at"], "activated_at": r["activated_at"]})
            results.append(data)
        return results

    def activate_preference(self, preference_id: str) -> dict[str, Any] | None:
        return self._update_status(preference_id, "active")

    def pause_preference(self, preference_id: str) -> dict[str, Any] | None:
        return self._update_status(preference_id, "paused")

    def reject_preference(self, preference_id: str) -> dict[str, Any] | None:
        return self._update_status(preference_id, "rejected")

    def _update_status(self, preference_id: str, new_status: str) -> dict[str, Any] | None:
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


# ── Migration utility ─────────────────────────────────────────────

def migrate_json_to_sqlite(
    *,
    sessions_dir: str = "data/sessions",
    artifacts_dir: str = "data/artifacts",
    corrections_dir: str = "data/corrections",
    preferences_dir: str = "data/preferences",
    db_path: str = "data/projecth.db",
) -> dict[str, int]:
    """Migrate JSON file stores to SQLite. Returns counts per table."""
    db = SQLiteDatabase(db_path)
    counts: dict[str, int] = {}

    # Sessions
    sessions_path = Path(sessions_dir)
    count = 0
    if sessions_path.is_dir():
        for f in sessions_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sid = data.get("session_id", f.stem)
                store = SQLiteSessionStore(db)
                store._save(sid, data)
                count += 1
            except Exception:
                continue
    counts["sessions"] = count

    # Artifacts
    artifacts_path = Path(artifacts_dir)
    count = 0
    if artifacts_path.is_dir():
        for f in artifacts_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                now = data.get("created_at", _now_iso())
                db.execute(
                    "INSERT OR IGNORE INTO artifacts (artifact_id, artifact_kind, session_id, source_message_id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (data["artifact_id"], data.get("artifact_kind", "grounded_brief"), data.get("session_id", ""), data.get("source_message_id", ""), json.dumps(data, ensure_ascii=False, default=str), now, now),
                )
                count += 1
            except Exception:
                continue
    db.commit()
    counts["artifacts"] = count

    # Preferences
    prefs_path = Path(preferences_dir)
    count = 0
    if prefs_path.is_dir():
        for f in prefs_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                now = data.get("created_at", _now_iso())
                db.execute(
                    "INSERT OR IGNORE INTO preferences (preference_id, delta_fingerprint, description, status, data, created_at, updated_at, activated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (data["preference_id"], data.get("delta_fingerprint", ""), data.get("description", ""), data.get("status", "candidate"), json.dumps(data, ensure_ascii=False, default=str), now, now, data.get("activated_at")),
                )
                count += 1
            except Exception:
                continue
    db.commit()
    counts["preferences"] = count

    db.close()
    return counts
