from __future__ import annotations

import os
import select
import socket
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from watcher_pty_adapter import PtyAdapter


class FakeProcess:
    _next_pid = 32000

    def __init__(self) -> None:
        type(self)._next_pid += 1
        self.pid = type(self)._next_pid
        self.returncode: int | None = None

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        if self.returncode is None:
            self.returncode = -15
        return self.returncode


class SocketPtyHarness:
    def __init__(self) -> None:
        self.child_fds: list[int] = []
        self.processes: list[FakeProcess] = []
        self.popen_calls: list[dict[str, object]] = []

    def openpty(self) -> tuple[int, int]:
        master, slave = socket.socketpair()
        self.child_fds.append(os.dup(slave.fileno()))
        return master.detach(), slave.detach()

    def popen(self, *args: object, **kwargs: object) -> FakeProcess:
        process = FakeProcess()
        self.processes.append(process)
        self.popen_calls.append({"args": args, "kwargs": kwargs})
        return process

    def killpg(self, pid: int, _signal_number: int) -> None:
        for process in self.processes:
            if process.pid == pid:
                process.returncode = -15
        for fd in list(self.child_fds):
            try:
                os.close(fd)
            except OSError:
                pass

    def close(self) -> None:
        for fd in list(self.child_fds):
            try:
                os.close(fd)
            except OSError:
                pass


class PtyAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.tempdir.name)
        self.harness = SocketPtyHarness()
        self.patches = [
            patch("watcher_pty_adapter.pty.openpty", side_effect=self.harness.openpty),
            patch("watcher_pty_adapter.subprocess.Popen", side_effect=self.harness.popen),
            patch("watcher_pty_adapter.os.killpg", side_effect=self.harness.killpg),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.addCleanup(self.harness.close)
        self.addCleanup(self.tempdir.cleanup)

    def _adapter(self) -> PtyAdapter:
        return PtyAdapter(self.project_root, "test-session")

    def _wait_for_capture(self, adapter: PtyAdapter, lane_name: str, expected: str) -> str:
        deadline = time.time() + 1.0
        captured = ""
        while time.time() < deadline:
            captured = adapter.capture_tail(lane_name)
            if expected in captured:
                return captured
            time.sleep(0.01)
        return captured

    def test_spawn_lane_starts_subprocess_and_marks_alive(self) -> None:
        adapter = self._adapter()

        self.assertTrue(adapter.spawn_lane("Codex", "python3 -i"))

        health = adapter.lane_health("Codex")
        self.assertTrue(health["alive"])
        self.assertIsInstance(health["pid"], int)
        self.assertIsNone(health["exit_code"])
        kwargs = self.harness.popen_calls[0]["kwargs"]
        self.assertEqual(kwargs["cwd"], str(self.project_root))
        self.assertEqual(kwargs["stdin"], kwargs["stdout"])
        self.assertEqual(kwargs["stdout"], kwargs["stderr"])

    def test_capture_tail_returns_subprocess_output(self) -> None:
        adapter = self._adapter()
        self.assertTrue(adapter.spawn_lane("Codex", "python3 -i"))

        os.write(self.harness.child_fds[-1], b"one\r\ntwo\nthree\n")

        captured = self._wait_for_capture(adapter, "Codex", "three")
        self.assertEqual(captured, "one\ntwo\nthree")
        self.assertEqual(adapter.capture_tail("Codex", lines=2), "two\nthree")

    def test_send_input_writes_bytes_to_master_fd(self) -> None:
        adapter = self._adapter()
        self.assertTrue(adapter.spawn_lane("Codex", "python3 -i"))

        self.assertTrue(adapter.send_input("Codex", "status\n"))

        ready, _, _ = select.select([self.harness.child_fds[-1]], [], [], 1.0)
        self.assertTrue(ready)
        self.assertEqual(os.read(self.harness.child_fds[-1], 7), b"status\n")

    def test_kill_lane_terminates_subprocess_and_marks_not_alive(self) -> None:
        adapter = self._adapter()
        self.assertTrue(adapter.spawn_lane("Codex", "python3 -i"))

        self.assertTrue(adapter.kill_lane("Codex"))

        health = adapter.lane_health("Codex")
        self.assertFalse(health["alive"])
        self.assertEqual(health["exit_code"], -15)
        self.assertFalse(adapter.session_exists())

    def test_restart_lane_kills_and_respawns(self) -> None:
        adapter = self._adapter()
        self.assertTrue(adapter.spawn_lane("Codex", "first"))
        first_pid = adapter.lane_health("Codex")["pid"]

        self.assertTrue(adapter.restart_lane("Codex", "second"))

        second_pid = adapter.lane_health("Codex")["pid"]
        self.assertNotEqual(first_pid, second_pid)
        self.assertEqual(len(self.harness.processes), 2)
        self.assertTrue(adapter.session_exists())

    def test_session_exists_returns_true_when_any_lane_is_alive(self) -> None:
        adapter = self._adapter()
        self.assertFalse(adapter.session_exists())

        self.assertTrue(adapter.spawn_lane("Codex", "python3 -i"))
        self.assertTrue(adapter.session_exists())

        self.assertTrue(adapter.kill_lane("Codex"))
        self.assertFalse(adapter.session_exists())

    def test_missing_lane_health_returns_expected_keys(self) -> None:
        adapter = self._adapter()

        self.assertEqual(
            adapter.lane_health("missing"),
            {"name": "missing", "alive": False, "pid": None, "exit_code": None},
        )


if __name__ == "__main__":
    unittest.main()
