"""Tests for pipeline_gui.backend control-slot parsing."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import pipeline_gui.backend
from pipeline_gui.backend import (
    confirm_pipeline_start,
    current_verify_activity,
    format_control_summary,
    normalize_runtime_status,
    parse_control_slots,
    pipeline_start,
    pipeline_start_failure_hint,
    read_runtime_status,
    watcher_log_snapshot,
    watcher_start_observed,
)


class TestParseControlSlots(unittest.TestCase):
    """Newest-valid-control selection and stale listing."""

    def _write_slot(
        self,
        pipeline_dir: Path,
        filename: str,
        status: str,
        age_offset: float = 0,
        control_seq: int | None = None,
    ) -> None:
        slot = pipeline_dir / filename
        seq_line = f"CONTROL_SEQ: {control_seq}\n" if control_seq is not None else ""
        slot.write_text(f"STATUS: {status}\n{seq_line}\nsome body text\n", encoding="utf-8")
        import os
        mtime = time.time() - age_offset
        os.utime(slot, (mtime, mtime))

    def test_single_valid_slot_is_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "claude_handoff.md", "implement")
            result = parse_control_slots(project)
            self.assertIsNotNone(result["active"])
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertEqual(result["stale"], [])

    def test_newest_slot_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "operator_request.md", "needs_operator", age_offset=100)
            self._write_slot(pipeline, "claude_handoff.md", "implement", age_offset=0)
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertEqual(len(result["stale"]), 1)
            self.assertEqual(result["stale"][0]["file"], "operator_request.md")

    def test_invalid_status_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "claude_handoff.md", "implement_blocked")
            result = parse_control_slots(project)
            self.assertIsNone(result["active"])

    def test_no_slots_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            result = parse_control_slots(project)
            self.assertIsNone(result["active"])
            self.assertEqual(result["stale"], [])

    def test_multiple_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "claude_handoff.md", "implement", age_offset=0)
            self._write_slot(pipeline, "gemini_request.md", "request_open", age_offset=50)
            self._write_slot(pipeline, "operator_request.md", "needs_operator", age_offset=100)
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertEqual(len(result["stale"]), 2)

    def test_control_seq_beats_newer_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "gemini_request.md", "request_open", age_offset=100, control_seq=8)
            self._write_slot(pipeline, "claude_handoff.md", "implement", age_offset=0, control_seq=7)
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "gemini_request.md")
            self.assertEqual(result["active"]["control_seq"], 8)

    def test_stale_gemini_slots_lose_to_higher_handoff_seq(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "gemini_request.md", "request_open", age_offset=0, control_seq=2)
            self._write_slot(pipeline, "gemini_advice.md", "advice_ready", age_offset=50, control_seq=3)
            self._write_slot(pipeline, "claude_handoff.md", "implement", age_offset=100, control_seq=4)
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertEqual([entry["file"] for entry in result["stale"]], ["gemini_advice.md", "gemini_request.md"])

    def test_same_second_mtime_uses_subsecond_precision(self):
        """When slots share the same integer second, sub-second mtime must break the tie."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            base_time = float(int(time.time()))  # truncated to integer second
            self._write_slot(pipeline, "operator_request.md", "needs_operator")
            os.utime(pipeline / "operator_request.md", (base_time + 0.1, base_time + 0.1))
            self._write_slot(pipeline, "claude_handoff.md", "implement")
            os.utime(pipeline / "claude_handoff.md", (base_time + 0.9, base_time + 0.9))
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertGreater(result["active"]["mtime"], result["stale"][0]["mtime"])


