import os
import tempfile
import unittest
import json
from pathlib import Path
from unittest import mock

import watcher_core


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
            core._waiting_for_claude = False

            with mock.patch.object(core.sm, "step", wraps=core.sm.step) as advance:
                core._poll()

            self.assertFalse(any((base_dir / "state").glob("*.json")))
            self.assertEqual(advance.call_count, 0)


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
            core._waiting_for_claude = True
            core._work_baseline_snapshot = {}

            handoff_sha = watcher_core.compute_file_sha256(handoff_path)
            pane_texts = {
                "claude-pane": (
                    "STATUS: implement_blocked\n"
                    "BLOCK_REASON: handoff_not_actionable\n"
                    "REQUEST: codex_triage\n"
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
            self.assertIn("ROLE_OWNER: Codex", args[1])
            self.assertIn("BLOCK_REASON: handoff_not_actionable", args[1])
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
            core._waiting_for_claude = True
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
            core._waiting_for_claude = True
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
            core._waiting_for_claude = True
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

            self.assertEqual(send.call_count, 1)
            args, _ = send.call_args
            self.assertIn("BLOCK_REASON: handoff_already_completed", args[1])

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
            self.assertEqual(core._determine_initial_turn(), "claude")

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
            self.assertEqual(core._determine_initial_turn(), "gemini")

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
            self.assertEqual(core._determine_initial_turn(), "claude")


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
            handoff_path.write_text("STATUS: implement\n")
            core.lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900)

            with mock.patch.object(core, "_notify_claude") as notify:
                core._check_pipeline_signal_updates()
                notify.assert_not_called()
                self.assertEqual(core._pending_claude_handoff_sig, core._get_path_sig(handoff_path))

                core.lease.release("slot_verify")
                core._check_pipeline_signal_updates()
                notify.assert_called_once_with("claude_handoff_pending_release", handoff_path)
                self.assertEqual(core._pending_claude_handoff_sig, "")


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
            self.assertIn("ROLE_OWNER: Codex", implement_prompt)
            self.assertNotIn("claude_implement", implement_prompt)
            self.assertNotIn("CLAUDE.md", implement_prompt)
            self.assertIn("AGENTS.md", implement_prompt)
            self.assertIn("work/README.md", implement_prompt)
            self.assertIn("leave a `/work` closeout note", implement_prompt)
            self.assertIn("do not use `report/` as the primary implementation closeout", implement_prompt)

            self.assertIn("ROLE: verify", verify_prompt)
            self.assertIn("ROLE_OWNER: Claude", verify_prompt)
            self.assertNotIn("codex_verify", verify_prompt)
            self.assertIn("CLAUDE.md", verify_prompt)

            self.assertIn("ROLE: advisory", advisory_prompt)
            self.assertIn("ROLE_OWNER: Gemini", advisory_prompt)
            self.assertNotIn("gemini_arbitrate", advisory_prompt)
            self.assertIn("GEMINI.md", advisory_prompt)

            self.assertIn("ROLE: followup", followup_prompt)
            self.assertIn("ROLE_OWNER: Claude", followup_prompt)
            self.assertNotIn("codex_followup", followup_prompt)
            self.assertIn("CLAUDE.md", followup_prompt)

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
            core._waiting_for_claude = True
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


if __name__ == "__main__":
    unittest.main()
