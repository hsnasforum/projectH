from __future__ import annotations

import fcntl
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
    def _write_task_hint(
        self,
        task_hint_dir: Path,
        *,
        lane: str = "Claude",
        job_id: str = "job-jsonl",
        dispatch_id: str = "dispatch-jsonl",
        control_seq: int = 410,
        attempt: int = 1,
        active: bool = True,
    ) -> None:
        task_hint_dir.mkdir(parents=True, exist_ok=True)
        (task_hint_dir / f"{lane.lower()}.json").write_text(
            json.dumps(
                {
                    "lane": lane,
                    "active": active,
                    "job_id": job_id,
                    "dispatch_id": dispatch_id,
                    "control_seq": control_seq,
                    "attempt": attempt,
                }
            ),
            encoding="utf-8",
        )

    def _read_wrapper_events(self, path: Path) -> list[dict[str, object]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

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

    def test_codex_update_auto_dismiss_uses_parsed_number_not_hardcoded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sent: list[bytes] = []
            emitter = _WrapperEmitter(
                wrapper_dir=Path(tmp),
                lane_name="Codex",
                task_hint_dir=None,
                child_pid=125,
                send_child_bytes=sent.append,
            )

            emitter.feed(
                "\n".join(
                    [
                        "update available",
                        "1) Install now",
                        "2) skip until next version",
                        "3) Cancel",
                    ]
                )
                + "\n"
            )

            self.assertEqual(sent, [b"2\r"])

    def test_emit_task_done_falls_back_for_invalid_control_seq(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            emitter = _WrapperEmitter(
                wrapper_dir=Path(tmp),
                lane_name="Codex",
                task_hint_dir=None,
                child_pid=126,
                send_child_bytes=lambda _data: None,
            )
            emitter.accepted_key = "job-bad-seq|dispatch-bad|not-int|1"
            emitter.accepted_payload = {
                "job_id": "job-bad-seq",
                "dispatch_id": "dispatch-bad",
                "control_seq": object(),
            }

            emitter._emit_task_done()

            events = [
                json.loads(line)
                for line in (Path(tmp) / "codex.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            task_done = [event for event in events if event.get("event_type") == "TASK_DONE"]
            self.assertEqual(len(task_done), 1)
            self.assertEqual(task_done[0]["payload"]["control_seq"], -1)

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
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)
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

    def test_visible_busy_tail_emits_task_accepted_when_task_hint_arrives_after_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            hint_path = task_hint_dir / "claude.json"
            hint_path.write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": False,
                        "job_id": "",
                        "dispatch_id": "",
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
                child_pid=795,
                send_child_bytes=lambda _data: None,
            )

            emitter.feed("Working (synthetic claude verify)\n", now=0.0)
            hint_path.write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": True,
                        "job_id": "job-visible-busy",
                        "dispatch_id": "dispatch-visible-busy",
                        "control_seq": 352,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            emitter.tick(now=1.0)

            wrapper_log = root / "claude.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "DISPATCH_SEEN"', log_text)
            self.assertIn('"event_type": "TASK_ACCEPTED"', log_text)
            self.assertIn('"dispatch_id": "dispatch-visible-busy"', log_text)

    def test_ready_prompt_after_busy_tail_keeps_active_task_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            (task_hint_dir / "claude.json").write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": True,
                        "job_id": "job-busy-then-ready",
                        "dispatch_id": "dispatch-busy-then-ready",
                        "control_seq": 353,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=796,
                send_child_bytes=lambda _data: None,
            )

            emitter.feed("Working (synthetic claude verify)\n", now=0.0)
            emitter.feed("Claude Code\n❯\n", now=3.0)
            emitter.tick(now=5.0)

            wrapper_log = root / "claude.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "TASK_ACCEPTED"', log_text)
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)
            self.assertIn('"event_type": "READY"', log_text)
            self.assertIn('"dispatch_id": "dispatch-busy-then-ready"', log_text)

    def test_ready_prompt_without_trailing_newline_keeps_active_task_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            task_hint_dir.mkdir(parents=True, exist_ok=True)
            (task_hint_dir / "claude.json").write_text(
                json.dumps(
                    {
                        "lane": "Claude",
                        "active": True,
                        "job_id": "job-partial-ready",
                        "dispatch_id": "dispatch-partial-ready",
                        "control_seq": 354,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=797,
                send_child_bytes=lambda _data: None,
            )

            emitter.feed("Working (synthetic claude verify)\n", now=0.0)
            emitter.feed("Claude Code\n❯ ", now=3.0)
            emitter.tick(now=5.0)

            wrapper_log = root / "claude.jsonl"
            log_text = wrapper_log.read_text(encoding="utf-8")
            self.assertIn('"event_type": "TASK_ACCEPTED"', log_text)
            self.assertNotIn('"event_type": "TASK_DONE"', log_text)
            self.assertIn('"event_type": "READY"', log_text)
            self.assertIn('"dispatch_id": "dispatch-partial-ready"', log_text)

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

    def test_claude_jsonl_text_event_emits_task_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(task_hint_dir)
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=800,
                send_child_bytes=lambda _data: None,
                jsonl_mode=True,
            )

            emitter.feed(json.dumps({"type": "text", "text": "작업을 시작합니다."}) + "\n", now=1.0)

            events = self._read_wrapper_events(root / "claude.jsonl")
            event_types = [str(event.get("event_type") or "") for event in events]
            self.assertEqual(event_types, ["DISPATCH_SEEN", "TASK_ACCEPTED"])
            self.assertEqual(events[-1]["payload"]["dispatch_id"], "dispatch-jsonl")

    def test_claude_jsonl_tool_use_event_emits_task_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(
                task_hint_dir,
                job_id="job-tool",
                dispatch_id="dispatch-tool",
                control_seq=411,
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=801,
                send_child_bytes=lambda _data: None,
                jsonl_mode=True,
            )

            emitter.feed(
                json.dumps({"type": "tool_use", "id": "tool-1", "name": "Read", "input": {"file_path": "x"}})
                + "\n",
                now=1.0,
            )

            events = self._read_wrapper_events(root / "claude.jsonl")
            event_types = [str(event.get("event_type") or "") for event in events]
            self.assertEqual(event_types, ["DISPATCH_SEEN", "TASK_ACCEPTED"])
            self.assertEqual(events[-1]["payload"]["dispatch_id"], "dispatch-tool")

    def test_claude_jsonl_result_event_emits_task_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(
                task_hint_dir,
                job_id="job-result",
                dispatch_id="dispatch-result",
                control_seq=412,
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=802,
                send_child_bytes=lambda _data: None,
                jsonl_mode=True,
            )

            emitter.feed(json.dumps({"type": "text", "text": "done soon"}) + "\n", now=1.0)
            emitter.feed(json.dumps({"type": "result"}) + "\n", now=2.0)

            events = self._read_wrapper_events(root / "claude.jsonl")
            task_done = [event for event in events if event.get("event_type") == "TASK_DONE"]
            self.assertEqual(len(task_done), 1)
            self.assertEqual(task_done[0]["payload"]["dispatch_id"], "dispatch-result")
            self.assertEqual(task_done[0]["payload"]["reason"], "claude_result")
            self.assertEqual(events[-1]["event_type"], "READY")

    def test_claude_jsonl_stream_finish_emits_task_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(
                task_hint_dir,
                job_id="job-eof",
                dispatch_id="dispatch-eof",
                control_seq=413,
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=803,
                send_child_bytes=lambda _data: None,
                jsonl_mode=True,
            )

            emitter.feed(json.dumps({"type": "text", "text": "working"}) + "\n", now=1.0)
            emitter.finish_stream(now=2.0)

            events = self._read_wrapper_events(root / "claude.jsonl")
            task_done = [event for event in events if event.get("event_type") == "TASK_DONE"]
            self.assertEqual(len(task_done), 1)
            self.assertEqual(task_done[0]["payload"]["dispatch_id"], "dispatch-eof")
            self.assertEqual(task_done[0]["payload"]["reason"], "stream_eof")

    def test_text_stream_finish_emits_task_done_once_after_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(
                task_hint_dir,
                job_id="job-text-eof",
                dispatch_id="dispatch-text-eof",
                control_seq=419,
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=807,
                send_child_bytes=lambda _data: None,
                jsonl_mode=False,
            )

            emitter.finish_stream(now=0.5)
            emitter.feed("Working (synthetic claude verify)\n", now=1.0)
            emitter.finish_stream(now=2.0)
            emitter.finish_stream(now=3.0)

            events = self._read_wrapper_events(root / "claude.jsonl")
            event_types = [str(event.get("event_type") or "") for event in events]
            self.assertEqual(event_types, ["DISPATCH_SEEN", "TASK_ACCEPTED", "TASK_DONE", "READY"])
            task_done = [event for event in events if event.get("event_type") == "TASK_DONE"]
            self.assertEqual(len(task_done), 1)
            self.assertEqual(task_done[0]["payload"]["job_id"], "job-text-eof")
            self.assertEqual(task_done[0]["payload"]["dispatch_id"], "dispatch-text-eof")
            self.assertEqual(task_done[0]["payload"]["control_seq"], 419)
            self.assertEqual(task_done[0]["payload"]["reason"], "stream_eof")

    def test_jsonl_mode_false_keeps_codex_text_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(
                task_hint_dir,
                lane="Codex",
                job_id="job-codex-text",
                dispatch_id="dispatch-codex-text",
                control_seq=414,
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Codex",
                task_hint_dir=task_hint_dir,
                child_pid=804,
                send_child_bytes=lambda _data: None,
                jsonl_mode=False,
            )

            emitter.feed("OpenAI Codex\n› Type your message\n", now=0.0)
            emitter.feed("• Working (22s • esc to interrupt)\n", now=1.0)

            events = self._read_wrapper_events(root / "codex.jsonl")
            event_types = [str(event.get("event_type") or "") for event in events]
            self.assertIn("TASK_ACCEPTED", event_types)
            self.assertEqual(events[-1]["payload"]["dispatch_id"], "dispatch-codex-text")

    def test_claude_jsonl_invalid_output_falls_back_to_text_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(
                task_hint_dir,
                job_id="job-fallback",
                dispatch_id="dispatch-fallback",
                control_seq=415,
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=805,
                send_child_bytes=lambda _data: None,
                jsonl_mode=True,
            )

            emitter.feed("Working (stream-json unsupported fallback)\n", now=1.0)

            events = self._read_wrapper_events(root / "claude.jsonl")
            event_types = [str(event.get("event_type") or "") for event in events]
            self.assertFalse(emitter.jsonl_mode)
            self.assertIn("TASK_ACCEPTED", event_types)
            self.assertEqual(events[-1]["payload"]["dispatch_id"], "dispatch-fallback")

    def test_claude_print_jsonl_pipe_sends_prompt_and_feeds_stdout(self) -> None:
        class FakeStdin:
            def write(self, data: str) -> int:
                sent_inputs.append(data)
                return len(data)

            def close(self) -> None:
                return None

        class FakeProcess:
            pid = 991
            returncode = 0

            def __init__(self) -> None:
                stdout = "\n".join(
                    [
                        json.dumps({"type": "text", "text": "working"}),
                        json.dumps({"type": "result"}),
                    ]
                ) + "\n"
                self.stdin = FakeStdin()
                self.stdout = io.StringIO(stdout)
                self.stderr = io.StringIO("")

            def wait(self) -> int:
                return self.returncode

        sent_inputs: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(
                task_hint_dir,
                job_id="job-print-pipe",
                dispatch_id="dispatch-print-pipe",
                control_seq=416,
            )
            with patch.object(runtime_cli.subprocess, "Popen", return_value=FakeProcess()) as popen:
                returncode, stderr = runtime_cli._run_claude_print_jsonl_pipe(
                    prompt="respond with exactly: OK",
                    wrapper_dir=root,
                    task_hint_dir=task_hint_dir,
                    cwd=root,
                    now=3.0,
                )

            self.assertEqual(returncode, 0)
            self.assertEqual(stderr, "")
            self.assertEqual(sent_inputs, ["respond with exactly: OK"])
            popen.assert_called_once_with(
                ["claude", "--print", "--verbose", "--output-format", "stream-json"],
                stdin=runtime_cli.subprocess.PIPE,
                stdout=runtime_cli.subprocess.PIPE,
                stderr=runtime_cli.subprocess.PIPE,
                cwd=str(root),
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            events = self._read_wrapper_events(root / "claude.jsonl")
            event_types = [str(event.get("event_type") or "") for event in events]
            self.assertEqual(event_types, ["DISPATCH_SEEN", "TASK_ACCEPTED", "TASK_DONE", "READY"])
            self.assertEqual(events[1]["payload"]["dispatch_id"], "dispatch-print-pipe")
            self.assertEqual(events[2]["payload"]["reason"], "claude_result")

    def test_claude_jsonl_assistant_event_marks_task_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(
                task_hint_dir,
                job_id="job-assistant-event",
                dispatch_id="dispatch-assistant-event",
                control_seq=417,
            )
            emitter = _WrapperEmitter(
                wrapper_dir=root,
                lane_name="Claude",
                task_hint_dir=task_hint_dir,
                child_pid=806,
                send_child_bytes=lambda _data: None,
                jsonl_mode=True,
            )

            emitter.feed(json.dumps({"type": "assistant", "message": {"content": []}}) + "\n", now=5.0)

            events = self._read_wrapper_events(root / "claude.jsonl")
            event_types = [str(event.get("event_type") or "") for event in events]
            self.assertEqual(event_types, ["DISPATCH_SEEN", "TASK_ACCEPTED"])
            self.assertEqual(events[1]["payload"]["dispatch_id"], "dispatch-assistant-event")

    def test_claude_print_jsonl_pipe_returns_stderr_and_nonzero_exit(self) -> None:
        class FakeStdin:
            def write(self, data: str) -> int:
                sent_inputs.append(data)
                return len(data)

            def close(self) -> None:
                return None

        class FakeProcess:
            pid = 992
            returncode = None

            def __init__(self) -> None:
                self.stdin = FakeStdin()
                self.stdout = io.StringIO("")
                self.stderr = io.StringIO("warning from claude\n")

            def wait(self) -> int:
                self.returncode = 7
                return 7

        sent_inputs: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(runtime_cli.subprocess, "Popen", return_value=FakeProcess()):
                returncode, stderr = runtime_cli._run_claude_print_jsonl_pipe(
                    prompt="hello",
                    wrapper_dir=root,
                    task_hint_dir=None,
                    claude_bin="/custom/claude",
                    now=4.0,
                )

            self.assertEqual(returncode, 7)
            self.assertEqual(stderr, "warning from claude\n")
            self.assertEqual(sent_inputs, ["hello"])

    def test_claude_print_jsonl_pipe_from_prompt_file_accepts_local_utf8_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt_path = root / "prompts" / "claude.txt"
            wrapper_dir = root / "events"
            task_hint_dir = root / "task-hints"
            prompt_path.parent.mkdir(parents=True)
            prompt_path.write_text("respond with exactly: OK\n", encoding="utf-8")

            with patch.object(runtime_cli, "_run_claude_print_jsonl_pipe", return_value=(0, "")) as pipe:
                returncode, stderr = runtime_cli._run_claude_print_jsonl_pipe_from_prompt_file(
                    prompt_path=Path("prompts") / "claude.txt",
                    allowed_root=root,
                    wrapper_dir=wrapper_dir,
                    task_hint_dir=task_hint_dir,
                    now=5.0,
                )

            self.assertEqual(returncode, 0)
            self.assertEqual(stderr, "")
            pipe.assert_called_once_with(
                prompt="respond with exactly: OK\n",
                wrapper_dir=wrapper_dir,
                task_hint_dir=task_hint_dir,
                claude_bin="claude",
                cwd=root.resolve(),
                now=5.0,
            )

    def test_claude_print_jsonl_pipe_prompt_source_rejects_invalid_inputs_without_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "root"
            root.mkdir()
            (root / "dir-prompt").mkdir()
            (root / "empty.txt").write_text(" \n\t", encoding="utf-8")
            outside = base / "outside.txt"
            outside.write_text("outside", encoding="utf-8")

            cases = [
                ("missing.txt", "prompt_path_missing"),
                ("dir-prompt", "prompt_path_directory"),
                ("empty.txt", "prompt_empty"),
                (outside, "prompt_path_outside_root"),
            ]
            for prompt_path, expected_code in cases:
                with self.subTest(expected_code=expected_code):
                    with (
                        patch.object(runtime_cli, "_run_claude_print_jsonl_pipe") as pipe,
                        patch.object(runtime_cli.subprocess, "Popen") as popen,
                    ):
                        with self.assertRaises(runtime_cli.ClaudePrintPromptSourceError) as caught:
                            runtime_cli._run_claude_print_jsonl_pipe_from_prompt_file(
                                prompt_path=prompt_path,
                                allowed_root=root,
                                wrapper_dir=root / "events",
                                task_hint_dir=None,
                            )

                    self.assertEqual(caught.exception.code, expected_code)
                    pipe.assert_not_called()
                    popen.assert_not_called()

    def test_claude_print_jsonl_pipe_subcommand_calls_prompt_file_helper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            task_hint_dir = root / "task-hints"
            stderr_buffer = io.StringIO()
            with (
                patch.object(
                    runtime_cli,
                    "_run_claude_print_jsonl_pipe_from_prompt_file",
                    return_value=(7, "warning from claude\n"),
                ) as pipe,
                patch.object(runtime_cli.sys, "stderr", stderr_buffer),
            ):
                returncode = runtime_cli.main(
                    [
                        "claude-print-jsonl-pipe",
                        "--project-root",
                        str(root),
                        "--run-id",
                        "run-opt-in",
                        "--prompt-file",
                        "prompts/claude.txt",
                        "--task-hint-dir",
                        str(task_hint_dir),
                        "--claude-bin",
                        "/custom/claude",
                    ]
                )

            wrapper_dir = root / ".pipeline" / "runs" / "run-opt-in" / "wrapper-events"
            self.assertEqual(returncode, 7)
            self.assertEqual(stderr_buffer.getvalue(), "warning from claude\n")
            self.assertTrue(wrapper_dir.is_dir())
            pipe.assert_called_once_with(
                prompt_path="prompts/claude.txt",
                allowed_root=root,
                wrapper_dir=wrapper_dir,
                task_hint_dir=task_hint_dir.resolve(),
                claude_bin="/custom/claude",
                cwd=root,
            )

    def test_claude_print_jsonl_pipe_subcommand_fake_e2e_emits_wrapper_events(self) -> None:
        class FakeStdin:
            def write(self, data: str) -> int:
                sent_inputs.append(data)
                return len(data)

            def close(self) -> None:
                return None

        class FakeProcess:
            pid = 993
            returncode = 0

            def __init__(self) -> None:
                stdout = "\n".join(
                    [
                        json.dumps({"type": "text", "text": "working"}),
                        json.dumps({"type": "result"}),
                    ]
                ) + "\n"
                self.stdin = FakeStdin()
                self.stdout = io.StringIO(stdout)
                self.stderr = io.StringIO("")

            def wait(self) -> int:
                return self.returncode

        sent_inputs: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            prompt_path = root / "prompts" / "claude.txt"
            task_hint_dir = root / "task-hints"
            run_id = "run-fake-e2e"
            prompt_path.parent.mkdir(parents=True)
            prompt_path.write_text("respond with exactly: OK\n", encoding="utf-8")
            self._write_task_hint(
                task_hint_dir,
                job_id="job-print-e2e",
                dispatch_id="dispatch-print-e2e",
                control_seq=417,
            )

            with patch.object(runtime_cli.subprocess, "Popen", return_value=FakeProcess()) as popen:
                returncode = runtime_cli.main(
                    [
                        "claude-print-jsonl-pipe",
                        "--project-root",
                        str(root),
                        "--run-id",
                        run_id,
                        "--prompt-file",
                        "prompts/claude.txt",
                        "--task-hint-dir",
                        str(task_hint_dir),
                        "--claude-bin",
                        "/custom/claude",
                    ]
                )

            wrapper_dir = root / ".pipeline" / "runs" / run_id / "wrapper-events"
            self.assertEqual(returncode, 0)
            self.assertEqual(sent_inputs, ["respond with exactly: OK\n"])
            popen.assert_called_once_with(
                ["/custom/claude", "--print", "--verbose", "--output-format", "stream-json"],
                stdin=runtime_cli.subprocess.PIPE,
                stdout=runtime_cli.subprocess.PIPE,
                stderr=runtime_cli.subprocess.PIPE,
                cwd=str(root),
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            events = self._read_wrapper_events(wrapper_dir / "claude.jsonl")
            event_types = [str(event.get("event_type") or "") for event in events]
            self.assertEqual(event_types, ["DISPATCH_SEEN", "TASK_ACCEPTED", "TASK_DONE", "READY"])
            self.assertEqual(events[1]["payload"]["job_id"], "job-print-e2e")
            self.assertEqual(events[1]["payload"]["dispatch_id"], "dispatch-print-e2e")
            self.assertEqual(events[1]["payload"]["control_seq"], 417)
            self.assertEqual(events[2]["payload"]["reason"], "claude_result")

    def test_claude_print_jsonl_pipe_subcommand_rejects_prompt_source_without_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stderr_buffer = io.StringIO()
            with (
                patch.object(runtime_cli, "_run_claude_print_jsonl_pipe") as pipe,
                patch.object(runtime_cli.subprocess, "Popen") as popen,
                patch.object(runtime_cli.sys, "stderr", stderr_buffer),
            ):
                returncode = runtime_cli.main(
                    [
                        "claude-print-jsonl-pipe",
                        "--project-root",
                        str(root),
                        "--run-id",
                        "run-reject",
                        "--prompt-file",
                        "missing.txt",
                    ]
                )

            self.assertEqual(returncode, 2)
            self.assertIn("prompt_path_missing", stderr_buffer.getvalue())
            self.assertIn(str(root / "missing.txt"), stderr_buffer.getvalue())
            pipe.assert_not_called()
            popen.assert_not_called()

    def test_claude_print_jsonl_pipe_subcommand_rejection_with_task_hint_emits_bridge_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            task_hint_dir = root / "task-hints"
            stderr_buffer = io.StringIO()
            self._write_task_hint(
                task_hint_dir,
                job_id="job-reject-audit",
                dispatch_id="dispatch-reject-audit",
                control_seq=418,
            )
            with (
                patch.object(runtime_cli, "_run_claude_print_jsonl_pipe") as pipe,
                patch.object(runtime_cli.subprocess, "Popen") as popen,
                patch.object(runtime_cli.sys, "stderr", stderr_buffer),
            ):
                returncode = runtime_cli.main(
                    [
                        "claude-print-jsonl-pipe",
                        "--project-root",
                        str(root),
                        "--run-id",
                        "run-reject-audit",
                        "--prompt-file",
                        "missing.txt",
                        "--task-hint-dir",
                        str(task_hint_dir),
                    ]
                )

            wrapper_log = root / ".pipeline" / "runs" / "run-reject-audit" / "wrapper-events" / "claude.jsonl"
            events = self._read_wrapper_events(wrapper_log)
            self.assertEqual(returncode, 2)
            self.assertIn("prompt_path_missing", stderr_buffer.getvalue())
            self.assertEqual([event["event_type"] for event in events], ["BRIDGE_DIAGNOSTIC"])
            self.assertEqual(events[0]["derived_from"], "prompt_source_rejected")
            self.assertEqual(events[0]["payload"]["job_id"], "job-reject-audit")
            self.assertEqual(events[0]["payload"]["dispatch_id"], "dispatch-reject-audit")
            self.assertEqual(events[0]["payload"]["control_seq"], 418)
            self.assertEqual(events[0]["payload"]["code"], "prompt_path_missing")
            self.assertEqual(events[0]["payload"]["path"], str(root / "missing.txt"))
            pipe.assert_not_called()
            popen.assert_not_called()

    def test_claude_print_jsonl_pipe_subcommand_rejection_without_task_hint_emits_broken(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stderr_buffer = io.StringIO()
            with (
                patch.object(runtime_cli, "_run_claude_print_jsonl_pipe") as pipe,
                patch.object(runtime_cli.subprocess, "Popen") as popen,
                patch.object(runtime_cli.sys, "stderr", stderr_buffer),
            ):
                returncode = runtime_cli.main(
                    [
                        "claude-print-jsonl-pipe",
                        "--project-root",
                        str(root),
                        "--run-id",
                        "run-reject-no-hint",
                        "--prompt-file",
                        "missing.txt",
                    ]
                )

            wrapper_log = root / ".pipeline" / "runs" / "run-reject-no-hint" / "wrapper-events" / "claude.jsonl"
            events = self._read_wrapper_events(wrapper_log)
            self.assertEqual(returncode, 2)
            self.assertIn("prompt_path_missing", stderr_buffer.getvalue())
            self.assertEqual([event["event_type"] for event in events], ["BROKEN"])
            self.assertEqual(events[0]["derived_from"], "prompt_source_rejected")
            self.assertEqual(events[0]["payload"]["pid"], 0)
            self.assertEqual(events[0]["payload"]["reason"], "prompt_source_rejected")
            self.assertEqual(events[0]["payload"]["code"], "prompt_path_missing")
            self.assertEqual(events[0]["payload"]["path"], str(root / "missing.txt"))
            pipe.assert_not_called()
            popen.assert_not_called()

    def test_lane_wrapper_initializes_all_lanes_in_text_mode(self) -> None:
        class FakeChild:
            pid = 900

            def poll(self) -> int:
                return 0

            def wait(self) -> int:
                return 0

        class FakeEmitter:
            def __init__(
                self,
                *,
                wrapper_dir: Path,
                lane_name: str,
                task_hint_dir: Path | None,
                child_pid: int,
                send_child_bytes,
                jsonl_mode: bool = False,
            ) -> None:
                modes.append((lane_name, jsonl_mode))

            def tick(self, *, now: float | None = None) -> None:
                return None

            def feed(self, text: str, *, now: float | None = None) -> None:
                return None

            def finish_stream(self, *, now: float | None = None) -> None:
                return None

        modes: list[tuple[str, bool]] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for lane_name in ("Claude", "Codex", "Gemini"):
                master_fd, slave_fd = os.pipe()
                args = Namespace(
                    project_root=str(root),
                    run_id=f"run-{lane_name.lower()}",
                    lane=lane_name,
                    shell_command="true",
                    task_hint_dir="",
                    heartbeat_interval=1.0,
                )
                with (
                    patch.object(runtime_cli.pty, "openpty", return_value=(master_fd, slave_fd)),
                    patch.object(runtime_cli.subprocess, "Popen", return_value=FakeChild()),
                    patch.object(runtime_cli, "_WrapperEmitter", FakeEmitter),
                    patch.object(runtime_cli.signal, "signal"),
                ):
                    self.assertEqual(runtime_cli._lane_wrapper(args), 0)

        self.assertEqual(modes, [("Claude", False), ("Codex", False), ("Gemini", False)])

    def test_lane_wrapper_finishes_stream_once_when_signal_requests_stop(self) -> None:
        class FakeChild:
            pid = 901

            def poll(self) -> None:
                return None

            def wait(self) -> int:
                return 0

        class FakeEmitter:
            def __init__(
                self,
                *,
                wrapper_dir: Path,
                lane_name: str,
                task_hint_dir: Path | None,
                child_pid: int,
                send_child_bytes,
                jsonl_mode: bool = False,
            ) -> None:
                return None

            def tick(self, *, now: float | None = None) -> None:
                return None

            def feed(self, text: str, *, now: float | None = None) -> None:
                return None

            def finish_stream(self, *, now: float | None = None) -> None:
                finish_calls.append(now)

        class FakeSelector:
            def register(self, _fd: int, _events: int) -> None:
                return None

            def select(self, timeout: float | None = None) -> list[tuple[object, object]]:
                if not signal_sent:
                    signal_sent.append(True)
                    handlers[signal.SIGTERM](signal.SIGTERM, None)
                return []

            def close(self) -> None:
                closed.append(True)

        handlers = {}
        signal_sent: list[bool] = []
        finish_calls: list[float | None] = []
        closed: list[bool] = []
        child = FakeChild()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            master_fd, slave_fd = os.pipe()
            args = Namespace(
                project_root=str(root),
                run_id="run-sigterm",
                lane="Claude",
                shell_command="sleep 10",
                task_hint_dir="",
                heartbeat_interval=1.0,
            )

            def _capture_signal(sig: int, handler) -> None:
                handlers[sig] = handler

            with (
                patch.object(runtime_cli.pty, "openpty", return_value=(master_fd, slave_fd)),
                patch.object(runtime_cli.subprocess, "Popen", return_value=child),
                patch.object(runtime_cli, "_WrapperEmitter", FakeEmitter),
                patch.object(runtime_cli.selectors, "DefaultSelector", return_value=FakeSelector()),
                patch.object(runtime_cli.signal, "signal", side_effect=_capture_signal),
                patch.object(runtime_cli.os, "killpg") as killpg,
            ):
                self.assertEqual(runtime_cli._lane_wrapper(args), 0)

        self.assertEqual(len(finish_calls), 1)
        self.assertEqual(signal_sent, [True])
        self.assertEqual(closed, [True])
        killpg.assert_called_once_with(child.pid, signal.SIGTERM)

    def test_lane_wrapper_signal_stop_with_real_emitter_emits_task_done(self) -> None:
        def _run_replay(*, signum: int, signal_slug: str, control_seq: int) -> None:
            class FakeChild:
                pid = 902

                def poll(self) -> None:
                    return None

                def wait(self) -> int:
                    return 0

            class FakeSelector:
                def register(self, _fd: int, _events: int) -> None:
                    return None

                def select(self, timeout: float | None = None) -> list[tuple[Namespace, object]]:
                    if not output_sent:
                        output_sent.append(True)
                        os.write(writer_fd, b"Working (synthetic claude verify)\n")
                        return [(Namespace(fd=master_fd), None)]
                    if not signal_sent:
                        signal_sent.append(True)
                        handlers[signum](signum, None)
                    return []

                def close(self) -> None:
                    closed.append(True)

            class FakeStdout:
                def __init__(self, fd: int) -> None:
                    self._fd = fd

                def fileno(self) -> int:
                    return self._fd

                def flush(self) -> None:
                    return None

            handlers = {}
            output_sent: list[bool] = []
            signal_sent: list[bool] = []
            closed: list[bool] = []
            child = FakeChild()
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                task_hint_dir = root / "task-hints"
                self._write_task_hint(
                    task_hint_dir,
                    lane="Claude",
                    job_id=f"job-signal-real-{signal_slug}",
                    dispatch_id=f"dispatch-signal-real-{signal_slug}",
                    control_seq=control_seq,
                )
                master_fd, slave_fd = os.pipe()
                writer_fd = os.dup(slave_fd)
                stdout_fd = os.open(os.devnull, os.O_WRONLY)
                args = Namespace(
                    project_root=str(root),
                    run_id=f"run-real-{signal_slug}",
                    lane="Claude",
                    shell_command="sleep 10",
                    task_hint_dir=str(task_hint_dir),
                    heartbeat_interval=1.0,
                )

                def _capture_signal(sig: int, handler) -> None:
                    handlers[sig] = handler

                try:
                    with (
                        patch.object(runtime_cli.pty, "openpty", return_value=(master_fd, slave_fd)),
                        patch.object(runtime_cli.subprocess, "Popen", return_value=child),
                        patch.object(runtime_cli.selectors, "DefaultSelector", return_value=FakeSelector()),
                        patch.object(runtime_cli.signal, "signal", side_effect=_capture_signal),
                        patch.object(runtime_cli.os, "killpg") as killpg,
                        patch.object(runtime_cli.sys, "stdout", FakeStdout(stdout_fd)),
                    ):
                        self.assertEqual(runtime_cli._lane_wrapper(args), 0)
                finally:
                    os.close(writer_fd)
                    os.close(stdout_fd)

                events = self._read_wrapper_events(
                    root / ".pipeline" / "runs" / f"run-real-{signal_slug}" / "wrapper-events" / "claude.jsonl"
                )

            event_types = [str(event.get("event_type") or "") for event in events]
            task_done = [event for event in events if event.get("event_type") == "TASK_DONE"]
            self.assertEqual(len(task_done), 1)
            self.assertEqual(task_done[0]["payload"]["job_id"], f"job-signal-real-{signal_slug}")
            self.assertEqual(task_done[0]["payload"]["dispatch_id"], f"dispatch-signal-real-{signal_slug}")
            self.assertEqual(task_done[0]["payload"]["control_seq"], control_seq)
            self.assertEqual(task_done[0]["payload"]["reason"], "stream_eof")
            done_index = event_types.index("TASK_DONE")
            self.assertEqual(event_types[done_index + 1], "READY")
            self.assertEqual(output_sent, [True])
            self.assertEqual(signal_sent, [True])
            self.assertEqual(closed, [True])
            killpg.assert_called_once_with(child.pid, signum)

        for signum, signal_slug, control_seq in (
            (signal.SIGTERM, "sigterm", 420),
            (signal.SIGINT, "sigint", 421),
        ):
            with self.subTest(signal=signal_slug):
                _run_replay(signum=signum, signal_slug=signal_slug, control_seq=control_seq)

    def test_lane_wrapper_child_exit_with_real_emitter_emits_task_done(self) -> None:
        class FakeChild:
            pid = 903

            def poll(self) -> int:
                poll_calls.append(True)
                return 0

            def wait(self) -> int:
                wait_calls.append(True)
                return 0

        class FakeSelector:
            def register(self, _fd: int, _events: int) -> None:
                return None

            def select(self, timeout: float | None = None) -> list[tuple[Namespace, object]]:
                if not output_sent:
                    output_sent.append(True)
                    os.write(writer_fd, b"Working (synthetic claude verify)\n")
                    os.close(writer_fd)
                    writer_closed.append(True)
                    return [(Namespace(fd=master_fd), None)]
                return []

            def close(self) -> None:
                closed.append(True)

        class FakeStdout:
            def __init__(self, fd: int) -> None:
                self._fd = fd

            def fileno(self) -> int:
                return self._fd

            def flush(self) -> None:
                return None

        output_sent: list[bool] = []
        writer_closed: list[bool] = []
        poll_calls: list[bool] = []
        wait_calls: list[bool] = []
        closed: list[bool] = []
        child = FakeChild()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_hint_dir = root / "task-hints"
            self._write_task_hint(
                task_hint_dir,
                lane="Claude",
                job_id="job-child-exit-real",
                dispatch_id="dispatch-child-exit-real",
                control_seq=422,
            )
            master_fd, slave_fd = os.pipe()
            writer_fd = os.dup(slave_fd)
            stdout_fd = os.open(os.devnull, os.O_WRONLY)
            args = Namespace(
                project_root=str(root),
                run_id="run-real-child-exit",
                lane="Claude",
                shell_command="sleep 10",
                task_hint_dir=str(task_hint_dir),
                heartbeat_interval=1.0,
            )

            try:
                with (
                    patch.object(runtime_cli.pty, "openpty", return_value=(master_fd, slave_fd)),
                    patch.object(runtime_cli.subprocess, "Popen", return_value=child),
                    patch.object(runtime_cli.selectors, "DefaultSelector", return_value=FakeSelector()),
                    patch.object(runtime_cli.signal, "signal"),
                    patch.object(runtime_cli.sys, "stdout", FakeStdout(stdout_fd)),
                ):
                    self.assertEqual(runtime_cli._lane_wrapper(args), 0)
            finally:
                if not writer_closed:
                    os.close(writer_fd)
                os.close(stdout_fd)

            events = self._read_wrapper_events(
                root / ".pipeline" / "runs" / "run-real-child-exit" / "wrapper-events" / "claude.jsonl"
            )

        event_types = [str(event.get("event_type") or "") for event in events]
        task_done = [event for event in events if event.get("event_type") == "TASK_DONE"]
        self.assertEqual(len(task_done), 1)
        self.assertEqual(task_done[0]["payload"]["job_id"], "job-child-exit-real")
        self.assertEqual(task_done[0]["payload"]["dispatch_id"], "dispatch-child-exit-real")
        self.assertEqual(task_done[0]["payload"]["control_seq"], 422)
        self.assertEqual(task_done[0]["payload"]["reason"], "stream_eof")
        done_index = event_types.index("TASK_DONE")
        self.assertEqual(event_types[done_index + 1], "READY")
        self.assertEqual(output_sent, [True])
        self.assertEqual(writer_closed, [True])
        self.assertEqual(closed, [True])
        self.assertGreaterEqual(len(poll_calls), 1)
        self.assertEqual(wait_calls, [True])

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

    def test_doctor_reports_tmux_warn_when_session_missing(self) -> None:
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
            adapter = Mock()
            adapter.session_exists.return_value = False

            with (
                patch.object(runtime_cli, "_find_cli_bin", return_value=True),
                patch.object(runtime_cli, "_list_supervisor_pids", return_value=[]),
                patch.object(runtime_cli, "TmuxAdapter", return_value=adapter),
            ):
                payload = runtime_cli._doctor_payload(project_root, "aip-test")

            checks = {item["name"]: item for item in payload["checks"]}
            self.assertEqual(checks["tmux_session"]["status"], "warn")
            self.assertIn("not found", checks["tmux_session"]["detail"])
            self.assertIn("start", checks["tmux_session"]["hint"])

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

    def test_supervisor_running_ignores_zombie_pidfile_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_root = root / "project"
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            proc_dir = root / "proc" / "4242"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            proc_dir.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("4242", encoding="utf-8")
            (proc_dir / "stat").write_text("4242 (python3) Z 1 2 3\n", encoding="utf-8")

            with patch.object(runtime_cli.os, "kill", return_value=None):
                pid = runtime_cli._supervisor_running(project_root, proc_root=root / "proc")

            self.assertIsNone(pid)

    def test_supervisor_running_keeps_non_zombie_pidfile_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_root = root / "project"
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            proc_dir = root / "proc" / "4242"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            proc_dir.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("4242", encoding="utf-8")
            (proc_dir / "stat").write_text("4242 (python3) S 1 2 3\n", encoding="utf-8")

            with patch.object(runtime_cli.os, "kill", return_value=None):
                pid = runtime_cli._supervisor_running(project_root, proc_root=root / "proc")

            self.assertEqual(pid, 4242)

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

    def test_automation_health_source_newer_than_supervisor_pidfile_requests_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            source_path = project_root / "pipeline_runtime" / "automation_health.py"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("1234", encoding="utf-8")
            source_path.write_text("# updated automation health\n", encoding="utf-8")
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
                patch.object(runtime_cli, "start_preflight_failure_message", return_value=""),
                patch.object(runtime_cli, "RuntimeSupervisor", return_value=Mock(run_id="run-fresh")),
                patch.object(runtime_cli.subprocess, "Popen", return_value=process) as popen,
                patch.object(runtime_cli, "_current_run_matches", return_value=True),
            ):
                code = runtime_cli._spawn_supervisor(args)

            self.assertEqual(code, 0)
            stop_supervisor.assert_called_once_with(args)
            popen.assert_called_once()

    def test_spawn_supervisor_returns_success_when_start_lock_is_held(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            lock_path = project_root / ".pipeline" / ".supervisor-start.lock"
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            first_fd = os.open(str(lock_path), os.O_CREAT | os.O_WRONLY)
            second_fd = os.open(str(lock_path), os.O_CREAT | os.O_WRONLY)
            args = Namespace(
                project_root=str(project_root),
                legacy_mode="",
                mode="experimental",
                session="aip-projectH",
            )

            try:
                fcntl.flock(first_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(second_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

                with (
                    patch.object(runtime_cli, "_runtime_source_newer_than_supervisor_pidfile") as source_newer,
                    patch.object(runtime_cli, "_reconcile_supervisors", return_value=None) as reconcile,
                    patch.object(
                        runtime_cli,
                        "start_preflight_failure_message",
                        return_value="pipeline doctor should not run while start lock is held",
                    ) as preflight,
                    patch.object(runtime_cli.subprocess, "Popen") as popen,
                ):
                    code = runtime_cli._spawn_supervisor(args)

                self.assertEqual(code, 0)
                source_newer.assert_not_called()
                reconcile.assert_not_called()
                preflight.assert_not_called()
                popen.assert_not_called()
            finally:
                try:
                    fcntl.flock(first_fd, fcntl.LOCK_UN)
                except OSError:
                    pass
                os.close(second_fd)
                os.close(first_fd)

    def test_spawn_supervisor_blocks_when_start_preflight_fails(self) -> None:
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
                patch.object(runtime_cli, "_reconcile_supervisors", return_value=None),
                patch.object(runtime_cli, "start_preflight_failure_message", return_value="pipeline doctor required preflight failed: AGENTS.md"),
                patch.object(runtime_cli.subprocess, "Popen") as popen,
            ):
                code = runtime_cli._spawn_supervisor(args)

            self.assertEqual(code, 1)
            popen.assert_not_called()

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

    def test_stop_supervisor_returns_success_after_force_cleanup_when_supervisors_exit(self) -> None:
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
                patch.object(runtime_cli, "_orphan_runtime_needs_cleanup", return_value=False),
                patch.object(runtime_cli, "_coerce_status_to_stopped") as coerce,
            ):
                code = runtime_cli._stop_supervisor(args)

            self.assertEqual(code, 0)
            self.assertEqual(signaled, [(111, signal.SIGTERM)])
            self.assertEqual(killed, [111])
            coerce.assert_called_once_with(project_root)
            self.assertFalse(pid_path.exists())

    def test_stop_supervisor_returns_failure_when_force_kill_cannot_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            pid_path = project_root / ".pipeline" / "supervisor.pid"
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text("111", encoding="utf-8")
            args = Namespace(project_root=str(project_root), legacy_mode="", session="aip-projectH")

            with (
                patch.object(runtime_cli, "_list_supervisor_pids", side_effect=[[111], [111]]),
                patch.object(runtime_cli, "_supervisor_running", return_value=111),
                patch.object(runtime_cli, "_signal_pid"),
                patch.object(runtime_cli, "_wait_for_stop_completion", return_value=False),
                patch.object(runtime_cli, "_kill_pid"),
                patch.object(runtime_cli, "_wait_for_supervisors_exit", return_value=False),
                patch.object(runtime_cli, "_coerce_status_to_stopped") as coerce,
            ):
                code = runtime_cli._stop_supervisor(args)

            self.assertEqual(code, 1)
            coerce.assert_not_called()

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

    def test_stop_supervisor_coerces_status_when_no_process_is_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            run_dir = project_root / ".pipeline" / "runs" / "run-1"
            run_dir.mkdir(parents=True, exist_ok=True)
            (project_root / ".pipeline" / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "status_path": ".pipeline/runs/run-1/status.json",
                    }
                ),
                encoding="utf-8",
            )
            status_path = run_dir / "status.json"
            status_path.write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "runtime_state": "RUNNING",
                        "watcher": {"alive": True, "pid": 111},
                        "lanes": [
                            {"name": "Codex", "state": "READY", "pid": 222, "attachable": True}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            args = Namespace(project_root=str(project_root), legacy_mode="", session="aip-projectH")

            with (
                patch.object(runtime_cli, "_list_supervisor_pids", return_value=[]),
                patch.object(runtime_cli, "_supervisor_running", return_value=None),
                patch.object(runtime_cli, "_orphan_runtime_needs_cleanup", return_value=False),
            ):
                code = runtime_cli._stop_supervisor(args)

            self.assertEqual(code, 0)
            repaired = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(repaired["runtime_state"], "STOPPED")
            self.assertEqual(repaired["watcher"], {"alive": False, "pid": None})
            self.assertEqual(repaired["runtime_snapshot"]["runtime_state"], "STOPPED")
            self.assertEqual(repaired["runtime_snapshot"]["queue"]["status"], "Runtime inactive")

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
            self.assertEqual(repaired["runtime_snapshot"]["runtime_state"], "STOPPED")
            self.assertEqual(repaired["runtime_snapshot"]["queue"]["status"], "Runtime inactive")
            self.assertFalse(repaired_hint["active"])
            self.assertEqual(repaired_hint["job_id"], "")
            self.assertEqual(repaired_hint["dispatch_id"], "")
            self.assertEqual(repaired_hint["control_seq"], -1)
            self.assertEqual(repaired_hint["inactive_reason"], "runtime_stopped")
