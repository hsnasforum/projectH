from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

try:
    from .token_parsers.base import UsageEntry
except ImportError:
    from token_parsers.base import UsageEntry


class TokenStore:
    def __init__(self, db_path: Path, schema_path: Path | None = None) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.schema_path = schema_path or (Path(__file__).resolve().parent / "token_schema.sql")
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _init_db(self) -> None:
        schema = self.schema_path.read_text(encoding="utf-8")
        with self.connect() as conn:
            conn.executescript(schema)
            self._ensure_column(conn, "job_usage_link", "linked_at", "TEXT")
            self._ensure_column(conn, "job_usage_link", "note", "TEXT")

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, type_sql: str) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        if any(str(row["name"]) == column for row in rows):
            return
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_sql}")

    def get_file_state(self, path: Path) -> sqlite3.Row | None:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM file_state WHERE path = ?",
                (str(path),),
            ).fetchone()

    def upsert_file_state(
        self,
        path: Path,
        parser_kind: str,
        mtime_ns: int,
        size: int,
        last_offset: int | None,
        last_line_no: int | None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO file_state (
                  path, parser_kind, mtime_ns, size, last_offset, last_line_no, last_scanned_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                  parser_kind = excluded.parser_kind,
                  mtime_ns = excluded.mtime_ns,
                  size = excluded.size,
                  last_offset = excluded.last_offset,
                  last_line_no = excluded.last_line_no,
                  last_scanned_at = excluded.last_scanned_at
                """,
                (
                    str(path),
                    parser_kind,
                    mtime_ns,
                    size,
                    last_offset,
                    last_line_no,
                    _utc_now_iso(),
                ),
            )

    def insert_usage_entries(self, entries: list[UsageEntry]) -> int:
        if not entries:
            return 0
        collected_at = _utc_now_iso()
        with self.connect() as conn:
            before = conn.total_changes
            conn.executemany(
                """
                INSERT OR IGNORE INTO raw_usage (
                  dedup_key, ts, day, source, model,
                  input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
                  thinking_tokens, web_search_requests,
                  actual_cost_usd, estimated_cost_usd,
                  message_id, request_id,
                  raw_path, raw_offset, raw_line_no, content_hash, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        entry.dedup_key(),
                        entry.ts,
                        entry.day,
                        entry.source,
                        entry.model,
                        entry.input_tokens,
                        entry.output_tokens,
                        entry.cache_read_tokens,
                        entry.cache_write_tokens,
                        entry.thinking_tokens,
                        entry.web_search_requests,
                        entry.actual_cost_usd,
                        entry.estimated_cost_usd,
                        entry.message_id,
                        entry.request_id,
                        entry.raw_path,
                        entry.raw_offset,
                        entry.raw_line_no,
                        entry.content_hash,
                        collected_at,
                    )
                    for entry in entries
                ],
            )
            return conn.total_changes - before

    def insert_pipeline_events(self, events: list[dict[str, object]]) -> int:
        if not events:
            return 0
        with self.connect() as conn:
            before = conn.total_changes
            conn.executemany(
                """
                INSERT OR IGNORE INTO pipeline_event (
                  event_key, ts, job_id, round, event_type, slot, agent,
                  pane_target, artifact_path, raw_path, raw_line_no, log_family, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        event["event_key"],
                        event["ts"],
                        event["job_id"],
                        event.get("round"),
                        event["event_type"],
                        event.get("slot"),
                        event.get("agent"),
                        event.get("pane_target"),
                        event.get("artifact_path"),
                        event["raw_path"],
                        event.get("raw_line_no"),
                        event.get("log_family"),
                        event["payload_json"],
                    )
                    for event in events
                ],
            )
            return conn.total_changes - before

    def update_collector_status(
        self,
        phase: str,
        *,
        last_scan_started_at: str | None = None,
        last_scan_finished_at: str | None = None,
        scanned_files: int | None = None,
        parsed_events: int | None = None,
        last_error: str | None = None,
    ) -> None:
        with self.connect() as conn:
            current = conn.execute(
                "SELECT * FROM collector_status WHERE singleton_key = 1"
            ).fetchone()
            conn.execute(
                """
                INSERT INTO collector_status (
                  singleton_key, phase, last_heartbeat_at, last_scan_started_at,
                  last_scan_finished_at, scanned_files, parsed_events, last_error
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(singleton_key) DO UPDATE SET
                  phase = excluded.phase,
                  last_heartbeat_at = excluded.last_heartbeat_at,
                  last_scan_started_at = COALESCE(excluded.last_scan_started_at, collector_status.last_scan_started_at),
                  last_scan_finished_at = COALESCE(excluded.last_scan_finished_at, collector_status.last_scan_finished_at),
                  scanned_files = COALESCE(excluded.scanned_files, collector_status.scanned_files),
                  parsed_events = COALESCE(excluded.parsed_events, collector_status.parsed_events),
                  last_error = CASE
                    WHEN excluded.last_error IS NULL THEN collector_status.last_error
                    ELSE excluded.last_error
                  END
                """,
                (
                    phase,
                    _utc_now_iso(),
                    last_scan_started_at,
                    last_scan_finished_at,
                    scanned_files if scanned_files is not None else (current["scanned_files"] if current else 0),
                    parsed_events if parsed_events is not None else (current["parsed_events"] if current else 0),
                    last_error,
                ),
            )

    def get_collector_status(self) -> sqlite3.Row | None:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM collector_status WHERE singleton_key = 1"
            ).fetchone()

    def replace_job_links(
        self,
        job_id: str,
        links: list[tuple[int, str, float, str | None]],
    ) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM job_usage_link WHERE job_id = ?", (job_id,))
            conn.executemany(
                """
                INSERT OR REPLACE INTO job_usage_link (
                  job_id, usage_id, link_method, confidence, linked_at, note
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (job_id, usage_id, method, confidence, _utc_now_iso(), note)
                    for usage_id, method, confidence, note in links
                ],
            )


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
