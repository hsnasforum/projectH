from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import pipeline_runtime_gate


class PipelineRuntimeGateSoakTest(unittest.TestCase):
    def test_run_soak_fails_when_degraded_is_seen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            time_values = iter([0.0, 0.0, 1.0])

            with mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")), \
                 mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")), \
                 mock.patch.object(
                     pipeline_runtime_gate,
                     "_read_status",
                     return_value={"runtime_state": "DEGRADED", "degraded_reason": "receipt_manifest:job-1:missing_manifest_path"},
                 ), \
                 mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None), \
                 mock.patch.object(pipeline_runtime_gate.time, "time", side_effect=lambda: next(time_values)):
                ok, summary = pipeline_runtime_gate.run_soak(
                    root,
                    mode="experimental",
                    session="aip-test",
                    duration_sec=0.5,
                    sample_interval_sec=0.5,
                )

            self.assertFalse(ok)
            self.assertEqual(summary["state_counts"]["DEGRADED"], 1)
            self.assertEqual(summary["degraded_counts"]["receipt_manifest:job-1:missing_manifest_path"], 1)
            self.assertFalse(summary["broken_seen"])
            self.assertTrue(summary["degraded_seen"])

    def test_run_soak_fails_when_operator_candidate_uses_fallback_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            time_values = iter([0.0, 0.0, 1.0])

            with mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")), \
                 mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")), \
                 mock.patch.object(
                     pipeline_runtime_gate,
                     "_read_status",
                     return_value={
                         "runtime_state": "RUNNING",
                         "control": {
                             "active_control_file": ".pipeline/operator_request.md",
                             "active_control_seq": 205,
                             "active_control_status": "needs_operator",
                         },
                         "autonomy": {
                             "mode": "needs_operator",
                             "reason_code": "approval_required",
                             "operator_policy": "immediate_publish",
                             "classification_source": "metadata_missing_fallback",
                         },
                     },
                 ), \
                 mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None), \
                 mock.patch.object(pipeline_runtime_gate.time, "time", side_effect=lambda: next(time_values)):
                ok, summary = pipeline_runtime_gate.run_soak(
                    root,
                    mode="experimental",
                    session="aip-test",
                    duration_sec=0.5,
                    sample_interval_sec=0.5,
                )

            self.assertFalse(ok)
            self.assertEqual(summary["classification_gate_failures"], 1)
            self.assertTrue(summary["classification_gate_details"])
            self.assertIn("classification_fallback_detected", summary["classification_gate_details"][0])

    def test_run_operator_classification_gate_fails_on_fallback_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current_run = root / ".pipeline" / "current_run.json"
            status_path = root / ".pipeline" / "runs" / "run-1" / "status.json"
            status_path.parent.mkdir(parents=True, exist_ok=True)
            current_run.parent.mkdir(parents=True, exist_ok=True)
            current_run.write_text(
                '{"run_id":"run-1","status_path":".pipeline/runs/run-1/status.json"}',
                encoding="utf-8",
            )
            status_path.write_text(
                '{"control":{"active_control_file":".pipeline/operator_request.md","active_control_status":"needs_operator"},'
                '"autonomy":{"mode":"needs_operator","reason_code":"approval_required","operator_policy":"immediate_publish",'
                '"classification_source":"metadata_fallback"}}',
                encoding="utf-8",
            )

            ok, detail = pipeline_runtime_gate.run_operator_classification_gate(root)

        self.assertFalse(ok)
        self.assertIn("classification_fallback_detected", detail)

    def test_prepare_synthetic_workspace_seeds_profile_and_work_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace, env = pipeline_runtime_gate.prepare_synthetic_workspace(Path(tmp))

            self.assertTrue((workspace / ".pipeline" / "config" / "agent_profile.json").exists())
            self.assertTrue(any((workspace / "work").rglob("*.md")))
            self.assertIn("PIPELINE_RUNTIME_LANE_COMMAND_CODEX", env)
            self.assertEqual(env["PIPELINE_RUNTIME_DISABLE_TOKEN_COLLECTOR"], "1")

    def test_finalize_synthetic_workspace_keeps_failed_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            retained, cleanup_mode = pipeline_runtime_gate._finalize_synthetic_workspace(
                workspace=Path(tmp),
                keep_workspace=False,
                ok=False,
            )

        self.assertTrue(retained)
        self.assertEqual(cleanup_mode, "retained_for_failure")

    def test_finalize_synthetic_workspace_schedules_background_delete_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(
                pipeline_runtime_gate,
                "_schedule_workspace_cleanup",
                return_value=(True, "background_delete_requested(pid=1234)"),
            ) as cleanup:
                retained, cleanup_mode = pipeline_runtime_gate._finalize_synthetic_workspace(
                    workspace=Path(tmp),
                    keep_workspace=False,
                    ok=True,
                )

        self.assertFalse(retained)
        self.assertEqual(cleanup_mode, "background_delete_requested(pid=1234)")
        cleanup.assert_called_once()

    def test_finalize_synthetic_workspace_retains_on_cleanup_schedule_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(
                pipeline_runtime_gate,
                "_schedule_workspace_cleanup",
                return_value=(False, "background_delete_failed:OSError"),
            ):
                retained, cleanup_mode = pipeline_runtime_gate._finalize_synthetic_workspace(
                    workspace=Path(tmp),
                    keep_workspace=False,
                    ok=True,
                )

        self.assertTrue(retained)
        self.assertEqual(cleanup_mode, "background_delete_failed:OSError")

    def test_status_ready_for_faults_requires_running_state_and_ready_lane(self) -> None:
        self.assertFalse(
            pipeline_runtime_gate._status_ready_for_faults(
                {"runtime_state": "STARTING", "lanes": [{"state": "READY", "attachable": True}]}
            )
        )
        self.assertFalse(
            pipeline_runtime_gate._status_ready_for_faults(
                {"runtime_state": "RUNNING", "lanes": [{"state": "BOOTING", "attachable": True}]}
            )
        )
        self.assertTrue(
            pipeline_runtime_gate._status_ready_for_faults(
                {"runtime_state": "RUNNING", "lanes": [{"state": "READY", "attachable": True}]}
            )
        )

    def test_pick_fault_lane_prefers_wrapper_event_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / ".pipeline" / "runs" / "run-1"
            (root / ".pipeline").mkdir(parents=True, exist_ok=True)
            run_dir.mkdir(parents=True, exist_ok=True)
            (root / ".pipeline" / "current_run.json").write_text(
                '{"run_id":"run-1","status_path":".pipeline/runs/run-1/status.json","events_path":".pipeline/runs/run-1/events.jsonl"}',
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text("{}", encoding="utf-8")
            wrapper_dir = run_dir / "wrapper-events"
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            (wrapper_dir / "claude.jsonl").write_text(
                '{"payload":{"pid":7777}}\n',
                encoding="utf-8",
            )

            lane, pid = pipeline_runtime_gate._pick_fault_lane(
                root,
                {"lanes": [{"name": "Claude", "state": "READY", "pid": 1234, "attachable": True}]},
            )

        self.assertEqual(lane, "Claude")
        self.assertEqual(pid, 7777)
