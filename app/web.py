from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import threading
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.localization import localize_text
from app.serializers import SerializerMixin
from config.runtime_hosts import (
    browser_host_for_bind,
    resolve_bind_host,
    windows_fallback_host,
)
from core.contracts import (
    ContentVerdict,
    FeedbackLabel,
    FeedbackReason,
    WebSearchPermission,
)
from config.settings import AppSettings
from model_adapter.base import ModelAdapterError
from storage.session_store import SessionStore
from storage.task_log import TaskLogger
from storage.web_search_store import WebSearchStore


from app.errors import WebApiError
from app.handlers.aggregate import AggregateHandlerMixin
from app.handlers.feedback import FeedbackHandlerMixin
from app.handlers.preferences import PreferenceHandlerMixin
from app.handlers.chat import ChatHandlerMixin

DEFAULT_SESSION_ID = "demo-session"


class WebAppService(ChatHandlerMixin, AggregateHandlerMixin, FeedbackHandlerMixin, PreferenceHandlerMixin, SerializerMixin):
    def __init__(
        self,
        settings: AppSettings,
        *,
        template_path: str | None = None,
    ) -> None:
        self.settings = settings
        if settings.storage_backend == "sqlite":
            from storage.sqlite_store import (
                SQLiteDatabase, SQLiteSessionStore, SQLiteTaskLogger,
                SQLiteArtifactStore, SQLitePreferenceStore, SQLiteCorrectionStore,
            )
            db = SQLiteDatabase(db_path=settings.sqlite_db_path)
            self.session_store = SQLiteSessionStore(db)  # type: ignore[assignment]
            self.task_logger = SQLiteTaskLogger(db)  # type: ignore[assignment]
            self.artifact_store = SQLiteArtifactStore(db)  # type: ignore[assignment]
            self.preference_store = SQLitePreferenceStore(db)  # type: ignore[assignment]
            self.correction_store = SQLiteCorrectionStore(db)  # type: ignore[assignment]
            try:
                correction_count = db.fetchone(
                    "SELECT COUNT(*) as cnt FROM corrections", ()
                )
                if (correction_count or {}).get("cnt", 0) == 0:
                    corrections_path = Path(settings.corrections_dir)
                    if corrections_path.is_dir() and any(corrections_path.glob("*.json")):
                        from storage.sqlite_store import migrate_json_to_sqlite
                        migrate_json_to_sqlite(
                            corrections_dir=str(corrections_path),
                            sessions_dir=None,
                            artifacts_dir=None,
                            preferences_dir=None,
                            db_path=settings.sqlite_db_path,
                        )
            except Exception:
                pass
        else:
            self.session_store = SessionStore(base_dir=settings.sessions_dir)
            self.task_logger = TaskLogger(path=settings.task_log_path)
            from storage.artifact_store import ArtifactStore
            self.artifact_store = ArtifactStore(base_dir=settings.artifacts_dir)
            from storage.correction_store import CorrectionStore
            self.correction_store = CorrectionStore(base_dir=settings.corrections_dir)
            from storage.preference_store import PreferenceStore
            self.preference_store = PreferenceStore(base_dir=settings.preferences_dir)
        self.web_search_store = WebSearchStore(base_dir=settings.web_search_history_dir)
        self.template_path = Path(template_path) if template_path else Path(__file__).with_name("templates") / "index.html"
        self._active_stream_requests: dict[str, threading.Event] = {}
        self._active_stream_lock = threading.Lock()

    def render_index(self) -> str:
        template = self.template_path.read_text(encoding="utf-8")
        default_model = self.settings.ollama_model if self.settings.model_provider == "ollama" else ""
        default_model_label = default_model or "선택형 로컬 모델"
        default_web_search_permission = self._normalize_web_search_permission(self.settings.web_search_permission)
        return (
            template.replace("__APP_NAME__", self.settings.app_name)
            .replace("__DEFAULT_PROVIDER__", self.settings.model_provider)
            .replace("__DEFAULT_MODEL__", default_model)
            .replace("__DEFAULT_MODEL_LABEL__", default_model_label)
            .replace("__DEFAULT_BASE_URL__", self.settings.ollama_base_url)
            .replace("__DEFAULT_SESSION_ID__", DEFAULT_SESSION_ID)
            .replace("__DEFAULT_WEB_SEARCH_PERMISSION__", default_web_search_permission)
            .replace("__DEFAULT_WEB_SEARCH_PERMISSION_LABEL__", self._web_search_permission_label(default_web_search_permission))
        )

    def get_config(self) -> dict[str, Any]:
        default_model = self.settings.ollama_model if self.settings.model_provider == "ollama" else ""
        default_web_search_permission = self._normalize_web_search_permission(self.settings.web_search_permission)
        return {
            "ok": True,
            "app_name": self.settings.app_name,
            "default_session_id": DEFAULT_SESSION_ID,
            "default_provider": self.settings.model_provider,
            "default_model": default_model,
            "default_model_label": default_model or "선택형 로컬 모델",
            "default_base_url": self.settings.ollama_base_url,
            "default_web_search_permission": default_web_search_permission,
            "default_web_search_permission_label": self._web_search_permission_label(default_web_search_permission),
            "web_search_tool_connected": True,
            "web_host": self.settings.web_host,
            "web_port": self.settings.web_port,
            "notes_dir": self.settings.notes_dir,
        }

    def list_sessions_payload(self) -> dict[str, Any]:
        sessions = self.session_store.list_sessions()
        for item in sessions:
            preview = item.get("last_message_preview")
            if isinstance(preview, str):
                item["last_message_preview"] = localize_text(preview)
        return {
            "ok": True,
            "sessions": sessions,
        }

    def get_session_payload(self, session_id: str | None) -> dict[str, Any]:
        normalized = self._normalize_session_id(session_id)
        return {
            "ok": True,
            "session": self._serialize_session(self.session_store.get_session(normalized)),
        }

    # -- Session management --

    def delete_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_optional_text(payload.get("session_id"))
        if not session_id:
            raise WebApiError(400, "삭제할 세션 ID가 필요합니다.")
        deleted = self.session_store.delete_session(session_id)
        if deleted:
            self.task_logger.log(session_id=session_id, action="session_deleted", detail={})
        return {"ok": True, "deleted": deleted, "session_id": session_id}

    def delete_all_sessions(self) -> dict[str, Any]:
        count = self.session_store.delete_all_sessions()
        self.task_logger.log(session_id="system", action="all_sessions_deleted", detail={"count": count})
        return {"ok": True, "deleted_count": count}

    # -- Normalizer / parser utilities --

    def _normalize_session_id(self, raw_value: Any) -> str:
        session_id = self._normalize_optional_text(raw_value) or DEFAULT_SESSION_ID
        session_id = session_id.replace("/", "-").replace("\\", "-").strip()
        return session_id or DEFAULT_SESSION_ID

    def _normalize_optional_text(self, raw_value: Any) -> str | None:
        if not isinstance(raw_value, str):
            return None
        normalized = raw_value.strip()
        return normalized or None

    def _normalize_feedback_label(self, raw_value: Any) -> str | None:
        normalized = self._normalize_optional_text(raw_value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered not in {FeedbackLabel.HELPFUL, FeedbackLabel.UNCLEAR, FeedbackLabel.INCORRECT}:
            return None
        return lowered

    def _normalize_feedback_reason(self, raw_value: Any) -> str | None:
        normalized = self._normalize_optional_text(raw_value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered not in {FeedbackReason.FACTUAL_ERROR, FeedbackReason.IRRELEVANT_RESULT, FeedbackReason.CONTEXT_MISS, FeedbackReason.AWKWARD_TONE}:
            return None
        return lowered

    def _normalize_content_verdict(self, raw_value: Any) -> str | None:
        normalized = self._normalize_optional_text(raw_value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered == ContentVerdict.REJECTED:
            return lowered
        return None

    def _normalize_web_search_permission(self, raw_value: Any) -> str:
        if not isinstance(raw_value, str):
            return WebSearchPermission.DISABLED
        normalized = raw_value.strip().lower()
        if normalized in {WebSearchPermission.DISABLED, WebSearchPermission.APPROVAL, WebSearchPermission.ENABLED}:
            return normalized
        return WebSearchPermission.DISABLED

    def _web_search_permission_label(self, permission: Any) -> str:
        normalized = self._normalize_web_search_permission(permission)
        if normalized == WebSearchPermission.APPROVAL:
            return "승인 필요 · 읽기 전용 검색"
        if normalized == WebSearchPermission.ENABLED:
            return "허용 · 읽기 전용 검색"
        return "차단 · 읽기 전용 검색"

    def _coerce_bool(self, raw_value: Any) -> bool:
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, str):
            return raw_value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(raw_value)

    def _parse_selected_paths(self, raw_value: Any) -> list[str] | None:
        if raw_value is None:
            return None
        if isinstance(raw_value, str):
            values = raw_value.replace("\r", "\n").split("\n")
        elif isinstance(raw_value, list):
            values = []
            for item in raw_value:
                if isinstance(item, str):
                    values.extend(item.split("\n"))
        else:
            raise WebApiError(400, "선택 경로는 문자열 또는 문자열 목록이어야 합니다.")

        parsed: list[str] = []
        for value in values:
            for part in value.split(","):
                normalized = part.strip()
                if normalized:
                    parsed.append(normalized)
        return parsed or None

    def _parse_positive_int(self, raw_value: Any, *, default: int) -> int:
        if raw_value in (None, ""):
            return default
        if isinstance(raw_value, int):
            parsed = raw_value
        elif isinstance(raw_value, str) and raw_value.strip().isdigit():
            parsed = int(raw_value.strip())
        else:
            raise WebApiError(400, "검색 개수 제한은 1 이상의 정수여야 합니다.")

        if parsed <= 0:
            raise WebApiError(400, "검색 개수 제한은 1 이상의 정수여야 합니다.")
        return parsed


class LocalOnlyHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], service: WebAppService) -> None:
        super().__init__(server_address, LocalAssistantHandler)
        self.service = service


