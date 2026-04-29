from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .operator_autonomy import (
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
    OPERATOR_APPROVAL_COMPLETED_REASON,
    PUBLICATION_BOUNDARY_REASON_CODES,
    PR_CREATION_GATE_REASON,
    PR_MERGE_GATE_REASON,
)

# The watcher normally polls once per second. Keep this well above a typical
# verify/handoff round pause so the flag means "stuck for a long time", not
# "an agent is still working through a normal round".
STALE_CONTROL_CYCLE_THRESHOLD = 900
STALE_ADVISORY_GRACE_CYCLES = 60
IMPLEMENT_READY_IDLE_CYCLE_THRESHOLD = 120

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

PR_BOUNDARY_REASONS = PUBLICATION_BOUNDARY_REASON_CODES

ADVISORY_FOLLOWUP_REASONS = frozenset({
    "slice_ambiguity",
    "context_exhaustion",
    "session_rollover",
    "continue_vs_switch",
    "operator_retriage_no_next_control",
    "stale_control_advisory",
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
    "pr_merge_completed",
    "pr_merge_head_mismatch",
    OPERATOR_APPROVAL_COMPLETED_REASON,
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
    PR_CREATION_GATE_REASON,
    PR_MERGE_GATE_REASON,
    "newer_unverified_work_present",
})

RECOVERY_REASONS = frozenset({
    "session_missing",
    "provider_outage",
    "idle_release_pending",
})


def _clean(value: object) -> str:
    return str(value or "").strip()


def _nonnegative_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        normalized = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return normalized if normalized >= 0 else default


def advance_control_seq_age(
    *,
    last_seen_control_seq: int | None,
    control_seq_age_cycles: int,
    current_control_seq: int | None,
) -> tuple[int | None, int]:
    """Advance consecutive-cycle age for the currently highest CONTROL_SEQ."""
    if current_control_seq is None:
        return None, 0
    if current_control_seq == last_seen_control_seq:
        return current_control_seq, _nonnegative_int(control_seq_age_cycles) + 1
    return current_control_seq, 0


def automation_incident_family(reason_code: object) -> str:
    reason = _clean(reason_code)
    if not reason:
        return ""
    if reason == "implement_active_idle":
        return "idle_release_pending"
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


def _active_implement_lane_ready(status: Mapping[str, Any]) -> bool:
    turn_state = status.get("turn_state")
    if not isinstance(turn_state, Mapping):
        return False
    active_lane = _clean(turn_state.get("active_lane"))
    if not active_lane:
        return False
    for lane in list(status.get("lanes") or []):
        if not isinstance(lane, Mapping):
            continue
        if _clean(lane.get("name")) != active_lane:
            continue
        return _clean(lane.get("state")) == "READY" and _clean(lane.get("note")) in {
            "",
            "prompt_visible",
        }
    return False


def _active_round_matches_latest_work(status: Mapping[str, Any]) -> bool:
    active_round = status.get("active_round")
    if not isinstance(active_round, Mapping):
        return False
    artifacts = status.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return False
    latest_work = artifacts.get("latest_work")
    if not isinstance(latest_work, Mapping):
        return False
    latest_path = _clean(latest_work.get("path"))
    round_path = _clean(active_round.get("artifact_path"))
    if not latest_path or latest_path == "—" or not round_path:
        return False
    normalized_latest = latest_path.lstrip("./")
    normalized_round = round_path.replace("\\", "/").lstrip("./")
    return normalized_round.endswith(normalized_latest)


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
    control_age_cycles: int = 0,
) -> dict[str, object]:
    family = automation_incident_family(reason_code)
    normalized_control_age = _nonnegative_int(control_age_cycles)
    stale_control_seq = normalized_control_age >= STALE_CONTROL_CYCLE_THRESHOLD
    stale_advisory_pending = (
        normalized_control_age
        >= STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES
    )
    health_detail = (
        f"제어 슬롯 고착 감지됨 ({normalized_control_age} 사이클)"
        if stale_control_seq
        else ""
    )
    return {
        "automation_health": health if health in AUTOMATION_HEALTH_VALUES else "attention",
        "automation_reason_code": reason_code,
        "automation_incident_family": family,
        "automation_next_action": (
            next_action if next_action in AUTOMATION_NEXT_ACTION_VALUES else "verify_followup"
        ),
        "control_age_cycles": normalized_control_age,
        "stale_control_seq": stale_control_seq,
        "stale_control_cycle_threshold": STALE_CONTROL_CYCLE_THRESHOLD,
        "stale_advisory_grace_cycles": STALE_ADVISORY_GRACE_CYCLES,
        "stale_advisory_pending": stale_advisory_pending,
        "automation_health_detail": health_detail,
    }


def _control_age_from_status(status: Mapping[str, Any]) -> int:
    top_level_age = status.get("control_age_cycles")
    if top_level_age is not None:
        return _nonnegative_int(top_level_age)
    control = status.get("control")
    if isinstance(control, Mapping):
        return _nonnegative_int(control.get("control_age_cycles"))
    return 0


