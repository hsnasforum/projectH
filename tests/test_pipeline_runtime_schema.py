from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from pipeline_runtime.schema import latest_round_markdown, parse_control_slots, read_control_meta


class RuntimeSchemaTest(unittest.TestCase):
    def test_read_control_meta_reads_extended_operator_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = Path(tmp) / "operator_request.md"
            slot.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 184",
                        "REASON_CODE: approval_required",
                        "OPERATOR_POLICY: immediate_publish",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: approve runtime auth refresh",
                        "BASED_ON_WORK: work/4/16/example.md",
                        "BASED_ON_VERIFY: verify/4/16/example.md",
                    ]
                ),
                encoding="utf-8",
            )

            meta = read_control_meta(slot)

            self.assertEqual(meta["status"], "needs_operator")
            self.assertEqual(meta["control_seq"], 184)
            self.assertEqual(meta["reason_code"], "approval_required")
            self.assertEqual(meta["operator_policy"], "immediate_publish")
            self.assertEqual(meta["decision_class"], "operator_only")
            self.assertEqual(meta["decision_required"], "approve runtime auth refresh")
            self.assertEqual(meta["based_on_work"], "work/4/16/example.md")
            self.assertEqual(meta["based_on_verify"], "verify/4/16/example.md")

    def test_parse_control_slots_ignores_extended_headers_for_active_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pipeline = Path(tmp)
            (pipeline / "operator_request.md").write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 184",
                        "REASON_CODE: approval_required",
                        "OPERATOR_POLICY: immediate_publish",
                    ]
                ),
                encoding="utf-8",
            )
            (pipeline / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 185\n",
                encoding="utf-8",
            )

            slots = parse_control_slots(pipeline)

            self.assertEqual(slots["active"]["file"], "claude_handoff.md")
            self.assertEqual(slots["stale"][0]["file"], "operator_request.md")

    def test_latest_round_markdown_ignores_root_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# metadata\n", encoding="utf-8")
            round_note = root / "4" / "16" / "2026-04-16-real-round.md"
            round_note.parent.mkdir(parents=True, exist_ok=True)
            round_note.write_text("# round\n", encoding="utf-8")

            round_mtime = round_note.stat().st_mtime + 1
            readme_mtime = round_mtime + 10
            os.utime(round_note, (round_mtime, round_mtime))
            os.utime(readme, (readme_mtime, readme_mtime))

            rel, mtime = latest_round_markdown(root)

            self.assertEqual(rel, "4/16/2026-04-16-real-round.md")
            self.assertEqual(mtime, round_mtime)


if __name__ == "__main__":
    unittest.main()
