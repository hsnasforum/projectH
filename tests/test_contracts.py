"""Backward-compatibility tests for core.contracts.

Every enum value must match the exact string previously hardcoded
across the codebase. If any value drifts, downstream serialization,
frontend comparisons, and stored JSON records will break silently.
"""

from __future__ import annotations

import unittest

from core.contracts import (
    ALLOWED_APPROVAL_REASON_LABELS,
    ALLOWED_CANDIDATE_CONFIRMATION_LABELS,
    ALLOWED_CONTENT_REASON_LABELS,
    ALLOWED_CORRECTED_OUTCOMES,
    ALLOWED_FEEDBACK_LABELS,
    ALLOWED_FEEDBACK_REASONS,
    ALLOWED_SAVE_CONTENT_SOURCES,
    ALLOWED_SESSION_LOCAL_CANDIDATE_FAMILIES,
    ALLOWED_WEB_SEARCH_PERMISSIONS,
    CANDIDATE_REVIEW_ACTION_TO_STATUS,
    RECORD_STAGE_TRANSITIONS,
    TRUSTED_SOURCE_ROLES,
    AnswerMode,
    ApprovalKind,
    ApprovalReasonScope,
    ArtifactKind,
    CandidateConfirmationScope,
    CandidateFamily,
    CandidateReviewAction,
    ContentReasonScope,
    ContentVerdict,
    CorrectedOutcome,
    CoverageStatus,
    FeedbackLabel,
    FeedbackReason,
    FreshnessRisk,
    FollowUpIntent,
    RecordStage,
    ResponseOriginKind,
    ResponseOriginProvider,
    ResponseStatus,
    ResultStage,
    SaveContentSource,
    SearchIntentKind,
    SourceRole,
    SourceType,
    StreamEventType,
    WebSearchPermission,
)


