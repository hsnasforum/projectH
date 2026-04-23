"""Tests for app.handlers.preferences."""

from __future__ import annotations

from typing import Any
import unittest

from app.handlers.preferences import PreferenceHandlerMixin, _jaccard_word_similarity


class _PreferenceStore:
    def __init__(self, preferences: list[dict[str, Any]]) -> None:
        self._preferences = preferences

    def list_all(self) -> list[dict[str, Any]]:
        return self._preferences


class _SessionStore:
    def get_global_audit_summary(self) -> dict[str, Any]:
        return {"per_preference_stats": {}}


class _PreferenceService(PreferenceHandlerMixin):
    def __init__(self, preferences: list[dict[str, Any]]) -> None:
        self.preference_store = _PreferenceStore(preferences)
        self.session_store = _SessionStore()


class PreferenceHandlerTest(unittest.TestCase):
    def test_list_preferences_payload_quality_info_present(self) -> None:
        service = _PreferenceService([
            {
                "preference_id": "pref-quality",
                "delta_fingerprint": "fingerprint-quality",
                "description": "quality preference",
                "status": "candidate",
                "avg_similarity_score": 0.15,
            }
        ])

        payload = service.list_preferences_payload()
        pref = payload["preferences"][0]

        self.assertEqual(pref["quality_info"]["avg_similarity_score"], 0.15)
        self.assertIs(pref["quality_info"]["is_high_quality"], True)

    def test_list_preferences_payload_quality_info_none(self) -> None:
        service = _PreferenceService([
            {
                "preference_id": "pref-no-quality",
                "delta_fingerprint": "fingerprint-no-quality",
                "description": "no quality preference",
                "status": "candidate",
            }
        ])

        payload = service.list_preferences_payload()
        pref = payload["preferences"][0]

        self.assertIsNone(pref["quality_info"]["avg_similarity_score"])
        self.assertIsNone(pref["quality_info"]["is_high_quality"])

    def test_list_preferences_payload_no_conflict_for_dissimilar_descriptions(self) -> None:
        service = _PreferenceService([
            {
                "preference_id": "pref-active-a",
                "delta_fingerprint": "fingerprint-a",
                "description": "교정 후 간결하게 유지",
                "status": "active",
            },
            {
                "preference_id": "pref-active-b",
                "delta_fingerprint": "fingerprint-b",
                "description": "출처와 날짜를 명확하게 표시",
                "status": "active",
            },
        ])

        payload = service.list_preferences_payload()

        for pref in payload["preferences"]:
            self.assertFalse(pref["conflict_info"]["has_conflict"])
            self.assertEqual(pref["conflict_info"]["conflicting_preference_ids"], [])

    def test_list_preferences_payload_conflict_for_similar_descriptions(self) -> None:
        service = _PreferenceService([
            {
                "preference_id": "pref-active-a",
                "delta_fingerprint": "fingerprint-a",
                "description": "교정 후 간결하게",
                "status": "active",
            },
            {
                "preference_id": "pref-active-b",
                "delta_fingerprint": "fingerprint-b",
                "description": "교정 후 간결하게 유지",
                "status": "active",
            },
            {
                "preference_id": "pref-candidate",
                "delta_fingerprint": "fingerprint-c",
                "description": "교정 후 간결하게",
                "status": "candidate",
            },
        ])

        payload = service.list_preferences_payload()
        by_id = {pref["preference_id"]: pref for pref in payload["preferences"]}

        self.assertTrue(by_id["pref-active-a"]["conflict_info"]["has_conflict"])
        self.assertEqual(
            by_id["pref-active-a"]["conflict_info"]["conflicting_preference_ids"],
            ["pref-active-b"],
        )
        self.assertTrue(by_id["pref-active-b"]["conflict_info"]["has_conflict"])
        self.assertEqual(
            by_id["pref-active-b"]["conflict_info"]["conflicting_preference_ids"],
            ["pref-active-a"],
        )
        self.assertFalse(by_id["pref-candidate"]["conflict_info"]["has_conflict"])

    def test_get_preference_audit_returns_counts(self) -> None:
        service = _PreferenceService([
            {
                "preference_id": "pref-active-a",
                "delta_fingerprint": "fingerprint-a",
                "description": "교정 후 간결하게",
                "status": "active",
            },
            {
                "preference_id": "pref-active-b",
                "delta_fingerprint": "fingerprint-b",
                "description": "교정 후 간결하게 유지",
                "status": "active",
            },
            {
                "preference_id": "pref-candidate",
                "delta_fingerprint": "fingerprint-c",
                "description": "후보 설명",
                "status": "candidate",
            },
            {
                "preference_id": "pref-paused",
                "delta_fingerprint": "fingerprint-d",
                "description": "일시중지 설명",
                "status": "paused",
            },
        ])

        audit = service.get_preference_audit()

        self.assertEqual(audit["total"], 4)
        self.assertEqual(audit["by_status"]["active"], 2)
        self.assertEqual(audit["by_status"]["candidate"], 1)
        self.assertEqual(audit["by_status"]["paused"], 1)
        self.assertEqual(audit["conflict_pair_count"], 1)

    def test_jaccard_word_similarity_thresholds(self) -> None:
        self.assertAlmostEqual(_jaccard_word_similarity("hello world", "hello world"), 1.0)
        self.assertAlmostEqual(_jaccard_word_similarity("hello world", "foo bar"), 0.0)
        self.assertAlmostEqual(_jaccard_word_similarity("a b", "a c"), 1 / 3)
        self.assertGreater(
            _jaccard_word_similarity("교정 후 간결하게", "교정 후 간결하게 유지"),
            0.7,
        )


if __name__ == "__main__":
    unittest.main()
