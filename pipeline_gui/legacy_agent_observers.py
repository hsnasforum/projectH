"""Legacy pane/log observer helpers kept for debug and compatibility surfaces only."""
from __future__ import annotations

import datetime as dt
import re
import time
from collections.abc import Callable
from pathlib import Path

from pipeline_runtime.lane_catalog import default_role_bindings

from .formatting import format_elapsed
from .setup_profile import resolve_project_runtime_adapter

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
BOX_DRAWING_ONLY_RE = re.compile(r"^[\s\-_=~│┃┆┊┌┐└┘├┤┬┴┼╭╮╯╰•·●○■□▶◀▸▹▾▿▴▵>*]+$")
WATCHER_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")
_ELAPSED_RE = re.compile(r"(\d+)\s*(h|m|s)")
_CLAUDE_PROMPT_ONLY_RE = re.compile(r"^[❯›⏵>]+$")
_RECENT_PROGRESS_LINE_RE = re.compile(
    r"^[+•●◦○▪✻✶*\-]?\s*[A-Za-z][A-Za-z-]*ing(?:\.\.\.|…)?(?:\s*[|│].*)?$",
    re.IGNORECASE,
)
_BUSY_PATTERNS = (
    "working (",
    "working for ",
    "• working",
    "◦ working",
    "noodling",
    "crunching",
    "growing",
    "waiting for background",
    "background terminal",
    "cascading",
    "lollygagging",
    "hashing",
    "leavering",
    "flumoxing",
    "philosophising",
    "thinking",
    "esc to interrupt",
)
_CLAUDE_STRONG_LIVE_BUSY_PATTERNS = (
    "noodling",
    "crunching",
    "growing",
    "background terminal",
    "waiting for background",
    "waited for background",
    "without interrupting claude's current work",
    "cascading",
    "lollygagging",
    "hashing",
    "leavering",
    "flumoxing",
    "philosophising",
    "thinking",
)


def _parse_elapsed(note: str) -> float:
    total = 0.0
    for match in _ELAPSED_RE.finditer(note):
        value = int(match.group(1))
        unit = match.group(2)
        if unit == "h":
            total += value * 3600
        elif unit == "m":
            total += value * 60
        else:
            total += value
    return total


def _recent_nonempty_lines(pane_text: str, limit: int = 24) -> list[str]:
    return [line.strip() for line in pane_text.splitlines() if line.strip()][-limit:]


def _recent_busy_indicator(pane_text: str, limit: int = 18) -> bool:
    recent_lower = "\n".join(_recent_nonempty_lines(pane_text, limit)).lower()
    return any(pattern in recent_lower for pattern in _BUSY_PATTERNS)


def _has_recent_claude_ready_prompt(recent_lines: list[str]) -> bool:
    tail = recent_lines[-4:]
    for line in tail:
        stripped = line.strip()
        lowered = stripped.lower()
        if "bypass permissions" in lowered:
            return True
        if _CLAUDE_PROMPT_ONLY_RE.match(stripped):
            return True
    return False


def _has_recent_live_progress_line(recent_lines: list[str]) -> bool:
    for line in recent_lines[-6:]:
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if "working (" in lowered or "worked for " in lowered:
            continue
        if "sautéed" in lowered or "baked" in lowered:
            continue
        if _RECENT_PROGRESS_LINE_RE.match(stripped):
            return True
    return False


def _extract_working_note(lines: list[str]) -> str:
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


def detect_agent_status(label: str, pane_text: str) -> tuple[str, str]:
    lines = [line.strip() for line in pane_text.splitlines() if line.strip()]
    if not lines:
        return "DEAD", ""
    lower = pane_text.lower()
    recent_lines = _recent_nonempty_lines(pane_text, 18)
    recent_lower = "\n".join(recent_lines).lower()
    has_recent_claude_prompt = label == "Claude" and _has_recent_claude_ready_prompt(recent_lines)
    has_recent_busy = _recent_busy_indicator(pane_text)
    has_recent_live_progress = _has_recent_live_progress_line(recent_lines)
    if (
        has_recent_claude_prompt
        and not has_recent_live_progress
        and not any(pattern in recent_lower for pattern in _CLAUDE_STRONG_LIVE_BUSY_PATTERNS)
    ):
        return "READY", ""
    if (
        has_recent_busy
        or has_recent_live_progress
        or "waited for background" in recent_lower
        or "without interrupting claude's current work" in recent_lower
    ):
        return "WORKING", _extract_working_note(lines)
    if label == "Gemini" and "esc to cancel" in recent_lower:
        return "WORKING", ""
    if label == "Codex" and ("› " in pane_text or "openai codex" in lower):
        return "READY", ""
    if label == "Claude" and ("❯" in pane_text or "claude code" in lower or "bypass permissions" in lower):
        return "READY", ""
    if label == "Gemini" and ("type your message" in lower or "gemini cli" in lower or "workspace" in lower):
        return "READY", ""
    return "BOOTING", ""


def rejoin_wrapped_pane_lines(text: str) -> str:
    if not text:
        return text
    result_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.rstrip()
        if not result_lines:
            result_lines.append(stripped)
            continue
        previous = result_lines[-1]
        is_natural_break = (
            not previous
            or previous.endswith((".", "!", "?", ":", ")", "]", "}", "─", "│", "┘", "┐", "┤", "┴"))
            or stripped.startswith(("•", "─", "│", "┌", "└", "├", "›", ">", "$", "#", "-", "*", "✓", "✗"))
            or stripped.startswith(("  •", "  -", "  *", "  ✓"))
            or not stripped
        )
        if is_natural_break:
            result_lines.append(stripped)
        else:
            result_lines[-1] = previous + " " + stripped.lstrip()
    return "\n".join(result_lines)


