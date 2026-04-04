"""UI constants, color scheme, font definitions, widget helpers."""
from __future__ import annotations

from tkinter import Frame, font as tkfont
from tkinter.ttk import Style as TtkStyle

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
    """Initialize ttk dark scrollbar style. Call once after Tk() creation."""
    style = TtkStyle()
    style.theme_use("clam")
    style.configure("Dark.Vertical.TScrollbar",
                     background="#20202e", troughcolor=LOG_BG,
                     borderwidth=0, relief="flat", arrowcolor="#40405a")
    style.map("Dark.Vertical.TScrollbar",
              background=[("active", "#30304a"), ("pressed", "#3a3a50")])


def create_fonts() -> dict[str, tkfont.Font]:
    """Create and return named font dict."""
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
    """Create a dark panel card."""
    return Frame(
        parent, bg=CARD_BG, padx=padx, pady=pady,
        highlightthickness=1, highlightbackground=CARD_BORDER,
    )


def lighten(hex_color: str, amount: int = 20) -> str:
    """Lighten a hex color by amount per channel."""
    hex_color = hex_color.lstrip("#")
    r = min(255, int(hex_color[0:2], 16) + amount)
    g = min(255, int(hex_color[2:4], 16) + amount)
    b = min(255, int(hex_color[4:6], 16) + amount)
    return f"#{r:02x}{g:02x}{b:02x}"
