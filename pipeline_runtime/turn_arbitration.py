from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .role_routes import (
    VERIFY_FOLLOWUP_ROUTE,
    VERIFY_FOLLOWUP_ROUTE_ALIASES,
    is_verify_followup_route,
)
from .schema import active_control_snapshot_from_status, control_seq_value, snapshot_control_seq

TURN_IMPLEMENT = "implement"
TURN_VERIFY = "verify"
TURN_VERIFY_FOLLOWUP = "verify_followup"
TURN_OPERATOR = "operator"
TURN_ADVISORY = "advisory"
TURN_IDLE = "idle"

LEGACY_WATCHER_TURN_BY_CANONICAL = {
    TURN_IMPLEMENT: "claude",
    TURN_VERIFY: "codex",
    TURN_VERIFY_FOLLOWUP: VERIFY_FOLLOWUP_ROUTE,
    TURN_ADVISORY: "gemini",
    TURN_OPERATOR: "operator",
    TURN_IDLE: "idle",
}

LEGACY_WATCHER_TURN_ALIASES = {
    alias: TURN_VERIFY_FOLLOWUP for alias in VERIFY_FOLLOWUP_ROUTE_ALIASES
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
ACTIVE_ROUND_RECEIPT_STATES = frozenset({"RECEIPT_PENDING"})
ACTIVE_ROUND_SURFACE_STATES = VERIFY_ROUND_STATES | ACTIVE_ROUND_RECEIPT_STATES


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


@dataclass(frozen=True)
class VerifyRoundTaskHint:
    active: bool
    job_id: str = ""
    dispatch_id: str = ""
    control_seq: int = -1


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


def active_round_dispatch_control_seq(active_round: Mapping[str, Any] | None) -> int:
    value = control_seq_value((active_round or {}).get("dispatch_control_seq"), default=-1)
    return value if isinstance(value, int) else -1


def active_round_artifact_path(active_round: Mapping[str, Any] | None) -> str:
    return str((active_round or {}).get("artifact_path") or "").replace("\\", "/").lstrip("./").strip()


def active_round_matches_job(
    job_state: Mapping[str, Any] | None,
    active_round: Mapping[str, Any] | None,
) -> bool:
    if not job_state or not active_round:
        return False
    return (
        str(job_state.get("job_id") or "") == str(active_round.get("job_id") or "")
        and int(job_state.get("round") or 0) == int(active_round.get("round") or 0)
    )


def active_round_matches_artifact_path(
    active_round: Mapping[str, Any] | None,
    work_path: object,
    *,
    normalize_path: Callable[[object], str] | None = None,
) -> bool:
    if not active_round:
        return False
    normalized_round = (
        normalize_path(active_round.get("artifact_path"))
        if normalize_path is not None
        else active_round_artifact_path(active_round)
    )
    normalized_work = (
        normalize_path(work_path)
        if normalize_path is not None
        else str(work_path or "").replace("\\", "/").lstrip("./").strip()
    )
    if not normalized_round or not normalized_work or normalized_work == "—":
        return False
    return normalized_round == normalized_work or normalized_round.endswith(f"/{normalized_work}")


def _receipt_closes_latest(
    data: Mapping[str, Any],
    *,
    last_receipt: Mapping[str, Any] | None,
    receipt_closes_job_round: Callable[[str, int, Mapping[str, Any] | None], bool] | None,
) -> bool:
    job_id = str(data.get("job_id") or "")
    round_number = int(data.get("round") or 0)
    if not job_id or round_number <= 0:
        return False
    if receipt_closes_job_round is not None:
        return receipt_closes_job_round(job_id, round_number, last_receipt)
    return bool(
        last_receipt
        and str(last_receipt.get("job_id") or "") == job_id
        and int(last_receipt.get("round") or -1) == round_number
    )


def build_active_round_snapshot(
    job_states: list[Mapping[str, Any]],
    last_receipt: Mapping[str, Any] | None,
    *,
    active_control: Mapping[str, Any] | None = None,
    receipt_closes_job_round: Callable[[str, int, Mapping[str, Any] | None], bool] | None = None,
) -> dict[str, Any] | None:
    if not job_states:
        return None

    active_control_seq = snapshot_control_seq(
        active_control_snapshot_from_status(dict(active_control or {}))
    )

    def receipt_closes(data: Mapping[str, Any]) -> bool:
        return _receipt_closes_latest(
            data,
            last_receipt=last_receipt,
            receipt_closes_job_round=receipt_closes_job_round,
        )

    def dispatch_control_seq(data: Mapping[str, Any]) -> int:
        value = control_seq_value(data.get("dispatch_control_seq"), default=-1)
        return value if isinstance(value, int) else -1

    def control_seq_rank(data: Mapping[str, Any]) -> int:
        if active_control_seq < 0:
            return 0
        return 1 if dispatch_control_seq(data) == active_control_seq else 0

    def liveness_rank(data: Mapping[str, Any]) -> int:
        status = str(data.get("status") or "")
        if status in {"VERIFY_PENDING", "VERIFY_RUNNING"}:
            return 2
        if status == "VERIFY_DONE" and not receipt_closes(data):
            return 1
        return 0

    latest_job = max(
        job_states,
        key=lambda data: (
            control_seq_rank(data),
            liveness_rank(data),
            float(data.get("updated_at") or 0.0),
            float(data.get("last_activity_at") or 0.0),
            str(data.get("job_id") or ""),
        ),
    )
    job_id = str(latest_job.get("job_id") or "")
    round_number = int(latest_job.get("round") or 0)
    has_receipt = receipt_closes(latest_job)
    status = str(latest_job.get("status") or "")
    round_state = {
        "NEW_ARTIFACT": "DISCOVERED",
        "STABILIZING": "STABILIZING",
        "VERIFY_PENDING": "VERIFY_PENDING",
        "VERIFY_RUNNING": "VERIFYING",
        "VERIFY_DONE": "CLOSED" if has_receipt else "RECEIPT_PENDING",
    }.get(status, status or "IDLE")
    dispatch_id = str(latest_job.get("dispatch_id") or "")
    accepted_dispatch_id = str(latest_job.get("accepted_dispatch_id") or "")
    done_dispatch_id = str(latest_job.get("done_dispatch_id") or "")
    completion_stage = str(latest_job.get("completion_stall_stage") or "")
    if not completion_stage and dispatch_id:
        if done_dispatch_id == dispatch_id:
            completion_stage = "receipt_close_pending"
        elif accepted_dispatch_id == dispatch_id:
            completion_stage = "task_done_pending"
    return {
        "job_id": job_id,
        "round": round_number,
        "state": round_state,
        "artifact_path": str(latest_job.get("artifact_path") or ""),
        "status": status,
        "dispatch_id": dispatch_id,
        "dispatch_control_seq": dispatch_control_seq(latest_job),
        "dispatch_stage": str(latest_job.get("dispatch_stall_stage") or ""),
        "completion_stage": completion_stage,
        "note": str(latest_job.get("lane_note") or ""),
        "degraded_reason": str(latest_job.get("degraded_reason") or ""),
    }


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

    # Operator recovery/gate markers are fallbacks after active advisory,
    # verify, and releasable handoff work has already been given priority.
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


def should_suppress_active_round_after_verified_latest_work(
    *,
    turn_state: Mapping[str, Any] | None,
    active_round: Mapping[str, Any] | None,
    control: Mapping[str, Any] | None,
    artifacts: Mapping[str, Any] | None,
    normalize_path: Callable[[object], str] | None = None,
) -> bool:
    if not active_round:
        return False
    if str((control or {}).get("active_control_status") or "none") != "none":
        return False
    turn_name = canonical_turn_state_name(
        (turn_state or {}).get("state"),
        legacy_state=(turn_state or {}).get("legacy_state"),
    )
    if turn_name != TURN_STATE_IDLE:
        return False
    if str((turn_state or {}).get("reason") or "") not in {"handoff_already_completed", "duplicate_handoff"}:
        return False
    if str(active_round.get("state") or "") not in ACTIVE_ROUND_SURFACE_STATES:
        return False
    latest_work = ((artifacts or {}).get("latest_work") or {}) if isinstance(artifacts, Mapping) else {}
    latest_verify = ((artifacts or {}).get("latest_verify") or {}) if isinstance(artifacts, Mapping) else {}
    work_path = str((latest_work or {}).get("path") or "").strip()
    verify_path = str((latest_verify or {}).get("path") or "").strip()
    if not work_path or work_path == "—" or not verify_path or verify_path == "—":
        return False
    return not active_round_matches_artifact_path(
        active_round,
        work_path,
        normalize_path=normalize_path,
    )


def verify_round_task_hint(
    *,
    active_lane: str,
    active_round: Mapping[str, Any] | None,
    turn_state: Mapping[str, Any] | None,
    verify_owner: str,
) -> VerifyRoundTaskHint:
    active_job_id = str((active_round or {}).get("job_id") or "")
    active_dispatch_id = str((active_round or {}).get("dispatch_id") or "")
    active_round_state = str((active_round or {}).get("state") or "")
    turn_state_name = canonical_turn_state_name(
        (turn_state or {}).get("state"),
        legacy_state=(turn_state or {}).get("legacy_state"),
    )
    active = (
        active_lane == verify_owner
        and bool(active_job_id)
        and bool(active_dispatch_id)
        and active_round_state in VERIFY_ROUND_STATES
        and turn_state_name not in {
            TURN_STATE_VERIFY_FOLLOWUP,
            TURN_STATE_ADVISORY_ACTIVE,
            TURN_STATE_OPERATOR_WAIT,
        }
    )
    if not active:
        return VerifyRoundTaskHint(active=False)
    return VerifyRoundTaskHint(
        active=True,
        job_id=active_job_id,
        dispatch_id=active_dispatch_id,
        control_seq=active_round_dispatch_control_seq(active_round),
    )
