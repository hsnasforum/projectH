from __future__ import annotations

from dataclasses import dataclass

from .agents import STATUS_COLORS, _parse_elapsed, format_elapsed
from .backend import format_control_summary, time_ago
from .tokens import format_token_usage_note
from pipeline_runtime.turn_arbitration import canonical_turn_state_name

_AGENT_STATUS_LABELS = {
    "READY": "대기",
    "WORKING": "작업 중",
    "OFF": "꺼짐",
    "DEAD": "종료됨",
    "BOOTING": "기동 중",
}

_AGENT_NOTE_LABELS = {
    "prompt_visible": "대기 중",
    "waiting_next_control": "다음 지시 대기",
    "signal_mismatch": "상태 확인 필요",
    "verify_pending": "검증 대기",
    "followup": "후속 처리",
    "implement": "구현 중",
    "progress:implementing": "구현 진행 중",
    "progress:work_closeout_written": "work 작성 완료",
    "progress:verify_dispatch_pending": "검증 준비 중",
    "progress:running_verification": "검증 실행 중",
    "progress:verify_note_written_next_control_pending": "verify 작성 완료, 다음 지시 정리",
    "progress:receipt_close_pending": "receipt 마감 대기",
    "progress:operator_gate_followup": "operator gate 후속 처리",
    "progress:next_control_pending": "다음 control 정리 중",
    "progress:next_control_written": "다음 control 작성 완료",
    "progress:advisory_running": "자문 진행 중",
    "progress:operator_boundary": "operator 경계 대기",
}

_AUTOMATION_HEALTH_LABELS = {
    "ok": "정상",
    "recovering": "복구 중",
    "attention": "주의",
    "needs_operator": "개입 필요",
}


@dataclass(frozen=True)
class PipelineStatusPresentation:
    pipeline_text: str
    status_text: str
    fg: str
    bg: str


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