class ContractValueStabilityTest(unittest.TestCase):
    """Assert that every enum .value is the exact string the codebase relies on."""

    def test_response_status_values(self) -> None:
        self.assertEqual(ResponseStatus.ANSWER, "answer")
        self.assertEqual(ResponseStatus.ERROR, "error")
        self.assertEqual(ResponseStatus.NEEDS_APPROVAL, "needs_approval")
        self.assertEqual(ResponseStatus.SAVED, "saved")

    def test_artifact_kind_values(self) -> None:
        self.assertEqual(ArtifactKind.GROUNDED_BRIEF, "grounded_brief")

    def test_save_content_source_values(self) -> None:
        self.assertEqual(SaveContentSource.ORIGINAL_DRAFT, "original_draft")
        self.assertEqual(SaveContentSource.CORRECTED_TEXT, "corrected_text")

    def test_record_stage_values(self) -> None:
        self.assertEqual(RecordStage.EMITTED, "emitted_record_only_not_applied")
        self.assertEqual(RecordStage.APPLIED_PENDING, "applied_pending_result")
        self.assertEqual(RecordStage.APPLIED_WITH_RESULT, "applied_with_result")
        self.assertEqual(RecordStage.STOPPED, "stopped")
        self.assertEqual(RecordStage.REVERSED, "reversed")
        self.assertEqual(RecordStage.CONFLICT_CHECKED, "conflict_visibility_checked")

    def test_result_stage_values(self) -> None:
        self.assertEqual(ResultStage.RESULT_RECORDED_EFFECT_PENDING, "result_recorded_effect_pending")
        self.assertEqual(ResultStage.EFFECT_ACTIVE, "effect_active")
        self.assertEqual(ResultStage.EFFECT_STOPPED, "effect_stopped")
        self.assertEqual(ResultStage.EFFECT_REVERSED, "effect_reversed")

    def test_answer_mode_values(self) -> None:
        self.assertEqual(AnswerMode.GENERAL, "general")
        self.assertEqual(AnswerMode.ENTITY_CARD, "entity_card")
        self.assertEqual(AnswerMode.LATEST_UPDATE, "latest_update")

    def test_source_type_values(self) -> None:
        self.assertEqual(SourceType.OFFICIAL, "official")
        self.assertEqual(SourceType.DATABASE, "database")
        self.assertEqual(SourceType.NEWS, "news")
        self.assertEqual(SourceType.WIKI, "wiki")
        self.assertEqual(SourceType.COMMUNITY, "community")
        self.assertEqual(SourceType.GENERAL, "general")

    def test_source_role_values(self) -> None:
        self.assertEqual(SourceRole.WIKI, "백과 기반")
        self.assertEqual(SourceRole.OFFICIAL, "공식 기반")
        self.assertEqual(SourceRole.DATABASE, "데이터 기반")
        self.assertEqual(SourceRole.DESCRIPTIVE, "설명형 출처")
        self.assertEqual(SourceRole.NEWS, "보조 기사")
        self.assertEqual(SourceRole.AUXILIARY, "보조 출처")
        self.assertEqual(SourceRole.COMMUNITY, "보조 커뮤니티")
        self.assertEqual(SourceRole.PORTAL, "보조 포털")
        self.assertEqual(SourceRole.BLOG, "보조 블로그")

    def test_coverage_status_values(self) -> None:
        self.assertEqual(CoverageStatus.STRONG, "strong")
        self.assertEqual(CoverageStatus.WEAK, "weak")
        self.assertEqual(CoverageStatus.MISSING, "missing")

    def test_search_intent_kind_values(self) -> None:
        self.assertEqual(SearchIntentKind.NONE, "none")
        self.assertEqual(SearchIntentKind.EXPLICIT_WEB, "explicit_web")
        self.assertEqual(SearchIntentKind.LIVE_LATEST, "live_latest")
        self.assertEqual(SearchIntentKind.EXTERNAL_FACT, "external_fact")

    def test_freshness_risk_values(self) -> None:
        self.assertEqual(FreshnessRisk.LOW, "low")
        self.assertEqual(FreshnessRisk.HIGH, "high")

    def test_web_search_permission_values(self) -> None:
        self.assertEqual(WebSearchPermission.DISABLED, "disabled")
        self.assertEqual(WebSearchPermission.APPROVAL, "approval")
        self.assertEqual(WebSearchPermission.ENABLED, "enabled")

    def test_feedback_label_values(self) -> None:
        self.assertEqual(FeedbackLabel.HELPFUL, "helpful")
        self.assertEqual(FeedbackLabel.UNCLEAR, "unclear")
        self.assertEqual(FeedbackLabel.INCORRECT, "incorrect")

    def test_feedback_reason_values(self) -> None:
        self.assertEqual(FeedbackReason.FACTUAL_ERROR, "factual_error")
        self.assertEqual(FeedbackReason.IRRELEVANT_RESULT, "irrelevant_result")
        self.assertEqual(FeedbackReason.CONTEXT_MISS, "context_miss")
        self.assertEqual(FeedbackReason.AWKWARD_TONE, "awkward_tone")

    def test_corrected_outcome_values(self) -> None:
        self.assertEqual(CorrectedOutcome.ACCEPTED_AS_IS, "accepted_as_is")
        self.assertEqual(CorrectedOutcome.CORRECTED, "corrected")
        self.assertEqual(CorrectedOutcome.REJECTED, "rejected")

    def test_content_verdict_values(self) -> None:
        self.assertEqual(ContentVerdict.REJECTED, "rejected")

    def test_approval_reason_scope_values(self) -> None:
        self.assertEqual(ApprovalReasonScope.APPROVAL_REJECT, "approval_reject")
        self.assertEqual(ApprovalReasonScope.APPROVAL_REISSUE, "approval_reissue")

    def test_stream_event_type_values(self) -> None:
        self.assertEqual(StreamEventType.PHASE, "phase")
        self.assertEqual(StreamEventType.RUNTIME_STATUS, "runtime_status")
        self.assertEqual(StreamEventType.RESPONSE_ORIGIN, "response_origin")
        self.assertEqual(StreamEventType.TEXT_DELTA, "text_delta")
        self.assertEqual(StreamEventType.TEXT_REPLACE, "text_replace")
        self.assertEqual(StreamEventType.FINAL, "final")
        self.assertEqual(StreamEventType.CANCELLED, "cancelled")
        self.assertEqual(StreamEventType.ERROR, "error")
        self.assertEqual(StreamEventType.SEARCH_PREVIEW, "search_preview")

    def test_response_origin_provider_values(self) -> None:
        self.assertEqual(ResponseOriginProvider.OLLAMA, "ollama")
        self.assertEqual(ResponseOriginProvider.MOCK, "mock")
        self.assertEqual(ResponseOriginProvider.SYSTEM, "system")

    def test_response_origin_kind_values(self) -> None:
        self.assertEqual(ResponseOriginKind.APPROVAL, "approval")
        self.assertEqual(ResponseOriginKind.ASSISTANT, "assistant")

    def test_follow_up_intent_values(self) -> None:
        self.assertEqual(FollowUpIntent.GENERAL, "general")
        self.assertEqual(FollowUpIntent.KEY_POINTS, "key_points")
        self.assertEqual(FollowUpIntent.ACTION_ITEMS, "action_items")
        self.assertEqual(FollowUpIntent.MEMO, "memo")

    def test_approval_kind_values(self) -> None:
        self.assertEqual(ApprovalKind.SAVE_NOTE, "save_note")

    def test_candidate_family_values(self) -> None:
        self.assertEqual(CandidateFamily.CORRECTION_REWRITE, "correction_rewrite_preference")

    def test_candidate_review_action_values(self) -> None:
        self.assertEqual(CandidateReviewAction.ACCEPT, "accept")


