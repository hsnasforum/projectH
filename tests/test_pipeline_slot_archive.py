import hashlib
import json
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

    def _run_archive(
        self,
        script_path: Path,
        *args: str,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{REPO_ROOT}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else str(REPO_ROOT)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(script_path), *args],
            cwd=script_path.parent.parent,
            check=True,
            text=True,
            capture_output=True,
            env=env,
        )

    def test_all_stale_archives_only_non_newest_slots(self) -> None:
        tmp, pipeline_dir, script_path = self._make_temp_pipeline()
        with tmp:
            older = pipeline_dir / "operator_request.md"
            newest = pipeline_dir / "implement_handoff.md"
            self._write_slot(older, "STATUS: needs_operator\nCONTROL_SEQ: 1\n", 100)
            self._write_slot(newest, "STATUS: implement\nCONTROL_SEQ: 2\n", 200)

            result = self._run_archive(script_path, "--all-stale")

            self.assertIn("Protected control file: implement_handoff.md", result.stdout)
            self.assertTrue(newest.exists())
            self.assertFalse(older.exists())
            archived = list((pipeline_dir / "archive").rglob("operator_request.*.md"))
            self.assertEqual(len(archived), 1)
            manifests = list((pipeline_dir / "archive").rglob("archive-manifest.jsonl"))
            self.assertEqual(len(manifests), 1)
            manifest_entries = [
                json.loads(line)
                for line in manifests[0].read_text(encoding="utf-8").splitlines()
            ]
            archived_hash = hashlib.sha256(archived[0].read_bytes()).hexdigest()
            self.assertEqual(manifest_entries[0]["slot"], "operator_request.md")
            self.assertFalse(manifest_entries[0]["dry_run"])
            self.assertEqual(manifest_entries[0]["source_path"], ".pipeline/operator_request.md")
            self.assertTrue(manifest_entries[0]["target_path"].startswith(".pipeline/archive/"))
            self.assertEqual(manifest_entries[0]["sha256"], archived_hash)
            self.assertEqual(manifest_entries[0]["archived_slot"]["file"], "operator_request.md")
            self.assertEqual(manifest_entries[0]["archived_slot"]["control_seq"], 1)
            self.assertEqual(manifest_entries[0]["pre_active_control"]["file"], "implement_handoff.md")
            self.assertEqual(manifest_entries[0]["pre_active_control"]["control_seq"], 2)
            self.assertEqual(manifest_entries[0]["protected_control"]["file"], "implement_handoff.md")
            self.assertEqual(manifest_entries[0]["post_active_control"]["file"], "implement_handoff.md")

    def test_all_stale_keeps_highest_control_seq_even_when_mtime_is_older(self) -> None:
        tmp, pipeline_dir, script_path = self._make_temp_pipeline()
        with tmp:
            active = pipeline_dir / "implement_handoff.md"
            newer_stale = pipeline_dir / "operator_request.md"
            self._write_slot(active, "STATUS: implement\nCONTROL_SEQ: 739\n", 100)
            self._write_slot(newer_stale, "STATUS: needs_operator\nCONTROL_SEQ: 734\n", 200)

            result = self._run_archive(script_path, "--all-stale")

            self.assertIn("Protected control file: implement_handoff.md", result.stdout)
            self.assertIn("SKIP protected control file implement_handoff.md", result.stdout)
            self.assertTrue(active.exists())
            self.assertFalse(newer_stale.exists())
            archived = list((pipeline_dir / "archive").rglob("operator_request.*.md"))
            self.assertEqual(len(archived), 1)

    def test_explicit_newest_slot_is_skipped(self) -> None:
        tmp, pipeline_dir, script_path = self._make_temp_pipeline()
        with tmp:
            older = pipeline_dir / "operator_request.md"
            newest = pipeline_dir / "implement_handoff.md"
            self._write_slot(older, "STATUS: needs_operator\nCONTROL_SEQ: 1\n", 100)
            self._write_slot(newest, "STATUS: implement\nCONTROL_SEQ: 2\n", 200)

            result = self._run_archive(script_path, "implement_handoff.md")

            self.assertIn("SKIP protected control file implement_handoff.md", result.stdout)
            self.assertTrue(newest.exists())
            self.assertTrue(older.exists())
            self.assertFalse((pipeline_dir / "archive").exists())

    def test_dry_run_does_not_archive_or_write_manifest(self) -> None:
        tmp, pipeline_dir, script_path = self._make_temp_pipeline()
        with tmp:
            stale = pipeline_dir / "operator_request.md"
            active = pipeline_dir / "implement_handoff.md"
            self._write_slot(stale, "STATUS: needs_operator\nCONTROL_SEQ: 1\n", 100)
            self._write_slot(active, "STATUS: implement\nCONTROL_SEQ: 2\n", 200)

            result = self._run_archive(
                script_path,
                "--all-stale",
                extra_env={"PIPELINE_ARCHIVE_DRY_RUN": "1"},
            )

            self.assertIn("Dry run: 1", result.stdout)
            self.assertTrue(active.exists())
            self.assertTrue(stale.exists())
            self.assertFalse((pipeline_dir / "archive").exists())

    def test_all_stale_appends_manifest_entry_per_archived_slot(self) -> None:
        tmp, pipeline_dir, script_path = self._make_temp_pipeline()
        with tmp:
            active = pipeline_dir / "implement_handoff.md"
            first_stale = pipeline_dir / "operator_request.md"
            second_stale = pipeline_dir / "advisory_request.md"
            self._write_slot(active, "STATUS: implement\nCONTROL_SEQ: 3\n", 300)
            self._write_slot(first_stale, "STATUS: needs_operator\nCONTROL_SEQ: 1\n", 100)
            self._write_slot(second_stale, "STATUS: request_open\nCONTROL_SEQ: 2\n", 200)

            self._run_archive(script_path, "--all-stale")

            manifests = list((pipeline_dir / "archive").rglob("archive-manifest.jsonl"))
            self.assertEqual(len(manifests), 1)
            entries = [
                json.loads(line)
                for line in manifests[0].read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                [entry["slot"] for entry in entries],
                ["advisory_request.md", "operator_request.md"],
            )
            self.assertTrue(all(entry["post_active_control"]["file"] == "implement_handoff.md" for entry in entries))


if __name__ == "__main__":
    unittest.main()
