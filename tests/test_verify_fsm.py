from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_fsm
from verify_fsm import JobState, JobStatus, StateMachine


class _Collector:
    def __init__(self, root: Path) -> None:
        self.root = root

    def poll(self, job: JobState) -> None:
        return None

    def manifest_path(self, job_id: str, round_number: int) -> Path:
        return self.root / f"{job_id}-r{round_number}.json"


class _Lease:
    def __init__(self) -> None:
        self.released: list[str] = []

    def acquire(self, slot: str, job_id: str, round_number: int, pane_target: str) -> bool:
        return True

    def release(self, slot: str) -> None:
        self.released.append(slot)


class _Dedupe:
    def forget(self, job_id: str, round_number: int, artifact_hash: str, slot: str) -> None:
        return None


def _make_machine(
    root: Path,
    *,
    pipeline_dir: Path | None,
    feedback_sig_builder=None,
    verify_receipt_builder=None,
) -> StateMachine:
    return StateMachine(
        project_root=root,
        verify_lane_name="Codex",
        state_dir=root / ".pipeline" / "state",
        stabilizer=None,
        lease=_Lease(),
        dedupe=_Dedupe(),
        collector=_Collector(root / ".pipeline" / "manifests"),
        verify_pane_target="codex-pane",
        verify_pane_type="codex",
        verify_prompt_template="verify {job_id}",
        verify_context_builder=None,
        feedback_sig_builder=feedback_sig_builder,
        verify_receipt_builder=verify_receipt_builder,
        verify_retry_backoff_sec=1.0,
        verify_incomplete_idle_retry_sec=30.0,
        verify_accept_deadline_sec=30.0,
        verify_done_deadline_sec=45.0,
        runtime_started_at=0.0,
        restart_recovery_grace_sec=15.0,
        completion_paths=[root / ".pipeline" / "implement_handoff.md"],
        error_log=root / ".pipeline" / "events" / "errors.jsonl",
        capture_pane_text=lambda target: "ready>",
        pane_text_has_busy_indicator=lambda text: False,
        pane_text_has_input_cursor=lambda text: True,
        pane_text_is_idle=lambda text: True,
        normalize_prompt_text=lambda text: text,
        send_keys=lambda target, prompt, dry_run, pane_type: True,
        dry_run=True,
        pipeline_dir=pipeline_dir,
    )


def _running_job(root: Path, *, dispatch_control_seq: int) -> JobState:
    artifact = root / "work" / "4" / "22" / "note.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("done\n", encoding="utf-8")
    now = time.time()
    job = JobState(
        job_id="job-1",
        status=JobStatus.VERIFY_RUNNING,
        artifact_path=str(artifact),
        artifact_hash="artifact-hash",
    )
    job.round = 1
    job.last_dispatch_at = now - 2.0
    job.dispatch_id = "dispatch-1"
    job.accepted_dispatch_id = "dispatch-1"
    job.accepted_at = now - 1.5
    job.done_dispatch_id = "dispatch-1"
    job.done_at = now - 1.0
    job.last_activity_at = now
    job.feedback_baseline_sig = "old-control"
    job.verify_feedback_baseline_sig = "old-verify"
    job.verify_receipt_baseline_path = "verify/old.md"
    job.verify_receipt_baseline_mtime = 1.0
    job.dispatch_control_seq = dispatch_control_seq
    return job


def _receipt_builder(root: Path):
    receipt = root / "verify" / "4" / "22" / "verify.md"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text("verified\n", encoding="utf-8")

    def _builder(job: JobState) -> tuple[str, float]:
        return str(receipt), receipt.stat().st_mtime

    return _builder


class VerifyFsmSnapshotCloseTest(unittest.TestCase):
    def test_release_verify_lease_calls_lease_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = _make_machine(root, pipeline_dir=None)

            with patch.object(machine.lease, "release") as release:
                machine._release_verify_lease("slot_verify")

            release.assert_called_once_with("slot_verify")

    def test_release_verify_lease_with_reason_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = _make_machine(root, pipeline_dir=None)
            job = _running_job(root, dispatch_control_seq=-1)

            machine._release_verify_lease("slot_verify", job, reason="unit_test")

            log_entry = json.loads(machine.error_log.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(log_entry["event"], "lease_released")
            self.assertEqual(log_entry["slot"], "slot_verify")
            self.assertEqual(log_entry["job_id"], "job-1")
            self.assertEqual(log_entry["reason"], "unit_test")

    def test_verify_close_chain_detects_control_seq_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = _make_machine(
                root,
                pipeline_dir=root / ".pipeline",
                feedback_sig_builder=lambda job: ("ignored-control", "new-verify"),
                verify_receipt_builder=_receipt_builder(root),
            )
            job = _running_job(root, dispatch_control_seq=9)

            with patch(
                "verify_fsm.read_pipeline_control_snapshot",
                return_value={"active": {"control_seq": 10}},
            ) as read_snapshot:
                result = machine._handle_verify_running(job)

            read_snapshot.assert_called_with(root / ".pipeline")
            self.assertEqual(result.status, JobStatus.VERIFY_DONE)
            self.assertEqual(result.verify_result, "passed_by_feedback")

    def test_verify_close_chain_no_change_same_seq(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = _make_machine(
                root,
                pipeline_dir=root / ".pipeline",
                feedback_sig_builder=lambda job: ("ignored-control", "new-verify"),
                verify_receipt_builder=_receipt_builder(root),
            )
            job = _running_job(root, dispatch_control_seq=10)

            with patch(
                "verify_fsm.read_pipeline_control_snapshot",
                return_value={"active": {"control_seq": 10}},
            ):
                result = machine._handle_verify_running(job)

            self.assertEqual(result.status, JobStatus.VERIFY_RUNNING)
            self.assertEqual(result.verify_result, "")

    def test_verify_close_chain_fallback_no_pipeline_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = _make_machine(root, pipeline_dir=None)
            job = _running_job(root, dispatch_control_seq=-1)

            with patch.object(verify_fsm, "compute_multi_file_sig", return_value="new-control") as compute_sig:
                result = machine._handle_verify_running(job)

            compute_sig.assert_called_once_with([root / ".pipeline" / "implement_handoff.md"])
            self.assertEqual(result.status, JobStatus.VERIFY_RUNNING)


if __name__ == "__main__":
    unittest.main()
