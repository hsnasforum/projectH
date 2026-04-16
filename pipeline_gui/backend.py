"""Runtime-facing backend helpers; legacy tmux/log observers are compat-only wrappers."""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import time
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from pipeline_runtime.schema import parse_iso_utc, read_jsonl_tail
from pipeline_runtime.tmux_adapter import TmuxAdapter

from . import legacy_backend_debug
from .platform import (
    IS_WINDOWS, WSL_DISTRO,
    CREATE_NO_WINDOW, FILE_QUERY_TIMEOUT,
    _wsl_path_str, _windows_to_wsl_mount, _run, _hidden_subprocess_kwargs,
    _normalize_token_runtime_asset_path, _wsl_wrap, resolve_packaged_file, resolve_project_runtime_file,
)
from .formatting import time_ago as time_ago  # noqa: F811 — canonical + re-export
from .project import _session_name_for
from .setup_profile import join_display_resolver_messages, resolve_project_active_profile

DEFAULT_TOKEN_SINCE_DAYS = 7
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_VERIFY_ACTIVE_STATUSES = {"VERIFY_PENDING", "VERIFY_RUNNING"}
_VERIFY_ACTIVITY_LABELS = {
    "VERIFY_PENDING": "Codex 검증 준비 중",
    "VERIFY_RUNNING": "Codex 검증 실행 중",
}
_RUNTIME_STATUS_STALE_AFTER_SEC = 15.0
_STALE_RUNTIME_REASON = "supervisor_missing"
_AMBIGUOUS_RUNTIME_REASON = "supervisor_missing_recent_ambiguous"
_UNDATED_AMBIGUOUS_RUNTIME_REASON = "supervisor_missing_snapshot_undated"


def _read_log_lines(path: Path, *, tail_count: int) -> list[str]:
    return legacy_backend_debug.read_log_lines(
        path,
        tail_count=tail_count,
        is_windows=IS_WINDOWS,
        run=_run,
        wsl_path_str=_wsl_path_str,
        file_query_timeout=FILE_QUERY_TIMEOUT,
    )


def _clean_log_lines(lines: list[str]) -> list[str]:
    return legacy_backend_debug.clean_log_lines(lines)


def _read_json_file(path: Path) -> dict[str, object] | None:
    if IS_WINDOWS:
        code, content = _run(["cat", _wsl_path_str(path)], timeout=FILE_QUERY_TIMEOUT)
        if code != 0 or not content.strip():
            return None
        text = content
    else:
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def normalize_runtime_status(value: object | None) -> dict[str, object]:
    """Coerce runtime status payloads to a dict for UI callers."""
    if isinstance(value, dict):
        return value
    return {}


def _supervisor_pid(project: Path) -> int | None:
    path = project / ".pipeline" / "supervisor.pid"
    if IS_WINDOWS:
        code, content = _run(["cat", _wsl_path_str(path)], timeout=FILE_QUERY_TIMEOUT)
        if code != 0:
            return None
        text = content.strip()
    else:
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            return None
    try:
        return int(text)
    except ValueError:
        return None


