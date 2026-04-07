"""HTTP integration tests through LocalAssistantHandler.

These tests verify the actual HTTP request/response cycle including
routing, request parsing, header validation, and error handling.
They start a real LocalOnlyHTTPServer on a random port and issue
requests via http.client.HTTPConnection.
"""

import http.client
import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from app.web import LocalAssistantHandler, LocalOnlyHTTPServer, WebAppService
from config.settings import AppSettings
from tools.file_reader import FileReaderTool
from tools.file_search import FileSearchTool
from tools.write_note import WriteNoteTool


class _FakeWebSearchTool:
    """Minimal fake web search tool replicating the pattern from test_web_app.py."""

    def __init__(self, results=None, pages=None):
        self._results = results or []
        self._pages = dict(pages or {})

    def search(self, *, query: str, max_results: int = 5):
        if isinstance(self._results, dict):
            return list(self._results.get(query, []))[:max_results]
        return list(self._results)[:max_results]

    def fetch_page(self, *, url: str, max_chars: int | None = None):
        page = self._pages.get(url)
        if page is None:
            raise RuntimeError("fixture page not found")
        return SimpleNamespace(
            url=url,
            title=str(page.get("title") or ""),
            text=str(page.get("text") or "")[:max_chars or 10000],
            excerpt=str(page.get("excerpt") or ""),
            content_type=str(page.get("content_type") or "text/html"),
        )


