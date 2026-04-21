from __future__ import annotations

import datetime as dt
import sqlite3


VERIFY_WINDOW_BEFORE_SEC = 5
VERIFY_WINDOW_AFTER_SEC = 15 * 60
CLAUDE_ARTIFACT_FALLBACK_BEFORE_SEC = 10 * 60
CLAUDE_ARTIFACT_AFTER_SEC = 30
CLAUDE_ARTIFACT_MAX_GAP_SEC = 2 * 60 * 60
CLAUDE_RECENT_HIGH_CONFIDENCE_BEFORE_SEC = 5 * 60
CLAUDE_RECENT_LOW_CONFIDENCE_BEFORE_SEC = 10 * 60
GEMINI_NOTIFY_BEFORE_SEC = 15
GEMINI_NOTIFY_AFTER_SEC = 20 * 60
GEMINI_JOB_LOOKBACK_SEC = 2 * 60 * 60
TURN_SIGNAL_JOB_ID = "turn_signal"


def relink_jobs(conn: sqlite3.Connection) -> int:
    conn.row_factory = sqlite3.Row
    candidate_rows = conn.execute(
        """
        SELECT DISTINCT job_id
        FROM pipeline_event
        WHERE job_id != ?
        ORDER BY job_id ASC
        """,
        (TURN_SIGNAL_JOB_ID,),
    ).fetchall()
    candidate_job_ids = {str(row["job_id"]) for row in candidate_rows if str(row["job_id"] or "")}
    if not candidate_job_ids:
        return 0
    dispatches = conn.execute(
        """
        SELECT *
        FROM pipeline_event
        WHERE event_type = 'dispatch' AND slot = 'slot_verify'
        ORDER BY ts ASC
        """
    ).fetchall()
    links_by_job: dict[str, dict[int, tuple[str, float, str | None]]] = {}
    _merge_links(links_by_job, _build_verify_links(conn, dispatches))
    _merge_links(links_by_job, _build_claude_artifact_links(conn))
    _merge_links(links_by_job, _build_gemini_notify_links(conn))
    for job_id in candidate_job_ids:
        conn.execute("DELETE FROM job_usage_link WHERE job_id = ?", (job_id,))
    rows: list[tuple[str, int, str, float, str, str | None]] = []
    linked_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    for job_id, links in links_by_job.items():
        for usage_id, (method, confidence, note) in sorted(links.items()):
            rows.append((job_id, usage_id, method, confidence, linked_at, note))
    if rows:
        conn.executemany(
            """
            INSERT OR REPLACE INTO job_usage_link (
              job_id, usage_id, link_method, confidence, linked_at, note
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    conn.commit()
    return len(candidate_job_ids)


def relink_job(conn: sqlite3.Connection, job_id: str) -> bool:
    job_event = conn.execute(
        """
        SELECT 1
        FROM pipeline_event
        WHERE job_id = ?
        LIMIT 1
        """,
        (job_id,),
    ).fetchone()
    if job_event is None:
        return False
    relink_jobs(conn)
    return True


def _merge_links(
    target: dict[str, dict[int, tuple[str, float, str | None]]],
    source: dict[str, list[tuple[int, str, float, str | None]]],
) -> None:
    for job_id, links in source.items():
        bucket = target.setdefault(job_id, {})
        for usage_id, method, confidence, note in links:
            current = bucket.get(usage_id)
            if current is None or confidence > current[1]:
                bucket[usage_id] = (method, confidence, note)


def _build_verify_links(
    conn: sqlite3.Connection,
    dispatches: list[sqlite3.Row],
) -> dict[str, list[tuple[int, str, float, str | None]]]:
    if not dispatches:
        return {}
    windows: list[tuple[str, dt.datetime, dt.datetime, dt.datetime]] = []
    for dispatch in dispatches:
        job_id = str(dispatch["job_id"] or "")
        dispatch_ts = _parse_ts(str(dispatch["ts"]))
        if not job_id or dispatch_ts is None:
            continue
        windows.append(
            (
                job_id,
                dispatch_ts,
                dispatch_ts - dt.timedelta(seconds=VERIFY_WINDOW_BEFORE_SEC),
                dispatch_ts + dt.timedelta(seconds=VERIFY_WINDOW_AFTER_SEC),
            )
        )
    if not windows:
        return {}
    min_ts = min(window[2] for window in windows).isoformat().replace("+00:00", "Z")
    max_ts = max(window[3] for window in windows).isoformat().replace("+00:00", "Z")
    usages = conn.execute(
        """
        SELECT id, ts
        FROM raw_usage
        WHERE source = 'codex' AND ts >= ? AND ts <= ?
        ORDER BY ts ASC, id ASC
        """,
        (min_ts, max_ts),
    ).fetchall()
    links_by_job: dict[str, list[tuple[int, str, float, str | None]]] = {}
    for usage in usages:
        usage_ts = _parse_ts(str(usage["ts"]))
        if usage_ts is None:
            continue
        candidates = [window for window in windows if window[2] <= usage_ts <= window[3]]
        if not candidates:
            continue
        best_job_id, best_dispatch_ts, _start, _end = min(
            candidates,
            key=lambda window: (
                abs((usage_ts - window[1]).total_seconds()),
                0 if window[1] <= usage_ts else 1,
                -window[1].timestamp(),
            ),
        )
        delta_sec = int((usage_ts - best_dispatch_ts).total_seconds())
        links_by_job.setdefault(best_job_id, []).append(
            (
                int(usage["id"]),
                "dispatch_slot_verify_window",
                0.9,
                f"slot_verify dispatch window (-5s,+15m); delta={delta_sec}s",
            )
        )
    return links_by_job


def _build_claude_artifact_links(conn: sqlite3.Connection) -> dict[str, list[tuple[int, str, float, str | None]]]:
    artifacts = conn.execute(
        """
        SELECT job_id, ts, artifact_path
        FROM pipeline_event
        WHERE event_type = 'artifact_seen' AND job_id != ?
        ORDER BY ts ASC, raw_line_no ASC
        """,
        (TURN_SIGNAL_JOB_ID,),
    ).fetchall()
    windows: list[tuple[str, dt.datetime, dt.datetime, dt.datetime, str]] = []
    previous_artifact_ts: dt.datetime | None = None
    for artifact in artifacts:
        job_id = str(artifact["job_id"] or "")
        artifact_ts = _parse_ts(str(artifact["ts"]))
        artifact_path = str(artifact["artifact_path"] or "")
        if not job_id or artifact_ts is None or not _is_claude_artifact_path(artifact_path):
            continue
        start = artifact_ts - dt.timedelta(seconds=CLAUDE_ARTIFACT_FALLBACK_BEFORE_SEC)
        anchor_note = "fallback_before_45m"
        if previous_artifact_ts is not None:
            gap_sec = int((artifact_ts - previous_artifact_ts).total_seconds())
            if 0 < gap_sec <= CLAUDE_ARTIFACT_MAX_GAP_SEC:
                start = previous_artifact_ts
                anchor_note = f"previous_artifact gap={gap_sec}s"
            else:
                anchor_note = f"fallback_before_45m gap={gap_sec}s"
        end = artifact_ts + dt.timedelta(seconds=CLAUDE_ARTIFACT_AFTER_SEC)
        windows.append((job_id, artifact_ts, start, end, anchor_note))
        previous_artifact_ts = artifact_ts
    if not windows:
        return {}
    min_ts = min(window[2] for window in windows).isoformat().replace("+00:00", "Z")
    max_ts = max(window[3] for window in windows).isoformat().replace("+00:00", "Z")
    usages = conn.execute(
        """
        SELECT id, ts
        FROM raw_usage
        WHERE source = 'claude' AND ts >= ? AND ts <= ?
        ORDER BY ts ASC, id ASC
        """,
        (min_ts, max_ts),
    ).fetchall()
    links_by_job: dict[str, list[tuple[int, str, float, str | None]]] = {}
    for usage in usages:
        usage_ts = _parse_ts(str(usage["ts"]))
        if usage_ts is None:
            continue
        candidates = [window for window in windows if window[2] <= usage_ts <= window[3]]
        if not candidates:
            continue
        best_job_id, best_artifact_ts, _start, _end, anchor_note = min(
            candidates,
            key=lambda window: (
                0 if usage_ts <= window[1] else 1,
                abs((window[1] - usage_ts).total_seconds()),
                -window[1].timestamp(),
            ),
        )
        delta_sec = int((usage_ts - best_artifact_ts).total_seconds())
        confidence = _claude_confidence(delta_sec)
        if confidence is None:
            continue
        links_by_job.setdefault(best_job_id, []).append(
            (
                int(usage["id"]),
                "artifact_seen_work_window",
                confidence,
                f"work artifact window ({anchor_note}; fallback_before=10m; after=30s); delta={delta_sec}s",
            )
        )
    return links_by_job


def _build_gemini_notify_links(conn: sqlite3.Connection) -> dict[str, list[tuple[int, str, float, str | None]]]:
    notify_rows = conn.execute(
        """
        SELECT event_key, ts
        FROM pipeline_event
        WHERE event_type IN ('gemini_notify', 'advisory_notify')
        ORDER BY ts ASC, raw_line_no ASC
        """
    ).fetchall()
    windows: list[tuple[str, dt.datetime, dt.datetime, dt.datetime, str, int]] = []
    for notify in notify_rows:
        notify_ts = _parse_ts(str(notify["ts"]))
        if notify_ts is None:
            continue
        cutoff = (notify_ts - dt.timedelta(seconds=GEMINI_JOB_LOOKBACK_SEC)).isoformat().replace("+00:00", "Z")
        notify_ts_raw = notify_ts.isoformat().replace("+00:00", "Z")
        related = conn.execute(
            """
            SELECT job_id, ts, event_type
            FROM pipeline_event
            WHERE job_id != ? AND ts >= ? AND ts <= ?
            ORDER BY ts DESC, raw_line_no DESC
            LIMIT 1
            """,
            (TURN_SIGNAL_JOB_ID, cutoff, notify_ts_raw),
        ).fetchone()
        if related is None:
            continue
        related_job_id = str(related["job_id"] or "")
        related_ts = _parse_ts(str(related["ts"]))
        related_event_type = str(related["event_type"] or "")
        if not related_job_id or related_ts is None:
            continue
        windows.append(
            (
                related_job_id,
                notify_ts,
                notify_ts - dt.timedelta(seconds=GEMINI_NOTIFY_BEFORE_SEC),
                notify_ts + dt.timedelta(seconds=GEMINI_NOTIFY_AFTER_SEC),
                related_event_type or "job_event",
                int((notify_ts - related_ts).total_seconds()),
            )
        )
    if not windows:
        return {}
    min_ts = min(window[2] for window in windows).isoformat().replace("+00:00", "Z")
    max_ts = max(window[3] for window in windows).isoformat().replace("+00:00", "Z")
    usages = conn.execute(
        """
        SELECT id, ts
        FROM raw_usage
        WHERE source = 'gemini' AND ts >= ? AND ts <= ?
        ORDER BY ts ASC, id ASC
        """,
        (min_ts, max_ts),
    ).fetchall()
    links_by_job: dict[str, list[tuple[int, str, float, str | None]]] = {}
    for usage in usages:
        usage_ts = _parse_ts(str(usage["ts"]))
        if usage_ts is None:
            continue
        candidates = [window for window in windows if window[2] <= usage_ts <= window[3]]
        if not candidates:
            continue
        best_job_id, best_notify_ts, _start, _end, related_event_type, job_gap_sec = min(
            candidates,
            key=lambda window: (
                0 if window[1] <= usage_ts else 1,
                abs((usage_ts - window[1]).total_seconds()),
                -window[1].timestamp(),
            ),
        )
        delta_sec = int((usage_ts - best_notify_ts).total_seconds())
        confidence = 0.5 if 0 <= delta_sec <= 300 else 0.4
        links_by_job.setdefault(best_job_id, []).append(
            (
                int(usage["id"]),
                "gemini_notify_recent_job_window",
                confidence,
                f"gemini_notify via {related_event_type} ({job_gap_sec}s before notify); delta={delta_sec}s",
            )
        )
    return links_by_job


def _claude_confidence(delta_sec: int) -> float | None:
    if -CLAUDE_RECENT_HIGH_CONFIDENCE_BEFORE_SEC <= delta_sec <= 30:
        return 0.7
    if -CLAUDE_RECENT_LOW_CONFIDENCE_BEFORE_SEC <= delta_sec <= 30:
        return 0.55
    return None


def _is_claude_artifact_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith("work/") or "/work/" in normalized


def _parse_ts(raw: str) -> dt.datetime | None:
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
