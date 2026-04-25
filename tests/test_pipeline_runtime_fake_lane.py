from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.pipeline_runtime_fake_lane import handle_prompt


class PipelineRuntimeFakeLaneTest(unittest.TestCase):
    def test_verify_prompt_writes_verify_note_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = handle_prompt(
                root,
                "Codex",
                "ROLE: verify\nNEXT_CONTROL_SEQ: 4\nWORK: work/4/12/seed.md\nVERIFY: 없음\n",
                gemini_every=5,
            )

            self.assertEqual(len(written), 2)
            verify_notes = list((root / "verify").rglob("*.md"))
            self.assertEqual(len(verify_notes), 1)
            self.assertIn("work/4/12/seed.md", verify_notes[0].read_text(encoding="utf-8"))
            handoff = root / ".pipeline" / "implement_handoff.md"
            self.assertTrue(handoff.exists())
            self.assertIn("CONTROL_SEQ: 4", handoff.read_text(encoding="utf-8"))

    def test_verify_prompt_routes_to_advisory_request_on_schedule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handle_prompt(
                root,
                "Codex",
                "ROLE: verify\nNEXT_CONTROL_SEQ: 5\nWORK: work/4/12/seed.md\nVERIFY: 없음\n",
                gemini_every=5,
            )

            request_path = root / ".pipeline" / "advisory_request.md"
            self.assertTrue(request_path.exists())
            self.assertIn("STATUS: request_open", request_path.read_text(encoding="utf-8"))

    def test_advisory_prompt_writes_report_and_advice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handle_prompt(
                root,
                "Gemini",
                "ROLE: advisory\nNEXT_CONTROL_SEQ: 6\n- advisory log: report/gemini/synthetic.md\n",
                gemini_every=5,
            )

            report_path = root / "report" / "gemini" / "synthetic.md"
            advice_path = root / ".pipeline" / "advisory_advice.md"
            self.assertTrue(report_path.exists())
            self.assertTrue(advice_path.exists())
            self.assertIn("STATUS: advice_ready", advice_path.read_text(encoding="utf-8"))

    def test_implement_prompt_writes_work_note_from_handoff_seq(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = root / ".pipeline" / "implement_handoff.md"
            handoff_path.parent.mkdir(parents=True, exist_ok=True)
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 8\n", encoding="utf-8")

            handle_prompt(
                root,
                "Claude",
                "ROLE: implement\nHANDOFF: .pipeline/implement_handoff.md\nHANDOFF_SHA: abc123\n",
                gemini_every=5,
            )

            work_notes = list((root / "work").rglob("*.md"))
            self.assertEqual(len(work_notes), 1)
            self.assertIn("CONTROL_SEQ 8", work_notes[0].read_text(encoding="utf-8"))
