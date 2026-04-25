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


class _SessionStore:
    def get_global_audit_summary(self) -> dict[str, Any]:
        return {"per_preference_stats": {}}


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
    ) -> None:
        self.preference_store = _PreferenceStore(preferences)
        self.session_store = _SessionStore()
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
