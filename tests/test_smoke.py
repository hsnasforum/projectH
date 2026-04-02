import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from app.web import WebAppService
from config.settings import AppSettings
from core.agent_loop import AgentLoop, UserRequest
from model_adapter.mock import MockModelAdapter
from storage.session_store import SessionStore
from storage.task_log import TaskLogger
from storage.web_search_store import WebSearchStore
from tools.file_reader import FileReaderTool
from tools.file_search import FileSearchResult, FileSearchTool
from tools.write_note import WriteNoteTool


class _FakePdfPage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeEmptyPdfReader:
    def __init__(self, path: str) -> None:
        self.path = path
        self.pages = [
            _FakePdfPage(""),
            _FakePdfPage("   "),
        ]


class _FakeWebSearchTool:
    def __init__(self, results, pages=None):
        self._results = results
        self._pages = dict(pages or {})
        self.search_calls: list[str] = []

    def search(self, *, query: str, max_results: int = 5):
        self.search_calls.append(query)
        if isinstance(self._results, dict):
            return list(self._results.get(query, []))[:max_results]
        return list(self._results)[:max_results]

    def fetch_page(self, *, url: str, max_chars: int | None = None):
        page = self._pages.get(url)
        if page is None:
            raise RuntimeError("원문 페이지 fixture가 없습니다.")
        return SimpleNamespace(
            url=url,
            title=str(page.get("title") or ""),
            text=str(page.get("text") or "")[: max_chars or len(str(page.get("text") or ""))],
            excerpt=str(page.get("excerpt") or ""),
            content_type=str(page.get("content_type") or "text/html"),
        )


