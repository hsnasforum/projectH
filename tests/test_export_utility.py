import json
import unittest
from pathlib import Path
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

    def test_stream_trace_pairs_includes_feedback_key(self) -> None:
        with TemporaryDirectory() as base_dir:
            store = self._make_store_with_pair(
                base_dir, "sess-fb", "original text", "corrected text"
            )
            pairs = list(store.stream_trace_pairs())
            self.assertEqual(len(pairs), 1)
            self.assertIn("feedback", pairs[0])
            self.assertIsNone(pairs[0]["feedback"])

    def test_stream_trace_pairs_includes_applied_preference_ids_key(self) -> None:
        with TemporaryDirectory() as base_dir:
            store = self._make_store_with_pair(
                base_dir, "sess-pref", "original text", "corrected text"
            )
            pairs = list(store.stream_trace_pairs())
            self.assertEqual(len(pairs), 1)
            self.assertIn("applied_preference_ids", pairs[0])
            self.assertIsNone(pairs[0]["applied_preference_ids"])

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


class TestPreferenceExport(unittest.TestCase):
    def test_preference_assets_path_targets_data_jsonl(self) -> None:
        from scripts.export_traces import PREF_PATH

        self.assertEqual(PREF_PATH.name, "preference_assets.jsonl")
        self.assertEqual(PREF_PATH.parent.name, "data")

    def test_preference_export_includes_candidates_and_active(self) -> None:
        from core.contracts import PreferenceStatus
        from storage.preference_store import PreferenceStore

        with TemporaryDirectory() as base_dir:
            pref_store = PreferenceStore(base_dir=str(Path(base_dir) / "preferences"))
            candidate = pref_store.record_reviewed_candidate_preference(
                delta_fingerprint="candidate-fingerprint",
                candidate_family="correction_rewrite",
                description="candidate preference",
                source_refs={"candidate_id": "cand-1"},
            )
            active = pref_store.record_reviewed_candidate_preference(
                delta_fingerprint="active-fingerprint",
                candidate_family="correction_rewrite",
                description="active preference",
                source_refs={"candidate_id": "cand-2"},
            )
            pref_store.activate_preference(active["preference_id"])

            pref_records = pref_store.get_candidates() + pref_store.get_active_preferences()
            out = Path(base_dir) / "preference_assets.jsonl"
            with out.open("w", encoding="utf-8") as pref_out:
                for rec in pref_records:
                    pref_out.write(json.dumps(rec, ensure_ascii=False) + "\n")

            lines = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertEqual({rec["preference_id"] for rec in lines}, {
                candidate["preference_id"],
                active["preference_id"],
            })
            self.assertEqual({rec["status"] for rec in lines}, {
                PreferenceStatus.CANDIDATE,
                PreferenceStatus.ACTIVE,
            })


class TestCorrectionPreferenceLinks(unittest.TestCase):
    def test_record_correction_stores_applied_preference_ids(self) -> None:
        from storage.correction_store import CorrectionStore

        with TemporaryDirectory() as base_dir:
            store = CorrectionStore(base_dir=str(Path(base_dir) / "corrections"))
            with_preferences = store.record_correction(
                artifact_id="artifact-pref",
                session_id="sess-pref",
                source_message_id="msg-pref",
                original_text="original text",
                corrected_text="corrected text",
                applied_preference_ids=["pref-abc"],
            )
            without_preferences = store.record_correction(
                artifact_id="artifact-none",
                session_id="sess-none",
                source_message_id="msg-none",
                original_text="another original text",
                corrected_text="another corrected text",
                applied_preference_ids=None,
            )

            self.assertIsNotNone(with_preferences)
            self.assertEqual(with_preferences["applied_preference_ids"], ["pref-abc"])
            self.assertIsNotNone(without_preferences)
            self.assertIsNone(without_preferences["applied_preference_ids"])


if __name__ == "__main__":
    unittest.main()
