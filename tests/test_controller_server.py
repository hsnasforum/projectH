from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import config.runtime_hosts as runtime_hosts
import controller.server as controller_server
from pipeline_gui.backend import PIPELINE_START_READY_TIMEOUT_SECONDS
from pipeline_gui.token_queries import AgentTotals, CollectorStatus, TodayTotals, TokenDashboard
from pipeline_runtime.state_contract import RUNTIME_SNAPSHOT_CONTRACT_VERSION, reduce_runtime_snapshot


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
        snapshot = status["runtime_snapshot"]
        self.assertEqual(snapshot["contract_version"], RUNTIME_SNAPSHOT_CONTRACT_VERSION)
        self.assertEqual(snapshot["runtime_state"], "STOPPED")
        self.assertEqual(snapshot["queue"]["status"], "Runtime inactive")

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

    def test_get_runtime_status_synthesizes_runtime_snapshot_for_legacy_payload(self) -> None:
        with (
            mock.patch.object(
                controller_server,
                "read_runtime_status",
                return_value={
                    "runtime_state": "RUNNING",
                    "automation_health": "ok",
                    "automation_next_action": "continue",
                    "watcher": {"alive": True, "pid": 12345},
                    "lanes": [{"name": "Codex", "state": "ready", "attachable": True, "pid": 12346}],
                    "control": {
                        "active_control_file": ".pipeline/implement_handoff.md",
                        "active_control_seq": 2043,
                        "active_control_status": "implement",
                    },
                    "artifacts": {},
                },
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
        snapshot = data["runtime_snapshot"]
        self.assertEqual(snapshot["contract_version"], RUNTIME_SNAPSHOT_CONTRACT_VERSION)
        self.assertEqual(snapshot["runtime_state"], "RUNNING")
        self.assertEqual(snapshot["control_state"], "implement")
        self.assertEqual(snapshot["queue"]["status"], "implement #2043")
        self.assertFalse(snapshot["queue"]["no_queued_pipeline_task"])

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
        snapshot = data["runtime_snapshot"]
        self.assertEqual(snapshot["contract_version"], RUNTIME_SNAPSHOT_CONTRACT_VERSION)
        self.assertEqual(snapshot["runtime_state"], "STOPPED")
        self.assertEqual(snapshot["queue"]["status"], "Runtime inactive")

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
            "automation_health": "ok",
            "automation_next_action": "continue",
            "control": {
                "active_control_file": ".pipeline/implement_handoff.md",
                "active_control_seq": 2044,
                "active_control_status": "implement",
            },
            "lanes": [{"name": "Codex", "state": "working"}],
        }
        runtime["runtime_snapshot"] = reduce_runtime_snapshot(runtime)
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
        runtime_snapshot = snapshot["runtime"]["runtime_snapshot"]
        self.assertEqual(runtime_snapshot["contract_version"], RUNTIME_SNAPSHOT_CONTRACT_VERSION)
        self.assertEqual(runtime_snapshot["queue"]["status"], "implement #2044")
        self.assertEqual(runtime_snapshot["queue"]["class_name"], "neutral")
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

    def _controller_sources(self) -> dict[str, str]:
        controller_dir = Path(__file__).resolve().parents[1] / "controller"
        return {
            "html": (controller_dir / "index.html").read_text(encoding="utf-8"),
            "css": (controller_dir / "css" / "office.css").read_text(encoding="utf-8"),
            "server": (controller_dir / "server.py").read_text(encoding="utf-8"),
            "cozy": (controller_dir / "js" / "cozy.js").read_text(encoding="utf-8"),
            "panel": (controller_dir / "js" / "panel.js").read_text(encoding="utf-8"),
            "queue": (controller_dir / "js" / "queue-presentation.js").read_text(encoding="utf-8"),
            "zones": (controller_dir / "js" / "zones.js").read_text(encoding="utf-8"),
        }

    def test_controller_shell_scripts_keep_shared_source_ownership(self) -> None:
        sources = self._controller_sources()
        html = sources["html"]
        # Runtime behavior lives in the shared /controller-assets/js/cozy.js
        # module. index.html only carries the DOM shell and a script tag that
        # wires the cozy runtime back under shared controller/js ownership.
        queue_script = 'src="/controller-assets/js/queue-presentation.js"'
        cozy_script = 'src="/controller-assets/js/cozy.js"'
        self.assertIn(queue_script, html)
        self.assertIn(cozy_script, html)
        self.assertLess(html.index(queue_script), html.index(cozy_script))
        for module_script in ("panel.js", "zones.js", "state.js", "config.js", "agents.js", "canvas.js", "sidebar.js"):
            self.assertNotIn(f'src="/controller-assets/js/{module_script}"', html)
        self.assertNotIn("pollRuntime", html)
        self.assertNotIn("sendModalInput", html)

    def test_controller_shell_runtime_api_source_contract(self) -> None:
        sources = self._controller_sources()
        cozy_js = sources["cozy"]
        server_source = sources["server"]
        # Shipped shell runtime actions are wired from the shared cozy module.
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
        self.assertIn("POLL_MS", cozy_js)
        self.assertIn("ACTION_REPOLL_MS", cozy_js)
        self.assertIn("LOG_REFRESH_MS", cozy_js)
        self.assertIn("logRefreshInFlight", cozy_js)
        self.assertIn("modalSendInFlight", cozy_js)
        self.assertIn("recordStatusFetchFailure", cozy_js)
        self.assertIn("clearStatusFetchFailure", cozy_js)
        self.assertIn("statusFetchFailureActive", cozy_js)
        self.assertIn("상태 조회 복구:", cozy_js)
        self.assertIn("/api/runtime/send-input", server_source)
        self.assertIn("resolve_project_runtime_adapter", server_source)
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
        self.assertNotIn("/api/state", server_source)
        self.assertNotIn("/api/health", server_source)
        self.assertNotIn("/api/start", server_source)
        self.assertNotIn("/api/stop", server_source)
        self.assertNotIn("/api/restart", server_source)
        self.assertNotIn("/api/runtime/attach", server_source)

    def test_controller_shell_action_request_shape_contract(self) -> None:
        cozy_js = self._controller_sources()["cozy"]
        self.assertIn("const response = await fetch(path, { method: 'POST' });", cozy_js)
        self.assertIn("document.getElementById('btn-start').onclick = () => apiPost('/api/runtime/start');", cozy_js)
        self.assertIn("document.getElementById('btn-stop').onclick = () => apiPost('/api/runtime/stop');", cozy_js)
        self.assertIn("document.getElementById('btn-restart').onclick = () => apiPost('/api/runtime/restart');", cozy_js)
        self.assertIn("const response = await fetch('/api/runtime/send-input', {", cozy_js)
        self.assertIn("headers: { 'Content-Type': 'application/json' }", cozy_js)
        self.assertIn("body: JSON.stringify({ lane, text })", cozy_js)

    def test_controller_panel_request_shape_stays_module_side(self) -> None:
        sources = self._controller_sources()
        panel_js = sources["panel"]
        zones_js = sources["zones"]
        # Panel is module-side source imported by zones.js, not a direct shell script.
        self.assertIn("import { openPanel } from './panel.js';", zones_js)
        self.assertIn("const res = await fetch('/api/runtime/send-input', {", panel_js)
        self.assertIn("method: 'POST', headers: { 'Content-Type': 'application/json' }", panel_js)
        self.assertIn("body: JSON.stringify({ lane: _panelLane, text })", panel_js)

    def test_controller_visual_source_markers_stay_available(self) -> None:
        sources = self._controller_sources()
        html = sources["html"]
        css = sources["css"]
        cozy_js = sources["cozy"]
        queue_js = sources["queue"]
        # Cozy scene should not depend on GIF/background runtime assets
        self.assertNotIn("/controller-assets/BOOTING.gif", cozy_js)
        self.assertNotIn("/controller-assets/WORKING.gif", cozy_js)
        self.assertNotIn("/controller-assets/BROKEN.gif", cozy_js)
        self.assertNotIn("/controller-assets/READY.gif", cozy_js)
        self.assertNotIn("/controller-assets/DEAD.gif", cozy_js)
        self.assertNotIn("/controller-assets/generated/office-sprite-manifest.json", cozy_js)
        self.assertIn("marquee-text", html)
        self.assertIn("marquee-scroll", css)
        self.assertIn("파티 명부", cozy_js)
        self.assertIn("토큰 사용 현황", cozy_js)
        self.assertIn("renderTokenHud", cozy_js)
        self.assertIn("에이전트 검사기", html)
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
        self.assertIn("역할 배정", cozy_js)
        self.assertIn("roleOwnerRows", cozy_js)
        self.assertIn("구현 담당 (Implement)", cozy_js)
        self.assertIn("검증 담당 (Verify)", cozy_js)
        self.assertIn("자문 담당 (Advisory)", cozy_js)
        self.assertIn("의뢰 기록", html)
        # Log modal DOM elements must exist in HTML; modal wiring lives in cozy.js
        self.assertIn("log-modal", html)
        self.assertIn("log-modal-body", html)
        self.assertIn("lm-input", html)
        self.assertIn("sendModalInput()", cozy_js)
        self.assertIn("log-modal-send-status", html)
        # CSS assertions
        self.assertIn("width: min(1360px, 98vw)", css)
        self.assertIn("width: 100%;", css)
        self.assertIn("min-width: 0;", css)
        self.assertIn("flex-wrap: wrap", css)
        self.assertIn("white-space: normal;", css)
        # Runtime presentation helpers
        self.assertIn("getPresentation", cozy_js)
        self.assertIn("supervisor_missing_recent_ambiguous", cozy_js)
        self.assertIn("supervisor_missing_snapshot_undated", cozy_js)
        self.assertIn("UNCERTAIN_RUNTIME_REASONS", cozy_js)
        self.assertIn("Runtime truth uncertain", cozy_js)
        self.assertIn("PipelineQueuePresentation = Object.freeze", queue_js)
        self.assertIn("function queuePresentationHelper", cozy_js)
        self.assertIn("globalThis.PipelineQueuePresentation", cozy_js)
        self.assertIn("대기 중인 작업 없음", queue_js)
        self.assertIn("pipelineQueueStatus", cozy_js)
        self.assertIn("isNoQueuedPipelineTask", cozy_js)
        self.assertIn("대기열 ${presentation.pipelineQueueStatus}", cozy_js)
        self.assertIn("badge.stopping", css)
        self.assertIn("badge.broken", css)
        self.assertIn(".info-value.dim", css)
        self.assertIn("Watcher", cozy_js)
        self.assertIn("자동화 상태", cozy_js)
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

    def test_cozy_agent_state_uses_lane_state_as_runtime_truth(self) -> None:
        controller_dir = Path(__file__).resolve().parents[1] / "controller"
        cozy_js = (controller_dir / "js" / "cozy.js").read_text(encoding="utf-8")
        active_round_start = cozy_js.index("function activeRoundLaneName")
        active_round_end = cozy_js.index("\n}\n\nfunction effectiveLaneState", active_round_start)
        active_round_helper = cozy_js[active_round_start:active_round_end]
        lane_state_start = cozy_js.index("function effectiveLaneState")
        lane_state_end = cozy_js.index("\n}\n\nfunction zoneKeyForRole", lane_state_start)
        lane_state_helper = cozy_js[lane_state_start:lane_state_end]

        self.assertIn("ACTIVE_ROUND_ROLE_BY_STATE[roundState]", active_round_helper)
        self.assertIn("currentRoleOwners(data)[role]", active_round_helper)
        self.assertIn("activeRoundLaneName(data)", lane_state_helper)
        self.assertIn("activeRoundLane === agentName && rawState === 'ready'", lane_state_helper)
        self.assertIn("return 'working';", lane_state_helper)
        self.assertIn("Lane state is still the default runtime truth", lane_state_helper)
        self.assertIn("turn_state can stay active", lane_state_helper)
        self.assertIn("return rawState || 'off';", lane_state_helper)
        self.assertNotIn("activeWorkLaneName", lane_state_helper)
        self.assertNotIn("? 'working'", lane_state_helper)

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


class _HandlerFixture:
    def __init__(self, handler: controller_server.ControllerHandler) -> None:
        self.handler = handler
        self.responses: list[object] = []
        self.header_pairs: list[tuple[str, str]] = []
        self.end_count = 0

    @property
    def headers(self) -> dict[str, str]:
        return dict(self.header_pairs)

    @property
    def body(self) -> bytes:
        return self.handler.wfile.getvalue()

    def send_response(self, status: object) -> None:
        self.responses.append(status)

    def send_header(self, key: str, value: str) -> None:
        self.header_pairs.append((key, value))

    def end_headers(self) -> None:
        self.end_count += 1


class ControllerAssetResolutionTests(unittest.TestCase):
    def _response_handler(
        self,
        *,
        path: str | None = None,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> _HandlerFixture:
        handler = object.__new__(controller_server.ControllerHandler)
        fixture = _HandlerFixture(handler)

        if path is not None:
            handler.path = path
        if body is not None:
            handler.rfile = io.BytesIO(body)
            handler.headers = {"Content-Length": str(len(body))}
        if headers is not None:
            handler.headers = dict(headers)
        handler.wfile = io.BytesIO()
        handler.send_response = fixture.send_response
        handler.send_header = fixture.send_header
        handler.end_headers = fixture.end_headers
        return fixture

    def _asset_response(self, rel_path: str) -> tuple[list[object], dict[str, str], bytes, int]:
        fixture = self._response_handler()
        controller_server.ControllerHandler._serve_controller_asset(fixture.handler, rel_path)
        return fixture.responses, fixture.headers, fixture.body, fixture.end_count

    def _html_response(self) -> tuple[list[object], dict[str, str], bytes, int]:
        fixture = self._response_handler()
        controller_server.ControllerHandler._serve_html(fixture.handler)
        return fixture.responses, fixture.headers, fixture.body, fixture.end_count

    def _json_route_response(self, path: str) -> tuple[list[object], dict[str, str], bytes, int]:
        fixture = self._response_handler(path=path)
        controller_server.ControllerHandler.do_GET(fixture.handler)
        return fixture.responses, fixture.headers, fixture.body, fixture.end_count

    def _json_post_response(
        self,
        path: str,
        body: bytes = b"",
        *,
        headers: dict[str, str] | None = None,
    ) -> tuple[list[object], dict[str, str], bytes, int]:
        fixture = self._response_handler(path=path, body=body, headers=headers)
        controller_server.ControllerHandler.do_POST(fixture.handler)
        return fixture.responses, fixture.headers, fixture.body, fixture.end_count

    def _assert_json_response(
        self,
        responses: list[object],
        headers: dict[str, str],
        body: bytes,
        ended: int,
        *,
        status: object,
        payload: dict[str, object],
    ) -> dict[str, object]:
        decoded = json.loads(body.decode("utf-8"))
        self.assertEqual(responses, [status])
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Content-Length"], str(len(body)))
        self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
        self.assertEqual(decoded, payload)
        self.assertEqual(ended, 1)
        return decoded

    def _send_input_body(self, payload: object) -> bytes:
        return json.dumps(payload).encode("utf-8")

    def _assert_send_input_bad_request(
        self,
        responses: list[object],
        headers: dict[str, str],
        body: bytes,
        ended: int,
        *,
        error: str,
    ) -> None:
        self._assert_json_response(
            responses,
            headers,
            body,
            ended,
            status=controller_server.HTTPStatus.BAD_REQUEST,
            payload={"ok": False, "error": error},
        )

    def _assert_runtime_get_json_route(
        self,
        path: str,
        helper_name: str,
        helper_return: object,
        *,
        status: object,
        payload: dict[str, object],
    ) -> tuple[mock.Mock, dict[str, object]]:
        with mock.patch.object(controller_server, helper_name, return_value=helper_return) as backend:
            decoded = self._assert_json_response(
                *self._json_route_response(path),
                status=status,
                payload=payload,
            )
        return backend, decoded

    def _assert_runtime_post_json_route(
        self,
        path: str,
        helper_name: str,
        helper_return: object,
        *,
        status: object,
        payload: dict[str, object],
    ) -> mock.Mock:
        with mock.patch.object(controller_server, helper_name, return_value=helper_return) as backend:
            self._assert_json_response(
                *self._json_post_response(path),
                status=status,
                payload=payload,
            )
        return backend

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

    def test_resolve_real_controller_queue_js_assets(self) -> None:
        controller_dir = Path(__file__).resolve().parents[1] / "controller"

        queue_path, queue_type = controller_server._resolve_controller_asset("js/queue-presentation.js")
        cozy_path, cozy_type = controller_server._resolve_controller_asset("js/cozy.js")

        self.assertEqual(queue_path, controller_dir / "js" / "queue-presentation.js")
        self.assertEqual(cozy_path, controller_dir / "js" / "cozy.js")
        self.assertIn("javascript", queue_type)
        self.assertIn("javascript", cozy_type)

    def test_do_get_dispatches_real_controller_queue_js_assets(self) -> None:
        for rel_path in ("js/queue-presentation.js", "js/cozy.js"):
            with self.subTest(rel_path=rel_path):
                fixture = self._response_handler(path=f"/controller-assets/{rel_path}")
                with mock.patch.object(fixture.handler, "_serve_controller_asset") as serve_asset:
                    controller_server.ControllerHandler.do_GET(fixture.handler)
                serve_asset.assert_called_once_with(rel_path)

    def test_do_get_dispatches_controller_shell_routes_to_html(self) -> None:
        for path in ("/", "/controller", "/controller/"):
            with self.subTest(path=path):
                fixture = self._response_handler(path=path)
                with mock.patch.object(fixture.handler, "_serve_html") as serve_html:
                    controller_server.ControllerHandler.do_GET(fixture.handler)
                serve_html.assert_called_once_with()

    def test_serve_html_returns_controller_shell_with_queue_scripts(self) -> None:
        responses, headers, body, ended = self._html_response()
        html = body.decode("utf-8")
        queue_script = 'src="/controller-assets/js/queue-presentation.js"'
        cozy_script = 'src="/controller-assets/js/cozy.js"'

        self.assertEqual(responses, [controller_server.HTTPStatus.OK])
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertEqual(headers["Content-Length"], str(len(body)))
        self.assertGreater(len(body), 0)
        self.assertIn(queue_script, html)
        self.assertIn(cozy_script, html)
        self.assertLess(html.index(queue_script), html.index(cozy_script))
        self.assertEqual(ended, 1)

    def test_do_get_runtime_status_route_returns_json_snapshot(self) -> None:
        payload = {
            "runtime_state": "RUNNING",
            "automation_health": "ok",
            "runtime_snapshot": {
                "runtime_state": "RUNNING",
                "queue": {"status": "implement #2050", "class_name": "neutral"},
            },
        }

        get_status, decoded = self._assert_runtime_get_json_route(
            "/api/runtime/status",
            "get_runtime_status",
            (payload, controller_server.HTTPStatus.OK),
            status=controller_server.HTTPStatus.OK,
            payload=payload,
        )
        get_status.assert_called_once_with()
        self.assertEqual(decoded["runtime_state"], "RUNNING")
        self.assertEqual(decoded["automation_health"], "ok")
        self.assertEqual(decoded["runtime_snapshot"], payload["runtime_snapshot"])

    def test_do_get_monitor_snapshot_route_returns_json_payload(self) -> None:
        payload = {
            "ok": True,
            "runtime_snapshot": {
                "runtime_state": "RUNNING",
                "queue": {"status": "monitor #2051", "class_name": "neutral"},
            },
        }

        monitor_snapshot, _decoded = self._assert_runtime_get_json_route(
            "/api/runtime/monitor-snapshot",
            "runtime_monitor_snapshot",
            payload,
            status=controller_server.HTTPStatus.OK,
            payload=payload,
        )
        monitor_snapshot.assert_called_once_with()

    def test_do_get_agent_inspector_route_returns_json_payload(self) -> None:
        payload = {
            "ok": True,
            "agent": "Codex",
            "tail": "agent inspector payload",
        }

        agent_inspector, _decoded = self._assert_runtime_get_json_route(
            "/api/runtime/agent-inspector?agent=Codex&lines=77",
            "runtime_agent_inspector",
            (payload, controller_server.HTTPStatus.ACCEPTED),
            status=controller_server.HTTPStatus.ACCEPTED,
            payload=payload,
        )
        agent_inspector.assert_called_once_with(agent="Codex", lines=77)

    def test_do_get_capture_tail_route_returns_json_payload(self) -> None:
        payload = {
            "ok": True,
            "lane": "Codex",
            "text": "capture tail payload",
        }

        capture_tail, _decoded = self._assert_runtime_get_json_route(
            "/api/runtime/capture-tail?lane=Codex&lines=40",
            "runtime_capture_tail",
            (payload, controller_server.HTTPStatus.PARTIAL_CONTENT),
            status=controller_server.HTTPStatus.PARTIAL_CONTENT,
            payload=payload,
        )
        capture_tail.assert_called_once_with(lane="Codex", lines=40)

    def test_do_get_unknown_runtime_route_returns_json_404(self) -> None:
        self._assert_json_response(
            *self._json_route_response("/api/runtime/not-real"),
            status=controller_server.HTTPStatus.NOT_FOUND,
            payload={"error": "not found"},
        )

    def test_do_post_runtime_start_route_returns_json_payload(self) -> None:
        payload = {"ok": True, "message": "start accepted"}

        pipeline_start = self._assert_runtime_post_json_route(
            "/api/runtime/start",
            "pipeline_start",
            payload,
            status=controller_server.HTTPStatus.OK,
            payload=payload,
        )
        pipeline_start.assert_called_once_with()

    def test_do_post_runtime_stop_route_returns_json_payload(self) -> None:
        payload = {"ok": True, "message": "stop accepted"}

        pipeline_stop = self._assert_runtime_post_json_route(
            "/api/runtime/stop",
            "pipeline_stop",
            payload,
            status=controller_server.HTTPStatus.OK,
            payload=payload,
        )
        pipeline_stop.assert_called_once_with()

    def test_do_post_runtime_restart_route_returns_json_payload(self) -> None:
        payload = {"ok": True, "message": "restart accepted"}

        pipeline_restart = self._assert_runtime_post_json_route(
            "/api/runtime/restart",
            "pipeline_restart",
            payload,
            status=controller_server.HTTPStatus.OK,
            payload=payload,
        )
        pipeline_restart.assert_called_once_with()

    def test_do_post_send_input_route_parses_json_payload(self) -> None:
        request = {"lane": "Codex", "text": "hello"}
        response = {"ok": True, "lane": "Codex", "text": "hello"}

        with mock.patch.object(
            controller_server,
            "runtime_send_input",
            return_value=(response, controller_server.HTTPStatus.ACCEPTED),
        ) as send_input:
            responses, headers, body, ended = self._json_post_response(
                "/api/runtime/send-input",
                self._send_input_body(request),
            )

        send_input.assert_called_once_with(lane="Codex", text="hello")
        self._assert_json_response(
            responses,
            headers,
            body,
            ended,
            status=controller_server.HTTPStatus.ACCEPTED,
            payload=response,
        )

    def test_do_post_send_input_propagates_backend_failure(self) -> None:
        request = {"lane": "Codex", "text": "hello"}
        expected = {"ok": False, "error": "failed to send input"}

        with mock.patch.object(
            controller_server,
            "backend_runtime_send_input",
            return_value=False,
        ) as send_input:
            responses, headers, body, ended = self._json_post_response(
                "/api/runtime/send-input",
                self._send_input_body(request),
            )

        send_input.assert_called_once_with(
            controller_server.PROJECT_ROOT,
            controller_server.SESSION_NAME,
            "Codex",
            text="hello",
        )
        self._assert_json_response(
            responses,
            headers,
            body,
            ended,
            status=controller_server.HTTPStatus.BAD_GATEWAY,
            payload=expected,
        )

    def test_do_post_send_input_rejects_empty_body_payload(self) -> None:
        with mock.patch.object(controller_server, "backend_runtime_send_input") as send_input:
            responses, headers, body, ended = self._json_post_response("/api/runtime/send-input")

        send_input.assert_not_called()
        self._assert_send_input_bad_request(
            responses,
            headers,
            body,
            ended,
            error="lane is required",
        )

    def test_do_post_send_input_rejects_missing_lane_payload(self) -> None:
        request = {"text": "hello"}

        with mock.patch.object(controller_server, "backend_runtime_send_input") as send_input:
            responses, headers, body, ended = self._json_post_response(
                "/api/runtime/send-input",
                self._send_input_body(request),
            )

        send_input.assert_not_called()
        self._assert_send_input_bad_request(
            responses,
            headers,
            body,
            ended,
            error="lane is required",
        )

    def test_do_post_send_input_rejects_blank_text_payload(self) -> None:
        request = {"lane": "Codex", "text": "   "}

        with mock.patch.object(controller_server, "backend_runtime_send_input") as send_input:
            responses, headers, body, ended = self._json_post_response(
                "/api/runtime/send-input",
                self._send_input_body(request),
            )

        send_input.assert_not_called()
        self._assert_send_input_bad_request(
            responses,
            headers,
            body,
            ended,
            error="text is required",
        )

    def test_do_post_send_input_rejects_invalid_json(self) -> None:
        with mock.patch.object(controller_server, "runtime_send_input") as send_input:
            responses, headers, body, ended = self._json_post_response(
                "/api/runtime/send-input",
                b'{"lane": "Codex",',
            )

        send_input.assert_not_called()
        self._assert_send_input_bad_request(
            responses,
            headers,
            body,
            ended,
            error="invalid json",
        )

    def test_do_post_send_input_rejects_malformed_utf8_body(self) -> None:
        with mock.patch.object(controller_server, "runtime_send_input") as send_input:
            responses, headers, body, ended = self._json_post_response(
                "/api/runtime/send-input",
                b"\xff\xfe",
            )

        send_input.assert_not_called()
        self._assert_send_input_bad_request(
            responses,
            headers,
            body,
            ended,
            error="invalid json",
        )

    def test_do_post_send_input_rejects_invalid_content_length(self) -> None:
        with mock.patch.object(controller_server, "runtime_send_input") as send_input:
            responses, headers, body, ended = self._json_post_response(
                "/api/runtime/send-input",
                b'{"lane": "Codex", "text": "hello"}',
                headers={"Content-Length": "not-a-number"},
            )

        send_input.assert_not_called()
        self._assert_send_input_bad_request(
            responses,
            headers,
            body,
            ended,
            error="invalid json",
        )

    def test_do_post_send_input_rejects_negative_content_length(self) -> None:
        with mock.patch.object(controller_server, "runtime_send_input") as send_input:
            responses, headers, body, ended = self._json_post_response(
                "/api/runtime/send-input",
                b'{"lane": "Codex", "text": "hello"}',
                headers={"Content-Length": "-1"},
            )

        send_input.assert_not_called()
        self._assert_send_input_bad_request(
            responses,
            headers,
            body,
            ended,
            error="invalid json",
        )

    def test_do_post_send_input_rejects_non_object_json_payload(self) -> None:
        with mock.patch.object(controller_server, "runtime_send_input") as send_input:
            responses, headers, body, ended = self._json_post_response(
                "/api/runtime/send-input",
                b'["Codex", "hello"]',
            )

        send_input.assert_not_called()
        self._assert_send_input_bad_request(
            responses,
            headers,
            body,
            ended,
            error="invalid json",
        )

    def test_do_post_unknown_runtime_route_returns_json_404(self) -> None:
        self._assert_json_response(
            *self._json_post_response("/api/runtime/not-real"),
            status=controller_server.HTTPStatus.NOT_FOUND,
            payload={"error": "not found"},
        )

    def test_serve_real_controller_queue_js_assets_returns_js_response(self) -> None:
        cases = (
            ("js/queue-presentation.js", "PipelineQueuePresentation"),
            ("js/cozy.js", "queuePresentationHelper"),
        )
        for rel_path, marker in cases:
            with self.subTest(rel_path=rel_path):
                responses, headers, body, ended = self._asset_response(rel_path)

                self.assertEqual(responses, [controller_server.HTTPStatus.OK])
                self.assertIn("javascript", headers["Content-Type"])
                self.assertEqual(headers["Content-Length"], str(len(body)))
                self.assertEqual(headers["Cache-Control"], "no-cache")
                self.assertGreater(len(body), 0)
                self.assertIn(marker, body.decode("utf-8"))
                self.assertEqual(ended, 1)

    def test_serve_controller_asset_fails_closed_for_bad_paths(self) -> None:
        for rel_path in ("js/missing-queue-helper.js", "../server.py"):
            with self.subTest(rel_path=rel_path):
                responses, headers, body, ended = self._asset_response(rel_path)

                self.assertEqual(responses, [controller_server.HTTPStatus.NOT_FOUND])
                self.assertEqual(headers["Content-Type"], "application/json")
                self.assertEqual(headers["Content-Length"], str(len(body)))
                self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
                self.assertNotIn("Cache-Control", headers)
                self.assertNotIn("javascript", headers["Content-Type"])
                self.assertEqual(body.decode("utf-8"), '{"error": "asset not found"}')
                self.assertEqual(ended, 1)

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
