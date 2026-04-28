"""Tests for GET /api/corrections/summary via AggregateHandlerMixin."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.handlers.aggregate import AggregateHandlerMixin
from storage.correction_store import CorrectionStore


class _CorrectionSummaryService(AggregateHandlerMixin):
    def __init__(self, store: CorrectionStore) -> None:
        self.correction_store = store


class CorrectionSummaryTest(unittest.TestCase):
    def _make_store(self, base_dir: str) -> CorrectionStore:
        return CorrectionStore(base_dir=str(Path(base_dir) / "corrections"))

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


if __name__ == "__main__":
    unittest.main()
