from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Optional

from pipeline_runtime.schema import (
    PipelineControlSnapshot,
    append_jsonl,
    read_json,
    read_pipeline_control_snapshot,
)
from pipeline_runtime.lane_surface import pane_text_has_unsubmitted_pasted_content
from pipeline_runtime.wrapper_events import build_lane_read_models

# --------------- backward-compat re-exports from watcher_state ---------------
# JobState, JobStatus, and TERMINAL_STATES are defined in watcher_state.py.
# Keep them importable from verify_fsm for older callers; new code should import
# these watcher state types from watcher_state directly.
# SCHEMA_VERSION is an internal compatibility alias for persisted JobState
# payloads and is intentionally not exported through __all__.
# ---------------------------------------------------------------------------
from watcher_state import (
    JOB_STATE_SCHEMA_VERSION as SCHEMA_VERSION,
    JobState,
    JobStatus,
    TERMINAL_STATES,
)

__all__ = [
    # Public API owned by verify_fsm.
    "StateMachine",
    "make_job_id",
    "compute_file_sig",
    "compute_md_tree_sig",
    "compute_multi_file_sig",
    # Backward-compatible watcher_state re-exports.
    "JobState",
    "JobStatus",
    "TERMINAL_STATES",
]

log = logging.getLogger("watcher_core")

