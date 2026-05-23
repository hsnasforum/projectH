from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pipeline_runtime.schema import jobs_state_dir

log = logging.getLogger(__name__)
_job_state_log = logging.getLogger("watcher_core")
JOB_STATE_SCHEMA_VERSION = 1

try:
    import jsonschema as _jsonschema
    _JSONSCHEMA_AVAILABLE = True
except ImportError:
    _jsonschema = None  # type: ignore
    _JSONSCHEMA_AVAILABLE = False


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


class JobStatus(str, Enum):
    NEW_ARTIFACT = "NEW_ARTIFACT"
    STABILIZING = "STABILIZING"
    VERIFY_PENDING = "VERIFY_PENDING"
    VERIFY_RUNNING = "VERIFY_RUNNING"
    VERIFY_DONE = "VERIFY_DONE"


TERMINAL_STATES: set[JobStatus] = {JobStatus.VERIFY_DONE}


@dataclass
class JobState:
    job_id: str
    status: JobStatus
    artifact_path: str
    run_id: str = ""
    schema_version: int = JOB_STATE_SCHEMA_VERSION
    artifact_hash: str = ""
    artifact_size: int = 0
    artifact_mtime: float = 0.0
    stabilized_at: float = 0.0
    round: int = 1
    retry_budget: int = 3
    last_dispatch_at: float = 0.0
    last_dispatch_slot: str = ""
    last_failed_dispatch_at: float = 0.0
    last_failed_dispatch_snapshot: str = ""
    dispatch_fail_count: int = 0
    feedback_baseline_sig: str = ""
    verify_feedback_baseline_sig: str = ""
    verify_receipt_baseline_path: str = ""
    verify_receipt_baseline_mtime: float = 0.0
    verify_manifest_path: str = ""
    verify_completed_at: float = 0.0
    validation_score: float = -1.0
    blocker_count: int = -1
    verify_result: str = ""
    dispatch_stall_fingerprint: str = ""
    dispatch_stall_count: int = 0
    dispatch_stall_detected_at: float = 0.0
    dispatch_id: str = ""
    dispatch_control_seq: int = -1
    seen_dispatch_id: str = ""
    seen_at: float = 0.0
    accept_deadline_at: float = 0.0
    accepted_dispatch_id: str = ""
    accepted_at: float = 0.0
    done_dispatch_id: str = ""
    done_at: float = 0.0
    done_deadline_at: float = 0.0
    dispatch_stall_stage: str = ""
    completion_stall_fingerprint: str = ""
    completion_stall_count: int = 0
    completion_stall_detected_at: float = 0.0
    completion_stall_stage: str = ""
    degraded_reason: str = ""
    lane_note: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    history: list = field(default_factory=list)
    last_pane_snapshot: str = ""
    last_activity_at: float = 0.0

    def transition(self, new_status: JobStatus, reason: str = "") -> None:
        old = self.status
        self.status = new_status
        self.updated_at = time.time()
        self.history.append(
            {
                "from": old.value,
                "to": new_status.value,
                "at": self.updated_at,
                "reason": reason,
            }
        )
        _job_state_log.info("state %s  %s → %s  (%s)", self.job_id, old.value, new_status.value, reason)

    def save(self, state_dir: Path) -> None:
        # primary JobState path는 `<state_dir>/jobs/<job_id>.json`. 쓰기는 항상 primary로
        # 간다. migration 기간 동안 루트에 남아 있는 fallback copy는 읽기에만 허용하고
        # 이번 라운드에서는 자동 이동시키지 않는다.
        primary_dir = jobs_state_dir(state_dir)
        primary_dir.mkdir(parents=True, exist_ok=True)
        path = primary_dir / f"{self.job_id}.json"
        tmp_path = path.with_suffix(f"{path.suffix}.tmp")
        data = asdict(self)
        data["status"] = self.status.value
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp_path.replace(path)

    @classmethod
    def load(cls, state_dir: Path, job_id: str) -> Optional["JobState"]:
        primary_path = jobs_state_dir(state_dir) / f"{job_id}.json"
        fallback_path = state_dir / f"{job_id}.json"
        if primary_path.exists():
            path = primary_path
        elif fallback_path.exists():
            path = fallback_path
        else:
            return None
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            corrupt_path = path.with_suffix(f"{path.suffix}.corrupt-{int(time.time())}")
            try:
                path.replace(corrupt_path)
                _job_state_log.warning("quarantined corrupt job state: %s -> %s (%s)", path, corrupt_path, exc)
            except OSError:
                _job_state_log.warning("failed to quarantine corrupt job state: %s (%s)", path, exc)
            return None
        data["status"] = JobStatus(data["status"])
        return cls(**data)

    @classmethod
    def from_artifact(cls, job_id: str, artifact_path: str, *, run_id: str = "") -> "JobState":
        return cls(
            job_id=job_id,
            status=JobStatus.NEW_ARTIFACT,
            artifact_path=artifact_path,
            run_id=run_id,
        )


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

    def release_if_mismatched(self, slot: str, job_id: str, round_: int, *, reason: str) -> bool:
        path = self._lock_path(slot)
        self._clear_if_owner_dead(slot)
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._clear_lock(slot, reason=reason)
            return True
        try:
            lock_round = int(data.get("round") or 0)
        except (TypeError, ValueError):
            lock_round = 0
        if str(data.get("job_id") or "") == str(job_id or "") and lock_round == int(round_):
            return False
        self._clear_lock(slot, reason=reason)
        return True

    def archive_for_restart(self, slot: str, *, archive_dir: Path | None = None) -> bool:
        """
        Preserve a potentially stale lease before watcher self-restart.

        The supervisor owns the watcher process and can remain alive while the
        old watcher's lock is no longer useful. Archiving keeps evidence while
        allowing the restarted watcher to acquire the slot without waiting for
        TTL expiry.
        """
        path = self._lock_path(slot)
        if not path.exists():
            return True
        dest_dir = archive_dir or (self.lock_dir / "archive")
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            log.warning("lease archive dir creation failed: slot=%s dir=%s error=%s", slot, dest_dir, exc)
            return False
        ts = int(time.time())
        dest = dest_dir / f"{slot}.lock.stale-{ts}"
        try:
            path.rename(dest)
        except OSError as exc:
            log.warning("lease archive failed: slot=%s dest=%s error=%s", slot, dest, exc)
            return False
        log.info("lease archived for restart: slot=%s dest=%s", slot, dest)
        return True

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
                    entry = json.loads(line)
                    key = entry["key"]
                    if entry.get("event") == "forget":
                        self._seen.discard(key)
                    else:
                        self._seen.add(key)
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
        self.events_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": "forget", "key": key, "job_id": job_id,
            "round": round_, "artifact_hash": artifact_hash,
            "target_slot": target_slot, "at": time.time(),
        }
        with self.dispatch_log.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


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

    def poll(self, job: Any) -> Optional[dict]:
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

    def validate(self, manifest: dict, job: Any) -> tuple[bool, str]:
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
