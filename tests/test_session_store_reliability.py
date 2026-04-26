"""Focused reliability accounting tests for SessionStore audit summary."""

from __future__ import annotations

from tempfile import TemporaryDirectory
import unittest

from storage.session_store import SessionStore


class SessionStoreReliabilityTest(unittest.TestCase):
    def test_feedback_labels_update_per_preference_corrected_count(self) -> None:
        with TemporaryDirectory() as base_dir:
            store = SessionStore(base_dir=base_dir)
            data = store.get_session("reliability-feedback")
            data["messages"].extend(
                [
                    {
                        "message_id": "msg-incorrect",
                        "role": "assistant",
                        "artifact_kind": "grounded_brief",
                        "applied_preference_ids": ["pref-incorrect"],
                        "feedback": {"label": "incorrect"},
                        "text": "response with incorrect preference",
                    },
                    {
                        "message_id": "msg-unclear",
                        "role": "assistant",
                        "artifact_kind": "grounded_brief",
                        "applied_preference_ids": ["pref-unclear"],
                        "feedback": {"label": "unclear"},
                        "text": "response with unclear preference",
                    },
                    {
                        "message_id": "msg-helpful",
                        "role": "assistant",
                        "artifact_kind": "grounded_brief",
                        "applied_preference_ids": ["pref-helpful"],
                        "feedback": {"label": "helpful"},
                        "text": "response with helpful preference",
                    },
                    {
                        "message_id": "msg-corrected",
                        "role": "assistant",
                        "artifact_id": "artifact-corrected",
                        "artifact_kind": "grounded_brief",
                        "applied_preference_ids": ["pref-corrected"],
                        "corrected_text": "corrected response",
                        "original_response_snapshot": {
                            "artifact_id": "artifact-corrected",
                            "artifact_kind": "grounded_brief",
                            "draft_text": "original response",
                            "source_paths": [],
                        },
                        "text": "original response",
                    },
                ]
            )
            store._save("reliability-feedback", data)

            summary = store.get_global_audit_summary()
            per = summary["per_preference_stats"]

            for pref_id in ["pref-incorrect", "pref-unclear"]:
                self.assertEqual(per[pref_id]["applied_count"], 1)
                self.assertEqual(per[pref_id]["corrected_count"], 1)

            self.assertEqual(per["pref-helpful"]["applied_count"], 1)
            self.assertEqual(per["pref-helpful"]["corrected_count"], 0)
            self.assertEqual(per["pref-corrected"]["applied_count"], 1)
            self.assertEqual(per["pref-corrected"]["corrected_count"], 1)
            self.assertEqual(summary["feedback_like_count"], 1)
            self.assertEqual(summary["feedback_dislike_count"], 2)
            self.assertEqual(summary["personalized_correction_count"], 1)


if __name__ == "__main__":
    unittest.main()
