from __future__ import annotations

import unittest

from pipeline_runtime.automation_health import derive_automation_health


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
