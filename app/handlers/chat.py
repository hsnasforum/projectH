from __future__ import annotations

import base64
import json
import queue
import threading
from dataclasses import asdict
from http import HTTPStatus
from pathlib import Path
from typing import Any, Callable

from app.localization import localize_runtime_status_payload, localize_text
from app.errors import WebApiError
from core.agent_loop import AgentLoop, AgentResponse, RequestCancelledError, UserRequest
from core.contracts import (
    ArtifactKind,
    ResponseOriginKind,
    ResponseOriginProvider,
    SearchIntentKind,
    StreamEventType,
)
from core.request_intents import classify_search_intent
from model_adapter.base import ModelAdapterError, ModelRuntimeStatus
from model_adapter.factory import build_model_adapter
from tools.file_reader import FileReaderTool
from tools.file_search import FileSearchTool
from tools.web_search import WebSearchTool
from tools.write_note import WriteNoteTool


class ChatHandlerMixin:
    """Chat / streaming core methods extracted from WebAppService."""

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
                event_queue.put({"ok": True, "event": StreamEventType.FINAL, "data": final_payload})
            except RequestCancelledError:
                event_queue.put(
                    {
                        "ok": True,
                        "event": StreamEventType.CANCELLED,
                        "request_id": request_id,
                        "message": "요청을 취소했습니다. 현재까지 받은 응답만 화면에 남겨둡니다.",
                    }
                )
            except WebApiError as exc:
                event_queue.put(
                    {
                        "ok": False,
                        "event": StreamEventType.ERROR,
                        "error": {"message": localize_text(exc.message)},
                        "status_code": int(exc.status_code),
                    }
                )
            except json.JSONDecodeError:
                event_queue.put(
                    {
                        "ok": False,
                        "event": StreamEventType.ERROR,
                        "error": {"message": "JSON 요청 본문 형식이 올바르지 않습니다."},
                        "status_code": int(HTTPStatus.BAD_REQUEST),
                    }
                )
            except ModelAdapterError as exc:
                event_queue.put(
                    {
                        "ok": False,
                        "event": StreamEventType.ERROR,
                        "error": {"message": localize_text(str(exc))},
                        "status_code": int(HTTPStatus.BAD_GATEWAY),
                    }
                )
            except Exception as exc:
                event_queue.put(
                    {
                        "ok": False,
                        "event": StreamEventType.ERROR,
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
        corrected_save_message_id = self._normalize_optional_text(payload.get("corrected_save_message_id"))
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

        requested_action_ids = [
            value
            for value in [
                approved_approval_id,
                rejected_approval_id,
                reissue_approval_id,
                corrected_save_message_id,
            ]
            if value
        ]
        if len(requested_action_ids) > 1:
            raise WebApiError(400, "승인 실행, 승인 취소, 승인 재발급, 수정본 저장 요청은 동시에 처리할 수 없습니다.")

        if reissue_approval_id and not note_path:
            raise WebApiError(400, "승인을 다시 만들 때는 새 저장 경로를 함께 보내야 합니다.")

        if approved_approval_id or rejected_approval_id or reissue_approval_id or corrected_save_message_id:
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
                artifact_store=self.artifact_store,
                preference_store=self.preference_store,
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
                        **({"corrected_save_message_id": corrected_save_message_id} if corrected_save_message_id else {}),
                        "web_search_permission": web_search_permission,
                    },
                ),
                phase_event_callback=meta_event_callback,
                cancel_requested=cancel_requested,
            )
            response.response_origin = self._build_response_origin(
                provider=ResponseOriginProvider.SYSTEM,
                model_name=None,
                response_kind=ResponseOriginKind.APPROVAL,
            )
            if meta_event_callback:
                meta_event_callback(
                    {
                        "event": StreamEventType.RESPONSE_ORIGIN,
                        "response_origin": self._serialize_response_origin(response.response_origin),
                    }
                )
            snapshot = self._synchronize_original_response_snapshot(response)
            self.session_store.update_last_message(
                session_id,
                {
                    "response_origin": dict(response.response_origin),
                    **({"original_response_snapshot": dict(snapshot)} if snapshot else {}),
                },
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
        explicit_web_search_request = search_intent.kind == SearchIntentKind.EXPLICIT_WEB
        implicit_web_search_query = search_intent.query if search_intent.kind == SearchIntentKind.LIVE_LATEST else None
        external_fact_web_query = search_intent.query if search_intent.kind == SearchIntentKind.EXTERNAL_FACT else None
        suggested_web_query = search_intent.suggestion_query if search_intent.kind == SearchIntentKind.NONE else None
        needs_model = (
            not (has_search_request and search_only)
            and not explicit_web_search_request
            and not implicit_web_search_query
            and not external_fact_web_query
            and not suggested_web_query
            and not load_web_search_record_id
        )

        # "auto" means router decides per-task; use medium (7B) as base model
        if model_name == "auto" and provider == "ollama":
            model_name = "qwen2.5:7b"
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
            response_kind=ResponseOriginKind.ASSISTANT,
        )
        if meta_event_callback and localized_runtime_status:
            meta_event_callback(
                {
                    "event": StreamEventType.RUNTIME_STATUS,
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
                    "event": StreamEventType.RESPONSE_ORIGIN,
                    "response_origin": self._serialize_response_origin(response_origin),
                }
            )

        model_router = self._build_model_router()
        loop = AgentLoop(
            model=model,
            session_store=self.session_store,
            task_logger=self.task_logger,
            tools=self._build_tools(),
            notes_dir=self.settings.notes_dir,
            web_search_store=self.web_search_store,
            artifact_store=self.artifact_store,
            preference_store=self.preference_store,
            model_router=model_router,
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
        response = self._apply_reviewed_memory_effects(session_id, response, stream_event_callback)
        if response.response_origin is None:
            response.response_origin = response_origin
        elif meta_event_callback and response.response_origin != response_origin:
            meta_event_callback(
                {
                    "event": StreamEventType.RESPONSE_ORIGIN,
                    "response_origin": self._serialize_response_origin(response.response_origin),
                }
            )
        snapshot = self._synchronize_original_response_snapshot(response)
        self.session_store.update_last_message(
            session_id,
            {
                "response_origin": dict(response.response_origin),
                **({"original_response_snapshot": dict(snapshot)} if snapshot else {}),
                **(
                    {"applied_preference_ids": [p["fingerprint"] for p in response.applied_preferences]}
                    if response.applied_preferences
                    else {}
                ),
            },
        )
        session_payload = self.session_store.get_session(session_id)
        return {
            "ok": True,
            "response": self._serialize_response(response),
            "runtime_status": localized_runtime_status,
            "session": self._serialize_session(session_payload),
        }

    def _apply_reviewed_memory_effects(
        self,
        session_id: str,
        response: AgentResponse,
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> AgentResponse:
        session = self.session_store.get_session(session_id)
        active_effects = session.get("reviewed_memory_active_effects")
        if not isinstance(active_effects, list) or not active_effects:
            return response
        if not response.text or not response.text.strip():
            return response

        correction_effects = [
            effect for effect in active_effects
            if isinstance(effect, dict)
            and str(effect.get("effect_kind") or "").strip() == "reviewed_memory_correction_pattern"
        ]
        if not correction_effects:
            return response

        notes: list[str] = []
        for effect in correction_effects:
            reason = str(effect.get("operator_reason_or_note") or "").strip()
            fingerprint = str(effect.get("aggregate_fingerprint") or "").strip()[:16]
            if reason:
                notes.append(f"[검토 메모 활성] {reason} (패턴 {fingerprint})")
            else:
                notes.append(f"[검토 메모 활성] 교정 패턴이 적용되었습니다. (패턴 {fingerprint})")

        prefix = "\n".join(notes)
        updated_text = f"{prefix}\n\n{response.text}"
        response.text = updated_text

        if stream_event_callback:
            stream_event_callback({"event": StreamEventType.TEXT_REPLACE, "text": updated_text})

        return response

    def _build_model_router(self) -> Any:
        """Build model router config if provider is ollama."""
        if self.settings.model_provider != "ollama":
            return None
        try:
            from model_adapter.router import ModelConfig
            return ModelConfig()  # uses defaults: 3b/7b/14b
        except Exception:
            return None

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
                "event": StreamEventType.PHASE,
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

    def _build_response_origin(
        self,
        *,
        provider: str,
        model_name: str | None,
        response_kind: str,
    ) -> dict[str, Any]:
        normalized_provider = (provider or ResponseOriginProvider.SYSTEM).strip().lower()
        if normalized_provider == ResponseOriginProvider.OLLAMA:
            return {
                "provider": ResponseOriginProvider.OLLAMA,
                "badge": "OLLAMA",
                "label": "실제 로컬 모델 응답",
                "model": model_name or "선택형 로컬 모델",
                "kind": response_kind,
            }
        if normalized_provider == ResponseOriginProvider.MOCK:
            return {
                "provider": ResponseOriginProvider.MOCK,
                "badge": "MOCK",
                "label": "모의 데모 응답",
                "model": model_name or "내장 모의 어댑터",
                "kind": response_kind,
            }
        return {
            "provider": ResponseOriginProvider.SYSTEM,
            "badge": "SYSTEM",
            "label": "시스템 응답",
            "model": None,
            "kind": response_kind,
        }

    def _synchronize_original_response_snapshot(self, response: AgentResponse) -> dict[str, Any] | None:
        if (
            response.original_response_snapshot is None
            and (
                response.artifact_kind != ArtifactKind.GROUNDED_BRIEF
                or not response.artifact_id
                or (not response.evidence and not response.summary_chunks)
            )
        ):
            return None

        snapshot = {
            "artifact_id": response.artifact_id,
            "artifact_kind": response.artifact_kind,
            "draft_text": response.text,
            "source_paths": [str(path) for path in response.selected_source_paths if str(path).strip()],
            "response_origin": dict(response.response_origin) if isinstance(response.response_origin, dict) else None,
            "summary_chunks_snapshot": [dict(item) for item in response.summary_chunks if isinstance(item, dict)],
            "evidence_snapshot": [dict(item) for item in response.evidence if isinstance(item, dict)],
        }
        response.original_response_snapshot = snapshot
        return snapshot
