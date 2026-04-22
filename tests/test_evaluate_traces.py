import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory


class TestEvaluateTraces(unittest.TestCase):
    def _write_jsonl(self, path: Path, records: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _make_record(self, i: int, score: float = 0.075, hq: bool = True) -> dict:
        return {
            "prompt": "a" * 200,
            "completion": "b" * 180,
            "session_id": f"sess-{i}",
            "message_id": f"msg-{i}",
            "similarity_score": score,
            "change_types": [],
            "is_high_quality": hq,
            "feedback": None,
        }

    def test_evaluate_justified_verdict(self) -> None:
        from scripts.evaluate_traces import evaluate

        records = [self._make_record(i) for i in range(120)]
        buf = io.StringIO()
        with redirect_stdout(buf):
            evaluate(records)
        self.assertIn("JUSTIFIED", buf.getvalue())
        self.assertIn("120", buf.getvalue())

    def test_evaluate_insufficient_verdict(self) -> None:
        from scripts.evaluate_traces import evaluate

        records = [self._make_record(i, hq=False) for i in range(30)]
        buf = io.StringIO()
        with redirect_stdout(buf):
            evaluate(records)
        self.assertIn("INSUFFICIENT", buf.getvalue())

    def test_evaluate_empty_records_exits_cleanly(self) -> None:
        from scripts.evaluate_traces import evaluate

        buf = io.StringIO()
        with redirect_stdout(buf):
            evaluate([])
        self.assertIn("No correction pairs", buf.getvalue())

    def test_missing_file_main_exits_cleanly(self) -> None:
        import scripts.evaluate_traces as et

        with TemporaryDirectory() as base_dir:
            original = et.ALL_PATH
            et.ALL_PATH = Path(base_dir) / "missing.jsonl"
            try:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    et.main()
                self.assertIn("run export_traces.py", buf.getvalue())
            finally:
                et.ALL_PATH = original


if __name__ == "__main__":
    unittest.main()
