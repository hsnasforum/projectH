from __future__ import annotations

import unittest

from pipeline_runtime.role_routes import (
    ADVISORY_ADVICE_FOLLOWUP_NOTIFY,
    ADVISORY_RECOVERY_NOTIFY,
    ADVISORY_REQUEST_NOTIFY,
    IMPLEMENT_HANDOFF_NOTIFY,
    VERIFY_FOLLOWUP_ROUTE,
    VERIFY_TRIAGE_ESCALATION,
    VERIFY_TRIAGE_ONLY_REASON,
    normalize_followup_route,
    normalize_notify_kind,
    normalize_verify_triage_escalation,
    normalize_verify_triage_reason,
)
from pipeline_runtime.turn_arbitration import (
    TURN_IMPLEMENT,
    TURN_OPERATOR,
    TURN_VERIFY,
    TURN_VERIFY_FOLLOWUP,
    WatcherTurnInputs,
    active_lane_for_runtime,
    resolve_watcher_turn,
    suppress_active_round_for_turn,
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


if __name__ == "__main__":
    unittest.main()
