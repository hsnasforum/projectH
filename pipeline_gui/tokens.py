"""Local token usage readers for Claude/Codex/Gemini CLI logs."""
from __future__ import annotations

import datetime as dt
import json
import time
from collections.abc import Callable
from pathlib import Path

from .formatting import format_compact_count
from .platform import IS_WINDOWS, _run, _windows_to_wsl_mount, resolve_project_runtime_file
from .token_usage_shared import (
    collect_all_token_usage as _shared_collect_all_token_usage,
    collect_claude_usage as _shared_collect_claude_usage,
    collect_codex_usage as _shared_collect_codex_usage,
    collect_gemini_usage as _shared_collect_gemini_usage,
    empty_summary as _shared_empty_summary,
)

_CACHE_TTL_SECONDS = 30.0
_TOKEN_CACHE: dict[str, tuple[float, dict[str, dict[str, object]]]] = {}
_DEFAULT_USAGE_SOURCES = {
    "Claude": "~/.claude/projects",
    "Codex": "~/.codex/sessions",
    "Gemini": "~/.gemini/tmp",
}


def _project_agnostic_reader(
    project: Path,
    reader: Callable[..., dict[str, object]],
    **kwargs: object,
) -> dict[str, object]:
    del project
    return reader(**kwargs)

def collect_claude_usage(
    project: Path,
    root: Path | None = None,
    today: dt.date | None = None,
) -> dict[str, object]:
    return _project_agnostic_reader(project, _shared_collect_claude_usage, root=root, today=today)


def collect_codex_usage(
    project: Path,
    root: Path | None = None,
    today: dt.date | None = None,
) -> dict[str, object]:
    return _project_agnostic_reader(project, _shared_collect_codex_usage, root=root, today=today)


def collect_gemini_usage(
    project: Path,
    root: Path | None = None,
    today: dt.date | None = None,
) -> dict[str, object]:
    del today
    return _project_agnostic_reader(project, _shared_collect_gemini_usage, root=root)


def format_token_usage_note(summary: dict[str, object]) -> str:
    if not summary or not summary.get("available"):
        return ""
    parts: list[str] = []
    used_percent = summary.get("used_percent")
    if isinstance(used_percent, (int, float)):
        parts.append(f"{round(float(used_percent))}% used")
    session_tokens = int(summary.get("session_tokens", 0) or 0)
    if session_tokens > 0:
        parts.append(f"Sess {format_compact_count(session_tokens)}")
    today_tokens = int(summary.get("today_tokens", 0) or 0)
    if today_tokens > 0 and today_tokens != session_tokens:
        parts.append(f"Today {format_compact_count(today_tokens)}")
    reset_at = str(summary.get("reset_at") or "")
    if reset_at and used_percent is not None:
        parts.append(f"Reset {reset_at}")
    return " · ".join(parts[:3])


def _normalize_result(raw: object) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {
        key: _shared_empty_summary(source)
        for key, source in _DEFAULT_USAGE_SOURCES.items()
    }
    if not isinstance(raw, dict):
        return result
    for key in result:
        value = raw.get(key)
        if isinstance(value, dict):
            result[key].update(value)
    return result


def _collect_token_usage_via_wsl(project: Path) -> dict[str, dict[str, object]]:
    script_path = resolve_project_runtime_file(project, "token_usage_shared.py")
    code, output = _run(["python3", _windows_to_wsl_mount(script_path)], timeout=12.0)
    if code != 0 or not output:
        return _normalize_result({})
    try:
        return _normalize_result(json.loads(output))
    except json.JSONDecodeError:
        return _normalize_result({})


def collect_token_usage(project: Path) -> dict[str, dict[str, object]]:
    cache_key = "__global__"
    cached = _TOKEN_CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    if IS_WINDOWS:
        result = _collect_token_usage_via_wsl(project)
    else:
        result = _shared_collect_all_token_usage()
    result = _normalize_result(result)
    _TOKEN_CACHE[cache_key] = (now, result)
    return result
