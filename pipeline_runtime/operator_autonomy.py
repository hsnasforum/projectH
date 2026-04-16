from __future__ import annotations

import hashlib
import re
import time
from typing import Any, Iterable, Mapping

from .schema import iso_utc

OPERATOR_SUPPRESS_WINDOW_SEC = 24 * 60 * 60

_SPACE_RE = re.compile(r"\s+")
_NON_REASON_CODE_RE = re.compile(r"[^a-z0-9_]+")

_IMMEDIATE_REASON_CODES = {
    "safety_stop": {"mode": "needs_operator", "routed_to": "operator"},
    "approval_required": {"mode": "needs_operator", "routed_to": "operator"},
    "truth_sync_required": {"mode": "needs_operator", "routed_to": "operator"},
    "security_incident": {"mode": "needs_operator", "routed_to": "operator"},
    "destructive_risk": {"mode": "needs_operator", "routed_to": "operator"},
}

_GATED_REASON_CODES = {
    "context_exhaustion": {"mode": "triage", "routed_to": "codex_followup"},
    "session_rollover": {"mode": "triage", "routed_to": "codex_followup"},
    "continue_vs_switch": {"mode": "triage", "routed_to": "codex_followup"},
    "slice_ambiguity": {"mode": "triage", "routed_to": "codex_followup"},
    "auth_login_required": {"mode": "recovery", "routed_to": "codex_followup"},
    "provider_outage": {"mode": "triage", "routed_to": "codex_followup"},
    "receipt_repair": {"mode": "recovery", "routed_to": "codex_followup"},
    "verify_manifest_mismatch": {"mode": "recovery", "routed_to": "codex_followup"},
    "duplicate_handoff": {"mode": "recovery", "routed_to": "codex_followup"},
    "lane_recovery_exhausted": {"mode": "recovery", "routed_to": "codex_followup"},
    "session_missing": {"mode": "recovery", "routed_to": "codex_followup"},
}

_INTERNAL_REASON_CODES = {
    "codex_triage_only": {"mode": "triage", "routed_to": "codex_followup"},
    "gemini_tiebreak": {"mode": "triage", "routed_to": "codex_followup"},
    "waiting_next_control": {"mode": "hibernate", "routed_to": "hibernate"},
    "idle_hibernate": {"mode": "hibernate", "routed_to": "hibernate"},
}

_REASON_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
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
        "codex_triage_only",
        (
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


def normalize_reason_code(value: object) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    text = _NON_REASON_CODE_RE.sub("_", text)
    return text.strip("_")


def normalize_operator_policy(value: object) -> str:
    text = normalize_reason_code(value)
    aliases = {
        "immediate": "immediate_publish",
        "publish_now": "immediate_publish",
        "gate": "gate_24h",
        "gate24h": "gate_24h",
        "gate_24": "gate_24h",
        "internal": "internal_only",
        "suppress": "internal_only",
        "suppress_internal": "internal_only",
    }
    return aliases.get(text, text)


def normalize_decision_class(value: object) -> str:
    return normalize_reason_code(value)


def _match_reason(text: str) -> str:
    if not text:
        return ""
    for reason, markers in _REASON_RULES:
        if any(marker in text for marker in markers):
            return reason
    return ""


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
    turn_reason: str = "",
    degraded_reasons: Iterable[object] = (),
    lane_notes: Iterable[object] = (),
    idle_stable: bool = False,
    now_ts: float | None = None,
) -> dict[str, object]:
    now = time.time() if now_ts is None else now_ts
    first_seen_ts = control_mtime if control_mtime > 0 else now
    meta = _normalize_meta(control_meta)
    normalized = _normalize_text(
        [
            control_text,
            turn_reason,
            *list(degraded_reasons or []),
            *list(lane_notes or []),
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

    _default_policy, mode, routed_to = _reason_behavior(resolved_reason, idle_stable=idle_stable)
    if operator_policy == "immediate_publish":
        mode = "needs_operator"
        routed_to = "operator"
    elif operator_policy == "gate_24h":
        if resolved_reason in _IMMEDIATE_REASON_CODES:
            mode = "pending_operator"
            routed_to = "codex_followup"
    elif operator_policy == "internal_only":
        if resolved_reason in _IMMEDIATE_REASON_CODES:
            mode = "pending_operator"
            routed_to = "codex_followup"
        elif idle_stable and resolved_reason == "operator_candidate_pending":
            resolved_reason = "idle_hibernate"
            mode = "hibernate"
            routed_to = "hibernate"

    if operator_policy == "gate_24h":
        suppress_until_ts = first_seen_ts + OPERATOR_SUPPRESS_WINDOW_SEC
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

    fingerprint_source = "\n".join(
        [
            str(control_path or ".pipeline/operator_request.md"),
            str(control_seq),
            resolved_reason,
            operator_policy,
            decision_class,
            decision_required,
            based_on_work,
            based_on_verify,
            normalized,
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
        "first_seen_at": iso_utc(first_seen_ts),
        "suppress_operator_until": iso_utc(suppress_until_ts) if suppress_until_ts > 0 else "",
        "operator_eligible": operator_eligible,
        "publish_immediately": operator_policy == "immediate_publish",
        "routed_to": routed_to,
        "fingerprint": fingerprint,
    }
