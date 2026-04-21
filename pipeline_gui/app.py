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

from pipeline_runtime.lane_catalog import (
    default_role_bindings,
    default_selected_agent,
    lane_support_rank_map,
    physical_lane_order,
)
from .formatting import format_compact_count
from .platform import (
    IS_WINDOWS, APP_ROOT, TMUX_QUERY_TIMEOUT, WSL_DISTRO,
    resolve_project_runtime_file,
    _wsl_path_str, _windows_to_wsl_mount, _normalize_picked_path, _run,
    read_json_path,
)
from .project import (
    _load_recent_projects, _save_project_path,
    resolve_project_root, validate_project_root, bootstrap_project_root,
    _session_name_for,
)
from .backend import (
    pipeline_start, pipeline_stop, token_collector_alive,
    confirm_pipeline_start,
    runtime_attach, runtime_state,
    backfill_token_history, rebuild_token_db,
)
from .home_controller import HomeController
from .home_presenter import (
    build_agent_card_presentations,
    build_console_presentation,
    build_control_presentation,
    build_empty_agent_card_presentation,
)
from .agents import (
    format_elapsed,
)
from .setup import (
    _HARD_BLOCKERS, _SOFT_WARNINGS,
    _find_cli_bin, _file_exists,
    _check_hard_blockers, _check_soft_warnings,
    _check_missing_guides, _create_guide_file, _GUIDE_TEMPLATES,
)
from .setup_controller import SetupController
from .setup_models import RuntimeLaunchPresentation, SetupActionState, SetupStatusPresentation
from .setup_presenter import (
    build_setup_action_buttons,
    build_setup_detail_presentation,
    build_setup_fast_presentation,
    build_setup_inline_errors,
    format_setup_state_label,
)
from .view import (
    BG, FG, ACCENT, SUB_FG, BTN_BG, BTN_FG,
    CARD_BG, CARD_BORDER, LOG_BG, HEADER_BG, AGENT_CARD_BG,
    POLL_MS, init_ttk_style, create_fonts, make_card, lighten,
    build_header, build_project_bar, build_control_bar,
    build_status_panels, build_agent_cards, build_token_panel, build_console_panels, build_setup_panels,
)
from .guide import DEFAULT_GUIDE
from .token_presenter import build_token_panel_presentation
from .setup_executor import LocalSetupExecutorAdapter
from storage.json_store_base import utc_now_iso

_SETUP_AGENT_ORDER = physical_lane_order()
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
_SETUP_AGENT_SUPPORT_RANK = lane_support_rank_map()
_SETUP_DEFAULT_APPLY_RESULT_MESSAGE = "설정 적용 결과가 도착했습니다."
_SETUP_DETAIL_PENDING_TEXT = "갱신 중..."


