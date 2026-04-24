from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Callable
from typing import Any, Iterable, Mapping

from .role_routes import (
    VERIFY_FOLLOWUP_ROUTE,
    VERIFY_TRIAGE_ONLY_REASON,
    normalize_verify_triage_reason,
)
from .schema import iso_utc

OPERATOR_SUPPRESS_WINDOW_SEC = 24 * 60 * 60
OPERATOR_APPROVAL_COMPLETED_REASON = "operator_approval_completed"
COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON = "commit_push_bundle_authorization"
PR_CREATION_GATE_REASON = "pr_creation_gate"
PR_MERGE_GATE_REASON = "pr_merge_gate"
PUBLICATION_BOUNDARY_REASON_CODES = frozenset({
    "pr_boundary",
    "publication_boundary",
    "external_publication_boundary",
    PR_MERGE_GATE_REASON,
})

_SPACE_RE = re.compile(r"\s+")
_NON_REASON_CODE_RE = re.compile(r"[^a-z0-9_]+")
_COMMIT_APPROVAL_MARKERS = ("commit", "커밋")
_PUSH_APPROVAL_MARKERS = ("push", "푸시")
_COMMIT_PUSH_APPROVAL_REASONS = frozenset(
    {"approval_required", COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON}
)
_LETTER_CHOICE_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?"
    r"(?:(?:option|choice|candidate|proposal|decision)\s*)?"
    r"([a-z])(?:[.)]|[:])(?:\s|$)"
)
_NUMBER_CHOICE_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?"
    r"(?:(?:option|choice|candidate|proposal|decision|선택지|후보|옵션|결정|안)\s*)?"
    r"(?:#\s*)?([1-9][0-9]?)(?:[.)]|[:]|안\b|번\b)(?:\s|$)"
)
_CIRCLED_CHOICE_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?"
    r"(?:(?:option|choice|candidate|proposal|decision|선택지|후보|옵션|결정|안)\s*)?"
    r"([①②③④⑤⑥⑦⑧⑨])(?:[.)]|[:])?(?:\s|$)"
)
_OPERATOR_CHOICE_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?operator\b[^\n]{0,80}?"
    r"\b([a-z]|[1-9][0-9]?|[①②③④⑤⑥⑦⑧⑨])(?:\b|[.)]|[:])"
)
_INLINE_LETTER_CHOICE_SET_RE = re.compile(r"(?i)\b[a-z](?:\s*/\s*[a-z]){1,5}\b")
_INLINE_NUMBER_CHOICE_SET_RE = re.compile(r"\b[1-9][0-9]?(?:\s*/\s*[1-9][0-9]?){1,5}\b")
_INLINE_KOREAN_CHOICE_SET_RE = re.compile(
    r"(?:[1-9][0-9]?\s*(?:안|번)|[①②③④⑤⑥⑦⑧⑨])"
    r"(?:\s*/\s*(?:[1-9][0-9]?\s*(?:안|번)|[①②③④⑤⑥⑦⑧⑨])){1,5}"
)
_INLINE_PAREN_CHOICE_LABEL_RE = re.compile(
    r"(?i)(?:^|[;,\n]\s*)\(([a-z]|[1-9][0-9]?|[①②③④⑤⑥⑦⑧⑨])\)"
)
_VOLATILE_CONTROL_LINE_RE = re.compile(
    r"(?i)^\s*"
    r"(?:status|control_seq|source|supersedes|updated_at|written_at|created_at|timestamp)"
    r"\b\s*:?.*$"
)
_WORK_PATH_RE = re.compile(r"(work/\d+/\d+/[^\s`]+\.md)")
_PR_NUMBER_RE = re.compile(
    r"(?i)(?:\bPR\s*#\s*|/pull/)([1-9][0-9]*)\b"
)
_CURRENT_PR_FIELD_KEYS = (
    "pr",
    "pr_number",
    "pr_url",
    "pull_request",
    "pull_request_number",
    "pull_request_url",
    "current_pr",
    "current_pr_number",
    "current_pr_url",
    "gate_pr",
    "gate_pr_number",
    "gate_pr_url",
    "merge_pr",
    "merge_pr_number",
    "merge_pr_url",
)
_CURRENT_PR_FIELD_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?`?"
    r"(?:PR|PR_NUMBER|PR_URL|PULL_REQUEST|PULL_REQUEST_NUMBER|PULL_REQUEST_URL|"
    r"CURRENT_PR|CURRENT_PR_NUMBER|CURRENT_PR_URL|GATE_PR|GATE_PR_NUMBER|GATE_PR_URL|"
    r"MERGE_PR|MERGE_PR_NUMBER|MERGE_PR_URL)"
    r"`?(?:\*\*)?\s*:\s*(?P<value>.*)$"
)
_CURRENT_PR_NUMBER_RE = re.compile(
    r"(?i)(?:\bPR\s*#\s*|#\s*|/pull/)([1-9][0-9]*)\b"
)
_BARE_PR_NUMBER_RE = re.compile(r"^\s*([1-9][0-9]*)\s*$")
_CHOICE_INTENT_MARKERS = (
    "choose",
    "pick",
    "select",
    "choice",
    "option",
    "candidate",
    "proposal",
    "decision",
    "택1",
    "선택",
    "선택지",
    "후보",
    "옵션",
    "결정",
    "고르",
    "정하",
)
_MENU_CHOICE_BLOCKER_MARKERS = (
    "safety_stop",
    "safety stop",
    "security_incident",
    "security incident",
    "destructive_risk",
    "destructive risk",
    "truth_sync_required",
    "truth sync required",
    "truth-sync required",
    "auth_login_required",
    "auth login",
    "login required",
    "invalid authentication credentials",
    "approval_record",
    "approval-record",
    "approval record",
    "approval record repair",
    "통과 후",
    "완료 후",
    "password",
    "credential",
    "secret",
    "api key",
    "token",
    "delete file",
    "remove file",
    "커밋",
    "commit",
    "push",
    "milestone",
    "마일스톤",
)
_CIRCLED_DIGITS = {
    "①": "1",
    "②": "2",
    "③": "3",
    "④": "4",
    "⑤": "5",
    "⑥": "6",
    "⑦": "7",
    "⑧": "8",
    "⑨": "9",
}

