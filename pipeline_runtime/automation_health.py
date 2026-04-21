from __future__ import annotations

from collections.abc import Mapping
from typing import Any

AUTOMATION_HEALTH_VALUES = frozenset({"ok", "recovering", "attention", "needs_operator"})
AUTOMATION_NEXT_ACTION_VALUES = frozenset({
    "continue",
    "retrying",
    "advisory_followup",
    "verify_followup",
    "operator_required",
    "pr_boundary",
})

REAL_RISK_REASONS = frozenset({
    "approval_required",
    "truth_sync_required",
    "safety_stop",
    "security_incident",
    "destructive_risk",
    "auth_login_required",
})

PR_BOUNDARY_REASONS = frozenset({
    "pr_boundary",
    "publication_boundary",
    "external_publication_boundary",
})

ADVISORY_FOLLOWUP_REASONS = frozenset({
    "slice_ambiguity",
    "context_exhaustion",
    "session_rollover",
    "continue_vs_switch",
    "operator_retriage_no_next_control",
})

VERIFY_FOLLOWUP_REASONS = frozenset({
    "dispatch_stall",
    "post_accept_completion_stall",
    "signal_mismatch",
    "receipt_repair",
    "verify_manifest_mismatch",
    "duplicate_handoff",
    "waiting_next_control",
    "verified_blockers_resolved",
    "newer_unverified_work_present",
})

RECOVERY_REASONS = frozenset({
    "session_missing",
    "provider_outage",
    "idle_release_pending",
})


def _clean(value: object) -> str:
    return str(value or "").strip()


def automation_incident_family(reason_code: object) -> str:
    reason = _clean(reason_code)
    if not reason:
        return ""
    if reason == "post_accept_completion_stall" or reason.startswith("receipt_"):
        return "completion_stall"
    if reason == "dispatch_stall":
        return "dispatch_stall"
    if reason == "signal_mismatch":
        return "signal_mismatch"
    if reason == "operator_retriage_no_next_control":
        return "operator_retriage_no_next_control"
    if reason == "idle_release_pending":
        return "idle_release_pending"
    if reason == "session_recovery_exhausted":
        return "session_recovery_exhausted"
    if reason == "lane_recovery_exhausted" or reason.endswith("_recovery_failed") or reason.endswith("_broken"):
        return "lane_recovery_exhausted"
    return reason


def _is_real_risk_reason(reason: str) -> bool:
    return (
        reason in REAL_RISK_REASONS
        or reason.endswith("_auth_login_required")
        or reason.endswith("_credential_required")
        or "credential" in reason
    )


def _is_pr_boundary_reason(reason: str) -> bool:
    return reason in PR_BOUNDARY_REASONS


def _lane_note_reason(status: Mapping[str, Any]) -> str:
    for lane in list(status.get("lanes") or []):
        if not isinstance(lane, Mapping):
            continue
        note = _clean(lane.get("note"))
        if note in {"signal_mismatch", "idle_release_pending"}:
            return note
    return ""


def _first_recovery_exhaustion(degraded_reasons: list[str]) -> str:
    for reason in degraded_reasons:
        if (
            reason in {"lane_recovery_exhausted", "session_recovery_exhausted"}
            or reason.endswith("_recovery_failed")
            or reason.endswith("_broken")
        ):
            return reason
    return ""


def _payload(
    *,
    health: str,
    reason_code: str = "",
    next_action: str = "continue",
) -> dict[str, str]:
    family = automation_incident_family(reason_code)
    return {
        "automation_health": health if health in AUTOMATION_HEALTH_VALUES else "attention",
        "automation_reason_code": reason_code,
        "automation_incident_family": family,
        "automation_next_action": (
            next_action if next_action in AUTOMATION_NEXT_ACTION_VALUES else "verify_followup"
        ),
    }


def derive_automation_health(status: Mapping[str, Any] | None) -> dict[str, str]:
    if not isinstance(status, Mapping):
        return _payload(health="ok")

    runtime_state = _clean(status.get("runtime_state")) or "STOPPED"
    degraded_reasons = [_clean(item) for item in list(status.get("degraded_reasons") or []) if _clean(item)]
    degraded_reason = _clean(status.get("degraded_reason")) or (degraded_reasons[0] if degraded_reasons else "")
    autonomy = dict(status.get("autonomy") or {})
    control = dict(status.get("control") or {})
    autonomy_mode = _clean(autonomy.get("mode")) or "normal"
    autonomy_reason = (
        _clean(autonomy.get("reason_code"))
        or _clean(autonomy.get("block_reason"))
        or _clean(autonomy.get("degraded_reason"))
    )
    control_status = _clean(control.get("active_control_status"))

    if control_status == "needs_operator" or autonomy_mode == "needs_operator":
        reason = autonomy_reason or degraded_reason or "operator_required"
        next_action = "pr_boundary" if _is_pr_boundary_reason(reason) else "operator_required"
        return _payload(health="needs_operator", reason_code=reason, next_action=next_action)

    exhausted = _first_recovery_exhaustion(degraded_reasons)
    if exhausted:
        return _payload(
            health="needs_operator",
            reason_code=exhausted,
            next_action="operator_required",
        )

    if _is_real_risk_reason(degraded_reason) or _is_pr_boundary_reason(degraded_reason):
        next_action = "pr_boundary" if _is_pr_boundary_reason(degraded_reason) else "operator_required"
        return _payload(health="needs_operator", reason_code=degraded_reason, next_action=next_action)

    if runtime_state == "BROKEN":
        return _payload(
            health="needs_operator",
            reason_code=degraded_reason or "runtime_broken",
            next_action="operator_required",
        )

    if autonomy_mode == "triage":
        reason = autonomy_reason or "operator_candidate_pending"
        action = "verify_followup" if reason in VERIFY_FOLLOWUP_REASONS else "advisory_followup"
        return _payload(health="attention", reason_code=reason, next_action=action)

    if autonomy_mode == "recovery":
        reason = autonomy_reason or "runtime_recovery"
        action = "verify_followup" if reason in VERIFY_FOLLOWUP_REASONS else "retrying"
        return _payload(health="recovering", reason_code=reason, next_action=action)

    if autonomy_mode == "pending_operator":
        reason = autonomy_reason or "operator_candidate_pending"
        return _payload(health="attention", reason_code=reason, next_action="advisory_followup")

    note_reason = _lane_note_reason(status)
    if note_reason:
        action = "retrying" if note_reason == "idle_release_pending" else "verify_followup"
        health = "recovering" if note_reason == "idle_release_pending" else "attention"
        return _payload(health=health, reason_code=note_reason, next_action=action)

    if degraded_reason:
        if degraded_reason in RECOVERY_REASONS:
            return _payload(health="recovering", reason_code=degraded_reason, next_action="retrying")
        if degraded_reason in VERIFY_FOLLOWUP_REASONS or degraded_reason.startswith("receipt_"):
            action = "verify_followup"
        else:
            action = "advisory_followup"
        return _payload(health="attention", reason_code=degraded_reason, next_action=action)

    if runtime_state in {"STARTING", "STOPPING"}:
        reason = "runtime_starting" if runtime_state == "STARTING" else "runtime_stopping"
        return _payload(health="recovering", reason_code=reason, next_action="retrying")

    if runtime_state == "STOPPED":
        return _payload(
            health="attention",
            reason_code="runtime_stopped",
            next_action="operator_required",
        )

    return _payload(health="ok")
