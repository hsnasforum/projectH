import os
import tempfile
import time
import unittest
import json
import itertools
from pathlib import Path
from unittest import mock

import watcher_core
from pipeline_runtime.wrapper_events import append_wrapper_event


def _write_active_profile(root: Path, payload: dict | None = None) -> None:
    active_path = root / ".pipeline" / "config" / "agent_profile.json"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(
        json.dumps(
            payload
            or {
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


def _write_work_note(path: Path, changed_files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    changed_lines = "\n".join(f"- `{changed}`" for changed in changed_files) or "- 없음"
    path.write_text(
        "\n".join(
            [
                f"# {path.stem}",
                "",
                "## 변경 파일",
                changed_lines,
                "",
                "## 사용 skill",
                "- 없음",
                "",
                "## 변경 이유",
                "- 테스트",
                "",
                "## 핵심 변경",
                "- 테스트",
                "",
                "## 검증",
                "- 없음",
                "",
                "## 남은 리스크",
                "- 없음",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_verify_note(path: Path, changed_files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    changed_lines = "\n".join(f"- `{changed}`" for changed in changed_files) or "- 없음"
    path.write_text(
        "\n".join(
            [
                f"# {path.stem}",
                "",
                "## 변경 파일",
                changed_lines,
                "",
                "## 사용 skill",
                "- 없음",
                "",
                "## 변경 이유",
                "- 테스트",
                "",
                "## 핵심 변경",
                "- 테스트",
                "",
                "## 검증",
                "- 없음",
                "",
                "## 남은 리스크",
                "- 없음",
                "",
            ]
        ),
        encoding="utf-8",
    )


class WorkNoteFilteringTest(unittest.TestCase):
    def test_latest_work_path_skips_metadata_only_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            real_note = watch_dir / "4" / "9" / "2026-04-09-real-implementation.md"
            _write_work_note(real_note, ["docs/PRODUCT_PROPOSAL.md"])
            meta_note = watch_dir / "4" / "9" / "2026-04-09-claude-handoff-task-list-review.md"
            _write_work_note(meta_note, ["work/4/9/2026-04-09-claude-handoff-task-list-review.md"])
            os.utime(meta_note, (real_note.stat().st_atime + 5, real_note.stat().st_mtime + 5))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertEqual(core._get_latest_work_path(), real_note)
            self.assertTrue(core._is_metadata_only_work_note(meta_note))
            self.assertFalse(core._is_dispatchable_work_note(meta_note))

    def test_work_snapshot_ignores_metadata_only_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            meta_note = watch_dir / "4" / "9" / "2026-04-09-claude-handoff-task-list-review.md"
            _write_work_note(meta_note, ["work/4/9/2026-04-09-claude-handoff-task-list-review.md"])

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertEqual(core._get_work_tree_snapshot(), {})
            self.assertFalse(core._latest_work_needs_verify())

    def test_poll_does_not_create_verify_job_for_metadata_only_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\nCONTROL_SEQ: 8\n", encoding="utf-8")

            meta_note = watch_dir / "4" / "9" / "2026-04-09-claude-handoff-task-list-review.md"
            _write_work_note(meta_note, ["work/4/9/2026-04-09-claude-handoff-task-list-review.md"])

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
            core._transition_turn(watcher_core.WatcherTurnState.IDLE, "test_setup")

            with mock.patch.object(core.sm, "step", wraps=core.sm.step) as advance:
                core._poll()

            job_jsons = [
                p for p in (base_dir / "state").glob("*.json")
                if p.name != "turn_state.json"
            ]
            self.assertFalse(any(job_jsons))
            self.assertEqual(advance.call_count, 0)


class PanePromptDetectionTest(unittest.TestCase):
    def test_gemini_text_prompt_counts_as_input_ready(self) -> None:
        text = "\n".join(
            [
                "Gemini CLI",
                "Type your message",
                "workspace",
            ]
        )

        self.assertTrue(watcher_core._pane_text_has_input_cursor(text))

    def test_gemini_current_cli_prompt_counts_as_input_ready(self) -> None:
        text = "\n".join(
            [
                "Gemini CLI v0.38.1",
                "YOLO Ctrl+Y",
                "*   Type your message or @path/to/file",
                "workspace              sandbox",
            ]
        )

        self.assertTrue(watcher_core._pane_text_has_input_cursor(text))

    def test_non_prompt_text_does_not_count_as_input_ready(self) -> None:
        text = "\n".join(
            [
                "Recommendation:",
                "- proceed with the bounded implement handoff",
            ]
        )

        self.assertFalse(watcher_core._pane_text_has_input_cursor(text))


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
            _write_active_profile(root)
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
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
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
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]), \
                 mock.patch("watcher_core._is_pane_dead", return_value=False):
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
            _write_active_profile(root)
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
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
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
            _write_active_profile(root)
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
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
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
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]), \
                 mock.patch("watcher_core._is_pane_dead", return_value=False):
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
            _write_active_profile(root)
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
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
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
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]), \
                 mock.patch("watcher_core._is_pane_dead", return_value=False):
                with mock.patch.object(core, "_get_work_tree_snapshot", side_effect=[{}, {}, {"work.md": "changed"}, {"work.md": "changed"}]):
                    core._poll()
                    self.assertTrue((base_dir / "session_arbitration_draft.md").exists())
                    core._poll()

            draft_path = base_dir / "session_arbitration_draft.md"
            self.assertFalse(draft_path.exists())
            self.assertNotEqual(core._current_turn_state, watcher_core.WatcherTurnState.CLAUDE_ACTIVE)

    def test_same_fingerprint_is_suppressed_during_cooldown_after_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

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
            _write_active_profile(root)
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
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
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


class ClaudeImplementBlockedTest(unittest.TestCase):
    def test_extract_implement_blocked_tolerates_wrapped_handoff_fields(self) -> None:
        signal = watcher_core._extract_claude_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: smoke_handoff_blocked",
                    "REQUEST: verify_triage",
                    "HANDOFF: .pipeline/live-blocked-smoke-j3",
                    "YWbK/claude_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "fedcba0987654321",
                    "BLOCK_ID: abcdef1234567890fedc",
                    "ba0987654321:smoke_handoff_blocked",
                    ">",
                ]
            ),
            active_handoff_path=".pipeline/live-blocked-smoke-j3YWbK/claude_handoff.md",
            active_handoff_sha="abcdef1234567890fedcba0987654321",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason"], "smoke_handoff_blocked")
        self.assertEqual(signal["fingerprint"], "abcdef1234567890fedcba0987654321:smoke_handoff_blocked")

    def test_extract_implement_blocked_tolerates_wrapped_status_and_reason(self) -> None:
        signal = watcher_core._extract_claude_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS:",
                    "implement_blocked",
                    "BLOCK_REASON:",
                    "renderResult follow-up",
                    "correctly drops review-outcome",
                    "REQUEST: verify_triage",
                    "HANDOFF: .pipeline/claud",
                    "e_handoff.md",
                    "HANDOFF_SHA:",
                    "abcdef1234567890",
                    "fedcba0987654321",
                    "BLOCK_ID:",
                    "abcdef1234567890",
                    "fedcba0987654321:renderResult-follow-up",
                    "분석 결과:",
                    ">",
                ]
            ),
            active_handoff_path=".pipeline/claude_handoff.md",
            active_handoff_sha="abcdef1234567890fedcba0987654321",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason"], "renderresult follow-up correctly drops review-outcome")
        self.assertEqual(signal["fingerprint"], "abcdef1234567890fedcba0987654321:renderResult-follow-up")

    def test_extract_implement_blocked_prefers_structured_reason_code_and_escalation_class(self) -> None:
        signal = watcher_core._extract_claude_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: context window exhausted after diff review",
                    "BLOCK_REASON_CODE: context_exhaustion",
                    "REQUEST: codex_triage",
                    "ESCALATION_CLASS: codex_triage",
                    "HANDOFF: .pipeline/claude_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "BLOCK_ID: block-structured-001",
                ]
            ),
            active_handoff_path=".pipeline/claude_handoff.md",
            active_handoff_sha="abcdef1234567890",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason_code"], "context_exhaustion")
        self.assertEqual(signal["escalation_class"], "codex_triage")
        self.assertEqual(signal["request"], "codex_triage")

    def test_extract_implement_blocked_ignores_prompt_template_example(self) -> None:
        signal = watcher_core._extract_claude_implement_blocked_signal(
            "\n".join(
                [
                    "- if the handoff is blocked or not actionable, emit the exact sentinel below and stop",
                    "BLOCKED_SENTINEL:",
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: <short_reason>",
                    "REQUEST: verify_triage",
                    "HANDOFF: .pipeline/claude_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "BLOCK_ID: abcdef1234567890:<short_reason>",
                    ">",
                ]
            ),
            active_handoff_path=".pipeline/claude_handoff.md",
            active_handoff_sha="abcdef1234567890",
        )

        self.assertIsNone(signal)

    def test_waiting_for_claude_routes_explicit_implement_blocked_to_codex(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n")

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
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            handoff_sha = watcher_core.compute_file_sha256(handoff_path)
            pane_texts = {
                "claude-pane": (
                    "STATUS: implement_blocked\n"
                    "BLOCK_REASON: handoff_not_actionable\n"
                    "BLOCK_REASON_CODE: codex_triage_only\n"
                    "REQUEST: codex_triage\n"
                    "ESCALATION_CLASS: codex_triage\n"
                    "HANDOFF: .pipeline/claude_handoff.md\n"
                    f"HANDOFF_SHA: {handoff_sha}\n"
                    "BLOCK_ID: block-001\n"
                ),
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    core._poll()

            send.assert_called_once()
            args, kwargs = send.call_args
            self.assertEqual(args[0], "codex-pane")
            self.assertIn("ROLE: verify_triage", args[1])
            self.assertIn("OWNER: Codex", args[1])
            self.assertIn("BLOCK_REASON: handoff_not_actionable", args[1])
            self.assertIn("BLOCK_REASON_CODE: codex_triage_only", args[1])
            self.assertIn("ESCALATION_CLASS: codex_triage", args[1])
            self.assertIn("BLOCK_ID: block-001", args[1])
            self.assertEqual(kwargs.get("pane_type"), "codex")
            self.assertEqual(core._last_claude_blocked_fingerprint, "block-001")

    def test_same_block_id_is_not_redispatched_while_outstanding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n")

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
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            handoff_sha = watcher_core.compute_file_sha256(handoff_path)
            pane_texts = {
                "claude-pane": (
                    "STATUS: implement_blocked\n"
                    "BLOCK_REASON: handoff_not_actionable\n"
                    "REQUEST: codex_triage\n"
                    "HANDOFF: .pipeline/claude_handoff.md\n"
                    f"HANDOFF_SHA: {handoff_sha}\n"
                    "BLOCK_ID: block-dedupe\n"
                ),
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    core._poll()
                    core._poll()

            self.assertEqual(send.call_count, 1)
            self.assertEqual(core._last_claude_blocked_fingerprint, "block-dedupe")

    def test_forbidden_operator_menu_soft_blocks_after_settle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
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
                    "implement_blocked_settle_sec": 3.0,
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": "진행 전에 다음 중 하나를 선택해 주세요.\n1. operator에게 묻기\n2. 나중에 진행\n> ",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    with mock.patch("watcher_core.time.time", return_value=10.0):
                        core._poll()
                    self.assertEqual(send.call_count, 0)
                    with mock.patch("watcher_core.time.time", return_value=20.0):
                        core._poll()

            self.assertEqual(send.call_count, 1)
            args, _ = send.call_args
            self.assertIn("BLOCK_REASON: forbidden_operator_menu", args[1])

    def test_already_completed_handoff_soft_blocks_after_settle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n", encoding="utf-8")

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
                    "implement_blocked_settle_sec": 3.0,
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": (
                    "No uncommitted changes in either file. Let me check if the latest commit already addressed these.\n"
                    "The work described in the handoff was already completed in commits 2edf687 and 43e6099.\n"
                    "이 슬라이스에 추가로 변경할 파일이 없으므로 구현 작업 없이 완료입니다.\n> "
                ),
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    with mock.patch("watcher_core.time.time", return_value=10.0):
                        core._poll()
                    self.assertEqual(send.call_count, 0)
                    with mock.patch("watcher_core.time.time", return_value=20.0):
                        core._poll()
                    with mock.patch("watcher_core.time.time", return_value=21.0):
                        core._poll()

            self.assertEqual(send.call_count, 1)
            args, _ = send.call_args
            self.assertIn("BLOCK_REASON: handoff_already_completed", args[1])
            raw_events = [
                json.loads(line)
                for line in (core.events_dir / "raw.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            notify = [event for event in raw_events if event.get("event") == "codex_blocked_triage_notify"]
            self.assertEqual(len(notify), 1)
            self.assertTrue(str(notify[0].get("handoff_sha") or ""))

    def test_newer_handoff_remains_active_when_older_operator_request_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            operator_path = base_dir / "operator_request.md"
            handoff_path = base_dir / "claude_handoff.md"
            operator_path.write_text("STATUS: needs_operator\n")
            handoff_path.write_text("STATUS: implement\n")
            os.utime(operator_path, (100.0, 100.0))
            os.utime(handoff_path, (200.0, 200.0))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, handoff_path)
            self.assertEqual(core._get_pending_operator_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "claude")

    def test_higher_control_seq_beats_newer_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            request_path = base_dir / "gemini_request.md"
            handoff_path = base_dir / "claude_handoff.md"
            request_path.write_text("STATUS: request_open\nCONTROL_SEQ: 8\n")
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 7\n")
            os.utime(request_path, (100.0, 100.0))
            os.utime(handoff_path, (200.0, 200.0))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, request_path)
            self.assertEqual(active.control_seq, 8)
            self.assertEqual(core._resolve_turn(), "gemini")

    def test_stale_gemini_slots_do_not_block_newer_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            request_path = base_dir / "gemini_request.md"
            advice_path = base_dir / "gemini_advice.md"
            handoff_path = base_dir / "claude_handoff.md"
            request_path.write_text("STATUS: request_open\nCONTROL_SEQ: 2\n")
            advice_path.write_text("STATUS: advice_ready\nCONTROL_SEQ: 3\n")
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 4\n")
            os.utime(request_path, (300.0, 300.0))
            os.utime(advice_path, (200.0, 200.0))
            os.utime(handoff_path, (100.0, 100.0))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, handoff_path)
            self.assertEqual(core._get_pending_gemini_request_mtime(), 0.0)
            self.assertEqual(core._get_pending_gemini_advice_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "claude")


class ClaudeHandoffDispatchTest(unittest.TestCase):
    def test_handoff_update_waits_until_verify_lease_released(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work" / "4" / "8"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir = root / "verify" / "4" / "8"
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "2026-04-08-sample-work.md"
            verify_note = verify_dir / "2026-04-08-sample-verify.md"
            work_note.write_text("## 변경 파일\n- 없음\n")
            verify_note.write_text("## 변경 파일\n- 없음\n")
            os.utime(work_note, (10.0, 10.0))
            os.utime(verify_note, (20.0, 20.0))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 10\n")
            core.lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900)

            with mock.patch.object(core, "_notify_claude") as notify:
                core._check_pipeline_signal_updates()
                notify.assert_not_called()
                # Handoff detected but verify active, so stays at current state
                self.assertNotEqual(core._current_turn_state, watcher_core.WatcherTurnState.CLAUDE_ACTIVE)

                core.lease.release("slot_verify")
                core._check_pipeline_signal_updates()
                notify.assert_called_once()
                self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CLAUDE_ACTIVE)

    def test_handoff_update_releases_from_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work" / "4" / "8"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir = root / "verify" / "4" / "8"
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "2026-04-08-sample-work.md"
            verify_note = verify_dir / "2026-04-08-sample-verify.md"
            work_note.write_text("## 변경 파일\n- 없음\n")
            verify_note.write_text("## 변경 파일\n- 없음\n")
            os.utime(work_note, (10.0, 10.0))
            os.utime(verify_note, (20.0, 20.0))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 10\n")
            core._transition_turn(
                watcher_core.WatcherTurnState.CODEX_FOLLOWUP,
                "test_followup_active",
                active_control_file="gemini_advice.md",
                active_control_seq=9,
            )
            core.lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900)

            with mock.patch.object(core, "_notify_claude") as notify:
                core._check_pipeline_signal_updates()
                notify.assert_not_called()
                self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CODEX_FOLLOWUP)

                core.lease.release("slot_verify")
                core._check_pipeline_signal_updates()
                notify.assert_called_once()
                self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CLAUDE_ACTIVE)


