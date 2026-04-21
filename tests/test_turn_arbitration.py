from __future__ import annotations

import unittest

from pipeline_runtime.turn_arbitration import (
    TURN_CLAUDE,
    TURN_CODEX_FOLLOWUP,
    TURN_CODEX_VERIFY,
    TURN_OPERATOR,
    WatcherTurnInputs,
    active_lane_for_runtime,
    resolve_watcher_turn,
    suppress_active_round_for_turn,
)


class WatcherTurnArbitrationTest(unittest.TestCase):
    def test_operator_request_wins_without_recovery_or_gate(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=True,
                gemini_request_active=False,
                gemini_advice_active=False,
                claude_handoff_active=True,
                latest_work_needs_verify=False,
                claude_handoff_verify_active=False,
                idle_release_cooldown_active=False,
            )
        )
        self.assertEqual(turn, TURN_OPERATOR)

    def test_handoff_with_verify_need_prefers_codex_verify(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=False,
                gemini_request_active=False,
                gemini_advice_active=False,
                claude_handoff_active=True,
                latest_work_needs_verify=True,
                claude_handoff_verify_active=False,
                idle_release_cooldown_active=False,
            )
        )
        self.assertEqual(turn, TURN_CODEX_VERIFY)

    def test_operator_gate_routes_to_followup_until_hibernate(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=False,
                gemini_request_active=False,
                gemini_advice_active=False,
                claude_handoff_active=False,
                latest_work_needs_verify=False,
                claude_handoff_verify_active=False,
                idle_release_cooldown_active=False,
                operator_gate_marker={"routed_to": "codex_followup"},
            )
        )
        self.assertEqual(turn, TURN_CODEX_FOLLOWUP)

    def test_handoff_without_verify_need_returns_claude(self) -> None:
        turn = resolve_watcher_turn(
            WatcherTurnInputs(
                operator_request_active=False,
                gemini_request_active=False,
                gemini_advice_active=False,
                claude_handoff_active=True,
                latest_work_needs_verify=False,
                claude_handoff_verify_active=False,
                idle_release_cooldown_active=False,
            )
        )
        self.assertEqual(turn, TURN_CLAUDE)


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
