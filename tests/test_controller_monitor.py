from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from controller.monitor import AgentLogParser, ParsedLogEvent, RuntimeMonitorStateManager


class ControllerMonitorTests(unittest.TestCase):
    def test_agent_log_parser_extracts_agent_state_tokens_and_prompt(self) -> None:
        parser = AgentLogParser()
        event = parser.parse_line("Codex status=working tokens=1,234 prompt=Fix controller tests", source_path="/tmp/codex.log")

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.agent_id, "Codex")
        self.assertEqual(event.state, "working")
        self.assertEqual(event.tokens, 1234)
        self.assertEqual(event.prompt, "Fix controller tests")
        self.assertEqual(event.source_path, "/tmp/codex.log")

    def test_agent_log_parser_extracts_coordination_metadata(self) -> None:
        parser = AgentLogParser()
        event = parser.parse_line(
            '{"agent":"Claude","event_type":"handoff","target_agent_id":"Codex",'
            '"team_id":"round-7","parent_prompt_id":"prompt-1","approval_wait":true,'
            '"message":"delegate verification"}',
            source_path="/tmp/events.jsonl",
        )

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.agent_id, "Claude")
        self.assertEqual(event.event_type, "handoff")
        self.assertEqual(event.target_agent_id, "Codex")
        self.assertEqual(event.team_id, "round-7")
        self.assertEqual(event.parent_id, "prompt-1")
        self.assertTrue(event.approval_wait)

    def test_state_manager_watches_extra_log_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            project.mkdir()
            log_dir = Path(td) / "logs"
            log_dir.mkdir()
            log_path = log_dir / "session.log"
            log_path.write_text("Claude state=ready tokens=42 prompt=wait for handoff\n", encoding="utf-8")

            manager = RuntimeMonitorStateManager(project, extra_log_roots=[log_dir])
            snapshot = manager.snapshot(
                runtime_status={"runtime_state": "RUNNING", "lanes": []},
                dashboard_payload={"today_totals": {}, "collector_status": {}, "agent_totals": []},
            )

        self.assertEqual(snapshot["state_manager"]["parsed_events"], 1)
        self.assertEqual(snapshot["log_state"]["Claude"]["state"], "ready")
        self.assertEqual(snapshot["log_state"]["Claude"]["tokens"], 42)
        self.assertIn("wait for handoff", snapshot["log_state"]["Claude"]["prompt"])

    def test_state_manager_ingests_external_events_for_future_ports(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            project.mkdir()
            manager = RuntimeMonitorStateManager(project)

            result = manager.submit_external_event(
                {
                    "agent": "Claude",
                    "event_type": "handoff",
                    "target_agent_id": "Codex",
                    "team_id": "team-a",
                    "parent_prompt_id": "prompt-root",
                    "message": "handoff to verifier",
                    "tokens": 99,
                },
                source_name="local_socket:test",
            )
            manager.ingest_events(
                [
                    ParsedLogEvent(
                        agent_id="Codex",
                        state="ready",
                        team_id="team-a",
                        parent_id="prompt-root",
                        approval_wait=True,
                        message="waiting for approval",
                        source_path="rest:test",
                    )
                ]
            )
            snapshot = manager.snapshot(
                runtime_status={"runtime_state": "RUNNING", "lanes": []},
                dashboard_payload={"today_totals": {}, "collector_status": {}, "agent_totals": []},
            )

        self.assertEqual(result["parsed_events"], 1)
        self.assertIn("memory_port", snapshot["state_manager"]["input_ports"])
        self.assertEqual(snapshot["log_state"]["Claude"]["team_id"], "team-a")
        self.assertEqual(snapshot["coordination_state"]["Codex"]["parent_id"], "prompt-root")
        self.assertTrue(snapshot["coordination_state"]["Codex"]["approval_wait"])
        self.assertEqual(snapshot["communications"][0]["from"], "Claude")
        self.assertEqual(snapshot["communications"][0]["to"], "Codex")
        self.assertEqual(snapshot["teams"][0]["agents"], ["Claude", "Codex"])


if __name__ == "__main__":
    unittest.main()
