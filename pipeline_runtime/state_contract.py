from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping

from .lane_catalog import default_role_bindings


RUNTIME_SNAPSHOT_CONTRACT_VERSION = "2026-05-20.runtime_snapshot_v1"

INACTIVE_RUNTIME_STATES = frozenset({"STOPPED", "STOPPING", "BROKEN"})
UNCERTAIN_RUNTIME_REASONS = frozenset(
    {
        "supervisor_missing_recent_ambiguous",
        "supervisor_missing_snapshot_undated",
    }
)
TERMINAL_TURN_STATES = frozenset({"", "IDLE", "CLOSED", "DONE"})
ACTIVE_ROUND_ROLE_BY_STATE = {
    "VERIFY_PENDING": "verify",
    "VERIFYING": "verify",
    "RECEIPT_PENDING": "verify",
}


class ControlState(str, Enum):
    NONE = "none"
    IMPLEMENT = "implement"
    ADVISORY_REQUEST = "request_open"
    ADVISORY_ADVICE = "advice_ready"
    NEEDS_OPERATOR = "needs_operator"
    UNCERTAIN = "uncertain"


class RoundState(str, Enum):
    IDLE = "IDLE"
    DISCOVERED = "DISCOVERED"
    STABILIZING = "STABILIZING"
    VERIFY_PENDING = "VERIFY_PENDING"
    VERIFYING = "VERIFYING"
    RECEIPT_PENDING = "RECEIPT_PENDING"
    CLOSED = "CLOSED"
    UNCERTAIN = "uncertain"


class LaneLifecycle(str, Enum):
    OFF = "off"
    BOOTING = "booting"
    READY = "ready"
    DISPATCH_SEEN = "dispatch_seen"
    ACCEPTED = "accepted"
    DONE = "done"
    BROKEN = "broken"
    UNKNOWN = "unknown"


class RuntimeHealth(str, Enum):
    OK = "ok"
    RECOVERING = "recovering"
    ATTENTION = "attention"
    NEEDS_OPERATOR = "needs_operator"


@dataclass(frozen=True)
class QueueSnapshot:
    no_queued_pipeline_task: bool
    status: str
    class_name: str


@dataclass(frozen=True)
class RuntimeSnapshot:
    schema_version: int
    contract_version: str
    runtime_state: str
    show_live: bool
    control_state: str
    round_state: str
    active_lane: str
    health: dict[str, Any]
    queue: QueueSnapshot
    lanes: list[dict[str, Any]]
    invariants: dict[str, Any]


def _clean(value: object) -> str:
    return str(value or "").strip()


def _number(value: object, default: int = -1) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _current_turn_state(status: Mapping[str, Any]) -> Mapping[str, Any]:
    turn_state = _mapping(status.get("turn_state"))
    if turn_state:
        return turn_state
    compat = _mapping(status.get("compat"))
    compat_turn = _mapping(compat.get("turn_state"))
    return compat_turn


def _live_round_state(status: Mapping[str, Any], turn_state: Mapping[str, Any]) -> str:
    active_round = _mapping(status.get("active_round"))
    round_state = _clean(active_round.get("state")).upper()
    turn_name = _clean(turn_state.get("state")).upper()
    if round_state and round_state != RoundState.IDLE.value:
        return round_state
    return turn_name or round_state or RoundState.IDLE.value


def _control_status(status: Mapping[str, Any], *, show_live: bool, uncertain: bool) -> str:
    if not show_live:
        return ControlState.UNCERTAIN.value if uncertain else ControlState.NONE.value
    control = _mapping(status.get("control"))
    return _clean(control.get("active_control_status")) or ControlState.NONE.value


def _compat_active_control(status: Mapping[str, Any]) -> Mapping[str, Any]:
    compat = _mapping(status.get("compat"))
    slots = _mapping(compat.get("control_slots"))
    return _mapping(slots.get("active"))


def _active_control_present(status: Mapping[str, Any], control_status: str) -> bool:
    control = _mapping(status.get("control"))
    control_file = _clean(control.get("active_control_file"))
    control_seq = _number(control.get("active_control_seq"))
    return bool(control_file or control_seq >= 0 or control_status not in {"", ControlState.NONE.value})


