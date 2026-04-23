"""Tests for app.handlers.preferences."""

from __future__ import annotations

import unittest
from typing import Any

from app.handlers.preferences import PreferenceHandlerMixin


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


if __name__ == "__main__":
    unittest.main()
