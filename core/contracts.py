"""Canonical source of truth for all enums, constants, and transition rules.

Every module in the project imports shared string constants from here.
Frontend JS constants are generated from this file.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class ResponseStatus(StrEnum):
    ANSWER = "answer"
    ERROR = "error"
    NEEDS_APPROVAL = "needs_approval"
    SAVED = "saved"


# ---------------------------------------------------------------------------
# Artifact
# ---------------------------------------------------------------------------

class ArtifactKind(StrEnum):
    GROUNDED_BRIEF = "grounded_brief"


# ---------------------------------------------------------------------------
# Save content source
# ---------------------------------------------------------------------------

class SaveContentSource(StrEnum):
    ORIGINAL_DRAFT = "original_draft"
    CORRECTED_TEXT = "corrected_text"


ALLOWED_SAVE_CONTENT_SOURCES = frozenset(SaveContentSource)


# ---------------------------------------------------------------------------
# Session-local memory signal
# ---------------------------------------------------------------------------

SESSION_LOCAL_MEMORY_SIGNAL_VERSION = "session_local_memory_signal_v1"


# ---------------------------------------------------------------------------
# Reviewed-memory transition lifecycle (record_stage)
# ---------------------------------------------------------------------------

class RecordStage(StrEnum):
    EMITTED = "emitted_record_only_not_applied"
    APPLIED_PENDING = "applied_pending_result"
    APPLIED_WITH_RESULT = "applied_with_result"
    STOPPED = "stopped"
    REVERSED = "reversed"
    CONFLICT_CHECKED = "conflict_visibility_checked"


RECORD_STAGE_TRANSITIONS: dict[RecordStage, tuple[RecordStage, ...]] = {
    RecordStage.EMITTED: (RecordStage.APPLIED_PENDING,),
    RecordStage.APPLIED_PENDING: (RecordStage.APPLIED_WITH_RESULT,),
    RecordStage.APPLIED_WITH_RESULT: (RecordStage.STOPPED,),
    RecordStage.STOPPED: (RecordStage.REVERSED,),
    RecordStage.REVERSED: (RecordStage.CONFLICT_CHECKED,),
}


# ---------------------------------------------------------------------------
# Result stage (effect lifecycle)
# ---------------------------------------------------------------------------

class ResultStage(StrEnum):
    RESULT_RECORDED_EFFECT_PENDING = "result_recorded_effect_pending"
    EFFECT_ACTIVE = "effect_active"
    EFFECT_STOPPED = "effect_stopped"
    EFFECT_REVERSED = "effect_reversed"


# ---------------------------------------------------------------------------
# Answer mode
# ---------------------------------------------------------------------------

class AnswerMode(StrEnum):
    GENERAL = "general"
    ENTITY_CARD = "entity_card"
    LATEST_UPDATE = "latest_update"


# ---------------------------------------------------------------------------
# Source type and role
# ---------------------------------------------------------------------------

class SourceType(StrEnum):
    OFFICIAL = "official"
    DATABASE = "database"
    NEWS = "news"
    WIKI = "wiki"
    COMMUNITY = "community"
    GENERAL = "general"


class SourceRole(StrEnum):
    WIKI = "백과 기반"
    OFFICIAL = "공식 기반"
    DATABASE = "데이터 기반"
    DESCRIPTIVE = "설명형 출처"
    NEWS = "보조 기사"
    AUXILIARY = "보조 출처"
    COMMUNITY = "보조 커뮤니티"
    PORTAL = "보조 포털"
    BLOG = "보조 블로그"


TRUSTED_SOURCE_ROLES = frozenset({
    SourceRole.WIKI,
    SourceRole.OFFICIAL,
    SourceRole.DATABASE,
    SourceRole.DESCRIPTIVE,
})


# ---------------------------------------------------------------------------
# Coverage status
# ---------------------------------------------------------------------------

class CoverageStatus(StrEnum):
    STRONG = "strong"
    CONFLICT = "conflict"
    WEAK = "weak"
    MISSING = "missing"


# ---------------------------------------------------------------------------
# Search intent
# ---------------------------------------------------------------------------

class SearchIntentKind(StrEnum):
    NONE = "none"
    EXPLICIT_WEB = "explicit_web"
    LIVE_LATEST = "live_latest"
    EXTERNAL_FACT = "external_fact"


class FreshnessRisk(StrEnum):
    LOW = "low"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Web search permission
# ---------------------------------------------------------------------------

class WebSearchPermission(StrEnum):
    DISABLED = "disabled"
    APPROVAL = "approval"
    ENABLED = "enabled"


ALLOWED_WEB_SEARCH_PERMISSIONS = frozenset(WebSearchPermission)


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackLabel(StrEnum):
    HELPFUL = "helpful"
    UNCLEAR = "unclear"
    INCORRECT = "incorrect"


ALLOWED_FEEDBACK_LABELS = frozenset(FeedbackLabel)


class FeedbackReason(StrEnum):
    FACTUAL_ERROR = "factual_error"
    IRRELEVANT_RESULT = "irrelevant_result"
    CONTEXT_MISS = "context_miss"
    AWKWARD_TONE = "awkward_tone"


ALLOWED_FEEDBACK_REASONS = frozenset(FeedbackReason)


# ---------------------------------------------------------------------------
# Corrected outcome
# ---------------------------------------------------------------------------

class CorrectedOutcome(StrEnum):
    ACCEPTED_AS_IS = "accepted_as_is"
    CORRECTED = "corrected"
    REJECTED = "rejected"


ALLOWED_CORRECTED_OUTCOMES = frozenset(CorrectedOutcome)


class CorrectedOutcomeReasonLabel(StrEnum):
    EXPLICIT_CORRECTION_SUBMITTED = "explicit_correction_submitted"


ALLOWED_CORRECTED_OUTCOME_REASON_LABELS: dict[str, frozenset[str]] = {
    CorrectedOutcome.CORRECTED: frozenset({CorrectedOutcomeReasonLabel.EXPLICIT_CORRECTION_SUBMITTED}),
}


# ---------------------------------------------------------------------------
# Content verdict
# ---------------------------------------------------------------------------

class ContentVerdict(StrEnum):
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Approval reason
# ---------------------------------------------------------------------------

class ApprovalReasonScope(StrEnum):
    APPROVAL_REJECT = "approval_reject"
    APPROVAL_REISSUE = "approval_reissue"


class ApprovalReasonLabel(StrEnum):
    EXPLICIT_REJECTION = "explicit_rejection"
    PATH_CHANGE = "path_change"
    CORRECTED_TEXT_REISSUE = "corrected_text_reissue"


ALLOWED_APPROVAL_REASON_LABELS: dict[str, frozenset[str]] = {
    ApprovalReasonScope.APPROVAL_REJECT: frozenset({ApprovalReasonLabel.EXPLICIT_REJECTION}),
    ApprovalReasonScope.APPROVAL_REISSUE: frozenset({
        ApprovalReasonLabel.PATH_CHANGE,
        ApprovalReasonLabel.CORRECTED_TEXT_REISSUE,
    }),
}


# ---------------------------------------------------------------------------
# Content reason
# ---------------------------------------------------------------------------

class ContentReasonScope(StrEnum):
    CONTENT_REJECT = "content_reject"


class ContentReasonLabel(StrEnum):
    EXPLICIT_CONTENT_REJECTION = "explicit_content_rejection"
    FACT_ERROR = "fact_error"
    TONE_ERROR = "tone_error"
    MISSING_INFO = "missing_info"


ALLOWED_CONTENT_REASON_LABELS: dict[str, frozenset[str]] = {
    ContentReasonScope.CONTENT_REJECT: frozenset({
        ContentReasonLabel.EXPLICIT_CONTENT_REJECTION,
        ContentReasonLabel.FACT_ERROR,
        ContentReasonLabel.TONE_ERROR,
        ContentReasonLabel.MISSING_INFO,
    }),
}


# ---------------------------------------------------------------------------
# Candidate
# ---------------------------------------------------------------------------

class CandidateFamily(StrEnum):
    CORRECTION_REWRITE = "correction_rewrite_preference"


ALLOWED_SESSION_LOCAL_CANDIDATE_FAMILIES = frozenset(CandidateFamily)


class CandidateConfirmationScope(StrEnum):
    CANDIDATE_REUSE = "candidate_reuse"


ALLOWED_CANDIDATE_CONFIRMATION_LABELS: dict[str, frozenset[str]] = {
    CandidateConfirmationScope.CANDIDATE_REUSE: frozenset({"explicit_reuse_confirmation"}),
}


class CandidateReviewAction(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    DEFER = "defer"
    EDIT = "edit"


class CandidateReviewSuggestedScope(StrEnum):
    MESSAGE_ONLY = "message_only"
    FAMILY_SCOPED = "family_scoped"
    GLOBAL_PREFERENCE = "global_preference"


class OperatorActionKind(StrEnum):
    LOCAL_FILE_EDIT = "local_file_edit"
    SHELL_EXECUTE = "shell_execute"
    SESSION_MUTATION = "session_mutation"


class OperatorActionContract(TypedDict, total=False):
    action_kind: str
    target_id: str
    content: str
    requested_at: str
    audit_trace_required: bool
    is_reversible: bool


class OperatorActionRecord(TypedDict, total=False):
    action_kind: str
    target_id: str
    content: str
    requested_at: str
    audit_trace_required: bool
    is_reversible: bool
    approval_id: str
    status: str
    outcome_id: str
    backup_path: str


CANDIDATE_REVIEW_ACTION_TO_STATUS: dict[str, str] = {
    CandidateReviewAction.ACCEPT: "accepted",
    CandidateReviewAction.REJECT: "rejected",
    CandidateReviewAction.DEFER: "deferred",
    CandidateReviewAction.EDIT: "edited",
}

CANDIDATE_REVIEW_OPTIONAL_FIELDS: frozenset[str] = frozenset({"reason_note", "suggested_scope"})


def sanitize_supporting_review_refs(refs: object) -> list[dict]:
    """Return only accepted review refs; reject/defer stay source-message audit-only."""
    if not isinstance(refs, list):
        return []
    return [
        dict(ref) for ref in refs
        if isinstance(ref, dict)
        and str(ref.get("review_action") or "").strip() == CandidateReviewAction.ACCEPT
    ]


# ---------------------------------------------------------------------------
# Stream event types
# ---------------------------------------------------------------------------

class StreamEventType(StrEnum):
    PHASE = "phase"
    RUNTIME_STATUS = "runtime_status"
    RESPONSE_ORIGIN = "response_origin"
    TEXT_DELTA = "text_delta"
    TEXT_REPLACE = "text_replace"
    FINAL = "final"
    CANCELLED = "cancelled"
    ERROR = "error"
    SEARCH_PREVIEW = "search_preview"


# ---------------------------------------------------------------------------
# Response origin
# ---------------------------------------------------------------------------

class ResponseOriginProvider(StrEnum):
    OLLAMA = "ollama"
    MOCK = "mock"
    SYSTEM = "system"


class ResponseOriginKind(StrEnum):
    APPROVAL = "approval"
    ASSISTANT = "assistant"


# ---------------------------------------------------------------------------
# Follow-up intent
# ---------------------------------------------------------------------------

class FollowUpIntent(StrEnum):
    GENERAL = "general"
    KEY_POINTS = "key_points"
    ACTION_ITEMS = "action_items"
    MEMO = "memo"


# ---------------------------------------------------------------------------
# Approval kind
# ---------------------------------------------------------------------------

class ApprovalKind(StrEnum):
    SAVE_NOTE = "save_note"
    OPERATOR_ACTION = "operator_action"


# ---------------------------------------------------------------------------
# Correction lifecycle
# ---------------------------------------------------------------------------

class CorrectionStatus(StrEnum):
    RECORDED = "recorded"
    CONFIRMED = "confirmed"
    PROMOTED = "promoted"
    ACTIVE = "active"
    STOPPED = "stopped"


CORRECTION_STATUS_TRANSITIONS: dict[CorrectionStatus, tuple[CorrectionStatus, ...]] = {
    CorrectionStatus.RECORDED: (CorrectionStatus.CONFIRMED,),
    CorrectionStatus.CONFIRMED: (CorrectionStatus.PROMOTED,),
    CorrectionStatus.PROMOTED: (CorrectionStatus.ACTIVE,),
    CorrectionStatus.ACTIVE: (CorrectionStatus.STOPPED,),
}


# ---------------------------------------------------------------------------
# Preference lifecycle (cross-session)
# ---------------------------------------------------------------------------

class PreferenceStatus(StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    PAUSED = "paused"
    REJECTED = "rejected"


PREFERENCE_STATUS_TRANSITIONS: dict[PreferenceStatus, tuple[PreferenceStatus, ...]] = {
    PreferenceStatus.CANDIDATE: (PreferenceStatus.ACTIVE, PreferenceStatus.REJECTED),
    PreferenceStatus.ACTIVE: (PreferenceStatus.PAUSED, PreferenceStatus.REJECTED),
    PreferenceStatus.PAUSED: (PreferenceStatus.ACTIVE, PreferenceStatus.REJECTED),
}
