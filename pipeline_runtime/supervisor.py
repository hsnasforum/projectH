from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from pipeline_gui.platform import resolve_project_runtime_file
from pipeline_gui.project import _session_name_for
from pipeline_gui.setup_profile import resolve_project_runtime_adapter

from .operator_autonomy import classify_operator_candidate
from .receipts import build_receipt, receipt_path, validate_manifest, write_receipt
from .schema import (
    RUNTIME_LANE_ORDER,
    atomic_write_json,
    append_jsonl,
    iso_utc,
    latest_round_markdown,
    latest_receipt,
    load_job_states,
    parse_iso_utc,
    parse_control_slots,
    read_control_meta,
    read_json,
    repo_relative,
)
from .tmux_adapter import TmuxAdapter
from .wrapper_events import append_wrapper_event, build_lane_read_models

_DEFAULT_TOKEN_SINCE_DAYS = 7
_WORK_PATH_RE = re.compile(r"(work/\d+/\d+/[^\s`]+\.md)")
_AUTH_LOGIN_REASON = "auth_login_required"
_AUTH_LOGIN_PATTERNS = (
    re.compile(r"invalid authentication credentials", re.IGNORECASE),
    re.compile(r"please run\s+/login", re.IGNORECASE),
    re.compile(r"api error:\s*401", re.IGNORECASE),
    re.compile(r'"type"\s*:\s*"authentication_error"', re.IGNORECASE),
)
_BUSY_TAIL_MARKERS = (
    "working (",
    "working for ",
    "• working",
    "◦ working",
    "inferring",
    "thinking with ",
)


