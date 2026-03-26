import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.write_note import WriteNoteTool


class WriteNoteToolTest(unittest.TestCase):
    def test_rejects_writes_outside_allowed_roots(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            notes_dir = root / "notes"
            tool = WriteNoteTool(allowed_roots=[str(notes_dir)])

            with self.assertRaises(PermissionError):
                tool.inspect_target(path=str(root / "outside.md"))

    def test_allows_new_file_inside_allowed_roots(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            notes_dir = root / "notes"
            tool = WriteNoteTool(allowed_roots=[str(notes_dir)])

            target = notes_dir / "demo.md"
            info = tool.inspect_target(path=str(target))
            written = tool.run(path=str(target), text="# Demo", approved=True)

            self.assertFalse(info["overwrite"])
            self.assertEqual(Path(written), target.resolve())
            self.assertTrue(target.exists())

    def test_refuses_overwrite_by_default(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            notes_dir = root / "notes"
            notes_dir.mkdir(parents=True, exist_ok=True)
            target = notes_dir / "demo.md"
            target.write_text("# Old", encoding="utf-8")
            tool = WriteNoteTool(allowed_roots=[str(notes_dir)])

            info = tool.inspect_target(path=str(target))

            self.assertTrue(info["overwrite"])
            with self.assertRaises(FileExistsError):
                tool.run(path=str(target), text="# New", approved=True)


if __name__ == "__main__":
    unittest.main()
