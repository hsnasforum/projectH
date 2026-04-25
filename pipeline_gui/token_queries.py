"""Read-only token usage queries for the launcher UI."""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from .platform import IS_WINDOWS, _run, _windows_to_wsl_mount, _wsl_path_str, resolve_project_runtime_file
from .token_dashboard_shared import (
    SQL_AGENT_TOTALS as _SQL_AGENT_TOTALS,
    SQL_COLLECTOR_STATUS as _SQL_COLLECTOR_STATUS,
    SQL_TODAY_TOTALS as _SQL_TODAY_TOTALS,
    SQL_TOP_JOBS as _SQL_TOP_JOBS,
    collect_dashboard_payload as _shared_collect_dashboard_payload,
    connect_db as _shared_connect_db,
    read_collector_sidecars as _shared_read_collector_sidecars,
)

COLLECTOR_STALE_AFTER_SEC = 45


@dataclass(slots=True)
class CollectorStatus:
    available: bool = False
    phase: str = "missing"
    last_heartbeat_at: str = ""
    last_scan_started_at: str = ""
    last_scan_finished_at: str = ""
    scanned_files: int = 0
    parsed_events: int = 0
    last_error: str = ""
    is_stale: bool = False
    heartbeat_age_sec: int = 0
    launch_mode: str = ""
    pane_id: str = ""
    window_name: str = ""


@dataclass(slots=True)
class TodayTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    thinking_tokens: int = 0
    actual_cost_usd_sum: float = 0.0
    estimated_only_cost_usd_sum: float = 0.0

    @property
    def total_cost_usd(self) -> float:
        return self.actual_cost_usd_sum + self.estimated_only_cost_usd_sum


@dataclass(slots=True)
class AgentTotals:
    source: str
    events: int
    linked_events: int
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    actual_cost_usd_sum: float
    estimated_only_cost_usd_sum: float
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    thinking_tokens: int = 0


@dataclass(slots=True)
class JobTotals:
    job_id: str
    events: int
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    primary_link_method: str
    max_confidence: float
    avg_confidence: float
    low_confidence_events: int


@dataclass(slots=True)
class LinkMethodSummary:
    source: str
    link_method: str
    events: int
    jobs: int
    avg_confidence: float
    max_confidence: float
    low_confidence_events: int


@dataclass(slots=True)
class LinkSample:
    job_id: str
    source: str
    ts: str
    model: str
    total_tokens: int
    total_cost_usd: float
    confidence: float
    link_method: str
    note: str
    raw_path: str


@dataclass(slots=True)
class UnlinkedUsageSummary:
    source: str
    events: int
    total_tokens: int
    total_cost_usd: float


@dataclass(slots=True)
class TokenDashboard:
    display_day: str
    collector_status: CollectorStatus
    today_totals: TodayTotals
    agent_totals: list[AgentTotals]
    top_jobs: list[JobTotals]


def get_usage_db_path(project: Path) -> Path:
    return Path(project) / ".pipeline" / "usage" / "usage.db"


def _project_from_usage_db_path(db_path: Path) -> Path:
    return db_path.parent.parent.parent


def get_collector_status(
    db_path: str | Path,
    *,
    now: dt.datetime | None = None,
    stale_after_sec: int = COLLECTOR_STALE_AFTER_SEC,
) -> CollectorStatus:
    db = Path(db_path)
    if not db.exists():
        return CollectorStatus()
    with _shared_connect_db(db) as conn:
        row = conn.execute(_SQL_COLLECTOR_STATUS).fetchone()
    if row is None:
        return CollectorStatus()
    sidecars = _shared_read_collector_sidecars(db)
    return _finalize_collector_status(
        CollectorStatus(
            available=True,
            phase=str(row["phase"] or "missing"),
            last_heartbeat_at=str(row["last_heartbeat_at"] or ""),
            last_scan_started_at=str(row["last_scan_started_at"] or ""),
            last_scan_finished_at=str(row["last_scan_finished_at"] or ""),
            scanned_files=int(row["scanned_files"] or 0),
            parsed_events=int(row["parsed_events"] or 0),
            last_error=str(row["last_error"] or ""),
            launch_mode=sidecars["launch_mode"],
            pane_id=sidecars["pane_id"],
            window_name=sidecars["window_name"],
        ),
        now=now,
        stale_after_sec=stale_after_sec,
    )


