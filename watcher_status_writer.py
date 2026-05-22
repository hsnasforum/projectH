from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from pipeline_runtime.automation_health import derive_automation_health
from pipeline_runtime.schema import (
    active_control_snapshot_from_entry,
    active_control_snapshot_from_status,
    control_block_from_snapshot,
)


class ActiveControlLike(Protocol):
    path: Path
    status: str
    mtime: float
    control_seq: int
    slot_id: str
    canonical_file: str
    is_legacy_alias: bool


def _control_snapshot(
    *,
    active_control: ActiveControlLike | None,
    fallback_active_control_file: str,
    fallback_active_control_seq: int,
) -> tuple[Mapping[str, Any], bool]:
    if active_control is not None:
        return (
            active_control_snapshot_from_entry(
                {
                    "file": Path(str(active_control.path)).name,
                    "control_seq": active_control.control_seq,
                    "status": active_control.status,
                    "mtime": active_control.mtime,
                    "slot_id": active_control.slot_id,
                    "canonical_file": active_control.canonical_file,
                }
            ),
            active_control.is_legacy_alias,
        )
    if fallback_active_control_file:
        return (
            active_control_snapshot_from_status(
                {
                    "active_control_file": f".pipeline/{fallback_active_control_file}",
                    "active_control_seq": fallback_active_control_seq,
                }
            ),
            False,
        )
    return {}, False


def build_runtime_status_payload(
    *,
    run_id: str,
    turn_state: str,
    legacy_turn_state: str,
    runtime_controls: Mapping[str, object],
    active_control: ActiveControlLike | None,
    fallback_active_control_file: str,
    fallback_active_control_seq: int,
    control_seq_age_cycles: int,
    lane_statuses: Sequence[Mapping[str, object]],
    heartbeat_iso: str,
) -> dict[str, object]:
    control_snapshot, control_is_legacy_alias = _control_snapshot(
        active_control=active_control,
        fallback_active_control_file=fallback_active_control_file,
        fallback_active_control_seq=fallback_active_control_seq,
    )
    data: dict[str, object] = {
        "schema_version": 1,
        "run_id": run_id,
        "state": "RUNNING",
        "runtime_state": "RUNNING",
        "turn_state": turn_state,
        "legacy_turn_state": legacy_turn_state,
        "degraded_reason": "",
        "runtime_controls": dict(runtime_controls),
        "control": control_block_from_snapshot(
            control_snapshot,
            control_age_cycles=control_seq_age_cycles,
            is_legacy_alias=control_is_legacy_alias,
        ),
        "control_age_cycles": control_seq_age_cycles,
        "lanes": [dict(lane) for lane in lane_statuses],
        "last_receipt_id": "",
        "last_heartbeat_at": heartbeat_iso,
        "updated_at": heartbeat_iso,
    }
    data.update(derive_automation_health(data))
    return data


def write_runtime_status(
    *,
    enabled: bool,
    run_status_path: Path,
    run_id: str,
    turn_state: str,
    legacy_turn_state: str,
    runtime_controls: Mapping[str, object],
    active_control: ActiveControlLike | None,
    fallback_active_control_file: str,
    fallback_active_control_seq: int,
    control_seq_age_cycles: int,
    lane_statuses: Sequence[Mapping[str, object]],
    heartbeat_iso: str,
    write_current_run_pointer: Callable[[], None],
) -> dict[str, object] | None:
    if not enabled:
        return None

    data = build_runtime_status_payload(
        run_id=run_id,
        turn_state=turn_state,
        legacy_turn_state=legacy_turn_state,
        runtime_controls=runtime_controls,
        active_control=active_control,
        fallback_active_control_file=fallback_active_control_file,
        fallback_active_control_seq=fallback_active_control_seq,
        control_seq_age_cycles=control_seq_age_cycles,
        lane_statuses=lane_statuses,
        heartbeat_iso=heartbeat_iso,
    )
    tmp_path = run_status_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(run_status_path)
    write_current_run_pointer()
    return data


__all__ = ["build_runtime_status_payload", "write_runtime_status"]