def build_pipeline_status_presentation(
    *,
    runtime_state: str,
    automation_health: str = "ok",
) -> PipelineStatusPresentation:
    health = str(automation_health or "ok")
    if health != "ok":
        label = _AUTOMATION_HEALTH_LABELS.get(health, health)
        if health == "needs_operator":
            return PipelineStatusPresentation(f"파이프라인: ! {label}", label, "#f87171", "#2a1015")
        if health == "attention":
            return PipelineStatusPresentation(f"파이프라인: ▲ {label}", label, "#fb923c", "#2a160f")
        return PipelineStatusPresentation(f"파이프라인: ◐ {label}", label, "#fbbf24", "#2b2110")

    state = str(runtime_state or "STOPPED")
    if state == "RUNNING":
        return PipelineStatusPresentation("파이프라인: ● 실행 중", "실행 중", "#4ade80", "#0a2a18")
    if state == "STARTING":
        return PipelineStatusPresentation("파이프라인: ◐ 기동 중", "기동 중", "#fbbf24", "#2b2110")
    if state == "DEGRADED":
        return PipelineStatusPresentation("파이프라인: ▲ 부분 장애", "부분 장애", "#fb923c", "#2a160f")
    if state == "BROKEN":
        return PipelineStatusPresentation("파이프라인: ✗ 장애", "장애", "#f87171", "#2a1015")
    return PipelineStatusPresentation("파이프라인: ■ 중지됨", "중지됨", "#f87171", "#2a1015")


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
    runtime_state = str(_snapshot_get(snapshot, "runtime_state", "STOPPED") or "STOPPED")
    degraded_reason = str(_snapshot_get(snapshot, "degraded_reason", "") or "")
    automation_health = str(_snapshot_get(snapshot, "automation_health", "ok") or "ok")
    automation_reason = str(_snapshot_get(snapshot, "automation_reason_code", "") or "")
    automation_family = str(_snapshot_get(snapshot, "automation_incident_family", "") or "")
    automation_action = str(_snapshot_get(snapshot, "automation_next_action", "continue") or "continue")
    is_live = runtime_state in {"STARTING", "RUNNING", "DEGRADED"}
    lane_details = _snapshot_get(snapshot, "lane_details", {}) or {}
    run = _snapshot_get(snapshot, "run_summary", {}) or {}
    agents = list(_snapshot_get(snapshot, "agents", []) or [])
    work_name = str(_snapshot_get(snapshot, "work_name", "—") or "—")
    work_mtime = float(_snapshot_get(snapshot, "work_mtime", 0.0) or 0.0)
    verify_name = str(_snapshot_get(snapshot, "verify_name", "—") or "—")
    verify_mtime = float(_snapshot_get(snapshot, "verify_mtime", 0.0) or 0.0)
    turn_state = _snapshot_get(snapshot, "turn_state", {}) or {}
    log_lines = list(_snapshot_get(snapshot, "log_lines", []) or [])

    focus_lines: list[str] = [f"runtime: {runtime_state}"]
    if automation_health != "ok" or automation_reason:
        focus_lines.append(f"automation_health: {automation_health}")
        if automation_reason:
            focus_lines.append(f"automation_reason_code: {automation_reason}")
        if automation_family:
            focus_lines.append(f"automation_incident_family: {automation_family}")
        if automation_action:
            focus_lines.append(f"automation_next_action: {automation_action}")
    selected_lane = dict(lane_details.get(selected_agent) or {}) if isinstance(lane_details, dict) else {}
    selected_state = str(selected_lane.get("state") or "")
    if selected_state:
        focus_lines.append(f"lane_state: {selected_state}")
    else:
        for label, status, note, _quota in agents:
            if label != selected_agent:
                continue
            focus_lines.append(f"lane_state: {status}")
            if note:
                focus_lines.append(f"note: {note}")
            break
    note = str(selected_lane.get("note") or "")
    if note:
        focus_lines.append(f"note: {note}")
    progress_phase = str(selected_lane.get("progress_phase") or "")
    if progress_phase:
        focus_lines.append(f"progress_phase: {progress_phase}")
    progress_reason = str(selected_lane.get("progress_reason") or "")
    if progress_reason:
        focus_lines.append(f"progress_reason: {progress_reason}")
    if "attachable" in selected_lane:
        focus_lines.append(f"attachable: {'true' if bool(selected_lane.get('attachable')) else 'false'}")
    pid_value = selected_lane.get("pid")
    if pid_value not in (None, ""):
        focus_lines.append(f"pid: {pid_value}")
    last_heartbeat_at = str(selected_lane.get("last_heartbeat_at") or "")
    if last_heartbeat_at:
        focus_lines.append(f"last_heartbeat_at: {last_heartbeat_at}")
    last_event_at = str(selected_lane.get("last_event_at") or "")
    if last_event_at and last_event_at != last_heartbeat_at:
        focus_lines.append(f"last_event_at: {last_event_at}")
    last_wrapper_event = str(selected_lane.get("last_wrapper_event") or "")
    if last_wrapper_event:
        focus_lines.append(f"last_wrapper_event: {last_wrapper_event}")
    if degraded_reason and runtime_state in {"DEGRADED", "BROKEN"}:
        focus_lines.append(f"degraded_reason: {degraded_reason}")

    run_turn = str(run.get("turn", "") or "") if isinstance(run, dict) else ""
    run_phase = str(run.get("phase", "") or "") if isinstance(run, dict) else ""
    run_phase_label = _format_progress_phase(run_phase)
    run_job = str(run.get("job", "") or "") if isinstance(run, dict) else ""
    if run_turn:
        focus_lines.append(f"active_turn: {run_turn}")
    if run_phase:
        focus_lines.append(f"active_phase: {run_phase}")
    if run_job:
        focus_lines.append(f"job_id: {run_job}")
    selected_text = "\n".join(focus_lines) if focus_lines else "(runtime 정보 없음)"

    if runtime_state == "BROKEN":
        focus_title = f"{selected_agent.upper()} • Runtime 장애 상태"
    elif is_live:
        focus_title = f"{selected_agent.upper()} • Runtime 상태"
    else:
        focus_title = f"{selected_agent.upper()} • 최근 Runtime 상태"

    artifact_color = "#c0a060" if is_live else "#505868"
    artifacts_title = "라운드 기록" if is_live else "라운드 기록 (마지막 실행)"

    if is_live and (run_job or run_phase or run_turn):
        parts = []
        if run_turn:
            parts.append(f"턴: {run_turn}")
        if run_phase:
            parts.append(f"단계: {run_phase_label}")
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

    work_text, verify_text = _build_round_record_lines(
        is_live=is_live,
        turn_state=turn_state if isinstance(turn_state, dict) else {},
        work_name=work_name,
        work_mtime=work_mtime,
        verify_name=verify_name,
        verify_mtime=verify_mtime,
    )

    log_hint_parts = []
    if run_turn:
        log_hint_parts.append(run_turn)
    if run_phase:
        log_hint_parts.append(run_phase_label)
    log_hint = f" • {' → '.join(log_hint_parts)}" if log_hint_parts else ""
    if is_live:
        log_title = f"Runtime 이벤트{log_hint}"
    else:
        log_title = f"Runtime 이벤트 (마지막 실행){log_hint}"
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


