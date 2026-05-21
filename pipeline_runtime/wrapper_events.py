from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import append_jsonl, iso_utc, parse_iso_utc

WRAPPER_EVENT_SCHEMA_VERSION = "1"

ALL_EVENT_TYPES = frozenset({
    "READY",
    "HEARTBEAT",
    "DISPATCH_SEEN",
    "TASK_ACCEPTED",
    "TASK_DONE",
    "BRIDGE_DIAGNOSTIC",
    "BROKEN",
})

TASK_EVENT_TYPES = frozenset({
    "DISPATCH_SEEN",
    "TASK_ACCEPTED",
    "TASK_DONE",
    "BRIDGE_DIAGNOSTIC",
})

_WRAPPER_EVENT_REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    "READY": frozenset(),
    "HEARTBEAT": frozenset({"pid"}),
    "DISPATCH_SEEN": frozenset({"job_id", "dispatch_id", "control_seq", "attempt"}),
    "TASK_ACCEPTED": frozenset({"job_id", "dispatch_id", "control_seq", "attempt"}),
    "TASK_DONE": frozenset({"job_id", "dispatch_id", "control_seq"}),
    "BRIDGE_DIAGNOSTIC": frozenset({"job_id", "dispatch_id", "control_seq", "code"}),
    "BROKEN": frozenset(),
}

_WRAPPER_EVENT_REQUIRED_FIELD_ORDER: dict[str, tuple[str, ...]] = {
    "HEARTBEAT": ("pid",),
    "DISPATCH_SEEN": ("job_id", "dispatch_id", "control_seq", "attempt"),
    "TASK_ACCEPTED": ("job_id", "dispatch_id", "control_seq", "attempt"),
    "TASK_DONE": ("job_id", "dispatch_id", "control_seq"),
    "BRIDGE_DIAGNOSTIC": ("job_id", "dispatch_id", "control_seq", "code"),
}


def lane_event_path(wrapper_events_dir: Path, lane_name: str) -> Path:
    return wrapper_events_dir / f"{lane_name.strip().lower()}.jsonl"


def validate_wrapper_event_payload(
    event_type: str,
    payload: dict[str, Any],
) -> list[str]:
    """Return missing required wrapper-event payload fields."""
    required = _WRAPPER_EVENT_REQUIRED_FIELDS.get(event_type)
    if required is None:
        return []
    ordered_fields = _WRAPPER_EVENT_REQUIRED_FIELD_ORDER.get(event_type, ())
    missing = [field for field in ordered_fields if field in required and field not in payload]
    remaining = sorted(field for field in required if field not in payload and field not in ordered_fields)
    return [*missing, *remaining]


def append_wrapper_event(
    wrapper_events_dir: Path,
    lane_name: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    source: str,
    derived_from: str = "",
) -> None:
    entry = {
        "ts": iso_utc(),
        "lane": lane_name,
        "event_type": event_type,
        "schema_version": WRAPPER_EVENT_SCHEMA_VERSION,
        "source": source,
        "payload": payload,
    }
    missing_fields = validate_wrapper_event_payload(event_type, payload)
    if missing_fields:
        entry["_schema_warnings"] = missing_fields
    if derived_from:
        entry["derived_from"] = derived_from
    append_jsonl(
        lane_event_path(wrapper_events_dir, lane_name),
        entry,
    )


