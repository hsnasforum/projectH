from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from .backend import (
    describe_turn_state,
    normalize_runtime_status,
    read_runtime_event_tail,
    read_runtime_status,
)
from .home_models import HomeSnapshot
from .token_queries import load_token_dashboard
from .tokens import collect_token_usage


class HomeController:
    def __init__(self, project: Path, session_name: str) -> None:
        self.project = project
        self.session_name = session_name
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

    def set_session_name(self, session_name: str) -> None:
        self.session_name = session_name

    def token_dashboard_loading(self) -> bool:
        with self._token_dashboard_lock:
            return self._token_dashboard_refresh_in_flight and self._token_dashboard_cache is None

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

    def build_snapshot(
        self,
        *,
        selected_agent: str,
        on_token_usage_refresh: Callable[[str, dict[str, dict[str, object]]], None] | None = None,
        on_token_dashboard_refresh: Callable[[str, object | None], None] | None = None,
    ) -> HomeSnapshot:
        polled_at = time.time()
        runtime_status = normalize_runtime_status(read_runtime_status(self.project))
        runtime_state = str(runtime_status.get("runtime_state") or "STOPPED")
        session_ok = runtime_state != "STOPPED"
        degraded_reason = str(runtime_status.get("degraded_reason") or "")
        automation_health = str(runtime_status.get("automation_health") or "ok")
        automation_reason_code = str(runtime_status.get("automation_reason_code") or "")
        automation_incident_family = str(runtime_status.get("automation_incident_family") or "")
        automation_next_action = str(runtime_status.get("automation_next_action") or "continue")
        automation_health_detail = str(runtime_status.get("automation_health_detail") or "")
        control_age_cycles = int(runtime_status.get("control_age_cycles") or 0)
        stale_control_seq = bool(runtime_status.get("stale_control_seq"))
        stale_control_cycle_threshold = int(runtime_status.get("stale_control_cycle_threshold") or 0)
        stale_advisory_pending = bool(runtime_status.get("stale_advisory_pending"))
        watcher = dict(runtime_status.get("watcher") or {})
        watcher_ok = bool(watcher.get("alive"))
        watcher_pid = watcher.get("pid")
        lanes = list(runtime_status.get("lanes") or [])
        agents = []
        lane_details: dict[str, dict[str, object]] = {}
        for lane in lanes:
            label = str(lane.get("name") or "")
            if not label:
                continue
            state = str(lane.get("state") or "OFF")
            note = str(lane.get("note") or "")
            progress_phase = str(lane.get("progress_phase") or "")
            display_note = f"progress:{progress_phase}" if progress_phase else note
            agents.append((label, state, display_note, ""))
            lane_details[label] = {
                "state": state,
                "note": note,
                "progress_phase": progress_phase,
                "progress_reason": str(lane.get("progress_reason") or ""),
                "attachable": bool(lane.get("attachable")),
                "pid": lane.get("pid"),
                "last_event_at": str(lane.get("last_event_at") or ""),
                "last_heartbeat_at": str(lane.get("last_heartbeat_at") or ""),
                "last_wrapper_event": str(lane.get("last_wrapper_event") or ""),
            }
        pane_map: dict[str, str] = {}
        token_usage = self.get_cached_token_usage(on_refresh=on_token_usage_refresh)
        token_dashboard = self.get_cached_token_dashboard(on_refresh=on_token_dashboard_refresh)
        role_owners = dict(runtime_status.get("role_owners") or {})
        artifacts = dict(runtime_status.get("artifacts") or {})
        latest_work = dict(artifacts.get("latest_work") or {})
        latest_verify = dict(artifacts.get("latest_verify") or {})
        work_name = str(latest_work.get("path") or "—")
        work_mtime = float(latest_work.get("mtime") or 0.0)
        verify_name = str(latest_verify.get("path") or "—")
        verify_mtime = float(latest_verify.get("mtime") or 0.0)
        compat = dict(runtime_status.get("compat") or {})
        turn_state = (
            dict(runtime_status.get("turn_state") or {})
            or dict(compat.get("turn_state") or {})
            or None
        )
        turn_description = describe_turn_state(turn_state, lane_details=lane_details)
        log_lines: list[str] = []
        for data in read_runtime_event_tail(self.project, max_lines=14):
            event_type = str(data.get("event_type") or "")
            payload = dict(data.get("payload") or {})
            if event_type == "automation_incident":
                health = str(payload.get("automation_health") or "")
                reason = str(payload.get("reason_code") or "")
                action = str(payload.get("next_action") or "")
                log_lines.append(" ".join(part for part in [event_type, health, reason, action] if part))
                continue
            lane_name = str(payload.get("lane") or payload.get("job_id") or payload.get("receipt_id") or "")
            suffix = f" {lane_name}" if lane_name else ""
            log_lines.append(f"{event_type}{suffix}".strip())
        active_round = dict(runtime_status.get("active_round") or {})
        progress = dict(runtime_status.get("progress") or {})
        verify_activity = None
        round_state = str(active_round.get("state") or "")
        if round_state in {"VERIFY_PENDING", "VERIFYING", "RECEIPT_PENDING"}:
            turn_active_lane = str((turn_state or {}).get("active_lane") or "").strip()
            verify_owner = str(role_owners.get("verify") or "").strip()
            verify_lane = (
                turn_active_lane
                if turn_description.get("active_role") == "verify"
                else ""
            ) or verify_owner
            verify_label = (
                f"{verify_lane} 검증 실행 중" if verify_lane else "verify 실행 중"
            ) if round_state != "VERIFY_PENDING" else (
                f"{verify_lane} 검증 준비 중" if verify_lane else "verify 준비 중"
            )
            verify_activity = {
                "job_id": str(active_round.get("job_id") or ""),
                "status": "VERIFY_RUNNING" if round_state != "VERIFY_PENDING" else "VERIFY_PENDING",
                "label": verify_label,
                "artifact_name": verify_name,
                "artifact_path": verify_name,
            }
        run_summary = {
            "job": str(active_round.get("job_id") or ""),
            "phase": str(progress.get("phase") or round_state),
            "turn": "" if turn_description["state"] == "IDLE" else turn_description["label"],
        }
        return HomeSnapshot(
            runtime_state=runtime_state,
            degraded_reason=degraded_reason,
            automation_health=automation_health,
            automation_reason_code=automation_reason_code,
            automation_incident_family=automation_incident_family,
            automation_next_action=automation_next_action,
            automation_health_detail=automation_health_detail,
            control_age_cycles=control_age_cycles,
            stale_control_seq=stale_control_seq,
            stale_control_cycle_threshold=stale_control_cycle_threshold,
            stale_advisory_pending=stale_advisory_pending,
            session_ok=session_ok,
            watcher_alive=watcher_ok,
            watcher_pid=watcher_pid,
            agents=agents,
            lane_details=lane_details,
            pane_map=pane_map,
            token_usage=token_usage,
            token_dashboard=token_dashboard,
            work_name=work_name,
            work_mtime=work_mtime,
            verify_name=verify_name,
            verify_mtime=verify_mtime,
            log_lines=log_lines,
            run_summary=run_summary,
            control_slots=dict(compat.get("control_slots") or {"active": None, "stale": []}),
            verify_activity=verify_activity,
            turn_state=turn_state,
            polled_at=polled_at,
        )