class RuntimePlanConsumptionTest(unittest.TestCase):
    def test_role_neutral_prompt_contract_survives_nondefault_role_owners(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
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
                },
            )
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n", encoding="utf-8")
            work_note = watch_dir / "2026-04-09-runtime-role-neutral.md"
            work_note.write_text("## 변경 파일\n- watcher_core.py\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            job = watcher_core.JobState.from_artifact("job-role-neutral", str(work_note))

            implement_prompt = core._format_implement_prompt(handoff_path)
            verify_prompt = core.sm.verify_prompt_template.format(**core._build_verify_prompt_context(job))
            advisory_prompt = core._format_runtime_prompt(core.advisory_prompt)
            followup_prompt = core._format_runtime_prompt(core.followup_prompt)

            self.assertIn("ROLE: implement", implement_prompt)
            self.assertIn("OWNER: Codex", implement_prompt)
            self.assertNotIn("claude_implement", implement_prompt)
            self.assertNotIn("CLAUDE.md", implement_prompt)
            self.assertIn("AGENTS.md", implement_prompt)
            self.assertIn("work/README.md", implement_prompt)
            self.assertIn("GOAL:", implement_prompt)
            self.assertIn("leave one `/work` closeout and stop", implement_prompt)
            self.assertIn("do not commit, push, publish a branch/PR, or choose the next slice", implement_prompt)
            self.assertNotIn(".pipeline/README.md", implement_prompt)

            self.assertIn("ROLE: verify", verify_prompt)
            self.assertIn("OWNER: Claude", verify_prompt)
            self.assertNotIn("codex_verify", verify_prompt)
            self.assertIn("CLAUDE.md", verify_prompt)
            self.assertIn("GOAL:", verify_prompt)
            self.assertIn("leave or update `/verify` before any next control slot", verify_prompt)
            self.assertIn("same-day same-family docs-only truth-sync already repeated 3+ times", verify_prompt)
            self.assertIn(".pipeline/claude_handoff.md (STATUS: implement, CONTROL_SEQ:", verify_prompt)
            self.assertNotIn(".pipeline/README.md", verify_prompt)
            self.assertNotIn("never route needs_operator to Claude", verify_prompt)

            self.assertIn("ROLE: advisory", advisory_prompt)
            self.assertIn("OWNER: Gemini", advisory_prompt)
            self.assertNotIn("gemini_arbitrate", advisory_prompt)
            self.assertIn("GEMINI.md", advisory_prompt)
            self.assertIn("GOAL:", advisory_prompt)
            self.assertIn("pane-only answer is not completion", advisory_prompt)

            self.assertIn("ROLE: followup", followup_prompt)
            self.assertIn("OWNER: Claude", followup_prompt)
            self.assertNotIn("codex_followup", followup_prompt)
            self.assertIn("CLAUDE.md", followup_prompt)
            self.assertIn("GOAL:", followup_prompt)

    def test_gemini_request_dispatch_allows_advisory_without_session_arbitration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex", "Gemini"],
                    "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
                    "role_options": {
                        "advisory_enabled": True,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": False,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )
            gemini_request = base_dir / "gemini_request.md"
            gemini_request.write_text("STATUS: request_open\nCONTROL_SEQ: 5\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._last_gemini_request_sig = ""

            with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                core._check_pipeline_signal_updates()

            args, kwargs = send.call_args
            self.assertEqual(args[0], "gemini-pane")
            self.assertEqual(kwargs.get("pane_type"), "gemini")

    def test_operator_request_disabled_is_not_active_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex"],
                    "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": ""},
                    "role_options": {
                        "advisory_enabled": False,
                        "operator_stop_enabled": False,
                        "session_arbitration_enabled": False,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )
            operator_path = base_dir / "operator_request.md"
            handoff_path = base_dir / "claude_handoff.md"
            operator_path.write_text("STATUS: needs_operator\nCONTROL_SEQ: 9\n", encoding="utf-8")
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 8\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, handoff_path)
            self.assertEqual(core._get_pending_operator_mtime(), 0.0)

    def test_gemini_request_disabled_without_advisory_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex"],
                    "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": ""},
                    "role_options": {
                        "advisory_enabled": False,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": False,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )
            gemini_request = base_dir / "gemini_request.md"
            handoff_path = base_dir / "claude_handoff.md"
            gemini_request.write_text("STATUS: request_open\nCONTROL_SEQ: 9\n", encoding="utf-8")
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 8\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, handoff_path)
            self.assertEqual(core._get_gemini_request_mtime(), 0.0)

    def test_verify_owner_updates_runtime_verify_target_and_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude"],
                    "role_bindings": {"implement": "Claude", "verify": "Claude", "advisory": ""},
                    "role_options": {
                        "advisory_enabled": False,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": False,
                    },
                    "mode_flags": {
                        "single_agent_mode": True,
                        "self_verify_allowed": True,
                        "self_advisory_allowed": False,
                    },
                },
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            self.assertEqual(core.sm.verify_pane_target, "claude-pane")
            self.assertEqual(core.sm.verify_pane_type, "claude")

    def test_implement_notify_routes_to_runtime_owner_pane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Codex"],
                    "role_bindings": {"implement": "Codex", "verify": "Codex", "advisory": ""},
                    "role_options": {
                        "advisory_enabled": False,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": False,
                    },
                    "mode_flags": {
                        "single_agent_mode": True,
                        "self_verify_allowed": True,
                        "self_advisory_allowed": False,
                    },
                },
            )
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                core._notify_claude("test-runtime-implement", handoff_path)

            args, kwargs = send.call_args
            self.assertEqual(args[0], "codex-pane")
            self.assertEqual(kwargs.get("pane_type"), "codex")

    def test_session_arbitration_disabled_skips_live_escalation_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Codex"],
                    "role_bindings": {"implement": "Codex", "verify": "Codex", "advisory": ""},
                    "role_options": {
                        "advisory_enabled": False,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": False,
                    },
                    "mode_flags": {
                        "single_agent_mode": True,
                        "self_verify_allowed": True,
                        "self_advisory_allowed": False,
                    },
                },
            )
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.CLAUDE_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "codex-pane": (
                    "이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.\n"
                    "context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.\n"
                    "진행할까요?\n>\n"
                ),
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts.get(target, "> ")):
                core._poll()

            self.assertFalse((base_dir / "session_arbitration_draft.md").exists())