def _finalize_collector_status(
    status: CollectorStatus,
    *,
    now: dt.datetime | None = None,
    stale_after_sec: int = COLLECTOR_STALE_AFTER_SEC,
) -> CollectorStatus:
    if not status.available or not status.last_heartbeat_at:
        return status
    heartbeat = _parse_ts(status.last_heartbeat_at)
    if heartbeat is None:
        return status
    current = now or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=dt.timezone.utc)
    age_sec = max(0, int((current - heartbeat).total_seconds()))
    is_stale = age_sec > max(0, stale_after_sec)
    phase = "stale" if is_stale and status.phase not in {"missing", "error"} else status.phase
    return CollectorStatus(
        available=True,
        phase=phase,
        last_heartbeat_at=status.last_heartbeat_at,
        last_scan_started_at=status.last_scan_started_at,
        last_scan_finished_at=status.last_scan_finished_at,
        scanned_files=status.scanned_files,
        parsed_events=status.parsed_events,
        last_error=status.last_error,
        is_stale=is_stale,
        heartbeat_age_sec=age_sec,
        launch_mode=status.launch_mode,
        pane_id=status.pane_id,
        window_name=status.window_name,
    )


def get_today_totals(db_path: str | Path, day: str) -> TodayTotals:
    db = Path(db_path)
    if not db.exists():
        return TodayTotals()
    with _shared_connect_db(db) as conn:
        row = conn.execute(_SQL_TODAY_TOTALS, (day,)).fetchone()
    return _row_as_dataclass(row, TodayTotals, default=TodayTotals())


def get_agent_totals_today(db_path: str | Path, day: str) -> list[AgentTotals]:
    db = Path(db_path)
    if not db.exists():
        return []
    with _shared_connect_db(db) as conn:
        rows = conn.execute(_SQL_AGENT_TOTALS, (day,)).fetchall()
    return _rows_as_dataclasses(rows, AgentTotals)


def get_top_jobs_today(db_path: str | Path, day: str, limit: int = 20) -> list[JobTotals]:
    db = Path(db_path)
    if not db.exists():
        return []
    with _shared_connect_db(db) as conn:
        rows = conn.execute(_SQL_TOP_JOBS, (day, day, limit)).fetchall()
    return _rows_as_dataclasses(rows, JobTotals)


def get_link_method_summaries(
    db_path: str | Path,
    *,
    day: str | None = None,
    sources: tuple[str, ...] | None = None,
    low_confidence_threshold: float = 0.6,
) -> list[LinkMethodSummary]:
    db = Path(db_path)
    if not db.exists():
        return []
    where_sql, filter_params = _build_usage_filters(day=day, sources=sources)
    with _shared_connect_db(db) as conn:
        rows = conn.execute(
            f"""
            SELECT
              u.source,
              l.link_method,
              COUNT(*) AS events,
              COUNT(DISTINCT l.job_id) AS jobs,
              COALESCE(AVG(l.confidence), 0.0) AS avg_confidence,
              COALESCE(MAX(l.confidence), 0.0) AS max_confidence,
              COALESCE(SUM(CASE WHEN l.confidence < ? THEN 1 ELSE 0 END), 0) AS low_confidence_events
            FROM job_usage_link l
            JOIN raw_usage u ON u.id = l.usage_id
            WHERE {where_sql}
            GROUP BY u.source, l.link_method
            ORDER BY u.source ASC, avg_confidence DESC, l.link_method ASC
            """,
            (float(low_confidence_threshold), *filter_params),
        ).fetchall()
    return _rows_as_dataclasses(rows, LinkMethodSummary)


def get_link_samples(
    db_path: str | Path,
    *,
    day: str | None = None,
    source: str | None = None,
    link_method: str | None = None,
    max_confidence: float | None = None,
    limit: int = 20,
) -> list[LinkSample]:
    db = Path(db_path)
    if not db.exists():
        return []
    where_sql, params = _build_usage_filters(
        day=day,
        source=source,
        link_method=link_method,
        max_confidence=max_confidence,
    )
    with _shared_connect_db(db) as conn:
        rows = conn.execute(
            f"""
            SELECT
              l.job_id,
              u.source,
              u.ts,
              COALESCE(u.model, '') AS model,
              (u.input_tokens + u.output_tokens + u.cache_read_tokens + u.cache_write_tokens + u.thinking_tokens)
                AS total_tokens,
              COALESCE(u.actual_cost_usd, u.estimated_cost_usd, 0.0) AS total_cost_usd,
              l.confidence,
              l.link_method,
              COALESCE(l.note, '') AS note,
              u.raw_path
            FROM job_usage_link l
            JOIN raw_usage u ON u.id = l.usage_id
            WHERE {where_sql}
            ORDER BY l.confidence ASC, u.ts DESC, l.job_id ASC
            LIMIT ?
            """,
            (*params, int(limit)),
        ).fetchall()
    return _rows_as_dataclasses(rows, LinkSample)


