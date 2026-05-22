from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from watcher_status_writer import build_runtime_status_payload, write_runtime_status


class WatcherStatusWriterTest(unittest.TestCase):
    def _lane_statuses(self, heartbeat_iso: str) -> list[dict[str, object]]:
        return [
            {
                "name": "Codex",
                "state": "WORKING",
                "attachable": True,
                "last_heartbeat_at": heartbeat_iso,
            }
        ]

    def test_build_payload_uses_active_control_signal(self) -> None:
        heartbeat_iso = "2026-05-22T00:00:00Z"
        active_control = SimpleNamespace(
            path=Path("claude_handoff.md"),
            control_seq=42,
            status="implement",
            mtime=0.0,
            slot_id="implement_handoff",
            canonical_file="implement_handoff.md",
            is_legacy_alias=True,
        )

        payload = build_runtime_status_payload(
            run_id="run-1",
            turn_state="IMPLEMENT_ACTIVE",
            legacy_turn_state="IMPLEMENT_ACTIVE",
            runtime_controls={"advisory_enabled": False},
            active_control=active_control,
            fallback_active_control_file="",
            fallback_active_control_seq=-1,
            control_seq_age_cycles=3,
            lane_statuses=self._lane_statuses(heartbeat_iso),
            heartbeat_iso=heartbeat_iso,
        )

        control = payload["control"]
        self.assertIsInstance(control, dict)
        self.assertEqual(control["active_control_file"], ".pipeline/claude_handoff.md")
        self.assertEqual(control["active_control_canonical_file"], ".pipeline/implement_handoff.md")
        self.assertEqual(control["active_control_status"], "implement")
        self.assertEqual(control["active_control_seq"], 42)
        self.assertTrue(control["active_control_is_legacy_alias"])
        self.assertEqual(payload["runtime_controls"], {"advisory_enabled": False})
        self.assertEqual(payload["lanes"], self._lane_statuses(heartbeat_iso))
        self.assertIn("automation_health", payload)
        self.assertIn("automation_next_action", payload)

    def test_build_payload_uses_turn_fallback_when_active_control_missing(self) -> None:
        heartbeat_iso = "2026-05-22T00:00:00Z"

        payload = build_runtime_status_payload(
            run_id="run-1",
            turn_state="VERIFY_ACTIVE",
            legacy_turn_state="CODEX_VERIFY",
            runtime_controls={},
            active_control=None,
            fallback_active_control_file="implement_handoff.md",
            fallback_active_control_seq=17,
            control_seq_age_cycles=0,
            lane_statuses=self._lane_statuses(heartbeat_iso),
            heartbeat_iso=heartbeat_iso,
        )

        control = payload["control"]
        self.assertIsInstance(control, dict)
        self.assertEqual(control["active_control_file"], ".pipeline/implement_handoff.md")
        self.assertEqual(control["active_control_seq"], 17)
        self.assertEqual(control["active_control_status"], "none")
        self.assertFalse(control["active_control_is_legacy_alias"])
        self.assertEqual(payload["turn_state"], "VERIFY_ACTIVE")
        self.assertEqual(payload["legacy_turn_state"], "CODEX_VERIFY")

    def test_write_runtime_status_writes_json_and_updates_run_pointer(self) -> None:
        heartbeat_iso = "2026-05-22T00:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "status.json"
            pointer_calls: list[str] = []

            written = write_runtime_status(
                enabled=True,
                run_status_path=status_path,
                run_id="run-1",
                turn_state="IDLE",
                legacy_turn_state="IDLE",
                runtime_controls={},
                active_control=None,
                fallback_active_control_file="",
                fallback_active_control_seq=-1,
                control_seq_age_cycles=0,
                lane_statuses=self._lane_statuses(heartbeat_iso),
                heartbeat_iso=heartbeat_iso,
                write_current_run_pointer=lambda: pointer_calls.append("called"),
            )

            self.assertIsNotNone(written)
            self.assertEqual(pointer_calls, ["called"])
            self.assertFalse(status_path.with_suffix(".json.tmp").exists())
            data = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(data["run_id"], "run-1")
            self.assertEqual(data["last_heartbeat_at"], heartbeat_iso)

    def test_disabled_writer_does_not_write_or_update_run_pointer(self) -> None:
        heartbeat_iso = "2026-05-22T00:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "status.json"
            pointer_calls: list[str] = []

            written = write_runtime_status(
                enabled=False,
                run_status_path=status_path,
                run_id="run-1",
                turn_state="IDLE",
                legacy_turn_state="IDLE",
                runtime_controls={},
                active_control=None,
                fallback_active_control_file="",
                fallback_active_control_seq=-1,
                control_seq_age_cycles=0,
                lane_statuses=self._lane_statuses(heartbeat_iso),
                heartbeat_iso=heartbeat_iso,
                write_current_run_pointer=lambda: pointer_calls.append("called"),
            )

            self.assertIsNone(written)
            self.assertEqual(pointer_calls, [])
            self.assertFalse(status_path.exists())


if __name__ == "__main__":
    unittest.main()
