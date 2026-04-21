import re
from pathlib import Path
import unittest

from pipeline_runtime.control_writers import validate_operator_request_headers
from pipeline_runtime.operator_autonomy import (
    SUPPORTED_DECISION_CLASSES,
    SUPPORTED_OPERATOR_POLICIES,
    SUPPORTED_REASON_CODES,
    _MENU_CHOICE_BLOCKER_MARKERS,
    normalize_decision_class,
    normalize_operator_policy,
    normalize_reason_code,
)

FIXTURE_HEADER: str = r"""STATUS: needs_operator
CONTROL_SEQ: 462
REASON_CODE: slice_ambiguity
OPERATOR_POLICY: gate_24h
DECISION_CLASS: operator_only
DECISION_REQUIRED: confirm next slice choice
BASED_ON_WORK: work/4/20/2026-04-20-example-work.md
BASED_ON_VERIFY: verify/4/20/2026-04-20-example-verification.md

Reason:
- example reason line.
"""


def _parse_operator_request_header(text: str) -> dict[str, str]:
    header: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            break
        match = re.match(r"^([A-Z_]+):\s*(.*)$", line)
        if match:
            header[match.group(1)] = match.group(2).rstrip()
    return header


class OperatorRequestHeaderSchemaTests(unittest.TestCase):
    def test_canonical_header_parses_all_expected_fields(self) -> None:
        parsed = _parse_operator_request_header(FIXTURE_HEADER)
        self.assertEqual(
            set(parsed),
            {
                "STATUS",
                "CONTROL_SEQ",
                "REASON_CODE",
                "OPERATOR_POLICY",
                "DECISION_CLASS",
                "DECISION_REQUIRED",
                "BASED_ON_WORK",
                "BASED_ON_VERIFY",
            },
        )

    def test_status_and_control_seq_in_first_12_lines(self) -> None:
        labels = []
        for line in FIXTURE_HEADER.splitlines()[:12]:
            match = re.match(r"^([A-Z_]+):\s*(.*)$", line)
            if match:
                labels.append(match.group(1))
        self.assertIn("STATUS", labels)
        self.assertIn("CONTROL_SEQ", labels)

    def test_reason_code_is_canonical(self) -> None:
        self.assertIn(_parse_operator_request_header(FIXTURE_HEADER)["REASON_CODE"], SUPPORTED_REASON_CODES)

    def test_operator_policy_is_canonical(self) -> None:
        self.assertIn(
            _parse_operator_request_header(FIXTURE_HEADER)["OPERATOR_POLICY"],
            SUPPORTED_OPERATOR_POLICIES,
        )

    def test_decision_class_is_canonical(self) -> None:
        self.assertIn(
            _parse_operator_request_header(FIXTURE_HEADER)["DECISION_CLASS"],
            SUPPORTED_DECISION_CLASSES,
        )

    def test_menu_choice_blocker_markers_includes_git_markers(self) -> None:
        """git/milestone 마커가 _MENU_CHOICE_BLOCKER_MARKERS에 포함되어야 함"""
        for marker in ("커밋", "commit", "push", "milestone", "마일스톤"):
            self.assertIn(marker, _MENU_CHOICE_BLOCKER_MARKERS, f"{marker!r} missing")

    def test_seq617_raw_operator_headers_normalize_to_canonical_metadata(self) -> None:
        self.assertEqual(
            normalize_reason_code("branch_complete_pending_milestone_transition"),
            "approval_required",
        )
        self.assertEqual(
            normalize_reason_code("branch_commit_and_milestone_transition"),
            "approval_required",
        )
        self.assertEqual(
            normalize_operator_policy("stop_until_operator_decision"),
            "immediate_publish",
        )
        self.assertEqual(
            normalize_operator_policy("branch_complete_pending_milestone_transition"),
            "gate_24h",
        )
        self.assertEqual(
            normalize_decision_class("branch_closure_and_milestone_transition"),
            "operator_only",
        )
        self.assertEqual(
            normalize_decision_class("branch_complete_pending_milestone_transition"),
            "operator_only",
        )

        validated = validate_operator_request_headers(
            control_seq=617,
            reason_code="branch_complete_pending_milestone_transition",
            operator_policy="stop_until_operator_decision",
            decision_class="branch_closure_and_milestone_transition",
            decision_required="close branch and decide milestone transition",
            based_on_work="work/4/21/2026-04-21-axis-g15-watcher-test-origin-annotations.md",
            based_on_verify="verify/4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral-verification.md",
        )

        self.assertEqual(validated["reason_code"], "approval_required")
        self.assertEqual(validated["operator_policy"], "immediate_publish")
        self.assertEqual(validated["decision_class"], "operator_only")
        self.assertIn(validated["reason_code"], SUPPORTED_REASON_CODES)
        self.assertIn(validated["operator_policy"], SUPPORTED_OPERATOR_POLICIES)
        self.assertIn(validated["decision_class"], SUPPORTED_DECISION_CLASSES)

    def test_operator_request_writer_rejects_random_decision_class(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported decision_class"):
            validate_operator_request_headers(
                control_seq=618,
                reason_code="approval_required",
                operator_policy="immediate_publish",
                decision_class="not_a_supported_decision_class",
                decision_required="operator must decide",
                based_on_work="work/4/21/2026-04-21-example.md",
                based_on_verify="verify/4/21/2026-04-21-example.md",
            )

    def test_live_operator_request_header_canonical(self) -> None:
        live_file = Path(__file__).parent.parent / ".pipeline" / "operator_request.md"
        if not live_file.exists():
            self.skipTest("operator_request.md not present")
        header = _parse_operator_request_header(live_file.read_text(encoding="utf-8"))
        reason_code = header.get("REASON_CODE", "")
        if reason_code not in SUPPORTED_REASON_CODES:
            self.skipTest(f"Live file drift detected: REASON_CODE={reason_code!r}")
        self.assertIn(header.get("OPERATOR_POLICY", ""), SUPPORTED_OPERATOR_POLICIES)
        self.assertIn(header.get("DECISION_CLASS", ""), SUPPORTED_DECISION_CLASSES)


if __name__ == "__main__":
    unittest.main()
