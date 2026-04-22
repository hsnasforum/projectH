from __future__ import annotations

from typing import Any

from app.errors import WebApiError
from core.contracts import ContentReasonScope, ContentVerdict


class FeedbackHandlerMixin:
    """Feedback/correction methods extracted from WebAppService."""

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
                    "reason_label": corrected_outcome.get("reason_label"),
                    "recorded_at": corrected_outcome.get("recorded_at"),
                    "artifact_id": corrected_outcome.get("artifact_id"),
                    "source_message_id": corrected_outcome.get("source_message_id"),
                    "approval_id": corrected_outcome.get("approval_id"),
                    "saved_note_path": corrected_outcome.get("saved_note_path"),
                    "corrected_text_length": len(serialized_corrected_text or ""),
                },
            )

        artifact_id = str(updated_message.get("artifact_id") or "").strip()
        if artifact_id and self.artifact_store.get(artifact_id):
            try:
                self.artifact_store.append_correction(
                    artifact_id,
                    corrected_text=serialized_corrected_text or "",
                    outcome="corrected",
                )
            except Exception:
                pass

        # Record correction pattern in correction store
        original_snapshot = updated_message.get("original_response_snapshot")
        if (
            artifact_id
            and isinstance(original_snapshot, dict)
            and serialized_corrected_text
        ):
            original_draft = str(original_snapshot.get("draft_text") or "").strip()
            if original_draft and original_draft != serialized_corrected_text:
                try:
                    self.correction_store.record_correction(
                        artifact_id=artifact_id,
                        session_id=session_id,
                        source_message_id=(
                            corrected_outcome.get("source_message_id")
                            if corrected_outcome else message_id
                        ),
                        original_text=original_draft,
                        corrected_text=serialized_corrected_text,
                    )
                except Exception:
                    pass

        # Auto-promote to preference candidate if cross-session recurrence detected
        if artifact_id:
            try:
                corrections = self.correction_store.find_by_artifact(artifact_id)
                for c in corrections:
                    fp = c.get("delta_fingerprint")
                    if fp:
                        self.preference_store.promote_from_corrections(fp, self.correction_store)
            except Exception:
                pass

        return {
            "ok": True,
            "message_id": message_id,
            "artifact_id": artifact_id or None,
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
        if content_verdict != ContentVerdict.REJECTED:
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
                    "reason_label": corrected_outcome.get("reason_label"),
                    "recorded_at": corrected_outcome.get("recorded_at"),
                    "artifact_id": corrected_outcome.get("artifact_id"),
                    "source_message_id": corrected_outcome.get("source_message_id"),
                    "approval_id": corrected_outcome.get("approval_id"),
                    "saved_note_path": corrected_outcome.get("saved_note_path"),
                    "content_reason_record": content_reason_record,
                },
            )

        artifact_id = str(updated_message.get("artifact_id") or "").strip()
        if artifact_id and self.artifact_store.get(artifact_id):
            try:
                self.artifact_store.record_outcome(
                    artifact_id,
                    outcome="rejected",
                    content_verdict="rejected",
                )
            except Exception:
                pass

        return {
            "ok": True,
            "message_id": message_id,
            "artifact_id": artifact_id or None,
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
                "reason_scope": content_reason_record.get("reason_scope") if content_reason_record else ContentReasonScope.CONTENT_REJECT,
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

    def submit_content_reason_label(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        message_id = self._normalize_optional_text(payload.get("message_id"))
        reason_label = self._normalize_optional_text(payload.get("reason_label"))

        if not message_id:
            raise WebApiError(400, "레이블을 기록할 메시지 ID가 필요합니다.")
        if not reason_label:
            raise WebApiError(400, "reason_label을 입력해 주세요.")

        try:
            updated_message = self.session_store.record_content_reason_label_for_message(
                session_id,
                message_id=message_id,
                reason_label=reason_label,
            )
        except ValueError as exc:
            raise WebApiError(400, str(exc)) from exc

        if updated_message is None:
            raise WebApiError(404, "레이블을 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

        corrected_outcome = self._serialize_corrected_outcome(updated_message.get("corrected_outcome"))
        content_reason_record = self._serialize_content_reason_record(updated_message.get("content_reason_record"))
        self.task_logger.log(
            session_id=session_id,
            action="content_reason_label_recorded",
            detail={
                "message_id": message_id,
                "artifact_id": updated_message.get("artifact_id"),
                "artifact_kind": updated_message.get("artifact_kind"),
                "reason_label": reason_label,
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
