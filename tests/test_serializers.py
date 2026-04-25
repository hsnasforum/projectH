"""Tests for app.serializers."""

from __future__ import annotations

import unittest
from typing import Any

from app.serializers import SerializerMixin


class _CorrectionStore:
    def __init__(self, corrections_by_artifact: dict[str, list[dict[str, Any]]]) -> None:
        self._corrections_by_artifact = corrections_by_artifact

    def find_by_artifact(self, artifact_id: str) -> list[dict[str, Any]]:
        return self._corrections_by_artifact.get(artifact_id, [])


class _Serializer(SerializerMixin):
    def __init__(self, corrections_by_artifact: dict[str, list[dict[str, Any]]]) -> None:
        self.correction_store = _CorrectionStore(corrections_by_artifact)

    def _normalize_optional_text(self, raw_value: Any) -> str | None:
        if not isinstance(raw_value, str):
            return None
        normalized = raw_value.strip()
        return normalized or None


def _review_queue_message() -> dict[str, Any]:
    return {
        "message_id": "msg-quality",
        "source_message_id": "msg-quality",
        "artifact_id": "artifact-quality",
        "artifact_kind": "grounded_brief",
        "original_response_snapshot": {
            "artifact_id": "artifact-quality",
            "artifact_kind": "grounded_brief",
            "draft_text": "original summary",
        },
        "durable_candidate": {
            "candidate_id": "candidate-quality",
            "candidate_scope": "durable_candidate",
            "candidate_family": "correction_rewrite_preference",
            "artifact_id": "artifact-quality",
            "source_message_id": "msg-quality",
            "statement": "explicit rewrite correction recorded for this grounded brief",
            "supporting_artifact_ids": ["artifact-quality"],
            "supporting_source_message_ids": ["msg-quality"],
            "supporting_signal_refs": [
                {
                    "signal_name": "session_local_memory_signal.correction_signal",
                    "relationship": "primary_basis",
                }
            ],
            "supporting_confirmation_refs": [
                {
                    "artifact_id": "artifact-quality",
                    "source_message_id": "msg-quality",
                    "candidate_id": "candidate-quality",
                    "candidate_updated_at": "2026-04-23T00:00:00+00:00",
                    "confirmation_label": "explicit_reuse_confirmation",
                    "recorded_at": "2026-04-23T00:01:00+00:00",
                }
            ],
            "evidence_strength": "explicit_single_artifact",
            "has_explicit_confirmation": True,
            "promotion_basis": "explicit_confirmation",
            "promotion_eligibility": "eligible_for_review",
            "created_at": "2026-04-23T00:01:00+00:00",
            "updated_at": "2026-04-23T00:01:00+00:00",
        },
    }


class SerializerReviewQueueQualityTest(unittest.TestCase):
    def test_build_review_queue_items_includes_quality_info(self) -> None:
        serializer = _Serializer({
            "artifact-quality": [{"similarity_score": 0.15}],
        })

        items = serializer._build_review_queue_items([_review_queue_message()])

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["quality_info"]["avg_similarity_score"], 0.15)
        self.assertIs(items[0]["quality_info"]["is_high_quality"], True)

    def test_build_review_queue_items_quality_info_none_when_no_corrections(self) -> None:
        serializer = _Serializer({"artifact-quality": []})

        items = serializer._build_review_queue_items([_review_queue_message()])

        self.assertEqual(len(items), 1)
        self.assertIsNone(items[0]["quality_info"]["avg_similarity_score"])
        self.assertIsNone(items[0]["quality_info"]["is_high_quality"])

    def test_build_review_queue_items_includes_recent_context_turns(self) -> None:
        serializer = _Serializer({"artifact-quality": []})
        long_user_text = "긴 사용자 맥락 " + ("x" * 600)
        messages = [
            {"message_id": "msg-old", "role": "user", "text": "오래된 맥락"},
            {"message_id": "msg-context-1", "role": "assistant", "text": "첫 번째 최근 답변"},
            {"message_id": "msg-context-2", "role": "user", "corrected_text": long_user_text},
            {"message_id": "msg-context-3", "role": "assistant", "content": "세 번째 최근 답변"},
            _review_queue_message(),
        ]

        items = serializer._build_review_queue_items(messages)

        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0]["context_turns"],
            [
                {"role": "assistant", "text": "첫 번째 최근 답변", "message_id": "msg-context-1"},
                {"role": "user", "text": long_user_text[:500], "message_id": "msg-context-2"},
                {"role": "assistant", "text": "세 번째 최근 답변", "message_id": "msg-context-3"},
            ],
        )
        self.assertLessEqual(len(items[0]["context_turns"][1]["text"]), 500)


if __name__ == "__main__":
    unittest.main()
