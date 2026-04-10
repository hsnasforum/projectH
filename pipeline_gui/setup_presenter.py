from __future__ import annotations

from dataclasses import dataclass

from .setup_models import SetupActionState

SETUP_STATE_LABELS = {
    "DraftOnly": "초안 상태",
    "PreviewWaiting": "미리보기 대기 중",
    "PreviewReady": "미리보기 준비됨",
    "ApplyPending": "적용 진행 중",
    "RecoveryNeeded": "복구 필요",
    "ApplyFailed": "적용 실패",
    "Applied": "적용 완료",
    "InvalidConfig": "잘못된 설정",
}

SETUP_SUPPORT_LABELS = {
    "supported": "지원",
    "experimental": "실험적",
    "blocked": "차단",
}

SETUP_SUPPORT_STYLES = {
    "supported": {"fg": "#4ade80", "bg": "#1a1f2b"},
    "experimental": {"fg": "#fbbf24", "bg": "#2a2112"},
    "blocked": {"fg": "#f87171", "bg": "#2a1418"},
}


@dataclass(frozen=True)
class SetupInlineErrors:
    agent_error: str = ""
    implement_error: str = ""
    verify_error: str = ""
    advisory_error: str = ""


@dataclass(frozen=True)
class SetupActionButtonsPresentation:
    save_enabled: bool
    generate_enabled: bool
    apply_enabled: bool
    clean_enabled: bool
    restart_enabled: bool


@dataclass(frozen=True)
class SetupFastPresentation:
    mode_state_text: str
    support_level_text: str
    support_fg: str
    support_bg: str
    validation_text: str
    preview_summary_text: str
    apply_readiness_text: str
    restart_notice_text: str
    current_setup_id_text: str
    current_preview_fingerprint_text: str
    inline_errors: SetupInlineErrors
    buttons: SetupActionButtonsPresentation


@dataclass(frozen=True)
class SetupDetailPresentation:
    mode_state_text: str
    support_level_text: str
    support_fg: str
    support_bg: str
    validation_text: str
    preview_summary_text: str
    apply_readiness_text: str
    restart_notice_text: str
    current_setup_id_text: str
    current_preview_fingerprint_text: str
    inline_errors: SetupInlineErrors
    buttons: SetupActionButtonsPresentation


def format_setup_state_label(state: str) -> str:
    return SETUP_STATE_LABELS.get(state, state)


def format_setup_support_label(level: str) -> str:
    return SETUP_SUPPORT_LABELS.get(level, level)


def support_style_for_level(level: str) -> dict[str, str]:
    return dict(SETUP_SUPPORT_STYLES.get(level, SETUP_SUPPORT_STYLES["blocked"]))


def build_setup_inline_errors(errors: list[str]) -> SetupInlineErrors:
    agent_error = ""
    implement_error = ""
    verify_error = ""
    advisory_error = ""
    for msg in errors:
        if "최소 1개의 agent" in msg:
            agent_error = msg
        elif "검증 역할" in msg or "구현 역할과 검증 역할" in msg:
            verify_error = msg
        elif "자문 역할" in msg or "자문 역할을 구현/검증" in msg:
            advisory_error = msg
        elif "구현 역할" in msg:
            implement_error = msg
    return SetupInlineErrors(
        agent_error=agent_error,
        implement_error=implement_error,
        verify_error=verify_error,
        advisory_error=advisory_error,
    )


