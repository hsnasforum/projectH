from __future__ import annotations

import hashlib
import re
import time
from typing import Iterable

from .schema import iso_utc

OPERATOR_SUPPRESS_WINDOW_SEC = 24 * 60 * 60

_IMMEDIATE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("safety_stop", ("safety_stop", "safety stop", "immediate safety stop")),
    ("approval_required", ("approval_required", "approval required", "approval blocker")),
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
)

_RECOVERY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("lane_broken", ("lane_broken", "lane broken")),
    ("session_missing", ("session_missing", "session missing")),
    ("receipt_verify_missing", ("receipt_verify_missing", "receipt verify missing")),
    ("receipt_manifest", ("receipt_manifest:",)),
    ("duplicate_handoff", ("duplicate_handoff", "handoff_already_completed")),
    (
        "auth_login",
        (
            "auth_login_required",
            "auth_login",
            "auth login",
            "please run /login",
            "invalid authentication credentials",
            "authentication_error",
        ),
    ),
)

_TRIAGE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
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
    ("provider_outage", ("provider_outage", "provider outage")),
)

_PENDING_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "real_operator_only",
        (
            "real operator-only decision",
            "real operator only decision",
            "operator-only decision",
            "operator only decision",
            "operator must decide",
        ),
    ),
)

_SPACE_RE = re.compile(r"\s+")


def _normalize_text(parts: Iterable[object]) -> str:
    text = "\n".join(str(part or "") for part in parts if str(part or "").strip()).lower()
    return _SPACE_RE.sub(" ", text).strip()


def _match_reason(text: str, rules: tuple[tuple[str, tuple[str, ...]], ...]) -> str:
    if not text:
        return ""
    for reason, markers in rules:
        if any(marker in text for marker in markers):
            return reason
    return ""


def classify_operator_candidate(
    control_text: str,
    *,
    control_path: str = ".pipeline/operator_request.md",
    control_seq: int = -1,
    control_mtime: float = 0.0,
    turn_reason: str = "",
    degraded_reasons: Iterable[object] = (),
    lane_notes: Iterable[object] = (),
    idle_stable: bool = False,
    now_ts: float | None = None,
) -> dict[str, object]:
    now = time.time() if now_ts is None else now_ts
    first_seen_ts = control_mtime if control_mtime > 0 else now
    normalized = _normalize_text(
        [
            control_text,
            turn_reason,
            *list(degraded_reasons or []),
            *list(lane_notes or []),
        ]
    )

    block_reason = _match_reason(normalized, _IMMEDIATE_RULES)
    immediate = bool(block_reason)
    mode = "needs_operator"
    routed_to = "operator"

    if not block_reason:
        block_reason = _match_reason(normalized, _RECOVERY_RULES)
        if block_reason:
            mode = "recovery"
            routed_to = "codex_followup"

    if not block_reason:
        block_reason = _match_reason(normalized, _TRIAGE_RULES)
        if block_reason:
            mode = "triage"
            routed_to = "codex_followup"

    if not block_reason and idle_stable:
        block_reason = "idle_stable"
        mode = "hibernate"
        routed_to = "hibernate"

    if not block_reason:
        pending_reason = _match_reason(normalized, _PENDING_RULES)
        block_reason = pending_reason or "operator_candidate_pending"
        mode = "pending_operator"
        routed_to = "codex_followup"

    suppress_until_ts = first_seen_ts if immediate else first_seen_ts + OPERATOR_SUPPRESS_WINDOW_SEC
    operator_eligible = immediate or now >= suppress_until_ts
    visible_mode = "needs_operator" if operator_eligible else mode
    if operator_eligible:
        routed_to = "operator"

    fingerprint_source = "\n".join(
        [
            str(control_path or ".pipeline/operator_request.md"),
            str(control_seq),
            block_reason,
            normalized,
        ]
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()

    return {
        "mode": visible_mode,
        "suppressed_mode": mode,
        "block_reason": block_reason,
        "first_seen_at": iso_utc(first_seen_ts),
        "suppress_operator_until": iso_utc(suppress_until_ts) if not immediate else "",
        "operator_eligible": operator_eligible,
        "publish_immediately": immediate,
        "routed_to": routed_to,
        "fingerprint": fingerprint,
    }
