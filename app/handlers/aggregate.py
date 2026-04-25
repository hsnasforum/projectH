from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.errors import WebApiError
from core.contracts import (
    CANDIDATE_REVIEW_ACTION_TO_STATUS,
    CandidateFamily,
    CandidateConfirmationScope,
    CandidateReviewAction,
    PreferenceStatus,
    RecordStage,
    ResultStage,
    sanitize_supporting_review_refs,
)


def _first_correction_snippets(corrections: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for correction in corrections:
        original_text = correction.get("original_text") or ""
        corrected_text = correction.get("corrected_text") or ""
        if original_text and corrected_text:
            return str(original_text)[:400], str(corrected_text)[:400]
    return None, None


class AggregateHandlerMixin:
    """Candidate/aggregate transition methods extracted from WebAppService."""

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
            "record_stage": RecordStage.EMITTED,
            "task_log_mirror_relation": "mirror_allowed_not_canonical",
            "emitted_at": now,
        }
        supporting_review_refs = sanitize_supporting_review_refs(
            target_aggregate.get("supporting_review_refs")
        )
        if supporting_review_refs:
            transition_record["supporting_review_refs"] = supporting_review_refs

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
                "record_stage": RecordStage.EMITTED,
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
        if str(target_record.get("record_stage") or "").strip() != RecordStage.EMITTED:
            raise WebApiError(400, "이미 적용된 transition record입니다.")

        now = datetime.now(timezone.utc).isoformat()
        target_record["record_stage"] = RecordStage.APPLIED_PENDING
        target_record["applied_at"] = now
        self.session_store._save(session_id, session)

        self.task_logger.log(
            session_id=session_id,
            action="reviewed_memory_transition_applied",
            detail={
                "canonical_transition_id": canonical_transition_id,
                "transition_action": str(target_record.get("transition_action") or ""),
                "aggregate_fingerprint": aggregate_fingerprint,
                "record_stage": RecordStage.APPLIED_PENDING,
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
        if str(target_record.get("record_stage") or "").strip() != RecordStage.APPLIED_PENDING:
            raise WebApiError(400, "아직 적용 실행이 완료되지 않았거나 이미 결과가 확정되었습니다.")

        now = datetime.now(timezone.utc).isoformat()
        aggregate_identity_ref = dict(target_record.get("aggregate_identity_ref") or {})
        operator_reason = str(target_record.get("operator_reason_or_note") or "").strip()
        target_record["record_stage"] = RecordStage.APPLIED_WITH_RESULT
        target_record["apply_result"] = {
            "result_version": "first_reviewed_memory_apply_result_v1",
            "applied_effect_kind": "reviewed_memory_correction_pattern",
            "applied_scope": "same_session_exact_recurrence_aggregate_only",
            "aggregate_identity_ref": aggregate_identity_ref,
            "transition_ref": canonical_transition_id,
            "result_stage": ResultStage.EFFECT_ACTIVE,
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
                "record_stage": RecordStage.APPLIED_WITH_RESULT,
                "applied_effect_kind": "reviewed_memory_correction_pattern",
                "result_stage": ResultStage.EFFECT_ACTIVE,
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
        if str(target_record.get("record_stage") or "").strip() != RecordStage.APPLIED_WITH_RESULT:
            raise WebApiError(400, "적용 결과가 확정된 상태에서만 중단할 수 있습니다.")

        now = datetime.now(timezone.utc).isoformat()
        target_record["record_stage"] = RecordStage.STOPPED
        target_record["stopped_at"] = now
        if isinstance(target_record.get("apply_result"), dict):
            target_record["apply_result"]["result_stage"] = ResultStage.EFFECT_STOPPED

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
                "record_stage": RecordStage.STOPPED,
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
        if str(target_record.get("record_stage") or "").strip() != RecordStage.STOPPED:
            raise WebApiError(400, "적용이 중단된 상태에서만 되돌릴 수 있습니다.")

        now = datetime.now(timezone.utc).isoformat()
        target_record["record_stage"] = RecordStage.REVERSED
        target_record["reversed_at"] = now
        if isinstance(target_record.get("apply_result"), dict):
            target_record["apply_result"]["result_stage"] = ResultStage.EFFECT_REVERSED

        self.session_store._save(session_id, session)

        self.task_logger.log(
            session_id=session_id,
            action="reviewed_memory_transition_reversed",
            detail={
                "canonical_transition_id": canonical_transition_id,
                "aggregate_fingerprint": aggregate_fingerprint,
                "record_stage": RecordStage.REVERSED,
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
        if str(target_record.get("record_stage") or "").strip() != RecordStage.REVERSED:
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
                    if str(r.get("record_stage") or "").strip() == RecordStage.REVERSED
                ]
                active_records = [
                    r for r in applied_records
                    if str(r.get("record_stage") or "").strip() == RecordStage.APPLIED_WITH_RESULT
                    and isinstance(r.get("apply_result"), dict)
                    and str(r["apply_result"].get("result_stage") or "").strip() == ResultStage.EFFECT_ACTIVE
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
            "conflict_visibility_stage": RecordStage.CONFLICT_CHECKED,
            "record_stage": RecordStage.CONFLICT_CHECKED,
            "task_log_mirror_relation": "mirror_allowed_not_canonical",
            "checked_at": now,
        }
        supporting_review_refs = sanitize_supporting_review_refs(
            target_record.get("supporting_review_refs")
        )
        if supporting_review_refs:
            conflict_visibility_record["supporting_review_refs"] = supporting_review_refs

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
                "record_stage": RecordStage.CONFLICT_CHECKED,
                "checked_at": now,
            },
        )

        return {
            "ok": True,
            "canonical_transition_id": conflict_transition_id,
            "conflict_visibility_record": conflict_visibility_record,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }
