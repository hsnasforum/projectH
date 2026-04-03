"""Pipeline Controller API — 최소 vertical slice.

tmux 백엔드를 그대로 유지하면서 상태 조회 + 제어 엔드포인트를 제공합니다.
"""

from __future__ import annotations

import json
import subprocess
import os
import signal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parent.parent))
PIPELINE_DIR = PROJECT_ROOT / ".pipeline"
SESSION_NAME = "ai-pipeline"
CONTROLLER_PORT = int(os.environ.get("CONTROLLER_PORT", "8780"))


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
    last = lines[-1]
    # Working indicators
    if "Working" in pane_text or "Flumoxing" in pane_text or "thinking" in pane_text.lower():
        return "working"
    if "• Explored" in pane_text or "• Ran " in pane_text or "• Read " in pane_text:
        return "working"
    # Idle indicators
    if last.startswith("›") or last.endswith(">") or "> " in last:
        return "idle"
    if last.rstrip().endswith("$"):
        return "off"
    return "unknown"


def get_full_state() -> dict:
    session_alive = tmux_session_exists()
    panes = tmux_list_panes() if session_alive else []

    agents = []
    for agent_def in AGENT_ROLES:
        pane = next((p for p in panes if p["index"] == agent_def["pane_index"]), None)
        pane_text = ""
        status = "off"
        if pane and not pane["dead"]:
            pane_text = tmux_capture_pane(pane["pane_id"])
            status = detect_agent_status(pane_text)
        elif pane and pane["dead"]:
            status = "dead"

        agents.append({
            "name": agent_def["name"],
            "role": agent_def["role"],
            "status": status,
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
