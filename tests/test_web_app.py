import base64
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from types import SimpleNamespace
from unittest.mock import patch

from app.web import LocalAssistantHandler, LocalOnlyHTTPServer, WebAppService, WebApiError
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
        self._results = results
        self._pages = dict(pages or {})

    def search(self, *, query: str, max_results: int = 5):
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
            self.assertIn("claim-coverage-box", html)
            self.assertIn("evidence-scroll-region", html)
            self.assertIn("summary-chunks-scroll-region", html)
            self.assertIn("claim-coverage-scroll-region", html)
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
            self.assertIn("response-content-verdict-box", html)
            self.assertIn("response-content-reject", html)
            self.assertIn("response-content-reason-box", html)
            self.assertIn("response-content-reason-input", html)
            self.assertIn("response-content-reason-submit", html)
            self.assertIn("response-correction-box", html)
            self.assertIn("response-correction-input", html)
            self.assertIn("response-correction-submit", html)
            self.assertIn("response-correction-save-request", html)
            self.assertIn("response-candidate-confirmation-box", html)
            self.assertIn("response-candidate-confirmation-submit", html)
            self.assertIn("이 수정 방향 재사용 확인", html)
            self.assertIn("review-queue-box", html)
            self.assertIn("review-queue-list", html)
            self.assertIn("review-queue-accept", html)
            self.assertIn("검토 후보", html)
            self.assertIn("현재 후보는 검토 수락만 기록할 수 있습니다. 아직 적용, 편집, 거절은 열지 않았습니다.", html)
            self.assertIn("검토 수락", html)
            self.assertIn("aggregate-trigger-box", html)
            self.assertIn("aggregate-trigger-list", html)
            self.assertIn("aggregate-trigger-start", html)
            self.assertIn("검토 메모 적용 후보", html)
            self.assertIn("검토 메모 적용 시작", html)
            self.assertIn("현재 반복 교정 묶음은 aggregate 단위 경계만 보여주며, 아직 시작할 수 없습니다.", html)
            self.assertIn("아직 검토 메모를 적용할 수 없습니다. capability 상태가", html)
            self.assertIn("이 버튼을 누르면 grounded-brief 원문 응답에 내용 거절을 즉시 기록합니다.", html)
            self.assertIn("이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.", html)
            self.assertIn("이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.", html)
            self.assertIn("내용 거절 기록됨", html)
            self.assertIn("비워 두면 메모 기록 버튼이 켜지지 않으며", html)
            self.assertIn("빈 제출로 기록된 거절 메모를 지우는 동작은 아직 지원하지 않습니다.", html)
            self.assertIn("먼저 수정본 기록을 눌러야 저장 요청 버튼이 켜집니다.", html)
            self.assertIn("저장 요청 버튼은 직전 기록본으로만 동작합니다.", html)
            self.assertIn("positive reuse confirmation만 남깁니다.", html)
            self.assertIn("저장 승인, 내용 거절, 거절 메모, 피드백과는 별도입니다.", html)
            self.assertIn("저장 기준 요청 시점 수정본 스냅샷", html)
            self.assertIn("저장 기준: 기록된 수정본 스냅샷", html)
            self.assertIn("더 새 수정본을 저장하려면 응답 카드에서 새 저장 요청을 다시 만들어야 합니다.", html)
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
            self.assertEqual(payload["session"]["review_queue_items"], [])
            self.assertNotIn("recurrence_aggregate_candidates", payload["session"])
            self.assertEqual(payload["session"]["permissions"]["web_search"], "disabled")
            self.assertEqual(payload["session"]["web_search_history"], [])
            self.assertEqual(payload["session"]["schema_version"], "1.0")

    def test_get_session_payload_serializes_claim_coverage(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            settings = AppSettings(
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=str(Path(tmp_dir) / "notes"),
                web_search_history_dir=str(Path(tmp_dir) / "web-search"),
            )
            service = WebAppService(settings=settings)

            service.session_store.append_message(
                "claim-session",
                {
                    "role": "assistant",
                    "text": "설명형 웹 검색 답변",
                    "status": "answer",
                    "claim_coverage": [
                        {
                            "slot": "개발",
                            "status": "strong",
                            "status_label": "교차 확인",
                            "support_count": 2,
                            "candidate_count": 2,
                            "value": "펄어비스",
                            "source_role": "백과 기반",
                            "rendered_as": "fact_card",
                        },
                        {
                            "slot": "이용 형태",
                            "status": "missing",
                            "status_label": "미확인",
                            "support_count": 0,
                            "candidate_count": 0,
                            "value": "",
                            "source_role": "",
                            "rendered_as": "not_rendered",
                        },
                    ],
                },
            )

            payload = service.get_session_payload("claim-session")

            self.assertTrue(payload["ok"])
            claim_coverage = payload["session"]["messages"][-1]["claim_coverage"]
            self.assertEqual(len(claim_coverage), 2)
            self.assertEqual(claim_coverage[0]["slot"], "개발")
            self.assertEqual(claim_coverage[0]["status"], "strong")
            self.assertEqual(claim_coverage[0]["rendered_as"], "fact_card")
            self.assertEqual(claim_coverage[1]["slot"], "이용 형태")
            self.assertEqual(claim_coverage[1]["status"], "missing")

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
                {
                    "role": "assistant",
                    "text": "답변",
                    "status": "answer",
                    "artifact_id": "artifact-feedback",
                    "artifact_kind": "grounded_brief",
                },
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
            self.assertIn("artifact-feedback", log_text)
            self.assertIn("incorrect", log_text)
            self.assertIn("factual_error", log_text)

    def test_submit_correction_updates_grounded_brief_source_message_and_logs(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            source_path = base / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            settings = AppSettings(
                sessions_dir=str(base / "sessions"),
                task_log_path=str(base / "task_log.jsonl"),
                notes_dir=str(base / "notes"),
                web_search_history_dir=str(base / "web-search"),
            )
            service = WebAppService(settings=settings)

            service.session_store.append_message("correction-session", {"role": "user", "text": "질문"})
            stored_message = service.session_store.append_message(
                "correction-session",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-correction",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": [str(source_path)],
                    "response_origin": {"provider": "mock", "badge": "MOCK", "label": "모의 데모 응답", "kind": "assistant"},
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

            payload = service.submit_correction(
                {
                    "session_id": "correction-session",
                    "message_id": stored_message["message_id"],
                    "corrected_text": "수정한 요약입니다.\n핵심만 다시 적었습니다.",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["message_id"], stored_message["message_id"])
            self.assertEqual(payload["artifact_id"], "artifact-correction")
            self.assertEqual(payload["corrected_text"], "수정한 요약입니다.\n핵심만 다시 적었습니다.")
            self.assertEqual(payload["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(payload["corrected_outcome"]["artifact_id"], "artifact-correction")
            self.assertEqual(payload["corrected_outcome"]["source_message_id"], stored_message["message_id"])

            session_message = payload["session"]["messages"][-1]
            self.assertEqual(session_message["artifact_id"], "artifact-correction")
            self.assertEqual(session_message["corrected_text"], "수정한 요약입니다.\n핵심만 다시 적었습니다.")
            self.assertEqual(session_message["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(session_message["corrected_outcome"]["source_message_id"], stored_message["message_id"])
            self.assertEqual(session_message["original_response_snapshot"]["draft_text"], "원본 요약입니다.")

            log_text = Path(settings.task_log_path).read_text(encoding="utf-8")
            self.assertIn("correction_submitted", log_text)
            self.assertIn("corrected_outcome_recorded", log_text)
            self.assertIn("artifact-correction", log_text)
            self.assertIn("corrected", log_text)

    def test_submit_correction_rejects_unchanged_text(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            source_path = base / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            settings = AppSettings(
                sessions_dir=str(base / "sessions"),
                task_log_path=str(base / "task_log.jsonl"),
                notes_dir=str(base / "notes"),
                web_search_history_dir=str(base / "web-search"),
            )
            service = WebAppService(settings=settings)

            service.session_store.append_message("correction-session", {"role": "user", "text": "질문"})
            stored_message = service.session_store.append_message(
                "correction-session",
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

            with self.assertRaises(WebApiError) as cm:
                service.submit_correction(
                    {
                        "session_id": "correction-session",
                        "message_id": stored_message["message_id"],
                        "corrected_text": "원본 요약입니다.",
                    }
                )

            self.assertEqual(cm.exception.status_code, 400)
            self.assertIn("현재 초안과 동일합니다", str(cm.exception))

    def test_submit_content_verdict_records_rejected_outcome_and_logs(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            source_path = base / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            settings = AppSettings(
                sessions_dir=str(base / "sessions"),
                task_log_path=str(base / "task_log.jsonl"),
                notes_dir=str(base / "notes"),
                web_search_history_dir=str(base / "web-search"),
            )
            service = WebAppService(settings=settings)

            service.session_store.append_message("verdict-session", {"role": "user", "text": "질문"})
            stored_message = service.session_store.append_message(
                "verdict-session",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-verdict",
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

            payload = service.submit_content_verdict(
                {
                    "session_id": "verdict-session",
                    "message_id": stored_message["message_id"],
                    "content_verdict": "rejected",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["message_id"], stored_message["message_id"])
            self.assertEqual(payload["artifact_id"], "artifact-verdict")
            self.assertEqual(payload["content_verdict"], "rejected")
            self.assertEqual(payload["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(payload["corrected_outcome"]["artifact_id"], "artifact-verdict")
            self.assertEqual(payload["corrected_outcome"]["source_message_id"], stored_message["message_id"])
            self.assertEqual(payload["content_reason_record"]["reason_scope"], "content_reject")
            self.assertEqual(payload["content_reason_record"]["reason_label"], "explicit_content_rejection")
            self.assertEqual(payload["content_reason_record"]["artifact_kind"], "grounded_brief")
            self.assertEqual(payload["content_reason_record"]["source_message_id"], stored_message["message_id"])
            self.assertIsNone(payload["content_reason_record"]["reason_note"])

            session_message = payload["session"]["messages"][-1]
            self.assertEqual(session_message["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(session_message["content_reason_record"]["reason_scope"], "content_reject")
            self.assertEqual(session_message["content_reason_record"]["reason_label"], "explicit_content_rejection")
            self.assertNotIn("approval_reason_record", session_message)

            log_text = Path(settings.task_log_path).read_text(encoding="utf-8")
            self.assertIn("content_verdict_recorded", log_text)
            self.assertIn("corrected_outcome_recorded", log_text)
            self.assertIn("artifact-verdict", log_text)
            self.assertIn("explicit_content_rejection", log_text)

    def test_submit_content_reason_note_updates_existing_reject_record_and_logs(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            source_path = base / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            settings = AppSettings(
                sessions_dir=str(base / "sessions"),
                task_log_path=str(base / "task_log.jsonl"),
                notes_dir=str(base / "notes"),
                web_search_history_dir=str(base / "web-search"),
            )
            service = WebAppService(settings=settings)

            service.session_store.append_message("verdict-note-session", {"role": "user", "text": "질문"})
            stored_message = service.session_store.append_message(
                "verdict-note-session",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-verdict-note",
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

            rejected_payload = service.submit_content_verdict(
                {
                    "session_id": "verdict-note-session",
                    "message_id": stored_message["message_id"],
                    "content_verdict": "rejected",
                }
            )
            rejected_recorded_at = rejected_payload["corrected_outcome"]["recorded_at"]
            initial_reason_recorded_at = rejected_payload["content_reason_record"]["recorded_at"]

            time.sleep(0.01)

            payload = service.submit_content_reason_note(
                {
                    "session_id": "verdict-note-session",
                    "message_id": stored_message["message_id"],
                    "reason_note": "핵심 결론이 문서 문맥과 다릅니다.",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["message_id"], stored_message["message_id"])
            self.assertEqual(payload["artifact_id"], "artifact-verdict-note")
            self.assertEqual(payload["content_verdict"], "rejected")
            self.assertEqual(payload["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(payload["corrected_outcome"]["recorded_at"], rejected_recorded_at)
            self.assertEqual(payload["content_reason_record"]["reason_scope"], "content_reject")
            self.assertEqual(payload["content_reason_record"]["reason_label"], "explicit_content_rejection")
            self.assertEqual(payload["content_reason_record"]["reason_note"], "핵심 결론이 문서 문맥과 다릅니다.")
            self.assertNotEqual(payload["content_reason_record"]["recorded_at"], initial_reason_recorded_at)

            session_message = payload["session"]["messages"][-1]
            self.assertEqual(session_message["corrected_outcome"]["recorded_at"], rejected_recorded_at)
            self.assertEqual(
                session_message["content_reason_record"]["reason_note"],
                "핵심 결론이 문서 문맥과 다릅니다.",
            )

            log_text = Path(settings.task_log_path).read_text(encoding="utf-8")
            self.assertIn("content_reason_note_recorded", log_text)
            self.assertIn("핵심 결론이 문서 문맥과 다릅니다.", log_text)
            self.assertIn("explicit_content_rejection", log_text)

    def test_submit_content_reason_note_rejects_blank_note(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            source_path = base / "source.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            settings = AppSettings(
                sessions_dir=str(base / "sessions"),
                task_log_path=str(base / "task_log.jsonl"),
                notes_dir=str(base / "notes"),
                web_search_history_dir=str(base / "web-search"),
            )
            service = WebAppService(settings=settings)

            service.session_store.append_message("verdict-note-blank", {"role": "user", "text": "질문"})
            stored_message = service.session_store.append_message(
                "verdict-note-blank",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-verdict-note-blank",
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
            service.submit_content_verdict(
                {
                    "session_id": "verdict-note-blank",
                    "message_id": stored_message["message_id"],
                    "content_verdict": "rejected",
                }
            )

            with self.assertRaises(WebApiError) as ctx:
                service.submit_content_reason_note(
                    {
                        "session_id": "verdict-note-blank",
                        "message_id": stored_message["message_id"],
                        "reason_note": "   \n  ",
                    }
                )

            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("거절 메모를 입력해 주세요.", ctx.exception.message)

    def test_handle_chat_corrected_save_bridge_requires_recorded_correction(self) -> None:
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

            initial = service.handle_chat(
                {
                    "session_id": "corrected-save-guard",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )

            source_message_id = initial["response"]["source_message_id"]
            payload = service.handle_chat(
                {
                    "session_id": "corrected-save-guard",
                    "corrected_save_message_id": source_message_id,
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "error")
            self.assertIn("기록된 수정본이 없습니다", payload["response"]["text"])
            self.assertEqual(payload["session"]["pending_approvals"], [])

    def test_handle_chat_corrected_save_bridge_creates_immutable_approval_snapshot(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "source-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "corrected-save-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            source_message_id = initial["response"]["source_message_id"]
            artifact_id = initial["response"]["artifact_id"]

            service.submit_correction(
                {
                    "session_id": "corrected-save-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 A입니다.\n핵심만 남겼습니다.",
                }
            )

            bridge = service.handle_chat(
                {
                    "session_id": "corrected-save-session",
                    "corrected_save_message_id": source_message_id,
                }
            )

            self.assertTrue(bridge["ok"])
            self.assertEqual(bridge["response"]["status"], "needs_approval")
            self.assertEqual(bridge["response"]["artifact_id"], artifact_id)
            self.assertEqual(bridge["response"]["source_message_id"], source_message_id)
            self.assertEqual(bridge["response"]["save_content_source"], "corrected_text")
            self.assertIn("현재 기록된 수정본 스냅샷", bridge["response"]["text"])
            self.assertIn("요청 시점 그대로 고정", bridge["response"]["text"])
            self.assertEqual(bridge["response"]["approval"]["artifact_id"], artifact_id)
            self.assertEqual(bridge["response"]["approval"]["source_message_id"], source_message_id)
            self.assertEqual(bridge["response"]["approval"]["save_content_source"], "corrected_text")
            self.assertEqual(bridge["response"]["approval"]["requested_path"], str(note_path))
            self.assertIn("수정본 A입니다.", bridge["response"]["approval"]["preview_markdown"])

            approval_id = bridge["response"]["approval"]["approval_id"]
            pending_before = service.session_store.get_pending_approval("corrected-save-session", approval_id)
            self.assertIsNotNone(pending_before)
            self.assertEqual(pending_before["note_text"], "수정본 A입니다.\n핵심만 남겼습니다.")

            service.submit_correction(
                {
                    "session_id": "corrected-save-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 B입니다.\n다시 손봤습니다.",
                }
            )

            pending_after = service.session_store.get_pending_approval("corrected-save-session", approval_id)
            self.assertIsNotNone(pending_after)
            self.assertEqual(pending_after["note_text"], "수정본 A입니다.\n핵심만 남겼습니다.")
            self.assertIn("수정본 A입니다.", pending_after["preview_markdown"])

            approved = service.handle_chat(
                {
                    "session_id": "corrected-save-session",
                    "approved_approval_id": approval_id,
                }
            )

            self.assertTrue(approved["ok"])
            self.assertEqual(approved["response"]["status"], "saved")
            self.assertEqual(approved["response"]["artifact_id"], artifact_id)
            self.assertEqual(approved["response"]["source_message_id"], source_message_id)
            self.assertEqual(approved["response"]["save_content_source"], "corrected_text")
            self.assertEqual(approved["response"]["saved_note_path"], str(note_path))
            self.assertIn("승인 시점에 고정된 수정본", approved["response"]["text"])
            self.assertIn("다시 저장 요청", approved["response"]["text"])
            self.assertTrue(note_path.exists())
            self.assertEqual(note_path.read_text(encoding="utf-8"), "수정본 A입니다.\n핵심만 남겼습니다.")

            source_messages = [
                message
                for message in approved["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ]
            self.assertTrue(source_messages)
            source_message = source_messages[-1]
            self.assertEqual(source_message["corrected_text"], "수정본 B입니다.\n다시 손봤습니다.")
            self.assertEqual(source_message["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(source_message["corrected_outcome"]["approval_id"], approval_id)
            self.assertEqual(source_message["corrected_outcome"]["saved_note_path"], str(note_path))
            self.assertEqual(source_message["corrected_outcome"]["source_message_id"], source_message_id)

            saved_message = approved["session"]["messages"][-1]
            self.assertEqual(saved_message["artifact_id"], artifact_id)
            self.assertEqual(saved_message["source_message_id"], source_message_id)
            self.assertEqual(saved_message["save_content_source"], "corrected_text")
            self.assertEqual(approved["session"]["pending_approvals"], [])

    def test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "signal-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "signal-session",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "note_path": str(note_path),
                    "provider": "mock",
                }
            )

            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]
            original_approval_id = initial["response"]["approval"]["approval_id"]

            initial_source_message = [
                message
                for message in initial["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            initial_signal = initial_source_message["session_local_memory_signal"]
            self.assertEqual(initial_signal["signal_scope"], "session_local")
            self.assertEqual(initial_signal["artifact_id"], artifact_id)
            self.assertEqual(initial_signal["source_message_id"], source_message_id)
            self.assertIsNone(initial_signal["content_signal"]["latest_corrected_outcome"])
            self.assertFalse(initial_signal["content_signal"]["has_corrected_text"])
            self.assertNotIn("approval_signal", initial_signal)
            self.assertNotIn("save_signal", initial_signal)
            self.assertNotIn("superseded_reject_signal", initial_source_message)

            rejected_approval = service.handle_chat(
                {
                    "session_id": "signal-session",
                    "rejected_approval_id": original_approval_id,
                }
            )

            rejected_source_message = [
                message
                for message in rejected_approval["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            rejected_signal = rejected_source_message["session_local_memory_signal"]
            self.assertEqual(
                rejected_signal["approval_signal"]["latest_approval_reason_record"]["reason_scope"],
                "approval_reject",
            )
            self.assertEqual(
                rejected_signal["approval_signal"]["latest_approval_reason_record"]["reason_label"],
                "explicit_rejection",
            )
            self.assertEqual(
                rejected_signal["approval_signal"]["latest_approval_reason_record"]["approval_id"],
                original_approval_id,
            )
            self.assertNotIn("save_signal", rejected_signal)
            self.assertNotIn("superseded_reject_signal", rejected_source_message)

            service.submit_correction(
                {
                    "session_id": "signal-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 시그널입니다.\n핵심만 남겼습니다.",
                }
            )
            bridge = service.handle_chat(
                {
                    "session_id": "signal-session",
                    "corrected_save_message_id": source_message_id,
                }
            )
            corrected_approval_id = bridge["response"]["approval"]["approval_id"]
            approved = service.handle_chat(
                {
                    "session_id": "signal-session",
                    "approved_approval_id": corrected_approval_id,
                }
            )

            source_message = [
                message
                for message in approved["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            signal = source_message["session_local_memory_signal"]
            self.assertEqual(signal["signal_scope"], "session_local")
            self.assertEqual(signal["artifact_id"], artifact_id)
            self.assertEqual(signal["source_message_id"], source_message_id)
            self.assertEqual(signal["content_signal"]["latest_corrected_outcome"]["outcome"], "corrected")
            self.assertTrue(signal["content_signal"]["has_corrected_text"])
            self.assertNotIn("content_reason_record", signal["content_signal"])
            self.assertEqual(
                signal["approval_signal"]["latest_approval_reason_record"]["approval_id"],
                original_approval_id,
            )
            self.assertEqual(signal["save_signal"]["latest_save_content_source"], "corrected_text")
            self.assertEqual(signal["save_signal"]["latest_saved_note_path"], str(note_path))
            self.assertEqual(signal["save_signal"]["latest_approval_id"], corrected_approval_id)
            self.assertNotIn("superseded_reject_signal", source_message)

    def test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals(self) -> None:
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

            initial = service.handle_chat(
                {
                    "session_id": "session-local-candidate-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )

            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]

            initial_source_message = [
                message
                for message in initial["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertNotIn("session_local_candidate", initial_source_message)
            self.assertNotIn("candidate_recurrence_key", initial_source_message)

            rejected = service.submit_content_verdict(
                {
                    "session_id": "session-local-candidate-session",
                    "message_id": source_message_id,
                    "content_verdict": "rejected",
                }
            )
            rejected_source_message = [
                message
                for message in rejected["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertNotIn("session_local_candidate", rejected_source_message)
            self.assertNotIn("candidate_recurrence_key", rejected_source_message)

            corrected = service.submit_correction(
                {
                    "session_id": "session-local-candidate-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본입니다.\n핵심만 남겼습니다.",
                }
            )

            source_message = [
                message
                for message in corrected["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            candidate = source_message["session_local_candidate"]
            recurrence_key = source_message["candidate_recurrence_key"]
            corrected_outcome = source_message["session_local_memory_signal"]["content_signal"]["latest_corrected_outcome"]
            self.assertEqual(
                candidate["candidate_id"],
                f"session-local-candidate:{artifact_id}:{source_message_id}:correction_rewrite_preference",
            )
            self.assertEqual(candidate["candidate_scope"], "session_local")
            self.assertEqual(candidate["candidate_family"], "correction_rewrite_preference")
            self.assertEqual(
                candidate["statement"],
                "explicit rewrite correction recorded for this grounded brief",
            )
            self.assertEqual(candidate["supporting_artifact_ids"], [artifact_id])
            self.assertEqual(candidate["supporting_source_message_ids"], [source_message_id])
            self.assertEqual(
                candidate["supporting_signal_refs"],
                [
                    {
                        "signal_name": "session_local_memory_signal.content_signal",
                        "relationship": "primary_basis",
                    }
                ],
            )
            self.assertEqual(candidate["evidence_strength"], "explicit_single_artifact")
            self.assertEqual(candidate["status"], "session_local_candidate")
            self.assertEqual(candidate["created_at"], corrected_outcome["recorded_at"])
            self.assertEqual(candidate["updated_at"], corrected_outcome["recorded_at"])
            self.assertEqual(recurrence_key["candidate_family"], "correction_rewrite_preference")
            self.assertEqual(recurrence_key["key_scope"], "correction_rewrite_recurrence")
            self.assertEqual(recurrence_key["key_version"], "explicit_pair_rewrite_delta_v1")
            self.assertEqual(recurrence_key["derivation_source"], "explicit_corrected_pair")
            self.assertEqual(recurrence_key["source_candidate_id"], candidate["candidate_id"])
            self.assertEqual(recurrence_key["source_candidate_updated_at"], candidate["updated_at"])
            self.assertTrue(recurrence_key["normalized_delta_fingerprint"].startswith("sha256:"))
            self.assertIn("replace", recurrence_key["rewrite_dimensions"]["change_types"])
            self.assertGreaterEqual(recurrence_key["rewrite_dimensions"]["changed_segment_count"], 1)
            self.assertEqual(recurrence_key["stability"], "deterministic_local")
            self.assertEqual(recurrence_key["derived_at"], candidate["updated_at"])
            self.assertEqual(
                source_message["session_local_memory_signal"]["content_signal"]["latest_corrected_outcome"]["outcome"],
                "corrected",
            )
            self.assertIn("superseded_reject_signal", source_message)
            self.assertNotIn("historical_save_identity_signal", source_message)

    def test_session_local_candidate_uses_current_save_signal_only_for_support(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "candidate-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "session-local-candidate-save-support",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]

            service.submit_correction(
                {
                    "session_id": "session-local-candidate-save-support",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 A입니다.\n핵심만 남겼습니다.",
                }
            )
            bridge = service.handle_chat(
                {
                    "session_id": "session-local-candidate-save-support",
                    "corrected_save_message_id": source_message_id,
                    "note_path": str(note_path),
                }
            )
            approval_id = bridge["response"]["approval"]["approval_id"]
            approved = service.handle_chat(
                {
                    "session_id": "session-local-candidate-save-support",
                    "approved_approval_id": approval_id,
                }
            )

            approved_source_message = [
                message
                for message in approved["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            supported_candidate = approved_source_message["session_local_candidate"]
            supported_recurrence_key = approved_source_message["candidate_recurrence_key"]
            self.assertEqual(supported_candidate["evidence_strength"], "explicit_single_artifact")
            self.assertEqual(
                supported_candidate["supporting_signal_refs"],
                [
                    {
                        "signal_name": "session_local_memory_signal.content_signal",
                        "relationship": "primary_basis",
                    },
                    {
                        "signal_name": "session_local_memory_signal.save_signal",
                        "relationship": "supporting_evidence",
                    },
                ],
            )
            self.assertEqual(supported_recurrence_key["source_candidate_id"], supported_candidate["candidate_id"])
            self.assertEqual(
                supported_recurrence_key["source_candidate_updated_at"],
                supported_candidate["updated_at"],
            )
            self.assertNotIn("historical_save_identity_signal", approved_source_message)

            corrected_again = service.submit_correction(
                {
                    "session_id": "session-local-candidate-save-support",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 B입니다.\n다시 다듬었습니다.",
                }
            )

            source_message = [
                message
                for message in corrected_again["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            candidate = source_message["session_local_candidate"]
            recurrence_key = source_message["candidate_recurrence_key"]
            corrected_outcome = source_message["session_local_memory_signal"]["content_signal"]["latest_corrected_outcome"]
            self.assertEqual(candidate["candidate_family"], "correction_rewrite_preference")
            self.assertEqual(candidate["evidence_strength"], "explicit_single_artifact")
            self.assertEqual(
                candidate["supporting_signal_refs"],
                [
                    {
                        "signal_name": "session_local_memory_signal.content_signal",
                        "relationship": "primary_basis",
                    }
                ],
            )
            self.assertEqual(candidate["created_at"], corrected_outcome["recorded_at"])
            self.assertEqual(candidate["updated_at"], corrected_outcome["recorded_at"])
            self.assertEqual(recurrence_key["source_candidate_id"], candidate["candidate_id"])
            self.assertEqual(recurrence_key["source_candidate_updated_at"], candidate["updated_at"])
            self.assertNotEqual(
                recurrence_key["normalized_delta_fingerprint"],
                supported_recurrence_key["normalized_delta_fingerprint"],
            )
            self.assertIn("historical_save_identity_signal", source_message)
            self.assertNotIn(
                {
                    "signal_name": "historical_save_identity_signal",
                    "relationship": "supporting_evidence",
                },
                candidate["supporting_signal_refs"],
            )

    def test_recurrence_aggregate_candidates_require_two_distinct_source_messages_and_ignore_same_anchor_replays(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_source_path = tmp_path / "source-a.md"
            second_source_path = tmp_path / "source-b.md"
            third_source_path = tmp_path / "source-c.md"
            shared_body = "# Demo\n\nhello world"
            first_source_path.write_text(shared_body, encoding="utf-8")
            second_source_path.write_text(shared_body, encoding="utf-8")
            third_source_path.write_text(shared_body, encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            first = service.handle_chat(
                {
                    "session_id": "recurrence-aggregate-session",
                    "source_path": str(first_source_path),
                    "provider": "mock",
                }
            )
            first_artifact_id = first["response"]["artifact_id"]
            first_source_message_id = first["response"]["source_message_id"]
            corrected_text = "수정본입니다.\n핵심만 남겼습니다."
            first_corrected = service.submit_correction(
                {
                    "session_id": "recurrence-aggregate-session",
                    "message_id": first_source_message_id,
                    "corrected_text": corrected_text,
                }
            )
            self.assertNotIn("recurrence_aggregate_candidates", first_corrected["session"])

            second = service.handle_chat(
                {
                    "session_id": "recurrence-aggregate-session",
                    "source_path": str(second_source_path),
                    "provider": "mock",
                }
            )
            second_artifact_id = second["response"]["artifact_id"]
            second_source_message_id = second["response"]["source_message_id"]
            second_corrected = service.submit_correction(
                {
                    "session_id": "recurrence-aggregate-session",
                    "message_id": second_source_message_id,
                    "corrected_text": corrected_text,
                }
            )

            self.assertIn("recurrence_aggregate_candidates", second_corrected["session"])
            aggregate = second_corrected["session"]["recurrence_aggregate_candidates"][0]
            self.assertEqual(len(second_corrected["session"]["recurrence_aggregate_candidates"]), 1)
            self.assertEqual(
                aggregate["aggregate_key"],
                {
                    "candidate_family": "correction_rewrite_preference",
                    "key_scope": "correction_rewrite_recurrence",
                    "key_version": "explicit_pair_rewrite_delta_v1",
                    "derivation_source": "explicit_corrected_pair",
                    "normalized_delta_fingerprint": aggregate["aggregate_key"]["normalized_delta_fingerprint"],
                },
            )
            self.assertEqual(aggregate["recurrence_count"], 2)
            self.assertEqual(aggregate["scope_boundary"], "same_session_current_state_only")
            self.assertEqual(aggregate["confidence_marker"], "same_session_exact_key_match")
            self.assertEqual(
                aggregate["aggregate_promotion_marker"],
                {
                    "promotion_basis": "same_session_exact_recurrence_aggregate",
                    "promotion_eligibility": "blocked_pending_reviewed_memory_boundary",
                    "reviewed_memory_boundary": "not_open",
                    "marker_version": "same_session_blocked_reviewed_memory_v1",
                    "derived_at": aggregate["last_seen_at"],
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
                    "evaluated_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_boundary_draft"],
                {
                    "boundary_version": "fixed_narrow_reviewed_scope_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "boundary_stage": "draft_not_applied",
                    "drafted_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_rollback_contract"],
                {
                    "rollback_version": "first_reviewed_memory_effect_reversal_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "rollback_target_kind": "future_applied_reviewed_memory_effect_only",
                    "rollback_stage": "contract_only_not_applied",
                    "audit_trace_expectation": "operator_visible_local_transition_required",
                    "defined_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_disable_contract"],
                {
                    "disable_version": "first_reviewed_memory_effect_stop_apply_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "disable_target_kind": "future_applied_reviewed_memory_effect_only",
                    "disable_stage": "contract_only_not_applied",
                    "effect_behavior": "stop_apply_without_reversal",
                    "audit_trace_expectation": "operator_visible_local_transition_required",
                    "defined_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_conflict_contract"],
                {
                    "conflict_version": "first_reviewed_memory_scope_visibility_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "conflict_target_categories": [
                        "future_reviewed_memory_candidate_draft_vs_applied_effect",
                        "future_applied_reviewed_memory_effect_vs_applied_effect",
                    ],
                    "conflict_visibility_stage": "contract_only_not_resolved",
                    "audit_trace_expectation": "operator_visible_local_transition_required",
                    "defined_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_transition_audit_contract"],
                {
                    "audit_version": "first_reviewed_memory_transition_identity_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
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
                    "defined_at": aggregate["last_seen_at"],
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
                    "evaluated_at": aggregate["last_seen_at"],
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
                    "capability_outcome": "unblocked_all_required",
                    "satisfaction_basis_boundary": "canonical_reviewed_memory_layer_capabilities_only",
                    "partial_state_policy": "partial_states_not_materialized",
                    "evaluated_at": aggregate["last_seen_at"],
                },
            )
            source_context = {
                "source_version": "same_session_reviewed_memory_capability_source_refs_v1",
                "source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "required_preconditions": list(
                    aggregate["reviewed_memory_unblock_contract"]["required_preconditions"]
                ),
                "evaluated_at": aggregate["last_seen_at"],
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
                    "trigger_action_label": "검토 메모 적용 시작",
                    "trigger_state": "visible_disabled",
                    "target_label": "eligible_for_reviewed_memory_draft_planning_only",
                    "target_boundary": "reviewed_memory_draft_planning_only",
                    "defined_at": aggregate["last_seen_at"],
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
            mismatched_source_context = dict(source_context)
            mismatched_source_context["aggregate_identity_ref"] = {"candidate_family": "different"}
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
                    aggregate,
                    mismatched_source_context,
                )
            )
            aggregate_without_first_seen_at = dict(aggregate)
            aggregate_without_first_seen_at.pop("first_seen_at", None)
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
            self.assertIn("reviewed_memory_capability_basis", aggregate)
            capability_basis = aggregate["reviewed_memory_capability_basis"]
            self.assertEqual(capability_basis["basis_version"], "same_session_reviewed_memory_capability_basis_v1")
            self.assertEqual(capability_basis["reviewed_scope"], "same_session_exact_recurrence_aggregate_only")
            self.assertEqual(capability_basis["aggregate_identity_ref"], dict(aggregate["aggregate_key"]))
            self.assertEqual(capability_basis["basis_status"], "all_required_capabilities_present")
            self.assertEqual(capability_basis["satisfaction_basis_boundary"], "canonical_reviewed_memory_layer_capabilities_only")
            self.assertEqual(
                aggregate["reviewed_memory_capability_status"]["capability_outcome"],
                "unblocked_all_required",
            )
            self.assertEqual(
                aggregate["reviewed_memory_planning_target_ref"],
                {
                    "planning_target_version": "same_session_reviewed_memory_planning_target_ref_v1",
                    "target_label": "eligible_for_reviewed_memory_draft_planning_only",
                    "target_scope": "same_session_exact_recurrence_aggregate_only",
                    "target_boundary": "reviewed_memory_draft_planning_only",
                    "defined_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_planning_target_ref"]["target_label"],
                "eligible_for_reviewed_memory_draft_planning_only",
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_transition_record(aggregate)
            )
            self.assertNotIn("future_transition_target", aggregate["reviewed_memory_precondition_status"])
            self.assertNotIn("readiness_target", aggregate["reviewed_memory_unblock_contract"])
            self.assertNotIn("readiness_target", aggregate["reviewed_memory_capability_status"])
            self.assertEqual(
                {
                    (item["artifact_id"], item["source_message_id"])
                    for item in aggregate["supporting_source_message_refs"]
                },
                {
                    (first_artifact_id, first_source_message_id),
                    (second_artifact_id, second_source_message_id),
                },
            )
            self.assertEqual(
                {
                    (item["artifact_id"], item["source_message_id"])
                    for item in aggregate["supporting_candidate_refs"]
                },
                {
                    (first_artifact_id, first_source_message_id),
                    (second_artifact_id, second_source_message_id),
                },
            )
            self.assertNotIn("supporting_review_refs", aggregate)

            third = service.handle_chat(
                {
                    "session_id": "recurrence-aggregate-session",
                    "source_path": str(third_source_path),
                    "provider": "mock",
                }
            )
            third_source_message_id = third["response"]["source_message_id"]
            third_corrected = service.submit_correction(
                {
                    "session_id": "recurrence-aggregate-session",
                    "message_id": third_source_message_id,
                    "corrected_text": "수정본입니다.\n다르게 손봤습니다.",
                }
            )
            self.assertEqual(len(third_corrected["session"]["recurrence_aggregate_candidates"]), 1)
            self.assertEqual(
                third_corrected["session"]["recurrence_aggregate_candidates"][0]["recurrence_count"],
                2,
            )

            source_messages = [
                message
                for message in third_corrected["session"]["messages"]
                if message.get("original_response_snapshot")
            ]
            for source_message in source_messages:
                self.assertIn("session_local_candidate", source_message)
                self.assertIn("candidate_recurrence_key", source_message)
                self.assertNotIn("candidate_review_record", source_message)

    def test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            messages = [
                {
                    "message_id": "msg-web-proof-a",
                    "source_message_id": "msg-web-proof-a",
                    "artifact_id": "artifact-web-proof-a",
                    "artifact_kind": "grounded_brief",
                    "role": "assistant",
                    "text": "초안입니다.",
                    "original_response_snapshot": {
                        "artifact_id": "artifact-web-proof-a",
                        "artifact_kind": "grounded_brief",
                        "draft_text": "초안입니다.",
                    },
                    "corrected_text": "다듬은 초안입니다.",
                    "corrected_outcome": {
                        "outcome": "corrected",
                        "recorded_at": "2026-03-28T00:01:00+00:00",
                        "artifact_id": "artifact-web-proof-a",
                        "source_message_id": "msg-web-proof-a",
                    },
                },
                {
                    "message_id": "msg-web-proof-b",
                    "source_message_id": "msg-web-proof-b",
                    "artifact_id": "artifact-web-proof-b",
                    "artifact_kind": "grounded_brief",
                    "role": "assistant",
                    "text": "초안입니다.",
                    "original_response_snapshot": {
                        "artifact_id": "artifact-web-proof-b",
                        "artifact_kind": "grounded_brief",
                        "draft_text": "초안입니다.",
                    },
                    "corrected_text": "다듬은 초안입니다.",
                    "corrected_outcome": {
                        "outcome": "corrected",
                        "recorded_at": "2026-03-28T00:02:00+00:00",
                        "artifact_id": "artifact-web-proof-b",
                        "source_message_id": "msg-web-proof-b",
                    },
                },
            ]
            session_payload = {
                "session_id": "web-proof-record-session",
                "messages": messages,
            }
            for message in messages:
                session_local_memory_signal = service.session_store.build_session_local_memory_signal(
                    session_payload,
                    source_message=message,
                )
                session_local_candidate = service._build_session_local_candidate_for_message(
                    message=message,
                    session_local_memory_signal=session_local_memory_signal,
                )
                message["candidate_recurrence_key"] = service._serialize_candidate_recurrence_key(
                    service._build_candidate_recurrence_key_for_message(
                        message=message,
                        session_local_candidate=session_local_candidate,
                    )
                )

            base_aggregate = service._build_recurrence_aggregate_candidates(messages)[0]
            source_context = service._build_recurrence_aggregate_reviewed_memory_source_context(
                base_aggregate
            )
            self.assertIsNotNone(source_context)
            boundary_source_ref = service._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
                base_aggregate,
                source_context or {},
            )
            self.assertIsNotNone(boundary_source_ref)
            proof_record_store_entries = (
                service._build_reviewed_memory_local_effect_presence_proof_record_store_entries(
                    [base_aggregate]
                )
            )
            self.assertEqual(len(proof_record_store_entries), 1)
            proof_record_entry = proof_record_store_entries[0]
            self.assertIsNotNone(proof_record_entry.get("applied_effect_id"))
            aggregate_with_store = service._build_recurrence_aggregate_candidates(
                messages,
                proof_record_store_entries=proof_record_store_entries,
            )[0]
            expected_proof_record_entry = {
                "proof_record_version": "first_same_session_reviewed_memory_local_effect_presence_proof_record_v1",
                "proof_record_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "proof_capability_boundary": "local_effect_presence_only",
                "proof_record_stage": "canonical_presence_recorded_local_only",
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "present_locally_at": base_aggregate["last_seen_at"],
            }
            if isinstance(base_aggregate.get("supporting_review_refs"), list) and base_aggregate.get(
                "supporting_review_refs"
            ):
                expected_proof_record_entry["supporting_review_refs"] = list(
                    base_aggregate["supporting_review_refs"]
                )
            self.assertEqual(
                proof_record_entry,
                expected_proof_record_entry,
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "proof_boundary_version": "first_same_session_reviewed_memory_local_effect_presence_proof_boundary_v1",
                    "proof_boundary_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "boundary_source_ref": dict(boundary_source_ref),
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "proof_capability_boundary": "local_effect_presence_only",
                    "proof_stage": "first_presence_proved_local_only",
                    "applied_effect_id": proof_record_entry["applied_effect_id"],
                    "present_locally_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "fact_source_instance_version": (
                        "first_same_session_reviewed_memory_local_effect_presence_fact_source_instance_v1"
                    ),
                    "fact_source_instance_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "boundary_source_ref": dict(boundary_source_ref),
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "fact_capability_boundary": "local_effect_presence_only",
                    "fact_stage": "presence_fact_available_local_only",
                    "applied_effect_id": proof_record_entry["applied_effect_id"],
                    "present_locally_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "fact_source_version": "first_same_session_reviewed_memory_local_effect_presence_fact_source_v1",
                    "fact_source_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "boundary_source_ref": dict(boundary_source_ref),
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "fact_capability_boundary": "local_effect_presence_only",
                    "fact_stage": "presence_fact_available_local_only",
                    "applied_effect_id": proof_record_entry["applied_effect_id"],
                    "present_locally_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "event_version": "first_same_session_reviewed_memory_local_effect_presence_event_v1",
                    "event_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "boundary_source_ref": dict(boundary_source_ref),
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "event_capability_boundary": "local_effect_presence_only",
                    "event_stage": "presence_observed_local_only",
                    "applied_effect_id": proof_record_entry["applied_effect_id"],
                    "present_locally_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "producer_version": "first_same_session_reviewed_memory_local_effect_presence_event_producer_v1",
                    "producer_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "boundary_source_ref": dict(boundary_source_ref),
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "producer_capability_boundary": "local_effect_presence_only",
                    "producer_stage": "presence_event_recorded_local_only",
                    "applied_effect_id": proof_record_entry["applied_effect_id"],
                    "present_locally_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "event_source_version": "first_same_session_reviewed_memory_local_effect_presence_event_source_v1",
                    "event_source_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "boundary_source_ref": dict(boundary_source_ref),
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "event_capability_boundary": "local_effect_presence_only",
                    "event_stage": "presence_event_recorded_local_only",
                    "applied_effect_id": proof_record_entry["applied_effect_id"],
                    "present_locally_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "source_version": "first_same_session_reviewed_memory_local_effect_presence_record_v1",
                    "source_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "boundary_source_ref": dict(boundary_source_ref),
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "source_capability_boundary": "local_effect_presence_only",
                    "source_stage": "presence_recorded_local_only",
                    "applied_effect_id": proof_record_entry["applied_effect_id"],
                    "present_locally_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_applied_effect_target(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "target_version": "first_same_session_reviewed_memory_applied_effect_target_v1",
                    "target_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "boundary_source_ref": dict(boundary_source_ref),
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "target_capability_boundary": "local_effect_presence_only",
                    "target_stage": "effect_present_local_only",
                    "applied_effect_id": proof_record_entry["applied_effect_id"],
                    "present_locally_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
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
                "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "rollback_contract_ref": dict(base_aggregate["reviewed_memory_rollback_contract"]),
                "applied_effect_id": proof_record_entry["applied_effect_id"],
                "defined_at": base_aggregate["last_seen_at"],
            }
            if isinstance(base_aggregate.get("supporting_review_refs"), list) and base_aggregate.get(
                "supporting_review_refs"
            ):
                handle_identity_payload["supporting_review_refs"] = list(
                    base_aggregate["supporting_review_refs"]
                )
            expected_handle_id = (
                "reviewed-memory-handle:"
                + hashlib.sha256(
                    json.dumps(handle_identity_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()[:24]
            )
            self.assertEqual(
                service._build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(
                    aggregate_with_store,
                    source_context,
                ),
                {
                    "handle_version": "first_same_session_reviewed_memory_reversible_effect_handle_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "boundary_source_ref": dict(boundary_source_ref),
                    "rollback_contract_ref": dict(base_aggregate["reviewed_memory_rollback_contract"]),
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "effect_capability": "reversible_local_only",
                    "effect_invariant": "retain_identity_supporting_refs_boundary_and_audit",
                    "effect_stage": "handle_defined_not_applied",
                    "handle_id": expected_handle_id,
                    "defined_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
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
                    "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                    "handle_id": expected_handle_id,
                    "effect_target_kind": "applied_reviewed_memory_effect",
                    "effect_capability": "reversible_local_only",
                    "effect_stage": "handle_defined_not_applied",
                    "defined_at": base_aggregate["last_seen_at"],
                }
                | (
                    {"supporting_review_refs": list(base_aggregate["supporting_review_refs"])}
                    if isinstance(base_aggregate.get("supporting_review_refs"), list)
                    and base_aggregate.get("supporting_review_refs")
                    else {}
                ),
            )

            expected_disable_source_ref = {
                "ref_version": "same_session_reviewed_memory_disable_source_ref_v1",
                "ref_kind": "reviewed_memory_disable_contract_backed_source",
                "ref_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "disable_contract_ref": dict(base_aggregate["reviewed_memory_disable_contract"]),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "effect_capability": "disable_local_only",
                "effect_stage": "disable_defined_not_applied",
                "defined_at": base_aggregate["last_seen_at"],
            }
            if isinstance(base_aggregate.get("supporting_review_refs"), list) and base_aggregate.get(
                "supporting_review_refs"
            ):
                expected_disable_source_ref["supporting_review_refs"] = list(
                    base_aggregate["supporting_review_refs"]
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
                "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "conflict_contract_ref": dict(base_aggregate["reviewed_memory_conflict_contract"]),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "effect_capability": "conflict_visible_local_only",
                "effect_stage": "conflict_scope_defined_not_applied",
                "defined_at": base_aggregate["last_seen_at"],
            }
            if isinstance(base_aggregate.get("supporting_review_refs"), list) and base_aggregate.get(
                "supporting_review_refs"
            ):
                expected_conflict_source_ref["supporting_review_refs"] = list(
                    base_aggregate["supporting_review_refs"]
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
                "aggregate_identity_ref": dict(base_aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(base_aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(base_aggregate["supporting_candidate_refs"]),
                "boundary_source_ref": dict(boundary_source_ref),
                "transition_audit_contract_ref": dict(base_aggregate["reviewed_memory_transition_audit_contract"]),
                "effect_target_kind": "applied_reviewed_memory_effect",
                "effect_capability": "transition_audit_local_only",
                "effect_stage": "audit_defined_not_emitted",
                "defined_at": base_aggregate["last_seen_at"],
            }
            if isinstance(base_aggregate.get("supporting_review_refs"), list) and base_aggregate.get(
                "supporting_review_refs"
            ):
                expected_transition_audit_source_ref["supporting_review_refs"] = list(
                    base_aggregate["supporting_review_refs"]
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

            payload = service._serialize_session(
                {
                    "session_id": session_payload["session_id"],
                    "title": "web-proof-record-session",
                    "messages": messages,
                    "pending_approvals": [],
                    "permissions": {"web_search": "disabled"},
                    "created_at": "2026-03-28T00:00:00+00:00",
                    "updated_at": "2026-03-28T00:02:00+00:00",
                }
            )

            self.assertNotIn("reviewed_memory_local_effect_presence_proof_record_store", payload)
            aggregate = payload["recurrence_aggregate_candidates"][0]
            self.assertNotIn("_reviewed_memory_local_effect_presence_proof_record_store_entries", aggregate)
            self.assertNotIn("reviewed_memory_local_effect_presence_proof_record", aggregate)
            self.assertNotIn("reviewed_memory_local_effect_presence_proof_boundary", aggregate)
            self.assertNotIn("reviewed_memory_local_effect_presence_fact_source_instance", aggregate)
            self.assertNotIn("reviewed_memory_local_effect_presence_fact_source", aggregate)
            self.assertNotIn("reviewed_memory_local_effect_presence_event", aggregate)
            self.assertNotIn("reviewed_memory_local_effect_presence_event_producer", aggregate)
            self.assertNotIn("reviewed_memory_local_effect_presence_event_source", aggregate)
            self.assertNotIn("reviewed_memory_local_effect_presence_record", aggregate)
            self.assertNotIn("reviewed_memory_applied_effect_target", aggregate)
            self.assertNotIn("reviewed_memory_reversible_effect_handle", aggregate)
            self.assertNotIn("reviewed_memory_capability_source_refs", aggregate)
            self.assertIn("reviewed_memory_capability_basis", aggregate)
            capability_basis = aggregate["reviewed_memory_capability_basis"]
            self.assertEqual(capability_basis["basis_version"], "same_session_reviewed_memory_capability_basis_v1")
            self.assertEqual(capability_basis["reviewed_scope"], "same_session_exact_recurrence_aggregate_only")
            self.assertEqual(capability_basis["aggregate_identity_ref"], dict(aggregate["aggregate_key"]))
            self.assertEqual(capability_basis["basis_status"], "all_required_capabilities_present")
            self.assertEqual(capability_basis["satisfaction_basis_boundary"], "canonical_reviewed_memory_layer_capabilities_only")
            self.assertNotIn("reviewed_memory_transition_record", aggregate)
            self.assertEqual(
                aggregate["reviewed_memory_capability_status"]["capability_outcome"],
                "unblocked_all_required",
            )

    def test_recurrence_aggregate_candidates_keep_candidate_review_as_support_only(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_source_path = tmp_path / "source-a.md"
            second_source_path = tmp_path / "source-b.md"
            shared_body = "# Demo\n\nhello world"
            first_source_path.write_text(shared_body, encoding="utf-8")
            second_source_path.write_text(shared_body, encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            first = service.handle_chat(
                {
                    "session_id": "recurrence-aggregate-review-session",
                    "source_path": str(first_source_path),
                    "provider": "mock",
                }
            )
            first_artifact_id = first["response"]["artifact_id"]
            first_source_message_id = first["response"]["source_message_id"]
            corrected_text = "수정본입니다.\n핵심만 남겼습니다."
            first_corrected = service.submit_correction(
                {
                    "session_id": "recurrence-aggregate-review-session",
                    "message_id": first_source_message_id,
                    "corrected_text": corrected_text,
                }
            )
            first_source_message = [
                message
                for message in first_corrected["session"]["messages"]
                if message.get("artifact_id") == first_artifact_id and message.get("original_response_snapshot")
            ][-1]
            candidate = first_source_message["session_local_candidate"]

            confirmed = service.submit_candidate_confirmation(
                {
                    "session_id": "recurrence-aggregate-review-session",
                    "message_id": first_source_message_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                }
            )
            reviewed = service.submit_candidate_review(
                {
                    "session_id": "recurrence-aggregate-review-session",
                    "message_id": first_source_message_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                    "review_action": "accept",
                }
            )
            self.assertEqual(reviewed["session"]["review_queue_items"], [])

            second = service.handle_chat(
                {
                    "session_id": "recurrence-aggregate-review-session",
                    "source_path": str(second_source_path),
                    "provider": "mock",
                }
            )
            second_artifact_id = second["response"]["artifact_id"]
            second_source_message_id = second["response"]["source_message_id"]
            payload = service.submit_correction(
                {
                    "session_id": "recurrence-aggregate-review-session",
                    "message_id": second_source_message_id,
                    "corrected_text": corrected_text,
                }
            )

            self.assertIn("recurrence_aggregate_candidates", payload["session"])
            aggregate = payload["session"]["recurrence_aggregate_candidates"][0]
            self.assertEqual(aggregate["recurrence_count"], 2)
            self.assertEqual(aggregate["confidence_marker"], "same_session_exact_key_match")
            self.assertEqual(
                aggregate["aggregate_promotion_marker"],
                {
                    "promotion_basis": "same_session_exact_recurrence_aggregate",
                    "promotion_eligibility": "blocked_pending_reviewed_memory_boundary",
                    "reviewed_memory_boundary": "not_open",
                    "marker_version": "same_session_blocked_reviewed_memory_v1",
                    "derived_at": aggregate["last_seen_at"],
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
                    "evaluated_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_boundary_draft"],
                {
                    "boundary_version": "fixed_narrow_reviewed_scope_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                    "boundary_stage": "draft_not_applied",
                    "drafted_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_rollback_contract"],
                {
                    "rollback_version": "first_reviewed_memory_effect_reversal_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                    "rollback_target_kind": "future_applied_reviewed_memory_effect_only",
                    "rollback_stage": "contract_only_not_applied",
                    "audit_trace_expectation": "operator_visible_local_transition_required",
                    "defined_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_disable_contract"],
                {
                    "disable_version": "first_reviewed_memory_effect_stop_apply_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                    "disable_target_kind": "future_applied_reviewed_memory_effect_only",
                    "disable_stage": "contract_only_not_applied",
                    "effect_behavior": "stop_apply_without_reversal",
                    "audit_trace_expectation": "operator_visible_local_transition_required",
                    "defined_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_conflict_contract"],
                {
                    "conflict_version": "first_reviewed_memory_scope_visibility_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                    "conflict_target_categories": [
                        "future_reviewed_memory_candidate_draft_vs_applied_effect",
                        "future_applied_reviewed_memory_effect_vs_applied_effect",
                    ],
                    "conflict_visibility_stage": "contract_only_not_resolved",
                    "audit_trace_expectation": "operator_visible_local_transition_required",
                    "defined_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_transition_audit_contract"],
                {
                    "audit_version": "first_reviewed_memory_transition_identity_v1",
                    "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                    "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                    "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                    "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                    "supporting_review_refs": list(aggregate["supporting_review_refs"]),
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
                    "defined_at": aggregate["last_seen_at"],
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
                    "evaluated_at": aggregate["last_seen_at"],
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
                    "capability_outcome": "unblocked_all_required",
                    "satisfaction_basis_boundary": "canonical_reviewed_memory_layer_capabilities_only",
                    "partial_state_policy": "partial_states_not_materialized",
                    "evaluated_at": aggregate["last_seen_at"],
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
                "evaluated_at": aggregate["last_seen_at"],
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
                    "defined_at": aggregate["last_seen_at"],
                },
            )
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(
                    aggregate,
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
            aggregate_without_boundary_draft = dict(aggregate)
            aggregate_without_boundary_draft.pop("reviewed_memory_boundary_draft", None)
            self.assertIsNone(
                service._resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(
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
            self.assertNotIn("reviewed_memory_capability_source_refs", aggregate)
            self.assertIn("reviewed_memory_capability_basis", aggregate)
            capability_basis = aggregate["reviewed_memory_capability_basis"]
            self.assertEqual(capability_basis["basis_version"], "same_session_reviewed_memory_capability_basis_v1")
            self.assertEqual(capability_basis["reviewed_scope"], "same_session_exact_recurrence_aggregate_only")
            self.assertEqual(capability_basis["aggregate_identity_ref"], dict(aggregate["aggregate_key"]))
            self.assertEqual(capability_basis["basis_status"], "all_required_capabilities_present")
            self.assertEqual(capability_basis["satisfaction_basis_boundary"], "canonical_reviewed_memory_layer_capabilities_only")
            self.assertEqual(
                aggregate["reviewed_memory_capability_status"]["capability_outcome"],
                "unblocked_all_required",
            )
            self.assertEqual(
                aggregate["reviewed_memory_planning_target_ref"],
                {
                    "planning_target_version": "same_session_reviewed_memory_planning_target_ref_v1",
                    "target_label": "eligible_for_reviewed_memory_draft_planning_only",
                    "target_scope": "same_session_exact_recurrence_aggregate_only",
                    "target_boundary": "reviewed_memory_draft_planning_only",
                    "defined_at": aggregate["last_seen_at"],
                },
            )
            self.assertEqual(
                aggregate["reviewed_memory_planning_target_ref"]["target_label"],
                "eligible_for_reviewed_memory_draft_planning_only",
            )
            self.assertNotIn("future_transition_target", aggregate["reviewed_memory_precondition_status"])
            self.assertNotIn("readiness_target", aggregate["reviewed_memory_unblock_contract"])
            self.assertNotIn("readiness_target", aggregate["reviewed_memory_capability_status"])
            self.assertEqual(
                {
                    (item["artifact_id"], item["source_message_id"])
                    for item in aggregate["supporting_source_message_refs"]
                },
                {
                    (first_artifact_id, first_source_message_id),
                    (second_artifact_id, second_source_message_id),
                },
            )
            self.assertEqual(
                aggregate["supporting_review_refs"],
                [
                    {
                        "artifact_id": first_artifact_id,
                        "source_message_id": first_source_message_id,
                        "candidate_id": candidate["candidate_id"],
                        "candidate_updated_at": candidate["updated_at"],
                        "review_action": "accept",
                        "review_status": "accepted",
                        "recorded_at": reviewed["candidate_review_record"]["recorded_at"],
                    }
                ],
            )
            aggregate_with_support_only = dict(aggregate)
            aggregate_with_support_only.pop("reviewed_memory_capability_basis", None)
            aggregate_with_support_only["review_queue_items"] = [
                {
                    "artifact_id": first_artifact_id,
                    "source_message_id": first_source_message_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                }
            ]
            aggregate_with_support_only["candidate_review_record"] = dict(
                aggregate["supporting_review_refs"][0]
            )
            aggregate_with_support_only["approval_backed_save_support"] = {
                "saved_note_path": str(tmp_path / "notes" / "support-only.md")
            }
            aggregate_with_support_only["historical_adjunct"] = {
                "artifact_id": first_artifact_id,
                "source_message_id": first_source_message_id,
            }
            aggregate_with_support_only["task_log_replay"] = {
                "canonical_transition_id": "transition-local-1",
                "operator_reason_or_note": "apply now",
                "emitted_at": "2026-03-28T00:07:00+00:00",
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
            support_only_status = service._build_recurrence_aggregate_reviewed_memory_capability_status(
                aggregate_with_support_only
            )
            self.assertIsNotNone(support_only_status)
            self.assertEqual(support_only_status["capability_outcome"], "blocked_all_required")
            aggregate_with_fake_handle = dict(aggregate)
            aggregate_with_fake_handle["reviewed_memory_reversible_effect_handle"] = {
                "handle_version": "first_same_session_reviewed_memory_reversible_effect_handle_v1",
                "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
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
                "defined_at": aggregate["last_seen_at"],
            }
            aggregate_with_fake_target = dict(aggregate)
            aggregate_with_fake_target["reviewed_memory_applied_effect_target"] = {
                "target_version": "first_same_session_reviewed_memory_applied_effect_target_v1",
                "target_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "target_capability_boundary": "local_effect_presence_only",
                "target_stage": "effect_present_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": aggregate["last_seen_at"],
            }
            aggregate_with_fake_source = dict(aggregate)
            aggregate_with_fake_source["reviewed_memory_local_effect_presence_record"] = {
                "source_version": "first_same_session_reviewed_memory_local_effect_presence_record_v1",
                "source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "source_capability_boundary": "local_effect_presence_only",
                "source_stage": "presence_recorded_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": aggregate["last_seen_at"],
            }
            aggregate_with_fake_event_source = dict(aggregate)
            aggregate_with_fake_event_source["reviewed_memory_local_effect_presence_event_source"] = {
                "event_source_version": "first_same_session_reviewed_memory_local_effect_presence_event_source_v1",
                "event_source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "event_capability_boundary": "local_effect_presence_only",
                "event_stage": "presence_event_recorded_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": aggregate["last_seen_at"],
            }
            aggregate_with_fake_producer = dict(aggregate)
            aggregate_with_fake_producer["reviewed_memory_local_effect_presence_event_producer"] = {
                "producer_version": "first_same_session_reviewed_memory_local_effect_presence_event_producer_v1",
                "producer_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "producer_capability_boundary": "local_effect_presence_only",
                "producer_stage": "presence_event_recorded_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": aggregate["last_seen_at"],
            }
            aggregate_with_fake_event = dict(aggregate)
            aggregate_with_fake_event["reviewed_memory_local_effect_presence_event"] = {
                "event_version": "first_same_session_reviewed_memory_local_effect_presence_event_v1",
                "event_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "event_capability_boundary": "local_effect_presence_only",
                "event_stage": "presence_observed_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": aggregate["last_seen_at"],
            }
            aggregate_with_fake_fact_source = dict(aggregate)
            aggregate_with_fake_fact_source["reviewed_memory_local_effect_presence_fact_source"] = {
                "fact_source_version": "first_same_session_reviewed_memory_local_effect_presence_fact_source_v1",
                "fact_source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "fact_capability_boundary": "local_effect_presence_only",
                "fact_stage": "presence_fact_available_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": aggregate["last_seen_at"],
            }
            aggregate_with_fake_proof_boundary = dict(aggregate)
            aggregate_with_fake_proof_boundary["reviewed_memory_local_effect_presence_proof_boundary"] = {
                "proof_boundary_version": "first_same_session_reviewed_memory_local_effect_presence_proof_boundary_v1",
                "proof_boundary_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "proof_capability_boundary": "local_effect_presence_only",
                "proof_stage": "first_presence_proved_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": aggregate["last_seen_at"],
            }
            aggregate_with_fake_proof_record = dict(aggregate)
            aggregate_with_fake_proof_record["reviewed_memory_local_effect_presence_proof_record"] = {
                "proof_record_version": "first_same_session_reviewed_memory_local_effect_presence_proof_record_v1",
                "proof_record_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "proof_capability_boundary": "local_effect_presence_only",
                "proof_record_stage": "canonical_presence_recorded_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": aggregate["last_seen_at"],
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
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "boundary_source_ref": {"ref_kind": "fake-boundary-source-ref"},
                "effect_target_kind": "applied_reviewed_memory_effect",
                "fact_capability_boundary": "local_effect_presence_only",
                "fact_stage": "presence_fact_available_local_only",
                "applied_effect_id": "fake-effect",
                "present_locally_at": aggregate["last_seen_at"],
            }
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(
                    aggregate_with_fake_proof_record,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(
                    aggregate_with_fake_proof_record,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(
                    aggregate_with_fake_proof_record,
                    source_context,
                )
            )
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(
                    aggregate_with_fake_proof_record,
                    source_context,
                )
            )
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
            aggregate_with_fake_source_refs.pop("reviewed_memory_capability_basis", None)
            aggregate_with_fake_source_refs["reviewed_memory_capability_source_refs"] = {
                "source_version": "same_session_reviewed_memory_capability_source_refs_v1",
                "source_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
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
                "evaluated_at": aggregate["last_seen_at"],
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
            fake_refs_status = service._build_recurrence_aggregate_reviewed_memory_capability_status(
                aggregate_with_fake_source_refs
            )
            self.assertIsNotNone(fake_refs_status)
            self.assertEqual(fake_refs_status["capability_outcome"], "blocked_all_required")
            aggregate_with_fake_basis = dict(aggregate)
            aggregate_with_fake_basis["reviewed_memory_capability_basis"] = {
                "basis_version": "same_session_reviewed_memory_capability_basis_v1",
                "reviewed_scope": "same_session_exact_recurrence_aggregate_only",
                "aggregate_identity_ref": dict(aggregate["aggregate_key"]),
                "supporting_source_message_refs": list(aggregate["supporting_source_message_refs"]),
                "supporting_candidate_refs": list(aggregate["supporting_candidate_refs"]),
                "supporting_review_refs": list(aggregate["supporting_review_refs"]),
                "required_preconditions": list(
                    aggregate["reviewed_memory_unblock_contract"]["required_preconditions"]
                ),
                "basis_status": "all_required_capabilities_present",
                "satisfaction_basis_boundary": "canonical_reviewed_memory_layer_capabilities_only",
                "evaluated_at": aggregate["last_seen_at"],
            }
            self.assertIsNone(
                service._build_recurrence_aggregate_reviewed_memory_capability_status(
                    aggregate_with_fake_basis
                )
            )
            self.assertEqual(
                payload["session"]["messages"][-1]["candidate_recurrence_key"]["normalized_delta_fingerprint"],
                aggregate["aggregate_key"]["normalized_delta_fingerprint"],
            )

    def test_recurrence_aggregate_candidates_do_not_materialize_from_save_support_or_historical_adjunct_only(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            corrected_source_path = tmp_path / "corrected-source.md"
            saved_only_source_path = tmp_path / "saved-only-source.md"
            corrected_note_path = tmp_path / "notes" / "corrected.md"
            saved_only_note_path = tmp_path / "notes" / "saved-only.md"
            corrected_source_path.write_text("# Demo\n\nhello world", encoding="utf-8")
            saved_only_source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            corrected = service.handle_chat(
                {
                    "session_id": "recurrence-aggregate-save-support",
                    "source_path": str(corrected_source_path),
                    "provider": "mock",
                }
            )
            corrected_source_message_id = corrected["response"]["source_message_id"]
            service.submit_correction(
                {
                    "session_id": "recurrence-aggregate-save-support",
                    "message_id": corrected_source_message_id,
                    "corrected_text": "수정본입니다.\n핵심만 남겼습니다.",
                }
            )
            bridge = service.handle_chat(
                {
                    "session_id": "recurrence-aggregate-save-support",
                    "corrected_save_message_id": corrected_source_message_id,
                    "note_path": str(corrected_note_path),
                }
            )
            service.handle_chat(
                {
                    "session_id": "recurrence-aggregate-save-support",
                    "approved_approval_id": bridge["response"]["approval"]["approval_id"],
                }
            )
            historical_only = service.submit_correction(
                {
                    "session_id": "recurrence-aggregate-save-support",
                    "message_id": corrected_source_message_id,
                    "corrected_text": "수정본입니다.\n다르게 손봤습니다.",
                }
            )

            saved_only = service.handle_chat(
                {
                    "session_id": "recurrence-aggregate-save-support",
                    "source_path": str(saved_only_source_path),
                    "save_summary": True,
                    "note_path": str(saved_only_note_path),
                    "approved": True,
                    "provider": "mock",
                }
            )

            self.assertNotIn("recurrence_aggregate_candidates", saved_only["session"])
            historical_source_message = [
                message
                for message in historical_only["session"]["messages"]
                if message.get("message_id") == corrected_source_message_id
            ][-1]
            self.assertIn("historical_save_identity_signal", historical_source_message)
            saved_only_source_message = [
                message
                for message in saved_only["session"]["messages"]
                if message.get("artifact_id") == saved_only["response"]["artifact_id"] and message.get("original_response_snapshot")
            ][-1]
            self.assertNotIn("candidate_recurrence_key", saved_only_source_message)

    def test_submit_candidate_confirmation_requires_current_session_local_candidate(self) -> None:
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

            initial = service.handle_chat(
                {
                    "session_id": "candidate-confirmation-required",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            source_message_id = initial["response"]["source_message_id"]

            with self.assertRaises(WebApiError) as context:
                service.submit_candidate_confirmation(
                    {
                        "session_id": "candidate-confirmation-required",
                        "message_id": source_message_id,
                        "candidate_id": "session-local-candidate:missing",
                        "candidate_updated_at": "2026-03-28T00:00:00+00:00",
                    }
                )

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("session-local candidate가 없습니다", str(context.exception))

    def test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "candidate-confirmation.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "candidate-confirmation-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]

            corrected = service.submit_correction(
                {
                    "session_id": "candidate-confirmation-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 A입니다.\n핵심만 남겼습니다.",
                }
            )
            corrected_source_message = [
                message
                for message in corrected["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            candidate = corrected_source_message["session_local_candidate"]
            self.assertEqual(corrected["session"]["review_queue_items"], [])
            self.assertNotIn("candidate_confirmation_record", corrected_source_message)
            self.assertNotIn("durable_candidate", corrected_source_message)

            bridge = service.handle_chat(
                {
                    "session_id": "candidate-confirmation-session",
                    "corrected_save_message_id": source_message_id,
                    "note_path": str(note_path),
                }
            )
            approval_id = bridge["response"]["approval"]["approval_id"]
            approved = service.handle_chat(
                {
                    "session_id": "candidate-confirmation-session",
                    "approved_approval_id": approval_id,
                }
            )

            approved_source_message = [
                message
                for message in approved["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertIn("session_local_candidate", approved_source_message)
            self.assertNotIn("candidate_confirmation_record", approved_source_message)
            self.assertNotIn("durable_candidate", approved_source_message)
            self.assertEqual(approved["session"]["review_queue_items"], [])
            self.assertEqual(
                approved_source_message["session_local_candidate"]["supporting_signal_refs"],
                [
                    {
                        "signal_name": "session_local_memory_signal.content_signal",
                        "relationship": "primary_basis",
                    },
                    {
                        "signal_name": "session_local_memory_signal.save_signal",
                        "relationship": "supporting_evidence",
                    },
                ],
            )

            payload = service.submit_candidate_confirmation(
                {
                    "session_id": "candidate-confirmation-session",
                    "message_id": source_message_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["artifact_id"], artifact_id)
            self.assertEqual(payload["candidate_id"], candidate["candidate_id"])
            self.assertEqual(
                payload["candidate_confirmation_record"],
                {
                    "candidate_id": candidate["candidate_id"],
                    "candidate_family": "correction_rewrite_preference",
                    "candidate_updated_at": candidate["updated_at"],
                    "artifact_id": artifact_id,
                    "source_message_id": source_message_id,
                    "confirmation_scope": "candidate_reuse",
                    "confirmation_label": "explicit_reuse_confirmation",
                    "recorded_at": payload["candidate_confirmation_record"]["recorded_at"],
                },
            )

            confirmed_source_message = [
                message
                for message in payload["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertEqual(
                confirmed_source_message["candidate_confirmation_record"],
                payload["candidate_confirmation_record"],
            )
            self.assertEqual(
                confirmed_source_message["session_local_candidate"]["supporting_signal_refs"],
                approved_source_message["session_local_candidate"]["supporting_signal_refs"],
            )
            self.assertNotIn("has_explicit_confirmation", confirmed_source_message["session_local_candidate"])
            self.assertNotIn("promotion_basis", confirmed_source_message["session_local_candidate"])
            self.assertNotIn("promotion_eligibility", confirmed_source_message["session_local_candidate"])
            self.assertEqual(
                confirmed_source_message["durable_candidate"],
                {
                    "candidate_id": candidate["candidate_id"],
                    "candidate_scope": "durable_candidate",
                    "candidate_family": "correction_rewrite_preference",
                    "statement": "explicit rewrite correction recorded for this grounded brief",
                    "supporting_artifact_ids": [artifact_id],
                    "supporting_source_message_ids": [source_message_id],
                    "supporting_signal_refs": approved_source_message["session_local_candidate"]["supporting_signal_refs"],
                    "supporting_confirmation_refs": [
                        {
                            "artifact_id": artifact_id,
                            "source_message_id": source_message_id,
                            "candidate_id": candidate["candidate_id"],
                            "candidate_updated_at": candidate["updated_at"],
                            "confirmation_label": "explicit_reuse_confirmation",
                            "recorded_at": payload["candidate_confirmation_record"]["recorded_at"],
                        }
                    ],
                    "evidence_strength": "explicit_single_artifact",
                    "has_explicit_confirmation": True,
                    "promotion_basis": "explicit_confirmation",
                    "promotion_eligibility": "eligible_for_review",
                    "created_at": payload["candidate_confirmation_record"]["recorded_at"],
                    "updated_at": payload["candidate_confirmation_record"]["recorded_at"],
                },
            )
            self.assertEqual(
                payload["session"]["review_queue_items"],
                [
                    {
                        "candidate_id": candidate["candidate_id"],
                        "candidate_family": "correction_rewrite_preference",
                        "statement": "explicit rewrite correction recorded for this grounded brief",
                        "promotion_basis": "explicit_confirmation",
                        "promotion_eligibility": "eligible_for_review",
                        "artifact_id": artifact_id,
                        "source_message_id": source_message_id,
                        "supporting_artifact_ids": [artifact_id],
                        "supporting_source_message_ids": [source_message_id],
                        "supporting_signal_refs": approved_source_message["session_local_candidate"]["supporting_signal_refs"],
                        "supporting_confirmation_refs": [
                            {
                                "artifact_id": artifact_id,
                                "source_message_id": source_message_id,
                                "candidate_id": candidate["candidate_id"],
                                "candidate_updated_at": candidate["updated_at"],
                                "confirmation_label": "explicit_reuse_confirmation",
                                "recorded_at": payload["candidate_confirmation_record"]["recorded_at"],
                            }
                        ],
                        "created_at": payload["candidate_confirmation_record"]["recorded_at"],
                        "updated_at": payload["candidate_confirmation_record"]["recorded_at"],
                    }
                ],
            )

            corrected_again = service.submit_correction(
                {
                    "session_id": "candidate-confirmation-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 B입니다.\n다시 손봤습니다.",
                }
            )
            latest_source_message = [
                message
                for message in corrected_again["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertNotIn("candidate_confirmation_record", latest_source_message)
            self.assertIn("session_local_candidate", latest_source_message)
            self.assertNotIn("durable_candidate", latest_source_message)
            self.assertEqual(corrected_again["session"]["review_queue_items"], [])

            log_text = (tmp_path / "task_log.jsonl").read_text(encoding="utf-8")
            self.assertIn("candidate_confirmation_recorded", log_text)
            self.assertIn("explicit_reuse_confirmation", log_text)
            self.assertIn(candidate["candidate_id"], log_text)

    def test_submit_candidate_review_requires_current_durable_candidate(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "review-requires-durable.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "candidate-review-required",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            source_message_id = initial["response"]["source_message_id"]

            corrected = service.submit_correction(
                {
                    "session_id": "candidate-review-required",
                    "message_id": source_message_id,
                    "corrected_text": "수정본입니다.\n핵심만 남겼습니다.",
                }
            )
            candidate = [
                message
                for message in corrected["session"]["messages"]
                if message.get("message_id") == source_message_id
            ][-1]["session_local_candidate"]

            bridge = service.handle_chat(
                {
                    "session_id": "candidate-review-required",
                    "corrected_save_message_id": source_message_id,
                    "note_path": str(note_path),
                }
            )
            approval_id = bridge["response"]["approval"]["approval_id"]
            approved = service.handle_chat(
                {
                    "session_id": "candidate-review-required",
                    "approved_approval_id": approval_id,
                }
            )
            self.assertEqual(approved["session"]["review_queue_items"], [])

            with self.assertRaises(WebApiError) as context:
                service.submit_candidate_review(
                    {
                        "session_id": "candidate-review-required",
                        "message_id": source_message_id,
                        "candidate_id": candidate["candidate_id"],
                        "candidate_updated_at": candidate["updated_at"],
                        "review_action": "accept",
                    }
                )

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("durable candidate가 없습니다", str(context.exception))

    def test_submit_candidate_review_accept_records_source_message_trace_and_removes_pending_queue_item(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "candidate-review.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "candidate-review-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]

            corrected = service.submit_correction(
                {
                    "session_id": "candidate-review-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 A입니다.\n핵심만 남겼습니다.",
                }
            )
            candidate = [
                message
                for message in corrected["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]["session_local_candidate"]

            bridge = service.handle_chat(
                {
                    "session_id": "candidate-review-session",
                    "corrected_save_message_id": source_message_id,
                    "note_path": str(note_path),
                }
            )
            approval_id = bridge["response"]["approval"]["approval_id"]
            approved = service.handle_chat(
                {
                    "session_id": "candidate-review-session",
                    "approved_approval_id": approval_id,
                }
            )
            approved_source_message = [
                message
                for message in approved["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]

            confirmed = service.submit_candidate_confirmation(
                {
                    "session_id": "candidate-review-session",
                    "message_id": source_message_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                }
            )
            confirmed_source_message = [
                message
                for message in confirmed["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            confirmed_recurrence_key = confirmed_source_message["candidate_recurrence_key"]
            self.assertEqual(len(confirmed["session"]["review_queue_items"]), 1)

            payload = service.submit_candidate_review(
                {
                    "session_id": "candidate-review-session",
                    "message_id": source_message_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                    "review_action": "accept",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["artifact_id"], artifact_id)
            self.assertEqual(payload["candidate_id"], candidate["candidate_id"])
            self.assertEqual(
                payload["candidate_review_record"],
                {
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                    "artifact_id": artifact_id,
                    "source_message_id": source_message_id,
                    "review_scope": "source_message_candidate_review",
                    "review_action": "accept",
                    "review_status": "accepted",
                    "recorded_at": payload["candidate_review_record"]["recorded_at"],
                },
            )

            reviewed_source_message = [
                message
                for message in payload["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertEqual(reviewed_source_message["candidate_recurrence_key"], confirmed_recurrence_key)
            self.assertEqual(reviewed_source_message["candidate_review_record"], payload["candidate_review_record"])
            self.assertEqual(
                reviewed_source_message["candidate_confirmation_record"],
                confirmed_source_message["candidate_confirmation_record"],
            )
            self.assertEqual(
                reviewed_source_message["session_local_candidate"]["supporting_signal_refs"],
                approved_source_message["session_local_candidate"]["supporting_signal_refs"],
            )
            self.assertEqual(
                reviewed_source_message["durable_candidate"],
                confirmed_source_message["durable_candidate"],
            )
            self.assertEqual(payload["session"]["review_queue_items"], [])

            corrected_again = service.submit_correction(
                {
                    "session_id": "candidate-review-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 B입니다.\n다시 손봤습니다.",
                }
            )
            latest_source_message = [
                message
                for message in corrected_again["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertIn("candidate_recurrence_key", latest_source_message)
            self.assertNotIn("candidate_review_record", latest_source_message)
            self.assertNotIn("candidate_confirmation_record", latest_source_message)
            self.assertNotIn("durable_candidate", latest_source_message)
            self.assertIn("session_local_candidate", latest_source_message)
            self.assertNotEqual(
                latest_source_message["candidate_recurrence_key"]["normalized_delta_fingerprint"],
                confirmed_recurrence_key["normalized_delta_fingerprint"],
            )
            self.assertEqual(corrected_again["session"]["review_queue_items"], [])

            log_text = (tmp_path / "task_log.jsonl").read_text(encoding="utf-8")
            self.assertIn("candidate_review_recorded", log_text)
            self.assertIn("\"review_action\": \"accept\"", log_text)
            self.assertIn("\"review_status\": \"accepted\"", log_text)
            self.assertIn(candidate["candidate_id"], log_text)

    def test_durable_candidate_requires_exact_current_candidate_confirmation_join(self) -> None:
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

            initial = service.handle_chat(
                {
                    "session_id": "durable-candidate-join-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]

            corrected = service.submit_correction(
                {
                    "session_id": "durable-candidate-join-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본입니다.\n핵심만 남겼습니다.",
                }
            )
            corrected_source_message = [
                message
                for message in corrected["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            candidate = corrected_source_message["session_local_candidate"]

            service.session_store.update_message(
                "durable-candidate-join-session",
                source_message_id,
                {
                    "candidate_confirmation_record": {
                        "candidate_id": candidate["candidate_id"],
                        "candidate_family": "correction_rewrite_preference",
                        "candidate_updated_at": "2026-03-28T00:00:00+00:00",
                        "artifact_id": artifact_id,
                        "source_message_id": source_message_id,
                        "confirmation_scope": "candidate_reuse",
                        "confirmation_label": "explicit_reuse_confirmation",
                    }
                },
            )

            payload = service.get_session_payload("durable-candidate-join-session")
            source_message = [
                message
                for message in payload["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertIn("session_local_candidate", source_message)
            self.assertNotIn("candidate_confirmation_record", source_message)
            self.assertNotIn("durable_candidate", source_message)
            self.assertEqual(payload["session"]["review_queue_items"], [])

    def test_candidate_review_record_requires_exact_current_candidate_join(self) -> None:
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

            initial = service.handle_chat(
                {
                    "session_id": "candidate-review-join-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]

            corrected = service.submit_correction(
                {
                    "session_id": "candidate-review-join-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본입니다.\n핵심만 남겼습니다.",
                }
            )
            corrected_source_message = [
                message
                for message in corrected["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            candidate = corrected_source_message["session_local_candidate"]

            confirmed = service.submit_candidate_confirmation(
                {
                    "session_id": "candidate-review-join-session",
                    "message_id": source_message_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                }
            )
            self.assertEqual(len(confirmed["session"]["review_queue_items"]), 1)

            service.session_store.update_message(
                "candidate-review-join-session",
                source_message_id,
                {
                    "candidate_review_record": {
                        "candidate_id": candidate["candidate_id"],
                        "candidate_updated_at": "2026-03-28T00:00:00+00:00",
                        "artifact_id": artifact_id,
                        "source_message_id": source_message_id,
                        "review_scope": "source_message_candidate_review",
                        "review_action": "accept",
                        "review_status": "accepted",
                    }
                },
            )

            payload = service.get_session_payload("candidate-review-join-session")
            source_message = [
                message
                for message in payload["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertIn("durable_candidate", source_message)
            self.assertNotIn("candidate_review_record", source_message)
            self.assertEqual(len(payload["session"]["review_queue_items"]), 1)

    def test_session_local_candidate_omits_same_text_pair_even_if_corrected_outcome_exists(self) -> None:
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

            stored_source = service.session_store.append_message(
                "session-local-candidate-same-text",
                {
                    "role": "assistant",
                    "text": "원본 요약입니다.",
                    "status": "answer",
                    "artifact_id": "artifact-same-text",
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
            service.session_store.update_message(
                "session-local-candidate-same-text",
                stored_source["message_id"],
                {
                    "corrected_text": "원본 요약입니다.",
                    "corrected_outcome": {
                        "outcome": "corrected",
                        "recorded_at": "2026-03-28T00:00:00+00:00",
                        "artifact_id": "artifact-same-text",
                        "source_message_id": stored_source["message_id"],
                    },
                },
            )

            payload = service.get_session_payload("session-local-candidate-same-text")
            source_message = [
                message
                for message in payload["session"]["messages"]
                if message.get("artifact_id") == "artifact-same-text" and message.get("original_response_snapshot")
            ][-1]
            self.assertEqual(
                source_message["session_local_memory_signal"]["content_signal"]["latest_corrected_outcome"]["outcome"],
                "corrected",
            )
            self.assertTrue(source_message["session_local_memory_signal"]["content_signal"]["has_corrected_text"])
            self.assertNotIn("session_local_candidate", source_message)
            self.assertNotIn("candidate_recurrence_key", source_message)

    def test_session_local_candidate_omits_accepted_as_is_only_save_path(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "accepted-as-is-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "session-local-candidate-accepted-as-is",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "note_path": str(note_path),
                    "provider": "mock",
                }
            )
            artifact_id = initial["response"]["artifact_id"]
            approval_id = initial["response"]["approval"]["approval_id"]

            approved = service.handle_chat(
                {
                    "session_id": "session-local-candidate-accepted-as-is",
                    "approved_approval_id": approval_id,
                }
            )

            source_message = [
                message
                for message in approved["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertEqual(
                source_message["session_local_memory_signal"]["content_signal"]["latest_corrected_outcome"]["outcome"],
                "accepted_as_is",
            )
            self.assertNotIn("session_local_candidate", source_message)
            self.assertNotIn("candidate_recurrence_key", source_message)

    def test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal(self) -> None:
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

            initial = service.handle_chat(
                {
                    "session_id": "superseded-reject-session",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )

            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]

            rejected = service.submit_content_verdict(
                {
                    "session_id": "superseded-reject-session",
                    "message_id": source_message_id,
                    "content_verdict": "rejected",
                }
            )
            rejected_source_message = [
                message
                for message in rejected["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertEqual(rejected_source_message["corrected_outcome"]["outcome"], "rejected")
            self.assertNotIn("superseded_reject_signal", rejected_source_message)

            noted = service.submit_content_reason_note(
                {
                    "session_id": "superseded-reject-session",
                    "message_id": source_message_id,
                    "reason_note": "초기 결론이 문서 문맥과 다릅니다.",
                }
            )
            self.assertTrue(noted["ok"])

            corrected = service.submit_correction(
                {
                    "session_id": "superseded-reject-session",
                    "message_id": source_message_id,
                    "corrected_text": "수정본입니다.\n핵심만 남겼습니다.",
                }
            )

            source_message = [
                message
                for message in corrected["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            current_signal = source_message["session_local_memory_signal"]
            self.assertEqual(current_signal["content_signal"]["latest_corrected_outcome"]["outcome"], "corrected")
            self.assertTrue(current_signal["content_signal"]["has_corrected_text"])
            self.assertNotIn("content_reason_record", current_signal["content_signal"])

            superseded_signal = source_message["superseded_reject_signal"]
            self.assertEqual(superseded_signal["artifact_id"], artifact_id)
            self.assertEqual(superseded_signal["source_message_id"], source_message_id)
            self.assertEqual(superseded_signal["replay_source"], "task_log_audit")
            self.assertEqual(superseded_signal["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(
                superseded_signal["corrected_outcome"]["recorded_at"],
                rejected["corrected_outcome"]["recorded_at"],
            )
            self.assertEqual(
                superseded_signal["content_reason_record"]["reason_scope"],
                "content_reject",
            )
            self.assertEqual(
                superseded_signal["content_reason_record"]["reason_label"],
                "explicit_content_rejection",
            )
            self.assertEqual(
                superseded_signal["content_reason_record"]["reason_note"],
                "초기 결론이 문서 문맥과 다릅니다.",
            )
            self.assertEqual(
                superseded_signal["content_reason_record"]["recorded_at"],
                noted["content_reason_record"]["recorded_at"],
            )

    def test_superseded_reject_signal_omits_ambiguous_note_association(self) -> None:
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

            initial = service.handle_chat(
                {
                    "session_id": "superseded-reject-ambiguous-note",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )

            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]

            rejected = service.submit_content_verdict(
                {
                    "session_id": "superseded-reject-ambiguous-note",
                    "message_id": source_message_id,
                    "content_verdict": "rejected",
                }
            )
            self.assertTrue(rejected["ok"])

            corrected = service.submit_correction(
                {
                    "session_id": "superseded-reject-ambiguous-note",
                    "message_id": source_message_id,
                    "corrected_text": "수정본입니다.\n다시 정리했습니다.",
                }
            )
            self.assertTrue(corrected["ok"])

            service.task_logger.log(
                session_id="superseded-reject-ambiguous-note",
                action="content_reason_note_recorded",
                detail={
                    "message_id": source_message_id,
                    "artifact_id": artifact_id,
                    "artifact_kind": "grounded_brief",
                    "source_message_id": source_message_id,
                    "reason_scope": "approval_reject",
                    "reason_label": "explicit_rejection",
                    "reason_note": "이 메모는 붙으면 안 됩니다.",
                    "content_reason_record": {
                        "reason_scope": "approval_reject",
                        "reason_label": "explicit_rejection",
                        "reason_note": "이 메모는 붙으면 안 됩니다.",
                        "recorded_at": "2026-03-27T00:00:00+00:00",
                        "artifact_id": artifact_id,
                        "artifact_kind": "grounded_brief",
                        "source_message_id": source_message_id,
                    },
                },
            )

            payload = service.get_session_payload("superseded-reject-ambiguous-note")
            source_message = [
                message
                for message in payload["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]

            current_signal = source_message["session_local_memory_signal"]
            self.assertEqual(current_signal["content_signal"]["latest_corrected_outcome"]["outcome"], "corrected")
            self.assertNotIn("content_reason_record", current_signal["content_signal"])

            superseded_signal = source_message["superseded_reject_signal"]
            self.assertEqual(superseded_signal["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(
                superseded_signal["corrected_outcome"]["recorded_at"],
                rejected["corrected_outcome"]["recorded_at"],
            )
            self.assertEqual(
                superseded_signal["content_reason_record"]["reason_scope"],
                "content_reject",
            )
            self.assertEqual(
                superseded_signal["content_reason_record"]["reason_label"],
                "explicit_content_rejection",
            )
            self.assertIsNone(superseded_signal["content_reason_record"]["reason_note"])

    def test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "historical-save-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "historical-save-signal",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "note_path": str(note_path),
                    "provider": "mock",
                }
            )

            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]
            approval_id = initial["response"]["approval"]["approval_id"]

            approved = service.handle_chat(
                {
                    "session_id": "historical-save-signal",
                    "approved_approval_id": approval_id,
                }
            )
            approved_source_message = [
                message
                for message in approved["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            self.assertEqual(
                approved_source_message["session_local_memory_signal"]["save_signal"]["latest_approval_id"],
                approval_id,
            )
            self.assertNotIn("historical_save_identity_signal", approved_source_message)

            corrected = service.submit_correction(
                {
                    "session_id": "historical-save-signal",
                    "message_id": source_message_id,
                    "corrected_text": "저장 뒤에 다시 수정했습니다.\n현재 상태는 아직 미저장입니다.",
                }
            )

            source_message = [
                message
                for message in corrected["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            current_save_signal = source_message["session_local_memory_signal"]["save_signal"]
            self.assertEqual(current_save_signal["latest_save_content_source"], "original_draft")
            self.assertEqual(current_save_signal["latest_saved_note_path"], str(note_path))
            self.assertNotIn("latest_approval_id", current_save_signal)

            historical_signal = source_message["historical_save_identity_signal"]
            self.assertEqual(historical_signal["artifact_id"], artifact_id)
            self.assertEqual(historical_signal["source_message_id"], source_message_id)
            self.assertEqual(historical_signal["replay_source"], "task_log_audit")
            self.assertEqual(historical_signal["approval_id"], approval_id)
            self.assertEqual(historical_signal["save_content_source"], "original_draft")
            self.assertEqual(historical_signal["saved_note_path"], str(note_path))
            self.assertTrue(historical_signal["recorded_at"])

    def test_historical_save_identity_signal_requires_same_anchor_write_note_not_approval_granted_only(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "historical-save-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "historical-save-approval-only",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            artifact_id = initial["response"]["artifact_id"]
            source_message_id = initial["response"]["source_message_id"]

            service.session_store.record_corrected_outcome_for_artifact(
                "historical-save-approval-only",
                artifact_id=artifact_id,
                outcome="accepted_as_is",
                approval_id="approval-manual-only",
                saved_note_path=str(note_path),
            )
            service.session_store.append_message(
                "historical-save-approval-only",
                {
                    "role": "assistant",
                    "text": f"요약 노트를 {note_path}에 저장했습니다.",
                    "status": "saved",
                    "artifact_id": artifact_id,
                    "artifact_kind": "grounded_brief",
                    "source_message_id": source_message_id,
                    "saved_note_path": str(note_path),
                    "save_content_source": "original_draft",
                },
            )
            service.submit_correction(
                {
                    "session_id": "historical-save-approval-only",
                    "message_id": source_message_id,
                    "corrected_text": "지금은 수정만 남았습니다.\n저장은 다시 하지 않았습니다.",
                }
            )
            service.task_logger.log(
                session_id="historical-save-approval-only",
                action="approval_granted",
                detail={
                    "approval_id": "approval-manual-only",
                    "kind": "save_note",
                    "requested_path": str(note_path),
                    "artifact_id": artifact_id,
                    "source_message_id": source_message_id,
                    "save_content_source": "original_draft",
                },
            )

            payload = service.get_session_payload("historical-save-approval-only")
            source_message = [
                message
                for message in payload["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ][-1]
            current_save_signal = source_message["session_local_memory_signal"]["save_signal"]
            self.assertEqual(current_save_signal["latest_save_content_source"], "original_draft")
            self.assertEqual(current_save_signal["latest_saved_note_path"], str(note_path))
            self.assertNotIn("latest_approval_id", current_save_signal)
            self.assertNotIn("historical_save_identity_signal", source_message)

    def test_submit_correction_after_corrected_save_late_reject_preserves_saved_snapshot_history(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "source-summary.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            initial = service.handle_chat(
                {
                    "session_id": "corrected-save-long-history",
                    "source_path": str(source_path),
                    "provider": "mock",
                }
            )
            source_message_id = initial["response"]["source_message_id"]
            artifact_id = initial["response"]["artifact_id"]

            service.submit_correction(
                {
                    "session_id": "corrected-save-long-history",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 A입니다.\n핵심만 남겼습니다.",
                }
            )

            bridge = service.handle_chat(
                {
                    "session_id": "corrected-save-long-history",
                    "corrected_save_message_id": source_message_id,
                }
            )
            approval_id = bridge["response"]["approval"]["approval_id"]

            approved = service.handle_chat(
                {
                    "session_id": "corrected-save-long-history",
                    "approved_approval_id": approval_id,
                }
            )

            self.assertTrue(approved["ok"])
            self.assertEqual(approved["response"]["status"], "saved")
            self.assertEqual(approved["response"]["save_content_source"], "corrected_text")
            self.assertTrue(note_path.exists())
            self.assertEqual(note_path.read_text(encoding="utf-8"), "수정본 A입니다.\n핵심만 남겼습니다.")

            rejected = service.submit_content_verdict(
                {
                    "session_id": "corrected-save-long-history",
                    "message_id": source_message_id,
                    "content_verdict": "rejected",
                }
            )

            self.assertTrue(rejected["ok"])
            self.assertEqual(rejected["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(rejected["corrected_outcome"]["source_message_id"], source_message_id)
            self.assertEqual(note_path.read_text(encoding="utf-8"), "수정본 A입니다.\n핵심만 남겼습니다.")

            noted = service.submit_content_reason_note(
                {
                    "session_id": "corrected-save-long-history",
                    "message_id": source_message_id,
                    "reason_note": "초기 수정본의 결론이 여전히 과장되어 있습니다.",
                }
            )

            self.assertTrue(noted["ok"])
            self.assertEqual(
                noted["content_reason_record"]["reason_note"],
                "초기 수정본의 결론이 여전히 과장되어 있습니다.",
            )

            corrected = service.submit_correction(
                {
                    "session_id": "corrected-save-long-history",
                    "message_id": source_message_id,
                    "corrected_text": "수정본 B입니다.\n다시 손봤습니다.",
                }
            )

            self.assertTrue(corrected["ok"])
            self.assertEqual(corrected["message_id"], source_message_id)
            self.assertEqual(corrected["corrected_text"], "수정본 B입니다.\n다시 손봤습니다.")
            self.assertEqual(corrected["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(note_path.read_text(encoding="utf-8"), "수정본 A입니다.\n핵심만 남겼습니다.")

            session_messages = corrected["session"]["messages"]
            source_messages = [
                message
                for message in session_messages
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ]
            self.assertTrue(source_messages)
            source_message = source_messages[-1]
            self.assertEqual(source_message["corrected_text"], "수정본 B입니다.\n다시 손봤습니다.")
            self.assertEqual(source_message["corrected_outcome"]["outcome"], "corrected")
            self.assertEqual(source_message["corrected_outcome"]["source_message_id"], source_message_id)
            self.assertIsNone(source_message["corrected_outcome"]["approval_id"])
            self.assertIsNone(source_message["corrected_outcome"]["saved_note_path"])
            self.assertNotIn("content_reason_record", source_message)

            saved_messages = [
                message
                for message in session_messages
                if message.get("saved_note_path") == str(note_path)
            ]
            self.assertTrue(saved_messages)
            self.assertEqual(saved_messages[-1]["artifact_id"], artifact_id)
            self.assertEqual(saved_messages[-1]["source_message_id"], source_message_id)
            self.assertEqual(saved_messages[-1]["save_content_source"], "corrected_text")

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
            self.assertTrue(str(payload["response"]["artifact_id"]).startswith("artifact-"))
            self.assertEqual(payload["response"]["artifact_kind"], "grounded_brief")
            self.assertIn("[모의 요약]", payload["response"]["text"])
            self.assertGreater(len(payload["response"]["follow_up_suggestions"]), 0)
            self.assertEqual(payload["response"]["active_context"]["label"], "source.md")
            self.assertEqual(payload["response"]["response_origin"]["provider"], "mock")
            self.assertEqual(payload["response"]["response_origin"]["badge"], "MOCK")
            self.assertIn("모의 데모 응답", payload["response"]["response_origin"]["label"])
            self.assertGreaterEqual(len(payload["response"]["evidence"]), 1)
            self.assertEqual(payload["response"]["evidence"][0]["source_name"], "source.md")
            snapshot = payload["response"]["original_response_snapshot"]
            self.assertEqual(snapshot["artifact_id"], payload["response"]["artifact_id"])
            self.assertEqual(snapshot["artifact_kind"], "grounded_brief")
            self.assertEqual(snapshot["draft_text"], payload["response"]["text"])
            self.assertEqual(snapshot["source_paths"], [str(source_path)])
            self.assertEqual(snapshot["response_origin"]["provider"], "mock")
            self.assertEqual(snapshot["summary_chunks_snapshot"], payload["response"]["summary_chunks"])
            self.assertEqual(snapshot["evidence_snapshot"], payload["response"]["evidence"])
            self.assertEqual(payload["session"]["session_id"], "web-session")
            self.assertGreaterEqual(len(payload["session"]["messages"]), 2)
            self.assertEqual(payload["session"]["messages"][-1]["artifact_id"], payload["response"]["artifact_id"])
            self.assertEqual(payload["session"]["messages"][-1]["artifact_kind"], "grounded_brief")
            self.assertEqual(payload["session"]["messages"][-1]["response_origin"]["provider"], "mock")
            self.assertGreaterEqual(len(payload["session"]["messages"][-1]["evidence"]), 1)
            signal = payload["session"]["messages"][-1]["session_local_memory_signal"]
            self.assertEqual(signal["signal_scope"], "session_local")
            self.assertEqual(signal["artifact_id"], payload["response"]["artifact_id"])
            self.assertEqual(signal["source_message_id"], payload["response"]["source_message_id"])
            self.assertIsNone(signal["content_signal"]["latest_corrected_outcome"])
            self.assertFalse(signal["content_signal"]["has_corrected_text"])
            self.assertNotIn("approval_signal", signal)
            self.assertNotIn("save_signal", signal)
            self.assertEqual(
                payload["session"]["messages"][-1]["original_response_snapshot"]["artifact_id"],
                payload["response"]["artifact_id"],
            )
            self.assertEqual(
                payload["session"]["messages"][-1]["original_response_snapshot"]["response_origin"]["provider"],
                "mock",
            )
            self.assertEqual(payload["runtime_status"]["provider"], "mock")

    def test_get_session_payload_backfills_original_response_snapshot_for_legacy_grounded_brief(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            settings = AppSettings(
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=str(Path(tmp_dir) / "notes"),
                web_search_history_dir=str(Path(tmp_dir) / "web-search"),
            )
            service = WebAppService(settings=settings)

            service.session_store.append_message(
                "legacy-snapshot-session",
                {
                    "role": "assistant",
                    "text": "[mock-summary] legacy brief",
                    "status": "answer",
                    "artifact_id": "artifact-legacy",
                    "artifact_kind": "grounded_brief",
                    "selected_source_paths": ["/tmp/source.md"],
                    "response_origin": {
                        "provider": "mock",
                        "badge": "MOCK",
                        "label": "모의 데모 응답",
                        "model": "demo",
                        "kind": "assistant",
                    },
                    "summary_chunks": [
                        {
                            "chunk_id": "chunk-1",
                            "chunk_index": 1,
                            "total_chunks": 1,
                            "source_path": "/tmp/source.md",
                            "source_name": "source.md",
                            "selected_line": "legacy line",
                        }
                    ],
                    "evidence": [
                        {
                            "label": "문서 핵심",
                            "source_name": "source.md",
                            "source_path": "/tmp/source.md",
                            "snippet": "legacy evidence",
                        }
                    ],
                },
            )

            payload = service.get_session_payload("legacy-snapshot-session")

            snapshot = payload["session"]["messages"][-1]["original_response_snapshot"]
            self.assertEqual(snapshot["artifact_id"], "artifact-legacy")
            self.assertEqual(snapshot["artifact_kind"], "grounded_brief")
            self.assertEqual(snapshot["draft_text"], "[모의 요약] legacy brief")
            self.assertEqual(snapshot["source_paths"], ["/tmp/source.md"])
            self.assertEqual(snapshot["response_origin"]["provider"], "mock")
            self.assertEqual(len(snapshot["summary_chunks_snapshot"]), 1)
            self.assertEqual(len(snapshot["evidence_snapshot"]), 1)

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
            self.assertIn("웹 최신 확인: 오늘 날씨", payload["response"]["text"])
            self.assertEqual(payload["response"]["response_origin"]["answer_mode"], "latest_update")
            self.assertGreaterEqual(len(payload["response"]["response_origin"]["source_roles"]), 1)
            self.assertTrue(payload["response"]["response_origin"]["verification_label"])
            self.assertIn("source_role", payload["response"]["evidence"][0])

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
            self.assertIn("웹 최신 확인: 아이유 최신 소식", payload["response"]["text"])
            self.assertEqual(payload["response"]["response_origin"]["answer_mode"], "latest_update")
            self.assertTrue(payload["response"]["response_origin"]["verification_label"])

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
            self.assertIn("웹 최신 확인: 서울 날씨", payload["response"]["text"])
            self.assertIn("읽을 수 있었던 원문 1건", payload["response"]["text"])
            self.assertTrue(payload["response"]["web_search_record_path"])
            self.assertTrue(Path(payload["response"]["web_search_record_path"]).exists())
            self.assertEqual(len(payload["session"]["web_search_history"]), 1)
            self.assertEqual(payload["session"]["web_search_history"][0]["query"], "서울 날씨")
            self.assertEqual(payload["session"]["web_search_history"][0]["answer_mode"], "latest_update")
            self.assertTrue(payload["session"]["web_search_history"][0]["verification_label"])
            self.assertGreaterEqual(len(payload["session"]["web_search_history"][0]["source_roles"]), 1)
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

    def test_handle_chat_entity_web_search_serializes_claim_coverage(self) -> None:
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
                            title="붉은사막 - 나무위키",
                            url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
                            snippet="붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
                        ),
                    ]
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            payload = service.handle_chat(
                {
                    "session_id": "claim-coverage-web-session",
                    "user_text": "붉은사막에 대해 알려줘",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["response_origin"]["provider"], "web")
            self.assertGreaterEqual(len(payload["response"]["claim_coverage"]), 5)
            self.assertEqual(payload["session"]["web_search_history"][0]["answer_mode"], "entity_card")
            self.assertEqual(payload["session"]["web_search_history"][0]["claim_coverage_summary"]["weak"], 3)
            self.assertEqual(payload["session"]["web_search_history"][0]["claim_coverage_summary"]["missing"], 2)
            coverage_by_slot = {
                str(item.get("slot") or ""): dict(item)
                for item in payload["response"]["claim_coverage"]
                if isinstance(item, dict)
            }
            self.assertEqual(coverage_by_slot["개발"]["status"], "weak")
            self.assertEqual(coverage_by_slot["개발"]["rendered_as"], "uncertain")
            self.assertIn("붉은사막 서비스 공식 검색해봐", payload["response"]["follow_up_suggestions"])
            self.assertIn("붉은사막 공식 플랫폼 검색해봐", payload["response"]["follow_up_suggestions"])
            self.assertEqual(payload["session"]["messages"][-1]["claim_coverage"][0]["slot"], "개발")
            self.assertIn(
                "붉은사막 서비스 공식 검색해봐",
                payload["session"]["active_context"]["suggested_prompts"],
            )

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

    def test_handle_chat_entity_reinvestigation_serializes_claim_progress(self) -> None:
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
                ),
                "write_note": WriteNoteTool(allowed_roots=[str(tmp_path), str(tmp_path / "notes")]),
            }

            first = service.handle_chat(
                {
                    "session_id": "entity-progress-web-session",
                    "user_text": "붉은사막에 대해 알려줘",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )
            self.assertTrue(first["ok"])
            self.assertEqual(first["response"]["response_origin"]["answer_mode"], "entity_card")
            self.assertEqual(first["response"]["claim_coverage_progress_summary"], "")

            second = service.handle_chat(
                {
                    "session_id": "entity-progress-web-session",
                    "user_text": "붉은사막 공식 플랫폼 검색해봐",
                    "provider": "mock",
                    "web_search_permission": "enabled",
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["response_origin"]["provider"], "web")
            self.assertEqual(second["response"]["response_origin"]["answer_mode"], "entity_card")
            self.assertIn("이용 형태", second["response"]["claim_coverage_progress_summary"])
            self.assertIn("단일 출처 상태", second["response"]["claim_coverage_progress_summary"])
            self.assertIn("웹 검색 요약: 붉은사막", second["response"]["text"])
            coverage_by_slot = {
                str(item.get("slot") or ""): dict(item)
                for item in second["response"]["claim_coverage"]
                if isinstance(item, dict)
            }
            self.assertEqual(coverage_by_slot["이용 형태"]["progress_state"], "unchanged")
            self.assertEqual(coverage_by_slot["이용 형태"]["progress_label"], "유지")
            self.assertTrue(coverage_by_slot["이용 형태"]["is_focus_slot"])
            self.assertIn(
                "이용 형태",
                second["session"]["messages"][-1]["claim_coverage_progress_summary"],
            )
            self.assertIn(
                "이용 형태",
                second["session"]["active_context"]["claim_coverage_progress_summary"],
            )

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
            self.assertTrue(str(payload["response"]["artifact_id"]).startswith("artifact-"))
            self.assertEqual(payload["response"]["artifact_kind"], "grounded_brief")
            self.assertEqual(payload["response"]["approval"]["artifact_id"], payload["response"]["artifact_id"])
            self.assertEqual(
                payload["response"]["source_message_id"],
                payload["response"]["approval"]["source_message_id"],
            )
            self.assertEqual(payload["response"]["approval"]["save_content_source"], "original_draft")
            self.assertGreater(len(payload["response"]["follow_up_suggestions"]), 0)
            self.assertEqual(len(payload["session"]["pending_approvals"]), 1)
            last_message = payload["session"]["messages"][-1]
            self.assertEqual(last_message["approval_id"], payload["response"]["approval"]["approval_id"])
            self.assertEqual(last_message["artifact_id"], payload["response"]["artifact_id"])
            self.assertEqual(
                payload["session"]["pending_approvals"][0]["requested_path"],
                payload["response"]["approval"]["requested_path"],
            )
            self.assertEqual(
                payload["session"]["pending_approvals"][0]["artifact_id"],
                payload["response"]["artifact_id"],
            )
            self.assertEqual(
                payload["session"]["pending_approvals"][0]["source_message_id"],
                payload["response"]["source_message_id"],
            )
            self.assertEqual(
                payload["session"]["pending_approvals"][0]["save_content_source"],
                "original_draft",
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
            artifact_id = first["response"]["artifact_id"]
            source_message_id = first["response"]["approval"]["source_message_id"]
            second = service.handle_chat(
                {
                    "session_id": "approval-session",
                    "approved_approval_id": approval_id,
                }
            )

            self.assertTrue(second["ok"])
            self.assertEqual(second["response"]["status"], "saved")
            self.assertEqual(second["response"]["artifact_id"], artifact_id)
            self.assertEqual(second["response"]["artifact_kind"], "grounded_brief")
            self.assertEqual(second["response"]["source_message_id"], source_message_id)
            self.assertEqual(second["response"]["save_content_source"], "original_draft")
            self.assertEqual(second["response"]["saved_note_path"], str(note_path))
            self.assertEqual(second["response"]["response_origin"]["provider"], "system")
            self.assertEqual(second["response"]["response_origin"]["badge"], "SYSTEM")
            self.assertIsNone(second["response"]["original_response_snapshot"])
            self.assertIsNone(second["response"]["corrected_outcome"])
            self.assertEqual(second["session"]["pending_approvals"], [])
            self.assertEqual(second["session"]["messages"][-1]["artifact_id"], artifact_id)
            self.assertEqual(second["session"]["messages"][-1]["source_message_id"], source_message_id)
            self.assertEqual(second["session"]["messages"][-1]["save_content_source"], "original_draft")
            self.assertEqual(second["session"]["messages"][-1]["response_origin"]["provider"], "system")
            self.assertNotIn("original_response_snapshot", second["session"]["messages"][-1])
            self.assertNotIn("corrected_outcome", second["session"]["messages"][-1])
            source_messages = [
                message
                for message in second["session"]["messages"]
                if message.get("artifact_id") == artifact_id and message.get("original_response_snapshot")
            ]
            self.assertTrue(source_messages)
            corrected_outcome = source_messages[-1]["corrected_outcome"]
            self.assertEqual(corrected_outcome["outcome"], "accepted_as_is")
            self.assertEqual(corrected_outcome["artifact_id"], artifact_id)
            self.assertEqual(corrected_outcome["approval_id"], approval_id)
            self.assertEqual(corrected_outcome["saved_note_path"], str(note_path))
            self.assertEqual(corrected_outcome["source_message_id"], source_messages[-1]["message_id"])
            self.assertTrue(note_path.exists())

    def test_handle_chat_direct_approved_save_serializes_corrected_outcome(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "direct-approved-note.md"
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
                    "session_id": "direct-approved-session",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "note_path": str(note_path),
                    "approved": True,
                    "provider": "mock",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["response"]["status"], "saved")
            self.assertEqual(payload["response"]["artifact_kind"], "grounded_brief")
            self.assertEqual(
                payload["response"]["source_message_id"],
                payload["response"]["corrected_outcome"]["source_message_id"],
            )
            self.assertIsNotNone(payload["response"]["original_response_snapshot"])
            corrected_outcome = payload["response"]["corrected_outcome"]
            self.assertIsNotNone(corrected_outcome)
            self.assertEqual(corrected_outcome["outcome"], "accepted_as_is")
            self.assertEqual(corrected_outcome["artifact_id"], payload["response"]["artifact_id"])
            self.assertEqual(corrected_outcome["saved_note_path"], str(note_path))
            self.assertEqual(
                corrected_outcome["source_message_id"],
                payload["session"]["messages"][-1]["message_id"],
            )
            self.assertEqual(payload["response"]["save_content_source"], "original_draft")
            self.assertEqual(
                payload["session"]["messages"][-1]["source_message_id"],
                payload["response"]["source_message_id"],
            )
            self.assertEqual(payload["session"]["messages"][-1]["save_content_source"], "original_draft")
            self.assertEqual(
                payload["session"]["messages"][-1]["corrected_outcome"]["artifact_id"],
                payload["response"]["artifact_id"],
            )
            self.assertTrue(note_path.exists())

    def test_submit_content_verdict_after_original_draft_save_preserves_saved_history(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "source.md"
            note_path = tmp_path / "notes" / "late-flip-note.md"
            source_path.write_text("# Demo\n\nhello world", encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)

            saved = service.handle_chat(
                {
                    "session_id": "late-flip-session",
                    "source_path": str(source_path),
                    "save_summary": True,
                    "note_path": str(note_path),
                    "approved": True,
                    "provider": "mock",
                }
            )

            self.assertTrue(saved["ok"])
            self.assertEqual(saved["response"]["status"], "saved")
            source_message_id = saved["response"]["source_message_id"]
            self.assertTrue(source_message_id)
            saved_body = note_path.read_text(encoding="utf-8")

            payload = service.submit_content_verdict(
                {
                    "session_id": "late-flip-session",
                    "message_id": source_message_id,
                    "content_verdict": "rejected",
                }
            )

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["message_id"], source_message_id)
            self.assertEqual(payload["content_verdict"], "rejected")
            self.assertEqual(payload["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(payload["corrected_outcome"]["source_message_id"], source_message_id)
            self.assertTrue(note_path.exists())
            self.assertEqual(note_path.read_text(encoding="utf-8"), saved_body)

            session_messages = payload["session"]["messages"]
            source_messages = [
                message
                for message in session_messages
                if message.get("artifact_id") == saved["response"]["artifact_id"] and message.get("original_response_snapshot")
            ]
            self.assertTrue(source_messages)
            self.assertEqual(source_messages[-1]["corrected_outcome"]["outcome"], "rejected")
            self.assertEqual(source_messages[-1].get("saved_note_path"), str(note_path))
            self.assertEqual(
                source_messages[-1].get("corrected_outcome", {}).get("saved_note_path"),
                None,
            )

            saved_messages = [
                message for message in session_messages
                if message.get("saved_note_path") == str(note_path)
            ]
            self.assertTrue(saved_messages)
            self.assertEqual(saved_messages[-1]["artifact_id"], saved["response"]["artifact_id"])
            self.assertEqual(saved_messages[-1]["save_content_source"], "original_draft")

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
            self.assertEqual(second["response"]["artifact_id"], first["response"]["artifact_id"])
            self.assertEqual(
                second["response"]["source_message_id"],
                first["response"]["source_message_id"],
            )
            self.assertEqual(second["response"]["save_content_source"], "original_draft")
            self.assertEqual(second["response"]["proposed_note_path"], str(second_note_path))
            self.assertNotEqual(second["response"]["approval"]["approval_id"], first_approval["approval_id"])
            self.assertEqual(second["response"]["approval"]["artifact_id"], first["response"]["artifact_id"])
            self.assertEqual(
                second["response"]["approval"]["source_message_id"],
                first["response"]["source_message_id"],
            )
            self.assertEqual(second["response"]["approval"]["requested_path"], str(second_note_path))
            self.assertEqual(second["response"]["approval"]["save_content_source"], "original_draft")
            approval_reason_record = second["response"]["approval_reason_record"]
            self.assertIsNotNone(approval_reason_record)
            self.assertEqual(approval_reason_record["reason_scope"], "approval_reissue")
            self.assertEqual(approval_reason_record["reason_label"], "path_change")
            self.assertEqual(approval_reason_record["artifact_id"], first["response"]["artifact_id"])
            self.assertTrue(approval_reason_record["source_message_id"])
            self.assertEqual(
                approval_reason_record["approval_id"],
                second["response"]["approval"]["approval_id"],
            )
            self.assertEqual(
                second["response"]["approval"]["approval_reason_record"]["approval_id"],
                second["response"]["approval"]["approval_id"],
            )
            self.assertEqual(second["response"]["response_origin"]["provider"], "system")
            self.assertIn("새 경로로 저장하려면 다시 승인해 주세요.", second["response"]["text"])
            self.assertEqual(len(second["session"]["pending_approvals"]), 1)
            self.assertEqual(second["session"]["pending_approvals"][0]["requested_path"], str(second_note_path))
            self.assertEqual(second["session"]["pending_approvals"][0]["artifact_id"], first["response"]["artifact_id"])
            self.assertEqual(
                second["session"]["pending_approvals"][0]["source_message_id"],
                first["response"]["source_message_id"],
            )
            self.assertEqual(second["session"]["pending_approvals"][0]["save_content_source"], "original_draft")
            self.assertEqual(
                second["session"]["pending_approvals"][0]["approval_reason_record"]["reason_scope"],
                "approval_reissue",
            )
            self.assertEqual(
                second["session"]["messages"][-1]["approval_reason_record"]["approval_id"],
                second["response"]["approval"]["approval_id"],
            )
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
            approval_reason_record = second["response"]["approval_reason_record"]
            self.assertIsNotNone(approval_reason_record)
            self.assertEqual(approval_reason_record["reason_scope"], "approval_reject")
            self.assertEqual(approval_reason_record["reason_label"], "explicit_rejection")
            self.assertTrue(approval_reason_record["source_message_id"])
            self.assertEqual(approval_reason_record["approval_id"], approval_id)
            self.assertEqual(second["session"]["pending_approvals"], [])
            self.assertEqual(
                second["session"]["messages"][-1]["approval_reason_record"]["approval_id"],
                approval_id,
            )
            log_text = Path(settings.task_log_path).read_text(encoding="utf-8")
            self.assertIn("approval_rejected", log_text)
            self.assertIn("approval_reject", log_text)
            self.assertIn("explicit_rejection", log_text)

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

    def test_check_aggregate_conflict_visibility_creates_separate_record_with_key_fields(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_source_path = tmp_path / "cv-source-a.md"
            second_source_path = tmp_path / "cv-source-b.md"
            shared_body = "# Conflict Visibility\n\nhello world"
            first_source_path.write_text(shared_body, encoding="utf-8")
            second_source_path.write_text(shared_body, encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            session_id = "conflict-visibility-regression-session"
            corrected_text = "수정본입니다.\n핵심만 남겼습니다."

            # Step 1: first file → correct → confirm → review(accept)
            first = service.handle_chat(
                {"session_id": session_id, "source_path": str(first_source_path), "provider": "mock"}
            )
            first_artifact_id = first["response"]["artifact_id"]
            first_source_message_id = first["response"]["source_message_id"]
            first_corrected = service.submit_correction(
                {"session_id": session_id, "message_id": first_source_message_id, "corrected_text": corrected_text}
            )
            first_source_message = [
                m for m in first_corrected["session"]["messages"]
                if m.get("artifact_id") == first_artifact_id and m.get("original_response_snapshot")
            ][-1]
            candidate = first_source_message["session_local_candidate"]
            service.submit_candidate_confirmation(
                {
                    "session_id": session_id,
                    "message_id": first_source_message_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                }
            )
            service.submit_candidate_review(
                {
                    "session_id": session_id,
                    "message_id": first_source_message_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_updated_at": candidate["updated_at"],
                    "review_action": "accept",
                }
            )

            # Step 2: second file → correct → aggregate emerges unblocked
            second = service.handle_chat(
                {"session_id": session_id, "source_path": str(second_source_path), "provider": "mock"}
            )
            second_source_message_id = second["response"]["source_message_id"]
            payload = service.submit_correction(
                {"session_id": session_id, "message_id": second_source_message_id, "corrected_text": corrected_text}
            )
            aggregate = payload["session"]["recurrence_aggregate_candidates"][0]
            self.assertEqual(aggregate["reviewed_memory_capability_status"]["capability_outcome"], "unblocked_all_required")
            aggregate_fingerprint = aggregate["aggregate_key"]["normalized_delta_fingerprint"]

            # Step 3: emit → apply → confirm result → stop → reverse
            emitted = service.emit_aggregate_transition(
                {
                    "session_id": session_id,
                    "aggregate_fingerprint": aggregate_fingerprint,
                    "operator_reason_or_note": "테스트용 적용",
                }
            )
            canonical_transition_id = emitted["canonical_transition_id"]

            service.apply_aggregate_transition(
                {
                    "session_id": session_id,
                    "aggregate_fingerprint": aggregate_fingerprint,
                    "canonical_transition_id": canonical_transition_id,
                }
            )
            service.confirm_aggregate_transition_result(
                {
                    "session_id": session_id,
                    "aggregate_fingerprint": aggregate_fingerprint,
                    "canonical_transition_id": canonical_transition_id,
                }
            )
            service.stop_apply_aggregate_transition(
                {
                    "session_id": session_id,
                    "aggregate_fingerprint": aggregate_fingerprint,
                    "canonical_transition_id": canonical_transition_id,
                }
            )
            reverse_result = service.reverse_aggregate_transition(
                {
                    "session_id": session_id,
                    "aggregate_fingerprint": aggregate_fingerprint,
                    "canonical_transition_id": canonical_transition_id,
                }
            )
            self.assertEqual(reverse_result["transition_record"]["record_stage"], "reversed")

            # Step 4: conflict visibility check
            cv_result = service.check_aggregate_conflict_visibility(
                {
                    "session_id": session_id,
                    "aggregate_fingerprint": aggregate_fingerprint,
                    "canonical_transition_id": canonical_transition_id,
                }
            )
            self.assertTrue(cv_result["ok"])
            cv_record = cv_result["conflict_visibility_record"]

            # Key field assertions per codex_feedback.md
            self.assertEqual(cv_record["transition_action"], "future_reviewed_memory_conflict_visibility")
            self.assertEqual(cv_record["record_stage"], "conflict_visibility_checked")
            self.assertEqual(cv_record["conflict_visibility_stage"], "conflict_visibility_checked")
            self.assertEqual(cv_record["source_apply_transition_ref"], canonical_transition_id)
            self.assertIn("checked_at", cv_record)
            self.assertIsInstance(cv_record["checked_at"], str)
            self.assertIn("conflict_entries", cv_record)
            self.assertIsInstance(cv_record["conflict_entries"], list)
            self.assertIn("conflict_entry_count", cv_record)
            self.assertEqual(cv_record["conflict_entry_count"], len(cv_record["conflict_entries"]))

            # Verify it is a separate record with its own canonical_transition_id
            self.assertNotEqual(cv_record["canonical_transition_id"], canonical_transition_id)
            self.assertTrue(cv_record["canonical_transition_id"].startswith("transition-local-"))

            # Verify the original apply/reversal record is NOT mutated
            original_record = reverse_result["transition_record"]
            self.assertEqual(original_record["record_stage"], "reversed")
            self.assertEqual(original_record["transition_action"], "future_reviewed_memory_apply")

            # Verify the conflict_visibility_record appears in serialized session aggregate
            serialized_session = cv_result["session"]
            serialized_aggregate = serialized_session["recurrence_aggregate_candidates"][0]
            self.assertIn("reviewed_memory_conflict_visibility_record", serialized_aggregate)
            serialized_cv = serialized_aggregate["reviewed_memory_conflict_visibility_record"]
            self.assertEqual(serialized_cv["transition_action"], "future_reviewed_memory_conflict_visibility")
            self.assertEqual(serialized_cv["record_stage"], "conflict_visibility_checked")
            self.assertEqual(serialized_cv["source_apply_transition_ref"], canonical_transition_id)

            # Verify precondition: calling conflict check on non-reversed record fails
            with self.assertRaises(WebApiError) as ctx:
                service.check_aggregate_conflict_visibility(
                    {
                        "session_id": session_id,
                        "aggregate_fingerprint": aggregate_fingerprint,
                        "canonical_transition_id": cv_record["canonical_transition_id"],
                    }
                )
            self.assertEqual(ctx.exception.status_code, 400)

    def test_handler_dispatches_aggregate_transition_stop_to_service(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            server = LocalOnlyHTTPServer(("127.0.0.1", 0), service)
            port = server.server_address[1]

            import http.client
            import threading

            thread = threading.Thread(target=server.handle_request, daemon=True)
            thread.start()

            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                body = json.dumps({
                    "session_id": "handler-stop-test",
                    "aggregate_fingerprint": "nonexistent",
                    "canonical_transition_id": "nonexistent",
                }).encode("utf-8")
                conn.request(
                    "POST",
                    "/api/aggregate-transition-stop",
                    body=body,
                    headers={
                        "Content-Type": "application/json",
                        "Content-Length": str(len(body)),
                        "Host": f"127.0.0.1:{port}",
                        "Origin": f"http://127.0.0.1:{port}",
                    },
                )
                resp = conn.getresponse()
                resp_body = json.loads(resp.read().decode("utf-8"))
                conn.close()
            finally:
                server.server_close()
                thread.join(timeout=5)

            self.assertEqual(resp.status, 404)
            self.assertFalse(resp_body.get("ok", True))
            self.assertIn("error", resp_body)

    def test_handler_dispatches_aggregate_transition_stop_returns_ok(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_source_path = tmp_path / "hstop-source-a.md"
            second_source_path = tmp_path / "hstop-source-b.md"
            shared_body = "# Handler Stop\n\nhello world"
            first_source_path.write_text(shared_body, encoding="utf-8")
            second_source_path.write_text(shared_body, encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            session_id = "handler-stop-ok-session"
            corrected_text = "수정본입니다.\n핵심만 남겼습니다."

            # Build an unblocked aggregate and drive through emit→apply→confirm
            first = service.handle_chat(
                {"session_id": session_id, "source_path": str(first_source_path), "provider": "mock"}
            )
            first_sid = first["response"]["source_message_id"]
            first_aid = first["response"]["artifact_id"]
            fc = service.submit_correction(
                {"session_id": session_id, "message_id": first_sid, "corrected_text": corrected_text}
            )
            fm = [m for m in fc["session"]["messages"]
                  if m.get("artifact_id") == first_aid and m.get("original_response_snapshot")][-1]
            cand = fm["session_local_candidate"]
            service.submit_candidate_confirmation(
                {"session_id": session_id, "message_id": first_sid,
                 "candidate_id": cand["candidate_id"], "candidate_updated_at": cand["updated_at"]}
            )
            service.submit_candidate_review(
                {"session_id": session_id, "message_id": first_sid,
                 "candidate_id": cand["candidate_id"], "candidate_updated_at": cand["updated_at"],
                 "review_action": "accept"}
            )
            second = service.handle_chat(
                {"session_id": session_id, "source_path": str(second_source_path), "provider": "mock"}
            )
            second_sid = second["response"]["source_message_id"]
            service.submit_correction(
                {"session_id": session_id, "message_id": second_sid, "corrected_text": corrected_text}
            )
            sess = service.get_session_payload(session_id)
            agg = sess["session"]["recurrence_aggregate_candidates"][0]
            fp = agg["aggregate_key"]["normalized_delta_fingerprint"]

            emitted = service.emit_aggregate_transition(
                {"session_id": session_id, "aggregate_fingerprint": fp, "operator_reason_or_note": "핸들러 stop 테스트"}
            )
            tid = emitted["canonical_transition_id"]
            service.apply_aggregate_transition(
                {"session_id": session_id, "aggregate_fingerprint": fp, "canonical_transition_id": tid}
            )
            service.confirm_aggregate_transition_result(
                {"session_id": session_id, "aggregate_fingerprint": fp, "canonical_transition_id": tid}
            )

            # Now test stop via HTTP handler
            server = LocalOnlyHTTPServer(("127.0.0.1", 0), service)
            port = server.server_address[1]

            import http.client
            import threading

            thread = threading.Thread(target=server.handle_request, daemon=True)
            thread.start()

            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                body = json.dumps({
                    "session_id": session_id,
                    "aggregate_fingerprint": fp,
                    "canonical_transition_id": tid,
                }).encode("utf-8")
                conn.request(
                    "POST",
                    "/api/aggregate-transition-stop",
                    body=body,
                    headers={
                        "Content-Type": "application/json",
                        "Content-Length": str(len(body)),
                        "Host": f"127.0.0.1:{port}",
                        "Origin": f"http://127.0.0.1:{port}",
                    },
                )
                resp = conn.getresponse()
                resp_body = json.loads(resp.read().decode("utf-8"))
                conn.close()
            finally:
                server.server_close()
                thread.join(timeout=5)

            self.assertEqual(resp.status, 200)
            self.assertTrue(resp_body["ok"])
            self.assertIn("canonical_transition_id", resp_body)
            self.assertEqual(resp_body["transition_record"]["record_stage"], "stopped")

    def test_handler_dispatches_aggregate_transition_reverse_to_service(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            server = LocalOnlyHTTPServer(("127.0.0.1", 0), service)
            port = server.server_address[1]

            import http.client
            import threading

            thread = threading.Thread(target=server.handle_request, daemon=True)
            thread.start()

            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                body = json.dumps({
                    "session_id": "handler-reverse-test",
                    "aggregate_fingerprint": "nonexistent",
                    "canonical_transition_id": "nonexistent",
                }).encode("utf-8")
                conn.request(
                    "POST",
                    "/api/aggregate-transition-reverse",
                    body=body,
                    headers={
                        "Content-Type": "application/json",
                        "Content-Length": str(len(body)),
                        "Host": f"127.0.0.1:{port}",
                        "Origin": f"http://127.0.0.1:{port}",
                    },
                )
                resp = conn.getresponse()
                resp_body = json.loads(resp.read().decode("utf-8"))
                conn.close()
            finally:
                server.server_close()
                thread.join(timeout=5)

            # The route dispatches to reverse_aggregate_transition;
            # with no transition records the service returns a 404 error.
            self.assertEqual(resp.status, 404)
            self.assertFalse(resp_body.get("ok", True))
            self.assertIn("error", resp_body)

    def test_handler_dispatches_aggregate_transition_reverse_returns_ok(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_source_path = tmp_path / "hrev-source-a.md"
            second_source_path = tmp_path / "hrev-source-b.md"
            shared_body = "# Handler Reverse\n\nhello world"
            first_source_path.write_text(shared_body, encoding="utf-8")
            second_source_path.write_text(shared_body, encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            session_id = "handler-reverse-ok-session"
            corrected_text = "수정본입니다.\n핵심만 남겼습니다."

            # Build an unblocked aggregate and drive through emit→apply→confirm→stop
            first = service.handle_chat(
                {"session_id": session_id, "source_path": str(first_source_path), "provider": "mock"}
            )
            first_sid = first["response"]["source_message_id"]
            first_aid = first["response"]["artifact_id"]
            fc = service.submit_correction(
                {"session_id": session_id, "message_id": first_sid, "corrected_text": corrected_text}
            )
            fm = [m for m in fc["session"]["messages"]
                  if m.get("artifact_id") == first_aid and m.get("original_response_snapshot")][-1]
            cand = fm["session_local_candidate"]
            service.submit_candidate_confirmation(
                {"session_id": session_id, "message_id": first_sid,
                 "candidate_id": cand["candidate_id"], "candidate_updated_at": cand["updated_at"]}
            )
            service.submit_candidate_review(
                {"session_id": session_id, "message_id": first_sid,
                 "candidate_id": cand["candidate_id"], "candidate_updated_at": cand["updated_at"],
                 "review_action": "accept"}
            )
            second = service.handle_chat(
                {"session_id": session_id, "source_path": str(second_source_path), "provider": "mock"}
            )
            second_sid = second["response"]["source_message_id"]
            service.submit_correction(
                {"session_id": session_id, "message_id": second_sid, "corrected_text": corrected_text}
            )
            sess = service.get_session_payload(session_id)
            agg = sess["session"]["recurrence_aggregate_candidates"][0]
            fp = agg["aggregate_key"]["normalized_delta_fingerprint"]

            emitted = service.emit_aggregate_transition(
                {"session_id": session_id, "aggregate_fingerprint": fp, "operator_reason_or_note": "핸들러 reverse 테스트"}
            )
            tid = emitted["canonical_transition_id"]
            service.apply_aggregate_transition(
                {"session_id": session_id, "aggregate_fingerprint": fp, "canonical_transition_id": tid}
            )
            service.confirm_aggregate_transition_result(
                {"session_id": session_id, "aggregate_fingerprint": fp, "canonical_transition_id": tid}
            )
            service.stop_apply_aggregate_transition(
                {"session_id": session_id, "aggregate_fingerprint": fp, "canonical_transition_id": tid}
            )

            # Now test reverse via HTTP handler
            server = LocalOnlyHTTPServer(("127.0.0.1", 0), service)
            port = server.server_address[1]

            import http.client
            import threading

            thread = threading.Thread(target=server.handle_request, daemon=True)
            thread.start()

            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                body = json.dumps({
                    "session_id": session_id,
                    "aggregate_fingerprint": fp,
                    "canonical_transition_id": tid,
                }).encode("utf-8")
                conn.request(
                    "POST",
                    "/api/aggregate-transition-reverse",
                    body=body,
                    headers={
                        "Content-Type": "application/json",
                        "Content-Length": str(len(body)),
                        "Host": f"127.0.0.1:{port}",
                        "Origin": f"http://127.0.0.1:{port}",
                    },
                )
                resp = conn.getresponse()
                resp_body = json.loads(resp.read().decode("utf-8"))
                conn.close()
            finally:
                server.server_close()
                thread.join(timeout=5)

            self.assertEqual(resp.status, 200)
            self.assertTrue(resp_body["ok"])
            self.assertIn("canonical_transition_id", resp_body)
            self.assertEqual(resp_body["transition_record"]["record_stage"], "reversed")

    def test_handler_dispatches_aggregate_transition_conflict_check_to_service(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            server = LocalOnlyHTTPServer(("127.0.0.1", 0), service)
            port = server.server_address[1]

            import http.client
            import threading

            thread = threading.Thread(target=server.handle_request, daemon=True)
            thread.start()

            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                body = json.dumps({
                    "session_id": "handler-cv-test",
                    "aggregate_fingerprint": "nonexistent",
                    "canonical_transition_id": "nonexistent",
                }).encode("utf-8")
                conn.request(
                    "POST",
                    "/api/aggregate-transition-conflict-check",
                    body=body,
                    headers={
                        "Content-Type": "application/json",
                        "Content-Length": str(len(body)),
                        "Host": f"127.0.0.1:{port}",
                        "Origin": f"http://127.0.0.1:{port}",
                    },
                )
                resp = conn.getresponse()
                resp_body = json.loads(resp.read().decode("utf-8"))
                conn.close()
            finally:
                server.server_close()
                thread.join(timeout=5)

            # The route dispatches to check_aggregate_conflict_visibility;
            # with no transition records the service returns a 404 error.
            self.assertEqual(resp.status, 404)
            self.assertFalse(resp_body.get("ok", True))
            self.assertIn("error", resp_body)

    def test_handler_dispatches_aggregate_transition_conflict_check_returns_ok(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_source_path = tmp_path / "hcv-source-a.md"
            second_source_path = tmp_path / "hcv-source-b.md"
            shared_body = "# Handler CV\n\nhello world"
            first_source_path.write_text(shared_body, encoding="utf-8")
            second_source_path.write_text(shared_body, encoding="utf-8")

            settings = AppSettings(
                sessions_dir=str(tmp_path / "sessions"),
                task_log_path=str(tmp_path / "task_log.jsonl"),
                notes_dir=str(tmp_path / "notes"),
                model_provider="mock",
            )
            service = WebAppService(settings=settings)
            session_id = "handler-conflict-visibility-ok-session"
            corrected_text = "수정본입니다.\n핵심만 남겼습니다."

            # Build an unblocked aggregate and drive through emit→apply→confirm→stop→reverse
            first = service.handle_chat(
                {"session_id": session_id, "source_path": str(first_source_path), "provider": "mock"}
            )
            first_sid = first["response"]["source_message_id"]
            first_aid = first["response"]["artifact_id"]
            fc = service.submit_correction(
                {"session_id": session_id, "message_id": first_sid, "corrected_text": corrected_text}
            )
            fm = [m for m in fc["session"]["messages"]
                  if m.get("artifact_id") == first_aid and m.get("original_response_snapshot")][-1]
            cand = fm["session_local_candidate"]
            service.submit_candidate_confirmation(
                {"session_id": session_id, "message_id": first_sid,
                 "candidate_id": cand["candidate_id"], "candidate_updated_at": cand["updated_at"]}
            )
            service.submit_candidate_review(
                {"session_id": session_id, "message_id": first_sid,
                 "candidate_id": cand["candidate_id"], "candidate_updated_at": cand["updated_at"],
                 "review_action": "accept"}
            )
            second = service.handle_chat(
                {"session_id": session_id, "source_path": str(second_source_path), "provider": "mock"}
            )
            second_sid = second["response"]["source_message_id"]
            service.submit_correction(
                {"session_id": session_id, "message_id": second_sid, "corrected_text": corrected_text}
            )
            sess = service.get_session_payload(session_id)
            agg = sess["session"]["recurrence_aggregate_candidates"][0]
            fp = agg["aggregate_key"]["normalized_delta_fingerprint"]

            emitted = service.emit_aggregate_transition(
                {"session_id": session_id, "aggregate_fingerprint": fp, "operator_reason_or_note": "핸들러 테스트"}
            )
            tid = emitted["canonical_transition_id"]
            service.apply_aggregate_transition(
                {"session_id": session_id, "aggregate_fingerprint": fp, "canonical_transition_id": tid}
            )
            service.confirm_aggregate_transition_result(
                {"session_id": session_id, "aggregate_fingerprint": fp, "canonical_transition_id": tid}
            )
            service.stop_apply_aggregate_transition(
                {"session_id": session_id, "aggregate_fingerprint": fp, "canonical_transition_id": tid}
            )
            service.reverse_aggregate_transition(
                {"session_id": session_id, "aggregate_fingerprint": fp, "canonical_transition_id": tid}
            )

            # Now test via HTTP handler
            server = LocalOnlyHTTPServer(("127.0.0.1", 0), service)
            port = server.server_address[1]

            import http.client
            import threading

            thread = threading.Thread(target=server.handle_request, daemon=True)
            thread.start()

            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                body = json.dumps({
                    "session_id": session_id,
                    "aggregate_fingerprint": fp,
                    "canonical_transition_id": tid,
                }).encode("utf-8")
                conn.request(
                    "POST",
                    "/api/aggregate-transition-conflict-check",
                    body=body,
                    headers={
                        "Content-Type": "application/json",
                        "Content-Length": str(len(body)),
                        "Host": f"127.0.0.1:{port}",
                        "Origin": f"http://127.0.0.1:{port}",
                    },
                )
                resp = conn.getresponse()
                resp_body = json.loads(resp.read().decode("utf-8"))
                conn.close()
            finally:
                server.server_close()
                thread.join(timeout=5)

            self.assertEqual(resp.status, 200)
            self.assertTrue(resp_body["ok"])
            self.assertIn("canonical_transition_id", resp_body)
            self.assertEqual(
                resp_body["conflict_visibility_record"]["transition_action"],
                "future_reviewed_memory_conflict_visibility",
            )

    def test_send_json_ignores_broken_pipe(self) -> None:
        handler = LocalAssistantHandler.__new__(LocalAssistantHandler)
        handler.wfile = _BrokenPipeWriter()
        handler.send_response = lambda status: None
        handler.send_header = lambda name, value: None
        handler.end_headers = lambda: None

        handler._send_json(200, {"ok": True})


    def test_get_config_includes_notes_dir(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            notes_path = str(Path(tmp_dir) / "custom_notes")
            settings = AppSettings(
                app_name="config-test",
                sessions_dir=str(Path(tmp_dir) / "sessions"),
                task_log_path=str(Path(tmp_dir) / "task_log.jsonl"),
                notes_dir=notes_path,
                model_provider="mock",
                ollama_model="",
            )
            service = WebAppService(settings=settings)
            config = service.get_config()
            self.assertEqual(config["notes_dir"], notes_path)


if __name__ == "__main__":
    unittest.main()