class PipelineGUI:
    def __init__(self, project: Path) -> None:
        self.project = project
        self._session_name = _session_name_for(project)
        self.selected_agent = default_selected_agent()
        self._auto_focus_agent = True
        self._poll_in_flight = False
        self._last_snapshot: dict[str, object] | None = None
        self._last_poll_at: float | None = None
        self._working_since: dict[str, float] = {}  # agent label → epoch when WORKING started
        self._poll_after_id: str | None = None
        self._tick_after_id: str | None = None
        self._validate_after_id: str | None = None
        self._setup_refresh_after_id: str | None = None
        self._setup_detail_after_id: str | None = None
        self._token_ui_after_id: str | None = None
        self._token_ui_queue: queue.Queue[callable] = queue.Queue()
        self._setup_snapshot_refresh_last_at: float = 0.0
        self._setup_snapshot_refresh_ttl_sec: float = 2.0
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
        self._apply_setup_fast_snapshot(self._build_setup_fast_snapshot())

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
        self._setup_executor_adapter = LocalSetupExecutorAdapter()
        self._setup_state_model = SetupActionState()
        self._setup_controller = SetupController(
            self.project,
            executor_adapter=self._setup_executor_adapter,
            agent_order=_SETUP_AGENT_ORDER,
            agent_support_rank=_SETUP_AGENT_SUPPORT_RANK,
            default_apply_result_message=_SETUP_DEFAULT_APPLY_RESULT_MESSAGE,
            detail_pending_text=_SETUP_DETAIL_PENDING_TEXT,
        )
        self._home_controller = HomeController(self.project, self._session_name)
        self._setup_refresh_generation = 0

        self._setup_agent_vars = {
            name: BooleanVar(value=True) for name in _SETUP_AGENT_ORDER
        }
        default_bindings = default_role_bindings()
        self._setup_implement_var = StringVar(value=default_bindings["implement"])
        self._setup_verify_var = StringVar(value=default_bindings["verify"])
        self._setup_advisory_var = StringVar(value=default_bindings["advisory"])
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
        self._setup_mode_state_var = StringVar(value=format_setup_state_label("DraftOnly"))
        self._setup_support_level_var = StringVar(value="확인 중")
        self._setup_runtime_profile_var = StringVar(value="실행 프로필: 확인 중")
        self._setup_validation_var = StringVar(value="유효성 문제 없음.")
        self._setup_preview_summary_var = StringVar(value="생성된 미리보기 없음.")
        self._setup_current_setup_id_var = StringVar(value="—")
        self._setup_current_preview_fingerprint_var = StringVar(value="—")
        self._setup_apply_readiness_var = StringVar(value="적용 비활성: 먼저 미리보기를 생성하세요")
        self._setup_restart_notice_var = StringVar(value="")
        self._setup_cleanup_summary_var = StringVar(value="아직 정리 기록이 없습니다.")
        self._runtime_launch_var = StringVar(value="실행 프로필: 확인 중")

    def _ensure_home_controller(self) -> HomeController:
        controller = getattr(self, "_home_controller", None)
        project = getattr(self, "project", Path("."))
        session_name = getattr(self, "_session_name", "aip-projectH")
        if controller is None:
            controller = HomeController(project, session_name)
            self._home_controller = controller
        controller.set_project(project)
        controller.set_session_name(session_name)
        return controller

    def _ensure_setup_controller(self) -> SetupController:
        controller = getattr(self, "_setup_controller", None)
        project = getattr(self, "project", Path("."))
        executor_adapter = getattr(self, "_setup_executor_adapter", None) or LocalSetupExecutorAdapter()
        self._setup_executor_adapter = executor_adapter
        if controller is None:
            controller = SetupController(
                project,
                executor_adapter=executor_adapter,
                agent_order=_SETUP_AGENT_ORDER,
                agent_support_rank=_SETUP_AGENT_SUPPORT_RANK,
                default_apply_result_message=_SETUP_DEFAULT_APPLY_RESULT_MESSAGE,
                detail_pending_text=_SETUP_DETAIL_PENDING_TEXT,
            )
            self._setup_controller = controller
        controller.set_project(project)
        controller.set_executor_adapter(executor_adapter)
        return controller

    def _export_setup_state(self) -> SetupActionState:
        state = getattr(self, "_setup_state_model", None)
        if state is None:
            state = SetupActionState()
            self._setup_state_model = state
        return state

    def _apply_setup_state_model(self, state: SetupActionState) -> None:
        self._setup_state_model = state

    def _update_setup_state(self, **updates: object) -> SetupActionState:
        state = self._export_setup_state()
        for key, value in updates.items():
            setattr(state, key, value)
        self._apply_setup_state_model(state)
        return state

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

    _prev_focus_text: str = ""
    _prev_log_text: str = ""

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

    def _set_var_if_changed(self, var: object, new_value: str) -> None:
        getter = getattr(var, "get", None)
        setter = getattr(var, "set", None)
        if setter is None:
            return
        current = None
        if callable(getter):
            try:
                current = getter()
            except Exception:
                current = None
        if current == new_value:
            return
        setter(new_value)

    def _configure_widget_if_changed(self, widget: object, **kwargs: object) -> None:
        configure = getattr(widget, "configure", None)
        if configure is None:
            return
        cache = dict(getattr(widget, "_projecth_last_config", {}) or {})
        changed = {key: value for key, value in kwargs.items() if cache.get(key) != value}
        if not changed:
            return
        configure(**changed)
        cache.update(changed)
        setattr(widget, "_projecth_last_config", cache)

    def _get_cached_token_usage(self) -> dict[str, dict[str, object]]:
        controller = self._ensure_home_controller()
        return controller.get_cached_token_usage(on_refresh=self._queue_token_usage_refresh)

    def _start_token_usage_refresh(self, *, force: bool = False) -> None:
        controller = self._ensure_home_controller()
        controller.start_token_usage_refresh(
            on_refresh=self._queue_token_usage_refresh,
            force=force,
        )

    def _token_usage_refresh_worker(self, project: Path, project_key: str) -> None:
        self._ensure_home_controller().start_token_usage_refresh(
            on_refresh=self._queue_token_usage_refresh,
            force=True,
        )

    def _queue_token_usage_refresh(self, project_key: str, result: dict[str, dict[str, object]]) -> None:
        try:
            self.root.after(0, lambda: self._apply_token_usage_cache(project_key, result))
        except Exception:
            pass

    def _apply_token_usage_cache(self, project_key: str, result: dict[str, dict[str, object]]) -> None:
        if str(self.project) != project_key:
            return
        if self._last_snapshot is None:
            return
        if hasattr(self._last_snapshot, "updated"):
            snapshot = self._last_snapshot.updated(token_usage=result)
        else:
            snapshot = dict(self._last_snapshot)
            snapshot["token_usage"] = result
        self._apply_snapshot(snapshot)

    def _refresh_token_dashboard_async(self) -> None:
        self._start_token_dashboard_refresh(force=True)

    def _get_cached_token_dashboard(self) -> object | None:
        controller = self._ensure_home_controller()
        return controller.get_cached_token_dashboard(on_refresh=self._queue_token_dashboard_refresh)

    def _start_token_dashboard_refresh(self, *, force: bool = False) -> None:
        controller = self._ensure_home_controller()
        controller.start_token_dashboard_refresh(
            on_refresh=self._queue_token_dashboard_refresh,
            force=force,
        )

    def _queue_token_dashboard_refresh(self, project_key: str, dashboard: object | None) -> None:
        try:
            self.root.after(0, lambda: self._apply_token_dashboard_refresh(project_key, dashboard))
        except Exception:
            pass

    def _apply_token_dashboard_refresh(self, project_key: str, dashboard: object) -> None:
        if str(self.project) != project_key:
            return
        if self._last_snapshot is None:
            self._apply_token_dashboard(dashboard)
            return
        if hasattr(self._last_snapshot, "updated"):
            snapshot = self._last_snapshot.updated(token_dashboard=dashboard)
        else:
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
        for i, name in enumerate(_SETUP_AGENT_ORDER):
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
        if self._setup_refresh_after_id is not None:
            self.root.after_cancel(self._setup_refresh_after_id)
            self._setup_refresh_after_id = None
        if self._setup_detail_after_id is not None:
            self.root.after_cancel(self._setup_detail_after_id)
            self._setup_detail_after_id = None
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

    def _cancel_setup_refresh_callbacks(self) -> None:
        if not hasattr(self, "root"):
            return
        if self._setup_refresh_after_id is not None:
            self.root.after_cancel(self._setup_refresh_after_id)
            self._setup_refresh_after_id = None
        if self._setup_detail_after_id is not None:
            self.root.after_cancel(self._setup_detail_after_id)
            self._setup_detail_after_id = None

    def _invalidate_setup_refresh_generation(self) -> int:
        self._setup_refresh_generation = int(getattr(self, "_setup_refresh_generation", 0) or 0) + 1
        self._cancel_setup_refresh_callbacks()
        return self._setup_refresh_generation

    def _switch_mode(self, mode: str) -> None:
        """Home/Guide/Setup 모드 전환."""
        if mode == self._mode:
            return
        self._invalidate_setup_refresh_generation()
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
            self._apply_setup_fast_snapshot(self._build_setup_fast_snapshot())
            self._schedule_setup_detail_refresh(
                self._setup_refresh_generation,
                delay_ms=0,
                after_idle=True,
            )

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
            self._ensure_home_controller().set_project(new_path)
            self._ensure_home_controller().set_session_name(self._session_name)
            self._ensure_setup_controller().set_project(new_path)
            self._update_setup_state(runtime_launch_resolution=None)
            _save_project_path(new_path_str)
            self._refresh_recent_buttons()
            self._load_project_guide()
            self._setup_reset_cleanup_history()
            self._load_setup_form_from_disk()
            self._setup_cleanup_staged_files_once_on_startup()
            self._invalidate_setup_refresh_generation()
            self._apply_setup_fast_snapshot(self._build_setup_fast_snapshot())
            if getattr(self, "_mode", "home") == "setup":
                self._schedule_setup_detail_refresh(
                    self._setup_refresh_generation,
                    delay_ms=0,
                    after_idle=True,
                )
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
        controller = self._ensure_home_controller()
        snapshot = controller.build_snapshot(
            selected_agent=getattr(self, "selected_agent", default_selected_agent()),
            on_token_usage_refresh=self._queue_token_usage_refresh,
            on_token_dashboard_refresh=self._queue_token_dashboard_refresh,
        )
        return snapshot

    def _apply_snapshot(self, snapshot: dict[str, object]) -> None:
        self._last_snapshot = snapshot
        self._last_poll_at = float(snapshot.get("polled_at") or time.time())
        runtime_state_value = str(snapshot.get("runtime_state") or "STOPPED")
        session_ok = runtime_state_value != "STOPPED"
        w_alive = bool(snapshot["watcher_alive"])
        w_pid = snapshot["watcher_pid"]
        agents = snapshot["agents"]
        token_usage = snapshot.get("token_usage", {})
        token_dashboard = snapshot.get("token_dashboard")

        # Pipeline status
        if runtime_state_value == "RUNNING":
            self._set_var_if_changed(self.pipeline_var, "파이프라인: ● 실행 중")
            self._set_var_if_changed(self.status_var, "실행 중")
            self._configure_widget_if_changed(self.status_label, fg="#4ade80", bg="#0a2a18")
            self._configure_widget_if_changed(self.pipeline_state_label, fg="#4ade80")
        elif runtime_state_value == "STARTING":
            self._set_var_if_changed(self.pipeline_var, "파이프라인: ◐ 기동 중")
            self._set_var_if_changed(self.status_var, "기동 중")
            self._configure_widget_if_changed(self.status_label, fg="#fbbf24", bg="#2b2110")
            self._configure_widget_if_changed(self.pipeline_state_label, fg="#fbbf24")
        elif runtime_state_value == "DEGRADED":
            self._set_var_if_changed(self.pipeline_var, "파이프라인: ▲ 부분 장애")
            self._set_var_if_changed(self.status_var, "부분 장애")
            self._configure_widget_if_changed(self.status_label, fg="#fb923c", bg="#2a160f")
            self._configure_widget_if_changed(self.pipeline_state_label, fg="#fb923c")
        elif runtime_state_value == "BROKEN":
            self._set_var_if_changed(self.pipeline_var, "파이프라인: ✗ 장애")
            self._set_var_if_changed(self.status_var, "장애")
            self._configure_widget_if_changed(self.status_label, fg="#f87171", bg="#2a1015")
            self._configure_widget_if_changed(self.pipeline_state_label, fg="#f87171")
        else:
            self._set_var_if_changed(self.pipeline_var, "파이프라인: ■ 중지됨")
            self._set_var_if_changed(self.status_var, "중지됨")
            self._configure_widget_if_changed(self.status_label, fg="#f87171", bg="#2a1015")
            self._configure_widget_if_changed(self.pipeline_state_label, fg="#f87171")

        # Watcher
        if w_alive:
            self._set_var_if_changed(self.watcher_var, f"워처: ● 활성 (PID:{w_pid})")
            self._configure_widget_if_changed(self.watcher_state_label, fg="#34d399")
        else:
            self._set_var_if_changed(self.watcher_var, "워처: ✗ 비활성")
            self._configure_widget_if_changed(self.watcher_state_label, fg="#ef4444")
        self._update_poll_freshness()
        launch_resolution = self._resolve_runtime_active_profile()
        self._apply_runtime_launch_presentation(launch_resolution)
        control_slots = snapshot.get("control_slots", {})
        verify_activity = snapshot.get("verify_activity")
        turn_state = snapshot.get("turn_state")

        working_labels = [label for label, status, _note, _quota in agents if status == "WORKING"]
        if self.selected_agent not in {label for label, _s, _n, _q in agents}:
            self.selected_agent = working_labels[0] if working_labels else default_selected_agent()
        elif self._auto_focus_agent and working_labels:
            self.selected_agent = working_labels[0]

        control_presentation = build_control_presentation(control_slots, verify_activity, turn_state=turn_state)
        self._set_var_if_changed(self.active_control_var, control_presentation.active_text)
        self._configure_widget_if_changed(
            self.active_control_box,
            bg=control_presentation.active_box_bg,
            highlightbackground=control_presentation.active_box_border,
        )
        self._configure_widget_if_changed(
            self.active_control_title_label,
            bg=control_presentation.active_box_bg,
            fg=control_presentation.active_title_fg,
        )
        self._configure_widget_if_changed(
            self.active_control_label,
            bg=control_presentation.active_box_bg,
            fg=control_presentation.active_fg,
        )
        self._set_var_if_changed(self.stale_control_var, control_presentation.stale_text)
        if control_presentation.stale_visible:
            self._configure_widget_if_changed(
                self.stale_control_box,
                bg=control_presentation.stale_box_bg,
                highlightbackground=control_presentation.stale_box_border,
            )
            self._configure_widget_if_changed(
                self.stale_control_title_label,
                bg=control_presentation.stale_box_bg,
                fg=control_presentation.stale_title_fg,
            )
            self._configure_widget_if_changed(
                self.stale_control_label,
                bg=control_presentation.stale_box_bg,
                fg=control_presentation.stale_label_fg,
            )
            if not getattr(self, "_stale_control_box_visible", False):
                self.stale_control_box.pack(fill=X, pady=(6, 0))
                self._stale_control_box_visible = True
        elif getattr(self, "_stale_control_box_visible", False):
            self.stale_control_box.pack_forget()
            self._stale_control_box_visible = False

        card_presentations, self._working_since = build_agent_card_presentations(
            agents=agents,
            selected_agent=self.selected_agent,
            token_usage=token_usage,
            working_since=self._working_since,
            now=time.time(),
        )
        empty_card = build_empty_agent_card_presentation()
        for i, (card, dot_lbl, status_lbl, note_lbl, quota_lbl) in enumerate(self.agent_labels):
            presentation = card_presentations[i] if i < len(card_presentations) else empty_card
            self._configure_widget_if_changed(dot_lbl, fg=presentation.status_fg)
            self._configure_widget_if_changed(status_lbl, text=presentation.status_text, fg=presentation.status_fg)
            if presentation.note_text is not None:
                self._configure_widget_if_changed(note_lbl, text=presentation.note_text, fg=presentation.note_fg)
            self._configure_widget_if_changed(quota_lbl, text=presentation.quota_text, fg=presentation.quota_fg)
            self._configure_widget_if_changed(
                card,
                highlightbackground=presentation.card_border,
                highlightthickness=presentation.card_thickness,
                bg=presentation.card_bg,
            )
            for child in card.winfo_children():
                try:
                    self._configure_widget_if_changed(child, bg=presentation.card_bg)
                except Exception:
                    pass

        self._apply_token_dashboard(token_dashboard)
        console_presentation = build_console_presentation(selected_agent=self.selected_agent, snapshot=snapshot)
        self._set_var_if_changed(self.focus_title_var, console_presentation.focus_title)
        self._update_text_if_changed(self.focus_text, console_presentation.focus_text)
        self._set_var_if_changed(self._artifacts_title_var, console_presentation.artifacts_title)
        self._configure_widget_if_changed(self._work_label, fg=console_presentation.artifact_color)
        self._configure_widget_if_changed(self._verify_label, fg=console_presentation.artifact_color)
        self._set_var_if_changed(self._run_context_var, console_presentation.run_context_text)
        self._configure_widget_if_changed(self._run_context_label, fg=console_presentation.run_context_fg)
        self._set_var_if_changed(self.work_var, console_presentation.work_text)
        self._set_var_if_changed(self.verify_var, console_presentation.verify_text)
        self._set_var_if_changed(self._log_title_var, console_presentation.log_title)
        self._update_text_if_changed(self.log_text, console_presentation.log_text)

        can_launch = self._runtime_launch_allowed(launch_resolution)
        can_start = not session_ok and can_launch
        self._set_main_button_states(
            all_disabled=self._action_in_progress,
            can_start=can_start,
            can_restart=session_ok and can_launch,
            session_ok=session_ok,
        )
        self._refresh_setup_mode_state_if_due()

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
            runtime_state_value = str(self._last_snapshot.get("runtime_state") or "STOPPED")
            is_live = runtime_state_value in {"STARTING", "RUNNING", "DEGRADED"}
        text, color = self._poll_status_text(is_live=is_live, now=now)
        self._set_var_if_changed(self.poll_var, text)
        self._configure_widget_if_changed(self.poll_state_label, fg=color)

    def _apply_token_dashboard(self, dashboard: object) -> None:
        token_usage = {}
        if isinstance(self._last_snapshot, dict):
            raw_usage = self._last_snapshot.get("token_usage")
            if isinstance(raw_usage, dict):
                token_usage = raw_usage
        presentation = build_token_panel_presentation(
            selected_agent=self.selected_agent,
            token_usage=token_usage,
            dashboard=dashboard,
            token_loading=self._token_dashboard_loading(),
        )
        self._set_var_if_changed(self._token_status_var, presentation.status_text)
        self._set_var_if_changed(self._token_totals_var, presentation.totals_text)
        self._set_var_if_changed(self._token_agents_var, presentation.agents_text)
        self._set_var_if_changed(self._token_selected_var, presentation.selected_text)
        self._set_var_if_changed(self._token_jobs_var, presentation.jobs_text)

    def _token_dashboard_loading(self) -> bool:
        token_action_text = ""
        if hasattr(self, "_token_action_var"):
            token_action_text = str(self._token_action_var.get() or "")
        action_loading = self._action_in_progress and (
            "전체 히스토리" in token_action_text or "DB 재구성" in token_action_text
        )
        controller = getattr(self, "_home_controller", None)
        if controller is None and hasattr(self, "project"):
            controller = self._ensure_home_controller()
        background_loading = controller.token_dashboard_loading() if controller is not None else False
        return action_loading or background_loading

    def _fmt_count(self, value: int) -> str:
        return format_compact_count(value)

    # ── Setup mode ──

    def _setup_paths(self) -> dict[str, Path]:
        return self._ensure_setup_controller().paths()

    def _setup_default_profile(self) -> dict[str, object]:
        return self._ensure_setup_controller().default_profile()

    def _setup_selected_agents(self) -> list[str]:
        return [name for name in _SETUP_AGENT_ORDER if bool(self._setup_agent_vars[name].get())]

    def _setup_recommended_executor(
        self,
        selected_agents: list[str],
        role_bindings: dict[str, str | None],
    ) -> str:
        return self._ensure_setup_controller().recommended_executor(selected_agents, role_bindings)

    def _setup_collect_form_payload(self) -> dict[str, object]:
        selected_agents = self._setup_selected_agents()
        advisory_enabled = bool(self._setup_advisory_enabled_var.get())
        return self._ensure_setup_controller().collect_form_payload(
            selected_agents=selected_agents,
            implement=self._setup_implement_var.get().strip() or None,
            verify=self._setup_verify_var.get().strip() or None,
            advisory=self._setup_advisory_var.get().strip() or None,
            advisory_enabled=advisory_enabled,
            operator_stop_enabled=bool(self._setup_operator_stop_enabled_var.get()),
            session_arbitration_enabled=bool(self._setup_session_arbitration_var.get()),
            self_verify_allowed=bool(self._setup_self_verify_var.get()),
            self_advisory_allowed=bool(self._setup_self_advisory_var.get()),
            executor_override=self._setup_executor_var.get().strip() or "auto",
        )

    def _setup_draft_payload(self, form_payload: dict[str, object]) -> dict[str, object]:
        return self._ensure_setup_controller().draft_payload(form_payload)

    def _setup_active_payload(
        self,
        form_payload: dict[str, object],
        *,
        source_setup_id: str,
    ) -> dict[str, object]:
        return self._ensure_setup_controller().active_payload(
            form_payload,
            source_setup_id=source_setup_id,
        )

    def _setup_payload_for_fingerprint(self, payload: dict[str, object]) -> dict[str, object]:
        return self._ensure_setup_controller().payload_for_fingerprint(payload)

    def _setup_fingerprint(self, payload: dict[str, object]) -> str:
        return self._ensure_setup_controller().fingerprint(payload)

    def _setup_active_profile_fingerprint(self, payload: dict[str, object]) -> str:
        return self._ensure_setup_controller().active_profile_fingerprint(payload)

    def _setup_preview_fingerprint(
        self,
        form_payload: dict[str, object],
        *,
        setup_id: str,
        draft_fingerprint: str,
    ) -> str:
        return self._ensure_setup_controller().preview_fingerprint(
            form_payload,
            setup_id=setup_id,
            draft_fingerprint=draft_fingerprint,
        )

    @staticmethod
    def _setup_preview_matches_current(
        preview_payload: dict[str, object] | None,
        current_setup_id: str,
        current_draft_fingerprint: str,
    ) -> bool:
        return SetupController.preview_matches_current(
            preview_payload,
            current_setup_id,
            current_draft_fingerprint,
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
        return SetupController.result_can_promote_active(
            result_payload,
            apply_payload,
            preview_payload,
            current_setup_id,
            draft_payload,
            current_draft_fingerprint,
            draft_fingerprint_fn,
        )

    def _setup_resolve_support(self, form_payload: dict[str, object]) -> dict[str, object]:
        return self._ensure_setup_controller().resolve_support(form_payload)

    def _resolve_runtime_active_profile(self) -> dict[str, object]:
        resolved = self._ensure_setup_controller().resolve_runtime_active_profile()
        self._update_setup_state(runtime_launch_resolution=resolved)
        return resolved

    def _runtime_resolution_messages(self, resolved: dict[str, object]) -> list[str]:
        return self._ensure_setup_controller().runtime_resolution_messages(resolved)

    def _runtime_resolution_detail(self, resolved: dict[str, object]) -> str:
        return self._ensure_setup_controller().runtime_resolution_detail(resolved)

    def _runtime_resolution_feedback_lines(self, resolved: dict[str, object]) -> list[str]:
        return self._ensure_setup_controller().runtime_resolution_feedback_lines(resolved)

    def _runtime_launch_presentation(
        self,
        resolved: dict[str, object] | None = None,
    ) -> RuntimeLaunchPresentation:
        state = self._export_setup_state()
        resolution = resolved or state.runtime_launch_resolution or self._resolve_runtime_active_profile()
        return self._ensure_setup_controller().build_runtime_launch_presentation(
            self._setup_state,
            resolution,
        )

    def _apply_runtime_launch_presentation(self, resolved: dict[str, object]) -> RuntimeLaunchPresentation:
        presentation = self._runtime_launch_presentation(resolved)
        if hasattr(self, "_runtime_launch_var"):
            self._set_var_if_changed(self._runtime_launch_var, presentation.text)
        if hasattr(self, "_setup_runtime_profile_var"):
            self._set_var_if_changed(self._setup_runtime_profile_var, presentation.text)
        if hasattr(self, "_runtime_launch_label"):
            self._configure_widget_if_changed(self._runtime_launch_label, fg=presentation.color)
        if hasattr(self, "_setup_runtime_profile_label"):
            self._configure_widget_if_changed(self._setup_runtime_profile_label, fg=presentation.color)
        return presentation

    def _runtime_launch_allowed(self, resolved: dict[str, object] | None = None) -> bool:
        return self._runtime_launch_presentation(resolved).launch_allowed

    def _setup_support_banner_lines(
        self,
        support_level: str,
        controls: dict[str, object],
    ) -> list[str]:
        return SetupController.support_banner_lines(support_level, controls)

    def _setup_validate(self, form_payload: dict[str, object]) -> tuple[list[str], list[str], list[str]]:
        return self._ensure_setup_controller().validate(form_payload)

    def _setup_effective_executor(self, form_payload: dict[str, object]) -> str:
        return self._ensure_setup_controller().effective_executor(form_payload)

    def _setup_write_json(self, path: Path, payload: dict[str, object]) -> None:
        self._ensure_setup_controller().write_json(path, payload)
        self._invalidate_setup_runtime_caches()

    def _invalidate_setup_runtime_caches(self) -> None:
        controller = self._ensure_setup_controller()
        controller.invalidate_runtime_caches()
        self._update_setup_state(runtime_launch_resolution=None)

    def _read_setup_disk_state(self, *, force: bool = False) -> dict[str, object]:
        return self._ensure_setup_controller().read_disk_state(force=force)

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

        self._update_setup_state(
            draft_saved=draft_saved,
            dirty=False,
            current_setup_id="",
            current_draft_fingerprint="",
            current_preview_fingerprint="",
            current_request_payload=None,
            current_preview_payload=None,
            current_apply_payload=None,
            current_result_payload=None,
            current_support_resolution=None,
            restart_required=False,
            detail_ready=False,
        )
        self._update_setup_widget_options()

    def _load_setup_form_from_disk(self) -> None:
        disk_state = self._read_setup_disk_state(force=True)
        draft_payload = disk_state.get("draft_payload")
        active_payload = disk_state.get("active_payload")
        source = draft_payload or active_payload or self._setup_default_profile()
        self._setup_apply_form_payload(source, draft_saved=draft_payload is not None)

    def _setup_reset_cleanup_history(self) -> None:
        self._update_setup_state(cleanup_history=[])
        self._setup_cleanup_summary_var.set("아직 정리 기록이 없습니다.")

    def _build_setup_fast_snapshot(self) -> dict[str, object]:
        controller = self._ensure_setup_controller()
        return controller.build_fast_snapshot(
            self._setup_collect_form_payload(),
            self._export_setup_state(),
        )

    def _apply_setup_fast_snapshot(self, snapshot: dict[str, object]) -> None:
        if not hasattr(self, "_setup_mode_state_var"):
            return
        state = self._export_setup_state()
        errors = list(snapshot.get("errors") or [])
        warnings = list(snapshot.get("warnings") or [])
        infos = list(snapshot.get("infos") or [])
        support_resolution = dict(snapshot.get("support_resolution") or {})
        support_level = str(support_resolution.get("support_level") or "blocked")
        support_controls = dict(support_resolution.get("controls") or {})
        form_payload = dict(snapshot.get("form_payload") or {})
        active_matches_current = bool(snapshot.get("active_matches_current"))
        action_pending = bool(snapshot.get("action_pending"))

        state.detail_ready = False
        state.mode_state = str(snapshot.get("fast_state") or "DraftOnly")
        state.current_draft_fingerprint = str(snapshot.get("current_draft_fingerprint") or "")
        state.draft_saved = bool(snapshot.get("draft_saved"))
        state.has_error = bool(errors)
        state.has_warning = bool(warnings)
        state.errors = list(errors)
        state.warnings = list(warnings)
        state.infos = list(infos)
        state.current_support_resolution = support_resolution
        self._apply_setup_state_model(state)

        self._update_setup_widget_options()
        presentation = build_setup_fast_presentation(
            snapshot,
            state,
            project_valid=self._project_valid,
            action_in_progress=self._action_in_progress,
            detail_pending_text=_SETUP_DETAIL_PENDING_TEXT,
        )
        self._setup_apply_inline_errors(errors)
        self._set_var_if_changed(self._setup_mode_state_var, presentation.mode_state_text)
        self._set_var_if_changed(self._setup_support_level_var, presentation.support_level_text)
        self._configure_widget_if_changed(
            self._setup_support_label,
            fg=presentation.support_fg,
            bg=presentation.support_bg,
        )
        self._set_var_if_changed(self._setup_validation_var, presentation.validation_text)
        self._set_var_if_changed(self._setup_preview_summary_var, presentation.preview_summary_text)
        self._set_var_if_changed(self._setup_apply_readiness_var, presentation.apply_readiness_text)
        self._set_var_if_changed(self._setup_restart_notice_var, presentation.restart_notice_text)
        self._set_var_if_changed(self._setup_current_setup_id_var, presentation.current_setup_id_text)
        self._set_var_if_changed(
            self._setup_current_preview_fingerprint_var,
            presentation.current_preview_fingerprint_text,
        )
        self._apply_runtime_launch_presentation(dict(snapshot.get("runtime_resolution") or {}))
        self._configure_widget_if_changed(
            self.btn_setup_save_draft,
            state=NORMAL if presentation.buttons.save_enabled else DISABLED,
        )
        self._configure_widget_if_changed(
            self.btn_setup_generate_preview,
            state=NORMAL if presentation.buttons.generate_enabled else DISABLED,
        )
        self._configure_widget_if_changed(self.btn_setup_apply, state=DISABLED)
        if hasattr(self, "btn_setup_clean_staged"):
            self._configure_widget_if_changed(
                self.btn_setup_clean_staged,
                state=NORMAL if presentation.buttons.clean_enabled else DISABLED,
            )
        if hasattr(self, "btn_setup_restart_now"):
            self._configure_widget_if_changed(
                self.btn_setup_restart_now,
                state=NORMAL if presentation.buttons.restart_enabled else DISABLED,
            )
        self._setup_snapshot_refresh_last_at = time.time()

    def _schedule_setup_detail_refresh(
        self,
        generation: int,
        *,
        delay_ms: int = 250,
        after_idle: bool = False,
    ) -> None:
        if getattr(self, "_mode", "home") != "setup":
            return
        if not hasattr(self, "root"):
            self._run_setup_detail_refresh(generation)
            return
        if self._setup_detail_after_id is not None:
            self.root.after_cancel(self._setup_detail_after_id)
            self._setup_detail_after_id = None

        def _run() -> None:
            self._setup_detail_after_id = None
            self._run_setup_detail_refresh(generation)

        if after_idle and hasattr(self.root, "after_idle"):
            self._setup_detail_after_id = self.root.after_idle(_run)
        else:
            self._setup_detail_after_id = self.root.after(max(0, delay_ms), _run)

    def _run_setup_detail_refresh(self, generation: int) -> None:
        if generation != int(getattr(self, "_setup_refresh_generation", 0) or 0):
            return
        if getattr(self, "_mode", "home") != "setup":
            return
        try:
            snapshot = self._build_setup_detail_snapshot()
        except Exception:
            return
        if generation != int(getattr(self, "_setup_refresh_generation", 0) or 0):
            return
        if getattr(self, "_mode", "home") != "setup":
            return
        self._apply_setup_detail_snapshot(snapshot)

    def _request_setup_mode_refresh(
        self,
        *,
        fast_delay_ms: int = 80,
        detail_delay_ms: int = 250,
        detail_after_idle: bool = False,
    ) -> None:
        if not hasattr(self, "root"):
            self._refresh_setup_mode_state()
            return
        generation = self._invalidate_setup_refresh_generation()

        def _run() -> None:
            self._setup_refresh_after_id = None
            if generation != int(getattr(self, "_setup_refresh_generation", 0) or 0):
                return
            if getattr(self, "_mode", "home") != "setup":
                return
            self._apply_setup_fast_snapshot(self._build_setup_fast_snapshot())

        self._setup_refresh_after_id = self.root.after(max(0, fast_delay_ms), _run)
        self._schedule_setup_detail_refresh(
            generation,
            delay_ms=detail_delay_ms,
            after_idle=detail_after_idle,
        )

    def _refresh_setup_mode_state_if_due(self, *, force: bool = False) -> None:
        if force:
            self._refresh_setup_mode_state()
            return
        if getattr(self, "_mode", "home") != "setup":
            return
        now = time.time()
        last_refresh = float(getattr(self, "_setup_snapshot_refresh_last_at", 0.0) or 0.0)
        ttl = float(getattr(self, "_setup_snapshot_refresh_ttl_sec", 2.0) or 2.0)
        if (now - last_refresh) < ttl:
            return
        generation = self._invalidate_setup_refresh_generation()
        self._apply_setup_fast_snapshot(self._build_setup_fast_snapshot())
        self._schedule_setup_detail_refresh(
            generation,
            delay_ms=0,
            after_idle=True,
        )

    def _setup_record_cleanup_result(
        self,
        *,
        source_label: str,
        removed_count: int,
        include_noop: bool = False,
    ) -> None:
        summary = self._ensure_setup_controller().record_cleanup_result(
            self._export_setup_state(),
            source_label=source_label,
            removed_count=removed_count,
            include_noop=include_noop,
        )
        self._apply_setup_state_model(self._setup_state_model)
        if summary is not None:
            self._set_var_if_changed(self._setup_cleanup_summary_var, summary)

    def _setup_cleanup_staged_files_once_on_startup(self) -> None:
        state = self._export_setup_state()
        removed_count = self._ensure_setup_controller().cleanup_staged_files_once_on_startup(state)
        self._apply_setup_state_model(state)
        if removed_count > 0:
            self._set_var_if_changed(self._setup_cleanup_summary_var, "\n".join(state.cleanup_history))

    def _setup_run_automatic_cleanup(self) -> None:
        state = self._export_setup_state()
        removed_count = self._ensure_setup_controller().run_automatic_cleanup(state)
        self._apply_setup_state_model(state)
        if removed_count > 0:
            self._set_var_if_changed(self._setup_cleanup_summary_var, "\n".join(state.cleanup_history))

    def _setup_cleanup_staged_files(
        self,
        *,
        request_payload: dict[str, object] | None,
        preview_payload: dict[str, object] | None,
        apply_payload: dict[str, object] | None,
        result_payload: dict[str, object] | None,
        last_applied_payload: dict[str, object] | None = None,
    ) -> list[Path]:
        state = self._export_setup_state()
        removed = self._ensure_setup_controller().cleanup_staged_files(
            state,
            request_payload=request_payload,
            preview_payload=preview_payload,
            apply_payload=apply_payload,
            result_payload=result_payload,
            last_applied_payload=last_applied_payload,
        )
        self._apply_setup_state_model(state)
        if removed:
            self._invalidate_setup_runtime_caches()
        return removed

    def _on_setup_clean_staged(self) -> None:
        if not self._project_valid:
            return
        disk_state = self._read_setup_disk_state(force=True)
        removed = self._setup_cleanup_staged_files(
            request_payload=disk_state.get("request_payload"),
            preview_payload=disk_state.get("preview_payload"),
            apply_payload=disk_state.get("apply_payload"),
            result_payload=disk_state.get("result_payload"),
            last_applied_payload=disk_state.get("last_applied_payload"),
        )
        self._setup_record_cleanup_result(
            source_label="수동 정리",
            removed_count=len(removed),
            include_noop=True,
        )
        generation = self._invalidate_setup_refresh_generation()
        self._apply_setup_fast_snapshot(self._build_setup_fast_snapshot())
        self._schedule_setup_detail_refresh(
            generation,
            delay_ms=0,
            after_idle=True,
        )
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

        form_enabled = self._export_setup_state().mode_state != "ApplyPending"
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
        presentation = build_setup_inline_errors(errors)
        self._set_var_if_changed(self._setup_agent_error_var, presentation.agent_error)
        self._set_var_if_changed(self._setup_implement_error_var, presentation.implement_error)
        self._set_var_if_changed(self._setup_verify_error_var, presentation.verify_error)
        self._set_var_if_changed(self._setup_advisory_error_var, presentation.advisory_error)

    def _setup_summary_text(
        self,
        form_payload: dict[str, object],
        preview_payload: dict[str, object] | None,
        *,
        preview_current: bool,
        stale_preview: bool,
    ) -> str:
        return self._ensure_setup_controller().summary_text(
            form_payload,
            preview_payload,
            preview_current=preview_current,
            stale_preview=stale_preview,
        )

    def _setup_restart_required_for_payload(self, payload: dict[str, object]) -> bool:
        return self._ensure_setup_controller().restart_required_for_payload(payload)

    def _setup_active_matches_current_form(
        self,
        active_payload: dict[str, object] | None,
        form_payload: dict[str, object],
    ) -> bool:
        return self._ensure_setup_controller().active_matches_current_form(
            active_payload,
            form_payload,
            dirty=self._export_setup_state().dirty,
        )

    def _setup_build_preview_payload(
        self,
        form_payload: dict[str, object],
        *,
        setup_id: str,
        draft_fingerprint: str,
    ) -> dict[str, object]:
        return self._ensure_setup_controller().build_preview_payload(
            form_payload,
            setup_id=setup_id,
            draft_fingerprint=draft_fingerprint,
        )

    def _setup_preview_can_promote_canonical(self, setup_id: str) -> bool:
        return self._ensure_setup_controller().preview_can_promote_canonical(
            self._export_setup_state(),
            setup_id,
        )

    def _setup_result_can_promote_canonical(self, setup_id: str) -> bool:
        return self._ensure_setup_controller().result_can_promote_canonical(
            self._export_setup_state(),
            setup_id,
        )

    @staticmethod
    def _setup_result_matches_current(
        result_payload: dict[str, object] | None,
        *,
        current_setup_id: str,
        current_preview_fingerprint: str,
    ) -> bool:
        return SetupController.result_matches_current(
            result_payload,
            current_setup_id=current_setup_id,
            current_preview_fingerprint=current_preview_fingerprint,
        )

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
        return self._ensure_setup_controller().protected_staged_setup_ids(
            self._export_setup_state(),
            request_payload=request_payload,
            preview_payload=preview_payload,
            apply_payload=apply_payload,
            result_payload=result_payload,
            last_applied_payload=last_applied_payload,
            extra_setup_ids=extra_setup_ids,
        )

    def _setup_execute_preview_roundtrip(
        self,
        request_payload: dict[str, object],
        form_payload: dict[str, object],
    ) -> None:
        self._ensure_setup_controller().execute_preview_roundtrip(
            self._export_setup_state(),
            request_payload,
            form_payload,
            on_complete=lambda: self._schedule_refresh_setup_mode_state(run_cleanup=True),
        )

    def _schedule_refresh_setup_mode_state(self, *, run_cleanup: bool = False) -> None:
        """비동기 executor 완료 후 main thread에서 setup state를 갱신합니다."""
        try:
            def _run() -> None:
                if run_cleanup:
                    self._setup_run_automatic_cleanup()
                self._invalidate_setup_refresh_generation()
                if getattr(self, "_mode", "home") == "setup":
                    self._apply_setup_fast_snapshot(self._build_setup_fast_snapshot())
                    self._schedule_setup_detail_refresh(
                        self._setup_refresh_generation,
                        delay_ms=0,
                        after_idle=True,
                    )
                else:
                    # Home mode still needs the full detail fold after async setup roundtrips.
                    # A fast snapshot alone can regress PreviewReady/Applied back to
                    # PreviewWaiting/ApplyPending because request/apply files are intentionally
                    # retained as historical context until cleanup.
                    self._refresh_setup_mode_state()
                    self._setup_snapshot_refresh_last_at = 0.0

            if hasattr(self, "root"):
                self.root.after(0, _run)
            else:
                _run()
        except Exception:
            pass

    def _setup_execute_apply_roundtrip(
        self,
        apply_payload: dict[str, object],
        form_payload: dict[str, object],
        preview_payload: dict[str, object],
        current_draft_fingerprint: str,
    ) -> None:
        self._ensure_setup_controller().execute_apply_roundtrip(
            self._export_setup_state(),
            apply_payload,
            form_payload,
            preview_payload,
            current_draft_fingerprint,
            on_complete=lambda: self._schedule_refresh_setup_mode_state(run_cleanup=True),
        )

    def _setup_result_feedback_lines(
        self,
        result_payload: dict[str, object] | None,
        *,
        current_setup_id: str,
    ) -> list[str]:
        return self._ensure_setup_controller().result_feedback_lines(
            result_payload,
            current_setup_id=current_setup_id,
        )

    def _setup_sync_last_applied_record(
        self,
        *,
        active_payload: dict[str, object],
        result_payload: dict[str, object],
        fallback_executor: str,
    ) -> dict[str, object]:
        return self._ensure_setup_controller().sync_last_applied_record(
            active_payload=active_payload,
            result_payload=result_payload,
            fallback_executor=fallback_executor,
        )

    @staticmethod
    def _setup_result_replays_last_applied(
        result_payload: dict[str, object] | None,
        last_applied_payload: dict[str, object] | None,
        *,
        active_exists: bool,
    ) -> bool:
        return SetupController.result_replays_last_applied(
            result_payload,
            last_applied_payload,
            active_exists=active_exists,
        )

    def _setup_reconcile_last_applied(
        self,
        *,
        active_payload: dict[str, object] | None = None,
        last_applied_payload: dict[str, object] | None = None,
        active_exists: bool | None = None,
        last_applied_exists: bool | None = None,
    ) -> dict[str, object]:
        return self._ensure_setup_controller().reconcile_last_applied(
            active_payload=active_payload,
            last_applied_payload=last_applied_payload,
            active_exists=active_exists,
            last_applied_exists=last_applied_exists,
        )

    def _setup_last_applied_feedback_lines(self, reconciliation: dict[str, object]) -> list[str]:
        return SetupController.last_applied_feedback_lines(reconciliation)

    def _setup_last_applied_notice_text(
        self,
        reconciliation: dict[str, object],
        *,
        state: str,
        restart_required: bool | None = None,
    ) -> str:
        effective_restart_required = self._export_setup_state().restart_required if restart_required is None else restart_required
        return SetupController.last_applied_notice_text(
            reconciliation,
            state=state,
            restart_required=effective_restart_required,
        )

    def _build_setup_detail_snapshot(self) -> dict[str, object]:
        controller = self._ensure_setup_controller()
        return controller.build_detail_snapshot(
            self._setup_collect_form_payload(),
            self._export_setup_state(),
        )

    def _apply_setup_detail_snapshot(self, snapshot: dict[str, object]) -> None:
        if not hasattr(self, "_setup_mode_state_var"):
            return
        state = self._export_setup_state()
        errors = list(snapshot.get("errors") or [])
        warnings = list(snapshot.get("warnings") or [])
        infos = list(snapshot.get("infos") or [])
        support_resolution = dict(snapshot.get("support_resolution") or {})

        state.current_draft_fingerprint = str(snapshot.get("current_draft_fingerprint") or "")
        state.draft_saved = bool(snapshot.get("draft_saved"))
        state.errors = list(errors)
        state.warnings = list(warnings)
        state.infos = list(infos)
        state.has_error = bool(errors)
        state.has_warning = bool(warnings)
        state.current_support_resolution = support_resolution
        state.current_setup_id = str(snapshot.get("current_setup_id") or "")
        state.current_request_payload = snapshot.get("current_request_payload")
        state.current_preview_payload = snapshot.get("current_preview_payload")
        state.current_preview_fingerprint = str(snapshot.get("current_preview_fingerprint") or "")
        state.current_apply_payload = snapshot.get("current_apply_payload")
        state.current_result_payload = snapshot.get("current_result_payload")
        state.restart_required = bool(snapshot.get("restart_required"))
        state.mode_state = str(snapshot.get("state") or "DraftOnly")
        state.detail_ready = True
        self._apply_setup_state_model(state)

        self._update_setup_widget_options()
        presentation = build_setup_detail_presentation(
            snapshot,
            state,
            project_valid=self._project_valid,
            action_in_progress=self._action_in_progress,
        )
        self._set_var_if_changed(self._setup_agent_error_var, presentation.inline_errors.agent_error)
        self._set_var_if_changed(self._setup_implement_error_var, presentation.inline_errors.implement_error)
        self._set_var_if_changed(self._setup_verify_error_var, presentation.inline_errors.verify_error)
        self._set_var_if_changed(self._setup_advisory_error_var, presentation.inline_errors.advisory_error)
        self._set_var_if_changed(self._setup_mode_state_var, presentation.mode_state_text)
        self._set_var_if_changed(self._setup_support_level_var, presentation.support_level_text)
        self._configure_widget_if_changed(
            self._setup_support_label,
            fg=presentation.support_fg,
            bg=presentation.support_bg,
        )
        self._set_var_if_changed(self._setup_current_setup_id_var, presentation.current_setup_id_text)
        self._set_var_if_changed(
            self._setup_current_preview_fingerprint_var,
            presentation.current_preview_fingerprint_text,
        )
        self._set_var_if_changed(self._setup_validation_var, presentation.validation_text)
        self._set_var_if_changed(self._setup_preview_summary_var, presentation.preview_summary_text)
        self._set_var_if_changed(self._setup_restart_notice_var, presentation.restart_notice_text)
        self._set_var_if_changed(self._setup_apply_readiness_var, presentation.apply_readiness_text)
        self._update_setup_action_buttons()
        self._setup_snapshot_refresh_last_at = time.time()
        self._sync_start_button_state()

    def _refresh_setup_mode_state(self) -> None:
        if not hasattr(self, "_setup_mode_state_var"):
            return
        snapshot = self._build_setup_detail_snapshot()
        self._apply_setup_detail_snapshot(snapshot)

    def _setup_apply_readiness_text(
        self,
        state: str,
        preview_current: bool,
        preview_payload: dict[str, object] | None = None,
    ) -> str:
        return self._ensure_setup_controller().apply_readiness_text(
            state,
            preview_current,
            preview_payload,
            state=self._export_setup_state(),
        )

    def _update_setup_action_buttons(self) -> None:
        if not hasattr(self, "btn_setup_save_draft"):
            return
        state = self._export_setup_state()
        support_resolution = state.current_support_resolution or self._setup_resolve_support(self._setup_collect_form_payload())
        support_controls = dict(support_resolution.get("controls") or {})
        preview_controls = dict((state.current_preview_payload or {}).get("controls") or {})
        active_matches_current = False
        if state.mode_state == "Applied" and not state.dirty:
            active_payload = self._read_setup_disk_state().get("active_payload")
            active_matches_current = self._setup_active_matches_current_form(
                active_payload,
                self._setup_collect_form_payload(),
            )
        buttons = build_setup_action_buttons(
            project_valid=self._project_valid,
            action_in_progress=self._action_in_progress,
            state=state,
            preview_allowed=bool(support_controls.get("preview_allowed", True)),
            apply_allowed=bool(preview_controls.get("apply_allowed")),
            active_matches_current=active_matches_current,
        )

        self._configure_widget_if_changed(self.btn_setup_save_draft, state=NORMAL if buttons.save_enabled else DISABLED)
        self._configure_widget_if_changed(
            self.btn_setup_generate_preview,
            state=NORMAL if buttons.generate_enabled else DISABLED,
        )
        self._configure_widget_if_changed(self.btn_setup_apply, state=NORMAL if buttons.apply_enabled else DISABLED)
        if hasattr(self, "btn_setup_clean_staged"):
            self._configure_widget_if_changed(
                self.btn_setup_clean_staged,
                state=NORMAL if buttons.clean_enabled else DISABLED,
            )
        if hasattr(self, "btn_setup_restart_now"):
            self._configure_widget_if_changed(
                self.btn_setup_restart_now,
                state=NORMAL if buttons.restart_enabled else DISABLED,
            )

    def _setup_promote_active_profile(
        self,
        draft_payload: dict[str, object],
        *,
        source_setup_id: str,
    ) -> dict[str, object]:
        paths = self._setup_paths()
        active_payload = read_json_path(paths["active"])
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
        self._update_setup_state(dirty=True)
        self._update_setup_widget_options()
        self._request_setup_mode_refresh()

    def _on_setup_role_change(self, _event=None) -> None:
        if self._setup_form_updating:
            return
        self._update_setup_state(dirty=True)
        self._request_setup_mode_refresh()

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
        self._update_setup_state(dirty=True)
        self._update_setup_widget_options()
        self._request_setup_mode_refresh()

    def _on_setup_executor_change(self, _event=None) -> None:
        if self._setup_form_updating:
            return
        self._update_setup_state(dirty=True)
        self._request_setup_mode_refresh()

    def _on_setup_save_draft(self) -> None:
        if not self._project_valid:
            return
        payload = self._setup_draft_payload(self._setup_collect_form_payload())
        draft_fingerprint = self._setup_fingerprint(payload)
        self._setup_write_json(self._setup_paths()["draft"], payload)
        self._update_setup_state(
            current_draft_fingerprint=draft_fingerprint,
            draft_saved=True,
            dirty=False,
        )
        self._request_setup_mode_refresh(
            fast_delay_ms=0,
            detail_delay_ms=0,
            detail_after_idle=True,
        )
        self._set_toast_style("success")
        self.msg_var.set("설정 초안을 저장했습니다")
        self._clear_msg_later()

    def _on_setup_generate_preview(self) -> None:
        if not self._project_valid:
            return
        try:
            state = self._export_setup_state()
            if state.dirty or not state.draft_saved:
                self._on_setup_save_draft()
                state = self._export_setup_state()
            form_payload = self._setup_collect_form_payload()
            draft_payload = self._setup_draft_payload(form_payload)
            draft_fingerprint = self._setup_fingerprint(draft_payload)
            support_resolution = self._setup_resolve_support(form_payload)
            support_controls = dict(support_resolution.get("controls") or {})
            if not bool(support_controls.get("preview_allowed", True)):
                self._set_toast_style("error")
                self.msg_var.set("미리보기 생성 실패: 현재 프로필은 preview만 허용되지 않는 상태입니다.")
                self._clear_msg_later(8000)
                return
            current_setup_id = self._setup_generate_setup_id()
            request_payload = {
                "status": "setup_requested",
                "setup_id": current_setup_id,
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
                "draft_fingerprint": draft_fingerprint,
                "executor_candidate": self._setup_effective_executor(form_payload),
                "support_level": str(support_resolution.get("support_level") or "blocked"),
                "controls": support_controls,
                "messages": list(support_resolution.get("messages") or []),
                "effective_runtime_plan": support_resolution.get("effective_runtime_plan"),
            }
            self._update_setup_state(
                current_setup_id=current_setup_id,
                current_draft_fingerprint=draft_fingerprint,
                current_request_payload=request_payload,
                current_preview_payload=None,
                current_preview_fingerprint="",
                current_apply_payload=None,
                current_result_payload=None,
                current_support_resolution=support_resolution,
                detail_ready=False,
            )
            self._setup_write_json(self._setup_paths()["request"], request_payload)
            self._setup_execute_preview_roundtrip(request_payload, form_payload)
            self._request_setup_mode_refresh(
                fast_delay_ms=0,
                detail_delay_ms=0,
                detail_after_idle=True,
            )
            self._set_toast_style("progress")
            self.msg_var.set("설정 미리보기를 요청했습니다")
            self._clear_msg_later()
        except Exception as exc:
            self._set_toast_style("error")
            self.msg_var.set(f"미리보기 요청 실패: {exc}")
            self._clear_msg_later(10000)

    def _on_setup_apply(self) -> None:
        state = self._export_setup_state()
        preview_payload = state.current_preview_payload
        if not preview_payload:
            self._set_toast_style("error")
            self.msg_var.set("적용 실패: 먼저 현재 초안 기준 미리보기를 생성해 주세요.")
            self._clear_msg_later(8000)
            return
        preview_controls = dict(preview_payload.get("controls") or {})
        if not bool(preview_controls.get("apply_allowed")):
            self._set_toast_style("error")
            self.msg_var.set("적용 실패: 현재 미리보기 조합은 apply가 차단되어 있습니다.")
            self._clear_msg_later(8000)
            return
        try:
            form_payload = self._setup_collect_form_payload()
            apply_payload = {
                "status": "apply_requested",
                "setup_id": state.current_setup_id,
                "schema_version": 1,
                "approved_at": utc_now_iso(),
                "approved_preview_fingerprint": state.current_preview_fingerprint,
                "executor": self._setup_effective_executor(form_payload),
            }
            self._setup_write_json(self._setup_paths()["apply"], apply_payload)
            self._update_setup_state(
                current_apply_payload=apply_payload,
                current_result_payload=None,
                detail_ready=False,
            )
            self._setup_execute_apply_roundtrip(
                apply_payload,
                form_payload,
                preview_payload,
                state.current_draft_fingerprint,
            )
            self._request_setup_mode_refresh(
                fast_delay_ms=0,
                detail_delay_ms=0,
                detail_after_idle=True,
            )
            self._set_toast_style("progress")
            self.msg_var.set("설정 적용을 요청했습니다")
            self._clear_msg_later()
        except Exception as exc:
            self._set_toast_style("error")
            self.msg_var.set(f"적용 요청 실패: {exc}")
            self._clear_msg_later(10000)

    def _on_setup_confirm_restart(self) -> None:
        state = self._export_setup_state()
        if state.mode_state != "Applied" or not state.restart_required:
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

    def _setup_state_presentation(self, resolved: dict[str, object] | None = None) -> SetupStatusPresentation:
        resolution = resolved
        if resolution is None:
            resolution = self._export_setup_state().runtime_launch_resolution
        return self._ensure_setup_controller().build_setup_state_presentation(
            self._setup_state,
            self._setup_state_detail,
            resolution,
        )

    def _apply_setup_state_presentation(self, resolved: dict[str, object] | None = None) -> None:
        if not hasattr(self, "setup_var") or not hasattr(self, "setup_state_label"):
            return
        presentation = self._setup_state_presentation(resolved)
        self._set_var_if_changed(self.setup_var, presentation.text)
        self._configure_widget_if_changed(self.setup_state_label, fg=presentation.color)

    def _set_setup_state(self, state: str, detail: str = "") -> None:
        """Setup 상태 UI를 갱신합니다. main thread에서 호출해야 합니다."""
        self._setup_state = state
        self._setup_state_detail = detail
        self._apply_setup_state_presentation(self._export_setup_state().runtime_launch_resolution)
        self._sync_start_button_state()

    def _sync_start_button_state(self) -> None:
        """Setup 상태에 따라 Start 버튼 활성/비활성."""
        if self._action_in_progress:
            return
        resolved = self._resolve_runtime_active_profile()
        launch = self._apply_runtime_launch_presentation(resolved)
        self._apply_setup_state_presentation(resolved)
        session_ok = False
        if self._last_snapshot is not None:
            session_ok = str(self._last_snapshot.get("runtime_state") or "STOPPED") != "STOPPED"
        elif hasattr(self, "_session_name"):
            session_ok = runtime_state(self.project) != "STOPPED"
        can_launch = launch.launch_allowed
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
            for sec in range(10):
                time.sleep(1)
                current_runtime_state = runtime_state(self.project)
                collector_alive, _collector_pid = token_collector_alive(self.project)
                if current_runtime_state == "STOPPED" and not collector_alive:
                    self.root.after(0, lambda: self._unlock_buttons("■ 중지 완료"))
                    self.root.after(0, lambda: self._clear_msg_later())
                    return
                self.root.after(0, lambda s=sec: self.msg_var.set(
                    f"■ 중지 중... runtime {runtime_state(self.project)} ({s+1}초)"))
            remaining = []
            if runtime_state(self.project) != "STOPPED":
                remaining.append(f"runtime {runtime_state(self.project)}")
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
            for sec in range(10):
                time.sleep(1)
                if runtime_state(self.project) == "STOPPED":
                    break
                self.root.after(0, lambda s=sec: self.msg_var.set(
                    f"↻ 중지 중... runtime {runtime_state(self.project)} ({s+2}초)"))
            if runtime_state(self.project) != "STOPPED":
                self.root.after(0, lambda: self._unlock_buttons(
                    "↻ 재시작 실패: 기존 runtime을 중지하지 못했습니다", is_error=True))
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
        if runtime_state(self.project) != "STOPPED":
            runtime_attach(self.project, self._session_name)
            self._set_toast_style("success")
            self.msg_var.set("runtime attach 실행됨")
            self._clear_msg_later()
        else:
            self._set_toast_style("error")
            self.msg_var.set("실행 중인 runtime이 없습니다. 먼저 Start하세요.")
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
