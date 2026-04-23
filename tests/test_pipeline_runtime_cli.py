from __future__ import annotations

import json
import os
import io
import signal
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

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

    def test_codex_queue_prompt_emits_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sent: list[bytes] = []
            emitter = _WrapperEmitter(
                wrapper_dir=Path(tmp),
                lane_name="Codex",
                task_hint_dir=None,
                child_pid=456,
                send_child_bytes=sent.append,
            )

            emitter.feed("tab to queue message\n55% context left\n")

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
                        "dispatch_id": "dispatch-42",
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
            wrapper_log = root / "claude.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "DISPATCH_SEEN"', log_text)
            self.assertIn('"dispatch_id": "dispatch-42"', log_text)

            emitter.feed("● Now let me inspect the file.\n❯\n", now=1.0)

            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "TASK_ACCEPTED"', log_text)
            self.assertIn('"dispatch_id": "dispatch-42"', log_text)
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)

            emitter.tick(now=2.0)
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)

            emitter.feed("❯\n", now=3.0)
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "TASK_DONE"', log_text)
            self.assertIn('"dispatch_id": "dispatch-42"', log_text)
            self.assertGreaterEqual(log_text.count('"event_type": "READY"'), 2)
            self.assertEqual(log_text.count('"event_type": "DISPATCH_SEEN"'), 1)

    def test_dispatch_seen_emits_before_accept_without_activity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            (task_hint_dir / "claude.json").write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": True,
                        "job_id": "job-99",
                        "dispatch_id": "dispatch-99",
                        "control_seq": 211,
                        "attempt": 1,
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

            wrapper_log = root / "claude.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "DISPATCH_SEEN"', log_text)
            self.assertNotIn('"event_type": "TASK_ACCEPTED"', log_text)

    def test_codex_bullet_activity_emits_task_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            (task_hint_dir / "codex.json").write_text(
                json.dumps(
                    {
                        "lane": "Codex",
                        "active": True,
                        "job_id": "job-codex-accept",
                        "dispatch_id": "dispatch-codex-accept",
                        "control_seq": 347,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Codex",
                task_hint_dir=task_hint_dir,
                child_pid=793,
                send_child_bytes=lambda _data: None,
            )

            emitter.feed("OpenAI Codex\n› Type your message\n", now=0.0)
            emitter.feed("• Exploring the workspace before changing files\n", now=1.0)

            wrapper_log = root / "codex.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "DISPATCH_SEEN"', log_text)
            self.assertIn('"event_type": "TASK_ACCEPTED"', log_text)
            self.assertIn('"dispatch_id": "dispatch-codex-accept"', log_text)

    def test_codex_working_status_line_emits_task_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            (task_hint_dir / "codex.json").write_text(
                json.dumps(
                    {
                        "lane": "Codex",
                        "active": True,
                        "job_id": "job-codex-working",
                        "dispatch_id": "dispatch-codex-working",
                        "control_seq": 349,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Codex",
                task_hint_dir=task_hint_dir,
                child_pid=794,
                send_child_bytes=lambda _data: None,
            )

            emitter.feed("OpenAI Codex\n› Type your message\n", now=0.0)
            emitter.feed("• Working (22s • esc to interrupt)\n", now=1.0)

            wrapper_log = root / "codex.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "DISPATCH_SEEN"', log_text)
            self.assertIn('"event_type": "TASK_ACCEPTED"', log_text)
            self.assertIn('"dispatch_id": "dispatch-codex-working"', log_text)
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)

    def test_active_task_hint_with_invalid_control_seq_emits_bridge_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            (task_hint_dir / "claude.json").write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": True,
                        "job_id": "job-invalid-seq",
                        "dispatch_id": "dispatch-invalid-seq",
                        "control_seq": -1,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=791,
                send_child_bytes=lambda _data: None,
            )

            emitter.feed("Claude Code\n❯\n", now=0.0)

            wrapper_log = root / "claude.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "BRIDGE_DIAGNOSTIC"', log_text)
            self.assertIn('"code": "active_task_hint_metadata_invalid"', log_text)
            self.assertNotIn('"event_type": "DISPATCH_SEEN"', log_text)

    def test_active_task_hint_with_non_numeric_control_seq_emits_bridge_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            (task_hint_dir / "claude.json").write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": True,
                        "job_id": "job-invalid-seq-text",
                        "dispatch_id": "dispatch-invalid-seq-text",
                        "control_seq": "none",
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=792,
                send_child_bytes=lambda _data: None,
            )

            emitter.feed("Claude Code\n❯\n", now=0.0)

            wrapper_log = root / "claude.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "BRIDGE_DIAGNOSTIC"', log_text)
            self.assertIn('"code": "active_task_hint_metadata_invalid"', log_text)
            self.assertIn('"detail": "control_seq_missing_for_active_dispatch"', log_text)
            self.assertNotIn('"event_type": "DISPATCH_SEEN"', log_text)

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
                        "dispatch_id": "dispatch-154",
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
            self.assertEqual(task_done[0]["payload"]["dispatch_id"], "dispatch-154")
            self.assertEqual(task_done[0]["payload"]["reason"], "duplicate_handoff")


class SupervisorCliTest(unittest.TestCase):
    def test_status_json_reads_current_run_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            run_dir = project_root / ".pipeline" / "runs" / "run-status"
            run_dir.mkdir(parents=True, exist_ok=True)
            (project_root / ".pipeline" / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-status",
                        "status_path": ".pipeline/runs/run-status/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps({"run_id": "run-status", "runtime_state": "RUNNING"}),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with patch("sys.stdout", stdout):
                code = runtime_cli._status(Namespace(project_root=str(project_root), json=True))

            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["runtime_state"], "RUNNING")
            self.assertEqual(payload["current_run"]["run_id"], "run-status")

    def test_doctor_json_reports_ready_project_without_current_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            (project_root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
            profile_path = project_root / ".pipeline" / "config" / "agent_profile.json"
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(
                json.dumps(
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
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            adapter = Mock()
            adapter.session_exists.return_value = False

            with (
                patch.object(runtime_cli, "_find_cli_bin", return_value=True),
                patch.object(runtime_cli, "_list_supervisor_pids", return_value=[]),
                patch.object(runtime_cli, "TmuxAdapter", return_value=adapter),
                patch("sys.stdout", stdout),
            ):
                code = runtime_cli._doctor(
                    Namespace(project_root=str(project_root), session="aip-test", json=True)
                )

            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["read_only"])
            checks = {item["name"]: item for item in payload["checks"]}
            self.assertEqual(checks["runtime_status"]["status"], "ok")
            self.assertIn("No current run yet", checks["runtime_status"]["detail"])
            self.assertEqual(checks["agent_cli:codex"]["status"], "ok")

    def test_doctor_fails_when_active_profile_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            (project_root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
            stdout = io.StringIO()
            adapter = Mock()
            adapter.session_exists.return_value = False

            with (
                patch.object(runtime_cli, "_find_cli_bin", return_value=True),
                patch.object(runtime_cli, "_list_supervisor_pids", return_value=[]),
                patch.object(runtime_cli, "TmuxAdapter", return_value=adapter),
                patch("sys.stdout", stdout),
            ):
                code = runtime_cli._doctor(
                    Namespace(project_root=str(project_root), session="aip-test", json=True)
                )

            self.assertEqual(code, 1)
            payload = json.loads(stdout.getvalue())
            checks = {item["name"]: item for item in payload["checks"]}
            self.assertEqual(checks["active_profile"]["status"], "fail")
            self.assertIn("미리보기 생성 후 적용", checks["active_profile"]["detail"])

    def test_doctor_warns_on_stale_current_run_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            (project_root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
            profile_path = project_root / ".pipeline" / "config" / "agent_profile.json"
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(
                json.dumps(
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
                    }
                ),
                encoding="utf-8",
            )
            (project_root / ".pipeline" / "current_run.json").write_text(
                json.dumps({"run_id": "missing-run", "status_path": ".pipeline/runs/missing-run/status.json"}),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            adapter = Mock()
            adapter.session_exists.return_value = False

            with (
                patch.object(runtime_cli, "_find_cli_bin", return_value=True),
                patch.object(runtime_cli, "_list_supervisor_pids", return_value=[]),
                patch.object(runtime_cli, "TmuxAdapter", return_value=adapter),
                patch("sys.stdout", stdout),
            ):
                code = runtime_cli._doctor(
                    Namespace(project_root=str(project_root), session="aip-test", json=True)
                )

            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            checks = {item["name"]: item for item in payload["checks"]}
            self.assertEqual(checks["runtime_status"]["status"], "warn")
            self.assertIn("current_run points to missing", checks["runtime_status"]["detail"])

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

    def test_runtime_source_newer_than_supervisor_pidfile_requests_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            source_path = project_root / "watcher_core.py"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("1234", encoding="utf-8")
            source_path.write_text("# updated watcher\n", encoding="utf-8")
            old_ts = 10.0
            new_ts = 20.0
            os.utime(pid_path, (old_ts, old_ts))
            os.utime(source_path, (new_ts, new_ts))

            self.assertTrue(runtime_cli._runtime_source_newer_than_supervisor_pidfile(project_root))

    def test_spawn_supervisor_replaces_live_daemon_when_runtime_source_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            args = Namespace(
                project_root=str(project_root),
                legacy_mode="",
                mode="experimental",
                session="aip-projectH",
            )
            process = Mock()
            process.poll.return_value = None
            process.returncode = None

            with (
                patch.object(runtime_cli, "_runtime_source_newer_than_supervisor_pidfile", return_value=True),
                patch.object(runtime_cli, "_reconcile_supervisors", return_value=1234),
                patch.object(runtime_cli, "_stop_supervisor", return_value=0) as stop_supervisor,
                patch.object(runtime_cli.time, "sleep", return_value=None),
                patch.object(runtime_cli, "RuntimeSupervisor", return_value=Mock(run_id="run-fresh")),
                patch.object(runtime_cli.subprocess, "Popen", return_value=process) as popen,
                patch.object(runtime_cli, "_current_run_matches", return_value=True),
            ):
                code = runtime_cli._spawn_supervisor(args)

            self.assertEqual(code, 0)
            stop_supervisor.assert_called_once_with(args)
            popen.assert_called_once()

    def test_spawn_supervisor_keeps_live_daemon_when_runtime_source_is_not_newer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            args = Namespace(
                project_root=str(project_root),
                legacy_mode="",
                mode="experimental",
                session="aip-projectH",
            )

            with (
                patch.object(runtime_cli, "_runtime_source_newer_than_supervisor_pidfile", return_value=False),
                patch.object(runtime_cli, "_reconcile_supervisors", return_value=1234),
                patch.object(runtime_cli, "_stop_supervisor") as stop_supervisor,
                patch.object(runtime_cli.subprocess, "Popen") as popen,
            ):
                code = runtime_cli._spawn_supervisor(args)

            self.assertEqual(code, 0)
            stop_supervisor.assert_not_called()
            popen.assert_not_called()

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

    def test_stop_supervisor_cleans_orphan_runtime_when_supervisor_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("111", encoding="utf-8")
            args = Namespace(project_root=str(project_root), legacy_mode="", session="aip-projectH")

            with (
                patch.object(runtime_cli, "_list_supervisor_pids", return_value=[]),
                patch.object(runtime_cli, "_supervisor_running", return_value=None),
                patch.object(runtime_cli, "_orphan_runtime_needs_cleanup", return_value=True),
                patch.object(runtime_cli, "_cleanup_orphan_runtime") as cleanup,
            ):
                code = runtime_cli._stop_supervisor(args)

            self.assertEqual(code, 0)
            cleanup.assert_called_once_with(project_root, "aip-projectH")
            self.assertFalse(pid_path.exists())

    def test_coerce_status_to_stopped_clears_live_runtime_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            run_dir = project_root / ".pipeline" / "runs" / "run-1"
            run_dir.mkdir(parents=True, exist_ok=True)
            current_run = project_root / ".pipeline" / "current_run.json"
            current_run.parent.mkdir(parents=True, exist_ok=True)
            current_run.write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "status_path": ".pipeline/runs/run-1/status.json",
                    }
                ),
                encoding="utf-8",
            )
            status_path = run_dir / "status.json"
            task_hint_dir = run_dir / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            (task_hint_dir / "claude.json").write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": True,
                        "job_id": "job-1",
                        "dispatch_id": "dispatch-1",
                        "control_seq": 197,
                        "attempt": 2,
                        "inactive_reason": "",
                    }
                ),
                encoding="utf-8",
            )
            status_path.write_text(
                json.dumps(
                    {
                        "runtime_state": "STOPPING",
                        "degraded_reason": "dispatch_stall",
                        "degraded_reasons": ["dispatch_stall", "session_missing"],
                        "control": {
                            "active_control_file": ".pipeline/operator_request.md",
                            "active_control_seq": 197,
                            "active_control_status": "needs_operator",
                            "active_control_updated_at": "2026-04-16T10:40:00Z",
                        },
                        "active_round": {"state": "CLOSED", "job_id": "job-1"},
                        "watcher": {"alive": True, "pid": 123},
                        "lanes": [
                            {"name": "Claude", "state": "READY", "pid": 11, "attachable": True, "note": "prompt_visible"}
                        ],
                        "autonomy": {"mode": "recovery", "block_reason": "verified_blockers_resolved"},
                    }
                ),
                encoding="utf-8",
            )

            runtime_cli._coerce_status_to_stopped(project_root)

            repaired = json.loads(status_path.read_text(encoding="utf-8"))
            repaired_hint = json.loads((task_hint_dir / "claude.json").read_text(encoding="utf-8"))
            self.assertEqual(repaired["runtime_state"], "STOPPED")
            self.assertEqual(repaired["degraded_reason"], "")
            self.assertEqual(repaired["degraded_reasons"], [])
            self.assertEqual(repaired["control"]["active_control_status"], "none")
            self.assertIsNone(repaired["active_round"])
            self.assertEqual(repaired["watcher"], {"alive": False, "pid": None})
            self.assertEqual(repaired["autonomy"]["mode"], "normal")
            self.assertEqual(repaired["lanes"][0]["state"], "OFF")
            self.assertEqual(repaired["lanes"][0]["pid"], None)
            self.assertFalse(repaired_hint["active"])
            self.assertEqual(repaired_hint["job_id"], "")
            self.assertEqual(repaired_hint["dispatch_id"], "")
            self.assertEqual(repaired_hint["control_seq"], -1)
            self.assertEqual(repaired_hint["inactive_reason"], "runtime_stopped")
