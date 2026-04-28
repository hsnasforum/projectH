from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Any, Dict, Iterator
from uuid import uuid4

from core.approval import (
    default_save_content_source_for_approval_kind,
    normalize_approval_reason_record,
    normalize_save_content_source,
    normalize_source_message_id,
)
from storage.errors import SaveConflictError, SessionCorruptError
from storage.json_store_base import atomic_write, json_path, read_json, utc_now_iso
from core.contracts import (
    ALLOWED_CANDIDATE_CONFIRMATION_LABELS,
    ALLOWED_CONTENT_REASON_LABELS,
    ALLOWED_CORRECTED_OUTCOME_REASON_LABELS,
    ALLOWED_CORRECTED_OUTCOMES,
    ALLOWED_FEEDBACK_LABELS,
    ALLOWED_FEEDBACK_REASONS,
    ALLOWED_SESSION_LOCAL_CANDIDATE_FAMILIES,
    ALLOWED_WEB_SEARCH_PERMISSIONS,
    CANDIDATE_REVIEW_ACTION_TO_STATUS,
    CandidateReviewSuggestedScope,
    ContentReasonLabel,
    ContentReasonScope,
    SESSION_LOCAL_MEMORY_SIGNAL_VERSION,
    WebSearchPermission,
)


SESSION_SCHEMA_VERSION = "1.0"
MAX_MESSAGES_PER_SESSION = 500

# Re-export for backward compatibility
ALLOWED_CANDIDATE_REVIEW_ACTION_TO_STATUS = CANDIDATE_REVIEW_ACTION_TO_STATUS


