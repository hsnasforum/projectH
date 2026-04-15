"""Active agent UI helpers; legacy pane/log observers are compat-only wrappers."""
from __future__ import annotations

import re
import time
from pathlib import Path

from . import legacy_agent_observers
from .formatting import format_elapsed as format_elapsed  # noqa: F811 — canonical + re-export
from .platform import (
    IS_WINDOWS, TMUX_QUERY_TIMEOUT, FILE_QUERY_TIMEOUT,
    _wsl_path_str, _run,
)
from .project import _session_name_for
from .setup_profile import SETUP_AGENT_ORDER

AGENT_INDEX_NAMES: dict[int, str] = {i: name for i, name in enumerate(SETUP_AGENT_ORDER)}

_ELAPSED_RE = re.compile(r"(\d+)\s*(h|m|s)")

STATUS_COLORS = {
    "WORKING": "#4ade80",
    "READY": "#5b9cf6",
    "DEAD": "#f87171",
    "BOOTING": "#e0a040",
    "OFF": "#404058",
}

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


def detect_agent_status(label: str, pane_text: str) -> tuple[str, str]:
    return legacy_agent_observers.detect_agent_status(label, pane_text)


def capture_agent_panes(project: Path, history_lines: int = 180, session: str = "") -> dict[str, str]:
    return legacy_agent_observers.capture_agent_panes(
        project,
        history_lines=history_lines,
        session=session or _session_name_for(project),
        agent_index_names=AGENT_INDEX_NAMES,
        run=_run,
        timeout=TMUX_QUERY_TIMEOUT,
    )


def rejoin_wrapped_pane_lines(text: str) -> str:
    return legacy_agent_observers.rejoin_wrapped_pane_lines(text)


def format_focus_output(pane_text: str, max_lines: int = 40, max_chars: int = 300) -> str:
    return legacy_agent_observers.format_focus_output(pane_text, max_lines=max_lines, max_chars=max_chars)


def watcher_runtime_hints(project: Path) -> dict[str, tuple[str, str]]:
    return legacy_agent_observers.watcher_runtime_hints(
        project,
        is_windows=IS_WINDOWS,
        run=_run,
        wsl_path_str=_wsl_path_str,
        file_query_timeout=FILE_QUERY_TIMEOUT,
        now_fn=time.time,
    )


def watcher_runtime_hints_from_lines(lines: list[str]) -> dict[str, tuple[str, str]]:
    return legacy_agent_observers.watcher_runtime_hints_from_lines(lines, now_fn=time.time)
