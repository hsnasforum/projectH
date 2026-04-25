from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _data.token_store import TokenStore
import pipeline_gui.token_queries as token_queries_module
from pipeline_gui.token_queries import (
    get_agent_totals_today,
    get_collector_status,
    get_link_method_summaries,
    get_link_samples,
    get_today_totals,
    get_top_jobs_today,
    get_unlinked_usage_counts,
    load_token_dashboard,
)


class TokenQueriesTest(unittest.TestCase):
    def test_queries_return_collector_status_and_today_totals(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            store.update_collector_status(
                "idle",
                last_scan_started_at="2026-04-05T01:00:00Z",
                last_scan_finished_at="2026-04-05T01:00:05Z",
                scanned_files=12,
                parsed_events=33,
                last_error="",
            )
            usage_dir = db_path.parent
            (usage_dir / "collector.launch_mode").write_text("tmux", encoding="utf-8")
            (usage_dir / "collector.window_name").write_text("usage-collector", encoding="utf-8")
            (usage_dir / "collector.pane_id").write_text("%7", encoding="utf-8")
            with store.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "a", "2026-04-05T01:00:00Z", "2026-04-05", "codex", None,
                        10, 5, 3, 1, 2, 0, 1.25, None,
                        None, None, "/tmp/a", 0, 1, "h1", "2026-04-05T01:00:05Z",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "b", "2026-04-05T02:00:00Z", "2026-04-05", "claude", None,
                        7, 4, 0, 0, 0, 1, None, 0.75,
                        None, None, "/tmp/b", 1, 2, "h2", "2026-04-05T02:00:05Z",
                    ),
                )
                conn.commit()
            status = get_collector_status(db_path)
            totals = get_today_totals(db_path, "2026-04-05")
            agents = get_agent_totals_today(db_path, "2026-04-05")
            self.assertTrue(status.available)
            self.assertEqual(status.phase, "idle")
            self.assertEqual(status.scanned_files, 12)
            self.assertEqual(status.launch_mode, "tmux")
            self.assertEqual(status.window_name, "usage-collector")
            self.assertEqual(totals.input_tokens, 17)
            self.assertEqual(totals.output_tokens, 9)
            self.assertEqual(totals.actual_cost_usd_sum, 1.25)
            self.assertEqual(totals.estimated_only_cost_usd_sum, 0.75)
            self.assertEqual(len(agents), 2)
            by_source = {item.source: item for item in agents}
            self.assertEqual(by_source["codex"].cache_read_tokens, 3)
            self.assertEqual(by_source["codex"].cache_write_tokens, 1)
            self.assertEqual(by_source["codex"].thinking_tokens, 2)
            self.assertEqual(agents[0].linked_events, 0)
            self.assertEqual(agents[1].linked_events, 0)

    def test_collector_status_marks_stale_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            store.update_collector_status(
                "idle"
            )
            with store.connect() as conn:
                conn.execute(
                    """
                    UPDATE collector_status
                    SET last_heartbeat_at = ?, last_scan_started_at = ?, last_scan_finished_at = ?,
                        scanned_files = ?, parsed_events = ?, last_error = ?
                    WHERE singleton_key = 1
                    """,
                    ("2026-04-05T01:00:00Z", "2026-04-05T01:00:00Z", "2026-04-05T01:00:05Z", 2, 4, ""),
                )
                conn.commit()
            status = get_collector_status(
                db_path,
                now=dt.datetime(2026, 4, 5, 1, 2, 0, tzinfo=dt.timezone.utc),
                stale_after_sec=30,
            )
            self.assertTrue(status.available)
            self.assertTrue(status.is_stale)
            self.assertEqual(status.phase, "stale")
            self.assertGreaterEqual(status.heartbeat_age_sec, 100)

    def test_load_token_dashboard_falls_back_to_latest_usage_day(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            usage_dir = project / ".pipeline" / "usage"
            usage_dir.mkdir(parents=True)
            db_path = usage_dir / "usage.db"
            store = TokenStore(db_path)
            with store.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "latest-day", "2026-04-05T01:00:00Z", "2026-04-05", "codex", None,
                        11, 7, 0, 0, 0, 0, None, 0.2,
                        None, None, "/tmp/latest", 0, 1, "h1", "2026-04-05T01:00:05Z",
                    ),
                )
                conn.commit()

            dashboard = load_token_dashboard(project, day="2026-04-06")
            self.assertEqual(dashboard.display_day, "2026-04-05")
            self.assertEqual(dashboard.today_totals.input_tokens, 11)
            self.assertEqual(len(dashboard.agent_totals), 1)

    def test_top_jobs_today_returns_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            with store.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "a", "2026-04-05T01:00:00Z", "2026-04-05", "codex", None,
                        10, 5, 0, 0, 0, 0, None, 1.0,
                        None, None, "/tmp/a", 0, 1, "h1", "2026-04-05T01:00:05Z",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "b", "2026-04-05T01:00:10Z", "2026-04-05", "claude", None,
                        3, 2, 0, 0, 0, 0, None, 0.3,
                        None, None, "/tmp/b", 1, 2, "h2", "2026-04-05T01:00:15Z",
                    ),
                )
                usage_id = conn.execute("SELECT id FROM raw_usage WHERE dedup_key = 'a'").fetchone()["id"]
                usage_id_2 = conn.execute("SELECT id FROM raw_usage WHERE dedup_key = 'b'").fetchone()["id"]
                conn.execute(
                    """
                    INSERT INTO job_usage_link (job_id, usage_id, link_method, confidence, linked_at, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("job-1", usage_id, "dispatch_slot_verify_window", 0.9, "2026-04-05T01:00:06Z", "verify"),
                )
                conn.execute(
                    """
                    INSERT INTO job_usage_link (job_id, usage_id, link_method, confidence, linked_at, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("job-1", usage_id_2, "artifact_seen_work_window", 0.55, "2026-04-05T01:00:16Z", "artifact"),
                )
                conn.commit()
            jobs = get_top_jobs_today(db_path, "2026-04-05", limit=5)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0].job_id, "job-1")
            self.assertEqual(jobs[0].primary_link_method, "dispatch_slot_verify_window")
            self.assertEqual(jobs[0].max_confidence, 0.9)
            self.assertEqual(jobs[0].low_confidence_events, 1)

    def test_agent_totals_include_linked_event_count(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            with store.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "claude-linked", "2026-04-05T01:00:00Z", "2026-04-05", "claude", None,
                        4, 2, 0, 0, 0, 0, None, 0.3,
                        None, None, "/tmp/a", 0, 1, "h1", "2026-04-05T01:00:05Z",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "gemini-unlinked", "2026-04-05T02:00:00Z", "2026-04-05", "gemini", None,
                        6, 1, 0, 0, 0, 0, None, 0.2,
                        None, None, "/tmp/b", 1, 2, "h2", "2026-04-05T02:00:05Z",
                    ),
                )
                usage_id = conn.execute(
                    "SELECT id FROM raw_usage WHERE dedup_key = 'claude-linked'"
                ).fetchone()["id"]
                conn.execute(
                    """
                    INSERT INTO job_usage_link (job_id, usage_id, link_method, confidence, linked_at, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("job-1", usage_id, "artifact_seen_work_window", 0.7, "2026-04-05T01:00:06Z", "artifact"),
                )
                conn.commit()
            agents = get_agent_totals_today(db_path, "2026-04-05")
            by_source = {item.source: item for item in agents}
            self.assertEqual(by_source["claude"].linked_events, 1)
            self.assertEqual(by_source["gemini"].linked_events, 0)

    def test_link_audit_queries_return_summaries_samples_and_unlinked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "usage.db"
            store = TokenStore(db_path)
            with store.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "claude-a", "2026-04-05T01:00:00Z", "2026-04-05", "claude", "claude-opus",
                        10, 5, 1, 0, 0, 0, None, 0.8,
                        None, None, "/tmp/claude-a", 0, 1, "h1", "2026-04-05T01:00:05Z",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "gemini-a", "2026-04-05T02:00:00Z", "2026-04-05", "gemini", "gemini-2.5-pro",
                        12, 4, 3, 0, 2, 0, None, 0.4,
                        None, None, "/tmp/gemini-a", 1, 2, "h2", "2026-04-05T02:00:05Z",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO raw_usage (
                      dedup_key, ts, day, source, model, input_tokens, output_tokens,
                      cache_read_tokens, cache_write_tokens, thinking_tokens,
                      web_search_requests, actual_cost_usd, estimated_cost_usd,
                      message_id, request_id, raw_path, raw_offset, raw_line_no,
                      content_hash, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "claude-b", "2026-04-05T03:00:00Z", "2026-04-05", "claude", "claude-opus",
                        5, 1, 0, 0, 0, 0, None, 0.2,
                        None, None, "/tmp/claude-b", 2, 3, "h3", "2026-04-05T03:00:05Z",
                    ),
                )
                claude_usage_id = conn.execute(
                    "SELECT id FROM raw_usage WHERE dedup_key = 'claude-a'"
                ).fetchone()["id"]
                gemini_usage_id = conn.execute(
                    "SELECT id FROM raw_usage WHERE dedup_key = 'gemini-a'"
                ).fetchone()["id"]
                conn.execute(
                    """
                    INSERT INTO job_usage_link (job_id, usage_id, link_method, confidence, linked_at, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("job-claude", claude_usage_id, "artifact_seen_work_window", 0.55, "2026-04-05T01:00:06Z", "artifact"),
                )
                conn.execute(
                    """
                    INSERT INTO job_usage_link (job_id, usage_id, link_method, confidence, linked_at, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("job-gemini", gemini_usage_id, "gemini_notify_recent_job_window", 0.4, "2026-04-05T02:00:06Z", "notify"),
                )
                conn.commit()

            summaries = get_link_method_summaries(
                db_path,
                day="2026-04-05",
                sources=("claude", "gemini"),
                low_confidence_threshold=0.6,
            )
            samples = get_link_samples(
                db_path,
                day="2026-04-05",
                source="gemini",
                max_confidence=0.5,
                limit=5,
            )
            unlinked = get_unlinked_usage_counts(
                db_path,
                day="2026-04-05",
                sources=("claude", "gemini"),
            )

            self.assertEqual(len(summaries), 2)
            self.assertEqual(summaries[0].low_confidence_events, 1)
            self.assertEqual(summaries[1].low_confidence_events, 1)
            self.assertEqual(len(samples), 1)
            self.assertEqual(samples[0].job_id, "job-gemini")
            self.assertEqual(samples[0].link_method, "gemini_notify_recent_job_window")
            self.assertEqual(len(unlinked), 1)
            self.assertEqual(unlinked[0].source, "claude")
            self.assertEqual(unlinked[0].events, 1)

    def test_load_token_dashboard_via_wsl_uses_shared_dashboard_script(self) -> None:
        project = Path("/tmp/projectH")
        payload = {
            "display_day": "2026-04-05",
            "collector_status": {"available": True, "phase": "idle"},
            "today_totals": {"input_tokens": 10, "output_tokens": 3},
            "agent_totals": [],
            "top_jobs": [],
        }
        with (
            mock.patch.object(token_queries_module, "IS_WINDOWS", True),
            mock.patch.object(
                token_queries_module,
                "resolve_project_runtime_file",
                return_value=Path("/tmp/token_dashboard_shared.py"),
            ) as resolve_mock,
            mock.patch.object(
                token_queries_module,
                "_windows_to_wsl_mount",
                return_value="/mnt/c/token_dashboard_shared.py",
            ) as mount_mock,
            mock.patch.object(
                token_queries_module,
                "_run",
                return_value=(0, json.dumps(payload)),
            ) as run_mock,
        ):
            dashboard = load_token_dashboard(project, day="2026-04-06", top_n=7)

        resolve_mock.assert_called_once_with(project, "token_dashboard_shared.py")
        mount_arg = mount_mock.call_args.args[0]
        self.assertEqual(mount_arg, Path("/tmp/token_dashboard_shared.py"))
        run_mock.assert_called_once_with(
            [
                "python3",
                "/mnt/c/token_dashboard_shared.py",
                "/tmp/projectH/.pipeline/usage/usage.db",
                "2026-04-06",
                "7",
            ],
            timeout=12.0,
        )
        self.assertEqual(dashboard.display_day, "2026-04-05")
        self.assertEqual(dashboard.today_totals.input_tokens, 10)
