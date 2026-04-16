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
        html = (Path(__file__).resolve().parents[1] / "controller" / "index.html").read_text(encoding="utf-8")
        server_source = (Path(__file__).resolve().parents[1] / "controller" / "server.py").read_text(encoding="utf-8")
        self.assertIn("/api/runtime/status", html)
        self.assertIn("/api/runtime/start", html)
        self.assertIn("/api/runtime/stop", html)
        self.assertIn("/api/runtime/restart", html)
        self.assertIn("/api/runtime/capture-tail", html)
        self.assertIn("const STATE_GIF_ASSETS = {", html)
        self.assertIn("/controller-assets/BOOTING.gif", html)
        self.assertIn("/controller-assets/WORKING.gif", html)
        self.assertIn("/controller-assets/BROKEN.gif", html)
        self.assertIn("/controller-assets/READY.gif", html)
        self.assertIn("/controller-assets/DEAD.gif", html)
        self.assertIn("/controller-assets/background.png", html)
        self.assertIn("/controller-assets/generated/bg-office.png", html)
        self.assertIn("/controller-assets/generated/office-sprite-manifest.json", html)
        self.assertIn("const BACKGROUND_ASSET_CANDIDATES = [", html)
        self.assertIn("function _loadBackgroundAsset(", html)
        self.assertIn("_bgImg.onload", html)
        self.assertIn("_bgImg.onerror", html)
        self.assertIn("_bgImg.complete", html)
        self.assertIn("naturalWidth", html)
        self.assertIn("_bgLoadError", html)
        self.assertIn("_emitBackgroundSignal(", html)
        self.assertIn("SpriteManager.init()", html)
        self.assertIn("openLogModal(agent)", html)
        self.assertIn("log-modal", html)
        self.assertIn("log-modal-body", html)
        self.assertIn("width: min(1100px, 96vw)", html)
        self.assertIn("width: 100%; min-width: 0;", html)
        self.assertIn("flex-wrap: wrap", html)
        self.assertIn("white-space: normal;", html)
        self.assertIn("renderRuntimeInfo(data, presentation)", html)
        self.assertIn("function getRuntimePresentation(data)", html)
        self.assertIn("supervisor_missing_recent_ambiguous", html)
        self.assertIn("supervisor_missing_snapshot_undated", html)
        self.assertIn("UNCERTAIN_RUNTIME_REASONS", html)
        self.assertIn("Runtime truth uncertain", html)
        self.assertIn("badge.stopping", html)
        self.assertIn("badge.broken", html)
        self.assertIn(".info-value.dim", html)
        self.assertIn("<span class=\"info-label\">Scene</span>", html)
        self.assertIn("Watcher", html)
        self.assertIn("function emitDelivery(", html)
        self.assertIn("Work delivered →", html)
        self.assertIn("Verify updated →", html)
        self.assertIn("Receipt issued →", html)
        # Delivery trigger must track artifact mtime for update-in-place detection
        self.assertIn("latestWorkMtime", html)
        self.assertIn("latestVerifyMtime", html)
        self.assertIn(".mtime", html)
        self.assertIn("claude_desk:  { x: 492, y: 236 }", html)
        self.assertIn("codex_desk:   { x: 492, y: 366 }", html)
        self.assertIn("gemini_desk:  { x: 492, y: 496 }", html)
        self.assertIn("entrance:     { x: 868, y: 664 }", html)
        self.assertIn("const IDLE_ROAM_SPOTS = [", html)
        self.assertIn("_pickIdleTarget()", html)
        self.assertIn("x: 770, y: 300", html)
        self.assertIn("x: 832, y: 318", html)
        self.assertIn("case 'ready':", html)
        self.assertIn("case 'idle':", html)
        self.assertIn("dest = this._pickIdleTarget();", html)
        # Pet nap target must use a defined location (sofa, not sofa_2)
        self.assertNotIn("LOCATIONS.sofa_2", html)
        self.assertIn("LOCATIONS.sofa.x", html)
        # AmbientAudio must not auto-start from poll()
        self.assertNotIn("AmbientAudio._start()", html)
        # Low-motion mode must gate decorative layers browser-locally
        self.assertIn("let _lowMotion = false", html)
        self.assertIn("function toggleLowMotion()", html)
        self.assertIn("motion-btn", html)
        self.assertIn("if (_lowMotion) return", html)
        # Toolbar preferences must persist via browser-local storage
        self.assertIn("office_low_motion", html)
        self.assertIn("office_muted", html)
        self.assertIn("localStorage.setItem", html)
        self.assertIn("localStorage.getItem", html)
        # Shared storage helper must exist and surface fallback visibility
        self.assertIn("PrefStore", html)
        self.assertIn("PrefStore.get(", html)
        self.assertIn("PrefStore.set(", html)
        self.assertIn("_probe()", html)
        self.assertIn("환경 설정 저장 불가", html)
        # Toolbar storage-unavailable indicator must exist
        self.assertIn("storage-warn", html)
        self.assertIn("설정 비저장", html)
        self.assertIn("PrefStore.available", html)
        self.assertNotIn("laneAction('pause')", html)
        self.assertNotIn("laneAction('resume')", html)
        self.assertNotIn("laneAction('restart')", html)
        self.assertNotIn("/api/runtime/lane/", html)
        self.assertNotIn("/api/runtime/attach", html)
        self.assertNotIn("control_slots", html)
        self.assertNotIn("turn_state", html)
        self.assertNotIn('fetch("/api/state")', html)
        self.assertNotIn("apiPost('/api/start')", html)
        self.assertNotIn("/api/runtime/exec", html)
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


if __name__ == "__main__":
    unittest.main()
