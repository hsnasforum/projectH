"""Pipeline Controller API — 최소 vertical slice.

tmux 백엔드를 그대로 유지하면서 상태 조회 + 제어 엔드포인트를 제공합니다.
"""

from __future__ import annotations

import json
import subprocess
import os
import signal
import time
import datetime as dt
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parent.parent))
PIPELINE_DIR = PROJECT_ROOT / ".pipeline"
CONTROLLER_PORT = int(os.environ.get("CONTROLLER_PORT", "8780"))
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

# Session name: pipeline-gui.py / start-pipeline.sh / watcher_core.py와 동일 규칙
_SESSION_PREFIX = "aip"


def _session_name_for_project(project: Path) -> str:
    """aip-<safe-dirname> — 전체 파이프라인과 동일한 deterministic session name."""
    name = project.resolve().name or "default"
    safe = re.sub(r"[^A-Za-z0-9_-]", "", name)
    return f"{_SESSION_PREFIX}-{safe}" if safe else f"{_SESSION_PREFIX}-default"


SESSION_NAME = _session_name_for_project(PROJECT_ROOT)
WATCHER_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")


# ── tmux 헬퍼 ─────────────────────────────────────────────────

def _run(cmd: list[str], timeout: float = 5.0) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def tmux_session_exists() -> bool:
    return bool(_run(["tmux", "has-session", "-t", SESSION_NAME]) == "" and
                subprocess.run(["tmux", "has-session", "-t", SESSION_NAME],
                               capture_output=True).returncode == 0)


def tmux_list_panes() -> list[dict]:
    raw = _run([
        "tmux", "list-panes", "-t", SESSION_NAME, "-F",
        "#{pane_id}\t#{pane_index}\t#{pane_current_command}\t#{pane_pid}\t#{pane_dead}",
    ])
    panes = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) >= 5:
            panes.append({
                "pane_id": parts[0],
                "index": int(parts[1]),
                "command": parts[2],
                "pid": int(parts[3]) if parts[3].isdigit() else 0,
                "dead": parts[4] == "1",
            })
    return panes


def tmux_capture_pane(pane_id: str, lines: int = 240) -> str:
    """Capture pane text and rejoin wrapped lines for wide display."""
    raw = _run(["tmux", "capture-pane", "-p", "-J", "-t", pane_id, "-S", f"-{lines}"])
    if not raw:
        return raw
    # -J handles soft-wraps, but narrow panes still produce short hard-wrapped lines.
    # Rejoin lines that were split mid-sentence: if a line doesn't end with a
    # "natural break" character and the next line doesn't start with a bullet/prompt,
    # merge them into one continuous line.
    result_lines: list[str] = []
    for line in raw.split("\n"):
        stripped = line.rstrip()
        if not result_lines:
            result_lines.append(stripped)
            continue
        prev = result_lines[-1]
        # Natural break: empty line, ends with punctuation, or next line starts with
        # a structural marker (bullet, prompt, heading, box drawing, etc.)
        is_natural_break = (
            not prev
            or prev.endswith((".", "!", "?", ":", ")", "]", "}", "─", "│", "┘", "┐", "┤", "┴"))
            or stripped.startswith(("•", "─", "│", "┌", "└", "├", "›", ">", "$", "#", "-", "*", "✓", "✗"))
            or stripped.startswith(("  •", "  -", "  *", "  ✓"))
            or not stripped  # empty next line
        )
        if is_natural_break:
            result_lines.append(stripped)
        else:
            # Merge: continuation of previous line
            result_lines[-1] = prev + " " + stripped.lstrip()
    return "\n".join(result_lines)


def watcher_alive() -> dict:
    pid_path = PIPELINE_DIR / "experimental.pid"
    if not pid_path.exists():
        return {"alive": False, "pid": None}
    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, 0)
        return {"alive": True, "pid": pid}
    except (ValueError, OSError):
        return {"alive": False, "pid": None}