def build_setup_action_buttons(
    *,
    project_valid: bool,
    action_in_progress: bool,
    state: SetupActionState,
    preview_allowed: bool,
    apply_allowed: bool,
    active_matches_current: bool,
) -> SetupActionButtonsPresentation:
    action_pending = state.mode_state in {"PreviewWaiting", "ApplyPending"}
    applied_current = state.mode_state == "Applied" and not state.dirty
    preview_current = bool(state.current_preview_payload)
    action_blocked = action_in_progress or action_pending

    save_enabled = (
        project_valid
        and not action_blocked
        and ((state.dirty or not state.draft_saved) and not active_matches_current)
    )
    generate_enabled = (
        project_valid
        and not action_blocked
        and not applied_current
        and preview_allowed
    )
    apply_enabled = (
        state.detail_ready
        and preview_current
        and apply_allowed
        and not action_blocked
    )
    clean_enabled = project_valid and not action_in_progress
    restart_enabled = (
        state.detail_ready
        and state.mode_state == "Applied"
        and state.restart_required
        and not action_in_progress
    )

    return SetupActionButtonsPresentation(
        save_enabled=save_enabled,
        generate_enabled=generate_enabled,
        apply_enabled=apply_enabled,
        clean_enabled=clean_enabled,
        restart_enabled=restart_enabled,
    )


def build_setup_fast_presentation(
    snapshot: dict[str, object],
    state: SetupActionState,
    *,
    project_valid: bool,
    action_in_progress: bool,
    detail_pending_text: str,
) -> SetupFastPresentation:
    support_resolution = dict(snapshot.get("support_resolution") or {})
    support_level = str(support_resolution.get("support_level") or "blocked")
    support_controls = dict(support_resolution.get("controls") or {})
    inline_errors = build_setup_inline_errors(list(snapshot.get("errors") or []))
    buttons = build_setup_action_buttons(
        project_valid=project_valid,
        action_in_progress=action_in_progress,
        state=state,
        preview_allowed=bool(support_controls.get("preview_allowed", True)),
        apply_allowed=False,
        active_matches_current=bool(snapshot.get("active_matches_current")),
    )
    style = support_style_for_level(support_level)
    return SetupFastPresentation(
        mode_state_text=str(snapshot.get("state_text") or "상태 확인 중..."),
        support_level_text=format_setup_support_label(support_level),
        support_fg=str(style["fg"]),
        support_bg=str(style["bg"]),
        validation_text=detail_pending_text,
        preview_summary_text=detail_pending_text,
        apply_readiness_text="적용 비활성: 설정 상태를 갱신 중입니다",
        restart_notice_text="",
        current_setup_id_text=str(snapshot.get("current_setup_id_text") or "—"),
        current_preview_fingerprint_text=str(snapshot.get("current_preview_fingerprint_text") or "—"),
        inline_errors=inline_errors,
        buttons=buttons,
    )


def build_setup_detail_presentation(
    snapshot: dict[str, object],
    state: SetupActionState,
    *,
    project_valid: bool,
    action_in_progress: bool,
) -> SetupDetailPresentation:
    support_level = str(snapshot.get("display_support_level") or "blocked")
    support_controls = dict((state.current_support_resolution or {}).get("controls") or {})
    preview_controls = dict((state.current_preview_payload or {}).get("controls") or {})
    inline_errors = build_setup_inline_errors(list(snapshot.get("errors") or []))
    buttons = build_setup_action_buttons(
        project_valid=project_valid,
        action_in_progress=action_in_progress,
        state=state,
        preview_allowed=bool(support_controls.get("preview_allowed", True)),
        apply_allowed=bool(preview_controls.get("apply_allowed")),
        active_matches_current=False,
    )
    style = support_style_for_level(support_level)
    return SetupDetailPresentation(
        mode_state_text=format_setup_state_label(state.mode_state),
        support_level_text=format_setup_support_label(support_level),
        support_fg=str(style["fg"]),
        support_bg=str(style["bg"]),
        validation_text=str(snapshot.get("validation_text") or "유효성 문제 없음."),
        preview_summary_text=str(snapshot.get("preview_summary_text") or "생성된 미리보기가 없습니다."),
        apply_readiness_text=str(snapshot.get("apply_readiness_text") or ""),
        restart_notice_text=str(snapshot.get("restart_notice_text") or ""),
        current_setup_id_text=state.current_setup_id or "—",
        current_preview_fingerprint_text=state.current_preview_fingerprint or "—",
        inline_errors=inline_errors,
        buttons=buttons,
    )