class HTTPIntegrationBase(unittest.TestCase):
    """Base class that boots a real HTTP server on a random port."""

    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)

        self.settings = AppSettings(
            sessions_dir=str(self.tmp_path / "sessions"),
            task_log_path=str(self.tmp_path / "task_log.jsonl"),
            notes_dir=str(self.tmp_path / "notes"),
            web_search_history_dir=str(self.tmp_path / "web-search"),
            model_provider="mock",
            ollama_model="",
        )

        self.service = WebAppService(settings=self.settings)

        # Wire in safe tools that do not touch real filesystem/network
        self.service._build_tools = lambda: {
            "read_file": FileReaderTool(),
            "search_files": FileSearchTool(reader=FileReaderTool()),
            "search_web": _FakeWebSearchTool(),
            "write_note": WriteNoteTool(
                allowed_roots=[str(self.tmp_path), str(self.tmp_path / "notes")]
            ),
        }

        # port=0 lets the OS pick a free port
        self.server = LocalOnlyHTTPServer(("127.0.0.1", 0), self.service)
        self.host, self.port = self.server.server_address

        self._server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._server_thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self._server_thread.join(timeout=5)
        self._tmpdir.cleanup()

    # ---- helpers ----

    def _conn(self) -> http.client.HTTPConnection:
        return http.client.HTTPConnection(self.host, self.port, timeout=10)

    def _origin(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def _default_headers(self) -> dict[str, str]:
        return {
            "Host": f"127.0.0.1:{self.port}",
            "Origin": self._origin(),
            "Content-Type": "application/json",
        }

    def get(self, path: str) -> http.client.HTTPResponse:
        conn = self._conn()
        conn.request("GET", path, headers=self._default_headers())
        resp = conn.getresponse()
        return resp

    def post(self, path: str, body: dict | None = None) -> http.client.HTTPResponse:
        encoded = json.dumps(body or {}, ensure_ascii=False).encode("utf-8")
        headers = self._default_headers()
        headers["Content-Length"] = str(len(encoded))
        conn = self._conn()
        conn.request("POST", path, body=encoded, headers=headers)
        resp = conn.getresponse()
        return resp

    def post_raw(self, path: str, body_bytes: bytes, headers: dict[str, str]) -> http.client.HTTPResponse:
        conn = self._conn()
        conn.request("POST", path, body=body_bytes, headers=headers)
        resp = conn.getresponse()
        return resp

    def read_json(self, resp: http.client.HTTPResponse) -> dict:
        return json.loads(resp.read().decode("utf-8"))


# =====================================================================
# GET endpoint tests
# =====================================================================


class TestGetEndpoints(HTTPIntegrationBase):
    def test_get_root_redirects_to_app(self) -> None:
        resp = self.get("/")
        self.assertEqual(resp.status, 302)
        self.assertEqual(resp.getheader("Location"), "/app")
        self.assertEqual(resp.read(), b"")

    def test_get_api_config(self) -> None:
        resp = self.get("/api/config")
        self.assertEqual(resp.status, 200)
        data = self.read_json(resp)
        self.assertTrue(data["ok"])
        self.assertIn("app_name", data)
        self.assertIn("default_session_id", data)

    def test_get_api_sessions(self) -> None:
        resp = self.get("/api/sessions")
        self.assertEqual(resp.status, 200)
        data = self.read_json(resp)
        self.assertTrue(data["ok"])
        self.assertIsInstance(data["sessions"], list)

    def test_get_api_session_with_id(self) -> None:
        resp = self.get("/api/session?session_id=test-session")
        self.assertEqual(resp.status, 200)
        data = self.read_json(resp)
        self.assertTrue(data["ok"])
        self.assertIn("session", data)

    def test_get_healthz(self) -> None:
        resp = self.get("/healthz")
        self.assertEqual(resp.status, 200)
        data = self.read_json(resp)
        self.assertTrue(data["ok"])

    def test_get_nonexistent_returns_404(self) -> None:
        resp = self.get("/nonexistent")
        self.assertEqual(resp.status, 404)
        data = self.read_json(resp)
        self.assertFalse(data["ok"])

    def test_get_app_serves_shipped_template_shell(self) -> None:
        resp = self.get("/app")
        self.assertEqual(resp.status, 200)
        self.assertIn("text/html", resp.getheader("Content-Type", ""))
        body = resp.read().decode("utf-8")
        self.assertIn("요청 실행", body)
        self.assertIn("advanced-settings", body)
        self.assertIn("response-copy-text", body)

    def test_get_app_preview_serves_react_build(self) -> None:
        react_dist = self.tmp_path / "react-dist"
        react_assets = react_dist / "assets"
        react_assets.mkdir(parents=True)
        (react_dist / "index.html").write_text(
            "<!doctype html><html><body>react preview</body></html>",
            encoding="utf-8",
        )
        (react_assets / "main.js").write_text("console.log('preview');", encoding="utf-8")

        with patch.object(LocalAssistantHandler, "_REACT_DIST_DIR", react_dist):
            app_resp = self.get("/app-preview")
            self.assertEqual(app_resp.status, 200)
            self.assertIn("text/html", app_resp.getheader("Content-Type", ""))
            self.assertIn("react preview", app_resp.read().decode("utf-8"))

            asset_resp = self.get("/assets/main.js")
            self.assertEqual(asset_resp.status, 200)
            self.assertIn("javascript", asset_resp.getheader("Content-Type", ""))
            self.assertIn("preview", asset_resp.read().decode("utf-8"))

    def test_get_app_preview_returns_404_when_react_build_missing(self) -> None:
        react_dist = self.tmp_path / "missing-react-dist"
        with patch.object(LocalAssistantHandler, "_REACT_DIST_DIR", react_dist):
            resp = self.get("/app-preview")
        self.assertEqual(resp.status, 404)
        data = self.read_json(resp)
        self.assertFalse(data["ok"])


# =====================================================================
# POST /api/chat tests
# =====================================================================


class TestPostChat(HTTPIntegrationBase):
    def test_chat_simple_text(self) -> None:
        """Simple user text returns expected response shape."""
        resp = self.post("/api/chat", {
            "session_id": "http-chat-1",
            "user_text": "hello",
            "provider": "mock",
        })
        self.assertEqual(resp.status, 200)
        data = self.read_json(resp)
        self.assertTrue(data["ok"])
        self.assertIn("response", data)
        self.assertIn("text", data["response"])
        self.assertIn("status", data["response"])
        self.assertIn("session", data)
        self.assertIn("session_id", data["session"])

    def test_chat_file_summary(self) -> None:
        """Providing a source_path to a real temp file returns a file summary."""
        source = self.tmp_path / "sample.txt"
        source.write_text("This is a sample document for testing.", encoding="utf-8")

        resp = self.post("/api/chat", {
            "session_id": "http-file-summary",
            "source_path": str(source),
            "provider": "mock",
        })
        self.assertEqual(resp.status, 200)
        data = self.read_json(resp)
        self.assertTrue(data["ok"])
        self.assertIn("response", data)
        # Without save_summary the status is "answer"; with it it becomes "needs_approval"
        self.assertIn(data["response"]["status"], ("answer", "needs_approval", "ok"))
        # File summaries always produce an artifact_kind of grounded_brief
        self.assertEqual(data["response"]["artifact_kind"], "grounded_brief")


# =====================================================================
# POST /api/feedback tests
# =====================================================================


class TestPostFeedback(HTTPIntegrationBase):
    def test_feedback_success(self) -> None:
        """Submit feedback on an existing assistant message."""
        # First create a chat message so there is an assistant message to give feedback on
        chat_resp = self.post("/api/chat", {
            "session_id": "http-feedback",
            "user_text": "feedback test",
            "provider": "mock",
        })
        chat_data = self.read_json(chat_resp)

        # The assistant message_id is in the session messages, not source_message_id
        # (source_message_id is only populated for file-summary artifacts)
        messages = chat_data["session"].get("messages", [])
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        self.assertTrue(len(assistant_msgs) > 0, "Expected at least one assistant message")
        message_id = assistant_msgs[-1]["message_id"]

        # Now submit feedback
        resp = self.post("/api/feedback", {
            "session_id": "http-feedback",
            "message_id": message_id,
            "feedback_label": "helpful",
        })
        self.assertEqual(resp.status, 200)
        data = self.read_json(resp)
        self.assertTrue(data["ok"])
        self.assertEqual(data["feedback_label"], "helpful")

    def test_feedback_missing_fields_returns_400(self) -> None:
        """Missing message_id or feedback_label returns 400."""
        resp = self.post("/api/feedback", {
            "session_id": "http-feedback-bad",
        })
        self.assertEqual(resp.status, 400)
        data = self.read_json(resp)
        self.assertFalse(data["ok"])


# =====================================================================
# POST /api/correction tests
# =====================================================================


class TestPostCorrection(HTTPIntegrationBase):
    def test_correction_on_grounded_brief(self) -> None:
        """Submit a correction to a grounded-brief message via HTTP."""
        # Create a file summary first (grounded_brief artifact)
        source = self.tmp_path / "correct-doc.txt"
        source.write_text("Important document content here for correction test.", encoding="utf-8")

        chat_resp = self.post("/api/chat", {
            "session_id": "http-correction",
            "source_path": str(source),
            "provider": "mock",
        })
        chat_data = self.read_json(chat_resp)
        self.assertTrue(chat_data["ok"])
        message_id = chat_data["response"].get("source_message_id")

        resp = self.post("/api/correction", {
            "session_id": "http-correction",
            "message_id": message_id,
            "corrected_text": "This is the corrected version.",
        })
        self.assertEqual(resp.status, 200)
        data = self.read_json(resp)
        self.assertTrue(data["ok"])
        self.assertEqual(data["message_id"], message_id)


# =====================================================================
# Approval flow tests
# =====================================================================


class TestApprovalFlow(HTTPIntegrationBase):
    def test_approve_file_summary(self) -> None:
        """Create a file summary, then approve it."""
        source = self.tmp_path / "approve-doc.txt"
        source.write_text("Document to be approved.\nWith multiple lines.", encoding="utf-8")
        notes_dir = self.tmp_path / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Create the file summary (should get needs_approval)
        chat_resp = self.post("/api/chat", {
            "session_id": "http-approval",
            "source_path": str(source),
            "provider": "mock",
            "save_summary": True,
            "note_path": str(notes_dir / "approved-note.md"),
        })
        chat_data = self.read_json(chat_resp)
        self.assertTrue(chat_data["ok"])
        self.assertEqual(chat_data["response"]["status"], "needs_approval")

        # Find the approval ID
        pending = chat_data["session"].get("pending_approvals", [])
        self.assertTrue(len(pending) > 0, "Expected at least one pending approval")
        approval_id = pending[0]["approval_id"]

        # Step 2: Approve it
        approve_resp = self.post("/api/chat", {
            "session_id": "http-approval",
            "approved_approval_id": approval_id,
        })
        approve_data = self.read_json(approve_resp)
        self.assertTrue(approve_data["ok"])
        self.assertIn(approve_data["response"]["status"], ("ok", "saved"))

    def test_reject_file_summary(self) -> None:
        """Create a file summary, then reject it."""
        source = self.tmp_path / "reject-doc.txt"
        source.write_text("Document to be rejected.", encoding="utf-8")
        notes_dir = self.tmp_path / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        chat_resp = self.post("/api/chat", {
            "session_id": "http-reject",
            "source_path": str(source),
            "provider": "mock",
            "save_summary": True,
            "note_path": str(notes_dir / "rejected-note.md"),
        })
        chat_data = self.read_json(chat_resp)
        self.assertTrue(chat_data["ok"])
        pending = chat_data["session"].get("pending_approvals", [])
        self.assertTrue(len(pending) > 0)
        approval_id = pending[0]["approval_id"]

        reject_resp = self.post("/api/chat", {
            "session_id": "http-reject",
            "rejected_approval_id": approval_id,
        })
        reject_data = self.read_json(reject_resp)
        self.assertTrue(reject_data["ok"])


# =====================================================================
# Error handling tests
# =====================================================================


class TestErrorHandling(HTTPIntegrationBase):
    def test_missing_content_length_returns_400(self) -> None:
        """POST without Content-Length header returns 400."""
        headers = {
            "Host": f"127.0.0.1:{self.port}",
            "Origin": self._origin(),
            "Content-Type": "application/json",
            # Deliberately omit Content-Length
        }
        conn = self._conn()
        # Send a POST with an empty body and no Content-Length
        conn.request("POST", "/api/chat", body=b"", headers=headers)
        resp = conn.getresponse()
        self.assertEqual(resp.status, 400)
        data = self.read_json(resp)
        self.assertFalse(data["ok"])

    def test_malformed_json_body_returns_400(self) -> None:
        """POST with invalid JSON returns 400."""
        bad_body = b"this is not json"
        headers = {
            "Host": f"127.0.0.1:{self.port}",
            "Origin": self._origin(),
            "Content-Type": "application/json",
            "Content-Length": str(len(bad_body)),
        }
        resp = self.post_raw("/api/chat", bad_body, headers)
        self.assertEqual(resp.status, 400)
        data = self.read_json(resp)
        self.assertFalse(data["ok"])

    def test_cross_origin_request_returns_403(self) -> None:
        """POST with wrong Origin header returns 403."""
        body = json.dumps({"user_text": "hello"}).encode("utf-8")
        headers = {
            "Host": f"127.0.0.1:{self.port}",
            "Origin": "http://evil.example.com",
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }
        resp = self.post_raw("/api/chat", body, headers)
        self.assertEqual(resp.status, 403)
        data = self.read_json(resp)
        self.assertFalse(data["ok"])

    def test_post_to_unknown_endpoint_returns_404(self) -> None:
        """POST to an unrecognized path returns 404."""
        resp = self.post("/api/nonexistent", {"foo": "bar"})
        self.assertEqual(resp.status, 404)
        data = self.read_json(resp)
        self.assertFalse(data["ok"])

    def test_post_chat_with_no_input_returns_400(self) -> None:
        """POST /api/chat with empty payload (no user_text, source_path, etc.) returns 400."""
        resp = self.post("/api/chat", {
            "session_id": "http-empty",
            "provider": "mock",
        })
        self.assertEqual(resp.status, 400)
        data = self.read_json(resp)
        self.assertFalse(data["ok"])


# =====================================================================
# Streaming tests
# =====================================================================


class TestStreaming(HTTPIntegrationBase):
    def test_stream_chat_returns_ndjson(self) -> None:
        """POST /api/chat/stream returns ndjson with at least a final event."""
        resp = self.post("/api/chat/stream", {
            "session_id": "http-stream-1",
            "user_text": "stream test",
            "provider": "mock",
            "request_id": "req-stream-1",
        })
        self.assertEqual(resp.status, 200)
        content_type = resp.getheader("Content-Type", "")
        self.assertIn("ndjson", content_type)

        raw = resp.read().decode("utf-8")
        lines = [line for line in raw.strip().split("\n") if line.strip()]
        self.assertTrue(len(lines) >= 1, "Expected at least one ndjson line")

        events = [json.loads(line) for line in lines]
        event_types = [ev.get("event") for ev in events if "event" in ev]
        # There should be a "final" event
        self.assertIn("final", event_types)

    def test_cancel_stream(self) -> None:
        """POST /api/chat/cancel returns a valid response."""
        resp = self.post("/api/chat/cancel", {
            "session_id": "http-cancel-1",
            "request_id": "nonexistent-request",
        })
        self.assertEqual(resp.status, 200)
        data = self.read_json(resp)
        self.assertTrue(data["ok"])
        # Since there is no active stream, cancelled should be False
        self.assertFalse(data["cancelled"])


# =====================================================================
# Session isolation test
# =====================================================================


class TestSessionIsolation(HTTPIntegrationBase):
    def test_different_sessions_are_independent(self) -> None:
        """Messages in session A do not appear in session B."""
        # Send a message to session A
        self.post("/api/chat", {
            "session_id": "http-session-A",
            "user_text": "message for session A",
            "provider": "mock",
        })

        # Check session B is empty
        resp = self.get("/api/session?session_id=http-session-B")
        data = self.read_json(resp)
        self.assertTrue(data["ok"])
        messages = data["session"].get("messages", [])
        # Session B should have no messages (or only system-level ones)
        user_messages = [m for m in messages if m.get("role") == "user"]
        self.assertEqual(len(user_messages), 0)


# =====================================================================
# Content-Verdict endpoint test
# =====================================================================


class TestContentVerdict(HTTPIntegrationBase):
    def test_content_verdict_missing_fields_returns_400(self) -> None:
        """POST /api/content-verdict with missing required fields returns 400."""
        resp = self.post("/api/content-verdict", {
            "session_id": "http-verdict-bad",
        })
        self.assertEqual(resp.status, 400)
        data = self.read_json(resp)
        self.assertFalse(data["ok"])


if __name__ == "__main__":
    unittest.main()
