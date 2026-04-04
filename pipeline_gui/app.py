"""PipelineGUI — main application class with polling, control, and UI."""
from __future__ import annotations

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

from .platform import (
    IS_WINDOWS, APP_ROOT, TMUX_QUERY_TIMEOUT, WSL_DISTRO,
    _wsl_path_str, _windows_to_wsl_mount, _normalize_picked_path, _run,
)
from .project import (
    _load_recent_projects, _save_project_path,
    resolve_project_root, validate_project_root, bootstrap_project_root,
    _session_name_for,
)
from .backend import (
    tmux_alive, watcher_alive, latest_md, time_ago,
    watcher_log_tail, pipeline_start, pipeline_stop, tmux_attach,
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
)
from .guide import DEFAULT_GUIDE

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

        # Colors from view module
        bg = BG
        fg = FG
        accent = ACCENT
        sub_fg = SUB_FG
        btn_bg = BTN_BG
        btn_fg = BTN_FG
        card_bg = CARD_BG
        card_border = CARD_BORDER
        log_bg = LOG_BG
        header_bg = HEADER_BG

        fonts = create_fonts()
        title_font = fonts["title"]
        body_font = fonts["body"]
        small_font = fonts["small"]
        status_font = fonts["status"]
        section_font = fonts["section"]
        ctrl_font = fonts["ctrl"]



        # ── 상단 헤더 (콘솔 바) ──
        top = Frame(self.root, bg=header_bg, padx=16, pady=8)
        top.pack(fill=X)
        # 좌측 세로선 accent
        Frame(top, bg=accent, width=3).pack(side=LEFT, fill=Y, padx=(0, 10))

        Label(top, text="PIPELINE OPS", font=title_font, bg=header_bg, fg="#8090b0").pack(side=LEFT)

        # ── Home / Guide 모드 전환 ──
        mode_frame = Frame(top, bg=header_bg)
        mode_frame.pack(side=LEFT, padx=(24, 0))
        self._mode = "home"
        self._mode_btn_home = Button(
            mode_frame, text="OPS", font=ctrl_font,
            bg="#2a2a3a", fg="#d8dae0", activebackground="#3a3a4e", activeforeground="#ffffff",
            bd=0, padx=12, pady=3, highlightthickness=0, cursor="hand2",
            command=lambda: self._switch_mode("home"),
        )
        self._mode_btn_home.bind("<Enter>", lambda e: self._mode_btn_home.configure(bg="#363648"))
        self._mode_btn_home.bind("<Leave>", lambda e: self._mode_btn_home.configure(
            bg="#2a2a3a" if self._mode == "home" else "#18182a"))
        self._mode_btn_home.pack(side=LEFT, padx=(0, 2))
        self._mode_btn_guide = Button(
            mode_frame, text="GUIDE", font=ctrl_font,
            bg="#18182a", fg="#6b7280", activebackground="#2a2a3a", activeforeground="#ffffff",
            bd=0, padx=12, pady=3, highlightthickness=0, cursor="hand2",
            command=lambda: self._switch_mode("guide"),
        )
        self._mode_btn_guide.bind("<Enter>", lambda e: self._mode_btn_guide.configure(bg="#363648"))
        self._mode_btn_guide.bind("<Leave>", lambda e: self._mode_btn_guide.configure(
            bg="#2a2a3a" if self._mode == "guide" else "#18182a"))
        self._mode_btn_guide.pack(side=LEFT)

        self.status_var = StringVar(value="STOPPED")
        self.status_label = Label(
            top,
            textvariable=self.status_var,
            font=ctrl_font,
            bg="#2a1015",
            fg="#f87171",
            padx=12,
            pady=3,
        )
        self.status_label.pack(side=RIGHT)

        # ── 메인 컨텐츠 컨테이너 ──
        self._content_container = Frame(self.root, bg=bg)
        self._content_container.pack(fill=BOTH, expand=True)

        # Home 모드 프레임
        content = Frame(self._content_container, bg=bg, padx=14, pady=12)
        self._home_frame = content
        content.pack(fill=BOTH, expand=True)

        # Guide 모드 프레임 (나중에 채움)
        self._guide_frame = Frame(self._content_container, bg=bg, padx=14, pady=12)

        # ── 프로젝트 경로 (Entry + Browse + Apply) ──
        proj_card = make_card(content)
        proj_card.pack(fill=X, pady=(0, 10))
        Label(proj_card, text="Project", font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")

        path_row = Frame(proj_card, bg=card_bg)
        path_row.pack(fill=X, pady=(4, 0))

        self._path_var = StringVar(
            value=_wsl_path_str(self.project) if IS_WINDOWS else str(self.project),
        )
        self._path_entry = Entry(
            path_row,
            textvariable=self._path_var,
            font=body_font,
            bg="#1a1a1a",
            fg="#f59e0b",
            insertbackground="#f59e0b",
            bd=0,
            highlightthickness=1,
            highlightbackground="#444444",
            highlightcolor="#f59e0b",
        )
        self._path_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 6))
        self._path_entry.bind("<Return>", lambda _e: self._apply_project_path())

        _browse_bg = btn_bg
        self._path_browse_btn = Button(
            path_row,
            text="Browse…",
            command=self._on_browse,
            font=small_font,
            bg=_browse_bg,
            fg=btn_fg,
            activebackground=lighten(_browse_bg, 30),
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=4,
            highlightthickness=1,
            highlightbackground="#444444",
            cursor="hand2",
        )
        self._path_browse_btn.bind("<Enter>", lambda e: self._path_browse_btn.configure(bg=lighten(_browse_bg, 18)))
        self._path_browse_btn.bind("<Leave>", lambda e: self._path_browse_btn.configure(bg=_browse_bg))
        self._path_browse_btn.pack(side=RIGHT, padx=(4, 0))

        _apply_bg = btn_bg
        self._path_apply_btn = Button(
            path_row,
            text="Apply",
            command=self._apply_project_path,
            font=small_font,
            bg=_apply_bg,
            fg=btn_fg,
            activebackground=lighten(_apply_bg, 30),
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=4,
            highlightthickness=1,
            highlightbackground="#444444",
            disabledforeground="#555555",
        )
        self._path_apply_btn.bind("<Enter>", lambda e: self._path_apply_btn.configure(bg=lighten(_apply_bg, 18)) if str(self._path_apply_btn["state"]) != "disabled" else None)
        self._path_apply_btn.bind("<Leave>", lambda e: self._path_apply_btn.configure(bg=_apply_bg))
        self._path_apply_btn.pack(side=RIGHT)

        # Apply 버튼 활성/비활성: Entry가 비어있으면 비활성
        self._path_var.trace_add("write", self._on_path_var_change)
        self._on_path_var_change()  # 초기 상태 설정

        # ── 최근 프로젝트 quick select ──
        self._recent_row = Frame(proj_card, bg=card_bg)
        self._recent_row.pack(fill=X, pady=(4, 0))
        self._refresh_recent_buttons()

        # ── 제어 패널 ──
        ctrl_bar = Frame(content, bg="#0e0e14")
        ctrl_bar.pack(fill=X, pady=(0, 8))

        def make_ctrl_btn(parent: Frame, text: str, cmd, color: str = btn_bg,
                          fg_color: str = btn_fg) -> Button:
            hover_bg = lighten(color, 18)
            press_bg = lighten(color, 30)
            btn = Button(
                parent, text=text, command=cmd, font=ctrl_font,
                bg=color, fg=fg_color, activebackground=press_bg,
                activeforeground="#ffffff", bd=0, padx=14, pady=6,
                highlightthickness=1, highlightbackground="#36364a",
                disabledforeground="#404050", cursor="hand2",
            )
            # hover 피드백
            btn.bind("<Enter>", lambda e, b=btn, h=hover_bg: b.configure(bg=h) if str(b["state"]) != "disabled" else None)
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c) if str(b["state"]) != "disabled" else None)
            return btn

        self.btn_setup = make_ctrl_btn(ctrl_bar, "⚙ SETUP", self._on_setup_check)
        self.btn_setup.pack(side=LEFT, padx=(0, 4))
        self.btn_start = make_ctrl_btn(ctrl_bar, "▶ START", self._on_start, "#1a3a1a", "#4ade80")
        self.btn_start.pack(side=LEFT, padx=4)
        self.btn_stop = make_ctrl_btn(ctrl_bar, "■ STOP", self._on_stop, "#3a1a1a", "#f87171")
        self.btn_stop.pack(side=LEFT, padx=4)
        self.btn_restart = make_ctrl_btn(ctrl_bar, "↻ RESTART", self._on_restart)
        self.btn_restart.pack(side=LEFT, padx=4)
        self.btn_attach = make_ctrl_btn(ctrl_bar, "⬜ ATTACH", self._on_attach)
        self.btn_attach.pack(side=LEFT, padx=4)

        self._action_in_progress = False

        # ── 상태 개요 + 최신 파일 ──
        overview = Frame(content, bg=bg)
        overview.pack(fill=X, pady=(0, 10))

        system_card = make_card(overview)
        system_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 6))
        Label(system_card, text="SYSTEM", font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")
        self.pipeline_var = StringVar(value="Pipeline: —")
        self.watcher_var = StringVar(value="Watcher: —")
        self.setup_var = StringVar(value="Setup: … Checking")
        self.pipeline_state_label = Label(system_card, textvariable=self.pipeline_var, font=body_font, bg=card_bg, fg=fg, anchor="w")
        self.pipeline_state_label.pack(anchor="w", pady=(6, 2))
        self.watcher_state_label = Label(system_card, textvariable=self.watcher_var, font=body_font, bg=card_bg, fg=fg, anchor="w")
        self.watcher_state_label.pack(anchor="w", pady=(0, 2))
        self.setup_state_label = Label(system_card, textvariable=self.setup_var, font=body_font, bg=card_bg, fg="#e0a040", anchor="w")
        self.setup_state_label.pack(anchor="w")

        file_card = make_card(overview)
        file_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(6, 0))
        self._artifacts_title_var = StringVar(value="ARTIFACTS")
        Label(file_card, textvariable=self._artifacts_title_var, font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")
        self.work_var = StringVar(value="Latest work: —")
        self.verify_var = StringVar(value="Latest verify: —")
        # current run context
        self._run_context_var = StringVar(value="")
        self._run_context_label = Label(file_card, textvariable=self._run_context_var, font=small_font,
                                         bg=card_bg, fg="#5b9cf6", anchor="w", justify=LEFT, wraplength=400)
        self._run_context_label.pack(anchor="w", pady=(4, 4))
        self._work_label = Label(file_card, textvariable=self.work_var, font=body_font, bg=card_bg, fg="#c0a060", anchor="w", justify=LEFT, wraplength=400)
        self._work_label.pack(anchor="w", pady=(0, 2))
        self._verify_label = Label(file_card, textvariable=self.verify_var, font=body_font, bg=card_bg, fg="#c0a060", anchor="w", justify=LEFT, wraplength=400)
        self._verify_label.pack(anchor="w")

        # ── Agent 상태 ──
        agent_section = Frame(content, bg=bg)
        agent_section.pack(fill=X, pady=(0, 8))
        Label(agent_section, text="AGENTS", font=section_font, bg=bg, fg=sub_fg).pack(anchor="w", pady=(0, 4))

        cards_row = Frame(agent_section, bg=bg)
        cards_row.pack(fill=X)

        agent_card_bg = "#12121a"
        self.agent_labels: list[tuple[Frame, Label, Label, Label, Label]] = []
        for idx, name in enumerate(["Claude", "Codex", "Gemini"]):
            card = Frame(
                cards_row,
                bg=agent_card_bg,
                padx=10,
                pady=8,
                highlightthickness=2,
                highlightbackground="#1e1e2e",
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 3, 0 if idx == 2 else 3))
            cards_row.grid_columnconfigure(idx, weight=1, uniform="agents")

            name_row = Frame(card, bg=agent_card_bg)
            name_row.pack(fill=X)
            dot = Label(name_row, text="●", font=body_font, bg=agent_card_bg, fg="#404058")
            dot.pack(side=LEFT)
            name_lbl = Label(name_row, text=name.upper(), font=section_font, bg=agent_card_bg, fg="#8890a8")
            name_lbl.pack(side=LEFT, padx=(6, 0))

            status_lbl = Label(card, text="—", font=status_font, bg=agent_card_bg, fg="#505068", anchor="w")
            status_lbl.pack(anchor="w", pady=(4, 1))
            note_lbl = Label(card, text="", font=small_font, bg=agent_card_bg, fg="#606878", anchor="w", justify=LEFT, wraplength=250)
            note_lbl.pack(anchor="w")
            quota_lbl = Label(card, text="", font=small_font, bg=agent_card_bg, fg="#505868", anchor="w", justify=LEFT, wraplength=250)
            quota_lbl.pack(anchor="w", pady=(2, 0))
            self.agent_labels.append((card, dot, status_lbl, note_lbl, quota_lbl))

            for widget in (card, name_row, dot, name_lbl, status_lbl, note_lbl, quota_lbl):
                widget.bind("<Button-1>", lambda _event, agent=name: self._select_agent(agent))
                widget.configure(cursor="hand2")

        # ── 하단 2영역: agent output + watcher log ──
        from tkinter import PanedWindow, VERTICAL

        paned = PanedWindow(content, orient=VERTICAL, bg="#222222", sashwidth=4, sashrelief="flat")
        paned.pack(fill=BOTH, expand=True)
        self.paned = paned

        # ── 선택 agent 상세 출력 (콘솔 패널) ──
        focus_frame = Frame(paned, bg=log_bg, padx=0, pady=0,
                            highlightthickness=1, highlightbackground="#1e1e30")

        focus_header = Frame(focus_frame, bg="#12121c", padx=10, pady=5)
        focus_header.pack(fill=X)
        Label(focus_header, text="AGENT OUTPUT", font=section_font, bg="#12121c", fg="#5060a0").pack(side=LEFT)
        self.focus_title_var = StringVar(value="CLAUDE • pane tail")
        Label(focus_header, textvariable=self.focus_title_var, font=small_font, bg="#12121c", fg="#4a5070").pack(side=RIGHT)

        focus_font = tkfont.Font(family="Consolas", size=9)
        self.focus_text = Text(
            focus_frame, font=focus_font, bg=log_bg, fg="#a0a8c0",
            wrap=WORD, bd=0, highlightthickness=0, padx=12, pady=8,
            state=DISABLED, spacing1=0, spacing3=1,
        )
        focus_scroll = TtkScrollbar(focus_frame, command=self.focus_text.yview, style="Dark.Vertical.TScrollbar")
        self.focus_text.configure(yscrollcommand=focus_scroll.set)
        focus_scroll.pack(side=RIGHT, fill=Y)
        self.focus_text.pack(side=LEFT, fill=BOTH, expand=True)

        paned.add(focus_frame, minsize=140, stretch="always")

        # ── Watcher log (콘솔 패널) ──
        log_frame = Frame(paned, bg=log_bg, padx=0, pady=0,
                          highlightthickness=1, highlightbackground="#1e1e30")

        log_header = Frame(log_frame, bg="#12121c", padx=10, pady=5)
        log_header.pack(fill=X)
        self._log_title_var = StringVar(value="WATCHER LOG")
        Label(log_header, textvariable=self._log_title_var, font=section_font, bg="#12121c", fg="#5060a0").pack(side=LEFT)

        self.log_text = Text(log_frame, font=small_font, bg=log_bg, fg="#707898",
                             wrap=WORD, bd=0, highlightthickness=0, padx=12, pady=6,
                             state=DISABLED)
        scrollbar = TtkScrollbar(log_frame, command=self.log_text.yview, style="Dark.Vertical.TScrollbar")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        paned.add(log_frame, minsize=100, stretch="never")
        # 초기 sash: focus 75% / log 25%
        self.root.update_idletasks()
        paned_h = paned.winfo_height()
        if paned_h > 240:
            paned.sash_place(0, 0, int(paned_h * 0.75))

        # ── Guide 모드 화면 (상단 Home/Guide 전환으로 표시) ──
        gf = self._guide_frame

        guide_header = Frame(gf, bg=card_bg, padx=12, pady=8,
                             highlightthickness=1, highlightbackground=card_border)
        guide_header.pack(fill=X, pady=(0, 10))
        Label(guide_header, text="Project Guide", font=section_font, bg=card_bg, fg=sub_fg).pack(side=LEFT)
        self._guide_status_var = StringVar(value="")
        Label(guide_header, textvariable=self._guide_status_var, font=small_font,
              bg=card_bg, fg="#34d399").pack(side=RIGHT)
        _export_bg = "#2563eb"
        _export_btn = Button(
            guide_header, text="  Export .md  ", command=self._export_guide_md,
            font=tkfont.Font(family="Consolas", size=10, weight="bold"),
            bg=_export_bg, fg="#ffffff",
            activebackground="#1d4ed8", activeforeground="#ffffff",
            bd=0, padx=14, pady=5,
            highlightthickness=1, highlightbackground="#3b82f6",
            cursor="hand2",
        )
        _export_btn.bind("<Enter>", lambda e: _export_btn.configure(bg=lighten(_export_bg, 20)))
        _export_btn.bind("<Leave>", lambda e: _export_btn.configure(bg=_export_bg))
        _export_btn.pack(side=RIGHT, padx=(0, 8))

        guide_body = Frame(gf, bg=bg)
        guide_body.pack(fill=BOTH, expand=True)

        self._guide_text = Text(
            guide_body, font=body_font, bg="#1a1a1a", fg="#d4d4d8",
            wrap=WORD, bd=0,
            highlightthickness=1, highlightbackground="#333333",
            padx=10, pady=8, state=DISABLED,
            cursor="arrow",
        )
        guide_scroll = TtkScrollbar(guide_body, command=self._guide_text.yview, style="Dark.Vertical.TScrollbar")
        self._guide_text.configure(yscrollcommand=guide_scroll.set)
        guide_scroll.pack(side=RIGHT, fill=Y)
        self._guide_text.pack(side=LEFT, fill=BOTH, expand=True)

        # canonical guide 로드
        self._load_project_guide()

        # ── 상단 overlay toast banner ──
        self._toast_font = tkfont.Font(family="Consolas", size=10, weight="bold")
        self.msg_var = StringVar(value="")
        self.msg_label = Label(
            self.root,
            textvariable=self.msg_var,
            font=self._toast_font,
            bg="#1e3a5f",
            fg="#93c5fd",
            pady=8,
            padx=18,
            anchor="center",
            wraplength=700,
        )
        # 초기엔 숨김 — _show_toast에서 place로 표시
        self.msg_var.trace_add("write", self._on_toast_change)
        self.root.after(120, self._set_initial_pane_split)

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
                    status = "WORKING"
                    if not note:
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
        # 모든 버튼 비활성
        self.btn_setup.configure(state=DISABLED)
        self.btn_start.configure(state=DISABLED)
        self.btn_stop.configure(state=DISABLED)
        self.btn_restart.configure(state=DISABLED)
        self.btn_attach.configure(state=DISABLED)

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
                quota_lbl.configure(text=f"Quota: {quota}" if quota else "Quota: —", fg="#7c8798")
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

        # 버튼 enable/disable — 작업 중이면 전부 비활성
        if self._action_in_progress:
            self.btn_setup.configure(state=DISABLED)
            self.btn_start.configure(state=DISABLED)
            self.btn_stop.configure(state=DISABLED)
            self.btn_restart.configure(state=DISABLED)
            self.btn_attach.configure(state=DISABLED)
        else:
            self.btn_setup.configure(state=NORMAL)
            can_start = not session_ok and self._setup_state == "ready"
            self.btn_start.configure(state=NORMAL if can_start else DISABLED)
            self.btn_stop.configure(state=NORMAL if session_ok else DISABLED)
            self.btn_restart.configure(state=NORMAL if session_ok else DISABLED)
            self.btn_attach.configure(state=NORMAL if session_ok else DISABLED)

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
        """Background thread에서 main-thread messagebox를 호출하고 결과 대기."""
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
            script = APP_ROOT / "start-pipeline.sh"
            if not script.exists() and not IS_WINDOWS:
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
            msg = pipeline_stop(self.project, self._session_name)
            self.root.after(0, lambda: self._unlock_buttons(f"■ {msg}"))
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

    # ── 실행 ──

    def run(self) -> None:
        self.root.mainloop()

