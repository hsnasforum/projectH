"""Tests for pipeline_gui.backend control-slot parsing."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from pipeline_gui.backend import parse_control_slots, format_control_summary


class TestParseControlSlots(unittest.TestCase):
    """Newest-valid-control selection and stale listing."""

    def _write_slot(
        self,
        pipeline_dir: Path,
        filename: str,
        status: str,
        age_offset: float = 0,
        control_seq: int | None = None,
    ) -> None:
        slot = pipeline_dir / filename
        seq_line = f"CONTROL_SEQ: {control_seq}\n" if control_seq is not None else ""
        slot.write_text(f"STATUS: {status}\n{seq_line}\nsome body text\n", encoding="utf-8")
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

    def test_control_seq_beats_newer_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "gemini_request.md", "request_open", age_offset=100, control_seq=8)
            self._write_slot(pipeline, "claude_handoff.md", "implement", age_offset=0, control_seq=7)
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "gemini_request.md")
            self.assertEqual(result["active"]["control_seq"], 8)

    def test_stale_gemini_slots_lose_to_higher_handoff_seq(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            self._write_slot(pipeline, "gemini_request.md", "request_open", age_offset=0, control_seq=2)
            self._write_slot(pipeline, "gemini_advice.md", "advice_ready", age_offset=50, control_seq=3)
            self._write_slot(pipeline, "claude_handoff.md", "implement", age_offset=100, control_seq=4)
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertEqual([entry["file"] for entry in result["stale"]], ["gemini_advice.md", "gemini_request.md"])

    def test_same_second_mtime_uses_subsecond_precision(self):
        """When slots share the same integer second, sub-second mtime must break the tie."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            base_time = float(int(time.time()))  # truncated to integer second
            self._write_slot(pipeline, "operator_request.md", "needs_operator")
            os.utime(pipeline / "operator_request.md", (base_time + 0.1, base_time + 0.1))
            self._write_slot(pipeline, "claude_handoff.md", "implement")
            os.utime(pipeline / "claude_handoff.md", (base_time + 0.9, base_time + 0.9))
            result = parse_control_slots(project)
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertGreater(result["active"]["mtime"], result["stale"][0]["mtime"])


class TestParseControlSlotsWindowsBranch(unittest.TestCase):
    """Exercise the IS_WINDOWS / _run branch via mocking."""

    def test_windows_find_printf_produces_subsecond_mtime(self):
        """find -printf '%T@' produces real sub-second epoch floats on WSL."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            (pipeline / "claude_handoff.md").write_text("STATUS: implement\n")
            (pipeline / "operator_request.md").write_text("STATUS: needs_operator\n")

            find_count = {"n": 0}
            # Real find -printf '%T@\n' output: epoch seconds with fractional nanoseconds
            find_responses = {
                "claude_handoff.md": "1712700000.5000000000",
                "operator_request.md": "1712700000.1000000000",
            }

            def fake_run(cmd, **kwargs):
                if isinstance(cmd, list) and cmd[0] == "find":
                    find_count["n"] += 1
                    for fname, resp in find_responses.items():
                        if fname in str(cmd[1]):
                            return 0, resp + "\n"
                    return 1, ""
                if isinstance(cmd, list) and cmd[0] == "head":
                    for fname in find_responses:
                        if fname in str(cmd[-1]):
                            return 0, (pipeline / fname).read_text()
                    return 1, ""
                return 1, ""

            with mock.patch("pipeline_gui.backend.IS_WINDOWS", True), \
                 mock.patch("pipeline_gui.backend._run", side_effect=fake_run), \
                 mock.patch("pipeline_gui.backend._wsl_path_str", side_effect=str):
                result = parse_control_slots(project)

            self.assertGreater(find_count["n"], 0, "find must be called on Windows path")
            self.assertIsNotNone(result["active"])
            self.assertEqual(result["active"]["file"], "claude_handoff.md")
            self.assertAlmostEqual(result["active"]["mtime"], 1712700000.5, places=1)
            self.assertEqual(len(result["stale"]), 1)
            self.assertEqual(result["stale"][0]["file"], "operator_request.md")

    def test_windows_find_same_second_resolved_by_fractional(self):
        """Same integer second but different fractional part must pick the newer slot."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            pipeline = project / ".pipeline"
            pipeline.mkdir()
            (pipeline / "claude_handoff.md").write_text("STATUS: implement\n")
            (pipeline / "gemini_request.md").write_text("STATUS: request_open\n")

            find_responses = {
                "claude_handoff.md": "1712700000.2000000000",
                "gemini_request.md": "1712700000.8000000000",
            }

            def fake_run(cmd, **kwargs):
                if isinstance(cmd, list) and cmd[0] == "find":
                    for fname, resp in find_responses.items():
                        if fname in str(cmd[1]):
                            return 0, resp + "\n"
                    return 1, ""
                if isinstance(cmd, list) and cmd[0] == "head":
                    for fname in find_responses:
                        if fname in str(cmd[-1]):
                            return 0, (pipeline / fname).read_text()
                    return 1, ""
                return 1, ""

            with mock.patch("pipeline_gui.backend.IS_WINDOWS", True), \
                 mock.patch("pipeline_gui.backend._run", side_effect=fake_run), \
                 mock.patch("pipeline_gui.backend._wsl_path_str", side_effect=str):
                result = parse_control_slots(project)

            self.assertEqual(result["active"]["file"], "gemini_request.md")
            self.assertAlmostEqual(result["active"]["mtime"], 1712700000.8, places=1)


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
        self.assertIn("mtime fallback", active_text)
        self.assertIn("operator_request.md", stale_text)
        self.assertIn("비활성", stale_text)
        self.assertIn("mtime fallback", stale_text)

    def test_active_with_control_seq_shows_seq(self):
        parsed = {
            "active": {"file": "claude_handoff.md", "status": "implement", "label": "Claude 실행", "mtime": 1.0, "control_seq": 5},
            "stale": [],
        }
        active_text, _ = format_control_summary(parsed)
        self.assertIn("seq 5", active_text)
        self.assertNotIn("mtime fallback", active_text)

    def test_stale_with_mixed_provenance(self):
        parsed = {
            "active": {"file": "claude_handoff.md", "status": "implement", "label": "Claude 실행", "mtime": 1.0, "control_seq": 3},
            "stale": [
                {"file": "operator_request.md", "status": "needs_operator", "label": "operator 대기", "mtime": 0.5, "control_seq": 2},
                {"file": "gemini_request.md", "status": "request_open", "label": "Gemini 실행", "mtime": 0.3},
            ],
        }
        active_text, stale_text = format_control_summary(parsed)
        self.assertIn("seq 3", active_text)
        self.assertIn("operator_request.md (seq 2)", stale_text)
        self.assertIn("gemini_request.md (mtime fallback)", stale_text)

    def test_active_only_no_stale_text(self):
        parsed = {
            "active": {"file": "gemini_advice.md", "status": "advice_ready", "label": "Codex follow-up", "mtime": 1.0},
            "stale": [],
        }
        _, stale_text = format_control_summary(parsed)
        self.assertEqual(stale_text, "")


if __name__ == "__main__":
    unittest.main()
