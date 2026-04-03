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
POLL_MS = 1500


# ── 상태 조회 (pipeline-launcher.py와 동일 로직) ──────────────

def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str]:
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


def agent_snapshots(project: Path) -> list[tuple[str, str, str]]:
    """[(label, status, note), ...] — launcher 수준 truth."""
    code, output = _run(
        ["tmux", "list-panes", "-t", f"{SESSION_NAME}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
        timeout=2.0,
    )
    if code != 0 or not output:
        return [("Claude", "OFF", ""), ("Codex", "OFF", ""), ("Gemini", "OFF", "")]

    names = {0: "Claude", 1: "Codex", 2: "Gemini"}
    hints = watcher_runtime_hints(project)
    results: list[tuple[str, str, str]] = []

    for raw in output.splitlines():
        try:
            idx_s, pane_id, dead = raw.split("|", 2)
            idx = int(idx_s)
        except ValueError:
            continue
        label = names.get(idx, f"Pane {idx}")
        if dead == "1":
            results.append((label, "DEAD", ""))
            continue
        cap_code, captured = _run(["tmux", "capture-pane", "-pt", pane_id, "-S", "-60"], timeout=2.0)
        if cap_code != 0 or not captured:
            results.append((label, "BOOTING", ""))
            continue
        cleaned = ANSI_RE.sub("", captured)
        status, note = detect_agent_status(label, cleaned)

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

        results.append((label, status, note))
    return results


# ── 파이프라인 제어 ────────────────────────────────────────────

def pipeline_start(project: Path) -> str:
    script = project / "start-pipeline.sh"
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
        self.root = Tk()
        self.root.title("Pipeline Launcher")
        self.root.configure(bg="#0f0f0f")
        self.root.geometry("700x620")
        self.root.minsize(500, 400)

        self._build_ui()
        self._schedule_poll()

    def _build_ui(self) -> None:
        bg = "#0f0f0f"
        fg = "#e0e0e0"
        accent = "#60a5fa"
        btn_bg = "#1a1a1a"
        btn_fg = "#cccccc"

        mono = tkfont.Font(family="Consolas", size=10)
        small = tkfont.Font(family="Consolas", size=9)

        # ── 상단: 프로젝트 + 상태 ──
        top = Frame(self.root, bg="#1a1a1a", pady=6, padx=10)
        top.pack(fill=X)

        Label(top, text="Pipeline Launcher", font=("Consolas", 13, "bold"),
              bg="#1a1a1a", fg=accent).pack(side=LEFT)

        self.status_var = StringVar(value="—")
        self.status_label = Label(top, textvariable=self.status_var, font=small,
                                  bg="#1a1a1a", fg="#888888", padx=10)
        self.status_label.pack(side=RIGHT)

        # ── 프로젝트 경로 ──
        proj_frame = Frame(self.root, bg=bg, padx=10, pady=4)
        proj_frame.pack(fill=X)
        Label(proj_frame, text="Project:", font=small, bg=bg, fg="#888888").pack(side=LEFT)
        Label(proj_frame, text=str(self.project), font=small, bg=bg, fg="#f59e0b").pack(side=LEFT, padx=6)

        # ── 버튼 바 ──
        btn_frame = Frame(self.root, bg=bg, padx=10, pady=6)
        btn_frame.pack(fill=X)

        for text, cmd in [
            ("▶ Start", self._on_start),
            ("■ Stop", self._on_stop),
            ("↻ Restart", self._on_restart),
            ("⬜ Attach tmux", self._on_attach),
        ]:
            Button(btn_frame, text=text, command=cmd, font=small,
                   bg=btn_bg, fg=btn_fg, activebackground="#333333",
                   activeforeground="#ffffff", bd=0, padx=12, pady=4,
                   highlightthickness=1, highlightbackground="#444444",
                   ).pack(side=LEFT, padx=3)

        # ── Pipeline + Watcher 상태 ──
        state_frame = Frame(self.root, bg=bg, padx=10, pady=4)
        state_frame.pack(fill=X)

        self.pipeline_var = StringVar(value="Pipeline: —")
        self.watcher_var = StringVar(value="Watcher: —")
        Label(state_frame, textvariable=self.pipeline_var, font=small, bg=bg, fg=fg).pack(side=LEFT)
        Label(state_frame, textvariable=self.watcher_var, font=small, bg=bg, fg=fg, padx=20).pack(side=LEFT)

        # ── Agent 상태 ──
        agent_frame = Frame(self.root, bg=bg, padx=10, pady=4)
        agent_frame.pack(fill=X)

        Label(agent_frame, text="Agents:", font=small, bg=bg, fg="#888888").pack(anchor="w")

        self.agent_labels: list[tuple[Label, Label, Label]] = []
        for name in ["Claude", "Codex", "Gemini"]:
            row = Frame(agent_frame, bg=bg)
            row.pack(fill=X, pady=1)
            dot = Label(row, text="●", font=small, bg=bg, fg="#666666", width=2)
            dot.pack(side=LEFT)
            name_lbl = Label(row, text=name, font=("Consolas", 10, "bold"), bg=bg, fg=fg, width=8, anchor="w")
            name_lbl.pack(side=LEFT)
            status_lbl = Label(row, text="—", font=small, bg=bg, fg="#888888")
            status_lbl.pack(side=LEFT, padx=6)
            self.agent_labels.append((dot, name_lbl, status_lbl))

        # ── Latest files ──
        file_frame = Frame(self.root, bg=bg, padx=10, pady=4)
        file_frame.pack(fill=X)

        self.work_var = StringVar(value="Latest work: —")
        self.verify_var = StringVar(value="Latest verify: —")
        Label(file_frame, textvariable=self.work_var, font=small, bg=bg, fg="#f59e0b").pack(anchor="w")
        Label(file_frame, textvariable=self.verify_var, font=small, bg=bg, fg="#f59e0b").pack(anchor="w")

        # ── Watcher log ──
        log_frame = Frame(self.root, bg=bg, padx=10, pady=4)
        log_frame.pack(fill=BOTH, expand=True)

        Label(log_frame, text="Recent log:", font=small, bg=bg, fg="#888888").pack(anchor="w")

        log_inner = Frame(log_frame, bg="#141414")
        log_inner.pack(fill=BOTH, expand=True, pady=2)

        self.log_text = Text(log_inner, font=small, bg="#141414", fg="#aaaaaa",
                             wrap=WORD, bd=0, highlightthickness=0, padx=6, pady=4,
                             state=DISABLED, height=8)
        scrollbar = Scrollbar(log_inner, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        # ── 하단 메시지 ──
        self.msg_var = StringVar(value="")
        Label(self.root, textvariable=self.msg_var, font=small,
              bg=bg, fg="#f59e0b", pady=4).pack(fill=X, padx=10)

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
            self.status_label.configure(fg="#34d399")
        else:
            self.pipeline_var.set("Pipeline: ■ Stopped")
            self.status_var.set("Stopped")
            self.status_label.configure(fg="#ef4444")

        # Watcher
        if w_alive:
            self.watcher_var.set(f"Watcher: ● Alive (PID:{w_pid})")
        else:
            self.watcher_var.set("Watcher: ✗ Dead")

        # Agents
        agents = agent_snapshots(self.project)
        for i, (dot_lbl, name_lbl, status_lbl) in enumerate(self.agent_labels):
            if i < len(agents):
                label, status, note = agents[i]
                color = STATUS_COLORS.get(status, "#666666")
                dot_lbl.configure(fg=color)
                status_text = status
                if note:
                    status_text += f" ({note})"
                status_lbl.configure(text=status_text, fg=color)
            else:
                dot_lbl.configure(fg="#666666")
                status_lbl.configure(text="—", fg="#666666")

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
        log_lines = watcher_log_tail(self.project, lines=5)
        self.log_text.configure(state=NORMAL)
        self.log_text.delete("1.0", END)
        for line in log_lines:
            # 타임스탬프 간소화
            clean = line.strip()
            if len(clean) > 100:
                clean = clean[:97] + "..."
            self.log_text.insert(END, clean + "\n")
        self.log_text.configure(state=DISABLED)
        self.log_text.see(END)

    # ── 제어 ──

    def _on_start(self) -> None:
        self.msg_var.set("Starting pipeline...")
        threading.Thread(target=self._do_start, daemon=True).start()

    def _do_start(self) -> None:
        msg = pipeline_start(self.project)
        self.root.after(0, lambda: self.msg_var.set(f"Start: {msg}"))
        time.sleep(5)
        self.root.after(0, lambda: self.msg_var.set(""))

    def _on_stop(self) -> None:
        self.msg_var.set("Stopping pipeline...")
        threading.Thread(target=self._do_stop, daemon=True).start()

    def _do_stop(self) -> None:
        msg = pipeline_stop(self.project)
        self.root.after(0, lambda: self.msg_var.set(f"Stop: {msg}"))
        time.sleep(3)
        self.root.after(0, lambda: self.msg_var.set(""))

    def _on_restart(self) -> None:
        self.msg_var.set("Restarting pipeline...")
        threading.Thread(target=self._do_restart, daemon=True).start()

    def _do_restart(self) -> None:
        pipeline_stop(self.project)
        time.sleep(2)
        msg = pipeline_start(self.project)
        self.root.after(0, lambda: self.msg_var.set(f"Restart: {msg}"))
        time.sleep(5)
        self.root.after(0, lambda: self.msg_var.set(""))

    def _on_attach(self) -> None:
        if tmux_alive():
            tmux_attach()
            self.msg_var.set("tmux attach 실행됨")
        else:
            self.msg_var.set("tmux 세션이 없습니다. 먼저 Start하세요.")

    # ── 실행 ──

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    project = resolve_project_root()
    app = PipelineGUI(project)
    app.run()


if __name__ == "__main__":
    main()
