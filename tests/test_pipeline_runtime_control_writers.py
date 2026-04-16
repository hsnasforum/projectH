from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from pipeline_runtime.control_writers import (
    render_implement_blocked,
    render_operator_request,
    validate_operator_candidate_status,
    write_operator_request,
)
from pipeline_runtime.schema import read_control_meta


class ControlWritersTest(unittest.TestCase):
    def test_write_operator_request_round_trips_through_control_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "operator_request.md"
            write_operator_request(
                path,
                control_seq=184,
                reason_code="approval_required",
                operator_policy="immediate_publish",
                decision_class="operator_only",
                decision_required="approve runtime auth refresh",
                based_on_work="work/4/16/example.md",
                based_on_verify="verify/4/16/example.md",
                body="Why now:\n- smoke only",
            )

            meta = read_control_meta(path)

            self.assertEqual(meta["status"], "needs_operator")
            self.assertEqual(meta["control_seq"], 184)
            self.assertEqual(meta["reason_code"], "approval_required")
            self.assertEqual(meta["operator_policy"], "immediate_publish")
            self.assertEqual(meta["decision_class"], "operator_only")
            self.assertEqual(meta["based_on_work"], "work/4/16/example.md")
            self.assertEqual(meta["based_on_verify"], "verify/4/16/example.md")

    def test_render_operator_request_rejects_missing_required_headers(self) -> None:
        with self.assertRaisesRegex(ValueError, "based_on_verify is required"):
            render_operator_request(
                control_seq=184,
                reason_code="approval_required",
                operator_policy="immediate_publish",
                decision_class="operator_only",
                decision_required="approve runtime auth refresh",
                based_on_work="work/4/16/example.md",
                based_on_verify="",
                body="body",
            )

    def test_render_implement_blocked_rejects_unknown_reason_code_and_escalation_class(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported block_reason_code"):
            render_implement_blocked(
                block_reason="blocked",
                block_reason_code="unknown_reason",
                request="codex_triage",
                escalation_class="codex_triage",
                handoff=".pipeline/claude_handoff.md",
                handoff_sha="sha256:test",
                block_id="sha256:test:blocked",
            )
        with self.assertRaisesRegex(ValueError, "unsupported escalation_class"):
            render_implement_blocked(
                block_reason="blocked",
                block_reason_code="codex_triage_only",
                request="codex_triage",
                escalation_class="operator_only",
                handoff=".pipeline/claude_handoff.md",
                handoff_sha="sha256:test",
                block_id="sha256:test:blocked",
            )

    def test_validate_operator_candidate_status_requires_structured_classification_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "structured metadata"):
            validate_operator_candidate_status(
                {
                    "control": {
                        "active_control_file": ".pipeline/operator_request.md",
                        "active_control_status": "needs_operator",
                    },
                    "autonomy": {
                        "mode": "needs_operator",
                        "reason_code": "slice_ambiguity",
                        "operator_policy": "gate_24h",
                        "classification_source": "metadata_missing_fallback",
                    },
                }
            )

        validate_operator_candidate_status(
            {
                "control": {"active_control_file": "", "active_control_status": "none"},
                "autonomy": {
                    "mode": "triage",
                    "reason_code": "slice_ambiguity",
                    "operator_policy": "gate_24h",
                    "classification_source": "reason_code",
                },
            }
        )

    def test_no_non_test_direct_writes_for_operator_or_implement_blocked(self) -> None:
        root = Path(__file__).resolve().parent.parent
        targets = [
            root / "watcher_core.py",
            root / ".pipeline" / "smoke-implement-blocked-auto-triage.sh",
        ]
        targets.extend(sorted((root / "pipeline_runtime").glob("*.py")))

        forbidden_patterns = {
            "write_text needs_operator": re.compile(
                r'write_text\(\s*(?:f|r|rf)?["\']STATUS:\s*needs_operator',
                re.S,
            ),
            "write_text implement_blocked": re.compile(
                r'write_text\(\s*(?:f|r|rf)?["\']STATUS:\s*implement_blocked',
                re.S,
            ),
            "stdout implement_blocked": re.compile(
                r'sys\.stdout\.write\(\s*(?:f|r|rf)?["\']STATUS:\s*implement_blocked',
                re.S,
            ),
        }

        violations: list[str] = []
        for path in targets:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for label, pattern in forbidden_patterns.items():
                if pattern.search(text):
                    violations.append(f"{path.relative_to(root)}: {label}")

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
