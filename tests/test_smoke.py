import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from core.agent_loop import AgentLoop, UserRequest
from model_adapter.mock import MockModelAdapter
from storage.session_store import SessionStore
from storage.task_log import TaskLogger
from storage.web_search_store import WebSearchStore
from tools.file_reader import FileReaderTool
from tools.file_search import FileSearchTool
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
            self.assertIn("웹 검색 요약: 오늘 날씨", response.text)

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
            self.assertIn("웹 검색 요약: 아이유 최신 소식", response.text)

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
            self.assertIn("[원문] 체인소맨 애니메이션 소개", response.text)
            self.assertIn("[원문] 체인소 맨 - 위키백과", response.text)
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
            self.assertIn("한 줄 정의:", response.text)
            self.assertIn("사실 카드:", response.text)
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
            self.assertIn("메이플스토리는 넥슨이 서비스하거나 배급하는 액션 RPG 게임입니다.", response.text)
            self.assertIn("이용 형태는 온라인입니다.", response.text)
            self.assertIn("근거 출처:", response.text)
            self.assertIn("사실 카드:", response.text)
            self.assertIn("서비스/배급: 넥슨", response.text)
            self.assertIn("이용 형태: 온라인", response.text)
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
                    for call in ["붉은사막 플랫폼", "붉은사막 서비스", "붉은사막 운영사", "붉은사막 개발사"]
                )
            )
            self.assertGreater(len(search_tool.search_calls), 4)

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
            self.assertGreater(len(response.follow_up_suggestions), 0)
            self.assertIsNotNone(response.active_context)
            self.assertIsNotNone(response.proposed_note_path)
            self.assertIsNotNone(response.note_preview)
            self.assertGreaterEqual(len(response.evidence), 1)
            self.assertIn("# source.md 요약", response.note_preview or "")
            session = loop.session_store.get_session("session-1")
            self.assertEqual(len(session["pending_approvals"]), 1)
            self.assertEqual(session["active_context"]["label"], "source.md")
            self.assertFalse(Path(response.proposed_note_path or "").exists())

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
            self.assertTrue(note_path.exists())
            self.assertEqual(third.status, "error")
            self.assertIn("찾지 못했습니다", third.text)

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
            self.assertEqual(second.proposed_note_path, str(second_note_path))
            self.assertNotEqual(second.approval["approval_id"], first_approval_id)
            self.assertIn("새 경로로 저장하려면 다시 승인해 주세요.", second.text)
            session = loop.session_store.get_session("session-reissue")
            self.assertEqual(len(session["pending_approvals"]), 1)
            self.assertEqual(session["pending_approvals"][0]["requested_path"], str(second_note_path))

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
            saved_path = Path(response.saved_note_path or "")
            self.assertTrue(saved_path.exists())
            self.assertIn("# source.md 요약", saved_path.read_text(encoding="utf-8"))

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
            saved_path = Path(response.saved_note_path or "")
            self.assertTrue(saved_path.exists())
            note_text = saved_path.read_text(encoding="utf-8")
            self.assertIn("# 'budget' 검색 요약", note_text)
            self.assertIn("budget-plan.md", note_text)
            self.assertIn("meeting-notes.md", note_text)

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
