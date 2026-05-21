from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from watcher_runtime_exporter import WatcherRuntimeExporter


class WatcherRuntimeExporterTest(unittest.TestCase):
    def _exporter(self, root: Path, *, enabled: bool = True) -> WatcherRuntimeExporter:
        run_id = "20260522T000000Z-p123"
        run_dir = root / ".pipeline" / "runs" / run_id
        current_run_path = root / ".pipeline" / "current_run.json"
        current_run_path.parent.mkdir(parents=True, exist_ok=True)
        return WatcherRuntimeExporter(
            enabled=enabled,
            run_id=run_id,
            run_dir=run_dir,
            run_status_path=run_dir / "status.json",
            run_events_path=run_dir / "events.jsonl",
            current_run_path=current_run_path,
            repo_root=root,
        )

    def test_write_run_pointer_records_run_paths_pid_and_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exporter = self._exporter(root)

            with (
                mock.patch("watcher_runtime_exporter.os.getpid", return_value=4242),
                mock.patch(
                    "watcher_runtime_exporter.process_starttime_fingerprint",
                    return_value="fingerprint-4242",
                ),
            ):
                exporter.write_run_pointer()

            data = json.loads((root / ".pipeline" / "current_run.json").read_text(encoding="utf-8"))
            self.assertEqual(data["run_id"], "20260522T000000Z-p123")
            self.assertEqual(data["status_path"], ".pipeline/runs/20260522T000000Z-p123/status.json")
            self.assertEqual(data["events_path"], ".pipeline/runs/20260522T000000Z-p123/events.jsonl")
            self.assertEqual(data["watcher_pid"], 4242)
            self.assertEqual(data["watcher_fingerprint"], "fingerprint-4242")
            self.assertTrue(str(data["updated_at"]).endswith("Z"))

    def test_append_event_records_monotonic_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exporter = self._exporter(root)

            exporter.append_event("first", {"ok": True})
            exporter.append_event("second", {"ok": False})

            events_path = root / ".pipeline" / "runs" / "20260522T000000Z-p123" / "events.jsonl"
            rows = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual([row["seq"] for row in rows], [1, 2])
            self.assertEqual([row["event_type"] for row in rows], ["first", "second"])
            self.assertEqual(rows[0]["source"], "watcher-exporter")
            self.assertEqual(rows[1]["payload"], {"ok": False})

    def test_disabled_exporter_does_not_write_files_or_advance_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exporter = self._exporter(root, enabled=False)

            exporter.write_run_pointer()
            exporter.append_event("ignored", {"ok": True})

            self.assertFalse((root / ".pipeline" / "current_run.json").exists())
            self.assertFalse(
                (root / ".pipeline" / "runs" / "20260522T000000Z-p123" / "events.jsonl").exists()
            )
            self.assertEqual(exporter._event_seq, 0)
