import re
import tempfile
from pathlib import Path
import unittest

from pipeline_runtime.control_writers import validate_operator_request_headers
from pipeline_runtime.operator_autonomy import (
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
    PUBLICATION_BOUNDARY_REASON_CODES,
    PR_CREATION_GATE_REASON,
    PR_MERGE_GATE_REASON,
    SUPPORTED_DECISION_CLASSES,
    SUPPORTED_OPERATOR_POLICIES,
    SUPPORTED_REASON_CODES,
    _MENU_CHOICE_BLOCKER_MARKERS,
    classify_operator_candidate,
    evaluate_stale_operator_control,
    is_commit_push_approval_stop,
    normalize_decision_class,
    normalize_operator_policy,
    normalize_reason_code,
    operator_gate_marker_from_decision,
    referenced_operator_pr_numbers,
    resolve_operator_control,
)
from pipeline_runtime.schema import read_control_meta

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

    def test_commit_push_approval_stop_uses_metadata_and_body_predicate(self) -> None:
        self.assertTrue(
            is_commit_push_approval_stop(
                {
                    "status": "needs_operator",
                    "reason_code": "approval_required",
                    "decision_required": "approve completed commit and remote push publication",
                }
            )
        )
        self.assertTrue(
            is_commit_push_approval_stop(
                {
                    "status": "needs_operator",
                    "reason_code": "approval_required",
                },
                control_text="operator approval is required after commit evidence and push evidence are ready",
            )
        )
        self.assertTrue(
            is_commit_push_approval_stop(
                {
                    "status": "needs_operator",
                    "reason_code": COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
                    "decision_required": "automation bundle commit and push authorization",
                }
            )
        )

    def test_commit_push_approval_stop_rejects_non_matching_stops(self) -> None:
        self.assertFalse(
            is_commit_push_approval_stop(
                {
                    "status": "implement",
                    "reason_code": "approval_required",
                    "decision_required": "approve completed commit and remote push publication",
                }
            )
        )
        self.assertFalse(
            is_commit_push_approval_stop(
                {
                    "status": "needs_operator",
                    "reason_code": "truth_sync_required",
                    "decision_required": "approve completed commit and remote push publication",
                }
            )
        )
        self.assertFalse(
            is_commit_push_approval_stop(
                {
                    "status": "needs_operator",
                    "reason_code": "approval_required",
                    "decision_required": "approve completed commit only",
                }
            )
        )

    def test_shared_stale_operator_evaluator_requires_verified_allowed_work(self) -> None:
        marker = evaluate_stale_operator_control(
            control_text=(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 462\n"
                "REASON_CODE: truth_sync_required\n"
                "BASED_ON_WORK: work/4/20/2026-04-20-example-work.md\n"
            ),
            control_meta={
                "status": "needs_operator",
                "reason_code": "truth_sync_required",
                "based_on_work": "work/4/20/2026-04-20-example-work.md",
            },
            verified_work_paths=["work/4/20/2026-04-20-example-work.md"],
            control_file="operator_request.md",
            control_seq=462,
        )

        self.assertEqual(marker["reason"], "verified_blockers_resolved")
        self.assertEqual(marker["resolved_work_paths"], ["work/4/20/2026-04-20-example-work.md"])

    def test_shared_stale_operator_evaluator_keeps_publication_boundary_stopped(self) -> None:
        marker = evaluate_stale_operator_control(
            control_text=(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 463\n"
                "REASON_CODE: approval_required\n"
                "BASED_ON_WORK: work/4/20/2026-04-20-example-work.md\n"
            ),
            control_meta={
                "status": "needs_operator",
                "reason_code": "approval_required",
                "based_on_work": "work/4/20/2026-04-20-example-work.md",
            },
            verified_work_paths=["work/4/20/2026-04-20-example-work.md"],
            control_file="operator_request.md",
            control_seq=463,
        )

        self.assertIsNone(marker)

    def test_shared_gate_marker_shape_matches_consumers(self) -> None:
        decision = classify_operator_candidate(
            "",
            control_meta={
                "reason_code": COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
                "operator_policy": "internal_only",
                "decision_class": "release_gate",
            },
            control_seq=713,
            now_ts=1_000.0,
        )

        marker = operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=713,
        )

        self.assertIsNotNone(marker)
        self.assertEqual(marker["reason"], COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON)
        self.assertEqual(marker["mode"], "triage")
        self.assertEqual(marker["routed_to"], "verify_followup")

    def test_commit_push_bundle_authorization_is_internal_followup_metadata(self) -> None:
        self.assertIn(COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON, SUPPORTED_REASON_CODES)
        self.assertIn("release_gate", SUPPORTED_DECISION_CLASSES)

        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            f"REASON_CODE: {COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON}\n"
            "OPERATOR_POLICY: internal_only\n"
            "DECISION_CLASS: release_gate\n"
            "DECISION_REQUIRED: automation axis commit and push authorization\n",
            control_meta={
                "status": "needs_operator",
                "reason_code": COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
                "operator_policy": "internal_only",
                "decision_class": "release_gate",
                "decision_required": "automation axis commit and push authorization",
            },
            idle_stable=True,
            now_ts=1_000.0,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(decision["operator_policy"], "internal_only")
        self.assertEqual(decision["decision_class"], "release_gate")
        self.assertFalse(decision["operator_eligible"])

    def test_pr_creation_gate_routes_to_verify_publish_followup(self) -> None:
        self.assertIn(PR_CREATION_GATE_REASON, SUPPORTED_REASON_CODES)
        self.assertIn("release_gate", SUPPORTED_DECISION_CLASSES)

        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            f"REASON_CODE: {PR_CREATION_GATE_REASON}\n"
            "OPERATOR_POLICY: gate_24h\n"
            "DECISION_CLASS: release_gate\n"
            "DECISION_REQUIRED: create PR feat/example -> main\n",
            control_meta={
                "status": "needs_operator",
                "reason_code": PR_CREATION_GATE_REASON,
                "operator_policy": "gate_24h",
                "decision_class": "release_gate",
                "decision_required": "create PR feat/example -> main",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(decision["operator_policy"], "gate_24h")
        self.assertEqual(decision["decision_class"], "release_gate")
        self.assertFalse(decision["operator_eligible"])

    def test_pr_merge_gate_internal_only_routes_to_verify_followup_backlog(self) -> None:
        self.assertIn(PR_MERGE_GATE_REASON, SUPPORTED_REASON_CODES)
        self.assertIn("merge_gate", SUPPORTED_DECISION_CLASSES)

        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            f"REASON_CODE: {PR_MERGE_GATE_REASON}\n"
            "OPERATOR_POLICY: internal_only\n"
            "DECISION_CLASS: merge_gate\n"
            "DECISION_REQUIRED: PR #27 merge approval\n",
            control_meta={
                "status": "needs_operator",
                "reason_code": PR_MERGE_GATE_REASON,
                "operator_policy": "internal_only",
                "decision_class": "merge_gate",
                "decision_required": "PR #27 merge approval",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        marker = operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=1718,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(decision["operator_policy"], "internal_only")
        self.assertEqual(decision["decision_class"], "merge_gate")
        self.assertFalse(decision["operator_eligible"])
        self.assertIsNotNone(marker)
        self.assertEqual(marker["reason"], PR_MERGE_GATE_REASON)
        self.assertEqual(marker["routed_to"], "verify_followup")

    def test_compound_milestone_pr_merge_gate_routes_to_verify_followup_backlog(self) -> None:
        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            "CONTROL_SEQ: 114\n"
            "REASON_CODE: m28_direction + pr_merge_gate\n"
            "OPERATOR_POLICY: internal_only\n"
            "DECISION_CLASS: next_milestone_selection + branch_strategy\n"
            "DECISION_REQUIRED: M28 scope OR PR merge first\n",
            control_meta={
                "status": "needs_operator",
                "control_seq": 114,
                "reason_code": "m28_direction + pr_merge_gate",
                "operator_policy": "internal_only",
                "decision_class": "next_milestone_selection + branch_strategy",
                "decision_required": "M28 scope OR PR merge first",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        marker = operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=114,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(decision["reason_code"], PR_MERGE_GATE_REASON)
        self.assertEqual(decision["decision_class"], "next_slice_selection")
        self.assertFalse(decision["operator_eligible"])
        self.assertIsNotNone(marker)
        self.assertEqual(marker["reason"], PR_MERGE_GATE_REASON)
        self.assertEqual(marker["routed_to"], "verify_followup")

    def test_pr_merge_gate_is_recoverable_after_referenced_pr_is_completed(self) -> None:
        marker = evaluate_stale_operator_control(
            control_text=(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 1721\n"
                f"REASON_CODE: {PR_MERGE_GATE_REASON}\n"
                "OPERATOR_POLICY: internal_only\n"
                "DECISION_CLASS: merge_gate\n"
                "DECISION_REQUIRED: PR #27 merge approval\n"
                "PR #27: https://github.com/hsnasforum/projectH/pull/27\n"
            ),
            control_meta={
                "status": "needs_operator",
                "control_seq": 1721,
                "reason_code": PR_MERGE_GATE_REASON,
                "operator_policy": "internal_only",
                "decision_class": "merge_gate",
                "decision_required": "PR #27 merge approval",
            },
            verified_work_paths=[],
            completed_pr_numbers=[27],
            control_file="operator_request.md",
            control_seq=1721,
        )

        self.assertIsNotNone(marker)
        self.assertEqual(marker["reason"], "pr_merge_completed")
        self.assertEqual(marker["resolved_pr_numbers"], [27])

    def test_pr_merge_gate_head_mismatch_routes_to_recovery(self) -> None:
        marker = evaluate_stale_operator_control(
            control_text=(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 2\n"
                f"REASON_CODE: {PR_MERGE_GATE_REASON}\n"
                "OPERATOR_POLICY: internal_only\n"
                "DECISION_CLASS: merge_gate\n"
                "DECISION_REQUIRED: PR #27 merge approval\n"
                "- HEAD: `77d1827`\n"
                "PR #27: https://github.com/hsnasforum/projectH/pull/27\n"
            ),
            control_meta={
                "status": "needs_operator",
                "control_seq": 2,
                "reason_code": PR_MERGE_GATE_REASON,
                "operator_policy": "internal_only",
                "decision_class": "merge_gate",
                "decision_required": "PR #27 merge approval",
            },
            verified_work_paths=[],
            mismatched_pr_numbers=[27],
            control_file="operator_request.md",
            control_seq=2,
        )

        self.assertIsNotNone(marker)
        self.assertEqual(marker["reason"], "pr_merge_head_mismatch")
        self.assertEqual(marker["resolved_pr_numbers"], [27])

    def test_referenced_operator_pr_numbers_prefers_current_pr_field(self) -> None:
        numbers = referenced_operator_pr_numbers(
            control_text=(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 12\n"
                f"REASON_CODE: {PR_MERGE_GATE_REASON}\n"
                "OPERATOR_POLICY: internal_only\n"
                "DECISION_CLASS: merge_gate\n"
                "DECISION_REQUIRED: merge current PR gate\n"
                "PR: https://github.com/hsnasforum/projectH/pull/28\n"
                "\n"
                "Background:\n"
                "- Earlier PR #27 was merged at an older HEAD.\n"
            ),
            control_meta={
                "status": "needs_operator",
                "reason_code": PR_MERGE_GATE_REASON,
                "operator_policy": "internal_only",
                "decision_class": "merge_gate",
                "decision_required": "merge current PR gate",
            },
        )

        self.assertEqual(numbers, [28])

    def test_referenced_operator_pr_numbers_prefers_structured_metadata(self) -> None:
        numbers = referenced_operator_pr_numbers(
            control_text=(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 13\n"
                f"REASON_CODE: {PR_MERGE_GATE_REASON}\n"
                "\n"
                "Background:\n"
                "- Earlier PR #27 was merged at an older HEAD.\n"
            ),
            control_meta={
                "reason_code": PR_MERGE_GATE_REASON,
                "pr_url": "https://github.com/hsnasforum/projectH/pull/28",
                "decision_required": "merge current PR gate",
            },
        )

        self.assertEqual(numbers, [28])

    def test_external_publication_boundary_stays_operator_visible(self) -> None:
        for reason in PUBLICATION_BOUNDARY_REASON_CODES:
            with self.subTest(reason=reason):
                self.assertIn(reason, SUPPORTED_REASON_CODES)

                decision = classify_operator_candidate(
                    "STATUS: needs_operator\n"
                    f"REASON_CODE: {reason}\n"
                    "OPERATOR_POLICY: gate_24h\n"
                    "DECISION_CLASS: release_gate\n"
                    "DECISION_REQUIRED: approve merge of draft PR\n",
                    control_meta={
                        "status": "needs_operator",
                        "reason_code": reason,
                        "operator_policy": "gate_24h",
                        "decision_class": "release_gate",
                        "decision_required": "approve merge of draft PR",
                    },
                    idle_stable=True,
                    control_mtime=1_000.0,
                    now_ts=1_000.0,
                )

                self.assertEqual(decision["mode"], "needs_operator")
                self.assertEqual(decision["suppressed_mode"], "needs_operator")
                self.assertEqual(decision["routed_to"], "operator")
                self.assertEqual(decision["operator_policy"], "gate_24h")
                self.assertEqual(decision["decision_class"], "release_gate")
                self.assertTrue(decision["operator_eligible"])

    def test_auth_login_required_stays_operator_visible(self) -> None:
        self.assertIn("auth_login_required", SUPPORTED_REASON_CODES)

        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            "REASON_CODE: auth_login_required\n"
            "OPERATOR_POLICY: gate_24h\n"
            "DECISION_CLASS: operator_only\n"
            "DECISION_REQUIRED: run login before continuing automation\n",
            control_meta={
                "status": "needs_operator",
                "reason_code": "auth_login_required",
                "operator_policy": "gate_24h",
                "decision_class": "operator_only",
                "decision_required": "run login before continuing automation",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )
        marker = operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=1801,
        )

        self.assertEqual(decision["mode"], "needs_operator")
        self.assertEqual(decision["suppressed_mode"], "needs_operator")
        self.assertEqual(decision["reason_code"], "auth_login_required")
        self.assertEqual(decision["routed_to"], "operator")
        self.assertEqual(decision["operator_policy"], "gate_24h")
        self.assertEqual(decision["decision_class"], "operator_only")
        self.assertTrue(decision["operator_eligible"])
        self.assertIsNone(marker)

    def test_advisory_before_operator_milestone_direction_routes_to_verify_followup(self) -> None:
        control_text = (
            "STATUS: needs_operator\n"
            "CONTROL_SEQ: 133\n"
            "REASON_CODE: m30_direction_fresh_scoping\n"
            "OPERATOR_POLICY: advisory_before_operator\n"
            "DECISION_CLASS: next_milestone_selection\n"
            "DECISION_REQUIRED: M30 direction — choose next milestone\n"
            "BASED_ON_WORK: work/4/24/2026-04-24-m29-release-gate-milestones.md\n"
            "BASED_ON_VERIFY: verify/4/24/2026-04-24-m29-release-gate-milestones.md\n"
        )

        self.assertEqual(normalize_reason_code("m30_direction_fresh_scoping"), "slice_ambiguity")
        self.assertEqual(normalize_operator_policy("advisory_before_operator"), "gate_24h")

        decision = classify_operator_candidate(
            control_text,
            control_meta={
                "status": "needs_operator",
                "control_seq": 133,
                "reason_code": "m30_direction_fresh_scoping",
                "operator_policy": "advisory_before_operator",
                "decision_class": "next_milestone_selection",
                "decision_required": "M30 direction — choose next milestone",
                "based_on_work": "work/4/24/2026-04-24-m29-release-gate-milestones.md",
                "based_on_verify": "verify/4/24/2026-04-24-m29-release-gate-milestones.md",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )
        marker = operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=133,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["reason_code"], "slice_ambiguity")
        self.assertEqual(decision["operator_policy"], "gate_24h")
        self.assertEqual(decision["decision_class"], "next_slice_selection")
        self.assertEqual(decision["classification_source"], "operator_policy")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertFalse(decision["operator_eligible"])
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker["routed_to"], "verify_followup")

    def test_next_direction_after_launcher_close_routes_to_verify_followup(self) -> None:
        control_text = (
            "STATUS: needs_operator\n"
            "CONTROL_SEQ: 290\n"
            "REASON_CODE: next_direction_after_launcher_close\n"
            "OPERATOR_POLICY: direction_selection_after_feature_complete\n"
            "DECISION_CLASS: milestone_direction\n"
            "DECISION_REQUIRED: confirm next priority — M44 publish, M45 start, or runtime hardening\n"
            "BASED_ON_WORK: work/4/26/2026-04-26-pipeline-launcher-hibernate-surface.md\n"
            "BASED_ON_VERIFY: verify/4/26/2026-04-26-pipeline-launcher-hibernate-surface.md\n"
        )

        self.assertEqual(normalize_reason_code("next_direction_after_launcher_close"), "slice_ambiguity")
        self.assertEqual(normalize_operator_policy("direction_selection_after_feature_complete"), "gate_24h")
        self.assertEqual(normalize_decision_class("milestone_direction"), "next_slice_selection")

        decision = classify_operator_candidate(
            control_text,
            control_meta={
                "status": "needs_operator",
                "control_seq": 290,
                "reason_code": "next_direction_after_launcher_close",
                "operator_policy": "direction_selection_after_feature_complete",
                "decision_class": "milestone_direction",
                "decision_required": "confirm next priority — M44 publish, M45 start, or runtime hardening",
                "based_on_work": "work/4/26/2026-04-26-pipeline-launcher-hibernate-surface.md",
                "based_on_verify": "verify/4/26/2026-04-26-pipeline-launcher-hibernate-surface.md",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )
        marker = operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=290,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["reason_code"], "slice_ambiguity")
        self.assertEqual(decision["operator_policy"], "gate_24h")
        self.assertEqual(decision["decision_class"], "next_slice_selection")
        self.assertEqual(decision["classification_source"], "operator_policy")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertFalse(decision["operator_eligible"])
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker["reason"], "slice_ambiguity")
        self.assertEqual(marker["routed_to"], "verify_followup")

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
        self.assertEqual(
            normalize_reason_code("m21_complete_push_and_pr_bundle"),
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
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

    def test_m21_publish_bundle_alias_routes_to_internal_verify_followup(self) -> None:
        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            "REASON_CODE: m21_complete_push_and_pr_bundle\n"
            "OPERATOR_POLICY: internal_only\n"
            "DECISION_CLASS: release_gate\n"
            "DECISION_REQUIRED: push branch and handle draft PR follow-up\n",
            control_meta={
                "status": "needs_operator",
                "reason_code": "m21_complete_push_and_pr_bundle",
                "operator_policy": "internal_only",
                "decision_class": "release_gate",
                "decision_required": "push branch and handle draft PR follow-up",
            },
            idle_stable=True,
            now_ts=1_000.0,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(
            decision["reason_code"],
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(decision["operator_policy"], "internal_only")
        self.assertEqual(decision["decision_class"], "release_gate")
        self.assertFalse(decision["operator_eligible"])

    def test_milestone_publish_bundle_authorization_routes_to_internal_followup(self) -> None:
        self.assertEqual(
            normalize_reason_code("m84_publish_bundle_authorization"),
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(normalize_decision_class("publish_authorization"), "release_gate")

        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            "CONTROL_SEQ: 1305\n"
            "REASON_CODE: m84_publish_bundle_authorization\n"
            "OPERATOR_POLICY: internal_only\n"
            "DECISION_CLASS: publish_authorization\n"
            "DECISION_REQUIRED: uncommitted M84 doc-sync + stale cancel guard branch commit push PR approval\n",
            control_meta={
                "status": "needs_operator",
                "control_seq": 1305,
                "reason_code": "m84_publish_bundle_authorization",
                "operator_policy": "internal_only",
                "decision_class": "publish_authorization",
                "decision_required": (
                    "uncommitted M84 doc-sync + stale cancel guard branch commit push PR approval"
                ),
            },
            idle_stable=True,
            now_ts=1_000.0,
        )

        marker = operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=1305,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(decision["reason_code"], COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON)
        self.assertEqual(decision["operator_policy"], "internal_only")
        self.assertEqual(decision["decision_class"], "release_gate")
        self.assertEqual(decision["classification_source"], "operator_policy")
        self.assertFalse(decision["operator_eligible"])
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker["reason"], COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON)
        self.assertEqual(marker["routed_to"], "verify_followup")

    def test_legacy_milestone_commit_push_doc_sync_routes_to_internal_followup(self) -> None:
        self.assertEqual(
            normalize_reason_code("m37_commit_push_milestones_doc_sync"),
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(
            normalize_operator_policy("pr_creation_gate + commit_push_bundle_authorization"),
            "internal_only",
        )
        self.assertEqual(normalize_decision_class("publication"), "release_gate")

        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            "CONTROL_SEQ: 216\n"
            "REASON_CODE: m37_commit_push_milestones_doc_sync\n"
            "OPERATOR_POLICY: pr_creation_gate + commit_push_bundle_authorization\n"
            "DECISION_CLASS: publication\n"
            "DECISION_REQUIRED: M37 Axis 2 commit + push + MILESTONES.md doc-sync approval\n",
            control_meta={
                "status": "needs_operator",
                "control_seq": 216,
                "reason_code": "m37_commit_push_milestones_doc_sync",
                "operator_policy": "pr_creation_gate + commit_push_bundle_authorization",
                "decision_class": "publication",
                "decision_required": "M37 Axis 2 commit + push + MILESTONES.md doc-sync approval",
            },
            idle_stable=True,
            now_ts=1_000.0,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(
            decision["reason_code"],
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(decision["operator_policy"], "internal_only")
        self.assertEqual(decision["decision_class"], "release_gate")
        self.assertEqual(decision["classification_source"], "operator_policy")
        self.assertFalse(decision["operator_eligible"])

    def test_b1_dirty_tree_release_gate_routes_to_internal_followup(self) -> None:
        self.assertEqual(
            normalize_reason_code("b1_release_gate_commit_authorization_dirty_tree"),
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(
            normalize_operator_policy("commit_push_bundle_authorization + pr_creation_gate"),
            "internal_only",
        )
        self.assertEqual(
            normalize_decision_class("commit_publish_authorization"),
            "release_gate",
        )

        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            "CONTROL_SEQ: 248\n"
            "REASON_CODE: b1_release_gate_commit_authorization_dirty_tree\n"
            "OPERATOR_POLICY: commit_push_bundle_authorization + pr_creation_gate\n"
            "DECISION_CLASS: commit_publish_authorization\n"
            "DECISION_REQUIRED: commit_scope + e2e_gate + pr_creation\n"
            "BASED_ON_WORK: work/4/26/2026-04-26-m42-deep-doc-bundle.md\n"
            "BASED_ON_VERIFY: verify/4/26/2026-04-26-m42-deep-doc-bundle.md\n",
            control_meta={
                "status": "needs_operator",
                "control_seq": 248,
                "reason_code": "b1_release_gate_commit_authorization_dirty_tree",
                "operator_policy": "commit_push_bundle_authorization + pr_creation_gate",
                "decision_class": "commit_publish_authorization",
                "decision_required": "commit_scope + e2e_gate + pr_creation",
                "based_on_work": "work/4/26/2026-04-26-m42-deep-doc-bundle.md",
                "based_on_verify": "verify/4/26/2026-04-26-m42-deep-doc-bundle.md",
            },
            idle_stable=True,
            now_ts=1_000.0,
        )

        marker = operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=248,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(
            decision["reason_code"],
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(decision["operator_policy"], "internal_only")
        self.assertEqual(decision["decision_class"], "release_gate")
        self.assertEqual(decision["classification_source"], "operator_policy")
        self.assertFalse(decision["operator_eligible"])
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker["routed_to"], "verify_followup")

    def test_ad_hoc_commit_push_pr_creation_bundle_routes_to_internal_followup(self) -> None:
        self.assertEqual(
            normalize_reason_code("commit_push_pr_creation_m68_bundle"),
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(
            normalize_operator_policy(
                "commit_push_bundle_authorization + pr_creation_gate + internal_only"
            ),
            "internal_only",
        )

        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            "CONTROL_SEQ: 1239\n"
            "REASON_CODE: commit_push_pr_creation_m68_bundle\n"
            "OPERATOR_POLICY: commit_push_bundle_authorization + pr_creation_gate + internal_only\n"
            "DECISION_CLASS: publish_boundary\n"
            "DECISION_REQUIRED: M68 commit + branch push + PR creation\n",
            control_meta={
                "status": "needs_operator",
                "control_seq": 1239,
                "reason_code": "commit_push_pr_creation_m68_bundle",
                "operator_policy": (
                    "commit_push_bundle_authorization + pr_creation_gate + internal_only"
                ),
                "decision_class": "publish_boundary",
                "decision_required": "M68 commit + branch push + PR creation",
            },
            idle_stable=True,
            now_ts=1_000.0,
        )

        marker = operator_gate_marker_from_decision(
            decision,
            control_file="operator_request.md",
            control_seq=1239,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(
            decision["reason_code"],
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(decision["operator_policy"], "internal_only")
        self.assertFalse(decision["operator_eligible"])
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker["reason"], COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON)
        self.assertEqual(marker["routed_to"], "verify_followup")

    def test_live_legacy_release_gate_file_resolves_via_shared_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            operator_path = Path(tmp) / ".pipeline" / "operator_request.md"
            operator_path.parent.mkdir(parents=True)
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 248\n"
                "REASON_CODE: b1_release_gate_commit_authorization_dirty_tree\n"
                "OPERATOR_POLICY: commit_push_bundle_authorization + pr_creation_gate\n"
                "DECISION_CLASS: commit_publish_authorization\n"
                "DECISION_REQUIRED: commit_scope + e2e_gate + pr_creation\n"
                "BASED_ON_WORK: work/4/26/2026-04-26-m42-deep-doc-bundle.md\n"
                "BASED_ON_VERIFY: verify/4/26/2026-04-26-m42-deep-doc-bundle.md\n",
                encoding="utf-8",
            )
            control_text = operator_path.read_text(encoding="utf-8")
            resolution = resolve_operator_control(
                control_text=control_text,
                control_meta=read_control_meta(operator_path),
                control_file="operator_request.md",
                control_path=str(operator_path),
                control_seq=248,
                control_mtime=operator_path.stat().st_mtime,
                idle_stable=True,
                now_ts=1_000.0,
            )

        decision = resolution["decision"]
        gate_marker = resolution["gate_marker"]
        stale_marker = resolution["stale_marker"]

        self.assertIsNone(stale_marker)
        self.assertIsInstance(decision, dict)
        self.assertIsInstance(gate_marker, dict)
        assert isinstance(decision, dict)
        assert isinstance(gate_marker, dict)
        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(
            decision["reason_code"],
            COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
        )
        self.assertEqual(decision["operator_policy"], "internal_only")
        self.assertEqual(decision["decision_class"], "release_gate")
        self.assertEqual(decision["classification_source"], "operator_policy")
        self.assertFalse(decision["operator_eligible"])
        self.assertEqual(gate_marker["routed_to"], "verify_followup")
        self.assertEqual(gate_marker["reason"], COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON)

    def test_compound_pr_creation_gate_policy_routes_to_verify_followup(self) -> None:
        self.assertEqual(
            normalize_operator_policy("pr_creation_gate + gate_24h + release_gate"),
            "gate_24h",
        )
        self.assertEqual(
            normalize_decision_class("publication release_gate"),
            "release_gate",
        )

        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            f"REASON_CODE: {PR_CREATION_GATE_REASON}\n"
            "OPERATOR_POLICY: pr_creation_gate + gate_24h + release_gate\n"
            "DECISION_CLASS: publication release_gate\n"
            "DECISION_REQUIRED: create draft PR for verified release bundle\n",
            control_meta={
                "status": "needs_operator",
                "reason_code": PR_CREATION_GATE_REASON,
                "operator_policy": "pr_creation_gate + gate_24h + release_gate",
                "decision_class": "publication release_gate",
                "decision_required": "create draft PR for verified release bundle",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        self.assertEqual(decision["mode"], "triage")
        self.assertEqual(decision["suppressed_mode"], "triage")
        self.assertEqual(decision["routed_to"], "verify_followup")
        self.assertEqual(decision["reason_code"], PR_CREATION_GATE_REASON)
        self.assertEqual(decision["operator_policy"], "gate_24h")
        self.assertEqual(decision["decision_class"], "release_gate")
        self.assertEqual(decision["classification_source"], "operator_policy")
        self.assertFalse(decision["operator_eligible"])

    def test_unknown_release_gate_metadata_still_fails_closed(self) -> None:
        decision = classify_operator_candidate(
            "STATUS: needs_operator\n"
            "REASON_CODE: m37_publish_bundle_unknown\n"
            "OPERATOR_POLICY: publication_review\n"
            "DECISION_CLASS: publication\n"
            "DECISION_REQUIRED: approve unknown publication boundary\n",
            control_meta={
                "status": "needs_operator",
                "reason_code": "m37_publish_bundle_unknown",
                "operator_policy": "publication_review",
                "decision_class": "publication",
                "decision_required": "approve unknown publication boundary",
            },
            idle_stable=True,
            now_ts=1_000.0,
        )

        self.assertEqual(decision["mode"], "needs_operator")
        self.assertEqual(decision["routed_to"], "operator")
        self.assertEqual(decision["operator_policy"], "immediate_publish")
        self.assertEqual(decision["decision_class"], "release_gate")
        self.assertEqual(decision["classification_source"], "metadata_fallback")
        self.assertTrue(decision["operator_eligible"])

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
        reason_code = normalize_reason_code(header.get("REASON_CODE", ""))
        if reason_code not in SUPPORTED_REASON_CODES:
            self.skipTest(f"Live file drift detected: REASON_CODE={reason_code!r}")
        self.assertIn(
            normalize_operator_policy(header.get("OPERATOR_POLICY", "")),
            SUPPORTED_OPERATOR_POLICIES,
        )
        self.assertIn(
            normalize_decision_class(header.get("DECISION_CLASS", "")),
            SUPPORTED_DECISION_CLASSES,
        )


if __name__ == "__main__":
    unittest.main()
