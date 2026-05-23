#!/usr/bin/env python3
"""
watcher_core.py  –  Pipeline Watcher v2.0

변경 내역 (v1.1 → v2.0) — 2단계
  1. VERIFY_DONE 상태 추가
  2. ManifestCollector : manifest 파일 폴링 + jsonschema 검증 (optional)
  3. 4중 일치 확인 : job_id / round / role / artifact_hash
  4. JobState 확장 : verify_manifest_path / verify_completed_at /
                     validation_score / blocker_count / verify_result
  5. VERIFY_RUNNING → VERIFY_DONE 전이
  6. 로그 디렉터리 분리 : experimental/ (baseline은 .pipeline/logs/baseline/ 유지)
  7. A/B 비율 계산식 고정 : suppressed/raw, dispatch/raw

1단계 범위 (유지)
  NEW_ARTIFACT → STABILIZING → VERIFY_PENDING → VERIFY_RUNNING

2단계 추가
  VERIFY_RUNNING → VERIFY_DONE

미포함 (3단계 이후)
  trust score 합성, COUNTER_PENDING, RETRY_PENDING, FINALIZED, ISOLATED
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

_PROJECT_IMPORT_ROOT = os.environ.get("PROJECT_ROOT") or os.getcwd()
if _PROJECT_IMPORT_ROOT:
    project_import_path = str(Path(_PROJECT_IMPORT_ROOT).resolve())
    if project_import_path not in sys.path:
        sys.path.insert(0, project_import_path)

import watcher_dispatch
from pipeline_gui.project import _session_name_for as _session_name_for_project
from pipeline_gui.setup_profile import resolve_project_runtime_adapter
from pipeline_runtime.automation_health import (
    STALE_ADVISORY_GRACE_CYCLES,
    STALE_CONTROL_CYCLE_THRESHOLD,
    advance_control_seq_age,
)
from pipeline_runtime.lane_surface import (
    _line_looks_like_input_prompt,
    _pane_text_has_gemini_ready_prompt,
    capture_pane_text as _shared_capture_pane_text,
    pane_text_busy_age_seconds as _shared_pane_text_busy_age_seconds,
    pane_text_has_busy_indicator as _shared_pane_text_has_busy_indicator,
    pane_text_has_codex_activity as _shared_pane_text_has_codex_activity,
    pane_text_has_gemini_activity as _shared_pane_text_has_gemini_activity,
    pane_text_has_input_cursor as _shared_pane_text_has_input_cursor,
    pane_text_is_idle as _shared_pane_text_is_idle,
)
from pipeline_runtime.lane_catalog import (
    default_role_bindings,
    legacy_watcher_pane_target_arg_for_lane,
    physical_lane_specs,
    read_first_doc_for_owner,
)
from pipeline_runtime.operator_autonomy import (
    OPERATOR_APPROVAL_COMPLETED_REASON,
    is_commit_push_approval_stop,
    load_runtime_policy,
    normalize_reason_code,
    resolve_operator_control,
)
from pipeline_runtime.pr_merge_state import PrMergeStatusCache
from pipeline_runtime.role_routes import (
    VERIFY_FOLLOWUP_ROUTE,
    VERIFY_TRIAGE_ESCALATION,
    VERIFY_TRIAGE_ONLY_REASON,
    is_verify_followup_route,
    is_verify_triage_escalation,
    normalize_verify_triage_escalation,
)
from pipeline_runtime.schema import (
    active_control_snapshot_from_status,
    atomic_write_json,
    atomic_write_text,
    completed_implement_handoff_truth,
    control_seq_value,
    control_slot_spec,
    iter_job_state_paths,
    iter_control_slot_specs,
    read_control_meta,
    read_json,
    snapshot_control_seq,
)
from pipeline_runtime.turn_arbitration import (
    TURN_VERIFY_FOLLOWUP,
    WatcherTurnInputs,
    legacy_turn_state_name,
    legacy_watcher_turn_name,
    resolve_watcher_turn,
)
from pipeline_runtime.wrapper_events import build_lane_read_models
from verify_fsm import (
    StateMachine,
    compute_file_sig,
    make_job_id,
)
from watcher_state import (
    _JSONSCHEMA_AVAILABLE,
    ControlSignal,
    DedupeGuard,
    JobState,
    JobStatus,
    LeaseData,
    ManifestCollector,
    PaneLease,
    TERMINAL_STATES,
    WatcherTurnState,
)
from watcher_stabilizer import (
    ArtifactStabilizer,
    StabilizeSnapshot,
    compute_file_sha256,
)
from watcher_artifact_scanner import ArtifactScanner
from watcher_control_signals import (
    ControlSignalReader,
    control_signal_for_slot,
    control_signal_matches,
    newest_control_signal,
)
from watcher_job_state import JobStateManager
from watcher_lane_status import build_lane_statuses
from watcher_prompt_assembly import (
    DEFAULT_ADVISORY_PROMPT,
    DEFAULT_ADVISORY_RECOVERY_PROMPT,
    DEFAULT_CONTROL_RECOVERY_PROMPT,
    DEFAULT_FOLLOWUP_PROMPT,
    DEFAULT_IMPLEMENT_PROMPT,
    DEFAULT_OPERATOR_RETRIAGE_PROMPT,
    DEFAULT_VERIFY_PROMPT_TEMPLATE,
    DEFAULT_VERIFY_TRIAGE_PROMPT,
    PromptDispatchSpec,
    WatcherPromptAssembler,
    _cleanup_prompt_files,
    _normalize_prompt_text,
    _prompt_cleanup_list,
    _write_prompt_file,
)
from watcher_runtime_exporter import WatcherRuntimeExporter
from watcher_recovery import OperatorRetrageTracker, StaleAdvisoryRecovery
from watcher_pty_adapter import PtyLaneBridge
from watcher_status_writer import write_runtime_status

_ROLLING_PIPELINE_PATHS = frozenset(
    {
        ".pipeline/implement_handoff.md",
        ".pipeline/advisory_request.md",
        ".pipeline/advisory_advice.md",
        ".pipeline/operator_request.md",
        ".pipeline/session_arbitration_draft.md",
        ".pipeline/codex_feedback.md",
        ".pipeline/gpt_prompt.md",
        ".pipeline/current_run.json",
    }
)
_ROLLING_PIPELINE_PREFIXES = (
    ".pipeline/runs/",
    ".pipeline/state/",
    ".pipeline/logs/",
    ".pipeline/receipts/",
    ".pipeline/wrapper-events/",
)
def _default_pane_target_for_lane(session: str, lane: dict[str, object]) -> str:
    raw_index = lane.get("pane_index")
    try:
        pane_index = int(raw_index)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        pane_index = 0
    return f"{session}:0.{pane_index}"


def _default_runtime_lane_configs() -> list[dict[str, object]]:
    return [{**spec, "enabled": True} for spec in physical_lane_specs()]


def _legacy_pane_target_config_key(lane: dict[str, object]) -> str:
    option = legacy_watcher_pane_target_arg_for_lane(lane)
    return option[2:].replace("-", "_") if option.startswith("--") else ""


def _default_dispatch_pane_type() -> str:
    specs = physical_lane_specs()
    return str((specs[0] if specs else {}).get("pane_type") or "claude")


def _config_bool(value: object, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if not text:
        return default
    return text not in {"0", "false", "no", "off"}


def _pane_text_looks_like_advisory_dispatch(text: str) -> bool:
    normalized = str(text or "").lower()
    if not normalized.strip():
        return False
    return (
        ("role: advisory" in normalized and "request: @.pipeline/advisory_request.md" in normalized)
        or "role_harness: .pipeline/harness/advisory.md" in normalized
    )


def _extract_visible_advisory_next_control_seq(text: str) -> int:
    match = re.search(r"(?im)^\s*next_control_seq:\s*(\d+)\s*$", str(text or ""))
    if match is None:
        return -1
    try:
        return int(match.group(1))
    except ValueError:
        return -1


# ---------------------------------------------------------------------------
# 로깅
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("watcher_core")
DEFAULT_ADVISORY_RECOVERY_SEC = 300.0
DEFAULT_VERIFY_DONE_DEADLINE_SEC = 900.0

__all__ = ["WatcherCore", "main"]

SCHEMA_VERSION = 1
_MATCHING_VERIFY_PENDING_ARCHIVE_REASON = "matching_verify_already_exists"


def _pane_has_input_cursor(pane_target: str) -> bool:
    """Check if the pane shows an input prompt in the recent visible lines."""
    text = _shared_capture_pane_text(pane_target)
    return _shared_pane_text_has_input_cursor(text)


from watcher_signals import (
    _LIVE_SESSION_ESCALATION_PATTERNS,
    _LIVE_SESSION_ESCALATION_FALLBACK_KEYWORDS,
    _IMPLEMENT_BLOCKED_STATUS_RE,
    _IMPLEMENT_BLOCKED_FIELD_RE,
    _IMPLEMENT_BLOCKED_WRAP_KEYS,
    _IMPLEMENT_BLOCKED_TEMPLATE_MARKERS,
    _IMPLEMENT_ALREADY_DONE_PATTERNS,
    _IMPLEMENT_NO_CHANGE_PATTERNS,
    _IMPLEMENT_FORBIDDEN_MENU_PATTERNS,
    _HANDOFF_MARKDOWN_BULLET_LITERAL_RE,
    _MATERIALIZED_BLOCK_REASON_CODES,
    _MATERIALIZED_BLOCK_REASONS,
    _HandoffSentenceReplacementTarget,
    _normalize_escalation_line,
    _match_implement_blocked_status,
    _can_append_implement_blocked_wrap,
    _decode_handoff_markdown_literal,
    _parse_handoff_sentence_replacement_target,
    _fallback_escalation_reasons,
    _extract_live_session_escalation,
    _normalize_control_path_hint,
    _extract_implement_blocked_signal,
    _extract_implement_forbidden_menu_signal,
    _extract_implement_completed_handoff_signal,
)


# ---------------------------------------------------------------------------
# WatcherCore – 메인 폴링 루프
# ---------------------------------------------------------------------------
class WatcherCore:
    """
    메인 폴링 루프 v2.1
    변경: 시작 시 턴(turn) 판단 + rolling control 감시로 active owner lane에 신호 전달.
    로그는 .pipeline/logs/experimental/ 에 저장 (baseline은 .pipeline/logs/baseline/).
    """

    def __init__(self, config: dict) -> None:
        base = Path(config.get("base_dir", ".pipeline"))

        self.base_dir      = base
        self.pipeline_dir  = base
        self.watch_dir     = Path(config["watch_dir"])
        self.artifact_root = self.watch_dir.parent
        self.repo_root     = Path(config.get("repo_root", str(self.artifact_root))).resolve()
        self.verify_dir    = self.artifact_root / "verify"
        self.advisory_report_dir = self.artifact_root / "report" / "gemini"
        self.state_dir     = base / "state"
        self.state_archive_dir = base / "state-archive"
        self.lock_dir      = base / "locks"
        self.manifests_dir = base / "manifests"

        # 로그 디렉터리 분리: experimental vs baseline
        self.events_dir = base / "logs" / "experimental"
        self.events_dir.mkdir(parents=True, exist_ok=True)

        self.poll_interval = config.get("poll_interval", 1.0)
        self.dry_run       = config.get("dry_run", False)
        self.gemini_git_permission_auto_allow = _config_bool(
            config.get("gemini_git_permission_auto_allow"),
            default=True,
        )
        self.startup_grace_sec = float(config.get("startup_grace_sec", 8.0))
        self.state_cleanup_legacy_grace_sec = float(
            config.get("state_cleanup_legacy_grace_sec", 300.0)
        )
        self.session_arbitration_settle_sec = float(config.get("session_arbitration_settle_sec", 5.0))
        self.session_arbitration_cooldown_sec = float(config.get("session_arbitration_cooldown_sec", 300.0))
        self.implement_blocked_settle_sec = float(config.get("implement_blocked_settle_sec", 5.0))
        self.implement_blocked_cooldown_sec = float(config.get("implement_blocked_cooldown_sec", 300.0))
        self.started_at = time.time()
        self.runtime_adapter = resolve_project_runtime_adapter(self.repo_root)
        self.runtime_policy = load_runtime_policy(self.repo_root)
        self.runtime_controls = dict(self.runtime_adapter.get("controls") or {})
        self.runtime_role_owners = dict(self.runtime_adapter.get("role_owners") or {})
        self.runtime_prompt_owners = dict(self.runtime_adapter.get("prompt_owners") or self.runtime_role_owners)
        self.runtime_lane_configs = list(self.runtime_adapter.get("lane_configs") or [])
        self._pr_merge_status_cache = PrMergeStatusCache()

        # rolling control slots (role-based canonical filenames; historical names are read-only aliases)
        implement_spec = control_slot_spec("implement_handoff")
        advisory_request_spec = control_slot_spec("advisory_request")
        advisory_advice_spec = control_slot_spec("advisory_advice")
        operator_spec = control_slot_spec("operator_request")
        self.implement_handoff_path    = base / (implement_spec.canonical_filename if implement_spec else "implement_handoff.md")
        self.advisory_request_path    = base / (advisory_request_spec.canonical_filename if advisory_request_spec else "advisory_request.md")
        self.advisory_advice_path     = base / (advisory_advice_spec.canonical_filename if advisory_advice_spec else "advisory_advice.md")
        self.operator_request_path  = base / (operator_spec.canonical_filename if operator_spec else "operator_request.md")
        self.session_arbitration_draft_path = base / "session_arbitration_draft.md"  # watcher-generated non-canonical draft
        self.completion_paths       = [
            self.implement_handoff_path,
            self.advisory_request_path,
            self.operator_request_path,
        ]
        # pane target: 명시 인자 우선, 없으면 active physical lane catalog 기반 default
        repo_root_str = str(self.repo_root)
        _sess = _session_name_for_project(repo_root_str)
        _lane_configs_for_targets = self.runtime_lane_configs or _default_runtime_lane_configs()
        self.agent_pane_targets: dict[str, str] = {}
        for lane in _lane_configs_for_targets:
            lane_name = str(lane.get("name") or "").strip()
            if not lane_name:
                continue
            config_key = _legacy_pane_target_config_key(lane)
            explicit_target = str(config.get(config_key) or "").strip() if config_key else ""
            self.agent_pane_targets[lane_name] = explicit_target or _default_pane_target_for_lane(_sess, lane)
        self.claude_pane_target  = self.agent_pane_targets.get("Claude", "")
        self.gemini_pane_target  = self.agent_pane_targets.get("Gemini", "")
        self.codex_pane_target   = self.agent_pane_targets.get("Codex", "")
        self._pty_bridge = PtyLaneBridge()
        self._pty_pilot_lane = self._normalize_pty_pilot_lane(self.runtime_policy.get("pty_pilot_lane"))
        self._pty_pilot_register_result: dict[str, object] | None = None
        self._setup_pty_pilot_bridge()
        self.implement_prompt = _normalize_prompt_text(
            config.get("implement_prompt")
            or config.get("claude_prompt")
            or DEFAULT_IMPLEMENT_PROMPT
        )
        self.advisory_prompt = _normalize_prompt_text(
            config.get("advisory_prompt")
            or config.get("gemini_prompt")
            or DEFAULT_ADVISORY_PROMPT
        )
        self.followup_prompt = _normalize_prompt_text(
            config.get("followup_prompt")
            or config.get("codex_followup_prompt")
            or DEFAULT_FOLLOWUP_PROMPT
        )
        self.advisory_recovery_prompt = _normalize_prompt_text(
            config.get("advisory_recovery_prompt")
            or DEFAULT_ADVISORY_RECOVERY_PROMPT
        )
        self.control_recovery_prompt = _normalize_prompt_text(
            config.get("control_recovery_prompt")
            or DEFAULT_CONTROL_RECOVERY_PROMPT
        )
        self.operator_retriage_prompt = _normalize_prompt_text(
            config.get("operator_retriage_prompt")
            or DEFAULT_OPERATOR_RETRIAGE_PROMPT
        )
        self.verify_triage_prompt = _normalize_prompt_text(
            config.get("verify_blocked_triage_prompt")
            or config.get("verify_triage_prompt")
            or config.get("codex_blocked_triage_prompt")
            or DEFAULT_VERIFY_TRIAGE_PROMPT
        )

        # rolling 슬롯 시그니처 추적 (mtime_ns + size + hash)
        self._last_implement_handoff_sig: str = self._get_path_sig(self.implement_handoff_path)
        self._last_advisory_request_sig: str = self._get_path_sig(self.advisory_request_path)
        self._last_advisory_advice_sig: str = self._get_path_sig(self.advisory_advice_path)
        self._last_operator_request_sig: str = self._get_path_sig(self.operator_request_path)
        self._csreader = ControlSignalReader(
            pipeline_dir=self.pipeline_dir,
            advisory_enabled=self._advisory_enabled(),
            operator_stop_enabled=self._operator_stop_enabled(),
            path_sig_fn=self._get_path_sig,
        )
        self._scanner = ArtifactScanner(
            watch_dir=self.watch_dir,
            verify_dir=self.verify_dir,
            repo_root=self.repo_root,
            completion_paths=tuple(self.completion_paths),
        )
        self._last_seen_control_seq: int | None = None
        self._control_seq_age_cycles: int = 0
        self._last_session_arbitration_draft_sig: str = self._get_path_sig(self.session_arbitration_draft_path)
        self._last_session_arbitration_fingerprint: str = ""
        self._session_arbitration_snapshot_fingerprints: dict[str, str] = {}
        self._session_arbitration_snapshot_changed_at: dict[str, float] = {}
        self._session_arbitration_cooldowns: dict[str, float] = {}
        self._last_implement_blocked_fingerprint: str = ""
        self._implement_blocked_snapshot_fingerprints: dict[str, str] = {}
        self._implement_blocked_snapshot_changed_at: dict[str, float] = {}
        self._implement_blocked_cooldowns: dict[str, float] = {}
        # 시작 시 이미 implement 차례인지 판단하는 플래그
        self._initial_turn_checked: bool = False
        # implement 차례일 때: 시작 시점 work/ 스냅샷
        # 이후 스냅샷이 달라질 때만 새 작업으로 인정
        self._work_baseline_snapshot: dict[str, str] = {}
        # Turn state (single source of truth for dispatch)
        self._current_turn_state: WatcherTurnState = WatcherTurnState.IDLE
        self._turn_entered_at: float = 0.0
        self._turn_active_control_file: str = ""
        self._turn_active_control_seq: int = -1
        self._turn_state_path: Path = self.state_dir / "turn_state.json"
        self._lane_input_defer_cooldown_sec: float = float(
            config.get("lane_input_defer_cooldown_sec", 5.0)
        )
        self.advisory_retry_sec: float = float(
            config.get("advisory_idle_retry_sec", config.get("advisory_retry_sec", 30.0))
        )
        self.advisory_recovery_sec: float = float(
            config.get("advisory_recovery_sec", DEFAULT_ADVISORY_RECOVERY_SEC)
        )
        self.inactive_advisory_cancel_sec: float = float(
            config.get("inactive_advisory_cancel_sec", 60.0)
        )
        self.operator_retriage_no_control_sec: float = float(
            config.get("operator_retriage_no_control_sec", 45.0)
        )
        self._inactive_advisory_busy_key: str = ""
        self._inactive_advisory_busy_since: float = 0.0
        self._last_inactive_advisory_cancel_key: str = ""
        self._last_inactive_advisory_cancel_at: float = 0.0
        self._runtime_export_enabled: bool = os.environ.get("PIPELINE_RUNTIME_DISABLE_EXPORTER", "").strip().lower() not in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.run_id: str = self._resolve_run_id()
        self.run_dir: Path = self.base_dir / "runs" / self.run_id
        self.run_status_path: Path = self.run_dir / "status.json"
        self.run_events_path: Path = self.run_dir / "events.jsonl"
        self.current_run_path: Path = self.base_dir / "current_run.json"
        self._exporter = WatcherRuntimeExporter(
            enabled=self._runtime_export_enabled,
            run_id=self.run_id,
            run_dir=self.run_dir,
            run_status_path=self.run_status_path,
            run_events_path=self.run_events_path,
            current_run_path=self.current_run_path,
            repo_root=self.repo_root,
        )
        self._jsm = JobStateManager(
            state_dir=self.state_dir,
            run_id=self.run_id,
            archive_dir_fn=self._job_state_archive_dir,
            started_at=self.started_at,
            state_cleanup_legacy_grace_sec=self.state_cleanup_legacy_grace_sec,
        )
        if self._runtime_export_enabled:
            self.run_dir.mkdir(parents=True, exist_ok=True)
        self._archive_stale_job_states()

        # Implement-owner idle timeout tracking. The legacy key remains a read-only
        # config alias so existing local profiles do not lose their timeout.
        self.implement_active_idle_timeout_sec: float = float(
            config.get(
                "implement_active_idle_timeout_sec",
                config.get("claude_active_idle_timeout_sec", 300),
            )
        )
        self.operator_wait_retriage_sec: float = float(
            config.get("operator_wait_retriage_sec", 3600)
        )
        self._last_progress_at: float = 0.0
        self._last_active_pane_fingerprint: str = ""
        self._last_idle_release_handoff_sig: str = ""
        self._last_idle_release_at: float = 0.0
        self._pending_idle_release_handoff: dict[str, object] | None = None

        self.stabilizer = ArtifactStabilizer(
            settle_sec=config.get("settle_sec", 3.0),
            required_stable=config.get("required_stable", 2),
        )
        # owner_pid_path는 watcher init 시점의 `supervisor.pid` 존재 여부와 무관하게 항상
        # 동일 경로를 가리킨다. supervisor가 나중에 뜨고/정리되는 전환은 `PaneLease._owner_dead`
        # 가 매 check마다 파일을 다시 읽어 판단한다. 이렇게 두지 않으면 watcher가 supervisor
        # 보다 먼저 뜨는 start-up race에서 owner_pid_path가 None으로 영구 고정되어,
        # supervisor가 비정상 종료해도 stale lease가 TTL 만기 전까지 해제되지 않는다.
        self.lease  = PaneLease(
            self.lock_dir,
            default_ttl=config.get("lease_ttl", 900),
            dry_run=self.dry_run,
            owner_pid_path=self.base_dir / "supervisor.pid",
        )
        self.dedupe = DedupeGuard(self.events_dir)

        schema_path = Path(config.get(
            "manifest_schema_path",
            str(Path(__file__).parent / "schemas" / "agent_manifest.schema.json"),
        ))
        self.collector = ManifestCollector(self.manifests_dir, schema_path)
        self.dispatch_queue = watcher_dispatch.WatcherDispatchQueue(
            lane_input_defer_cooldown_sec=self._lane_input_defer_cooldown_sec,
            capture_pane_text=lambda target: self._capture_pane_text(target),
            send_keys=lambda target, prompt, pane_type: self._send_prompt_to_pane(target, prompt, pane_type),
            get_path_sig=self._get_path_sig,
            role_owner=self._prompt_owner,
            log_raw=self._log_raw,
            append_runtime_event=self._append_runtime_event,
            get_active_control_signal=self._get_active_control_signal,
            is_active_control=self._is_active_control,
        )
        self._operator_retriage_tracker = OperatorRetrageTracker(
            operator_request_path=self.operator_request_path,
            current_turn_state=lambda: self._current_turn_state,
            turn_active_control_seq=lambda: self._turn_active_control_seq,
            operator_wait_retriage_sec=lambda: self.operator_wait_retriage_sec,
            is_active_control=lambda path, status: self._is_active_control(path, status),
            get_path_mtime=lambda path: self._get_path_mtime(path),
            read_control_seq_from_path=lambda path: self._read_control_seq_from_path(path),
            get_active_control=lambda: self._get_active_control_signal(),
            control_signal_for_slot=lambda active, slot, status: self._control_signal_for_slot(active, slot, status),
            satisfied_operator_approval_marker=lambda: self._satisfied_operator_approval_marker(),
            stale_operator_control_marker=lambda: self._stale_operator_control_marker(),
            get_path_sig=lambda path: self._get_path_sig(path),
            read_status_from_path=lambda path: self._read_status_from_path(path),
            clear_implement_blocked=lambda reason: self._clear_implement_blocked_state(reason),
            transition_turn=lambda *args, **kwargs: self._transition_turn(*args, **kwargs),
            record_operator_recovery_marker=lambda **kwargs: self._record_operator_recovery_marker(**kwargs),
            notify_verify_operator_retriage=lambda reason, marker: self._notify_verify_operator_retriage(reason, marker),
            notify_verify_control_recovery=lambda reason, marker: self._notify_verify_control_recovery(reason, marker),
            set_last_operator_request_sig=lambda sig: setattr(self, "_last_operator_request_sig", sig),
            now_fn=lambda: time.time(),
        )
        self._stale_advisory_recovery = StaleAdvisoryRecovery(
            advisory_request_path=self.advisory_request_path,
            run_events_path=self.run_events_path,
            current_turn_state=lambda: self._current_turn_state,
            turn_entered_at=lambda: self._turn_entered_at,
            turn_active_control_seq=lambda: self._turn_active_control_seq,
            advisory_retry_sec=lambda: self.advisory_retry_sec,
            advisory_recovery_sec=lambda: self.advisory_recovery_sec,
            dry_run=lambda: self.dry_run,
            advisory_enabled=lambda: self._advisory_enabled(),
            get_pending_operator_mtime=lambda: self._get_pending_operator_mtime(),
            get_active_control=lambda: self._get_active_control_signal(),
            control_signal_for_slot=lambda active, slot, status: self._control_signal_for_slot(active, slot, status),
            advisory_advice_is_current_for_request=lambda seq: self._advisory_advice_is_current_for_request(seq),
            prompt_owner=lambda role: self._prompt_owner(role),
            prompt_pane_target=lambda role: self._prompt_pane_target(role),
            lane_prompt_readiness=lambda target: self.dispatch_queue.lane_prompt_readiness(target),
            pending_notifications=lambda: list(self.dispatch_queue.pending_notifications.values()),
            log_raw=lambda event, path, job_id, extra: self._log_raw(event, path, job_id, extra),
            emit_event=lambda event, payload: self._append_runtime_event(event, payload),
            notify_advisory_owner=lambda reason: self._notify_advisory_owner(reason),
            notify_verify_advisory_recovery=lambda reason, marker: self._notify_verify_advisory_recovery(reason, marker),
            cancel_advisory_lane_if_busy=lambda **kwargs: self._cancel_advisory_lane_if_busy(**kwargs),
            clear_implement_blocked=lambda reason: self._clear_implement_blocked_state(reason),
            transition_turn=lambda *args, **kwargs: self._transition_turn(*args, **kwargs),
            read_control_seq_from_path=lambda path: self._read_control_seq_from_path(path),
            read_status_from_path=lambda path: self._read_status_from_path(path),
            get_path_sig=lambda path: self._get_path_sig(path),
            set_last_advisory_request_sig=lambda sig: setattr(self, "_last_advisory_request_sig", sig),
            capture_pane_text=lambda target: self._capture_pane_text(target),
            pane_text_has_busy_indicator=lambda text, lane: _shared_pane_text_has_busy_indicator(text, lane),
            pane_text_busy_age_seconds=lambda text, lane: _shared_pane_text_busy_age_seconds(text, lane),
            now_fn=lambda: time.time(),
        )
        self.prompt_assembler = WatcherPromptAssembler(
            advisory_report_dir=self.advisory_report_dir,
            implement_handoff_path=self.implement_handoff_path,
            advisory_request_path=self.advisory_request_path,
            advisory_advice_path=self.advisory_advice_path,
            operator_request_path=self.operator_request_path,
            runtime_enabled_lanes=list(self.runtime_adapter.get("enabled_lanes") or []),
            runtime_controls=self.runtime_controls,
            implement_prompt=self.implement_prompt,
            advisory_prompt=self.advisory_prompt,
            followup_prompt=self.followup_prompt,
            advisory_recovery_prompt=self.advisory_recovery_prompt,
            control_recovery_prompt=self.control_recovery_prompt,
            operator_retriage_prompt=self.operator_retriage_prompt,
            verify_triage_prompt=self.verify_triage_prompt,
            normalize_prompt_text=lambda text: _normalize_prompt_text(text),
            get_latest_work_path=self._get_latest_work_path,
            get_latest_same_day_verify_path_for_work=self._get_latest_same_day_verify_path_for_work,
            get_latest_same_day_verify_path=self._get_latest_same_day_verify_path,
            infer_advisory_report_hint=self._infer_advisory_report_hint,
            get_active_control_signal=self._get_active_control_signal,
            get_next_control_seq=self._get_next_control_seq,
            read_control_seq_from_path=self._read_control_seq_from_path,
            role_owner=self._prompt_owner,
            role_read_first_doc=self._prompt_read_first_doc,
            path_mention=self._path_mention,
            repo_relative=self._repo_relative,
            get_path_sha256=self._get_path_sha256,
            extract_changed_file_paths_from_round_note=self._extract_changed_file_paths_from_round_note,
            runtime_status_summary=self._runtime_prompt_status_summary,
        )

        self.sm = StateMachine(
            project_root=self.repo_root,
            verify_lane_name=self._prompt_owner("verify") or "",
            state_dir=self.state_dir,
            stabilizer=self.stabilizer,
            lease=self.lease,
            dedupe=self.dedupe,
            collector=self.collector,
            verify_pane_target=self._prompt_pane_target("verify"),
            verify_pane_type=self._prompt_pane_type("verify"),
            verify_prompt_template=config.get(
                "verify_prompt_template",
                DEFAULT_VERIFY_PROMPT_TEMPLATE,
            ),
            verify_context_builder=lambda job: self.prompt_assembler.build_verify_prompt_context(job.artifact_path),
            feedback_sig_builder=self._build_verify_feedback_sigs,
            verify_receipt_builder=self._build_verify_receipt_state,
            verify_retry_backoff_sec=float(config.get("verify_retry_backoff_sec", 20.0)),
            verify_incomplete_idle_retry_sec=float(
                config.get("verify_incomplete_idle_retry_sec", 25.0)
            ),
            verify_accept_deadline_sec=float(
                config.get("verify_accept_deadline_sec", 30.0)
            ),
            verify_done_deadline_sec=float(
                config.get("verify_done_deadline_sec", DEFAULT_VERIFY_DONE_DEADLINE_SEC)
            ),
            runtime_started_at=self.started_at,
            restart_recovery_grace_sec=float(config.get("restart_recovery_grace_sec", 15.0)),
            completion_paths=self.completion_paths,
            error_log=self.events_dir / "errors.jsonl",
            capture_pane_text=lambda target: self._capture_pane_text(target),
            pane_text_has_busy_indicator=lambda text: _shared_pane_text_has_busy_indicator(text),
            pane_text_has_input_cursor=lambda text: _shared_pane_text_has_input_cursor(text),
            pane_text_is_idle=lambda text: _shared_pane_text_is_idle(text),
            normalize_prompt_text=self.prompt_assembler.finalize_prompt_text,
            send_keys=self._send_verify_prompt_to_lane,
            verify_task_hint_writer=self._write_verify_task_hint,
            clear_failed_dispatch_input=lambda target, reason: watcher_dispatch.clear_codex_failed_dispatch_input(
                target,
                reason,
            ),
            dry_run=self.dry_run,
            pipeline_dir=self.pipeline_dir,
        )
        if self._runtime_export_enabled:
            self._write_current_run_pointer()
            self._append_runtime_event(
                "runtime_started",
                {
                    "runtime_state": "RUNNING",
                    "turn_state": self._current_turn_state.value,
                },
            )
            now_iso = self._iso_utc(time.time())
            write_runtime_status(
                enabled=True,
                run_status_path=self.run_status_path,
                run_id=self.run_id,
                turn_state=self._current_turn_state.value,
                legacy_turn_state=legacy_turn_state_name(self._current_turn_state.value),
                runtime_controls=self.runtime_controls,
                active_control=self._get_active_control_signal(),
                fallback_active_control_file=self._turn_active_control_file,
                fallback_active_control_seq=self._turn_active_control_seq,
                control_seq_age_cycles=self._control_seq_age_cycles,
                lane_statuses=self._build_lane_statuses(now_iso),
                heartbeat_iso=now_iso,
                write_current_run_pointer=self._write_current_run_pointer,
            )

    @property
    def _last_operator_retriage_sig(self) -> str:
        return self._operator_retriage_tracker.last_retriage_sig

    @_last_operator_retriage_sig.setter
    def _last_operator_retriage_sig(self, value: str) -> None:
        self._operator_retriage_tracker.last_retriage_sig = value

    @property
    def _last_operator_retriage_fingerprint(self) -> str:
        return self._operator_retriage_tracker.last_retriage_fingerprint

    @_last_operator_retriage_fingerprint.setter
    def _last_operator_retriage_fingerprint(self, value: str) -> None:
        self._operator_retriage_tracker.last_retriage_fingerprint = value

    @property
    def _operator_retriage_started_at(self) -> float:
        return self._operator_retriage_tracker.retriage_started_at

    @_operator_retriage_started_at.setter
    def _operator_retriage_started_at(self, value: float) -> None:
        self._operator_retriage_tracker.retriage_started_at = value

    @property
    def _last_operator_recovery_key(self) -> str:
        return self._operator_retriage_tracker.last_recovery_key

    @_last_operator_recovery_key.setter
    def _last_operator_recovery_key(self, value: str) -> None:
        self._operator_retriage_tracker.last_recovery_key = value

    @property
    def _operator_recovery_started_at(self) -> float:
        return self._operator_retriage_tracker.recovery_started_at

    @_operator_recovery_started_at.setter
    def _operator_recovery_started_at(self, value: float) -> None:
        self._operator_retriage_tracker.recovery_started_at = value

    @property
    def _last_advisory_retry_sig(self) -> str:
        return self._stale_advisory_recovery.last_retry_sig

    @_last_advisory_retry_sig.setter
    def _last_advisory_retry_sig(self, value: str) -> None:
        self._stale_advisory_recovery.last_retry_sig = value

    @property
    def _last_advisory_retry_at(self) -> float:
        return self._stale_advisory_recovery.last_retry_at

    @_last_advisory_retry_at.setter
    def _last_advisory_retry_at(self, value: float) -> None:
        self._stale_advisory_recovery.last_retry_at = value

    @property
    def _last_advisory_recovery_sig(self) -> str:
        return self._stale_advisory_recovery.last_recovery_sig

    @_last_advisory_recovery_sig.setter
    def _last_advisory_recovery_sig(self, value: str) -> None:
        self._stale_advisory_recovery.last_recovery_sig = value

    @property
    def _last_advisory_recovery_at(self) -> float:
        return self._stale_advisory_recovery.last_recovery_at

    @_last_advisory_recovery_at.setter
    def _last_advisory_recovery_at(self, value: float) -> None:
        self._stale_advisory_recovery.last_recovery_at = value

    # ------------------------------------------------------------------
    def _verify_task_hint_path(self, lane_name: str) -> Path:
        return self.run_dir / "task-hints" / f"{lane_name.strip().lower()}.json"

    def _write_verify_task_hint(
        self,
        job_id: str,
        dispatch_id: str,
        control_seq: int,
        active: bool,
    ) -> None:
        lane_name = self._prompt_owner("verify") or ""
        if not lane_name:
            return
        payload = {
            "lane": lane_name,
            "active": bool(active),
            "job_id": job_id if active else "",
            "dispatch_id": dispatch_id if active else "",
            "control_seq": control_seq if active else -1,
            "attempt": 1,
            "inactive_reason": "" if active else "task_hint_cleared",
            "updated_at": self._iso_utc(time.time()),
        }
        atomic_write_json(self._verify_task_hint_path(lane_name), payload)

    def _write_claude_verify_pending_prompt(self, prompt: str) -> bool:
        if self.dry_run:
            return True
        task_hint_dir = self.run_dir / "task-hints"
        try:
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            temp_path = task_hint_dir / ".claude.prompt.pending.tmp"
            pending_path = task_hint_dir / "claude.prompt.pending"
            temp_path.write_text(prompt, encoding="utf-8")
            temp_path.replace(pending_path)
            return True
        except OSError:
            log.exception("failed to write Claude verify pending prompt")
            return False

    def _send_verify_prompt_to_lane(
        self,
        target: str,
        prompt: str,
        dry_run: bool,
        pane_type: str,
    ) -> bool:
        if str(pane_type or "").strip().lower() == "claude":
            return self._write_claude_verify_pending_prompt(prompt)
        return watcher_dispatch.tmux_send_keys(target, prompt, dry_run, pane_type=pane_type)

    def _normalize_pty_pilot_lane(self, value: object) -> str:
        lane = str(value or "").strip()
        return "Gemini" if lane.lower() == "gemini" else ""

    def _pty_pilot_shell_command(self, lane_name: str) -> str:
        lane = self._lane_config(lane_name) or {}
        agent_cli = str(lane.get("agent_cli") or lane_name.lower()).strip()
        vendor_args = lane.get("vendor_args") or ()
        if not isinstance(vendor_args, (list, tuple)):
            vendor_args = ()
        parts = [agent_cli, *(str(arg) for arg in vendor_args if str(arg).strip())]
        return " ".join(shlex.quote(part) for part in parts if part)

    def _setup_pty_pilot_bridge(self) -> None:
        if self.dry_run:
            return
        if self._pty_pilot_lane != "Gemini":
            return
        if not self.gemini_pane_target:
            return
        command = self._pty_pilot_shell_command("Gemini")
        if not command:
            return
        registered = self._pty_bridge.register(
            self.gemini_pane_target,
            "Gemini",
            command,
            self.repo_root,
        )
        health = self._pty_bridge.health(self.gemini_pane_target)
        pty_health = None
        if health is not None:
            pty_health = {
                "alive": bool(health.get("alive")),
                "pid": health.get("pid"),
                "exit_code": health.get("exit_code"),
            }
        self._pty_pilot_register_result = {
            "lane": "Gemini",
            "pane_target": self.gemini_pane_target,
            "registered": bool(registered),
            "result": "registered" if registered else "failed",
            "policy_source": "runtime_policy.json",
            "command": command,
            "pty": pty_health,
        }
        self._log_raw(
            "pty_pilot_lane_register",
            "",
            "runtime_policy",
            {
                "lane": "Gemini",
                "pane_target": self.gemini_pane_target,
                "registered": bool(registered),
                "result": "registered" if registered else "failed",
                "policy_source": "runtime_policy.json",
                "command": command,
                "pty": pty_health,
            },
        )

    def _emit_pty_pilot_register_event(self) -> None:
        if self._pty_pilot_register_result is None:
            return
        payload = dict(self._pty_pilot_register_result)
        self._pty_pilot_register_result = None
        self._append_runtime_event("pty_pilot_lane_register", payload)

    def _pty_pilot_handles_target(self, target: str) -> bool:
        return (
            self._pty_pilot_lane == "Gemini"
            and bool(self.gemini_pane_target)
            and str(target or "").strip() == self.gemini_pane_target
        )

    def _capture_pane_text(self, target: str) -> str:
        if self._pty_pilot_handles_target(target):
            captured = self._pty_bridge.capture(target)
            if captured is not None:
                return captured
        return _shared_capture_pane_text(target)

    def _send_prompt_to_pane(self, target: str, prompt: str, pane_type: str) -> bool:
        if self._pty_pilot_handles_target(target):
            payload = prompt if prompt.endswith("\n") else f"{prompt}\n"
            sent = self._pty_bridge.send(target, payload)
            if sent is not None:
                return sent
        return watcher_dispatch.tmux_send_keys(target, prompt, self.dry_run, pane_type=pane_type)

    # ------------------------------------------------------------------
    def _lane_config(self, lane_name: str | None) -> Optional[dict[str, object]]:
        if not lane_name:
            return None
        for lane in self.runtime_lane_configs:
            if str(lane.get("name") or "") == lane_name:
                return lane
        return None

    # ------------------------------------------------------------------
    def _role_owner(self, role_name: str) -> Optional[str]:
        owner = str(self.runtime_role_owners.get(role_name) or "").strip()
        if owner:
            return owner
        if role_name in self.runtime_role_owners:
            return None
        return str(default_role_bindings().get(role_name) or "").strip() or None

    # ------------------------------------------------------------------
    def _prompt_owner(self, role_name: str) -> Optional[str]:
        owner = str(self.runtime_prompt_owners.get(role_name) or "").strip()
        return owner or self._role_owner(role_name)

    # ------------------------------------------------------------------
    def _role_read_first_doc(self, role_name: str) -> str:
        owner = self._role_owner(role_name) or ""
        return read_first_doc_for_owner(owner)

    # ------------------------------------------------------------------
    def _prompt_read_first_doc(self, role_name: str) -> str:
        owner = self._prompt_owner(role_name) or ""
        return read_first_doc_for_owner(owner)

    # ------------------------------------------------------------------
    def _role_pane_target(self, role_name: str) -> str:
        owner = self._role_owner(role_name)
        if not owner:
            return ""
        return str(self.agent_pane_targets.get(owner) or "")

    # ------------------------------------------------------------------
    def _prompt_pane_target(self, role_name: str) -> str:
        owner = self._prompt_owner(role_name)
        if not owner:
            return ""
        return str(self.agent_pane_targets.get(owner) or "")

    # ------------------------------------------------------------------
    def _role_pane_type(self, role_name: str) -> str:
        lane = self._lane_config(self._role_owner(role_name))
        pane_type = str((lane or {}).get("pane_type") or "").strip()
        return pane_type or _default_dispatch_pane_type()

    # ------------------------------------------------------------------
    def _prompt_pane_type(self, role_name: str) -> str:
        lane = self._lane_config(self._prompt_owner(role_name))
        pane_type = str((lane or {}).get("pane_type") or "").strip()
        return pane_type or _default_dispatch_pane_type()

    # ------------------------------------------------------------------
    def _dispatch_target_for_spec(self, spec: PromptDispatchSpec) -> tuple[str, str, str]:
        role = spec.functional_role or spec.lane_role
        owner = self._prompt_owner(role) or ""
        return self._prompt_pane_target(role), self._prompt_pane_type(role), owner

    # ------------------------------------------------------------------
    def _advisory_enabled(self) -> bool:
        return bool(self.runtime_controls.get("advisory_enabled")) and bool(self._role_owner("advisory"))

    # ------------------------------------------------------------------
    def _maybe_answer_gemini_git_permission_prompt(self) -> bool:
        if not self.gemini_git_permission_auto_allow:
            return False
        target = self.gemini_pane_target
        if not target:
            return False
        try:
            answered = watcher_dispatch.maybe_answer_gemini_git_permission_prompt(
                target,
                dry_run=self.dry_run,
            )
        except Exception as exc:
            log.warning("Gemini git permission prompt auto-answer check failed: %s", exc)
            return False
        if not answered:
            return False
        payload = {
            "lane": "Gemini",
            "pane_target": target,
            "tool": "git",
            "selection": "2",
            "scope": "session",
            "guard": "readonly_git_permission_prompt",
        }
        self._log_raw("gemini_git_permission_auto_allow_session", "", "lane_prompt", payload)
        self._append_runtime_event("gemini_git_permission_auto_allow_session", payload)
        return True

    # ------------------------------------------------------------------
    def _reset_inactive_advisory_busy_tracking(self) -> None:
        self._inactive_advisory_busy_key = ""
        self._inactive_advisory_busy_since = 0.0

    # ------------------------------------------------------------------
    def _active_advisory_request_in_progress(self) -> bool:
        if self._current_turn_state != WatcherTurnState.ADVISORY_ACTIVE:
            return False
        active_control = self._get_active_control_signal()
        request_control = self._control_signal_for_slot(
            active_control,
            "advisory_request",
            "request_open",
        )
        if request_control is None:
            return False
        request_seq = request_control.control_seq
        if request_seq >= 0 and request_seq < self._turn_active_control_seq:
            return False
        if self._advisory_advice_is_current_for_request(request_seq):
            return False
        return True

    # ------------------------------------------------------------------
    def _send_advisory_escape_for_snapshot(
        self,
        *,
        reason: str,
        snapshot: str,
        payload_extra: Optional[dict[str, object]] = None,
    ) -> bool:
        target = self._prompt_pane_target("advisory")
        if not target:
            return False
        owner = self._prompt_owner("advisory") or self._role_owner("advisory") or "advisory"
        if not _pane_text_looks_like_advisory_dispatch(snapshot):
            return False
        if not _shared_pane_text_has_busy_indicator(snapshot, owner):
            return False
        visible_next_seq = _extract_visible_advisory_next_control_seq(snapshot)
        payload: dict[str, object] = {
            "reason": reason,
            "lane": owner,
            "pane_target": target,
            "turn_state": self._current_turn_state.value,
            "active_control_file": self._turn_active_control_file,
            "active_control_seq": self._turn_active_control_seq,
            "visible_next_control_seq": visible_next_seq,
            "snapshot_hash": hashlib.sha256(snapshot.encode("utf-8")).hexdigest()[:16],
        }
        if payload_extra:
            payload.update(payload_extra)
        if not watcher_dispatch.tmux_send_escape(target, dry_run=self.dry_run):
            return False
        self._log_raw("advisory_lane_cancelled", "", "lane_prompt", payload)
        self._append_runtime_event("advisory_lane_cancelled", payload)
        return True

    # ------------------------------------------------------------------
    def _cancel_advisory_lane_if_busy(
        self,
        *,
        reason: str,
        payload_extra: Optional[dict[str, object]] = None,
    ) -> bool:
        target = self._prompt_pane_target("advisory")
        if not target:
            return False
        snapshot = self._capture_pane_text(target)
        return self._send_advisory_escape_for_snapshot(
            reason=reason,
            snapshot=snapshot,
            payload_extra=payload_extra,
        )

    # ------------------------------------------------------------------
    def _maybe_cancel_inactive_advisory_lane(self) -> bool:
        if not self._advisory_enabled():
            return False
        if self._active_advisory_request_in_progress():
            self._reset_inactive_advisory_busy_tracking()
            return False
        target = self._prompt_pane_target("advisory")
        if not target:
            self._reset_inactive_advisory_busy_tracking()
            return False

        snapshot = self._capture_pane_text(target)
        owner = self._prompt_owner("advisory") or self._role_owner("advisory") or "advisory"
        if (
            not _pane_text_looks_like_advisory_dispatch(snapshot)
            or not _shared_pane_text_has_busy_indicator(snapshot, owner)
        ):
            self._reset_inactive_advisory_busy_tracking()
            return False

        visible_next_seq = _extract_visible_advisory_next_control_seq(snapshot)
        busy_key = ":".join(
            [
                target,
                str(visible_next_seq),
                self._turn_active_control_file,
                str(self._turn_active_control_seq),
            ]
        )
        now = time.time()
        if busy_key != self._inactive_advisory_busy_key:
            self._inactive_advisory_busy_key = busy_key
            self._inactive_advisory_busy_since = now
        busy_age = now - self._inactive_advisory_busy_since
        if busy_age < self.inactive_advisory_cancel_sec:
            return False
        if (
            busy_key == self._last_inactive_advisory_cancel_key
            and now - self._last_inactive_advisory_cancel_at < max(60.0, self.inactive_advisory_cancel_sec)
        ):
            return False

        cancelled = self._send_advisory_escape_for_snapshot(
            reason="inactive_advisory_lane_busy",
            snapshot=snapshot,
            payload_extra={
                "inactive_busy_age_sec": int(busy_age),
                "cancel_threshold_sec": int(self.inactive_advisory_cancel_sec),
            },
        )
        if cancelled:
            self._last_inactive_advisory_cancel_key = busy_key
            self._last_inactive_advisory_cancel_at = now
            self._reset_inactive_advisory_busy_tracking()
        return cancelled

    # ------------------------------------------------------------------
    def _operator_stop_enabled(self) -> bool:
        return bool(self.runtime_controls.get("operator_stop_enabled"))

    # ------------------------------------------------------------------
    def _session_arbitration_enabled(self) -> bool:
        return (
            self._advisory_enabled()
            and bool(self.runtime_controls.get("session_arbitration_enabled"))
        )

    # ------------------------------------------------------------------
    def _make_run_id(self) -> str:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-p{os.getpid()}"

    # ------------------------------------------------------------------
    def _resolve_run_id(self) -> str:
        runtime_run_id = str(os.environ.get("PIPELINE_RUNTIME_RUN_ID") or "").strip()
        if runtime_run_id:
            return runtime_run_id
        return self._make_run_id()

    # ------------------------------------------------------------------
    def _job_state_archive_dir(self, source_run_id: str = "") -> Path:
        if source_run_id:
            return self.base_dir / "runs" / source_run_id / "state-archive"
        return self.state_archive_dir / "legacy"

    # ------------------------------------------------------------------
    def _job_state_manager(self) -> JobStateManager:
        self._jsm.state_dir = self.state_dir
        self._jsm.run_id = self.run_id
        self._jsm.started_at = self.started_at
        self._jsm.state_cleanup_legacy_grace_sec = self.state_cleanup_legacy_grace_sec
        return self._jsm

    # ------------------------------------------------------------------
    def _archive_job_state_file(self, path: Path, *, source_run_id: str = "", reason: str) -> None:
        return self._job_state_manager().archive_job_state_file(
            path,
            source_run_id=source_run_id,
            reason=reason,
        )

    # ------------------------------------------------------------------
    def _archive_stale_job_states(self) -> None:
        return self._job_state_manager().archive_stale_job_states()

    # ------------------------------------------------------------------
    @staticmethod
    def _iso_utc(ts: float) -> str:
        return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat().replace("+00:00", "Z")

    # ------------------------------------------------------------------
    def _runtime_exporter(self) -> WatcherRuntimeExporter:
        self._exporter.enabled = self._runtime_export_enabled
        self._exporter.run_id = self.run_id
        self._exporter.run_dir = self.run_dir
        self._exporter.run_status_path = self.run_status_path
        self._exporter.run_events_path = self.run_events_path
        self._exporter.current_run_path = self.current_run_path
        self._exporter.repo_root = self.repo_root
        return self._exporter

    # ------------------------------------------------------------------
    def _write_current_run_pointer(self) -> None:
        return self._runtime_exporter().write_run_pointer()

    # ------------------------------------------------------------------
    def _append_runtime_event(self, event_type: str, payload: dict[str, object]) -> None:
        return self._runtime_exporter().append_event(event_type, payload)

    # ------------------------------------------------------------------
    def _active_lane_name_for_turn(self, turn_state: Optional[WatcherTurnState] = None) -> str:
        state = turn_state or self._current_turn_state
        if state == WatcherTurnState.IMPLEMENT_ACTIVE:
            return self._prompt_owner("implement") or ""
        if state in (WatcherTurnState.VERIFY_ACTIVE, WatcherTurnState.VERIFY_FOLLOWUP):
            return self._prompt_owner("verify") or ""
        if state == WatcherTurnState.ADVISORY_ACTIVE:
            return self._prompt_owner("advisory") or ""
        return ""

    # ------------------------------------------------------------------
    def _active_role_for_turn(self, turn_state: Optional[WatcherTurnState] = None) -> str:
        state = turn_state or self._current_turn_state
        if state == WatcherTurnState.IMPLEMENT_ACTIVE:
            return "implement"
        if state in (WatcherTurnState.VERIFY_ACTIVE, WatcherTurnState.VERIFY_FOLLOWUP):
            return "verify"
        if state == WatcherTurnState.ADVISORY_ACTIVE:
            return "advisory"
        if state == WatcherTurnState.OPERATOR_WAIT:
            return "operator"
        return ""

    # ------------------------------------------------------------------
    def _implement_control_should_surface_working(self, active_control: Optional[ControlSignal]) -> bool:
        if active_control is None:
            return False
        if active_control.status != "implement" or active_control.control_seq < 0:
            return False
        implement_target = self._prompt_pane_target("implement")
        if not implement_target:
            return False
        pane_text = self._capture_pane_text(implement_target)
        if not pane_text.strip():
            return False
        return not _shared_pane_text_is_idle(pane_text)

    # ------------------------------------------------------------------
    def _build_lane_statuses(self, heartbeat_iso: str) -> list[dict[str, object]]:
        active_control = self._get_active_control_signal()
        lane_statuses = build_lane_statuses(
            heartbeat_iso=heartbeat_iso,
            active_lane=self._active_lane_name_for_turn(),
            implement_lane=self._prompt_owner("implement") or "",
            implement_live=self._implement_control_should_surface_working(active_control),
            lane_configs=self.runtime_lane_configs or _default_runtime_lane_configs(),
        )
        if self._pty_pilot_lane == "Gemini" and self.gemini_pane_target:
            pty_status: dict[str, object] | None = None
            health_fn = getattr(self._pty_bridge, "health", None)
            if callable(health_fn):
                health = health_fn(self.gemini_pane_target)
                if health is not None:
                    pty_status = {
                        "alive": bool(health.get("alive")),
                        "pid": health.get("pid"),
                        "exit_code": health.get("exit_code"),
                    }
            for lane_status in lane_statuses:
                if str(lane_status.get("name") or "") == "Gemini":
                    lane_status["pty"] = pty_status
                    break
        return lane_statuses

    # ------------------------------------------------------------------
    def _runtime_prompt_status_summary(self) -> str:
        status = read_json(self.run_status_path)
        if isinstance(status, dict):
            runtime_state = str(status.get("runtime_state") or "RUNNING").strip() or "RUNNING"
            automation_health = str(status.get("automation_health") or "ok").strip() or "ok"
            next_action = str(status.get("automation_next_action") or "continue").strip() or "continue"
            raw_control = status.get("control")
            raw_turn_state = status.get("turn_state")
            raw_active_round = status.get("active_round")
            control = dict(raw_control) if isinstance(raw_control, dict) else {}
            turn_state = dict(raw_turn_state) if isinstance(raw_turn_state, dict) else {}
            active_round = dict(raw_active_round) if isinstance(raw_active_round, dict) else {}
            control_file = str(control.get("active_control_file") or "none").strip() or "none"
            control_seq = control_seq_value(control.get("active_control_seq"), default=-1)
            control_status = str(control.get("active_control_status") or "none").strip() or "none"
            active_round_status = str(
                active_round.get("status")
                or active_round.get("state")
                or "none"
            ).strip() or "none"
            dispatch_stage = str(active_round.get("dispatch_stage") or "").strip()
            return "\n".join(
                [
                    f"- source: watcher status {self._repo_relative(self.run_status_path)}",
                    f"- run_id: {self.run_id}",
                    f"- runtime_state: {runtime_state}",
                    f"- automation_health: {automation_health}",
                    f"- automation_next_action: {next_action}",
                    f"- active_control: {control_file}#{control_seq} {control_status}",
                    f"- turn_state: {str(turn_state.get('state') or raw_turn_state or self._current_turn_state.value)}",
                    f"- active_round: {active_round_status}{(' dispatch_stage=' + dispatch_stage) if dispatch_stage else ''}",
                    "- lane_local_runtime_commands: non_authoritative_for_tmux_session_access_when_conflicting",
                ]
            )
        active_control = self._get_active_control_signal()
        if active_control is not None:
            control_file = f".pipeline/{active_control.path.name}"
            control_seq = active_control.control_seq
            control_status = active_control.status
        else:
            control_file = "none"
            control_seq = -1
            control_status = "none"
        return "\n".join(
            [
                "- source: watcher memory fallback",
                f"- run_id: {self.run_id}",
                "- runtime_state: RUNNING",
                "- automation_health: ok",
                "- automation_next_action: continue",
                f"- active_control: {control_file}#{control_seq} {control_status}",
                f"- turn_state: {self._current_turn_state.value}",
                "- lane_local_runtime_commands: non_authoritative_for_tmux_session_access_when_conflicting",
            ]
        )

    # ------------------------------------------------------------------
    def _transition_turn(
        self,
        new_state: WatcherTurnState,
        reason: str,
        *,
        active_control_file: str = "",
        active_control_seq: int = -1,
        verify_job_id: str = "",
    ) -> None:
        """Transition to a new turn state and write turn_state.json atomically."""
        old_state = self._current_turn_state
        now = time.time()
        control_snapshot = active_control_snapshot_from_status(
            {
                "active_control_file": active_control_file,
                "active_control_seq": active_control_seq,
            }
        )
        transition_control_file = str(control_snapshot.get("control_file") or active_control_file)
        transition_control_seq = snapshot_control_seq(
            control_snapshot,
            default=control_seq_value(active_control_seq, default=-1),
        )
        self._current_turn_state = new_state
        self._turn_entered_at = now
        self._turn_active_control_file = transition_control_file
        self._turn_active_control_seq = transition_control_seq
        active_role = self._active_role_for_turn(new_state)
        active_lane = self._active_lane_name_for_turn(new_state)
        legacy_state = legacy_turn_state_name(new_state.value)
        if new_state == WatcherTurnState.IMPLEMENT_ACTIVE:
            self._last_progress_at = now
            self._last_active_pane_fingerprint = ""
        log.info(
            "turn_state %s -> %s  reason=%s",
            old_state.value, new_state.value, reason,
        )
        self._log_raw(
            "turn_transition",
            "",
            "turn_state",
            {
                "from": old_state.value,
                "to": new_state.value,
                "from_legacy": legacy_turn_state_name(old_state.value),
                "to_legacy": legacy_state,
                "reason": reason,
                "active_control_file": transition_control_file,
                "active_control_seq": transition_control_seq,
                "active_role": active_role,
                "active_lane": active_lane,
            },
        )
        # Write turn_state.json atomically
        data: dict[str, object] = {
            "state": new_state.value,
            "legacy_state": legacy_state,
            "entered_at": now,
            "reason": reason,
            "active_control_file": transition_control_file,
            "active_control_seq": transition_control_seq,
            "active_role": active_role,
            "active_lane": active_lane,
        }
        if verify_job_id:
            data["verify_job_id"] = verify_job_id
        self.state_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self._turn_state_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp_path.replace(self._turn_state_path)
        self._append_runtime_event(
            "control_changed",
            {
                "turn_state": new_state.value,
                "legacy_turn_state": legacy_state,
                "reason": reason,
                "active_control_file": transition_control_file,
                "active_control_seq": transition_control_seq,
                "active_role": active_role,
                "active_lane": active_lane,
            },
        )
        if self._runtime_export_enabled:
            now_iso = self._iso_utc(time.time())
            write_runtime_status(
                enabled=True,
                run_status_path=self.run_status_path,
                run_id=self.run_id,
                turn_state=self._current_turn_state.value,
                legacy_turn_state=legacy_turn_state_name(self._current_turn_state.value),
                runtime_controls=self.runtime_controls,
                active_control=self._get_active_control_signal(),
                fallback_active_control_file=self._turn_active_control_file,
                fallback_active_control_seq=self._turn_active_control_seq,
                control_seq_age_cycles=self._control_seq_age_cycles,
                lane_statuses=self._build_lane_statuses(now_iso),
                heartbeat_iso=now_iso,
                write_current_run_pointer=self._write_current_run_pointer,
            )

    # ------------------------------------------------------------------
    def _get_path_mtime(self, path: Path) -> float:
        """path의 mtime 반환. 없으면 0.0."""
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    # ------------------------------------------------------------------
    def _get_path_sig(self, path: Path) -> str:
        """path 파일 시그니처 반환. 없으면 빈 문자열."""
        return compute_file_sig(path)

    # ------------------------------------------------------------------
    def _get_path_sha256(self, path: Path) -> str:
        return compute_file_sha256(path)

    # ------------------------------------------------------------------
    def _signal_claims_materialized(self, signal: dict[str, object]) -> bool:
        reason_code = normalize_reason_code(str(signal.get("reason_code") or ""))
        reason = normalize_reason_code(str(signal.get("reason") or ""))
        return (
            reason_code in _MATERIALIZED_BLOCK_REASON_CODES
            or reason in _MATERIALIZED_BLOCK_REASONS
        )

    # ------------------------------------------------------------------
    def _materialized_signal_corroborated(self, handoff_path: Path) -> Optional[bool]:
        try:
            handoff_text = handoff_path.read_text(encoding="utf-8")
        except OSError:
            return None
        replacement_target = _parse_handoff_sentence_replacement_target(handoff_text)
        if replacement_target is None:
            return None
        target_path = (self.repo_root / replacement_target.path).resolve()
        if not target_path.exists():
            return None
        try:
            target_text = target_path.read_text(encoding="utf-8")
        except OSError:
            return None
        has_current = replacement_target.current_sentence in target_text
        has_replacement = replacement_target.replacement_sentence in target_text
        if has_replacement and not has_current:
            return True
        if has_current and not has_replacement:
            return False
        return None

    # ------------------------------------------------------------------
    def _control_signal_reader(self) -> ControlSignalReader:
        self._csreader.advisory_enabled = self._advisory_enabled()
        self._csreader.operator_stop_enabled = self._operator_stop_enabled()
        return self._csreader

    # ------------------------------------------------------------------
    def _control_signal_from_entry(self, entry: dict[str, object]) -> Optional[ControlSignal]:
        return self._control_signal_reader().from_entry(entry)

    # ------------------------------------------------------------------
    def _iter_valid_control_signals(self, *, include_advisory_advice: bool = True) -> list[ControlSignal]:
        return self._control_signal_reader().iter_valid(
            include_advisory_advice=include_advisory_advice,
        )

    def _newest_control_signal(self, signals: list[ControlSignal]) -> Optional[ControlSignal]:
        return newest_control_signal(signals)

    def _control_signal_matches(self, signal: Optional[ControlSignal], path: Path, expected_status: str) -> bool:
        return control_signal_matches(signal, path, expected_status)

    def _control_signal_for_slot(
        self,
        signal: Optional[ControlSignal],
        slot_id: str,
        expected_status: str,
    ) -> Optional[ControlSignal]:
        return control_signal_for_slot(signal, slot_id, expected_status)

    def _newest_control_signal_for_slot(self, slot_id: str, expected_status: str) -> Optional[ControlSignal]:
        return self._control_signal_reader().for_slot(slot_id, expected_status)

    def _control_file_name(self, signal: Optional[ControlSignal], fallback: Path) -> str:
        return signal.path.name if signal is not None else fallback.name

    # ------------------------------------------------------------------
    def _get_active_control_signal(self) -> Optional[ControlSignal]:
        return self._newest_control_signal(self._iter_valid_control_signals())

    # ------------------------------------------------------------------
    def _highest_control_seq_for_age(self) -> int | None:
        candidates = self._iter_valid_control_signals(include_advisory_advice=False)
        seqs = [
            candidate.control_seq
            for candidate in candidates
            if candidate is not None and candidate.control_seq >= 0
        ]
        if not seqs:
            return None
        return max(seqs)

    # ------------------------------------------------------------------
    def _refresh_control_seq_age(self) -> int:
        try:
            current_seq = self._highest_control_seq_for_age()
        except Exception as exc:
            log.warning("failed to read control seq age: %s", exc)
            current_seq = None
        self._last_seen_control_seq, self._control_seq_age_cycles = advance_control_seq_age(
            last_seen_control_seq=self._last_seen_control_seq,
            control_seq_age_cycles=self._control_seq_age_cycles,
            current_control_seq=current_seq,
        )
        return self._control_seq_age_cycles

    # ------------------------------------------------------------------
    def _get_next_control_seq(self) -> int:
        seqs: list[int] = []
        seen: set[Path] = set()
        for spec in iter_control_slot_specs():
            for filename in spec.accepted_filenames:
                path = self.pipeline_dir / filename
                if path in seen or not path.exists():
                    continue
                seen.add(path)
                control_seq = self._read_control_seq_from_path(path)
                if control_seq >= 0:
                    seqs.append(control_seq)
        if not seqs:
            return 1
        return max(seqs) + 1

    # ------------------------------------------------------------------
    def _existing_stale_control_advisory_current(self, control_seq: int) -> bool:
        meta = read_control_meta(self.advisory_request_path)
        existing_seq = meta.get("control_seq")
        return (
            str(meta.get("status") or "").strip().lower() == "request_open"
            and str(meta.get("reason_code") or "").strip().lower() == "stale_control_advisory"
            and isinstance(existing_seq, int)
            and existing_seq >= control_seq
        )

    # ------------------------------------------------------------------
    def _render_stale_control_advisory_request(
        self,
        *,
        current_control_seq: int,
        next_control_seq: int,
    ) -> str:
        context = self.prompt_assembler.build_runtime_prompt_context()
        based_on_work = str(context["latest_work_path"])
        based_on_verify = str(context["latest_verify_path"])
        active_control = self._get_active_control_signal()
        active_control_file = (
            f".pipeline/{active_control.path.name}"
            if active_control is not None
            else ".pipeline/control slot"
        )
        active_control_seq = (
            active_control.control_seq
            if active_control is not None and active_control.control_seq >= 0
            else current_control_seq
        )
        read_first = [
            self._prompt_read_first_doc("advisory"),
            active_control_file,
        ]
        for path in (based_on_work, based_on_verify):
            if path and path != "없음" and path not in read_first:
                read_first.append(path)
        read_first_lines = "\n".join(f"- {path}" for path in read_first)
        return (
            "STATUS: request_open\n"
            f"CONTROL_SEQ: {next_control_seq}\n"
            "REASON_CODE: stale_control_advisory\n"
            "\n"
            "REQUEST: advisory-first routing for persistent stale control detection\n"
            "SOURCE: watcher stale_control_seq grace gate\n"
            f"SUPERSEDES: {active_control_file} CONTROL_SEQ {active_control_seq}\n"
            "\n"
            f"BASED_ON_WORK: {based_on_work}\n"
            f"BASED_ON_VERIFY: {based_on_verify}\n"
            "\n"
            "READ_FIRST:\n"
            f"{read_first_lines}\n"
            "\n"
            "---\n"
            "\n"
            "CONTEXT:\n"
            f"- `stale_control_seq=true` persisted for {self._control_seq_age_cycles} watcher cycles.\n"
            f"- Detection threshold: {STALE_CONTROL_CYCLE_THRESHOLD} cycles.\n"
            f"- Advisory grace: {STALE_ADVISORY_GRACE_CYCLES} additional cycles.\n"
            "- The watcher did not modify `.pipeline/implement_handoff.md` or `.pipeline/operator_request.md`.\n"
            "\n"
            "QUESTION:\n"
            "- Inspect the stale control state and recommend one exact next control action.\n"
        )

    # ------------------------------------------------------------------
    def _maybe_write_stale_control_advisory_request(self) -> bool:
        current_control_seq = self._last_seen_control_seq
        if current_control_seq is None or current_control_seq < 0:
            return False
        if not self._advisory_enabled():
            return False
        if self._is_active_control(self.operator_request_path, "needs_operator"):
            return False
        if self._is_active_control(self.advisory_request_path, "request_open"):
            return False
        if self._control_seq_age_cycles < (
            STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES
        ):
            return False
        if self._existing_stale_control_advisory_current(current_control_seq):
            return False

        next_control_seq = max(self._get_next_control_seq(), current_control_seq + 1)
        request_text = self._render_stale_control_advisory_request(
            current_control_seq=current_control_seq,
            next_control_seq=next_control_seq,
        )
        payload = {
            "reason_code": "stale_control_advisory",
            "tracked_control_seq": current_control_seq,
            "request_control_file": "advisory_request.md",
            "request_control_seq": next_control_seq,
            "control_age_cycles": self._control_seq_age_cycles,
            "stale_control_cycle_threshold": STALE_CONTROL_CYCLE_THRESHOLD,
            "stale_advisory_grace_cycles": STALE_ADVISORY_GRACE_CYCLES,
        }
        try:
            atomic_write_text(self.advisory_request_path, request_text)
        except Exception as exc:
            log.warning("failed to write stale control advisory request: %s", exc)
            try:
                self._log_raw(
                    "stale_control_advisory_write_failed",
                    str(self.advisory_request_path),
                    "turn_signal",
                    {**payload, "error": str(exc)},
                )
            except Exception as log_exc:
                log.warning("failed to log stale control advisory write failure: %s", log_exc)
            return False

        self._last_advisory_request_sig = self._get_path_sig(self.advisory_request_path)
        self._clear_implement_blocked_state("stale_control_advisory")
        self._log_raw(
            "stale_control_advisory_written",
            str(self.advisory_request_path),
            "turn_signal",
            payload,
        )
        self._append_runtime_event("stale_control_advisory_written", payload)
        self._transition_turn(
            WatcherTurnState.ADVISORY_ACTIVE,
            "stale_control_advisory",
            active_control_file="advisory_request.md",
            active_control_seq=next_control_seq,
        )
        self._notify_advisory_owner("stale_control_advisory")
        return True

    # ------------------------------------------------------------------
    def _is_active_control(self, path: Path, expected_status: str) -> bool:
        active = self._get_active_control_signal()
        return self._control_signal_matches(active, path, expected_status)

    # ------------------------------------------------------------------
    def _repo_relative(self, path: Optional[Path]) -> str:
        if path is None:
            return "없음"
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)

    # ------------------------------------------------------------------
    def _normalize_artifact_path(self, value: str | Path | None) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        path = Path(text)
        if path.is_absolute():
            try:
                path = path.resolve().relative_to(self.repo_root)
            except ValueError:
                return ""
            text = str(path)
        return text.replace("\\", "/")

    # ------------------------------------------------------------------
    def _verified_work_paths(self) -> set[str]:
        verified: set[str] = set()
        if not self.state_dir.exists():
            return verified
        for path in iter_job_state_paths(self.state_dir):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if str(data.get("status") or "") != JobStatus.VERIFY_DONE.value:
                continue
            normalized = self._normalize_artifact_path(data.get("artifact_path"))
            if normalized:
                verified.add(normalized)
        return verified

    # ------------------------------------------------------------------
    def _stale_operator_control_marker(self) -> Optional[dict[str, object]]:
        if not self._is_active_control(self.operator_request_path, "needs_operator"):
            return None
        try:
            control_text = self.operator_request_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        control_meta = read_control_meta(self.operator_request_path)
        pr_merge_resolution = self._pr_merge_status_cache.control_resolution(
            self.repo_root,
            control_text,
            control_meta,
        )
        resolution = resolve_operator_control(
            control_text=control_text,
            control_meta=control_meta,
            control_path=str(self.operator_request_path),
            control_mtime=self._get_path_mtime(self.operator_request_path),
            verified_work_paths=self._verified_work_paths(),
            completed_pr_numbers=pr_merge_resolution.completed_pr_numbers,
            mismatched_pr_numbers=pr_merge_resolution.head_mismatch_pr_numbers,
            control_file="operator_request.md",
            control_seq=self._read_control_seq_from_path(self.operator_request_path),
            normalize_path=self._normalize_artifact_path,
        )
        marker = resolution.get("stale_marker")
        return marker if isinstance(marker, dict) else None

    # ------------------------------------------------------------------
    def _operator_gate_marker(self) -> Optional[dict[str, object]]:
        if not self._is_active_control(self.operator_request_path, "needs_operator"):
            return None
        try:
            control_text = self.operator_request_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        control_meta = read_control_meta(self.operator_request_path)
        control_seq = self._read_control_seq_from_path(self.operator_request_path)
        resolution = resolve_operator_control(
            control_text=control_text,
            control_meta=control_meta,
            control_path=str(self.operator_request_path),
            control_seq=control_seq,
            control_mtime=self._get_path_mtime(self.operator_request_path),
            idle_stable=(
                not self._latest_work_needs_verify_broad()
                and not self._is_active_control(self.implement_handoff_path, "implement")
                and self._get_advisory_request_mtime() == 0.0
                and self._get_advisory_advice_mtime() == 0.0
            ),
        )
        marker = resolution.get("gate_marker")
        return marker if isinstance(marker, dict) else None

    # ------------------------------------------------------------------
    def _git_read(self, args: list[str]) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_root), *args],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    # ------------------------------------------------------------------
    def _git_exit_ok(self, args: list[str]) -> bool:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_root), *args],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0

    # ------------------------------------------------------------------
    def _is_allowed_rolling_pipeline_dirty_path(self, path_text: str) -> bool:
        normalized = path_text.replace("\\", "/").strip().strip('"')
        if not normalized:
            return False
        if " -> " in normalized:
            return all(
                self._is_allowed_rolling_pipeline_dirty_path(part)
                for part in normalized.split(" -> ", 1)
            )
        if normalized in _ROLLING_PIPELINE_PATHS:
            return True
        return any(normalized.startswith(prefix) for prefix in _ROLLING_PIPELINE_PREFIXES)

    # ------------------------------------------------------------------
    def _worktree_clean_except_rolling_pipeline(self) -> bool:
        status_text = self._git_read(["status", "--porcelain=v1", "--untracked-files=all"])
        if status_text is None:
            return False
        for raw_line in status_text.splitlines():
            line = raw_line.rstrip()
            if not line:
                continue
            path_text = line[3:] if len(line) > 3 else line
            if not self._is_allowed_rolling_pipeline_dirty_path(path_text):
                return False
        return True

    # ------------------------------------------------------------------
    def _satisfied_operator_approval_marker(self) -> Optional[dict[str, object]]:
        if not self._is_active_control(self.operator_request_path, "needs_operator"):
            return None
        try:
            control_text = self.operator_request_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        control_meta = read_control_meta(self.operator_request_path)
        if not is_commit_push_approval_stop(control_meta, control_text=control_text):
            return None

        branch = self._git_read(["branch", "--show-current"])
        if not branch or branch == "HEAD":
            return None
        upstream = self._git_read(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
        if not upstream:
            return None
        head_sha = self._git_read(["rev-parse", "HEAD"])
        upstream_sha = self._git_read(["rev-parse", "@{u}"])
        if not head_sha or not upstream_sha:
            return None
        upstream_contains_head = head_sha == upstream_sha or self._git_exit_ok(
            ["merge-base", "--is-ancestor", "HEAD", "@{u}"]
        )
        if not upstream_contains_head:
            return None
        if not self._worktree_clean_except_rolling_pipeline():
            return None

        return {
            "control_file": "operator_request.md",
            "control_seq": self._read_control_seq_from_path(self.operator_request_path),
            "reason": OPERATOR_APPROVAL_COMPLETED_REASON,
            "branch": branch,
            "head_sha": head_sha,
            "upstream": upstream,
            "upstream_sha": upstream_sha,
            "operator_request": "operator_request.md",
            "resolved_work_paths": [],
        }

    # ------------------------------------------------------------------
    def _mark_operator_retriage_started(self, operator_sig: str, marker: dict[str, object]) -> None:
        self._operator_retriage_tracker.mark_retriage_started(operator_sig, marker)

    # ------------------------------------------------------------------
    def _operator_retriage_is_same_semantic_bump(self, marker: dict[str, object]) -> bool:
        return self._operator_retriage_tracker.is_same_semantic_bump(marker)

    # ------------------------------------------------------------------
    def _idle_operator_retriage_marker(self) -> Optional[dict[str, object]]:
        return self._operator_retriage_tracker.idle_retriage_marker()

    # ------------------------------------------------------------------
    def _operator_control_recovery_marker(self) -> Optional[dict[str, object]]:
        return self._operator_retriage_tracker.control_recovery_marker()

    # ------------------------------------------------------------------
    def _operator_recovery_without_idle_marker(self) -> Optional[dict[str, object]]:
        return self._operator_retriage_tracker.recovery_without_idle_marker()

    # ------------------------------------------------------------------
    def _operator_recovery_key(self, operator_sig: str, marker: dict[str, object]) -> str:
        return self._operator_retriage_tracker.recovery_key(operator_sig, marker)

    # ------------------------------------------------------------------
    def _route_operator_recovery(
        self,
        *,
        operator_sig: str,
        operator_path: Path,
        status: str,
        marker: dict[str, object],
        source: str,
    ) -> bool:
        return self._operator_retriage_tracker.route_recovery(
            operator_sig=operator_sig,
            operator_path=operator_path,
            status=status,
            marker=marker,
            source=source,
        )

    # ------------------------------------------------------------------
    def _check_operator_recovery_without_signal(self) -> bool:
        return self._operator_retriage_tracker.check_recovery_without_signal()

    # ------------------------------------------------------------------
    def _path_mention(self, path: Optional[Path]) -> str:
        if path is None:
            return "(없음)"
        return f"@{self._repo_relative(path)}"

    # ------------------------------------------------------------------
    def _artifact_scanner(self) -> ArtifactScanner:
        self._scanner.watch_dir = self.watch_dir
        self._scanner.verify_dir = self.verify_dir
        self._scanner.repo_root = self.repo_root
        self._scanner.completion_paths = tuple(self.completion_paths)
        return self._scanner

    # ------------------------------------------------------------------
    def _find_latest_md(self, root: Path) -> Optional[Path]:
        return self._artifact_scanner().find_latest_md(root)

    # ------------------------------------------------------------------
    def _get_latest_work_path(self) -> Optional[Path]:
        return self._artifact_scanner().get_latest_work_path()

    # ------------------------------------------------------------------
    def _get_latest_work_path_broad(self) -> Optional[Path]:
        return self._artifact_scanner().get_latest_work_path_broad()

    # ------------------------------------------------------------------
    def _is_canonical_round_note(self, root: Path, path: Path) -> bool:
        return self._artifact_scanner().is_canonical_round_note(root, path)

    # ------------------------------------------------------------------
    def _is_metadata_only_work_note(self, work_path: Path) -> bool:
        return self._artifact_scanner().is_metadata_only_work_note(work_path)

    # ------------------------------------------------------------------
    def _is_dispatchable_work_note(self, work_path: Path) -> bool:
        return self._artifact_scanner().is_dispatchable_work_note(work_path)

    # ------------------------------------------------------------------
    def _get_latest_same_day_verify_path(self, work_path: Optional[Path]) -> Optional[Path]:
        return self._artifact_scanner().get_latest_same_day_verify_path(work_path)

    # ------------------------------------------------------------------
    def _get_latest_same_day_verify_path_for_work(self, work_path: Optional[Path]) -> Optional[Path]:
        return self._artifact_scanner().get_latest_same_day_verify_path_for_work(work_path)

    # ------------------------------------------------------------------
    def _get_same_day_verify_dir(self, work_path: Optional[Path]) -> Path:
        return self._artifact_scanner().get_same_day_verify_dir(work_path)

    # ------------------------------------------------------------------
    def _build_verify_feedback_sigs(self, job: JobState) -> tuple[str, str]:
        return self._artifact_scanner().build_verify_feedback_sigs(job)

    # ------------------------------------------------------------------
    def _build_verify_receipt_state(self, job: JobState) -> tuple[str, float]:
        return self._artifact_scanner().build_verify_receipt_state(job)

    # ------------------------------------------------------------------
    def _infer_advisory_report_hint(self, work_path: Optional[Path]) -> str:
        date_prefix = time.strftime("%Y-%m-%d")
        if work_path is not None:
            stem = work_path.stem
            if len(stem) >= 10 and stem[4] == "-" and stem[7] == "-":
                date_prefix = stem[:10]
        return f"{date_prefix}-<slug>.md"

    # ------------------------------------------------------------------
    def _extract_changed_file_paths_from_round_note(self, work_path: Optional[Path]) -> list[str]:
        return self._artifact_scanner().extract_changed_file_paths_from_round_note(work_path)

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    def _read_status_from_path(self, path: Path) -> Optional[str]:
        """지정 파일의 첫 STATUS: 줄을 읽어 값을 반환."""
        try:
            with path.open() as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("STATUS:"):
                        return stripped.split(":", 1)[1].strip().lower()
        except OSError:
            return None
        return None

    # ------------------------------------------------------------------
    def _read_control_seq_from_path(self, path: Path) -> int:
        """지정 control 파일의 CONTROL_SEQ 값을 읽는다. 없거나 invalid면 -1."""
        return control_seq_value(read_control_meta(path).get("control_seq"), default=-1)

    # ------------------------------------------------------------------
    def _supersede_stale_advisory_slots_for_operator_boundary(
        self,
        *,
        operator_seq: int,
        reason: str,
    ) -> None:
        """Mark older advisory control slots inactive once a real operator stop wins."""
        if operator_seq < 0:
            return

        targets = (
            (self.advisory_request_path, "request_open", "advisory_request.md"),
            (self.advisory_advice_path, "advice_ready", "advisory_advice.md"),
        )
        for path, expected_status, name in targets:
            if self._read_status_from_path(path) != expected_status:
                continue
            slot_seq = self._read_control_seq_from_path(path)
            if slot_seq >= 0 and slot_seq >= operator_seq:
                continue
            try:
                original_text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            supersede_lines = [
                "SUPERSEDED_BY: .pipeline/operator_request.md",
                f"SUPERSEDED_BY_SEQ: {operator_seq}",
                f"SUPERSEDED_REASON: {reason}",
            ]
            output_lines: list[str] = []
            status_written = False
            supersede_written = False
            for raw_line in original_text.splitlines():
                stripped = raw_line.strip()
                if stripped.startswith(
                    ("SUPERSEDED_BY:", "SUPERSEDED_BY_SEQ:", "SUPERSEDED_REASON:")
                ):
                    continue
                if stripped.startswith("STATUS:") and not status_written:
                    output_lines.append("STATUS: superseded")
                    status_written = True
                    continue
                output_lines.append(raw_line)
                if stripped.startswith("CONTROL_SEQ:") and not supersede_written:
                    output_lines.extend(supersede_lines)
                    supersede_written = True

            if not status_written:
                output_lines.insert(0, "STATUS: superseded")
            if not supersede_written:
                insert_at = 1 if output_lines and output_lines[0].strip().startswith("STATUS:") else 0
                output_lines[insert_at:insert_at] = supersede_lines

            atomic_write_text(path, "\n".join(output_lines).rstrip() + "\n")
            new_sig = self._get_path_sig(path)
            if path == self.advisory_request_path:
                self._last_advisory_request_sig = new_sig
            elif path == self.advisory_advice_path:
                self._last_advisory_advice_sig = new_sig
            payload = {
                "control_file": name,
                "control_seq": slot_seq,
                "superseded_by": "operator_request.md",
                "superseded_by_seq": operator_seq,
                "reason": reason,
            }
            self._log_raw(
                "advisory_slot_superseded",
                str(path),
                "turn_signal",
                payload,
            )
            self._append_runtime_event("advisory_slot_superseded", payload)

    # ------------------------------------------------------------------
    def _get_latest_implement_handoff(self) -> tuple[Optional[Path], float]:
        """active implement owner가 읽을 최신 implement handoff 슬롯을 고른다."""
        active_control = self._get_active_control_signal()
        implement_control = self._control_signal_for_slot(
            active_control,
            "implement_handoff",
            "implement",
        )
        if implement_control is None:
            return None, 0.0
        return implement_control.path, implement_control.mtime

    # ------------------------------------------------------------------
    def _get_pending_operator_mtime(self) -> float:
        """operator_request가 실제 pending stop이면 mtime을 반환한다."""
        if self._satisfied_operator_approval_marker() is not None:
            return 0.0
        if self._stale_operator_control_marker() is not None:
            return 0.0
        if self._operator_gate_marker() is not None:
            return 0.0
        active_control = self._get_active_control_signal()
        operator_control = self._control_signal_for_slot(
            active_control,
            "operator_request",
            "needs_operator",
        )
        if operator_control is not None:
            return operator_control.mtime
        return 0.0

    # ------------------------------------------------------------------
    def _get_advisory_request_mtime(self) -> float:
        active_control = self._get_active_control_signal()
        request_control = self._control_signal_for_slot(
            active_control,
            "advisory_request",
            "request_open",
        )
        if request_control is not None:
            return request_control.mtime
        return 0.0

    # ------------------------------------------------------------------
    def _get_advisory_advice_mtime(self) -> float:
        active_control = self._get_active_control_signal()
        advice_control = self._control_signal_for_slot(
            active_control,
            "advisory_advice",
            "advice_ready",
        )
        if advice_control is not None:
            return advice_control.mtime
        return 0.0

    # ------------------------------------------------------------------
    def _get_pending_advisory_request_mtime(self) -> float:
        return self._get_advisory_request_mtime()

    # ------------------------------------------------------------------
    def _get_pending_advisory_advice_mtime(self) -> float:
        return self._get_advisory_advice_mtime()

    # ------------------------------------------------------------------
    def _control_resolution_turn_active(self) -> bool:
        return self._current_turn_state in {
            WatcherTurnState.VERIFY_FOLLOWUP,
            WatcherTurnState.ADVISORY_ACTIVE,
            WatcherTurnState.OPERATOR_WAIT,
        }

    # ------------------------------------------------------------------
    def _advisory_advice_is_current_for_request(self, request_seq: int) -> bool:
        advice_control = self._newest_control_signal_for_slot(
            "advisory_advice",
            "advice_ready",
        )
        if advice_control is None or advice_control.control_seq < 0:
            return False
        if request_seq < 0:
            return True
        return advice_control.control_seq >= request_seq

    # ------------------------------------------------------------------
    def _retry_advisory_if_idle(self) -> None:
        self._stale_advisory_recovery.retry_if_idle()

    # ------------------------------------------------------------------
    def _stale_advisory_recovery_marker(self) -> Optional[dict[str, object]]:
        return self._stale_advisory_recovery.stale_recovery_marker()

    # ------------------------------------------------------------------
    def _advisory_recovery_attempt_for_request(self, request_control: ControlSignal) -> int:
        return self._stale_advisory_recovery.advisory_recovery_attempt_for_request(request_control)

    # ------------------------------------------------------------------
    def _prior_recovery_chain_count_from_request(self, request_path: Path) -> int:
        return self._stale_advisory_recovery.prior_recovery_chain_count_from_request(request_path)

    # ------------------------------------------------------------------
    def _prior_recovery_event_count(self, current_control_seq: int) -> int:
        return self._stale_advisory_recovery.prior_recovery_event_count(current_control_seq)

    # ------------------------------------------------------------------
    def _supersede_advisory_request_for_recovery(self, marker: dict[str, object]) -> bool:
        return self._stale_advisory_recovery.supersede_request_for_recovery(marker)

    # ------------------------------------------------------------------
    def _recover_stale_advisory(self) -> bool:
        return self._stale_advisory_recovery.recover_stale()

    # ------------------------------------------------------------------
    def _operator_blocks_handoff(self, handoff_mtime: float) -> bool:
        del handoff_mtime
        return self._get_pending_operator_mtime() > 0.0

    # ------------------------------------------------------------------
    def _get_work_tree_snapshot(self) -> dict[str, str]:
        return self._artifact_scanner().get_work_tree_snapshot()

    # ------------------------------------------------------------------
    def _get_work_tree_snapshot_broad(self) -> dict[str, str]:
        return self._artifact_scanner().get_work_tree_snapshot_broad()

    # ------------------------------------------------------------------
    def _get_latest_work_mtime(self) -> float:
        return self._artifact_scanner().get_latest_work_mtime()

    # ------------------------------------------------------------------
    def _work_has_matching_verify(
        self,
        work_path: Optional[Path],
        *,
        verified_work_paths: Optional[set[str]] = None,
    ) -> bool:
        return self._artifact_scanner().work_has_matching_verify(
            work_path,
            verified_work_paths=(
                verified_work_paths
                if verified_work_paths is not None
                else self._verified_work_paths()
            ),
        )

    # ------------------------------------------------------------------
    def _get_latest_unverified_work_path(
        self,
        *,
        include_metadata_only: bool,
        newer_than_mtime: float = 0.0,
    ) -> Optional[Path]:
        return self._artifact_scanner().get_latest_unverified_work_path(
            include_metadata_only=include_metadata_only,
            newer_than_mtime=newer_than_mtime,
            verified_work_paths=self._verified_work_paths(),
        )

    # ------------------------------------------------------------------
    def _handoff_verify_blocker_exists(self, handoff_mtime: float) -> bool:
        latest_work = self._get_latest_work_path_broad()
        if latest_work is None:
            return False
        latest_work_mtime = self._get_path_mtime(latest_work)
        if handoff_mtime > 0.0 and latest_work_mtime < handoff_mtime:
            return False
        return not self._work_has_matching_verify(latest_work)

    # ------------------------------------------------------------------
    def _latest_work_needs_verify(self) -> bool:
        return self._artifact_scanner().latest_work_needs_verify(
            verified_work_paths=self._verified_work_paths(),
        )

    # ------------------------------------------------------------------
    def _find_latest_md_broad(self, root: Path) -> Optional[Path]:
        return self._artifact_scanner().find_latest_md_broad(root)

    # ------------------------------------------------------------------
    def _latest_work_needs_verify_broad(self) -> bool:
        return self._artifact_scanner().latest_work_needs_verify_broad(
            verified_work_paths=self._verified_work_paths(),
        )

    # ------------------------------------------------------------------
    def _get_latest_verify_candidate_path(self) -> Optional[Path]:
        return self._artifact_scanner().get_latest_verify_candidate_path(
            verified_work_paths=self._verified_work_paths(),
        )

    # ------------------------------------------------------------------
    def _get_current_run_jobs(
        self,
        *,
        statuses: Optional[set[JobStatus]] = None,
    ) -> list[JobState]:
        return self._job_state_manager().get_current_run_jobs(statuses=statuses)

    # ------------------------------------------------------------------
    def _archive_current_run_job(self, job: JobState, *, reason: str) -> bool:
        return self._job_state_manager().archive_current_run_job(job, reason=reason)

    # ------------------------------------------------------------------
    def _archive_matching_verified_pending_jobs(self, jobs: list[JobState]) -> list[JobState]:
        """Drop stale current-run VERIFY_PENDING jobs that already have a matching /verify note."""
        active_jobs: list[JobState] = []
        for job in jobs:
            if job.status != JobStatus.VERIFY_PENDING:
                active_jobs.append(job)
                continue
            artifact_path = Path(job.artifact_path)
            if not self._work_has_matching_verify(artifact_path):
                active_jobs.append(job)
                continue
            self.stabilizer.clear(job.job_id)
            self.sm.release_verify_lease_for_archive(job)
            if job.artifact_hash:
                self.dedupe.forget(job.job_id, job.round, job.artifact_hash, "slot_verify")
            archived = self._archive_current_run_job(
                job,
                reason=_MATCHING_VERIFY_PENDING_ARCHIVE_REASON,
            )
            payload = {
                "job_id": job.job_id,
                "artifact_path": self._normalize_artifact_path(artifact_path) or str(artifact_path),
                "status": job.status.value,
                "reason": _MATCHING_VERIFY_PENDING_ARCHIVE_REASON,
                "archived": archived,
            }
            self._log_raw(
                "stale_verify_pending_archived",
                str(artifact_path),
                job.job_id,
                payload,
            )
            self._append_runtime_event("stale_verify_pending_archived", payload)
        return active_jobs

    # ------------------------------------------------------------------
    def _resolve_canonical_turn(self) -> str:
        """Resolve which functional role should act next."""
        handoff_active = self._is_active_control(self.implement_handoff_path, "implement")
        handoff_mtime = self._get_path_mtime(self.implement_handoff_path) if handoff_active else 0.0
        operator_request_active = self._is_active_control(self.operator_request_path, "needs_operator")
        advisory_request_active = self._is_active_control(self.advisory_request_path, "request_open")
        advisory_advice_active = self._is_active_control(self.advisory_advice_path, "advice_ready")
        handoff_completed = bool(
            handoff_active
            and completed_implement_handoff_truth(
                self.implement_handoff_path,
                repo_root=self.repo_root,
                work_root=self.watch_dir,
                verify_root=self.verify_dir,
                active_control_updated_at=handoff_mtime,
            )
            is not None
        )
        if (
            handoff_completed
            and not operator_request_active
            and not advisory_request_active
            and not advisory_advice_active
        ):
            return TURN_VERIFY_FOLLOWUP
        return resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=operator_request_active,
                advisory_request_active=advisory_request_active,
                advisory_advice_active=advisory_advice_active,
                implement_handoff_active=handoff_active and not handoff_completed,
                latest_work_needs_verify=(
                    self._handoff_verify_blocker_exists(handoff_mtime)
                    if not handoff_completed
                    else False
                ),
                implement_handoff_verify_active=self._implement_handoff_verify_active(),
                idle_release_cooldown_active=self._is_idle_release_cooldown_active(),
                operator_recovery_marker=self._operator_control_recovery_marker(),
                operator_gate_marker=self._operator_gate_marker(),
            )
        )

    # ------------------------------------------------------------------
    def _resolve_turn(self) -> str:
        """Compat helper returning the legacy watcher turn token."""
        return legacy_watcher_turn_name(self._resolve_canonical_turn())

    # ------------------------------------------------------------------
    def _check_implement_idle_timeout(self) -> None:
        """Check whether the active implement-owner lane has been idle too long."""
        if self._current_turn_state != WatcherTurnState.IMPLEMENT_ACTIVE:
            return

        target = self._prompt_pane_target("implement")
        if not target:
            return

        now = time.time()
        pane_text = self._capture_pane_text(target)
        pane_fingerprint = hashlib.md5(pane_text.encode()).hexdigest() if pane_text else ""

        # Check for progress: pane fingerprint changed
        if pane_fingerprint and pane_fingerprint != self._last_active_pane_fingerprint:
            self._last_active_pane_fingerprint = pane_fingerprint
            self._last_progress_at = now
            return

        # Check for progress: work snapshot changed
        current_snapshot = self._get_work_tree_snapshot_broad()
        if current_snapshot != self._work_baseline_snapshot:
            self._last_progress_at = now
            return

        # No progress — check timeout
        elapsed = now - self._last_progress_at
        if elapsed < self.implement_active_idle_timeout_sec:
            return

        # Final guard: pane must look idle too
        if not _shared_pane_text_is_idle(pane_text):
            return

        log.warning(
            "implement idle timeout: %.0fs since last progress, transitioning to IDLE",
            elapsed,
        )
        # Record cooldown to prevent immediate re-dispatch of same handoff
        self._last_idle_release_handoff_sig = self._get_path_sig(self.implement_handoff_path)
        self._last_idle_release_at = now
        self._transition_turn(WatcherTurnState.IDLE, "implement_idle_timeout")

    # ------------------------------------------------------------------
    def _check_operator_wait_idle_timeout(self) -> None:
        if self._current_turn_state != WatcherTurnState.OPERATOR_WAIT:
            return
        marker = self._idle_operator_retriage_marker()
        if marker is None:
            return
        operator_sig = self._get_path_sig(self.operator_request_path)
        if not operator_sig or operator_sig == self._last_operator_retriage_sig:
            return
        target = self._prompt_pane_target("verify")
        if not target:
            return
        verify_snapshot = self._capture_pane_text(target)
        if not _shared_pane_text_is_idle(verify_snapshot):
            return
        self._mark_operator_retriage_started(operator_sig, marker)
        self._clear_implement_blocked_state("operator_wait_idle_retriage")
        self._transition_turn(
            WatcherTurnState.VERIFY_FOLLOWUP,
            "operator_wait_idle_retriage",
            active_control_file="operator_request.md",
            active_control_seq=control_seq_value(marker.get("control_seq"), default=-1),
        )
        self._log_raw(
            "operator_request_idle_retriage",
            str(self.operator_request_path),
            "turn_signal",
            marker,
        )
        self._notify_verify_operator_retriage("operator_wait_idle_retriage", marker)

    # ------------------------------------------------------------------
    def _operator_retriage_no_next_control_marker(self) -> Optional[dict[str, object]]:
        if self._current_turn_state != WatcherTurnState.VERIFY_FOLLOWUP:
            return None
        if self._get_pending_advisory_request_mtime() > 0.0 or self._get_pending_advisory_advice_mtime() > 0.0:
            return None

        operator_sig = self._get_path_sig(self.operator_request_path)
        if not operator_sig:
            return None
        if any(
            str(pending.get("notify_kind") or "") in {
                "verify_operator_retriage",
                "codex_operator_retriage",
                "verify_control_recovery",
            }
            for pending in self.dispatch_queue.pending_notifications.values()
        ):
            return None

        marker = self._operator_gate_marker()
        followup_kind = "operator_retriage"
        started_at = 0.0
        if marker is not None:
            if not is_verify_followup_route(marker.get("routed_to")):
                return None
            if operator_sig != self._last_operator_retriage_sig:
                marker = None
            else:
                marker_fingerprint = str(marker.get("fingerprint") or "")
                semantic_started_at = (
                    self._operator_retriage_started_at
                    if marker_fingerprint
                    and marker_fingerprint == self._last_operator_retriage_fingerprint
                    and self._operator_retriage_started_at > 0.0
                    else 0.0
                )
                started_at = max(self._turn_entered_at, semantic_started_at) if semantic_started_at else max(
                    self._turn_entered_at,
                    self._get_path_mtime(self.operator_request_path),
                )

        if marker is None:
            recovery_marker = self._operator_recovery_without_idle_marker()
            if recovery_marker is None:
                return None
            recovery_key = self._operator_recovery_key(operator_sig, recovery_marker)
            if not recovery_key or recovery_key != self._last_operator_recovery_key:
                return None
            marker = recovery_marker
            followup_kind = "operator_recovery"
            recovery_started_at = self._operator_recovery_started_at if self._operator_recovery_started_at > 0.0 else 0.0
            started_at = max(self._turn_entered_at, recovery_started_at) if recovery_started_at else max(
                self._turn_entered_at,
                self._get_path_mtime(self.operator_request_path),
            )

        operator_seq = control_seq_value(marker.get("control_seq"), default=-1)
        if self._turn_active_control_seq >= 0 and operator_seq < self._turn_active_control_seq:
            return None

        now = time.time()
        if now - started_at < self.operator_retriage_no_control_sec:
            return None

        target = self._prompt_pane_target("verify")
        if not target:
            return None
        ready, defer_reason = self.dispatch_queue.lane_prompt_readiness(target)
        if not ready:
            return None

        return {
            **marker,
            "source_reason": str(marker.get("reason") or marker.get("reason_code") or ""),
            "followup_kind": followup_kind,
            "reason": "operator_retriage_no_next_control",
            "operator_sig": operator_sig,
            "verify_lane_ready": True,
            "verify_lane_ready_reason": defer_reason,
            "operator_retriage_age_sec": int(now - started_at),
        }

    # ------------------------------------------------------------------
    def _render_operator_retriage_advisory_request(
        self,
        *,
        marker: dict[str, object],
        next_control_seq: int,
    ) -> str:
        meta = read_control_meta(self.operator_request_path)
        context = self.prompt_assembler.build_runtime_prompt_context()
        based_on_work = str(meta.get("based_on_work") or context["latest_work_path"])
        based_on_verify = str(meta.get("based_on_verify") or context["latest_verify_path"])
        read_first = [
            self._prompt_read_first_doc("advisory"),
            ".pipeline/operator_request.md",
        ]
        for path in (based_on_work, based_on_verify):
            if path and path != "없음" and path not in read_first:
                read_first.append(path)
        read_first_lines = "\n".join(f"- {path}" for path in read_first)
        operator_seq = control_seq_value(marker.get("control_seq"), default=-1)
        reason_code = str(
            marker.get("reason_code")
            or marker.get("source_reason")
            or marker.get("reason")
            or "slice_ambiguity"
        )
        decision_class = str(marker.get("decision_class") or "next_slice_selection")
        return (
            "STATUS: request_open\n"
            f"CONTROL_SEQ: {next_control_seq}\n"
            "\n"
            "REQUEST: advisory-first arbitration after verify/handoff retriage returned without next control\n"
            "SOURCE: watcher operator_retriage_no_next_control\n"
            f"SUPERSEDES: .pipeline/operator_request.md CONTROL_SEQ {operator_seq}\n"
            "\n"
            f"BASED_ON_WORK: {based_on_work}\n"
            f"BASED_ON_VERIFY: {based_on_verify}\n"
            "\n"
            "READ_FIRST:\n"
            f"{read_first_lines}\n"
            "\n"
            "---\n"
            "\n"
            "CONTEXT:\n"
            f"- `.pipeline/operator_request.md` CONTROL_SEQ {operator_seq} was classified as `{reason_code}` / `{decision_class}` and routed to verify/handoff follow-up.\n"
            "- The verify/handoff owner was already prompted for operator retriage, but the lane returned idle without writing a newer `.pipeline/implement_handoff.md`, `.pipeline/advisory_request.md`, or `.pipeline/operator_request.md`.\n"
            "- This request keeps automation moving by asking the advisory owner to break the tie before falling back to an operator-only stop.\n"
            "\n"
            "QUESTION:\n"
            "Choose one exact next action from the current operator decision menu:\n"
            "\n"
            "1. `RECOMMEND: implement <exact validation or implementation slice>` if a bounded automatic slice is safe.\n"
            "2. `RECOMMEND: close family and switch axis <exact next axis>` if the current runtime family is sufficiently closed.\n"
            "3. `RECOMMEND: needs_operator <one decision>` only if safety, destructive action, auth/credential, approval-record, truth-sync, external publish approval, or another real operator-only blocker remains.\n"
            "\n"
            "OUTPUTS:\n"
            f"- Write advisory notes to `{context['advisory_report_path']}`.\n"
            f"- Write `.pipeline/advisory_advice.md` with `STATUS: advice_ready` and `CONTROL_SEQ: {next_control_seq}`.\n"
        )

    # ------------------------------------------------------------------
    def _promote_operator_retriage_no_next_control(self) -> bool:
        marker = self._operator_retriage_no_next_control_marker()
        if marker is None:
            return False

        operator_seq = control_seq_value(marker.get("control_seq"), default=-1)
        if not self._advisory_enabled():
            payload = {
                **marker,
                "advisory_disabled": True,
                "publish_held": True,
                "request_control_file": "",
                "request_control_seq": -1,
            }
            operator_sig = str(marker.get("operator_sig") or self._get_path_sig(self.operator_request_path))
            self._last_operator_retriage_sig = operator_sig
            self._last_operator_retriage_fingerprint = str(marker.get("fingerprint") or "")
            self._operator_retriage_started_at = time.time()
            self._last_operator_recovery_key = ""
            self._operator_recovery_started_at = 0.0
            self._clear_implement_blocked_state("operator_retriage_no_next_control")
            self._log_raw(
                "operator_retriage_no_next_control",
                str(self.operator_request_path),
                "turn_signal",
                payload,
            )
            self._append_runtime_event("operator_retriage_no_next_control", payload)
            self._transition_turn(
                WatcherTurnState.VERIFY_FOLLOWUP,
                "verify_followup_no_next_control",
                active_control_file="operator_request.md",
                active_control_seq=operator_seq,
            )
            self._notify_verify_operator_retriage(
                "operator_retriage_no_next_control",
                payload,
            )
            return True

        next_control_seq = max(self._get_next_control_seq(), operator_seq + 1)
        request_text = self._render_operator_retriage_advisory_request(
            marker=marker,
            next_control_seq=next_control_seq,
        )
        atomic_write_text(self.advisory_request_path, request_text)
        request_sig = self._get_path_sig(self.advisory_request_path)
        payload = {
            **marker,
            "request_control_file": "advisory_request.md",
            "request_control_seq": next_control_seq,
        }
        self._last_advisory_request_sig = request_sig
        self._clear_implement_blocked_state("operator_retriage_no_next_control")
        self._log_raw(
            "operator_retriage_no_next_control",
            str(self.operator_request_path),
            "turn_signal",
            payload,
        )
        self._append_runtime_event("operator_retriage_no_next_control", payload)
        self._transition_turn(
            WatcherTurnState.ADVISORY_ACTIVE,
            "operator_retriage_no_next_control",
            active_control_file="advisory_request.md",
            active_control_seq=next_control_seq,
        )
        self._operator_retriage_started_at = 0.0
        self._last_operator_retriage_fingerprint = ""
        self._last_operator_recovery_key = ""
        self._operator_recovery_started_at = 0.0
        self._notify_advisory_owner("operator_retriage_no_next_control")
        return True

    # ------------------------------------------------------------------
    def _is_idle_release_cooldown_active(self) -> bool:
        """True if the same handoff was recently released from idle timeout."""
        if not self._last_idle_release_handoff_sig:
            return False
        current_sig = self._get_path_sig(self.implement_handoff_path)
        if current_sig != self._last_idle_release_handoff_sig:
            return False
        elapsed = time.time() - self._last_idle_release_at
        return elapsed < self.implement_active_idle_timeout_sec

    # ------------------------------------------------------------------
    def _release_implement_handoff_from_idle(self, handoff_seq: int, release_reason: str) -> None:
        log.info(
            "implement handoff updated after implement lane became idle: release deferred seq=%s",
            handoff_seq,
        )
        self._log_raw(
            "implement_handoff_idle_release",
            str(self.implement_handoff_path),
            "turn_signal",
            {
                "status": "implement",
                "active_control_seq": handoff_seq,
                "previous_turn_control_seq": self._turn_active_control_seq,
                "release_reason": release_reason,
            },
        )
        self._clear_implement_blocked_state("implement_handoff_idle_release")
        self._transition_turn(
            WatcherTurnState.IMPLEMENT_ACTIVE,
            "implement_handoff_idle_release",
            active_control_file="implement_handoff.md",
            active_control_seq=handoff_seq,
        )
        self._work_baseline_snapshot = self._get_work_tree_snapshot_broad()
        self._pending_idle_release_handoff = None
        self._notify_implement_owner("implement_handoff_idle_release", self.implement_handoff_path)

    # ------------------------------------------------------------------
    def _check_pending_idle_release_handoff(self) -> bool:
        pending = self._pending_idle_release_handoff
        if not pending:
            return False
        if self._current_turn_state != WatcherTurnState.IMPLEMENT_ACTIVE:
            self._pending_idle_release_handoff = None
            return False
        active_control = self._get_active_control_signal()
        handoff_control = self._control_signal_for_slot(
            active_control,
            "implement_handoff",
            "implement",
        )
        handoff_sig = handoff_control.sig if handoff_control is not None else ""
        if not handoff_sig or handoff_sig != str(pending.get("sig") or ""):
            self._pending_idle_release_handoff = None
            return False
        handoff_seq = control_seq_value(pending.get("control_seq"), default=-1)
        if (
            handoff_control is None
            or handoff_control.control_seq != handoff_seq
            or handoff_seq <= self._turn_active_control_seq
            or self._is_idle_release_cooldown_active()
        ):
            self._pending_idle_release_handoff = None
            return False
        handoff_mtime = handoff_control.mtime
        dispatch_state = self._implement_handoff_dispatch_state(
            handoff_mtime,
            handoff_control.path if handoff_control is not None else self.implement_handoff_path,
        )
        if not dispatch_state["dispatchable"]:
            self._pending_idle_release_handoff = None
            return False
        if self._get_work_tree_snapshot_broad() != self._work_baseline_snapshot:
            self._pending_idle_release_handoff = None
            return False
        release_ready, release_reason = self._implement_lane_ready_for_handoff_release()
        if not release_ready:
            return False
        self._release_implement_handoff_from_idle(handoff_seq, release_reason)
        return True

    # ------------------------------------------------------------------
    def _dispatch_notify_spec(
        self,
        *,
        spec: PromptDispatchSpec,
        reason: str,
        missing_target_level: int = logging.WARNING,
    ) -> bool:
        target, pane_type, owner = self._dispatch_target_for_spec(spec)
        if not target:
            log_method = log.info if missing_target_level <= logging.INFO else log.warning
            role_label = spec.functional_role or spec.lane_role
            log_method("%s skipped: no %s owner target", spec.notify_label, role_label)
            return False
        log.info(
            "%s: reason=%s target=%s owner=%s lane_id=%s role=%s",
            spec.notify_label,
            reason,
            target,
            owner,
            spec.lane_id,
            spec.functional_role or spec.lane_role,
        )
        if spec.raw_event:
            self._log_raw(
                spec.raw_event,
                str(spec.prompt_path),
                "turn_signal",
                dict(spec.raw_payload),
        )
        return self.dispatch_queue.dispatch(
            watcher_dispatch.DispatchIntent(
                pending_key=spec.pending_key,
                notify_kind=spec.notify_kind,
                lane_role=spec.lane_role,
                functional_role=spec.functional_role or spec.lane_role,
                lane_id=spec.lane_id,
                agent_kind=spec.agent_kind,
                model_alias=spec.model_alias,
                reason=reason,
                prompt=spec.prompt,
                prompt_path=spec.prompt_path,
                target=target,
                pane_type=pane_type,
                control_seq=spec.control_seq,
                expected_status=spec.expected_status,
                expected_control_path=spec.expected_control_path,
                expected_control_slot=spec.expected_control_slot,
                expected_control_seq=spec.expected_control_seq,
                require_active_control=spec.require_active_control,
            )
        )

    # ------------------------------------------------------------------
    def _notify_implement_owner(self, reason: str, handoff_path: Optional[Path] = None) -> None:
        """implement owner pane에 다음 작업 프롬프트 전송."""
        self._dispatch_notify_spec(
            spec=self.prompt_assembler.build_implement_dispatch_spec(reason, handoff_path),
            reason=reason,
        )

    # ------------------------------------------------------------------
    def _notify_advisory_owner(self, reason: str) -> None:
        """advisory owner pane에 arbitration 프롬프트 전송."""
        if not self._advisory_enabled():
            log.info("notify_advisory_owner skipped: advisory disabled")
            self._log_raw(
                "advisory_notify_skipped",
                str(self.advisory_request_path),
                "turn_signal",
                {
                    "reason": "runtime_advisory_disabled",
                },
            )
            return
        if not self._prompt_pane_target("advisory"):
            log.info("notify_advisory_owner skipped: no advisory owner target")
            self._log_raw(
                "advisory_notify_skipped",
                str(self.advisory_request_path),
                "turn_signal",
                {
                    "reason": "missing_advisory_target",
                },
            )
            return
        self._dispatch_notify_spec(
            spec=self.prompt_assembler.build_advisory_dispatch_spec(reason),
            reason=reason,
            missing_target_level=logging.INFO,
        )

    # ------------------------------------------------------------------
    def _notify_verify_followup(self, reason: str) -> None:
        """advisory recommendation 이후 verify/handoff owner follow-up을 재호출."""
        self._dispatch_notify_spec(
            spec=self.prompt_assembler.build_verify_followup_dispatch_spec(reason),
            reason=reason,
        )

    # ------------------------------------------------------------------
    def _notify_verify_advisory_recovery(self, reason: str, marker: dict[str, object]) -> None:
        self._dispatch_notify_spec(
            spec=self.prompt_assembler.build_advisory_recovery_dispatch_spec(marker, reason),
            reason=reason,
        )

    # ------------------------------------------------------------------
    def _notify_control_recovery(self, reason: str, marker: dict[str, object]) -> None:
        """stale operator stop 해소 뒤 verify/handoff owner가 다음 control을 재결정하도록 호출."""
        self._dispatch_notify_spec(
            spec=self.prompt_assembler.build_control_recovery_dispatch_spec(marker, reason),
            reason=reason,
        )

    # ------------------------------------------------------------------
    def _notify_verify_control_recovery(self, reason: str, marker: dict[str, object]) -> None:
        self._notify_control_recovery(reason, marker)

    # ------------------------------------------------------------------
    def _record_operator_recovery_marker(
        self,
        *,
        recovery_reason: str,
        status: str,
        marker: dict[str, object],
        source: str,
    ) -> str:
        event_name = (
            OPERATOR_APPROVAL_COMPLETED_REASON
            if recovery_reason == OPERATOR_APPROVAL_COMPLETED_REASON
            else "operator_request_stale_ignored"
        )
        payload = {"status": status, **marker}
        self._log_raw(
            event_name,
            str(self.operator_request_path),
            source,
            payload,
        )
        if event_name == OPERATOR_APPROVAL_COMPLETED_REASON:
            self._append_runtime_event(
                event_name,
                {
                    "control_file": "operator_request.md",
                    "control_seq": control_seq_value(marker.get("control_seq"), default=-1),
                    "branch": str(marker.get("branch") or ""),
                    "head_sha": str(marker.get("head_sha") or ""),
                    "upstream": str(marker.get("upstream") or ""),
                    "upstream_sha": str(marker.get("upstream_sha") or ""),
                    "operator_request": "operator_request.md",
                    "reason": recovery_reason,
                },
            )
        return event_name

    # ------------------------------------------------------------------
    def _notify_operator_retriage(self, reason: str, marker: dict[str, object]) -> None:
        self._dispatch_notify_spec(
            spec=self.prompt_assembler.build_operator_retriage_dispatch_spec(marker, reason),
            reason=reason,
        )

    # ------------------------------------------------------------------
    def _notify_verify_operator_retriage(self, reason: str, marker: dict[str, object]) -> None:
        self._notify_operator_retriage(reason, marker)

    # ------------------------------------------------------------------
    def _notify_verify_blocked_triage(self, signal: dict[str, object], reason: str) -> bool:
        spec = self.prompt_assembler.build_blocked_triage_dispatch_spec(signal, reason)
        ok = self._dispatch_notify_spec(
            spec=spec,
            reason=reason,
        )
        if ok or spec.pending_key in self.dispatch_queue.pending_notifications:
            self._last_implement_blocked_fingerprint = str(signal.get("fingerprint", ""))
            self._clear_session_arbitration_draft("implement_blocked_triage")
            return True
        return False

    # ------------------------------------------------------------------
    def _implement_handoff_verify_active(self) -> bool:
        return self.lease.is_active("slot_verify")

    # ------------------------------------------------------------------
    def _implement_handoff_dispatch_state(
        self,
        handoff_mtime: float,
        handoff_path: Optional[Path] = None,
    ) -> dict[str, bool]:
        operator_blocked = self._operator_blocks_handoff(handoff_mtime)
        pending_verify = self._handoff_verify_blocker_exists(handoff_mtime)
        verify_active = self._implement_handoff_verify_active()
        completed_handoff = (
            completed_implement_handoff_truth(
                handoff_path or self.implement_handoff_path,
                repo_root=self.repo_root,
                work_root=self.watch_dir,
                verify_root=self.verify_dir,
                active_control_updated_at=handoff_mtime,
            )
            is not None
        )
        return {
            "operator_blocked": operator_blocked,
            "pending_verify": pending_verify,
            "verify_active": verify_active,
            "completed_handoff": completed_handoff,
            "dispatchable": (
                not operator_blocked
                and not pending_verify
                and not verify_active
                and not completed_handoff
            ),
        }

    # ------------------------------------------------------------------
    def _implement_lane_ready_for_handoff_release(self) -> tuple[bool, str]:
        target = self._prompt_pane_target("implement")
        if not target:
            return False, "implement_target_missing"
        try:
            pane_text = self._capture_pane_text(target)
        except Exception:
            return False, "pane_capture_failed"
        if not pane_text.strip():
            return False, "pane_blank"
        if not _shared_pane_text_is_idle(pane_text):
            return False, "implement_lane_busy"
        return True, "implement_lane_idle"

    # ------------------------------------------------------------------
    def _flush_pending_implement_handoff(self) -> None:
        """If verify lease just released and handoff is waiting, transition to implement."""
        if self._current_turn_state not in (
            WatcherTurnState.VERIFY_ACTIVE,
            WatcherTurnState.VERIFY_FOLLOWUP,
            WatcherTurnState.IDLE,
        ):
            return
        if self._implement_handoff_verify_active():
            return  # verify still running

        # Re-resolve: maybe the implement owner can go now
        turn = self._resolve_canonical_turn()
        if turn == "implement":
            handoff_path, _ = self._get_latest_implement_handoff()
            active_control = self._get_active_control_signal()
            seq = active_control.control_seq if active_control else -1
            if seq < self._turn_active_control_seq:
                return  # stale
            self._transition_turn(
                WatcherTurnState.IMPLEMENT_ACTIVE,
                "verify_lease_released",
                active_control_file=handoff_path.name if handoff_path is not None else self.implement_handoff_path.name,
                active_control_seq=seq,
            )
            self._work_baseline_snapshot = self._get_work_tree_snapshot_broad()
            self._clear_implement_blocked_state("implement_handoff_pending_release")
            self._notify_implement_owner("verify_lease_released", handoff_path)

    # ------------------------------------------------------------------
    def _check_pipeline_signal_updates(self) -> None:
        """handoff/operator 슬롯 시그니처를 확인하고 next owner routing을 결정한다."""
        self.dispatch_queue.flush_pending()
        active_control = self._get_active_control_signal()

        operator_control = self._control_signal_for_slot(
            active_control,
            "operator_request",
            "needs_operator",
        )
        operator_path = operator_control.path if operator_control is not None else self.operator_request_path
        operator_sig = operator_control.sig if operator_control is not None else self._get_path_sig(self.operator_request_path)
        if operator_sig and operator_sig != self._last_operator_request_sig:
            self._last_operator_request_sig = operator_sig
            status = self._read_status_from_path(operator_path) or "missing"
            operator_recovery = self._operator_control_recovery_marker()
            operator_gate = self._operator_gate_marker()
            if (
                operator_control is not None
                and operator_control.control_seq >= self._turn_active_control_seq
            ):
                if operator_recovery is not None:
                    self._route_operator_recovery(
                        operator_sig=operator_sig,
                        operator_path=operator_path,
                        status=status,
                        marker=operator_recovery,
                        source="turn_signal",
                    )
                    return
                if operator_gate is not None:
                    gate_reason = str(operator_gate.get("reason") or "operator_candidate_pending")
                    self._clear_implement_blocked_state(gate_reason)
                    if self._operator_retriage_is_same_semantic_bump(operator_gate):
                        self._last_operator_retriage_sig = operator_sig
                        self._log_raw(
                            "operator_request_gated_semantic_bump_ignored",
                            str(self.operator_request_path),
                            "turn_signal",
                            {"status": status, **operator_gate},
                        )
                        return
                    self._log_raw(
                        "operator_request_gated",
                        str(self.operator_request_path),
                        "turn_signal",
                        {"status": status, **operator_gate},
                    )
                    if str(operator_gate.get("routed_to") or "") == "hibernate":
                        self._transition_turn(WatcherTurnState.IDLE, "operator_request_gated_hibernate")
                        return
                    self._mark_operator_retriage_started(operator_sig, operator_gate)
                    self._transition_turn(
                        WatcherTurnState.VERIFY_FOLLOWUP,
                        "operator_request_gated",
                        active_control_seq=operator_control.control_seq,
                    )
                    self._notify_verify_operator_retriage("operator_request_gated", operator_gate)
                    return
                log.info("operator request updated: STATUS=needs_operator → implement notify blocked")
                self._clear_implement_blocked_state("operator_request_pending")
                self._transition_turn(
                    WatcherTurnState.OPERATOR_WAIT,
                    "operator_request_updated",
                    active_control_file=operator_path.name,
                    active_control_seq=operator_control.control_seq,
                )
                self._supersede_stale_advisory_slots_for_operator_boundary(
                    operator_seq=operator_control.control_seq,
                    reason="operator_request_pending",
                )
                self._log_raw(
                    "operator_request_pending",
                    str(operator_path),
                    "turn_signal",
                    {"status": status},
                )
            else:
                self._log_raw(
                    "operator_request_stale",
                    str(operator_path),
                    "turn_signal",
                    {
                        "status": status,
                        "active_control": active_control.kind if active_control else "none",
                    },
                )

        request_control = self._control_signal_for_slot(
            active_control,
            "advisory_request",
            "request_open",
        )
        request_path = request_control.path if request_control is not None else self.advisory_request_path
        advisory_request_sig = request_control.sig if request_control is not None else self._get_path_sig(self.advisory_request_path)
        if advisory_request_sig and advisory_request_sig != self._last_advisory_request_sig:
            self._last_advisory_request_sig = advisory_request_sig
            request_mtime = self._get_pending_advisory_request_mtime()
            status = self._read_status_from_path(request_path) or "missing"
            advisory_req_control_seq = request_control.control_seq if request_control is not None else -1
            if request_mtime > 0.0 and self._get_pending_operator_mtime() == 0.0 and advisory_req_control_seq >= self._turn_active_control_seq:
                log.info("advisory request updated: STATUS=request_open → advisory turn")
                self._clear_implement_blocked_state("advisory_request_pending")
                self._transition_turn(
                    WatcherTurnState.ADVISORY_ACTIVE,
                    "advisory_request_updated",
                    active_control_file=request_path.name,
                    active_control_seq=advisory_req_control_seq,
                )
                self._notify_advisory_owner("advisory_request_updated")
            else:
                self._log_raw(
                    "advisory_notify_skipped",
                    str(request_path),
                    "turn_signal",
                    {
                        "status": status,
                        "active_control": active_control.kind if active_control else "none",
                    },
                )

        advice_control = self._control_signal_for_slot(
            active_control,
            "advisory_advice",
            "advice_ready",
        )
        advice_path = advice_control.path if advice_control is not None else self.advisory_advice_path
        advisory_advice_sig = advice_control.sig if advice_control is not None else self._get_path_sig(self.advisory_advice_path)
        if advisory_advice_sig and advisory_advice_sig != self._last_advisory_advice_sig:
            self._last_advisory_advice_sig = advisory_advice_sig
            advice_mtime = self._get_pending_advisory_advice_mtime()
            status = self._read_status_from_path(advice_path) or "missing"
            advisory_adv_control_seq = advice_control.control_seq if advice_control is not None else -1
            if advice_mtime > 0.0 and self._get_pending_operator_mtime() == 0.0 and advisory_adv_control_seq >= self._turn_active_control_seq:
                log.info("advisory advice updated: STATUS=advice_ready → verify follow-up")
                self._clear_implement_blocked_state("advisory_advice_pending")
                self._transition_turn(
                    WatcherTurnState.VERIFY_FOLLOWUP,
                    "advisory_advice_updated",
                    active_control_file=advice_path.name,
                    active_control_seq=advisory_adv_control_seq,
                )
                self._cancel_advisory_lane_if_busy(
                    reason="advisory_advice_updated",
                    payload_extra={"advice_control_seq": advisory_adv_control_seq},
                )
                self._notify_verify_followup("advisory_advice_updated")
            else:
                self._log_raw(
                    "verify_followup_notify_skipped",
                    str(advice_path),
                    "turn_signal",
                    {
                        "status": status,
                        "active_control": active_control.kind if active_control else "none",
                    },
                )

        handoff_control = self._control_signal_for_slot(
            active_control,
            "implement_handoff",
            "implement",
        )
        handoff_path = handoff_control.path if handoff_control is not None else self.implement_handoff_path
        handoff_sig = (
            handoff_control.sig
            if handoff_control is not None
            else (self._get_path_sig(self.implement_handoff_path) if active_control is None else "")
        )
        if handoff_sig and handoff_sig != self._last_implement_handoff_sig:
            self._last_implement_handoff_sig = handoff_sig
            status = self._read_status_from_path(handoff_path) or "missing"
            handoff_mtime = self._get_path_mtime(handoff_path)
            dispatch_state = self._implement_handoff_dispatch_state(handoff_mtime, handoff_path)
            handoff_seq = handoff_control.control_seq if handoff_control is not None else -1
            if (
                handoff_control is not None
                and status == "implement"
                and self._current_turn_state == WatcherTurnState.IMPLEMENT_ACTIVE
            ):
                release_ready, release_reason = self._implement_lane_ready_for_handoff_release()
                if (
                    handoff_seq > self._turn_active_control_seq
                    and dispatch_state["dispatchable"]
                    and release_ready
                ):
                    self._release_implement_handoff_from_idle(handoff_seq, release_reason)
                else:
                    if handoff_seq > self._turn_active_control_seq and dispatch_state["dispatchable"]:
                        self._pending_idle_release_handoff = {
                            "sig": handoff_sig,
                            "control_seq": handoff_seq,
                        }
                    log.info("implement handoff updated during active implement round: defer hot-swap until round exit")
                    self._log_raw(
                        "implement_handoff_deferred",
                        str(handoff_path),
                        "turn_signal",
                        {
                            "status": status,
                            "active_control_seq": handoff_seq,
                            "current_turn_state": self._current_turn_state.value,
                            "current_turn_control_seq": self._turn_active_control_seq,
                            "dispatchable": dispatch_state["dispatchable"],
                            "completed_handoff": dispatch_state["completed_handoff"],
                            "release_ready": release_ready,
                            "release_reason": release_reason,
                        },
                    )
            elif (
                handoff_control is not None
                and status == "implement"
                and dispatch_state["dispatchable"]
                and handoff_seq >= self._turn_active_control_seq
            ):
                log.info("implement handoff updated: STATUS=implement → implement turn")
                self._clear_implement_blocked_state("implement_handoff_updated")
                self._transition_turn(
                    WatcherTurnState.IMPLEMENT_ACTIVE,
                    "implement_handoff_updated",
                    active_control_file=handoff_path.name,
                    active_control_seq=handoff_seq,
                )
                self._work_baseline_snapshot = self._get_work_tree_snapshot_broad()
                self._notify_implement_owner("implement_handoff_updated", handoff_path)
            else:
                if (
                    handoff_control is not None
                    and status == "implement"
                    and dispatch_state["verify_active"]
                ):
                    self._clear_implement_blocked_state("implement_handoff_pending_release")
                log.info("implement handoff updated: STATUS=%s → implement notify skipped", status)
                self._log_raw(
                    "implement_notify_skipped",
                    str(handoff_path),
                    "turn_signal",
                    {
                        "status": status,
                        "operator_blocked": dispatch_state["operator_blocked"],
                        "pending_verify": dispatch_state["pending_verify"],
                        "verify_active": dispatch_state["verify_active"],
                        "completed_handoff": dispatch_state["completed_handoff"],
                        "active_control": active_control.kind if active_control else "none",
                    },
                )

        self._flush_pending_implement_handoff()

    # ------------------------------------------------------------------
    def _log_raw(self, event: str, path: str, job_id: str,
                 extra: Optional[dict] = None) -> None:
        entry: dict = {"event": event, "path": path, "job_id": job_id, "at": time.time()}
        if extra:
            entry.update(extra)
        with (self.events_dir / "raw.jsonl").open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    def _write_session_arbitration_draft(self, signal: dict[str, object]) -> bool:
        now = time.time()
        fingerprint = str(signal["fingerprint"])
        if fingerprint == self._last_session_arbitration_fingerprint:
            return False
        if now < self._session_arbitration_cooldowns.get(fingerprint, 0.0):
            return False

        reasons = signal["reasons"]
        body = self.prompt_assembler.format_session_arbitration_draft(signal)
        self.session_arbitration_draft_path.write_text(body)
        self._last_session_arbitration_fingerprint = fingerprint
        self._last_session_arbitration_draft_sig = self._get_path_sig(self.session_arbitration_draft_path)
        self._log_raw(
            "session_arbitration_draft_written",
            str(self.session_arbitration_draft_path),
            "implement_session",
            {"reasons": list(reasons)},
        )
        return True

    # ------------------------------------------------------------------
    def _clear_session_arbitration_draft(self, reason: str) -> None:
        fingerprint = self._last_session_arbitration_fingerprint
        if fingerprint:
            self._session_arbitration_cooldowns[fingerprint] = (
                time.time() + self.session_arbitration_cooldown_sec
            )
        if self.session_arbitration_draft_path.exists():
            self.session_arbitration_draft_path.unlink()
            self._log_raw(
                "session_arbitration_draft_cleared",
                str(self.session_arbitration_draft_path),
                "implement_session",
                {"reason": reason},
            )
        self._last_session_arbitration_draft_sig = self._get_path_sig(self.session_arbitration_draft_path)
        self._last_session_arbitration_fingerprint = ""
        self._session_arbitration_snapshot_fingerprints = {}
        self._session_arbitration_snapshot_changed_at = {}

    # ------------------------------------------------------------------
    def _clear_implement_blocked_state(self, reason: str) -> None:
        fingerprint = self._last_implement_blocked_fingerprint
        if fingerprint:
            self._implement_blocked_cooldowns[fingerprint] = (
                time.time() + self.implement_blocked_cooldown_sec
            )
            self._log_raw(
                "implement_blocked_cleared",
                str(self.implement_handoff_path),
                "implement_session",
                {"reason": reason, "blocked_fingerprint": fingerprint},
            )
        self._last_implement_blocked_fingerprint = ""
        self._implement_blocked_snapshot_fingerprints = {}
        self._implement_blocked_snapshot_changed_at = {}

    # ------------------------------------------------------------------
    def _implement_blocked_snapshot_stable_sec(self, snapshot: str) -> float:
        now = time.time()
        fingerprint = hashlib.sha1(snapshot.encode("utf-8")).hexdigest()
        if self._implement_blocked_snapshot_fingerprints.get("implement") != fingerprint:
            self._implement_blocked_snapshot_fingerprints["implement"] = fingerprint
            self._implement_blocked_snapshot_changed_at["implement"] = now
            return 0.0
        changed_at = self._implement_blocked_snapshot_changed_at.get("implement", now)
        return max(0.0, now - changed_at)

    # ------------------------------------------------------------------
    def _check_implement_blocked(self) -> bool:
        handoff_path, _ = self._get_latest_implement_handoff()
        if handoff_path is None:
            self._clear_implement_blocked_state("handoff_inactive")
            return False

        implement_target = self._prompt_pane_target("implement")
        if not implement_target:
            self._clear_implement_blocked_state("implement_target_missing")
            return False
        implement_snapshot = self._capture_pane_text(implement_target)
        handoff_path_rel = self._repo_relative(handoff_path)
        handoff_sha = self._get_path_sha256(handoff_path)

        signal = _extract_implement_blocked_signal(
            implement_snapshot,
            active_handoff_path=handoff_path_rel,
            active_handoff_sha=handoff_sha,
        )
        soft_signal: Optional[dict[str, object]] = None
        if signal is None:
            soft_signal = _extract_implement_completed_handoff_signal(implement_snapshot, active_handoff_sha=handoff_sha)
            if soft_signal is None:
                soft_signal = _extract_implement_forbidden_menu_signal(implement_snapshot, active_handoff_sha=handoff_sha)
            if (
                soft_signal is not None
                and self._implement_blocked_snapshot_stable_sec(implement_snapshot) >= self.implement_blocked_settle_sec
            ):
                signal = soft_signal

        if signal is None:
            if soft_signal is not None:
                return False
            self._clear_implement_blocked_state("signal_cleared")
            return False

        fingerprint = str(signal["fingerprint"])
        if fingerprint == self._last_implement_blocked_fingerprint:
            return True
        if time.time() < self._implement_blocked_cooldowns.get(fingerprint, 0.0):
            return False
        if self._signal_claims_materialized(signal):
            corroborated = self._materialized_signal_corroborated(handoff_path)
            if corroborated is False:
                self._log_raw(
                    "implement_blocked_ignored",
                    str(handoff_path),
                    "implement_session",
                    {
                        "blocked_source": signal.get("source", "sentinel"),
                        "blocked_reason": signal.get("reason", "implement_blocked"),
                        "blocked_reason_code": signal.get("reason_code", ""),
                        "blocked_fingerprint": fingerprint,
                        "handoff_sha": handoff_sha,
                        "ignore_reason": "materialization_uncorroborated",
                    },
                )
                return False

        self._log_raw(
            "implement_blocked_detected",
            str(handoff_path),
            "implement_session",
            {
                "blocked_source": signal.get("source", "sentinel"),
                "blocked_reason": signal.get("reason", "implement_blocked"),
                "blocked_fingerprint": fingerprint,
                "handoff_sha": handoff_sha,
            },
        )
        self._notify_verify_blocked_triage(signal, "implement_blocked")
        return True

    # ------------------------------------------------------------------
    def _pane_snapshot_stable_sec(self, pane_name: str, snapshot: str) -> float:
        now = time.time()
        fingerprint = hashlib.sha1(snapshot.encode("utf-8")).hexdigest()
        if self._session_arbitration_snapshot_fingerprints.get(pane_name) != fingerprint:
            self._session_arbitration_snapshot_fingerprints[pane_name] = fingerprint
            self._session_arbitration_snapshot_changed_at[pane_name] = now
            return 0.0
        changed_at = self._session_arbitration_snapshot_changed_at.get(pane_name, now)
        return max(0.0, now - changed_at)

    # ------------------------------------------------------------------
    def _session_arbitration_ready(self, pane_snapshots: dict[str, str]) -> bool:
        if not self._session_arbitration_enabled():
            return False
        implement_target = self._prompt_pane_target("implement")
        verify_target = self._prompt_pane_target("verify")
        advisory_target = self._prompt_pane_target("advisory")
        if not implement_target or not verify_target or not advisory_target:
            return False
        if watcher_dispatch._is_pane_dead(implement_target):
            return False
        if watcher_dispatch._is_pane_dead(verify_target):
            return False
        if watcher_dispatch._is_pane_dead(advisory_target):
            return False
        if not _shared_pane_text_is_idle(pane_snapshots["verify"]):
            return False
        if not _shared_pane_text_is_idle(pane_snapshots["advisory"]):
            return False
        if _shared_pane_text_is_idle(pane_snapshots["implement"]):
            return True
        return (
            self._pane_snapshot_stable_sec("implement", pane_snapshots["implement"])
            >= self.session_arbitration_settle_sec
        )

    # ------------------------------------------------------------------
    def _check_implement_live_session_escalation(self) -> None:
        if self._current_turn_state != WatcherTurnState.IMPLEMENT_ACTIVE:
            return
        if not self._session_arbitration_enabled():
            self._clear_session_arbitration_draft("session_arbitration_disabled")
            return
        if self._get_pending_operator_mtime() > 0.0:
            self._clear_session_arbitration_draft("operator_request_pending")
            return
        if self._get_pending_advisory_request_mtime() > 0.0 or self._get_pending_advisory_advice_mtime() > 0.0:
            self._clear_session_arbitration_draft("canonical_advisory_pending")
            return
        if self._read_status_from_path(self.implement_handoff_path) != "implement":
            self._clear_session_arbitration_draft("handoff_inactive")
            return

        pane_snapshots = {
            "implement": self._capture_pane_text(self._prompt_pane_target("implement")),
            "verify": self._capture_pane_text(self._prompt_pane_target("verify")),
            "advisory": self._capture_pane_text(self._prompt_pane_target("advisory")),
        }
        signal = _extract_live_session_escalation(pane_snapshots["implement"])
        if signal is None:
            self._clear_session_arbitration_draft("signal_cleared")
            return
        if not self._session_arbitration_ready(pane_snapshots):
            return
        if self._write_session_arbitration_draft(signal):
            log.info(
                "live session escalation draft written: reasons=%s path=%s",
                ",".join(signal["reasons"]),
                self.session_arbitration_draft_path,
            )

    # ------------------------------------------------------------------
    def print_ab_ratios(self) -> None:
        """
        A/B 비율 계산식 고정:
          suppression_rate = suppressed / raw
          dispatch_rate    = dispatch / raw
        """
        def count(p: Path) -> int:
            return sum(1 for _ in p.open()) if p.exists() else 0

        raw        = count(self.events_dir / "raw.jsonl")
        suppressed = count(self.events_dir / "suppressed.jsonl")
        dispatched = count(self.events_dir / "dispatch.jsonl")

        if raw == 0:
            log.info("A/B ratios: no raw events yet")
            return

        log.info(
            "A/B ratios [experimental]  raw=%d  suppressed=%d (%.1f%%)  dispatch=%d (%.1f%%)",
            raw,
            suppressed, 100 * suppressed / raw,
            dispatched, 100 * dispatched / raw,
        )

    # ------------------------------------------------------------------
    def run(self) -> None:
        log.info(
            "WatcherCore v2.1 started  watch_dir=%s  dry_run=%s  poll=%.1fs  "
            "startup_grace=%.1fs  jsonschema=%s  implement_pane=%s  verify_pane=%s  enabled_lanes=%s",
            self.watch_dir, self.dry_run, self.poll_interval,
            self.startup_grace_sec, _JSONSCHEMA_AVAILABLE,
            self._prompt_pane_target("implement"),
            self._prompt_pane_target("verify"),
            ",".join(self.runtime_adapter.get("enabled_lanes") or []),
        )
        last_report_at = time.time()
        report_interval_sec = 60.0
        previous_signals: dict[int, object] = {}

        def _handle_shutdown_signal(signum: int, _frame: object) -> None:
            log.info("watcher shutdown signal: %s", signum)
            raise SystemExit(0)

        for signum in (signal.SIGTERM, signal.SIGINT):
            try:
                previous_signals[signum] = signal.getsignal(signum)
                signal.signal(signum, _handle_shutdown_signal)
            except (OSError, ValueError):
                continue
        try:
            while True:
                try:
                    self._poll()
                    now = time.time()
                    if now - last_report_at >= report_interval_sec:
                        self.print_ab_ratios()
                        last_report_at = now
                except Exception as e:
                    log.exception("poll error: %s", e)
                time.sleep(self.poll_interval)
        finally:
            self._pty_bridge.teardown()
            for signum, previous in previous_signals.items():
                try:
                    signal.signal(signum, previous)
                except (OSError, ValueError):
                    pass

    # ------------------------------------------------------------------
    def _reset_job_for_new_round(self, job: JobState, job_id: str, reason: str) -> None:
        """현재 파일 내용이 바뀌었을 때 새 라운드로 재진입."""
        self.sm.reset_job_for_new_round(job, job_id, reason)
        log.info("re-entered: job=%s round=%d (%s)", job_id, job.round, reason)

    # ------------------------------------------------------------------
    def _poll(self) -> None:
        if not self.watch_dir.exists():
            return

        self._refresh_control_seq_age()
        if self._runtime_export_enabled:
            now_iso = self._iso_utc(time.time())
            write_runtime_status(
                enabled=True,
                run_status_path=self.run_status_path,
                run_id=self.run_id,
                turn_state=self._current_turn_state.value,
                legacy_turn_state=legacy_turn_state_name(self._current_turn_state.value),
                runtime_controls=self.runtime_controls,
                active_control=self._get_active_control_signal(),
                fallback_active_control_file=self._turn_active_control_file,
                fallback_active_control_seq=self._turn_active_control_seq,
                control_seq_age_cycles=self._control_seq_age_cycles,
                lane_statuses=self._build_lane_statuses(now_iso),
                heartbeat_iso=now_iso,
                write_current_run_pointer=self._write_current_run_pointer,
            )
            self._emit_pty_pilot_register_event()
        if self._maybe_answer_gemini_git_permission_prompt():
            return
        if self._maybe_write_stale_control_advisory_request():
            return

        # 새 tmux lane이 막 떠 있는 동안 초기 dispatch가 삼켜지지 않도록
        # startup grace가 끝날 때까지 초기 turn 판정을 보류한다.
        if not self._initial_turn_checked:
            elapsed = time.time() - self.started_at
            if elapsed < self.startup_grace_sec:
                return

        # --- 시작 시 1회: 턴 판단 ---
        if not self._initial_turn_checked:
            self._initial_turn_checked = True
            turn = self._resolve_canonical_turn()
            log.info("initial turn: %s", turn)
            self._log_raw("initial_turn", "", "startup", {"turn": turn})
            if turn == "implement":
                handoff_path, _ = self._get_latest_implement_handoff()
                handoff_seq = self._read_control_seq_from_path(handoff_path) if handoff_path else -1
                self._work_baseline_snapshot = self._get_work_tree_snapshot_broad()
                self._transition_turn(
                    WatcherTurnState.IMPLEMENT_ACTIVE,
                    "startup_turn_implement",
                    active_control_file=handoff_path.name if handoff_path else self.implement_handoff_path.name,
                    active_control_seq=handoff_seq,
                )
                self._notify_implement_owner("startup_turn_implement", handoff_path)
                log.info("IMPLEMENT_ACTIVE: baseline_files=%d",
                         len(self._work_baseline_snapshot))
                return
            if turn == "operator":
                active_control = self._get_active_control_signal()
                operator_control = self._control_signal_for_slot(
                    active_control,
                    "operator_request",
                    "needs_operator",
                )
                operator_seq = (
                    operator_control.control_seq
                    if operator_control is not None
                    else self._read_control_seq_from_path(self.operator_request_path)
                )
                self._transition_turn(
                    WatcherTurnState.OPERATOR_WAIT,
                    "startup_turn_operator",
                    active_control_file=operator_control.path.name if operator_control is not None else self.operator_request_path.name,
                    active_control_seq=operator_seq,
                )
                self._supersede_stale_advisory_slots_for_operator_boundary(
                    operator_seq=operator_seq,
                    reason="startup_turn_operator",
                )
                log.info("startup turn blocked by pending operator_request")
                self._log_raw(
                    "operator_request_pending",
                    str(self.operator_request_path),
                    "startup",
                    {"status": "needs_operator"},
                )
                return
            if turn == "advisory":
                active_control = self._get_active_control_signal()
                advisory_control = self._control_signal_for_slot(
                    active_control,
                    "advisory_request",
                    "request_open",
                )
                advisory_seq = (
                    advisory_control.control_seq
                    if advisory_control is not None
                    else self._read_control_seq_from_path(self.advisory_request_path)
                )
                self._transition_turn(
                    WatcherTurnState.ADVISORY_ACTIVE,
                    "startup_turn_advisory",
                    active_control_file=advisory_control.path.name if advisory_control is not None else self.advisory_request_path.name,
                    active_control_seq=advisory_seq,
                )
                self._notify_advisory_owner("startup_turn_advisory")
                return
            if turn == "verify_followup":
                operator_recovery = self._operator_control_recovery_marker()
                operator_gate = self._operator_gate_marker()
                if operator_recovery is not None:
                    recovery_reason = str(operator_recovery.get("reason") or "verified_blockers_resolved")
                    self._transition_turn(
                        WatcherTurnState.VERIFY_FOLLOWUP,
                        recovery_reason,
                        active_control_file="operator_request.md",
                        active_control_seq=control_seq_value(
                            operator_recovery.get("control_seq"),
                            default=-1,
                        ),
                    )
                    if recovery_reason == "operator_wait_idle_retriage":
                        self._mark_operator_retriage_started(
                            self._get_path_sig(self.operator_request_path),
                            operator_recovery,
                        )
                    recovery_event = self._record_operator_recovery_marker(
                        recovery_reason=recovery_reason,
                        status="needs_operator",
                        marker=operator_recovery,
                        source="startup",
                    )
                    if recovery_reason == "operator_wait_idle_retriage":
                        self._notify_verify_operator_retriage("startup_turn_operator_idle_retriage", operator_recovery)
                    else:
                        self._notify_verify_control_recovery(recovery_event, operator_recovery)
                elif operator_gate is not None:
                    self._transition_turn(WatcherTurnState.VERIFY_FOLLOWUP, "startup_turn_verify_followup")
                    self._mark_operator_retriage_started(
                        self._get_path_sig(self.operator_request_path),
                        operator_gate,
                    )
                    self._log_raw(
                        "operator_request_gated",
                        str(self.operator_request_path),
                        "startup",
                        operator_gate,
                    )
                    self._notify_verify_operator_retriage("startup_turn_operator_gated", operator_gate)
                else:
                    self._transition_turn(WatcherTurnState.VERIFY_FOLLOWUP, "startup_turn_verify_followup")
                    self._notify_verify_followup("startup_turn_verify_followup")
                return
            if turn == "verify":
                self._transition_turn(WatcherTurnState.VERIFY_ACTIVE, "startup_turn_verify")
                # verify/handoff rerun은 work/ 감시 루프에서 자연스럽게 디스패치됨
                return
            # idle
            self._transition_turn(WatcherTurnState.IDLE, "startup_turn_idle")

        # --- rolling handoff / operator 슬롯 감시 (verify → implement / operator 방향) ---
        self._check_pipeline_signal_updates()
        if self._maybe_cancel_inactive_advisory_lane():
            return
        if self._promote_operator_retriage_no_next_control():
            return
        if self._check_operator_recovery_without_signal():
            return
        self._check_operator_wait_idle_timeout()

        # --- 최신 control signal이 operator stop이면 자동 진행을 멈춤 ---
        _, handoff_mtime = self._get_latest_implement_handoff()
        if self._operator_blocks_handoff(handoff_mtime):
            return

        # --- current-run verify가 살아 있으면 그 라운드를 끝까지 우선 진행 ---
        active_verify_jobs = self._get_current_run_jobs(statuses={JobStatus.VERIFY_RUNNING})
        if active_verify_jobs:
            for job in active_verify_jobs:
                self.sm.step_verify_close_chain(job)
            self._flush_pending_implement_handoff()
            return

        advisory_control_pending = (
            self._get_pending_advisory_request_mtime() > 0.0
            or self._get_pending_advisory_advice_mtime() > 0.0
        )

        pending_verify_jobs = self._get_current_run_jobs(statuses={JobStatus.VERIFY_PENDING})
        pending_verify_jobs = self._archive_matching_verified_pending_jobs(pending_verify_jobs)
        if pending_verify_jobs:
            if advisory_control_pending or self._control_resolution_turn_active():
                if advisory_control_pending:
                    if self._recover_stale_advisory():
                        return
                    self._retry_advisory_if_idle()
                    self._clear_session_arbitration_draft("canonical_advisory_pending")
                return
            # startup 이후 state에서 복원된 current-run verify pending은 최신 work candidate
            # 스캔만으로는 다시 step되지 않을 수 있으므로, 가장 최근 pending round를 먼저
            # 재개해 starvation 없이 verify lane으로 다시 밀어준다.
            self.sm.step(pending_verify_jobs[0])
            self._flush_pending_implement_handoff()
            return

        # --- advisory arbitration이 pending이면 다른 자동 진행을 잠시 멈춤 ---
        if advisory_control_pending:
            if self._recover_stale_advisory():
                return
            self._retry_advisory_if_idle()
            self._clear_session_arbitration_draft("canonical_advisory_pending")
            return

        # --- follow-up/advisory/operator resolution 중에는 stale verify를 다시 열지 않음 ---
        if self._control_resolution_turn_active():
            return

        # --- implement 차례 대기 중이면 work/ 감시 건너뜀 ---
        if self._current_turn_state == WatcherTurnState.IMPLEMENT_ACTIVE:
            if self._check_implement_blocked():
                return
            self._check_implement_live_session_escalation()
            if self._check_pending_idle_release_handoff():
                return
            self._check_implement_idle_timeout()
            if self._current_turn_state != WatcherTurnState.IMPLEMENT_ACTIVE:
                return  # idle timeout fired
            # work/ 전체 스냅샷이 달라졌는지 확인
            current_snapshot = self._get_work_tree_snapshot_broad()
            if current_snapshot == self._work_baseline_snapshot:
                return  # implement owner가 아직 작업 안 함 → verify dispatch 하지 않음
            # implement owner가 새 파일을 썼거나 기존 파일 내용을 바꿨으므로 대기 해제
            self._transition_turn(WatcherTurnState.IDLE, "implement_activity_detected")
            self._work_baseline_snapshot = {}
            self._clear_session_arbitration_draft("implement_activity_resumed")
            self._clear_implement_blocked_state("implement_activity_resumed")
            log.info("implement activity detected by snapshot diff, resuming verify dispatch")

        # --- work/ 디렉터리 감시 (implement → verify 방향) ---
        # baseline과 동일하게 가장 최신 파일 1개만 처리
        latest = self._get_latest_verify_candidate_path()
        artifacts_to_process = [latest] if latest else []
        for artifact in artifacts_to_process:
            job_id = make_job_id(self.watch_dir, artifact)
            job    = JobState.load(self.state_dir, job_id)

            if job is None:
                self._log_raw("artifact_seen", str(artifact), job_id)
                job = JobState.from_artifact(job_id, str(artifact), run_id=self.run_id)
                job.save(self.state_dir)
                log.info("new job: %s  path=%s", job_id, artifact)
            elif not job.run_id:
                job.run_id = self.run_id
                job.save(self.state_dir)
            elif job.run_id != self.run_id:
                previous_run_id = job.run_id
                self._log_raw(
                    "artifact_reseen_new_run",
                    str(artifact),
                    job_id,
                    {
                        "previous_run_id": previous_run_id,
                        "current_run_id": self.run_id,
                    },
                )
                job = JobState.from_artifact(job_id, str(artifact), run_id=self.run_id)
                job.save(self.state_dir)
                log.info("job reset for new run: %s previous_run=%s", job_id, previous_run_id)

            current_hash: Optional[str] = None
            if job.status in TERMINAL_STATES or job.status == JobStatus.VERIFY_PENDING:
                try:
                    current_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
                except OSError:
                    continue

            if job.status in TERMINAL_STATES:
                if current_hash == job.artifact_hash:
                    continue  # 내용 동일 → 진짜 완료
                self._reset_job_for_new_round(job, job_id, "content changed")

            elif job.status == JobStatus.VERIFY_PENDING:
                if job.artifact_hash and current_hash and current_hash != job.artifact_hash:
                    self._reset_job_for_new_round(
                        job, job_id, "content changed before verify dispatch")
                    continue

            elif job.status == JobStatus.VERIFY_RUNNING:
                try:
                    running_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
                except OSError:
                    continue
                if job.artifact_hash and running_hash != job.artifact_hash:
                    self._log_raw(
                        "artifact_changed_during_verify", str(artifact), job_id,
                        {"round": job.round},
                    )
                    log.info("artifact changed during verify: job=%s round=%d", job_id, job.round)

            if job.status == JobStatus.VERIFY_PENDING:
                self._log_raw(
                    "dispatch_candidate", str(artifact), job_id,
                    {"slot": "slot_verify", "round": job.round},
                )

            self.sm.step(job)


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="watcher_core.py - Pipeline Watcher v2.1")
    parser.add_argument("--watch-dir",            required=True)
    parser.add_argument("--base-dir",             default=".pipeline")
    parser.add_argument("--repo-root",            default="",
                        help="프롬프트 표시 기준 repo root (기본: watch-dir parent)")
    parser.add_argument("--verify-pane-target",   default="",
                        help="verify-owner pane target (physical default: <session>:0.1)")
    parser.add_argument("--claude-pane-target",   default="",
                        help="implement-owner pane target (physical default: <session>:0.0)")
    parser.add_argument("--gemini-pane-target",   default="",
                        help="advisory-owner pane target (physical default: <session>:0.2)")
    parser.add_argument("--manifest-schema-path", default="",
                        help="agent_manifest.schema.json 경로 (기본: ./schemas/)")
    parser.add_argument("--dry-run",              action="store_true")
    parser.add_argument("--poll",                 type=float, default=1.0)
    parser.add_argument("--settle",               type=float, default=3.0)
    parser.add_argument("--startup-grace",        type=float, default=8.0)
    parser.add_argument("--lease-ttl",            type=int,   default=900)
    parser.add_argument("--verify-done-deadline", type=float, default=DEFAULT_VERIFY_DONE_DEADLINE_SEC,
                        help="seconds to wait after verify TASK_ACCEPTED before TASK_DONE is considered missing")
    parser.add_argument("--verify-prompt",         default="",
                        help="verify role prompt (기본: 내부 verify contract)")
    parser.add_argument("--implement-prompt",      default="",
                        help="implement role prompt")
    parser.add_argument("--advisory-prompt",       default="",
                        help="advisory role prompt")
    parser.add_argument("--followup-prompt",       default="",
                        help="followup role prompt")
    parser.add_argument("--claude-prompt",         default="",
                        help=argparse.SUPPRESS)
    parser.add_argument("--gemini-prompt",         default="",
                        help=argparse.SUPPRESS)
    parser.add_argument("--codex-followup-prompt", default="",
                        help=argparse.SUPPRESS)
    parser.add_argument("--disable-gemini-git-permission-auto-allow", action="store_true",
                        help="disable narrow Gemini readonly git permission prompt auto-answer")
    args = parser.parse_args()

    config: dict = {
        "watch_dir":          args.watch_dir,
        "base_dir":           args.base_dir,
        "repo_root":          args.repo_root or str(Path(args.watch_dir).parent),
        "dry_run":            args.dry_run,
        "poll_interval":      args.poll,
        "settle_sec":         args.settle,
        "startup_grace_sec":  args.startup_grace,
        "lease_ttl":          args.lease_ttl,
        "verify_done_deadline_sec": args.verify_done_deadline,
        "gemini_git_permission_auto_allow": not args.disable_gemini_git_permission_auto_allow,
    }
    # pane target: 명시되면 config에 포함, 비어있으면 WatcherCore가 project-aware default 사용
    if args.verify_pane_target:
        config["verify_pane_target"] = args.verify_pane_target
    if args.claude_pane_target:
        config["claude_pane_target"] = args.claude_pane_target
    if args.gemini_pane_target:
        config["gemini_pane_target"] = args.gemini_pane_target
    if args.verify_prompt:
        config["verify_prompt_template"] = args.verify_prompt
    if args.implement_prompt:
        config["implement_prompt"] = args.implement_prompt
    elif args.claude_prompt:
        config["claude_prompt"] = args.claude_prompt
    if args.advisory_prompt:
        config["advisory_prompt"] = args.advisory_prompt
    elif args.gemini_prompt:
        config["gemini_prompt"] = args.gemini_prompt
    if args.followup_prompt:
        config["followup_prompt"] = args.followup_prompt
    elif args.codex_followup_prompt:
        config["codex_followup_prompt"] = args.codex_followup_prompt
    if args.manifest_schema_path:
        config["manifest_schema_path"] = args.manifest_schema_path

    WatcherCore(config).run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("watcher_core crashed")
        raise
