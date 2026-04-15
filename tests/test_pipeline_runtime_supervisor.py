from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from pipeline_runtime.cli import build_parser
from pipeline_runtime.supervisor import RuntimeSupervisor
from pipeline_runtime.wrapper_events import append_wrapper_event, build_lane_read_models


def _write_active_profile(root: Path) -> None:
    active_path = root / ".pipeline" / "config" / "agent_profile.json"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "selected_agents": ["Claude", "Codex", "Gemini"],
                "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
                "role_options": {
                    "advisory_enabled": True,
                    "operator_stop_enabled": True,
                    "session_arbitration_enabled": True,
                },
                "mode_flags": {
                    "single_agent_mode": False,
                    "self_verify_allowed": False,
                    "self_advisory_allowed": False,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


class RuntimeSupervisorTest(unittest.TestCase):
    def test_cli_start_parser_accepts_legacy_mode_positionally(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["start", "/tmp/projectH", "baseline", "--no-attach"])
        self.assertEqual(args.project_root, "/tmp/projectH")
        self.assertEqual(args.legacy_mode, "baseline")
        self.assertTrue(args.no_attach)

    def test_write_status_emits_receipt_and_control_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-1"
            verify_dir = root / "verify" / "4" / "11"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 17\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 17,
                        "verify_job_id": "job-1",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-2.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-1",
                        "round": 2,
                        "role": "verify",
                        "artifact_hash": "artifact-hash-1",
                        "created_at": "2026-04-11T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-1.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-1",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/11/work-note.md",
                        "artifact_hash": "artifact-hash-1",
                        "round": 2,
                        "verify_manifest_path": str(manifest_path),
                        "verify_result": "passed_by_feedback",
                        "updated_at": 100.0,
                        "verify_completed_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )
            verify_path = verify_dir / "2026-04-11-verify.md"
            verify_path.write_text("# verify\n", encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            status = supervisor._write_status()

            self.assertEqual(status["control"]["active_control_file"], ".pipeline/claude_handoff.md")
            self.assertEqual(status["control"]["active_control_seq"], 17)
            self.assertEqual(status["active_round"]["job_id"], "job-1")
            self.assertTrue(status["last_receipt_id"])
            receipt_path = supervisor.receipts_dir / f"{status['last_receipt_id']}.json"
            self.assertTrue(receipt_path.exists())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["job_id"], "job-1")
            self.assertEqual(receipt["control_seq"], 17)
            self.assertEqual(receipt["verify_result"], "passed_by_feedback")

    def test_current_run_pointer_tracks_run_scoped_status_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, run_id="20260415T010203Z-p123", start_runtime=False)

            supervisor._write_current_run_pointer()

            current_run = json.loads((root / ".pipeline" / "current_run.json").read_text(encoding="utf-8"))
            self.assertEqual(current_run["run_id"], "20260415T010203Z-p123")
            self.assertEqual(current_run["status_path"], ".pipeline/runs/20260415T010203Z-p123/status.json")
            self.assertEqual(current_run["events_path"], ".pipeline/runs/20260415T010203Z-p123/events.jsonl")

    def test_manifest_mismatch_blocks_receipt_and_marks_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-2"
            verify_dir = root / "verify" / "4" / "11"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 23\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 23,
                        "verify_job_id": "job-2",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-1.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-2",
                        "round": 1,
                        "role": "verify",
                        "artifact_hash": "expected-hash",
                        "created_at": "2026-04-11T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-2.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-2",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/11/work-note.md",
                        "artifact_hash": "mismatched-hash",
                        "round": 1,
                        "verify_manifest_path": str(manifest_path),
                        "verify_result": "failed",
                        "updated_at": 100.0,
                        "verify_completed_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )
            (verify_dir / "2026-04-11-verify.md").write_text("# verify\n", encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertIn("receipt_manifest:job-2", status["degraded_reason"])
            self.assertEqual(status["last_receipt_id"], "")

    def test_slot_verify_manifest_role_is_accepted_for_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-slot-verify"
            verify_dir = root / "verify" / "4" / "11"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 31\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 31,
                        "verify_job_id": "job-slot-verify",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-1.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-slot-verify",
                        "round": 1,
                        "role": "slot_verify",
                        "artifact_hash": "artifact-hash-slot-verify",
                        "created_at": "2026-04-11T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-slot-verify.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-slot-verify",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/11/work-note.md",
                        "artifact_hash": "artifact-hash-slot-verify",
                        "round": 1,
                        "verify_manifest_path": str(manifest_path),
                        "verify_result": "passed_by_feedback",
                        "updated_at": 100.0,
                        "verify_completed_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )
            (verify_dir / "2026-04-11-verify.md").write_text("# verify\n", encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "STOPPED")
            self.assertEqual(status["degraded_reason"], "")
            self.assertTrue(status["last_receipt_id"])

    def test_stale_verify_done_does_not_degrade_when_newer_round_is_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "job-old.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-old",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/11/old.md",
                        "artifact_hash": "old-hash",
                        "round": 1,
                        "verify_manifest_path": "",
                        "verify_result": "passed",
                        "updated_at": 10.0,
                        "verify_completed_at": 10.0,
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-new.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-new",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/11/new.md",
                        "artifact_hash": "new-hash",
                        "round": 2,
                        "verify_manifest_path": "",
                        "updated_at": 20.0,
                        "verify_completed_at": 0.0,
                    }
                ),
                encoding="utf-8",
            )
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 101}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [{"name": "Claude", "state": "READY", "attachable": True, "pid": 11}],
                        {"Claude": {"state": "READY", "note": ""}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "RUNNING")
            self.assertEqual(status["degraded_reason"], "")
            self.assertEqual(list(status.get("degraded_reasons") or []), [])

    def test_verify_done_without_receipt_stays_receipt_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "job-receipt-pending.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-receipt-pending",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/15/work-note.md",
                        "artifact_hash": "artifact-hash-pending",
                        "round": 4,
                        "verify_manifest_path": "",
                        "verify_result": "passed",
                        "updated_at": 50.0,
                        "verify_completed_at": 50.0,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            status = supervisor._write_status()

            self.assertEqual(status["active_round"]["job_id"], "job-receipt-pending")
            self.assertEqual(status["active_round"]["state"], "RECEIPT_PENDING")
            self.assertEqual(status["last_receipt_id"], "")
            self.assertNotEqual(status["active_round"]["state"], "CLOSED")

    def test_build_lane_read_models_marks_working_and_heartbeat_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wrapper_dir = Path(tmp)
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "READY",
                {"reason": "prompt_visible"},
                source="wrapper",
                derived_from="vendor_output",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "HEARTBEAT",
                {},
                source="wrapper",
                derived_from="process_alive",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_ACCEPTED",
                {"job_id": "job-42", "control_seq": 19, "attempt": 1},
                source="wrapper",
                derived_from="vendor_output",
            )
            models = build_lane_read_models(wrapper_dir, heartbeat_timeout_sec=3600.0, now_ts=1.0)
            self.assertEqual(models["Codex"]["state"], "WORKING")
            self.assertEqual(models["Codex"]["accepted_task"]["job_id"], "job-42")

            stale_models = build_lane_read_models(wrapper_dir, heartbeat_timeout_sec=0.0, now_ts=9999999999.0)
            self.assertEqual(stale_models["Codex"]["state"], "BROKEN")
            self.assertEqual(stale_models["Codex"]["note"], "heartbeat_timeout")

    def test_active_verify_round_keeps_codex_surface_working_even_if_wrapper_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with mock.patch.object(
                supervisor.adapter,
                "lane_health",
                return_value={"alive": True, "pid": 4242, "attachable": True, "pane_id": "%2"},
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-15T08:33:21.218699Z",
                            "last_heartbeat_at": "2026-04-15T08:33:27.312433Z",
                        }
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-42",
                        "state": "VERIFYING",
                        "status": "VERIFY_RUNNING",
                    },
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "WORKING")
            self.assertEqual(codex["note"], "verifying")

    def test_active_lane_auth_failure_marks_lane_broken(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 4242, "attachable": True, "pane_id": "%2"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    return_value=(
                        "API Error: 401\n"
                        '{"error":{"type":"authentication_error","message":"Invalid authentication credentials"}}\n'
                        "Please run /login\n"
                    ),
                ),
            ):
                lanes, models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Claude": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-15T08:33:21.218699Z",
                            "last_heartbeat_at": "2026-04-15T08:33:27.312433Z",
                        }
                    },
                    active_lane="Claude",
                    active_round=None,
                    control={"active_control_status": "implement"},
                )
            claude = next(lane for lane in lanes if lane["name"] == "Claude")
            self.assertEqual(claude["state"], "BROKEN")
            self.assertEqual(claude["note"], "auth_login_required")
            self.assertEqual(models["Claude"]["failure_reason"], "auth_login_required")

    def test_codex_followup_turn_surfaces_working_even_without_active_control_seq(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with mock.patch.object(
                supervisor.adapter,
                "lane_health",
                return_value={"alive": True, "pid": 5252, "attachable": True, "pane_id": "%5"},
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-15T08:33:21.218699Z",
                            "last_heartbeat_at": "2026-04-15T08:33:27.312433Z",
                        }
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-closed",
                        "state": "CLOSED",
                        "status": "VERIFY_DONE",
                    },
                    turn_state={"state": "CODEX_FOLLOWUP"},
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "WORKING")
            self.assertEqual(codex["note"], "followup")

    def test_active_verify_round_falls_back_to_codex_when_turn_state_is_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "IDLE"},
                {
                    "job_id": "job-42",
                    "state": "VERIFYING",
                    "status": "VERIFY_RUNNING",
                },
                control={},
            )

            self.assertEqual(active_lane, "Codex")

    def test_operator_wait_blocks_verify_fallback_active_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "OPERATOR_WAIT"},
                {
                    "job_id": "job-42",
                    "state": "VERIFYING",
                    "status": "VERIFY_RUNNING",
                },
                control={},
            )

            self.assertEqual(active_lane, "")

    def test_operator_wait_allows_verify_fallback_when_stale_operator_stop_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "OPERATOR_WAIT"},
                {
                    "job_id": "job-42",
                    "state": "VERIFYING",
                    "status": "VERIFY_RUNNING",
                },
                control={},
                stale_operator_control={"reason": "verified_blockers_resolved"},
            )

            self.assertEqual(active_lane, "Codex")

    def test_active_lane_for_runtime_ignores_stale_claude_active_when_control_seq_is_already_receipted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "CLAUDE_ACTIVE"},
                {"job_id": "job-42", "state": "CLOSED", "status": "VERIFY_DONE"},
                control={
                    "active_control_file": ".pipeline/claude_handoff.md",
                    "active_control_seq": 154,
                    "active_control_status": "implement",
                },
                last_receipt={"control_seq": 154},
                duplicate_control=None,
            )

            self.assertEqual(active_lane, "")

    def test_write_status_clears_codex_task_hint_during_operator_wait(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 142\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "OPERATOR_WAIT",
                        "entered_at": 1.0,
                        "reason": "operator_request_updated",
                        "active_control_file": "operator_request.md",
                        "active_control_seq": 142,
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-42.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-42",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/15/work-note.md",
                        "round": 1,
                        "updated_at": 100.0,
                    }
                ),
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
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            codex_hint = json.loads(supervisor._task_hint_path("Codex").read_text(encoding="utf-8"))
            self.assertEqual(status["control"]["active_control_status"], "needs_operator")
            self.assertEqual(status["compat"]["turn_state"]["state"], "OPERATOR_WAIT")
            self.assertEqual(next(lane for lane in status["lanes"] if lane["name"] == "Codex")["state"], "READY")
            self.assertFalse(codex_hint["active"])
            self.assertEqual(codex_hint["job_id"], "")
            self.assertEqual(codex_hint["control_seq"], -1)

    def test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            logs_dir = pipeline_dir / "logs" / "experimental"
            state_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)
            handoff_path = pipeline_dir / "claude_handoff.md"
            handoff_path.write_text(
                "STATUS: implement\nCONTROL_SEQ: 154\n",
                encoding="utf-8",
            )
            handoff_sha = hashlib.sha256(handoff_path.read_bytes()).hexdigest()
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CLAUDE_ACTIVE",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 154,
                    }
                ),
                encoding="utf-8",
            )
            handoff_logged_at = time.time()
            os.utime(handoff_path, (handoff_logged_at - 5.0, handoff_logged_at - 5.0))
            (logs_dir / "raw.jsonl").write_text(
                json.dumps(
                    {
                        "event": "codex_blocked_triage_notify",
                        "path": str(handoff_path),
                        "blocked_reason": "handoff_already_completed",
                        "blocked_fingerprint": "dup-154",
                        "handoff_sha": handoff_sha,
                        "at": handoff_logged_at,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    side_effect=lambda lane_name: {
                        "alive": True,
                        "pid": {"Claude": 11, "Codex": 12, "Gemini": 13}.get(lane_name),
                        "attachable": True,
                        "pane_id": "%1",
                    },
                ),
                mock.patch(
                    "pipeline_runtime.supervisor.build_lane_read_models",
                    return_value={
                        "Claude": {
                            "state": "WORKING",
                            "note": "seq 154",
                            "accepted_task": {"job_id": "job-42", "control_seq": 154, "attempt": 1},
                            "last_event_at": "2026-04-15T13:22:16.919339Z",
                            "last_heartbeat_at": "2026-04-15T13:22:16.919339Z",
                        }
                    },
                ),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            claude = next(lane for lane in status["lanes"] if lane["name"] == "Claude")
            claude_hint = json.loads(supervisor._task_hint_path("Claude").read_text(encoding="utf-8"))
            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(claude["state"], "READY")
            self.assertEqual(claude["note"], "waiting_next_control")
            self.assertFalse(claude_hint["active"])
            self.assertEqual(claude_hint["inactive_reason"], "duplicate_handoff")
            duplicate_events = [event for event in events if event.get("event_type") == "control_duplicate_ignored"]
            self.assertEqual(len(duplicate_events), 1)
            self.assertEqual(duplicate_events[0]["payload"]["control_seq"], 154)
            self.assertEqual(duplicate_events[0]["payload"]["routed_to"], "codex_triage")

    def test_write_status_ignores_operator_stop_when_referenced_work_is_already_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 155",
                        "",
                        "- work/4/15/2026-04-15-review-queue-action-vocabulary-reject-defer.md",
                        "- work/4/15/2026-04-15-review-queue-source-message-review-outcome-visibility.md",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "OPERATOR_WAIT",
                        "entered_at": 1.0,
                        "reason": "operator_request_updated",
                        "active_control_file": "operator_request.md",
                        "active_control_seq": 155,
                    }
                ),
                encoding="utf-8",
            )
            for job_id, artifact_path, updated_at in [
                (
                    "job-reject-defer",
                    str(root / "work" / "4" / "15" / "2026-04-15-review-queue-action-vocabulary-reject-defer.md"),
                    100.0,
                ),
                (
                    "job-source-message",
                    str(root / "work" / "4" / "15" / "2026-04-15-review-queue-source-message-review-outcome-visibility.md"),
                    110.0,
                ),
            ]:
                artifact = Path(artifact_path)
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text("# work\n", encoding="utf-8")
                (state_dir / f"{job_id}.json").write_text(
                    json.dumps(
                        {
                            "job_id": job_id,
                            "status": "VERIFY_DONE",
                            "artifact_path": artifact_path,
                            "artifact_hash": f"hash-{job_id}",
                            "round": 1,
                            "verify_result": "passed_by_feedback",
                            "updated_at": updated_at,
                            "verify_completed_at": updated_at,
                        }
                    ),
                    encoding="utf-8",
                )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            stale_events = [event for event in events if event.get("event_type") == "control_operator_stale_ignored"]

            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["control"]["active_control_seq"], -1)
            self.assertEqual(status["compat"]["control_slots"]["active"]["file"], "operator_request.md")
            self.assertEqual(len(stale_events), 1)
            self.assertEqual(stale_events[0]["payload"]["control_seq"], 155)
            self.assertEqual(stale_events[0]["payload"]["reason"], "verified_blockers_resolved")

    def test_launch_runtime_spawns_lanes_and_watcher_directly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(supervisor, "_find_cli_bin", side_effect=lambda name: f"/usr/bin/{name}"),
                mock.patch.object(supervisor.adapter, "kill_session", return_value=True),
                mock.patch.object(supervisor.adapter, "create_scaffold", return_value={"Claude": "%1", "Codex": "%2", "Gemini": "%3"}),
                mock.patch.object(supervisor.adapter, "spawn_lane", return_value=True) as spawn_lane,
                mock.patch.object(supervisor.adapter, "pane_for_lane", side_effect=lambda lane: {"pane_id": {"Claude": "%1", "Codex": "%2", "Gemini": "%3"}[lane]}),
                mock.patch.object(supervisor.adapter, "spawn_watcher", return_value={"pane_id": "%9", "pid": 12345, "window_name": "watcher-exp"}) as spawn_watcher,
                mock.patch("pipeline_runtime.supervisor.resolve_project_runtime_file", side_effect=lambda _project, name: root / name),
                mock.patch.object(supervisor, "_start_token_collector"),
                mock.patch.object(supervisor, "_terminate_repo_watchers"),
            ):
                for helper in ("watcher_core.py", "pipeline-watcher-v3-logged.sh", "token_collector.py"):
                    (root / helper).write_text("#!/bin/bash\n", encoding="utf-8")
                supervisor._launch_runtime()

            self.assertTrue(supervisor._runtime_started)
            self.assertGreaterEqual(spawn_lane.call_count, 3)
            self.assertTrue(any("lane-wrapper" in str(call.args[1]) for call in spawn_lane.call_args_list))
            spawn_watcher.assert_called()
            self.assertIn(
                "PIPELINE_RUNTIME_DISABLE_EXPORTER=1",
                str(spawn_watcher.call_args.kwargs.get("shell_command") or ""),
            )
            experimental_pid = root / ".pipeline" / "experimental.pid"
            self.assertTrue(experimental_pid.exists())

    def test_runtime_stays_starting_until_all_enabled_lanes_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 101}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11},
                            {"name": "Codex", "state": "BOOTING", "attachable": True, "pid": 12},
                        ],
                        {
                            "Claude": {"state": "READY", "note": ""},
                            "Codex": {"state": "BOOTING", "note": ""},
                        },
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
            self.assertEqual(status["runtime_state"], "STARTING")

    def test_verify_prompt_prefers_gemini_before_operator_for_slice_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            prompt = supervisor._prompt_templates()["verify"]

            self.assertIn("next-slice ambiguity", prompt)
            self.assertIn(".pipeline/gemini_request.md before .pipeline/operator_request.md", prompt)
            self.assertIn("real operator-only decision", prompt)

    def test_followup_prompt_only_uses_operator_after_inconclusive_gemini_advice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            prompt = supervisor._prompt_templates()["followup"]

            self.assertIn("after Gemini advice", prompt)
            self.assertIn(".pipeline/operator_request.md", prompt)
            self.assertIn("no truthful exact slice", prompt)

    def test_session_loss_transitions_runtime_to_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 101}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [{"name": "Claude", "state": "READY", "attachable": True, "pid": 11}],
                        {"Claude": {"state": "READY", "note": ""}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertEqual(status["degraded_reason"], "session_missing")
            self.assertIn("session_missing", list(status.get("degraded_reasons") or []))

    def test_session_loss_stays_degraded_even_when_watcher_is_also_gone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [{"name": "Claude", "state": "READY", "attachable": True, "pid": 11}],
                        {"Claude": {"state": "READY", "note": ""}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertEqual(status["degraded_reason"], "session_missing")
            self.assertIn("session_missing", list(status.get("degraded_reasons") or []))

    def test_session_loss_degrades_even_if_lane_health_has_already_dropped_to_off(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "OFF", "attachable": False, "pid": None},
                            {"name": "Codex", "state": "OFF", "attachable": False, "pid": None},
                        ],
                        {"Claude": {}, "Codex": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertIn("session_missing", list(status.get("degraded_reasons") or []))

    def test_claude_post_accept_breakage_blocks_blind_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            lane = {"name": "Claude", "state": "BROKEN"}
            lane_model = {
                "accepted_task": {"job_id": "job-7", "control_seq": 21, "attempt": 1},
            }
            with mock.patch.object(supervisor.adapter, "restart_lane") as restart_lane:
                reason = supervisor._maybe_recover_lane(
                    lane,
                    lane_model=lane_model,
                    active_round={"job_id": "job-7", "state": "VERIFYING"},
                )
            self.assertEqual(reason, "claude_interrupted_post_accept")
            restart_lane.assert_not_called()

    def test_auth_failure_breakage_blocks_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            lane = {"name": "Claude", "state": "BROKEN", "note": "auth_login_required"}
            lane_model = {"accepted_task": None, "failure_reason": "auth_login_required"}
            with mock.patch.object(supervisor.adapter, "restart_lane") as restart_lane:
                reason = supervisor._maybe_recover_lane(
                    lane,
                    lane_model=lane_model,
                    active_round=None,
                )
            self.assertEqual(reason, "claude_auth_login_required")
            restart_lane.assert_not_called()

    def test_write_status_marks_runtime_degraded_on_active_lane_auth_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 17\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CLAUDE_ACTIVE",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 17,
                    }
                ),
                encoding="utf-8",
            )
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            def lane_health(lane_name: str) -> dict[str, object]:
                return {"alive": True, "pid": 5000, "attachable": True, "pane_id": f"%{lane_name}"}

            def capture_tail(lane_name: str, lines: int = 60) -> str:
                if lane_name == "Claude":
                    return (
                        "API Error: 401\n"
                        '{"error":{"type":"authentication_error","message":"Invalid authentication credentials"}}\n'
                        "Please run /login\n"
                    )
                return ""

            with (
                mock.patch.object(supervisor.adapter, "lane_health", side_effect=lane_health),
                mock.patch.object(supervisor.adapter, "capture_tail", side_effect=capture_tail),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
            ):
                status = supervisor._write_status()

            claude = next(lane for lane in status["lanes"] if lane["name"] == "Claude")
            self.assertEqual(claude["state"], "BROKEN")
            self.assertEqual(claude["note"], "auth_login_required")
            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertIn("claude_auth_login_required", list(status.get("degraded_reasons") or []))

    def test_codex_pre_completion_breakage_restarts_within_retry_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            lane = {"name": "Codex", "state": "BROKEN"}
            lane_model = {"accepted_task": None}
            with (
                mock.patch.object(supervisor.adapter, "restart_lane", return_value=True) as restart_lane,
                mock.patch.object(supervisor, "_lane_shell_command", return_value="run-codex") as lane_shell_command,
            ):
                reason = supervisor._maybe_recover_lane(
                    lane,
                    lane_model=lane_model,
                    active_round={"job_id": "job-8", "state": "VERIFY_PENDING"},
                )
            self.assertEqual(reason, "")
            lane_shell_command.assert_called_once_with("Codex")
            restart_lane.assert_called_once_with("Codex", "run-codex")
            self.assertEqual(supervisor._lane_restart_counts["Codex"], 1)

    def test_codex_breakage_stops_after_retry_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._lane_restart_counts["Codex"] = 2
            reason = supervisor._maybe_recover_lane(
                {"name": "Codex", "state": "BROKEN"},
                lane_model={"accepted_task": None},
                active_round={"job_id": "job-9", "state": "VERIFY_PENDING"},
            )
            self.assertEqual(reason, "codex_broken")

    def test_lane_vendor_command_prefers_env_override_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, run_id="run-123", start_runtime=False)
            with mock.patch.dict(
                "os.environ",
                {
                    "PIPELINE_RUNTIME_LANE_COMMAND_CODEX": "python3 fake.py --project-root {project_root_shlex} --lane {lane} --run {run_id}",
                },
                clear=False,
            ):
                command = supervisor._lane_vendor_command("Codex")
            self.assertIn("python3 fake.py", command)
            self.assertIn("--project-root", command)
            self.assertIn(str(root), command)
            self.assertIn("--lane Codex", command)
            self.assertIn("--run run-123", command)

    def test_lane_shell_command_carries_pythonpath_into_tmux_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, run_id="run-456", start_runtime=False)
            with mock.patch.dict("os.environ", {"PYTHONPATH": "/tmp/fake-path"}, clear=False):
                command = supervisor._lane_shell_command("Codex")
            self.assertIn("env PYTHONPATH=/tmp/fake-path", command)
            self.assertIn(f"PROJECT_ROOT={root}", command)
            self.assertIn("pipeline_runtime.cli lane-wrapper", command)


if __name__ == "__main__":
    unittest.main()
