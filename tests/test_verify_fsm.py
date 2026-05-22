from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_fsm
import watcher_state
from pipeline_runtime.wrapper_events import append_wrapper_event
from verify_fsm import JobState, JobStatus, StateMachine


class VerifyFsmExportBoundaryTest(unittest.TestCase):
    def test_public_exports_distinguish_owned_api_and_compat_reexports(self) -> None:
        self.assertIn("StateMachine", verify_fsm.__all__)
        self.assertIn("compute_file_sig", verify_fsm.__all__)
        self.assertIn("JobState", verify_fsm.__all__)
        self.assertNotIn("SCHEMA_VERSION", verify_fsm.__all__)

        from verify_fsm import JobState as CompatJobState
        from verify_fsm import StateMachine as CompatStateMachine
        from verify_fsm import compute_file_sig

        self.assertIs(CompatJobState, watcher_state.JobState)
        self.assertIs(CompatStateMachine, StateMachine)
        self.assertIs(compute_file_sig, verify_fsm.compute_file_sig)


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

    def is_duplicate(self, job_id: str, round_number: int, artifact_hash: str, slot: str) -> bool:
        return False

    def mark_suppressed(
        self,
        job_id: str,
        round_number: int,
        artifact_hash: str,
        slot: str,
        reason: str,
    ) -> None:
        return None

    def mark_dispatch(
        self,
        job_id: str,
        round_number: int,
        artifact_hash: str,
        slot: str,
        pane_target: str,
        dry_run: bool,
    ) -> None:
        return None