def capture_agent_panes(
    project: Path,
    *,
    history_lines: int,
    session: str,
    agent_index_names: dict[int, str],
    run: Callable[..., tuple[int, str]],
    timeout: float,
) -> dict[str, str]:
    code, output = run(
        ["tmux", "list-panes", "-t", f"{session}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
        timeout=timeout,
    )
    results: dict[str, str] = {}
    if code != 0 or not output:
        return results
    for raw in output.splitlines():
        try:
            idx_s, pane_id, dead = raw.split("|", 2)
            idx = int(idx_s)
        except ValueError:
            continue
        label = agent_index_names.get(idx, f"Pane {idx}")
        if dead == "1":
            results[label] = ""
            continue
        cap_code, captured = run(
            ["tmux", "capture-pane", "-J", "-p", "-t", pane_id, "-S", f"-{history_lines}"],
            timeout=timeout,
        )
        if cap_code != 0 or not captured:
            results[label] = ""
            continue
        cleaned = ANSI_RE.sub("", captured)
        results[label] = rejoin_wrapped_pane_lines(cleaned)
    return results


def _normalize_focus_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.rstrip().strip())


def format_focus_output(pane_text: str, max_lines: int = 40, max_chars: int = 300) -> str:
    if not pane_text.strip():
        return "(출력 없음)"
    lines = [line.rstrip() for line in pane_text.splitlines()]
    filtered = [line for line in lines if line.strip() and not BOX_DRAWING_ONLY_RE.match(line.strip())]
    if not filtered:
        return "(표시할 출력 없음)"
    interesting_markers = (
        "working",
        "cascading",
        "lollygagging",
        "hashing",
        "leavering",
        "read",
        "search",
        "searched",
        "bash(",
        "ran ",
        "updated plan",
        "goal:",
        "목표:",
        "변경",
        "검증",
        "thinking",
        "without interrupting",
        "background",
        "role:",
        "handoff:",
        "state:",
        "explored",
        "waiting",
        "write",
        "edit",
        "create",
        "error",
        "fail",
        "success",
        "complete",
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


def watcher_runtime_hints(
    project: Path,
    *,
    is_windows: bool,
    run: Callable[..., tuple[int, str]],
    wsl_path_str: Callable[[Path], str],
    file_query_timeout: float,
    now_fn: Callable[[], float] = time.time,
) -> dict[str, tuple[str, str]]:
    log_path = project / ".pipeline" / "logs" / "experimental" / "watcher.log"
    if is_windows:
        code, content = run(["tail", "-n", "300", wsl_path_str(log_path)], timeout=file_query_timeout)
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
    adapter = resolve_project_runtime_adapter(project)
    owners = dict(adapter.get("role_owners") or {})
    return watcher_runtime_hints_from_lines(
        lines,
        now_fn=now_fn,
        implement_owner=str(owners.get("implement") or ""),
        verify_owner=str(owners.get("verify") or ""),
        advisory_owner=str(owners.get("advisory") or ""),
    )


def watcher_runtime_hints_from_lines(
    lines: list[str],
    *,
    now_fn: Callable[[], float] = time.time,
    implement_owner: str = "",
    verify_owner: str = "",
    advisory_owner: str = "",
) -> dict[str, tuple[str, str]]:
    if not lines:
        return {}
    default_owners = default_role_bindings()
    implement_lane = str(implement_owner or default_owners["implement"]).strip()
    verify_lane = str(verify_owner or default_owners["verify"]).strip()
    advisory_lane = str(advisory_owner or default_owners["advisory"]).strip()
    role_started_at: dict[str, float | None] = {
        "implement": None,
        "verify": None,
        "advisory": None,
    }
    role_done: dict[str, bool] = {
        "implement": False,
        "verify": False,
        "advisory": False,
    }
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
            or "notify_implement_owner" in line
            or ("send-keys" in line and "pane_type=claude" in line)
            or "waiting_for_claude" in line
        ):
            role_started_at["implement"] = timestamp
            role_done["implement"] = False
        elif "activity detected by snapshot diff" in line or ("new job:" in line and role_started_at["implement"] is not None):
            role_done["implement"] = True
        if "lease acquired: slot=slot_verify" in line or "VERIFY_PENDING → VERIFY_RUNNING" in line:
            role_started_at["verify"] = timestamp
            role_done["verify"] = False
        elif (
            "task completed" in line
            or "lease released: slot=slot_verify" in line
            or "VERIFY_RUNNING → VERIFY_DONE" in line
        ):
            role_done["verify"] = True
        if "notify_gemini" in line or "notify_advisory_owner" in line or "gemini response activity" in line:
            role_started_at["advisory"] = timestamp
            role_done["advisory"] = False
        elif "gemini advice updated" in line:
            role_done["advisory"] = True
    now = now_fn()
    hints: dict[str, tuple[str, str]] = {}
    for role_name, lane_name, note_prefix in (
        ("implement", implement_lane, "impl"),
        ("verify", verify_lane, "verify"),
        ("advisory", advisory_lane, "advice"),
    ):
        if not lane_name:
            continue
        started_at = role_started_at[role_name]
        if started_at is not None and not role_done[role_name]:
            hints[lane_name] = ("WORKING", f"{note_prefix} {format_elapsed(now - started_at)}")
        elif role_done[role_name]:
            hints[lane_name] = ("READY", "")
    return hints
