from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline_runtime.schema import parse_control_slots, read_control_meta


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


if __name__ == "__main__":
    unittest.main()
