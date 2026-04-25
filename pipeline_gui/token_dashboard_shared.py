"""Shared token dashboard query helpers for local and WSL launcher paths."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

SQL_COLLECTOR_STATUS = """
SELECT phase, last_heartbeat_at, last_scan_started_at, last_scan_finished_at,
       scanned_files, parsed_events, COALESCE(last_error, '') AS last_error
FROM collector_status
WHERE singleton_key = 1
"""

SQL_TODAY_TOTALS = """
SELECT
  COALESCE(SUM(input_tokens), 0) AS input_tokens,
  COALESCE(SUM(output_tokens), 0) AS output_tokens,
  COALESCE(SUM(cache_read_tokens), 0) AS cache_read_tokens,
  COALESCE(SUM(cache_write_tokens), 0) AS cache_write_tokens,
  COALESCE(SUM(thinking_tokens), 0) AS thinking_tokens,
  COALESCE(SUM(actual_cost_usd), 0.0) AS actual_cost_usd_sum,
  COALESCE(SUM(CASE WHEN actual_cost_usd IS NULL THEN estimated_cost_usd ELSE 0 END), 0.0)
    AS estimated_only_cost_usd_sum
FROM raw_usage
WHERE day = ?
"""

SQL_AGENT_TOTALS = """
SELECT
  source,
  COUNT(*) AS events,
  COUNT(DISTINCT l.usage_id) AS linked_events,
  COALESCE(SUM(input_tokens), 0) AS input_tokens,
  COALESCE(SUM(output_tokens), 0) AS output_tokens,
  COALESCE(SUM(cache_read_tokens), 0) AS cache_read_tokens,
  COALESCE(SUM(cache_write_tokens), 0) AS cache_write_tokens,
  COALESCE(SUM(thinking_tokens), 0) AS thinking_tokens,
  COALESCE(SUM(COALESCE(actual_cost_usd, estimated_cost_usd, 0.0)), 0.0) AS total_cost_usd,
  COALESCE(SUM(actual_cost_usd), 0.0) AS actual_cost_usd_sum,
  COALESCE(SUM(CASE WHEN actual_cost_usd IS NULL THEN estimated_cost_usd ELSE 0 END), 0.0)
    AS estimated_only_cost_usd_sum
FROM raw_usage
LEFT JOIN (SELECT DISTINCT usage_id FROM job_usage_link) l ON l.usage_id = raw_usage.id
WHERE day = ?
GROUP BY source
ORDER BY total_cost_usd DESC, output_tokens DESC, source ASC
"""

SQL_TOP_JOBS = """
WITH method_counts AS (
  SELECT
    l.job_id,
    l.link_method,
    COUNT(*) AS method_events,
    COALESCE(MAX(l.confidence), 0.0) AS method_max_confidence
  FROM job_usage_link l
  JOIN raw_usage u ON u.id = l.usage_id
  WHERE u.day = ?
  GROUP BY l.job_id, l.link_method
)
SELECT
  l.job_id,
  COUNT(*) AS events,
  COALESCE(SUM(u.input_tokens), 0) AS input_tokens,
  COALESCE(SUM(u.output_tokens), 0) AS output_tokens,
  COALESCE((
    SELECT mc.link_method
    FROM method_counts mc
    WHERE mc.job_id = l.job_id
    ORDER BY mc.method_events DESC, mc.method_max_confidence DESC, mc.link_method ASC
    LIMIT 1
  ), '') AS primary_link_method,
  COALESCE(SUM(COALESCE(u.actual_cost_usd, u.estimated_cost_usd, 0.0)), 0.0) AS total_cost_usd,
  COALESCE(MAX(l.confidence), 0.0) AS max_confidence,
  COALESCE(AVG(l.confidence), 0.0) AS avg_confidence,
  COALESCE(SUM(CASE WHEN l.confidence < 0.6 THEN 1 ELSE 0 END), 0) AS low_confidence_events