def _compat_control_present(status: Mapping[str, Any]) -> bool:
    active = _compat_active_control(status)
    if not active:
        return False
    status_value = _clean(active.get("status"))
    seq = _number(active.get("control_seq"))
    filename = _clean(active.get("file"))
    return bool(status_value or filename or seq >= 0)


def _compat_operator_candidate_is_suppressed(
    status: Mapping[str, Any],
    *,
    automation_health: str,
    control_status: str,
) -> bool:
    active = _compat_active_control(status)
    filename = _clean(active.get("file")).rsplit("/", 1)[-1]
    active_status = _clean(active.get("status"))
    automation_next_action = _clean(status.get("automation_next_action")) or "continue"
    control = _mapping(status.get("control"))
    control_file = _clean(control.get("active_control_file"))
    control_seq = _number(control.get("active_control_seq"))
    return (
        control_status == ControlState.NONE.value
        and automation_health == RuntimeHealth.OK.value
        and automation_next_action == "continue"
        and not _clean(status.get("automation_reason_code"))
        and not control_file
        and control_seq < 0
        and filename == "operator_request.md"
        and active_status == ControlState.NEEDS_OPERATOR.value
    )


def _control_label(status: Mapping[str, Any], control_status: str) -> str:
    control = _mapping(status.get("control"))
    control_seq = _number(control.get("active_control_seq"))
    if control_status and control_status != ControlState.NONE.value:
        suffix = f" #{control_seq}" if control_seq >= 0 else ""
        return f"{control_status}{suffix}"
    active = _compat_active_control(status)
    compat_status = _clean(active.get("status"))
    compat_seq = _number(active.get("control_seq"))
    if compat_status:
        suffix = f" #{compat_seq}" if compat_seq >= 0 else ""
        return f"{compat_status}{suffix}"
    return ""


def _control_class(control_status: str) -> str:
    if control_status == ControlState.NEEDS_OPERATOR.value:
        return "warn"
    return "neutral"


def _runtime_uncertain(runtime_state: str, degraded_reasons: list[str]) -> bool:
    return runtime_state == "DEGRADED" and any(
        reason in UNCERTAIN_RUNTIME_REASONS for reason in degraded_reasons
    )


def _suppressed_operator_candidate(
    status: Mapping[str, Any],
    *,
    automation_health: str,
    control_status: str,
) -> bool:
    autonomy = _mapping(status.get("autonomy"))
    gated_autonomy_candidate = (
        control_status == ControlState.NONE.value
        and automation_health == RuntimeHealth.OK.value
        and autonomy.get("operator_eligible") is False
        and _clean(autonomy.get("mode")) == "hibernate"
    )
    return gated_autonomy_candidate or _compat_operator_candidate_is_suppressed(
        status,
        automation_health=automation_health,
        control_status=control_status,
    )


def _queue_snapshot(
    status: Mapping[str, Any],
    *,
    show_live: bool,
    control_status: str,
    round_state: str,
    automation_health: str,
    violations: list[str],
) -> QueueSnapshot:
    active_round = status.get("active_round")
    control = _mapping(status.get("control"))
    control_file = _clean(control.get("active_control_file"))
    control_seq = _number(control.get("active_control_seq"))
    top_level_control_present = _active_control_present(status, control_status)
    suppressed_compat_operator_candidate = _compat_operator_candidate_is_suppressed(
        status,
        automation_health=automation_health,
        control_status=control_status,
    )
    compat_control_present = _compat_control_present(status) and not suppressed_compat_operator_candidate
    no_queued = bool(
        show_live
        and control_status == ControlState.NONE.value
        and automation_health == RuntimeHealth.OK.value
        and not _clean(status.get("automation_reason_code"))
        and not bool(status.get("stale_advisory_pending"))
        and not control_file
        and control_seq < 0
        and not active_round
        and not compat_control_present
    )
    if (
        show_live
        and control_status == ControlState.NONE.value
        and not top_level_control_present
        and compat_control_present
    ):
        violations.append("active_control_slot_not_surfaced")

    if no_queued:
        return QueueSnapshot(True, "No queued pipeline task", "ok")
    if not show_live:
        return QueueSnapshot(False, "Runtime inactive", "dim")
    if automation_health and automation_health != RuntimeHealth.OK.value:
        return QueueSnapshot(False, automation_health, "warn")
    if top_level_control_present or compat_control_present:
        label = _control_label(status, control_status) or "control_pending"
        return QueueSnapshot(False, label, _control_class(control_status))
    if round_state and round_state not in {RoundState.IDLE.value, RoundState.UNCERTAIN.value}:
        return QueueSnapshot(False, round_state, "neutral")
    return QueueSnapshot(False, "No active control", "dim")


