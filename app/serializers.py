from __future__ import annotations

from pathlib import Path
from typing import Any

from app.localization import localize_text, localize_session
from core.contracts import (
    AnswerMode,
    CandidateConfirmationScope,
    CandidateFamily,
    CandidateReviewAction,
    CorrectedOutcome,
    CoverageStatus,
    ResponseOriginKind,
    ResponseOriginProvider,
    WebSearchPermission,
)
from core.agent_loop import AgentResponse


class SerializerMixin:
    """Mixin that groups all ``_serialize_*`` helpers used by WebAppService."""

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
            "applied_preferences": response.applied_preferences,
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
            "search_results": [
                {
                    "path": item.get("path", ""),
                    "matched_on": item.get("matched_on", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in (response.search_results or [])
            ],
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
                    "answer_mode": str(item.get("answer_mode") or AnswerMode.GENERAL),
                    "verification_label": localize_text(str(item.get("verification_label") or "")),
                    "source_roles": [localize_text(str(role)) for role in item.get("source_roles", []) if str(role).strip()],
                    "claim_coverage_summary": {
                        CoverageStatus.STRONG: int((item.get("claim_coverage_summary") or {}).get(CoverageStatus.STRONG) or 0),
                        CoverageStatus.WEAK: int((item.get("claim_coverage_summary") or {}).get(CoverageStatus.WEAK) or 0),
                        CoverageStatus.MISSING: int((item.get("claim_coverage_summary") or {}).get(CoverageStatus.MISSING) or 0),
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

    def _serialize_response_origin(self, origin: dict[str, Any] | None) -> dict[str, Any] | None:
        if origin is None:
            return None
        return {
            "provider": str(origin.get("provider") or ResponseOriginProvider.SYSTEM),
            "badge": str(origin.get("badge") or "SYSTEM"),
            "label": str(origin.get("label") or "시스템 응답"),
            "model": origin.get("model"),
            "kind": str(origin.get("kind") or ResponseOriginKind.ASSISTANT),
            "answer_mode": str(origin.get("answer_mode") or AnswerMode.GENERAL),
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
        if outcome != CorrectedOutcome.REJECTED or not recorded_at:
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
            or candidate_family != CandidateFamily.CORRECTION_REWRITE
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
            candidate_family != CandidateFamily.CORRECTION_REWRITE
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
            or candidate_family != CandidateFamily.CORRECTION_REWRITE
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
            or review_action != CandidateReviewAction.ACCEPT
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
            or candidate_family != CandidateFamily.CORRECTION_REWRITE
            or not candidate_updated_at
            or not artifact_id
            or source_message_id is None
            or confirmation_scope != CandidateConfirmationScope.CANDIDATE_REUSE
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
        web_search_permission = WebSearchPermission.DISABLED
        if isinstance(permissions, dict):
            web_search_permission = self._normalize_web_search_permission(permissions.get("web_search"))
        return {
            "web_search": web_search_permission,
            "web_search_label": self._web_search_permission_label(web_search_permission),
        }