class VerifyPromptScopeHintTest(unittest.TestCase):
    def test_docs_only_round_gets_docs_only_fast_path_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_dir = root / "work" / "4" / "9"
            work_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            work_note = work_dir / "2026-04-09-docs-only.md"
            work_note.write_text(
                "## 변경 파일\n"
                "- docs/PRODUCT_SPEC.md\n"
                "- docs/ACCEPTANCE_CRITERIA.md\n"
                "\n"
                "## 검증\n"
                "- git diff --check\n"
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )
            job = watcher_core.JobState.from_artifact("job-docs", str(work_note))

            context = core._build_verify_prompt_context(job)

            self.assertEqual(context["verify_scope_label"], "docs_only")
            self.assertIn("docs-only truth-sync round", context["verify_scope_hint"])
            self.assertIn("git diff --check", context["verify_scope_hint"])

    def test_code_mixed_round_keeps_standard_verify_scope_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_dir = root / "work" / "4" / "9"
            work_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            work_note = work_dir / "2026-04-09-mixed.md"
            work_note.write_text(
                "## 변경 파일\n"
                "- app/static/app.js\n"
                "- docs/PRODUCT_SPEC.md\n"
                "\n"
                "## 검증\n"
                "- python3 -m unittest -v tests.test_web_app\n"
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )
            job = watcher_core.JobState.from_artifact("job-mixed", str(work_note))

            context = core._build_verify_prompt_context(job)

            self.assertEqual(context["verify_scope_label"], "standard")
            self.assertIn("standard verification round", context["verify_scope_hint"])
            self.assertNotIn("docs-only truth-sync", context["verify_scope_hint"])