def get_unlinked_usage_counts(
    db_path: str | Path,
    *,
    day: str | None = None,
    sources: tuple[str, ...] | None = None,
) -> list[UnlinkedUsageSummary]:
    db = Path(db_path)
    if not db.exists():
        return []
    where_sql, params = _build_usage_filters(day=day, sources=sources, base_filters=("l.usage_id IS NULL",))
    with _shared_connect_db(db) as conn:
        rows = conn.execute(
            f"""
            SELECT
              u.source,
              COUNT(*) AS events,
              COALESCE(SUM(
                u.input_tokens + u.output_tokens + u.cache_read_tokens + u.cache_write_tokens + u.thinking_tokens
              ), 0) AS total_tokens,
              COALESCE(SUM(COALESCE(u.actual_cost_usd, u.estimated_cost_usd, 0.0)), 0.0) AS total_cost_usd
            FROM raw_usage u
            LEFT JOIN job_usage_link l ON l.usage_id = u.id
            WHERE {where_sql}
            GROUP BY u.source
            ORDER BY events DESC, u.source ASC
            """,
            params,
        ).fetchall()
    return _rows_as_dataclasses(rows, UnlinkedUsageSummary)


def load_token_dashboard(project: Path, day: str | None = None, top_n: int = 5) -> TokenDashboard:
    db_path = get_usage_db_path(project)
    requested_day = _format_day(day)
    if IS_WINDOWS:
        return _load_token_dashboard_via_wsl(
            db_path,
            requested_day=requested_day,
            top_n=top_n,
        )
    dashboard = _normalize_dashboard(
        _shared_collect_dashboard_payload(db_path, requested_day=requested_day, top_n=top_n)
    )
    dashboard.collector_status = _finalize_collector_status(dashboard.collector_status)
    return dashboard


def _normalize_dashboard(raw: object) -> TokenDashboard:
    if not isinstance(raw, dict):
        return _empty_dashboard()
    collector_raw = raw.get("collector_status") if isinstance(raw.get("collector_status"), dict) else {}
    totals_raw = raw.get("today_totals") if isinstance(raw.get("today_totals"), dict) else {}
    agents_raw = raw.get("agent_totals") if isinstance(raw.get("agent_totals"), list) else []
    jobs_raw = raw.get("top_jobs") if isinstance(raw.get("top_jobs"), list) else []
    return TokenDashboard(
        display_day=str(raw.get("display_day") or ""),
        collector_status=CollectorStatus(**collector_raw) if collector_raw else CollectorStatus(),
        today_totals=TodayTotals(**totals_raw) if totals_raw else TodayTotals(),
        agent_totals=[AgentTotals(**item) for item in agents_raw if isinstance(item, dict)],
        top_jobs=[JobTotals(**item) for item in jobs_raw if isinstance(item, dict)],
    )


def _load_token_dashboard_via_wsl(
    db_path: Path,
    *,
    requested_day: str,
    top_n: int,
) -> TokenDashboard:
    script_path = resolve_project_runtime_file(_project_from_usage_db_path(db_path), "token_dashboard_shared.py")
    code, output = _run(
        [
            "python3",
            _windows_to_wsl_mount(script_path),
            _wsl_path_str(db_path),
            requested_day,
            str(top_n),
        ],
        timeout=12.0,
    )
    if code != 0 or not output:
        return _empty_dashboard()
    try:
        dashboard = _normalize_dashboard(json.loads(output))
        dashboard.collector_status = _finalize_collector_status(dashboard.collector_status)
        return dashboard
    except json.JSONDecodeError:
        return _empty_dashboard()


def _format_day(raw: str | None = None) -> str:
    if raw:
        return raw
    return dt.date.today().isoformat()


T = TypeVar("T")


def _empty_dashboard() -> TokenDashboard:
    return TokenDashboard("", CollectorStatus(), TodayTotals(), [], [])


def _row_to_dict(row: object) -> dict[str, object]:
    assert hasattr(row, "keys")
    return {key: row[key] for key in row.keys()}


def _row_as_dataclass(row: object | None, cls: type[T], *, default: T) -> T:
    if row is None:
        return default
    return cls(**_row_to_dict(row))


def _rows_as_dataclasses(rows: list[object], cls: type[T]) -> list[T]:
    return [cls(**_row_to_dict(row)) for row in rows]


def _build_usage_filters(
    *,
    day: str | None = None,
    source: str | None = None,
    sources: tuple[str, ...] | None = None,
    link_method: str | None = None,
    max_confidence: float | None = None,
    base_filters: tuple[str, ...] = ("1=1",),
) -> tuple[str, tuple[object, ...]]:
    filters = list(base_filters)
    params: list[object] = []
    if day:
        filters.append("u.day = ?")
        params.append(day)
    if source:
        filters.append("u.source = ?")
        params.append(source)
    if sources:
        placeholders = ", ".join("?" for _ in sources)
        filters.append(f"u.source IN ({placeholders})")
        params.extend(sources)
    if link_method:
        filters.append("l.link_method = ?")
        params.append(link_method)
    if max_confidence is not None:
        filters.append("l.confidence <= ?")
        params.append(float(max_confidence))
    return " AND ".join(filters), tuple(params)


def _parse_ts(raw: str) -> dt.datetime | None:
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
