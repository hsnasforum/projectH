import unittest
from storage.sqlite_store import SQLiteDatabase, SQLitePreferenceStore, SQLiteSessionStore


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


if __name__ == "__main__":
    unittest.main()
