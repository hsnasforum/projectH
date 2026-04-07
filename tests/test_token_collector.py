from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from _data.job_linker import relink_jobs
from _data.token_collector import TokenCollector
from _data.token_parsers import ClaudeParser, CodexParser, GeminiParser
from _data.token_store import TokenStore


class TokenCollectorTest(unittest.TestCase):
    def _set_test_roots(
        self,
        collector: TokenCollector,
        *,
        claude_root: Path | None = None,
        codex_root: Path | None = None,
        gemini_root: Path | None = None,
    ) -> None:
        empty_root = Path(collector.project_root) / "__empty__"
        collector.parsers["claude"] = (collector.parsers["claude"][0], claude_root or empty_root, "*.jsonl")
        collector.parsers["codex"] = (collector.parsers["codex"][0], codex_root or empty_root, "*.jsonl")
        collector.parsers["gemini"] = (collector.parsers["gemini"][0], gemini_root or empty_root, "logs.json")

    def test_claude_parser_extracts_usage_entry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "claude.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:02:03Z",
                        "requestId": "req-1",
                        "uuid": "uuid-1",
                        "message": {
                            "model": "claude-opus-4-6",
                            "id": "msg-1",
                            "usage": {
                                "input_tokens": 10,
                                "output_tokens": 5,
                                "cache_read_input_tokens": 2,
                                "cache_creation_input_tokens": 3,
                                "server_tool_use": {"web_search_requests": 1},
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = ClaudeParser().parse_file(path)
            self.assertEqual(len(result.entries), 1)
            self.assertEqual(result.entries[0].source, "claude")
            self.assertEqual(result.entries[0].input_tokens, 10)
            self.assertEqual(result.entries[0].web_search_requests, 1)

    def test_codex_parser_uses_last_token_usage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "rollout.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:02:03Z",
                        "type": "event_msg",
                        "payload": {
                            "type": "token_count",
                            "info": {
                                "last_token_usage": {
                                    "input_tokens": 20,
                                    "cached_input_tokens": 7,
                                    "output_tokens": 4,
                                    "reasoning_output_tokens": 2,
                                    "total_tokens": 24,
                                }
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = CodexParser().parse_file(path)
            self.assertEqual(len(result.entries), 1)
            self.assertEqual(result.entries[0].source, "codex")
            self.assertEqual(result.entries[0].thinking_tokens, 2)

    def test_gemini_parser_reads_logs_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "logs.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "timestamp": "2026-04-05T04:00:00Z",
                            "sessionId": "sess-1",
                            "messageId": 1,
                            "usageMetadata": {
                                "promptTokenCount": 12,
                                "toolUsePromptTokenCount": 1,
                                "candidatesTokenCount": 4,
                                "cachedContentTokenCount": 3,
                                "thoughtsTokenCount": 2,
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )
            result = GeminiParser().parse_file(path)
            self.assertEqual(len(result.entries), 1)
            self.assertEqual(result.entries[0].source, "gemini")
            self.assertEqual(result.entries[0].input_tokens, 13)

    def test_store_dedup_ignores_duplicate_usage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            path = Path(td) / "claude.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:02:03Z",
                        "requestId": "req-1",
                        "uuid": "uuid-1",
                        "message": {
                            "model": "claude-opus-4-6",
                            "id": "msg-1",
                            "usage": {
                                "input_tokens": 10,
                                "output_tokens": 5,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = ClaudeParser().parse_file(path)
            self.assertEqual(store.insert_usage_entries(result.entries), 1)
            self.assertEqual(store.insert_usage_entries(result.entries), 0)

    def test_job_linker_links_codex_usage_to_slot_verify_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            codex_path = Path(td) / "rollout.jsonl"
            codex_path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:10:00Z",
                        "type": "event_msg",
                        "payload": {
                            "type": "token_count",
                            "info": {
                                "last_token_usage": {
                                    "input_tokens": 20,
                                    "cached_input_tokens": 7,
                                    "output_tokens": 4,
                                    "reasoning_output_tokens": 2,
                                    "total_tokens": 24,
                                }
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            store.insert_usage_entries(CodexParser().parse_file(codex_path).entries)
            store.insert_pipeline_events(
                [
                    {
                        "event_key": "dispatch:1",
                        "ts": "2026-04-05T01:09:55Z",
                        "job_id": "job-1",
                        "round": 1,
                        "event_type": "dispatch",
                        "slot": "slot_verify",
                        "agent": "codex",
                        "pane_target": "%1",
                        "artifact_path": "/tmp/a.md",
                        "raw_path": "/tmp/dispatch.jsonl",
                        "raw_line_no": 1,
                        "log_family": "experimental",
                        "payload_json": "{}",
                    }
                ]
            )
            with store.connect() as conn:
                relink_jobs(conn)
                row = conn.execute(
                    "SELECT confidence FROM job_usage_link WHERE job_id = ?",
                    ("job-1",),
                ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["confidence"], 0.9)

    def test_job_linker_does_not_double_link_overlapping_verify_windows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            codex_path = Path(td) / "rollout.jsonl"
            codex_path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:01:05Z",
                        "type": "event_msg",
                        "payload": {
                            "type": "token_count",
                            "info": {
                                "last_token_usage": {
                                    "input_tokens": 20,
                                    "cached_input_tokens": 7,
                                    "output_tokens": 4,
                                    "reasoning_output_tokens": 2,
                                    "total_tokens": 24,
                                }
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            store.insert_usage_entries(CodexParser().parse_file(codex_path).entries)
            store.insert_pipeline_events(
                [
                    {
                        "event_key": "dispatch:1",
                        "ts": "2026-04-05T01:00:00Z",
                        "job_id": "job-1",
                        "round": 1,
                        "event_type": "dispatch",
                        "slot": "slot_verify",
                        "agent": "codex",
                        "pane_target": "%1",
                        "artifact_path": "/tmp/a.md",
                        "raw_path": "/tmp/dispatch.jsonl",
                        "raw_line_no": 1,
                        "log_family": "experimental",
                        "payload_json": "{}",
                    },
                    {
                        "event_key": "dispatch:2",
                        "ts": "2026-04-05T01:01:00Z",
                        "job_id": "job-2",
                        "round": 1,
                        "event_type": "dispatch",
                        "slot": "slot_verify",
                        "agent": "codex",
                        "pane_target": "%2",
                        "artifact_path": "/tmp/b.md",
                        "raw_path": "/tmp/dispatch.jsonl",
                        "raw_line_no": 2,
                        "log_family": "experimental",
                        "payload_json": "{}",
                    },
                ]
            )
            with store.connect() as conn:
                relink_jobs(conn)
                rows = conn.execute(
                    "SELECT job_id, usage_id FROM job_usage_link ORDER BY job_id ASC"
                ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["job_id"], "job-2")

    def test_job_linker_links_claude_usage_to_work_artifact_window(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            claude_path = Path(td) / "claude.jsonl"
            claude_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-04-05T01:20:00Z",
                                "requestId": "req-1",
                                "uuid": "uuid-1",
                                "message": {
                                    "model": "claude-opus-4-6",
                                    "id": "msg-1",
                                    "usage": {"input_tokens": 10, "output_tokens": 4},
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-04-05T01:50:00Z",
                                "requestId": "req-2",
                                "uuid": "uuid-2",
                                "message": {
                                    "model": "claude-opus-4-6",
                                    "id": "msg-2",
                                    "usage": {"input_tokens": 8, "output_tokens": 3},
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            store.insert_usage_entries(ClaudeParser().parse_file(claude_path).entries)
            store.insert_pipeline_events(
                [
                    {
                        "event_key": "artifact:1",
                        "ts": "2026-04-05T01:00:00Z",
                        "job_id": "job-1",
                        "round": 1,
                        "event_type": "artifact_seen",
                        "slot": None,
                        "agent": None,
                        "pane_target": None,
                        "artifact_path": "work/4/5/job-1.md",
                        "raw_path": "/tmp/raw.jsonl",
                        "raw_line_no": 1,
                        "log_family": "experimental",
                        "payload_json": "{}",
                    },
                    {
                        "event_key": "artifact:2",
                        "ts": "2026-04-05T01:30:00Z",
                        "job_id": "job-2",
                        "round": 1,
                        "event_type": "artifact_seen",
                        "slot": None,
                        "agent": None,
                        "pane_target": None,
                        "artifact_path": "work/4/5/job-2.md",
                        "raw_path": "/tmp/raw.jsonl",
                        "raw_line_no": 2,
                        "log_family": "experimental",
                        "payload_json": "{}",
                    },
                    {
                        "event_key": "artifact:3",
                        "ts": "2026-04-05T02:00:00Z",
                        "job_id": "job-3",
                        "round": 1,
                        "event_type": "artifact_seen",
                        "slot": None,
                        "agent": None,
                        "pane_target": None,
                        "artifact_path": "work/4/5/job-3.md",
                        "raw_path": "/tmp/raw.jsonl",
                        "raw_line_no": 3,
                        "log_family": "experimental",
                        "payload_json": "{}",
                    },
                ]
            )
            with store.connect() as conn:
                relink_jobs(conn)
                rows = conn.execute(
                    """
                    SELECT job_id, link_method, confidence, note
                    FROM job_usage_link
                    ORDER BY job_id ASC
                    """
                ).fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["job_id"], "job-2")
            self.assertEqual(rows[0]["link_method"], "artifact_seen_work_window")
            self.assertGreaterEqual(rows[0]["confidence"], 0.45)
            self.assertIn("previous_artifact", rows[0]["note"])
            self.assertEqual(rows[1]["job_id"], "job-3")
            self.assertEqual(rows[1]["link_method"], "artifact_seen_work_window")

    def test_job_linker_links_gemini_usage_via_recent_job_before_notify(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            gemini_path = Path(td) / "logs.json"
            gemini_path.write_text(
                json.dumps(
                    [
                        {
                            "timestamp": "2026-04-05T01:05:30Z",
                            "sessionId": "sess-1",
                            "messageId": 1,
                            "usageMetadata": {
                                "promptTokenCount": 12,
                                "candidatesTokenCount": 4,
                                "cachedContentTokenCount": 3,
                                "thoughtsTokenCount": 2,
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )
            store.insert_usage_entries(GeminiParser().parse_file(gemini_path).entries)
            store.insert_pipeline_events(
                [
                    {
                        "event_key": "artifact:1",
                        "ts": "2026-04-05T01:00:00Z",
                        "job_id": "job-1",
                        "round": 1,
                        "event_type": "artifact_seen",
                        "slot": None,
                        "agent": None,
                        "pane_target": None,
                        "artifact_path": "work/4/5/job-1.md",
                        "raw_path": "/tmp/raw.jsonl",
                        "raw_line_no": 1,
                        "log_family": "experimental",
                        "payload_json": "{}",
                    },
                    {
                        "event_key": "notify:1",
                        "ts": "2026-04-05T01:05:00Z",
                        "job_id": "turn_signal",
                        "round": None,
                        "event_type": "gemini_notify",
                        "slot": None,
                        "agent": "gemini",
                        "pane_target": "%3",
                        "artifact_path": ".pipeline/gemini_request.md",
                        "raw_path": "/tmp/raw.jsonl",
                        "raw_line_no": 2,
                        "log_family": "experimental",
                        "payload_json": "{}",
                    },
                ]
            )
            with store.connect() as conn:
                relink_jobs(conn)
                row = conn.execute(
                    """
                    SELECT job_id, link_method, confidence, note
                    FROM job_usage_link
                    WHERE job_id = ?
                    """,
                    ("job-1",),
                ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["link_method"], "gemini_notify_recent_job_window")
            self.assertGreaterEqual(row["confidence"], 0.4)
            self.assertIn("gemini_notify via artifact_seen", row["note"])

    def test_job_linker_leaves_old_claude_usage_unlinked_when_artifact_gap_is_too_large(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            claude_path = Path(td) / "claude-old.jsonl"
            claude_path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:18:59Z",
                        "requestId": "req-old",
                        "uuid": "uuid-old",
                        "message": {
                            "model": "claude-opus-4-6",
                            "id": "msg-old",
                            "usage": {"input_tokens": 3, "output_tokens": 1},
                        },
                    }
                ),
                encoding="utf-8",
            )
            store.insert_usage_entries(ClaudeParser().parse_file(claude_path).entries)
            store.insert_pipeline_events(
                [
                    {
                        "event_key": "artifact:1",
                        "ts": "2026-04-05T01:30:00Z",
                        "job_id": "job-1",
                        "round": 1,
                        "event_type": "artifact_seen",
                        "slot": None,
                        "agent": None,
                        "pane_target": None,
                        "artifact_path": "work/4/5/job-1.md",
                        "raw_path": "/tmp/raw.jsonl",
                        "raw_line_no": 1,
                        "log_family": "experimental",
                        "payload_json": "{}",
                    }
                ]
            )
            with store.connect() as conn:
                relink_jobs(conn)
                row = conn.execute(
                    "SELECT 1 FROM job_usage_link WHERE job_id = ?",
                    ("job-1",),
                ).fetchone()
            self.assertIsNone(row)

    def test_collector_run_once_scans_pipeline_logs_and_usage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "project"
            project_root.mkdir()
            (project_root / ".pipeline" / "logs" / "experimental").mkdir(parents=True)
            dispatch_path = project_root / ".pipeline" / "logs" / "experimental" / "dispatch.jsonl"
            dispatch_path.write_text(
                json.dumps(
                    {
                        "event": "dispatch",
                        "job_id": "job-1",
                        "round": 1,
                        "target_slot": "slot_verify",
                        "pane_target": "%1",
                        "path": str(project_root / "work.md"),
                        "at": 1775310000.0,
                    }
                ),
                encoding="utf-8",
            )

            home = Path(td) / "home"
            claude_root = home / ".claude" / "projects" / "proj"
            claude_root.mkdir(parents=True)
            (claude_root / "session.jsonl").write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:00:00Z",
                        "requestId": "req-1",
                        "uuid": "uuid-1",
                        "message": {
                            "model": "claude-opus-4-6",
                            "id": "msg-1",
                            "usage": {"input_tokens": 1, "output_tokens": 2},
                        },
                    }
                ),
                encoding="utf-8",
            )

            collector = TokenCollector(project_root, project_root / ".pipeline" / "usage" / "usage.db", poll_interval=0.01)
            self._set_test_roots(collector, claude_root=home / ".claude" / "projects")
            summary = collector.run_once()

            self.assertGreaterEqual(summary["usage_inserted"], 1)
            self.assertGreaterEqual(summary["pipeline_inserted"], 1)
            self.assertGreaterEqual(summary["parsed_files"], 2)
            self.assertIn("elapsed_sec", summary)
            self.assertIn("db_size_mb", summary)

    def test_jsonl_trailing_partial_is_retried_without_advancing_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "project"
            project_root.mkdir()
            home = Path(td) / "home"
            claude_root = home / ".claude" / "projects" / "proj"
            claude_root.mkdir(parents=True)
            path = claude_root / "session.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:00:00Z",
                        "requestId": "req-1",
                        "uuid": "uuid-1",
                        "message": {"model": "claude", "id": "msg-1", "usage": {"input_tokens": 1, "output_tokens": 2}},
                    }
                )
                + "\n"
                + '{"timestamp":"2026-04-05T01:00:01Z"',
                encoding="utf-8",
            )
            collector = TokenCollector(project_root, project_root / ".pipeline" / "usage" / "usage.db")
            self._set_test_roots(collector, claude_root=home / ".claude" / "projects")
            summary = collector.run_once()
            self.assertEqual(summary["usage_inserted"], 1)
            state = collector.store.get_file_state(path)
            self.assertIsNone(state)

    def test_gemini_partial_json_does_not_advance_file_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "project"
            project_root.mkdir()
            home = Path(td) / "home"
            gemini_root = home / ".gemini" / "tmp" / "app"
            gemini_root.mkdir(parents=True)
            path = gemini_root / "logs.json"
            path.write_text('[{"timestamp":"2026-04-05T04:00:00Z"', encoding="utf-8")
            collector = TokenCollector(project_root, project_root / ".pipeline" / "usage" / "usage.db")
            self._set_test_roots(collector, gemini_root=home / ".gemini" / "tmp")
            summary = collector.run_once()
            self.assertEqual(summary["usage_inserted"], 0)
            state = collector.store.get_file_state(path)
            self.assertIsNone(state)

    def test_append_rescan_adds_only_new_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "project"
            project_root.mkdir()
            home = Path(td) / "home"
            claude_root = home / ".claude" / "projects" / "proj"
            claude_root.mkdir(parents=True)
            path = claude_root / "session.jsonl"
            first = json.dumps(
                {
                    "timestamp": "2026-04-05T01:00:00Z",
                    "requestId": "req-1",
                    "uuid": "uuid-1",
                    "message": {"model": "claude", "id": "msg-1", "usage": {"input_tokens": 1, "output_tokens": 2}},
                }
            )
            second = json.dumps(
                {
                    "timestamp": "2026-04-05T01:00:05Z",
                    "requestId": "req-2",
                    "uuid": "uuid-2",
                    "message": {"model": "claude", "id": "msg-2", "usage": {"input_tokens": 3, "output_tokens": 4}},
                }
            )
            path.write_text(first + "\n", encoding="utf-8")
            collector = TokenCollector(project_root, project_root / ".pipeline" / "usage" / "usage.db")
            self._set_test_roots(collector, claude_root=home / ".claude" / "projects")
            self.assertEqual(collector.run_once()["usage_inserted"], 1)
            path.write_text(first + "\n" + second + "\n", encoding="utf-8")
            self.assertEqual(collector.run_once()["usage_inserted"], 1)

    def test_force_rescan_reads_unchanged_files_again_but_dedup_keeps_zero_inserts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "project"
            project_root.mkdir()
            home = Path(td) / "home"
            claude_root = home / ".claude" / "projects" / "proj"
            claude_root.mkdir(parents=True)
            path = claude_root / "session.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:00:00Z",
                        "requestId": "req-1",
                        "uuid": "uuid-1",
                        "message": {"model": "claude", "id": "msg-1", "usage": {"input_tokens": 1, "output_tokens": 2}},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            db_path = project_root / ".pipeline" / "usage" / "usage.db"
            collector = TokenCollector(project_root, db_path)
            self._set_test_roots(collector, claude_root=home / ".claude" / "projects")
            first_summary = collector.run_once()
            self.assertEqual(first_summary["usage_inserted"], 1)

            force_collector = TokenCollector(project_root, db_path, force_rescan=True)
            self._set_test_roots(force_collector, claude_root=home / ".claude" / "projects")
            second_summary = force_collector.run_once()
            self.assertEqual(second_summary["scanned_files"], 1)
            self.assertEqual(second_summary["usage_inserted"], 0)
            self.assertEqual(second_summary["duplicates"], 1)

    def test_run_once_progress_callback_reports_scanning_and_idle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "project"
            project_root.mkdir()
            home = Path(td) / "home"
            claude_root = home / ".claude" / "projects" / "proj"
            claude_root.mkdir(parents=True)
            path = claude_root / "session.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:00:00Z",
                        "requestId": "req-1",
                        "uuid": "uuid-1",
                        "message": {"model": "claude", "id": "msg-1", "usage": {"input_tokens": 1, "output_tokens": 2}},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            collector = TokenCollector(project_root, project_root / ".pipeline" / "usage" / "usage.db")
            self._set_test_roots(collector, claude_root=home / ".claude" / "projects")
            events: list[dict[str, object]] = []
            summary = collector.run_once_with_progress(events.append)
            self.assertEqual(summary["usage_inserted"], 1)
            self.assertGreaterEqual(len(events), 3)
            self.assertEqual(events[0]["phase"], "preparing")
            self.assertEqual(events[0]["progress_percent"], 0)
            self.assertEqual(events[1]["phase"], "scanning")
            self.assertEqual(events[1]["progress_percent"], 0)
            self.assertEqual(events[1]["total_files"], 1)
            self.assertEqual(events[-1]["phase"], "idle")
            self.assertEqual(events[-1]["progress_percent"], 100)
            self.assertEqual(summary["total_files"], 1)
            self.assertEqual(summary["progress_percent"], 100)

    def test_collector_status_updates_after_scan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "project"
            project_root.mkdir()
            collector = TokenCollector(project_root, project_root / ".pipeline" / "usage" / "usage.db")
            self._set_test_roots(collector)
            summary = collector.run_once()
            status = collector.store.get_collector_status()
            self.assertIsNotNone(status)
            self.assertEqual(status["phase"], "idle")
            self.assertEqual(status["scanned_files"], summary["scanned_files"])

    def test_collector_run_once_recovers_from_stale_scanning_status(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "project"
            project_root.mkdir()
            collector = TokenCollector(project_root, project_root / ".pipeline" / "usage" / "usage.db")
            collector.store.update_collector_status(
                "scanning",
                last_scan_started_at="2026-04-05T00:00:00Z",
                last_error="stuck",
            )
            self._set_test_roots(collector)
            collector.run_once()
            status = collector.store.get_collector_status()
            self.assertIsNotNone(status)
            self.assertEqual(status["phase"], "idle")
            self.assertEqual(status["last_error"], "")

    def test_since_days_skips_old_files_on_first_scan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "project"
            project_root.mkdir()
            home = Path(td) / "home"
            claude_root = home / ".claude" / "projects" / "proj"
            claude_root.mkdir(parents=True)
            path = claude_root / "session.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-05T01:00:00Z",
                        "requestId": "req-1",
                        "uuid": "uuid-1",
                        "message": {"model": "claude", "id": "msg-1", "usage": {"input_tokens": 1, "output_tokens": 2}},
                    }
                ),
                encoding="utf-8",
            )
            old = 1_600_000_000
            Path(path).touch()
            import os
            os.utime(path, (old, old))
            collector = TokenCollector(
                project_root,
                project_root / ".pipeline" / "usage" / "usage.db",
                since_days=1,
            )
            self._set_test_roots(collector, claude_root=home / ".claude" / "projects")
            summary = collector.run_once()
            self.assertEqual(summary["usage_inserted"], 0)
