"""SQLite database connection and schema helpers."""

from __future__ import annotations

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
