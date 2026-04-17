from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from pipeline_runtime.schema import read_json
from pipeline_runtime.wrapper_events import build_lane_read_models

log = logging.getLogger("watcher_core")

SCHEMA_VERSION = 1


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
    schema_version: int = SCHEMA_VERSION
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
        log.info("state %s  %s → %s  (%s)", self.job_id, old.value, new_status.value, reason)

    def save(self, state_dir: Path) -> None:
        state_dir.mkdir(parents=True, exist_ok=True)
        path = state_dir / f"{self.job_id}.json"
        tmp_path = path.with_suffix(f"{path.suffix}.tmp")
        data = asdict(self)
        data["status"] = self.status.value
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp_path.replace(path)

    @classmethod
    def load(cls, state_dir: Path, job_id: str) -> Optional["JobState"]:
        path = state_dir / f"{job_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            corrupt_path = path.with_suffix(f"{path.suffix}.corrupt-{int(time.time())}")
            try:
                path.replace(corrupt_path)
                log.warning("quarantined corrupt job state: %s -> %s (%s)", path, corrupt_path, exc)
            except OSError:
                log.warning("failed to quarantine corrupt job state: %s (%s)", path, exc)
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


def make_job_id(watch_dir: Path, artifact: Path) -> str:
    rel = artifact.relative_to(watch_dir)
    path_hash = hashlib.sha1(str(rel).encode()).hexdigest()[:8]
    safe_stem = "".join(c if c.isalnum() or c == "-" else "-" for c in artifact.stem)[:32]
    date_str = time.strftime("%Y%m%d")
    return f"{date_str}-{safe_stem}-{path_hash}"


def compute_file_sig(path: Path) -> str:
    try:
        stat = path.stat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return f"{stat.st_mtime_ns}:{stat.st_size}:{digest}"
    except OSError:
        return ""


def compute_multi_file_sig(paths: list[Path]) -> str:
    parts: list[str] = []
    for path in paths:
        sig = compute_file_sig(path)
        if not sig:
            continue
        parts.append(f"{path.name}={sig}")
    return "|".join(parts)


def build_md_tree_snapshot(root: Path) -> dict[str, str]:
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
    snapshot = build_md_tree_snapshot(root)
    if not snapshot:
        return ""
    parts = [f"{path}={sig}" for path, sig in sorted(snapshot.items())]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


