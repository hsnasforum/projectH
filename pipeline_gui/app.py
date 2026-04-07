"""PipelineGUI — main application class with polling, control, and UI."""
from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Text, Entry,
    StringVar, LEFT, RIGHT, BOTH, X, Y, END, WORD, DISABLED, NORMAL,
    font as tkfont,
    filedialog, messagebox,
)
from tkinter import PanedWindow, VERTICAL
from tkinter.ttk import Scrollbar as TtkScrollbar

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
    backfill_token_history, rebuild_token_db,
)
from .agents import (
    STATUS_COLORS, ANSI_RE,
    _extract_run_summary, format_elapsed, _parse_elapsed,
    extract_quota_note, detect_agent_status, capture_agent_panes,
    rejoin_wrapped_pane_lines, format_focus_output,
    watcher_runtime_hints,
)
from .setup import (
    _HARD_BLOCKERS, _SOFT_WARNINGS,
    _find_cli_bin, _file_exists,
    _check_hard_blockers, _check_soft_warnings,
    _check_missing_guides, _create_guide_file, _GUIDE_TEMPLATES,
)
from .view import (
    BG, FG, ACCENT, SUB_FG, BTN_BG, BTN_FG,
    CARD_BG, CARD_BORDER, LOG_BG, HEADER_BG, AGENT_CARD_BG,
    POLL_MS, init_ttk_style, create_fonts, make_card, lighten,
    build_header, build_project_bar, build_control_bar,
    build_status_panels, build_agent_cards, build_token_panel, build_console_panels,
)
from .guide import DEFAULT_GUIDE
from .token_queries import load_token_dashboard
from .tokens import collect_token_usage, format_token_usage_note

