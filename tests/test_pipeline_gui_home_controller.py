from __future__ import annotations

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest import mock

from pipeline_gui.home_controller import HomeController


class PipelineGuiHomeControllerTest(unittest.TestCase):
    def test_get_cached_token_dashboard_starts_background_refresh_when_empty(self) -> None:
        controller = HomeController(Path("/tmp/projectH"), "aip-projectH")
        controller.start_token_dashboard_refresh = mock.Mock()

        dashboard = controller.get_cached_token_dashboard()

        self.assertIsNone(dashboard)
        controller.start_token_dashboard_refresh.assert_called_once_with(on_refresh=None)

    def test_build_snapshot_uses_runtime_status_as_single_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = HomeController(root, "aip-projectH")
            controller.get_cached_token_usage = mock.Mock(return_value={})
            controller.get_cached_token_dashboard = mock.Mock(return_value={"cached": True})
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "supervisor.pid").write_text(str(os.getpid()), encoding="utf-8")
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                        "events_path": ".pipeline/runs/20260411T010203Z-p123/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "events.jsonl").write_text(
                json.dumps({"event_type": "lane_working", "payload": {"lane": "Codex"}}) + "\n",
                encoding="utf-8",
            )
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "runtime_state": "RUNNING",
                        "automation_health": "attention",
                        "automation_reason_code": "stale_control_advisory",
                        "automation_incident_family": "stale_control_advisory",
                        "automation_next_action": "advisory_followup",
                        "automation_health_detail": "제어 슬롯 고착 감지됨 (961 사이클)",
                        "control_age_cycles": 961,
                        "stale_control_seq": True,
                        "stale_control_cycle_threshold": 900,
                        "stale_advisory_pending": True,
                        "watcher": {"alive": True, "pid": 321},
                        "lanes": [
                            {"name": "Claude", "state": "READY", "attachable": True},
                            {
                                "name": "Codex",
                                "state": "WORKING",
                                "attachable": True,
                                "note": "verify",
                                "progress_phase": "running_verification",
                            },
                        ],
                        "artifacts": {
                            "latest_work": {"path": "4/11/work.md", "mtime": 10.0},
                            "latest_verify": {"path": "4/11/verify.md", "mtime": 20.0},
                        },
                        "active_round": {"job_id": "job-1", "round": 2, "state": "VERIFYING"},
                        "compat": {
                            "control_slots": {"active": None, "stale": []},
                            "turn_state": {
                                "state": "CODEX_VERIFY",
                                "entered_at": 3.0,
                                "active_role": "verify",
                                "active_lane": "Claude",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            snapshot = controller.build_snapshot(selected_agent="Claude")

        self.assertEqual(snapshot.runtime_state, "RUNNING")
        self.assertEqual(snapshot.automation_health, "attention")
        self.assertEqual(snapshot.automation_reason_code, "stale_control_advisory")
        self.assertEqual(snapshot.automation_health_detail, "제어 슬롯 고착 감지됨 (961 사이클)")
        self.assertEqual(snapshot.control_age_cycles, 961)
        self.assertTrue(snapshot.stale_control_seq)
        self.assertEqual(snapshot.stale_control_cycle_threshold, 900)
        self.assertTrue(snapshot.stale_advisory_pending)
        self.assertEqual(snapshot.token_dashboard, {"cached": True})
        self.assertEqual(snapshot.watcher_pid, 321)
        self.assertEqual(snapshot.log_lines, ["lane_working Codex"])
        self.assertEqual(snapshot.work_name, "4/11/work.md")
        self.assertEqual(snapshot.verify_name, "4/11/verify.md")
        self.assertEqual(snapshot.verify_activity["status"], "VERIFY_RUNNING")
        self.assertEqual(snapshot.verify_activity["label"], "Claude 검증 실행 중")
        self.assertEqual(snapshot.run_summary["turn"], "Claude 검증 중")
        self.assertEqual(snapshot.agents[1], ("Codex", "WORKING", "progress:running_verification", ""))
        self.assertTrue(snapshot.lane_details["Codex"]["attachable"])
        self.assertEqual(snapshot.lane_details["Codex"]["note"], "verify")
        self.assertEqual(snapshot.lane_details["Codex"]["progress_phase"], "running_verification")

    def test_build_snapshot_prefers_verify_role_owner_when_turn_lane_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = HomeController(root, "aip-projectH")
            controller.get_cached_token_usage = mock.Mock(return_value={})
            controller.get_cached_token_dashboard = mock.Mock(return_value=None)
            pipeline_dir = root / ".pipeline"
            run_dir = pipeline_dir / "runs" / "20260411T010203Z-p123"
            run_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "supervisor.pid").write_text(str(os.getpid()), encoding="utf-8")
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "20260411T010203Z-p123",
                        "status_path": ".pipeline/runs/20260411T010203Z-p123/status.json",
                        "events_path": ".pipeline/runs/20260411T010203Z-p123/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "events.jsonl").write_text("", encoding="utf-8")
            (run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "runtime_state": "RUNNING",
                        "watcher": {"alive": True, "pid": 321},
                        "role_owners": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                        "lanes": [
                            {"name": "Claude", "state": "READY", "attachable": True},
                            {"name": "Codex", "state": "WORKING", "attachable": True, "note": "implement"},
                        ],
                        "artifacts": {
                            "latest_work": {"path": "4/11/work.md", "mtime": 10.0},
                            "latest_verify": {"path": "4/11/verify.md", "mtime": 20.0},
                        },
                        "active_round": {"job_id": "job-1", "round": 2, "state": "VERIFYING"},
                        "compat": {
                            "control_slots": {"active": None, "stale": []},
                            "turn_state": {
                                "state": "CODEX_VERIFY",
                                "entered_at": 3.0,
                                "active_role": "verify",
                                "active_lane": "",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            snapshot = controller.build_snapshot(selected_agent="Claude")

        self.assertEqual(snapshot.verify_activity["label"], "Claude 검증 실행 중")

    def test_home_controller_source_does_not_reintroduce_legacy_observers(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "pipeline_gui" / "home_controller.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("watcher_log_snapshot", source)
        self.assertNotIn("latest_md(", source)
        self.assertNotIn("detect_agent_status", source)
        self.assertNotIn("watcher_runtime_hints", source)


if __name__ == "__main__":
    unittest.main()
