from __future__ import annotations

import unittest

from pipeline_runtime.role_routes import (
    ADVISORY_ADVICE_FOLLOWUP_NOTIFY,
    ADVISORY_RECOVERY_NOTIFY,
    ADVISORY_REQUEST_NOTIFY,
    IMPLEMENT_HANDOFF_NOTIFY,
    VERIFY_FOLLOWUP_ROUTE,
    VERIFY_FOLLOWUP_ROUTE_ALIASES,
    VERIFY_TRIAGE_ESCALATION,
    VERIFY_TRIAGE_ONLY_REASON,
    normalize_followup_route,
    normalize_notify_kind,
    normalize_verify_triage_escalation,
    normalize_verify_triage_reason,
)
from pipeline_runtime.turn_arbitration import (
    TURN_IDLE,
    TURN_IMPLEMENT,
    TURN_OPERATOR,
    TURN_VERIFY,
    TURN_VERIFY_FOLLOWUP,
    WatcherTurnInputs,
    active_lane_for_runtime,
    build_active_round_snapshot,
    legacy_watcher_turn_name,
    resolve_watcher_turn,
    should_suppress_active_round_after_verified_latest_work,
    suppress_active_round_for_turn,
    verify_round_task_hint,
)


class RoleRouteCompatibilityTest(unittest.TestCase):
    def test_legacy_notify_kinds_normalize_to_role_names(self) -> None:
        self.assertEqual(normalize_notify_kind("claude_handoff"), IMPLEMENT_HANDOFF_NOTIFY)
        self.assertEqual(normalize_notify_kind("gemini_request"), ADVISORY_REQUEST_NOTIFY)
        self.assertEqual(normalize_notify_kind("gemini_advice_followup"), ADVISORY_ADVICE_FOLLOWUP_NOTIFY)
        self.assertEqual(normalize_notify_kind("gemini_advisory_recovery"), ADVISORY_RECOVERY_NOTIFY)

    def test_legacy_verify_routes_normalize_to_role_names(self) -> None:
        self.assertEqual(normalize_followup_route("codex_followup"), VERIFY_FOLLOWUP_ROUTE)
        self.assertEqual(normalize_verify_triage_escalation("codex_triage"), VERIFY_TRIAGE_ESCALATION)
        self.assertEqual(normalize_verify_triage_reason("codex_triage_only"), VERIFY_TRIAGE_ONLY_REASON)

    def test_watcher_turn_name_uses_all_verify_followup_route_aliases(self) -> None:
        for alias in sorted(VERIFY_FOLLOWUP_ROUTE_ALIASES):
            with self.subTest(alias=alias):
                self.assertEqual(legacy_watcher_turn_name(alias), VERIFY_FOLLOWUP_ROUTE)

    def test_watcher_turn_name_keeps_canonical_to_legacy_labels(self) -> None:
        self.assertEqual(legacy_watcher_turn_name(TURN_IMPLEMENT), "claude")
        self.assertEqual(legacy_watcher_turn_name(TURN_VERIFY), "codex")
        self.assertEqual(legacy_watcher_turn_name(TURN_VERIFY_FOLLOWUP), VERIFY_FOLLOWUP_ROUTE)


class WatcherTurnArbitrationTest(unittest.TestCase):
    def test_operator_request_wins_without_recovery_or_gate(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=True,
                advisory_request_active=False,
                advisory_advice_active=False,
                implement_handoff_active=True,
                latest_work_needs_verify=False,
                implement_handoff_verify_active=False,
                idle_release_cooldown_active=False,
            )
        )
        self.assertEqual(turn, TURN_OPERATOR)

    def test_handoff_with_verify_need_prefers_verify(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=False,
                advisory_request_active=False,
                advisory_advice_active=False,
                implement_handoff_active=True,
                latest_work_needs_verify=True,
                implement_handoff_verify_active=False,
                idle_release_cooldown_active=False,
            )
        )
        self.assertEqual(turn, TURN_VERIFY)

    def test_operator_gate_routes_to_followup_until_hibernate(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=False,
                advisory_request_active=False,
                advisory_advice_active=False,
                implement_handoff_active=False,
                latest_work_needs_verify=False,
                implement_handoff_verify_active=False,
                idle_release_cooldown_active=False,
                operator_gate_marker={"routed_to": "verify_followup"},
            )
        )
        self.assertEqual(turn, TURN_VERIFY_FOLLOWUP)

    def test_operator_recovery_marker_falls_back_to_followup_after_active_work(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=True,
                advisory_request_active=False,
                advisory_advice_active=False,
                implement_handoff_active=False,
                latest_work_needs_verify=False,
                implement_handoff_verify_active=False,
                idle_release_cooldown_active=False,
                operator_recovery_marker={"reason": "operator_retriage_no_next_control"},
            )
        )
        self.assertEqual(turn, TURN_VERIFY_FOLLOWUP)

    def test_verify_need_still_wins_over_operator_recovery_marker(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=True,
                advisory_request_active=False,
                advisory_advice_active=False,
                implement_handoff_active=False,
                latest_work_needs_verify=True,
                implement_handoff_verify_active=False,
                idle_release_cooldown_active=False,
                operator_recovery_marker={"reason": "operator_retriage_no_next_control"},
            )
        )
        self.assertEqual(turn, TURN_VERIFY)

    def test_operator_gate_followup_marker_is_reachable_without_active_work(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=True,
                advisory_request_active=False,
                advisory_advice_active=False,
                implement_handoff_active=False,
                latest_work_needs_verify=False,
                implement_handoff_verify_active=False,
                idle_release_cooldown_active=False,
                operator_gate_marker={"routed_to": "codex_followup"},
            )
        )
        self.assertEqual(turn, TURN_VERIFY_FOLLOWUP)

    def test_operator_gate_hibernate_suppresses_stale_verify_need(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=True,
                advisory_request_active=False,
                advisory_advice_active=False,
                implement_handoff_active=True,
                latest_work_needs_verify=True,
                implement_handoff_verify_active=False,
                idle_release_cooldown_active=False,
                operator_gate_marker={"routed_to": "hibernate"},
            )
        )
        self.assertEqual(turn, TURN_IDLE)

    def test_handoff_without_verify_need_returns_implement(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=False,
                advisory_request_active=False,
                advisory_advice_active=False,
                implement_handoff_active=True,
                latest_work_needs_verify=False,
                implement_handoff_verify_active=False,
                idle_release_cooldown_active=False,
            )
        )
        self.assertEqual(turn, TURN_IMPLEMENT)


