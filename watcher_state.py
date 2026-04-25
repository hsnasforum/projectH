from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

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
