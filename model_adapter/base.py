from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field


FOLLOW_UP_INTENT_GENERAL = "general"
FOLLOW_UP_INTENT_KEY_POINTS = "key_points"
FOLLOW_UP_INTENT_ACTION_ITEMS = "action_items"
FOLLOW_UP_INTENT_MEMO = "memo"


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
    def respond(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def summarize(self, text: str) -> str:
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
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> ModelRuntimeStatus:
        raise NotImplementedError

    def stream_respond(self, prompt: str) -> Iterator[ModelStreamEvent]:
        yield ModelStreamEvent(kind="text_replace", text=self.respond(prompt))

    def stream_summarize(self, text: str) -> Iterator[ModelStreamEvent]:
        yield ModelStreamEvent(kind="text_replace", text=self.summarize(text))

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
    ) -> Iterator[ModelStreamEvent]:
        yield ModelStreamEvent(
            kind="text_replace",
            text=self.answer_with_context(
                intent=intent,
                user_request=user_request,
                context_label=context_label,
                source_paths=source_paths,
                context_excerpt=context_excerpt,
                summary_hint=summary_hint,
                evidence_items=evidence_items,
            ),
        )
