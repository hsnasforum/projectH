"""PipelineGUI — main application class with polling, control, and UI."""
from __future__ import annotations

import hashlib
import json
import queue
import threading
import time
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Text, Entry,
    StringVar, BooleanVar, LEFT, RIGHT, BOTH, X, Y, END, WORD, DISABLED, NORMAL,
    font as tkfont,
    filedialog, messagebox,
)
from tkinter import PanedWindow, VERTICAL
from tkinter.ttk import Scrollbar as TtkScrollbar
from uuid import uuid4

from .formatting import format_compact_count
from .platform import (
    IS_WINDOWS, APP_ROOT, TMUX_QUERY_TIMEOUT, WSL_DISTRO,
    resolve_project_runtime_file,
    _wsl_path_str, _windows_to_wsl_mount, _normalize_picked_path, _run,
)
from .project import (
    _load_recent_projects, _save_project_path,
    resolve_project_root, validate_project_root, bootstrap_project_root,
    _session_name_for,
)
from .backend import (
    tmux_alive, watcher_alive, latest_md, time_ago,
    watcher_log_tail, pipeline_start, pipeline_stop, tmux_attach, token_collector_alive,
    confirm_pipeline_start,
    backfill_token_history, rebuild_token_db,
    current_verify_activity, parse_control_slots, format_control_summary,
)
from .agents import (
    STATUS_COLORS, ANSI_RE,
    _extract_run_summary, format_elapsed, _parse_elapsed,
    extract_quota_note, detect_agent_status, capture_agent_panes,
    rejoin_wrapped_pane_lines, format_focus_output,
    watcher_runtime_hints, merge_agent_status_hint,
)
from .setup import (
    _HARD_BLOCKERS, _SOFT_WARNINGS,
    _find_cli_bin, _file_exists,
    _check_hard_blockers, _check_soft_warnings,
    _check_missing_guides, _create_guide_file, _GUIDE_TEMPLATES,
)
from .setup_profile import (
    active_profile_fingerprint,
    build_last_applied_record,
    canonical_setup_payload_for_fingerprint,
    cleanup_stale_setup_artifacts,
    display_resolver_messages,
    fingerprint_payload,
    join_display_resolver_messages,
    reconcile_last_applied,
    resolve_active_profile,
    resolve_project_active_profile,
)
from .view import (
    BG, FG, ACCENT, SUB_FG, BTN_BG, BTN_FG,
    CARD_BG, CARD_BORDER, LOG_BG, HEADER_BG, AGENT_CARD_BG,
    POLL_MS, init_ttk_style, create_fonts, make_card, lighten,
    build_header, build_project_bar, build_control_bar,
    build_status_panels, build_agent_cards, build_token_panel, build_console_panels, build_setup_panels,
)
from .guide import DEFAULT_GUIDE
from .token_queries import load_token_dashboard
from .tokens import collect_token_usage, format_token_usage_note
from .setup_executor import LocalSetupExecutorAdapter
from storage.json_store_base import atomic_write, read_json, utc_now_iso

_SETUP_AGENT_ORDER = ("Claude", "Codex", "Gemini")
_SETUP_STATE_ORDER = (
    "InvalidConfig",
    "ApplyPending",
    "RecoveryNeeded",
    "ApplyFailed",
    "Applied",
    "PreviewReady",
    "PreviewWaiting",
    "DraftOnly",
)
_SETUP_AGENT_SUPPORT_RANK = {
    "Codex": 3,
    "Claude": 2,
    "Gemini": 1,
}
_AGENT_STATUS_LABELS = {
    "READY": "대기",
    "WORKING": "작업 중",
    "OFF": "꺼짐",
    "DEAD": "종료됨",
    "BOOTING": "기동 중",
}
_SETUP_STATE_LABELS = {
    "DraftOnly": "초안 상태",
    "PreviewWaiting": "미리보기 대기 중",
    "PreviewReady": "미리보기 준비됨",
    "ApplyPending": "적용 진행 중",
    "RecoveryNeeded": "복구 필요",
    "ApplyFailed": "적용 실패",
    "Applied": "적용 완료",
    "InvalidConfig": "잘못된 설정",
}
_SETUP_SUPPORT_LABELS = {
    "supported": "지원",
    "experimental": "실험적",
    "blocked": "차단",
}
_SETUP_SUPPORT_STYLES = {
    "supported": {"fg": "#4ade80", "bg": CARD_BG},
    "experimental": {"fg": "#fbbf24", "bg": "#2a2112"},
    "blocked": {"fg": "#f87171", "bg": "#2a1418"},
}
_SETUP_DEFAULT_APPLY_RESULT_MESSAGE = "설정 적용 결과가 도착했습니다."


def _setup_state_label(state: str) -> str:
    return _SETUP_STATE_LABELS.get(state, state)


def _setup_support_label(level: str) -> str:
    return _SETUP_SUPPORT_LABELS.get(level, level)