class RuntimeSupervisor:
    def __init__(
        self,
        project_root: Path,
        *,
        session_name: str | None = None,
        run_id: str | None = None,
        mode: str = "experimental",
        poll_interval: float = 1.0,
        start_runtime: bool = True,
    ) -> None:
        self.project_root = project_root.resolve()
        self.base_dir = self.project_root / ".pipeline"
        self.session_name = session_name or _session_name_for(self.project_root)
        self.mode = mode
        self.poll_interval = poll_interval
        self.run_id = run_id or self._make_run_id()
        self.run_dir = self.base_dir / "runs" / self.run_id
        self.logs_dir = self.run_dir / "logs"
        self.receipts_dir = self.run_dir / "receipts"
        self.wrapper_events_dir = self.run_dir / "wrapper-events"
        self.task_hints_dir = self.run_dir / "task-hints"
        self.compat_dir = self.run_dir / "compat"
        self.backend_dir = self.run_dir / "backend"
        self.autonomy_state_path = self.base_dir / "state" / "autonomy_state.json"
        self.status_path = self.run_dir / "status.json"
        self.events_path = self.run_dir / "events.jsonl"
        self.current_run_path = self.base_dir / "current_run.json"
        self.pid_path = self.base_dir / "supervisor.pid"
        self.adapter = TmuxAdapter(self.project_root, self.session_name, run_id=self.run_id)
        self.runtime_adapter = resolve_project_runtime_adapter(self.project_root)
        self.runtime_lane_configs = list(self.runtime_adapter.get("lane_configs") or [])
        self.runtime_controls = dict(self.runtime_adapter.get("controls") or {})
        self.enabled_lanes = [
            str(name).strip()
            for name in list(self.runtime_adapter.get("enabled_lanes") or [])
            if str(name).strip()
        ] or list(RUNTIME_LANE_ORDER)
        self.role_owners = dict(self.runtime_adapter.get("role_owners") or {})
        self.runtime_state = "STARTING"
        self.degraded_reason = ""
        self.degraded_reasons: list[str] = []
        self._stop_requested = False
        self._runtime_started = False
        self._event_seq = 0
        self._last_control_key = ""
        self._last_duplicate_control_key = ""
        self._last_stale_operator_control_key = ""
        self._last_operator_gate_key = ""
        self._last_autonomy_key = ""
        self._last_lane_states: dict[str, str] = {}
        self._last_degraded_reason = ""
        self._lane_restart_counts: dict[str, int] = {}
        self._start_runtime = start_runtime
        self._launch_failed_reason = ""
        self._current_duplicate_control_marker: dict[str, Any] | None = None
        self._current_stale_operator_control_marker: dict[str, Any] | None = None
        self._current_operator_gate_marker: dict[str, Any] | None = None
        self._current_autonomy: dict[str, Any] | None = None

    def _make_run_id(self) -> str:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-p{os.getpid()}"

    def _find_cli_bin(self, name: str) -> str:
        candidate = shutil.which(name)
        if candidate:
            return candidate
        home = Path.home()
        direct_candidates = [
            home / ".local" / "bin" / name,
            Path("/usr/local/bin") / name,
        ]
        nvm_root = home / ".nvm" / "versions" / "node"
        if nvm_root.exists():
            for bin_dir in sorted(nvm_root.glob("*/bin")):
                direct_candidates.append(bin_dir / name)
        for path in direct_candidates:
            if path.exists() and os.access(path, os.X_OK):
                return str(path)
        raise FileNotFoundError(f"{name} binary not found")

    def _lane_command_override(self, lane_name: str) -> str:
        env_key = f"PIPELINE_RUNTIME_LANE_COMMAND_{lane_name.upper()}"
        template = str(os.environ.get(env_key) or "").strip()
        if not template:
            raw_json = str(os.environ.get("PIPELINE_RUNTIME_LANE_COMMANDS_JSON") or "").strip()
            if raw_json:
                try:
                    mapping = json.loads(raw_json)
                except json.JSONDecodeError:
                    mapping = {}
                if isinstance(mapping, dict):
                    template = str(mapping.get(lane_name) or "").strip()
        if not template:
            return ""
        context = {
            "project_root": str(self.project_root),
            "project_root_shlex": shlex.quote(str(self.project_root)),
            "run_id": self.run_id,
            "run_id_shlex": shlex.quote(self.run_id),
            "lane": lane_name,
            "lane_shlex": shlex.quote(lane_name),
            "session_name": self.session_name,
            "session_name_shlex": shlex.quote(self.session_name),
        }
        try:
            return template.format(**context)
        except KeyError:
            return template

    def _write_pid(self) -> None:
        self.pid_path.parent.mkdir(parents=True, exist_ok=True)
        self.pid_path.write_text(str(os.getpid()), encoding="utf-8")

    def _write_current_run_pointer(self) -> None:
        atomic_write_json(
            self.current_run_path,
            {
                "run_id": self.run_id,
                "status_path": repo_relative(self.status_path, self.project_root),
                "events_path": repo_relative(self.events_path, self.project_root),
                "updated_at": iso_utc(),
            },
        )

    def _append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self._event_seq += 1
        append_jsonl(
            self.events_path,
            {
                "seq": self._event_seq,
                "ts": iso_utc(),
                "run_id": self.run_id,
                "event_type": event_type,
                "source": "supervisor",
                "payload": payload,
            },
        )

    def _watcher_status(self) -> dict[str, Any]:
        pid_path = self.base_dir / "experimental.pid"
        if not pid_path.exists():
            return {"alive": False, "pid": None}
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            return {"alive": True, "pid": pid}
        except (OSError, ValueError):
            return {"alive": False, "pid": None}

    def _control_path(self, control: dict[str, Any]) -> Path | None:
        control_file = str(control.get("active_control_file") or control.get("file") or "").strip()
        if not control_file:
            return None
        normalized = control_file.replace("\\", "/")
        if normalized.startswith(".pipeline/"):
            return self.project_root / normalized
        if normalized in {
            "claude_handoff.md",
            "gemini_request.md",
            "gemini_advice.md",
            "operator_request.md",
        }:
            return self.base_dir / normalized
        if normalized.startswith("./"):
            return self.project_root / normalized[2:]
        if normalized.startswith("/"):
            return Path(normalized)
        return self.project_root / normalized

    def _control_handoff_sha(self, control: dict[str, Any]) -> str:
        control_path = self._control_path(control)
        if control_path is None or not control_path.exists():
            return ""
        return hashlib.sha256(control_path.read_bytes()).hexdigest()

    def _duplicate_control_marker(self, control: dict[str, Any]) -> dict[str, Any] | None:
        if str(control.get("active_control_status") or "") != "implement":
            return None
        control_path = self._control_path(control)
        if control_path is None or not control_path.exists():
            return None
        handoff_sha = self._control_handoff_sha(control)
        if not handoff_sha:
            return None
        raw_log = self.base_dir / "logs" / "experimental" / "raw.jsonl"
        if not raw_log.exists():
            return None
        try:
            raw_lines = raw_log.read_text(encoding="utf-8").splitlines()
        except OSError:
            return None
        control_seq = int(control.get("active_control_seq") or -1)
        active_control_updated_at = parse_iso_utc(str(control.get("active_control_updated_at") or ""))
        fallback: dict[str, Any] | None = None
        for raw in reversed(raw_lines[-400:]):
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            if str(entry.get("blocked_reason") or "") != "handoff_already_completed":
                continue
            if str(entry.get("path") or "") != str(control_path):
                continue
            if str(entry.get("handoff_sha") or "") != handoff_sha:
                continue
            if float(entry.get("at") or 0.0) and float(entry.get("at") or 0.0) < active_control_updated_at:
                continue
            marker = {
                "control_file": str(control.get("active_control_file") or ""),
                "control_seq": control_seq,
                "handoff_sha": handoff_sha,
                "reason": "handoff_already_completed",
                "blocked_fingerprint": str(entry.get("blocked_fingerprint") or ""),
                "routed_to": "codex_triage",
                "source_event": str(entry.get("event") or ""),
            }
            if marker["source_event"] == "codex_blocked_triage_notify":
                return marker
            if fallback is None and marker["source_event"] == "claude_blocked_detected":
                fallback = marker
        return fallback

    def _normalize_artifact_path(self, value: str | Path | None) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        path = Path(text)
        if path.is_absolute():
            try:
                path = path.resolve().relative_to(self.project_root)
            except ValueError:
                return ""
            text = str(path)
        return text.replace("\\", "/")

    def _default_autonomy_block(self) -> dict[str, Any]:
        return {
            "mode": "normal",
            "block_reason": "",
            "reason_code": "",
            "operator_policy": "",
            "decision_class": "",
            "decision_required": "",
            "based_on_work": "",
            "based_on_verify": "",
            "classification_source": "",
            "first_seen_at": "",
            "suppress_operator_until": "",
            "operator_eligible": False,
            "same_fingerprint_retries": 0,
            "last_self_heal_at": "",
            "last_self_triage_at": "",
        }

    def _load_autonomy_state(self) -> dict[str, Any]:
        data = read_json(self.autonomy_state_path)
        return data if isinstance(data, dict) else {}

    def _save_autonomy_state(self, data: dict[str, Any]) -> None:
        atomic_write_json(self.autonomy_state_path, data)

    def _control_text(self, control: dict[str, Any]) -> str:
        control_path = self._control_path(control)
        if control_path is None or not control_path.exists():
            return ""
        try:
            return control_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def _stale_operator_control_marker(
        self,
        control: dict[str, Any],
        job_states: list[dict[str, Any]],
        turn_state: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        control_status = str(control.get("active_control_status") or control.get("status") or "")
        if control_status != "needs_operator":
            return None
        control_path = self._control_path(control)
        if control_path is None or not control_path.exists():
            return None
        control_meta = read_control_meta(control_path)
        try:
            control_text = control_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        based_on_work = self._normalize_artifact_path(control_meta.get("based_on_work"))
        if based_on_work:
            referenced_work_paths = [based_on_work]
        else:
            referenced_work_paths = sorted(
                {
                    self._normalize_artifact_path(match.group(1))
                    for match in _WORK_PATH_RE.finditer(control_text)
                    if self._normalize_artifact_path(match.group(1))
                }
            )
        reason = str((turn_state or {}).get("reason") or "")
        retriage_active = (
            str((turn_state or {}).get("state") or "") == "CODEX_FOLLOWUP"
            and reason == "operator_wait_idle_retriage"
        )
        if not referenced_work_paths:
            if retriage_active:
                return {
                    "control_file": str(control.get("active_control_file") or control.get("file") or ""),
                    "control_seq": int(control.get("active_control_seq") or control.get("control_seq") or -1),
                    "reason": "operator_wait_idle_retriage",
                    "resolved_work_paths": [],
                }
            return None
        verified_work_paths = {
            self._normalize_artifact_path(job_state.get("artifact_path"))
            for job_state in job_states
            if str(job_state.get("status") or "") == "VERIFY_DONE"
        }
        unresolved = [path for path in referenced_work_paths if path not in verified_work_paths]
        if unresolved:
            if retriage_active:
                return {
                    "control_file": str(control.get("active_control_file") or control.get("file") or ""),
                    "control_seq": int(control.get("active_control_seq") or control.get("control_seq") or -1),
                    "reason": "operator_wait_idle_retriage",
                    "resolved_work_paths": [],
                }
            return None
        return {
            "control_file": str(control.get("active_control_file") or control.get("file") or ""),
            "control_seq": int(control.get("active_control_seq") or control.get("control_seq") or -1),
            "reason": "verified_blockers_resolved",
            "resolved_work_paths": referenced_work_paths,
        }

    def _operator_gate_marker(
        self,
        control: dict[str, Any],
        *,
        turn_state: dict[str, Any] | None,
        active_round: dict[str, Any] | None,
        wrapper_models: dict[str, dict[str, Any]],
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        autonomy = self._default_autonomy_block()
        control_status = str(control.get("active_control_status") or control.get("status") or "")
        if control_status != "needs_operator":
            return None, autonomy

        control_path = self._control_path(control)
        if control_path is None or not control_path.exists():
            return None, autonomy
        control_meta = read_control_meta(control_path)

        try:
            control_mtime = float(control.get("mtime") or control_path.stat().st_mtime)
        except OSError:
            control_mtime = 0.0

        decision = classify_operator_candidate(
            self._control_text(control),
            control_meta=control_meta,
            control_path=str(control_path),
            control_seq=int(control.get("active_control_seq") or control.get("control_seq") or -1),
            control_mtime=control_mtime,
            turn_reason=str((turn_state or {}).get("reason") or ""),
            lane_notes=[
                str(model.get("failure_reason") or model.get("note") or "")
                for model in wrapper_models.values()
            ],
            idle_stable=not active_round or str((active_round or {}).get("state") or "") == "CLOSED",
        )
        persisted = self._load_autonomy_state()
        fingerprint = str(decision.get("fingerprint") or "")
        same_fingerprint = fingerprint and fingerprint == str(persisted.get("fingerprint") or "")
        retries = int(persisted.get("same_fingerprint_retries") or 0) if same_fingerprint else 0
        autonomy = {
            "mode": str(decision.get("mode") or "normal"),
            "block_reason": str(decision.get("block_reason") or ""),
            "reason_code": str(decision.get("reason_code") or ""),
            "operator_policy": str(decision.get("operator_policy") or ""),
            "decision_class": str(decision.get("decision_class") or ""),
            "decision_required": str(decision.get("decision_required") or ""),
            "based_on_work": str(decision.get("based_on_work") or ""),
            "based_on_verify": str(decision.get("based_on_verify") or ""),
            "classification_source": str(decision.get("classification_source") or ""),
            "first_seen_at": str(decision.get("first_seen_at") or ""),
            "suppress_operator_until": str(decision.get("suppress_operator_until") or ""),
            "operator_eligible": bool(decision.get("operator_eligible")),
            "same_fingerprint_retries": retries,
            "last_self_heal_at": (
                str(persisted.get("last_self_heal_at") or "")
                if same_fingerprint
                else (iso_utc() if str(decision.get("suppressed_mode") or "") == "recovery" else "")
            ),
            "last_self_triage_at": (
                str(persisted.get("last_self_triage_at") or "")
                if same_fingerprint
                else (
                    iso_utc()
                    if str(decision.get("suppressed_mode") or "") in {"triage", "pending_operator", "hibernate"}
                    else ""
                )
            ),
        }

        if bool(decision.get("operator_eligible")):
            return None, autonomy

        marker = {
            "control_file": str(control.get("active_control_file") or control.get("file") or ""),
            "control_seq": int(control.get("active_control_seq") or control.get("control_seq") or -1),
            "reason": str(decision.get("block_reason") or ""),
            "reason_code": str(decision.get("reason_code") or ""),
            "operator_policy": str(decision.get("operator_policy") or ""),
            "decision_class": str(decision.get("decision_class") or ""),
            "classification_source": str(decision.get("classification_source") or ""),
            "mode": str(decision.get("suppressed_mode") or ""),
            "routed_to": str(decision.get("routed_to") or ""),
            "suppress_operator_until": str(decision.get("suppress_operator_until") or ""),
            "fingerprint": fingerprint,
        }
        return marker, autonomy

    def _active_lane_for_runtime(
        self,
        turn_state: dict[str, Any] | None,
        active_round: dict[str, Any] | None,
        *,
        control: dict[str, Any] | None = None,
        last_receipt: dict[str, Any] | None = None,
        duplicate_control: dict[str, Any] | None = None,
        stale_operator_control: dict[str, Any] | None = None,
    ) -> str:
        if not turn_state:
            state = ""
        else:
            state = str(turn_state.get("state") or "")
        control = control or {}
        control_status = str(control.get("active_control_status") or "")
        control_seq = int(control.get("active_control_seq") or -1)
        last_receipt_seq = int((last_receipt or {}).get("control_seq") or -1)
        if (
            state == "CLAUDE_ACTIVE"
            and control_status == "implement"
            and control_seq >= 0
            and duplicate_control is None
            and control_seq > last_receipt_seq
        ):
            return str(self.role_owners.get("implement") or "Claude")
        if state in {"CODEX_VERIFY", "CODEX_FOLLOWUP"}:
            return str(self.role_owners.get("verify") or "Codex")
        if state == "GEMINI_ADVISORY":
            return str(self.role_owners.get("advisory") or "Gemini")
        if state == "OPERATOR_WAIT" and stale_operator_control is None:
            return ""

        round_state = str((active_round or {}).get("state") or "")
        if round_state in {"VERIFY_PENDING", "VERIFYING", "RECEIPT_PENDING"}:
            return str(self.role_owners.get("verify") or "Codex")
        return ""

    def _build_active_round(
        self,
        job_states: list[dict[str, Any]],
        last_receipt: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not job_states:
            return None
        latest_job = max(
            job_states,
            key=lambda data: (
                float(data.get("updated_at") or 0.0),
                float(data.get("last_activity_at") or 0.0),
                str(data.get("job_id") or ""),
            ),
        )
        job_id = str(latest_job.get("job_id") or "")
        round_number = int(latest_job.get("round") or 0)
        has_receipt = bool(
            last_receipt
            and last_receipt.get("job_id") == job_id
            and int(last_receipt.get("round") or -1) == round_number
        )
        status = str(latest_job.get("status") or "")
        round_state = {
            "NEW_ARTIFACT": "DISCOVERED",
            "STABILIZING": "STABILIZING",
            "VERIFY_PENDING": "VERIFY_PENDING",
            "VERIFY_RUNNING": "VERIFYING",
            "VERIFY_DONE": "CLOSED" if has_receipt else "RECEIPT_PENDING",
        }.get(status, status or "IDLE")
        return {
            "job_id": job_id,
            "round": round_number,
            "state": round_state,
            "artifact_path": str(latest_job.get("artifact_path") or ""),
            "status": status,
        }

    def _build_artifacts(self) -> dict[str, Any]:
        work_rel, work_mtime = latest_round_markdown(self.project_root / "work")
        verify_rel, verify_mtime = latest_round_markdown(self.project_root / "verify")
        return {
            "latest_work": {"path": work_rel, "mtime": work_mtime},
            "latest_verify": {"path": verify_rel, "mtime": verify_mtime},
        }

    def _task_hint_path(self, lane_name: str) -> Path:
        return self.task_hints_dir / f"{lane_name.strip().lower()}.json"

    def _write_task_hints(
        self,
        *,
        active_lane: str,
        active_round: dict[str, Any] | None,
        control: dict[str, Any],
        duplicate_control: dict[str, Any] | None = None,
    ) -> None:
        self.task_hints_dir.mkdir(parents=True, exist_ok=True)
        active_job_id = str((active_round or {}).get("job_id") or "")
        active_control_seq = int(control.get("active_control_seq") or -1)
        implement_owner = str(self.role_owners.get("implement") or "Claude")
        for lane_name in RUNTIME_LANE_ORDER:
            active = lane_name == active_lane and active_control_seq >= 0
            inactive_reason = ""
            if not active:
                if duplicate_control is not None and lane_name == implement_owner:
                    inactive_reason = "duplicate_handoff"
                else:
                    inactive_reason = "task_hint_cleared"
            payload = {
                "lane": lane_name,
                "active": active,
                "job_id": active_job_id if active else "",
                "control_seq": active_control_seq if active else -1,
                "attempt": self._lane_restart_counts.get(lane_name, 0) + 1,
                "inactive_reason": inactive_reason,
                "updated_at": iso_utc(),
            }
            atomic_write_json(self._task_hint_path(lane_name), payload)

    def _lane_should_surface_working(
        self,
        *,
        lane_name: str,
        active_lane: str,
        active_round: dict[str, Any] | None,
        turn_state: dict[str, Any] | None,
    ) -> bool:
        if lane_name != active_lane:
            return False
        turn_state_name = str((turn_state or {}).get("state") or "")
        if turn_state_name == "CLAUDE_ACTIVE":
            return True
        if turn_state_name == "CODEX_FOLLOWUP":
            return True
        if not active_round:
            return False
        if not str((active_round or {}).get("job_id") or ""):
            return False
        return str((active_round or {}).get("state") or "") in {"VERIFY_PENDING", "VERIFYING"}

    def _detect_active_lane_failure_reason(
        self,
        lane_name: str,
        *,
        active_lane: str,
        health: dict[str, Any],
    ) -> str:
        if lane_name != active_lane:
            return ""
        if not health.get("alive"):
            return ""
        try:
            tail_text = self.adapter.capture_tail(lane_name, lines=60)
        except Exception:
            return ""
        if not str(tail_text or "").strip():
            return ""
        for pattern in _AUTH_LOGIN_PATTERNS:
            if pattern.search(tail_text):
                return _AUTH_LOGIN_REASON
        return ""

    def _tail_has_busy_indicator(self, text: str) -> bool:
        lower = str(text or "").lower()
        if not lower.strip():
            return False
        return any(marker in lower for marker in _BUSY_TAIL_MARKERS)

    def _build_lane_statuses(
        self,
        *,
        wrapper_models: dict[str, dict[str, Any]],
        active_lane: str,
        active_round: dict[str, Any] | None,
        turn_state: dict[str, Any] | None = None,
        control: dict[str, Any] | None = None,
        duplicate_control: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        lanes: list[dict[str, Any]] = []
        lane_models: dict[str, dict[str, Any]] = {}
        implement_owner = str(self.role_owners.get("implement") or "Claude")
        control = control or {}
        lane_configs = self.runtime_lane_configs or [
            {"name": lane, "enabled": lane in self.enabled_lanes}
            for lane in RUNTIME_LANE_ORDER
        ]
        for lane_cfg in lane_configs:
            lane_name = str(lane_cfg.get("name") or "").strip()
            if not lane_name:
                continue
            enabled = bool(lane_cfg.get("enabled", lane_name in self.enabled_lanes))
            model = dict(wrapper_models.get(lane_name) or {})
            lane_models[lane_name] = model
            health = self.adapter.lane_health(lane_name) if enabled else {
                "alive": False,
                "pid": None,
                "attachable": False,
                "pane_id": None,
            }
            failure_reason = self._detect_active_lane_failure_reason(
                lane_name,
                active_lane=active_lane,
                health=health,
            )
            if failure_reason:
                model["failure_reason"] = failure_reason
            note = str(model.get("note") or "")
            last_event_at = str(model.get("last_event_at") or "")
            last_heartbeat_at = str(model.get("last_heartbeat_at") or "")
            if not enabled:
                state = "OFF"
            elif (
                duplicate_control is not None
                and lane_name == implement_owner
            ):
                state = "READY"
                note = "waiting_next_control"
            elif not health.get("alive"):
                state = "BROKEN" if model.get("state") else "OFF"
                if not note and state == "BROKEN":
                    note = "pane_dead"
            elif failure_reason:
                state = "BROKEN"
                note = failure_reason
            else:
                model_state = str(model.get("state") or "")
                implement_busy = False
                if (
                    duplicate_control is None
                    and lane_name == implement_owner
                    and str(control.get("active_control_status") or "") == "implement"
                    and model_state in {"READY", "WORKING"}
                ):
                    try:
                        implement_busy = self._tail_has_busy_indicator(
                            self.adapter.capture_tail(lane_name, lines=80)
                        )
                    except Exception:
                        implement_busy = False
                if implement_busy:
                    state = "WORKING"
                    if note in {"", "prompt_visible"}:
                        note = "implement"
                elif (
                    model_state in {"READY", "WORKING"}
                    and self._lane_should_surface_working(
                        lane_name=lane_name,
                        active_lane=active_lane,
                        active_round=active_round,
                        turn_state=turn_state,
                    )
                ):
                    state = "WORKING"
                    if note in {"", "prompt_visible"}:
                        turn_state_name = str((turn_state or {}).get("state") or "")
                        if turn_state_name == "CLAUDE_ACTIVE":
                            note = "implement"
                        elif turn_state_name == "CODEX_FOLLOWUP":
                            note = "followup"
                        else:
                            note = str((active_round or {}).get("state") or "").lower() or "active_round"
                elif model_state in {"READY", "WORKING", "BROKEN"}:
                    state = model_state
                elif model_state == "BOOTING" or not model_state:
                    state = "BOOTING"
                else:
                    state = "BOOTING"
            lanes.append(
                {
                    "name": lane_name,
                    "state": state,
                    "pid": health.get("pid"),
                    "attachable": bool(health.get("attachable")),
                    "last_event_at": last_event_at,
                    "last_heartbeat_at": last_heartbeat_at,
                    "note": note,
                }
            )
        return lanes, lane_models

    def _latest_verify_path(self) -> Path | None:
        verify_root = self.project_root / "verify"
        best_rel, _best_mtime = latest_round_markdown(verify_root)
        if best_rel == "—":
            return None
        return verify_root / best_rel

    def _reconcile_receipts(
        self,
        *,
        job_states: list[dict[str, Any]],
        active_control: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, str]:
        degraded_reason = ""
        if not job_states:
            return latest_receipt(self.receipts_dir), degraded_reason
        latest_job = max(
            job_states,
            key=lambda item: (
                float(item.get("updated_at") or 0.0),
                float(item.get("last_activity_at") or 0.0),
                str(item.get("job_id") or ""),
            ),
        )
        if str(latest_job.get("status") or "") != "VERIFY_DONE":
            return latest_receipt(self.receipts_dir), degraded_reason

        for job_state in [latest_job]:
            job_id = str(job_state.get("job_id") or "")
            round_number = int(job_state.get("round") or 0)
            target = receipt_path(self.receipts_dir, job_id, round_number)
            if target.exists():
                continue
            valid, reason = validate_manifest(job_state)
            if not valid:
                degraded_reason = f"receipt_manifest:{job_id}:{reason}"
                continue
            verify_path = self._latest_verify_path()
            if verify_path is None or not verify_path.exists():
                degraded_reason = f"receipt_verify_missing:{job_id}"
                continue
            control_seq = int((active_control or {}).get("control_seq") or -1)
            receipt = build_receipt(
                run_id=self.run_id,
                job_state=job_state,
                verify_artifact_path=verify_path,
                control_seq=control_seq,
                target_lane=str(self.role_owners.get("verify") or "Codex").lower(),
                closed_at=iso_utc(
                    float(job_state.get("verify_completed_at") or job_state.get("updated_at") or time.time())
                ),
            )
            write_receipt(self.receipts_dir, receipt)
            self._append_event(
                "receipt_written",
                {
                    "receipt_id": str(receipt.get("receipt_id") or ""),
                    "job_id": job_id,
                    "round": round_number,
                    "verify_result": receipt.get("verify_result"),
                },
            )
        return latest_receipt(self.receipts_dir), degraded_reason

    def _maybe_recover_lane(
        self,
        lane: dict[str, Any],
        *,
        lane_model: dict[str, Any],
        active_round: dict[str, Any] | None,
    ) -> str:
        lane_name = str(lane.get("name") or "")
        if self._stop_requested or not self._runtime_started:
            return ""
        if str(lane.get("state") or "") != "BROKEN":
            return ""
        failure_reason = str(lane_model.get("failure_reason") or lane.get("note") or "").strip()
        if failure_reason:
            return f"{lane_name.lower()}_{failure_reason}"
        accepted_task = dict(lane_model.get("accepted_task") or {})
        post_accept = bool(str(accepted_task.get("job_id") or ""))
        implement_owner = str(self.role_owners.get("implement") or "Claude")
        verify_owner = str(self.role_owners.get("verify") or "Codex")
        advisory_owner = str(self.role_owners.get("advisory") or "Gemini")

        if lane_name == implement_owner and post_accept:
            return f"{lane_name.lower()}_interrupted_post_accept"

        retry_limit = 1 if lane_name == implement_owner else 2 if lane_name in {verify_owner, advisory_owner} else 1
        retries = self._lane_restart_counts.get(lane_name, 0)
        round_state = str((active_round or {}).get("state") or "")
        completion_seen = round_state in {"CLOSED", "RECEIPT_PENDING"}
        if retries >= retry_limit or completion_seen:
            return f"{lane_name.lower()}_broken"

        lane_command = self._lane_shell_command(lane_name)
        self._append_event("recovery_started", {"lane": lane_name, "attempt": retries + 1})
        if self.adapter.restart_lane(lane_name, lane_command):
            self._lane_restart_counts[lane_name] = retries + 1
            self._append_event(
                "recovery_completed",
                {"lane": lane_name, "attempt": retries + 1, "result": "restarted"},
            )
            return ""
        return f"{lane_name.lower()}_recovery_failed"

    def _write_compat_files(self, status: dict[str, Any]) -> None:
        control_slots = dict((status.get("compat") or {}).get("control_slots") or {})
        atomic_write_json(self.compat_dir / "legacy-status.json", status)
        (self.compat_dir / "latest-work.txt").write_text(
            str(((status.get("artifacts") or {}).get("latest_work") or {}).get("path") or "—"),
            encoding="utf-8",
        )
        (self.compat_dir / "latest-verify.txt").write_text(
            str(((status.get("artifacts") or {}).get("latest_verify") or {}).get("path") or "—"),
            encoding="utf-8",
        )
        atomic_write_json(
            self.compat_dir / "control-slots.json",
            control_slots if isinstance(control_slots, dict) else {"active": None, "stale": []},
        )

    def _write_status(self) -> dict[str, Any]:
        turn_state = read_json(self.base_dir / "state" / "turn_state.json")
        control_slots = parse_control_slots(self.base_dir)
        active_control = dict(control_slots.get("active") or {})
        job_states = load_job_states(self.base_dir / "state")
        wrapper_models = build_lane_read_models(self.wrapper_events_dir)
        active_round_preview = self._build_active_round(job_states, latest_receipt(self.receipts_dir))
        stale_operator_control = self._stale_operator_control_marker(active_control, job_states, turn_state)
        operator_gate, autonomy = (
            (None, self._default_autonomy_block())
            if stale_operator_control is not None
            else self._operator_gate_marker(
                active_control,
                turn_state=turn_state if isinstance(turn_state, dict) else None,
                active_round=active_round_preview,
                wrapper_models=wrapper_models,
            )
        )
        self._current_stale_operator_control_marker = stale_operator_control
        self._current_operator_gate_marker = operator_gate
        effective_control = {} if stale_operator_control is not None or operator_gate is not None else active_control
        last_receipt, receipt_degraded = self._reconcile_receipts(
            job_states=job_states,
            active_control=effective_control or None,
        )
        active_round = self._build_active_round(job_states, last_receipt)
        if stale_operator_control is not None or operator_gate is not None:
            control_block = {
                "active_control_file": "",
                "active_control_seq": -1,
                "active_control_status": "none",
                "active_control_updated_at": "",
            }
        else:
            control_block = {
                "active_control_file": (
                    f".pipeline/{active_control.get('file')}"
                    if active_control.get("file")
                    else str((turn_state or {}).get("active_control_file") or "")
                ),
                "active_control_seq": int(
                    active_control.get("control_seq")
                    if active_control.get("control_seq") is not None
                    else (turn_state or {}).get("active_control_seq") or -1
                ),
                "active_control_status": str(active_control.get("status") or "none"),
                "active_control_updated_at": (
                    iso_utc(float(active_control.get("mtime") or time.time()))
                    if active_control.get("mtime")
                    else ""
                ),
            }
        duplicate_control = self._duplicate_control_marker(control_block)
        self._current_duplicate_control_marker = duplicate_control
        if duplicate_control is not None:
            control_block = {
                "active_control_file": "",
                "active_control_seq": -1,
                "active_control_status": "none",
                "active_control_updated_at": "",
            }
        active_lane = self._active_lane_for_runtime(
            turn_state,
            active_round,
            control=control_block,
            last_receipt=last_receipt,
            duplicate_control=duplicate_control,
            stale_operator_control=stale_operator_control or operator_gate,
        )
        self._write_task_hints(
            active_lane=active_lane,
            active_round=active_round,
            control=control_block,
            duplicate_control=duplicate_control,
        )
        lanes, lane_models = self._build_lane_statuses(
            wrapper_models=wrapper_models,
            active_lane=active_lane,
            active_round=active_round,
            turn_state=turn_state if isinstance(turn_state, dict) else None,
            control=control_block,
            duplicate_control=duplicate_control,
        )
        watcher = self._watcher_status()
        session_alive = self.adapter.session_exists()
        if not self._runtime_started and not session_alive and not watcher.get("alive"):
            lanes = [
                {
                    **lane,
                    "state": "OFF",
                    "pid": None,
                    "attachable": False,
                    "note": "",
                }
                for lane in lanes
            ]
        artifacts = self._build_artifacts()
        lane_configs = self.runtime_lane_configs or [
            {"name": lane, "enabled": lane in self.enabled_lanes}
            for lane in RUNTIME_LANE_ORDER
        ]
        configured_enabled_lanes = [
            lane_cfg
            for lane_cfg in lane_configs
            if bool(lane_cfg.get("enabled", str(lane_cfg.get("name") or "") in self.enabled_lanes))
        ]

        degraded_reasons = [item for item in [self._launch_failed_reason, receipt_degraded] if item]
        for lane in lanes:
            reason = self._maybe_recover_lane(
                lane,
                lane_model=lane_models.get(str(lane.get("name") or ""), {}),
                active_round=active_round,
            )
            if reason:
                degraded_reasons.append(reason)
        enabled_lanes = [lane for lane in lanes if str(lane.get("state") or "") != "OFF"]
        if self._runtime_started and not self._stop_requested and not session_alive and configured_enabled_lanes:
            degraded_reasons.append("session_missing")
        self.degraded_reasons = list(dict.fromkeys(item for item in degraded_reasons if item))
        self.degraded_reason = self.degraded_reasons[0] if self.degraded_reasons else ""

        ready_lanes = [
            lane
            for lane in enabled_lanes
            if str(lane.get("state") or "") in {"READY", "WORKING"}
        ]
        if self._stop_requested:
            self.runtime_state = "STOPPING"
        elif self._launch_failed_reason:
            self.runtime_state = "BROKEN"
        elif self.degraded_reason:
            self.runtime_state = "DEGRADED"
        elif not session_alive and not watcher.get("alive") and self._runtime_started:
            self.runtime_state = "STOPPED"
        elif watcher.get("alive") and enabled_lanes and len(ready_lanes) == len(enabled_lanes):
            self.runtime_state = "RUNNING"
        elif session_alive or watcher.get("alive"):
            self.runtime_state = "STARTING"
        else:
            self.runtime_state = "STOPPED"

        persisted_autonomy = self._load_autonomy_state()
        stable_idle = (
            control_block.get("active_control_status") == "none"
            and duplicate_control is None
            and stale_operator_control is None
            and operator_gate is None
            and (not active_round or str((active_round or {}).get("state") or "") == "CLOSED")
            and all(str(lane.get("state") or "") in {"READY", "OFF"} for lane in lanes)
        )
        if stale_operator_control is not None:
            autonomy = {
                **self._default_autonomy_block(),
                "mode": "recovery",
                "block_reason": str(stale_operator_control.get("reason") or ""),
                "last_self_heal_at": str(persisted_autonomy.get("last_self_heal_at") or iso_utc()),
            }
        elif stable_idle:
            autonomy = {
                **self._default_autonomy_block(),
                "mode": "hibernate",
                "block_reason": "idle_stable",
                "last_self_triage_at": str(persisted_autonomy.get("last_self_triage_at") or iso_utc()),
            }
        self._current_autonomy = autonomy
        desired_autonomy_state = {"fingerprint": str((operator_gate or {}).get("fingerprint") or ""), **autonomy}
        if desired_autonomy_state != persisted_autonomy:
            self._save_autonomy_state(desired_autonomy_state)

        if self.runtime_state in {"STOPPING", "STOPPED", "BROKEN"}:
            control_block = {
                "active_control_file": "",
                "active_control_seq": -1,
                "active_control_status": "none",
                "active_control_updated_at": "",
            }
            active_round = None

        status = {
            "schema_version": 1,
            "backend_type": "tmux",
            "run_id": self.run_id,
            "current_run_id": self.run_id,
            "runtime_state": self.runtime_state,
            "degraded_reason": self.degraded_reason,
            "degraded_reasons": list(self.degraded_reasons),
            "autonomy": autonomy,
            "control": control_block,
            "lanes": lanes,
            "active_round": active_round,
            "last_receipt": last_receipt,
            "last_receipt_id": str((last_receipt or {}).get("receipt_id") or ""),
            "watcher": watcher,
            "artifacts": artifacts,
            "compat": {
                "control_slots": control_slots,
                "turn_state": turn_state,
            },
            "last_heartbeat_at": iso_utc(),
            "updated_at": iso_utc(),
        }
        atomic_write_json(self.status_path, status)
        self._write_current_run_pointer()
        self._write_compat_files(status)
        return status

    def _record_status_events(self, status: dict[str, Any]) -> None:
        control = dict(status.get("control") or {})
        duplicate_control = dict(self._current_duplicate_control_marker or {})
        stale_operator_control = dict(self._current_stale_operator_control_marker or {})
        operator_gate = dict(self._current_operator_gate_marker or {})
        autonomy = dict(status.get("autonomy") or {})
        control_key = "|".join(
            [
                str(control.get("active_control_file") or ""),
                str(control.get("active_control_seq") or ""),
                str(control.get("active_control_status") or ""),
            ]
        )
        if control_key != self._last_control_key:
            self._last_control_key = control_key
            self._append_event("control_changed", control)

        duplicate_key = "|".join(
            [
                str(duplicate_control.get("control_file") or ""),
                str(duplicate_control.get("control_seq") or ""),
                str(duplicate_control.get("handoff_sha") or ""),
                str(duplicate_control.get("blocked_fingerprint") or ""),
            ]
        )
        if duplicate_key != self._last_duplicate_control_key:
            self._last_duplicate_control_key = duplicate_key
            if duplicate_control:
                self._append_event(
                    "control_duplicate_ignored",
                    {
                        "control_file": str(duplicate_control.get("control_file") or ""),
                        "control_seq": int(duplicate_control.get("control_seq") or -1),
                        "handoff_sha": str(duplicate_control.get("handoff_sha") or ""),
                        "reason": str(duplicate_control.get("reason") or ""),
                        "routed_to": str(duplicate_control.get("routed_to") or ""),
                    },
                )

        stale_operator_key = "|".join(
            [
                str(stale_operator_control.get("control_file") or ""),
                str(stale_operator_control.get("control_seq") or ""),
                str(stale_operator_control.get("reason") or ""),
                ",".join(str(item) for item in list(stale_operator_control.get("resolved_work_paths") or [])),
            ]
        )
        if stale_operator_key != self._last_stale_operator_control_key:
            self._last_stale_operator_control_key = stale_operator_key
            if stale_operator_control:
                self._append_event(
                    "control_operator_stale_ignored",
                    {
                        "control_file": str(stale_operator_control.get("control_file") or ""),
                        "control_seq": int(stale_operator_control.get("control_seq") or -1),
                        "reason": str(stale_operator_control.get("reason") or ""),
                        "resolved_work_paths": list(stale_operator_control.get("resolved_work_paths") or []),
                    },
                )

        operator_gate_key = "|".join(
            [
                str(operator_gate.get("control_file") or ""),
                str(operator_gate.get("control_seq") or ""),
                str(operator_gate.get("reason") or ""),
                str(operator_gate.get("mode") or ""),
                str(operator_gate.get("fingerprint") or ""),
            ]
        )
        if operator_gate_key != self._last_operator_gate_key:
            self._last_operator_gate_key = operator_gate_key
            if operator_gate:
                self._append_event(
                    "control_operator_gated",
                    {
                        "control_file": str(operator_gate.get("control_file") or ""),
                        "control_seq": int(operator_gate.get("control_seq") or -1),
                        "reason": str(operator_gate.get("reason") or ""),
                        "mode": str(operator_gate.get("mode") or ""),
                        "routed_to": str(operator_gate.get("routed_to") or ""),
                        "suppress_operator_until": str(operator_gate.get("suppress_operator_until") or ""),
                    },
                )

        autonomy_key = "|".join(
            [
                str(autonomy.get("mode") or ""),
                str(autonomy.get("block_reason") or ""),
                str(autonomy.get("first_seen_at") or ""),
                str(autonomy.get("suppress_operator_until") or ""),
            ]
        )
        if autonomy_key != self._last_autonomy_key:
            self._last_autonomy_key = autonomy_key
            self._append_event("autonomy_changed", autonomy)

        current_degraded = str(status.get("degraded_reason") or "")
        if current_degraded != self._last_degraded_reason:
            if current_degraded:
                self._append_event("degraded_entered", {"reason": current_degraded})
            elif self._last_degraded_reason:
                self._append_event("degraded_cleared", {"reason": self._last_degraded_reason})
            self._last_degraded_reason = current_degraded

        for lane in list(status.get("lanes") or []):
            lane_name = str(lane.get("name") or "")
            lane_state = str(lane.get("state") or "")
            previous = self._last_lane_states.get(lane_name)
            if previous == lane_state:
                continue
            self._last_lane_states[lane_name] = lane_state
            if lane_state == "WORKING":
                event_type = "lane_working"
            elif lane_state == "READY":
                event_type = "lane_ready"
            elif lane_state == "BROKEN":
                event_type = "lane_broken"
            elif lane_state == "BOOTING":
                event_type = "lane_booting"
            else:
                event_type = "lane_spawned"
            self._append_event(event_type, {"lane": lane_name, "state": lane_state})

    def _handle_signal(self, _signum: int, _frame: Any) -> None:
        self._stop_requested = True

    def _kill_pid(self, pid: int) -> None:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return
        deadline = time.time() + 3.0
        while time.time() < deadline:
            try:
                os.kill(pid, 0)
            except OSError:
                return
            time.sleep(0.1)
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    def _terminate_pid_file(self, path: Path) -> None:
        if not path.exists():
            return
        try:
            pid = int(path.read_text(encoding="utf-8").strip())
        except ValueError:
            pid = -1
        if pid > 0:
            self._kill_pid(pid)
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def _terminate_repo_watchers(self) -> None:
        result = subprocess.run(
            ["pgrep", "-f", r"watcher_core\.py|pipeline-watcher-v3(\-logged)?\.sh"],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        if result.returncode not in {0, 1}:
            return
        project_abs = str(self.project_root.resolve())
        for raw_pid in result.stdout.splitlines():
            raw_pid = raw_pid.strip()
            if not raw_pid.isdigit():
                continue
            pid = int(raw_pid)
            if pid in {os.getpid(), os.getppid()}:
                continue
            try:
                cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", errors="replace")
            except OSError:
                cmd = ""
            try:
                cwd = str(Path(os.readlink(f"/proc/{pid}/cwd")).resolve())
            except OSError:
                cwd = ""
            if cwd == project_abs or project_abs in cmd:
                self._kill_pid(pid)

    def _usage_path(self, name: str) -> Path:
        return self.base_dir / "usage" / name

    def _write_usage_text(self, name: str, value: str) -> None:
        path = self._usage_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def _clear_runtime_sidecars(self) -> None:
        for name in [
            "baseline.pid",
            "experimental.pid",
            "usage/collector.pid",
            "usage/collector.pane_id",
            "usage/collector.window_name",
            "usage/collector.launch_mode",
        ]:
            path = self.base_dir / name
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    def _prepare_runtime_surfaces(self) -> None:
        (self.base_dir / "logs" / "experimental").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "logs" / "baseline").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "state").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "locks").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "manifests").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "usage").mkdir(parents=True, exist_ok=True)
        self._usage_path("collector.log").write_text("", encoding="utf-8")
        for log_name in [
            "watcher.log",
            "raw.jsonl",
            "dispatch.jsonl",
            "pipeline-launcher-start.log",
        ]:
            (self.base_dir / "logs" / "experimental" / log_name).write_text("", encoding="utf-8")
        (self.base_dir / "logs" / "baseline" / "watcher.log").write_text("", encoding="utf-8")

    def _bash_prefixed(self, shell_command: str) -> str:
        prefix = 'if [ -s "$HOME/.nvm/nvm.sh" ]; then . "$HOME/.nvm/nvm.sh" 2>/dev/null; fi; '
        return prefix + shell_command

    def _lane_vendor_command(self, lane_name: str) -> str:
        override = self._lane_command_override(lane_name)
        if override:
            return override
        if lane_name == "Claude":
            return f'exec "{self._find_cli_bin("claude")}" --dangerously-skip-permissions'
        if lane_name == "Codex":
            return f'exec "{self._find_cli_bin("codex")}" --ask-for-approval never --disable apps'
        if lane_name == "Gemini":
            return f'exec "{self._find_cli_bin("gemini")}" --yolo'
        return "exec bash"

    def _lane_shell_command(self, lane_name: str) -> str:
        wrapper_args = [
            sys.executable,
            "-m",
            "pipeline_runtime.cli",
            "lane-wrapper",
            "--project-root",
            str(self.project_root),
            "--run-id",
            self.run_id,
            "--lane",
            lane_name,
            "--shell-command",
            self._lane_vendor_command(lane_name),
            "--task-hint-dir",
            str(self.task_hints_dir),
            "--heartbeat-interval",
            "5.0",
        ]
        command_parts: list[str] = []
        pythonpath = str(os.environ.get("PYTHONPATH") or "").strip()
        if pythonpath:
            command_parts.extend(
                [
                    "env",
                    f"PYTHONPATH={pythonpath}",
                    f"PROJECT_ROOT={self.project_root}",
                ]
            )
        command_parts.extend(wrapper_args)
        return self._bash_prefixed(shlex.join(command_parts))

    def _disabled_lane_command(self, lane_name: str) -> str:
        message = f"Physical lane {lane_name} disabled by active runtime plan; no runtime role is routed here."
        return f"printf '%s\\n' {shlex.quote(message)}; exec bash"

    def _role_owner(self, role_name: str) -> str:
        return str(self.role_owners.get(role_name) or "").strip() or {
            "implement": "Claude",
            "verify": "Codex",
            "advisory": "Gemini",
        }[role_name]

    def _role_read_first_doc(self, role_name: str) -> str:
        owner = self._role_owner(role_name)
        if owner == "Claude":
            return "CLAUDE.md"
        if owner == "Gemini":
            return "GEMINI.md"
        return "AGENTS.md"

    def _prompt_templates(self) -> dict[str, str]:
        return {
            "verify": (
                "ROLE: verify\n"
                f"OWNER: {self._role_owner('verify')}\n"
                "WORK: {latest_work_path}\n"
                "VERIFY: {latest_verify_path}\n"
                "NEXT_CONTROL_SEQ: {next_control_seq}\n"
                "GOAL:\n"
                "- verify the latest `/work` truthfully\n"
                "- leave or update `/verify` before any next control slot\n"
                "- then write exactly one next control outcome\n"
                "SCOPE_HINT:\n"
                "{verify_scope_hint}\n"
                "READ_FIRST:\n"
                f"- {self._role_read_first_doc('verify')}\n"
                "- work/README.md\n"
                "- verify/README.md\n"
                "OUTPUTS:\n"
                "- /verify note first\n"
                "- .pipeline/claude_handoff.md (STATUS: implement, CONTROL_SEQ: {next_control_seq})\n"
                "- .pipeline/gemini_request.md (STATUS: request_open, CONTROL_SEQ: {next_control_seq})\n"
                "- .pipeline/operator_request.md (STATUS: needs_operator, CONTROL_SEQ: {next_control_seq})\n"
                "RULES:\n"
                "- keep one exact next slice or one exact operator decision only\n"
                "- if you write .pipeline/operator_request.md, keep STATUS/CONTROL_SEQ in the first 12 lines and also include REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, and BASED_ON_VERIFY near the top\n"
                "- if the only blocker is next-slice ambiguity, overlapping candidates, or low-confidence prioritization, open .pipeline/gemini_request.md before .pipeline/operator_request.md\n"
                "- use .pipeline/operator_request.md without Gemini only for a real operator-only decision, approval/truth-sync blocker, immediate safety stop, or when Gemini is unavailable/already inconclusive\n"
                "- if same-day same-family docs-only truth-sync already repeated 3+ times, do not choose another narrower docs-only micro-slice; choose one bounded docs bundle or escalate"
            ),
            "implement": (
                "ROLE: implement\n"
                f"OWNER: {self._role_owner('implement')}\n"
                "HANDOFF: {active_handoff_path}\n"
                "HANDOFF_SHA: {active_handoff_sha}\n"
                "GOAL:\n"
                "- implement only the exact slice in the handoff\n"
                "- if finished, leave one `/work` closeout and stop\n"
                "READ_FIRST:\n"
                f"- {self._role_read_first_doc('implement')}\n"
                "- work/README.md\n"
                "- {active_handoff_path}\n"
                "RULES:\n"
                "- do not commit, push, publish a branch/PR, or choose the next slice\n"
                "- do not write .pipeline/gemini_request.md or .pipeline/operator_request.md yourself\n"
                "- if the handoff is blocked or not actionable, emit the exact sentinel below and stop\n"
                "BLOCKED_SENTINEL:\n"
                "STATUS: implement_blocked\n"
                "BLOCK_REASON: <short_reason>\n"
                "BLOCK_REASON_CODE: <reason_code>\n"
                "REQUEST: codex_triage\n"
                "ESCALATION_CLASS: codex_triage\n"
                "HANDOFF: {active_handoff_path}\n"
                "HANDOFF_SHA: {active_handoff_sha}\n"
                "BLOCK_ID: {active_handoff_sha}:<short_reason>"
            ),
            "advisory": (
                "ROLE: advisory\n"
                f"OWNER: {self._role_owner('advisory')}\n"
                "REQUEST: {gemini_request_mention}\n"
                "WORK: {latest_work_mention}\n"
                "VERIFY: {latest_verify_mention}\n"
                "NEXT_CONTROL_SEQ: {next_control_seq}\n"
                "GOAL:\n"
                "- leave one advisory log and one `.pipeline/gemini_advice.md`\n"
                "READ_FIRST:\n"
                f"- @{self._role_read_first_doc('advisory')}\n"
                "- {gemini_request_mention}\n"
                "- {latest_work_mention}\n"
                "- {latest_verify_mention}\n"
                "OUTPUTS:\n"
                "- advisory log: {gemini_report_path}\n"
                "- recommendation slot: {gemini_advice_path} (STATUS: advice_ready, CONTROL_SEQ: {next_control_seq})\n"
                "RULES:\n"
                "- pane-only answer is not completion\n"
                "- use edit/write tools only; no shell heredoc or shell redirection\n"
                "- do not modify other repo files\n"
                "- keep the recommendation short and exact"
            ),
            "followup": (
                "ROLE: followup\n"
                f"OWNER: {self._role_owner('verify')}\n"
                "NEXT_CONTROL_SEQ: {next_control_seq}\n"
                "REQUEST: .pipeline/gemini_request.md\n"
                "ADVICE: .pipeline/gemini_advice.md\n"
                "WORK: {latest_work_path}\n"
                "VERIFY: {latest_verify_path}\n"
                "GOAL:\n"
                "- convert the advisory into exactly one next control outcome\n"
                "READ_FIRST:\n"
                f"- {self._role_read_first_doc('verify')}\n"
                "- verify/README.md\n"
                "- .pipeline/gemini_request.md\n"
                "- .pipeline/gemini_advice.md\n"
                "OUTPUTS:\n"
                "- .pipeline/claude_handoff.md (STATUS: implement, CONTROL_SEQ: {next_control_seq})\n"
                "- .pipeline/operator_request.md (STATUS: needs_operator, CONTROL_SEQ: {next_control_seq})\n"
                "RULES:\n"
                "- write exactly one next control outcome\n"
                "- if you write .pipeline/operator_request.md, keep STATUS/CONTROL_SEQ in the first 12 lines and also include REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, and BASED_ON_VERIFY near the top\n"
                "- after Gemini advice, write .pipeline/operator_request.md only if the advice itself recommends a real operator decision or still leaves no truthful exact slice"
            ),
        }

    def _start_token_collector(self) -> None:
        if str(os.environ.get("PIPELINE_RUNTIME_DISABLE_TOKEN_COLLECTOR") or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            return
        try:
            script_path = resolve_project_runtime_file(self.project_root, "token_collector.py")
        except FileNotFoundError:
            return
        log_path = self._usage_path("collector.log")
        db_path = self._usage_path("usage.db")
        with log_path.open("a", encoding="utf-8") as handle:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-u",
                    str(script_path),
                    "--project-root",
                    str(self.project_root),
                    "--db-path",
                    str(db_path),
                    "--poll-interval",
                    "3.0",
                    "--daemon",
                    "--since-days",
                    str(_DEFAULT_TOKEN_SINCE_DAYS),
                ],
                cwd=str(self.project_root),
                stdout=handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        self._write_usage_text("collector.pid", str(proc.pid))
        self._write_usage_text("collector.pane_id", "")
        self._write_usage_text("collector.window_name", "")
        self._write_usage_text("collector.launch_mode", "background")

    def _stop_token_collector(self) -> None:
        self._terminate_pid_file(self._usage_path("collector.pid"))
        for name in ["collector.pane_id", "collector.window_name", "collector.launch_mode"]:
            try:
                self._usage_path(name).unlink()
            except FileNotFoundError:
                pass

    def _launch_runtime(self) -> None:
        self.adapter.kill_session()
        self._terminate_pid_file(self.base_dir / "baseline.pid")
        self._terminate_pid_file(self.base_dir / "experimental.pid")
        self._stop_token_collector()
        self._terminate_repo_watchers()
        self._prepare_runtime_surfaces()
        self._clear_runtime_sidecars()
        self.adapter.create_scaffold()

        lane_configs = self.runtime_lane_configs or [
            {"name": lane, "enabled": lane in self.enabled_lanes}
            for lane in RUNTIME_LANE_ORDER
        ]
        for lane_cfg in lane_configs:
            lane_name = str(lane_cfg.get("name") or "").strip()
            if not lane_name:
                continue
            enabled = bool(lane_cfg.get("enabled", lane_name in self.enabled_lanes))
            command = self._lane_shell_command(lane_name) if enabled else self._disabled_lane_command(lane_name)
            if not self.adapter.spawn_lane(lane_name, command):
                raise RuntimeError(f"lane spawn failed: {lane_name}")

        templates = self._prompt_templates()
        watcher_core_path = resolve_project_runtime_file(self.project_root, "watcher_core.py")
        watcher_log = self.base_dir / "logs" / "experimental" / "watcher.log"
        py_path = str(self.project_root)
        if os.environ.get("PYTHONPATH"):
            py_path = f"{py_path}:{os.environ['PYTHONPATH']}"
        watcher_args = [
            "env",
            f"PROJECT_ROOT={self.project_root}",
            "PIPELINE_RUNTIME_DISABLE_EXPORTER=1",
            f"PYTHONPATH={py_path}",
            sys.executable,
            str(watcher_core_path),
            "--watch-dir",
            str(self.project_root / "work"),
            "--base-dir",
            str(self.base_dir),
            "--repo-root",
            str(self.project_root),
            "--verify-pane-target",
            str((self.adapter.pane_for_lane("Codex") or {}).get("pane_id") or ""),
            "--claude-pane-target",
            str((self.adapter.pane_for_lane("Claude") or {}).get("pane_id") or ""),
            "--gemini-pane-target",
            str((self.adapter.pane_for_lane("Gemini") or {}).get("pane_id") or ""),
            "--verify-prompt",
            templates["verify"],
            "--implement-prompt",
            templates["implement"],
            "--advisory-prompt",
            templates["advisory"],
            "--followup-prompt",
            templates["followup"],
            "--startup-grace",
            "8",
            "--lease-ttl",
            "600",
        ]
        watcher_command = f"exec {shlex.join(watcher_args)} > {shlex.quote(str(watcher_log))} 2>&1"
        watcher_info = self.adapter.spawn_watcher(window_name="watcher-exp", shell_command=watcher_command)
        self.base_dir.joinpath("experimental.pid").write_text(str(watcher_info.get("pid") or ""), encoding="utf-8")

        if self.mode in {"baseline", "both"}:
            baseline_script = resolve_project_runtime_file(self.project_root, "pipeline-watcher-v3-logged.sh")
            baseline_log = self.base_dir / "logs" / "baseline" / "watcher.log"
            baseline_command = (
                f"exec bash {shlex.quote(str(baseline_script))} {shlex.quote(str(self.project_root))} "
                f"> {shlex.quote(str(baseline_log))} 2>&1"
            )
            baseline_info = self.adapter.spawn_watcher(window_name="watcher-baseline", shell_command=baseline_command)
            self.base_dir.joinpath("baseline.pid").write_text(str(baseline_info.get("pid") or ""), encoding="utf-8")

        self._start_token_collector()
        self._runtime_started = True

    def _stop_runtime(self) -> None:
        self._stop_token_collector()
        self._terminate_pid_file(self.base_dir / "experimental.pid")
        self._terminate_pid_file(self.base_dir / "baseline.pid")
        self._terminate_repo_watchers()
        self.adapter.kill_session()

    def run(self) -> int:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.wrapper_events_dir.mkdir(parents=True, exist_ok=True)
        self.task_hints_dir.mkdir(parents=True, exist_ok=True)
        self.compat_dir.mkdir(parents=True, exist_ok=True)
        self.backend_dir.mkdir(parents=True, exist_ok=True)
        self._write_pid()
        self._write_current_run_pointer()
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        self._append_event("runtime_started", {"runtime_state": self.runtime_state})
        if self._start_runtime:
            try:
                self._launch_runtime()
            except Exception as exc:
                self._launch_failed_reason = f"runtime_launch_failed:{type(exc).__name__}"
                (self.logs_dir / "launch-error.log").write_text(str(exc), encoding="utf-8")

        try:
            while True:
                status = self._write_status()
                self._record_status_events(status)
                if self._stop_requested:
                    break
                time.sleep(self.poll_interval)
        finally:
            self.runtime_state = "STOPPING"
            self._write_status()
            if self._runtime_started:
                self._stop_runtime()
            self._runtime_started = False
            self._stop_requested = False
            self.runtime_state = "STOPPED"
            final_status = self._write_status()
            self._record_status_events(final_status)
            self._append_event("runtime_stopped", {"runtime_state": "STOPPED"})
            try:
                self.pid_path.unlink()
            except FileNotFoundError:
                pass
        return 0
