"""State dataclasses for the agent orchestration flow.

These replace scattered local variables in AgentLoop.handle() with
structured, typed objects that make state flow explicit and testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.contracts import (
    AnswerMode,
    FreshnessRisk,
    SearchIntentKind,
)
from core.request_intents import SearchIntentDecision


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Normalized user input, session state, permissions, uploaded files.

    Constructed once at the top of handle() and never mutated.
    """

    user_text: str
    session_id: str

    # Local file search
    search_query: str | None = None
    search_root: str | None = None
    uploaded_search_files: list[dict[str, Any]] | None = None
    has_search_request: bool = False

    # Session state
    active_context: dict[str, Any] | None = None
    web_search_permission: str = "disabled"

    # Source selection
    has_explicit_source_path: bool = False
    source_path: str | None = None
    uploaded_file: dict[str, Any] | None = None

    # Retry / feedback
    retry_feedback_reason: str | None = None
    load_web_search_record_id: str | None = None
    wants_web_search_record_recall: bool = False

    # Derived classifiers
    follow_up_intent: str = "general"
    active_context_mode: str = "none"


@dataclass(slots=True)
class SearchIntentResolution:
    """Resolved search intent with possible entity-reinvestigation override.

    Starts from SearchIntentDecision, then may be mutated once via
    apply_entity_reinvestigation(). After that, treat as frozen.
    """

    raw_decision: SearchIntentDecision

    # Explicit web search (derived from raw_decision, may be overridden)
    explicit_query: str | None = None
    effective_query: str | None = None
    probe_query: str | None = None
    intent_kind: str = SearchIntentKind.NONE
    answer_mode: str = AnswerMode.GENERAL
    freshness_risk: str = FreshnessRisk.LOW

    # Implicit / external fact (never overridden)
    implicit_web_search_query: str | None = None
    external_fact_query: str | None = None

    def apply_entity_reinvestigation(self, *, effective_query: str) -> None:
        """One-time override when entity reinvestigation is detected."""
        self.intent_kind = SearchIntentKind.EXTERNAL_FACT
        self.answer_mode = AnswerMode.ENTITY_CARD
        self.freshness_risk = FreshnessRisk.LOW
        self.probe_query = self.explicit_query
        self.effective_query = effective_query

    @classmethod
    def from_intent(
        cls,
        decision: SearchIntentDecision,
        *,
        web_search_permission: str = "disabled",
    ) -> SearchIntentResolution:
        """Construct from a raw SearchIntentDecision."""
        explicit_query = (
            decision.query if decision.kind == SearchIntentKind.EXPLICIT_WEB else None
        )
        implicit_query = (
            decision.query
            if web_search_permission == "enabled"
            and decision.kind == SearchIntentKind.LIVE_LATEST
            else None
        )
        external_fact_query = (
            decision.query if decision.kind == SearchIntentKind.EXTERNAL_FACT else None
        )
        return cls(
            raw_decision=decision,
            explicit_query=explicit_query,
            effective_query=explicit_query,
            probe_query=None,
            intent_kind=decision.kind,
            answer_mode=decision.answer_mode,
            freshness_risk=decision.freshness_risk,
            implicit_web_search_query=implicit_query,
            external_fact_query=external_fact_query,
        )
