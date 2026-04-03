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
import os
import subprocess
import sys
import time
from pathlib import Path


# ── 프로젝트 경로 결정 ────────────────────────────────────────

def resolve_project_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    env = os.environ.get("PROJECT_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


SESSION_NAME = "ai-pipeline"


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
        return ["(로그 없음)"]
    try:
        all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        # suppressed/A/B ratio 제외
        filtered = [
            l for l in all_lines
            if "suppressed" not in l and "A/B ratio" not in l
        ]
        return filtered[-lines:] if filtered else ["(이벤트 없음)"]
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


# ── 파이프라인 제어 ────────────────────────────────────────────

def pipeline_start(project: Path) -> str:
    script = project / "start-pipeline.sh"
    if not script.exists():
        return "start-pipeline.sh 없음"
    # sed '$d'로 마지막 줄(tmux attach) 제거 후 실행
    subprocess.Popen(
        ["bash", "-c", f"sed '$d' '{script}' | bash -s '{project}' --mode experimental"],
        cwd=str(project),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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


# ── curses TUI ─────────────────────────────────────────────────

def draw(stdscr: curses.window, project: Path, message: str) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    if h < 10 or w < 40:
        stdscr.addstr(0, 0, "터미널을 더 크게 해주세요")
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
    stdscr.addstr(row, 0, f"┌{border}┐", CYAN)
    row += 1
    stdscr.addstr(row, 0, f"│{title:^{w-2}}│", CYAN | curses.A_BOLD)
    row += 1
    stdscr.addstr(row, 0, f"├{border}┤", CYAN)
    row += 1

    # 프로젝트
    proj_str = str(project)
    if len(proj_str) > w - 16:
        proj_str = "..." + proj_str[-(w - 19):]
    stdscr.addstr(row, 0, f"│ ", CYAN)
    stdscr.addstr(row, 2, "Project: ", WHITE)
    stdscr.addstr(row, 11, proj_str[:w-14], YELLOW)
    stdscr.addstr(row, w - 1, "│", CYAN)
    row += 1

    # 상태
    session_ok = tmux_alive()
    w_alive, w_pid = watcher_alive(project)

    stdscr.addstr(row, 0, f"│ ", CYAN)
    stdscr.addstr(row, 2, "Pipeline: ", WHITE)
    if session_ok:
        stdscr.addstr(row, 12, "● Running", GREEN | curses.A_BOLD)
    else:
        stdscr.addstr(row, 12, "■ Stopped", RED)

    stdscr.addstr(row, 26, "Watcher: ", WHITE)
    if w_alive:
        stdscr.addstr(row, 35, f"● Alive (PID:{w_pid})", GREEN)
    else:
        stdscr.addstr(row, 35, "✗ Dead", RED)
    stdscr.addstr(row, w - 1, "│", CYAN)
    row += 1

    # 구분선
    stdscr.addstr(row, 0, f"├{border}┤", CYAN)
    row += 1

    # 키 안내
    stdscr.addstr(row, 0, f"│ ", CYAN)
    keys = "[S] Start  [T] Stop  [R] Restart  [A] Attach  [Q] Quit"
    stdscr.addstr(row, 2, keys[:w-4], WHITE | curses.A_BOLD)
    stdscr.addstr(row, w - 1, "│", CYAN)
    row += 1

    # 구분선
    stdscr.addstr(row, 0, f"├{border}┤", CYAN)
    row += 1

    # 최신 파일
    work_name, work_mtime = latest_md(project / "work")
    verify_name, verify_mtime = latest_md(project / "verify")

    stdscr.addstr(row, 0, f"│ ", CYAN)
    stdscr.addstr(row, 2, "Latest work:   ", WHITE)
    work_display = f"{work_name} ({time_ago(work_mtime)})" if work_mtime else work_name
    stdscr.addstr(row, 17, work_display[:w-20], YELLOW)
    stdscr.addstr(row, w - 1, "│", CYAN)
    row += 1

    stdscr.addstr(row, 0, f"│ ", CYAN)
    stdscr.addstr(row, 2, "Latest verify: ", WHITE)
    verify_display = f"{verify_name} ({time_ago(verify_mtime)})" if verify_mtime else verify_name
    stdscr.addstr(row, 17, verify_display[:w-20], YELLOW)
    stdscr.addstr(row, w - 1, "│", CYAN)
    row += 1

    # 구분선
    stdscr.addstr(row, 0, f"├{border}┤", CYAN)
    row += 1

    # 로그
    stdscr.addstr(row, 0, f"│ ", CYAN)
    stdscr.addstr(row, 2, "Recent log:", WHITE)
    stdscr.addstr(row, w - 1, "│", CYAN)
    row += 1

    log_lines = watcher_log_tail(project, lines=3)
    for log_line in log_lines:
        if row >= h - 3:
            break
        # 타임스탬프 부분은 시간만 추출
        display = log_line
        if len(display) > w - 6:
            display = display[:w - 9] + "..."
        stdscr.addstr(row, 0, f"│ ", CYAN)
        stdscr.addstr(row, 2, f"  {display}", curses.color_pair(5) | curses.A_DIM)
        stdscr.addstr(row, w - 1, "│", CYAN)
        row += 1

    # 메시지 영역
    if row < h - 2:
        stdscr.addstr(row, 0, f"├{border}┤", CYAN)
        row += 1
    if row < h - 1 and message:
        stdscr.addstr(row, 0, f"│ ", CYAN)
        stdscr.addstr(row, 2, message[:w-4], YELLOW)
        stdscr.addstr(row, w - 1, "│", CYAN)
        row += 1

    # 하단 테두리
    if row < h:
        stdscr.addstr(row, 0, f"└{border}┘", CYAN)

    stdscr.refresh()


def main(stdscr: curses.window) -> None:
    project = resolve_project_root()

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(1000)  # 1초 폴링

    message = ""
    message_expire = 0.0

    while True:
        # 메시지 만료
        if message and time.time() > message_expire:
            message = ""

        draw(stdscr, project, message)

        key = stdscr.getch()
        if key == -1:
            continue

        ch = chr(key).lower() if 0 <= key < 256 else ""

        if ch == "q":
            break
        elif ch == "s":
            msg = pipeline_start(project)
            message = f"▶ {msg}"
            message_expire = time.time() + 5
        elif ch == "t":
            msg = pipeline_stop(project)
            message = f"■ {msg}"
            message_expire = time.time() + 5
        elif ch == "r":
            message = "↻ 재시작 중..."
            message_expire = time.time() + 10
            draw(stdscr, project, message)
            msg = pipeline_restart(project)
            message = f"↻ {msg}"
            message_expire = time.time() + 5
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
                message = "tmux에서 돌아옴 (Ctrl+B → D로 detach)"
                message_expire = time.time() + 5
            else:
                message = "tmux 세션이 없습니다. 먼저 Start하세요."
                message_expire = time.time() + 3


if __name__ == "__main__":
    curses.wrapper(main)
