"""Canonical source of truth for all enums, constants, and transition rules.

Every module in the project imports shared string constants from here.
Frontend JS constants are generated from this file.
"""

from __future__ import annotations

from enum import StrEnum


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


ALLOWED_APPROVAL_REASON_LABELS: dict[str, frozenset[str]] = {
    ApprovalReasonScope.APPROVAL_REJECT: frozenset({"explicit_rejection"}),
    ApprovalReasonScope.APPROVAL_REISSUE: frozenset({"path_change"}),
}


# ---------------------------------------------------------------------------
# Content reason
# ---------------------------------------------------------------------------

class ContentReasonScope(StrEnum):
    CONTENT_REJECT = "content_reject"


ALLOWED_CONTENT_REASON_LABELS: dict[str, frozenset[str]] = {
    ContentReasonScope.CONTENT_REJECT: frozenset({"explicit_content_rejection"}),
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


CANDIDATE_REVIEW_ACTION_TO_STATUS: dict[str, str] = {
    CandidateReviewAction.ACCEPT: "accepted",
    CandidateReviewAction.REJECT: "rejected",
    CandidateReviewAction.DEFER: "deferred",
}


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
