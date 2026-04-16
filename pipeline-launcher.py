#!/usr/bin/env python3
"""
pipeline-launcher.py — 내부용 pipeline desktop launcher (curses TUI)

사용법:
  python3 pipeline-launcher.py [project_path]
  python3 pipeline-launcher.py .
  PROJECT_ROOT=/path/to/project python3 pipeline-launcher.py

키 바인딩:
  S — pipeline start
  T — pipeline stop
  R — pipeline restart (stop → start)
  A — runtime attach (curses 일시 해제)
  Q — launcher 종료
"""

from __future__ import annotations

import curses
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import NamedTuple

from pipeline_gui.backend import (
    confirm_pipeline_start as backend_confirm_pipeline_start,
    normalize_runtime_status,
    read_runtime_event_tail,
    read_runtime_status,
    supervisor_alive,
)
from pipeline_gui.formatting import time_ago
from pipeline_gui.platform import IS_WINDOWS, WSL_DISTRO, _hidden_subprocess_kwargs, _wsl_path_str
from pipeline_gui.project import _session_name_for
from pipeline_gui.setup_profile import (
    join_resolver_messages,
    resolve_project_active_profile,
    resolve_project_runtime_adapter,
)

_START_READY_TIMEOUT_SEC = 15.0


# ── 프로젝트 경로 결정 ────────────────────────────────────────

def parse_args() -> tuple[Path, bool]:
    project_arg: str | None = None
    line_mode = False

    for arg in sys.argv[1:]:
        if arg == "--line-mode":
            line_mode = True
            continue
        if arg.startswith("--"):
            continue
        if project_arg is None:
            project_arg = arg

    if project_arg:
        return Path(project_arg).resolve(), line_mode

    env = os.environ.get("PROJECT_ROOT")
    if env:
        return Path(env).resolve(), line_mode
    return Path.cwd().resolve(), line_mode


def resolved_session_name(project: Path) -> str:
    return _session_name_for(project)


def launcher_error_log(project: Path) -> Path:
    return project / ".pipeline" / "logs" / "experimental" / "pipeline-launcher-error.log"


def launcher_action_log(project: Path, action: str) -> Path:
    return project / ".pipeline" / "logs" / "experimental" / f"pipeline-launcher-{action}.log"


def safe_addstr(
    stdscr: curses.window,
    row: int,
    col: int,
    text: str,
    attr: int = 0,
    max_width: int | None = None,
) -> None:
    """터미널 폭을 넘지 않도록 잘라서 그리고, curses 예외를 삼킵니다."""
    h, w = stdscr.getmaxyx()
    if row < 0 or row >= h or col >= w:
        return
    allowed = w - col
    if max_width is not None:
        allowed = min(allowed, max_width)
    if allowed <= 0:
        return
    clipped = text[:allowed]
    try:
        stdscr.addstr(row, col, clipped, attr)
    except curses.error:
        pass


def _fit_text(text: str, width: int) -> str:
    """고정폭 컬럼 안에 맞게 자르거나 패딩합니다."""
    if width <= 0:
        return ""
    if len(text) <= width:
        return text.ljust(width)
    if width == 1:
        return text[:1]
    return text[: width - 1] + "…"


def _control_summary(control_file: str, control_seq: int, control_status: str) -> str:
    label = Path(control_file).name if control_file else "(없음)"
    detail_parts: list[str] = []
    if control_status and control_status != "none":
        detail_parts.append(control_status)
    if control_seq >= 0:
        detail_parts.append(f"seq {control_seq}")
    if not detail_parts:
        return label
    return f"{label} · {' · '.join(detail_parts)}"


# ── 파이프라인 제어 ────────────────────────────────────────────

def _runtime_cli_base(project: Path) -> list[str]:
    if IS_WINDOWS:
        return [
            "wsl.exe",
            "-d",
            WSL_DISTRO,
            "--cd",
            _wsl_path_str(project),
            "--",
            "python3",
            "-m",
            "pipeline_runtime.cli",
        ]
    return ["python3", "-m", "pipeline_runtime.cli"]


def _runtime_has_live_surfaces(runtime_status: dict[str, object], *, project: Path) -> bool:
    watcher = dict(runtime_status.get("watcher") or {})
    lanes = list(runtime_status.get("lanes") or [])
    sup_alive, _sup_pid = supervisor_alive(project)
    attachable_lanes = any(
        bool(lane.get("attachable")) or str(lane.get("state") or "") in {"READY", "WORKING", "BOOTING"}
        for lane in lanes
        if isinstance(lane, dict)
    )
    return sup_alive or bool(watcher.get("alive")) or attachable_lanes


