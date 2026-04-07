"""Agent pane capture, status detection, focus output formatting, watcher hints, run summary."""
from __future__ import annotations

import datetime as dt
import re
import time
from pathlib import Path

from .platform import (
    IS_WINDOWS, TMUX_QUERY_TIMEOUT, FILE_QUERY_TIMEOUT,
    _wsl_path_str, _run,
)
from .project import _session_name_for

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
WATCHER_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")
_JOB_ID_RE = re.compile(r"new job:\s*(\S+)")
_STATE_TRANS_RE = re.compile(r"state\s+\S+\s+(\S+)\s*→\s*(\S+)")
_ELAPSED_RE = re.compile(r"(\d+)\s*(h|m|s)")
_BUSY_PATTERNS = (
    "working (",        # ◦ Working (36s • esc to interrupt)
    "working for ",     # Worked for 1m 25s (transition text)
    "• working",        # • Working ...
    "◦ working",        # ◦ Working ...
    "waiting for background",
    "background terminal",
    "cascading",
    "lollygagging",
    "hashing",
    "leavering",
    "flumoxing",
    "philosophising",
    "sautéed",
    "thinking",
    "esc to interrupt",
)

STATUS_COLORS = {
    "WORKING": "#4ade80",
    "READY": "#5b9cf6",
    "DEAD": "#f87171",
    "BOOTING": "#e0a040",
    "OFF": "#404058",
}


def _extract_run_summary(log_lines: list[str]) -> dict[str, str]:
    job = ""
    phase = ""
    turn = ""
    ts = ""
    for line in log_lines:
        m = _JOB_ID_RE.search(line)
        if m:
            job = m.group(1)
            ts_m = WATCHER_TS_RE.match(line)
            if ts_m:
                ts = ts_m.group(1)[-8:]
        m = _STATE_TRANS_RE.search(line)
        if m:
            phase = m.group(2)
        if "notify_claude" in line or "Claude 차례" in line:
            turn = "Claude"
        elif "lease acquired" in line or "dispatching codex" in line:
            turn = "Codex"
        elif "notify_gemini" in line or "Gemini 차례" in line:
            turn = "Gemini"
        elif "initial turn:" in line:
            t = line.split("initial turn:", 1)[1].strip()
            turn = t.capitalize() if t else turn
        elif "codex_followup" in line:
            turn = "Codex (follow-up)"
    return {"job": job, "phase": phase, "turn": turn, "ts": ts}


def format_elapsed(seconds: float) -> str:
    total = max(0, int(seconds))
    mins, secs = divmod(total, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def _parse_elapsed(note: str) -> float:
    total = 0.0
    for m in _ELAPSED_RE.finditer(note):
        val = int(m.group(1))
        unit = m.group(2)
        if unit == "h":
            total += val * 3600
        elif unit == "m":
            total += val * 60
        else:
            total += val
    return total


def _recent_nonempty_lines(pane_text: str, limit: int = 24) -> list[str]:
    return [line.strip() for line in pane_text.splitlines() if line.strip()][-limit:]


def _recent_busy_indicator(pane_text: str, limit: int = 18) -> bool:
    recent_lower = "\n".join(_recent_nonempty_lines(pane_text, limit)).lower()
    return any(pattern in recent_lower for pattern in _BUSY_PATTERNS)


def extract_working_note(lines: list[str]) -> str:
    for line in reversed(lines[-24:]):
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
    match = re.search(r"you['']ve used\s+(\d+%)", text, re.IGNORECASE)
    if match:
        return f"used {match.group(1)}"
    match = re.search(r"new 2x rate limits until ([^.]+)", text, re.IGNORECASE)
    if match:
        return f"2x until {match.group(1).strip()}"
    return ""


def detect_agent_status(label: str, pane_text: str) -> tuple[str, str]:
    lines = [l.strip() for l in pane_text.splitlines() if l.strip()]
    if not lines:
        return "DEAD", ""
    lower = pane_text.lower()
    recent_lower = "\n".join(_recent_nonempty_lines(pane_text, 18)).lower()
    has_recent_busy = _recent_busy_indicator(pane_text)
    if (
        has_recent_busy
        or "waited for background" in recent_lower
        or "without interrupting claude's current work" in recent_lower
    ):
        note = extract_working_note(lines)
        return "WORKING", note
    if label == "Gemini":
        if "esc to cancel" in recent_lower:
            return "WORKING", ""
    if label == "Codex" and ("› " in pane_text or "openai codex" in lower):
        return "READY", ""
    if label == "Claude" and ("❯" in pane_text or "claude code" in lower or "bypass permissions" in lower):
        return "READY", ""
    if label == "Gemini" and ("type your message" in lower or "gemini cli" in lower or "workspace" in lower):
        return "READY", ""
    return "BOOTING", ""


def capture_agent_panes(project: Path, history_lines: int = 180, session: str = "") -> dict[str, str]:
    sess = session or _session_name_for(project)
    code, output = _run(
        ["tmux", "list-panes", "-t", f"{sess}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
        timeout=TMUX_QUERY_TIMEOUT,
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
            ["tmux", "capture-pane", "-J", "-p", "-t", pane_id, "-S", f"-{history_lines}"],
            timeout=TMUX_QUERY_TIMEOUT,
        )
        if cap_code != 0 or not captured:
            results[label] = ""
            continue
        cleaned = ANSI_RE.sub("", captured)
        results[label] = rejoin_wrapped_pane_lines(cleaned)
    return results


def rejoin_wrapped_pane_lines(text: str) -> str:
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


def format_focus_output(pane_text: str, max_lines: int = 40, max_chars: int = 300) -> str:
    if not pane_text.strip():
        return "(출력 없음)"
    lines = [line.rstrip() for line in pane_text.splitlines()]
    filtered = [line for line in lines if line.strip() and not BOX_DRAWING_ONLY_RE.match(line.strip())]
    if not filtered:
        return "(표시할 출력 없음)"
    interesting_markers = (
        "working", "cascading", "lollygagging", "hashing", "leavering",
        "read", "search", "searched", "bash(", "ran ", "updated plan",
        "goal:", "목표:", "변경", "검증", "thinking", "without interrupting",
        "background", "role:", "handoff:", "state:", "explored", "waiting",
        "write", "edit", "create", "error", "fail", "success", "complete",
    )
    anchor = max(0, len(filtered) - max_lines)
    for idx in range(len(filtered) - 1, -1, -1):
        lowered = filtered[idx].lower()
        if any(marker in lowered for marker in interesting_markers):
            anchor = max(0, idx - (max_lines - 8))
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
    log_path = project / ".pipeline" / "logs" / "experimental" / "watcher.log"
    if IS_WINDOWS:
        code, content = _run(["tail", "-n", "300", _wsl_path_str(log_path)], timeout=FILE_QUERY_TIMEOUT)
        if code != 0:
            content = ""
        if not content:
            return {}
        lines = content.splitlines()[-300:]
    else:
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
        hints["Claude"] = ("WORKING", f"impl {format_elapsed(now - claude_started_at)}")
    elif claude_done:
        hints["Claude"] = ("READY", "")
    if codex_started_at is not None and not codex_done:
        hints["Codex"] = ("WORKING", f"verify {format_elapsed(now - codex_started_at)}")
    elif codex_done:
        hints["Codex"] = ("READY", "")
    if gemini_started_at is not None and not gemini_done:
        hints["Gemini"] = ("WORKING", f"advice {format_elapsed(now - gemini_started_at)}")
    elif gemini_done:
        hints["Gemini"] = ("READY", "")
    return hints
