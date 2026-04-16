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
from pipeline_runtime.operator_autonomy import classify_operator_candidate

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


def _session_name_for_project(project_path: str) -> str:
    """Project path → deterministic session name (aip-<safe-dirname>)."""
    name = Path(project_path).resolve().name or "default"
    safe = re.sub(r"[^A-Za-z0-9_-]", "", name)
    return f"{_SESSION_PREFIX}-{safe}" if safe else f"{_SESSION_PREFIX}-default"


def _default_pane_targets(session: str) -> tuple[str, str, str]:
    """(claude, codex/verify, gemini) default pane targets for a session."""
    return f"{session}:0.0", f"{session}:0.1", f"{session}:0.2"


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
WORK_PATH_RE = re.compile(r"(work/\d+/\d+/[^\s`]+\.md)")


# ---------------------------------------------------------------------------
# 상태 정의
# ---------------------------------------------------------------------------
class JobStatus(str, Enum):
    NEW_ARTIFACT   = "NEW_ARTIFACT"
    STABILIZING    = "STABILIZING"
    VERIFY_PENDING = "VERIFY_PENDING"
    VERIFY_RUNNING = "VERIFY_RUNNING"
    VERIFY_DONE    = "VERIFY_DONE"       # 2단계 추가
    # 3단계 이후 추가 예정
    # COUNTER_PENDING  = "COUNTER_PENDING"
    # COUNTER_RUNNING  = "COUNTER_RUNNING"
    # DECISION_PENDING = "DECISION_PENDING"
    # RETRY_PENDING    = "RETRY_PENDING"
    # RETRY_RUNNING    = "RETRY_RUNNING"
    # ISOLATED         = "ISOLATED"
    # FINALIZED        = "FINALIZED"


TERMINAL_STATES: set[JobStatus] = {JobStatus.VERIFY_DONE}
# VERIFY_DONE는 2단계에서 terminal. 3단계에서 trust 분기가 붙으면 제거됨


class WatcherTurnState(str, Enum):
    IDLE             = "IDLE"
    CLAUDE_ACTIVE    = "CLAUDE_ACTIVE"
    CODEX_VERIFY     = "CODEX_VERIFY"
    CODEX_FOLLOWUP   = "CODEX_FOLLOWUP"
    GEMINI_ADVISORY  = "GEMINI_ADVISORY"
    OPERATOR_WAIT    = "OPERATOR_WAIT"


# ---------------------------------------------------------------------------
# JobState 스키마
# ---------------------------------------------------------------------------
@dataclass
class JobState:
    job_id:               str
    status:               JobStatus
    artifact_path:        str
    schema_version:       int   = SCHEMA_VERSION
    artifact_hash:        str   = ""
    artifact_size:        int   = 0
    artifact_mtime:       float = 0.0
    stabilized_at:        float = 0.0
    round:                int   = 1
    retry_budget:         int   = 3
    last_dispatch_at:     float = 0.0
    last_dispatch_slot:   str   = ""
    last_failed_dispatch_at: float = 0.0
    last_failed_dispatch_snapshot: str = ""
    dispatch_fail_count:  int   = 0
    feedback_baseline_sig:str   = ""    # dispatch 직전 control-slot 시그니처
    verify_feedback_baseline_sig:str = ""  # dispatch 직전 same-day /verify 스냅샷 시그니처
    verify_receipt_baseline_path:str = ""  # dispatch 직전 latest same-day /verify note path
    verify_receipt_baseline_mtime:float = 0.0  # dispatch 직전 latest same-day /verify note mtime
    # 2단계 추가 필드
    verify_manifest_path: str   = ""    # 수집된 manifest 파일 경로
    verify_completed_at:  float = 0.0   # VERIFY_DONE 전이 시각
    validation_score:     float = -1.0  # passed_checks/required_checks (-1 = 미수집)
    blocker_count:        int   = -1    # critical blocker 수 (-1 = 미수집)
    verify_result:        str   = ""    # "passed" | "failed" | "invalid_manifest"
    created_at:           float = field(default_factory=time.time)
    updated_at:           float = field(default_factory=time.time)
    history:              list  = field(default_factory=list)
    # Activity-based idle detection (persisted)
    last_pane_snapshot:   str   = ""
    last_activity_at:     float = 0.0

    # ------------------------------------------------------------------
    def transition(self, new_status: JobStatus, reason: str = "") -> None:
        old             = self.status
        self.status     = new_status
        self.updated_at = time.time()
        self.history.append({
            "from":   old.value,
            "to":     new_status.value,
            "at":     self.updated_at,
            "reason": reason,
        })
        log.info("state %s  %s → %s  (%s)", self.job_id, old.value, new_status.value, reason)

    # ------------------------------------------------------------------
    def save(self, state_dir: Path) -> None:
        state_dir.mkdir(parents=True, exist_ok=True)
        path = state_dir / f"{self.job_id}.json"
        tmp_path = path.with_suffix(f"{path.suffix}.tmp")
        data = asdict(self)
        data["status"] = self.status.value
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp_path.replace(path)

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, state_dir: Path, job_id: str) -> Optional["JobState"]:
        path = state_dir / f"{job_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            corrupt_path = path.with_suffix(f"{path.suffix}.corrupt-{int(time.time())}")
            try:
                path.replace(corrupt_path)
                log.warning("quarantined corrupt job state: %s -> %s (%s)", path, corrupt_path, e)
            except OSError:
                log.warning("failed to quarantine corrupt job state: %s (%s)", path, e)
            return None
        data["status"] = JobStatus(data["status"])
        return cls(**data)

    # ------------------------------------------------------------------
    @classmethod
    def from_artifact(cls, job_id: str, artifact_path: str) -> "JobState":
        return cls(
            job_id=job_id,
            status=JobStatus.NEW_ARTIFACT,
            artifact_path=artifact_path,
        )


# ---------------------------------------------------------------------------
# job_id 생성 (충돌 방지)
# ---------------------------------------------------------------------------
def make_job_id(watch_dir: Path, artifact: Path) -> str:
    """
    YYYYMMDD-<safe_stem>-<path_hash8> 형태.
      - safe_stem : 영숫자·하이픈만 유지, 최대 32자
      - path_hash8 : watch_dir 기준 상대경로의 sha1 앞 8자
    """
    rel       = artifact.relative_to(watch_dir)
    path_hash = hashlib.sha1(str(rel).encode()).hexdigest()[:8]
    safe_stem = "".join(c if c.isalnum() or c == "-" else "-" for c in artifact.stem)[:32]
    date_str  = time.strftime("%Y%m%d")
    return f"{date_str}-{safe_stem}-{path_hash}"


def compute_file_sig(path: Path) -> str:
    """mtime_ns + size + sha256 조합 시그니처. 파일이 없으면 빈 문자열."""
    try:
        stat = path.stat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return f"{stat.st_mtime_ns}:{stat.st_size}:{digest}"
    except OSError:
        return ""


def compute_multi_file_sig(paths: list[Path]) -> str:
    """여러 파일 시그니처를 합친다. 없는 파일은 건너뛴다."""
    parts: list[str] = []
    for path in paths:
        sig = compute_file_sig(path)
        if not sig:
            continue
        parts.append(f"{path.name}={sig}")
    return "|".join(parts)


