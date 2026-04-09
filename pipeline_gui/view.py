"""UI constants, color scheme, font definitions, widget builders."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app import PipelineGUI

from tkinter import (
    Frame, Label, Button, Text, Entry, Checkbutton,
    StringVar, LEFT, RIGHT, BOTH, X, Y, END, WORD, DISABLED, NORMAL,
    font as tkfont,
    PanedWindow, VERTICAL,
)
from tkinter.ttk import Scrollbar as TtkScrollbar, Style as TtkStyle, Combobox as TtkCombobox

# ── Ops Console color scheme ──
BG = "#101014"
FG = "#d8dae0"
ACCENT = "#5b9cf6"
SUB_FG = "#6b7280"
BTN_BG = "#1c1c24"
BTN_FG = "#b0b4c0"
CARD_BG = "#16161e"
CARD_BORDER = "#26263a"
LOG_BG = "#0c0c10"
HEADER_BG = "#0a0a10"
AGENT_CARD_BG = "#12121a"

POLL_MS = 1000


def init_ttk_style() -> None:
    style = TtkStyle()
    style.theme_use("clam")
    style.configure("Dark.Vertical.TScrollbar",
                     background="#20202e", troughcolor=LOG_BG,
                     borderwidth=0, relief="flat", arrowcolor="#40405a")
    style.map("Dark.Vertical.TScrollbar",
              background=[("active", "#30304a"), ("pressed", "#3a3a50")])


def create_fonts() -> dict[str, tkfont.Font]:
    return {
        "title": tkfont.Font(family="Consolas", size=14, weight="bold"),
        "body": tkfont.Font(family="Consolas", size=10),
        "small": tkfont.Font(family="Consolas", size=9),
        "status": tkfont.Font(family="Consolas", size=11, weight="bold"),
        "section": tkfont.Font(family="Consolas", size=9, weight="bold"),
        "ctrl": tkfont.Font(family="Consolas", size=10, weight="bold"),
        "focus": tkfont.Font(family="Consolas", size=9),
        "toast": tkfont.Font(family="Consolas", size=10, weight="bold"),
    }


def make_card(parent: Frame, padx: int = 12, pady: int = 10) -> Frame:
    return Frame(parent, bg=CARD_BG, padx=padx, pady=pady,
                 highlightthickness=1, highlightbackground=CARD_BORDER)


def lighten(hex_color: str, amount: int = 20) -> str:
    hex_color = hex_color.lstrip("#")
    r = min(255, int(hex_color[0:2], 16) + amount)
    g = min(255, int(hex_color[2:4], 16) + amount)
    b = min(255, int(hex_color[4:6], 16) + amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def make_hover_btn(parent: Frame, text: str, cmd, font, color: str = BTN_BG,
                   fg_color: str = BTN_FG, **kw) -> Button:
    """Create a button with hover feedback."""
    hover_bg = lighten(color, 18)
    press_bg = lighten(color, 30)
    btn = Button(
        parent, text=text, command=cmd, font=font,
        bg=color, fg=fg_color, activebackground=press_bg,
        activeforeground="#ffffff", bd=0, cursor="hand2", **kw,
    )
    btn.bind("<Enter>", lambda e, b=btn, h=hover_bg: b.configure(bg=h) if str(b["state"]) != "disabled" else None)
    btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c) if str(b["state"]) != "disabled" else None)
    return btn


# ═══════════════════════════════════════════════════════════════
# Section builders — each takes the app instance and builds one UI section
# ═══════════════════════════════════════════════════════════════

def build_header(app: PipelineGUI) -> None:
    """Top console bar: title + mode tabs + status badge."""
    f = app._fonts
    top = Frame(app.root, bg=HEADER_BG, padx=16, pady=8)
    top.pack(fill=X)
    Frame(top, bg=ACCENT, width=3).pack(side=LEFT, fill=Y, padx=(0, 10))
    Label(top, text="PIPELINE 운영", font=f["title"], bg=HEADER_BG, fg="#8090b0").pack(side=LEFT)

    mode_frame = Frame(top, bg=HEADER_BG)
    mode_frame.pack(side=LEFT, padx=(24, 0))
    app._mode = "home"
    app._mode_btn_home = Button(
        mode_frame, text="운영", font=f["ctrl"],
        bg="#2a2a3a", fg="#d8dae0", activebackground="#3a3a4e", activeforeground="#ffffff",
        bd=0, padx=12, pady=3, highlightthickness=0, cursor="hand2",
        command=lambda: app._switch_mode("home"),
    )
    app._mode_btn_home.bind("<Enter>", lambda e: app._mode_btn_home.configure(bg="#363648"))
    app._mode_btn_home.bind("<Leave>", lambda e: app._mode_btn_home.configure(
        bg="#2a2a3a" if app._mode == "home" else "#18182a"))
    app._mode_btn_home.pack(side=LEFT, padx=(0, 2))
    app._mode_btn_guide = Button(
        mode_frame, text="가이드", font=f["ctrl"],
        bg="#18182a", fg="#6b7280", activebackground="#2a2a3a", activeforeground="#ffffff",
        bd=0, padx=12, pady=3, highlightthickness=0, cursor="hand2",
        command=lambda: app._switch_mode("guide"),
    )
    app._mode_btn_guide.bind("<Enter>", lambda e: app._mode_btn_guide.configure(bg="#363648"))
    app._mode_btn_guide.bind("<Leave>", lambda e: app._mode_btn_guide.configure(
        bg="#2a2a3a" if app._mode == "guide" else "#18182a"))
    app._mode_btn_guide.pack(side=LEFT)
    app._mode_btn_setup = Button(
        mode_frame, text="설정", font=f["ctrl"],
        bg="#18182a", fg="#6b7280", activebackground="#2a2a3a", activeforeground="#ffffff",
        bd=0, padx=12, pady=3, highlightthickness=0, cursor="hand2",
        command=lambda: app._switch_mode("setup"),
    )
    app._mode_btn_setup.bind("<Enter>", lambda e: app._mode_btn_setup.configure(bg="#363648"))
    app._mode_btn_setup.bind("<Leave>", lambda e: app._mode_btn_setup.configure(
        bg="#2a2a3a" if app._mode == "setup" else "#18182a"))
    app._mode_btn_setup.pack(side=LEFT, padx=(2, 0))

    app.status_var = StringVar(value="중지됨")
    app.status_label = Label(top, textvariable=app.status_var, font=f["ctrl"],
                              bg="#2a1015", fg="#f87171", padx=12, pady=3)
    app.status_label.pack(side=RIGHT)


def build_project_bar(app: PipelineGUI, content: Frame) -> None:
    """Project path entry + browse/apply + recent quick select."""
    from .platform import IS_WINDOWS, _wsl_path_str
    f = app._fonts
    proj_card = make_card(content)
    proj_card.pack(fill=X, pady=(0, 10))
    Label(proj_card, text="프로젝트", font=f["section"], bg=CARD_BG, fg=SUB_FG).pack(anchor="w")

    path_row = Frame(proj_card, bg=CARD_BG)
    path_row.pack(fill=X, pady=(4, 0))

    app._path_var = StringVar(
        value=_wsl_path_str(app.project) if IS_WINDOWS else str(app.project),
    )
    app._path_entry = Entry(
        path_row, textvariable=app._path_var, font=f["body"],
        bg="#1a1a1a", fg="#f59e0b", insertbackground="#f59e0b",
        bd=0, highlightthickness=1, highlightbackground="#444444", highlightcolor="#f59e0b",
    )
    app._path_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 6))
    app._path_entry.bind("<Return>", lambda _e: app._apply_project_path())

    app._path_browse_btn = make_hover_btn(
        path_row, "찾아보기…", app._on_browse, f["small"],
        padx=8, pady=4, highlightthickness=1, highlightbackground="#444444",
    )
    app._path_browse_btn.pack(side=RIGHT, padx=(4, 0))

    app._path_apply_btn = make_hover_btn(
        path_row, "적용", app._apply_project_path, f["small"],
        padx=10, pady=4, highlightthickness=1, highlightbackground="#444444",
        disabledforeground="#555555",
    )
    app._path_apply_btn.pack(side=RIGHT)

    app._path_var.trace_add("write", app._on_path_var_change)
    app._on_path_var_change()

    app._recent_row = Frame(proj_card, bg=CARD_BG)
    app._recent_row.pack(fill=X, pady=(4, 0))
    app._refresh_recent_buttons()


def build_control_bar(app: PipelineGUI, content: Frame) -> None:
    """Control panel buttons."""
    f = app._fonts
    ctrl_bar = Frame(content, bg="#0e0e14")
    ctrl_bar.pack(fill=X, pady=(0, 8))

    app.btn_setup = make_hover_btn(ctrl_bar, "⚙ 설정", app._open_setup_mode, f["ctrl"],
                                    padx=14, pady=6, highlightthickness=1, highlightbackground="#36364a",
                                    disabledforeground="#404050")
    app.btn_setup.pack(side=LEFT, padx=(0, 4))
    app.btn_start = make_hover_btn(ctrl_bar, "▶ 시작", app._on_start, f["ctrl"],
                                    color="#1a3a1a", fg_color="#4ade80",
                                    padx=14, pady=6, highlightthickness=1, highlightbackground="#36364a",
                                    disabledforeground="#404050")
    app.btn_start.pack(side=LEFT, padx=4)
    app.btn_stop = make_hover_btn(ctrl_bar, "■ 중지", app._on_stop, f["ctrl"],
                                   color="#3a1a1a", fg_color="#f87171",
                                   padx=14, pady=6, highlightthickness=1, highlightbackground="#36364a",
                                   disabledforeground="#404050")
    app.btn_stop.pack(side=LEFT, padx=4)
    app.btn_restart = make_hover_btn(ctrl_bar, "↻ 재시작", app._on_restart, f["ctrl"],
                                      padx=14, pady=6, highlightthickness=1, highlightbackground="#36364a",
                                      disabledforeground="#404050")
    app.btn_restart.pack(side=LEFT, padx=4)
    app.btn_attach = make_hover_btn(ctrl_bar, "⬜ 연결", app._on_attach, f["ctrl"],
                                     padx=14, pady=6, highlightthickness=1, highlightbackground="#36364a",
                                     disabledforeground="#404050")
    app.btn_attach.pack(side=LEFT, padx=4)
    app._action_in_progress = False


def build_status_panels(app: PipelineGUI, content: Frame) -> None:
    """System + Artifacts overview cards."""
    f = app._fonts
    overview = Frame(content, bg=BG)
    overview.pack(fill=X, pady=(0, 10))

    system_card = make_card(overview)
    system_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 6))
    Label(system_card, text="시스템", font=f["section"], bg=CARD_BG, fg=SUB_FG).pack(anchor="w")
    app.pipeline_var = StringVar(value="파이프라인: —")
    app.watcher_var = StringVar(value="워처: —")
    app.poll_var = StringVar(value="폴링: —")
    app.setup_var = StringVar(value="설정: … 점검 중")
    app.pipeline_state_label = Label(system_card, textvariable=app.pipeline_var, font=f["body"], bg=CARD_BG, fg=FG, anchor="w")
    app.pipeline_state_label.pack(anchor="w", pady=(6, 2))
    app.watcher_state_label = Label(system_card, textvariable=app.watcher_var, font=f["body"], bg=CARD_BG, fg=FG, anchor="w")
    app.watcher_state_label.pack(anchor="w", pady=(0, 2))
    app.poll_state_label = Label(system_card, textvariable=app.poll_var, font=f["small"], bg=CARD_BG, fg="#6b7280", anchor="w")
    app.poll_state_label.pack(anchor="w", pady=(0, 2))
    app.setup_state_label = Label(system_card, textvariable=app.setup_var, font=f["body"], bg=CARD_BG, fg="#e0a040", anchor="w")
    app.setup_state_label.pack(anchor="w")
    app._runtime_launch_label = Label(
        system_card,
        textvariable=app._runtime_launch_var,
        font=f["small"],
        bg=CARD_BG,
        fg="#d8dae0",
        anchor="w",
        justify=LEFT,
        wraplength=360,
    )
    app._runtime_launch_label.pack(anchor="w", pady=(4, 0))

    control_group = Frame(system_card, bg=CARD_BG)
    control_group.pack(fill=X, pady=(8, 0))

    app.active_control_box = Frame(
        control_group,
        bg="#101826",
        padx=8,
        pady=6,
        highlightthickness=1,
        highlightbackground="#1d4ed8",
    )
    app.active_control_box.pack(fill=X)
    app.active_control_title_label = Label(
        app.active_control_box,
        text="ACTIVE CONTROL",
        font=f["section"],
        bg="#101826",
        fg="#60a5fa",
        anchor="w",
    )
    app.active_control_title_label.pack(anchor="w")
    app.active_control_var = StringVar(value="활성 제어: —")
    app.active_control_label = Label(
        app.active_control_box,
        textvariable=app.active_control_var,
        font=f["small"],
        bg="#101826",
        fg="#93c5fd",
        anchor="w",
        justify=LEFT,
        wraplength=360,
    )
    app.active_control_label.pack(anchor="w", pady=(4, 0))

    app.stale_control_box = Frame(
        control_group,
        bg="#14161d",
        padx=8,
        pady=6,
        highlightthickness=1,
        highlightbackground="#374151",
    )
    app.stale_control_title_label = Label(
        app.stale_control_box,
        text="INACTIVE / STALE",
        font=f["section"],
        bg="#14161d",
        fg="#94a3b8",
        anchor="w",
    )
    app.stale_control_title_label.pack(anchor="w")
    app.stale_control_var = StringVar(value="")
    app.stale_control_label = Label(
        app.stale_control_box,
        textvariable=app.stale_control_var,
        font=f["small"],
        bg="#14161d",
        fg="#94a3b8",
        anchor="w",
        justify=LEFT,
        wraplength=360,
    )
    app.stale_control_label.pack(anchor="w", pady=(4, 0))
    app._stale_control_box_visible = False

    file_card = make_card(overview)
    file_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(6, 0))
    app._artifacts_title_var = StringVar(value="산출물")
    Label(file_card, textvariable=app._artifacts_title_var, font=f["section"], bg=CARD_BG, fg=SUB_FG).pack(anchor="w")
    app.work_var = StringVar(value="최신 work: —")
    app.verify_var = StringVar(value="최신 verify: —")
    app._run_context_var = StringVar(value="")
    app._run_context_label = Label(file_card, textvariable=app._run_context_var, font=f["small"],
                                    bg=CARD_BG, fg=ACCENT, anchor="w", justify=LEFT, wraplength=400)
    app._run_context_label.pack(anchor="w", pady=(4, 4))
    app._work_label = Label(file_card, textvariable=app.work_var, font=f["body"], bg=CARD_BG, fg="#c0a060", anchor="w", justify=LEFT, wraplength=400)
    app._work_label.pack(anchor="w", pady=(0, 2))
    app._verify_label = Label(file_card, textvariable=app.verify_var, font=f["body"], bg=CARD_BG, fg="#c0a060", anchor="w", justify=LEFT, wraplength=400)
    app._verify_label.pack(anchor="w")


def build_agent_cards(app: PipelineGUI, content: Frame) -> None:
    """Three agent status cards: Claude, Codex, Gemini."""
    f = app._fonts
    agent_section = Frame(content, bg=BG)
    agent_section.pack(fill=X, pady=(0, 8))
    Label(agent_section, text="에이전트", font=f["section"], bg=BG, fg=SUB_FG).pack(anchor="w", pady=(0, 4))

    cards_row = Frame(agent_section, bg=BG)
    cards_row.pack(fill=X)

    app.agent_labels = []
    for idx, name in enumerate(["Claude", "Codex", "Gemini"]):
        card = Frame(cards_row, bg=AGENT_CARD_BG, padx=10, pady=8,
                     highlightthickness=2, highlightbackground="#1e1e2e")
        card.grid(row=0, column=idx, sticky="nsew",
                  padx=(0 if idx == 0 else 3, 0 if idx == 2 else 3))
        cards_row.grid_columnconfigure(idx, weight=1, uniform="agents")

        name_row = Frame(card, bg=AGENT_CARD_BG)
        name_row.pack(fill=X)
        dot = Label(name_row, text="●", font=f["body"], bg=AGENT_CARD_BG, fg="#404058")
        dot.pack(side=LEFT)
        name_lbl = Label(name_row, text=name.upper(), font=f["section"], bg=AGENT_CARD_BG, fg="#8890a8")
        name_lbl.pack(side=LEFT, padx=(6, 0))

        status_lbl = Label(card, text="—", font=f["status"], bg=AGENT_CARD_BG, fg="#505068", anchor="w")
        status_lbl.pack(anchor="w", pady=(4, 1))
        note_lbl = Label(card, text="", font=f["small"], bg=AGENT_CARD_BG, fg="#606878", anchor="w", justify=LEFT, wraplength=250)
        note_lbl.pack(anchor="w")
        quota_lbl = Label(card, text="", font=f["small"], bg=AGENT_CARD_BG, fg="#505868", anchor="w", justify=LEFT, wraplength=250)
        quota_lbl.pack(anchor="w", pady=(2, 0))
        app.agent_labels.append((card, dot, status_lbl, note_lbl, quota_lbl))

        for widget in (card, name_row, dot, name_lbl, status_lbl, note_lbl, quota_lbl):
            widget.bind("<Button-1>", lambda _event, agent=name: app._select_agent(agent))
            widget.configure(cursor="hand2")


def build_token_panel(app: PipelineGUI, content: Frame) -> None:
    """Token overview panel with read-only metrics and maintenance actions."""
    f = app._fonts
    token_card = make_card(content)
    token_card.pack(fill=X, pady=(0, 8))
    header = Frame(token_card, bg=CARD_BG)
    header.pack(fill=X)
    Label(header, text="토큰", font=f["section"], bg=CARD_BG, fg=SUB_FG).pack(side=LEFT)
    app._token_status_var = StringVar(value="수집기: —")
    Label(header, textvariable=app._token_status_var, font=f["small"], bg=CARD_BG, fg="#7080a0").pack(side=RIGHT)

    actions_row = Frame(token_card, bg=CARD_BG)
    actions_row.pack(fill=X, pady=(6, 2))
    app.btn_token_backfill = make_hover_btn(
        actions_row, "전체 히스토리", app._on_token_backfill, f["small"],
        padx=10, pady=4, highlightthickness=1, highlightbackground="#3a3a54",
        disabledforeground="#555566",
    )
    app.btn_token_backfill.pack(side=LEFT, padx=(0, 6))
    app.btn_token_rebuild = make_hover_btn(
        actions_row, "DB 재구성", app._on_token_rebuild, f["small"],
        color="#2a1a1a", fg_color="#fca5a5",
        padx=10, pady=4, highlightthickness=1, highlightbackground="#4a3030",
        disabledforeground="#6a4a4a",
    )
    app.btn_token_rebuild.pack(side=LEFT)

    app._token_totals_var = StringVar(value="오늘: —")
    totals_lbl = Label(token_card, textvariable=app._token_totals_var, font=f["body"], bg=CARD_BG, fg="#d8dae0",
                       anchor="w", justify=LEFT, wraplength=860)
    totals_lbl.pack(anchor="w", pady=(6, 2))

    app._token_agents_var = StringVar(value="에이전트: —")
    agents_lbl = Label(token_card, textvariable=app._token_agents_var, font=f["small"], bg=CARD_BG, fg="#8fa0b8",
                       anchor="w", justify=LEFT, wraplength=860)
    agents_lbl.pack(anchor="w", pady=(0, 2))

    app._token_selected_var = StringVar(value="선택 에이전트: —")
    selected_lbl = Label(token_card, textvariable=app._token_selected_var, font=f["small"], bg=CARD_BG, fg="#9eb3c7",
                         anchor="w", justify=LEFT, wraplength=860)
    selected_lbl.pack(anchor="w", pady=(0, 2))

    app._token_jobs_var = StringVar(value="주요 작업: —")
    jobs_lbl = Label(token_card, textvariable=app._token_jobs_var, font=f["small"], bg=CARD_BG, fg="#7c8798",
                     anchor="w", justify=LEFT, wraplength=860)
    jobs_lbl.pack(anchor="w")

    app._token_action_var = StringVar(value="작업: —")
    action_lbl = Label(token_card, textvariable=app._token_action_var, font=f["small"], bg=CARD_BG, fg="#6e85a8",
                       anchor="w", justify=LEFT, wraplength=860)
    action_lbl.pack(anchor="w", pady=(4, 0))


def build_console_panels(app: PipelineGUI, content: Frame) -> None:
    """Agent output pane + watcher log pane (PanedWindow) + Guide mode + toast."""
    f = app._fonts

    paned = PanedWindow(content, orient=VERTICAL, bg="#222222", sashwidth=4, sashrelief="flat")
    paned.pack(fill=BOTH, expand=True)
    app.paned = paned

    # Agent output
    focus_frame = Frame(paned, bg=LOG_BG, padx=0, pady=0,
                        highlightthickness=1, highlightbackground="#1e1e30")
    fh = Frame(focus_frame, bg="#12121c", padx=10, pady=5)
    fh.pack(fill=X)
    Label(fh, text="에이전트 출력", font=f["section"], bg="#12121c", fg="#5060a0").pack(side=LEFT)
    app.focus_title_var = StringVar(value="CLAUDE • 최근 pane 출력")
    Label(fh, textvariable=app.focus_title_var, font=f["small"], bg="#12121c", fg="#4a5070").pack(side=RIGHT)
    app.focus_text = Text(
        focus_frame, font=f["focus"], bg=LOG_BG, fg="#a0a8c0",
        wrap=WORD, bd=0, highlightthickness=0, padx=12, pady=8,
        state=DISABLED, spacing1=0, spacing3=1,
    )
    fs = TtkScrollbar(focus_frame, command=app.focus_text.yview, style="Dark.Vertical.TScrollbar")
    app.focus_text.configure(yscrollcommand=fs.set)
    fs.pack(side=RIGHT, fill=Y)
    app.focus_text.pack(side=LEFT, fill=BOTH, expand=True)
    paned.add(focus_frame, minsize=140, stretch="always")

    # Watcher log
    log_frame = Frame(paned, bg=LOG_BG, padx=0, pady=0,
                      highlightthickness=1, highlightbackground="#1e1e30")
    lh = Frame(log_frame, bg="#12121c", padx=10, pady=5)
    lh.pack(fill=X)
    app._log_title_var = StringVar(value="워처 로그")
    Label(lh, textvariable=app._log_title_var, font=f["section"], bg="#12121c", fg="#5060a0").pack(side=LEFT)
    app.log_text = Text(log_frame, font=f["small"], bg=LOG_BG, fg="#707898",
                         wrap=WORD, bd=0, highlightthickness=0, padx=12, pady=6, state=DISABLED)
    ls = TtkScrollbar(log_frame, command=app.log_text.yview, style="Dark.Vertical.TScrollbar")
    app.log_text.configure(yscrollcommand=ls.set)
    ls.pack(side=RIGHT, fill=Y)
    app.log_text.pack(side=LEFT, fill=BOTH, expand=True)
    paned.add(log_frame, minsize=100, stretch="never")

    app.root.update_idletasks()
    ph = paned.winfo_height()
    if ph > 240:
        paned.sash_place(0, 0, int(ph * 0.75))

    # Guide mode
    gf = app._guide_frame
    gh = Frame(gf, bg=CARD_BG, padx=12, pady=8, highlightthickness=1, highlightbackground=CARD_BORDER)
    gh.pack(fill=X, pady=(0, 10))
    Label(gh, text="프로젝트 가이드", font=f["section"], bg=CARD_BG, fg=SUB_FG).pack(side=LEFT)
    app._guide_status_var = StringVar(value="")
    Label(gh, textvariable=app._guide_status_var, font=f["small"], bg=CARD_BG, fg="#34d399").pack(side=RIGHT)
    export_btn = make_hover_btn(gh, "  .md 내보내기  ", app._export_guide_md, f["ctrl"],
                                 color="#2563eb", fg_color="#ffffff",
                                 padx=14, pady=5, highlightthickness=1, highlightbackground="#3b82f6")
    export_btn.pack(side=RIGHT, padx=(0, 8))

    gb = Frame(gf, bg=BG)
    gb.pack(fill=BOTH, expand=True)
    app._guide_text = Text(gb, font=f["body"], bg="#1a1a1a", fg="#d4d4d8",
                            wrap=WORD, bd=0, highlightthickness=1, highlightbackground="#333333",
                            padx=10, pady=8, state=DISABLED, cursor="arrow")
    gs = TtkScrollbar(gb, command=app._guide_text.yview, style="Dark.Vertical.TScrollbar")
    app._guide_text.configure(yscrollcommand=gs.set)
    gs.pack(side=RIGHT, fill=Y)
    app._guide_text.pack(side=LEFT, fill=BOTH, expand=True)
    app._load_project_guide()

    # Toast
    app._toast_font = f["toast"]
    app.msg_var = StringVar(value="")
    app.msg_label = Label(app.root, textvariable=app.msg_var, font=app._toast_font,
                           bg="#1e3a5f", fg="#93c5fd", pady=8, padx=18,
                           anchor="center", wraplength=700)
    app.msg_var.trace_add("write", app._on_toast_change)
    app.root.after(120, app._set_initial_pane_split)


def build_setup_panels(app: PipelineGUI) -> None:
    """Setup mode screen: left inputs, right derived state/preview."""
    f = app._fonts
    root = app._setup_frame

    outer = Frame(root, bg=BG)
    outer.pack(fill=BOTH, expand=True)
    outer.grid_columnconfigure(0, weight=1, uniform="setup")
    outer.grid_columnconfigure(1, weight=1, uniform="setup")
    outer.grid_rowconfigure(0, weight=1)

    left = make_card(outer)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    right = make_card(outer)
    right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

    Label(left, text="설정 입력", font=f["section"], bg=CARD_BG, fg=SUB_FG).pack(anchor="w")
    Label(
        left,
        text="에이전트 선택, 역할 바인딩, 옵션, 실행자 지정을 다룹니다.",
        font=f["small"],
        bg=CARD_BG,
        fg="#7c8798",
        anchor="w",
        justify=LEFT,
    ).pack(anchor="w", pady=(4, 8))

    # Agent selection
    Label(left, text="에이전트 선택", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    agent_row = Frame(left, bg=CARD_BG)
    agent_row.pack(fill=X, pady=(4, 0))
    for idx, name in enumerate(("Claude", "Codex", "Gemini")):
        cb = Checkbutton(
            agent_row,
            text=name,
            variable=app._setup_agent_vars[name],
            command=app._on_setup_agent_change,
            bg=CARD_BG,
            fg=FG,
            activebackground=CARD_BG,
            activeforeground="#ffffff",
            selectcolor="#1a1a24",
            highlightthickness=0,
            bd=0,
            font=f["body"],
        )
        cb.grid(row=0, column=idx, sticky="w", padx=(0, 18))
    Label(left, textvariable=app._setup_agent_error_var, font=f["small"], bg=CARD_BG, fg="#f87171",
          anchor="w", justify=LEFT, wraplength=420).pack(anchor="w", pady=(2, 8))

    # Role bindings
    Label(left, text="역할 바인딩", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    role_block = Frame(left, bg=CARD_BG)
    role_block.pack(fill=X, pady=(4, 0))
    app._setup_bind_implement_combo = _setup_combo_row(
        role_block, "구현 역할", app._setup_implement_var, app._on_setup_role_change, f, 0,
    )
    Label(role_block, textvariable=app._setup_implement_error_var, font=f["small"], bg=CARD_BG, fg="#f87171",
          anchor="w", justify=LEFT, wraplength=420).grid(row=1, column=0, sticky="w", pady=(2, 6))
    app._setup_bind_verify_combo = _setup_combo_row(
        role_block, "검증 역할", app._setup_verify_var, app._on_setup_role_change, f, 2,
    )
    Label(role_block, textvariable=app._setup_verify_error_var, font=f["small"], bg=CARD_BG, fg="#f87171",
          anchor="w", justify=LEFT, wraplength=420).grid(row=3, column=0, sticky="w", pady=(2, 6))
    app._setup_bind_advisory_combo = _setup_combo_row(
        role_block, "자문 역할", app._setup_advisory_var, app._on_setup_role_change, f, 4,
    )
    Label(role_block, textvariable=app._setup_advisory_error_var, font=f["small"], bg=CARD_BG, fg="#f87171",
          anchor="w", justify=LEFT, wraplength=420).grid(row=5, column=0, sticky="w", pady=(2, 10))

    # Options
    Label(left, text="옵션", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    option_block = Frame(left, bg=CARD_BG)
    option_block.pack(fill=X, pady=(4, 0))
    for idx, (label, var_name, handler) in enumerate((
        ("자문 lane 사용", "_setup_advisory_enabled_var", app._on_setup_option_change),
        ("operator 중지 사용", "_setup_operator_stop_enabled_var", app._on_setup_option_change),
        ("세션 중재 사용", "_setup_session_arbitration_var", app._on_setup_option_change),
        ("자체 검증 허용", "_setup_self_verify_var", app._on_setup_option_change),
        ("자체 자문 허용", "_setup_self_advisory_var", app._on_setup_option_change),
    )):
        cb = Checkbutton(
            option_block,
            text=label,
            variable=getattr(app, var_name),
            command=handler,
            bg=CARD_BG,
            fg=FG,
            activebackground=CARD_BG,
            activeforeground="#ffffff",
            selectcolor="#1a1a24",
            highlightthickness=0,
            bd=0,
            font=f["body"],
        )
        cb.grid(row=idx, column=0, sticky="w", pady=(0, 2))
        setattr(app, f"_setup_option_cb_{idx}", cb)

    # Executor
    Label(left, text="실행자 지정", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w", pady=(10, 0))
    exec_block = Frame(left, bg=CARD_BG)
    exec_block.pack(fill=X, pady=(4, 0))
    Label(exec_block, text="설정 실행자", font=f["body"], bg=CARD_BG, fg=FG).grid(row=0, column=0, sticky="w")
    app._setup_executor_combo = TtkCombobox(
        exec_block,
        textvariable=app._setup_executor_var,
        state="readonly",
        font=f["body"],
        width=26,
    )
    app._setup_executor_combo.bind("<<ComboboxSelected>>", app._on_setup_executor_change)
    app._setup_executor_combo.grid(row=1, column=0, sticky="ew", pady=(4, 0))
    exec_block.grid_columnconfigure(0, weight=1)

    # Actions
    actions = Frame(left, bg=CARD_BG)
    actions.pack(fill=X, pady=(14, 0))
    app.btn_setup_save_draft = make_hover_btn(
        actions, "초안 저장", app._on_setup_save_draft, f["ctrl"],
        padx=12, pady=6, highlightthickness=1, highlightbackground="#36364a",
        disabledforeground="#404050",
    )
    app.btn_setup_save_draft.pack(side=LEFT, padx=(0, 6))
    app.btn_setup_generate_preview = make_hover_btn(
        actions, "미리보기 생성", app._on_setup_generate_preview, f["ctrl"],
        padx=12, pady=6, highlightthickness=1, highlightbackground="#36364a",
        disabledforeground="#404050",
    )
    app.btn_setup_generate_preview.pack(side=LEFT, padx=(0, 6))
    app.btn_setup_apply = make_hover_btn(
        actions, "적용", app._on_setup_apply, f["ctrl"],
        color="#1a3a1a", fg_color="#4ade80",
        padx=12, pady=6, highlightthickness=1, highlightbackground="#36364a",
        disabledforeground="#404050",
    )
    app.btn_setup_apply.pack(side=LEFT, padx=(0, 6))
    app.btn_setup_clean_staged = make_hover_btn(
        actions, "staged 정리", app._on_setup_clean_staged, f["ctrl"],
        padx=12, pady=6, highlightthickness=1, highlightbackground="#36364a",
        disabledforeground="#404050",
    )
    app.btn_setup_clean_staged.pack(side=LEFT)

    # Right pane
    Label(right, text="설정 해석", font=f["section"], bg=CARD_BG, fg=SUB_FG).pack(anchor="w")
    Label(
        right,
        text="초안 지원 수준과 현재 실행 프로필, 유효성 요약, 미리보기 요약, 적용 준비 상태를 보여줍니다.",
        font=f["small"],
        bg=CARD_BG,
        fg="#7c8798",
        anchor="w",
        justify=LEFT,
    ).pack(anchor="w", pady=(4, 8))

    Label(right, text="설정 상태", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    app._setup_mode_state_label = Label(
        right, textvariable=app._setup_mode_state_var, font=f["status"], bg=CARD_BG, fg="#5b9cf6", anchor="w"
    )
    app._setup_mode_state_label.pack(anchor="w", pady=(4, 10))

    Label(right, text="초안 지원 수준", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    app._setup_support_label = Label(
        right, textvariable=app._setup_support_level_var, font=f["body"], bg=CARD_BG, fg="#d8dae0",
        anchor="w", justify=LEFT, wraplength=420,
    )
    app._setup_support_label.pack(anchor="w", pady=(4, 10))

    Label(right, text="실행 프로필", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    app._setup_runtime_profile_label = Label(
        right, textvariable=app._setup_runtime_profile_var, font=f["body"], bg=CARD_BG, fg="#d8dae0",
        anchor="w", justify=LEFT, wraplength=420,
    )
    app._setup_runtime_profile_label.pack(anchor="w", pady=(4, 10))

    Label(right, text="유효성 요약", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    app._setup_validation_label = Label(
        right, textvariable=app._setup_validation_var, font=f["small"], bg=CARD_BG, fg="#d8dae0",
        anchor="w", justify=LEFT, wraplength=420,
    )
    app._setup_validation_label.pack(anchor="w", pady=(4, 10))

    Label(right, text="미리보기 요약", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    app._setup_preview_label = Label(
        right, textvariable=app._setup_preview_summary_var, font=f["small"], bg=CARD_BG, fg="#d8dae0",
        anchor="w", justify=LEFT, wraplength=420,
    )
    app._setup_preview_label.pack(anchor="w", pady=(4, 10))

    Label(right, text="현재 setup ID", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    app._setup_current_setup_id_label = Label(
        right, textvariable=app._setup_current_setup_id_var, font=f["small"], bg=CARD_BG, fg="#d8dae0",
        anchor="w", justify=LEFT, wraplength=420,
    )
    app._setup_current_setup_id_label.pack(anchor="w", pady=(4, 10))

    Label(right, text="현재 preview fingerprint", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    app._setup_current_preview_fingerprint_label = Label(
        right, textvariable=app._setup_current_preview_fingerprint_var, font=f["small"], bg=CARD_BG, fg="#d8dae0",
        anchor="w", justify=LEFT, wraplength=420,
    )
    app._setup_current_preview_fingerprint_label.pack(anchor="w", pady=(4, 10))

    Label(right, text="적용 준비 상태", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    app._setup_apply_readiness_label = Label(
        right, textvariable=app._setup_apply_readiness_var, font=f["small"], bg=CARD_BG, fg="#d8dae0",
        anchor="w", justify=LEFT, wraplength=420,
    )
    app._setup_apply_readiness_label.pack(anchor="w", pady=(4, 10))

    Label(right, text="정리 기록", font=f["section"], bg=CARD_BG, fg="#8fa0b8").pack(anchor="w")
    app._setup_cleanup_summary_label = Label(
        right, textvariable=app._setup_cleanup_summary_var, font=f["small"], bg=CARD_BG, fg="#d8dae0",
        anchor="w", justify=LEFT, wraplength=420,
    )
    app._setup_cleanup_summary_label.pack(anchor="w", pady=(4, 10))

    app._setup_restart_notice_label = Label(
        right, textvariable=app._setup_restart_notice_var, font=f["small"], bg=CARD_BG, fg="#f59e0b",
        anchor="w", justify=LEFT, wraplength=420,
    )
    app._setup_restart_notice_label.pack(anchor="w", pady=(0, 6))
    app.btn_setup_restart_now = make_hover_btn(
        right, "지금 재시작", app._on_setup_confirm_restart, f["ctrl"],
        color="#4b2e14", fg_color="#f59e0b",
        padx=12, pady=6, highlightthickness=1, highlightbackground="#36364a",
        disabledforeground="#404050",
    )
    app.btn_setup_restart_now.pack(anchor="w")


def _setup_combo_row(parent: Frame, label: str, variable: StringVar, handler, fonts: dict[str, tkfont.Font], row: int) -> TtkCombobox:
    Label(parent, text=label, font=fonts["body"], bg=CARD_BG, fg=FG).grid(row=row, column=0, sticky="w")
    combo = TtkCombobox(
        parent,
        textvariable=variable,
        state="readonly",
        font=fonts["body"],
        width=26,
    )
    combo.bind("<<ComboboxSelected>>", handler)
    combo.grid(row=row + 1, column=0, sticky="ew", pady=(4, 0))
    parent.grid_columnconfigure(0, weight=1)
    return combo
