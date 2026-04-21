from __future__ import annotations

import json
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

            profile_path = workspace / ".pipeline" / "config" / "agent_profile.json"
            self.assertTrue(profile_path.exists())
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(
                profile["role_bindings"],
                {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
            )
            self.assertTrue(any((workspace / "work").rglob("*.md")))
            self.assertIn("PIPELINE_RUNTIME_LANE_COMMAND_CODEX", env)
            self.assertEqual(env["PIPELINE_RUNTIME_DISABLE_TOKEN_COLLECTOR"], "1")

    def test_prepare_synthetic_workspace_accepts_legacy_role_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace, _env = pipeline_runtime_gate.prepare_synthetic_workspace(
                Path(tmp),
                role_bindings={"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
            )

            profile_path = workspace / ".pipeline" / "config" / "agent_profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))

            self.assertEqual(
                profile["role_bindings"],
                {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
            )

    def test_write_active_profile_accepts_legacy_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_runtime_gate._write_active_profile(
                root,
                role_bindings={"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
            )

            profile = json.loads(
                (root / ".pipeline" / "config" / "agent_profile.json").read_text(encoding="utf-8")
            )

        self.assertEqual(
            profile["role_bindings"],
            {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
        )

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

    def test_probe_receipt_manifest_mismatch_degraded_precedence_catches_regression(self) -> None:
        ok, detail, data = pipeline_runtime_gate._probe_receipt_manifest_mismatch_degraded_precedence()
        self.assertTrue(ok, detail)
        self.assertIn("runtime_state=DEGRADED", detail)
        self.assertIn("receipt_manifest:job-fault-manifest", detail)
        self.assertEqual(data.get("runtime_state"), "DEGRADED")
        self.assertEqual(
            data.get("expected_reason_prefix"), "receipt_manifest:job-fault-manifest"
        )
        self.assertTrue(
            str(data.get("matched_reason") or "").startswith("receipt_manifest:job-fault-manifest"),
            data,
        )
        self.assertTrue(
            any(
                reason.startswith("receipt_manifest:job-fault-manifest")
                for reason in (data.get("degraded_reasons") or [])
            ),
            data,
        )

    def test_probe_active_lane_auth_failure_degraded_precedence_catches_regression(self) -> None:
        ok, detail, data = pipeline_runtime_gate._probe_active_lane_auth_failure_degraded_precedence()
        self.assertTrue(ok, detail)
        self.assertIn("runtime_state=DEGRADED", detail)
        self.assertIn("claude_auth_login_required", detail)
        self.assertEqual(data.get("runtime_state"), "DEGRADED")
        self.assertEqual(data.get("expected_reason"), "claude_auth_login_required")
        self.assertEqual(data.get("matched_reason"), "claude_auth_login_required")
        self.assertIn("claude_auth_login_required", data.get("degraded_reasons") or [])

    def test_probe_receipt_manifest_mismatch_flags_regression_when_supervisor_hides_degrade(self) -> None:
        """If `_write_status` regresses and returns STOPPED for the seeded mismatch,
        the fault-check probe must flag ok=False so the gate does not silently pass
        and the structured payload must record the missing match explicitly."""
        with mock.patch.object(
            pipeline_runtime_gate.RuntimeSupervisor,
            "_write_status",
            autospec=True,
            return_value={"runtime_state": "STOPPED", "degraded_reasons": []},
        ):
            ok, detail, data = pipeline_runtime_gate._probe_receipt_manifest_mismatch_degraded_precedence()
        self.assertFalse(ok)
        self.assertIn("runtime_state=STOPPED", detail)
        self.assertEqual(data.get("runtime_state"), "STOPPED")
        self.assertEqual(data.get("matched_reason"), "")
        self.assertEqual(
            data.get("expected_reason_prefix"), "receipt_manifest:job-fault-manifest"
        )
        self.assertEqual(data.get("degraded_reasons"), [])

    def test_probe_active_lane_auth_failure_flags_regression_when_supervisor_hides_degrade(self) -> None:
        """If `_write_status` regresses and returns STARTING for the seeded auth
        failure, the fault-check probe must flag ok=False and the structured
        payload must record the missing match explicitly."""
        with mock.patch.object(
            pipeline_runtime_gate.RuntimeSupervisor,
            "_write_status",
            autospec=True,
            return_value={"runtime_state": "STARTING", "degraded_reasons": []},
        ):
            ok, detail, data = pipeline_runtime_gate._probe_active_lane_auth_failure_degraded_precedence()
        self.assertFalse(ok)
        self.assertIn("runtime_state=STARTING", detail)
        self.assertEqual(data.get("runtime_state"), "STARTING")
        self.assertEqual(data.get("matched_reason"), "")
        self.assertEqual(data.get("expected_reason"), "claude_auth_login_required")
        self.assertEqual(data.get("degraded_reasons"), [])

    def test_run_fault_check_synthetic_probe_entries_carry_structured_data_payloads(self) -> None:
        """The top-of-``run_fault_check`` synthetic probe entries must attach their
        structured payload as ``data`` alongside the human-readable ``detail``
        string so automation can read the match evidence directly. The markdown
        report must also reflect the human-readable proof."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_receipt_manifest_mismatch_degraded_precedence",
                    return_value=(
                        True,
                        "runtime_state=DEGRADED, reasons=[\"receipt_manifest:job-fault-manifest:artifact_hash_mismatch\"]",
                        {
                            "runtime_state": "DEGRADED",
                            "degraded_reasons": ["receipt_manifest:job-fault-manifest:artifact_hash_mismatch"],
                            "expected_reason_prefix": "receipt_manifest:job-fault-manifest",
                            "matched_reason": "receipt_manifest:job-fault-manifest:artifact_hash_mismatch",
                        },
                    ),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_active_lane_auth_failure_degraded_precedence",
                    return_value=(
                        True,
                        "runtime_state=DEGRADED, reasons=[\"claude_auth_login_required\"]",
                        {
                            "runtime_state": "DEGRADED",
                            "degraded_reasons": ["claude_auth_login_required"],
                            "expected_reason": "claude_auth_login_required",
                            "matched_reason": "claude_auth_login_required",
                        },
                    ),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_start_runtime",
                    return_value=(False, "synthetic: start skipped"),
                ),
                mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")),
            ):
                ok, checks = pipeline_runtime_gate.run_fault_check(
                    root,
                    mode="experimental",
                    session="aip-test",
                )
        receipt_entry = next(
            item for item in checks if item.get("name") == "receipt manifest mismatch degraded precedence"
        )
        auth_entry = next(
            item for item in checks if item.get("name") == "active lane auth failure degraded precedence"
        )
        self.assertTrue(receipt_entry.get("ok"))
        self.assertTrue(auth_entry.get("ok"))
        receipt_data = receipt_entry.get("data") or {}
        auth_data = auth_entry.get("data") or {}
        self.assertEqual(receipt_data.get("runtime_state"), "DEGRADED")
        self.assertEqual(
            receipt_data.get("matched_reason"),
            "receipt_manifest:job-fault-manifest:artifact_hash_mismatch",
        )
        self.assertEqual(
            receipt_data.get("expected_reason_prefix"),
            "receipt_manifest:job-fault-manifest",
        )
        self.assertEqual(auth_data.get("runtime_state"), "DEGRADED")
        self.assertEqual(auth_data.get("matched_reason"), "claude_auth_login_required")
        self.assertEqual(auth_data.get("expected_reason"), "claude_auth_login_required")
        report = pipeline_runtime_gate._markdown_report(
            title="Pipeline Runtime fault check",
            summary=["project=/tmp/fake"],
            checks=checks,
        )
        self.assertIn("`PASS` receipt manifest mismatch degraded precedence", report)
        self.assertIn("`PASS` active lane auth failure degraded precedence", report)
        self.assertIn("receipt_manifest:job-fault-manifest:artifact_hash_mismatch", report)
        self.assertIn("claude_auth_login_required", report)
        # The probe entries must be safe to run even when later live steps fail,
        # so the aggregate ``ok`` still matches the live-start failure here.
        self.assertFalse(ok)

    def test_run_fault_check_session_loss_requires_session_missing_as_representative_reason(self) -> None:
        """The live `session loss degraded` step must assert that the root-cause
        `degraded_reason` stays on `session_missing` even when per-lane
        `*_recovery_failed` entries coexist inside `degraded_reasons`."""
        representative_ok_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": [
                "session_missing",
                "claude_recovery_failed",
                "codex_recovery_failed",
                "gemini_recovery_failed",
            ],
        }
        representative_wrong_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "claude_recovery_failed",
            "degraded_reasons": [
                "claude_recovery_failed",
                "codex_recovery_failed",
                "gemini_recovery_failed",
                "session_missing",
            ],
        }
        ready_status = {
            "runtime_state": "RUNNING",
            "watcher": {"alive": True, "pid": 1},
            "lanes": [{"name": "Claude", "state": "READY", "attachable": True, "pid": 1234}],
            "control": {"active_control_status": "none"},
            "active_round": {"state": ""},
        }
        def _wait_until_one_shot(predicate, timeout_sec: float = 0.0):
            try:
                return predicate()
            except Exception:
                return None

        for status_payload, expected_ok in (
            (representative_ok_status, True),
            (representative_wrong_status, False),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with (
                    mock.patch.object(
                        pipeline_runtime_gate,
                        "_probe_receipt_manifest_mismatch_degraded_precedence",
                        return_value=(True, "probe ok", {}),
                    ),
                    mock.patch.object(
                        pipeline_runtime_gate,
                        "_probe_active_lane_auth_failure_degraded_precedence",
                        return_value=(True, "probe ok", {}),
                    ),
                    mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")),
                    mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")),
                    mock.patch.object(
                        pipeline_runtime_gate,
                        "_wait_for_runtime_readiness",
                        return_value=(True, ready_status, 0.5),
                    ),
                    mock.patch.object(pipeline_runtime_gate.TmuxAdapter, "kill_session", return_value=None),
                    mock.patch.object(pipeline_runtime_gate, "_read_status", return_value=status_payload),
                    mock.patch.object(pipeline_runtime_gate, "_wait_until", side_effect=_wait_until_one_shot),
                    mock.patch.object(pipeline_runtime_gate, "_pick_fault_lane", return_value=("Claude", 0)),
                    mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None),
                ):
                    ok, checks = pipeline_runtime_gate.run_fault_check(
                        root,
                        mode="experimental",
                        session="aip-test",
                    )
            session_loss_entry = next(
                item for item in checks if item.get("name") == "session loss degraded"
            )
            self.assertEqual(bool(session_loss_entry.get("ok")), expected_ok, session_loss_entry)
            if expected_ok:
                self.assertIn("reason=session_missing", session_loss_entry.get("detail") or "")
                self.assertIn("claude_recovery_failed", session_loss_entry.get("detail") or "")
                self.assertIn(
                    "secondary_recovery_failures=[\"claude_recovery_failed\", \"codex_recovery_failed\", \"gemini_recovery_failed\"]",
                    session_loss_entry.get("detail") or "",
                )
            else:
                self.assertIn("reason=claude_recovery_failed", session_loss_entry.get("detail") or "")
            # Regardless of representative-ordering assertion outcome, the run must not
            # be accidentally green when the representative reason is wrong.
            if not expected_ok:
                self.assertFalse(ok)

    def test_session_loss_check_exposes_secondary_recovery_failures_as_structured_data(self) -> None:
        """``session loss degraded`` must carry a structured ``data`` payload whose
        ``secondary_recovery_failures`` list is populated when per-lane
        ``*_recovery_failed`` entries coexist with ``session_missing``. Automation
        should be able to read the evidence without scraping the detail string."""
        representative_ok_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": [
                "session_missing",
                "claude_recovery_failed",
                "codex_recovery_failed",
                "gemini_recovery_failed",
            ],
        }
        ready_status = {
            "runtime_state": "RUNNING",
            "watcher": {"alive": True, "pid": 1},
            "lanes": [{"name": "Claude", "state": "READY", "attachable": True, "pid": 1234}],
            "control": {"active_control_status": "none"},
            "active_round": {"state": ""},
        }

        def _wait_until_one_shot(predicate, timeout_sec: float = 0.0):
            try:
                return predicate()
            except Exception:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_receipt_manifest_mismatch_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_active_lane_auth_failure_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")),
                mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_wait_for_runtime_readiness",
                    return_value=(True, ready_status, 0.5),
                ),
                mock.patch.object(pipeline_runtime_gate.TmuxAdapter, "kill_session", return_value=None),
                mock.patch.object(pipeline_runtime_gate, "_read_status", return_value=representative_ok_status),
                mock.patch.object(pipeline_runtime_gate, "_wait_until", side_effect=_wait_until_one_shot),
                mock.patch.object(pipeline_runtime_gate, "_pick_fault_lane", return_value=("Claude", 0)),
                mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None),
            ):
                ok, checks = pipeline_runtime_gate.run_fault_check(
                    root,
                    mode="experimental",
                    session="aip-test",
                )

        session_loss_entry = next(item for item in checks if item.get("name") == "session loss degraded")
        self.assertTrue(session_loss_entry.get("ok"))
        data = session_loss_entry.get("data") or {}
        self.assertEqual(data.get("representative_reason"), "session_missing")
        self.assertEqual(data.get("runtime_state"), "DEGRADED")
        self.assertEqual(
            data.get("secondary_recovery_failures"),
            ["claude_recovery_failed", "codex_recovery_failed", "gemini_recovery_failed"],
        )
        self.assertEqual(
            data.get("degraded_reasons"),
            [
                "session_missing",
                "claude_recovery_failed",
                "codex_recovery_failed",
                "gemini_recovery_failed",
            ],
        )
        # Markdown report remains readable and is consistent with the structured payload.
        report = pipeline_runtime_gate._markdown_report(
            title="Pipeline Runtime fault check",
            summary=["project=/tmp/fake"],
            checks=checks,
        )
        self.assertIn("`PASS` session loss degraded", report)
        self.assertIn("reason=session_missing", report)
        self.assertIn("secondary_recovery_failures=[\"claude_recovery_failed\", \"codex_recovery_failed\", \"gemini_recovery_failed\"]", report)

    def test_session_loss_check_reports_empty_secondary_recovery_failures_when_none_present(self) -> None:
        """When only ``session_missing`` is reported, the structured
        ``secondary_recovery_failures`` field must still be present as an empty
        list so automation can rely on a stable schema."""
        only_session_missing_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": ["session_missing"],
        }
        ready_status = {
            "runtime_state": "RUNNING",
            "watcher": {"alive": True, "pid": 1},
            "lanes": [{"name": "Claude", "state": "READY", "attachable": True, "pid": 1234}],
            "control": {"active_control_status": "none"},
            "active_round": {"state": ""},
        }

        def _wait_until_one_shot(predicate, timeout_sec: float = 0.0):
            try:
                return predicate()
            except Exception:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_receipt_manifest_mismatch_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_active_lane_auth_failure_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")),
                mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_wait_for_runtime_readiness",
                    return_value=(True, ready_status, 0.5),
                ),
                mock.patch.object(pipeline_runtime_gate.TmuxAdapter, "kill_session", return_value=None),
                mock.patch.object(pipeline_runtime_gate, "_read_status", return_value=only_session_missing_status),
                mock.patch.object(pipeline_runtime_gate, "_wait_until", side_effect=_wait_until_one_shot),
                mock.patch.object(pipeline_runtime_gate, "_pick_fault_lane", return_value=("Claude", 0)),
                mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None),
            ):
                ok, checks = pipeline_runtime_gate.run_fault_check(
                    root,
                    mode="experimental",
                    session="aip-test",
                )

        session_loss_entry = next(item for item in checks if item.get("name") == "session loss degraded")
        self.assertTrue(session_loss_entry.get("ok"))
        data = session_loss_entry.get("data") or {}
        self.assertEqual(data.get("representative_reason"), "session_missing")
        self.assertIn("secondary_recovery_failures", data)
        self.assertEqual(data.get("secondary_recovery_failures"), [])

    def _run_session_loss_with_events(
        self,
        degraded_status: dict,
        events: list[dict],
    ) -> list[dict]:
        ready_status = {
            "runtime_state": "RUNNING",
            "watcher": {"alive": True, "pid": 1},
            "lanes": [{"name": "Claude", "state": "READY", "attachable": True, "pid": 1234}],
            "control": {"active_control_status": "none"},
            "active_round": {"state": ""},
        }

        def _wait_until_one_shot(predicate, timeout_sec: float = 0.0):
            try:
                return predicate()
            except Exception:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_receipt_manifest_mismatch_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_active_lane_auth_failure_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")),
                mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_wait_for_runtime_readiness",
                    return_value=(True, ready_status, 0.5),
                ),
                mock.patch.object(pipeline_runtime_gate.TmuxAdapter, "kill_session", return_value=None),
                mock.patch.object(pipeline_runtime_gate, "_read_status", return_value=degraded_status),
                mock.patch.object(pipeline_runtime_gate, "_wait_until", side_effect=_wait_until_one_shot),
                mock.patch.object(pipeline_runtime_gate, "_pick_fault_lane", return_value=("Claude", 0)),
                mock.patch.object(pipeline_runtime_gate, "_read_events", return_value=events),
                mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None),
            ):
                _, checks = pipeline_runtime_gate.run_fault_check(
                    root,
                    mode="experimental",
                    session="aip-test",
                )
        return checks

    def test_session_loss_check_requires_bounded_session_recovery_completed_evidence(self) -> None:
        """When the degraded snapshot shows ``session_missing`` alongside a
        BROKEN lane, the gate must wait for a terminal
        ``session_recovery_completed`` event and record its structured payload
        inside the ``session loss degraded`` check."""
        degraded_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": ["session_missing"],
            "lanes": [
                {"name": "Claude", "state": "BROKEN", "attachable": False, "pid": 0},
                {"name": "Codex", "state": "BROKEN", "attachable": False, "pid": 0},
                {"name": "Gemini", "state": "BROKEN", "attachable": False, "pid": 0},
            ],
        }
        recovery_event = {
            "seq": 11,
            "ts": "2026-04-19T02:00:00Z",
            "run_id": "run-99",
            "event_type": "session_recovery_completed",
            "source": "supervisor",
            "payload": {"attempt": 1, "result": "recreated"},
        }
        checks = self._run_session_loss_with_events(degraded_status, [recovery_event])
        session_loss_entry = next(item for item in checks if item.get("name") == "session loss degraded")
        self.assertTrue(session_loss_entry.get("ok"))
        data = session_loss_entry.get("data") or {}
        self.assertEqual(data.get("representative_reason"), "session_missing")
        recovery_data = data.get("session_recovery") or {}
        self.assertTrue(recovery_data.get("recovery_expected"))
        self.assertEqual(recovery_data.get("broken_lane_names"), ["Claude", "Codex", "Gemini"])
        self.assertTrue(recovery_data.get("event_observed"))
        self.assertEqual(recovery_data.get("event_type"), "session_recovery_completed")
        self.assertEqual(recovery_data.get("attempt"), 1)
        self.assertEqual(recovery_data.get("result"), "recreated")
        self.assertEqual(recovery_data.get("error"), "")
        self.assertEqual(recovery_data.get("event"), recovery_event)
        self.assertIn("session_recovery=", session_loss_entry.get("detail") or "")
        self.assertIn("session_recovery_completed", session_loss_entry.get("detail") or "")

    def test_session_loss_check_accepts_bounded_session_recovery_failed_evidence(self) -> None:
        """A terminal ``session_recovery_failed`` event must count as bounded
        recovery evidence so the gate does not spuriously fail when the
        supervisor attempted but could not recreate the tmux session."""
        degraded_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": ["session_missing"],
            "lanes": [
                {"name": "Claude", "state": "BROKEN", "attachable": False, "pid": 0},
            ],
        }
        recovery_event = {
            "seq": 12,
            "ts": "2026-04-19T02:01:00Z",
            "run_id": "run-99",
            "event_type": "session_recovery_failed",
            "source": "supervisor",
            "payload": {"attempt": 1, "error": "RuntimeError: tmux split Codex pane failed: no space"},
        }
        checks = self._run_session_loss_with_events(degraded_status, [recovery_event])
        session_loss_entry = next(item for item in checks if item.get("name") == "session loss degraded")
        self.assertTrue(session_loss_entry.get("ok"))
        data = session_loss_entry.get("data") or {}
        recovery_data = data.get("session_recovery") or {}
        self.assertTrue(recovery_data.get("recovery_expected"))
        self.assertEqual(recovery_data.get("broken_lane_names"), ["Claude"])
        self.assertTrue(recovery_data.get("event_observed"))
        self.assertEqual(recovery_data.get("event_type"), "session_recovery_failed")
        self.assertEqual(recovery_data.get("attempt"), 1)
        self.assertEqual(recovery_data.get("result"), "")
        self.assertIn("tmux split Codex pane failed", recovery_data.get("error") or "")
        self.assertEqual(recovery_data.get("event"), recovery_event)

    def test_session_loss_check_fails_when_recovery_expected_but_no_event_observed(self) -> None:
        """If the supervisor contract expected bounded session recovery
        (``session_missing`` + BROKEN lane) but neither
        ``session_recovery_completed`` nor ``session_recovery_failed`` is ever
        emitted, the gate must fail instead of silently passing on the
        representative reason alone."""
        degraded_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": ["session_missing"],
            "lanes": [
                {"name": "Claude", "state": "BROKEN", "attachable": False, "pid": 0},
            ],
        }
        checks = self._run_session_loss_with_events(degraded_status, [])
        session_loss_entry = next(item for item in checks if item.get("name") == "session loss degraded")
        self.assertFalse(session_loss_entry.get("ok"))
        data = session_loss_entry.get("data") or {}
        self.assertEqual(data.get("representative_reason"), "session_missing")
        recovery_data = data.get("session_recovery") or {}
        self.assertTrue(recovery_data.get("recovery_expected"))
        self.assertFalse(recovery_data.get("event_observed"))
        self.assertEqual(recovery_data.get("event_type"), "")
        self.assertEqual(recovery_data.get("attempt"), 0)
        self.assertEqual(recovery_data.get("event"), {})

    def test_session_loss_check_does_not_overclaim_recovery_when_no_broken_lane(self) -> None:
        """When the degraded snapshot shows ``session_missing`` but no lane is
        BROKEN, the supervisor contract does not trigger bounded session
        recovery. The gate must reflect that with a stable structured payload
        (``recovery_expected=False``, no required event) and must still pass."""
        degraded_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": ["session_missing"],
            "lanes": [
                {"name": "Claude", "state": "READY", "attachable": True, "pid": 1234},
            ],
        }
        # Even if an unrelated event stream exists, the gate must not require
        # terminal session-recovery evidence when recovery was not expected.
        checks = self._run_session_loss_with_events(degraded_status, [])
        session_loss_entry = next(item for item in checks if item.get("name") == "session loss degraded")
        self.assertTrue(session_loss_entry.get("ok"))
        data = session_loss_entry.get("data") or {}
        recovery_data = data.get("session_recovery") or {}
        self.assertFalse(recovery_data.get("recovery_expected"))
        self.assertEqual(recovery_data.get("broken_lane_names"), [])
        self.assertFalse(recovery_data.get("event_observed"))
        self.assertEqual(recovery_data.get("event_type"), "")
        self.assertEqual(recovery_data.get("event"), {})

    def test_live_recovery_proof_checks_expose_structured_data_for_success_path(self) -> None:
        """``recoverable lane pid observed`` and ``lane recovery`` must carry
        structured ``data`` payloads alongside the human-readable detail so
        automation can read lane pid / recovery event fields without scraping."""
        representative_ok_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": [
                "session_missing",
                "claude_recovery_failed",
            ],
        }
        ready_status = {
            "runtime_state": "RUNNING",
            "watcher": {"alive": True, "pid": 1},
            "lanes": [{"name": "Claude", "state": "READY", "attachable": True, "pid": 1234}],
            "control": {"active_control_status": "none"},
            "active_round": {"state": ""},
        }
        recovery_event = {
            "seq": 8,
            "ts": "2026-04-18T09:30:00Z",
            "run_id": "run-42",
            "event_type": "recovery_completed",
            "source": "supervisor",
            "payload": {"lane": "Claude", "attempt": 1, "result": "restarted"},
        }

        def _wait_until_one_shot(predicate, timeout_sec: float = 0.0):
            try:
                return predicate()
            except Exception:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_receipt_manifest_mismatch_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_active_lane_auth_failure_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")),
                mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_wait_for_runtime_readiness",
                    return_value=(True, ready_status, 0.5),
                ),
                mock.patch.object(pipeline_runtime_gate.TmuxAdapter, "kill_session", return_value=None),
                mock.patch.object(pipeline_runtime_gate, "_read_status", return_value=representative_ok_status),
                mock.patch.object(pipeline_runtime_gate, "_wait_until", side_effect=_wait_until_one_shot),
                mock.patch.object(pipeline_runtime_gate, "_pick_fault_lane", return_value=("Claude", 9876)),
                mock.patch.object(pipeline_runtime_gate, "_kill_pid", return_value=None),
                mock.patch.object(pipeline_runtime_gate, "_read_events", return_value=[recovery_event]),
                mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None),
            ):
                ok, checks = pipeline_runtime_gate.run_fault_check(
                    root,
                    mode="experimental",
                    session="aip-test",
                )

        lane_pid_entry = next(item for item in checks if item.get("name") == "recoverable lane pid observed")
        self.assertTrue(lane_pid_entry.get("ok"))
        lane_pid_data = lane_pid_entry.get("data") or {}
        self.assertEqual(lane_pid_data.get("lane"), "Claude")
        self.assertEqual(lane_pid_data.get("pid"), 9876)
        self.assertTrue(lane_pid_data.get("pid_available"))
        self.assertIn("lane=Claude", lane_pid_entry.get("detail") or "")
        self.assertIn("pid=9876", lane_pid_entry.get("detail") or "")

        recovery_entry = next(item for item in checks if item.get("name") == "lane recovery")
        self.assertTrue(recovery_entry.get("ok"))
        recovery_data = recovery_entry.get("data") or {}
        self.assertTrue(recovery_data.get("event_observed"))
        self.assertEqual(recovery_data.get("event_type"), "recovery_completed")
        self.assertEqual(recovery_data.get("lane"), "Claude")
        self.assertEqual(recovery_data.get("attempt"), 1)
        self.assertEqual(recovery_data.get("result"), "restarted")
        self.assertEqual(recovery_data.get("event"), recovery_event)
        # Markdown report remains readable and is derived from the same evidence.
        report = pipeline_runtime_gate._markdown_report(
            title="Pipeline Runtime fault check",
            summary=["project=/tmp/fake"],
            checks=checks,
        )
        self.assertIn("`PASS` recoverable lane pid observed", report)
        self.assertIn("`PASS` lane recovery", report)
        self.assertIn("recovery_completed", report)
        # ``session loss degraded`` structured payload must not regress.
        session_loss_entry = next(item for item in checks if item.get("name") == "session loss degraded")
        self.assertEqual((session_loss_entry.get("data") or {}).get("representative_reason"), "session_missing")

    def test_live_recovery_proof_checks_expose_structured_empty_payload_when_lane_pid_unavailable(self) -> None:
        """If ``_pick_fault_lane`` returns no live pid, ``recoverable lane pid
        observed`` must still carry a stable structured ``data`` payload with
        ``pid_available=False``, and ``lane recovery`` must surface an empty
        recovery event payload with an explicit ``reason`` string."""
        representative_ok_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": ["session_missing"],
        }
        ready_status = {
            "runtime_state": "RUNNING",
            "watcher": {"alive": True, "pid": 1},
            "lanes": [{"name": "Claude", "state": "READY", "attachable": True, "pid": 1234}],
            "control": {"active_control_status": "none"},
            "active_round": {"state": ""},
        }

        def _wait_until_one_shot(predicate, timeout_sec: float = 0.0):
            try:
                return predicate()
            except Exception:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_receipt_manifest_mismatch_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_active_lane_auth_failure_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(pipeline_runtime_gate, "_start_runtime", return_value=(True, "started")),
                mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_wait_for_runtime_readiness",
                    return_value=(True, ready_status, 0.5),
                ),
                mock.patch.object(pipeline_runtime_gate.TmuxAdapter, "kill_session", return_value=None),
                mock.patch.object(pipeline_runtime_gate, "_read_status", return_value=representative_ok_status),
                mock.patch.object(pipeline_runtime_gate, "_wait_until", side_effect=_wait_until_one_shot),
                mock.patch.object(pipeline_runtime_gate, "_pick_fault_lane", return_value=("Claude", 0)),
                mock.patch.object(pipeline_runtime_gate, "_read_events", return_value=[]),
                mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None),
            ):
                ok, checks = pipeline_runtime_gate.run_fault_check(
                    root,
                    mode="experimental",
                    session="aip-test",
                )

        lane_pid_entry = next(item for item in checks if item.get("name") == "recoverable lane pid observed")
        self.assertFalse(lane_pid_entry.get("ok"))
        lane_pid_data = lane_pid_entry.get("data") or {}
        self.assertFalse(lane_pid_data.get("pid_available"))
        self.assertEqual(lane_pid_data.get("pid"), 0)
        self.assertEqual(lane_pid_data.get("lane"), "Claude")

        recovery_entry = next(item for item in checks if item.get("name") == "lane recovery")
        self.assertFalse(recovery_entry.get("ok"))
        recovery_data = recovery_entry.get("data") or {}
        self.assertFalse(recovery_data.get("event_observed"))
        self.assertEqual(recovery_data.get("event"), {})
        self.assertEqual(recovery_data.get("reason"), "lane_pid_unavailable_before_fault_injection")
        self.assertFalse(ok)

    def test_lifecycle_checks_expose_structured_data_on_green_path(self) -> None:
        """The four lifecycle lifecycle check entries (``runtime start``,
        ``status surface ready``, ``runtime stop after session loss``,
        ``runtime restart``) must each carry a stable structured ``data`` payload
        alongside the human-readable ``detail`` string so automation can read the
        lifecycle evidence without scraping."""
        representative_ok_status = {
            "runtime_state": "DEGRADED",
            "degraded_reason": "session_missing",
            "degraded_reasons": ["session_missing"],
        }
        ready_status = {
            "runtime_state": "RUNNING",
            "watcher": {"alive": True, "pid": 111},
            "lanes": [
                {
                    "name": "Claude",
                    "state": "READY",
                    "attachable": True,
                    "pid": 1234,
                    "note": "prompt_visible",
                    "last_event_at": "2026-04-18T09:00:00Z",
                    "last_heartbeat_at": "2026-04-18T09:00:00Z",
                },
                {
                    "name": "Codex",
                    "state": "WORKING",
                    "attachable": True,
                    "pid": 5678,
                    "note": "",
                    "last_event_at": "",
                    "last_heartbeat_at": "",
                },
            ],
            "control": {"active_control_status": "none"},
            "active_round": {"state": ""},
        }
        recovery_event = {
            "seq": 1,
            "ts": "2026-04-18T09:00:05Z",
            "run_id": "run-1",
            "event_type": "recovery_completed",
            "source": "supervisor",
            "payload": {"lane": "Claude", "attempt": 1, "result": "restarted"},
        }

        def _wait_until_one_shot(predicate, timeout_sec: float = 0.0):
            try:
                return predicate()
            except Exception:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_receipt_manifest_mismatch_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_active_lane_auth_failure_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_start_runtime",
                    return_value=(True, "started"),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_stop_runtime",
                    return_value=(True, "stopped"),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_wait_for_runtime_readiness",
                    return_value=(True, ready_status, 1.5),
                ),
                mock.patch.object(pipeline_runtime_gate.TmuxAdapter, "kill_session", return_value=None),
                mock.patch.object(pipeline_runtime_gate, "_read_status", return_value=representative_ok_status),
                mock.patch.object(pipeline_runtime_gate, "_wait_until", side_effect=_wait_until_one_shot),
                mock.patch.object(pipeline_runtime_gate, "_pick_fault_lane", return_value=("Claude", 9999)),
                mock.patch.object(pipeline_runtime_gate, "_kill_pid", return_value=None),
                mock.patch.object(pipeline_runtime_gate, "_read_events", return_value=[recovery_event]),
                mock.patch.object(pipeline_runtime_gate.time, "sleep", return_value=None),
            ):
                ok, checks = pipeline_runtime_gate.run_fault_check(
                    root,
                    mode="experimental",
                    session="aip-test",
                )

        by_name = {str(item.get("name") or ""): item for item in checks}

        runtime_start = by_name["runtime start"]
        self.assertTrue(runtime_start.get("ok"))
        self.assertEqual(runtime_start.get("data"), {
            "action": "start",
            "succeeded": True,
            "result": "started",
        })

        status_ready = by_name["status surface ready"]
        self.assertTrue(status_ready.get("ok"))
        ready_data = status_ready.get("data") or {}
        self.assertTrue(ready_data.get("ready"))
        self.assertEqual(ready_data.get("wait_sec"), 1.5)
        self.assertEqual(ready_data.get("runtime_state"), "RUNNING")
        self.assertTrue(ready_data.get("watcher_alive"))
        self.assertEqual(ready_data.get("active_control_status"), "none")
        self.assertEqual(ready_data.get("ready_lane_names"), ["Claude", "Codex"])
        self.assertEqual(ready_data.get("ready_lane_count"), 2)
        self.assertEqual(
            ready_data.get("snapshot"),
            pipeline_runtime_gate._status_readiness_snapshot(ready_status),
        )

        stop_entry = by_name["runtime stop after session loss"]
        self.assertTrue(stop_entry.get("ok"))
        self.assertEqual(stop_entry.get("data"), {
            "action": "stop",
            "succeeded": True,
            "result": "stopped",
        })

        restart_entry = by_name["runtime restart"]
        self.assertTrue(restart_entry.get("ok"))
        self.assertEqual(restart_entry.get("data"), {
            "action": "restart",
            "succeeded": True,
            "result": "started",
        })

        # Previously-landed structured payloads must not regress.
        session_loss = by_name["session loss degraded"]
        session_loss_data = session_loss.get("data") or {}
        self.assertEqual(session_loss_data.get("representative_reason"), "session_missing")
        # Green-path degraded snapshot has no BROKEN lane, so the bounded
        # session-recovery contract is not expected to fire. The structured
        # ``session_recovery`` sub-payload must still be present with stable
        # empty defaults so automation can read the same schema on every run.
        recovery_payload = session_loss_data.get("session_recovery") or {}
        self.assertIn("session_recovery", session_loss_data)
        self.assertFalse(recovery_payload.get("recovery_expected"))
        self.assertEqual(recovery_payload.get("broken_lane_names"), [])
        self.assertFalse(recovery_payload.get("event_observed"))
        self.assertEqual(recovery_payload.get("event_type"), "")
        self.assertEqual(recovery_payload.get("attempt"), 0)
        self.assertEqual(recovery_payload.get("result"), "")
        self.assertEqual(recovery_payload.get("error"), "")
        self.assertEqual(recovery_payload.get("event"), {})
        lane_pid = by_name["recoverable lane pid observed"]
        self.assertTrue((lane_pid.get("data") or {}).get("pid_available"))
        lane_recovery = by_name["lane recovery"]
        self.assertTrue((lane_recovery.get("data") or {}).get("event_observed"))

        # Markdown report keeps the same human-readable evidence lines.
        report = pipeline_runtime_gate._markdown_report(
            title="Pipeline Runtime fault check",
            summary=["project=/tmp/fake"],
            checks=checks,
        )
        self.assertIn("`PASS` runtime start", report)
        self.assertIn("`PASS` status surface ready", report)
        self.assertIn("wait_sec=1.5", report)
        self.assertIn("`PASS` runtime stop after session loss", report)
        self.assertIn("`PASS` runtime restart", report)

    def test_lifecycle_runtime_start_failure_exposes_structured_data(self) -> None:
        """A failed ``runtime start`` must surface the structured lifecycle payload
        so automation can read ``succeeded=False`` and the raw result string without
        scraping the detail field."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_receipt_manifest_mismatch_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_probe_active_lane_auth_failure_degraded_precedence",
                    return_value=(True, "probe ok", {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_start_runtime",
                    return_value=(False, "failed: adapter error"),
                ),
                mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")),
            ):
                ok, checks = pipeline_runtime_gate.run_fault_check(
                    root,
                    mode="experimental",
                    session="aip-test",
                )
        self.assertFalse(ok)
        runtime_start = next(item for item in checks if item.get("name") == "runtime start")
        self.assertFalse(runtime_start.get("ok"))
        self.assertEqual(
            runtime_start.get("data"),
            {"action": "start", "succeeded": False, "result": "failed: adapter error"},
        )
        # Downstream lifecycle checks must not appear once runtime start failed.
        later_names = {"status surface ready", "runtime stop after session loss", "runtime restart"}
        observed_names = {str(item.get("name") or "") for item in checks}
        self.assertTrue(later_names.isdisjoint(observed_names))

    def test_fault_check_cli_writes_markdown_and_json_sidecar_with_structured_checks(self) -> None:
        """The ``fault-check`` CLI path must persist both the markdown report
        and a JSON sidecar at the matching ``.json`` path. The sidecar carries
        the same summary metadata plus ``checks`` entries that keep their
        structured ``data`` payloads for probes, lifecycle, and live recovery."""
        import json as _json

        sample_checks = [
            {
                "name": "receipt manifest mismatch degraded precedence",
                "ok": True,
                "detail": "runtime_state=DEGRADED, reasons=[\"receipt_manifest:job-fault-manifest:artifact_hash_mismatch\"]",
                "data": {
                    "runtime_state": "DEGRADED",
                    "degraded_reasons": ["receipt_manifest:job-fault-manifest:artifact_hash_mismatch"],
                    "expected_reason_prefix": "receipt_manifest:job-fault-manifest",
                    "matched_reason": "receipt_manifest:job-fault-manifest:artifact_hash_mismatch",
                },
            },
            {
                "name": "runtime start",
                "ok": True,
                "detail": "started",
                "data": {"action": "start", "succeeded": True, "result": "started"},
            },
            {
                "name": "status surface ready",
                "ok": True,
                "detail": "wait_sec=1.0, {}",
                "data": {
                    "wait_sec": 1.0,
                    "ready": True,
                    "runtime_state": "RUNNING",
                    "watcher_alive": True,
                    "active_control_status": "none",
                    "ready_lane_names": ["Claude"],
                    "ready_lane_count": 1,
                    "snapshot": {"runtime_state": "RUNNING", "watcher": {"alive": True, "pid": 1}, "lanes": []},
                },
            },
            {
                "name": "session loss degraded",
                "ok": True,
                "detail": (
                    "runtime_state=DEGRADED, reason=session_missing, "
                    "reasons=[\"session_missing\"], "
                    "secondary_recovery_failures=[], "
                    "session_recovery={\"recovery_expected\": true, \"event_observed\": true, \"event_type\": \"session_recovery_completed\", \"attempt\": 1, \"result\": \"recreated\", \"error\": \"\"}"
                ),
                "data": {
                    "runtime_state": "DEGRADED",
                    "representative_reason": "session_missing",
                    "degraded_reasons": ["session_missing"],
                    "secondary_recovery_failures": [],
                    "session_recovery": {
                        "recovery_expected": True,
                        "broken_lane_names": ["Claude"],
                        "event_observed": True,
                        "event_type": "session_recovery_completed",
                        "attempt": 1,
                        "result": "recreated",
                        "error": "",
                        "event": {
                            "event_type": "session_recovery_completed",
                            "payload": {"attempt": 1, "result": "recreated"},
                        },
                    },
                },
            },
            {
                "name": "lane recovery",
                "ok": True,
                "detail": '{"event_type": "recovery_completed"}',
                "data": {
                    "event_observed": True,
                    "event_type": "recovery_completed",
                    "lane": "Claude",
                    "attempt": 1,
                    "result": "restarted",
                    "event": {"event_type": "recovery_completed", "payload": {"lane": "Claude", "attempt": 1, "result": "restarted"}},
                },
            },
        ]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            synthetic_root = tmp_root / "synthetic"
            synthetic_root.mkdir()
            report_path = tmp_root / "projecth-runtime-fault-check.md"
            expected_json_path = tmp_root / "projecth-runtime-fault-check.json"

            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "prepare_synthetic_workspace",
                    return_value=(synthetic_root, {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "run_fault_check",
                    return_value=(True, sample_checks),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_finalize_synthetic_workspace",
                    return_value=(False, "background_delete_requested(pid=123)"),
                ),
            ):
                exit_code = pipeline_runtime_gate.main(
                    [
                        "--project-root",
                        str(tmp_root),
                        "fault-check",
                        "--workspace-root",
                        str(tmp_root),
                        "--report",
                        str(report_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(report_path.exists())
            self.assertTrue(expected_json_path.exists())

            report_text = report_path.read_text(encoding="utf-8")
            # Markdown report keeps its human-readable content.
            self.assertIn("`PASS` receipt manifest mismatch degraded precedence", report_text)
            self.assertIn("`PASS` runtime start", report_text)
            self.assertIn("`PASS` status surface ready", report_text)
            self.assertIn("`PASS` session loss degraded", report_text)
            self.assertIn("session_recovery=", report_text)
            self.assertIn("`PASS` lane recovery", report_text)

            payload = _json.loads(expected_json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("title"), "Pipeline Runtime fault check")
            self.assertTrue(payload.get("ok"))
            summary = payload.get("summary") or {}
            self.assertEqual(summary.get("session"), pipeline_runtime_gate._session_name_for(synthetic_root))
            self.assertEqual(summary.get("mode"), "experimental")
            self.assertEqual(summary.get("workspace_retained"), False)
            self.assertEqual(summary.get("workspace_cleanup"), "background_delete_requested(pid=123)")
            checks_payload = payload.get("checks") or []
            names = {str(item.get("name") or ""): item for item in checks_payload}
            # Probe, lifecycle, and live recovery entries must retain their ``data`` payloads.
            probe_entry = names["receipt manifest mismatch degraded precedence"]
            self.assertEqual(
                (probe_entry.get("data") or {}).get("matched_reason"),
                "receipt_manifest:job-fault-manifest:artifact_hash_mismatch",
            )
            start_entry = names["runtime start"]
            self.assertEqual(start_entry.get("data"), {"action": "start", "succeeded": True, "result": "started"})
            ready_entry = names["status surface ready"]
            self.assertEqual((ready_entry.get("data") or {}).get("ready_lane_names"), ["Claude"])
            session_loss_entry = names["session loss degraded"]
            session_loss_payload = session_loss_entry.get("data") or {}
            self.assertEqual(session_loss_payload.get("representative_reason"), "session_missing")
            session_loss_recovery = session_loss_payload.get("session_recovery") or {}
            self.assertTrue(session_loss_recovery.get("recovery_expected"))
            self.assertEqual(session_loss_recovery.get("broken_lane_names"), ["Claude"])
            self.assertTrue(session_loss_recovery.get("event_observed"))
            self.assertEqual(session_loss_recovery.get("event_type"), "session_recovery_completed")
            self.assertEqual(session_loss_recovery.get("attempt"), 1)
            self.assertEqual(session_loss_recovery.get("result"), "recreated")
            self.assertEqual(
                session_loss_recovery.get("event"),
                {
                    "event_type": "session_recovery_completed",
                    "payload": {"attempt": 1, "result": "recreated"},
                },
            )
            recovery_entry = names["lane recovery"]
            self.assertEqual((recovery_entry.get("data") or {}).get("event_type"), "recovery_completed")

    def test_synthetic_soak_cli_writes_markdown_and_json_sidecar(self) -> None:
        """``synthetic-soak`` CLI must persist both the markdown report and a
        JSON sidecar at the matching ``.json`` path. The sidecar carries the
        same summary metadata that ``run_soak()`` produced plus representative
        check entries such as ``runtime ready barrier``, ``classification_fallback_detected``,
        and ``stop left no orphan session``."""
        import json as _json

        soak_summary = {
            "start_detail": "started",
            "ready_ok": True,
            "ready_wait_sec": 2.1,
            "ready_timeout_sec": 45.0,
            "duration_sec": 10.0,
            "samples": 6,
            "state_counts": {"RUNNING": 6},
            "degraded_counts": {},
            "degraded_seen": False,
            "broken_seen": False,
            "receipt_count": 2,
            "control_change_count": 1,
            "duplicate_dispatch_count": 0,
            "control_mismatch_samples": 0,
            "control_mismatch_max_streak": 0,
            "receipt_pending_samples": 0,
            "classification_gate_failures": 0,
            "classification_gate_details": [],
            "orphan_session": False,
            "readiness_snapshot": {"runtime_state": "RUNNING", "lanes": []},
            "runtime_context": {
                "current_run_id": "run-synthetic-1",
                "automation_health": "attention",
                "automation_reason_code": "dispatch_stall",
                "automation_incident_family": "dispatch_stall",
                "automation_next_action": "verify_followup",
                "open_control": {
                    "active_control_file": ".pipeline/claude_handoff.md",
                    "active_control_seq": 17,
                    "active_control_status": "implement",
                },
                "active_round": {"state": "VERIFY_PENDING", "job_id": "job-1"},
                "latest_status": {"runtime_state": "DEGRADED"},
                "recent_events": [
                    {"event_type": "automation_incident", "payload": {"reason_code": "dispatch_stall"}}
                ],
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            synthetic_root = tmp_root / "synthetic"
            synthetic_root.mkdir()
            report_path = tmp_root / "projecth-runtime-synthetic-soak.md"
            expected_json_path = tmp_root / "projecth-runtime-synthetic-soak.json"

            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "prepare_synthetic_workspace",
                    return_value=(synthetic_root, {}),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "run_soak",
                    return_value=(True, soak_summary),
                ),
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_finalize_synthetic_workspace",
                    return_value=(False, "background_delete_requested(pid=42)"),
                ),
            ):
                exit_code = pipeline_runtime_gate.main(
                    [
                        "--project-root",
                        str(tmp_root),
                        "synthetic-soak",
                        "--workspace-root",
                        str(tmp_root),
                        "--duration-sec",
                        "10",
                        "--sample-interval-sec",
                        "1",
                        "--min-receipts",
                        "1",
                        "--report",
                        str(report_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(report_path.exists())
            self.assertTrue(expected_json_path.exists())

            report_text = report_path.read_text(encoding="utf-8")
            # Markdown stays readable and includes representative checks.
            self.assertIn("`PASS` runtime ready barrier", report_text)
            self.assertIn("`PASS` classification_fallback_detected", report_text)
            self.assertIn("`PASS` stop left no orphan session", report_text)
            self.assertIn("current_run_id=run-synthetic-1", report_text)
            self.assertIn("incident_family=dispatch_stall", report_text)

            payload = _json.loads(expected_json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("title"), "Pipeline Runtime synthetic soak sample")
            self.assertTrue(payload.get("ok"))
            summary = payload.get("summary") or {}
            self.assertEqual(summary.get("project"), str(synthetic_root))
            self.assertEqual(summary.get("mode"), "experimental")
            self.assertEqual(summary.get("workspace_retained"), False)
            self.assertEqual(summary.get("workspace_cleanup"), "background_delete_requested(pid=42)")
            self.assertEqual(summary.get("receipt_count"), 2)
            self.assertEqual(summary.get("duplicate_dispatch_count"), 0)
            self.assertEqual(summary.get("classification_gate_failures"), 0)
            self.assertEqual(summary.get("classification_gate_details"), [])
            self.assertEqual(summary.get("orphan_session"), False)
            self.assertEqual(summary.get("readiness_snapshot"), {"runtime_state": "RUNNING", "lanes": []})
            self.assertEqual(summary.get("current_run_id"), "run-synthetic-1")
            self.assertEqual(summary.get("automation_health"), "attention")
            self.assertEqual(summary.get("automation_reason_code"), "dispatch_stall")
            self.assertEqual(summary.get("incident_family"), "dispatch_stall")
            self.assertEqual(summary.get("automation_next_action"), "verify_followup")
            runtime_context = summary.get("runtime_context") or {}
            self.assertEqual(runtime_context.get("open_control", {}).get("active_control_seq"), 17)
            self.assertEqual(runtime_context.get("active_round", {}).get("job_id"), "job-1")
            self.assertEqual((runtime_context.get("recent_events") or [])[0]["event_type"], "automation_incident")
            names = {str(item.get("name") or "") for item in payload.get("checks") or []}
            for expected_name in (
                "runtime start",
                "runtime ready barrier",
                "synthetic workload produced receipts",
                "classification_fallback_detected",
                "stop left no orphan session",
            ):
                self.assertIn(expected_name, names)

    def test_plain_soak_cli_writes_markdown_and_json_sidecar(self) -> None:
        """Plain ``soak`` CLI must also persist both markdown and JSON sidecar,
        sharing the same sidecar contract as ``synthetic-soak``. The sidecar
        must include the path-specific ``project`` / ``session`` / ``mode``
        metadata and representative readiness and classification checks."""
        import json as _json

        soak_summary = {
            "start_detail": "started",
            "ready_ok": True,
            "ready_wait_sec": 4.2,
            "ready_timeout_sec": 60.0,
            "duration_sec": 30.0,
            "samples": 10,
            "state_counts": {"RUNNING": 10},
            "degraded_counts": {},
            "degraded_seen": False,
            "broken_seen": False,
            "receipt_count": 5,
            "control_change_count": 3,
            "duplicate_dispatch_count": 0,
            "control_mismatch_samples": 0,
            "control_mismatch_max_streak": 0,
            "receipt_pending_samples": 0,
            "classification_gate_failures": 0,
            "classification_gate_details": [],
            "orphan_session": False,
            "readiness_snapshot": {"runtime_state": "RUNNING", "lanes": []},
            "runtime_context": {
                "current_run_id": "run-soak-1",
                "automation_health": "ok",
                "automation_reason_code": "",
                "automation_incident_family": "",
                "automation_next_action": "continue",
                "open_control": {
                    "active_control_file": "",
                    "active_control_seq": -1,
                    "active_control_status": "none",
                },
                "active_round": {"state": "IDLE"},
                "latest_status": {"runtime_state": "RUNNING"},
                "recent_events": [],
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            report_path = tmp_root / "projecth-runtime-soak-sample.md"
            expected_json_path = tmp_root / "projecth-runtime-soak-sample.json"

            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "run_soak",
                    return_value=(True, soak_summary),
                ),
            ):
                exit_code = pipeline_runtime_gate.main(
                    [
                        "--project-root",
                        str(tmp_root),
                        "soak",
                        "--duration-sec",
                        "30",
                        "--sample-interval-sec",
                        "1",
                        "--report",
                        str(report_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(report_path.exists())
            self.assertTrue(expected_json_path.exists())

            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("`PASS` runtime ready barrier", report_text)
            self.assertIn("`PASS` classification_fallback_detected", report_text)

            payload = _json.loads(expected_json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("title"), "Pipeline Runtime soak sample")
            self.assertTrue(payload.get("ok"))
            summary = payload.get("summary") or {}
            self.assertEqual(summary.get("project"), str(tmp_root))
            self.assertEqual(summary.get("mode"), "experimental")
            self.assertEqual(summary.get("receipt_count"), 5)
            self.assertEqual(summary.get("duplicate_dispatch_count"), 0)
            self.assertEqual(summary.get("current_run_id"), "run-soak-1")
            self.assertEqual(summary.get("automation_health"), "ok")
            self.assertEqual(summary.get("automation_next_action"), "continue")
            self.assertNotIn("workspace_retained", summary)
            self.assertNotIn("workspace_cleanup", summary)
            names = {str(item.get("name") or "") for item in payload.get("checks") or []}
            for expected_name in (
                "runtime start",
                "runtime ready barrier",
                "classification_fallback_detected",
                "stop left no orphan session",
            ):
                self.assertIn(expected_name, names)

    def test_report_json_sidecar_path_swaps_md_suffix_and_appends_for_suffixless_paths(self) -> None:
        self.assertEqual(
            pipeline_runtime_gate._report_json_sidecar_path(Path("/tmp/foo.md")),
            Path("/tmp/foo.json"),
        )
        self.assertEqual(
            pipeline_runtime_gate._report_json_sidecar_path(Path("/tmp/foo")),
            Path("/tmp/foo.json"),
        )

    def test_synthetic_soak_report_slug_promotes_six_hour_baseline(self) -> None:
        self.assertEqual(
            pipeline_runtime_gate._synthetic_soak_report_slug(21600),
            "6h-synthetic-soak",
        )
        self.assertEqual(
            pipeline_runtime_gate._synthetic_soak_report_slug(86400),
            "24h-synthetic-soak",
        )
        self.assertEqual(
            pipeline_runtime_gate._synthetic_soak_report_slug(60),
            "pipeline-runtime-synthetic-soak",
        )

    def test_run_fault_check_surfaces_degraded_precedence_probes_before_live_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(
                    pipeline_runtime_gate,
                    "_start_runtime",
                    return_value=(False, "synthetic: start skipped"),
                ),
                mock.patch.object(pipeline_runtime_gate, "_stop_runtime", return_value=(True, "stopped")),
            ):
                ok, checks = pipeline_runtime_gate.run_fault_check(
                    root,
                    mode="experimental",
                    session="aip-test",
                )
        check_names = [str(item.get("name") or "") for item in checks]
        self.assertIn("receipt manifest mismatch degraded precedence", check_names)
        self.assertIn("active lane auth failure degraded precedence", check_names)
        # Probes run before the live runtime-start step.
        self.assertLess(
            check_names.index("receipt manifest mismatch degraded precedence"),
            check_names.index("runtime start"),
        )
        self.assertLess(
            check_names.index("active lane auth failure degraded precedence"),
            check_names.index("runtime start"),
        )
        for name in (
            "receipt manifest mismatch degraded precedence",
            "active lane auth failure degraded precedence",
        ):
            entry = next(item for item in checks if item.get("name") == name)
            self.assertTrue(entry.get("ok"), entry.get("detail"))
        self.assertFalse(ok)

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
