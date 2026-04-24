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

import atexit
import datetime as dt
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

_PROJECT_IMPORT_ROOT = os.environ.get("PROJECT_ROOT") or os.getcwd()
if _PROJECT_IMPORT_ROOT:
    project_import_path = str(Path(_PROJECT_IMPORT_ROOT).resolve())
    if project_import_path not in sys.path:
        sys.path.insert(0, project_import_path)

from pipeline_gui.setup_profile import resolve_project_runtime_adapter
from pipeline_runtime.automation_health import (
    STALE_ADVISORY_GRACE_CYCLES,
    STALE_CONTROL_CYCLE_THRESHOLD,
    advance_control_seq_age,
    derive_automation_health,
)
from pipeline_runtime.lane_surface import (
    busy_markers_for_lane as _shared_busy_markers_for_lane,
    capture_pane_text as _shared_capture_pane_text,
    pane_text_has_busy_indicator as _shared_pane_text_has_busy_indicator,
    pane_text_has_codex_activity as _shared_pane_text_has_codex_activity,
    pane_text_has_gemini_activity as _shared_pane_text_has_gemini_activity,
    pane_text_has_input_cursor as _shared_pane_text_has_input_cursor,
    pane_text_has_working_indicator as _shared_pane_text_has_working_indicator,
    pane_text_is_idle as _shared_pane_text_is_idle,
    text_matches_markers as _shared_text_matches_markers,
    wait_for_pane_settle as _shared_wait_for_pane_settle,
)
from pipeline_runtime.lane_catalog import (
    default_role_bindings,
    legacy_watcher_pane_target_arg_for_lane,
    physical_lane_order,
    physical_lane_specs,
    read_first_doc_for_owner,
)
from pipeline_runtime.operator_autonomy import (
    OPERATOR_APPROVAL_COMPLETED_REASON,
    classify_operator_candidate,
    evaluate_stale_operator_control,
    is_commit_push_approval_stop,
    normalize_reason_code,
    operator_gate_marker_from_decision,
)
from pipeline_runtime.pr_merge_state import PrMergeStatusCache
from pipeline_runtime.role_routes import (
    ADVISORY_RECOVERY_NOTIFY,
    VERIFY_FOLLOWUP_ROUTE,
    VERIFY_TRIAGE_ESCALATION,
    VERIFY_TRIAGE_ONLY_REASON,
    is_verify_followup_route,
    is_verify_triage_escalation,
    normalize_notify_kind,
    normalize_verify_triage_escalation,
)
from pipeline_runtime.schema import (
    active_control_snapshot_from_entry,
    active_control_snapshot_from_status,
    atomic_write_text,
    completed_implement_handoff_truth,
    control_block_from_snapshot,
    control_filenames_equivalent,
    control_seq_value,
    control_slot_spec,
    control_slot_spec_for_filename,
    iter_job_state_paths,
    latest_verify_note_for_work,
    process_starttime_fingerprint,
    read_control_meta,
    read_json,
    read_pipeline_control_snapshot,
    same_day_verify_dir_for_work,
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
    JobState,
    JobStatus,
    StateMachine,
    TERMINAL_STATES,
    compute_file_sig,
    compute_md_tree_sig,
    compute_multi_file_sig,
    make_job_id,
)
from watcher_dispatch import DispatchIntent, WatcherDispatchQueue
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
)

# jsonschema는 선택적 의존성 — 없으면 필수 필드 구조 검증만 수행
try:
    import jsonschema as _jsonschema
    _JSONSCHEMA_AVAILABLE = True
except ImportError:
    _jsonschema = None  # type: ignore
    _JSONSCHEMA_AVAILABLE = False

# ---------------------------------------------------------------------------
# Session name — pipeline-gui.py / start-pipeline.sh와 동일 규칙
# ---------------------------------------------------------------------------
_SESSION_PREFIX = "aip"
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


def _session_name_for_project(project_path: str) -> str:
    """Project path → deterministic session name (aip-<safe-dirname>)."""
    name = Path(project_path).resolve().name or "default"
    safe = re.sub(r"[^A-Za-z0-9_-]", "", name)
    return f"{_SESSION_PREFIX}-{safe}" if safe else f"{_SESSION_PREFIX}-default"


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


# ---------------------------------------------------------------------------
# 로깅
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("watcher_core")

SCHEMA_VERSION = 1
ROUND_NOTE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")
ROUND_NOTE_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
ROUND_NOTE_PATH_RE = re.compile(r"(?<!@)(?:\./)?([A-Za-z0-9_.\-/]+?\.[A-Za-z0-9]+)")
ROUND_NOTE_METADATA_ONLY_PREFIXES = ("work/", "verify/", "report/", ".pipeline/", "pipeline/")
_DISPATCH_LOCKS_GUARD = threading.Lock()
_DISPATCH_LOCKS: dict[str, threading.Lock] = {}
_DISPATCH_LOCK_TIMEOUT_SEC = 30.0
_MATCHING_VERIFY_PENDING_ARCHIVE_REASON = "matching_verify_already_exists"


class WatcherTurnState(str, Enum):
    IDLE = "IDLE"
    IMPLEMENT_ACTIVE = "IMPLEMENT_ACTIVE"
    VERIFY_ACTIVE = "VERIFY_ACTIVE"
    VERIFY_FOLLOWUP = "VERIFY_FOLLOWUP"
    ADVISORY_ACTIVE = "ADVISORY_ACTIVE"
    OPERATOR_WAIT = "OPERATOR_WAIT"

    # Legacy enum aliases kept for a compatibility window. Callers may still
    # reference the old names, but persisted/runtime truth uses role-first
    # values above.
    CODEX_VERIFY = VERIFY_ACTIVE


