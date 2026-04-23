from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory

from core.agent_loop import AgentLoop, UserRequest, _NoOpContext
from core.contracts import AnswerMode, StreamEventType
from core.models import RequestContext
from model_adapter.base import ModelStreamEvent
from model_adapter.ollama import OllamaModelAdapter
from model_adapter.router import ModelConfig
from storage.session_store import SessionStore
from storage.task_log import TaskLogger


class _RecordingOllamaAdapter(OllamaModelAdapter):
    def __init__(self) -> None:
        super().__init__(base_url="http://localhost:11434", model="qwen2.5:3b")
        self.calls: list[tuple[str, str]] = []
        self.available_models: set[str] = {"qwen2.5:3b", "qwen2.5:7b", "qwen2.5:14b"}

    def is_model_available(self, model_name: str) -> bool:
        return model_name in self.available_models

    def stream_summarize(self, text: str):
        self.calls.append(("summarize", self._effective_model))
        yield ModelStreamEvent(kind=StreamEventType.TEXT_REPLACE, text="요약 결과")

    def stream_respond(self, prompt: str, *, active_preferences=None):
        self.calls.append(("respond", self._effective_model))
        yield ModelStreamEvent(kind=StreamEventType.TEXT_REPLACE, text="일반 응답")

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
        active_preferences=None,
    ):
        self.calls.append(("answer_context", self._effective_model))
        yield ModelStreamEvent(kind=StreamEventType.TEXT_REPLACE, text="문맥 응답")


def _build_loop(root: str, model: _RecordingOllamaAdapter) -> AgentLoop:
    return AgentLoop(
        model=model,
        session_store=SessionStore(base_dir=f"{root}/sessions"),
        task_logger=TaskLogger(path=f"{root}/task_log.jsonl"),
        tools={},
        model_router=ModelConfig(),
    )


class AgentLoopModelRoutingTest(unittest.TestCase):
    def test_summarize_uses_routed_medium_model_during_stream(self) -> None:
        with TemporaryDirectory() as tmp:
            model = _RecordingOllamaAdapter()
            loop = _build_loop(tmp, model)

            summary, chunks = loop._summarize_text_with_chunking(
                text="짧은 문서 본문입니다.",
                source_label="sample.txt",
            )

            self.assertEqual(summary, "요약 결과")
            self.assertEqual(chunks, [])
            self.assertEqual(model.calls, [("summarize", "qwen2.5:7b")])
            self.assertEqual(model._effective_model, "qwen2.5:3b")

    def test_general_response_uses_routed_medium_model_during_stream(self) -> None:
        with TemporaryDirectory() as tmp:
            model = _RecordingOllamaAdapter()
            loop = _build_loop(tmp, model)

            response = loop._handle_general_response(
                UserRequest(user_text="안녕하세요", session_id="s1"),
                RequestContext(user_text="안녕하세요", session_id="s1"),
            )

            self.assertEqual(response.text, "일반 응답")
            self.assertEqual(model.calls, [("respond", "qwen2.5:7b")])
            self.assertEqual(model._effective_model, "qwen2.5:3b")

    def test_entity_card_context_uses_routed_heavy_model_during_stream(self) -> None:
        with TemporaryDirectory() as tmp:
            model = _RecordingOllamaAdapter()
            loop = _build_loop(tmp, model)

            response = loop._respond_with_active_context(
                request=UserRequest(user_text="핵심 알려줘", session_id="s1"),
                active_context={
                    "kind": "web_search",
                    "answer_mode": AnswerMode.ENTITY_CARD,
                    "label": "검색 결과",
                    "source_paths": ["https://example.com/a"],
                    "excerpt": "예시 인물은 문서 도구를 개발한 것으로 알려져 있습니다.",
                    "summary_hint": "문서 도구 개발자",
                    "evidence_pool": [
                        {
                            "source_path": "https://example.com/a",
                            "text": "예시 인물은 문서 도구를 개발한 것으로 알려져 있습니다.",
                        }
                    ],
                },
            )

            self.assertEqual(response.text, "문맥 응답")
            self.assertEqual(model.calls, [("answer_context", "qwen2.5:14b")])
            self.assertEqual(model._effective_model, "qwen2.5:3b")

    def test_heavy_model_unavailable_falls_back_to_medium(self) -> None:
        with TemporaryDirectory() as tmp:
            model = _RecordingOllamaAdapter()
            model.available_models = {"qwen2.5:3b", "qwen2.5:7b"}
            loop = _build_loop(tmp, model)

            with loop._routed_model(task="respond", answer_mode=AnswerMode.ENTITY_CARD):
                self.assertEqual(model._effective_model, "qwen2.5:7b")

            self.assertEqual(model._effective_model, "qwen2.5:3b")

    def test_all_tier_models_unavailable_uses_noop(self) -> None:
        with TemporaryDirectory() as tmp:
            model = _RecordingOllamaAdapter()
            model.available_models = set()
            loop = _build_loop(tmp, model)

            routed_context = loop._routed_model(task="respond", answer_mode=AnswerMode.ENTITY_CARD)

            self.assertIsInstance(routed_context, _NoOpContext)
            with routed_context:
                self.assertEqual(model._effective_model, "qwen2.5:3b")


if __name__ == "__main__":
    unittest.main()