def format_elapsed(seconds: float) -> str:
    total = max(0, int(seconds))
    mins, secs = divmod(total, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


# ── 파이프라인 상태 슬롯 ───────────────────────────────────────

def read_slot(name: str) -> dict:
    path = PIPELINE_DIR / name
    if not path.exists():
        return {"exists": False, "status": None, "preview": None, "mtime": None}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        status = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("STATUS:"):
                status = stripped.split(":", 1)[1].strip()
                break
        mtime = path.stat().st_mtime
        preview = text[:500]
        return {"exists": True, "status": status, "preview": preview, "mtime": mtime}
    except OSError:
        return {"exists": False, "status": None, "preview": None, "mtime": None}


# ── Agent 상태 추론 ────────────────────────────────────────────

AGENT_ROLES = [
    {"name": "Claude", "role": "implementer", "pane_index": 0},
    {"name": "Codex", "role": "verifier", "pane_index": 1},
    {"name": "Gemini", "role": "arbiter", "pane_index": 2},
]


def detect_agent_status(pane_text: str) -> str:
    if not pane_text.strip():
        return "off"
    lines = [l.strip() for l in pane_text.strip().splitlines() if l.strip()]
    if not lines:
        return "off"
    lower = pane_text.lower()
    if (
        "working (" in lower
        or "background terminal" in lower
        or "waiting for background" in lower
        or "waited for background" in lower
        or "cascading" in lower
        or "lollygagging" in lower
        or "hashing" in lower
        or "leavering" in lower
        or "without interrupting claude's current work" in lower
        or "flumoxing" in lower
        or "philosophising" in lower
        or "sautéed" in lower
    ):
        return "working"
    last = lines[-1]
    if "openai codex" in lower or "› " in pane_text:
        return "ready"
    if "claude code" in lower or "bypass permissions" in lower or "❯" in pane_text:
        return "ready"
    if "gemini cli" in lower or "type your message" in lower or "workspace" in lower:
        return "ready"
    if last.rstrip().endswith("$"):
        return "off"
    return "booting"


def extract_working_note(lines: list[str]) -> str:
    for line in reversed(lines[-80:]):
        match = re.search(r"Working \(([^)]*)", line, re.IGNORECASE)
        if match:
            note = match.group(1).split("•", 1)[0].strip(" )…")
            if note:
                return note
        match = re.search(r"Cascading(?:…|\.{3})\s*\(([^)]*)", line, re.IGNORECASE)
        if match:
            return match.group(1).strip(" )…")
        match = re.search(r"Lollygagging(?:…|\.{3})\s*\(([^)]*)", line, re.IGNORECASE)
        if match:
            return match.group(1).strip(" )…")
        lowered = line.lower()
        if "background terminal" in lowered or "waiting for background" in lowered:
            return "bg-task"
    return ""


def watcher_runtime_hints() -> dict[str, tuple[str, str]]:
    log_path = PIPELINE_DIR / "logs" / "experimental" / "watcher.log"
    if not log_path.exists():
        return {}
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-300:]
    except OSError:
        return {}

    claude_started_at = None
    claude_done = False
    codex_started_at = None
    codex_done = False
    gemini_started_at = None
    gemini_done = False

    for line in lines:
        ts_match = WATCHER_TS_RE.match(line)
        if not ts_match:
            continue
        try:
            timestamp = dt.datetime.fromisoformat(ts_match.group(1)).timestamp()
        except ValueError:
            continue

        if "notify_claude" in line or ("send-keys" in line and "pane_type=claude" in line) or "waiting_for_claude" in line:
            claude_started_at = timestamp
            claude_done = False
        elif "claude activity detected" in line or ("new job:" in line and claude_started_at is not None):
            claude_done = True

        if "lease acquired: slot=slot_verify" in line or "dispatching codex prompt" in line or "VERIFY_PENDING → VERIFY_RUNNING" in line:
            codex_started_at = timestamp
            codex_done = False
        elif "codex task completed" in line or "lease released: slot=slot_verify" in line or "VERIFY_RUNNING → VERIFY_DONE" in line:
            codex_done = True

        if "notify_gemini" in line or "gemini response activity" in line:
            gemini_started_at = timestamp
            gemini_done = False
        elif "gemini advice updated" in line:
            gemini_done = True

    hints = {}
    now = time.time()
    if claude_started_at is not None and not claude_done:
        hints["Claude"] = ("working", format_elapsed(now - claude_started_at))
    elif claude_done:
        hints["Claude"] = ("ready", "")
    if codex_started_at is not None and not codex_done:
        hints["Codex"] = ("working", format_elapsed(now - codex_started_at))
    elif codex_done:
        hints["Codex"] = ("ready", "")
    if gemini_started_at is not None and not gemini_done:
        hints["Gemini"] = ("working", format_elapsed(now - gemini_started_at))
    elif gemini_done:
        hints["Gemini"] = ("ready", "")
    return hints


