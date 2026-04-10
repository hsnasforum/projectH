from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from pipeline_gui.home_controller import HomeController


class PipelineGuiHomeControllerTest(unittest.TestCase):
    def test_get_cached_latest_md_reuses_recent_result(self) -> None:
        controller = HomeController(Path("/tmp/projectH"), "aip-projectH")
        directory = Path("/tmp/projectH/work")

        with mock.patch("pipeline_gui.home_controller.latest_md", return_value=("latest.md", 123.0)) as latest:
            first = controller.get_cached_latest_md(directory, refresh_interval=30.0)
            second = controller.get_cached_latest_md(directory, refresh_interval=30.0)

        self.assertEqual(first, ("latest.md", 123.0))
        self.assertEqual(second, ("latest.md", 123.0))
        latest.assert_called_once_with(directory)

    def test_get_cached_token_dashboard_starts_background_refresh_when_empty(self) -> None:
        controller = HomeController(Path("/tmp/projectH"), "aip-projectH")
        controller.start_token_dashboard_refresh = mock.Mock()

        dashboard = controller.get_cached_token_dashboard()

        self.assertIsNone(dashboard)
        controller.start_token_dashboard_refresh.assert_called_once_with(on_refresh=None)

    def test_build_snapshot_reads_log_once_and_assembles_verify_activity(self) -> None:
        controller = HomeController(Path("/tmp/projectH"), "aip-projectH")
        controller.collect_all_agent_data = mock.Mock(return_value=([], {}))
        controller.get_cached_token_usage = mock.Mock(return_value={})
        controller.get_cached_token_dashboard = mock.Mock(return_value={"cached": True})
        controller.get_cached_latest_md = mock.Mock(side_effect=[("work.md", 10.0), ("verify.md", 20.0)])

        with (
            mock.patch("pipeline_gui.home_controller.tmux_alive", return_value=False),
            mock.patch("pipeline_gui.home_controller.watcher_alive", return_value=(False, None)),
            mock.patch(
                "pipeline_gui.home_controller.watcher_log_snapshot",
                return_value={
                    "display_lines": ["tail"],
                    "summary_lines": ["2026-04-10T15:31:00 [INFO] watcher_core: initial turn: claude"],
                    "hint_lines": [],
                },
            ) as log_snapshot,
            mock.patch("pipeline_gui.home_controller.parse_control_slots", return_value={"active": None, "stale": []}),
            mock.patch("pipeline_gui.home_controller.current_verify_activity", return_value={"state": "VERIFY_RUNNING"}),
        ):
            snapshot = controller.build_snapshot(selected_agent="Claude")

        log_snapshot.assert_called_once_with(
            controller.project,
            display_lines=14,
            summary_lines=50,
            hint_lines=300,
        )
        controller.collect_all_agent_data.assert_called_once_with(selected_agent="Claude", hints={})
        self.assertEqual(snapshot.token_dashboard, {"cached": True})
        self.assertEqual(snapshot.log_lines, ["tail"])
        self.assertEqual(snapshot.verify_activity, {"state": "VERIFY_RUNNING"})


if __name__ == "__main__":
    unittest.main()