class TestParseControlSlotsWindowsBranch(unittest.TestCase):
    """Exercise the IS_WINDOWS / _run branch via mocking."""

    def test_windows_find_printf_produces_subsecond_mtime(self):
        """find -printf '%T@' produces real sub-second epoch floats on WSL."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            (pipeline / "claude_handoff.md").write_text("STATUS: implement\n")
            (pipeline / "operator_request.md").write_text("STATUS: needs_operator\n")

            find_count = {"n": 0}
            # Real find -printf '%T@\n' output: epoch seconds with fractional nanoseconds
            find_responses = {
                "claude_handoff.md": "1712700000.5000000000",
                "operator_request.md": "1712700000.1000000000",
            }

            def fake_run(cmd, **kwargs):
                if isinstance(cmd, list) and cmd[0] == "find":
                    find_count["n"] += 1
                    for fname, resp in find_responses.items():
                        if fname in str(cmd[1]):
                            return 0, resp + "\n"
                    return 1, ""
                if isinstance(cmd, list) and cmd[0] == "head":
                    for fname in find_responses:
                        if fname in str(cmd[-1]):
                            return 0, (pipeline / fname).read_text()
                    return 1, ""
                return 1, ""

            with mock.patch("pipeline_gui.backend.IS_WINDOWS", True), \
                 mock.patch("pipeline_gui.backend._run", side_effect=fake_run), \
                 mock.patch("pipeline_gui.backend._wsl_path_str", side_effect=str):
                result = parse_control_slots(project)

            self.assertGreater(find_count["n"], 0, "find must be called on Windows path")
            self.assertIsNotNone(result["active"])
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertAlmostEqual(result["active"]["mtime"], 1712700000.5, places=1)
            self.assertEqual(len(result["stale"]), 1)
            self.assertEqual(result["stale"][0]["file"], "operator_request.md")

    def test_windows_find_same_second_resolved_by_fractional(self):
        """Same integer second but different fractional part must pick the newer slot."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            (pipeline / "claude_handoff.md").write_text("STATUS: implement\n")
            (pipeline / "gemini_request.md").write_text("STATUS: request_open\n")

            find_responses = {
                "claude_handoff.md": "1712700000.2000000000",
                "gemini_request.md": "1712700000.8000000000",
            }

            def fake_run(cmd, **kwargs):
                if isinstance(cmd, list) and cmd[0] == "find":
                    for fname, resp in find_responses.items():
                        if fname in str(cmd[1]):
                            return 0, resp + "\n"
                    return 1, ""
                if isinstance(cmd, list) and cmd[0] == "head":
                    for fname in find_responses:
                        if fname in str(cmd[-1]):
                            return 0, (pipeline / fname).read_text()
                    return 1, ""
                return 1, ""

            with mock.patch("pipeline_gui.backend.IS_WINDOWS", True), \
                 mock.patch("pipeline_gui.backend._run", side_effect=fake_run), \
                 mock.patch("pipeline_gui.backend._wsl_path_str", side_effect=str):
                result = parse_control_slots(project)

            self.assertEqual(result["active"]["file"], "gemini_request.md")
            self.assertAlmostEqual(result["active"]["mtime"], 1712700000.8, places=1)


class TestPipelineStartLaunchGate(unittest.TestCase):
    def test_pipeline_start_blocks_when_active_profile_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            with mock.patch("pipeline_gui.backend.resolve_project_runtime_file") as resolve_file, \
                 mock.patch("pipeline_gui.backend.subprocess.Popen") as popen:
                message = pipeline_start(project)
            self.assertIn("실행 차단:", message)
            self.assertIn("active profile이 없습니다", message)
            self.assertIn(".pipeline/config/agent_profile.json", message)
            resolve_file.assert_not_called()
            popen.assert_not_called()

    def test_pipeline_start_blocks_when_active_profile_launch_is_disallowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            active_path = project / ".pipeline" / "config" / "agent_profile.json"
            active_path.parent.mkdir(parents=True, exist_ok=True)
            active_path.write_text(
                (
                    '{"schema_version":1,"selected_agents":["Codex"],'
                    '"role_bindings":{"implement":"Codex","verify":"Codex","advisory":""},'
                    '"role_options":{"advisory_enabled":false,"operator_stop_enabled":true,"session_arbitration_enabled":false},'
                    '"mode_flags":{"single_agent_mode":true,"self_verify_allowed":false,"self_advisory_allowed":false}}'
                ),
                encoding="utf-8",
            )
            with mock.patch("pipeline_gui.backend.resolve_project_runtime_file") as resolve_file, \
                 mock.patch("pipeline_gui.backend.subprocess.Popen") as popen:
                message = pipeline_start(project)
            self.assertIn("실행 차단:", message)
            self.assertIn("implement and verify cannot share", message)
            resolve_file.assert_not_called()
            popen.assert_not_called()

    def test_pipeline_start_allows_experimental_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            active_path = project / ".pipeline" / "config" / "agent_profile.json"
            active_path.parent.mkdir(parents=True, exist_ok=True)
            active_path.write_text(
                (
                    '{"schema_version":1,"selected_agents":["Codex"],'
                    '"role_bindings":{"implement":"Codex","verify":"Codex","advisory":""},'
                    '"role_options":{"advisory_enabled":false,"operator_stop_enabled":true,"session_arbitration_enabled":false},'
                    '"mode_flags":{"single_agent_mode":true,"self_verify_allowed":true,"self_advisory_allowed":false}}'
                ),
                encoding="utf-8",
            )
            log_dir = project / ".pipeline" / "logs" / "experimental"
            script = project / "start-pipeline.sh"
            script.write_text("#!/bin/bash\n", encoding="utf-8")
            with mock.patch("pipeline_gui.backend.resolve_project_runtime_file", return_value=script), \
                 mock.patch("pipeline_gui.backend.IS_WINDOWS", False), \
                 mock.patch("pipeline_gui.backend.subprocess.Popen") as popen:
                message = pipeline_start(project)
            self.assertEqual(message, "시작 요청됨")
            self.assertTrue(log_dir.exists())
            popen.assert_called_once()

    def test_pipeline_start_windows_branch_refreshes_start_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            active_path = project / ".pipeline" / "config" / "agent_profile.json"
            active_path.parent.mkdir(parents=True, exist_ok=True)
            active_path.write_text(
                (
                    '{"schema_version":1,"selected_agents":["Codex"],'
                    '"role_bindings":{"implement":"Codex","verify":"Codex","advisory":""},'
                    '"role_options":{"advisory_enabled":false,"operator_stop_enabled":true,"session_arbitration_enabled":false},'
                    '"mode_flags":{"single_agent_mode":true,"self_verify_allowed":true,"self_advisory_allowed":false}}'
                ),
                encoding="utf-8",
            )
            script = project / ".pipeline" / "gui-runtime" / "_data" / "start-pipeline.sh"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text("#!/bin/bash\n", encoding="utf-8")
            log_path = project / ".pipeline" / "logs" / "experimental" / "pipeline-launcher-start.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("stale\n", encoding="utf-8")
            with mock.patch("pipeline_gui.backend.resolve_project_runtime_file", return_value=script), \
                 mock.patch("pipeline_gui.backend.IS_WINDOWS", True), \
                 mock.patch("pipeline_gui.backend._windows_to_wsl_mount", return_value="/home/test/project/.pipeline/gui-runtime/_data/start-pipeline.sh"), \
                 mock.patch("pipeline_gui.backend._wsl_path_str", side_effect=lambda path: str(path)), \
                 mock.patch("pipeline_gui.backend.subprocess.Popen") as popen:
                message = pipeline_start(project, "aip-projectH")
            self.assertEqual(message, "시작 요청됨")
            self.assertEqual(log_path.read_text(encoding="utf-8"), "")
            popen.assert_called_once()


