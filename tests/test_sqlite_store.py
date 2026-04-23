import unittest
from storage.sqlite_store import (
    SQLiteCorrectionStore,
    SQLiteDatabase,
    SQLitePreferenceStore,
    SQLiteSessionStore,
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


if __name__ == "__main__":
    unittest.main()
