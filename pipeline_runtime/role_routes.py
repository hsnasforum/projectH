from __future__ import annotations

from typing import NamedTuple


class RouteSpec(NamedTuple):
    canonical: str
    aliases: frozenset[str]


LEGACY_CODEX_FOLLOWUP_ROUTE = "codex_followup"
LEGACY_CODEX_TRIAGE_ESCALATION = "codex_triage"
LEGACY_CODEX_TRIAGE_ONLY_REASON = "codex_triage_only"
LEGACY_CLAUDE_HANDOFF_NOTIFY = "claude_handoff"
LEGACY_GEMINI_REQUEST_NOTIFY = "gemini_request"
LEGACY_GEMINI_ADVICE_FOLLOWUP_NOTIFY = "gemini_advice_followup"
LEGACY_GEMINI_ADVISORY_RECOVERY_NOTIFY = "gemini_advisory_recovery"


VERIFY_FOLLOWUP = RouteSpec(
    "verify_followup",
    frozenset({"verify_followup", LEGACY_CODEX_FOLLOWUP_ROUTE}),
)
VERIFY_TRIAGE = RouteSpec(
    "verify_triage",
    frozenset({"verify_triage", LEGACY_CODEX_TRIAGE_ESCALATION}),
)
VERIFY_TRIAGE_ONLY = RouteSpec(
    "verify_triage_only",
    frozenset({"verify_triage_only", LEGACY_CODEX_TRIAGE_ONLY_REASON}),
)
IMPLEMENT_HANDOFF = RouteSpec(
    "implement_handoff",
    frozenset({"implement_handoff", LEGACY_CLAUDE_HANDOFF_NOTIFY}),
)
ADVISORY_REQUEST = RouteSpec(
    "advisory_request",
    frozenset({"advisory_request", LEGACY_GEMINI_REQUEST_NOTIFY}),
)
ADVISORY_ADVICE_FOLLOWUP = RouteSpec(
    "advisory_advice_followup",
    frozenset({"advisory_advice_followup", LEGACY_GEMINI_ADVICE_FOLLOWUP_NOTIFY}),
)
ADVISORY_RECOVERY = RouteSpec(
    "advisory_recovery",
    frozenset({"advisory_recovery", LEGACY_GEMINI_ADVISORY_RECOVERY_NOTIFY}),
)

VERIFY_FOLLOWUP_ROUTE = VERIFY_FOLLOWUP.canonical
VERIFY_TRIAGE_ESCALATION = VERIFY_TRIAGE.canonical
VERIFY_TRIAGE_ONLY_REASON = VERIFY_TRIAGE_ONLY.canonical
IMPLEMENT_HANDOFF_NOTIFY = IMPLEMENT_HANDOFF.canonical
ADVISORY_REQUEST_NOTIFY = ADVISORY_REQUEST.canonical
ADVISORY_ADVICE_FOLLOWUP_NOTIFY = ADVISORY_ADVICE_FOLLOWUP.canonical
ADVISORY_RECOVERY_NOTIFY = ADVISORY_RECOVERY.canonical

VERIFY_FOLLOWUP_ROUTE_ALIASES = VERIFY_FOLLOWUP.aliases
VERIFY_TRIAGE_ESCALATION_ALIASES = VERIFY_TRIAGE.aliases
VERIFY_TRIAGE_ONLY_REASON_ALIASES = VERIFY_TRIAGE_ONLY.aliases
IMPLEMENT_HANDOFF_NOTIFY_ALIASES = IMPLEMENT_HANDOFF.aliases
ADVISORY_REQUEST_NOTIFY_ALIASES = ADVISORY_REQUEST.aliases
ADVISORY_ADVICE_FOLLOWUP_NOTIFY_ALIASES = ADVISORY_ADVICE_FOLLOWUP.aliases
ADVISORY_RECOVERY_NOTIFY_ALIASES = ADVISORY_RECOVERY.aliases

_CANONICAL_NOTIFY_KIND_BY_LEGACY = {
    LEGACY_CODEX_FOLLOWUP_ROUTE: VERIFY_FOLLOWUP_ROUTE,
    LEGACY_CODEX_TRIAGE_ESCALATION: VERIFY_TRIAGE_ESCALATION,
    LEGACY_CODEX_TRIAGE_ONLY_REASON: VERIFY_TRIAGE_ONLY_REASON,
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


def _normalize_route_alias(value: object, spec: RouteSpec) -> str:
    token = _clean_token(value)
    if token in spec.aliases:
        return spec.canonical
    return token


def normalize_followup_route(value: object) -> str:
    return _normalize_route_alias(value, VERIFY_FOLLOWUP)


def is_verify_followup_route(value: object) -> bool:
    return normalize_followup_route(value) == VERIFY_FOLLOWUP_ROUTE


def normalize_verify_triage_escalation(value: object) -> str:
    return _normalize_route_alias(value, VERIFY_TRIAGE)


def is_verify_triage_escalation(value: object) -> bool:
    return normalize_verify_triage_escalation(value) == VERIFY_TRIAGE_ESCALATION


def normalize_verify_triage_reason(value: object) -> str:
    return _normalize_route_alias(value, VERIFY_TRIAGE_ONLY)
