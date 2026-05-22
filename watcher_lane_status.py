from __future__ import annotations

from collections.abc import Mapping, Sequence

from pipeline_runtime.lane_catalog import physical_lane_order


def build_lane_statuses(
    *,
    heartbeat_iso: str,
    active_lane: str,
    implement_lane: str,
    implement_live: bool,
    lane_configs: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    lane_statuses: list[dict[str, object]] = []
    active_lane_name = str(active_lane or "").strip()
    implement_lane_name = str(implement_lane or "").strip()
    seen_names: set[str] = set()

    for lane in lane_configs:
        name = str(lane.get("name") or "").strip()
        if not name:
            continue
        seen_names.add(name)
        enabled = bool(lane.get("enabled", True))
        state = "OFF"
        if enabled:
            state = (
                "WORKING"
                if name == active_lane_name or (implement_live and name == implement_lane_name)
                else "READY"
            )
        lane_statuses.append(
            {
                "name": name,
                "state": state,
                "attachable": enabled,
                "last_heartbeat_at": heartbeat_iso if enabled else "",
            }
        )

    for fallback_name in physical_lane_order():
        if fallback_name in seen_names:
            continue
        lane_statuses.append(
            {
                "name": fallback_name,
                "state": (
                    "WORKING"
                    if fallback_name == active_lane_name
                    or (implement_live and fallback_name == implement_lane_name)
                    else "READY"
                ),
                "attachable": True,
                "last_heartbeat_at": heartbeat_iso,
            }
        )
    return lane_statuses


__all__ = ["build_lane_statuses"]
