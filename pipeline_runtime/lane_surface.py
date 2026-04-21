from __future__ import annotations

import subprocess
import time

_BASE_BUSY_MARKERS = (
    "working (",
    "working for ",
    "• working",
    "◦ working",
    "waiting for background",
    "background terminal",
    "inferring",
    "thinking with ",
    "discombobulating",
    "germinating",
    "flumoxing",
)
_ACTIVE_BUSY_MARKERS = (
    "waiting for background",
    "background terminal",
    "esc to interrupt",
    "esc to cancel",
    "thinking with ",
)

LANE_SURFACE_PROFILES = {
    "Claude": {
        "ready_markers": ("❯", "claude code", "bypass permissions"),
        "busy_markers": _BASE_BUSY_MARKERS + (
            "thinking",
            "without interrupting claude's current work",
        ),
    },
    "Codex": {
        "ready_markers": ("›", "openai codex", "tab to queue message", "context left"),
        "busy_markers": _BASE_BUSY_MARKERS + (
            "cascading",
            "lollygagging",
            "hashing",
            "leavering",
            "thinking",
            "esc to cancel",
        ),
    },
    "Gemini": {
        "ready_markers": ("type your message", "gemini cli", "workspace"),
        "busy_markers": _BASE_BUSY_MARKERS + (
            "thinking",
            "esc to cancel",
        ),
    },
}

READY_MARKERS = {
    lane_name: tuple(profile.get("ready_markers") or ())
    for lane_name, profile in LANE_SURFACE_PROFILES.items()
}
BUSY_MARKERS = tuple(
    dict.fromkeys(
        marker
        for profile in LANE_SURFACE_PROFILES.values()
        for marker in tuple(profile.get("busy_markers") or ())
    )
)


def busy_markers_for_lane(lane_name: str | None) -> tuple[str, ...]:
    if not lane_name:
        return BUSY_MARKERS
    profile = LANE_SURFACE_PROFILES.get(str(lane_name or ""))
    if not profile:
        return BUSY_MARKERS
    return tuple(profile.get("busy_markers") or ())


def capture_pane_text(pane_target: str) -> str:
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-pt", pane_target],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def wait_for_pane_settle(
    pane_target: str,
    timeout_sec: float = 12.0,
    quiet_sec: float = 1.0,
    poll_sec: float = 0.25,
) -> bool:
    deadline = time.time() + timeout_sec
    last_snapshot = None
    last_change_at = time.time()

    while time.time() < deadline:
        snapshot = capture_pane_text(pane_target)
        if snapshot != last_snapshot:
            last_snapshot = snapshot
            last_change_at = time.time()
        elif time.time() - last_change_at >= quiet_sec:
            return True
        time.sleep(poll_sec)
    return False


def _recent_nonempty_lines(text: str, *, limit: int) -> list[str]:
    return [line.strip().lower() for line in str(text or "").splitlines() if line.strip()][-limit:]


def line_looks_like_input_prompt(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return (
        stripped == ">"
        or stripped == "›"
        or stripped == "❯"
        or stripped.startswith("> ")
        or stripped.startswith("› ")
        or stripped.startswith("❯ ")
        or stripped.endswith("$")
    )


def pane_text_has_gemini_ready_prompt(text: str) -> bool:
    window = _recent_nonempty_lines(text, limit=12)
    if not window:
        return False
    has_type_your_message = any(
        line == "type your message"
        or line.startswith("type your message ")
        or "type your message" in line
        for line in window
    )
    has_workspace_hint = any(line == "workspace" or line.startswith("workspace ") for line in window)
    has_gemini_banner = any("gemini cli" in line for line in window)
    return has_type_your_message and (has_workspace_hint or has_gemini_banner)


def pane_text_has_busy_indicator(text: str, lane_name: str | None = None) -> bool:
    window = _recent_nonempty_lines(text, limit=18)
    if not window:
        return False
    busy_markers = tuple(marker.lower() for marker in busy_markers_for_lane(lane_name))
    busy_indices = [
        index
        for index, line in enumerate(window)
        if any(marker in line for marker in busy_markers)
    ]
    if not busy_indices:
        return False
    if any(any(marker in line for marker in _ACTIVE_BUSY_MARKERS) for line in window):
        return True
    prompt_indices = [
        index
        for index, line in enumerate(window)
        if line_looks_like_input_prompt(line)
    ]
    if prompt_indices and prompt_indices[-1] > busy_indices[-1]:
        return False
    return True


def pane_text_has_input_cursor(text: str) -> bool:
    lines = [line for line in str(text or "").strip().splitlines() if line.strip()]
    if not lines:
        return False
    for line in reversed(lines[-12:]):
        if line_looks_like_input_prompt(line):
            return True
    return pane_text_has_gemini_ready_prompt(text)


def pane_text_has_working_indicator(text: str) -> bool:
    return "• Working" in str(text or "")


def pane_text_is_idle(text: str, lane_name: str | None = None) -> bool:
    if not str(text or "").strip():
        return False
    return pane_text_has_input_cursor(text) and not pane_text_has_busy_indicator(text, lane_name)


def pane_text_has_codex_activity(text: str) -> bool:
    normalized = str(text or "")
    return "\n• " in normalized or normalized.lstrip().startswith("• ")


def pane_text_has_gemini_activity(text: str) -> bool:
    normalized = str(text or "")
    return (
        "\n✦ " in normalized
        or normalized.lstrip().startswith("✦ ")
        or "ReadFile" in normalized
        or "WriteFile" in normalized
        or "ReadManyFiles" in normalized
    )


def text_is_ready(lane_name: str, text: str) -> bool:
    markers = READY_MARKERS.get(str(lane_name or ""), ())
    lower = str(text or "").lower()
    if not lower.strip():
        return False
    return any(marker.lower() in lower for marker in markers)


def lines_match_markers(lines: list[str], markers: tuple[str, ...]) -> bool:
    if not lines:
        return False
    lowered = "\n".join(lines).lower()
    return any(marker.lower() in lowered for marker in markers)


def text_matches_markers(text: str, markers: tuple[str, ...]) -> bool:
    lower = str(text or "").lower()
    if not lower.strip():
        return False
    return any(marker.lower() in lower for marker in markers)


def tail_has_busy_indicator(text: str, lane_name: str | None = None) -> bool:
    return pane_text_has_busy_indicator(text, lane_name)


def tail_has_ready_indicator(lane_name: str, text: str) -> bool:
    return text_is_ready(lane_name, text)


def tail_surface_state(lane_name: str, text: str) -> str:
    trailing_lines = _recent_nonempty_lines(text, limit=12)
    if not trailing_lines:
        return ""
    ready_markers = tuple(marker.lower() for marker in READY_MARKERS.get(str(lane_name or ""), ()))
    if tail_has_busy_indicator(text, lane_name):
        return "WORKING"
    if any(any(marker in line for marker in ready_markers) for line in trailing_lines):
        return "READY"
    return ""