class RuntimeTurnArbitrationTest(unittest.TestCase):
    def test_receipt_pending_does_not_claim_codex_lane_when_turn_is_idle(self) -> None:
        active_lane = active_lane_for_runtime(
            {"state": "IDLE"},
            {
                "state": "RECEIPT_PENDING",
                "completion_stage": "receipt_close_pending",
            },
            implement_owner="Claude",
            verify_owner="Codex",
            advisory_owner="Gemini",
        )
        self.assertEqual(active_lane, "")

    def test_receipt_pending_keeps_codex_lane_when_followup_turn_is_active(self) -> None:
        active_lane = active_lane_for_runtime(
            {"state": "CODEX_FOLLOWUP"},
            {
                "state": "RECEIPT_PENDING",
                "completion_stage": "receipt_close_pending",
            },
            implement_owner="Claude",
            verify_owner="Codex",
            advisory_owner="Gemini",
        )
        self.assertEqual(active_lane, "Codex")

    def test_followup_turn_suppresses_stale_verify_active_round(self) -> None:
        self.assertTrue(
            suppress_active_round_for_turn(
                turn_state={"state": "CODEX_FOLLOWUP"},
                active_round={"state": "VERIFYING"},
            )
        )

    def test_implement_turn_suppresses_stale_verify_active_round(self) -> None:
        self.assertTrue(
            suppress_active_round_for_turn(
                turn_state={"state": "IMPLEMENT_ACTIVE"},
                active_round={"state": "VERIFY_PENDING"},
            )
        )

    def test_active_round_selection_uses_dispatch_control_seq_without_status_control(self) -> None:
        active_round = build_active_round_snapshot(
            [
                {
                    "job_id": "job-newer",
                    "status": "VERIFY_RUNNING",
                    "round": 1,
                    "dispatch_control_seq": 10,
                    "updated_at": 200.0,
                },
                {
                    "job_id": "job-matching-dispatch",
                    "status": "VERIFY_RUNNING",
                    "round": 2,
                    "dispatch_control_seq": 42,
                    "dispatch_id": "dispatch-42",
                    "updated_at": 100.0,
                },
            ],
            last_receipt=None,
            active_control={
                "active_control_status": "none",
                "active_control_seq": -1,
            },
        )

        self.assertIsNotNone(active_round)
        self.assertEqual(active_round["job_id"], "job-newer")
        self.assertEqual(active_round["dispatch_control_seq"], 10)

    def test_verify_task_hint_can_be_active_without_status_control(self) -> None:
        hint = verify_round_task_hint(
            active_lane="Codex",
            verify_owner="Codex",
            turn_state={"state": "VERIFY_ACTIVE"},
            active_round={
                "state": "VERIFY_PENDING",
                "job_id": "job-verify",
                "dispatch_id": "dispatch-verify",
                "dispatch_control_seq": 2037,
            },
        )

        self.assertTrue(hint.active)
        self.assertEqual(hint.job_id, "job-verify")
        self.assertEqual(hint.dispatch_id, "dispatch-verify")
        self.assertEqual(hint.control_seq, 2037)

    def test_verify_task_hint_drops_stale_round_after_followup_turn(self) -> None:
        hint = verify_round_task_hint(
            active_lane="Codex",
            verify_owner="Codex",
            turn_state={"state": "VERIFY_FOLLOWUP"},
            active_round={
                "state": "VERIFY_PENDING",
                "job_id": "job-stale",
                "dispatch_id": "dispatch-stale",
                "dispatch_control_seq": 2038,
            },
        )

        self.assertFalse(hint.active)
        self.assertEqual(hint.job_id, "")
        self.assertEqual(hint.dispatch_id, "")
        self.assertEqual(hint.control_seq, -1)

    def test_verified_latest_work_suppresses_stale_active_round(self) -> None:
        self.assertTrue(
            should_suppress_active_round_after_verified_latest_work(
                turn_state={"state": "IDLE", "reason": "handoff_already_completed"},
                active_round={
                    "state": "VERIFYING",
                    "artifact_path": "work/5/22/old.md",
                },
                control={"active_control_status": "none"},
                artifacts={
                    "latest_work": {"path": "work/5/23/new.md"},
                    "latest_verify": {"path": "verify/5/23/new.md"},
                },
            )
        )


if __name__ == "__main__":
    unittest.main()
