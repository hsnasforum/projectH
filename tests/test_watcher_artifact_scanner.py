from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from verify_fsm import JobState
from watcher_artifact_scanner import ArtifactScanner


def _write_work_note(path: Path, changed_files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bullets = "\n".join(f"- `{item}`" for item in changed_files) or "- 없음"
    path.write_text(
        f"# {path.stem}\n\n## 변경 파일\n{bullets}\n\n## 검증\n- 미실행\n",
        encoding="utf-8",
    )


def _write_verify_note_for_work(path: Path, work_ref: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {path.stem}\n\n## 대상\n- `{work_ref}`\n\n## 결과\n- 통과\n",
        encoding="utf-8",
    )


class ArtifactScannerTest(unittest.TestCase):
    def test_latest_work_and_snapshot_skip_metadata_only_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            scanner = ArtifactScanner(watch_dir=watch_dir, verify_dir=verify_dir, repo_root=root)
            real_note = watch_dir / "4" / "9" / "2026-04-09-real-implementation.md"
            meta_note = watch_dir / "4" / "9" / "2026-04-09-metadata.md"
            _write_work_note(real_note, ["docs/PRODUCT_SPEC.md"])
            _write_work_note(meta_note, ["work/4/9/2026-04-09-metadata.md"])
            os.utime(meta_note, (real_note.stat().st_atime + 5, real_note.stat().st_mtime + 5))

            self.assertEqual(scanner.get_latest_work_path(), real_note)
            self.assertTrue(scanner.is_metadata_only_work_note(meta_note))
            self.assertFalse(scanner.is_dispatchable_work_note(meta_note))
            self.assertIn("4/9/2026-04-09-real-implementation.md", scanner.get_work_tree_snapshot())
            self.assertNotIn("4/9/2026-04-09-metadata.md", scanner.get_work_tree_snapshot())
            self.assertIn("4/9/2026-04-09-metadata.md", scanner.get_work_tree_snapshot_broad())

    def test_work_has_matching_verify_accepts_same_day_and_cross_day_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            scanner = ArtifactScanner(watch_dir=watch_dir, verify_dir=verify_dir, repo_root=root)
            same_day_work = watch_dir / "4" / "9" / "2026-04-09-same-day.md"
            cross_day_work = watch_dir / "4" / "19" / "2026-04-19-cross-day.md"
            same_day_verify = verify_dir / "4" / "9" / "2026-04-09-same-day-verify.md"
            cross_day_verify = verify_dir / "4" / "20" / "2026-04-20-cross-day-verify.md"
            _write_work_note(same_day_work, ["app/main.py"])
            _write_work_note(cross_day_work, ["app/other.py"])
            _write_verify_note_for_work(same_day_verify, "work/4/9/2026-04-09-same-day.md")
            _write_verify_note_for_work(cross_day_verify, "work/4/19/2026-04-19-cross-day.md")
            now = time.time()
            for note in (same_day_work, cross_day_work):
                os.utime(note, (now - 20, now - 20))
            for note in (same_day_verify, cross_day_verify):
                os.utime(note, (now - 10, now - 10))

            self.assertEqual(scanner.get_latest_same_day_verify_path_for_work(same_day_work), same_day_verify)
            self.assertEqual(scanner.get_latest_same_day_verify_path_for_work(cross_day_work), cross_day_verify)
            self.assertTrue(scanner.work_has_matching_verify(same_day_work))
            self.assertTrue(scanner.work_has_matching_verify(cross_day_work))

    def test_latest_verify_candidate_uses_latest_broad_work_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            scanner = ArtifactScanner(watch_dir=watch_dir, verify_dir=verify_dir, repo_root=root)
            older_work = watch_dir / "4" / "19" / "2026-04-19-older.md"
            latest_work = watch_dir / "4" / "20" / "2026-04-20-latest.md"
            latest_verify = verify_dir / "4" / "20" / "2026-04-20-latest-verify.md"
            _write_work_note(older_work, ["watcher_core.py"])
            _write_work_note(latest_work, ["verify_fsm.py"])
            _write_verify_note_for_work(latest_verify, "work/4/20/2026-04-20-latest.md")
            now = time.time()
            os.utime(older_work, (now - 30, now - 30))
            os.utime(latest_work, (now - 20, now - 20))
            os.utime(latest_verify, (now - 10, now - 10))

            self.assertFalse(scanner.latest_work_needs_verify_broad())
            self.assertIsNone(scanner.get_latest_verify_candidate_path())
            self.assertEqual(
                scanner.get_latest_unverified_work_path(include_metadata_only=True),
                older_work,
            )

    def test_verify_feedback_and_receipt_state_follow_verify_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            control_path = root / ".pipeline" / "implement_handoff.md"
            control_path.parent.mkdir(parents=True, exist_ok=True)
            control_path.write_text("STATUS: implement\n", encoding="utf-8")
            scanner = ArtifactScanner(
                watch_dir=watch_dir,
                verify_dir=verify_dir,
                repo_root=root,
                completion_paths=(control_path,),
            )
            work_note = watch_dir / "4" / "19" / "2026-04-19-latest-meta.md"
            _write_work_note(work_note, ["work/4/19/2026-04-19-latest-meta.md"])
            job = JobState.from_artifact("job-1", str(work_note), run_id="run-1")

            control_sig, before_verify_sig = scanner.build_verify_feedback_sigs(job)

            verify_note = verify_dir / "4" / "20" / "2026-04-20-latest-meta-verification.md"
            _write_verify_note_for_work(verify_note, "work/4/19/2026-04-19-latest-meta.md")
            _, after_verify_sig = scanner.build_verify_feedback_sigs(job)
            receipt_path, receipt_mtime = scanner.build_verify_receipt_state(job)

            self.assertIn("implement_handoff.md", control_sig)
            self.assertNotEqual(before_verify_sig, after_verify_sig)
            self.assertEqual(receipt_path, "verify/4/20/2026-04-20-latest-meta-verification.md")
            self.assertGreater(receipt_mtime, 0.0)
