from __future__ import annotations

from contextlib import nullcontext
import unittest
from typing import Any

from core.agent_loop import AgentLoop, UserRequest
from core.contracts import ResponseStatus, StreamEventType
from model_adapter.base import ModelStreamEvent


class _PreferenceStore:
    def __init__(self, preferences: list[dict[str, Any]]) -> None:
        self._preferences = preferences

    def get_active_preferences(self) -> list[dict[str, Any]]:
        return list(self._preferences)


class _SessionStore:
    def __init__(self, per_preference_stats: dict[str, Any] | None = None) -> None:
        self._per_preference_stats = per_preference_stats or {}

    def get_global_audit_summary(self) -> dict[str, Any]:
        return {"per_preference_stats": self._per_preference_stats}


class _TaskLogger:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def log(self, *, session_id: str, action: str, detail: dict[str, Any]) -> None:
        self.entries.append({"session_id": session_id, "action": action, "detail": detail})


class _RecordingContextModel:
    def __init__(self) -> None:
        self.active_preferences: list[dict[str, str]] | None | str = "not-called"

    def stream_answer_with_context(self, **kwargs: Any) -> list[str]:
        self.active_preferences = kwargs.get("active_preferences")
        return ["web answer"]


class _RecordingSummaryModel:
    def __init__(self) -> None:
        self.active_preferences: list[list[dict[str, str]] | None] = []

    def stream_summarize(
        self, text: str, *, active_preferences: list[dict[str, str]] | None = None
    ) -> list[ModelStreamEvent]:
        self.active_preferences.append(active_preferences)
        return [ModelStreamEvent(kind=StreamEventType.TEXT_REPLACE, text="요약 결과")]


def _build_loop(
    preferences: list[dict[str, Any]] | None,
    per_preference_stats: dict[str, Any] | None = None,
) -> AgentLoop:
    loop = AgentLoop.__new__(AgentLoop)
    loop.preference_store = _PreferenceStore(preferences) if preferences is not None else None
    loop.session_store = _SessionStore(per_preference_stats)
    loop.task_logger = _TaskLogger()
    return loop


def _build_context_answer_loop(model: _RecordingContextModel) -> AgentLoop:
    loop = AgentLoop.__new__(AgentLoop)
    loop.model = model
    loop.task_logger = _TaskLogger()
    loop._detect_follow_up_intent = lambda _text: "general"  # type: ignore[method-assign]
    loop._refine_follow_up_intent_with_context = lambda _text, intent: intent  # type: ignore[method-assign]
    loop._extract_retry_feedback_label = lambda _request: None  # type: ignore[method-assign]
    loop._extract_retry_feedback_reason = lambda _request: None  # type: ignore[method-assign]
    loop._extract_retry_target_message_id = lambda _request: None  # type: ignore[method-assign]
    loop._build_retry_policy = lambda **_kwargs: {"max_evidence_items": 4, "max_supporting_chunks": 2}  # type: ignore[method-assign]
    loop._select_retrieval_chunks = lambda **_kwargs: []  # type: ignore[method-assign]
    loop._compose_retrieved_context_excerpt = lambda **kwargs: kwargs.get("fallback_excerpt", "")  # type: ignore[method-assign]
    loop._extract_evidence_from_chunks = lambda **_kwargs: []  # type: ignore[method-assign]
    loop._dedupe_evidence_items = lambda items, **_kwargs: items  # type: ignore[method-assign]
    loop._filter_evidence_pool_for_retry = lambda **kwargs: kwargs.get("evidence_pool", [])  # type: ignore[method-assign]
    loop._select_evidence_items = lambda **_kwargs: []  # type: ignore[method-assign]
    loop._compose_grounded_context_excerpt = lambda **kwargs: kwargs.get("fallback_excerpt", "")  # type: ignore[method-assign]
    loop._augment_retry_request = lambda **kwargs: kwargs.get("user_request", "")  # type: ignore[method-assign]
    loop._emit_phase = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    loop._routed_model = lambda **_kwargs: nullcontext()  # type: ignore[method-assign]
    loop._collect_model_stream = lambda stream, **_kwargs: "".join(stream)  # type: ignore[method-assign]
    loop._apply_context_conversation_mode = lambda **kwargs: kwargs.get("answer", "")  # type: ignore[method-assign]
    loop._public_active_context = lambda active_context: dict(active_context)  # type: ignore[method-assign]
    return loop


