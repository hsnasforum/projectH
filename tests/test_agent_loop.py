from __future__ import annotations

import unittest
from typing import Any

from core.agent_loop import AgentLoop


class _PreferenceStore:
    def __init__(self, preferences: list[dict[str, Any]]) -> None:
        self._preferences = preferences

    def get_active_preferences(self) -> list[dict[str, Any]]:
        return list(self._preferences)


class _SessionStore:
    def __init__(self, per_preference_stats: dict[str, Any] | None = None) -> None:
        self._per_preference_stats = per_preference_stats or {}

    def get_global_audit_summary(self) -> dict[str, Any]:
        return {"per_preference_stats": self._per_preference_stats}


def _build_loop(
    preferences: list[dict[str, Any]] | None,
    per_preference_stats: dict[str, Any] | None = None,
) -> AgentLoop:
    loop = AgentLoop.__new__(AgentLoop)
    loop.preference_store = _PreferenceStore(preferences) if preferences is not None else None
    loop.session_store = _SessionStore(per_preference_stats)
    return loop


class AgentLoopPreferenceTest(unittest.TestCase):
    def test_get_active_preferences_returns_none_without_store(self) -> None:
        loop = _build_loop(None)

        self.assertIsNone(loop._get_active_preferences())

    def test_get_active_preferences_excludes_not_high_quality_by_default(self) -> None:
        loop = _build_loop(
            [
                {
                    "description": "reliable preference",
                    "delta_fingerprint": "fp-reliable",
                    "avg_similarity_score": 0.15,
                },
                {
                    "description": "low quality preference",
                    "delta_fingerprint": "fp-low-quality",
                    "quality_info": {"avg_similarity_score": 0.99, "is_high_quality": False},
                },
            ],
            {
                "fp-reliable": {"applied_count": 3, "corrected_count": 0},
                "fp-low-quality": {"applied_count": 3, "corrected_count": 0},
            },
        )

        self.assertEqual(
            loop._get_active_preferences(),
            [{"description": "reliable preference", "fingerprint": "fp-reliable"}],
        )

    def test_get_active_preferences_excludes_low_application_count_by_default(self) -> None:
        loop = _build_loop(
            [
                {
                    "description": "reliable preference",
                    "delta_fingerprint": "fp-reliable",
                    "avg_similarity_score": 0.15,
                },
                {
                    "description": "too few applications",
                    "delta_fingerprint": "fp-too-few",
                    "avg_similarity_score": 0.15,
                },
            ],
            {
                "fp-reliable": {"applied_count": 4, "corrected_count": 0},
                "fp-too-few": {"applied_count": 2, "corrected_count": 0},
            },
        )

        self.assertEqual(
            loop._get_active_preferences(),
            [{"description": "reliable preference", "fingerprint": "fp-reliable"}],
        )

    def test_get_active_preferences_can_include_all_active_preferences(self) -> None:
        loop = _build_loop(
            [
                {
                    "description": "reliable preference",
                    "delta_fingerprint": "fp-reliable",
                    "avg_similarity_score": 0.15,
                },
                {
                    "description": "too few applications",
                    "delta_fingerprint": "fp-too-few",
                    "avg_similarity_score": 0.15,
                },
            ],
            {
                "fp-reliable": {"applied_count": 4, "corrected_count": 0},
                "fp-too-few": {"applied_count": 2, "corrected_count": 0},
            },
        )

        self.assertEqual(
            loop._get_active_preferences(highly_reliable_only=False),
            [
                {"description": "reliable preference", "fingerprint": "fp-reliable"},
                {"description": "too few applications", "fingerprint": "fp-too-few"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
