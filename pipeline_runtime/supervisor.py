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
from watcher_prompt_assembly import (
    DEFAULT_ADVISORY_PROMPT,
    DEFAULT_FOLLOWUP_PROMPT,
    DEFAULT_IMPLEMENT_PROMPT,
    DEFAULT_VERIFY_PROMPT_TEMPLATE,
)

from .automation_health import advance_control_seq_age, derive_automation_health
from .lane_catalog import (
    build_lane_configs,
    default_role_bindings,
    lane_vendor_command_parts,
    legacy_watcher_pane_target_arg_for_lane,
    physical_lane_specs,
    read_first_doc_for_owner,
)
from .lane_surface import tail_has_busy_indicator, tail_has_ready_indicator, tail_surface_state
from .operator_autonomy import (
    OPERATOR_APPROVAL_COMPLETED_REASON,
    classify_operator_candidate,
    evaluate_stale_operator_control,
    operator_gate_marker_from_decision,
)
from .pr_merge_state import PrMergeStatusCache
from .role_routes import VERIFY_TRIAGE_ESCALATION
from .receipts import (
    build_receipt,
    manifest_feedback_path,
    receipt_path,
    validate_manifest,
    write_receipt,
)
from .schema import (
    RUNTIME_LANE_ORDER,
    ActiveControlSnapshot,
    active_control_snapshot_from_status,
    atomic_write_json,
    append_jsonl,
    control_block_from_snapshot,
    control_seq_value,
    control_slot_spec_for_filename,
    iter_control_slot_specs,
    iso_utc,
    latest_verify_note_for_work,
    latest_round_markdown,
    latest_receipt,
    load_job_states,
    parse_iso_utc,
    parse_control_slots,
    pipeline_control_snapshot_from_slots,
    process_starttime_fingerprint,
    read_control_meta,
    read_json,
    repo_relative,
    snapshot_control_seq,
)
from .tmux_adapter import TmuxAdapter
from .turn_arbitration import (
    active_lane_for_runtime,
    canonical_turn_state_name,
    suppress_active_round_for_turn,
)
from .wrapper_events import append_wrapper_event, build_lane_read_models, iter_wrapper_task_events

