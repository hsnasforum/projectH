from __future__ import annotations

import unittest
from unittest import mock

from pipeline_gui.home_presenter import (
    build_agent_card_presentations,
    build_console_presentation,
    build_control_presentation,
    build_empty_agent_card_presentation,
    build_pipeline_status_presentation,
)


def _base_snapshot() -> dict[str, object]:
    return {
        "runtime_state": "STOPPED",
        "automation_health": "ok",
        "automation_reason_code": "",
        "automation_incident_family": "",
        "automation_next_action": "continue",
        "degraded_reason": "",
        "session_ok": False,
        "watcher_alive": False,
        "watcher_pid": None,
        "agents": [],
        "lane_details": {},
        "pane_map": {},
        "token_usage": {},
        "token_dashboard": None,
        "work_name": "—",
        "work_mtime": 0.0,
        "verify_name": "—",
        "verify_mtime": 0.0,
        "log_lines": [],
        "run_summary": {},
        "control_slots": {"active": None, "stale": []},
        "verify_activity": None,
        "turn_state": None,
        "polled_at": 0.0,
    }


class PipelineGuiHomePresenterTest(unittest.TestCase):
    def test_build_pipeline_status_presentation_prefers_automation_health_label(self) -> None:
        presentation = build_pipeline_status_presentation(
            runtime_state="RUNNING",
            automation_health="attention",
        )

        self.assertEqual(presentation.pipeline_text, "파이프라인: ▲ 주의")
        self.assertEqual(presentation.status_text, "주의")
        self.assertEqual(presentation.fg, "#fb923c")

    def test_build_pipeline_status_presentation_uses_runtime_state_when_health_ok(self) -> None:
        presentation = build_pipeline_status_presentation(
            runtime_state="RUNNING",
            automation_health="ok",
        )

        self.assertEqual(presentation.pipeline_text, "파이프라인: ● 실행 중")
        self.assertEqual(presentation.status_text, "실행 중")

    def test_build_control_presentation_normal_active(self) -> None:
        presentation = build_control_presentation(
            {
                "active": {"file": "claude_handoff.md", "status": "implement", "label": "implement handoff", "mtime": 1.0},
                "stale": [{"file": "operator_request.md", "status": "needs_operator", "label": "operator wait", "mtime": 0.5}],
            },
            None,
        )

        self.assertIn("implement handoff", presentation.active_text)
        self.assertIn("mtime fallback", presentation.active_text)
        self.assertIn("operator_request.md", presentation.stale_text)
        self.assertEqual(presentation.active_fg, "#93c5fd")
        self.assertEqual(presentation.active_box_bg, "#101826")
        self.assertEqual(presentation.active_box_border, "#1d4ed8")
        self.assertTrue(presentation.stale_visible)

    def test_build_control_presentation_needs_operator_is_red(self) -> None:
        presentation = build_control_presentation(
            {
                "active": {"file": "operator_request.md", "status": "needs_operator", "label": "operator wait", "mtime": 1.0},
                "stale": [],
            },
            None,
        )

        self.assertIn("operator wait", presentation.active_text)
        self.assertEqual(presentation.active_fg, "#fca5a5")
        self.assertEqual(presentation.active_box_bg, "#2a1015")
        self.assertEqual(presentation.active_box_border, "#7f1d1d")
        self.assertFalse(presentation.stale_visible)

    def test_build_control_presentation_no_active_is_gray(self) -> None:
        presentation = build_control_presentation({"active": None, "stale": []}, None)

        self.assertEqual(presentation.active_text, "활성 제어: 없음")
        self.assertEqual(presentation.stale_text, "")
        self.assertEqual(presentation.active_fg, "#9ca3af")
        self.assertEqual(presentation.active_box_bg, "#141418")
        self.assertEqual(presentation.active_box_border, "#30363d")
        self.assertFalse(presentation.stale_visible)

    def test_build_control_presentation_preserves_seq_provenance(self) -> None:
        presentation = build_control_presentation(
            {
                "active": {"file": "claude_handoff.md", "status": "implement", "label": "implement handoff", "mtime": 1.0, "control_seq": 7},
                "stale": [{"file": "gemini_request.md", "status": "request_open", "label": "advisory request", "mtime": 0.5, "control_seq": 5}],
            },
            None,
        )

        self.assertIn("seq 7", presentation.active_text)
        self.assertNotIn("mtime fallback", presentation.active_text)
        self.assertIn("seq 5", presentation.stale_text)

    def test_build_control_presentation_prefers_verify_activity_over_handoff_label(self) -> None:
        presentation = build_control_presentation(
            {
                "active": {"file": "claude_handoff.md", "status": "implement", "label": "implement handoff", "mtime": 1.0, "control_seq": 8},
                "stale": [],
            },
            {
                "status": "VERIFY_RUNNING",
                "label": "verify 실행 중",
                "artifact_name": "2026-04-09-docs-response-origin-summary-richness-family-closure.md",
            },
        )

        self.assertIn("verify 실행 중", presentation.active_text)
        self.assertIn("family-closure.md", presentation.active_text)
        self.assertIn("claude_handoff.md", presentation.active_text)
        self.assertEqual(presentation.active_fg, "#93c5fd")

    def test_build_control_presentation_mtime_fallback_without_seq(self) -> None:
        presentation = build_control_presentation(
            {
                "active": {"file": "gemini_advice.md", "status": "advice_ready", "label": "verify follow-up", "mtime": 2.0},
                "stale": [],
            },
            None,
        )

        self.assertIn("mtime fallback", presentation.active_text)
        self.assertNotIn("seq ", presentation.active_text)

    def test_build_console_presentation_uses_live_fallback_and_log_titles(self) -> None:
        snapshot = _base_snapshot()
        snapshot.update(
            {
                "runtime_state": "RUNNING",
                "session_ok": True,
                "watcher_alive": True,
                "agents": [("Claude", "WORKING", "1m 2s", ""), ("Codex", "READY", "", "")],
                "lane_details": {
                    "Claude": {
                        "state": "WORKING",
                        "note": "1m 2s",
                        "attachable": True,
                        "pid": 321,
                        "last_heartbeat_at": "2026-04-10T12:00:00Z",
                    }
                },
                "run_summary": {"turn": "Claude", "phase": "VERIFY_DONE", "job": "2026-04-10-history-card-header-b-3a1a225d"},
                "work_name": "work.md",
                "work_mtime": 10.0,
                "verify_name": "verify.md",
                "verify_mtime": 15.0,
                "turn_state": {"state": "IDLE", "entered_at": 0.0},
                "log_lines": ["  short  ", "x" * 150],
            }
        )

        with mock.patch("pipeline_gui.home_presenter.time_ago", side_effect=["방금 전", "방금 전"]):
            presentation = build_console_presentation(selected_agent="Claude", snapshot=snapshot)

        self.assertEqual(presentation.focus_title, "CLAUDE • Runtime 상태")
        self.assertIn("runtime: RUNNING", presentation.focus_text)
        self.assertIn("lane_state: WORKING", presentation.focus_text)
        self.assertIn("note: 1m 2s", presentation.focus_text)
        self.assertIn("attachable: true", presentation.focus_text)
        self.assertIn("pid: 321", presentation.focus_text)
        self.assertIn("active_turn: Claude", presentation.focus_text)
        self.assertEqual(presentation.artifacts_title, "라운드 기록")
        self.assertEqual(presentation.artifact_color, "#c0a060")
        self.assertIn("턴: Claude", presentation.run_context_text)
        self.assertIn("단계: VERIFY_DONE", presentation.run_context_text)
        self.assertIn("작업: 04-10-history-card-header-b-3a1a225d", presentation.run_context_text)
        self.assertEqual(presentation.run_context_fg, "#5b9cf6")
        self.assertEqual(presentation.work_text, "최신 work: work.md (방금 전)")
        self.assertEqual(presentation.verify_text, "최신 verify: verify.md (방금 전)")
        self.assertEqual(presentation.log_title, "Runtime 이벤트 • Claude → VERIFY_DONE")
        self.assertIn("short", presentation.log_text)
        self.assertTrue(presentation.log_text.endswith("…"))

    def test_build_console_presentation_keeps_raw_automation_note_in_details(self) -> None:
        snapshot = _base_snapshot()
        snapshot.update(
            {
                "runtime_state": "RUNNING",
                "automation_health": "attention",
                "automation_reason_code": "dispatch_stall",
                "automation_incident_family": "dispatch_stall",
                "automation_next_action": "verify_followup",
            }
        )

        presentation = build_console_presentation(selected_agent="Codex", snapshot=snapshot)

        self.assertIn("automation_health: attention", presentation.focus_text)
        self.assertIn("automation_reason_code: dispatch_stall", presentation.focus_text)
        self.assertIn("automation_incident_family: dispatch_stall", presentation.focus_text)
        self.assertIn("automation_next_action: verify_followup", presentation.focus_text)

    def test_build_console_presentation_distinguishes_current_round_work_gap(self) -> None:
        snapshot = _base_snapshot()
        snapshot.update(
            {
                "runtime_state": "RUNNING",
                "session_ok": True,
                "watcher_alive": True,
                "work_name": "work.md",
                "work_mtime": 10.0,
                "verify_name": "verify.md",
                "verify_mtime": 15.0,
                "turn_state": {"state": "IMPLEMENT_ACTIVE", "legacy_state": "CLAUDE_ACTIVE", "entered_at": 20.0},
            }
        )

        with mock.patch("pipeline_gui.home_presenter.time_ago", side_effect=["조금 전", "방금 전"]):
            presentation = build_console_presentation(selected_agent="Claude", snapshot=snapshot)

        self.assertEqual(presentation.artifacts_title, "라운드 기록")
        self.assertEqual(
            presentation.work_text,
            "현재 라운드 work: 아직 기록되지 않음 · 최신 work: work.md (조금 전)",
        )
        self.assertEqual(presentation.verify_text, "최신 verify: verify.md (방금 전)")

    def test_build_console_presentation_distinguishes_current_round_verify_gap(self) -> None:
        snapshot = _base_snapshot()
        snapshot.update(
            {
                "runtime_state": "RUNNING",
                "session_ok": True,
                "watcher_alive": True,
                "work_name": "work.md",
                "work_mtime": 10.0,
                "verify_name": "verify.md",
                "verify_mtime": 15.0,
                "turn_state": {"state": "VERIFY_ACTIVE", "legacy_state": "CODEX_VERIFY", "entered_at": 20.0},
            }
        )

        with mock.patch("pipeline_gui.home_presenter.time_ago", side_effect=["조금 전", "방금 전", "방금 전"]):
            presentation = build_console_presentation(selected_agent="Codex", snapshot=snapshot)

        self.assertEqual(presentation.work_text, "검증 기준 work: work.md (방금 전)")
        self.assertEqual(
            presentation.verify_text,
            "현재 라운드 verify: 아직 미기록 · 최신 verify: verify.md (방금 전)",
        )

    def test_build_agent_card_presentations_updates_working_anchor_and_styles(self) -> None:
        presentations, working_since = build_agent_card_presentations(
            agents=[("Claude", "WORKING", "1m 2s", ""), ("Codex", "READY", "", "")],
            selected_agent="Claude",
            token_usage={},
            working_since={},
            now=100.0,
        )

        self.assertEqual(len(presentations), 2)
        self.assertIn("Claude", working_since)
        self.assertAlmostEqual(working_since["Claude"], 38.0)
        self.assertEqual(presentations[0].status_text, "작업 중")
        self.assertEqual(presentations[0].note_text, "1m 2s")
        self.assertEqual(presentations[0].card_border, "#6ea8ff")
        self.assertEqual(presentations[0].card_thickness, 3)
        self.assertEqual(presentations[0].card_bg, "#1a1a30")
        self.assertEqual(presentations[1].status_text, "대기")
        self.assertEqual(presentations[1].note_text, "대기 중")
        self.assertEqual(presentations[1].card_border, "#1e1e2e")

    def test_build_agent_card_presentations_localizes_machine_notes(self) -> None:
        presentations, _working_since = build_agent_card_presentations(
            agents=[
                ("Codex", "READY", "signal_mismatch", ""),
                ("Claude", "READY", "waiting_next_control", ""),
                ("Gemini", "READY", "progress:operator_gate_followup", ""),
            ],
            selected_agent="Codex",
            token_usage={},
            working_since={},
            now=100.0,
        )

        self.assertEqual(presentations[0].note_text, "상태 확인 필요")
        self.assertEqual(presentations[1].note_text, "다음 지시 대기")
        self.assertEqual(presentations[2].note_text, "operator gate 후속 처리")

    def test_build_agent_card_presentations_reuses_anchor_and_prefers_usage_note(self) -> None:
        presentations, working_since = build_agent_card_presentations(
            agents=[("Codex", "WORKING", "verify 37s", "2x until April 2nd")],
            selected_agent="Claude",
            token_usage={
                "Codex": {
                    "available": True,
                    "used_percent": 14.2,
                    "session_tokens": 42100,
                    "today_tokens": 108200,
                    "reset_at": "03:00",
                }
            },
            working_since={"Codex": 50.0},
            now=100.0,
        )

        self.assertEqual(working_since["Codex"], 63.0)
        self.assertEqual(presentations[0].note_text, None)
        self.assertIn("14% 사용", presentations[0].quota_text)
        self.assertNotIn("2x until April 2nd", presentations[0].quota_text)
        self.assertEqual(presentations[0].card_border, "#4ade80")
        self.assertEqual(presentations[0].card_thickness, 2)
        self.assertEqual(presentations[0].card_bg, "#0e2a18")

    def test_build_empty_agent_card_presentation_matches_placeholder_state(self) -> None:
        presentation = build_empty_agent_card_presentation()

        self.assertEqual(presentation.status_text, "—")
        self.assertEqual(presentation.note_text, "")
        self.assertEqual(presentation.quota_text, "사용량: —")
        self.assertEqual(presentation.card_border, "#2a2a2a")


if __name__ == "__main__":
    unittest.main()
