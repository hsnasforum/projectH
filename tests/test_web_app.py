import unittest
import base64
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from types import SimpleNamespace
from unittest.mock import patch

from app.web import LocalAssistantHandler, WebAppService, WebApiError
from config.settings import AppSettings
from model_adapter.base import ModelAdapter, ModelRuntimeStatus, ModelStreamEvent, SummaryNoteDraft
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


class _BrokenPipeWriter:
    def write(self, _: bytes) -> None:
        raise BrokenPipeError("client disconnected")


class _SlowStreamingModel(ModelAdapter):
    def respond(self, prompt: str) -> str:
        return f"응답: {prompt}"

    def summarize(self, text: str) -> str:
        return f"요약: {text[:20]}"

    def create_summary_note(self, *, source_path: str, text: str) -> SummaryNoteDraft:
        return SummaryNoteDraft(
            title=f"{Path(source_path).name} 요약",
            summary=self.summarize(text),
            note_body=f"# {Path(source_path).name}\n\n{text[:40]}",
        )

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
        return f"{context_label}: {user_request}"

    def health_check(self) -> ModelRuntimeStatus:
        return ModelRuntimeStatus(
            provider="mock",
            configured_model="slow-stream",
            reachable=True,
            configured_model_available=True,
            detail="느린 스트리밍 테스트 모델입니다.",
        )

    def stream_summarize(self, text: str):
        for chunk in ("첫 번째 조각 ", "두 번째 조각 ", "세 번째 조각"):
            time.sleep(0.02)
            yield ModelStreamEvent(kind="text_delta", text=chunk)


class _NoPreflightModel(_SlowStreamingModel):
    def health_check(self) -> ModelRuntimeStatus:
        raise AssertionError("explicit web search should not preflight the model")


class _FakeWebSearchTool:
    def __init__(self, results, pages=None):
        self._results = list(results)
        self._pages = dict(pages or {})

    def search(self, *, query: str, max_results: int = 5):
        return self._results[:max_results]

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


