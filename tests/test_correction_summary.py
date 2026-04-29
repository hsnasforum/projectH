"""Tests for GET /api/corrections/summary via CorrectionHandlerMixin."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.handlers.corrections import CorrectionHandlerMixin
from core.contracts import PreferenceStatus
from storage.correction_store import CorrectionStore
from storage.preference_store import PreferenceStore


class _CorrectionSummaryService(CorrectionHandlerMixin):
    def __init__(
        self,
        store: CorrectionStore,
        preference_store: PreferenceStore | None = None,
    ) -> None:
        self.correction_store = store
        self.preference_store = preference_store


class CorrectionSummaryTest(unittest.TestCase):
    def _make_store(self, base_dir: str) -> CorrectionStore:
        return CorrectionStore(base_dir=str(Path(base_dir) / "corrections"))

    def _record_confirmed_pattern(
        self,
        store: CorrectionStore,
        *,
        count: int,
    ) -> str:
        records = []
        for index in range(count):
            record = store.record_correction(
                artifact_id=f"art-recur-{count}-{index}",
                session_id=f"s{index}",
                source_message_id=f"msg-recur-{count}-{index}",
                original_text="Make the answer short.",
                corrected_text="Make the answer concise.",
            )
            self.assertIsNotNone(record)
            records.append(record)
        delta_fingerprint = records[0]["delta_fingerprint"]
        confirmed = store.confirm_by_fingerprint(delta_fingerprint)
        self.assertEqual(len(confirmed), count)
        return delta_fingerprint

    def test_empty_store_returns_zero_total(self) -> None:
        with TemporaryDirectory() as d:
            service = _CorrectionSummaryService(self._make_store(d))

            payload = service.get_correction_summary()

            self.assertIs(payload["ok"], True)
            self.assertEqual(payload["total"], 0)
            self.assertEqual(payload["by_status"], {})
            self.assertEqual(payload["top_recurring_fingerprints"], [])

    def test_summary_counts_by_status_and_recurring_patterns(self) -> None:
        with TemporaryDirectory() as d:
            store = self._make_store(d)
            first = store.record_correction(
                artifact_id="art1",
                session_id="s1",
                source_message_id="msg1",
                original_text="original text one",
                corrected_text="corrected text one",
            )
            second = store.record_correction(
                artifact_id="art2",
                session_id="s2",
                source_message_id="msg2",
                original_text="original text one",
                corrected_text="corrected text one",
            )
            self.assertIsNotNone(first)
            self.assertIsNotNone(second)

            payload = _CorrectionSummaryService(store).get_correction_summary()

            self.assertEqual(payload["total"], 2)
            self.assertEqual(payload["by_status"], {"recorded": 2})
            fps = payload["top_recurring_fingerprints"]
            self.assertEqual(len(fps), 1)
            self.assertEqual(fps[0]["delta_fingerprint"], first["delta_fingerprint"])
            self.assertEqual(fps[0]["recurrence_count"], 2)
            self.assertEqual(fps[0].get("original_snippet"), "original text one")
            self.assertEqual(fps[0].get("corrected_snippet"), "corrected text one")

    def test_correction_list_empty_store(self) -> None:
        with TemporaryDirectory() as d:
            service = _CorrectionSummaryService(self._make_store(d))

            payload = service.get_correction_list()

            self.assertIs(payload["ok"], True)
            self.assertEqual(payload["corrections"], [])

    def test_correction_list_returns_recent(self) -> None:
        with TemporaryDirectory() as d:
            store = self._make_store(d)
            record = store.record_correction(
                artifact_id="art1",
                session_id="s1",
                source_message_id="msg1",
                original_text="original text one",
                corrected_text="corrected text one",
            )
            self.assertIsNotNone(record)

            payload = _CorrectionSummaryService(store).get_correction_list()

            self.assertIs(payload["ok"], True)
            self.assertEqual(len(payload["corrections"]), 1)
            self.assertEqual(payload["corrections"][0]["correction_id"], record["correction_id"])

    def test_correction_list_filters_by_status(self) -> None:
        with TemporaryDirectory() as d:
            store = self._make_store(d)
            recorded = store.record_correction(
                artifact_id="art1",
                session_id="s1",
                source_message_id="msg1",
                original_text="original recorded text",
                corrected_text="corrected recorded text",
            )
            confirmed = store.record_correction(
                artifact_id="art2",
                session_id="s2",
                source_message_id="msg2",
                original_text="Please include every detail in the response.",
                corrected_text="Please keep the response brief.",
            )
            self.assertIsNotNone(recorded)
            self.assertIsNotNone(confirmed)
            confirmed_records = store.confirm_by_fingerprint(confirmed["delta_fingerprint"])
            self.assertEqual(len(confirmed_records), 1)

            payload = _CorrectionSummaryService(store).get_correction_list(status="confirmed")

            self.assertIs(payload["ok"], True)
            self.assertEqual(len(payload["corrections"]), 1)
            self.assertEqual(payload["corrections"][0]["correction_id"], confirmed["correction_id"])
            self.assertEqual(payload["corrections"][0]["status"], "confirmed")
            self.assertNotEqual(payload["corrections"][0]["correction_id"], recorded["correction_id"])

    def test_promote_pattern_seeds_reliability_from_recurrence(self) -> None:
        with TemporaryDirectory() as d:
            correction_store = self._make_store(d)
            preference_store = PreferenceStore(base_dir=str(Path(d) / "preferences"))
            delta_fingerprint = self._record_confirmed_pattern(correction_store, count=3)

            payload = _CorrectionSummaryService(
                correction_store,
                preference_store,
            ).promote_correction_pattern({"delta_fingerprint": delta_fingerprint})

            self.assertEqual(payload["promoted_count"], 3)
            preference = preference_store.find_by_fingerprint(delta_fingerprint)
            self.assertIsNotNone(preference)
            assert preference is not None
            self.assertEqual(preference["status"], PreferenceStatus.ACTIVE)
            self.assertEqual(
                preference["reliability_stats"],
                {"applied_count": 3, "corrected_count": 0},
            )

    def test_promote_pattern_reports_highly_reliable_true_from_seeded_recurrence(self) -> None:
        with TemporaryDirectory() as d:
            correction_store = self._make_store(d)
            preference_store = PreferenceStore(base_dir=str(Path(d) / "preferences"))
            delta_fingerprint = self._record_confirmed_pattern(correction_store, count=3)

            payload = _CorrectionSummaryService(
                correction_store,
                preference_store,
            ).promote_correction_pattern({"delta_fingerprint": delta_fingerprint})

            self.assertIn("is_highly_reliable", payload)
            self.assertIs(payload["is_highly_reliable"], True)

    def test_promote_pattern_reports_highly_reliable_false_below_threshold(self) -> None:
        with TemporaryDirectory() as d:
            correction_store = self._make_store(d)
            preference_store = PreferenceStore(base_dir=str(Path(d) / "preferences"))
            delta_fingerprint = self._record_confirmed_pattern(correction_store, count=2)

            payload = _CorrectionSummaryService(
                correction_store,
                preference_store,
            ).promote_correction_pattern({"delta_fingerprint": delta_fingerprint})

            self.assertIn("is_highly_reliable", payload)
            self.assertIs(payload["is_highly_reliable"], False)


if __name__ == "__main__":
    unittest.main()
