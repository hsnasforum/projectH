"""Tests for TaskLogger read-path validation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from storage.task_log import TaskLogger


class TaskLogValidationTest(unittest.TestCase):
    def _make_logger(self, tmp_dir: str) -> TaskLogger:
        return TaskLogger(path=str(Path(tmp_dir) / "task_log.jsonl"))

    def _write_records(self, logger: TaskLogger, records: list[object]) -> None:
        logger.path.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
            encoding="utf-8",
        )

    def test_malformed_line_missing_ts_filtered(self) -> None:
        with TemporaryDirectory() as tmp:
            logger = self._make_logger(tmp)
            self._write_records(
                logger,
                [
                    {
                        "session_id": "session-task",
                        "action": "summary_created",
                        "detail": {},
                    }
                ],
            )

            records = logger.iter_session_records("session-task")

            self.assertEqual(records, [])

    def test_malformed_line_missing_action_filtered(self) -> None:
        with TemporaryDirectory() as tmp:
            logger = self._make_logger(tmp)
            self._write_records(
                logger,
                [
                    {
                        "ts": "2026-04-28T00:00:00+00:00",
                        "session_id": "session-task",
                        "detail": {},
                    }
                ],
            )

            records = logger.iter_session_records("session-task")

            self.assertEqual(records, [])

    def test_valid_record_included(self) -> None:
        with TemporaryDirectory() as tmp:
            logger = self._make_logger(tmp)
            record = {
                "ts": "2026-04-28T00:00:00+00:00",
                "session_id": "session-task",
                "action": "summary_created",
                "detail": {"artifact_id": "artifact-1"},
            }
            self._write_records(logger, [record])

            records = logger.iter_session_records("session-task")

            self.assertEqual(records, [record])


if __name__ == "__main__":
    unittest.main()
