from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest import mock

from pipeline_runtime.tmux_adapter import TmuxAdapter


class TestTmuxAdapter(unittest.TestCase):
    def test_run_returns_failed_completed_process_on_timeout(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")
        cmd = ["tmux", "list-panes"]

        def fake_run(
            _cmd: list[str],
            *,
            capture_output: bool,
            text: bool,
            timeout: float,
        ) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired(_cmd, timeout, output="partial", stderr="slow tmux")

        with mock.patch("pipeline_runtime.tmux_adapter.subprocess.run", side_effect=fake_run):
            result = adapter._run(cmd, timeout=0.1)

        self.assertEqual(result.args, cmd)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "partial")
        self.assertIn("slow tmux", result.stderr)

    def test_create_scaffold_uses_explicit_detached_session_size(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")
        calls: list[list[str]] = []
        split_count = 0

        def fake_run(cmd: list[str], *, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
            nonlocal split_count
            calls.append(cmd)
            if cmd[:3] == ["tmux", "new-session", "-d"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if cmd[:2] == ["tmux", "display-message"]:
                return subprocess.CompletedProcess(cmd, 0, "%0\n", "")
            if cmd[:2] == ["tmux", "split-window"]:
                pane_id = f"%{split_count + 1}"
                split_count += 1
                return subprocess.CompletedProcess(cmd, 0, f"{pane_id}\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            mock.patch.object(adapter, "kill_session", return_value=True),
            mock.patch.object(adapter, "_run", side_effect=fake_run),
        ):
            panes = adapter.create_scaffold()

        new_session = calls[0]
        self.assertEqual(new_session[:3], ["tmux", "new-session", "-d"])
        self.assertIn("-x", new_session)
        self.assertIn(str(adapter.DEFAULT_SESSION_COLS), new_session)
        self.assertIn("-y", new_session)
        self.assertIn(str(adapter.DEFAULT_SESSION_ROWS), new_session)
        self.assertEqual(panes, {"Claude": "%0", "Codex": "%1", "Gemini": "%2"})

    def test_create_scaffold_sets_window_size_manual(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")
        calls: list[list[str]] = []
        split_count = 0

        def fake_run(cmd: list[str], *, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
            nonlocal split_count
            calls.append(cmd)
            if cmd[:3] == ["tmux", "new-session", "-d"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if cmd[:2] == ["tmux", "display-message"]:
                return subprocess.CompletedProcess(cmd, 0, "%0\n", "")
            if cmd[:2] == ["tmux", "split-window"]:
                pane_id = f"%{split_count + 1}"
                split_count += 1
                return subprocess.CompletedProcess(cmd, 0, f"{pane_id}\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            mock.patch.object(adapter, "kill_session", return_value=True),
            mock.patch.object(adapter, "_run", side_effect=fake_run),
        ):
            adapter.create_scaffold()

        window_size_cmds = [
            c for c in calls
            if len(c) >= 6
            and c[:2] == ["tmux", "set-option"]
            and "window-size" in c
            and "manual" in c
        ]
        self.assertEqual(len(window_size_cmds), 1, "expected exactly one window-size manual set-option call")

    def test_create_scaffold_raises_on_required_option_failure(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")
        split_count = 0

        def fake_run(cmd: list[str], *, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
            nonlocal split_count
            if cmd[:3] == ["tmux", "new-session", "-d"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if cmd[:2] == ["tmux", "display-message"]:
                return subprocess.CompletedProcess(cmd, 0, "%0\n", "")
            if cmd[:2] == ["tmux", "split-window"]:
                pane_id = f"%{split_count + 1}"
                split_count += 1
                return subprocess.CompletedProcess(cmd, 0, f"{pane_id}\n", "")
            if "window-size" in cmd and "manual" in cmd:
                return subprocess.CompletedProcess(cmd, 1, "", "unknown option: window-size")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            mock.patch.object(adapter, "kill_session", return_value=True),
            mock.patch.object(adapter, "_run", side_effect=fake_run),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                adapter.create_scaffold()
            self.assertIn("window-size manual", str(ctx.exception))
            self.assertIn("unknown option", str(ctx.exception))

    def test_create_scaffold_rolls_back_partial_session_on_required_failure(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")

        def fake_run(cmd: list[str], *, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
            if cmd[:3] == ["tmux", "new-session", "-d"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if "window-size" in cmd and "manual" in cmd:
                return subprocess.CompletedProcess(cmd, 1, "", "unknown option: window-size")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            mock.patch.object(adapter, "kill_session", return_value=True) as kill_session,
            mock.patch.object(adapter, "_run", side_effect=fake_run),
        ):
            with self.assertRaises(RuntimeError):
                adapter.create_scaffold()

        self.assertEqual(kill_session.call_count, 2)

    def test_create_scaffold_tolerates_cosmetic_option_failure(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")
        split_count = 0

        def fake_run(cmd: list[str], *, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
            nonlocal split_count
            if cmd[:3] == ["tmux", "new-session", "-d"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if cmd[:2] == ["tmux", "display-message"]:
                return subprocess.CompletedProcess(cmd, 0, "%0\n", "")
            if cmd[:2] == ["tmux", "split-window"]:
                pane_id = f"%{split_count + 1}"
                split_count += 1
                return subprocess.CompletedProcess(cmd, 0, f"{pane_id}\n", "")
            if "status-style" in cmd:
                return subprocess.CompletedProcess(cmd, 1, "", "bad style")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            mock.patch.object(adapter, "kill_session", return_value=True),
            mock.patch.object(adapter, "_run", side_effect=fake_run),
        ):
            panes = adapter.create_scaffold()
        self.assertEqual(panes, {"Claude": "%0", "Codex": "%1", "Gemini": "%2"})

    def test_create_scaffold_raises_on_split_window_failure(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")

        def fake_run(cmd: list[str], *, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
            if cmd[:3] == ["tmux", "new-session", "-d"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if cmd[:2] == ["tmux", "display-message"]:
                return subprocess.CompletedProcess(cmd, 0, "%0\n", "")
            if cmd[:2] == ["tmux", "split-window"]:
                return subprocess.CompletedProcess(cmd, 1, "", "no space for new pane")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            mock.patch.object(adapter, "kill_session", return_value=True),
            mock.patch.object(adapter, "_run", side_effect=fake_run),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                adapter.create_scaffold()
            self.assertIn("split Codex pane", str(ctx.exception))
            self.assertIn("no space for new pane", str(ctx.exception))

    def test_create_scaffold_raises_on_empty_base_pane_id(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")

        def fake_run(cmd: list[str], *, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
            if cmd[:3] == ["tmux", "new-session", "-d"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if cmd[:2] == ["tmux", "display-message"]:
                return subprocess.CompletedProcess(cmd, 0, "\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            mock.patch.object(adapter, "kill_session", return_value=True),
            mock.patch.object(adapter, "_run", side_effect=fake_run),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                adapter.create_scaffold()
            self.assertIn("base pane id", str(ctx.exception))
            self.assertIn("empty pane id", str(ctx.exception))

    def test_create_scaffold_raises_on_select_layout_failure(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")
        split_count = 0

        def fake_run(cmd: list[str], *, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
            nonlocal split_count
            if cmd[:3] == ["tmux", "new-session", "-d"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if cmd[:2] == ["tmux", "display-message"]:
                return subprocess.CompletedProcess(cmd, 0, "%0\n", "")
            if cmd[:2] == ["tmux", "split-window"]:
                pane_id = f"%{split_count + 1}"
                split_count += 1
                return subprocess.CompletedProcess(cmd, 0, f"{pane_id}\n", "")
            if cmd[:2] == ["tmux", "select-layout"]:
                return subprocess.CompletedProcess(cmd, 1, "", "layout failed")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            mock.patch.object(adapter, "kill_session", return_value=True),
            mock.patch.object(adapter, "_run", side_effect=fake_run),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                adapter.create_scaffold()
            self.assertIn("select-layout", str(ctx.exception))

    def test_restart_lane_kills_then_spawns_lane(self) -> None:
        adapter = TmuxAdapter(Path("/tmp/projectH"), "projectH-test")
        calls: list[tuple[str, str]] = []

        def fake_kill(lane_name: str) -> bool:
            calls.append(("kill", lane_name))
            return True

        def fake_spawn(lane_name: str, shell_command: str) -> bool:
            calls.append(("spawn", lane_name))
            self.assertEqual(shell_command, "run-codex")
            return True

        with (
            mock.patch.object(adapter, "kill_lane", side_effect=fake_kill),
            mock.patch.object(adapter, "spawn_lane", side_effect=fake_spawn),
        ):
            self.assertTrue(adapter.restart_lane("Codex", "run-codex"))

        self.assertEqual(calls, [("kill", "Codex"), ("spawn", "Codex")])


if __name__ == "__main__":
    unittest.main()