def _role_owners(status: Mapping[str, Any]) -> Mapping[str, str]:
    raw = _mapping(status.get("role_owners"))
    if raw:
        return {str(key): str(value) for key, value in raw.items()}
    return default_role_bindings()


def _active_lane(status: Mapping[str, Any], round_state: str, turn_state: Mapping[str, Any]) -> str:
    lane = _clean(turn_state.get("active_lane"))
    role = _clean(turn_state.get("active_role")).lower()
    turn_name = _clean(turn_state.get("state")).upper()
    owners = _role_owners(status)
    if lane and role and turn_name not in TERMINAL_TURN_STATES:
        return lane
    round_role = ACTIVE_ROUND_ROLE_BY_STATE.get(round_state, "")
    return _clean(owners.get(round_role)) if round_role else ""


def _lane_lifecycle(lane: Mapping[str, Any]) -> str:
    state = _clean(lane.get("state")).lower()
    note = _clean(lane.get("note")).lower()
    if state == "working":
        if note.startswith("dispatch_seen"):
            return LaneLifecycle.DISPATCH_SEEN.value
        return LaneLifecycle.ACCEPTED.value
    if state == "ready" and note == "waiting_next_control":
        return LaneLifecycle.DONE.value
    if state in {item.value for item in LaneLifecycle}:
        return state
    if not state:
        return LaneLifecycle.UNKNOWN.value
    return LaneLifecycle.UNKNOWN.value


def _lane_snapshots(status: Mapping[str, Any], active_lane: str) -> list[dict[str, Any]]:
    lanes: list[dict[str, Any]] = []
    for lane in _list(status.get("lanes")):
        if not isinstance(lane, Mapping):
            continue
        name = _clean(lane.get("name"))
        lanes.append(
            {
                "name": name,
                "lifecycle": _lane_lifecycle(lane),
                "active": bool(name and name == active_lane),
                "note": _clean(lane.get("note")),
                "pid": lane.get("pid"),
                "attachable": bool(lane.get("attachable")),
            }
        )
    return lanes


def _extract_autonomy_section(status: Mapping[str, Any]) -> dict[str, Any]:
    runtime_state = (_clean(status.get("runtime_state")) or "STOPPED").upper()
    degraded_reasons = [
        _clean(item)
        for item in _list(status.get("degraded_reasons"))
        if _clean(item)
    ]
    degraded_reason = _clean(status.get("degraded_reason"))
    if degraded_reason and degraded_reason not in degraded_reasons:
        degraded_reasons.insert(0, degraded_reason)
    uncertain = _runtime_uncertain(runtime_state, degraded_reasons)
    show_live = runtime_state not in INACTIVE_RUNTIME_STATES and not uncertain
    automation_health = _clean(status.get("automation_health")) or RuntimeHealth.OK.value
    if automation_health not in {item.value for item in RuntimeHealth}:
        automation_health = RuntimeHealth.ATTENTION.value
    return {
        "runtime_state": runtime_state,
        "degraded_reasons": degraded_reasons,
        "uncertain": uncertain,
        "show_live": show_live,
        "automation_health": automation_health,
        "health": {
            "state": automation_health,
            "reason_code": _clean(status.get("automation_reason_code")),
            "incident_family": _clean(status.get("automation_incident_family")),
            "next_action": _clean(status.get("automation_next_action")) or "continue",
        },
    }