def derive_automation_health(status: Mapping[str, Any] | None) -> dict[str, object]:
    if not isinstance(status, Mapping):
        return _payload(health="ok")

    control_age_cycles = _control_age_from_status(status)

    def payload(
        *,
        health: str,
        reason_code: str = "",
        next_action: str = "continue",
    ) -> dict[str, object]:
        return _payload(
            health=health,
            reason_code=reason_code,
            next_action=next_action,
            control_age_cycles=control_age_cycles,
        )

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
    turn_state = status.get("turn_state")
    turn_name = ""
    turn_reason = ""
    if isinstance(turn_state, Mapping):
        turn_name = _clean(turn_state.get("state"))
        turn_reason = _clean(turn_state.get("reason"))

    if control_status == "needs_operator" or autonomy_mode == "needs_operator":
        reason = autonomy_reason or degraded_reason or "operator_required"
        next_action = "pr_boundary" if _is_pr_boundary_reason(reason) else "operator_required"
        return payload(health="needs_operator", reason_code=reason, next_action=next_action)

    exhausted = _first_recovery_exhaustion(degraded_reasons)
    if exhausted:
        return payload(
            health="needs_operator",
            reason_code=exhausted,
            next_action="operator_required",
        )

    if _is_real_risk_reason(degraded_reason) or _is_pr_boundary_reason(degraded_reason):
        next_action = "pr_boundary" if _is_pr_boundary_reason(degraded_reason) else "operator_required"
        return payload(health="needs_operator", reason_code=degraded_reason, next_action=next_action)

    if runtime_state == "BROKEN":
        return payload(
            health="needs_operator",
            reason_code=degraded_reason or "runtime_broken",
            next_action="operator_required",
        )

    if autonomy_mode == "triage":
        reason = autonomy_reason or "operator_candidate_pending"
        action = "verify_followup" if reason in VERIFY_FOLLOWUP_REASONS else "advisory_followup"
        return payload(health="attention", reason_code=reason, next_action=action)

    if autonomy_mode == "recovery":
        reason = autonomy_reason or "runtime_recovery"
        action = "verify_followup" if reason in VERIFY_FOLLOWUP_REASONS else "retrying"
        return payload(health="recovering", reason_code=reason, next_action=action)

    if autonomy_mode == "pending_operator":
        reason = autonomy_reason or "operator_candidate_pending"
        return payload(health="attention", reason_code=reason, next_action="advisory_followup")

    if autonomy_mode == "hibernate":
        reason = autonomy_reason or degraded_reason or "idle_hibernate"
        if _is_real_risk_reason(reason) or _is_pr_boundary_reason(reason):
            action = "pr_boundary" if _is_pr_boundary_reason(reason) else "operator_required"
            return payload(health="needs_operator", reason_code=reason, next_action=action)

    note_reason = _lane_note_reason(status)
    if note_reason:
        action = "retrying" if note_reason == "idle_release_pending" else "verify_followup"
        health = "recovering" if note_reason == "idle_release_pending" else "attention"
        return payload(health=health, reason_code=note_reason, next_action=action)

    if (
        runtime_state == "RUNNING"
        and control_status == "implement"
        and turn_name == "IDLE"
        and turn_reason == "implement_idle_timeout"
        and not _active_round_matches_latest_work(status)
    ):
        return payload(
            health="recovering",
            reason_code="idle_release_pending",
            next_action="retrying",
        )

    if (
        runtime_state == "RUNNING"
        and control_status == "implement"
        and turn_name == "IMPLEMENT_ACTIVE"
        and not _active_round_matches_latest_work(status)
        and control_age_cycles >= IMPLEMENT_READY_IDLE_CYCLE_THRESHOLD
        and _active_implement_lane_ready(status)
    ):
        return payload(
            health="attention",
            reason_code="implement_active_idle",
            next_action="retrying",
        )

    if degraded_reason:
        if degraded_reason in RECOVERY_REASONS:
            return payload(health="recovering", reason_code=degraded_reason, next_action="retrying")
        if degraded_reason in VERIFY_FOLLOWUP_REASONS or degraded_reason.startswith("receipt_"):
            action = "verify_followup"
        else:
            action = "advisory_followup"
        return payload(health="attention", reason_code=degraded_reason, next_action=action)

    if runtime_state in {"STARTING", "STOPPING"}:
        reason = "runtime_starting" if runtime_state == "STARTING" else "runtime_stopping"
        return payload(health="recovering", reason_code=reason, next_action="retrying")

    if runtime_state == "STOPPED":
        return payload(
            health="attention",
            reason_code="runtime_stopped",
            next_action="operator_required",
        )

    if control_age_cycles >= STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES:
        return payload(
            health="attention",
            reason_code="stale_control_advisory",
            next_action="advisory_followup",
        )

    return payload(health="ok")
