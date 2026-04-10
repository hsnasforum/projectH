from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import pipeline_gui.home_controller as home_module
from pipeline_gui.agents import detect_agent_status, watcher_runtime_hints


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

    def test_detect_agent_status_treats_recent_noodling_as_working(self) -> None:
        pane_text = (
            "핸드오프를 확인했습니다.\n"
            "+ Noodling...\n"
            "›\n"
            "⏵⏵ bypass permissions\n"
        )

        status, note = detect_agent_status("Claude", pane_text)

        self.assertEqual(status, "WORKING")
        self.assertEqual(note, "")

    def test_detect_agent_status_treats_recent_growing_as_working(self) -> None:
        pane_text = (
            "구현 경로를 다시 확인합니다.\n"
            "Growing...\n"
            "›\n"
            "⏵⏵ bypass permissions\n"
        )

        status, note = detect_agent_status("Claude", pane_text)

        self.assertEqual(status, "WORKING")
        self.assertEqual(note, "")

    def test_detect_agent_status_treats_recent_growing_with_tip_suffix_as_working(self) -> None:
        pane_text = (
            "구현 경로를 다시 확인합니다.\n"
            "* Growing... | Tip: /mobile to use Claude Code from the Claude app on your phone\n"
            "›\n"
            "⏵⏵ bypass permissions\n"
        )

        status, note = detect_agent_status("Claude", pane_text)

        self.assertEqual(status, "WORKING")
        self.assertEqual(note, "")

    def test_detect_agent_status_ignores_old_noodling_scrollback(self) -> None:
        filler = "\n".join(f"line {i}" for i in range(30))
        pane_text = (
            "+ Noodling...\n"
            f"{filler}\n"
            "검증: 1 passed (8.0s), git diff --check clean\n"
            "›\n"
            "⏵⏵ bypass permissions\n"
        )

        status, note = detect_agent_status("Claude", pane_text)

        self.assertEqual(status, "READY")
        self.assertEqual(note, "")

    def test_collect_all_agent_data_prefers_live_ready_over_stale_watcher_hint(self) -> None:
        controller = home_module.HomeController(Path("/tmp/projectH"), "aip-projectH")

        responses = [
            (0, "0|%65|0\n1|%66|0\n2|%67|0\n"),
            (0, "Claude output\n❯\n"),
            (0, "latest /verify는 truthful했습니다.\n› Implement {feature}\n"),
            (0, "Type your message\nworkspace\n"),
        ]

        def fake_run(*_args: object, **_kwargs: object) -> tuple[int, str]:
            return responses.pop(0)

        with mock.patch.object(home_module, "_run", side_effect=fake_run):
            with mock.patch.object(home_module, "watcher_runtime_hints", return_value={"Codex": ("WORKING", "verify 37s")}):
                agents, _pane_map = controller.collect_all_agent_data(selected_agent="Claude")

        status_by_label = {label: (status, note) for label, status, note, _quota in agents}
        self.assertEqual(status_by_label["Codex"], ("READY", ""))

    def test_collect_all_agent_data_upgrades_claude_ready_prompt_when_watcher_shows_live_work(self) -> None:
        controller = home_module.HomeController(Path("/tmp/projectH"), "aip-projectH")

        responses = [
            (0, "0|%65|0\n1|%66|0\n2|%67|0\n"),
            (0, "Claude output\n❯\n⏵⏵ bypass permissions\n"),
            (0, "latest /verify는 truthful했습니다.\n› Implement {feature}\n"),
            (0, "Type your message\nworkspace\n"),
        ]

        def fake_run(*_args: object, **_kwargs: object) -> tuple[int, str]:
            return responses.pop(0)

        with mock.patch.object(home_module, "_run", side_effect=fake_run):
            with mock.patch.object(home_module, "watcher_runtime_hints", return_value={"Claude": ("WORKING", "impl 12s")}):
                agents, _pane_map = controller.collect_all_agent_data(selected_agent="Claude")

        status_by_label = {label: (status, note) for label, status, note, _quota in agents}
        self.assertEqual(status_by_label["Claude"], ("WORKING", "impl 12s"))

    def test_collect_all_agent_data_reuses_cached_nonselected_pane_within_ttl(self) -> None:
        controller = home_module.HomeController(Path("/tmp/projectH"), "aip-projectH")
        controller._pane_capture_ttl_sec = 30.0

        first_responses = [
            (0, "0|%65|0\n1|%66|0\n2|%67|0\n"),
            (0, "Claude output\n❯\n"),
            (0, "Codex output\n› Implement {feature}\n"),
            (0, "Gemini output\nType your message\nworkspace\n"),
        ]
        second_responses = [
            (0, "0|%65|0\n1|%66|0\n2|%67|0\n"),
            (0, "Claude output\n❯\n"),
        ]

        with mock.patch.object(home_module, "_run", side_effect=first_responses.copy()):
            controller.collect_all_agent_data(selected_agent="Claude", hints={})

        with mock.patch.object(home_module, "_run", side_effect=second_responses.copy()) as run_mock:
            agents, pane_map = controller.collect_all_agent_data(selected_agent="Claude", hints={})

        status_by_label = {label: status for label, status, _note, _quota in agents}
        self.assertEqual(status_by_label["Codex"], "READY")
        self.assertIn("Codex output", pane_map["Codex"])
        capture_calls = [
            call.args[0]
            for call in run_mock.call_args_list
            if isinstance(call.args[0], list) and len(call.args[0]) >= 2 and call.args[0][1] == "capture-pane"
        ]
        self.assertEqual(len(capture_calls), 1)

    def test_collect_all_agent_data_refreshes_nonselected_working_hint_even_with_cache(self) -> None:
        controller = home_module.HomeController(Path("/tmp/projectH"), "aip-projectH")
        controller._pane_capture_cache = {
            "Codex": {
                "pane_id": "%66",
                "captured_at": time.time(),
                "text": "old codex output",
                "status": "READY",
                "note": "",
                "quota": "",
            }
        }
        controller._pane_capture_ttl_sec = 30.0

        responses = [
            (0, "0|%65|0\n1|%66|0\n2|%67|0\n"),
            (0, "Claude output\n❯\n"),
            (0, "Codex output\n• Working (37s • esc to interrupt)\n"),
            (0, "Gemini output\nType your message\nworkspace\n"),
        ]

        with mock.patch.object(home_module, "_run", side_effect=responses):
            agents, pane_map = controller.collect_all_agent_data(
                selected_agent="Claude",
                hints={"Codex": ("WORKING", "verify 37s")},
            )

        status_by_label = {label: (status, note) for label, status, note, _quota in agents}
        self.assertEqual(status_by_label["Codex"], ("WORKING", "verify 37s"))
        self.assertIn("Codex output", pane_map["Codex"])

    def test_detect_agent_status_treats_claude_sauteed_closeout_as_ready(self) -> None:
        pane_text = (
            "검증: 1 passed (8.0s), git diff --check clean\n"
            "남은 리스크: 없음.\n"
            "✻ Sautéed for 1m 29s\n"
            "❯\n"
            "⏵⏵ bypass permissions\n"
        )

        status, note = detect_agent_status("Claude", pane_text)

        self.assertEqual(status, "READY")
        self.assertEqual(note, "")

    def test_detect_agent_status_prefers_recent_claude_prompt_over_stale_busy_line(self) -> None:
        pane_text = (
            "• Working (54s • esc to interrupt)\n"
            "closeout note 작성 후 커밋합니다.\n"
            "✻ Sautéed for 7m 5s\n"
            "›\n"
            "›› bypass permissions\n"
        )

        status, note = detect_agent_status("Claude", pane_text)

        self.assertEqual(status, "READY")
        self.assertEqual(note, "")

    def test_detect_agent_status_treats_recent_claude_prompt_only_as_ready(self) -> None:
        pane_text = (
            "검증: 1 passed (8.0s), git diff --check clean\n"
            "✻ Sautéed for 1m 29s\n"
            "›\n"
        )

        status, note = detect_agent_status("Claude", pane_text)

        self.assertEqual(status, "READY")
        self.assertEqual(note, "")

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
