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
  A — tmux attach (curses 일시 해제)
  Q — launcher 종료
"""

from __future__ import annotations

import curses
import datetime as dt
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import NamedTuple


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


SESSION_NAME = "ai-pipeline"


def launcher_error_log(project: Path) -> Path:
    return project / ".pipeline" / "logs" / "experimental" / "pipeline-launcher-error.log"


def launcher_start_log(project: Path) -> Path:
    return project / ".pipeline" / "logs" / "experimental" / "pipeline-launcher-start.log"


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


# ── 상태 조회 ──────────────────────────────────────────────────

def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str]:
    """명령 실행 후 (returncode, stdout) 반환."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return -1, ""


def tmux_alive() -> bool:
    code, _ = _run(["tmux", "has-session", "-t", SESSION_NAME])
    return code == 0


def watcher_alive(project: Path) -> tuple[bool, int | None]:
    pid_path = project / ".pipeline" / "experimental.pid"
    if not pid_path.exists():
        return False, None
    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, 0)
        return True, pid
    except (ValueError, OSError):
        return False, None


def latest_md(directory: Path) -> tuple[str, float]:
    """디렉터리 내 최신 .md 파일명과 mtime 반환."""
    best_path: Path | None = None
    best_mtime: float = 0.0
    if not directory.exists():
        return "—", 0.0
    for md in directory.rglob("*.md"):
        try:
            mt = md.stat().st_mtime
            if mt > best_mtime:
                best_mtime = mt
                best_path = md
        except OSError:
            continue
    if best_path is None:
        return "—", 0.0
    try:
        rel = str(best_path.relative_to(directory))
    except ValueError:
        rel = best_path.name
    return rel, best_mtime


def watcher_log_tail(project: Path, lines: int = 3) -> list[str]:
    log_path = project / ".pipeline" / "logs" / "experimental" / "watcher.log"
    if not log_path.exists():
        return start_log_tail(project, lines=lines)
    try:
        all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        # suppressed/A/B ratio 제외
        filtered = [
            l for l in all_lines
            if "suppressed" not in l and "A/B ratio" not in l
        ]
        return filtered[-lines:] if filtered else start_log_tail(project, lines=lines)
    except OSError:
        return ["(읽기 실패)"]


ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
WATCHER_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")


def start_log_tail(project: Path, lines: int = 3) -> list[str]:
    log_path = launcher_start_log(project)
    if not log_path.exists():
        return ["(이벤트 없음)"]
    try:
        all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        cleaned = [ANSI_RE.sub("", line).strip() for line in all_lines]
        cleaned = [line for line in cleaned if line]
        return cleaned[-lines:] if cleaned else ["(이벤트 없음)"]
    except OSError:
        return ["(읽기 실패)"]


def time_ago(mtime: float) -> str:
    if mtime == 0:
        return ""
    diff = int(time.time() - mtime)
    if diff < 60:
        return f"{diff}초 전"
    if diff < 3600:
        return f"{diff // 60}분 전"
    return f"{diff // 3600}시간 전"


def format_elapsed(seconds: float) -> str:
    total = max(0, int(seconds))
    mins, secs = divmod(total, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def watcher_runtime_hints(project: Path) -> dict[str, tuple[str, str]]:
    log_path = project / ".pipeline" / "logs" / "experimental" / "watcher.log"
    if not log_path.exists():
        return {}

    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-300:]
    except OSError:
        return {}

    claude_started_at: float | None = None
    claude_done = False
    codex_started_at: float | None = None
    codex_done = False
    gemini_started_at: float | None = None
    gemini_done = False

    for line in lines:
        ts_match = WATCHER_TS_RE.match(line)
        if not ts_match:
            continue
        try:
            timestamp = dt.datetime.fromisoformat(ts_match.group(1)).timestamp()
        except ValueError:
            continue

        if (
            "notify_claude" in line
            or "send-keys" in line and "pane_type=claude" in line
            or "waiting_for_claude" in line
        ):
            claude_started_at = timestamp
            claude_done = False
        elif (
            "claude activity detected by snapshot diff" in line
            or ("new job:" in line and claude_started_at is not None)
        ):
            claude_done = True

        if (
            "lease acquired: slot=slot_verify" in line
            or "dispatching codex prompt" in line
            or "VERIFY_PENDING → VERIFY_RUNNING" in line
        ):
            codex_started_at = timestamp
            codex_done = False
        elif (
            "codex task completed" in line
            or "lease released: slot=slot_verify" in line
            or "VERIFY_RUNNING → VERIFY_DONE" in line
        ):
            codex_done = True

        if (
            "notify_gemini" in line
            or "gemini response activity detected" in line
        ):
            gemini_started_at = timestamp
            gemini_done = False
        elif "gemini advice updated" in line:
            gemini_done = True

    hints: dict[str, tuple[str, str]] = {}
    now = time.time()
    if claude_started_at is not None and not claude_done:
        hints["Claude"] = ("WORKING", format_elapsed(now - claude_started_at))
    elif claude_done:
        hints["Claude"] = ("READY", "")
    if codex_started_at is not None and not codex_done:
        hints["Codex"] = ("WORKING", format_elapsed(now - codex_started_at))
    elif codex_done:
        hints["Codex"] = ("READY", "")
    if gemini_started_at is not None and not gemini_done:
        hints["Gemini"] = ("WORKING", format_elapsed(now - gemini_started_at))
    elif gemini_done:
        hints["Gemini"] = ("READY", "")
    return hints