_DEFAULT_TOKEN_SINCE_DAYS = 7
_AUTH_LOGIN_REASON = "auth_login_required"
_AUTH_LOGIN_PATTERNS = (
    re.compile(r"invalid authentication credentials", re.IGNORECASE),
    re.compile(r"please run\s+/login", re.IGNORECASE),
    re.compile(r"api error:\s*401", re.IGNORECASE),
    re.compile(r'"type"\s*:\s*"authentication_error"', re.IGNORECASE),
)
# Lane failure reasons that cannot be cleared by a bounded restart attempt.
# Wrapper-surfaced exit/heartbeat/pane notes (e.g. ``exit:-15``, ``pane_dead``,
# ``heartbeat_timeout``) are recoverable pre-accept breakage and must consume
# retry budget instead of short-circuiting as terminal.
_TERMINAL_LANE_FAILURE_REASONS = frozenset({_AUTH_LOGIN_REASON})
_WATCHER_SELF_RESTART_SOURCE_NAMES = (
    "watcher_core.py",
    "watcher_dispatch.py",
    "watcher_prompt_assembly.py",
    "verify_fsm.py",
    "pipeline_runtime/lane_surface.py",
    "pipeline_runtime/role_harness.py",
    "pipeline_runtime/schema.py",
    "pipeline_runtime/turn_arbitration.py",
    "pipeline_runtime/operator_autonomy.py",
    "pipeline_runtime/pr_merge_state.py",
    "pipeline_runtime/wrapper_events.py",
)
_WATCHER_SELF_RESTART_COOLDOWN_SEC = 10.0
_SESSION_RECOVERY_RETRY_LIMIT = 1
_SESSION_RECOVERY_RESET_STABLE_SEC = 300.0
_CONTROL_SEQ_AGE_SLOT_FILES = frozenset(
    filename
    for spec in iter_control_slot_specs()
    if spec.slot_id != "advisory_advice"
    for filename in spec.accepted_filenames
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
        self.run_id = run_id or self._inherited_run_id_from_live_watcher() or self._make_run_id()
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
        self.started_at = time.time()
        self.role_owners = dict(self.runtime_adapter.get("role_owners") or {})
        self.prompt_owners = dict(self.runtime_adapter.get("prompt_owners") or self.role_owners)
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
        self._last_dispatch_stall_key = ""
        self._last_completion_stall_key = ""
        self._last_automation_incident_key = ""
        self._last_autonomy_key = ""
        self._last_lane_states: dict[str, str] = {}
        self._last_degraded_reason = ""
        self._lane_restart_counts: dict[str, int] = {}
        self._lane_override_events_emitted: set[str] = set()
        self._session_recovery_attempts = 0
        self._session_recovery_last_started_at = 0.0
        self._last_session_recovery_exhausted_key = ""
        self._start_runtime = start_runtime
        self._launch_failed_reason = ""
        self._current_duplicate_control_marker: dict[str, Any] | None = None
        self._current_stale_operator_control_marker: dict[str, Any] | None = None
        self._current_operator_gate_marker: dict[str, Any] | None = None
        self._current_dispatch_stall_marker: dict[str, Any] | None = None
        self._current_completion_stall_marker: dict[str, Any] | None = None
        self._current_autonomy: dict[str, Any] | None = None
        self._force_stopped_surface = False
        self._mirrored_wrapper_event_keys: set[str] = set()
        self._mirrored_wrapper_event_keys_seeded = False
        self._last_watcher_source_restart_key = ""
        self._last_watcher_source_restart_at = 0.0
        self._last_seen_control_seq: int | None = None
        self._control_seq_age_cycles = 0
        self._pr_merge_status_cache = PrMergeStatusCache()

    def _make_run_id(self) -> str:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-p{os.getpid()}"

    def _inherited_run_id_from_live_watcher(self) -> str:
        # supervisor restart 시 watcher가 그대로 살아있는 동안에는 watcher가 들고 있는
        # current run_id를 그대로 이어받아야 canonical `runs/<run_id>/status.json`이
        # watcher 쪽 current-run job state(예: startup-replayed VERIFY_PENDING)와 같은
        # 라인을 계속 비추게 된다. 다만 stale `current_run.json`이 다른 live watcher와
        # 섞여 잘못된 run을 이어받지 않도록, pointer가 직접 기록한 owner pid와 현재
        # `experimental.pid`가 같고, 같은 process instance 임을 증명하는 watcher
        # fingerprint(`/proc/<pid>/stat`의 starttime)까지 같을 때만 inheritance를
        # 허용한다. owner pid나 fingerprint가 없거나, mismatched이거나, live pid가
        # 죽었으면 fresh `_make_run_id()`가 그대로 이긴다. fingerprint를 같이 보면
        # 매우 짧은 시간 안에 같은 pid가 다른 process로 재사용되는 극단 케이스에서도
        # 잘못된 run을 이어받지 않는다.
        watcher_pid = self._live_experimental_watcher_pid()
        if watcher_pid <= 0:
            return ""
        live_fingerprint = self._watcher_process_fingerprint(watcher_pid)
        if not live_fingerprint:
            return ""
        current_run = read_json(self.base_dir / "current_run.json")
        if not isinstance(current_run, dict):
            return ""
        candidate = str(current_run.get("run_id") or "").strip()
        if not candidate:
            return ""
        pointer_owner_pid = self._coerce_pid(current_run.get("watcher_pid"))
        if pointer_owner_pid <= 0 or pointer_owner_pid != watcher_pid:
            return ""
        pointer_fingerprint = str(current_run.get("watcher_fingerprint") or "").strip()
        if not pointer_fingerprint or pointer_fingerprint != live_fingerprint:
            return ""
        return candidate

    @staticmethod
    def _coerce_pid(value: Any) -> int:
        if isinstance(value, bool):
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return 0
            try:
                return int(text)
            except ValueError:
                return 0
        return 0

    def _live_experimental_watcher_pid(self) -> int:
        pid_path = self.base_dir / "experimental.pid"
        if not pid_path.exists():
            return 0
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return 0
        if pid <= 0:
            return 0
        try:
            os.kill(pid, 0)
        except OSError:
            return 0
        return pid

    @staticmethod
    def _watcher_process_fingerprint(pid: int) -> str:
        # supervisor와 watcher exporter가 같은 ownership contract를 공유하도록,
        # process instance fingerprint 계산은 schema.process_starttime_fingerprint
        # 한 helper로 모은다. supervisor 쪽 호출자가 늘어나도 owner-match 정의가
        # drift 하지 않도록 계속 staticmethod 인터페이스로 노출만 유지한다.
        return process_starttime_fingerprint(pid)

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
        allow_override = str(os.environ.get("PIPELINE_RUNTIME_ALLOW_LANE_COMMAND_OVERRIDE") or "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        template = str(os.environ.get(env_key) or "").strip()
        source = env_key if template else ""
        if not template:
            raw_json = str(os.environ.get("PIPELINE_RUNTIME_LANE_COMMANDS_JSON") or "").strip()
            if raw_json:
                try:
                    mapping = json.loads(raw_json)
                except json.JSONDecodeError:
                    mapping = {}
                if isinstance(mapping, dict):
                    template = str(mapping.get(lane_name) or "").strip()
                    if template:
                        source = "PIPELINE_RUNTIME_LANE_COMMANDS_JSON"
        if not template:
            return ""
        if not allow_override:
            event_key = f"{lane_name}|{source}|ignored"
            if event_key not in self._lane_override_events_emitted:
                self._lane_override_events_emitted.add(event_key)
                self._append_event(
                    "lane_command_override_ignored",
                    {
                        "lane": lane_name,
                        "source": source,
                        "reason": "explicit_opt_in_required",
                    },
                )
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
            command = template.format(**context)
        except KeyError:
            command = template
        event_key = f"{lane_name}|{source}|{hashlib.sha256(command.encode('utf-8')).hexdigest()}"
        if event_key not in self._lane_override_events_emitted:
            self._lane_override_events_emitted.add(event_key)
            self._append_event(
                "lane_command_override",
                {
                    "lane": lane_name,
                    "source": source,
                    "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
                },
            )
        return command

    def _write_pid(self) -> None:
        self.pid_path.parent.mkdir(parents=True, exist_ok=True)
        self.pid_path.write_text(str(os.getpid()), encoding="utf-8")

    def _write_current_run_pointer(self) -> None:
        watcher_pid = self._live_experimental_watcher_pid()
        watcher_fingerprint = self._watcher_process_fingerprint(watcher_pid)
        atomic_write_json(
            self.current_run_path,
            {
                "run_id": self.run_id,
                "status_path": repo_relative(self.status_path, self.project_root),
                "events_path": repo_relative(self.events_path, self.project_root),
                "watcher_pid": watcher_pid,
                "watcher_fingerprint": watcher_fingerprint,
                "updated_at": iso_utc(),
            },
        )

    def _append_event(self, event_type: str, payload: dict[str, Any], *, source: str = "supervisor") -> None:
        self._event_seq += 1
        append_jsonl(
            self.events_path,
            {
                "seq": self._event_seq,
                "ts": iso_utc(),
                "run_id": self.run_id,
                "event_type": event_type,
                "source": source,
                "payload": payload,
            },
        )

    @staticmethod
    def _wrapper_task_event_key(event: dict[str, Any]) -> str:
        payload = dict(event.get("payload") or {})
        return "|".join(
            [
                str(event.get("lane") or payload.get("lane") or ""),
                str(event.get("event_type") or ""),
                str(event.get("ts") or payload.get("wrapper_ts") or ""),
                str(payload.get("job_id") or ""),
                str(payload.get("dispatch_id") or ""),
                str(payload.get("control_seq") or ""),
                str(payload.get("code") or ""),
                str(payload.get("reason") or ""),
            ]
        )

    def _seed_mirrored_wrapper_event_keys(self) -> None:
        if self._mirrored_wrapper_event_keys_seeded:
            return
        self._mirrored_wrapper_event_keys_seeded = True
        if not self.events_path.exists():
            return
        try:
            raw_lines = self.events_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return
        for raw_line in raw_lines:
            try:
                entry = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if str(entry.get("source") or "") != "wrapper":
                continue
            payload = dict(entry.get("payload") or {})
            key = self._wrapper_task_event_key(
                {
                    "lane": payload.get("lane"),
                    "event_type": entry.get("event_type"),
                    "ts": payload.get("wrapper_ts"),
                    "payload": payload,
                }
            )
            if key:
                self._mirrored_wrapper_event_keys.add(key)

    def _mirror_wrapper_task_events(self) -> None:
        self._seed_mirrored_wrapper_event_keys()
        for event in iter_wrapper_task_events(self.wrapper_events_dir):
            key = self._wrapper_task_event_key(event)
            if not key or key in self._mirrored_wrapper_event_keys:
                continue
            self._mirrored_wrapper_event_keys.add(key)
            raw_payload = dict(event.get("payload") or {})
            payload: dict[str, Any] = {
                "lane": str(event.get("lane") or raw_payload.get("lane") or ""),
                "job_id": str(raw_payload.get("job_id") or ""),
                "dispatch_id": str(raw_payload.get("dispatch_id") or ""),
                "control_seq": control_seq_value(raw_payload.get("control_seq"), default=-1),
                "derived_from": str(event.get("derived_from") or ""),
                "wrapper_ts": str(event.get("ts") or ""),
            }
            if raw_payload.get("attempt") is not None:
                payload["attempt"] = int(raw_payload.get("attempt") or 0)
            if raw_payload.get("reason"):
                payload["reason"] = str(raw_payload.get("reason") or "")
            if raw_payload.get("code"):
                payload["code"] = str(raw_payload.get("code") or "")
            if raw_payload.get("detail"):
                payload["detail"] = str(raw_payload.get("detail") or "")
            self._append_event(
                str(event.get("event_type") or ""),
                payload,
                source="wrapper",
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

    def _watcher_reload_sources(self) -> list[Path]:
        sources: list[Path] = []
        for name in _WATCHER_SELF_RESTART_SOURCE_NAMES:
            try:
                path = resolve_project_runtime_file(self.project_root, name)
            except FileNotFoundError:
                path = (Path(__file__).resolve().parent.parent / name).resolve()
            if path.exists():
                sources.append(path)
        return sources

    def _watcher_source_restart_marker(self) -> dict[str, Any] | None:
        pid = self._live_experimental_watcher_pid()
        if pid <= 0:
            return None
        pid_path = self.base_dir / "experimental.pid"
        try:
            pid_mtime = pid_path.stat().st_mtime
        except OSError:
            return None
        sources = self._watcher_reload_sources()
        if not sources:
            return None
        source_mtimes: list[tuple[float, Path]] = []
        for source_path in sources:
            try:
                source_mtimes.append((source_path.stat().st_mtime, source_path))
            except OSError:
                continue
        if not source_mtimes:
            return None
        newest_mtime, newest_path = max(source_mtimes, key=lambda item: item[0])
        if newest_mtime <= pid_mtime + 0.001:
            return None
        fingerprint = self._watcher_process_fingerprint(pid)
        key = f"{pid}|{fingerprint}|{newest_path}|{newest_mtime:.6f}"
        if key == self._last_watcher_source_restart_key:
            return None
        if time.time() - self._last_watcher_source_restart_at < _WATCHER_SELF_RESTART_COOLDOWN_SEC:
            return None
        return {
            "pid": pid,
            "watcher_fingerprint": fingerprint,
            "source_path": str(newest_path),
            "source_mtime": newest_mtime,
            "pidfile_mtime": pid_mtime,
            "restart_key": key,
            "reason": "watcher_source_updated",
        }

    def _control_path(self, control: dict[str, Any]) -> Path | None:
        snapshot = active_control_snapshot_from_status(control)
        control_file = str(snapshot.get("control_file") or control.get("file") or "").strip()
        if not control_file:
            return None
        normalized = control_file.replace("\\", "/")
        if normalized.startswith(".pipeline/"):
            return self.project_root / normalized
        if control_slot_spec_for_filename(normalized) is not None:
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

    def _control_block_from_snapshot(
        self,
        snapshot: ActiveControlSnapshot,
        *,
        control_age_cycles: int,
        is_legacy_alias: bool = False,
    ) -> dict[str, Any]:
        return control_block_from_snapshot(
            snapshot,
            control_age_cycles=control_age_cycles,
            is_legacy_alias=is_legacy_alias,
        )

    def _duplicate_control_marker(self, control: dict[str, Any]) -> dict[str, Any] | None:
        snapshot = active_control_snapshot_from_status(control)
        if str(snapshot.get("control_status") or "") != "implement":
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
        control_seq = snapshot_control_seq(snapshot)
        active_control_updated_at = parse_iso_utc(str(snapshot.get("control_updated_at") or ""))
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
                "control_file": str(snapshot.get("control_file") or ""),
                "control_seq": control_seq,
                "handoff_sha": handoff_sha,
                "reason": "handoff_already_completed",
                "blocked_fingerprint": str(entry.get("blocked_fingerprint") or ""),
                "routed_to": VERIFY_TRIAGE_ESCALATION,
                "source_event": str(entry.get("event") or ""),
            }
            if marker["source_event"] in {"verify_blocked_triage_notify", "codex_blocked_triage_notify"}:
                return marker
            if fallback is None and marker["source_event"] in {
                "implement_blocked_detected",
                "claude_blocked_detected",
            }:
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

    def _highest_control_seq_for_age(self, control_slots: dict[str, Any]) -> int | None:
        entries: list[dict[str, Any]] = []
        active = control_slots.get("active")
        if isinstance(active, dict):
            entries.append(active)
        for stale in list(control_slots.get("stale") or []):
            if isinstance(stale, dict):
                entries.append(stale)

        seqs: list[int] = []
        for entry in entries:
            if str(entry.get("file") or "") not in _CONTROL_SEQ_AGE_SLOT_FILES:
                continue
            seq = control_seq_value(entry.get("control_seq"), default=None)
            if seq is None:
                continue
            if seq >= 0:
                seqs.append(seq)
        if not seqs:
            return None
        return max(seqs)

    def _refresh_control_seq_age(self, control_slots: dict[str, Any]) -> int:
        try:
            current_seq = self._highest_control_seq_for_age(control_slots)
        except Exception:
            current_seq = None
        self._last_seen_control_seq, self._control_seq_age_cycles = advance_control_seq_age(
            last_seen_control_seq=self._last_seen_control_seq,
            control_seq_age_cycles=self._control_seq_age_cycles,
            current_control_seq=current_seq,
        )
        return self._control_seq_age_cycles

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
        snapshot = active_control_snapshot_from_status(control)
        turn_snapshot = active_control_snapshot_from_status(turn_state or {})
        control_status = str(snapshot.get("control_status") or "")
        if control_status != "needs_operator":
            return None
        control_file = str(snapshot.get("control_file") or "")
        control_seq = snapshot_control_seq(snapshot)
        control_path = self._control_path(control)
        if control_path is None or not control_path.exists():
            return None
        control_meta = read_control_meta(control_path)
        try:
            control_text = control_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        pr_merge_resolution = self._pr_merge_status_cache.control_resolution(
            self.project_root,
            control_text,
            control_meta,
        )
        reason = str((turn_state or {}).get("reason") or "")
        turn_state_name = canonical_turn_state_name(
            (turn_state or {}).get("state"),
            legacy_state=(turn_state or {}).get("legacy_state"),
        )
        verified_work_paths = {
            self._normalize_artifact_path(job_state.get("artifact_path"))
            for job_state in job_states
            if str(job_state.get("status") or "") == "VERIFY_DONE"
        }
        return evaluate_stale_operator_control(
            control_text=control_text,
            control_meta=control_meta,
            verified_work_paths=verified_work_paths,
            completed_pr_numbers=pr_merge_resolution.completed_pr_numbers,
            mismatched_pr_numbers=pr_merge_resolution.head_mismatch_pr_numbers,
            control_file=control_file,
            control_seq=control_seq,
            normalize_path=self._normalize_artifact_path,
            turn_state_name=turn_state_name,
            turn_reason=reason,
            turn_control_seq=snapshot_control_seq(turn_snapshot),
        )

    def _operator_gate_marker(
        self,
        control: dict[str, Any],
        *,
        turn_state: dict[str, Any] | None,
        active_round: dict[str, Any] | None,
        wrapper_models: dict[str, dict[str, Any]],
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        autonomy = self._default_autonomy_block()
        snapshot = active_control_snapshot_from_status(control)
        control_status = str(snapshot.get("control_status") or "")
        if control_status != "needs_operator":
            return None, autonomy
        control_file = str(snapshot.get("control_file") or "")
        control_seq = snapshot_control_seq(snapshot)

        control_path = self._control_path(control)
        if control_path is None or not control_path.exists():
            return None, autonomy
        control_meta = read_control_meta(control_path)

        try:
            control_mtime = float(control.get("mtime") or control_path.stat().st_mtime)
        except OSError:
            control_mtime = 0.0

        classify_kwargs = {
            "control_meta": control_meta,
            "control_path": str(control_path),
            "control_seq": control_seq,
            "control_mtime": control_mtime,
            "turn_reason": str((turn_state or {}).get("reason") or ""),
            "lane_notes": [
                str(model.get("failure_reason") or model.get("note") or "")
                for model in wrapper_models.values()
            ],
            "idle_stable": not active_round or str((active_round or {}).get("state") or "") == "CLOSED",
        }
        control_text = self._control_text(control)
        decision = classify_operator_candidate(control_text, **classify_kwargs)
        persisted = self._load_autonomy_state()
        fingerprint = str(decision.get("fingerprint") or "")
        same_fingerprint = fingerprint and fingerprint == str(persisted.get("fingerprint") or "")
        if same_fingerprint:
            persisted_first_seen_ts = parse_iso_utc(str(persisted.get("first_seen_at") or ""))
            if persisted_first_seen_ts > 0:
                decision = classify_operator_candidate(
                    control_text,
                    **classify_kwargs,
                    first_seen_ts=persisted_first_seen_ts,
                )
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

        marker = operator_gate_marker_from_decision(
            decision,
            control_file=control_file,
            control_seq=control_seq,
            fingerprint=fingerprint,
        )
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
        return active_lane_for_runtime(
            turn_state,
            active_round,
            control=control,
            last_receipt=last_receipt,
            duplicate_control=duplicate_control,
            stale_operator_control=stale_operator_control,
            implement_owner=self._prompt_owner("implement"),
            verify_owner=self._prompt_owner("verify"),
            advisory_owner=self._prompt_owner("advisory"),
        )

    def _build_active_round(
        self,
        job_states: list[dict[str, Any]],
        last_receipt: dict[str, Any] | None,
        *,
        active_control: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if not job_states:
            return None

        active_control_seq = snapshot_control_seq(
            active_control_snapshot_from_status(active_control or {})
        )

        # 동일 run 안에서도 실제 live verify 중인 job이나 receipt-close를 기다리는 job이
        # `updated_at`/`last_activity_at` 비교에서 stale real job에게 밀리지 않도록,
        # 먼저 liveness bucket 우선 순위를 보고 그 다음에 timestamp로 tie-break 합니다.
        # bucket 2: VERIFY_PENDING / VERIFY_RUNNING (live verify round).
        # bucket 1: VERIFY_DONE인데 matching receipt가 아직 없는 RECEIPT_PENDING round.
        # bucket 0: 그 외 (CLOSED VERIFY_DONE, NEW_ARTIFACT, STABILIZING, unknown).
        def _receipt_closes(data: dict[str, Any]) -> bool:
            if not last_receipt:
                return False
            return (
                str(last_receipt.get("job_id") or "") == str(data.get("job_id") or "")
                and int(last_receipt.get("round") or -1) == int(data.get("round") or 0)
            )

        def _dispatch_control_seq(data: dict[str, Any]) -> int:
            return control_seq_value(data.get("dispatch_control_seq"), default=-1)

        def _control_seq_rank(data: dict[str, Any]) -> int:
            if active_control_seq < 0:
                return 0
            return 1 if _dispatch_control_seq(data) == active_control_seq else 0

        def _liveness_rank(data: dict[str, Any]) -> int:
            status = str(data.get("status") or "")
            if status in {"VERIFY_PENDING", "VERIFY_RUNNING"}:
                return 2
            if status == "VERIFY_DONE" and not _receipt_closes(data):
                return 1
            return 0

        latest_job = max(
            job_states,
            key=lambda data: (
                _control_seq_rank(data),
                _liveness_rank(data),
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
        dispatch_id = str(latest_job.get("dispatch_id") or "")
        accepted_dispatch_id = str(latest_job.get("accepted_dispatch_id") or "")
        done_dispatch_id = str(latest_job.get("done_dispatch_id") or "")
        completion_stage = str(latest_job.get("completion_stall_stage") or "")
        if not completion_stage and dispatch_id:
            if done_dispatch_id == dispatch_id:
                completion_stage = "receipt_close_pending"
            elif accepted_dispatch_id == dispatch_id:
                completion_stage = "task_done_pending"
        return {
            "job_id": job_id,
            "round": round_number,
            "state": round_state,
            "artifact_path": str(latest_job.get("artifact_path") or ""),
            "status": status,
            "dispatch_id": dispatch_id,
            "dispatch_control_seq": _dispatch_control_seq(latest_job),
            "dispatch_stage": str(latest_job.get("dispatch_stall_stage") or ""),
            "completion_stage": completion_stage,
            "note": str(latest_job.get("lane_note") or ""),
            "degraded_reason": str(latest_job.get("degraded_reason") or ""),
        }

    def _suppress_active_round_for_turn(
        self,
        *,
        turn_state: dict[str, Any] | None,
        active_round: dict[str, Any] | None,
    ) -> bool:
        return suppress_active_round_for_turn(
            turn_state=turn_state,
            active_round=active_round,
        )

    def _job_matches_active_round(
        self,
        job_state: dict[str, Any],
        active_round: dict[str, Any] | None,
    ) -> bool:
        if not active_round:
            return False
        return (
            str(job_state.get("job_id") or "") == str(active_round.get("job_id") or "")
            and int(job_state.get("round") or 0) == int(active_round.get("round") or 0)
        )

    def _dispatch_stall_marker(
        self,
        job_states: list[dict[str, Any]],
        *,
        active_round: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not active_round:
            return None
        candidates = [
            job
            for job in job_states
            if float(job.get("dispatch_stall_detected_at") or 0.0) > 0.0
            and self._job_matches_active_round(job, active_round)
        ]
        if not candidates:
            return None
        latest_job = max(
            candidates,
            key=lambda data: (
                float(data.get("dispatch_stall_detected_at") or 0.0),
                float(data.get("updated_at") or 0.0),
                str(data.get("job_id") or ""),
            ),
        )
        detected_at = float(latest_job.get("dispatch_stall_detected_at") or 0.0)
        if detected_at <= 0.0:
            return None
        degraded_reason = str(latest_job.get("degraded_reason") or "")
        return {
            "job_id": str(latest_job.get("job_id") or ""),
            "round": int(latest_job.get("round") or 0),
            "fingerprint": str(latest_job.get("dispatch_stall_fingerprint") or ""),
            "attempt": int(latest_job.get("dispatch_stall_count") or 0),
            "detected_at": iso_utc(detected_at),
            "stage": str(latest_job.get("dispatch_stall_stage") or ""),
            "reason": str(latest_job.get("lane_note") or "waiting_task_accept_after_dispatch"),
            "degraded_reason": degraded_reason,
            "action": "degraded" if degraded_reason == "dispatch_stall" else "requeue",
            "lane": self._prompt_owner("verify"),
        }

    def _completion_stall_marker(
        self,
        job_states: list[dict[str, Any]],
        *,
        active_round: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not active_round:
            return None
        candidates = [
            job
            for job in job_states
            if float(job.get("completion_stall_detected_at") or 0.0) > 0.0
            and self._job_matches_active_round(job, active_round)
        ]
        if not candidates:
            return None
        latest_job = max(
            candidates,
            key=lambda data: (
                float(data.get("completion_stall_detected_at") or 0.0),
                float(data.get("updated_at") or 0.0),
                str(data.get("job_id") or ""),
            ),
        )
        detected_at = float(latest_job.get("completion_stall_detected_at") or 0.0)
        if detected_at <= 0.0:
            return None
        degraded_reason = str(latest_job.get("degraded_reason") or "")
        return {
            "job_id": str(latest_job.get("job_id") or ""),
            "round": int(latest_job.get("round") or 0),
            "fingerprint": str(latest_job.get("completion_stall_fingerprint") or ""),
            "attempt": int(latest_job.get("completion_stall_count") or 0),
            "detected_at": iso_utc(detected_at),
            "stage": str(latest_job.get("completion_stall_stage") or ""),
            "reason": str(latest_job.get("lane_note") or "waiting_task_done_after_accept"),
            "degraded_reason": degraded_reason,
            "action": "degraded" if degraded_reason == "post_accept_completion_stall" else "requeue",
            "lane": self._prompt_owner("verify"),
        }

    def _latest_verify_done_job_for_work(
        self,
        job_states: list[dict[str, Any]],
        work_value: str | Path | None,
    ) -> dict[str, Any] | None:
        normalized_work = self._normalize_artifact_path(work_value)
        if not normalized_work:
            return None
        candidates = [
            job_state
            for job_state in job_states
            if str(job_state.get("status") or "") == "VERIFY_DONE"
            and self._normalize_artifact_path(job_state.get("artifact_path")) == normalized_work
        ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda item: (
                float(item.get("verify_completed_at") or 0.0),
                float(item.get("updated_at") or 0.0),
                int(item.get("round") or 0),
                str(item.get("job_id") or ""),
            ),
        )

    def _verify_artifact_path_for_job(self, job_state: dict[str, Any]) -> Path | None:
        verify_path = manifest_feedback_path(job_state, repo_root=self.project_root)
        if verify_path is not None:
            return verify_path
        return self._matching_verify_path_for_work(job_state.get("artifact_path"))

    def _build_artifacts(self, *, job_states: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        work_rel, work_mtime = latest_round_markdown(self.project_root / "work")
        verify_rel = "—"
        verify_mtime = 0.0
        current_job_states = list(job_states or [])
        if work_rel != "—":
            work_path = self.project_root / "work" / work_rel
            verify_path = None
            matching_job = self._latest_verify_done_job_for_work(current_job_states, work_path)
            if matching_job is not None:
                verify_path = self._verify_artifact_path_for_job(matching_job)
            if verify_path is None:
                verify_path = self._matching_verify_path_for_work(work_path)
            if verify_path is not None:
                verify_rel = repo_relative(verify_path, self.project_root / "verify")
                try:
                    verify_mtime = verify_path.stat().st_mtime
                except OSError:
                    verify_rel = "—"
                    verify_mtime = 0.0
        else:
            verify_rel, verify_mtime = latest_round_markdown(self.project_root / "verify")
        work_date_key = ""
        if work_rel and work_rel != "—":
            work_date_key = Path(work_rel).name[:10]
        verify_date_key = ""
        if verify_rel and verify_rel != "—":
            verify_date_key = Path(verify_rel).name[:10]
        self._append_event(
            "dispatch_selection",
            {
                "latest_work": work_rel,
                "latest_verify": verify_rel,
                "date_key": work_date_key,
                "latest_work_mtime": work_mtime,
                "latest_verify_date_key": verify_date_key,
                "latest_verify_mtime": verify_mtime,
            },
        )
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
        turn_state: dict[str, Any] | None,
        control: dict[str, Any],
        duplicate_control: dict[str, Any] | None = None,
    ) -> None:
        self.task_hints_dir.mkdir(parents=True, exist_ok=True)
        active_job_id = str((active_round or {}).get("job_id") or "")
        active_dispatch_id = str((active_round or {}).get("dispatch_id") or "")
        active_dispatch_control_seq = (
            control_seq_value((active_round or {}).get("dispatch_control_seq"), default=-1)
        )
        control_snapshot = active_control_snapshot_from_status(control)
        active_control_seq = snapshot_control_seq(control_snapshot)
        turn_state_name = canonical_turn_state_name(
            (turn_state or {}).get("state"),
            legacy_state=(turn_state or {}).get("legacy_state"),
        )
        implement_owner = self._prompt_owner("implement")
        verify_owner = self._prompt_owner("verify")
        for lane_name in RUNTIME_LANE_ORDER:
            use_verify_round_hint = (
                lane_name == verify_owner
                and lane_name == active_lane
                and bool(active_job_id)
                and bool(active_dispatch_id)
                and turn_state_name not in {"VERIFY_FOLLOWUP", "ADVISORY_ACTIVE", "OPERATOR_WAIT"}
            )
            active = lane_name == active_lane and (
                use_verify_round_hint
                or active_control_seq >= 0
            )
            hint_control_seq = (
                active_dispatch_control_seq
                if use_verify_round_hint
                else active_control_seq
            )
            if lane_name == implement_owner and active and active_control_seq >= 0:
                hint_job_id = active_job_id or f"ctrl-{active_control_seq}"
                hint_dispatch_id = active_dispatch_id or f"seq-{active_control_seq}"
            else:
                hint_job_id = active_job_id if use_verify_round_hint else ""
                hint_dispatch_id = active_dispatch_id if use_verify_round_hint else ""
            inactive_reason = ""
            if not active:
                if duplicate_control is not None and lane_name == implement_owner:
                    inactive_reason = "duplicate_handoff"
                else:
                    inactive_reason = "task_hint_cleared"
            payload = {
                "lane": lane_name,
                "active": active,
                "job_id": hint_job_id,
                "dispatch_id": hint_dispatch_id,
                "control_seq": hint_control_seq if active else -1,
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
        turn_state_name = canonical_turn_state_name(
            (turn_state or {}).get("state"),
            legacy_state=(turn_state or {}).get("legacy_state"),
        )
        if turn_state_name == "IMPLEMENT_ACTIVE":
            return True
        if turn_state_name == "VERIFY_FOLLOWUP":
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
        return tail_has_busy_indicator(text)

    def _tail_has_ready_indicator(self, lane_name: str, text: str) -> bool:
        return tail_has_ready_indicator(lane_name, text)

    def _tail_surface_state(self, lane_name: str, text: str) -> str:
        return tail_surface_state(lane_name, text)

    def _build_progress_hint(
        self,
        *,
        active_lane: str,
        active_round: dict[str, Any] | None,
        turn_state: dict[str, Any] | None,
        control: dict[str, Any],
        autonomy: dict[str, Any],
        artifacts: dict[str, Any],
    ) -> dict[str, Any]:
        if self.runtime_state in {"STOPPED", "STOPPING", "BROKEN"}:
            return {}
        turn_state = turn_state if isinstance(turn_state, dict) else {}
        turn_name = canonical_turn_state_name(
            turn_state.get("state"),
            legacy_state=turn_state.get("legacy_state"),
        )
        if not turn_name or turn_name == "IDLE":
            return {}
        lane = str(turn_state.get("active_lane") or active_lane or "").strip()
        role = str(turn_state.get("active_role") or "").strip()
        entered_at = float(turn_state.get("entered_at") or 0.0)
        latest_work = dict((artifacts.get("latest_work") or {}) if isinstance(artifacts, dict) else {})
        latest_verify = dict((artifacts.get("latest_verify") or {}) if isinstance(artifacts, dict) else {})
        work_mtime = float(latest_work.get("mtime") or 0.0)
        verify_mtime = float(latest_verify.get("mtime") or 0.0)
        work_current = bool(entered_at and work_mtime and work_mtime >= entered_at)
        verify_current = bool(entered_at and verify_mtime and verify_mtime >= entered_at)
        control_snapshot = active_control_snapshot_from_status(control)
        control_status = str(control_snapshot.get("control_status") or "none")
        control_file = str(control_snapshot.get("control_file") or "")
        autonomy_mode = str(autonomy.get("mode") or "normal")
        autonomy_reason = str(autonomy.get("reason_code") or autonomy.get("block_reason") or "")
        round_state = str((active_round or {}).get("state") or "")
        phase = ""
        reason = ""

        if turn_name == "IMPLEMENT_ACTIVE":
            phase = "work_closeout_written" if work_current else "implementing"
        elif turn_name == "VERIFY_ACTIVE":
            if verify_current:
                phase = "verify_note_written_next_control_pending"
            elif round_state == "VERIFY_PENDING":
                phase = "verify_dispatch_pending"
            elif round_state == "RECEIPT_PENDING":
                phase = "receipt_close_pending"
            else:
                phase = "running_verification"
        elif turn_name == "VERIFY_FOLLOWUP":
            if autonomy_reason == OPERATOR_APPROVAL_COMPLETED_REASON:
                phase = OPERATOR_APPROVAL_COMPLETED_REASON
                reason = autonomy_reason
            elif control_status == "needs_operator" or autonomy_mode in {"pending_operator", "needs_operator"}:
                phase = "operator_gate_followup"
                reason = autonomy_reason or control_status
            elif control_status in {"implement", "request_open", "advice_ready"}:
                phase = "next_control_written"
            else:
                phase = "next_control_pending"
        elif turn_name == "ADVISORY_ACTIVE":
            phase = "advisory_running"
        elif turn_name in {"OPERATOR_WAIT", "NEEDS_OPERATOR"}:
            phase = "operator_boundary"
            reason = autonomy_reason or control_status

        if not phase:
            return {}
        return {
            "phase": phase,
            "lane": lane,
            "role": role,
            "turn_state": turn_name,
            "reason": reason,
            "control_file": control_file,
            "control_status": control_status,
        }

    @staticmethod
    def _annotate_lane_progress(lanes: list[dict[str, Any]], progress: dict[str, Any]) -> None:
        phase = str(progress.get("phase") or "")
        lane_name = str(progress.get("lane") or "")
        if not phase or not lane_name:
            return
        for lane in lanes:
            if str(lane.get("name") or "") != lane_name:
                continue
            lane["progress_phase"] = phase
            lane["progress_reason"] = str(progress.get("reason") or "")
            break

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
        implement_owner = self._prompt_owner("implement")
        verify_owner = self._prompt_owner("verify")
        control = control or {}
        control_snapshot = active_control_snapshot_from_status(control)
        control_status = str(control_snapshot.get("control_status") or "")
        active_control_seq = snapshot_control_seq(control_snapshot)
        lane_configs = self.runtime_lane_configs or build_lane_configs(
            enabled_lanes=self.enabled_lanes,
            role_owners=self.role_owners,
        )
        for lane_cfg in lane_configs:
            lane_name = str(lane_cfg.get("name") or "").strip()
            if not lane_name:
                continue
            enabled = bool(lane_cfg.get("enabled", lane_name in self.enabled_lanes))
            model = dict(wrapper_models.get(lane_name) or {})
            lane_models[lane_name] = model
            accepted_task = dict(model.get("accepted_task") or {})
            done_task = dict(model.get("done_task") or {})
            has_accepted_task = bool(str(accepted_task.get("job_id") or ""))
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
                active_round_note = str((active_round or {}).get("note") or "")
                tail_text = ""
                tail_surface = ""
                surface_working = (
                    model_state in {"READY", "WORKING"}
                    and self._lane_should_surface_working(
                        lane_name=lane_name,
                        active_lane=active_lane,
                        active_round=active_round,
                        turn_state=turn_state,
                    )
                )
                should_capture_tail = bool(health.get("attachable")) and (
                    model_state in {"READY", "WORKING"}
                    or lane_name == active_lane
                    or (
                        duplicate_control is None
                        and lane_name == implement_owner
                        and control_status == "implement"
                    )
                )
                if should_capture_tail:
                    try:
                        tail_text = self.adapter.capture_tail(lane_name, lines=80)
                    except Exception:
                        tail_text = ""
                    tail_surface = self._tail_surface_state(lane_name, tail_text)
                if has_accepted_task:
                    state = "WORKING"
                    if lane_name == implement_owner and control_status == "implement":
                        note = "implement"
                    elif lane_name == verify_owner:
                        round_state_note = str((active_round or {}).get("state") or "").strip().lower()
                        note = active_round_note or round_state_note or note or "working"
                    elif note in {"", "prompt_visible"}:
                        note = "working"
                elif (
                    duplicate_control is None
                    and lane_name == implement_owner
                    and control_status == "implement"
                    and tail_surface == "WORKING"
                ):
                    seen_task = dict(model.get("seen_task") or {})
                    if active_control_seq < 0:
                        state = "WORKING"
                        if note in {"", "prompt_visible"}:
                            note = "implement"
                    else:
                        activity_reason = str((turn_state or {}).get("reason") or "")
                        done_correlated = (
                            control_seq_value(done_task.get("control_seq"), default=-1) == active_control_seq
                        )
                        dispatch_correlated = (
                            control_seq_value(seen_task.get("control_seq"), default=-1) == active_control_seq
                            or control_seq_value(accepted_task.get("control_seq"), default=-1) == active_control_seq
                            or done_correlated
                            or activity_reason == "implement_activity_detected"
                            or activity_reason == f"{lane_name.lower()}_activity_detected"
                        )
                        if done_correlated:
                            state = "READY"
                            note = note or "waiting_next_control"
                        elif dispatch_correlated:
                            state = "WORKING"
                            if note in {"", "prompt_visible"}:
                                note = "implement"
                        else:
                            state = model_state if model_state and model_state != "WORKING" else "READY"
                            note = "signal_mismatch"
                elif surface_working and tail_surface == "READY":
                    state = "READY"
                    if lane_name == verify_owner and active_round_note:
                        note = active_round_note
                    elif lane_name == verify_owner:
                        note = str((active_round or {}).get("state") or "").lower() or "prompt_visible"
                    elif note in {"", "prompt_visible", "implement"}:
                        note = "prompt_visible"
                elif surface_working:
                    state = "WORKING"
                    if lane_name == verify_owner and active_round_note:
                        note = active_round_note
                    elif note in {"", "prompt_visible"}:
                        turn_state_name = canonical_turn_state_name(
                            (turn_state or {}).get("state"),
                            legacy_state=(turn_state or {}).get("legacy_state"),
                        )
                        if turn_state_name == "IMPLEMENT_ACTIVE":
                            note = "implement"
                        elif turn_state_name == "VERIFY_FOLLOWUP":
                            note = "followup"
                        else:
                            note = str((active_round or {}).get("state") or "").lower() or "active_round"
                elif model_state in {"READY", "WORKING"} and tail_surface and tail_surface != model_state:
                    state = tail_surface
                    if tail_surface == "READY":
                        if note in {"", "prompt_visible"} or model_state == "WORKING":
                            note = "prompt_visible"
                    elif note in {"", "prompt_visible"}:
                        if lane_name == implement_owner and control_status == "implement":
                            note = "implement"
                        elif lane_name == verify_owner and active_round_note:
                            note = active_round_note
                        elif lane_name == verify_owner and active_round:
                            note = str((active_round or {}).get("state") or "").lower() or "working"
                        else:
                            note = "working"
                elif model_state == "READY" and tail_surface == "READY" and note.startswith("dispatch_seen"):
                    state = "READY"
                    note = "prompt_visible"
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

    def _resolve_repo_path(self, value: str | Path | None) -> Path | None:
        text = str(value or "").strip()
        if not text:
            return None
        path = Path(text)
        if path.is_absolute():
            return path
        return self.project_root / path

    def _matching_verify_path_for_work(self, work_value: str | Path | None) -> Path | None:
        work_path = self._resolve_repo_path(work_value)
        if work_path is None:
            return None
        return latest_verify_note_for_work(
            self.project_root / "work",
            self.project_root / "verify",
            work_path,
            repo_root=self.project_root,
        )

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
            verify_path = self._verify_artifact_path_for_job(job_state)
            if verify_path is None or not verify_path.exists():
                degraded_reason = f"receipt_verify_missing:{job_id}"
                continue
            control_snapshot = active_control_snapshot_from_status(active_control or {})
            control_file = str(control_snapshot.get("control_file") or "")
            control_seq = snapshot_control_seq(control_snapshot)
            receipt = build_receipt(
                run_id=self.run_id,
                job_state=job_state,
                verify_artifact_path=verify_path,
                control_seq=control_seq,
                target_lane=self._prompt_owner("verify").lower(),
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
                    "control_file": control_file,
                    "control_seq": control_seq,
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
        if self._stop_requested:
            return ""
        if str(lane.get("state") or "") != "BROKEN":
            return ""
        failure_reason = str(lane_model.get("failure_reason") or lane.get("note") or "").strip()
        if failure_reason in _TERMINAL_LANE_FAILURE_REASONS:
            return f"{lane_name.lower()}_{failure_reason}"
        accepted_task = dict(lane_model.get("accepted_task") or {})
        post_accept = bool(str(accepted_task.get("job_id") or ""))
        implement_owner = self._prompt_owner("implement")
        verify_owner = self._prompt_owner("verify")
        advisory_owner = self._prompt_owner("advisory")

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
        self._lane_restart_counts[lane_name] = retries + 1
        if self.adapter.restart_lane(lane_name, lane_command):
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
        pipeline_control_snapshot = pipeline_control_snapshot_from_slots(control_slots)
        control_age_cycles = self._refresh_control_seq_age(control_slots)
        active_control = dict(pipeline_control_snapshot.get("active_entry") or {})
        active_control_snapshot = dict(pipeline_control_snapshot.get("active") or {})
        if not active_control_snapshot and isinstance(turn_state, dict):
            active_control_snapshot = active_control_snapshot_from_status(turn_state)
        active_control_block = self._control_block_from_snapshot(
            active_control_snapshot,
            control_age_cycles=control_age_cycles,
            is_legacy_alias=bool(active_control.get("is_legacy_alias")),
        )
        job_states = load_job_states(
            self.base_dir / "state",
            run_id=self.run_id,
            legacy_not_before=self.started_at - 5.0,
        )
        wrapper_models = build_lane_read_models(self.wrapper_events_dir)
        self._mirror_wrapper_task_events()
        force_stopped_surface = bool(self._force_stopped_surface)
        active_round_preview = self._build_active_round(
            job_states,
            latest_receipt(self.receipts_dir),
            active_control=active_control_block,
        )
        stale_operator_control = self._stale_operator_control_marker(active_control_block, job_states, turn_state)
        operator_gate, autonomy = (
            (None, self._default_autonomy_block())
            if stale_operator_control is not None
            else self._operator_gate_marker(
                active_control_block,
                turn_state=turn_state if isinstance(turn_state, dict) else None,
                active_round=active_round_preview,
                wrapper_models=wrapper_models,
            )
        )
        self._current_stale_operator_control_marker = stale_operator_control
        self._current_operator_gate_marker = operator_gate
        effective_control = {} if stale_operator_control is not None or operator_gate is not None else active_control_block
        last_receipt, receipt_degraded = self._reconcile_receipts(
            job_states=job_states,
            active_control=effective_control or None,
        )
        active_round = self._build_active_round(
            job_states,
            last_receipt,
            active_control=active_control_block,
        )
        if stale_operator_control is not None or operator_gate is not None:
            control_block = self._control_block_from_snapshot(
                {},
                control_age_cycles=control_age_cycles,
            )
        else:
            control_block = active_control_block
        duplicate_control = self._duplicate_control_marker(control_block)
        self._current_duplicate_control_marker = duplicate_control
        if duplicate_control is not None:
            control_block = self._control_block_from_snapshot(
                {},
                control_age_cycles=control_age_cycles,
            )
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
            turn_state=turn_state if isinstance(turn_state, dict) else None,
            control=control_block,
            duplicate_control=duplicate_control,
        )
        suppress_active_round = self._suppress_active_round_for_turn(
            turn_state=turn_state if isinstance(turn_state, dict) else None,
            active_round=active_round,
        )
        surfaced_active_round = None if suppress_active_round else active_round
        lanes, lane_models = self._build_lane_statuses(
            wrapper_models=wrapper_models,
            active_lane=active_lane,
            active_round=surfaced_active_round,
            turn_state=turn_state if isinstance(turn_state, dict) else None,
            control=control_block,
            duplicate_control=duplicate_control,
        )
        watcher = self._watcher_status()
        session_alive = self.adapter.session_exists()
        self._maybe_reset_session_recovery_budget(session_alive)
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
        artifacts = self._build_artifacts(job_states=job_states)
        lane_configs = self.runtime_lane_configs or build_lane_configs(
            enabled_lanes=self.enabled_lanes,
            role_owners=self.role_owners,
        )
        configured_enabled_lanes = [
            lane_cfg
            for lane_cfg in lane_configs
            if bool(lane_cfg.get("enabled", str(lane_cfg.get("name") or "") in self.enabled_lanes))
        ]
        runtime_inactive = (
            not self._runtime_started
            and not session_alive
            and not watcher.get("alive")
            and all(str(lane.get("state") or "") == "OFF" for lane in lanes)
        )

        active_breakage_reasons = [item for item in [receipt_degraded] if item]
        job_state_reasons: list[str] = []
        for job_state in job_states:
            if suppress_active_round:
                continue
            if surfaced_active_round and not self._job_matches_active_round(job_state, surfaced_active_round):
                continue
            reason = str(job_state.get("degraded_reason") or "").strip()
            if reason:
                job_state_reasons.append(reason)
        session_missing = bool(
            self._runtime_started
            and not self._stop_requested
            and not session_alive
            and configured_enabled_lanes
        )
        session_recovery_needed = session_missing and any(str(lane.get("state") or "") == "BROKEN" for lane in lanes)
        session_recovered = self._recover_missing_session() if session_recovery_needed else False
        session_recovery_exhausted = bool(
            session_missing
            and not session_recovered
            and self._session_recovery_attempts >= _SESSION_RECOVERY_RETRY_LIMIT
        )
        if session_recovery_exhausted:
            self._record_session_recovery_exhausted()
        lane_recover_reasons: list[str] = []
        if not session_recovered:
            for lane in lanes:
                reason = self._maybe_recover_lane(
                    lane,
                    lane_model=lane_models.get(str(lane.get("name") or ""), {}),
                    active_round=active_round,
                )
                if reason:
                    lane_recover_reasons.append(reason)
        active_breakage_reasons.extend(lane_recover_reasons)
        enabled_lanes = [lane for lane in lanes if str(lane.get("state") or "") != "OFF"]
        session_missing_reasons: list[str] = []
        if session_missing:
            session_missing_reasons.append("session_missing")
            if session_recovery_exhausted:
                session_missing_reasons.append("session_recovery_exhausted")
        if runtime_inactive and not self._launch_failed_reason:
            # Clean inactive runtime clears stale job-state reasons but keeps active
            # receipt / lane breakage visible so `runtime_state` does not drop to STOPPED
            # while the current boundary is still broken.
            degraded_reasons = list(active_breakage_reasons)
        else:
            # When the tmux session itself is gone, ``session_missing`` is the root
            # cause and per-lane ``*_recovery_failed`` entries are secondary evidence;
            # keep the representative reason on ``session_missing`` while preserving
            # the lane failures as later entries in ``degraded_reasons``.
            degraded_reasons = (
                ([self._launch_failed_reason] if self._launch_failed_reason else [])
                + session_missing_reasons
                + active_breakage_reasons
                + job_state_reasons
            )
        self.degraded_reasons = list(dict.fromkeys(item for item in degraded_reasons if item))
        self.degraded_reason = self.degraded_reasons[0] if self.degraded_reasons else ""
        if force_stopped_surface:
            self.degraded_reasons = []
            self.degraded_reason = ""

        ready_lanes = [
            lane
            for lane in enabled_lanes
            if str(lane.get("state") or "") in {"READY", "WORKING"}
        ]
        if force_stopped_surface:
            self.runtime_state = "STOPPED"
        elif self._stop_requested:
            self.runtime_state = "STOPPING"
        elif self._launch_failed_reason:
            self.runtime_state = "BROKEN"
        elif self.degraded_reason:
            self.runtime_state = "DEGRADED"
        elif runtime_inactive:
            self.runtime_state = "STOPPED"
        elif not session_alive and not watcher.get("alive") and self._runtime_started:
            self.runtime_state = "STOPPED"
        elif watcher.get("alive") and enabled_lanes and len(ready_lanes) == len(enabled_lanes):
            self.runtime_state = "RUNNING"
        elif session_alive or watcher.get("alive"):
            self.runtime_state = "STARTING"
        else:
            self.runtime_state = "STOPPED"

        persisted_autonomy = self._load_autonomy_state()
        control_snapshot = active_control_snapshot_from_status(control_block)
        stable_idle = (
            str(control_snapshot.get("control_status") or "none") == "none"
            and duplicate_control is None
            and stale_operator_control is None
            and operator_gate is None
            and (not surfaced_active_round or str((surfaced_active_round or {}).get("state") or "") == "CLOSED")
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
        autonomy_based_on_work = self._normalize_artifact_path(autonomy.get("based_on_work"))
        active_round_artifact = self._normalize_artifact_path((surfaced_active_round or {}).get("artifact_path"))
        if (
            autonomy_based_on_work
            and active_round_artifact
            and autonomy_based_on_work != active_round_artifact
        ):
            autonomy = self._default_autonomy_block()
        if self.runtime_state in {"STOPPING", "STOPPED"}:
            autonomy = self._default_autonomy_block()
        self._current_autonomy = autonomy
        desired_autonomy_state = {"fingerprint": str((operator_gate or {}).get("fingerprint") or ""), **autonomy}
        if desired_autonomy_state != persisted_autonomy:
            self._save_autonomy_state(desired_autonomy_state)

        if force_stopped_surface:
            turn_state = {
                "state": "IDLE",
                "legacy_state": "IDLE",
                "entered_at": time.time(),
                "reason": "runtime_stopped",
                "active_control_file": "",
                "active_control_seq": -1,
                "active_role": "",
                "active_lane": "",
            }
            control_block = self._control_block_from_snapshot(
                {},
                control_age_cycles=control_age_cycles,
            )
            surfaced_active_round = None
            watcher = {"alive": False, "pid": None}
            lanes = [
                {
                    **lane,
                    "state": "OFF",
                    "attachable": False,
                    "pid": None,
                    "note": "",
                }
                for lane in lanes
            ]
            self._write_task_hints(
                active_lane="",
                active_round=None,
                turn_state=turn_state,
                control=control_block,
                duplicate_control=duplicate_control,
            )
        elif self.runtime_state in {"STOPPING", "STOPPED", "BROKEN"}:
            control_block = self._control_block_from_snapshot(
                {},
                control_age_cycles=control_age_cycles,
            )
            # stopped runtime에서도 receipt-close를 기다리는 round는 launcher/controller가
            # current truth로 계속 보이게 유지합니다. live verify(`VERIFY_PENDING` /
            # `VERIFYING`) 같은 surface는 fail-safe 원칙에 따라 여전히 비우고, task hint도
            # active verify가 되살아나지 않도록 항상 초기화합니다.
            if (
                surfaced_active_round is None
                or str((surfaced_active_round or {}).get("state") or "") != "RECEIPT_PENDING"
            ):
                surfaced_active_round = None
            self._write_task_hints(
                active_lane="",
                active_round=None,
                turn_state=turn_state if isinstance(turn_state, dict) else None,
                control=control_block,
                duplicate_control=duplicate_control,
            )
        dispatch_stall_marker = self._dispatch_stall_marker(job_states, active_round=surfaced_active_round)
        self._current_dispatch_stall_marker = dispatch_stall_marker
        completion_stall_marker = self._completion_stall_marker(job_states, active_round=surfaced_active_round)
        self._current_completion_stall_marker = completion_stall_marker
        progress = self._build_progress_hint(
            active_lane=active_lane,
            active_round=surfaced_active_round,
            turn_state=turn_state if isinstance(turn_state, dict) else None,
            control=control_block,
            autonomy=autonomy,
            artifacts=artifacts,
        )
        self._annotate_lane_progress(lanes, progress)

        status = {
            "schema_version": 1,
            "backend_type": "tmux",
            "run_id": self.run_id,
            "current_run_id": self.run_id,
            "runtime_state": self.runtime_state,
            "degraded_reason": self.degraded_reason,
            "degraded_reasons": list(self.degraded_reasons),
            "control_age_cycles": control_age_cycles,
            "autonomy": autonomy,
            "control": control_block,
            "lanes": lanes,
            "active_round": surfaced_active_round,
            "turn_state": turn_state if isinstance(turn_state, dict) else None,
            "progress": progress,
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
        status.update(derive_automation_health(status))
        atomic_write_json(self.status_path, status)
        self._write_current_run_pointer()
        self._write_compat_files(status)
        return status

    def _record_status_events(self, status: dict[str, Any]) -> None:
        control = dict(status.get("control") or {})
        control_snapshot = active_control_snapshot_from_status(control)
        duplicate_control = dict(self._current_duplicate_control_marker or {})
        stale_operator_control = dict(self._current_stale_operator_control_marker or {})
        operator_gate = dict(self._current_operator_gate_marker or {})
        autonomy = dict(status.get("autonomy") or {})
        control_key = "|".join(
            [
                str(control_snapshot.get("control_file") or ""),
                str(control_snapshot.get("control_seq") or ""),
                str(control_snapshot.get("control_status") or ""),
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
                        "control_seq": control_seq_value(duplicate_control.get("control_seq"), default=-1),
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
                        "control_seq": control_seq_value(stale_operator_control.get("control_seq"), default=-1),
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
                        "control_seq": control_seq_value(operator_gate.get("control_seq"), default=-1),
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

        dispatch_stall = dict(self._current_dispatch_stall_marker or {})
        dispatch_stall_key = "|".join(
            [
                str(dispatch_stall.get("job_id") or ""),
                str(dispatch_stall.get("round") or ""),
                str(dispatch_stall.get("fingerprint") or ""),
                str(dispatch_stall.get("attempt") or ""),
                str(dispatch_stall.get("action") or ""),
            ]
        )
        if dispatch_stall_key != self._last_dispatch_stall_key:
            self._last_dispatch_stall_key = dispatch_stall_key
            if dispatch_stall:
                self._append_event("dispatch_stall_detected", dispatch_stall)

        completion_stall = dict(self._current_completion_stall_marker or {})
        completion_stall_key = "|".join(
            [
                str(completion_stall.get("job_id") or ""),
                str(completion_stall.get("round") or ""),
                str(completion_stall.get("fingerprint") or ""),
                str(completion_stall.get("attempt") or ""),
                str(completion_stall.get("action") or ""),
            ]
        )
        if completion_stall_key != self._last_completion_stall_key:
            self._last_completion_stall_key = completion_stall_key
            if completion_stall:
                self._append_event("completion_stall_detected", completion_stall)

        automation_health = str(status.get("automation_health") or "ok")
        automation_reason_code = str(status.get("automation_reason_code") or "")
        automation_incident_family = str(status.get("automation_incident_family") or "")
        automation_next_action = str(status.get("automation_next_action") or "")
        automation_key = "|".join(
            [
                automation_health,
                automation_reason_code,
                automation_incident_family,
                automation_next_action,
            ]
        )
        if automation_key != self._last_automation_incident_key:
            self._last_automation_incident_key = automation_key
            if automation_health != "ok" and (automation_reason_code or automation_incident_family):
                self._append_event(
                    "automation_incident",
                    {
                        "automation_health": automation_health,
                        "reason_code": automation_reason_code,
                        "incident_family": automation_incident_family,
                        "next_action": automation_next_action,
                        "control": dict(status.get("control") or {}),
                        "active_round": dict(status.get("active_round") or {}),
                    },
                )

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

    def _process_cmdline(self, pid: int) -> str:
        try:
            return (
                Path(f"/proc/{pid}/cmdline")
                .read_bytes()
                .replace(b"\0", b" ")
                .decode("utf-8", errors="replace")
            )
        except OSError:
            return ""

    def _process_cwd(self, pid: int) -> str:
        try:
            return str(Path(os.readlink(f"/proc/{pid}/cwd")).resolve())
        except OSError:
            return ""

    def _terminate_current_run_watcher(self) -> set[int]:
        killed: set[int] = set()
        current_run = read_json(self.current_run_path) or {}
        try:
            pid = int(current_run.get("watcher_pid") or -1)
        except (TypeError, ValueError):
            pid = -1
        if pid <= 0 or pid in {os.getpid(), os.getppid()}:
            return killed
        expected_fingerprint = str(current_run.get("watcher_fingerprint") or "").strip()
        if expected_fingerprint:
            live_fingerprint = process_starttime_fingerprint(pid)
            if live_fingerprint != expected_fingerprint:
                return killed
        elif self._process_cwd(pid) != str(self.project_root.resolve()):
            return killed
        self._kill_pid(pid)
        killed.add(pid)
        return killed

    def _terminate_repo_watchers(self) -> None:
        terminated = self._terminate_current_run_watcher()
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
            if pid in terminated or pid in {os.getpid(), os.getppid()}:
                continue
            cmd = self._process_cmdline(pid)
            cwd = self._process_cwd(pid)
            if cwd == project_abs and (
                "watcher_core.py" in cmd or "pipeline-watcher-v3" in cmd
            ):
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
        command_parts = lane_vendor_command_parts(lane_name)
        if command_parts:
            binary = self._find_cli_bin(command_parts[0])
            args = " ".join(shlex.quote(part) for part in command_parts[1:])
            if args:
                return f'exec "{binary}" {args}'
            return f'exec "{binary}"'
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
        fallback = default_role_bindings()
        return str(self.role_owners.get(role_name) or "").strip() or str(fallback.get(role_name) or "").strip()

    def _prompt_owner(self, role_name: str) -> str:
        return str(self.prompt_owners.get(role_name) or "").strip() or self._role_owner(role_name)

    def _prompt_read_first_doc(self, role_name: str) -> str:
        return read_first_doc_for_owner(self._prompt_owner(role_name))

    def _role_read_first_doc(self, role_name: str) -> str:
        return read_first_doc_for_owner(self._role_owner(role_name))

    def _prompt_templates(self) -> dict[str, str]:
        return {
            "verify": DEFAULT_VERIFY_PROMPT_TEMPLATE,
            "implement": DEFAULT_IMPLEMENT_PROMPT,
            "advisory": DEFAULT_ADVISORY_PROMPT,
            "followup": DEFAULT_FOLLOWUP_PROMPT,
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

    def _watcher_pane_target_args(self) -> list[str]:
        args: list[str] = []
        for lane in self.runtime_lane_configs or physical_lane_specs():
            lane_name = str(lane.get("name") or "").strip()
            if not lane_name:
                continue
            option = legacy_watcher_pane_target_arg_for_lane(lane)
            if not option:
                continue
            pane_id = str((self.adapter.pane_for_lane(lane_name) or {}).get("pane_id") or "")
            args.extend([option, pane_id])
        return args

    def _watcher_shell_command(self) -> str:
        templates = self._prompt_templates()
        watcher_core_path = resolve_project_runtime_file(self.project_root, "watcher_core.py")
        watcher_log = self.base_dir / "logs" / "experimental" / "watcher.log"
        py_path = str(self.project_root)
        if os.environ.get("PYTHONPATH"):
            py_path = f"{py_path}:{os.environ['PYTHONPATH']}"
        watcher_args = [
            "env",
            f"PROJECT_ROOT={self.project_root}",
            f"PIPELINE_RUNTIME_RUN_ID={self.run_id}",
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
            *self._watcher_pane_target_args(),
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
        return f"exec {shlex.join(watcher_args)} > {shlex.quote(str(watcher_log))} 2>&1"

    def _spawn_experimental_watcher(self) -> dict[str, Any]:
        watcher_info = self.adapter.spawn_watcher(
            window_name="watcher-exp",
            shell_command=self._watcher_shell_command(),
        )
        self.base_dir.joinpath("experimental.pid").write_text(
            str(watcher_info.get("pid") or ""),
            encoding="utf-8",
        )
        return watcher_info

    def _maybe_restart_watcher_for_source_change(self) -> bool:
        if self._stop_requested or not self._runtime_started:
            return False
        marker = self._watcher_source_restart_marker()
        if marker is None:
            return False
        restart_key = str(marker.get("restart_key") or "")
        self._last_watcher_source_restart_key = restart_key
        self._last_watcher_source_restart_at = time.time()
        payload = {key: value for key, value in marker.items() if key != "restart_key"}
        self._append_event("watcher_self_restart_started", payload)
        try:
            self._terminate_pid_file(self.base_dir / "experimental.pid")
            watcher_info = self._spawn_experimental_watcher()
        except Exception as exc:
            self._append_event(
                "watcher_self_restart_failed",
                {
                    **payload,
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )
            return False
        self._write_current_run_pointer()
        self._append_event(
            "watcher_self_restart_completed",
            {
                **payload,
                "new_pid": int(watcher_info.get("pid") or 0),
                "result": "restarted",
            },
        )
        return True

    def _spawn_runtime_session(self) -> None:
        self.adapter.create_scaffold()

        lane_configs = self.runtime_lane_configs or build_lane_configs(
            enabled_lanes=self.enabled_lanes,
            role_owners=self.role_owners,
        )
        for lane_cfg in lane_configs:
            lane_name = str(lane_cfg.get("name") or "").strip()
            if not lane_name:
                continue
            enabled = bool(lane_cfg.get("enabled", lane_name in self.enabled_lanes))
            command = self._lane_shell_command(lane_name) if enabled else self._disabled_lane_command(lane_name)
            if not self.adapter.spawn_lane(lane_name, command):
                raise RuntimeError(f"lane spawn failed: {lane_name}")

        self._spawn_experimental_watcher()

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
        self._write_current_run_pointer()

    def _launch_runtime(self) -> None:
        self.adapter.kill_session()
        self._terminate_pid_file(self.base_dir / "baseline.pid")
        self._terminate_pid_file(self.base_dir / "experimental.pid")
        self._stop_token_collector()
        self._terminate_repo_watchers()
        self._prepare_runtime_surfaces()
        self._clear_runtime_sidecars()
        self._spawn_runtime_session()

    def _recover_missing_session(self) -> bool:
        if self._stop_requested or not self._runtime_started:
            return False
        retries = self._session_recovery_attempts
        retry_limit = _SESSION_RECOVERY_RETRY_LIMIT
        if retries >= retry_limit:
            self._record_session_recovery_exhausted(retry_limit=retry_limit)
            return False
        attempt = retries + 1
        self._session_recovery_attempts = attempt
        self._session_recovery_last_started_at = time.time()
        self._append_event("session_recovery_started", {"attempt": attempt, "retry_limit": retry_limit})
        try:
            self.adapter.kill_session()
            self._terminate_pid_file(self.base_dir / "baseline.pid")
            self._terminate_pid_file(self.base_dir / "experimental.pid")
            self._stop_token_collector()
            self._terminate_repo_watchers()
            self._clear_runtime_sidecars()
            self._spawn_runtime_session()
        except Exception as exc:
            self._append_event(
                "session_recovery_failed",
                {
                    "attempt": attempt,
                    "retry_limit": retry_limit,
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )
            return False
        self._append_event("session_recovery_completed", {"attempt": attempt, "result": "recreated"})
        return True

    def _record_session_recovery_exhausted(self, *, retry_limit: int = _SESSION_RECOVERY_RETRY_LIMIT) -> None:
        attempts = self._session_recovery_attempts
        key = f"{attempts}|{retry_limit}"
        if key == self._last_session_recovery_exhausted_key:
            return
        self._last_session_recovery_exhausted_key = key
        self._append_event(
            "session_recovery_exhausted",
            {
                "attempts": attempts,
                "retry_limit": retry_limit,
                "reset_after_stable_sec": _SESSION_RECOVERY_RESET_STABLE_SEC,
            },
        )

    def _maybe_reset_session_recovery_budget(self, session_alive: bool) -> None:
        if not session_alive or self._session_recovery_attempts <= 0:
            return
        if self._session_recovery_last_started_at <= 0:
            return
        stable_sec = time.time() - self._session_recovery_last_started_at
        if stable_sec < _SESSION_RECOVERY_RESET_STABLE_SEC:
            return
        self._session_recovery_attempts = 0
        self._session_recovery_last_started_at = 0.0
        self._last_session_recovery_exhausted_key = ""
        self._append_event(
            "session_recovery_budget_reset",
            {
                "stable_sec": round(stable_sec, 3),
                "reset_after_stable_sec": _SESSION_RECOVERY_RESET_STABLE_SEC,
            },
        )

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
                self._maybe_restart_watcher_for_source_change()
                status = self._write_status()
                self._record_status_events(status)
                if self._stop_requested:
                    break
                time.sleep(self.poll_interval)
        finally:
            # 정상 종료(SIGTERM/SIGINT)에서는 여기까지 도달하므로 supervisor.pid를 unlink한다.
            # SIGKILL 같은 비정상 종료에서는 finally가 실행되지 않으므로 stale pid cleanup은
            # watcher의 owner-death 판정 경계가 맡고, 이 경로에 추가 책임을 기대하지 않는다.
            self.runtime_state = "STOPPING"
            self._write_status()
            if self._runtime_started:
                self._stop_runtime()
            self._runtime_started = False
            self._stop_requested = False
            self.runtime_state = "STOPPED"
            self._force_stopped_surface = True
            try:
                final_status = self._write_status()
            finally:
                self._force_stopped_surface = False
            self._record_status_events(final_status)
            self._append_event("runtime_stopped", {"runtime_state": "STOPPED"})
            try:
                self.pid_path.unlink()
            except FileNotFoundError:
                pass
        return 0