def get_full_state() -> dict:
    session_alive = tmux_session_exists()
    panes = tmux_list_panes() if session_alive else []
    hints = watcher_runtime_hints()

    agents = []
    for agent_def in AGENT_ROLES:
        pane = next((p for p in panes if p["index"] == agent_def["pane_index"]), None)
        pane_text = ""
        status = "off"
        status_note = ""
        if pane and not pane["dead"]:
            pane_text = tmux_capture_pane(pane["pane_id"])
            status = detect_agent_status(pane_text)
            lines = [ANSI_RE.sub("", l).strip() for l in pane_text.splitlines() if l.strip()]
            if status == "working":
                status_note = extract_working_note(lines)
        elif pane and pane["dead"]:
            status = "dead"

        hint = hints.get(agent_def["name"])
        if hint:
            hint_status, hint_note = hint
            if hint_status == "working":
                status = "working"
                if not status_note:
                    status_note = hint_note
            elif hint_status == "ready" and status == "booting":
                status = "ready"

        agents.append({
            "name": agent_def["name"],
            "role": agent_def["role"],
            "status": status,
            "status_note": status_note,
            "pane_id": pane["pane_id"] if pane else None,
            "pane_text": pane_text[-20000:] if pane_text else "",  # 최근 20000자
        })

    return {
        "project_root": str(PROJECT_ROOT),
        "session_alive": session_alive,
        "watcher": watcher_alive(),
        "agents": agents,
        "slots": {
            "claude_handoff": read_slot("claude_handoff.md"),
            "operator_request": read_slot("operator_request.md"),
            "gemini_request": read_slot("gemini_request.md"),
            "gemini_advice": read_slot("gemini_advice.md"),
        },
    }


# ── 파이프라인 제어 ────────────────────────────────────────────

def pipeline_start() -> dict:
    script = PROJECT_ROOT / "start-pipeline.sh"
    if not script.exists():
        return {"ok": False, "error": "start-pipeline.sh not found"}
    # 백그라운드로 실행 (tmux attach 제외 — 마지막 줄 스킵)
    subprocess.Popen(
        ["bash", "-c", f"sed '$d' '{script}' | bash -s '{PROJECT_ROOT}' --mode experimental"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return {"ok": True}


def pipeline_stop() -> dict:
    script = PROJECT_ROOT / "stop-pipeline.sh"
    if not script.exists():
        return {"ok": False, "error": "stop-pipeline.sh not found"}
    subprocess.run(["bash", str(script), str(PROJECT_ROOT)],
                   capture_output=True, timeout=15)
    return {"ok": True}


def pipeline_restart() -> dict:
    pipeline_stop()
    import time
    time.sleep(2)
    return pipeline_start()


# ── HTTP 핸들러 ────────────────────────────────────────────────

class ControllerHandler(BaseHTTPRequestHandler):

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/state":
            self._json(get_full_state())
            return

        if parsed.path == "/api/health":
            self._json({"ok": True})
            return

        if parsed.path in ("/", "/controller", "/controller/"):
            self._serve_html()
            return

        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/start":
            self._json(pipeline_start())
            return
        if parsed.path == "/api/stop":
            self._json(pipeline_stop())
            return
        if parsed.path == "/api/restart":
            self._json(pipeline_restart())
            return

        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def _json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_html(self) -> None:
        html_path = Path(__file__).parent / "index.html"
        if not html_path.exists():
            self._json({"error": "index.html not found"}, HTTPStatus.NOT_FOUND)
            return
        body = html_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args) -> None:
        pass  # 조용히


def main() -> None:
    print(f"Pipeline Controller: http://127.0.0.1:{CONTROLLER_PORT}/controller")
    print(f"  Project: {PROJECT_ROOT}")
    print(f"  API: http://127.0.0.1:{CONTROLLER_PORT}/api/state")
    server = ThreadingHTTPServer(("127.0.0.1", CONTROLLER_PORT), ControllerHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nController 종료")
        server.shutdown()


if __name__ == "__main__":
    main()
