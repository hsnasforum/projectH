from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline_runtime.automation_health import STALE_CONTROL_CYCLE_THRESHOLD
from pipeline_runtime.operator_autonomy import OPERATOR_APPROVAL_COMPLETED_REASON
from pipeline_runtime.status_labels import operator_facing_reason_label
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


class FakeCursesScreen:
    def __init__(self, height: int = 40, width: int = 220) -> None:
        self.height = height
        self.width = width
        self.writes: list[str] = []

    def erase(self) -> None:
        self.writes.clear()

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def addstr(self, _row: int, _col: int, text: str, _attr: int = 0) -> None:
        self.writes.append(text)

    def refresh(self) -> None:
        return None


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
                snapshots = pipeline_launcher.pane_snapshots(project, runtime_view)
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
                            "control_file": ".pipeline/implement_handoff.md",
                            "control_seq": 154,
                            "reason": "handoff_already_completed",
                        },
                    }
                ],
            ):
                runtime_view = pipeline_launcher._runtime_view(project)
                snapshots = pipeline_launcher.pane_snapshots(project, runtime_view)
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

    def test_build_snapshot_surfaces_verify_receipt_pending_context(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-receipt-pending-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "_runtime_view",
                return_value={
                    "runtime_state": "DEGRADED",
                    "watcher_alive": True,
                    "watcher_pid": 2020,
                    "work_name": "2026-04-17-sqlite-browser.md",
                    "work_mtime": 0.0,
                    "verify_name": "2026-04-17-sqlite-browser-verification.md",
                    "verify_mtime": 0.0,
                    "control_file": "",
                    "control_seq": -1,
                    "control_status": "none",
                    "active_round": {
                        "state": "RECEIPT_PENDING",
                        "job_id": "job-verify-42",
                        "dispatch_id": "dispatch-verify-42",
                        "note": "waiting_receipt_close_after_task_done",
                        "completion_stage": "receipt_close_pending",
                    },
                    "last_receipt_id": "",
                    "degraded_reason": "post_accept_completion_stall",
                    "degraded_reasons": ["post_accept_completion_stall"],
                    "lanes": [{"name": "Codex", "state": "READY", "attachable": True, "note": "waiting_receipt_close_after_task_done"}],
                    "event_lines": ["completion_stall_detected Codex task_done_missing"],
                    "events": [],
                },
            ):
                lines = pipeline_launcher.build_snapshot(project, session)

            self.assertTrue(any("Round  : RECEIPT_PENDING / job-verify-42 / dispatch-verify-42" in line for line in lines))
            self.assertTrue(any("Round note: waiting_receipt_close_after_task_done / receipt_close_pending" in line for line in lines))
            self.assertTrue(any("Receipt: pending close" in line for line in lines))

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
            self.assertEqual(runtime_view["automation_health"], "attention")
            self.assertEqual(runtime_view["automation_reason_code"], "dispatch_stall")
            self.assertEqual(runtime_view["automation_incident_family"], "dispatch_stall")
            self.assertEqual(runtime_view["automation_next_action"], "verify_followup")
            self.assertTrue(
                any(
                    "dispatch_stall_detected Codex degraded waiting_task_accept_after_dispatch" in line
                    for line in runtime_view["event_lines"]
                )
            )

    def test_runtime_view_surfaces_completion_stall_event_lines(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-completion-stall-") as tmp:
            project = Path(tmp).resolve()

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={
                    "runtime_state": "DEGRADED",
                    "degraded_reason": "post_accept_completion_stall",
                    "degraded_reasons": ["post_accept_completion_stall"],
                    "lanes": [
                        {"name": "Codex", "state": "READY", "note": "waiting_task_done_after_accept"},
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
                        "event_type": "completion_stall_detected",
                        "payload": {
                            "lane": "Codex",
                            "action": "degraded",
                            "reason": "waiting_task_done_after_accept",
                        },
                    }
                ],
            ):
                runtime_view = pipeline_launcher._runtime_view(project)

            self.assertEqual(runtime_view["runtime_state"], "DEGRADED")
            self.assertEqual(runtime_view["degraded_reason"], "post_accept_completion_stall")
            self.assertEqual(runtime_view["automation_health"], "attention")
            self.assertEqual(runtime_view["automation_reason_code"], "post_accept_completion_stall")
            self.assertEqual(runtime_view["automation_incident_family"], "completion_stall")
            self.assertEqual(runtime_view["automation_next_action"], "verify_followup")
            self.assertTrue(
                any(
                    "completion_stall_detected Codex degraded waiting_task_done_after_accept" in line
                    for line in runtime_view["event_lines"]
                )
            )

    def test_runtime_view_surfaces_automation_incident_event_lines(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-automation-incident-") as tmp:
            project = Path(tmp).resolve()

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={
                    "runtime_state": "DEGRADED",
                    "degraded_reason": "dispatch_stall",
                    "degraded_reasons": ["dispatch_stall"],
                    "lanes": [],
                    "watcher": {"alive": True, "pid": 1234},
                    "control": {"active_control_status": "implement"},
                    "autonomy": {"mode": "normal"},
                },
            ), mock.patch.object(
                pipeline_launcher,
                "read_runtime_event_tail",
                return_value=[
                    {
                        "event_type": "automation_incident",
                        "payload": {
                            "automation_health": "attention",
                            "reason_code": "dispatch_stall",
                            "incident_family": "dispatch_stall",
                            "next_action": "verify_followup",
                        },
                    }
                ],
            ):
                runtime_view = pipeline_launcher._runtime_view(project)

            self.assertTrue(
                any(
                    "automation_incident attention dispatch_stall verify_followup dispatch_stall" in line
                    for line in runtime_view["event_lines"]
                )
            )

    def test_runtime_view_surfaces_lane_input_deferred_event_lines(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-lane-input-deferred-") as tmp:
            project = Path(tmp).resolve()

            with mock.patch.object(
                pipeline_launcher,
                "read_runtime_status",
                return_value={
                    "runtime_state": "RUNNING",
                    "lanes": [{"name": "Codex", "state": "READY", "note": "prompt_visible"}],
                    "watcher": {"alive": True, "pid": 1234},
                    "control": {"active_control_status": "advice_ready"},
                    "autonomy": {"mode": "normal"},
                },
            ), mock.patch.object(
                pipeline_launcher,
                "read_runtime_event_tail",
                return_value=[
                    {
                        "event_type": "lane_input_deferred",
                        "payload": {
                            "lane": "Codex",
                            "reason": "advisory_advice_updated",
                            "defer_reason": "lane_busy",
                            "control_file": "advisory_advice.md",
                            "control_seq": 265,
                        },
                    }
                ],
            ):
                runtime_view = pipeline_launcher._runtime_view(project)

            self.assertTrue(
                any(
                    "lane_input_deferred Codex advisory_advice_updated lane_busy seq=265 advisory_advice.md" in line
                    for line in runtime_view["event_lines"]
                )
            )

    def test_focused_lane_details_include_lane_input_deferred_event(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-lane-detail-deferred-") as tmp:
            project = Path(tmp).resolve()

            runtime_view = {
                "lanes": [
                    {
                        "name": "Codex",
                        "state": "READY",
                        "attachable": True,
                        "pid": 222,
                        "note": "prompt_visible",
                        "last_event_at": "2026-04-17T08:17:39Z",
                    }
                ],
                "events": [
                    {
                        "event_type": "lane_input_deferred",
                        "payload": {
                            "lane": "Codex",
                            "reason": "advisory_advice_updated",
                            "defer_reason": "lane_busy",
                        },
                    }
                ],
            }

            with mock.patch.object(
                pipeline_launcher,
                "runtime_lane_name_map",
                return_value={0: "Codex"},
            ), mock.patch.object(
                pipeline_launcher,
                "resolve_project_runtime_adapter",
                return_value={"role_owners": {"implement": "Claude"}},
            ):
                details = pipeline_launcher.focused_lane_details(project, runtime_view, 0)

            self.assertIn("name=Codex", details)
            self.assertTrue(any("lane_input_deferred advisory_advice_updated" in line for line in details))

    def test_pane_snapshots_include_verify_round_context_for_codex(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-pane-round-context-") as tmp:
            project = Path(tmp).resolve()
            runtime_view = {
                "lanes": [
                    {
                        "name": "Codex",
                        "state": "READY",
                        "attachable": True,
                        "pid": 222,
                        "note": "waiting_receipt_close_after_task_done",
                        "progress_phase": "receipt_close_pending",
                        "last_event_at": "2026-04-17T08:17:39Z",
                    }
                ],
                "active_round": {
                    "state": "RECEIPT_PENDING",
                    "job_id": "job-verify-77",
                    "dispatch_id": "dispatch-verify-77",
                },
            }

            with mock.patch.object(
                pipeline_launcher,
                "resolve_project_runtime_adapter",
                return_value={"role_owners": {"verify": "Codex"}},
            ):
                snapshots = pipeline_launcher.pane_snapshots(project, runtime_view)

            self.assertEqual(len(snapshots), 1)
            self.assertEqual(snapshots[0].status_note, "receipt 마감 대기")
            self.assertIn("progress=receipt_close_pending", snapshots[0].detail)
            self.assertIn("round=RECEIPT_PENDING", snapshots[0].detail)
            self.assertIn("job=job-verify-77", snapshots[0].detail)
            self.assertIn("dispatch=dispatch-verify-77", snapshots[0].detail)

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
                    "automation_health": "attention",
                    "automation_reason_code": "slice_ambiguity",
                    "automation_incident_family": "slice_ambiguity",
                    "automation_next_action": "advisory_followup",
                    "active_round": {"state": "IDLE"},
                    "lanes": [],
                    "event_lines": [],
                    "events": [],
                },
            )

        self.assertTrue(any("Autonomy: triage / slice_ambiguity" in line for line in lines))
        self.assertTrue(
            any(
                "Automation: 주의 / slice_ambiguity / advisory_followup / family=slice_ambiguity" in line
                for line in lines
            )
        )

    def test_build_snapshot_localizes_operator_approval_completed_reason(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-operator-approval-completed-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)
            approval_label = operator_facing_reason_label(OPERATOR_APPROVAL_COMPLETED_REASON)

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
                    "autonomy_mode": "recovery",
                    "autonomy_reason": OPERATOR_APPROVAL_COMPLETED_REASON,
                    "automation_health": "recovering",
                    "automation_reason_code": OPERATOR_APPROVAL_COMPLETED_REASON,
                    "automation_incident_family": OPERATOR_APPROVAL_COMPLETED_REASON,
                    "automation_next_action": "verify_followup",
                    "active_round": {"state": "IDLE"},
                    "progress": {"phase": OPERATOR_APPROVAL_COMPLETED_REASON, "lane": "Codex"},
                    "lanes": [],
                    "event_lines": [f"{approval_label} seq=44 main"],
                    "events": [],
                },
            )

        self.assertTrue(any(f"Automation: 복구 중 / {approval_label}" in line for line in lines))
        self.assertTrue(
            any(
                f"Automation detail: reason={OPERATOR_APPROVAL_COMPLETED_REASON} / action=verify_followup / family={OPERATOR_APPROVAL_COMPLETED_REASON}"
                in line
                for line in lines
            )
        )
        self.assertTrue(
            any(
                f"Progress: {approval_label} / phase={OPERATOR_APPROVAL_COMPLETED_REASON} / lane=Codex"
                in line
                for line in lines
            )
        )
        self.assertTrue(any(f"{approval_label} seq=44 main" in line for line in lines))

    def test_build_snapshot_surfaces_stale_control_detail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-stale-control-detail-") as tmp:
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
                    "control_file": ".pipeline/implement_handoff.md",
                    "control_seq": 697,
                    "control_status": "implement",
                    "autonomy_mode": "normal",
                    "autonomy_reason": "",
                    "automation_health": "ok",
                    "automation_reason_code": "",
                    "automation_incident_family": "",
                    "automation_next_action": "continue",
                    "automation_health_detail": f"제어 슬롯 고착 감지됨 ({STALE_CONTROL_CYCLE_THRESHOLD} 사이클)",
                    "control_age_cycles": STALE_CONTROL_CYCLE_THRESHOLD,
                    "stale_control_seq": True,
                    "stale_control_cycle_threshold": STALE_CONTROL_CYCLE_THRESHOLD,
                    "active_round": {"state": "IDLE"},
                    "lanes": [],
                    "event_lines": [],
                    "events": [],
                },
            )

        self.assertTrue(any("제어 슬롯 고착 감지됨" in line for line in lines))
        self.assertTrue(any(f"control_age_cycles={STALE_CONTROL_CYCLE_THRESHOLD}" in line for line in lines))

    def test_build_snapshot_surfaces_stale_advisory_pending_detail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-stale-advisory-detail-") as tmp:
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
                    "control_file": ".pipeline/implement_handoff.md",
                    "control_seq": 700,
                    "control_status": "implement",
                    "autonomy_mode": "normal",
                    "autonomy_reason": "",
                    "automation_health": "ok",
                    "automation_reason_code": "",
                    "automation_incident_family": "",
                    "automation_next_action": "continue",
                    "automation_health_detail": f"제어 슬롯 고착 감지됨 ({STALE_CONTROL_CYCLE_THRESHOLD} 사이클)",
                    "control_age_cycles": STALE_CONTROL_CYCLE_THRESHOLD,
                    "stale_control_seq": True,
                    "stale_control_cycle_threshold": STALE_CONTROL_CYCLE_THRESHOLD,
                    "stale_advisory_pending": True,
                    "active_round": {"state": "IDLE"},
                    "lanes": [],
                    "event_lines": [],
                    "events": [],
                },
            )

        self.assertTrue(any("어드바이저리 요청 대기 중" in line for line in lines))
        self.assertTrue(any("stale_advisory_pending=true" in line for line in lines))

    def test_curses_draw_surfaces_same_automation_detail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-curses-stale-detail-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)
            screen = FakeCursesScreen()

            with (
                mock.patch.object(pipeline_launcher.curses, "init_pair"),
                mock.patch.object(pipeline_launcher.curses, "color_pair", side_effect=lambda value: value),
            ):
                pipeline_launcher.draw(
                    screen,
                    project,
                    session,
                    "",
                    runtime_view={
                        "runtime_state": "RUNNING",
                        "watcher_alive": True,
                        "watcher_pid": 2020,
                        "work_name": "—",
                        "work_mtime": 0.0,
                        "verify_name": "—",
                        "verify_mtime": 0.0,
                        "control_file": ".pipeline/implement_handoff.md",
                        "control_seq": 700,
                        "control_status": "implement",
                        "autonomy_mode": "normal",
                        "autonomy_reason": "",
                        "automation_health": "attention",
                        "automation_reason_code": "stale_control_advisory",
                        "automation_incident_family": "stale_control_advisory",
                        "automation_next_action": "advisory_followup",
                        "automation_health_detail": f"제어 슬롯 고착 감지됨 ({STALE_CONTROL_CYCLE_THRESHOLD} 사이클)",
                        "control_age_cycles": STALE_CONTROL_CYCLE_THRESHOLD,
                        "stale_control_seq": True,
                        "stale_control_cycle_threshold": STALE_CONTROL_CYCLE_THRESHOLD,
                        "stale_advisory_pending": True,
                        "active_round": {"state": "IDLE"},
                        "lanes": [],
                        "event_lines": [],
                        "events": [],
                    },
                )

        rendered = "\n".join(screen.writes)
        self.assertIn("Auto detail:", rendered)
        self.assertIn("stale_advisory_pending=true", rendered)

    def test_build_snapshot_surfaces_role_owners_from_runtime_adapter(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-role-owners-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "resolve_project_runtime_adapter",
                return_value={"role_owners": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"}},
            ):
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
                        "active_round": {"state": "IDLE"},
                        "lanes": [],
                        "event_lines": [],
                        "events": [],
                    },
                )

        self.assertTrue(any("Role owners : implement=Codex / verify=Claude / advisory=Gemini" in line for line in lines))

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
                snapshots = pipeline_launcher.pane_snapshots(project, runtime_view)

            self.assertEqual(
                [(snap.label, snap.status) for snap in snapshots],
                [("Claude", "OFF"), ("Codex", "BOOTING"), ("Gemini", "OFF")],
            )

    def test_pane_snapshots_include_role_context_for_swapped_verify_owner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-swapped-verify-") as tmp:
            project = Path(tmp).resolve()
            runtime_view = {
                "lanes": [
                    {
                        "name": "Claude",
                        "state": "READY",
                        "attachable": True,
                        "pid": 111,
                        "note": "waiting_receipt_close_after_task_done",
                        "last_event_at": "2026-04-17T08:17:39Z",
                    }
                ],
                "active_round": {
                    "state": "RECEIPT_PENDING",
                    "job_id": "job-verify-88",
                    "dispatch_id": "dispatch-verify-88",
                },
            }

            with mock.patch.object(
                pipeline_launcher,
                "resolve_project_runtime_adapter",
                return_value={"role_owners": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"}},
            ):
                snapshots = pipeline_launcher.pane_snapshots(project, runtime_view)

        self.assertEqual(len(snapshots), 1)
        self.assertIn("role=verify", snapshots[0].detail)
        self.assertIn("round=RECEIPT_PENDING", snapshots[0].detail)
        self.assertIn("job=job-verify-88", snapshots[0].detail)

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
