import json
import os
import tempfile
import unittest
from time import sleep

from core.contracts import CorrectionStatus, PreferenceStatus
from storage.sqlite_store import (
    SQLiteCorrectionStore,
    SQLiteDatabase,
    SQLitePreferenceStore,
    SQLiteSessionStore,
    migrate_json_to_sqlite,
)


class TestSQLiteSessionStoreAdoptionList(unittest.TestCase):
    """Pins the public-method adoption list for SQLiteSessionStore.

    If any method is later removed or renamed, this test will catch it.
    Methods are delegated via class-attribute assignment from SessionStore.
    """

    REQUIRED_METHODS = [
        "get_session",
        "list_sessions",
        "delete_session",
        "delete_all_sessions",
        "append_message",
        "update_last_message",
        "update_message",
        "add_pending_approval",
        "get_pending_approval",
        "pop_pending_approval",
        "set_active_context",
        "get_active_context",
        "set_permissions",
        "get_permissions",
        "find_artifact_source_message",
        "record_correction_for_message",
        "record_corrected_outcome_for_artifact",
        "record_rejected_content_verdict_for_message",
        "record_content_reason_note_for_message",
        "record_candidate_confirmation_for_message",
        "record_candidate_review_for_message",
        "build_session_local_memory_signal",
    ]

    def test_adoption_list_all_methods_accessible(self) -> None:
        for name in self.REQUIRED_METHODS:
            with self.subTest(method=name):
                self.assertTrue(
                    hasattr(SQLiteSessionStore, name),
                    f"SQLiteSessionStore is missing required method: {name}",
                )


