from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


TURN_OPERATOR = "operator"
TURN_GEMINI = "gemini"
TURN_CODEX_FOLLOWUP = "codex_followup"
TURN_CODEX_VERIFY = "codex"
TURN_CLAUDE = "claude"
TURN_IDLE = "idle"

TURN_STATES_WITHOUT_VERIFY_SURFACE = frozenset(
    {
        "CODEX_FOLLOWUP",
        "GEMINI_ADVISORY",
        "OPERATOR_WAIT",
    }
)

VERIFY_ROUND_STATES = frozenset({"VERIFY_PENDING", "VERIFYING"})


@dataclass(frozen=True)
class WatcherTurnInputs:
    operator_request_active: bool
    gemini_request_active: bool
    gemini_advice_active: bool
    claude_handoff_active: bool
    latest_work_needs_verify: bool
    claude_handoff_verify_active: bool
    idle_release_cooldown_active: bool
    operator_recovery_marker: Mapping[str, Any] | None = None
    operator_gate_marker: Mapping[str, Any] | None = None


def resolve_watcher_turn(inputs: WatcherTurnInputs) -> str:
    operator_recovery = inputs.operator_recovery_marker
    operator_gate = inputs.operator_gate_marker

    if (
        inputs.operator_request_active
        and operator_recovery is None
        and operator_gate is None
    ):
        return TURN_OPERATOR

    if inputs.gemini_request_active:
        return TURN_GEMINI

    if inputs.gemini_advice_active:
        return TURN_CODEX_FOLLOWUP

    if inputs.claude_handoff_active and (
        inputs.latest_work_needs_verify or inputs.claude_handoff_verify_active
    ):
        return TURN_CODEX_VERIFY

    if inputs.latest_work_needs_verify:
        return TURN_CODEX_VERIFY

    if inputs.claude_handoff_active and not inputs.idle_release_cooldown_active:
        return TURN_CLAUDE

    if operator_recovery is not None:
        return TURN_CODEX_FOLLOWUP

    if (
        operator_gate is not None
        and str(operator_gate.get("routed_to") or "") != "hibernate"
    ):
        return TURN_CODEX_FOLLOWUP

    return TURN_IDLE


def active_lane_for_runtime(
    turn_state: Mapping[str, Any] | None,
    active_round: Mapping[str, Any] | None,
    *,
    control: Mapping[str, Any] | None = None,
    last_receipt: Mapping[str, Any] | None = None,
    duplicate_control: Mapping[str, Any] | None = None,
    stale_operator_control: Mapping[str, Any] | None = None,
    implement_owner: str = "Claude",
    verify_owner: str = "Codex",
    advisory_owner: str = "Gemini",
) -> str:
    state = str((turn_state or {}).get("state") or "")
    round_state = str((active_round or {}).get("state") or "")
    completion_stage = str((active_round or {}).get("completion_stage") or "")
    control = control or {}
    control_status = str(control.get("active_control_status") or "")
    control_seq = int(control.get("active_control_seq") or -1)
    last_receipt_seq = int((last_receipt or {}).get("control_seq") or -1)

    if (
        state == "CLAUDE_ACTIVE"
        and control_status == "implement"
        and control_seq >= 0
        and duplicate_control is None
        and control_seq > last_receipt_seq
    ):
        return implement_owner

    if state in {"CODEX_VERIFY", "CODEX_FOLLOWUP"}:
        return verify_owner

    if state == "GEMINI_ADVISORY":
        return advisory_owner

    if state == "OPERATOR_WAIT" and stale_operator_control is None:
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

    turn_state_name = str((turn_state or {}).get("state") or "")
    if turn_state_name in TURN_STATES_WITHOUT_VERIFY_SURFACE:
        return True

    turn_reason = str((turn_state or {}).get("reason") or "")
    return turn_state_name == "IDLE" and turn_reason == "operator_request_gated_hibernate"
