import tempfile
import unittest
from pathlib import Path
from unittest import mock

import watcher_core


class LiveSessionEscalationTest(unittest.TestCase):
    def test_extract_live_session_escalation_detects_expected_reasons(self) -> None:
        text = """
이 세션에서 이미 28건의 동일 family smoke를 수행했고 context window가 매우 소진된 상태입니다.
새 세션에서 이어가시는 것을 강하게 권고드립니다.
그래도 진행을 원하시면 handoff를 확인하겠지만, 진행할까요?
"""
        signal = watcher_core._extract_live_session_escalation(text)

        self.assertIsNotNone(signal)
        self.assertEqual(
            signal["reasons"],
            ["context_exhaustion", "session_rollover", "continue_vs_switch"],
        )
        self.assertTrue(signal["fingerprint"])

    def test_extract_live_session_escalation_detects_additional_phrase_variants(self) -> None:
        text = """
The context exhausted warning says the window is nearly full.
Please start a new session for the next slice.
Should I continue here or handoff and continue in a fresh session?
"""
        signal = watcher_core._extract_live_session_escalation(text)

        self.assertIsNotNone(signal)
        self.assertEqual(
            signal["reasons"],
            ["context_exhaustion", "session_rollover", "continue_vs_switch"],
        )

    def test_extract_live_session_escalation_ignores_old_scrollback_matches(self) -> None:
        old_lines = [
            "context window is nearly full",
            "please start a new session",
            "should i continue here?",
        ]
        recent_lines = [f"recent output line {i}" for i in range(20)]
        text = "\n".join(old_lines + recent_lines)

        signal = watcher_core._extract_live_session_escalation(text)

        self.assertIsNone(signal)

    def test_extract_live_session_escalation_detects_semantic_fallback_combo(self) -> None:
        text = """
최근 답변이 너무 길어져서 이 대화는 거의 가득 찬 것 같습니다.
다음 세션에서 이어가는 편이 안전하겠습니다.
여기서 계속 진행할지, handoff로 넘길지 정할까요?
"""

        signal = watcher_core._extract_live_session_escalation(text)

        self.assertIsNotNone(signal)
        self.assertEqual(
            signal["reasons"],
            ["context_exhaustion", "session_rollover", "continue_vs_switch"],
        )

    def test_waiting_for_claude_writes_noncanonical_session_arbitration_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._waiting_for_claude = True
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
>
""",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                core._poll()

            draft_path = base_dir / "session_arbitration_draft.md"
            self.assertTrue(draft_path.exists())
            content = draft_path.read_text()
            self.assertIn("STATUS: draft_only", content)
            self.assertIn("non-canonical draft", content)
            self.assertIn(".pipeline/claude_handoff.md", content)
            self.assertFalse((base_dir / "gemini_request.md").exists())

    def test_waiting_for_claude_skips_draft_until_all_three_panes_are_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._waiting_for_claude = True
            core._work_baseline_snapshot = {}

            busy_snapshots = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
>
""",
                "codex-pane": "• Working (36s • esc to interrupt)\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: busy_snapshots[target]):
                core._poll()

            self.assertFalse((base_dir / "session_arbitration_draft.md").exists())

    def test_waiting_for_claude_allows_settled_escalation_even_if_claude_prompt_lags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "session_arbitration_settle_sec": 3.0,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._waiting_for_claude = True
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
""",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                core._poll()
                self.assertFalse((base_dir / "session_arbitration_draft.md").exists())
                fingerprint = watcher_core.hashlib.sha1(
                    pane_texts["claude-pane"].encode("utf-8")
                ).hexdigest()
                core._session_arbitration_snapshot_fingerprints["claude"] = fingerprint
                core._session_arbitration_snapshot_changed_at["claude"] = 0.0
                with mock.patch("watcher_core.time.time", return_value=10.0):
                    core._poll()

            draft_path = base_dir / "session_arbitration_draft.md"
            self.assertTrue(draft_path.exists())

    def test_waiting_for_claude_clears_draft_when_claude_activity_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._waiting_for_claude = True
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
>
""",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch.object(core, "_get_work_tree_snapshot", side_effect=[{}, {"work.md": "changed"}]):
                    core._poll()
                    self.assertTrue((base_dir / "session_arbitration_draft.md").exists())
                    core._poll()

            draft_path = base_dir / "session_arbitration_draft.md"
            self.assertFalse(draft_path.exists())
            self.assertFalse(core._waiting_for_claude)

    def test_same_fingerprint_is_suppressed_during_cooldown_after_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "session_arbitration_cooldown_sec": 300.0,
                }
            )
            signal = {
                "reasons": ["context_exhaustion"],
                "excerpt_lines": ["context window is full"],
                "fingerprint": "same-fingerprint",
            }

            with mock.patch("watcher_core.time.time", return_value=100.0):
                self.assertTrue(core._write_session_arbitration_draft(signal))
                self.assertTrue(core.session_arbitration_draft_path.exists())
                core._clear_session_arbitration_draft("test_resolved")
                self.assertFalse(core.session_arbitration_draft_path.exists())

            with mock.patch("watcher_core.time.time", return_value=200.0):
                self.assertFalse(core._write_session_arbitration_draft(signal))
                self.assertFalse(core.session_arbitration_draft_path.exists())

            with mock.patch("watcher_core.time.time", return_value=450.0):
                self.assertTrue(core._write_session_arbitration_draft(signal))
                self.assertTrue(core.session_arbitration_draft_path.exists())

    def test_waiting_for_claude_skips_draft_when_any_lane_is_dead(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._waiting_for_claude = True
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
>
""",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            def fake_dead(target: str) -> bool:
                return target == "codex-pane"

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core._is_pane_dead", side_effect=fake_dead):
                    core._poll()

            self.assertFalse((base_dir / "session_arbitration_draft.md").exists())


if __name__ == "__main__":
    unittest.main()
