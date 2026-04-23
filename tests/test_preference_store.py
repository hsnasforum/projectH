"""Tests for storage.preference_store."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

from core.contracts import PreferenceStatus
from storage.correction_store import CorrectionStore
from storage.preference_store import PreferenceStore


class PreferenceStoreTest(unittest.TestCase):

    def _make_stores(self, tmp_dir: str) -> tuple[PreferenceStore, CorrectionStore]:
        pref = PreferenceStore(base_dir=str(Path(tmp_dir) / "preferences"))
        corr = CorrectionStore(base_dir=str(Path(tmp_dir) / "corrections"))
        return pref, corr

    def _seed_corrections(
        self,
        corr: CorrectionStore,
        *,
        sessions: list[str] = ["s1", "s2"],
    ) -> str:
        """Create corrections in multiple sessions with same delta. Returns fingerprint."""
        original = "프로젝트H는 문서 비서입니다."
        corrected = "프로젝트H는 로컬 퍼스트 문서 비서입니다."
        fp = None
        for i, sid in enumerate(sessions):
            r = corr.record_correction(
                artifact_id=f"a{i}",
                session_id=sid,
                source_message_id=f"m{i}",
                original_text=original,
                corrected_text=corrected,
            )
            if r:
                fp = r["delta_fingerprint"]
        return fp

    def _record_same_fingerprint_correction(
        self,
        corr: CorrectionStore,
        *,
        artifact_id: str,
        session_id: str,
        filler: str,
    ) -> dict:
        record = corr.record_correction(
            artifact_id=artifact_id,
            session_id=session_id,
            source_message_id=f"msg-{artifact_id}",
            original_text=f"{filler} old {filler}",
            corrected_text=f"{filler} new {filler}",
        )
        self.assertIsNotNone(record)
        return record

    def test_promote_from_corrections_cross_session(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            result = pref.promote_from_corrections(fp, corr)
            self.assertIsNotNone(result)
            self.assertEqual(result["status"], PreferenceStatus.CANDIDATE)
            self.assertEqual(result["cross_session_count"], 2)
            self.assertEqual(result["evidence_count"], 2)
            self.assertTrue(result["description"])

    def test_promote_stores_avg_similarity_score(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            records = [
                self._record_same_fingerprint_correction(
                    corr,
                    artifact_id="quality-a",
                    session_id="s1",
                    filler="short",
                ),
                self._record_same_fingerprint_correction(
                    corr,
                    artifact_id="quality-b",
                    session_id="s2",
                    filler="long" * 20,
                ),
            ]
            fp = records[0]["delta_fingerprint"]
            self.assertEqual(records[1]["delta_fingerprint"], fp)

            result = pref.promote_from_corrections(fp, corr)

            expected = round(sum(r["similarity_score"] for r in records) / len(records), 4)
            self.assertEqual(result["avg_similarity_score"], expected)

    def test_promote_stores_original_corrected_snippets(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])

            result = pref.promote_from_corrections(fp, corr)

            self.assertEqual(result["original_snippet"], "프로젝트H는 문서 비서입니다."[:400])
            self.assertEqual(result["corrected_snippet"], "프로젝트H는 로컬 퍼스트 문서 비서입니다."[:400])

    def test_refresh_updates_avg_similarity_score(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            records = [
                self._record_same_fingerprint_correction(
                    corr,
                    artifact_id="quality-a",
                    session_id="s1",
                    filler="short",
                ),
                self._record_same_fingerprint_correction(
                    corr,
                    artifact_id="quality-b",
                    session_id="s2",
                    filler="long" * 20,
                ),
            ]
            fp = records[0]["delta_fingerprint"]
            created = pref.promote_from_corrections(fp, corr)

            new_record = self._record_same_fingerprint_correction(
                corr,
                artifact_id="quality-c",
                session_id="s3",
                filler="medium" * 8,
            )
            self.assertEqual(new_record["delta_fingerprint"], fp)
            refreshed = pref.promote_from_corrections(fp, corr)

            records.append(new_record)
            expected = round(sum(r["similarity_score"] for r in records) / len(records), 4)
            self.assertNotEqual(created["avg_similarity_score"], expected)
            self.assertEqual(refreshed["avg_similarity_score"], expected)

    def test_auto_activation_keeps_candidate_below_threshold(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            result = pref.promote_from_corrections(fp, corr)
            self.assertEqual(result["status"], PreferenceStatus.CANDIDATE)
            self.assertIsNone(result["activated_at"])

    def test_auto_activation_promotes_candidate_at_threshold(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2", "s3"])
            result = pref.promote_from_corrections(fp, corr)
            self.assertEqual(result["cross_session_count"], 3)
            self.assertEqual(result["status"], PreferenceStatus.ACTIVE)
            self.assertIsNotNone(result["activated_at"])

    def test_auto_activation_leaves_active_preference_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)
            activated = pref.activate_preference(created["preference_id"])

            corr.record_correction(
                artifact_id="a3",
                session_id="s3",
                source_message_id="m3",
                original_text="프로젝트H는 문서 비서입니다.",
                corrected_text="프로젝트H는 로컬 퍼스트 문서 비서입니다.",
            )
            refreshed = pref.promote_from_corrections(fp, corr)
            self.assertEqual(refreshed["cross_session_count"], 3)
            self.assertEqual(refreshed["status"], PreferenceStatus.ACTIVE)
            self.assertEqual(refreshed["activated_at"], activated["activated_at"])

    def test_auto_activation_leaves_rejected_preference_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)
            rejected = pref.reject_preference(created["preference_id"])

            corr.record_correction(
                artifact_id="a3",
                session_id="s3",
                source_message_id="m3",
                original_text="프로젝트H는 문서 비서입니다.",
                corrected_text="프로젝트H는 로컬 퍼스트 문서 비서입니다.",
            )
            refreshed = pref.promote_from_corrections(fp, corr)
            self.assertEqual(refreshed["cross_session_count"], 3)
            self.assertEqual(refreshed["status"], PreferenceStatus.REJECTED)
            self.assertEqual(refreshed["rejected_at"], rejected["rejected_at"])

    def test_promote_requires_2_sessions(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s1"])  # same session
            result = pref.promote_from_corrections(fp, corr)
            self.assertIsNone(result)

    def test_promote_idempotent(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            r1 = pref.promote_from_corrections(fp, corr)
            r2 = pref.promote_from_corrections(fp, corr)
            self.assertEqual(r1["preference_id"], r2["preference_id"])

    def test_get_and_find_by_fingerprint(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)

            fetched = pref.get(created["preference_id"])
            self.assertEqual(fetched["preference_id"], created["preference_id"])

            by_fp = pref.find_by_fingerprint(fp)
            self.assertEqual(by_fp["preference_id"], created["preference_id"])

    def test_get_nonexistent_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, _ = self._make_stores(tmp)
            self.assertIsNone(pref.get("pref-nope"))

    def test_activate_preference(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)

            activated = pref.activate_preference(created["preference_id"])
            self.assertEqual(activated["status"], PreferenceStatus.ACTIVE)
            self.assertIsNotNone(activated["activated_at"])

    def test_pause_preference(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)
            pref.activate_preference(created["preference_id"])

            paused = pref.pause_preference(created["preference_id"])
            self.assertEqual(paused["status"], PreferenceStatus.PAUSED)

    def test_reject_preference(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)

            rejected = pref.reject_preference(created["preference_id"])
            self.assertEqual(rejected["status"], PreferenceStatus.REJECTED)

    def test_update_description_changes_field(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, _ = self._make_stores(tmp)
            created = pref.record_reviewed_candidate_preference(
                delta_fingerprint="sha256:test_update_description",
                candidate_family="correction_rewrite",
                description="기존 설명",
                source_refs={"candidate_id": "cand-update-description"},
            )
            sleep(0.001)

            updated = pref.update_description(created["preference_id"], "새 설명")

            self.assertIsNotNone(updated)
            self.assertEqual(updated["description"], "새 설명")
            self.assertGreater(updated["updated_at"], created["created_at"])
            stored = pref.get(created["preference_id"])
            self.assertEqual(stored["description"], "새 설명")

    def test_update_description_returns_none_for_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, _ = self._make_stores(tmp)

            self.assertIsNone(pref.update_description("nonexistent-id", "text"))

    def test_lifecycle_candidate_to_active_to_paused_to_active(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)
            pid = created["preference_id"]

            self.assertEqual(pref.get(pid)["status"], PreferenceStatus.CANDIDATE)
            pref.activate_preference(pid)
            self.assertEqual(pref.get(pid)["status"], PreferenceStatus.ACTIVE)
            pref.pause_preference(pid)
            self.assertEqual(pref.get(pid)["status"], PreferenceStatus.PAUSED)
            pref.activate_preference(pid)
            self.assertEqual(pref.get(pid)["status"], PreferenceStatus.ACTIVE)

    def test_get_active_preferences(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)
            pref.activate_preference(created["preference_id"])

            active = pref.get_active_preferences()
            self.assertEqual(len(active), 1)
            self.assertEqual(active[0]["status"], PreferenceStatus.ACTIVE)

    def test_get_active_excludes_paused(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)
            pref.activate_preference(created["preference_id"])
            pref.pause_preference(created["preference_id"])

            self.assertEqual(len(pref.get_active_preferences()), 0)

    def test_get_candidates(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            pref.promote_from_corrections(fp, corr)
            candidates = pref.get_candidates()
            self.assertEqual(len(candidates), 1)

    def test_list_all(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            pref.promote_from_corrections(fp, corr)
            all_prefs = pref.list_all()
            self.assertEqual(len(all_prefs), 1)

    def test_description_generation_replacements(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)
            self.assertIn("교정 패턴", created["description"])

    def test_record_reviewed_candidate_preference_creates_and_idempotent(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, _ = self._make_stores(tmp)
            fp = "sha256:test_fingerprint_abc123"
            source_refs_a = {
                "candidate_id": "cand-aaa",
                "candidate_updated_at": "2026-04-16T00:00:00Z",
                "artifact_id": "art-1",
                "source_message_id": "msg-1",
                "review_action": "accept",
                "session_id": "s1",
            }
            r1 = pref.record_reviewed_candidate_preference(
                delta_fingerprint=fp,
                candidate_family="correction_rewrite",
                description="검토 수락된 교정 패턴",
                source_refs=source_refs_a,
            )
            self.assertEqual(r1["status"], PreferenceStatus.CANDIDATE)
            self.assertEqual(r1["delta_fingerprint"], fp)
            self.assertEqual(len(r1["reviewed_candidate_source_refs"]), 1)

            # same candidate_id => no duplicate
            r2 = pref.record_reviewed_candidate_preference(
                delta_fingerprint=fp,
                candidate_family="correction_rewrite",
                description="검토 수락된 교정 패턴",
                source_refs=source_refs_a,
            )
            self.assertEqual(r2["preference_id"], r1["preference_id"])
            self.assertEqual(len(r2["reviewed_candidate_source_refs"]), 1)

            # different candidate_id => appended
            source_refs_b = dict(source_refs_a, candidate_id="cand-bbb", session_id="s2")
            r3 = pref.record_reviewed_candidate_preference(
                delta_fingerprint=fp,
                candidate_family="correction_rewrite",
                description="검토 수락된 교정 패턴",
                source_refs=source_refs_b,
            )
            self.assertEqual(r3["preference_id"], r1["preference_id"])
            self.assertEqual(len(r3["reviewed_candidate_source_refs"]), 2)

            # shows up in list_all
            all_prefs = pref.list_all()
            self.assertEqual(len(all_prefs), 1)

    def test_record_reviewed_candidate_preference_with_rejected_status(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, _ = self._make_stores(tmp)
            result = pref.record_reviewed_candidate_preference(
                delta_fingerprint="sha256:test-reject-fp",
                candidate_family="correction_rewrite",
                description="거절 테스트 선호",
                source_refs={
                    "candidate_id": "global:sha256:test-reject-fp",
                    "source_message_id": "global",
                },
                status=PreferenceStatus.REJECTED,
            )

            self.assertEqual(result["status"], PreferenceStatus.REJECTED)
            self.assertIsNotNone(result["rejected_at"])
            fetched = pref.find_by_fingerprint("sha256:test-reject-fp")
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["status"], PreferenceStatus.REJECTED)

    def test_record_reviewed_candidate_stores_avg_similarity_score(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, _ = self._make_stores(tmp)

            record = pref.record_reviewed_candidate_preference(
                delta_fingerprint="sha256:test_avg_similarity",
                candidate_family="correction_rewrite",
                description="검토 수락된 교정 패턴",
                source_refs={"candidate_id": "cand-quality"},
                avg_similarity_score=0.25,
            )

            self.assertEqual(record["avg_similarity_score"], 0.25)
            stored = pref.get(record["preference_id"])
            self.assertEqual(stored["avg_similarity_score"], 0.25)

    def test_record_reviewed_candidate_stores_snippets(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, _ = self._make_stores(tmp)

            record = pref.record_reviewed_candidate_preference(
                delta_fingerprint="sha256:test_snippets",
                candidate_family="correction_rewrite",
                description="검토 수락된 교정 패턴",
                source_refs={"candidate_id": "cand-snippet"},
                original_snippet="hello",
                corrected_snippet="world",
            )

            self.assertEqual(record["original_snippet"], "hello")
            self.assertEqual(record["corrected_snippet"], "world")
            stored = pref.get(record["preference_id"])
            self.assertEqual(stored["original_snippet"], "hello")
            self.assertEqual(stored["corrected_snippet"], "world")

    def test_record_reviewed_candidate_update_preserves_score_when_none_passed(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, _ = self._make_stores(tmp)
            fp = "sha256:test_avg_similarity_preserve"
            created = pref.record_reviewed_candidate_preference(
                delta_fingerprint=fp,
                candidate_family="correction_rewrite",
                description="검토 수락된 교정 패턴",
                source_refs={"candidate_id": "cand-quality-a"},
                avg_similarity_score=0.3,
            )

            updated = pref.record_reviewed_candidate_preference(
                delta_fingerprint=fp,
                candidate_family="correction_rewrite",
                description="검토 수락된 교정 패턴",
                source_refs={"candidate_id": "cand-quality-b"},
                avg_similarity_score=None,
            )

            self.assertEqual(updated["preference_id"], created["preference_id"])
            self.assertEqual(updated["avg_similarity_score"], 0.3)
            stored = pref.get(created["preference_id"])
            self.assertEqual(stored["avg_similarity_score"], 0.3)

    def test_refresh_evidence_on_new_correction(self) -> None:
        with TemporaryDirectory() as tmp:
            pref, corr = self._make_stores(tmp)
            fp = self._seed_corrections(corr, sessions=["s1", "s2"])
            created = pref.promote_from_corrections(fp, corr)
            self.assertEqual(created["evidence_count"], 2)

            # Add a third correction in a third session
            corr.record_correction(
                artifact_id="a3",
                session_id="s3",
                source_message_id="m3",
                original_text="프로젝트H는 문서 비서입니다.",
                corrected_text="프로젝트H는 로컬 퍼스트 문서 비서입니다.",
            )
            refreshed = pref.promote_from_corrections(fp, corr)
            self.assertEqual(refreshed["evidence_count"], 3)
            self.assertEqual(refreshed["cross_session_count"], 3)
            self.assertEqual(refreshed["status"], PreferenceStatus.ACTIVE)
            self.assertIsNotNone(refreshed["activated_at"])
