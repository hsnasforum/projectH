import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.contracts import CorrectionStatus
from storage.correction_store import CorrectionStore


class TestPromoteAssets(unittest.TestCase):
    def _write_hq_jsonl(self, path: Path, pairs: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for p in pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    def test_promotes_pairs_to_correction_store(self) -> None:
        from scripts.promote_assets import promote_from_jsonl
        with TemporaryDirectory() as d:
            hq = Path(d) / "high_quality_traces.jsonl"
            self._write_hq_jsonl(hq, [{
                "session_id": "sess-1",
                "message_id": "msg-1",
                "prompt": "The document covers climate change impacts.",
                "completion": "The report examines climate adaptation strategies.",
                "similarity_score": 0.075,
                "change_types": [],
                "is_high_quality": True,
            }])
            store = CorrectionStore(base_dir=str(Path(d) / "corrections"))
            promoted, skipped = promote_from_jsonl(hq, store)
            self.assertEqual(promoted, 1)
            self.assertEqual(skipped, 0)
            records = store.list_recent(limit=10)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["status"], CorrectionStatus.PROMOTED)

    def test_promote_idempotent(self) -> None:
        from scripts.promote_assets import promote_from_jsonl
        with TemporaryDirectory() as d:
            hq = Path(d) / "high_quality_traces.jsonl"
            self._write_hq_jsonl(hq, [{
                "session_id": "sess-1",
                "message_id": "msg-1",
                "prompt": "Original document text for idempotency test.",
                "completion": "Revised document with substantial changes applied.",
                "similarity_score": 0.075,
                "change_types": [],
                "is_high_quality": True,
            }])
            store = CorrectionStore(base_dir=str(Path(d) / "corrections"))
            promote_from_jsonl(hq, store)
            promote_from_jsonl(hq, store)
            records = store.list_recent(limit=10)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["status"], CorrectionStatus.PROMOTED)

    def test_promote_missing_file_exits_cleanly(self) -> None:
        with TemporaryDirectory() as d:
            hq = Path(d) / "nonexistent.jsonl"
            # main() guards the missing-file case.
            import io
            from contextlib import redirect_stdout
            import scripts.promote_assets as pa
            original = pa.HQ_PATH
            pa.HQ_PATH = hq
            try:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    pa.main()
                self.assertIn("run export_traces.py", buf.getvalue())
            finally:
                pa.HQ_PATH = original


if __name__ == "__main__":
    unittest.main()
