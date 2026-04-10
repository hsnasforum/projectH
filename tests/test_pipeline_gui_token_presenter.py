from __future__ import annotations

import unittest

from pipeline_gui.token_presenter import build_token_panel_presentation, format_token_job_segment
from pipeline_gui.token_queries import CollectorStatus, TodayTotals, TokenDashboard


class PipelineGuiTokenPresenterTest(unittest.TestCase):
    def test_build_token_panel_presentation_shows_empty_labels_when_dashboard_missing(self) -> None:
        presentation = build_token_panel_presentation(
            selected_agent="Claude",
            token_usage={},
            dashboard=None,
            token_loading=False,
        )

        self.assertEqual(presentation.status_text, "수집기: —")
        self.assertEqual(presentation.totals_text, "오늘: —")
        self.assertEqual(presentation.agents_text, "에이전트: —")
        self.assertEqual(presentation.selected_text, "선택 에이전트 CLAUDE: —")
        self.assertEqual(presentation.jobs_text, "주요 작업: —")

    def test_build_token_panel_presentation_shows_loading_during_token_action_without_db(self) -> None:
        dashboard = TokenDashboard(
            display_day="",
            collector_status=CollectorStatus(),
            today_totals=TodayTotals(),
            agent_totals=[],
            top_jobs=[],
        )

        presentation = build_token_panel_presentation(
            selected_agent="Claude",
            token_usage={},
            dashboard=dashboard,
            token_loading=True,
        )

        self.assertEqual(presentation.status_text, "수집기: 불러오는 중...")
        self.assertEqual(presentation.totals_text, "오늘: 불러오는 중...")
        self.assertEqual(presentation.agents_text, "에이전트: 불러오는 중...")
        self.assertEqual(presentation.selected_text, "선택 에이전트 CLAUDE: 불러오는 중...")
        self.assertEqual(presentation.jobs_text, "주요 작업: 불러오는 중...")

    def test_build_token_panel_presentation_shows_selected_agent_detail(self) -> None:
        agent_row = type(
            "AgentRow",
            (),
            {
                "source": "codex",
                "events": 12,
                "linked_events": 4,
                "input_tokens": 1200,
                "output_tokens": 340,
                "total_cost_usd": 0.0,
            },
        )()
        dashboard = TokenDashboard(
            display_day="2026-04-05",
            collector_status=CollectorStatus(available=True, phase="idle"),
            today_totals=TodayTotals(input_tokens=1200, output_tokens=340),
            agent_totals=[agent_row],
            top_jobs=[],
        )

        presentation = build_token_panel_presentation(
            selected_agent="Codex",
            token_usage={
                "Codex": {
                    "available": True,
                    "used_percent": 14.2,
                    "session_tokens": 42100,
                    "today_tokens": 108200,
                    "reset_at": "03:00",
                }
            },
            dashboard=dashboard,
            token_loading=False,
        )

        self.assertIn("선택 에이전트 CODEX:", presentation.selected_text)
        self.assertIn("usage 14% 사용", presentation.selected_text)
        self.assertIn("최근 2026-04-05 1.2k/340", presentation.selected_text)
        self.assertIn("연결 4/12", presentation.selected_text)

    def test_format_token_job_segment_shortens_link_method(self) -> None:
        job = type(
            "JobRow",
            (),
            {
                "job_id": "20260406-verify-long-job-name",
                "total_cost_usd": 1.25,
                "primary_link_method": "dispatch_slot_verify_window",
                "max_confidence": 0.9,
                "low_confidence_events": 0,
                "events": 3,
            },
        )()

        text = format_token_job_segment(job)

        self.assertIn("verify-long-job-name", text)
        self.assertIn("$1.25", text)
        self.assertIn("dispatch", text)
        self.assertIn("c=0.90", text)
        self.assertIn("low=0/3", text)


if __name__ == "__main__":
    unittest.main()