def _extract_control_section(
    status: Mapping[str, Any],
    *,
    show_live: bool,
    uncertain: bool,
) -> dict[str, Any]:
    return {
        "control_status": _control_status(
            status,
            show_live=show_live,
            uncertain=uncertain,
        )
    }


def _extract_round_section(
    status: Mapping[str, Any],
    *,
    show_live: bool,
    uncertain: bool,
) -> dict[str, Any]:
    turn_state = _current_turn_state(status)
    round_state = _live_round_state(status, turn_state) if show_live else (
        RoundState.UNCERTAIN.value if uncertain else RoundState.IDLE.value
    )
    return {"turn_state": turn_state, "round_state": round_state}


def _extract_lane_summary(
    status: Mapping[str, Any],
    *,
    round_state: str,
    turn_state: Mapping[str, Any],
) -> dict[str, Any]:
    active_lane = _active_lane(status, round_state, turn_state)
    return {
        "active_lane": active_lane,
        "lanes": _lane_snapshots(status, active_lane),
    }


def _extract_queue_section(
    status: Mapping[str, Any],
    *,
    show_live: bool,
    control_status: str,
    round_state: str,
    automation_health: str,
) -> dict[str, Any]:
    violations: list[str] = []
    queue = _queue_snapshot(
        status,
        show_live=show_live,
        control_status=control_status,
        round_state=round_state,
        automation_health=automation_health,
        violations=violations,
    )
    if (
        show_live
        and queue.no_queued_pipeline_task
        and _compat_control_present(status)
        and not _compat_operator_candidate_is_suppressed(
            status,
            automation_health=automation_health,
            control_status=control_status,
        )
    ):
        violations.append("no_queue_with_active_control_slot")
    return {"queue": queue, "violations": sorted(set(violations))}


def _extract_runtime_sections(status: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    autonomy = _extract_autonomy_section(status)
    control = _extract_control_section(
        status,
        show_live=bool(autonomy["show_live"]),
        uncertain=bool(autonomy["uncertain"]),
    )
    round_section = _extract_round_section(
        status,
        show_live=bool(autonomy["show_live"]),
        uncertain=bool(autonomy["uncertain"]),
    )
    lane_summary = _extract_lane_summary(
        status,
        round_state=str(round_section["round_state"]),
        turn_state=_mapping(round_section["turn_state"]),
    )
    queue_section = _extract_queue_section(
        status,
        show_live=bool(autonomy["show_live"]),
        control_status=str(control["control_status"]),
        round_state=str(round_section["round_state"]),
        automation_health=str(autonomy["automation_health"]),
    )
    return {
        "autonomy": autonomy,
        "control": control,
        "round": round_section,
        "lane": lane_summary,
        "queue": queue_section,
    }


def _runtime_snapshot_from_sections(sections: Mapping[str, dict[str, Any]]) -> RuntimeSnapshot:
    autonomy = sections["autonomy"]
    control = sections["control"]
    round_section = sections["round"]
    lane_summary = sections["lane"]
    queue_section = sections["queue"]
    return RuntimeSnapshot(
        schema_version=1,
        contract_version=RUNTIME_SNAPSHOT_CONTRACT_VERSION,
        runtime_state=str(autonomy["runtime_state"]),
        show_live=bool(autonomy["show_live"]),
        control_state=str(control["control_status"]),
        round_state=str(round_section["round_state"]),
        active_lane=str(lane_summary["active_lane"]),
        health=dict(autonomy["health"]),
        queue=queue_section["queue"],
        lanes=list(lane_summary["lanes"]),
        invariants={"violations": list(queue_section["violations"])},
    )


def reduce_runtime_snapshot(status: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build the single consumer-facing runtime snapshot from legacy status fields."""
    payload = status if isinstance(status, Mapping) else {}
    sections = _extract_runtime_sections(payload)
    data = asdict(_runtime_snapshot_from_sections(sections))
    data["suppressed_operator_candidate"] = _suppressed_operator_candidate(
        payload,
        automation_health=str(sections["autonomy"]["automation_health"]),
        control_status=str(sections["control"]["control_status"]),
    )
    return data