FROM job_usage_link l
JOIN raw_usage u ON u.id = l.usage_id
WHERE u.day = ?
GROUP BY l.job_id
ORDER BY total_cost_usd DESC, output_tokens DESC, l.job_id ASC
LIMIT ?
"""


def empty_dashboard_payload(display_day: str = "") -> dict[str, object]:
    return {
        "display_day": display_day,
        "collector_status": {
            "available": False,
            "phase": "missing",
            "last_heartbeat_at": "",
            "last_scan_started_at": "",
            "last_scan_finished_at": "",
            "scanned_files": 0,
            "parsed_events": 0,
            "last_error": "",
            "is_stale": False,
            "heartbeat_age_sec": 0,
            "launch_mode": "",
            "pane_id": "",
            "window_name": "",
        },
        "today_totals": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "thinking_tokens": 0,
            "actual_cost_usd_sum": 0.0,
            "estimated_only_cost_usd_sum": 0.0,
        },
        "agent_totals": [],
        "top_jobs": [],
    }


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def read_collector_sidecars(db_path: Path) -> dict[str, str]:
    usage_dir = db_path.parent
    return {
        "launch_mode": read_text_file(usage_dir / "collector.launch_mode"),
        "pane_id": read_text_file(usage_dir / "collector.pane_id"),
        "window_name": read_text_file(usage_dir / "collector.window_name"),
    }


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def resolve_dashboard_day(db_path: Path, requested_day: str) -> str:
    if not db_path.exists():
        return requested_day
    with connect_db(db_path) as conn:
        row = conn.execute(
            """
            SELECT
              EXISTS(SELECT 1 FROM raw_usage WHERE day = ?) AS has_requested,
              COALESCE((SELECT MAX(day) FROM raw_usage), '') AS latest_day
            """,
            (requested_day,),
        ).fetchone()
    if row is None:
        return requested_day
    if int(row["has_requested"] or 0):
        return requested_day
    latest_day = str(row["latest_day"] or "")
    return latest_day or requested_day


def collect_dashboard_payload(
    db_path: Path,
    *,
    requested_day: str,
    top_n: int,
) -> dict[str, object]:
    resolved_day = resolve_dashboard_day(db_path, requested_day)
    payload = empty_dashboard_payload(resolved_day)
    if not db_path.exists():
        return payload
    with connect_db(db_path) as conn:
        row = conn.execute(SQL_COLLECTOR_STATUS).fetchone()
        if row is not None:
            sidecars = read_collector_sidecars(db_path)
            payload["collector_status"] = {
                "available": True,
                "phase": str(row["phase"] or "missing"),
                "last_heartbeat_at": str(row["last_heartbeat_at"] or ""),
                "last_scan_started_at": str(row["last_scan_started_at"] or ""),
                "last_scan_finished_at": str(row["last_scan_finished_at"] or ""),
                "scanned_files": int(row["scanned_files"] or 0),
                "parsed_events": int(row["parsed_events"] or 0),
                "last_error": str(row["last_error"] or ""),
                "is_stale": False,
                "heartbeat_age_sec": 0,
                "launch_mode": sidecars["launch_mode"],
                "pane_id": sidecars["pane_id"],
                "window_name": sidecars["window_name"],
            }
        row = conn.execute(SQL_TODAY_TOTALS, (resolved_day,)).fetchone()
        if row is not None:
            payload["today_totals"] = {key: row[key] for key in row.keys()}
        payload["agent_totals"] = [
            dict(row)
            for row in conn.execute(SQL_AGENT_TOTALS, (resolved_day,)).fetchall()
        ]
        payload["top_jobs"] = [
            dict(row)
            for row in conn.execute(SQL_TOP_JOBS, (resolved_day, resolved_day, int(top_n))).fetchall()
        ]
    return payload


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 3:
        raise SystemExit("usage: token_dashboard_shared.py DB_PATH REQUESTED_DAY TOP_N")
    db_path = Path(args[0])
    requested_day = str(args[1])
    top_n = int(args[2])
    print(json.dumps(collect_dashboard_payload(db_path, requested_day=requested_day, top_n=top_n)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
