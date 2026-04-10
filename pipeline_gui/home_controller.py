from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from .agents import (
    AGENT_INDEX_NAMES,
    ANSI_RE,
    _extract_run_summary,
    detect_agent_status,
    extract_quota_note,
    merge_agent_status_hint,
    rejoin_wrapped_pane_lines,
    watcher_runtime_hints,
    watcher_runtime_hints_from_lines,
)
from .backend import (
    current_verify_activity,
    latest_md,
    parse_control_slots,
    read_turn_state,
    tmux_alive,
    watcher_alive,
    watcher_log_snapshot,
)
from .home_models import HomeSnapshot
from .platform import TMUX_QUERY_TIMEOUT, _run
from .token_queries import load_token_dashboard
from .tokens import collect_token_usage


class HomeController:
    def __init__(self, project: Path, session_name: str) -> None:
        self.project = project
        self.session_name = session_name
        self._pane_capture_cache: dict[str, dict[str, object]] = {}
        self._pane_capture_ttl_sec: float = 3.0
        self._token_usage_cache: dict[str, dict[str, object]] = {}
        self._token_usage_project_key: str = str(project)
        self._token_usage_last_refresh: float = 0.0
        self._token_usage_refresh_in_flight = False
        self._token_usage_lock = threading.Lock()
        self._token_dashboard_cache: object | None = None
        self._token_dashboard_project_key: str = str(project)
        self._token_dashboard_last_refresh: float = 0.0
        self._token_dashboard_refresh_in_flight = False
        self._token_dashboard_lock = threading.Lock()
        self._latest_md_cache: dict[str, tuple[str, float, float]] = {}

    def set_project(self, project: Path) -> None:
        if self.project == project:
            return
        self.project = project
        self._token_usage_project_key = str(project)
        self._token_usage_cache = {}
        self._token_usage_last_refresh = 0.0
        self._token_usage_refresh_in_flight = False
        self._token_dashboard_project_key = str(project)
        self._token_dashboard_cache = None
        self._token_dashboard_last_refresh = 0.0
        self._token_dashboard_refresh_in_flight = False
        self._latest_md_cache = {}

    def set_session_name(self, session_name: str) -> None:
        self.session_name = session_name

    def token_dashboard_loading(self) -> bool:
        with self._token_dashboard_lock:
            return self._token_dashboard_refresh_in_flight and self._token_dashboard_cache is None

    def collect_all_agent_data(
        self,
        *,
        selected_agent: str,
        hints: dict[str, tuple[str, str]] | None = None,
    ) -> tuple[list[tuple[str, str, str, str]], dict[str, str]]:
        code, output = _run(
            ["tmux", "list-panes", "-t", f"{self.session_name}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
            timeout=TMUX_QUERY_TIMEOUT,
        )
        if code != 0 or not output:
            return ([(name, "OFF", "", "") for name in AGENT_INDEX_NAMES.values()], {})

        hints = hints if hints is not None else watcher_runtime_hints(self.project)
        now = time.time()
        agents: list[tuple[str, str, str, str]] = []
        pane_map: dict[str, str] = {}
        seen_labels: set[str] = set()

        for raw in output.splitlines():
            try:
                idx_s, pane_id, dead = raw.split("|", 2)
                idx = int(idx_s)
            except ValueError:
                continue
            label = AGENT_INDEX_NAMES.get(idx, f"Pane {idx}")
            seen_labels.add(label)
            if dead == "1":
                agents.append((label, "DEAD", "", ""))
                pane_map[label] = ""
                self._pane_capture_cache.pop(label, None)
                continue

            cached_entry = self._pane_capture_cache.get(label)
            hint_status = (hints.get(label) or ("", ""))[0]
            should_refresh = (
                cached_entry is None
                or str(cached_entry.get("pane_id") or "") != pane_id
                or label == selected_agent
                or hint_status == "WORKING"
                or (now - float(cached_entry.get("captured_at") or 0.0)) >= self._pane_capture_ttl_sec
            )

            if should_refresh:
                cap_code, captured = _run(
                    ["tmux", "capture-pane", "-J", "-p", "-t", pane_id, "-S", "-180"],
                    timeout=TMUX_QUERY_TIMEOUT,
                )
                if cap_code != 0 or not captured:
                    if cached_entry is not None:
                        agents.append(
                            (
                                label,
                                str(cached_entry.get("status") or "BOOTING"),
                                str(cached_entry.get("note") or ""),
                                str(cached_entry.get("quota") or ""),
                            )
                        )
                        pane_map[label] = str(cached_entry.get("text") or "")
                    else:
                        agents.append((label, "BOOTING", "", ""))
                        pane_map[label] = ""
                    continue

                cleaned = ANSI_RE.sub("", captured)
                status, note = detect_agent_status(label, cleaned)
                quota = extract_quota_note(cleaned)
                status, note = merge_agent_status_hint(label, status, note, hints.get(label))
                pane_text = rejoin_wrapped_pane_lines(cleaned)
                self._pane_capture_cache[label] = {
                    "pane_id": pane_id,
                    "captured_at": now,
                    "text": pane_text,
                    "status": status,
                    "note": note,
                    "quota": quota,
                }
                agents.append((label, status, note, quota))
                pane_map[label] = pane_text
                continue

            agents.append(
                (
                    label,
                    str(cached_entry.get("status") or "BOOTING"),
                    str(cached_entry.get("note") or ""),
                    str(cached_entry.get("quota") or ""),
                )
            )
            pane_map[label] = str(cached_entry.get("text") or "")

        stale_labels = [label for label in self._pane_capture_cache.keys() if label not in seen_labels]
        for label in stale_labels:
            self._pane_capture_cache.pop(label, None)
        return agents, pane_map

    def get_cached_token_usage(
        self,
        *,
        on_refresh: Callable[[str, dict[str, dict[str, object]]], None] | None = None,
    ) -> dict[str, dict[str, object]]:
        project_key = str(self.project)
        now = time.time()
        with self._token_usage_lock:
            if self._token_usage_project_key != project_key:
                self._token_usage_project_key = project_key
                self._token_usage_cache = {}
                self._token_usage_last_refresh = 0.0
                self._token_usage_refresh_in_flight = False
            cached = dict(self._token_usage_cache)
            last_refresh = self._token_usage_last_refresh
            in_flight = self._token_usage_refresh_in_flight
        if (not cached or (now - last_refresh) >= 30.0) and not in_flight:
            self.start_token_usage_refresh(on_refresh=on_refresh)
        return cached

    def start_token_usage_refresh(
        self,
        *,
        on_refresh: Callable[[str, dict[str, dict[str, object]]], None] | None = None,
        force: bool = False,
    ) -> None:
        project = Path(self.project)
        project_key = str(project)
        with self._token_usage_lock:
            if self._token_usage_project_key != project_key:
                self._token_usage_project_key = project_key
                self._token_usage_cache = {}
                self._token_usage_last_refresh = 0.0
                self._token_usage_refresh_in_flight = False
            if self._token_usage_refresh_in_flight:
                return
            if not force and self._token_usage_cache and (time.time() - self._token_usage_last_refresh) < 30.0:
                return
            self._token_usage_refresh_in_flight = True

        def _worker() -> None:
            try:
                result = collect_token_usage(project)
            except Exception:
                result = {}
            with self._token_usage_lock:
                if self._token_usage_project_key == project_key:
                    self._token_usage_cache = dict(result)
                    self._token_usage_last_refresh = time.time()
                self._token_usage_refresh_in_flight = False
            if on_refresh is not None:
                on_refresh(project_key, result)

        threading.Thread(target=_worker, daemon=True).start()

    def get_cached_token_dashboard(
        self,
        *,
        on_refresh: Callable[[str, object | None], None] | None = None,
    ) -> object | None:
        project_key = str(self.project)
        now = time.time()
        with self._token_dashboard_lock:
            if self._token_dashboard_project_key != project_key:
                self._token_dashboard_project_key = project_key
                self._token_dashboard_cache = None
                self._token_dashboard_last_refresh = 0.0
                self._token_dashboard_refresh_in_flight = False
            cached = self._token_dashboard_cache
            last_refresh = self._token_dashboard_last_refresh
            in_flight = self._token_dashboard_refresh_in_flight
        if (cached is None or (now - last_refresh) >= 30.0) and not in_flight:
            self.start_token_dashboard_refresh(on_refresh=on_refresh)
        return cached

    def start_token_dashboard_refresh(
        self,
        *,
        on_refresh: Callable[[str, object | None], None] | None = None,
        force: bool = False,
    ) -> None:
        project = Path(self.project)
        project_key = str(project)
        with self._token_dashboard_lock:
            if self._token_dashboard_project_key != project_key:
                self._token_dashboard_project_key = project_key
                self._token_dashboard_cache = None
                self._token_dashboard_last_refresh = 0.0
                self._token_dashboard_refresh_in_flight = False
            if self._token_dashboard_refresh_in_flight:
                return
            if (
                not force
                and self._token_dashboard_cache is not None
                and (time.time() - self._token_dashboard_last_refresh) < 30.0
            ):
                return
            self._token_dashboard_refresh_in_flight = True

        def _worker() -> None:
            try:
                dashboard = load_token_dashboard(project)
            except Exception:
                dashboard = None
            with self._token_dashboard_lock:
                if self._token_dashboard_project_key == project_key:
                    if dashboard is not None:
                        self._token_dashboard_cache = dashboard
                    self._token_dashboard_last_refresh = time.time()
                self._token_dashboard_refresh_in_flight = False
            if on_refresh is not None:
                on_refresh(project_key, dashboard)

        threading.Thread(target=_worker, daemon=True).start()

    def get_cached_latest_md(
        self,
        directory: Path,
        *,
        refresh_interval: float = 5.0,
    ) -> tuple[str, float]:
        cache_key = str(directory)
        now = time.time()
        cached = self._latest_md_cache.get(cache_key)
        if cached is not None:
            cached_name, cached_mtime, cached_at = cached
            if (now - cached_at) < refresh_interval:
                return cached_name, cached_mtime
        latest_name, latest_mtime = latest_md(directory)
        self._latest_md_cache[cache_key] = (latest_name, latest_mtime, now)
        return latest_name, latest_mtime

    def build_snapshot(
        self,
        *,
        selected_agent: str,
        on_token_usage_refresh: Callable[[str, dict[str, dict[str, object]]], None] | None = None,
        on_token_dashboard_refresh: Callable[[str, object | None], None] | None = None,
    ) -> HomeSnapshot:
        polled_at = time.time()
        session_ok = tmux_alive(self.session_name)
        watcher_ok, watcher_pid = watcher_alive(self.project)
        log_snapshot = watcher_log_snapshot(self.project, display_lines=14, summary_lines=50, hint_lines=300)
        watcher_hints = watcher_runtime_hints_from_lines(log_snapshot["hint_lines"])
        agents, pane_map = self.collect_all_agent_data(selected_agent=selected_agent, hints=watcher_hints)
        token_usage = self.get_cached_token_usage(on_refresh=on_token_usage_refresh)
        token_dashboard = self.get_cached_token_dashboard(on_refresh=on_token_dashboard_refresh)
        work_name, work_mtime = self.get_cached_latest_md(self.project / "work")
        verify_name, verify_mtime = self.get_cached_latest_md(self.project / "verify")
        return HomeSnapshot(
            session_ok=session_ok,
            watcher_alive=watcher_ok,
            watcher_pid=watcher_pid,
            agents=agents,
            pane_map=pane_map,
            token_usage=token_usage,
            token_dashboard=token_dashboard,
            work_name=work_name,
            work_mtime=work_mtime,
            verify_name=verify_name,
            verify_mtime=verify_mtime,
            log_lines=log_snapshot["display_lines"],
            run_summary=_extract_run_summary(log_snapshot["summary_lines"]),
            control_slots=parse_control_slots(self.project),
            verify_activity=current_verify_activity(self.project),
            turn_state=read_turn_state(self.project),
            polled_at=polled_at,
        )