def _format_record_line(prefix: str, name: str, mtime: float) -> str:
    text = f"{prefix}: {name}"
    if mtime:
        text += f" ({time_ago(mtime)})"
    return text


def _build_round_record_lines(
    *,
    is_live: bool,
    turn_state: dict[str, object],
    work_name: str,
    work_mtime: float,
    verify_name: str,
    verify_mtime: float,
) -> tuple[str, str]:
    if not is_live:
        return (
            _format_record_line("마지막 work", work_name, work_mtime),
            _format_record_line("마지막 verify", verify_name, verify_mtime),
        )

    state_value = canonical_turn_state_name(
        turn_state.get("state"),
        legacy_state=turn_state.get("legacy_state"),
    )
    entered_at = float(turn_state.get("entered_at") or 0.0)
    work_is_current = bool(work_mtime and entered_at and work_mtime >= entered_at)
    verify_is_current = bool(verify_mtime and entered_at and verify_mtime >= entered_at)

    latest_work_text = _format_record_line("최신 work", work_name, work_mtime)
    latest_verify_text = _format_record_line("최신 verify", verify_name, verify_mtime)

    if state_value == "IMPLEMENT_ACTIVE":
        if work_is_current:
            work_text = _format_record_line("현재 라운드 work", work_name, work_mtime)
        elif work_name == "—":
            work_text = "현재 라운드 work: 아직 기록되지 않음"
        else:
            work_text = f"현재 라운드 work: 아직 기록되지 않음 · {latest_work_text}"
        return work_text, latest_verify_text

    if state_value in {"VERIFY_ACTIVE", "VERIFY_FOLLOWUP"}:
        if work_name == "—":
            work_text = "검증 기준 work: 아직 확인되지 않음"
        else:
            work_text = _format_record_line("검증 기준 work", work_name, work_mtime)
        if verify_is_current:
            verify_text = _format_record_line("현재 라운드 verify", verify_name, verify_mtime)
        elif verify_name == "—":
            verify_text = "현재 라운드 verify: 아직 미기록"
        else:
            verify_text = f"현재 라운드 verify: 아직 미기록 · {latest_verify_text}"
        return work_text, verify_text

    return latest_work_text, latest_verify_text


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
                note_text = _format_agent_card_note(note) or format_elapsed(0)
            else:
                elapsed = _parse_elapsed(note)
                if elapsed > 0:
                    computed = now - updated_working_since[label]
                    if abs(computed - elapsed) > 5:
                        updated_working_since[label] = now - elapsed
                note_text = None
        else:
            updated_working_since.pop(label, None)
            note_text = _format_agent_card_note(note) or "대기 중"

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


def _format_agent_card_note(note: str) -> str:
    text = str(note or "").strip()
    if not text:
        return ""
    if _parse_elapsed(text) > 0:
        return text
    return _AGENT_NOTE_LABELS.get(text, text)


def _format_progress_phase(phase: str) -> str:
    text = str(phase or "").strip()
    if not text:
        return ""
    return _AGENT_NOTE_LABELS.get(f"progress:{text}", text)


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
