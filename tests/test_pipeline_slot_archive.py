import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_SOURCE = REPO_ROOT / ".pipeline" / "archive-stale-control-slots.sh"


class ArchiveStaleControlSlotsTest(unittest.TestCase):
    def _make_temp_pipeline(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        pipeline_dir = root / ".pipeline"
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        script_path = pipeline_dir / "archive-stale-control-slots.sh"
        script_path.write_text(SCRIPT_SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
        script_path.chmod(0o755)
        return tmp, pipeline_dir, script_path

    def _write_slot(self, path: Path, text: str, epoch: int) -> None:
        path.write_text(text, encoding="utf-8")
        os.utime(path, (epoch, epoch))

    def test_all_stale_archives_only_non_newest_slots(self) -> None:
        tmp, pipeline_dir, script_path = self._make_temp_pipeline()
        with tmp:
            older = pipeline_dir / "operator_request.md"
            newest = pipeline_dir / "claude_handoff.md"
            self._write_slot(older, "STATUS: needs_operator\n", 100)
            self._write_slot(newest, "STATUS: implement\n", 200)

            result = subprocess.run(
                ["bash", str(script_path), "--all-stale"],
                cwd=pipeline_dir.parent,
                check=True,
                text=True,
                capture_output=True,
            )

            self.assertIn("Newest control file: claude_handoff.md", result.stdout)
            self.assertTrue(newest.exists())
            self.assertFalse(older.exists())
            archived = list((pipeline_dir / "archive").rglob("operator_request.*.md"))
            self.assertEqual(len(archived), 1)

    def test_explicit_newest_slot_is_skipped(self) -> None:
        tmp, pipeline_dir, script_path = self._make_temp_pipeline()
        with tmp:
            older = pipeline_dir / "operator_request.md"
            newest = pipeline_dir / "claude_handoff.md"
            self._write_slot(older, "STATUS: needs_operator\n", 100)
            self._write_slot(newest, "STATUS: implement\n", 200)

            result = subprocess.run(
                ["bash", str(script_path), "claude_handoff.md"],
                cwd=pipeline_dir.parent,
                check=True,
                text=True,
                capture_output=True,
            )

            self.assertIn("SKIP newest control file claude_handoff.md", result.stdout)
            self.assertTrue(newest.exists())
            self.assertTrue(older.exists())
            self.assertFalse((pipeline_dir / "archive").exists())


if __name__ == "__main__":
    unittest.main()
