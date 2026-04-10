from __future__ import annotations

from dataclasses import dataclass

from .agents import STATUS_COLORS, _parse_elapsed, format_elapsed, format_focus_output
from .backend import format_control_summary, time_ago
from .tokens import format_token_usage_note

_AGENT_STATUS_LABELS = {
    "READY": "대기",
    "WORKING": "작업 중",
    "OFF": "꺼짐",
    "DEAD": "종료됨",
    "BOOTING": "기동 중",
}


@dataclass(frozen=True)
class ControlPresentation:
    active_text: str
    stale_text: str
    active_fg: str
    active_box_bg: str
    active_box_border: str
    active_title_fg: str
    stale_visible: bool
    stale_box_bg: str = "#14161d"
    stale_box_border: str = "#374151"
    stale_title_fg: str = "#94a3b8"
    stale_label_fg: str = "#94a3b8"


@dataclass(frozen=True)
class ConsolePresentation:
    focus_title: str
    focus_text: str
    artifacts_title: str
    artifact_color: str
    run_context_text: str
    run_context_fg: str
    work_text: str
    verify_text: str
    log_title: str
    log_text: str


@dataclass(frozen=True)
class AgentCardPresentation:
    status_text: str
    status_fg: str
    note_text: str | None
    note_fg: str
    quota_text: str
    quota_fg: str
    card_border: str
    card_thickness: int
    card_bg: str


def build_control_presentation(
    control_slots: object,
    verify_activity: object | None,
    turn_state: dict[str, object] | None = None,
) -> ControlPresentation:
    active_text, stale_text = format_control_summary(control_slots, verify_activity=verify_activity, turn_state=turn_state)
    active = None
    if isinstance(control_slots, dict):
        raw_active = control_slots.get("active")
        if isinstance(raw_active, dict):
            active = raw_active
    if verify_activity is not None and not (active is not None and active.get("status") == "needs_operator"):
        return ControlPresentation(
            active_text=active_text,
            stale_text=stale_text,
            active_fg="#93c5fd",
            active_box_bg="#101826",
            active_box_border="#1d4ed8",
            active_title_fg="#60a5fa",
            stale_visible=bool(stale_text),
        )
    if active is None:
        return ControlPresentation(
            active_text=active_text,
            stale_text=stale_text,
            active_fg="#9ca3af",
            active_box_bg="#141418",
            active_box_border="#30363d",
            active_title_fg="#6b7280",
            stale_visible=bool(stale_text),
        )
    if active.get("status") == "needs_operator":
        return ControlPresentation(
            active_text=active_text,
            stale_text=stale_text,
            active_fg="#fca5a5",
            active_box_bg="#2a1015",
            active_box_border="#7f1d1d",
            active_title_fg="#f87171",
            stale_visible=bool(stale_text),
        )
    return ControlPresentation(
        active_text=active_text,
        stale_text=stale_text,
        active_fg="#93c5fd",
        active_box_bg="#101826",
        active_box_border="#1d4ed8",
        active_title_fg="#60a5fa",
        stale_visible=bool(stale_text),
    )


