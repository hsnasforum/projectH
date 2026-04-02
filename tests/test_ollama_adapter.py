from __future__ import annotations

import json
import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from model_adapter.base import ModelAdapterError
from model_adapter.factory import build_model_adapter
from model_adapter.ollama import OllamaModelAdapter


class _FakeOllamaHandler(BaseHTTPRequestHandler):
    requests: list[dict[str, object]] = []
    models: list[str] = ["qwen2.5:3b", "llama3.2:latest"]
    version: str = "0.12.6"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/version":
            self._send_json(200, {"version": _FakeOllamaHandler.version})
            return
        if self.path != "/api/tags":
            self.send_error(404)
            return
        self._send_json(
            200,
            {
                "models": [{"name": name} for name in _FakeOllamaHandler.models]
            },
        )

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/generate":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        payload = json.loads(raw_body.decode("utf-8"))
        _FakeOllamaHandler.requests.append(payload)

        prompt = payload.get("prompt", "")
        system = payload.get("system", "")
        if isinstance(system, str) and ("Summarize the provided document" in system or "문서를 한국어로 요약" in system):
            response_text = f"summary::{str(prompt)[:32]}"
        elif isinstance(system, str) and ("Return exactly three bullet points" in system or "핵심 포인트 3개" in system):
            response_text = f"key_points::{str(prompt)[:32]}"
        elif isinstance(system, str) and ("Return only actionable next steps" in system or "실행 가능한 항목만 번호 목록" in system):
            response_text = f"action_items::{str(prompt)[:32]}"
        elif isinstance(system, str) and ("Rewrite the answer in Korean memo format" in system or "메모 형식으로 쓰세요" in system):
            response_text = f"memo::{str(prompt)[:32]}"
        else:
            response_text = f"response::{str(prompt)[:32]}"

        if payload.get("stream") is True:
            chunks = [
                {
                    "model": payload.get("model", "unknown"),
                    "response": response_text[: len(response_text) // 2],
                    "done": False,
                },
                {
                    "model": payload.get("model", "unknown"),
                    "response": response_text[len(response_text) // 2 :],
                    "done": True,
                },
            ]
            body = ("\n".join(json.dumps(chunk) for chunk in chunks) + "\n").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self._send_json(
            200,
            {
                "model": payload.get("model", "unknown"),
                "response": response_text,
                "done": True,
            },
        )

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class OllamaAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _FakeOllamaHandler.requests = []
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeOllamaHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def setUp(self) -> None:
        _FakeOllamaHandler.requests = []
        _FakeOllamaHandler.models = ["qwen2.5:3b", "llama3.2:latest"]
        _FakeOllamaHandler.version = "0.12.6"

    def test_summarize_uses_generate_endpoint(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        summary = adapter.summarize("hello world from adapter")

        self.assertEqual(summary, "summary::hello world from adapter")
        self.assertEqual(len(_FakeOllamaHandler.requests), 1)
        request_payload = _FakeOllamaHandler.requests[0]
        self.assertEqual(request_payload["model"], "qwen2.5:3b")
        self.assertEqual(request_payload["stream"], True)
        system_str = str(request_payload["system"])
        # Compact model uses Korean system prompt
        self.assertIn("한국어로 요약", system_str)
        self.assertIn("이야기글이면", system_str)
        self.assertIn("정보글이면", system_str)

    def test_respond_defaults_to_korean(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        response = adapter.respond("간단히 답해 주세요.")

        self.assertEqual(response, "response::간단히 답해 주세요.")
        request_payload = _FakeOllamaHandler.requests[0]
        system_str = str(request_payload["system"])
        # Compact model uses Korean system prompt
        self.assertIn("한국어로 답하세요", system_str)
        self.assertIn("추측하지 말고", system_str)

    def test_summarize_rewrites_han_script_output_to_korean(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)
        calls: list[dict[str, str]] = []
        response_groups = iter(
            [
                ["### 產品原則\n- 本地優先\n- 授權執行\n- 供應商中立"],
                ["로컬 우선, 승인 기반 실행, 공급자 중립 구조를 강조하는 문서입니다."],
            ]
        )

        def fake_iter_generate_raw(*, prompt: str, system: str):
            calls.append({"prompt": prompt, "system": system})
            yield from next(response_groups)

        adapter._iter_generate_raw = fake_iter_generate_raw  # type: ignore[method-assign]

        summary = adapter.summarize("demo text")

        self.assertEqual(summary, "로컬 우선, 승인 기반 실행, 공급자 중립 구조를 강조하는 문서입니다.")
        self.assertEqual(len(calls), 2)
        # Compact model uses Korean system prompt
        self.assertIn("한국어로 요약", calls[0]["system"])
        self.assertIn("Rewrite the supplied text into natural Korean", calls[1]["system"])

    def test_respond_rewrites_mixed_kana_output_to_korean(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)
        calls: list[dict[str, str]] = []
        response_groups = iter(
            [
                ["주로 레ゴ 장난감에 대한 영상을 올립니다."],
                ["주로 레고 장난감에 대한 영상을 올립니다."],
            ]
        )

        def fake_iter_generate_raw(*, prompt: str, system: str):
            calls.append({"prompt": prompt, "system": system})
            yield from next(response_groups)

        adapter._iter_generate_raw = fake_iter_generate_raw  # type: ignore[method-assign]

        response = adapter.respond("간단히 답해 주세요.")

        self.assertEqual(response, "주로 레고 장난감에 대한 영상을 올립니다.")
        self.assertEqual(len(calls), 2)
        # Compact model uses Korean system prompt
        self.assertIn("한국어로 답하세요", calls[0]["system"])
        self.assertIn("Rewrite the supplied text into natural Korean", calls[1]["system"])

    def test_stream_respond_buffers_mixed_kana_until_rewritten(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)
        calls: list[dict[str, str]] = []
        response_groups = iter(
            [
                ["주로 레ゴ 장난감에 대한 영상을 올립니다."],
                ["주로 레고 장난감에 대한 영상을 올립니다."],
            ]
        )

        def fake_iter_generate_raw(*, prompt: str, system: str):
            calls.append({"prompt": prompt, "system": system})
            yield from next(response_groups)

        adapter._iter_generate_raw = fake_iter_generate_raw  # type: ignore[method-assign]

        events = list(adapter.stream_respond("간단히 답해 주세요."))
        final_text = ""
        for event in events:
            final_text = adapter._apply_stream_event(final_text, event)  # type: ignore[attr-defined]

        self.assertEqual(final_text, "주로 레고 장난감에 대한 영상을 올립니다.")
        self.assertEqual(len(calls), 2)
        self.assertTrue(all("레ゴ" not in event.text for event in events if hasattr(event, "text")))

    def test_create_summary_note_produces_markdown(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        note = adapter.create_summary_note(
            source_path="/tmp/demo.md",
            text="hello from a local markdown file",
        )

        self.assertEqual(note.title, "demo.md 요약")
        self.assertIn("원본 파일: /tmp/demo.md", note.note_body)
        self.assertIn("summary::hello from a local markdown file", note.note_body)

    def test_answer_with_context_routes_key_points_intent(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        answer = adapter.answer_with_context(
            intent="key_points",
            user_request="핵심 3줄만 다시 정리해 주세요.",
            context_label="demo.md",
            source_paths=["/tmp/demo.md"],
            context_excerpt="demo excerpt",
            summary_hint="summary hint",
        )

        self.assertTrue(answer.startswith("- "))
        request_payload = _FakeOllamaHandler.requests[-1]
        # Compact model uses Korean system prompt
        self.assertIn("핵심 포인트 3개", str(request_payload["system"]))
        # Compact prompt uses simplified structure
        self.assertIn("질문", str(request_payload["prompt"]))

    def test_answer_with_context_routes_action_items_intent(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        answer = adapter.answer_with_context(
            intent="action_items",
            user_request="실행할 일만 뽑아 주세요.",
            context_label="demo.md",
            source_paths=["/tmp/demo.md"],
            context_excerpt="demo excerpt",
            summary_hint="summary hint",
        )

        self.assertTrue(answer.startswith("1. "))
        request_payload = _FakeOllamaHandler.requests[-1]
        # Compact model uses Korean system prompt
        self.assertIn("실행 가능한 항목만", str(request_payload["system"]))
        self.assertIn("질문", str(request_payload["prompt"]))

    def test_answer_with_context_action_items_prompt_adds_grounded_evidence_sections(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        adapter.answer_with_context(
            intent="action_items",
            user_request="실행할 일만 뽑아 주세요.",
            context_label="proposal.md",
            source_paths=["/tmp/proposal.md"],
            context_excerpt="\n".join(
                [
                    "# 로컬 AI 비서 프로젝트 제안서 및 실행 지침",
                    "- 영문 제목: Local AI Assistant Project Proposal & Execution Guide",
                    "- 버전: v1.1",
                    "## 13. 즉시 실행 권고 사항",
                    "1. 문서 기반 의사결정 고정: AGENTS.md/CLAUDE.md/기본 config를 저장소 기준으로 확정합니다.",
                    "2. model_adapter에 첫 실제 제공자를 연결하되 인터페이스는 공급자 중립으로 유지합니다.",
                ]
            ),
            summary_hint="proposal summary",
            evidence_items=[
                {
                    "source_path": "/tmp/proposal.md",
                    "source_name": "proposal.md",
                    "label": "실행 후보",
                    "snippet": "문서 기반 의사결정 고정: AGENTS.md/CLAUDE.md/기본 config를 저장소 기준으로 확정합니다.",
                },
                {
                    "source_path": "/tmp/proposal.md",
                    "source_name": "proposal.md",
                    "label": "실행 후보",
                    "snippet": "model_adapter에 첫 실제 제공자를 연결하되 인터페이스는 공급자 중립으로 유지합니다.",
                },
            ],
        )

        request_payload = _FakeOllamaHandler.requests[-1]
        prompt = str(request_payload["prompt"])
        system = str(request_payload["system"])
        # Compact prompt: evidence merged under 핵심 근거, document first
        self.assertIn("핵심 근거", prompt)
        self.assertIn("[1] proposal.md | 실행 후보 | 문서 기반 의사결정 고정", prompt)
        self.assertIn("문서 내용", prompt)
        self.assertIn("문서 기반 의사결정 고정", prompt)
        self.assertIn("질문", prompt)
        # Compact system: Korean guardrails
        self.assertIn("실행 가능한 항목만", system)
        self.assertIn("근거에 없는 내용은", system)

    def test_answer_with_context_general_prompt_requires_evidence_only_answers(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        adapter.answer_with_context(
            intent="general",
            user_request="이 인물이 실제로 어떤 일을 했나요?",
            context_label="웹 검색: sample",
            source_paths=["https://example.com/sample"],
            context_excerpt="선택된 근거 묶음:\n[1] 출처: sample\n[1] 근거: sample snippet",
            summary_hint=None,
            evidence_items=[
                {
                    "source_path": "https://example.com/sample",
                    "source_name": "sample",
                    "label": "웹 원문 근거",
                    "snippet": "sample snippet",
                },
            ],
        )

        request_payload = _FakeOllamaHandler.requests[-1]
        prompt = str(request_payload["prompt"])
        system = str(request_payload["system"])
        # Compact prompt: merged evidence
        self.assertIn("핵심 근거", prompt)
        self.assertIn("sample | 웹 원문 근거 | sample snippet", prompt)
        # Compact system: Korean guardrails
        self.assertIn("근거와 문서 발췌만 사용", system)
        self.assertIn("확인되지 않습니다", system)

    def test_answer_with_context_routes_memo_intent(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        answer = adapter.answer_with_context(
            intent="memo",
            user_request="메모 형식으로 다시 써 주세요.",
            context_label="demo.md",
            source_paths=["/tmp/demo.md"],
            context_excerpt="demo excerpt",
            summary_hint="summary hint",
        )

        self.assertIn("제목:", answer)
        self.assertIn("핵심:", answer)
        self.assertIn("다음 행동:", answer)
        request_payload = _FakeOllamaHandler.requests[-1]
        # Compact model uses Korean system prompt
        self.assertIn("메모 형식으로 쓰세요", str(request_payload["system"]))
        self.assertIn("질문", str(request_payload["prompt"]))

    def test_answer_with_context_key_points_prompt_prefers_principles_and_ignores_metadata(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        adapter.answer_with_context(
            intent="key_points",
            user_request="핵심 3줄만 다시 정리해 주세요.",
            context_label="proposal.md",
            source_paths=["/tmp/proposal.md"],
            context_excerpt="\n".join(
                [
                    "# 로컬 AI 비서 프로젝트 제안서 및 실행 지침",
                    "- 작성일: 2026-03-25",
                    "## 핵심 목표",
                    "- 로컬 파일 기반 생산성 도구를 안전하게 제공한다.",
                    "- 향후 독자 모델·독자 데이터로 확장 가능한 구조를 선행 확보한다.",
                    "- 상업화 시 권리 구조와 브랜드 리스크를 줄인다.",
                ]
            ),
            summary_hint="proposal summary",
        )

        request_payload = _FakeOllamaHandler.requests[-1]
        prompt = str(request_payload["prompt"])
        # Compact prompt: document content first, user question last
        self.assertIn("문서 내용", prompt)
        self.assertIn("로컬 파일 기반 생산성 도구를 안전하게 제공한다.", prompt)
        self.assertIn("질문", prompt)

    def test_answer_with_context_key_points_postprocess_filters_metadata_and_keeps_three_lines(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)
        adapter._generate = lambda **kwargs: "\n".join(  # type: ignore[method-assign]
            [
                "- 작성일: 2026-03-25",
                "- 로컬 파일 기반 생산성 도구를 안전하게 제공한다.",
                "- 향후 독자 모델·독자 데이터로 확장 가능한 구조를 선행 확보한다.",
                "- 상업화 시 권리 구조와 브랜드 리스크를 줄인다.",
            ]
        )

        answer = adapter.answer_with_context(
            intent="key_points",
            user_request="핵심 3줄만 다시 정리해 주세요.",
            context_label="proposal.md",
            source_paths=["/tmp/proposal.md"],
            context_excerpt="\n".join(
                [
                    "# 로컬 AI 비서 프로젝트 제안서 및 실행 지침",
                    "- 작성일: 2026-03-25",
                    "## 핵심 목표",
                    "- 로컬 파일 기반 생산성 도구를 안전하게 제공한다.",
                    "- 향후 독자 모델·독자 데이터로 확장 가능한 구조를 선행 확보한다.",
                    "- 상업화 시 권리 구조와 브랜드 리스크를 줄인다.",
                ]
            ),
            summary_hint="proposal summary",
        )

        self.assertNotIn("작성일", answer)
        lines = answer.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(line.startswith("- ") for line in lines))

    def test_answer_with_context_action_items_postprocess_filters_metadata_lines(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)
        adapter._generate = lambda **kwargs: "\n".join(  # type: ignore[method-assign]
            [
                "1. 영문 제목: Local AI Assistant Project Proposal & Execution Guide",
                "2. 문서 기반 의사결정 고정: AGENTS.md/CLAUDE.md/기본 config를 저장소 기준으로 확정합니다.",
                "3. 작성일: 2026-03-25",
                "4. model_adapter에 첫 실제 제공자를 연결하되 인터페이스는 공급자 중립으로 유지합니다.",
            ]
        )

        answer = adapter.answer_with_context(
            intent="action_items",
            user_request="실행할 일만 뽑아 주세요.",
            context_label="proposal.md",
            source_paths=["/tmp/proposal.md"],
            context_excerpt="\n".join(
                [
                    "# 로컬 AI 비서 프로젝트 제안서 및 실행 지침",
                    "- 영문 제목: Local AI Assistant Project Proposal & Execution Guide",
                    "- 작성일: 2026-03-25",
                    "## 13. 즉시 실행 권고 사항",
                    "1. 문서 기반 의사결정 고정: AGENTS.md/CLAUDE.md/기본 config를 저장소 기준으로 확정합니다.",
                    "2. model_adapter에 첫 실제 제공자를 연결하되 인터페이스는 공급자 중립으로 유지합니다.",
                ]
            ),
            summary_hint="proposal summary",
        )

        self.assertNotIn("영문 제목", answer)
        self.assertNotIn("작성일", answer)
        self.assertIn("문서 기반 의사결정 고정", answer)
        self.assertIn("model_adapter에 첫 실제 제공자를 연결", answer)
        self.assertTrue(answer.startswith("1. "))

    def test_answer_with_context_action_items_postprocess_uses_default_when_no_grounded_action_exists(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)
        adapter._generate = lambda **kwargs: "\n".join(  # type: ignore[method-assign]
            [
                "1. 영문 제목: Local AI Assistant Project Proposal & Execution Guide",
                "2. 작성일: 2026-03-25",
            ]
        )

        answer = adapter.answer_with_context(
            intent="action_items",
            user_request="실행할 일만 뽑아 주세요.",
            context_label="proposal.md",
            source_paths=["/tmp/proposal.md"],
            context_excerpt="\n".join(
                [
                    "# 로컬 AI 비서 프로젝트 제안서 및 실행 지침",
                    "- 영문 제목: Local AI Assistant Project Proposal & Execution Guide",
                    "- 작성일: 2026-03-25",
                    "## 프로젝트 요약",
                    "- 내 PC에서 실행되며, 문서를 읽고 요약하고 검색하고, 승인 기반으로 제한된 작업만 수행하는 로컬 AI 비서 MVP를 만든다.",
                ]
            ),
            summary_hint="proposal summary",
        )

        self.assertEqual(answer, "1. 문서에 바로 실행할 일은 명확히 나오지 않습니다.")

    def test_answer_with_context_memo_postprocess_preserves_required_sections(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)
        adapter._generate = lambda **kwargs: "\n".join(  # type: ignore[method-assign]
            [
                "제목: 제안서 메모",
                "핵심:",
                "- 작성일: 2026-03-25",
                "- 로컬 파일 기반 생산성 도구를 안전하게 제공한다.",
                "다음 행동:",
                "- 영문 제목: Local AI Assistant Project Proposal & Execution Guide",
                "- 문서 기반 의사결정 고정: AGENTS.md/CLAUDE.md/기본 config를 저장소 기준으로 확정합니다.",
            ]
        )

        answer = adapter.answer_with_context(
            intent="memo",
            user_request="메모 형식으로 다시 써 주세요.",
            context_label="proposal.md",
            source_paths=["/tmp/proposal.md"],
            context_excerpt="\n".join(
                [
                    "# 로컬 AI 비서 프로젝트 제안서 및 실행 지침",
                    "- 작성일: 2026-03-25",
                    "## 핵심 목표",
                    "- 로컬 파일 기반 생산성 도구를 안전하게 제공한다.",
                    "## 13. 즉시 실행 권고 사항",
                    "1. 문서 기반 의사결정 고정: AGENTS.md/CLAUDE.md/기본 config를 저장소 기준으로 확정합니다.",
                ]
            ),
            summary_hint="proposal summary",
        )

        self.assertIn("제목: 제안서 메모", answer)
        self.assertIn("핵심:", answer)
        self.assertIn("다음 행동:", answer)
        self.assertNotIn("영문 제목", answer)
        self.assertNotIn("작성일", answer)
        self.assertIn("문서 기반 의사결정 고정", answer)

    def test_list_models_reads_tags_endpoint(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        models = adapter.list_models()

        self.assertEqual(models, ["qwen2.5:3b", "llama3.2:latest"])

    def test_health_check_reports_version_and_model_availability(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        status = adapter.health_check()

        self.assertTrue(status.reachable)
        self.assertTrue(status.configured_model_available)
        self.assertEqual(status.version, "0.12.6")
        self.assertIn("is installed", status.detail)

    def test_health_check_reports_missing_model_with_pull_hint(self) -> None:
        _FakeOllamaHandler.models = ["llama3.2:latest"]
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)

        status = adapter.health_check()

        self.assertTrue(status.reachable)
        self.assertFalse(status.configured_model_available)
        self.assertIn("ollama pull qwen2.5:3b", status.detail)

    def test_factory_builds_ollama_adapter(self) -> None:
        adapter = build_model_adapter(
            provider="ollama",
            ollama_base_url=self.base_url,
            ollama_model="qwen2.5:3b",
            ollama_timeout_seconds=5,
        )

        self.assertIsInstance(adapter, OllamaModelAdapter)

    def test_connection_error_is_helpful(self) -> None:
        adapter = OllamaModelAdapter(
            base_url="http://127.0.0.1:9",
            model="qwen2.5:3b",
            timeout_seconds=0.2,
        )

        with self.assertRaises(ModelAdapterError) as context:
            adapter.respond("hello")

        self.assertIn("Unable to reach Ollama", str(context.exception))

    def test_timeout_error_is_helpful(self) -> None:
        adapter = OllamaModelAdapter(
            base_url=self.base_url,
            model="qwen2.5:3b",
            timeout_seconds=12,
        )

        with patch("model_adapter.ollama.request.urlopen", side_effect=socket.timeout("timed out")):
            with self.assertRaises(ModelAdapterError) as context:
                adapter.respond("hello")

        self.assertIn("timed out after 12 seconds", str(context.exception))
        self.assertIn("LOCAL_AI_OLLAMA_TIMEOUT_SECONDS", str(context.exception))

    def test_full_system_respond_contains_hedging_instruction(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:14b", timeout_seconds=5)
        prompt = adapter._FULL_SYSTEM_RESPOND
        self.assertIn("hedging expressions", prompt)
        self.assertIn("알려져 있습니다", prompt)
        self.assertIn("confirmed fact", prompt)

    def test_compact_system_respond_contains_hedging_instruction(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)
        prompt = adapter._COMPACT_SYSTEM_RESPOND
        self.assertIn("유보적 표현", prompt)

    def test_follow_up_intent_prompts_specify_density_bounds(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:14b", timeout_seconds=5)
        from model_adapter.base import (
            FOLLOW_UP_INTENT_KEY_POINTS, FOLLOW_UP_INTENT_ACTION_ITEMS,
            FOLLOW_UP_INTENT_MEMO, FOLLOW_UP_INTENT_GENERAL,
        )
        # key_points: exactly 3
        kp_sys = adapter._intent_system_prompt(FOLLOW_UP_INTENT_KEY_POINTS)
        self.assertIn("three bullet points", kp_sys)
        # action_items: 2 to 5
        ai_sys = adapter._intent_system_prompt(FOLLOW_UP_INTENT_ACTION_ITEMS)
        self.assertIn("2 to 5 items", ai_sys)
        ai_contract = adapter._intent_output_contract(FOLLOW_UP_INTENT_ACTION_ITEMS)
        self.assertIn("2 to 5", ai_contract)
        # memo: section item counts
        memo_sys = adapter._intent_system_prompt(FOLLOW_UP_INTENT_MEMO)
        self.assertIn("2~3", memo_sys)
        self.assertIn("1~3", memo_sys)
        memo_contract = adapter._intent_output_contract(FOLLOW_UP_INTENT_MEMO)
        self.assertIn("2~3", memo_contract)
        # general: sentence count
        gen_sys = adapter._intent_system_prompt(FOLLOW_UP_INTENT_GENERAL)
        self.assertIn("2~4", gen_sys)
        gen_contract = adapter._intent_output_contract(FOLLOW_UP_INTENT_GENERAL)
        self.assertIn("2~4", gen_contract)

    def test_compact_follow_up_intent_prompts_specify_density_bounds(self) -> None:
        adapter = OllamaModelAdapter(base_url=self.base_url, model="qwen2.5:3b", timeout_seconds=5)
        from model_adapter.base import (
            FOLLOW_UP_INTENT_ACTION_ITEMS, FOLLOW_UP_INTENT_MEMO,
            FOLLOW_UP_INTENT_GENERAL,
        )
        ai_sys = adapter._compact_intent_system_prompt(FOLLOW_UP_INTENT_ACTION_ITEMS)
        self.assertIn("2~5", ai_sys)
        memo_sys = adapter._compact_intent_system_prompt(FOLLOW_UP_INTENT_MEMO)
        self.assertIn("2~3", memo_sys)
        gen_sys = adapter._compact_intent_system_prompt(FOLLOW_UP_INTENT_GENERAL)
        self.assertIn("2~4", gen_sys)