def _runtime_already_active(project: Path) -> bool:
    runtime_status = normalize_runtime_status(read_runtime_status(project))
    runtime_state = str(runtime_status.get("runtime_state") or "STOPPED")
    if runtime_state == "STOPPED":
        return False
    if runtime_state == "BROKEN":
        return _runtime_has_live_surfaces(runtime_status, project=project)
    return _runtime_has_live_surfaces(runtime_status, project=project)


def _wait_for_runtime_stopped(project: Path, *, timeout_sec: float = 20.0) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        runtime_status = normalize_runtime_status(read_runtime_status(project))
        runtime_state = str(runtime_status.get("runtime_state") or "STOPPED")
        if runtime_state == "STOPPED" and not _runtime_has_live_surfaces(runtime_status, project=project):
            return True
        if not runtime_status:
            sup_alive, _ = supervisor_alive(project)
            if not sup_alive:
                return True
        time.sleep(0.25)
    return False


def _spawn_runtime_cli(project: Path, args: list[str], *, action: str) -> None:
    log_path = launcher_action_log(project, action)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = _runtime_cli_base(project) + args
    with log_path.open("w", encoding="utf-8") as logf:
        if IS_WINDOWS:
            subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=logf,
                stderr=subprocess.STDOUT,
                **_hidden_subprocess_kwargs(),
            )
            return
        subprocess.Popen(
            cmd,
            cwd=str(project),
            stdin=subprocess.DEVNULL,
            stdout=logf,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def _run_runtime_cli(project: Path, args: list[str], *, timeout: float = 40.0) -> subprocess.CompletedProcess[str]:
    cmd = _runtime_cli_base(project) + args
    kwargs: dict[str, object] = {
        "capture_output": True,
        "timeout": timeout,
    }
    if IS_WINDOWS:
        kwargs["encoding"] = "utf-8"
        kwargs["errors"] = "replace"
        kwargs.update(_hidden_subprocess_kwargs())
    else:
        kwargs["text"] = True
        kwargs["cwd"] = str(project)
    return subprocess.run(cmd, **kwargs)

def pipeline_start(project: Path, session: str = "") -> str:
    resolved_session = session or resolved_session_name(project)
    resolved = resolve_project_active_profile(project)
    controls = dict(resolved.get("controls") or {})
    if not bool(controls.get("launch_allowed")):
        detail = join_resolver_messages(resolved) or "Active profile launch is blocked."
        return f"실행 차단: {detail}"
    if _runtime_already_active(project):
        return "이미 실행 중입니다. Restart를 사용하세요."
    _spawn_runtime_cli(
        project,
        ["start", str(project), "--mode", "experimental", "--session", resolved_session, "--no-attach"],
        action="start",
    )
    return "시작 요청됨"


def pipeline_stop(project: Path, session: str = "") -> str:
    resolved_session = session or resolved_session_name(project)
    result = _run_runtime_cli(project, ["stop", str(project), "--session", resolved_session])
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() or f"exit={result.returncode}"
        return f"중지 실패: {detail.splitlines()[-1]}"
    if not _wait_for_runtime_stopped(project):
        return "중지 요청은 완료됐지만 STOPPED 상태 확인에 실패했습니다"
    return "중지 완료"


def pipeline_restart(project: Path, session: str = "") -> str:
    resolved_session = session or resolved_session_name(project)
    resolved = resolve_project_active_profile(project)
    controls = dict(resolved.get("controls") or {})
    if not bool(controls.get("launch_allowed")):
        detail = join_resolver_messages(resolved) or "Active profile launch is blocked."
        return f"실행 차단: {detail}"
    stop_message = pipeline_stop(project, resolved_session)
    if stop_message != "중지 완료":
        return f"재시작 중지 단계 실패: {stop_message}"
    start_message = pipeline_start(project, resolved_session)
    if start_message != "시작 요청됨":
        return f"재시작 시작 단계 실패: {start_message}"
    return "재시작 요청됨"


def runtime_attach(project: Path, session: str) -> str:
    """curses를 일시 해제하고 runtime CLI 경유 attach 실행."""
    resolved_session = session or resolved_session_name(project)
    result = subprocess.run(
        _runtime_cli_base(project) + ["attach", "--project-root", str(project), "--session", resolved_session],
        cwd=None if IS_WINDOWS else str(project),
        check=False,
    )
    if result.returncode == 0:
        return "runtime attach에서 돌아왔습니다."
    return f"runtime attach 실패 (exit={result.returncode})"


def wait_for_pipeline_ready(project: Path, session: str, timeout_sec: float = _START_READY_TIMEOUT_SEC) -> tuple[bool, str]:
    return backend_confirm_pipeline_start(
        project,
        session,
        start_requested_at=time.time(),
        action_label="기동",
        timeout_seconds=int(timeout_sec),
    )


class AgentSnapshot(NamedTuple):
    label: str
    status: str
    status_note: str
    detail: str


def runtime_lane_name_map(project: Path) -> dict[int, str]:
    lane_configs = list(resolve_project_runtime_adapter(project).get("lane_configs") or [])
    lane_names = {
        int(cfg.get("pane_index", idx)): str(cfg.get("name") or f"Pane {idx}")
        for idx, cfg in enumerate(lane_configs)
        if isinstance(cfg, dict)
    }
    for pane_index in range(3):
        lane_names.setdefault(pane_index, f"Pane {pane_index}")
    return lane_names


def _runtime_view(project: Path) -> dict[str, object]:
    status = normalize_runtime_status(read_runtime_status(project))
    artifacts = dict(status.get("artifacts") or {})
    lanes = list(status.get("lanes") or [])
    watcher = dict(status.get("watcher") or {})
    control = dict(status.get("control") or {})
    active_round = dict(status.get("active_round") or {})
    autonomy = dict(status.get("autonomy") or {})
    raw_events: list[dict[str, object]] = []
    event_lines: list[str] = []
    for event in read_runtime_event_tail(project, max_lines=12):
        raw_events.append(event)
        event_type = str(event.get("event_type") or "")
        payload = dict(event.get("payload") or {})
        subject = ""
        if event_type == "control_changed":
            control_status_text = str(payload.get("active_control_status") or "")
            seq = payload.get("active_control_seq")
            file_label = Path(str(payload.get("active_control_file") or "")).name
            detail_parts = [
                part
                for part in [control_status_text, f"seq={seq}" if seq is not None else "", file_label]
                if part
            ]
            subject = " ".join(detail_parts)
        elif event_type == "control_duplicate_ignored":
            reason = str(payload.get("reason") or "duplicate_control")
            seq = payload.get("control_seq")
            subject = f"{reason} seq={seq}" if seq is not None else reason
        elif event_type == "control_operator_stale_ignored":
            reason = str(payload.get("reason") or "stale_operator_control")
            seq = payload.get("control_seq")
            subject = f"{reason} seq={seq}" if seq is not None else reason
        elif event_type == "control_operator_gated":
            reason = str(payload.get("reason") or "operator_gate")
            mode = str(payload.get("mode") or "")
            seq = payload.get("control_seq")
            detail = " ".join(part for part in [reason, mode, f"seq={seq}" if seq is not None else ""] if part)
            subject = detail
        elif event_type == "autonomy_changed":
            mode = str(payload.get("mode") or "")
            reason = str(payload.get("block_reason") or "")
            subject = " ".join(part for part in [mode, reason] if part)
        elif event_type == "runtime_started":
            subject = str(payload.get("runtime_state") or "")
        else:
            subject = str(payload.get("lane") or payload.get("job_id") or payload.get("receipt_id") or "")
        event_lines.append(f"{event_type} {subject}".strip())
    return {
        "runtime_state": str(status.get("runtime_state") or "STOPPED"),
        "degraded_reason": str(status.get("degraded_reason") or ""),
        "degraded_reasons": [str(item) for item in list(status.get("degraded_reasons") or []) if str(item)],
        "watcher_alive": bool(watcher.get("alive")),
        "watcher_pid": watcher.get("pid"),
        "work_name": str((artifacts.get("latest_work") or {}).get("path") or "—"),
        "work_mtime": float((artifacts.get("latest_work") or {}).get("mtime") or 0.0),
        "verify_name": str((artifacts.get("latest_verify") or {}).get("path") or "—"),
        "verify_mtime": float((artifacts.get("latest_verify") or {}).get("mtime") or 0.0),
        "control_file": str(control.get("active_control_file") or ""),
        "control_seq": int(control.get("active_control_seq") or -1),
        "control_status": str(control.get("active_control_status") or "none"),
        "autonomy_mode": str(autonomy.get("mode") or "normal"),
        "autonomy_reason": str(autonomy.get("block_reason") or ""),
        "active_round": active_round,
        "last_receipt_id": str(status.get("last_receipt_id") or ""),
        "lanes": lanes,
        "event_lines": event_lines,
        "events": raw_events,
    }


def pane_snapshots(runtime_view: dict[str, object]) -> list[AgentSnapshot]:
    summaries: list[AgentSnapshot] = []
    for lane in list(runtime_view.get("lanes") or []):
        if not isinstance(lane, dict):
            continue
        name = str(lane.get("name") or "")
        state = str(lane.get("state") or "OFF")
        status_note = str(lane.get("note") or "")
        detail_parts = []
        if lane.get("pid"):
            detail_parts.append(f"pid={lane['pid']}")
        last_event_at = str(lane.get("last_event_at") or "")
        if last_event_at:
            detail_parts.append(f"event={last_event_at}")
        summaries.append(AgentSnapshot(name, state, status_note, " · ".join(detail_parts)))
    return summaries


def focused_lane_details(project: Path, runtime_view: dict[str, object], agent_index: int) -> list[str]:
    lane_name = runtime_lane_name_map(project).get(agent_index, "")
    implement_owner = str(resolve_project_runtime_adapter(project).get("role_owners", {}).get("implement") or "Claude")
    lane = next(
        (dict(item) for item in list(runtime_view.get("lanes") or []) if str(item.get("name") or "") == lane_name),
        {},
    )
    if not lane:
        return ["(lane status 없음)"]

    lines = [
        f"name={lane_name}",
        f"state={lane.get('state') or 'UNKNOWN'}",
        f"attachable={bool(lane.get('attachable'))}",
    ]
    if lane.get("pid"):
        lines.append(f"pid={lane['pid']}")
    if lane.get("note"):
        lines.append(f"note={lane['note']}")
    if lane.get("last_heartbeat_at"):
        lines.append(f"heartbeat={lane['last_heartbeat_at']}")
    if lane.get("last_event_at"):
        lines.append(f"event={lane['last_event_at']}")

    lane_events: list[str] = []
    for event in list(runtime_view.get("events") or []):
        payload = dict(event.get("payload") or {})
        event_type = str(event.get("event_type") or "")
        if str(payload.get("lane") or "") != lane_name:
            if not (lane_name == implement_owner and event_type == "control_duplicate_ignored"):
                continue
        subject = str(payload.get("state") or payload.get("result") or payload.get("reason") or "").strip()
        if event_type == "control_duplicate_ignored":
            subject = str(payload.get("reason") or "duplicate_control").strip()
        lane_events.append(f"{event_type} {subject}".strip())

    if lane_events:
        lines.append("")
        lines.append("recent runtime events:")
        lines.extend(lane_events[-6:])
    return lines


def build_snapshot(project: Path, session: str, runtime_view: dict[str, object] | None = None) -> list[str]:
    runtime_view = runtime_view or _runtime_view(project)
    runtime_status = str(runtime_view.get("runtime_state") or "STOPPED")
    watcher_ok = bool(runtime_view.get("watcher_alive"))
    watcher_pid = runtime_view.get("watcher_pid")
    work_name = str(runtime_view.get("work_name") or "—")
    work_mtime = float(runtime_view.get("work_mtime") or 0.0)
    verify_name = str(runtime_view.get("verify_name") or "—")
    verify_mtime = float(runtime_view.get("verify_mtime") or 0.0)
    log_lines = list(runtime_view.get("event_lines") or [])
    active_round = dict(runtime_view.get("active_round") or {})
    control_file = str(runtime_view.get("control_file") or "")
    control_seq = int(runtime_view.get("control_seq") or -1)
    control_status = str(runtime_view.get("control_status") or "none")
    autonomy_mode = str(runtime_view.get("autonomy_mode") or "normal")
    autonomy_reason = str(runtime_view.get("autonomy_reason") or "")
    degraded_reason = str(runtime_view.get("degraded_reason") or "")
    degraded_reasons = [str(item) for item in list(runtime_view.get("degraded_reasons") or []) if str(item)]

    lines = [
        "Pipeline Launcher",
        "=" * 72,
        f"Project : {project}",
        f"Runtime : {runtime_status}",
        f"Runtime helper : {'ALIVE pid=' + str(watcher_pid) if watcher_ok and watcher_pid else 'DEAD'}",
        "",
        f"Latest work  : {work_name} ({time_ago(work_mtime)})" if work_mtime else f"Latest work  : {work_name}",
        f"Latest verify: {verify_name} ({time_ago(verify_mtime)})" if verify_mtime else f"Latest verify: {verify_name}",
        "",
        f"Control: {_control_summary(control_file, control_seq, control_status)}",
        f"Autonomy: {autonomy_mode}" + (f" / {autonomy_reason}" if autonomy_reason else ""),
        f"Round  : {active_round.get('state') or 'IDLE'}" + (
            f" / {active_round.get('job_id')}" if active_round.get("job_id") else ""
        ),
    ]
    if degraded_reasons:
        lines.extend(["", "Degraded:"])
        lines.extend([f"  - {reason}" for reason in degraded_reasons])
    elif degraded_reason:
        lines.extend(["", f"Degraded: {degraded_reason}"])
    lines.extend([
        "",
        "Recent events:",
    ])
    if log_lines:
        lines.extend([f"  {line}" for line in log_lines])
    else:
        lines.append("  (이벤트 없음)")
    pane_lines = pane_snapshots(runtime_view)
    if pane_lines:
        lines.extend([
            "",
            "Agents:",
            *[
                f"  {_fit_text(snap.label, 6)} "
                f"{_fit_text(f'[{snap.status}]', 11)} "
                f"{_fit_text(snap.status_note, 8)} "
                f"{snap.detail}"
                for snap in pane_lines
            ],
        ])
    lines.extend([
        "",
        "Commands:",
        "  s = start",
        "  t = stop",
        "  r = restart",
        "  a = runtime attach",
        "  f = follow (8s live status)",
        "  q = quit",
        "  Enter = refresh",
    ])
    return lines


def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def show_follow_view(project: Path, title: str, seconds: int = 8) -> None:
    session = resolved_session_name(project)
    end_at = time.time() + seconds
    while time.time() < end_at:
        remaining = max(0, int(end_at - time.time()) + 1)
        clear_screen()
        for line in build_snapshot(project, session):
            print(line)
        print("")
        print(f"{title} ({remaining}s)")
        time.sleep(1.0)


def run_line_mode(project: Path) -> None:
    session = resolved_session_name(project)
    message = ""
    while True:
        clear_screen()
        for line in build_snapshot(project, session):
            print(line)
        if message:
            print("")
            print(message)
        try:
            cmd = input("\nCommand [s/t/r/a/q]: ").strip().lower()
        except EOFError:
            break

        message = ""
        if cmd == "":
            continue
        if cmd == "q":
            break
        if cmd == "s":
            message = pipeline_start(project, session)
            if message != "시작 요청됨":
                message = f"START: {message}"
                continue
            ok, status = wait_for_pipeline_ready(project, session)
            show_follow_view(project, "Start 후 live status", seconds=8)
            message = f"START: {status if ok else status}"
            continue
        if cmd == "t":
            message = f"STOP: {pipeline_stop(project, session)}"
            continue
        if cmd == "r":
            restart_message = pipeline_restart(project, session)
            if restart_message != "재시작 요청됨":
                message = f"RESTART: {restart_message}"
                continue
            ok, status = wait_for_pipeline_ready(project, session)
            show_follow_view(project, "Restart 후 live status", seconds=8)
            message = f"RESTART: {status if ok else status}"
            continue
        if cmd == "a":
            current_view = _runtime_view(project)
            if str(current_view.get("runtime_state") or "STOPPED") != "STOPPED":
                message = f"ATTACH: {runtime_attach(project, session)}"
            else:
                message = "ATTACH: runtime이 중지 상태입니다. 먼저 start 하세요."
            continue
        if cmd == "f":
            show_follow_view(project, "Live status", seconds=8)
            message = "FOLLOW: live status 종료"
            continue
        message = f"알 수 없는 명령: {cmd}"


# ── curses TUI ─────────────────────────────────────────────────

def draw(
    stdscr: curses.window,
    project: Path,
    session: str,
    message: str,
    pending_state: str = "",
    focused_agent: int | None = None,
    runtime_view: dict[str, object] | None = None,
) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    if h < 10 or w < 40:
        safe_addstr(stdscr, 0, 0, "터미널을 더 크게 해주세요")
        stdscr.refresh()
        return

    # 색상 설정
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)

    CYAN = curses.color_pair(1)
    GREEN = curses.color_pair(2)
    RED = curses.color_pair(3)
    YELLOW = curses.color_pair(4)
    WHITE = curses.color_pair(5)

    row = 0
    runtime_view = runtime_view or _runtime_view(project)

    # 헤더
    title = " Pipeline Launcher "
    border = "─" * (w - 2)
    safe_addstr(stdscr, row, 0, f"┌{border}┐", CYAN)
    row += 1
    safe_addstr(stdscr, row, 0, f"│{title:^{w-2}}│", CYAN | curses.A_BOLD)
    row += 1
    safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
    row += 1

    # 프로젝트
    proj_str = str(project)
    if len(proj_str) > w - 16:
        proj_str = "..." + proj_str[-(w - 19):]
    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    safe_addstr(stdscr, row, 2, "Project: ", WHITE)
    safe_addstr(stdscr, row, 11, proj_str[:max(0, w - 14)], YELLOW)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    # 상태
    runtime_status = str(runtime_view.get("runtime_state") or "STOPPED")
    w_alive = bool(runtime_view.get("watcher_alive"))
    w_pid = runtime_view.get("watcher_pid")

    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    safe_addstr(stdscr, row, 2, "Runtime: ", WHITE)
    if runtime_status == "RUNNING":
        pipeline_text = "[RUNNING]".ljust(12)
        pipeline_attr = GREEN | curses.A_BOLD
    elif runtime_status == "DEGRADED":
        pipeline_text = "[DEGRADED]".ljust(12)
        pipeline_attr = YELLOW | curses.A_BOLD
    elif runtime_status == "BROKEN":
        pipeline_text = "[BROKEN]".ljust(12)
        pipeline_attr = RED | curses.A_BOLD
    elif runtime_status == "STARTING" or pending_state:
        pipeline_text = "[STARTING]".ljust(12)
        pipeline_attr = YELLOW | curses.A_BOLD
    else:
        pipeline_text = "[STOPPED]".ljust(12)
        pipeline_attr = RED
    safe_addstr(stdscr, row, 12, pipeline_text, pipeline_attr, max_width=12)

    safe_addstr(stdscr, row, 26, "Watcher: ", WHITE)
    if w_alive:
        watcher_text = f"[ALIVE PID:{w_pid}]"
        watcher_attr = GREEN
    elif pending_state:
        watcher_text = "[STARTING]"
        watcher_attr = YELLOW
    else:
        watcher_text = "[DEAD]"
        watcher_attr = RED
    safe_addstr(stdscr, row, 35, watcher_text.ljust(max(0, w - 36)), watcher_attr)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    # 구분선
    safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
    row += 1

    # 키 안내
    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    lane_names = runtime_lane_name_map(project)
    if focused_agent is not None:
        keys = (
            f"[0/Esc] 전체  [1]{lane_names.get(0, '?')} [2]{lane_names.get(1, '?')} [3]{lane_names.get(2, '?')}  "
            f"── 포커스: {lane_names.get(focused_agent, '?')} status"
        )
    else:
        keys = (
            f"[S]Start [T]Stop [R]Restart [A]Attach "
            f"[1]{lane_names.get(0, '?')} [2]{lane_names.get(1, '?')} [3]{lane_names.get(2, '?')} [Q]Quit"
        )
    safe_addstr(stdscr, row, 2, keys[:max(0, w - 4)], WHITE | curses.A_BOLD)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    # 구분선
    safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
    row += 1

    # 최신 파일
    work_name = str(runtime_view.get("work_name") or "—")
    work_mtime = float(runtime_view.get("work_mtime") or 0.0)
    verify_name = str(runtime_view.get("verify_name") or "—")
    verify_mtime = float(runtime_view.get("verify_mtime") or 0.0)
    control_file = str(runtime_view.get("control_file") or "")
    control_seq = int(runtime_view.get("control_seq") or -1)
    control_status = str(runtime_view.get("control_status") or "none")
    autonomy_mode = str(runtime_view.get("autonomy_mode") or "normal")
    autonomy_reason = str(runtime_view.get("autonomy_reason") or "")

    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    safe_addstr(stdscr, row, 2, "Latest work:   ", WHITE)
    work_display = f"{work_name} ({time_ago(work_mtime)})" if work_mtime else work_name
    safe_addstr(stdscr, row, 17, work_display[:max(0, w - 20)], YELLOW)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    safe_addstr(stdscr, row, 2, "Latest verify: ", WHITE)
    verify_display = f"{verify_name} ({time_ago(verify_mtime)})" if verify_mtime else verify_name
    safe_addstr(stdscr, row, 17, verify_display[:max(0, w - 20)], YELLOW)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    safe_addstr(stdscr, row, 2, "Control:       ", WHITE)
    control_display = _control_summary(control_file, control_seq, control_status)
    control_attr = YELLOW if control_status == "needs_operator" else WHITE
    safe_addstr(stdscr, row, 17, control_display[:max(0, w - 20)], control_attr)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    safe_addstr(stdscr, row, 2, "Autonomy:      ", WHITE)
    autonomy_display = autonomy_mode + (f" / {autonomy_reason}" if autonomy_reason else "")
    autonomy_attr = YELLOW if autonomy_mode not in {"", "normal"} else WHITE
    safe_addstr(stdscr, row, 17, autonomy_display[:max(0, w - 20)], autonomy_attr)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    # 구분선
    safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
    row += 1

    # 로그
    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    safe_addstr(stdscr, row, 2, "Recent log:", WHITE)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    log_lines = list(runtime_view.get("event_lines") or [])[:3]
    for log_line in log_lines:
        if row >= h - 3:
            break
        # 타임스탬프 부분은 시간만 추출
        display = log_line
        if len(display) > w - 6:
            display = display[:w - 9] + "..."
        safe_addstr(stdscr, row, 0, "│ ", CYAN)
        safe_addstr(stdscr, row, 2, f"  {display}", curses.color_pair(5) | curses.A_DIM)
        safe_addstr(stdscr, row, w - 1, "│", CYAN)
        row += 1

    # agent 상태
    snapshots = pane_snapshots(runtime_view)
    if snapshots and row < h - 5:
        safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
        row += 1
        safe_addstr(stdscr, row, 0, "│ ", CYAN)
        safe_addstr(stdscr, row, 2, "Agents:", WHITE)
        safe_addstr(stdscr, row, w - 1, "│", CYAN)
        row += 1

        status_color = {
            "WORKING": GREEN | curses.A_BOLD,
            "READY": GREEN,
            "BOOTING": YELLOW,
            "DEAD": RED,
            "OFF": WHITE,
        }
        for i, snap in enumerate(snapshots):
            if row >= h - 4:
                break
            # 포커스된 agent 또는 WORKING agent 강조
            is_focused = (focused_agent == i)
            is_working = (snap.status == "WORKING")
            label_attr = WHITE | curses.A_BOLD if (is_focused or is_working) else WHITE
            bracket_attr = status_color.get(snap.status, WHITE)
            if is_focused:
                bracket_attr |= curses.A_BOLD
            indicator = "▶" if is_focused else "●" if is_working else " "
            label_col = 2
            label_width = 10
            status_col = label_col + label_width + 1
            status_width = 11
            duration_col = status_col + status_width + 1
            duration_width = 8
            detail_col = duration_col + duration_width + 1
            safe_addstr(stdscr, row, 0, "│ ", CYAN)
            safe_addstr(stdscr, row, label_col, _fit_text(f"{indicator} {snap.label}", label_width), label_attr)
            safe_addstr(stdscr, row, status_col, _fit_text(f"[{snap.status}]", status_width), bracket_attr)
            safe_addstr(stdscr, row, duration_col, _fit_text(snap.status_note, duration_width), bracket_attr)
            detail_text = snap.detail if (focused_agent is None or is_focused or is_working) else ""
            safe_addstr(
                stdscr,
                row,
                detail_col,
                detail_text[:max(0, w - detail_col - 1)],
                curses.color_pair(5) | curses.A_DIM,
            )
            safe_addstr(stdscr, row, w - 1, "│", CYAN)
            row += 1

    # ── Focused agent runtime detail viewer ──
    if focused_agent is not None and row < h - 4:
        safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
        row += 1
        viewer_title = f"  {lane_names.get(focused_agent, '?')} runtime detail (read-only)"
        safe_addstr(stdscr, row, 0, "│ ", CYAN)
        safe_addstr(stdscr, row, 2, viewer_title, WHITE | curses.A_BOLD)
        safe_addstr(stdscr, row, w - 1, "│", CYAN)
        row += 1

        margin = 3          # 좌우 여백 (│ + 공백 + 내용 ... 공백 + │)
        content_width = w - margin - 1  # 실제 텍스트 폭

        if content_width < 10:
            content_width = 10

        available_rows = h - row - 3  # 메시지 + 하단 테두리용 여유
        details = focused_lane_details(project, runtime_view, focused_agent)
        display = details[-available_rows:] if len(details) > available_rows else details

        for dline in display:
            if row >= h - 3:
                break
            truncated = dline[:content_width] if len(dline) > content_width else dline
            safe_addstr(stdscr, row, 0, "│ ", CYAN)
            safe_addstr(stdscr, row, margin, truncated, curses.color_pair(5))
            safe_addstr(stdscr, row, w - 1, "│", CYAN)
            row += 1

    # 메시지 영역
    if row < h - 2:
        safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
        row += 1
    if row < h - 1 and message:
        safe_addstr(stdscr, row, 0, "│ ", CYAN)
        safe_addstr(stdscr, row, 2, message[:max(0, w - 4)], YELLOW)
        safe_addstr(stdscr, row, w - 1, "│", CYAN)
        row += 1

    # 하단 테두리
    if row < h:
        safe_addstr(stdscr, row, 0, f"└{border}┘", CYAN)

    stdscr.refresh()


