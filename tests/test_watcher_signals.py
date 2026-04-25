import unittest

import watcher_signals


class LiveSessionEscalationSignalTest(unittest.TestCase):
    def test_extract_live_session_escalation_detects_expected_reasons(self) -> None:
        text = """
이 세션에서 이미 28건의 동일 family smoke를 수행했고 context window가 매우 소진된 상태입니다.
새 세션에서 이어가시는 것을 강하게 권고드립니다.
그래도 진행을 원하시면 handoff를 확인하겠지만, 진행할까요?
"""
        signal = watcher_signals._extract_live_session_escalation(text)

        self.assertIsNotNone(signal)
        self.assertEqual(
            signal["reasons"],
            ["context_exhaustion", "session_rollover", "continue_vs_switch"],
        )
        self.assertTrue(signal["fingerprint"])

    def test_extract_live_session_escalation_detects_additional_phrase_variants(self) -> None:
        text = """
The context exhausted warning says the window is nearly full.
Please start a new session for the next slice.
Should I continue here or handoff and continue in a fresh session?
"""
        signal = watcher_signals._extract_live_session_escalation(text)

        self.assertIsNotNone(signal)
        self.assertEqual(
            signal["reasons"],
            ["context_exhaustion", "session_rollover", "continue_vs_switch"],
        )

    def test_extract_live_session_escalation_ignores_old_scrollback_matches(self) -> None:
        old_lines = [
            "context window is nearly full",
            "please start a new session",
            "should i continue here?",
        ]
        recent_lines = [f"recent output line {i}" for i in range(20)]
        text = "\n".join(old_lines + recent_lines)

        signal = watcher_signals._extract_live_session_escalation(text)

        self.assertIsNone(signal)

    def test_extract_live_session_escalation_detects_semantic_fallback_combo(self) -> None:
        text = """
최근 답변이 너무 길어져서 이 대화는 거의 가득 찬 것 같습니다.
다음 세션에서 이어가는 편이 안전하겠습니다.
여기서 계속 진행할지, handoff로 넘길지 정할까요?
"""

        signal = watcher_signals._extract_live_session_escalation(text)

        self.assertIsNotNone(signal)
        self.assertEqual(
            signal["reasons"],
            ["context_exhaustion", "session_rollover", "continue_vs_switch"],
        )


class ImplementBlockedSignalTest(unittest.TestCase):
    def test_extract_implement_blocked_accepts_bulleted_status_line(self) -> None:
        signal = watcher_signals._extract_implement_blocked_signal(
            "\n".join(
                [
                    "• STATUS: implement_blocked",
                    "  BLOCK_REASON: conflict_count_owner_out_of_scope",
                    "  BLOCK_REASON_CODE: scope_missing_owner",
                    "  REQUEST: verify_triage",
                    "  ESCALATION_CLASS: verify_triage",
                    "  HANDOFF: .pipeline/implement_handoff.md",
                    "  HANDOFF_SHA: abcdef1234567890",
                    "  BLOCK_ID: block-bullet-001",
                    "› Summarize recent commits",
                ]
            ),
            active_handoff_path=".pipeline/implement_handoff.md",
            active_handoff_sha="abcdef1234567890",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason"], "conflict_count_owner_out_of_scope")
        self.assertEqual(signal["reason_code"], "scope_missing_owner")
        self.assertEqual(signal["fingerprint"], "block-bullet-001")

    def test_extract_implement_blocked_tolerates_wrapped_handoff_fields(self) -> None:
        signal = watcher_signals._extract_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: smoke_handoff_blocked",
                    "REQUEST: verify_triage",
                    "HANDOFF: .pipeline/live-blocked-smoke-j3",
                    "YWbK/implement_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "fedcba0987654321",
                    "BLOCK_ID: abcdef1234567890fedc",
                    "ba0987654321:smoke_handoff_blocked",
                    ">",
                ]
            ),
            active_handoff_path=".pipeline/live-blocked-smoke-j3YWbK/implement_handoff.md",
            active_handoff_sha="abcdef1234567890fedcba0987654321",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason"], "smoke_handoff_blocked")
        self.assertEqual(signal["fingerprint"], "abcdef1234567890fedcba0987654321:smoke_handoff_blocked")

    def test_extract_implement_blocked_tolerates_wrapped_status_and_reason(self) -> None:
        signal = watcher_signals._extract_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS:",
                    "implement_blocked",
                    "BLOCK_REASON:",
                    "renderResult follow-up",
                    "correctly drops review-outcome",
                    "REQUEST: verify_triage",
                    "HANDOFF: .pipeline/implement_",
                    "handoff.md",
                    "HANDOFF_SHA:",
                    "abcdef1234567890",
                    "fedcba0987654321",
                    "BLOCK_ID:",
                    "abcdef1234567890",
                    "fedcba0987654321:renderResult-follow-up",
                    "분석 결과:",
                    ">",
                ]
            ),
            active_handoff_path=".pipeline/implement_handoff.md",
            active_handoff_sha="abcdef1234567890fedcba0987654321",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason"], "renderresult follow-up correctly drops review-outcome")
        self.assertEqual(signal["fingerprint"], "abcdef1234567890fedcba0987654321:renderResult-follow-up")

    def test_extract_implement_blocked_prefers_structured_reason_code_and_escalation_class(self) -> None:
        signal = watcher_signals._extract_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: context window exhausted after diff review",
                    "BLOCK_REASON_CODE: context_exhaustion",
                    "REQUEST: verify_triage",
                    "ESCALATION_CLASS: verify_triage",
                    "HANDOFF: .pipeline/implement_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "BLOCK_ID: block-structured-001",
                ]
            ),
            active_handoff_path=".pipeline/implement_handoff.md",
            active_handoff_sha="abcdef1234567890",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason_code"], "context_exhaustion")
        self.assertEqual(signal["escalation_class"], "verify_triage")
        self.assertEqual(signal["request"], "verify_triage")

    def test_extract_implement_blocked_normalizes_legacy_codex_triage_alias(self) -> None:
        signal = watcher_signals._extract_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: legacy alias",
                    "BLOCK_REASON_CODE: codex_triage_only",
                    "REQUEST: codex_triage",
                    "ESCALATION_CLASS: codex_triage",
                    "HANDOFF: .pipeline/implement_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "BLOCK_ID: block-legacy-001",
                ]
            ),
            active_handoff_path=".pipeline/implement_handoff.md",
            active_handoff_sha="abcdef1234567890",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason_code"], "verify_triage_only")
        self.assertEqual(signal["escalation_class"], "verify_triage")
        self.assertEqual(signal["request"], "verify_triage")

    def test_extract_implement_blocked_ignores_prompt_template_example(self) -> None:
        signal = watcher_signals._extract_implement_blocked_signal(
            "\n".join(
                [
                    "- if the handoff is blocked or not actionable, emit the exact sentinel below and stop",
                    "BLOCKED_SENTINEL:",
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: <short_reason>",
                    "REQUEST: verify_triage",
                    "HANDOFF: .pipeline/implement_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "BLOCK_ID: abcdef1234567890:<short_reason>",
                    ">",
                ]
            ),
            active_handoff_path=".pipeline/implement_handoff.md",
            active_handoff_sha="abcdef1234567890",
        )

        self.assertIsNone(signal)


if __name__ == "__main__":
    unittest.main()
