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

import hashlib
import json
import logging
import subprocess
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

# jsonschema는 선택적 의존성 — 없으면 필수 필드 구조 검증만 수행
try:
    import jsonschema as _jsonschema
    _JSONSCHEMA_AVAILABLE = True
except ImportError:
    _jsonschema = None  # type: ignore
    _JSONSCHEMA_AVAILABLE = False

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
    feedback_baseline_sig:str   = ""    # dispatch 직전 codex_feedback.md 시그니처
    # 2단계 추가 필드
    verify_manifest_path: str   = ""    # 수집된 manifest 파일 경로
    verify_completed_at:  float = 0.0   # VERIFY_DONE 전이 시각
    validation_score:     float = -1.0  # passed_checks/required_checks (-1 = 미수집)
    blocker_count:        int   = -1    # critical blocker 수 (-1 = 미수집)
    verify_result:        str   = ""    # "passed" | "failed" | "invalid_manifest"
    created_at:           float = field(default_factory=time.time)
    updated_at:           float = field(default_factory=time.time)
    history:              list  = field(default_factory=list)

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
        data = asdict(self)
        data["status"] = self.status.value
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, state_dir: Path, job_id: str) -> Optional["JobState"]:
        path = state_dir / f"{job_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
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


def _pane_has_input_cursor(pane_target: str) -> bool:
    """Check if the pane shows an input prompt (> or $) on the last non-empty line."""
    text = _capture_pane_text(pane_target)
    lines = [l for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return False
    last = lines[-1].strip()
    # Codex shows "> " prompt, Claude shows "> " or "$"
    return last.endswith(">") or last.endswith("$") or "> " in last


def _wait_for_input_ready(
    pane_target: str,
    timeout_sec: float = 30.0,
    poll_sec: float = 1.0,
) -> bool:
    """Wait until the pane shows an input prompt, meaning the CLI is ready."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if _pane_has_input_cursor(pane_target):
            return True
        time.sleep(poll_sec)
    return False


def tmux_send_keys(pane_target: str, command: str, dry_run: bool = False) -> bool:
    log.info("send-keys target=%s dry_run=%s", pane_target, dry_run)
    if dry_run:
        return True
    try:
        # Phase 1: wait for pane output to settle (stop changing)
        settled = wait_for_pane_settle(pane_target)
        if not settled:
            log.warning("pane did not fully settle before dispatch: target=%s", pane_target)

        # Phase 2: wait for input prompt to appear (CLI ready for input)
        input_ready = _wait_for_input_ready(pane_target, timeout_sec=30.0)
        if not input_ready:
            log.warning("pane input prompt not detected, proceeding anyway: target=%s", pane_target)

        # Phase 3: Write prompt to a temp file, then execute via shell.
        #
        # Codex/Claude CLIs use raw terminal mode, so tmux paste-buffer +
        # Enter often fails: the text lands in the input line but Enter is
        # not consumed as "submit". This is a known issue with TUI apps
        # that use readline-like input handlers in raw mode.
        #
        # Reliable workaround: write prompt to a temp file, then send a
        # short shell command that pipes it into the CLI.
        import tempfile
        prompt_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="prompt-", delete=False,
            dir="/tmp",
        )
        prompt_file.write(command)
        prompt_file.close()
        prompt_path = prompt_file.name

        # First interrupt any stuck state (Ctrl+C), then send the prompt
        # via `codex exec` for Codex or paste for Claude.
        # Detect pane type: if pane has bash prompt ($) → codex exec mode
        # If pane has Claude prompt (>) → paste-buffer mode
        pane_text = _capture_pane_text(pane_target)
        pane_lines = [l.strip() for l in pane_text.strip().splitlines() if l.strip()]
        last_line = pane_lines[-1] if pane_lines else ""
        is_codex = last_line.endswith("$") or "codex" in pane_text.lower() or "openai" in pane_text.lower()

        if is_codex:
            # Codex interactive mode does not reliably accept pasted text + Enter.
            # Solution: run `codex "prompt"` from bash shell each time.
            #
            # If codex is already running (2nd+ dispatch), kill it first.
            # If this is first dispatch (bash prompt), skip cleanup.
            pane_last = _capture_pane_text(pane_target).strip().splitlines()
            pane_last_line = pane_last[-1].strip() if pane_last else ""
            if not pane_last_line.endswith("$"):
                # Codex is running — send Ctrl+C and /exit to get back to bash
                subprocess.run(["tmux", "send-keys", "-t", pane_target, "C-c"], check=False, capture_output=True)
                time.sleep(0.5)
                subprocess.run(["tmux", "send-keys", "-t", pane_target, "/exit", "Enter"], check=False, capture_output=True)
                time.sleep(1.5)
            # Launch codex interactive with prompt from file
            shell_cmd = f"codex --ask-for-approval never \"$(cat '{prompt_path}')\""
            subprocess.run(
                ["tmux", "send-keys", "-t", pane_target, shell_cmd, "Enter"],
                check=True, capture_output=True,
            )
            log.info("codex interactive dispatched with prompt file: %s", prompt_path)
        else:
            # For Claude: paste-buffer approach works better
            subprocess.run(["tmux", "set-buffer", command], check=True, capture_output=True)
            subprocess.run(["tmux", "paste-buffer", "-t", pane_target], check=True, capture_output=True)
            time.sleep(1.0)
            for attempt in range(3):
                subprocess.run(["tmux", "send-keys", "-t", pane_target, "Enter"], check=True, capture_output=True)
                time.sleep(1.5)
                if not _pane_has_input_cursor(pane_target):
                    log.info("prompt consumed after Enter attempt %d", attempt + 1)
                    break

        # Cleanup temp file after a delay (let shell read it first)
        import threading
        def _cleanup():
            time.sleep(10)
            try:
                import os
                os.unlink(prompt_path)
            except OSError:
                pass
        threading.Thread(target=_cleanup, daemon=True).start()

        return True
    except subprocess.CalledProcessError as e:
        log.error("send-keys failed: %s", e.stderr.decode().strip())
        return False


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
        verify_prompt_template: str,
        feedback_path:          Path,
        error_log:              Path,
        dry_run:                bool = False,
    ) -> None:
        self.state_dir              = state_dir
        self.stabilizer             = stabilizer
        self.lease                  = lease
        self.dedupe                 = dedupe
        self.collector              = collector
        self.verify_pane_target     = verify_pane_target
        self.verify_prompt_template = verify_prompt_template
        self.feedback_path          = feedback_path
        self.error_log              = error_log
        self.dry_run                = dry_run

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

        if self.dedupe.is_duplicate(job.job_id, job.round, job.artifact_hash, slot):
            self.dedupe.mark_suppressed(
                job.job_id, job.round, job.artifact_hash, slot, "dedupe")
            return job

        if not self.lease.acquire(slot, job.job_id, job.round, self.verify_pane_target):
            self.dedupe.mark_suppressed(
                job.job_id, job.round, job.artifact_hash, slot, "lease_busy")
            return job

        prompt = self.verify_prompt_template.format(
            job_id=job.job_id, round=job.round, artifact_path=job.artifact_path,
        )
        ok = tmux_send_keys(self.verify_pane_target, prompt, self.dry_run)

        if ok:
            self.dedupe.mark_dispatch(
                job.job_id, job.round, job.artifact_hash, slot,
                self.verify_pane_target, self.dry_run,
            )
            job.last_dispatch_at   = time.time()
            job.last_dispatch_slot = slot
            job.feedback_baseline_sig = compute_file_sig(self.feedback_path)
            job.transition(JobStatus.VERIFY_RUNNING, f"dispatched to {slot}")
            job.save(self.state_dir)
            if self.dry_run:
                self.lease.release(slot)
        else:
            self.lease.release(slot)
        return job

    # ------------------------------------------------------------------
    def _handle_verify_running(self, job: JobState) -> JobState:
        """
        manifest 파일을 폴링하고:
          - 없으면:
            · codex_feedback.md가 dispatch 이후 갱신됐으면 → Codex 완료로 간주, VERIFY_DONE
            · lease TTL 초과 → 타임아웃, VERIFY_DONE (result=timeout)
            · 그 외 → 대기 (VERIFY_RUNNING 유지)
          - 스키마/일치 검증 실패 → verify_result="invalid_manifest", VERIFY_RUNNING 유지
            + error 로그 기록
          - 검증 통과 → verify_result="passed"|"failed", VERIFY_DONE 전이
        """
        manifest = self.collector.poll(job)
        if manifest is None:
            # manifest 없음 — feedback 변경 또는 타임아웃 체크
            # Codex는 manifest를 안 남기고 codex_feedback.md만 갱신할 수 있음
            fb_sig = compute_file_sig(self.feedback_path)

            if fb_sig and fb_sig != job.feedback_baseline_sig:
                # feedback 내용/크기/mtime_ns 중 하나라도 달라졌으면 Codex 완료로 간주
                log.info("feedback signature changed after dispatch: job=%s, treating as verify done",
                         job.job_id)
                job.verify_result = "passed_by_feedback"
                job.verify_completed_at = time.time()
                self.lease.release("slot_verify")
                job.transition(JobStatus.VERIFY_DONE,
                               "codex_feedback.md signature changed after dispatch")
                job.save(self.state_dir)
                return job

            # lease 타임아웃 체크
            elapsed = time.time() - job.last_dispatch_at
            if elapsed > self.lease.default_ttl:
                log.warning("verify timeout: job=%s elapsed=%.0fs", job.job_id, elapsed)
                job.verify_result = "timeout"
                job.verify_completed_at = time.time()
                self.lease.release("slot_verify")
                job.transition(JobStatus.VERIFY_DONE,
                               f"timeout after {elapsed:.0f}s")
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

        self.watch_dir     = Path(config["watch_dir"])
        self.state_dir     = base / "state"
        self.lock_dir      = base / "locks"
        self.manifests_dir = base / "manifests"

        # 로그 디렉터리 분리: experimental vs baseline
        self.events_dir = base / "logs" / "experimental"
        self.events_dir.mkdir(parents=True, exist_ok=True)

        self.poll_interval = config.get("poll_interval", 1.0)
        self.dry_run       = config.get("dry_run", False)
        self.startup_grace_sec = float(config.get("startup_grace_sec", 8.0))
        self.started_at = time.time()

        # feedback 파일 경로 및 Claude pane 타겟
        self.feedback_path       = base / "codex_feedback.md"
        self.claude_pane_target  = config.get("claude_pane_target", "ai-pipeline:0.0")
        self.claude_prompt       = config.get(
            "claude_prompt",
            "CLAUDE.md, AGENTS.md, verify/README.md, work/README.md, .pipeline/README.md, "
            ".pipeline/codex_feedback.md를 읽고, STATUS가 implement일 때만 그 지시대로 한 슬라이스만 "
            "구현해줘. STATUS가 needs_operator면 새 구현을 시작하지 말고 기다려줘.",
        )

        # feedback 파일 시그니처 추적 (mtime_ns + size + hash)
        self._last_feedback_sig: str = self._get_feedback_sig()
        # 시작 시 이미 Claude 차례인지 판단하는 플래그
        self._initial_turn_checked: bool = False
        # Claude 차례일 때: 시작 시점 work/ 스냅샷
        # 이후 스냅샷이 달라질 때만 새 작업으로 인정
        self._work_baseline_snapshot: dict[str, str] = {}
        # Claude 차례 대기 중 플래그
        self._waiting_for_claude: bool = False

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
            verify_pane_target=config.get("verify_pane_target", "ai-pipeline:0.1"),
            verify_prompt_template=config.get(
                "verify_prompt_template",
                "verify job={job_id} round={round} path={artifact_path}",
            ),
            feedback_path=self.feedback_path,
            error_log=self.events_dir / "errors.jsonl",
            dry_run=self.dry_run,
        )

    # ------------------------------------------------------------------
    def _get_feedback_mtime(self) -> float:
        """feedback 파일의 mtime 반환. 없으면 0.0."""
        try:
            return self.feedback_path.stat().st_mtime
        except OSError:
            return 0.0

    # ------------------------------------------------------------------
    def _get_feedback_sig(self) -> str:
        """feedback 파일 시그니처 반환. 없으면 빈 문자열."""
        return compute_file_sig(self.feedback_path)

    # ------------------------------------------------------------------
    def _get_work_tree_snapshot(self) -> dict[str, str]:
        """work/ 전체 .md 스냅샷 반환."""
        return build_md_tree_snapshot(self.watch_dir)

    # ------------------------------------------------------------------
    def _get_latest_work_mtime(self) -> float:
        """work/ 내 최신 .md 파일의 mtime 반환. 없으면 0.0."""
        latest = 0.0
        for md in self.watch_dir.rglob("*.md"):
            try:
                mt = md.stat().st_mtime
                if mt > latest:
                    latest = mt
            except OSError:
                continue
        return latest

    # ------------------------------------------------------------------
    def _determine_initial_turn(self) -> str:
        """
        시작 시 턴 판단:
          - feedback.md와 work/ 내 최신 .md의 mtime 비교
          - feedback가 더 최신 → Claude 차례 (Codex가 마지막으로 작업한 것)
          - work가 더 최신 → Codex 차례 (Claude가 마지막으로 작업한 것)
          - 둘 다 없음 → Claude 차례 (초기 상태)
        """
        feedback_mtime = self._get_feedback_mtime()

        work_mtime = 0.0
        for md in self.watch_dir.rglob("*.md"):
            try:
                mt = md.stat().st_mtime
                if mt > work_mtime:
                    work_mtime = mt
            except OSError:
                continue

        if feedback_mtime == 0.0 and work_mtime == 0.0:
            return "claude"  # 초기 상태
        if feedback_mtime >= work_mtime:
            return "claude"  # Codex가 마지막 → Claude 차례
        return "codex"       # Claude가 마지막 → Codex 차례

    # ------------------------------------------------------------------
    def _notify_claude(self, reason: str) -> None:
        """Claude pane에 다음 작업 프롬프트 전송."""
        log.info("notify_claude: reason=%s target=%s", reason, self.claude_pane_target)
        self._log_raw("claude_notify", str(self.feedback_path), "turn_signal",
                       {"reason": reason})
        tmux_send_keys(self.claude_pane_target, self.claude_prompt, self.dry_run)

    # ------------------------------------------------------------------
    def _read_feedback_status(self) -> Optional[str]:
        """feedback 파일의 첫 STATUS: 줄을 읽어 값을 반환."""
        try:
            with self.feedback_path.open() as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("STATUS:"):
                        return stripped.split(":", 1)[1].strip().lower()
        except OSError:
            return None
        return None

    def _check_feedback_update(self) -> None:
        """feedback 파일 시그니처가 바뀌면 STATUS를 확인하고 implement일 때만 Claude에 알림."""
        current_sig = self._get_feedback_sig()
        if current_sig and current_sig != self._last_feedback_sig:
            self._last_feedback_sig = current_sig
            status = self._read_feedback_status()
            if status == "implement":
                log.info("feedback updated: STATUS=implement → Claude 차례")
                self._notify_claude("feedback_updated")
            else:
                reason = status or "missing"
                log.info("feedback updated: STATUS=%s → Claude notify 건너뜀", reason)
                self._log_raw("claude_notify_skipped", str(self.feedback_path),
                              "turn_signal", {"status": reason})

    # ------------------------------------------------------------------
    def _log_raw(self, event: str, path: str, job_id: str,
                 extra: Optional[dict] = None) -> None:
        entry: dict = {"event": event, "path": path, "job_id": job_id, "at": time.time()}
        if extra:
            entry.update(extra)
        with (self.events_dir / "raw.jsonl").open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

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
            "startup_grace=%.1fs  jsonschema=%s  claude_pane=%s",
            self.watch_dir, self.dry_run, self.poll_interval,
            self.startup_grace_sec, _JSONSCHEMA_AVAILABLE, self.claude_pane_target,
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
            turn = self._determine_initial_turn()
            log.info("initial turn: %s", turn)
            self._log_raw("initial_turn", "", "startup", {"turn": turn})
            if turn == "claude":
                # Claude 차례 → 시작 시점 work/ 전체 스냅샷을 기준선으로 저장
                self._work_baseline_snapshot = self._get_work_tree_snapshot()
                self._waiting_for_claude = True
                self._notify_claude("startup_turn_claude")
                log.info("waiting_for_claude: baseline_files=%d",
                         len(self._work_baseline_snapshot))
                return

        # --- feedback 파일 변경 감시 (Codex → Claude 방향) ---
        self._check_feedback_update()

        # --- Claude 차례 대기 중이면 work/ 감시 건너뜀 ---
        if self._waiting_for_claude:
            # work/ 전체 스냅샷이 달라졌는지 확인
            current_snapshot = self._get_work_tree_snapshot()
            if current_snapshot == self._work_baseline_snapshot:
                return  # Claude가 아직 작업 안 함 → Codex dispatch 하지 않음
            # Claude가 새 파일을 썼거나 기존 파일 내용을 바꿨으므로 대기 해제
            self._waiting_for_claude = False
            self._work_baseline_snapshot = {}
            log.info("claude activity detected by snapshot diff, resuming codex dispatch")

        # --- work/ 디렉터리 감시 (Claude → Codex 방향) ---
        # baseline과 동일하게 가장 최신 파일 1개만 처리
        all_mds = sorted(self.watch_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
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
    parser.add_argument("--verify-pane-target",   default="ai-pipeline:0.1")
    parser.add_argument("--claude-pane-target",   default="ai-pipeline:0.0",
                        help="Claude가 실행 중인 tmux pane (기본: ai-pipeline:0.0)")
    parser.add_argument("--manifest-schema-path", default="",
                        help="agent_manifest.schema.json 경로 (기본: ./schemas/)")
    parser.add_argument("--dry-run",              action="store_true")
    parser.add_argument("--poll",                 type=float, default=1.0)
    parser.add_argument("--settle",               type=float, default=3.0)
    parser.add_argument("--startup-grace",        type=float, default=8.0)
    parser.add_argument("--lease-ttl",            type=int,   default=900)
    parser.add_argument("--verify-prompt",         default="",
                        help="Codex pane에 보낼 프롬프트 (기본: 내부 job ID 형식)")
    parser.add_argument("--claude-prompt",         default="",
                        help="Claude pane에 보낼 프롬프트 (feedback 갱신 시)")
    args = parser.parse_args()

    config: dict = {
        "watch_dir":          args.watch_dir,
        "base_dir":           args.base_dir,
        "verify_pane_target": args.verify_pane_target,
        "claude_pane_target": args.claude_pane_target,
        "dry_run":            args.dry_run,
        "poll_interval":      args.poll,
        "settle_sec":         args.settle,
        "startup_grace_sec":  args.startup_grace,
        "lease_ttl":          args.lease_ttl,
    }
    if args.verify_prompt:
        config["verify_prompt_template"] = args.verify_prompt
    if args.claude_prompt:
        config["claude_prompt"] = args.claude_prompt
    if args.manifest_schema_path:
        config["manifest_schema_path"] = args.manifest_schema_path

    WatcherCore(config).run()


if __name__ == "__main__":
    main()
