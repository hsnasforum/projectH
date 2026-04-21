import unittest
from storage.sqlite_store import SQLiteSessionStore


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


if __name__ == "__main__":
    unittest.main()
