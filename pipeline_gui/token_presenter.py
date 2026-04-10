from __future__ import annotations

import time
from dataclasses import dataclass

from .formatting import format_compact_count
from .tokens import format_token_usage_note


@dataclass(frozen=True)
class TokenPanelPresentation:
    status_text: str
    totals_text: str
    agents_text: str
    selected_text: str
    jobs_text: str


def build_token_panel_presentation(
    *,
    selected_agent: str,
    token_usage: object,
    dashboard: object | None,
    token_loading: bool,
) -> TokenPanelPresentation:
    if dashboard is None:
        return TokenPanelPresentation(
            status_text=_empty_label("수집기"),
            totals_text=_empty_label("오늘"),
            agents_text=_empty_label("에이전트"),
            selected_text=_empty_label(f"선택 에이전트 {selected_agent.upper()}"),
            jobs_text=_empty_label("주요 작업"),
        )

    collector = getattr(dashboard, "collector_status", None)
    totals = getattr(dashboard, "today_totals", None)
    agents = list(getattr(dashboard, "agent_totals", []) or [])
    jobs = list(getattr(dashboard, "top_jobs", []) or [])
    display_day = str(getattr(dashboard, "display_day", "") or "")
    today_day = time.strftime("%Y-%m-%d")
    totals_label = "오늘" if not display_day or display_day == today_day else f"최근 {display_day}"
    totals_empty = _totals_empty(totals)

    return TokenPanelPresentation(
        status_text=_format_status_line(collector, token_loading=token_loading),
        totals_text=_format_totals_line(
            totals,
            totals_label=totals_label,
            token_loading=token_loading,
            totals_empty=totals_empty,
            has_agents=bool(agents),
            has_jobs=bool(jobs),
        ),
        agents_text=_format_agents_line(agents, token_loading=token_loading),
        selected_text=_format_selected_line(
            selected_agent=selected_agent,
            token_usage=token_usage,
            dashboard=dashboard,
            token_loading=token_loading,
            totals_label=totals_label,
        ),
        jobs_text=_format_jobs_line(
            jobs,
            token_loading=token_loading,
            has_agents=bool(agents),
            totals_empty=totals_empty,
        ),
    )


def format_token_job_segment(item: object) -> str:
    job_id = str(getattr(item, "job_id", "") or "")
    short_job = job_id.split("-", 1)[1][:28] if "-" in job_id else job_id[:28]
    cost = float(getattr(item, "total_cost_usd", 0.0) or 0.0)
    method = str(getattr(item, "primary_link_method", "") or "")
    confidence = float(getattr(item, "max_confidence", 0.0) or 0.0)
    low_confidence_events = int(getattr(item, "low_confidence_events", 0) or 0)
    total_events = int(getattr(item, "events", 0) or 0)
    segment = short_job
    if cost:
        segment += f" ${cost:.2f}"
    if method:
        segment += f" {_short_link_method(method)}"
    segment += f" c={confidence:.2f}"
    if total_events:
        segment += f" low={low_confidence_events}/{total_events}"
    return segment


def _format_selected_line(
    *,
    selected_agent: str,
    token_usage: object,
    dashboard: object,
    token_loading: bool,
    totals_label: str,
) -> str:
    title = f"선택 에이전트 {selected_agent.upper()}: "
    usage_summary: dict[str, object] = {}
    if isinstance(token_usage, dict):
        raw_usage = token_usage.get(selected_agent)
        if isinstance(raw_usage, dict):
            usage_summary = raw_usage
    agent_row = None
    for item in list(getattr(dashboard, "agent_totals", []) or []):
        if str(getattr(item, "source", "") or "").lower() == selected_agent.lower():
            agent_row = item
            break

    if token_loading and not usage_summary.get("available") and agent_row is None:
        return title + "불러오는 중..."

    parts: list[str] = []
    usage_note = format_token_usage_note(usage_summary) if usage_summary else ""
    if usage_note:
        parts.append(f"usage {usage_note}")

    if agent_row is not None:
        input_tokens = format_compact_count(int(getattr(agent_row, "input_tokens", 0) or 0))
        output_tokens = format_compact_count(int(getattr(agent_row, "output_tokens", 0) or 0))
        events = int(getattr(agent_row, "events", 0) or 0)
        linked_events = int(getattr(agent_row, "linked_events", 0) or 0)
        total_cost = float(getattr(agent_row, "total_cost_usd", 0.0) or 0.0)
        parts.append(f"{totals_label.lower()} {input_tokens}/{output_tokens}")
        if total_cost:
            parts.append(f"${total_cost:.2f}")
        if events > 0:
            if linked_events == 0:
                parts.append("미연결")
            else:
                parts.append(f"연결 {linked_events}/{events}")

    if not parts:
        parts.append("데이터 없음")
    return title + " · ".join(parts)


def _empty_label(label: str) -> str:
    return f"{label}: —"


def _loading_label(label: str) -> str:
    return f"{label}: 불러오는 중..."


