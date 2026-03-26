from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import queue
import threading
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from app.localization import localize_runtime_status_payload, localize_session, localize_text
from config.settings import AppSettings
from core.agent_loop import AgentLoop, AgentResponse, RequestCancelledError, UserRequest
from core.request_intents import classify_search_intent
from model_adapter.base import ModelAdapterError, ModelRuntimeStatus
from model_adapter.factory import build_model_adapter
from storage.session_store import SessionStore
from storage.task_log import TaskLogger
from storage.web_search_store import WebSearchStore
from tools.file_reader import FileReaderTool
from tools.file_search import FileSearchTool
from tools.web_search import WebSearchTool
from tools.write_note import WriteNoteTool


DEFAULT_SESSION_ID = "demo-session"


@dataclass(slots=True)
class WebApiError(RuntimeError):
    status_code: int
    message: str

    def __str__(self) -> str:
        return self.message


class WebAppService:
    def __init__(
        self,
        settings: AppSettings,
        *,
        template_path: str | None = None,
    ) -> None:
        self.settings = settings
        self.session_store = SessionStore(base_dir=settings.sessions_dir)
        self.task_logger = TaskLogger(path=settings.task_log_path)
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

    def submit_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        message_id = self._normalize_optional_text(payload.get("message_id"))
        feedback_label = self._normalize_feedback_label(payload.get("feedback_label"))
        feedback_reason = self._normalize_feedback_reason(payload.get("feedback_reason"))

        if not message_id:
            raise WebApiError(400, "피드백을 남길 메시지 ID가 필요합니다.")
        if not feedback_label:
            raise WebApiError(400, "피드백 종류는 helpful, unclear, incorrect 중 하나여야 합니다.")

        updated_message = self.session_store.update_message(
            session_id,
            message_id,
            {"feedback": {"label": feedback_label, **({"reason": feedback_reason} if feedback_reason else {})}},
        )
        if updated_message is None:
            raise WebApiError(404, "피드백을 남길 비서 메시지를 찾지 못했습니다.")

        self.task_logger.log(
            session_id=session_id,
            action="response_feedback_recorded",
            detail={
                "message_id": message_id,
                "feedback_label": feedback_label,
                "feedback_reason": feedback_reason,
            },
        )
        return {
            "ok": True,
            "message_id": message_id,
            "feedback_label": feedback_label,
            "feedback_reason": feedback_reason,
            "session": self._serialize_session(self.session_store.get_session(session_id)),
        }

    def handle_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._handle_chat_impl(payload)

    def cancel_stream(self, *, session_id: str | None, request_id: str | None) -> dict[str, Any]:
        normalized_session_id = self._normalize_session_id(session_id)
        normalized_request_id = self._normalize_optional_text(request_id)
        if not normalized_request_id:
            raise WebApiError(400, "취소할 요청 ID가 필요합니다.")

        key = self._stream_request_key(normalized_session_id, normalized_request_id)
        with self._active_stream_lock:
            cancel_event = self._active_stream_requests.get(key)
        if cancel_event is None:
            return {
                "ok": True,
                "cancelled": False,
                "session_id": normalized_session_id,
                "request_id": normalized_request_id,
                "message": "취소할 활성 스트리밍 요청을 찾지 못했습니다.",
            }

        cancel_event.set()
        self.task_logger.log(
            session_id=normalized_session_id,
            action="stream_cancel_requested",
            detail={"request_id": normalized_request_id},
        )
        return {
            "ok": True,
            "cancelled": True,
            "session_id": normalized_session_id,
            "request_id": normalized_request_id,
            "message": "스트리밍 취소를 요청했습니다.",
        }

    def stream_chat(self, payload: dict[str, Any]):
        event_queue: queue.Queue[dict[str, Any] | None] = queue.Queue()
        session_id = self._normalize_session_id(payload.get("session_id"))
        request_id = self._normalize_optional_text(payload.get("request_id")) or "request"
        cancel_event = threading.Event()
        stream_key = self._stream_request_key(session_id, request_id)

        with self._active_stream_lock:
            self._active_stream_requests[stream_key] = cancel_event

        def push_stream_event(event: dict[str, Any]) -> None:
            event_queue.put({"ok": True, **event})

        def worker() -> None:
            try:
                final_payload = self._handle_chat_impl(
                    payload,
                    stream_event_callback=push_stream_event,
                    meta_event_callback=push_stream_event,
                    cancel_requested=cancel_event.is_set,
                )
                event_queue.put({"ok": True, "event": "final", "data": final_payload})
            except RequestCancelledError:
                event_queue.put(
                    {
                        "ok": True,
                        "event": "cancelled",
                        "request_id": request_id,
                        "message": "요청을 취소했습니다. 현재까지 받은 응답만 화면에 남겨둡니다.",
                    }
                )
            except WebApiError as exc:
                event_queue.put(
                    {
                        "ok": False,
                        "event": "error",
                        "error": {"message": localize_text(exc.message)},
                        "status_code": int(exc.status_code),
                    }
                )
            except json.JSONDecodeError:
                event_queue.put(
                    {
                        "ok": False,
                        "event": "error",
                        "error": {"message": "JSON 요청 본문 형식이 올바르지 않습니다."},
                        "status_code": int(HTTPStatus.BAD_REQUEST),
                    }
                )
            except ModelAdapterError as exc:
                event_queue.put(
                    {
                        "ok": False,
                        "event": "error",
                        "error": {"message": localize_text(str(exc))},
                        "status_code": int(HTTPStatus.BAD_GATEWAY),
                    }
                )
            except Exception as exc:
                event_queue.put(
                    {
                        "ok": False,
                        "event": "error",
                        "error": {"message": localize_text(str(exc))},
                        "status_code": int(HTTPStatus.INTERNAL_SERVER_ERROR),
                    }
                )
            finally:
                with self._active_stream_lock:
                    self._active_stream_requests.pop(stream_key, None)
                event_queue.put(None)

        threading.Thread(target=worker, daemon=True).start()

        while True:
            item = event_queue.get()
            if item is None:
                break
            yield item

    def _handle_chat_impl(
        self,
        payload: dict[str, Any],
        *,
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
        meta_event_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        session_id = self._normalize_session_id(payload.get("session_id"))
        approved_approval_id = self._normalize_optional_text(payload.get("approved_approval_id"))
        rejected_approval_id = self._normalize_optional_text(payload.get("rejected_approval_id"))
        reissue_approval_id = self._normalize_optional_text(payload.get("reissue_approval_id"))
        source_path = self._normalize_optional_text(payload.get("source_path"))
        uploaded_file = self._parse_uploaded_file(payload.get("uploaded_file"))
        uploaded_search_files = self._parse_uploaded_search_files(payload.get("uploaded_search_files"))
        search_root = self._normalize_optional_text(payload.get("search_root"))
        search_query = self._normalize_optional_text(payload.get("search_query"))
        user_text = self._normalize_optional_text(payload.get("user_text"))
        load_web_search_record_id = self._normalize_optional_text(payload.get("load_web_search_record_id"))
        retry_feedback_label = self._normalize_feedback_label(payload.get("retry_feedback_label"))
        retry_feedback_reason = self._normalize_feedback_reason(payload.get("retry_feedback_reason"))
        retry_target_message_id = self._normalize_optional_text(payload.get("retry_target_message_id"))
        note_path = self._normalize_optional_text(payload.get("note_path"))
        save_summary = self._coerce_bool(payload.get("save_summary"))
        approved = self._coerce_bool(payload.get("approved"))
        search_only = self._coerce_bool(payload.get("search_only"))
        skip_preflight = self._coerce_bool(payload.get("skip_preflight"))
        selected_paths = self._parse_selected_paths(payload.get("selected_paths"))
        search_limit = self._parse_positive_int(payload.get("search_limit"), default=3)

        existing_permissions = self.session_store.get_permissions(session_id)
        raw_web_search_permission = payload.get("web_search_permission")
        if raw_web_search_permission is None:
            web_search_permission = self._normalize_web_search_permission(
                existing_permissions.get("web_search") or self.settings.web_search_permission
            )
        else:
            web_search_permission = self._normalize_web_search_permission(raw_web_search_permission)
        if existing_permissions.get("web_search") != web_search_permission:
            self.session_store.set_permissions(session_id, {"web_search": web_search_permission})
            self.task_logger.log(
                session_id=session_id,
                action="web_search_permission_updated",
                detail={"web_search": web_search_permission},
            )

        requested_approval_actions = [value for value in [approved_approval_id, rejected_approval_id, reissue_approval_id] if value]
        if len(requested_approval_actions) > 1:
            raise WebApiError(400, "승인 실행, 승인 취소, 승인 재발급은 동시에 요청할 수 없습니다.")

        if reissue_approval_id and not note_path:
            raise WebApiError(400, "승인을 다시 만들 때는 새 저장 경로를 함께 보내야 합니다.")

        if approved_approval_id or rejected_approval_id or reissue_approval_id:
            loop = AgentLoop(
                model=build_model_adapter(
                    provider="mock",
                    ollama_base_url=self.settings.ollama_base_url,
                    ollama_model=self.settings.ollama_model,
                    ollama_timeout_seconds=self.settings.ollama_timeout_seconds,
                ),
                session_store=self.session_store,
                task_logger=self.task_logger,
                tools=self._build_tools(),
                notes_dir=self.settings.notes_dir,
                web_search_store=self.web_search_store,
            )
            response = loop.handle(
                UserRequest(
                    user_text="",
                    session_id=session_id,
                    approved_approval_id=approved_approval_id,
                    rejected_approval_id=rejected_approval_id,
                    reissue_approval_id=reissue_approval_id,
                    metadata={
                        **({"note_path": note_path} if note_path else {}),
                        "web_search_permission": web_search_permission,
                    },
                ),
                phase_event_callback=meta_event_callback,
                cancel_requested=cancel_requested,
            )
            response.response_origin = self._build_response_origin(
                provider="system",
                model_name=None,
                response_kind="approval",
            )
            if meta_event_callback:
                meta_event_callback(
                    {
                        "event": "response_origin",
                        "response_origin": self._serialize_response_origin(response.response_origin),
                    }
                )
            self.session_store.update_last_message(
                session_id,
                {"response_origin": dict(response.response_origin)},
            )
            session_payload = self.session_store.get_session(session_id)
            return {
                "ok": True,
                "response": self._serialize_response(response),
                "runtime_status": None,
                "session": self._serialize_session(session_payload),
            }

        if (search_root or uploaded_search_files) and not search_query:
            raise WebApiError(400, "검색 루트를 입력했다면 검색어도 함께 입력해야 합니다.")
        if search_query and not search_root and not uploaded_search_files:
            raise WebApiError(400, "검색어를 입력했다면 검색 루트도 함께 입력하거나 폴더를 선택해야 합니다.")
        if (
            not source_path
            and uploaded_file is None
            and not ((search_root or uploaded_search_files) and search_query)
            and not user_text
            and not load_web_search_record_id
        ):
            raise WebApiError(400, "파일 경로, 검색 루트/검색어, 일반 메시지 중 하나는 입력해야 합니다.")

        provider = self._normalize_optional_text(payload.get("provider")) or self.settings.model_provider
        model_name = self._normalize_optional_text(payload.get("model")) or self.settings.ollama_model
        base_url = self._normalize_optional_text(payload.get("base_url")) or self.settings.ollama_base_url
        has_search_request = bool(search_query and (search_root or uploaded_search_files))
        search_intent = classify_search_intent(user_text)
        explicit_web_search_request = search_intent.kind == "explicit_web"
        implicit_web_search_query = search_intent.query if search_intent.kind == "live_latest" else None
        external_fact_web_query = search_intent.query if search_intent.kind == "external_fact" else None
        suggested_web_query = search_intent.suggestion_query if search_intent.kind == "none" else None
        needs_model = (
            not (has_search_request and search_only)
            and not explicit_web_search_request
            and not implicit_web_search_query
            and not external_fact_web_query
            and not suggested_web_query
            and not load_web_search_record_id
        )

        if provider == "ollama" and needs_model and not model_name:
            raise WebApiError(400, "Ollama를 사용할 때는 모델명을 입력해야 합니다.")

        model = build_model_adapter(
            provider=provider,
            ollama_base_url=base_url,
            ollama_model=model_name,
            ollama_timeout_seconds=self.settings.ollama_timeout_seconds,
        )
        if meta_event_callback and not skip_preflight and needs_model:
            self._emit_phase(
                meta_event_callback,
                phase="runtime_preflight",
                title="런타임 상태 확인 중",
                detail=f"{provider} 프로바이더와 모델 준비 상태를 확인하는 중입니다.",
                note="첫 요청에서는 모델 로딩 여부 확인 때문에 잠시 시간이 걸릴 수 있습니다.",
            )
        runtime_status = self._maybe_preflight_model(
            model=model,
            skip_preflight=skip_preflight,
            needs_model=needs_model,
        )
        localized_runtime_status = localize_runtime_status_payload(asdict(runtime_status)) if runtime_status else None
        response_origin = self._build_response_origin(
            provider=provider,
            model_name=model_name,
            response_kind="assistant",
        )
        if meta_event_callback and localized_runtime_status:
            meta_event_callback(
                {
                    "event": "runtime_status",
                    "runtime_status": localized_runtime_status,
                }
            )
            self._emit_phase(
                meta_event_callback,
                phase="runtime_ready",
                title="런타임 확인 완료",
                detail=f"{provider} 프로바이더가 준비되었고 이제 실제 응답 생성을 시작합니다.",
                note="이제 파일 읽기나 문서 검색, 모델 응답 단계로 넘어갑니다.",
            )
        if meta_event_callback:
            meta_event_callback(
                {
                    "event": "response_origin",
                    "response_origin": self._serialize_response_origin(response_origin),
                }
            )

        loop = AgentLoop(
            model=model,
            session_store=self.session_store,
            task_logger=self.task_logger,
            tools=self._build_tools(),
            notes_dir=self.settings.notes_dir,
            web_search_store=self.web_search_store,
        )
        request = UserRequest(
            user_text=self._build_user_text(
                user_text=user_text,
                source_path=source_path,
                uploaded_file=uploaded_file,
                uploaded_search_files=uploaded_search_files,
                search_root=search_root,
                search_query=search_query,
                load_web_search_record_id=load_web_search_record_id,
            ),
            session_id=session_id,
            approved=approved,
            metadata=self._build_metadata(
                source_path=source_path,
                uploaded_file=uploaded_file,
                uploaded_search_files=uploaded_search_files,
                search_root=search_root,
                search_query=search_query,
                search_limit=search_limit,
                search_only=search_only,
                selected_paths=selected_paths,
                save_summary=save_summary,
                note_path=note_path,
                web_search_permission=web_search_permission,
                load_web_search_record_id=load_web_search_record_id,
                retry_feedback_label=retry_feedback_label,
                retry_feedback_reason=retry_feedback_reason,
                retry_target_message_id=retry_target_message_id,
            ),
        )
        response = loop.handle(
            request,
            stream_event_callback=stream_event_callback,
            phase_event_callback=meta_event_callback,
            cancel_requested=cancel_requested,
        )
        if response.response_origin is None:
            response.response_origin = response_origin
        elif meta_event_callback and response.response_origin != response_origin:
            meta_event_callback(
                {
                    "event": "response_origin",
                    "response_origin": self._serialize_response_origin(response.response_origin),
                }
            )
        self.session_store.update_last_message(
            session_id,
            {"response_origin": dict(response.response_origin)},
        )
        session_payload = self.session_store.get_session(session_id)
        return {
            "ok": True,
            "response": self._serialize_response(response),
            "runtime_status": localized_runtime_status,
            "session": self._serialize_session(session_payload),
        }

    def _build_tools(self) -> dict[str, Any]:
        reader = FileReaderTool()
        allowed_roots = [str(Path.cwd()), self.settings.notes_dir]
        return {
            "read_file": reader,
            "search_files": FileSearchTool(reader=reader),
            "search_web": WebSearchTool(timeout_seconds=self.settings.web_search_timeout_seconds),
            "write_note": WriteNoteTool(allowed_roots=allowed_roots),
        }

    def _maybe_preflight_model(
        self,
        *,
        model: Any,
        skip_preflight: bool,
        needs_model: bool,
    ) -> ModelRuntimeStatus | None:
        if skip_preflight or not needs_model:
            return None

        status = model.health_check()
        if not status.reachable:
            raise WebApiError(503, localize_text(status.detail))
        if not status.configured_model_available:
            raise WebApiError(503, localize_text(status.detail))
        return status

    def _emit_phase(
        self,
        callback: Callable[[dict[str, Any]], None] | None,
        *,
        phase: str,
        title: str,
        detail: str,
        note: str = "",
    ) -> None:
        if callback is None:
            return
        callback(
            {
                "event": "phase",
                "phase": phase,
                "title": title,
                "detail": detail,
                "note": note,
            }
        )

    def _stream_request_key(self, session_id: str, request_id: str) -> str:
        return f"{session_id}:{request_id}"

    def _build_user_text(
        self,
        *,
        user_text: str | None,
        source_path: str | None,
        uploaded_file: dict[str, Any] | None,
        uploaded_search_files: list[dict[str, Any]] | None,
        search_root: str | None,
        search_query: str | None,
        load_web_search_record_id: str | None,
    ) -> str:
        if user_text:
            return user_text
        if load_web_search_record_id:
            return "최근 웹 검색 기록을 다시 불러와 주세요."
        if uploaded_search_files and search_query:
            folder_label = str(uploaded_search_files[0].get("root_label") or "선택 폴더")
            return f"{folder_label}에서 '{search_query}'를 검색하고 결과를 요약해 주세요."
        if search_root and search_query:
            return f"{search_root}에서 '{search_query}'를 검색하고 결과를 요약해 주세요."
        if uploaded_file:
            file_name = str(uploaded_file.get("name") or "selected-file")
            return f"{file_name} 파일을 요약해 주세요."
        if source_path:
            return f"{source_path} 파일을 요약해 주세요."
        return "안녕하세요"

    def _build_metadata(
        self,
        *,
        source_path: str | None,
        uploaded_file: dict[str, Any] | None,
        uploaded_search_files: list[dict[str, Any]] | None,
        search_root: str | None,
        search_query: str | None,
        search_limit: int,
        search_only: bool,
        selected_paths: list[str] | None,
        save_summary: bool,
        note_path: str | None,
        web_search_permission: str,
        load_web_search_record_id: str | None,
        retry_feedback_label: str | None,
        retry_feedback_reason: str | None,
        retry_target_message_id: str | None,
    ) -> dict[str, Any]:
        if (search_root or uploaded_search_files) and search_query:
            return {
                "search_root": search_root,
                "uploaded_search_files": uploaded_search_files,
                "search_query": search_query,
                "search_result_limit": search_limit,
                "search_only": search_only,
                "search_selected_paths": selected_paths,
                "save_summary": save_summary,
                "note_path": note_path,
                "web_search_permission": web_search_permission,
                "load_web_search_record_id": load_web_search_record_id,
                "retry_feedback_label": retry_feedback_label,
                "retry_feedback_reason": retry_feedback_reason,
                "retry_target_message_id": retry_target_message_id,
            }
        return {
            "source_path": source_path,
            "uploaded_file": uploaded_file,
            "save_summary": save_summary,
            "note_path": note_path,
            "web_search_permission": web_search_permission,
            "load_web_search_record_id": load_web_search_record_id,
            "retry_feedback_label": retry_feedback_label,
            "retry_feedback_reason": retry_feedback_reason,
            "retry_target_message_id": retry_target_message_id,
        }

    def _parse_uploaded_file(self, raw_value: Any) -> dict[str, Any] | None:
        if raw_value is None:
            return None
        parsed = self._parse_uploaded_file_record(raw_value, require_relative_path=False)
        return {
            "name": parsed["name"],
            "mime_type": parsed["mime_type"],
            "size_bytes": parsed["size_bytes"],
            "content_bytes": parsed["content_bytes"],
        }

    def _parse_uploaded_search_files(self, raw_value: Any) -> list[dict[str, Any]] | None:
        if raw_value is None:
            return None
        if not isinstance(raw_value, list):
            raise WebApiError(400, "선택 폴더 정보는 JSON 배열이어야 합니다.")
        if not raw_value:
            return None
        if len(raw_value) > 50:
            raise WebApiError(400, "선택 폴더에는 최대 50개 파일까지만 담아 주세요.")

        parsed_files: list[dict[str, Any]] = []
        total_bytes = 0
        for item in raw_value:
            parsed = self._parse_uploaded_file_record(item, require_relative_path=True)
            total_bytes += parsed["size_bytes"]
            if total_bytes > 20 * 1024 * 1024:
                raise WebApiError(400, "선택 폴더 전체 크기가 20MB를 넘습니다. 더 작은 폴더로 나눠서 다시 시도해 주세요.")
            parsed_files.append(parsed)
        return parsed_files

    def _parse_uploaded_file_record(
        self,
        raw_value: Any,
        *,
        require_relative_path: bool,
    ) -> dict[str, Any]:
        if not isinstance(raw_value, dict):
            raise WebApiError(400, "선택 파일 정보는 JSON 객체여야 합니다.")

        name = self._normalize_optional_text(raw_value.get("name"))
        content_base64 = self._normalize_optional_text(raw_value.get("content_base64"))
        mime_type = self._normalize_optional_text(raw_value.get("mime_type"))
        relative_path = self._normalize_optional_text(raw_value.get("relative_path"))
        provided_root_label = self._normalize_optional_text(raw_value.get("root_label"))
        size_bytes_raw = raw_value.get("size_bytes")

        if not name or not content_base64:
            raise WebApiError(400, "선택 파일에는 name과 content_base64가 필요합니다.")
        if require_relative_path and not relative_path:
            raise WebApiError(400, "선택 폴더 파일에는 relative_path가 필요합니다.")

        if not isinstance(size_bytes_raw, int) or size_bytes_raw < 0:
            raise WebApiError(400, "선택 파일 크기는 0 이상의 정수여야 합니다.")

        try:
            content_bytes = base64.b64decode(content_base64.encode("ascii"), validate=True)
        except Exception as exc:
            raise WebApiError(400, "선택 파일 본문(base64)을 해석할 수 없습니다.") from exc

        if len(content_bytes) != size_bytes_raw:
            raise WebApiError(400, "선택 파일 크기 정보가 실제 본문과 다릅니다.")
        if len(content_bytes) > 10 * 1024 * 1024:
            raise WebApiError(400, "선택 파일 크기가 10MB를 넘습니다. 경로 입력 방식이나 더 작은 파일로 다시 시도해 주세요.")

        normalized_relative_path = relative_path or ""
        root_label = provided_root_label or ""
        if relative_path:
            normalized_relative_path = relative_path.replace("\\", "/")
            root_label = root_label or normalized_relative_path.split("/", 1)[0]
        return {
            "name": name,
            "relative_path": normalized_relative_path,
            "root_label": root_label,
            "mime_type": mime_type or "",
            "size_bytes": size_bytes_raw,
            "content_bytes": content_bytes,
        }

    def _serialize_response(
        self,
        response: AgentResponse,
    ) -> dict[str, Any]:
        return {
            "status": response.status,
            "text": localize_text(response.text),
            "actions_taken": response.actions_taken,
            "requires_approval": response.requires_approval,
            "proposed_note_path": response.proposed_note_path,
            "saved_note_path": response.saved_note_path,
            "web_search_record_path": response.web_search_record_path,
            "selected_source_paths": response.selected_source_paths,
            "note_preview": localize_text(response.note_preview) if response.note_preview else None,
            "approval": self._serialize_approval(response.approval),
            "active_context": self._serialize_active_context(response.active_context),
            "follow_up_suggestions": [localize_text(str(item)) for item in response.follow_up_suggestions],
            "response_origin": self._serialize_response_origin(response.response_origin),
            "evidence": self._serialize_evidence(response.evidence),
            "summary_chunks": self._serialize_summary_chunks(response.summary_chunks),
        }

    def _serialize_session(self, session: dict[str, Any]) -> dict[str, Any]:
        localized = localize_session(session)
        localized["pending_approvals"] = [
            self._serialize_approval(approval)
            for approval in session.get("pending_approvals", [])
            if isinstance(approval, dict)
        ]
        localized["active_context"] = self._serialize_active_context(session.get("active_context"))
        localized["permissions"] = self._serialize_permissions(session.get("permissions"))
        localized["web_search_history"] = self._serialize_web_search_history(session.get("session_id"))
        return localized

    def _serialize_web_search_history(self, session_id: Any) -> list[dict[str, Any]]:
        normalized_session_id = self._normalize_optional_text(session_id)
        if not normalized_session_id:
            return []
        history = self.web_search_store.list_session_record_summaries(normalized_session_id, limit=8)
        serialized: list[dict[str, Any]] = []
        for item in history:
            serialized.append(
                {
                    "record_id": str(item.get("record_id") or ""),
                    "query": localize_text(str(item.get("query") or "")),
                    "created_at": str(item.get("created_at") or ""),
                    "result_count": int(item.get("result_count") or 0),
                    "page_count": int(item.get("page_count") or 0),
                    "record_path": str(item.get("record_path") or ""),
                    "summary_head": localize_text(str(item.get("summary_head") or "")),
                    "pages_preview": [
                        {
                            "title": localize_text(str(page.get("title") or "")),
                            "url": str(page.get("url") or ""),
                            "excerpt": localize_text(str(page.get("excerpt") or "")),
                            "text_preview": localize_text(str(page.get("text_preview") or "")),
                            "char_count": int(page.get("char_count") or 0),
                        }
                        for page in item.get("pages_preview", [])
                        if isinstance(page, dict)
                    ],
                }
            )
        return serialized

    def _serialize_approval(self, approval: dict[str, Any] | None) -> dict[str, Any] | None:
        if approval is None:
            return None
        preview_markdown = approval.get("preview_markdown")
        return {
            "approval_id": approval.get("approval_id"),
            "kind": approval.get("kind"),
            "requested_path": approval.get("requested_path"),
            "overwrite": bool(approval.get("overwrite", False)),
            "preview_markdown": localize_text(str(preview_markdown)) if isinstance(preview_markdown, str) else "",
            "source_paths": [str(path) for path in approval.get("source_paths", [])],
            "created_at": approval.get("created_at"),
        }

    def _serialize_active_context(self, context: dict[str, Any] | None) -> dict[str, Any] | None:
        if context is None:
            return None
        return {
            "kind": context.get("kind"),
            "label": context.get("label"),
            "source_paths": [str(path) for path in context.get("source_paths", [])],
            "summary_hint": localize_text(str(context.get("summary_hint", ""))),
            "suggested_prompts": [localize_text(str(item)) for item in context.get("suggested_prompts", [])],
            "record_path": str(context.get("record_path") or ""),
        }

    def _build_response_origin(
        self,
        *,
        provider: str,
        model_name: str | None,
        response_kind: str,
    ) -> dict[str, Any]:
        normalized_provider = (provider or "system").strip().lower()
        if normalized_provider == "ollama":
            return {
                "provider": "ollama",
                "badge": "OLLAMA",
                "label": "실제 로컬 모델 응답",
                "model": model_name or "선택형 로컬 모델",
                "kind": response_kind,
            }
        if normalized_provider == "mock":
            return {
                "provider": "mock",
                "badge": "MOCK",
                "label": "모의 데모 응답",
                "model": model_name or "내장 모의 어댑터",
                "kind": response_kind,
            }
        return {
            "provider": "system",
            "badge": "SYSTEM",
            "label": "시스템 응답",
            "model": None,
            "kind": response_kind,
        }

    def _serialize_response_origin(self, origin: dict[str, Any] | None) -> dict[str, Any] | None:
        if origin is None:
            return None
        return {
            "provider": str(origin.get("provider") or "system"),
            "badge": str(origin.get("badge") or "SYSTEM"),
            "label": str(origin.get("label") or "시스템 응답"),
            "model": origin.get("model"),
            "kind": str(origin.get("kind") or "assistant"),
        }

    def _serialize_evidence(self, evidence: list[dict[str, Any]] | None) -> list[dict[str, str]]:
        serialized: list[dict[str, str]] = []
        for item in evidence or []:
            if not isinstance(item, dict):
                continue
            snippet = str(item.get("snippet") or "").strip()
            if not snippet:
                continue
            source_path = str(item.get("source_path") or "")
            serialized.append(
                {
                    "label": str(item.get("label") or "문서 근거"),
                    "source_name": str(item.get("source_name") or Path(source_path).name or "(출처 없음)"),
                    "source_path": source_path,
                    "snippet": snippet,
                }
            )
        return serialized

    def _serialize_summary_chunks(self, summary_chunks: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for item in summary_chunks or []:
            if not isinstance(item, dict):
                continue
            selected_line = str(item.get("selected_line") or "").strip()
            if not selected_line:
                continue
            source_path = str(item.get("source_path") or "")
            serialized.append(
                {
                    "chunk_id": str(item.get("chunk_id") or ""),
                    "chunk_index": int(item.get("chunk_index") or 0),
                    "total_chunks": int(item.get("total_chunks") or 0),
                    "source_path": source_path,
                    "source_name": str(item.get("source_name") or Path(source_path).name or "(출처 없음)"),
                    "selected_line": selected_line,
                }
            )
        return serialized

    def _serialize_permissions(self, permissions: Any) -> dict[str, str]:
        web_search_permission = "disabled"
        if isinstance(permissions, dict):
            web_search_permission = self._normalize_web_search_permission(permissions.get("web_search"))
        return {
            "web_search": web_search_permission,
            "web_search_label": self._web_search_permission_label(web_search_permission),
        }

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
        if lowered not in {"helpful", "unclear", "incorrect"}:
            return None
        return lowered

    def _normalize_feedback_reason(self, raw_value: Any) -> str | None:
        normalized = self._normalize_optional_text(raw_value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered not in {"factual_error", "irrelevant_result", "context_miss", "awkward_tone"}:
            return None
        return lowered

    def _normalize_web_search_permission(self, raw_value: Any) -> str:
        if not isinstance(raw_value, str):
            return "disabled"
        normalized = raw_value.strip().lower()
        if normalized in {"disabled", "approval", "enabled"}:
            return normalized
        return "disabled"

    def _web_search_permission_label(self, permission: Any) -> str:
        normalized = self._normalize_web_search_permission(permission)
        if normalized == "approval":
            return "승인 필요 · 읽기 전용 검색"
        if normalized == "enabled":
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

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(HTTPStatus.OK, self.server.service.render_index())
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
        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/chat", "/api/chat/stream", "/api/chat/cancel", "/api/feedback"}:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": {"message": "요청한 경로를 찾을 수 없습니다."}})
            return

        try:
            self._validate_same_origin()
            payload = self._read_json_body()
            if parsed.path == "/api/feedback":
                response = self.server.service.submit_feedback(payload)
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
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise WebApiError(HTTPStatus.BAD_REQUEST, "JSON 본문은 객체 형태여야 합니다.")
        return payload

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


def main() -> int:
    args = build_parser().parse_args()
    settings = AppSettings.from_env()
    host = args.host or settings.web_host
    port = args.port or settings.web_port

    service = WebAppService(settings=settings)
    server = LocalOnlyHTTPServer((host, port), service)
    print(f"로컬 웹 셸이 http://{host}:{port} 에서 실행 중입니다.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n로컬 웹 셸을 종료합니다.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