def _build_summary_loop(
    model: _RecordingSummaryModel,
    preferences: list[dict[str, Any]],
    per_preference_stats: dict[str, Any],
) -> AgentLoop:
    loop = _build_loop(preferences, per_preference_stats)
    loop.model = model
    loop._model_router = None
    return loop


class AgentLoopPreferenceTest(unittest.TestCase):
    def test_get_active_preferences_returns_none_without_store(self) -> None:
        loop = _build_loop(None)

        self.assertIsNone(loop._get_active_preferences())

    def test_get_active_preferences_excludes_not_high_quality_by_default(self) -> None:
        loop = _build_loop(
            [
                {
                    "description": "reliable preference",
                    "delta_fingerprint": "fp-reliable",
                    "avg_similarity_score": 0.15,
                },
                {
                    "description": "low quality preference",
                    "delta_fingerprint": "fp-low-quality",
                    "quality_info": {"avg_similarity_score": 0.99, "is_high_quality": False},
                },
            ],
            {
                "fp-reliable": {"applied_count": 3, "corrected_count": 0},
                "fp-low-quality": {"applied_count": 3, "corrected_count": 0},
            },
        )

        self.assertEqual(
            loop._get_active_preferences(),
            [{"description": "reliable preference", "fingerprint": "fp-reliable"}],
        )

    def test_get_active_preferences_excludes_low_application_count_by_default(self) -> None:
        loop = _build_loop(
            [
                {
                    "description": "reliable preference",
                    "delta_fingerprint": "fp-reliable",
                    "avg_similarity_score": 0.15,
                },
                {
                    "description": "too few applications",
                    "delta_fingerprint": "fp-too-few",
                    "avg_similarity_score": 0.15,
                },
            ],
            {
                "fp-reliable": {"applied_count": 4, "corrected_count": 0},
                "fp-too-few": {"applied_count": 2, "corrected_count": 0},
            },
        )

        self.assertEqual(
            loop._get_active_preferences(),
            [{"description": "reliable preference", "fingerprint": "fp-reliable"}],
        )

    def test_get_active_preferences_can_include_all_active_preferences(self) -> None:
        loop = _build_loop(
            [
                {
                    "description": "reliable preference",
                    "delta_fingerprint": "fp-reliable",
                    "avg_similarity_score": 0.15,
                },
                {
                    "description": "too few applications",
                    "delta_fingerprint": "fp-too-few",
                    "avg_similarity_score": 0.15,
                },
            ],
            {
                "fp-reliable": {"applied_count": 4, "corrected_count": 0},
                "fp-too-few": {"applied_count": 2, "corrected_count": 0},
            },
        )

        self.assertEqual(
            loop._get_active_preferences(highly_reliable_only=False),
            [
                {"description": "reliable preference", "fingerprint": "fp-reliable"},
                {"description": "too few applications", "fingerprint": "fp-too-few"},
            ],
        )

    def test_get_active_preferences_without_user_input_returns_all_active_preferences(self) -> None:
        loop = _build_loop(
            [
                {
                    "preference_id": "pref-one",
                    "description": "budget summaries should be concise",
                    "delta_fingerprint": "fp-one",
                    "is_highly_reliable": True,
                },
                {
                    "preference_id": "pref-two",
                    "description": "meeting notes should use bullets",
                    "delta_fingerprint": "fp-two",
                    "is_highly_reliable": True,
                },
            ],
        )

        self.assertEqual(
            loop._get_active_preferences(),
            [
                {"description": "budget summaries should be concise", "fingerprint": "fp-one"},
                {"description": "meeting notes should use bullets", "fingerprint": "fp-two"},
            ],
        )

    def test_preference_context_terms_removes_stop_words(self) -> None:
        loop = _build_loop([])

        self.assertEqual(
            loop._preference_context_terms("The budget is in report should 는 요약"),
            {"budget", "report", "요약"},
        )

    def test_get_active_preferences_with_stop_words_only_falls_back_to_all(self) -> None:
        loop = _build_loop(
            [
                {
                    "preference_id": "pref-budget",
                    "description": "budget summaries should be concise",
                    "delta_fingerprint": "fp-budget",
                    "is_highly_reliable": True,
                },
                {
                    "preference_id": "pref-meeting",
                    "description": "meeting notes should use bullets",
                    "delta_fingerprint": "fp-meeting",
                    "is_highly_reliable": True,
                },
            ],
        )

        self.assertEqual(
            loop._get_active_preferences(user_input="the is a", session_id="session-1"),
            [
                {"description": "budget summaries should be concise", "fingerprint": "fp-budget"},
                {"description": "meeting notes should use bullets", "fingerprint": "fp-meeting"},
            ],
        )
        self.assertEqual(
            [entry["detail"]["reason"] for entry in loop.task_logger.entries],
            ["fallback_all", "fallback_all"],
        )

    def test_get_active_preferences_with_user_input_returns_context_matches(self) -> None:
        loop = _build_loop(
            [
                {
                    "preference_id": "pref-budget",
                    "description": "formal voice",
                    "corrected_text": "budget summary format",
                    "delta_fingerprint": "fp-budget",
                    "is_highly_reliable": True,
                },
                {
                    "preference_id": "pref-meeting",
                    "description": "meeting notes use bullets",
                    "delta_fingerprint": "fp-meeting",
                    "is_highly_reliable": True,
                },
            ],
        )

        self.assertEqual(
            loop._get_active_preferences(user_input="budget please", session_id="session-1"),
            [{"description": "formal voice", "fingerprint": "fp-budget"}],
        )

    def test_get_active_preferences_orders_context_matches_by_overlap_score(self) -> None:
        loop = _build_loop(
            [
                {
                    "preference_id": "pref-low-score",
                    "description": "budget",
                    "delta_fingerprint": "fp-low-score",
                    "is_highly_reliable": True,
                },
                {
                    "preference_id": "pref-high-score",
                    "description": "formal voice",
                    "corrected_text": "budget summary format",
                    "delta_fingerprint": "fp-high-score",
                    "is_highly_reliable": True,
                },
            ],
        )

        self.assertEqual(
            loop._get_active_preferences(
                user_input="budget summary format",
                session_id="session-1",
            ),
            [
                {"description": "formal voice", "fingerprint": "fp-high-score"},
                {"description": "budget", "fingerprint": "fp-low-score"},
            ],
        )

    def test_get_active_preferences_prefers_highly_reliable_on_context_score_tie(self) -> None:
        loop = _build_loop(
            [
                {
                    "preference_id": "pref-normal",
                    "description": "budget wording",
                    "delta_fingerprint": "fp-normal",
                    "is_highly_reliable": False,
                },
                {
                    "preference_id": "pref-reliable",
                    "description": "budget format",
                    "delta_fingerprint": "fp-reliable",
                    "is_highly_reliable": True,
                },
            ],
        )

        self.assertEqual(
            loop._get_active_preferences(
                highly_reliable_only=False,
                user_input="budget",
                session_id="session-1",
            ),
            [
                {"description": "budget format", "fingerprint": "fp-reliable"},
                {"description": "budget wording", "fingerprint": "fp-normal"},
            ],
        )

    def test_get_active_preferences_with_no_context_match_falls_back_to_all(self) -> None:
        loop = _build_loop(
            [
                {
                    "preference_id": "pref-budget",
                    "description": "budget summaries should be concise",
                    "delta_fingerprint": "fp-budget",
                    "is_highly_reliable": True,
                },
                {
                    "preference_id": "pref-meeting",
                    "description": "meeting notes should use bullets",
                    "delta_fingerprint": "fp-meeting",
                    "is_highly_reliable": True,
                },
            ],
        )

        self.assertEqual(
            loop._get_active_preferences(user_input="invoice total", session_id="session-1"),
            [
                {"description": "budget summaries should be concise", "fingerprint": "fp-budget"},
                {"description": "meeting notes should use bullets", "fingerprint": "fp-meeting"},
            ],
        )
        self.assertEqual(
            [entry["detail"]["reason"] for entry in loop.task_logger.entries],
            ["fallback_all", "fallback_all"],
        )

    def test_get_active_preferences_logs_preference_injected_events(self) -> None:
        loop = _build_loop(
            [
                {
                    "preference_id": "pref-budget",
                    "description": "budget summaries should be concise",
                    "delta_fingerprint": "fp-budget",
                    "is_highly_reliable": True,
                },
                {
                    "preference_id": "pref-meeting",
                    "description": "meeting notes should use bullets",
                    "delta_fingerprint": "fp-meeting",
                    "is_highly_reliable": True,
                },
            ],
        )

        result = loop._get_active_preferences(
            user_input="budget",
            session_id="session-1",
        )

        self.assertEqual(result, [{"description": "budget summaries should be concise", "fingerprint": "fp-budget"}])
        self.assertEqual(
            loop.task_logger.entries,
            [
                {
                    "session_id": "session-1",
                    "action": "preference_injected",
                    "detail": {
                        "preference_id": "pref-budget",
                        "reason": "context_match",
                        "user_input_snippet": "budget",
                    },
                }
            ],
        )

    def test_summarize_text_injects_highly_reliable_preferences(self) -> None:
        model = _RecordingSummaryModel()
        loop = _build_summary_loop(
            model,
            [
                {
                    "description": "요약은 짧게",
                    "delta_fingerprint": "fp-reliable",
                    "avg_similarity_score": 0.15,
                },
                {
                    "description": "적용 횟수 부족",
                    "delta_fingerprint": "fp-too-few",
                    "avg_similarity_score": 0.15,
                },
            ],
            {
                "fp-reliable": {"applied_count": 3, "corrected_count": 0},
                "fp-too-few": {"applied_count": 2, "corrected_count": 0},
            },
        )

        summary, chunks = loop._summarize_text_with_chunking(
            text="짧은 문서 본문입니다.",
            source_label="sample.txt",
        )

        self.assertEqual(summary, "요약 결과")
        self.assertEqual(chunks, [])
        self.assertEqual(
            model.active_preferences,
            [[{"description": "요약은 짧게", "fingerprint": "fp-reliable"}]],
        )


class AgentLoopWebPreferenceInjectionTest(unittest.TestCase):
    def test_web_investigation_answer_does_not_inject_preferences(self) -> None:
        model = _RecordingContextModel()
        loop = _build_context_answer_loop(model)
        routed_preference_calls: list[dict[str, Any]] = []

        def _routed_preferences(**kwargs: Any) -> list[dict[str, str]]:
            routed_preference_calls.append(kwargs)
            return [{"description": "should not be injected", "fingerprint": "fp-pref"}]

        loop._routed_preferences = _routed_preferences  # type: ignore[method-assign]

        response = loop._respond_with_active_context(
            request=UserRequest(user_text="요약해줘", session_id="session-1"),
            active_context={
                "kind": "web_search",
                "label": "웹 조사 결과",
                "source_paths": ["https://example.com/a"],
                "excerpt": "web excerpt",
            },
        )

        self.assertEqual(response.status, ResponseStatus.ANSWER)
        self.assertEqual(response.text, "web answer")
        self.assertIsNone(model.active_preferences)
        self.assertIsNone(response.applied_preferences)
        self.assertEqual(routed_preference_calls, [])


if __name__ == "__main__":
    unittest.main()
