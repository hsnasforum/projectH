from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path
from typing import Any

from app.localization import localize_text, localize_session
from core.delta_analysis import is_high_quality
from core.contracts import (
    CANDIDATE_REVIEW_ACTION_TO_STATUS,
    AnswerMode,
    ArtifactKind,
    CandidateConfirmationScope,
    CandidateFamily,
    CandidateReviewAction,
    ContentReasonScope,
    ContentVerdict,
    CorrectedOutcome,
    CoverageStatus,
    RecordStage,
    ResponseOriginKind,
    ResponseOriginProvider,
    SESSION_LOCAL_MEMORY_SIGNAL_VERSION,
    WebSearchPermission,
    sanitize_supporting_review_refs,
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
                        CoverageStatus.CONFLICT: int((item.get("claim_coverage_summary") or {}).get(CoverageStatus.CONFLICT) or 0),
                        CoverageStatus.WEAK: int((item.get("claim_coverage_summary") or {}).get(CoverageStatus.WEAK) or 0),
                        CoverageStatus.MISSING: int((item.get("claim_coverage_summary") or {}).get(CoverageStatus.MISSING) or 0),
                    },
                    "claim_coverage_progress_summary": localize_text(
                        str(item.get("claim_coverage_progress_summary") or "")
                    ).strip(),
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
        raw_basis = str(context.get("summary_hint_basis") or "").strip()
        basis = raw_basis if raw_basis in {"current_summary", "recorded_correction"} else "current_summary"
        return {
            "kind": context.get("kind"),
            "label": context.get("label"),
            "source_paths": [str(path) for path in context.get("source_paths", [])],
            "summary_hint": localize_text(str(context.get("summary_hint", ""))),
            "summary_hint_basis": basis,
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
            "reason_label": str(corrected_outcome.get("reason_label") or "").strip() or None,
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

        signal_version = str(session_local_memory_signal.get("signal_version") or "").strip()
        signal_scope = str(session_local_memory_signal.get("signal_scope") or "").strip()
        artifact_id = str(session_local_memory_signal.get("artifact_id") or "").strip()
        source_message_id = self._serialize_source_message_id(session_local_memory_signal.get("source_message_id"))
        derived_at = str(session_local_memory_signal.get("derived_at") or "").strip()
        if (
            signal_version != SESSION_LOCAL_MEMORY_SIGNAL_VERSION
            or signal_scope != "session_local"
            or not artifact_id
            or source_message_id is None
            or not derived_at
        ):
            return None

        serialized: dict[str, Any] = {
            "signal_version": signal_version,
            "signal_scope": signal_scope,
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "derived_at": derived_at,
        }

        correction_signal = session_local_memory_signal.get("correction_signal")
        if isinstance(correction_signal, dict):
            corrected_outcome = self._serialize_corrected_outcome(correction_signal.get("corrected_outcome"))
            if isinstance(corrected_outcome, dict) and corrected_outcome.get("outcome") == CorrectedOutcome.CORRECTED:
                serialized["correction_signal"] = {
                    "corrected_outcome": corrected_outcome,
                    "has_corrected_text": bool(correction_signal.get("has_corrected_text")),
                }

        content_signal = session_local_memory_signal.get("content_signal")
        if isinstance(content_signal, dict):
            serialized_content_reason_record = self._serialize_content_reason_record(
                content_signal.get("content_reason_record")
            )
            if serialized_content_reason_record is not None:
                serialized["content_signal"] = {
                    "content_reason_record": serialized_content_reason_record,
                }

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
            latest_saved_at = str(save_signal.get("latest_saved_at") or "").strip() or None
            if latest_saved_at is not None:
                serialized_save_signal["latest_saved_at"] = latest_saved_at
            if serialized_save_signal:
                serialized["save_signal"] = serialized_save_signal

        if not any(
            key in serialized
            for key in ("correction_signal", "content_signal", "approval_signal", "save_signal")
        ):
            return None
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
        artifact_id = str(durable_candidate.get("artifact_id") or confirmation_ref["artifact_id"]).strip()
        source_message_id = self._serialize_source_message_id(
            durable_candidate.get("source_message_id") or confirmation_ref["source_message_id"]
        )
        derived_at = str(durable_candidate.get("derived_at") or confirmation_ref["recorded_at"]).strip()
        if (
            not artifact_id
            or source_message_id is None
            or artifact_id != confirmation_ref["artifact_id"]
            or source_message_id != confirmation_ref["source_message_id"]
            or not derived_at
        ):
            return None
        derived_from = {
            "record_type": "candidate_confirmation_record",
            "artifact_id": confirmation_ref["artifact_id"],
            "source_message_id": confirmation_ref["source_message_id"],
            "candidate_id": confirmation_ref["candidate_id"],
            "candidate_updated_at": confirmation_ref["candidate_updated_at"],
            "confirmation_label": confirmation_ref["confirmation_label"],
            "recorded_at": confirmation_ref["recorded_at"],
        }

        return {
            "candidate_id": candidate_id,
            "candidate_scope": candidate_scope,
            "candidate_family": candidate_family,
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "statement": statement,
            "derived_from": derived_from,
            "derived_at": derived_at,
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
        expected_status = CANDIDATE_REVIEW_ACTION_TO_STATUS.get(review_action)
        if (
            not candidate_id
            or not candidate_updated_at
            or not artifact_id
            or source_message_id is None
            or review_scope != "source_message_candidate_review"
            or expected_status is None
            or review_status != expected_status
            or not recorded_at
        ):
            return None

        normalized = {
            "candidate_id": candidate_id,
            "candidate_updated_at": candidate_updated_at,
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "review_scope": review_scope,
            "review_action": review_action,
            "review_status": review_status,
            "recorded_at": recorded_at,
        }
        reason_note = str(candidate_review_record.get("reason_note") or "").strip()
        if reason_note:
            normalized["reason_note"] = reason_note
        suggested_scope = str(candidate_review_record.get("suggested_scope") or "").strip()
        if suggested_scope:
            normalized["suggested_scope"] = suggested_scope
        return normalized

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
                    "support_plurality": str(item.get("support_plurality") or "").strip(),
                    "trust_tier": str(item.get("trust_tier") or "").strip(),
                    "trusted_source_count": int(item.get("trusted_source_count") or 0),
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

        aggregate_key = aggregate_candidate.get("aggregate_key")
        if not isinstance(aggregate_key, dict):
            return None
        fingerprint = str(aggregate_key.get("normalized_delta_fingerprint") or "").strip()
        if not fingerprint:
            return None

        stored_records = aggregate_candidate.get("_reviewed_memory_emitted_transition_records")
        if not isinstance(stored_records, list):
            return None

        matching_record: dict[str, Any] | None = None
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
            matching_record = record
            break

        if matching_record is None:
            return None

        record_stage = str(matching_record.get("record_stage") or "").strip()
        record_backed = record_stage not in ("", "emitted_record_only_not_applied")

        if not record_backed:
            expected_transition_audit_contract = (
                self._build_recurrence_aggregate_reviewed_memory_transition_audit_contract(aggregate_candidate)
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

        result = dict(matching_record)
        sanitized = sanitize_supporting_review_refs(result.get("supporting_review_refs"))
        if sanitized:
            result["supporting_review_refs"] = sanitized
        else:
            result.pop("supporting_review_refs", None)
        return result

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
            if str(record.get("record_stage") or "").strip() != RecordStage.CONFLICT_CHECKED:
                continue
            result = dict(record)
            sanitized = sanitize_supporting_review_refs(result.get("supporting_review_refs"))
            if sanitized:
                result["supporting_review_refs"] = sanitized
            else:
                result.pop("supporting_review_refs", None)
            return result

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
        current_candidate_index: dict[tuple[str, str], tuple[str, str]] = {}
        for message in messages:
            if not isinstance(message, dict):
                continue
            anchor = self._normalize_source_message_anchor(message)
            if anchor is None:
                continue
            slc = message.get("session_local_candidate")
            if isinstance(slc, dict):
                cid = str(slc.get("candidate_id") or "").strip()
                cua = str(slc.get("updated_at") or "").strip()
                if cid and cua:
                    current_candidate_index[anchor] = (cid, cua)
                    continue
            crk = message.get("candidate_recurrence_key")
            if isinstance(crk, dict):
                cid = str(crk.get("source_candidate_id") or "").strip()
                cua = str(crk.get("source_candidate_updated_at") or "").strip()
                if cid and cua:
                    current_candidate_index[anchor] = (cid, cua)

        grouped_members: dict[tuple[str, str, str, str, str], dict[tuple[str, str], dict[str, Any]]] = {}

        for message in messages:
            if not isinstance(message, dict):
                continue
            if (
                str(message.get("artifact_kind") or "").strip() != ArtifactKind.GROUNDED_BRIEF
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

        record_backed_fingerprints: set[str] = set()
        if isinstance(emitted_transition_records, list):
            for rec in emitted_transition_records:
                if not isinstance(rec, dict):
                    continue
                rec_identity = rec.get("aggregate_identity_ref")
                if not isinstance(rec_identity, dict):
                    continue
                fp = str(rec_identity.get("normalized_delta_fingerprint") or "").strip()
                if fp:
                    record_backed_fingerprints.add(fp)

        aggregate_candidates: list[dict[str, Any]] = []
        emitted_fingerprints: set[str] = set()
        for aggregate_identity, group_members in grouped_members.items():
            if len(group_members) < 2:
                continue

            fingerprint = aggregate_identity[4]
            has_record_backed_lifecycle = fingerprint in record_backed_fingerprints

            if not has_record_backed_lifecycle:
                stale = False
                for anchor, member in group_members.items():
                    current = current_candidate_index.get(anchor)
                    if current is None:
                        stale = True
                        break
                    current_cid, current_cua = current
                    if (
                        str(member.get("candidate_id") or "").strip() != current_cid
                        or str(member.get("candidate_updated_at") or "").strip() != current_cua
                    ):
                        stale = True
                        break
                if stale:
                    continue

            emitted_fingerprints.add(fingerprint)
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
                and str(review_ref.get("review_action") or "").strip() == "accept"
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

        missing_record_backed = record_backed_fingerprints - emitted_fingerprints
        if missing_record_backed and isinstance(emitted_transition_records, list):
            for rec in emitted_transition_records:
                if not isinstance(rec, dict):
                    continue
                rec_identity = rec.get("aggregate_identity_ref")
                if not isinstance(rec_identity, dict):
                    continue
                fp = str(rec_identity.get("normalized_delta_fingerprint") or "").strip()
                if not fp or fp not in missing_record_backed or fp in emitted_fingerprints:
                    continue
                emitted_fingerprints.add(fp)
                stored_source_refs = [
                    dict(ref) for ref in rec.get("supporting_source_message_refs", [])
                    if isinstance(ref, dict)
                ]
                stored_candidate_refs = [
                    dict(ref) for ref in rec.get("supporting_candidate_refs", [])
                    if isinstance(ref, dict)
                ]
                if not stored_source_refs:
                    continue
                timestamps = [
                    str(ref.get("candidate_updated_at") or "")
                    for ref in stored_candidate_refs
                    if str(ref.get("candidate_updated_at") or "").strip()
                ]
                first_seen = min(timestamps) if timestamps else str(rec.get("emitted_at") or "")
                last_seen = max(timestamps) if timestamps else str(rec.get("emitted_at") or "")
                aggregate_candidate = {
                    "aggregate_key": dict(rec_identity),
                    "supporting_source_message_refs": stored_source_refs,
                    "supporting_candidate_refs": stored_candidate_refs,
                    "recurrence_count": len(stored_source_refs),
                    "scope_boundary": "same_session_current_state_only",
                    "confidence_marker": "same_session_exact_key_match",
                    "first_seen_at": first_seen,
                    "last_seen_at": last_seen,
                }
                stored_review_refs = [
                    dict(ref) for ref in rec.get("supporting_review_refs", [])
                    if isinstance(ref, dict)
                ]
                if stored_review_refs:
                    aggregate_candidate["supporting_review_refs"] = stored_review_refs
                if isinstance(proof_record_store_entries, list) and proof_record_store_entries:
                    aggregate_candidate["_reviewed_memory_local_effect_presence_proof_record_store_entries"] = [
                        dict(item) for item in proof_record_store_entries if isinstance(item, dict)
                    ]
                aggregate_candidate["_reviewed_memory_emitted_transition_records"] = [
                    dict(item) for item in emitted_transition_records if isinstance(item, dict)
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
                str(message.get("artifact_kind") or "").strip() != ArtifactKind.GROUNDED_BRIEF
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

            corrections = self.correction_store.find_by_artifact(artifact_id)
            scores = [
                float(c["similarity_score"])
                for c in corrections
                if isinstance(c.get("similarity_score"), (int, float))
            ]
            avg_similarity_score = round(sum(scores) / len(scores), 4) if scores else None
            quality_info = {
                "avg_similarity_score": avg_similarity_score,
                "is_high_quality": (
                    is_high_quality(avg_similarity_score)
                    if avg_similarity_score is not None
                    else None
                ),
            }
            delta_summary = None
            for correction in corrections:
                candidate_delta_summary = correction.get("delta_summary")
                if isinstance(candidate_delta_summary, dict) and candidate_delta_summary:
                    delta_summary = candidate_delta_summary
                    break
            original_snippet = None
            corrected_snippet = None
            for correction in corrections:
                original_text = correction.get("original_text")
                corrected_text = correction.get("corrected_text")
                if isinstance(original_text, str) and isinstance(corrected_text, str) and original_text and corrected_text:
                    original_snippet = original_text[:400]
                    corrected_snippet = corrected_text[:400]
                    break

            review_queue_items.append(
                {
                    "item_type": "durable_candidate",
                    "candidate_id": durable_candidate["candidate_id"],
                    "candidate_scope": durable_candidate["candidate_scope"],
                    "candidate_family": durable_candidate["candidate_family"],
                    "statement": durable_candidate["statement"],
                    "derived_from": dict(durable_candidate["derived_from"]),
                    "derived_at": durable_candidate["derived_at"],
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
                    "quality_info": quality_info,
                    "delta_summary": delta_summary,
                    "original_snippet": original_snippet,
                    "corrected_snippet": corrected_snippet,
                    "is_global": False,
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
        try:
            recurring = self.correction_store.find_recurring_patterns()
            session_fps = {
                str(item.get("derived_from", {}).get("normalized_delta_fingerprint") or "")
                for item in review_queue_items
            }
            find_preference_by_fingerprint = getattr(self.preference_store, "find_by_fingerprint", None)
            list_preferences = getattr(self.preference_store, "list_all", None)
            for pattern in recurring:
                fp = str(pattern.get("delta_fingerprint") or "").strip()
                if not fp or fp in session_fps:
                    continue
                existing_preference = (
                    find_preference_by_fingerprint(fp)
                    if callable(find_preference_by_fingerprint)
                    else None
                )
                if existing_preference is None and callable(list_preferences):
                    existing_preference = next(
                        (
                            preference
                            for preference in list_preferences(limit=1000)
                            if str(preference.get("delta_fingerprint") or "").strip() == fp
                        ),
                        None,
                    )
                if existing_preference is not None:
                    continue

                corrections = pattern.get("corrections", [])
                first_correction = corrections[0] if corrections else {}
                delta_summary = first_correction.get("delta_summary") if isinstance(first_correction, dict) else None
                replacements = (
                    delta_summary.get("replacements", [])
                    if isinstance(delta_summary, dict)
                    else []
                )
                first_replacement = replacements[0] if replacements and isinstance(replacements[0], dict) else {}
                statement = str(first_replacement.get("to") or "").strip() or fp[:60]
                review_queue_items.append({
                    "item_type": "global_candidate",
                    "candidate_id": f"global:{fp}",
                    "candidate_scope": "global",
                    "candidate_family": pattern.get("pattern_family", "correction_rewrite"),
                    "statement": statement,
                    "derived_from": {"normalized_delta_fingerprint": fp, "record_type": "global_recurrence"},
                    "derived_at": pattern.get("last_seen_at", ""),
                    "promotion_basis": f"cross_session_recurrence:{pattern.get('recurrence_count', 0)}",
                    "promotion_eligibility": "eligible_for_review",
                    "artifact_id": first_correction.get("artifact_id", "") if isinstance(first_correction, dict) else "",
                    "source_message_id": "global",
                    "supporting_artifact_ids": [
                        correction.get("artifact_id", "")
                        for correction in corrections
                        if isinstance(correction, dict) and correction.get("artifact_id")
                    ],
                    "supporting_source_message_ids": [],
                    "supporting_signal_refs": [],
                    "supporting_confirmation_refs": [],
                    "created_at": pattern.get("first_seen_at", ""),
                    "updated_at": pattern.get("last_seen_at", ""),
                    "quality_info": None,
                    "delta_summary": delta_summary,
                    "original_snippet": (
                        str(first_correction.get("original_text") or "")[:400] or None
                    ) if isinstance(first_correction, dict) else None,
                    "corrected_snippet": (
                        str(first_correction.get("corrected_text") or "")[:400] or None
                    ) if isinstance(first_correction, dict) else None,
                    "is_global": True,
                })
        except Exception:
            pass
        return review_queue_items

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
            or candidate_family != CandidateFamily.CORRECTION_REWRITE
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
            "artifact_id": confirmation_artifact_id,
            "source_message_id": confirmation_source_message_id,
            "statement": session_local_candidate.get("statement"),
            "derived_from": {
                "record_type": "candidate_confirmation_record",
                "artifact_id": confirmation_artifact_id,
                "source_message_id": confirmation_source_message_id,
                "candidate_id": candidate_id,
                "candidate_updated_at": candidate_updated_at,
                "confirmation_label": candidate_confirmation_record.get("confirmation_label"),
                "recorded_at": confirmation_recorded_at,
            },
            "derived_at": confirmation_recorded_at,
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

        correction_signal = session_local_memory_signal.get("correction_signal")
        if not isinstance(correction_signal, dict):
            return None
        latest_corrected_outcome = correction_signal.get("corrected_outcome")
        if not isinstance(latest_corrected_outcome, dict):
            return None
        if str(latest_corrected_outcome.get("outcome") or "").strip() != CorrectedOutcome.CORRECTED:
            return None
        if not bool(correction_signal.get("has_corrected_text")):
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
                "signal_name": "session_local_memory_signal.correction_signal",
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
            "candidate_family": CandidateFamily.CORRECTION_REWRITE,
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
            or candidate_family != CandidateFamily.CORRECTION_REWRITE
            or not candidate_updated_at
            or artifact_id not in supporting_artifact_ids
            or source_message_id not in supporting_source_message_ids
        ):
            return None

        corrected_outcome = self._serialize_corrected_outcome(message.get("corrected_outcome"))
        if (
            not isinstance(corrected_outcome, dict)
            or str(corrected_outcome.get("outcome") or "").strip() != CorrectedOutcome.CORRECTED
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
        if serialized.get("reason_scope") != ContentReasonScope.CONTENT_REJECT:
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
        serialized["artifact_kind"] = str(serialized.get("artifact_kind") or "").strip() or ArtifactKind.GROUNDED_BRIEF
        serialized["source_message_id"] = source_message_id
        if not str(serialized.get("recorded_at") or "").strip():
            return None
        return serialized

    def _iter_task_log_records(self, *, session_id: str) -> list[dict[str, Any]]:
        normalized_session_id = self._normalize_optional_text(session_id)
        if normalized_session_id is None:
            return []
        return self.task_logger.iter_session_records(normalized_session_id)

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
                if str(detail.get("content_verdict") or "").strip() != ContentVerdict.REJECTED:
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
                        "outcome": CorrectedOutcome.REJECTED,
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

        latest_corrected_outcome = self._serialize_corrected_outcome(message.get("corrected_outcome"))
        if isinstance(latest_corrected_outcome, dict):
            if str(latest_corrected_outcome.get("outcome") or "").strip() == CorrectedOutcome.REJECTED:
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