class TurnStateEnumTest(unittest.TestCase):
    def test_turn_state_values(self) -> None:
        from watcher_core import WatcherTurnState
        expected = {"IDLE", "CLAUDE_ACTIVE", "CODEX_VERIFY", "CODEX_FOLLOWUP",
                    "GEMINI_ADVISORY", "OPERATOR_WAIT"}
        self.assertEqual(set(e.value for e in WatcherTurnState), expected)


class TurnResolutionTest(unittest.TestCase):
    def test_codex_verify_before_claude_when_work_exists(self) -> None:
        """When work needs verify and handoff is active, Codex goes first."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            work_note = watch_dir / "4" / "10" / "2026-04-10-some-work.md"
            _write_work_note(work_note, ["controller/server.py"])

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "codex")

    def test_claude_active_when_no_pending_verify(self) -> None:
        """When no work needs verify and handoff is active, Claude goes."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "claude")

    def test_idle_fallback_when_nothing_pending(self) -> None:
        """When no control signals and no work, state is IDLE."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "idle")

    def test_stale_operator_request_resolves_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 20",
                        "REASON_CODE: truth_sync_required",
                        "OPERATOR_POLICY: immediate_publish",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: confirm blocker closeout",
                        "BASED_ON_WORK: work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "",
                        "Stop now:",
                        "- `work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md`",
                    ]
                ),
                encoding="utf-8",
            )
            (state_dir / "job-1.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-1",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "artifact_hash": "hash-1",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._stale_operator_control_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(core._get_pending_operator_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_aged_operator_request_resolves_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 23",
                        "",
                        "Reason:",
                        "- still waiting",
                    ]
                ),
                encoding="utf-8",
            )
            old = time.time() - 30
            os.utime(operator_path, (old, old))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "operator_wait_retriage_sec": 5,
                }
            )

            marker = core._operator_control_recovery_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "operator_wait_idle_retriage")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_fresh_slice_ambiguity_operator_request_routes_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 26\n"
                "REASON_CODE: slice_ambiguity\n"
                "OPERATOR_POLICY: gate_24h\n"
                "DECISION_CLASS: operator_only\n"
                "DECISION_REQUIRED: choose exact next slice\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "slice_ambiguity")
            self.assertEqual(marker["operator_policy"], "gate_24h")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_truth_sync_operator_request_stays_operator_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 27\n"
                "REASON_CODE: truth_sync_required\n"
                "OPERATOR_POLICY: immediate_publish\n"
                "DECISION_CLASS: operator_only\n"
                "DECISION_REQUIRED: confirm truth sync\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_gate_marker())
            self.assertEqual(core._resolve_turn(), "operator")

    def test_fresh_idle_operator_request_hibernates_instead_of_operator_wait(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 28\n"
                "REASON_CODE: idle_hibernate\n"
                "OPERATOR_POLICY: internal_only\n"
                "DECISION_CLASS: internal_only\n"
                "DECISION_REQUIRED: wait for next control\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["mode"], "hibernate")
            self.assertEqual(core._resolve_turn(), "idle")

    def test_operator_request_missing_structured_headers_stays_fail_safe_operator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 29\n\nReason:\n- slice_ambiguity\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_gate_marker())
            self.assertEqual(core._resolve_turn(), "operator")

    def test_codex_verify_before_claude_even_for_metadata_only_note(self) -> None:
        """Metadata-only work note still triggers Codex verify before Claude."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            meta_note = watch_dir / "4" / "10" / "2026-04-10-meta-only.md"
            _write_work_note(meta_note, ["work/4/10/2026-04-10-meta-only.md"])

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "codex")