def latest_wrapper_events(wrapper_events_dir: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    if not wrapper_events_dir.exists():
        return latest
    for path in wrapper_events_dir.glob("*.jsonl"):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for raw in reversed(lines):
            if not raw.strip():
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                lane = str(data.get("lane") or path.stem.capitalize())
                latest[lane] = data
                break
    return latest


def read_wrapper_state(wrapper_events_dir: Path, lane_name: str) -> dict[str, Any] | None:
    path = lane_event_path(wrapper_events_dir, lane_name)
    if not path.exists():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for raw in reversed(lines):
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return None


def _load_lane_events(path: Path) -> list[dict[str, Any]]:
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    events: list[dict[str, Any]] = []
    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            events.append(data)
    return events


def iter_wrapper_task_events(wrapper_events_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not wrapper_events_dir.exists():
        return events
    for path in sorted(wrapper_events_dir.glob("*.jsonl")):
        for event in _load_lane_events(path):
            event_type = str(event.get("event_type") or "")
            if event_type in TASK_EVENT_TYPES:
                lane = str(event.get("lane") or path.stem.capitalize())
                events.append({**event, "lane": lane})
    return events


def build_lane_read_models(
    wrapper_events_dir: Path,
    *,
    heartbeat_timeout_sec: float = 15.0,
    now_ts: float | None = None,
) -> dict[str, dict[str, Any]]:
    now_value = float(now_ts) if now_ts is not None else parse_iso_utc(iso_utc())
    models: dict[str, dict[str, Any]] = {}
    if not wrapper_events_dir.exists():
        return models

    for path in wrapper_events_dir.glob("*.jsonl"):
        lane_name = path.stem.capitalize()
        model: dict[str, Any] = {
            "lane": lane_name,
            "state": "",
            "note": "",
            "last_event_at": "",
            "last_event_ts": 0.0,
            "last_heartbeat_at": "",
            "last_heartbeat_ts": 0.0,
            "seen_task": None,
            "accepted_task": None,
            "done_task": None,
            "done_at": "",
            "done_ts": 0.0,
            "bridge_diagnostic": None,
            "derived_from": "",
        }
        for event in _load_lane_events(path):
            lane_name = str(event.get("lane") or lane_name)
            event_type = str(event.get("event_type") or "")
            payload = dict(event.get("payload") or {})
            ts = str(event.get("ts") or "")
            parsed_ts = parse_iso_utc(ts)
            model["lane"] = lane_name
            model["last_event_at"] = ts
            model["last_event_ts"] = parsed_ts
            model["derived_from"] = str(event.get("derived_from") or "")
            if event_type == "READY":
                model["state"] = "READY"
                model["note"] = str(payload.get("reason") or "")
            elif event_type == "HEARTBEAT":
                model["last_heartbeat_at"] = ts
                model["last_heartbeat_ts"] = parsed_ts
            elif event_type == "DISPATCH_SEEN":
                model["done_task"] = None
                model["done_at"] = ""
                model["done_ts"] = 0.0
                model["seen_task"] = {
                    "job_id": str(payload.get("job_id") or ""),
                    "control_seq": int(payload.get("control_seq") or -1),
                    "attempt": int(payload.get("attempt") or 0),
                    "dispatch_id": str(payload.get("dispatch_id") or ""),
                }
                if str(model.get("state") or "") != "WORKING":
                    model["note"] = (
                        f"dispatch_seen seq {model['seen_task']['control_seq']}"
                        if model["seen_task"]["control_seq"] >= 0
                        else "dispatch_seen"
                    )
            elif event_type == "TASK_ACCEPTED":
                model["state"] = "WORKING"
                model["done_task"] = None
                model["done_at"] = ""
                model["done_ts"] = 0.0
                model["seen_task"] = {
                    "job_id": str(payload.get("job_id") or ""),
                    "control_seq": int(payload.get("control_seq") or -1),
                    "attempt": int(payload.get("attempt") or 0),
                    "dispatch_id": str(payload.get("dispatch_id") or ""),
                }
                model["accepted_task"] = {
                    "job_id": str(payload.get("job_id") or ""),
                    "control_seq": int(payload.get("control_seq") or -1),
                    "attempt": int(payload.get("attempt") or 0),
                    "dispatch_id": str(payload.get("dispatch_id") or ""),
                }
                model["note"] = (
                    f"seq {model['accepted_task']['control_seq']}"
                    if model["accepted_task"]["control_seq"] >= 0
                    else ""
                )
            elif event_type == "TASK_DONE":
                model["state"] = "READY"
                model["seen_task"] = None
                model["accepted_task"] = None
                model["done_task"] = {
                    "job_id": str(payload.get("job_id") or ""),
                    "control_seq": int(payload.get("control_seq") or -1),
                    "dispatch_id": str(payload.get("dispatch_id") or ""),
                    "reason": str(payload.get("reason") or ""),
                }
                model["done_at"] = ts
                model["done_ts"] = parsed_ts
                reason = str(payload.get("reason") or "")
                model["note"] = "waiting_next_control" if reason == "duplicate_handoff" else ""
            elif event_type == "BRIDGE_DIAGNOSTIC":
                model["bridge_diagnostic"] = {
                    "code": str(payload.get("code") or ""),
                    "detail": str(payload.get("detail") or ""),
                    "job_id": str(payload.get("job_id") or ""),
                    "dispatch_id": str(payload.get("dispatch_id") or ""),
                    "control_seq": int(payload.get("control_seq") or -1),
                }
                if str(model.get("state") or "") != "WORKING":
                    model["note"] = str(payload.get("code") or "bridge_diagnostic")
            elif event_type == "BROKEN":
                model["state"] = "BROKEN"
                model["note"] = str(payload.get("reason") or "")

        if not str(model.get("state") or "") and str(model.get("last_event_at") or ""):
            model["state"] = "BOOTING"
        last_hb_ts = float(model.get("last_heartbeat_ts") or 0.0)
        if str(model.get("state") or "") in {"READY", "WORKING"} and last_hb_ts:
            if (now_value - last_hb_ts) > heartbeat_timeout_sec:
                model["state"] = "BROKEN"
                model["note"] = "heartbeat_timeout"
        models[str(model.get("lane") or lane_name)] = model
    return models