def compute_file_sha256(path: Path) -> str:
    """파일 내용 기준 sha256 hex. 읽을 수 없으면 빈 문자열."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def build_md_tree_snapshot(root: Path) -> dict[str, str]:
    """root 하위 .md 파일의 상대경로 → 시그니처 스냅샷."""
    snapshot: dict[str, str] = {}
    if not root.exists():
        return snapshot
    for md in root.rglob("*.md"):
        sig = compute_file_sig(md)
        if not sig:
            continue
        try:
            rel = str(md.relative_to(root))
        except ValueError:
            rel = str(md)
        snapshot[rel] = sig
    return snapshot


def compute_md_tree_sig(root: Path) -> str:
    """root 하위 .md 트리 시그니처. 비어 있으면 빈 문자열."""
    snapshot = build_md_tree_snapshot(root)
    if not snapshot:
        return ""
    parts = [f"{path}={sig}" for path, sig in sorted(snapshot.items())]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


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


@dataclass
class ControlSignal:
    kind:        str
    path:        Path
    status:      str
    mtime:       float
    sig:         str
    control_seq: int = -1


class PaneLease:
    """slot별 lock 파일 기반 lease. dry_run 시 dispatch 직후 즉시 해제."""

    def __init__(self, lock_dir: Path, default_ttl: int = 900, dry_run: bool = False) -> None:
        self.lock_dir    = lock_dir
        self.default_ttl = default_ttl
        self.dry_run     = dry_run
        lock_dir.mkdir(parents=True, exist_ok=True)

    def _lock_path(self, slot: str) -> Path:
        return self.lock_dir / f"{slot}.lock"

    def acquire(self, slot: str, job_id: str, round_: int,
                pane_target: str, ttl: Optional[int] = None) -> bool:
        path = self._lock_path(slot)
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
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-pt", pane_target],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


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
    deadline = time.time() + timeout_sec
    last_snapshot = None
    last_change_at = time.time()

    while time.time() < deadline:
        snapshot = _capture_pane_text(pane_target)
        if snapshot != last_snapshot:
            last_snapshot = snapshot
            last_change_at = time.time()
        elif time.time() - last_change_at >= quiet_sec:
            return True
        time.sleep(poll_sec)
    return False


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
    has_type_your_message = any(line == "type your message" for line in window)
    has_workspace_hint = any(line == "workspace" or line.startswith("workspace ") for line in window)
    has_gemini_banner = any("gemini cli" in line for line in window)
    return has_type_your_message and (has_workspace_hint or has_gemini_banner)


def _pane_text_has_busy_indicator(text: str) -> bool:
    """Check if pane text contains any sign that the agent is still working."""
    # Case-insensitive search across entire visible pane text.
    # These patterns mean the agent has NOT finished yet.
    lower = text.lower()
    busy_patterns = [
        "working (",        # ◦ Working (36s • esc to interrupt)
        "working for ",     # Worked for 1m 25s (transition text)
        "• working",        # • Working ...
        "◦ working",        # ◦ Working ...
        "waiting for background",   # Waiting for background terminal
        "background terminal",      # background terminal (active)
        "germinating",      # Codex startup indicator
        "flumoxing",        # Claude thinking indicator
    ]
    for pattern in busy_patterns:
        if pattern in lower:
            return True
    return False


def _pane_text_has_input_cursor(text: str) -> bool:
    lines = [l for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return False
    for line in reversed(lines[-12:]):
        if _line_looks_like_input_prompt(line):
            return True
    return _pane_text_has_gemini_ready_prompt(text)


def _pane_has_input_cursor(pane_target: str) -> bool:
    """Check if the pane shows an input prompt in the recent visible lines."""
    text = _capture_pane_text(pane_target)
    return _pane_text_has_input_cursor(text)


def _pane_has_working_indicator(pane_target: str) -> bool:
    """Check whether the recent pane output shows Codex has started working."""
    text = _capture_pane_text(pane_target)
    return "• Working" in text


def _pane_text_is_idle(text: str) -> bool:
    """Treat a pane as idle only when a prompt is visible and no busy signal remains."""
    if not text.strip():
        return False
    return _pane_text_has_input_cursor(text) and not _pane_text_has_busy_indicator(text)


def _pane_text_has_codex_activity(text: str) -> bool:
    """Detect Codex response activity even when the input prompt remains visible."""
    return "\n• " in text or text.lstrip().startswith("• ")


def _pane_text_has_gemini_activity(text: str) -> bool:
    """Detect Gemini response/tool activity even when the input prompt remains visible."""
    return (
        "\n✦ " in text
        or text.lstrip().startswith("✦ ")
        or "ReadFile" in text
        or "WriteFile" in text
        or "ReadManyFiles" in text
    )


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

_IMPLEMENT_BLOCKED_STATUS_RE = re.compile(r"^\s*STATUS:\s*(.*?)\s*$", re.IGNORECASE)
_IMPLEMENT_BLOCKED_FIELD_RE = re.compile(r"^\s*([A-Z_]+):\s*(.*?)\s*$")
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


def _extract_claude_implement_blocked_signal(
    text: str,
    active_handoff_path: str = "",
    active_handoff_sha: str = "",
) -> Optional[dict[str, object]]:
    """Return an explicit implement_blocked sentinel if present in recent Claude output."""
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

        request = fields.get("REQUEST", "").lower()
        if request and request not in {"verify_triage", "codex_triage"}:
            return None

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
            "excerpt_lines": block_lines[:6],
            "fingerprint": fingerprint,
            "handoff_hint": handoff_hint,
        }
    return None


def _extract_claude_forbidden_menu_signal(text: str, active_handoff_sha: str = "") -> Optional[dict[str, object]]:
    """Detect forbidden operator-choice text in recent Claude output as a soft blocked signal."""
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
        "excerpt_lines": matched_lines[:6],
        "fingerprint": hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest(),
        "handoff_hint": "",
    }


def _extract_claude_completed_handoff_signal(text: str, active_handoff_sha: str = "") -> Optional[dict[str, object]]:
    """Detect Claude saying the current handoff is already complete / no-op."""
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
    try:
        if not _wait_for_dispatch_window(pane_target, pane_type):
            return False
        if pane_type == "codex":
            return _dispatch_codex(pane_target, command)
        elif pane_type == "gemini":
            _dispatch_gemini(pane_target, command)
        else:
            _dispatch_claude(pane_target, command)

        return True
    except subprocess.CalledProcessError as e:
        log.error("send-keys failed: %s", e.stderr.decode().strip())
        return False


def _dispatch_codex(pane_target: str, command: str) -> bool:
    """Dispatch to Codex pane.

    Codex interactive session is kept alive (started by start-pipeline.sh).
    Always paste-buffer into the running session — never re-launch codex.
    """
    log.info("dispatching codex prompt: chars=%d", len(command))
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
            log.info("codex dispatch not confirmed after consume: no working indicator or response activity")
            continue
        if snapshot != pasted_snapshot and _pane_text_has_codex_activity(snapshot):
            log.info("codex response activity detected: attempt %d", attempt + 1)
            return True
    log.info("codex prompt still visible or unconfirmed after retries")
    return False


def _dispatch_claude(pane_target: str, command: str) -> None:
    """Dispatch to Claude pane via paste-buffer + Enter."""
    subprocess.run(["tmux", "set-buffer", command], check=True, capture_output=True)
    subprocess.run(["tmux", "paste-buffer", "-t", pane_target], check=True, capture_output=True)
    time.sleep(1.0)
    for attempt in range(3):
        subprocess.run(["tmux", "send-keys", "-t", pane_target, "Enter"], check=True, capture_output=True)
        time.sleep(1.5)
        if not _pane_has_input_cursor(pane_target):
            log.info("claude prompt consumed: attempt %d", attempt + 1)
            break


def _dispatch_gemini(pane_target: str, command: str) -> None:
    """Dispatch to Gemini pane via paste-buffer + Enter."""
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
            break
        if snapshot != pasted_snapshot and _pane_text_has_gemini_activity(snapshot):
            log.info("gemini response activity detected: attempt %d", attempt + 1)
            break


# ---------------------------------------------------------------------------
# StateMachine
# ---------------------------------------------------------------------------
class StateMachine:
    """
    전이 규칙:
      NEW_ARTIFACT   → STABILIZING    : 새 산출물 감지
      STABILIZING    → VERIFY_PENDING : hash+mtime+size 안정화 완료
      VERIFY_PENDING → VERIFY_RUNNING : lease 획득 + send-keys 성공
      VERIFY_RUNNING → VERIFY_DONE    : manifest 수집 + 4중 일치 + 스키마 검증 통과   ← 2단계
    """

    def __init__(
        self,
        state_dir:              Path,
        stabilizer:             ArtifactStabilizer,
        lease:                  PaneLease,
        dedupe:                 DedupeGuard,
        collector:              ManifestCollector,
        verify_pane_target:     str,
        verify_pane_type:       str,
        verify_prompt_template: str,
        verify_context_builder: Optional[Callable[[JobState], dict[str, str]]],
        feedback_sig_builder:   Optional[Callable[[JobState], tuple[str, str]]],
        verify_receipt_builder: Optional[Callable[[JobState], tuple[str, float]]],
        verify_retry_backoff_sec: float,
        runtime_started_at:     float,
        restart_recovery_grace_sec: float,
        completion_paths:       list[Path],
        error_log:              Path,
        dry_run:                bool = False,
    ) -> None:
        self.state_dir              = state_dir
        self.stabilizer             = stabilizer
        self.lease                  = lease
        self.dedupe                 = dedupe
        self.collector              = collector
        self.verify_pane_target     = verify_pane_target
        self.verify_pane_type       = verify_pane_type
        self.verify_prompt_template = verify_prompt_template
        self.verify_context_builder = verify_context_builder
        self.feedback_sig_builder   = feedback_sig_builder
        self.verify_receipt_builder = verify_receipt_builder
        self.verify_retry_backoff_sec = verify_retry_backoff_sec
        self.runtime_started_at     = runtime_started_at
        self.restart_recovery_grace_sec = restart_recovery_grace_sec
        self.completion_paths       = completion_paths
        self.error_log              = error_log
        self.dry_run                = dry_run

    # ------------------------------------------------------------------
    def _write_feedback_manifest(self, job: JobState, verify_receipt_path: str) -> Optional[Path]:
        manifest_path = self.collector.manifest_path(job.job_id, job.round)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": 1,
            "job_id": job.job_id,
            "round": job.round,
            "role": "slot_verify",
            "artifact_hash": job.artifact_hash,
            "required_checks": 0,
            "passed_checks": 0,
            "blockers": [],
            "recommended_next_action": "finalize",
            "feedback_path": verify_receipt_path,
            "created_at": dt.datetime.fromtimestamp(time.time(), dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        tmp_path = manifest_path.with_suffix(f"{manifest_path.suffix}.tmp")
        try:
            tmp_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
            tmp_path.replace(manifest_path)
        except OSError as exc:
            log.warning("feedback manifest write failed: job=%s path=%s err=%s", job.job_id, manifest_path, exc)
            return None
        return manifest_path

    # ------------------------------------------------------------------
    def step(self, job: JobState) -> JobState:
        if job.status == JobStatus.NEW_ARTIFACT:
            return self._handle_new_artifact(job)
        if job.status == JobStatus.STABILIZING:
            return self._handle_stabilizing(job)
        if job.status == JobStatus.VERIFY_PENDING:
            return self._handle_verify_pending(job)
        if job.status == JobStatus.VERIFY_RUNNING:
            return self._handle_verify_running(job)
        return job

    # ------------------------------------------------------------------
    def _handle_new_artifact(self, job: JobState) -> JobState:
        job.transition(JobStatus.STABILIZING, "new artifact detected")
        job.save(self.state_dir)
        return job

    def _handle_stabilizing(self, job: JobState) -> JobState:
        if not self.stabilizer.check(job.job_id, job.artifact_path):
            return job
        path               = Path(job.artifact_path)
        stat               = path.stat()
        job.artifact_hash  = hashlib.sha256(path.read_bytes()).hexdigest()
        job.artifact_size  = stat.st_size
        job.artifact_mtime = stat.st_mtime
        job.stabilized_at  = time.time()
        self.stabilizer.clear(job.job_id)
        job.transition(JobStatus.VERIFY_PENDING, "artifact stabilized")
        job.save(self.state_dir)
        return job

    def _handle_verify_pending(self, job: JobState) -> JobState:
        slot = "slot_verify"

        if job.last_failed_dispatch_at:
            backoff_deadline = job.last_failed_dispatch_at + self.verify_retry_backoff_sec
            if time.time() < backoff_deadline:
                self.dedupe.mark_suppressed(
                    job.job_id, job.round, job.artifact_hash, slot, "dispatch_backoff"
                )
                return job

            if job.last_failed_dispatch_snapshot:
                current_pane = _capture_pane_text(self.verify_pane_target)
                if current_pane == job.last_failed_dispatch_snapshot:
                    self.dedupe.mark_suppressed(
                        job.job_id, job.round, job.artifact_hash, slot, "dispatch_backoff_same_snapshot"
                    )
                    return job

        if self.dedupe.is_duplicate(job.job_id, job.round, job.artifact_hash, slot):
            self.dedupe.mark_suppressed(
                job.job_id, job.round, job.artifact_hash, slot, "dedupe")
            return job

        if not self.lease.acquire(slot, job.job_id, job.round, self.verify_pane_target):
            self.dedupe.mark_suppressed(
                job.job_id, job.round, job.artifact_hash, slot, "lease_busy")
            return job

        prompt_context = {
            "job_id": job.job_id,
            "round": job.round,
            "artifact_path": job.artifact_path,
            "latest_work_path": job.artifact_path,
            "latest_verify_path": "없음",
        }
        if self.verify_context_builder:
            prompt_context.update(self.verify_context_builder(job))

        prompt = _normalize_prompt_text(self.verify_prompt_template.format(**prompt_context))
        ok = tmux_send_keys(
            self.verify_pane_target,
            prompt,
            self.dry_run,
            pane_type=self.verify_pane_type,
        )

        if ok:
            self.dedupe.mark_dispatch(
                job.job_id, job.round, job.artifact_hash, slot,
                self.verify_pane_target, self.dry_run,
            )
            job.last_dispatch_at   = time.time()
            job.last_dispatch_slot = slot
            job.last_failed_dispatch_at = 0.0
            job.last_failed_dispatch_snapshot = ""
            job.dispatch_fail_count = 0
            if self.feedback_sig_builder is not None:
                (
                    job.feedback_baseline_sig,
                    job.verify_feedback_baseline_sig,
                ) = self.feedback_sig_builder(job)
            else:
                job.feedback_baseline_sig = compute_multi_file_sig(self.completion_paths)
                job.verify_feedback_baseline_sig = ""
            if self.verify_receipt_builder is not None:
                (
                    job.verify_receipt_baseline_path,
                    job.verify_receipt_baseline_mtime,
                ) = self.verify_receipt_builder(job)
            else:
                job.verify_receipt_baseline_path = ""
                job.verify_receipt_baseline_mtime = 0.0
            job.transition(JobStatus.VERIFY_RUNNING, f"dispatched to {slot}")
            job.save(self.state_dir)
            if self.dry_run:
                self.lease.release(slot)
        else:
            job.last_failed_dispatch_at = time.time()
            job.dispatch_fail_count += 1
            job.last_failed_dispatch_snapshot = _capture_pane_text(self.verify_pane_target)
            job.save(self.state_dir)
            self.lease.release(slot)
        return job

    # ------------------------------------------------------------------
    def _handle_verify_running(self, job: JobState) -> JobState:
        """
        manifest 파일을 폴링하고:
          - 없으면:
            · control slot이 dispatch 이후 갱신됐으면 → Codex 완료로 간주, VERIFY_DONE
            · lease TTL 초과 → 타임아웃, VERIFY_DONE (result=timeout)
            · 그 외 → 대기 (VERIFY_RUNNING 유지)
          - 스키마/일치 검증 실패 → verify_result="invalid_manifest", VERIFY_RUNNING 유지
            + error 로그 기록
          - 검증 통과 → verify_result="passed"|"failed", VERIFY_DONE 전이
        """
        manifest = self.collector.poll(job)
        if manifest is None:
            # manifest 없음 — feedback 변경 또는 타임아웃 체크
            # Codex는 manifest 없이 /verify + rolling control slot을 함께 갱신할 수 있음
            if self.feedback_sig_builder is not None:
                fb_sig, verify_sig = self.feedback_sig_builder(job)
            else:
                fb_sig = compute_multi_file_sig(self.completion_paths)
                verify_sig = ""
            if self.verify_receipt_builder is not None:
                verify_receipt_path, verify_receipt_mtime = self.verify_receipt_builder(job)
            else:
                verify_receipt_path, verify_receipt_mtime = "", 0.0

            control_changed = bool(fb_sig and fb_sig != job.feedback_baseline_sig)
            verify_changed = bool(verify_sig and verify_sig != job.verify_feedback_baseline_sig)
            verify_receipt_present = bool(
                verify_receipt_path
                and verify_receipt_mtime > 0.0
                # Some filesystems round mtime to whole seconds, so allow a small skew.
                and verify_receipt_mtime >= (job.last_dispatch_at - 1.0)
                and (
                    verify_receipt_path != job.verify_receipt_baseline_path
                    or verify_receipt_mtime > job.verify_receipt_baseline_mtime
                )
            )
            outputs_complete = control_changed and verify_changed and verify_receipt_present

            if outputs_complete:
                # current-round /verify receipt와 next control이 둘 다 달라졌으면 Codex 완료로 간주
                log.info(
                    "current-round verify receipt + control changed after dispatch: job=%s, treating as verify done",
                    job.job_id,
                )
                manifest_path = self._write_feedback_manifest(job, verify_receipt_path)
                if manifest_path is None:
                    return job
                job.verify_result = "passed_by_feedback"
                job.verify_manifest_path = str(manifest_path)
                job.verify_completed_at = time.time()
                job.validation_score = 1.0
                job.blocker_count = 0
                self.lease.release("slot_verify")
                job.transition(JobStatus.VERIFY_DONE,
                               "current-round verify receipt + control changed after dispatch")
                job.save(self.state_dir)
                return job
            if control_changed and verify_changed and not verify_receipt_present:
                log.info(
                    "control + /verify tree changed but current-round /verify receipt is still missing: job=%s receipt=%s baseline=%s",
                    job.job_id,
                    verify_receipt_path or "none",
                    job.verify_receipt_baseline_path or "none",
                )
            if control_changed and not verify_changed:
                log.info(
                    "control slot changed but /verify not updated yet: job=%s",
                    job.job_id,
                )

            # Check if Codex finished: pane must show an input prompt AND
            # have no active working/waiting indicators anywhere in visible text.
            current_pane = _capture_pane_text(self.verify_pane_target)
            still_busy = _pane_text_has_busy_indicator(current_pane)
            has_prompt = _pane_text_has_input_cursor(current_pane)
            codex_idle = has_prompt and not still_busy
            elapsed_since_dispatch = time.time() - job.last_dispatch_at
            stale_dispatch_before_runtime = (
                job.last_dispatch_at > 0.0
                and job.last_dispatch_at < self.runtime_started_at
            )
            # Idle alone is not enough; Codex must leave /verify + next control (or manifest).
            if codex_idle and elapsed_since_dispatch > 15 and not (control_changed and verify_changed):
                log.info(
                    "codex idle observed but required outputs are incomplete: job=%s elapsed=%.0fs",
                    job.job_id,
                    elapsed_since_dispatch,
                )
            if (
                stale_dispatch_before_runtime
                and codex_idle
                and elapsed_since_dispatch >= self.restart_recovery_grace_sec
                and not outputs_complete
            ):
                log.info(
                    "startup recovery: stale verify dispatch before watcher start and pane is idle: job=%s elapsed=%.0fs",
                    job.job_id,
                    elapsed_since_dispatch,
                )
                self.dedupe.forget(job.job_id, job.round, job.artifact_hash, "slot_verify")
                job.last_failed_dispatch_at = 0.0
                job.last_failed_dispatch_snapshot = ""
                job.last_dispatch_slot = ""
                self.lease.release("slot_verify")
                job.transition(
                    JobStatus.VERIFY_PENDING,
                    f"startup recovery after stale dispatch ({elapsed_since_dispatch:.0f}s old, pane idle)",
                )
                job.save(self.state_dir)
                return job

            # Activity-based timeout: only timeout if pane output hasn't changed.
            elapsed = time.time() - job.last_dispatch_at
            last_activity = job.last_activity_at or job.last_dispatch_at

            if current_pane != job.last_pane_snapshot:
                # Pane changed — task is still active, reset activity timer
                job.last_pane_snapshot = current_pane
                job.last_activity_at = time.time()
                job.save(self.state_dir)
            else:
                # Pane unchanged — check idle timeout (5 min idle = timeout)
                idle_sec = time.time() - last_activity
                if idle_sec > 300:
                    if not outputs_complete:
                        log.warning(
                            "verify idle timeout with incomplete outputs: job=%s idle=%.0fs total=%.0fs → retry pending",
                            job.job_id, idle_sec, elapsed,
                        )
                        self.dedupe.forget(job.job_id, job.round, job.artifact_hash, "slot_verify")
                        job.last_failed_dispatch_at = time.time()
                        job.dispatch_fail_count += 1
                        # If the pane is already back at an idle prompt, keep only the timed
                        # backoff and let the next retry re-dispatch instead of permanently
                        # pinning VERIFY_PENDING on the same visible snapshot.
                        job.last_failed_dispatch_snapshot = "" if codex_idle else current_pane
                        job.last_dispatch_slot = ""
                        self.lease.release("slot_verify")
                        job.transition(
                            JobStatus.VERIFY_PENDING,
                            f"idle timeout with incomplete outputs after {idle_sec:.0f}s idle, {elapsed:.0f}s total",
                        )
                        job.save(self.state_dir)
                        return job
                    log.warning("verify idle timeout: job=%s idle=%.0fs total=%.0fs",
                                job.job_id, idle_sec, elapsed)
                    job.verify_result = "timeout"
                    job.verify_completed_at = time.time()
                    self.lease.release("slot_verify")
                    job.transition(JobStatus.VERIFY_DONE,
                                   f"idle timeout after {idle_sec:.0f}s idle, {elapsed:.0f}s total")
                    job.save(self.state_dir)
                    return job

            return job  # 아직 대기

        manifest_path = self.collector.manifest_path(job.job_id, job.round)

        valid, reason = self.collector.validate(manifest, job)
        if not valid:
            # 스키마 또는 일치 검증 실패 → VERIFY_RUNNING 유지, error 기록
            job.verify_result = "invalid_manifest"
            job.save(self.state_dir)
            self._log_error(job.job_id, job.round, "invalid_manifest", reason, str(manifest_path))
            log.warning("invalid manifest: job=%s round=%d reason=%s",
                        job.job_id, job.round, reason)
            return job

        # 검증 통과 → 정량 필드 추출
        scores = self.collector.extract_scores(manifest)
        job.validation_score    = scores["validation_score"]
        job.blocker_count       = scores["blocker_count"]
        job.verify_manifest_path = str(manifest_path)
        job.verify_completed_at  = time.time()

        # blocker가 있으면 failed, 없으면 passed
        job.verify_result = "failed" if job.blocker_count > 0 else "passed"

        self.lease.release("slot_verify")
        job.transition(
            JobStatus.VERIFY_DONE,
            f"manifest valid: result={job.verify_result} "
            f"score={job.validation_score:.3f} blockers={job.blocker_count}",
        )
        job.save(self.state_dir)
        log.info(
            "VERIFY_DONE: job=%s round=%d result=%s score=%.3f blockers=%d",
            job.job_id, job.round, job.verify_result,
            job.validation_score, job.blocker_count,
        )
        return job

    # ------------------------------------------------------------------
    def _log_error(self, job_id: str, round_: int, error_type: str,
                   reason: str, manifest_path: str) -> None:
        self.error_log.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "event":         "manifest_error",
            "job_id":        job_id,
            "round":         round_,
            "error_type":    error_type,
            "reason":        reason,
            "manifest_path": manifest_path,
            "at":            time.time(),
        }
        with self.error_log.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# WatcherCore – 메인 폴링 루프
# ---------------------------------------------------------------------------
class WatcherCore:
    """
    메인 폴링 루프 v2.1
    변경: 시작 시 턴(turn) 판단 + feedback 파일 감시로 Claude에 신호 전달.
    로그는 .pipeline/logs/experimental/ 에 저장 (baseline은 .pipeline/logs/baseline/).
    """

    def __init__(self, config: dict) -> None:
        base = Path(config.get("base_dir", ".pipeline"))

        self.base_dir      = base
        self.watch_dir     = Path(config["watch_dir"])
        self.artifact_root = self.watch_dir.parent
        self.repo_root     = Path(config.get("repo_root", str(self.artifact_root))).resolve()
        self.verify_dir    = self.artifact_root / "verify"
        self.report_gemini_dir = self.artifact_root / "report" / "gemini"
        self.state_dir     = base / "state"
        self.lock_dir      = base / "locks"
        self.manifests_dir = base / "manifests"

        # 로그 디렉터리 분리: experimental vs baseline
        self.events_dir = base / "logs" / "experimental"
        self.events_dir.mkdir(parents=True, exist_ok=True)

        self.poll_interval = config.get("poll_interval", 1.0)
        self.dry_run       = config.get("dry_run", False)
        self.startup_grace_sec = float(config.get("startup_grace_sec", 8.0))
        self.session_arbitration_settle_sec = float(config.get("session_arbitration_settle_sec", 5.0))
        self.session_arbitration_cooldown_sec = float(config.get("session_arbitration_cooldown_sec", 300.0))
        self.implement_blocked_settle_sec = float(config.get("implement_blocked_settle_sec", 5.0))
        self.implement_blocked_cooldown_sec = float(config.get("implement_blocked_cooldown_sec", 300.0))
        self.started_at = time.time()
        self.runtime_adapter = resolve_project_runtime_adapter(self.repo_root)
        self.runtime_controls = dict(self.runtime_adapter.get("controls") or {})
        self.runtime_role_owners = dict(self.runtime_adapter.get("role_owners") or {})
        self.runtime_lane_configs = list(self.runtime_adapter.get("lane_configs") or [])

        # rolling handoff 슬롯
        self.claude_handoff_path    = base / "claude_handoff.md"      # Claude-only execution slot
        self.gemini_request_path    = base / "gemini_request.md"      # Codex -> Gemini request slot
        self.gemini_advice_path     = base / "gemini_advice.md"       # Gemini -> Codex advice slot
        self.operator_request_path  = base / "operator_request.md"    # operator-only stop slot
        self.session_arbitration_draft_path = base / "session_arbitration_draft.md"  # watcher-generated non-canonical draft
        self.completion_paths       = [
            self.claude_handoff_path,
            self.gemini_request_path,
            self.operator_request_path,
        ]
        # pane target: 명시 인자 우선, 없으면 project-aware session 기반 default
        repo_root_str = str(self.repo_root)
        _sess = _session_name_for_project(repo_root_str)
        _def_claude, _def_codex, _def_gemini = _default_pane_targets(_sess)
        self.claude_pane_target  = config.get("claude_pane_target", _def_claude)
        self.gemini_pane_target  = config.get("gemini_pane_target", _def_gemini)
        self.codex_pane_target   = config.get("verify_pane_target", _def_codex)
        self.agent_pane_targets = {
            "Claude": self.claude_pane_target,
            "Codex": self.codex_pane_target,
            "Gemini": self.gemini_pane_target,
        }
        self.implement_prompt       = _normalize_prompt_text(
            config.get("implement_prompt")
            or config.get("claude_prompt")
            or
            "ROLE: implement\n"
            "OWNER: {runtime_implement_owner}\n"
            "HANDOFF: {active_handoff_path}\n"
            "HANDOFF_SHA: {active_handoff_sha}\n"
            "GOAL:\n"
            "- implement only the exact slice in the handoff\n"
            "- if finished, leave one `/work` closeout and stop\n"
            "READ_FIRST:\n"
            "- {runtime_implement_read_first_doc}\n"
            "- work/README.md\n"
            "- {active_handoff_path}\n"
            "RULES:\n"
            "- do not commit, push, publish a branch/PR, or choose the next slice\n"
            "- do not write .pipeline/gemini_request.md or .pipeline/operator_request.md yourself\n"
            "- if the handoff is blocked or not actionable, emit the exact sentinel below and stop\n"
            "BLOCKED_SENTINEL:\n"
            "STATUS: implement_blocked\n"
            "BLOCK_REASON: <short_reason>\n"
            "REQUEST: verify_triage\n"
            "HANDOFF: {active_handoff_path}\n"
            "HANDOFF_SHA: {active_handoff_sha}\n"
            "BLOCK_ID: {active_handoff_sha}:<short_reason>"
        )
        self.advisory_prompt       = _normalize_prompt_text(
            config.get("advisory_prompt")
            or config.get("gemini_prompt")
            or
            "ROLE: advisory\n"
            "OWNER: {runtime_advisory_owner}\n"
            "REQUEST: {gemini_request_mention}\n"
            "WORK: {latest_work_mention}\n"
            "VERIFY: {latest_verify_mention}\n"
            "NEXT_CONTROL_SEQ: {next_control_seq}\n"
            "GOAL:\n"
            "- leave one advisory log and one `.pipeline/gemini_advice.md`\n"
            "READ_FIRST:\n"
            "- {runtime_advisory_read_first_doc}\n"
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
        )
        self.followup_prompt = _normalize_prompt_text(
            config.get("followup_prompt")
            or config.get("codex_followup_prompt")
            or
            "ROLE: followup\n"
            "OWNER: {runtime_verify_owner}\n"
            "NEXT_CONTROL_SEQ: {next_control_seq}\n"
            "REQUEST: .pipeline/gemini_request.md\n"
            "ADVICE: .pipeline/gemini_advice.md\n"
            "WORK: {latest_work_path}\n"
            "VERIFY: {latest_verify_path}\n"
            "GOAL:\n"
            "- convert the advisory into exactly one next control outcome\n"
            "READ_FIRST:\n"
            "- {runtime_verify_read_first_doc}\n"
            "- verify/README.md\n"
            "- .pipeline/gemini_request.md\n"
            "- .pipeline/gemini_advice.md\n"
            "OUTPUTS:\n"
            "- .pipeline/claude_handoff.md (STATUS: implement, CONTROL_SEQ: {next_control_seq})\n"
            "- .pipeline/operator_request.md (STATUS: needs_operator, CONTROL_SEQ: {next_control_seq})\n"
            "RULES:\n"
            "- write exactly one next control outcome\n"
            "- after Gemini advice, write .pipeline/operator_request.md only if the advice itself recommends a real operator decision or still leaves no truthful exact slice"
        )
        self.control_recovery_prompt = _normalize_prompt_text(
            config.get("control_recovery_prompt")
            or
            "ROLE: control_recovery\n"
            "OWNER: {runtime_verify_owner}\n"
            "STALE_CONTROL: {stale_control_path}\n"
            "STALE_CONTROL_SEQ: {stale_control_seq}\n"
            "REASON: {stale_control_reason}\n"
            "RESOLVED_BLOCKERS:\n"
            "{stale_control_resolved_work_paths}\n"
            "WORK: {latest_work_path}\n"
            "VERIFY: {latest_verify_path}\n"
            "GOAL:\n"
            "- the active operator stop was suppressed because its referenced blocker work notes are already VERIFY_DONE\n"
            "- write exactly one next control outcome so runtime does not stay idle on stale control alone\n"
            "READ_FIRST:\n"
            "- {runtime_verify_read_first_doc}\n"
            "- verify/README.md\n"
            "- {stale_control_path}\n"
            "- {latest_work_path}\n"
            "- {latest_verify_path}\n"
            "OUTPUTS:\n"
            "- .pipeline/claude_handoff.md (STATUS: implement, CONTROL_SEQ: {next_control_seq})\n"
            "- .pipeline/gemini_request.md (STATUS: request_open, CONTROL_SEQ: {next_control_seq})\n"
            "- .pipeline/operator_request.md (STATUS: needs_operator, CONTROL_SEQ: {next_control_seq})\n"
            "RULES:\n"
            "- write exactly one next control outcome\n"
            "- if the only blocker is next-slice ambiguity, overlapping candidates, or low-confidence prioritization, write .pipeline/gemini_request.md before .pipeline/operator_request.md\n"
            "- do not leave runtime idle on a stale operator stop alone\n"
            "- only use STATUS: needs_operator without Gemini for a real operator-only decision, approval/truth-sync blocker, immediate safety stop, or when Gemini is unavailable/already inconclusive"
        )
        self.operator_retriage_prompt = _normalize_prompt_text(
            config.get("operator_retriage_prompt")
            or
            "ROLE: operator_retriage\n"
            "OWNER: {runtime_verify_owner}\n"
            "ACTIVE_CONTROL: {operator_request_path}\n"
            "ACTIVE_CONTROL_SEQ: {stale_control_seq}\n"
            "PENDING_AGE_SEC: {operator_wait_age_sec}\n"
            "REASON: {stale_control_reason}\n"
            "WORK: {latest_work_path}\n"
            "VERIFY: {latest_verify_path}\n"
            "GOAL:\n"
            "- the active operator stop is pending or gated, so runtime should re-triage it instead of publishing operator wait immediately\n"
            "- verify whether the stop is still a real operator-only decision after self-heal / triage / hibernate checks\n"
            "- then write exactly one next control outcome\n"
            "READ_FIRST:\n"
            "- {runtime_verify_read_first_doc}\n"
            "- verify/README.md\n"
            "- {operator_request_path}\n"
            "- {latest_work_path}\n"
            "- {latest_verify_path}\n"
            "OUTPUTS:\n"
            "- .pipeline/claude_handoff.md (STATUS: implement, CONTROL_SEQ: {next_control_seq})\n"
            "- .pipeline/gemini_request.md (STATUS: request_open, CONTROL_SEQ: {next_control_seq})\n"
            "- .pipeline/operator_request.md (STATUS: needs_operator, CONTROL_SEQ: {next_control_seq})\n"
            "RULES:\n"
            "- write exactly one next control outcome\n"
            "- prefer .pipeline/gemini_request.md before .pipeline/operator_request.md when the only blocker is next-slice ambiguity\n"
            "- only keep STATUS: needs_operator if a real operator-only decision, approval/truth-sync blocker, or immediate safety stop still remains right now"
        )
        self.verify_triage_prompt = _normalize_prompt_text(
            config.get("verify_triage_prompt")
            or config.get("codex_blocked_triage_prompt")
            or
            "ROLE: verify_triage\n"
            "OWNER: {runtime_verify_owner}\n"
            "HANDOFF: {active_handoff_path}\n"
            "HANDOFF_SHA: {active_handoff_sha}\n"
            "BLOCK_SOURCE: {blocked_source}\n"
            "BLOCK_REASON: {blocked_reason}\n"
            "BLOCK_ID: {blocked_fingerprint}\n"
            "NEXT_CONTROL_SEQ: {next_control_seq}\n"
            "WORK: {latest_work_path}\n"
            "VERIFY: {latest_verify_path}\n"
            "GOAL:\n"
            "- recover from implement_blocked with exactly one next control outcome\n"
            "BLOCK_EXCERPT:\n"
            "{blocked_excerpt}\n"
            "READ_FIRST:\n"
            "- {runtime_verify_read_first_doc}\n"
            "- verify/README.md\n"
            "- {active_handoff_path}\n"
            "- {latest_work_path}\n"
            "- {latest_verify_path}\n"
            "OUTPUTS:\n"
            "- .pipeline/claude_handoff.md (STATUS: implement, CONTROL_SEQ: {next_control_seq})\n"
            "- .pipeline/gemini_request.md (STATUS: request_open, CONTROL_SEQ: {next_control_seq})\n"
            "- .pipeline/operator_request.md (STATUS: needs_operator, CONTROL_SEQ: {next_control_seq})\n"
            "RULES:\n"
            "- write exactly one next control outcome\n"
            "- do not leave Claude waiting on an operator-choice menu\n"
            "- if the only blocker is next-slice ambiguity, overlapping candidates, or low-confidence prioritization, write .pipeline/gemini_request.md before .pipeline/operator_request.md\n"
            "- only use STATUS: needs_operator without Gemini for a real operator-only decision, approval/truth-sync blocker, immediate safety stop, or when Gemini is unavailable/already inconclusive"
        )

        # rolling 슬롯 시그니처 추적 (mtime_ns + size + hash)
        self._last_claude_handoff_sig: str = self._get_path_sig(self.claude_handoff_path)
        self._last_gemini_request_sig: str = self._get_path_sig(self.gemini_request_path)
        self._last_gemini_advice_sig: str = self._get_path_sig(self.gemini_advice_path)
        self._last_operator_request_sig: str = self._get_path_sig(self.operator_request_path)
        self._last_operator_retriage_sig: str = ""
        self._last_session_arbitration_draft_sig: str = self._get_path_sig(self.session_arbitration_draft_path)
        self._last_session_arbitration_fingerprint: str = ""
        self._session_arbitration_snapshot_fingerprints: dict[str, str] = {}
        self._session_arbitration_snapshot_changed_at: dict[str, float] = {}
        self._session_arbitration_cooldowns: dict[str, float] = {}
        self._last_claude_blocked_fingerprint: str = ""
        self._claude_blocked_snapshot_fingerprints: dict[str, str] = {}
        self._claude_blocked_snapshot_changed_at: dict[str, float] = {}
        self._claude_blocked_cooldowns: dict[str, float] = {}
        # 시작 시 이미 Claude 차례인지 판단하는 플래그
        self._initial_turn_checked: bool = False
        # Claude 차례일 때: 시작 시점 work/ 스냅샷
        # 이후 스냅샷이 달라질 때만 새 작업으로 인정
        self._work_baseline_snapshot: dict[str, str] = {}
        # Turn state (single source of truth for dispatch)
        self._current_turn_state: WatcherTurnState = WatcherTurnState.IDLE
        self._turn_entered_at: float = 0.0
        self._turn_active_control_file: str = ""
        self._turn_active_control_seq: int = -1
        self._turn_state_path: Path = self.state_dir / "turn_state.json"
        self._runtime_export_enabled: bool = os.environ.get("PIPELINE_RUNTIME_DISABLE_EXPORTER", "").strip().lower() not in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.run_id: str = self._make_run_id()
        self.run_dir: Path = self.base_dir / "runs" / self.run_id
        self.run_status_path: Path = self.run_dir / "status.json"
        self.run_events_path: Path = self.run_dir / "events.jsonl"
        self.current_run_path: Path = self.base_dir / "current_run.json"
        self._runtime_event_seq: int = 0
        if self._runtime_export_enabled:
            self.run_dir.mkdir(parents=True, exist_ok=True)

        # Claude idle timeout tracking
        self.claude_active_idle_timeout_sec: float = float(
            config.get("claude_active_idle_timeout_sec", 300)
        )
        self.operator_wait_retriage_sec: float = float(
            config.get("operator_wait_retriage_sec", 3600)
        )
        self._last_progress_at: float = 0.0
        self._last_active_pane_fingerprint: str = ""
        self._last_idle_release_handoff_sig: str = ""
        self._last_idle_release_at: float = 0.0

        self.stabilizer = ArtifactStabilizer(
            settle_sec=config.get("settle_sec", 3.0),
            required_stable=config.get("required_stable", 2),
        )
        self.lease  = PaneLease(
            self.lock_dir,
            default_ttl=config.get("lease_ttl", 900),
            dry_run=self.dry_run,
        )
        self.dedupe = DedupeGuard(self.events_dir)

        schema_path = Path(config.get(
            "manifest_schema_path",
            str(Path(__file__).parent / "schemas" / "agent_manifest.schema.json"),
        ))
        self.collector = ManifestCollector(self.manifests_dir, schema_path)

        self.sm = StateMachine(
            state_dir=self.state_dir,
            stabilizer=self.stabilizer,
            lease=self.lease,
            dedupe=self.dedupe,
            collector=self.collector,
            verify_pane_target=self._role_pane_target("verify") or config.get("verify_pane_target", _def_codex),
            verify_pane_type=self._role_pane_type("verify"),
            verify_prompt_template=config.get(
                "verify_prompt_template",
                "ROLE: verify\n"
                "OWNER: {runtime_verify_owner}\n"
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
                "- {runtime_verify_read_first_doc}\n"
                "- work/README.md\n"
                "- verify/README.md\n"
                "OUTPUTS:\n"
                "- /verify note first\n"
                "- .pipeline/claude_handoff.md (STATUS: implement, CONTROL_SEQ: {next_control_seq})\n"
                "- .pipeline/gemini_request.md (STATUS: request_open, CONTROL_SEQ: {next_control_seq})\n"
                "- .pipeline/operator_request.md (STATUS: needs_operator, CONTROL_SEQ: {next_control_seq})\n"
                "RULES:\n"
                "- keep one exact next slice or one exact operator decision only\n"
                "- if the only blocker is next-slice ambiguity, overlapping candidates, or low-confidence prioritization, open .pipeline/gemini_request.md before .pipeline/operator_request.md\n"
                "- use .pipeline/operator_request.md without Gemini only for a real operator-only decision, approval/truth-sync blocker, immediate safety stop, or when Gemini is unavailable/already inconclusive\n"
                "- if same-day same-family docs-only truth-sync already repeated 3+ times, do not choose another narrower docs-only micro-slice; choose one bounded docs bundle or escalate",
            ),
            verify_context_builder=self._build_verify_prompt_context,
            feedback_sig_builder=self._build_verify_feedback_sigs,
            verify_receipt_builder=self._build_verify_receipt_state,
            verify_retry_backoff_sec=float(config.get("verify_retry_backoff_sec", 20.0)),
            runtime_started_at=self.started_at,
            restart_recovery_grace_sec=float(config.get("restart_recovery_grace_sec", 15.0)),
            completion_paths=self.completion_paths,
            error_log=self.events_dir / "errors.jsonl",
            dry_run=self.dry_run,
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
        return owner or None

    # ------------------------------------------------------------------
    def _role_read_first_doc(self, role_name: str) -> str:
        owner = self._role_owner(role_name) or ""
        if owner == "Claude":
            return "CLAUDE.md"
        if owner == "Gemini":
            return "GEMINI.md"
        return "AGENTS.md"

    # ------------------------------------------------------------------
    def _role_pane_target(self, role_name: str) -> str:
        owner = self._role_owner(role_name)
        if not owner:
            return ""
        return str(self.agent_pane_targets.get(owner) or "")

    # ------------------------------------------------------------------
    def _role_pane_type(self, role_name: str) -> str:
        lane = self._lane_config(self._role_owner(role_name))
        pane_type = str((lane or {}).get("pane_type") or "").strip()
        return pane_type or "claude"

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
    @staticmethod
    def _iso_utc(ts: float) -> str:
        return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat().replace("+00:00", "Z")

    # ------------------------------------------------------------------
    def _write_current_run_pointer(self) -> None:
        if not self._runtime_export_enabled:
            return
        data = {
            "run_id": self.run_id,
            "status_path": self._repo_relative(self.run_status_path),
            "events_path": self._repo_relative(self.run_events_path),
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
        if state == WatcherTurnState.CLAUDE_ACTIVE:
            return self._role_owner("implement") or ""
        if state in (WatcherTurnState.CODEX_VERIFY, WatcherTurnState.CODEX_FOLLOWUP):
            return self._role_owner("verify") or ""
        if state == WatcherTurnState.GEMINI_ADVISORY:
            return self._role_owner("advisory") or ""
        return ""

    # ------------------------------------------------------------------
    def _implement_control_should_surface_working(self, active_control: Optional[ControlSignal]) -> bool:
        if active_control is None:
            return False
        if active_control.status != "implement" or active_control.control_seq < 0:
            return False
        implement_target = self._role_pane_target("implement")
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
        implement_lane = self._role_owner("implement") or ""
        implement_live = self._implement_control_should_surface_working(active_control)
        seen_names: set[str] = set()
        lane_configs = self.runtime_lane_configs or [
            {"name": "Claude", "enabled": True},
            {"name": "Codex", "enabled": True},
            {"name": "Gemini", "enabled": True},
        ]
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
        for fallback_name in ("Claude", "Codex", "Gemini"):
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
        control_file = ""
        control_seq = self._turn_active_control_seq
        control_status = "none"
        control_updated_at = ""
        if active_control is not None:
            control_file = f".pipeline/{active_control.path.name}"
            control_seq = active_control.control_seq
            control_status = active_control.status
            control_updated_at = self._iso_utc(active_control.mtime)
        elif self._turn_active_control_file:
            control_file = f".pipeline/{self._turn_active_control_file}"
        data = {
            "schema_version": 1,
            "run_id": self.run_id,
            "state": "RUNNING",
            "runtime_state": "RUNNING",
            "turn_state": self._current_turn_state.value,
            "degraded_reason": "",
            "control": {
                "active_control_file": control_file,
                "active_control_seq": control_seq,
                "active_control_status": control_status,
                "active_control_updated_at": control_updated_at,
            },
            "lanes": self._build_lane_statuses(now_iso),
            "last_receipt_id": "",
            "last_heartbeat_at": now_iso,
            "updated_at": now_iso,
        }
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
        self._current_turn_state = new_state
        self._turn_entered_at = now
        self._turn_active_control_file = active_control_file
        self._turn_active_control_seq = active_control_seq
        if new_state == WatcherTurnState.CLAUDE_ACTIVE:
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
                "reason": reason,
                "active_control_file": active_control_file,
                "active_control_seq": active_control_seq,
            },
        )
        # Write turn_state.json atomically
        data: dict[str, object] = {
            "state": new_state.value,
            "entered_at": now,
            "reason": reason,
            "active_control_file": active_control_file,
            "active_control_seq": active_control_seq,
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
                "reason": reason,
                "active_control_file": active_control_file,
                "active_control_seq": active_control_seq,
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
    def _get_valid_control_signal(self, path: Path, expected_status: str, kind: str) -> Optional[ControlSignal]:
        if kind in {"gemini_request", "gemini_advice"} and not self._advisory_enabled():
            return None
        if kind == "operator_request" and not self._operator_stop_enabled():
            return None
        status = self._read_status_from_path(path)
        if status != expected_status:
            return None
        mtime = self._get_path_mtime(path)
        if mtime == 0.0:
            return None
        return ControlSignal(
            kind=kind,
            path=path,
            status=status,
            mtime=mtime,
            sig=self._get_path_sig(path),
            control_seq=self._read_control_seq_from_path(path),
        )

    # ------------------------------------------------------------------
    def _get_active_control_signal(self) -> Optional[ControlSignal]:
        candidates = [
            self._get_valid_control_signal(self.claude_handoff_path, "implement", "claude_handoff"),
            self._get_valid_control_signal(self.gemini_request_path, "request_open", "gemini_request"),
            self._get_valid_control_signal(self.gemini_advice_path, "advice_ready", "gemini_advice"),
            self._get_valid_control_signal(self.operator_request_path, "needs_operator", "operator_request"),
        ]
        valid = [candidate for candidate in candidates if candidate is not None]
        if not valid:
            return None
        return max(
            valid,
            key=lambda signal: (
                signal.control_seq >= 0,
                signal.control_seq,
                signal.mtime,
                signal.path.name,
            ),
        )

    # ------------------------------------------------------------------
    def _get_next_control_seq(self) -> int:
        candidates = [
            self._get_valid_control_signal(self.claude_handoff_path, "implement", "claude_handoff"),
            self._get_valid_control_signal(self.gemini_request_path, "request_open", "gemini_request"),
            self._get_valid_control_signal(self.gemini_advice_path, "advice_ready", "gemini_advice"),
            self._get_valid_control_signal(self.operator_request_path, "needs_operator", "operator_request"),
        ]
        seqs = [candidate.control_seq for candidate in candidates if candidate is not None and candidate.control_seq >= 0]
        if not seqs:
            return 1
        return max(seqs) + 1

    # ------------------------------------------------------------------
    def _is_active_control(self, path: Path, expected_status: str) -> bool:
        active = self._get_active_control_signal()
        return active is not None and active.path == path and active.status == expected_status

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
        for path in self.state_dir.glob("*.json"):
            if path.name == "turn_state.json":
                continue
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
        referenced_work_paths = sorted(
            {
                self._normalize_artifact_path(match.group(1))
                for match in WORK_PATH_RE.finditer(control_text)
                if self._normalize_artifact_path(match.group(1))
            }
        )
        if not referenced_work_paths:
            return None
        verified_work_paths = self._verified_work_paths()
        unresolved = [path for path in referenced_work_paths if path not in verified_work_paths]
        if unresolved:
            return None
        return {
            "control_file": "operator_request.md",
            "control_seq": self._read_control_seq_from_path(self.operator_request_path),
            "reason": "verified_blockers_resolved",
            "resolved_work_paths": referenced_work_paths,
        }

    # ------------------------------------------------------------------
    def _operator_gate_marker(self) -> Optional[dict[str, object]]:
        if not self._is_active_control(self.operator_request_path, "needs_operator"):
            return None
        try:
            control_text = self.operator_request_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        decision = classify_operator_candidate(
            control_text,
            control_path=str(self.operator_request_path),
            control_seq=self._read_control_seq_from_path(self.operator_request_path),
            control_mtime=self._get_path_mtime(self.operator_request_path),
            idle_stable=(
                not self._latest_work_needs_verify_broad()
                and not self._is_active_control(self.claude_handoff_path, "implement")
                and self._get_gemini_request_mtime() == 0.0
                and self._get_gemini_advice_mtime() == 0.0
            ),
        )
        if bool(decision.get("operator_eligible")):
            return None
        return {
            "control_file": "operator_request.md",
            "control_seq": self._read_control_seq_from_path(self.operator_request_path),
            "reason": str(decision.get("block_reason") or ""),
            "mode": str(decision.get("suppressed_mode") or ""),
            "routed_to": str(decision.get("routed_to") or ""),
            "suppress_operator_until": str(decision.get("suppress_operator_until") or ""),
            "fingerprint": str(decision.get("fingerprint") or ""),
        }

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
        stale = self._stale_operator_control_marker()
        if stale is not None:
            return stale
        return self._idle_operator_retriage_marker()

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
    def _is_canonical_round_note(self, root: Path, path: Path) -> bool:
        try:
            rel = path.relative_to(root)
        except ValueError:
            return False
        if len(rel.parts) < 3:
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
    def _get_same_day_verify_dir(self, work_path: Optional[Path]) -> Path:
        if work_path is None:
            return self.verify_dir
        try:
            rel = work_path.relative_to(self.watch_dir)
        except ValueError:
            return self.verify_dir
        if len(rel.parts) >= 2:
            return self.verify_dir / rel.parts[0] / rel.parts[1]
        return self.verify_dir

    # ------------------------------------------------------------------
    def _build_verify_feedback_sigs(self, job: JobState) -> tuple[str, str]:
        work_path = Path(job.artifact_path)
        control_sig = compute_multi_file_sig(self.completion_paths)
        verify_dir = self._get_same_day_verify_dir(work_path)
        verify_sig = compute_md_tree_sig(verify_dir)
        return control_sig, verify_sig

    # ------------------------------------------------------------------
    def _build_verify_receipt_state(self, job: JobState) -> tuple[str, float]:
        work_path = Path(job.artifact_path)
        latest_verify = self._get_latest_same_day_verify_path(work_path)
        if latest_verify is None:
            return "", 0.0
        return self._repo_relative(latest_verify), self._get_path_mtime(latest_verify)

    # ------------------------------------------------------------------
    def _infer_gemini_report_hint(self, work_path: Optional[Path]) -> str:
        date_prefix = time.strftime("%Y-%m-%d")
        if work_path is not None:
            stem = work_path.stem
            if len(stem) >= 10 and stem[4] == "-" and stem[7] == "-":
                date_prefix = stem[:10]
        return f"{date_prefix}-<slug>.md"

    # ------------------------------------------------------------------
    def _build_runtime_prompt_context(self, work_path: Optional[Path] = None) -> dict[str, str]:
        latest_work = work_path or self._get_latest_work_path()
        latest_verify = self._get_latest_same_day_verify_path(latest_work)
        gemini_report_hint = self._infer_gemini_report_hint(latest_work)
        gemini_report_path = self.report_gemini_dir / gemini_report_hint
        active_control = self._get_active_control_signal()
        return {
            "latest_work_path": self._repo_relative(latest_work),
            "latest_verify_path": self._repo_relative(latest_verify),
            "gemini_report_dir": self._repo_relative(self.report_gemini_dir) + "/",
            "gemini_report_hint": gemini_report_hint,
            "gemini_report_path": self._repo_relative(gemini_report_path),
            "claude_handoff_path": self._repo_relative(self.claude_handoff_path),
            "gemini_request_path": self._repo_relative(self.gemini_request_path),
            "gemini_advice_path": self._repo_relative(self.gemini_advice_path),
            "operator_request_path": self._repo_relative(self.operator_request_path),
            "latest_work_mention": self._path_mention(latest_work),
            "latest_verify_mention": self._path_mention(latest_verify),
            "gemini_request_mention": self._path_mention(self.gemini_request_path),
            "gemini_advice_mention": self._path_mention(self.gemini_advice_path),
            "active_control_path": self._repo_relative(active_control.path if active_control else None),
            "active_control_status": active_control.status if active_control else "none",
            "active_control_sig": active_control.sig if active_control else "",
            "active_control_seq": str(active_control.control_seq if active_control and active_control.control_seq >= 0 else "none"),
            "next_control_seq": str(self._get_next_control_seq()),
            "runtime_enabled_lanes": ",".join(self.runtime_adapter.get("enabled_lanes") or []),
            "runtime_implement_owner": self._role_owner("implement") or "none",
            "runtime_verify_owner": self._role_owner("verify") or "none",
            "runtime_advisory_owner": self._role_owner("advisory") or "none",
            "runtime_implement_read_first_doc": self._role_read_first_doc("implement"),
            "runtime_verify_read_first_doc": self._role_read_first_doc("verify"),
            "runtime_advisory_read_first_doc": self._role_read_first_doc("advisory"),
            "runtime_advisory_enabled": "true" if self.runtime_controls.get("advisory_enabled") else "false",
            "runtime_operator_stop_enabled": "true" if self.runtime_controls.get("operator_stop_enabled") else "false",
            "runtime_session_arbitration_enabled": "true" if self.runtime_controls.get("session_arbitration_enabled") else "false",
        }

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
    def _verify_scope_hint_for_work(self, work_path: Optional[Path]) -> tuple[str, str]:
        changed_paths = self._extract_changed_file_paths_from_round_note(work_path)
        if changed_paths and all(path.endswith(".md") for path in changed_paths):
            return (
                "docs_only",
                "- docs-only truth-sync round detected from `## 변경 파일`\n"
                "- re-check the changed markdown docs against current code/docs truth first\n"
                "- prefer `git diff --check` and direct file comparison; do not widen into unit or Playwright reruns unless the work note itself claims code/test/runtime changes\n"
                "- if truthful, keep `/verify` concise and move directly to one exact next slice",
            )
        return (
            "standard",
            "- standard verification round\n"
            "- rerun only the narrowest checks actually needed for the claimed changes",
        )

    # ------------------------------------------------------------------
    def _build_verify_prompt_context(self, job: JobState) -> dict[str, str]:
        artifact = Path(job.artifact_path)
        verify_scope_label, verify_scope_hint = self._verify_scope_hint_for_work(artifact)
        return {
            "artifact_path": job.artifact_path,
            "verify_scope_label": verify_scope_label,
            "verify_scope_hint": verify_scope_hint,
            **self._build_runtime_prompt_context(artifact),
        }

    # ------------------------------------------------------------------
    def _format_runtime_prompt(self, template: str, work_path: Optional[Path] = None) -> str:
        return _normalize_prompt_text(template.format(**self._build_runtime_prompt_context(work_path)))

    # ------------------------------------------------------------------
    def _build_implement_prompt_context(self, handoff_path: Optional[Path] = None) -> dict[str, str]:
        handoff = handoff_path or self.claude_handoff_path
        return {
            **self._build_runtime_prompt_context(),
            "active_handoff_path": self._repo_relative(handoff),
            "active_handoff_sha": self._get_path_sha256(handoff),
        }

    # ------------------------------------------------------------------
    def _format_implement_prompt(self, handoff_path: Optional[Path] = None) -> str:
        return _normalize_prompt_text(self.implement_prompt.format(**self._build_implement_prompt_context(handoff_path)))

    # ------------------------------------------------------------------
    def _format_verify_triage_prompt(self, signal: dict[str, object]) -> str:
        context = {
            **self._build_implement_prompt_context(self.claude_handoff_path),
            "blocked_source": str(signal.get("source", "sentinel")),
            "blocked_reason": str(signal.get("reason", "implement_blocked")),
            "blocked_fingerprint": str(signal.get("fingerprint", "")),
            "blocked_excerpt": "\n".join(
                f"- {line}" for line in signal.get("excerpt_lines", [])
            ) or "- (없음)",
        }
        return _normalize_prompt_text(self.verify_triage_prompt.format(**context))

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
        try:
            with path.open() as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("CONTROL_SEQ:"):
                        raw = stripped.split(":", 1)[1].strip()
                        try:
                            value = int(raw)
                        except ValueError:
                            return -1
                        return value if value >= 0 else -1
        except OSError:
            return -1
        return -1

    # ------------------------------------------------------------------
    def _get_latest_implement_handoff(self) -> tuple[Optional[Path], float]:
        """Claude가 읽을 최신 implement handoff 슬롯을 고른다."""
        if not self._is_active_control(self.claude_handoff_path, "implement"):
            return None, 0.0
        return self.claude_handoff_path, self._get_path_mtime(self.claude_handoff_path)

    # ------------------------------------------------------------------
    def _get_pending_operator_mtime(self) -> float:
        """operator_request가 실제 pending stop이면 mtime을 반환한다."""
        if self._stale_operator_control_marker() is not None:
            return 0.0
        if self._operator_gate_marker() is not None:
            return 0.0
        if self._is_active_control(self.operator_request_path, "needs_operator"):
            return self._get_path_mtime(self.operator_request_path)
        return 0.0

    # ------------------------------------------------------------------
    def _get_gemini_request_mtime(self) -> float:
        if self._is_active_control(self.gemini_request_path, "request_open"):
            return self._get_path_mtime(self.gemini_request_path)
        return 0.0

    # ------------------------------------------------------------------
    def _get_gemini_advice_mtime(self) -> float:
        if self._is_active_control(self.gemini_advice_path, "advice_ready"):
            return self._get_path_mtime(self.gemini_advice_path)
        return 0.0

    # ------------------------------------------------------------------
    def _get_pending_gemini_request_mtime(self) -> float:
        return self._get_gemini_request_mtime()

    # ------------------------------------------------------------------
    def _get_pending_gemini_advice_mtime(self) -> float:
        return self._get_gemini_advice_mtime()

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
    def _latest_work_needs_verify(self) -> bool:
        """
        최신 canonical /work가 same-day 최신 /verify보다 앞서 있으면 True.
        handoff 파일 mtime보다 product truth를 우선해 Codex가 먼저 따라붙어야 하는지 판단한다.
        """
        latest_work = self._get_latest_work_path()
        if latest_work is None:
            return False

        latest_verify = self._get_latest_same_day_verify_path(latest_work)
        work_mtime = self._get_path_mtime(latest_work)
        verify_mtime = self._get_path_mtime(latest_verify) if latest_verify else 0.0
        return work_mtime > verify_mtime

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
        """Like _latest_work_needs_verify but includes metadata-only notes.

        For verify-needed judgment, all canonical round notes count.
        Metadata-only filtering is only for dispatch prompt content.
        """
        latest_work = self._find_latest_md_broad(self.watch_dir)
        if latest_work is None:
            return False
        latest_verify = self._get_latest_same_day_verify_path(latest_work)
        work_mtime = self._get_path_mtime(latest_work)
        verify_mtime = self._get_path_mtime(latest_verify) if latest_verify else 0.0
        return work_mtime > verify_mtime

    # ------------------------------------------------------------------
    def _resolve_turn(self) -> str:
        """Resolve which agent should act next.

        Returns one of: "operator", "gemini", "codex_followup", "codex", "claude", "idle".
        This is a pure query — it does not trigger transitions or side effects.
        Used by both initial turn and rolling turn decisions.
        """
        operator_recovery = self._operator_control_recovery_marker()
        operator_gate = self._operator_gate_marker()

        # 1. operator_request active → operator
        if (
            self._is_active_control(self.operator_request_path, "needs_operator")
            and operator_recovery is None
            and operator_gate is None
        ):
            return "operator"

        # 2. gemini_request active → gemini
        if self._is_active_control(self.gemini_request_path, "request_open"):
            return "gemini"

        # 3. gemini_advice active → codex_followup
        if self._is_active_control(self.gemini_advice_path, "advice_ready"):
            return "codex_followup"

        # 4. handoff active + implement, but verify_pending or verify_active → codex first
        handoff_active = self._is_active_control(self.claude_handoff_path, "implement")
        verify_pending = self._latest_work_needs_verify_broad()
        verify_active = self._claude_handoff_verify_active()
        if handoff_active and (verify_pending or verify_active):
            return "codex"

        # 5. work needs verify (no handoff) → codex
        if verify_pending:
            return "codex"

        # 6. handoff active and dispatchable → claude (unless cooldown)
        if handoff_active and not self._is_idle_release_cooldown_active():
            return "claude"

        # 6.5. stale operator stop cleared → codex follow-up
        if operator_recovery is not None:
            return "codex_followup"

        # 6.6. gated operator candidate → Codex follow-up or quiet hibernate
        if operator_gate is not None and str(operator_gate.get("routed_to") or "") != "hibernate":
            return "codex_followup"

        # 7. fallback
        return "idle"

    # ------------------------------------------------------------------
    def _check_claude_idle_timeout(self) -> None:
        """Check if Claude has been idle too long and transition to IDLE if so."""
        if self._current_turn_state != WatcherTurnState.CLAUDE_ACTIVE:
            return

        target = self._role_pane_target("implement")
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
        current_snapshot = self._get_work_tree_snapshot()
        if current_snapshot != self._work_baseline_snapshot:
            self._last_progress_at = now
            return

        # No progress — check timeout
        elapsed = now - self._last_progress_at
        if elapsed < self.claude_active_idle_timeout_sec:
            return

        # Final guard: pane must look idle too
        if not _pane_text_is_idle(pane_text):
            return

        log.warning(
            "claude idle timeout: %.0fs since last progress, transitioning to IDLE",
            elapsed,
        )
        # Record cooldown to prevent immediate re-dispatch of same handoff
        self._last_idle_release_handoff_sig = self._get_path_sig(self.claude_handoff_path)
        self._last_idle_release_at = now
        self._transition_turn(WatcherTurnState.IDLE, "claude_idle_timeout")

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
        target = self._role_pane_target("verify")
        if not target:
            return
        codex_snapshot = _capture_pane_text(target)
        if not _pane_text_is_idle(codex_snapshot):
            return
        self._last_operator_retriage_sig = operator_sig
        self._clear_claude_blocked_state("operator_wait_idle_retriage")
        self._transition_turn(
            WatcherTurnState.CODEX_FOLLOWUP,
            "operator_wait_idle_retriage",
            active_control_file="operator_request.md",
            active_control_seq=int(marker.get("control_seq") or -1),
        )
        self._log_raw(
            "operator_request_idle_retriage",
            str(self.operator_request_path),
            "turn_signal",
            marker,
        )
        self._notify_codex_operator_retriage("operator_wait_idle_retriage", marker)

    # ------------------------------------------------------------------
    def _is_idle_release_cooldown_active(self) -> bool:
        """True if the same handoff was recently released from idle timeout."""
        if not self._last_idle_release_handoff_sig:
            return False
        current_sig = self._get_path_sig(self.claude_handoff_path)
        if current_sig != self._last_idle_release_handoff_sig:
            return False
        elapsed = time.time() - self._last_idle_release_at
        return elapsed < self.claude_active_idle_timeout_sec

    # ------------------------------------------------------------------
    def _notify_claude(self, reason: str, handoff_path: Optional[Path] = None) -> None:
        """Claude pane에 다음 작업 프롬프트 전송."""
        target = self._role_pane_target("implement")
        pane_type = self._role_pane_type("implement")
        if not target:
            log.warning("notify_claude skipped: no implement owner target")
            return
        log.info("notify_claude: reason=%s target=%s owner=%s", reason, target, self._role_owner("implement"))
        self._log_raw(
            "claude_notify",
            str(handoff_path or self.claude_handoff_path),
            "turn_signal",
            {"reason": reason},
        )
        prompt = self._format_implement_prompt(handoff_path)
        tmux_send_keys(target, prompt, self.dry_run, pane_type=pane_type)

    # ------------------------------------------------------------------
    def _notify_gemini(self, reason: str) -> None:
        """Gemini pane에 arbitration 프롬프트 전송."""
        if not self._advisory_enabled():
            log.info("notify_gemini skipped: advisory disabled")
            self._log_raw(
                "gemini_notify_skipped",
                str(self.gemini_request_path),
                "turn_signal",
                {"reason": "runtime_advisory_disabled"},
            )
            return
        target = self._role_pane_target("advisory")
        pane_type = self._role_pane_type("advisory")
        if not target:
            log.info("notify_gemini skipped: no advisory owner target")
            self._log_raw(
                "gemini_notify_skipped",
                str(self.gemini_request_path),
                "turn_signal",
                {"reason": "missing_advisory_target"},
            )
            return
        log.info("notify_gemini: reason=%s target=%s owner=%s", reason, target, self._role_owner("advisory"))
        self._log_raw(
            "gemini_notify",
            str(self.gemini_request_path),
            "turn_signal",
            {"reason": reason},
        )
        prompt = self._format_runtime_prompt(self.advisory_prompt)
        tmux_send_keys(target, prompt, self.dry_run, pane_type=pane_type)

    # ------------------------------------------------------------------
    def _notify_codex_followup(self, reason: str) -> None:
        """Gemini advice 이후 Codex가 최종 결론을 쓰도록 재호출."""
        target = self._role_pane_target("verify")
        pane_type = self._role_pane_type("verify")
        if not target:
            log.warning("notify_codex_followup skipped: no verify owner target")
            return
        log.info("notify_codex_followup: reason=%s target=%s owner=%s", reason, target, self._role_owner("verify"))
        self._log_raw(
            "codex_followup_notify",
            str(self.gemini_advice_path),
            "turn_signal",
            {"reason": reason},
        )
        prompt = self._format_runtime_prompt(self.followup_prompt)
        tmux_send_keys(target, prompt, self.dry_run, pane_type=pane_type)

    # ------------------------------------------------------------------
    def _format_control_recovery_prompt(self, marker: dict[str, object]) -> str:
        resolved_paths = list(marker.get("resolved_work_paths") or [])
        context = {
            **self._build_runtime_prompt_context(),
            "stale_control_path": ".pipeline/operator_request.md",
            "stale_control_seq": str(marker.get("control_seq") or "none"),
            "stale_control_reason": str(marker.get("reason") or "verified_blockers_resolved"),
            "stale_control_resolved_work_paths": "\n".join(f"- {path}" for path in resolved_paths) or "- (없음)",
        }
        return _normalize_prompt_text(self.control_recovery_prompt.format(**context))

    # ------------------------------------------------------------------
    def _format_operator_retriage_prompt(self, marker: dict[str, object]) -> str:
        context = {
            **self._build_runtime_prompt_context(),
            "stale_control_seq": str(marker.get("control_seq") or "none"),
            "stale_control_reason": str(marker.get("reason") or "operator_wait_idle_retriage"),
            "operator_wait_age_sec": str(marker.get("operator_wait_age_sec") or "0"),
        }
        return _normalize_prompt_text(self.operator_retriage_prompt.format(**context))

    # ------------------------------------------------------------------
    def _notify_codex_control_recovery(self, reason: str, marker: dict[str, object]) -> None:
        """stale operator stop 해소 뒤 Codex가 다음 control을 재결정하도록 호출."""
        target = self._role_pane_target("verify")
        pane_type = self._role_pane_type("verify")
        if not target:
            log.warning("notify_codex_control_recovery skipped: no verify owner target")
            return
        log.info("notify_codex_control_recovery: reason=%s target=%s owner=%s", reason, target, self._role_owner("verify"))
        self._log_raw(
            "codex_control_recovery_notify",
            str(self.operator_request_path),
            "turn_signal",
            {"reason": reason, **marker},
        )
        prompt = self._format_control_recovery_prompt(marker)
        tmux_send_keys(target, prompt, self.dry_run, pane_type=pane_type)

    # ------------------------------------------------------------------
    def _notify_codex_operator_retriage(self, reason: str, marker: dict[str, object]) -> None:
        target = self._role_pane_target("verify")
        pane_type = self._role_pane_type("verify")
        if not target:
            log.warning("notify_codex_operator_retriage skipped: no verify owner target")
            return
        log.info("notify_codex_operator_retriage: reason=%s target=%s owner=%s", reason, target, self._role_owner("verify"))
        self._log_raw(
            "codex_operator_retriage_notify",
            str(self.operator_request_path),
            "turn_signal",
            {"reason": reason, **marker},
        )
        prompt = self._format_operator_retriage_prompt(marker)
        tmux_send_keys(target, prompt, self.dry_run, pane_type=pane_type)

    # ------------------------------------------------------------------
    def _notify_codex_blocked_triage(self, signal: dict[str, object], reason: str) -> bool:
        target = self._role_pane_target("verify")
        pane_type = self._role_pane_type("verify")
        if not target:
            return False
        handoff_sha = self._get_path_sha256(self.claude_handoff_path)
        codex_snapshot = _capture_pane_text(target)
        if not _pane_text_is_idle(codex_snapshot):
            self._log_raw(
                "codex_blocked_triage_skipped",
                str(self.claude_handoff_path),
                "turn_signal",
                {"reason": "codex_busy", "blocked_reason": signal.get("reason", "implement_blocked")},
            )
            return False

        prompt = self._format_verify_triage_prompt(signal)
        self._log_raw(
            "codex_blocked_triage_notify",
            str(self.claude_handoff_path),
            "turn_signal",
            {
                "reason": reason,
                "blocked_reason": signal.get("reason", "implement_blocked"),
                "blocked_source": signal.get("source", "sentinel"),
                "blocked_fingerprint": signal.get("fingerprint", ""),
                "handoff_sha": handoff_sha,
            },
        )
        ok = tmux_send_keys(target, prompt, self.dry_run, pane_type=pane_type)
        if ok:
            self._last_claude_blocked_fingerprint = str(signal.get("fingerprint", ""))
            self._clear_session_arbitration_draft("claude_blocked_triage")
        return ok

    # ------------------------------------------------------------------
    def _claude_handoff_verify_active(self) -> bool:
        return self.lease.is_active("slot_verify")

    # ------------------------------------------------------------------
    def _claude_handoff_dispatch_state(self, handoff_mtime: float) -> dict[str, bool]:
        operator_blocked = self._operator_blocks_handoff(handoff_mtime)
        pending_verify = self._latest_work_needs_verify()
        verify_active = self._claude_handoff_verify_active()
        return {
            "operator_blocked": operator_blocked,
            "pending_verify": pending_verify,
            "verify_active": verify_active,
            "dispatchable": not operator_blocked and not pending_verify and not verify_active,
        }

    # ------------------------------------------------------------------
    def _flush_pending_claude_handoff(self) -> None:
        """If verify lease just released and handoff is waiting, transition to Claude."""
        if self._current_turn_state not in (
            WatcherTurnState.CODEX_VERIFY,
            WatcherTurnState.CODEX_FOLLOWUP,
            WatcherTurnState.IDLE,
        ):
            return
        if self._claude_handoff_verify_active():
            return  # verify still running

        # Re-resolve: maybe Claude can go now
        turn = self._resolve_turn()
        if turn == "claude":
            handoff_path, _ = self._get_latest_implement_handoff()
            active_control = self._get_active_control_signal()
            seq = active_control.control_seq if active_control else -1
            if seq < self._turn_active_control_seq:
                return  # stale
            self._transition_turn(
                WatcherTurnState.CLAUDE_ACTIVE,
                "verify_lease_released",
                active_control_file="claude_handoff.md",
                active_control_seq=seq,
            )
            self._work_baseline_snapshot = self._get_work_tree_snapshot()
            self._clear_claude_blocked_state("claude_handoff_pending_release")
            self._notify_claude("verify_lease_released", handoff_path)

    # ------------------------------------------------------------------
    def _check_pipeline_signal_updates(self) -> None:
        """handoff/operator 슬롯 시그니처를 확인하고 Claude 라우팅을 결정한다."""
        active_control = self._get_active_control_signal()

        operator_sig = self._get_path_sig(self.operator_request_path)
        if operator_sig and operator_sig != self._last_operator_request_sig:
            self._last_operator_request_sig = operator_sig
            status = self._read_status_from_path(self.operator_request_path) or "missing"
            operator_recovery = self._operator_control_recovery_marker()
            operator_gate = self._operator_gate_marker()
            if (
                active_control is not None
                and active_control.path == self.operator_request_path
                and active_control.control_seq >= self._turn_active_control_seq
            ):
                if operator_recovery is not None:
                    recovery_reason = str(operator_recovery.get("reason") or "verified_blockers_resolved")
                    log.info("operator request updated but recoverable: Codex follow-up resumes (%s)", recovery_reason)
                    self._clear_claude_blocked_state(recovery_reason)
                    self._transition_turn(
                        WatcherTurnState.CODEX_FOLLOWUP,
                        recovery_reason,
                        active_control_seq=active_control.control_seq,
                    )
                    if recovery_reason == "operator_wait_idle_retriage":
                        self._last_operator_retriage_sig = operator_sig
                    self._log_raw(
                        "operator_request_stale_ignored",
                        str(self.operator_request_path),
                        "turn_signal",
                        {"status": status, **operator_recovery},
                    )
                    if recovery_reason == "operator_wait_idle_retriage":
                        self._notify_codex_operator_retriage(recovery_reason, operator_recovery)
                    else:
                        self._notify_codex_control_recovery("operator_request_stale_ignored", operator_recovery)
                    return
                if operator_gate is not None:
                    gate_reason = str(operator_gate.get("reason") or "operator_candidate_pending")
                    self._clear_claude_blocked_state(gate_reason)
                    self._log_raw(
                        "operator_request_gated",
                        str(self.operator_request_path),
                        "turn_signal",
                        {"status": status, **operator_gate},
                    )
                    if str(operator_gate.get("routed_to") or "") == "hibernate":
                        self._transition_turn(WatcherTurnState.IDLE, "operator_request_gated_hibernate")
                        return
                    self._last_operator_retriage_sig = operator_sig
                    self._transition_turn(
                        WatcherTurnState.CODEX_FOLLOWUP,
                        "operator_request_gated",
                        active_control_seq=active_control.control_seq,
                    )
                    self._notify_codex_operator_retriage("operator_request_gated", operator_gate)
                    return
                log.info("operator request updated: STATUS=needs_operator → Claude notify 차단")
                self._clear_claude_blocked_state("operator_request_pending")
                self._transition_turn(
                    WatcherTurnState.OPERATOR_WAIT,
                    "operator_request_updated",
                    active_control_file="operator_request.md",
                    active_control_seq=active_control.control_seq,
                )
                self._log_raw(
                    "operator_request_pending",
                    str(self.operator_request_path),
                    "turn_signal",
                    {"status": status},
                )
            else:
                self._log_raw(
                    "operator_request_stale",
                    str(self.operator_request_path),
                    "turn_signal",
                    {
                        "status": status,
                        "active_control": active_control.kind if active_control else "none",
                    },
                )

        gemini_request_sig = self._get_path_sig(self.gemini_request_path)
        if gemini_request_sig and gemini_request_sig != self._last_gemini_request_sig:
            self._last_gemini_request_sig = gemini_request_sig
            request_mtime = self._get_pending_gemini_request_mtime()
            status = self._read_status_from_path(self.gemini_request_path) or "missing"
            gemini_req_control_seq = active_control.control_seq if active_control and active_control.path == self.gemini_request_path else -1
            if request_mtime > 0.0 and self._get_pending_operator_mtime() == 0.0 and gemini_req_control_seq >= self._turn_active_control_seq:
                log.info("gemini request updated: STATUS=request_open → Gemini 차례")
                self._clear_claude_blocked_state("gemini_request_pending")
                self._transition_turn(
                    WatcherTurnState.GEMINI_ADVISORY,
                    "gemini_request_updated",
                    active_control_file="gemini_request.md",
                    active_control_seq=gemini_req_control_seq,
                )
                self._notify_gemini("gemini_request_updated")
            else:
                self._log_raw(
                    "gemini_notify_skipped",
                    str(self.gemini_request_path),
                    "turn_signal",
                    {
                        "status": status,
                        "active_control": active_control.kind if active_control else "none",
                    },
                )

        gemini_advice_sig = self._get_path_sig(self.gemini_advice_path)
        if gemini_advice_sig and gemini_advice_sig != self._last_gemini_advice_sig:
            self._last_gemini_advice_sig = gemini_advice_sig
            advice_mtime = self._get_pending_gemini_advice_mtime()
            status = self._read_status_from_path(self.gemini_advice_path) or "missing"
            gemini_adv_control_seq = active_control.control_seq if active_control and active_control.path == self.gemini_advice_path else -1
            if advice_mtime > 0.0 and self._get_pending_operator_mtime() == 0.0 and gemini_adv_control_seq >= self._turn_active_control_seq:
                log.info("gemini advice updated: STATUS=advice_ready → Codex follow-up")
                self._clear_claude_blocked_state("gemini_advice_pending")
                self._transition_turn(
                    WatcherTurnState.CODEX_FOLLOWUP,
                    "gemini_advice_updated",
                    active_control_file="gemini_advice.md",
                    active_control_seq=gemini_adv_control_seq,
                )
                self._notify_codex_followup("gemini_advice_updated")
            else:
                self._log_raw(
                    "codex_followup_notify_skipped",
                    str(self.gemini_advice_path),
                    "turn_signal",
                    {
                        "status": status,
                        "active_control": active_control.kind if active_control else "none",
                    },
                )

        handoff_sig = self._get_path_sig(self.claude_handoff_path)
        if handoff_sig and handoff_sig != self._last_claude_handoff_sig:
            self._last_claude_handoff_sig = handoff_sig
            status = self._read_status_from_path(self.claude_handoff_path) or "missing"
            handoff_mtime = self._get_path_mtime(self.claude_handoff_path)
            dispatch_state = self._claude_handoff_dispatch_state(handoff_mtime)
            handoff_seq = active_control.control_seq if active_control and active_control.path == self.claude_handoff_path else -1
            if (
                active_control is not None
                and active_control.path == self.claude_handoff_path
                and status == "implement"
                and self._current_turn_state == WatcherTurnState.CLAUDE_ACTIVE
            ):
                log.info("claude handoff updated during active Claude round: defer hot-swap until round exit")
                self._log_raw(
                    "claude_handoff_deferred",
                    str(self.claude_handoff_path),
                    "turn_signal",
                    {
                        "status": status,
                        "active_control_seq": handoff_seq,
                        "current_turn_state": self._current_turn_state.value,
                    },
                )
            elif (
                active_control is not None
                and active_control.path == self.claude_handoff_path
                and status == "implement"
                and dispatch_state["dispatchable"]
                and handoff_seq >= self._turn_active_control_seq
            ):
                log.info("claude handoff updated: STATUS=implement → Claude 차례")
                self._clear_claude_blocked_state("claude_handoff_updated")
                self._transition_turn(
                    WatcherTurnState.CLAUDE_ACTIVE,
                    "claude_handoff_updated",
                    active_control_file="claude_handoff.md",
                    active_control_seq=handoff_seq,
                )
                self._work_baseline_snapshot = self._get_work_tree_snapshot()
                self._notify_claude("claude_handoff_updated", self.claude_handoff_path)
            else:
                if (
                    active_control is not None
                    and active_control.path == self.claude_handoff_path
                    and status == "implement"
                    and dispatch_state["verify_active"]
                ):
                    self._clear_claude_blocked_state("claude_handoff_pending_release")
                log.info("claude handoff updated: STATUS=%s → Claude notify 건너뜀", status)
                self._log_raw(
                    "claude_notify_skipped",
                    str(self.claude_handoff_path),
                    "turn_signal",
                    {
                        "status": status,
                        "operator_blocked": dispatch_state["operator_blocked"],
                        "pending_verify": dispatch_state["pending_verify"],
                        "verify_active": dispatch_state["verify_active"],
                        "active_control": active_control.kind if active_control else "none",
                    },
                )

        self._flush_pending_claude_handoff()

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

        context = self._build_runtime_prompt_context()
        reasons = signal["reasons"]
        excerpt_lines = signal["excerpt_lines"]
        reason_lines = "\n".join(f"- {reason}" for reason in reasons)
        excerpt_block = "\n".join(f"> {line}" for line in excerpt_lines) or "> (없음)"
        body = (
            "STATUS: draft_only\n\n"
            "역할:\n"
            "- watcher가 active Claude session의 live side question 신호를 감지해 남긴 non-canonical draft\n"
            "- 이 파일은 자동 실행 슬롯이 아니며 watcher와 Claude/Gemini는 이 파일만으로 dispatch하지 않음\n"
            "- Codex가 보고 short lane reply로 끝낼지, `.pipeline/gemini_request.md`로 승격할지 결정해야 함\n\n"
            "감지 이유:\n"
            f"{reason_lines}\n\n"
            "현재 round-start contract:\n"
            f"- `.pipeline/claude_handoff.md`: {context['claude_handoff_path']}\n"
            f"- latest `/work`: {context['latest_work_path']}\n"
            f"- latest `/verify`: {context['latest_verify_path']}\n\n"
            "관찰 excerpt:\n"
            f"{excerpt_block}\n\n"
            "Codex next step:\n"
            "- active session을 mid-session handoff rewrite 없이 처리할지 먼저 판단\n"
            "- 필요하면 Gemini arbitration request를 사람이 검토 가능한 canonical 슬롯으로만 승격\n"
            "- 그렇지 않으면 Claude에게 short lane reply만 전달\n"
        )
        self.session_arbitration_draft_path.write_text(body)
        self._last_session_arbitration_fingerprint = fingerprint
        self._last_session_arbitration_draft_sig = self._get_path_sig(self.session_arbitration_draft_path)
        self._log_raw(
            "session_arbitration_draft_written",
            str(self.session_arbitration_draft_path),
            "claude_session",
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
                "claude_session",
                {"reason": reason},
            )
        self._last_session_arbitration_draft_sig = self._get_path_sig(self.session_arbitration_draft_path)
        self._last_session_arbitration_fingerprint = ""
        self._session_arbitration_snapshot_fingerprints = {}
        self._session_arbitration_snapshot_changed_at = {}

    # ------------------------------------------------------------------
    def _clear_claude_blocked_state(self, reason: str) -> None:
        fingerprint = self._last_claude_blocked_fingerprint
        if fingerprint:
            self._claude_blocked_cooldowns[fingerprint] = (
                time.time() + self.implement_blocked_cooldown_sec
            )
            self._log_raw(
                "claude_blocked_cleared",
                str(self.claude_handoff_path),
                "claude_session",
                {"reason": reason, "blocked_fingerprint": fingerprint},
            )
        self._last_claude_blocked_fingerprint = ""
        self._claude_blocked_snapshot_fingerprints = {}
        self._claude_blocked_snapshot_changed_at = {}

    # ------------------------------------------------------------------
    def _claude_blocked_snapshot_stable_sec(self, snapshot: str) -> float:
        now = time.time()
        fingerprint = hashlib.sha1(snapshot.encode("utf-8")).hexdigest()
        if self._claude_blocked_snapshot_fingerprints.get("claude") != fingerprint:
            self._claude_blocked_snapshot_fingerprints["claude"] = fingerprint
            self._claude_blocked_snapshot_changed_at["claude"] = now
            return 0.0
        changed_at = self._claude_blocked_snapshot_changed_at.get("claude", now)
        return max(0.0, now - changed_at)

    # ------------------------------------------------------------------
    def _check_claude_implement_blocked(self) -> bool:
        handoff_path, _ = self._get_latest_implement_handoff()
        if handoff_path is None:
            self._clear_claude_blocked_state("handoff_inactive")
            return False

        implement_target = self._role_pane_target("implement")
        if not implement_target:
            self._clear_claude_blocked_state("implement_target_missing")
            return False
        claude_snapshot = _capture_pane_text(implement_target)
        handoff_path_rel = self._repo_relative(handoff_path)
        handoff_sha = self._get_path_sha256(handoff_path)

        signal = _extract_claude_implement_blocked_signal(
            claude_snapshot,
            active_handoff_path=handoff_path_rel,
            active_handoff_sha=handoff_sha,
        )
        soft_signal: Optional[dict[str, object]] = None
        if signal is None:
            soft_signal = _extract_claude_completed_handoff_signal(claude_snapshot, active_handoff_sha=handoff_sha)
            if soft_signal is None:
                soft_signal = _extract_claude_forbidden_menu_signal(claude_snapshot, active_handoff_sha=handoff_sha)
            if (
                soft_signal is not None
                and self._claude_blocked_snapshot_stable_sec(claude_snapshot) >= self.implement_blocked_settle_sec
            ):
                signal = soft_signal

        if signal is None:
            if soft_signal is not None:
                return False
            self._clear_claude_blocked_state("signal_cleared")
            return False

        fingerprint = str(signal["fingerprint"])
        if fingerprint == self._last_claude_blocked_fingerprint:
            return True
        if time.time() < self._claude_blocked_cooldowns.get(fingerprint, 0.0):
            return False

        self._log_raw(
            "claude_blocked_detected",
            str(handoff_path),
            "claude_session",
            {
                "blocked_source": signal.get("source", "sentinel"),
                "blocked_reason": signal.get("reason", "implement_blocked"),
                "blocked_fingerprint": fingerprint,
                "handoff_sha": handoff_sha,
            },
        )
        self._notify_codex_blocked_triage(signal, "claude_implement_blocked")
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
    def _claude_session_arbitration_ready(self, pane_snapshots: dict[str, str]) -> bool:
        if not self._session_arbitration_enabled():
            return False
        implement_target = self._role_pane_target("implement")
        verify_target = self._role_pane_target("verify")
        advisory_target = self._role_pane_target("advisory")
        if not implement_target or not verify_target or not advisory_target:
            return False
        if _is_pane_dead(implement_target):
            return False
        if _is_pane_dead(verify_target):
            return False
        if _is_pane_dead(advisory_target):
            return False
        if not _pane_text_is_idle(pane_snapshots["codex"]):
            return False
        if not _pane_text_is_idle(pane_snapshots["gemini"]):
            return False
        if _pane_text_is_idle(pane_snapshots["claude"]):
            return True
        return (
            self._pane_snapshot_stable_sec("claude", pane_snapshots["claude"])
            >= self.session_arbitration_settle_sec
        )

    # ------------------------------------------------------------------
    def _check_claude_live_session_escalation(self) -> None:
        if self._current_turn_state != WatcherTurnState.CLAUDE_ACTIVE:
            return
        if not self._session_arbitration_enabled():
            self._clear_session_arbitration_draft("session_arbitration_disabled")
            return
        if self._get_pending_operator_mtime() > 0.0:
            self._clear_session_arbitration_draft("operator_request_pending")
            return
        if self._get_pending_gemini_request_mtime() > 0.0 or self._get_pending_gemini_advice_mtime() > 0.0:
            self._clear_session_arbitration_draft("canonical_gemini_pending")
            return
        if self._read_status_from_path(self.claude_handoff_path) != "implement":
            self._clear_session_arbitration_draft("handoff_inactive")
            return

        pane_snapshots = {
            "claude": _capture_pane_text(self._role_pane_target("implement")),
            "codex": _capture_pane_text(self._role_pane_target("verify")),
            "gemini": _capture_pane_text(self._role_pane_target("advisory")),
        }
        signal = _extract_live_session_escalation(pane_snapshots["claude"])
        if signal is None:
            self._clear_session_arbitration_draft("signal_cleared")
            return
        if not self._claude_session_arbitration_ready(pane_snapshots):
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
            self._role_pane_target("implement"),
            self._role_pane_target("verify"),
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
        job.round += 1
        job.artifact_hash = ""
        job.artifact_size = 0
        job.artifact_mtime = 0.0
        job.last_dispatch_at = 0.0
        job.last_dispatch_slot = ""
        job.feedback_baseline_sig = ""
        job.verify_result = ""
        job.verify_manifest_path = ""
        job.verify_completed_at = 0.0
        job.validation_score = -1.0
        job.blocker_count = -1
        self.stabilizer.clear(job_id)
        job.transition(JobStatus.STABILIZING, f"{reason}, round={job.round}")
        job.save(self.state_dir)
        log.info("re-entered: job=%s round=%d (%s)", job_id, job.round, reason)

    # ------------------------------------------------------------------
    def _poll(self) -> None:
        if not self.watch_dir.exists():
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
            turn = self._resolve_turn()
            log.info("initial turn: %s", turn)
            self._log_raw("initial_turn", "", "startup", {"turn": turn})
            if turn == "claude":
                self._work_baseline_snapshot = self._get_work_tree_snapshot()
                self._transition_turn(
                    WatcherTurnState.CLAUDE_ACTIVE,
                    "startup_turn_claude",
                    active_control_file="claude_handoff.md",
                    active_control_seq=self._read_control_seq_from_path(self.claude_handoff_path),
                )
                handoff_path, _ = self._get_latest_implement_handoff()
                self._notify_claude("startup_turn_claude", handoff_path)
                log.info("CLAUDE_ACTIVE: baseline_files=%d",
                         len(self._work_baseline_snapshot))
                return
            if turn == "operator":
                self._transition_turn(WatcherTurnState.OPERATOR_WAIT, "startup_turn_operator")
                log.info("startup turn blocked by pending operator_request")
                self._log_raw(
                    "operator_request_pending",
                    str(self.operator_request_path),
                    "startup",
                    {"status": "needs_operator"},
                )
                return
            if turn == "gemini":
                self._transition_turn(WatcherTurnState.GEMINI_ADVISORY, "startup_turn_gemini")
                self._notify_gemini("startup_turn_gemini")
                return
            if turn == "codex_followup":
                self._transition_turn(WatcherTurnState.CODEX_FOLLOWUP, "startup_turn_codex_followup")
                operator_recovery = self._operator_control_recovery_marker()
                operator_gate = self._operator_gate_marker()
                if operator_recovery is not None:
                    recovery_reason = str(operator_recovery.get("reason") or "verified_blockers_resolved")
                    if recovery_reason == "operator_wait_idle_retriage":
                        self._last_operator_retriage_sig = self._get_path_sig(self.operator_request_path)
                    self._log_raw(
                        "operator_request_stale_ignored",
                        str(self.operator_request_path),
                        "startup",
                        operator_recovery,
                    )
                    if recovery_reason == "operator_wait_idle_retriage":
                        self._notify_codex_operator_retriage("startup_turn_operator_idle_retriage", operator_recovery)
                    else:
                        self._notify_codex_control_recovery("startup_turn_stale_operator", operator_recovery)
                elif operator_gate is not None:
                    self._last_operator_retriage_sig = self._get_path_sig(self.operator_request_path)
                    self._log_raw(
                        "operator_request_gated",
                        str(self.operator_request_path),
                        "startup",
                        operator_gate,
                    )
                    self._notify_codex_operator_retriage("startup_turn_operator_gated", operator_gate)
                else:
                    self._notify_codex_followup("startup_turn_codex_followup")
                return
            if turn == "codex":
                self._transition_turn(WatcherTurnState.CODEX_VERIFY, "startup_turn_codex")
                # Codex verify는 work/ 감시 루프에서 자연스럽게 디스패치됨
                return
            # idle
            self._transition_turn(WatcherTurnState.IDLE, "startup_turn_idle")

        # --- rolling handoff / operator 슬롯 감시 (Codex → Claude / operator 방향) ---
        self._check_pipeline_signal_updates()
        self._check_operator_wait_idle_timeout()

        # --- 최신 control signal이 operator stop이면 자동 진행을 멈춤 ---
        _, handoff_mtime = self._get_latest_implement_handoff()
        if self._operator_blocks_handoff(handoff_mtime):
            return

        # --- Gemini arbitration이 pending이면 다른 자동 진행을 잠시 멈춤 ---
        if self._get_pending_gemini_request_mtime() > 0.0 or self._get_pending_gemini_advice_mtime() > 0.0:
            self._clear_session_arbitration_draft("canonical_gemini_pending")
            return

        # --- Claude 차례 대기 중이면 work/ 감시 건너뜀 ---
        if self._current_turn_state == WatcherTurnState.CLAUDE_ACTIVE:
            if self._check_claude_implement_blocked():
                return
            self._check_claude_live_session_escalation()
            self._check_claude_idle_timeout()
            if self._current_turn_state != WatcherTurnState.CLAUDE_ACTIVE:
                return  # idle timeout fired
            # work/ 전체 스냅샷이 달라졌는지 확인
            current_snapshot = self._get_work_tree_snapshot()
            if current_snapshot == self._work_baseline_snapshot:
                return  # Claude가 아직 작업 안 함 → Codex dispatch 하지 않음
            # Claude가 새 파일을 썼거나 기존 파일 내용을 바꿨으므로 대기 해제
            self._transition_turn(WatcherTurnState.IDLE, "claude_activity_detected")
            self._work_baseline_snapshot = {}
            self._clear_session_arbitration_draft("claude_activity_resumed")
            self._clear_claude_blocked_state("claude_activity_resumed")
            log.info("claude activity detected by snapshot diff, resuming codex dispatch")

        # --- work/ 디렉터리 감시 (Claude → Codex 방향) ---
        # baseline과 동일하게 가장 최신 파일 1개만 처리
        all_mds = sorted(
            (p for p in self.watch_dir.rglob("*.md") if self._is_dispatchable_work_note(p)),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )
        latest = all_mds[0] if all_mds else None
        artifacts_to_process = [latest] if latest else []
        for artifact in artifacts_to_process:
            job_id = make_job_id(self.watch_dir, artifact)
            job    = JobState.load(self.state_dir, job_id)

            if job is None:
                self._log_raw("artifact_seen", str(artifact), job_id)
                job = JobState.from_artifact(job_id, str(artifact))
                job.save(self.state_dir)
                log.info("new job: %s  path=%s", job_id, artifact)

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
                        help="Codex/verify pane target (기본: <session>:0.1)")
    parser.add_argument("--claude-pane-target",   default="",
                        help="Claude pane target (기본: <session>:0.0)")
    parser.add_argument("--gemini-pane-target",   default="",
                        help="Gemini pane target (기본: <session>:0.2)")
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
