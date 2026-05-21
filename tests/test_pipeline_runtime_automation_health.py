from __future__ import annotations

import unittest

from pipeline_runtime.automation_health import (
    AUTOMATION_HEALTH_RULESET_VERSION,
    IMPLEMENT_READY_IDLE_CYCLE_THRESHOLD,
    LOCAL_SOCKET_GUARD_AUTO_HELD_REASON,
    STALE_ADVISORY_GRACE_CYCLES,
    STALE_CONTROL_CYCLE_THRESHOLD,
    derive_automation_health,
)
from pipeline_runtime.operator_autonomy import (
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
    OPERATOR_APPROVAL_COMPLETED_REASON,
    PR_CREATION_GATE_REASON,
    PR_MERGE_GATE_REASON,
)


class AutomationHealthTest(unittest.TestCase):
    def test_advisory_disabled_attention_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "runtime_controls": {"advisory_enabled": False},
                "autonomy": {"mode": "triage", "reason_code": "slice_ambiguity"},
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "slice_ambiguity")
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_advisory_disabled_pending_operator_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "runtime_controls": {"advisory_enabled": False},
                "autonomy": {"mode": "pending_operator", "reason_code": "slice_ambiguity"},
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "slice_ambiguity")
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_advisory_disabled_degraded_fallback_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "DEGRADED",
                "runtime_controls": {"advisory_enabled": False},
                "degraded_reason": "slice_ambiguity",
                "degraded_reasons": ["slice_ambiguity"],
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "slice_ambiguity")
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_advisory_disabled_stale_control_grace_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "runtime_controls": {"advisory_enabled": False},
                "control_age_cycles": STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES,
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "stale_control_advisory")
        self.assertEqual(health["automation_next_action"], "verify_followup")
        self.assertTrue(health["stale_advisory_pending"])

    def test_slice_ambiguity_routes_to_advisory_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "autonomy": {"mode": "triage", "reason_code": "slice_ambiguity"},
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "slice_ambiguity")
        self.assertEqual(health["automation_next_action"], "advisory_followup")

    def test_advisory_disabled_advisory_followup_reasons_route_to_verify_followup(self) -> None:
        for reason in (
            "context_exhaustion",
            "session_rollover",
            "continue_vs_switch",
            "operator_retriage_no_next_control",
        ):
            with self.subTest(reason=reason):
                health = derive_automation_health(
                    {
                        "runtime_state": "RUNNING",
                        "runtime_controls": {"advisory_enabled": False},
                        "autonomy": {"mode": "triage", "reason_code": reason},
                    }
                )

                self.assertEqual(health["automation_health"], "attention")
                self.assertEqual(health["automation_reason_code"], reason)
                self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_advisory_enabled_advisory_followup_reasons_stay_advisory_followup(self) -> None:
        for reason in (
            "context_exhaustion",
            "session_rollover",
            "continue_vs_switch",
            "operator_retriage_no_next_control",
        ):
            with self.subTest(reason=reason):
                health = derive_automation_health(
                    {
                        "runtime_state": "RUNNING",
                        "autonomy": {"mode": "triage", "reason_code": reason},
                    }
                )

                self.assertEqual(health["automation_health"], "attention")
                self.assertEqual(health["automation_reason_code"], reason)
                self.assertEqual(health["automation_next_action"], "advisory_followup")


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

    def test_broken_local_socket_guard_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "BROKEN",
                "degraded_reason": LOCAL_SOCKET_GUARD_AUTO_HELD_REASON,
                "degraded_reasons": [LOCAL_SOCKET_GUARD_AUTO_HELD_REASON],
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], LOCAL_SOCKET_GUARD_AUTO_HELD_REASON)
        self.assertEqual(health["automation_incident_family"], LOCAL_SOCKET_GUARD_AUTO_HELD_REASON)
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_generic_broken_runtime_still_requires_operator(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "BROKEN",
                "degraded_reason": "runtime_launch_failed:RuntimeError",
                "degraded_reasons": ["runtime_launch_failed:RuntimeError"],
            }
        )

        self.assertEqual(health["automation_health"], "needs_operator")
        self.assertEqual(health["automation_reason_code"], "runtime_launch_failed:RuntimeError")
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

    def test_codex_verify_dispatch_failure_loop_requires_operator(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "DEGRADED",
                "degraded_reason": "codex_verify_dispatch_failure_loop",
                "degraded_reasons": ["codex_verify_dispatch_failure_loop"],
                "active_round": {
                    "state": "VERIFY_PENDING",
                    "dispatch_stage": "dispatch_failed_submit",
                    "degraded_reason": "codex_verify_dispatch_failure_loop",
                },
            }
        )

        self.assertEqual(health["automation_health"], "needs_operator")
        self.assertEqual(health["automation_reason_code"], "codex_verify_dispatch_failure_loop")
        self.assertEqual(health["automation_incident_family"], "dispatch_stall")
        self.assertEqual(health["automation_next_action"], "operator_required")

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

    def test_unknown_reason_code_returns_empty_family(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "DEGRADED",
                "degraded_reason": "totally_unknown_reason_xyz",
                "degraded_reasons": ["totally_unknown_reason_xyz"],
            }
        )

        self.assertEqual(health["automation_reason_code"], "totally_unknown_reason_xyz")
        self.assertEqual(health["automation_incident_family"], "")

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

    def test_waiting_next_control_retriage_surface_is_not_operator_wait(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "runtime_controls": {"advisory_enabled": False},
                "control": {"active_control_status": "none"},
                "autonomy": {
                    "mode": "triage",
                    "reason_code": "waiting_next_control",
                    "operator_policy": "internal_only",
                    "decision_class": "next_slice_selection",
                    "operator_eligible": False,
                },
                "turn_state": {
                    "state": "VERIFY_FOLLOWUP",
                    "reason": "operator_request_gated",
                    "active_control_file": "",
                    "active_control_seq": 1994,
                    "active_role": "verify",
                    "active_lane": "Codex",
                },
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "waiting_next_control")
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
                "control": {"active_control_status": "none"},
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

    def test_pr_merge_completed_recovery_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "autonomy": {
                    "mode": "recovery",
                    "reason_code": "pr_merge_completed",
                    "operator_policy": "internal_only",
                    "decision_class": "merge_gate",
                },
            }
        )

        self.assertEqual(health["automation_health"], "recovering")
        self.assertEqual(health["automation_reason_code"], "pr_merge_completed")
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_pr_merge_gate_without_completion_stays_pr_boundary(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "none"},
                "autonomy": {
                    "mode": "needs_operator",
                    "reason_code": PR_MERGE_GATE_REASON,
                    "operator_policy": "internal_only",
                    "decision_class": "merge_gate",
                },
            }
        )

        self.assertEqual(health["automation_health"], "needs_operator")
        self.assertEqual(health["automation_reason_code"], PR_MERGE_GATE_REASON)
        self.assertEqual(health["automation_next_action"], "pr_boundary")

    def test_pr_merge_gate_backlog_routes_to_verify_followup_attention(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "autonomy": {
                    "mode": "triage",
                    "reason_code": PR_MERGE_GATE_REASON,
                    "operator_policy": "internal_only",
                    "decision_class": "merge_gate",
                },
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], PR_MERGE_GATE_REASON)
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

    def test_duplicate_handoff_idle_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "none"},
                "turn_state": {
                    "state": "IDLE",
                    "reason": "handoff_already_completed",
                    "active_control_file": "",
                    "active_control_seq": -1,
                    "active_lane": "",
                },
                "progress": {},
                "lanes": [{"name": "Codex", "state": "READY", "note": "waiting_next_control"}],
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "duplicate_handoff")
        self.assertEqual(health["automation_incident_family"], "duplicate_handoff")
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_waiting_next_control_idle_routes_to_verify_followup(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "none"},
                "turn_state": {"state": "IDLE", "reason": "startup_turn_idle"},
                "lanes": [{"name": "Codex", "state": "READY", "note": "waiting_next_control"}],
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "waiting_next_control")
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_codex_verify_followup_no_next_control_is_not_ok_continue(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "none"},
                "turn_state": {
                    "state": "VERIFY_FOLLOWUP",
                    "reason": "verify_followup_no_next_control",
                    "active_control_file": "operator_request.md",
                    "active_control_seq": 1624,
                    "active_lane": "Codex",
                },
                "lanes": [{"name": "Codex", "state": "READY", "note": "followup"}],
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "verify_followup_no_next_control")
        self.assertEqual(health["automation_incident_family"], "operator_retriage_no_next_control")
        self.assertEqual(health["automation_next_action"], "verify_followup")

    def test_non_degraded_verify_pending_dispatch_wait_is_recovering(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "implement"},
                "active_round": {
                    "state": "VERIFY_PENDING",
                    "dispatch_stage": "task_accept_missing",
                    "degraded_reason": "",
                },
                "lanes": [{"name": "Codex", "state": "WORKING", "note": "waiting_task_accept_after_dispatch"}],
            }
        )

        self.assertEqual(health["automation_health"], "recovering")
        self.assertEqual(health["automation_reason_code"], "dispatch_stall")
        self.assertEqual(health["automation_incident_family"], "dispatch_stall")
        self.assertEqual(health["automation_next_action"], "retrying")
        source = health["automation_health_source"]
        self.assertEqual(source["ruleset_version"], AUTOMATION_HEALTH_RULESET_VERSION)
        self.assertEqual(source["derived_by"], "pipeline_runtime.automation_health.derive_automation_health")
        self.assertEqual(source["runtime_state"], "RUNNING")
        self.assertEqual(source["active_round_state"], "VERIFY_PENDING")
        self.assertEqual(source["turn_state"], "")
        self.assertEqual(source["reason_code"], "dispatch_stall")
        self.assertEqual(source["next_action"], "retrying")

    def test_idle_verify_pending_round_is_not_ok_continue(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "implement"},
                "turn_state": {"state": "IDLE", "reason": "verify_lease_released"},
                "active_round": {
                    "state": "VERIFY_PENDING",
                    "dispatch_stage": "",
                    "degraded_reason": "",
                },
            }
        )

        self.assertEqual(health["automation_health"], "recovering")
        self.assertEqual(health["automation_reason_code"], "dispatch_stall")
        self.assertEqual(health["automation_incident_family"], "dispatch_stall")
        self.assertEqual(health["automation_next_action"], "retrying")
        source = health["automation_health_source"]
        self.assertEqual(source["ruleset_version"], AUTOMATION_HEALTH_RULESET_VERSION)
        self.assertEqual(source["derived_by"], "pipeline_runtime.automation_health.derive_automation_health")
        self.assertEqual(source["runtime_state"], "RUNNING")
        self.assertEqual(source["active_round_state"], "VERIFY_PENDING")
        self.assertEqual(source["turn_state"], "IDLE")
        self.assertEqual(source["reason_code"], "dispatch_stall")
        self.assertEqual(source["next_action"], "retrying")

    def test_idle_verifying_round_is_not_ok_continue(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "implement"},
                "turn_state": {"state": "IDLE", "reason": "implement_activity_detected"},
                "active_round": {
                    "state": "VERIFYING",
                    "completion_stage": "receipt_close_pending",
                    "degraded_reason": "",
                },
            }
        )

        self.assertEqual(health["automation_health"], "recovering")
        self.assertEqual(health["automation_reason_code"], "dispatch_stall")
        self.assertEqual(health["automation_incident_family"], "dispatch_stall")
        self.assertEqual(health["automation_next_action"], "retrying")
        source = health["automation_health_source"]
        self.assertEqual(source["ruleset_version"], AUTOMATION_HEALTH_RULESET_VERSION)
        self.assertEqual(source["derived_by"], "pipeline_runtime.automation_health.derive_automation_health")
        self.assertEqual(source["runtime_state"], "RUNNING")
        self.assertEqual(source["active_round_state"], "VERIFYING")
        self.assertEqual(source["turn_state"], "IDLE")
        self.assertEqual(source["reason_code"], "dispatch_stall")
        self.assertEqual(source["next_action"], "retrying")

    def test_active_implement_lane_ready_too_long_is_not_silent_ok(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control_age_cycles": IMPLEMENT_READY_IDLE_CYCLE_THRESHOLD,
                "control": {"active_control_status": "implement"},
                "turn_state": {
                    "state": "IMPLEMENT_ACTIVE",
                    "active_lane": "Codex",
                    "active_role": "implement",
                },
                "lanes": [{"name": "Codex", "state": "READY", "note": "prompt_visible"}],
                "active_round": None,
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "implement_active_idle")
        self.assertEqual(health["automation_incident_family"], "idle_release_pending")
        self.assertEqual(health["automation_next_action"], "retrying")

    def test_active_implement_lane_closed_too_long_is_not_silent_ok(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control_age_cycles": IMPLEMENT_READY_IDLE_CYCLE_THRESHOLD,
                "control": {"active_control_status": "implement"},
                "turn_state": {
                    "state": "IMPLEMENT_ACTIVE",
                    "active_lane": "Codex",
                },
                "lanes": [{"name": "Codex", "state": "READY", "note": "closed"}],
            }
        )

        self.assertEqual(health["automation_health"], "attention")
        self.assertEqual(health["automation_reason_code"], "implement_active_idle")
        self.assertEqual(health["automation_next_action"], "retrying")

    def test_implement_idle_timeout_with_active_handoff_is_recovering(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "implement"},
                "turn_state": {
                    "state": "IDLE",
                    "reason": "implement_idle_timeout",
                },
                "lanes": [{"name": "Codex", "state": "READY", "note": "prompt_visible"}],
            }
        )

        self.assertEqual(health["automation_health"], "recovering")
        self.assertEqual(health["automation_reason_code"], "idle_release_pending")
        self.assertEqual(health["automation_incident_family"], "idle_release_pending")
        self.assertEqual(health["automation_next_action"], "retrying")

    def test_current_work_verify_round_is_not_misread_as_idle_release(self) -> None:
        health = derive_automation_health(
            {
                "runtime_state": "RUNNING",
                "control": {"active_control_status": "implement"},
                "turn_state": {
                    "state": "IDLE",
                    "reason": "implement_idle_timeout",
                },
                "active_round": {
                    "state": "VERIFY_PENDING",
                    "artifact_path": "/repo/work/4/29/2026-04-29-current.md",
                },
                "artifacts": {
                    "latest_work": {"path": "4/29/2026-04-29-current.md"},
                },
                "lanes": [{"name": "Claude", "state": "READY", "note": "verify_pending"}],
            }
        )

        self.assertEqual(health["automation_health"], "recovering")
        self.assertEqual(health["automation_reason_code"], "dispatch_stall")
        self.assertEqual(health["automation_next_action"], "retrying")


if __name__ == "__main__":
    unittest.main()
