#!/usr/bin/env python3
"""
pipeline-gui.py — 내부용 desktop GUI launcher (tkinter)

사용법:
  python3 pipeline-gui.py [project_path]
  python3 pipeline-gui.py .

나중에 exe 패키징:
  pip install pyinstaller
  pyinstaller --onefile --noconsole pipeline-gui.py
"""

from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import sys
import time
import threading
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Text, Scrollbar,
    StringVar, LEFT, RIGHT, TOP, BOTTOM, BOTH, X, Y, END, WORD, DISABLED, NORMAL,
    font as tkfont,
)

# ── 프로젝트 경로 ─────────────────────────────────────────────

def resolve_project_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    env = os.environ.get("PROJECT_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


SESSION_NAME = "ai-pipeline"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
BOX_DRAWING_ONLY_RE = re.compile(r"^[\s\-_=~│┃┆┊┌┐└┘├┤┬┴┼╭╮╯╰•·●○■□▶◀▸▹▾▿▴▵>*]+$")
FOCUS_ENTRY_START_RE = re.compile(
    r"^(?:"
    r"[•●◦○▪*-]\s+|"
    r"bash\(|read\b|search(?:ing|ed)?\b|ran\b|updated plan\b|working\b|"
    r"cascading\b|lollygagging\b|hashing\b|thinking\b|goal:|목표:|변경|검증|결과:|"
    r"wait(?:ed|ing)\b|without interrupting\b|role:|state:|handoff:|read_first:|"
    r"claude code\b|openai codex\b|gemini cli\b"
    r")",
    re.IGNORECASE,
)
POLL_MS = 1500
IS_WINDOWS = sys.platform == "win32"
WSL_DISTRO = os.environ.get("WSL_DISTRO", "Ubuntu")


# ── Platform-aware command execution ──────────────────────────

def _wsl_wrap(cmd: list[str]) -> list[str]:
    """Windows에서는 wsl.exe로 감싸서 WSL 내부 명령을 실행합니다."""
    if IS_WINDOWS:
        return ["wsl.exe", "-d", WSL_DISTRO, "--"] + cmd
    return cmd


def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str]:
    try:
        r = subprocess.run(_wsl_wrap(cmd), capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return -1, ""


def tmux_alive() -> bool:
    code, _ = _run(["tmux", "has-session", "-t", SESSION_NAME])
    return code == 0


def watcher_alive(project: Path) -> tuple[bool, int | None]:
    pid_path = project / ".pipeline" / "experimental.pid"
    if IS_WINDOWS:
        # Windows에서는 WSL 파일시스템을 직접 읽을 수 없으므로 wsl cat으로 읽기
        code, content = _run(["cat", str(pid_path)])
        if code != 0 or not content.strip():
            return False, None
        try:
            pid = int(content.strip())
        except ValueError:
            return False, None
        check_code, _ = _run(["kill", "-0", str(pid)])
        return check_code == 0, pid
    else:
        if not pid_path.exists():
            return False, None
        try:
            pid = int(pid_path.read_text().strip())
            os.kill(pid, 0)
            return True, pid
        except (ValueError, OSError):
            return False, None


def latest_md(directory: Path) -> tuple[str, float]:
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


def time_ago(mtime: float) -> str:
    if mtime == 0:
        return ""
    diff = int(time.time() - mtime)
    if diff < 60:
        return f"{diff}초 전"
    if diff < 3600:
        return f"{diff // 60}분 전"
    return f"{diff // 3600}시간 전"


def watcher_log_tail(project: Path, lines: int = 5) -> list[str]:
    log_path = project / ".pipeline" / "logs" / "experimental" / "watcher.log"
    if not log_path.exists():
        return ["(로그 없음)"]
    try:
        all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        filtered = [l for l in all_lines if "suppressed" not in l and "A/B ratio" not in l]
        return filtered[-lines:] if filtered else ["(이벤트 없음)"]
    except OSError:
        return ["(읽기 실패)"]


WATCHER_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")


def format_elapsed(seconds: float) -> str:
    total = max(0, int(seconds))
    mins, secs = divmod(total, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def extract_working_note(lines: list[str]) -> str:
    """pane 출력에서 Working 경과시간/상태 노트 추출."""
    for line in reversed(lines[-80:]):
        match = re.search(r"Working \(([^)]*)", line, re.IGNORECASE)
        if match:
            note = match.group(1).split("•", 1)[0].strip(" )…")
            if note:
                return note
        match = re.search(r"Cascading(?:…|\.{3})\s*\(([^)]*)", line, re.IGNORECASE)
        if match:
            return match.group(1).strip(" )…")
        match = re.search(r"Lollygagging(?:…|\.{3})\s*\(([^)]*)", line, re.IGNORECASE)
        if match:
            return match.group(1).strip(" )…")
        lowered = line.lower()
        if "background terminal" in lowered or "waiting for background" in lowered:
            return "bg-task"
    return ""


def extract_quota_note(pane_text: str) -> str:
    text = " ".join(line.strip() for line in pane_text.splitlines() if line.strip())

    match = re.search(r"(\d+%)\s+lef", text, re.IGNORECASE)
    if match:
        return f"{match.group(1)} left"

    match = re.search(r"you['’]ve used\s+(\d+%)", text, re.IGNORECASE)
    if match:
        return f"used {match.group(1)}"

    match = re.search(r"new 2x rate limits until ([^.]+)", text, re.IGNORECASE)
    if match:
        return f"2x until {match.group(1).strip()}"

    return ""


def detect_agent_status(label: str, pane_text: str) -> tuple[str, str]:
    """(status, note) — launcher 수준 판정."""
    lines = [l.strip() for l in pane_text.splitlines() if l.strip()]
    if not lines:
        return "DEAD", ""

    lower = pane_text.lower()

    # Working indicators — launcher와 동일한 10+ 패턴
    if (
        "working (" in lower
        or "background terminal" in lower
        or "waiting for background" in lower
        or "waited for background" in lower
        or "cascading" in lower
        or "lollygagging" in lower
        or "hashing" in lower
        or "leavering" in lower
        or "without interrupting claude's current work" in lower
        or "flumoxing" in lower
        or "philosophising" in lower
        or "sautéed" in lower
    ):
        note = extract_working_note(lines)
        return "WORKING", note

    # Ready indicators
    if label == "Codex" and ("› " in pane_text or "openai codex" in lower):
        return "READY", ""
    if label == "Claude" and ("❯" in pane_text or "claude code" in lower or "bypass permissions" in lower):
        return "READY", ""
    if label == "Gemini" and ("type your message" in lower or "gemini cli" in lower or "workspace" in lower):
        return "READY", ""

    return "BOOTING", ""


def capture_agent_panes(project: Path, history_lines: int = 180) -> dict[str, str]:
    """agent label -> cleaned pane text."""
    code, output = _run(
        ["tmux", "list-panes", "-t", f"{SESSION_NAME}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
        timeout=2.0,
    )
    names = {0: "Claude", 1: "Codex", 2: "Gemini"}
    results: dict[str, str] = {}
    if code != 0 or not output:
        return results

    for raw in output.splitlines():
        try:
            idx_s, pane_id, dead = raw.split("|", 2)
            idx = int(idx_s)
        except ValueError:
            continue
        label = names.get(idx, f"Pane {idx}")
        if dead == "1":
            results[label] = ""
            continue
        cap_code, captured = _run(
            ["tmux", "capture-pane", "-J", "-pt", pane_id, "-S", f"-{history_lines}"],
            timeout=2.0,
        )
        if cap_code != 0 or not captured:
            results[label] = ""
            continue
        cleaned = ANSI_RE.sub("", captured)
        results[label] = rejoin_wrapped_pane_lines(cleaned)
    return results


def _is_interesting_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if BOX_DRAWING_ONLY_RE.match(stripped):
        return False
    lowered = stripped.lower()
    if (
        "bypass" in lowered
        or "sandbox disabled" in lowered
        or "claude code has switc" in lowered
        or lowered in {"/effort", "high · /effort", "high /effort"}
        or lowered.startswith("workspace /")
        or lowered.startswith("type your message")
        or lowered == "workspace"
        or lowered.endswith("skills")
    ):
        return False
    return True


def rejoin_wrapped_pane_lines(text: str) -> str:
    """좁은 tmux pane에서 mid-sentence로 하드 래핑된 줄을 최대한 다시 붙입니다.

    controller/server.py의 wide-display 보정과 같은 계열 로직입니다.
    """
    if not text:
        return text

    result_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.rstrip()
        if not result_lines:
            result_lines.append(stripped)
            continue

        prev = result_lines[-1]
        is_natural_break = (
            not prev
            or prev.endswith((".", "!", "?", ":", ")", "]", "}", "─", "│", "┘", "┐", "┤", "┴"))
            or stripped.startswith(("•", "─", "│", "┌", "└", "├", "›", ">", "$", "#", "-", "*", "✓", "✗"))
            or stripped.startswith(("  •", "  -", "  *", "  ✓"))
            or not stripped
        )
        if is_natural_break:
            result_lines.append(stripped)
        else:
            result_lines[-1] = prev + " " + stripped.lstrip()

    return "\n".join(result_lines)


def _normalize_focus_line(line: str) -> str:
    line = line.rstrip()
    line = re.sub(r"\s+", " ", line.strip())
    return line


def _focus_line_starts_new_entry(line: str) -> bool:
    return bool(FOCUS_ENTRY_START_RE.match(line))


def format_focus_output(pane_text: str, max_lines: int = 24, max_chars: int = 220) -> str:
    """선택 agent pane을 최근 20줄 이상 문맥 중심으로 보여준다."""
    if not pane_text.strip():
        return "(출력 없음)"

    lines = [line.rstrip() for line in pane_text.splitlines()]
    filtered = [line for line in lines if _is_interesting_line(line)]
    if not filtered:
        return "(표시할 출력 없음)"

    interesting_markers = (
        "working", "cascading", "lollygagging", "hashing", "leavering",
        "read", "search", "searched", "bash(", "ran ", "updated plan",
        "goal:", "목표:", "변경", "검증", "thinking", "without interrupting",
        "background", "role:", "handoff:", "state:", "explored", "waiting",
    )

    anchor = max(0, len(filtered) - max_lines)
    for idx in range(len(filtered) - 1, -1, -1):
        lowered = filtered[idx].lower()
        if any(marker in lowered for marker in interesting_markers):
            anchor = max(0, idx - (max_lines - 6))
            break

    tail = filtered[anchor:]

    rendered: list[str] = []
    previous_blank = False
    for raw in tail:
        line = _normalize_focus_line(raw)
        if not line:
            if not previous_blank:
                rendered.append("")
            previous_blank = True
            continue
        previous_blank = False

        if len(line) > max_chars:
            rendered.append(line[: max_chars - 3] + "...")
        else:
            rendered.append(line)

    rendered = rendered[-max_lines:]
    if not rendered:
        return "(표시할 출력 없음)"
    return "\n".join(rendered)


def watcher_runtime_hints(project: Path) -> dict[str, tuple[str, str]]:
    """watcher.log에서 agent별 WORKING/READY 힌트와 경과시간 추출."""
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

        if "notify_claude" in line or ("send-keys" in line and "pane_type=claude" in line) or "waiting_for_claude" in line:
            claude_started_at = timestamp
            claude_done = False
        elif "claude activity detected" in line or ("new job:" in line and claude_started_at is not None):
            claude_done = True

        if "lease acquired: slot=slot_verify" in line or "VERIFY_PENDING → VERIFY_RUNNING" in line:
            codex_started_at = timestamp
            codex_done = False
        elif "codex task completed" in line or "lease released: slot=slot_verify" in line or "VERIFY_RUNNING → VERIFY_DONE" in line:
            codex_done = True

        if "notify_gemini" in line or "gemini response activity" in line:
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


def agent_snapshots(project: Path) -> list[tuple[str, str, str, str]]:
    """[(label, status, note, quota), ...] — launcher 수준 truth."""
    code, output = _run(
        ["tmux", "list-panes", "-t", f"{SESSION_NAME}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
        timeout=2.0,
    )
    if code != 0 or not output:
        return [("Claude", "OFF", "", ""), ("Codex", "OFF", "", ""), ("Gemini", "OFF", "", "")]

    names = {0: "Claude", 1: "Codex", 2: "Gemini"}
    hints = watcher_runtime_hints(project)
    results: list[tuple[str, str, str, str]] = []

    for raw in output.splitlines():
        try:
            idx_s, pane_id, dead = raw.split("|", 2)
            idx = int(idx_s)
        except ValueError:
            continue
        label = names.get(idx, f"Pane {idx}")
        if dead == "1":
            results.append((label, "DEAD", "", ""))
            continue
        cap_code, captured = _run(["tmux", "capture-pane", "-pt", pane_id, "-S", "-60"], timeout=2.0)
        if cap_code != 0 or not captured:
            results.append((label, "BOOTING", "", ""))
            continue
        cleaned = ANSI_RE.sub("", captured)
        status, note = detect_agent_status(label, cleaned)
        quota = extract_quota_note(cleaned)

        # watcher 힌트로 보정 (launcher와 동일 로직)
        hint = hints.get(label)
        if hint:
            hint_status, hint_note = hint
            if hint_status == "WORKING":
                status = "WORKING"
                if not note:
                    note = hint_note
            elif hint_status == "READY" and status == "BOOTING":
                status = "READY"
                note = ""

        results.append((label, status, note, quota))
    return results


# ── 파이프라인 제어 ────────────────────────────────────────────

def pipeline_start(project: Path) -> str:
    script = project / "start-pipeline.sh"
    if IS_WINDOWS:
        # Windows: wsl.exe로 bash 실행
        subprocess.Popen(
            ["wsl.exe", "-d", WSL_DISTRO, "--cd", str(project), "--",
             "bash", "-l", str(script), str(project), "--mode", "experimental", "--no-attach"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
    else:
        if not script.exists():
            return "start-pipeline.sh 없음"
        log_path = project / ".pipeline" / "logs" / "experimental" / "pipeline-launcher-start.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as logf:
            subprocess.Popen(
                ["bash", "-l", str(script), str(project), "--mode", "experimental", "--no-attach"],
                cwd=str(project), stdout=logf, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, start_new_session=True,
            )
    return "시작 요청됨"


def pipeline_stop(project: Path) -> str:
    script = project / "stop-pipeline.sh"
    if IS_WINDOWS:
        subprocess.run(
            ["wsl.exe", "-d", WSL_DISTRO, "--cd", str(project), "--",
             "bash", str(script), str(project)],
            capture_output=True, timeout=15,
        )
    else:
        if not script.exists():
            return "stop-pipeline.sh 없음"
        subprocess.run(["bash", str(script), str(project)], capture_output=True, timeout=15)
    return "중지 완료"


def tmux_attach() -> None:
    """별도 터미널에서 tmux attach 실행."""
    # WSL 환경에서 새 터미널 창 열기
    try:
        subprocess.Popen(
            ["wsl.exe", "bash", "-lc", f"tmux attach -t {SESSION_NAME}"],
            start_new_session=True,
        )
    except FileNotFoundError:
        # WSL이 아닌 환경 — 직접 attach
        subprocess.Popen(
            ["bash", "-c", f"tmux attach -t {SESSION_NAME}"],
            start_new_session=True,
        )


# ── GUI ────────────────────────────────────────────────────────

STATUS_COLORS = {
    "WORKING": "#34d399",
    "READY": "#60a5fa",
    "DEAD": "#ef4444",
    "BOOTING": "#f59e0b",
    "OFF": "#666666",
}


class PipelineGUI:
    def __init__(self, project: Path) -> None:
        self.project = project
        self.selected_agent = "Claude"
        self._auto_focus_agent = True
        self.root = Tk()
        self.root.title("Pipeline Launcher")
        self.root.configure(bg="#0f0f0f")
        self.root.resizable(True, True)
        self._set_initial_window_geometry()
        self.root.minsize(900, 600)

        self._build_ui()
        self._schedule_poll()

    def _set_initial_window_geometry(self) -> None:
        screen_w = max(1280, self.root.winfo_screenwidth())
        screen_h = max(900, self.root.winfo_screenheight())

        width = min(900, screen_w - 40)
        height = min(900, screen_h - 60)

        x = max(20, (screen_w - width) // 2)
        y = max(20, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        bg = "#0f0f0f"
        fg = "#e0e0e0"
        accent = "#60a5fa"
        sub_fg = "#9ca3af"
        btn_bg = "#1a1a1a"
        btn_fg = "#d1d5db"
        card_bg = "#171717"
        card_border = "#2a2a2a"
        log_bg = "#121212"

        title_font = tkfont.Font(family="Consolas", size=15, weight="bold")
        body_font = tkfont.Font(family="Consolas", size=10)
        small_font = tkfont.Font(family="Consolas", size=9)
        status_font = tkfont.Font(family="Consolas", size=11, weight="bold")
        section_font = tkfont.Font(family="Consolas", size=10, weight="bold")

        def make_card(parent: Frame, padx: int = 12, pady: int = 10) -> Frame:
            card = Frame(
                parent,
                bg=card_bg,
                padx=padx,
                pady=pady,
                highlightthickness=1,
                highlightbackground=card_border,
            )
            return card

        # ── 상단 헤더 ──
        top = Frame(self.root, bg="#161616", padx=14, pady=10)
        top.pack(fill=X)

        Label(top, text="Pipeline Launcher", font=title_font, bg="#161616", fg=accent).pack(side=LEFT)
        self.status_var = StringVar(value="Stopped")
        self.status_label = Label(
            top,
            textvariable=self.status_var,
            font=status_font,
            bg="#2a1717",
            fg="#ef4444",
            padx=10,
            pady=4,
        )
        self.status_label.pack(side=RIGHT)

        content = Frame(self.root, bg=bg, padx=14, pady=12)
        content.pack(fill=BOTH, expand=True)

        # ── 프로젝트 경로 ──
        proj_card = make_card(content)
        proj_card.pack(fill=X, pady=(0, 10))
        Label(proj_card, text="Project", font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")
        Label(
            proj_card,
            text=str(self.project),
            font=body_font,
            bg=card_bg,
            fg="#f59e0b",
            anchor="w",
            justify=LEFT,
            wraplength=860,
        ).pack(anchor="w", pady=(4, 0))

        # ── 버튼 바 ──
        btn_card = make_card(content, padx=10, pady=8)
        btn_card.pack(fill=X, pady=(0, 10))

        def make_btn(parent: Frame, text: str, cmd) -> Button:
            return Button(
                parent, text=text, command=cmd, font=body_font,
                bg=btn_bg, fg=btn_fg, activebackground="#333333",
                activeforeground="#ffffff", bd=0, padx=12, pady=6,
                highlightthickness=1, highlightbackground="#444444",
                disabledforeground="#555555",
            )

        self.btn_start = make_btn(btn_card, "▶ Start", self._on_start)
        self.btn_start.pack(side=LEFT, padx=4)
        self.btn_stop = make_btn(btn_card, "■ Stop", self._on_stop)
        self.btn_stop.pack(side=LEFT, padx=4)
        self.btn_restart = make_btn(btn_card, "↻ Restart", self._on_restart)
        self.btn_restart.pack(side=LEFT, padx=4)
        self.btn_attach = make_btn(btn_card, "⬜ Attach tmux", self._on_attach)
        self.btn_attach.pack(side=LEFT, padx=4)

        self._action_in_progress = False

        # ── 상태 개요 + 최신 파일 ──
        overview = Frame(content, bg=bg)
        overview.pack(fill=X, pady=(0, 10))

        system_card = make_card(overview)
        system_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 6))
        Label(system_card, text="System", font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")
        self.pipeline_var = StringVar(value="Pipeline: —")
        self.watcher_var = StringVar(value="Watcher: —")
        self.pipeline_state_label = Label(system_card, textvariable=self.pipeline_var, font=body_font, bg=card_bg, fg=fg, anchor="w")
        self.pipeline_state_label.pack(anchor="w", pady=(8, 2))
        self.watcher_state_label = Label(system_card, textvariable=self.watcher_var, font=body_font, bg=card_bg, fg=fg, anchor="w")
        self.watcher_state_label.pack(anchor="w")

        file_card = make_card(overview)
        file_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(6, 0))
        Label(file_card, text="Artifacts", font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")
        self.work_var = StringVar(value="Latest work: —")
        self.verify_var = StringVar(value="Latest verify: —")
        Label(file_card, textvariable=self.work_var, font=body_font, bg=card_bg, fg="#f59e0b", anchor="w", justify=LEFT, wraplength=400).pack(anchor="w", pady=(8, 2))
        Label(file_card, textvariable=self.verify_var, font=body_font, bg=card_bg, fg="#f59e0b", anchor="w", justify=LEFT, wraplength=400).pack(anchor="w")

        # ── Agent 상태 ──
        agent_section = make_card(content)
        agent_section.pack(fill=X, pady=(0, 10))
        Label(agent_section, text="Agents", font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")

        cards_row = Frame(agent_section, bg=card_bg)
        cards_row.pack(fill=X, pady=(8, 0))

        self.agent_labels: list[tuple[Frame, Label, Label, Label, Label]] = []
        for idx, name in enumerate(["Claude", "Codex", "Gemini"]):
            card = Frame(
                cards_row,
                bg="#111111",
                padx=10,
                pady=8,
                highlightthickness=1,
                highlightbackground=card_border,
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 4, 0 if idx == 2 else 4))
            cards_row.grid_columnconfigure(idx, weight=1)

            name_row = Frame(card, bg="#111111")
            name_row.pack(fill=X)
            dot = Label(name_row, text="●", font=body_font, bg="#111111", fg="#666666")
            dot.pack(side=LEFT)
            Label(name_row, text=name, font=section_font, bg="#111111", fg=fg).pack(side=LEFT, padx=(6, 0))

            status_lbl = Label(card, text="—", font=status_font, bg="#111111", fg="#888888", anchor="w")
            status_lbl.pack(anchor="w", pady=(6, 1))
            note_lbl = Label(card, text="", font=small_font, bg="#111111", fg=sub_fg, anchor="w", justify=LEFT, wraplength=250)
            note_lbl.pack(anchor="w")
            quota_lbl = Label(card, text="", font=small_font, bg="#111111", fg="#7c8798", anchor="w", justify=LEFT, wraplength=250)
            quota_lbl.pack(anchor="w", pady=(2, 0))
            self.agent_labels.append((card, dot, status_lbl, note_lbl, quota_lbl))

            for widget in (card, name_row, dot, status_lbl, note_lbl, quota_lbl):
                widget.bind("<Button-1>", lambda _event, agent=name: self._select_agent(agent))

        # ── 하단 2영역: agent output + watcher log (균등 분할) ──
        from tkinter import PanedWindow, VERTICAL
        paned = PanedWindow(content, orient=VERTICAL, bg="#222222", sashwidth=4, sashrelief="flat")
        paned.pack(fill=BOTH, expand=True)
        self.paned = paned

        # ── 선택 agent 상세 출력 ──
        focus_frame = Frame(paned, bg=card_bg, padx=12, pady=10,
                            highlightthickness=1, highlightbackground=card_border)

        focus_header = Frame(focus_frame, bg=card_bg)
        focus_header.pack(fill=X)
        Label(focus_header, text="Selected agent output", font=section_font, bg=card_bg, fg=sub_fg).pack(side=LEFT)
        self.focus_title_var = StringVar(value="Claude • 최근 pane tail (read-only)")
        Label(focus_header, textvariable=self.focus_title_var, font=small_font, bg=card_bg, fg="#9ca3af").pack(side=RIGHT)

        focus_inner = Frame(focus_frame, bg=log_bg)
        focus_inner.pack(fill=BOTH, expand=True, pady=(8, 0))
        focus_font = tkfont.Font(family="Consolas", size=9)
        self.focus_text = Text(
            focus_inner, font=focus_font, bg=log_bg, fg="#d4d4d8",
            wrap=WORD, bd=0, highlightthickness=0, padx=10, pady=6,
            state=DISABLED, spacing1=0, spacing3=1,
        )
        focus_scroll = Scrollbar(focus_inner, command=self.focus_text.yview)
        self.focus_text.configure(yscrollcommand=focus_scroll.set)
        focus_scroll.pack(side=RIGHT, fill=Y)
        self.focus_text.pack(side=LEFT, fill=BOTH, expand=True)

        paned.add(focus_frame, minsize=140, stretch="always")

        # ── Watcher log ──
        log_frame = Frame(paned, bg=card_bg, padx=12, pady=8,
                          highlightthickness=1, highlightbackground=card_border)
        Label(log_frame, text="Recent watcher log", font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")

        log_inner = Frame(log_frame, bg=log_bg)
        log_inner.pack(fill=BOTH, expand=True, pady=(8, 0))

        self.log_text = Text(log_inner, font=small_font, bg=log_bg, fg="#a1a1aa",
                             wrap=WORD, bd=0, highlightthickness=0, padx=10, pady=6,
                             state=DISABLED)
        scrollbar = Scrollbar(log_inner, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        paned.add(log_frame, minsize=100, stretch="never")
        # 초기 sash: focus 75% / log 25%
        self.root.update_idletasks()
        paned_h = paned.winfo_height()
        if paned_h > 240:
            paned.sash_place(0, 0, int(paned_h * 0.75))

        # ── 하단 메시지 ──
        self.msg_var = StringVar(value="")
        self.msg_label = Label(self.root, textvariable=self.msg_var, font=body_font,
                               bg=bg, fg="#f59e0b", pady=8, anchor="w", padx=14)
        self.msg_label.pack(fill=X)
        self.root.after(120, self._set_initial_pane_split)

    def _set_initial_pane_split(self) -> None:
        try:
            total_h = self.paned.winfo_height()
            if total_h > 240:
                self.paned.sash_place(0, 0, int(total_h * 0.62))
        except Exception:
            pass

    def _ensure_log_pane_visible(self) -> None:
        try:
            total_h = self.paned.winfo_height()
            if total_h <= 240:
                return
            _x, sash_y = self.paned.sash_coord(0)
            lower_h = total_h - sash_y
            if lower_h < 150:
                self.paned.sash_place(0, 0, int(total_h * 0.62))
        except Exception:
            pass

    # ── 데이터 수집 (tmux 호출 통합) ──

    _prev_focus_text: str = ""
    _prev_log_text: str = ""

    def _collect_all_agent_data(self) -> tuple[list[tuple[str, str, str, str]], dict[str, str]]:
        """list-panes 1회 + capture-pane x3 = 4회 subprocess로 status + output 둘 다 반환."""
        code, output = _run(
            ["tmux", "list-panes", "-t", f"{SESSION_NAME}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
            timeout=2.0,
        )
        if code != 0 or not output:
            return (
                [("Claude", "OFF", "", ""), ("Codex", "OFF", "", ""), ("Gemini", "OFF", "", "")],
                {},
            )

        names = {0: "Claude", 1: "Codex", 2: "Gemini"}
        hints = watcher_runtime_hints(self.project)
        agents: list[tuple[str, str, str, str]] = []
        pane_map: dict[str, str] = {}

        for raw in output.splitlines():
            try:
                idx_s, pane_id, dead = raw.split("|", 2)
                idx = int(idx_s)
            except ValueError:
                continue
            label = names.get(idx, f"Pane {idx}")
            if dead == "1":
                agents.append((label, "DEAD", "", ""))
                pane_map[label] = ""
                continue

            # 한 번만 capture — 긴 history로 가져와서 status와 output 양쪽에 사용
            cap_code, captured = _run(
                ["tmux", "capture-pane", "-J", "-pt", pane_id, "-S", "-180"],
                timeout=2.0,
            )
            if cap_code != 0 or not captured:
                agents.append((label, "BOOTING", "", ""))
                pane_map[label] = ""
                continue

            cleaned = ANSI_RE.sub("", captured)

            # status 판정 (agent_snapshots 로직)
            status, note = detect_agent_status(label, cleaned)
            quota = extract_quota_note(cleaned)
            hint = hints.get(label)
            if hint:
                hint_status, hint_note = hint
                if hint_status == "WORKING":
                    status = "WORKING"
                    if not note:
                        note = hint_note
                elif hint_status == "READY" and status == "BOOTING":
                    status = "READY"
                    note = ""
            agents.append((label, status, note, quota))

            # output (capture_agent_panes 로직)
            pane_map[label] = rejoin_wrapped_pane_lines(cleaned)

        return agents, pane_map

    def _update_text_if_changed(self, widget: Text, new_text: str) -> None:
        """Text 위젯의 내용이 바뀌었을 때만 갱신합니다."""
        widget.configure(state=NORMAL)
        current = widget.get("1.0", f"{END}-1c")
        if current == new_text:
            widget.configure(state=DISABLED)
            return
        at_bottom = widget.yview()[1] >= 0.95
        widget.delete("1.0", END)
        widget.insert(END, new_text)
        widget.configure(state=DISABLED)
        if at_bottom:
            widget.see(END)

    def _select_agent(self, agent: str) -> None:
        self.selected_agent = agent
        self._auto_focus_agent = False
        self._poll()

    # ── 폴링 ──

    def _schedule_poll(self) -> None:
        self._poll()
        self.root.after(POLL_MS, self._schedule_poll)

    def _poll(self) -> None:
        session_ok = tmux_alive()
        w_alive, w_pid = watcher_alive(self.project)

        # Pipeline status
        if session_ok:
            self.pipeline_var.set("Pipeline: ● Running")
            self.status_var.set("Running")
            self.status_label.configure(fg="#34d399", bg="#0f2f23")
            self.pipeline_state_label.configure(fg="#34d399")
        else:
            self.pipeline_var.set("Pipeline: ■ Stopped")
            self.status_var.set("Stopped")
            self.status_label.configure(fg="#ef4444", bg="#351717")
            self.pipeline_state_label.configure(fg="#ef4444")

        # Watcher
        if w_alive:
            self.watcher_var.set(f"Watcher: ● Alive (PID:{w_pid})")
            self.watcher_state_label.configure(fg="#34d399")
        else:
            self.watcher_var.set("Watcher: ✗ Dead")
            self.watcher_state_label.configure(fg="#ef4444")

        # Agents — 통합 조회: list-panes 1회 + capture-pane x3
        # agent_snapshots + capture_agent_panes 를 한 번에 처리
        agents, pane_map = self._collect_all_agent_data()
        working_labels = [label for label, status, _note, _quota in agents if status == "WORKING"]
        if self.selected_agent not in {label for label, _s, _n, _q in agents}:
            self.selected_agent = working_labels[0] if working_labels else "Claude"
        elif self._auto_focus_agent and working_labels:
            self.selected_agent = working_labels[0]

        for i, (card, dot_lbl, status_lbl, note_lbl, quota_lbl) in enumerate(self.agent_labels):
            if i < len(agents):
                label, status, note, quota = agents[i]
                color = STATUS_COLORS.get(status, "#666666")
                dot_lbl.configure(fg=color)
                status_lbl.configure(text=status, fg=color)
                note_lbl.configure(text=note or "대기 중", fg="#9ca3af")
                quota_lbl.configure(text=f"Quota: {quota}" if quota else "Quota: —", fg="#7c8798")
                if label == self.selected_agent:
                    card.configure(highlightbackground="#f59e0b", bg="#141414")
                    for child in card.winfo_children():
                        try:
                            child.configure(bg="#141414")
                        except Exception:
                            pass
                else:
                    border_color = color if status == "WORKING" else "#2a2a2a"
                    border_width = 2 if status == "WORKING" else 1
                    card.configure(highlightbackground=border_color, highlightthickness=border_width, bg="#111111")
                    for child in card.winfo_children():
                        try:
                            child.configure(bg="#111111")
                        except Exception:
                            pass
            else:
                dot_lbl.configure(fg="#666666")
                status_lbl.configure(text="—", fg="#666666")
                note_lbl.configure(text="", fg="#666666")
                quota_lbl.configure(text="Quota: —", fg="#666666")
                card.configure(highlightbackground="#2a2a2a")

        selected_text = format_focus_output(pane_map.get(self.selected_agent, ""))
        self.focus_title_var.set(f"{self.selected_agent} • 최근 pane tail (read-only)")
        # diff 갱신: 내용 변경 시에만 Text 위젯 업데이트
        self._update_text_if_changed(self.focus_text, selected_text)

        # Latest files
        work_name, work_mtime = latest_md(self.project / "work")
        verify_name, verify_mtime = latest_md(self.project / "verify")
        work_display = f"Latest work:   {work_name}"
        if work_mtime:
            work_display += f" ({time_ago(work_mtime)})"
        verify_display = f"Latest verify: {verify_name}"
        if verify_mtime:
            verify_display += f" ({time_ago(verify_mtime)})"
        self.work_var.set(work_display)
        self.verify_var.set(verify_display)

        # Watcher log
        log_lines = watcher_log_tail(self.project, lines=8)
        log_text = "\n".join(
            (l.strip()[:117] + "..." if len(l.strip()) > 120 else l.strip())
            for l in log_lines
        )
        self._update_text_if_changed(self.log_text, log_text)

        # 버튼 enable/disable — 작업 중이면 전부 비활성
        if self._action_in_progress:
            self.btn_start.configure(state=DISABLED)
            self.btn_stop.configure(state=DISABLED)
            self.btn_restart.configure(state=DISABLED)
            self.btn_attach.configure(state=DISABLED)
        else:
            self.btn_start.configure(state=NORMAL if not session_ok else DISABLED)
            self.btn_stop.configure(state=NORMAL if session_ok else DISABLED)
            self.btn_restart.configure(state=NORMAL if session_ok else DISABLED)
            self.btn_attach.configure(state=NORMAL if session_ok else DISABLED)

    # ── 제어 ──

    def _lock_buttons(self, label: str) -> None:
        self._action_in_progress = True
        self.msg_var.set(label)
        self.msg_label.configure(fg="#60a5fa")

    def _unlock_buttons(self, msg: str, is_error: bool = False) -> None:
        self._action_in_progress = False
        self.msg_var.set(msg)
        self.msg_label.configure(fg="#ef4444" if is_error else "#34d399")

    def _clear_msg_later(self, delay_ms: int = 6000) -> None:
        self.root.after(delay_ms, lambda: self.msg_var.set("") if not self._action_in_progress else None)

    def _on_start(self) -> None:
        if self._action_in_progress:
            return
        self._lock_buttons("▶ Starting pipeline...")
        threading.Thread(target=self._do_start, daemon=True).start()

    def _do_start(self) -> None:
        try:
            msg = pipeline_start(self.project)
            # 기동 대기 (최대 12초)
            for _ in range(12):
                time.sleep(1)
                if tmux_alive():
                    self.root.after(0, lambda: self._unlock_buttons("▶ Pipeline started"))
                    self.root.after(0, lambda: self._clear_msg_later())
                    return
            self.root.after(0, lambda: self._unlock_buttons(f"▶ Start: {msg} (tmux 확인 안 됨)", is_error=True))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"▶ Start failed: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later(10000))

    def _on_stop(self) -> None:
        if self._action_in_progress:
            return
        self._lock_buttons("■ Stopping pipeline...")
        threading.Thread(target=self._do_stop, daemon=True).start()

    def _do_stop(self) -> None:
        try:
            msg = pipeline_stop(self.project)
            self.root.after(0, lambda: self._unlock_buttons(f"■ {msg}"))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"■ Stop failed: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later())

    def _on_restart(self) -> None:
        if self._action_in_progress:
            return
        self._lock_buttons("↻ Restarting pipeline...")
        threading.Thread(target=self._do_restart, daemon=True).start()

    def _do_restart(self) -> None:
        try:
            self.root.after(0, lambda: self.msg_var.set("↻ Stopping..."))
            pipeline_stop(self.project)
            time.sleep(2)
            self.root.after(0, lambda: self.msg_var.set("↻ Starting..."))
            pipeline_start(self.project)
            for _ in range(12):
                time.sleep(1)
                if tmux_alive():
                    self.root.after(0, lambda: self._unlock_buttons("↻ Pipeline restarted"))
                    self.root.after(0, lambda: self._clear_msg_later())
                    return
            self.root.after(0, lambda: self._unlock_buttons("↻ Restart: tmux 확인 안 됨", is_error=True))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"↻ Restart failed: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later(10000))

    def _on_attach(self) -> None:
        if tmux_alive():
            tmux_attach()
            self.msg_var.set("tmux attach 실행됨")
            self.msg_label.configure(fg="#34d399")
            self._clear_msg_later()
        else:
            self.msg_var.set("tmux 세션이 없습니다. 먼저 Start하세요.")
            self.msg_label.configure(fg="#ef4444")
            self._clear_msg_later()

    # ── 실행 ──

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    project = resolve_project_root()
    app = PipelineGUI(project)
    app.run()


if __name__ == "__main__":
    main()
