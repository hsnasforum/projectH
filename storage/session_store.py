from __future__ import annotations

import json
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
import threading
from typing import Any, Dict
from uuid import uuid4


SESSION_SCHEMA_VERSION = "1.0"
ALLOWED_WEB_SEARCH_PERMISSIONS = {"disabled", "approval", "enabled"}
ALLOWED_FEEDBACK_LABELS = {"helpful", "unclear", "incorrect"}
ALLOWED_FEEDBACK_REASONS = {"factual_error", "irrelevant_result", "context_miss", "awkward_tone"}


class SessionStore:
    def __init__(self, base_dir: str = "data/sessions") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _default_session(self, session_id: str) -> Dict[str, Any]:
        now = self._now()
        return {
            "schema_version": SESSION_SCHEMA_VERSION,
            "session_id": session_id,
            "title": session_id,
            "messages": [],
            "pending_approvals": [],
            "permissions": {"web_search": "disabled"},
            "active_context": None,
            "created_at": now,
            "updated_at": now,
        }

    def _normalize_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(message)
        normalized["message_id"] = normalized.get("message_id") or f"msg-{uuid4().hex[:12]}"
        normalized["created_at"] = normalized.get("created_at") or self._now()
        normalized["role"] = normalized.get("role", "assistant")
        normalized["text"] = str(normalized.get("text", ""))
        feedback = normalized.get("feedback")
        if isinstance(feedback, dict):
            label = str(feedback.get("label") or "").strip().lower()
            if label in ALLOWED_FEEDBACK_LABELS:
                feedback_record = {
                    "label": label,
                    "updated_at": str(feedback.get("updated_at") or self._now()),
                }
                reason = str(feedback.get("reason") or "").strip().lower()
                if reason in ALLOWED_FEEDBACK_REASONS:
                    feedback_record["reason"] = reason
                normalized["feedback"] = feedback_record
            else:
                normalized.pop("feedback", None)
        elif feedback is not None:
            normalized.pop("feedback", None)
        return normalized

    def _derive_title(self, session_id: str, messages: list[Dict[str, Any]]) -> str:
        for message in messages:
            if message.get("role") != "user":
                continue
            text = str(message.get("text", "")).strip()
            if not text:
                continue
            compact = " ".join(text.split())
            return compact[:40] + ("..." if len(compact) > 40 else "")
        return session_id

    def _normalize_session(self, session_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._default_session(session_id)
        normalized.update({key: value for key, value in data.items() if key not in {"messages", "pending_approvals"}})
        messages = data.get("messages", [])
        pending_approvals = data.get("pending_approvals", [])
        permissions = data.get("permissions")
        normalized["messages"] = [
            self._normalize_message(message)
            for message in messages
            if isinstance(message, dict)
        ]
        normalized["pending_approvals"] = [
            dict(approval)
            for approval in pending_approvals
            if isinstance(approval, dict)
        ]
        if isinstance(permissions, dict):
            web_search_permission = str(permissions.get("web_search") or "disabled").strip().lower()
            if web_search_permission not in ALLOWED_WEB_SEARCH_PERMISSIONS:
                web_search_permission = "disabled"
        else:
            web_search_permission = "disabled"
        normalized["permissions"] = {"web_search": web_search_permission}
        normalized["schema_version"] = SESSION_SCHEMA_VERSION
        normalized["title"] = str(normalized.get("title") or self._derive_title(session_id, normalized["messages"]))
        if normalized.get("active_context") is not None and not isinstance(normalized.get("active_context"), dict):
            normalized["active_context"] = None
        normalized["created_at"] = str(normalized.get("created_at") or self._now())
        normalized["updated_at"] = str(normalized.get("updated_at") or normalized["created_at"])
        return normalized

    def _save(self, session_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            path = self._path(session_id)
            temp_path = path.with_name(f"{path.name}.{uuid4().hex[:8]}.tmp")
            data["updated_at"] = self._now()
            encoded = json.dumps(data, ensure_ascii=False, indent=2)
            temp_path.write_text(encoded, encoding="utf-8")
            temp_path.replace(path)

    def _backup_corrupt_session_file(self, path: Path) -> None:
        if not path.exists():
            return
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        backup_path = path.with_name(f"{path.stem}.corrupt-{timestamp}{path.suffix}")
        try:
            path.replace(backup_path)
        except OSError:
            path.unlink(missing_ok=True)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            path = self._path(session_id)
            if path.exists():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                except (JSONDecodeError, OSError):
                    self._backup_corrupt_session_file(path)
                    recovered = self._default_session(session_id)
                    self._save(session_id, recovered)
                    return recovered
                normalized = self._normalize_session(session_id, loaded)
                if normalized != loaded:
                    self._save(session_id, normalized)
                return normalized
            return self._default_session(session_id)

    def list_sessions(self) -> list[Dict[str, Any]]:
        with self._lock:
            summaries: list[Dict[str, Any]] = []
            for path in sorted(self.base_dir.glob("*.json")):
                try:
                    session_id = path.stem
                    data = self.get_session(session_id)
                except Exception:
                    continue
                last_message = data["messages"][-1]["text"] if data["messages"] else ""
                summaries.append(
                    {
                        "session_id": data["session_id"],
                        "title": data["title"],
                        "updated_at": data["updated_at"],
                        "created_at": data["created_at"],
                        "message_count": len(data["messages"]),
                        "pending_approval_count": len(data["pending_approvals"]),
                        "last_message_preview": last_message[:80],
                    }
                )
            return sorted(summaries, key=lambda item: item.get("updated_at", ""), reverse=True)

    def append_message(self, session_id: str, message: Dict[str, Any]) -> None:
        with self._lock:
            data = self.get_session(session_id)
            normalized_message = self._normalize_message(message)
            data["messages"].append(normalized_message)
            if data.get("title") == session_id and normalized_message["role"] == "user":
                data["title"] = self._derive_title(session_id, data["messages"])
            self._save(session_id, data)

    def update_last_message(self, session_id: str, updates: Dict[str, Any]) -> None:
        with self._lock:
            data = self.get_session(session_id)
            messages = data.get("messages", [])
            if not messages:
                return

            last_message = dict(messages[-1])
            last_message.update(updates)
            messages[-1] = self._normalize_message(last_message)
            data["messages"] = messages
            self._save(session_id, data)

    def update_message(self, session_id: str, message_id: str, updates: Dict[str, Any]) -> Dict[str, Any] | None:
        with self._lock:
            data = self.get_session(session_id)
            messages = data.get("messages", [])
            updated_message: Dict[str, Any] | None = None
            for index, message in enumerate(messages):
                if str(message.get("message_id") or "") != str(message_id or ""):
                    continue
                patched = dict(message)
                patched.update(updates)
                normalized = self._normalize_message(patched)
                messages[index] = normalized
                updated_message = dict(normalized)
                break

            if updated_message is None:
                return None

            data["messages"] = messages
            self._save(session_id, data)
            return updated_message

    def add_pending_approval(self, session_id: str, approval: Dict[str, Any]) -> None:
        with self._lock:
            data = self.get_session(session_id)
            pending = data.get("pending_approvals", [])
            pending.append(dict(approval))
            data["pending_approvals"] = pending
            self._save(session_id, data)

    def get_pending_approval(self, session_id: str, approval_id: str) -> Dict[str, Any] | None:
        with self._lock:
            data = self.get_session(session_id)
            for approval in data.get("pending_approvals", []):
                if approval.get("approval_id") == approval_id:
                    return dict(approval)
            return None

    def pop_pending_approval(self, session_id: str, approval_id: str) -> Dict[str, Any] | None:
        with self._lock:
            data = self.get_session(session_id)
            pending = data.get("pending_approvals", [])
            kept: list[Dict[str, Any]] = []
            popped: Dict[str, Any] | None = None
            for approval in pending:
                if approval.get("approval_id") == approval_id and popped is None:
                    popped = dict(approval)
                    continue
                kept.append(dict(approval))
            if popped is None:
                return None
            data["pending_approvals"] = kept
            self._save(session_id, data)
            return popped

    def set_active_context(self, session_id: str, context: Dict[str, Any] | None) -> None:
        with self._lock:
            data = self.get_session(session_id)
            data["active_context"] = dict(context) if isinstance(context, dict) else None
            self._save(session_id, data)

    def get_active_context(self, session_id: str) -> Dict[str, Any] | None:
        with self._lock:
            data = self.get_session(session_id)
            context = data.get("active_context")
            if not isinstance(context, dict):
                return None
            return dict(context)

    def set_permissions(self, session_id: str, permissions: Dict[str, Any]) -> None:
        with self._lock:
            data = self.get_session(session_id)
            web_search_permission = str(
                permissions.get("web_search") or data.get("permissions", {}).get("web_search") or "disabled"
            ).strip().lower()
            if web_search_permission not in ALLOWED_WEB_SEARCH_PERMISSIONS:
                web_search_permission = "disabled"
            data["permissions"] = {"web_search": web_search_permission}
            self._save(session_id, data)

    def get_permissions(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            data = self.get_session(session_id)
            permissions = data.get("permissions")
            if not isinstance(permissions, dict):
                return {"web_search": "disabled"}
            web_search_permission = str(permissions.get("web_search") or "disabled").strip().lower()
            if web_search_permission not in ALLOWED_WEB_SEARCH_PERMISSIONS:
                web_search_permission = "disabled"
            return {"web_search": web_search_permission}