def main(stdscr: curses.window) -> None:
    project, _ = parse_args()
    session = resolved_session_name(project)

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(1000)  # 1초 폴링

    message = ""
    message_expire = 0.0
    pending_state = ""
    pending_state_expire = 0.0
    pending_started_at = 0.0
    focused_agent: int | None = None  # None=전체, 0=Claude, 1=Codex, 2=Gemini

    while True:
        # 메시지 만료
        if message and time.time() > message_expire:
            message = ""

        if pending_state and time.time() > pending_state_expire:
            pending_state = ""

        runtime_view = _runtime_view(project)
        current_runtime_state = str(runtime_view.get("runtime_state") or "STOPPED")
        ready_lanes = [
            lane
            for lane in list(runtime_view.get("lanes") or [])
            if bool(lane.get("attachable")) and str(lane.get("state") or "") in {"READY", "WORKING"}
        ]
        if current_runtime_state in {"RUNNING", "DEGRADED"} and ready_lanes:
            if message.startswith("START failed:"):
                message = ""
            pending_state = ""
            pending_started_at = 0.0
        elif current_runtime_state == "BROKEN":
            reason = str(runtime_view.get("degraded_reason") or "runtime broken")
            message = f"START failed: {reason}"
            message_expire = time.time() + 12
            pending_state = ""
            pending_started_at = 0.0
        elif pending_state and pending_started_at and time.time() - pending_started_at > _START_READY_TIMEOUT_SEC:
            message = "START failed: runtime READY 조건을 만족하지 못했습니다"
            message_expire = time.time() + 12
            pending_state = ""
            pending_started_at = 0.0

        display_message = message
        if not display_message and pending_state:
            display_message = pending_state

        # 포커스 모드에서는 더 빠른 폴링으로 실시간감 제공
        stdscr.timeout(500 if focused_agent is not None else 1000)
        draw(stdscr, project, session, display_message, pending_state, focused_agent, runtime_view)

        key = stdscr.getch()
        if key == -1:
            continue

        ch = chr(key).lower() if 0 <= key < 256 else ""

        if ch == "q":
            break
        elif ch == "s":
            msg = pipeline_start(project, session)
            message = f"START: {msg}"
            message_expire = time.time() + 5
            if msg == "시작 요청됨":
                pending_state = "초기화 중... runtime lane readiness를 확인하는 중입니다."
                pending_state_expire = time.time() + _START_READY_TIMEOUT_SEC
                pending_started_at = time.time()
            else:
                pending_state = ""
                pending_started_at = 0.0
        elif ch == "t":
            msg = pipeline_stop(project, session)
            message = f"STOP: {msg}"
            message_expire = time.time() + 5
            pending_state = ""
            pending_started_at = 0.0
        elif ch == "r":
            message = "RESTART: 재시작 중..."
            message_expire = time.time() + 10
            draw(stdscr, project, session, message, pending_state, focused_agent, runtime_view)
            msg = pipeline_restart(project, session)
            message = f"RESTART: {msg}"
            message_expire = time.time() + 5
            if msg == "재시작 요청됨":
                pending_state = "초기화 중... runtime lane readiness를 확인하는 중입니다."
                pending_state_expire = time.time() + _START_READY_TIMEOUT_SEC
                pending_started_at = time.time()
            else:
                pending_state = ""
                pending_started_at = 0.0
        elif ch == "a":
            if str(runtime_view.get("runtime_state") or "STOPPED") != "STOPPED":
                # curses를 잠시 내리고 runtime attach를 실행한 뒤 복귀합니다.
                curses.endwin()
                attach_message = runtime_attach(project, session)
                stdscr = curses.initscr()
                curses.curs_set(0)
                stdscr.nodelay(True)
                stdscr.timeout(1000)
                curses.start_color()
                message = f"ATTACH: {attach_message}"
                message_expire = time.time() + 6
            else:
                message = "ATTACH: 실행 중인 runtime이 없습니다. 먼저 Start하세요."
                message_expire = time.time() + 3
        elif ch == "1":
            focused_agent = 0 if focused_agent != 0 else None
        elif ch == "2":
            focused_agent = 1 if focused_agent != 1 else None
        elif ch == "3":
            focused_agent = 2 if focused_agent != 2 else None
        elif ch == "0" or key == 27:  # 0 또는 Esc
            focused_agent = None


if __name__ == "__main__":
    project, line_mode = parse_args()
    try:
        if line_mode:
            run_line_mode(project)
        else:
            curses.wrapper(main)
    except Exception:
        log_path = launcher_error_log(project)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        raise