CODEX_VERIFY_DISPATCH_FAILURE_LOOP_REASON = "codex_verify_dispatch_failure_loop"
DISPATCH_FAILED_SUBMIT_STAGE = "dispatch_failed_submit"


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
        clear_failed_dispatch_input: Optional[Callable[[str, str], bool]] = None,
        dry_run: bool = False,
        pipeline_dir: Optional[Path] = None,
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
        self.clear_failed_dispatch_input = clear_failed_dispatch_input
        self.dry_run = dry_run
        self.pipeline_dir = pipeline_dir

    def _pipeline_control_seq(self) -> int:
        if self.pipeline_dir is None:
            return -1
        pipeline_snapshot: PipelineControlSnapshot = read_pipeline_control_snapshot(self.pipeline_dir)
        active_snapshot = pipeline_snapshot.get("active") or {}
        raw_seq = active_snapshot.get("control_seq")
        if isinstance(raw_seq, bool):
            return -1
        try:
            return int(raw_seq)
        except (TypeError, ValueError):
            return -1

    def _release_verify_lease(self, slot: str, job: JobState | None = None, *, reason: str = "") -> None:
        self.lease.release(slot)
        if self.error_log and reason:
            append_jsonl(
                self.error_log,
                {
                    "event": "lease_released",
                    "slot": slot,
                    "job_id": job.job_id if job else "",
                    "reason": reason,
                },
            )

    def release_verify_lease_for_archive(self, job: JobState) -> None:
        self._release_verify_lease("slot_verify", job, reason="archive_matching_verified_pending")

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
        accepted_seen_at = 0.0
        # wrapper read model은 최신 current state를 평탄화하므로, polling 타이밍이 늦으면
        # 같은 dispatch의 TASK_ACCEPTED가 already-folded TASK_DONE 뒤에 보이지 않을 수 있다.
        # 이 경우 current dispatch의 matching TASK_DONE는 이미 accept가 있었다는 더 강한 증거다.
        if not accepted_task:
            done_task = dict(lane_model.get("done_task") or {})
            done_dispatch_id = str(done_task.get("dispatch_id") or "")
            if done_dispatch_id and done_dispatch_id == job.dispatch_id:
                accepted_task = {
                    "job_id": str(done_task.get("job_id") or job.job_id),
                    "dispatch_id": done_dispatch_id,
                    "control_seq": int(done_task.get("control_seq") or -1),
                    "attempt": int(done_task.get("attempt") or 0),
                }
                accepted_seen_at = float(lane_model.get("done_ts") or lane_model.get("last_event_ts") or 0.0)
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
        job.accepted_at = accepted_seen_at if accepted_seen_at > 0.0 else time.time()
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

    def _mark_task_done_from_completed_outputs(
        self,
        job: JobState,
        *,
        current_pane: str,
        reason: str,
    ) -> None:
        now = time.time()
        job.done_dispatch_id = job.dispatch_id
        job.done_at = now
        job.last_activity_at = now
        job.last_pane_snapshot = current_pane
        job.history.append(
            {
                "from": job.status.value,
                "to": job.status.value,
                "at": now,
                "reason": reason,
            }
        )
        job.save(self.state_dir)

    def _failed_dispatch_snapshot_for_pane(self, current_pane: str) -> str:
        snapshot = (current_pane or "").rstrip()
        if not snapshot:
            return ""
        if pane_text_has_unsubmitted_pasted_content(snapshot):
            return ""
        if "[Pasted Content" in snapshot:
            return snapshot
        if self.pane_text_is_idle(snapshot):
            return ""
        return snapshot

    def _current_pane_is_clearable_pasted_prompt(
        self,
        current_pane: str,
        last_failed_snapshot: str,
    ) -> bool:
        if "[Pasted Content" not in str(last_failed_snapshot or ""):
            return False
        return pane_text_has_unsubmitted_pasted_content(current_pane)

    def _codex_snapshot_has_pasted_content(self, text: str) -> bool:
        if self.verify_pane_type != "codex":
            return False
        snapshot = str(text or "")
        return "[Pasted Content" in snapshot or pane_text_has_unsubmitted_pasted_content(snapshot)

    def _mark_codex_dispatch_failure_loop(
        self,
        job: JobState,
        *,
        now: float,
    ) -> None:
        job.dispatch_fail_count = max(job.dispatch_fail_count, max(1, job.retry_budget))
        fingerprint = self._dispatch_stall_fingerprint(job, DISPATCH_FAILED_SUBMIT_STAGE)
        if fingerprint == job.dispatch_stall_fingerprint:
            job.dispatch_stall_count += 1
        else:
            job.dispatch_stall_fingerprint = fingerprint
            job.dispatch_stall_count = 1
        job.dispatch_stall_detected_at = now
        job.dispatch_stall_stage = DISPATCH_FAILED_SUBMIT_STAGE
        job.degraded_reason = CODEX_VERIFY_DISPATCH_FAILURE_LOOP_REASON
        job.lane_note = CODEX_VERIFY_DISPATCH_FAILURE_LOOP_REASON

    def _clear_failed_dispatch_input_if_possible(self, job: JobState, slot: str, reason: str) -> bool:
        if self.clear_failed_dispatch_input is None:
            return False
        if self.verify_pane_type != "codex":
            return False
        if not self.clear_failed_dispatch_input(self.verify_pane_target, reason):
            return False
        job.last_failed_dispatch_at = 0.0
        job.last_failed_dispatch_snapshot = ""
        job.lane_note = "cleared_failed_dispatch_prompt"
        job.save(self.state_dir)
        self.dedupe.forget(job.job_id, job.round, job.artifact_hash, slot)
        return True

    def _forget_requeued_failed_dispatch_dedupe(self, job: JobState, slot: str) -> None:
        if job.last_failed_dispatch_at <= 0.0 or job.last_dispatch_at <= 0.0:
            return
        if job.last_failed_dispatch_at < job.last_dispatch_at:
            return
        self.dedupe.forget(job.job_id, job.round, job.artifact_hash, slot)

    def _build_verify_prompt(self, job: JobState) -> tuple[dict[str, str], str]:
        prompt_context = {
            "job_id": job.job_id,
            "round": job.round,
            "artifact_path": job.artifact_path,
            "latest_work_path": job.artifact_path,
            "latest_verify_path": "없음",
        }
        if self.verify_context_builder:
            prompt_context.update(self.verify_context_builder(job))
        prompt = self.normalize_prompt_text(self.verify_prompt_template.format(**prompt_context))
        return prompt_context, prompt

    def _prompt_marker_map(self, prompt: str) -> dict[str, str]:
        markers: dict[str, str] = {}
        for raw_line in prompt.splitlines():
            line = raw_line.strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not value:
                continue
            if key in {"ROLE", "OWNER", "NEXT_CONTROL_SEQ", "WORK", "VERIFY"}:
                markers[key] = f"{key}: {value}"
        return markers

    def _pane_contains_prompt_markers(self, current_pane: str, prompt: str) -> bool:
        pane_text = (current_pane or "").replace("\r\n", "\n")
        markers = self._prompt_marker_map(prompt)
        required = [markers.get("ROLE"), markers.get("OWNER"), markers.get("NEXT_CONTROL_SEQ")]
        if not all(marker and marker in pane_text for marker in required):
            return False
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
        job.last_failed_dispatch_snapshot = self._failed_dispatch_snapshot_for_pane(current_pane)
        job.last_dispatch_slot = ""
        job.dispatch_id = ""
        job.seen_dispatch_id = ""
        job.seen_at = 0.0
        job.accept_deadline_at = 0.0
        job.accepted_dispatch_id = ""
        job.accepted_at = 0.0
        job.degraded_reason = "dispatch_stall"
        self._release_verify_lease("slot_verify", job, reason="dispatch_stall_degraded")
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
        job.last_failed_dispatch_snapshot = self._failed_dispatch_snapshot_for_pane(current_pane)
        job.last_dispatch_slot = ""
        job.dispatch_id = ""
        job.seen_dispatch_id = ""
        job.seen_at = 0.0
        job.accept_deadline_at = 0.0
        job.accepted_dispatch_id = ""
        job.accepted_at = 0.0
        self._clear_done_tracking(job)
        job.degraded_reason = "post_accept_completion_stall"
        self._release_verify_lease("slot_verify", job, reason="completion_stall_degraded")
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
        job.last_failed_dispatch_snapshot = self._failed_dispatch_snapshot_for_pane(current_pane)
        job.last_dispatch_slot = ""
        job.dispatch_id = ""
        job.seen_dispatch_id = ""
        job.seen_at = 0.0
        job.accept_deadline_at = 0.0
        job.accepted_dispatch_id = ""
        job.accepted_at = 0.0
        self._clear_done_tracking(job)
        self._release_verify_lease("slot_verify", job, reason="requeue_verify_pending")
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

    def step_verify_close_chain(self, job: JobState) -> JobState:
        """Advance the verify close chain owned by this FSM.

        Watcher polling owns discovery/routing only. The ordered
        TASK_ACCEPTED -> TASK_DONE -> receipt/control close transition stays
        here so consumers do not reinterpret a running verify round.
        """
        if job.status != JobStatus.VERIFY_RUNNING:
            return job
        return self._handle_verify_running(job)

    def reset_job_for_new_round(self, job: JobState, job_id: str, reason: str) -> JobState:
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
        self._clear_dispatch_stall_state(job)
        if self.stabilizer is not None:
            self.stabilizer.clear(job_id)
        job.transition(JobStatus.STABILIZING, f"{reason}, round={job.round}")
        job.save(self.state_dir)
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
        prompt_context, prompt = self._build_verify_prompt(job)

        if job.dispatch_control_seq < 0:
            try:
                job.dispatch_control_seq = int(prompt_context.get("next_control_seq") or -1)
            except (TypeError, ValueError):
                job.dispatch_control_seq = -1

        degraded_suppression_reasons = {
            "dispatch_stall": "dispatch_stall_degraded",
            "post_accept_completion_stall": "completion_stall_degraded",
            CODEX_VERIFY_DISPATCH_FAILURE_LOOP_REASON: "dispatch_failure_loop_degraded",
        }
        degraded_suppression_reason = degraded_suppression_reasons.get(job.degraded_reason)
        if degraded_suppression_reason:
            self.dedupe.mark_suppressed(
                job.job_id,
                job.round,
                job.artifact_hash,
                slot,
                degraded_suppression_reason,
            )
            return job

        if job.last_failed_dispatch_at:
            backoff_deadline = job.last_failed_dispatch_at + self.verify_retry_backoff_sec
            if time.time() < backoff_deadline:
                self.dedupe.mark_suppressed(job.job_id, job.round, job.artifact_hash, slot, "dispatch_backoff")
                return job

            if job.last_failed_dispatch_snapshot:
                current_pane = self.capture_pane_text(self.verify_pane_target)
                current_snapshot = self._failed_dispatch_snapshot_for_pane(current_pane)
                if self._codex_snapshot_has_pasted_content(
                    job.last_failed_dispatch_snapshot
                ) or self._codex_snapshot_has_pasted_content(current_pane):
                    now = time.time()
                    job.last_failed_dispatch_at = now
                    job.last_failed_dispatch_snapshot = (
                        current_snapshot
                        or current_pane.rstrip()
                        or job.last_failed_dispatch_snapshot
                    )
                    self._mark_codex_dispatch_failure_loop(job, now=now)
                    job.save(self.state_dir)
                    self.dedupe.mark_suppressed(
                        job.job_id,
                        job.round,
                        job.artifact_hash,
                        slot,
                        "dispatch_failure_loop_degraded",
                    )
                    return job
                clearable_pasted_prompt = self._current_pane_is_clearable_pasted_prompt(
                    current_pane,
                    job.last_failed_dispatch_snapshot,
                )
                cleared_failed_dispatch_prompt = False
                if self._pane_contains_prompt_markers(current_pane, prompt):
                    if self._clear_failed_dispatch_input_if_possible(
                        job,
                        slot,
                        "dispatch_backoff_prompt_visible",
                    ):
                        cleared_failed_dispatch_prompt = True
                        current_pane = ""
                        current_snapshot = ""
                    else:
                        job.last_failed_dispatch_at = time.time()
                        job.last_failed_dispatch_snapshot = current_snapshot or current_pane.rstrip()
                        job.save(self.state_dir)
                        self.dedupe.mark_suppressed(
                            job.job_id, job.round, job.artifact_hash, slot, "dispatch_backoff_prompt_visible"
                        )
                        return job
                if not cleared_failed_dispatch_prompt and not clearable_pasted_prompt and (
                    (
                        current_snapshot
                        and current_snapshot == job.last_failed_dispatch_snapshot
                    )
                    or current_pane.rstrip() == job.last_failed_dispatch_snapshot
                ):
                    job.last_failed_dispatch_at = time.time()
                    job.last_failed_dispatch_snapshot = current_snapshot or current_pane.rstrip()
                    job.save(self.state_dir)
                    self.dedupe.mark_suppressed(
                        job.job_id, job.round, job.artifact_hash, slot, "dispatch_backoff_same_snapshot"
                    )
                    return job

        self._forget_requeued_failed_dispatch_dedupe(job, slot)

        if self.dedupe.is_duplicate(job.job_id, job.round, job.artifact_hash, slot):
            self.dedupe.mark_suppressed(job.job_id, job.round, job.artifact_hash, slot, "dedupe")
            return job

        if not self.lease.acquire(slot, job.job_id, job.round, self.verify_pane_target):
            self.dedupe.mark_suppressed(job.job_id, job.round, job.artifact_hash, slot, "lease_busy")
            return job

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
                job.feedback_baseline_sig = (
                    "" if self.pipeline_dir is not None else compute_multi_file_sig(self.completion_paths)
                )
                job.verify_feedback_baseline_sig = ""
            if self.pipeline_dir is not None:
                pipeline_control_seq = self._pipeline_control_seq()
                if pipeline_control_seq >= 0:
                    job.dispatch_control_seq = pipeline_control_seq
            if self.verify_receipt_builder is not None:
                job.verify_receipt_baseline_path, job.verify_receipt_baseline_mtime = self.verify_receipt_builder(job)
            else:
                job.verify_receipt_baseline_path = ""
                job.verify_receipt_baseline_mtime = 0.0
            self._clear_dispatch_stall_surface(job)
            job.transition(JobStatus.VERIFY_RUNNING, f"dispatched to {slot}")
            job.save(self.state_dir)
            if self.dry_run:
                self._release_verify_lease(slot, job, reason="dispatch_dry_run")
        else:
            now = time.time()
            job.last_failed_dispatch_at = now
            job.dispatch_fail_count += 1
            job.last_failed_dispatch_snapshot = self.capture_pane_text(self.verify_pane_target)
            job.dispatch_id = ""
            job.seen_dispatch_id = ""
            job.seen_at = 0.0
            job.accept_deadline_at = 0.0
            job.accepted_dispatch_id = ""
            job.accepted_at = 0.0
            self._clear_done_tracking(job)
            release_reason = "dispatch_failed"
            if self._codex_snapshot_has_pasted_content(
                job.last_failed_dispatch_snapshot
            ) or job.dispatch_fail_count >= max(1, job.retry_budget):
                self._mark_codex_dispatch_failure_loop(job, now=now)
                release_reason = "dispatch_failure_loop_degraded"
            job.save(self.state_dir)
            self._release_verify_lease(slot, job, reason=release_reason)
        return job

    def _handle_verify_running(self, job: JobState) -> JobState:
        manifest = self.collector.poll(job)
        if manifest is None:
            if self.feedback_sig_builder is not None:
                fb_sig, verify_sig = self.feedback_sig_builder(job)
            else:
                fb_sig = "" if self.pipeline_dir is not None else compute_multi_file_sig(self.completion_paths)
                verify_sig = ""
            if self.verify_receipt_builder is not None:
                verify_receipt_path, verify_receipt_mtime = self.verify_receipt_builder(job)
            else:
                verify_receipt_path, verify_receipt_mtime = "", 0.0

            if self.pipeline_dir is not None:
                current_seq = self._pipeline_control_seq()
                control_changed = job.dispatch_control_seq >= 0 and current_seq != job.dispatch_control_seq
            else:
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
            close_chain_done = (
                bool(job.dispatch_id)
                and job.accepted_dispatch_id == job.dispatch_id
                and job.done_dispatch_id == job.dispatch_id
            )
            waiting_for_accept = bool(job.dispatch_id) and job.accepted_dispatch_id != job.dispatch_id
            waiting_for_done = (
                bool(job.dispatch_id)
                and job.accepted_dispatch_id == job.dispatch_id
                and job.done_dispatch_id != job.dispatch_id
            )
            waiting_for_receipt_close = (
                close_chain_done
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
                self._release_verify_lease("slot_verify", job, reason="startup_recovery")
                job.transition(
                    JobStatus.VERIFY_PENDING,
                    f"startup recovery after stale dispatch ({elapsed_since_dispatch:.0f}s old, pane idle)",
                )
                job.save(self.state_dir)
                return job

            if waiting_for_accept:
                if still_busy:
                    # Codex can show a prompt while the current task is still
                    # running. Keep the same dispatch alive until the lane
                    # becomes idle or the wrapper emits TASK_ACCEPTED.
                    extended_accept_deadline = now_value + self.verify_accept_deadline_sec
                    if extended_accept_deadline > (job.accept_deadline_at + 1.0):
                        job.accept_deadline_at = extended_accept_deadline
                    job.last_activity_at = now_value
                    job.lane_note = "waiting_task_accept_lane_busy"
                    job.save(self.state_dir)
                    return job
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
                if outputs_complete:
                    log.info(
                        "verify close outputs changed before TASK_ACCEPTED; keeping verify open: job=%s",
                        job.job_id,
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
                idle_done_grace = min(self.verify_incomplete_idle_retry_sec, self.verify_done_deadline_sec)
                if outputs_complete and codex_idle and (now_value - last_activity) >= idle_done_grace:
                    log.warning(
                        "verify outputs closed and codex idle before TASK_DONE; inferring task done after idle grace: job=%s idle=%.0fs total=%.0fs",
                        job.job_id,
                        now_value - last_activity,
                        elapsed,
                    )
                    self._mark_task_done_from_completed_outputs(
                        job,
                        current_pane=current_pane,
                        reason=(
                            "inferred TASK_DONE from current-round verify receipt + control close "
                            f"after {idle_done_grace:.0f}s idle grace"
                        ),
                    )
                    waiting_for_done = False
                    waiting_for_receipt_close = False
                    close_chain_done = True
                if job.done_deadline_at > 0.0 and now_value >= job.done_deadline_at:
                    if outputs_complete and codex_idle:
                        log.warning(
                            "verify outputs closed before TASK_DONE; inferring task done from receipt/control close: job=%s total=%.0fs",
                            job.job_id,
                            elapsed,
                        )
                        self._mark_task_done_from_completed_outputs(
                            job,
                            current_pane=current_pane,
                            reason=(
                                "inferred TASK_DONE from current-round verify receipt + control close "
                                f"after {self.verify_done_deadline_sec:.0f}s deadline"
                            ),
                        )
                        waiting_for_done = False
                        waiting_for_receipt_close = False
                        close_chain_done = True
                    else:
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
                if waiting_for_done:
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

            if outputs_complete and not close_chain_done:
                log.info(
                    "verify close outputs changed before TASK_DONE; keeping verify open: job=%s",
                    job.job_id,
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
                self._release_verify_lease("slot_verify", job, reason="feedback_verify_complete")
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
        self._release_verify_lease("slot_verify", job, reason="manifest_verify_complete")
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
