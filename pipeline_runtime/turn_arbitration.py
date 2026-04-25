from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .role_routes import (
    LEGACY_CODEX_FOLLOWUP_ROUTE,
    VERIFY_FOLLOWUP_ROUTE,
    is_verify_followup_route,
)
from .schema import active_control_snapshot_from_status, control_seq_value, snapshot_control_seq

TURN_IMPLEMENT = "implement"
TURN_VERIFY = "verify"
TURN_VERIFY_FOLLOWUP = "verify_followup"
TURN_OPERATOR = "operator"
TURN_ADVISORY = "advisory"
TURN_IDLE = "idle"

TURN_CLAUDE = TURN_IMPLEMENT
TURN_CODEX_VERIFY = TURN_VERIFY
TURN_CODEX_FOLLOWUP = TURN_VERIFY_FOLLOWUP
TURN_GEMINI = TURN_ADVISORY

LEGACY_WATCHER_TURN_BY_CANONICAL = {
    TURN_IMPLEMENT: "claude",
    TURN_VERIFY: "codex",
    TURN_VERIFY_FOLLOWUP: VERIFY_FOLLOWUP_ROUTE,
    TURN_ADVISORY: "gemini",
    TURN_OPERATOR: "operator",
    TURN_IDLE: "idle",
}

LEGACY_WATCHER_TURN_ALIASES = {
    LEGACY_CODEX_FOLLOWUP_ROUTE: TURN_VERIFY_FOLLOWUP,
}

TURN_STATE_IDLE = "IDLE"
TURN_STATE_IMPLEMENT_ACTIVE = "IMPLEMENT_ACTIVE"
TURN_STATE_VERIFY_ACTIVE = "VERIFY_ACTIVE"
TURN_STATE_VERIFY_FOLLOWUP = "VERIFY_FOLLOWUP"
TURN_STATE_ADVISORY_ACTIVE = "ADVISORY_ACTIVE"
TURN_STATE_OPERATOR_WAIT = "OPERATOR_WAIT"

LEGACY_TURN_STATE_BY_CANONICAL = {
    TURN_STATE_IDLE: "IDLE",
    TURN_STATE_IMPLEMENT_ACTIVE: "CLAUDE_ACTIVE",
    TURN_STATE_VERIFY_ACTIVE: "CODEX_VERIFY",
    TURN_STATE_VERIFY_FOLLOWUP: "CODEX_FOLLOWUP",
    TURN_STATE_ADVISORY_ACTIVE: "GEMINI_ADVISORY",
    TURN_STATE_OPERATOR_WAIT: "OPERATOR_WAIT",
}
CANONICAL_TURN_STATE_BY_LEGACY = {
    legacy: canonical
    for canonical, legacy in LEGACY_TURN_STATE_BY_CANONICAL.items()
}
TURN_ROLE_BY_STATE = {
    TURN_STATE_IMPLEMENT_ACTIVE: "implement",
    TURN_STATE_VERIFY_ACTIVE: "verify",
    TURN_STATE_VERIFY_FOLLOWUP: "verify",
    TURN_STATE_ADVISORY_ACTIVE: "advisory",
    TURN_STATE_OPERATOR_WAIT: "operator",
}

TURN_STATES_WITHOUT_VERIFY_SURFACE = frozenset(
    {
        TURN_STATE_IMPLEMENT_ACTIVE,
        TURN_STATE_VERIFY_FOLLOWUP,
        TURN_STATE_ADVISORY_ACTIVE,
        TURN_STATE_OPERATOR_WAIT,
    }
)

VERIFY_ROUND_STATES = frozenset({"VERIFY_PENDING", "VERIFYING"})


@dataclass(frozen=True)
class WatcherTurnInputs:
    operator_request_active: bool
    advisory_request_active: bool
    advisory_advice_active: bool
    implement_handoff_active: bool
    latest_work_needs_verify: bool
    implement_handoff_verify_active: bool
    idle_release_cooldown_active: bool
    operator_recovery_marker: Mapping[str, Any] | None = None
    operator_gate_marker: Mapping[str, Any] | None = None


def canonical_turn_state_name(
    state: object,
    *,
    legacy_state: object = "",
) -> str:
    state_value = str(state or "").strip()
    if state_value in LEGACY_TURN_STATE_BY_CANONICAL:
        return state_value
    if state_value in CANONICAL_TURN_STATE_BY_LEGACY:
        return CANONICAL_TURN_STATE_BY_LEGACY[state_value]
    legacy_value = str(legacy_state or "").strip()
    if legacy_value in CANONICAL_TURN_STATE_BY_LEGACY:
        return CANONICAL_TURN_STATE_BY_LEGACY[legacy_value]
    return TURN_STATE_IDLE


