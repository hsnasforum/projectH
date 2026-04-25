from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import config.runtime_hosts as runtime_hosts
import controller.server as controller_server
from pipeline_gui.backend import PIPELINE_START_READY_TIMEOUT_SECONDS
from pipeline_gui.token_queries import AgentTotals, CollectorStatus, TodayTotals, TokenDashboard


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
        with (
            mock.patch.object(controller_server, "read_runtime_status", return_value="corrupted-status"),
            mock.patch.object(
                controller_server,
                "resolve_project_runtime_adapter",
                return_value={
                    "resolution_state": "ready",
                    "role_owners": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "prompt_owners": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "enabled_lanes": ["Codex", "Claude", "Gemini"],
                },
            ),
        ):
            status = controller_server._runtime_status_or_placeholder()
        self.assertEqual(status["runtime_state"], "STOPPED")
        self.assertEqual(status["project_root"], str(controller_server.PROJECT_ROOT))
        self.assertEqual(status["autonomy"]["mode"], "normal")
        self.assertEqual(status["automation_health"], "ok")
        self.assertEqual(status["automation_next_action"], "continue")
        self.assertFalse(status["stale_advisory_pending"])
        self.assertEqual(status["role_owners"]["implement"], "Codex")
        self.assertEqual(status["role_owners"]["verify"], "Claude")
        self.assertEqual(status["prompt_owners"]["implement"], "Codex")

    def test_get_runtime_status_includes_active_profile_role_metadata(self) -> None:
        with (
            mock.patch.object(
                controller_server,
                "read_runtime_status",
                return_value={"runtime_state": "RUNNING", "lanes": [], "control": {}, "artifacts": {}},
            ),
            mock.patch.object(
                controller_server,
                "resolve_project_runtime_adapter",
                return_value={
                    "resolution_state": "ready",
                    "role_owners": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "prompt_owners": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "enabled_lanes": ["Codex", "Claude", "Gemini"],
                },
            ),
        ):
            data, status = controller_server.get_runtime_status()

        self.assertEqual(int(status), 200)
        self.assertEqual(data["role_owners"]["implement"], "Codex")
        self.assertEqual(data["role_owners"]["verify"], "Claude")
        self.assertEqual(data["prompt_owners"]["verify"], "Claude")
        self.assertEqual(data["enabled_lanes"], ["Codex", "Claude", "Gemini"])

    def test_get_runtime_status_returns_stopped_placeholder_when_unavailable(self) -> None:
        with (
            mock.patch.object(controller_server, "read_runtime_status", return_value=None),
            mock.patch.object(
                controller_server,
                "resolve_project_runtime_adapter",
                return_value={
                    "resolution_state": "ready",
                    "role_owners": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "prompt_owners": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "enabled_lanes": ["Codex", "Claude", "Gemini"],
                },
            ),
        ):
            data, status = controller_server.get_runtime_status()

        self.assertEqual(int(status), 200)
        self.assertEqual(data["runtime_state"], "STOPPED")
        self.assertEqual(data["project_root"], str(controller_server.PROJECT_ROOT))
        self.assertEqual(data["role_owners"]["verify"], "Claude")

    def test_runtime_monitor_snapshot_fans_in_token_hud(self) -> None:
        dashboard = TokenDashboard(
            display_day="2026-04-05",
            collector_status=CollectorStatus(available=True, phase="idle"),
            today_totals=TodayTotals(
                input_tokens=100,
                output_tokens=50,
                cache_read_tokens=25,
                cache_write_tokens=5,
                thinking_tokens=10,
                actual_cost_usd_sum=1.25,
                estimated_only_cost_usd_sum=0.25,
            ),
            agent_totals=[
                AgentTotals(
                    source="codex",
                    events=4,
                    linked_events=3,
                    input_tokens=80,
                    output_tokens=20,
                    cache_read_tokens=40,
                    cache_write_tokens=0,
                    thinking_tokens=10,
                    total_cost_usd=0.75,
                    actual_cost_usd_sum=0.5,
                    estimated_only_cost_usd_sum=0.25,
                )
            ],
            top_jobs=[],
        )
        runtime = {
            "runtime_state": "RUNNING",
            "lanes": [{"name": "Codex", "state": "working"}],
        }
        with (
            mock.patch.object(
                controller_server,
                "get_runtime_status",
                return_value=(runtime, controller_server.HTTPStatus.OK),
            ),
            mock.patch.object(controller_server, "load_token_dashboard", return_value=dashboard),
        ):
            snapshot = controller_server.runtime_monitor_snapshot()

        self.assertTrue(snapshot["ok"])
        self.assertTrue(snapshot["source"]["read_only"])
        self.assertEqual(snapshot["runtime"]["runtime_state"], "RUNNING")
        self.assertEqual(snapshot["hud"]["totals"]["total_tokens"], 190)
        self.assertEqual(snapshot["hud"]["totals"]["total_cost_usd"], 1.5)
        self.assertEqual(snapshot["hud"]["totals"]["cache_hit_rate"], 0.1923)
        codex = snapshot["hud"]["agents"][0]
        self.assertEqual(codex["name"], "Codex")
        self.assertEqual(codex["state"], "working")
        self.assertTrue(codex["active"])
        self.assertEqual(codex["total_tokens"], 150)
        self.assertEqual(codex["cache_hit_rate"], 0.3333)
        self.assertIn("input_ports", snapshot["state_manager"])
        self.assertIn("teams", snapshot)
        self.assertIn("communications", snapshot)
        self.assertIn("coordination_state", snapshot)

    def test_runtime_agent_inspector_reads_lane_tail(self) -> None:
        dashboard = TokenDashboard(
            display_day="2026-04-05",
            collector_status=CollectorStatus(available=True, phase="idle"),
            today_totals=TodayTotals(input_tokens=1, output_tokens=2),
            agent_totals=[],
            top_jobs=[],
        )
        runtime = {
            "runtime_state": "RUNNING",
            "role_owners": {"verify": "Codex"},
            "lanes": [{"name": "Codex", "state": "working", "note": "checking monitor", "pid": 123}],
        }
        with (
            mock.patch.object(
                controller_server,
                "get_runtime_status",
                return_value=(runtime, controller_server.HTTPStatus.OK),
            ),
            mock.patch.object(controller_server, "load_token_dashboard", return_value=dashboard),
            mock.patch.object(
                controller_server,
                "backend_runtime_capture_tail",
                return_value="Prompt: inspect agent drawer\nAssistant: working",
            ) as capture_tail,
        ):
            data, status = controller_server.runtime_agent_inspector(agent="Codex", lines=77)

        self.assertEqual(int(status), 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["agent"]["id"], "Codex")
        self.assertEqual(data["agent"]["role"], "verify")
        self.assertIn("Prompt: inspect agent drawer", data["current_prompt"])
        self.assertIn("Assistant: working", data["conversation"])
        capture_tail.assert_called_once_with(
            controller_server.PROJECT_ROOT,
            controller_server.SESSION_NAME,
            "Codex",
            lines=77,
        )

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
                return_value=(
                    False,
                    f"시작 실패: {PIPELINE_START_READY_TIMEOUT_SECONDS}초 안에 runtime READY 조건을 만족하지 못했습니다 — supervisor/status를 확인해 주세요",
                ),
            ),
        ):
            result = controller_server.pipeline_start()
        self.assertEqual(result["ok"], False)
        self.assertIn(f"{PIPELINE_START_READY_TIMEOUT_SECONDS}초 안에 runtime READY 조건", result["error"])

    def test_controller_html_polls_runtime_api_only(self) -> None:
        controller_dir = Path(__file__).resolve().parents[1] / "controller"
        html = (controller_dir / "index.html").read_text(encoding="utf-8")
        css = (controller_dir / "css" / "office.css").read_text(encoding="utf-8")
        server_source = (controller_dir / "server.py").read_text(encoding="utf-8")
        cozy_js = (controller_dir / "js" / "cozy.js").read_text(encoding="utf-8")
        # Runtime behavior lives in the shared /controller-assets/js/cozy.js
        # module. index.html only carries the DOM shell and a script tag that
        # wires the cozy runtime back under shared controller/js ownership.
        self.assertIn('src="/controller-assets/js/cozy.js"', html)
        self.assertNotIn("pollRuntime", html)
        self.assertNotIn("sendModalInput", html)
        # API endpoints are wired from the shared cozy runtime module
        self.assertIn("/api/runtime/status", cozy_js)
        self.assertIn("/api/runtime/start", cozy_js)
        self.assertIn("/api/runtime/stop", cozy_js)
        self.assertIn("/api/runtime/restart", cozy_js)
        self.assertIn("/api/runtime/capture-tail", cozy_js)
        self.assertIn("/api/runtime/send-input", cozy_js)
        self.assertIn("/api/runtime/monitor-snapshot", cozy_js)
        self.assertIn("/api/runtime/agent-inspector", cozy_js)
        self.assertIn("/api/runtime/agent-inspector", server_source)
        self.assertIn("/ws/runtime/monitor", cozy_js)
        self.assertIn("/ws/runtime/monitor", server_source)
        self.assertIn("__officeRuntimeMonitorDisabled", cozy_js)
        self.assertIn("role_owners", cozy_js)
        self.assertIn("currentRoleOwners", cozy_js)
        self.assertIn("ownerForZone", cozy_js)
        # Cozy scene should not depend on GIF/background runtime assets
        self.assertNotIn("/controller-assets/BOOTING.gif", cozy_js)
        self.assertNotIn("/controller-assets/WORKING.gif", cozy_js)
        self.assertNotIn("/controller-assets/BROKEN.gif", cozy_js)
        self.assertNotIn("/controller-assets/READY.gif", cozy_js)
        self.assertNotIn("/controller-assets/DEAD.gif", cozy_js)
        self.assertNotIn("/controller-assets/generated/office-sprite-manifest.json", cozy_js)
        self.assertIn("marquee-text", html)
        self.assertIn("marquee-scroll", css)
        self.assertIn("Party Roster", cozy_js)
        self.assertIn("Token HUD", cozy_js)
        self.assertIn("renderTokenHud", cozy_js)
        self.assertIn("Agent Inspector", html)
        self.assertIn("renderAgentInspector", cozy_js)
        self.assertIn("operator-attention-board", html)
        self.assertIn("operator-attention-board", css)
        self.assertIn("buildOperatorAttention", cozy_js)
        self.assertIn("renderOperatorAttentionBoard", cozy_js)
        self.assertIn("getOperatorAttentionDebug", cozy_js)
        self.assertIn("findPath", cozy_js)
        self.assertIn("PATH_OBSTACLES", cozy_js)
        self.assertIn("drawTeamHulls", cozy_js)
        self.assertIn("queueCommunicationTransfer", cozy_js)
        self.assertIn("approvalWaitingForAgent", cozy_js)
        self.assertIn("isWorldRectVisible", cozy_js)
        self.assertIn("CHARACTER_SKINS", cozy_js)
        self.assertIn("프리렌풍 엘프 마법사", cozy_js)
        self.assertIn("아카네풍 배우", cozy_js)
        self.assertIn("귀여운 오리지널 여캐", cozy_js)
        self.assertIn("token-agent-row", css)
        self.assertIn("agent-inspector", css)
        self.assertIn("Role Binding", cozy_js)
        self.assertIn("roleOwnerRows", cozy_js)
        self.assertIn("Implement owner", cozy_js)
        self.assertIn("Verify owner", cozy_js)
        self.assertIn("Advisory owner", cozy_js)
        self.assertIn("Quest Log", html)
        # Log modal DOM elements must exist in HTML; modal wiring lives in cozy.js
        self.assertIn("log-modal", html)
        self.assertIn("log-modal-body", html)
        self.assertIn("lm-input", html)
        self.assertIn("sendModalInput()", cozy_js)
        self.assertIn("log-modal-send-status", html)
        # Polling / modal control lives in the shared cozy runtime module
        self.assertIn("POLL_MS", cozy_js)
        self.assertIn("ACTION_REPOLL_MS", cozy_js)
        self.assertIn("LOG_REFRESH_MS", cozy_js)
        self.assertIn("logRefreshInFlight", cozy_js)
        self.assertIn("modalSendInFlight", cozy_js)
        self.assertIn("recordStatusFetchFailure", cozy_js)
        self.assertIn("clearStatusFetchFailure", cozy_js)
        self.assertIn("statusFetchFailureActive", cozy_js)
        self.assertIn("상태 조회 복구:", cozy_js)
        # CSS assertions
        self.assertIn("width: min(1360px, 98vw)", css)
        self.assertIn("width: 100%; min-width: 0;", css)
        self.assertIn("flex-wrap: wrap", css)
        self.assertIn("white-space: normal;", css)
        # Runtime presentation helpers
        self.assertIn("getPresentation", cozy_js)
        self.assertIn("supervisor_missing_recent_ambiguous", cozy_js)
        self.assertIn("supervisor_missing_snapshot_undated", cozy_js)
        self.assertIn("UNCERTAIN_RUNTIME_REASONS", cozy_js)
        self.assertIn("Runtime truth uncertain", cozy_js)
        self.assertIn("badge.stopping", css)
        self.assertIn("badge.broken", css)
        self.assertIn(".info-value.dim", css)
        self.assertIn("Watcher", cozy_js)
        self.assertIn("Automation", cozy_js)
        self.assertIn("automationHealth", cozy_js)
        self.assertIn("staleAdvisoryPending", cozy_js)
        # Delivery/event tracking for sidebar and quest log
        self.assertIn("Latest work →", cozy_js)
        self.assertIn("Latest verify →", cozy_js)
        self.assertIn("Receipt issued →", cozy_js)
        # Delivery trigger must track artifact mtime for update-in-place detection
        self.assertIn("latestWorkMtime", cozy_js)
        self.assertIn("latestVerifyMtime", cozy_js)
        # Zone-based layout (replaces LOCATIONS)
        self.assertIn("ZONE_MAP", cozy_js)
        self.assertIn("claude_desk", cozy_js)
        self.assertIn("codex_desk", cozy_js)
        self.assertIn("gemini_desk", cozy_js)
        self.assertIn("lounge", cozy_js)
        # Lounge rest roaming and scene test hooks stay available
        self.assertIn("sampleIdleTarget", cozy_js)
        self.assertIn("setAgentFatigue", cozy_js)
        self.assertIn("getRoamBounds", cozy_js)
        self.assertIn("getAgentPositions", cozy_js)
        self.assertIn("testPickIdleTargets", cozy_js)
        self.assertIn("testAntiStacking", cozy_js)
        self.assertIn("testHistoryPenalty", cozy_js)
        self.assertIn("testPetCat", cozy_js)
        self.assertIn("getSceneDebug", cozy_js)
        self.assertIn("roleOwners: currentRoleOwners()", cozy_js)
        self.assertIn("drawWindow", cozy_js)
        self.assertIn("drawPneumaticTube", cozy_js)
        self.assertIn("sendPacket", cozy_js)
        self.assertIn("sendOwl", cozy_js)
        self.assertIn("window.Audio8", cozy_js)
        # Low-motion and browser-local preferences
        self.assertIn("motion-btn", html)
        self.assertIn("office_low_motion", cozy_js)
        self.assertIn("office_muted", cozy_js)
        self.assertIn("localStorage.setItem", cozy_js)
        self.assertIn("localStorage.getItem", cozy_js)
        self.assertIn("PrefStore", cozy_js)
        # Toolbar storage-unavailable indicator must exist in HTML
        self.assertIn("storage-warn", html)
        self.assertNotIn("laneAction('pause')", cozy_js)
        self.assertNotIn("laneAction('resume')", cozy_js)
        self.assertNotIn("laneAction('restart')", cozy_js)
        self.assertNotIn("/api/runtime/lane/", cozy_js)
        self.assertNotIn("/api/runtime/attach", cozy_js)
        self.assertNotIn("control_slots", cozy_js)
        self.assertIn("turn_state", cozy_js)
        self.assertNotIn('fetch("/api/state")', cozy_js)
        self.assertNotIn("apiPost('/api/start')", cozy_js)
        self.assertNotIn("/api/runtime/exec", cozy_js)
        self.assertIn("/api/runtime/send-input", server_source)
        self.assertIn("resolve_project_runtime_adapter", server_source)
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
