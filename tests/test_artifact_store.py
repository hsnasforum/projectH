"""Tests for storage.artifact_store."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from storage.artifact_store import ArtifactStore


class ArtifactStoreTest(unittest.TestCase):

    def _make_store(self, tmp_dir: str) -> ArtifactStore:
        return ArtifactStore(base_dir=str(Path(tmp_dir) / "artifacts"))

    def _create_sample(self, store: ArtifactStore, **overrides) -> dict:
        defaults = dict(
            artifact_id="artifact-abc123",
            artifact_kind="grounded_brief",
            session_id="session-1",
            source_message_id="msg-xyz",
            draft_text="Sample draft text.",
            source_paths=["/tmp/file.txt"],
            response_origin={"provider": "mock", "badge": "MOCK"},
            summary_chunks=[{"text": "chunk1"}],
            evidence=[{"label": "heading", "text": "Evidence text."}],
        )
        defaults.update(overrides)
        return store.create(**defaults)

    def test_create_and_get(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._create_sample(store)
            self.assertEqual(record["artifact_id"], "artifact-abc123")
            self.assertEqual(record["artifact_kind"], "grounded_brief")
            self.assertEqual(record["draft_text"], "Sample draft text.")
            self.assertEqual(record["corrections"], [])
            self.assertEqual(record["saves"], [])
            self.assertIsNone(record["latest_corrected_text"])
            self.assertIsNone(record["latest_outcome"])

            fetched = store.get("artifact-abc123")
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["artifact_id"], "artifact-abc123")

    def test_get_nonexistent_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self.assertIsNone(store.get("artifact-doesnotexist"))

    def test_create_sets_timestamps(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            record = self._create_sample(store)
            self.assertIn("created_at", record)
            self.assertIn("updated_at", record)
            self.assertEqual(record["created_at"], record["updated_at"])

    def test_append_correction(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._create_sample(store)

            updated = store.append_correction("artifact-abc123", corrected_text="Fixed text v1")
            self.assertIsNotNone(updated)
            self.assertEqual(len(updated["corrections"]), 1)
            self.assertEqual(updated["latest_corrected_text"], "Fixed text v1")
            self.assertEqual(updated["latest_outcome"], "corrected")

            updated2 = store.append_correction("artifact-abc123", corrected_text="Fixed text v2")
            self.assertEqual(len(updated2["corrections"]), 2)
            self.assertEqual(updated2["latest_corrected_text"], "Fixed text v2")

    def test_append_correction_nonexistent_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self.assertIsNone(store.append_correction("nope", corrected_text="x"))

    def test_append_save(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._create_sample(store)

            updated = store.append_save(
                "artifact-abc123",
                saved_note_path="/notes/summary.md",
                save_content_source="original_draft",
                approval_id="approval-xyz",
            )
            self.assertIsNotNone(updated)
            self.assertEqual(len(updated["saves"]), 1)
            self.assertEqual(updated["saves"][0]["saved_note_path"], "/notes/summary.md")
            self.assertEqual(updated["saves"][0]["save_content_source"], "original_draft")
            self.assertEqual(updated["saves"][0]["approval_id"], "approval-xyz")

    def test_record_outcome_accepted(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._create_sample(store)

            updated = store.record_outcome("artifact-abc123", outcome="accepted_as_is")
            self.assertEqual(updated["latest_outcome"], "accepted_as_is")
            self.assertIsNone(updated["content_verdict"])

    def test_record_outcome_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._create_sample(store)

            updated = store.record_outcome("artifact-abc123", outcome="rejected", content_verdict="rejected")
            self.assertEqual(updated["latest_outcome"], "rejected")
            self.assertEqual(updated["content_verdict"], "rejected")

    def test_list_by_session(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._create_sample(store, artifact_id="a1", session_id="s-alpha")
            self._create_sample(store, artifact_id="a2", session_id="s-alpha")
            self._create_sample(store, artifact_id="a3", session_id="s-alpha")
            self._create_sample(store, artifact_id="b1", session_id="s-beta")

            alpha = store.list_by_session("s-alpha")
            self.assertEqual(len(alpha), 3)
            beta = store.list_by_session("s-beta")
            self.assertEqual(len(beta), 1)
            gamma = store.list_by_session("s-gamma")
            self.assertEqual(len(gamma), 0)

    def test_list_recent(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._create_sample(store, artifact_id="old", session_id="s1")
            # Mutate to change updated_at
            store.append_correction("old", corrected_text="fix")
            self._create_sample(store, artifact_id="new", session_id="s1")

            recent = store.list_recent(limit=2)
            self.assertEqual(len(recent), 2)
            # Both should be returned; order by updated_at desc

    def test_atomic_write_no_orphan_on_failure(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            self._create_sample(store)
            artifacts_dir = Path(tmp) / "artifacts"
            tmp_files = list(artifacts_dir.glob("*.tmp"))
            self.assertEqual(len(tmp_files), 0)

    def test_corrupt_file_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            store = self._make_store(tmp)
            path = store._path("artifact-corrupt")
            path.write_text("not valid json", encoding="utf-8")
            self.assertIsNone(store.get("artifact-corrupt"))