def _pid_is_alive(pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    if IS_WINDOWS:
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _runtime_status_age_sec(status: dict[str, object]) -> float | None:
    updated_at = parse_iso_utc(str(status.get("updated_at") or ""))
    if updated_at <= 0:
        return None
    return max(0.0, time.time() - updated_at)


def _coerce_optional_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _lane_status_quiescent(lane: object) -> bool:
    if not isinstance(lane, dict):
        return False
    lane_state = str(lane.get("state") or "").upper()
    if lane_state in {"OFF", "BROKEN", "DEAD"}:
        return True
    lane_pid = _coerce_optional_int(lane.get("pid"))
    if lane_pid is None:
        return False
    return not _pid_is_alive(lane_pid)


def _lane_status_inactive(lane: object) -> bool:
    if not isinstance(lane, dict):
        return False
    return str(lane.get("state") or "").upper() in {"OFF", "BROKEN", "DEAD"}


def _runtime_status_processes_quiescent(status: dict[str, object]) -> bool:
    watcher = dict(status.get("watcher") or {})
    watcher_pid = _coerce_optional_int(watcher.get("pid"))
    watcher_alive_claim = bool(watcher.get("alive"))
    watcher_reported = bool(watcher) and ("alive" in watcher or watcher_pid is not None)
    watcher_quiescent = watcher_reported and (
        (watcher_pid is not None and not _pid_is_alive(watcher_pid))
        or (watcher_pid is None and not watcher_alive_claim)
    )
    lanes = [lane for lane in list(status.get("lanes") or []) if isinstance(lane, dict)]
    return watcher_quiescent and bool(lanes) and all(_lane_status_quiescent(lane) for lane in lanes)


def _runtime_status_fields_quiescent(status: dict[str, object]) -> bool:
    control = dict(status.get("control") or {})
    watcher = dict(status.get("watcher") or {})
    lanes = [lane for lane in list(status.get("lanes") or []) if isinstance(lane, dict)]
    control_inactive = str(control.get("active_control_status") or "none") == "none"
    watcher_inactive = bool(watcher) and not bool(watcher.get("alive"))
    lanes_inactive = bool(lanes) and all(_lane_status_inactive(lane) for lane in lanes)
    return control_inactive and status.get("active_round") is None and watcher_inactive and lanes_inactive


def _runtime_status_claims_activity(status: dict[str, object]) -> bool:
    control = dict(status.get("control") or {})
    watcher = dict(status.get("watcher") or {})
    if str(control.get("active_control_status") or "none") != "none":
        return True
    if status.get("active_round") is not None:
        return True
    if bool(watcher.get("alive")):
        return True
    lanes = [lane for lane in list(status.get("lanes") or []) if isinstance(lane, dict)]
    return any(not _lane_status_inactive(lane) for lane in lanes)


def _runtime_status_live_identity_missing(status: dict[str, object]) -> bool:
    watcher = dict(status.get("watcher") or {})
    watcher_pid = _coerce_optional_int(watcher.get("pid"))
    watcher_has_live_identity = watcher_pid is not None and _pid_is_alive(watcher_pid)
    lanes = [lane for lane in list(status.get("lanes") or []) if isinstance(lane, dict)]
    active_lanes = [lane for lane in lanes if not _lane_status_inactive(lane)]
    active_lane_has_pid = any(_coerce_optional_int(lane.get("pid")) is not None for lane in active_lanes)
    return not watcher_has_live_identity and not active_lane_has_pid


def _runtime_status_ambiguous(status: dict[str, object]) -> bool:
    return _runtime_status_claims_activity(status) and _runtime_status_live_identity_missing(status)


def _clear_inactive_runtime_fields(status: dict[str, object]) -> dict[str, object]:
    result = dict(status)
    control = dict(result.get("control") or {})
    control["active_control_file"] = ""
    control["active_control_seq"] = -1
    control["active_control_status"] = "none"
    control["active_control_updated_at"] = ""
    result["control"] = control
    result["active_round"] = None
    return result


def _mark_runtime_status_stale(status: dict[str, object]) -> dict[str, object]:
    result = _clear_inactive_runtime_fields(status)
    prior_runtime_state = str(status.get("runtime_state") or "").upper()

    if prior_runtime_state == "STOPPING":
        result["runtime_state"] = "STOPPED"
        result["degraded_reason"] = ""
        result["degraded_reasons"] = []

        normalized_lanes = []
        for lane in list(result.get("lanes") or []):
            lane_copy = dict(lane) if isinstance(lane, dict) else {}
            lane_copy["state"] = "OFF"
            lane_copy["note"] = "stopped"
            lane_copy["pid"] = None
            lane_copy["attachable"] = False
            normalized_lanes.append(lane_copy)
        result["lanes"] = normalized_lanes

        watcher = dict(result.get("watcher") or {})
        watcher["alive"] = False
        watcher["pid"] = None
        result["watcher"] = watcher
        return result

    degraded_reasons = [str(item) for item in list(result.get("degraded_reasons") or []) if str(item)]
    if _STALE_RUNTIME_REASON not in degraded_reasons:
        degraded_reasons.append(_STALE_RUNTIME_REASON)
    result["runtime_state"] = "BROKEN"
    result["degraded_reason"] = _STALE_RUNTIME_REASON
    result["degraded_reasons"] = degraded_reasons

    normalized_lanes = []
    for lane in list(result.get("lanes") or []):
        lane_copy = dict(lane) if isinstance(lane, dict) else {}
        lane_state = str(lane_copy.get("state") or "")
        if lane_state not in {"BROKEN", "OFF"}:
            lane_copy["state"] = "BROKEN"
        lane_copy["note"] = _STALE_RUNTIME_REASON
        lane_copy["pid"] = None
        lane_copy["attachable"] = False
        normalized_lanes.append(lane_copy)
    result["lanes"] = normalized_lanes
    watcher = dict(result.get("watcher") or {})
    watcher["alive"] = False
    watcher["pid"] = None
    result["watcher"] = watcher
    return result


def _mark_runtime_status_recent_ambiguous(status: dict[str, object]) -> dict[str, object]:
    result = dict(status)
    degraded_reasons = [str(item) for item in list(result.get("degraded_reasons") or []) if str(item)]
    if _AMBIGUOUS_RUNTIME_REASON not in degraded_reasons:
        degraded_reasons.append(_AMBIGUOUS_RUNTIME_REASON)
    result["runtime_state"] = "DEGRADED"
    result["degraded_reason"] = _AMBIGUOUS_RUNTIME_REASON
    result["degraded_reasons"] = degraded_reasons
    return result


def _mark_runtime_status_undated_ambiguous(status: dict[str, object]) -> dict[str, object]:
    result = dict(status)
    degraded_reasons = [str(item) for item in list(result.get("degraded_reasons") or []) if str(item)]
    if _UNDATED_AMBIGUOUS_RUNTIME_REASON not in degraded_reasons:
        degraded_reasons.append(_UNDATED_AMBIGUOUS_RUNTIME_REASON)
    result["runtime_state"] = "DEGRADED"
    result["degraded_reason"] = _UNDATED_AMBIGUOUS_RUNTIME_REASON
    result["degraded_reasons"] = degraded_reasons
    return result


def tmux_alive(session: str = "") -> bool:
    return legacy_backend_debug.tmux_alive(session, run=_run)


def watcher_alive(project: Path) -> tuple[bool, int | None]:
    return legacy_backend_debug.watcher_alive(
        project,
        is_windows=IS_WINDOWS,
        run=_run,
        wsl_path_str=_wsl_path_str,
    )


def latest_md(directory: Path) -> tuple[str, float]:
    return legacy_backend_debug.latest_md(
        directory,
        is_windows=IS_WINDOWS,
        run=_run,
        wsl_path_str=_wsl_path_str,
        file_query_timeout=FILE_QUERY_TIMEOUT,
    )




def watcher_log_tail(project: Path, lines: int = 5) -> list[str]:
    return watcher_log_snapshot(project, display_lines=lines)["display_lines"]


def watcher_log_snapshot(
    project: Path,
    *,
    display_lines: int = 14,
    summary_lines: int = 50,
    hint_lines: int = 300,
) -> dict[str, list[str]]:
    return legacy_backend_debug.watcher_log_snapshot(
        project,
        display_lines=display_lines,
        summary_lines=summary_lines,
        hint_lines=hint_lines,
        read_log_lines=_read_log_lines,
    )


def pipeline_start_log_tail(project: Path, lines: int = 5) -> list[str]:
    log_path = project / ".pipeline" / "logs" / "experimental" / "pipeline-launcher-start.log"
    all_lines = _read_log_lines(log_path, tail_count=max(lines * 8, 40))
    if not all_lines:
        return ["(로그 없음)"]
    cleaned = _clean_log_lines(all_lines)
    return cleaned[-lines:] if cleaned else ["(이벤트 없음)"]


def pipeline_start_failure_hint(project: Path) -> str:
    lines = pipeline_start_log_tail(project, lines=12)
    if not lines or lines[0].startswith("("):
        return ""
    keywords = (
        "launch blocked",
        "blocked",
        "error",
        "failed",
        "failure",
        "차단",
        "실패",
        "없음",
        "missing",
        "not found",
        "cannot",
        "찾지 못",
    )
    for line in reversed(lines):
        lower = line.lower()
        if any(keyword in lower for keyword in keywords):
            return line
    return lines[-1]


def watcher_start_observed(project: Path, *, not_before: float) -> bool:
    return legacy_backend_debug.watcher_start_observed(
        project,
        not_before=not_before,
        is_windows=IS_WINDOWS,
        run=_run,
        wsl_path_str=_wsl_path_str,
        file_query_timeout=FILE_QUERY_TIMEOUT,
        watcher_log_tail=lambda runtime_project, lines: watcher_log_tail(runtime_project, lines=lines),
    )


def confirm_pipeline_start(
    project: Path,
    session: str,
    *,
    start_requested_at: float,
    action_label: str = "시작",
    progress_callback: Callable[[str], None] | None = None,
    timeout_seconds: int = 15,
    sleep_fn: Callable[[float], None] | None = None,
) -> tuple[bool, str]:
    sleeper = sleep_fn or time.sleep
    for sec in range(timeout_seconds):
        sleeper(1)
        runtime_status = normalize_runtime_status(read_runtime_status(project))
        runtime_state = str(runtime_status.get("runtime_state") or "")
        lanes = list(runtime_status.get("lanes") or [])
        ready_lanes = [
            lane
            for lane in lanes
            if bool(lane.get("attachable")) and str(lane.get("state") or "") in {"READY", "WORKING"}
        ]
        if runtime_state in {"RUNNING", "DEGRADED"} and ready_lanes:
            return True, f"파이프라인 {action_label} 완료"
        if runtime_state == "BROKEN":
            detail = str(runtime_status.get("degraded_reason") or "runtime broken")
            return False, f"{action_label} 실패: supervisor가 BROKEN 상태로 전이했습니다 — {detail}"
        if progress_callback is not None:
            progress_callback(f"{action_label} 중... runtime {runtime_state or 'STARTING'} 대기 중 ({sec + 1}초)")

    hint = pipeline_start_failure_hint(project)
    suffix = f" — {hint}" if hint else ""
    return (
        False,
        f"{action_label} 실패: 15초 안에 runtime READY 조건을 만족하지 못했습니다 "
        f"— supervisor/status를 확인해 주세요{suffix}",
    )


def pipeline_start(project: Path, session: str = "") -> str:
    sess = session or _session_name_for(project)
    resolved = resolve_project_active_profile(project)
    controls = dict(resolved.get("controls") or {})
    if not bool(controls.get("launch_allowed")):
        detail = join_display_resolver_messages(resolved) or "Active profile launch is blocked."
        return f"실행 차단: {detail}"
    try:
        script = resolve_project_runtime_file(project, "start-pipeline.sh")
    except FileNotFoundError:
        return "start-pipeline.sh 없음"
    log_path = project / ".pipeline" / "logs" / "experimental" / "pipeline-launcher-start.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if IS_WINDOWS:
        wsl_script = _windows_to_wsl_mount(script)
        wsl_project = _wsl_path_str(project)
        with log_path.open("w", encoding="utf-8") as logf:
            subprocess.Popen(
                ["wsl.exe", "-d", WSL_DISTRO, "--cd", wsl_project, "--",
                 "bash", "-l", wsl_script, wsl_project,
                 "--mode", "experimental", "--no-attach", "--session", sess],
                stdin=subprocess.DEVNULL, stdout=logf, stderr=subprocess.STDOUT,
                creationflags=CREATE_NO_WINDOW,
            )
    else:
        with log_path.open("w", encoding="utf-8") as logf:
            subprocess.Popen(
                ["bash", "-l", str(script), str(project),
                 "--mode", "experimental", "--no-attach", "--session", sess],
                cwd=str(project), stdout=logf, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, start_new_session=True,
            )
    return "시작 요청됨"


def pipeline_stop(project: Path, session: str = "") -> str:
    sess = session or _session_name_for(project)
    try:
        script = resolve_project_runtime_file(project, "stop-pipeline.sh")
    except FileNotFoundError:
        return "stop-pipeline.sh 없음"
    if IS_WINDOWS:
        wsl_script = _windows_to_wsl_mount(script)
        wsl_project = _wsl_path_str(project)
        result = subprocess.run(
            ["wsl.exe", "-d", WSL_DISTRO, "--cd", wsl_project, "--",
             "bash", wsl_script, wsl_project, "--session", sess],
            capture_output=True, timeout=15,
            **_hidden_subprocess_kwargs(),
        )
    else:
        result = subprocess.run(
            ["bash", str(script), str(project), "--session", sess],
            capture_output=True, timeout=15,
        )
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace") if isinstance(result.stderr, bytes) else str(result.stderr or "")
        stdout = (result.stdout or b"").decode("utf-8", errors="replace") if isinstance(result.stdout, bytes) else str(result.stdout or "")
        detail = (stderr.strip() or stdout.strip() or f"exit={result.returncode}").splitlines()[-1]
        raise RuntimeError(f"stop-pipeline.sh failed: {detail}")
    return "중지 완료"


# ---------------------------------------------------------------------------
# Control-slot parsing (newest-valid-control semantics)
# ---------------------------------------------------------------------------

_CONTROL_SLOTS = {
    "claude_handoff.md": "implement",
    "gemini_request.md": "request_open",
    "gemini_advice.md": "advice_ready",
    "operator_request.md": "needs_operator",
}

_SLOT_LABELS = {
    "claude_handoff.md": "Claude 실행",
    "gemini_request.md": "Gemini 실행",
    "gemini_advice.md": "Codex follow-up",
    "operator_request.md": "operator 대기",
}


def _read_slot_status(path: Path) -> str | None:
    """Return the STATUS value from a control slot file, or None."""
    if IS_WINDOWS:
        code, content = _run(["head", "-5", _wsl_path_str(path)], timeout=FILE_QUERY_TIMEOUT)
        if code != 0:
            return None
        text = content
    else:
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    for line in text.splitlines()[:10]:
        stripped = line.strip()
        if stripped.startswith("STATUS:"):
            return stripped.split(":", 1)[1].strip()
    return None


def _read_slot_control_seq(path: Path) -> int | None:
    """Return CONTROL_SEQ from a control slot file, or None."""
    if IS_WINDOWS:
        code, content = _run(["head", "-10", _wsl_path_str(path)], timeout=FILE_QUERY_TIMEOUT)
        if code != 0:
            return None
        text = content
    else:
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    for line in text.splitlines()[:10]:
        stripped = line.strip()
        if stripped.startswith("CONTROL_SEQ:"):
            try:
                value = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                return None
            return value if value >= 0 else None
    return None


def parse_control_slots(project: Path) -> dict[str, object]:
    """Parse the four canonical control slots and return active/stale info.

    Returns a dict with:
      - ``active``: ``{"file": str, "status": str, "label": str, "mtime": float, "control_seq": int | None}`` or ``None``
      - ``stale``: list of ``{"file": str, "status": str, "label": str, "mtime": float, "control_seq": int | None}``
    """
    pipeline_dir = project / ".pipeline"
    entries: list[dict[str, object]] = []

    for filename, expected_status in _CONTROL_SLOTS.items():
        slot_path = pipeline_dir / filename
        if IS_WINDOWS:
            wsl_path = _wsl_path_str(slot_path)
            code, find_out = _run(
                ["find", wsl_path, "-maxdepth", "0", "-printf", "%T@\\n"],
                timeout=FILE_QUERY_TIMEOUT,
            )
            if code != 0:
                continue
            try:
                mtime = float(find_out.strip())
            except ValueError:
                continue
        else:
            if not slot_path.exists():
                continue
            try:
                mtime = slot_path.stat().st_mtime
            except OSError:
                continue

        status = _read_slot_status(slot_path)
        if status != expected_status:
            continue  # invalid status — not a valid control slot

        entries.append({
            "file": filename,
            "status": status,
            "label": _SLOT_LABELS[filename],
            "mtime": mtime,
            "control_seq": _read_slot_control_seq(slot_path),
        })

    if not entries:
        return {"active": None, "stale": []}

    entries.sort(
        key=lambda e: (
            e["control_seq"] is not None,
            e["control_seq"] if e["control_seq"] is not None else -1,
            e["mtime"],
        ),
        reverse=True,
    )
    return {"active": entries[0], "stale": entries[1:]}


def current_verify_activity(project: Path) -> dict[str, object] | None:
    state_dir = project / ".pipeline" / "state"
    if not state_dir.exists():
        return None

    best_entry: dict[str, object] | None = None
    best_key: tuple[float, float, float, str] | None = None
    for state_path in state_dir.glob("*.json"):
        data = _read_json_file(state_path)
        if data is None:
            continue
        status = str(data.get("status") or "").strip()
        if status not in _VERIFY_ACTIVE_STATUSES:
            continue
        artifact_path = str(data.get("artifact_path") or "").strip()
        if not artifact_path:
            continue
        dispatch_at = float(data.get("last_dispatch_at") or 0.0)
        updated_at = float(data.get("updated_at") or 0.0)
        activity_at = float(data.get("last_activity_at") or dispatch_at or updated_at)
        sort_key = (activity_at, dispatch_at, updated_at, state_path.name)
        if best_key is None or sort_key > best_key:
            artifact_name = PurePosixPath(artifact_path).name or Path(artifact_path).name or artifact_path
            best_key = sort_key
            best_entry = {
                "job_id": str(data.get("job_id") or ""),
                "status": status,
                "label": _VERIFY_ACTIVITY_LABELS.get(status, "Codex 검증"),
                "artifact_path": artifact_path,
                "artifact_name": artifact_name,
                "last_dispatch_at": dispatch_at,
                "last_activity_at": activity_at,
            }
    return best_entry


def read_turn_state(project: Path) -> dict[str, object] | None:
    """Read .pipeline/state/turn_state.json if present."""
    path = project / ".pipeline" / "state" / "turn_state.json"
    return _read_json_file(path)


def read_current_run(project: Path) -> dict[str, object] | None:
    """Read .pipeline/current_run.json if present."""
    path = project / ".pipeline" / "current_run.json"
    return _read_json_file(path)


def read_runtime_status(project: Path) -> dict[str, object] | None:
    """Read the current run-scoped runtime status if present."""
    current_run = read_current_run(project)
    if not current_run:
        return None
    data: dict[str, object] | None = None
    status_path_value = str(current_run.get("status_path") or "").strip()
    if status_path_value:
        status_path = project / status_path_value
        data = _read_json_file(status_path)
    if data is None:
        run_id = str(current_run.get("run_id") or "").strip()
        if not run_id:
            return None
        status_path = project / ".pipeline" / "runs" / run_id / "status.json"
        data = _read_json_file(status_path)
    if data is None:
        return None
    runtime_state = str(data.get("runtime_state") or "STOPPED").upper()
    supervisor_alive = _pid_is_alive(_supervisor_pid(project))
    age_sec = _runtime_status_age_sec(data)
    if runtime_state == "STOPPING" and not supervisor_alive:
        return _mark_runtime_status_stale(data)
    if runtime_state == "BROKEN":
        if supervisor_alive:
            return data
        return _mark_runtime_status_stale(data)
    if runtime_state == "STOPPED":
        return data
    if (
        runtime_state in {"RUNNING", "DEGRADED"}
        and not supervisor_alive
        and (
            _runtime_status_processes_quiescent(data)
            or _runtime_status_fields_quiescent(data)
        )
    ):
        return _mark_runtime_status_stale(data)
    if (
        runtime_state in {"RUNNING", "DEGRADED"}
        and not supervisor_alive
        and age_sec is not None
        and age_sec <= _RUNTIME_STATUS_STALE_AFTER_SEC
        and _runtime_status_ambiguous(data)
    ):
        return _mark_runtime_status_recent_ambiguous(data)
    if (
        runtime_state in {"RUNNING", "DEGRADED"}
        and not supervisor_alive
        and age_sec is None
        and _runtime_status_ambiguous(data)
    ):
        return _mark_runtime_status_undated_ambiguous(data)
    if age_sec is None or age_sec <= _RUNTIME_STATUS_STALE_AFTER_SEC:
        return data
    if supervisor_alive:
        return data
    return _mark_runtime_status_stale(data)


def read_runtime_event_tail(project: Path, *, max_lines: int = 14) -> list[dict[str, object]]:
    current_run = read_current_run(project)
    if not current_run:
        return []
    events_path_value = str(current_run.get("events_path") or "").strip()
    if events_path_value:
        events_path = project / events_path_value
    else:
        run_id = str(current_run.get("run_id") or "").strip()
        if not run_id:
            return []
        events_path = project / ".pipeline" / "runs" / run_id / "events.jsonl"
    return [dict(item) for item in read_jsonl_tail(events_path, max_lines=max_lines)]


def runtime_state(project: Path) -> str:
    status = normalize_runtime_status(read_runtime_status(project))
    if not status:
        return "STOPPED"
    return str(status.get("runtime_state") or "STOPPED")


def runtime_active(project: Path) -> bool:
    return runtime_state(project) not in {"STOPPED", "BROKEN"}


def runtime_attach(project: Path, session: str = "", lane: str | None = None) -> int:
    sess = session or _session_name_for(project)
    cmd = [
        "python3",
        "-m",
        "pipeline_runtime.cli",
        "attach",
        "--project-root",
        str(project),
        "--session",
        sess,
    ]
    if lane:
        cmd.extend(["--lane", lane])
    if IS_WINDOWS:
        wsl_project = _wsl_path_str(project)
        process = subprocess.Popen(
            ["wsl.exe", "-d", WSL_DISTRO, "--cd", wsl_project, "--", *cmd],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
        return int(process.pid)
    process = subprocess.Popen(
        cmd,
        cwd=str(project),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return int(process.pid)


def runtime_attach_blocking(project: Path, session: str = "", lane: str | None = None) -> int:
    adapter = TmuxAdapter(project, session or _session_name_for(project))
    return adapter.attach_blocking(lane)


def runtime_capture_tail(project: Path, session: str = "", lane: str | None = None, *, lines: int = 120) -> str:
    if not lane:
        return ""
    adapter = TmuxAdapter(project, session or _session_name_for(project))
    return adapter.capture_tail(lane, lines=lines)


_TURN_STATE_LABELS: dict[str, str] = {
    "IDLE": "대기",
    "CLAUDE_ACTIVE": "Claude 실행 중",
    "CODEX_VERIFY": "Codex 검증 중",
    "CODEX_FOLLOWUP": "Codex 후속 판단 중",
    "GEMINI_ADVISORY": "Gemini 자문 중",
    "OPERATOR_WAIT": "운영자 결정 대기",
}


def _slot_provenance(entry: dict[str, object]) -> str:
    """Return 'seq N' or 'mtime fallback' for a parsed control-slot entry."""
    seq = entry.get("control_seq")
    if seq is not None:
        return f"seq {seq}"
    return "mtime fallback"


def format_control_summary(
    parsed: dict[str, object],
    *,
    verify_activity: dict[str, object] | None = None,
    turn_state: dict[str, object] | None = None,
) -> tuple[str, str]:
    """Return (active_text, stale_text) for display in the system card.

    If turn_state is provided, use it exclusively for active display.
    Do not mix turn_state with legacy slot parsing.
    """
    if turn_state is not None:
        state_value = str(turn_state.get("state") or "IDLE")
        label = _TURN_STATE_LABELS.get(state_value, state_value)
        control_file = str(turn_state.get("active_control_file") or "")
        seq = turn_state.get("active_control_seq")
        parts = [f"활성 제어: {label}"]
        if control_file:
            prov_part = f"({control_file}"
            if seq is not None and int(seq) >= 0:
                prov_part += f", seq {seq}"
            prov_part += ")"
            parts.append(prov_part)
        active_text = " ".join(parts)

        stale_list = parsed.get("stale") or []
        if not stale_list:
            stale_text = ""
        else:
            stale_parts = []
            for s in stale_list:
                prov = _slot_provenance(s)  # type: ignore[arg-type]
                stale_parts.append(f"{s['file']} ({prov})")  # type: ignore[index]
            stale_text = f"비활성: {', '.join(stale_parts)}"

        return active_text, stale_text

    # Legacy fallback
    active = parsed.get("active")
    if verify_activity is not None:
        artifact_name = str(verify_activity.get("artifact_name") or "latest /work")
        phase_label = str(verify_activity.get("label") or "Codex 검증")
        active_text = f"활성 제어: {phase_label} ({artifact_name})"
        if active is not None:
            prov = _slot_provenance(active)  # type: ignore[arg-type]
            active_text += f" · 대기 제어 {active['label']} ({active['file']}, {prov})"  # type: ignore[index]
    elif active is None:
        active_text = "활성 제어: 없음"
    else:
        prov = _slot_provenance(active)  # type: ignore[arg-type]
        active_text = f"활성 제어: {active['label']} ({active['file']}, {prov})"  # type: ignore[index]

    stale_list = parsed.get("stale", [])
    if not stale_list:
        stale_text = ""
    else:
        parts = []
        for s in stale_list:
            prov = _slot_provenance(s)  # type: ignore[arg-type]
            parts.append(f"{s['file']} ({prov})")  # type: ignore[index]
        stale_text = f"비활성: {', '.join(parts)}"

    return active_text, stale_text


def token_usage_db_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "usage.db"


def token_collector_pid_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.pid"


def token_collector_log_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.log"


def token_collector_pane_id_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.pane_id"


def token_collector_window_name_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.window_name"


def token_collector_launch_mode_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.launch_mode"


def token_collector_alive(project: Path) -> tuple[bool, int | None]:
    pid_path = token_collector_pid_path(project)
    if IS_WINDOWS:
        code, content = _run(["cat", _wsl_path_str(pid_path)])
        if code != 0 or not content.strip():
            return False, None
        try:
            pid = int(content.strip())
        except ValueError:
            return False, None
        check_code, _ = _run(["kill", "-0", str(pid)])
        return check_code == 0, pid
    if not pid_path.exists():
        return False, None
    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, 0)
        return True, pid
    except (ValueError, OSError):
        return False, None


def token_collector_stop(project: Path) -> str:
    alive, pid = token_collector_alive(project)
    session = _session_name_for(project)
    launch_mode = _read_sidecar_text(token_collector_launch_mode_path(project))
    window_name = _read_sidecar_text(token_collector_window_name_path(project)) or "usage-collector"
    if pid is None:
        _remove_token_collector_metadata(project)
        return "token collector not running"
    if alive:
        if IS_WINDOWS:
            _run(["kill", "-TERM", str(pid)], timeout=5.0)
        else:
            try:
                os.kill(pid, 15)
            except OSError:
                pass
        for _ in range(20):
            time.sleep(0.1)
            still_alive, _ = token_collector_alive(project)
            if not still_alive:
                break
    if launch_mode == "tmux" and tmux_alive(session):
        _run(["tmux", "kill-window", "-t", f"{session}:{window_name}"], timeout=5.0)
    _remove_token_collector_metadata(project)
    return "token collector stopped"


def token_collector_start(project: Path, since_days: int = DEFAULT_TOKEN_SINCE_DAYS) -> str:
    session = _session_name_for(project)
    if tmux_alive(session):
        return _spawn_token_collector_tmux(project, session=session, since_days=since_days)
    return _spawn_token_collector_background(project, since_days=since_days)


def _spawn_token_collector_tmux(project: Path, *, session: str, since_days: int) -> str:
    usage_dir = project / ".pipeline" / "usage"
    usage_dir.mkdir(parents=True, exist_ok=True)
    log_path = token_collector_log_path(project)
    db_path = token_usage_db_path(project)
    script_path = _token_collector_script_path(project)
    _remove_token_collector_metadata(project)
    _run(["tmux", "kill-window", "-t", f"{session}:usage-collector"], timeout=5.0)
    collector_args = [
        "--project-root",
        _wsl_path_str(project) if IS_WINDOWS else str(project),
        "--db-path",
        _wsl_path_str(db_path) if IS_WINDOWS else str(db_path),
        "--poll-interval",
        "3.0",
        "--daemon",
        "--since-days",
        str(int(since_days)),
    ]
    command = (
        _token_collector_wsl_python_shell(script_path, collector_args)
        + f" >> {shlex.quote(_wsl_path_str(log_path) if IS_WINDOWS else str(log_path))} 2>&1"
    )
    code, pane_id = _run(
        [
            "tmux",
            "new-window",
            "-d",
            "-P",
            "-F",
            "#{pane_id}",
            "-t",
            session,
            "-n",
            "usage-collector",
            "-c",
            _wsl_path_str(project) if IS_WINDOWS else str(project),
            command,
        ],
        timeout=8.0,
    )
    if code != 0 or not pane_id:
        raise RuntimeError("token collector tmux window could not be created")
    code, pid_text = _run(["tmux", "display-message", "-p", "-t", pane_id, "#{pane_pid}"], timeout=5.0)
    if code != 0 or not pid_text.strip():
        raise RuntimeError("token collector pane PID could not be resolved")
    _write_token_collector_metadata(
        project,
        pid=pid_text.strip(),
        pane_id=pane_id.strip(),
        window_name="usage-collector",
        launch_mode="tmux",
    )
    alive, _pid = token_collector_alive(project)
    if not alive:
        raise RuntimeError("token collector daemon could not be started")
    return "token collector started"


def _spawn_token_collector_background(project: Path, *, since_days: int) -> str:
    usage_dir = project / ".pipeline" / "usage"
    usage_dir.mkdir(parents=True, exist_ok=True)
    log_path = token_collector_log_path(project)
    db_path = token_usage_db_path(project)
    script_path = _token_collector_script_path(project)
    _remove_token_collector_metadata(project)
    if IS_WINDOWS:
        wsl_project = _wsl_path_str(project)
        usage_dir_wsl = _wsl_path_str(usage_dir)
        log_wsl = _wsl_path_str(log_path)
        pid_wsl = _wsl_path_str(token_collector_pid_path(project))
        db_wsl = _wsl_path_str(db_path)
        collector_args = [
            "--project-root",
            wsl_project,
            "--db-path",
            db_wsl,
            "--poll-interval",
            "3.0",
            "--daemon",
            "--since-days",
            str(int(since_days)),
        ]
        command = (
            f"cd {shlex.quote(wsl_project)} && "
            f"mkdir -p {shlex.quote(usage_dir_wsl)} && "
            f"rm -f {shlex.quote(pid_wsl)} && "
            + _token_collector_wsl_python_shell(
                script_path,
                collector_args,
                daemon=True,
                log_path=log_wsl,
                pid_path=pid_wsl,
            )
        )
        result = subprocess.run(
            _wsl_wrap(["bash", "-lc", command]),
            capture_output=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
            **_hidden_subprocess_kwargs(),
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip() or f"exit {result.returncode}"
            raise RuntimeError(f"token collector background launch failed: {detail}")
        pid_text = _wait_for_sidecar_text(token_collector_pid_path(project))
    else:
        with log_path.open("a", encoding="utf-8") as logf:
            proc = subprocess.Popen(
                [
                    "python3",
                    "-u",
                    str(script_path),
                    "--project-root",
                    str(project),
                    "--db-path",
                    str(db_path),
                    "--poll-interval",
                    "3.0",
                    "--daemon",
                    "--since-days",
                    str(int(since_days)),
                ],
                cwd=str(project),
                stdout=logf,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        pid_text = str(proc.pid)
    if not pid_text.strip():
        detail = _token_collector_start_failure_detail(project) or "PID file was not written"
        raise RuntimeError(f"token collector background process could not be started: {detail}")
    _write_token_collector_metadata(
        project,
        pid=pid_text.strip(),
        pane_id="",
        window_name="",
        launch_mode="background",
    )
    alive = False
    _pid: int | None = None
    for _ in range(20):
        alive, _pid = token_collector_alive(project)
        if alive:
            break
        time.sleep(0.1)
    if not alive:
        detail = _token_collector_start_failure_detail(project)
        raise RuntimeError(
            f"token collector background process could not be started"
            + (f": {detail}" if detail else "")
        )
    return "token collector started"


def run_token_collector_once(
    project: Path,
    db_path: Path,
    *,
    since_days: int | None = None,
    force_rescan: bool = False,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    usage_dir = db_path.parent
    usage_dir.mkdir(parents=True, exist_ok=True)
    script_path = _token_collector_script_path(project)
    cmd = [
        "--project-root",
        _wsl_path_str(project) if IS_WINDOWS else str(project),
        "--db-path",
        _wsl_path_str(db_path) if IS_WINDOWS else str(db_path),
        "--once",
        "--progress",
    ]
    if since_days is not None:
        cmd.extend(["--since-days", str(int(since_days))])
    if force_rescan:
        cmd.append("--force-rescan")
    popen_kwargs: dict[str, object] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "bufsize": 1,
    }
    if IS_WINDOWS:
        popen_kwargs["text"] = True
        popen_kwargs["encoding"] = "utf-8"
        popen_kwargs["errors"] = "replace"
        popen_kwargs.update(_hidden_subprocess_kwargs())
        proc = subprocess.Popen(
            _wsl_wrap(["bash", "-lc", _token_collector_wsl_python_shell(script_path, cmd)]),
            **popen_kwargs,
        )
    else:
        popen_kwargs["text"] = True
        proc = subprocess.Popen(["python3", "-u", script_path, *cmd], cwd=str(project), **popen_kwargs)

    summary: dict[str, object] | None = None
    output_lines: list[str] = []
    assert proc.stdout is not None
    for raw_line in proc.stdout:
        line = raw_line.strip()
        if not line:
            continue
        output_lines.append(line)
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("event") == "progress":
            if progress_callback is not None:
                progress_callback(payload)
            continue
        if isinstance(payload, dict):
            summary = payload
    return_code = proc.wait()
    if return_code != 0 or summary is None:
        detail = output_lines[-1] if output_lines else f"exit={return_code}"
        raise RuntimeError(f"token collector failed: {detail}")
    return summary


def backfill_token_history(
    project: Path,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    db_path = token_usage_db_path(project)
    was_running, summary, restart_warn = _run_token_maintenance_once(
        project,
        db_path,
        progress_callback=progress_callback,
    )
    return _token_maintenance_result("backfill", summary, was_running, restart_warning=restart_warn)


def rebuild_token_db(
    project: Path,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    usage_dir = token_usage_db_path(project).parent
    usage_dir.mkdir(parents=True, exist_ok=True)
    db_path = token_usage_db_path(project)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    temp_db = usage_dir / f"usage.rebuild-{stamp}.db"
    backup_db = usage_dir / f"usage.backup-{stamp}.db"
    summary: dict[str, object] | None = None
    was_running = False
    action_error: Exception | None = None
    restart_error: Exception | None = None
    try:
        was_running, summary, _rw = _run_token_maintenance_once(
            project,
            temp_db,
            progress_callback=progress_callback,
            restart_collector=False,
        )
        if db_path.exists():
            os.replace(db_path, backup_db)
        os.replace(temp_db, db_path)
    except Exception as exc:
        action_error = exc
        try:
            temp_db.unlink(missing_ok=True)
        except OSError:
            pass
    finally:
        try:
            _restart_token_collector(project, progress_callback=progress_callback, summary=summary)
        except Exception as exc:
            restart_error = exc
    _raise_token_maintenance_errors(action_error, restart_error)
    restart_warn = str(restart_error) if restart_error is not None else ""
    return _token_maintenance_result(
        "rebuild",
        summary,
        was_running,
        backup_path=backup_db if backup_db.exists() else "",
        restart_warning=restart_warn,
    )


def _token_maintenance_result(
    action: str,
    summary: dict[str, object] | None,
    collector_was_running: bool,
    *,
    backup_path: Path | str = "",
    restart_warning: str = "",
) -> dict[str, object]:
    result: dict[str, object] = {
        "action": action,
        "summary": dict(summary or {}),
        "backup_path": str(backup_path) if backup_path else "",
        "collector_was_running": collector_was_running,
    }
    if restart_warning:
        result["restart_warning"] = restart_warning
    return result


def _raise_token_maintenance_errors(
    action_error: Exception | None,
    restart_error: Exception | None,
) -> None:
    """Raise if action failed. Collector restart failure alone is demoted to warning."""
    if action_error is not None and restart_error is not None:
        raise RuntimeError(f"{action_error}; collector restart failed: {restart_error}")
    if action_error is not None:
        raise action_error
    # restart_error alone: action succeeded, collector restart is best-effort
    # Don't raise — the caller should still report success with a warning


def _emit_token_progress(
    progress_callback: Callable[[dict[str, object]], None] | None,
    phase: str,
    *,
    progress_percent: int,
    summary: dict[str, object] | None = None,
) -> None:
    if progress_callback is None:
        return
    data = summary or {}
    progress_callback(
        {
            "event": "progress",
            "phase": phase,
            "progress_percent": progress_percent,
            "scanned_files": int(data.get("scanned_files") or 0),
            "parsed_files": int(data.get("parsed_files") or 0),
            "total_files": int(data.get("total_files") or 0),
            "usage_inserted": int(data.get("usage_inserted") or 0),
            "pipeline_inserted": int(data.get("pipeline_inserted") or 0),
            "duplicates": int(data.get("duplicates") or 0),
            "retry_later": int(data.get("retry_later") or 0),
            "elapsed_sec": float(data.get("elapsed_sec") or 0.0),
        }
    )


def _restart_token_collector(
    project: Path,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    summary: dict[str, object] | None = None,
) -> None:
    _emit_token_progress(progress_callback, "starting_collector", progress_percent=100, summary=summary)
    token_collector_start(project, since_days=DEFAULT_TOKEN_SINCE_DAYS)


def _run_token_maintenance_once(
    project: Path,
    db_path: Path,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    restart_collector: bool = True,
) -> tuple[bool, dict[str, object], str]:
    """Returns (was_running, summary, restart_warning)."""
    was_running, _pid = token_collector_alive(project)
    if was_running:
        _emit_token_progress(progress_callback, "stopping_collector", progress_percent=0)
        token_collector_stop(project)
    summary: dict[str, object] | None = None
    action_error: Exception | None = None
    restart_error: Exception | None = None
    try:
        summary = run_token_collector_once(
            project,
            db_path,
            force_rescan=True,
            progress_callback=progress_callback,
        )
    except Exception as exc:
        action_error = exc
    finally:
        if restart_collector:
            try:
                _restart_token_collector(project, progress_callback=progress_callback, summary=summary)
            except Exception as exc:
                restart_error = exc
    _raise_token_maintenance_errors(action_error, restart_error)
    restart_warning = str(restart_error) if restart_error is not None else ""
    return was_running, dict(summary or {}), restart_warning


def _token_collector_script_path(project: Path) -> str:
    script = _normalize_token_runtime_asset_path(
        resolve_project_runtime_file(project, "token_collector.py")
    )
    return _windows_to_wsl_mount(script) if IS_WINDOWS else str(script)


def _token_collector_wsl_candidates(script_path: str) -> list[str]:
    raw = script_path.replace("\\", "/")
    seen: set[str] = set()
    candidates: list[str] = []

    def _add(path: str) -> None:
        path = path.replace("\\", "/")
        while "/_data/_data/" in path:
            path = path.replace("/_data/_data/", "/_data/")
        if path in seen:
            return
        seen.add(path)
        candidates.append(path)

    _add(raw)
    path = PurePosixPath(raw)
    if path.name == "token_collector.py":
        parent = path.parent
        while parent.name == "_data":
            _add(str(parent / path.name))
            parent = parent.parent
            _add(str(parent / path.name))
    return candidates


def _token_collector_wsl_python_shell(
    script_path: str,
    collector_args: list[str],
    *,
    daemon: bool = False,
    log_path: str | None = None,
    pid_path: str | None = None,
) -> str:
    """Build a bash command string that runs token_collector.py.

    Uses the resolved script_path directly instead of multi-candidate probing
    to avoid Windows command-line escaping issues with wsl.exe -- bash -lc.
    """
    quoted_script = shlex.quote(script_path)
    quoted_args = " ".join(shlex.quote(arg) for arg in collector_args)

    # Verify the script exists, then run it
    command = (
        f"if [ ! -f {quoted_script} ]; then "
        f"echo 'token_collector.py not found: '{quoted_script} >&2; exit 127; "
        f"fi; "
    )
    if daemon:
        if not log_path or not pid_path:
            raise ValueError("daemon token collector launch requires log_path and pid_path")
        return (
            command
            + f"nohup python3 -u {quoted_script} {quoted_args} "
            + f">> {shlex.quote(log_path)} 2>&1 < /dev/null & echo $! > {shlex.quote(pid_path)}"
        )
    return command + f"exec python3 -u {quoted_script} {quoted_args}"


def _write_token_collector_metadata(
    project: Path,
    *,
    pid: str,
    pane_id: str,
    window_name: str,
    launch_mode: str,
) -> None:
    _write_sidecar_text(token_collector_pid_path(project), pid)
    _write_sidecar_text(token_collector_pane_id_path(project), pane_id)
    _write_sidecar_text(token_collector_window_name_path(project), window_name)
    _write_sidecar_text(token_collector_launch_mode_path(project), launch_mode)


def _remove_token_collector_metadata(project: Path) -> None:
    for path in (
        token_collector_pid_path(project),
        token_collector_pane_id_path(project),
        token_collector_window_name_path(project),
        token_collector_launch_mode_path(project),
    ):
        _remove_sidecar_file(path)


def _read_sidecar_text(path: Path) -> str:
    if IS_WINDOWS:
        code, output = _run(["cat", _wsl_path_str(path)], timeout=3.0)
        return output.strip() if code == 0 else ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _wait_for_sidecar_text(path: Path, timeout_sec: float = 2.0) -> str:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        content = _read_sidecar_text(path)
        if content.strip():
            return content
        time.sleep(0.1)
    return _read_sidecar_text(path)


def _token_collector_start_failure_detail(project: Path, lines: int = 12) -> str:
    log_path = token_collector_log_path(project)
    if IS_WINDOWS:
        code, output = _run(["tail", "-n", str(lines), _wsl_path_str(log_path)], timeout=3.0)
        if code == 0 and output.strip():
            return output.strip().splitlines()[-1]
        return ""
    if not log_path.exists():
        return ""
    try:
        lines_text = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""
    return lines_text[-1].strip() if lines_text else ""


def _write_sidecar_text(path: Path, value: str) -> None:
    if IS_WINDOWS:
        parent = _wsl_path_str(path.parent)
        target = _wsl_path_str(path)
        command = (
            f"mkdir -p {shlex.quote(parent)} && "
            f"printf %s {shlex.quote(value)} > {shlex.quote(target)}"
        )
        _run(["bash", "-lc", command], timeout=5.0)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _remove_sidecar_file(path: Path) -> None:
    if IS_WINDOWS:
        _run(["rm", "-f", _wsl_path_str(path)], timeout=3.0)
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