class PipelineGUI:
    def __init__(self, project: Path) -> None:
        self.project = project
        self._session_name = _session_name_for(project)
        self.selected_agent = "Claude"
        self._auto_focus_agent = True
        self._poll_in_flight = False
        self._last_snapshot: dict[str, object] | None = None
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
        self._project_valid, self._project_error = validate_project_root(project)
        if self._project_valid:
            boot_ok, boot_error = bootstrap_project_root(project)
            if not boot_ok:
                self._project_valid = False
                self._project_error = boot_error
        self.root = Tk()
        self.root.title("Pipeline Launcher")
        self.root.configure(bg="#0f0f0f")
        self.root.resizable(True, True)
        self._set_initial_window_geometry()
        self.root.minsize(900, 600)

        self._build_ui()

        if not self._project_valid:
            self._show_project_error()
        else:
            _save_project_path(_wsl_path_str(self.project) if IS_WINDOWS else str(self.project))
            self._schedule_poll()
            self._tick_after_id = self.root.after(1000, self._tick_elapsed)
            # 초기 setup 자동 점검 (bg thread)
            self.root.after(500, lambda: threading.Thread(
                target=self._run_setup_check_silent, daemon=True).start())

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

        # Build sections
        build_project_bar(self, content)
        build_control_bar(self, content)
        build_status_panels(self, content)
        build_agent_cards(self, content)
        build_token_panel(self, content)
        build_console_panels(self, content)

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
            hint = hints.get(label)
            if hint:
                hint_status, hint_note = hint
                if hint_status == "WORKING":
                    if status in {"BOOTING", "OFF"}:
                        status = "WORKING"
                        note = hint_note or note
                    elif status == "WORKING" and hint_note:
                        note = hint_note
                elif hint_status == "READY" and status == "BOOTING":
                    status = "READY"
                    note = ""
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
        self.status_var.set("Invalid Project")
        self.status_label.configure(fg="#ef4444", bg="#351717")
        self.pipeline_var.set("Pipeline: — (invalid project root)")
        self.pipeline_state_label.configure(fg="#ef4444")
        self.watcher_var.set("Watcher: —")
        self.watcher_state_label.configure(fg="#888888")
        self.work_var.set("Latest work: —")
        self.verify_var.set("Latest verify: —")
        self._set_toast_style("error")
        self.msg_var.set(self._project_error)
        self.setup_var.set("Setup: —")
        self.setup_state_label.configure(fg="#888888")
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
        """Home/Guide 모드 전환."""
        if mode == self._mode:
            return
        self._mode = mode
        if mode == "home":
            self._guide_frame.pack_forget()
            self._home_frame.pack(fill=BOTH, expand=True)
            self._mode_btn_home.configure(bg="#2a2a3a", fg="#d8dae0")
            self._mode_btn_guide.configure(bg="#18182a", fg="#6b7280")
        else:
            self._home_frame.pack_forget()
            self._guide_frame.pack(fill=BOTH, expand=True)
            self._mode_btn_guide.configure(bg="#2a2a3a", fg="#d8dae0")
            self._mode_btn_home.configure(bg="#18182a", fg="#6b7280")

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
            with self._token_usage_lock:
                self._token_usage_project_key = str(new_path)
                self._token_usage_cache = {}
                self._token_usage_last_refresh = 0.0
                self._token_usage_refresh_in_flight = False
            _save_project_path(new_path_str)
            self._refresh_recent_buttons()
            self._load_project_guide()
            self._set_toast_style("success")
            self.msg_var.set(f"Project applied: {new_path_str}")
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
        }

    def _apply_snapshot(self, snapshot: dict[str, object]) -> None:
        self._last_snapshot = snapshot
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
            self.pipeline_var.set("Pipeline: ● RUNNING")
            self.status_var.set("RUNNING")
            self.status_label.configure(fg="#4ade80", bg="#0a2a18")
            self.pipeline_state_label.configure(fg="#4ade80")
        else:
            self.pipeline_var.set("Pipeline: ■ STOPPED")
            self.status_var.set("STOPPED")
            self.status_label.configure(fg="#f87171", bg="#2a1015")
            self.pipeline_state_label.configure(fg="#f87171")

        # Watcher
        if w_alive:
            self.watcher_var.set(f"Watcher: ● Alive (PID:{w_pid})")
            self.watcher_state_label.configure(fg="#34d399")
        else:
            self.watcher_var.set("Watcher: ✗ Dead")
            self.watcher_state_label.configure(fg="#ef4444")

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
                status_lbl.configure(text=status, fg=color)
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
                    text=f"Quota: {display_quota}" if display_quota else "Quota: —",
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
                quota_lbl.configure(text="Quota: —", fg="#666666")
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
                fallback_parts.append(f"Current turn: {run_turn}")
            if run_phase:
                fallback_parts.append(f"Phase: {run_phase}")
            if run_job:
                fallback_parts.append(f"Job: {run_job}")
            # agent별 watcher 힌트 추가
            for label, status, note, _quota in agents:
                if label == self.selected_agent and status == "WORKING" and note:
                    fallback_parts.append(f"{label}: WORKING ({note})")
                elif label == self.selected_agent and status != "OFF":
                    fallback_parts.append(f"{label}: {status}")
            if fallback_parts:
                selected_text = "\n".join(fallback_parts)

        if is_live:
            title_suffix = "pane tail" if selected_text not in ("(출력 없음)", "(표시할 출력 없음)") else "run context"
            self.focus_title_var.set(f"{self.selected_agent.upper()} • {title_suffix}")
        else:
            self.focus_title_var.set(f"{self.selected_agent.upper()} • pane tail (last run)")
        self._update_text_if_changed(self.focus_text, selected_text)

        # Artifacts / log: stale label + dim color
        stale_tag = "" if is_live else " (last run)"
        artifact_color = "#c0a060" if is_live else "#505868"

        self._artifacts_title_var.set("ARTIFACTS" if is_live else "ARTIFACTS (last run)")
        self._work_label.configure(fg=artifact_color)
        self._verify_label.configure(fg=artifact_color)

        # current run context
        run_job = run.get("job", "")
        run_phase = run.get("phase", "")
        run_turn = run.get("turn", "")
        if is_live and (run_job or run_phase or run_turn):
            parts = []
            if run_turn:
                parts.append(f"Turn: {run_turn}")
            if run_phase:
                parts.append(f"Phase: {run_phase}")
            if run_job:
                # job ID에서 날짜 이후 의미 부분만 추출
                short_job = run_job.split("-", 1)[1][:50] if "-" in run_job else run_job[:50]
                parts.append(f"Job: {short_job}")
            self._run_context_var.set(" │ ".join(parts))
            self._run_context_label.configure(fg="#5b9cf6")
        elif not is_live and run_job:
            self._run_context_var.set(f"Last job: {run_job.split('-', 1)[1][:50] if '-' in run_job else run_job[:50]}")
            self._run_context_label.configure(fg="#404058")
        else:
            self._run_context_var.set("")

        work_display = f"Latest work:   {work_name}"
        if work_mtime:
            work_display += f" ({time_ago(work_mtime)})"
        verify_display = f"Latest verify: {verify_name}"
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
            self._log_title_var.set(f"WATCHER LOG{log_hint}")
        else:
            self._log_title_var.set(f"WATCHER LOG (last run){log_hint}")

        log_text = "\n".join(
            (l.strip()[:140] + "…" if len(l.strip()) > 143 else l.strip())
            for l in log_lines
        )
        self._update_text_if_changed(self.log_text, log_text)

        can_start = not session_ok and self._setup_state == "ready"
        self._set_main_button_states(
            all_disabled=self._action_in_progress,
            can_start=can_start,
            session_ok=session_ok,
        )

    def _apply_token_dashboard(self, dashboard: object) -> None:
        if dashboard is None:
            self._token_status_var.set(self._empty_token_label("Collector"))
            self._token_totals_var.set(self._empty_token_label("Today"))
            self._token_agents_var.set(self._empty_token_label("Agents"))
            self._token_selected_var.set(self._empty_token_label(f"Selected {self.selected_agent.upper()}"))
            self._token_jobs_var.set(self._empty_token_label("Top jobs"))
            return
        collector = getattr(dashboard, "collector_status", None)
        totals = getattr(dashboard, "today_totals", None)
        agents = list(getattr(dashboard, "agent_totals", []) or [])
        jobs = list(getattr(dashboard, "top_jobs", []) or [])
        display_day = str(getattr(dashboard, "display_day", "") or "")
        today_day = time.strftime("%Y-%m-%d")
        totals_label = "Today" if not display_day or display_day == today_day else f"Latest {display_day}"
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
        title = f"Selected {selected.upper()}: "
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
            self._token_selected_var.set(title + "loading...")
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
                    parts.append("no-link")
                else:
                    parts.append(f"linked {linked_events}/{events}")

        if not parts:
            parts.append("no data")
        self._token_selected_var.set(title + " · ".join(parts))

    def _empty_token_label(self, label: str) -> str:
        return f"{label}: —"

    def _loading_token_label(self, label: str) -> str:
        return f"{label}: loading..."

    def _token_dashboard_loading(self) -> bool:
        token_action_text = ""
        if hasattr(self, "_token_action_var"):
            token_action_text = str(self._token_action_var.get() or "")
        return self._action_in_progress and (
            "FULL HISTORY" in token_action_text or "REBUILD DB" in token_action_text
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
            return self._loading_token_label("Collector") if token_loading else "Collector: missing"
        phase = getattr(collector, "phase", "missing")
        heartbeat = str(getattr(collector, "last_heartbeat_at", "") or "")
        heartbeat_age_sec = int(getattr(collector, "heartbeat_age_sec", 0) or 0)
        parsed = int(getattr(collector, "parsed_events", 0) or 0)
        files = int(getattr(collector, "scanned_files", 0) or 0)
        error = str(getattr(collector, "last_error", "") or "")
        launch_mode = str(getattr(collector, "launch_mode", "") or "")
        window_name = str(getattr(collector, "window_name", "") or "")
        status_parts = [f"Collector: {phase}"]
        if launch_mode:
            status_parts.append(f"{launch_mode}:{window_name}" if launch_mode == "tmux" and window_name else launch_mode)
        if heartbeat:
            status_parts.append(f"HB {heartbeat[11:19] if len(heartbeat) >= 19 else heartbeat}")
        if getattr(collector, "is_stale", False) and heartbeat_age_sec:
            status_parts.append(f"stale {heartbeat_age_sec}s")
        if files or parsed:
            status_parts.append(f"{files} files · {parsed} events")
        if error:
            status_parts.append(f"Err {error[:60]}")
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
            f"{totals_label} In {self._fmt_count(int(getattr(totals, 'input_tokens', 0) or 0))}",
            f"Out {self._fmt_count(int(getattr(totals, 'output_tokens', 0) or 0))}",
        ]
        cache_total = int(getattr(totals, "cache_read_tokens", 0) or 0) + int(
            getattr(totals, "cache_write_tokens", 0) or 0
        )
        thinking = int(getattr(totals, "thinking_tokens", 0) or 0)
        if cache_total:
            total_parts.append(f"Cache {self._fmt_count(cache_total)}")
        if thinking:
            total_parts.append(f"Think {self._fmt_count(thinking)}")
        actual_cost = float(getattr(totals, "actual_cost_usd_sum", 0.0) or 0.0)
        estimated_cost = float(getattr(totals, "estimated_only_cost_usd_sum", 0.0) or 0.0)
        total_parts.append(f"Cost ${actual_cost + estimated_cost:.2f}")
        if actual_cost:
            total_parts.append(f"Actual ${actual_cost:.2f}")
        if estimated_cost:
            total_parts.append(f"Est ${estimated_cost:.2f}")
        return " | ".join(total_parts)

    def _format_token_agents_line(self, agents: list[object], *, token_loading: bool) -> str:
        if token_loading and not agents:
            return self._loading_token_label("Agents")
        if not agents:
            return self._empty_token_label("Agents")
        return "Agents: " + " | ".join(self._format_token_agent_segment(item) for item in agents[:3])

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
            segment += " no-link"
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
            return self._loading_token_label("Top jobs")
        if not jobs and (has_agents or not totals_empty):
            return "Top jobs: no linked jobs yet"
        if not jobs:
            return self._empty_token_label("Top jobs")
        return "Top jobs: " + " | ".join(self._format_token_job_segment(item) for item in jobs[:3])

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

    def _set_main_button_states(
        self,
        *,
        all_disabled: bool,
        can_start: bool = False,
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
        self.btn_setup.configure(state=NORMAL)
        self.btn_start.configure(state=NORMAL if can_start else DISABLED)
        self.btn_stop.configure(state=NORMAL if session_ok else DISABLED)
        self.btn_restart.configure(state=NORMAL if session_ok else DISABLED)
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

    def _unlock_buttons(self, msg: str, is_error: bool = False) -> None:
        self._action_in_progress = False
        self._set_toast_style("error" if is_error else "success")
        self.msg_var.set(msg)

    def _set_token_action_text(self, text: str) -> None:
        if hasattr(self, "_token_action_var"):
            self._token_action_var.set(text)

    def _update_token_action_progress(self, action_label: str, payload: dict[str, object]) -> None:
        phase = str(payload.get("phase") or "scanning")
        phase_display = phase.replace("_", " ")
        elapsed = float(payload.get("elapsed_sec") or 0.0)
        scanned_files = int(payload.get("scanned_files") or 0)
        parsed_files = int(payload.get("parsed_files") or 0)
        total_files = int(payload.get("total_files") or 0)
        progress_percent = int(payload.get("progress_percent") or 0)
        inserted = int(payload.get("usage_inserted") or 0) + int(payload.get("pipeline_inserted") or 0)
        duplicates = int(payload.get("duplicates") or 0)
        retry_later = int(payload.get("retry_later") or 0)
        text = (
            f"Action: {action_label} · {progress_percent}% · {phase_display} · {elapsed:.1f}s"
            f" · scan {scanned_files}/{total_files or scanned_files} · parse {parsed_files}"
            f" · insert {self._fmt_count(inserted)} · dup {self._fmt_count(duplicates)}"
        )
        if retry_later:
            text += f" · retry {retry_later}"
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
            f"Action: {action_label} · {progress_percent}% · idle · {elapsed:.1f}s"
            f" · scan {scanned_files}/{total_files or scanned_files} · parse {parsed_files}"
            f" · insert {self._fmt_count(inserted)} · dup {self._fmt_count(duplicates)}"
        )
        if retry_later:
            text += f" · retry {retry_later}"
        if backup_path:
            text += f" · backup {Path(backup_path).name}"
        return text

    def _clear_msg_later(self, delay_ms: int = 6000) -> None:
        self.root.after(delay_ms, lambda: self.msg_var.set("") if not self._action_in_progress else None)

    # ── Setup state ──

    def _set_setup_state(self, state: str, detail: str = "") -> None:
        """Setup 상태 UI를 갱신합니다. main thread에서 호출해야 합니다."""
        self._setup_state = state
        if state == "ready":
            self.setup_var.set("Setup: ● Ready")
            self.setup_state_label.configure(fg="#34d399")
        elif state == "ready_warn":
            self.setup_var.set(f"Setup: ● Ready ({detail})")
            self.setup_state_label.configure(fg="#f59e0b")
        elif state == "checking":
            self.setup_var.set(f"Setup: … {detail or 'Checking'}")
            self.setup_state_label.configure(fg="#f59e0b")
        elif state == "missing":
            self.setup_var.set(f"Setup: ■ Missing {detail}")
            self.setup_state_label.configure(fg="#ef4444")
        elif state == "failed":
            self.setup_var.set(f"Setup: ■ {detail or 'Install failed'}")
            self.setup_state_label.configure(fg="#ef4444")
        else:
            self.setup_var.set("Setup: — Unknown")
            self.setup_state_label.configure(fg="#888888")
        self._sync_start_button_state()

    def _sync_start_button_state(self) -> None:
        """Setup 상태에 따라 Start 버튼 활성/비활성."""
        if self._action_in_progress:
            return
        can_start = self._setup_state in ("ready", "ready_warn")
        self.btn_start.configure(state=NORMAL if can_start else DISABLED)

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
        while result[0] is None:
            time.sleep(0.1)
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
        self._lock_buttons("⚙ Checking dependencies...")
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
                "Missing Guide Files",
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
                    self._msg(f"⚙ Guide 생성 완료: {', '.join(created)}")
                if failed:
                    self._msg(f"⚙ Guide 생성 실패: {', '.join(failed)}")
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
                f"⚙ Missing (수동 확인 필요): {names}", is_error=True))
            self.root.after(0, lambda: self._clear_msg_later(10000))
            return

        if not installable:
            # 모든 hard blocker OK
            if warns:
                detail = ", ".join(warns) + " 없음"
                self.root.after(0, lambda: self._set_setup_state("ready_warn", detail))
            else:
                self.root.after(0, lambda: self._set_setup_state("ready"))
            self.root.after(0, lambda: self._unlock_buttons("⚙ Setup ready"))
            self.root.after(0, lambda: self._clear_msg_later())
            return

        # ── 5. 설치 가능한 hard blocker → 설치 제안 ──
        names = ", ".join(n for n, _ in installable)
        self.root.after(0, lambda: self._set_setup_state("missing", names))
        hints = "\n".join(f"  • {n}: {h}" for n, h in installable)
        if not self._ask_yn(
            "Missing Dependencies",
            f"다음 실행 전제가 WSL에 없습니다:\n\n{hints}\n\n설치를 시도할까요?",
        ):
            self.root.after(0, lambda: self._unlock_buttons(
                f"⚙ Setup: missing {names}", is_error=True))
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
                    "Install Failed",
                    f"설치 실패:\n\n{fail_text}\n\n수동으로 설치한 뒤 Setup/Check를 다시 누르세요.",
                )
                self._unlock_buttons("⚙ Install failed", is_error=True)
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
            "Setup Complete",
            "설치가 완료되었습니다.\n지금 파이프라인을 실행하시겠습니까?",
            icon="info",
        ):
            self._msg("▶ 시작 중...")
            self.root.after(0, lambda: self._unlock_buttons(""))
            self._do_start()
        else:
            self.root.after(0, lambda: self._unlock_buttons("⚙ Setup 완료 — Start 준비됨"))
            self.root.after(0, lambda: self._clear_msg_later(8000))

    # ── Start (setup ready일 때만) ──

    def _on_start(self) -> None:
        if self._action_in_progress:
            return
        if self._setup_state not in ("ready", "ready_warn"):
            self._set_toast_style("error")
            self.msg_var.set("Setup이 완료되지 않았습니다. Setup/Check를 먼저 실행하세요.")
            self._clear_msg_later(5000)
            return
        self._lock_buttons("▶ Starting pipeline...")
        threading.Thread(target=self._do_start, daemon=True).start()

    def _do_start(self) -> None:
        try:
            # Pre-check: launcher script 접근 가능 여부
            try:
                script = resolve_project_runtime_file(self.project, "start-pipeline.sh")
            except FileNotFoundError:
                self.root.after(0, lambda: self._unlock_buttons(
                    "▶ Start failed: start-pipeline.sh not found", is_error=True))
                self.root.after(0, lambda: self._clear_msg_later(10000))
                return
            if IS_WINDOWS:
                wsl_script = _windows_to_wsl_mount(script)
                code, _ = _run(["test", "-f", wsl_script], timeout=5.0)
                if code != 0:
                    self.root.after(0, lambda: self._unlock_buttons(
                        f"▶ Start failed: {wsl_script} not accessible from WSL", is_error=True))
                    self.root.after(0, lambda: self._clear_msg_later(10000))
                    return

            self.root.after(0, lambda: self.msg_var.set("▶ Starting pipeline..."))
            pipeline_start(self.project, self._session_name)

            # 최대 15초 대기 — 단계별 진단
            for sec in range(15):
                time.sleep(1)
                if tmux_alive(self._session_name):
                    # tmux OK — watcher도 확인
                    w_alive, w_pid = watcher_alive(self.project)
                    if w_alive:
                        self.root.after(0, lambda: self._unlock_buttons("▶ Pipeline started"))
                        self.root.after(0, lambda: self._clear_msg_later())
                        return
                    if sec >= 10:
                        self.root.after(0, lambda: self._unlock_buttons(
                            f"▶ Start incomplete: tmux session exists but watcher not detected "
                            f"— check .pipeline/logs/experimental/ for errors", is_error=True))
                        self.root.after(0, lambda: self._clear_msg_later(12000))
                        return
                    # watcher 아직 안 뜸 — 조금 더 대기
                    self.root.after(0, lambda s=sec: self.msg_var.set(
                        f"▶ Starting... tmux OK, waiting for watcher ({s+1}s)"))
                    continue
                # tmux도 아직 없음
                if sec >= 5:
                    self.root.after(0, lambda s=sec: self.msg_var.set(
                        f"▶ Starting... waiting for tmux session ({s+1}s)"))

            # 15초 후에도 tmux 없음
            self.root.after(0, lambda: self._unlock_buttons(
                f"▶ Start failed: tmux session '{self._session_name}' not detected after 15s "
                f"— launcher script may have exited with an error", is_error=True))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"▶ Start failed: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later(10000))

    def _on_stop(self) -> None:
        if self._action_in_progress:
            return
        self._lock_buttons("■ Stopping pipeline...")
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
                    f"■ Stopping... ({s+1}s)"))
            remaining = []
            if tmux_alive(self._session_name):
                remaining.append("tmux session")
            collector_alive, _collector_pid = token_collector_alive(self.project)
            if collector_alive:
                remaining.append("token collector")
            detail = ", ".join(remaining) if remaining else "processes"
            self.root.after(0, lambda d=detail: self._unlock_buttons(
                f"■ Stop incomplete: {d} still detected",
                is_error=True,
            ))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"■ Stop failed: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later())

    def _on_restart(self) -> None:
        if self._action_in_progress:
            return
        self._lock_buttons("↻ Restarting pipeline...")
        threading.Thread(target=self._do_restart, daemon=True).start()

    def _do_restart(self) -> None:
        try:
            # ── Stop 단계 ──
            self.root.after(0, lambda: self.msg_var.set("↻ Stopping pipeline..."))
            pipeline_stop(self.project, self._session_name)
            # stop 확인 (최대 5초)
            for sec in range(5):
                time.sleep(1)
                if not tmux_alive(self._session_name):
                    break
                self.root.after(0, lambda s=sec: self.msg_var.set(
                    f"↻ Stopping... ({s+2}s)"))
            if tmux_alive(self._session_name):
                self.root.after(0, lambda: self._unlock_buttons(
                    "↻ Restart failed: could not stop existing session", is_error=True))
                self.root.after(0, lambda: self._clear_msg_later(10000))
                return
            self.root.after(0, lambda: self.msg_var.set("↻ Stopped — starting..."))
            time.sleep(1)

            # ── Start 단계 (Start와 동일한 진단) ──
            pipeline_start(self.project, self._session_name)
            for sec in range(15):
                time.sleep(1)
                if tmux_alive(self._session_name):
                    w_alive, w_pid = watcher_alive(self.project)
                    if w_alive:
                        self.root.after(0, lambda: self._unlock_buttons("↻ Pipeline restarted"))
                        self.root.after(0, lambda: self._clear_msg_later())
                        return
                    if sec >= 10:
                        self.root.after(0, lambda: self._unlock_buttons(
                            "↻ Restart incomplete: tmux exists but watcher not detected "
                            "— check .pipeline/logs/experimental/", is_error=True))
                        self.root.after(0, lambda: self._clear_msg_later(12000))
                        return
                    self.root.after(0, lambda s=sec: self.msg_var.set(
                        f"↻ Restarting... tmux OK, waiting for watcher ({s+1}s)"))
                    continue
                if sec >= 5:
                    self.root.after(0, lambda s=sec: self.msg_var.set(
                        f"↻ Restarting... waiting for tmux session ({s+1}s)"))

            self.root.after(0, lambda: self._unlock_buttons(
                f"↻ Restart failed: tmux session '{self._session_name}' not detected after 15s",
                is_error=True))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"↻ Restart failed: {e}", is_error=True))
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
                lambda text=f"Action: {action_label} · error · {err}": self._set_token_action_text(text)
            )
            self._enqueue_token_ui(lambda text=f"{error_message}: {err}": self._unlock_buttons(text, is_error=True))
        self._enqueue_token_ui(lambda: self._clear_msg_later(10000))

    def _on_token_backfill(self) -> None:
        self._start_token_maintenance_action(
            action_label="FULL HISTORY",
            dialog_title="Full History Backfill",
            dialog_message=(
                "기존 usage.db를 유지한 채 전체 히스토리를 추가로 채웁니다.\n"
                "중복은 dedup로 막고, 실행 중 collector가 있으면 잠시 멈췄다가 다시 시작합니다.\n\n"
                "계속하시겠습니까?"
            ),
            icon="question",
            lock_message="TOKENS: full history backfill...",
            worker_target=self._do_token_backfill,
        )

    def _do_token_backfill(self) -> None:
        self._run_token_maintenance_action(
            action_label="FULL HISTORY",
            action_runner=lambda: backfill_token_history(
                self.project,
                progress_callback=self._token_progress_callback("FULL HISTORY"),
            ),
            unlock_message_builder=lambda summary, _backup_path: (
                f"TOKENS: full history backfill complete "
                f"({float(summary.get('elapsed_sec') or 0.0):.1f}s, "
                f"{self._fmt_count(int(summary.get('usage_inserted') or 0))} usage)"
            ),
            error_message="TOKENS: backfill failed",
        )

    def _on_token_rebuild(self) -> None:
        self._start_token_maintenance_action(
            action_label="REBUILD DB",
            dialog_title="Rebuild Token DB",
            dialog_message=(
                "임시 DB로 전체 스캔을 다시 수행한 뒤, 성공 시 기존 usage.db를 backup으로 남기고 교체합니다.\n"
                "실패하면 현재 usage.db는 유지됩니다.\n"
                "실행 중 collector가 있으면 잠시 멈췄다가 다시 시작합니다.\n\n"
                "계속하시겠습니까?"
            ),
            icon="warning",
            lock_message="TOKENS: rebuilding usage DB...",
            worker_target=self._do_token_rebuild,
        )

    def _do_token_rebuild(self) -> None:
        self._run_token_maintenance_action(
            action_label="REBUILD DB",
            action_runner=lambda: rebuild_token_db(
                self.project,
                progress_callback=self._token_progress_callback("REBUILD DB"),
            ),
            unlock_message_builder=lambda summary, backup_path: (
                f"TOKENS: DB rebuilt ({float(summary.get('elapsed_sec') or 0.0):.1f}s)"
                f"{f' · backup {Path(backup_path).name}' if backup_path else ''}"
            ),
            error_message="TOKENS: rebuild failed",
        )

    # ── 실행 ──

    def run(self) -> None:
        self.root.mainloop()
