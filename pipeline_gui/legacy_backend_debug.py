"""Legacy tmux/log observer helpers kept for debug and compatibility surfaces only."""
from __future__ import annotations

import os
import re
from collections.abc import Callable
from pathlib import Path

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def read_log_lines(
    path: Path,
    *,
    tail_count: int,
    is_windows: bool,
    run: Callable[..., tuple[int, str]],
    wsl_path_str: Callable[[Path], str],
    file_query_timeout: float,
) -> list[str]:
    if is_windows:
        code, content = run(["tail", "-n", str(tail_count), wsl_path_str(path)], timeout=file_query_timeout)
        if code != 0:
            return []
        return content.splitlines()
    if not path.exists():
        return []
    try:
        from collections import deque

        with open(path, encoding="utf-8", errors="replace") as handle:
            return [line.rstrip("\n") for line in deque(handle, maxlen=tail_count)]
    except OSError:
        return []


def clean_log_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    for line in lines:
        stripped = _ANSI_RE.sub("", line).strip()
        if not stripped:
            continue
        if set(stripped) == {"="}:
            continue
        cleaned.append(stripped)
    return cleaned


def tmux_alive(session: str, *, run: Callable[..., tuple[int, str]]) -> bool:
    code, _ = run(["tmux", "has-session", "-t", session or "ai-pipeline"])
    return code == 0


def watcher_alive(
    project: Path,
    *,
    is_windows: bool,
    run: Callable[..., tuple[int, str]],
    wsl_path_str: Callable[[Path], str],
) -> tuple[bool, int | None]:
    pid_path = project / ".pipeline" / "experimental.pid"
    if is_windows:
        code, content = run(["cat", wsl_path_str(pid_path)])
        if code != 0 or not content.strip():
            return False, None
        try:
            pid = int(content.strip())
        except ValueError:
            return False, None
        check_code, _ = run(["kill", "-0", str(pid)])
        return check_code == 0, pid
    if not pid_path.exists():
        return False, None
    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, 0)
        return True, pid
    except (ValueError, OSError):
        return False, None


def latest_md(
    directory: Path,
    *,
    is_windows: bool,
    run: Callable[..., tuple[int, str]],
    wsl_path_str: Callable[[Path], str],
    file_query_timeout: float,
) -> tuple[str, float]:
    if is_windows:
        code, output = run(
            [
                "find",
                wsl_path_str(directory),
                "-name",
                "*.md",
                "-type",
                "f",
                "-printf",
                "%T@\\t%P\\n",
            ],
            timeout=file_query_timeout,
        )
        if code != 0 or not output.strip():
            return "—", 0.0
        best_mtime = 0.0
        best_rel = ""
        for line in output.strip().splitlines():
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            try:
                mtime = float(parts[0])
            except ValueError:
                continue
            if mtime > best_mtime:
                best_mtime = mtime
                best_rel = parts[1]
        return (best_rel or "—"), best_mtime
    best_path: Path | None = None
    best_mtime = 0.0
    if not directory.exists():
        return "—", 0.0
    for candidate in directory.rglob("*.md"):
        try:
            mtime = candidate.stat().st_mtime
        except OSError:
            continue
        if mtime > best_mtime:
            best_mtime = mtime
            best_path = candidate
    if best_path is None:
        return "—", 0.0
    try:
        relative = str(best_path.relative_to(directory))
    except ValueError:
        relative = best_path.name
    return relative, best_mtime


def watcher_log_snapshot(
    project: Path,
    *,
    display_lines: int,
    summary_lines: int,
    hint_lines: int,
    read_log_lines: Callable[..., list[str]],
) -> dict[str, list[str]]:
    log_path = project / ".pipeline" / "logs" / "experimental" / "watcher.log"
    tail_count = max(display_lines * 8, 40, summary_lines, hint_lines)
    all_lines = read_log_lines(log_path, tail_count=tail_count)
    if not all_lines:
        return {
            "display_lines": ["(로그 없음)"],
            "summary_lines": [],
            "hint_lines": [],
        }
    filtered = [line for line in all_lines if "suppressed" not in line and "A/B ratio" not in line]
    return {
        "display_lines": filtered[-display_lines:] if filtered else ["(이벤트 없음)"],
        "summary_lines": all_lines[-summary_lines:],
        "hint_lines": all_lines[-hint_lines:],
    }


def watcher_start_observed(
    project: Path,
    *,
    not_before: float,
    is_windows: bool,
    run: Callable[..., tuple[int, str]],
    wsl_path_str: Callable[[Path], str],
    file_query_timeout: float,
    watcher_log_tail: Callable[[Path, int], list[str]],
) -> bool:
    log_path = project / ".pipeline" / "logs" / "experimental" / "watcher.log"
    if is_windows:
        code, stat_text = run(["stat", "-c", "%Y", wsl_path_str(log_path)], timeout=file_query_timeout)
        if code != 0 or not stat_text.strip():
            return False
        try:
            log_mtime = float(stat_text.strip())
        except ValueError:
            return False
    else:
        if not log_path.exists():
            return False
        try:
            log_mtime = log_path.stat().st_mtime
        except OSError:
            return False
    if log_mtime < not_before:
        return False

    lines = watcher_log_tail(project, 12)
    if not lines or lines[0].startswith("("):
        return False
    markers = (
        "WatcherCore v2.1 started",
        "initial turn:",
        "notify_claude:",
        "notify_gemini:",
        "notify_codex_followup:",
        "waiting_for_claude:",
    )
    return any(any(marker in line for marker in markers) for line in lines)