class TestFormatControlSummary(unittest.TestCase):
    """GUI text rendering from parsed control-slot summary."""

    def test_no_active(self):
        active_text, stale_text = format_control_summary({"active": None, "stale": []})
        self.assertEqual(active_text, "활성 제어: 없음")
        self.assertEqual(stale_text, "")

    def test_active_with_stale(self):
        parsed = {
            "active": {"file": "claude_handoff.md", "status": "implement", "label": "implement handoff", "mtime": 1.0},
            "stale": [{"file": "operator_request.md", "status": "needs_operator", "label": "operator wait", "mtime": 0.5}],
        }
        active_text, stale_text = format_control_summary(parsed)
        self.assertIn("implement handoff", active_text)
        self.assertIn("claude_handoff.md", active_text)
        self.assertIn("mtime fallback", active_text)
        self.assertIn("operator_request.md", stale_text)
        self.assertIn("비활성", stale_text)
        self.assertIn("mtime fallback", stale_text)

    def test_active_with_control_seq_shows_seq(self):
        parsed = {
            "active": {"file": "claude_handoff.md", "status": "implement", "label": "implement handoff", "mtime": 1.0, "control_seq": 5},
            "stale": [],
        }
        active_text, _ = format_control_summary(parsed)
        self.assertIn("seq 5", active_text)
        self.assertNotIn("mtime fallback", active_text)

    def test_stale_with_mixed_provenance(self):
        parsed = {
            "active": {"file": "claude_handoff.md", "status": "implement", "label": "implement handoff", "mtime": 1.0, "control_seq": 3},
            "stale": [
                {"file": "operator_request.md", "status": "needs_operator", "label": "operator wait", "mtime": 0.5, "control_seq": 2},
                {"file": "gemini_request.md", "status": "request_open", "label": "advisory request", "mtime": 0.3},
            ],
        }
        active_text, stale_text = format_control_summary(parsed)
        self.assertIn("seq 3", active_text)
        self.assertIn("operator_request.md (seq 2)", stale_text)
        self.assertIn("gemini_request.md (mtime fallback)", stale_text)

    def test_active_only_no_stale_text(self):
        parsed = {
            "active": {"file": "gemini_advice.md", "status": "advice_ready", "label": "verify follow-up", "mtime": 1.0},
            "stale": [],
        }
        _, stale_text = format_control_summary(parsed)
        self.assertEqual(stale_text, "")

    def test_verify_activity_overrides_active_slot_display(self):
        parsed = {
            "active": {"file": "claude_handoff.md", "status": "implement", "label": "implement handoff", "mtime": 1.0, "control_seq": 8},
            "stale": [],
        }
        verify_activity = {
            "status": "VERIFY_RUNNING",
            "label": "verify 실행 중",
            "artifact_name": "2026-04-09-docs-response-origin-summary-richness-family-closure.md",
        }
        active_text, stale_text = format_control_summary(parsed, verify_activity=verify_activity)
        self.assertIn("verify 실행 중", active_text)
        self.assertIn("family-closure.md", active_text)
        self.assertIn("claude_handoff.md", active_text)
        self.assertIn("seq 8", active_text)
        self.assertEqual(stale_text, "")


class TestCurrentVerifyActivity(unittest.TestCase):
    def test_current_verify_activity_picks_latest_running_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state_dir = project / ".pipeline" / "state"
            state_dir.mkdir(parents=True)
            older = state_dir / "older.json"
            newer = state_dir / "newer.json"
            older.write_text(
                '{"job_id":"job-old","status":"VERIFY_RUNNING","artifact_path":"/tmp/old.md","last_dispatch_at":10,"last_activity_at":11}',
                encoding="utf-8",
            )
            newer.write_text(
                '{"job_id":"job-new","status":"VERIFY_RUNNING","artifact_path":"/tmp/new.md","last_dispatch_at":20,"last_activity_at":21}',
                encoding="utf-8",
            )

            activity = current_verify_activity(project)

        self.assertIsNotNone(activity)
        self.assertEqual(activity["job_id"], "job-new")
        self.assertEqual(activity["status"], "VERIFY_RUNNING")
        self.assertEqual(activity["artifact_name"], "new.md")


