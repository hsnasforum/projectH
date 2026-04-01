"""Tests verifying that active preferences are injected into model prompts."""

from __future__ import annotations

import unittest

from model_adapter.ollama import OllamaModelAdapter
from model_adapter.mock import MockModelAdapter


class PreferenceFormatBlockTest(unittest.TestCase):
    """Test the _format_preference_block static method."""

    def test_none_returns_empty(self) -> None:
        self.assertEqual(OllamaModelAdapter._format_preference_block(None), "")

    def test_empty_list_returns_empty(self) -> None:
        self.assertEqual(OllamaModelAdapter._format_preference_block([]), "")

    def test_single_preference(self) -> None:
        prefs = [{"description": "'~입니다' → '~이다' 체를 선호", "fingerprint": "sha256:abc"}]
        result = OllamaModelAdapter._format_preference_block(prefs)
        self.assertIn("User correction preferences", result)
        self.assertIn("'~입니다' → '~이다' 체를 선호", result)

    def test_multiple_preferences(self) -> None:
        prefs = [
            {"description": "패턴 A", "fingerprint": "sha256:aaa"},
            {"description": "패턴 B", "fingerprint": "sha256:bbb"},
        ]
        result = OllamaModelAdapter._format_preference_block(prefs)
        self.assertIn("패턴 A", result)
        self.assertIn("패턴 B", result)

    def test_max_10_preferences(self) -> None:
        prefs = [{"description": f"패턴 {i}", "fingerprint": f"fp{i}"} for i in range(15)]
        result = OllamaModelAdapter._format_preference_block(prefs)
        self.assertIn("패턴 9", result)
        self.assertNotIn("패턴 10", result)

    def test_empty_description_skipped(self) -> None:
        prefs = [
            {"description": "", "fingerprint": "fp1"},
            {"description": "유효한 패턴", "fingerprint": "fp2"},
        ]
        result = OllamaModelAdapter._format_preference_block(prefs)
        self.assertIn("유효한 패턴", result)
        self.assertEqual(result.count("- "), 1)


class MockModelPreferenceTest(unittest.TestCase):
    """Test that MockModelAdapter surfaces preferences in mock responses."""

    def test_respond_without_preferences(self) -> None:
        model = MockModelAdapter()
        response = model.respond("hello")
        self.assertIn("[모의 응답]", response)
        self.assertNotIn("선호", response)

    def test_respond_with_preferences(self) -> None:
        model = MockModelAdapter()
        prefs = [{"description": "테스트 패턴", "fingerprint": "fp"}]
        response = model.respond("hello", active_preferences=prefs)
        self.assertIn("선호 1건 반영", response)

    def test_answer_with_context_accepts_preferences(self) -> None:
        model = MockModelAdapter()
        prefs = [{"description": "패턴", "fingerprint": "fp"}]
        # Should not raise
        response = model.answer_with_context(
            intent="general",
            user_request="test",
            context_label="doc",
            source_paths=["/tmp/file.txt"],
            context_excerpt="some context",
            active_preferences=prefs,
        )
        self.assertIsInstance(response, str)
