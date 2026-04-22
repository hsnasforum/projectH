from __future__ import annotations

VERIFY_FOLLOWUP_ROUTE = "verify_followup"
LEGACY_CODEX_FOLLOWUP_ROUTE = "codex_followup"

VERIFY_TRIAGE_ESCALATION = "verify_triage"
LEGACY_CODEX_TRIAGE_ESCALATION = "codex_triage"

VERIFY_TRIAGE_ONLY_REASON = "verify_triage_only"
LEGACY_CODEX_TRIAGE_ONLY_REASON = "codex_triage_only"

IMPLEMENT_HANDOFF_NOTIFY = "implement_handoff"
LEGACY_CLAUDE_HANDOFF_NOTIFY = "claude_handoff"

ADVISORY_REQUEST_NOTIFY = "advisory_request"
LEGACY_GEMINI_REQUEST_NOTIFY = "gemini_request"

ADVISORY_ADVICE_FOLLOWUP_NOTIFY = "advisory_advice_followup"
LEGACY_GEMINI_ADVICE_FOLLOWUP_NOTIFY = "gemini_advice_followup"

ADVISORY_RECOVERY_NOTIFY = "advisory_recovery"
LEGACY_GEMINI_ADVISORY_RECOVERY_NOTIFY = "gemini_advisory_recovery"

VERIFY_FOLLOWUP_ROUTE_ALIASES = frozenset({
    VERIFY_FOLLOWUP_ROUTE,
    LEGACY_CODEX_FOLLOWUP_ROUTE,
})
VERIFY_TRIAGE_ESCALATION_ALIASES = frozenset({
    VERIFY_TRIAGE_ESCALATION,
    LEGACY_CODEX_TRIAGE_ESCALATION,
})
IMPLEMENT_HANDOFF_NOTIFY_ALIASES = frozenset({
    IMPLEMENT_HANDOFF_NOTIFY,
    LEGACY_CLAUDE_HANDOFF_NOTIFY,
})
ADVISORY_REQUEST_NOTIFY_ALIASES = frozenset({
    ADVISORY_REQUEST_NOTIFY,
    LEGACY_GEMINI_REQUEST_NOTIFY,
})
ADVISORY_ADVICE_FOLLOWUP_NOTIFY_ALIASES = frozenset({
    ADVISORY_ADVICE_FOLLOWUP_NOTIFY,
    LEGACY_GEMINI_ADVICE_FOLLOWUP_NOTIFY,
})
ADVISORY_RECOVERY_NOTIFY_ALIASES = frozenset({
    ADVISORY_RECOVERY_NOTIFY,
    LEGACY_GEMINI_ADVISORY_RECOVERY_NOTIFY,
})

_CANONICAL_NOTIFY_KIND_BY_LEGACY = {
    LEGACY_CLAUDE_HANDOFF_NOTIFY: IMPLEMENT_HANDOFF_NOTIFY,
    LEGACY_GEMINI_REQUEST_NOTIFY: ADVISORY_REQUEST_NOTIFY,
    LEGACY_GEMINI_ADVICE_FOLLOWUP_NOTIFY: ADVISORY_ADVICE_FOLLOWUP_NOTIFY,
    LEGACY_GEMINI_ADVISORY_RECOVERY_NOTIFY: ADVISORY_RECOVERY_NOTIFY,
}


def _clean_token(value: object) -> str:
    return str(value or "").strip().lower()


def normalize_notify_kind(value: object) -> str:
    token = _clean_token(value)
    return _CANONICAL_NOTIFY_KIND_BY_LEGACY.get(token, token)


def normalize_followup_route(value: object) -> str:
    token = _clean_token(value)
    if token == LEGACY_CODEX_FOLLOWUP_ROUTE:
        return VERIFY_FOLLOWUP_ROUTE
    return token


def is_verify_followup_route(value: object) -> bool:
    return normalize_followup_route(value) == VERIFY_FOLLOWUP_ROUTE


def normalize_verify_triage_escalation(value: object) -> str:
    token = _clean_token(value)
    if token == LEGACY_CODEX_TRIAGE_ESCALATION:
        return VERIFY_TRIAGE_ESCALATION
    return token


def is_verify_triage_escalation(value: object) -> bool:
    return normalize_verify_triage_escalation(value) == VERIFY_TRIAGE_ESCALATION


def normalize_verify_triage_reason(value: object) -> str:
    token = _clean_token(value)
    if token == LEGACY_CODEX_TRIAGE_ONLY_REASON:
        return VERIFY_TRIAGE_ONLY_REASON
    return token
