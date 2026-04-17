from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import config.runtime_hosts as runtime_hosts
import controller.server as controller_server


class ControllerServerHostTests(unittest.TestCase):
    def test_bind_host_defaults_to_localhost_outside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=False):
            with mock.patch.dict(os.environ, {}, clear=False):
                self.assertEqual(controller_server._controller_bind_host(), "127.0.0.1")

    def test_bind_host_defaults_to_all_interfaces_inside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=True):
            with mock.patch.dict(os.environ, {}, clear=False):
                self.assertEqual(controller_server._controller_bind_host(), "0.0.0.0")

    def test_bind_host_respects_explicit_override(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=True):
            with mock.patch.dict(os.environ, {"CONTROLLER_HOST": "127.0.0.1"}, clear=False):
                self.assertEqual(controller_server._controller_bind_host(), "127.0.0.1")

    def test_browser_host_uses_localhost_for_all_interfaces_bind(self) -> None:
        self.assertEqual(controller_server._controller_browser_host("0.0.0.0"), "127.0.0.1")
        self.assertEqual(controller_server._controller_browser_host("127.0.0.1"), "127.0.0.1")

    def test_windows_fallback_host_returns_none_outside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=False):
            self.assertIsNone(controller_server._controller_windows_fallback_host())

    def test_windows_fallback_host_uses_first_ipv4(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=True):
            with mock.patch.object(
                runtime_hosts.subprocess,
                "check_output",
                return_value="172.20.128.246 fe80::1\n",
            ):
                self.assertEqual(
                    controller_server._controller_windows_fallback_host(),
                    "172.20.128.246",
                )


