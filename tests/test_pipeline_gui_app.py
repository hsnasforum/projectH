from __future__ import annotations

import unittest
from unittest import mock

from pipeline_gui.app import PipelineGUI
from pipeline_gui.token_queries import CollectorStatus, TodayTotals, TokenDashboard


class _Var:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def set(self, value: str) -> None:
        self.value = value

    def get(self) -> str:
        return self.value


class _Widget:
    def __init__(self) -> None:
        self.state = None

    def configure(self, **kwargs: object) -> None:
        if "state" in kwargs:
            self.state = kwargs["state"]


class PipelineGuiAppTest(unittest.TestCase):
    def test_ask_yn_calls_messagebox_directly_on_main_thread(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.root = mock.Mock()
        with mock.patch("pipeline_gui.app.messagebox.askyesno", return_value=True) as ask_mock:
            result = PipelineGUI._ask_yn(gui, "Title", "Body", icon="question")
        self.assertTrue(result)
        ask_mock.assert_called_once_with("Title", "Body", icon="question")
        gui.root.after.assert_not_called()

    def test_apply_token_dashboard_shows_loading_during_token_action_without_db(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.selected_agent = "Claude"
        gui._action_in_progress = True
        gui._token_action_var = _Var("Action: FULL HISTORY · 0% · preparing · 0.0s · scan 0/0")
        gui._token_status_var = _Var()
        gui._token_totals_var = _Var()
        gui._token_agents_var = _Var()
        gui._token_selected_var = _Var()
        gui._token_jobs_var = _Var()
        gui._last_snapshot = {"token_usage": {}}
        gui._fmt_count = PipelineGUI._fmt_count.__get__(gui, PipelineGUI)

        dashboard = TokenDashboard(
            display_day="",
            collector_status=CollectorStatus(),
            today_totals=TodayTotals(),
            agent_totals=[],
            top_jobs=[],
        )

        PipelineGUI._apply_token_dashboard(gui, dashboard)

        self.assertEqual(gui._token_status_var.get(), "Collector: loading...")
        self.assertEqual(gui._token_totals_var.get(), "Today: loading...")
        self.assertEqual(gui._token_agents_var.get(), "Agents: loading...")
        self.assertEqual(gui._token_selected_var.get(), "Selected CLAUDE: loading...")
        self.assertEqual(gui._token_jobs_var.get(), "Top jobs: loading...")

    def test_apply_token_dashboard_shows_selected_agent_detail(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.selected_agent = "Codex"
        gui._action_in_progress = False
        gui._token_action_var = _Var("Action: —")
        gui._token_status_var = _Var()
        gui._token_totals_var = _Var()
        gui._token_agents_var = _Var()
        gui._token_selected_var = _Var()
        gui._token_jobs_var = _Var()
        gui._last_snapshot = {
            "token_usage": {
                "Codex": {
                    "available": True,
                    "used_percent": 14.2,
                    "session_tokens": 42100,
                    "today_tokens": 108200,
                    "reset_at": "03:00",
                }
            }
        }
        gui._fmt_count = PipelineGUI._fmt_count.__get__(gui, PipelineGUI)

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

        PipelineGUI._apply_token_dashboard(gui, dashboard)

        self.assertIn("Selected CODEX:", gui._token_selected_var.get())
        self.assertIn("usage 14% used", gui._token_selected_var.get())
        self.assertIn("latest 2026-04-05 1.2k/340", gui._token_selected_var.get())
        self.assertIn("linked 4/12", gui._token_selected_var.get())

    def test_start_token_maintenance_action_uses_shared_setup_flow(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._action_in_progress = False
        gui._ask_yn = mock.Mock(return_value=True)
        gui._lock_buttons = mock.Mock()
        gui._update_token_action_progress = mock.Mock()
        gui._start_token_ui_pump = mock.Mock()
        gui._token_action_initial_payload = mock.Mock(return_value={"phase": "preparing"})
        worker = mock.Mock()

        with mock.patch("pipeline_gui.app.threading.Thread") as thread_cls:
            thread = thread_cls.return_value
            PipelineGUI._start_token_maintenance_action(
                gui,
                action_label="FULL HISTORY",
                dialog_title="Title",
                dialog_message="Body",
                icon="question",
                lock_message="LOCK",
                worker_target=worker,
            )

        gui._ask_yn.assert_called_once_with("Title", "Body", icon="question")
        gui._lock_buttons.assert_called_once_with("LOCK")
        gui._update_token_action_progress.assert_called_once_with("FULL HISTORY", {"phase": "preparing"})
        gui._start_token_ui_pump.assert_called_once_with()
        thread_cls.assert_called_once_with(target=worker, daemon=True)
        thread.start.assert_called_once_with()

    def test_run_token_maintenance_action_enqueues_shared_success_flow(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        queued: list[object] = []
        gui._enqueue_token_ui = lambda callback: queued.append(callback)
        gui._format_token_action_done = mock.Mock(return_value="Action: done")
        gui._set_token_action_text = mock.Mock()
        gui._refresh_token_dashboard_async = mock.Mock()
        gui._start_token_usage_refresh = mock.Mock()
        gui._unlock_buttons = mock.Mock()
        gui._clear_msg_later = mock.Mock()

        PipelineGUI._run_token_maintenance_action(
            gui,
            action_label="REBUILD DB",
            action_runner=lambda: {
                "summary": {"elapsed_sec": 3.2, "usage_inserted": 12},
                "backup_path": "/tmp/usage.backup-1.db",
            },
            unlock_message_builder=lambda summary, backup_path: (
                f"done {summary['elapsed_sec']:.1f} {backup_path}"
            ),
            error_message="should not be used",
        )

        for callback in queued:
            callback()

        gui._format_token_action_done.assert_called_once()
        gui._set_token_action_text.assert_called_once_with("Action: done")
        gui._refresh_token_dashboard_async.assert_called_once_with()
        gui._start_token_usage_refresh.assert_called_once_with(force=True)
        gui._unlock_buttons.assert_called_once_with("done 3.2 /tmp/usage.backup-1.db")
        gui._clear_msg_later.assert_called_once_with(10000)

    def test_format_token_job_segment_shortens_link_method(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
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

        text = PipelineGUI._format_token_job_segment(gui, job)

        self.assertIn("verify-long-job-name", text)
        self.assertIn("$1.25", text)
        self.assertIn("dispatch", text)
        self.assertIn("c=0.90", text)
        self.assertIn("low=0/3", text)

    def test_set_main_button_states_handles_disabled_and_ready_modes(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.btn_setup = _Widget()
        gui.btn_start = _Widget()
        gui.btn_stop = _Widget()
        gui.btn_restart = _Widget()
        gui.btn_attach = _Widget()
        gui.btn_token_backfill = _Widget()
        gui.btn_token_rebuild = _Widget()

        PipelineGUI._set_main_button_states(gui, all_disabled=True)
        self.assertEqual(gui.btn_setup.state, "disabled")
        self.assertEqual(gui.btn_start.state, "disabled")
        self.assertEqual(gui.btn_token_rebuild.state, "disabled")

        PipelineGUI._set_main_button_states(gui, all_disabled=False, can_start=True, session_ok=True)
        self.assertEqual(gui.btn_setup.state, "normal")
        self.assertEqual(gui.btn_start.state, "normal")
        self.assertEqual(gui.btn_stop.state, "normal")
        self.assertEqual(gui.btn_restart.state, "normal")
        self.assertEqual(gui.btn_attach.state, "normal")
        self.assertEqual(gui.btn_token_backfill.state, "normal")
        self.assertEqual(gui.btn_token_rebuild.state, "normal")


if __name__ == "__main__":
    unittest.main()