def _make_machine(
    root: Path,
    *,
    pipeline_dir: Path | None,
    feedback_sig_builder=None,
    verify_receipt_builder=None,
    send_keys=None,
    verify_pane_type: str = "codex",
    verify_task_hint_writer=None,
) -> StateMachine:
    if send_keys is None:
        send_keys = lambda target, prompt, dry_run, pane_type: True
    return StateMachine(
        project_root=root,
        verify_lane_name="Codex",
        state_dir=root / ".pipeline" / "state",
        stabilizer=None,
        lease=_Lease(),
        dedupe=_Dedupe(),
        collector=_Collector(root / ".pipeline" / "manifests"),
        verify_pane_target="codex-pane",
        verify_pane_type=verify_pane_type,
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
        send_keys=send_keys,
        dry_run=True,
        pipeline_dir=pipeline_dir,
        verify_task_hint_writer=verify_task_hint_writer,
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


class VerifyFsmClaudeDispatchTest(unittest.TestCase):
    def test_claude_verify_dispatch_writes_task_hint_before_prompt_send(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "work" / "5" / "22" / "note.md"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("ready\n", encoding="utf-8")
            calls: list[tuple[str, object]] = []

            def _task_hint_writer(
                job_id: str,
                dispatch_id: str,
                control_seq: int,
                active: bool,
            ) -> None:
                calls.append(
                    (
                        "hint",
                        {
                            "job_id": job_id,
                            "dispatch_id": dispatch_id,
                            "control_seq": control_seq,
                            "active": active,
                        },
                    )
                )

            def _send_keys(target: str, prompt: str, dry_run: bool, pane_type: str) -> bool:
                calls.append(("send", {"pane_type": pane_type, "prompt": prompt}))
                self.assertEqual(calls[0][0], "hint")
                return True

            machine = _make_machine(
                root,
                pipeline_dir=None,
                send_keys=_send_keys,
                verify_pane_type="claude",
                verify_task_hint_writer=_task_hint_writer,
            )
            job = JobState(
                job_id="job-claude",
                status=JobStatus.VERIFY_PENDING,
                artifact_path=str(artifact),
                artifact_hash="artifact-hash",
            )
            job.dispatch_control_seq = 2125

            result = machine.step(job)

            self.assertEqual(result.status, JobStatus.VERIFY_RUNNING)
            self.assertEqual(calls[0][0], "hint")
            self.assertEqual(calls[1][0], "send")
            hint_payload = calls[0][1]
            self.assertEqual(hint_payload["job_id"], "job-claude")
            self.assertEqual(hint_payload["dispatch_id"], result.dispatch_id)
            self.assertEqual(hint_payload["control_seq"], 2125)
            self.assertTrue(hint_payload["active"])


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

    def test_release_verify_lease_for_archive_uses_archive_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = _make_machine(root, pipeline_dir=None)
            job = _running_job(root, dispatch_control_seq=-1)

            with patch.object(machine.lease, "release") as release:
                machine.release_verify_lease_for_archive(job)

            release.assert_called_once_with("slot_verify")
            log_entry = json.loads(machine.error_log.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(log_entry["event"], "lease_released")
            self.assertEqual(log_entry["slot"], "slot_verify")
            self.assertEqual(log_entry["job_id"], "job-1")
            self.assertEqual(log_entry["reason"], "archive_matching_verified_pending")

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

    def test_verify_close_chain_replays_task_accepted_task_done_then_receipt_close(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_dir = root / ".pipeline" / "runs" / "run-1" / "wrapper-events"
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            (root / ".pipeline" / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )
            machine = _make_machine(
                root,
                pipeline_dir=root / ".pipeline",
                feedback_sig_builder=lambda job: ("ignored-control", "new-verify"),
                verify_receipt_builder=_receipt_builder(root),
            )
            job = _running_job(root, dispatch_control_seq=9)
            job.accepted_dispatch_id = ""
            job.accepted_at = 0.0
            job.done_dispatch_id = ""
            job.done_at = 0.0
            job.done_deadline_at = 0.0

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_ACCEPTED",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 9,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="vendor_output",
            )
            with patch(
                "verify_fsm.read_pipeline_control_snapshot",
                return_value={"active": {"control_seq": 10}},
            ):
                result = machine.step_verify_close_chain(job)

            self.assertEqual(result.status, JobStatus.VERIFY_RUNNING)
            self.assertEqual(result.accepted_dispatch_id, job.dispatch_id)
            self.assertEqual(result.done_dispatch_id, "")
            self.assertEqual(result.verify_result, "")

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_DONE",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 9,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="vendor_output",
            )
            with patch(
                "verify_fsm.read_pipeline_control_snapshot",
                return_value={"active": {"control_seq": 10}},
            ):
                result = machine.step_verify_close_chain(job)

            self.assertEqual(result.status, JobStatus.VERIFY_DONE)
            self.assertEqual(result.done_dispatch_id, job.dispatch_id)
            self.assertEqual(result.verify_result, "passed_by_feedback")
            self.assertTrue(result.verify_manifest_path)

    def test_verify_close_outputs_do_not_close_before_task_accept_and_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = _make_machine(
                root,
                pipeline_dir=root / ".pipeline",
                feedback_sig_builder=lambda job: ("ignored-control", "new-verify"),
                verify_receipt_builder=_receipt_builder(root),
            )
            job = _running_job(root, dispatch_control_seq=9)
            job.accepted_dispatch_id = ""
            job.accepted_at = 0.0
            job.done_dispatch_id = ""
            job.done_at = 0.0
            job.done_deadline_at = 0.0
            job.accept_deadline_at = time.time() + 30.0

            with patch(
                "verify_fsm.read_pipeline_control_snapshot",
                return_value={"active": {"control_seq": 10}},
            ):
                result = machine.step_verify_close_chain(job)

            self.assertEqual(result.status, JobStatus.VERIFY_RUNNING)
            self.assertEqual(result.accepted_dispatch_id, "")
            self.assertEqual(result.done_dispatch_id, "")
            self.assertEqual(result.verify_result, "")
            self.assertEqual(result.verify_manifest_path, "")

    def test_verify_outputs_close_when_codex_idle_without_task_done_after_grace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = _make_machine(
                root,
                pipeline_dir=root / ".pipeline",
                feedback_sig_builder=lambda job: ("ignored-control", "new-verify"),
                verify_receipt_builder=_receipt_builder(root),
            )
            machine.verify_incomplete_idle_retry_sec = 5.0
            job = _running_job(root, dispatch_control_seq=9)
            job.done_dispatch_id = ""
            job.done_at = 0.0
            job.done_deadline_at = time.time() + 120.0
            job.last_pane_snapshot = "ready>"
            job.last_activity_at = time.time() - 10.0

            with patch(
                "verify_fsm.read_pipeline_control_snapshot",
                return_value={"active": {"control_seq": 10}},
            ):
                result = machine.step_verify_close_chain(job)

            self.assertEqual(result.status, JobStatus.VERIFY_DONE)
            self.assertEqual(result.done_dispatch_id, job.dispatch_id)
            self.assertEqual(result.verify_result, "passed_by_feedback")
            self.assertTrue(result.verify_manifest_path)

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

    def test_verify_accept_wait_extends_while_codex_lane_is_busy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = _make_machine(
                root,
                pipeline_dir=root / ".pipeline",
                feedback_sig_builder=lambda job: ("same-control", "same-verify"),
                verify_receipt_builder=lambda job: ("", 0.0),
            )
            job = _running_job(root, dispatch_control_seq=10)
            job.accepted_dispatch_id = ""
            job.accepted_at = 0.0
            job.done_dispatch_id = ""
            job.done_at = 0.0
            job.done_deadline_at = 0.0
            job.seen_dispatch_id = job.dispatch_id
            job.accept_deadline_at = time.time() - 1.0
            old_deadline = job.accept_deadline_at
            machine.capture_pane_text = lambda target: "• Working (12s • esc to interrupt)\n"
            machine.pane_text_has_busy_indicator = lambda text: True

            with patch(
                "verify_fsm.read_pipeline_control_snapshot",
                return_value={"active": {"control_seq": 10}},
            ):
                result = machine.step_verify_close_chain(job)

            self.assertEqual(result.status, JobStatus.VERIFY_RUNNING)
            self.assertEqual(result.accepted_dispatch_id, "")
            self.assertGreater(result.accept_deadline_at, old_deadline)
            self.assertEqual(result.lane_note, "waiting_task_accept_lane_busy")

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
