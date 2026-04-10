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
            script = project / "start-pipeline.sh"
            script.write_text("#!/bin/bash\n", encoding="utf-8")
            expected_session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "resolve_project_active_profile",
                return_value={"controls": {"launch_allowed": True}},
            ), mock.patch.object(pipeline_launcher.subprocess, "Popen") as popen:
                message = pipeline_launcher.pipeline_start(project)

            self.assertEqual(message, "시작 요청됨")
            command = popen.call_args.args[0]
            self.assertIn("--session", command)
            self.assertEqual(command[command.index("--session") + 1], expected_session)

    def test_pipeline_stop_passes_project_aware_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-stop-") as tmp:
            project = Path(tmp).resolve()
            script = project / "stop-pipeline.sh"
            script.write_text("#!/bin/bash\n", encoding="utf-8")
            expected_session = _session_name_for(project)

            with mock.patch.object(pipeline_launcher.subprocess, "run") as run:
                message = pipeline_launcher.pipeline_stop(project)

            self.assertEqual(message, "중지 완료")
            command = run.call_args.args[0]
            self.assertEqual(command[-2:], ["--session", expected_session])

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

    def test_tmux_views_and_attach_use_same_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-tmux-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "_run",
                side_effect=[
                    (0, "0|%1|0"),
                    (0, "first line\nsecond line\n"),
                    (0, ""),
                ],
            ) as run, mock.patch.object(
                pipeline_launcher,
                "resolve_project_runtime_adapter",
                return_value={
                    "lane_configs": [
                        {"name": "Claude", "pane_index": 0, "enabled": True, "roles": ["implement"]},
                        {"name": "Codex", "pane_index": 1, "enabled": True, "roles": ["verify"]},
                        {"name": "Gemini", "pane_index": 2, "enabled": True, "roles": ["advisory"]},
                    ]
                },
            ), mock.patch.object(pipeline_launcher.os, "system") as system:
                pane_lines = pipeline_launcher.capture_agent_pane(session, 0, lines=10)
                snapshots = pipeline_launcher.pane_snapshots(project, session)
                pipeline_launcher.tmux_attach(session)

            self.assertEqual(pane_lines, ["first line", "second line"])
            self.assertEqual(snapshots, [])
            first_tmux_target = run.call_args_list[0].args[0]
            last_tmux_target = run.call_args_list[-1].args[0]
            self.assertEqual(first_tmux_target[3], f"{session}:0")
            self.assertEqual(last_tmux_target[3], f"{session}:0")
            system.assert_called_once_with(f"tmux attach -t {session}")

    def test_pane_snapshots_mark_disabled_lane_off_from_runtime_adapter(self) -> None:
        with tempfile.TemporaryDirectory(prefix="projH-disabled-") as tmp:
            project = Path(tmp).resolve()
            session = _session_name_for(project)

            with mock.patch.object(
                pipeline_launcher,
                "_run",
                return_value=(0, "0|%1|0\n1|%2|0\n2|%3|0\n"),
            ), mock.patch.object(
                pipeline_launcher,
                "resolve_project_runtime_adapter",
                return_value={
                    "lane_configs": [
                        {"name": "Claude", "pane_index": 0, "enabled": False, "roles": []},
                        {"name": "Codex", "pane_index": 1, "enabled": True, "roles": ["implement", "verify"]},
                        {"name": "Gemini", "pane_index": 2, "enabled": False, "roles": []},
                    ]
                },
            ):
                snapshots = pipeline_launcher.pane_snapshots(project, session)

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