def build_console_presentation(*, selected_agent: str, snapshot: object) -> ConsolePresentation:
    session_ok = bool(_snapshot_get(snapshot, "session_ok", False))
    watcher_alive = bool(_snapshot_get(snapshot, "watcher_alive", False))
    is_live = session_ok and watcher_alive
    pane_map = _snapshot_get(snapshot, "pane_map", {}) or {}
    run = _snapshot_get(snapshot, "run_summary", {}) or {}
    agents = list(_snapshot_get(snapshot, "agents", []) or [])
    work_name = str(_snapshot_get(snapshot, "work_name", "—") or "—")
    work_mtime = float(_snapshot_get(snapshot, "work_mtime", 0.0) or 0.0)
    verify_name = str(_snapshot_get(snapshot, "verify_name", "—") or "—")
    verify_mtime = float(_snapshot_get(snapshot, "verify_mtime", 0.0) or 0.0)
    log_lines = list(_snapshot_get(snapshot, "log_lines", []) or [])

    selected_text = format_focus_output(str(pane_map.get(selected_agent, "") if isinstance(pane_map, dict) else ""))
    if selected_text in ("(출력 없음)", "(표시할 출력 없음)") and is_live:
        fallback_parts: list[str] = []
        run_turn = str(run.get("turn", "") or "") if isinstance(run, dict) else ""
        run_phase = str(run.get("phase", "") or "") if isinstance(run, dict) else ""
        run_job = str(run.get("job", "") or "") if isinstance(run, dict) else ""
        if run_turn:
            fallback_parts.append(f"현재 턴: {run_turn}")
        if run_phase:
            fallback_parts.append(f"단계: {run_phase}")
        if run_job:
            fallback_parts.append(f"작업: {run_job}")
        for label, status, note, _quota in agents:
            if label == selected_agent and status == "WORKING" and note:
                fallback_parts.append(f"{label}: 작업 중 ({note})")
            elif label == selected_agent and status != "OFF":
                fallback_parts.append(f"{label}: {_AGENT_STATUS_LABELS.get(status, status)}")
        if fallback_parts:
            selected_text = "\n".join(fallback_parts)

    if is_live:
        title_suffix = "최근 pane 출력" if selected_text not in ("(출력 없음)", "(표시할 출력 없음)") else "실행 문맥"
        focus_title = f"{selected_agent.upper()} • {title_suffix}"
    else:
        focus_title = f"{selected_agent.upper()} • 최근 pane 출력 (마지막 실행)"

    artifact_color = "#c0a060" if is_live else "#505868"
    artifacts_title = "산출물" if is_live else "산출물 (마지막 실행)"

    run_job = str(run.get("job", "") or "") if isinstance(run, dict) else ""
    run_phase = str(run.get("phase", "") or "") if isinstance(run, dict) else ""
    run_turn = str(run.get("turn", "") or "") if isinstance(run, dict) else ""
    if is_live and (run_job or run_phase or run_turn):
        parts = []
        if run_turn:
            parts.append(f"턴: {run_turn}")
        if run_phase:
            parts.append(f"단계: {run_phase}")
        if run_job:
            short_job = run_job.split("-", 1)[1][:50] if "-" in run_job else run_job[:50]
            parts.append(f"작업: {short_job}")
        run_context_text = " │ ".join(parts)
        run_context_fg = "#5b9cf6"
    elif not is_live and run_job:
        short_job = run_job.split("-", 1)[1][:50] if "-" in run_job else run_job[:50]
        run_context_text = f"마지막 작업: {short_job}"
        run_context_fg = "#404058"
    else:
        run_context_text = ""
        run_context_fg = "#404058"

    work_text = f"최신 work:   {work_name}"
    if work_mtime:
        work_text += f" ({time_ago(work_mtime)})"
    verify_text = f"최신 verify: {verify_name}"
    if verify_mtime:
        verify_text += f" ({time_ago(verify_mtime)})"

    log_hint_parts = []
    if run_turn:
        log_hint_parts.append(run_turn)
    if run_phase:
        log_hint_parts.append(run_phase)
    log_hint = f" • {' → '.join(log_hint_parts)}" if log_hint_parts else ""
    if is_live:
        log_title = f"워처 로그{log_hint}"
    else:
        log_title = f"워처 로그 (마지막 실행){log_hint}"
    log_text = "\n".join(
        (line.strip()[:140] + "…" if len(line.strip()) > 143 else line.strip())
        for line in log_lines
    )

    return ConsolePresentation(
        focus_title=focus_title,
        focus_text=selected_text,
        artifacts_title=artifacts_title,
        artifact_color=artifact_color,
        run_context_text=run_context_text,
        run_context_fg=run_context_fg,
        work_text=work_text,
        verify_text=verify_text,
        log_title=log_title,
        log_text=log_text,
    )


def build_agent_card_presentations(
    *,
    agents: list[tuple[str, str, str, str]],
    selected_agent: str,
    token_usage: object,
    working_since: dict[str, float],
    now: float,
) -> tuple[list[AgentCardPresentation], dict[str, float]]:
    updated_working_since = dict(working_since)
    presentations: list[AgentCardPresentation] = []
    for label, status, note, quota in agents:
        color = STATUS_COLORS.get(status, "#666666")
        if status == "WORKING":
            note_text: str | None
            if label not in updated_working_since:
                elapsed = _parse_elapsed(note)
                updated_working_since[label] = now - elapsed if elapsed > 0 else now
                note_text = note or format_elapsed(0)
            else:
                elapsed = _parse_elapsed(note)
                if elapsed > 0:
                    computed = now - updated_working_since[label]
                    if abs(computed - elapsed) > 5:
                        updated_working_since[label] = now - elapsed
                note_text = None
        else:
            updated_working_since.pop(label, None)
            note_text = note or "대기 중"

        usage_quota = ""
        if isinstance(token_usage, dict):
            raw_usage = token_usage.get(label)
            if isinstance(raw_usage, dict):
                usage_quota = format_token_usage_note(raw_usage)
        display_quota = usage_quota or quota

        if label == selected_agent:
            card_border = "#6ea8ff"
            card_thickness = 3
            card_bg = "#1a1a30"
        elif status == "WORKING":
            card_border = "#4ade80"
            card_thickness = 2
            card_bg = "#0e2a18"
        else:
            card_border = "#1e1e2e"
            card_thickness = 1
            card_bg = "#12121a"

        presentations.append(
            AgentCardPresentation(
                status_text=_AGENT_STATUS_LABELS.get(status, status),
                status_fg=color,
                note_text=note_text,
                note_fg="#9ca3af",
                quota_text=f"사용량: {display_quota}" if display_quota else "사용량: —",
                quota_fg="#7c8798",
                card_border=card_border,
                card_thickness=card_thickness,
                card_bg=card_bg,
            )
        )
    return presentations, updated_working_since


def build_empty_agent_card_presentation() -> AgentCardPresentation:
    return AgentCardPresentation(
        status_text="—",
        status_fg="#666666",
        note_text="",
        note_fg="#666666",
        quota_text="사용량: —",
        quota_fg="#666666",
        card_border="#2a2a2a",
        card_thickness=1,
        card_bg="#12121a",
    )


def _snapshot_get(snapshot: object, key: str, default: object) -> object:
    getter = getattr(snapshot, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(snapshot, key, default)