def _totals_empty(totals: object) -> bool:
    return bool(
        totals is not None
        and not int(getattr(totals, "input_tokens", 0) or 0)
        and not int(getattr(totals, "output_tokens", 0) or 0)
        and not int(getattr(totals, "cache_read_tokens", 0) or 0)
        and not int(getattr(totals, "cache_write_tokens", 0) or 0)
        and not int(getattr(totals, "thinking_tokens", 0) or 0)
        and not float(getattr(totals, "actual_cost_usd_sum", 0.0) or 0.0)
        and not float(getattr(totals, "estimated_only_cost_usd_sum", 0.0) or 0.0)
    )


def _format_status_line(collector: object, *, token_loading: bool) -> str:
    if collector is None or not getattr(collector, "available", False):
        return _loading_label("수집기") if token_loading else "수집기: 없음"
    phase = getattr(collector, "phase", "missing")
    heartbeat = str(getattr(collector, "last_heartbeat_at", "") or "")
    heartbeat_age_sec = int(getattr(collector, "heartbeat_age_sec", 0) or 0)
    parsed = int(getattr(collector, "parsed_events", 0) or 0)
    files = int(getattr(collector, "scanned_files", 0) or 0)
    error = str(getattr(collector, "last_error", "") or "")
    launch_mode = str(getattr(collector, "launch_mode", "") or "")
    window_name = str(getattr(collector, "window_name", "") or "")
    phase_map = {
        "idle": "대기",
        "running": "실행 중",
        "starting": "시작 중",
        "stopping": "중지 중",
        "error": "오류",
        "missing": "없음",
    }
    status_parts = [f"수집기: {phase_map.get(phase, phase)}"]
    if launch_mode:
        status_parts.append(f"{launch_mode}:{window_name}" if launch_mode == "tmux" and window_name else launch_mode)
    if heartbeat:
        status_parts.append(f"HB {heartbeat[11:19] if len(heartbeat) >= 19 else heartbeat}")
    if getattr(collector, "is_stale", False) and heartbeat_age_sec:
        status_parts.append(f"지연 {heartbeat_age_sec}초")
    if files or parsed:
        status_parts.append(f"파일 {files}개 · 이벤트 {parsed}개")
    if error:
        status_parts.append(f"오류 {error[:60]}")
    return " | ".join(status_parts)


def _format_totals_line(
    totals: object,
    *,
    totals_label: str,
    token_loading: bool,
    totals_empty: bool,
    has_agents: bool,
    has_jobs: bool,
) -> str:
    if token_loading and totals_empty and not has_agents and not has_jobs:
        return _loading_label(totals_label)
    if totals is None:
        return _empty_label(totals_label)
    total_parts = [
        f"{totals_label} 입력 {format_compact_count(int(getattr(totals, 'input_tokens', 0) or 0))}",
        f"출력 {format_compact_count(int(getattr(totals, 'output_tokens', 0) or 0))}",
    ]
    cache_total = int(getattr(totals, "cache_read_tokens", 0) or 0) + int(
        getattr(totals, "cache_write_tokens", 0) or 0
    )
    thinking = int(getattr(totals, "thinking_tokens", 0) or 0)
    if cache_total:
        total_parts.append(f"캐시 {format_compact_count(cache_total)}")
    if thinking:
        total_parts.append(f"추론 {format_compact_count(thinking)}")
    actual_cost = float(getattr(totals, "actual_cost_usd_sum", 0.0) or 0.0)
    estimated_cost = float(getattr(totals, "estimated_only_cost_usd_sum", 0.0) or 0.0)
    total_parts.append(f"비용 ${actual_cost + estimated_cost:.2f}")
    if actual_cost:
        total_parts.append(f"실비 ${actual_cost:.2f}")
    if estimated_cost:
        total_parts.append(f"예상 ${estimated_cost:.2f}")
    return " | ".join(total_parts)


def _format_agents_line(agents: list[object], *, token_loading: bool) -> str:
    if token_loading and not agents:
        return _loading_label("에이전트")
    if not agents:
        return _empty_label("에이전트")
    return "에이전트: " + " | ".join(_format_agent_segment(item) for item in agents[:3])


def _format_agent_segment(item: object) -> str:
    source = str(getattr(item, "source", "") or "").upper()
    inp = format_compact_count(int(getattr(item, "input_tokens", 0) or 0))
    out = format_compact_count(int(getattr(item, "output_tokens", 0) or 0))
    events = int(getattr(item, "events", 0) or 0)
    linked_events = int(getattr(item, "linked_events", 0) or 0)
    cost = float(getattr(item, "total_cost_usd", 0.0) or 0.0)
    segment = f"{source} {inp}/{out}"
    if cost:
        segment += f" ${cost:.2f}"
    if events > 0 and linked_events == 0:
        segment += " 미연결"
    return segment


def _format_jobs_line(
    jobs: list[object],
    *,
    token_loading: bool,
    has_agents: bool,
    totals_empty: bool,
) -> str:
    if token_loading and not jobs:
        return _loading_label("주요 작업")
    if not jobs and (has_agents or not totals_empty):
        return "주요 작업: 연결된 작업이 아직 없습니다"
    if not jobs:
        return _empty_label("주요 작업")
    return "주요 작업: " + " | ".join(format_token_job_segment(item) for item in jobs[:3])


def _short_link_method(method: str) -> str:
    return (
        method.replace("dispatch_slot_verify_window", "dispatch")
        .replace("artifact_seen_work_window", "artifact")
        .replace("gemini_notify_recent_job_window", "gemini")
    )