class StateMachine:
    def __init__(
        self,
        project_root: Path,
        verify_lane_name: str,
        state_dir: Path,
        stabilizer: Any,
        lease: Any,
        dedupe: Any,
        collector: Any,
        verify_pane_target: str,
        verify_pane_type: str,
        verify_prompt_template: str,
        verify_context_builder: Optional[Callable[[JobState], dict[str, str]]],
        feedback_sig_builder: Optional[Callable[[JobState], tuple[str, str]]],
        verify_receipt_builder: Optional[Callable[[JobState], tuple[str, float]]],
        verify_retry_backoff_sec: float,
        verify_incomplete_idle_retry_sec: float,
        verify_accept_deadline_sec: float,
        verify_done_deadline_sec: float,
        runtime_started_at: float,
        restart_recovery_grace_sec: float,
        completion_paths: list[Path],
        error_log: Path,
        capture_pane_text: Callable[[str], str],
        pane_text_has_busy_indicator: Callable[[str], bool],
        pane_text_has_input_cursor: Callable[[str], bool],
        pane_text_is_idle: Callable[[str], bool],
        normalize_prompt_text: Callable[[str], str],
        send_keys: Callable[[str, str, bool, str], bool],
        dry_run: bool = False,
    ) -> None:
        self.project_root = project_root
        self.verify_lane_name = verify_lane_name
        self.state_dir = state_dir
        self.stabilizer = stabilizer
        self.lease = lease
        self.dedupe = dedupe
        self.collector = collector
        self.verify_pane_target = verify_pane_target
        self.verify_pane_type = verify_pane_type
        self.verify_prompt_template = verify_prompt_template
        self.verify_context_builder = verify_context_builder
        self.feedback_sig_builder = feedback_sig_builder
        self.verify_receipt_builder = verify_receipt_builder
        self.verify_retry_backoff_sec = verify_retry_backoff_sec
        self.verify_incomplete_idle_retry_sec = verify_incomplete_idle_retry_sec
        self.verify_accept_deadline_sec = verify_accept_deadline_sec
        self.verify_done_deadline_sec = verify_done_deadline_sec
        self.runtime_started_at = runtime_started_at
        self.restart_recovery_grace_sec = restart_recovery_grace_sec
        self.completion_paths = completion_paths
        self.error_log = error_log
        self.capture_pane_text = capture_pane_text
        self.pane_text_has_busy_indicator = pane_text_has_busy_indicator
        self.pane_text_has_input_cursor = pane_text_has_input_cursor
        self.pane_text_is_idle = pane_text_is_idle
        self.normalize_prompt_text = normalize_prompt_text
        self.send_keys = send_keys
        self.dry_run = dry_run

    def _dispatch_stall_fingerprint(self, job: JobState, stage: str = "") -> str:
        source = "|".join(
            [
                job.job_id,
                str(job.round),
                job.artifact_hash,
                job.last_dispatch_slot or "slot_verify",
                job.verify_receipt_baseline_path,
                stage or "task_accept_missing",
            ]
        )
        return hashlib.sha1(source.encode("utf-8")).hexdigest()

    def _completion_stall_fingerprint(self, job: JobState, stage: str = "") -> str:
        source = "|".join(
            [
                job.job_id,
                str(job.round),
                job.artifact_hash,
                job.last_dispatch_slot or "slot_verify",
                job.verify_receipt_baseline_path,
                stage or "task_done_missing",
            ]
        )
        return hashlib.sha1(source.encode("utf-8")).hexdigest()

    def _clear_done_tracking(self, job: JobState) -> None:
        job.done_dispatch_id = ""
        job.done_at = 0.0
        job.done_deadline_at = 0.0

    def _clear_completion_stall_state(self, job: JobState) -> None:
        job.completion_stall_fingerprint = ""
        job.completion_stall_count = 0
        job.completion_stall_detected_at = 0.0
        job.completion_stall_stage = ""

    def _clear_dispatch_stall_state(self, job: JobState) -> None:
        job.dispatch_stall_fingerprint = ""
        job.dispatch_stall_count = 0
        job.dispatch_stall_detected_at = 0.0
        job.dispatch_id = ""
        job.dispatch_control_seq = -1
        job.seen_dispatch_id = ""
        job.seen_at = 0.0
        job.accept_deadline_at = 0.0
        job.accepted_dispatch_id = ""
        job.accepted_at = 0.0
        self._clear_done_tracking(job)
        job.dispatch_stall_stage = ""
        self._clear_completion_stall_state(job)
        job.degraded_reason = ""
        job.lane_note = ""

    def _clear_dispatch_stall_surface(self, job: JobState) -> None:
        job.degraded_reason = ""
        job.lane_note = ""
        job.dispatch_stall_stage = ""
        job.completion_stall_stage = ""

    def _current_wrapper_events_dir(self) -> Optional[Path]:
        current_run = read_json(self.project_root / ".pipeline" / "current_run.json")
        if not isinstance(current_run, dict):
            return None
        events_path_value = str(current_run.get("events_path") or "").strip()
        if events_path_value:
            events_path = (self.project_root / events_path_value).resolve()
            return events_path.parent / "wrapper-events"
        run_id = str(current_run.get("run_id") or "").strip()
        if not run_id:
            return None
        return self.project_root / ".pipeline" / "runs" / run_id / "wrapper-events"

    def _verify_wrapper_model(self) -> dict[str, object]:
        wrapper_dir = self._current_wrapper_events_dir()
        if wrapper_dir is None or not wrapper_dir.exists():
            return {}
        models = build_lane_read_models(
            wrapper_dir,
            heartbeat_timeout_sec=max(60.0, self.verify_accept_deadline_sec * 2.0),
            now_ts=time.time(),
        )
        return dict(models.get(self.verify_lane_name) or {})

    def _mark_dispatch_seen_if_seen(
        self,
        job: JobState,
        *,
        current_pane: str,
        lane_model: dict[str, object] | None = None,
    ) -> bool:
        if not job.dispatch_id or job.seen_dispatch_id == job.dispatch_id:
            return False
        lane_model = dict(lane_model or self._verify_wrapper_model())
        seen_task = dict(lane_model.get("seen_task") or {})
        if not seen_task:
            return False

        seen_dispatch_id = str(seen_task.get("dispatch_id") or "")
        matched = False
        if seen_dispatch_id:
            matched = seen_dispatch_id == job.dispatch_id
        else:
            matched = (
                str(seen_task.get("job_id") or "") == job.job_id
                and float(lane_model.get("last_event_ts") or 0.0) >= (job.last_dispatch_at - 1.0)
            )
        if not matched:
            return False

        job.seen_dispatch_id = job.dispatch_id
        job.seen_at = time.time()
        job.last_activity_at = job.seen_at
        job.last_pane_snapshot = current_pane
        job.save(self.state_dir)
        return True

    def _mark_dispatch_accepted_if_seen(
        self,
        job: JobState,
        *,
        current_pane: str,
        lane_model: dict[str, object] | None = None,
    ) -> bool:
        if not job.dispatch_id or job.accepted_dispatch_id == job.dispatch_id:
            return False
        lane_model = dict(lane_model or self._verify_wrapper_model())
        accepted_task = dict(lane_model.get("accepted_task") or {})
        if not accepted_task:
            return False

        accepted_dispatch_id = str(accepted_task.get("dispatch_id") or "")
        matched = False
        if accepted_dispatch_id:
            matched = accepted_dispatch_id == job.dispatch_id
        else:
            matched = (
                str(accepted_task.get("job_id") or "") == job.job_id
                and float(lane_model.get("last_event_ts") or 0.0) >= (job.last_dispatch_at - 1.0)
            )
        if not matched:
            return False

        job.accepted_dispatch_id = job.dispatch_id
        job.accepted_at = time.time()
        job.done_deadline_at = job.accepted_at + self.verify_done_deadline_sec
        job.last_activity_at = job.accepted_at
        job.last_pane_snapshot = current_pane
        job.save(self.state_dir)
        return True

    def _mark_task_done_if_seen(
        self,
        job: JobState,
        *,
        current_pane: str,
        lane_model: dict[str, object] | None = None,
    ) -> bool:
        if not job.dispatch_id or job.done_dispatch_id == job.dispatch_id:
            return False
        lane_model = dict(lane_model or self._verify_wrapper_model())
        done_task = dict(lane_model.get("done_task") or {})
        if not done_task:
            return False

        done_dispatch_id = str(done_task.get("dispatch_id") or "")
        if not done_dispatch_id or done_dispatch_id != job.dispatch_id:
            return False

        done_ts = float(lane_model.get("done_ts") or 0.0)
        job.done_dispatch_id = job.dispatch_id
        job.done_at = done_ts if done_ts > 0.0 else time.time()
        job.last_activity_at = job.done_at
        job.last_pane_snapshot = current_pane
        job.save(self.state_dir)
        return True

    def _record_dispatch_stall(
        self,
        job: JobState,
        *,
        current_pane: str,
        reason: str,
        stage: str,
        lane_note: str,
    ) -> JobState:
        fingerprint = self._dispatch_stall_fingerprint(job, stage)
        now = time.time()
        same_fingerprint = fingerprint == job.dispatch_stall_fingerprint
        attempt = job.dispatch_stall_count + 1 if same_fingerprint else 1

        job.dispatch_stall_fingerprint = fingerprint
        job.dispatch_stall_count = attempt
        job.dispatch_stall_detected_at = now
        job.dispatch_stall_stage = stage
        job.lane_note = lane_note

        if attempt <= 1:
            job.degraded_reason = ""
            return self._requeue_verify_pending(job, current_pane=current_pane, reason=reason)

        self.dedupe.forget(job.job_id, job.round, job.artifact_hash, "slot_verify")
        job.last_failed_dispatch_at = now
        job.dispatch_fail_count += 1
        job.last_failed_dispatch_snapshot = "" if self.pane_text_is_idle(current_pane) else current_pane
        job.last_dispatch_slot = ""
        job.dispatch_id = ""
        job.seen_dispatch_id = ""
        job.seen_at = 0.0
        job.accept_deadline_at = 0.0
        job.accepted_dispatch_id = ""
        job.accepted_at = 0.0
        job.degraded_reason = "dispatch_stall"
        self.lease.release("slot_verify")
        job.transition(JobStatus.VERIFY_PENDING, reason)
        job.save(self.state_dir)
        return job

    def _record_completion_stall(
        self,
        job: JobState,
        *,
        current_pane: str,
        reason: str,
        stage: str,
        lane_note: str,
    ) -> JobState:
        fingerprint = self._completion_stall_fingerprint(job, stage)
        now = time.time()
        same_fingerprint = fingerprint == job.completion_stall_fingerprint
        attempt = job.completion_stall_count + 1 if same_fingerprint else 1

        job.completion_stall_fingerprint = fingerprint
        job.completion_stall_count = attempt
        job.completion_stall_detected_at = now
        job.completion_stall_stage = stage
        job.lane_note = lane_note

        if attempt <= 1:
            job.degraded_reason = ""
            return self._requeue_verify_pending(job, current_pane=current_pane, reason=reason)

        self.dedupe.forget(job.job_id, job.round, job.artifact_hash, "slot_verify")
        job.last_failed_dispatch_at = now
        job.dispatch_fail_count += 1
        job.last_failed_dispatch_snapshot = "" if self.pane_text_is_idle(current_pane) else current_pane
        job.last_dispatch_slot = ""
        job.dispatch_id = ""
        job.seen_dispatch_id = ""
        job.seen_at = 0.0
        job.accept_deadline_at = 0.0
        job.accepted_dispatch_id = ""
        job.accepted_at = 0.0
        self._clear_done_tracking(job)
        job.degraded_reason = "post_accept_completion_stall"
        self.lease.release("slot_verify")
        job.transition(JobStatus.VERIFY_PENDING, reason)
        job.save(self.state_dir)
        return job

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

    def _requeue_verify_pending(
        self,
        job: JobState,
        *,
        current_pane: str,
        reason: str,
    ) -> JobState:
        self.dedupe.forget(job.job_id, job.round, job.artifact_hash, "slot_verify")
        job.last_failed_dispatch_at = time.time()
        job.dispatch_fail_count += 1
        job.last_failed_dispatch_snapshot = "" if self.pane_text_is_idle(current_pane) else current_pane
        job.last_dispatch_slot = ""
        job.dispatch_id = ""
        job.seen_dispatch_id = ""
        job.seen_at = 0.0
        job.accept_deadline_at = 0.0
        job.accepted_dispatch_id = ""
        job.accepted_at = 0.0
        self._clear_done_tracking(job)
        self.lease.release("slot_verify")
        job.transition(JobStatus.VERIFY_PENDING, reason)
        job.save(self.state_dir)
        return job

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

    def _handle_new_artifact(self, job: JobState) -> JobState:
        job.transition(JobStatus.STABILIZING, "new artifact detected")
        job.save(self.state_dir)
        return job

    def _handle_stabilizing(self, job: JobState) -> JobState:
        if not self.stabilizer.check(job.job_id, job.artifact_path):
            return job
        path = Path(job.artifact_path)
        stat = path.stat()
        job.artifact_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        job.artifact_size = stat.st_size
        job.artifact_mtime = stat.st_mtime
        job.stabilized_at = time.time()
        self.stabilizer.clear(job.job_id)
        job.transition(JobStatus.VERIFY_PENDING, "artifact stabilized")
        job.save(self.state_dir)
        return job

    def _handle_verify_pending(self, job: JobState) -> JobState:
        slot = "slot_verify"

        if job.degraded_reason in {"dispatch_stall", "post_accept_completion_stall"}:
            self.dedupe.mark_suppressed(
                job.job_id,
                job.round,
                job.artifact_hash,
                slot,
                "dispatch_stall_degraded"
                if job.degraded_reason == "dispatch_stall"
                else "completion_stall_degraded",
            )
            return job

        if job.last_failed_dispatch_at:
            backoff_deadline = job.last_failed_dispatch_at + self.verify_retry_backoff_sec
            if time.time() < backoff_deadline:
                self.dedupe.mark_suppressed(job.job_id, job.round, job.artifact_hash, slot, "dispatch_backoff")
                return job

            if job.last_failed_dispatch_snapshot:
                current_pane = self.capture_pane_text(self.verify_pane_target)
                if current_pane == job.last_failed_dispatch_snapshot:
                    self.dedupe.mark_suppressed(
                        job.job_id, job.round, job.artifact_hash, slot, "dispatch_backoff_same_snapshot"
                    )
                    return job

        if self.dedupe.is_duplicate(job.job_id, job.round, job.artifact_hash, slot):
            self.dedupe.mark_suppressed(job.job_id, job.round, job.artifact_hash, slot, "dedupe")
            return job

        if not self.lease.acquire(slot, job.job_id, job.round, self.verify_pane_target):
            self.dedupe.mark_suppressed(job.job_id, job.round, job.artifact_hash, slot, "lease_busy")
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
        if job.dispatch_control_seq < 0:
            try:
                job.dispatch_control_seq = int(prompt_context.get("next_control_seq") or -1)
            except (TypeError, ValueError):
                job.dispatch_control_seq = -1

        prompt = self.normalize_prompt_text(self.verify_prompt_template.format(**prompt_context))
        ok = self.send_keys(self.verify_pane_target, prompt, self.dry_run, self.verify_pane_type)

        if ok:
            self.dedupe.mark_dispatch(
                job.job_id, job.round, job.artifact_hash, slot, self.verify_pane_target, self.dry_run
            )
            job.last_dispatch_at = time.time()
            job.last_dispatch_slot = slot
            job.last_failed_dispatch_at = 0.0
            job.last_failed_dispatch_snapshot = ""
            job.dispatch_fail_count = 0
            job.dispatch_id = hashlib.sha1(
                "|".join(
                    [
                        job.job_id,
                        str(job.round),
                        job.artifact_hash,
                        slot,
                        f"{job.last_dispatch_at:.6f}",
                    ]
                ).encode("utf-8")
            ).hexdigest()
            job.seen_dispatch_id = ""
            job.seen_at = 0.0
            job.accept_deadline_at = job.last_dispatch_at + self.verify_accept_deadline_sec
            job.accepted_dispatch_id = ""
            job.accepted_at = 0.0
            self._clear_done_tracking(job)
            job.dispatch_stall_stage = ""
            if self.feedback_sig_builder is not None:
                job.feedback_baseline_sig, job.verify_feedback_baseline_sig = self.feedback_sig_builder(job)
            else:
                job.feedback_baseline_sig = compute_multi_file_sig(self.completion_paths)
                job.verify_feedback_baseline_sig = ""
            if self.verify_receipt_builder is not None:
                job.verify_receipt_baseline_path, job.verify_receipt_baseline_mtime = self.verify_receipt_builder(job)
            else:
                job.verify_receipt_baseline_path = ""
                job.verify_receipt_baseline_mtime = 0.0
            self._clear_dispatch_stall_surface(job)
            job.transition(JobStatus.VERIFY_RUNNING, f"dispatched to {slot}")
            job.save(self.state_dir)
            if self.dry_run:
                self.lease.release(slot)
        else:
            job.last_failed_dispatch_at = time.time()
            job.dispatch_fail_count += 1
            job.last_failed_dispatch_snapshot = self.capture_pane_text(self.verify_pane_target)
            job.dispatch_id = ""
            job.seen_dispatch_id = ""
            job.seen_at = 0.0
            job.accept_deadline_at = 0.0
            job.accepted_dispatch_id = ""
            job.accepted_at = 0.0
            self._clear_done_tracking(job)
            job.save(self.state_dir)
            self.lease.release(slot)
        return job

    def _handle_verify_running(self, job: JobState) -> JobState:
        manifest = self.collector.poll(job)
        if manifest is None:
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
                and verify_receipt_mtime >= (job.last_dispatch_at - 1.0)
                and (
                    verify_receipt_path != job.verify_receipt_baseline_path
                    or verify_receipt_mtime > job.verify_receipt_baseline_mtime
                )
            )
            outputs_complete = control_changed and verify_changed and verify_receipt_present

            current_pane = self.capture_pane_text(self.verify_pane_target)
            still_busy = self.pane_text_has_busy_indicator(current_pane)
            has_prompt = self.pane_text_has_input_cursor(current_pane)
            codex_idle = has_prompt and not still_busy
            now_value = time.time()
            elapsed_since_dispatch = now_value - job.last_dispatch_at
            stale_dispatch_before_runtime = (
                job.last_dispatch_at > 0.0
                and job.last_dispatch_at < self.runtime_started_at
            )
            elapsed = now_value - job.last_dispatch_at
            last_activity = job.last_activity_at or job.last_dispatch_at

            if current_pane != job.last_pane_snapshot:
                job.last_pane_snapshot = current_pane
                job.last_activity_at = now_value
                job.save(self.state_dir)
            lane_model = self._verify_wrapper_model() if job.dispatch_id else {}
            dispatch_seen = self._mark_dispatch_seen_if_seen(job, current_pane=current_pane, lane_model=lane_model)
            dispatch_accepted = self._mark_dispatch_accepted_if_seen(
                job, current_pane=current_pane, lane_model=lane_model
            )
            task_done = self._mark_task_done_if_seen(job, current_pane=current_pane, lane_model=lane_model)
            if dispatch_seen and not dispatch_accepted:
                last_activity = job.last_activity_at or now_value
            if dispatch_accepted:
                last_activity = job.last_activity_at or now_value
            if task_done:
                last_activity = job.last_activity_at or now_value
            waiting_for_accept = bool(job.dispatch_id) and job.accepted_dispatch_id != job.dispatch_id
            waiting_for_done = (
                bool(job.dispatch_id)
                and job.accepted_dispatch_id == job.dispatch_id
                and job.done_dispatch_id != job.dispatch_id
            )
            waiting_for_receipt_close = (
                bool(job.dispatch_id)
                and job.done_dispatch_id == job.dispatch_id
                and not outputs_complete
            )
            if (
                stale_dispatch_before_runtime
                and codex_idle
                and elapsed_since_dispatch >= self.restart_recovery_grace_sec
                and not outputs_complete
                and waiting_for_accept
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
                job.dispatch_id = ""
                job.seen_dispatch_id = ""
                job.seen_at = 0.0
                job.accept_deadline_at = 0.0
                job.accepted_dispatch_id = ""
                job.accepted_at = 0.0
                self._clear_done_tracking(job)
                self.lease.release("slot_verify")
                job.transition(
                    JobStatus.VERIFY_PENDING,
                    f"startup recovery after stale dispatch ({elapsed_since_dispatch:.0f}s old, pane idle)",
                )
                job.save(self.state_dir)
                return job

            if waiting_for_accept and not outputs_complete:
                if job.accept_deadline_at > 0.0 and now_value >= job.accept_deadline_at:
                    log.warning(
                        "verify accept deadline exceeded: job=%s total=%.0fs deadline=%.0fs",
                        job.job_id,
                        elapsed,
                        self.verify_accept_deadline_sec,
                    )
                    seen_dispatch = job.seen_dispatch_id == job.dispatch_id
                    stall_stage = "task_accept_missing" if seen_dispatch else "dispatch_seen_missing"
                    stall_note = "waiting_task_accept_after_dispatch" if seen_dispatch else "waiting_dispatch_seen_after_dispatch"
                    stall_reason = (
                        f"dispatch stall after {elapsed:.0f}s total with no TASK_ACCEPTED "
                        f"after DISPATCH_SEEN before {self.verify_accept_deadline_sec:.0f}s deadline"
                        if seen_dispatch
                        else f"dispatch stall after {elapsed:.0f}s total with no DISPATCH_SEEN before {self.verify_accept_deadline_sec:.0f}s deadline"
                    )
                    return self._record_dispatch_stall(
                        job,
                        current_pane=current_pane,
                        reason=stall_reason,
                        stage=stall_stage,
                        lane_note=stall_note,
                    )
                return job

            if waiting_for_done:
                if still_busy:
                    refreshed = False
                    if now_value - (job.last_activity_at or 0.0) >= 5.0:
                        job.last_activity_at = now_value
                        refreshed = True
                    extended_done_deadline = now_value + self.verify_done_deadline_sec
                    if extended_done_deadline > (job.done_deadline_at + 1.0):
                        job.done_deadline_at = extended_done_deadline
                        refreshed = True
                    if refreshed:
                        job.last_pane_snapshot = current_pane
                        job.save(self.state_dir)
                    return job
                if job.done_deadline_at > 0.0 and now_value >= job.done_deadline_at:
                    log.warning(
                        "verify done deadline exceeded: job=%s total=%.0fs deadline=%.0fs",
                        job.job_id,
                        elapsed,
                        self.verify_done_deadline_sec,
                    )
                    return self._record_completion_stall(
                        job,
                        current_pane=current_pane,
                        reason=(
                            f"completion stall after {elapsed:.0f}s total with no TASK_DONE "
                            f"after TASK_ACCEPTED before {self.verify_done_deadline_sec:.0f}s deadline"
                        ),
                        stage="task_done_missing",
                        lane_note="waiting_task_done_after_accept",
                    )
                if outputs_complete:
                    log.info(
                        "current-round verify/control/receipt changed before TASK_DONE, keeping verify open: job=%s",
                        job.job_id,
                    )
                if codex_idle and elapsed_since_dispatch > 15:
                    log.info(
                        "codex idle observed after TASK_ACCEPTED but TASK_DONE is still missing: job=%s elapsed=%.0fs",
                        job.job_id,
                        elapsed_since_dispatch,
                    )
                return job

            if outputs_complete:
                log.info(
                    "current-round verify receipt + control changed after TASK_DONE: job=%s, treating as verify done",
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
                self._clear_dispatch_stall_state(job)
                self.lease.release("slot_verify")
                job.transition(JobStatus.VERIFY_DONE, "current-round verify receipt + control changed after TASK_DONE")
                job.save(self.state_dir)
                return job
            if control_changed and verify_changed and not verify_receipt_present:
                log.info(
                    "control + /verify tree changed but current-round /verify receipt is still missing after TASK_DONE: job=%s receipt=%s baseline=%s",
                    job.job_id,
                    verify_receipt_path or "none",
                    job.verify_receipt_baseline_path or "none",
                )
            if control_changed and not verify_changed:
                log.info("control slot changed but /verify not updated yet after TASK_DONE: job=%s", job.job_id)
            if codex_idle and elapsed_since_dispatch > 15 and not (control_changed and verify_changed):
                log.info(
                    "codex idle observed after TASK_DONE but required close outputs are incomplete: job=%s elapsed=%.0fs done=%s",
                    job.job_id,
                    elapsed_since_dispatch,
                    task_done or bool(job.done_at),
                )

            if waiting_for_receipt_close and current_pane == job.last_pane_snapshot:
                idle_sec = now_value - last_activity
                if codex_idle and idle_sec > self.verify_incomplete_idle_retry_sec:
                    log.warning(
                        "verify task done but close outputs are incomplete: job=%s idle=%.0fs total=%.0fs",
                        job.job_id,
                        idle_sec,
                        elapsed,
                    )
                    return self._record_completion_stall(
                        job,
                        current_pane=current_pane,
                        reason=(
                            f"completion stall after TASK_DONE with missing receipt/control close for "
                            f"{idle_sec:.0f}s idle, {elapsed:.0f}s total"
                        ),
                        stage="receipt_close_missing",
                        lane_note="waiting_receipt_close_after_task_done",
                    )
            return job

        manifest_path = self.collector.manifest_path(job.job_id, job.round)
        valid, reason = self.collector.validate(manifest, job)
        if not valid:
            job.verify_result = "invalid_manifest"
            job.save(self.state_dir)
            self._log_error(job.job_id, job.round, "invalid_manifest", reason, str(manifest_path))
            log.warning("invalid manifest: job=%s round=%d reason=%s", job.job_id, job.round, reason)
            return job

        scores = self.collector.extract_scores(manifest)
        job.validation_score = scores["validation_score"]
        job.blocker_count = scores["blocker_count"]
        job.verify_manifest_path = str(manifest_path)
        job.verify_completed_at = time.time()
        job.verify_result = "failed" if job.blocker_count > 0 else "passed"

        self._clear_dispatch_stall_state(job)
        self.lease.release("slot_verify")
        job.transition(
            JobStatus.VERIFY_DONE,
            f"manifest valid: result={job.verify_result} score={job.validation_score:.3f} blockers={job.blocker_count}",
        )
        job.save(self.state_dir)
        log.info(
            "VERIFY_DONE: job=%s round=%d result=%s score=%.3f blockers=%d",
            job.job_id,
            job.round,
            job.verify_result,
            job.validation_score,
            job.blocker_count,
        )
        return job

    def _log_error(self, job_id: str, round_: int, error_type: str, reason: str, manifest_path: str) -> None:
        self.error_log.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": "manifest_error",
            "job_id": job_id,
            "round": round_,
            "error_type": error_type,
            "reason": reason,
            "manifest_path": manifest_path,
            "at": time.time(),
        }
        with self.error_log.open("a") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