class TestMigrationIntegrity(unittest.TestCase):
    def test_migrate_corrections_insert_or_ignore_idempotent(self) -> None:
        """migrate_json_to_sqlite can be run twice safely via INSERT OR IGNORE."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            corrections_dir = os.path.join(tmp, "corrections")
            os.makedirs(corrections_dir)
            correction = {
                "correction_id": "correction-test001",
                "artifact_id": "art1",
                "session_id": "sess1",
                "delta_fingerprint": "sha256:aaaa",
                "status": "recorded",
                "created_at": "2026-04-23T00:00:00+00:00",
                "updated_at": "2026-04-23T00:00:00+00:00",
            }
            with open(
                os.path.join(corrections_dir, "correction-test001.json"),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(correction, f)

            counts1 = migrate_json_to_sqlite(
                corrections_dir=corrections_dir,
                db_path=db_path,
                sessions_dir=os.path.join(tmp, "sessions"),
                artifacts_dir=os.path.join(tmp, "artifacts"),
                preferences_dir=os.path.join(tmp, "preferences"),
            )
            self.assertEqual(counts1.get("corrections"), 1)

            counts2 = migrate_json_to_sqlite(
                corrections_dir=corrections_dir,
                db_path=db_path,
                sessions_dir=os.path.join(tmp, "sessions"),
                artifacts_dir=os.path.join(tmp, "artifacts"),
                preferences_dir=os.path.join(tmp, "preferences"),
            )
            self.assertEqual(counts2.get("corrections"), 0)


class TestSQLitePreferenceStoreAutoActivation(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SQLiteDatabase(":memory:")
        self.store = SQLitePreferenceStore(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def _record(
        self,
        *,
        delta_fingerprint: str = "fingerprint-auto-activation",
        candidate_id: str,
    ) -> dict:
        return self.store.record_reviewed_candidate_preference(
            delta_fingerprint=delta_fingerprint,
            candidate_family="correction_rewrite",
            description="Prefer concise answers",
            source_refs={"candidate_id": candidate_id, "session_id": candidate_id},
        )

    def test_sqlite_auto_activation_keeps_candidate_below_threshold(self) -> None:
        self._record(candidate_id="candidate-0")
        self._record(candidate_id="candidate-1")
        record = self._record(candidate_id="candidate-2")

        self.assertEqual(record["cross_session_count"], 2)
        self.assertEqual(record["status"], "candidate")
        stored = self.store.get(record["preference_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["status"], "candidate")
        self.assertIsNone(stored["activated_at"])

    def test_sqlite_auto_activation_promotes_candidate_at_threshold(self) -> None:
        self._record(candidate_id="candidate-0")
        self._record(candidate_id="candidate-1")
        self._record(candidate_id="candidate-2")
        record = self._record(candidate_id="candidate-3")

        self.assertEqual(record["cross_session_count"], 3)
        self.assertEqual(record["status"], "active")
        self.assertIsNotNone(record["activated_at"])
        stored = self.store.get(record["preference_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["status"], "active")
        self.assertIsNotNone(stored["activated_at"])

    def test_sqlite_auto_activation_leaves_active_unchanged(self) -> None:
        record = self._record(candidate_id="candidate-0")
        active_record = self.store.activate_preference(record["preference_id"])
        self.assertIsNotNone(active_record)
        activated_at = active_record["activated_at"]

        updated = self._record(candidate_id="candidate-1")

        self.assertEqual(updated["status"], "active")
        self.assertEqual(updated["activated_at"], activated_at)
        stored = self.store.get(record["preference_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["status"], "active")
        self.assertEqual(stored["activated_at"], activated_at)

    def test_sqlite_auto_activation_leaves_rejected_unchanged(self) -> None:
        record = self._record(candidate_id="candidate-0")
        rejected_record = self.store.reject_preference(record["preference_id"])
        self.assertIsNotNone(rejected_record)

        updated = self._record(candidate_id="candidate-1")

        self.assertEqual(updated["status"], "rejected")
        stored = self.store.get(record["preference_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["status"], "rejected")
        self.assertIsNone(stored["activated_at"])

    def test_sqlite_record_reviewed_candidate_stores_avg_similarity_score(self) -> None:
        record = self.store.record_reviewed_candidate_preference(
            delta_fingerprint="fingerprint-avg-similarity",
            candidate_family="correction_rewrite",
            description="Prefer concise answers",
            source_refs={"candidate_id": "candidate-quality"},
            avg_similarity_score=0.25,
        )

        self.assertEqual(record["avg_similarity_score"], 0.25)
        stored = self.store.get(record["preference_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["avg_similarity_score"], 0.25)

    def test_sqlite_record_reviewed_candidate_stores_snippets(self) -> None:
        record = self.store.record_reviewed_candidate_preference(
            delta_fingerprint="fingerprint-snippets",
            candidate_family="correction_rewrite",
            description="Prefer concise answers",
            source_refs={"candidate_id": "candidate-snippet"},
            original_snippet="hello",
            corrected_snippet="world",
        )

        self.assertEqual(record["original_snippet"], "hello")
        self.assertEqual(record["corrected_snippet"], "world")
        stored = self.store.get(record["preference_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["original_snippet"], "hello")
        self.assertEqual(stored["corrected_snippet"], "world")

    def test_sqlite_update_description_changes_field(self) -> None:
        created = self._record(candidate_id="candidate-update-description")
        sleep(0.001)

        updated = self.store.update_description(created["preference_id"], "Prefer structured answers")

        self.assertIsNotNone(updated)
        self.assertEqual(updated["description"], "Prefer structured answers")
        self.assertGreater(updated["updated_at"], created["created_at"])
        stored = self.store.get(created["preference_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["description"], "Prefer structured answers")

    def test_sqlite_record_reviewed_candidate_update_preserves_score_when_none_passed(self) -> None:
        created = self.store.record_reviewed_candidate_preference(
            delta_fingerprint="fingerprint-avg-similarity-preserve",
            candidate_family="correction_rewrite",
            description="Prefer concise answers",
            source_refs={"candidate_id": "candidate-quality-a"},
            avg_similarity_score=0.3,
        )

        updated = self.store.record_reviewed_candidate_preference(
            delta_fingerprint="fingerprint-avg-similarity-preserve",
            candidate_family="correction_rewrite",
            description="Prefer concise answers",
            source_refs={"candidate_id": "candidate-quality-b"},
            avg_similarity_score=None,
        )

        self.assertEqual(updated["preference_id"], created["preference_id"])
        self.assertEqual(updated["avg_similarity_score"], 0.3)
        stored = self.store.get(created["preference_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["avg_similarity_score"], 0.3)

    def test_sqlite_record_reviewed_candidate_rejected_status(self) -> None:
        result = self.store.record_reviewed_candidate_preference(
            delta_fingerprint="sha256:test-sqlite-reject",
            candidate_family="correction_rewrite",
            description="SQLite 거절 테스트",
            source_refs={
                "candidate_id": "global:sha256:test-sqlite-reject",
                "source_message_id": "global",
            },
            status=PreferenceStatus.REJECTED,
        )

        self.assertEqual(result["status"], PreferenceStatus.REJECTED)
        self.assertIsNotNone(result["rejected_at"])
        fetched = self.store.get(result["preference_id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["status"], PreferenceStatus.REJECTED)


class TestSQLiteCorrectionStore(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SQLiteDatabase(":memory:")
        self.store = SQLiteCorrectionStore(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def _record(
        self,
        *,
        artifact_id: str = "artifact-1",
        session_id: str = "session-1",
        source_message_id: str = "message-1",
        original_text: str = "alpha foo omega",
        corrected_text: str = "alpha bar omega",
    ) -> dict:
        record = self.store.record_correction(
            artifact_id=artifact_id,
            session_id=session_id,
            source_message_id=source_message_id,
            original_text=original_text,
            corrected_text=corrected_text,
        )
        self.assertIsNotNone(record)
        return record

    def _assert_lifecycle_transition(
        self,
        method_name: str,
        expected_status: str,
        timestamp_field: str,
        prerequisite_methods: tuple[str, ...] = (),
    ) -> None:
        record = self._record(
            artifact_id=f"artifact-{method_name}",
            session_id=f"session-{method_name}",
            source_message_id=f"message-{method_name}",
        )
        for prerequisite in prerequisite_methods:
            updated = getattr(self.store, prerequisite)(record["correction_id"])
            self.assertIsNotNone(updated)
        sleep(0.001)

        updated = getattr(self.store, method_name)(record["correction_id"])

        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], expected_status)
        self.assertIsNotNone(updated[timestamp_field])
        self.assertGreater(updated["updated_at"], record["updated_at"])
        stored = self.store.get(record["correction_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["status"], expected_status)
        self.assertEqual(stored[timestamp_field], updated[timestamp_field])
        raw_row = self.db.fetchone(
            "SELECT status, data FROM corrections WHERE correction_id = ?",
            (record["correction_id"],),
        )
        self.assertIsNotNone(raw_row)
        self.assertEqual(raw_row["status"], expected_status)
        raw_data = json.loads(raw_row["data"])
        self.assertEqual(raw_data["status"], expected_status)
        self.assertEqual(raw_data[timestamp_field], updated[timestamp_field])

    def test_record_returns_none_for_identical_texts(self) -> None:
        record = self.store.record_correction(
            artifact_id="artifact-same",
            session_id="session-same",
            source_message_id="message-same",
            original_text="same text",
            corrected_text="same text",
        )

        self.assertIsNone(record)

    def test_record_creates_correction_with_fields(self) -> None:
        record = self._record()

        self.assertTrue(record["correction_id"].startswith("correction-"))
        self.assertTrue(record["delta_fingerprint"].startswith("sha256:"))
        self.assertIsInstance(record["similarity_score"], float)
        self.assertEqual(record["original_text"], "alpha foo omega")
        self.assertEqual(record["corrected_text"], "alpha bar omega")

    def test_sqlite_confirm_correction_updates_status(self) -> None:
        self._assert_lifecycle_transition(
            "confirm_correction",
            "confirmed",
            "confirmed_at",
        )

    def test_sqlite_promote_correction_updates_status(self) -> None:
        self._assert_lifecycle_transition(
            "promote_correction",
            "promoted",
            "promoted_at",
            ("confirm_correction",),
        )

    def test_sqlite_activate_correction_updates_status(self) -> None:
        self._assert_lifecycle_transition(
            "activate_correction",
            "active",
            "activated_at",
            ("confirm_correction", "promote_correction"),
        )

    def test_sqlite_stop_correction_updates_status(self) -> None:
        self._assert_lifecycle_transition(
            "stop_correction",
            "stopped",
            "stopped_at",
            ("confirm_correction", "promote_correction", "activate_correction"),
        )

    def test_sqlite_transition_returns_none_for_missing_id(self) -> None:
        self.assertIsNone(
            self.store._transition("correction-missing", "confirmed", "confirmed_at")
        )

    def test_transition_guard_rejects_out_of_order(self) -> None:
        correction = self._record(
            artifact_id="artifact-guard-1",
            session_id="session-guard-1",
            source_message_id="message-guard-1",
        )

        result = self.store.activate_correction(correction["correction_id"])

        self.assertIsNone(result)
        row = self.store.get(correction["correction_id"])
        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "recorded")

    def test_transition_guard_rejects_from_stopped(self) -> None:
        correction = self._record(
            artifact_id="artifact-guard-2",
            session_id="session-guard-2",
            source_message_id="message-guard-2",
        )
        correction_id = correction["correction_id"]
        self.assertIsNotNone(self.store.confirm_correction(correction_id))
        self.assertIsNotNone(self.store.promote_correction(correction_id))
        self.assertIsNotNone(self.store.activate_correction(correction_id))
        self.assertIsNotNone(self.store.stop_correction(correction_id))

        result = self.store.confirm_correction(correction_id)

        self.assertIsNone(result)
        row = self.store.get(correction_id)
        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "stopped")

    def test_transition_guard_allows_valid_chain(self) -> None:
        correction = self._record(
            artifact_id="artifact-guard-3",
            session_id="session-guard-3",
            source_message_id="message-guard-3",
        )
        correction_id = correction["correction_id"]

        confirmed = self.store.confirm_correction(correction_id)
        self.assertIsNotNone(confirmed)
        self.assertEqual(confirmed["status"], "confirmed")

        promoted = self.store.promote_correction(correction_id)
        self.assertIsNotNone(promoted)
        self.assertEqual(promoted["status"], "promoted")

        active = self.store.activate_correction(correction_id)
        self.assertIsNotNone(active)
        self.assertEqual(active["status"], "active")

        stopped = self.store.stop_correction(correction_id)
        self.assertIsNotNone(stopped)
        self.assertEqual(stopped["status"], "stopped")

    def test_record_idempotent_for_same_artifact_source_fingerprint(self) -> None:
        first = self._record(
            artifact_id="artifact-idempotent",
            session_id="session-idempotent",
            source_message_id="message-idempotent",
            original_text="alpha foo omega",
            corrected_text="alpha bar omega",
        )
        second = self._record(
            artifact_id="artifact-idempotent",
            session_id="session-idempotent",
            source_message_id="message-idempotent",
            original_text="beta foo omega",
            corrected_text="beta bar omega",
        )

        self.assertEqual(second["correction_id"], first["correction_id"])

    def test_find_by_fingerprint(self) -> None:
        first = self._record(
            artifact_id="artifact-fingerprint-1",
            source_message_id="message-fingerprint-1",
            original_text="alpha foo omega",
            corrected_text="alpha bar omega",
        )
        second = self._record(
            artifact_id="artifact-fingerprint-2",
            source_message_id="message-fingerprint-2",
            original_text="beta foo omega",
            corrected_text="beta bar omega",
        )

        matches = self.store.find_by_fingerprint(first["delta_fingerprint"])

        self.assertEqual(len(matches), 2)
        self.assertEqual(
            {match["correction_id"] for match in matches},
            {first["correction_id"], second["correction_id"]},
        )

    def test_find_by_artifact(self) -> None:
        first = self._record(
            artifact_id="artifact-target",
            source_message_id="message-artifact-1",
        )
        self._record(
            artifact_id="artifact-other",
            source_message_id="message-artifact-2",
            original_text="beta foo omega",
            corrected_text="beta bar omega",
        )

        matches = self.store.find_by_artifact("artifact-target")

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["correction_id"], first["correction_id"])

    def test_find_by_session(self) -> None:
        first = self._record(
            session_id="session-target",
            artifact_id="artifact-session-1",
            source_message_id="message-session-1",
        )
        self._record(
            session_id="session-other",
            artifact_id="artifact-session-2",
            source_message_id="message-session-2",
            original_text="beta foo omega",
            corrected_text="beta bar omega",
        )

        matches = self.store.find_by_session("session-target")

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["correction_id"], first["correction_id"])

    def test_list_recent(self) -> None:
        self._record(
            artifact_id="artifact-recent-1",
            source_message_id="message-recent-1",
            original_text="alpha foo omega",
            corrected_text="alpha bar omega",
        )
        self._record(
            artifact_id="artifact-recent-2",
            source_message_id="message-recent-2",
            original_text="beta foo omega",
            corrected_text="beta bar omega",
        )
        self._record(
            artifact_id="artifact-recent-3",
            source_message_id="message-recent-3",
            original_text="gamma foo omega",
            corrected_text="gamma bar omega",
        )

        matches = self.store.list_recent(2)

        self.assertEqual(len(matches), 2)

    def test_list_incomplete_corrections_returns_only_non_terminal_records(self) -> None:
        recorded = self._record(
            artifact_id="artifact-incomplete-recorded",
            source_message_id="message-incomplete-recorded",
        )

        confirmed = self._record(
            artifact_id="artifact-incomplete-confirmed",
            source_message_id="message-incomplete-confirmed",
        )
        self.assertIsNotNone(self.store.confirm_correction(confirmed["correction_id"]))

        promoted = self._record(
            artifact_id="artifact-incomplete-promoted",
            source_message_id="message-incomplete-promoted",
        )
        self.assertIsNotNone(self.store.confirm_correction(promoted["correction_id"]))
        self.assertIsNotNone(self.store.promote_correction(promoted["correction_id"]))

        active = self._record(
            artifact_id="artifact-incomplete-active",
            source_message_id="message-incomplete-active",
        )
        self.assertIsNotNone(self.store.confirm_correction(active["correction_id"]))
        self.assertIsNotNone(self.store.promote_correction(active["correction_id"]))
        self.assertIsNotNone(self.store.activate_correction(active["correction_id"]))

        stopped = self._record(
            artifact_id="artifact-incomplete-stopped",
            source_message_id="message-incomplete-stopped",
        )
        self.assertIsNotNone(self.store.confirm_correction(stopped["correction_id"]))
        self.assertIsNotNone(self.store.promote_correction(stopped["correction_id"]))
        self.assertIsNotNone(self.store.activate_correction(stopped["correction_id"]))
        self.assertIsNotNone(self.store.stop_correction(stopped["correction_id"]))

        incomplete = self.store.list_incomplete_corrections()

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
            {"recorded", "confirmed", "promoted"},
        )

    def test_find_recurring_patterns_detects_cross_occurrence(self) -> None:
        self._record(
            artifact_id="art1",
            session_id="sess1",
            source_message_id="msg1",
            original_text="hello world",
            corrected_text="hello there",
        )
        self._record(
            artifact_id="art2",
            session_id="sess2",
            source_message_id="msg2",
            original_text="hello world",
            corrected_text="hello there",
        )
        self._record(
            artifact_id="art3",
            session_id="sess3",
            source_message_id="msg3",
            original_text="unique text here",
            corrected_text="unique text changed",
        )

        patterns = self.store.find_recurring_patterns()

        recur_fps = {pattern["delta_fingerprint"] for pattern in patterns}
        self.assertEqual(len(recur_fps), 1)
        self.assertEqual(patterns[0]["recurrence_count"], 2)
        self.assertEqual(len(patterns[0]["corrections"]), 2)

    def test_find_recurring_patterns_session_filter(self) -> None:
        self._record(
            artifact_id="art1",
            session_id="s1",
            source_message_id="m1",
            original_text="hello world",
            corrected_text="hello there",
        )
        self._record(
            artifact_id="art1",
            session_id="s1",
            source_message_id="m1b",
            original_text="hello world",
            corrected_text="hello there",
        )
        self._record(
            artifact_id="art2",
            session_id="s2",
            source_message_id="m2",
            original_text="hello world",
            corrected_text="hello there",
        )

        s1_patterns = self.store.find_recurring_patterns(session_id="s1")
        s2_patterns = self.store.find_recurring_patterns(session_id="s2")

        self.assertEqual(len(s1_patterns), 1)
        self.assertEqual(s1_patterns[0]["recurrence_count"], 2)
        self.assertEqual(len(s2_patterns), 0)

    def test_find_recurring_patterns_requires_distinct_sessions(self) -> None:
        self._record(
            artifact_id="art1",
            session_id="same-session",
            source_message_id="m1",
            original_text="hello world",
            corrected_text="hello there",
        )
        self._record(
            artifact_id="art2",
            session_id="same-session",
            source_message_id="m2",
            original_text="hello world",
            corrected_text="hello there",
        )

        global_patterns = self.store.find_recurring_patterns()
        session_patterns = self.store.find_recurring_patterns(session_id="same-session")

        self.assertEqual(len(global_patterns), 0)
        self.assertEqual(len(session_patterns), 1)

    def test_scan_all_returns_all_records(self) -> None:
        self._record(artifact_id="art1", session_id="s1", source_message_id="msg1")
        self._record(
            artifact_id="art2",
            session_id="s2",
            source_message_id="msg2",
            original_text="beta foo omega",
            corrected_text="beta bar omega",
        )
        result = self.store._scan_all()
        self.assertEqual(len(result), 2)
        statuses = {r["status"] for r in result}
        self.assertEqual(statuses, {"recorded"})

    def test_list_filtered_by_query_matches_original_or_corrected_text(self) -> None:
        original_match = self._record(
            artifact_id="artifact-query-original",
            source_message_id="message-query-original",
            original_text="needle original text",
            corrected_text="plain corrected text",
        )
        corrected_match = self._record(
            artifact_id="artifact-query-corrected",
            source_message_id="message-query-corrected",
            original_text="plain original text",
            corrected_text="needle corrected text",
        )
        self._record(
            artifact_id="artifact-query-miss",
            source_message_id="message-query-miss",
            original_text="other original text",
            corrected_text="other corrected text",
        )

        results = self.store.list_filtered(query="needle")

        self.assertEqual(
            {record["correction_id"] for record in results},
            {original_match["correction_id"], corrected_match["correction_id"]},
        )

    def test_list_filtered_by_status(self) -> None:
        recorded = self._record(
            artifact_id="artifact-recorded-filter",
            source_message_id="message-recorded-filter",
        )
        confirmed = self._record(
            artifact_id="artifact-confirmed-filter",
            source_message_id="message-confirmed-filter",
        )
        self.assertIsNotNone(self.store.confirm_correction(confirmed["correction_id"]))

        results = self.store.list_filtered(status=CorrectionStatus.CONFIRMED)

        self.assertEqual([record["correction_id"] for record in results], [confirmed["correction_id"]])
        self.assertNotIn(recorded["correction_id"], {record["correction_id"] for record in results})

    def test_list_filtered_applies_query_and_status(self) -> None:
        recorded_match = self._record(
            artifact_id="artifact-recorded-query-filter",
            source_message_id="message-recorded-query-filter",
            original_text="needle recorded original",
            corrected_text="needle recorded corrected",
        )
        confirmed_match = self._record(
            artifact_id="artifact-confirmed-query-filter",
            source_message_id="message-confirmed-query-filter",
            original_text="needle confirmed original",
            corrected_text="needle confirmed corrected",
        )
        self.assertIsNotNone(self.store.confirm_correction(confirmed_match["correction_id"]))

        results = self.store.list_filtered(query="needle", status=CorrectionStatus.CONFIRMED)

        self.assertEqual([record["correction_id"] for record in results], [confirmed_match["correction_id"]])
        self.assertNotIn(recorded_match["correction_id"], {record["correction_id"] for record in results})

    def test_list_filtered_empty_result(self) -> None:
        self._record()

        results = self.store.list_filtered(query="missing needle")

        self.assertEqual(results, [])

    def test_confirm_by_fingerprint_batch(self) -> None:
        first = self._record(artifact_id="art1", session_id="s1", source_message_id="msg1")
        second = self._record(artifact_id="art2", session_id="s2", source_message_id="msg2")
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        fp = first["delta_fingerprint"]
        self.assertEqual(fp, second["delta_fingerprint"])

        confirmed = self.store.confirm_by_fingerprint(fp)

        self.assertEqual(len(confirmed), 2)
        for r in confirmed:
            self.assertEqual(r["status"], "confirmed")

    def test_dismiss_by_fingerprint_batch(self) -> None:
        first = self._record(artifact_id="art1", session_id="s1", source_message_id="msg1")
        second = self._record(artifact_id="art2", session_id="s2", source_message_id="msg2")
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        fp = first["delta_fingerprint"]
        self.assertEqual(fp, second["delta_fingerprint"])

        dismissed = self.store.dismiss_by_fingerprint(fp)

        self.assertEqual(len(dismissed), 2)
        for r in dismissed:
            self.assertEqual(r["status"], "stopped")

    def test_promote_by_fingerprint_promotes_only_confirmed(self) -> None:
        confirmed = self._record(
            artifact_id="art-promote-confirmed",
            session_id="s1",
            source_message_id="msg-promote-confirmed",
        )
        recorded = self._record(
            artifact_id="art-promote-recorded",
            session_id="s2",
            source_message_id="msg-promote-recorded",
        )
        stopped = self._record(
            artifact_id="art-promote-stopped",
            session_id="s3",
            source_message_id="msg-promote-stopped",
        )
        fp = confirmed["delta_fingerprint"]
        self.assertEqual(fp, recorded["delta_fingerprint"])
        self.assertEqual(fp, stopped["delta_fingerprint"])
        self.assertIsNotNone(self.store.confirm_correction(confirmed["correction_id"]))
        self.assertIsNotNone(self.store.stop_correction(stopped["correction_id"]))

        promoted = self.store.promote_by_fingerprint(fp)

        self.assertEqual([r["correction_id"] for r in promoted], [confirmed["correction_id"]])
        self.assertEqual(promoted[0]["status"], CorrectionStatus.PROMOTED)
        stored_recorded = self.store.get(recorded["correction_id"])
        stored_stopped = self.store.get(stopped["correction_id"])
        self.assertIsNotNone(stored_recorded)
        self.assertIsNotNone(stored_stopped)
        self.assertEqual(stored_recorded["status"], CorrectionStatus.RECORDED)
        self.assertEqual(stored_stopped["status"], CorrectionStatus.STOPPED)

    def test_promote_by_fingerprint_missing_returns_empty(self) -> None:
        self.assertEqual(self.store.promote_by_fingerprint("sha256:missing"), [])


if __name__ == "__main__":
    unittest.main()
