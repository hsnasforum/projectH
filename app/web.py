from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
import difflib
import hashlib
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import queue
import threading
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from datetime import datetime, timezone
from uuid import uuid4

from app.localization import localize_runtime_status_payload, localize_session, localize_text
from config.settings import AppSettings
from core.agent_loop import AgentLoop, AgentResponse, RequestCancelledError, UserRequest
from core.request_intents import classify_search_intent
from model_adapter.base import ModelAdapterError, ModelRuntimeStatus
from model_adapter.factory import build_model_adapter
from storage.session_store import SessionStore
from storage.task_log import TaskLogger
from storage.web_search_store import WebSearchStore
from tools.file_reader import FileReaderTool
from tools.file_search import FileSearchTool
from tools.web_search import WebSearchTool
from tools.write_note import WriteNoteTool


DEFAULT_SESSION_ID = "demo-session"


@dataclass(slots=True)
class WebApiError(RuntimeError):
    status_code: int
    message: str

    def __str__(self) -> str:
        return self.message


class WebAppService:
    def __init__(
        self,
        settings: AppSettings,
        *,
        template_path: str | None = None,
    ) -> None:
        self.settings = settings
        self.session_store = SessionStore(base_dir=settings.sessions_dir)
        self.task_logger = TaskLogger(path=settings.task_log_path)
        self.web_search_store = WebSearchStore(base_dir=settings.web_search_history_dir)
        self.template_path = Path(template_path) if template_path else Path(__file__).with_name("templates") / "index.html"
        self._active_stream_requests: dict[str, threading.Event] = {}
        self._active_stream_lock = threading.Lock()

    def render_index(self) -> str:
        template = self.template_path.read_text(encoding="utf-8")
        default_model = self.settings.ollama_model if self.settings.model_provider == "ollama" else ""
        default_model_label = default_model or "선택형 로컬 모델"
        default_web_search_permission = self._normalize_web_search_permission(self.settings.web_search_permission)
        return (
            template.replace("__APP_NAME__", self.settings.app_name)
            .replace("__DEFAULT_PROVIDER__", self.settings.model_provider)
            .replace("__DEFAULT_MODEL__", default_model)
            .replace("__DEFAULT_MODEL_LABEL__", default_model_label)
            .replace("__DEFAULT_BASE_URL__", self.settings.ollama_base_url)
            .replace("__DEFAULT_SESSION_ID__", DEFAULT_SESSION_ID)
            .replace("__DEFAULT_WEB_SEARCH_PERMISSION__", default_web_search_permission)
            .replace("__DEFAULT_WEB_SEARCH_PERMISSION_LABEL__", self._web_search_permission_label(default_web_search_permission))
        )

    def get_config(self) -> dict[str, Any]:
        default_model = self.settings.ollama_model if self.settings.model_provider == "ollama" else ""
        default_web_search_permission = self._normalize_web_search_permission(self.settings.web_search_permission)
        return {
            "ok": True,
            "app_name": self.settings.app_name,
            "default_session_id": DEFAULT_SESSION_ID,
            "default_provider": self.settings.model_provider,
            "default_model": default_model,
            "default_model_label": default_model or "선택형 로컬 모델",
            "default_base_url": self.settings.ollama_base_url,
            "default_web_search_permission": default_web_search_permission,
            "default_web_search_permission_label": self._web_search_permission_label(default_web_search_permission),
            "web_search_tool_connected": True,
            "web_host": self.settings.web_host,
            "web_port": self.settings.web_port,
            "notes_dir": self.settings.notes_dir,
        }

    def list_sessions_payload(self) -> dict[str, Any]:
        sessions = self.session_store.list_sessions()
        for item in sessions:
            preview = item.get("last_message_preview")
            if isinstance(preview, str):
                item["last_message_preview"] = localize_text(preview)
        return {
            "ok": True,
            "sessions": sessions,
        }

    def get_session_payload(self, session_id: str | None) -> dict[str, Any]:
        normalized = self._normalize_session_id(session_id)
        return {
            "ok": True,
            "session": self._serialize_session(self.session_store.get_session(normalized)),
        }

    def submit_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        message_id = self._normalize_optional_text(payload.get("message_id"))
        feedback_label = self._normalize_feedback_label(payload.get("feedback_label"))
        feedback_reason = self._normalize_feedback_reason(payload.get("feedback_reason"))

        if not message_id:
            raise WebApiError(400, "피드백을 남길 메시지 ID가 필요합니다.")
        if not feedback_label:
            raise WebApiError(400, "피드백 종류는 helpful, unclear, incorrect 중 하나여야 합니다.")

        updated_message = self.session_store.update_message(
            session_id,
            message_id,
            {"feedback": {"label": feedback_label, **({"reason": feedback_reason} if feedback_reason else {})}},
        )
        if updated_message is None:
            raise WebApiError(404, "피드백을 남길 비서 메시지를 찾지 못했습니다.")

        self.task_logger.log(
            session_id=session_id,
            action="response_feedback_recorded",
            detail={
                "message_id": message_id,
                "artifact_id": updated_message.get("artifact_id"),
                "artifact_kind": updated_message.get("artifact_kind"),
                "feedback_label": feedback_label,
                "feedback_reason": feedback_reason,
            },
        )
        return {
            "ok": True,
            "message_id": message_id,
            "feedback_label": feedback_label,
            "feedback_reason": feedback_reason,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def submit_correction(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        message_id = self._normalize_optional_text(payload.get("message_id"))
        corrected_text = payload.get("corrected_text")

        if not message_id:
            raise WebApiError(400, "교정할 메시지 ID가 필요합니다.")
        if not isinstance(corrected_text, str):
            raise WebApiError(400, "수정 텍스트를 문자열로 보내 주세요.")

        try:
            updated_message = self.session_store.record_correction_for_message(
                session_id,
                message_id=message_id,
                corrected_text=corrected_text,
            )
        except ValueError as exc:
            raise WebApiError(400, str(exc)) from exc

        if updated_message is None:
            raise WebApiError(404, "교정할 grounded-brief 원문 응답을 찾지 못했습니다.")

        corrected_outcome = self._serialize_corrected_outcome(updated_message.get("corrected_outcome"))
        serialized_corrected_text = self._serialize_corrected_text(updated_message.get("corrected_text"))
        self.task_logger.log(
            session_id=session_id,
            action="correction_submitted",
            detail={
                "message_id": message_id,
                "artifact_id": updated_message.get("artifact_id"),
                "artifact_kind": updated_message.get("artifact_kind"),
                "source_message_id": corrected_outcome.get("source_message_id") if corrected_outcome else message_id,
                "corrected_text_length": len(serialized_corrected_text or ""),
            },
        )
        if corrected_outcome is not None:
            self.task_logger.log(
                session_id=session_id,
                action="corrected_outcome_recorded",
                detail={
                    "outcome": corrected_outcome.get("outcome"),
                    "recorded_at": corrected_outcome.get("recorded_at"),
                    "artifact_id": corrected_outcome.get("artifact_id"),
                    "source_message_id": corrected_outcome.get("source_message_id"),
                    "approval_id": corrected_outcome.get("approval_id"),
                    "saved_note_path": corrected_outcome.get("saved_note_path"),
                    "corrected_text_length": len(serialized_corrected_text or ""),
                },
            )

        return {
            "ok": True,
            "message_id": message_id,
            "artifact_id": str(updated_message.get("artifact_id") or "").strip() or None,
            "corrected_text": serialized_corrected_text,
            "corrected_outcome": corrected_outcome,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def submit_content_verdict(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        message_id = self._normalize_optional_text(payload.get("message_id"))
        content_verdict = self._normalize_content_verdict(payload.get("content_verdict"))

        if not message_id:
            raise WebApiError(400, "내용 판정을 기록할 메시지 ID가 필요합니다.")
        if content_verdict != "rejected":
            raise WebApiError(400, "현재 content verdict는 rejected만 지원합니다.")

        try:
            updated_message = self.session_store.record_rejected_content_verdict_for_message(
                session_id,
                message_id=message_id,
            )
        except ValueError as exc:
            raise WebApiError(400, str(exc)) from exc

        if updated_message is None:
            raise WebApiError(404, "내용 판정을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

        corrected_outcome = self._serialize_corrected_outcome(updated_message.get("corrected_outcome"))
        content_reason_record = self._serialize_content_reason_record(updated_message.get("content_reason_record"))
        self.task_logger.log(
            session_id=session_id,
            action="content_verdict_recorded",
            detail={
                "message_id": message_id,
                "artifact_id": updated_message.get("artifact_id"),
                "artifact_kind": updated_message.get("artifact_kind"),
                "source_message_id": corrected_outcome.get("source_message_id") if corrected_outcome else message_id,
                "content_verdict": content_verdict,
                "content_reason_record": content_reason_record,
            },
        )
        if corrected_outcome is not None:
            self.task_logger.log(
                session_id=session_id,
                action="corrected_outcome_recorded",
                detail={
                    "outcome": corrected_outcome.get("outcome"),
                    "recorded_at": corrected_outcome.get("recorded_at"),
                    "artifact_id": corrected_outcome.get("artifact_id"),
                    "source_message_id": corrected_outcome.get("source_message_id"),
                    "approval_id": corrected_outcome.get("approval_id"),
                    "saved_note_path": corrected_outcome.get("saved_note_path"),
                    "content_reason_record": content_reason_record,
                },
            )

        return {
            "ok": True,
            "message_id": message_id,
            "artifact_id": str(updated_message.get("artifact_id") or "").strip() or None,
            "content_verdict": content_verdict,
            "corrected_outcome": corrected_outcome,
            "content_reason_record": content_reason_record,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def submit_content_reason_note(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        message_id = self._normalize_optional_text(payload.get("message_id"))
        reason_note = self._normalize_optional_text(payload.get("reason_note"))

        if not message_id:
            raise WebApiError(400, "거절 메모를 기록할 메시지 ID가 필요합니다.")
        if reason_note is None:
            raise WebApiError(400, "거절 메모를 입력해 주세요.")

        try:
            updated_message = self.session_store.record_content_reason_note_for_message(
                session_id,
                message_id=message_id,
                reason_note=reason_note,
            )
        except ValueError as exc:
            raise WebApiError(400, str(exc)) from exc

        if updated_message is None:
            raise WebApiError(404, "거절 메모를 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

        corrected_outcome = self._serialize_corrected_outcome(updated_message.get("corrected_outcome"))
        content_reason_record = self._serialize_content_reason_record(updated_message.get("content_reason_record"))
        self.task_logger.log(
            session_id=session_id,
            action="content_reason_note_recorded",
            detail={
                "message_id": message_id,
                "artifact_id": updated_message.get("artifact_id"),
                "artifact_kind": updated_message.get("artifact_kind"),
                "source_message_id": (
                    content_reason_record.get("source_message_id")
                    if content_reason_record
                    else corrected_outcome.get("source_message_id") if corrected_outcome else message_id
                ),
                "reason_scope": content_reason_record.get("reason_scope") if content_reason_record else "content_reject",
                "reason_label": (
                    content_reason_record.get("reason_label")
                    if content_reason_record
                    else "explicit_content_rejection"
                ),
                "reason_note": content_reason_record.get("reason_note") if content_reason_record else reason_note,
                "content_reason_record": content_reason_record,
            },
        )

        return {
            "ok": True,
            "message_id": message_id,
            "artifact_id": str(updated_message.get("artifact_id") or "").strip() or None,
            "content_verdict": corrected_outcome.get("outcome") if corrected_outcome else None,
            "corrected_outcome": corrected_outcome,
            "content_reason_record": content_reason_record,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def submit_candidate_confirmation(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        message_id = self._normalize_optional_text(payload.get("message_id"))
        candidate_id = self._normalize_optional_text(payload.get("candidate_id"))
        candidate_updated_at = self._normalize_optional_text(payload.get("candidate_updated_at"))

        if not message_id:
            raise WebApiError(400, "재사용 확인을 기록할 메시지 ID가 필요합니다.")
        if not candidate_id or not candidate_updated_at:
            raise WebApiError(400, "현재 session-local candidate 정보가 필요합니다.")

        session = self.session_store.get_session(session_id)
        source_message = None
        for message in reversed(session.get("messages", [])):
            if str(message.get("message_id") or "").strip() != message_id:
                continue
            source_message = dict(message)
            break
        if source_message is None:
            raise WebApiError(404, "재사용 확인을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

        session_local_memory_signal = self.session_store.build_session_local_memory_signal(
            session,
            source_message=source_message,
        )
        current_candidate = self._build_session_local_candidate_for_message(
            message=source_message,
            session_local_memory_signal=session_local_memory_signal,
        )
        if not isinstance(current_candidate, dict):
            raise WebApiError(400, "현재 재사용 확인을 기록할 session-local candidate가 없습니다.")
        if (
            str(current_candidate.get("candidate_id") or "").strip() != candidate_id
            or str(current_candidate.get("updated_at") or "").strip() != candidate_updated_at
        ):
            raise WebApiError(409, "현재 수정 방향이 바뀌어 재사용 확인 대상을 다시 불러와야 합니다.")

        try:
            updated_message = self.session_store.record_candidate_confirmation_for_message(
                session_id,
                message_id=message_id,
                candidate_confirmation_record={
                    "candidate_id": candidate_id,
                    "candidate_family": current_candidate.get("candidate_family"),
                    "candidate_updated_at": candidate_updated_at,
                    "artifact_id": source_message.get("artifact_id"),
                    "source_message_id": source_message.get("message_id"),
                    "confirmation_scope": "candidate_reuse",
                    "confirmation_label": "explicit_reuse_confirmation",
                },
            )
        except ValueError as exc:
            raise WebApiError(400, str(exc)) from exc

        if updated_message is None:
            raise WebApiError(404, "재사용 확인을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

        candidate_confirmation_record = self._serialize_candidate_confirmation_record(
            updated_message.get("candidate_confirmation_record")
        )
        if candidate_confirmation_record is None:
            raise WebApiError(500, "candidate confirmation record를 직렬화하지 못했습니다.")

        self.task_logger.log(
            session_id=session_id,
            action="candidate_confirmation_recorded",
            detail={
                "message_id": message_id,
                "artifact_id": updated_message.get("artifact_id"),
                "source_message_id": candidate_confirmation_record.get("source_message_id"),
                "candidate_id": candidate_confirmation_record.get("candidate_id"),
                "candidate_family": candidate_confirmation_record.get("candidate_family"),
                "candidate_updated_at": candidate_confirmation_record.get("candidate_updated_at"),
                "confirmation_scope": candidate_confirmation_record.get("confirmation_scope"),
                "confirmation_label": candidate_confirmation_record.get("confirmation_label"),
            },
        )

        return {
            "ok": True,
            "message_id": message_id,
            "artifact_id": str(updated_message.get("artifact_id") or "").strip() or None,
            "candidate_id": candidate_id,
            "candidate_confirmation_record": candidate_confirmation_record,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def submit_candidate_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        message_id = self._normalize_optional_text(payload.get("message_id"))
        candidate_id = self._normalize_optional_text(payload.get("candidate_id"))
        candidate_updated_at = self._normalize_optional_text(payload.get("candidate_updated_at"))
        review_action = self._normalize_optional_text(payload.get("review_action"))

        if not message_id:
            raise WebApiError(400, "검토 수락을 기록할 메시지 ID가 필요합니다.")
        if review_action != "accept":
            raise WebApiError(400, "현재 review action은 검토 수락만 지원합니다.")
        if not candidate_id or not candidate_updated_at:
            raise WebApiError(400, "현재 durable candidate 정보가 필요합니다.")

        session = self.session_store.get_session(session_id)
        source_message = None
        for message in reversed(session.get("messages", [])):
            if str(message.get("message_id") or "").strip() != message_id:
                continue
            source_message = dict(message)
            break
        if source_message is None:
            raise WebApiError(404, "검토 수락을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

        session_local_memory_signal = self.session_store.build_session_local_memory_signal(
            session,
            source_message=source_message,
        )
        current_session_local_candidate = self._build_session_local_candidate_for_message(
            message=source_message,
            session_local_memory_signal=session_local_memory_signal,
        )
        candidate_confirmation_record = self._serialize_candidate_confirmation_record(
            self._resolve_candidate_confirmation_record_for_message(
                message=source_message,
                session_local_candidate=current_session_local_candidate,
            )
        )
        session_local_candidate = self._serialize_session_local_candidate(current_session_local_candidate)
        durable_candidate = self._serialize_durable_candidate(
            self._build_durable_candidate_for_message(
                session_local_candidate=session_local_candidate,
                candidate_confirmation_record=candidate_confirmation_record,
            )
        )
        if durable_candidate is None:
            raise WebApiError(400, "현재 검토 수락을 기록할 durable candidate가 없습니다.")

        current_candidate_updated_at = ""
        for raw_ref in durable_candidate.get("supporting_confirmation_refs", []):
            if not isinstance(raw_ref, dict):
                continue
            if str(raw_ref.get("candidate_id") or "").strip() != durable_candidate.get("candidate_id"):
                continue
            current_candidate_updated_at = str(raw_ref.get("candidate_updated_at") or "").strip()
            if current_candidate_updated_at:
                break
        if (
            str(durable_candidate.get("candidate_id") or "").strip() != candidate_id
            or not current_candidate_updated_at
            or current_candidate_updated_at != candidate_updated_at
        ):
            raise WebApiError(409, "현재 검토 후보가 바뀌어 검토 수락 대상을 다시 불러와야 합니다.")

        try:
            updated_message = self.session_store.record_candidate_review_for_message(
                session_id,
                message_id=message_id,
                candidate_review_record={
                    "candidate_id": candidate_id,
                    "candidate_updated_at": candidate_updated_at,
                    "artifact_id": source_message.get("artifact_id"),
                    "source_message_id": source_message.get("message_id"),
                    "review_scope": "source_message_candidate_review",
                    "review_action": "accept",
                    "review_status": "accepted",
                },
            )
        except ValueError as exc:
            raise WebApiError(400, str(exc)) from exc

        if updated_message is None:
            raise WebApiError(404, "검토 수락을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

        candidate_review_record = self._serialize_candidate_review_record(updated_message.get("candidate_review_record"))
        if candidate_review_record is None:
            raise WebApiError(500, "candidate review record를 직렬화하지 못했습니다.")

        self.task_logger.log(
            session_id=session_id,
            action="candidate_review_recorded",
            detail={
                "message_id": message_id,
                "artifact_id": updated_message.get("artifact_id"),
                "source_message_id": candidate_review_record.get("source_message_id"),
                "candidate_id": candidate_review_record.get("candidate_id"),
                "candidate_family": durable_candidate.get("candidate_family"),
                "candidate_updated_at": candidate_review_record.get("candidate_updated_at"),
                "review_scope": candidate_review_record.get("review_scope"),
                "review_action": candidate_review_record.get("review_action"),
                "review_status": candidate_review_record.get("review_status"),
            },
        )

        return {
            "ok": True,
            "message_id": message_id,
            "artifact_id": str(updated_message.get("artifact_id") or "").strip() or None,
            "candidate_id": candidate_id,
            "candidate_review_record": candidate_review_record,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def emit_aggregate_transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        aggregate_fingerprint = self._normalize_optional_text(payload.get("aggregate_fingerprint"))
        operator_reason_or_note = self._normalize_optional_text(payload.get("operator_reason_or_note"))

        if not aggregate_fingerprint:
            raise WebApiError(400, "transition record를 발행할 aggregate fingerprint가 필요합니다.")
        if not operator_reason_or_note:
            raise WebApiError(400, "transition record를 발행하려면 사유를 입력해야 합니다.")

        session = self.session_store.get_session(session_id)
        serialized = self._serialize_session(session)
        aggregates = serialized.get("recurrence_aggregate_candidates") or []
        target_aggregate = None
        for agg in aggregates:
            agg_key = agg.get("aggregate_key") or {}
            if str(agg_key.get("normalized_delta_fingerprint") or "").strip() == aggregate_fingerprint:
                target_aggregate = agg
                break
        if target_aggregate is None:
            raise WebApiError(404, "해당 fingerprint의 aggregate를 찾지 못했습니다.")

        capability_outcome = str(
            (target_aggregate.get("reviewed_memory_capability_status") or {}).get("capability_outcome") or ""
        ).strip()
        if capability_outcome != "unblocked_all_required":
            raise WebApiError(400, "현재 aggregate의 capability가 unblocked 상태가 아닙니다.")

        audit_contract = target_aggregate.get("reviewed_memory_transition_audit_contract")
        if not isinstance(audit_contract, dict):
            raise WebApiError(400, "현재 aggregate에 transition audit contract가 없습니다.")

        now = datetime.now(timezone.utc).isoformat()
        canonical_transition_id = f"transition-local-{uuid4().hex[:12]}"

        transition_record = {
            "transition_record_version": "first_reviewed_memory_transition_record_v1",
            "canonical_transition_id": canonical_transition_id,
            "transition_action": "future_reviewed_memory_apply",
            "aggregate_identity_ref": dict(target_aggregate.get("aggregate_key") or {}),
            "supporting_source_message_refs": list(target_aggregate.get("supporting_source_message_refs") or []),
            "supporting_candidate_refs": list(target_aggregate.get("supporting_candidate_refs") or []),
            "operator_reason_or_note": operator_reason_or_note,
            "record_stage": "emitted_record_only_not_applied",
            "task_log_mirror_relation": "mirror_allowed_not_canonical",
            "emitted_at": now,
        }
        supporting_review_refs = target_aggregate.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            transition_record["supporting_review_refs"] = list(supporting_review_refs)

        existing_records = session.get("reviewed_memory_emitted_transition_records")
        if not isinstance(existing_records, list):
            existing_records = []
        existing_records.append(transition_record)
        session["reviewed_memory_emitted_transition_records"] = existing_records
        self.session_store._save(session_id, session)

        self.task_logger.log(
            session_id=session_id,
            action="reviewed_memory_transition_emitted",
            detail={
                "canonical_transition_id": canonical_transition_id,
                "transition_action": "future_reviewed_memory_apply",
                "aggregate_fingerprint": aggregate_fingerprint,
                "operator_reason_or_note": operator_reason_or_note,
                "record_stage": "emitted_record_only_not_applied",
                "emitted_at": now,
            },
        )

        return {
            "ok": True,
            "canonical_transition_id": canonical_transition_id,
            "transition_record": transition_record,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def apply_aggregate_transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        aggregate_fingerprint = self._normalize_optional_text(payload.get("aggregate_fingerprint"))
        canonical_transition_id = self._normalize_optional_text(payload.get("canonical_transition_id"))

        if not aggregate_fingerprint:
            raise WebApiError(400, "적용할 aggregate fingerprint가 필요합니다.")
        if not canonical_transition_id:
            raise WebApiError(400, "적용할 transition record의 canonical_transition_id가 필요합니다.")

        session = self.session_store.get_session(session_id)
        existing_records = session.get("reviewed_memory_emitted_transition_records")
        if not isinstance(existing_records, list):
            raise WebApiError(404, "발행된 transition record가 없습니다.")

        target_record = None
        for record in existing_records:
            if not isinstance(record, dict):
                continue
            if str(record.get("canonical_transition_id") or "").strip() != canonical_transition_id:
                continue
            rec_identity = record.get("aggregate_identity_ref")
            if not isinstance(rec_identity, dict):
                continue
            if str(rec_identity.get("normalized_delta_fingerprint") or "").strip() != aggregate_fingerprint:
                continue
            target_record = record
            break

        if target_record is None:
            raise WebApiError(404, "해당 transition record를 찾지 못했습니다.")
        if str(target_record.get("record_stage") or "").strip() != "emitted_record_only_not_applied":
            raise WebApiError(400, "이미 적용된 transition record입니다.")

        now = datetime.now(timezone.utc).isoformat()
        target_record["record_stage"] = "applied_pending_result"
        target_record["applied_at"] = now
        self.session_store._save(session_id, session)

        self.task_logger.log(
            session_id=session_id,
            action="reviewed_memory_transition_applied",
            detail={
                "canonical_transition_id": canonical_transition_id,
                "transition_action": str(target_record.get("transition_action") or ""),
                "aggregate_fingerprint": aggregate_fingerprint,
                "record_stage": "applied_pending_result",
                "applied_at": now,
            },
        )

        return {
            "ok": True,
            "canonical_transition_id": canonical_transition_id,
            "transition_record": dict(target_record),
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def confirm_aggregate_transition_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        aggregate_fingerprint = self._normalize_optional_text(payload.get("aggregate_fingerprint"))
        canonical_transition_id = self._normalize_optional_text(payload.get("canonical_transition_id"))

        if not aggregate_fingerprint:
            raise WebApiError(400, "결과를 확정할 aggregate fingerprint가 필요합니다.")
        if not canonical_transition_id:
            raise WebApiError(400, "결과를 확정할 transition record의 canonical_transition_id가 필요합니다.")

        session = self.session_store.get_session(session_id)
        existing_records = session.get("reviewed_memory_emitted_transition_records")
        if not isinstance(existing_records, list):
            raise WebApiError(404, "발행된 transition record가 없습니다.")

        target_record = None
        for record in existing_records:
            if not isinstance(record, dict):
                continue
            if str(record.get("canonical_transition_id") or "").strip() != canonical_transition_id:
                continue
            rec_identity = record.get("aggregate_identity_ref")
            if not isinstance(rec_identity, dict):
                continue
            if str(rec_identity.get("normalized_delta_fingerprint") or "").strip() != aggregate_fingerprint:
                continue
            target_record = record
            break

        if target_record is None:
            raise WebApiError(404, "해당 transition record를 찾지 못했습니다.")
        if str(target_record.get("record_stage") or "").strip() != "applied_pending_result":
            raise WebApiError(400, "아직 적용 실행이 완료되지 않았거나 이미 결과가 확정되었습니다.")

        now = datetime.now(timezone.utc).isoformat()
        aggregate_identity_ref = dict(target_record.get("aggregate_identity_ref") or {})
        operator_reason = str(target_record.get("operator_reason_or_note") or "").strip()
        target_record["record_stage"] = "applied_with_result"
        target_record["apply_result"] = {
            "result_version": "first_reviewed_memory_apply_result_v1",
            "applied_effect_kind": "reviewed_memory_correction_pattern",
            "applied_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": aggregate_identity_ref,
            "transition_ref": canonical_transition_id,
            "result_stage": "effect_active",
            "result_at": now,
        }
        target_record["result_at"] = now

        active_effects = session.get("reviewed_memory_active_effects")
        if not isinstance(active_effects, list):
            active_effects = []
        active_effects.append({
            "effect_kind": "reviewed_memory_correction_pattern",
            "aggregate_fingerprint": aggregate_fingerprint,
            "aggregate_identity_ref": aggregate_identity_ref,
            "transition_ref": canonical_transition_id,
            "operator_reason_or_note": operator_reason,
            "activated_at": now,
        })
        session["reviewed_memory_active_effects"] = active_effects
        self.session_store._save(session_id, session)

        self.task_logger.log(
            session_id=session_id,
            action="reviewed_memory_transition_result_confirmed",
            detail={
                "canonical_transition_id": canonical_transition_id,
                "aggregate_fingerprint": aggregate_fingerprint,
                "record_stage": "applied_with_result",
                "applied_effect_kind": "reviewed_memory_correction_pattern",
                "result_stage": "effect_active",
                "result_at": now,
            },
        )

        return {
            "ok": True,
            "canonical_transition_id": canonical_transition_id,
            "transition_record": dict(target_record),
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def stop_apply_aggregate_transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        aggregate_fingerprint = self._normalize_optional_text(payload.get("aggregate_fingerprint"))
        canonical_transition_id = self._normalize_optional_text(payload.get("canonical_transition_id"))

        if not aggregate_fingerprint:
            raise WebApiError(400, "중단할 aggregate fingerprint가 필요합니다.")
        if not canonical_transition_id:
            raise WebApiError(400, "중단할 transition record의 canonical_transition_id가 필요합니다.")

        session = self.session_store.get_session(session_id)

        existing_records = session.get("reviewed_memory_emitted_transition_records")
        if not isinstance(existing_records, list):
            raise WebApiError(404, "발행된 transition record가 없습니다.")
        target_record = None
        for record in existing_records:
            if not isinstance(record, dict):
                continue
            if str(record.get("canonical_transition_id") or "").strip() != canonical_transition_id:
                continue
            target_record = record
            break
        if target_record is None:
            raise WebApiError(404, "해당 transition record를 찾지 못했습니다.")
        if str(target_record.get("record_stage") or "").strip() != "applied_with_result":
            raise WebApiError(400, "적용 결과가 확정된 상태에서만 중단할 수 있습니다.")

        now = datetime.now(timezone.utc).isoformat()
        target_record["record_stage"] = "stopped"
        target_record["stopped_at"] = now
        if isinstance(target_record.get("apply_result"), dict):
            target_record["apply_result"]["result_stage"] = "effect_stopped"

        active_effects = session.get("reviewed_memory_active_effects")
        if isinstance(active_effects, list):
            session["reviewed_memory_active_effects"] = [
                effect for effect in active_effects
                if not isinstance(effect, dict)
                or str(effect.get("transition_ref") or "").strip() != canonical_transition_id
            ]

        self.session_store._save(session_id, session)

        self.task_logger.log(
            session_id=session_id,
            action="reviewed_memory_transition_stopped",
            detail={
                "canonical_transition_id": canonical_transition_id,
                "aggregate_fingerprint": aggregate_fingerprint,
                "record_stage": "stopped",
                "stopped_at": now,
            },
        )

        return {
            "ok": True,
            "canonical_transition_id": canonical_transition_id,
            "transition_record": dict(target_record),
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def reverse_aggregate_transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        aggregate_fingerprint = self._normalize_optional_text(payload.get("aggregate_fingerprint"))
        canonical_transition_id = self._normalize_optional_text(payload.get("canonical_transition_id"))

        if not aggregate_fingerprint:
            raise WebApiError(400, "되돌릴 aggregate fingerprint가 필요합니다.")
        if not canonical_transition_id:
            raise WebApiError(400, "되돌릴 transition record의 canonical_transition_id가 필요합니다.")

        session = self.session_store.get_session(session_id)

        existing_records = session.get("reviewed_memory_emitted_transition_records")
        if not isinstance(existing_records, list):
            raise WebApiError(404, "발행된 transition record가 없습니다.")
        target_record = None
        for record in existing_records:
            if not isinstance(record, dict):
                continue
            if str(record.get("canonical_transition_id") or "").strip() != canonical_transition_id:
                continue
            target_record = record
            break
        if target_record is None:
            raise WebApiError(404, "해당 transition record를 찾지 못했습니다.")
        if str(target_record.get("record_stage") or "").strip() != "stopped":
            raise WebApiError(400, "적용이 중단된 상태에서만 되돌릴 수 있습니다.")

        now = datetime.now(timezone.utc).isoformat()
        target_record["record_stage"] = "reversed"
        target_record["reversed_at"] = now
        if isinstance(target_record.get("apply_result"), dict):
            target_record["apply_result"]["result_stage"] = "effect_reversed"

        self.session_store._save(session_id, session)

        self.task_logger.log(
            session_id=session_id,
            action="reviewed_memory_transition_reversed",
            detail={
                "canonical_transition_id": canonical_transition_id,
                "aggregate_fingerprint": aggregate_fingerprint,
                "record_stage": "reversed",
                "reversed_at": now,
            },
        )

        return {
            "ok": True,
            "canonical_transition_id": canonical_transition_id,
            "transition_record": dict(target_record),
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def check_aggregate_conflict_visibility(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        aggregate_fingerprint = self._normalize_optional_text(payload.get("aggregate_fingerprint"))
        canonical_transition_id = self._normalize_optional_text(payload.get("canonical_transition_id"))

        if not aggregate_fingerprint:
            raise WebApiError(400, "충돌 확인할 aggregate fingerprint가 필요합니다.")
        if not canonical_transition_id:
            raise WebApiError(400, "충돌 확인할 transition record의 canonical_transition_id가 필요합니다.")

        session = self.session_store.get_session(session_id)

        existing_records = session.get("reviewed_memory_emitted_transition_records")
        if not isinstance(existing_records, list):
            raise WebApiError(404, "발행된 transition record가 없습니다.")
        target_record = None
        for record in existing_records:
            if not isinstance(record, dict):
                continue
            if str(record.get("canonical_transition_id") or "").strip() != canonical_transition_id:
                continue
            target_record = record
            break
        if target_record is None:
            raise WebApiError(404, "해당 transition record를 찾지 못했습니다.")
        if str(target_record.get("record_stage") or "").strip() != "reversed":
            raise WebApiError(400, "적용이 되돌려진 상태에서만 충돌 확인할 수 있습니다.")

        now = datetime.now(timezone.utc).isoformat()
        conflict_transition_id = f"transition-local-{uuid4().hex[:12]}"

        conflict_entries: list[dict[str, Any]] = []

        serialized = self._serialize_session(session)
        aggregates = serialized.get("recurrence_aggregate_candidates") or []
        target_aggregate = None
        for agg in aggregates:
            agg_key = agg.get("aggregate_key") or {}
            if str(agg_key.get("normalized_delta_fingerprint") or "").strip() == aggregate_fingerprint:
                target_aggregate = agg
                break

        if target_aggregate is not None:
            conflict_contract = target_aggregate.get("reviewed_memory_conflict_contract")
            if isinstance(conflict_contract, dict):
                candidate_refs = target_aggregate.get("supporting_candidate_refs") or []
                source_message_refs = target_aggregate.get("supporting_source_message_refs") or []

                applied_records = [
                    r for r in existing_records
                    if isinstance(r, dict)
                    and str(r.get("transition_action") or "").strip() == "future_reviewed_memory_apply"
                    and str((r.get("aggregate_identity_ref") or {}).get("normalized_delta_fingerprint") or "").strip() == aggregate_fingerprint
                ]
                reversed_records = [
                    r for r in applied_records
                    if str(r.get("record_stage") or "").strip() == "reversed"
                ]
                active_records = [
                    r for r in applied_records
                    if str(r.get("record_stage") or "").strip() == "applied_with_result"
                    and isinstance(r.get("apply_result"), dict)
                    and str(r["apply_result"].get("result_stage") or "").strip() == "effect_active"
                ]

                if candidate_refs and (active_records or reversed_records):
                    conflict_entries.append({
                        "conflict_category": "future_reviewed_memory_candidate_draft_vs_applied_effect",
                        "candidate_count": len(candidate_refs),
                        "applied_or_reversed_count": len(active_records) + len(reversed_records),
                        "detail": "동일 aggregate 내 후보 초안과 적용된/되돌려진 효과가 공존합니다.",
                    })

                if len(applied_records) > 1:
                    conflict_entries.append({
                        "conflict_category": "future_applied_reviewed_memory_effect_vs_applied_effect",
                        "applied_record_count": len(applied_records),
                        "detail": "동일 aggregate 내 복수의 적용 이력이 존재합니다.",
                    })

        aggregate_identity_ref = dict(target_record.get("aggregate_identity_ref") or {})

        conflict_visibility_record = {
            "transition_record_version": "first_reviewed_memory_transition_record_v1",
            "canonical_transition_id": conflict_transition_id,
            "transition_action": "future_reviewed_memory_conflict_visibility",
            "aggregate_identity_ref": aggregate_identity_ref,
            "supporting_source_message_refs": list(target_record.get("supporting_source_message_refs") or []),
            "supporting_candidate_refs": list(target_record.get("supporting_candidate_refs") or []),
            "source_apply_transition_ref": canonical_transition_id,
            "conflict_entries": conflict_entries,
            "conflict_entry_count": len(conflict_entries),
            "conflict_visibility_stage": "conflict_visibility_checked",
            "record_stage": "conflict_visibility_checked",
            "task_log_mirror_relation": "mirror_allowed_not_canonical",
            "checked_at": now,
        }
        supporting_review_refs = target_record.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            conflict_visibility_record["supporting_review_refs"] = list(supporting_review_refs)

        existing_records.append(conflict_visibility_record)
        session["reviewed_memory_emitted_transition_records"] = existing_records
        self.session_store._save(session_id, session)

        self.task_logger.log(
            session_id=session_id,
            action="reviewed_memory_conflict_visibility_checked",
            detail={
                "canonical_transition_id": conflict_transition_id,
                "transition_action": "future_reviewed_memory_conflict_visibility",
                "aggregate_fingerprint": aggregate_fingerprint,
                "source_apply_transition_ref": canonical_transition_id,
                "conflict_entry_count": len(conflict_entries),
                "record_stage": "conflict_visibility_checked",
                "checked_at": now,
            },
        )

        return {
            "ok": True,
            "canonical_transition_id": conflict_transition_id,
            "conflict_visibility_record": conflict_visibility_record,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def handle_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._handle_chat_impl(payload)

    def cancel_stream(self, *, session_id: str | None, request_id: str | None) -> dict[str, Any]:
        normalized_session_id = self._normalize_session_id(session_id)
        normalized_request_id = self._normalize_optional_text(request_id)
        if not normalized_request_id:
            raise WebApiError(400, "취소할 요청 ID가 필요합니다.")

        key = self._stream_request_key(normalized_session_id, normalized_request_id)
        with self._active_stream_lock:
            cancel_event = self._active_stream_requests.get(key)
        if cancel_event is None:
            return {
                "ok": True,
                "cancelled": False,
                "session_id": normalized_session_id,
                "request_id": normalized_request_id,
                "message": "취소할 활성 스트리밍 요청을 찾지 못했습니다.",
            }

        cancel_event.set()
        self.task_logger.log(
            session_id=normalized_session_id,
            action="stream_cancel_requested",
            detail={"request_id": normalized_request_id},
        )
        return {
            "ok": True,
            "cancelled": True,
            "session_id": normalized_session_id,
            "request_id": normalized_request_id,
            "message": "스트리밍 취소를 요청했습니다.",
        }

    def stream_chat(self, payload: dict[str, Any]):
        event_queue: queue.Queue[dict[str, Any] | None] = queue.Queue()
        session_id = self._normalize_session_id(payload.get("session_id"))
        request_id = self._normalize_optional_text(payload.get("request_id")) or "request"
        cancel_event = threading.Event()
        stream_key = self._stream_request_key(session_id, request_id)

        with self._active_stream_lock:
            self._active_stream_requests[stream_key] = cancel_event

        def push_stream_event(event: dict[str, Any]) -> None:
            event_queue.put({"ok": True, **event})

        def worker() -> None:
            try:
                final_payload = self._handle_chat_impl(
                    payload,
                    stream_event_callback=push_stream_event,
                    meta_event_callback=push_stream_event,
                    cancel_requested=cancel_event.is_set,
                )
                event_queue.put({"ok": True, "event": "final", "data": final_payload})
            except RequestCancelledError:
                event_queue.put(
                    {
                        "ok": True,
                        "event": "cancelled",
                        "request_id": request_id,
                        "message": "요청을 취소했습니다. 현재까지 받은 응답만 화면에 남겨둡니다.",
                    }
                )
            except WebApiError as exc:
                event_queue.put(
                    {
                        "ok": False,
                        "event": "error",
                        "error": {"message": localize_text(exc.message)},
                        "status_code": int(exc.status_code),
                    }
                )
            except json.JSONDecodeError:
                event_queue.put(
                    {
                        "ok": False,
                        "event": "error",
                        "error": {"message": "JSON 요청 본문 형식이 올바르지 않습니다."},
                        "status_code": int(HTTPStatus.BAD_REQUEST),
                    }
                )
            except ModelAdapterError as exc:
                event_queue.put(
                    {
                        "ok": False,
                        "event": "error",
                        "error": {"message": localize_text(str(exc))},
                        "status_code": int(HTTPStatus.BAD_GATEWAY),
                    }
                )
            except Exception as exc:
                event_queue.put(
                    {
                        "ok": False,
                        "event": "error",
                        "error": {"message": localize_text(str(exc))},
                        "status_code": int(HTTPStatus.INTERNAL_SERVER_ERROR),
                    }
                )
            finally:
                with self._active_stream_lock:
                    self._active_stream_requests.pop(stream_key, None)
                event_queue.put(None)

        threading.Thread(target=worker, daemon=True).start()

        while True:
            item = event_queue.get()
            if item is None:
                break
            yield item

    def _handle_chat_impl(
        self,
        payload: dict[str, Any],
        *,
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
        meta_event_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        approved_approval_id = self._normalize_optional_text(payload.get("approved_approval_id"))
        rejected_approval_id = self._normalize_optional_text(payload.get("rejected_approval_id"))
        reissue_approval_id = self._normalize_optional_text(payload.get("reissue_approval_id"))
        corrected_save_message_id = self._normalize_optional_text(payload.get("corrected_save_message_id"))
        source_path = self._normalize_optional_text(payload.get("source_path"))
        uploaded_file = self._parse_uploaded_file(payload.get("uploaded_file"))
        uploaded_search_files = self._parse_uploaded_search_files(payload.get("uploaded_search_files"))
        search_root = self._normalize_optional_text(payload.get("search_root"))
        search_query = self._normalize_optional_text(payload.get("search_query"))
        user_text = self._normalize_optional_text(payload.get("user_text"))
        load_web_search_record_id = self._normalize_optional_text(payload.get("load_web_search_record_id"))
        retry_feedback_label = self._normalize_feedback_label(payload.get("retry_feedback_label"))
        retry_feedback_reason = self._normalize_feedback_reason(payload.get("retry_feedback_reason"))
        retry_target_message_id = self._normalize_optional_text(payload.get("retry_target_message_id"))
        note_path = self._normalize_optional_text(payload.get("note_path"))
        save_summary = self._coerce_bool(payload.get("save_summary"))
        approved = self._coerce_bool(payload.get("approved"))
        search_only = self._coerce_bool(payload.get("search_only"))
        skip_preflight = self._coerce_bool(payload.get("skip_preflight"))
        selected_paths = self._parse_selected_paths(payload.get("selected_paths"))
        search_limit = self._parse_positive_int(payload.get("search_limit"), default=3)

        existing_permissions = self.session_store.get_permissions(session_id)
        raw_web_search_permission = payload.get("web_search_permission")
        if raw_web_search_permission is None:
            web_search_permission = self._normalize_web_search_permission(
                existing_permissions.get("web_search") or self.settings.web_search_permission
            )
        else:
            web_search_permission = self._normalize_web_search_permission(raw_web_search_permission)
        if existing_permissions.get("web_search") != web_search_permission:
            self.session_store.set_permissions(session_id, {"web_search": web_search_permission})
            self.task_logger.log(
                session_id=session_id,
                action="web_search_permission_updated",
                detail={"web_search": web_search_permission},
            )

        requested_action_ids = [
            value
            for value in [
                approved_approval_id,
                rejected_approval_id,
                reissue_approval_id,
                corrected_save_message_id,
            ]
            if value
        ]
        if len(requested_action_ids) > 1:
            raise WebApiError(400, "승인 실행, 승인 취소, 승인 재발급, 수정본 저장 요청은 동시에 처리할 수 없습니다.")

        if reissue_approval_id and not note_path:
            raise WebApiError(400, "승인을 다시 만들 때는 새 저장 경로를 함께 보내야 합니다.")

        if approved_approval_id or rejected_approval_id or reissue_approval_id or corrected_save_message_id:
            loop = AgentLoop(
                model=build_model_adapter(
                    provider="mock",
                    ollama_base_url=self.settings.ollama_base_url,
                    ollama_model=self.settings.ollama_model,
                    ollama_timeout_seconds=self.settings.ollama_timeout_seconds,
                ),
                session_store=self.session_store,
                task_logger=self.task_logger,
                tools=self._build_tools(),
                notes_dir=self.settings.notes_dir,
                web_search_store=self.web_search_store,
            )
            response = loop.handle(
                UserRequest(
                    user_text="",
                    session_id=session_id,
                    approved_approval_id=approved_approval_id,
                    rejected_approval_id=rejected_approval_id,
                    reissue_approval_id=reissue_approval_id,
                    metadata={
                        **({"note_path": note_path} if note_path else {}),
                        **({"corrected_save_message_id": corrected_save_message_id} if corrected_save_message_id else {}),
                        "web_search_permission": web_search_permission,
                    },
                ),
                phase_event_callback=meta_event_callback,
                cancel_requested=cancel_requested,
            )
            response.response_origin = self._build_response_origin(
                provider="system",
                model_name=None,
                response_kind="approval",
            )
            if meta_event_callback:
                meta_event_callback(
                    {
                        "event": "response_origin",
                        "response_origin": self._serialize_response_origin(response.response_origin),
                    }
                )
            snapshot = self._synchronize_original_response_snapshot(response)
            self.session_store.update_last_message(
                session_id,
                {
                    "response_origin": dict(response.response_origin),
                    **({"original_response_snapshot": dict(snapshot)} if snapshot else {}),
                },
            )
            session_payload = self.session_store.get_session(session_id)
            return {
                "ok": True,
                "response": self._serialize_response(response),
                "runtime_status": None,
                "session": self._serialize_session(session_payload),
            }

        if (search_root or uploaded_search_files) and not search_query:
            raise WebApiError(400, "검색 루트를 입력했다면 검색어도 함께 입력해야 합니다.")
        if search_query and not search_root and not uploaded_search_files:
            raise WebApiError(400, "검색어를 입력했다면 검색 루트도 함께 입력하거나 폴더를 선택해야 합니다.")
        if (
            not source_path
            and uploaded_file is None
            and not ((search_root or uploaded_search_files) and search_query)
            and not user_text
            and not load_web_search_record_id
        ):
            raise WebApiError(400, "파일 경로, 검색 루트/검색어, 일반 메시지 중 하나는 입력해야 합니다.")

        provider = self._normalize_optional_text(payload.get("provider")) or self.settings.model_provider
        model_name = self._normalize_optional_text(payload.get("model")) or self.settings.ollama_model
        base_url = self._normalize_optional_text(payload.get("base_url")) or self.settings.ollama_base_url
        has_search_request = bool(search_query and (search_root or uploaded_search_files))
        search_intent = classify_search_intent(user_text)
        explicit_web_search_request = search_intent.kind == "explicit_web"
        implicit_web_search_query = search_intent.query if search_intent.kind == "live_latest" else None
        external_fact_web_query = search_intent.query if search_intent.kind == "external_fact" else None
        suggested_web_query = search_intent.suggestion_query if search_intent.kind == "none" else None
        needs_model = (
            not (has_search_request and search_only)
            and not explicit_web_search_request
            and not implicit_web_search_query
            and not external_fact_web_query
            and not suggested_web_query
            and not load_web_search_record_id
        )

        if provider == "ollama" and needs_model and not model_name:
            raise WebApiError(400, "Ollama를 사용할 때는 모델명을 입력해야 합니다.")

        model = build_model_adapter(
            provider=provider,
            ollama_base_url=base_url,
            ollama_model=model_name,
            ollama_timeout_seconds=self.settings.ollama_timeout_seconds,
        )
        if meta_event_callback and not skip_preflight and needs_model:
            self._emit_phase(
                meta_event_callback,
                phase="runtime_preflight",
                title="런타임 상태 확인 중",
                detail=f"{provider} 프로바이더와 모델 준비 상태를 확인하는 중입니다.",
                note="첫 요청에서는 모델 로딩 여부 확인 때문에 잠시 시간이 걸릴 수 있습니다.",
            )
        runtime_status = self._maybe_preflight_model(
            model=model,
            skip_preflight=skip_preflight,
            needs_model=needs_model,
        )
        localized_runtime_status = localize_runtime_status_payload(asdict(runtime_status)) if runtime_status else None
        response_origin = self._build_response_origin(
            provider=provider,
            model_name=model_name,
            response_kind="assistant",
        )
        if meta_event_callback and localized_runtime_status:
            meta_event_callback(
                {
                    "event": "runtime_status",
                    "runtime_status": localized_runtime_status,
                }
            )
            self._emit_phase(
                meta_event_callback,
                phase="runtime_ready",
                title="런타임 확인 완료",
                detail=f"{provider} 프로바이더가 준비되었고 이제 실제 응답 생성을 시작합니다.",
                note="이제 파일 읽기나 문서 검색, 모델 응답 단계로 넘어갑니다.",
            )
        if meta_event_callback:
            meta_event_callback(
                {
                    "event": "response_origin",
                    "response_origin": self._serialize_response_origin(response_origin),
                }
            )

        loop = AgentLoop(
            model=model,
            session_store=self.session_store,
            task_logger=self.task_logger,
            tools=self._build_tools(),
            notes_dir=self.settings.notes_dir,
            web_search_store=self.web_search_store,
        )
        request = UserRequest(
            user_text=self._build_user_text(
                user_text=user_text,
                source_path=source_path,
                uploaded_file=uploaded_file,
                uploaded_search_files=uploaded_search_files,
                search_root=search_root,
                search_query=search_query,
                load_web_search_record_id=load_web_search_record_id,
            ),
            session_id=session_id,
            approved=approved,
            metadata=self._build_metadata(
                source_path=source_path,
                uploaded_file=uploaded_file,
                uploaded_search_files=uploaded_search_files,
                search_root=search_root,
                search_query=search_query,
                search_limit=search_limit,
                search_only=search_only,
                selected_paths=selected_paths,
                save_summary=save_summary,
                note_path=note_path,
                web_search_permission=web_search_permission,
                load_web_search_record_id=load_web_search_record_id,
                retry_feedback_label=retry_feedback_label,
                retry_feedback_reason=retry_feedback_reason,
                retry_target_message_id=retry_target_message_id,
            ),
        )
        response = loop.handle(
            request,
            stream_event_callback=stream_event_callback,
            phase_event_callback=meta_event_callback,
            cancel_requested=cancel_requested,
        )
        response = self._apply_reviewed_memory_effects(session_id, response, stream_event_callback)
        if response.response_origin is None:
            response.response_origin = response_origin
        elif meta_event_callback and response.response_origin != response_origin:
            meta_event_callback(
                {
                    "event": "response_origin",
                    "response_origin": self._serialize_response_origin(response.response_origin),
                }
            )
        snapshot = self._synchronize_original_response_snapshot(response)
        self.session_store.update_last_message(
            session_id,
            {
                "response_origin": dict(response.response_origin),
                **({"original_response_snapshot": dict(snapshot)} if snapshot else {}),
            },
        )
        session_payload = self.session_store.get_session(session_id)
        return {
            "ok": True,
            "response": self._serialize_response(response),
            "runtime_status": localized_runtime_status,
            "session": self._serialize_session(session_payload),
        }

    def _apply_reviewed_memory_effects(
        self,
        session_id: str,
        response: AgentResponse,
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> AgentResponse:
        session = self.session_store.get_session(session_id)
        active_effects = session.get("reviewed_memory_active_effects")
        if not isinstance(active_effects, list) or not active_effects:
            return response
        if not response.text or not response.text.strip():
            return response

        correction_effects = [
            effect for effect in active_effects
            if isinstance(effect, dict)
            and str(effect.get("effect_kind") or "").strip() == "reviewed_memory_correction_pattern"
        ]
        if not correction_effects:
            return response

        notes: list[str] = []
        for effect in correction_effects:
            reason = str(effect.get("operator_reason_or_note") or "").strip()
            fingerprint = str(effect.get("aggregate_fingerprint") or "").strip()[:16]
            if reason:
                notes.append(f"[검토 메모 활성] {reason} (패턴 {fingerprint})")
            else:
                notes.append(f"[검토 메모 활성] 교정 패턴이 적용되었습니다. (패턴 {fingerprint})")

        prefix = "\n".join(notes)
        updated_text = f"{prefix}\n\n{response.text}"
        response.text = updated_text

        if stream_event_callback:
            stream_event_callback({"event": "text_replace", "text": updated_text})

        return response

    def _build_tools(self) -> dict[str, Any]:
        reader = FileReaderTool()
        allowed_roots = [str(Path.cwd()), self.settings.notes_dir]
        return {
            "read_file": reader,
            "search_files": FileSearchTool(reader=reader),
            "search_web": WebSearchTool(timeout_seconds=self.settings.web_search_timeout_seconds),
            "write_note": WriteNoteTool(allowed_roots=allowed_roots),
        }

    def _maybe_preflight_model(
        self,
        *,
        model: Any,
        skip_preflight: bool,
        needs_model: bool,
    ) -> ModelRuntimeStatus | None:
        if skip_preflight or not needs_model:
            return None

        status = model.health_check()
        if not status.reachable:
            raise WebApiError(503, localize_text(status.detail))
        if not status.configured_model_available:
            raise WebApiError(503, localize_text(status.detail))
        return status

    def _emit_phase(
        self,
        callback: Callable[[dict[str, Any]], None] | None,
        *,
        phase: str,
        title: str,
        detail: str,
        note: str = "",
    ) -> None:
        if callback is None:
            return
        callback(
            {
                "event": "phase",
                "phase": phase,
                "title": title,
                "detail": detail,
                "note": note,
            }
        )

    def _stream_request_key(self, session_id: str, request_id: str) -> str:
        return f"{session_id}:{request_id}"

    def _build_user_text(
        self,
        *,
        user_text: str | None,
        source_path: str | None,
        uploaded_file: dict[str, Any] | None,
        uploaded_search_files: list[dict[str, Any]] | None,
        search_root: str | None,
        search_query: str | None,
        load_web_search_record_id: str | None,
    ) -> str:
        if user_text:
            return user_text
        if load_web_search_record_id:
            return "최근 웹 검색 기록을 다시 불러와 주세요."
        if uploaded_search_files and search_query:
            folder_label = str(uploaded_search_files[0].get("root_label") or "선택 폴더")
            return f"{folder_label}에서 '{search_query}'를 검색하고 결과를 요약해 주세요."
        if search_root and search_query:
            return f"{search_root}에서 '{search_query}'를 검색하고 결과를 요약해 주세요."
        if uploaded_file:
            file_name = str(uploaded_file.get("name") or "selected-file")
            return f"{file_name} 파일을 요약해 주세요."
        if source_path:
            return f"{source_path} 파일을 요약해 주세요."
        return "안녕하세요"

    def _build_metadata(
        self,
        *,
        source_path: str | None,
        uploaded_file: dict[str, Any] | None,
        uploaded_search_files: list[dict[str, Any]] | None,
        search_root: str | None,
        search_query: str | None,
        search_limit: int,
        search_only: bool,
        selected_paths: list[str] | None,
        save_summary: bool,
        note_path: str | None,
        web_search_permission: str,
        load_web_search_record_id: str | None,
        retry_feedback_label: str | None,
        retry_feedback_reason: str | None,
        retry_target_message_id: str | None,
    ) -> dict[str, Any]:
        if (search_root or uploaded_search_files) and search_query:
            return {
                "search_root": search_root,
                "uploaded_search_files": uploaded_search_files,
                "search_query": search_query,
                "search_result_limit": search_limit,
                "search_only": search_only,
                "search_selected_paths": selected_paths,
                "save_summary": save_summary,
                "note_path": note_path,
                "web_search_permission": web_search_permission,
                "load_web_search_record_id": load_web_search_record_id,
                "retry_feedback_label": retry_feedback_label,
                "retry_feedback_reason": retry_feedback_reason,
                "retry_target_message_id": retry_target_message_id,
            }
        return {
            "source_path": source_path,
            "uploaded_file": uploaded_file,
            "save_summary": save_summary,
            "note_path": note_path,
            "web_search_permission": web_search_permission,
            "load_web_search_record_id": load_web_search_record_id,
            "retry_feedback_label": retry_feedback_label,
            "retry_feedback_reason": retry_feedback_reason,
            "retry_target_message_id": retry_target_message_id,
        }

    def _parse_uploaded_file(self, raw_value: Any) -> dict[str, Any] | None:
        if raw_value is None:
            return None
        parsed = self._parse_uploaded_file_record(raw_value, require_relative_path=False)
        return {
            "name": parsed["name"],
            "mime_type": parsed["mime_type"],
            "size_bytes": parsed["size_bytes"],
            "content_bytes": parsed["content_bytes"],
        }

    def _parse_uploaded_search_files(self, raw_value: Any) -> list[dict[str, Any]] | None:
        if raw_value is None:
            return None
        if not isinstance(raw_value, list):
            raise WebApiError(400, "선택 폴더 정보는 JSON 배열이어야 합니다.")
        if not raw_value:
            return None
        if len(raw_value) > 50:
            raise WebApiError(400, "선택 폴더에는 최대 50개 파일까지만 담아 주세요.")

        parsed_files: list[dict[str, Any]] = []
        total_bytes = 0
        for item in raw_value:
            parsed = self._parse_uploaded_file_record(item, require_relative_path=True)
            total_bytes += parsed["size_bytes"]
            if total_bytes > 20 * 1024 * 1024:
                raise WebApiError(400, "선택 폴더 전체 크기가 20MB를 넘습니다. 더 작은 폴더로 나눠서 다시 시도해 주세요.")
            parsed_files.append(parsed)
        return parsed_files

    def _parse_uploaded_file_record(
        self,
        raw_value: Any,
        *,
        require_relative_path: bool,
    ) -> dict[str, Any]:
        if not isinstance(raw_value, dict):
            raise WebApiError(400, "선택 파일 정보는 JSON 객체여야 합니다.")

        name = self._normalize_optional_text(raw_value.get("name"))
        content_base64 = self._normalize_optional_text(raw_value.get("content_base64"))
        mime_type = self._normalize_optional_text(raw_value.get("mime_type"))
        relative_path = self._normalize_optional_text(raw_value.get("relative_path"))
        provided_root_label = self._normalize_optional_text(raw_value.get("root_label"))
        size_bytes_raw = raw_value.get("size_bytes")

        if not name or not content_base64:
            raise WebApiError(400, "선택 파일에는 name과 content_base64가 필요합니다.")
        if require_relative_path and not relative_path:
            raise WebApiError(400, "선택 폴더 파일에는 relative_path가 필요합니다.")

        if not isinstance(size_bytes_raw, int) or size_bytes_raw < 0:
            raise WebApiError(400, "선택 파일 크기는 0 이상의 정수여야 합니다.")

        try:
            content_bytes = base64.b64decode(content_base64.encode("ascii"), validate=True)
        except Exception as exc:
            raise WebApiError(400, "선택 파일 본문(base64)을 해석할 수 없습니다.") from exc

        if len(content_bytes) != size_bytes_raw:
            raise WebApiError(400, "선택 파일 크기 정보가 실제 본문과 다릅니다.")
        if len(content_bytes) > 10 * 1024 * 1024:
            raise WebApiError(400, "선택 파일 크기가 10MB를 넘습니다. 경로 입력 방식이나 더 작은 파일로 다시 시도해 주세요.")

        normalized_relative_path = relative_path or ""
        root_label = provided_root_label or ""
        if relative_path:
            normalized_relative_path = relative_path.replace("\\", "/")
            root_label = root_label or normalized_relative_path.split("/", 1)[0]
        return {
            "name": name,
            "relative_path": normalized_relative_path,
            "root_label": root_label,
            "mime_type": mime_type or "",
            "size_bytes": size_bytes_raw,
            "content_bytes": content_bytes,
        }

    def _serialize_response(
        self,
        response: AgentResponse,
    ) -> dict[str, Any]:
        return {
            "artifact_id": response.artifact_id,
            "artifact_kind": response.artifact_kind,
            "source_message_id": self._serialize_source_message_id(
                response.source_message_id or ((response.approval or {}).get("source_message_id") if response.approval else None)
            ),
            "status": response.status,
            "text": localize_text(response.text),
            "actions_taken": response.actions_taken,
            "requires_approval": response.requires_approval,
            "proposed_note_path": response.proposed_note_path,
            "saved_note_path": response.saved_note_path,
            "web_search_record_path": response.web_search_record_path,
            "selected_source_paths": response.selected_source_paths,
            "note_preview": localize_text(response.note_preview) if response.note_preview else None,
            "approval": self._serialize_approval(response.approval),
            "active_context": self._serialize_active_context(response.active_context),
            "follow_up_suggestions": [localize_text(str(item)) for item in response.follow_up_suggestions],
            "response_origin": self._serialize_response_origin(response.response_origin),
            "evidence": self._serialize_evidence(response.evidence),
            "summary_chunks": self._serialize_summary_chunks(response.summary_chunks),
            "original_response_snapshot": self._serialize_original_response_snapshot(response.original_response_snapshot),
            "corrected_outcome": self._serialize_corrected_outcome(response.corrected_outcome),
            "approval_reason_record": self._serialize_approval_reason_record(response.approval_reason_record),
            "content_reason_record": self._serialize_content_reason_record(getattr(response, "content_reason_record", None)),
            "save_content_source": self._serialize_save_content_source(response.save_content_source),
            "claim_coverage": self._serialize_claim_coverage(response.claim_coverage),
            "claim_coverage_progress_summary": localize_text(
                str(response.claim_coverage_progress_summary or "")
            ).strip(),
        }

    def _serialize_session(self, session: dict[str, Any]) -> dict[str, Any]:
        localized = localize_session(session)
        localized.pop("reviewed_memory_local_effect_presence_proof_record_store", None)
        localized_source_messages = localized.get("messages", [])
        localized_messages: list[dict[str, Any]] = []
        superseded_reject_index = self._build_superseded_reject_signal_index(session)
        historical_save_identity_index = self._build_historical_save_identity_signal_index(session)
        existing_proof_record_store_entries = session.get(
            "reviewed_memory_local_effect_presence_proof_record_store"
        )
        if not isinstance(existing_proof_record_store_entries, list):
            existing_proof_record_store_entries = None
        for index, message in enumerate(session.get("messages", [])):
            if not isinstance(message, dict):
                continue
            localized_message = (
                dict(localized_source_messages[index])
                if index < len(localized_source_messages) and isinstance(localized_source_messages[index], dict)
                else dict(message)
            )
            localized_message["claim_coverage"] = self._serialize_claim_coverage(localized_message.get("claim_coverage"))
            original_response_snapshot = self._serialize_original_response_snapshot(message.get("original_response_snapshot"))
            if original_response_snapshot is not None:
                localized_message["original_response_snapshot"] = original_response_snapshot
            else:
                localized_message.pop("original_response_snapshot", None)
            corrected_outcome = self._serialize_corrected_outcome(message.get("corrected_outcome"))
            if corrected_outcome is not None:
                localized_message["corrected_outcome"] = corrected_outcome
            else:
                localized_message.pop("corrected_outcome", None)
            corrected_text = self._serialize_corrected_text(message.get("corrected_text"))
            if corrected_text is not None:
                localized_message["corrected_text"] = corrected_text
            else:
                localized_message.pop("corrected_text", None)
            approval_reason_record = self._serialize_approval_reason_record(message.get("approval_reason_record"))
            if approval_reason_record is not None:
                localized_message["approval_reason_record"] = approval_reason_record
            else:
                localized_message.pop("approval_reason_record", None)
            content_reason_record = self._serialize_content_reason_record(message.get("content_reason_record"))
            if content_reason_record is not None:
                localized_message["content_reason_record"] = content_reason_record
            else:
                localized_message.pop("content_reason_record", None)
            save_content_source = self._serialize_save_content_source(message.get("save_content_source"))
            if save_content_source is not None:
                localized_message["save_content_source"] = save_content_source
            else:
                localized_message.pop("save_content_source", None)
            source_message_id = self._serialize_source_message_id(message.get("source_message_id"))
            if source_message_id is not None:
                localized_message["source_message_id"] = source_message_id
            else:
                localized_message.pop("source_message_id", None)
            session_local_memory_signal = self._serialize_session_local_memory_signal(
                self.session_store.build_session_local_memory_signal(
                    session,
                    source_message=message,
                )
            )
            if session_local_memory_signal is not None:
                localized_message["session_local_memory_signal"] = session_local_memory_signal
            else:
                localized_message.pop("session_local_memory_signal", None)
            superseded_reject_signal = self._serialize_superseded_reject_signal(
                self._resolve_superseded_reject_signal_for_message(
                    message=message,
                    session_local_memory_signal=session_local_memory_signal,
                    superseded_reject_index=superseded_reject_index,
                )
            )
            if superseded_reject_signal is not None:
                localized_message["superseded_reject_signal"] = superseded_reject_signal
            else:
                localized_message.pop("superseded_reject_signal", None)
            historical_save_identity_signal = self._serialize_historical_save_identity_signal(
                self._resolve_historical_save_identity_signal_for_message(
                    message=message,
                    session_local_memory_signal=session_local_memory_signal,
                    historical_save_identity_index=historical_save_identity_index,
                )
            )
            if historical_save_identity_signal is not None:
                localized_message["historical_save_identity_signal"] = historical_save_identity_signal
            else:
                localized_message.pop("historical_save_identity_signal", None)
            current_session_local_candidate = self._build_session_local_candidate_for_message(
                message=message,
                session_local_memory_signal=session_local_memory_signal,
            )
            candidate_confirmation_record = self._serialize_candidate_confirmation_record(
                self._resolve_candidate_confirmation_record_for_message(
                    message=message,
                    session_local_candidate=current_session_local_candidate,
                )
            )
            if candidate_confirmation_record is not None:
                localized_message["candidate_confirmation_record"] = candidate_confirmation_record
            else:
                localized_message.pop("candidate_confirmation_record", None)
            session_local_candidate = self._serialize_session_local_candidate(current_session_local_candidate)
            if session_local_candidate is not None:
                localized_message["session_local_candidate"] = session_local_candidate
            else:
                localized_message.pop("session_local_candidate", None)
            candidate_recurrence_key = self._serialize_candidate_recurrence_key(
                self._build_candidate_recurrence_key_for_message(
                    message=message,
                    session_local_candidate=session_local_candidate,
                )
            )
            if candidate_recurrence_key is not None:
                localized_message["candidate_recurrence_key"] = candidate_recurrence_key
            else:
                localized_message.pop("candidate_recurrence_key", None)
            durable_candidate = self._serialize_durable_candidate(
                self._build_durable_candidate_for_message(
                    session_local_candidate=session_local_candidate,
                    candidate_confirmation_record=candidate_confirmation_record,
                )
            )
            if durable_candidate is not None:
                localized_message["durable_candidate"] = durable_candidate
            else:
                localized_message.pop("durable_candidate", None)
            candidate_review_record = self._serialize_candidate_review_record(
                self._resolve_candidate_review_record_for_message(
                    message=message,
                    durable_candidate=durable_candidate,
                )
            )
            if candidate_review_record is not None:
                localized_message["candidate_review_record"] = candidate_review_record
            else:
                localized_message.pop("candidate_review_record", None)
            localized_message["claim_coverage_progress_summary"] = localize_text(
                str(localized_message.get("claim_coverage_progress_summary") or "")
            ).strip()
            localized_messages.append(localized_message)
        localized["messages"] = localized_messages
        preliminary_recurrence_aggregate_candidates = self._build_recurrence_aggregate_candidates(
            localized_messages
        )
        proof_record_store_entries = (
            self._build_reviewed_memory_local_effect_presence_proof_record_store_entries(
                preliminary_recurrence_aggregate_candidates,
                existing_entries=existing_proof_record_store_entries,
            )
        )
        existing_emitted_transition_records = session.get("reviewed_memory_emitted_transition_records")
        if not isinstance(existing_emitted_transition_records, list):
            existing_emitted_transition_records = None
        recurrence_aggregate_candidates = self._build_recurrence_aggregate_candidates(
            localized_messages,
            proof_record_store_entries=proof_record_store_entries or None,
            emitted_transition_records=existing_emitted_transition_records,
        )
        internal_keys = {
            "_reviewed_memory_local_effect_presence_proof_record_store_entries",
            "_reviewed_memory_emitted_transition_records",
        }
        if recurrence_aggregate_candidates:
            localized["recurrence_aggregate_candidates"] = [
                {
                    key: value
                    for key, value in aggregate_candidate.items()
                    if key not in internal_keys
                }
                for aggregate_candidate in recurrence_aggregate_candidates
            ]
        else:
            localized.pop("recurrence_aggregate_candidates", None)
        localized["review_queue_items"] = self._build_review_queue_items(localized_messages)
        localized["pending_approvals"] = [
            self._serialize_approval(approval)
            for approval in session.get("pending_approvals", [])
            if isinstance(approval, dict)
        ]
        localized["active_context"] = self._serialize_active_context(session.get("active_context"))
        localized["permissions"] = self._serialize_permissions(session.get("permissions"))
        localized["web_search_history"] = self._serialize_web_search_history(session.get("session_id"))
        return localized

    def _serialize_web_search_history(self, session_id: Any) -> list[dict[str, Any]]:
        normalized_session_id = self._normalize_optional_text(session_id)
        if not normalized_session_id:
            return []
        history = self.web_search_store.list_session_record_summaries(normalized_session_id, limit=8)
        serialized: list[dict[str, Any]] = []
        for item in history:
            serialized.append(
                {
                    "record_id": str(item.get("record_id") or ""),
                    "query": localize_text(str(item.get("query") or "")),
                    "created_at": str(item.get("created_at") or ""),
                    "result_count": int(item.get("result_count") or 0),
                    "page_count": int(item.get("page_count") or 0),
                    "record_path": str(item.get("record_path") or ""),
                    "summary_head": localize_text(str(item.get("summary_head") or "")),
                    "answer_mode": str(item.get("answer_mode") or "general"),
                    "verification_label": localize_text(str(item.get("verification_label") or "")),
                    "source_roles": [localize_text(str(role)) for role in item.get("source_roles", []) if str(role).strip()],
                    "claim_coverage_summary": {
                        "strong": int((item.get("claim_coverage_summary") or {}).get("strong") or 0),
                        "weak": int((item.get("claim_coverage_summary") or {}).get("weak") or 0),
                        "missing": int((item.get("claim_coverage_summary") or {}).get("missing") or 0),
                    },
                    "pages_preview": [
                        {
                            "title": localize_text(str(page.get("title") or "")),
                            "url": str(page.get("url") or ""),
                            "excerpt": localize_text(str(page.get("excerpt") or "")),
                            "text_preview": localize_text(str(page.get("text_preview") or "")),
                            "char_count": int(page.get("char_count") or 0),
                        }
                        for page in item.get("pages_preview", [])
                        if isinstance(page, dict)
                    ],
                }
            )
        return serialized

    def _serialize_approval(self, approval: dict[str, Any] | None) -> dict[str, Any] | None:
        if approval is None:
            return None
        preview_markdown = approval.get("preview_markdown")
        return {
            "approval_id": approval.get("approval_id"),
            "artifact_id": approval.get("artifact_id"),
            "source_message_id": self._serialize_source_message_id(approval.get("source_message_id")),
            "kind": approval.get("kind"),
            "requested_path": approval.get("requested_path"),
            "overwrite": bool(approval.get("overwrite", False)),
            "preview_markdown": localize_text(str(preview_markdown)) if isinstance(preview_markdown, str) else "",
            "source_paths": [str(path) for path in approval.get("source_paths", [])],
            "created_at": approval.get("created_at"),
            "save_content_source": self._serialize_save_content_source(approval.get("save_content_source")),
            "approval_reason_record": self._serialize_approval_reason_record(approval.get("approval_reason_record")),
        }

    def _serialize_active_context(self, context: dict[str, Any] | None) -> dict[str, Any] | None:
        if context is None:
            return None
        return {
            "kind": context.get("kind"),
            "label": context.get("label"),
            "source_paths": [str(path) for path in context.get("source_paths", [])],
            "summary_hint": localize_text(str(context.get("summary_hint", ""))),
            "suggested_prompts": [localize_text(str(item)) for item in context.get("suggested_prompts", [])],
            "record_path": str(context.get("record_path") or ""),
            "claim_coverage_progress_summary": localize_text(
                str(context.get("claim_coverage_progress_summary") or "")
            ).strip(),
        }

    def _build_response_origin(
        self,
        *,
        provider: str,
        model_name: str | None,
        response_kind: str,
    ) -> dict[str, Any]:
        normalized_provider = (provider or "system").strip().lower()
        if normalized_provider == "ollama":
            return {
                "provider": "ollama",
                "badge": "OLLAMA",
                "label": "실제 로컬 모델 응답",
                "model": model_name or "선택형 로컬 모델",
                "kind": response_kind,
            }
        if normalized_provider == "mock":
            return {
                "provider": "mock",
                "badge": "MOCK",
                "label": "모의 데모 응답",
                "model": model_name or "내장 모의 어댑터",
                "kind": response_kind,
            }
        return {
            "provider": "system",
            "badge": "SYSTEM",
            "label": "시스템 응답",
            "model": None,
            "kind": response_kind,
        }

    def _serialize_response_origin(self, origin: dict[str, Any] | None) -> dict[str, Any] | None:
        if origin is None:
            return None
        return {
            "provider": str(origin.get("provider") or "system"),
            "badge": str(origin.get("badge") or "SYSTEM"),
            "label": str(origin.get("label") or "시스템 응답"),
            "model": origin.get("model"),
            "kind": str(origin.get("kind") or "assistant"),
            "answer_mode": str(origin.get("answer_mode") or "general"),
            "source_roles": [str(item) for item in origin.get("source_roles", []) if str(item).strip()],
            "verification_label": str(origin.get("verification_label") or "").strip(),
        }

    def _serialize_original_response_snapshot(
        self,
        snapshot: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(snapshot, dict):
            return None
        return {
            "artifact_id": str(snapshot.get("artifact_id") or "").strip(),
            "artifact_kind": str(snapshot.get("artifact_kind") or "").strip(),
            "draft_text": localize_text(str(snapshot.get("draft_text") or "")),
            "source_paths": [str(path) for path in snapshot.get("source_paths", []) if str(path).strip()],
            "response_origin": self._serialize_response_origin(snapshot.get("response_origin")),
            "summary_chunks_snapshot": self._serialize_summary_chunks(snapshot.get("summary_chunks_snapshot")),
            "evidence_snapshot": self._serialize_evidence(snapshot.get("evidence_snapshot")),
        }

    def _serialize_corrected_outcome(
        self,
        corrected_outcome: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(corrected_outcome, dict):
            return None
        return {
            "outcome": str(corrected_outcome.get("outcome") or "").strip(),
            "recorded_at": str(corrected_outcome.get("recorded_at") or ""),
            "artifact_id": str(corrected_outcome.get("artifact_id") or "").strip(),
            "source_message_id": str(corrected_outcome.get("source_message_id") or "").strip(),
            "approval_id": str(corrected_outcome.get("approval_id") or "").strip() or None,
            "saved_note_path": str(corrected_outcome.get("saved_note_path") or "").strip() or None,
        }

    def _serialize_corrected_text(self, corrected_text: Any) -> str | None:
        if not isinstance(corrected_text, str):
            return None
        normalized = corrected_text.replace("\r\n", "\n").strip()
        return normalized or None

    def _serialize_save_content_source(self, save_content_source: Any) -> str | None:
        if not isinstance(save_content_source, str):
            return None
        normalized = save_content_source.strip()
        return normalized or None

    def _serialize_source_message_id(self, source_message_id: Any) -> str | None:
        if not isinstance(source_message_id, str):
            return None
        normalized = source_message_id.strip()
        return normalized or None

    def _serialize_approval_reason_record(
        self,
        approval_reason_record: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(approval_reason_record, dict):
            return None
        return {
            "reason_scope": str(approval_reason_record.get("reason_scope") or "").strip(),
            "reason_label": str(approval_reason_record.get("reason_label") or "").strip(),
            "reason_note": localize_text(str(approval_reason_record.get("reason_note") or "")).strip() or None,
            "recorded_at": str(approval_reason_record.get("recorded_at") or ""),
            "artifact_id": str(approval_reason_record.get("artifact_id") or "").strip(),
            "artifact_kind": str(approval_reason_record.get("artifact_kind") or "").strip(),
            "source_message_id": str(approval_reason_record.get("source_message_id") or "").strip(),
            "approval_id": str(approval_reason_record.get("approval_id") or "").strip(),
        }

    def _serialize_content_reason_record(
        self,
        content_reason_record: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(content_reason_record, dict):
            return None
        return {
            "reason_scope": str(content_reason_record.get("reason_scope") or "").strip(),
            "reason_label": str(content_reason_record.get("reason_label") or "").strip(),
            "reason_note": localize_text(str(content_reason_record.get("reason_note") or "")).strip() or None,
            "recorded_at": str(content_reason_record.get("recorded_at") or ""),
            "artifact_id": str(content_reason_record.get("artifact_id") or "").strip(),
            "artifact_kind": str(content_reason_record.get("artifact_kind") or "").strip(),
            "source_message_id": str(content_reason_record.get("source_message_id") or "").strip(),
        }

    def _serialize_session_local_memory_signal(
        self,
        session_local_memory_signal: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(session_local_memory_signal, dict):
            return None

        signal_scope = str(session_local_memory_signal.get("signal_scope") or "").strip()
        artifact_id = str(session_local_memory_signal.get("artifact_id") or "").strip()
        source_message_id = self._serialize_source_message_id(session_local_memory_signal.get("source_message_id"))
        content_signal = session_local_memory_signal.get("content_signal")
        if not signal_scope or not artifact_id or source_message_id is None or not isinstance(content_signal, dict):
            return None

        serialized: dict[str, Any] = {
            "signal_scope": signal_scope,
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "content_signal": {
                "latest_corrected_outcome": self._serialize_corrected_outcome(
                    content_signal.get("latest_corrected_outcome")
                ),
                "has_corrected_text": bool(content_signal.get("has_corrected_text")),
            },
        }
        serialized_content_reason_record = self._serialize_content_reason_record(content_signal.get("content_reason_record"))
        if serialized_content_reason_record is not None:
            serialized["content_signal"]["content_reason_record"] = serialized_content_reason_record

        approval_signal = session_local_memory_signal.get("approval_signal")
        if isinstance(approval_signal, dict):
            latest_approval_reason_record = self._serialize_approval_reason_record(
                approval_signal.get("latest_approval_reason_record")
            )
            if latest_approval_reason_record is not None:
                serialized["approval_signal"] = {
                    "latest_approval_reason_record": latest_approval_reason_record,
                }

        save_signal = session_local_memory_signal.get("save_signal")
        if isinstance(save_signal, dict):
            serialized_save_signal: dict[str, Any] = {}
            latest_save_content_source = self._serialize_save_content_source(save_signal.get("latest_save_content_source"))
            if latest_save_content_source is not None:
                serialized_save_signal["latest_save_content_source"] = latest_save_content_source
            latest_approval_id = str(save_signal.get("latest_approval_id") or "").strip() or None
            if latest_approval_id is not None:
                serialized_save_signal["latest_approval_id"] = latest_approval_id
            latest_saved_note_path = str(save_signal.get("latest_saved_note_path") or "").strip() or None
            if latest_saved_note_path is not None:
                serialized_save_signal["latest_saved_note_path"] = latest_saved_note_path
            if serialized_save_signal:
                serialized["save_signal"] = serialized_save_signal

        return serialized

    def _serialize_superseded_reject_signal(
        self,
        superseded_reject_signal: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(superseded_reject_signal, dict):
            return None

        artifact_id = str(superseded_reject_signal.get("artifact_id") or "").strip()
        source_message_id = self._serialize_source_message_id(superseded_reject_signal.get("source_message_id"))
        replay_source = str(superseded_reject_signal.get("replay_source") or "").strip()
        corrected_outcome = superseded_reject_signal.get("corrected_outcome")
        if (
            not artifact_id
            or source_message_id is None
            or replay_source != "task_log_audit"
            or not isinstance(corrected_outcome, dict)
        ):
            return None

        outcome = str(corrected_outcome.get("outcome") or "").strip()
        recorded_at = str(corrected_outcome.get("recorded_at") or "").strip()
        if outcome != "rejected" or not recorded_at:
            return None

        serialized = {
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "replay_source": replay_source,
            "corrected_outcome": {
                "outcome": outcome,
                "recorded_at": recorded_at,
            },
        }
        content_reason_record = self._serialize_content_reason_record(
            superseded_reject_signal.get("content_reason_record")
        )
        if content_reason_record is not None:
            serialized["content_reason_record"] = content_reason_record
        return serialized

    def _serialize_historical_save_identity_signal(
        self,
        historical_save_identity_signal: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(historical_save_identity_signal, dict):
            return None

        artifact_id = str(historical_save_identity_signal.get("artifact_id") or "").strip()
        source_message_id = self._serialize_source_message_id(
            historical_save_identity_signal.get("source_message_id")
        )
        replay_source = str(historical_save_identity_signal.get("replay_source") or "").strip()
        approval_id = str(historical_save_identity_signal.get("approval_id") or "").strip() or None
        if (
            not artifact_id
            or source_message_id is None
            or replay_source != "task_log_audit"
            or approval_id is None
        ):
            return None

        recorded_at = str(historical_save_identity_signal.get("recorded_at") or "").strip()
        if not recorded_at:
            return None

        serialized = {
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "replay_source": replay_source,
            "approval_id": approval_id,
            "recorded_at": recorded_at,
        }
        save_content_source = self._serialize_save_content_source(
            historical_save_identity_signal.get("save_content_source")
        )
        if save_content_source is not None:
            serialized["save_content_source"] = save_content_source
        saved_note_path = str(historical_save_identity_signal.get("saved_note_path") or "").strip() or None
        if saved_note_path is not None:
            serialized["saved_note_path"] = saved_note_path
        return serialized

    def _serialize_session_local_candidate(
        self,
        session_local_candidate: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(session_local_candidate, dict):
            return None

        candidate_id = str(session_local_candidate.get("candidate_id") or "").strip()
        candidate_scope = str(session_local_candidate.get("candidate_scope") or "").strip()
        candidate_family = str(session_local_candidate.get("candidate_family") or "").strip()
        statement = localize_text(str(session_local_candidate.get("statement") or "")).strip()
        status = str(session_local_candidate.get("status") or "").strip()
        created_at = str(session_local_candidate.get("created_at") or "").strip()
        updated_at = str(session_local_candidate.get("updated_at") or "").strip()
        evidence_strength = str(session_local_candidate.get("evidence_strength") or "").strip()
        if (
            not candidate_id
            or candidate_scope != "session_local"
            or candidate_family != "correction_rewrite_preference"
            or not statement
            or status != "session_local_candidate"
            or not created_at
            or not updated_at
            or evidence_strength != "explicit_single_artifact"
        ):
            return None

        supporting_artifact_ids = [
            artifact_id
            for raw_artifact_id in session_local_candidate.get("supporting_artifact_ids", [])
            if isinstance(raw_artifact_id, str)
            and (artifact_id := raw_artifact_id.strip())
        ]
        supporting_source_message_ids = [
            source_message_id
            for raw_source_message_id in session_local_candidate.get("supporting_source_message_ids", [])
            if isinstance(raw_source_message_id, str)
            and (source_message_id := raw_source_message_id.strip())
        ]
        supporting_signal_refs: list[dict[str, str]] = []
        for raw_ref in session_local_candidate.get("supporting_signal_refs", []):
            if not isinstance(raw_ref, dict):
                continue
            signal_name = str(raw_ref.get("signal_name") or "").strip()
            relationship = str(raw_ref.get("relationship") or "").strip()
            if not signal_name or relationship not in {"primary_basis", "supporting_evidence"}:
                continue
            supporting_signal_refs.append(
                {
                    "signal_name": signal_name,
                    "relationship": relationship,
                }
            )

        if not supporting_artifact_ids or not supporting_source_message_ids or not supporting_signal_refs:
            return None

        return {
            "candidate_id": candidate_id,
            "candidate_scope": candidate_scope,
            "candidate_family": candidate_family,
            "statement": statement,
            "supporting_artifact_ids": supporting_artifact_ids,
            "supporting_source_message_ids": supporting_source_message_ids,
            "supporting_signal_refs": supporting_signal_refs,
            "evidence_strength": evidence_strength,
            "status": status,
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def _serialize_candidate_recurrence_key(
        self,
        candidate_recurrence_key: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(candidate_recurrence_key, dict):
            return None

        candidate_family = str(candidate_recurrence_key.get("candidate_family") or "").strip()
        key_scope = str(candidate_recurrence_key.get("key_scope") or "").strip()
        key_version = str(candidate_recurrence_key.get("key_version") or "").strip()
        derivation_source = str(candidate_recurrence_key.get("derivation_source") or "").strip()
        source_candidate_id = str(candidate_recurrence_key.get("source_candidate_id") or "").strip()
        source_candidate_updated_at = str(candidate_recurrence_key.get("source_candidate_updated_at") or "").strip()
        normalized_delta_fingerprint = str(candidate_recurrence_key.get("normalized_delta_fingerprint") or "").strip()
        stability = str(candidate_recurrence_key.get("stability") or "").strip()
        derived_at = str(candidate_recurrence_key.get("derived_at") or "").strip()
        if (
            candidate_family != "correction_rewrite_preference"
            or key_scope != "correction_rewrite_recurrence"
            or key_version != "explicit_pair_rewrite_delta_v1"
            or derivation_source != "explicit_corrected_pair"
            or not source_candidate_id
            or not source_candidate_updated_at
            or not normalized_delta_fingerprint
            or stability != "deterministic_local"
            or derived_at != source_candidate_updated_at
        ):
            return None

        serialized = {
            "candidate_family": candidate_family,
            "key_scope": key_scope,
            "key_version": key_version,
            "derivation_source": derivation_source,
            "source_candidate_id": source_candidate_id,
            "source_candidate_updated_at": source_candidate_updated_at,
            "normalized_delta_fingerprint": normalized_delta_fingerprint,
            "stability": stability,
            "derived_at": derived_at,
        }

        rewrite_dimensions = candidate_recurrence_key.get("rewrite_dimensions")
        if isinstance(rewrite_dimensions, dict):
            change_types = [
                change_type
                for raw_change_type in rewrite_dimensions.get("change_types", [])
                if (change_type := str(raw_change_type or "").strip()) in {"delete", "insert", "replace"}
            ]
            changed_segment_count = rewrite_dimensions.get("changed_segment_count")
            line_count_delta = rewrite_dimensions.get("line_count_delta")
            character_count_delta = rewrite_dimensions.get("character_count_delta")
            serialized_dimensions: dict[str, Any] = {}
            if change_types:
                serialized_dimensions["change_types"] = sorted(set(change_types))
            if isinstance(changed_segment_count, int):
                serialized_dimensions["changed_segment_count"] = changed_segment_count
            if isinstance(line_count_delta, int):
                serialized_dimensions["line_count_delta"] = line_count_delta
            if isinstance(character_count_delta, int):
                serialized_dimensions["character_count_delta"] = character_count_delta
            if serialized_dimensions:
                serialized["rewrite_dimensions"] = serialized_dimensions

        return serialized

    def _derive_normalized_rewrite_delta(
        self,
        *,
        original_text: str,
        corrected_text: str,
    ) -> tuple[str, dict[str, Any] | None] | tuple[None, None]:
        matcher = difflib.SequenceMatcher(a=original_text, b=corrected_text, autojunk=False)
        normalized_delta_segments: list[dict[str, str]] = []
        change_types: list[str] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            from_text = original_text[i1:i2]
            to_text = corrected_text[j1:j2]
            if not from_text and not to_text:
                continue
            normalized_delta_segments.append(
                {
                    "from": from_text,
                    "op": tag,
                    "to": to_text,
                }
            )
            change_types.append(tag)

        if not normalized_delta_segments:
            return None, None

        delta_payload = json.dumps(
            normalized_delta_segments,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        normalized_delta_fingerprint = f"sha256:{hashlib.sha256(delta_payload.encode('utf-8')).hexdigest()}"
        rewrite_dimensions = {
            "change_types": sorted(set(change_types)),
            "changed_segment_count": len(normalized_delta_segments),
            "line_count_delta": corrected_text.count("\n") - original_text.count("\n"),
            "character_count_delta": len(corrected_text) - len(original_text),
        }
        return normalized_delta_fingerprint, rewrite_dimensions

    def _serialize_durable_candidate(
        self,
        durable_candidate: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(durable_candidate, dict):
            return None

        candidate_id = str(durable_candidate.get("candidate_id") or "").strip()
        candidate_scope = str(durable_candidate.get("candidate_scope") or "").strip()
        candidate_family = str(durable_candidate.get("candidate_family") or "").strip()
        statement = localize_text(str(durable_candidate.get("statement") or "")).strip()
        evidence_strength = str(durable_candidate.get("evidence_strength") or "").strip()
        has_explicit_confirmation = durable_candidate.get("has_explicit_confirmation") is True
        promotion_basis = str(durable_candidate.get("promotion_basis") or "").strip()
        promotion_eligibility = str(durable_candidate.get("promotion_eligibility") or "").strip()
        created_at = str(durable_candidate.get("created_at") or "").strip()
        updated_at = str(durable_candidate.get("updated_at") or "").strip()
        if (
            not candidate_id
            or candidate_scope != "durable_candidate"
            or candidate_family != "correction_rewrite_preference"
            or not statement
            or evidence_strength != "explicit_single_artifact"
            or not has_explicit_confirmation
            or promotion_basis != "explicit_confirmation"
            or promotion_eligibility != "eligible_for_review"
            or not created_at
            or not updated_at
        ):
            return None

        supporting_artifact_ids = [
            artifact_id
            for raw_artifact_id in durable_candidate.get("supporting_artifact_ids", [])
            if isinstance(raw_artifact_id, str)
            and (artifact_id := raw_artifact_id.strip())
        ]
        supporting_source_message_ids = [
            source_message_id
            for raw_source_message_id in durable_candidate.get("supporting_source_message_ids", [])
            if isinstance(raw_source_message_id, str)
            and (source_message_id := raw_source_message_id.strip())
        ]
        supporting_signal_refs: list[dict[str, str]] = []
        for raw_ref in durable_candidate.get("supporting_signal_refs", []):
            if not isinstance(raw_ref, dict):
                continue
            signal_name = str(raw_ref.get("signal_name") or "").strip()
            relationship = str(raw_ref.get("relationship") or "").strip()
            if not signal_name or relationship not in {"primary_basis", "supporting_evidence"}:
                continue
            supporting_signal_refs.append(
                {
                    "signal_name": signal_name,
                    "relationship": relationship,
                }
            )

        supporting_confirmation_refs: list[dict[str, str]] = []
        for raw_ref in durable_candidate.get("supporting_confirmation_refs", []):
            if not isinstance(raw_ref, dict):
                continue
            ref_artifact_id = str(raw_ref.get("artifact_id") or "").strip()
            ref_source_message_id = self._serialize_source_message_id(raw_ref.get("source_message_id"))
            ref_candidate_id = str(raw_ref.get("candidate_id") or "").strip()
            ref_candidate_updated_at = str(raw_ref.get("candidate_updated_at") or "").strip()
            confirmation_label = str(raw_ref.get("confirmation_label") or "").strip()
            recorded_at = str(raw_ref.get("recorded_at") or "").strip()
            if (
                not ref_artifact_id
                or ref_source_message_id is None
                or ref_candidate_id != candidate_id
                or not ref_candidate_updated_at
                or confirmation_label != "explicit_reuse_confirmation"
                or not recorded_at
            ):
                continue
            supporting_confirmation_refs.append(
                {
                    "artifact_id": ref_artifact_id,
                    "source_message_id": ref_source_message_id,
                    "candidate_id": ref_candidate_id,
                    "candidate_updated_at": ref_candidate_updated_at,
                    "confirmation_label": confirmation_label,
                    "recorded_at": recorded_at,
                }
            )

        if not supporting_artifact_ids or not supporting_source_message_ids or not supporting_signal_refs:
            return None
        if len(supporting_confirmation_refs) != 1:
            return None
        confirmation_ref = supporting_confirmation_refs[0]
        if (
            confirmation_ref["artifact_id"] not in supporting_artifact_ids
            or confirmation_ref["source_message_id"] not in supporting_source_message_ids
        ):
            return None

        return {
            "candidate_id": candidate_id,
            "candidate_scope": candidate_scope,
            "candidate_family": candidate_family,
            "statement": statement,
            "supporting_artifact_ids": supporting_artifact_ids,
            "supporting_source_message_ids": supporting_source_message_ids,
            "supporting_signal_refs": supporting_signal_refs,
            "supporting_confirmation_refs": supporting_confirmation_refs,
            "evidence_strength": evidence_strength,
            "has_explicit_confirmation": has_explicit_confirmation,
            "promotion_basis": promotion_basis,
            "promotion_eligibility": promotion_eligibility,
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def _build_recurrence_aggregate_review_ref(
        self,
        *,
        message: dict[str, Any],
        artifact_id: str,
        source_message_id: str,
        candidate_id: str,
        candidate_updated_at: str,
    ) -> dict[str, Any] | None:
        review_record = self._serialize_candidate_review_record(message.get("candidate_review_record"))
        if review_record is None:
            return None
        if (
            str(review_record.get("artifact_id") or "").strip() != artifact_id
            or self._serialize_source_message_id(review_record.get("source_message_id")) != source_message_id
            or str(review_record.get("candidate_id") or "").strip() != candidate_id
            or str(review_record.get("candidate_updated_at") or "").strip() != candidate_updated_at
        ):
            return None
        return {
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "candidate_id": candidate_id,
            "candidate_updated_at": candidate_updated_at,
            "review_action": str(review_record.get("review_action") or "").strip(),
            "review_status": str(review_record.get("review_status") or "").strip(),
            "recorded_at": str(review_record.get("recorded_at") or "").strip(),
        }

    def _build_recurrence_aggregate_promotion_marker(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        aggregate_key = aggregate_candidate.get("aggregate_key")
        if not isinstance(aggregate_key, dict):
            return None
        required_identity_fields = (
            "candidate_family",
            "key_scope",
            "key_version",
            "derivation_source",
            "normalized_delta_fingerprint",
        )
        if any(not str(aggregate_key.get(field_name) or "").strip() for field_name in required_identity_fields):
            return None

        recurrence_count = aggregate_candidate.get("recurrence_count")
        if not isinstance(recurrence_count, int) or recurrence_count < 2:
            return None
        if str(aggregate_candidate.get("scope_boundary") or "").strip() != "same_session_current_state_only":
            return None
        if str(aggregate_candidate.get("confidence_marker") or "").strip() != "same_session_exact_key_match":
            return None

        derived_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not derived_at:
            return None

        return {
            "promotion_basis": "same_session_exact_recurrence_aggregate",
            "promotion_eligibility": "blocked_pending_reviewed_memory_boundary",
            "reviewed_memory_boundary": "not_open",
            "marker_version": "same_session_blocked_reviewed_memory_v1",
            "derived_at": derived_at,
        }

    def _build_recurrence_aggregate_reviewed_memory_precondition_status(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        aggregate_key = aggregate_candidate.get("aggregate_key")
        if not isinstance(aggregate_key, dict):
            return None
        required_identity_fields = (
            "candidate_family",
            "key_scope",
            "key_version",
            "derivation_source",
            "normalized_delta_fingerprint",
        )
        if any(not str(aggregate_key.get(field_name) or "").strip() for field_name in required_identity_fields):
            return None

        recurrence_count = aggregate_candidate.get("recurrence_count")
        if not isinstance(recurrence_count, int) or recurrence_count < 2:
            return None
        if str(aggregate_candidate.get("scope_boundary") or "").strip() != "same_session_current_state_only":
            return None
        if str(aggregate_candidate.get("confidence_marker") or "").strip() != "same_session_exact_key_match":
            return None

        expected_promotion_marker = self._build_recurrence_aggregate_promotion_marker(aggregate_candidate)
        if expected_promotion_marker is None:
            return None
        current_promotion_marker = aggregate_candidate.get("aggregate_promotion_marker")
        if not isinstance(current_promotion_marker, dict) or dict(current_promotion_marker) != expected_promotion_marker:
            return None

        evaluated_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        return {
            "status_version": "same_session_reviewed_memory_preconditions_v1",
            "overall_status": "blocked_all_required",
            "all_required": True,
            "preconditions": [
                "reviewed_memory_boundary_defined",
                "rollback_ready_reviewed_memory_effect",
                "disable_ready_reviewed_memory_effect",
                "conflict_visible_reviewed_memory_scope",
                "operator_auditable_reviewed_memory_transition",
            ],
            "evaluated_at": evaluated_at,
        }

    def _build_recurrence_aggregate_reviewed_memory_boundary_draft(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        aggregate_key = aggregate_candidate.get("aggregate_key")
        if not isinstance(aggregate_key, dict):
            return None
        required_identity_fields = (
            "candidate_family",
            "key_scope",
            "key_version",
            "derivation_source",
            "normalized_delta_fingerprint",
        )
        if any(not str(aggregate_key.get(field_name) or "").strip() for field_name in required_identity_fields):
            return None

        recurrence_count = aggregate_candidate.get("recurrence_count")
        if not isinstance(recurrence_count, int) or recurrence_count < 2:
            return None
        if str(aggregate_candidate.get("scope_boundary") or "").strip() != "same_session_current_state_only":
            return None
        if str(aggregate_candidate.get("confidence_marker") or "").strip() != "same_session_exact_key_match":
            return None

        expected_promotion_marker = self._build_recurrence_aggregate_promotion_marker(aggregate_candidate)
        if expected_promotion_marker is None:
            return None
        current_promotion_marker = aggregate_candidate.get("aggregate_promotion_marker")
        if not isinstance(current_promotion_marker, dict) or dict(current_promotion_marker) != expected_promotion_marker:
            return None

        expected_precondition_status = self._build_recurrence_aggregate_reviewed_memory_precondition_status(
            aggregate_candidate
        )
        if expected_precondition_status is None:
            return None
        current_precondition_status = aggregate_candidate.get("reviewed_memory_precondition_status")
        if (
            not isinstance(current_precondition_status, dict)
            or dict(current_precondition_status) != expected_precondition_status
        ):
            return None

        supporting_source_message_refs = []
        for raw_ref in aggregate_candidate.get("supporting_source_message_refs", []):
            if not isinstance(raw_ref, dict):
                return None
            artifact_id = str(raw_ref.get("artifact_id") or "").strip()
            source_message_id = str(raw_ref.get("source_message_id") or "").strip()
            if not artifact_id or not source_message_id:
                return None
            supporting_source_message_refs.append(
                {
                    "artifact_id": artifact_id,
                    "source_message_id": source_message_id,
                }
            )

        supporting_candidate_refs = []
        for raw_ref in aggregate_candidate.get("supporting_candidate_refs", []):
            if not isinstance(raw_ref, dict):
                return None
            artifact_id = str(raw_ref.get("artifact_id") or "").strip()
            source_message_id = str(raw_ref.get("source_message_id") or "").strip()
            candidate_id = str(raw_ref.get("candidate_id") or "").strip()
            candidate_updated_at = str(raw_ref.get("candidate_updated_at") or "").strip()
            if not artifact_id or not source_message_id or not candidate_id or not candidate_updated_at:
                return None
            supporting_candidate_refs.append(
                {
                    "artifact_id": artifact_id,
                    "source_message_id": source_message_id,
                    "candidate_id": candidate_id,
                    "candidate_updated_at": candidate_updated_at,
                }
            )

        if len(supporting_source_message_refs) < 2 or len(supporting_candidate_refs) < 2:
            return None

        drafted_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not drafted_at:
            return None

        boundary_draft = {
            "boundary_version": "fixed_narrow_reviewed_scope_v1",
            "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": {
                field_name: str(aggregate_key.get(field_name) or "").strip()
                for field_name in required_identity_fields
            },
            "supporting_source_message_refs": supporting_source_message_refs,
            "supporting_candidate_refs": supporting_candidate_refs,
            "boundary_stage": "draft_not_applied",
            "drafted_at": drafted_at,
        }

        supporting_review_refs = []
        for raw_ref in aggregate_candidate.get("supporting_review_refs", []):
            if not isinstance(raw_ref, dict):
                return None
            artifact_id = str(raw_ref.get("artifact_id") or "").strip()
            source_message_id = str(raw_ref.get("source_message_id") or "").strip()
            candidate_id = str(raw_ref.get("candidate_id") or "").strip()
            candidate_updated_at = str(raw_ref.get("candidate_updated_at") or "").strip()
            review_action = str(raw_ref.get("review_action") or "").strip()
            review_status = str(raw_ref.get("review_status") or "").strip()
            recorded_at = str(raw_ref.get("recorded_at") or "").strip()
            if (
                not artifact_id
                or not source_message_id
                or not candidate_id
                or not candidate_updated_at
                or not review_action
                or not review_status
                or not recorded_at
            ):
                return None
            supporting_review_refs.append(
                {
                    "artifact_id": artifact_id,
                    "source_message_id": source_message_id,
                    "candidate_id": candidate_id,
                    "candidate_updated_at": candidate_updated_at,
                    "review_action": review_action,
                    "review_status": review_status,
                    "recorded_at": recorded_at,
                }
            )
        if supporting_review_refs:
            boundary_draft["supporting_review_refs"] = supporting_review_refs

        return boundary_draft

    def _build_recurrence_aggregate_reviewed_memory_rollback_contract(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_boundary_draft = self._build_recurrence_aggregate_reviewed_memory_boundary_draft(
            aggregate_candidate
        )
        if expected_boundary_draft is None:
            return None
        current_boundary_draft = aggregate_candidate.get("reviewed_memory_boundary_draft")
        if not isinstance(current_boundary_draft, dict) or dict(current_boundary_draft) != expected_boundary_draft:
            return None

        defined_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not defined_at:
            return None

        rollback_contract = {
            "rollback_version": "first_reviewed_memory_effect_reversal_v1",
            "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(expected_boundary_draft.get("aggregate_identity_ref") or {}),
            "supporting_source_message_refs": list(expected_boundary_draft.get("supporting_source_message_refs") or []),
            "supporting_candidate_refs": list(expected_boundary_draft.get("supporting_candidate_refs") or []),
            "rollback_target_kind": "future_applied_reviewed_memory_effect_only",
            "rollback_stage": "contract_only_not_applied",
            "audit_trace_expectation": "operator_visible_local_transition_required",
            "defined_at": defined_at,
        }
        supporting_review_refs = expected_boundary_draft.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            rollback_contract["supporting_review_refs"] = list(supporting_review_refs)
        return rollback_contract

    def _build_recurrence_aggregate_reviewed_memory_disable_contract(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_rollback_contract = self._build_recurrence_aggregate_reviewed_memory_rollback_contract(
            aggregate_candidate
        )
        if expected_rollback_contract is None:
            return None
        current_rollback_contract = aggregate_candidate.get("reviewed_memory_rollback_contract")
        if not isinstance(current_rollback_contract, dict) or dict(current_rollback_contract) != expected_rollback_contract:
            return None

        defined_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not defined_at:
            return None

        disable_contract = {
            "disable_version": "first_reviewed_memory_effect_stop_apply_v1",
            "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(expected_rollback_contract.get("aggregate_identity_ref") or {}),
            "supporting_source_message_refs": list(expected_rollback_contract.get("supporting_source_message_refs") or []),
            "supporting_candidate_refs": list(expected_rollback_contract.get("supporting_candidate_refs") or []),
            "disable_target_kind": "future_applied_reviewed_memory_effect_only",
            "disable_stage": "contract_only_not_applied",
            "effect_behavior": "stop_apply_without_reversal",
            "audit_trace_expectation": "operator_visible_local_transition_required",
            "defined_at": defined_at,
        }
        supporting_review_refs = expected_rollback_contract.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            disable_contract["supporting_review_refs"] = list(supporting_review_refs)
        return disable_contract

    def _build_recurrence_aggregate_reviewed_memory_conflict_contract(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_disable_contract = self._build_recurrence_aggregate_reviewed_memory_disable_contract(
            aggregate_candidate
        )
        if expected_disable_contract is None:
            return None
        current_disable_contract = aggregate_candidate.get("reviewed_memory_disable_contract")
        if not isinstance(current_disable_contract, dict) or dict(current_disable_contract) != expected_disable_contract:
            return None

        defined_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not defined_at:
            return None

        conflict_contract = {
            "conflict_version": "first_reviewed_memory_scope_visibility_v1",
            "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(expected_disable_contract.get("aggregate_identity_ref") or {}),
            "supporting_source_message_refs": list(expected_disable_contract.get("supporting_source_message_refs") or []),
            "supporting_candidate_refs": list(expected_disable_contract.get("supporting_candidate_refs") or []),
            "conflict_target_categories": [
                "future_reviewed_memory_candidate_draft_vs_applied_effect",
                "future_applied_reviewed_memory_effect_vs_applied_effect",
            ],
            "conflict_visibility_stage": "contract_only_not_resolved",
            "audit_trace_expectation": "operator_visible_local_transition_required",
            "defined_at": defined_at,
        }
        supporting_review_refs = expected_disable_contract.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            conflict_contract["supporting_review_refs"] = list(supporting_review_refs)
        return conflict_contract

    def _build_recurrence_aggregate_reviewed_memory_transition_audit_contract(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_conflict_contract = self._build_recurrence_aggregate_reviewed_memory_conflict_contract(
            aggregate_candidate
        )
        if expected_conflict_contract is None:
            return None
        current_conflict_contract = aggregate_candidate.get("reviewed_memory_conflict_contract")
        if not isinstance(current_conflict_contract, dict) or dict(current_conflict_contract) != expected_conflict_contract:
            return None

        defined_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not defined_at:
            return None

        transition_audit_contract = {
            "audit_version": "first_reviewed_memory_transition_identity_v1",
            "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(expected_conflict_contract.get("aggregate_identity_ref") or {}),
            "supporting_source_message_refs": list(expected_conflict_contract.get("supporting_source_message_refs") or []),
            "supporting_candidate_refs": list(expected_conflict_contract.get("supporting_candidate_refs") or []),
            "transition_action_vocabulary": [
                "future_reviewed_memory_apply",
                "future_reviewed_memory_stop_apply",
                "future_reviewed_memory_reversal",
                "future_reviewed_memory_conflict_visibility",
            ],
            "transition_identity_requirement": "canonical_local_transition_id_required",
            "operator_visible_reason_boundary": "explicit_reason_or_note_required",
            "audit_stage": "contract_only_not_emitted",
            "audit_store_boundary": "canonical_transition_record_separate_from_task_log",
            "post_transition_invariants": "aggregate_identity_and_contract_refs_retained",
            "defined_at": defined_at,
        }
        supporting_review_refs = expected_conflict_contract.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            transition_audit_contract["supporting_review_refs"] = list(supporting_review_refs)
        return transition_audit_contract

    def _build_recurrence_aggregate_reviewed_memory_unblock_contract(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_precondition_status = self._build_recurrence_aggregate_reviewed_memory_precondition_status(
            aggregate_candidate
        )
        if expected_precondition_status is None:
            return None
        current_precondition_status = aggregate_candidate.get("reviewed_memory_precondition_status")
        if (
            not isinstance(current_precondition_status, dict)
            or dict(current_precondition_status) != expected_precondition_status
        ):
            return None

        expected_transition_audit_contract = self._build_recurrence_aggregate_reviewed_memory_transition_audit_contract(
            aggregate_candidate
        )
        if expected_transition_audit_contract is None:
            return None
        current_transition_audit_contract = aggregate_candidate.get("reviewed_memory_transition_audit_contract")
        if (
            not isinstance(current_transition_audit_contract, dict)
            or dict(current_transition_audit_contract) != expected_transition_audit_contract
        ):
            return None

        evaluated_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        required_preconditions = expected_precondition_status.get("preconditions")
        if not isinstance(required_preconditions, list) or not required_preconditions:
            return None

        return {
            "unblock_version": "same_session_reviewed_memory_unblock_v1",
            "required_preconditions": [str(item) for item in required_preconditions if str(item).strip()],
            "unblock_status": "blocked_all_required",
            "satisfaction_basis_boundary": "canonical_reviewed_memory_layer_capabilities_only",
            "partial_state_policy": "partial_states_not_materialized",
            "evaluated_at": evaluated_at,
        }

    def _build_recurrence_aggregate_reviewed_memory_capability_status(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_unblock_contract = self._build_recurrence_aggregate_reviewed_memory_unblock_contract(
            aggregate_candidate
        )
        if expected_unblock_contract is None:
            return None
        current_unblock_contract = aggregate_candidate.get("reviewed_memory_unblock_contract")
        if not isinstance(current_unblock_contract, dict) or dict(current_unblock_contract) != expected_unblock_contract:
            return None

        evaluated_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        required_preconditions = expected_unblock_contract.get("required_preconditions")
        if not isinstance(required_preconditions, list) or not required_preconditions:
            return None

        expected_capability_basis = self._build_recurrence_aggregate_reviewed_memory_capability_basis(
            aggregate_candidate
        )
        current_capability_basis = aggregate_candidate.get("reviewed_memory_capability_basis")
        if expected_capability_basis is None:
            if current_capability_basis is not None:
                return None
        else:
            if not isinstance(current_capability_basis, dict) or dict(current_capability_basis) != expected_capability_basis:
                return None

        capability_outcome = (
            "unblocked_all_required"
            if expected_capability_basis is not None
            else "blocked_all_required"
        )

        return {
            "capability_version": "same_session_reviewed_memory_capabilities_v1",
            "required_preconditions": [str(item) for item in required_preconditions if str(item).strip()],
            "capability_outcome": capability_outcome,
            "satisfaction_basis_boundary": "canonical_reviewed_memory_layer_capabilities_only",
            "partial_state_policy": "partial_states_not_materialized",
            "evaluated_at": evaluated_at,
        }

    def _resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_draft = self._build_recurrence_aggregate_reviewed_memory_boundary_draft(
            aggregate_candidate
        )
        if expected_boundary_draft is None:
            return None
        current_boundary_draft = aggregate_candidate.get("reviewed_memory_boundary_draft")
        if not isinstance(current_boundary_draft, dict) or dict(current_boundary_draft) != expected_boundary_draft:
            return None

        expected_aggregate_identity_ref = expected_boundary_draft.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_draft.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or []) != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_draft.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or []) != list(expected_supporting_candidate_refs)
        ):
            return None

        required_preconditions = source_context.get("required_preconditions")
        if (
            not isinstance(required_preconditions, list)
            or "reviewed_memory_boundary_defined" not in required_preconditions
        ):
            return None

        defined_at = str(source_context.get("evaluated_at") or expected_boundary_draft.get("drafted_at") or "").strip()
        if not defined_at:
            return None

        boundary_source_ref = {
            "ref_version": "same_session_reviewed_memory_boundary_source_ref_v1",
            "ref_kind": "aggregate_reviewed_memory_trigger_affordance",
            "ref_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(expected_aggregate_identity_ref),
            "supporting_source_message_refs": list(expected_supporting_source_message_refs),
            "supporting_candidate_refs": list(expected_supporting_candidate_refs),
            "trigger_action_label": "검토 메모 적용 시작",
            "trigger_state": "visible_disabled",
            "target_label": "eligible_for_reviewed_memory_draft_planning_only",
            "target_boundary": "reviewed_memory_draft_planning_only",
            "defined_at": defined_at,
        }

        expected_supporting_review_refs = expected_boundary_draft.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None
            boundary_source_ref["supporting_review_refs"] = list(expected_supporting_review_refs)

        return boundary_source_ref

    def _build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_rollback_contract = self._build_recurrence_aggregate_reviewed_memory_rollback_contract(
            aggregate_candidate
        )
        if expected_rollback_contract is None:
            return None
        current_rollback_contract = aggregate_candidate.get("reviewed_memory_rollback_contract")
        if not isinstance(current_rollback_contract, dict) or dict(current_rollback_contract) != expected_rollback_contract:
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if expected_boundary_source_ref is None:
            return None

        expected_aggregate_identity_ref = expected_rollback_contract.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_rollback_contract.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_rollback_contract.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_rollback_contract.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        required_preconditions = source_context.get("required_preconditions")
        if (
            not isinstance(required_preconditions, list)
            or "rollback_ready_reviewed_memory_effect" not in required_preconditions
        ):
            return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        expected_applied_effect_target = self._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_applied_effect_target, dict):
            return None

        defined_at = str(source_context.get("evaluated_at") or expected_rollback_contract.get("defined_at") or "").strip()
        if not defined_at:
            return None

        aggregate_identity_ref = expected_applied_effect_target.get("aggregate_identity_ref")
        supporting_source_message_refs = expected_applied_effect_target.get(
            "supporting_source_message_refs"
        )
        supporting_candidate_refs = expected_applied_effect_target.get("supporting_candidate_refs")
        boundary_source_ref = expected_applied_effect_target.get("boundary_source_ref")
        effect_target_kind = str(expected_applied_effect_target.get("effect_target_kind") or "").strip()
        target_capability_boundary = str(
            expected_applied_effect_target.get("target_capability_boundary") or ""
        ).strip()
        target_stage = str(expected_applied_effect_target.get("target_stage") or "").strip()
        applied_effect_id = str(expected_applied_effect_target.get("applied_effect_id") or "").strip()
        present_locally_at = str(expected_applied_effect_target.get("present_locally_at") or "").strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
            or effect_target_kind != "applied_reviewed_memory_effect"
            or target_capability_boundary != "local_effect_presence_only"
            or target_stage != "effect_present_local_only"
            or not applied_effect_id
            or not present_locally_at
        ):
            return None

        supporting_review_refs = expected_applied_effect_target.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and any(
            not isinstance(item, dict) for item in supporting_review_refs
        ):
            return None

        if dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref):
            return None

        if list(supporting_source_message_refs) != list(expected_supporting_source_message_refs):
            return None

        if list(supporting_candidate_refs) != list(expected_supporting_candidate_refs):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if not isinstance(supporting_review_refs, list):
                return None
            if list(supporting_review_refs) != list(expected_supporting_review_refs):
                return None
        elif isinstance(supporting_review_refs, list) and supporting_review_refs:
            return None

        if dict(boundary_source_ref) != dict(expected_boundary_source_ref):
            return None

        if present_locally_at != defined_at:
            return None

        handle_identity_payload: dict[str, Any] = {
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "rollback_contract_ref": dict(expected_rollback_contract),
            "applied_effect_id": applied_effect_id,
            "defined_at": defined_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            handle_identity_payload["supporting_review_refs"] = list(supporting_review_refs)

        handle_id = (
            "reviewed-memory-handle:"
            + hashlib.sha256(
                json.dumps(handle_identity_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()[:24]
        )

        reversible_effect_handle = {
            "handle_version": "first_same_session_reviewed_memory_reversible_effect_handle_v1",
            "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "rollback_contract_ref": dict(expected_rollback_contract),
            "effect_target_kind": effect_target_kind,
            "effect_capability": "reversible_local_only",
            "effect_invariant": "retain_identity_supporting_refs_boundary_and_audit",
            "effect_stage": "handle_defined_not_applied",
            "handle_id": handle_id,
            "defined_at": defined_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            reversible_effect_handle["supporting_review_refs"] = list(supporting_review_refs)
        return reversible_effect_handle

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_boundary_source_ref, dict):
            return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        expected_aggregate_identity_ref = expected_boundary_source_ref.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_source_ref.get(
            "supporting_source_message_refs"
        )
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_source_ref.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_boundary_source_ref.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        evaluated_at = str(source_context.get("evaluated_at") or aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        expected_local_effect_presence_event_source = (
            self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                aggregate_candidate,
                source_context,
            )
        )
        if not isinstance(expected_local_effect_presence_event_source, dict):
            return None

        aggregate_identity_ref = expected_local_effect_presence_event_source.get("aggregate_identity_ref")
        supporting_source_message_refs = expected_local_effect_presence_event_source.get(
            "supporting_source_message_refs"
        )
        supporting_candidate_refs = expected_local_effect_presence_event_source.get("supporting_candidate_refs")
        boundary_source_ref = expected_local_effect_presence_event_source.get("boundary_source_ref")
        effect_target_kind = str(
            expected_local_effect_presence_event_source.get("effect_target_kind") or ""
        ).strip()
        event_capability_boundary = str(
            expected_local_effect_presence_event_source.get("event_capability_boundary") or ""
        ).strip()
        event_stage = str(expected_local_effect_presence_event_source.get("event_stage") or "").strip()
        applied_effect_id = str(expected_local_effect_presence_event_source.get("applied_effect_id") or "").strip()
        present_locally_at = str(expected_local_effect_presence_event_source.get("present_locally_at") or "").strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
            or effect_target_kind != "applied_reviewed_memory_effect"
            or event_capability_boundary != "local_effect_presence_only"
            or event_stage != "presence_event_recorded_local_only"
            or not applied_effect_id
            or not present_locally_at
        ):
            return None

        supporting_review_refs = expected_local_effect_presence_event_source.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and any(
            not isinstance(item, dict) for item in supporting_review_refs
        ):
            return None

        if dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref):
            return None

        if list(supporting_source_message_refs) != list(expected_supporting_source_message_refs):
            return None

        if list(supporting_candidate_refs) != list(expected_supporting_candidate_refs):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if not isinstance(supporting_review_refs, list):
                return None
            if list(supporting_review_refs) != list(expected_supporting_review_refs):
                return None
        elif isinstance(supporting_review_refs, list) and supporting_review_refs:
            return None

        if dict(boundary_source_ref) != dict(expected_boundary_source_ref):
            return None

        if present_locally_at != evaluated_at:
            return None

        local_effect_presence_record = {
            "source_version": "first_same_session_reviewed_memory_local_effect_presence_record_v1",
            "source_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "effect_target_kind": effect_target_kind,
            "source_capability_boundary": "local_effect_presence_only",
            "source_stage": "presence_recorded_local_only",
            "applied_effect_id": applied_effect_id,
            "present_locally_at": present_locally_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            local_effect_presence_record["supporting_review_refs"] = list(supporting_review_refs)
        return local_effect_presence_record

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_boundary_source_ref, dict):
            return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        local_effect_presence_proof_record = (
            self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
                aggregate_candidate,
                source_context,
            )
        )
        if not isinstance(local_effect_presence_proof_record, dict):
            return None

        aggregate_identity_ref = local_effect_presence_proof_record.get("aggregate_identity_ref")
        supporting_source_message_refs = local_effect_presence_proof_record.get("supporting_source_message_refs")
        supporting_candidate_refs = local_effect_presence_proof_record.get("supporting_candidate_refs")
        boundary_source_ref = local_effect_presence_proof_record.get("boundary_source_ref")
        applied_effect_id = str(local_effect_presence_proof_record.get("applied_effect_id") or "").strip()
        present_locally_at = str(local_effect_presence_proof_record.get("present_locally_at") or "").strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
            or not applied_effect_id
            or not present_locally_at
        ):
            return None

        supporting_review_refs = local_effect_presence_proof_record.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and any(
            not isinstance(item, dict) for item in supporting_review_refs
        ):
            return None

        expected_aggregate_identity_ref = expected_boundary_source_ref.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_source_ref.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(supporting_source_message_refs) != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_source_ref.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(supporting_candidate_refs) != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_boundary_source_ref.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if not isinstance(supporting_review_refs, list):
                return None
            if list(supporting_review_refs) != list(expected_supporting_review_refs):
                return None
        elif isinstance(supporting_review_refs, list) and supporting_review_refs:
            return None

        if dict(boundary_source_ref) != dict(expected_boundary_source_ref):
            return None

        expected_present_locally_at = str(
            source_context.get("evaluated_at") or aggregate_candidate.get("last_seen_at") or ""
        ).strip()
        if not expected_present_locally_at or present_locally_at != expected_present_locally_at:
            return None

        local_effect_presence_proof_boundary = {
            "proof_boundary_version": "first_same_session_reviewed_memory_local_effect_presence_proof_boundary_v1",
            "proof_boundary_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "effect_target_kind": "applied_reviewed_memory_effect",
            "proof_capability_boundary": "local_effect_presence_only",
            "proof_stage": "first_presence_proved_local_only",
            "applied_effect_id": applied_effect_id,
            "present_locally_at": present_locally_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            local_effect_presence_proof_boundary["supporting_review_refs"] = list(supporting_review_refs)
        return local_effect_presence_proof_boundary

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if expected_boundary_source_ref is None:
            return None

        expected_aggregate_identity_ref = expected_boundary_source_ref.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_source_ref.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_source_ref.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_boundary_source_ref.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        evaluated_at = str(source_context.get("evaluated_at") or aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        raw_store_entries = aggregate_candidate.get(
            "_reviewed_memory_local_effect_presence_proof_record_store_entries"
        )
        if not isinstance(raw_store_entries, list) or not raw_store_entries:
            return None

        matching_records: list[dict[str, Any]] = []
        for raw_store_entry in raw_store_entries:
            if not isinstance(raw_store_entry, dict):
                continue

            proof_record_version = str(raw_store_entry.get("proof_record_version") or "").strip()
            proof_record_scope = str(raw_store_entry.get("proof_record_scope") or "").strip()
            aggregate_identity_ref = raw_store_entry.get("aggregate_identity_ref")
            supporting_source_message_refs = raw_store_entry.get("supporting_source_message_refs")
            supporting_candidate_refs = raw_store_entry.get("supporting_candidate_refs")
            boundary_source_ref = raw_store_entry.get("boundary_source_ref")
            effect_target_kind = str(raw_store_entry.get("effect_target_kind") or "").strip()
            proof_capability_boundary = str(raw_store_entry.get("proof_capability_boundary") or "").strip()
            proof_record_stage = str(raw_store_entry.get("proof_record_stage") or "").strip()
            applied_effect_id = str(raw_store_entry.get("applied_effect_id") or "").strip()
            present_locally_at = str(raw_store_entry.get("present_locally_at") or "").strip()
            if (
                proof_record_version
                != "first_same_session_reviewed_memory_local_effect_presence_proof_record_v1"
                or proof_record_scope != "same_session_exact_recurrence_aggregate_only"
                or not isinstance(aggregate_identity_ref, dict)
                or dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref)
                or not isinstance(supporting_source_message_refs, list)
                or list(supporting_source_message_refs) != list(expected_supporting_source_message_refs)
                or not isinstance(supporting_candidate_refs, list)
                or list(supporting_candidate_refs) != list(expected_supporting_candidate_refs)
                or not isinstance(boundary_source_ref, dict)
                or dict(boundary_source_ref) != dict(expected_boundary_source_ref)
                or effect_target_kind != "applied_reviewed_memory_effect"
                or proof_capability_boundary != "local_effect_presence_only"
                or proof_record_stage != "canonical_presence_recorded_local_only"
                or not applied_effect_id
                or not present_locally_at
            ):
                continue

            supporting_review_refs = raw_store_entry.get("supporting_review_refs")
            if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
                if not isinstance(supporting_review_refs, list):
                    continue
                if list(supporting_review_refs) != list(expected_supporting_review_refs):
                    continue
            elif isinstance(supporting_review_refs, list) and supporting_review_refs:
                continue

            matching_record = {
                "proof_record_version": proof_record_version,
                "proof_record_scope": proof_record_scope,
                "aggregate_identity_ref": dict(aggregate_identity_ref),
                "supporting_source_message_refs": list(supporting_source_message_refs),
                "supporting_candidate_refs": list(supporting_candidate_refs),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": effect_target_kind,
                "proof_capability_boundary": proof_capability_boundary,
                "proof_record_stage": proof_record_stage,
                "applied_effect_id": applied_effect_id,
                "present_locally_at": present_locally_at,
            }
            if isinstance(supporting_review_refs, list) and supporting_review_refs:
                matching_record["supporting_review_refs"] = list(supporting_review_refs)
            matching_records.append(matching_record)

        if len(matching_records) != 1:
            return None
        return matching_records[0]

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_boundary_source_ref, dict):
            return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        expected_aggregate_identity_ref = expected_boundary_source_ref.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_source_ref.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_source_ref.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_boundary_source_ref.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        evaluated_at = str(source_context.get("evaluated_at") or aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        local_effect_presence_proof_boundary = (
            self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                aggregate_candidate,
                source_context,
            )
        )
        if not isinstance(local_effect_presence_proof_boundary, dict):
            return None

        aggregate_identity_ref = local_effect_presence_proof_boundary.get("aggregate_identity_ref")
        supporting_source_message_refs = local_effect_presence_proof_boundary.get(
            "supporting_source_message_refs"
        )
        supporting_candidate_refs = local_effect_presence_proof_boundary.get("supporting_candidate_refs")
        boundary_source_ref = local_effect_presence_proof_boundary.get("boundary_source_ref")
        effect_target_kind = str(local_effect_presence_proof_boundary.get("effect_target_kind") or "").strip()
        proof_capability_boundary = str(
            local_effect_presence_proof_boundary.get("proof_capability_boundary") or ""
        ).strip()
        proof_stage = str(local_effect_presence_proof_boundary.get("proof_stage") or "").strip()
        applied_effect_id = str(local_effect_presence_proof_boundary.get("applied_effect_id") or "").strip()
        present_locally_at = str(local_effect_presence_proof_boundary.get("present_locally_at") or "").strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
            or effect_target_kind != "applied_reviewed_memory_effect"
            or proof_capability_boundary != "local_effect_presence_only"
            or proof_stage != "first_presence_proved_local_only"
            or not applied_effect_id
            or not present_locally_at
        ):
            return None

        supporting_review_refs = local_effect_presence_proof_boundary.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and any(
            not isinstance(item, dict) for item in supporting_review_refs
        ):
            return None

        if dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref):
            return None

        if list(supporting_source_message_refs) != list(expected_supporting_source_message_refs):
            return None

        if list(supporting_candidate_refs) != list(expected_supporting_candidate_refs):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if not isinstance(supporting_review_refs, list):
                return None
            if list(supporting_review_refs) != list(expected_supporting_review_refs):
                return None
        elif isinstance(supporting_review_refs, list) and supporting_review_refs:
            return None

        if dict(boundary_source_ref) != dict(expected_boundary_source_ref):
            return None

        if present_locally_at != evaluated_at:
            return None

        local_effect_presence_fact_source_instance = {
            "fact_source_instance_version": (
                "first_same_session_reviewed_memory_local_effect_presence_fact_source_instance_v1"
            ),
            "fact_source_instance_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "effect_target_kind": effect_target_kind,
            "fact_capability_boundary": "local_effect_presence_only",
            "fact_stage": "presence_fact_available_local_only",
            "applied_effect_id": applied_effect_id,
            "present_locally_at": present_locally_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            local_effect_presence_fact_source_instance["supporting_review_refs"] = list(
                supporting_review_refs
            )
        return local_effect_presence_fact_source_instance

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_boundary_source_ref, dict):
            return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        expected_aggregate_identity_ref = expected_boundary_source_ref.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_source_ref.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_source_ref.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_boundary_source_ref.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        evaluated_at = str(source_context.get("evaluated_at") or aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        local_effect_presence_fact_source_instance = (
            self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                aggregate_candidate,
                source_context,
            )
        )
        if not isinstance(local_effect_presence_fact_source_instance, dict):
            return None

        aggregate_identity_ref = local_effect_presence_fact_source_instance.get("aggregate_identity_ref")
        supporting_source_message_refs = local_effect_presence_fact_source_instance.get(
            "supporting_source_message_refs"
        )
        supporting_candidate_refs = local_effect_presence_fact_source_instance.get("supporting_candidate_refs")
        boundary_source_ref = local_effect_presence_fact_source_instance.get("boundary_source_ref")
        effect_target_kind = str(
            local_effect_presence_fact_source_instance.get("effect_target_kind") or ""
        ).strip()
        fact_capability_boundary = str(
            local_effect_presence_fact_source_instance.get("fact_capability_boundary") or ""
        ).strip()
        fact_stage = str(local_effect_presence_fact_source_instance.get("fact_stage") or "").strip()
        applied_effect_id = str(local_effect_presence_fact_source_instance.get("applied_effect_id") or "").strip()
        present_locally_at = str(local_effect_presence_fact_source_instance.get("present_locally_at") or "").strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
            or effect_target_kind != "applied_reviewed_memory_effect"
            or fact_capability_boundary != "local_effect_presence_only"
            or fact_stage != "presence_fact_available_local_only"
            or not applied_effect_id
            or not present_locally_at
        ):
            return None

        supporting_review_refs = local_effect_presence_fact_source_instance.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and any(
            not isinstance(item, dict) for item in supporting_review_refs
        ):
            return None

        if dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref):
            return None

        if list(supporting_source_message_refs) != list(expected_supporting_source_message_refs):
            return None

        if list(supporting_candidate_refs) != list(expected_supporting_candidate_refs):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if not isinstance(supporting_review_refs, list):
                return None
            if list(supporting_review_refs) != list(expected_supporting_review_refs):
                return None
        elif isinstance(supporting_review_refs, list) and supporting_review_refs:
            return None

        if dict(boundary_source_ref) != dict(expected_boundary_source_ref):
            return None

        if present_locally_at != evaluated_at:
            return None

        local_effect_presence_fact_source = {
            "fact_source_version": "first_same_session_reviewed_memory_local_effect_presence_fact_source_v1",
            "fact_source_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "effect_target_kind": effect_target_kind,
            "fact_capability_boundary": "local_effect_presence_only",
            "fact_stage": "presence_fact_available_local_only",
            "applied_effect_id": applied_effect_id,
            "present_locally_at": present_locally_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            local_effect_presence_fact_source["supporting_review_refs"] = list(supporting_review_refs)
        return local_effect_presence_fact_source

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_boundary_source_ref, dict):
            return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        expected_aggregate_identity_ref = expected_boundary_source_ref.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_source_ref.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_source_ref.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_boundary_source_ref.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        evaluated_at = str(source_context.get("evaluated_at") or aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        local_effect_presence_fact_source = (
            self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                aggregate_candidate,
                source_context,
            )
        )
        if not isinstance(local_effect_presence_fact_source, dict):
            return None

        aggregate_identity_ref = local_effect_presence_fact_source.get("aggregate_identity_ref")
        supporting_source_message_refs = local_effect_presence_fact_source.get(
            "supporting_source_message_refs"
        )
        supporting_candidate_refs = local_effect_presence_fact_source.get("supporting_candidate_refs")
        boundary_source_ref = local_effect_presence_fact_source.get("boundary_source_ref")
        effect_target_kind = str(local_effect_presence_fact_source.get("effect_target_kind") or "").strip()
        fact_capability_boundary = str(
            local_effect_presence_fact_source.get("fact_capability_boundary") or ""
        ).strip()
        fact_stage = str(local_effect_presence_fact_source.get("fact_stage") or "").strip()
        applied_effect_id = str(local_effect_presence_fact_source.get("applied_effect_id") or "").strip()
        present_locally_at = str(local_effect_presence_fact_source.get("present_locally_at") or "").strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
            or effect_target_kind != "applied_reviewed_memory_effect"
            or fact_capability_boundary != "local_effect_presence_only"
            or fact_stage != "presence_fact_available_local_only"
            or not applied_effect_id
            or not present_locally_at
        ):
            return None

        supporting_review_refs = local_effect_presence_fact_source.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and any(
            not isinstance(item, dict) for item in supporting_review_refs
        ):
            return None

        if dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref):
            return None

        if list(supporting_source_message_refs) != list(expected_supporting_source_message_refs):
            return None

        if list(supporting_candidate_refs) != list(expected_supporting_candidate_refs):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if not isinstance(supporting_review_refs, list):
                return None
            if list(supporting_review_refs) != list(expected_supporting_review_refs):
                return None
        elif isinstance(supporting_review_refs, list) and supporting_review_refs:
            return None

        if dict(boundary_source_ref) != dict(expected_boundary_source_ref):
            return None

        if present_locally_at != evaluated_at:
            return None

        local_effect_presence_event = {
            "event_version": "first_same_session_reviewed_memory_local_effect_presence_event_v1",
            "event_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "effect_target_kind": effect_target_kind,
            "event_capability_boundary": "local_effect_presence_only",
            "event_stage": "presence_observed_local_only",
            "applied_effect_id": applied_effect_id,
            "present_locally_at": present_locally_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            local_effect_presence_event["supporting_review_refs"] = list(supporting_review_refs)
        return local_effect_presence_event

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if expected_boundary_source_ref is None:
            return None

        expected_aggregate_identity_ref = expected_boundary_source_ref.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_source_ref.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_source_ref.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_boundary_source_ref.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        evaluated_at = str(source_context.get("evaluated_at") or aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        expected_local_effect_presence_event = (
            self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
                aggregate_candidate,
                source_context,
            )
        )
        if not isinstance(expected_local_effect_presence_event, dict):
            return None

        aggregate_identity_ref = expected_local_effect_presence_event.get("aggregate_identity_ref")
        supporting_source_message_refs = expected_local_effect_presence_event.get(
            "supporting_source_message_refs"
        )
        supporting_candidate_refs = expected_local_effect_presence_event.get("supporting_candidate_refs")
        boundary_source_ref = expected_local_effect_presence_event.get("boundary_source_ref")
        effect_target_kind = str(expected_local_effect_presence_event.get("effect_target_kind") or "").strip()
        event_capability_boundary = str(
            expected_local_effect_presence_event.get("event_capability_boundary") or ""
        ).strip()
        event_stage = str(expected_local_effect_presence_event.get("event_stage") or "").strip()
        applied_effect_id = str(expected_local_effect_presence_event.get("applied_effect_id") or "").strip()
        present_locally_at = str(expected_local_effect_presence_event.get("present_locally_at") or "").strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
            or effect_target_kind != "applied_reviewed_memory_effect"
            or event_capability_boundary != "local_effect_presence_only"
            or event_stage != "presence_observed_local_only"
            or not applied_effect_id
            or not present_locally_at
        ):
            return None

        supporting_review_refs = expected_local_effect_presence_event.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and any(
            not isinstance(item, dict) for item in supporting_review_refs
        ):
            return None

        if dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref):
            return None

        if list(supporting_source_message_refs) != list(expected_supporting_source_message_refs):
            return None

        if list(supporting_candidate_refs) != list(expected_supporting_candidate_refs):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if not isinstance(supporting_review_refs, list):
                return None
            if list(supporting_review_refs) != list(expected_supporting_review_refs):
                return None
        elif isinstance(supporting_review_refs, list) and supporting_review_refs:
            return None

        if dict(boundary_source_ref) != dict(expected_boundary_source_ref):
            return None

        if present_locally_at != evaluated_at:
            return None

        local_effect_presence_event_producer = {
            "producer_version": "first_same_session_reviewed_memory_local_effect_presence_event_producer_v1",
            "producer_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "effect_target_kind": effect_target_kind,
            "producer_capability_boundary": "local_effect_presence_only",
            "producer_stage": "presence_event_recorded_local_only",
            "applied_effect_id": applied_effect_id,
            "present_locally_at": present_locally_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            local_effect_presence_event_producer["supporting_review_refs"] = list(supporting_review_refs)
        return local_effect_presence_event_producer

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_boundary_source_ref, dict):
            return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        expected_aggregate_identity_ref = expected_boundary_source_ref.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_source_ref.get(
            "supporting_source_message_refs"
        )
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_source_ref.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_boundary_source_ref.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        evaluated_at = str(source_context.get("evaluated_at") or aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        expected_local_effect_presence_event_producer = (
            self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                aggregate_candidate,
                source_context,
            )
        )
        if not isinstance(expected_local_effect_presence_event_producer, dict):
            return None

        aggregate_identity_ref = expected_local_effect_presence_event_producer.get("aggregate_identity_ref")
        supporting_source_message_refs = expected_local_effect_presence_event_producer.get(
            "supporting_source_message_refs"
        )
        supporting_candidate_refs = expected_local_effect_presence_event_producer.get(
            "supporting_candidate_refs"
        )
        boundary_source_ref = expected_local_effect_presence_event_producer.get("boundary_source_ref")
        effect_target_kind = str(
            expected_local_effect_presence_event_producer.get("effect_target_kind") or ""
        ).strip()
        producer_capability_boundary = str(
            expected_local_effect_presence_event_producer.get("producer_capability_boundary") or ""
        ).strip()
        producer_stage = str(expected_local_effect_presence_event_producer.get("producer_stage") or "").strip()
        applied_effect_id = str(
            expected_local_effect_presence_event_producer.get("applied_effect_id") or ""
        ).strip()
        present_locally_at = str(
            expected_local_effect_presence_event_producer.get("present_locally_at") or ""
        ).strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
            or effect_target_kind != "applied_reviewed_memory_effect"
            or producer_capability_boundary != "local_effect_presence_only"
            or producer_stage != "presence_event_recorded_local_only"
            or not applied_effect_id
            or not present_locally_at
        ):
            return None

        supporting_review_refs = expected_local_effect_presence_event_producer.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and any(
            not isinstance(item, dict) for item in supporting_review_refs
        ):
            return None

        if dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref):
            return None

        if list(supporting_source_message_refs) != list(expected_supporting_source_message_refs):
            return None

        if list(supporting_candidate_refs) != list(expected_supporting_candidate_refs):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if not isinstance(supporting_review_refs, list):
                return None
            if list(supporting_review_refs) != list(expected_supporting_review_refs):
                return None
        elif isinstance(supporting_review_refs, list) and supporting_review_refs:
            return None

        if dict(boundary_source_ref) != dict(expected_boundary_source_ref):
            return None

        if present_locally_at != evaluated_at:
            return None

        local_effect_presence_event_source = {
            "event_source_version": "first_same_session_reviewed_memory_local_effect_presence_event_source_v1",
            "event_source_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "effect_target_kind": effect_target_kind,
            "event_capability_boundary": "local_effect_presence_only",
            "event_stage": "presence_event_recorded_local_only",
            "applied_effect_id": applied_effect_id,
            "present_locally_at": present_locally_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            local_effect_presence_event_source["supporting_review_refs"] = list(supporting_review_refs)
        return local_effect_presence_event_source

    def _build_recurrence_aggregate_reviewed_memory_applied_effect_target(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if expected_boundary_source_ref is None:
            return None

        expected_unblock_contract = self._build_recurrence_aggregate_reviewed_memory_unblock_contract(
            aggregate_candidate
        )
        if expected_unblock_contract is None:
            return None
        current_unblock_contract = aggregate_candidate.get("reviewed_memory_unblock_contract")
        if not isinstance(current_unblock_contract, dict) or dict(current_unblock_contract) != expected_unblock_contract:
            return None

        expected_aggregate_identity_ref = expected_boundary_source_ref.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_boundary_source_ref.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_boundary_source_ref.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_boundary_source_ref.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if not first_seen_at:
            return None

        required_preconditions = expected_unblock_contract.get("required_preconditions")
        if (
            not isinstance(required_preconditions, list)
            or list(source_context.get("required_preconditions") or []) != list(required_preconditions)
        ):
            return None

        evaluated_at = str(source_context.get("evaluated_at") or aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        expected_local_effect_presence_source = (
            self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                aggregate_candidate,
                source_context,
            )
        )
        if not isinstance(expected_local_effect_presence_source, dict):
            return None

        aggregate_identity_ref = expected_local_effect_presence_source.get("aggregate_identity_ref")
        supporting_source_message_refs = expected_local_effect_presence_source.get(
            "supporting_source_message_refs"
        )
        supporting_candidate_refs = expected_local_effect_presence_source.get("supporting_candidate_refs")
        boundary_source_ref = expected_local_effect_presence_source.get("boundary_source_ref")
        effect_target_kind = str(expected_local_effect_presence_source.get("effect_target_kind") or "").strip()
        source_capability_boundary = str(
            expected_local_effect_presence_source.get("source_capability_boundary") or ""
        ).strip()
        source_stage = str(expected_local_effect_presence_source.get("source_stage") or "").strip()
        applied_effect_id = str(expected_local_effect_presence_source.get("applied_effect_id") or "").strip()
        present_locally_at = str(expected_local_effect_presence_source.get("present_locally_at") or "").strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
            or effect_target_kind != "applied_reviewed_memory_effect"
            or source_capability_boundary != "local_effect_presence_only"
            or source_stage != "presence_recorded_local_only"
            or not applied_effect_id
            or not present_locally_at
        ):
            return None

        supporting_review_refs = expected_local_effect_presence_source.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and any(
            not isinstance(item, dict) for item in supporting_review_refs
        ):
            return None

        if dict(aggregate_identity_ref) != dict(expected_aggregate_identity_ref):
            return None

        if list(supporting_source_message_refs) != list(expected_supporting_source_message_refs):
            return None

        if list(supporting_candidate_refs) != list(expected_supporting_candidate_refs):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if not isinstance(supporting_review_refs, list):
                return None
            if list(supporting_review_refs) != list(expected_supporting_review_refs):
                return None
        elif isinstance(supporting_review_refs, list) and supporting_review_refs:
            return None

        if dict(boundary_source_ref) != dict(expected_boundary_source_ref):
            return None

        if present_locally_at != evaluated_at:
            return None

        applied_effect_target = {
            "target_version": "first_same_session_reviewed_memory_applied_effect_target_v1",
            "target_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "effect_target_kind": effect_target_kind,
            "target_capability_boundary": "local_effect_presence_only",
            "target_stage": "effect_present_local_only",
            "applied_effect_id": applied_effect_id,
            "present_locally_at": present_locally_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            applied_effect_target["supporting_review_refs"] = list(supporting_review_refs)
        return applied_effect_target

    def _resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_rollback_contract = self._build_recurrence_aggregate_reviewed_memory_rollback_contract(
            aggregate_candidate
        )
        if expected_rollback_contract is None:
            return None
        current_rollback_contract = aggregate_candidate.get("reviewed_memory_rollback_contract")
        if not isinstance(current_rollback_contract, dict) or dict(current_rollback_contract) != expected_rollback_contract:
            return None

        expected_aggregate_identity_ref = expected_rollback_contract.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_rollback_contract.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_rollback_contract.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_rollback_contract.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        required_preconditions = source_context.get("required_preconditions")
        if (
            not isinstance(required_preconditions, list)
            or "rollback_ready_reviewed_memory_effect" not in required_preconditions
        ):
            return None

        evaluated_at = str(source_context.get("evaluated_at") or expected_rollback_contract.get("defined_at") or "").strip()
        if not evaluated_at:
            return None

        reversible_effect_handle = self._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(reversible_effect_handle, dict):
            return None

        if dict(reversible_effect_handle.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref):
            return None

        if list(reversible_effect_handle.get("supporting_source_message_refs") or []) != list(
            expected_supporting_source_message_refs
        ):
            return None

        if list(reversible_effect_handle.get("supporting_candidate_refs") or []) != list(
            expected_supporting_candidate_refs
        ):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(reversible_effect_handle.get("supporting_review_refs") or []) != list(
                expected_supporting_review_refs
            ):
                return None
        elif isinstance(reversible_effect_handle.get("supporting_review_refs"), list) and reversible_effect_handle.get(
            "supporting_review_refs"
        ):
            return None

        if dict(reversible_effect_handle.get("rollback_contract_ref") or {}) != expected_rollback_contract:
            return None

        if str(reversible_effect_handle.get("effect_target_kind") or "").strip() != "applied_reviewed_memory_effect":
            return None
        if str(reversible_effect_handle.get("effect_capability") or "").strip() != "reversible_local_only":
            return None

        handle_id = str(reversible_effect_handle.get("handle_id") or "").strip()
        if not handle_id:
            return None

        effect_stage = str(reversible_effect_handle.get("effect_stage") or "").strip()
        defined_at = str(reversible_effect_handle.get("defined_at") or "").strip() or evaluated_at
        if effect_stage != "handle_defined_not_applied" or not defined_at:
            return None

        rollback_source_ref = {
            "ref_version": "same_session_reviewed_memory_rollback_source_ref_v1",
            "ref_kind": "reviewed_memory_reversible_effect_handle",
            "ref_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(expected_aggregate_identity_ref),
            "supporting_source_message_refs": list(expected_supporting_source_message_refs),
            "supporting_candidate_refs": list(expected_supporting_candidate_refs),
            "handle_id": handle_id,
            "effect_target_kind": "applied_reviewed_memory_effect",
            "effect_capability": "reversible_local_only",
            "effect_stage": effect_stage,
            "defined_at": defined_at,
        }
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            rollback_source_ref["supporting_review_refs"] = list(expected_supporting_review_refs)

        return rollback_source_ref

    def _resolve_recurrence_aggregate_reviewed_memory_disable_source_ref(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_disable_contract = self._build_recurrence_aggregate_reviewed_memory_disable_contract(
            aggregate_candidate
        )
        if expected_disable_contract is None:
            return None
        current_disable_contract = aggregate_candidate.get("reviewed_memory_disable_contract")
        if not isinstance(current_disable_contract, dict) or dict(current_disable_contract) != expected_disable_contract:
            return None

        expected_aggregate_identity_ref = expected_disable_contract.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_disable_contract.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_disable_contract.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_disable_contract.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        required_preconditions = source_context.get("required_preconditions")
        if (
            not isinstance(required_preconditions, list)
            or "disable_ready_reviewed_memory_effect" not in required_preconditions
        ):
            return None

        evaluated_at = str(source_context.get("evaluated_at") or expected_disable_contract.get("defined_at") or "").strip()
        if not evaluated_at:
            return None

        expected_applied_effect_target = self._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_applied_effect_target, dict):
            return None

        if dict(expected_applied_effect_target.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref):
            return None

        if list(expected_applied_effect_target.get("supporting_source_message_refs") or []) != list(
            expected_supporting_source_message_refs
        ):
            return None

        if list(expected_applied_effect_target.get("supporting_candidate_refs") or []) != list(
            expected_supporting_candidate_refs
        ):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(expected_applied_effect_target.get("supporting_review_refs") or []) != list(
                expected_supporting_review_refs
            ):
                return None
        elif isinstance(expected_applied_effect_target.get("supporting_review_refs"), list) and expected_applied_effect_target.get(
            "supporting_review_refs"
        ):
            return None

        target_effect_target_kind = str(expected_applied_effect_target.get("effect_target_kind") or "").strip()
        target_capability_boundary = str(
            expected_applied_effect_target.get("target_capability_boundary") or ""
        ).strip()
        target_stage = str(expected_applied_effect_target.get("target_stage") or "").strip()
        applied_effect_id = str(expected_applied_effect_target.get("applied_effect_id") or "").strip()
        present_locally_at = str(expected_applied_effect_target.get("present_locally_at") or "").strip()
        boundary_source_ref = expected_applied_effect_target.get("boundary_source_ref")

        if (
            target_effect_target_kind != "applied_reviewed_memory_effect"
            or target_capability_boundary != "local_effect_presence_only"
            or target_stage != "effect_present_local_only"
            or not applied_effect_id
            or not present_locally_at
            or not isinstance(boundary_source_ref, dict)
        ):
            return None

        disable_source_ref = {
            "ref_version": "same_session_reviewed_memory_disable_source_ref_v1",
            "ref_kind": "reviewed_memory_disable_contract_backed_source",
            "ref_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(expected_aggregate_identity_ref),
            "supporting_source_message_refs": list(expected_supporting_source_message_refs),
            "supporting_candidate_refs": list(expected_supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "disable_contract_ref": dict(expected_disable_contract),
            "effect_target_kind": "applied_reviewed_memory_effect",
            "effect_capability": "disable_local_only",
            "effect_stage": "disable_defined_not_applied",
            "defined_at": evaluated_at,
        }
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            disable_source_ref["supporting_review_refs"] = list(expected_supporting_review_refs)

        return disable_source_ref

    def _resolve_recurrence_aggregate_reviewed_memory_conflict_source_ref(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_conflict_contract = self._build_recurrence_aggregate_reviewed_memory_conflict_contract(
            aggregate_candidate
        )
        if expected_conflict_contract is None:
            return None
        current_conflict_contract = aggregate_candidate.get("reviewed_memory_conflict_contract")
        if not isinstance(current_conflict_contract, dict) or dict(current_conflict_contract) != expected_conflict_contract:
            return None

        expected_aggregate_identity_ref = expected_conflict_contract.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_conflict_contract.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_conflict_contract.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_conflict_contract.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        required_preconditions = source_context.get("required_preconditions")
        if (
            not isinstance(required_preconditions, list)
            or "conflict_visible_reviewed_memory_scope" not in required_preconditions
        ):
            return None

        evaluated_at = str(source_context.get("evaluated_at") or expected_conflict_contract.get("defined_at") or "").strip()
        if not evaluated_at:
            return None

        expected_applied_effect_target = self._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_applied_effect_target, dict):
            return None

        if dict(expected_applied_effect_target.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref):
            return None

        if list(expected_applied_effect_target.get("supporting_source_message_refs") or []) != list(
            expected_supporting_source_message_refs
        ):
            return None

        if list(expected_applied_effect_target.get("supporting_candidate_refs") or []) != list(
            expected_supporting_candidate_refs
        ):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(expected_applied_effect_target.get("supporting_review_refs") or []) != list(
                expected_supporting_review_refs
            ):
                return None
        elif isinstance(expected_applied_effect_target.get("supporting_review_refs"), list) and expected_applied_effect_target.get(
            "supporting_review_refs"
        ):
            return None

        target_effect_target_kind = str(expected_applied_effect_target.get("effect_target_kind") or "").strip()
        target_capability_boundary = str(
            expected_applied_effect_target.get("target_capability_boundary") or ""
        ).strip()
        target_stage = str(expected_applied_effect_target.get("target_stage") or "").strip()
        applied_effect_id = str(expected_applied_effect_target.get("applied_effect_id") or "").strip()
        present_locally_at = str(expected_applied_effect_target.get("present_locally_at") or "").strip()
        boundary_source_ref = expected_applied_effect_target.get("boundary_source_ref")

        if (
            target_effect_target_kind != "applied_reviewed_memory_effect"
            or target_capability_boundary != "local_effect_presence_only"
            or target_stage != "effect_present_local_only"
            or not applied_effect_id
            or not present_locally_at
            or not isinstance(boundary_source_ref, dict)
        ):
            return None

        conflict_source_ref = {
            "ref_version": "same_session_reviewed_memory_conflict_source_ref_v1",
            "ref_kind": "reviewed_memory_conflict_contract_backed_source",
            "ref_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(expected_aggregate_identity_ref),
            "supporting_source_message_refs": list(expected_supporting_source_message_refs),
            "supporting_candidate_refs": list(expected_supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "conflict_contract_ref": dict(expected_conflict_contract),
            "effect_target_kind": "applied_reviewed_memory_effect",
            "effect_capability": "conflict_visible_local_only",
            "effect_stage": "conflict_scope_defined_not_applied",
            "defined_at": evaluated_at,
        }
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            conflict_source_ref["supporting_review_refs"] = list(expected_supporting_review_refs)

        return conflict_source_ref

    def _resolve_recurrence_aggregate_reviewed_memory_transition_audit_source_ref(
        self,
        aggregate_candidate: dict[str, Any],
        source_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict) or not isinstance(source_context, dict):
            return None

        expected_transition_audit_contract = self._build_recurrence_aggregate_reviewed_memory_transition_audit_contract(
            aggregate_candidate
        )
        if expected_transition_audit_contract is None:
            return None
        current_transition_audit_contract = aggregate_candidate.get("reviewed_memory_transition_audit_contract")
        if (
            not isinstance(current_transition_audit_contract, dict)
            or dict(current_transition_audit_contract) != expected_transition_audit_contract
        ):
            return None

        expected_aggregate_identity_ref = expected_transition_audit_contract.get("aggregate_identity_ref")
        if (
            not isinstance(expected_aggregate_identity_ref, dict)
            or dict(source_context.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref)
        ):
            return None

        expected_supporting_source_message_refs = expected_transition_audit_contract.get("supporting_source_message_refs")
        if (
            not isinstance(expected_supporting_source_message_refs, list)
            or list(source_context.get("supporting_source_message_refs") or [])
            != list(expected_supporting_source_message_refs)
        ):
            return None

        expected_supporting_candidate_refs = expected_transition_audit_contract.get("supporting_candidate_refs")
        if (
            not isinstance(expected_supporting_candidate_refs, list)
            or list(source_context.get("supporting_candidate_refs") or [])
            != list(expected_supporting_candidate_refs)
        ):
            return None

        expected_supporting_review_refs = expected_transition_audit_contract.get("supporting_review_refs")
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(source_context.get("supporting_review_refs") or []) != list(expected_supporting_review_refs):
                return None

        required_preconditions = source_context.get("required_preconditions")
        if (
            not isinstance(required_preconditions, list)
            or "operator_auditable_reviewed_memory_transition" not in required_preconditions
        ):
            return None

        evaluated_at = str(
            source_context.get("evaluated_at") or expected_transition_audit_contract.get("defined_at") or ""
        ).strip()
        if not evaluated_at:
            return None

        expected_applied_effect_target = self._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(expected_applied_effect_target, dict):
            return None

        if dict(expected_applied_effect_target.get("aggregate_identity_ref") or {}) != dict(expected_aggregate_identity_ref):
            return None

        if list(expected_applied_effect_target.get("supporting_source_message_refs") or []) != list(
            expected_supporting_source_message_refs
        ):
            return None

        if list(expected_applied_effect_target.get("supporting_candidate_refs") or []) != list(
            expected_supporting_candidate_refs
        ):
            return None

        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            if list(expected_applied_effect_target.get("supporting_review_refs") or []) != list(
                expected_supporting_review_refs
            ):
                return None
        elif isinstance(expected_applied_effect_target.get("supporting_review_refs"), list) and expected_applied_effect_target.get(
            "supporting_review_refs"
        ):
            return None

        target_effect_target_kind = str(expected_applied_effect_target.get("effect_target_kind") or "").strip()
        target_capability_boundary = str(
            expected_applied_effect_target.get("target_capability_boundary") or ""
        ).strip()
        target_stage = str(expected_applied_effect_target.get("target_stage") or "").strip()
        applied_effect_id = str(expected_applied_effect_target.get("applied_effect_id") or "").strip()
        present_locally_at = str(expected_applied_effect_target.get("present_locally_at") or "").strip()
        boundary_source_ref = expected_applied_effect_target.get("boundary_source_ref")

        if (
            target_effect_target_kind != "applied_reviewed_memory_effect"
            or target_capability_boundary != "local_effect_presence_only"
            or target_stage != "effect_present_local_only"
            or not applied_effect_id
            or not present_locally_at
            or not isinstance(boundary_source_ref, dict)
        ):
            return None

        transition_audit_source_ref = {
            "ref_version": "same_session_reviewed_memory_transition_audit_source_ref_v1",
            "ref_kind": "reviewed_memory_transition_audit_contract_backed_source",
            "ref_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(expected_aggregate_identity_ref),
            "supporting_source_message_refs": list(expected_supporting_source_message_refs),
            "supporting_candidate_refs": list(expected_supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "transition_audit_contract_ref": dict(expected_transition_audit_contract),
            "effect_target_kind": "applied_reviewed_memory_effect",
            "effect_capability": "transition_audit_local_only",
            "effect_stage": "audit_defined_not_emitted",
            "defined_at": evaluated_at,
        }
        if isinstance(expected_supporting_review_refs, list) and expected_supporting_review_refs:
            transition_audit_source_ref["supporting_review_refs"] = list(expected_supporting_review_refs)

        return transition_audit_source_ref

    def _build_recurrence_aggregate_reviewed_memory_source_context(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_transition_audit_contract = self._build_recurrence_aggregate_reviewed_memory_transition_audit_contract(
            aggregate_candidate
        )
        if expected_transition_audit_contract is None:
            return None
        current_transition_audit_contract = aggregate_candidate.get("reviewed_memory_transition_audit_contract")
        if (
            not isinstance(current_transition_audit_contract, dict)
            or dict(current_transition_audit_contract) != expected_transition_audit_contract
        ):
            return None

        expected_unblock_contract = self._build_recurrence_aggregate_reviewed_memory_unblock_contract(
            aggregate_candidate
        )
        if expected_unblock_contract is None:
            return None
        current_unblock_contract = aggregate_candidate.get("reviewed_memory_unblock_contract")
        if not isinstance(current_unblock_contract, dict) or dict(current_unblock_contract) != expected_unblock_contract:
            return None

        aggregate_identity_ref = expected_transition_audit_contract.get("aggregate_identity_ref")
        if not isinstance(aggregate_identity_ref, dict) or not aggregate_identity_ref:
            return None

        supporting_source_message_refs = expected_transition_audit_contract.get("supporting_source_message_refs")
        if not isinstance(supporting_source_message_refs, list) or not supporting_source_message_refs:
            return None

        supporting_candidate_refs = expected_transition_audit_contract.get("supporting_candidate_refs")
        if not isinstance(supporting_candidate_refs, list) or not supporting_candidate_refs:
            return None

        required_preconditions = expected_unblock_contract.get("required_preconditions")
        if not isinstance(required_preconditions, list) or not required_preconditions:
            return None

        evaluated_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        source_context = {
            "source_version": "same_session_reviewed_memory_capability_source_refs_v1",
            "source_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "required_preconditions": [str(item) for item in required_preconditions if str(item).strip()],
            "evaluated_at": evaluated_at,
        }

        supporting_review_refs = expected_transition_audit_contract.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            source_context["supporting_review_refs"] = list(supporting_review_refs)
        return source_context

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record_scope_key(
        self,
        proof_record_entry: dict[str, Any],
    ) -> str | None:
        if not isinstance(proof_record_entry, dict):
            return None

        aggregate_identity_ref = proof_record_entry.get("aggregate_identity_ref")
        supporting_source_message_refs = proof_record_entry.get("supporting_source_message_refs")
        supporting_candidate_refs = proof_record_entry.get("supporting_candidate_refs")
        boundary_source_ref = proof_record_entry.get("boundary_source_ref")
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not isinstance(boundary_source_ref, dict)
        ):
            return None

        scope_key_payload: dict[str, Any] = {
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
        }
        supporting_review_refs = proof_record_entry.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            scope_key_payload["supporting_review_refs"] = list(supporting_review_refs)
        return json.dumps(scope_key_payload, ensure_ascii=False, sort_keys=True)

    def _build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record_store_entry(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        source_context = self._build_recurrence_aggregate_reviewed_memory_source_context(aggregate_candidate)
        if source_context is None:
            return None

        boundary_source_ref = self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
            aggregate_candidate,
            source_context,
        )
        if not isinstance(boundary_source_ref, dict):
            return None

        aggregate_identity_ref = source_context.get("aggregate_identity_ref")
        supporting_source_message_refs = source_context.get("supporting_source_message_refs")
        supporting_candidate_refs = source_context.get("supporting_candidate_refs")
        present_locally_at = str(source_context.get("evaluated_at") or "").strip()
        first_seen_at = str(aggregate_candidate.get("first_seen_at") or "").strip()
        if (
            not isinstance(aggregate_identity_ref, dict)
            or not isinstance(supporting_source_message_refs, list)
            or not isinstance(supporting_candidate_refs, list)
            or not first_seen_at
            or not present_locally_at
        ):
            return None

        proof_identity_payload: dict[str, Any] = {
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "present_locally_at": present_locally_at,
        }
        supporting_review_refs = source_context.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            proof_identity_payload["supporting_review_refs"] = list(supporting_review_refs)

        applied_effect_id = (
            "reviewed-memory-effect:"
            + hashlib.sha256(
                json.dumps(proof_identity_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()[:24]
        )
        proof_record_entry = {
            "proof_record_version": "first_same_session_reviewed_memory_local_effect_presence_proof_record_v1",
            "proof_record_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_identity_ref),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "boundary_source_ref": dict(boundary_source_ref),
            "effect_target_kind": "applied_reviewed_memory_effect",
            "proof_capability_boundary": "local_effect_presence_only",
            "proof_record_stage": "canonical_presence_recorded_local_only",
            "applied_effect_id": applied_effect_id,
            "present_locally_at": present_locally_at,
        }
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            proof_record_entry["supporting_review_refs"] = list(supporting_review_refs)
        return proof_record_entry

    def _build_reviewed_memory_local_effect_presence_proof_record_store_entries(
        self,
        aggregate_candidates: list[dict[str, Any]],
        *,
        existing_entries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        derived_entries: list[dict[str, Any]] = []
        derived_scope_keys: set[str] = set()
        for aggregate_candidate in aggregate_candidates:
            if not isinstance(aggregate_candidate, dict):
                continue
            proof_record_entry = (
                self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record_store_entry(
                    aggregate_candidate
                )
            )
            if not isinstance(proof_record_entry, dict):
                continue
            scope_key = self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record_scope_key(
                proof_record_entry
            )
            if scope_key is None or scope_key in derived_scope_keys:
                continue
            derived_scope_keys.add(scope_key)
            derived_entries.append(proof_record_entry)

        merged_entries: list[dict[str, Any]] = []
        seen_scope_keys: set[str] = set()
        if isinstance(existing_entries, list):
            for raw_entry in existing_entries:
                if not isinstance(raw_entry, dict):
                    continue
                scope_key = self._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record_scope_key(
                    raw_entry
                )
                if scope_key is None or scope_key in derived_scope_keys or scope_key in seen_scope_keys:
                    continue
                seen_scope_keys.add(scope_key)
                merged_entries.append(dict(raw_entry))

        merged_entries.extend(derived_entries)
        return merged_entries

    def _build_recurrence_aggregate_reviewed_memory_capability_source_refs(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        source_context = self._build_recurrence_aggregate_reviewed_memory_source_context(aggregate_candidate)
        if source_context is None:
            return None

        capability_source_refs = {
            "boundary_source_ref": self._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
                aggregate_candidate,
                source_context,
            ),
            "rollback_source_ref": self._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                aggregate_candidate,
                source_context,
            ),
            "disable_source_ref": self._resolve_recurrence_aggregate_reviewed_memory_disable_source_ref(
                aggregate_candidate,
                source_context,
            ),
            "conflict_source_ref": self._resolve_recurrence_aggregate_reviewed_memory_conflict_source_ref(
                aggregate_candidate,
                source_context,
            ),
            "transition_audit_source_ref": self._resolve_recurrence_aggregate_reviewed_memory_transition_audit_source_ref(
                aggregate_candidate,
                source_context,
            ),
        }
        if any(value is None for value in capability_source_refs.values()):
            return None

        source_context["capability_source_refs"] = capability_source_refs
        source_context["source_status"] = "all_required_sources_present"
        return source_context

    def _build_recurrence_aggregate_reviewed_memory_capability_basis(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_capability_source_refs = self._build_recurrence_aggregate_reviewed_memory_capability_source_refs(
            aggregate_candidate
        )
        if expected_capability_source_refs is None:
            return None

        expected_unblock_contract = self._build_recurrence_aggregate_reviewed_memory_unblock_contract(
            aggregate_candidate
        )
        if expected_unblock_contract is None:
            return None
        current_unblock_contract = aggregate_candidate.get("reviewed_memory_unblock_contract")
        if not isinstance(current_unblock_contract, dict) or dict(current_unblock_contract) != expected_unblock_contract:
            return None

        required_preconditions = expected_unblock_contract.get("required_preconditions")
        if not isinstance(required_preconditions, list) or not required_preconditions:
            return None

        evaluated_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not evaluated_at:
            return None

        aggregate_key = aggregate_candidate.get("aggregate_key")
        if not isinstance(aggregate_key, dict):
            return None

        supporting_source_message_refs = aggregate_candidate.get("supporting_source_message_refs")
        if not isinstance(supporting_source_message_refs, list) or not supporting_source_message_refs:
            return None

        supporting_candidate_refs = aggregate_candidate.get("supporting_candidate_refs")
        if not isinstance(supporting_candidate_refs, list) or not supporting_candidate_refs:
            return None

        basis = {
            "basis_version": "same_session_reviewed_memory_capability_basis_v1",
            "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": dict(aggregate_key),
            "supporting_source_message_refs": list(supporting_source_message_refs),
            "supporting_candidate_refs": list(supporting_candidate_refs),
            "required_preconditions": [str(item) for item in required_preconditions if str(item).strip()],
            "basis_status": "all_required_capabilities_present",
            "satisfaction_basis_boundary": "canonical_reviewed_memory_layer_capabilities_only",
            "evaluated_at": evaluated_at,
        }

        supporting_review_refs = aggregate_candidate.get("supporting_review_refs")
        if isinstance(supporting_review_refs, list) and supporting_review_refs:
            basis["supporting_review_refs"] = list(supporting_review_refs)

        return basis

    def _build_recurrence_aggregate_reviewed_memory_transition_record(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_transition_audit_contract = self._build_recurrence_aggregate_reviewed_memory_transition_audit_contract(
            aggregate_candidate
        )
        if expected_transition_audit_contract is None:
            return None
        current_transition_audit_contract = aggregate_candidate.get("reviewed_memory_transition_audit_contract")
        if (
            not isinstance(current_transition_audit_contract, dict)
            or dict(current_transition_audit_contract) != expected_transition_audit_contract
        ):
            return None

        expected_capability_status = self._build_recurrence_aggregate_reviewed_memory_capability_status(
            aggregate_candidate
        )
        if expected_capability_status is None:
            return None
        current_capability_status = aggregate_candidate.get("reviewed_memory_capability_status")
        if (
            not isinstance(current_capability_status, dict)
            or dict(current_capability_status) != expected_capability_status
        ):
            return None

        if str(expected_capability_status.get("capability_outcome") or "").strip() != "unblocked_all_required":
            return None

        aggregate_key = aggregate_candidate.get("aggregate_key")
        if not isinstance(aggregate_key, dict):
            return None
        fingerprint = str(aggregate_key.get("normalized_delta_fingerprint") or "").strip()
        if not fingerprint:
            return None

        stored_records = aggregate_candidate.get("_reviewed_memory_emitted_transition_records")
        if not isinstance(stored_records, list):
            return None

        for record in stored_records:
            if not isinstance(record, dict):
                continue
            rec_identity = record.get("aggregate_identity_ref")
            if not isinstance(rec_identity, dict):
                continue
            if str(rec_identity.get("normalized_delta_fingerprint") or "").strip() != fingerprint:
                continue
            canonical_id = str(record.get("canonical_transition_id") or "").strip()
            operator_note = str(record.get("operator_reason_or_note") or "").strip()
            emitted_at = str(record.get("emitted_at") or "").strip()
            if not canonical_id or not operator_note or not emitted_at:
                continue
            if str(record.get("transition_action") or "").strip() != "future_reviewed_memory_apply":
                continue
            return dict(record)

        return None

    def _build_recurrence_aggregate_reviewed_memory_conflict_visibility_record(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        aggregate_key = aggregate_candidate.get("aggregate_key")
        if not isinstance(aggregate_key, dict):
            return None
        fingerprint = str(aggregate_key.get("normalized_delta_fingerprint") or "").strip()
        if not fingerprint:
            return None

        stored_records = aggregate_candidate.get("_reviewed_memory_emitted_transition_records")
        if not isinstance(stored_records, list):
            return None

        for record in stored_records:
            if not isinstance(record, dict):
                continue
            rec_identity = record.get("aggregate_identity_ref")
            if not isinstance(rec_identity, dict):
                continue
            if str(rec_identity.get("normalized_delta_fingerprint") or "").strip() != fingerprint:
                continue
            canonical_id = str(record.get("canonical_transition_id") or "").strip()
            checked_at = str(record.get("checked_at") or "").strip()
            if not canonical_id or not checked_at:
                continue
            if str(record.get("transition_action") or "").strip() != "future_reviewed_memory_conflict_visibility":
                continue
            if str(record.get("record_stage") or "").strip() != "conflict_visibility_checked":
                continue
            return dict(record)

        return None

    def _build_recurrence_aggregate_reviewed_memory_planning_target_ref(
        self,
        aggregate_candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(aggregate_candidate, dict):
            return None

        expected_precondition_status = self._build_recurrence_aggregate_reviewed_memory_precondition_status(
            aggregate_candidate
        )
        if expected_precondition_status is None:
            return None
        current_precondition_status = aggregate_candidate.get("reviewed_memory_precondition_status")
        if (
            not isinstance(current_precondition_status, dict)
            or dict(current_precondition_status) != expected_precondition_status
        ):
            return None

        expected_unblock_contract = self._build_recurrence_aggregate_reviewed_memory_unblock_contract(
            aggregate_candidate
        )
        if expected_unblock_contract is None:
            return None
        current_unblock_contract = aggregate_candidate.get("reviewed_memory_unblock_contract")
        if not isinstance(current_unblock_contract, dict) or dict(current_unblock_contract) != expected_unblock_contract:
            return None

        expected_capability_status = self._build_recurrence_aggregate_reviewed_memory_capability_status(
            aggregate_candidate
        )
        if expected_capability_status is None:
            return None
        current_capability_status = aggregate_candidate.get("reviewed_memory_capability_status")
        if not isinstance(current_capability_status, dict) or dict(current_capability_status) != expected_capability_status:
            return None

        defined_at = str(aggregate_candidate.get("last_seen_at") or "").strip()
        if not defined_at:
            return None

        return {
            "planning_target_version": "same_session_reviewed_memory_planning_target_ref_v1",
            "target_label": "eligible_for_reviewed_memory_draft_planning_only",
            "target_scope": "same_session_exact_recurrence_aggregate_only",
            "target_boundary": "reviewed_memory_draft_planning_only",
            "defined_at": defined_at,
        }

    def _build_recurrence_aggregate_candidates(
        self,
        messages: list[dict[str, Any]],
        *,
        proof_record_store_entries: list[dict[str, Any]] | None = None,
        emitted_transition_records: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        grouped_members: dict[tuple[str, str, str, str, str], dict[tuple[str, str], dict[str, Any]]] = {}

        for message in messages:
            if not isinstance(message, dict):
                continue
            if (
                str(message.get("artifact_kind") or "").strip() != "grounded_brief"
                or not isinstance(message.get("original_response_snapshot"), dict)
            ):
                continue

            anchor = self._normalize_source_message_anchor(message)
            if anchor is None:
                continue
            artifact_id, source_message_id = anchor

            recurrence_key = self._serialize_candidate_recurrence_key(message.get("candidate_recurrence_key"))
            if recurrence_key is None:
                continue

            candidate_id = str(recurrence_key.get("source_candidate_id") or "").strip()
            candidate_updated_at = str(recurrence_key.get("source_candidate_updated_at") or "").strip()
            if not candidate_id or not candidate_updated_at:
                continue

            aggregate_identity = (
                str(recurrence_key.get("candidate_family") or "").strip(),
                str(recurrence_key.get("key_scope") or "").strip(),
                str(recurrence_key.get("key_version") or "").strip(),
                str(recurrence_key.get("derivation_source") or "").strip(),
                str(recurrence_key.get("normalized_delta_fingerprint") or "").strip(),
            )
            if not all(aggregate_identity):
                continue

            group_members = grouped_members.setdefault(aggregate_identity, {})
            review_ref = self._build_recurrence_aggregate_review_ref(
                message=message,
                artifact_id=artifact_id,
                source_message_id=source_message_id,
                candidate_id=candidate_id,
                candidate_updated_at=candidate_updated_at,
            )
            member = {
                "artifact_id": artifact_id,
                "source_message_id": source_message_id,
                "candidate_id": candidate_id,
                "candidate_updated_at": candidate_updated_at,
                "review_ref": review_ref,
            }
            existing = group_members.get(anchor)
            if existing is None or (
                candidate_updated_at,
                candidate_id,
                artifact_id,
                source_message_id,
            ) > (
                str(existing.get("candidate_updated_at") or ""),
                str(existing.get("candidate_id") or ""),
                str(existing.get("artifact_id") or ""),
                str(existing.get("source_message_id") or ""),
            ):
                group_members[anchor] = member

        aggregate_candidates: list[dict[str, Any]] = []
        for aggregate_identity, group_members in grouped_members.items():
            if len(group_members) < 2:
                continue

            members = list(group_members.values())
            members.sort(
                key=lambda item: (
                    str(item.get("candidate_updated_at") or ""),
                    str(item.get("artifact_id") or ""),
                    str(item.get("source_message_id") or ""),
                    str(item.get("candidate_id") or ""),
                ),
                reverse=True,
            )

            aggregate_candidate = {
                "aggregate_key": {
                    "candidate_family": aggregate_identity[0],
                    "key_scope": aggregate_identity[1],
                    "key_version": aggregate_identity[2],
                    "derivation_source": aggregate_identity[3],
                    "normalized_delta_fingerprint": aggregate_identity[4],
                },
                "supporting_source_message_refs": [
                    {
                        "artifact_id": str(member.get("artifact_id") or ""),
                        "source_message_id": str(member.get("source_message_id") or ""),
                    }
                    for member in members
                ],
                "supporting_candidate_refs": [
                    {
                        "artifact_id": str(member.get("artifact_id") or ""),
                        "source_message_id": str(member.get("source_message_id") or ""),
                        "candidate_id": str(member.get("candidate_id") or ""),
                        "candidate_updated_at": str(member.get("candidate_updated_at") or ""),
                    }
                    for member in members
                ],
                "recurrence_count": len(members),
                "scope_boundary": "same_session_current_state_only",
                "confidence_marker": "same_session_exact_key_match",
                "first_seen_at": min(
                    str(member.get("candidate_updated_at") or "")
                    for member in members
                ),
                "last_seen_at": max(
                    str(member.get("candidate_updated_at") or "")
                    for member in members
                ),
            }
            supporting_review_refs = [
                dict(review_ref)
                for member in members
                if isinstance((review_ref := member.get("review_ref")), dict)
            ]
            if supporting_review_refs:
                aggregate_candidate["supporting_review_refs"] = supporting_review_refs
            if isinstance(proof_record_store_entries, list) and proof_record_store_entries:
                aggregate_candidate["_reviewed_memory_local_effect_presence_proof_record_store_entries"] = [
                    dict(item)
                    for item in proof_record_store_entries
                    if isinstance(item, dict)
                ]
            if isinstance(emitted_transition_records, list) and emitted_transition_records:
                aggregate_candidate["_reviewed_memory_emitted_transition_records"] = [
                    dict(item)
                    for item in emitted_transition_records
                    if isinstance(item, dict)
                ]
            aggregate_promotion_marker = self._build_recurrence_aggregate_promotion_marker(aggregate_candidate)
            if aggregate_promotion_marker is not None:
                aggregate_candidate["aggregate_promotion_marker"] = aggregate_promotion_marker
            reviewed_memory_precondition_status = (
                self._build_recurrence_aggregate_reviewed_memory_precondition_status(aggregate_candidate)
            )
            if reviewed_memory_precondition_status is not None:
                aggregate_candidate["reviewed_memory_precondition_status"] = reviewed_memory_precondition_status
            reviewed_memory_boundary_draft = (
                self._build_recurrence_aggregate_reviewed_memory_boundary_draft(aggregate_candidate)
            )
            if reviewed_memory_boundary_draft is not None:
                aggregate_candidate["reviewed_memory_boundary_draft"] = reviewed_memory_boundary_draft
            reviewed_memory_rollback_contract = (
                self._build_recurrence_aggregate_reviewed_memory_rollback_contract(aggregate_candidate)
            )
            if reviewed_memory_rollback_contract is not None:
                aggregate_candidate["reviewed_memory_rollback_contract"] = reviewed_memory_rollback_contract
            reviewed_memory_disable_contract = (
                self._build_recurrence_aggregate_reviewed_memory_disable_contract(aggregate_candidate)
            )
            if reviewed_memory_disable_contract is not None:
                aggregate_candidate["reviewed_memory_disable_contract"] = reviewed_memory_disable_contract
            reviewed_memory_conflict_contract = (
                self._build_recurrence_aggregate_reviewed_memory_conflict_contract(aggregate_candidate)
            )
            if reviewed_memory_conflict_contract is not None:
                aggregate_candidate["reviewed_memory_conflict_contract"] = reviewed_memory_conflict_contract
            reviewed_memory_transition_audit_contract = (
                self._build_recurrence_aggregate_reviewed_memory_transition_audit_contract(aggregate_candidate)
            )
            if reviewed_memory_transition_audit_contract is not None:
                aggregate_candidate["reviewed_memory_transition_audit_contract"] = (
                    reviewed_memory_transition_audit_contract
                )
            reviewed_memory_unblock_contract = (
                self._build_recurrence_aggregate_reviewed_memory_unblock_contract(aggregate_candidate)
            )
            if reviewed_memory_unblock_contract is not None:
                aggregate_candidate["reviewed_memory_unblock_contract"] = reviewed_memory_unblock_contract
            reviewed_memory_capability_basis = (
                self._build_recurrence_aggregate_reviewed_memory_capability_basis(aggregate_candidate)
            )
            if reviewed_memory_capability_basis is not None:
                aggregate_candidate["reviewed_memory_capability_basis"] = reviewed_memory_capability_basis
            reviewed_memory_capability_status = (
                self._build_recurrence_aggregate_reviewed_memory_capability_status(aggregate_candidate)
            )
            if reviewed_memory_capability_status is not None:
                aggregate_candidate["reviewed_memory_capability_status"] = reviewed_memory_capability_status
            reviewed_memory_transition_record = (
                self._build_recurrence_aggregate_reviewed_memory_transition_record(aggregate_candidate)
            )
            if reviewed_memory_transition_record is not None:
                aggregate_candidate["reviewed_memory_transition_record"] = reviewed_memory_transition_record
            reviewed_memory_conflict_visibility_record = (
                self._build_recurrence_aggregate_reviewed_memory_conflict_visibility_record(aggregate_candidate)
            )
            if reviewed_memory_conflict_visibility_record is not None:
                aggregate_candidate["reviewed_memory_conflict_visibility_record"] = (
                    reviewed_memory_conflict_visibility_record
                )
            reviewed_memory_planning_target_ref = (
                self._build_recurrence_aggregate_reviewed_memory_planning_target_ref(aggregate_candidate)
            )
            if reviewed_memory_planning_target_ref is not None:
                aggregate_candidate["reviewed_memory_planning_target_ref"] = reviewed_memory_planning_target_ref
            aggregate_candidates.append(aggregate_candidate)

        aggregate_candidates.sort(
            key=lambda item: str(
                (
                    item.get("aggregate_key") or {}
                ).get("normalized_delta_fingerprint") or ""
            ),
        )
        aggregate_candidates.sort(
            key=lambda item: str(item.get("last_seen_at") or ""),
            reverse=True,
        )
        return aggregate_candidates

    def _build_review_queue_items(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        review_queue_items: list[dict[str, Any]] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            if (
                str(message.get("artifact_kind") or "").strip() != "grounded_brief"
                or not isinstance(message.get("original_response_snapshot"), dict)
            ):
                continue

            durable_candidate = self._serialize_durable_candidate(message.get("durable_candidate"))
            if durable_candidate is None:
                continue
            if str(durable_candidate.get("promotion_eligibility") or "").strip() != "eligible_for_review":
                continue

            anchor = self._normalize_source_message_anchor(message)
            if anchor is None:
                continue
            artifact_id, source_message_id = anchor
            if (
                artifact_id not in durable_candidate.get("supporting_artifact_ids", [])
                or source_message_id not in durable_candidate.get("supporting_source_message_ids", [])
            ):
                continue
            if self._serialize_candidate_review_record(message.get("candidate_review_record")) is not None:
                continue

            review_queue_items.append(
                {
                    "candidate_id": durable_candidate["candidate_id"],
                    "candidate_family": durable_candidate["candidate_family"],
                    "statement": durable_candidate["statement"],
                    "promotion_basis": durable_candidate["promotion_basis"],
                    "promotion_eligibility": durable_candidate["promotion_eligibility"],
                    "artifact_id": artifact_id,
                    "source_message_id": source_message_id,
                    "supporting_artifact_ids": list(durable_candidate["supporting_artifact_ids"]),
                    "supporting_source_message_ids": list(durable_candidate["supporting_source_message_ids"]),
                    "supporting_signal_refs": [
                        dict(ref)
                        for ref in durable_candidate.get("supporting_signal_refs", [])
                        if isinstance(ref, dict)
                    ],
                    "supporting_confirmation_refs": [
                        dict(ref)
                        for ref in durable_candidate.get("supporting_confirmation_refs", [])
                        if isinstance(ref, dict)
                    ],
                    "created_at": durable_candidate["created_at"],
                    "updated_at": durable_candidate["updated_at"],
                }
            )

        review_queue_items.sort(
            key=lambda item: (
                str(item.get("updated_at") or ""),
                str(item.get("created_at") or ""),
                str(item.get("candidate_id") or ""),
                str(item.get("artifact_id") or ""),
                str(item.get("source_message_id") or ""),
            ),
            reverse=True,
        )
        return review_queue_items

    def _serialize_candidate_review_record(
        self,
        candidate_review_record: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(candidate_review_record, dict):
            return None

        candidate_id = str(candidate_review_record.get("candidate_id") or "").strip()
        candidate_updated_at = str(candidate_review_record.get("candidate_updated_at") or "").strip()
        artifact_id = str(candidate_review_record.get("artifact_id") or "").strip()
        source_message_id = self._serialize_source_message_id(candidate_review_record.get("source_message_id"))
        review_scope = str(candidate_review_record.get("review_scope") or "").strip()
        review_action = str(candidate_review_record.get("review_action") or "").strip()
        review_status = str(candidate_review_record.get("review_status") or "").strip()
        recorded_at = str(candidate_review_record.get("recorded_at") or "").strip()
        if (
            not candidate_id
            or not candidate_updated_at
            or not artifact_id
            or source_message_id is None
            or review_scope != "source_message_candidate_review"
            or review_action != "accept"
            or review_status != "accepted"
            or not recorded_at
        ):
            return None

        return {
            "candidate_id": candidate_id,
            "candidate_updated_at": candidate_updated_at,
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "review_scope": review_scope,
            "review_action": review_action,
            "review_status": review_status,
            "recorded_at": recorded_at,
        }

    def _serialize_candidate_confirmation_record(
        self,
        candidate_confirmation_record: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(candidate_confirmation_record, dict):
            return None

        candidate_id = str(candidate_confirmation_record.get("candidate_id") or "").strip()
        candidate_family = str(candidate_confirmation_record.get("candidate_family") or "").strip()
        candidate_updated_at = str(candidate_confirmation_record.get("candidate_updated_at") or "").strip()
        artifact_id = str(candidate_confirmation_record.get("artifact_id") or "").strip()
        source_message_id = self._serialize_source_message_id(candidate_confirmation_record.get("source_message_id"))
        confirmation_scope = str(candidate_confirmation_record.get("confirmation_scope") or "").strip()
        confirmation_label = str(candidate_confirmation_record.get("confirmation_label") or "").strip()
        recorded_at = str(candidate_confirmation_record.get("recorded_at") or "").strip()
        if (
            not candidate_id
            or candidate_family != "correction_rewrite_preference"
            or not candidate_updated_at
            or not artifact_id
            or source_message_id is None
            or confirmation_scope != "candidate_reuse"
            or confirmation_label != "explicit_reuse_confirmation"
            or not recorded_at
        ):
            return None

        return {
            "candidate_id": candidate_id,
            "candidate_family": candidate_family,
            "candidate_updated_at": candidate_updated_at,
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "confirmation_scope": confirmation_scope,
            "confirmation_label": confirmation_label,
            "recorded_at": recorded_at,
        }

    def _normalize_text_block(self, raw_value: Any) -> str | None:
        if not isinstance(raw_value, str):
            return None
        normalized = raw_value.replace("\r\n", "\n").strip()
        return normalized or None

    def _resolve_candidate_confirmation_record_for_message(
        self,
        *,
        message: dict[str, Any],
        session_local_candidate: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(session_local_candidate, dict):
            return None

        serialized = self._serialize_candidate_confirmation_record(message.get("candidate_confirmation_record"))
        if serialized is None:
            return None

        candidate_id = str(session_local_candidate.get("candidate_id") or "").strip()
        candidate_family = str(session_local_candidate.get("candidate_family") or "").strip()
        candidate_updated_at = str(session_local_candidate.get("updated_at") or "").strip()
        supporting_artifact_ids = [
            str(item).strip()
            for item in session_local_candidate.get("supporting_artifact_ids", [])
            if str(item).strip()
        ]
        supporting_source_message_ids = [
            str(item).strip()
            for item in session_local_candidate.get("supporting_source_message_ids", [])
            if str(item).strip()
        ]
        if (
            serialized.get("candidate_id") != candidate_id
            or serialized.get("candidate_family") != candidate_family
            or serialized.get("candidate_updated_at") != candidate_updated_at
            or serialized.get("artifact_id") not in supporting_artifact_ids
            or serialized.get("source_message_id") not in supporting_source_message_ids
        ):
            return None
        return serialized

    def _resolve_candidate_review_record_for_message(
        self,
        *,
        message: dict[str, Any],
        durable_candidate: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(durable_candidate, dict):
            return None

        serialized = self._serialize_candidate_review_record(message.get("candidate_review_record"))
        if serialized is None:
            return None

        anchor = self._normalize_source_message_anchor(message)
        if anchor is None:
            return None
        artifact_id, source_message_id = anchor
        candidate_id = str(durable_candidate.get("candidate_id") or "").strip()
        candidate_updated_at = ""
        for raw_ref in durable_candidate.get("supporting_confirmation_refs", []):
            if not isinstance(raw_ref, dict):
                continue
            if (
                str(raw_ref.get("artifact_id") or "").strip() != artifact_id
                or self._serialize_source_message_id(raw_ref.get("source_message_id")) != source_message_id
                or str(raw_ref.get("candidate_id") or "").strip() != candidate_id
            ):
                continue
            candidate_updated_at = str(raw_ref.get("candidate_updated_at") or "").strip()
            if candidate_updated_at:
                break

        if (
            serialized.get("artifact_id") != artifact_id
            or serialized.get("source_message_id") != source_message_id
            or serialized.get("candidate_id") != candidate_id
            or not candidate_updated_at
            or serialized.get("candidate_updated_at") != candidate_updated_at
            or artifact_id not in durable_candidate.get("supporting_artifact_ids", [])
            or source_message_id not in durable_candidate.get("supporting_source_message_ids", [])
        ):
            return None
        return serialized

    def _build_durable_candidate_for_message(
        self,
        *,
        session_local_candidate: dict[str, Any] | None,
        candidate_confirmation_record: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(session_local_candidate, dict) or not isinstance(candidate_confirmation_record, dict):
            return None

        candidate_id = str(session_local_candidate.get("candidate_id") or "").strip()
        candidate_family = str(session_local_candidate.get("candidate_family") or "").strip()
        candidate_updated_at = str(session_local_candidate.get("updated_at") or "").strip()
        artifact_ids = [
            str(item).strip()
            for item in session_local_candidate.get("supporting_artifact_ids", [])
            if str(item).strip()
        ]
        source_message_ids = [
            str(item).strip()
            for item in session_local_candidate.get("supporting_source_message_ids", [])
            if str(item).strip()
        ]
        confirmation_artifact_id = str(candidate_confirmation_record.get("artifact_id") or "").strip()
        confirmation_source_message_id = self._serialize_source_message_id(
            candidate_confirmation_record.get("source_message_id")
        )
        confirmation_recorded_at = str(candidate_confirmation_record.get("recorded_at") or "").strip()
        if (
            not candidate_id
            or candidate_family != "correction_rewrite_preference"
            or not candidate_updated_at
            or candidate_confirmation_record.get("candidate_id") != candidate_id
            or candidate_confirmation_record.get("candidate_family") != candidate_family
            or candidate_confirmation_record.get("candidate_updated_at") != candidate_updated_at
            or not confirmation_artifact_id
            or confirmation_source_message_id is None
            or confirmation_artifact_id not in artifact_ids
            or confirmation_source_message_id not in source_message_ids
            or not confirmation_recorded_at
        ):
            return None

        return {
            "candidate_id": candidate_id,
            "candidate_scope": "durable_candidate",
            "candidate_family": candidate_family,
            "statement": session_local_candidate.get("statement"),
            "supporting_artifact_ids": list(artifact_ids),
            "supporting_source_message_ids": list(source_message_ids),
            "supporting_signal_refs": [
                dict(ref)
                for ref in session_local_candidate.get("supporting_signal_refs", [])
                if isinstance(ref, dict)
            ],
            "supporting_confirmation_refs": [
                {
                    "artifact_id": confirmation_artifact_id,
                    "source_message_id": confirmation_source_message_id,
                    "candidate_id": candidate_id,
                    "candidate_updated_at": candidate_updated_at,
                    "confirmation_label": candidate_confirmation_record.get("confirmation_label"),
                    "recorded_at": confirmation_recorded_at,
                }
            ],
            "evidence_strength": session_local_candidate.get("evidence_strength"),
            "has_explicit_confirmation": True,
            "promotion_basis": "explicit_confirmation",
            "promotion_eligibility": "eligible_for_review",
            "created_at": confirmation_recorded_at,
            "updated_at": confirmation_recorded_at,
        }

    def _build_session_local_candidate_for_message(
        self,
        *,
        message: dict[str, Any],
        session_local_memory_signal: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(session_local_memory_signal, dict):
            return None

        anchor = self._normalize_source_message_anchor(message)
        if anchor is None:
            return None
        artifact_id, source_message_id = anchor

        content_signal = session_local_memory_signal.get("content_signal")
        if not isinstance(content_signal, dict):
            return None
        latest_corrected_outcome = content_signal.get("latest_corrected_outcome")
        if not isinstance(latest_corrected_outcome, dict):
            return None
        if str(latest_corrected_outcome.get("outcome") or "").strip() != "corrected":
            return None
        if not bool(content_signal.get("has_corrected_text")):
            return None

        original_response_snapshot = message.get("original_response_snapshot")
        if not isinstance(original_response_snapshot, dict):
            return None
        original_draft_text = self._normalize_text_block(original_response_snapshot.get("draft_text"))
        corrected_text = self._normalize_text_block(message.get("corrected_text"))
        if original_draft_text is None or corrected_text is None or original_draft_text == corrected_text:
            return None

        recorded_at = str(latest_corrected_outcome.get("recorded_at") or "").strip()
        if not recorded_at:
            return None

        supporting_signal_refs = [
            {
                "signal_name": "session_local_memory_signal.content_signal",
                "relationship": "primary_basis",
            }
        ]
        evidence_strength = "explicit_single_artifact"

        save_signal = session_local_memory_signal.get("save_signal")
        if isinstance(save_signal, dict):
            latest_approval_id = self._normalize_optional_text(save_signal.get("latest_approval_id"))
            if latest_approval_id is not None:
                supporting_signal_refs.append(
                    {
                        "signal_name": "session_local_memory_signal.save_signal",
                        "relationship": "supporting_evidence",
                    }
                )

        return {
            "candidate_id": (
                f"session-local-candidate:{artifact_id}:{source_message_id}:correction_rewrite_preference"
            ),
            "candidate_scope": "session_local",
            "candidate_family": "correction_rewrite_preference",
            "statement": "explicit rewrite correction recorded for this grounded brief",
            "supporting_artifact_ids": [artifact_id],
            "supporting_source_message_ids": [source_message_id],
            "supporting_signal_refs": supporting_signal_refs,
            "evidence_strength": evidence_strength,
            "status": "session_local_candidate",
            "created_at": recorded_at,
            "updated_at": recorded_at,
        }

    def _build_candidate_recurrence_key_for_message(
        self,
        *,
        message: dict[str, Any],
        session_local_candidate: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(session_local_candidate, dict):
            return None

        anchor = self._normalize_source_message_anchor(message)
        if anchor is None:
            return None
        artifact_id, source_message_id = anchor

        candidate_id = str(session_local_candidate.get("candidate_id") or "").strip()
        candidate_family = str(session_local_candidate.get("candidate_family") or "").strip()
        candidate_updated_at = str(session_local_candidate.get("updated_at") or "").strip()
        supporting_artifact_ids = [
            str(item).strip()
            for item in session_local_candidate.get("supporting_artifact_ids", [])
            if str(item).strip()
        ]
        supporting_source_message_ids = [
            str(item).strip()
            for item in session_local_candidate.get("supporting_source_message_ids", [])
            if str(item).strip()
        ]
        if (
            not candidate_id
            or candidate_family != "correction_rewrite_preference"
            or not candidate_updated_at
            or artifact_id not in supporting_artifact_ids
            or source_message_id not in supporting_source_message_ids
        ):
            return None

        corrected_outcome = self._serialize_corrected_outcome(message.get("corrected_outcome"))
        if (
            not isinstance(corrected_outcome, dict)
            or str(corrected_outcome.get("outcome") or "").strip() != "corrected"
            or str(corrected_outcome.get("artifact_id") or "").strip() != artifact_id
            or str(corrected_outcome.get("source_message_id") or "").strip() != source_message_id
            or str(corrected_outcome.get("recorded_at") or "").strip() != candidate_updated_at
        ):
            return None

        original_response_snapshot = message.get("original_response_snapshot")
        if not isinstance(original_response_snapshot, dict):
            return None

        original_draft_text = self._normalize_text_block(original_response_snapshot.get("draft_text"))
        corrected_text = self._normalize_text_block(message.get("corrected_text"))
        if original_draft_text is None or corrected_text is None or original_draft_text == corrected_text:
            return None

        normalized_delta_fingerprint, rewrite_dimensions = self._derive_normalized_rewrite_delta(
            original_text=original_draft_text,
            corrected_text=corrected_text,
        )
        if normalized_delta_fingerprint is None:
            return None

        recurrence_key = {
            "candidate_family": candidate_family,
            "key_scope": "correction_rewrite_recurrence",
            "key_version": "explicit_pair_rewrite_delta_v1",
            "derivation_source": "explicit_corrected_pair",
            "source_candidate_id": candidate_id,
            "source_candidate_updated_at": candidate_updated_at,
            "normalized_delta_fingerprint": normalized_delta_fingerprint,
            "stability": "deterministic_local",
            "derived_at": candidate_updated_at,
        }
        if rewrite_dimensions is not None:
            recurrence_key["rewrite_dimensions"] = rewrite_dimensions
        return recurrence_key

    def _normalize_source_message_anchor(self, message: dict[str, Any]) -> tuple[str, str] | None:
        artifact_id = self._normalize_optional_text(message.get("artifact_id"))
        source_message_id = self._serialize_source_message_id(message.get("source_message_id"))
        if source_message_id is None:
            source_message_id = self._serialize_source_message_id(message.get("message_id"))
        if artifact_id is None or source_message_id is None:
            return None
        return artifact_id, source_message_id

    def _normalize_superseded_reject_anchor_from_detail(
        self,
        detail: dict[str, Any],
    ) -> tuple[str, str] | None:
        artifact_id = self._normalize_optional_text(detail.get("artifact_id"))
        source_message_id = self._serialize_source_message_id(detail.get("source_message_id"))
        if source_message_id is None:
            source_message_id = self._serialize_source_message_id(detail.get("message_id"))
        content_reason_record = detail.get("content_reason_record")
        if isinstance(content_reason_record, dict):
            if artifact_id is None:
                artifact_id = self._normalize_optional_text(content_reason_record.get("artifact_id"))
            if source_message_id is None:
                source_message_id = self._serialize_source_message_id(content_reason_record.get("source_message_id"))
        if artifact_id is None or source_message_id is None:
            return None
        return artifact_id, source_message_id

    def _normalize_historical_save_anchor_from_detail(
        self,
        detail: dict[str, Any],
    ) -> tuple[str, str] | None:
        artifact_id = self._normalize_optional_text(detail.get("artifact_id"))
        source_message_id = self._serialize_source_message_id(detail.get("source_message_id"))
        if source_message_id is None:
            source_message_id = self._serialize_source_message_id(detail.get("message_id"))
        if artifact_id is None or source_message_id is None:
            return None
        return artifact_id, source_message_id

    def _normalize_superseded_reject_reason_record(
        self,
        content_reason_record: Any,
        *,
        artifact_id: str,
        source_message_id: str,
    ) -> dict[str, Any] | None:
        serialized = self._serialize_content_reason_record(content_reason_record)
        if serialized is None:
            return None
        if serialized.get("reason_scope") != "content_reject":
            return None
        if serialized.get("reason_label") != "explicit_content_rejection":
            return None

        record_artifact_id = str(serialized.get("artifact_id") or "").strip()
        record_source_message_id = self._serialize_source_message_id(serialized.get("source_message_id"))
        if record_artifact_id and record_artifact_id != artifact_id:
            return None
        if record_source_message_id is not None and record_source_message_id != source_message_id:
            return None

        serialized["artifact_id"] = artifact_id
        serialized["artifact_kind"] = str(serialized.get("artifact_kind") or "").strip() or "grounded_brief"
        serialized["source_message_id"] = source_message_id
        if not str(serialized.get("recorded_at") or "").strip():
            return None
        return serialized

    def _iter_task_log_records(self, *, session_id: str) -> list[dict[str, Any]]:
        normalized_session_id = self._normalize_optional_text(session_id)
        if normalized_session_id is None or not self.task_logger.path.exists():
            return []

        records: list[dict[str, Any]] = []
        with self.task_logger.path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    loaded = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(loaded, dict):
                    continue
                if self._normalize_optional_text(loaded.get("session_id")) != normalized_session_id:
                    continue
                records.append(loaded)
        return records

    def _build_superseded_reject_signal_index(
        self,
        session: dict[str, Any],
    ) -> dict[tuple[str, str], dict[str, Any]]:
        session_id = self._normalize_optional_text(session.get("session_id"))
        if session_id is None:
            return {}

        candidates: dict[tuple[str, str], dict[str, Any]] = {}
        for record in self._iter_task_log_records(session_id=session_id):
            action = str(record.get("action") or "").strip()
            detail = record.get("detail")
            if not isinstance(detail, dict):
                continue
            anchor = self._normalize_superseded_reject_anchor_from_detail(detail)
            if anchor is None:
                continue
            artifact_id, source_message_id = anchor

            if action == "content_verdict_recorded":
                if str(detail.get("content_verdict") or "").strip() != "rejected":
                    continue
                content_reason_record = self._normalize_superseded_reject_reason_record(
                    detail.get("content_reason_record"),
                    artifact_id=artifact_id,
                    source_message_id=source_message_id,
                )
                recorded_at = (
                    str(content_reason_record.get("recorded_at") or "").strip()
                    if content_reason_record is not None
                    else ""
                ) or str(record.get("ts") or "").strip()
                if not recorded_at:
                    continue
                candidate: dict[str, Any] = {
                    "artifact_id": artifact_id,
                    "source_message_id": source_message_id,
                    "replay_source": "task_log_audit",
                    "corrected_outcome": {
                        "outcome": "rejected",
                        "recorded_at": recorded_at,
                    },
                }
                if content_reason_record is not None:
                    candidate["content_reason_record"] = content_reason_record
                candidates[anchor] = candidate
                continue

            if action != "content_reason_note_recorded":
                continue

            candidate = candidates.get(anchor)
            if not isinstance(candidate, dict):
                continue
            content_reason_record = self._normalize_superseded_reject_reason_record(
                detail.get("content_reason_record"),
                artifact_id=artifact_id,
                source_message_id=source_message_id,
            )
            if content_reason_record is None:
                continue
            reason_note = content_reason_record.get("reason_note")
            if not isinstance(reason_note, str) or not reason_note.strip():
                continue

            baseline_reason_record = candidate.get("content_reason_record")
            if isinstance(baseline_reason_record, dict):
                merged_reason_record = dict(baseline_reason_record)
                merged_reason_record["reason_note"] = reason_note
                merged_reason_record["recorded_at"] = (
                    str(content_reason_record.get("recorded_at") or "").strip()
                    or str(merged_reason_record.get("recorded_at") or "").strip()
                )
                candidate["content_reason_record"] = merged_reason_record
            else:
                candidate["content_reason_record"] = content_reason_record

        return candidates

    def _build_historical_save_identity_signal_index(
        self,
        session: dict[str, Any],
    ) -> dict[tuple[str, str], dict[str, Any]]:
        session_id = self._normalize_optional_text(session.get("session_id"))
        if session_id is None:
            return {}

        candidates: dict[tuple[str, str], tuple[str, int, dict[str, Any]]] = {}
        for index, record in enumerate(self._iter_task_log_records(session_id=session_id)):
            if str(record.get("action") or "").strip() != "write_note":
                continue
            detail = record.get("detail")
            if not isinstance(detail, dict):
                continue
            anchor = self._normalize_historical_save_anchor_from_detail(detail)
            if anchor is None:
                continue
            approval_id = self._normalize_optional_text(detail.get("approval_id"))
            if approval_id is None:
                continue
            recorded_at = self._normalize_optional_text(record.get("ts"))
            if recorded_at is None:
                continue
            save_content_source = self._serialize_save_content_source(detail.get("save_content_source"))
            saved_note_path = self._normalize_optional_text(detail.get("note_path"))
            candidate: dict[str, Any] = {
                "artifact_id": anchor[0],
                "source_message_id": anchor[1],
                "replay_source": "task_log_audit",
                "approval_id": approval_id,
                "recorded_at": recorded_at,
            }
            if save_content_source is not None:
                candidate["save_content_source"] = save_content_source
            if saved_note_path is not None:
                candidate["saved_note_path"] = saved_note_path

            previous = candidates.get(anchor)
            if previous is None or (recorded_at, index) >= (previous[0], previous[1]):
                candidates[anchor] = (recorded_at, index, candidate)

        return {
            anchor: dict(candidate)
            for anchor, (_, _, candidate) in candidates.items()
        }

    def _resolve_superseded_reject_signal_for_message(
        self,
        *,
        message: dict[str, Any],
        session_local_memory_signal: dict[str, Any] | None,
        superseded_reject_index: dict[tuple[str, str], dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not isinstance(session_local_memory_signal, dict):
            return None

        content_signal = session_local_memory_signal.get("content_signal")
        if not isinstance(content_signal, dict):
            return None
        latest_corrected_outcome = content_signal.get("latest_corrected_outcome")
        if isinstance(latest_corrected_outcome, dict):
            if str(latest_corrected_outcome.get("outcome") or "").strip() == "rejected":
                return None

        anchor = self._normalize_source_message_anchor(message)
        if anchor is None:
            return None
        candidate = superseded_reject_index.get(anchor)
        if not isinstance(candidate, dict):
            return None
        return dict(candidate)

    def _resolve_historical_save_identity_signal_for_message(
        self,
        *,
        message: dict[str, Any],
        session_local_memory_signal: dict[str, Any] | None,
        historical_save_identity_index: dict[tuple[str, str], dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not isinstance(session_local_memory_signal, dict):
            return None

        save_signal = session_local_memory_signal.get("save_signal")
        if not isinstance(save_signal, dict):
            return None
        if self._normalize_optional_text(save_signal.get("latest_approval_id")) is not None:
            return None

        current_save_content_source = self._serialize_save_content_source(save_signal.get("latest_save_content_source"))
        current_saved_note_path = self._normalize_optional_text(save_signal.get("latest_saved_note_path"))
        if current_save_content_source is None and current_saved_note_path is None:
            return None

        anchor = self._normalize_source_message_anchor(message)
        if anchor is None:
            return None
        candidate = historical_save_identity_index.get(anchor)
        if not isinstance(candidate, dict):
            return None

        candidate_approval_id = self._normalize_optional_text(candidate.get("approval_id"))
        if candidate_approval_id is None:
            return None
        candidate_save_content_source = self._serialize_save_content_source(candidate.get("save_content_source"))
        candidate_saved_note_path = self._normalize_optional_text(candidate.get("saved_note_path"))

        if current_save_content_source is not None and candidate_save_content_source != current_save_content_source:
            return None
        if current_saved_note_path is not None and candidate_saved_note_path != current_saved_note_path:
            return None

        return dict(candidate)

    def _synchronize_original_response_snapshot(self, response: AgentResponse) -> dict[str, Any] | None:
        if (
            response.original_response_snapshot is None
            and (
                response.artifact_kind != "grounded_brief"
                or not response.artifact_id
                or (not response.evidence and not response.summary_chunks)
            )
        ):
            return None

        snapshot = {
            "artifact_id": response.artifact_id,
            "artifact_kind": response.artifact_kind,
            "draft_text": response.text,
            "source_paths": [str(path) for path in response.selected_source_paths if str(path).strip()],
            "response_origin": dict(response.response_origin) if isinstance(response.response_origin, dict) else None,
            "summary_chunks_snapshot": [dict(item) for item in response.summary_chunks if isinstance(item, dict)],
            "evidence_snapshot": [dict(item) for item in response.evidence if isinstance(item, dict)],
        }
        response.original_response_snapshot = snapshot
        return snapshot

    def _serialize_evidence(self, evidence: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for item in evidence or []:
            if not isinstance(item, dict):
                continue
            snippet = str(item.get("snippet") or "").strip()
            if not snippet:
                continue
            source_path = str(item.get("source_path") or "")
            serialized.append(
                {
                    "label": str(item.get("label") or "문서 근거"),
                    "source_name": str(item.get("source_name") or Path(source_path).name or "(출처 없음)"),
                    "source_path": source_path,
                    "snippet": snippet,
                    "source_role": str(item.get("source_role") or "").strip(),
                }
            )
        return serialized

    def _serialize_summary_chunks(self, summary_chunks: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for item in summary_chunks or []:
            if not isinstance(item, dict):
                continue
            selected_line = str(item.get("selected_line") or "").strip()
            if not selected_line:
                continue
            source_path = str(item.get("source_path") or "")
            serialized.append(
                {
                    "chunk_id": str(item.get("chunk_id") or ""),
                    "chunk_index": int(item.get("chunk_index") or 0),
                    "total_chunks": int(item.get("total_chunks") or 0),
                    "source_path": source_path,
                    "source_name": str(item.get("source_name") or Path(source_path).name or "(출처 없음)"),
                    "selected_line": selected_line,
                }
            )
        return serialized

    def _serialize_claim_coverage(self, claim_coverage: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for item in claim_coverage or []:
            if not isinstance(item, dict):
                continue
            slot = str(item.get("slot") or "").strip()
            status = str(item.get("status") or "").strip()
            if not slot or not status:
                continue
            serialized.append(
                {
                    "slot": slot,
                    "status": status,
                    "status_label": str(item.get("status_label") or "").strip(),
                    "previous_status": str(item.get("previous_status") or "").strip(),
                    "previous_status_label": str(item.get("previous_status_label") or "").strip(),
                    "progress_state": str(item.get("progress_state") or "").strip(),
                    "progress_label": str(item.get("progress_label") or "").strip(),
                    "is_focus_slot": bool(item.get("is_focus_slot")),
                    "support_count": int(item.get("support_count") or 0),
                    "candidate_count": int(item.get("candidate_count") or 0),
                    "value": str(item.get("value") or "").strip(),
                    "source_role": str(item.get("source_role") or "").strip(),
                    "rendered_as": str(item.get("rendered_as") or "").strip(),
                }
            )
        return serialized

    def _serialize_permissions(self, permissions: Any) -> dict[str, str]:
        web_search_permission = "disabled"
        if isinstance(permissions, dict):
            web_search_permission = self._normalize_web_search_permission(permissions.get("web_search"))
        return {
            "web_search": web_search_permission,
            "web_search_label": self._web_search_permission_label(web_search_permission),
        }

    def _normalize_session_id(self, raw_value: Any) -> str:
        session_id = self._normalize_optional_text(raw_value) or DEFAULT_SESSION_ID
        session_id = session_id.replace("/", "-").replace("\\", "-").strip()
        return session_id or DEFAULT_SESSION_ID

    def _normalize_optional_text(self, raw_value: Any) -> str | None:
        if not isinstance(raw_value, str):
            return None
        normalized = raw_value.strip()
        return normalized or None

    def _normalize_feedback_label(self, raw_value: Any) -> str | None:
        normalized = self._normalize_optional_text(raw_value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered not in {"helpful", "unclear", "incorrect"}:
            return None
        return lowered

    def _normalize_feedback_reason(self, raw_value: Any) -> str | None:
        normalized = self._normalize_optional_text(raw_value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered not in {"factual_error", "irrelevant_result", "context_miss", "awkward_tone"}:
            return None
        return lowered

    def _normalize_content_verdict(self, raw_value: Any) -> str | None:
        normalized = self._normalize_optional_text(raw_value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered == "rejected":
            return lowered
        return None

    def _normalize_web_search_permission(self, raw_value: Any) -> str:
        if not isinstance(raw_value, str):
            return "disabled"
        normalized = raw_value.strip().lower()
        if normalized in {"disabled", "approval", "enabled"}:
            return normalized
        return "disabled"

    def _web_search_permission_label(self, permission: Any) -> str:
        normalized = self._normalize_web_search_permission(permission)
        if normalized == "approval":
            return "승인 필요 · 읽기 전용 검색"
        if normalized == "enabled":
            return "허용 · 읽기 전용 검색"
        return "차단 · 읽기 전용 검색"

    def _coerce_bool(self, raw_value: Any) -> bool:
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, str):
            return raw_value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(raw_value)

    def _parse_selected_paths(self, raw_value: Any) -> list[str] | None:
        if raw_value is None:
            return None
        if isinstance(raw_value, str):
            values = raw_value.replace("\r", "\n").split("\n")
        elif isinstance(raw_value, list):
            values = []
            for item in raw_value:
                if isinstance(item, str):
                    values.extend(item.split("\n"))
        else:
            raise WebApiError(400, "선택 경로는 문자열 또는 문자열 목록이어야 합니다.")

        parsed: list[str] = []
        for value in values:
            for part in value.split(","):
                normalized = part.strip()
                if normalized:
                    parsed.append(normalized)
        return parsed or None

    def _parse_positive_int(self, raw_value: Any, *, default: int) -> int:
        if raw_value in (None, ""):
            return default
        if isinstance(raw_value, int):
            parsed = raw_value
        elif isinstance(raw_value, str) and raw_value.strip().isdigit():
            parsed = int(raw_value.strip())
        else:
            raise WebApiError(400, "검색 개수 제한은 1 이상의 정수여야 합니다.")

        if parsed <= 0:
            raise WebApiError(400, "검색 개수 제한은 1 이상의 정수여야 합니다.")
        return parsed


class LocalOnlyHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], service: WebAppService) -> None:
        super().__init__(server_address, LocalAssistantHandler)
        self.service = service


class LocalAssistantHandler(BaseHTTPRequestHandler):
    server: LocalOnlyHTTPServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(HTTPStatus.OK, self.server.service.render_index())
            return
        if parsed.path == "/api/config":
            self._send_json(HTTPStatus.OK, self.server.service.get_config())
            return
        if parsed.path == "/api/sessions":
            self._send_json(HTTPStatus.OK, self.server.service.list_sessions_payload())
            return
        if parsed.path == "/api/session":
            session_id = parse_qs(parsed.query).get("session_id", [DEFAULT_SESSION_ID])[0]
            self._send_json(HTTPStatus.OK, self.server.service.get_session_payload(session_id))
            return
        if parsed.path == "/healthz":
            self._send_json(HTTPStatus.OK, {"ok": True})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {
            "/api/chat",
            "/api/chat/stream",
            "/api/chat/cancel",
            "/api/feedback",
            "/api/correction",
            "/api/candidate-confirmation",
            "/api/candidate-review",
            "/api/aggregate-transition",
            "/api/aggregate-transition-apply",
            "/api/aggregate-transition-result",
            "/api/aggregate-transition-stop",
            "/api/aggregate-transition-reverse",
            "/api/aggregate-transition-conflict-check",
            "/api/content-verdict",
            "/api/content-reason-note",
        }:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})
            return

        try:
            self._validate_same_origin()
            payload = self._read_json_body()
            if parsed.path == "/api/feedback":
                response = self.server.service.submit_feedback(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/correction":
                response = self.server.service.submit_correction(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/candidate-confirmation":
                response = self.server.service.submit_candidate_confirmation(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/candidate-review":
                response = self.server.service.submit_candidate_review(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition":
                response = self.server.service.emit_aggregate_transition(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-apply":
                response = self.server.service.apply_aggregate_transition(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-result":
                response = self.server.service.confirm_aggregate_transition_result(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-stop":
                response = self.server.service.stop_apply_aggregate_transition(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-reverse":
                response = self.server.service.reverse_aggregate_transition(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-conflict-check":
                response = self.server.service.check_aggregate_conflict_visibility(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/content-verdict":
                response = self.server.service.submit_content_verdict(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/content-reason-note":
                response = self.server.service.submit_content_reason_note(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/chat/cancel":
                response = self.server.service.cancel_stream(
                    session_id=payload.get("session_id"),
                    request_id=payload.get("request_id"),
                )
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/chat/stream":
                self._send_json_stream(self.server.service.stream_chat(payload))
                return
            response = self.server.service.handle_chat(payload)
            self._send_json(HTTPStatus.OK, response)
        except WebApiError as exc:
            self._send_json(exc.status_code, {"ok": False, "error": {"message": localize_text(exc.message)}})
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": {"message": "JSON 요청 본문 형식이 올바르지 않습니다."}})
        except ModelAdapterError as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": {"message": localize_text(str(exc))}})
        except Exception as exc:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": {"message": localize_text(str(exc))}})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _validate_same_origin(self) -> None:
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        referer = self.headers.get("Referer")

        if origin:
            if urlparse(origin).netloc != host:
                raise WebApiError(HTTPStatus.FORBIDDEN, "로컬 웹 셸에서는 다른 origin의 요청을 허용하지 않습니다.")
            return

        if referer and urlparse(referer).netloc != host:
            raise WebApiError(HTTPStatus.FORBIDDEN, "로컬 웹 셸에서는 다른 origin의 요청을 허용하지 않습니다.")

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise WebApiError(HTTPStatus.BAD_REQUEST, "요청 본문이 필요합니다.")

        body = self.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise WebApiError(HTTPStatus.BAD_REQUEST, "JSON 본문은 객체 형태여야 합니다.")
        return payload

    def _send_html(self, status: HTTPStatus, body: str) -> None:
        encoded = body.encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_json(self, status: int | HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_json_stream(self, events) -> None:
        try:
            self.send_response(int(HTTPStatus.OK))
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            for event in events:
                encoded = (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")
                self.wfile.write(encoded)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return


def build_parser() -> Any:
    import argparse

    parser = argparse.ArgumentParser(description="로컬 AI 비서 웹 셸을 실행합니다.")
    parser.add_argument("--host", default=None, help="바인드할 호스트입니다. 기본값은 LOCAL_AI_WEB_HOST 또는 127.0.0.1입니다.")
    parser.add_argument("--port", type=int, default=None, help="바인드할 포트입니다. 기본값은 LOCAL_AI_WEB_PORT 또는 8765입니다.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    settings = AppSettings.from_env()
    host = args.host or settings.web_host
    port = args.port or settings.web_port

    service = WebAppService(settings=settings)
    server = LocalOnlyHTTPServer((host, port), service)
    print(f"로컬 웹 셸이 http://{host}:{port} 에서 실행 중입니다.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n로컬 웹 셸을 종료합니다.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
