from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import pipeline_runtime_gate
from pipeline_runtime.supervisor import RuntimeSupervisor


class PipelineRuntimeGateSoakTest(unittest.TestCase):
    def test_wait_for_runtime_readiness_returns_last_snapshot_on_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            time_values = iter([0.0, 0.0, 0.6, 1.1, 1.2])
            stale_status = {
                "runtime_state": "STARTING",
                "watcher": {"alive": False, "pid": None},
                "lanes": [
                    {
                        "name": "Codex",
                        "state": "BOOTING",
                        "attachable": True,
                        "pid": 4242,
                        "note": "",
                        "last_event_at": "",
                        "last_heartbeat_at": "",
                    }
                ],
                "control": {"active_control_status": "implement"},
                "active_round": {"state": "VERIFY_PENDING"},
            }

            with mock.patch.object(
                pipeline_runtime_gate,
                "_read_status",
                side_effect=[stale_status, stale_status, stale_status],
            ), \
                mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None), \
                mock.patch.object(pipeline_runtime_gate.time, "time", side_effect=lambda: next(time_values)):
                ok, status, wait_sec = pipeline_runtime_gate._wait_for_runtime_readiness(
                    root,
                    timeout_sec=1.0,
                )

        self.assertFalse(ok)
        self.assertEqual(status, stale_status)
        self.assertGreaterEqual(wait_sec, 1.0)

    def test_run_soak_waits_for_ready_before_counting_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_status = {
                "runtime_state": "RUNNING",
                "watcher": {"alive": True, "pid": 123},
                "lanes": [{"name": "Codex", "state": "READY", "attachable": True, "pid": 456, "note": ""}],
                "control": {
                    "active_control_file": "",
                    "active_control_seq": -1,
                    "active_control_status": "none",
                },
                "active_round": {"state": ""},
            }
            time_values = iter([0.0, 0.0, 1.0])

            with mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")), \
                 mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")), \
                 mock.patch.object(
                     pipeline_runtime_gate,
                     "_wait_for_runtime_readiness",
                     return_value=(True, ready_status, 3.5),
                 ) as ready_wait, \
                 mock.patch.object(pipeline_runtime_gate, "_read_status", return_value=ready_status), \
                 mock.patch.object(
                     pipeline_runtime_gate,
                     "_analyze_run_artifacts",
                     return_value={"dispatch_count": 0, "duplicate_dispatch_count": 0, "orphan_session": False},
                 ), \
                 mock.patch.object(pipeline_runtime_gate, "parse_control_slots", return_value={"active": {}}), \
                 mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None), \
                 mock.patch.object(pipeline_runtime_gate.time, "time", side_effect=lambda: next(time_values)):
                ok, summary = pipeline_runtime_gate.run_soak(
                    root,
                    mode="experimental",
                    session="aip-test",
                    duration_sec=0.5,
                    sample_interval_sec=0.5,
                    ready_timeout_sec=45.0,
                )

        self.assertTrue(ok)
        self.assertTrue(summary["ready_ok"])
        self.assertEqual(summary["ready_wait_sec"], 3.5)
        self.assertEqual(summary["state_counts"], {"RUNNING": 1})
        ready_wait.assert_called_once_with(root, timeout_sec=45.0)

    def test_run_soak_fails_when_ready_barrier_times_out_with_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readiness_status = {
                "runtime_state": "STARTING",
                "watcher": {"alive": False, "pid": None},
                "lanes": [
                    {
                        "name": "Claude",
                        "state": "BOOTING",
                        "attachable": True,
                        "pid": 111,
                        "note": "",
                        "last_event_at": "",
                        "last_heartbeat_at": "",
                    }
                ],
                "control": {"active_control_status": "implement"},
                "active_round": {"state": "VERIFY_PENDING"},
            }

            with mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")), \
                 mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")), \
                 mock.patch.object(
                     pipeline_runtime_gate,
                     "_wait_for_runtime_readiness",
                     return_value=(False, readiness_status, 45.0),
                 ):
                ok, summary = pipeline_runtime_gate.run_soak(
                    root,
                    mode="experimental",
                    session="aip-test",
                    duration_sec=5.0,
                    sample_interval_sec=1.0,
                    ready_timeout_sec=45.0,
                )

        self.assertFalse(ok)
        self.assertFalse(summary["ready_ok"])
        self.assertEqual(summary["ready_wait_sec"], 45.0)
        self.assertEqual(summary["samples"], 0)
        self.assertEqual(
            summary["readiness_snapshot"],
            pipeline_runtime_gate._status_readiness_snapshot(readiness_status),
        )

    def test_run_soak_fails_when_degraded_is_seen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            time_values = iter([0.0, 0.0, 1.0])

            with mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")), \
                 mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")), \
                 mock.patch.object(
                     pipeline_runtime_gate,
                     "_wait_for_runtime_readiness",
                     return_value=(
                         True,
                         {
                             "runtime_state": "RUNNING",
                             "watcher": {"alive": True, "pid": 1},
                             "lanes": [{"state": "READY", "attachable": True}],
                         },
                         0.5,
                     ),
                 ), \
                 mock.patch.object(
                     pipeline_runtime_gate,
                     "_read_status",
                     return_value={"runtime_state": "DEGRADED", "degraded_reason": "receipt_manifest:job-1:missing_manifest_path"},
                 ), \
                 mock.patch.object(
                     pipeline_runtime_gate,
                     "_analyze_run_artifacts",
                     return_value={"dispatch_count": 0, "duplicate_dispatch_count": 0, "orphan_session": False},
                 ), \
                 mock.patch.object(pipeline_runtime_gate, "parse_control_slots", return_value={"active": {}}), \
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
                     "_wait_for_runtime_readiness",
                     return_value=(
                         True,
                         {
                             "runtime_state": "RUNNING",
                             "watcher": {"alive": True, "pid": 1},
                             "lanes": [{"state": "READY", "attachable": True}],
                         },
                         0.5,
                     ),
                 ), \
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
                 mock.patch.object(
                     pipeline_runtime_gate,
                     "_analyze_run_artifacts",
                     return_value={"dispatch_count": 0, "duplicate_dispatch_count": 0, "orphan_session": False},
                 ), \
                 mock.patch.object(pipeline_runtime_gate, "parse_control_slots", return_value={"active": {}}), \
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

    def test_run_operator_classification_gate_fails_after_supervisor_writes_malformed_operator_request_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_runtime_gate._write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 190\n\nReason:\n- slice_ambiguity\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["autonomy"]["classification_source"], "metadata_missing_fallback")

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