class SessionStore:
    def __init__(self, base_dir: str = "data/sessions") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, session_id: str) -> Path:
        return json_path(self.base_dir, session_id, sanitise=False)

    def _now(self) -> str:
        return utc_now_iso()

    def _default_session(self, session_id: str) -> Dict[str, Any]:
        now = self._now()
        return {
            "schema_version": SESSION_SCHEMA_VERSION,
            "session_id": session_id,
            "title": session_id,
            "messages": [],
            "pending_approvals": [],
            "operator_action_history": [],
            "permissions": {"web_search": "disabled"},
            "active_context": None,
            "_version": 0,
            "created_at": now,
            "updated_at": now,
        }

    def _normalize_text_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()]

    def _normalize_multiline_text(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.replace("\r\n", "\n").strip()
        return normalized or None

    def _normalize_dict_list(self, value: Any) -> list[Dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [dict(item) for item in value if isinstance(item, dict)]

    def _normalize_original_response_snapshot(self, snapshot: Any) -> Dict[str, Any] | None:
        if not isinstance(snapshot, dict):
            return None

        artifact_id = str(snapshot.get("artifact_id") or "").strip()
        artifact_kind = str(snapshot.get("artifact_kind") or "").strip()
        if not artifact_id or not artifact_kind:
            return None

        response_origin = snapshot.get("response_origin")
        return {
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "draft_text": str(snapshot.get("draft_text") or ""),
            "source_paths": self._normalize_text_list(snapshot.get("source_paths")),
            "response_origin": dict(response_origin) if isinstance(response_origin, dict) else None,
            "summary_chunks_snapshot": self._normalize_dict_list(snapshot.get("summary_chunks_snapshot")),
            "evidence_snapshot": self._normalize_dict_list(snapshot.get("evidence_snapshot")),
        }

    def _normalize_approval_record(
        self,
        approval: Any,
        *,
        include_note_text: bool = False,
        artifact_source_message_ids: dict[str, str] | None = None,
    ) -> Dict[str, Any] | None:
        if not isinstance(approval, dict):
            return None

        approval_id = str(approval.get("approval_id") or "").strip()
        kind = str(approval.get("kind") or "").strip()
        requested_path = str(approval.get("requested_path") or "").strip()
        if not approval_id or not kind or not requested_path:
            return None

        artifact_id = str(approval.get("artifact_id") or "").strip()
        source_message_id = normalize_source_message_id(approval.get("source_message_id"))
        if source_message_id is None and artifact_id and artifact_source_message_ids:
            source_message_id = normalize_source_message_id(artifact_source_message_ids.get(artifact_id))
        normalized = {
            "approval_id": approval_id,
            "kind": kind,
            "requested_path": requested_path,
            "overwrite": bool(approval.get("overwrite", False)),
            "preview_markdown": str(approval.get("preview_markdown", "")),
            "source_paths": self._normalize_text_list(approval.get("source_paths")),
            "created_at": str(approval.get("created_at") or self._now()),
        }
        if artifact_id:
            normalized["artifact_id"] = artifact_id
        if source_message_id:
            normalized["source_message_id"] = source_message_id
        save_content_source = (
            normalize_save_content_source(approval.get("save_content_source"))
            or default_save_content_source_for_approval_kind(kind)
        )
        if save_content_source is not None:
            normalized["save_content_source"] = save_content_source
        if include_note_text:
            normalized["note_text"] = str(approval.get("note_text", ""))

        approval_reason_record = normalize_approval_reason_record(
            approval.get("approval_reason_record"),
            fallback_artifact_id=artifact_id or None,
            fallback_artifact_kind="grounded_brief" if artifact_id else None,
            fallback_source_message_id=source_message_id,
            fallback_approval_id=approval_id,
        )
        if approval_reason_record is not None:
            normalized["approval_reason_record"] = approval_reason_record
        return normalized

    def _normalize_operator_action_record(self, approval: Any) -> Dict[str, Any] | None:
        if not isinstance(approval, dict):
            return None

        approval_id = str(approval.get("approval_id") or "").strip()
        kind = str(approval.get("kind") or "").strip()
        status = str(approval.get("status") or "").strip()
        if not approval_id or kind != "operator_action" or not status:
            return None

        normalized: Dict[str, Any] = {
            "approval_id": approval_id,
            "kind": "operator_action",
            "status": status,
        }
        for field in (
            "action_kind", "target_id", "content", "requested_at",
            "audit_trace_required", "is_reversible", "outcome_id",
        ):
            if field in approval:
                normalized[field] = approval[field]
        return normalized

    def _normalize_pending_approval_record(
        self,
        approval: Any,
        *,
        include_note_text: bool = False,
        artifact_source_message_ids: dict[str, str] | None = None,
    ) -> Dict[str, Any] | None:
        if isinstance(approval, dict) and str(approval.get("kind") or "").strip() == "operator_action":
            return self._normalize_operator_action_record(approval)
        return self._normalize_approval_record(
            approval,
            include_note_text=include_note_text,
            artifact_source_message_ids=artifact_source_message_ids,
        )

    def _normalize_corrected_outcome(
        self,
        corrected_outcome: Any,
        *,
        fallback_artifact_id: str | None = None,
        fallback_source_message_id: str | None = None,
    ) -> Dict[str, Any] | None:
        if not isinstance(corrected_outcome, dict):
            return None

        outcome = str(corrected_outcome.get("outcome") or "").strip().lower()
        if outcome not in ALLOWED_CORRECTED_OUTCOMES:
            return None

        artifact_id = str(corrected_outcome.get("artifact_id") or fallback_artifact_id or "").strip()
        source_message_id = str(
            corrected_outcome.get("source_message_id") or fallback_source_message_id or ""
        ).strip()
        if not artifact_id or not source_message_id:
            return None

        normalized = {
            "outcome": outcome,
            "recorded_at": str(corrected_outcome.get("recorded_at") or self._now()),
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
        }
        reason_label = str(corrected_outcome.get("reason_label") or "").strip().lower()
        if reason_label:
            allowed_reason_labels = ALLOWED_CORRECTED_OUTCOME_REASON_LABELS.get(outcome, frozenset())
            if reason_label not in allowed_reason_labels:
                return None
            normalized["reason_label"] = reason_label
        approval_id = str(corrected_outcome.get("approval_id") or "").strip()
        if approval_id:
            normalized["approval_id"] = approval_id
        saved_note_path = str(corrected_outcome.get("saved_note_path") or "").strip()
        if saved_note_path:
            normalized["saved_note_path"] = saved_note_path
        return normalized

    def _normalize_content_reason_record(
        self,
        record: Any,
        *,
        fallback_artifact_id: str | None = None,
        fallback_artifact_kind: str | None = None,
        fallback_source_message_id: str | None = None,
    ) -> Dict[str, Any] | None:
        if not isinstance(record, dict):
            return None

        reason_scope = str(record.get("reason_scope") or "").strip().lower()
        allowed_labels = ALLOWED_CONTENT_REASON_LABELS.get(reason_scope)
        if not allowed_labels:
            return None

        reason_label = str(record.get("reason_label") or "").strip().lower()
        if reason_label not in allowed_labels:
            return None

        artifact_id = str(record.get("artifact_id") or fallback_artifact_id or "").strip()
        artifact_kind = str(record.get("artifact_kind") or fallback_artifact_kind or "").strip()
        source_message_id = str(record.get("source_message_id") or fallback_source_message_id or "").strip()
        if not artifact_id or not artifact_kind or not source_message_id:
            return None

        normalized = {
            "reason_scope": reason_scope,
            "reason_label": reason_label,
            "recorded_at": str(record.get("recorded_at") or self._now()),
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "source_message_id": source_message_id,
        }
        reason_note = self._normalize_multiline_text(record.get("reason_note"))
        if reason_note:
            normalized["reason_note"] = reason_note
        return normalized

    def _normalize_candidate_confirmation_record(
        self,
        record: Any,
        *,
        fallback_artifact_id: str | None = None,
        fallback_source_message_id: str | None = None,
    ) -> Dict[str, Any] | None:
        if not isinstance(record, dict):
            return None

        candidate_id = str(record.get("candidate_id") or "").strip()
        candidate_family = str(record.get("candidate_family") or "").strip().lower()
        candidate_updated_at = str(record.get("candidate_updated_at") or "").strip()
        confirmation_scope = str(record.get("confirmation_scope") or "").strip().lower()
        allowed_labels = ALLOWED_CANDIDATE_CONFIRMATION_LABELS.get(confirmation_scope)
        if (
            not candidate_id
            or candidate_family not in ALLOWED_SESSION_LOCAL_CANDIDATE_FAMILIES
            or not candidate_updated_at
            or not allowed_labels
        ):
            return None

        confirmation_label = str(record.get("confirmation_label") or "").strip().lower()
        if confirmation_label not in allowed_labels:
            return None

        artifact_id = str(record.get("artifact_id") or fallback_artifact_id or "").strip()
        source_message_id = str(record.get("source_message_id") or fallback_source_message_id or "").strip()
        if not artifact_id or not source_message_id:
            return None

        return {
            "candidate_id": candidate_id,
            "candidate_family": candidate_family,
            "candidate_updated_at": candidate_updated_at,
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "confirmation_scope": confirmation_scope,
            "confirmation_label": confirmation_label,
            "recorded_at": str(record.get("recorded_at") or self._now()),
        }

    def _normalize_candidate_review_record(
        self,
        record: Any,
        *,
        fallback_artifact_id: str | None = None,
        fallback_source_message_id: str | None = None,
    ) -> Dict[str, Any] | None:
        if not isinstance(record, dict):
            return None

        candidate_id = str(record.get("candidate_id") or "").strip()
        candidate_updated_at = str(record.get("candidate_updated_at") or "").strip()
        review_scope = str(record.get("review_scope") or "").strip().lower()
        review_action = str(record.get("review_action") or "").strip().lower()
        review_status = str(record.get("review_status") or "").strip().lower()
        expected_status = ALLOWED_CANDIDATE_REVIEW_ACTION_TO_STATUS.get(review_action)
        if (
            not candidate_id
            or not candidate_updated_at
            or review_scope != "source_message_candidate_review"
            or expected_status is None
            or review_status != expected_status
        ):
            return None

        artifact_id = str(record.get("artifact_id") or fallback_artifact_id or "").strip()
        source_message_id = str(record.get("source_message_id") or fallback_source_message_id or "").strip()
        if not artifact_id or not source_message_id:
            return None

        normalized = {
            "candidate_id": candidate_id,
            "candidate_updated_at": candidate_updated_at,
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "review_scope": review_scope,
            "review_action": review_action,
            "review_status": review_status,
            "recorded_at": str(record.get("recorded_at") or self._now()),
        }
        reason_note = self._normalize_multiline_text(record.get("reason_note"))
        if reason_note:
            normalized["reason_note"] = reason_note
        suggested_scope = self._normalize_multiline_text(record.get("suggested_scope"))
        if suggested_scope:
            try:
                CandidateReviewSuggestedScope(suggested_scope)
            except ValueError as exc:
                raise ValueError(f"invalid suggested_scope: {suggested_scope!r}") from exc
            normalized["suggested_scope"] = suggested_scope
        return normalized

    def _build_original_response_snapshot_from_message(self, message: Dict[str, Any]) -> Dict[str, Any] | None:
        artifact_id = str(message.get("artifact_id") or "").strip()
        artifact_kind = str(message.get("artifact_kind") or "").strip()
        if message.get("role") != "assistant" or artifact_kind != "grounded_brief" or not artifact_id:
            return None

        evidence_snapshot = self._normalize_dict_list(message.get("evidence"))
        summary_chunks_snapshot = self._normalize_dict_list(message.get("summary_chunks"))
        if not evidence_snapshot and not summary_chunks_snapshot:
            return None

        response_origin = message.get("response_origin")
        return self._normalize_original_response_snapshot(
            {
                "artifact_id": artifact_id,
                "artifact_kind": artifact_kind,
                "draft_text": str(message.get("text") or ""),
                "source_paths": self._normalize_text_list(message.get("selected_source_paths")),
                "response_origin": dict(response_origin) if isinstance(response_origin, dict) else None,
                "summary_chunks_snapshot": summary_chunks_snapshot,
                "evidence_snapshot": evidence_snapshot,
            }
        )

    def _build_artifact_source_message_ids(self, messages: list[Dict[str, Any]]) -> dict[str, str]:
        artifact_source_message_ids: dict[str, str] = {}
        for message in messages:
            artifact_id = str(message.get("artifact_id") or "").strip()
            message_id = str(message.get("message_id") or "").strip()
            if not artifact_id or not message_id:
                continue
            if not isinstance(message.get("original_response_snapshot"), dict):
                continue
            artifact_source_message_ids[artifact_id] = message_id
        return artifact_source_message_ids

    def _find_artifact_source_message_in_messages(
        self,
        messages: list[Dict[str, Any]],
        artifact_id: str,
    ) -> tuple[int, Dict[str, Any]] | None:
        normalized_artifact_id = str(artifact_id or "").strip()
        if not normalized_artifact_id:
            return None
        for index in range(len(messages) - 1, -1, -1):
            message = messages[index]
            if str(message.get("artifact_id") or "").strip() != normalized_artifact_id:
                continue
            if not isinstance(message.get("original_response_snapshot"), dict):
                continue
            return index, dict(message)
        return None

    def _normalize_source_message_anchor(
        self,
        message: Dict[str, Any],
    ) -> tuple[str, str] | None:
        artifact_id = str(message.get("artifact_id") or "").strip()
        source_message_id = normalize_source_message_id(message.get("source_message_id"))
        message_id = str(message.get("message_id") or "").strip()
        if source_message_id is None and message_id:
            source_message_id = message_id
        if not artifact_id or not source_message_id:
            return None
        return artifact_id, source_message_id

    def _is_matching_anchor(
        self,
        *,
        artifact_id: str,
        source_message_id: str,
        candidate_artifact_id: Any,
        candidate_source_message_id: Any,
    ) -> bool:
        normalized_artifact_id = str(candidate_artifact_id or "").strip()
        normalized_source_message_id = normalize_source_message_id(candidate_source_message_id)
        return normalized_artifact_id == artifact_id and normalized_source_message_id == source_message_id

    def _latest_approval_reason_record_for_anchor(
        self,
        session: Dict[str, Any],
        *,
        artifact_id: str,
        source_message_id: str,
    ) -> Dict[str, Any] | None:
        candidates: list[tuple[str, int, Dict[str, Any]]] = []
        messages = session.get("messages", [])
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            approval_reason_record = normalize_approval_reason_record(
                message.get("approval_reason_record"),
                fallback_artifact_id=str(message.get("artifact_id") or "").strip() or None,
                fallback_artifact_kind=str(message.get("artifact_kind") or "").strip() or None,
                fallback_source_message_id=normalize_source_message_id(message.get("source_message_id")),
                fallback_approval_id=(
                    str(message.get("approval_id") or "").strip()
                    or str((message.get("approval") or {}).get("approval_id") or "").strip()
                    or None
                ),
            )
            if approval_reason_record is None:
                continue
            if not self._is_matching_anchor(
                artifact_id=artifact_id,
                source_message_id=source_message_id,
                candidate_artifact_id=approval_reason_record.get("artifact_id"),
                candidate_source_message_id=approval_reason_record.get("source_message_id"),
            ):
                continue
            candidates.append(
                (
                    str(approval_reason_record.get("recorded_at") or ""),
                    index,
                    approval_reason_record,
                )
            )

        artifact_source_message_ids = self._build_artifact_source_message_ids(messages)
        pending_offset = len(messages)
        for index, approval in enumerate(session.get("pending_approvals", [])):
            normalized_approval = self._normalize_approval_record(
                approval,
                include_note_text=True,
                artifact_source_message_ids=artifact_source_message_ids,
            )
            if normalized_approval is None:
                continue
            if not self._is_matching_anchor(
                artifact_id=artifact_id,
                source_message_id=source_message_id,
                candidate_artifact_id=normalized_approval.get("artifact_id"),
                candidate_source_message_id=normalized_approval.get("source_message_id"),
            ):
                continue
            approval_reason_record = normalize_approval_reason_record(
                normalized_approval.get("approval_reason_record"),
                fallback_artifact_id=artifact_id,
                fallback_artifact_kind="grounded_brief",
                fallback_source_message_id=source_message_id,
                fallback_approval_id=str(normalized_approval.get("approval_id") or "").strip() or None,
            )
            if approval_reason_record is None:
                continue
            candidates.append(
                (
                    str(approval_reason_record.get("recorded_at") or ""),
                    pending_offset + index,
                    approval_reason_record,
                )
            )

        if not candidates:
            return None
        return dict(max(candidates, key=lambda item: (item[0], item[1]))[2])

    def _latest_save_signal_for_anchor(
        self,
        session: Dict[str, Any],
        *,
        artifact_id: str,
        source_message_id: str,
        source_message: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        latest_saved_message: Dict[str, Any] | None = None
        for message in reversed(session.get("messages", [])):
            if not isinstance(message, dict):
                continue
            if not self._is_matching_anchor(
                artifact_id=artifact_id,
                source_message_id=source_message_id,
                candidate_artifact_id=message.get("artifact_id"),
                candidate_source_message_id=message.get("source_message_id"),
            ):
                continue
            saved_note_path = str(message.get("saved_note_path") or "").strip()
            if not saved_note_path:
                continue
            latest_saved_message = message
            break

        signal: Dict[str, Any] = {}
        if latest_saved_message is not None:
            latest_save_content_source = normalize_save_content_source(latest_saved_message.get("save_content_source"))
            latest_saved_note_path = str(latest_saved_message.get("saved_note_path") or "").strip()
            latest_approval_id = str(latest_saved_message.get("approval_id") or "").strip()
            latest_saved_at = str(latest_saved_message.get("created_at") or "").strip()
            if latest_save_content_source is not None:
                signal["latest_save_content_source"] = latest_save_content_source
            if latest_saved_note_path:
                signal["latest_saved_note_path"] = latest_saved_note_path
            if latest_approval_id:
                signal["latest_approval_id"] = latest_approval_id
            if latest_saved_at:
                signal["latest_saved_at"] = latest_saved_at

        corrected_outcome = self._normalize_corrected_outcome(
            source_message.get("corrected_outcome"),
            fallback_artifact_id=artifact_id,
            fallback_source_message_id=source_message_id,
        )
        if corrected_outcome is not None:
            latest_approval_id = str(corrected_outcome.get("approval_id") or "").strip()
            latest_saved_note_path = str(corrected_outcome.get("saved_note_path") or "").strip()
            if latest_approval_id:
                signal["latest_approval_id"] = latest_approval_id
            if latest_saved_note_path and "latest_saved_note_path" not in signal:
                signal["latest_saved_note_path"] = latest_saved_note_path
            latest_saved_at = str(corrected_outcome.get("recorded_at") or "").strip()
            if latest_saved_at and "latest_saved_at" not in signal:
                signal["latest_saved_at"] = latest_saved_at

        return signal or None

    def build_session_local_memory_signal(
        self,
        session: Dict[str, Any],
        *,
        source_message: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        if (
            source_message.get("role") != "assistant"
            or str(source_message.get("artifact_kind") or "").strip() != "grounded_brief"
            or not isinstance(source_message.get("original_response_snapshot"), dict)
        ):
            return None

        anchor = self._normalize_source_message_anchor(source_message)
        if anchor is None:
            return None
        artifact_id, source_message_id = anchor

        corrected_outcome = self._normalize_corrected_outcome(
            source_message.get("corrected_outcome"),
            fallback_artifact_id=artifact_id,
            fallback_source_message_id=source_message_id,
        )
        content_reason_record = self._normalize_content_reason_record(
            source_message.get("content_reason_record"),
            fallback_artifact_id=artifact_id,
            fallback_artifact_kind="grounded_brief",
            fallback_source_message_id=source_message_id,
        )
        approval_reason_record = self._latest_approval_reason_record_for_anchor(
            session,
            artifact_id=artifact_id,
            source_message_id=source_message_id,
        )
        save_signal = self._latest_save_signal_for_anchor(
            session,
            artifact_id=artifact_id,
            source_message_id=source_message_id,
            source_message=source_message,
        )

        signal: Dict[str, Any] = {
            "signal_version": SESSION_LOCAL_MEMORY_SIGNAL_VERSION,
            "signal_scope": "session_local",
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
        }
        derived_at_candidates: list[str] = []

        if corrected_outcome is not None and corrected_outcome.get("outcome") == "corrected":
            signal["correction_signal"] = {
                "corrected_outcome": corrected_outcome,
                "has_corrected_text": self._normalize_multiline_text(source_message.get("corrected_text")) is not None,
            }
            recorded_at = str(corrected_outcome.get("recorded_at") or "").strip()
            if recorded_at:
                derived_at_candidates.append(recorded_at)
        if content_reason_record is not None:
            signal["content_signal"] = {
                "content_reason_record": content_reason_record,
            }
            recorded_at = str(content_reason_record.get("recorded_at") or "").strip()
            if recorded_at:
                derived_at_candidates.append(recorded_at)
        if approval_reason_record is not None:
            signal["approval_signal"] = {
                "latest_approval_reason_record": approval_reason_record,
            }
            recorded_at = str(approval_reason_record.get("recorded_at") or "").strip()
            if recorded_at:
                derived_at_candidates.append(recorded_at)
        if save_signal is not None:
            signal["save_signal"] = save_signal
            latest_saved_at = str(save_signal.get("latest_saved_at") or "").strip()
            if latest_saved_at:
                derived_at_candidates.append(latest_saved_at)

        if not any(key in signal for key in ("correction_signal", "content_signal", "approval_signal", "save_signal")):
            return None
        signal["derived_at"] = max(derived_at_candidates) if derived_at_candidates else self._now()
        return signal

    def _current_correctable_text(self, message: Dict[str, Any]) -> str:
        corrected_text = self._normalize_multiline_text(message.get("corrected_text"))
        if corrected_text:
            return corrected_text

        snapshot = message.get("original_response_snapshot")
        if isinstance(snapshot, dict):
            draft_text = self._normalize_multiline_text(snapshot.get("draft_text"))
            if draft_text:
                return draft_text

        return self._normalize_multiline_text(message.get("text")) or ""

    def _normalize_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(message)
        normalized["message_id"] = normalized.get("message_id") or f"msg-{uuid4().hex[:12]}"
        normalized["created_at"] = normalized.get("created_at") or self._now()
        normalized["role"] = normalized.get("role", "assistant")
        normalized["text"] = str(normalized.get("text", ""))
        approval = self._normalize_approval_record(normalized.get("approval"))
        if approval is not None:
            normalized["approval"] = approval
            normalized["approval_id"] = approval["approval_id"]
        else:
            normalized.pop("approval", None)
            if normalized.get("approval_id") is None:
                normalized.pop("approval_id", None)
        save_content_source = normalize_save_content_source(normalized.get("save_content_source"))
        if save_content_source is not None and normalized.get("role") == "assistant":
            normalized["save_content_source"] = save_content_source
        else:
            normalized.pop("save_content_source", None)
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

        snapshot = self._build_original_response_snapshot_from_message(normalized)
        if snapshot is not None:
            normalized["original_response_snapshot"] = snapshot
        else:
            normalized_snapshot = self._normalize_original_response_snapshot(normalized.get("original_response_snapshot"))
            if normalized_snapshot is not None:
                normalized["original_response_snapshot"] = normalized_snapshot
            else:
                normalized.pop("original_response_snapshot", None)

        corrected_text = self._normalize_multiline_text(normalized.get("corrected_text"))
        is_grounded_brief_source = (
            normalized.get("role") == "assistant"
            and normalized.get("artifact_kind") == "grounded_brief"
            and isinstance(normalized.get("original_response_snapshot"), dict)
        )
        is_applied_preference_response = (
            normalized.get("role") == "assistant"
            and bool(normalized.get("applied_preference_ids"))
        )
        source_message_id = normalize_source_message_id(normalized.get("source_message_id"))
        if source_message_id is None and isinstance(normalized.get("approval"), dict):
            source_message_id = normalize_source_message_id((normalized.get("approval") or {}).get("source_message_id"))
        if source_message_id is None and is_grounded_brief_source:
            source_message_id = normalize_source_message_id(normalized.get("message_id"))
        if normalized.get("role") == "assistant" and source_message_id is not None:
            normalized["source_message_id"] = source_message_id
        else:
            normalized.pop("source_message_id", None)
        if (is_grounded_brief_source or is_applied_preference_response) and corrected_text is not None:
            normalized["corrected_text"] = corrected_text
        else:
            normalized.pop("corrected_text", None)

        approval_reason_record = normalize_approval_reason_record(
            normalized.get("approval_reason_record"),
            fallback_artifact_id=str(normalized.get("artifact_id") or "").strip() or None,
            fallback_artifact_kind=str(normalized.get("artifact_kind") or "").strip() or None,
            fallback_approval_id=(
                str(normalized.get("approval_id") or "").strip()
                or str((normalized.get("approval") or {}).get("approval_id") or "").strip()
                or None
            ),
        )
        if approval_reason_record is not None:
            normalized["approval_reason_record"] = approval_reason_record
        else:
            normalized.pop("approval_reason_record", None)

        corrected_outcome = self._normalize_corrected_outcome(
            normalized.get("corrected_outcome"),
            fallback_artifact_id=str(normalized.get("artifact_id") or "").strip() or None,
            fallback_source_message_id=str(normalized.get("message_id") or "").strip() or None,
        )
        if is_grounded_brief_source and corrected_outcome is not None:
            if corrected_outcome.get("outcome") == "corrected" and corrected_text is None:
                corrected_outcome = None
            else:
                normalized["corrected_outcome"] = corrected_outcome
        if corrected_outcome is None or not is_grounded_brief_source:
            normalized.pop("corrected_outcome", None)

        content_reason_record = self._normalize_content_reason_record(
            normalized.get("content_reason_record"),
            fallback_artifact_id=str(normalized.get("artifact_id") or "").strip() or None,
            fallback_artifact_kind=str(normalized.get("artifact_kind") or "").strip() or None,
            fallback_source_message_id=str(normalized.get("message_id") or "").strip() or None,
        )
        if (
            is_grounded_brief_source
            and corrected_outcome is not None
            and corrected_outcome.get("outcome") == "rejected"
            and content_reason_record is not None
        ):
            normalized["content_reason_record"] = content_reason_record
        else:
            normalized.pop("content_reason_record", None)

        candidate_confirmation_record = self._normalize_candidate_confirmation_record(
            normalized.get("candidate_confirmation_record"),
            fallback_artifact_id=str(normalized.get("artifact_id") or "").strip() or None,
            fallback_source_message_id=str(normalized.get("message_id") or "").strip() or None,
        )
        if (
            is_grounded_brief_source
            and corrected_outcome is not None
            and corrected_outcome.get("outcome") == "corrected"
            and corrected_text is not None
            and candidate_confirmation_record is not None
        ):
            normalized["candidate_confirmation_record"] = candidate_confirmation_record
        else:
            normalized.pop("candidate_confirmation_record", None)

        candidate_review_record = self._normalize_candidate_review_record(
            normalized.get("candidate_review_record"),
            fallback_artifact_id=str(normalized.get("artifact_id") or "").strip() or None,
            fallback_source_message_id=str(normalized.get("message_id") or "").strip() or None,
        )
        if (
            is_grounded_brief_source
            and corrected_outcome is not None
            and corrected_outcome.get("outcome") == "corrected"
            and corrected_text is not None
            and candidate_confirmation_record is not None
            and candidate_review_record is not None
        ):
            normalized["candidate_review_record"] = candidate_review_record
        else:
            normalized.pop("candidate_review_record", None)
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
        if len(normalized["messages"]) > MAX_MESSAGES_PER_SESSION:
            normalized["messages"] = normalized["messages"][-MAX_MESSAGES_PER_SESSION:]
        artifact_source_message_ids = self._build_artifact_source_message_ids(normalized["messages"])
        normalized["pending_approvals"] = [
            normalized_approval
            for approval in pending_approvals
            if (
                normalized_approval := self._normalize_pending_approval_record(
                    approval,
                    include_note_text=True,
                    artifact_source_message_ids=artifact_source_message_ids,
                )
            )
            is not None
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
        self._backfill_active_context_summary_hint_basis(normalized)
        normalized["created_at"] = str(normalized.get("created_at") or self._now())
        normalized["updated_at"] = str(normalized.get("updated_at") or normalized["created_at"])
        return normalized

    @staticmethod
    def _compact_summary_hint_for_persist(text: str, max_chars: int = 240) -> str:
        compact = " ".join(str(text or "").split())
        if len(compact) <= max_chars:
            return compact
        return compact[:max_chars].rstrip() + "..."

    @staticmethod
    def _backfill_active_context_summary_hint_basis(data: Dict[str, Any]) -> None:
        """Ensure `active_context.summary_hint_basis` is set on legacy sessions.

        Legacy sessions saved before the field existed may still carry
        `active_context.summary_hint` without an explicit `summary_hint_basis`.
        Recover `recorded_correction` only when a same-session grounded-brief
        assistant message with `corrected_text` compacts to the current hint;
        otherwise fall back to the safe `current_summary`.
        """
        active_context = data.get("active_context")
        if not isinstance(active_context, dict):
            return
        if "summary_hint" not in active_context:
            return
        raw_basis = str(active_context.get("summary_hint_basis") or "").strip()
        if raw_basis in {"current_summary", "recorded_correction"}:
            return
        hint = active_context.get("summary_hint")
        if not hint:
            active_context["summary_hint_basis"] = "current_summary"
            return
        hint_text = str(hint)
        matched = False
        for message in data.get("messages", []) or []:
            if not isinstance(message, dict):
                continue
            if message.get("role") != "assistant":
                continue
            if str(message.get("artifact_kind") or "").strip() != "grounded_brief":
                continue
            corrected_text = message.get("corrected_text")
            if not corrected_text:
                continue
            if SessionStore._compact_summary_hint_for_persist(str(corrected_text)) == hint_text:
                matched = True
                break
        active_context["summary_hint_basis"] = "recorded_correction" if matched else "current_summary"

    def _save(self, session_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            path = self._path(session_id)
            data["_version"] = data.get("_version", 0) + 1
            data["updated_at"] = self._now()
            atomic_write(path, data)

    def _backup_corrupt_session_file(self, path: Path) -> Path | None:
        if not path.exists():
            return None
        quarantine_dir = self.base_dir / ".quarantine"
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        quarantine_path = quarantine_dir / f"{path.stem}.corrupt-{timestamp}{path.suffix}"
        try:
            path.replace(quarantine_path)
            return quarantine_path
        except OSError:
            path.unlink(missing_ok=True)
            return None

    def get_session(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            path = self._path(session_id)
            if path.exists():
                loaded = read_json(path)
                if not isinstance(loaded, dict):
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

    def get_global_audit_summary(self) -> Dict[str, Any]:
        """Return aggregate trace counts across all sessions for precondition assessment."""
        with self._lock:
            summary: Dict[str, Any] = {
                "session_count": 0,
                "correction_pair_count": 0,
                "feedback_like_count": 0,
                "feedback_dislike_count": 0,
                "personalized_response_count": 0,
                "personalized_correction_count": 0,
                "per_preference_stats": {},
                "operator_executed_count": 0,
                "operator_rolled_back_count": 0,
                "operator_failed_count": 0,
            }
            def count_feedback(feedback: Any) -> None:
                if not isinstance(feedback, dict):
                    return
                label = str(feedback.get("label") or "").strip().lower()
                if label in {"helpful", "like"}:
                    summary["feedback_like_count"] += 1
                elif label in {"unclear", "incorrect", "dislike"}:
                    summary["feedback_dislike_count"] += 1

            for path in sorted(self.base_dir.glob("*.json")):
                try:
                    session_id = path.stem
                    data = self.get_session(session_id)
                except Exception:
                    continue
                summary["session_count"] += 1
                for msg in data.get("messages", []):
                    if (
                        str(msg.get("artifact_kind") or "") == "grounded_brief"
                        and msg.get("corrected_text") is not None
                    ):
                        summary["correction_pair_count"] += 1
                    if msg.get("applied_preference_ids"):
                        summary["personalized_response_count"] += 1
                        is_personalized_correction = msg.get("corrected_text") is not None
                        if is_personalized_correction:
                            summary["personalized_correction_count"] += 1
                        for pref_id in msg["applied_preference_ids"]:
                            pstats = summary["per_preference_stats"].setdefault(
                                pref_id, {"applied_count": 0, "corrected_count": 0}
                            )
                            pstats["applied_count"] += 1
                            if is_personalized_correction:
                                pstats["corrected_count"] += 1
                    for event in msg.get("preference_correction_events", []):
                        if not isinstance(event, dict):
                            continue
                        event_fingerprint = str(event.get("fingerprint") or "").strip()
                        if not event_fingerprint:
                            continue
                        event_stats = summary["per_preference_stats"].setdefault(
                            event_fingerprint, {"applied_count": 0, "corrected_count": 0}
                        )
                        event_stats["corrected_count"] += 1
                    count_feedback(msg.get("feedback"))
                count_feedback(data.get("feedback"))
                for action in data.get("operator_action_history", []):
                    status = str(action.get("status") or "").strip()
                    if status == "executed":
                        summary["operator_executed_count"] += 1
                    elif status == "rolled_back":
                        summary["operator_rolled_back_count"] += 1
                    elif status == "failed":
                        summary["operator_failed_count"] += 1
            return summary

    def stream_trace_pairs(self) -> Iterator[Dict[str, Any]]:
        """Yield correction pairs (prompt/completion) from all sessions."""
        for path in sorted(self.base_dir.glob("*.json")):
            try:
                session_id = path.stem
                data = self.get_session(session_id)
            except Exception:
                continue
            for msg in data.get("messages", []):
                if str(msg.get("artifact_kind") or "") != "grounded_brief":
                    continue
                corrected_text = msg.get("corrected_text")
                if corrected_text is None:
                    continue
                snapshot = msg.get("original_response_snapshot")
                if not isinstance(snapshot, dict):
                    continue
                draft_text = str(snapshot.get("draft_text") or "").strip()
                if not draft_text:
                    continue
                yield {
                    "prompt": draft_text,
                    "completion": str(corrected_text),
                    "session_id": session_id,
                    "message_id": str(msg.get("message_id") or ""),
                    "feedback": msg.get("feedback"),
                    "applied_preference_ids": msg.get("applied_preference_ids"),
                }

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            path = self._path(session_id)
            if path.exists():
                path.unlink()
                return True
            return False

    def delete_all_sessions(self) -> int:
        with self._lock:
            count = 0
            for path in list(self.base_dir.glob("*.json")):
                try:
                    path.unlink()
                    count += 1
                except OSError:
                    continue
            return count

    def append_message(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self.get_session(session_id)
            normalized_message = self._normalize_message(message)
            data["messages"].append(normalized_message)
            if data.get("title") == session_id and normalized_message["role"] == "user":
                data["title"] = self._derive_title(session_id, data["messages"])
            self._save(session_id, data)
            return dict(normalized_message)

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

    def find_artifact_source_message(self, session_id: str, artifact_id: str) -> Dict[str, Any] | None:
        with self._lock:
            data = self.get_session(session_id)
            found = self._find_artifact_source_message_in_messages(data.get("messages", []), artifact_id)
            if found is None:
                return None
            _, message = found
            return message

    def record_correction_for_message(
        self,
        session_id: str,
        *,
        message_id: str,
        corrected_text: str,
    ) -> Dict[str, Any] | None:
        normalized_message_id = str(message_id or "").strip()
        normalized_corrected_text = self._normalize_multiline_text(corrected_text)
        if not normalized_message_id:
            raise ValueError("교정할 메시지 ID가 필요합니다.")
        if normalized_corrected_text is None:
            raise ValueError("수정 텍스트를 입력해 주세요.")

        with self._lock:
            data = self.get_session(session_id)
            messages = data.get("messages", [])
            updated_message: Dict[str, Any] | None = None
            for index, message in enumerate(messages):
                if str(message.get("message_id") or "").strip() != normalized_message_id:
                    continue

                if (
                    message.get("role") != "assistant"
                    or str(message.get("artifact_kind") or "").strip() != "grounded_brief"
                    or not isinstance(message.get("original_response_snapshot"), dict)
                ):
                    raise ValueError("교정할 grounded-brief 원문 응답을 찾지 못했습니다.")

                artifact_id = str(message.get("artifact_id") or "").strip()
                if not artifact_id:
                    raise ValueError("교정할 grounded-brief artifact anchor를 찾지 못했습니다.")

                current_text = self._current_correctable_text(message)
                if normalized_corrected_text == current_text:
                    raise ValueError("현재 초안과 동일합니다. 내용을 바꾼 뒤 제출해 주세요.")

                patched = dict(message)
                patched["corrected_text"] = normalized_corrected_text
                patched["corrected_outcome"] = {
                    "outcome": "corrected",
                    "reason_label": "explicit_correction_submitted",
                    "recorded_at": self._now(),
                    "artifact_id": artifact_id,
                    "source_message_id": normalized_message_id,
                }
                patched.pop("candidate_confirmation_record", None)
                patched.pop("candidate_review_record", None)
                patched.pop("content_reason_record", None)
                normalized = self._normalize_message(patched)
                messages[index] = normalized
                updated_message = dict(normalized)
                break

            if updated_message is None:
                return None

            data["messages"] = messages

            active_context = data.get("active_context")
            if isinstance(active_context, dict) and "summary_hint" in active_context:
                active_context["summary_hint"] = self._compact_summary_hint_for_persist(
                    normalized_corrected_text
                )
                active_context["summary_hint_basis"] = "recorded_correction"
                data["active_context"] = active_context

            self._save(session_id, data)
            return updated_message

    def record_preference_explicit_correction(
        self,
        session_id: str,
        *,
        message_id: str,
        fingerprint: str,
    ) -> bool:
        """applied-preference 응답에 대한 명시적 교정 신호를 기록한다."""
        normalized_message_id = str(message_id or "").strip()
        normalized_fingerprint = str(fingerprint or "").strip()
        if not normalized_message_id or not normalized_fingerprint:
            return False

        with self._lock:
            data = self.get_session(session_id)
            for message in data.get("messages", []):
                if str(message.get("message_id") or "").strip() != normalized_message_id:
                    continue
                if message.get("role") != "assistant":
                    return False
                applied_preference_ids = [
                    str(item).strip()
                    for item in (message.get("applied_preference_ids") or [])
                    if str(item).strip()
                ]
                if normalized_fingerprint not in applied_preference_ids:
                    return False
                events = message.setdefault("preference_correction_events", [])
                if not isinstance(events, list):
                    events = []
                    message["preference_correction_events"] = events
                events.append({"fingerprint": normalized_fingerprint, "ts": self._now()})
                self._save(session_id, data)
                return True
        return False

    def record_corrected_outcome_for_artifact(
        self,
        session_id: str,
        *,
        artifact_id: str | None,
        outcome: str,
        approval_id: str | None = None,
        saved_note_path: str | None = None,
        preserve_existing: bool = False,
    ) -> Dict[str, Any] | None:
        normalized_artifact_id = str(artifact_id or "").strip()
        normalized_outcome = str(outcome or "").strip().lower()
        if not normalized_artifact_id or normalized_outcome not in ALLOWED_CORRECTED_OUTCOMES:
            return None

        with self._lock:
            data = self.get_session(session_id)
            messages = data.get("messages", [])
            found = self._find_artifact_source_message_in_messages(messages, normalized_artifact_id)
            if found is None:
                return None

            index, message = found
            patched = dict(message)
            recorded_at = self._now()
            stored_outcome = normalized_outcome
            reason_label: str | None = None
            if preserve_existing:
                existing_outcome = self._normalize_corrected_outcome(
                    message.get("corrected_outcome"),
                    fallback_artifact_id=normalized_artifact_id,
                    fallback_source_message_id=str(message.get("message_id") or ""),
                )
                if existing_outcome is not None and str(existing_outcome.get("outcome") or "") == normalized_outcome:
                    stored_outcome = normalized_outcome
                    recorded_at = str(existing_outcome.get("recorded_at") or recorded_at)
                    reason_label = str(existing_outcome.get("reason_label") or "").strip() or None

            if stored_outcome == "corrected" and preserve_existing and reason_label is None:
                reason_label = "explicit_correction_submitted"

            patched["corrected_outcome"] = {
                "outcome": stored_outcome,
                **({"reason_label": reason_label} if reason_label else {}),
                "recorded_at": recorded_at,
                "artifact_id": normalized_artifact_id,
                "source_message_id": str(message.get("message_id") or ""),
                **({"approval_id": approval_id} if approval_id else {}),
                **({"saved_note_path": saved_note_path} if saved_note_path else {}),
            }
            if stored_outcome != "corrected":
                patched.pop("candidate_confirmation_record", None)
                patched.pop("candidate_review_record", None)
            if stored_outcome == "accepted_as_is":
                patched.pop("content_reason_record", None)
            normalized = self._normalize_message(patched)
            messages[index] = normalized
            updated_message = dict(normalized)

            data["messages"] = messages
            self._save(session_id, data)
            return updated_message

    def record_rejected_content_verdict_for_message(
        self,
        session_id: str,
        *,
        message_id: str,
    ) -> Dict[str, Any] | None:
        normalized_message_id = str(message_id or "").strip()
        if not normalized_message_id:
            raise ValueError("내용 거절을 기록할 메시지 ID가 필요합니다.")

        with self._lock:
            data = self.get_session(session_id)
            messages = data.get("messages", [])
            updated_message: Dict[str, Any] | None = None
            for index, message in enumerate(messages):
                if str(message.get("message_id") or "").strip() != normalized_message_id:
                    continue

                if (
                    message.get("role") != "assistant"
                    or str(message.get("artifact_kind") or "").strip() != "grounded_brief"
                    or not isinstance(message.get("original_response_snapshot"), dict)
                ):
                    raise ValueError("내용 거절을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

                artifact_id = str(message.get("artifact_id") or "").strip()
                if not artifact_id:
                    raise ValueError("내용 거절을 기록할 grounded-brief artifact anchor를 찾지 못했습니다.")

                existing_outcome = self._normalize_corrected_outcome(
                    message.get("corrected_outcome"),
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if existing_outcome is not None and existing_outcome.get("outcome") == "rejected":
                    raise ValueError("이미 내용 거절로 기록된 grounded-brief 원문 응답입니다.")

                recorded_at = self._now()
                patched = dict(message)
                patched["corrected_outcome"] = {
                    "outcome": "rejected",
                    "recorded_at": recorded_at,
                    "artifact_id": artifact_id,
                    "source_message_id": normalized_message_id,
                }
                patched["content_reason_record"] = {
                    "reason_scope": ContentReasonScope.CONTENT_REJECT,
                    "reason_label": ContentReasonLabel.EXPLICIT_CONTENT_REJECTION,
                    "recorded_at": recorded_at,
                    "artifact_id": artifact_id,
                    "artifact_kind": "grounded_brief",
                    "source_message_id": normalized_message_id,
                }
                patched.pop("candidate_confirmation_record", None)
                patched.pop("candidate_review_record", None)
                normalized = self._normalize_message(patched)
                messages[index] = normalized
                updated_message = dict(normalized)
                break

            if updated_message is None:
                return None

            data["messages"] = messages
            self._save(session_id, data)
            return updated_message

    def record_content_reason_note_for_message(
        self,
        session_id: str,
        *,
        message_id: str,
        reason_note: str,
    ) -> Dict[str, Any] | None:
        normalized_message_id = str(message_id or "").strip()
        normalized_reason_note = self._normalize_multiline_text(reason_note)
        if not normalized_message_id:
            raise ValueError("거절 메모를 기록할 메시지 ID가 필요합니다.")
        if normalized_reason_note is None:
            raise ValueError("거절 메모를 입력해 주세요.")

        with self._lock:
            data = self.get_session(session_id)
            messages = data.get("messages", [])
            updated_message: Dict[str, Any] | None = None
            for index, message in enumerate(messages):
                if str(message.get("message_id") or "").strip() != normalized_message_id:
                    continue

                if (
                    message.get("role") != "assistant"
                    or str(message.get("artifact_kind") or "").strip() != "grounded_brief"
                    or not isinstance(message.get("original_response_snapshot"), dict)
                ):
                    raise ValueError("거절 메모를 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

                artifact_id = str(message.get("artifact_id") or "").strip()
                if not artifact_id:
                    raise ValueError("거절 메모를 기록할 grounded-brief artifact anchor를 찾지 못했습니다.")

                existing_outcome = self._normalize_corrected_outcome(
                    message.get("corrected_outcome"),
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if existing_outcome is None or existing_outcome.get("outcome") != "rejected":
                    raise ValueError("현재 내용 거절로 기록된 grounded-brief 원문 응답에서만 거절 메모를 남길 수 있습니다.")

                existing_reason_record = self._normalize_content_reason_record(
                    message.get("content_reason_record"),
                    fallback_artifact_id=artifact_id,
                    fallback_artifact_kind="grounded_brief",
                    fallback_source_message_id=normalized_message_id,
                )
                if existing_reason_record is None:
                    raise ValueError("거절 메모를 연결할 content reason record를 찾지 못했습니다.")

                patched = dict(message)
                patched["content_reason_record"] = {
                    "reason_scope": str(existing_reason_record.get("reason_scope") or ContentReasonScope.CONTENT_REJECT),
                    "reason_label": str(
                        existing_reason_record.get("reason_label") or ContentReasonLabel.EXPLICIT_CONTENT_REJECTION
                    ),
                    "reason_note": normalized_reason_note,
                    "recorded_at": self._now(),
                    "artifact_id": artifact_id,
                    "artifact_kind": str(existing_reason_record.get("artifact_kind") or "grounded_brief"),
                    "source_message_id": normalized_message_id,
                }
                normalized = self._normalize_message(patched)
                messages[index] = normalized
                updated_message = dict(normalized)
                break

            if updated_message is None:
                return None

            data["messages"] = messages
            self._save(session_id, data)
            return updated_message

    def record_content_reason_label_for_message(
        self,
        session_id: str,
        *,
        message_id: str,
        reason_label: str,
    ) -> Dict[str, Any] | None:
        normalized_message_id = str(message_id or "").strip()
        normalized_reason_label = str(reason_label or "").strip()
        if not normalized_message_id:
            raise ValueError("레이블을 기록할 메시지 ID가 필요합니다.")
        allowed = ALLOWED_CONTENT_REASON_LABELS.get(ContentReasonScope.CONTENT_REJECT, frozenset())
        if normalized_reason_label not in allowed:
            raise ValueError(f"허용되지 않은 reason_label: {normalized_reason_label!r}")

        with self._lock:
            data = self.get_session(session_id)
            messages = data.get("messages", [])
            updated_message: Dict[str, Any] | None = None
            for index, message in enumerate(messages):
                if str(message.get("message_id") or "").strip() != normalized_message_id:
                    continue

                if (
                    message.get("role") != "assistant"
                    or str(message.get("artifact_kind") or "").strip() != "grounded_brief"
                    or not isinstance(message.get("original_response_snapshot"), dict)
                ):
                    raise ValueError("레이블을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

                artifact_id = str(message.get("artifact_id") or "").strip()
                if not artifact_id:
                    raise ValueError("레이블을 기록할 grounded-brief artifact anchor를 찾지 못했습니다.")

                existing_outcome = self._normalize_corrected_outcome(
                    message.get("corrected_outcome"),
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if existing_outcome is None or existing_outcome.get("outcome") != "rejected":
                    raise ValueError("현재 내용 거절로 기록된 grounded-brief 원문 응답에서만 레이블을 변경할 수 있습니다.")

                existing_reason_record = self._normalize_content_reason_record(
                    message.get("content_reason_record"),
                    fallback_artifact_id=artifact_id,
                    fallback_artifact_kind="grounded_brief",
                    fallback_source_message_id=normalized_message_id,
                )
                if existing_reason_record is None:
                    raise ValueError("레이블을 연결할 content reason record를 찾지 못했습니다.")

                patched = dict(message)
                patched["content_reason_record"] = {
                    "reason_scope": str(existing_reason_record.get("reason_scope") or ContentReasonScope.CONTENT_REJECT),
                    "reason_label": normalized_reason_label,
                    "reason_note": existing_reason_record.get("reason_note"),
                    "recorded_at": self._now(),
                    "artifact_id": artifact_id,
                    "artifact_kind": str(existing_reason_record.get("artifact_kind") or "grounded_brief"),
                    "source_message_id": normalized_message_id,
                }
                normalized = self._normalize_message(patched)
                messages[index] = normalized
                updated_message = dict(normalized)
                break

            if updated_message is None:
                return None

            data["messages"] = messages
            self._save(session_id, data)
            return updated_message

    def record_candidate_confirmation_for_message(
        self,
        session_id: str,
        *,
        message_id: str,
        candidate_confirmation_record: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        normalized_message_id = str(message_id or "").strip()
        if not normalized_message_id:
            raise ValueError("재사용 확인을 기록할 메시지 ID가 필요합니다.")

        with self._lock:
            data = self.get_session(session_id)
            messages = data.get("messages", [])
            updated_message: Dict[str, Any] | None = None
            for index, message in enumerate(messages):
                if str(message.get("message_id") or "").strip() != normalized_message_id:
                    continue

                if (
                    message.get("role") != "assistant"
                    or str(message.get("artifact_kind") or "").strip() != "grounded_brief"
                    or not isinstance(message.get("original_response_snapshot"), dict)
                ):
                    raise ValueError("재사용 확인을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

                artifact_id = str(message.get("artifact_id") or "").strip()
                if not artifact_id:
                    raise ValueError("재사용 확인을 기록할 grounded-brief artifact anchor를 찾지 못했습니다.")

                corrected_outcome = self._normalize_corrected_outcome(
                    message.get("corrected_outcome"),
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if corrected_outcome is None or corrected_outcome.get("outcome") != "corrected":
                    raise ValueError("현재 재사용 확인을 기록할 session-local candidate가 없습니다.")

                original_draft_text = self._normalize_multiline_text(
                    (message.get("original_response_snapshot") or {}).get("draft_text")
                )
                corrected_text = self._normalize_multiline_text(message.get("corrected_text"))
                if original_draft_text is None or corrected_text is None or original_draft_text == corrected_text:
                    raise ValueError("현재 재사용 확인을 기록할 session-local candidate가 없습니다.")

                normalized_record = self._normalize_candidate_confirmation_record(
                    candidate_confirmation_record,
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if normalized_record is None:
                    raise ValueError("candidate confirmation record 형식이 올바르지 않습니다.")
                if normalized_record.get("artifact_id") != artifact_id or normalized_record.get("source_message_id") != normalized_message_id:
                    raise ValueError("candidate confirmation anchor가 현재 source message와 일치하지 않습니다.")
                if normalized_record.get("candidate_updated_at") != str(corrected_outcome.get("recorded_at") or "").strip():
                    raise ValueError("candidate confirmation이 현재 corrected pair와 일치하지 않습니다.")

                existing_record = self._normalize_candidate_confirmation_record(
                    message.get("candidate_confirmation_record"),
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if (
                    existing_record is not None
                    and existing_record.get("candidate_id") == normalized_record.get("candidate_id")
                    and existing_record.get("candidate_updated_at") == normalized_record.get("candidate_updated_at")
                ):
                    raise ValueError("이미 현재 수정 방향 재사용 확인이 기록되어 있습니다.")

                patched = dict(message)
                patched["candidate_confirmation_record"] = normalized_record
                normalized = self._normalize_message(patched)
                messages[index] = normalized
                updated_message = dict(normalized)
                break

            if updated_message is None:
                return None

            data["messages"] = messages
            self._save(session_id, data)
            return updated_message

    def record_candidate_review_for_message(
        self,
        session_id: str,
        *,
        message_id: str,
        candidate_review_record: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        normalized_message_id = str(message_id or "").strip()
        if not normalized_message_id:
            raise ValueError("검토 수락을 기록할 메시지 ID가 필요합니다.")

        with self._lock:
            data = self.get_session(session_id)
            messages = data.get("messages", [])
            updated_message: Dict[str, Any] | None = None
            for index, message in enumerate(messages):
                if str(message.get("message_id") or "").strip() != normalized_message_id:
                    continue

                if (
                    message.get("role") != "assistant"
                    or str(message.get("artifact_kind") or "").strip() != "grounded_brief"
                    or not isinstance(message.get("original_response_snapshot"), dict)
                ):
                    raise ValueError("검토 수락을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

                artifact_id = str(message.get("artifact_id") or "").strip()
                if not artifact_id:
                    raise ValueError("검토 수락을 기록할 grounded-brief artifact anchor를 찾지 못했습니다.")

                corrected_outcome = self._normalize_corrected_outcome(
                    message.get("corrected_outcome"),
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if corrected_outcome is None or corrected_outcome.get("outcome") != "corrected":
                    raise ValueError("현재 검토 수락을 기록할 durable candidate가 없습니다.")

                original_draft_text = self._normalize_multiline_text(
                    (message.get("original_response_snapshot") or {}).get("draft_text")
                )
                corrected_text = self._normalize_multiline_text(message.get("corrected_text"))
                if original_draft_text is None or corrected_text is None or original_draft_text == corrected_text:
                    raise ValueError("현재 검토 수락을 기록할 durable candidate가 없습니다.")

                current_confirmation_record = self._normalize_candidate_confirmation_record(
                    message.get("candidate_confirmation_record"),
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if current_confirmation_record is None:
                    raise ValueError("현재 검토 수락을 기록할 durable candidate가 없습니다.")

                normalized_record = self._normalize_candidate_review_record(
                    candidate_review_record,
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if normalized_record is None:
                    raise ValueError("candidate review record 형식이 올바르지 않습니다.")
                if normalized_record.get("artifact_id") != artifact_id or normalized_record.get("source_message_id") != normalized_message_id:
                    raise ValueError("candidate review anchor가 현재 source message와 일치하지 않습니다.")

                current_candidate_updated_at = str(corrected_outcome.get("recorded_at") or "").strip()
                if (
                    normalized_record.get("candidate_updated_at") != current_candidate_updated_at
                    or current_confirmation_record.get("candidate_id") != normalized_record.get("candidate_id")
                    or current_confirmation_record.get("candidate_updated_at") != current_candidate_updated_at
                ):
                    raise ValueError("현재 검토 후보가 바뀌어 검토 수락 대상을 다시 불러와야 합니다.")

                existing_record = self._normalize_candidate_review_record(
                    message.get("candidate_review_record"),
                    fallback_artifact_id=artifact_id,
                    fallback_source_message_id=normalized_message_id,
                )
                if (
                    existing_record is not None
                    and existing_record.get("candidate_id") == normalized_record.get("candidate_id")
                    and existing_record.get("candidate_updated_at") == normalized_record.get("candidate_updated_at")
                ):
                    raise ValueError("이미 현재 검토 수락이 기록되어 있습니다.")

                patched = dict(message)
                patched["candidate_review_record"] = normalized_record
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
            artifact_source_message_ids = self._build_artifact_source_message_ids(data.get("messages", []))
            normalized_approval = self._normalize_approval_record(
                approval,
                include_note_text=True,
                artifact_source_message_ids=artifact_source_message_ids,
            )
            if normalized_approval is None:
                return
            pending = data.get("pending_approvals", [])
            pending.append(normalized_approval)
            data["pending_approvals"] = pending
            self._save(session_id, data)

    def record_operator_action_request(
        self, session_id: str, action_contract: Dict[str, Any]
    ) -> str:
        approval_id = str(uuid4())
        record: Dict[str, Any] = {
            "approval_id": approval_id,
            "kind": "operator_action",
            "status": "pending",
        }
        for field in (
            "action_kind", "target_id", "content", "requested_at",
            "audit_trace_required", "is_reversible",
        ):
            if field in action_contract:
                record[field] = action_contract[field]
        with self._lock:
            data = self.get_session(session_id)
            pending = data.get("pending_approvals", [])
            pending.append(record)
            data["pending_approvals"] = pending
            self._save(session_id, data)
        return approval_id

    def record_operator_action_outcome(
        self, session_id: str, record: Dict[str, Any]
    ) -> None:
        with self._lock:
            data = self.get_session(session_id)
            outcome = dict(record)
            outcome.setdefault("status", "executed")
            outcome["completed_at"] = self._now()
            history = data.get("operator_action_history", [])
            history.append(outcome)
            data["operator_action_history"] = history
            self._save(session_id, data)

    def get_operator_action_from_history(
        self, session_id: str, approval_id: str
    ) -> Dict[str, Any] | None:
        with self._lock:
            data = self.get_session(session_id)
            for entry in data.get("operator_action_history", []):
                if entry.get("approval_id") == approval_id:
                    return dict(entry)
            return None

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