class RollingSignalTransitionTest(unittest.TestCase):
    def test_stale_control_seq_does_not_trigger_transition(self) -> None:
        """A signal with lower control_seq than current should not cause transition."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            # Set current state with seq 17
            core._transition_turn(
                watcher_core.WatcherTurnState.CODEX_VERIFY,
                "test_setup",
                active_control_seq=17,
            )

            # A handoff with lower seq should not override
            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 15\n", encoding="utf-8")
            # Reset sig tracking so change is detected
            core._last_claude_handoff_sig = ""
            core._check_pipeline_signal_updates()

            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CODEX_VERIFY)

    def test_higher_seq_handoff_transitions_to_claude(self) -> None:
        """A handoff with higher seq should trigger Claude transition."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IDLE,
                "test_setup",
                active_control_seq=15,
            )

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 18\n", encoding="utf-8")
            core._last_claude_handoff_sig = ""

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                core._check_pipeline_signal_updates()

            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CLAUDE_ACTIVE)

    def test_stale_operator_request_update_routes_to_codex_control_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 21",
                        "REASON_CODE: truth_sync_required",
                        "OPERATOR_POLICY: immediate_publish",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: confirm blocker closeout",
                        "BASED_ON_WORK: work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "",
                        "Stop now:",
                        "- `work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md`",
                    ]
                ),
                encoding="utf-8",
            )
            (state_dir / "job-2.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-2",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "artifact_hash": "hash-2",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })
            core._last_operator_request_sig = ""

            with mock.patch.object(core, "_notify_codex_control_recovery") as notify:
                core._check_pipeline_signal_updates()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CODEX_FOLLOWUP)

    def test_startup_turn_uses_codex_control_recovery_for_stale_operator_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 22",
                        "REASON_CODE: truth_sync_required",
                        "OPERATOR_POLICY: immediate_publish",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: confirm blocker closeout",
                        "BASED_ON_WORK: work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "",
                        "Stop now:",
                        "- `work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md`",
                    ]
                ),
                encoding="utf-8",
            )
            (state_dir / "job-3.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-3",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "artifact_hash": "hash-3",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })
            core.started_at = time.time() - core.startup_grace_sec - 1.0

            with mock.patch.object(core, "_notify_codex_control_recovery") as notify:
                core._poll()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CODEX_FOLLOWUP)

    def test_startup_turn_uses_codex_operator_retriage_for_aged_operator_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 25\n\nReason:\n- still pending\n",
                encoding="utf-8",
            )
            old = time.time() - 30
            os.utime(operator_path, (old, old))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "operator_wait_retriage_sec": 5,
                }
            )
            core.started_at = time.time() - core.startup_grace_sec - 1.0

            with mock.patch.object(core, "_notify_codex_operator_retriage") as notify:
                core._poll()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CODEX_FOLLOWUP)

    def test_operator_wait_idle_timeout_routes_to_codex_operator_retriage_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 24\n\nReason:\n- still pending\n",
                encoding="utf-8",
            )
            old = time.time() - 30
            os.utime(operator_path, (old, old))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "operator_wait_retriage_sec": 5,
                }
            )
            core._transition_turn(
                watcher_core.WatcherTurnState.OPERATOR_WAIT,
                "test_setup_operator_wait",
                active_control_file="operator_request.md",
                active_control_seq=24,
            )

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="$ "),
                mock.patch("watcher_core._pane_text_is_idle", return_value=True),
                mock.patch.object(core, "_notify_codex_operator_retriage") as notify,
            ):
                core._check_operator_wait_idle_timeout()
                core._check_operator_wait_idle_timeout()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CODEX_FOLLOWUP)
            self.assertEqual(core._turn_active_control_seq, 24)

    def test_higher_seq_handoff_is_deferred_while_claude_round_is_active(self) -> None:
        """An updated handoff should not hot-swap into an already active Claude round."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
                "test_setup",
                active_control_seq=17,
            )

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 18\n", encoding="utf-8")
            core._last_claude_handoff_sig = ""

            with mock.patch.object(core, "_notify_claude") as notify:
                core._check_pipeline_signal_updates()

            notify.assert_not_called()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CLAUDE_ACTIVE)

    def test_deferred_handoff_flushes_after_active_claude_round_exits(self) -> None:
        """A deferred handoff should dispatch once the active Claude round exits."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
                "test_setup",
                active_control_seq=17,
            )

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 18\n", encoding="utf-8")
            core._last_claude_handoff_sig = ""

            with mock.patch.object(core, "_notify_claude") as notify:
                core._check_pipeline_signal_updates()
                notify.assert_not_called()

                core._transition_turn(
                    watcher_core.WatcherTurnState.IDLE,
                    "test_round_exit",
                    active_control_seq=17,
                )
                core._check_pipeline_signal_updates()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CLAUDE_ACTIVE)


