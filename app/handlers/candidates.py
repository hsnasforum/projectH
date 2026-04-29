"""Candidate confirmation and review handler methods.

Extracted from AggregateHandlerMixin (the final extraction completing
the aggregate.py decomposition trilogy: M70, M77, M78).
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.errors import WebApiError
from app.handlers.corrections import _first_correction_snippets
from core.contracts import (
    CANDIDATE_REVIEW_ACTION_TO_STATUS,
    CandidateFamily,
    CandidateConfirmationScope,
    CandidateReviewAction,
    PreferenceStatus,
)


class CandidateHandlerMixin:
    """Candidate confirmation and review methods."""

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
                    "confirmation_scope": CandidateConfirmationScope.CANDIDATE_REUSE,
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
        reason_note = self._normalize_optional_text(payload.get("reason_note"))
        suggested_scope = self._normalize_optional_text(payload.get("suggested_scope"))
        statement_override = self._normalize_optional_text(payload.get("statement"))

        if str(message_id or "").strip() == "global":
            review_status = CANDIDATE_REVIEW_ACTION_TO_STATUS.get(review_action or "")
            if not review_status:
                raise WebApiError(400, "지원하지 않는 review action입니다.")
            fingerprint = str(candidate_id or "").removeprefix("global:").strip()
            if not fingerprint:
                raise WebApiError(400, "글로벌 후보 fingerprint를 확인할 수 없습니다.")
            session = self.session_store.get_session(session_id)
            session_title = str(session.get("title") or "").strip() or None
            if review_action == CandidateReviewAction.ACCEPT:
                corrections = self.correction_store.find_by_fingerprint(fingerprint)
                original_snippet, corrected_snippet = _first_correction_snippets(corrections)
                first_correction = corrections[0] if corrections else {}
                delta_summary = (
                    first_correction.get("delta_summary")
                    if isinstance(first_correction, dict)
                    else None
                )
                replacements = (
                    delta_summary.get("replacements", [])
                    if isinstance(delta_summary, dict)
                    else []
                )
                first_replacement = (
                    replacements[0]
                    if replacements and isinstance(replacements[0], dict)
                    else {}
                )
                default_description = str(first_replacement.get("to") or "").strip() or fingerprint[:60]
                description = str(statement_override or default_description)
                self.preference_store.record_reviewed_candidate_preference(
                    delta_fingerprint=fingerprint,
                    candidate_family=str(first_correction.get("pattern_family") or CandidateFamily.CORRECTION_REWRITE),
                    description=description,
                    source_refs={
                        "candidate_id": candidate_id or "",
                        "candidate_updated_at": candidate_updated_at or "",
                        "artifact_id": first_correction.get("artifact_id", ""),
                        "source_message_id": "global",
                        "review_action": review_action,
                        "session_id": session_id,
                        **({"reason_note": reason_note} if reason_note else {}),
                        **({"session_title": session_title} if session_title else {}),
                    },
                    original_snippet=original_snippet,
                    corrected_snippet=corrected_snippet,
                )
            elif review_action == CandidateReviewAction.REJECT:
                corrections = self.correction_store.find_by_fingerprint(fingerprint)
                first_correction = corrections[0] if corrections else {}
                self.preference_store.record_reviewed_candidate_preference(
                    delta_fingerprint=fingerprint,
                    candidate_family=str(first_correction.get("pattern_family") or CandidateFamily.CORRECTION_REWRITE),
                    description=fingerprint[:60],
                    source_refs={
                        "candidate_id": candidate_id or "",
                        "candidate_updated_at": candidate_updated_at or "",
                        "artifact_id": first_correction.get("artifact_id", "") if isinstance(first_correction, dict) else "",
                        "source_message_id": "global",
                        "review_action": review_action,
                        "session_id": session_id,
                        **({"reason_note": reason_note} if reason_note else {}),
                        **({"session_title": session_title} if session_title else {}),
                    },
                    status=PreferenceStatus.REJECTED,
                )
            self.task_logger.log(
                session_id=session_id,
                action="global_candidate_review_recorded",
                detail={
                    "candidate_id": candidate_id,
                    "fingerprint": fingerprint,
                    "review_action": review_action,
                },
            )
            return {
                "ok": True,
                "session": self._serialize_session(self.session_store.get_session(session_id)),
            }

        if not message_id:
            raise WebApiError(400, "검토 결과를 기록할 메시지 ID가 필요합니다.")
        review_status = CANDIDATE_REVIEW_ACTION_TO_STATUS.get(review_action or "")
        if not review_status:
            raise WebApiError(400, "지원하지 않는 review action입니다.")
        if not candidate_id or not candidate_updated_at:
            raise WebApiError(400, "현재 durable candidate 정보가 필요합니다.")

        session = self.session_store.get_session(session_id)
        session_title = str(session.get("title") or "").strip() or None
        source_message = None
        for message in reversed(session.get("messages", [])):
            if str(message.get("message_id") or "").strip() != message_id:
                continue
            source_message = dict(message)
            break
        if source_message is None:
            raise WebApiError(404, "검토 결과를 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

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
            raise WebApiError(400, "현재 검토 결과를 기록할 durable candidate가 없습니다.")

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
            raise WebApiError(409, "현재 검토 후보가 바뀌어 검토 대상을 다시 불러와야 합니다.")

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
                    "review_action": review_action,
                    "review_status": review_status,
                    **({"reason_note": reason_note} if reason_note else {}),
                    **({"suggested_scope": suggested_scope} if suggested_scope else {}),
                },
            )
        except ValueError as exc:
            raise WebApiError(400, str(exc)) from exc

        if updated_message is None:
            raise WebApiError(404, "검토 결과를 기록할 grounded-brief 원문 응답을 찾지 못했습니다.")

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

        if review_action == CandidateReviewAction.ACCEPT:
            candidate_recurrence_key = self._serialize_candidate_recurrence_key(
                self._build_candidate_recurrence_key_for_message(
                    message=source_message,
                    session_local_candidate=session_local_candidate,
                )
            )
            if candidate_recurrence_key is not None:
                fingerprint = str(candidate_recurrence_key.get("normalized_delta_fingerprint") or "").strip()
                if fingerprint:
                    artifact_id = str(source_message.get("artifact_id") or "").strip()
                    corrections = self.correction_store.find_by_artifact(artifact_id) if artifact_id else []
                    scores = [
                        float(c["similarity_score"])
                        for c in corrections
                        if isinstance(c.get("similarity_score"), (int, float))
                    ]
                    avg_similarity_score = round(sum(scores) / len(scores), 4) if scores else None
                    original_snippet, corrected_snippet = _first_correction_snippets(corrections)
                    self.preference_store.record_reviewed_candidate_preference(
                        delta_fingerprint=fingerprint,
                        candidate_family=str(durable_candidate.get("candidate_family") or ""),
                        description=str(statement_override or durable_candidate.get("statement") or "검토 수락된 교정 패턴"),
                        source_refs={
                            "candidate_id": candidate_id,
                            "candidate_updated_at": candidate_updated_at,
                            "artifact_id": artifact_id,
                            "source_message_id": str(source_message.get("message_id") or ""),
                            "review_action": review_action,
                            "session_id": session_id,
                            **({"reason_note": reason_note} if reason_note else {}),
                            **({"session_title": session_title} if session_title else {}),
                        },
                        avg_similarity_score=avg_similarity_score,
                        original_snippet=original_snippet,
                        corrected_snippet=corrected_snippet,
                    )
                    self.task_logger.log(
                        session_id=session_id,
                        action="preference_candidate_recorded",
                        detail={
                            "delta_fingerprint": fingerprint,
                            "candidate_id": candidate_id,
                            "candidate_family": durable_candidate.get("candidate_family"),
                            "source": "accepted_reviewed_candidate",
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
