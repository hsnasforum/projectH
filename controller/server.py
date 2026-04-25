"""Pipeline Controller API backed by runtime supervisor status."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import time
from base64 import b64encode
from dataclasses import asdict
from hashlib import sha1
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from controller.monitor import RuntimeMonitorStateManager
from config.runtime_hosts import (
    browser_host_for_bind,
    resolve_bind_host,
    running_in_wsl,
    windows_fallback_host,
)
from pipeline_gui.backend import (
    confirm_pipeline_start as backend_confirm_pipeline_start,
    normalize_runtime_status,
    pipeline_start as backend_pipeline_start,
    pipeline_stop as backend_pipeline_stop,
    read_runtime_status,
    runtime_capture_tail as backend_runtime_capture_tail,
    runtime_send_input as backend_runtime_send_input,
)
from pipeline_gui.project import _session_name_for
from pipeline_gui.setup_profile import resolve_project_runtime_adapter
from pipeline_gui.token_queries import load_token_dashboard

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parent.parent))
CONTROLLER_DIR = Path(__file__).parent
CONTROLLER_PORT = int(os.environ.get("CONTROLLER_PORT", "8780"))
_MONITOR_STREAM_INTERVAL_SEC = 1.0
_WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_KNOWN_LANE_NAMES = ("Claude", "Codex", "Gemini")
_DEFAULT_ROLE_OWNERS = {
    "implement": "Claude",
    "verify": "Codex",
    "advisory": "Gemini",
}
_USAGE_SOURCE_BY_AGENT = {
    "Claude": "claude",
    "Codex": "codex",
    "Gemini": "gemini",
}


def _running_in_wsl() -> bool:
    return running_in_wsl()


def _controller_bind_host() -> str:
    return resolve_bind_host(explicit_host=os.environ.get("CONTROLLER_HOST"))


def _controller_browser_host(bind_host: str) -> str:
    return browser_host_for_bind(bind_host)


def _controller_windows_fallback_host() -> str | None:
    return windows_fallback_host()


CONTROLLER_HOST = _controller_bind_host()
SESSION_NAME = _session_name_for(PROJECT_ROOT)
_MONITOR_STATE_MANAGER = RuntimeMonitorStateManager(
    PROJECT_ROOT,
    agent_names=_KNOWN_LANE_NAMES,
    source_by_agent=_USAGE_SOURCE_BY_AGENT,
)


def _runtime_role_metadata() -> dict:
    try:
        adapter = resolve_project_runtime_adapter(PROJECT_ROOT)
    except Exception:
        adapter = {}

    ready_profile = isinstance(adapter, dict) and str(adapter.get("resolution_state") or "") == "ready"
    raw_role_owners = dict(adapter.get("role_owners") or {}) if isinstance(adapter, dict) else {}
    raw_prompt_owners = dict(adapter.get("prompt_owners") or {}) if isinstance(adapter, dict) else {}
    raw_enabled_lanes = list(adapter.get("enabled_lanes") or []) if isinstance(adapter, dict) else []

    role_owners: dict[str, str] = {}
    prompt_owners: dict[str, str] = {}
    for role, default_owner in _DEFAULT_ROLE_OWNERS.items():
        role_owner = str(raw_role_owners.get(role) or "").strip()
        prompt_owner = str(raw_prompt_owners.get(role) or "").strip()
        if role_owner not in _KNOWN_LANE_NAMES:
            role_owner = "" if ready_profile else default_owner
        if prompt_owner not in _KNOWN_LANE_NAMES:
            prompt_owner = role_owner or ("" if ready_profile else default_owner)
        role_owners[role] = role_owner
        prompt_owners[role] = prompt_owner

    enabled_lanes = [name for name in raw_enabled_lanes if str(name) in _KNOWN_LANE_NAMES]
    if not enabled_lanes:
        enabled_lanes = list(_KNOWN_LANE_NAMES)

    return {
        "role_owners": role_owners,
        "prompt_owners": prompt_owners,
        "enabled_lanes": enabled_lanes,
    }


def _resolve_controller_asset(rel_path: str) -> tuple[Path | None, str | None]:
    requested = str(rel_path or "").strip().lstrip("/")
    if not requested:
        return None, None
    if requested.startswith("css/"):
        asset_root = (CONTROLLER_DIR / "css").resolve()
        local = requested[len("css/"):]
    elif requested.startswith("js/"):
        asset_root = (CONTROLLER_DIR / "js").resolve()
        local = requested[len("js/"):]
    else:
        asset_root = (CONTROLLER_DIR / "assets").resolve()
        local = requested
    candidate = (asset_root / local).resolve()
    try:
        candidate.relative_to(asset_root)
    except ValueError:
        return None, None
    if not candidate.is_file():
        return None, None
    content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
    return candidate, content_type


def _runtime_status_or_placeholder() -> dict:
    status = normalize_runtime_status(read_runtime_status(PROJECT_ROOT))
    if status:
        return {**status, "project_root": str(PROJECT_ROOT), **_runtime_role_metadata()}
    return {
        "schema_version": 1,
        "backend_type": "tmux",
        "project_root": str(PROJECT_ROOT),
        **_runtime_role_metadata(),
        "run_id": "",
        "current_run_id": "",
        "runtime_state": "STOPPED",
        "degraded_reason": "",
        "degraded_reasons": [],
        "automation_health": "ok",
        "automation_reason_code": "",
        "automation_incident_family": "",
        "automation_next_action": "continue",
        "automation_health_detail": "",
        "control_age_cycles": 0,
        "stale_control_seq": False,
        "stale_control_cycle_threshold": 0,
        "stale_advisory_pending": False,
        "autonomy": {
            "mode": "normal",
            "block_reason": "",
            "first_seen_at": "",
            "suppress_operator_until": "",
            "operator_eligible": False,
            "same_fingerprint_retries": 0,
            "last_self_heal_at": "",
            "last_self_triage_at": "",
        },
        "control": {
            "active_control_file": "",
            "active_control_seq": -1,
            "active_control_status": "none",
            "active_control_updated_at": "",
        },
        "lanes": [],
        "active_round": None,
        "last_receipt": None,
        "last_receipt_id": "",
        "watcher": {"alive": False, "pid": None},
        "artifacts": {
            "latest_work": {"path": "—", "mtime": 0.0},
            "latest_verify": {"path": "—", "mtime": 0.0},
        },
        "compat": {
            "control_slots": {"active": None, "stale": []},
            "turn_state": None,
        },
        "last_heartbeat_at": "",
        "updated_at": "",
    }


def _normalize_capture_tail_text(text: str) -> str:
    normalized = str(text or "")
    normalized = re.sub(
        r"([^\n])(\[Pasted Content \d+ chars\])",
        r"\1\n\2",
        normalized,
    )
    normalized = re.sub(
        r"(\[Pasted Content \d+ chars\])(?=\[Pasted Content \d+ chars\])",
        r"\1\n",
        normalized,
    )
    return normalized


def get_runtime_status() -> tuple[dict, HTTPStatus]:
    status = normalize_runtime_status(read_runtime_status(PROJECT_ROOT))
    if not status:
        return _runtime_status_or_placeholder(), HTTPStatus.OK
    return {**status, "project_root": str(PROJECT_ROOT), **_runtime_role_metadata()}, HTTPStatus.OK


def pipeline_start() -> dict:
    start_requested_at = time.time()
    start_result = backend_pipeline_start(PROJECT_ROOT, SESSION_NAME)
    if start_result != "시작 요청됨":
        return {"ok": False, "error": start_result}
    ok, message = backend_confirm_pipeline_start(
        PROJECT_ROOT,
        SESSION_NAME,
        start_requested_at=start_requested_at,
        action_label="시작",
    )
    if ok:
        return {"ok": True, "message": message}
    return {"ok": False, "error": message}


def pipeline_stop() -> dict:
    try:
        stop_result = backend_pipeline_stop(PROJECT_ROOT, SESSION_NAME)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    if stop_result == "중지 완료":
        return {"ok": True}
    return {"ok": False, "error": stop_result}


def pipeline_restart() -> dict:
    stopped = pipeline_stop()
    if not stopped.get("ok"):
        return stopped
    time.sleep(1)
    return pipeline_start()


def runtime_capture_tail(lane: str | None = None, *, lines: int = 120) -> tuple[dict, HTTPStatus]:
    lane_name = str(lane or "").strip()
    if not lane_name:
        return {"ok": False, "error": "lane is required"}, HTTPStatus.BAD_REQUEST
    text = backend_runtime_capture_tail(PROJECT_ROOT, SESSION_NAME, lane_name, lines=lines)
    return {
        "ok": True,
        "lane": lane_name,
        "lines": int(lines),
        "text": _normalize_capture_tail_text(text),
    }, HTTPStatus.OK


def runtime_send_input(lane: str | None = None, *, text: str = "") -> tuple[dict, HTTPStatus]:
    lane_name = str(lane or "").strip()
    payload = str(text or "")
    if not lane_name:
        return {"ok": False, "error": "lane is required"}, HTTPStatus.BAD_REQUEST
    if not payload.strip():
        return {"ok": False, "error": "text is required"}, HTTPStatus.BAD_REQUEST
    ok = backend_runtime_send_input(PROJECT_ROOT, SESSION_NAME, lane_name, text=payload)
    if not ok:
        return {"ok": False, "error": "failed to send input"}, HTTPStatus.BAD_GATEWAY
    return {
        "ok": True,
        "lane": lane_name,
        "text": payload,
    }, HTTPStatus.OK


def _now_epoch_ms() -> int:
    return int(time.time() * 1000)


def _load_dashboard_payload() -> tuple[dict, str]:
    try:
        return asdict(load_token_dashboard(PROJECT_ROOT, top_n=5)), ""
    except Exception as exc:
        return {
            "display_day": "",
            "collector_status": {"available": False, "phase": "error", "last_error": str(exc)},
            "today_totals": {},
            "agent_totals": [],
            "top_jobs": [],
        }, str(exc)


def runtime_monitor_snapshot() -> dict:
    runtime_status, _status = get_runtime_status()
    dashboard_payload, usage_error = _load_dashboard_payload()
    return _MONITOR_STATE_MANAGER.snapshot(
        runtime_status=runtime_status,
        dashboard_payload=dashboard_payload,
        usage_error=usage_error,
    )


def runtime_agent_inspector(agent: str | None = None, *, lines: int = 160) -> tuple[dict, HTTPStatus]:
    agent_name = str(agent or "").strip()
    if agent_name not in _KNOWN_LANE_NAMES:
        return {"ok": False, "error": "unknown agent"}, HTTPStatus.BAD_REQUEST
    runtime_status, _status = get_runtime_status()
    dashboard_payload, _usage_error = _load_dashboard_payload()
    tail_text = backend_runtime_capture_tail(PROJECT_ROOT, SESSION_NAME, agent_name, lines=lines)
    payload = _MONITOR_STATE_MANAGER.inspector_payload(
        agent_name=agent_name,
        runtime_status=runtime_status,
        dashboard_payload=dashboard_payload,
        tail_text=_normalize_capture_tail_text(tail_text),
    )
    return payload, HTTPStatus.OK


def _websocket_accept_key(raw_key: str) -> str:
    digest = sha1((raw_key + _WEBSOCKET_GUID).encode("ascii")).digest()
    return b64encode(digest).decode("ascii")


def _websocket_text_frame(payload: dict) -> bytes:
    body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    size = len(body)
    if size < 126:
        header = bytes([0x81, size])
    elif size <= 0xFFFF:
        header = bytes([0x81, 126]) + size.to_bytes(2, "big")
    else:
        header = bytes([0x81, 127]) + size.to_bytes(8, "big")
    return header + body


class ControllerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/ws/runtime/monitor":
            self._serve_monitor_websocket()
            return

        if parsed.path.startswith("/controller-assets/"):
            rel_path = parsed.path[len("/controller-assets/") :]
            self._serve_controller_asset(rel_path)
            return

        if parsed.path == "/api/runtime/status":
            data, status = get_runtime_status()
            self._json(data, status)
            return

        if parsed.path == "/api/runtime/monitor-snapshot":
            self._json(runtime_monitor_snapshot())
            return

        if parsed.path == "/api/runtime/agent-inspector":
            query = parse_qs(parsed.query or "")
            agent = (query.get("agent") or [None])[0]
            raw_lines = (query.get("lines") or ["160"])[0]
            try:
                lines = max(20, min(400, int(raw_lines)))
            except ValueError:
                lines = 160
            data, status = runtime_agent_inspector(agent=agent, lines=lines)
            self._json(data, status)
            return

        if parsed.path == "/api/runtime/capture-tail":
            lane = (parse_qs(parsed.query or "").get("lane") or [None])[0]
            raw_lines = (parse_qs(parsed.query or "").get("lines") or ["120"])[0]
            try:
                lines = max(1, min(400, int(raw_lines)))
            except ValueError:
                lines = 120
            data, status = runtime_capture_tail(lane=lane, lines=lines)
            self._json(data, status)
            return

        if parsed.path in ("/", "/controller", "/controller/"):
            self._serve_html()
            return

        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/runtime/start":
            self._json(pipeline_start())
            return
        if parsed.path == "/api/runtime/stop":
            self._json(pipeline_stop())
            return
        if parsed.path == "/api/runtime/restart":
            self._json(pipeline_restart())
            return
        if parsed.path == "/api/runtime/send-input":
            content_length = int(self.headers.get("Content-Length") or "0")
            try:
                raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                self._json({"ok": False, "error": "invalid json"}, HTTPStatus.BAD_REQUEST)
                return
            if not isinstance(payload, dict):
                self._json({"ok": False, "error": "invalid json"}, HTTPStatus.BAD_REQUEST)
                return
            data, status = runtime_send_input(
                lane=payload.get("lane"),
                text=str(payload.get("text") or ""),
            )
            self._json(data, status)
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
        html_path = CONTROLLER_DIR / "index.html"
        if not html_path.exists():
            self._json({"error": "index.html not found"}, HTTPStatus.NOT_FOUND)
            return
        body = html_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_controller_asset(self, rel_path: str) -> None:
        asset_path, content_type = _resolve_controller_asset(rel_path)
        if asset_path is None or content_type is None:
            self._json({"error": "asset not found"}, HTTPStatus.NOT_FOUND)
            return
        body = asset_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _serve_monitor_websocket(self) -> None:
        upgrade = str(self.headers.get("Upgrade") or "").lower()
        key = str(self.headers.get("Sec-WebSocket-Key") or "").strip()
        if upgrade != "websocket" or not key:
            self._json({"ok": False, "error": "websocket upgrade required"}, HTTPStatus.BAD_REQUEST)
            return
        self.send_response(HTTPStatus.SWITCHING_PROTOCOLS)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", _websocket_accept_key(key))
        self.end_headers()
        self.close_connection = True
        while True:
            try:
                self.wfile.write(_websocket_text_frame(runtime_monitor_snapshot()))
                self.wfile.flush()
                time.sleep(_MONITOR_STREAM_INTERVAL_SEC)
            except OSError:
                break

    def log_message(self, fmt, *args) -> None:
        pass


def main() -> None:
    browser_host = _controller_browser_host(CONTROLLER_HOST)
    fallback_host = _controller_windows_fallback_host()
    print(f"Pipeline Controller: http://{browser_host}:{CONTROLLER_PORT}/controller")
    print(f"  Project: {PROJECT_ROOT}")
    print(f"  Runtime API: http://{browser_host}:{CONTROLLER_PORT}/api/runtime/status")
    if CONTROLLER_HOST != browser_host:
        print(f"  Bind: {CONTROLLER_HOST}:{CONTROLLER_PORT} (WSL -> Windows 브라우저 접근용)")
    if fallback_host and fallback_host != browser_host:
        print(f"  Windows fallback: http://{fallback_host}:{CONTROLLER_PORT}/controller")
    server = ThreadingHTTPServer((CONTROLLER_HOST, CONTROLLER_PORT), ControllerHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nController 종료")
        server.shutdown()


if __name__ == "__main__":
    main()
