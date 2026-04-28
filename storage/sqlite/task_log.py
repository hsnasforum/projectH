"""SQLite-backed task logger."""

from __future__ import annotations

import json
from typing import Any

from core.contracts import TaskLogEntry
from storage.sqlite.database import SQLiteDatabase, _now_iso


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

    def iter_session_records(self, session_id: str) -> list[TaskLogEntry]:
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

