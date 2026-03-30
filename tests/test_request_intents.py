from __future__ import annotations

import unittest

from core.request_intents import (
    classify_search_intent,
    extract_explicit_web_search_query,
    extract_external_fact_query,
    extract_implicit_web_search_query,
    is_explicit_web_search_request,
    looks_like_external_fact_info_request,
    looks_like_live_or_latest_info_request,
)


class RequestIntentTest(unittest.TestCase):
    def test_colloquial_web_search_phrases_are_detected(self) -> None:
        expectations = {
            "아이유좀검색": "아이유",
            "아이유 찾아와": "아이유",
            "아이유 관련해서 좀 볼래": "아이유",
            "서울 날씨 검색해요": "서울 날씨",
        }

        for phrase, expected_query in expectations.items():
            with self.subTest(phrase=phrase):
                self.assertTrue(is_explicit_web_search_request(phrase))
                self.assertEqual(extract_explicit_web_search_query(phrase), expected_query)

    def test_local_document_hints_block_web_search_detection(self) -> None:
        phrase = "이 문서에서 아이유 찾아줘"
        self.assertFalse(is_explicit_web_search_request(phrase))
        self.assertIsNone(extract_explicit_web_search_query(phrase))

    def test_live_or_latest_info_queries_can_be_auto_searched(self) -> None:
        expectations = {
            "오늘 날씨 어때요?": "오늘 날씨",
            "서울 환율 알려줘": "서울 환율",
            "아이유 최신 소식 알려줘": "아이유 최신 소식",
        }

        for phrase, expected_query in expectations.items():
            with self.subTest(phrase=phrase):
                self.assertTrue(looks_like_live_or_latest_info_request(phrase))
                self.assertEqual(extract_implicit_web_search_query(phrase), expected_query)

    def test_external_fact_info_queries_can_be_auto_searched(self) -> None:
        expectations = {
            "메이플스토리에 대해 알려줘": "메이플스토리",
            "BTS 설명해줘": "BTS",
            "아이유 소개해줘": "아이유",
            "김창섭이 누구야?": "김창섭",
            "김창섭이 누구야 ?": "김창섭",
            "김창섭 좀 알려줘": "김창섭",
            "김창섭 아냐?": "김창섭",
            "김창섭 어떤 사람이야?": "김창섭",
            "김창섭 어떤 분이야?": "김창섭",
            "김창섭 얘기 좀 해줘": "김창섭",
            "김창섭 얘기해봐": "김창섭",
            "김창섭 관련 정보 있나?": "김창섭",
            "김창섭 관련된 거 좀 알려줘": "김창섭",
            "김창섭 쪽은 어때?": "김창섭",
            "김창섭 쪽으로 좀 봐줘": "김창섭",
            "김창섭 뭐하는 사람이야?": "김창섭",
            "김창섭 누군지 궁금해": "김창섭",
            "김창섭 어떤 사람인지 궁금해": "김창섭",
            "김창섭 대충 알려줘": "김창섭",
            "김창섭이 누군지 알려줘": "김창섭",
            "김창섭이 누군지 궁금한데": "김창섭",
            "메이플스토리가 뭐야?": "메이플스토리",
            "메이플스토리가 뭐야 ?": "메이플스토리",
            "붉은사막이 무슨게임이야?": "붉은사막",
            "붉은사막이 무슨 게임이야?": "붉은사막",
            "붉은사막이 어떤게임이야?": "붉은사막",
            "메이플스토리 뭐하는 게임이야?": "메이플스토리",
            "메이플스토리가 뭐하는 게임인지 알려줘": "메이플스토리",
            "메이플 뭐임?": "메이플",
            "naver라는 사이트 알아?": "naver",
            "네이버가 뭔지 알려줘": "네이버",
            "네이버 뭐하는 곳이야?": "네이버",
        }

        for phrase, expected_query in expectations.items():
            with self.subTest(phrase=phrase):
                self.assertTrue(looks_like_external_fact_info_request(phrase))
                self.assertEqual(extract_external_fact_query(phrase), expected_query)

    def test_classify_search_intent_returns_kind_and_reasons(self) -> None:
        decision = classify_search_intent("김창섭이 누군지 궁금한데")

        self.assertEqual(decision.kind, "external_fact")
        self.assertEqual(decision.query, "김창섭")
        self.assertGreaterEqual(decision.score, 4)
        self.assertIn("identity_curiosity", decision.reasons)
        self.assertEqual(decision.answer_mode, "entity_card")
        self.assertEqual(decision.freshness_risk, "low")

    def test_classify_search_intent_can_return_low_confidence_suggestion(self) -> None:
        decision = classify_search_intent("김창섭 궁금한데")

        self.assertEqual(decision.kind, "none")
        self.assertEqual(decision.suggestion_kind, "external_fact")
        self.assertEqual(decision.suggestion_query, "김창섭")
        self.assertGreaterEqual(decision.suggestion_score, 3)
        self.assertIn("soft_curiosity", decision.suggestion_reasons)
        self.assertEqual(decision.suggestion_answer_mode, "entity_card")
        self.assertEqual(decision.suggestion_freshness_risk, "low")

    def test_classify_search_intent_ignores_feedback_retry_suffix(self) -> None:
        decision = classify_search_intent(
            "붉은사막이 무슨게임이야?\n\n"
            "방금 답변은 틀림 이유는 '사실과 다름'입니다. 같은 세션 문맥과 근거를 기준으로 더 정확하고 "
            "관련성 높게 다시 답변해 주세요."
        )

        self.assertEqual(decision.kind, "external_fact")
        self.assertEqual(decision.query, "붉은사막")

    def test_live_latest_queries_are_marked_as_latest_update(self) -> None:
        decision = classify_search_intent("오늘 날씨 어때요?")

        self.assertEqual(decision.kind, "live_latest")
        self.assertEqual(decision.answer_mode, "latest_update")
        self.assertEqual(decision.freshness_risk, "high")

    def test_explicit_latest_search_queries_are_marked_as_latest_update(self) -> None:
        decision = classify_search_intent("아이유 최신 소식 검색해봐")

        self.assertEqual(decision.kind, "explicit_web")
        self.assertEqual(decision.answer_mode, "latest_update")
        self.assertEqual(decision.freshness_risk, "high")


if __name__ == "__main__":
    unittest.main()
