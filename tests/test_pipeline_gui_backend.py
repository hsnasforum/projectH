"""Tests for pipeline_gui.backend control-slot parsing."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from pipeline_gui.backend import parse_control_slots, format_control_summary


class TestParseControlSlots(unittest.TestCase):
    """Newest-valid-control selection and stale listing."""

    def _write_slot(self, pipeline_dir: Path, filename: str, status: str, age_offset: float = 0) -> None:
        slot = pipeline_dir / filename
        slot.write_text(f"STATUS: {status}\n\nsome body text\n", encoding="utf-8")
        import os
        mtime = time.time() - age_offset
        os.utime(slot, (mtime, mtime))

    def test_single_valid_slot_is_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "claude_handoff.md", "implement")
            result = parse_control_slots(project)
            self.assertIsNotNone(result["active"])
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertEqual(result["stale"], [])

    def test_newest_slot_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "operator_request.md", "needs_operator", age_offset=100)
            self._write_slot(pipeline, "claude_handoff.md", "implement", age_offset=0)
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertEqual(len(result["stale"]), 1)
            self.assertEqual(result["stale"][0]["file"], "operator_request.md")

    def test_invalid_status_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "claude_handoff.md", "implement_blocked")
            result = parse_control_slots(project)
            self.assertIsNone(result["active"])

    def test_no_slots_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            result = parse_control_slots(project)
            self.assertIsNone(result["active"])
            self.assertEqual(result["stale"], [])

    def test_multiple_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "claude_handoff.md", "implement", age_offset=0)
            self._write_slot(pipeline, "gemini_request.md", "request_open", age_offset=50)
            self._write_slot(pipeline, "operator_request.md", "needs_operator", age_offset=100)
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertEqual(len(result["stale"]), 2)


class TestFormatControlSummary(unittest.TestCase):
    """GUI text rendering from parsed control-slot summary."""

    def test_no_active(self):
        active_text, stale_text = format_control_summary({"active": None, "stale": []})
        self.assertEqual(active_text, "활성 제어: 없음")
        self.assertEqual(stale_text, "")

    def test_active_with_stale(self):
        parsed = {
            "active": {"file": "claude_handoff.md", "status": "implement", "label": "Claude 실행", "mtime": 1.0},
            "stale": [{"file": "operator_request.md", "status": "needs_operator", "label": "operator 대기", "mtime": 0.5}],
        }
        active_text, stale_text = format_control_summary(parsed)
        self.assertIn("Claude 실행", active_text)
        self.assertIn("claude_handoff.md", active_text)
        self.assertIn("operator_request.md", stale_text)
        self.assertIn("비활성", stale_text)

    def test_active_only_no_stale_text(self):
        parsed = {
            "active": {"file": "gemini_advice.md", "status": "advice_ready", "label": "Codex follow-up", "mtime": 1.0},
            "stale": [],
        }
        _, stale_text = format_control_summary(parsed)
        self.assertEqual(stale_text, "")


if __name__ == "__main__":
    unittest.main()
