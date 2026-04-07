from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import pipeline_gui.app as app_module
from pipeline_gui.agents import detect_agent_status, watcher_runtime_hints
from pipeline_gui.app import PipelineGUI


class PipelineGuiAgentsTest(unittest.TestCase):
    def test_detect_agent_status_ignores_old_working_scrollback(self) -> None:
        filler = "\n".join(f"line {i}" for i in range(30))
        pane_text = (
            "• Working (2m 10s • esc to interrupt)\n"
            f"{filler}\n"
            "latest /verify는 truthful했습니다.\n"
            "› Implement {feature}\n"
            "gpt-5.4 xhigh · 24% left\n"
        )

        status, note = detect_agent_status("Codex", pane_text)

        self.assertEqual(status, "READY")
        self.assertEqual(note, "")

    def test_detect_agent_status_keeps_recent_working_indicator(self) -> None:
        pane_text = (
            "latest /verify는 truthful했습니다.\n"
            "• Working (37s • esc to interrupt)\n"
            "› Implement {feature}\n"
            "gpt-5.4 xhigh · 24% left\n"
        )

        status, note = detect_agent_status("Codex", pane_text)

        self.assertEqual(status, "WORKING")
        self.assertEqual(note, "37s")

    def test_collect_all_agent_data_prefers_live_ready_over_stale_watcher_hint(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._session_name = "aip-projectH"
        gui.project = Path("/tmp/projectH")

        responses = [
            (0, "0|%65|0\n1|%66|0\n2|%67|0\n"),
            (0, "Claude output\n❯\n"),
            (0, "latest /verify는 truthful했습니다.\n› Implement {feature}\n"),
            (0, "Type your message\nworkspace\n"),
        ]

        def fake_run(*_args: object, **_kwargs: object) -> tuple[int, str]:
            return responses.pop(0)

        with mock.patch.object(app_module, "_run", side_effect=fake_run):
            with mock.patch.object(app_module, "watcher_runtime_hints", return_value={"Codex": ("WORKING", "verify 37s")}):
                agents, _pane_map = PipelineGUI._collect_all_agent_data(gui)

        status_by_label = {label: (status, note) for label, status, note, _quota in agents}
        self.assertEqual(status_by_label["Codex"], ("READY", ""))

    def test_watcher_runtime_hints_adds_phase_label(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            log_dir = project / ".pipeline" / "logs" / "experimental"
            log_dir.mkdir(parents=True)
            log_dir.joinpath("watcher.log").write_text(
                "\n".join(
                    [
                        "2026-04-07T22:52:11 [INFO] watcher_core: lease acquired: slot=slot_verify job=job round=1 pane=%66",
                        "2026-04-07T22:52:17 [INFO] watcher_core: state job VERIFY_PENDING → VERIFY_RUNNING (dispatched to slot_verify)",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch("pipeline_gui.agents.time.time", return_value=time.mktime((2026, 4, 7, 22, 52, 47, 0, 0, -1))):
                hints = watcher_runtime_hints(project)

        self.assertEqual(hints["Codex"][0], "WORKING")
        self.assertIn("verify", hints["Codex"][1])


if __name__ == "__main__":
    unittest.main()
