"""Tests for storage.correction_store."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.contracts import CorrectionStatus
from storage.correction_store import CorrectionStore
from storage.sqlite_store import SQLiteCorrectionStore, SQLiteDatabase


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

    def _activate_json_at(
        self, store: CorrectionStore, record: dict, activated_at: str
    ) -> dict:
        correction_id = record["correction_id"]
        store.confirm_correction(correction_id)
        store.promote_correction(correction_id)
        active = store.activate_correction(correction_id)
        active["activated_at"] = activated_at
        active["updated_at"] = activated_at
        store._path(correction_id).write_text(
            json.dumps(active, ensure_ascii=False),
            encoding="utf-8",
        )
        return active

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

    def test_invalid_record_is_filtered_from_scan_all(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            path = store._path("correction-invalid")
            path.write_text(
                json.dumps(
                    {
                        "correction_id": "correction-invalid",
                        "status": CorrectionStatus.RECORDED,
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(store._scan_all(), [])

    def test_valid_record_passes_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._record_sample(store)

            scanned = store._scan_all()

            self.assertEqual([item["correction_id"] for item in scanned], [record["correction_id"]])

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

    def test_list_filtered_by_query_matches_original_or_corrected_text(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            original_match = self._record_sample(
                store,
                artifact_id="a-query-original",
                source_message_id="m-query-original",
                original_text="needle original text",
                corrected_text="plain corrected text",
            )
            corrected_match = self._record_sample(
                store,
                artifact_id="a-query-corrected",
                source_message_id="m-query-corrected",
                original_text="plain original text",
                corrected_text="needle corrected text",
            )
            self._record_sample(
                store,
                artifact_id="a-query-miss",
                source_message_id="m-query-miss",
                original_text="other original text",
                corrected_text="other corrected text",
            )

            results = store.list_filtered(query="needle")

            self.assertEqual(
                {record["correction_id"] for record in results},
                {original_match["correction_id"], corrected_match["correction_id"]},
            )

    def test_list_filtered_by_status(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            recorded = self._record_sample(store, artifact_id="a-recorded-filter", source_message_id="m-recorded-filter")
            confirmed = self._record_sample(store, artifact_id="a-confirmed-filter", source_message_id="m-confirmed-filter")
            store.confirm_correction(confirmed["correction_id"])

            results = store.list_filtered(status=CorrectionStatus.CONFIRMED)

            self.assertEqual([record["correction_id"] for record in results], [confirmed["correction_id"]])
            self.assertNotIn(recorded["correction_id"], {record["correction_id"] for record in results})

    def test_list_filtered_applies_query_and_status(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            recorded_match = self._record_sample(
                store,
                artifact_id="a-recorded-query-filter",
                source_message_id="m-recorded-query-filter",
                original_text="needle recorded original",
                corrected_text="needle recorded corrected",
            )
            confirmed_match = self._record_sample(
                store,
                artifact_id="a-confirmed-query-filter",
                source_message_id="m-confirmed-query-filter",
                original_text="needle confirmed original",
                corrected_text="needle confirmed corrected",
            )
            store.confirm_correction(confirmed_match["correction_id"])

            results = store.list_filtered(query="needle", status=CorrectionStatus.CONFIRMED)

            self.assertEqual([record["correction_id"] for record in results], [confirmed_match["correction_id"]])
            self.assertNotIn(recorded_match["correction_id"], {record["correction_id"] for record in results})

    def test_list_filtered_empty_result(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._record_sample(store)

            results = store.list_filtered(query="missing needle")

            self.assertEqual(results, [])

    def test_confirm_by_fingerprint(self) -> None:
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
            fp = first["delta_fingerprint"]

            confirmed = store.confirm_by_fingerprint(fp)

            self.assertEqual(len(confirmed), 2)
            for r in confirmed:
                self.assertEqual(r["status"], "confirmed")

    def test_dismiss_by_fingerprint(self) -> None:
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
            fp = first["delta_fingerprint"]

            dismissed = store.dismiss_by_fingerprint(fp)

            self.assertEqual(len(dismissed), 2)
            for r in dismissed:
                self.assertEqual(r["status"], "stopped")

    def test_promote_by_fingerprint_promotes_only_confirmed(self) -> None:
        with TemporaryDirectory() as d:
            store = self._make_store(d)
            confirmed = store.record_correction(
                artifact_id="art-confirmed",
                session_id="s1",
                source_message_id="msg-confirmed",
                original_text="original text one",
                corrected_text="corrected text one",
            )
            recorded = store.record_correction(
                artifact_id="art-recorded",
                session_id="s2",
                source_message_id="msg-recorded",
                original_text="original text one",
                corrected_text="corrected text one",
            )
            stopped = store.record_correction(
                artifact_id="art-stopped",
                session_id="s3",
                source_message_id="msg-stopped",
                original_text="original text one",
                corrected_text="corrected text one",
            )
            self.assertIsNotNone(confirmed)
            self.assertIsNotNone(recorded)
            self.assertIsNotNone(stopped)
            fp = confirmed["delta_fingerprint"]
            store.confirm_correction(confirmed["correction_id"])
            store.stop_correction(stopped["correction_id"])

            promoted = store.promote_by_fingerprint(fp)

            self.assertEqual([r["correction_id"] for r in promoted], [confirmed["correction_id"]])
            self.assertEqual(promoted[0]["status"], CorrectionStatus.PROMOTED)
            self.assertEqual(store.get(recorded["correction_id"])["status"], CorrectionStatus.RECORDED)
            self.assertEqual(store.get(stopped["correction_id"])["status"], CorrectionStatus.STOPPED)

    def test_promote_by_fingerprint_missing_returns_empty(self) -> None:
        with TemporaryDirectory() as d:
            store = self._make_store(d)

            promoted = store.promote_by_fingerprint("sha256:missing")

            self.assertEqual(promoted, [])

    def test_list_incomplete_corrections_returns_only_non_terminal_records(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)

            recorded = self._record_sample(store, artifact_id="a-recorded", source_message_id="m-recorded")

            confirmed = self._record_sample(store, artifact_id="a-confirmed", source_message_id="m-confirmed")
            store.confirm_correction(confirmed["correction_id"])

            promoted = self._record_sample(store, artifact_id="a-promoted", source_message_id="m-promoted")
            store.confirm_correction(promoted["correction_id"])
            store.promote_correction(promoted["correction_id"])

            active = self._record_sample(store, artifact_id="a-active", source_message_id="m-active")
            store.confirm_correction(active["correction_id"])
            store.promote_correction(active["correction_id"])
            store.activate_correction(active["correction_id"])

            stopped = self._record_sample(store, artifact_id="a-stopped", source_message_id="m-stopped")
            store.confirm_correction(stopped["correction_id"])
            store.promote_correction(stopped["correction_id"])
            store.activate_correction(stopped["correction_id"])
            store.stop_correction(stopped["correction_id"])

            incomplete = store.list_incomplete_corrections()

            self.assertEqual(
                {record["correction_id"] for record in incomplete},
                {
                    recorded["correction_id"],
                    confirmed["correction_id"],
                    promoted["correction_id"],
                },
            )
            self.assertEqual(
                {record["status"] for record in incomplete},
                {
                    CorrectionStatus.RECORDED,
                    CorrectionStatus.CONFIRMED,
                    CorrectionStatus.PROMOTED,
                },
            )

    def test_find_adopted_corrections_returns_only_active_records(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            active = self._record_sample(store, artifact_id="a-active", source_message_id="m-active")
            self._activate_json_at(store, active, "2026-04-24T00:00:01+00:00")
            self._record_sample(store, artifact_id="a-recorded", source_message_id="m-recorded")

            adopted = store.find_adopted_corrections()

            self.assertEqual([record["correction_id"] for record in adopted], [active["correction_id"]])
            self.assertEqual({record["status"] for record in adopted}, {CorrectionStatus.ACTIVE})

    def test_find_adopted_corrections_sorts_by_activated_at(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            later = self._record_sample(store, artifact_id="a-later", source_message_id="m-later")
            earlier = self._record_sample(store, artifact_id="a-earlier", source_message_id="m-earlier")
            self._activate_json_at(store, later, "2026-04-24T00:00:02+00:00")
            self._activate_json_at(store, earlier, "2026-04-24T00:00:01+00:00")

            adopted = store.find_adopted_corrections()

            self.assertEqual(
                [record["correction_id"] for record in adopted],
                [earlier["correction_id"], later["correction_id"]],
            )

    def test_corrupt_file_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            path = store._path("correction-corrupt")
            path.write_text("not json", encoding="utf-8")
            self.assertIsNone(store.get("correction-corrupt"))

    def test_record_correction_returns_typed_fields(self) -> None:
        """record_correction이 CorrectionRecord 계약 필드를 포함한다."""
        from core.contracts import CorrectionRecord
        with TemporaryDirectory() as base_dir:
            store = CorrectionStore(base_dir=base_dir)
            record = store.record_correction(
                artifact_id="art-typed",
                session_id="sess-typed",
                source_message_id="msg-typed",
                original_text="original text for typing test",
                corrected_text="corrected text for typing test",
                applied_preference_ids=["fp-abc"],
            )
            assert record is not None
            typed_record: CorrectionRecord = record
            assert "correction_id" in typed_record
            assert "delta_fingerprint" in typed_record
            assert "status" in typed_record
            assert typed_record.get("applied_preference_ids") == ["fp-abc"]
            assert isinstance(typed_record, dict)


class SQLiteCorrectionStoreAdoptionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SQLiteDatabase(":memory:")
        self.store = SQLiteCorrectionStore(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def _record(self, *, artifact_id: str, source_message_id: str) -> dict:
        record = self.store.record_correction(
            artifact_id=artifact_id,
            session_id="session-1",
            source_message_id=source_message_id,
            original_text="alpha foo omega",
            corrected_text="alpha bar omega",
        )
        self.assertIsNotNone(record)
        return record

    def _activate_sqlite_at(self, record: dict, activated_at: str) -> dict:
        correction_id = record["correction_id"]
        self.store.confirm_correction(correction_id)
        self.store.promote_correction(correction_id)
        active = self.store.activate_correction(correction_id)
        active["activated_at"] = activated_at
        active["updated_at"] = activated_at
        self.db.execute(
            "UPDATE corrections SET data = ?, updated_at = ? WHERE correction_id = ?",
            (json.dumps(active, ensure_ascii=False), activated_at, correction_id),
        )
        self.db.commit()
        return active

    def test_find_adopted_corrections_returns_only_active_records(self) -> None:
        active = self._record(artifact_id="a-active", source_message_id="m-active")
        self._activate_sqlite_at(active, "2026-04-24T00:00:01+00:00")
        self._record(artifact_id="a-recorded", source_message_id="m-recorded")

        adopted = self.store.find_adopted_corrections()

        self.assertEqual([record["correction_id"] for record in adopted], [active["correction_id"]])
        self.assertEqual({record["status"] for record in adopted}, {CorrectionStatus.ACTIVE})

    def test_find_adopted_corrections_sorts_by_activated_at(self) -> None:
        later = self._record(artifact_id="a-later", source_message_id="m-later")
        earlier = self._record(artifact_id="a-earlier", source_message_id="m-earlier")
        self._activate_sqlite_at(later, "2026-04-24T00:00:02+00:00")
        self._activate_sqlite_at(earlier, "2026-04-24T00:00:01+00:00")

        adopted = self.store.find_adopted_corrections()

        self.assertEqual(
            [record["correction_id"] for record in adopted],
            [earlier["correction_id"], later["correction_id"]],
        )

    def test_sqlite_record_correction_returns_typed_fields(self) -> None:
        """SQLiteCorrectionStore.record_correction이 CorrectionRecord 계약 필드를 포함한다."""
        from core.contracts import CorrectionRecord

        record = self.store.record_correction(
            artifact_id="art-sqlite-typed",
            session_id="sess-sqlite-typed",
            source_message_id="msg-sqlite-typed",
            original_text="sqlite original text for typing",
            corrected_text="sqlite corrected text for typing",
            applied_preference_ids=["fp-sqlite"],
        )

        assert record is not None
        typed_record: CorrectionRecord = record
        assert "correction_id" in typed_record
        assert "delta_fingerprint" in typed_record
        assert "status" in typed_record
        assert typed_record.get("applied_preference_ids") == ["fp-sqlite"]
        assert isinstance(typed_record, dict)