_IMMEDIATE_REASON_CODES = {
    "safety_stop": {"mode": "needs_operator", "routed_to": "operator"},
    "approval_required": {"mode": "needs_operator", "routed_to": "operator"},
    "truth_sync_required": {"mode": "needs_operator", "routed_to": "operator"},
    "security_incident": {"mode": "needs_operator", "routed_to": "operator"},
    "destructive_risk": {"mode": "needs_operator", "routed_to": "operator"},
    **{
        reason: {"mode": "needs_operator", "routed_to": "operator"}
        for reason in PUBLICATION_BOUNDARY_REASON_CODES
    },
}

_GATED_REASON_CODES = {
    "context_exhaustion": {"mode": "triage", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "session_rollover": {"mode": "triage", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "continue_vs_switch": {"mode": "triage", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "slice_ambiguity": {"mode": "triage", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "newer_unverified_work_present": {"mode": "recovery", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "auth_login_required": {"mode": "recovery", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "provider_outage": {"mode": "triage", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "receipt_repair": {"mode": "recovery", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "verify_manifest_mismatch": {"mode": "recovery", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "duplicate_handoff": {"mode": "recovery", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "lane_recovery_exhausted": {"mode": "recovery", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "session_missing": {"mode": "recovery", "routed_to": VERIFY_FOLLOWUP_ROUTE},
}

_INTERNAL_REASON_CODES = {
    VERIFY_TRIAGE_ONLY_REASON: {"mode": "triage", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON: {
        "mode": "triage",
        "routed_to": VERIFY_FOLLOWUP_ROUTE,
    },
    PR_CREATION_GATE_REASON: {
        "mode": "triage",
        "routed_to": VERIFY_FOLLOWUP_ROUTE,
    },
    "gemini_tiebreak": {"mode": "triage", "routed_to": VERIFY_FOLLOWUP_ROUTE},
    "waiting_next_control": {"mode": "hibernate", "routed_to": "hibernate"},
    "idle_hibernate": {"mode": "hibernate", "routed_to": "hibernate"},
}

_VERIFIED_BLOCKER_AUTO_RECOVERY_REASON_CODES = frozenset({"truth_sync_required"})

SUPPORTED_OPERATOR_POLICIES = frozenset({"immediate_publish", "gate_24h", "internal_only"})
SUPPORTED_REASON_CODES = frozenset(
    set(_IMMEDIATE_REASON_CODES)
    | set(_GATED_REASON_CODES)
    | set(_INTERNAL_REASON_CODES)
)
SUPPORTED_DECISION_CLASSES: frozenset[str] = frozenset(
    {
        "operator_only",
        "advisory_only",
        "next_slice_selection",
        "internal_only",
        "release_gate",
        "merge_gate",
        "truth_sync_scope",
        "red_test_family_scope_decision",
    }
)

_REASON_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("safety_stop", ("safety_stop", "safety stop", "immediate safety stop")),
    ("approval_required", ("approval_required", "approval required", "approval blocker")),
    (
        "external_publication_boundary",
        (
            "external_publication_boundary",
            "external publication boundary",
            "external publish boundary",
            "publication boundary",
            "pr boundary",
            "merge pr",
            "merge draft pr",
        ),
    ),
    (
        "truth_sync_required",
        (
            "truth_sync_required",
            "truth sync required",
            "truth-sync required",
            "truth_sync blocker",
            "truth-sync blocker",
            "truth sync blocker",
        ),
    ),
    ("security_incident", ("security_incident", "security incident")),
    ("destructive_risk", ("destructive_risk", "destructive risk")),
    ("context_exhaustion", ("context_exhaustion", "context exhaustion")),
    ("session_rollover", ("session_rollover", "session rollover")),
    ("continue_vs_switch", ("continue_vs_switch", "continue vs switch")),
    (
        "slice_ambiguity",
        (
            "slice_ambiguity",
            "slice ambiguity",
            "next-slice ambiguity",
            "overlapping candidates",
            "low-confidence prioritization",
        ),
    ),
    (
        "newer_unverified_work_present",
        (
            "newer_unverified_work_present",
            "newer unverified work present",
            "verify latest work first",
            "latest /work",
        ),
    ),
    (
        "auth_login_required",
        (
            "auth_login_required",
            "auth_login",
            "auth login",
            "please run /login",
            "invalid authentication credentials",
            "authentication_error",
        ),
    ),
    ("provider_outage", ("provider_outage", "provider outage")),
    ("receipt_repair", ("receipt_repair", "receipt verify missing", "receipt_verify_missing")),
    (
        "verify_manifest_mismatch",
        (
            "verify_manifest_mismatch",
            "receipt_manifest:",
            "verify manifest mismatch",
        ),
    ),
    ("duplicate_handoff", ("duplicate_handoff", "handoff_already_completed")),
    ("lane_recovery_exhausted", ("lane_recovery_exhausted", "lane_broken", "lane broken")),
    ("session_missing", ("session_missing", "session missing")),
    (
        VERIFY_TRIAGE_ONLY_REASON,
        (
            "verify_triage_only",
            "verify triage only",
            "codex_triage_only",
            "codex triage only",
            "forbidden_operator_menu",
            "handoff_not_actionable",
        ),
    ),
    ("gemini_tiebreak", ("gemini_tiebreak", "gemini tiebreak")),
    ("waiting_next_control", ("waiting_next_control", "waiting next control")),
    ("idle_hibernate", ("idle_hibernate", "idle stable", "still pending")),
)


def _normalize_text(parts: Iterable[object]) -> str:
    text = "\n".join(str(part or "") for part in parts if str(part or "").strip()).lower()
    return _SPACE_RE.sub(" ", text).strip()


def _strip_volatile_control_lines(value: object) -> str:
    lines = []
    for line in str(value or "").splitlines():
        if _VOLATILE_CONTROL_LINE_RE.match(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def _normalize_control_token(value: object) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    text = _NON_REASON_CODE_RE.sub("_", text)
    return text.strip("_")


def _raw_text(parts: Iterable[object]) -> str:
    return "\n".join(str(part or "") for part in parts if str(part or "").strip())


def normalize_reason_code(value: object) -> str:
    text = _normalize_control_token(value)
    compound_aliases = (
        (COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON, COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON),
        (PR_CREATION_GATE_REASON, PR_CREATION_GATE_REASON),
        (PR_MERGE_GATE_REASON, PR_MERGE_GATE_REASON),
    )
    for marker, canonical in compound_aliases:
        if text == marker or text.startswith(f"{marker}_") or text.endswith(f"_{marker}") or f"_{marker}_" in text:
            return canonical
    aliases = {
        "branch_commit_and_milestone_transition": "approval_required",
        "branch_commit_milestone_transition": "approval_required",
        "branch_complete_pending_milestone_transition": "approval_required",
        "gemini_axis_switch_without_exact_slice": "slice_ambiguity",
        "m21_complete_push_and_pr_bundle": COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
    }
    return normalize_verify_triage_reason(aliases.get(text, text))


def normalize_operator_policy(value: object) -> str:
    text = _normalize_control_token(value)
    aliases = {
        "immediate": "immediate_publish",
        "publish_now": "immediate_publish",
        "branch_complete_pending_milestone_transition": "gate_24h",
        "stop_until_operator_decision": "immediate_publish",
        "gate": "gate_24h",
        "gate24h": "gate_24h",
        "gate_24": "gate_24h",
        "stop_until_truth_sync": "gate_24h",
        "stop_until_exact_slice_selected": "gate_24h",
        "stop_until_exact_slice_selection": "gate_24h",
        "internal": "internal_only",
        "suppress": "internal_only",
        "suppress_internal": "internal_only",
    }
    return aliases.get(text, text)


def normalize_decision_class(value: object) -> str:
    text = _normalize_control_token(value)
    if (
        text == "next_milestone_selection"
        or text.startswith("next_milestone_selection_")
        or text.endswith("_next_milestone_selection")
        or "_next_milestone_selection_" in text
        or text == "branch_strategy"
        or text.startswith("branch_strategy_")
        or text.endswith("_branch_strategy")
        or "_branch_strategy_" in text
    ):
        return "next_slice_selection"
    aliases = {
        "branch_closure_and_milestone_transition": "operator_only",
        "branch_complete_pending_milestone_transition": "operator_only",
    }
    return aliases.get(text, text)


def allows_verified_blocker_auto_recovery(control_meta: Mapping[str, Any] | None = None) -> bool:
    meta = _normalize_meta(control_meta)
    reason_code = normalize_reason_code(meta.get("reason_code"))
    return reason_code in _VERIFIED_BLOCKER_AUTO_RECOVERY_REASON_CODES


def _default_normalize_artifact_path(value: object) -> str:
    return str(value or "").strip().replace("\\", "/")


def referenced_operator_work_paths(
    control_text: object,
    control_meta: Mapping[str, Any] | None = None,
    *,
    normalize_path: Callable[[object], str] | None = None,
) -> list[str]:
    """Return normalized /work paths referenced by an operator control."""
    normalize = normalize_path or _default_normalize_artifact_path
    meta = _normalize_meta(control_meta)
    based_on_work = normalize(meta.get("based_on_work"))
    if based_on_work:
        return [based_on_work]
    return sorted(
        {
            normalize(match.group(1))
            for match in _WORK_PATH_RE.finditer(str(control_text or ""))
            if normalize(match.group(1))
        }
    )


def _append_pr_numbers_from_field_value(
    numbers: list[int],
    seen: set[int],
    value: object,
) -> None:
    text = str(value or "").strip()
    if not text:
        return
    matched = False
    for match in _CURRENT_PR_NUMBER_RE.finditer(text):
        try:
            number = int(match.group(1))
        except (TypeError, ValueError):
            continue
        matched = True
        if number <= 0 or number in seen:
            continue
        numbers.append(number)
        seen.add(number)
    if matched:
        return
    bare_match = _BARE_PR_NUMBER_RE.match(text)
    if not bare_match:
        return
    try:
        number = int(bare_match.group(1))
    except (TypeError, ValueError):
        return
    if number > 0 and number not in seen:
        numbers.append(number)
        seen.add(number)


def _current_operator_pr_numbers(
    control_text: object,
    control_meta: Mapping[str, Any] | None = None,
) -> list[int]:
    meta = _normalize_meta(control_meta)
    numbers: list[int] = []
    seen: set[int] = set()
    for key in _CURRENT_PR_FIELD_KEYS:
        _append_pr_numbers_from_field_value(numbers, seen, meta.get(key))
    for match in _CURRENT_PR_FIELD_LINE_RE.finditer(str(control_text or "")):
        _append_pr_numbers_from_field_value(numbers, seen, match.group("value"))
    return numbers


def referenced_operator_pr_numbers(
    control_text: object,
    control_meta: Mapping[str, Any] | None = None,
) -> list[int]:
    """Return PR numbers referenced by an operator control."""
    meta = _normalize_meta(control_meta)
    current_numbers = _current_operator_pr_numbers(control_text, meta)
    if current_numbers:
        return current_numbers
    text = _raw_text(
        [
            meta.get("decision_required"),
            control_text,
        ]
    )
    numbers: list[int] = []
    seen: set[int] = set()
    for match in _PR_NUMBER_RE.finditer(text):
        try:
            number = int(match.group(1))
        except (TypeError, ValueError):
            continue
        if number <= 0 or number in seen:
            continue
        numbers.append(number)
        seen.add(number)
    return numbers


def evaluate_stale_operator_control(
    *,
    control_text: object,
    control_meta: Mapping[str, Any] | None,
    verified_work_paths: Iterable[object],
    completed_pr_numbers: Iterable[object] = (),
    mismatched_pr_numbers: Iterable[object] = (),
    control_file: str,
    control_seq: int,
    normalize_path: Callable[[object], str] | None = None,
    turn_state_name: str = "",
    turn_reason: str = "",
    turn_control_seq: int = -1,
) -> dict[str, object] | None:
    """Classify operator controls that can safely route back to verify follow-up.

    The helper is intentionally pure so watcher and supervisor use the same
    recovery boundary while keeping their own file/status/event plumbing thin.
    """
    normalize = normalize_path or _default_normalize_artifact_path
    meta = _normalize_meta(control_meta)

    if (
        str(turn_state_name or "") == "VERIFY_FOLLOWUP"
        and str(turn_reason or "") == OPERATOR_APPROVAL_COMPLETED_REASON
        and int(turn_control_seq or -1) == int(control_seq or -1)
    ):
        return {
            "control_file": control_file,
            "control_seq": control_seq,
            "reason": OPERATOR_APPROVAL_COMPLETED_REASON,
            "resolved_work_paths": [],
        }

    completed_prs: set[int] = set()
    for value in completed_pr_numbers:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number > 0:
            completed_prs.add(number)
    mismatched_prs: set[int] = set()
    for value in mismatched_pr_numbers:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number > 0:
            mismatched_prs.add(number)
    if normalize_reason_code(meta.get("reason_code")) == PR_MERGE_GATE_REASON and (completed_prs or mismatched_prs):
        referenced_prs = referenced_operator_pr_numbers(control_text, meta)
        resolved_prs = [number for number in referenced_prs if number in completed_prs]
        if resolved_prs:
            return {
                "control_file": control_file,
                "control_seq": control_seq,
                "reason": "pr_merge_completed",
                "resolved_work_paths": [],
                "resolved_pr_numbers": resolved_prs,
            }
        mismatched = [number for number in referenced_prs if number in mismatched_prs]
        if mismatched:
            return {
                "control_file": control_file,
                "control_seq": control_seq,
                "reason": "pr_merge_head_mismatch",
                "resolved_work_paths": [],
                "resolved_pr_numbers": mismatched,
            }

    referenced_work_paths = referenced_operator_work_paths(
        control_text,
        meta,
        normalize_path=normalize,
    )
    retriage_active = (
        str(turn_state_name or "") == "VERIFY_FOLLOWUP"
        and str(turn_reason or "") == "operator_wait_idle_retriage"
    )
    auto_recovery_allowed = allows_verified_blocker_auto_recovery(meta)
    has_structured_operator_contract = any(
        str(meta.get(key) or "").strip()
        for key in ("reason_code", "operator_policy", "decision_class", "based_on_work")
    )

    if not referenced_work_paths:
        if retriage_active:
            return {
                "control_file": control_file,
                "control_seq": control_seq,
                "reason": "operator_wait_idle_retriage",
                "resolved_work_paths": [],
            }
        return None

    if has_structured_operator_contract and not auto_recovery_allowed and not retriage_active:
        return None

    verified_paths = {normalize(path) for path in verified_work_paths if normalize(path)}
    unresolved = [path for path in referenced_work_paths if path not in verified_paths]
    if unresolved:
        if retriage_active:
            return {
                "control_file": control_file,
                "control_seq": control_seq,
                "reason": "operator_wait_idle_retriage",
                "resolved_work_paths": [],
            }
        return None

    return {
        "control_file": control_file,
        "control_seq": control_seq,
        "reason": "verified_blockers_resolved",
        "resolved_work_paths": referenced_work_paths,
    }


def operator_gate_marker_from_decision(
    decision: Mapping[str, Any],
    *,
    control_file: str,
    control_seq: int,
    fingerprint: str | None = None,
) -> dict[str, object] | None:
    """Return the shared watcher/supervisor marker for a gated operator stop."""
    routed_to = str(decision.get("routed_to") or "")
    mode = str(decision.get("suppressed_mode") or decision.get("mode") or "")
    if routed_to == "operator" or mode == "needs_operator":
        return None
    if bool(decision.get("operator_eligible")):
        return None
    return {
        "control_file": control_file,
        "control_seq": control_seq,
        "reason": str(decision.get("block_reason") or ""),
        "reason_code": str(decision.get("reason_code") or ""),
        "operator_policy": str(decision.get("operator_policy") or ""),
        "decision_class": str(decision.get("decision_class") or ""),
        "classification_source": str(decision.get("classification_source") or ""),
        "mode": str(decision.get("suppressed_mode") or decision.get("mode") or ""),
        "routed_to": str(decision.get("routed_to") or ""),
        "suppress_operator_until": str(decision.get("suppress_operator_until") or ""),
        "fingerprint": str(fingerprint if fingerprint is not None else decision.get("fingerprint") or ""),
    }


def is_commit_push_approval_stop(
    control_meta: Mapping[str, Any] | None,
    *,
    control_text: object = "",
) -> bool:
    """Return true for structured stops that ask for commit and push approval."""
    meta = _normalize_meta(control_meta)
    status = str(meta.get("status") or "").strip()
    if status and status != "needs_operator":
        return False
    if normalize_reason_code(meta.get("reason_code")) not in _COMMIT_PUSH_APPROVAL_REASONS:
        return False

    searchable = _normalize_text(
        [
            meta.get("decision_required"),
            control_text,
        ]
    )
    if not searchable:
        return False
    return (
        any(marker in searchable for marker in _COMMIT_APPROVAL_MARKERS)
        and any(marker in searchable for marker in _PUSH_APPROVAL_MARKERS)
    )


def _match_reason(text: str) -> str:
    if not text:
        return ""
    for reason, markers in _REASON_RULES:
        if any(marker in text for marker in markers):
            return reason
    return ""


def _choice_key(value: str) -> str:
    text = str(value or "").strip().lower()
    return _CIRCLED_DIGITS.get(text, text)


def _looks_like_agent_resolvable_choice_menu(text: str, *, blocker_text: str = "") -> bool:
    if not text:
        return False
    normalized_blocker_text = _normalize_text([blocker_text or text])
    if any(marker in normalized_blocker_text for marker in _MENU_CHOICE_BLOCKER_MARKERS):
        return False
    normalized = _normalize_text([text])

    option_keys = {
        _choice_key(match.group(1))
        for regex in (
            _LETTER_CHOICE_LINE_RE,
            _NUMBER_CHOICE_LINE_RE,
            _CIRCLED_CHOICE_LINE_RE,
            _OPERATOR_CHOICE_LINE_RE,
        )
        for match in regex.finditer(text)
    }
    if len(option_keys) >= 2:
        return True
    paren_option_keys = {
        _choice_key(match.group(1))
        for match in _INLINE_PAREN_CHOICE_LABEL_RE.finditer(text)
    }
    if len(paren_option_keys) >= 2:
        return True
    has_choice_intent = any(marker in normalized for marker in _CHOICE_INTENT_MARKERS)
    if not has_choice_intent:
        return False
    return any(
        regex.search(text)
        for regex in (
            _INLINE_LETTER_CHOICE_SET_RE,
            _INLINE_NUMBER_CHOICE_SET_RE,
            _INLINE_KOREAN_CHOICE_SET_RE,
        )
    )


def _reason_behavior(reason_code: str, *, idle_stable: bool) -> tuple[str, str, str]:
    if reason_code in _IMMEDIATE_REASON_CODES:
        behavior = _IMMEDIATE_REASON_CODES[reason_code]
        return "immediate_publish", str(behavior["mode"]), str(behavior["routed_to"])
    if reason_code in _GATED_REASON_CODES:
        behavior = _GATED_REASON_CODES[reason_code]
        return "gate_24h", str(behavior["mode"]), str(behavior["routed_to"])
    if reason_code in _INTERNAL_REASON_CODES:
        behavior = _INTERNAL_REASON_CODES[reason_code]
        return "internal_only", str(behavior["mode"]), str(behavior["routed_to"])
    if idle_stable:
        return "internal_only", "hibernate", "hibernate"
    return "immediate_publish", "needs_operator", "operator"


def _normalize_meta(meta: Mapping[str, Any] | None) -> dict[str, Any]:
    lowered: dict[str, Any] = {}
    for key, value in dict(meta or {}).items():
        lowered[str(key).strip().lower()] = value
    return lowered


def classify_operator_candidate(
    control_text: str,
    *,
    control_meta: Mapping[str, Any] | None = None,
    control_path: str = ".pipeline/operator_request.md",
    control_seq: int = -1,
    control_mtime: float = 0.0,
    first_seen_ts: float | None = None,
    turn_reason: str = "",
    degraded_reasons: Iterable[object] = (),
    lane_notes: Iterable[object] = (),
    idle_stable: bool = False,
    now_ts: float | None = None,
) -> dict[str, object]:
    now = time.time() if now_ts is None else now_ts
    resolved_first_seen_ts = first_seen_ts if first_seen_ts and first_seen_ts > 0 else (
        control_mtime if control_mtime > 0 else now
    )
    meta = _normalize_meta(control_meta)
    degraded_reason_parts = list(degraded_reasons or [])
    lane_note_parts = list(lane_notes or [])
    normalized = _normalize_text(
        [
            control_text,
            turn_reason,
            *degraded_reason_parts,
            *lane_note_parts,
        ]
    )
    semantic_normalized = _normalize_text(
        [
            _strip_volatile_control_lines(control_text),
            _strip_volatile_control_lines(turn_reason),
            *(_strip_volatile_control_lines(part) for part in degraded_reason_parts),
            *(_strip_volatile_control_lines(part) for part in lane_note_parts),
        ]
    )

    raw_reason_code = str(meta.get("reason_code") or "").strip()
    raw_operator_policy = str(meta.get("operator_policy") or "").strip()
    has_reason_code = bool(raw_reason_code)
    has_operator_policy = bool(raw_operator_policy)

    reason_code = normalize_reason_code(raw_reason_code)
    operator_policy = normalize_operator_policy(raw_operator_policy)
    decision_class = normalize_decision_class(meta.get("decision_class"))
    decision_required = str(meta.get("decision_required") or "").strip()
    based_on_work = str(meta.get("based_on_work") or "").strip()
    based_on_verify = str(meta.get("based_on_verify") or "").strip()
    legacy_reason_code = _match_reason(normalized)

    classification_source = ""
    if operator_policy in {"immediate_publish", "gate_24h", "internal_only"}:
        classification_source = "operator_policy"
        resolved_reason = reason_code or legacy_reason_code or ("idle_hibernate" if idle_stable else "operator_candidate_pending")
    elif reason_code in _IMMEDIATE_REASON_CODES or reason_code in _GATED_REASON_CODES or reason_code in _INTERNAL_REASON_CODES:
        classification_source = "reason_code"
        resolved_reason = reason_code
        operator_policy, _mode_hint, _route_hint = _reason_behavior(resolved_reason, idle_stable=idle_stable)
    elif has_operator_policy or has_reason_code:
        classification_source = "metadata_fallback"
        operator_policy = "immediate_publish"
        resolved_reason = legacy_reason_code or reason_code or "operator_candidate_pending"
    else:
        classification_source = "metadata_missing_fallback"
        operator_policy = "immediate_publish"
        resolved_reason = legacy_reason_code or ("idle_hibernate" if idle_stable else "operator_candidate_pending")

    menu_choice_text = _raw_text(
        [
            control_text,
            decision_required,
            turn_reason,
            *degraded_reason_parts,
            *lane_note_parts,
        ]
    )
    menu_blocker_text = _raw_text(
        [
            decision_required,
            turn_reason,
            *degraded_reason_parts,
            *lane_note_parts,
        ]
    )
    if (
        operator_policy == "gate_24h"
        and resolved_reason in {"approval_required", "operator_candidate_pending"}
        and decision_class in {"", "operator_only", "next_slice_selection"}
        and _looks_like_agent_resolvable_choice_menu(
            menu_choice_text,
            blocker_text=menu_blocker_text,
        )
    ):
        resolved_reason = "slice_ambiguity"
        decision_class = "next_slice_selection"

    _default_policy, mode, routed_to = _reason_behavior(resolved_reason, idle_stable=idle_stable)
    if operator_policy == "immediate_publish":
        mode = "needs_operator"
        routed_to = "operator"
    elif operator_policy == "gate_24h":
        if resolved_reason in _IMMEDIATE_REASON_CODES:
            mode = "needs_operator"
            routed_to = "operator"
    elif operator_policy == "internal_only":
        if resolved_reason == PR_MERGE_GATE_REASON:
            mode = "triage"
            routed_to = VERIFY_FOLLOWUP_ROUTE
        elif resolved_reason in _IMMEDIATE_REASON_CODES:
            mode = "needs_operator"
            routed_to = "operator"
        elif (
            decision_class == "next_slice_selection"
            and resolved_reason == "waiting_next_control"
        ):
            mode = "triage"
            routed_to = VERIFY_FOLLOWUP_ROUTE
        elif idle_stable and resolved_reason == "operator_candidate_pending":
            resolved_reason = "idle_hibernate"
            mode = "hibernate"
            routed_to = "hibernate"

    if operator_policy == "gate_24h" and routed_to != "operator":
        suppress_until_ts = resolved_first_seen_ts + OPERATOR_SUPPRESS_WINDOW_SEC
        operator_eligible = now >= suppress_until_ts
    elif operator_policy == "internal_only":
        suppress_until_ts = 0.0
        operator_eligible = False
    else:
        suppress_until_ts = 0.0
        operator_eligible = True

    visible_mode = "needs_operator" if operator_eligible else mode
    if operator_eligible:
        routed_to = "operator"
    if not decision_class:
        if visible_mode == "needs_operator":
            decision_class = "operator_only"
        elif visible_mode == "pending_operator":
            decision_class = "operator_only"
        elif visible_mode == "triage":
            decision_class = "next_slice_selection"
        elif visible_mode == "hibernate":
            decision_class = "internal_only"

    fingerprint_source = "\n".join(
        [
            str(control_path or ".pipeline/operator_request.md"),
            resolved_reason,
            operator_policy,
            decision_class,
            decision_required,
            based_on_work,
            based_on_verify,
            semantic_normalized,
        ]
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()

    return {
        "mode": visible_mode,
        "suppressed_mode": mode,
        "block_reason": resolved_reason,
        "reason_code": resolved_reason,
        "operator_policy": operator_policy,
        "decision_class": decision_class,
        "decision_required": decision_required,
        "based_on_work": based_on_work,
        "based_on_verify": based_on_verify,
        "classification_source": classification_source,
        "first_seen_at": iso_utc(resolved_first_seen_ts),
        "suppress_operator_until": iso_utc(suppress_until_ts) if suppress_until_ts > 0 else "",
        "operator_eligible": operator_eligible,
        "publish_immediately": operator_policy == "immediate_publish",
        "routed_to": routed_to,
        "fingerprint": fingerprint,
    }
