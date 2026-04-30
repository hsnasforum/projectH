"""Tests for app.handlers.preferences."""

from __future__ import annotations

from typing import Any
import unittest

from app.handlers.preferences import PreferenceHandlerMixin, _jaccard_word_similarity


class _PreferenceStore:
    def __init__(self, preferences: list[dict[str, Any]]) -> None:
        self._preferences = preferences
        self.record_calls: list[dict[str, Any]] = []

    def list_all(self) -> list[dict[str, Any]]:
        return self._preferences

    def find_by_fingerprint(self, delta_fingerprint: str) -> dict[str, Any] | None:
        for preference in self._preferences:
            if preference.get("delta_fingerprint") == delta_fingerprint:
                return preference
        return None

    def record_reviewed_candidate_preference(
        self,
        *,
        delta_fingerprint: str,
        candidate_family: str,
        description: str,
        source_refs: dict[str, Any],
        avg_similarity_score: float | None = None,
        original_snippet: str | None = None,
        corrected_snippet: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        call = {
            "delta_fingerprint": delta_fingerprint,
            "candidate_family": candidate_family,
            "description": description,
            "source_refs": source_refs,
            "avg_similarity_score": avg_similarity_score,
            "original_snippet": original_snippet,
            "corrected_snippet": corrected_snippet,
            "status": status,
        }
        self.record_calls.append(call)
        existing = self.find_by_fingerprint(delta_fingerprint)
        if existing is not None:
            return existing
        record = {
            "preference_id": f"pref-{len(self._preferences) + 1}",
            "delta_fingerprint": delta_fingerprint,
            "pattern_family": candidate_family,
            "description": description,
            "reviewed_candidate_source_refs": [source_refs],
            "avg_similarity_score": avg_similarity_score,
            "original_snippet": original_snippet,
            "corrected_snippet": corrected_snippet,
            "status": status or "candidate",
        }
        self._preferences.append(record)
        return record


class _PreferenceStoreWithCandidates(_PreferenceStore):
    def __init__(self, preferences: list[dict[str, Any]]) -> None:
        super().__init__(preferences)
        self.get_candidates_calls = 0

    def get_candidates(self) -> list[dict[str, Any]]:
        self.get_candidates_calls += 1
        return [
            preference
            for preference in self._preferences
            if preference.get("status") == "candidate"
        ]


class _SessionStore:
    def __init__(self, summary: dict[str, Any] | None = None) -> None:
        self._summary = summary or {"per_preference_stats": {}}

    def get_global_audit_summary(self) -> dict[str, Any]:
        return self._summary


class _CorrectionStore:
    def __init__(self, adopted: list[dict[str, Any]]) -> None:
        self._adopted = adopted

    def find_adopted_corrections(self) -> list[dict[str, Any]]:
        return self._adopted


class _TaskLogger:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def log(self, *, session_id: str, action: str, detail: dict[str, Any]) -> None:
        self.entries.append({"session_id": session_id, "action": action, "detail": detail})


class _PreferenceService(PreferenceHandlerMixin):
    def __init__(
        self,
        preferences: list[dict[str, Any]],
        adopted_corrections: list[dict[str, Any]] | None = None,
        audit_summary: dict[str, Any] | None = None,
    ) -> None:
        self.preference_store = _PreferenceStore(preferences)
        self.session_store = _SessionStore(audit_summary)
        self.correction_store = _CorrectionStore(adopted_corrections or [])
        self.task_logger = _TaskLogger()


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

    def test_list_preferences_payload_includes_candidate_preferences_with_fallback(self) -> None:
        service = _PreferenceService([
            {
                "preference_id": "pref-active",
                "delta_fingerprint": "fingerprint-active",
                "description": "active preference",
                "status": "active",
            },
            {
                "preference_id": "pref-candidate-a",
                "delta_fingerprint": "fingerprint-candidate-a",
                "description": "candidate preference a",
                "status": "candidate",
                "avg_similarity_score": 0.15,
            },
            {
                "preference_id": "pref-candidate-b",
                "delta_fingerprint": "fingerprint-candidate-b",
                "description": "candidate preference b",
                "status": "candidate",
            },
        ])

        payload = service.list_preferences_payload()

        self.assertIn("candidate_preferences", payload)
        self.assertEqual(
            {pref["preference_id"] for pref in payload["candidate_preferences"]},
            {"pref-candidate-a", "pref-candidate-b"},
        )
        self.assertTrue(
            all(pref.get("status") == "candidate" for pref in payload["candidate_preferences"])
        )

    def test_list_preferences_payload_uses_get_candidates_when_available(self) -> None:
        preferences = [
            {
                "preference_id": "pref-active",
                "delta_fingerprint": "fingerprint-active",
                "description": "active preference",
                "status": "active",
            },
            {
                "preference_id": "pref-candidate",
                "delta_fingerprint": "fingerprint-candidate",
                "description": "candidate preference",
                "status": "candidate",
                "avg_similarity_score": 0.15,
            },
        ]
        service = _PreferenceService(
            preferences,
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-candidate": {"applied_count": 3, "corrected_count": 0},
                },
            },
        )
        candidate_store = _PreferenceStoreWithCandidates(preferences)
        service.preference_store = candidate_store

        payload = service.list_preferences_payload()

        self.assertEqual(candidate_store.get_candidates_calls, 1)
        self.assertEqual(len(payload["candidate_preferences"]), 1)
        candidate = payload["candidate_preferences"][0]
        self.assertEqual(candidate["preference_id"], "pref-candidate")
        self.assertEqual(candidate["status"], "candidate")
        self.assertIs(candidate["is_highly_reliable"], True)

    def test_list_preferences_payload_counts_high_quality_active_preferences(self) -> None:
        mixed_service = _PreferenceService([
            {
                "preference_id": "pref-active-high",
                "delta_fingerprint": "fingerprint-active-high",
                "description": "active high quality",
                "status": "active",
                "avg_similarity_score": 0.15,
            },
            {
                "preference_id": "pref-active-low",
                "delta_fingerprint": "fingerprint-active-low",
                "description": "active low quality",
                "status": "active",
                "avg_similarity_score": 0.99,
            },
            {
                "preference_id": "pref-candidate-high",
                "delta_fingerprint": "fingerprint-candidate-high",
                "description": "candidate high quality",
                "status": "candidate",
                "avg_similarity_score": 0.15,
            },
            {
                "preference_id": "pref-paused-high",
                "delta_fingerprint": "fingerprint-paused-high",
                "description": "paused high quality",
                "status": "paused",
                "avg_similarity_score": 0.15,
            },
        ])

        mixed_payload = mixed_service.list_preferences_payload()

        self.assertEqual(mixed_payload["high_quality_active_count"], 1)

        no_active_high_quality_service = _PreferenceService([
            {
                "preference_id": "pref-active-low-only",
                "delta_fingerprint": "fingerprint-active-low-only",
                "description": "active low quality only",
                "status": "active",
                "avg_similarity_score": 0.99,
            },
            {
                "preference_id": "pref-candidate-high-only",
                "delta_fingerprint": "fingerprint-candidate-high-only",
                "description": "candidate high quality only",
                "status": "candidate",
                "avg_similarity_score": 0.15,
            },
        ])

        no_active_high_quality_payload = no_active_high_quality_service.list_preferences_payload()

        self.assertEqual(no_active_high_quality_payload["high_quality_active_count"], 0)

    def test_list_preferences_payload_marks_highly_reliable_preferences(self) -> None:
        service = _PreferenceService(
            [
                {
                    "preference_id": "pref-reliable",
                    "delta_fingerprint": "fingerprint-reliable",
                    "description": "highly reliable preference",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-too-few",
                    "delta_fingerprint": "fingerprint-too-few",
                    "description": "too few applications",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-correction-rate",
                    "delta_fingerprint": "fingerprint-correction-rate",
                    "description": "correction rate at threshold",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-no-quality",
                    "delta_fingerprint": "fingerprint-no-quality",
                    "description": "no quality signal",
                    "status": "active",
                },
            ],
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-reliable": {"applied_count": 3, "corrected_count": 0},
                    "fingerprint-too-few": {"applied_count": 2, "corrected_count": 0},
                    "fingerprint-correction-rate": {"applied_count": 20, "corrected_count": 3},
                    "fingerprint-no-quality": {"applied_count": 5, "corrected_count": 0},
                },
            },
        )

        payload = service.list_preferences_payload()
        by_id = {pref["preference_id"]: pref for pref in payload["preferences"]}

        self.assertIs(by_id["pref-reliable"]["is_highly_reliable"], True)
        self.assertIs(by_id["pref-too-few"]["is_highly_reliable"], False)
        self.assertIs(by_id["pref-correction-rate"]["is_highly_reliable"], False)
        self.assertIs(by_id["pref-no-quality"]["is_highly_reliable"], False)

    def test_list_preferences_payload_includes_injected_count(self) -> None:
        service = _PreferenceService(
            [
                {
                    "preference_id": "pref-injected",
                    "delta_fingerprint": "fingerprint-injected",
                    "description": "injected preference",
                    "status": "active",
                },
                {
                    "preference_id": "pref-default",
                    "delta_fingerprint": "fingerprint-default",
                    "description": "default injected count",
                    "status": "active",
                },
            ],
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-injected": {
                        "applied_count": 2,
                        "corrected_count": 1,
                        "injected_count": 4,
                    },
                },
            },
        )

        payload = service.list_preferences_payload()
        by_id = {pref["preference_id"]: pref for pref in payload["preferences"]}

        self.assertEqual(by_id["pref-injected"]["injected_count"], 4)
        self.assertEqual(
            by_id["pref-injected"]["reliability_stats"],
            {"applied_count": 2, "corrected_count": 1},
        )
        self.assertEqual(by_id["pref-default"]["injected_count"], 0)

    def test_list_preferences_payload_counts_highly_reliable_active_preferences(self) -> None:
        mixed_service = _PreferenceService(
            [
                {
                    "preference_id": "pref-active-reliable-a",
                    "delta_fingerprint": "fingerprint-active-reliable-a",
                    "description": "first active reliable preference",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-active-reliable-b",
                    "delta_fingerprint": "fingerprint-active-reliable-b",
                    "description": "second active reliable preference",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-active-unreliable",
                    "delta_fingerprint": "fingerprint-active-unreliable",
                    "description": "active but too few applications",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-candidate-reliable",
                    "delta_fingerprint": "fingerprint-candidate-reliable",
                    "description": "candidate reliable preference",
                    "status": "candidate",
                    "avg_similarity_score": 0.15,
                },
            ],
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-active-reliable-a": {"applied_count": 3, "corrected_count": 0},
                    "fingerprint-active-reliable-b": {"applied_count": 8, "corrected_count": 1},
                    "fingerprint-active-unreliable": {"applied_count": 2, "corrected_count": 0},
                    "fingerprint-candidate-reliable": {"applied_count": 5, "corrected_count": 0},
                },
            },
        )

        mixed_payload = mixed_service.list_preferences_payload()

        self.assertEqual(mixed_payload["highly_reliable_active_count"], 2)

        no_active_highly_reliable_service = _PreferenceService(
            [
                {
                    "preference_id": "pref-active-low",
                    "delta_fingerprint": "fingerprint-active-low",
                    "description": "active low quality preference",
                    "status": "active",
                    "avg_similarity_score": 0.99,
                },
                {
                    "preference_id": "pref-paused-reliable",
                    "delta_fingerprint": "fingerprint-paused-reliable",
                    "description": "paused reliable preference",
                    "status": "paused",
                    "avg_similarity_score": 0.15,
                },
            ],
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-active-low": {"applied_count": 7, "corrected_count": 0},
                    "fingerprint-paused-reliable": {"applied_count": 7, "corrected_count": 0},
                },
            },
        )

        no_active_highly_reliable_payload = no_active_highly_reliable_service.list_preferences_payload()

        self.assertEqual(no_active_highly_reliable_payload["highly_reliable_active_count"], 0)

    def test_list_preferences_payload_counts_low_reliability_active_preferences(self) -> None:
        service = _PreferenceService(
            [
                {
                    "preference_id": "pref-active-low",
                    "delta_fingerprint": "fingerprint-active-low",
                    "description": "active low reliability preference",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-active-reliable",
                    "delta_fingerprint": "fingerprint-active-reliable",
                    "description": "active reliable preference",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-active-measuring",
                    "delta_fingerprint": "fingerprint-active-measuring",
                    "description": "active measuring preference",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-candidate-low",
                    "delta_fingerprint": "fingerprint-candidate-low",
                    "description": "candidate low reliability preference",
                    "status": "candidate",
                    "avg_similarity_score": 0.15,
                },
            ],
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-active-low": {"applied_count": 5, "corrected_count": 2},
                    "fingerprint-active-reliable": {"applied_count": 5, "corrected_count": 0},
                    "fingerprint-active-measuring": {"applied_count": 2, "corrected_count": 1},
                    "fingerprint-candidate-low": {"applied_count": 5, "corrected_count": 2},
                },
            },
        )

        payload = service.list_preferences_payload()

        self.assertEqual(payload["low_reliability_active_count"], 1)

    def test_list_preferences_payload_zero_low_reliability_when_all_reliable(self) -> None:
        service = _PreferenceService(
            [
                {
                    "preference_id": "pref-reliable-a",
                    "delta_fingerprint": "fingerprint-reliable-a",
                    "description": "first active reliable preference",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-reliable-b",
                    "delta_fingerprint": "fingerprint-reliable-b",
                    "description": "second active reliable preference",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
            ],
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-reliable-a": {"applied_count": 3, "corrected_count": 0},
                    "fingerprint-reliable-b": {"applied_count": 8, "corrected_count": 1},
                },
            },
        )

        payload = service.list_preferences_payload()

        self.assertEqual(payload["low_reliability_active_count"], 0)

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

    def test_list_preferences_payload_marks_conflict_severity(self) -> None:
        service = _PreferenceService(
            [
                {
                    "preference_id": "pref-both-high-a",
                    "delta_fingerprint": "fingerprint-both-high-a",
                    "description": "prefer concise summary wording",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-both-high-b",
                    "delta_fingerprint": "fingerprint-both-high-b",
                    "description": "prefer concise summary wording always",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-one-high",
                    "delta_fingerprint": "fingerprint-one-high",
                    "description": "include cited source date",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-one-normal",
                    "delta_fingerprint": "fingerprint-one-normal",
                    "description": "include cited source date always",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-neither-a",
                    "delta_fingerprint": "fingerprint-neither-a",
                    "description": "keep final answer brief",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-neither-b",
                    "delta_fingerprint": "fingerprint-neither-b",
                    "description": "keep final answer brief always",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
                {
                    "preference_id": "pref-no-conflict",
                    "delta_fingerprint": "fingerprint-no-conflict",
                    "description": "use korean honorific style",
                    "status": "active",
                    "avg_similarity_score": 0.15,
                },
            ],
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-both-high-a": {"applied_count": 3, "corrected_count": 0},
                    "fingerprint-both-high-b": {"applied_count": 4, "corrected_count": 0},
                    "fingerprint-one-high": {"applied_count": 3, "corrected_count": 0},
                    "fingerprint-one-normal": {"applied_count": 2, "corrected_count": 0},
                    "fingerprint-neither-a": {"applied_count": 2, "corrected_count": 0},
                    "fingerprint-neither-b": {"applied_count": 2, "corrected_count": 0},
                    "fingerprint-no-conflict": {"applied_count": 3, "corrected_count": 0},
                },
            },
        )

        payload = service.list_preferences_payload()
        by_id = {pref["preference_id"]: pref for pref in payload["preferences"]}

        self.assertEqual(by_id["pref-both-high-a"]["conflict_info"]["conflict_severity"], "high")
        self.assertEqual(by_id["pref-both-high-b"]["conflict_info"]["conflict_severity"], "high")
        self.assertEqual(by_id["pref-one-high"]["conflict_info"]["conflict_severity"], "high")
        self.assertEqual(by_id["pref-one-normal"]["conflict_info"]["conflict_severity"], "high")
        self.assertEqual(by_id["pref-neither-a"]["conflict_info"]["conflict_severity"], "normal")
        self.assertEqual(by_id["pref-neither-b"]["conflict_info"]["conflict_severity"], "normal")
        self.assertFalse(by_id["pref-no-conflict"]["conflict_info"]["has_conflict"])
        self.assertEqual(by_id["pref-no-conflict"]["conflict_info"]["conflict_severity"], "none")

    def test_list_preferences_payload_aggregates_active_reliability_totals(self) -> None:
        no_active_service = _PreferenceService(
            [
                {
                    "preference_id": "pref-candidate-only",
                    "delta_fingerprint": "fingerprint-candidate-only",
                    "description": "후보만 있는 선호",
                    "status": "candidate",
                },
            ],
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-candidate-only": {
                        "applied_count": 7,
                        "corrected_count": 3,
                    },
                },
            },
        )

        no_active_payload = no_active_service.list_preferences_payload()

        self.assertEqual(no_active_payload["total_applied"], 0)
        self.assertEqual(no_active_payload["total_corrected"], 0)

        mixed_service = _PreferenceService(
            [
                {
                    "preference_id": "pref-active-a",
                    "delta_fingerprint": "fingerprint-active-a",
                    "description": "첫 활성 선호",
                    "status": "active",
                },
                {
                    "preference_id": "pref-active-b",
                    "delta_fingerprint": "fingerprint-active-b",
                    "description": "둘째 활성 선호",
                    "status": "active",
                },
                {
                    "preference_id": "pref-paused",
                    "delta_fingerprint": "fingerprint-paused",
                    "description": "일시중지 선호",
                    "status": "paused",
                },
                {
                    "preference_id": "pref-candidate",
                    "delta_fingerprint": "fingerprint-candidate",
                    "description": "후보 선호",
                    "status": "candidate",
                },
            ],
            audit_summary={
                "per_preference_stats": {
                    "fingerprint-active-a": {"applied_count": 2, "corrected_count": 1},
                    "fingerprint-active-b": {"applied_count": 5, "corrected_count": 4},
                    "fingerprint-paused": {"applied_count": 11, "corrected_count": 9},
                    "fingerprint-candidate": {"applied_count": 13, "corrected_count": 8},
                },
            },
        )

        mixed_payload = mixed_service.list_preferences_payload()

        self.assertEqual(mixed_payload["total_applied"], 7)
        self.assertEqual(mixed_payload["total_corrected"], 5)

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

    def test_get_preference_audit_includes_adopted_count_zero(self) -> None:
        service = _PreferenceService([])

        audit = service.get_preference_audit()

        self.assertIn("adopted_corrections_count", audit)
        self.assertEqual(audit["adopted_corrections_count"], 0)
        self.assertIn("available_to_sync_count", audit)
        self.assertEqual(audit["available_to_sync_count"], 0)

    def test_get_preference_audit_includes_adopted_count_nonzero(self) -> None:
        service = _PreferenceService([], adopted_corrections=[{"status": "active"}])

        audit = service.get_preference_audit()

        self.assertEqual(audit["adopted_corrections_count"], 1)
        self.assertEqual(audit["available_to_sync_count"], 0)

    def test_get_preference_audit_counts_available_adopted_corrections(self) -> None:
        service = _PreferenceService(
            [],
            adopted_corrections=[
                {
                    "correction_id": "correction-available",
                    "delta_fingerprint": "sha256:available",
                    "status": "active",
                }
            ],
        )

        audit = service.get_preference_audit()

        self.assertEqual(audit["adopted_corrections_count"], 1)
        self.assertEqual(audit["available_to_sync_count"], 1)

    def test_get_preference_audit_excludes_existing_preference_from_available_sync(self) -> None:
        service = _PreferenceService(
            [
                {
                    "preference_id": "pref-existing",
                    "delta_fingerprint": "sha256:existing",
                    "description": "existing candidate",
                    "status": "candidate",
                }
            ],
            adopted_corrections=[
                {
                    "correction_id": "correction-existing",
                    "delta_fingerprint": "sha256:existing",
                    "status": "active",
                }
            ],
        )

        audit = service.get_preference_audit()

        self.assertEqual(audit["adopted_corrections_count"], 1)
        self.assertEqual(audit["available_to_sync_count"], 0)

    def test_sync_adopted_corrections_to_candidates_records_mapping(self) -> None:
        service = _PreferenceService(
            [],
            adopted_corrections=[
                {
                    "correction_id": "correction-1",
                    "artifact_id": "artifact-1",
                    "session_id": "session-1",
                    "source_message_id": "message-1",
                    "original_text": "old text",
                    "corrected_text": "new text",
                    "delta_fingerprint": "sha256:adopted-fp",
                    "delta_summary": "Prefer the corrected wording",
                    "pattern_family": "correction_rewrite_preference",
                    "activated_at": "2026-04-24T01:02:03Z",
                }
            ],
        )

        payload = service.sync_adopted_corrections_to_candidates()

        self.assertEqual(payload["synced_count"], 1)
        self.assertEqual(payload["skipped_count"], 0)
        self.assertEqual(len(service.preference_store.record_calls), 1)
        call = service.preference_store.record_calls[0]
        self.assertEqual(call["delta_fingerprint"], "sha256:adopted-fp")
        self.assertEqual(call["candidate_family"], "correction_rewrite_preference")
        self.assertEqual(call["description"], "Prefer the corrected wording")
        self.assertEqual(call["original_snippet"], "old text")
        self.assertEqual(call["corrected_snippet"], "new text")
        self.assertEqual(call["source_refs"]["candidate_id"], "adopted-correction:correction-1")
        self.assertEqual(call["source_refs"]["correction_id"], "correction-1")
        self.assertEqual(call["source_refs"]["source"], "adopted_correction")
        self.assertEqual(call["source_refs"]["artifact_id"], "artifact-1")
        self.assertEqual(call["source_refs"]["source_message_id"], "message-1")
        self.assertEqual(call["source_refs"]["session_id"], "session-1")
        self.assertEqual(service.task_logger.entries[0]["action"], "adopted_corrections_synced_to_candidates")

    def test_sync_adopted_corrections_to_candidates_skips_existing_fingerprint(self) -> None:
        service = _PreferenceService(
            [
                {
                    "preference_id": "pref-existing",
                    "delta_fingerprint": "sha256:existing",
                    "description": "existing candidate",
                    "status": "candidate",
                }
            ],
            adopted_corrections=[
                {
                    "correction_id": "correction-existing",
                    "corrected_text": "updated text",
                    "delta_fingerprint": "sha256:existing",
                    "pattern_family": "correction_rewrite_preference",
                }
            ],
        )

        payload = service.sync_adopted_corrections_to_candidates()

        self.assertEqual(payload["synced_count"], 0)
        self.assertEqual(payload["skipped_count"], 1)
        self.assertEqual(service.preference_store.record_calls, [])
        self.assertEqual(len(service.preference_store.list_all()), 1)

    def test_sync_adopted_corrections_to_candidates_no_active_corrections(self) -> None:
        service = _PreferenceService([], adopted_corrections=[])

        payload = service.sync_adopted_corrections_to_candidates()

        self.assertEqual(payload["synced_count"], 0)
        self.assertEqual(payload["skipped_count"], 0)
        self.assertEqual(service.preference_store.record_calls, [])

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