class ControllerServerLaunchGateTests(unittest.TestCase):
    def test_runtime_status_placeholder_handles_non_mapping_payload(self) -> None:
        with mock.patch.object(controller_server, "read_runtime_status", return_value="corrupted-status"):
            status = controller_server._runtime_status_or_placeholder()
        self.assertEqual(status["runtime_state"], "STOPPED")
        self.assertEqual(status["project_root"], str(controller_server.PROJECT_ROOT))
        self.assertEqual(status["autonomy"]["mode"], "normal")

    def test_pipeline_start_propagates_launch_gate_error_from_backend(self) -> None:
        with mock.patch.object(controller_server, "backend_pipeline_start", return_value="실행 차단: active profile이 없습니다 (.pipeline/config/agent_profile.json)."):
            result = controller_server.pipeline_start()
        self.assertEqual(result["ok"], False)
        self.assertIn("active profile이 없습니다", result["error"])
        self.assertIn(".pipeline/config/agent_profile.json", result["error"])

    def test_pipeline_start_waits_for_shared_readiness_confirmation(self) -> None:
        with (
            mock.patch.object(controller_server, "backend_pipeline_start", return_value="시작 요청됨"),
            mock.patch.object(controller_server, "backend_confirm_pipeline_start", return_value=(True, "파이프라인 시작 완료")),
        ):
            result = controller_server.pipeline_start()
        self.assertEqual(result, {"ok": True, "message": "파이프라인 시작 완료"})

    def test_pipeline_start_returns_shared_readiness_failure(self) -> None:
        with (
            mock.patch.object(controller_server, "backend_pipeline_start", return_value="시작 요청됨"),
            mock.patch.object(
                controller_server,
                "backend_confirm_pipeline_start",
                return_value=(False, "시작 실패: 15초 안에 runtime READY 조건을 만족하지 못했습니다 — supervisor/status를 확인해 주세요"),
            ),
        ):
            result = controller_server.pipeline_start()
        self.assertEqual(result["ok"], False)
        self.assertIn("15초 안에 runtime READY 조건", result["error"])

    def test_controller_html_polls_runtime_api_only(self) -> None:
        controller_dir = Path(__file__).resolve().parents[1] / "controller"
        html = (controller_dir / "index.html").read_text(encoding="utf-8")
        css = (controller_dir / "css" / "office.css").read_text(encoding="utf-8")
        server_source = (controller_dir / "server.py").read_text(encoding="utf-8")
        # Read all JS module sources for assertions that moved out of inline HTML
        js_dir = controller_dir / "js"
        js_sources = ""
        if js_dir.is_dir():
            for jsf in sorted(js_dir.glob("*.js")):
                js_sources += jsf.read_text(encoding="utf-8") + "\n"
        # Combined frontend source = HTML inline script + JS modules
        frontend = html + "\n" + js_sources
        # API endpoints (some in HTML inline script, some in JS modules)
        self.assertIn("/api/runtime/status", frontend)
        self.assertIn("/api/runtime/start", html)
        self.assertIn("/api/runtime/stop", html)
        self.assertIn("/api/runtime/restart", html)
        self.assertIn("/api/runtime/capture-tail", frontend)
        self.assertIn("/api/runtime/send-input", frontend)
        # State GIF assets (now in config.js module)
        self.assertIn("STATE_GIF_ASSETS", frontend)
        self.assertIn("/controller-assets/BOOTING.gif", frontend)
        self.assertIn("/controller-assets/WORKING.gif", frontend)
        self.assertIn("/controller-assets/BROKEN.gif", frontend)
        self.assertIn("/controller-assets/READY.gif", frontend)
        self.assertIn("/controller-assets/DEAD.gif", frontend)
        # Sprite manifest (now in agents.js module)
        self.assertIn("/controller-assets/generated/office-sprite-manifest.json", frontend)
        self.assertIn("SpriteManager.init()", frontend)
        # Log modal DOM elements must exist in HTML
        self.assertIn("log-modal", html)
        self.assertIn("log-modal-body", html)
        self.assertIn("lm-input", html)
        self.assertIn("sendModalInput()", frontend)
        self.assertIn("log-modal-send-status", html)
        # Polling constants (now in config.js)
        self.assertIn("POLL_MS", frontend)
        self.assertIn("ACTION_REPOLL_MS", frontend)
        self.assertIn("LOG_REFRESH_MS", frontend)
        self.assertIn("_logRefreshInFlight", frontend)
        # CSS assertions
        self.assertIn("width: min(1360px, 98vw)", css)
        self.assertIn("width: 100%; min-width: 0;", css)
        self.assertIn("flex-wrap: wrap", css)
        self.assertIn("white-space: normal;", css)
        # Runtime presentation (now in state.js module)
        self.assertIn("getPresentation", frontend)
        self.assertIn("supervisor_missing_recent_ambiguous", frontend)
        self.assertIn("supervisor_missing_snapshot_undated", frontend)
        self.assertIn("UNCERTAIN_RUNTIME_REASONS", frontend)
        self.assertIn("Runtime truth uncertain", frontend)
        self.assertIn("badge.stopping", css)
        self.assertIn("badge.broken", css)
        self.assertIn(".info-value.dim", css)
        self.assertIn("Watcher", frontend)
        # Delivery events (now in delivery.js module)
        self.assertIn("Work delivered", frontend)
        self.assertIn("Verify updated", frontend)
        self.assertIn("Receipt issued", frontend)
        # Delivery trigger must track artifact mtime for update-in-place detection
        self.assertIn("latestWorkMtime", frontend)
        self.assertIn("latestVerifyMtime", frontend)
        self.assertIn(".mtime", frontend)
        # Zone-based layout (replaces LOCATIONS)
        self.assertIn("ZONE_MAP", frontend)
        self.assertIn("claude_desk", frontend)
        self.assertIn("codex_desk", frontend)
        self.assertIn("gemini_desk", frontend)
        # Zone-bounded idle roaming (replaces IDLE_ROAM_SPOTS)
        self.assertIn("_pickIdleTarget()", frontend)
        self.assertIn("case 'ready':", frontend)
        self.assertIn("case 'idle':", frontend)
        # AmbientAudio must not auto-start from poll()
        self.assertNotIn("AmbientAudio._start()", frontend)
        # Low-motion mode (now split between canvas.js and inline script)
        self.assertIn("_lowMotion", frontend)
        self.assertIn("motion-btn", html)
        # Toolbar preferences must persist via browser-local storage
        self.assertIn("office_low_motion", frontend)
        self.assertIn("office_muted", frontend)
        self.assertIn("localStorage.setItem", frontend)
        self.assertIn("localStorage.getItem", frontend)
        # Shared storage helper (now in audio.js module)
        self.assertIn("PrefStore", frontend)
        # Toolbar storage-unavailable indicator must exist in HTML
        self.assertIn("storage-warn", html)
        self.assertNotIn("laneAction('pause')", frontend)
        self.assertNotIn("laneAction('resume')", frontend)
        self.assertNotIn("laneAction('restart')", frontend)
        self.assertNotIn("/api/runtime/lane/", frontend)
        self.assertNotIn("/api/runtime/attach", frontend)
        self.assertNotIn("control_slots", frontend)
        self.assertNotIn("turn_state", frontend)
        self.assertNotIn('fetch("/api/state")', frontend)
        self.assertNotIn("apiPost('/api/start')", frontend)
        self.assertNotIn("/api/runtime/exec", frontend)
        self.assertIn("/api/runtime/send-input", server_source)
        self.assertNotIn("/api/state", server_source)
        self.assertNotIn("/api/health", server_source)
        self.assertNotIn("/api/start", server_source)
        self.assertNotIn("/api/stop", server_source)
        self.assertNotIn("/api/restart", server_source)
        self.assertNotIn("/api/runtime/attach", server_source)

    def test_runtime_capture_tail_requires_lane(self) -> None:
        data, status = controller_server.runtime_capture_tail(lane=None)
        self.assertEqual(int(status), 400)
        self.assertFalse(data["ok"])

    def test_runtime_capture_tail_delegates_to_backend_helper(self) -> None:
        with mock.patch.object(
            controller_server,
            "backend_runtime_capture_tail",
            return_value="tail output",
        ) as capture_tail:
            data, status = controller_server.runtime_capture_tail(lane="Claude", lines=77)
        self.assertEqual(int(status), 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["text"], "tail output")
        capture_tail.assert_called_once_with(
            controller_server.PROJECT_ROOT,
            controller_server.SESSION_NAME,
            "Claude",
            lines=77,
        )

    def test_runtime_capture_tail_normalizes_adjacent_pasted_content_markers(self) -> None:
        with mock.patch.object(
            controller_server,
            "backend_runtime_capture_tail",
            return_value="line[Pasted Content 100 chars][Pasted Content 200 chars]",
        ):
            data, status = controller_server.runtime_capture_tail(lane="Codex", lines=40)

        self.assertEqual(int(status), 200)
        self.assertEqual(
            data["text"],
            "line\n[Pasted Content 100 chars]\n[Pasted Content 200 chars]",
        )

    def test_runtime_send_input_requires_lane(self) -> None:
        data, status = controller_server.runtime_send_input(lane=None, text="1")
        self.assertEqual(int(status), 400)
        self.assertFalse(data["ok"])

    def test_runtime_send_input_requires_text(self) -> None:
        data, status = controller_server.runtime_send_input(lane="Claude", text="   ")
        self.assertEqual(int(status), 400)
        self.assertFalse(data["ok"])

    def test_runtime_send_input_delegates_to_backend_helper(self) -> None:
        with mock.patch.object(
            controller_server,
            "backend_runtime_send_input",
            return_value=True,
        ) as send_input:
            data, status = controller_server.runtime_send_input(lane="Codex", text="1")
        self.assertEqual(int(status), 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["lane"], "Codex")
        self.assertEqual(data["text"], "1")
        send_input.assert_called_once_with(
            controller_server.PROJECT_ROOT,
            controller_server.SESSION_NAME,
            "Codex",
            text="1",
        )

    def test_resolve_controller_asset_returns_existing_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "assets"
            assets.mkdir(parents=True, exist_ok=True)
            sprite = assets / "fren-office-sheet.png"
            sprite.write_bytes(b"png")
            with mock.patch.object(controller_server, "CONTROLLER_DIR", root):
                path, content_type = controller_server._resolve_controller_asset("fren-office-sheet.png")
        self.assertEqual(path, sprite)
        self.assertEqual(content_type, "image/png")

    def test_resolve_controller_asset_returns_existing_gif(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "assets"
            assets.mkdir(parents=True, exist_ok=True)
            ready_gif = assets / "READY.gif"
            ready_gif.write_bytes(b"gif")
            with mock.patch.object(controller_server, "CONTROLLER_DIR", root):
                path, content_type = controller_server._resolve_controller_asset("READY.gif")
        self.assertEqual(path, ready_gif)
        self.assertEqual(content_type, "image/gif")

    def test_resolve_controller_asset_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "assets"
            assets.mkdir(parents=True, exist_ok=True)
            with mock.patch.object(controller_server, "CONTROLLER_DIR", root):
                path, content_type = controller_server._resolve_controller_asset("../index.html")
        self.assertIsNone(path)
        self.assertIsNone(content_type)


class ControllerAssetResolutionTests(unittest.TestCase):
    def test_resolve_css_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            css_dir = root / "css"
            css_dir.mkdir(parents=True, exist_ok=True)
            css_file = css_dir / "office.css"
            css_file.write_text("body { margin: 0; }", encoding="utf-8")
            with mock.patch.object(controller_server, "CONTROLLER_DIR", root):
                path, content_type = controller_server._resolve_controller_asset("css/office.css")
        self.assertEqual(path, css_file)
        self.assertEqual(content_type, "text/css")

    def test_resolve_js_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            js_dir = root / "js"
            js_dir.mkdir(parents=True, exist_ok=True)
            js_file = js_dir / "config.js"
            js_file.write_text("const x = 1;", encoding="utf-8")
            with mock.patch.object(controller_server, "CONTROLLER_DIR", root):
                path, content_type = controller_server._resolve_controller_asset("js/config.js")
        self.assertEqual(path, js_file)
        self.assertIn("javascript", content_type)

    def test_resolve_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir(parents=True, exist_ok=True)
            (root / "css").mkdir(parents=True, exist_ok=True)
            (root / "js").mkdir(parents=True, exist_ok=True)
            with mock.patch.object(controller_server, "CONTROLLER_DIR", root):
                path, content_type = controller_server._resolve_controller_asset("../server.py")
        self.assertIsNone(path)
        self.assertIsNone(content_type)


if __name__ == "__main__":
    unittest.main()
