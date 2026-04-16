from __future__ import annotations

import json
import signal
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pipeline_runtime.cli as runtime_cli
from pipeline_runtime.cli import _WrapperEmitter


class WrapperEmitterTest(unittest.TestCase):
    def test_codex_update_prompt_is_auto_dismissed_with_skip_until_next_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sent: list[bytes] = []
            emitter = _WrapperEmitter(
                wrapper_dir=Path(tmp),
                lane_name="Codex",
                task_hint_dir=None,
                child_pid=123,
                send_child_bytes=sent.append,
            )

            emitter.feed(
                "\n".join(
                    [
                        "✨ Update available! 0.1",
                        "› 1. Update now (runs `npm install -g @openai/codex`)",
                        "2. Skip",
                        "3. Skip until next version",
                    ]
                )
                + "\n"
            )

            self.assertEqual(sent, [b"3\r"])
            wrapper_log = Path(tmp) / "codex.jsonl"
            if wrapper_log.exists():
                self.assertNotIn("READY", wrapper_log.read_text(encoding="utf-8"))

            emitter.feed(
                "\n".join(
                    [
                        "✨ Update available! 0.1",
                        "› 1. Update now (runs `npm install -g @openai/codex`)",
                        "2. Skip",
                        "3. Skip until next version",
                    ]
                )
                + "\n"
            )
            self.assertEqual(sent, [b"3\r"])

    def test_codex_update_prompt_is_not_misclassified_as_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sent: list[bytes] = []
            emitter = _WrapperEmitter(
                wrapper_dir=Path(tmp),
                lane_name="Codex",
                task_hint_dir=None,
                child_pid=124,
                send_child_bytes=sent.append,
            )

            emitter.feed(
                "\n".join(
                    [
                        "✨ Update available! 0.121.0 -> 0.122.0",
                        "Release notes: https://github.com/openai/codex/releases/latest",
                        "› 1. Update now",
                        "2. Skip",
                        "3. Skip until next version",
                    ]
                )
                + "\n"
            )

            self.assertEqual(sent, [b"3\r"])
            wrapper_log = Path(tmp) / "codex.jsonl"
            if wrapper_log.exists():
                self.assertNotIn('"event_type": "READY"', wrapper_log.read_text(encoding="utf-8"))

    def test_codex_prompt_visible_emits_ready_when_not_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sent: list[bytes] = []
            emitter = _WrapperEmitter(
                wrapper_dir=Path(tmp),
                lane_name="Codex",
                task_hint_dir=None,
                child_pid=456,
                send_child_bytes=sent.append,
            )

            emitter.feed("OpenAI Codex\n› Type your message\n")

            self.assertEqual(sent, [])
            wrapper_log = Path(tmp) / "codex.jsonl"
            self.assertTrue(wrapper_log.exists())
            self.assertIn('"event_type": "READY"', wrapper_log.read_text(encoding="utf-8"))

    def test_task_accept_waits_for_settle_before_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            (task_hint_dir / "claude.json").write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": True,
                        "job_id": "job-42",
                        "control_seq": 135,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=789,
                send_child_bytes=lambda _data: None,
            )

            emitter.feed("Claude Code\n❯\n", now=0.0)
            emitter.feed("● Now let me inspect the file.\n❯\n", now=1.0)

            wrapper_log = root / "claude.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "TASK_ACCEPTED"', log_text)
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)

            emitter.tick(now=2.0)
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)

            emitter.feed("❯\n", now=3.0)
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)

            (task_hint_dir / "claude.json").write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": False,
                        "job_id": "",
                        "control_seq": -1,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            emitter.feed("❯\n", now=7.0)
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)

            emitter.tick(now=9.0)
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "TASK_DONE"', log_text)
            self.assertGreaterEqual(log_text.count('"event_type": "READY"'), 2)

    def test_duplicate_handoff_task_hint_closure_emits_reason_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            hint_path = task_hint_dir / "claude.json"
            hint_path.write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": True,
                        "job_id": "job-42",
                        "control_seq": 154,
                        "attempt": 1,
                        "inactive_reason": "",
                    }
                ),
                encoding="utf-8",
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=790,
                send_child_bytes=lambda _data: None,
            )

            emitter.feed("Claude Code\n❯\n", now=0.0)
            emitter.feed("● Now let me inspect the file.\n❯\n", now=1.0)
            hint_path.write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": False,
                        "job_id": "",
                        "control_seq": -1,
                        "attempt": 1,
                        "inactive_reason": "duplicate_handoff",
                    }
                ),
                encoding="utf-8",
            )

            emitter.feed("❯\n", now=4.0)
            emitter.tick(now=6.0)
            emitter.feed("❯\n", now=8.0)

            events = [
                json.loads(line)
                for line in (root / "claude.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            task_done = [event for event in events if event.get("event_type") == "TASK_DONE"]
            self.assertEqual(len(task_done), 1)
            self.assertEqual(task_done[0]["payload"]["reason"], "duplicate_handoff")


class SupervisorCliTest(unittest.TestCase):
    def test_list_supervisor_pids_filters_project_and_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_root = root / "project"
            project_root.mkdir(parents=True, exist_ok=True)
            proc_root = root / "proc"
            proc_root.mkdir(parents=True, exist_ok=True)

            def _write_cmdline(pid: int, argv: list[str]) -> None:
                proc_dir = proc_root / str(pid)
                proc_dir.mkdir(parents=True, exist_ok=True)
                (proc_dir / "cmdline").write_bytes(b"\0".join(item.encode("utf-8") for item in argv) + b"\0")

            _write_cmdline(
                101,
                [
                    "/usr/bin/python3",
                    "-m",
                    "pipeline_runtime.cli",
                    "daemon",
                    "--project-root",
                    str(project_root.resolve()),
                    "--session",
                    "aip-projectH",
                ],
            )
            _write_cmdline(
                102,
                [
                    "/usr/bin/python3",
                    "-m",
                    "pipeline_runtime.cli",
                    "daemon",
                    "--project-root",
                    str(project_root.resolve()),
                    "--session",
                    "other-session",
                ],
            )
            _write_cmdline(
                103,
                [
                    "/usr/bin/python3",
                    "-m",
                    "pipeline_runtime.cli",
                    "daemon",
                    "--project-root",
                    str((root / "other-project").resolve()),
                    "--session",
                    "aip-projectH",
                ],
            )

            pids = runtime_cli._list_supervisor_pids(project_root, "aip-projectH", proc_root=proc_root)
            self.assertEqual(pids, [101])

    def test_reconcile_supervisors_rewrites_pidfile_for_single_live_daemon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("999", encoding="utf-8")

            with patch.object(runtime_cli, "_list_supervisor_pids", return_value=[1234]):
                live_pid = runtime_cli._reconcile_supervisors(project_root, "aip-projectH")

            self.assertEqual(live_pid, 1234)
            self.assertEqual(pid_path.read_text(encoding="utf-8").strip(), "1234")

    def test_stop_supervisor_signals_duplicate_live_daemons_and_waits_for_flush(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("111", encoding="utf-8")
            args = Namespace(project_root=str(project_root), legacy_mode="", session="aip-projectH")

            signaled: list[tuple[int, int]] = []
            with (
                patch.object(runtime_cli, "_list_supervisor_pids", return_value=[111, 222]),
                patch.object(runtime_cli, "_supervisor_running", return_value=111),
                patch.object(runtime_cli, "_signal_pid", side_effect=lambda pid, sig: signaled.append((pid, sig))),
                patch.object(runtime_cli, "_wait_for_stop_completion", return_value=True),
            ):
                code = runtime_cli._stop_supervisor(args)

            self.assertEqual(code, 0)
            self.assertEqual(signaled, [(111, signal.SIGTERM), (222, signal.SIGTERM)])
            self.assertFalse(pid_path.exists())

    def test_stop_supervisor_waits_for_graceful_stopped_status_flush(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("111", encoding="utf-8")
            args = Namespace(project_root=str(project_root), legacy_mode="", session="aip-projectH")

            signaled: list[tuple[int, int]] = []
            with (
                patch.object(runtime_cli, "_list_supervisor_pids", return_value=[111]),
                patch.object(runtime_cli, "_supervisor_running", return_value=111),
                patch.object(runtime_cli, "_signal_pid", side_effect=lambda pid, sig: signaled.append((pid, sig))),
                patch.object(runtime_cli, "_wait_for_stop_completion", return_value=True) as wait_stop,
            ):
                code = runtime_cli._stop_supervisor(args)

            self.assertEqual(code, 0)
            self.assertEqual(signaled, [(111, signal.SIGTERM)])
            wait_stop.assert_called_once_with(project_root, "aip-projectH")
            self.assertFalse(pid_path.exists())

    def test_stop_supervisor_returns_failure_when_graceful_flush_never_arrives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("111", encoding="utf-8")
            args = Namespace(project_root=str(project_root), legacy_mode="", session="aip-projectH")

            signaled: list[tuple[int, int]] = []
            killed: list[int] = []
            with (
                patch.object(runtime_cli, "_list_supervisor_pids", side_effect=[[111], [111]]),
                patch.object(runtime_cli, "_supervisor_running", return_value=111),
                patch.object(runtime_cli, "_signal_pid", side_effect=lambda pid, sig: signaled.append((pid, sig))),
                patch.object(runtime_cli, "_wait_for_stop_completion", return_value=False),
                patch.object(runtime_cli, "_kill_pid", side_effect=killed.append),
                patch.object(runtime_cli, "_wait_for_supervisors_exit", return_value=True),
            ):
                code = runtime_cli._stop_supervisor(args)

            self.assertEqual(code, 1)
            self.assertEqual(signaled, [(111, signal.SIGTERM)])
            self.assertEqual(killed, [111])
            self.assertFalse(pid_path.exists())