class ClaudeIdleTimeoutTest(unittest.TestCase):
    def test_claude_idle_timeout_transitions_to_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_active_idle_timeout_sec": 5,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
                "test_setup",
            )
            import hashlib as _hlib
            idle_fingerprint = _hlib.md5(b"$ ").hexdigest()
            core._last_active_pane_fingerprint = idle_fingerprint
            core._last_progress_at = time.time() - 10
            core._work_baseline_snapshot = {}

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "):
                with mock.patch("watcher_core._pane_text_is_idle", return_value=True):
                    core._check_claude_idle_timeout()

            self.assertEqual(
                core._current_turn_state,
                watcher_core.WatcherTurnState.IDLE,
            )

    def test_claude_progress_resets_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_active_idle_timeout_sec": 5,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
                "test_setup",
            )
            core._last_progress_at = time.time() - 10
            core._last_active_pane_fingerprint = "old_fingerprint"

            with mock.patch("watcher_core._capture_pane_text", return_value="running tests..."):
                with mock.patch("watcher_core._pane_text_is_idle", return_value=False):
                    core._check_claude_idle_timeout()

            self.assertEqual(
                core._current_turn_state,
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
            )
            self.assertGreater(core._last_progress_at, time.time() - 2)

    def test_idle_release_cooldown_prevents_redispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_active_idle_timeout_sec": 5,
            })

            handoff_sig = core._get_path_sig(handoff)
            core._last_idle_release_handoff_sig = handoff_sig
            core._last_idle_release_at = time.time()

            self.assertTrue(core._is_idle_release_cooldown_active())


