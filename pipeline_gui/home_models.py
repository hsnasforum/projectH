from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass
class AgentCardSnapshot:
    label: str
    status: str
    note: str
    quota: str


@dataclass
class ConsoleSnapshot:
    pane_map: dict[str, str]
    log_lines: list[str]
    run_summary: dict[str, object]


@dataclass
class TokenSnapshot:
    token_usage: dict[str, dict[str, object]]
    token_dashboard: object | None


@dataclass
class RuntimeLaunchSnapshot:
    resolved: dict[str, object]
    launch_allowed: bool


@dataclass
class HomeSnapshot:
    session_ok: bool
    watcher_alive: bool
    watcher_pid: int | None
    agents: list[tuple[str, str, str, str]]
    pane_map: dict[str, str]
    token_usage: dict[str, dict[str, object]]
    token_dashboard: object | None
    work_name: str
    work_mtime: float
    verify_name: str
    verify_mtime: float
    log_lines: list[str]
    run_summary: dict[str, object]
    control_slots: dict[str, object]
    verify_activity: dict[str, object] | None
    turn_state: dict[str, object] | None
    polled_at: float

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def updated(self, **kwargs: Any) -> "HomeSnapshot":
        return replace(self, **kwargs)
