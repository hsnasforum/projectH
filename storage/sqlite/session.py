"""SQLite-backed session store."""

from __future__ import annotations

import json
import threading
from typing import Any

from storage.sqlite.database import SQLiteDatabase, _now_iso


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

