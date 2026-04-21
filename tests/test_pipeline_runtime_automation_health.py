from __future__ import annotations

import unittest

from pipeline_runtime.automation_health import (
    STALE_ADVISORY_GRACE_CYCLES,
    STALE_CONTROL_CYCLE_THRESHOLD,
    derive_automation_health,
)
from pipeline_runtime.operator_autonomy import (
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
    OPERATOR_APPROVAL_COMPLETED_REASON,
    PR_CREATION_GATE_REASON,
)


class PipelineRuntimeAutomationHealthTest(unittest.TestCase):
    def test_running_without_incident_is_ok(self) -> None:
        health = derive_automation_health({"runtime_state": "RUNNING"})

        self.assertEqual(health["automation_health"], "ok")
        self.assertEqual(health["automation_reason_code"], "")
        self.assertEqual(health["automation_next_action"], "continue")

    def test_stopped_runtime_is_not_silent_ok(self) -> None:
        health = derive_automation_health({"runtime_state": "STOPPED"})

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "runtime_stopped")
        self.assertEqual(health["automation_incident_family"], "runtime_stopped")
        self.assertEqual(health["automation_next_action"], "operator_required")

    def test_dispatch_stall_maps_to_verify_attention(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "DEGRADED",
                "degraded_reason": "dispatch_stall",
                "degraded_reasons": ["dispatch_stall"],
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "dispatch_stall")
        self.assertEqual(health["automation_incident_family"], "dispatch_stall")
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_completion_stall_maps_to_canonical_family(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "DEGRADED",
                "degraded_reason": "post_accept_completion_stall",
                "degraded_reasons": ["post_accept_completion_stall"],
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_incident_family"], "completion_stall")
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_operator_approval_completed_recovery_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "autonomy": {"mode": "recovery", "reason_code": OPERATOR_APPROVAL_COMPLETED_REASON},
            }
        )

        self.assertEqual(health["automation_health"], "recovering")
        self.assertEqual(health["automation_reason_code"], OPERATOR_APPROVAL_COMPLETED_REASON)
        self.assertEqual(health["automation_incident_family"], OPERATOR_APPROVAL_COMPLETED_REASON)
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_commit_push_bundle_authorization_triage_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "autonomy": {
                    "mode": "triage",
                    "reason_code": COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
                },
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(
            health["automation_reason_code"],
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_control_age_below_threshold_is_not_stale(self) -> None:
        age = STALE_CONTROL_CYCLE_THRESHOLD - 1
        health = derive_automation_health({"runtime_state": "RUNNING", "control_age_cycles": age})

        self.assertEqual(health["control_age_cycles"], age)
        self.assertEqual(health["stale_control_cycle_threshold"], STALE_CONTROL_CYCLE_THRESHOLD)
        self.assertFalse(health["stale_control_seq"])
        self.assertNotIn("제어 슬롯 고착 감지됨", str(health["automation_health_detail"]))

    def test_control_age_at_threshold_is_stale(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control_age_cycles": STALE_CONTROL_CYCLE_THRESHOLD,
            }
        )

        self.assertEqual(health["control_age_cycles"], STALE_CONTROL_CYCLE_THRESHOLD)
        self.assertTrue(health["stale_control_seq"])
        self.assertFalse(health["stale_advisory_pending"])

    def test_control_age_after_advisory_grace_is_advisory_pending(self) -> None:
        age = STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES
        health = derive_automation_health({"runtime_state": "RUNNING", "control_age_cycles": age})

        self.assertEqual(health["control_age_cycles"], age)
        self.assertEqual(health["stale_advisory_grace_cycles"], STALE_ADVISORY_GRACE_CYCLES)
        self.assertTrue(health["stale_control_seq"])
        self.assertTrue(health["stale_advisory_pending"])
        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "stale_control_advisory")
        self.assertEqual(health["automation_next_action"], "advisory_followup")

    def test_stale_control_seq_label_appears_in_health_detail(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control_age_cycles": STALE_CONTROL_CYCLE_THRESHOLD,
            }
        )

        self.assertIn("제어 슬롯 고착 감지됨", str(health["automation_health_detail"]))
        self.assertIn(f"{STALE_CONTROL_CYCLE_THRESHOLD} 사이클", str(health["automation_health_detail"]))

    def test_non_stale_control_seq_label_absent_from_health_detail(self) -> None:
        health = derive_automation_health({"runtime_state": "RUNNING", "control_age_cycles": 0})

        self.assertFalse(health["stale_control_seq"])
        self.assertEqual(health["automation_health_detail"], "")

    def test_menu_or_session_ambiguity_routes_to_advisory_followup(self) -> None:
        for reason in ("slice_ambiguity", "context_exhaustion", "session_rollover"):
            health = derive_automation_health(
                {
                    "runtime_state": "RUNNING",
                    "autonomy": {"mode": "triage", "reason_code": reason},
                }
            )

            self.assertEqual(health["automation_health"], "attention")
            self.assertEqual(health["automation_reason_code"], reason)
            self.assertEqual(health["automation_next_action"], "advisory_followup")

    def test_real_risk_operator_stop_stays_needs_operator(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "needs_operator"},
                "autonomy": {"mode": "needs_operator", "reason_code": "approval_required"},
            }
        )

        self.assertEqual(health["automation_health"], "needs_operator")
        self.assertEqual(health["automation_reason_code"], "approval_required")
        self.assertEqual(health["automation_next_action"], "operator_required")

    def test_hibernating_publication_boundary_is_not_silent_ok(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "autonomy": {
                    "mode": "hibernate",
                    "reason_code": "external_publication_boundary",
                    "operator_policy": "gate_24h",
                    "decision_class": "release_gate",
                },
                "turn_state": {
                    "state": "OPERATOR_WAIT",
                    "active_control_file": "operator_request.md",
                    "active_control_seq": 722,
                },
            }
        )

        self.assertEqual(health["automation_health"], "needs_operator")
        self.assertEqual(health["automation_reason_code"], "external_publication_boundary")
        self.assertEqual(health["automation_incident_family"], "external_publication_boundary")
        self.assertEqual(health["automation_next_action"], "pr_boundary")

    def test_pr_creation_gate_maps_to_verify_followup_attention(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "autonomy": {
                    "mode": "triage",
                    "reason_code": PR_CREATION_GATE_REASON,
                },
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], PR_CREATION_GATE_REASON)
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_recovery_exhaustion_requires_operator(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "DEGRADED",
                "degraded_reason": "session_missing",
                "degraded_reasons": ["session_missing", "claude_recovery_failed"],
            }
        )

        self.assertEqual(health["automation_health"], "needs_operator")
        self.assertEqual(health["automation_reason_code"], "claude_recovery_failed")
        self.assertEqual(health["automation_incident_family"], "lane_recovery_exhausted")
        self.assertEqual(health["automation_next_action"], "operator_required")

    def test_session_recovery_exhaustion_requires_operator(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "DEGRADED",
                "degraded_reason": "session_missing",
                "degraded_reasons": ["session_missing", "session_recovery_exhausted"],
            }
        )

        self.assertEqual(health["automation_health"], "needs_operator")
        self.assertEqual(health["automation_reason_code"], "session_recovery_exhausted")
        self.assertEqual(health["automation_incident_family"], "session_recovery_exhausted")
        self.assertEqual(health["automation_next_action"], "operator_required")

    def test_lane_prefixed_auth_failure_requires_operator(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "DEGRADED",
                "degraded_reason": "claude_auth_login_required",
                "degraded_reasons": ["claude_auth_login_required"],
            }
        )

        self.assertEqual(health["automation_health"], "needs_operator")
        self.assertEqual(health["automation_reason_code"], "claude_auth_login_required")
        self.assertEqual(health["automation_next_action"], "operator_required")

    def test_lane_signal_mismatch_is_attention(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "lanes": [{"name": "Codex", "state": "READY", "note": "signal_mismatch"}],
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "signal_mismatch")
        self.assertEqual(health["automation_next_action"], "verify_followup")


if __name__ == "__main__":
    unittest.main()