class LocalAssistantHandler(BaseHTTPRequestHandler):
    server: LocalOnlyHTTPServer
    _CONTROLLER_DIR = Path(__file__).resolve().parent.parent / "controller"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(int(HTTPStatus.FOUND))
            self.send_header("Location", "/app")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if parsed.path == "/api/config":
            self._send_json(HTTPStatus.OK, self.server.service.get_config())
            return
        if parsed.path == "/api/sessions":
            self._send_json(HTTPStatus.OK, self.server.service.list_sessions_payload())
            return
        if parsed.path == "/api/session":
            session_id = parse_qs(parsed.query).get("session_id", [DEFAULT_SESSION_ID])[0]
            self._send_json(HTTPStatus.OK, self.server.service.get_session_payload(session_id))
            return
        if parsed.path == "/healthz":
            self._send_json(HTTPStatus.OK, {"ok": True})
            return
        if parsed.path == "/api/preferences":
            self._send_json(HTTPStatus.OK, self.server.service.list_preferences_payload())
            return
        if parsed.path == "/api/preferences/audit":
            self._send_json(HTTPStatus.OK, {"ok": True, "audit": self.server.service.get_preference_audit()})
            return
        if parsed.path.startswith("/controller-assets/"):
            self._serve_controller_asset(parsed.path)
            return
        if parsed.path.startswith("/static/"):
            self._serve_static(parsed.path)
            return
        if parsed.path == "/controller" or parsed.path == "/controller/":
            self._serve_controller_html()
            return
        if parsed.path == "/app" or parsed.path == "/app/":
            self._serve_shipped_app()
            return
        if parsed.path == "/app-preview" or parsed.path == "/app-preview/":
            self._serve_react_app()
            return
        if parsed.path.startswith("/assets/"):
            self._serve_react_asset(parsed.path)
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {
            "/api/chat",
            "/api/chat/stream",
            "/api/chat/cancel",
            "/api/feedback",
            "/api/correction",
            "/api/candidate-confirmation",
            "/api/candidate-review",
            "/api/aggregate-transition",
            "/api/aggregate-transition-apply",
            "/api/aggregate-transition-result",
            "/api/aggregate-transition-stop",
            "/api/aggregate-transition-reverse",
            "/api/aggregate-transition-conflict-check",
            "/api/content-verdict",
            "/api/content-reason-note",
            "/api/content-reason-label",
            "/api/preferences/activate",
            "/api/preferences/pause",
            "/api/preferences/reject",
            "/api/preferences/update-description",
            "/api/sessions/delete",
            "/api/sessions/delete-all",
        }:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})
            return

        try:
            self._validate_same_origin()
            payload = self._read_json_body()
            if parsed.path == "/api/feedback":
                response = self.server.service.submit_feedback(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/correction":
                response = self.server.service.submit_correction(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/candidate-confirmation":
                response = self.server.service.submit_candidate_confirmation(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/candidate-review":
                response = self.server.service.submit_candidate_review(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition":
                response = self.server.service.emit_aggregate_transition(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-apply":
                response = self.server.service.apply_aggregate_transition(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-result":
                response = self.server.service.confirm_aggregate_transition_result(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-stop":
                response = self.server.service.stop_apply_aggregate_transition(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-reverse":
                response = self.server.service.reverse_aggregate_transition(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/aggregate-transition-conflict-check":
                response = self.server.service.check_aggregate_conflict_visibility(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/content-verdict":
                response = self.server.service.submit_content_verdict(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/content-reason-note":
                response = self.server.service.submit_content_reason_note(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/content-reason-label":
                response = self.server.service.submit_content_reason_label(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/preferences/activate":
                response = self.server.service.activate_preference(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/preferences/pause":
                response = self.server.service.pause_preference(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/preferences/reject":
                response = self.server.service.reject_preference(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/preferences/update-description":
                response = self.server.service.update_preference_description(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/sessions/delete":
                response = self.server.service.delete_session(payload)
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/sessions/delete-all":
                response = self.server.service.delete_all_sessions()
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/chat/cancel":
                response = self.server.service.cancel_stream(
                    session_id=payload.get("session_id"),
                    request_id=payload.get("request_id"),
                )
                self._send_json(HTTPStatus.OK, response)
                return
            if parsed.path == "/api/chat/stream":
                self._send_json_stream(self.server.service.stream_chat(payload))
                return
            response = self.server.service.handle_chat(payload)
            self._send_json(HTTPStatus.OK, response)
        except WebApiError as exc:
            self._send_json(exc.status_code, {"ok": False, "error": {"message": localize_text(exc.message)}})
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": {"message": "JSON 요청 본문 형식이 올바르지 않습니다."}})
        except ModelAdapterError as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": {"message": localize_text(str(exc))}})
        except Exception as exc:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": {"message": localize_text(str(exc))}})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _validate_same_origin(self) -> None:
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        referer = self.headers.get("Referer")

        if origin:
            if urlparse(origin).netloc != host:
                raise WebApiError(HTTPStatus.FORBIDDEN, "로컬 웹 셸에서는 다른 origin의 요청을 허용하지 않습니다.")
            return

        if referer and urlparse(referer).netloc != host:
            raise WebApiError(HTTPStatus.FORBIDDEN, "로컬 웹 셸에서는 다른 origin의 요청을 허용하지 않습니다.")

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise WebApiError(HTTPStatus.BAD_REQUEST, "요청 본문이 필요합니다.")

        body = self.rfile.read(content_length)
        try:
            decoded = body.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            raise WebApiError(HTTPStatus.BAD_REQUEST, "요청 본문이 올바른 UTF-8 형식이 아닙니다.")
        try:
            payload = json.loads(decoded)
        except (json.JSONDecodeError, ValueError):
            raise WebApiError(HTTPStatus.BAD_REQUEST, "JSON 요청 본문 형식이 올바르지 않습니다.")
        if not isinstance(payload, dict):
            raise WebApiError(HTTPStatus.BAD_REQUEST, "JSON 본문은 객체 형태여야 합니다.")
        return payload

    _STATIC_DIR = Path(__file__).with_name("static")
    _CONTROLLER_HTML = _CONTROLLER_DIR / "index.html"

    def _resolve_controller_asset(self, url_path: str) -> Path | None:
        relative = url_path[len("/controller-assets/"):].strip().lstrip("/")
        if not relative:
            return None
        if relative.startswith("css/"):
            root = (self._CONTROLLER_DIR / "css").resolve()
            local = relative[len("css/"):]
        elif relative.startswith("js/"):
            root = (self._CONTROLLER_DIR / "js").resolve()
            local = relative[len("js/"):]
        else:
            root = (self._CONTROLLER_DIR / "assets").resolve()
            local = relative
        candidate = (root / local).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
        if not candidate.is_file():
            return None
        return candidate

    def _serve_controller_html(self) -> None:
        if not self._CONTROLLER_HTML.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})
            return
        try:
            data = self._CONTROLLER_HTML.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _serve_controller_asset(self, url_path: str) -> None:
        file_path = self._resolve_controller_asset(url_path)
        if file_path is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})
            return
        content_type, _ = mimetypes.guess_type(file_path.name)
        if content_type is None:
            content_type = "application/octet-stream"
        try:
            data = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _serve_static(self, url_path: str) -> None:
        relative = url_path[len("/static/"):]
        if not relative or ".." in relative or relative.startswith("/"):
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})
            return
        file_path = self._STATIC_DIR / relative
        if not file_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})
            return
        content_type, _ = mimetypes.guess_type(file_path.name)
        if content_type is None:
            content_type = "application/octet-stream"
        try:
            data = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            return

    _REACT_DIST_DIR = Path(__file__).resolve().parent / "static" / "dist"

    def _serve_shipped_app(self) -> None:
        self._send_html(HTTPStatus.OK, self.server.service.render_index())

    def _serve_react_app(self) -> None:
        index_path = self._REACT_DIST_DIR / "index.html"
        if not index_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "React preview 빌드가 없습니다. app/frontend에서 npm run build를 실행해 주세요."}})
            return
        try:
            data = index_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _serve_react_asset(self, url_path: str) -> None:
        relative = url_path[len("/assets/"):]
        if not relative or ".." in relative or relative.startswith("/"):
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})
            return
        file_path = self._REACT_DIST_DIR / "assets" / relative
        if not file_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})
            return
        content_type, _ = mimetypes.guess_type(file_path.name)
        if content_type is None:
            content_type = "application/octet-stream"
        try:
            data = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_html(self, status: HTTPStatus, body: str) -> None:
        encoded = body.encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_json(self, status: int | HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_json_stream(self, events) -> None:
        try:
            self.send_response(int(HTTPStatus.OK))
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            for event in events:
                encoded = (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")
                self.wfile.write(encoded)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return


def build_parser() -> Any:
    import argparse

    parser = argparse.ArgumentParser(description="로컬 AI 비서 웹 셸을 실행합니다.")
    parser.add_argument("--host", default=None, help="바인드할 호스트입니다. 기본값은 LOCAL_AI_WEB_HOST 또는 127.0.0.1입니다.")
    parser.add_argument("--port", type=int, default=None, help="바인드할 포트입니다. 기본값은 LOCAL_AI_WEB_PORT 또는 8765입니다.")
    return parser


def _effective_web_host(*, args_host: str | None, settings: AppSettings) -> str:
    if args_host is not None:
        explicit_host = args_host
    elif settings.web_host != "127.0.0.1":
        explicit_host = settings.web_host
    else:
        explicit_host = ""
    return resolve_bind_host(explicit_host=explicit_host)


def main() -> int:
    args = build_parser().parse_args()
    settings = AppSettings.from_env()
    host = _effective_web_host(args_host=args.host, settings=settings)
    port = args.port or settings.web_port
    browser_host = browser_host_for_bind(host)
    fallback_host = windows_fallback_host()

    service = WebAppService(settings=settings)
    server = LocalOnlyHTTPServer((host, port), service)
    print(f"로컬 웹 셸이 http://{browser_host}:{port}/app 에서 실행 중입니다.")
    if host != browser_host:
        print(f"  Bind: {host}:{port} (WSL -> Windows 브라우저 접근용)")
    if fallback_host and fallback_host != browser_host:
        print(f"  Windows fallback: http://{fallback_host}:{port}/app")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n로컬 웹 셸을 종료합니다.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