# ── 파이프라인 제어 ────────────────────────────────────────────

def pipeline_start(project: Path) -> str:
    script = project / "start-pipeline.sh"
    if not script.exists():
        return "start-pipeline.sh 없음"
    log_path = launcher_start_log(project)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("", encoding="utf-8")
    # launcher에서는 start-pipeline.sh의 tmux attach를 건너뛰고 백그라운드로 기동합니다.
    with log_path.open("w", encoding="utf-8") as logf:
        subprocess.Popen(
            ["bash", "-l", str(script), str(project), "--mode", "experimental", "--no-attach"],
            cwd=str(project),
            stdout=logf,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    return "시작 요청됨"


def pipeline_stop(project: Path) -> str:
    script = project / "stop-pipeline.sh"
    if not script.exists():
        return "stop-pipeline.sh 없음"
    subprocess.run(
        ["bash", str(script), str(project)],
        capture_output=True, timeout=15,
    )
    return "중지 완료"


def pipeline_restart(project: Path) -> str:
    pipeline_stop(project)
    time.sleep(2)
    pipeline_start(project)
    return "재시작 요청됨"


def tmux_attach() -> None:
    """curses를 일시 해제하고 tmux attach 실행."""
    os.system(f"tmux attach -t {SESSION_NAME}")


def wait_for_pipeline_ready(project: Path, timeout_sec: float = 12.0) -> tuple[bool, str]:
    started_at = time.time()
    while time.time() - started_at < timeout_sec:
        session_ok = tmux_alive()
        watcher_ok, _ = watcher_alive(project)
        if session_ok and watcher_ok:
            return True, "기동 완료"
        time.sleep(1.0)
    tail = start_log_tail(project, lines=1)
    reason = tail[-1] if tail else "(원인 미상)"
    return False, f"START failed: {reason}"


class AgentSnapshot(NamedTuple):
    label: str
    status: str
    status_note: str
    detail: str


def extract_working_note(lines: list[str]) -> str:
    for line in reversed(lines[-80:]):
        match = re.search(r"Working \(([^)]*)", line, re.IGNORECASE)
        if match:
            note = match.group(1).split("•", 1)[0].strip(" )…")
            if note:
                return note
        match = re.search(r"Cascading(?:…|\.{3})\s*\(([^)]*)", line, re.IGNORECASE)
        if match:
            note = match.group(1).strip(" )…")
            if note:
                return note
        match = re.search(r"Lollygagging(?:…|\.{3})\s*\(([^)]*)", line, re.IGNORECASE)
        if match:
            note = match.group(1).strip(" )…")
            if note:
                return note
        lowered = line.lower()
        if "background terminal" in lowered or "waiting for background" in lowered:
            return "bg-task"
    return ""


def detect_agent_status(label: str, lines: list[str]) -> tuple[str, str, str]:
    recent_lines = lines[-80:]
    text = "\n".join(recent_lines)
    lower = text.lower()

    if not lines:
        return "DEAD", "", "(출력 없음)"

    if (
        "working (" in lower
        or "background terminal" in lower
        or "waiting for background" in lower
        or "waited for background" in lower
        or "cascading" in lower
        or "lollygagging" in lower
        or "without interrupting claude's current work" in lower
    ):
        note = extract_working_note(lines)
        return "WORKING", note, " / ".join(lines[-2:]) if len(lines) >= 2 else lines[-1]
    if label == "Codex" and ("› " in text or "openai codex" in lower):
        return "READY", "", " / ".join(lines[-2:]) if len(lines) >= 2 else lines[-1]
    if label == "Claude" and ("❯" in text or "claude code" in lower or "bypass permissions" in lower):
        return "READY", "", " / ".join(lines[-2:]) if len(lines) >= 2 else lines[-1]
    if label == "Gemini" and ("type your message" in lower or "gemini cli" in lower or "workspace" in lower):
        return "READY", "", " / ".join(lines[-2:]) if len(lines) >= 2 else lines[-1]
    return "BOOTING", "", " / ".join(lines[-2:]) if len(lines) >= 2 else lines[-1]


def pane_snapshots(project: Path) -> list[AgentSnapshot]:
    code, output = _run(
        [
            "tmux",
            "list-panes",
            "-t",
            f"{SESSION_NAME}:0",
            "-F",
            "#{pane_index}|#{pane_id}|#{pane_dead}",
        ],
        timeout=2.0,
    )
    if code != 0 or not output:
        return []

    lane_names = {0: "Claude", 1: "Codex", 2: "Gemini"}
    runtime_hints = watcher_runtime_hints(project)
    summaries: list[AgentSnapshot] = []
    for raw in output.splitlines():
        try:
            pane_index_s, pane_id, pane_dead = raw.split("|", 2)
            pane_index = int(pane_index_s)
        except ValueError:
            continue

        label = lane_names.get(pane_index, f"Pane {pane_index}")
        if pane_dead == "1":
            summaries.append(AgentSnapshot(label, "DEAD", "", "(pane dead)"))
            continue

        capture_code, captured = _run(
            ["tmux", "capture-pane", "-pt", pane_id, "-S", "-60"],
            timeout=2.0,
        )
        if capture_code != 0 or not captured:
            summaries.append(AgentSnapshot(label, "BOOTING", "", "(출력 대기 중)"))
            continue

        lines = [ANSI_RE.sub("", line).strip() for line in captured.splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            summaries.append(AgentSnapshot(label, "BOOTING", "", "(출력 대기 중)"))
            continue
        status, status_note, snippet = detect_agent_status(label, lines)
        hint = runtime_hints.get(label)
        if hint:
            hint_status, hint_note = hint
            if hint_status == "WORKING":
                # watcher가 작업 중임을 감지했다면 pane READY보다 WORKING을 우선합니다.
                status = "WORKING"
                if not status_note:
                    status_note = hint_note
            elif hint_status == "READY" and status == "BOOTING":
                # pane 출력이 아직 얕을 때만 watcher의 READY 힌트로 보정합니다.
                status = "READY"
                status_note = ""

        if len(snippet) > 110:
            snippet = snippet[:107] + "..."
        summaries.append(AgentSnapshot(label, status, status_note, snippet))
    return summaries


def capture_agent_pane(agent_index: int, lines: int = 200) -> list[str]:
    """지정 agent pane의 최근 출력을 가져옵니다."""
    code, output = _run(
        ["tmux", "list-panes", "-t", f"{SESSION_NAME}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
        timeout=2.0,
    )
    if code != 0 or not output:
        return ["(tmux 세션 없음)"]
    for raw in output.splitlines():
        try:
            idx_s, pane_id, dead = raw.split("|", 2)
            if int(idx_s) == agent_index:
                if dead == "1":
                    return ["(pane dead)"]
                cap_code, captured = _run(
                    ["tmux", "capture-pane", "-pt", pane_id, "-S", f"-{lines}"],
                    timeout=3.0,
                )
                if cap_code != 0 or not captured:
                    return ["(출력 없음)"]
                cleaned = [ANSI_RE.sub("", l).rstrip() for l in captured.splitlines()]
                return [l for l in cleaned if l]
        except ValueError:
            continue
    return ["(pane 없음)"]


def build_snapshot(project: Path) -> list[str]:
    session_ok = tmux_alive()
    watcher_ok, watcher_pid = watcher_alive(project)
    work_name, work_mtime = latest_md(project / "work")
    verify_name, verify_mtime = latest_md(project / "verify")
    log_lines = watcher_log_tail(project, lines=3)

    lines = [
        "Pipeline Launcher",
        "=" * 72,
        f"Project : {project}",
        f"Pipeline: {'RUNNING' if session_ok else 'STOPPED'}",
        f"Watcher : {'ALIVE pid=' + str(watcher_pid) if watcher_ok and watcher_pid else 'DEAD'}",
        "",
        f"Latest work  : {work_name} ({time_ago(work_mtime)})" if work_mtime else f"Latest work  : {work_name}",
        f"Latest verify: {verify_name} ({time_ago(verify_mtime)})" if verify_mtime else f"Latest verify: {verify_name}",
        "",
        "Recent log:",
    ]
    if log_lines:
        lines.extend([f"  {line}" for line in log_lines])
    else:
        lines.append("  (이벤트 없음)")
    pane_lines = pane_snapshots(project)
    if pane_lines:
        lines.extend([
            "",
            "Agents:",
            *[
                f"  {snap.label:<6} "
                f"[{snap.status}{(' ' + snap.status_note) if snap.status_note else '':<14}] "
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
        "  a = tmux attach",
        "  f = follow (8s live view)",
        "  q = quit",
        "  Enter = refresh",
    ])
    return lines


def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def show_follow_view(project: Path, title: str, seconds: int = 8) -> None:
    end_at = time.time() + seconds
    while time.time() < end_at:
        remaining = max(0, int(end_at - time.time()) + 1)
        clear_screen()
        for line in build_snapshot(project):
            print(line)
        print("")
        print(f"{title} ({remaining}s)")
        time.sleep(1.0)


def run_line_mode(project: Path) -> None:
    message = ""
    while True:
        clear_screen()
        for line in build_snapshot(project):
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
            message = pipeline_start(project)
            ok, status = wait_for_pipeline_ready(project)
            show_follow_view(project, "Start 후 live status", seconds=8)
            message = f"START: {status if ok else status}"
            continue
        if cmd == "t":
            message = f"STOP: {pipeline_stop(project)}"
            continue
        if cmd == "r":
            pipeline_stop(project)
            time.sleep(2)
            pipeline_start(project)
            ok, status = wait_for_pipeline_ready(project)
            show_follow_view(project, "Restart 후 live status", seconds=8)
            message = f"RESTART: {status if ok else status}"
            continue
        if cmd == "a":
            if tmux_alive():
                tmux_attach()
                message = "ATTACH: tmux에서 돌아왔습니다."
            else:
                message = "ATTACH: tmux 세션이 없습니다. 먼저 start 하세요."
            continue
        if cmd == "f":
            show_follow_view(project, "Live status", seconds=8)
            message = "FOLLOW: live status 종료"
            continue
        message = f"알 수 없는 명령: {cmd}"


# ── curses TUI ─────────────────────────────────────────────────

def draw(stdscr: curses.window, project: Path, message: str, pending_state: str = "", focused_agent: int | None = None) -> None:
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
    session_ok = tmux_alive()
    w_alive, w_pid = watcher_alive(project)

    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    safe_addstr(stdscr, row, 2, "Pipeline: ", WHITE)
    if session_ok:
        pipeline_text = "[RUNNING]".ljust(12)
        pipeline_attr = GREEN | curses.A_BOLD
    elif pending_state:
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
    if focused_agent is not None:
        agent_names = {0: "Claude", 1: "Codex", 2: "Gemini"}
        keys = f"[0/Esc] 전체  [1]Claude [2]Codex [3]Gemini  ── 포커스: {agent_names.get(focused_agent, '?')}"
    else:
        keys = "[S]Start [T]Stop [R]Restart [A]Attach [1]Claude [2]Codex [3]Gemini [Q]Quit"
    safe_addstr(stdscr, row, 2, keys[:max(0, w - 4)], WHITE | curses.A_BOLD)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    # 구분선
    safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
    row += 1

    # 최신 파일
    work_name, work_mtime = latest_md(project / "work")
    verify_name, verify_mtime = latest_md(project / "verify")

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

    # 구분선
    safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
    row += 1

    # 로그
    safe_addstr(stdscr, row, 0, "│ ", CYAN)
    safe_addstr(stdscr, row, 2, "Recent log:", WHITE)
    safe_addstr(stdscr, row, w - 1, "│", CYAN)
    row += 1

    log_lines = watcher_log_tail(project, lines=3)
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
    snapshots = pane_snapshots(project)
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
        }
        for i, snap in enumerate(snapshots):
            if row >= h - 4:
                break
            status_text = f"{snap.status}{(' ' + snap.status_note) if snap.status_note else ''}"
            # 포커스된 agent 또는 WORKING agent 강조
            is_focused = (focused_agent == i)
            is_working = (snap.status == "WORKING")
            label_attr = WHITE | curses.A_BOLD if (is_focused or is_working) else WHITE
            bracket_attr = status_color.get(snap.status, WHITE)
            if is_focused:
                bracket_attr |= curses.A_BOLD
            indicator = "▶" if is_focused else "●" if is_working else " "
            safe_addstr(stdscr, row, 0, "│ ", CYAN)
            safe_addstr(stdscr, row, 2, f"{indicator} {snap.label:<6}", label_attr)
            safe_addstr(stdscr, row, 12, f"[{status_text:<14}]", bracket_attr)
            safe_addstr(stdscr, row, 29, snap.detail[:max(0, w - 32)], curses.color_pair(5) | curses.A_DIM)
            safe_addstr(stdscr, row, w - 1, "│", CYAN)
            row += 1

    # ── Focused agent read-only viewer ──
    if focused_agent is not None and row < h - 4:
        safe_addstr(stdscr, row, 0, f"├{border}┤", CYAN)
        row += 1
        agent_names = {0: "Claude", 1: "Codex", 2: "Gemini"}
        viewer_title = f"  {agent_names.get(focused_agent, '?')} pane output (read-only)"
        safe_addstr(stdscr, row, 0, "│ ", CYAN)
        safe_addstr(stdscr, row, 2, viewer_title, WHITE | curses.A_BOLD)
        safe_addstr(stdscr, row, w - 1, "│", CYAN)
        row += 1

        available_lines = h - row - 3  # 메시지 + 하단 테두리용 여유
        pane_lines = capture_agent_pane(focused_agent, lines=available_lines + 20)
        # 최근 줄을 available_lines만큼 표시
        display = pane_lines[-available_lines:] if len(pane_lines) > available_lines else pane_lines
        for pline in display:
            if row >= h - 3:
                break
            truncated = pline[:w - 4] if len(pline) > w - 4 else pline
            safe_addstr(stdscr, row, 0, "│ ", CYAN)
            safe_addstr(stdscr, row, 2, truncated, curses.color_pair(5))
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

        session_ok = tmux_alive()
        watcher_ok, _ = watcher_alive(project)
        if session_ok or watcher_ok:
            pending_state = ""
            pending_started_at = 0.0
        elif pending_state and pending_started_at and time.time() - pending_started_at > 12:
            tail = start_log_tail(project, lines=1)
            reason = tail[-1] if tail else "(원인 미상)"
            message = f"START failed: {reason}"
            message_expire = time.time() + 12
            pending_state = ""
            pending_started_at = 0.0

        display_message = message
        if not display_message and pending_state:
            display_message = pending_state

        # 포커스 모드에서는 더 빠른 폴링으로 실시간감 제공
        stdscr.timeout(500 if focused_agent is not None else 1000)
        draw(stdscr, project, display_message, pending_state, focused_agent)

        key = stdscr.getch()
        if key == -1:
            continue

        ch = chr(key).lower() if 0 <= key < 256 else ""

        if ch == "q":
            break
        elif ch == "s":
            msg = pipeline_start(project)
            message = f"START: {msg}"
            message_expire = time.time() + 5
            pending_state = "초기화 중... tmux/watcher 기동까지 몇 초 걸릴 수 있습니다."
            pending_state_expire = time.time() + 15
            pending_started_at = time.time()
        elif ch == "t":
            msg = pipeline_stop(project)
            message = f"STOP: {msg}"
            message_expire = time.time() + 5
            pending_state = ""
            pending_started_at = 0.0
        elif ch == "r":
            message = "RESTART: 재시작 중..."
            message_expire = time.time() + 10
            draw(stdscr, project, message, pending_state, focused_agent)
            msg = pipeline_restart(project)
            message = f"RESTART: {msg}"
            message_expire = time.time() + 5
            pending_state = "초기화 중... tmux/watcher 기동까지 몇 초 걸릴 수 있습니다."
            pending_state_expire = time.time() + 15
            pending_started_at = time.time()
        elif ch == "a":
            if tmux_alive():
                # curses 일시 해제 → tmux attach → 복귀
                curses.endwin()
                tmux_attach()
                stdscr = curses.initscr()
                curses.curs_set(0)
                stdscr.nodelay(True)
                stdscr.timeout(1000)
                curses.start_color()
                message = "ATTACH: tmux에서 돌아왔습니다 (Ctrl+B, D로 detach)"
                message_expire = time.time() + 5
            else:
                message = "ATTACH: tmux 세션이 없습니다. 먼저 Start하세요."
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