def legacy_turn_state_name(state: object) -> str:
    canonical = canonical_turn_state_name(state)
    return LEGACY_TURN_STATE_BY_CANONICAL.get(canonical, "IDLE")


def turn_state_role(
    state: object,
    *,
    active_role: object = "",
) -> str:
    active_role_value = str(active_role or "").strip()
    if active_role_value:
        return active_role_value
    canonical = canonical_turn_state_name(state)
    return TURN_ROLE_BY_STATE.get(canonical, "")


def legacy_watcher_turn_name(turn: object) -> str:
    token = str(turn or "").strip()
    return LEGACY_WATCHER_TURN_BY_CANONICAL.get(
        LEGACY_WATCHER_TURN_ALIASES.get(token, token),
        TURN_IDLE,
    )


def resolve_watcher_turn(inputs: WatcherTurnInputs) -> str:
    operator_recovery = inputs.operator_recovery_marker
    operator_gate = inputs.operator_gate_marker

    if (
        inputs.operator_request_active
        and operator_recovery is None
        and operator_gate is None
    ):
        return TURN_OPERATOR

    if inputs.advisory_request_active:
        return TURN_ADVISORY

    if inputs.advisory_advice_active:
        return TURN_VERIFY_FOLLOWUP

    if (
        operator_gate is not None
        and str(operator_gate.get("routed_to") or "") == "hibernate"
    ):
        return TURN_IDLE

    if inputs.implement_handoff_active and (
        inputs.latest_work_needs_verify or inputs.implement_handoff_verify_active
    ):
        return TURN_VERIFY

    if inputs.latest_work_needs_verify:
        return TURN_VERIFY

    if inputs.implement_handoff_active and not inputs.idle_release_cooldown_active:
        return TURN_IMPLEMENT

    if operator_recovery is not None:
        return TURN_VERIFY_FOLLOWUP

    if (
        operator_gate is not None
        and is_verify_followup_route(operator_gate.get("routed_to"))
    ):
        return TURN_VERIFY_FOLLOWUP

    return TURN_IDLE


def active_lane_for_runtime(
    turn_state: Mapping[str, Any] | None,
    active_round: Mapping[str, Any] | None,
    *,
    control: Mapping[str, Any] | None = None,
    last_receipt: Mapping[str, Any] | None = None,
    duplicate_control: Mapping[str, Any] | None = None,
    stale_operator_control: Mapping[str, Any] | None = None,
    implement_owner: str,
    verify_owner: str,
    advisory_owner: str,
) -> str:
    state = canonical_turn_state_name(
        (turn_state or {}).get("state"),
        legacy_state=(turn_state or {}).get("legacy_state"),
    )
    round_state = str((active_round or {}).get("state") or "")
    completion_stage = str((active_round or {}).get("completion_stage") or "")
    control_snapshot = active_control_snapshot_from_status(dict(control or {}))
    control_status = str(control_snapshot.get("control_status") or "")
    control_seq = snapshot_control_seq(control_snapshot)
    last_receipt_seq = control_seq_value((last_receipt or {}).get("control_seq"), default=-1)

    if (
        state == TURN_STATE_IMPLEMENT_ACTIVE
        and control_status == "implement"
        and control_seq >= 0
        and duplicate_control is None
        and control_seq > last_receipt_seq
    ):
        return implement_owner

    if state in {TURN_STATE_VERIFY_ACTIVE, TURN_STATE_VERIFY_FOLLOWUP}:
        return verify_owner

    if state == TURN_STATE_ADVISORY_ACTIVE:
        return advisory_owner

    if state == TURN_STATE_OPERATOR_WAIT and stale_operator_control is None:
        return ""

    if round_state in VERIFY_ROUND_STATES:
        return verify_owner

    if round_state == "RECEIPT_PENDING":
        if completion_stage == "receipt_close_pending":
            return ""
        return ""

    return ""


def suppress_active_round_for_turn(
    *,
    turn_state: Mapping[str, Any] | None,
    active_round: Mapping[str, Any] | None,
) -> bool:
    if not active_round:
        return False
    round_state = str((active_round or {}).get("state") or "")
    if round_state not in {"VERIFY_PENDING", "VERIFYING", "RECEIPT_PENDING"}:
        return False

    turn_state_name = canonical_turn_state_name(
        (turn_state or {}).get("state"),
        legacy_state=(turn_state or {}).get("legacy_state"),
    )
    if turn_state_name in TURN_STATES_WITHOUT_VERIFY_SURFACE:
        return True

    turn_reason = str((turn_state or {}).get("reason") or "")
    return turn_state_name == TURN_STATE_IDLE and turn_reason == "operator_request_gated_hibernate"
