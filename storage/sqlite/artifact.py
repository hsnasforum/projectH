"""SQLite-backed artifact store."""

from __future__ import annotations

import json
from typing import Any

from core.contracts import ArtifactRecord
from storage.artifact_store import _is_valid_artifact_record
from storage.sqlite.database import SQLiteDatabase, _now_iso


# ── SQLite Artifact Store ─────────────────────────────────────────

class SQLiteArtifactStore:
    """Drop-in replacement for ArtifactStore, backed by SQLite."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def create(self, *, artifact_id: str, artifact_kind: str, session_id: str,
               source_message_id: str, draft_text: str, source_paths: list[str] | None = None,
               response_origin: dict[str, Any] | None = None,
               summary_chunks: list[dict[str, Any]] | None = None,
               evidence: list[dict[str, Any]] | None = None) -> ArtifactRecord:
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

    def get(self, artifact_id: str) -> ArtifactRecord | None:
        row = self._db.fetchone("SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,))
        if not row:
            return None
        data = json.loads(row["data"])
        data.update({"artifact_id": row["artifact_id"], "artifact_kind": row["artifact_kind"], "session_id": row["session_id"], "created_at": row["created_at"], "updated_at": row["updated_at"]})
        return data

    def list_by_session(self, session_id: str) -> list[ArtifactRecord]:
        rows = self._db.fetchall("SELECT * FROM artifacts WHERE session_id = ? ORDER BY created_at DESC", (session_id,))
        return [
            record
            for record in (
                {
                    "artifact_id": r["artifact_id"],
                    "session_id": r["session_id"],
                    **json.loads(r["data"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            )
            if _is_valid_artifact_record(record)
        ]

    def list_recent(self, limit: int = 20) -> list[ArtifactRecord]:
        rows = self._db.fetchall("SELECT * FROM artifacts ORDER BY created_at DESC LIMIT ?", (limit,))
        return [
            record
            for record in (
                {
                    "artifact_id": r["artifact_id"],
                    "session_id": r["session_id"],
                    **json.loads(r["data"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            )
            if _is_valid_artifact_record(record)
        ]

