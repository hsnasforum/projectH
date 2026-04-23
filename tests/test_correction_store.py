"""Tests for storage.correction_store."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.contracts import CorrectionStatus
from storage.correction_store import CorrectionStore


class CorrectionStoreTest(unittest.TestCase):

    def _make_store(self, tmp_dir: str) -> CorrectionStore:
        return CorrectionStore(base_dir=str(Path(tmp_dir) / "corrections"))

    def _record_sample(self, store: CorrectionStore, **overrides) -> dict:
        defaults = dict(
            artifact_id="artifact-abc",
            session_id="session-1",
            source_message_id="msg-xyz",
            original_text="프로젝트H는 로컬 문서 비서입니다.",
            corrected_text="프로젝트H는 로컬 퍼스트 문서 비서 웹 MVP입니다.",
        )
        defaults.update(overrides)
        return store.record_correction(**defaults)

    def test_record_and_get(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)
            self.assertIsNotNone(record)
            self.assertTrue(record["correction_id"].startswith("correction-"))
            self.assertEqual(record["artifact_id"], "artifact-abc")
            self.assertEqual(record["status"], CorrectionStatus.RECORDED)

            fetched = store.get(record["correction_id"])
            self.assertEqual(fetched["correction_id"], record["correction_id"])

    def test_get_nonexistent_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self.assertIsNone(store.get("correction-nope"))

    def test_record_sets_timestamps(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)
            self.assertIn("created_at", record)
            self.assertEqual(record["first_seen_at"], record["last_seen_at"])

    def test_record_computes_delta_fingerprint(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)
            self.assertTrue(record["delta_fingerprint"].startswith("sha256:"))

    def test_record_computes_delta_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)
            summary = record["delta_summary"]
            self.assertIn("additions", summary)
            self.assertIn("removals", summary)
            self.assertIn("replacements", summary)

    def test_record_computes_similarity_score(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)
            self.assertGreater(record["similarity_score"], 0.0)
            self.assertLessEqual(record["similarity_score"], 1.0)

    def test_identical_texts_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            result = store.record_correction(
                artifact_id="a", session_id="s", source_message_id="m",
                original_text="same", corrected_text="same",
            )
            self.assertIsNone(result)

    def test_deduplicate_same_artifact_message_fingerprint(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            r1 = self._record_sample(store)
            r2 = self._record_sample(store)  # same artifact+message+text
            self.assertEqual(r1["correction_id"], r2["correction_id"])

    def test_confirm_correction(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)
            updated = store.confirm_correction(record["correction_id"])
            self.assertEqual(updated["status"], CorrectionStatus.CONFIRMED)
            self.assertIsNotNone(updated["confirmed_at"])

    def test_lifecycle_transitions(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)
            cid = record["correction_id"]

            r = store.confirm_correction(cid)
            self.assertEqual(r["status"], CorrectionStatus.CONFIRMED)
            r = store.promote_correction(cid)
            self.assertEqual(r["status"], CorrectionStatus.PROMOTED)
            r = store.activate_correction(cid)
            self.assertEqual(r["status"], CorrectionStatus.ACTIVE)
            r = store.stop_correction(cid)
            self.assertEqual(r["status"], CorrectionStatus.STOPPED)

    def test_transition_guard_rejects_out_of_order(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)
            cid = record["correction_id"]

            result = store.activate_correction(cid)

            self.assertIsNone(result)
            fetched = store.get(cid)
            self.assertEqual(fetched["status"], CorrectionStatus.RECORDED)

    def test_transition_guard_rejects_from_stopped(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)
            cid = record["correction_id"]

            store.confirm_correction(cid)
            store.promote_correction(cid)
            store.activate_correction(cid)
            store.stop_correction(cid)

            result = store.confirm_correction(cid)

            self.assertIsNone(result)
            fetched = store.get(cid)
            self.assertEqual(fetched["status"], CorrectionStatus.STOPPED)

    def test_recurrence_count_incremented(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            r1 = self._record_sample(store, artifact_id="a1", source_message_id="m1")
            self.assertEqual(r1["recurrence_count"], 1)

            r2 = self._record_sample(store, artifact_id="a2", source_message_id="m2")
            self.assertEqual(r2["recurrence_count"], 2)

            # r1 should also be updated
            r1_updated = store.get(r1["correction_id"])
            self.assertEqual(r1_updated["recurrence_count"], 2)

    def test_find_by_fingerprint(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            r1 = self._record_sample(store, artifact_id="a1", source_message_id="m1")
            self._record_sample(store, artifact_id="a2", source_message_id="m2")

            results = store.find_by_fingerprint(r1["delta_fingerprint"])
            self.assertEqual(len(results), 2)

    def test_find_by_session(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._record_sample(store, session_id="s1", artifact_id="a1", source_message_id="m1")
            self._record_sample(store, session_id="s2", artifact_id="a2", source_message_id="m2")

            s1 = store.find_by_session("s1")
            self.assertEqual(len(s1), 1)

    def test_find_recurring_patterns_single_not_returned(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._record_sample(store)
            patterns = store.find_recurring_patterns()
            self.assertEqual(len(patterns), 0)

    def test_find_recurring_patterns_two_matches_returned(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._record_sample(store, artifact_id="a1", source_message_id="m1")
            self._record_sample(store, artifact_id="a2", source_message_id="m2")
            patterns = store.find_recurring_patterns()
            self.assertEqual(len(patterns), 1)
            self.assertEqual(patterns[0]["recurrence_count"], 2)

    def test_find_recurring_patterns_scoped_to_session(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._record_sample(store, session_id="s1", artifact_id="a1", source_message_id="m1")
            self._record_sample(store, session_id="s2", artifact_id="a2", source_message_id="m2")

            # Same fingerprint but different sessions
            s1_patterns = store.find_recurring_patterns(session_id="s1")
            self.assertEqual(len(s1_patterns), 0)  # only 1 in s1

            # Cross-session
            all_patterns = store.find_recurring_patterns()
            self.assertEqual(len(all_patterns), 1)

    def test_list_recent(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._record_sample(store, artifact_id="a1", source_message_id="m1")
            self._record_sample(store, artifact_id="a2", source_message_id="m2",
                                original_text="다른 원본", corrected_text="다른 수정본")
            recent = store.list_recent(limit=1)
            self.assertEqual(len(recent), 1)

    def test_corrupt_file_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            path = store._path("correction-corrupt")
            path.write_text("not json", encoding="utf-8")
            self.assertIsNone(store.get("correction-corrupt"))