class PipelineGUI:
    def __init__(self, project: Path) -> None:
        self.project = project
        self._session_name = _session_name_for(project)
        self.selected_agent = "Claude"
        self._auto_focus_agent = True
        self._poll_in_flight = False
        self._last_snapshot: dict[str, object] | None = None
        self._last_poll_at: float | None = None
        self._working_since: dict[str, float] = {}  # agent label → epoch when WORKING started
        self._poll_after_id: str | None = None
        self._tick_after_id: str | None = None
        self._validate_after_id: str | None = None
        self._token_ui_after_id: str | None = None
        self._token_ui_queue: queue.Queue[callable] = queue.Queue()
        self._token_usage_cache: dict[str, dict[str, object]] = {}
        self._token_usage_project_key: str = str(project)
        self._token_usage_last_refresh: float = 0.0
        self._token_usage_refresh_in_flight = False
        self._token_usage_lock = threading.Lock()
        self._setup_state: str = "unknown"  # unknown / checking / ready / missing / failed
        self._setup_state_detail: str = ""
        self._project_valid, self._project_error = validate_project_root(project)
        if self._project_valid:
            boot_ok, boot_error = bootstrap_project_root(project)
            if not boot_ok:
                self._project_valid = False
                self._project_error = boot_error
        self.root = Tk()
        self.root.title("파이프라인 런처")
        self.root.configure(bg="#0f0f0f")
        self.root.resizable(True, True)
        self._init_setup_mode_state()
        self._set_initial_window_geometry()
        self.root.minsize(900, 600)

        self._build_ui()
        self._load_setup_form_from_disk()
        self._setup_cleanup_staged_files_once_on_startup()
        self._refresh_setup_mode_state()

        if not self._project_valid:
            self._show_project_error()
        else:
            _save_project_path(_wsl_path_str(self.project) if IS_WINDOWS else str(self.project))
            self._schedule_poll()
            self._tick_after_id = self.root.after(1000, self._tick_elapsed)
            # 초기 setup 자동 점검 (bg thread)
            self.root.after(500, lambda: threading.Thread(
                target=self._run_setup_check_silent, daemon=True).start())

    def _init_setup_mode_state(self) -> None:
        self._setup_form_updating = False
        self._setup_mode_state = "DraftOnly"
        self._setup_executor_adapter = LocalSetupExecutorAdapter()
        self._setup_current_setup_id = ""
        self._setup_current_draft_fingerprint = ""
        self._setup_current_preview_fingerprint = ""
        self._setup_current_request_payload: dict[str, object] | None = None
        self._setup_current_preview_payload: dict[str, object] | None = None
        self._setup_current_apply_payload: dict[str, object] | None = None
        self._setup_current_result_payload: dict[str, object] | None = None
        self._setup_current_support_resolution: dict[str, object] | None = None
        self._setup_draft_saved = False
        self._setup_dirty = False
        self._setup_has_error = False
        self._setup_has_warning = False
        self._setup_errors: list[str] = []
        self._setup_warnings: list[str] = []
        self._setup_infos: list[str] = []
        self._setup_restart_required = False
        self._setup_cleanup_history: list[str] = []
        self._runtime_launch_resolution: dict[str, object] | None = None

        self._setup_agent_vars = {
            name: BooleanVar(value=True) for name in _SETUP_AGENT_ORDER
        }
        self._setup_implement_var = StringVar(value="Claude")
        self._setup_verify_var = StringVar(value="Codex")
        self._setup_advisory_var = StringVar(value="Gemini")
        self._setup_advisory_enabled_var = BooleanVar(value=True)
        self._setup_operator_stop_enabled_var = BooleanVar(value=True)
        self._setup_session_arbitration_var = BooleanVar(value=True)
        self._setup_self_verify_var = BooleanVar(value=False)
        self._setup_self_advisory_var = BooleanVar(value=False)
        self._setup_executor_var = StringVar(value="auto")

        self._setup_agent_error_var = StringVar(value="")
        self._setup_implement_error_var = StringVar(value="")
        self._setup_verify_error_var = StringVar(value="")
        self._setup_advisory_error_var = StringVar(value="")
        self._setup_mode_state_var = StringVar(value=_SETUP_STATE_LABELS["DraftOnly"])
        self._setup_support_level_var = StringVar(value=_SETUP_SUPPORT_LABELS["supported"])
        self._setup_runtime_profile_var = StringVar(value="실행 프로필: 확인 중")
        self._setup_validation_var = StringVar(value="유효성 문제 없음.")
        self._setup_preview_summary_var = StringVar(value="생성된 미리보기 없음.")
        self._setup_current_setup_id_var = StringVar(value="—")
        self._setup_current_preview_fingerprint_var = StringVar(value="—")
        self._setup_apply_readiness_var = StringVar(value="적용 비활성: 먼저 미리보기를 생성하세요")
        self._setup_restart_notice_var = StringVar(value="")
        self._setup_cleanup_summary_var = StringVar(value="아직 정리 기록이 없습니다.")
        self._runtime_launch_var = StringVar(value="실행 프로필: 확인 중")

    def _set_initial_window_geometry(self) -> None:
        screen_w = max(1280, self.root.winfo_screenwidth())
        screen_h = max(900, self.root.winfo_screenheight())

        width = min(900, screen_w - 40)
        height = min(900, screen_h - 60)

        x = max(20, (screen_w - width) // 2)
        y = max(20, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        init_ttk_style()
        self._fonts = create_fonts()

        # Header must be packed before the expanding content container,
        # otherwise Tk packs it after the main body and it appears at the bottom.
        build_header(self)

        # Container frames
        self._content_container = Frame(self.root, bg=BG)
        self._content_container.pack(fill=BOTH, expand=True)
        content = Frame(self._content_container, bg=BG, padx=14, pady=12)
        self._home_frame = content
        content.pack(fill=BOTH, expand=True)
        self._guide_frame = Frame(self._content_container, bg=BG, padx=14, pady=12)
        self._setup_frame = Frame(self._content_container, bg=BG, padx=14, pady=12)

        # Build sections
        build_project_bar(self, content)
        build_control_bar(self, content)
        build_status_panels(self, content)
        build_agent_cards(self, content)
        build_token_panel(self, content)
        build_console_panels(self, content)
        build_setup_panels(self)

    def _set_initial_pane_split(self) -> None:
        try:
            total_h = self.paned.winfo_height()
            if total_h > 240:
                self.paned.sash_place(0, 0, int(total_h * 0.62))
        except Exception:
            pass

    def _ensure_log_pane_visible(self) -> None:
        try:
            total_h = self.paned.winfo_height()
            if total_h <= 240:
                return
            _x, sash_y = self.paned.sash_coord(0)
            lower_h = total_h - sash_y
            if lower_h < 150:
                self.paned.sash_place(0, 0, int(total_h * 0.62))
        except Exception:
            pass

    # ── 데이터 수집 (tmux 호출 통합) ──

    _prev_focus_text: str = ""
    _prev_log_text: str = ""

    def _collect_all_agent_data(self) -> tuple[list[tuple[str, str, str, str]], dict[str, str]]:
        """list-panes 1회 + capture-pane x3 = 4회 subprocess로 status + output 둘 다 반환."""
        code, output = _run(
            ["tmux", "list-panes", "-t", f"{self._session_name}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
            timeout=TMUX_QUERY_TIMEOUT,
        )
        if code != 0 or not output:
            return (
                [("Claude", "OFF", "", ""), ("Codex", "OFF", "", ""), ("Gemini", "OFF", "", "")],
                {},
            )

        names = {0: "Claude", 1: "Codex", 2: "Gemini"}
        hints = watcher_runtime_hints(self.project)
        agents: list[tuple[str, str, str, str]] = []
        pane_map: dict[str, str] = {}

        for raw in output.splitlines():
            try:
                idx_s, pane_id, dead = raw.split("|", 2)
                idx = int(idx_s)
            except ValueError:
                continue
            label = names.get(idx, f"Pane {idx}")
            if dead == "1":
                agents.append((label, "DEAD", "", ""))
                pane_map[label] = ""
                continue

            # 한 번만 capture — 긴 history로 가져와서 status와 output 양쪽에 사용
            cap_code, captured = _run(
                ["tmux", "capture-pane", "-J", "-p", "-t", pane_id, "-S", "-180"],
                timeout=TMUX_QUERY_TIMEOUT,
            )
            if cap_code != 0 or not captured:
                agents.append((label, "BOOTING", "", ""))
                pane_map[label] = ""
                continue

            cleaned = ANSI_RE.sub("", captured)

            # status 판정 (agent_snapshots 로직)
            status, note = detect_agent_status(label, cleaned)
            quota = extract_quota_note(cleaned)
            status, note = merge_agent_status_hint(label, status, note, hints.get(label))
            agents.append((label, status, note, quota))

            # output (capture_agent_panes 로직)
            pane_map[label] = rejoin_wrapped_pane_lines(cleaned)

        return agents, pane_map

    def _update_text_if_changed(self, widget: Text, new_text: str) -> None:
        """Text 위젯의 내용이 바뀌었을 때만 갱신합니다."""
        widget.configure(state=NORMAL)
        current = widget.get("1.0", f"{END}-1c")
        if current == new_text:
            widget.configure(state=DISABLED)
            return
        at_bottom = widget.yview()[1] >= 0.95
        widget.delete("1.0", END)
        widget.insert(END, new_text)
        # Windows Tk에서 disabled Text의 fg가 무시되는 문제 우회:
        # tag로 전체 텍스트에 fg 색상을 강제 적용
        fg_color = widget.cget("fg") or widget.cget("foreground")
        if fg_color:
            widget.tag_configure("visible", foreground=fg_color)
            widget.tag_add("visible", "1.0", END)
        widget.configure(state=DISABLED)
        if at_bottom:
            widget.see(END)

    def _get_cached_token_usage(self) -> dict[str, dict[str, object]]:
        project_key = str(self.project)
        now = time.time()
        with self._token_usage_lock:
            if self._token_usage_project_key != project_key:
                self._token_usage_project_key = project_key
                self._token_usage_cache = {}
                self._token_usage_last_refresh = 0.0
                self._token_usage_refresh_in_flight = False
            cached = dict(self._token_usage_cache)
            last_refresh = self._token_usage_last_refresh
            in_flight = self._token_usage_refresh_in_flight
        if (not cached or (now - last_refresh) >= 30.0) and not in_flight:
            self._start_token_usage_refresh()
        return cached

    def _start_token_usage_refresh(self, *, force: bool = False) -> None:
        project = Path(self.project)
        project_key = str(project)
        with self._token_usage_lock:
            if self._token_usage_project_key != project_key:
                self._token_usage_project_key = project_key
                self._token_usage_cache = {}
                self._token_usage_last_refresh = 0.0
                self._token_usage_refresh_in_flight = False
            if self._token_usage_refresh_in_flight:
                return
            if (
                not force
                and self._token_usage_cache
                and (time.time() - self._token_usage_last_refresh) < 30.0
            ):
                return
            self._token_usage_refresh_in_flight = True
        threading.Thread(
            target=self._token_usage_refresh_worker,
            args=(project, project_key),
            daemon=True,
        ).start()

    def _token_usage_refresh_worker(self, project: Path, project_key: str) -> None:
        result: dict[str, dict[str, object]]
        try:
            result = collect_token_usage(project)
        except Exception:
            result = {}
        with self._token_usage_lock:
            if self._token_usage_project_key == project_key:
                self._token_usage_cache = dict(result)
                self._token_usage_last_refresh = time.time()
            self._token_usage_refresh_in_flight = False
        try:
            self.root.after(0, lambda: self._apply_token_usage_cache(project_key, result))
        except Exception:
            pass

    def _apply_token_usage_cache(self, project_key: str, result: dict[str, dict[str, object]]) -> None:
        if str(self.project) != project_key:
            return
        if self._last_snapshot is None:
            return
        snapshot = dict(self._last_snapshot)
        snapshot["token_usage"] = result
        self._apply_snapshot(snapshot)

    def _refresh_token_dashboard_async(self) -> None:
        project = Path(self.project)
        project_key = str(project)

        def _worker() -> None:
            try:
                dashboard = load_token_dashboard(project)
            except Exception:
                return
            try:
                self.root.after(0, lambda: self._apply_token_dashboard_refresh(project_key, dashboard))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_token_dashboard_refresh(self, project_key: str, dashboard: object) -> None:
        if str(self.project) != project_key:
            return
        if self._last_snapshot is None:
            self._apply_token_dashboard(dashboard)
            return
        snapshot = dict(self._last_snapshot)
        snapshot["token_dashboard"] = dashboard
        self._apply_snapshot(snapshot)

    def _select_agent(self, agent: str) -> None:
        self.selected_agent = agent
        self._auto_focus_agent = False
        if self._last_snapshot is not None:
            self._apply_snapshot(self._last_snapshot)
        else:
            self._start_poll_worker()

    # ── 폴링 ──

    def _show_project_error(self) -> None:
        """invalid project root일 때 GUI를 에러 상태로 표시합니다."""
        self.status_var.set("잘못된 프로젝트")
        self.status_label.configure(fg="#ef4444", bg="#351717")
        self.pipeline_var.set("파이프라인: — (잘못된 프로젝트 루트)")
        self.pipeline_state_label.configure(fg="#ef4444")
        self.watcher_var.set("워처: —")
        self.watcher_state_label.configure(fg="#888888")
        self.poll_var.set("폴링: —")
        self.poll_state_label.configure(fg="#666666")
        self.work_var.set("최신 work: —")
        self.verify_var.set("최신 verify: —")
        self._set_toast_style("error")
        self.msg_var.set(self._project_error)
        self.setup_var.set("설정: —")
        self.setup_state_label.configure(fg="#888888")
        if hasattr(self, "_runtime_launch_var"):
            self._runtime_launch_var.set("실행 프로필: —")
        if hasattr(self, "_runtime_launch_label"):
            self._runtime_launch_label.configure(fg="#888888")
        self._set_main_button_states(all_disabled=True)

    def _tick_elapsed(self) -> None:
        """Lightweight tick — updates WORKING elapsed note aligned to second boundaries."""
        now = time.time()
        for i, name in enumerate(("Claude", "Codex", "Gemini")):
            since = self._working_since.get(name)
            if since is not None and i < len(self.agent_labels):
                new_text = format_elapsed(now - since)
                _, _, _, note_lbl, _ = self.agent_labels[i]
                if note_lbl.cget("text") != new_text:
                    note_lbl.configure(text=new_text)
        self._update_poll_freshness()
        # Align to next whole-second boundary for metronomic rhythm
        frac_ms = int((now % 1.0) * 1000)
        self._tick_after_id = self.root.after(max(50, 1000 - frac_ms), self._tick_elapsed)

    def _schedule_poll(self) -> None:
        self._start_poll_worker()
        self._poll_after_id = self.root.after(POLL_MS, self._schedule_poll)

    def _stop_all_timers(self) -> None:
        """Cancel active poll and tick chains."""
        if self._poll_after_id is not None:
            self.root.after_cancel(self._poll_after_id)
            self._poll_after_id = None
        if self._tick_after_id is not None:
            self.root.after_cancel(self._tick_after_id)
            self._tick_after_id = None
        if self._token_ui_after_id is not None:
            self.root.after_cancel(self._token_ui_after_id)
            self._token_ui_after_id = None

    _VALIDATE_DEBOUNCE_MS = 600

    def _refresh_recent_buttons(self) -> None:
        """최근 프로젝트 목록에서 quick-select 버튼을 재생성합니다."""
        if not hasattr(self, "_recent_row"):
            return  # _build_ui에서 아직 생성 전 (trace_add 조기 발화 방어)
        for child in self._recent_row.winfo_children():
            child.destroy()

        recent = _load_recent_projects()
        current = self._path_var.get().strip()

        if current:
            current_short = Path(current).name or current
            current_lbl = Label(
                self._recent_row,
                text=f"현재: {current_short}",
                font=tkfont.Font(family="Consolas", size=8),
                bg="#141414",
                fg="#f59e0b",
                padx=6,
                pady=2,
                highlightthickness=1,
                highlightbackground="#444444",
            )
            current_lbl.pack(side=LEFT, padx=(0, 6))

        other_recent = [path_str for path_str in recent if path_str != current]
        if not other_recent:
            empty_lbl = Label(
                self._recent_row,
                text="최근 경로 없음",
                font=tkfont.Font(family="Consolas", size=8),
                bg="#171717",
                fg="#6b7280",
                padx=2,
                pady=2,
            )
            empty_lbl.pack(side=LEFT)
            return

        recent_lbl = Label(
            self._recent_row,
            text="최근:",
            font=tkfont.Font(family="Consolas", size=8),
            bg="#171717",
            fg="#9ca3af",
            padx=2,
            pady=2,
        )
        recent_lbl.pack(side=LEFT, padx=(0, 4))

        for path_str in other_recent:
            short = Path(path_str).name or path_str
            btn = Button(
                self._recent_row,
                text=short,
                command=lambda p=path_str: self._on_recent_select(p),
                font=tkfont.Font(family="Consolas", size=8),
                bg="#1a1a1a",
                fg="#9ca3af",
                activebackground="#333333",
                activeforeground="#f59e0b",
                bd=0,
                padx=6,
                pady=2,
                highlightthickness=1,
                highlightbackground="#333333",
            )
            btn.pack(side=LEFT, padx=(0, 4))

    def _on_recent_select(self, path_str: str) -> None:
        """Quick-select 클릭 시 Entry에 경로를 채웁니다."""
        self._path_var.set(path_str)
        self._refresh_recent_buttons()

    def _switch_mode(self, mode: str) -> None:
        """Home/Guide/Setup 모드 전환."""
        if mode == self._mode:
            return
        self._mode = mode
        self._home_frame.pack_forget()
        self._guide_frame.pack_forget()
        self._setup_frame.pack_forget()
        self._mode_btn_home.configure(bg="#18182a", fg="#6b7280")
        self._mode_btn_guide.configure(bg="#18182a", fg="#6b7280")
        self._mode_btn_setup.configure(bg="#18182a", fg="#6b7280")

        if mode == "home":
            self._home_frame.pack(fill=BOTH, expand=True)
            self._mode_btn_home.configure(bg="#2a2a3a", fg="#d8dae0")
        elif mode == "guide":
            self._guide_frame.pack(fill=BOTH, expand=True)
            self._mode_btn_guide.configure(bg="#2a2a3a", fg="#d8dae0")
        else:
            self._setup_frame.pack(fill=BOTH, expand=True)
            self._mode_btn_setup.configure(bg="#2a2a3a", fg="#d8dae0")
            self._refresh_setup_mode_state()

    def _load_project_guide(self) -> None:
        """canonical guide를 read-only 텍스트 위젯에 로드합니다."""
        if not hasattr(self, "_guide_text"):
            return
        self._guide_text.configure(state=NORMAL)
        self._guide_text.delete("1.0", END)
        self._guide_text.insert("1.0", DEFAULT_GUIDE)
        fg_color = self._guide_text.cget("fg") or self._guide_text.cget("foreground")
        if fg_color:
            self._guide_text.tag_configure("visible", foreground=fg_color)
            self._guide_text.tag_add("visible", "1.0", END)
        self._guide_text.configure(state=DISABLED)
        self._guide_status_var.set("")

    def _export_guide_md(self) -> None:
        """현재 guide 내용을 .md 파일로 내보냅니다."""
        project_name = Path(_wsl_path_str(self.project) if IS_WINDOWS else str(self.project)).name or "project"
        default_name = f"{project_name}-pipeline-guide.md"
        path = filedialog.asksaveasfilename(
            title="Export Pipeline Guide",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not path:
            return
        text = self._guide_text.get("1.0", f"{END}-1c")
        try:
            Path(path).write_text(text, encoding="utf-8")
            self._guide_status_var.set(f"Exported: {Path(path).name}")
            self.root.after(3000, lambda: self._guide_status_var.set(""))
        except OSError as e:
            self._guide_status_var.set(f"Export failed: {e}")
            self.root.after(5000, lambda: self._guide_status_var.set(""))

    def _on_path_var_change(self, *_args: object) -> None:
        """Entry 변경 시 cheap precheck + debounced marker 검증으로 Apply 활성/비활성."""
        # Cancel pending debounced check
        if self._validate_after_id is not None:
            self.root.after_cancel(self._validate_after_id)
            self._validate_after_id = None

        raw = self._path_var.get().strip()

        # Tier 1: instant cheap precheck
        if not raw:
            self._path_apply_btn.configure(state=DISABLED)
            return
        normalized = _normalize_picked_path(raw)
        if not normalized.startswith("/"):
            self._path_apply_btn.configure(state=DISABLED)
            self._refresh_recent_buttons()
            return

        # Format OK — disable while waiting for debounced marker check
        self._path_apply_btn.configure(state=DISABLED)
        self._refresh_recent_buttons()
        self._validate_after_id = self.root.after(
            self._VALIDATE_DEBOUNCE_MS,
            lambda: self._check_path_markers(normalized),
        )

    def _check_path_markers(self, path_str: str) -> None:
        """Debounced marker validation — lightweight check for repo markers."""
        self._validate_after_id = None

        def _apply(valid: bool) -> None:
            # Only apply if entry still matches this check
            current = _normalize_picked_path(self._path_var.get().strip())
            if current == path_str:
                self._path_apply_btn.configure(state=NORMAL if valid else DISABLED)

        if IS_WINDOWS:
            # Run wsl test in background thread to avoid blocking GUI
            def _worker() -> None:
                code, _ = _run(["test", "-f", f"{path_str}/AGENTS.md"], timeout=3.0)
                valid = code == 0
                try:
                    self.root.after(0, lambda: _apply(valid))
                except Exception:
                    pass
            threading.Thread(target=_worker, daemon=True).start()
        else:
            # Linux: instant filesystem check
            p = Path(path_str)
            _apply((p / "AGENTS.md").exists())

    def _on_browse(self) -> None:
        """폴더 선택기를 열어 project root를 선택합니다."""
        if IS_WINDOWS:
            initial = f"\\\\wsl.localhost\\{WSL_DISTRO}"
        else:
            initial = str(Path.home())
        picked = filedialog.askdirectory(
            title="Select project root",
            initialdir=initial,
        )
        if not picked:
            return  # 취소됨
        normalized = _normalize_picked_path(picked)
        self._path_var.set(normalized)
        # Browse gave us a real directory — skip debounce, validate immediately
        if self._validate_after_id is not None:
            self.root.after_cancel(self._validate_after_id)
            self._validate_after_id = None
        self._check_path_markers(normalized)

    def _apply_project_path(self) -> None:
        """Entry에서 입력한 경로를 검증하고 적용합니다."""
        new_path_str = self._path_var.get().strip()
        if not new_path_str:
            return
        # Normalize in case user pasted a UNC path directly
        new_path_str = _normalize_picked_path(new_path_str)
        self._path_var.set(new_path_str)
        new_path = Path(new_path_str)
        valid, error = validate_project_root(new_path)
        if valid:
            boot_ok, boot_error = bootstrap_project_root(new_path)
            if not boot_ok:
                self._stop_all_timers()
                self._project_valid = False
                self._project_error = boot_error
                self._show_project_error()
                return
            self._stop_all_timers()
            self.project = new_path
            self._session_name = _session_name_for(new_path)
            self._project_valid = True
            self._project_error = ""
            self._working_since.clear()
            self._last_snapshot = None
            self._last_poll_at = None
            with self._token_usage_lock:
                self._token_usage_project_key = str(new_path)
                self._token_usage_cache = {}
                self._token_usage_last_refresh = 0.0
                self._token_usage_refresh_in_flight = False
            _save_project_path(new_path_str)
            self._refresh_recent_buttons()
            self._load_project_guide()
            self._setup_reset_cleanup_history()
            self._load_setup_form_from_disk()
            self._setup_cleanup_staged_files_once_on_startup()
            self._refresh_setup_mode_state()
            self._set_toast_style("success")
            self.msg_var.set(f"프로젝트 경로 적용 완료: {new_path_str}")
            self._clear_msg_later()
            self._schedule_poll()
            self._tick_after_id = self.root.after(1000, self._tick_elapsed)
        else:
            self._stop_all_timers()
            self._project_valid = False
            self._project_error = error
            self._show_project_error()

    def _start_poll_worker(self) -> None:
        if self._poll_in_flight:
            return
        self._poll_in_flight = True
        threading.Thread(target=self._poll_worker, daemon=True).start()

    def _poll_worker(self) -> None:
        snapshot: dict[str, object] | None = None
        try:
            snapshot = self._build_snapshot()
        except Exception:
            snapshot = None

        def _finish() -> None:
            self._poll_in_flight = False
            if snapshot is not None:
                self._apply_snapshot(snapshot)

        try:
            self.root.after(0, _finish)
        except Exception:
            self._poll_in_flight = False

    def _build_snapshot(self) -> dict[str, object]:
        polled_at = time.time()
        session_ok = tmux_alive(self._session_name)
        w_alive, w_pid = watcher_alive(self.project)
        agents, pane_map = self._collect_all_agent_data()
        token_usage = self._get_cached_token_usage()
        token_dashboard = load_token_dashboard(self.project)
        work_name, work_mtime = latest_md(self.project / "work")
        verify_name, verify_mtime = latest_md(self.project / "verify")
        log_lines = watcher_log_tail(self.project, lines=14)
        # run summary는 더 넓은 범위에서 추출 (최근 50줄)
        summary_lines = watcher_log_tail(self.project, lines=50)
        run_summary = _extract_run_summary(summary_lines)
        control_slots = parse_control_slots(self.project)
        verify_activity = current_verify_activity(self.project)

        return {
            "session_ok": session_ok,
            "watcher_alive": w_alive,
            "watcher_pid": w_pid,
            "agents": agents,
            "pane_map": pane_map,
            "token_usage": token_usage,
            "token_dashboard": token_dashboard,
            "work_name": work_name,
            "work_mtime": work_mtime,
            "verify_name": verify_name,
            "verify_mtime": verify_mtime,
            "log_lines": log_lines,
            "run_summary": run_summary,
            "control_slots": control_slots,
            "verify_activity": verify_activity,
            "polled_at": polled_at,
        }

    def _apply_snapshot(self, snapshot: dict[str, object]) -> None:
        self._last_snapshot = snapshot
        self._last_poll_at = float(snapshot.get("polled_at") or time.time())
        session_ok = bool(snapshot["session_ok"])
        w_alive = bool(snapshot["watcher_alive"])
        w_pid = snapshot["watcher_pid"]
        agents = snapshot["agents"]
        pane_map = snapshot["pane_map"]
        token_usage = snapshot.get("token_usage", {})
        token_dashboard = snapshot.get("token_dashboard")
        work_name = snapshot["work_name"]
        work_mtime = float(snapshot["work_mtime"])
        verify_name = snapshot["verify_name"]
        verify_mtime = float(snapshot["verify_mtime"])
        log_lines = snapshot["log_lines"]
        run = snapshot.get("run_summary", {})

        # Pipeline status
        if session_ok:
            self.pipeline_var.set("파이프라인: ● 실행 중")
            self.status_var.set("실행 중")
            self.status_label.configure(fg="#4ade80", bg="#0a2a18")
            self.pipeline_state_label.configure(fg="#4ade80")
        else:
            self.pipeline_var.set("파이프라인: ■ 중지됨")
            self.status_var.set("중지됨")
            self.status_label.configure(fg="#f87171", bg="#2a1015")
            self.pipeline_state_label.configure(fg="#f87171")

        # Watcher
        if w_alive:
            self.watcher_var.set(f"워처: ● 활성 (PID:{w_pid})")
            self.watcher_state_label.configure(fg="#34d399")
        else:
            self.watcher_var.set("워처: ✗ 비활성")
            self.watcher_state_label.configure(fg="#ef4444")
        self._update_poll_freshness()
        launch_resolution = self._resolve_runtime_active_profile()
        self._apply_runtime_launch_presentation(launch_resolution)

        # Control slot summary
        control_slots = snapshot.get("control_slots", {})
        verify_activity = snapshot.get("verify_activity")
        active_text, stale_text = format_control_summary(control_slots, verify_activity=verify_activity)
        self.active_control_var.set(active_text)
        active = control_slots.get("active")
        if verify_activity is not None and not (
            active is not None and active.get("status") == "needs_operator"  # type: ignore[union-attr]
        ):
            active_fg = "#93c5fd"
            active_box_bg = "#101826"
            active_box_border = "#1d4ed8"
            active_title_fg = "#60a5fa"
        elif active is None:
            active_fg = "#9ca3af"
            active_box_bg = "#141418"
            active_box_border = "#30363d"
            active_title_fg = "#6b7280"
        elif active.get("status") == "needs_operator":  # type: ignore[union-attr]
            active_fg = "#fca5a5"
            active_box_bg = "#2a1015"
            active_box_border = "#7f1d1d"
            active_title_fg = "#f87171"
        else:
            active_fg = "#93c5fd"
            active_box_bg = "#101826"
            active_box_border = "#1d4ed8"
            active_title_fg = "#60a5fa"
        self.active_control_box.configure(bg=active_box_bg, highlightbackground=active_box_border)
        self.active_control_title_label.configure(bg=active_box_bg, fg=active_title_fg)
        self.active_control_label.configure(bg=active_box_bg, fg=active_fg)
        self.stale_control_var.set(stale_text)
        if stale_text:
            self.stale_control_box.configure(bg="#14161d", highlightbackground="#374151")
            self.stale_control_title_label.configure(bg="#14161d", fg="#94a3b8")
            self.stale_control_label.configure(bg="#14161d", fg="#94a3b8")
            if not getattr(self, "_stale_control_box_visible", False):
                self.stale_control_box.pack(fill=X, pady=(6, 0))
                self._stale_control_box_visible = True
        elif getattr(self, "_stale_control_box_visible", False):
            self.stale_control_box.pack_forget()
            self._stale_control_box_visible = False

        working_labels = [label for label, status, _note, _quota in agents if status == "WORKING"]
        if self.selected_agent not in {label for label, _s, _n, _q in agents}:
            self.selected_agent = working_labels[0] if working_labels else "Claude"
        elif self._auto_focus_agent and working_labels:
            self.selected_agent = working_labels[0]

        now = time.time()
        for i, (card, dot_lbl, status_lbl, note_lbl, quota_lbl) in enumerate(self.agent_labels):
            if i < len(agents):
                label, status, note, quota = agents[i]
                color = STATUS_COLORS.get(status, "#666666")
                dot_lbl.configure(fg=color)
                status_lbl.configure(text=_AGENT_STATUS_LABELS.get(status, status), fg=color)
                # Track working_since for smooth 1s elapsed ticks
                if status == "WORKING":
                    if label not in self._working_since:
                        # First detection — anchor and set initial note
                        elapsed = _parse_elapsed(note)
                        self._working_since[label] = now - elapsed if elapsed > 0 else now
                        note_lbl.configure(text=note or format_elapsed(0), fg="#9ca3af")
                    else:
                        # Already ticking — only re-anchor on large drift (>5s),
                        # do NOT touch note_lbl (tick handles it to avoid stutter)
                        elapsed = _parse_elapsed(note)
                        if elapsed > 0:
                            computed = now - self._working_since[label]
                            if abs(computed - elapsed) > 5:
                                self._working_since[label] = now - elapsed
                else:
                    self._working_since.pop(label, None)
                    note_lbl.configure(text=note or "대기 중", fg="#9ca3af")
                usage_quota = ""
                if isinstance(token_usage, dict):
                    usage_quota = format_token_usage_note(token_usage.get(label, {}))
                display_quota = usage_quota or quota
                quota_lbl.configure(
                    text=f"사용량: {display_quota}" if display_quota else "사용량: —",
                    fg="#7c8798",
                )
                if label == self.selected_agent:
                    # Selected: 굵은 밝은 파란 보더 + 밝은 배경
                    sel_bg = "#1a1a30"
                    card.configure(highlightbackground="#6ea8ff", highlightthickness=3, bg=sel_bg)
                    for child in card.winfo_children():
                        try:
                            child.configure(bg=sel_bg)
                        except Exception:
                            pass
                else:
                    if status == "WORKING":
                        # WORKING (not selected): 녹색 보더 + 녹색 tint
                        card.configure(highlightbackground="#4ade80", highlightthickness=2, bg="#0e2a18")
                        for child in card.winfo_children():
                            try:
                                child.configure(bg="#0e2a18")
                            except Exception:
                                pass
                    else:
                        # 기본: 얇은 어두운 보더
                        card.configure(highlightbackground="#1e1e2e", highlightthickness=1, bg="#12121a")
                        for child in card.winfo_children():
                            try:
                                child.configure(bg="#12121a")
                            except Exception:
                                pass
            else:
                dot_lbl.configure(fg="#666666")
                status_lbl.configure(text="—", fg="#666666")
                note_lbl.configure(text="", fg="#666666")
                quota_lbl.configure(text="사용량: —", fg="#666666")
                card.configure(highlightbackground="#2a2a2a")

        self._apply_token_dashboard(token_dashboard)

        # running vs stopped 구분 — 아래 title/color에서 사용
        is_live = session_ok and w_alive

        selected_text = format_focus_output(pane_map.get(self.selected_agent, ""))

        # 빈 출력이면 run context를 fallback으로 표시
        if selected_text in ("(출력 없음)", "(표시할 출력 없음)") and is_live:
            fallback_parts = []
            run_turn = run.get("turn", "")
            run_phase = run.get("phase", "")
            run_job = run.get("job", "")
            if run_turn:
                fallback_parts.append(f"현재 턴: {run_turn}")
            if run_phase:
                fallback_parts.append(f"단계: {run_phase}")
            if run_job:
                fallback_parts.append(f"작업: {run_job}")
            # agent별 watcher 힌트 추가
            for label, status, note, _quota in agents:
                if label == self.selected_agent and status == "WORKING" and note:
                    fallback_parts.append(f"{label}: 작업 중 ({note})")
                elif label == self.selected_agent and status != "OFF":
                    fallback_parts.append(f"{label}: {_AGENT_STATUS_LABELS.get(status, status)}")
            if fallback_parts:
                selected_text = "\n".join(fallback_parts)

        if is_live:
            title_suffix = "최근 pane 출력" if selected_text not in ("(출력 없음)", "(표시할 출력 없음)") else "실행 문맥"
            self.focus_title_var.set(f"{self.selected_agent.upper()} • {title_suffix}")
        else:
            self.focus_title_var.set(f"{self.selected_agent.upper()} • 최근 pane 출력 (마지막 실행)")
        self._update_text_if_changed(self.focus_text, selected_text)

        # Artifacts / log: stale label + dim color
        stale_tag = "" if is_live else " (last run)"
        artifact_color = "#c0a060" if is_live else "#505868"

        self._artifacts_title_var.set("산출물" if is_live else "산출물 (마지막 실행)")
        self._work_label.configure(fg=artifact_color)
        self._verify_label.configure(fg=artifact_color)

        # current run context
        run_job = run.get("job", "")
        run_phase = run.get("phase", "")
        run_turn = run.get("turn", "")
        if is_live and (run_job or run_phase or run_turn):
            parts = []
            if run_turn:
                parts.append(f"턴: {run_turn}")
            if run_phase:
                parts.append(f"단계: {run_phase}")
            if run_job:
                # job ID에서 날짜 이후 의미 부분만 추출
                short_job = run_job.split("-", 1)[1][:50] if "-" in run_job else run_job[:50]
                parts.append(f"작업: {short_job}")
            self._run_context_var.set(" │ ".join(parts))
            self._run_context_label.configure(fg="#5b9cf6")
        elif not is_live and run_job:
            self._run_context_var.set(f"마지막 작업: {run_job.split('-', 1)[1][:50] if '-' in run_job else run_job[:50]}")
            self._run_context_label.configure(fg="#404058")
        else:
            self._run_context_var.set("")

        work_display = f"최신 work:   {work_name}"
        if work_mtime:
            work_display += f" ({time_ago(work_mtime)})"
        verify_display = f"최신 verify: {verify_name}"
        if verify_mtime:
            verify_display += f" ({time_ago(verify_mtime)})"
        self.work_var.set(work_display)
        self.verify_var.set(verify_display)

        # watcher log title에 run summary 반영
        log_hint_parts = []
        if run_turn:
            log_hint_parts.append(run_turn)
        if run_phase:
            log_hint_parts.append(run_phase)
        log_hint = f" • {' → '.join(log_hint_parts)}" if log_hint_parts else ""
        if is_live:
            self._log_title_var.set(f"워처 로그{log_hint}")
        else:
            self._log_title_var.set(f"워처 로그 (마지막 실행){log_hint}")

        log_text = "\n".join(
            (l.strip()[:140] + "…" if len(l.strip()) > 143 else l.strip())
            for l in log_lines
        )
        self._update_text_if_changed(self.log_text, log_text)

        can_launch = self._runtime_launch_allowed(launch_resolution)
        can_start = not session_ok and can_launch
        self._set_main_button_states(
            all_disabled=self._action_in_progress,
            can_start=can_start,
            can_restart=session_ok and can_launch,
            session_ok=session_ok,
        )
        self._refresh_setup_mode_state()

    def _poll_status_text(self, *, is_live: bool, now: float | None = None) -> tuple[str, str]:
        current = time.time() if now is None else now
        if self._last_poll_at is None:
            return "폴링: —", "#666666"
        age = max(0, int(current - self._last_poll_at))
        stale_after_sec = max(3, int(POLL_MS / 1000) * 3)
        if is_live:
            if age <= stale_after_sec:
                return f"폴링: 최신 {age}초", "#34d399"
            return f"폴링: 지연 {age}초", "#e0a040"
        if age == 0:
            return "폴링: 마지막 실행", "#666666"
        return f"폴링: 마지막 실행 {age}초 전", "#666666"

    def _update_poll_freshness(self, now: float | None = None) -> None:
        if not hasattr(self, "poll_var"):
            return
        is_live = False
        if self._last_snapshot is not None:
            is_live = bool(self._last_snapshot.get("session_ok")) and bool(self._last_snapshot.get("watcher_alive"))
        text, color = self._poll_status_text(is_live=is_live, now=now)
        self.poll_var.set(text)
        self.poll_state_label.configure(fg=color)

    def _apply_token_dashboard(self, dashboard: object) -> None:
        if dashboard is None:
            self._token_status_var.set(self._empty_token_label("수집기"))
            self._token_totals_var.set(self._empty_token_label("오늘"))
            self._token_agents_var.set(self._empty_token_label("에이전트"))
            self._token_selected_var.set(self._empty_token_label(f"선택 에이전트 {self.selected_agent.upper()}"))
            self._token_jobs_var.set(self._empty_token_label("주요 작업"))
            return
        collector = getattr(dashboard, "collector_status", None)
        totals = getattr(dashboard, "today_totals", None)
        agents = list(getattr(dashboard, "agent_totals", []) or [])
        jobs = list(getattr(dashboard, "top_jobs", []) or [])
        display_day = str(getattr(dashboard, "display_day", "") or "")
        today_day = time.strftime("%Y-%m-%d")
        totals_label = "오늘" if not display_day or display_day == today_day else f"최근 {display_day}"
        token_loading = self._token_dashboard_loading()
        totals_empty = self._token_totals_empty(totals)

        self._token_status_var.set(self._format_token_status_line(collector, token_loading=token_loading))
        self._token_totals_var.set(
            self._format_token_totals_line(
                totals,
                totals_label=totals_label,
                token_loading=token_loading,
                totals_empty=totals_empty,
                has_agents=bool(agents),
                has_jobs=bool(jobs),
            )
        )
        self._token_agents_var.set(self._format_token_agents_line(agents, token_loading=token_loading))

        token_usage = {}
        if isinstance(self._last_snapshot, dict):
            raw_usage = self._last_snapshot.get("token_usage")
            if isinstance(raw_usage, dict):
                token_usage = raw_usage
        self._apply_selected_token_detail(token_usage, dashboard, token_loading=token_loading, totals_label=totals_label)
        self._token_jobs_var.set(
            self._format_token_jobs_line(
                jobs,
                token_loading=token_loading,
                has_agents=bool(agents),
                totals_empty=totals_empty,
            )
        )

    def _apply_selected_token_detail(
        self,
        token_usage: object,
        dashboard: object,
        *,
        token_loading: bool,
        totals_label: str,
    ) -> None:
        selected = self.selected_agent
        title = f"선택 에이전트 {selected.upper()}: "
        usage_summary: dict[str, object] = {}
        if isinstance(token_usage, dict):
            raw_usage = token_usage.get(selected)
            if isinstance(raw_usage, dict):
                usage_summary = raw_usage
        agent_row = None
        for item in list(getattr(dashboard, "agent_totals", []) or []):
            if str(getattr(item, "source", "") or "").lower() == selected.lower():
                agent_row = item
                break

        if token_loading and not usage_summary.get("available") and agent_row is None:
            self._token_selected_var.set(title + "불러오는 중...")
            return

        parts: list[str] = []
        usage_note = format_token_usage_note(usage_summary) if usage_summary else ""
        if usage_note:
            parts.append(f"usage {usage_note}")

        if agent_row is not None:
            input_tokens = self._fmt_count(int(getattr(agent_row, "input_tokens", 0) or 0))
            output_tokens = self._fmt_count(int(getattr(agent_row, "output_tokens", 0) or 0))
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
        self._token_selected_var.set(title + " · ".join(parts))

    def _empty_token_label(self, label: str) -> str:
        return f"{label}: —"

    def _loading_token_label(self, label: str) -> str:
        return f"{label}: 불러오는 중..."

    def _token_dashboard_loading(self) -> bool:
        token_action_text = ""
        if hasattr(self, "_token_action_var"):
            token_action_text = str(self._token_action_var.get() or "")
        return self._action_in_progress and (
            "전체 히스토리" in token_action_text or "DB 재구성" in token_action_text
        )

    def _token_totals_empty(self, totals: object) -> bool:
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

    def _format_token_status_line(self, collector: object, *, token_loading: bool) -> str:
        if collector is None or not getattr(collector, "available", False):
            return self._loading_token_label("수집기") if token_loading else "수집기: 없음"
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

    def _format_token_totals_line(
        self,
        totals: object,
        *,
        totals_label: str,
        token_loading: bool,
        totals_empty: bool,
        has_agents: bool,
        has_jobs: bool,
    ) -> str:
        if token_loading and totals_empty and not has_agents and not has_jobs:
            return self._loading_token_label(totals_label)
        if totals is None:
            return self._empty_token_label(totals_label)
        total_parts = [
            f"{totals_label} 입력 {self._fmt_count(int(getattr(totals, 'input_tokens', 0) or 0))}",
            f"출력 {self._fmt_count(int(getattr(totals, 'output_tokens', 0) or 0))}",
        ]
        cache_total = int(getattr(totals, "cache_read_tokens", 0) or 0) + int(
            getattr(totals, "cache_write_tokens", 0) or 0
        )
        thinking = int(getattr(totals, "thinking_tokens", 0) or 0)
        if cache_total:
            total_parts.append(f"캐시 {self._fmt_count(cache_total)}")
        if thinking:
            total_parts.append(f"추론 {self._fmt_count(thinking)}")
        actual_cost = float(getattr(totals, "actual_cost_usd_sum", 0.0) or 0.0)
        estimated_cost = float(getattr(totals, "estimated_only_cost_usd_sum", 0.0) or 0.0)
        total_parts.append(f"비용 ${actual_cost + estimated_cost:.2f}")
        if actual_cost:
            total_parts.append(f"실비 ${actual_cost:.2f}")
        if estimated_cost:
            total_parts.append(f"예상 ${estimated_cost:.2f}")
        return " | ".join(total_parts)

    def _format_token_agents_line(self, agents: list[object], *, token_loading: bool) -> str:
        if token_loading and not agents:
            return self._loading_token_label("에이전트")
        if not agents:
            return self._empty_token_label("에이전트")
        return "에이전트: " + " | ".join(self._format_token_agent_segment(item) for item in agents[:3])

    def _format_token_agent_segment(self, item: object) -> str:
        source = str(getattr(item, "source", "") or "").upper()
        inp = self._fmt_count(int(getattr(item, "input_tokens", 0) or 0))
        out = self._fmt_count(int(getattr(item, "output_tokens", 0) or 0))
        events = int(getattr(item, "events", 0) or 0)
        linked_events = int(getattr(item, "linked_events", 0) or 0)
        cost = float(getattr(item, "total_cost_usd", 0.0) or 0.0)
        segment = f"{source} {inp}/{out}"
        if cost:
            segment += f" ${cost:.2f}"
        if events > 0 and linked_events == 0:
            segment += " 미연결"
        return segment

    def _format_token_jobs_line(
        self,
        jobs: list[object],
        *,
        token_loading: bool,
        has_agents: bool,
        totals_empty: bool,
    ) -> str:
        if token_loading and not jobs:
            return self._loading_token_label("주요 작업")
        if not jobs and (has_agents or not totals_empty):
            return "주요 작업: 연결된 작업이 아직 없습니다"
        if not jobs:
            return self._empty_token_label("주요 작업")
        return "주요 작업: " + " | ".join(self._format_token_job_segment(item) for item in jobs[:3])

    def _format_token_job_segment(self, item: object) -> str:
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
            segment += f" {self._short_token_link_method(method)}"
        segment += f" c={confidence:.2f}"
        if total_events:
            segment += f" low={low_confidence_events}/{total_events}"
        return segment

    def _short_token_link_method(self, method: str) -> str:
        return (
            method.replace("dispatch_slot_verify_window", "dispatch")
            .replace("artifact_seen_work_window", "artifact")
            .replace("gemini_notify_recent_job_window", "gemini")
        )

    def _fmt_count(self, value: int) -> str:
        return format_compact_count(value)

    # ── Setup mode ──

    def _setup_paths(self) -> dict[str, Path]:
        pipeline_dir = self.project / ".pipeline"
        config_dir = pipeline_dir / "config"
        setup_dir = pipeline_dir / "setup"
        return {
            "config_dir": config_dir,
            "setup_dir": setup_dir,
            "active": config_dir / "agent_profile.json",
            "draft": config_dir / "agent_profile.draft.json",
            "request": setup_dir / "request.json",
            "preview": setup_dir / "preview.json",
            "apply": setup_dir / "apply.json",
            "result": setup_dir / "result.json",
            "last_applied": setup_dir / "last_applied.json",
        }

    def _setup_default_profile(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "selected_agents": list(_SETUP_AGENT_ORDER),
            "role_bindings": {
                "implement": "Claude",
                "verify": "Codex",
                "advisory": "Gemini",
            },
            "role_options": {
                "advisory_enabled": True,
                "operator_stop_enabled": True,
                "session_arbitration_enabled": True,
            },
            "mode_flags": {
                "single_agent_mode": False,
                "self_verify_allowed": False,
                "self_advisory_allowed": False,
            },
            "executor_override": "auto",
        }

    def _setup_selected_agents(self) -> list[str]:
        return [name for name in _SETUP_AGENT_ORDER if bool(self._setup_agent_vars[name].get())]

    def _setup_recommended_executor(
        self,
        selected_agents: list[str],
        role_bindings: dict[str, str | None],
    ) -> str:
        verify = str(role_bindings.get("verify") or "")
        implement = str(role_bindings.get("implement") or "")
        if verify and verify in selected_agents:
            return verify
        if implement and implement in selected_agents:
            return implement
        if not selected_agents:
            return "auto"
        return max(selected_agents, key=lambda name: _SETUP_AGENT_SUPPORT_RANK.get(name, 0))

    def _setup_collect_form_payload(self) -> dict[str, object]:
        selected_agents = self._setup_selected_agents()
        advisory_enabled = bool(self._setup_advisory_enabled_var.get())
        advisory_value = self._setup_advisory_var.get().strip() or None
        if not advisory_enabled:
            advisory_value = None
        return {
            "schema_version": 1,
            "selected_agents": selected_agents,
            "role_bindings": {
                "implement": self._setup_implement_var.get().strip() or None,
                "verify": self._setup_verify_var.get().strip() or None,
                "advisory": advisory_value,
            },
            "role_options": {
                "advisory_enabled": advisory_enabled,
                "operator_stop_enabled": bool(self._setup_operator_stop_enabled_var.get()),
                "session_arbitration_enabled": bool(self._setup_session_arbitration_var.get()) if advisory_enabled else False,
            },
            "mode_flags": {
                "single_agent_mode": len(selected_agents) == 1,
                "self_verify_allowed": bool(self._setup_self_verify_var.get()),
                "self_advisory_allowed": bool(self._setup_self_advisory_var.get()) if advisory_enabled else False,
            },
            "executor_override": self._setup_executor_var.get().strip() or "auto",
        }

    def _setup_draft_payload(self, form_payload: dict[str, object]) -> dict[str, object]:
        payload = {
            "schema_version": 1,
            "selected_agents": list(form_payload.get("selected_agents", []) or []),
            "role_bindings": dict(form_payload.get("role_bindings", {}) or {}),
            "role_options": dict(form_payload.get("role_options", {}) or {}),
            "mode_flags": dict(form_payload.get("mode_flags", {}) or {}),
            "executor_override": str(form_payload.get("executor_override") or "auto"),
        }
        payload["metadata"] = {
            "draft_saved_at": utc_now_iso(),
            "saved_by": "launcher",
        }
        return payload

    def _setup_active_payload(
        self,
        form_payload: dict[str, object],
        *,
        source_setup_id: str,
    ) -> dict[str, object]:
        payload = {
            "schema_version": 1,
            "selected_agents": list(form_payload.get("selected_agents", []) or []),
            "role_bindings": dict(form_payload.get("role_bindings", {}) or {}),
            "role_options": dict(form_payload.get("role_options", {}) or {}),
            "mode_flags": dict(form_payload.get("mode_flags", {}) or {}),
        }
        payload["metadata"] = {
            "saved_at": utc_now_iso(),
            "saved_by": "launcher",
            "source_setup_id": source_setup_id,
        }
        return payload

    def _setup_payload_for_fingerprint(self, payload: dict[str, object]) -> dict[str, object]:
        normalized = canonical_setup_payload_for_fingerprint(payload)
        normalized["schema_version"] = int(normalized.get("schema_version") or 1)
        return normalized

    def _setup_fingerprint(self, payload: dict[str, object]) -> str:
        return fingerprint_payload(self._setup_payload_for_fingerprint(payload))

    def _setup_active_profile_fingerprint(self, payload: dict[str, object]) -> str:
        return active_profile_fingerprint(payload)

    def _setup_preview_fingerprint(
        self,
        form_payload: dict[str, object],
        *,
        setup_id: str,
        draft_fingerprint: str,
    ) -> str:
        preview_basis = {
            "schema_version": 1,
            "setup_id": setup_id,
            "draft_fingerprint": draft_fingerprint,
            "effective_executor": self._setup_effective_executor(form_payload),
            "config": self._setup_payload_for_fingerprint(form_payload),
        }
        return fingerprint_payload(preview_basis)

    @staticmethod
    def _setup_preview_matches_current(
        preview_payload: dict[str, object] | None,
        current_setup_id: str,
        current_draft_fingerprint: str,
    ) -> bool:
        if not preview_payload or not current_setup_id or not current_draft_fingerprint:
            return False
        return (
            str(preview_payload.get("setup_id") or "") == current_setup_id
            and str(preview_payload.get("draft_fingerprint") or "") == current_draft_fingerprint
        )

    @staticmethod
    def _setup_result_can_promote_active(
        result_payload: dict[str, object] | None,
        apply_payload: dict[str, object] | None,
        preview_payload: dict[str, object] | None,
        current_setup_id: str,
        draft_payload: dict[str, object] | None,
        current_draft_fingerprint: str,
        draft_fingerprint_fn,
    ) -> tuple[bool, str]:
        if not result_payload or not apply_payload or not preview_payload or not current_setup_id:
            return False, "적용 결과에 필요한 setup 기록이 아직 완성되지 않았습니다."
        if str(result_payload.get("status") or "") != "applied":
            return False, "적용 결과가 성공 상태가 아니어서 active 승격을 보류했습니다."
        if str(result_payload.get("setup_id") or "") != current_setup_id:
            return False, "적용 결과의 setup_id가 현재 setup과 달라 active 승격을 보류했습니다."
        if str(apply_payload.get("setup_id") or "") != current_setup_id:
            return False, "적용 요청의 setup_id가 현재 setup과 달라 active 승격을 보류했습니다."
        if str(preview_payload.get("setup_id") or "") != current_setup_id:
            return False, "미리보기 setup_id가 현재 setup과 달라 active 승격을 보류했습니다."
        approved = str(apply_payload.get("approved_preview_fingerprint") or "")
        if not approved:
            return False, "적용 요청에 승인된 preview fingerprint가 없어 active 승격을 보류했습니다."
        if str(result_payload.get("approved_preview_fingerprint") or "") != approved:
            return False, "적용 결과의 approved preview fingerprint가 apply와 달라 active 승격을 보류했습니다."
        if str(preview_payload.get("preview_fingerprint") or "") != approved:
            return False, "현재 preview fingerprint가 apply 승인값과 달라 active 승격을 보류했습니다."
        if not draft_payload:
            return False, "현재 draft 파일이 없어 active 승격을 보류했습니다."
        if not current_draft_fingerprint:
            return False, "현재 draft fingerprint를 확인할 수 없어 active 승격을 보류했습니다."
        if str(preview_payload.get("draft_fingerprint") or "") != current_draft_fingerprint:
            return False, "현재 draft fingerprint와 preview 기준 draft가 달라 active 승격을 보류했습니다."
        if draft_fingerprint_fn(draft_payload) != current_draft_fingerprint:
            return False, "현재 draft 파일이 바뀌어 active 승격을 보류했습니다."
        return True, ""

    def _setup_resolve_support(self, form_payload: dict[str, object]) -> dict[str, object]:
        return resolve_active_profile(form_payload)

    def _resolve_runtime_active_profile(self) -> dict[str, object]:
        resolved = resolve_project_active_profile(self.project)
        self._runtime_launch_resolution = resolved
        return resolved

    def _runtime_resolution_messages(self, resolved: dict[str, object]) -> list[str]:
        return display_resolver_messages(resolved)

    def _runtime_resolution_detail(self, resolved: dict[str, object]) -> str:
        return " / ".join(self._runtime_resolution_messages(resolved))

    def _runtime_resolution_feedback_lines(self, resolved: dict[str, object]) -> list[str]:
        detail_lines = self._runtime_resolution_messages(resolved)
        if not detail_lines:
            return []
        status = str(resolved.get("resolution_state") or "")
        prefix = "오류" if status in {"broken", "needs_migration"} else "경고"
        return [f"{prefix}: 현재 runtime {line}" for line in detail_lines]

    def _apply_runtime_launch_presentation(self, resolved: dict[str, object]) -> None:
        support_level = str(resolved.get("support_level") or "blocked")
        detail = self._runtime_resolution_detail(resolved) or join_display_resolver_messages(resolved)
        text = f"실행 프로필: {_setup_support_label(support_level)}"
        if detail:
            text = f"{text} — {detail}"
        if hasattr(self, "_runtime_launch_var"):
            self._runtime_launch_var.set(text)
        if hasattr(self, "_setup_runtime_profile_var"):
            self._setup_runtime_profile_var.set(text)
        if hasattr(self, "_runtime_launch_label"):
            style = _SETUP_SUPPORT_STYLES.get(support_level, _SETUP_SUPPORT_STYLES["blocked"])
            self._runtime_launch_label.configure(fg=style["fg"])
        if hasattr(self, "_setup_runtime_profile_label"):
            style = _SETUP_SUPPORT_STYLES.get(support_level, _SETUP_SUPPORT_STYLES["blocked"])
            self._setup_runtime_profile_label.configure(fg=style["fg"])

    def _runtime_launch_allowed(self, resolved: dict[str, object] | None = None) -> bool:
        resolution = resolved or self._resolve_runtime_active_profile()
        controls = dict(resolution.get("controls") or {})
        return self._setup_state in ("ready", "ready_warn") and bool(controls.get("launch_allowed"))

    def _setup_support_banner_lines(
        self,
        support_level: str,
        controls: dict[str, object],
    ) -> list[str]:
        if not bool(controls.get("banner_required")):
            return []
        if support_level == "experimental":
            return ["안내: 현재 조합은 실험적 프로필입니다. 수동 확인이 더 필요할 수 있습니다."]
        if support_level == "blocked":
            return ["경고: 현재 프로필은 차단 상태입니다. 미리보기만 허용되고 적용과 launch는 차단됩니다."]
        return []

    def _update_setup_support_presentation(self, support_level: str) -> None:
        if not hasattr(self, "_setup_support_label"):
            return
        style = _SETUP_SUPPORT_STYLES.get(support_level, _SETUP_SUPPORT_STYLES["blocked"])
        self._setup_support_label.configure(
            fg=style["fg"],
            bg=style["bg"],
        )

    def _setup_validate(self, form_payload: dict[str, object]) -> tuple[list[str], list[str], list[str]]:
        selected = list(form_payload.get("selected_agents", []) or [])
        bindings = dict(form_payload.get("role_bindings", {}) or {})
        options = dict(form_payload.get("role_options", {}) or {})
        flags = dict(form_payload.get("mode_flags", {}) or {})

        implement = str(bindings.get("implement") or "")
        verify = str(bindings.get("verify") or "")
        advisory = str(bindings.get("advisory") or "")
        advisory_enabled = bool(options.get("advisory_enabled"))
        session_arbitration_enabled = bool(options.get("session_arbitration_enabled"))
        self_verify_allowed = bool(flags.get("self_verify_allowed"))
        self_advisory_allowed = bool(flags.get("self_advisory_allowed"))
        executor_override = str(form_payload.get("executor_override") or "auto")

        errors: list[str] = []
        warnings: list[str] = []
        infos: list[str] = []

        if not selected:
            errors.append("최소 1개의 agent를 선택해야 합니다.")
        if not implement:
            errors.append("구현 역할은 반드시 지정해야 합니다.")
        elif implement not in selected:
            errors.append("구현 역할이 선택되지 않은 agent를 가리킵니다.")

        if verify and verify not in selected:
            errors.append("검증 역할이 선택되지 않은 agent를 가리킵니다.")
        if advisory_enabled and advisory and advisory not in selected:
            errors.append("자문 역할이 선택되지 않은 agent를 가리킵니다.")
        if implement and verify and implement == verify and not self_verify_allowed:
            errors.append("현재 설정에서는 구현 역할과 검증 역할을 같은 agent에 둘 수 없습니다.")
        if advisory_enabled and advisory and not self_advisory_allowed and advisory in {implement, verify}:
            errors.append("현재 설정에서는 자문 역할을 구현/검증과 같은 agent에 둘 수 없습니다.")

        if not verify:
            warnings.append("검증 역할이 비어 있습니다. 자체 검증 또는 수동 확인이 필요할 수 있습니다.")
        if session_arbitration_enabled and not advisory_enabled:
            warnings.append("세션 중재는 자문 역할이 비활성일 때 사용할 수 없습니다.")

        effective_executor = self._setup_effective_executor(form_payload)
        if executor_override == "auto" and effective_executor != "auto":
            infos.append(f"설정 실행자는 {effective_executor}로 자동 선택됩니다.")
        if not advisory_enabled:
            infos.append("자문 역할이 비활성화되어 관련 바인딩과 중재 옵션은 무시됩니다.")
        infos.append("적용 전까지 runtime은 active config만 사용합니다.")
        return errors, warnings, infos

    def _setup_effective_executor(self, form_payload: dict[str, object]) -> str:
        override = str(form_payload.get("executor_override") or "auto")
        selected = list(form_payload.get("selected_agents", []) or [])
        if override != "auto" and override in selected:
            return override
        return self._setup_recommended_executor(selected, dict(form_payload.get("role_bindings", {}) or {}))

    def _setup_write_json(self, path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, payload)

    def _setup_apply_form_payload(self, payload: dict[str, object], *, draft_saved: bool) -> None:
        normalized = self._setup_default_profile()
        normalized.update({
            "selected_agents": list(payload.get("selected_agents", []) or []),
            "role_bindings": dict(payload.get("role_bindings", {}) or {}),
            "role_options": dict(payload.get("role_options", {}) or {}),
            "mode_flags": dict(payload.get("mode_flags", {}) or {}),
            "executor_override": str(payload.get("executor_override") or "auto"),
        })
        selected = set(normalized["selected_agents"])

        self._setup_form_updating = True
        try:
            for name in _SETUP_AGENT_ORDER:
                self._setup_agent_vars[name].set(name in selected)
            bindings = normalized["role_bindings"]
            self._setup_implement_var.set(str(bindings.get("implement") or ""))
            self._setup_verify_var.set(str(bindings.get("verify") or ""))
            self._setup_advisory_var.set(str(bindings.get("advisory") or ""))
            role_options = normalized["role_options"]
            self._setup_advisory_enabled_var.set(bool(role_options.get("advisory_enabled")))
            self._setup_operator_stop_enabled_var.set(bool(role_options.get("operator_stop_enabled")))
            self._setup_session_arbitration_var.set(bool(role_options.get("session_arbitration_enabled")))
            mode_flags = normalized["mode_flags"]
            self._setup_self_verify_var.set(bool(mode_flags.get("self_verify_allowed")))
            self._setup_self_advisory_var.set(bool(mode_flags.get("self_advisory_allowed")))
            self._setup_executor_var.set(str(normalized.get("executor_override") or "auto"))
        finally:
            self._setup_form_updating = False

        self._setup_draft_saved = draft_saved
        self._setup_dirty = False
        self._setup_current_setup_id = ""
        self._setup_current_preview_fingerprint = ""
        self._setup_current_request_payload = None
        self._setup_current_preview_payload = None
        self._setup_current_apply_payload = None
        self._setup_current_result_payload = None
        self._update_setup_widget_options()

    def _load_setup_form_from_disk(self) -> None:
        paths = self._setup_paths()
        draft_payload = read_json(paths["draft"])
        active_payload = read_json(paths["active"])
        source = draft_payload or active_payload or self._setup_default_profile()
        self._setup_apply_form_payload(source, draft_saved=draft_payload is not None)

    def _setup_reset_cleanup_history(self) -> None:
        self._setup_cleanup_history = []
        self._setup_cleanup_summary_var.set("아직 정리 기록이 없습니다.")

    def _setup_record_cleanup_result(
        self,
        *,
        source_label: str,
        removed_count: int,
        include_noop: bool = False,
    ) -> None:
        if removed_count <= 0 and not include_noop:
            return
        if removed_count > 0:
            line = f"{source_label}: 오래된 setup 파일 {removed_count}개 정리"
        else:
            line = f"{source_label}: 정리할 오래된 setup 파일이 없습니다"
        history = list(self._setup_cleanup_history)
        history.insert(0, line)
        self._setup_cleanup_history = history[:5]
        self._setup_cleanup_summary_var.set("\n".join(self._setup_cleanup_history))

    def _setup_cleanup_staged_files_once_on_startup(self) -> None:
        paths = self._setup_paths()
        removed = self._setup_cleanup_staged_files(
            request_payload=read_json(paths["request"]),
            preview_payload=read_json(paths["preview"]),
            apply_payload=read_json(paths["apply"]),
            result_payload=read_json(paths["result"]),
            last_applied_payload=read_json(paths["last_applied"]),
        )
        self._setup_record_cleanup_result(source_label="초기 정리", removed_count=len(removed))

    def _setup_cleanup_staged_files(
        self,
        *,
        request_payload: dict[str, object] | None,
        preview_payload: dict[str, object] | None,
        apply_payload: dict[str, object] | None,
        result_payload: dict[str, object] | None,
        last_applied_payload: dict[str, object] | None = None,
    ) -> list[Path]:
        paths = self._setup_paths()
        protected_setup_ids = self._setup_protected_staged_setup_ids(
            request_payload=request_payload,
            preview_payload=preview_payload,
            apply_payload=apply_payload,
            result_payload=result_payload,
            last_applied_payload=last_applied_payload,
        )
        removed = cleanup_stale_setup_artifacts(
            setup_dir=paths["setup_dir"],
            protected_setup_ids=protected_setup_ids,
        )
        removed.extend(
            self._setup_executor_adapter.cleanup_staged_files(
                setup_dir=paths["setup_dir"],
                protected_setup_ids=protected_setup_ids,
            )
        )
        return removed

    def _on_setup_clean_staged(self) -> None:
        if not self._project_valid:
            return
        paths = self._setup_paths()
        request_payload = read_json(paths["request"])
        preview_payload = read_json(paths["preview"])
        apply_payload = read_json(paths["apply"])
        result_payload = read_json(paths["result"])
        last_applied_payload = read_json(paths["last_applied"])
        removed = self._setup_cleanup_staged_files(
            request_payload=request_payload,
            preview_payload=preview_payload,
            apply_payload=apply_payload,
            result_payload=result_payload,
            last_applied_payload=last_applied_payload,
        )
        self._setup_record_cleanup_result(
            source_label="수동 정리",
            removed_count=len(removed),
            include_noop=True,
        )
        self._refresh_setup_mode_state()
        self._set_toast_style("success")
        if removed:
            self.msg_var.set(f"오래된 setup 파일 {len(removed)}개를 정리했습니다")
        else:
            self.msg_var.set("정리할 오래된 setup 파일이 없습니다")
        self._clear_msg_later()

    def _update_setup_widget_options(self) -> None:
        if not hasattr(self, "_setup_bind_implement_combo"):
            return
        selected_agents = self._setup_selected_agents()
        role_values = [""] + selected_agents
        executor_values = ["auto"] + selected_agents

        for combo in (
            self._setup_bind_implement_combo,
            self._setup_bind_verify_combo,
            self._setup_bind_advisory_combo,
        ):
            combo.configure(values=role_values)
        self._setup_executor_combo.configure(values=executor_values)

        form_enabled = self._setup_mode_state != "ApplyPending"
        role_state = "readonly" if form_enabled and selected_agents else "disabled"
        self._setup_bind_implement_combo.configure(state=role_state)
        self._setup_bind_verify_combo.configure(state=role_state)
        advisory_state = (
            "readonly"
            if form_enabled and selected_agents and bool(self._setup_advisory_enabled_var.get())
            else "disabled"
        )
        self._setup_bind_advisory_combo.configure(state=advisory_state)
        self._setup_executor_combo.configure(
            state="readonly" if form_enabled and selected_agents else "disabled"
        )
        if hasattr(self, "_setup_option_cb_0"):
            for cb in (
                self._setup_option_cb_0,
                self._setup_option_cb_1,
                self._setup_option_cb_3,
            ):
                cb.configure(state=NORMAL if form_enabled else DISABLED)
            self._setup_option_cb_2.configure(
                state=NORMAL if form_enabled and bool(self._setup_advisory_enabled_var.get()) else DISABLED
            )
            self._setup_option_cb_4.configure(
                state=NORMAL if form_enabled and bool(self._setup_advisory_enabled_var.get()) else DISABLED
            )

    def _setup_apply_inline_errors(self, errors: list[str]) -> None:
        agent_error = ""
        implement_error = ""
        verify_error = ""
        advisory_error = ""
        for msg in errors:
            if "최소 1개의 agent" in msg:
                agent_error = msg
            elif "구현 역할" in msg:
                implement_error = msg
            elif "검증 역할" in msg or "구현 역할과 검증 역할" in msg:
                verify_error = msg
            elif "자문 역할" in msg or "자문 역할을 구현/검증" in msg:
                advisory_error = msg
        self._setup_agent_error_var.set(agent_error)
        self._setup_implement_error_var.set(implement_error)
        self._setup_verify_error_var.set(verify_error)
        self._setup_advisory_error_var.set(advisory_error)

    def _setup_summary_text(
        self,
        form_payload: dict[str, object],
        preview_payload: dict[str, object] | None,
        *,
        preview_current: bool,
        stale_preview: bool,
    ) -> str:
        bindings = dict(form_payload.get("role_bindings", {}) or {})
        options = dict(form_payload.get("role_options", {}) or {})
        lines = [
            f"에이전트: {', '.join(form_payload.get('selected_agents', []) or ['—'])}",
            f"구현: {bindings.get('implement') or '—'}",
            f"검증: {bindings.get('verify') or '—'}",
            f"자문: {bindings.get('advisory') or '—'}",
            (
                "옵션: "
                f"자문={'켜짐' if options.get('advisory_enabled') else '꺼짐'} · "
                f"operator 중지={'켜짐' if options.get('operator_stop_enabled') else '꺼짐'} · "
                f"세션 중재={'켜짐' if options.get('session_arbitration_enabled') else '꺼짐'}"
            ),
            f"실행자: {self._setup_effective_executor(form_payload)}",
        ]
        if preview_current and preview_payload:
            lines.append(
                "지원 수준: "
                + _setup_support_label(str(preview_payload.get("support_level") or "experimental"))
            )
            planned = preview_payload.get("planned_changes") or {}
            writes = list((planned.get("write") if isinstance(planned, dict) else []) or [])
            if writes:
                lines.append("예정 쓰기: " + ", ".join(str(item) for item in writes[:4]))
            diff_summary = list(preview_payload.get("diff_summary") or [])
            if diff_summary:
                lines.append("미리보기: " + str(diff_summary[0]))
        elif stale_preview and preview_payload:
            lines.append("미리보기: 현재 초안과 맞지 않는 이전 미리보기를 무시했습니다")
        else:
            lines.append("미리보기: 생성된 미리보기가 없습니다")
        return "\n".join(lines)

    def _setup_restart_required_for_payload(self, payload: dict[str, object]) -> bool:
        active_payload = read_json(self._setup_paths()["active"])
        if not active_payload:
            return True
        return self._setup_active_profile_fingerprint(active_payload) != self._setup_active_profile_fingerprint(payload)

    def _setup_active_matches_current_form(
        self,
        active_payload: dict[str, object] | None,
        form_payload: dict[str, object],
    ) -> bool:
        if not active_payload or self._setup_dirty:
            return False
        return self._setup_active_profile_fingerprint(active_payload) == self._setup_active_profile_fingerprint(
            form_payload
        )

    def _setup_build_preview_payload(
        self,
        form_payload: dict[str, object],
        *,
        setup_id: str,
        draft_fingerprint: str,
    ) -> dict[str, object]:
        errors, warnings, infos = self._setup_validate(form_payload)
        support_resolution = self._setup_resolve_support(form_payload)
        support_level = str(support_resolution.get("support_level") or "blocked")
        controls = dict(support_resolution.get("controls") or {})
        messages = list(support_resolution.get("messages") or [])
        effective_executor = self._setup_effective_executor(form_payload)
        preview_fingerprint = self._setup_preview_fingerprint(
            form_payload,
            setup_id=setup_id,
            draft_fingerprint=draft_fingerprint,
        )
        selected = list(form_payload.get("selected_agents", []) or [])
        bindings = dict(form_payload.get("role_bindings", {}) or {})
        options = dict(form_payload.get("role_options", {}) or {})
        restart_required = self._setup_restart_required_for_payload(self._setup_draft_payload(form_payload))
        diff_summary = [
            f"에이전트 {', '.join(selected or ['—'])} / 구현 {bindings.get('implement') or '—'} / 검증 {bindings.get('verify') or '—'} / 자문 {bindings.get('advisory') or '—'}",
            (
                "옵션 "
                f"자문={'켜짐' if options.get('advisory_enabled') else '꺼짐'} · "
                f"operator 중지={'켜짐' if options.get('operator_stop_enabled') else '꺼짐'} · "
                f"세션 중재={'켜짐' if options.get('session_arbitration_enabled') else '꺼짐'}"
            ),
        ]
        return {
            "status": "preview_ready",
            "setup_id": setup_id,
            "schema_version": 1,
            "generated_at": utc_now_iso(),
            "draft_fingerprint": draft_fingerprint,
            "preview_fingerprint": preview_fingerprint,
            "effective_executor": effective_executor,
            "support_level": support_level,
            "controls": controls,
            "messages": messages,
            "effective_runtime_plan": support_resolution.get("effective_runtime_plan"),
            "warnings": warnings,
            "infos": infos,
            "planned_changes": {
                "write": [".pipeline/config/agent_profile.json"],
                "restart_targets": ["watcher", "launcher"] if restart_required else [],
            },
            "diff_summary": diff_summary,
            "restart_required": restart_required,
        }

    def _setup_preview_can_promote_canonical(self, setup_id: str) -> bool:
        request_payload = read_json(self._setup_paths()["request"])
        return bool(
            setup_id
            and setup_id == self._setup_current_setup_id
            and request_payload
            and str(request_payload.get("setup_id") or "") == setup_id
        )

    def _setup_result_can_promote_canonical(self, setup_id: str) -> bool:
        apply_payload = read_json(self._setup_paths()["apply"])
        return bool(
            setup_id
            and setup_id == self._setup_current_setup_id
            and apply_payload
            and str(apply_payload.get("setup_id") or "") == setup_id
        )

    @staticmethod
    def _setup_result_matches_current(
        result_payload: dict[str, object] | None,
        *,
        current_setup_id: str,
        current_preview_fingerprint: str,
    ) -> bool:
        if not result_payload or not current_setup_id:
            return False
        if str(result_payload.get("setup_id") or "") != current_setup_id:
            return False
        approved = str(result_payload.get("approved_preview_fingerprint") or "")
        if current_preview_fingerprint and approved and approved != current_preview_fingerprint:
            return False
        return True

    def _setup_protected_staged_setup_ids(
        self,
        *,
        request_payload: dict[str, object] | None = None,
        preview_payload: dict[str, object] | None = None,
        apply_payload: dict[str, object] | None = None,
        result_payload: dict[str, object] | None = None,
        last_applied_payload: dict[str, object] | None = None,
        extra_setup_ids: tuple[str, ...] = (),
    ) -> set[str]:
        protected: set[str] = {item for item in extra_setup_ids if item}
        payloads = (
            request_payload,
            apply_payload,
            last_applied_payload,
            getattr(self, "_setup_current_request_payload", None),
            self._setup_current_apply_payload,
        )
        current_only_payloads = (
            preview_payload,
            result_payload,
            self._setup_current_preview_payload,
            self._setup_current_result_payload,
        )
        if self._setup_mode_state in {"PreviewWaiting", "ApplyPending"} and self._setup_current_setup_id:
            protected.add(self._setup_current_setup_id)
        for payload in payloads:
            if not payload:
                continue
            setup_id = str(payload.get("setup_id") or "").strip()
            if setup_id:
                protected.add(setup_id)
        for payload in current_only_payloads:
            if not payload:
                continue
            setup_id = str(payload.get("setup_id") or "").strip()
            if setup_id and setup_id == self._setup_current_setup_id:
                protected.add(setup_id)
        return {item for item in protected if item}

    def _setup_execute_preview_roundtrip(
        self,
        request_payload: dict[str, object],
        form_payload: dict[str, object],
    ) -> None:
        self._setup_executor_adapter.dispatch_preview(
            destination=self._setup_paths()["preview"],
            build_payload=lambda: self._setup_build_preview_payload(
                form_payload,
                setup_id=str(request_payload.get("setup_id") or ""),
                draft_fingerprint=str(request_payload.get("draft_fingerprint") or ""),
            ),
            write_json=self._setup_write_json,
            should_promote=self._setup_preview_can_promote_canonical,
            protected_setup_ids=self._setup_protected_staged_setup_ids,
        )

    def _setup_execute_apply_roundtrip(
        self,
        apply_payload: dict[str, object],
        form_payload: dict[str, object],
        preview_payload: dict[str, object],
        current_draft_fingerprint: str,
    ) -> None:
        self._setup_executor_adapter.dispatch_result(
            destination=self._setup_paths()["result"],
            build_payload=lambda: {
                "status": "applied",
                "setup_id": str(apply_payload.get("setup_id") or ""),
                "schema_version": 1,
                "finished_at": utc_now_iso(),
                "approved_preview_fingerprint": str(apply_payload.get("approved_preview_fingerprint") or ""),
                "effective_executor": self._setup_effective_executor(form_payload),
                "restart_required": bool(preview_payload.get("restart_required")),
                "draft_fingerprint": current_draft_fingerprint,
                "message": _SETUP_DEFAULT_APPLY_RESULT_MESSAGE,
            },
            write_json=self._setup_write_json,
            should_promote=self._setup_result_can_promote_canonical,
            protected_setup_ids=self._setup_protected_staged_setup_ids,
        )

    def _setup_result_feedback_lines(
        self,
        result_payload: dict[str, object] | None,
        *,
        current_setup_id: str,
    ) -> list[str]:
        if not result_payload or str(result_payload.get("setup_id") or "") != current_setup_id:
            return []
        lines: list[str] = []
        status = str(result_payload.get("status") or "")
        errors = list(result_payload.get("errors") or [])
        warnings = list(result_payload.get("warnings") or [])
        infos = list(result_payload.get("infos") or [])
        message = str(result_payload.get("message") or "").strip()

        if status == "apply_failed":
            if errors:
                lines.extend(f"오류: {msg}" for msg in errors if str(msg).strip())
            if message:
                lines.append(f"오류: {message}")
            if not errors and not message:
                lines.append("오류: 설정 적용이 실패했습니다.")
        else:
            if errors:
                lines.extend(f"오류: {msg}" for msg in errors if str(msg).strip())
            if message and message != _SETUP_DEFAULT_APPLY_RESULT_MESSAGE:
                lines.append(f"안내: {message}")
        if warnings:
            lines.extend(f"경고: {msg}" for msg in warnings if str(msg).strip())
        if infos:
            lines.extend(f"안내: {msg}" for msg in infos if str(msg).strip())
        return lines

    def _setup_sync_last_applied_record(
        self,
        *,
        active_payload: dict[str, object],
        result_payload: dict[str, object],
        fallback_executor: str,
    ) -> dict[str, object]:
        record = build_last_applied_record(
            setup_id=str(result_payload.get("setup_id") or ""),
            approved_preview_fingerprint=str(result_payload.get("approved_preview_fingerprint") or ""),
            active_payload=active_payload,
            restart_required=bool(result_payload.get("restart_required")),
            executor=str(result_payload.get("effective_executor") or fallback_executor or "auto"),
            applied_at=str(result_payload.get("finished_at") or utc_now_iso()),
        )
        path = self._setup_paths()["last_applied"]
        current_payload = read_json(path)
        if current_payload != record:
            self._setup_write_json(path, record)
        return record

    @staticmethod
    def _setup_result_replays_last_applied(
        result_payload: dict[str, object] | None,
        last_applied_payload: dict[str, object] | None,
        *,
        active_exists: bool,
    ) -> bool:
        if active_exists or not result_payload or not isinstance(last_applied_payload, dict):
            return False
        result_setup_id = str(result_payload.get("setup_id") or "").strip()
        result_approved = str(result_payload.get("approved_preview_fingerprint") or "").strip()
        return bool(
            result_setup_id
            and result_approved
            and result_setup_id == str(last_applied_payload.get("setup_id") or "").strip()
            and result_approved == str(last_applied_payload.get("approved_preview_fingerprint") or "").strip()
        )

    def _setup_reconcile_last_applied(self) -> dict[str, object]:
        paths = self._setup_paths()
        active_path = paths["active"]
        last_applied_path = paths["last_applied"]
        return reconcile_last_applied(
            active_payload=read_json(active_path),
            last_applied_payload=read_json(last_applied_path),
            active_exists=active_path.exists(),
            last_applied_exists=last_applied_path.exists(),
        )

    def _setup_last_applied_feedback_lines(self, reconciliation: dict[str, object]) -> list[str]:
        status = str(reconciliation.get("status") or "")
        setup_id = str(reconciliation.get("setup_id") or "").strip()
        executor = str(reconciliation.get("executor") or "").strip()
        prefix = f"최근 적용 기록({setup_id}" if setup_id else "최근 적용 기록("
        if setup_id and executor:
            prefix += f", 실행자 {executor}"
        elif executor:
            prefix += f"실행자 {executor}"
        prefix += ")"
        if status == "ok" and bool(reconciliation.get("restart_required")):
            return [f"안내: {prefix}이 active profile과 일치합니다."]
        if status == "mismatch":
            if not str(reconciliation.get("current_active_profile_fingerprint") or "").strip():
                return [f"경고: {prefix}은 있지만 active profile이 없습니다. 설정을 다시 적용하거나 active profile을 복구해 주세요."]
            return [f"경고: {prefix}과 active profile이 다릅니다. preview/apply를 다시 확인해 주세요."]
        if status == "broken":
            return ["오류: 최근 적용 기록을 확인할 수 없어 restart reconciliation을 완료하지 못했습니다."]
        return []

    def _setup_last_applied_notice_text(self, reconciliation: dict[str, object], *, state: str) -> str:
        if state == "Applied" and self._setup_restart_required:
            return "설정 적용이 끝났습니다. active profile을 읽으려면 watcher/launcher를 재시작하세요."
        status = str(reconciliation.get("status") or "")
        if status == "ok" and bool(reconciliation.get("restart_required")):
            return "최근 적용 기록이 active profile과 일치합니다."
        if status == "mismatch":
            if not str(reconciliation.get("current_active_profile_fingerprint") or "").strip():
                return "최근 적용 기록은 있지만 active profile이 없어 recovery가 필요합니다."
            return "최근 적용 기록과 active profile이 달라 restart reconciliation이 필요합니다."
        if status == "broken":
            return "최근 적용 기록을 읽지 못해 restart reconciliation을 확인할 수 없습니다."
        return ""

    def _refresh_setup_mode_state(self) -> None:
        if not hasattr(self, "_setup_mode_state_var"):
            return

        form_payload = self._setup_collect_form_payload()
        current_draft_fingerprint = self._setup_fingerprint(self._setup_draft_payload(form_payload))
        paths = self._setup_paths()
        draft_payload = read_json(paths["draft"])
        request_payload = read_json(paths["request"])
        preview_payload = read_json(paths["preview"])
        apply_payload = read_json(paths["apply"])
        result_payload = read_json(paths["result"])
        active_payload = read_json(paths["active"])
        last_applied_payload = read_json(paths["last_applied"])
        disk_setup_truth_exists = any(
            path.exists()
            for path in (
                paths["active"],
                paths["request"],
                paths["preview"],
                paths["apply"],
                paths["result"],
                paths["last_applied"],
            )
        )

        if not disk_setup_truth_exists:
            self._setup_current_setup_id = ""
            self._setup_current_preview_fingerprint = ""
            self._setup_current_request_payload = None
            self._setup_current_preview_payload = None
            self._setup_current_apply_payload = None
            self._setup_current_result_payload = None

        self._setup_current_draft_fingerprint = current_draft_fingerprint
        self._setup_draft_saved = bool(
            draft_payload
            and self._setup_fingerprint(draft_payload) == current_draft_fingerprint
        )

        errors, warnings, infos = self._setup_validate(form_payload)
        self._setup_errors = errors
        self._setup_warnings = warnings
        self._setup_infos = infos
        self._setup_has_error = bool(errors)
        self._setup_has_warning = bool(warnings)
        support_resolution = self._setup_resolve_support(form_payload)
        self._setup_current_support_resolution = support_resolution

        request_current = bool(
            request_payload
            and str(request_payload.get("setup_id") or "") == self._setup_current_setup_id
            and str(request_payload.get("draft_fingerprint") or "") == current_draft_fingerprint
        )
        self._setup_current_request_payload = request_payload if request_current else None

        canonical_preview_current = self._setup_preview_matches_current(
            preview_payload, self._setup_current_setup_id, current_draft_fingerprint
        )
        cached_preview_current = self._setup_preview_matches_current(
            self._setup_current_preview_payload, self._setup_current_setup_id, current_draft_fingerprint
        )
        stale_preview = bool(preview_payload) and not canonical_preview_current
        preview_current = False
        effective_preview_payload: dict[str, object] | None = None
        if canonical_preview_current and preview_payload:
            preview_current = True
            effective_preview_payload = preview_payload
        elif cached_preview_current and self._setup_current_preview_payload:
            preview_current = True
            effective_preview_payload = self._setup_current_preview_payload
        if effective_preview_payload:
            self._setup_current_preview_payload = effective_preview_payload
            self._setup_current_preview_fingerprint = str(effective_preview_payload.get("preview_fingerprint") or "")
        else:
            self._setup_current_preview_payload = None
            self._setup_current_preview_fingerprint = ""

        apply_current = bool(
            apply_payload
            and str(apply_payload.get("setup_id") or "") == self._setup_current_setup_id
            and str(apply_payload.get("approved_preview_fingerprint") or "") == self._setup_current_preview_fingerprint
        )
        self._setup_current_apply_payload = apply_payload if apply_current else None

        promotion_failed = False
        promotion_failed_message = ""
        canonical_result_current = self._setup_result_matches_current(
            result_payload,
            current_setup_id=self._setup_current_setup_id,
            current_preview_fingerprint=self._setup_current_preview_fingerprint,
        )
        cached_result_current = self._setup_result_matches_current(
            self._setup_current_result_payload,
            current_setup_id=self._setup_current_setup_id,
            current_preview_fingerprint=self._setup_current_preview_fingerprint,
        )
        effective_result_payload: dict[str, object] | None = None
        if canonical_result_current and result_payload:
            effective_result_payload = result_payload
        elif cached_result_current and self._setup_current_result_payload:
            effective_result_payload = self._setup_current_result_payload

        if effective_result_payload:
            self._setup_current_result_payload = effective_result_payload
            replayed_result = self._setup_result_replays_last_applied(
                effective_result_payload,
                last_applied_payload,
                active_exists=paths["active"].exists(),
            )
            if replayed_result:
                self._setup_restart_required = False
            else:
                can_promote, promotion_failed_message = self._setup_result_can_promote_active(
                    effective_result_payload,
                    self._setup_current_apply_payload,
                    self._setup_current_preview_payload,
                    self._setup_current_setup_id,
                    draft_payload,
                    current_draft_fingerprint,
                    self._setup_fingerprint,
                )
            if not replayed_result and can_promote:
                promoted_active_payload = self._setup_promote_active_profile(
                    draft_payload,
                    source_setup_id=self._setup_current_setup_id,
                )
                last_applied_payload = self._setup_sync_last_applied_record(
                    active_payload=promoted_active_payload,
                    result_payload=effective_result_payload,
                    fallback_executor=self._setup_effective_executor(form_payload),
                )
                self._setup_restart_required = bool(effective_result_payload.get("restart_required"))
            elif not replayed_result and str(effective_result_payload.get("status") or "") == "applied":
                promotion_failed = True
        else:
            self._setup_current_result_payload = None
            self._setup_restart_required = False

        active_matches_current = self._setup_active_matches_current_form(active_payload, form_payload)

        state = "DraftOnly"
        if self._setup_has_error:
            state = "InvalidConfig"
        elif apply_current and self._setup_current_result_payload is None:
            state = "ApplyPending"
        elif (
            self._setup_current_result_payload is not None
            and str(self._setup_current_result_payload.get("status") or "") == "apply_failed"
        ) or promotion_failed:
            state = "ApplyFailed"
        elif (
            self._setup_current_result_payload is not None
            and str(self._setup_current_result_payload.get("status") or "") == "applied"
            and not promotion_failed
        ):
            state = "Applied"
        elif active_matches_current:
            state = "Applied"
        elif preview_current:
            state = "PreviewReady"
        elif request_current:
            state = "PreviewWaiting"
        reconciliation = self._setup_reconcile_last_applied()
        reconciliation_status = str(reconciliation.get("status") or "")
        if state == "Applied" and reconciliation_status in {"mismatch", "broken"}:
            state = "RecoveryNeeded"

        self._setup_mode_state = state
        self._update_setup_widget_options()

        self._setup_apply_inline_errors(errors)
        display_support_level = str(support_resolution.get("support_level") or "blocked")
        display_controls = dict(support_resolution.get("controls") or {})
        if preview_current and self._setup_current_preview_payload:
            display_support_level = str(self._setup_current_preview_payload.get("support_level") or display_support_level)
            display_controls = dict(self._setup_current_preview_payload.get("controls") or display_controls)
        self._setup_mode_state_var.set(_setup_state_label(state))
        self._setup_support_level_var.set(_setup_support_label(display_support_level))
        self._update_setup_support_presentation(display_support_level)
        self._setup_current_setup_id_var.set(self._setup_current_setup_id or "—")
        self._setup_current_preview_fingerprint_var.set(self._setup_current_preview_fingerprint or "—")

        validation_lines = self._setup_result_feedback_lines(
            self._setup_current_result_payload,
            current_setup_id=self._setup_current_setup_id,
        )
        validation_lines.extend(self._setup_support_banner_lines(display_support_level, display_controls))
        validation_lines.extend(self._setup_last_applied_feedback_lines(reconciliation))
        validation_lines.extend(self._runtime_resolution_feedback_lines(self._resolve_runtime_active_profile()))
        if errors:
            validation_lines.extend(f"오류: {msg}" for msg in errors)
        if promotion_failed_message:
            validation_lines.append(f"오류: {promotion_failed_message}")
        if warnings:
            validation_lines.extend(f"경고: {msg}" for msg in warnings)
        if infos:
            validation_lines.extend(f"안내: {msg}" for msg in infos)
        self._setup_validation_var.set("\n".join(validation_lines) if validation_lines else "유효성 문제 없음.")
        self._setup_preview_summary_var.set(
            self._setup_summary_text(
                form_payload,
                self._setup_current_preview_payload or preview_payload,
                preview_current=preview_current,
                stale_preview=stale_preview,
            )
        )
        self._setup_restart_notice_var.set(self._setup_last_applied_notice_text(reconciliation, state=state))
        self._setup_apply_readiness_var.set(
            self._setup_apply_readiness_text(
                state,
                preview_current,
                self._setup_current_preview_payload,
            )
        )
        self._update_setup_action_buttons()
        removed = self._setup_cleanup_staged_files(
            request_payload=request_payload,
            preview_payload=preview_payload,
            apply_payload=apply_payload,
            result_payload=result_payload,
            last_applied_payload=last_applied_payload,
        )
        self._setup_record_cleanup_result(source_label="자동 정리", removed_count=len(removed))
        self._sync_start_button_state()

    def _setup_apply_readiness_text(
        self,
        state: str,
        preview_current: bool,
        preview_payload: dict[str, object] | None = None,
    ) -> str:
        preview_controls = dict((preview_payload or {}).get("controls") or {})
        if preview_current and preview_payload and not bool(preview_controls.get("apply_allowed")):
            return "적용 비활성: 현재 프로필은 차단 상태여서 미리보기만 가능합니다"
        if state == "InvalidConfig":
            return "적용 비활성: 설정이 올바르지 않습니다"
        if state == "PreviewWaiting":
            return "적용 비활성: 현재 초안 기준 미리보기를 기다리는 중입니다"
        if state == "ApplyPending":
            return "적용 비활성: 이미 적용이 진행 중입니다"
        if state == "RecoveryNeeded":
            if preview_current and preview_payload and bool(preview_controls.get("apply_allowed")):
                return "적용 가능: active profile 복구를 위해 현재 미리보기를 다시 적용할 수 있습니다"
            return "적용 비활성: active profile 복구를 위해 미리보기를 다시 생성하세요"
        if state == "Applied" and not self._setup_dirty:
            return "적용 비활성: active profile이 현재 초안과 이미 같습니다"
        if not preview_current:
            if self._setup_dirty or not self._setup_draft_saved:
                return "적용 비활성: 현재 초안을 저장하거나 미리보기를 다시 생성하세요"
            return "적용 비활성: 미리보기를 기다리는 중입니다"
        return "적용 가능: 미리보기가 현재 초안과 일치합니다"

    def _update_setup_action_buttons(self) -> None:
        if not hasattr(self, "btn_setup_save_draft"):
            return
        action_pending = self._setup_mode_state in {"PreviewWaiting", "ApplyPending"}
        applied_current = self._setup_mode_state == "Applied" and not self._setup_dirty
        preview_current = bool(self._setup_current_preview_payload)
        action_blocked = self._action_in_progress or action_pending
        support_resolution = self._setup_current_support_resolution or self._setup_resolve_support(self._setup_collect_form_payload())
        support_controls = dict(support_resolution.get("controls") or {})
        preview_controls = dict((self._setup_current_preview_payload or {}).get("controls") or {})

        save_enabled = self._project_valid and not action_blocked and ((self._setup_dirty or not self._setup_draft_saved) and not applied_current)
        generate_enabled = self._project_valid and not action_blocked and not applied_current and bool(support_controls.get("preview_allowed", True))
        apply_enabled = preview_current and bool(preview_controls.get("apply_allowed")) and not action_blocked

        self.btn_setup_save_draft.configure(state=NORMAL if save_enabled else DISABLED)
        self.btn_setup_generate_preview.configure(state=NORMAL if generate_enabled else DISABLED)
        self.btn_setup_apply.configure(state=NORMAL if apply_enabled else DISABLED)
        if hasattr(self, "btn_setup_clean_staged"):
            clean_enabled = self._project_valid and not self._action_in_progress
            self.btn_setup_clean_staged.configure(state=NORMAL if clean_enabled else DISABLED)
        if hasattr(self, "btn_setup_restart_now"):
            restart_enabled = (
                self._setup_mode_state == "Applied"
                and self._setup_restart_required
                and not self._action_in_progress
            )
            self.btn_setup_restart_now.configure(state=NORMAL if restart_enabled else DISABLED)

    def _setup_promote_active_profile(
        self,
        draft_payload: dict[str, object],
        *,
        source_setup_id: str,
    ) -> dict[str, object]:
        paths = self._setup_paths()
        active_payload = read_json(paths["active"])
        if (
            active_payload
            and str((active_payload.get("metadata") or {}).get("source_setup_id") or "") == source_setup_id
        ):
            return active_payload
        promoted = self._setup_active_payload(draft_payload, source_setup_id=source_setup_id)
        self._setup_write_json(paths["active"], promoted)
        return promoted

    def _setup_generate_setup_id(self) -> str:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        return f"setup-{stamp}-{uuid4().hex[:6]}"

    def _on_setup_agent_change(self) -> None:
        if self._setup_form_updating:
            return
        selected = set(self._setup_selected_agents())
        self._setup_form_updating = True
        try:
            if self._setup_implement_var.get() and self._setup_implement_var.get() not in selected:
                self._setup_implement_var.set("")
            if self._setup_verify_var.get() and self._setup_verify_var.get() not in selected:
                self._setup_verify_var.set("")
            if self._setup_advisory_var.get() and self._setup_advisory_var.get() not in selected:
                self._setup_advisory_var.set("")
            if self._setup_executor_var.get() not in {"auto", *selected}:
                self._setup_executor_var.set("auto")
        finally:
            self._setup_form_updating = False
        self._setup_dirty = True
        self._update_setup_widget_options()
        self._refresh_setup_mode_state()

    def _on_setup_role_change(self, _event=None) -> None:
        if self._setup_form_updating:
            return
        self._setup_dirty = True
        self._refresh_setup_mode_state()

    def _on_setup_option_change(self) -> None:
        if self._setup_form_updating:
            return
        self._setup_form_updating = True
        try:
            if not self._setup_advisory_enabled_var.get():
                self._setup_advisory_var.set("")
                self._setup_session_arbitration_var.set(False)
                self._setup_self_advisory_var.set(False)
        finally:
            self._setup_form_updating = False
        self._setup_dirty = True
        self._update_setup_widget_options()
        self._refresh_setup_mode_state()

    def _on_setup_executor_change(self, _event=None) -> None:
        if self._setup_form_updating:
            return
        self._setup_dirty = True
        self._refresh_setup_mode_state()

    def _on_setup_save_draft(self) -> None:
        if not self._project_valid:
            return
        payload = self._setup_draft_payload(self._setup_collect_form_payload())
        self._setup_write_json(self._setup_paths()["draft"], payload)
        self._setup_draft_saved = True
        self._setup_dirty = False
        self._refresh_setup_mode_state()
        self._set_toast_style("success")
        self.msg_var.set("설정 초안을 저장했습니다")
        self._clear_msg_later()

    def _on_setup_generate_preview(self) -> None:
        if not self._project_valid:
            return
        try:
            if self._setup_dirty or not self._setup_draft_saved:
                self._on_setup_save_draft()
            form_payload = self._setup_collect_form_payload()
            support_resolution = self._setup_resolve_support(form_payload)
            support_controls = dict(support_resolution.get("controls") or {})
            if not bool(support_controls.get("preview_allowed", True)):
                self._set_toast_style("error")
                self.msg_var.set("미리보기 생성 실패: 현재 프로필은 preview만 허용되지 않는 상태입니다.")
                self._clear_msg_later(8000)
                return
            self._setup_current_setup_id = self._setup_generate_setup_id()
            request_payload = {
                "status": "setup_requested",
                "setup_id": self._setup_current_setup_id,
                "schema_version": 1,
                "project_root": str(self.project),
                "selected_agents": list(form_payload.get("selected_agents", []) or []),
                "role_bindings": dict(form_payload.get("role_bindings", {}) or {}),
                "role_options": dict(form_payload.get("role_options", {}) or {}),
                "mode_flags": dict(form_payload.get("mode_flags", {}) or {}),
                "config_paths": {
                    "active": ".pipeline/config/agent_profile.json",
                    "draft": ".pipeline/config/agent_profile.draft.json",
                },
                "draft_fingerprint": self._setup_current_draft_fingerprint,
                "executor_candidate": self._setup_effective_executor(form_payload),
                "support_level": str(support_resolution.get("support_level") or "blocked"),
                "controls": support_controls,
                "messages": list(support_resolution.get("messages") or []),
                "effective_runtime_plan": support_resolution.get("effective_runtime_plan"),
            }
            self._setup_current_preview_payload = None
            self._setup_current_preview_fingerprint = ""
            self._setup_current_request_payload = request_payload
            self._setup_current_apply_payload = None
            self._setup_current_result_payload = None
            self._setup_write_json(self._setup_paths()["request"], request_payload)
            self._setup_execute_preview_roundtrip(request_payload, form_payload)
            self._refresh_setup_mode_state()
            self._set_toast_style("progress")
            self.msg_var.set("설정 미리보기를 요청했습니다")
            self._clear_msg_later()
        except Exception as exc:
            self._set_toast_style("error")
            self.msg_var.set(f"미리보기 요청 실패: {exc}")
            self._clear_msg_later(10000)

    def _on_setup_apply(self) -> None:
        if not self._setup_current_preview_payload:
            self._set_toast_style("error")
            self.msg_var.set("적용 실패: 먼저 현재 초안 기준 미리보기를 생성해 주세요.")
            self._clear_msg_later(8000)
            return
        preview_controls = dict(self._setup_current_preview_payload.get("controls") or {})
        if not bool(preview_controls.get("apply_allowed")):
            self._set_toast_style("error")
            self.msg_var.set("적용 실패: 현재 미리보기 조합은 apply가 차단되어 있습니다.")
            self._clear_msg_later(8000)
            return
        try:
            form_payload = self._setup_collect_form_payload()
            apply_payload = {
                "status": "apply_requested",
                "setup_id": self._setup_current_setup_id,
                "schema_version": 1,
                "approved_at": utc_now_iso(),
                "approved_preview_fingerprint": self._setup_current_preview_fingerprint,
                "executor": self._setup_effective_executor(form_payload),
            }
            self._setup_write_json(self._setup_paths()["apply"], apply_payload)
            self._setup_current_apply_payload = apply_payload
            self._setup_current_result_payload = None
            self._setup_execute_apply_roundtrip(
                apply_payload,
                form_payload,
                self._setup_current_preview_payload,
                self._setup_current_draft_fingerprint,
            )
            self._refresh_setup_mode_state()
            self._set_toast_style("progress")
            self.msg_var.set("설정 적용을 요청했습니다")
            self._clear_msg_later()
        except Exception as exc:
            self._set_toast_style("error")
            self.msg_var.set(f"적용 요청 실패: {exc}")
            self._clear_msg_later(10000)

    def _on_setup_confirm_restart(self) -> None:
        if self._setup_mode_state != "Applied" or not self._setup_restart_required:
            return
        if not self._ask_yn(
            "파이프라인 재시작",
            "새 active 설정을 반영하려면 watcher/launcher를 재시작해야 합니다. 지금 재시작하시겠습니까?",
            icon="question",
        ):
            return
        self._on_restart()

    def _open_setup_mode(self) -> None:
        if self._mode != "setup":
            self._switch_mode("setup")
            threading.Thread(target=self._run_setup_check_silent, daemon=True).start()
            return
        self._on_setup_check()

    def _set_main_button_states(
        self,
        *,
        all_disabled: bool,
        can_start: bool = False,
        can_restart: bool | None = None,
        session_ok: bool = False,
    ) -> None:
        if all_disabled:
            self.btn_setup.configure(state=DISABLED)
            self.btn_start.configure(state=DISABLED)
            self.btn_stop.configure(state=DISABLED)
            self.btn_restart.configure(state=DISABLED)
            self.btn_attach.configure(state=DISABLED)
            self.btn_token_backfill.configure(state=DISABLED)
            self.btn_token_rebuild.configure(state=DISABLED)
            return
        restart_enabled = session_ok if can_restart is None else can_restart
        self.btn_setup.configure(state=NORMAL)
        self.btn_start.configure(state=NORMAL if can_start else DISABLED)
        self.btn_stop.configure(state=NORMAL if session_ok else DISABLED)
        self.btn_restart.configure(state=NORMAL if restart_enabled else DISABLED)
        self.btn_attach.configure(state=NORMAL if session_ok else DISABLED)
        self.btn_token_backfill.configure(state=NORMAL)
        self.btn_token_rebuild.configure(state=NORMAL)

    # ── 제어 ──

    def _on_toast_change(self, *_args: object) -> None:
        """Toast 텍스트 변경 시 표시/숨김 전환."""
        text = self.msg_var.get().strip()
        if text:
            self.msg_label.place(relx=0.5, rely=0.0, anchor="n", y=4)
            self.msg_label.lift()
        else:
            self.msg_label.place_forget()

    def _set_toast_style(self, level: str) -> None:
        """Toast 색상을 level에 따라 설정."""
        if level == "progress":
            self.msg_label.configure(bg="#141830", fg="#7090d0")
        elif level == "success":
            self.msg_label.configure(bg="#0a2a18", fg="#4ade80")
        elif level == "error":
            self.msg_label.configure(bg="#2a1015", fg="#f87171")
        else:
            self.msg_label.configure(bg="#141830", fg="#7090d0")

    def _lock_buttons(self, label: str) -> None:
        self._action_in_progress = True
        self._set_toast_style("progress")
        self.msg_var.set(label)
        if hasattr(self, "_setup_mode_state_var"):
            self._refresh_setup_mode_state()

    def _unlock_buttons(self, msg: str, is_error: bool = False) -> None:
        self._action_in_progress = False
        self._set_toast_style("error" if is_error else "success")
        self.msg_var.set(msg)
        if hasattr(self, "_setup_mode_state_var"):
            self._refresh_setup_mode_state()

    def _set_token_action_text(self, text: str) -> None:
        if hasattr(self, "_token_action_var"):
            self._token_action_var.set(text)

    def _update_token_action_progress(self, action_label: str, payload: dict[str, object]) -> None:
        phase = str(payload.get("phase") or "scanning")
        phase_display = {
            "scanning": "스캔 중",
            "parsing": "파싱 중",
            "stopping_collector": "collector 중지 중",
            "starting_collector": "collector 시작 중",
            "rebuilding": "재구성 중",
        }.get(phase, phase.replace("_", " "))
        elapsed = float(payload.get("elapsed_sec") or 0.0)
        scanned_files = int(payload.get("scanned_files") or 0)
        parsed_files = int(payload.get("parsed_files") or 0)
        total_files = int(payload.get("total_files") or 0)
        progress_percent = int(payload.get("progress_percent") or 0)
        inserted = int(payload.get("usage_inserted") or 0) + int(payload.get("pipeline_inserted") or 0)
        duplicates = int(payload.get("duplicates") or 0)
        retry_later = int(payload.get("retry_later") or 0)
        text = (
            f"작업: {action_label} · {progress_percent}% · {phase_display} · {elapsed:.1f}초"
            f" · 스캔 {scanned_files}/{total_files or scanned_files} · 파싱 {parsed_files}"
            f" · 적재 {self._fmt_count(inserted)} · 중복 {self._fmt_count(duplicates)}"
        )
        if retry_later:
            text += f" · 재시도 {retry_later}"
        self._set_token_action_text(text)

    def _token_progress_callback(self, action_label: str):
        def _callback(payload: dict[str, object]) -> None:
            self._enqueue_token_ui(
                lambda p=dict(payload), a=action_label: self._update_token_action_progress(a, p)
            )
        return _callback

    def _enqueue_token_ui(self, callback) -> None:
        self._token_ui_queue.put(callback)

    def _start_token_ui_pump(self) -> None:
        if self._token_ui_after_id is None:
            self._token_ui_after_id = self.root.after(50, self._drain_token_ui_queue)

    def _drain_token_ui_queue(self) -> None:
        self._token_ui_after_id = None
        while True:
            try:
                callback = self._token_ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback()
            except Exception:
                continue
        if self._action_in_progress or not self._token_ui_queue.empty():
            self._token_ui_after_id = self.root.after(50, self._drain_token_ui_queue)

    def _format_token_action_done(
        self,
        action_label: str,
        summary: dict[str, object],
        *,
        backup_path: str = "",
    ) -> str:
        elapsed = float(summary.get("elapsed_sec") or 0.0)
        scanned_files = int(summary.get("scanned_files") or 0)
        parsed_files = int(summary.get("parsed_files") or 0)
        total_files = int(summary.get("total_files") or 0)
        progress_percent = int(summary.get("progress_percent") or 100)
        inserted = int(summary.get("usage_inserted") or 0) + int(summary.get("pipeline_inserted") or 0)
        duplicates = int(summary.get("duplicates") or 0)
        retry_later = int(summary.get("retry_later") or 0)
        text = (
            f"작업: {action_label} · {progress_percent}% · 대기 · {elapsed:.1f}초"
            f" · 스캔 {scanned_files}/{total_files or scanned_files} · 파싱 {parsed_files}"
            f" · 적재 {self._fmt_count(inserted)} · 중복 {self._fmt_count(duplicates)}"
        )
        if retry_later:
            text += f" · 재시도 {retry_later}"
        if backup_path:
            text += f" · 백업 {Path(backup_path).name}"
        return text

    def _clear_msg_later(self, delay_ms: int | None = 6000) -> None:
        if delay_ms is None:
            return
        self.root.after(delay_ms, lambda: self.msg_var.set("") if not self._action_in_progress else None)

    # ── Setup state ──

    def _setup_state_presentation(self, resolved: dict[str, object] | None = None) -> tuple[str, str]:
        state = self._setup_state
        detail = self._setup_state_detail
        if state == "ready":
            text = "설정: ● 준비됨"
            color = "#34d399"
        elif state == "ready_warn":
            text = f"설정: ● 준비됨 ({detail})"
            color = "#f59e0b"
        elif state == "checking":
            text = f"설정: … {detail or '점검 중'}"
            color = "#f59e0b"
        elif state == "missing":
            text = f"설정: ■ 누락 {detail}"
            color = "#ef4444"
        elif state == "failed":
            text = f"설정: ■ {detail or '설치 실패'}"
            color = "#ef4444"
        else:
            text = "설정: — 알 수 없음"
            color = "#888888"

        if state not in {"ready", "ready_warn"} or not resolved:
            return text, color

        controls = dict(resolved.get("controls") or {})
        support_level = str(resolved.get("support_level") or "")
        runtime_detail = self._runtime_resolution_detail(resolved) or join_display_resolver_messages(resolved)
        if not bool(controls.get("launch_allowed")):
            suffix = "실행 차단"
            if runtime_detail:
                suffix = f"{suffix}: {runtime_detail}"
            return f"{text} / {suffix}", "#ef4444"
        if support_level == "experimental":
            suffix = "실험적"
            if runtime_detail:
                suffix = f"{suffix}: {runtime_detail}"
            return f"{text} / {suffix}", "#f59e0b"
        return text, color

    def _apply_setup_state_presentation(self, resolved: dict[str, object] | None = None) -> None:
        if not hasattr(self, "setup_var") or not hasattr(self, "setup_state_label"):
            return
        text, color = self._setup_state_presentation(resolved)
        self.setup_var.set(text)
        self.setup_state_label.configure(fg=color)

    def _set_setup_state(self, state: str, detail: str = "") -> None:
        """Setup 상태 UI를 갱신합니다. main thread에서 호출해야 합니다."""
        self._setup_state = state
        self._setup_state_detail = detail
        self._apply_setup_state_presentation(self._runtime_launch_resolution)
        self._sync_start_button_state()

    def _sync_start_button_state(self) -> None:
        """Setup 상태에 따라 Start 버튼 활성/비활성."""
        if self._action_in_progress:
            return
        resolved = self._resolve_runtime_active_profile()
        self._apply_runtime_launch_presentation(resolved)
        self._apply_setup_state_presentation(resolved)
        session_ok = False
        if self._last_snapshot is not None:
            session_ok = bool(self._last_snapshot.get("session_ok"))
        elif hasattr(self, "_session_name"):
            session_ok = tmux_alive(self._session_name)
        can_launch = self._runtime_launch_allowed(resolved)
        if hasattr(self, "btn_start"):
            self.btn_start.configure(state=NORMAL if (not session_ok and can_launch) else DISABLED)
        if hasattr(self, "btn_restart"):
            self.btn_restart.configure(state=NORMAL if (session_ok and can_launch) else DISABLED)

    def _msg(self, text: str) -> None:
        """Background thread에서 안전하게 하단 메시지 갱신."""
        self.root.after(0, lambda: self.msg_var.set(text))

    def _ask_yn(self, title: str, msg: str, icon: str = "warning") -> bool:
        """현재 thread 문맥에 맞춰 yes/no dialog를 안전하게 표시합니다."""
        if threading.current_thread() is threading.main_thread():
            return bool(messagebox.askyesno(title, msg, icon=icon))
        result: list[bool | None] = [None]

        def _ask() -> None:
            result[0] = messagebox.askyesno(title, msg, icon=icon)

        self.root.after(0, _ask)
        deadline = time.time() + 30.0
        while result[0] is None and time.time() < deadline:
            time.sleep(0.1)
        if result[0] is None:
            return False
        return bool(result[0])

    # ── Setup/Check ──

    def _run_setup_check_silent(self) -> None:
        """앱 시작 시 자동 점검 — dialog 없이 상태만 갱신."""
        self.root.after(0, lambda: self._set_setup_state("checking"))
        total = len(_HARD_BLOCKERS) + len(_SOFT_WARNINGS)
        step = 0

        # Hard blockers
        missing_hard: list[tuple[str, str]] = []
        for label, check_type, target, hint in _HARD_BLOCKERS:
            step += 1
            self.root.after(0, lambda n=label, s=step: self._set_setup_state(
                "checking", f"({s}/{total}) {n}"))
            try:
                if check_type == "cli":
                    ok = _find_cli_bin(target)
                elif check_type == "launcher_file":
                    ok = _file_exists(APP_ROOT, target)
                elif check_type == "repo_file":
                    ok = _file_exists(self.project, target)
                else:
                    ok = True
            except Exception:
                ok = False
            if not ok:
                missing_hard.append((label, hint))

        if missing_hard:
            names = ", ".join(n for n, _ in missing_hard)
            self.root.after(0, lambda: self._set_setup_state("missing", names))
            return

        # Soft warnings
        warns: list[str] = []
        for label, check_type, target in _SOFT_WARNINGS:
            step += 1
            self.root.after(0, lambda n=label, s=step: self._set_setup_state(
                "checking", f"({s}/{total}) {n}"))
            try:
                if check_type == "launcher_file":
                    ok = _file_exists(APP_ROOT, target)
                elif check_type == "repo_file":
                    ok = _file_exists(self.project, target)
                else:
                    ok = True
            except Exception:
                ok = True  # soft — assume ok on error
            if not ok:
                warns.append(label)

        if warns:
            detail = ", ".join(warns) + " 없음"
            self.root.after(0, lambda: self._set_setup_state("ready_warn", detail))
        else:
            self.root.after(0, lambda: self._set_setup_state("ready"))

    def _on_setup_check(self) -> None:
        """Setup/Check 버튼 — 점검 + 설치 제안."""
        if self._action_in_progress:
            return
        self._lock_buttons("⚙ 실행 전제를 점검하는 중...")
        threading.Thread(target=self._do_setup_check, daemon=True).start()

    def _do_setup_check(self) -> None:
        """Hard blocker + soft warning 점검 → 누락 guide 승인 생성 → 설치 제안."""
        total = len(_HARD_BLOCKERS) + len(_SOFT_WARNINGS)
        step = 0

        # ── 1. Hard blockers 점검 ──
        missing_hard: list[tuple[str, str]] = []
        for label, check_type, target, hint in _HARD_BLOCKERS:
            step += 1
            self._msg(f"⚙ 점검 ({step}/{total}) {label}...")
            self.root.after(0, lambda n=label, s=step: self._set_setup_state(
                "checking", f"({s}/{total}) {n}"))
            try:
                if check_type == "cli":
                    ok = _find_cli_bin(target)
                elif check_type == "launcher_file":
                    ok = _file_exists(APP_ROOT, target)
                elif check_type == "repo_file":
                    ok = _file_exists(self.project, target)
                else:
                    ok = True
            except Exception:
                ok = False
            if not ok:
                missing_hard.append((label, hint))

        # ── 2. Soft warnings 점검 ──
        warns: list[str] = []
        for label, check_type, target in _SOFT_WARNINGS:
            step += 1
            self._msg(f"⚙ 점검 ({step}/{total}) {label}...")
            try:
                if check_type == "launcher_file":
                    ok = _file_exists(APP_ROOT, target)
                elif check_type == "repo_file":
                    ok = _file_exists(self.project, target)
                else:
                    ok = True
            except Exception:
                ok = True
            if not ok:
                warns.append(label)

        # ── 3. Missing guide 파일 승인 생성 (2순위) ──
        missing_guides = _check_missing_guides(self.project)
        if missing_guides:
            guide_list = ", ".join(missing_guides)
            if self._ask_yn(
                "가이드 파일 누락",
                f"target repo에 다음 guide 파일이 없습니다:\n\n"
                f"  {guide_list}\n\n"
                f"기본 템플릿을 생성할까요?\n(기존 파일은 덮어쓰지 않습니다)",
                icon="question",
            ):
                created: list[str] = []
                failed: list[str] = []
                for name, content in _GUIDE_TEMPLATES:
                    if name in missing_guides:
                        self._msg(f"⚙ 생성 중: {name}...")
                        if _create_guide_file(self.project, name, content):
                            created.append(name)
                        else:
                            failed.append(name)
                if created:
                    self._msg(f"⚙ 가이드 생성 완료: {', '.join(created)}")
                if failed:
                    self._msg(f"⚙ 가이드 생성 실패: {', '.join(failed)}")
                # AGENTS.md가 hard blocker이므로 재점검
                missing_hard = [(l, h) for l, h in missing_hard if not _file_exists(
                    self.project if l == "AGENTS.md" else APP_ROOT,
                    next((t for la, _, t, _ in _HARD_BLOCKERS if la == l), l))]

        # ── 4. Hard blocker 결과 처리 ──
        installable = [(n, h) for n, h in missing_hard if h]
        non_installable = [(n, h) for n, h in missing_hard if not h]

        if non_installable:
            names = ", ".join(n for n, _ in non_installable)
            self.root.after(0, lambda: self._set_setup_state("missing", names))
            self.root.after(0, lambda: self._unlock_buttons(
                f"⚙ 누락 항목 있음 (수동 확인 필요): {names}", is_error=True))
            self.root.after(0, lambda: self._clear_msg_later(10000))
            return

        if not installable:
            # 모든 hard blocker OK
            if warns:
                detail = ", ".join(warns) + " 없음"
                self.root.after(0, lambda: self._set_setup_state("ready_warn", detail))
            else:
                self.root.after(0, lambda: self._set_setup_state("ready"))
            self.root.after(0, lambda: self._unlock_buttons("⚙ 설정 점검 완료"))
            self.root.after(0, lambda: self._clear_msg_later())
            return

        # ── 5. 설치 가능한 hard blocker → 설치 제안 ──
        names = ", ".join(n for n, _ in installable)
        self.root.after(0, lambda: self._set_setup_state("missing", names))
        hints = "\n".join(f"  • {n}: {h}" for n, h in installable)
        if not self._ask_yn(
            "의존성 누락",
            f"다음 실행 전제가 WSL에 없습니다:\n\n{hints}\n\n설치를 시도할까요?",
        ):
            self.root.after(0, lambda: self._unlock_buttons(
                f"⚙ 설정 누락: {names}", is_error=True))
            self.root.after(0, lambda: self._clear_msg_later(8000))
            return

        # ── 6. 설치 진행 ──
        install_failures: list[str] = []
        for i, (name, hint) in enumerate(installable, 1):
            self._msg(f"⚙ 설치 ({i}/{len(installable)}) {name}...")
            code, output = _run(["bash", "-c", hint], timeout=120.0)
            if code != 0:
                install_failures.append(f"{name}: {output[:80]}" if output else name)

        if install_failures:
            fail_text = "\n".join(install_failures)
            def _show_fail() -> None:
                self._set_setup_state("failed", "Install failed")
                messagebox.showerror(
                    "설치 실패",
                    f"설치 실패:\n\n{fail_text}\n\n수동으로 설치한 뒤 설정 버튼을 다시 눌러 재확인하세요.",
                )
                self._unlock_buttons("⚙ 설치 실패", is_error=True)
                self._clear_msg_later(10000)
            self.root.after(0, _show_fail)
            return

        # ── 7. 설치 성공 ──
        if warns:
            detail = ", ".join(warns) + " 없음"
            self.root.after(0, lambda: self._set_setup_state("ready_warn", detail))
        else:
            self.root.after(0, lambda: self._set_setup_state("ready"))

        if self._ask_yn(
            "설정 완료",
            "설치가 완료되었습니다.\n지금 파이프라인을 실행하시겠습니까?",
            icon="info",
        ):
            self._msg("▶ 시작 중...")
            self.root.after(0, lambda: self._unlock_buttons(""))
            self._do_start()
        else:
            self.root.after(0, lambda: self._unlock_buttons("⚙ 설정 완료 — 시작 준비됨"))
            self.root.after(0, lambda: self._clear_msg_later(8000))

    # ── Start (setup ready일 때만) ──

    def _on_start(self) -> None:
        if self._action_in_progress:
            return
        if self._setup_state not in ("ready", "ready_warn"):
            self._set_toast_style("error")
            self.msg_var.set("설정이 완료되지 않았습니다. 먼저 설정 화면에서 실행 전제를 확인하세요.")
            self._clear_msg_later(5000)
            return
        launch_resolution = self._resolve_runtime_active_profile()
        self._apply_runtime_launch_presentation(launch_resolution)
        if not self._runtime_launch_allowed(launch_resolution):
            self._set_toast_style("error")
            self.msg_var.set(self._runtime_resolution_detail(launch_resolution) or "Active profile launch is blocked.")
            self._clear_msg_later(8000)
            return
        self._lock_buttons("▶ 파이프라인 시작 중...")
        threading.Thread(target=self._do_start, daemon=True).start()

    def _do_start(self) -> None:
        try:
            # Pre-check: launcher script 접근 가능 여부
            try:
                script = resolve_project_runtime_file(self.project, "start-pipeline.sh")
            except FileNotFoundError:
                self.root.after(0, lambda: self._unlock_buttons(
                    "▶ 시작 실패: start-pipeline.sh를 찾지 못했습니다", is_error=True))
                self.root.after(0, lambda: self._clear_msg_later(10000))
                return
            if IS_WINDOWS:
                wsl_script = _windows_to_wsl_mount(script)
                code, _ = _run(["test", "-f", wsl_script], timeout=5.0)
                if code != 0:
                    self.root.after(0, lambda: self._unlock_buttons(
                        f"▶ 시작 실패: WSL에서 {wsl_script}에 접근할 수 없습니다", is_error=True))
                    self.root.after(0, lambda: self._clear_msg_later(10000))
                    return

            self.root.after(0, lambda: self.msg_var.set("▶ 파이프라인 시작 중..."))
            start_requested_at = time.time()
            start_result = pipeline_start(self.project, self._session_name)
            if start_result != "시작 요청됨":
                self.root.after(0, lambda msg=start_result: self._unlock_buttons(f"▶ 시작 차단: {msg}", is_error=True))
                self.root.after(0, lambda: self._clear_msg_later(10000))
                return

            ok, detail = confirm_pipeline_start(
                self.project,
                self._session_name,
                start_requested_at=start_requested_at,
                action_label="시작",
                progress_callback=lambda message: self.root.after(
                    0,
                    lambda m=message: self.msg_var.set(f"▶ {m}"),
                ),
            )
            self.root.after(0, lambda d=detail, success=ok: self._unlock_buttons(f"▶ {d}", is_error=not success))
            self.root.after(0, lambda: self._clear_msg_later(10000 if not ok else None))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"▶ 시작 실패: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later(10000))

    def _on_stop(self) -> None:
        if self._action_in_progress:
            return
        self._lock_buttons("■ 파이프라인 중지 중...")
        threading.Thread(target=self._do_stop, daemon=True).start()

    def _do_stop(self) -> None:
        try:
            pipeline_stop(self.project, self._session_name)
            for sec in range(5):
                time.sleep(1)
                session_alive = tmux_alive(self._session_name)
                collector_alive, _collector_pid = token_collector_alive(self.project)
                if not session_alive and not collector_alive:
                    self.root.after(0, lambda: self._unlock_buttons("■ 중지 완료"))
                    self.root.after(0, lambda: self._clear_msg_later())
                    return
                self.root.after(0, lambda s=sec: self.msg_var.set(
                    f"■ 중지 중... ({s+1}초)"))
            remaining = []
            if tmux_alive(self._session_name):
                remaining.append("tmux 세션")
            collector_alive, _collector_pid = token_collector_alive(self.project)
            if collector_alive:
                remaining.append("token collector")
            detail = ", ".join(remaining) if remaining else "프로세스"
            self.root.after(0, lambda d=detail: self._unlock_buttons(
                f"■ 중지 불완전: 아직 {d}가 감지됩니다",
                is_error=True,
            ))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"■ 중지 실패: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later())

    def _on_restart(self) -> None:
        if self._action_in_progress:
            return
        if self._setup_state not in ("ready", "ready_warn"):
            self._set_toast_style("error")
            self.msg_var.set("설정이 완료되지 않았습니다. 먼저 설정 화면에서 실행 전제를 확인하세요.")
            self._clear_msg_later(5000)
            return
        launch_resolution = self._resolve_runtime_active_profile()
        self._apply_runtime_launch_presentation(launch_resolution)
        if not self._runtime_launch_allowed(launch_resolution):
            self._set_toast_style("error")
            self.msg_var.set(self._runtime_resolution_detail(launch_resolution) or "Active profile launch is blocked.")
            self._clear_msg_later(8000)
            return
        self._lock_buttons("↻ 파이프라인 재시작 중...")
        threading.Thread(target=self._do_restart, daemon=True).start()

    def _do_restart(self) -> None:
        try:
            # ── Stop 단계 ──
            self.root.after(0, lambda: self.msg_var.set("↻ 파이프라인 중지 중..."))
            pipeline_stop(self.project, self._session_name)
            # stop 확인 (최대 5초)
            for sec in range(5):
                time.sleep(1)
                if not tmux_alive(self._session_name):
                    break
                self.root.after(0, lambda s=sec: self.msg_var.set(
                    f"↻ 중지 중... ({s+2}초)"))
            if tmux_alive(self._session_name):
                self.root.after(0, lambda: self._unlock_buttons(
                    "↻ 재시작 실패: 기존 세션을 중지하지 못했습니다", is_error=True))
                self.root.after(0, lambda: self._clear_msg_later(10000))
                return
            self.root.after(0, lambda: self.msg_var.set("↻ 중지 완료 — 다시 시작하는 중..."))
            time.sleep(1)

            # ── Start 단계 (Start와 동일한 진단) ──
            start_requested_at = time.time()
            start_result = pipeline_start(self.project, self._session_name)
            if start_result != "시작 요청됨":
                self.root.after(0, lambda msg=start_result: self._unlock_buttons(f"↻ 재시작 차단: {msg}", is_error=True))
                self.root.after(0, lambda: self._clear_msg_later(10000))
                return
            ok, detail = confirm_pipeline_start(
                self.project,
                self._session_name,
                start_requested_at=start_requested_at,
                action_label="재시작",
                progress_callback=lambda message: self.root.after(
                    0,
                    lambda m=message: self.msg_var.set(f"↻ {m}"),
                ),
            )
            self.root.after(0, lambda d=detail, success=ok: self._unlock_buttons(f"↻ {d}", is_error=not success))
            self.root.after(0, lambda: self._clear_msg_later(10000 if not ok else None))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"↻ 재시작 실패: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later(10000))

    def _on_attach(self) -> None:
        if tmux_alive(self._session_name):
            tmux_attach(self._session_name)
            self._set_toast_style("success")
            self.msg_var.set("tmux attach 실행됨")
            self._clear_msg_later()
        else:
            self._set_toast_style("error")
            self.msg_var.set("tmux 세션이 없습니다. 먼저 Start하세요.")
            self._clear_msg_later()

    def _token_action_initial_payload(self) -> dict[str, object]:
        return {
            "phase": "preparing",
            "elapsed_sec": 0.0,
            "scanned_files": 0,
            "parsed_files": 0,
            "total_files": 0,
            "progress_percent": 0,
            "usage_inserted": 0,
            "pipeline_inserted": 0,
            "duplicates": 0,
            "retry_later": 0,
        }

    def _start_token_maintenance_action(
        self,
        *,
        action_label: str,
        dialog_title: str,
        dialog_message: str,
        icon: str,
        lock_message: str,
        worker_target,
    ) -> None:
        if self._action_in_progress:
            return
        if not self._ask_yn(dialog_title, dialog_message, icon=icon):
            return
        self._lock_buttons(lock_message)
        self._update_token_action_progress(action_label, self._token_action_initial_payload())
        self._start_token_ui_pump()
        threading.Thread(target=worker_target, daemon=True).start()

    def _run_token_maintenance_action(
        self,
        *,
        action_label: str,
        action_runner,
        unlock_message_builder,
        error_message: str,
    ) -> None:
        try:
            result = action_runner()
            summary = dict(result.get("summary") or {})
            backup_path = str(result.get("backup_path") or "")
            done_text = self._format_token_action_done(action_label, summary, backup_path=backup_path)
            self._enqueue_token_ui(lambda text=done_text: self._set_token_action_text(text))
            self._enqueue_token_ui(self._refresh_token_dashboard_async)
            self._enqueue_token_ui(lambda: self._start_token_usage_refresh(force=True))
            unlock_message = unlock_message_builder(summary, backup_path)
            self._enqueue_token_ui(lambda text=unlock_message: self._unlock_buttons(text))
        except Exception as e:
            err = str(e)
            self._enqueue_token_ui(
                lambda text=f"작업: {action_label} · 오류 · {err}": self._set_token_action_text(text)
            )
            self._enqueue_token_ui(lambda text=f"{error_message}: {err}": self._unlock_buttons(text, is_error=True))
        self._enqueue_token_ui(lambda: self._clear_msg_later(10000))

    def _on_token_backfill(self) -> None:
        self._start_token_maintenance_action(
            action_label="전체 히스토리",
            dialog_title="전체 히스토리 보강",
            dialog_message=(
                "기존 usage.db를 유지한 채 전체 히스토리를 추가로 채웁니다.\n"
                "중복은 dedup로 막고, 실행 중 collector가 있으면 잠시 멈췄다가 다시 시작합니다.\n\n"
                "계속하시겠습니까?"
            ),
            icon="question",
            lock_message="토큰: 전체 히스토리 보강 중...",
            worker_target=self._do_token_backfill,
        )

    def _do_token_backfill(self) -> None:
        self._run_token_maintenance_action(
            action_label="전체 히스토리",
            action_runner=lambda: backfill_token_history(
                self.project,
                progress_callback=self._token_progress_callback("전체 히스토리"),
            ),
            unlock_message_builder=lambda summary, _backup_path: (
                f"토큰: 전체 히스토리 보강 완료 "
                f"({float(summary.get('elapsed_sec') or 0.0):.1f}s, "
                f"{self._fmt_count(int(summary.get('usage_inserted') or 0))} usage)"
            ),
            error_message="토큰: 히스토리 보강 실패",
        )

    def _on_token_rebuild(self) -> None:
        self._start_token_maintenance_action(
            action_label="DB 재구성",
            dialog_title="토큰 DB 재구성",
            dialog_message=(
                "임시 DB로 전체 스캔을 다시 수행한 뒤, 성공 시 기존 usage.db를 backup으로 남기고 교체합니다.\n"
                "실패하면 현재 usage.db는 유지됩니다.\n"
                "실행 중 collector가 있으면 잠시 멈췄다가 다시 시작합니다.\n\n"
                "계속하시겠습니까?"
            ),
            icon="warning",
            lock_message="토큰: usage DB 재구성 중...",
            worker_target=self._do_token_rebuild,
        )

    def _do_token_rebuild(self) -> None:
        self._run_token_maintenance_action(
            action_label="DB 재구성",
            action_runner=lambda: rebuild_token_db(
                self.project,
                progress_callback=self._token_progress_callback("DB 재구성"),
            ),
            unlock_message_builder=lambda summary, backup_path: (
                f"토큰: DB 재구성 완료 ({float(summary.get('elapsed_sec') or 0.0):.1f}초)"
                f"{f' · 백업 {Path(backup_path).name}' if backup_path else ''}"
            ),
            error_message="토큰: DB 재구성 실패",
        )

    # ── 실행 ──

    def run(self) -> None:
        self.root.mainloop()