class WebAppServiceTest(unittest.TestCase):
    def test_render_index_replaces_runtime_defaults(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            settings = AppSettings(
                app_name="demo-shell",
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=str(Path(tmp_dir) / "notes"),
                model_provider="mock",
                ollama_model="",
            )
            service = WebAppService(settings=settings)

            html = service.render_index()

            self.assertIn("demo-shell", html)
            self.assertIn("요청 실행", html)
            self.assertIn("선택형 로컬 모델", html)
            self.assertIn("response-origin-badge", html)
            self.assertIn("progress-box", html)
            self.assertIn("cancel-request", html)
            self.assertIn("evidence-box", html)
            self.assertIn("summary-chunks-box", html)
            self.assertIn("evidence-scroll-region", html)
            self.assertIn("summary-chunks-scroll-region", html)
            self.assertIn("approval-path-input", html)
            self.assertIn("reissue-button", html)
            self.assertIn("response-copy-path", html)
            self.assertIn("advanced-settings", html)
            self.assertIn("session-id", html)
            self.assertIn("browser-file-input", html)
            self.assertIn("pick-file-button", html)
            self.assertIn("browser-folder-input", html)
            self.assertIn("pick-folder-button", html)
            self.assertIn("response-feedback-box", html)
            self.assertIn("response-feedback-retry", html)
            self.assertIn("meta-web-search", html)
            self.assertIn("web-search-permission", html)
            self.assertIn("읽기 전용으로 연결되어 있고", html)
            self.assertIn("search-history-box", html)
            self.assertIn("history-item-detail", html)
            self.assertIn("응답 생성 중", html)
            self.assertNotIn("__APP_NAME__", html)

    def test_get_session_payload_returns_empty_session(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            settings = AppSettings(
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=str(Path(tmp_dir) / "notes"),
                web_search_history_dir=str(Path(tmp_dir) / "web-search"),
            )
            service = WebAppService(settings=settings)

            payload = service.get_session_payload("demo-session")

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["session"]["session_id"], "demo-session")
            self.assertEqual(payload["session"]["messages"], [])
            self.assertEqual(payload["session"]["pending_approvals"], [])
            self.assertEqual(payload["session"]["permissions"]["web_search"], "disabled")
            self.assertEqual(payload["session"]["web_search_history"], [])
            self.assertEqual(payload["session"]["schema_version"], "1.0")

    def test_list_sessions_payload_returns_summaries(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(base / "sessions"),
                task_log_path=str(base / "task_log.jsonl"),
                notes_dir=str(base / "notes"),
            )
            service = WebAppService(settings=settings)

            service.session_store.append_message("session-a", {"role": "user", "text": "첫 번째 메시지"})
            service.session_store.append_message("session-b", {"role": "user", "text": "두 번째 메시지"})

            payload = service.list_sessions_payload()

            self.assertTrue(payload["ok"])
            self.assertEqual(len(payload["sessions"]), 2)
            self.assertIn("session_id", payload["sessions"][0])
            self.assertIn("pending_approval_count", payload["sessions"][0])

    def test_submit_feedback_updates_assistant_message_and_logs(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(base / "sessions"),
                task_log_path=str(base / "task_log.jsonl"),
                notes_dir=str(base / "notes"),
                web_search_history_dir=str(base / "web-search"),
            )
            service = WebAppService(settings=settings)

            service.session_store.append_message("feedback-session", {"role": "user", "text": "질문"})
            service.session_store.append_message(
                "feedback-session",
                {"role": "assistant", "text": "답변", "status": "answer"},
            )
            assistant_message = service.session_store.get_session("feedback-session")["messages"][-1]

            payload = service.submit_feedback(
                {
                    "session_id": "feedback-session",
                    "message_id": assistant_message["message_id"],
                    "feedback_label": "incorrect",
                    "feedback_reason": "factual_error",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["feedback_label"], "incorrect")
            self.assertEqual(payload["feedback_reason"], "factual_error")
            self.assertEqual(payload["session"]["messages"][-1]["feedback"]["label"], "incorrect")
            self.assertEqual(payload["session"]["messages"][-1]["feedback"]["reason"], "factual_error")
            log_text = Path(settings.task_log_path).read_text(encoding="utf-8")
            self.assertIn("response_feedback_recorded", log_text)
            self.assertIn("incorrect", log_text)
            self.assertIn("factual_error", log_text)

    def test_handle_chat_summarize_file_returns_session_and_runtime(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "web-session",
                    "source_path": str(source_path),
                    "save_summary": False,
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "answer")
            self.assertIn("[모의 요약]", payload["response"]["text"])
            self.assertGreater(len(payload["response"]["follow_up_suggestions"]), 0)
            self.assertEqual(payload["response"]["active_context"]["label"], "source.md")
            self.assertEqual(payload["response"]["response_origin"]["provider"], "mock")
            self.assertEqual(payload["response"]["response_origin"]["badge"], "MOCK")
            self.assertIn("모의 데모 응답", payload["response"]["response_origin"]["label"])
            self.assertGreaterEqual(len(payload["response"]["evidence"]), 1)
            self.assertEqual(payload["response"]["evidence"][0]["source_name"], "source.md")
            self.assertEqual(payload["session"]["session_id"], "web-session")
            self.assertGreaterEqual(len(payload["session"]["messages"]), 2)
            self.assertEqual(payload["session"]["messages"][-1]["response_origin"]["provider"], "mock")
            self.assertGreaterEqual(len(payload["session"]["messages"][-1]["evidence"]), 1)
            self.assertEqual(payload["runtime_status"]["provider"], "mock")

    def test_handle_chat_summarize_uploaded_file_returns_summary(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            raw_bytes = "# 업로드 문서\n\nhello world".encode("utf-8")

            payload = service.handle_chat(
                {
                    "session_id": "uploaded-web-session",
                    "provider": "mock",
                    "uploaded_file": {
                        "name": "picked-source.md",
                        "mime_type": "text/markdown",
                        "size_bytes": len(raw_bytes),
                        "content_base64": base64.b64encode(raw_bytes).decode("ascii"),
                    },
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "answer")
            self.assertIn("[모의 요약]", payload["response"]["text"])
            self.assertEqual(payload["response"]["selected_source_paths"], ["picked-source.md"])
            self.assertEqual(payload["response"]["active_context"]["label"], "picked-source.md")
            self.assertEqual(payload["session"]["session_id"], "uploaded-web-session")

    def test_handle_chat_unverified_external_fact_returns_system_guidance(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "limited-general-session",
                    "user_text": "유튜버 레고77이 누구야?",
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "answer")
            self.assertEqual(payload["response"]["actions_taken"], ["respond_with_limitations"])
            self.assertIn("외부 웹 검색이 차단되어 있어", payload["response"]["text"])
            self.assertIn("유튜버 레고77", payload["response"]["text"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "system")
            self.assertEqual(payload["response"]["response_origin"]["badge"], "SYSTEM")

    def test_handle_chat_site_question_returns_system_guidance(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "site-session",
                    "user_text": "naver라는 사이트 알아?",
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "answer")
            self.assertEqual(payload["response"]["actions_taken"], ["respond_with_limitations"])
            self.assertIn("외부 웹 검색이 차단되어 있어", payload["response"]["text"])
            self.assertIn("'naver' 검색", payload["response"]["text"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "system")

    def test_handle_chat_live_info_question_returns_system_guidance(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "weather-session",
                    "user_text": "오늘 날씨 어때요?",
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "answer")
            self.assertEqual(payload["response"]["actions_taken"], ["respond_with_limitations"])
            self.assertIn("웹 검색 권한이 차단되어 있고", payload["response"]["text"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "system")

    def test_handle_chat_live_info_question_uses_web_search_when_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="서울 날씨 - 예보",
                            url="https://example.com/seoul-weather",
                            snippet="서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
                        )
                    ],
                    pages={
                        "https://example.com/seoul-weather": {
                            "title": "서울 날씨 - 예보",
                            "text": "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.\n미세먼지는 보통 수준으로 예상됩니다.",
                            "excerpt": "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
                        }
                    },
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            payload = service.handle_chat(
                {
                    "session_id": "weather-enabled-session",
                    "user_text": "오늘 날씨 어때요?",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIn("웹 검색 요약: 오늘 날씨", payload["response"]["text"])

    def test_handle_chat_external_fact_info_uses_web_search_when_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
                web_search_permission="enabled",
            )
            service = WebAppService(settings=settings)

            with patch.object(
                service,
                "_build_tools",
                return_value={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(reader=FileReaderTool()),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="메이플스토리 - 공식 소개",
                                url="https://example.com/maplestory",
                                snippet="메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.",
                            ),
                        ]
                    ),
                    "write_note": WriteNoteTool(allowed_roots=[str(Path.cwd()), settings.notes_dir]),
                },
            ):
                payload = service.handle_chat(
                    {
                        "session_id": "external-fact-web-service",
                        "user_text": "메이플스토리에 대해 알려줘",
                        "provider": "ollama",
                        "model": "qwen2.5:3b",
                        "web_search_permission": "enabled",
                    }
                )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIn("웹 검색 요약: 메이플스토리", payload["response"]["text"])

    def test_handle_chat_external_fact_retry_prompt_uses_web_search_when_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                web_search_permission="enabled",
            )
            service = WebAppService(settings=settings)
            with patch.object(
                service,
                "_build_tools",
                return_value={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(reader=FileReaderTool()),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="붉은사막 - 나무위키",
                                url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                                snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                            )
                        ]
                    ),
                    "write_note": WriteNoteTool(allowed_roots=[str(Path.cwd()), settings.notes_dir]),
                },
            ):
                payload = service.handle_chat(
                    {
                        "session_id": "retry-external-fact-service",
                        "user_text": (
                            "붉은사막이 무슨게임이야?\n\n"
                            "방금 답변은 틀림 이유는 '사실과 다름'입니다. 같은 세션 문맥과 근거를 기준으로 "
                            "더 정확하고 관련성 높게 다시 답변해 주세요."
                        ),
                        "provider": "mock",
                        "web_search_permission": "enabled",
                        "retry_feedback_label": "incorrect",
                        "retry_feedback_reason": "factual_error",
                    }
                )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIn("웹 검색 요약: 붉은사막", payload["response"]["text"])

    def test_handle_chat_external_fact_who_question_uses_web_search_when_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
                web_search_permission="enabled",
            )
            service = WebAppService(settings=settings)

            with patch.object(
                service,
                "_build_tools",
                return_value={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(reader=FileReaderTool()),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="김창섭 - 소개",
                                url="https://example.com/kim-changseop",
                                snippet="김창섭은 예시 인물 소개 페이지입니다.",
                            ),
                        ]
                    ),
                    "write_note": WriteNoteTool(allowed_roots=[str(Path.cwd()), settings.notes_dir]),
                },
            ):
                payload = service.handle_chat(
                    {
                        "session_id": "external-fact-who-web-service",
                        "user_text": "김창섭이 누구야?",
                        "provider": "ollama",
                        "model": "qwen2.5:3b",
                        "web_search_permission": "enabled",
                    }
                )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIn("웹 검색 요약: 김창섭", payload["response"]["text"])

    def test_handle_chat_external_fact_who_question_with_spaced_question_mark_uses_web_search_when_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
                web_search_permission="enabled",
            )
            service = WebAppService(settings=settings)

            with patch.object(
                service,
                "_build_tools",
                return_value={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(reader=FileReaderTool()),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="김창섭 - 소개",
                                url="https://example.com/kim-changseop",
                                snippet="김창섭은 예시 인물 소개 페이지입니다.",
                            ),
                        ]
                    ),
                    "write_note": WriteNoteTool(allowed_roots=[str(Path.cwd()), settings.notes_dir]),
                },
            ):
                payload = service.handle_chat(
                    {
                        "session_id": "external-fact-who-spaced-web-service",
                        "user_text": "김창섭이 누구야 ?",
                        "provider": "ollama",
                        "model": "qwen2.5:3b",
                        "web_search_permission": "enabled",
                    }
                )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIn("웹 검색 요약: 김창섭", payload["response"]["text"])

    def test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
                web_search_permission="enabled",
            )
            service = WebAppService(settings=settings)

            with patch.object(
                service,
                "_build_tools",
                return_value={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(reader=FileReaderTool()),
                    "search_web": _FakeWebSearchTool(
                        [
                            SimpleNamespace(
                                title="김창섭 - 소개",
                                url="https://example.com/kim-changseop",
                                snippet="김창섭은 예시 인물 소개 페이지입니다.",
                            ),
                        ]
                    ),
                    "write_note": WriteNoteTool(allowed_roots=[str(Path.cwd()), settings.notes_dir]),
                },
            ):
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
                        payload = service.handle_chat(
                            {
                                "session_id": f"external-fact-colloquial-web-service-{index}",
                                "user_text": phrase,
                                "provider": "ollama",
                                "model": "qwen2.5:3b",
                                "web_search_permission": "enabled",
                            }
                        )

                        self.assertTrue(payload["ok"])
                        self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
                        self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
                        self.assertIn("웹 검색 요약: 김창섭", payload["response"]["text"])

    def test_handle_chat_low_confidence_external_fact_question_returns_search_suggestion(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="ollama",
                ollama_model="qwen2.5:3b",
                web_search_permission="enabled",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "suggest-session",
                    "user_text": "김창섭 궁금한데",
                    "provider": "ollama",
                    "model": "qwen2.5:3b",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["suggest_web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "system")
            self.assertIn("자동 웹 검색으로 바로 넘길 확신은 낮습니다", payload["response"]["text"])
            self.assertEqual(payload["response"]["follow_up_suggestions"], ["김창섭 검색해봐"])

    def test_handle_chat_site_question_permission_prompt_uses_cleaned_query(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "site-cleaned-query-session",
                    "user_text": "naver라는 사이트 알아?",
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["respond_with_limitations"])
            self.assertIn("'naver' 검색", payload["response"]["text"])

    def test_handle_chat_latest_info_uses_web_search_even_with_existing_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            service.session_store.set_active_context(
                "latest-info-existing-context",
                {
                    "kind": "document",
                    "label": "기존 문서",
                    "source_paths": [str(tmp_path / "memo.txt")],
                    "summary_hint": "기존 문서 요약",
                    "suggested_prompts": [],
                },
            )
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="아이유 최신 소식 - 결과",
                            url="https://example.com/iu-latest",
                            snippet="아이유의 최근 활동과 최신 소식을 정리한 검색 결과입니다.",
                        )
                    ]
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            payload = service.handle_chat(
                {
                    "session_id": "latest-info-existing-context",
                    "user_text": "아이유 최신 소식 알려줘",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIn("웹 검색 요약: 아이유 최신 소식", payload["response"]["text"])

    def test_handle_chat_persists_web_search_permission_in_session(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "permission-session",
                    "user_text": "유튜버 레고77이 누구야?",
                    "provider": "mock",
                    "web_search_permission": "approval",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["session"]["permissions"]["web_search"], "approval")
            self.assertEqual(payload["session"]["permissions"]["web_search_label"], "승인 필요 · 읽기 전용 검색")
            self.assertIn("승인 후에만 허용하도록 설정해 두었습니다", payload["response"]["text"])
            self.assertIn("웹 검색 승인 카드가 아직 연결되지 않아", payload["response"]["text"])

    def test_handle_chat_enabled_web_search_returns_web_results(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="서울 날씨 - 예보",
                            url="https://example.com/seoul-weather",
                            snippet="서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
                        )
                    ],
                    pages={
                        "https://example.com/seoul-weather": {
                            "title": "서울 날씨 - 예보",
                            "text": "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.\n미세먼지는 보통 수준으로 예상됩니다.",
                            "excerpt": "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
                        }
                    },
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            payload = service.handle_chat(
                {
                    "session_id": "weather-search-session",
                    "user_text": "서울 날씨 검색해봐",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIn("서울 날씨", payload["response"]["text"])
            self.assertIn("원문 확인: 1건", payload["response"]["text"])
            self.assertTrue(payload["response"]["web_search_record_path"])
            self.assertTrue(Path(payload["response"]["web_search_record_path"]).exists())
            self.assertEqual(len(payload["session"]["web_search_history"]), 1)
            self.assertEqual(payload["session"]["web_search_history"][0]["query"], "서울 날씨")
            self.assertEqual(payload["session"]["web_search_history"][0]["page_count"], 1)
            self.assertEqual(len(payload["session"]["web_search_history"][0]["pages_preview"]), 1)
            self.assertEqual(payload["session"]["web_search_history"][0]["pages_preview"][0]["title"], "서울 날씨 - 예보")
            self.assertIn(
                "미세먼지는 보통 수준",
                payload["session"]["web_search_history"][0]["pages_preview"][0]["text_preview"],
            )

    def test_handle_chat_web_search_history_preview_avoids_footer_only_excerpt(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
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
                        }
                    },
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            payload = service.handle_chat(
                {
                    "session_id": "maplestory-preview-session",
                    "user_text": "메이플스토리에 대해 알려줘",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(payload["ok"])
            preview = payload["session"]["web_search_history"][0]["pages_preview"][0]
            self.assertIn("메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임", preview["excerpt"])
            self.assertNotIn("사업자등록번호", preview["excerpt"])
            self.assertNotIn("1588-7701", preview["text_preview"])
            self.assertNotIn("대표이사", preview["text_preview"])

    def test_handle_chat_enabled_web_search_without_space_uses_web_results(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="아이유 - 위키백과",
                            url="https://example.com/iu",
                            snippet="아이유는 대한민국의 가수이자 배우입니다.",
                        )
                    ]
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            payload = service.handle_chat(
                {
                    "session_id": "iu-search-session",
                    "user_text": "아이유검색해",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIn("웹 검색 요약: 아이유", payload["response"]["text"])

    def test_handle_chat_colloquial_web_search_phrases_use_web_results(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="아이유 - 위키백과",
                            url="https://example.com/iu",
                            snippet="아이유는 대한민국의 가수이자 배우입니다.",
                        )
                    ]
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            phrases = [
                "아이유좀검색",
                "아이유 찾아와",
                "아이유 관련해서 좀 볼래",
            ]

            for index, phrase in enumerate(phrases, start=1):
                payload = service.handle_chat(
                    {
                        "session_id": f"iu-colloquial-session-{index}",
                        "user_text": phrase,
                        "provider": "mock",
                        "web_search_permission": "enabled",
                    }
                )

                self.assertTrue(payload["ok"], phrase)
                self.assertEqual(payload["response"]["actions_taken"], ["web_search"], phrase)
                self.assertEqual(payload["response"]["response_origin"]["provider"], "web", phrase)
                self.assertIn("웹 검색 요약: 아이유", payload["response"]["text"], phrase)

    def test_handle_chat_enabled_web_search_skips_ollama_preflight(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="ollama",
                ollama_model="qwen2.5:3b",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="이재용 - 최근 기사",
                            url="https://example.com/lee-jaeyong",
                            snippet="이재용 관련 기사와 프로필을 정리한 검색 결과입니다.",
                        )
                    ]
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            with patch("app.web.build_model_adapter", return_value=_NoPreflightModel()):
                payload = service.handle_chat(
                    {
                        "session_id": "explicit-web-search-with-ollama",
                        "user_text": "이재용 검색해봐",
                        "provider": "ollama",
                        "model": "qwen2.5:3b",
                        "web_search_permission": "enabled",
                    }
                )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIsNone(payload["runtime_status"])

    def test_handle_chat_live_info_web_search_skips_ollama_preflight(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="ollama",
                ollama_model="qwen2.5:3b",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="오늘 날씨 - 예보",
                            url="https://example.com/today-weather",
                            snippet="오늘은 전국이 대체로 맑고 서울은 최고 17도로 예보되었습니다.",
                        )
                    ]
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            with patch("app.web.build_model_adapter", return_value=_NoPreflightModel()):
                payload = service.handle_chat(
                    {
                        "session_id": "live-info-web-search-with-ollama",
                        "user_text": "오늘 날씨 어때요?",
                        "provider": "ollama",
                        "model": "qwen2.5:3b",
                        "web_search_permission": "enabled",
                    }
                )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["actions_taken"], ["web_search"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertIsNone(payload["runtime_status"])

    def test_handle_chat_can_reload_recent_web_search_record(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="이재용 - 나무위키",
                            url="https://example.com/lee-jaeyong",
                            snippet="이재용 관련 주요 이력을 정리한 검색 결과입니다.",
                        )
                    ]
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            first = service.handle_chat(
                {
                    "session_id": "reload-search-session",
                    "user_text": "이재용 검색해봐",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "reload-search-session",
                    "user_text": "방금 검색한 결과 다시 보여줘",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["actions_taken"], ["load_web_search_record"])
            self.assertIn("최근 웹 검색 기록을 다시 불러왔습니다.", second["response"]["text"])
            self.assertEqual(second["response"]["active_context"]["kind"], "web_search")
            self.assertEqual(second["response"]["web_search_record_path"], first["response"]["web_search_record_path"])
            self.assertEqual(len(second["session"]["web_search_history"]), 1)

    def test_handle_chat_can_reload_recent_web_search_record_for_follow_up(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="서울 날씨 - 예보",
                            url="https://example.com/seoul-weather",
                            snippet="서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
                        )
                    ]
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            service.handle_chat(
                {
                    "session_id": "reload-follow-up-session",
                    "user_text": "서울 날씨 검색해봐",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "reload-follow-up-session",
                    "user_text": "방금 검색한 결과 핵심 3줄만 다시 정리해줘",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["actions_taken"], ["load_web_search_record", "answer_with_active_context"])
            self.assertIn("[모의 핵심 3줄]", second["response"]["text"])
            self.assertEqual(second["response"]["active_context"]["kind"], "web_search")
            self.assertTrue(second["response"]["web_search_record_path"])

    def test_handle_chat_can_reload_specific_web_search_record_by_id(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                web_search_history_dir=str(tmp_path / "web-search"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            service._build_tools = lambda: {
                "read_file": FileReaderTool(),
                "search_files": FileSearchTool(reader=FileReaderTool()),
                "search_web": _FakeWebSearchTool(
                    [
                        SimpleNamespace(
                            title="체인소맨 - 위키백과",
                            url="https://example.com/chainsawman",
                            snippet="체인소맨 관련 기본 정보를 정리한 검색 결과입니다.",
                        )
                    ]
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            first = service.handle_chat(
                {
                    "session_id": "reload-by-id-session",
                    "user_text": "체인소맨 검색해봐",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )
            record_id = first["session"]["web_search_history"][0]["record_id"]

            second = service.handle_chat(
                {
                    "session_id": "reload-by-id-session",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                    "load_web_search_record_id": record_id,
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["actions_taken"], ["load_web_search_record"])
            self.assertEqual(second["response"]["web_search_record_path"], first["response"]["web_search_record_path"])
            self.assertEqual(second["response"]["active_context"]["record_path"], first["response"]["web_search_record_path"])

    def test_handle_chat_search_uploaded_folder_returns_search_results(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            budget_bytes = "# Budget\n\nbudget discussion".encode("utf-8")
            memo_bytes = "# Memo\n\nother topic".encode("utf-8")

            payload = service.handle_chat(
                {
                    "session_id": "uploaded-search-session",
                    "provider": "mock",
                    "search_query": "budget",
                    "search_only": True,
                    "uploaded_search_files": [
                        {
                            "name": "budget-plan.md",
                            "relative_path": "team-docs/budget-plan.md",
                            "root_label": "team-docs",
                            "mime_type": "text/markdown",
                            "size_bytes": len(budget_bytes),
                            "content_base64": base64.b64encode(budget_bytes).decode("ascii"),
                        },
                        {
                            "name": "memo.md",
                            "relative_path": "team-docs/memo.md",
                            "root_label": "team-docs",
                            "mime_type": "text/markdown",
                            "size_bytes": len(memo_bytes),
                            "content_base64": base64.b64encode(memo_bytes).decode("ascii"),
                        },
                    ],
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "answer")
            self.assertIn("검색 결과:", payload["response"]["text"])
            self.assertIn("team-docs/budget-plan.md", payload["response"]["text"])
            self.assertEqual(payload["response"]["selected_source_paths"], ["team-docs/budget-plan.md"])
            self.assertIsNone(payload["runtime_status"])

    def test_handle_chat_search_uploaded_folder_can_summarize_results(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            budget_bytes = "# Budget\n\nbudget discussion".encode("utf-8")
            notes_bytes = "# Notes\n\nbudget action items".encode("utf-8")

            payload = service.handle_chat(
                {
                    "session_id": "uploaded-search-summary-session",
                    "provider": "mock",
                    "search_query": "budget",
                    "uploaded_search_files": [
                        {
                            "name": "budget-plan.md",
                            "relative_path": "team-docs/budget-plan.md",
                            "root_label": "team-docs",
                            "mime_type": "text/markdown",
                            "size_bytes": len(budget_bytes),
                            "content_base64": base64.b64encode(budget_bytes).decode("ascii"),
                        },
                        {
                            "name": "notes.md",
                            "relative_path": "team-docs/notes.md",
                            "root_label": "team-docs",
                            "mime_type": "text/markdown",
                            "size_bytes": len(notes_bytes),
                            "content_base64": base64.b64encode(notes_bytes).decode("ascii"),
                        },
                    ],
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "answer")
            self.assertIn("[모의 요약]", payload["response"]["text"])
            self.assertIn("team-docs/budget-plan.md", payload["response"]["selected_source_paths"])
            self.assertEqual(payload["response"]["active_context"]["kind"], "search")
            self.assertEqual(payload["runtime_status"]["provider"], "mock")

    def test_handle_chat_long_summary_returns_summary_chunks(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "long-source.md"
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

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "long-web-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(len(payload["response"]["summary_chunks"]), 1)
            self.assertIn(middle_signal, payload["response"]["summary_chunks"][0]["selected_line"])
            self.assertGreaterEqual(len(payload["session"]["messages"][-1]["summary_chunks"]), 1)

    def test_stream_chat_emits_runtime_and_final_events(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            events = list(
                service.stream_chat(
                    {
                        "session_id": "stream-session",
                        "source_path": str(source_path),
                        "provider": "mock",
                    }
                )
            )

            event_names = [event["event"] for event in events]
            phase_names = [event.get("phase") for event in events if event.get("event") == "phase"]
            self.assertIn("runtime_preflight", phase_names)
            self.assertIn("runtime_ready", phase_names)
            self.assertIn("read_file_started", phase_names)
            self.assertIn("summarize_started", phase_names)
            self.assertIn("runtime_status", event_names)
            self.assertIn("response_origin", event_names)
            self.assertIn("text_delta", event_names)
            self.assertEqual(events[-1]["event"], "final")
            self.assertTrue(events[-1]["data"]["ok"])
            self.assertEqual(events[-1]["data"]["response"]["response_origin"]["provider"], "mock")

    def test_cancel_stream_returns_false_for_unknown_request(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            settings = AppSettings(
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=str(Path(tmp_dir) / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.cancel_stream(session_id="missing-session", request_id="missing-request")

            self.assertTrue(payload["ok"])
            self.assertFalse(payload["cancelled"])
            self.assertEqual(payload["request_id"], "missing-request")

    def test_stream_chat_emits_cancelled_event_after_cancel_request(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            with patch("app.web.build_model_adapter", return_value=_SlowStreamingModel()):
                stream = service.stream_chat(
                    {
                        "session_id": "cancel-stream-session",
                        "source_path": str(source_path),
                        "provider": "mock",
                        "request_id": "req-cancel-1",
                    }
                )

                events = []
                cancel_response = None
                for event in stream:
                    events.append(event)
                    if event.get("event") == "text_delta":
                        cancel_response = service.cancel_stream(
                            session_id="cancel-stream-session",
                            request_id="req-cancel-1",
                        )
                        break

                events.extend(list(stream))

            self.assertIsNotNone(cancel_response)
            self.assertTrue(cancel_response["cancelled"])
            self.assertIn("cancelled", [event["event"] for event in events])
            self.assertNotIn("final", [event["event"] for event in events])
            session = service.session_store.get_session("cancel-stream-session")
            assistant_messages = [message for message in session["messages"] if message.get("role") == "assistant"]
            self.assertEqual(assistant_messages, [])

    def test_handle_chat_search_only_reports_skipped_scanned_pdf(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "scan.pdf").write_bytes(b"%PDF-1.4\n%stub pdf bytes\n")
            (docs_dir / "notes.txt").write_text("hello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            with patch(
                "tools.file_reader.importlib.import_module",
                return_value=SimpleNamespace(PdfReader=_FakeEmptyPdfReader),
            ):
                payload = service.handle_chat(
                    {
                        "session_id": "search-session",
                        "search_root": str(docs_dir),
                        "search_query": "budget",
                        "search_only": True,
                        "provider": "mock",
                    }
                )

            self.assertTrue(payload["ok"])
            self.assertIn("OCR", payload["response"]["text"])
            self.assertIsNone(payload["runtime_status"])

    def test_handle_chat_save_request_returns_approval_object(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "approval-session",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "needs_approval")
            self.assertTrue(payload["response"]["requires_approval"])
            self.assertIsNotNone(payload["response"]["approval"])
            self.assertGreater(len(payload["response"]["follow_up_suggestions"]), 0)
            self.assertEqual(len(payload["session"]["pending_approvals"]), 1)
            last_message = payload["session"]["messages"][-1]
            self.assertEqual(last_message["approval_id"], payload["response"]["approval"]["approval_id"])
            self.assertEqual(
                payload["session"]["pending_approvals"][0]["requested_path"],
                payload["response"]["approval"]["requested_path"],
            )

    def test_handle_chat_can_approve_pending_request_and_write_note(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "approved-note.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            first = service.handle_chat(
                {
                    "session_id": "approval-session",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "note_path": str(note_path),
                    "provider": "mock",
                }
            )

            approval_id = first["response"]["approval"]["approval_id"]
            second = service.handle_chat(
                {
                    "session_id": "approval-session",
                    "approved_approval_id": approval_id,
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "saved")
            self.assertEqual(second["response"]["saved_note_path"], str(note_path))
            self.assertEqual(second["response"]["response_origin"]["provider"], "system")
            self.assertEqual(second["response"]["response_origin"]["badge"], "SYSTEM")
            self.assertEqual(second["session"]["pending_approvals"], [])
            self.assertEqual(second["session"]["messages"][-1]["response_origin"]["provider"], "system")
            self.assertTrue(note_path.exists())

    def test_handle_chat_can_reissue_pending_approval_with_new_path(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            first_note_path = tmp_path / "notes" / "first-note.md"
            second_note_path = tmp_path / "notes" / "second-note.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            first = service.handle_chat(
                {
                    "session_id": "reissue-session",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "note_path": str(first_note_path),
                    "provider": "mock",
                }
            )
            first_approval = first["response"]["approval"]

            second = service.handle_chat(
                {
                    "session_id": "reissue-session",
                    "reissue_approval_id": first_approval["approval_id"],
                    "note_path": str(second_note_path),
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "needs_approval")
            self.assertEqual(second["response"]["proposed_note_path"], str(second_note_path))
            self.assertNotEqual(second["response"]["approval"]["approval_id"], first_approval["approval_id"])
            self.assertEqual(second["response"]["approval"]["requested_path"], str(second_note_path))
            self.assertEqual(second["response"]["response_origin"]["provider"], "system")
            self.assertIn("새 경로로 저장하려면 다시 승인해 주세요.", second["response"]["text"])
            self.assertEqual(len(second["session"]["pending_approvals"]), 1)
            self.assertEqual(second["session"]["pending_approvals"][0]["requested_path"], str(second_note_path))
            self.assertFalse(second_note_path.exists())

    def test_handle_chat_reissue_existing_path_marks_overwrite_without_writing(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            existing_note_path = tmp_path / "notes" / "existing-note.md"
            requested_note_path = tmp_path / "notes" / "requested-note.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            existing_note_path.parent.mkdir(parents=True, exist_ok=True)
            existing_note_path.write_text("existing", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            first = service.handle_chat(
                {
                    "session_id": "reissue-overwrite-session",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "note_path": str(requested_note_path),
                    "provider": "mock",
                }
            )

            second = service.handle_chat(
                {
                    "session_id": "reissue-overwrite-session",
                    "reissue_approval_id": first["response"]["approval"]["approval_id"],
                    "note_path": str(existing_note_path),
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "needs_approval")
            self.assertTrue(second["response"]["approval"]["overwrite"])
            self.assertIn("이미 파일이 있으므로", second["response"]["text"])
            self.assertEqual(second["session"]["pending_approvals"][0]["requested_path"], str(existing_note_path))
            self.assertEqual(existing_note_path.read_text(encoding="utf-8"), "existing")

    def test_stream_chat_emits_final_event_for_approval(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "approved-note.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            first = service.handle_chat(
                {
                    "session_id": "approval-stream-session",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "note_path": str(note_path),
                    "provider": "mock",
                }
            )
            approval_id = first["response"]["approval"]["approval_id"]

            events = list(
                service.stream_chat(
                    {
                        "session_id": "approval-stream-session",
                        "approved_approval_id": approval_id,
                    }
                )
            )

            phase_names = [event.get("phase") for event in events if event.get("event") == "phase"]
            self.assertIn("approval_execute", phase_names)
            self.assertIn("response_origin", [event["event"] for event in events])
            self.assertEqual(events[-1]["event"], "final")
            self.assertEqual(events[-1]["data"]["response"]["response_origin"]["provider"], "system")

    def test_handle_chat_follow_up_uses_active_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "context-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "context-session",
                    "user_text": "이 문서 핵심만 다시 정리해 주세요.",
                    "provider": "mock",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("[모의 핵심 3줄]", second["response"]["text"])
            self.assertEqual(second["response"]["active_context"]["label"], "source.md")
            self.assertGreaterEqual(len(second["response"]["evidence"]), 1)

    def test_handle_chat_feedback_retry_marks_response_and_limits_evidence(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text(
                "\n".join(
                    [
                        "# Demo",
                        "",
                        "## 즉시 실행 권고 사항",
                        "1. AGENTS.md를 기준으로 운영 원칙을 확정합니다.",
                        "2. 근거 밖 단정을 줄입니다.",
                    ]
                ),
                encoding="utf-8",
            )

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "retry-context-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "retry-context-session",
                    "user_text": "이 문서에서 실행할 일만 다시 정리해 주세요.",
                    "provider": "mock",
                    "retry_feedback_label": "incorrect",
                    "retry_feedback_reason": "factual_error",
                    "retry_target_message_id": "msg-demo",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("feedback_retry", second["response"]["actions_taken"])
            self.assertLessEqual(len(second["response"]["evidence"]), 2)
            self.assertIn("AGENTS.md를 기준으로 운영 원칙을 확정합니다", second["response"]["text"])

    def test_handle_chat_irrelevant_result_feedback_retries_web_search(self) -> None:
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
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
                web_search_permission="enabled",
            )
            service = WebAppService(settings=settings)
            retry_tool = _RetryingWebSearchTool()
            with patch.object(
                service,
                "_build_tools",
                return_value={
                    "read_file": FileReaderTool(),
                    "search_files": FileSearchTool(reader=FileReaderTool()),
                    "search_web": retry_tool,
                    "write_note": WriteNoteTool(allowed_roots=[str(Path.cwd()), settings.notes_dir]),
                },
            ):
                first = service.handle_chat(
                    {
                        "session_id": "retry-web-search-service",
                        "user_text": "BTS 알아봐줘",
                        "provider": "mock",
                        "web_search_permission": "enabled",
                    }
                )
                second = service.handle_chat(
                    {
                        "session_id": "retry-web-search-service",
                        "user_text": "BTS 알아봐줘",
                        "provider": "mock",
                        "web_search_permission": "enabled",
                        "retry_feedback_label": "incorrect",
                        "retry_feedback_reason": "irrelevant_result",
                    }
                )

            self.assertTrue(first["ok"])
            self.assertTrue(second["ok"])
            self.assertEqual(first["response"]["actions_taken"], ["web_search"])
            self.assertEqual(second["response"]["actions_taken"], ["feedback_retry", "web_search_retry"])
            self.assertEqual(second["response"]["response_origin"]["provider"], "web")
            self.assertIn("다시 찾아봤습니다", second["response"]["text"])
            self.assertIn("위키백과", second["response"]["text"])

    def test_handle_chat_follow_up_with_filename_uses_active_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "local-ai-assistant-project-proposal.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "context-session-2",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "context-session-2",
                    "user_text": "local-ai-assistant-project-proposal.md 핵심 3줄만 다시 정리해 주세요.",
                    "provider": "mock",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("[모의 핵심 3줄]", second["response"]["text"])
            self.assertEqual(
                second["response"]["active_context"]["label"],
                "local-ai-assistant-project-proposal.md",
            )

    def test_handle_chat_short_greeting_with_active_context_uses_general_response(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "small-talk-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "small-talk-session",
                    "user_text": "반갑고",
                    "provider": "mock",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("[모의 응답]", second["response"]["text"])
            self.assertNotIn("[모의 문서 응답]", second["response"]["text"])
            self.assertEqual(second["response"]["actions_taken"], ["respond"])
            self.assertEqual(second["session"]["active_context"]["label"], "source.md")

    def test_handle_chat_mixed_greeting_and_follow_up_uses_active_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "mixed-context-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "mixed-context-session",
                    "user_text": "안녕하세요. 이 문서 핵심만 다시 정리해 주세요.",
                    "provider": "mock",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("반갑습니다.", second["response"]["text"])
            self.assertIn("[모의 핵심 3줄]", second["response"]["text"])
            self.assertEqual(second["response"]["actions_taken"], ["answer_with_active_context"])
            self.assertEqual(second["response"]["active_context"]["label"], "source.md")

    def test_handle_chat_mixed_follow_up_without_context_returns_gentle_guidance(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            settings = AppSettings(
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=str(Path(tmp_dir) / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "no-context-mixed-session",
                    "user_text": "안녕하세요. 이 문서 핵심만 다시 정리해 주세요.",
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "error")
            self.assertIn("반갑습니다.", payload["response"]["text"])
            self.assertIn("현재 문서 문맥이 없습니다", payload["response"]["text"])

    def test_handle_chat_implicit_mixed_follow_up_uses_active_context(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "implicit-mixed-context-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "implicit-mixed-context-session",
                    "user_text": "안녕하세요. 조금 더 짧게 부탁드려요.",
                    "provider": "mock",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("반갑습니다.", second["response"]["text"])
            self.assertIn("[모의 핵심 3줄]", second["response"]["text"])
            self.assertEqual(second["response"]["actions_taken"], ["answer_with_active_context"])
            self.assertEqual(second["response"]["active_context"]["label"], "source.md")

    def test_handle_chat_colloquial_mixed_follow_up_adds_intro(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "colloquial-mixed-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "colloquial-mixed-session",
                    "user_text": "좋아요. 이걸 한 줄로 줄여 주세요.",
                    "provider": "mock",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("좋습니다.", second["response"]["text"])
            self.assertIn("[모의 핵심 3줄]", second["response"]["text"])
            self.assertEqual(second["response"]["actions_taken"], ["answer_with_active_context"])

    def test_handle_chat_action_style_follow_up_uses_action_items_intent(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world\n\n다음 행동: 승인 카드 UX를 정리합니다.", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "action-follow-up-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "action-follow-up-session",
                    "user_text": "그럼 다음엔 뭘 하면 돼요?",
                    "provider": "mock",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("[모의 실행 항목]", second["response"]["text"])
            self.assertEqual(second["response"]["actions_taken"], ["answer_with_active_context"])

    def test_handle_chat_plain_small_talk_with_context_stays_general(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "general-small-talk-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            second = service.handle_chat(
                {
                    "session_id": "general-small-talk-session",
                    "user_text": "근데 그냥 잡담인데 오늘 점심 뭐 먹지?",
                    "provider": "mock",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("[모의 응답]", second["response"]["text"])
            self.assertEqual(second["response"]["actions_taken"], ["respond"])

    def test_handle_chat_follow_up_without_context_returns_guidance(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            settings = AppSettings(
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=str(Path(tmp_dir) / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            payload = service.handle_chat(
                {
                    "session_id": "no-context-session",
                    "user_text": "local-ai-assistant-project-proposal.md 핵심 3줄만 다시 정리해 주세요.",
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "error")
            self.assertIn("현재 문서 문맥이 없습니다", payload["response"]["text"])

    def test_handle_chat_follow_up_intents_have_distinct_mock_formats(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world. approve tasks. write memo.", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            service.handle_chat(
                {
                    "session_id": "intent-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )

            key_points = service.handle_chat(
                {
                    "session_id": "intent-session",
                    "user_text": "source.md 핵심 3줄만 다시 정리해 주세요.",
                    "provider": "mock",
                }
            )
            action_items = service.handle_chat(
                {
                    "session_id": "intent-session",
                    "user_text": "source.md에서 실행할 일만 뽑아 주세요.",
                    "provider": "mock",
                }
            )
            memo = service.handle_chat(
                {
                    "session_id": "intent-session",
                    "user_text": "source.md 내용을 메모 형식으로 다시 써 주세요.",
                    "provider": "mock",
                }
            )

            self.assertIn("[모의 핵심 3줄]", key_points["response"]["text"])
            self.assertIn("[모의 실행 항목]", action_items["response"]["text"])
            self.assertIn("[모의 메모 재작성]", memo["response"]["text"])

    def test_handle_chat_can_reject_pending_request(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            first = service.handle_chat(
                {
                    "session_id": "approval-session",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "provider": "mock",
                }
            )

            approval_id = first["response"]["approval"]["approval_id"]
            second = service.handle_chat(
                {
                    "session_id": "approval-session",
                    "rejected_approval_id": approval_id,
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "answer")
            self.assertIn("취소", second["response"]["text"])
            self.assertEqual(second["session"]["pending_approvals"], [])

    def test_handle_chat_requires_model_name_for_ollama_provider(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            settings = AppSettings(
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=str(Path(tmp_dir) / "notes"),
                model_provider="mock",
                ollama_model="",
            )
            service = WebAppService(settings=settings)

            with self.assertRaises(WebApiError):
                service.handle_chat(
                    {
                        "session_id": "ollama-session",
                        "user_text": "hello",
                        "provider": "ollama",
                    }
                )

    def test_handle_chat_localizes_ollama_unreachable_error(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            settings = AppSettings(
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=str(Path(tmp_dir) / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            fake_model = SimpleNamespace(
                health_check=lambda: ModelRuntimeStatus(
                    provider="ollama",
                    configured_model="qwen2.5:3b",
                    reachable=False,
                    configured_model_available=False,
                    detail=(
                        "Unable to reach Ollama at http://localhost:11434. Is the local runtime running? "
                        "If this app is running inside WSL, localhost may point to the Linux environment instead of Windows. "
                        "Start Ollama in the same environment or use the Windows host IP as Base URL."
                    ),
                )
            )

            with patch("app.web.build_model_adapter", return_value=fake_model):
                with self.assertRaises(WebApiError) as context:
                    service.handle_chat(
                        {
                            "session_id": "ollama-session",
                            "user_text": "hello",
                            "provider": "ollama",
                            "model": "qwen2.5:3b",
                        }
                    )

        self.assertIn("Ollama에 연결할 수 없습니다", str(context.exception))
        self.assertIn("Windows 호스트 IP", str(context.exception))

    def test_send_json_ignores_broken_pipe(self) -> None:
        handler = LocalAssistantHandler.__new__(LocalAssistantHandler)
        handler.wfile = _BrokenPipeWriter()
        handler.send_response = lambda status: None
        handler.send_header = lambda name, value: None
        handler.end_headers = lambda: None

        handler._send_json(200, {"ok": True})


if __name__ == "__main__":
    unittest.main()
