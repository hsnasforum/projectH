from __future__ import annotations

import tempfile
import time
import unittest
import json
from pathlib import Path
from unittest import mock

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
            profile_path = project / ".pipeline" / "config" / "agent_profile.json"
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(
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
                    }
                ),
                encoding="utf-8",
            )
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

    def test_watcher_runtime_hints_accepts_canonical_advisory_notify_marker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            log_dir = project / ".pipeline" / "logs" / "experimental"
            log_dir.mkdir(parents=True)
            profile_path = project / ".pipeline" / "config" / "agent_profile.json"
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "selected_agents": ["Claude", "Codex", "Gemini"],
                        "role_bindings": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
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
                    }
                ),
                encoding="utf-8",
            )
            log_dir.joinpath("watcher.log").write_text(
                "\n".join(
                    [
                        "2026-04-07T22:52:11 [INFO] watcher_core: notify_advisory_owner: reason=startup_turn_gemini",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch("pipeline_gui.agents.time.time", return_value=time.mktime((2026, 4, 7, 22, 52, 21, 0, 0, -1))):
                hints = watcher_runtime_hints(project)

        self.assertEqual(hints["Gemini"][0], "WORKING")


if __name__ == "__main__":
    unittest.main()