class ContractDerivedSetsTest(unittest.TestCase):
    """Assert that ALLOWED_* frozensets match the old hand-maintained sets."""

    def test_allowed_save_content_sources(self) -> None:
        self.assertEqual(ALLOWED_SAVE_CONTENT_SOURCES, frozenset({"original_draft", "corrected_text"}))

    def test_allowed_web_search_permissions(self) -> None:
        self.assertEqual(ALLOWED_WEB_SEARCH_PERMISSIONS, frozenset({"disabled", "approval", "enabled"}))

    def test_allowed_feedback_labels(self) -> None:
        self.assertEqual(ALLOWED_FEEDBACK_LABELS, frozenset({"helpful", "unclear", "incorrect"}))

    def test_allowed_feedback_reasons(self) -> None:
        self.assertEqual(ALLOWED_FEEDBACK_REASONS, frozenset({"factual_error", "irrelevant_result", "context_miss", "awkward_tone"}))

    def test_allowed_corrected_outcomes(self) -> None:
        self.assertEqual(ALLOWED_CORRECTED_OUTCOMES, frozenset({"accepted_as_is", "corrected", "rejected"}))

    def test_allowed_approval_reason_labels(self) -> None:
        self.assertIn("approval_reject", ALLOWED_APPROVAL_REASON_LABELS)
        self.assertIn("explicit_rejection", ALLOWED_APPROVAL_REASON_LABELS["approval_reject"])
        self.assertIn("approval_reissue", ALLOWED_APPROVAL_REASON_LABELS)
        self.assertIn("path_change", ALLOWED_APPROVAL_REASON_LABELS["approval_reissue"])

    def test_allowed_content_reason_labels(self) -> None:
        self.assertIn("content_reject", ALLOWED_CONTENT_REASON_LABELS)
        self.assertIn("explicit_content_rejection", ALLOWED_CONTENT_REASON_LABELS["content_reject"])

    def test_allowed_candidate_families(self) -> None:
        self.assertEqual(ALLOWED_SESSION_LOCAL_CANDIDATE_FAMILIES, frozenset({"correction_rewrite_preference"}))

    def test_allowed_candidate_confirmation_labels(self) -> None:
        self.assertIn("candidate_reuse", ALLOWED_CANDIDATE_CONFIRMATION_LABELS)
        self.assertIn("explicit_reuse_confirmation", ALLOWED_CANDIDATE_CONFIRMATION_LABELS["candidate_reuse"])

    def test_candidate_review_action_to_status(self) -> None:
        self.assertEqual(CANDIDATE_REVIEW_ACTION_TO_STATUS["accept"], "accepted")

    def test_trusted_source_roles(self) -> None:
        self.assertEqual(TRUSTED_SOURCE_ROLES, frozenset({"백과 기반", "공식 기반", "데이터 기반", "설명형 출처"}))


class ContractTransitionRulesTest(unittest.TestCase):
    """Assert that the record-stage state machine is correct."""

    def test_emitted_can_transition_to_applied_pending(self) -> None:
        self.assertIn(RecordStage.APPLIED_PENDING, RECORD_STAGE_TRANSITIONS[RecordStage.EMITTED])

    def test_applied_pending_can_transition_to_applied_with_result(self) -> None:
        self.assertIn(RecordStage.APPLIED_WITH_RESULT, RECORD_STAGE_TRANSITIONS[RecordStage.APPLIED_PENDING])

    def test_applied_with_result_can_transition_to_stopped(self) -> None:
        self.assertIn(RecordStage.STOPPED, RECORD_STAGE_TRANSITIONS[RecordStage.APPLIED_WITH_RESULT])

    def test_stopped_can_transition_to_reversed(self) -> None:
        self.assertIn(RecordStage.REVERSED, RECORD_STAGE_TRANSITIONS[RecordStage.STOPPED])

    def test_reversed_can_transition_to_conflict_checked(self) -> None:
        self.assertIn(RecordStage.CONFLICT_CHECKED, RECORD_STAGE_TRANSITIONS[RecordStage.REVERSED])

    def test_no_backward_transitions(self) -> None:
        for source, targets in RECORD_STAGE_TRANSITIONS.items():
            for target in targets:
                if target in RECORD_STAGE_TRANSITIONS:
                    self.assertNotIn(
                        source,
                        RECORD_STAGE_TRANSITIONS[target],
                        f"Backward transition detected: {target} -> {source}",
                    )


class ContractStrEnumCompatibilityTest(unittest.TestCase):
    """StrEnum values must be == comparable with plain strings."""

    def test_str_equality(self) -> None:
        self.assertEqual(RecordStage.EMITTED, "emitted_record_only_not_applied")
        self.assertTrue(RecordStage.EMITTED == "emitted_record_only_not_applied")

    def test_str_in_frozenset(self) -> None:
        self.assertIn("disabled", ALLOWED_WEB_SEARCH_PERMISSIONS)
        self.assertIn("helpful", ALLOWED_FEEDBACK_LABELS)

    def test_str_as_dict_key(self) -> None:
        d = {RecordStage.EMITTED: 1}
        self.assertEqual(d["emitted_record_only_not_applied"], 1)

    def test_json_serializable(self) -> None:
        import json
        self.assertEqual(json.dumps(RecordStage.EMITTED), '"emitted_record_only_not_applied"')
        self.assertEqual(json.dumps(SourceRole.WIKI, ensure_ascii=False), '"백과 기반"')