def compute_file_sha256(path: Path) -> str:
    """파일 내용 기준 sha256 hex. 읽을 수 없으면 빈 문자열."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# ArtifactStabilizer
# ---------------------------------------------------------------------------
@dataclass
class StabilizeSnapshot:
    hash:  str
    size:  int
    mtime: float


class ArtifactStabilizer:
    """hash + mtime + size 3중 비교로 연속 N회 동일할 때만 안정화 완료 판정."""

    def __init__(self, settle_sec: float = 3.0, required_stable: int = 2) -> None:
        self.settle_sec      = settle_sec
        self.required_stable = required_stable
        self._snapshots: dict[str, list[StabilizeSnapshot]] = {}

    def _snapshot(self, path: Path) -> Optional[StabilizeSnapshot]:
        try:
            stat = path.stat()
            h    = hashlib.sha256(path.read_bytes()).hexdigest()
            return StabilizeSnapshot(hash=h, size=stat.st_size, mtime=stat.st_mtime)
        except OSError:
            return None

    def check(self, job_id: str, artifact_path: str) -> bool:
        path = Path(artifact_path)
        snap = self._snapshot(path)
        if snap is None:
            self._snapshots.pop(job_id, None)
            return False

        if time.time() - snap.mtime < self.settle_sec:
            self._snapshots.pop(job_id, None)
            return False

        history = self._snapshots.setdefault(job_id, [])

        # hash + size + mtime 3중 비교 — touch처럼 내용 동일 mtime 변경도 리셋
        if history and history[-1] != snap:
            self._snapshots[job_id] = []
            history = self._snapshots[job_id]

        history.append(snap)
        return len(history) >= self.required_stable

    def clear(self, job_id: str) -> None:
        self._snapshots.pop(job_id, None)


# ---------------------------------------------------------------------------
# PaneLease
# ---------------------------------------------------------------------------
@dataclass
class LeaseData:
    job_id:        str
    round:         int
    started_at:    float
    lease_ttl_sec: int
    pane_target:   str
    owner_pid:     int | None = None


@dataclass
class ControlSignal:
    kind:        str
    path:        Path
    status:      str
    mtime:       float
    sig:         str
    control_seq: int = -1
    slot_id:     str = ""
    canonical_file: str = ""
    is_legacy_alias: bool = False


class PaneLease:
    """slot별 lock 파일 기반 lease. dry_run 시 dispatch 직후 즉시 해제."""

    def __init__(
        self,
        lock_dir: Path,
        default_ttl: int = 900,
        dry_run: bool = False,
        owner_pid_path: Optional[Path] = None,
    ) -> None:
        self.lock_dir    = lock_dir
        self.default_ttl = default_ttl
        self.dry_run     = dry_run
        self.owner_pid_path = owner_pid_path
        lock_dir.mkdir(parents=True, exist_ok=True)

    def _lock_path(self, slot: str) -> Path:
        return self.lock_dir / f"{slot}.lock"

    def _read_owner_pid_state(self) -> tuple[int | None, float]:
        if self.owner_pid_path is None:
            return None, 0.0
        try:
            stat = self.owner_pid_path.stat()
            raw_pid = self.owner_pid_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return None, 0.0
        except OSError:
            return None, 0.0
        if not raw_pid:
            return None, stat.st_mtime
        try:
            pid = int(raw_pid)
        except ValueError:
            return None, stat.st_mtime
        if pid <= 0:
            return None, stat.st_mtime
        return pid, stat.st_mtime

    def _pid_dead(self, pid: int | None) -> bool:
        if pid is None or pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        except OSError:
            return False
        return False

    def _owner_dead(self) -> bool:
        # owner_pid_path가 wired되지 않은 경우: 감시할 supervisor가 없는 standalone 운영이
        # 가능하므로 "dead"로 판정하지 않는다.
        owner_pid, _ = self._read_owner_pid_state()
        if owner_pid is None:
            # pid 파일이 없거나 비어 있거나 손상된 경우는 dead가 아니라 판단 보류.
            return False
        return self._pid_dead(owner_pid)

    def _clear_lock(self, slot: str, *, reason: str) -> None:
        path = self._lock_path(slot)
        if not path.exists():
            return
        try:
            path.unlink()
        except OSError:
            return
        log.warning("lease released: slot=%s reason=%s", slot, reason)

    def _clear_if_owner_dead(self, slot: str) -> None:
        path = self._lock_path(slot)
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}

        owner_pid = data.get("owner_pid")
        if isinstance(owner_pid, int) and owner_pid > 0:
            if self._pid_dead(owner_pid):
                self._clear_lock(slot, reason="owner_dead")
            return

        # legacy lease에는 owner_pid가 없으므로, supervisor.pid가 lock보다 나중에
        # 다시 쓰였으면 restart 이후 stale lease로 보고 정리한다.
        _, owner_pid_mtime = self._read_owner_pid_state()
        started_at = 0.0
        try:
            started_at = float(data.get("started_at") or 0.0)
        except (TypeError, ValueError):
            started_at = 0.0
        if owner_pid_mtime > 0.0 and started_at > 0.0 and owner_pid_mtime > started_at:
            self._clear_lock(slot, reason="owner_restarted")
            return

        if self._owner_dead():
            self._clear_lock(slot, reason="owner_dead")

    def acquire(self, slot: str, job_id: str, round_: int,
                pane_target: str, ttl: Optional[int] = None) -> bool:
        path = self._lock_path(slot)
        self._clear_if_owner_dead(slot)
        if path.exists():
            try:
                data    = json.loads(path.read_text())
                elapsed = time.time() - data["started_at"]
                if elapsed < data["lease_ttl_sec"]:
                    log.debug("lease active: slot=%s job=%s elapsed=%.1fs",
                              slot, data["job_id"], elapsed)
                    return False
            except (json.JSONDecodeError, KeyError):
                pass

        lease = LeaseData(
            job_id=job_id, round=round_, started_at=time.time(),
            lease_ttl_sec=ttl or self.default_ttl, pane_target=pane_target,
            owner_pid=self._read_owner_pid_state()[0],
        )
        path.write_text(json.dumps(asdict(lease), ensure_ascii=False, indent=2))
        log.info("lease acquired: slot=%s job=%s round=%d pane=%s",
                 slot, job_id, round_, pane_target)
        return True

    def release(self, slot: str) -> None:
        path = self._lock_path(slot)
        if path.exists():
            path.unlink()
            log.info("lease released: slot=%s", slot)

    def is_active(self, slot: str) -> bool:
        path = self._lock_path(slot)
        self._clear_if_owner_dead(slot)
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text())
            return (time.time() - data["started_at"]) < data["lease_ttl_sec"]
        except (json.JSONDecodeError, KeyError):
            return False


# ---------------------------------------------------------------------------
# DedupeGuard
# ---------------------------------------------------------------------------
class DedupeGuard:
    """
    job_id + round + artifact_hash + target_slot 조합으로 중복 dispatch 억제.
    dispatch.jsonl / suppressed.jsonl 에 reason 포함 기록.
    로그 디렉터리: events_dir (experimental/)
    """

    def __init__(self, events_dir: Path) -> None:
        self.events_dir     = events_dir
        self.dispatch_log   = events_dir / "dispatch.jsonl"
        self.suppressed_log = events_dir / "suppressed.jsonl"
        self._seen: set[str] = set()
        self._load()

    def _load(self) -> None:
        if self.dispatch_log.exists():
            for line in self.dispatch_log.read_text().splitlines():
                try:
                    self._seen.add(json.loads(line)["key"])
                except (json.JSONDecodeError, KeyError):
                    pass

    @staticmethod
    def _make_key(job_id: str, round_: int, artifact_hash: str, target_slot: str) -> str:
        return f"{job_id}|{round_}|{artifact_hash}|{target_slot}"

    def is_duplicate(self, job_id: str, round_: int,
                     artifact_hash: str, target_slot: str) -> bool:
        return self._make_key(job_id, round_, artifact_hash, target_slot) in self._seen

    def mark_dispatch(self, job_id: str, round_: int, artifact_hash: str,
                      target_slot: str, pane_target: str, dry_run: bool) -> None:
        key = self._make_key(job_id, round_, artifact_hash, target_slot)
        self._seen.add(key)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": "dispatch", "key": key, "job_id": job_id,
            "round": round_, "artifact_hash": artifact_hash,
            "target_slot": target_slot, "pane_target": pane_target,
            "dry_run": dry_run, "at": time.time(),
        }
        with self.dispatch_log.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def mark_suppressed(self, job_id: str, round_: int, artifact_hash: str,
                        target_slot: str, reason: str) -> None:
        key = self._make_key(job_id, round_, artifact_hash, target_slot)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": "suppressed", "key": key, "job_id": job_id,
            "round": round_, "artifact_hash": artifact_hash,
            "target_slot": target_slot, "reason": reason, "at": time.time(),
        }
        with self.suppressed_log.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        log.info("suppressed: job=%s slot=%s reason=%s", job_id, target_slot, reason)

    def forget(self, job_id: str, round_: int, artifact_hash: str, target_slot: str) -> None:
        key = self._make_key(job_id, round_, artifact_hash, target_slot)
        self._seen.discard(key)


# ---------------------------------------------------------------------------
# ManifestCollector  (2단계 핵심)
# ---------------------------------------------------------------------------
class ManifestCollector:
    """
    verify pane이 저장한 manifest JSON을 폴링하고 유효성을 검증한다.

    manifest 경로: <manifests_dir>/<job_id>/round-<n>.verify.json

    유효 조건 (4중 일치):
      1. job_id 일치
      2. round 일치
      3. role == "slot_verify"
      4. artifact_hash == 현재 라운드 아티팩트 hash

    jsonschema 미설치 시: 필수 필드 존재 여부만 확인 (구조 검증으로 대체)
    """

    REQUIRED_FIELDS = {"schema_version", "job_id", "round", "role", "artifact_hash", "created_at"}

    def __init__(self, manifests_dir: Path, schema_path: Optional[Path] = None) -> None:
        self.manifests_dir = manifests_dir
        self._schema: Optional[dict] = None
        if schema_path and schema_path.exists():
            try:
                self._schema = json.loads(schema_path.read_text())
                log.info("manifest schema loaded: %s  jsonschema=%s",
                         schema_path, _JSONSCHEMA_AVAILABLE)
            except (json.JSONDecodeError, OSError) as e:
                log.warning("schema load failed: %s", e)

    def manifest_path(self, job_id: str, round_: int) -> Path:
        return self.manifests_dir / job_id / f"round-{round_}.verify.json"

    def poll(self, job: JobState) -> Optional[dict]:
        """
        manifest 파일이 존재하면 읽어서 반환.
        없으면 None.
        """
        path = self.manifest_path(job.job_id, job.round)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            log.warning("manifest read error: job=%s path=%s err=%s", job.job_id, path, e)
            return None

    def validate(self, manifest: dict, job: JobState) -> tuple[bool, str]:
        """
        (valid: bool, reason: str) 반환.

        검증 순서:
          1. jsonschema (설치된 경우) 또는 필수 필드 구조 검증
          2. 4중 일치 확인
        """
        # --- 스키마 검증 ---
        if _JSONSCHEMA_AVAILABLE and self._schema:
            try:
                _jsonschema.validate(instance=manifest, schema=self._schema)
            except _jsonschema.ValidationError as e:
                return False, f"schema_error: {e.message}"
        else:
            # jsonschema 미설치 fallback: 필수 필드 존재 + 최소 값 검증
            missing = [k for k in self.REQUIRED_FIELDS if k not in manifest]
            if missing:
                return False, f"missing_fields: {sorted(missing)}"
            if manifest.get("schema_version") != 1:
                return False, f"schema_version_invalid: {manifest.get('schema_version')}"
            if manifest.get("role") not in {"slot_gen", "slot_verify", "slot_counter"}:
                return False, f"role_invalid: {manifest.get('role')}"

        # --- 4중 일치 ---
        if manifest.get("job_id") != job.job_id:
            return False, f"job_id_mismatch: {manifest.get('job_id')} != {job.job_id}"
        if manifest.get("round") != job.round:
            return False, f"round_mismatch: {manifest.get('round')} != {job.round}"
        if manifest.get("role") != "slot_verify":
            return False, f"role_mismatch: {manifest.get('role')}"
        if manifest.get("artifact_hash") != job.artifact_hash:
            return False, (f"hash_mismatch: manifest={manifest.get('artifact_hash')[:16]}… "
                           f"job={job.artifact_hash[:16]}…")

        return True, "ok"

    def extract_scores(self, manifest: dict) -> dict:
        """
        JobState 업데이트에 필요한 정량 필드 추출.
        없는 필드는 안전 기본값으로 채운다.
        """
        required_checks = manifest.get("required_checks", 0)
        passed_checks   = manifest.get("passed_checks", 0)
        validation_score = (
            passed_checks / required_checks if required_checks > 0 else 0.0
        )

        blockers     = manifest.get("blockers", [])
        blocker_count = sum(1 for b in blockers if b.get("severity") == "critical")

        return {
            "validation_score": round(validation_score, 4),
            "blocker_count":    blocker_count,
        }


# ---------------------------------------------------------------------------
# tmux 전송 헬퍼
# ---------------------------------------------------------------------------
def _capture_pane_text(pane_target: str) -> str:
    return _shared_capture_pane_text(pane_target)


def wait_for_pane_settle(
    pane_target: str,
    timeout_sec: float = 12.0,
    quiet_sec: float = 1.0,
    poll_sec: float = 0.25,
) -> bool:
    """
    pane 출력이 잠잠해질 때까지 기다린다.
    fresh CLI lane에서 startup 로그나 MCP 초기화 출력이 계속 나오는 동안
    첫 handoff를 보내면 텍스트만 남고 submit이 누락될 수 있다.
    """
    return _shared_wait_for_pane_settle(
        pane_target,
        timeout_sec=timeout_sec,
        quiet_sec=quiet_sec,
        poll_sec=poll_sec,
    )


def _line_looks_like_input_prompt(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return (
        stripped == ">"
        or stripped == "›"
        or stripped == "❯"
        or stripped.startswith("> ")
        or stripped.startswith("› ")
        or stripped.startswith("❯ ")
        or stripped.endswith("$")
    )


def _pane_text_has_gemini_ready_prompt(text: str) -> bool:
    recent_lines = [line.strip().lower() for line in text.splitlines() if line.strip()]
    if not recent_lines:
        return False
    window = recent_lines[-12:]
    has_type_your_message = any(
        line == "type your message"
        or line.startswith("type your message ")
        or "type your message" in line
        for line in window
    )
    has_workspace_hint = any(line == "workspace" or line.startswith("workspace ") for line in window)
    has_gemini_banner = any("gemini cli" in line for line in window)
    return has_type_your_message and (has_workspace_hint or has_gemini_banner)


def _pane_text_has_busy_indicator(text: str) -> bool:
    return _shared_pane_text_has_busy_indicator(text)


def _pane_text_has_input_cursor(text: str) -> bool:
    return _shared_pane_text_has_input_cursor(text)


def _pane_has_input_cursor(pane_target: str) -> bool:
    """Check if the pane shows an input prompt in the recent visible lines."""
    text = _capture_pane_text(pane_target)
    return _pane_text_has_input_cursor(text)


def _pane_has_working_indicator(pane_target: str) -> bool:
    """Check whether the recent pane output shows Codex has started working."""
    text = _capture_pane_text(pane_target)
    return _shared_pane_text_has_working_indicator(text)


def _pane_text_is_idle(text: str) -> bool:
    """Treat a pane as idle only when a prompt is visible and no busy signal remains."""
    return _shared_pane_text_is_idle(text)


def _pane_text_has_codex_activity(text: str) -> bool:
    """Detect Codex response activity even when the input prompt remains visible."""
    return _shared_pane_text_has_codex_activity(text)


def _pane_text_has_gemini_activity(text: str) -> bool:
    """Detect Gemini response/tool activity even when the input prompt remains visible."""
    return _shared_pane_text_has_gemini_activity(text)


_LIVE_SESSION_ESCALATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "context_exhaustion",
        re.compile(
            r"context window|context exhausted|window nearly full|maximum context|conversation too long|컨텍스트\s*window|컨텍스트.*가득",
            re.IGNORECASE,
        ),
    ),
    (
        "session_rollover",
        re.compile(
            r"new session recommended|session rollover|start a new session|fresh session|new thread|새 세션|새로.*세션",
            re.IGNORECASE,
        ),
    ),
    (
        "continue_vs_switch",
        re.compile(
            r"continue\?|should i continue|continue here|handoff and continue|진행할까요|이어가시는 것을 강하게 권고|이어서 진행",
            re.IGNORECASE,
        ),
    ),
)

_LIVE_SESSION_ESCALATION_FALLBACK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "context_exhaustion": (
        "context", "window", "full", "exhaust", "too long", "maximum context",
        "token", "limit", "컨텍스트", "가득", "소진", "길어",
    ),
    "session_rollover": (
        "new session", "fresh session", "new thread", "start over", "restart session",
        "open a new", "새 세션", "새로", "다음 세션", "새 thread",
    ),
    "continue_vs_switch": (
        "continue", "keep going", "handoff", "switch", "continue here",
        "진행", "이어서", "계속", "이어갈", "이어가",
    ),
}

_IMPLEMENT_BLOCKED_STATUS_RE = re.compile(r"^\s*(?:[-*•]\s+)?STATUS:\s*(.*?)\s*$", re.IGNORECASE)
_IMPLEMENT_BLOCKED_FIELD_RE = re.compile(r"^\s*(?:[-*•]\s+)?([A-Z_]+):\s*(.*?)\s*$")
_IMPLEMENT_BLOCKED_WRAP_KEYS = {"BLOCK_REASON", "HANDOFF", "HANDOFF_SHA", "BLOCK_ID"}
_IMPLEMENT_BLOCKED_TEMPLATE_MARKERS = (
    "blocked_sentinel:",
    "emit the exact sentinel below",
)
_IMPLEMENT_ALREADY_DONE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\balready completed\b", re.IGNORECASE),
    re.compile(r"\balready addressed\b", re.IGNORECASE),
    re.compile(r"\bthe work described in the handoff was already completed\b", re.IGNORECASE),
    re.compile(r"\bthe handoff was already completed\b", re.IGNORECASE),
    re.compile(r"핸드오프.*이미.*완료", re.IGNORECASE),
    re.compile(r"슬라이스.*이미.*완료", re.IGNORECASE),
    re.compile(r"이미 완료된 상태", re.IGNORECASE),
)
_IMPLEMENT_NO_CHANGE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bno uncommitted changes\b", re.IGNORECASE),
    re.compile(r"\bno remaining\b", re.IGNORECASE),
    re.compile(r"\bno generic instances remain\b", re.IGNORECASE),
    re.compile(r"추가로 변경할 파일이 없", re.IGNORECASE),
    re.compile(r"변경할 파일이 없", re.IGNORECASE),
    re.compile(r"잔존 없음", re.IGNORECASE),
)
_IMPLEMENT_FORBIDDEN_MENU_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"다음\s+중\s+하나를\s+선택", re.IGNORECASE),
    re.compile(r"choose one of the following", re.IGNORECASE),
    re.compile(r"which option should i", re.IGNORECASE),
    re.compile(r"select (?:one|an option)", re.IGNORECASE),
    re.compile(r"operator.*choose", re.IGNORECASE),
)
_HANDOFF_MARKDOWN_BULLET_LITERAL_RE = re.compile(r"^\s*-\s+`(.*)`\s*$")
_MATERIALIZED_BLOCK_REASON_CODES = {
    "already_implemented",
    "duplicate_handoff",
    "handoff_already_applied",
}
_MATERIALIZED_BLOCK_REASONS = {
    "handoff_already_completed",
    "slice_already_materialized",
}


def _normalize_escalation_line(line: str) -> str:
    normalized = line.strip().lower()
    normalized = re.sub(r"\d+[hmsp초분시간]+", "#", normalized)
    normalized = re.sub(r"\d+", "#", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _match_implement_blocked_status(
    recent_lines: list[str],
    idx: int,
) -> tuple[bool, int, list[str]]:
    line = recent_lines[idx]
    match = _IMPLEMENT_BLOCKED_STATUS_RE.match(line)
    if not match:
        return False, idx, []
    value = match.group(1).strip().lower()
    if value == "implement_blocked":
        return True, idx + 1, [f"STATUS: {value}"]
    if value:
        return False, idx, []
    if idx + 1 >= len(recent_lines):
        return False, idx, []
    next_line = recent_lines[idx + 1].strip().lower()
    if next_line != "implement_blocked":
        return False, idx, []
    return True, idx + 2, ["STATUS: implement_blocked"]


def _can_append_implement_blocked_wrap(key: str, stripped: str) -> bool:
    if not stripped or _line_looks_like_input_prompt(stripped):
        return False
    if key == "BLOCK_REASON":
        return True
    if key == "HANDOFF":
        return True
    if key == "HANDOFF_SHA":
        return bool(re.fullmatch(r"[0-9a-fA-F]+", stripped))
    if key == "BLOCK_ID":
        return bool(re.fullmatch(r"[0-9A-Za-z._:/-]+", stripped))
    return False


def _decode_handoff_markdown_literal(line: str) -> str:
    match = _HANDOFF_MARKDOWN_BULLET_LITERAL_RE.match(line)
    if not match:
        return ""
    return match.group(1).replace("\\`", "`").strip()


@dataclass(frozen=True)
class _HandoffSentenceReplacementTarget:
    path: str
    current_sentence: str
    replacement_sentence: str


def _parse_handoff_sentence_replacement_target(
    handoff_text: str,
) -> Optional[_HandoffSentenceReplacementTarget]:
    target_path = ""
    current_sentence = ""
    replacement_sentence = ""
    capture_mode = ""
    for raw_line in handoff_text.splitlines():
        line = raw_line.strip()
        if line == "EDIT EXACTLY ONE FILE:":
            capture_mode = "path"
            continue
        if line.startswith("CURRENT SENTENCE TO REPLACE"):
            capture_mode = "current"
            continue
        if line.startswith("REPLACEMENT SENTENCE"):
            capture_mode = "replacement"
            continue
        if not line.startswith("- "):
            continue
        literal = _decode_handoff_markdown_literal(line)
        if not literal:
            continue
        if capture_mode == "path" and not target_path:
            target_path = literal
        elif capture_mode == "current" and not current_sentence:
            current_sentence = literal
        elif capture_mode == "replacement" and not replacement_sentence:
            replacement_sentence = literal
        capture_mode = ""
        if target_path and current_sentence and replacement_sentence:
            return _HandoffSentenceReplacementTarget(
                path=target_path,
                current_sentence=current_sentence,
                replacement_sentence=replacement_sentence,
            )
    if not target_path or not current_sentence or not replacement_sentence:
        return None
    return _HandoffSentenceReplacementTarget(
        path=target_path,
        current_sentence=current_sentence,
        replacement_sentence=replacement_sentence,
    )


def _fallback_escalation_reasons(lines: list[str]) -> list[str]:
    window_text = " ".join(_normalize_escalation_line(line) for line in lines)
    matched: list[str] = []
    for reason, keywords in _LIVE_SESSION_ESCALATION_FALLBACK_KEYWORDS.items():
        if any(keyword in window_text for keyword in keywords):
            matched.append(reason)
    if len(matched) < 2:
        return []
    if "continue_vs_switch" in matched and any(
        reason in matched for reason in ("context_exhaustion", "session_rollover")
    ):
        return matched
    if {"context_exhaustion", "session_rollover"}.issubset(matched):
        return matched
    return []


def _extract_live_session_escalation(text: str) -> Optional[dict[str, object]]:
    """Return a normalized live-session escalation signal from pane text."""
    if not text.strip():
        return None

    recent_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not recent_lines:
        return None
    recent_lines = recent_lines[-60:]
    hot_window = recent_lines[-12:]

    matched_reasons: list[str] = []
    excerpt_lines: list[str] = []
    matched_in_hot_window = False
    for line in recent_lines:
        matched_here = False
        for reason, pattern in _LIVE_SESSION_ESCALATION_PATTERNS:
            if pattern.search(line):
                matched_here = True
                if reason not in matched_reasons:
                    matched_reasons.append(reason)
        if matched_here:
            excerpt_lines.append(line)
            if line in hot_window:
                matched_in_hot_window = True

    if not matched_reasons:
        fallback_reasons = _fallback_escalation_reasons(hot_window)
        if fallback_reasons:
            matched_reasons = fallback_reasons
            excerpt_lines = hot_window[-8:]
            matched_in_hot_window = True

    if not matched_reasons or not matched_in_hot_window:
        return None

    normalized_excerpt = [_normalize_escalation_line(line) for line in excerpt_lines[:8]]
    fingerprint_source = "|".join(matched_reasons + normalized_excerpt)
    fingerprint = hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest()
    return {
        "reasons": matched_reasons,
        "excerpt_lines": excerpt_lines[:8],
        "fingerprint": fingerprint,
    }


def _normalize_control_path_hint(path_hint: str) -> str:
    return path_hint.strip().lstrip("./").replace("\\", "/")


def _extract_implement_blocked_signal(
    text: str,
    active_handoff_path: str = "",
    active_handoff_sha: str = "",
) -> Optional[dict[str, object]]:
    """Return an explicit implement_blocked sentinel if present in recent implement-owner output."""
    if not text.strip():
        return None

    recent_lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not recent_lines:
        return None
    recent_lines = recent_lines[-80:]

    for idx in range(len(recent_lines) - 1, -1, -1):
        matched, field_start_idx, block_lines = _match_implement_blocked_status(recent_lines, idx)
        if not matched:
            continue

        template_context = "\n".join(line.strip().lower() for line in recent_lines[max(0, idx - 3):idx])
        if any(marker in template_context for marker in _IMPLEMENT_BLOCKED_TEMPLATE_MARKERS):
            continue

        fields: dict[str, str] = {}
        current_key = ""
        for line in recent_lines[field_start_idx: field_start_idx + 24]:
            stripped = line.strip()
            if _line_looks_like_input_prompt(stripped):
                break
            match = _IMPLEMENT_BLOCKED_FIELD_RE.match(line)
            if match:
                current_key = match.group(1).upper()
                fields[current_key] = match.group(2).strip()
                block_lines.append(f"{current_key}: {fields[current_key]}".rstrip())
                continue
            if (
                current_key in _IMPLEMENT_BLOCKED_WRAP_KEYS
                and _can_append_implement_blocked_wrap(current_key, stripped)
            ):
                prefix = fields.get(current_key, "")
                separator = " " if current_key == "BLOCK_REASON" and prefix else ""
                fields[current_key] = prefix + separator + stripped
                if block_lines:
                    block_lines[-1] = f"{current_key}: {fields[current_key]}".rstrip()
                continue
            if current_key == "BLOCK_ID":
                break
            if stripped:
                block_lines.append(stripped)

        request = normalize_verify_triage_escalation(fields.get("REQUEST", ""))
        escalation_class = fields.get("ESCALATION_CLASS", "").strip().lower()
        escalation_class = normalize_verify_triage_escalation(escalation_class)
        if request and not is_verify_triage_escalation(request):
            return None
        if escalation_class and not is_verify_triage_escalation(escalation_class):
            return None
        if escalation_class and request and escalation_class != request:
            return None
        request = escalation_class or request or VERIFY_TRIAGE_ESCALATION

        block_reason_code = normalize_reason_code(fields.get("BLOCK_REASON_CODE", ""))

        handoff_hint = fields.get("HANDOFF", "")
        if active_handoff_path and handoff_hint:
            if _normalize_control_path_hint(handoff_hint) != _normalize_control_path_hint(active_handoff_path):
                return None

        handoff_sig = fields.get("HANDOFF_SHA") or fields.get("HANDOFF_SIG") or ""
        if active_handoff_sha and handoff_sig and handoff_sig != active_handoff_sha:
            return None

        block_reason = fields.get("BLOCK_REASON", "implement_blocked").strip().lower() or "implement_blocked"
        if block_reason.startswith("<"):
            continue
        fingerprint_source = "|".join(
            [
                "sentinel",
                active_handoff_sha or handoff_sig,
                block_reason,
                "|".join(_normalize_escalation_line(line) for line in block_lines[:6]),
            ]
        )
        fingerprint = fields.get("BLOCK_ID", "").strip() or hashlib.sha1(
            fingerprint_source.encode("utf-8")
        ).hexdigest()
        if fingerprint.startswith("<") or "<short_reason" in fingerprint.lower():
            continue
        return {
            "source": "sentinel",
            "reason": block_reason,
            "reason_code": block_reason_code,
            "escalation_class": request,
            "request": request,
            "excerpt_lines": block_lines[:6],
            "fingerprint": fingerprint,
            "handoff_hint": handoff_hint,
        }
    return None


def _extract_implement_forbidden_menu_signal(text: str, active_handoff_sha: str = "") -> Optional[dict[str, object]]:
    """Detect forbidden operator-choice text in recent implement-owner output as a soft blocked signal."""
    if not text.strip():
        return None

    recent_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not recent_lines:
        return None
    hot_window = recent_lines[-16:]
    matched_lines = [
        line for line in hot_window
        if any(pattern.search(line) for pattern in _IMPLEMENT_FORBIDDEN_MENU_PATTERNS)
    ]
    if not matched_lines:
        return None

    fingerprint_source = "|".join(
        ["soft_blocked", active_handoff_sha, *(_normalize_escalation_line(line) for line in matched_lines[:6])]
    )
    return {
        "source": "soft_blocked",
        "reason": "forbidden_operator_menu",
        "reason_code": VERIFY_TRIAGE_ONLY_REASON,
        "escalation_class": VERIFY_TRIAGE_ESCALATION,
        "request": VERIFY_TRIAGE_ESCALATION,
        "excerpt_lines": matched_lines[:6],
        "fingerprint": hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest(),
        "handoff_hint": "",
    }


def _extract_implement_completed_handoff_signal(text: str, active_handoff_sha: str = "") -> Optional[dict[str, object]]:
    """Detect the implement owner saying the current handoff is already complete / no-op."""
    if not text.strip():
        return None

    recent_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not recent_lines:
        return None
    hot_window = recent_lines[-24:]
    done_lines = [
        line for line in hot_window
        if any(pattern.search(line) for pattern in _IMPLEMENT_ALREADY_DONE_PATTERNS)
    ]
    noop_lines = [
        line for line in hot_window
        if any(pattern.search(line) for pattern in _IMPLEMENT_NO_CHANGE_PATTERNS)
    ]
    if not done_lines:
        return None
    if not noop_lines and not any("handoff" in line.lower() for line in done_lines):
        return None

    excerpt_lines = (done_lines + noop_lines)[:6]
    fingerprint_source = "|".join(
        ["soft_completed", active_handoff_sha, *(_normalize_escalation_line(line) for line in excerpt_lines)]
    )
    return {
        "source": "soft_completed",
        "reason": "handoff_already_completed",
        "reason_code": "duplicate_handoff",
        "escalation_class": VERIFY_TRIAGE_ESCALATION,
        "request": VERIFY_TRIAGE_ESCALATION,
        "excerpt_lines": excerpt_lines,
        "fingerprint": hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest(),
        "handoff_hint": "",
    }


def _wait_for_input_ready(
    pane_target: str,
    timeout_sec: float = 30.0,
    poll_sec: float = 0.5,
    stable_sec: float = 2.0,
) -> bool:
    """
    Wait until the pane shows a stable input prompt.

    For fresh Codex startup, the prompt may briefly appear while MCP boot/logging is
    still settling. Requiring a short continuous ready window makes the first
    dispatch less likely to land during that unstable startup phase.
    """
    deadline = time.time() + timeout_sec
    ready_since: Optional[float] = None
    while time.time() < deadline:
        snapshot = _capture_pane_text(pane_target)
        if _pane_text_has_input_cursor(snapshot):
            if ready_since is None:
                ready_since = time.time()
            elif time.time() - ready_since >= stable_sec:
                return True
        else:
            ready_since = None
        time.sleep(poll_sec)
    return False


def _wait_for_dispatch_window(
    pane_target: str,
    pane_type: str,
    timeout_sec: float = 10.0,
) -> bool:
    """
    Dispatch 직전 pane이 실제 입력을 받을 준비가 됐는지 기다린다.
    MCP 문자열 기반 장기 대기 대신, 고정된 짧은 readiness 확인만 수행한다.
    """
    if _is_pane_dead(pane_target):
        _respawn_pane(pane_target)

    if not _wait_for_input_ready(
        pane_target,
        timeout_sec=timeout_sec,
        poll_sec=0.5,
        stable_sec=2.0,
    ):
        log.warning(
            "%s pane not ready for dispatch (timeout=%.1fs)",
            pane_type, timeout_sec,
        )
        return False

    wait_for_pane_settle(
        pane_target,
        timeout_sec=3.0,
        quiet_sec=0.75,
        poll_sec=0.25,
    )
    return True


# Prompt temp file cleanup list (cleaned at exit)
_prompt_cleanup_list: list[str] = []


def _cleanup_prompt_files() -> None:
    for path in _prompt_cleanup_list:
        try:
            os.unlink(path)
        except OSError:
            pass


atexit.register(_cleanup_prompt_files)


def _is_pane_dead(pane_target: str) -> bool:
    """Check if a tmux pane is in dead (exited) state."""
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-t", pane_target, "-p", "#{pane_dead}"],
            check=True, capture_output=True, text=True,
        )
        return result.stdout.strip() == "1"
    except subprocess.CalledProcessError:
        return True


def _respawn_pane(pane_target: str) -> None:
    """Respawn a dead tmux pane back to a bash shell."""
    log.info("respawning dead pane: %s", pane_target)
    subprocess.run(
        ["tmux", "respawn-pane", "-k", "-t", pane_target],
        check=False, capture_output=True,
    )
    time.sleep(1.0)


def _write_prompt_file(command: str) -> str:
    """Write prompt to a temp file. Registered for cleanup at exit."""
    fd = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="prompt-", delete=False, dir="/tmp",
    )
    fd.write(command)
    fd.close()
    _prompt_cleanup_list.append(fd.name)
    return fd.name


def _normalize_prompt_text(text: str) -> str:
    """Convert literal \\n sequences from shell-passed templates into real newlines."""
    return text.replace("\\n", "\n")


def _clear_prompt_input_line(pane_target: str) -> None:
    """Clear any stale unsent text before an automated dispatch."""
    subprocess.run(
        ["tmux", "send-keys", "-t", pane_target, "C-u"],
        check=True,
        capture_output=True,
    )
    time.sleep(0.1)


def _dispatch_lock_for(pane_target: str) -> threading.Lock:
    with _DISPATCH_LOCKS_GUARD:
        lock = _DISPATCH_LOCKS.get(pane_target)
        if lock is None:
            lock = threading.Lock()
            _DISPATCH_LOCKS[pane_target] = lock
        return lock


def tmux_send_keys(
    pane_target: str,
    command: str,
    dry_run: bool = False,
    pane_type: str = "claude",
) -> bool:
    """Send a prompt to a tmux pane.

    pane_type: "codex" — paste-buffer + Enter retry with working-indicator check
               "claude" — paste-buffer + Enter retry
               "gemini" — paste-buffer + Enter retry
    """
    log.info("send-keys target=%s pane_type=%s dry_run=%s", pane_target, pane_type, dry_run)
    if dry_run:
        return True
    dispatch_lock = _dispatch_lock_for(pane_target)
    if not dispatch_lock.acquire(timeout=_DISPATCH_LOCK_TIMEOUT_SEC):
        log.warning(
            "send-keys skipped: pane dispatch busy target=%s pane_type=%s",
            pane_target,
            pane_type,
        )
        return False
    try:
        if not _wait_for_dispatch_window(pane_target, pane_type):
            return False
        if pane_type == "codex":
            return _dispatch_codex(pane_target, command)
        if pane_type == "gemini":
            return _dispatch_gemini(pane_target, command)
        return _dispatch_claude(pane_target, command)
    except subprocess.CalledProcessError as e:
        log.error("send-keys failed: %s", e.stderr.decode().strip())
        return False
    finally:
        dispatch_lock.release()


def _dispatch_codex(pane_target: str, command: str) -> bool:
    """Dispatch to Codex pane.

    Codex interactive session is kept alive (started by start-pipeline.sh).
    Always paste-buffer into the running session — never re-launch codex.
    """
    log.info("dispatching codex prompt: chars=%d", len(command))
    _clear_prompt_input_line(pane_target)
    subprocess.run(["tmux", "set-buffer", command], check=True, capture_output=True)
    subprocess.run(["tmux", "paste-buffer", "-t", pane_target], check=True, capture_output=True)
    pasted_snapshot = _capture_pane_text(pane_target)
    time.sleep(1.0)
    for attempt in range(3):
        subprocess.run(["tmux", "send-keys", "-t", pane_target, "Enter"], check=True, capture_output=True)
        time.sleep(1.5)
        snapshot = _capture_pane_text(pane_target)
        if not _pane_text_has_input_cursor(snapshot):
            log.info("codex prompt consumed: attempt %d", attempt + 1)
            deadline = time.time() + 6.0
            while time.time() < deadline:
                if _pane_has_working_indicator(pane_target):
                    log.info("codex working indicator detected")
                    return True
                current_snapshot = _capture_pane_text(pane_target)
                if current_snapshot != snapshot and _pane_text_has_codex_activity(current_snapshot):
                    log.info("codex response activity detected after consume: attempt %d", attempt + 1)
                    return True
                time.sleep(0.5)
            log.info(
                "codex dispatch consumed without immediate confirmation: defer acceptance to wrapper events"
            )
            return True
        if snapshot != pasted_snapshot and _pane_text_has_codex_activity(snapshot):
            log.info("codex response activity detected: attempt %d", attempt + 1)
            return True
    log.info("codex prompt still visible or unconfirmed after retries")
    return False


def _dispatch_claude(pane_target: str, command: str) -> bool:
    """Dispatch to Claude pane via paste-buffer + Enter."""
    _clear_prompt_input_line(pane_target)
    subprocess.run(["tmux", "set-buffer", command], check=True, capture_output=True)
    subprocess.run(["tmux", "paste-buffer", "-t", pane_target], check=True, capture_output=True)
    pasted_snapshot = _capture_pane_text(pane_target)
    time.sleep(1.0)
    for attempt in range(3):
        subprocess.run(["tmux", "send-keys", "-t", pane_target, "Enter"], check=True, capture_output=True)
        time.sleep(1.5)
        snapshot = _capture_pane_text(pane_target)
        if not _pane_text_has_input_cursor(snapshot):
            log.info("claude prompt consumed: attempt %d", attempt + 1)
            return True
        if snapshot != pasted_snapshot:
            if _shared_text_matches_markers(snapshot, _shared_busy_markers_for_lane("Claude")):
                log.info("claude busy output detected after dispatch: attempt %d", attempt + 1)
                return True
            if _pane_text_is_idle(snapshot):
                log.info("claude ready output detected after dispatch: attempt %d", attempt + 1)
                return True
    log.info("claude prompt still visible or unconfirmed after retries")
    return False


def _dispatch_gemini(pane_target: str, command: str) -> bool:
    """Dispatch to Gemini pane via paste-buffer + Enter."""
    _clear_prompt_input_line(pane_target)
    subprocess.run(["tmux", "set-buffer", command], check=True, capture_output=True)
    subprocess.run(["tmux", "paste-buffer", "-t", pane_target], check=True, capture_output=True)
    pasted_snapshot = _capture_pane_text(pane_target)
    time.sleep(1.0)
    for attempt in range(3):
        subprocess.run(["tmux", "send-keys", "-t", pane_target, "Enter"], check=True, capture_output=True)
        time.sleep(1.5)
        snapshot = _capture_pane_text(pane_target)
        if not _pane_text_has_input_cursor(snapshot):
            log.info("gemini prompt consumed: attempt %d", attempt + 1)
            return True
        if snapshot != pasted_snapshot and _pane_text_has_gemini_activity(snapshot):
            log.info("gemini response activity detected: attempt %d", attempt + 1)
            return True
    log.info("gemini prompt still visible or unconfirmed after retries")
    return False


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
        self._last_seen_control_seq: int | None = None
        self._control_seq_age_cycles: int = 0
        self._last_operator_retriage_sig: str = ""
        self._last_operator_retriage_fingerprint: str = ""
        self._operator_retriage_started_at: float = 0.0
        self._last_operator_recovery_key: str = ""
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
        self.advisory_recovery_sec: float = float(config.get("advisory_recovery_sec", 900.0))
        self.operator_retriage_no_control_sec: float = float(
            config.get("operator_retriage_no_control_sec", 45.0)
        )
        self._last_advisory_retry_sig: str = ""
        self._last_advisory_retry_at: float = 0.0
        self._last_advisory_recovery_sig: str = ""
        self._last_advisory_recovery_at: float = 0.0
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
        self._runtime_event_seq: int = 0
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
        self.dispatch_queue = WatcherDispatchQueue(
            lane_input_defer_cooldown_sec=self._lane_input_defer_cooldown_sec,
            capture_pane_text=lambda target: _capture_pane_text(target),
            send_keys=lambda target, prompt, pane_type: tmux_send_keys(
                target, prompt, self.dry_run, pane_type=pane_type
            ),
            get_path_sig=self._get_path_sig,
            role_owner=self._prompt_owner,
            log_raw=self._log_raw,
            append_runtime_event=self._append_runtime_event,
            get_active_control_signal=self._get_active_control_signal,
            is_active_control=self._is_active_control,
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
                config.get("verify_done_deadline_sec", 45.0)
            ),
            runtime_started_at=self.started_at,
            restart_recovery_grace_sec=float(config.get("restart_recovery_grace_sec", 15.0)),
            completion_paths=self.completion_paths,
            error_log=self.events_dir / "errors.jsonl",
            capture_pane_text=lambda target: _capture_pane_text(target),
            pane_text_has_busy_indicator=lambda text: _pane_text_has_busy_indicator(text),
            pane_text_has_input_cursor=lambda text: _pane_text_has_input_cursor(text),
            pane_text_is_idle=lambda text: _pane_text_is_idle(text),
            normalize_prompt_text=self.prompt_assembler.finalize_prompt_text,
            send_keys=lambda target, prompt, dry_run, pane_type: tmux_send_keys(
                target,
                prompt,
                dry_run,
                pane_type=pane_type,
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
            self._write_runtime_status()

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
    def _archive_job_state_file(self, path: Path, *, source_run_id: str = "", reason: str) -> None:
        archive_dir = self._job_state_archive_dir(source_run_id)
        archive_dir.mkdir(parents=True, exist_ok=True)
        target = archive_dir / path.name
        if target.exists():
            target = archive_dir / f"{path.stem}-{int(time.time())}{path.suffix}"
        try:
            path.replace(target)
        except OSError as exc:
            log.warning("failed to archive stale job state: %s (%s)", path, exc)
            return
        log.info("archived stale job state: %s -> %s (%s)", path, target, reason)

    # ------------------------------------------------------------------
    def _archive_stale_job_states(self) -> None:
        if not self.state_dir.exists():
            return
        terminal_values = {status.value for status in TERMINAL_STATES}
        archived = 0
        legacy_cutoff = self.started_at - self.state_cleanup_legacy_grace_sec
        for path in iter_job_state_paths(self.state_dir):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            status = str(data.get("status") or "").strip()
            if status in terminal_values:
                continue
            state_run_id = str(data.get("run_id") or "").strip()
            if state_run_id:
                if state_run_id == self.run_id:
                    continue
                self._archive_job_state_file(
                    path,
                    source_run_id=state_run_id,
                    reason="previous_run_nonterminal",
                )
                archived += 1
                continue
            try:
                state_mtime = path.stat().st_mtime
            except OSError:
                state_mtime = 0.0
            updated_at = float(data.get("updated_at") or 0.0)
            if max(state_mtime, updated_at) >= legacy_cutoff:
                continue
            self._archive_job_state_file(
                path,
                reason="legacy_nonterminal_before_startup",
            )
            archived += 1
        if archived:
            log.info("archived %d stale job state files before startup", archived)

    # ------------------------------------------------------------------
    @staticmethod
    def _iso_utc(ts: float) -> str:
        return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat().replace("+00:00", "Z")

    # ------------------------------------------------------------------
    def _write_current_run_pointer(self) -> None:
        if not self._runtime_export_enabled:
            return
        # watcher가 자기 process identity(`watcher_pid` + `watcher_fingerprint`)를
        # current_run.json에 같이 남겨야, supervisor 재시작 inheritance가 watcher가
        # 직접 쓴 pointer를 보고도 같은 owner-match 계약 아래에서 prior run_id를
        # 이어받을 수 있다. 이 두 필드가 빠지면 supervisor가 fresh run_id로 fall
        # through 하면서 canonical runtime surface가 다시 어긋난다.
        watcher_pid = os.getpid()
        watcher_fingerprint = process_starttime_fingerprint(watcher_pid)
        data = {
            "run_id": self.run_id,
            "status_path": self._repo_relative(self.run_status_path),
            "events_path": self._repo_relative(self.run_events_path),
            "watcher_pid": watcher_pid,
            "watcher_fingerprint": watcher_fingerprint,
            "updated_at": self._iso_utc(time.time()),
        }
        tmp_path = self.current_run_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp_path.replace(self.current_run_path)

    # ------------------------------------------------------------------
    def _append_runtime_event(self, event_type: str, payload: dict[str, object]) -> None:
        if not self._runtime_export_enabled:
            return
        self._runtime_event_seq += 1
        entry = {
            "seq": self._runtime_event_seq,
            "ts": self._iso_utc(time.time()),
            "run_id": self.run_id,
            "event_type": event_type,
            "source": "watcher-exporter",
            "payload": payload,
        }
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with self.run_events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

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
        pane_text = _capture_pane_text(implement_target)
        if not pane_text.strip():
            return False
        return not _pane_text_is_idle(pane_text)

    # ------------------------------------------------------------------
    def _build_lane_statuses(self, heartbeat_iso: str) -> list[dict[str, object]]:
        lane_statuses: list[dict[str, object]] = []
        active_lane = self._active_lane_name_for_turn()
        active_control = self._get_active_control_signal()
        implement_lane = self._prompt_owner("implement") or ""
        implement_live = self._implement_control_should_surface_working(active_control)
        seen_names: set[str] = set()
        lane_configs = self.runtime_lane_configs or _default_runtime_lane_configs()
        for lane in lane_configs:
            name = str(lane.get("name") or "").strip()
            if not name:
                continue
            seen_names.add(name)
            enabled = bool(lane.get("enabled", True))
            state = "OFF"
            if enabled:
                state = "WORKING" if name == active_lane or (implement_live and name == implement_lane) else "READY"
            lane_statuses.append(
                {
                    "name": name,
                    "state": state,
                    "attachable": enabled,
                    "last_heartbeat_at": heartbeat_iso if enabled else "",
                }
            )
        for fallback_name in physical_lane_order():
            if fallback_name in seen_names:
                continue
            lane_statuses.append(
                {
                    "name": fallback_name,
                    "state": (
                        "WORKING"
                        if fallback_name == active_lane or (implement_live and fallback_name == implement_lane)
                        else "READY"
                    ),
                    "attachable": True,
                    "last_heartbeat_at": heartbeat_iso,
                }
            )
        return lane_statuses

    # ------------------------------------------------------------------
    def _write_runtime_status(self) -> None:
        if not self._runtime_export_enabled:
            return
        now = time.time()
        now_iso = self._iso_utc(now)
        active_control = self._get_active_control_signal()
        control_snapshot = {}
        control_is_legacy_alias = False
        if active_control is not None:
            control_snapshot = active_control_snapshot_from_entry(
                {
                    "file": active_control.path.name,
                    "control_seq": active_control.control_seq,
                    "status": active_control.status,
                    "mtime": active_control.mtime,
                    "slot_id": active_control.slot_id,
                    "canonical_file": active_control.canonical_file,
                }
            )
            control_is_legacy_alias = active_control.is_legacy_alias
        elif self._turn_active_control_file:
            control_snapshot = active_control_snapshot_from_status(
                {
                    "active_control_file": f".pipeline/{self._turn_active_control_file}",
                    "active_control_seq": self._turn_active_control_seq,
                }
            )
        data = {
            "schema_version": 1,
            "run_id": self.run_id,
            "state": "RUNNING",
            "runtime_state": "RUNNING",
            "turn_state": self._current_turn_state.value,
            "legacy_turn_state": legacy_turn_state_name(self._current_turn_state.value),
            "degraded_reason": "",
            "control": control_block_from_snapshot(
                control_snapshot,
                control_age_cycles=self._control_seq_age_cycles,
                is_legacy_alias=control_is_legacy_alias,
            ),
            "control_age_cycles": self._control_seq_age_cycles,
            "lanes": self._build_lane_statuses(now_iso),
            "last_receipt_id": "",
            "last_heartbeat_at": now_iso,
            "updated_at": now_iso,
        }
        data.update(derive_automation_health(data))
        tmp_path = self.run_status_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp_path.replace(self.run_status_path)
        self._write_current_run_pointer()

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
        self._write_runtime_status()

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
    def _control_signal_from_entry(self, entry: dict[str, object]) -> Optional[ControlSignal]:
        slot_id = str(entry.get("slot_id") or "").strip()
        if slot_id in {"advisory_request", "advisory_advice"} and not self._advisory_enabled():
            return None
        if slot_id == "operator_request" and not self._operator_stop_enabled():
            return None
        filename = str(entry.get("file") or "").strip()
        status = str(entry.get("status") or "").strip()
        if not filename or not status:
            return None
        path = self.pipeline_dir / filename
        try:
            mtime = float(entry.get("mtime") or 0.0)
        except (TypeError, ValueError):
            mtime = 0.0
        if mtime == 0.0:
            return None
        control_seq = control_seq_value(entry.get("control_seq"), default=-1)
        return ControlSignal(
            kind=slot_id or filename,
            path=path,
            status=status,
            mtime=mtime,
            sig=self._get_path_sig(path),
            control_seq=control_seq,
            slot_id=slot_id,
            canonical_file=str(entry.get("canonical_file") or filename),
            is_legacy_alias=bool(entry.get("is_legacy_alias")),
        )

    # ------------------------------------------------------------------
    def _iter_valid_control_signals(self, *, include_advisory_advice: bool = True) -> list[ControlSignal]:
        snapshot = read_pipeline_control_snapshot(self.pipeline_dir)
        entries: list[dict[str, object]] = []
        active_entry = snapshot.get("active_entry")
        if isinstance(active_entry, dict):
            entries.append(active_entry)
        entries.extend(
            entry
            for entry in list(snapshot.get("stale_entries") or [])
            if isinstance(entry, dict)
        )
        candidates: list[ControlSignal] = []
        for entry in entries:
            if not include_advisory_advice and str(entry.get("slot_id") or "") == "advisory_advice":
                continue
            signal = self._control_signal_from_entry(entry)
            if signal is not None:
                candidates.append(signal)
        return candidates

    def _newest_control_signal(self, signals: list[ControlSignal]) -> Optional[ControlSignal]:
        if not signals:
            return None
        return signals[0]

    def _control_signal_matches(self, signal: Optional[ControlSignal], path: Path, expected_status: str) -> bool:
        if signal is None or signal.status != expected_status:
            return False
        if signal.path == path:
            return True
        return control_filenames_equivalent(signal.path.name, path.name)

    def _control_signal_for_slot(
        self,
        signal: Optional[ControlSignal],
        slot_id: str,
        expected_status: str,
    ) -> Optional[ControlSignal]:
        if signal is None or signal.status != expected_status:
            return None
        if signal.slot_id == slot_id:
            return signal
        spec = control_slot_spec_for_filename(signal.path.name)
        if spec is not None and spec.slot_id == slot_id:
            return signal
        return None

    def _newest_control_signal_for_slot(self, slot_id: str, expected_status: str) -> Optional[ControlSignal]:
        signals = [
            signal
            for signal in self._iter_valid_control_signals()
            if signal.slot_id == slot_id and signal.status == expected_status
        ]
        return self._newest_control_signal(signals)

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
        candidates = self._iter_valid_control_signals()
        seqs = [candidate.control_seq for candidate in candidates if candidate is not None and candidate.control_seq >= 0]
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
        return evaluate_stale_operator_control(
            control_text=control_text,
            control_meta=control_meta,
            verified_work_paths=self._verified_work_paths(),
            completed_pr_numbers=pr_merge_resolution.completed_pr_numbers,
            mismatched_pr_numbers=pr_merge_resolution.head_mismatch_pr_numbers,
            control_file="operator_request.md",
            control_seq=self._read_control_seq_from_path(self.operator_request_path),
            normalize_path=self._normalize_artifact_path,
        )

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
        decision = classify_operator_candidate(
            control_text,
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
        return operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=control_seq,
        )

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
        fingerprint = str(marker.get("fingerprint") or "")
        if (
            fingerprint
            and fingerprint == self._last_operator_retriage_fingerprint
            and self._operator_retriage_started_at > 0.0
        ):
            self._last_operator_retriage_sig = operator_sig
            return
        self._last_operator_retriage_sig = operator_sig
        self._last_operator_retriage_fingerprint = fingerprint
        self._operator_retriage_started_at = time.time()

    # ------------------------------------------------------------------
    def _operator_retriage_is_same_semantic_bump(self, marker: dict[str, object]) -> bool:
        fingerprint = str(marker.get("fingerprint") or "")
        return (
            self._current_turn_state == WatcherTurnState.VERIFY_FOLLOWUP
            and bool(fingerprint)
            and fingerprint == self._last_operator_retriage_fingerprint
            and self._operator_retriage_started_at > 0.0
        )

    # ------------------------------------------------------------------
    def _idle_operator_retriage_marker(self) -> Optional[dict[str, object]]:
        if not self._is_active_control(self.operator_request_path, "needs_operator"):
            return None
        control_mtime = self._get_path_mtime(self.operator_request_path)
        if control_mtime <= 0:
            return None
        age_sec = max(0.0, time.time() - control_mtime)
        if age_sec < self.operator_wait_retriage_sec:
            return None
        return {
            "control_file": "operator_request.md",
            "control_seq": self._read_control_seq_from_path(self.operator_request_path),
            "reason": "operator_wait_idle_retriage",
            "resolved_work_paths": [],
            "operator_wait_age_sec": int(age_sec),
        }

    # ------------------------------------------------------------------
    def _operator_control_recovery_marker(self) -> Optional[dict[str, object]]:
        satisfied = self._satisfied_operator_approval_marker()
        if satisfied is not None:
            return satisfied
        stale = self._stale_operator_control_marker()
        if stale is not None:
            return stale
        return self._idle_operator_retriage_marker()

    # ------------------------------------------------------------------
    def _operator_recovery_without_idle_marker(self) -> Optional[dict[str, object]]:
        satisfied = self._satisfied_operator_approval_marker()
        if satisfied is not None:
            return satisfied
        return self._stale_operator_control_marker()

    # ------------------------------------------------------------------
    def _operator_recovery_key(self, operator_sig: str, marker: dict[str, object]) -> str:
        resolved_work = ",".join(str(item) for item in list(marker.get("resolved_work_paths") or []))
        resolved_prs = ",".join(str(item) for item in list(marker.get("resolved_pr_numbers") or []))
        return "|".join(
            [
                operator_sig,
                str(marker.get("control_seq") or ""),
                str(marker.get("reason") or ""),
                resolved_work,
                resolved_prs,
            ]
        )

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
        recovery_reason = str(marker.get("reason") or "verified_blockers_resolved")
        control_seq = control_seq_value(marker.get("control_seq"), default=-1)
        recovery_key = self._operator_recovery_key(operator_sig, marker)
        if (
            recovery_key
            and recovery_key == self._last_operator_recovery_key
            and self._current_turn_state == WatcherTurnState.VERIFY_FOLLOWUP
            and control_seq == self._turn_active_control_seq
        ):
            return True
        self._last_operator_recovery_key = recovery_key
        if operator_sig:
            self._last_operator_request_sig = operator_sig
        log.info("operator request recoverable without operator action: verify follow-up resumes (%s)", recovery_reason)
        self._clear_implement_blocked_state(recovery_reason)
        self._transition_turn(
            WatcherTurnState.VERIFY_FOLLOWUP,
            recovery_reason,
            active_control_file=operator_path.name,
            active_control_seq=control_seq,
        )
        if recovery_reason == "operator_wait_idle_retriage":
            self._mark_operator_retriage_started(operator_sig, marker)
        recovery_event = self._record_operator_recovery_marker(
            recovery_reason=recovery_reason,
            status=status,
            marker=marker,
            source=source,
        )
        if recovery_reason == "operator_wait_idle_retriage":
            self._notify_verify_operator_retriage(recovery_reason, marker)
        else:
            self._notify_verify_control_recovery(recovery_event, marker)
        return True

    # ------------------------------------------------------------------
    def _check_operator_recovery_without_signal(self) -> bool:
        active_control = self._get_active_control_signal()
        operator_control = self._control_signal_for_slot(
            active_control,
            "operator_request",
            "needs_operator",
        )
        if operator_control is None:
            return False
        if operator_control.control_seq < self._turn_active_control_seq:
            return False
        marker = self._operator_recovery_without_idle_marker()
        if marker is None:
            return False
        operator_sig = operator_control.sig or self._get_path_sig(operator_control.path)
        status = self._read_status_from_path(operator_control.path) or "missing"
        return self._route_operator_recovery(
            operator_sig=operator_sig,
            operator_path=operator_control.path,
            status=status,
            marker=marker,
            source="turn_signal",
        )

    # ------------------------------------------------------------------
    def _path_mention(self, path: Optional[Path]) -> str:
        if path is None:
            return "(없음)"
        return f"@{self._repo_relative(path)}"

    # ------------------------------------------------------------------
    def _find_latest_md(self, root: Path) -> Optional[Path]:
        latest_path: Optional[Path] = None
        latest_mtime = 0.0
        if not root.exists():
            return None
        for md in root.rglob("*.md"):
            if root == self.watch_dir:
                if not self._is_dispatchable_work_note(md):
                    continue
            elif not self._is_canonical_round_note(root, md):
                continue
            try:
                mt = md.stat().st_mtime
            except OSError:
                continue
            if mt >= latest_mtime:
                latest_path = md
                latest_mtime = mt
        return latest_path

    # ------------------------------------------------------------------
    def _get_latest_work_path(self) -> Optional[Path]:
        return self._find_latest_md(self.watch_dir)

    # ------------------------------------------------------------------
    def _get_latest_work_path_broad(self) -> Optional[Path]:
        return self._find_latest_md_broad(self.watch_dir)

    # ------------------------------------------------------------------
    def _is_canonical_round_note(self, root: Path, path: Path) -> bool:
        try:
            rel = path.relative_to(root)
        except ValueError:
            return False
        min_depth = 3
        for base in (self.watch_dir, self.verify_dir):
            try:
                base_rel = root.relative_to(base)
            except ValueError:
                continue
            # top-level work/verify roots expect month/day/file (=3),
            # but same-day subdirs like verify/4/17 only need the file itself.
            min_depth = max(1, 3 - len(base_rel.parts))
            break
        if len(rel.parts) < min_depth:
            return False
        return bool(ROUND_NOTE_NAME_RE.match(path.name))

    # ------------------------------------------------------------------
    def _is_metadata_only_work_note(self, work_path: Path) -> bool:
        if not self._is_canonical_round_note(self.watch_dir, work_path):
            return False
        changed_paths = [path.lstrip("./") for path in self._extract_changed_file_paths_from_round_note(work_path)]
        if not changed_paths:
            # "변경 파일" 섹션이 비었거나 "- 없음"만 있으면 메타 문서로 취급
            return True
        work_rel = self._repo_relative(work_path)
        return all(
            path == work_rel or path.startswith(ROUND_NOTE_METADATA_ONLY_PREFIXES)
            for path in changed_paths
        )

    # ------------------------------------------------------------------
    def _is_dispatchable_work_note(self, work_path: Path) -> bool:
        return (
            self._is_canonical_round_note(self.watch_dir, work_path)
            and not self._is_metadata_only_work_note(work_path)
        )

    # ------------------------------------------------------------------
    def _get_latest_same_day_verify_path(self, work_path: Optional[Path]) -> Optional[Path]:
        if work_path is None:
            return self._find_latest_md(self.verify_dir)

        try:
            rel = work_path.relative_to(self.watch_dir)
        except ValueError:
            return self._find_latest_md(self.verify_dir)

        if len(rel.parts) >= 2:
            same_day_dir = self.verify_dir / rel.parts[0] / rel.parts[1]
            latest_same_day = self._find_latest_md(same_day_dir)
            if latest_same_day is not None:
                return latest_same_day

        return self._find_latest_md(self.verify_dir)

    # ------------------------------------------------------------------
    def _get_latest_same_day_verify_path_for_work(self, work_path: Optional[Path]) -> Optional[Path]:
        if work_path is None:
            return None
        return latest_verify_note_for_work(
            self.watch_dir,
            self.verify_dir,
            work_path,
            repo_root=self.repo_root,
        )

    # ------------------------------------------------------------------
    def _get_same_day_verify_dir(self, work_path: Optional[Path]) -> Path:
        if work_path is None:
            return self.verify_dir
        return same_day_verify_dir_for_work(self.watch_dir, self.verify_dir, work_path)

    # ------------------------------------------------------------------
    def _build_verify_feedback_sigs(self, job: JobState) -> tuple[str, str]:
        work_path = Path(job.artifact_path)
        control_sig = compute_multi_file_sig(self.completion_paths)
        del work_path
        verify_sig = compute_md_tree_sig(self.verify_dir)
        return control_sig, verify_sig

    # ------------------------------------------------------------------
    def _build_verify_receipt_state(self, job: JobState) -> tuple[str, float]:
        work_path = Path(job.artifact_path)
        latest_verify = (
            self._get_latest_same_day_verify_path_for_work(work_path)
            or self._get_latest_same_day_verify_path(work_path)
        )
        if latest_verify is None:
            return "", 0.0
        return self._repo_relative(latest_verify), self._get_path_mtime(latest_verify)

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
        if work_path is None or not work_path.exists():
            return []
        try:
            lines = work_path.read_text().splitlines()
        except OSError:
            return []

        in_changed_files = False
        collected: list[str] = []
        for raw_line in lines:
            line = raw_line.rstrip()
            section = ROUND_NOTE_SECTION_RE.match(line.strip())
            if section:
                in_changed_files = section.group(1).strip() == "변경 파일"
                continue
            if not in_changed_files:
                continue
            if not line.strip():
                continue
            if line.lstrip().startswith("-"):
                bullet = line.lstrip()[1:].strip()
                if bullet == "없음":
                    continue
                for match in ROUND_NOTE_PATH_RE.finditer(bullet):
                    collected.append(match.group(1).lstrip("./"))
        return collected

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
        if self._current_turn_state != WatcherTurnState.ADVISORY_ACTIVE:
            return
        if not self._advisory_enabled():
            return
        if self._get_pending_operator_mtime() > 0.0:
            return
        active_control = self._get_active_control_signal()
        request_control = self._control_signal_for_slot(
            active_control,
            "advisory_request",
            "request_open",
        )
        if request_control is None:
            return

        request_sig = request_control.sig
        if not request_sig:
            return
        request_seq = request_control.control_seq
        if request_seq >= 0 and request_seq < self._turn_active_control_seq:
            return
        if self._advisory_advice_is_current_for_request(request_seq):
            return

        now = time.time()
        if request_sig == self._last_advisory_retry_sig:
            if now - self._last_advisory_retry_at < self.advisory_retry_sec:
                return
        else:
            request_started_at = max(self._turn_entered_at, request_control.mtime)
            if now - request_started_at < self.advisory_retry_sec:
                return

        target = self._prompt_pane_target("advisory")
        if not target:
            return
        ready, _ = self.dispatch_queue.lane_prompt_readiness(target)
        if not ready:
            return

        payload = {
            "reason": "advisory_idle_retry",
            "control_file": str(request_control.path.name),
            "control_seq": request_seq,
            "turn_state": self._current_turn_state.value,
            "target": target,
        }
        self._log_raw(
            "advisory_idle_retry",
            str(request_control.path),
            "turn_signal",
            payload,
        )
        self._append_runtime_event("advisory_idle_retry", payload)
        self._last_advisory_retry_sig = request_sig
        self._last_advisory_retry_at = now
        self._notify_advisory_owner("advisory_idle_retry")

    # ------------------------------------------------------------------
    def _stale_advisory_recovery_marker(self) -> Optional[dict[str, object]]:
        if self._current_turn_state != WatcherTurnState.ADVISORY_ACTIVE:
            return None
        if self._get_pending_operator_mtime() > 0.0:
            return None
        active_control = self._get_active_control_signal()
        request_control = self._control_signal_for_slot(
            active_control,
            "advisory_request",
            "request_open",
        )
        if request_control is None:
            return None

        request_sig = request_control.sig
        if not request_sig:
            return None
        if request_sig == self._last_advisory_recovery_sig:
            return None

        request_seq = request_control.control_seq
        if request_seq >= 0 and request_seq < self._turn_active_control_seq:
            return None
        if self._advisory_advice_is_current_for_request(request_seq):
            return None

        now = time.time()
        request_started_at = max(self._turn_entered_at, request_control.mtime)
        pending_age = now - request_started_at
        if pending_age < self.advisory_recovery_sec:
            return None

        if any(
            normalize_notify_kind(pending.get("notify_kind")) == ADVISORY_RECOVERY_NOTIFY
            for pending in self.dispatch_queue.pending_notifications.values()
        ):
            return None

        target = self._prompt_pane_target("verify")
        if not target:
            return None
        ready, defer_reason = self.dispatch_queue.lane_prompt_readiness(target)
        if not ready:
            return None

        return {
            "reason": "advisory_recovery",
            "control_file": request_control.path.name,
            "control_seq": request_seq,
            "request_sig": request_sig,
            "advisory_pending_age_sec": int(pending_age),
            "verify_lane_ready": True,
            "verify_lane_ready_reason": defer_reason,
        }

    # ------------------------------------------------------------------
    def _recover_stale_advisory(self) -> bool:
        marker = self._stale_advisory_recovery_marker()
        if marker is None:
            return False

        request_seq = control_seq_value(marker.get("control_seq"), default=-1)
        request_sig = str(marker.get("request_sig") or "")
        self._last_advisory_recovery_sig = request_sig
        self._last_advisory_recovery_at = time.time()
        self._clear_implement_blocked_state("advisory_recovery")
        self._log_raw(
            "advisory_recovery",
            str(self.advisory_request_path),
            "turn_signal",
            marker,
        )
        self._append_runtime_event("advisory_recovery", marker)
        self._transition_turn(
            WatcherTurnState.VERIFY_FOLLOWUP,
            "advisory_recovery",
            active_control_file="advisory_request.md",
            active_control_seq=request_seq,
        )
        self._notify_verify_advisory_recovery("advisory_recovery", marker)
        return True

    # ------------------------------------------------------------------
    def _operator_blocks_handoff(self, handoff_mtime: float) -> bool:
        del handoff_mtime
        return self._get_pending_operator_mtime() > 0.0

    # ------------------------------------------------------------------
    def _get_work_tree_snapshot(self) -> dict[str, str]:
        """work/ 전체 .md 스냅샷 반환."""
        snapshot: dict[str, str] = {}
        if not self.watch_dir.exists():
            return snapshot
        for md in self.watch_dir.rglob("*.md"):
            if not self._is_dispatchable_work_note(md):
                continue
            sig = compute_file_sig(md)
            if not sig:
                continue
            try:
                rel = str(md.relative_to(self.watch_dir))
            except ValueError:
                rel = str(md)
            snapshot[rel] = sig
        return snapshot

    # ------------------------------------------------------------------
    def _get_work_tree_snapshot_broad(self) -> dict[str, str]:
        """work/ 전체 canonical round-note 스냅샷 반환 (metadata-only 포함)."""
        snapshot: dict[str, str] = {}
        if not self.watch_dir.exists():
            return snapshot
        for md in self.watch_dir.rglob("*.md"):
            if not self._is_canonical_round_note(self.watch_dir, md):
                continue
            sig = compute_file_sig(md)
            if not sig:
                continue
            try:
                rel = str(md.relative_to(self.watch_dir))
            except ValueError:
                rel = str(md)
            snapshot[rel] = sig
        return snapshot

    # ------------------------------------------------------------------
    def _get_latest_work_mtime(self) -> float:
        """work/ 내 최신 .md 파일의 mtime 반환. 없으면 0.0."""
        latest = 0.0
        for md in self.watch_dir.rglob("*.md"):
            if not self._is_dispatchable_work_note(md):
                continue
            try:
                mt = md.stat().st_mtime
                if mt > latest:
                    latest = mt
            except OSError:
                continue
        return latest

    # ------------------------------------------------------------------
    def _work_has_matching_verify(
        self,
        work_path: Optional[Path],
        *,
        verified_work_paths: Optional[set[str]] = None,
    ) -> bool:
        if work_path is None:
            return False
        normalized_work = self._normalize_artifact_path(work_path)
        if not normalized_work:
            return False
        verified_paths = verified_work_paths if verified_work_paths is not None else self._verified_work_paths()
        if normalized_work in verified_paths:
            return True
        latest_verify = self._get_latest_same_day_verify_path_for_work(work_path)
        if latest_verify is None:
            return False
        return self._get_path_mtime(latest_verify) >= self._get_path_mtime(work_path)

    # ------------------------------------------------------------------
    def _get_latest_unverified_work_path(
        self,
        *,
        include_metadata_only: bool,
        newer_than_mtime: float = 0.0,
    ) -> Optional[Path]:
        if not self.watch_dir.exists():
            return None
        verified_work_paths = self._verified_work_paths()
        candidates: list[tuple[float, Path]] = []
        for md in self.watch_dir.rglob("*.md"):
            if include_metadata_only:
                if not self._is_canonical_round_note(self.watch_dir, md):
                    continue
            elif not self._is_dispatchable_work_note(md):
                continue
            try:
                mt = md.stat().st_mtime
            except OSError:
                continue
            if newer_than_mtime > 0.0 and mt < newer_than_mtime:
                continue
            candidates.append((mt, md))
        for _, md in sorted(candidates, key=lambda item: item[0], reverse=True):
            if self._work_has_matching_verify(md, verified_work_paths=verified_work_paths):
                continue
            return md
        return None

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
        """
        자동 verify rerun은 항상 최신 dispatchable `/work` 한 장만 기준으로 본다.
        오래된 backlog note는 이미 열린 current-run job replay로만 이어지고, 새 자동 스캔이
        과거 round를 다시 끌어오지는 않는다.
        """
        latest_work = self._get_latest_work_path()
        if latest_work is None:
            return False
        return not self._work_has_matching_verify(latest_work)

    # ------------------------------------------------------------------
    def _find_latest_md_broad(self, root: Path) -> Optional[Path]:
        """Find latest canonical round note without metadata-only filtering."""
        latest_path: Optional[Path] = None
        latest_mtime = 0.0
        if not root.exists():
            return None
        for md in root.rglob("*.md"):
            if not self._is_canonical_round_note(root, md):
                continue
            try:
                mt = md.stat().st_mtime
            except OSError:
                continue
            if mt >= latest_mtime:
                latest_path = md
                latest_mtime = mt
        return latest_path

    # ------------------------------------------------------------------
    def _latest_work_needs_verify_broad(self) -> bool:
        """Like _latest_work_needs_verify but includes metadata-only notes for the latest round only."""
        latest_work = self._get_latest_work_path_broad()
        if latest_work is None:
            return False
        return not self._work_has_matching_verify(latest_work)

    # ------------------------------------------------------------------
    def _get_latest_verify_candidate_path(self) -> Optional[Path]:
        """Latest canonical work note that should drive automatic verify/handoff rerun.

        Historical unmatched backlog is not reopened by fresh scans; only the newest canonical
        round note may open a new automatic verify job. Older notes can still continue when a
        current-run VERIFY_PENDING / VERIFY_RUNNING job already exists.
        """
        latest_work = self._get_latest_work_path_broad()
        if latest_work is None:
            return None
        if self._work_has_matching_verify(latest_work):
            return None
        return latest_work

    # ------------------------------------------------------------------
    def _get_current_run_jobs(
        self,
        *,
        statuses: Optional[set[JobStatus]] = None,
    ) -> list[JobState]:
        """Load current-run watcher jobs from shared state.

        Blank run_id is tolerated for test scaffolds and legacy local state.
        """
        if not self.state_dir.exists():
            return []
        jobs: list[JobState] = []
        seen_job_ids: set[str] = set()
        for path in iter_job_state_paths(self.state_dir):
            if path.stem in seen_job_ids:
                continue
            seen_job_ids.add(path.stem)
            job = JobState.load(self.state_dir, path.stem)
            if job is None:
                continue
            if job.run_id and job.run_id != self.run_id:
                continue
            if statuses is not None and job.status not in statuses:
                continue
            jobs.append(job)
        jobs.sort(
            key=lambda job: (
                float(job.last_dispatch_at or 0.0),
                float(job.updated_at or 0.0),
                str(job.job_id),
            ),
            reverse=True,
        )
        return jobs

    # ------------------------------------------------------------------
    def _archive_current_run_job(self, job: JobState, *, reason: str) -> bool:
        archived = False
        source_run_id = job.run_id or self.run_id
        for path in iter_job_state_paths(self.state_dir):
            if path.stem != job.job_id:
                continue
            self._archive_job_state_file(path, source_run_id=source_run_id, reason=reason)
            archived = True
        return archived

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
        pane_text = _capture_pane_text(target)
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
        if not _pane_text_is_idle(pane_text):
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
        verify_snapshot = _capture_pane_text(target)
        if not _pane_text_is_idle(verify_snapshot):
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
        if not self._advisory_enabled():
            return None
        if self._get_pending_advisory_request_mtime() > 0.0 or self._get_pending_advisory_advice_mtime() > 0.0:
            return None

        marker = self._operator_gate_marker()
        if marker is None:
            return None
        if not is_verify_followup_route(marker.get("routed_to")):
            return None

        operator_sig = self._get_path_sig(self.operator_request_path)
        if not operator_sig or operator_sig != self._last_operator_retriage_sig:
            return None
        if any(
            str(pending.get("notify_kind") or "") in {"verify_operator_retriage", "codex_operator_retriage"}
            for pending in self.dispatch_queue.pending_notifications.values()
        ):
            return None

        operator_seq = control_seq_value(marker.get("control_seq"), default=-1)
        if self._turn_active_control_seq >= 0 and operator_seq < self._turn_active_control_seq:
            return None

        now = time.time()
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
        reason_code = str(marker.get("reason_code") or marker.get("reason") or "slice_ambiguity")
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
            DispatchIntent(
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
            pane_text = _capture_pane_text(target)
        except Exception:
            return False, "pane_capture_failed"
        if not pane_text.strip():
            return False, "pane_blank"
        if not _pane_text_is_idle(pane_text):
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
        handoff_sig = handoff_control.sig if handoff_control is not None else self._get_path_sig(self.implement_handoff_path)
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
        implement_snapshot = _capture_pane_text(implement_target)
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
        if _is_pane_dead(implement_target):
            return False
        if _is_pane_dead(verify_target):
            return False
        if _is_pane_dead(advisory_target):
            return False
        if not _pane_text_is_idle(pane_snapshots["verify"]):
            return False
        if not _pane_text_is_idle(pane_snapshots["advisory"]):
            return False
        if _pane_text_is_idle(pane_snapshots["implement"]):
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
            "implement": _capture_pane_text(self._prompt_pane_target("implement")),
            "verify": _capture_pane_text(self._prompt_pane_target("verify")),
            "advisory": _capture_pane_text(self._prompt_pane_target("advisory")),
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
        self._write_runtime_status()
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
        if self._check_operator_recovery_without_signal():
            return
        self._check_operator_wait_idle_timeout()
        if self._promote_operator_retriage_no_next_control():
            return

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
