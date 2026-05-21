from __future__ import annotations

import unittest

from pipeline_runtime.lane_catalog import default_role_bindings
from pipeline_runtime.state_contract import (
    RUNTIME_SNAPSHOT_CONTRACT_VERSION,
    _extract_autonomy_section,
    _extract_control_section,
    _extract_lane_summary,
    _extract_round_section,
    _role_owners,
    reduce_runtime_snapshot,
)


class RuntimeStateContractTests(unittest.TestCase):
    def _base_status(self) -> dict[str, object]:
        return {
            "runtime_state": "RUNNING",
            "automation_health": "ok",
            "automation_reason_code": "",
            "automation_incident_family": "",
            "automation_next_action": "continue",
            "stale_advisory_pending": False,
            "control": {
                "active_control_status": "none",
                "active_control_seq": -1,
                "active_control_file": "",
            },
            "turn_state": {"state": "IDLE"},
            "watcher": {"alive": True},
            "lanes": [],
        }

    def test_live_idle_queue_is_empty_only_without_control_or_round(self) -> None:
        snapshot = reduce_runtime_snapshot(self._base_status())

        self.assertEqual(snapshot["contract_version"], RUNTIME_SNAPSHOT_CONTRACT_VERSION)
        self.assertTrue(snapshot["queue"]["no_queued_pipeline_task"])
        self.assertEqual(snapshot["queue"]["status"], "No queued pipeline task")
        self.assertEqual(snapshot["invariants"]["violations"], [])

    def test_default_role_owners_follow_lane_catalog_defaults(self) -> None:
        self.assertEqual(dict(_role_owners({})), default_role_bindings())

    def test_extracted_sections_are_independently_testable(self) -> None:
        status = self._base_status()
        status["active_round"] = {"state": "VERIFYING", "job_id": "job-1"}
        status["turn_state"] = {"state": "VERIFY_ACTIVE", "active_role": "verify", "active_lane": "Codex"}
        status["lanes"] = [{"name": "Codex", "state": "READY", "note": "prompt_visible", "pid": 123}]

        autonomy = _extract_autonomy_section(status)
        control = _extract_control_section(
            status,
            show_live=bool(autonomy["show_live"]),
            uncertain=bool(autonomy["uncertain"]),
        )
        round_section = _extract_round_section(
            status,
            show_live=bool(autonomy["show_live"]),
            uncertain=bool(autonomy["uncertain"]),
        )
        lane_summary = _extract_lane_summary(
            status,
            round_state=str(round_section["round_state"]),
            turn_state=round_section["turn_state"],
        )

        self.assertEqual(autonomy["runtime_state"], "RUNNING")
        self.assertEqual(control["control_status"], "none")
        self.assertEqual(round_section["round_state"], "VERIFYING")
        self.assertEqual(lane_summary["active_lane"], "Codex")
        self.assertEqual(lane_summary["lanes"][0]["lifecycle"], "ready")

    def test_reduce_runtime_snapshot_preserves_contract_shape(self) -> None:
        snapshot = reduce_runtime_snapshot(self._base_status())

        self.assertEqual(
            set(snapshot),
            {
                "schema_version",
                "contract_version",
                "runtime_state",
                "show_live",
                "control_state",
                "round_state",
                "active_lane",
                "health",
                "queue",
                "lanes",
                "invariants",
                "suppressed_operator_candidate",
            },
        )
        self.assertEqual(set(snapshot["health"]), {"state", "reason_code", "incident_family", "next_action"})
        self.assertEqual(set(snapshot["queue"]), {"no_queued_pipeline_task", "status", "class_name"})
        self.assertEqual(set(snapshot["invariants"]), {"violations"})

    def test_compat_active_control_prevents_empty_queue_surface(self) -> None:
        status = self._base_status()
        status["compat"] = {
            "control_slots": {
                "active": {
                    "file": "implement_handoff.md",
                    "status": "implement",
                    "control_seq": 2042,
                },
                "stale": [],
            }
        }

        snapshot = reduce_runtime_snapshot(status)

        self.assertFalse(snapshot["queue"]["no_queued_pipeline_task"])
        self.assertEqual(snapshot["queue"]["status"], "implement #2042")
        self.assertIn(
            "active_control_slot_not_surfaced",
            snapshot["invariants"]["violations"],
        )

    def test_suppressed_operator_compat_control_does_not_look_queued(self) -> None:
        status = self._base_status()
        status["compat"] = {
            "control_slots": {
                "active": {
                    "file": "operator_request.md",
                    "status": "needs_operator",
                    "control_seq": 2072,
                },
                "stale": [],
            }
        }

        snapshot = reduce_runtime_snapshot(status)

        self.assertTrue(snapshot["queue"]["no_queued_pipeline_task"])
        self.assertEqual(snapshot["queue"]["status"], "No queued pipeline task")
        self.assertTrue(snapshot["suppressed_operator_candidate"])
        self.assertEqual(snapshot["invariants"]["violations"], [])

    def test_suppressed_operator_compat_control_defers_to_active_round(self) -> None:
        status = self._base_status()
        status["active_round"] = {
            "state": "VERIFYING",
            "job_id": "job-verify",
        }
        status["compat"] = {
            "control_slots": {
                "active": {
                    "file": ".pipeline/operator_request.md",
                    "status": "needs_operator",
                    "control_seq": 2072,
                },
                "stale": [],
            }
        }

        snapshot = reduce_runtime_snapshot(status)

        self.assertFalse(snapshot["queue"]["no_queued_pipeline_task"])
        self.assertEqual(snapshot["queue"]["status"], "VERIFYING")
        self.assertTrue(snapshot["suppressed_operator_candidate"])
        self.assertEqual(snapshot["invariants"]["violations"], [])

    def test_operator_compat_control_still_surfaces_when_dispatch_is_not_continuing(self) -> None:
        status = self._base_status()
        status["automation_next_action"] = "operator_required"
        status["compat"] = {
            "control_slots": {
                "active": {
                    "file": "operator_request.md",
                    "status": "needs_operator",
                    "control_seq": 2072,
                },
                "stale": [],
            }
        }

        snapshot = reduce_runtime_snapshot(status)

        self.assertFalse(snapshot["queue"]["no_queued_pipeline_task"])
        self.assertEqual(snapshot["queue"]["status"], "needs_operator #2072")
        self.assertFalse(snapshot["suppressed_operator_candidate"])
        self.assertIn(
            "active_control_slot_not_surfaced",
            snapshot["invariants"]["violations"],
        )

    def test_prompt_visible_idle_turn_does_not_hide_active_verify_round(self) -> None:
        status = self._base_status()
        status["active_round"] = {
            "state": "VERIFYING",
            "job_id": "job-verify",
            "dispatch_id": "dispatch-verify",
        }
        status["turn_state"] = {
            "state": "IDLE",
            "reason": "implement_activity_detected",
        }
        status["lanes"] = [
            {
                "name": "Codex",
                "state": "READY",
                "note": "prompt_visible",
                "pid": 123,
                "attachable": True,
            }
        ]

        snapshot = reduce_runtime_snapshot(status)

        self.assertEqual(snapshot["round_state"], "VERIFYING")
        self.assertEqual(snapshot["active_lane"], "Codex")
        self.assertFalse(snapshot["queue"]["no_queued_pipeline_task"])
        self.assertEqual(snapshot["queue"]["status"], "VERIFYING")

    def test_stopped_runtime_is_inactive_even_if_compat_control_exists(self) -> None:
        status = self._base_status()
        status["runtime_state"] = "STOPPED"
        status["compat"] = {
            "control_slots": {
                "active": {
                    "file": "implement_handoff.md",
                    "status": "implement",
                    "control_seq": 2042,
                }
            }
        }

        snapshot = reduce_runtime_snapshot(status)

        self.assertFalse(snapshot["show_live"])
        self.assertFalse(snapshot["queue"]["no_queued_pipeline_task"])
        self.assertEqual(snapshot["queue"]["status"], "Runtime inactive")

    def test_lane_lifecycle_keeps_dispatch_seen_separate_from_accepted(self) -> None:
        status = self._base_status()
        status["lanes"] = [
            {"name": "Codex", "state": "WORKING", "note": "dispatch_seen seq 2042"},
            {"name": "Claude", "state": "WORKING", "note": "implement"},
            {"name": "Gemini", "state": "READY", "note": "waiting_next_control"},
        ]

        snapshot = reduce_runtime_snapshot(status)
        lifecycles = {lane["name"]: lane["lifecycle"] for lane in snapshot["lanes"]}

        self.assertEqual(lifecycles["Codex"], "dispatch_seen")
        self.assertEqual(lifecycles["Claude"], "accepted")
        self.assertEqual(lifecycles["Gemini"], "done")


if __name__ == "__main__":
    unittest.main()
