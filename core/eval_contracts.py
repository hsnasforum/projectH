"""Eval fixture-family matrix and artifact core trace contract for Milestone 8.

Establishes the quality axes and trace shape for document -> grounded brief evaluation.
This is the manual-placeholder stage; service fixtures and unit helpers come later.
"""
from __future__ import annotations

from enum import StrEnum
from typing import TypedDict


# ---------------------------------------------------------------------------
# Fixture families
# ---------------------------------------------------------------------------

class EvalFixtureFamily(StrEnum):
    CORRECTION_REUSE = "correction_reuse"
    APPROVAL_FRICTION = "approval_friction"
    REVIEWED_VS_UNREVIEWED_TRACE = "reviewed_vs_unreviewed_trace"
    SCOPE_SUGGESTION_SAFETY = "scope_suggestion_safety"
    ROLLBACK_STOP_APPLY = "rollback_stop_apply"
    CONFLICT_DEFER_TRACE = "conflict_defer_trace"
    EXPLICIT_VS_SAVE_SUPPORT = "explicit_vs_save_support"


# ---------------------------------------------------------------------------
# Quality axes (kept separate per MILESTONES.md)
# ---------------------------------------------------------------------------

EVAL_QUALITY_AXES: frozenset[str] = frozenset({
    "correction_reuse",
    "approval_friction",
    "scope_safety",
    "reviewability",
    "rollbackability",
    "trace_completeness",
})


# ---------------------------------------------------------------------------
# Family -> quality axes mapping
# ---------------------------------------------------------------------------

EVAL_FIXTURE_FAMILY_AXES: dict[str, frozenset[str]] = {
    EvalFixtureFamily.CORRECTION_REUSE: frozenset({"correction_reuse", "trace_completeness"}),
    EvalFixtureFamily.APPROVAL_FRICTION: frozenset({"approval_friction", "trace_completeness"}),
    EvalFixtureFamily.REVIEWED_VS_UNREVIEWED_TRACE: frozenset({
        "reviewability", "trace_completeness",
    }),
    EvalFixtureFamily.SCOPE_SUGGESTION_SAFETY: frozenset({"scope_safety", "trace_completeness"}),
    EvalFixtureFamily.ROLLBACK_STOP_APPLY: frozenset({
        "rollbackability", "trace_completeness",
    }),
    EvalFixtureFamily.CONFLICT_DEFER_TRACE: frozenset({
        "reviewability", "rollbackability", "trace_completeness",
    }),
    EvalFixtureFamily.EXPLICIT_VS_SAVE_SUPPORT: frozenset({
        "approval_friction", "trace_completeness",
    }),
}


# ---------------------------------------------------------------------------
# Eval artifact core trace contract
# ---------------------------------------------------------------------------

class EvalArtifactCoreTrace(TypedDict, total=False):
    """Minimum fields shared by all eval trace artifacts.

    Family-specific extensions add fields on top of this contract.
    Approval-backed save counts as supporting evidence only, never sole quality signal.
    """
    artifact_id: str
    session_id: str
    fixture_family: str
    eval_axes: list[str]
    trace_version: str
    recorded_at: str


class CorrectionReuseTrace(EvalArtifactCoreTrace, total=False):
    reused_artifact_id: str
    reused_correction_id: str


class ApprovalFrictionTrace(EvalArtifactCoreTrace, total=False):
    approval_latency_sec: float
    rejection_count: int


class ReviewabilityTrace(EvalArtifactCoreTrace, total=False):
    is_reviewed: bool
    review_action: str


class ScopeSafetyTrace(EvalArtifactCoreTrace, total=False):
    suggested_scope: str
    safety_violation_count: int


class RollbackabilityTrace(EvalArtifactCoreTrace, total=False):
    is_rollback_possible: bool
    rollback_target_artifact_id: str


class ConflictDeferTrace(EvalArtifactCoreTrace, total=False):
    conflict_type: str
    deferral_count: int


class ExplicitVsSaveSupportTrace(EvalArtifactCoreTrace, total=False):
    support_method: str
    confidence_score: float


EVAL_FAMILY_TRACE_CLASS: dict[str, type] = {
    EvalFixtureFamily.CORRECTION_REUSE: CorrectionReuseTrace,
    EvalFixtureFamily.APPROVAL_FRICTION: ApprovalFrictionTrace,
    EvalFixtureFamily.REVIEWED_VS_UNREVIEWED_TRACE: ReviewabilityTrace,
    EvalFixtureFamily.SCOPE_SUGGESTION_SAFETY: ScopeSafetyTrace,
    EvalFixtureFamily.ROLLBACK_STOP_APPLY: RollbackabilityTrace,
    EvalFixtureFamily.CONFLICT_DEFER_TRACE: ConflictDeferTrace,
    EvalFixtureFamily.EXPLICIT_VS_SAVE_SUPPORT: ExplicitVsSaveSupportTrace,
}