class TestPipelineStartDiagnostics(unittest.TestCase):
    def test_watcher_log_snapshot_reads_log_once_and_reuses_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            raw_lines = [
                "2026-04-10T15:31:00 [INFO] watcher_core: WatcherCore v2.1 started",
                "2026-04-10T15:31:01 [INFO] watcher_core: initial turn: claude",
                "2026-04-10T15:31:02 [INFO] watcher_core: notify_implement_owner: seq=17",
                "2026-04-10T15:31:03 [INFO] watcher_core: suppressed duplicate line",
                "2026-04-10T15:31:04 [INFO] watcher_core: waiting_for_claude: baseline_files=980",
            ]
            with mock.patch("pipeline_gui.backend._read_log_lines", return_value=raw_lines) as read_lines:
                snapshot = watcher_log_snapshot(project, display_lines=2, summary_lines=3, hint_lines=4)

            read_lines.assert_called_once()
            self.assertEqual(
                snapshot["display_lines"],
                [
                    "2026-04-10T15:31:02 [INFO] watcher_core: notify_implement_owner: seq=17",
                    "2026-04-10T15:31:04 [INFO] watcher_core: waiting_for_claude: baseline_files=980",
                ],
            )
            self.assertEqual(snapshot["summary_lines"], raw_lines[-3:])
            self.assertEqual(snapshot["hint_lines"], raw_lines[-4:])

    def test_pipeline_start_failure_hint_prefers_meaningful_error_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            log_dir = project / ".pipeline" / "logs" / "experimental"
            log_dir.mkdir(parents=True, exist_ok=True)
            (log_dir / "pipeline-launcher-start.log").write_text(
                (
                    "\x1b[0;36m============================================\x1b[0m\n"
                    "  AI Pipeline Launcher  [mode: experimental]\n"
                    "  프로젝트: /tmp/project\n"
                    "Launch blocked: active profile이 없습니다 (.pipeline/config/agent_profile.json). 설정 탭에서 미리보기 생성 후 적용을 완료해 주세요.\n"
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                pipeline_start_failure_hint(project),
                "Launch blocked: active profile이 없습니다 (.pipeline/config/agent_profile.json). 설정 탭에서 미리보기 생성 후 적용을 완료해 주세요.",
            )

    def test_watcher_start_observed_requires_recent_log_and_start_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            log_dir = project / ".pipeline" / "logs" / "experimental"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "watcher.log"
            log_path.write_text(
                (
                    "2026-04-09T20:52:57 [INFO] watcher_core: WatcherCore v2.1 started\n"
                    "2026-04-09T20:53:05 [INFO] watcher_core: initial turn: claude\n"
                ),
                encoding="utf-8",
            )
            now = time.time()
            os.utime(log_path, (now, now))
            self.assertTrue(watcher_start_observed(project, not_before=now - 1.0))
            self.assertFalse(watcher_start_observed(project, not_before=now + 5.0))

    def test_watcher_start_observed_accepts_canonical_notify_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            log_dir = project / ".pipeline" / "logs" / "experimental"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "watcher.log"
            log_path.write_text(
                (
                    "2026-04-09T20:52:57 [INFO] watcher_core: WatcherCore v2.1 started\n"
                    "2026-04-09T20:53:05 [INFO] watcher_core: notify_advisory_owner: reason=startup_turn_gemini\n"
                ),
                encoding="utf-8",
            )
            now = time.time()
            os.utime(log_path, (now, now))
            self.assertTrue(watcher_start_observed(project, not_before=now - 1.0))

    def test_confirm_pipeline_start_accepts_runtime_ready_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            progress_updates: list[str] = []
            with (
                mock.patch(
                    "pipeline_gui.backend.read_runtime_status",
                    return_value={
                        "runtime_state": "RUNNING",
                        "watcher": {"alive": False, "pid": None},
                        "lanes": [{"name": "Claude", "state": "READY", "attachable": True}],
                    },
                ),
                mock.patch("pipeline_gui.backend.time.sleep", return_value=None),
            ):
                ok, message = confirm_pipeline_start(
                    project,
                    "aip-projectH",
                    start_requested_at=time.time(),
                    progress_callback=progress_updates.append,
                )
            self.assertTrue(ok)
            self.assertIn("파이프라인 시작 완료", message)
            self.assertEqual(progress_updates, [])

    def test_confirm_pipeline_start_does_not_treat_watcher_alive_as_ready_shortcut(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            with (
                mock.patch(
                    "pipeline_gui.backend.read_runtime_status",
                    return_value={
                        "runtime_state": "STARTING",
                        "watcher": {"alive": True, "pid": 11},
                        "lanes": [{"name": "Claude", "state": "READY", "attachable": True}],
                    },
                ),
                mock.patch("pipeline_gui.backend.pipeline_start_failure_hint", return_value=""),
                mock.patch("pipeline_gui.backend.time.sleep", return_value=None),
            ):
                ok, message = confirm_pipeline_start(
                    project,
                    "aip-projectH",
                    start_requested_at=time.time(),
                    timeout_seconds=2,
                )
            self.assertFalse(ok)
            self.assertIn("runtime READY 조건", message)

    def test_confirm_pipeline_start_returns_timeout_with_failure_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            progress_updates: list[str] = []
            with (
                mock.patch("pipeline_gui.backend.read_runtime_status", return_value=None),
                mock.patch("pipeline_gui.backend.pipeline_start_failure_hint", return_value="Launch blocked: Active profile is missing."),
                mock.patch("pipeline_gui.backend.time.sleep", return_value=None),
            ):
                ok, message = confirm_pipeline_start(
                    project,
                    "aip-projectH",
                    start_requested_at=time.time(),
                    progress_callback=progress_updates.append,
                )
            self.assertFalse(ok)
            self.assertIn("15초 안에 runtime READY 조건을 만족하지 못했습니다", message)
            self.assertIn("Launch blocked: Active profile is missing.", message)
            self.assertTrue(any("runtime STARTING 대기 중" in update for update in progress_updates))


class TestTurnStateRead(unittest.TestCase):
    def test_read_turn_state_returns_data(self) -> None:
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            turn_state = state_dir / "turn_state.json"
            turn_state.write_text(json.dumps({
                "state": "VERIFY_ACTIVE",
                "legacy_state": "CODEX_VERIFY",
                "entered_at": 1744300000.0,
                "reason": "work_needs_verify",
                "active_control_file": "claude_handoff.md",
                "active_control_seq": 17,
                "active_role": "verify",
                "active_lane": "Claude",
            }))

            from pipeline_gui.backend import read_turn_state
            result = read_turn_state(root)
            self.assertIsNotNone(result)
            self.assertEqual(result["state"], "VERIFY_ACTIVE")
            self.assertEqual(result["legacy_state"], "CODEX_VERIFY")

    def test_read_turn_state_returns_none_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from pipeline_gui.backend import read_turn_state
            result = read_turn_state(root)
            self.assertIsNone(result)

    def test_format_control_summary_uses_turn_state(self) -> None:
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "turn_state.json").write_text(json.dumps({
                "state": "VERIFY_ACTIVE",
                "legacy_state": "CODEX_VERIFY",
                "entered_at": 1744300000.0,
                "reason": "work_needs_verify",
                "active_control_file": "claude_handoff.md",
                "active_control_seq": 17,
                "active_role": "verify",
                "active_lane": "Claude",
            }))

            from pipeline_gui.backend import read_turn_state
            turn = read_turn_state(root)
            parsed: dict[str, object] = {"active": None, "stale": []}
            active_text, _ = format_control_summary(parsed, turn_state=turn)
            self.assertIn("Claude 검증 중", active_text)

    def test_format_control_summary_falls_back_without_turn_state(self) -> None:
        parsed: dict[str, object] = {"active": None, "stale": []}
        active_text, _ = format_control_summary(parsed, turn_state=None)
        self.assertIn("없음", active_text)


class TestRuntimeStatusRead(unittest.TestCase):
    def test_read_runtime_status_from_current_run_pointer(self) -> None:
        import json

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                        "events_path": ".pipeline/runs/20260411T010203Z-p123/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "RUNNING",
                        "control": {
                            "active_control_file": ".pipeline/claude_handoff.md",
                            "active_control_seq": 17,
                            "active_control_status": "implement",
                            "active_control_updated_at": "2026-04-11T01:02:03Z",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch("pipeline_gui.backend._supervisor_pid", return_value=999),
                mock.patch("pipeline_gui.backend._pid_is_alive", side_effect=lambda pid: pid == 999),
            ):
                result = read_runtime_status(root)
            self.assertIsNotNone(result)
            self.assertEqual(result["run_id"], "20260411T010203Z-p123")
            self.assertEqual(result["runtime_state"], "RUNNING")

    def test_read_runtime_status_returns_none_without_current_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(read_runtime_status(root))

    def test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing(self) -> None:
        import json
        from pipeline_runtime.schema import parse_iso_utc

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            updated_at = "2026-04-11T01:02:03Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "RUNNING",
                        "updated_at": updated_at,
                        "degraded_reason": "",
                        "degraded_reasons": [],
                        "control": {
                            "active_control_file": ".pipeline/claude_handoff.md",
                            "active_control_seq": 17,
                            "active_control_status": "implement",
                            "active_control_updated_at": updated_at,
                        },
                        "lanes": [
                            {
                                "name": "Claude",
                                "state": "READY",
                                "note": "prompt_visible",
                                "attachable": True,
                                "pid": 4243,
                            }
                        ],
                        "active_round": {
                            "job_id": "job-1",
                            "round": 1,
                            "state": "VERIFYING",
                        },
                        "watcher": {
                            "alive": True,
                            "pid": 4242,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pipeline_gui.backend.time.time", return_value=parse_iso_utc(updated_at) + 20.0):
                result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "BROKEN")
            self.assertEqual(result["degraded_reason"], "supervisor_missing")
            self.assertIn("supervisor_missing", result["degraded_reasons"])
            self.assertEqual(result["control"]["active_control_status"], "none")
            self.assertEqual(result["control"]["active_control_seq"], -1)
            self.assertIsNone(result["active_round"])
            self.assertEqual(result["lanes"][0]["state"], "BROKEN")
            self.assertEqual(result["lanes"][0]["note"], "supervisor_missing")
            self.assertIsNone(result["lanes"][0]["pid"])
            self.assertFalse(result["lanes"][0]["attachable"])
            self.assertEqual(result["watcher"]["alive"], False)
            self.assertIsNone(result["watcher"]["pid"])

    def test_read_runtime_status_converts_stopping_without_supervisor_into_stopped(self) -> None:
        import json
        from pipeline_runtime.schema import parse_iso_utc

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            updated_at = "2026-04-11T01:02:03Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "STOPPING",
                        "updated_at": updated_at,
                        "degraded_reason": "",
                        "degraded_reasons": [],
                        "control": {
                            "active_control_file": ".pipeline/claude_handoff.md",
                            "active_control_seq": 17,
                            "active_control_status": "implement",
                            "active_control_updated_at": updated_at,
                        },
                        "lanes": [
                            {
                                "name": "Claude",
                                "state": "READY",
                                "note": "prompt_visible",
                                "attachable": True,
                                "pid": 4243,
                            }
                        ],
                        "active_round": {
                            "job_id": "job-1",
                            "round": 1,
                            "state": "VERIFYING",
                        },
                        "watcher": {
                            "alive": True,
                            "pid": 4242,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pipeline_gui.backend.time.time", return_value=parse_iso_utc(updated_at) + 1.0):
                result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "STOPPED")
            self.assertEqual(result["degraded_reason"], "")
            self.assertEqual(result["degraded_reasons"], [])
            self.assertEqual(result["control"]["active_control_status"], "none")
            self.assertEqual(result["control"]["active_control_seq"], -1)
            self.assertIsNone(result["active_round"])
            self.assertEqual(result["lanes"][0]["state"], "OFF")
            self.assertEqual(result["lanes"][0]["note"], "stopped")
            self.assertIsNone(result["lanes"][0]["pid"])
            self.assertFalse(result["lanes"][0]["attachable"])
            self.assertEqual(result["watcher"]["alive"], False)
            self.assertIsNone(result["watcher"]["pid"])

    def test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing(self) -> None:
        import json
        from pipeline_runtime.schema import parse_iso_utc

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            updated_at = "2026-04-11T01:02:03Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "BROKEN",
                        "updated_at": updated_at,
                        "degraded_reason": "auth_login_required",
                        "degraded_reasons": ["auth_login_required"],
                        "control": {
                            "active_control_file": ".pipeline/claude_handoff.md",
                            "active_control_seq": 17,
                            "active_control_status": "implement",
                            "active_control_updated_at": updated_at,
                        },
                        "lanes": [
                            {
                                "name": "Claude",
                                "state": "BROKEN",
                                "note": "auth_login_required",
                                "attachable": True,
                                "pid": 4243,
                            }
                        ],
                        "active_round": {
                            "job_id": "job-1",
                            "round": 1,
                            "state": "VERIFYING",
                        },
                        "watcher": {
                            "alive": True,
                            "pid": 4242,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pipeline_gui.backend.time.time", return_value=parse_iso_utc(updated_at) + 1.0):
                result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "BROKEN")
            self.assertEqual(result["degraded_reason"], "supervisor_missing")
            self.assertIn("supervisor_missing", result["degraded_reasons"])
            self.assertEqual(result["control"]["active_control_status"], "none")
            self.assertEqual(result["control"]["active_control_seq"], -1)
            self.assertIsNone(result["active_round"])
            self.assertEqual(result["lanes"][0]["state"], "BROKEN")
            self.assertEqual(result["lanes"][0]["note"], "supervisor_missing")
            self.assertIsNone(result["lanes"][0]["pid"])
            self.assertFalse(result["lanes"][0]["attachable"])
            self.assertEqual(result["watcher"]["alive"], False)
            self.assertIsNone(result["watcher"]["pid"])

    def test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor(self) -> None:
        import json
        from pipeline_runtime.schema import parse_iso_utc

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            updated_at = "2026-04-11T01:02:03Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "RUNNING",
                        "updated_at": updated_at,
                        "degraded_reason": "",
                        "degraded_reasons": [],
                        "control": {
                            "active_control_file": ".pipeline/claude_handoff.md",
                            "active_control_seq": 17,
                            "active_control_status": "implement",
                            "active_control_updated_at": updated_at,
                        },
                        "lanes": [
                            {
                                "name": "Claude",
                                "state": "READY",
                                "note": "prompt_visible",
                                "attachable": True,
                                "pid": 4243,
                            }
                        ],
                        "active_round": {
                            "job_id": "job-1",
                            "round": 1,
                            "state": "VERIFYING",
                        },
                        "watcher": {
                            "alive": True,
                            "pid": 4242,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch("pipeline_gui.backend.time.time", return_value=parse_iso_utc(updated_at) + 1.0),
                mock.patch("pipeline_gui.backend._pid_is_alive", side_effect=lambda pid: False),
            ):
                result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "BROKEN")
            self.assertEqual(result["degraded_reason"], "supervisor_missing")
            self.assertIn("supervisor_missing", result["degraded_reasons"])
            self.assertEqual(result["control"]["active_control_status"], "none")
            self.assertEqual(result["control"]["active_control_seq"], -1)
            self.assertIsNone(result["active_round"])
            self.assertEqual(result["lanes"][0]["state"], "BROKEN")
            self.assertEqual(result["lanes"][0]["note"], "supervisor_missing")
            self.assertIsNone(result["lanes"][0]["pid"])
            self.assertFalse(result["lanes"][0]["attachable"])
            self.assertEqual(result["watcher"]["alive"], False)
            self.assertIsNone(result["watcher"]["pid"])

    def test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids(self) -> None:
        import json
        from pipeline_runtime.schema import parse_iso_utc

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            updated_at = "2026-04-11T01:02:03Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "RUNNING",
                        "updated_at": updated_at,
                        "degraded_reason": "",
                        "degraded_reasons": [],
                        "control": {
                            "active_control_file": "",
                            "active_control_seq": -1,
                            "active_control_status": "none",
                            "active_control_updated_at": "",
                        },
                        "lanes": [
                            {
                                "name": "Claude",
                                "state": "OFF",
                                "note": "stopped",
                                "attachable": False,
                                "pid": None,
                            }
                        ],
                        "active_round": None,
                        "watcher": {
                            "alive": False,
                            "pid": None,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pipeline_gui.backend.time.time", return_value=parse_iso_utc(updated_at) + 1.0):
                result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "BROKEN")
            self.assertEqual(result["degraded_reason"], "supervisor_missing")
            self.assertIn("supervisor_missing", result["degraded_reasons"])
            self.assertEqual(result["control"]["active_control_status"], "none")
            self.assertEqual(result["control"]["active_control_seq"], -1)
            self.assertIsNone(result["active_round"])
            self.assertEqual(result["lanes"][0]["state"], "OFF")
            self.assertEqual(result["lanes"][0]["note"], "supervisor_missing")
            self.assertIsNone(result["lanes"][0]["pid"])
            self.assertFalse(result["lanes"][0]["attachable"])
            self.assertEqual(result["watcher"]["alive"], False)
            self.assertIsNone(result["watcher"]["pid"])

    def test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous(self) -> None:
        import json
        from pipeline_runtime.schema import parse_iso_utc

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            updated_at = "2026-04-11T01:02:03Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "RUNNING",
                        "updated_at": updated_at,
                        "lanes": [
                            {
                                "name": "Claude",
                                "state": "READY",
                                "note": "prompt_visible",
                                "attachable": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pipeline_gui.backend.time.time", return_value=parse_iso_utc(updated_at) + 10.0):
                result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "DEGRADED")
            self.assertEqual(result["degraded_reason"], "supervisor_missing_recent_ambiguous")
            self.assertIn("supervisor_missing_recent_ambiguous", result["degraded_reasons"])
            self.assertEqual(result["lanes"][0]["state"], "READY")

    def test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken(self) -> None:
        import json
        from pipeline_runtime.schema import parse_iso_utc

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            updated_at = "2026-04-11T01:02:03Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "RUNNING",
                        "updated_at": updated_at,
                        "control": {
                            "active_control_file": ".pipeline/claude_handoff.md",
                            "active_control_seq": 17,
                            "active_control_status": "implement",
                            "active_control_updated_at": updated_at,
                        },
                        "lanes": [
                            {
                                "name": "Claude",
                                "state": "READY",
                                "note": "prompt_visible",
                                "attachable": True,
                                "pid": None,
                            }
                        ],
                        "active_round": {
                            "job_id": "job-1",
                            "round": 1,
                            "state": "VERIFYING",
                        },
                        "watcher": {
                            "alive": False,
                            "pid": None,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pipeline_gui.backend.time.time", return_value=parse_iso_utc(updated_at) + 20.0):
                result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "BROKEN")
            self.assertEqual(result["degraded_reason"], "supervisor_missing")
            self.assertEqual(result["control"]["active_control_status"], "none")
            self.assertIsNone(result["active_round"])
            self.assertEqual(result["lanes"][0]["state"], "BROKEN")
            self.assertEqual(result["lanes"][0]["note"], "supervisor_missing")
            self.assertEqual(result["watcher"]["alive"], False)

    def test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive(self) -> None:
        import json
        from pipeline_runtime.schema import parse_iso_utc

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            updated_at = "2026-04-11T01:02:03Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "RUNNING",
                        "updated_at": updated_at,
                        "control": {
                            "active_control_file": ".pipeline/claude_handoff.md",
                            "active_control_seq": 17,
                            "active_control_status": "implement",
                            "active_control_updated_at": updated_at,
                        },
                        "lanes": [
                            {
                                "name": "Claude",
                                "state": "READY",
                                "note": "prompt_visible",
                                "attachable": True,
                                "pid": None,
                            }
                        ],
                        "active_round": {
                            "job_id": "job-1",
                            "round": 1,
                            "state": "VERIFYING",
                        },
                        "watcher": {
                            "alive": False,
                            "pid": None,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch("pipeline_gui.backend.time.time", return_value=parse_iso_utc(updated_at) + 10.0),
                mock.patch("pipeline_gui.backend._supervisor_pid", return_value=999),
                mock.patch("pipeline_gui.backend._pid_is_alive", side_effect=lambda pid: pid == 999),
            ):
                result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "RUNNING")
            self.assertEqual(result["control"]["active_control_status"], "implement")
            self.assertEqual(result["lanes"][0]["state"], "READY")

    def test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded(self) -> None:
        import json

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "RUNNING",
                        "control": {
                            "active_control_file": ".pipeline/claude_handoff.md",
                            "active_control_seq": 17,
                            "active_control_status": "implement",
                            "active_control_updated_at": "",
                        },
                        "lanes": [
                            {
                                "name": "Claude",
                                "state": "READY",
                                "note": "prompt_visible",
                                "attachable": True,
                                "pid": None,
                            }
                        ],
                        "active_round": {
                            "job_id": "job-1",
                            "round": 1,
                            "state": "VERIFYING",
                        },
                        "watcher": {
                            "alive": True,
                            "pid": None,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "DEGRADED")
            self.assertEqual(result["degraded_reason"], "supervisor_missing_snapshot_undated")
            self.assertIn("supervisor_missing_snapshot_undated", result["degraded_reasons"])
            self.assertEqual(result["control"]["active_control_status"], "implement")
            self.assertEqual(result["watcher"]["alive"], True)

    def test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous(self) -> None:
        import json
        from pipeline_runtime.schema import parse_iso_utc

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            updated_at = "2026-04-11T01:02:03Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": "20260411T010203Z-p123",
                        "runtime_state": "RUNNING",
                        "updated_at": updated_at,
                        "control": {
                            "active_control_file": "",
                            "active_control_seq": -1,
                            "active_control_status": "none",
                            "active_control_updated_at": "",
                        },
                        "lanes": [],
                        "active_round": None,
                        "watcher": {
                            "alive": True,
                            "pid": None,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pipeline_gui.backend.time.time", return_value=parse_iso_utc(updated_at) + 5.0):
                result = read_runtime_status(root)

            self.assertIsNotNone(result)
            self.assertEqual(result["runtime_state"], "DEGRADED")
            self.assertEqual(result["degraded_reason"], "supervisor_missing_recent_ambiguous")
            self.assertIn("supervisor_missing_recent_ambiguous", result["degraded_reasons"])
            self.assertEqual(result["watcher"]["alive"], True)

    def test_normalize_runtime_status_drops_non_mapping_payload(self) -> None:
        self.assertEqual(normalize_runtime_status("broken-payload"), {})
        self.assertEqual(normalize_runtime_status(None), {})
        normalized = normalize_runtime_status({"runtime_state": "RUNNING"})
        self.assertEqual(normalized["runtime_state"], "RUNNING")
        self.assertEqual(normalized["automation_health"], "ok")
        self.assertFalse(normalized["stale_control_seq"])

    def test_normalize_runtime_status_converts_inactive_degraded_snapshot_to_stopped(self) -> None:
        result = normalize_runtime_status(
            {
                "runtime_state": "DEGRADED",
                "degraded_reason": "dispatch_stall",
                "degraded_reasons": ["dispatch_stall"],
                "control": {
                    "active_control_file": ".pipeline/claude_handoff.md",
                    "active_control_seq": 252,
                    "active_control_status": "implement",
                    "active_control_updated_at": "2026-04-17T03:52:41Z",
                },
                "active_round": {
                    "job_id": "job-1",
                    "round": 1,
                    "state": "CLOSED",
                },
                "watcher": {
                    "alive": False,
                    "pid": None,
                },
                "lanes": [
                    {
                        "name": "Claude",
                        "state": "OFF",
                        "attachable": False,
                        "pid": None,
                        "note": "stopped",
                    },
                    {
                        "name": "Codex",
                        "state": "OFF",
                        "attachable": False,
                        "pid": None,
                        "note": "stopped",
                    },
                ],
            }
        )

        self.assertEqual(result["runtime_state"], "STOPPED")
        self.assertEqual(result["degraded_reason"], "")
        self.assertEqual(result["degraded_reasons"], [])
        self.assertEqual(result["control"]["active_control_status"], "none")
        self.assertIsNone(result["active_round"])


if __name__ == "__main__":
    unittest.main()