class TransitionTurnTest(unittest.TestCase):
    def test_transition_writes_turn_state_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CODEX_VERIFY,
                "work_needs_verify",
                active_control_file="claude_handoff.md",
                active_control_seq=17,
                verify_job_id="test-job-1",
            )

            state_path = base_dir / "state" / "turn_state.json"
            self.assertTrue(state_path.exists())
            data = json.loads(state_path.read_text())
            self.assertEqual(data["state"], "CODEX_VERIFY")
            self.assertEqual(data["reason"], "work_needs_verify")
            self.assertEqual(data["active_control_file"], "claude_handoff.md")
            self.assertEqual(data["active_control_seq"], 17)
            self.assertEqual(data["verify_job_id"], "test-job-1")
            self.assertIn("entered_at", data)

            current_run_path = base_dir / "current_run.json"
            self.assertTrue(current_run_path.exists())
            current_run = json.loads(current_run_path.read_text())
            self.assertEqual(current_run["run_id"], core.run_id)

            status_path = base_dir / "runs" / core.run_id / "status.json"
            self.assertTrue(status_path.exists())
            status = json.loads(status_path.read_text())
            self.assertEqual(status["run_id"], core.run_id)
            self.assertEqual(status["runtime_state"], "RUNNING")
            self.assertEqual(status["turn_state"], "CODEX_VERIFY")
            self.assertEqual(status["control"]["active_control_file"], ".pipeline/claude_handoff.md")
            self.assertEqual(status["control"]["active_control_seq"], 17)

            events_path = base_dir / "runs" / core.run_id / "events.jsonl"
            self.assertTrue(events_path.exists())
            events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
            self.assertGreaterEqual(len(events), 2)
            self.assertEqual(events[0]["event_type"], "runtime_started")
            self.assertEqual(events[-1]["event_type"], "control_changed")

    def test_runtime_export_keeps_claude_working_while_implement_control_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            with mock.patch("watcher_core._capture_pane_text", return_value="• Working (12s • esc to interrupt)\n"):
                core._transition_turn(
                    watcher_core.WatcherTurnState.CODEX_VERIFY,
                    "work_needs_verify",
                    active_control_file="claude_handoff.md",
                    active_control_seq=17,
                    verify_job_id="test-job-1",
                )

            status_path = base_dir / "runs" / core.run_id / "status.json"
            status = json.loads(status_path.read_text())
            claude = next(lane for lane in status["lanes"] if lane["name"] == "Claude")
            codex = next(lane for lane in status["lanes"] if lane["name"] == "Codex")

            self.assertEqual(status["control"]["active_control_status"], "implement")
            self.assertEqual(claude["state"], "WORKING")
            self.assertEqual(codex["state"], "WORKING")

    def test_runtime_export_keeps_idle_claude_ready_during_verify_follow_on(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            with mock.patch(
                "watcher_core._capture_pane_text",
                return_value=(
                    "❯ \n"
                    "───────────────────────────────────────────────────────────────────────────────\n"
                    "  ⏵⏵ bypass permissions on (shift+tab to cycle) · esc to interrupt\n"
                ),
            ):
                core._transition_turn(
                    watcher_core.WatcherTurnState.CODEX_VERIFY,
                    "work_needs_verify",
                    active_control_file="claude_handoff.md",
                    active_control_seq=17,
                    verify_job_id="test-job-1",
                )

            status_path = base_dir / "runs" / core.run_id / "status.json"
            status = json.loads(status_path.read_text())
            claude = next(lane for lane in status["lanes"] if lane["name"] == "Claude")
            codex = next(lane for lane in status["lanes"] if lane["name"] == "Codex")

            self.assertEqual(status["control"]["active_control_status"], "implement")
            self.assertEqual(claude["state"], "READY")
            self.assertEqual(codex["state"], "WORKING")

    def test_transition_updates_internal_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CLAUDE_ACTIVE,
                "startup",
            )
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CLAUDE_ACTIVE)

            core._transition_turn(
                watcher_core.WatcherTurnState.IDLE,
                "claude_idle_timeout",
            )
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IDLE)


class VerifyCompletionContractTest(unittest.TestCase):
    def test_control_slot_change_without_verify_note_keeps_verify_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["docs/ACCEPTANCE_CRITERIA.md"])
            job = watcher_core.JobState.from_artifact("job-verify-contract", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 19\n", encoding="utf-8")

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

            verify_note = root / "verify" / "4" / "10" / "2026-04-10-slice-verification.md"
            _write_verify_note(verify_note, ["verify/4/10/2026-04-10-slice-verification.md"])

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_DONE)
            self.assertEqual(job.verify_result, "passed_by_feedback")
            self.assertTrue(job.verify_manifest_path)
            manifest_path = Path(job.verify_manifest_path)
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["role"], "slot_verify")
            self.assertEqual(
                manifest["feedback_path"],
                "verify/4/10/2026-04-10-slice-verification.md",
            )

    def test_verify_tree_change_without_current_round_receipt_keeps_verify_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            verify_day = verify_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            verify_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            old_verify_note = verify_day / "2026-04-10-old-verification.md"
            _write_verify_note(old_verify_note, ["verify/4/10/2026-04-10-old-verification.md"])
            os.utime(old_verify_note, (10.0, 10.0))
            job = watcher_core.JobState.from_artifact("job-verify-receipt", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

    def test_idle_timeout_with_incomplete_outputs_requeues_verify_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-retry", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

            job.last_activity_at = time.time() - 400
            job.last_dispatch_at = time.time() - 400
            job.last_pane_snapshot = "$ "
            core.sm.runtime_started_at = time.time() - 800

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertGreater(job.last_failed_dispatch_at, 0.0)
            self.assertEqual(job.last_failed_dispatch_snapshot, "")
            self.assertGreaterEqual(job.dispatch_fail_count, 1)
            self.assertEqual(job.verify_receipt_baseline_path, "")
            self.assertFalse(
                core.dedupe.is_duplicate(job.job_id, job.round, job.artifact_hash, "slot_verify")
            )

            job.last_failed_dispatch_at = time.time() - 30
            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

    def test_idle_prompt_with_incomplete_outputs_requeues_before_long_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-quick-idle", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_incomplete_idle_retry_sec": 20.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = time.time() - 35
            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 30
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertGreater(job.last_failed_dispatch_at, 0.0)
            self.assertEqual(job.last_failed_dispatch_snapshot, "")
            self.assertEqual(job.dispatch_stall_count, 0)
            self.assertEqual(job.degraded_reason, "")
            self.assertEqual(job.lane_note, "")
            self.assertIn("TASK_ACCEPTED", job.history[-1]["reason"])

    def test_repeated_dispatch_stall_marks_job_degraded_after_one_requeue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-stall-repeat", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_incomplete_idle_retry_sec": 20.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            first_dispatch_at = time.time() - 35
            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = first_dispatch_at
            job.accept_deadline_at = time.time() - 1
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.dispatch_stall_count, 1)
            self.assertEqual(job.degraded_reason, "")

            job.last_failed_dispatch_at = time.time() - 30
            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.dispatch_stall_count, 1)
            self.assertEqual(job.degraded_reason, "")

            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = time.time() - 35
            job.accept_deadline_at = time.time() - 1
            job.last_pane_snapshot = "› prompt"

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.dispatch_stall_count, 2)
            self.assertEqual(job.degraded_reason, "dispatch_stall")
            self.assertEqual(job.lane_note, "waiting_task_accept_after_dispatch")

            with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_keys:
                same_job = core.sm._handle_verify_pending(job)

            self.assertIs(same_job, job)
            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            send_keys.assert_not_called()

    def test_delayed_task_accepted_does_not_false_stall_before_accept_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            run_dir = base_dir / "runs" / "run-1"
            wrapper_dir = run_dir / "wrapper-events"
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-delayed-accept", str(work_note))

            with mock.patch.dict(os.environ, {"PIPELINE_RUNTIME_DISABLE_EXPORTER": "1"}):
                core = watcher_core.WatcherCore(
                    {
                        "watch_dir": str(watch_dir),
                        "base_dir": str(base_dir),
                        "repo_root": str(root),
                        "dry_run": True,
                        "verify_pane_target": "codex-pane",
                        "verify_incomplete_idle_retry_sec": 20.0,
                        "verify_accept_deadline_sec": 30.0,
                    }
                )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

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

            job.last_activity_at = time.time() - 25
            job.last_dispatch_at = time.time() - 25
            job.accept_deadline_at = time.time() + 5
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.degraded_reason, "")
            self.assertEqual(job.accepted_dispatch_id, "")

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_ACCEPTED",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="vendor_output",
            )

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.accepted_dispatch_id, job.dispatch_id)
            self.assertEqual(job.degraded_reason, "")

    def test_verify_running_startup_recovery_requeues_stale_idle_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-startup-recovery", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_RUNNING
            job.artifact_hash = "artifact-hash"
            job.last_dispatch_at = time.time() - 30
            job.last_pane_snapshot = "$ "
            job.last_activity_at = time.time() - 5

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "restart_recovery_grace_sec": 5.0,
                }
            )
            core.sm.runtime_started_at = time.time() - 10
            core.sm.dedupe.mark_dispatch(
                job.job_id,
                job.round,
                job.artifact_hash,
                "slot_verify",
                "codex-pane",
                True,
            )

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.last_dispatch_slot, "")
            self.assertFalse(
                core.dedupe.is_duplicate(job.job_id, job.round, job.artifact_hash, "slot_verify")
            )


