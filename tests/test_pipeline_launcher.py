from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline_gui.project import _session_name_for


def _load_launcher_module():
    module_name = "pipeline_launcher_under_test"
    module_path = Path(__file__).resolve().parents[1] / "pipeline-launcher.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load pipeline-launcher.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


pipeline_launcher = _load_launcher_module()


class TestPipelineLauncherSessionContract(unittest.TestCase):
    def test_resolved_session_name_matches_shared_project_rule(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-session-") as tmp:
            project = Path(tmp).resolve()
            self.assertEqual(
                pipeline_launcher.resolved_session_name(project),
                _session_name_for(project),
            )

    def test_pipeline_start_passes_project_aware_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-start-") as tmp:
            project = Path(tmp).resolve()
            expected_session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "resolve_project_active_profile",
                return_value={"controls": {"launch_allowed": True}},
            ), mock.patch.object(
                pipeline_launcher,
                "_spawn_runtime_cli",
            ) as spawn_cli:
                message = pipeline_launcher.pipeline_start(project)

            self.assertEqual(message, "시작 요청됨")
            spawn_cli.assert_called_once_with(
                project,
                ["start", str(project), "--mode", "experimental", "--session", expected_session, "--no-attach"],
                action="start",
            )

    def test_pipeline_start_returns_already_running_when_runtime_active(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-start-active-") as tmp:
            project = Path(tmp).resolve()

            with mock.patch.object(
                pipeline_launcher,
                "resolve_project_active_profile",
                return_value={"controls": {"launch_allowed": True}},
            ), mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={"runtime_state": "RUNNING", "watcher": {"alive": True, "pid": 1234}},
            ), mock.patch.object(
                pipeline_launcher,
                "_spawn_runtime_cli",
            ) as spawn_cli:
                message = pipeline_launcher.pipeline_start(project)

            self.assertEqual(message, "이미 실행 중입니다. Restart를 사용하세요.")
            spawn_cli.assert_not_called()

    def test_pipeline_stop_passes_project_aware_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-stop-") as tmp:
            project = Path(tmp).resolve()
            expected_session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "_run_runtime_cli",
                return_value=mock.Mock(returncode=0, stdout="", stderr=""),
            ) as run_cli:
                message = pipeline_launcher.pipeline_stop(project)

            self.assertEqual(message, "중지 완료")
            run_cli.assert_called_once_with(
                project,
                ["stop", str(project), "--session", expected_session],
            )

    def test_pipeline_restart_reuses_same_resolved_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-restart-") as tmp:
            project = Path(tmp).resolve()
            expected_session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "resolve_project_active_profile",
                return_value={"controls": {"launch_allowed": True}},
            ), mock.patch.object(
                pipeline_launcher, "pipeline_stop", return_value="중지 완료"
            ) as stop, mock.patch.object(
                pipeline_launcher, "pipeline_start", return_value="시작 요청됨"
            ) as start, mock.patch.object(pipeline_launcher.time, "sleep"):
                message = pipeline_launcher.pipeline_restart(project)

            self.assertEqual(message, "재시작 요청됨")
            stop.assert_called_once_with(project, expected_session)
            start.assert_called_once_with(project, expected_session)

    def test_runtime_views_and_attach_use_same_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-runtime-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={
                    "runtime_state": "RUNNING",
                    "lanes": [
                        {"name": "Claude", "state": "READY", "pid": 111, "last_event_at": "2026-04-11T00:00:00Z"},
                        {"name": "Codex", "state": "WORKING", "pid": 222, "last_event_at": "2026-04-11T00:01:00Z"},
                    ]
                },
            ), mock.patch.object(
                pipeline_launcher,
                "read_runtime_event_tail",
                return_value=[
                    {"event_type": "lane_ready", "payload": {"lane": "Claude", "state": "READY"}},
                    {"event_type": "lane_working", "payload": {"lane": "Codex", "state": "WORKING"}},
                ],
            ), mock.patch.object(
                pipeline_launcher.subprocess,
                "run",
                return_value=mock.Mock(returncode=0),
            ) as run_attach:
                runtime_view = pipeline_launcher._runtime_view(project)
                snapshots = pipeline_launcher.pane_snapshots(runtime_view)
                details = pipeline_launcher.focused_lane_details(project, runtime_view, 0)
                pipeline_launcher.runtime_attach(project, session)

            self.assertEqual(
                [(snap.label, snap.status) for snap in snapshots],
                [("Claude", "READY"), ("Codex", "WORKING")],
            )
            self.assertIn("name=Claude", details)
            self.assertIn("state=READY", details)
            self.assertIn("lane_ready READY", details)
            run_attach.assert_called_once()

    def test_duplicate_handoff_ready_note_is_rendered_truthfully(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-duplicate-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={
                    "runtime_state": "RUNNING",
                    "lanes": [
                        {
                            "name": "Claude",
                            "state": "READY",
                            "pid": 111,
                            "note": "waiting_next_control",
                            "last_event_at": "2026-04-15T13:24:13Z",
                        }
                    ]
                },
            ), mock.patch.object(
                pipeline_launcher,
                "read_runtime_event_tail",
                return_value=[
                    {
                        "event_type": "control_duplicate_ignored",
                        "payload": {
                            "control_file": ".pipeline/claude_handoff.md",
                            "control_seq": 154,
                            "reason": "handoff_already_completed",
                        },
                    }
                ],
            ):
                runtime_view = pipeline_launcher._runtime_view(project)
                snapshots = pipeline_launcher.pane_snapshots(runtime_view)
                details = pipeline_launcher.focused_lane_details(project, runtime_view, 0)

            self.assertEqual([(snap.label, snap.status, snap.status_note) for snap in snapshots], [("Claude", "READY", "waiting_next_control")])
            self.assertIn("note=waiting_next_control", details)
            self.assertTrue(any("control_duplicate_ignored" in line for line in details))

    def test_build_snapshot_surfaces_operator_wait_control_clearly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-operator-wait-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "_runtime_view",
                return_value={
                    "runtime_state": "RUNNING",
                    "watcher_alive": True,
                    "watcher_pid": 1010,
                    "work_name": "—",
                    "work_mtime": 0.0,
                    "verify_name": "—",
                    "verify_mtime": 0.0,
                    "control_file": ".pipeline/operator_request.md",
                    "control_seq": 155,
                    "control_status": "needs_operator",
                    "active_round": {"state": "CLOSED", "job_id": "job-123"},
                    "lanes": [{"name": "Claude", "state": "READY", "attachable": True}],
                    "event_lines": ["control_changed needs_operator seq=155 operator_request.md"],
                    "events": [],
                },
            ):
                lines = pipeline_launcher.build_snapshot(project, session)

            self.assertTrue(any("Control: operator_request.md · needs_operator · seq 155" in line for line in lines))
            self.assertTrue(any("control_changed needs_operator seq=155 operator_request.md" in line for line in lines))

    def test_runtime_view_tolerates_non_mapping_status_payload(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-status-shape-") as tmp:
            project = Path(tmp).resolve()

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value="runtime-status-corrupted",
            ), mock.patch.object(
                pipeline_launcher,
                "read_runtime_event_tail",
                return_value=[],
            ):
                runtime_view = pipeline_launcher._runtime_view(project)

            self.assertEqual(runtime_view["runtime_state"], "STOPPED")
            self.assertEqual(runtime_view["lanes"], [])

    def test_runtime_view_keeps_status_mapping_when_control_changed_event_exists(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-control-event-") as tmp:
            project = Path(tmp).resolve()

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={
                    "runtime_state": "RUNNING",
                    "lanes": [],
                    "watcher": {"alive": True, "pid": 1234},
                    "control": {
                        "active_control_file": ".pipeline/operator_request.md",
                        "active_control_seq": 155,
                        "active_control_status": "needs_operator",
                    },
                    "autonomy": {
                        "mode": "needs_operator",
                        "reason_code": "approval_required",
                        "operator_policy": "immediate_publish",
                        "classification_source": "operator_policy",
                    },
                },
            ), mock.patch.object(
                pipeline_launcher,
                "read_runtime_event_tail",
                return_value=[
                    {
                        "event_type": "control_changed",
                        "payload": {
                            "active_control_file": ".pipeline/operator_request.md",
                            "active_control_seq": 155,
                            "active_control_status": "needs_operator",
                        },
                    }
                ],
            ):
                runtime_view = pipeline_launcher._runtime_view(project)

            self.assertEqual(runtime_view["runtime_state"], "RUNNING")
            self.assertEqual(runtime_view["control_status"], "needs_operator")
            self.assertTrue(any("control_changed needs_operator" in line for line in runtime_view["event_lines"]))

    def test_runtime_view_surfaces_dispatch_stall_event_lines(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-dispatch-stall-") as tmp:
            project = Path(tmp).resolve()

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={
                    "runtime_state": "DEGRADED",
                    "degraded_reason": "dispatch_stall",
                    "degraded_reasons": ["dispatch_stall"],
                    "lanes": [
                        {"name": "Codex", "state": "READY", "note": "waiting_task_accept_after_dispatch"},
                    ],
                    "watcher": {"alive": True, "pid": 1234},
                    "control": {"active_control_status": "implement"},
                    "autonomy": {"mode": "normal"},
                },
            ), mock.patch.object(
                pipeline_launcher,
                "read_runtime_event_tail",
                return_value=[
                    {
                        "event_type": "dispatch_stall_detected",
                        "payload": {
                            "lane": "Codex",
                            "action": "degraded",
                            "reason": "waiting_task_accept_after_dispatch",
                        },
                    }
                ],
            ):
                runtime_view = pipeline_launcher._runtime_view(project)

            self.assertEqual(runtime_view["runtime_state"], "DEGRADED")
            self.assertEqual(runtime_view["degraded_reason"], "dispatch_stall")
            self.assertTrue(
                any(
                    "dispatch_stall_detected Codex degraded waiting_task_accept_after_dispatch" in line
                    for line in runtime_view["event_lines"]
                )
            )

    def test_runtime_view_marks_operator_classification_fallback_as_broken_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-operator-gate-") as tmp:
            project = Path(tmp).resolve()

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={
                    "runtime_state": "RUNNING",
                    "lanes": [],
                    "watcher": {"alive": True, "pid": 1234},
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
            ), mock.patch.object(
                pipeline_launcher,
                "read_runtime_event_tail",
                return_value=[],
            ):
                runtime_view = pipeline_launcher._runtime_view(project)

            self.assertEqual(runtime_view["runtime_state"], "BROKEN")
            self.assertEqual(runtime_view["degraded_reason"], "classification_fallback_detected")
            self.assertEqual(runtime_view["launcher_gate_status"], "FAILED")
            self.assertTrue(any("classification_fallback_detected" in line for line in runtime_view["event_lines"]))

    def test_build_snapshot_surfaces_autonomy_when_operator_is_gated(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-autonomy-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            lines = pipeline_launcher.build_snapshot(
                project,
                session,
                runtime_view={
                    "runtime_state": "RUNNING",
                    "watcher_alive": True,
                    "watcher_pid": 2020,
                    "work_name": "—",
                    "work_mtime": 0.0,
                    "verify_name": "—",
                    "verify_mtime": 0.0,
                    "control_file": "",
                    "control_seq": -1,
                    "control_status": "none",
                    "autonomy_mode": "triage",
                    "autonomy_reason": "slice_ambiguity",
                    "active_round": {"state": "IDLE"},
                    "lanes": [],
                    "event_lines": [],
                    "events": [],
                },
            )

        self.assertTrue(any("Autonomy: triage / slice_ambiguity" in line for line in lines))

    def test_launcher_source_keeps_runtime_wording_for_attach_and_start_pending(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "pipeline-launcher.py").read_text(encoding="utf-8")
        self.assertNotIn("def tmux_attach", source)
        self.assertNotIn("tmux/watcher 기동", source)
        self.assertNotIn("tmux 세션이 없습니다", source)
        self.assertNotIn("tmux에서 돌아왔습니다", source)

    def test_pane_snapshots_mark_disabled_lane_off_from_runtime_adapter(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-disabled-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={
                    "runtime_state": "RUNNING",
                    "lanes": [
                        {"name": "Claude", "state": "OFF", "attachable": False},
                        {"name": "Codex", "state": "BOOTING", "attachable": True},
                        {"name": "Gemini", "state": "OFF", "attachable": False},
                    ]
                },
            ):
                runtime_view = pipeline_launcher._runtime_view(project)
                snapshots = pipeline_launcher.pane_snapshots(runtime_view)

            self.assertEqual(
                [(snap.label, snap.status) for snap in snapshots],
                [("Claude", "OFF"), ("Codex", "BOOTING"), ("Gemini", "OFF")],
            )

    def test_follow_view_builds_snapshot_with_resolved_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-follow-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher, "build_snapshot", return_value=["snapshot"]
            ) as build_snapshot, mock.patch.object(
                pipeline_launcher, "clear_screen"
            ), mock.patch.object(
                pipeline_launcher.time,
                "time",
                side_effect=[0.0, 0.0, 0.0, 2.0],
            ), mock.patch.object(
                pipeline_launcher.time, "sleep"
            ), mock.patch("builtins.print"):
                pipeline_launcher.show_follow_view(project, "Live status", seconds=1)

            build_snapshot.assert_called_once_with(project, session)


if __name__ == "__main__":
    unittest.main()
