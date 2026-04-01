"""Tests for storage.preference_store."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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