class CodexDispatchConfirmationTest(unittest.TestCase):
    def test_dispatch_codex_clears_existing_prompt_input_before_paste(self) -> None:
        snapshots = iter([
            "› stale draft",
            "processing view without prompt",
        ])
        run_calls: list[list[str]] = []

        def _run(cmd, **kwargs):
            run_calls.append(list(cmd))
            return mock.Mock(stdout="", stderr=b"")

        with mock.patch("watcher_core.subprocess.run", side_effect=_run), \
             mock.patch("watcher_core._capture_pane_text", side_effect=lambda _pane: next(snapshots)), \
             mock.patch("watcher_core._pane_has_working_indicator", return_value=True), \
             mock.patch("watcher_core.time.sleep", return_value=None):
            result = watcher_core._dispatch_codex("%1", "ROLE: verify")

        self.assertTrue(result)
        self.assertGreaterEqual(len(run_calls), 3)
        self.assertEqual(run_calls[0], ["tmux", "send-keys", "-t", "%1", "C-u"])

    def test_dispatch_codex_returns_false_when_no_working_or_activity_is_confirmed(self) -> None:
        snapshots = itertools.chain(
            [
                "› prompt pasted",
                "processing view without prompt",
            ],
            itertools.repeat("processing view without prompt"),
        )

        with mock.patch("watcher_core.subprocess.run") as run_mock, \
             mock.patch("watcher_core._capture_pane_text", side_effect=lambda _pane: next(snapshots)), \
             mock.patch("watcher_core._pane_has_working_indicator", return_value=False), \
             mock.patch("watcher_core._pane_text_has_codex_activity", return_value=False), \
             mock.patch("watcher_core.time.sleep", return_value=None):
            result = watcher_core._dispatch_codex("%1", "ROLE: verify")

        self.assertFalse(result)
        self.assertGreaterEqual(run_mock.call_count, 3)

    def test_dispatch_codex_returns_true_when_working_indicator_appears(self) -> None:
        snapshots = iter([
            "› prompt pasted",
            "processing view without prompt",
        ])

        with mock.patch("watcher_core.subprocess.run"), \
             mock.patch("watcher_core._capture_pane_text", side_effect=lambda _pane: next(snapshots)), \
             mock.patch("watcher_core._pane_has_working_indicator", side_effect=[True]), \
             mock.patch("watcher_core.time.sleep", return_value=None):
            result = watcher_core._dispatch_codex("%1", "ROLE: verify")

        self.assertTrue(result)


class VerifyPendingBackoffTest(unittest.TestCase):
    def test_failed_dispatch_sets_retry_backoff_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "2026-04-10-slice.md"
            _write_work_note(work_note, ["e2e/tests/web-smoke.spec.mjs"])
            job = watcher_core.JobState.from_artifact("job-backoff", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_PENDING
            job.artifact_hash = "hash-1"

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=False), \
                 mock.patch("watcher_core._capture_pane_text", return_value="› pasted prompt placeholder"):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertGreater(job.last_failed_dispatch_at, 0.0)
            self.assertEqual(job.last_failed_dispatch_snapshot, "› pasted prompt placeholder")
            self.assertEqual(job.dispatch_fail_count, 1)

    def test_failed_dispatch_backoff_skips_immediate_redispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "2026-04-10-slice.md"
            _write_work_note(work_note, ["e2e/tests/web-smoke.spec.mjs"])
            job = watcher_core.JobState.from_artifact("job-backoff", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_PENDING
            job.artifact_hash = "hash-1"
            job.last_failed_dispatch_at = time.time()
            job.last_failed_dispatch_snapshot = "› pasted prompt placeholder"

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch.object(core.lease, "acquire", side_effect=AssertionError("lease should not be acquired")), \
                 mock.patch("watcher_core.tmux_send_keys", side_effect=AssertionError("dispatch should not run")):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)

    def test_failed_dispatch_same_snapshot_skips_retry_after_backoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "2026-04-10-slice.md"
            _write_work_note(work_note, ["e2e/tests/web-smoke.spec.mjs"])
            job = watcher_core.JobState.from_artifact("job-backoff", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_PENDING
            job.artifact_hash = "hash-1"
            job.last_failed_dispatch_at = time.time() - 30
            job.last_failed_dispatch_snapshot = "› pasted prompt placeholder"

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch.object(core.lease, "acquire", side_effect=AssertionError("lease should not be acquired")), \
                 mock.patch("watcher_core.tmux_send_keys", side_effect=AssertionError("dispatch should not run")), \
                 mock.patch("watcher_core._capture_pane_text", return_value="› pasted prompt placeholder"):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)


if __name__ == "__main__":
    unittest.main()