class _CaptureContextModel(MockModelAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.last_context_call: dict[str, object] | None = None

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
        self.last_context_call = {
            "intent": intent,
            "user_request": user_request,
            "context_label": context_label,
            "source_paths": list(source_paths),
            "context_excerpt": context_excerpt,
            "summary_hint": summary_hint,
            "evidence_items": [dict(item) for item in (evidence_items or [])],
        }
        return super().answer_with_context(
            intent=intent,
            user_request=user_request,
            context_label=context_label,
            source_paths=source_paths,
            context_excerpt=context_excerpt,
            summary_hint=summary_hint,
            evidence_items=evidence_items,
        )


class _NarrativeReduceModel(MockModelAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.summary_inputs: list[str] = []

    def summarize(self, text: str) -> str:
        self.summary_inputs.append(text)
        normalized = " ".join(text.split())
        if "Summary mode: merged_chunk_outline" in text:
            return (
                "태양과 영희는 서로의 감정을 모른 척할 수 없게 되고, "
                "철수는 그 변화를 모른 채 진심을 드러내며, "
                "마지막에는 관계가 끝난 게 아니라는 신호가 다시 남습니다."
            )
        if "철수는 태양에게" in normalized:
            return "철수는 태양에게 영희를 향한 진심을 털어놓고 태양은 더 깊이 흔들립니다."
        if "오늘 끝난 거 아니죠" in normalized:
            return "전시 이후 영희는 오늘이 끝난 게 아니라고 다시 신호를 보냅니다."
        if "못 들은 척 못 하겠어" in normalized:
            return "태양과 영희는 더는 감정을 모른 척할 수 없게 됩니다."
        return super().summarize(text)


class _SearchReduceModel(MockModelAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.summary_inputs: list[str] = []

    def summarize(self, text: str) -> str:
        self.summary_inputs.append(text)
        if "Summary mode: merged_chunk_outline" in text and "Summary source type: search_results" in text:
            return (
                "여러 검색 결과를 종합하면 예산 통제와 승인 기반 저장 유지가 공통으로 강조되고, "
                "문서마다 실행 항목의 우선순위와 범위에는 차이가 있다는 점이 함께 드러납니다."
            )
        return super().summarize(text)


class _ShortSummaryCaptureModel(MockModelAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.summary_inputs: list[str] = []

    def summarize(self, text: str) -> str:
        self.summary_inputs.append(text)
        if "Summary mode: short_summary" in text and "Summary source type: search_results" in text:
            return (
                "여러 검색 결과를 종합하면 예산 통제 유지가 공통으로 보이고, "
                "문서마다 우선 실행 항목과 조정 범위가 다르다는 점이 함께 정리됩니다."
            )
        if "Summary mode: short_summary" in text and "Summary source type: local_document" in text:
            return (
                "태양과 영희의 긴장이 커지고 철수는 변화를 놓친 채 일정을 밀어붙이며, "
                "마지막에는 관계가 아직 끝나지 않았다는 신호가 남습니다."
            )
        return super().summarize(text)


class SmokeTest(unittest.TestCase):
    def test_mock_summary(self) -> None:
        adapter = MockModelAdapter()
        self.assertIn("[모의 요약]", adapter.summarize("hello world"))

    def test_unverified_external_fact_request_returns_limited_response(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="유튜버 레고77이 누구야?",
                    session_id="limited-general-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["respond_with_limitations"])
            self.assertIn("외부 웹 검색이 차단되어 있어", response.text)
            self.assertIn("유튜버 레고77", response.text)
            self.assertEqual(response.response_origin["provider"], "system")

    def test_site_question_returns_limited_response(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="naver라는 사이트 알아?",
                    session_id="site-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["respond_with_limitations"])
            self.assertIn("외부 웹 검색이 차단되어 있어", response.text)
            self.assertIn("'naver' 검색", response.text)
            self.assertEqual(response.response_origin["provider"], "system")

    def test_personal_experience_question_returns_limited_response(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="체인소맨 봤어?",
                    session_id="experience-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["respond_with_limitations"])
            self.assertIn("직접 봤다거나 써 봤다거나", response.text)
            self.assertEqual(response.response_origin["provider"], "system")

    def test_live_info_question_returns_limited_response(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="오늘 날씨 어때요?",
                    session_id="weather-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["respond_with_limitations"])
            self.assertIn("웹 검색 권한이 차단되어 있고", response.text)
            self.assertEqual(response.response_origin["provider"], "system")

    def test_live_info_question_uses_web_search_when_permission_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="서울 날씨 - 예보",
                                url="https://example.com/seoul-weather",
                                snippet="서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="오늘 날씨 어때요?",
                    session_id="weather-enabled-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["provider"], "web")
            self.assertIn("웹 최신 확인: 오늘 날씨", response.text)
            self.assertIn("현재 확인된 최신 정보:", response.text)
            self.assertIn("기준:", response.text)
            self.assertIn("확인 강도:", response.text)
            self.assertEqual(response.response_origin["answer_mode"], "latest_update")
            self.assertGreaterEqual(len(response.response_origin["source_roles"]), 1)
            self.assertTrue(response.response_origin["verification_label"])

    def test_external_fact_info_request_uses_web_search_when_permission_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="메이플스토리 - 공식 소개",
                                url="https://example.com/maplestory",
                                snippet="메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="메이플스토리에 대해 알려줘",
                    session_id="external-fact-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["provider"], "web")
            self.assertIn("웹 검색 요약: 메이플스토리", response.text)

    def test_external_fact_retry_prompt_uses_web_search_when_permission_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            )
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text=(
                        "붉은사막이 무슨게임이야?\n\n"
                        "방금 답변은 틀림 이유는 '사실과 다름'입니다. 같은 세션 문맥과 근거를 기준으로 "
                        "더 정확하고 관련성 높게 다시 답변해 주세요."
                    ),
                    session_id="external-fact-retry-session",
                    metadata={
                        "web_search_permission": "enabled",
                        "retry_feedback_label": "incorrect",
                        "retry_feedback_reason": "factual_error",
                    },
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["provider"], "web")
            self.assertIn("웹 검색 요약: 붉은사막", response.text)

    def test_external_fact_who_question_uses_web_search_when_permission_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="김창섭 - 소개",
                                url="https://example.com/kim-changseop",
                                snippet="김창섭은 예시 인물 소개 페이지입니다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="김창섭이 누구야?",
                    session_id="external-fact-who-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["provider"], "web")
            self.assertIn("웹 검색 요약: 김창섭", response.text)

    def test_external_fact_who_question_with_spaced_question_mark_uses_web_search(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="김창섭 - 소개",
                                url="https://example.com/kim-changseop",
                                snippet="김창섭은 예시 인물 소개 페이지입니다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="김창섭이 누구야 ?",
                    session_id="external-fact-who-spaced-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["provider"], "web")
            self.assertIn("웹 검색 요약: 김창섭", response.text)

    def test_external_fact_colloquial_info_questions_use_web_search(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="김창섭 - 소개",
                                url="https://example.com/kim-changseop",
                                snippet="김창섭은 예시 인물 소개 페이지입니다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            phrases = [
                "김창섭 좀 알려줘",
                "김창섭 아냐?",
                "김창섭 어떤 사람이야?",
                "김창섭 어떤 분이야?",
                "김창섭 얘기 좀 해줘",
                "김창섭 얘기해봐",
                "김창섭 관련 정보 있나?",
                "김창섭 관련된 거 좀 알려줘",
                "김창섭 쪽은 어때?",
                "김창섭 쪽으로 좀 봐줘",
                "김창섭 뭐하는 사람이야?",
                "김창섭 누군지 궁금해",
                "김창섭 어떤 사람인지 궁금해",
                "김창섭 대충 알려줘",
                "김창섭이 누군지 알려줘",
                "김창섭이 누군지 궁금한데",
            ]

            for index, phrase in enumerate(phrases, start=1):
                with self.subTest(phrase=phrase):
                    response = loop.handle(
                        UserRequest(
                            user_text=phrase,
                            session_id=f"external-fact-colloquial-session-{index}",
                            metadata={"web_search_permission": "enabled"},
                        )
                    )

                    self.assertEqual(response.status, "answer")
                    self.assertEqual(response.actions_taken, ["web_search"])
                    self.assertEqual(response.response_origin["provider"], "web")
                    self.assertIn("웹 검색 요약: 김창섭", response.text)

    def test_low_confidence_external_fact_question_returns_web_search_suggestion(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="김창섭 궁금한데",
                    session_id="suggest-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["suggest_web_search"])
            self.assertEqual(response.response_origin["provider"], "system")
            self.assertIn("자동 웹 검색으로 바로 넘길 확신은 낮습니다", response.text)
            self.assertEqual(response.follow_up_suggestions, ["김창섭 검색해봐"])

    def test_external_fact_site_question_strips_descriptor_before_permission_prompt(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="naver라는 사이트 알아?",
                    session_id="site-session-cleaned-query",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["respond_with_limitations"])
            self.assertIn("'naver' 검색", response.text)

    def test_live_info_question_uses_web_search_even_with_existing_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            session_store = SessionStore(base_dir=str(tmp_path / "sessions"))
            session_store.set_active_context(
                "weather-existing-context",
                {
                    "kind": "document",
                    "label": "기존 문서",
                    "source_paths": [str(tmp_path / "memo.txt")],
                    "summary_hint": "기존 문서 요약",
                    "suggested_prompts": [],
                },
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=session_store,
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="오늘 날씨 - 예보",
                                url="https://example.com/today-weather",
                                snippet="오늘은 전국이 대체로 맑고 서울은 최고 17도로 예보되었습니다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="아이유 최신 소식 알려줘",
                    session_id="weather-existing-context",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["provider"], "web")
            self.assertIn("웹 최신 확인: 아이유 최신 소식", response.text)
            self.assertEqual(response.response_origin["answer_mode"], "latest_update")
            self.assertTrue(response.response_origin["verification_label"])

    def test_external_fact_response_reflects_web_search_permission(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="naver라는 사이트 알아?",
                    session_id="permission-aware-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("웹 검색을 허용한 상태지만", response.text)

    def test_enabled_web_search_request_uses_results_and_saves_record(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="체인소 맨 - 위키백과",
                                url="https://example.com/chainsawman",
                                snippet="체인소 맨은 일본의 다크 판타지 만화 작품입니다.",
                            ),
                            SimpleNamespace(
                                title="체인소맨 애니메이션 소개",
                                url="https://example.com/chainsawman-anime",
                                snippet="애니메이션과 원작 만화 정보를 정리한 소개 문서입니다.",
                            ),
                        ],
                        pages={
                            "https://example.com/chainsawman": {
                                "title": "체인소 맨 - 위키백과",
                                "text": "체인소 맨은 일본의 다크 판타지 만화 작품입니다.\n주인공과 세계관, 애니메이션 정보가 함께 정리되어 있습니다.",
                                "excerpt": "체인소 맨은 일본의 다크 판타지 만화 작품입니다.",
                            },
                            "https://example.com/chainsawman-anime": {
                                "title": "체인소맨 애니메이션 소개",
                                "text": "애니메이션과 원작 만화 정보를 정리한 소개 문서입니다.\n등장인물과 방영 정보가 요약되어 있습니다.",
                                "excerpt": "애니메이션과 원작 만화 정보를 정리한 소개 문서입니다.",
                            },
                        },
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="체인소맨 검색해봐",
                    session_id="web-search-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["provider"], "web")
            self.assertIn("웹 검색 요약: 체인소맨", response.text)
            self.assertIn("체인소맨 애니메이션 소개", response.text)
            self.assertIn("체인소 맨 - 위키백과", response.text)
            self.assertTrue(response.web_search_record_path)
            self.assertTrue(Path(response.web_search_record_path).exists())
            self.assertEqual(response.active_context["kind"], "web_search")
            self.assertIn("https://example.com/chainsawman", response.selected_source_paths)
            saved_record = response.web_search_record_path and Path(response.web_search_record_path).read_text(encoding="utf-8")
            self.assertIn('"page_count": 2', saved_record)
            self.assertIn("체인소 맨은 일본의 다크 판타지 만화 작품입니다.", saved_record)

    def test_web_search_summary_prefers_relevant_page_segments_over_boilerplate(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 프리뷰",
                                url="https://example.com/crimson-desert-preview",
                                snippet="붉은사막은 오픈월드 액션 어드벤처 게임으로 소개됩니다.",
                            ),
                        ],
                        pages={
                            "https://example.com/crimson-desert-preview": {
                                "title": "붉은사막 프리뷰",
                                "text": (
                                    "로그인 로그아웃 회원가입 전체메뉴 기사제보 PDF보기 English Deutsch Русский\n"
                                    "붉은사막은 오픈월드 액션 어드벤처 게임으로, 파이웰 대륙을 배경으로 탐험과 전투를 중심으로 진행됩니다.\n"
                                    "출시 버전에서는 다양한 지역과 서사가 순차적으로 공개될 예정입니다."
                                ),
                                "excerpt": "로그인 로그아웃 회원가입 전체메뉴 기사제보 PDF보기",
                            },
                        },
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에대해 검색해봐",
                    session_id="web-search-quality-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("오픈월드 액션 어드벤처 게임", response.text)
            self.assertNotIn("로그인 로그아웃", response.text)

    def test_web_search_summary_falls_back_to_relevant_snippets_when_js_heavy_page_is_noisy(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="BTS - 나무위키",
                                url="https://namu.wiki/w/BTS",
                                snippet="BTS는 대한민국의 7인조 보이 그룹이다.",
                            ),
                            SimpleNamespace(
                                title="BTS - 위키백과",
                                url="https://ko.wikipedia.org/wiki/BTS",
                                snippet="BTS는 대한민국의 보이 밴드로 2013년에 데뷔했다.",
                            ),
                            SimpleNamespace(
                                title="BTS - YouTube",
                                url="https://www.youtube.com/@BTS",
                                snippet="BTS 공식 유튜브 채널.",
                            ),
                        ],
                        pages={
                            "https://www.youtube.com/@BTS": {
                                "title": "BTS - YouTube",
                                "text": (
                                    "YouTube Google LLC 이용약관 개인정보 쿠키 정책 "
                                    "YouTube 앱 TV에서 보기 YouTube Premium YouTube Music"
                                ),
                                "excerpt": "YouTube Google LLC 이용약관 개인정보 쿠키 정책",
                            },
                        },
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="BTS 알아봐줘",
                    session_id="web-search-bts-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["provider"], "web")
            self.assertIn("대한민국의 7인조 보이 그룹", response.text)
            self.assertNotIn("Google LLC", response.text)
            self.assertNotIn("YouTube Premium", response.text)

    def test_web_search_summary_ignores_contact_footer_segments_from_official_page(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="메이플스토리",
                                url="https://maplestory.nexon.com/Home/Main",
                                snippet="메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.",
                            ),
                            SimpleNamespace(
                                title="메이플스토리 - 네이버 게임",
                                url="https://game.naver.com/MapleStory",
                                snippet="메이플스토리는 다양한 직업과 모험 요소가 있는 온라인 RPG이다.",
                            ),
                        ],
                        pages={
                            "https://maplestory.nexon.com/Home/Main": {
                                "title": "메이플스토리",
                                "text": (
                                    "메이플스토리와 함께 이용해 보세요! (주)넥슨코리아 대표이사 강대현·김정욱 "
                                    "경기도 성남시 분당구 판교로 256번길 7 전화 : 1588-7701 팩스 : 0502-258-8322 "
                                    "E-mail : contact-us@nexon.co.kr 사업자등록번호 : 220-87-17483 "
                                    "통신판매업 신고번호 : 제2013-경기성남-1659호"
                                ),
                                "excerpt": "메이플스토리와 함께 이용해 보세요! (주)넥슨코리아 대표이사 강대현·김정욱",
                            },
                        },
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="메이플스토리에 대해 알려줘",
                    session_id="maplestory-footer-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("메이플스토리는", response.text)
            self.assertIn("액션 RPG", response.text)
            self.assertIn("이용 형태는 온라인", response.text)
            self.assertNotIn("1588-7701", response.text)
            self.assertNotIn("사업자등록번호", response.text)
            self.assertNotIn("대표이사", response.text)

    def test_web_search_entity_summary_prefers_explainer_sources_over_event_news(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="넥슨, 방탄소년단 진과 '메이플스토리' 협업 이벤트",
                                url="https://biz.example.com/maplestory-event",
                                snippet="넥슨은 메이플스토리 협업 이벤트를 진행한다고 밝혔다.",
                            ),
                            SimpleNamespace(
                                title="메이플스토리 - 나무위키",
                                url="https://namu.wiki/w/%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC",
                                snippet="메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.",
                            ),
                            SimpleNamespace(
                                title="메이플스토리 - 네이버 게임",
                                url="https://game.naver.com/MapleStory",
                                snippet="메이플스토리는 다양한 직업과 모험 요소가 있는 온라인 RPG이다.",
                            ),
                        ],
                        pages={
                            "https://biz.example.com/maplestory-event": {
                                "title": "넥슨, 방탄소년단 진과 '메이플스토리' 협업 이벤트",
                                "text": (
                                    "넥슨은 메이플스토리와 방탄소년단 진 협업 이벤트를 공개했다. "
                                    "이벤트 기간 동안 다양한 보상을 제공한다."
                                ),
                                "excerpt": "메이플스토리 협업 이벤트를 공개했다.",
                            },
                            "https://namu.wiki/w/%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC": {
                                "title": "메이플스토리 - 나무위키",
                                "text": "메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임으로, 2003년부터 서비스 중이다.",
                                "excerpt": "메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.",
                            },
                        },
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="메이플스토리에 대해 알려줘",
                    session_id="maplestory-entity-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("메이플스토리는 넥슨이 서비스하거나 배급하는 액션 RPG 게임입니다.", response.text)
            self.assertIn("이용 형태는 온라인입니다.", response.text)
            self.assertTrue("한 줄 정의:" in response.text or "한 줄 정의 (교차 확인 부족):" in response.text)
            self.assertIn("단일 출처 정보 (교차 확인 부족, 추가 확인 필요):", response.text)
            self.assertNotIn("협업 이벤트", response.text)
            self.assertEqual(response.active_context["source_paths"][0], "https://namu.wiki/w/%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC")

    def test_web_search_entity_summary_uses_expanded_queries_for_better_explainer_results(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            search_tool = _FakeWebSearchTool(
                {
                    "메이플스토리": [
                        SimpleNamespace(
                            title="메이플스토리 인벤",
                            url="https://maple.inven.co.kr/",
                            snippet="메이플 관련 게시판과 커뮤니티 정보를 제공합니다.",
                        ),
                        SimpleNamespace(
                            title="메이플스토리 - 네이버 게임",
                            url="https://game.naver.com/MapleStory",
                            snippet="영상 더보기와 업데이트 소식이 정리되어 있습니다.",
                        ),
                    ],
                    "메이플스토리 소개": [
                        SimpleNamespace(
                            title="메이플스토리 - 나무위키",
                            url="https://namu.wiki/w/%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC",
                            snippet="메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.",
                        ),
                    ],
                    "메이플스토리 설명": [
                        SimpleNamespace(
                            title="메이플스토리 - 위키백과",
                            url="https://ko.wikipedia.org/wiki/%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC",
                            snippet="메이플스토리는 넥슨이 배급하는 온라인 게임이다.",
                        ),
                    ],
                    "메이플스토리 위키": [
                        SimpleNamespace(
                            title="메이플스토리 - 위키백과",
                            url="https://ko.wikipedia.org/wiki/%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC",
                            snippet="메이플스토리는 넥슨이 배급하는 온라인 게임이다.",
                        ),
                    ],
                }
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": search_tool,
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="메이플스토리에 대해 알려줘",
                    session_id="maplestory-expanded-query-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertTrue("한 줄 정의:" in response.text or "한 줄 정의 (교차 확인 부족):" in response.text)
            self.assertIn("메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.", response.text)
            self.assertIn("근거 출처:", response.text)
            self.assertIn("확인된 사실:", response.text)
            self.assertIn("서비스/배급: 넥슨", response.text)
            self.assertIn("이용 형태: 온라인", response.text)
            self.assertIn("단일 출처 정보 (교차 확인 부족, 추가 확인 필요):", response.text)
            self.assertIn("장르/성격: 액션 RPG 게임", response.text)
            self.assertIn("[백과 기반]", response.text)
            self.assertNotIn("영상 더보기", response.text)
            self.assertIn("메이플스토리 설명", search_tool.search_calls)

    def test_web_search_entity_summary_runs_second_pass_queries_for_missing_core_slots(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            search_tool = _FakeWebSearchTool(
                {
                    "붉은사막": [
                        SimpleNamespace(
                            title="붉은사막 - 네이버 게임",
                            url="https://game.naver.com/CrimsonDesert",
                            snippet="붉은사막은 액션 어드벤처 게임으로 소개된다.",
                        ),
                    ],
                    "붉은사막 소개": [
                        SimpleNamespace(
                            title="붉은사막 소개",
                            url="https://portal.example.com/crimson-desert-overview",
                            snippet="붉은사막은 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 설명": [
                        SimpleNamespace(
                            title="붉은사막 설명",
                            url="https://portal.example.com/crimson-desert-summary",
                            snippet="붉은사막은 파이웰 대륙을 배경으로 하는 게임이다.",
                        ),
                    ],
                    "붉은사막 위키": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 공식": [
                        SimpleNamespace(
                            title="Crimson Desert | Pearl Abyss",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=123",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 개발사": [
                        SimpleNamespace(
                            title="붉은사막 - 위키백과",
                            url="https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 플랫폼": [
                        SimpleNamespace(
                            title="붉은사막 공식 소개",
                            url="https://official.example.com/crimson-desert-platform",
                            snippet="붉은사막은 PC와 콘솔에서 즐길 수 있다.",
                        ),
                    ],
                }
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": search_tool,
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-second-pass-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("펄어비스", response.text)
            self.assertIn("오픈월드 액션 어드벤처 게임", response.text)
            self.assertTrue(
                any(
                    call in search_tool.search_calls
                    for call in [
                        "붉은사막 서비스 공식",
                        "붉은사막 공식 플랫폼",
                        "붉은사막 개발사 펄어비스",
                        "붉은사막 개발 중",
                    ]
                )
            )
            self.assertGreater(len(search_tool.search_calls), 4)

    def test_web_search_entity_summary_uses_claim_confirmation_query_for_weak_slot(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            search_tool = _FakeWebSearchTool(
                {
                    "붉은사막": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 서비스하는 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 소개": [
                        SimpleNamespace(
                            title="붉은사막 공식 소개",
                            url="https://official.example.com/crimson-desert-overview",
                            snippet="붉은사막은 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 설명": [
                        SimpleNamespace(
                            title="붉은사막 소개",
                            url="https://portal.example.com/crimson-desert-summary",
                            snippet="붉은사막은 파이웰 대륙을 배경으로 하는 게임이다.",
                        ),
                    ],
                    "붉은사막 위키": [
                        SimpleNamespace(
                            title="붉은사막 - 위키백과",
                            url="https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 펄어비스 서비스 공식": [
                        SimpleNamespace(
                            title="Crimson Desert | Pearl Abyss",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=1000",
                            snippet="붉은사막은 펄어비스가 서비스하는 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 펄어비스 서비스": [
                        SimpleNamespace(
                            title="Crimson Desert | Pearl Abyss",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=999",
                            snippet="붉은사막은 펄어비스가 서비스하는 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                }
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": search_tool,
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-claim-confirm-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("서비스/배급: 펄어비스", response.text)
            self.assertIn("붉은사막 펄어비스 서비스 공식", search_tool.search_calls)
            self.assertNotIn("붉은사막 펄어비스 서비스", search_tool.search_calls)

    def test_web_search_entity_summary_uses_official_probe_query_for_missing_slot(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            search_tool = _FakeWebSearchTool(
                {
                    "붉은사막": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 소개": [
                        SimpleNamespace(
                            title="붉은사막 소개",
                            url="https://wiki.example.com/crimson-desert-overview",
                            snippet="붉은사막은 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 설명": [
                        SimpleNamespace(
                            title="붉은사막 설명",
                            url="https://blog.example.com/crimson-desert-summary",
                            snippet="붉은사막은 파이웰 대륙을 배경으로 한다.",
                        ),
                    ],
                    "붉은사막 위키": [
                        SimpleNamespace(
                            title="붉은사막 - 위키백과",
                            url="https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 공식 플랫폼": [
                        SimpleNamespace(
                            title="Crimson Desert | Pearl Abyss",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=321",
                            snippet="붉은사막은 PC와 콘솔 플랫폼에서 즐길 수 있다.",
                        ),
                    ],
                }
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": search_tool,
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-platform-probe-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("붉은사막 공식 플랫폼", search_tool.search_calls)
            self.assertIn("이용 형태: PC / 콘솔", response.text)

    def test_web_search_entity_summary_runs_third_probe_variant_for_remaining_missing_slot(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            search_tool = _FakeWebSearchTool(
                {
                    "붉은사막": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 서비스하는 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 소개": [
                        SimpleNamespace(
                            title="붉은사막 소개",
                            url="https://wiki.example.com/crimson-desert-overview",
                            snippet="붉은사막은 파이웰 대륙을 배경으로 한다.",
                        ),
                    ],
                    "붉은사막 설명": [
                        SimpleNamespace(
                            title="붉은사막 설명",
                            url="https://blog.example.com/crimson-desert-summary",
                            snippet="붉은사막은 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 위키": [
                        SimpleNamespace(
                            title="붉은사막 - 위키백과",
                            url="https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 플랫폼": [
                        SimpleNamespace(
                            title="붉은사막 플랫폼 안내",
                            url="https://official.example.com/crimson-desert-platform",
                            snippet="붉은사막은 PC와 콘솔에서 즐길 수 있다.",
                        ),
                    ],
                }
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": search_tool,
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-third-probe-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("붉은사막 공식 플랫폼", search_tool.search_calls)
            self.assertIn("붉은사막 플랫폼 위키", search_tool.search_calls)
            self.assertIn("붉은사막 플랫폼", search_tool.search_calls)
            self.assertIn("이용 형태: PC / 콘솔", response.text)

    def test_web_search_entity_summary_marks_unresolved_slots_when_claim_support_is_weak(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-weak-coverage-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertTrue("한 줄 정의:" in response.text or "한 줄 정의 (교차 확인 부족):" in response.text)
            self.assertIn("단일 출처 정보 (교차 확인 부족, 추가 확인 필요):", response.text)
            self.assertIn("확인되지 않은 항목:", response.text)
            # Exact qualifier wording for trusted single-source claims
            self.assertIn("개발: 펄어비스 (단일 출처, 백과 기반, 확정 표현 주의)", response.text)
            self.assertIn("서비스/배급: 교차 확인 가능한 근거를 찾지 못했습니다.", response.text)
            self.assertIn("이용 형태: 교차 확인 가능한 근거를 찾지 못했습니다.", response.text)
            self.assertGreaterEqual(len(response.claim_coverage), 5)
            coverage_by_slot = {
                str(item.get("slot") or ""): dict(item)
                for item in response.claim_coverage
                if isinstance(item, dict)
            }
            self.assertEqual(coverage_by_slot["개발"]["status"], "weak")
            self.assertEqual(coverage_by_slot["개발"]["rendered_as"], "uncertain")
            self.assertEqual(coverage_by_slot["서비스/배급"]["status"], "missing")
            self.assertEqual(coverage_by_slot["이용 형태"]["status"], "missing")
            self.assertIn("붉은사막 서비스 공식 검색해봐", response.follow_up_suggestions)
            self.assertIn("붉은사막 공식 플랫폼 검색해봐", response.follow_up_suggestions)
            self.assertIn("붉은사막 개발사 검색해봐", response.follow_up_suggestions)

    def test_web_search_entity_summary_prefers_trusted_diverse_sources(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 - 네이버 게임",
                                url="https://game.naver.com/CrimsonDesert",
                                snippet="붉은사막은 오픈월드 액션 어드벤처 게임으로 소개된다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 인벤",
                                url="https://www.inven.co.kr/webzine/news/?news=123456",
                                snippet="붉은사막 관련 커뮤니티와 업데이트 소식을 모아 볼 수 있다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 - 위키백과",
                                url="https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발하는 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="Crimson Desert | Pearl Abyss",
                                url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=123",
                                snippet="붉은사막은 파이웰 대륙을 배경으로 한 오픈월드 액션 어드벤처 게임이다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-diverse-source-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", response.text)
            self.assertIn("https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", response.text)
            self.assertIn("https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=123", response.text)
            self.assertIn("[백과 기반]", response.text)
            self.assertIn("[공식 기반]", response.text)
            self.assertNotIn("https://game.naver.com/CrimsonDesert", response.text)
            self.assertNotIn("https://www.inven.co.kr/webzine/news/?news=123456", response.text)
            self.assertEqual(
                response.active_context["source_paths"][:3],
                [
                    "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                    "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                    "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=123",
                ],
            )

    def test_web_search_entity_source_type_diversity_caps_same_type_at_two(self) -> None:
        """3개 wiki 도메인 + 1개 official 도메인이 있을 때,
        wiki가 2개까지만 선택되고 official이 포함되어 source_type 다양성을 확보합니다."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 - 위키백과",
                                url="https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발하는 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 - Britannica",
                                url="https://www.britannica.com/topic/CrimsonDesert",
                                snippet="붉은사막은 한국 개발사 펄어비스의 오픈월드 액션 게임이다.",
                            ),
                            SimpleNamespace(
                                title="Crimson Desert | Pearl Abyss",
                                url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=123",
                                snippet="붉은사막은 파이웰 대륙을 배경으로 한 오픈월드 액션 어드벤처 게임이다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-type-diversity-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            source_paths = response.active_context["source_paths"][:3]
            # wiki 2개 + official 1개가 선택되어야 함
            self.assertIn("https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=123", source_paths)
            wiki_count = sum(
                1 for url in source_paths
                if "namu.wiki" in url or "wikipedia.org" in url or "britannica.com" in url
            )
            self.assertEqual(wiki_count, 2)
            self.assertIn("[공식 기반]", response.text)

    def test_web_search_entity_probe_replaces_same_domain_generic_official(self) -> None:
        """same-domain official overview와 slot-targeted official probe가
        함께 있을 때, probe가 hostname dedupe에 막히지 않고 generic을
        대체하여 missing slot을 메웁니다."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            search_tool = _FakeWebSearchTool(
                {
                    "붉은사막에 대해 알려줘": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                        SimpleNamespace(
                            title="Crimson Desert | Pearl Abyss",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=100",
                            snippet="붉은사막은 파이웰 대륙을 배경으로 한 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                        SimpleNamespace(
                            title="Crimson Desert | Pearl Abyss",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=100",
                            snippet="붉은사막은 파이웰 대륙을 배경으로 한 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 공식 플랫폼 검색해봐": [
                        SimpleNamespace(
                            title="붉은사막 | 플랫폼 - 공식",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
                            snippet="붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
                        ),
                    ],
                    "붉은사막 공식 플랫폼": [
                        SimpleNamespace(
                            title="붉은사막 | 플랫폼 - 공식",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
                            snippet="붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
                        ),
                    ],
                },
                pages={
                    "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200": {
                        "title": "붉은사막 | 플랫폼 - 공식",
                        "text": "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임입니다.",
                        "excerpt": "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정입니다.",
                    },
                },
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": search_tool,
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="probe-replaces-generic-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            source_paths = response.active_context["source_paths"][:3]
            # probe page(boardNo=200)가 generic overview(boardNo=100)를 대체하여 선택되어야 함
            self.assertIn("https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200", source_paths)
            self.assertNotIn("https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=100", source_paths)

    def test_web_search_entity_dual_probe_different_slots_coexist_on_same_domain(self) -> None:
        """같은 official domain에서 서로 다른 slot을 메우는 probe 2개가
        hostname dedupe에 막히지 않고 공존합니다."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            search_tool = _FakeWebSearchTool(
                {
                    "붉은사막에 대해 알려줘": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 공식 플랫폼 검색해봐": [
                        SimpleNamespace(
                            title="붉은사막 | 플랫폼 - 공식",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
                            snippet="붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
                        ),
                    ],
                    "붉은사막 공식 플랫폼": [
                        SimpleNamespace(
                            title="붉은사막 | 플랫폼 - 공식",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
                            snippet="붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
                        ),
                    ],
                    "붉은사막 서비스 공식 검색해봐": [
                        SimpleNamespace(
                            title="붉은사막 | 서비스 - 공식",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300",
                            snippet="붉은사막은 펄어비스가 운영하는 게임이다.",
                        ),
                    ],
                    "붉은사막 서비스 공식": [
                        SimpleNamespace(
                            title="붉은사막 | 서비스 - 공식",
                            url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300",
                            snippet="붉은사막은 펄어비스가 운영하는 게임이다.",
                        ),
                    ],
                },
                pages={
                    "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200": {
                        "title": "붉은사막 | 플랫폼 - 공식",
                        "text": "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임입니다.",
                        "excerpt": "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정입니다.",
                    },
                    "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300": {
                        "title": "붉은사막 | 서비스 - 공식",
                        "text": "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다.",
                        "excerpt": "붉은사막은 펄어비스가 운영하는 게임입니다.",
                    },
                },
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": search_tool,
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="dual-probe-coexist-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            source_paths = response.active_context["source_paths"]
            # entity claims selection + active_context source_paths 모두에서 두 probe가 공존해야 함
            self.assertIn("https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200", source_paths)
            self.assertIn("https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300", source_paths)

    def test_entity_card_zero_strong_slot_downgrades_verification_label(self) -> None:
        """strong-reference source 2개(wiki+wiki)가 있어도 claim_coverage에
        strong slot이 0개이면 verification_label이 '설명형 다중 출처 합의'가 아닌
        non-strong label로 내려갑니다."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="테스트게임 - 나무위키",
                                url="https://namu.wiki/w/testgame",
                                snippet="테스트게임은 알 수 없는 개발사의 게임이다.",
                            ),
                            SimpleNamespace(
                                title="테스트게임 - 위키백과",
                                url="https://ko.wikipedia.org/wiki/testgame",
                                snippet="테스트게임은 정보가 부족한 게임이다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="테스트게임에 대해 알려줘",
                    session_id="zero-strong-slot-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["answer_mode"], "entity_card")
            # strong slot이 0개이므로 '설명형 다중 출처 합의'가 아니어야 함
            self.assertNotEqual(response.response_origin["verification_label"], "설명형 다중 출처 합의")
            # claim_coverage에 strong이 없는지 확인
            strong_items = [
                item for item in response.claim_coverage
                if isinstance(item, dict) and str(item.get("status") or "") == "strong"
            ]
            self.assertEqual(len(strong_items), 0)

    def test_web_search_entity_agreement_prefers_trusted_peer_over_low_trust_peer(self) -> None:
        """같은 사실에 합의하는 peer가 있을 때, high-trust peer(wiki)와 합의한
        소스가 low-trust peer(커뮤니티)와만 합의한 소스보다 우선 선택됩니다."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 정보 - 게임 커뮤니티",
                                url="https://www.inven.co.kr/webzine/news/?news=234567",
                                snippet="붉은사막은 펄어비스가 개발하는 오픈월드 액션 게임이다.",
                            ),
                            SimpleNamespace(
                                title="Crimson Desert | Pearl Abyss",
                                url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=123",
                                snippet="붉은사막은 파이웰 대륙을 배경으로 한 오픈월드 액션 어드벤처 게임이다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="trust-weighted-agreement-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            source_paths = response.active_context["source_paths"][:3]
            # wiki(trust 12)와 사실이 일치하는 official(trust 10)이
            # community(trust -5)보다 우선 선택되어야 함
            self.assertIn("https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", source_paths)
            self.assertIn("https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=123", source_paths)
            self.assertIn("[백과 기반]", response.text)
            self.assertIn("[공식 기반]", response.text)
            # community 소스는 선택되지 않아야 함
            self.assertNotIn("https://www.inven.co.kr/webzine/news/?news=234567", source_paths)

    def test_reuse_web_search_record_uses_stored_answer_mode_over_summary_prefix(self) -> None:
        """_reuse_web_search_record가 summary_text 접두사가 아닌
        저장된 response_origin.answer_mode를 기준으로 reloaded answer_mode를
        결정하여 추론 불안정을 방지합니다."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            store = WebSearchStore(base_dir=str(tmp_path / "web-search"))
            session_id = "stored-origin-reload-session"

            # latest_update 검색 결과를 직접 저장 — summary_text를 의도적으로
            # "웹 최신 확인:" 접두사 없이 저장하여 접두사 기반 추론이 실패하는 상황 재현
            store.save(
                session_id=session_id,
                query="서울 날씨",
                permission="enabled",
                results=[{"title": "서울 날씨", "url": "https://example.com/weather", "snippet": "서울 맑음 17도"}],
                summary_text="서울은 맑고 낮 최고 17도입니다.",
                pages=[],
                response_origin={
                    "provider": "web",
                    "badge": "WEB",
                    "label": "외부 웹 최신 확인",
                    "answer_mode": "latest_update",
                    "verification_label": "단일 출처 참고",
                    "source_roles": ["보조 출처"],
                },
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool([]),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=store,
            )

            response = loop.handle(
                UserRequest(
                    user_text="방금 검색한 결과 다시 보여줘",
                    session_id=session_id,
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["load_web_search_record"])
            self.assertEqual(response.response_origin["answer_mode"], "latest_update")
            self.assertEqual(response.response_origin["verification_label"], "단일 출처 참고")

    def test_entity_reinvestigation_query_reports_claim_progress(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            search_tool = _FakeWebSearchTool(
                {
                    "붉은사막에 대해 알려줘": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막": [
                        SimpleNamespace(
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ],
                    "붉은사막 공식 플랫폼 검색해봐": [
                        SimpleNamespace(
                            title="붉은사막 | 플랫폼 - 공식",
                            url="https://crimsondesert.pearlabyss.com/ko-KR/Board/Detail?_boardNo=12",
                            snippet="붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
                        ),
                    ],
                    "붉은사막 공식 플랫폼": [
                        SimpleNamespace(
                            title="붉은사막 | 플랫폼 - 공식",
                            url="https://crimsondesert.pearlabyss.com/ko-KR/Board/Detail?_boardNo=12",
                            snippet="붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
                        ),
                    ],
                },
                pages={
                    "https://crimsondesert.pearlabyss.com/ko-KR/Board/Detail?_boardNo=12": {
                        "title": "붉은사막 | 플랫폼 - 공식",
                        "text": "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임입니다.",
                        "excerpt": "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정입니다.",
                    }
                },
            )
            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": search_tool,
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            first = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="entity-progress-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )
            self.assertEqual(first.response_origin["answer_mode"], "entity_card")
            self.assertIsNone(first.claim_coverage_progress_summary)
            first_search_call_count = len(search_tool.search_calls)

            second = loop.handle(
                UserRequest(
                    user_text="붉은사막 공식 플랫폼 검색해봐",
                    session_id="entity-progress-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(second.actions_taken, ["web_search"])
            self.assertEqual(second.response_origin["provider"], "web")
            self.assertEqual(second.response_origin["answer_mode"], "entity_card")
            self.assertTrue(second.claim_coverage_progress_summary)
            self.assertIn("이용 형태", second.claim_coverage_progress_summary)
            self.assertIn("단일 출처 상태", second.claim_coverage_progress_summary)
            coverage_by_slot = {
                str(item.get("slot") or ""): dict(item)
                for item in second.claim_coverage
                if isinstance(item, dict)
            }
            self.assertEqual(coverage_by_slot["이용 형태"]["status"], "weak")
            self.assertEqual(coverage_by_slot["이용 형태"]["progress_state"], "unchanged")
            self.assertEqual(coverage_by_slot["이용 형태"]["progress_label"], "유지")
            self.assertTrue(coverage_by_slot["이용 형태"]["is_focus_slot"])
            self.assertIn("웹 검색 요약: 붉은사막", second.text)
            second_search_calls = search_tool.search_calls[first_search_call_count:]
            self.assertIn("붉은사막", second_search_calls)
            self.assertIn("붉은사막 공식 플랫폼", second_search_calls)

    def test_web_search_entity_summary_prefers_multi_source_agreement_over_single_blog_claim(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 후기 블로그",
                                url="https://blog.example.com/crimson-desert-review",
                                snippet="붉은사막은 생존 제작 RPG라는 평이 있다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 - 위키백과",
                                url="https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="Crimson Desert | Pearl Abyss",
                                url="https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=777",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-consensus-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("펄어비스", response.text)
            self.assertIn("오픈월드 액션 어드벤처 게임", response.text)
            self.assertIn("https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", response.text)
            self.assertIn("https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", response.text)
            self.assertIn("https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=777", response.text)
            self.assertNotIn("https://blog.example.com/crimson-desert-review", response.text)
            self.assertNotIn("생존 제작 RPG", response.text)

    def test_entity_card_community_only_source_does_not_surface_weak_claim_section(self) -> None:
        """Community-only sources are not in TRUSTED_CLAIM_SOURCE_ROLES, so they
        cannot enter weak_selected.  The '비공식 출처, 확정 금지' qualifier in the
        rendering path is currently unreachable dead code. This test locks the
        current gating behavior: community-only fixtures must NOT produce a
        '단일 출처 정보' section."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 후기 블로그",
                                url="https://blog.example.com/crimson-desert",
                                snippet="붉은사막은 생존 제작 RPG로 블로그에서 소개되고 있다. 개발사는 펄어비스다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )
            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="community-qualifier-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )
            # Community sources are gated out of weak_selected → no "단일 출처 정보" section
            self.assertNotIn("단일 출처 정보", response.text)
            self.assertNotIn("비공식 출처, 확정 금지", response.text)
            self.assertNotIn("확정 표현 주의", response.text)

    def test_web_search_entity_summary_avoids_single_source_feature_when_core_facts_agree(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 - 위키백과",
                                url="https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 상세 공략 블로그",
                                url="https://blog.example.com/crimson-desert-guide",
                                snippet="붉은사막은 랜턴과 빛 반사를 활용해 주변 정보를 스스로 찾아내는 플레이가 중요하다는 평이 있다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-core-facts-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertIn("개발: 펄어비스", response.text)
            self.assertIn("장르/성격: 오픈월드 액션 어드벤처 게임", response.text)
            self.assertNotIn("플레이 특징:", response.text)
            self.assertNotIn("주변 정보를 스스로 찾아내는", response.text)

    def test_web_search_entity_summary_prefers_consensus_facts_across_sources(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 - 위키백과",
                                url="https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발하는 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 관련 블로그",
                                url="https://example.com/blog/crimson-desert",
                                snippet="붉은사막은 마법 세계관이 강점이라는 평이 있다.",
                            ),
                        ],
                        pages={
                            "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89": {
                                "title": "붉은사막 - 나무위키",
                                "text": "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                                "excerpt": "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            },
                            "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89": {
                                "title": "붉은사막 - 위키백과",
                                "text": "붉은사막은 펄어비스가 개발하는 액션 어드벤처 게임이다.",
                                "excerpt": "붉은사막은 펄어비스가 개발하는 액션 어드벤처 게임이다.",
                            },
                            "https://example.com/blog/crimson-desert": {
                                "title": "붉은사막 관련 블로그",
                                "text": "붉은사막은 마법 세계관이 강점이라는 평이 있다.",
                                "excerpt": "붉은사막은 마법 세계관이 강점이라는 평이 있다.",
                            },
                        },
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-consensus-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertIn("개발: 펄어비스", response.text)
            self.assertIn("장르/성격:", response.text)
            self.assertNotIn("마법 세계관이 강점", response.text)

    def test_web_search_entity_summary_filters_operational_noise_from_intro_and_details(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            ),
                            SimpleNamespace(
                                title="붉은사막 업데이트 안내",
                                url="https://example.com/crimson-desert-update",
                                snippet="출시일 전 플레이 방지를 위해 데이원 패치 전에는 플레이를 못하게 해뒀다.",
                            ),
                        ],
                        pages={
                            "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89": {
                                "title": "붉은사막 - 나무위키",
                                "text": (
                                    "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. "
                                    "파이웰 대륙을 배경으로 탐험과 전투를 중심으로 진행된다. "
                                    "오픈월드 게임에서 가장 중요한 과제는 주변 정보 탐색이다. "
                                    "그중에서도 붉은사막은 게임 정보를 스스로 비춰서 찾아내야 하는 것이 대부분이다. "
                                    "싱글 플레이 중심 구조와 사실적인 전투 연출이 특징으로 소개된다. "
                                    "붉은사막 | 오픈월드 액션 어드벤처 - Pearl Abyss. "
                                    "여러분은 희생각기 클리프가 되어 다가오는 위험으로부터 세상을 구하기 위한 여정을 떠나게 됩니다."
                                ),
                                "excerpt": "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            },
                            "https://example.com/crimson-desert-update": {
                                "title": "붉은사막 업데이트 안내",
                                "text": (
                                    "출시일 전 플레이를 막기 위해 데이원 패치 전에는 플레이를 못하게 해뒀다. "
                                    "에픽게임즈 스토어에서 구매 시 주인공 클리프의 스킨을 받을 수 있다."
                                ),
                                "excerpt": "출시일 전 플레이를 막기 위해 데이원 패치 전에는 플레이를 못하게 해뒀다.",
                            },
                        },
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="붉은사막에 대해 알려줘",
                    session_id="crimson-desert-entity-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertIn("붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임입니다.", response.text)
            self.assertIn("장르/성격: 오픈월드 액션 어드벤처 게임", response.text)
            self.assertIn("개발: 펄어비스", response.text)
            self.assertIn("상태: 개발 중", response.text)
            self.assertIn("배경: 파이웰 대륙을 배경으로 탐험과 전투를 중심으로 진행된다", response.text)
            self.assertIn("특징: 싱글 플레이 중심 구조와 사실적인 전투 연출이 특징으로 소개된다", response.text)
            self.assertNotIn("주변 정보 탐색", response.text)
            self.assertNotIn("게임 정보를 스스로 비춰서", response.text)
            self.assertNotIn("붉은사막 업데이트 안내", response.text)
            self.assertNotIn("데이원 패치", response.text)
            self.assertNotIn("클리프의 스킨", response.text)
            self.assertNotIn("붉은사막 | 오픈월드 액션 어드벤처 - Pearl Abyss", response.text)
            self.assertNotIn("여러분은 희생각기 클리프가 되어", response.text)

    def test_irrelevant_result_feedback_retries_web_search_with_new_ranking(self) -> None:
        class _RetryingWebSearchTool:
            def __init__(self) -> None:
                self.call_count = 0

            def search(self, *, query: str, max_results: int = 5):
                self.call_count += 1
                if self.call_count == 1:
                    return [
                        SimpleNamespace(
                            title="BTS - YouTube",
                            url="https://www.youtube.com/@BTS",
                            snippet="BTS 공식 유튜브 채널.",
                        ),
                        SimpleNamespace(
                            title="BTS - 나무위키",
                            url="https://namu.wiki/w/BTS",
                            snippet="BTS는 대한민국의 7인조 보이 그룹이다.",
                        ),
                    ][:max_results]
                return [
                    SimpleNamespace(
                        title="BTS - 위키백과",
                        url="https://ko.wikipedia.org/wiki/BTS",
                        snippet="BTS는 대한민국의 보이 밴드로 2013년에 데뷔했다.",
                    ),
                    SimpleNamespace(
                        title="BTS - 공식 소개",
                        url="https://example.com/bts-profile",
                        snippet="BTS는 대한민국의 7인조 보이 그룹으로 글로벌 활동을 이어 가고 있다.",
                    ),
                ][:max_results]

            def fetch_page(self, *, url: str, max_chars: int | None = None):
                if "youtube.com" in url:
                    return SimpleNamespace(
                        url=url,
                        title="BTS - YouTube",
                        text="YouTube Google LLC 이용약관 개인정보 쿠키 정책 YouTube Premium",
                        excerpt="YouTube Google LLC 이용약관 개인정보 쿠키 정책",
                        content_type="text/html",
                    )
                raise RuntimeError("페이지 fetch fixture 없음")

        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            tool = _RetryingWebSearchTool()
            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": tool,
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            first = loop.handle(
                UserRequest(
                    user_text="BTS 알아봐줘",
                    session_id="retry-web-search-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )
            second = loop.handle(
                UserRequest(
                    user_text="BTS 알아봐줘",
                    session_id="retry-web-search-session",
                    metadata={
                        "web_search_permission": "enabled",
                        "retry_feedback_label": "incorrect",
                        "retry_feedback_reason": "irrelevant_result",
                    },
                )
            )

            self.assertEqual(first.actions_taken, ["web_search"])
            self.assertEqual(second.actions_taken, ["feedback_retry", "web_search_retry"])
            self.assertEqual(second.response_origin["provider"], "web")
            self.assertIn("다시 찾아봤습니다", second.text)
            self.assertIn("위키백과", second.text)
            self.assertNotIn("YouTube Premium", second.text)

    def test_enabled_web_search_request_without_space_still_uses_web_search(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="아이유 - 위키백과",
                                url="https://example.com/iu",
                                snippet="아이유는 대한민국의 가수이자 배우입니다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            response = loop.handle(
                UserRequest(
                    user_text="아이유검색해",
                    session_id="web-search-tight-suffix",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["web_search"])
            self.assertEqual(response.response_origin["provider"], "web")
            self.assertIn("웹 검색 요약: 아이유", response.text)

    def test_colloquial_web_search_requests_use_web_search(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="아이유 - 위키백과",
                                url="https://example.com/iu",
                                snippet="아이유는 대한민국의 가수이자 배우입니다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            phrases = [
                "아이유좀검색",
                "아이유 찾아와",
                "아이유 관련해서 좀 볼래",
            ]

            for index, phrase in enumerate(phrases, start=1):
                response = loop.handle(
                    UserRequest(
                        user_text=phrase,
                        session_id=f"web-search-colloquial-{index}",
                        metadata={"web_search_permission": "enabled"},
                    )
                )

                self.assertEqual(response.actions_taken, ["web_search"], phrase)
                self.assertEqual(response.response_origin["provider"], "web", phrase)
                self.assertIn("웹 검색 요약: 아이유", response.text, phrase)

    def test_recent_web_search_record_can_be_reloaded(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="이재용 - 위키백과",
                                url="https://example.com/lee-jaeyong",
                                snippet="이재용 관련 기본 정보를 정리한 문서입니다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            first = loop.handle(
                UserRequest(
                    user_text="이재용 검색해봐",
                    session_id="web-search-reload-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )
            second = loop.handle(
                UserRequest(
                    user_text="방금 검색한 결과 다시 보여줘",
                    session_id="web-search-reload-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(first.actions_taken, ["web_search"])
            self.assertEqual(second.actions_taken, ["load_web_search_record"])
            self.assertIn("최근 웹 검색 기록을 다시 불러왔습니다.", second.text)
            self.assertEqual(second.active_context["kind"], "web_search")
            self.assertEqual(second.web_search_record_path, first.web_search_record_path)

    def test_recent_web_search_record_can_drive_follow_up_answer(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="서울 날씨 - 예보",
                                url="https://example.com/seoul-weather",
                                snippet="서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
                            ),
                        ]
                    ),
                },
                notes_dir=str(tmp_path / "notes"),
                web_search_store=WebSearchStore(base_dir=str(tmp_path / "web-search")),
            )

            loop.handle(
                UserRequest(
                    user_text="서울 날씨 검색해봐",
                    session_id="web-search-follow-up-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )
            response = loop.handle(
                UserRequest(
                    user_text="방금 검색한 결과 핵심 3줄만 다시 정리해줘",
                    session_id="web-search-follow-up-session",
                    metadata={"web_search_permission": "enabled"},
                )
            )

            self.assertEqual(response.actions_taken, ["load_web_search_record", "answer_with_active_context"])
            self.assertIn("[모의 핵심 3줄]", response.text)
            self.assertEqual(response.active_context["kind"], "web_search")
            self.assertTrue(response.web_search_record_path)

    def test_underspecified_next_step_without_context_returns_clarification(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="다음엔 뭘 하면 돼요?",
                    session_id="next-step-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertEqual(response.actions_taken, ["respond_with_limitations"])
            self.assertIn("어떤 작업의 다음 단계인지 맥락이 조금 더 필요합니다", response.text)
            self.assertEqual(response.response_origin["provider"], "system")

    def test_uploaded_text_summary_works_without_source_path(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            uploaded_bytes = "# 업로드 문서\n\nhello world".encode("utf-8")
            response = loop.handle(
                UserRequest(
                    user_text="picked-source.md 파일을 요약해 주세요.",
                    session_id="uploaded-session",
                    metadata={
                        "uploaded_file": {
                            "name": "picked-source.md",
                            "mime_type": "text/markdown",
                            "size_bytes": len(uploaded_bytes),
                            "content_bytes": uploaded_bytes,
                        },
                    },
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("[모의 요약]", response.text)
            self.assertEqual(response.selected_source_paths, ["picked-source.md"])

    def test_uploaded_folder_search_surfaces_failed_file_notice(self) -> None:
        """업로드 검색 중 일부 파일 읽기가 실패하면 응답에
        실패 건수를 알리는 참고 문구가 포함됩니다."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            class _FailingReaderTool(FileReaderTool):
                def run_uploaded(self, *, name, content_bytes, mime_type=None):
                    if "corrupt" in name:
                        raise RuntimeError("simulated read failure")
                    return super().run_uploaded(name=name, content_bytes=content_bytes, mime_type=mime_type)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": _FailingReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="선택한 폴더에서 budget를 검색해 주세요.",
                    session_id="uploaded-search-failure-session",
                    metadata={
                        "search_query": "budget",
                        "search_only": True,
                        "uploaded_search_files": [
                            {
                                "name": "budget-plan.md",
                                "relative_path": "team-docs/budget-plan.md",
                                "root_label": "team-docs",
                                "mime_type": "text/markdown",
                                "size_bytes": len(b"budget discussion"),
                                "content_bytes": b"budget discussion",
                            },
                            {
                                "name": "corrupt-file.md",
                                "relative_path": "team-docs/corrupt-file.md",
                                "root_label": "team-docs",
                                "mime_type": "text/markdown",
                                "size_bytes": 10,
                                "content_bytes": b"irrelevant",
                            },
                        ],
                    },
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("검색 결과:", response.text)
            self.assertIn("budget-plan.md", response.text)
            self.assertIn("1건", response.text)
            self.assertIn("읽지 못해 검색에서 제외", response.text)

    def test_uploaded_folder_search_only_works_without_search_root(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="선택한 폴더에서 budget를 검색해 주세요.",
                    session_id="uploaded-search-session",
                    metadata={
                        "search_query": "budget",
                        "search_only": True,
                        "uploaded_search_files": [
                            {
                                "name": "budget-plan.md",
                                "relative_path": "team-docs/budget-plan.md",
                                "root_label": "team-docs",
                                "mime_type": "text/markdown",
                                "size_bytes": len(b"budget discussion"),
                                "content_bytes": b"budget discussion",
                            },
                            {
                                "name": "memo.md",
                                "relative_path": "team-docs/memo.md",
                                "root_label": "team-docs",
                                "mime_type": "text/markdown",
                                "size_bytes": len(b"other topic"),
                                "content_bytes": b"other topic",
                            },
                        ],
                    },
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("검색 결과:", response.text)
            self.assertEqual(response.actions_taken, ["search_uploaded_files"])
            self.assertEqual(response.selected_source_paths, ["team-docs/budget-plan.md"])

    def test_write_note_requires_approval(self) -> None:
        tool = WriteNoteTool()
        with self.assertRaises(PermissionError):
            tool.run(path="data/test-note.md", text="hello", approved=False)

    def test_summary_save_without_approval_requests_confirmation(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path} and save the summary",
                    session_id="session-1",
                    approved=False,
                    metadata={
                        "source_path": str(source_path),
                        "save_summary": True,
                    },
                )
            )

            self.assertTrue(response.requires_approval)
            self.assertEqual(response.status, "needs_approval")
            self.assertIsNotNone(response.approval)
            self.assertEqual(response.artifact_kind, "grounded_brief")
            self.assertTrue(str(response.artifact_id).startswith("artifact-"))
            self.assertEqual(response.approval["artifact_id"], response.artifact_id)
            self.assertEqual(response.approval["save_content_source"], "original_draft")
            self.assertEqual(response.source_message_id, response.approval["source_message_id"])
            self.assertIsNotNone(response.original_response_snapshot)
            self.assertEqual(response.original_response_snapshot["artifact_id"], response.artifact_id)
            self.assertEqual(response.original_response_snapshot["artifact_kind"], "grounded_brief")
            self.assertEqual(response.original_response_snapshot["draft_text"], response.text)
            self.assertEqual(response.original_response_snapshot["source_paths"], [str(source_path)])
            self.assertIsNone(response.original_response_snapshot["response_origin"])
            self.assertEqual(
                response.original_response_snapshot["summary_chunks_snapshot"],
                response.summary_chunks,
            )
            self.assertEqual(
                response.original_response_snapshot["evidence_snapshot"],
                response.evidence,
            )
            self.assertGreater(len(response.follow_up_suggestions), 0)
            self.assertIsNotNone(response.active_context)
            self.assertIsNotNone(response.proposed_note_path)
            self.assertIsNotNone(response.note_preview)
            self.assertGreaterEqual(len(response.evidence), 1)
            self.assertIn("# source.md 요약", response.note_preview or "")
            session = loop.session_store.get_session("session-1")
            self.assertEqual(len(session["pending_approvals"]), 1)
            self.assertEqual(session["active_context"]["label"], "source.md")
            self.assertEqual(session["pending_approvals"][0]["artifact_id"], response.artifact_id)
            self.assertEqual(session["pending_approvals"][0]["save_content_source"], "original_draft")
            self.assertEqual(session["pending_approvals"][0]["source_message_id"], response.source_message_id)
            self.assertEqual(session["messages"][-1]["artifact_id"], response.artifact_id)
            self.assertEqual(session["messages"][-1]["artifact_kind"], "grounded_brief")
            self.assertEqual(session["messages"][-1]["source_message_id"], response.source_message_id)
            self.assertEqual(session["messages"][-1]["original_response_snapshot"]["artifact_id"], response.artifact_id)
            self.assertEqual(
                session["messages"][-1]["original_response_snapshot"]["draft_text"],
                response.text,
            )
            self.assertFalse(Path(response.proposed_note_path or "").exists())
            log_records = [
                json.loads(line)
                for line in (tmp_path / "task_log.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            approval_record = next(record for record in log_records if record["action"] == "approval_requested")
            self.assertEqual(approval_record["detail"]["artifact_id"], response.artifact_id)
            self.assertEqual(approval_record["detail"]["source_message_id"], response.source_message_id)
            self.assertEqual(approval_record["detail"]["save_content_source"], "original_draft")

    def test_pending_approval_can_be_executed_once_by_approval_id(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "approved.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            first = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path} and save the summary",
                    session_id="session-approval",
                    metadata={
                        "source_path": str(source_path),
                        "save_summary": True,
                        "note_path": str(note_path),
                    },
                )
            )
            approval_id = first.approval["approval_id"]
            artifact_id = first.artifact_id
            source_message_id = first.approval["source_message_id"]

            second = loop.handle(
                UserRequest(
                    user_text="",
                    session_id="session-approval",
                    approved_approval_id=approval_id,
                )
            )
            third = loop.handle(
                UserRequest(
                    user_text="",
                    session_id="session-approval",
                    approved_approval_id=approval_id,
                )
            )

            self.assertEqual(second.status, "saved")
            self.assertEqual(second.artifact_id, artifact_id)
            self.assertEqual(second.artifact_kind, "grounded_brief")
            self.assertEqual(second.source_message_id, source_message_id)
            self.assertEqual(second.save_content_source, "original_draft")
            self.assertIsNone(second.corrected_outcome)
            self.assertTrue(note_path.exists())
            self.assertEqual(third.status, "error")
            self.assertIn("찾지 못했습니다", third.text)
            session = loop.session_store.get_session("session-approval")
            source_messages = [
                message
                for message in session["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ]
            self.assertTrue(source_messages)
            corrected_outcome = source_messages[-1].get("corrected_outcome")
            self.assertIsNotNone(corrected_outcome)
            self.assertEqual(corrected_outcome["outcome"], "accepted_as_is")
            self.assertEqual(corrected_outcome["artifact_id"], artifact_id)
            self.assertEqual(corrected_outcome["approval_id"], approval_id)
            self.assertEqual(corrected_outcome["saved_note_path"], str(note_path))
            self.assertEqual(corrected_outcome["source_message_id"], source_messages[-1]["message_id"])
            saved_messages = [
                message
                for message in session["messages"]
                if message.get("saved_note_path") == str(note_path)
            ]
            self.assertTrue(saved_messages)
            self.assertEqual(saved_messages[-1]["artifact_id"], artifact_id)
            self.assertEqual(saved_messages[-1]["source_message_id"], source_message_id)
            self.assertEqual(saved_messages[-1]["save_content_source"], "original_draft")
            log_records = [
                json.loads(line)
                for line in (tmp_path / "task_log.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            approval_granted = next(record for record in log_records if record["action"] == "approval_granted")
            write_note = next(record for record in log_records if record["action"] == "write_note" and record["detail"].get("approval_id") == approval_id)
            corrected_outcome_recorded = next(record for record in log_records if record["action"] == "corrected_outcome_recorded")
            self.assertEqual(approval_granted["detail"]["artifact_id"], artifact_id)
            self.assertEqual(approval_granted["detail"]["source_message_id"], source_message_id)
            self.assertEqual(approval_granted["detail"]["save_content_source"], "original_draft")
            self.assertEqual(write_note["detail"]["artifact_id"], artifact_id)
            self.assertEqual(write_note["detail"]["source_message_id"], source_message_id)
            self.assertEqual(write_note["detail"]["save_content_source"], "original_draft")
            self.assertEqual(corrected_outcome_recorded["detail"]["artifact_id"], artifact_id)
            self.assertEqual(corrected_outcome_recorded["detail"]["approval_id"], approval_id)
            self.assertEqual(corrected_outcome_recorded["detail"]["saved_note_path"], str(note_path))

    def test_pending_approval_can_be_reissued_with_new_path(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            first_note_path = tmp_path / "first.md"
            second_note_path = tmp_path / "notes" / "second.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            first = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path} and save the summary",
                    session_id="session-reissue",
                    metadata={
                        "source_path": str(source_path),
                        "save_summary": True,
                        "note_path": str(first_note_path),
                    },
                )
            )
            first_approval_id = first.approval["approval_id"]

            second = loop.handle(
                UserRequest(
                    user_text="",
                    session_id="session-reissue",
                    reissue_approval_id=first_approval_id,
                    metadata={"note_path": str(second_note_path)},
                )
            )

            self.assertEqual(second.status, "needs_approval")
            self.assertEqual(second.artifact_id, first.artifact_id)
            self.assertEqual(second.approval["artifact_id"], first.artifact_id)
            self.assertEqual(second.source_message_id, first.source_message_id)
            self.assertEqual(second.approval["source_message_id"], first.source_message_id)
            self.assertEqual(second.approval["save_content_source"], "original_draft")
            self.assertEqual(second.save_content_source, "original_draft")
            self.assertEqual(second.proposed_note_path, str(second_note_path))
            self.assertNotEqual(second.approval["approval_id"], first_approval_id)
            self.assertIsNotNone(second.approval_reason_record)
            self.assertEqual(second.approval_reason_record["reason_scope"], "approval_reissue")
            self.assertEqual(second.approval_reason_record["reason_label"], "path_change")
            self.assertEqual(second.approval_reason_record["artifact_id"], first.artifact_id)
            self.assertTrue(second.approval_reason_record["source_message_id"])
            self.assertEqual(second.approval_reason_record["approval_id"], second.approval["approval_id"])
            self.assertEqual(
                second.approval["approval_reason_record"]["approval_id"],
                second.approval["approval_id"],
            )
            self.assertIn("새 경로로 저장하려면 다시 승인해 주세요.", second.text)
            session = loop.session_store.get_session("session-reissue")
            self.assertEqual(len(session["pending_approvals"]), 1)
            self.assertEqual(session["pending_approvals"][0]["requested_path"], str(second_note_path))
            self.assertEqual(session["pending_approvals"][0]["artifact_id"], first.artifact_id)
            self.assertEqual(session["pending_approvals"][0]["source_message_id"], first.source_message_id)
            self.assertEqual(session["pending_approvals"][0]["save_content_source"], "original_draft")
            self.assertEqual(
                session["pending_approvals"][0]["approval_reason_record"]["reason_scope"],
                "approval_reissue",
            )
            self.assertEqual(
                session["messages"][-1]["approval_reason_record"]["approval_id"],
                second.approval["approval_id"],
            )
            log_records = [
                json.loads(line)
                for line in (tmp_path / "task_log.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            approval_reissued = next(record for record in log_records if record["action"] == "approval_reissued")
            self.assertEqual(approval_reissued["detail"]["source_message_id"], first.source_message_id)
            self.assertEqual(approval_reissued["detail"]["save_content_source"], "original_draft")
            self.assertEqual(
                approval_reissued["detail"]["approval_reason_record"]["approval_id"],
                second.approval["approval_id"],
            )

    def test_pending_approval_can_be_rejected_with_reason_record(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            first = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path} and save the summary",
                    session_id="session-reject",
                    metadata={
                        "source_path": str(source_path),
                        "save_summary": True,
                    },
                )
            )
            approval_id = first.approval["approval_id"]

            second = loop.handle(
                UserRequest(
                    user_text="",
                    session_id="session-reject",
                    rejected_approval_id=approval_id,
                )
            )

            self.assertEqual(second.status, "answer")
            self.assertIsNotNone(second.approval_reason_record)
            self.assertEqual(second.approval_reason_record["reason_scope"], "approval_reject")
            self.assertEqual(second.approval_reason_record["reason_label"], "explicit_rejection")
            self.assertTrue(second.approval_reason_record["source_message_id"])
            self.assertEqual(second.approval_reason_record["approval_id"], approval_id)
            self.assertEqual(second.approval_reason_record["artifact_id"], first.artifact_id)
            session = loop.session_store.get_session("session-reject")
            self.assertEqual(session["pending_approvals"], [])
            self.assertEqual(
                session["messages"][-1]["approval_reason_record"]["approval_id"],
                approval_id,
            )
            log_records = [
                json.loads(line)
                for line in (tmp_path / "task_log.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            approval_rejected = next(record for record in log_records if record["action"] == "approval_rejected")
            agent_response = next(
                record
                for record in log_records
                if record["action"] == "agent_response" and record["detail"].get("approval_reason_record")
            )
            self.assertEqual(
                approval_rejected["detail"]["approval_reason_record"]["reason_label"],
                "explicit_rejection",
            )
            self.assertEqual(
                agent_response["detail"]["approval_reason_record"]["approval_id"],
                approval_id,
            )

    def test_follow_up_question_uses_document_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            first = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="context-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            second = loop.handle(
                UserRequest(
                    user_text="이 문서 핵심만 다시 말해 주세요.",
                    session_id="context-session",
                )
            )

            self.assertEqual(first.status, "answer")
            self.assertEqual(second.status, "answer")
            self.assertIn("[모의 핵심 3줄]", second.text)
            self.assertIn("source.md", second.text)
            self.assertGreaterEqual(len(first.evidence), 1)
            self.assertGreaterEqual(len(second.evidence), 1)
            self.assertEqual(second.selected_source_paths, [str(source_path.resolve())])

    def test_follow_up_question_with_filename_uses_existing_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "local-ai-assistant-project-proposal.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="context-session-2",
                    metadata={"source_path": str(source_path)},
                )
            )
            second = loop.handle(
                UserRequest(
                    user_text="local-ai-assistant-project-proposal.md 핵심 3줄만 다시 정리해 주세요.",
                    session_id="context-session-2",
                )
            )

            self.assertEqual(second.status, "answer")
            self.assertIn("[모의 핵심 3줄]", second.text)
            self.assertIn("local-ai-assistant-project-proposal.md", second.text)

    def test_short_greeting_with_active_context_uses_general_response(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="small-talk-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            response = loop.handle(
                UserRequest(
                    user_text="반갑고",
                    session_id="small-talk-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("[모의 응답]", response.text)
            self.assertNotIn("[모의 문서 응답]", response.text)
            self.assertEqual(response.actions_taken, ["respond"])

    def test_mixed_greeting_with_active_context_uses_document_response(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="mixed-context-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            response = loop.handle(
                UserRequest(
                    user_text="안녕하세요. 이 문서 핵심만 다시 정리해 주세요.",
                    session_id="mixed-context-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("반갑습니다.", response.text)
            self.assertIn("[모의 핵심 3줄]", response.text)
            self.assertEqual(response.actions_taken, ["answer_with_active_context"])

    def test_mixed_follow_up_without_active_context_returns_gentle_guidance(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="안녕하세요. 이 문서 핵심만 다시 정리해 주세요.",
                    session_id="no-context-mixed-session",
                )
            )

            self.assertEqual(response.status, "error")
            self.assertIn("반갑습니다.", response.text)
            self.assertIn("현재 문서 문맥이 없습니다", response.text)

    def test_implicit_mixed_follow_up_uses_active_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="implicit-mixed-context-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            response = loop.handle(
                UserRequest(
                    user_text="안녕하세요. 조금 더 짧게 부탁드려요.",
                    session_id="implicit-mixed-context-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("반갑습니다.", response.text)
            self.assertIn("[모의 핵심 3줄]", response.text)
            self.assertEqual(response.actions_taken, ["answer_with_active_context"])

    def test_colloquial_memo_follow_up_uses_active_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="colloquial-memo-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            response = loop.handle(
                UserRequest(
                    user_text="오케이 그럼 메모처럼 바꿔 주세요.",
                    session_id="colloquial-memo-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("좋습니다.", response.text)
            self.assertIn("[모의 메모 재작성]", response.text)
            self.assertEqual(response.actions_taken, ["answer_with_active_context"])

    def test_action_style_follow_up_uses_action_items_intent(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text(
                "# Demo\n\n이 문서는 로컬 우선 원칙을 설명합니다.\n다음 행동: 승인 카드 UX를 정리합니다.",
                encoding="utf-8",
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="action-follow-up-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            response = loop.handle(
                UserRequest(
                    user_text="그럼 다음엔 뭘 하면 돼요?",
                    session_id="action-follow-up-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("[모의 실행 항목]", response.text)
            self.assertEqual(response.actions_taken, ["answer_with_active_context"])

    def test_context_does_not_hijack_plain_small_talk_question(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="general-small-talk-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            response = loop.handle(
                UserRequest(
                    user_text="근데 그냥 잡담인데 오늘 점심 뭐 먹지?",
                    session_id="general-small-talk-session",
                )
            )

            self.assertEqual(response.status, "answer")
            self.assertIn("[모의 응답]", response.text)
            self.assertEqual(response.actions_taken, ["respond"])

    def test_follow_up_without_active_context_returns_helpful_guidance(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="local-ai-assistant-project-proposal.md 핵심 3줄만 다시 정리해 주세요.",
                    session_id="no-context-session",
                )
            )

            self.assertEqual(response.status, "error")
            self.assertIn("현재 문서 문맥이 없습니다", response.text)

    def test_follow_up_intents_return_visibly_different_mock_outputs(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world. approve tasks. write memo.", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="intent-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            key_points = loop.handle(
                UserRequest(
                    user_text="source.md 핵심 3줄만 다시 정리해 주세요.",
                    session_id="intent-session",
                )
            )
            action_items = loop.handle(
                UserRequest(
                    user_text="source.md에서 실행할 일만 뽑아 주세요.",
                    session_id="intent-session",
                )
            )
            memo = loop.handle(
                UserRequest(
                    user_text="source.md 내용을 메모 형식으로 다시 써 주세요.",
                    session_id="intent-session",
                )
            )

            self.assertIn("[모의 핵심 3줄]", key_points.text)
            self.assertIn("[모의 실행 항목]", action_items.text)
            self.assertIn("[모의 메모 재작성]", memo.text)

    def test_follow_up_action_items_extract_document_specific_lines(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "proposal.md"
            source_path.write_text(
                "\n".join(
                    [
                        "# 로컬 AI 비서 프로젝트 제안서",
                        "",
                        "## 핵심 목표",
                        "- 로컬 우선 구조를 유지합니다.",
                        "- 승인 기반 저장을 제공합니다.",
                        "",
                        "## 즉시 실행 권고 사항",
                        "1. AGENTS.md와 운영 원칙을 확정합니다.",
                        "2. model_adapter intent 분기를 강화합니다.",
                        "3. 웹 승인 UX를 재정리합니다.",
                    ]
                ),
                encoding="utf-8",
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="action-extract-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            response = loop.handle(
                UserRequest(
                    user_text="proposal.md에서 실행할 일만 뽑아 주세요.",
                    session_id="action-extract-session",
                )
            )

            self.assertIn("AGENTS.md와 운영 원칙을 확정합니다", response.text)
            self.assertIn("model_adapter intent 분기를 강화합니다", response.text)
            self.assertGreaterEqual(len(response.evidence), 1)

    def test_long_document_follow_up_retrieves_middle_action_chunk(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "long-proposal.md"
            middle_action = "중간 섹션에서 승인 로그 정책을 확정합니다."
            source_path.write_text(
                "\n".join(
                    [
                        "# 긴 제안 문서",
                        "",
                        *["머리말 설명 문장입니다." for _ in range(420)],
                        "",
                        "## 즉시 실행 권고 사항",
                        f"1. {middle_action}",
                        "2. chunk retrieval을 도입합니다.",
                        "",
                        *["마무리 설명 문장입니다." for _ in range(420)],
                    ]
                ),
                encoding="utf-8",
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="long-doc-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            response = loop.handle(
                UserRequest(
                    user_text="이 문서에서 실행할 일만 뽑아 주세요.",
                    session_id="long-doc-session",
                )
            )

            self.assertIn(middle_action, response.text)
            self.assertTrue(any(middle_action[:12] in item["snippet"] for item in response.evidence))

    def test_follow_up_uses_grounded_evidence_excerpt_instead_of_full_noisy_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            model = _CaptureContextModel()
            session_store = SessionStore(base_dir=str(tmp_path / "sessions"))
            session_store.set_active_context(
                "grounded-follow-up-session",
                {
                    "kind": "web_search",
                    "label": "웹 검색: 붉은사막",
                    "source_paths": ["https://example.com/crimson-desert"],
                    "excerpt": (
                        "로그인 로그아웃 회원가입 전체메뉴 기사제보 PDF보기 English Deutsch Русский\n"
                        "붉은사막은 오픈월드 액션 어드벤처 게임으로, 파이웰 대륙을 배경으로 탐험과 전투를 중심으로 진행됩니다."
                    ),
                    "summary_hint": "붉은사막 관련 검색 결과 요약입니다.",
                    "suggested_prompts": [],
                    "evidence_pool": [
                        {
                            "source_path": "https://example.com/crimson-desert",
                            "source_name": "붉은사막 프리뷰",
                            "label": "웹 원문 근거",
                            "snippet": "붉은사막은 오픈월드 액션 어드벤처 게임으로, 파이웰 대륙을 배경으로 탐험과 전투를 중심으로 진행됩니다.",
                        }
                    ],
                    "retrieval_chunks": [
                        {
                            "chunk_id": "web-page-1-1",
                            "chunk_index": 1,
                            "total_chunks": 1,
                            "source_path": "https://example.com/crimson-desert",
                            "source_name": "붉은사막 프리뷰",
                            "text": (
                                "로그인 로그아웃 회원가입 전체메뉴 기사제보 PDF보기 English Deutsch Русский\n"
                                "붉은사막은 오픈월드 액션 어드벤처 게임으로, 파이웰 대륙을 배경으로 탐험과 전투를 중심으로 진행됩니다."
                            ),
                        }
                    ],
                },
            )

            loop = AgentLoop(
                model=model,
                session_store=session_store,
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="이 게임 핵심만 다시 알려 주세요.",
                    session_id="grounded-follow-up-session",
                    metadata={
                        "retry_feedback_label": "incorrect",
                        "retry_feedback_reason": "factual_error",
                    },
                )
            )

            self.assertEqual(response.actions_taken, ["feedback_retry", "answer_with_active_context"])
            self.assertIsNotNone(model.last_context_call)
            context_excerpt = str(model.last_context_call["context_excerpt"])
            self.assertIn("선택된 근거 묶음:", context_excerpt)
            self.assertIn("붉은사막은 오픈월드 액션 어드벤처 게임", context_excerpt)
            self.assertNotIn("로그인 로그아웃 회원가입", context_excerpt)
            self.assertEqual(model.last_context_call["summary_hint"], None)
            self.assertIn("제공된 근거만으로는 확인되지 않습니다.", str(model.last_context_call["user_request"]))
            self.assertIn("근거:", str(model.last_context_call["user_request"]))
            self.assertEqual(len(model.last_context_call["evidence_items"]), 1)
            self.assertEqual(response.evidence[0]["label"], "웹 원문 근거")

    def test_long_document_initial_summary_keeps_middle_chunk_signal(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "long-summary.md"
            middle_signal = "중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다."
            source_path.write_text(
                "\n".join(
                    [
                        "# 긴 요약 문서",
                        "",
                        *["도입 설명 문장입니다." for _ in range(360)],
                        "",
                        "## 핵심 결정",
                        middle_signal,
                        "추가로 로컬 우선 구조를 유지합니다.",
                        "",
                        *["마무리 설명 문장입니다." for _ in range(360)],
                    ]
                ),
                encoding="utf-8",
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="long-summary-session",
                    metadata={"source_path": str(source_path)},
                )
            )

            self.assertIn(middle_signal, response.text)
            self.assertTrue(any("승인 기반 저장" in item["snippet"] for item in response.evidence))
            self.assertGreaterEqual(len(response.summary_chunks), 1)
            self.assertIn(middle_signal, response.summary_chunks[0]["selected_line"])

    def test_summary_chunk_selection_splits_by_truthful_source_type(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )
            chunk_summaries = [
                {
                    "chunk_id": "chunk-1",
                    "index": 1,
                    "summary": "마지막에 갈등이 커지고 관계 변화가 더 선명해집니다.",
                    "source_path": str(tmp_path / "story.txt"),
                    "evidence": [
                        {
                            "source_path": str(tmp_path / "story.txt"),
                            "source_name": "story.txt",
                            "label": "본문 근거",
                            "snippet": "마지막에 갈등이 커지고 관계 변화가 더 선명해집니다.",
                        }
                    ],
                },
                {
                    "chunk_id": "chunk-2",
                    "index": 2,
                    "summary": "여러 결과를 종합하면 공통 정책은 로컬 저장 유지이고 우선 조정할 항목이 남아 있습니다.",
                    "source_path": str(tmp_path / "search-a.txt"),
                    "evidence": [
                        {
                            "source_path": str(tmp_path / "search-a.txt"),
                            "source_name": "search-a.txt",
                            "label": "본문 근거",
                            "snippet": "여러 결과를 종합하면 공통 정책은 로컬 저장 유지이고 우선 조정할 항목이 남아 있습니다.",
                        }
                    ],
                },
            ]

            local_refs = loop._build_summary_chunk_refs(
                chunk_summaries=chunk_summaries,
                max_items=1,
                summary_source_type="local_document",
            )
            search_refs = loop._build_summary_chunk_refs(
                chunk_summaries=chunk_summaries,
                max_items=1,
                summary_source_type="search_results",
            )

            self.assertEqual(
                set(local_refs[0].keys()),
                {"chunk_id", "chunk_index", "total_chunks", "source_path", "source_name", "selected_line"},
            )
            self.assertEqual(
                set(search_refs[0].keys()),
                {"chunk_id", "chunk_index", "total_chunks", "source_path", "source_name", "selected_line"},
            )
            self.assertIn("갈등", local_refs[0]["selected_line"])
            self.assertIn("종합하면 공통 정책", search_refs[0]["selected_line"])
            self.assertNotEqual(local_refs[0]["selected_line"], search_refs[0]["selected_line"])

    def test_long_narrative_summary_reduces_chunk_notes_into_one_flow(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "narrative.txt"
            source_path.write_text(
                "\n".join(
                    [
                        "3화. 모르는 척하는 사람이 제일 오래 버틴다",
                        "",
                        *["장면 도입 문장입니다." for _ in range(180)],
                        "영희가 태양에게 못 들은 척 못 하겠다고 말하며 둘의 감정선이 더는 숨겨지지 않습니다.",
                        *["감정 묘사 문장입니다." for _ in range(180)],
                        "철수는 태양에게 영희를 향한 진심을 털어놓고, 태양은 그 말을 들으며 더 깊이 흔들립니다.",
                        *["전시 장면 문장입니다." for _ in range(180)],
                        "영희는 마지막에 오늘 끝난 거 아니죠 라는 메시지를 보내며 관계가 계속될 것임을 남깁니다.",
                        *["마무리 장면 문장입니다." for _ in range(180)],
                    ]
                ),
                encoding="utf-8",
            )

            model = _NarrativeReduceModel()
            loop = AgentLoop(
                model=model,
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="long-narrative-summary-session",
                    metadata={"source_path": str(source_path)},
                )
            )

            self.assertEqual(
                response.text,
                "태양과 영희는 서로의 감정을 모른 척할 수 없게 되고, 철수는 그 변화를 모른 채 진심을 드러내며, 마지막에는 관계가 끝난 게 아니라는 신호가 다시 남습니다.",
            )
            self.assertGreaterEqual(len(response.summary_chunks), 1)
            local_chunk_prompts = [
                prompt
                for prompt in model.summary_inputs
                if "Summary mode: chunk_note" in prompt
            ]
            self.assertTrue(local_chunk_prompts)
            self.assertTrue(all("Summary source type: local_document" in prompt for prompt in local_chunk_prompts))
            self.assertTrue(
                any(
                    "part of a larger local document" in prompt
                    and "major characters or actors" in prompt
                    for prompt in local_chunk_prompts
                )
            )
            self.assertTrue(all("selected search-result excerpt" not in prompt for prompt in local_chunk_prompts))
            self.assertTrue(any("Summary mode: merged_chunk_outline" in prompt for prompt in model.summary_inputs))
            self.assertTrue(
                any(
                    "Summary source type: local_document" in prompt
                    for prompt in model.summary_inputs
                    if "Summary mode: merged_chunk_outline" in prompt
                )
            )

    def test_short_local_document_summary_uses_local_document_prompt(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "short-narrative.txt"
            source_path.write_text(
                "\n".join(
                    [
                        "태양과 영희는 전시 준비를 함께 하며 서로의 긴장을 숨기지 못합니다.",
                        "철수는 그 변화를 눈치채지 못한 채 일정을 밀어붙입니다.",
                        "마지막에는 영희가 오늘 끝난 건 아니라고 말합니다.",
                    ]
                ),
                encoding="utf-8",
            )

            model = _ShortSummaryCaptureModel()
            loop = AgentLoop(
                model=model,
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="short-local-summary-session",
                    metadata={"source_path": str(source_path)},
                )
            )

            self.assertEqual(
                response.text,
                "태양과 영희의 긴장이 커지고 철수는 변화를 놓친 채 일정을 밀어붙이며, 마지막에는 관계가 아직 끝나지 않았다는 신호가 남습니다.",
            )
            self.assertEqual(response.summary_chunks, [])
            short_prompts = [
                prompt
                for prompt in model.summary_inputs
                if "Summary mode: short_summary" in prompt
            ]
            self.assertTrue(short_prompts)
            self.assertTrue(all("Summary source type: local_document" in prompt for prompt in short_prompts))
            self.assertTrue(
                any(
                    "local document summary" in prompt
                    and "document flow or state changes even when the text is short" in prompt
                    and "major characters or actors" in prompt
                    and "Return only concise Korean plain text with no heading or bullet label." in prompt
                    for prompt in short_prompts
                )
            )
            self.assertTrue(all("search-result text" not in prompt for prompt in short_prompts))
            self.assertTrue(all("Summary mode: chunk_note" not in prompt for prompt in model.summary_inputs))
            self.assertTrue(all("Summary mode: merged_chunk_outline" not in prompt for prompt in model.summary_inputs))
            self.assertTrue(
                all("STRICT:" in prompt and "Do not add events that did not happen" in prompt for prompt in short_prompts),
                "local document short summary must include strict source-anchored faithfulness rule",
            )

    def test_local_document_prompt_strict_rule_absent_in_search_results(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )
            local_chunk = loop._build_individual_chunk_summary_prompt(
                source_label="story.txt",
                chunk_text="태양이 영희에게 말한다.",
                summary_source_type="local_document",
            )
            search_chunk = loop._build_individual_chunk_summary_prompt(
                source_label="result.txt",
                chunk_text="검색 결과입니다.",
                summary_source_type="search_results",
            )
            local_short = loop._build_short_summary_prompt(
                source_label="story.txt",
                text="태양이 영희에게 말한다.",
                summary_source_type="local_document",
            )
            search_short = loop._build_short_summary_prompt(
                source_label="result.txt",
                text="검색 결과입니���.",
                summary_source_type="search_results",
            )
            local_reduce = loop._build_chunk_summary_reduce_prompt(
                source_label="story.txt",
                chunk_summaries=[{"summary": "chunk 1 요약", "chunk_id": "c1", "index": 1, "source_path": "story.txt"}],
                reduce_source_type="local_document",
            )
            search_reduce = loop._build_chunk_summary_reduce_prompt(
                source_label="result.txt",
                chunk_summaries=[{"summary": "chunk 1 요약", "chunk_id": "c1", "index": 1, "source_path": "result.txt"}],
                reduce_source_type="search_results",
            )
            for label, prompt in [("local_chunk", local_chunk), ("local_short", local_short), ("local_reduce", local_reduce)]:
                self.assertIn("STRICT:", prompt, f"{label} must contain STRICT rule")
                self.assertIn("Do not add events that did not happen", prompt, f"{label} must forbid fabricated events")
            for label, prompt in [("search_chunk", search_chunk), ("search_short", search_short), ("search_reduce", search_reduce)]:
                self.assertNotIn("STRICT:", prompt, f"{label} must NOT contain STRICT rule")

    def test_target_length_guidance_in_all_summary_prompts(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )
            local_chunk = loop._build_individual_chunk_summary_prompt(
                source_label="doc.txt", chunk_text="내용입니다.", summary_source_type="local_document",
            )
            search_chunk = loop._build_individual_chunk_summary_prompt(
                source_label="res.txt", chunk_text="결과입니다.", summary_source_type="search_results",
            )
            local_short = loop._build_short_summary_prompt(
                source_label="doc.txt", text="내용입니다.", summary_source_type="local_document",
            )
            search_short = loop._build_short_summary_prompt(
                source_label="res.txt", text="결과입니다.", summary_source_type="search_results",
            )
            local_reduce = loop._build_chunk_summary_reduce_prompt(
                source_label="doc.txt",
                chunk_summaries=[{"summary": "요약", "chunk_id": "c1", "index": 1, "source_path": "doc.txt"}],
                reduce_source_type="local_document",
            )
            search_reduce = loop._build_chunk_summary_reduce_prompt(
                source_label="res.txt",
                chunk_summaries=[{"summary": "요약", "chunk_id": "c1", "index": 1, "source_path": "res.txt"}],
                reduce_source_type="search_results",
            )
            # local_document: all three prompts must have Target length guidance
            for label, prompt in [("local_chunk", local_chunk), ("local_short", local_short), ("local_reduce", local_reduce)]:
                self.assertIn("Target length:", prompt, f"{label} must contain Target length guidance")
            # search_results: all three prompts now have Target length guidance
            for label, prompt in [("search_chunk", search_chunk), ("search_short", search_short), ("search_reduce", search_reduce)]:
                self.assertIn("Target length:", prompt, f"{label} must contain Target length guidance")

    def test_search_short_summary_sparse_input_escape_hatch(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )
            search_short = loop._build_short_summary_prompt(
                source_label="res.txt", text="결과입니다.", summary_source_type="search_results",
            )
            self.assertIn(
                "For sparse or single-result input, 2~3 sentences (120~250 Korean characters) are acceptable",
                search_short,
                "search_results short_summary must contain sparse-input escape hatch with character range",
            )

    def test_search_reduce_two_note_target_length_escape_hatch(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )
            two_note_reduce = loop._build_chunk_summary_reduce_prompt(
                source_label="res.txt",
                chunk_summaries=[
                    {"summary": "첫 번째 검색 결과 요약", "chunk_id": "c1", "index": 1, "source_path": "res.txt"},
                    {"summary": "두 번째 검색 결과 요약", "chunk_id": "c2", "index": 2, "source_path": "res.txt"},
                ],
                reduce_source_type="search_results",
            )
            self.assertIn(
                "For two-note input, 3~5 sentences (220~420 Korean characters) are acceptable",
                two_note_reduce,
                "search_results reduce prompt with 2 chunks must contain two-note escape hatch",
            )
            three_note_reduce = loop._build_chunk_summary_reduce_prompt(
                source_label="res.txt",
                chunk_summaries=[
                    {"summary": "요약1", "chunk_id": "c1", "index": 1, "source_path": "res.txt"},
                    {"summary": "요약2", "chunk_id": "c2", "index": 2, "source_path": "res.txt"},
                    {"summary": "요약3", "chunk_id": "c3", "index": 3, "source_path": "res.txt"},
                ],
                reduce_source_type="search_results",
            )
            self.assertNotIn(
                "two-note input",
                three_note_reduce,
                "search_results reduce prompt with 3 chunks must NOT contain two-note escape hatch",
            )

    def test_long_search_summary_reduce_uses_search_result_synthesis_prompt(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_path = tmp_path / "budget-plan.md"
            second_path = tmp_path / "budget-actions.md"
            first_path.write_text(
                "\n".join(
                    [
                        "# 예산 계획",
                        *["예산 통제와 승인 기반 저장 유지가 중요하다는 설명입니다." for _ in range(220)],
                        "이번 분기 예산 계획은 승인 기반 저장을 유지하면서 비용 초과를 줄이는 데 초점을 둡니다.",
                    ]
                ),
                encoding="utf-8",
            )
            second_path.write_text(
                "\n".join(
                    [
                        "# 예산 실행 항목",
                        *["예산 실행 항목과 우선순위를 정리하는 설명입니다." for _ in range(220)],
                        "운영비 절감과 승인 대기 항목 정리가 우선이며, 팀별 집행 순서를 다시 조정해야 합니다.",
                    ]
                ),
                encoding="utf-8",
            )

            model = _SearchReduceModel()
            loop = AgentLoop(
                model=model,
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )
            selected_results = [
                FileSearchResult(
                    path=str(first_path),
                    matched_on="content",
                    snippet="예산 통제와 승인 기반 저장 유지가 중요하다고 설명합니다.",
                ),
                FileSearchResult(
                    path=str(second_path),
                    matched_on="content",
                    snippet="운영비 절감과 승인 대기 항목 정리를 우선 과제로 제시합니다.",
                ),
            ]
            read_results = [loop.tools["read_file"].run(path=str(first_path)), loop.tools["read_file"].run(path=str(second_path))]

            summary, note_body, summary_chunks = loop._build_multi_file_summary(
                search_query="budget",
                selected_results=selected_results,
                read_results=read_results,
            )

            self.assertEqual(
                summary,
                "여러 검색 결과를 종합하면 예산 통제와 승인 기반 저장 유지가 공통으로 강조되고, 문서마다 실행 항목의 우선순위와 범위에는 차이가 있다는 점이 함께 드러납니다.",
            )
            self.assertIn("검색어: budget", note_body)
            self.assertGreaterEqual(len(summary_chunks), 1)
            search_reduce_prompts = [
                prompt
                for prompt in model.summary_inputs
                if "Summary mode: merged_chunk_outline" in prompt
            ]
            search_chunk_prompts = [
                prompt
                for prompt in model.summary_inputs
                if "Summary mode: chunk_note" in prompt
            ]
            self.assertTrue(search_chunk_prompts)
            self.assertTrue(all("Summary source type: search_results" in prompt for prompt in search_chunk_prompts))
            self.assertTrue(
                any(
                    "selected search-result excerpt" in prompt.lower()
                    and "source-backed evidence chunk within a larger search-result synthesis" in prompt
                    and "meaningful differences, and explicit actions or decisions" in prompt
                    for prompt in search_chunk_prompts
                )
            )
            self.assertTrue(all("major characters or actors" not in prompt for prompt in search_chunk_prompts))
            self.assertTrue(search_reduce_prompts)
            self.assertTrue(any("Summary source type: search_results" in prompt for prompt in search_reduce_prompts))
            self.assertTrue(
                any(
                    "selected search-result notes" in prompt
                    and "shared facts, meaningful differences, key actions or decisions, and the grounded conclusion" in prompt
                    for prompt in search_reduce_prompts
                )
            )
            self.assertTrue(
                all("major characters or actors" not in prompt for prompt in search_reduce_prompts)
            )

    def test_short_search_summary_uses_search_result_short_prompt(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_path = tmp_path / "budget-plan.md"
            second_path = tmp_path / "budget-actions.md"
            first_path.write_text(
                "\n".join(
                    [
                        "# 예산 계획",
                        "예산 통제와 승인 기반 저장 유지를 계속 유지해야 합니다.",
                    ]
                ),
                encoding="utf-8",
            )
            second_path.write_text(
                "\n".join(
                    [
                        "# 예산 실행 항목",
                        "운영비 절감이 우선이고 팀별 집행 순서를 다시 조정해야 합니다.",
                    ]
                ),
                encoding="utf-8",
            )

            model = _ShortSummaryCaptureModel()
            loop = AgentLoop(
                model=model,
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )
            selected_results = [
                FileSearchResult(
                    path=str(first_path),
                    matched_on="content",
                    snippet="예산 통제와 승인 기반 저장 유지를 계속 유지해야 한다고 말합니다.",
                ),
                FileSearchResult(
                    path=str(second_path),
                    matched_on="content",
                    snippet="운영비 절감과 팀별 집행 순서 조정을 우선 과제로 제시합니다.",
                ),
            ]
            read_results = [loop.tools["read_file"].run(path=str(first_path)), loop.tools["read_file"].run(path=str(second_path))]

            summary, note_body, summary_chunks = loop._build_multi_file_summary(
                search_query="budget",
                selected_results=selected_results,
                read_results=read_results,
            )

            self.assertEqual(
                summary,
                "여러 검색 결과를 종합하면 예산 통제 유지가 공통으로 보이고, 문서마다 우선 실행 항목과 조정 범위가 다르다는 점이 함께 정리됩니다.",
            )
            self.assertIn("검색어: budget", note_body)
            self.assertEqual(summary_chunks, [])
            short_prompts = [
                prompt
                for prompt in model.summary_inputs
                if "Summary mode: short_summary" in prompt
            ]
            self.assertTrue(short_prompts)
            self.assertTrue(all("Summary source type: search_results" in prompt for prompt in short_prompts))
            self.assertTrue(
                any(
                    "selected local search results, not as one narrative document" in prompt
                    and "shared facts, meaningful differences, explicit actions or decisions, and the grounded conclusion supported by the selected results" in prompt
                    and "Return only concise Korean plain text with no heading or bullet label." in prompt
                    for prompt in short_prompts
                )
            )
            self.assertTrue(all("major characters or actors" not in prompt for prompt in short_prompts))
            self.assertTrue(all("Summary mode: chunk_note" not in prompt for prompt in model.summary_inputs))
            self.assertTrue(all("Summary mode: merged_chunk_outline" not in prompt for prompt in model.summary_inputs))

    def test_summary_save_with_approval_writes_note(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path} and save the summary",
                    session_id="session-2",
                    approved=True,
                    metadata={
                        "source_path": str(source_path),
                        "save_summary": True,
                    },
                )
            )

            self.assertFalse(response.requires_approval)
            self.assertIsNotNone(response.saved_note_path)
            self.assertTrue(str(response.artifact_id).startswith("artifact-"))
            self.assertEqual(response.artifact_kind, "grounded_brief")
            self.assertEqual(response.source_message_id, response.corrected_outcome["source_message_id"])
            self.assertEqual(response.save_content_source, "original_draft")
            self.assertIsNotNone(response.corrected_outcome)
            self.assertEqual(response.corrected_outcome["outcome"], "accepted_as_is")
            self.assertEqual(response.corrected_outcome["artifact_id"], response.artifact_id)
            self.assertEqual(response.corrected_outcome["saved_note_path"], response.saved_note_path)
            saved_path = Path(response.saved_note_path or "")
            self.assertTrue(saved_path.exists())
            self.assertIn("# source.md 요약", saved_path.read_text(encoding="utf-8"))
            session = loop.session_store.get_session("session-2")
            self.assertEqual(session["messages"][-1]["source_message_id"], response.source_message_id)
            self.assertEqual(session["messages"][-1]["save_content_source"], "original_draft")
            self.assertEqual(
                session["messages"][-1]["corrected_outcome"]["source_message_id"],
                session["messages"][-1]["message_id"],
            )
            log_records = [
                json.loads(line)
                for line in (tmp_path / "task_log.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            write_note = next(record for record in log_records if record["action"] == "write_note")
            corrected_outcome_recorded = next(record for record in log_records if record["action"] == "corrected_outcome_recorded")
            self.assertEqual(write_note["detail"]["artifact_id"], response.artifact_id)
            self.assertEqual(write_note["detail"]["source_message_id"], response.source_message_id)
            self.assertEqual(write_note["detail"]["save_content_source"], "original_draft")
            self.assertEqual(corrected_outcome_recorded["detail"]["artifact_id"], response.artifact_id)
            self.assertIsNone(corrected_outcome_recorded["detail"]["approval_id"])

    def test_non_utf8_summary_save_with_approval_writes_note(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "korean-note.txt"
            source_path.write_bytes("예산 요약 문서".encode("cp949"))

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path} and save the summary",
                    session_id="session-2b",
                    approved=True,
                    metadata={
                        "source_path": str(source_path),
                        "save_summary": True,
                    },
                )
            )

            self.assertFalse(response.requires_approval)
            self.assertIsNotNone(response.saved_note_path)
            saved_path = Path(response.saved_note_path or "")
            self.assertTrue(saved_path.exists())
            self.assertIn("# korean-note.txt 요약", saved_path.read_text(encoding="utf-8"))

    def test_session_store_records_corrected_text_on_grounded_brief_source_message(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            store = SessionStore(base_dir=str(tmp_path / "sessions"))

            store.append_message("session-correction", {"role": "user", "text": "질문"})
            stored_message = store.append_message(
                "session-correction",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-correction",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": [str(source_path)],
                    "evidence": [
                        {
                            "source_path": str(source_path),
                            "source_name": "source.md",
                            "label": "본문 근거",
                            "snippet": "hello world",
                        }
                    ],
                },
            )

            updated = store.record_correction_for_message(
                "session-correction",
                message_id=stored_message["message_id"],
                corrected_text="수정한 요약입니다.\n핵심만 남겼습니다.",
            )

            self.assertIsNotNone(updated)
            self.assertEqual(updated["corrected_text"], "수정한 요약입니다.\n핵심만 남겼습니다.")
            self.assertEqual(updated["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(updated["corrected_outcome"]["artifact_id"], "artifact-correction")
            self.assertEqual(updated["corrected_outcome"]["source_message_id"], stored_message["message_id"])
            self.assertEqual(updated["original_response_snapshot"]["draft_text"], "원본 요약입니다.")

            session = store.get_session("session-correction")
            source_messages = [
                message
                for message in session["messages"]
                if message.get("artifact_id") == "artifact-correction" and message.get("original_response_snapshot")
            ]
            self.assertTrue(source_messages)
            self.assertEqual(source_messages[-1]["corrected_text"], "수정한 요약입니다.\n핵심만 남겼습니다.")
            self.assertEqual(source_messages[-1]["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(source_messages[-1]["corrected_outcome"]["source_message_id"], stored_message["message_id"])

    def test_correction_updates_active_context_summary_hint(self) -> None:
        """교정 제출 후 active_context의 summary_hint가 corrected_text로 갱신되는지 확인."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            store = SessionStore(base_dir=str(tmp_path / "sessions"))

            store.append_message("session-hint-update", {"role": "user", "text": "요약해줘"})
            stored_message = store.append_message(
                "session-hint-update",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-hint",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": [str(source_path)],
                    "evidence": [
                        {
                            "source_path": str(source_path),
                            "source_name": "source.md",
                            "label": "본문 근거",
                            "snippet": "hello world",
                        }
                    ],
                },
            )

            store.set_active_context(
                "session-hint-update",
                {
                    "kind": "document",
                    "label": "source.md 요약",
                    "source_paths": [str(source_path)],
                    "excerpt": "hello world",
                    "summary_hint": "원본 요약입니다.",
                    "suggested_prompts": [],
                    "evidence_pool": [],
                    "retrieval_chunks": [],
                },
            )

            ctx_before = store.get_active_context("session-hint-update")
            self.assertEqual(ctx_before["summary_hint"], "원본 요약입니다.")

            store.record_correction_for_message(
                "session-hint-update",
                message_id=stored_message["message_id"],
                corrected_text="수정한 요약입니다. 핵심만 남겼습니다.",
            )

            ctx_after = store.get_active_context("session-hint-update")
            self.assertIsNotNone(ctx_after)
            self.assertEqual(ctx_after["summary_hint"], "수정한 요약입니다. 핵심만 남겼습니다.")

    def test_correction_without_active_context_does_not_fail(self) -> None:
        """active_context가 없는 상태에서 교정해도 에러 없이 동작하는지 확인."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Test", encoding="utf-8")
            store = SessionStore(base_dir=str(tmp_path / "sessions"))

            store.append_message("session-no-ctx", {"role": "user", "text": "요약해줘"})
            stored_message = store.append_message(
                "session-no-ctx",
                {
                    "role": "assistant",
                    "text": "원본 요약.",
                    "status": "answer",
                    "artifact_id": "artifact-no-ctx",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": [str(source_path)],
                    "evidence": [{"source_path": str(source_path), "source_name": "source.md", "label": "근거", "snippet": "Test"}],
                },
            )

            updated = store.record_correction_for_message(
                "session-no-ctx",
                message_id=stored_message["message_id"],
                corrected_text="수정된 요약.",
            )
            self.assertIsNotNone(updated)
            self.assertIsNone(store.get_active_context("session-no-ctx"))

    def test_rejected_content_verdict_records_reason_and_is_cleared_by_later_correction(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            store = SessionStore(base_dir=str(tmp_path / "sessions"))

            store.append_message("session-rejected-verdict", {"role": "user", "text": "질문"})
            stored_message = store.append_message(
                "session-rejected-verdict",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-rejected",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": [str(source_path)],
                    "evidence": [
                        {
                            "source_path": str(source_path),
                            "source_name": "source.md",
                            "label": "본문 근거",
                            "snippet": "hello world",
                        }
                    ],
                },
            )

            rejected = store.record_rejected_content_verdict_for_message(
                "session-rejected-verdict",
                message_id=stored_message["message_id"],
            )

            self.assertIsNotNone(rejected)
            self.assertEqual(rejected["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(rejected["corrected_outcome"]["artifact_id"], "artifact-rejected")
            self.assertEqual(rejected["corrected_outcome"]["source_message_id"], stored_message["message_id"])
            self.assertEqual(rejected["content_reason_record"]["reason_scope"], "content_reject")
            self.assertEqual(rejected["content_reason_record"]["reason_label"], "explicit_content_rejection")
            self.assertEqual(rejected["content_reason_record"]["artifact_kind"], "grounded_brief")
            self.assertNotIn("approval_reason_record", rejected)
            rejected_recorded_at = rejected["corrected_outcome"]["recorded_at"]

            noted = store.record_content_reason_note_for_message(
                "session-rejected-verdict",
                message_id=stored_message["message_id"],
                reason_note="핵심 결론이 문서 문맥과 다릅니다.",
            )

            self.assertIsNotNone(noted)
            self.assertEqual(noted["corrected_outcome"]["recorded_at"], rejected_recorded_at)
            self.assertEqual(noted["content_reason_record"]["reason_scope"], "content_reject")
            self.assertEqual(noted["content_reason_record"]["reason_label"], "explicit_content_rejection")
            self.assertEqual(noted["content_reason_record"]["reason_note"], "핵심 결론이 문서 문맥과 다릅니다.")

            corrected = store.record_correction_for_message(
                "session-rejected-verdict",
                message_id=stored_message["message_id"],
                corrected_text="다시 고친 요약입니다.",
            )

            self.assertIsNotNone(corrected)
            self.assertEqual(corrected["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(corrected["corrected_text"], "다시 고친 요약입니다.")
            self.assertNotIn("content_reason_record", corrected)

            session = store.get_session("session-rejected-verdict")
            source_messages = [
                message
                for message in session["messages"]
                if message.get("artifact_id") == "artifact-rejected" and message.get("original_response_snapshot")
            ]
            self.assertTrue(source_messages)
            latest_source = source_messages[-1]
            self.assertEqual(latest_source["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(latest_source["corrected_text"], "다시 고친 요약입니다.")
            self.assertNotIn("content_reason_record", latest_source)

    def test_rejected_content_reason_note_rejects_blank_submit(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            store = SessionStore(base_dir=str(tmp_path / "sessions"))

            store.append_message("session-rejected-note-blank", {"role": "user", "text": "질문"})
            stored_message = store.append_message(
                "session-rejected-note-blank",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-rejected-note-blank",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": [str(source_path)],
                    "evidence": [
                        {
                            "source_path": str(source_path),
                            "source_name": "source.md",
                            "label": "본문 근거",
                            "snippet": "hello world",
                        }
                    ],
                },
            )
            store.record_rejected_content_verdict_for_message(
                "session-rejected-note-blank",
                message_id=stored_message["message_id"],
            )

            with self.assertRaises(ValueError) as ctx:
                store.record_content_reason_note_for_message(
                    "session-rejected-note-blank",
                    message_id=stored_message["message_id"],
                    reason_note="   \n ",
                )

            self.assertIn("거절 메모를 입력해 주세요.", str(ctx.exception))

    def test_corrected_save_after_rejected_content_verdict_restores_corrected_outcome(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "source-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            initial = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="session-rejected-save",
                    metadata={"source_path": str(source_path)},
                )
            )
            artifact_id = initial.artifact_id
            source_message_id = initial.source_message_id
            self.assertIsNotNone(source_message_id)

            updated_source = loop.session_store.record_correction_for_message(
                "session-rejected-save",
                message_id=source_message_id or "",
                corrected_text="수정본 A입니다.\n핵심만 남겼습니다.",
            )
            self.assertIsNotNone(updated_source)

            rejected = loop.session_store.record_rejected_content_verdict_for_message(
                "session-rejected-save",
                message_id=source_message_id or "",
            )
            self.assertIsNotNone(rejected)
            self.assertEqual(rejected["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(rejected["corrected_text"], "수정본 A입니다.\n핵심만 남겼습니다.")
            noted = loop.session_store.record_content_reason_note_for_message(
                "session-rejected-save",
                message_id=source_message_id or "",
                reason_note="핵심 결론이 문맥과 다릅니다.",
            )
            self.assertIsNotNone(noted)
            self.assertEqual(noted["content_reason_record"]["reason_note"], "핵심 결론이 문맥과 다릅니다.")

            bridge = loop.handle(
                UserRequest(
                    user_text="",
                    session_id="session-rejected-save",
                    metadata={"corrected_save_message_id": source_message_id},
                )
            )
            self.assertEqual(bridge.status, "needs_approval")
            self.assertEqual(bridge.save_content_source, "corrected_text")
            self.assertIsNotNone(bridge.approval)
            approval_id = bridge.approval["approval_id"]

            approved = loop.handle(
                UserRequest(
                    user_text="",
                    session_id="session-rejected-save",
                    approved_approval_id=approval_id,
                )
            )

            self.assertEqual(approved.status, "saved")
            self.assertEqual(approved.save_content_source, "corrected_text")
            self.assertEqual(approved.saved_note_path, str(note_path))
            self.assertTrue(note_path.exists())
            self.assertEqual(note_path.read_text(encoding="utf-8"), "수정본 A입니다.\n핵심만 남겼습니다.")

            session = loop.session_store.get_session("session-rejected-save")
            source_messages = [
                message
                for message in session["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ]
            self.assertTrue(source_messages)
            source_message = source_messages[-1]
            self.assertEqual(source_message["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(source_message["corrected_outcome"]["approval_id"], approval_id)
            self.assertEqual(source_message["corrected_outcome"]["saved_note_path"], str(note_path))
            self.assertEqual(source_message["corrected_text"], "수정본 A입니다.\n핵심만 남겼습니다.")
            self.assertNotIn("content_reason_record", source_message)

    def test_session_local_memory_signal_keeps_latest_save_linkage_but_omits_stale_reject_note(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "source-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            store = SessionStore(base_dir=str(tmp_path / "sessions"))

            store.append_message("session-signal", {"role": "user", "text": "질문"})
            source_message = store.append_message(
                "session-signal",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-session-signal",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": [str(source_path)],
                    "evidence": [
                        {
                            "source_path": str(source_path),
                            "source_name": "source.md",
                            "label": "본문 근거",
                            "snippet": "hello world",
                        }
                    ],
                },
            )

            store.record_correction_for_message(
                "session-signal",
                message_id=source_message["message_id"],
                corrected_text="수정본 A입니다.\n핵심만 남겼습니다.",
            )
            store.record_corrected_outcome_for_artifact(
                "session-signal",
                artifact_id="artifact-session-signal",
                outcome="corrected",
                approval_id="approval-corrected",
                saved_note_path=str(note_path),
                preserve_existing=True,
            )
            store.append_message(
                "session-signal",
                {
                    "role": "assistant",
                    "text": f"승인 시점에 고정된 수정본을 {note_path}에 저장했습니다.",
                    "status": "saved",
                    "artifact_id": "artifact-session-signal",
                    "artifact_kind": "grounded_brief",
                    "source_message_id": source_message["message_id"],
                    "saved_note_path": str(note_path),
                    "save_content_source": "corrected_text",
                },
            )
            store.record_rejected_content_verdict_for_message(
                "session-signal",
                message_id=source_message["message_id"],
            )
            store.record_content_reason_note_for_message(
                "session-signal",
                message_id=source_message["message_id"],
                reason_note="핵심 결론이 문맥과 다릅니다.",
            )
            store.record_correction_for_message(
                "session-signal",
                message_id=source_message["message_id"],
                corrected_text="수정본 B입니다.\n다시 손봤습니다.",
            )

            session = store.get_session("session-signal")
            latest_source_message = [
                message
                for message in session["messages"]
                if message.get("artifact_id") == "artifact-session-signal" and message.get("original_response_snapshot")
            ][-1]

            signal = store.build_session_local_memory_signal(
                session,
                source_message=latest_source_message,
            )

            self.assertIsNotNone(signal)
            self.assertEqual(signal["signal_scope"], "session_local")
            self.assertEqual(signal["artifact_id"], "artifact-session-signal")
            self.assertEqual(signal["source_message_id"], source_message["message_id"])
            self.assertEqual(signal["content_signal"]["latest_corrected_outcome"]["outcome"], "corrected")
            self.assertTrue(signal["content_signal"]["has_corrected_text"])
            self.assertNotIn("content_reason_record", signal["content_signal"])
            self.assertEqual(signal["save_signal"]["latest_save_content_source"], "corrected_text")
            self.assertEqual(signal["save_signal"]["latest_saved_note_path"], str(note_path))
            self.assertNotIn("latest_approval_id", signal["save_signal"])

    def test_candidate_recurrence_key_helper_uses_explicit_pair_only_and_keeps_fingerprint_stable(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            service = WebAppService(
                settings=AppSettings(
                    sessions_dir=str(tmp_path / "sessions"),
                    task_log_path=str(tmp_path / "task_log.jsonl"),
                    notes_dir=str(tmp_path / "notes"),
                    model_provider="mock",
                )
            )

            def build_candidate(*, artifact_id: str, source_message_id: str, updated_at: str) -> dict[str, object]:
                return {
                    "candidate_id": (
                        f"session-local-candidate:{artifact_id}:{source_message_id}:correction_rewrite_preference"
                    ),
                    "candidate_scope": "session_local",
                    "candidate_family": "correction_rewrite_preference",
                    "statement": "explicit rewrite correction recorded for this grounded brief",
                    "supporting_artifact_ids": [artifact_id],
                    "supporting_source_message_ids": [source_message_id],
                    "supporting_signal_refs": [
                        {
                            "signal_name": "session_local_memory_signal.content_signal",
                            "relationship": "primary_basis",
                        }
                    ],
                    "evidence_strength": "explicit_single_artifact",
                    "status": "session_local_candidate",
                    "created_at": updated_at,
                    "updated_at": updated_at,
                }

            original_text = "원본 요약입니다.\n핵심을 설명합니다."
            corrected_text = "수정본 요약입니다.\n핵심만 남깁니다."
            recorded_at = "2026-03-28T00:00:00+00:00"
            first_message = {
                "message_id": "msg-a",
                "source_message_id": "msg-a",
                "artifact_id": "artifact-a",
                "artifact_kind": "grounded_brief",
                "original_response_snapshot": {
                    "artifact_id": "artifact-a",
                    "artifact_kind": "grounded_brief",
                    "draft_text": original_text,
                },
                "corrected_text": corrected_text,
                "corrected_outcome": {
                    "outcome": "corrected",
                    "recorded_at": recorded_at,
                    "artifact_id": "artifact-a",
                    "source_message_id": "msg-a",
                },
            }
            second_message = {
                "message_id": "msg-b",
                "source_message_id": "msg-b",
                "artifact_id": "artifact-b",
                "artifact_kind": "grounded_brief",
                "original_response_snapshot": {
                    "artifact_id": "artifact-b",
                    "artifact_kind": "grounded_brief",
                    "draft_text": original_text,
                },
                "corrected_text": corrected_text,
                "corrected_outcome": {
                    "outcome": "corrected",
                    "recorded_at": recorded_at,
                    "artifact_id": "artifact-b",
                    "source_message_id": "msg-b",
                },
            }

            first_key = service._serialize_candidate_recurrence_key(
                service._build_candidate_recurrence_key_for_message(
                    message=first_message,
                    session_local_candidate=build_candidate(
                        artifact_id="artifact-a",
                        source_message_id="msg-a",
                        updated_at=recorded_at,
                    ),
                )
            )
            second_key = service._serialize_candidate_recurrence_key(
                service._build_candidate_recurrence_key_for_message(
                    message=second_message,
                    session_local_candidate=build_candidate(
                        artifact_id="artifact-b",
                        source_message_id="msg-b",
                        updated_at=recorded_at,
                    ),
                )
            )

            self.assertIsNotNone(first_key)
            self.assertIsNotNone(second_key)
            self.assertEqual(first_key["key_scope"], "correction_rewrite_recurrence")
            self.assertEqual(first_key["key_version"], "explicit_pair_rewrite_delta_v1")
            self.assertEqual(first_key["normalized_delta_fingerprint"], second_key["normalized_delta_fingerprint"])
            self.assertEqual(first_key["rewrite_dimensions"], second_key["rewrite_dimensions"])

            reviewed_without_pair = {
                "message_id": "msg-reviewed",
                "source_message_id": "msg-reviewed",
                "artifact_id": "artifact-reviewed",
                "artifact_kind": "grounded_brief",
                "original_response_snapshot": {
                    "artifact_id": "artifact-reviewed",
                    "artifact_kind": "grounded_brief",
                    "draft_text": original_text,
                },
                "corrected_outcome": {
                    "outcome": "accepted_as_is",
                    "recorded_at": recorded_at,
                    "artifact_id": "artifact-reviewed",
                    "source_message_id": "msg-reviewed",
                },
                "candidate_review_record": {
                    "candidate_id": (
                        "session-local-candidate:artifact-reviewed:msg-reviewed:"
                        "correction_rewrite_preference"
                    ),
                    "candidate_updated_at": recorded_at,
                    "artifact_id": "artifact-reviewed",
                    "source_message_id": "msg-reviewed",
                    "review_scope": "source_message_candidate_review",
                    "review_action": "accept",
                    "review_status": "accepted",
                    "recorded_at": recorded_at,
                },
            }
            reviewed_without_pair_key = service._build_candidate_recurrence_key_for_message(
                message=reviewed_without_pair,
                session_local_candidate=build_candidate(
                    artifact_id="artifact-reviewed",
                    source_message_id="msg-reviewed",
                    updated_at=recorded_at,
                ),
            )
            self.assertIsNone(reviewed_without_pair_key)

    def test_recurrence_aggregate_candidates_helper_requires_exact_identity_and_distinct_anchors(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            service = WebAppService(
                settings=AppSettings(
                    sessions_dir=str(tmp_path / "sessions"),
                    task_log_path=str(tmp_path / "task_log.jsonl"),
                    notes_dir=str(tmp_path / "notes"),
                    model_provider="mock",
                )
            )

            base_identity = {
                "candidate_family": "correction_rewrite_preference",
                "key_scope": "correction_rewrite_recurrence",
                "key_version": "explicit_pair_rewrite_delta_v1",
                "derivation_source": "explicit_corrected_pair",
                "normalized_delta_fingerprint": "sha256:shared-fingerprint",
                "stability": "deterministic_local",
            }

            aggregate_candidates = service._build_recurrence_aggregate_candidates(
                [
                    {
                        "message_id": "msg-a",
                        "source_message_id": "msg-a",
                        "artifact_id": "artifact-a",
                        "artifact_kind": "grounded_brief",
                        "original_response_snapshot": {
                            "artifact_id": "artifact-a",
                            "artifact_kind": "grounded_brief",
                            "draft_text": "원본 요약입니다.",
                        },
                        "candidate_recurrence_key": {
                            **base_identity,
                            "source_candidate_id": "candidate-a:v1",
                            "source_candidate_updated_at": "2026-03-28T00:00:00+00:00",
                            "derived_at": "2026-03-28T00:00:00+00:00",
                        },
                    },
                    {
                        "message_id": "msg-a",
                        "source_message_id": "msg-a",
                        "artifact_id": "artifact-a",
                        "artifact_kind": "grounded_brief",
                        "original_response_snapshot": {
                            "artifact_id": "artifact-a",
                            "artifact_kind": "grounded_brief",
                            "draft_text": "원본 요약입니다.",
                        },
                        "candidate_recurrence_key": {
                            **base_identity,
                            "source_candidate_id": "candidate-a:v2",
                            "source_candidate_updated_at": "2026-03-28T00:05:00+00:00",
                            "derived_at": "2026-03-28T00:05:00+00:00",
                        },
                        "candidate_review_record": {
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "review_scope": "source_message_candidate_review",
                            "review_action": "accept",
                            "review_status": "accepted",
                            "recorded_at": "2026-03-28T00:06:00+00:00",
                        },
                    },
                    {
                        "message_id": "msg-b",
                        "source_message_id": "msg-b",
                        "artifact_id": "artifact-b",
                        "artifact_kind": "grounded_brief",
                        "original_response_snapshot": {
                            "artifact_id": "artifact-b",
                            "artifact_kind": "grounded_brief",
                            "draft_text": "원본 요약입니다.",
                        },
                        "candidate_recurrence_key": {
                            **base_identity,
                            "source_candidate_id": "candidate-b:v1",
                            "source_candidate_updated_at": "2026-03-28T00:04:00+00:00",
                            "derived_at": "2026-03-28T00:04:00+00:00",
                        },
                    },
                    {
                        "message_id": "msg-c",
                        "source_message_id": "msg-c",
                        "artifact_id": "artifact-c",
                        "artifact_kind": "grounded_brief",
                        "original_response_snapshot": {
                            "artifact_id": "artifact-c",
                            "artifact_kind": "grounded_brief",
                            "draft_text": "원본 요약입니다.",
                        },
                        "candidate_recurrence_key": {
                            **base_identity,
                            "normalized_delta_fingerprint": "sha256:different-fingerprint",
                            "source_candidate_id": "candidate-c:v1",
                            "source_candidate_updated_at": "2026-03-28T00:07:00+00:00",
                            "derived_at": "2026-03-28T00:07:00+00:00",
                        },
                        "candidate_review_record": {
                            "candidate_id": "candidate-c:v1",
                            "candidate_updated_at": "2026-03-28T00:07:00+00:00",
                            "artifact_id": "artifact-c",
                            "source_message_id": "msg-c",
                            "review_scope": "source_message_candidate_review",
                            "review_action": "accept",
                            "review_status": "accepted",
                            "recorded_at": "2026-03-28T00:08:00+00:00",
                        },
                    },
                    {
                        "message_id": "msg-d",
                        "source_message_id": "msg-d",
                        "artifact_id": "artifact-d",
                        "artifact_kind": "grounded_brief",
                        "original_response_snapshot": {
                            "artifact_id": "artifact-d",
                            "artifact_kind": "grounded_brief",
                            "draft_text": "원본 요약입니다.",
                        },
                        "durable_candidate": {
                            "candidate_id": "candidate-d:v1",
                            "candidate_scope": "durable_candidate",
                            "candidate_family": "correction_rewrite_preference",
                            "statement": "explicit rewrite correction recorded for this grounded brief",
                            "supporting_artifact_ids": ["artifact-d"],
                            "supporting_source_message_ids": ["msg-d"],
                            "supporting_signal_refs": [
                                {
                                    "signal_name": "session_local_memory_signal.content_signal",
                                    "relationship": "primary_basis",
                                }
                            ],
                            "supporting_confirmation_refs": [
                                {
                                    "artifact_id": "artifact-d",
                                    "source_message_id": "msg-d",
                                    "candidate_id": "candidate-d:v1",
                                    "candidate_updated_at": "2026-03-28T00:09:00+00:00",
                                    "confirmation_label": "explicit_reuse_confirmation",
                                    "recorded_at": "2026-03-28T00:09:00+00:00",
                                }
                            ],
                            "evidence_strength": "explicit_single_artifact",
                            "has_explicit_confirmation": True,
                            "promotion_basis": "explicit_confirmation",
                            "promotion_eligibility": "eligible_for_review",
                            "created_at": "2026-03-28T00:09:00+00:00",
                            "updated_at": "2026-03-28T00:09:00+00:00",
                        },
                        "historical_save_identity_signal": {
                            "artifact_id": "artifact-d",
                            "source_message_id": "msg-d",
                            "replay_source": "task_log_audit",
                            "approval_id": "approval-d",
                            "recorded_at": "2026-03-28T00:10:00+00:00",
                        },
                    },
                ]
            )

            self.assertEqual(len(aggregate_candidates), 1)
            aggregate = aggregate_candidates[0]
            self.assertEqual(
                aggregate["aggregate_key"],
                {
                    "candidate_family": "correction_rewrite_preference",
                    "key_scope": "correction_rewrite_recurrence",
                    "key_version": "explicit_pair_rewrite_delta_v1",
                    "derivation_source": "explicit_corrected_pair",
                    "normalized_delta_fingerprint": "sha256:shared-fingerprint",
                },
            )
            self.assertEqual(aggregate["recurrence_count"], 2)
            self.assertEqual(aggregate["scope_boundary"], "same_session_current_state_only")
            self.assertEqual(aggregate["confidence_marker"], "same_session_exact_key_match")
            self.assertEqual(aggregate["first_seen_at"], "2026-03-28T00:04:00+00:00")
            self.assertEqual(aggregate["last_seen_at"], "2026-03-28T00:05:00+00:00")
            self.assertEqual(
                aggregate["aggregate_promotion_marker"],
                {
                    "promotion_basis": "same_session_exact_recurrence_aggregate",
                    "promotion_eligibility": "blocked_pending_reviewed_memory_boundary",
                    "reviewed_memory_boundary": "not_open",
                    "marker_version": "same_session_blocked_reviewed_memory_v1",
                    "derived_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_precondition_status"],
                {
                    "status_version": "same_session_reviewed_memory_preconditions_v1",
                    "overall_status": "blocked_all_required",
                    "all_required": True,
                    "preconditions": [
                        "reviewed_memory_boundary_defined",
                        "rollback_ready_reviewed_memory_effect",
                        "disable_ready_reviewed_memory_effect",
                        "conflict_visible_reviewed_memory_scope",
                        "operator_auditable_reviewed_memory_transition",
                    ],
                    "evaluated_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_boundary_draft"],
                {
                    "boundary_version": "fixed_narrow_reviewed_scope_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": {
                        "candidate_family": "correction_rewrite_preference",
                        "key_scope": "correction_rewrite_recurrence",
                        "key_version": "explicit_pair_rewrite_delta_v1",
                        "derivation_source": "explicit_corrected_pair",
                        "normalized_delta_fingerprint": "sha256:shared-fingerprint",
                    },
                    "supporting_source_message_refs": [
                        {"artifact_id": "artifact-a", "source_message_id": "msg-a"},
                        {"artifact_id": "artifact-b", "source_message_id": "msg-b"},
                    ],
                    "supporting_candidate_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                        },
                        {
                            "artifact_id": "artifact-b",
                            "source_message_id": "msg-b",
                            "candidate_id": "candidate-b:v1",
                            "candidate_updated_at": "2026-03-28T00:04:00+00:00",
                        },
                    ],
                    "supporting_review_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                            "review_action": "accept",
                            "review_status": "accepted",
                            "recorded_at": "2026-03-28T00:06:00+00:00",
                        }
                    ],
                    "boundary_stage": "draft_not_applied",
                    "drafted_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_rollback_contract"],
                {
                    "rollback_version": "first_reviewed_memory_effect_reversal_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": {
                        "candidate_family": "correction_rewrite_preference",
                        "key_scope": "correction_rewrite_recurrence",
                        "key_version": "explicit_pair_rewrite_delta_v1",
                        "derivation_source": "explicit_corrected_pair",
                        "normalized_delta_fingerprint": "sha256:shared-fingerprint",
                    },
                    "supporting_source_message_refs": [
                        {"artifact_id": "artifact-a", "source_message_id": "msg-a"},
                        {"artifact_id": "artifact-b", "source_message_id": "msg-b"},
                    ],
                    "supporting_candidate_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                        },
                        {
                            "artifact_id": "artifact-b",
                            "source_message_id": "msg-b",
                            "candidate_id": "candidate-b:v1",
                            "candidate_updated_at": "2026-03-28T00:04:00+00:00",
                        },
                    ],
                    "supporting_review_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                            "review_action": "accept",
                            "review_status": "accepted",
                            "recorded_at": "2026-03-28T00:06:00+00:00",
                        }
                    ],
                    "rollback_target_kind": "future_applied_reviewed_memory_effect_only",
                    "rollback_stage": "contract_only_not_applied",
                    "audit_trace_expectation": "operator_visible_local_transition_required",
                    "defined_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_disable_contract"],
                {
                    "disable_version": "first_reviewed_memory_effect_stop_apply_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": {
                        "candidate_family": "correction_rewrite_preference",
                        "key_scope": "correction_rewrite_recurrence",
                        "key_version": "explicit_pair_rewrite_delta_v1",
                        "derivation_source": "explicit_corrected_pair",
                        "normalized_delta_fingerprint": "sha256:shared-fingerprint",
                    },
                    "supporting_source_message_refs": [
                        {"artifact_id": "artifact-a", "source_message_id": "msg-a"},
                        {"artifact_id": "artifact-b", "source_message_id": "msg-b"},
                    ],
                    "supporting_candidate_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                        },
                        {
                            "artifact_id": "artifact-b",
                            "source_message_id": "msg-b",
                            "candidate_id": "candidate-b:v1",
                            "candidate_updated_at": "2026-03-28T00:04:00+00:00",
                        },
                    ],
                    "supporting_review_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                            "review_action": "accept",
                            "review_status": "accepted",
                            "recorded_at": "2026-03-28T00:06:00+00:00",
                        }
                    ],
                    "disable_target_kind": "future_applied_reviewed_memory_effect_only",
                    "disable_stage": "contract_only_not_applied",
                    "effect_behavior": "stop_apply_without_reversal",
                    "audit_trace_expectation": "operator_visible_local_transition_required",
                    "defined_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_conflict_contract"],
                {
                    "conflict_version": "first_reviewed_memory_scope_visibility_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": {
                        "candidate_family": "correction_rewrite_preference",
                        "key_scope": "correction_rewrite_recurrence",
                        "key_version": "explicit_pair_rewrite_delta_v1",
                        "derivation_source": "explicit_corrected_pair",
                        "normalized_delta_fingerprint": "sha256:shared-fingerprint",
                    },
                    "supporting_source_message_refs": [
                        {"artifact_id": "artifact-a", "source_message_id": "msg-a"},
                        {"artifact_id": "artifact-b", "source_message_id": "msg-b"},
                    ],
                    "supporting_candidate_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                        },
                        {
                            "artifact_id": "artifact-b",
                            "source_message_id": "msg-b",
                            "candidate_id": "candidate-b:v1",
                            "candidate_updated_at": "2026-03-28T00:04:00+00:00",
                        },
                    ],
                    "supporting_review_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                            "review_action": "accept",
                            "review_status": "accepted",
                            "recorded_at": "2026-03-28T00:06:00+00:00",
                        }
                    ],
                    "conflict_target_categories": [
                        "future_reviewed_memory_candidate_draft_vs_applied_effect",
                        "future_applied_reviewed_memory_effect_vs_applied_effect",
                    ],
                    "conflict_visibility_stage": "contract_only_not_resolved",
                    "audit_trace_expectation": "operator_visible_local_transition_required",
                    "defined_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_transition_audit_contract"],
                {
                    "audit_version": "first_reviewed_memory_transition_identity_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": {
                        "candidate_family": "correction_rewrite_preference",
                        "key_scope": "correction_rewrite_recurrence",
                        "key_version": "explicit_pair_rewrite_delta_v1",
                        "derivation_source": "explicit_corrected_pair",
                        "normalized_delta_fingerprint": "sha256:shared-fingerprint",
                    },
                    "supporting_source_message_refs": [
                        {"artifact_id": "artifact-a", "source_message_id": "msg-a"},
                        {"artifact_id": "artifact-b", "source_message_id": "msg-b"},
                    ],
                    "supporting_candidate_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                        },
                        {
                            "artifact_id": "artifact-b",
                            "source_message_id": "msg-b",
                            "candidate_id": "candidate-b:v1",
                            "candidate_updated_at": "2026-03-28T00:04:00+00:00",
                        },
                    ],
                    "supporting_review_refs": [
                        {
                            "artifact_id": "artifact-a",
                            "source_message_id": "msg-a",
                            "candidate_id": "candidate-a:v2",
                            "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                            "review_action": "accept",
                            "review_status": "accepted",
                            "recorded_at": "2026-03-28T00:06:00+00:00",
                        }
                    ],
                    "transition_action_vocabulary": [
                        "future_reviewed_memory_apply",
                        "future_reviewed_memory_stop_apply",
                        "future_reviewed_memory_reversal",
                        "future_reviewed_memory_conflict_visibility",
                    ],
                    "transition_identity_requirement": "canonical_local_transition_id_required",
                    "operator_visible_reason_boundary": "explicit_reason_or_note_required",
                    "audit_stage": "contract_only_not_emitted",
                    "audit_store_boundary": "canonical_transition_record_separate_from_task_log",
                    "post_transition_invariants": "aggregate_identity_and_contract_refs_retained",
                    "defined_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertNotIn("reviewed_memory_transition_record", aggregate)
            self.assertEqual(
                aggregate["reviewed_memory_unblock_contract"],
                {
                    "unblock_version": "same_session_reviewed_memory_unblock_v1",
                    "required_preconditions": [
                        "reviewed_memory_boundary_defined",
                        "rollback_ready_reviewed_memory_effect",
                        "disable_ready_reviewed_memory_effect",
                        "conflict_visible_reviewed_memory_scope",
                        "operator_auditable_reviewed_memory_transition",
                    ],
                    "unblock_status": "blocked_all_required",
                    "satisfaction_basis_boundary": "canonical_reviewed_memory_layer_capabilities_only",
                    "partial_state_policy": "partial_states_not_materialized",
                    "evaluated_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_capability_status"],
                {
                    "capability_version": "same_session_reviewed_memory_capabilities_v1",
                    "required_preconditions": [
                        "reviewed_memory_boundary_defined",
                        "rollback_ready_reviewed_memory_effect",
                        "disable_ready_reviewed_memory_effect",
                        "conflict_visible_reviewed_memory_scope",
                        "operator_auditable_reviewed_memory_transition",
                    ],
                    "capability_outcome": "blocked_all_required",
                    "satisfaction_basis_boundary": "canonical_reviewed_memory_layer_capabilities_only",
                    "partial_state_policy": "partial_states_not_materialized",
                    "evaluated_at": "2026-03-28T00:05:00+00:00",
                },
            )
            source_context = {
                "source_version": "same_session_reviewed_memory_capability_source_refs_v1",
                "source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "required_preconditions": list(
                    aggregate["reviewed_memory_unblock_contract"]["required_preconditions"]
                ),
                "evaluated_at": "2026-03-28T00:05:00+00:00",
            }
            self.assertEqual(
                service._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
                    aggregate,
                    source_context,
                ),
                {
                    "ref_version": "same_session_reviewed_memory_boundary_source_ref_v1",
                    "ref_kind": "aggregate_reviewed_memory_trigger_affordance",
                    "ref_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                    "trigger_action_label": "검토 메모 적용 시작",
                    "trigger_state": "visible_disabled",
                    "target_label": "eligible_for_reviewed_memory_draft_planning_only",
                    "target_boundary": "reviewed_memory_draft_planning_only",
                    "defined_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate,
                    source_context,
                )
            )
            rollback_mismatched_source_context = dict(source_context)
            rollback_mismatched_source_context["aggregate_identity_ref"] = {
                "candidate_family": "different"
            }
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate,
                    rollback_mismatched_source_context,
                )
            )
            rollback_missing_precondition_context = dict(source_context)
            rollback_missing_precondition_context["required_preconditions"] = [
                item
                for item in source_context["required_preconditions"]
                if item != "rollback_ready_reviewed_memory_effect"
            ]
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate,
                    rollback_missing_precondition_context,
                )
            )
            aggregate_missing_rollback_contract = dict(aggregate)
            aggregate_missing_rollback_contract.pop("reviewed_memory_rollback_contract", None)
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_missing_rollback_contract,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_disable_source_ref(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_conflict_source_ref(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_transition_audit_source_ref(
                    aggregate,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
                    aggregate,
                    source_context,
                )
            )
            aggregate_without_boundary_draft = dict(aggregate)
            aggregate_without_boundary_draft.pop("reviewed_memory_boundary_draft", None)
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_without_boundary_draft,
                    source_context,
                )
            )
            aggregate_without_first_seen_at = dict(aggregate)
            aggregate_without_first_seen_at.pop("first_seen_at", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_without_first_seen_at,
                    source_context,
                )
            )
            self.assertNotIn("reviewed_memory_capability_source_refs", aggregate)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_source_refs(aggregate)
            )
            self.assertNotIn("reviewed_memory_capability_basis", aggregate)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_basis(aggregate)
            )
            self.assertEqual(
                aggregate["reviewed_memory_planning_target_ref"],
                {
                    "planning_target_version": "same_session_reviewed_memory_planning_target_ref_v1",
                    "target_label": "eligible_for_reviewed_memory_draft_planning_only",
                    "target_scope": "same_session_exact_recurrence_aggregate_only",
                    "target_boundary": "reviewed_memory_draft_planning_only",
                    "defined_at": "2026-03-28T00:05:00+00:00",
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_planning_target_ref"]["target_label"],
                "eligible_for_reviewed_memory_draft_planning_only",
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_transition_record(aggregate)
            )
            aggregate_with_task_log_replay = dict(aggregate)
            aggregate_with_task_log_replay["task_log_replay"] = {
                "canonical_transition_id": "transition-local-1",
                "operator_reason_or_note": "apply now",
                "emitted_at": "2026-03-28T00:07:00+00:00",
            }
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_source_refs(
                    aggregate_with_task_log_replay
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
                    aggregate_with_task_log_replay,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                    aggregate_with_task_log_replay,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate_with_task_log_replay,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate_with_task_log_replay,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_task_log_replay,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_task_log_replay,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_task_log_replay,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_basis(
                    aggregate_with_task_log_replay
                )
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_capability_status(
                    aggregate_with_task_log_replay
                ),
                aggregate["reviewed_memory_capability_status"],
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_transition_record(
                    aggregate_with_task_log_replay
                )
            )

    def test_local_effect_presence_proof_record_materializes_only_from_exact_internal_store_entry(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            service = WebAppService(
                settings=AppSettings(
                    sessions_dir=str(tmp_path / "sessions"),
                    task_log_path=str(tmp_path / "task_log.jsonl"),
                    notes_dir=str(tmp_path / "notes"),
                    model_provider="mock",
                )
            )

            base_identity = {
                "candidate_family": "correction_rewrite_preference",
                "key_scope": "correction_rewrite_recurrence",
                "key_version": "explicit_pair_rewrite_delta_v1",
                "derivation_source": "explicit_corrected_pair",
                "normalized_delta_fingerprint": "sha256:proof-record-fingerprint",
                "stability": "deterministic_local",
            }
            messages = [
                {
                    "message_id": "msg-proof-a",
                    "source_message_id": "msg-proof-a",
                    "artifact_id": "artifact-proof-a",
                    "artifact_kind": "grounded_brief",
                    "original_response_snapshot": {
                        "artifact_id": "artifact-proof-a",
                        "artifact_kind": "grounded_brief",
                        "draft_text": "원본 요약입니다.",
                    },
                    "candidate_recurrence_key": {
                        **base_identity,
                        "source_candidate_id": "candidate-proof-a:v1",
                        "source_candidate_updated_at": "2026-03-28T00:01:00+00:00",
                        "derived_at": "2026-03-28T00:01:00+00:00",
                    },
                },
                {
                    "message_id": "msg-proof-b",
                    "source_message_id": "msg-proof-b",
                    "artifact_id": "artifact-proof-b",
                    "artifact_kind": "grounded_brief",
                    "original_response_snapshot": {
                        "artifact_id": "artifact-proof-b",
                        "artifact_kind": "grounded_brief",
                        "draft_text": "원본 요약입니다.",
                    },
                    "candidate_recurrence_key": {
                        **base_identity,
                        "source_candidate_id": "candidate-proof-b:v1",
                        "source_candidate_updated_at": "2026-03-28T00:03:00+00:00",
                        "derived_at": "2026-03-28T00:03:00+00:00",
                    },
                },
            ]

            aggregate = service._build_recurrence_aggregate_candidates(messages)[0]
            source_context = service._build_recurrence_aggregate_reviewed_memory_source_context(
                aggregate
            )
            self.assertIsNotNone(source_context)
            boundary_source_ref = service._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
                aggregate,
                source_context or {},
            )
            self.assertIsNotNone(boundary_source_ref)
            proof_record_entry = (
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record_store_entry(
                    aggregate
                )
            )
            self.assertIsNotNone(proof_record_entry)
            expected_proof_record_entry = {
                "proof_record_version": "first_same_session_reviewed_memory_local_effect_presence_proof_record_v1",
                "proof_record_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "proof_capability_boundary": "local_effect_presence_only",
                "proof_record_stage": "canonical_presence_recorded_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_proof_record_entry["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                proof_record_entry,
                expected_proof_record_entry,
            )

            conflicting_proof_record_entry = dict(proof_record_entry)
            conflicting_proof_record_entry["applied_effect_id"] = "reviewed-memory-effect:stale"
            conflicting_proof_record_entry["present_locally_at"] = "2026-03-28T00:04:00+00:00"
            merged_proof_record_store_entries = (
                service._build_reviewed_memory_local_effect_presence_proof_record_store_entries(
                    [aggregate],
                    existing_entries=[conflicting_proof_record_entry],
                )
            )
            self.assertEqual(merged_proof_record_store_entries, [proof_record_entry])

            aggregate_with_store = service._build_recurrence_aggregate_candidates(
                messages,
                proof_record_store_entries=merged_proof_record_store_entries,
            )[0]
            proof_record = service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
                aggregate_with_store,
                source_context or {},
            )
            self.assertEqual(proof_record, proof_record_entry)
            expected_proof_boundary = {
                "proof_boundary_version": "first_same_session_reviewed_memory_local_effect_presence_proof_boundary_v1",
                "proof_boundary_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "proof_capability_boundary": "local_effect_presence_only",
                "proof_stage": "first_presence_proved_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_proof_boundary["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                    aggregate_with_store,
                    source_context,
                ),
                expected_proof_boundary,
            )
            expected_fact_source_instance = {
                "fact_source_instance_version": (
                    "first_same_session_reviewed_memory_local_effect_presence_fact_source_instance_v1"
                ),
                "fact_source_instance_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "fact_capability_boundary": "local_effect_presence_only",
                "fact_stage": "presence_fact_available_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_fact_source_instance["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate_with_store,
                    source_context,
                ),
                expected_fact_source_instance,
            )
            expected_fact_source = {
                "fact_source_version": "first_same_session_reviewed_memory_local_effect_presence_fact_source_v1",
                "fact_source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "fact_capability_boundary": "local_effect_presence_only",
                "fact_stage": "presence_fact_available_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_fact_source["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate_with_store,
                    source_context,
                ),
                expected_fact_source,
            )
            expected_event = {
                "event_version": "first_same_session_reviewed_memory_local_effect_presence_event_v1",
                "event_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "event_capability_boundary": "local_effect_presence_only",
                "event_stage": "presence_observed_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_event["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
                    aggregate_with_store,
                    source_context,
                ),
                expected_event,
            )
            expected_producer = {
                "producer_version": "first_same_session_reviewed_memory_local_effect_presence_event_producer_v1",
                "producer_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "producer_capability_boundary": "local_effect_presence_only",
                "producer_stage": "presence_event_recorded_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_producer["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                    aggregate_with_store,
                    source_context,
                ),
                expected_producer,
            )
            expected_event_source = {
                "event_source_version": "first_same_session_reviewed_memory_local_effect_presence_event_source_v1",
                "event_source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "event_capability_boundary": "local_effect_presence_only",
                "event_stage": "presence_event_recorded_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_event_source["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_with_store,
                    source_context,
                ),
                expected_event_source,
            )
            mismatched_event_source_context = dict(source_context)
            mismatched_event_source_context["aggregate_identity_ref"] = {"candidate_family": "different"}
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_with_store,
                    mismatched_event_source_context,
                )
            )
            expected_record = {
                "source_version": "first_same_session_reviewed_memory_local_effect_presence_record_v1",
                "source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "source_capability_boundary": "local_effect_presence_only",
                "source_stage": "presence_recorded_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_record["supporting_review_refs"] = list(aggregate["supporting_review_refs"])
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_with_store,
                    source_context,
                ),
                expected_record,
            )
            mismatched_record_context = dict(source_context)
            mismatched_record_context["aggregate_identity_ref"] = {"candidate_family": "different"}
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_with_store,
                    mismatched_record_context,
                )
            )
            expected_target = {
                "target_version": "first_same_session_reviewed_memory_applied_effect_target_v1",
                "target_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "target_capability_boundary": "local_effect_presence_only",
                "target_stage": "effect_present_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_target["supporting_review_refs"] = list(aggregate["supporting_review_refs"])
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_store,
                    source_context,
                ),
                expected_target,
            )
            mismatched_target_context = dict(source_context)
            mismatched_target_context["aggregate_identity_ref"] = {"candidate_family": "different"}
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_store,
                    mismatched_target_context,
                )
            )
            handle_identity_payload = {
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "rollback_contract_ref": dict(aggregate["reviewed_memory_rollback_contract"]),
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "defined_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                handle_identity_payload["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            expected_handle_id = (
                "reviewed-memory-handle:"
                + hashlib.sha256(
                    json.dumps(handle_identity_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()[:24]
            )
            expected_handle = {
                "handle_version": "first_same_session_reviewed_memory_reversible_effect_handle_v1",
                "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "rollback_contract_ref": dict(aggregate["reviewed_memory_rollback_contract"]),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "effect_capability": "reversible_local_only",
                "effect_invariant": "retain_identity_supporting_refs_boundary_and_audit",
                "effect_stage": "handle_defined_not_applied",
                "handle_id": expected_handle_id,
                "defined_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_handle["supporting_review_refs"] = list(aggregate["supporting_review_refs"])
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_store,
                    source_context,
                ),
                expected_handle,
            )
            mismatched_handle_context = dict(source_context)
            mismatched_handle_context["aggregate_identity_ref"] = {"candidate_family": "different"}
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_store,
                    mismatched_handle_context,
                )
            )
            self.assertEqual(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "ref_version": "same_session_reviewed_memory_rollback_source_ref_v1",
                    "ref_kind": "reviewed_memory_reversible_effect_handle",
                    "ref_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "handle_id": expected_handle_id,
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "effect_capability": "reversible_local_only",
                    "effect_stage": "handle_defined_not_applied",
                    "defined_at": aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(aggregate["supporting_review_refs"])}
                    if isinstance(aggregate.get("supporting_review_refs"), list)
                    and aggregate.get("supporting_review_refs")
                    else {}
                ),
            )
            expected_disable_source_ref = {
                "ref_version": "same_session_reviewed_memory_disable_source_ref_v1",
                "ref_kind": "reviewed_memory_disable_contract_backed_source",
                "ref_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "disable_contract_ref": dict(aggregate["reviewed_memory_disable_contract"]),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "effect_capability": "disable_local_only",
                "effect_stage": "disable_defined_not_applied",
                "defined_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_disable_source_ref["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                service._resolve_recurrence_aggregate_reviewed_memory_disable_source_ref(
                    aggregate_with_store,
                    source_context,
                ),
                expected_disable_source_ref,
            )
            disable_mismatched_context = dict(source_context)
            disable_mismatched_context["aggregate_identity_ref"] = {"candidate_family": "different"}
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_disable_source_ref(
                    aggregate_with_store,
                    disable_mismatched_context,
                )
            )
            disable_missing_precondition_context = dict(source_context)
            disable_missing_precondition_context["required_preconditions"] = [
                item
                for item in source_context["required_preconditions"]
                if item != "disable_ready_reviewed_memory_effect"
            ]
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_disable_source_ref(
                    aggregate_with_store,
                    disable_missing_precondition_context,
                )
            )
            aggregate_missing_disable_contract = dict(aggregate_with_store)
            aggregate_missing_disable_contract.pop("reviewed_memory_disable_contract", None)
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_disable_source_ref(
                    aggregate_missing_disable_contract,
                    source_context,
                )
            )
            expected_conflict_source_ref = {
                "ref_version": "same_session_reviewed_memory_conflict_source_ref_v1",
                "ref_kind": "reviewed_memory_conflict_contract_backed_source",
                "ref_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "conflict_contract_ref": dict(aggregate["reviewed_memory_conflict_contract"]),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "effect_capability": "conflict_visible_local_only",
                "effect_stage": "conflict_scope_defined_not_applied",
                "defined_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_conflict_source_ref["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                service._resolve_recurrence_aggregate_reviewed_memory_conflict_source_ref(
                    aggregate_with_store,
                    source_context,
                ),
                expected_conflict_source_ref,
            )
            conflict_mismatched_context = dict(source_context)
            conflict_mismatched_context["aggregate_identity_ref"] = {"candidate_family": "different"}
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_conflict_source_ref(
                    aggregate_with_store,
                    conflict_mismatched_context,
                )
            )
            conflict_missing_precondition_context = dict(source_context)
            conflict_missing_precondition_context["required_preconditions"] = [
                item
                for item in source_context["required_preconditions"]
                if item != "conflict_visible_reviewed_memory_scope"
            ]
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_conflict_source_ref(
                    aggregate_with_store,
                    conflict_missing_precondition_context,
                )
            )
            aggregate_missing_conflict_contract = dict(aggregate_with_store)
            aggregate_missing_conflict_contract.pop("reviewed_memory_conflict_contract", None)
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_conflict_source_ref(
                    aggregate_missing_conflict_contract,
                    source_context,
                )
            )
            expected_transition_audit_source_ref = {
                "ref_version": "same_session_reviewed_memory_transition_audit_source_ref_v1",
                "ref_kind": "reviewed_memory_transition_audit_contract_backed_source",
                "ref_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "transition_audit_contract_ref": dict(aggregate["reviewed_memory_transition_audit_contract"]),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "effect_capability": "transition_audit_local_only",
                "effect_stage": "audit_defined_not_emitted",
                "defined_at": aggregate["last_seen_at"],
            }
            if isinstance(aggregate.get("supporting_review_refs"), list) and aggregate.get(
                "supporting_review_refs"
            ):
                expected_transition_audit_source_ref["supporting_review_refs"] = list(
                    aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                service._resolve_recurrence_aggregate_reviewed_memory_transition_audit_source_ref(
                    aggregate_with_store,
                    source_context,
                ),
                expected_transition_audit_source_ref,
            )
            audit_mismatched_context = dict(source_context)
            audit_mismatched_context["aggregate_identity_ref"] = {"candidate_family": "different"}
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_transition_audit_source_ref(
                    aggregate_with_store,
                    audit_mismatched_context,
                )
            )
            audit_missing_precondition_context = dict(source_context)
            audit_missing_precondition_context["required_preconditions"] = [
                item
                for item in source_context["required_preconditions"]
                if item != "operator_auditable_reviewed_memory_transition"
            ]
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_transition_audit_source_ref(
                    aggregate_with_store,
                    audit_missing_precondition_context,
                )
            )
            aggregate_missing_audit_contract = dict(aggregate_with_store)
            aggregate_missing_audit_contract.pop("reviewed_memory_transition_audit_contract", None)
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_transition_audit_source_ref(
                    aggregate_missing_audit_contract,
                    source_context,
                )
            )
            capability_source_refs_result = (
                service._build_recurrence_aggregate_reviewed_memory_capability_source_refs(
                    aggregate_with_store
                )
            )
            self.assertIsNotNone(capability_source_refs_result)
            self.assertEqual(
                capability_source_refs_result["source_status"],
                "all_required_sources_present",
            )
            self.assertIn("capability_source_refs", capability_source_refs_result)
            self.assertIsNotNone(capability_source_refs_result["capability_source_refs"]["boundary_source_ref"])
            self.assertIsNotNone(capability_source_refs_result["capability_source_refs"]["rollback_source_ref"])
            self.assertIsNotNone(capability_source_refs_result["capability_source_refs"]["disable_source_ref"])
            self.assertIsNotNone(capability_source_refs_result["capability_source_refs"]["conflict_source_ref"])
            self.assertIsNotNone(capability_source_refs_result["capability_source_refs"]["transition_audit_source_ref"])
            self.assertIn("reviewed_memory_capability_basis", aggregate_with_store)
            capability_basis = aggregate_with_store["reviewed_memory_capability_basis"]
            self.assertEqual(capability_basis["basis_version"], "same_session_reviewed_memory_capability_basis_v1")
            self.assertEqual(capability_basis["reviewed_scope"], "same_session_exact_recurrence_aggregate_only")
            self.assertEqual(capability_basis["aggregate_identity_ref"], dict(aggregate_with_store["aggregate_key"]))
            self.assertEqual(
                capability_basis["supporting_source_message_refs"],
                list(aggregate_with_store["supporting_source_message_refs"]),
            )
            self.assertEqual(
                capability_basis["supporting_candidate_refs"],
                list(aggregate_with_store["supporting_candidate_refs"]),
            )
            self.assertEqual(
                capability_basis["required_preconditions"],
                list(aggregate_with_store["reviewed_memory_unblock_contract"]["required_preconditions"]),
            )
            self.assertEqual(capability_basis["basis_status"], "all_required_capabilities_present")
            self.assertEqual(capability_basis["satisfaction_basis_boundary"], "canonical_reviewed_memory_layer_capabilities_only")
            self.assertEqual(capability_basis["evaluated_at"], aggregate_with_store["last_seen_at"])
            self.assertEqual(
                aggregate_with_store["reviewed_memory_capability_status"]["capability_outcome"],
                "unblocked_all_required",
            )
            self.assertNotIn("reviewed_memory_transition_record", aggregate_with_store)

            mismatched_proof_record_entry = dict(proof_record_entry)
            mismatched_proof_record_entry["aggregate_identity_ref"] = {
                "candidate_family": "different"
            }
            aggregate_with_mismatched_store = service._build_recurrence_aggregate_candidates(
                messages,
                proof_record_store_entries=[mismatched_proof_record_entry],
            )[0]
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
                    aggregate_with_mismatched_store,
                    source_context,
                )
            )
            aggregate_with_support_only = dict(aggregate)
            aggregate_with_support_only["review_queue_items"] = [
                {
                    "artifact_id": "artifact-a",
                    "source_message_id": "msg-a",
                    "candidate_id": "candidate-a:v2",
                    "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                }
            ]
            aggregate_with_support_only["candidate_review_record"] = {
                "artifact_id": "artifact-a",
                "source_message_id": "msg-a",
                "candidate_id": "candidate-a:v2",
                "candidate_updated_at": "2026-03-28T00:05:00+00:00",
                "review_action": "accept",
                "review_status": "accepted",
                "recorded_at": "2026-03-28T00:06:00+00:00",
            }
            aggregate_with_support_only["approval_backed_save_support"] = {
                "saved_note_path": "/tmp/note.md"
            }
            aggregate_with_support_only["historical_adjunct"] = {
                "artifact_id": "artifact-a",
                "saved_note_path": "/tmp/note.md",
            }
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_source_refs(
                    aggregate_with_support_only
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_basis(
                    aggregate_with_support_only
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_support_only,
                    source_context,
                )
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_capability_status(
                    aggregate_with_support_only
                ),
                aggregate["reviewed_memory_capability_status"],
            )
            supporting_review_refs = list(aggregate.get("supporting_review_refs") or [])
            aggregate_with_fake_handle = dict(aggregate)
            aggregate_with_fake_handle["reviewed_memory_reversible_effect_handle"] = {
                "handle_version": "first_same_session_reviewed_memory_reversible_effect_handle_v1",
                "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": supporting_review_refs,
                "boundary_source_ref": {
                    "ref_kind": "fake-boundary-source-ref",
                },
                "rollback_contract_ref": {
                    "rollback_version": "first_reviewed_memory_effect_reversal_v1",
                },
                "effect_target_kind": "applied_reviewed_memory_effect",
                "effect_capability": "reversible_local_only",
                "effect_stage": "handle_defined_not_applied",
                "handle_id": "fake-handle",
                "defined_at": "2026-03-28T00:05:00+00:00",
            }
            aggregate_with_fake_target = dict(aggregate)
            aggregate_with_fake_target["reviewed_memory_applied_effect_target"] = {
                "target_version": "first_same_session_reviewed_memory_applied_effect_target_v1",
                "target_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": supporting_review_refs,
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "target_capability_boundary": "local_effect_presence_only",
                "target_stage": "effect_present_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": "2026-03-28T00:05:00+00:00",
            }
            aggregate_with_fake_source = dict(aggregate)
            aggregate_with_fake_source["reviewed_memory_local_effect_presence_record"] = {
                "source_version": "first_same_session_reviewed_memory_local_effect_presence_record_v1",
                "source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": supporting_review_refs,
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "source_capability_boundary": "local_effect_presence_only",
                "source_stage": "presence_recorded_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": "2026-03-28T00:05:00+00:00",
            }
            aggregate_with_fake_event_source = dict(aggregate)
            aggregate_with_fake_event_source["reviewed_memory_local_effect_presence_event_source"] = {
                "event_source_version": "first_same_session_reviewed_memory_local_effect_presence_event_source_v1",
                "event_source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": supporting_review_refs,
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "event_capability_boundary": "local_effect_presence_only",
                "event_stage": "presence_event_recorded_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": "2026-03-28T00:05:00+00:00",
            }
            aggregate_with_fake_producer = dict(aggregate)
            aggregate_with_fake_producer["reviewed_memory_local_effect_presence_event_producer"] = {
                "producer_version": "first_same_session_reviewed_memory_local_effect_presence_event_producer_v1",
                "producer_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": supporting_review_refs,
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "producer_capability_boundary": "local_effect_presence_only",
                "producer_stage": "presence_event_recorded_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": "2026-03-28T00:05:00+00:00",
            }
            aggregate_with_fake_event = dict(aggregate)
            aggregate_with_fake_event["reviewed_memory_local_effect_presence_event"] = {
                "event_version": "first_same_session_reviewed_memory_local_effect_presence_event_v1",
                "event_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": supporting_review_refs,
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "event_capability_boundary": "local_effect_presence_only",
                "event_stage": "presence_observed_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": "2026-03-28T00:05:00+00:00",
            }
            aggregate_with_fake_fact_source = dict(aggregate)
            aggregate_with_fake_fact_source["reviewed_memory_local_effect_presence_fact_source"] = {
                "fact_source_version": "first_same_session_reviewed_memory_local_effect_presence_fact_source_v1",
                "fact_source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": supporting_review_refs,
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "fact_capability_boundary": "local_effect_presence_only",
                "fact_stage": "presence_fact_available_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": "2026-03-28T00:05:00+00:00",
            }
            aggregate_with_fake_proof_boundary = dict(aggregate)
            aggregate_with_fake_proof_boundary["reviewed_memory_local_effect_presence_proof_boundary"] = {
                "proof_boundary_version": "first_same_session_reviewed_memory_local_effect_presence_proof_boundary_v1",
                "proof_boundary_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": supporting_review_refs,
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "proof_capability_boundary": "local_effect_presence_only",
                "proof_stage": "first_presence_proved_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": "2026-03-28T00:05:00+00:00",
            }
            aggregate_with_fake_fact_source_instance = dict(aggregate)
            aggregate_with_fake_fact_source_instance["reviewed_memory_local_effect_presence_fact_source_instance"] = {
                "fact_source_instance_version": (
                    "first_same_session_reviewed_memory_local_effect_presence_fact_source_instance_v1"
                ),
                "fact_source_instance_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": supporting_review_refs,
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "fact_capability_boundary": "local_effect_presence_only",
                "fact_stage": "presence_fact_available_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": "2026-03-28T00:05:00+00:00",
            }
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                    aggregate_with_fake_proof_boundary,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate_with_fake_proof_boundary,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate_with_fake_fact_source_instance,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate_with_fake_fact_source_instance,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate_with_fake_fact_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
                    aggregate_with_fake_event,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                    aggregate_with_fake_event,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_with_fake_event,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_with_fake_event,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_fake_event,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_fake_event,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_fake_event,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                    aggregate_with_fake_producer,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_with_fake_producer,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_with_fake_producer,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_fake_producer,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_fake_producer,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_fake_producer,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_with_fake_event_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_with_fake_event_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_fake_event_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_fake_event_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_fake_event_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
                    aggregate_with_fake_fact_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                    aggregate_with_fake_fact_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_with_fake_fact_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_with_fake_fact_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_fake_fact_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_fake_fact_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_fake_fact_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_with_fake_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_fake_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_fake_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_fake_source,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_fake_target,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_fake_target,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_fake_target,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_fake_handle,
                    source_context,
                )
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate_with_fake_handle,
                    source_context,
                )
            )
            aggregate_with_fake_source_refs = dict(aggregate)
            aggregate_with_fake_source_refs["reviewed_memory_capability_source_refs"] = {
                "source_version": "same_session_reviewed_memory_capability_source_refs_v1",
                "source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "required_preconditions": list(
                    aggregate["reviewed_memory_unblock_contract"]["required_preconditions"]
                ),
                "capability_source_refs": {
                    "boundary_source_ref": {"ref_kind": "fake"},
                    "rollback_source_ref": {"ref_kind": "fake"},
                    "disable_source_ref": {"ref_kind": "fake"},
                    "conflict_source_ref": {"ref_kind": "fake"},
                    "transition_audit_source_ref": {"ref_kind": "fake"},
                },
                "source_status": "all_required_sources_present",
                "evaluated_at": "2026-03-28T00:05:00+00:00",
            }
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_source_refs(
                    aggregate_with_fake_source_refs
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_basis(
                    aggregate_with_fake_source_refs
                )
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_capability_status(
                    aggregate_with_fake_source_refs
                ),
                aggregate["reviewed_memory_capability_status"],
            )
            aggregate_with_fake_basis = dict(aggregate)
            aggregate_with_fake_basis["reviewed_memory_capability_basis"] = {
                "basis_version": "same_session_reviewed_memory_capability_basis_v1",
                "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "required_preconditions": list(
                    aggregate["reviewed_memory_unblock_contract"]["required_preconditions"]
                ),
                "basis_status": "all_required_capabilities_present",
                "satisfaction_basis_boundary": "canonical_reviewed_memory_layer_capabilities_only",
                "evaluated_at": "2026-03-28T00:05:00+00:00",
            }
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_status(
                    aggregate_with_fake_basis
                )
            )
            self.assertNotIn("future_transition_target", aggregate["reviewed_memory_precondition_status"])
            self.assertNotIn("readiness_target", aggregate["reviewed_memory_unblock_contract"])
            self.assertNotIn("readiness_target", aggregate["reviewed_memory_capability_status"])
            aggregate_without_marker = dict(aggregate)
            aggregate_without_marker.pop("aggregate_promotion_marker", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_precondition_status(aggregate_without_marker)
            )
            aggregate_without_status = dict(aggregate)
            aggregate_without_status.pop("reviewed_memory_precondition_status", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_boundary_draft(aggregate_without_status)
            )
            aggregate_without_boundary_draft = dict(aggregate)
            aggregate_without_boundary_draft.pop("reviewed_memory_boundary_draft", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_rollback_contract(
                    aggregate_without_boundary_draft
                )
            )
            aggregate_without_rollback_contract = dict(aggregate)
            aggregate_without_rollback_contract.pop("reviewed_memory_rollback_contract", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_disable_contract(
                    aggregate_without_rollback_contract
                )
            )
            aggregate_without_disable_contract = dict(aggregate)
            aggregate_without_disable_contract.pop("reviewed_memory_disable_contract", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_conflict_contract(
                    aggregate_without_disable_contract
                )
            )
            aggregate_without_conflict_contract = dict(aggregate)
            aggregate_without_conflict_contract.pop("reviewed_memory_conflict_contract", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_transition_audit_contract(
                    aggregate_without_conflict_contract
                )
            )
            aggregate_without_transition_audit_contract = dict(aggregate)
            aggregate_without_transition_audit_contract.pop("reviewed_memory_transition_audit_contract", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_unblock_contract(
                    aggregate_without_transition_audit_contract
                )
            )
            aggregate_without_unblock_contract = dict(aggregate)
            aggregate_without_unblock_contract.pop("reviewed_memory_unblock_contract", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_status(
                    aggregate_without_unblock_contract
                )
            )
            aggregate_without_capability_status = dict(aggregate)
            aggregate_without_capability_status.pop("reviewed_memory_capability_status", None)
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_planning_target_ref(
                    aggregate_without_capability_status
                )
            )
            self.assertEqual(
                aggregate["supporting_source_message_refs"],
                [
                    {"artifact_id": "artifact-proof-b", "source_message_id": "msg-proof-b"},
                    {"artifact_id": "artifact-proof-a", "source_message_id": "msg-proof-a"},
                ],
            )
            self.assertEqual(
                aggregate["supporting_candidate_refs"],
                [
                    {
                        "artifact_id": "artifact-proof-b",
                        "source_message_id": "msg-proof-b",
                        "candidate_id": "candidate-proof-b:v1",
                        "candidate_updated_at": "2026-03-28T00:03:00+00:00",
                    },
                    {
                        "artifact_id": "artifact-proof-a",
                        "source_message_id": "msg-proof-a",
                        "candidate_id": "candidate-proof-a:v1",
                        "candidate_updated_at": "2026-03-28T00:01:00+00:00",
                    },
                ],
            )
            self.assertNotIn("supporting_review_refs", aggregate)

    def test_candidate_confirmation_record_stays_source_message_anchored_and_clears_on_superseding_correction(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            store = SessionStore(base_dir=str(tmp_path / "sessions"))

            store.append_message("candidate-confirmation-store", {"role": "user", "text": "질문"})
            source_message = store.append_message(
                "candidate-confirmation-store",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-candidate-confirmation",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": [str(source_path)],
                    "evidence": [
                        {
                            "source_path": str(source_path),
                            "source_name": "source.md",
                            "label": "본문 근거",
                            "snippet": "hello world",
                        }
                    ],
                },
            )

            corrected = store.record_correction_for_message(
                "candidate-confirmation-store",
                message_id=source_message["message_id"],
                corrected_text="수정본 A입니다.\n핵심만 남겼습니다.",
            )
            self.assertIsNotNone(corrected)
            candidate_updated_at = corrected["corrected_outcome"]["recorded_at"]

            confirmed = store.record_candidate_confirmation_for_message(
                "candidate-confirmation-store",
                message_id=source_message["message_id"],
                candidate_confirmation_record={
                    "candidate_id": (
                        "session-local-candidate:artifact-candidate-confirmation:"
                        f"{source_message['message_id']}:correction_rewrite_preference"
                    ),
                    "candidate_family": "correction_rewrite_preference",
                    "candidate_updated_at": candidate_updated_at,
                    "artifact_id": "artifact-candidate-confirmation",
                    "source_message_id": source_message["message_id"],
                    "confirmation_scope": "candidate_reuse",
                    "confirmation_label": "explicit_reuse_confirmation",
                },
            )
            self.assertIsNotNone(confirmed)
            self.assertEqual(
                confirmed["candidate_confirmation_record"]["candidate_id"],
                (
                    "session-local-candidate:artifact-candidate-confirmation:"
                    f"{source_message['message_id']}:correction_rewrite_preference"
                ),
            )
            self.assertEqual(
                confirmed["candidate_confirmation_record"]["candidate_updated_at"],
                candidate_updated_at,
            )
            self.assertEqual(
                confirmed["candidate_confirmation_record"]["source_message_id"],
                source_message["message_id"],
            )

            corrected_again = store.record_correction_for_message(
                "candidate-confirmation-store",
                message_id=source_message["message_id"],
                corrected_text="수정본 B입니다.\n다시 손봤습니다.",
            )
            self.assertIsNotNone(corrected_again)
            self.assertNotIn("candidate_confirmation_record", corrected_again)

    def test_candidate_review_record_stays_source_message_anchored_and_clears_on_superseding_correction(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            store = SessionStore(base_dir=str(tmp_path / "sessions"))

            store.append_message("candidate-review-store", {"role": "user", "text": "질문"})
            source_message = store.append_message(
                "candidate-review-store",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-candidate-review",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": [str(source_path)],
                    "evidence": [
                        {
                            "source_path": str(source_path),
                            "source_name": "source.md",
                            "label": "본문 근거",
                            "snippet": "hello world",
                        }
                    ],
                },
            )

            corrected = store.record_correction_for_message(
                "candidate-review-store",
                message_id=source_message["message_id"],
                corrected_text="수정본 A입니다.\n핵심만 남겼습니다.",
            )
            self.assertIsNotNone(corrected)
            candidate_updated_at = corrected["corrected_outcome"]["recorded_at"]

            confirmed = store.record_candidate_confirmation_for_message(
                "candidate-review-store",
                message_id=source_message["message_id"],
                candidate_confirmation_record={
                    "candidate_id": (
                        "session-local-candidate:artifact-candidate-review:"
                        f"{source_message['message_id']}:correction_rewrite_preference"
                    ),
                    "candidate_family": "correction_rewrite_preference",
                    "candidate_updated_at": candidate_updated_at,
                    "artifact_id": "artifact-candidate-review",
                    "source_message_id": source_message["message_id"],
                    "confirmation_scope": "candidate_reuse",
                    "confirmation_label": "explicit_reuse_confirmation",
                },
            )
            self.assertIsNotNone(confirmed)

            reviewed = store.record_candidate_review_for_message(
                "candidate-review-store",
                message_id=source_message["message_id"],
                candidate_review_record={
                    "candidate_id": (
                        "session-local-candidate:artifact-candidate-review:"
                        f"{source_message['message_id']}:correction_rewrite_preference"
                    ),
                    "candidate_updated_at": candidate_updated_at,
                    "artifact_id": "artifact-candidate-review",
                    "source_message_id": source_message["message_id"],
                    "review_scope": "source_message_candidate_review",
                    "review_action": "accept",
                    "review_status": "accepted",
                },
            )
            self.assertIsNotNone(reviewed)
            self.assertEqual(
                reviewed["candidate_review_record"]["candidate_id"],
                (
                    "session-local-candidate:artifact-candidate-review:"
                    f"{source_message['message_id']}:correction_rewrite_preference"
                ),
            )
            self.assertEqual(
                reviewed["candidate_review_record"]["candidate_updated_at"],
                candidate_updated_at,
            )
            self.assertEqual(
                reviewed["candidate_review_record"]["source_message_id"],
                source_message["message_id"],
            )

            corrected_again = store.record_correction_for_message(
                "candidate-review-store",
                message_id=source_message["message_id"],
                corrected_text="수정본 B입니다.\n다시 손봤습니다.",
            )
            self.assertIsNotNone(corrected_again)
            self.assertNotIn("candidate_confirmation_record", corrected_again)
            self.assertNotIn("candidate_review_record", corrected_again)

    def test_corrected_save_bridge_uses_recorded_snapshot_and_preserves_corrected_outcome(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "source-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            initial = loop.handle(
                UserRequest(
                    user_text=f"Summarize {source_path}",
                    session_id="corrected-save-session",
                    metadata={"source_path": str(source_path)},
                )
            )
            artifact_id = initial.artifact_id
            source_message_id = initial.source_message_id
            self.assertIsNotNone(source_message_id)

            updated_source = loop.session_store.record_correction_for_message(
                "corrected-save-session",
                message_id=source_message_id or "",
                corrected_text="수정본 A입니다.\n핵심만 남겼습니다.",
            )
            self.assertIsNotNone(updated_source)

            bridge = loop.handle(
                UserRequest(
                    user_text="",
                    session_id="corrected-save-session",
                    metadata={"corrected_save_message_id": source_message_id},
                )
            )

            self.assertEqual(bridge.status, "needs_approval")
            self.assertTrue(bridge.requires_approval)
            self.assertEqual(bridge.artifact_id, artifact_id)
            self.assertEqual(bridge.source_message_id, source_message_id)
            self.assertEqual(bridge.save_content_source, "corrected_text")
            self.assertIn("현재 기록된 수정본 스냅샷", bridge.text)
            self.assertIn("요청 시점 그대로 고정", bridge.text)
            self.assertIsNotNone(bridge.approval)
            self.assertEqual(bridge.approval["artifact_id"], artifact_id)
            self.assertEqual(bridge.approval["source_message_id"], source_message_id)
            self.assertEqual(bridge.approval["save_content_source"], "corrected_text")
            self.assertEqual(bridge.approval["requested_path"], str(note_path))
            self.assertIn("수정본 A입니다.", bridge.approval["preview_markdown"])

            approval_id = bridge.approval["approval_id"]
            pending_before = loop.session_store.get_pending_approval("corrected-save-session", approval_id)
            self.assertIsNotNone(pending_before)
            self.assertEqual(pending_before["note_text"], "수정본 A입니다.\n핵심만 남겼습니다.")

            updated_again = loop.session_store.record_correction_for_message(
                "corrected-save-session",
                message_id=source_message_id or "",
                corrected_text="수정본 B입니다.\n다시 손봤습니다.",
            )
            self.assertIsNotNone(updated_again)

            pending_after = loop.session_store.get_pending_approval("corrected-save-session", approval_id)
            self.assertIsNotNone(pending_after)
            self.assertEqual(pending_after["note_text"], "수정본 A입니다.\n핵심만 남겼습니다.")
            self.assertIn("수정본 A입니다.", pending_after["preview_markdown"])

            approved = loop.handle(
                UserRequest(
                    user_text="",
                    session_id="corrected-save-session",
                    approved_approval_id=approval_id,
                )
            )

            self.assertEqual(approved.status, "saved")
            self.assertEqual(approved.artifact_id, artifact_id)
            self.assertEqual(approved.source_message_id, source_message_id)
            self.assertEqual(approved.save_content_source, "corrected_text")
            self.assertEqual(approved.saved_note_path, str(note_path))
            self.assertIn("승인 시점에 고정된 수정본", approved.text)
            self.assertIn("다시 저장 요청", approved.text)
            self.assertTrue(note_path.exists())
            self.assertEqual(note_path.read_text(encoding="utf-8"), "수정본 A입니다.\n핵심만 남겼습니다.")

            session = loop.session_store.get_session("corrected-save-session")
            source_messages = [
                message
                for message in session["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ]
            self.assertTrue(source_messages)
            source_message = source_messages[-1]
            self.assertEqual(source_message["corrected_text"], "수정본 B입니다.\n다시 손봤습니다.")
            self.assertEqual(source_message["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(source_message["corrected_outcome"]["artifact_id"], artifact_id)
            self.assertEqual(source_message["corrected_outcome"]["approval_id"], approval_id)
            self.assertEqual(source_message["corrected_outcome"]["saved_note_path"], str(note_path))
            self.assertEqual(source_message["corrected_outcome"]["source_message_id"], source_message_id)

            saved_messages = [
                message
                for message in session["messages"]
                if message.get("saved_note_path") == str(note_path)
            ]
            self.assertTrue(saved_messages)
            self.assertEqual(saved_messages[-1]["artifact_id"], artifact_id)
            self.assertEqual(saved_messages[-1]["source_message_id"], source_message_id)
            self.assertEqual(saved_messages[-1]["save_content_source"], "corrected_text")

            log_records = [
                json.loads(line)
                for line in (tmp_path / "task_log.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            approval_requested = next(
                record
                for record in log_records
                if record["action"] == "approval_requested" and record["detail"].get("approval_id") == approval_id
            )
            approval_granted = next(
                record
                for record in log_records
                if record["action"] == "approval_granted" and record["detail"].get("approval_id") == approval_id
            )
            write_note = next(
                record
                for record in log_records
                if record["action"] == "write_note" and record["detail"].get("approval_id") == approval_id
            )
            corrected_outcome_recorded = next(
                record
                for record in log_records
                if record["action"] == "corrected_outcome_recorded" and record["detail"].get("approval_id") == approval_id
            )
            self.assertEqual(approval_requested["detail"]["artifact_id"], artifact_id)
            self.assertEqual(approval_requested["detail"]["source_message_id"], source_message_id)
            self.assertEqual(approval_requested["detail"]["save_content_source"], "corrected_text")
            self.assertEqual(approval_granted["detail"]["artifact_id"], artifact_id)
            self.assertEqual(approval_granted["detail"]["source_message_id"], source_message_id)
            self.assertEqual(approval_granted["detail"]["save_content_source"], "corrected_text")
            self.assertEqual(write_note["detail"]["artifact_id"], artifact_id)
            self.assertEqual(write_note["detail"]["source_message_id"], source_message_id)
            self.assertEqual(write_note["detail"]["save_content_source"], "corrected_text")
            self.assertEqual(corrected_outcome_recorded["detail"]["outcome"], "corrected")
            self.assertEqual(corrected_outcome_recorded["detail"]["artifact_id"], artifact_id)
            self.assertEqual(corrected_outcome_recorded["detail"]["approval_id"], approval_id)
            self.assertEqual(corrected_outcome_recorded["detail"]["saved_note_path"], str(note_path))

    def test_scanned_pdf_returns_helpful_ocr_message(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "scan.pdf"
            source_path.write_bytes(b"%PDF-1.4\n%stub pdf bytes\n")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            with patch(
                "tools.file_reader.importlib.import_module",
                return_value=SimpleNamespace(PdfReader=_FakeEmptyPdfReader),
            ):
                response = loop.handle(
                    UserRequest(
                        user_text=f"Summarize {source_path}",
                        session_id="session-2c",
                        approved=False,
                        metadata={
                            "source_path": str(source_path),
                        },
                    )
                )

            self.assertIn("요약할 수 없습니다", response.text)
            self.assertIn("OCR", response.text)
            self.assertIn("이미지형 PDF", response.text)
            self.assertIn("다음 단계:", response.text)
            self.assertEqual(response.actions_taken, ["ocr_not_supported"])

    def test_search_only_reports_skipped_scanned_pdfs(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "scan.pdf").write_bytes(b"%PDF-1.4\n%stub pdf bytes\n")
            (docs_dir / "notes.txt").write_text("hello world", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            with patch(
                "tools.file_reader.importlib.import_module",
                return_value=SimpleNamespace(PdfReader=_FakeEmptyPdfReader),
            ):
                response = loop.handle(
                    UserRequest(
                        user_text="Search docs for budget",
                        session_id="session-2d",
                        metadata={
                            "search_root": str(docs_dir),
                            "search_query": "budget",
                            "search_only": True,
                        },
                    )
                )

            self.assertIn("검색 결과를 찾지 못했습니다", response.text)
            self.assertIn("스캔본 또는 이미지형 PDF 1개를 건너뛰었습니다", response.text)

    def test_search_summary_save_with_approval_writes_note(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "budget-plan.md").write_text(
                "# Budget Plan\n\nlocal budget summary and plan",
                encoding="utf-8",
            )
            (docs_dir / "meeting-notes.md").write_text(
                "# Notes\n\nbudget discussion details",
                encoding="utf-8",
            )

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="Search docs for budget and summarize the results",
                    session_id="session-3",
                    approved=True,
                    metadata={
                        "search_root": str(docs_dir),
                        "search_query": "budget",
                        "search_result_limit": 2,
                        "save_summary": True,
                    },
                )
            )

            self.assertFalse(response.requires_approval)
            self.assertIsNotNone(response.saved_note_path)
            self.assertEqual(response.artifact_kind, "grounded_brief")
            self.assertEqual(response.source_message_id, response.corrected_outcome["source_message_id"])
            self.assertEqual(response.save_content_source, "original_draft")
            self.assertIsNotNone(response.corrected_outcome)
            self.assertEqual(response.corrected_outcome["outcome"], "accepted_as_is")
            self.assertEqual(response.corrected_outcome["artifact_id"], response.artifact_id)
            self.assertEqual(response.corrected_outcome["saved_note_path"], response.saved_note_path)
            saved_path = Path(response.saved_note_path or "")
            self.assertTrue(saved_path.exists())
            note_text = saved_path.read_text(encoding="utf-8")
            self.assertIn("# 'budget' 검색 요약", note_text)
            self.assertIn("budget-plan.md", note_text)
            self.assertIn("meeting-notes.md", note_text)
            session = loop.session_store.get_session("session-3")
            self.assertEqual(session["messages"][-1]["artifact_id"], response.artifact_id)
            self.assertEqual(session["messages"][-1]["source_message_id"], response.source_message_id)
            self.assertEqual(session["messages"][-1]["save_content_source"], "original_draft")
            self.assertEqual(
                session["messages"][-1]["corrected_outcome"]["source_message_id"],
                session["messages"][-1]["message_id"],
            )
            log_records = [
                json.loads(line)
                for line in (tmp_path / "task_log.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            write_note = next(record for record in log_records if record["action"] == "write_note")
            corrected_outcome_recorded = next(record for record in log_records if record["action"] == "corrected_outcome_recorded")
            self.assertEqual(write_note["detail"]["source_message_id"], response.source_message_id)
            self.assertEqual(write_note["detail"]["save_content_source"], "original_draft")
            self.assertEqual(corrected_outcome_recorded["detail"]["artifact_id"], response.artifact_id)
            self.assertIsNone(corrected_outcome_recorded["detail"]["approval_id"])

    def test_session_store_backfills_save_content_source_for_legacy_pending_save_approval(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            session_path = tmp_path / "sessions" / "legacy-save-content-source.json"
            session_path.parent.mkdir(parents=True, exist_ok=True)
            session_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "session_id": "legacy-save-content-source",
                        "title": "legacy-save-content-source",
                        "messages": [
                            {
                                "message_id": "msg-source-legacy",
                                "role": "assistant",
                                "text": "legacy grounded brief",
                                "artifact_id": "artifact-legacy",
                                "artifact_kind": "grounded_brief",
                                "original_response_snapshot": {
                                    "artifact_id": "artifact-legacy",
                                    "artifact_kind": "grounded_brief",
                                    "draft_text": "legacy grounded brief",
                                    "source_paths": [str(tmp_path / "source.md")],
                                    "response_origin": None,
                                    "summary_chunks_snapshot": [],
                                    "evidence_snapshot": [],
                                },
                            }
                        ],
                        "pending_approvals": [
                            {
                                "approval_id": "approval-legacy",
                                "artifact_id": "artifact-legacy",
                                "kind": "save_note",
                                "requested_path": str(tmp_path / "notes" / "legacy.md"),
                                "overwrite": False,
                                "preview_markdown": "# legacy",
                                "source_paths": [str(tmp_path / "source.md")],
                                "created_at": "2026-03-27T00:00:00+00:00",
                                "note_text": "# legacy",
                            }
                        ],
                        "permissions": {"web_search": "disabled"},
                        "active_context": None,
                        "created_at": "2026-03-27T00:00:00+00:00",
                        "updated_at": "2026-03-27T00:00:00+00:00",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            store = SessionStore(base_dir=str(tmp_path / "sessions"))

            session = store.get_session("legacy-save-content-source")

            self.assertEqual(session["pending_approvals"][0]["save_content_source"], "original_draft")
            self.assertEqual(session["pending_approvals"][0]["source_message_id"], "msg-source-legacy")

    def test_search_only_lists_numbered_results(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "budget-plan.md").write_text("budget details", encoding="utf-8")
            (docs_dir / "notes.md").write_text("local budget notes", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="Search docs for budget",
                    session_id="session-4",
                    metadata={
                        "search_root": str(docs_dir),
                        "search_query": "budget",
                        "search_only": True,
                    },
                )
            )

            self.assertIn("검색 결과:", response.text)
            self.assertIn("1.", response.text)
            self.assertIn("발췌:", response.text)
            self.assertFalse(response.requires_approval)

    def test_search_selection_uses_only_selected_sources(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "budget-plan.md").write_text("budget plan details", encoding="utf-8")
            (docs_dir / "meeting-notes.md").write_text("budget meeting notes", encoding="utf-8")
            (docs_dir / "other.md").write_text("something else", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="Search docs for budget and save the summary",
                    session_id="session-5",
                    approved=True,
                    metadata={
                        "search_root": str(docs_dir),
                        "search_query": "budget",
                        "search_selected_indices": [2],
                        "save_summary": True,
                    },
                )
            )

            self.assertEqual(len(response.selected_source_paths), 1)
            self.assertIn("meeting-notes.md", response.selected_source_paths[0])
            saved_path = Path(response.saved_note_path or "")
            self.assertTrue(saved_path.exists())
            note_text = saved_path.read_text(encoding="utf-8")
            self.assertIn("meeting-notes.md", note_text)
            self.assertNotIn("budget-plan.md", note_text)

    def test_search_selection_by_path_uses_unique_suffix(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "budget-plan.md").write_text("budget plan details", encoding="utf-8")
            (docs_dir / "meeting-notes.md").write_text("budget meeting notes", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="Search docs for budget and save the summary",
                    session_id="session-6",
                    approved=True,
                    metadata={
                        "search_root": str(docs_dir),
                        "search_query": "budget",
                        "search_selected_paths": ["meeting-notes.md"],
                        "save_summary": True,
                    },
                )
            )

            self.assertEqual(len(response.selected_source_paths), 1)
            self.assertIn("meeting-notes.md", response.selected_source_paths[0])
            saved_path = Path(response.saved_note_path or "")
            self.assertTrue(saved_path.exists())
            note_text = saved_path.read_text(encoding="utf-8")
            self.assertIn("meeting-notes.md", note_text)
            self.assertNotIn("budget-plan.md", note_text)

    def test_search_save_without_approval_returns_note_preview(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "budget-plan.md").write_text("budget plan details", encoding="utf-8")
            (docs_dir / "meeting-notes.md").write_text("budget meeting notes", encoding="utf-8")

            loop = AgentLoop(
                model=MockModelAdapter(),
                session_store=SessionStore(base_dir=str(tmp_path / "sessions")),
                task_logger=TaskLogger(path=str(tmp_path / "task_log.jsonl")),
                tools={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(),
                    "write_note": WriteNoteTool(),
                },
                notes_dir=str(tmp_path / "notes"),
            )

            response = loop.handle(
                UserRequest(
                    user_text="Search docs for budget and save the summary",
                    session_id="session-7",
                    approved=False,
                    metadata={
                        "search_root": str(docs_dir),
                        "search_query": "budget",
                        "search_selected_paths": ["budget-plan.md"],
                        "save_summary": True,
                    },
                )
            )

            self.assertTrue(response.requires_approval)
            self.assertIsNotNone(response.note_preview)
            self.assertIn("# 'budget' 검색 요약", response.note_preview or "")
            self.assertIn("budget-plan.md", response.note_preview or "")


if __name__ == "__main__":
    unittest.main()
