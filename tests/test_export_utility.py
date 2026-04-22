import json
import unittest
from tempfile import TemporaryDirectory

from storage.session_store import SessionStore


class TestStreamTracePairs(unittest.TestCase):
    def _make_store_with_pair(
        self, base_dir: str, session_id: str, prompt: str, completion: str
    ) -> SessionStore:
        store = SessionStore(base_dir=base_dir)
        data = store.get_session(session_id)
        data["messages"].append({
            "message_id": "msg-1",
            "role": "assistant",
            "artifact_kind": "grounded_brief",
            "artifact_id": "art-1",
            "text": prompt,
            "corrected_text": completion,
            "original_response_snapshot": {
                "artifact_id": "art-1",
                "artifact_kind": "grounded_brief",
                "draft_text": prompt,
            },
        })
        store._save(session_id, data)
        return store

    def test_yields_correct_prompt_and_completion(self) -> None:
        with TemporaryDirectory() as base_dir:
            store = self._make_store_with_pair(
                base_dir, "sess-1", "original text", "corrected text"
            )
            pairs = list(store.stream_trace_pairs())
            self.assertEqual(len(pairs), 1)
            self.assertEqual(pairs[0]["prompt"], "original text")
            self.assertEqual(pairs[0]["completion"], "corrected text")
            self.assertEqual(pairs[0]["session_id"], "sess-1")
            self.assertEqual(pairs[0]["message_id"], "msg-1")

    def test_empty_store_yields_nothing(self) -> None:
        with TemporaryDirectory() as base_dir:
            store = SessionStore(base_dir=base_dir)
            self.assertEqual(list(store.stream_trace_pairs()), [])

    def test_newlines_preserved_in_prompt_and_completion(self) -> None:
        with TemporaryDirectory() as base_dir:
            store = self._make_store_with_pair(
                base_dir, "sess-2", "line1\nline2", "fixed\nversion"
            )
            pairs = list(store.stream_trace_pairs())
            self.assertEqual(len(pairs), 1)
            roundtripped = json.loads(json.dumps(pairs[0], ensure_ascii=False))
            self.assertIn("\n", roundtripped["prompt"])
            self.assertIn("\n", roundtripped["completion"])

    def test_skips_messages_without_corrected_text(self) -> None:
        with TemporaryDirectory() as base_dir:
            store = SessionStore(base_dir=base_dir)
            data = store.get_session("sess-3")
            data["messages"].append({
                "message_id": "msg-1",
                "role": "assistant",
                "artifact_kind": "grounded_brief",
                "artifact_id": "art-1",
                "text": "original",
                "original_response_snapshot": {
                    "artifact_id": "art-1",
                    "artifact_kind": "grounded_brief",
                    "draft_text": "original",
                },
            })
            store._save("sess-3", data)
            self.assertEqual(list(store.stream_trace_pairs()), [])

    def test_quality_score_in_range_is_high_quality(self) -> None:
        from core.delta_analysis import compute_correction_delta
        from scripts.export_traces import _is_high_quality
        # Moderate rewrite: scores well within [0.20, 0.98]
        delta = compute_correction_delta(
            "The assistant summarized the document incorrectly.",
            "The assistant provided an accurate summary of the document.",
        )
        self.assertIsNotNone(delta)
        self.assertTrue(_is_high_quality(delta.similarity_score))

    def test_trivial_fix_not_high_quality(self) -> None:
        from core.delta_analysis import compute_correction_delta
        from scripts.export_traces import _is_high_quality
        # Single char change in a long string -> ratio > 0.98
        original = "a" * 200 + "x"
        corrected = "a" * 200 + "y"
        delta = compute_correction_delta(original, corrected)
        self.assertIsNotNone(delta)
        self.assertFalse(_is_high_quality(delta.similarity_score))

    def test_complete_rewrite_not_high_quality(self) -> None:
        from core.delta_analysis import compute_correction_delta
        from scripts.export_traces import _is_high_quality
        # No shared characters -> ratio near 0
        delta = compute_correction_delta("aaaaaaaaaaaa", "bbbbbbbbbbbb")
        self.assertIsNotNone(delta)
        self.assertFalse(_is_high_quality(delta.similarity_score))

    def test_identical_texts_returns_none_delta(self) -> None:
        from core.delta_analysis import compute_correction_delta
        delta = compute_correction_delta("same text", "same text")
        self.assertIsNone(delta)

    def test_grounded_brief_range_is_high_quality(self) -> None:
        from scripts.export_traces import _is_high_quality
        # Grounded-brief rewrites empirically score 0.067-0.090; must be accepted
        self.assertTrue(_is_high_quality(0.075))
        self.assertTrue(_is_high_quality(0.067))
        self.assertTrue(_is_high_quality(0.090))
        # Below new floor is not high quality
        self.assertFalse(_is_high_quality(0.03))


if __name__ == "__main__":
    unittest.main()
