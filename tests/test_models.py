"""Tests for core.models state dataclasses."""

from __future__ import annotations

import unittest

from core.contracts import AnswerMode, FreshnessRisk, SearchIntentKind
from core.models import RequestContext, SearchIntentResolution
from core.request_intents import SearchIntentDecision


class RequestContextTest(unittest.TestCase):

    def test_construction_with_defaults(self) -> None:
        rc = RequestContext(user_text="hello", session_id="s1")
        self.assertEqual(rc.user_text, "hello")
        self.assertEqual(rc.session_id, "s1")
        self.assertIsNone(rc.search_query)
        self.assertFalse(rc.has_search_request)
        self.assertEqual(rc.web_search_permission, "disabled")
        self.assertEqual(rc.follow_up_intent, "general")
        self.assertEqual(rc.active_context_mode, "none")

    def test_construction_with_all_fields(self) -> None:
        rc = RequestContext(
            user_text="search test",
            session_id="s2",
            search_query="query",
            search_root="/tmp",
            has_search_request=True,
            active_context={"label": "doc"},
            web_search_permission="enabled",
            source_path="/tmp/file.txt",
            has_explicit_source_path=True,
            follow_up_intent="key_points",
            active_context_mode="document",
        )
        self.assertEqual(rc.search_query, "query")
        self.assertTrue(rc.has_search_request)
        self.assertEqual(rc.web_search_permission, "enabled")
        self.assertEqual(rc.active_context_mode, "document")

    def test_frozen_immutability(self) -> None:
        rc = RequestContext(user_text="x", session_id="s")
        with self.assertRaises(AttributeError):
            rc.user_text = "changed"  # type: ignore[misc]


class SearchIntentResolutionTest(unittest.TestCase):

    def test_from_intent_explicit_web(self) -> None:
        decision = SearchIntentDecision(
            kind=SearchIntentKind.EXPLICIT_WEB,
            query="test query",
            score=10,
            answer_mode=AnswerMode.GENERAL,
            freshness_risk=FreshnessRisk.LOW,
        )
        sir = SearchIntentResolution.from_intent(decision)
        self.assertEqual(sir.explicit_query, "test query")
        self.assertEqual(sir.effective_query, "test query")
        self.assertIsNone(sir.probe_query)
        self.assertEqual(sir.intent_kind, SearchIntentKind.EXPLICIT_WEB)
        self.assertEqual(sir.answer_mode, AnswerMode.GENERAL)
        self.assertIsNone(sir.implicit_web_search_query)
        self.assertIsNone(sir.external_fact_query)

    def test_from_intent_live_latest_with_enabled_permission(self) -> None:
        decision = SearchIntentDecision(
            kind=SearchIntentKind.LIVE_LATEST,
            query="weather",
            score=8,
            answer_mode=AnswerMode.LATEST_UPDATE,
            freshness_risk=FreshnessRisk.HIGH,
        )
        sir = SearchIntentResolution.from_intent(decision, web_search_permission="enabled")
        self.assertIsNone(sir.explicit_query)
        self.assertEqual(sir.implicit_web_search_query, "weather")
        self.assertEqual(sir.intent_kind, SearchIntentKind.LIVE_LATEST)

    def test_from_intent_live_latest_without_enabled_permission(self) -> None:
        decision = SearchIntentDecision(
            kind=SearchIntentKind.LIVE_LATEST,
            query="weather",
            score=8,
        )
        sir = SearchIntentResolution.from_intent(decision, web_search_permission="disabled")
        self.assertIsNone(sir.implicit_web_search_query)

    def test_from_intent_external_fact(self) -> None:
        decision = SearchIntentDecision(
            kind=SearchIntentKind.EXTERNAL_FACT,
            query="BTS",
            score=5,
            answer_mode=AnswerMode.ENTITY_CARD,
        )
        sir = SearchIntentResolution.from_intent(decision)
        self.assertIsNone(sir.explicit_query)
        self.assertEqual(sir.external_fact_query, "BTS")
        self.assertEqual(sir.intent_kind, SearchIntentKind.EXTERNAL_FACT)
        self.assertEqual(sir.answer_mode, AnswerMode.ENTITY_CARD)

    def test_from_intent_none(self) -> None:
        decision = SearchIntentDecision()
        sir = SearchIntentResolution.from_intent(decision)
        self.assertIsNone(sir.explicit_query)
        self.assertIsNone(sir.implicit_web_search_query)
        self.assertIsNone(sir.external_fact_query)
        self.assertEqual(sir.intent_kind, SearchIntentKind.NONE)

    def test_apply_entity_reinvestigation(self) -> None:
        decision = SearchIntentDecision(
            kind=SearchIntentKind.EXPLICIT_WEB,
            query="game X",
            score=10,
            answer_mode=AnswerMode.GENERAL,
            freshness_risk=FreshnessRisk.LOW,
        )
        sir = SearchIntentResolution.from_intent(decision)
        self.assertEqual(sir.intent_kind, SearchIntentKind.EXPLICIT_WEB)
        self.assertEqual(sir.answer_mode, AnswerMode.GENERAL)

        sir.apply_entity_reinvestigation(effective_query="game X official")
        self.assertEqual(sir.intent_kind, SearchIntentKind.EXTERNAL_FACT)
        self.assertEqual(sir.answer_mode, AnswerMode.ENTITY_CARD)
        self.assertEqual(sir.freshness_risk, FreshnessRisk.LOW)
        self.assertEqual(sir.probe_query, "game X")
        self.assertEqual(sir.effective_query, "game X official")

    def test_raw_decision_preserved_after_reinvestigation(self) -> None:
        decision = SearchIntentDecision(
            kind=SearchIntentKind.EXPLICIT_WEB,
            query="original",
            score=10,
        )
        sir = SearchIntentResolution.from_intent(decision)
        sir.apply_entity_reinvestigation(effective_query="modified")
        self.assertEqual(sir.raw_decision.kind, SearchIntentKind.EXPLICIT_WEB)
        self.assertEqual(sir.raw_decision.query, "original")
