from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field

from core.contracts import FollowUpIntent, StreamEventType

# Re-export for backward compatibility with existing importers
FOLLOW_UP_INTENT_GENERAL = FollowUpIntent.GENERAL
FOLLOW_UP_INTENT_KEY_POINTS = FollowUpIntent.KEY_POINTS
FOLLOW_UP_INTENT_ACTION_ITEMS = FollowUpIntent.ACTION_ITEMS
FOLLOW_UP_INTENT_MEMO = FollowUpIntent.MEMO


@dataclass(slots=True)
class SummaryNoteDraft:
    title: str
    summary: str
    note_body: str


@dataclass(slots=True)
class ModelStreamEvent:
    kind: str
    text: str


@dataclass(slots=True)
class ModelRuntimeStatus:
    provider: str
    configured_model: str
    reachable: bool
    configured_model_available: bool
    detail: str
    base_url: str | None = None
    version: str | None = None
    available_models: list[str] = field(default_factory=list)


class ModelAdapterError(RuntimeError):
    pass


class ModelAdapter(ABC):
    @abstractmethod
    def respond(self, prompt: str, *, active_preferences: list[dict[str, str]] | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def summarize(self, text: str, *, active_preferences: list[dict[str, str]] | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_summary_note(self, *, source_path: str, text: str) -> SummaryNoteDraft:
        raise NotImplementedError

    @abstractmethod
    def answer_with_context(
        self,
        *,
        intent: str,
        user_request: str,
        context_label: str,
        source_paths: list[str],
        context_excerpt: str,
        summary_hint: str | None = None,
        evidence_items: list[dict[str, str]] | None = None,
        active_preferences: list[dict[str, str]] | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> ModelRuntimeStatus:
        raise NotImplementedError

    def review_draft(self, *, draft: str, user_request: str, context_hint: str = "") -> str | None:
        """Review a draft with a stronger model. Returns corrected text or None if OK."""
        return None

    def stream_respond(self, prompt: str, *, active_preferences: list[dict[str, str]] | None = None) -> Iterator[ModelStreamEvent]:
        yield ModelStreamEvent(kind=StreamEventType.TEXT_REPLACE, text=self.respond(prompt, active_preferences=active_preferences))

    def stream_summarize(
        self, text: str, *, active_preferences: list[dict[str, str]] | None = None
    ) -> Iterator[ModelStreamEvent]:
        yield ModelStreamEvent(
            kind=StreamEventType.TEXT_REPLACE,
            text=self.summarize(text, active_preferences=active_preferences),
        )

    def stream_answer_with_context(
        self,
        *,
        intent: str,
        user_request: str,
        context_label: str,
        source_paths: list[str],
        context_excerpt: str,
        summary_hint: str | None = None,
        evidence_items: list[dict[str, str]] | None = None,
        active_preferences: list[dict[str, str]] | None = None,
    ) -> Iterator[ModelStreamEvent]:
        yield ModelStreamEvent(
            kind=StreamEventType.TEXT_REPLACE,
            text=self.answer_with_context(
                intent=intent,
                user_request=user_request,
                context_label=context_label,
                source_paths=source_paths,
                context_excerpt=context_excerpt,
                summary_hint=summary_hint,
                evidence_items=evidence_items,
                active_preferences=active_preferences,
            ),
        )
