from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Callable, Dict, Mapping
from urllib.parse import urlparse
from uuid import uuid4

from core.approval import (
    SAVE_CONTENT_SOURCE_CORRECTED_TEXT,
    SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT,
    ApprovalRequest,
    build_approval_reason_record,
)
from core.contracts import (
    ArtifactKind,
    AnswerMode,
    CoverageStatus,
    FreshnessRisk,
    FollowUpIntent,
    ResponseStatus,
    SaveContentSource,
    SearchIntentKind,
    SourceRole,
    SourceType,
    StreamEventType,
)
from core.request_intents import classify_search_intent
from core.source_policy import build_source_policy, score_source_for_mode
from core.web_claims import (
    CORE_ENTITY_SLOTS,
    TRUSTED_CLAIM_SOURCE_ROLES,
    ClaimRecord,
    merge_claim_records,
    summarize_slot_coverage,
)
from model_adapter.base import (
    FOLLOW_UP_INTENT_ACTION_ITEMS,
    FOLLOW_UP_INTENT_GENERAL,
    FOLLOW_UP_INTENT_KEY_POINTS,
    FOLLOW_UP_INTENT_MEMO,
    ModelAdapter,
    SummaryNoteDraft,
)
from storage.session_store import SessionStore
from storage.task_log import TaskLogger
from tools.file_reader import OcrRequiredError
from tools.file_search import FileSearchResult


@dataclass
class UserRequest:
    user_text: str
    session_id: str
    approved: bool = False
    approved_approval_id: str | None = None
    rejected_approval_id: str | None = None
    reissue_approval_id: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    text: str
    message_id: str | None = None
    source_message_id: str | None = None
    status: str = ResponseStatus.ANSWER
    actions_taken: list[str] = field(default_factory=list)
    requires_approval: bool = False
    proposed_note_path: str | None = None
    saved_note_path: str | None = None
    selected_source_paths: list[str] = field(default_factory=list)
    note_preview: str | None = None
    approval: dict[str, Any] | None = None
    active_context: dict[str, Any] | None = None
    follow_up_suggestions: list[str] = field(default_factory=list)
    response_origin: dict[str, Any] | None = None
    evidence: list[dict[str, str]] = field(default_factory=list)
    summary_chunks: list[dict[str, Any]] = field(default_factory=list)
    claim_coverage: list[dict[str, Any]] = field(default_factory=list)
    claim_coverage_progress_summary: str | None = None
    web_search_record_path: str | None = None
    artifact_id: str | None = None
    artifact_kind: str | None = None
    original_response_snapshot: dict[str, Any] | None = None
    corrected_outcome: dict[str, Any] | None = None
    approval_reason_record: dict[str, Any] | None = None
    save_content_source: str | None = None
    search_results: list[dict[str, str]] = field(default_factory=list)


class RequestCancelledError(RuntimeError):
    pass


class AgentLoop:
    def __init__(
        self,
        model: ModelAdapter,
        session_store: SessionStore,
        task_logger: TaskLogger,
        tools: Mapping[str, Any],
        notes_dir: str = "data/notes",
        web_search_store: Any | None = None,
    ) -> None:
        self.model = model
        self.session_store = session_store
        self.task_logger = task_logger
        self.tools = tools
        self.notes_dir = Path(notes_dir)
        self.web_search_store = web_search_store

    def _new_grounded_brief_artifact_id(self) -> str:
        return f"artifact-{uuid4().hex[:12]}"

    def _new_message_id(self) -> str:
        return f"msg-{uuid4().hex[:12]}"

    def _build_original_response_snapshot(self, response: AgentResponse) -> dict[str, Any] | None:
        if response.artifact_kind != ArtifactKind.GROUNDED_BRIEF or not response.artifact_id:
            return None
        if not response.evidence and not response.summary_chunks:
            return None

        return {
            "artifact_id": response.artifact_id,
            "artifact_kind": response.artifact_kind,
            "draft_text": response.text,
            "source_paths": [str(path) for path in response.selected_source_paths if str(path).strip()],
            "response_origin": dict(response.response_origin) if isinstance(response.response_origin, dict) else None,
            "summary_chunks_snapshot": [dict(item) for item in response.summary_chunks if isinstance(item, dict)],
            "evidence_snapshot": [dict(item) for item in response.evidence if isinstance(item, dict)],
        }

    def _build_grounded_brief_response(self, **kwargs: Any) -> AgentResponse:
        response = AgentResponse(**kwargs)
        response.original_response_snapshot = self._build_original_response_snapshot(response)
        return response

    def _build_accepted_as_is_outcome(
        self,
        *,
        artifact_id: str | None,
        saved_note_path: str | None,
        approval_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not artifact_id or not saved_note_path:
            return None
        outcome = {
            "outcome": "accepted_as_is",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "artifact_id": artifact_id,
            "saved_note_path": saved_note_path,
        }
        if approval_id:
            outcome["approval_id"] = approval_id
        return outcome

    def _log_corrected_outcome_recorded(self, session_id: str, corrected_outcome: dict[str, Any]) -> None:
        self.task_logger.log(
            session_id=session_id,
            action="corrected_outcome_recorded",
            detail={
                "outcome": corrected_outcome.get("outcome"),
                "recorded_at": corrected_outcome.get("recorded_at"),
                "artifact_id": corrected_outcome.get("artifact_id"),
                "source_message_id": corrected_outcome.get("source_message_id"),
                "approval_id": corrected_outcome.get("approval_id"),
                "saved_note_path": corrected_outcome.get("saved_note_path"),
            },
        )

    def _resolve_artifact_source_message_id(self, session_id: str, artifact_id: str | None) -> str | None:
        normalized_artifact_id = str(artifact_id or "").strip()
        if not normalized_artifact_id:
            return None
        source_message = self.session_store.find_artifact_source_message(session_id, normalized_artifact_id)
        if not isinstance(source_message, dict):
            return None
        source_message_id = str(source_message.get("message_id") or "").strip()
        return source_message_id or None

    def _build_approval_reason_record(
        self,
        *,
        session_id: str,
        artifact_id: str | None,
        approval_id: str | None,
        source_message_id: str | None = None,
        reason_scope: str,
        reason_label: str,
        reason_note: str | None = None,
    ) -> dict[str, Any] | None:
        normalized_artifact_id = str(artifact_id or "").strip()
        normalized_approval_id = str(approval_id or "").strip()
        resolved_source_message_id = str(source_message_id or "").strip() or self._resolve_artifact_source_message_id(
            session_id,
            normalized_artifact_id,
        )
        if not normalized_artifact_id or not normalized_approval_id or not resolved_source_message_id:
            return None
        return build_approval_reason_record(
            reason_scope=reason_scope,
            reason_label=reason_label,
            reason_note=reason_note,
            artifact_id=normalized_artifact_id,
            artifact_kind=ArtifactKind.GROUNDED_BRIEF,
            source_message_id=resolved_source_message_id,
            approval_id=normalized_approval_id,
        )

    def _find_message_by_id(self, session_id: str, message_id: str | None) -> dict[str, Any] | None:
        normalized_message_id = str(message_id or "").strip()
        if not normalized_message_id:
            return None
        session = self.session_store.get_session(session_id)
        messages = session.get("messages", [])
        for message in reversed(messages):
            if str(message.get("message_id") or "").strip() != normalized_message_id:
                continue
            return dict(message)
        return None

    def _extract_grounded_brief_source_paths(self, message: dict[str, Any] | None) -> list[str]:
        if not isinstance(message, dict):
            return []
        snapshot = message.get("original_response_snapshot")
        if isinstance(snapshot, dict):
            source_paths = [str(path) for path in snapshot.get("source_paths", []) if str(path).strip()]
            if source_paths:
                return source_paths
        return [str(path) for path in message.get("selected_source_paths", []) if str(path).strip()]

    def _extract_search_query_from_label(self, label: str | None) -> str | None:
        normalized_label = str(label or "").strip()
        match = re.match(r"^'(?P<query>.+)' 검색 결과$", normalized_label)
        if not match:
            return None
        search_query = str(match.group("query") or "").strip()
        return search_query or None

    def _latest_pending_note_path_for_artifact(self, session_id: str, artifact_id: str | None) -> str | None:
        normalized_artifact_id = str(artifact_id or "").strip()
        if not normalized_artifact_id:
            return None
        session = self.session_store.get_session(session_id)
        for approval in reversed(session.get("pending_approvals", [])):
            if not isinstance(approval, dict):
                continue
            if str(approval.get("artifact_id") or "").strip() != normalized_artifact_id:
                continue
            requested_path = str(approval.get("requested_path") or "").strip()
            if requested_path:
                return requested_path
        return None

    def _resolve_corrected_save_note_path(
        self,
        *,
        request: UserRequest,
        source_message: dict[str, Any],
    ) -> str | None:
        requested_note_path = str(request.metadata.get("note_path") or "").strip()
        if requested_note_path:
            return requested_note_path

        artifact_id = str(source_message.get("artifact_id") or "").strip() or None
        pending_path = self._latest_pending_note_path_for_artifact(request.session_id, artifact_id)
        if pending_path:
            return pending_path

        saved_note_path = str(source_message.get("saved_note_path") or "").strip()
        if saved_note_path:
            return saved_note_path

        corrected_outcome = source_message.get("corrected_outcome")
        if isinstance(corrected_outcome, dict):
            corrected_saved_path = str(corrected_outcome.get("saved_note_path") or "").strip()
            if corrected_saved_path:
                return corrected_saved_path

        proposed_note_path = str(source_message.get("proposed_note_path") or "").strip()
        if proposed_note_path:
            return proposed_note_path

        source_paths = self._extract_grounded_brief_source_paths(source_message)
        if len(source_paths) == 1:
            return self._build_note_path(request, source_paths[0])

        active_context = source_message.get("active_context")
        if isinstance(active_context, dict) and str(active_context.get("kind") or "").strip() == "search":
            search_query = self._extract_search_query_from_label(active_context.get("label"))
            if search_query:
                return self._build_search_note_path(request, search_query)

        return None

    def _request_corrected_save_bridge(self, request: UserRequest) -> AgentResponse:
        source_message_id = str(request.metadata.get("corrected_save_message_id") or "").strip()
        if not source_message_id:
            return AgentResponse(
                text="저장 요청을 만들 수정본 원문 메시지 ID가 없습니다.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        source_message = self._find_message_by_id(request.session_id, source_message_id)
        if not isinstance(source_message, dict):
            return AgentResponse(
                text="수정본 저장 요청을 만들 grounded-brief 원문 응답을 찾지 못했습니다.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        artifact_id = str(source_message.get("artifact_id") or "").strip()
        if (
            source_message.get("role") != "assistant"
            or str(source_message.get("artifact_kind") or "").strip() != ArtifactKind.GROUNDED_BRIEF
            or not artifact_id
            or not isinstance(source_message.get("original_response_snapshot"), dict)
        ):
            return AgentResponse(
                text="수정본 저장 요청은 grounded-brief 원문 응답에서만 만들 수 있습니다.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        corrected_text = str(source_message.get("corrected_text") or "").replace("\r\n", "\n").strip()
        if not corrected_text:
            return AgentResponse(
                text="기록된 수정본이 없습니다. 먼저 수정본 기록을 눌러 주세요.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
                artifact_id=artifact_id,
                artifact_kind=ArtifactKind.GROUNDED_BRIEF,
                source_message_id=source_message_id,
            )

        note_path = self._resolve_corrected_save_note_path(
            request=request,
            source_message=source_message,
        )
        if not note_path:
            return AgentResponse(
                text="수정본 저장 경로를 정할 수 없습니다. 먼저 원래 저장 요청을 만들거나 저장된 경로가 있는 응답에서 다시 시도해 주세요.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
                artifact_id=artifact_id,
                artifact_kind=ArtifactKind.GROUNDED_BRIEF,
                source_message_id=source_message_id,
            )

        source_paths = self._extract_grounded_brief_source_paths(source_message)
        approval = self._request_save_note_approval(
            session_id=request.session_id,
            note_path=note_path,
            note_body=corrected_text,
            source_paths=source_paths,
            artifact_id=artifact_id,
            source_message_id=source_message_id,
            save_content_source=SAVE_CONTENT_SOURCE_CORRECTED_TEXT,
        )
        return AgentResponse(
            text=(
                f"현재 기록된 수정본 스냅샷을 {approval.requested_path}에 저장하려면 승인이 필요합니다. "
                "이 승인 미리보기는 요청 시점 그대로 고정됩니다."
            ),
            status=ResponseStatus.NEEDS_APPROVAL,
            actions_taken=["approval_requested"],
            requires_approval=True,
            proposed_note_path=approval.requested_path,
            selected_source_paths=source_paths,
            note_preview=approval.preview_markdown,
            approval=approval.to_public_dict(),
            artifact_id=artifact_id,
            artifact_kind=ArtifactKind.GROUNDED_BRIEF,
            source_message_id=source_message_id,
            save_content_source=approval.save_content_source,
        )

    def _append_response_message(self, session_id: str, response: AgentResponse) -> dict[str, Any]:
        stored_message = self.session_store.append_message(session_id, self._assistant_message(response))
        stored_message_id = str(stored_message.get("message_id") or "").strip()
        if stored_message_id:
            response.message_id = stored_message_id
        stored_source_message_id = str(stored_message.get("source_message_id") or "").strip()
        if stored_source_message_id:
            response.source_message_id = stored_source_message_id
        stored_approval = stored_message.get("approval")
        if isinstance(stored_approval, dict):
            response.approval = dict(stored_approval)
            if not response.source_message_id:
                approval_source_message_id = str(stored_approval.get("source_message_id") or "").strip()
                if approval_source_message_id:
                    response.source_message_id = approval_source_message_id
        approval_reason_record = stored_message.get("approval_reason_record")
        if isinstance(approval_reason_record, dict):
            response.approval_reason_record = dict(approval_reason_record)
            if isinstance(response.approval, dict):
                response.approval["approval_reason_record"] = dict(approval_reason_record)
        corrected_outcome = stored_message.get("corrected_outcome")
        if isinstance(corrected_outcome, dict):
            response.corrected_outcome = dict(corrected_outcome)
            if not response.source_message_id:
                corrected_source_message_id = str(corrected_outcome.get("source_message_id") or "").strip()
                if corrected_source_message_id:
                    response.source_message_id = corrected_source_message_id
            self._log_corrected_outcome_recorded(session_id, corrected_outcome)
        return stored_message

    def _extract_search_query(self, request: UserRequest) -> str | None:
        search_query = request.metadata.get("search_query")
        if isinstance(search_query, str) and search_query.strip():
            return search_query.strip()
        return None

    def _extract_search_root(self, request: UserRequest) -> str | None:
        search_root = request.metadata.get("search_root")
        if isinstance(search_root, str) and search_root.strip():
            return search_root.strip()
        return None

    def _wants_search_only(self, request: UserRequest) -> bool:
        return bool(request.metadata.get("search_only"))

    def _extract_search_selected_indices(self, request: UserRequest) -> list[int] | None:
        value = request.metadata.get("search_selected_indices")
        if not isinstance(value, list):
            return None

        indices: list[int] = []
        for item in value:
            if isinstance(item, int) and item > 0:
                indices.append(item)
        return indices or None

    def _extract_search_selected_paths(self, request: UserRequest) -> list[str] | None:
        value = request.metadata.get("search_selected_paths")
        if not isinstance(value, list):
            return None

        selected_paths: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                selected_paths.append(item.strip())
        return selected_paths or None

    def _extract_retry_feedback_label(self, request: UserRequest) -> str | None:
        value = request.metadata.get("retry_feedback_label")
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower()
        if normalized in {"helpful", "unclear", "incorrect"}:
            return normalized
        return None

    def _extract_retry_feedback_reason(self, request: UserRequest) -> str | None:
        value = request.metadata.get("retry_feedback_reason")
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower()
        if normalized in {"factual_error", "irrelevant_result", "context_miss", "awkward_tone"}:
            return normalized
        return None

    def _extract_retry_target_message_id(self, request: UserRequest) -> str | None:
        value = request.metadata.get("retry_target_message_id")
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _format_uploaded_search_root_label(self, uploaded_files: list[dict[str, Any]] | None) -> str:
        if not uploaded_files:
            return "선택한 폴더"

        first = uploaded_files[0]
        root_label = str(first.get("root_label") or "").strip()
        if root_label:
            return root_label
        relative_path = str(first.get("relative_path") or "").strip()
        if relative_path:
            return Path(relative_path).parts[0]
        return "선택한 폴더"

    def _search_result_limit(self, request: UserRequest) -> int:
        limit = request.metadata.get("search_result_limit")
        if isinstance(limit, int) and limit > 0:
            return limit
        return 3

    def _extract_source_path(self, request: UserRequest) -> str | None:
        metadata_path = request.metadata.get("source_path")
        if isinstance(metadata_path, str) and metadata_path.strip():
            return metadata_path

        match = re.search(r"([^\s]+(?:\.[A-Za-z0-9_-]+))", request.user_text)
        if match:
            candidate = match.group(1)
            if self._looks_like_path(candidate):
                return candidate
        return None

    def _extract_uploaded_search_files(self, request: UserRequest) -> list[dict[str, Any]] | None:
        uploaded_files = request.metadata.get("uploaded_search_files")
        if not isinstance(uploaded_files, list):
            return None

        parsed: list[dict[str, Any]] = []
        for item in uploaded_files:
            if not isinstance(item, dict):
                continue
            relative_path = item.get("relative_path")
            content_bytes = item.get("content_bytes")
            if not isinstance(relative_path, str) or not relative_path.strip():
                continue
            if not isinstance(content_bytes, (bytes, bytearray)):
                continue
            parsed.append(
                {
                    "name": str(item.get("name") or Path(relative_path).name),
                    "relative_path": relative_path.strip(),
                    "root_label": str(item.get("root_label") or ""),
                    "mime_type": str(item.get("mime_type") or ""),
                    "size_bytes": int(item.get("size_bytes") or len(content_bytes)),
                    "content_bytes": bytes(content_bytes),
                }
            )
        return parsed or None

    def _extract_uploaded_file(self, request: UserRequest) -> dict[str, Any] | None:
        uploaded_file = request.metadata.get("uploaded_file")
        if not isinstance(uploaded_file, dict):
            return None

        name = uploaded_file.get("name")
        content_bytes = uploaded_file.get("content_bytes")
        if not isinstance(name, str) or not name.strip():
            return None
        if not isinstance(content_bytes, (bytes, bytearray)):
            return None

        return {
            "name": name.strip(),
            "content_bytes": bytes(content_bytes),
            "mime_type": str(uploaded_file.get("mime_type") or ""),
            "size_bytes": int(uploaded_file.get("size_bytes") or len(content_bytes)),
        }

    def _has_explicit_source_path(self, request: UserRequest) -> bool:
        metadata_path = request.metadata.get("source_path")
        return isinstance(metadata_path, str) and bool(metadata_path.strip())

    def _looks_like_path(self, candidate: str) -> bool:
        normalized = candidate.strip()
        if not normalized:
            return False
        if "/" in normalized or "\\" in normalized:
            return True
        if normalized.startswith(("./", "../", "~/")):
            return True
        if re.match(r"^[A-Za-z]:[\\/]", normalized):
            return True
        return False

    def _wants_summary_save(self, request: UserRequest) -> bool:
        requested = request.metadata.get("save_summary")
        if isinstance(requested, bool):
            return requested
        lowered = request.user_text.lower()
        return "save" in lowered and "summary" in lowered

    def _build_note_path(self, request: UserRequest, source_path: str) -> str:
        requested_note_path = request.metadata.get("note_path")
        if isinstance(requested_note_path, str) and requested_note_path.strip():
            return requested_note_path

        source_name = Path(source_path).stem
        return str(self.notes_dir / f"{source_name}-summary.md")

    def _build_search_note_path(self, request: UserRequest, search_query: str) -> str:
        requested_note_path = request.metadata.get("note_path")
        if isinstance(requested_note_path, str) and requested_note_path.strip():
            return requested_note_path

        slug = re.sub(r"[^a-zA-Z0-9]+", "-", search_query.strip()).strip("-").lower()
        if not slug:
            slug = "search"
        return str(self.notes_dir / f"search-{slug}-summary.md")

    def _format_search_results(self, results: list[FileSearchResult]) -> str:
        lines = ["검색 결과:"]
        for index, result in enumerate(results, start=1):
            lines.extend(
                [
                    f"{index}. {result.path}",
                    f"   일치 방식: {result.matched_on}",
                    f"   발췌: {result.snippet or '(발췌 없음)'}",
                ]
            )
        return "\n".join(lines)

    def _extract_skipped_ocr_paths(self) -> list[str]:
        search_tool = self.tools.get("search_files")
        if search_tool is None:
            return []

        stats = getattr(search_tool, "last_run_stats", None)
        if stats is None:
            return []

        skipped_paths = getattr(stats, "skipped_ocr_paths", None)
        if not isinstance(skipped_paths, list):
            return []
        return [path for path in skipped_paths if isinstance(path, str)]

    def _format_search_ocr_notice(self, skipped_paths: list[str] | None = None) -> str | None:
        skipped_paths = skipped_paths if skipped_paths is not None else self._extract_skipped_ocr_paths()
        if not skipped_paths:
            return None

        count = len(skipped_paths)
        examples = ", ".join(skipped_paths[:2])
        if count > 2:
            examples = f"{examples}, ..."
        return (
            f"이 MVP에서는 OCR을 지원하지 않습니다. 검색 중 스캔본 또는 이미지형 PDF {count}개를 건너뛰었습니다. "
            f"예시: {examples}"
        )

    def _extract_query_snippet(self, *, text: str, query: str, radius: int = 80) -> str:
        lowered = text.lower()
        index = lowered.find(query.lower())
        if index == -1:
            return ""

        start = max(0, index - radius)
        end = min(len(text), index + len(query) + radius)
        snippet = " ".join(text[start:end].split())
        if start > 0:
            snippet = f"...{snippet}"
        if end < len(text):
            snippet = f"{snippet}..."
        return snippet

    def _search_uploaded_files(
        self,
        *,
        uploaded_files: list[dict[str, Any]],
        query: str,
        max_results: int,
    ) -> tuple[list[FileSearchResult], dict[str, Any], list[str], list[str]]:
        matches: list[FileSearchResult] = []
        read_results_by_path: dict[str, Any] = {}
        skipped_ocr_paths: list[str] = []
        failed_paths: list[str] = []
        lowered_query = query.lower()

        for uploaded_file in uploaded_files:
            relative_path = str(uploaded_file.get("relative_path") or uploaded_file.get("name") or "").strip()
            if not relative_path:
                continue
            try:
                read_result = self.tools["read_file"].run_uploaded(
                    name=relative_path,
                    content_bytes=bytes(uploaded_file.get("content_bytes") or b""),
                    mime_type=str(uploaded_file.get("mime_type") or ""),
                )
            except OcrRequiredError:
                skipped_ocr_paths.append(relative_path)
                continue
            except Exception:
                failed_paths.append(relative_path)
                continue

            read_results_by_path[relative_path] = read_result
            if lowered_query in Path(relative_path).name.lower():
                matches.append(
                    FileSearchResult(
                        path=relative_path,
                        matched_on="filename",
                        snippet=f"Filename matched query: {Path(relative_path).name}",
                    )
                )
            elif lowered_query in read_result.text.lower():
                matches.append(
                    FileSearchResult(
                        path=relative_path,
                        matched_on="content",
                        snippet=self._extract_query_snippet(text=read_result.text, query=query),
                    )
                )
            if len(matches) >= max_results:
                break

        return sorted(matches, key=lambda item: item.path), read_results_by_path, skipped_ocr_paths, failed_paths

    def _append_notice(self, text: str, notice: str | None) -> str:
        if not notice:
            return text
        return f"{text}\n\n참고: {notice}"

    def _format_ocr_guidance(self, source_path: str | None, error_text: str) -> str:
        path_text = source_path or "이 PDF"
        return "\n".join(
            [
                f"{path_text} 파일은 요약할 수 없습니다.",
                error_text,
                "",
                "다음 단계:",
                "1. 텍스트 레이어가 있는 검색 가능한 PDF로 다시 저장하거나 내보낸 뒤 다시 시도하세요.",
                "2. 다른 로컬 도구에서 OCR을 수행한 뒤, OCR 처리된 PDF나 텍스트 파일로 다시 시도하세요.",
                "3. 원래의 텍스트 기반 원본 문서가 있다면 그 파일로 다시 시도하세요.",
            ]
        )

    def _select_search_results_by_path(
        self,
        *,
        results: list[FileSearchResult],
        requested_paths: list[str],
    ) -> list[FileSearchResult]:
        selected_results: list[FileSearchResult] = []
        seen_paths: set[str] = set()
        for requested_path in requested_paths:
            exact_matches = [item for item in results if item.path == requested_path]
            if len(exact_matches) == 1:
                match = exact_matches[0]
            else:
                suffix_matches = [item for item in results if item.path.endswith(requested_path)]
                if len(suffix_matches) == 1:
                    match = suffix_matches[0]
                elif not suffix_matches:
                    raise ValueError(f"선택 경로 '{requested_path}'에 해당하는 검색 결과가 없습니다.")
                else:
                    candidate_paths = ", ".join(item.path for item in suffix_matches)
                    raise ValueError(f"선택 경로 '{requested_path}'가 여러 검색 결과와 겹칩니다: {candidate_paths}")

            if match.path in seen_paths:
                continue
            selected_results.append(match)
            seen_paths.add(match.path)
        return selected_results

    def _select_search_results(
        self,
        *,
        results: list[FileSearchResult],
        request: UserRequest,
    ) -> list[FileSearchResult]:
        selected_paths = self._extract_search_selected_paths(request)
        if selected_paths:
            return self._select_search_results_by_path(
                results=results,
                requested_paths=selected_paths,
            )

        selected_indices = self._extract_search_selected_indices(request)
        if not selected_indices:
            return results

        selected_results: list[FileSearchResult] = []
        seen: set[int] = set()
        for index in selected_indices:
            if index in seen:
                continue
            if index < 1 or index > len(results):
                raise ValueError(f"선택 번호 {index}가 검색 결과 범위를 벗어났습니다. 전체 결과 수: {len(results)}.")
            selected_results.append(results[index - 1])
            seen.add(index)
        return selected_results

    def _format_selected_sources(self, results: list[FileSearchResult]) -> str:
        lines = ["선택된 출처:"]
        for index, result in enumerate(results, start=1):
            lines.extend(
                [
                    f"{index}. {result.path}",
                    f"   일치 방식: {result.matched_on}",
                    f"   발췌: {result.snippet or '(발췌 없음)'}",
                ]
            )
        return "\n".join(lines)

    def _build_note_preview(self, note_body: str, max_chars: int = 1200) -> str:
        if len(note_body) <= max_chars:
            return note_body
        return note_body[:max_chars].rstrip() + "\n\n...[미리보기 생략]"

    def _follow_up_suggestions_for_file(self, source_path: str) -> list[str]:
        return [
            "현재 문서 핵심 3줄만 다시 정리해 주세요.",
            "현재 문서에서 실행할 일만 뽑아 주세요.",
            "현재 문서 내용을 메모 형식으로 다시 써 주세요.",
        ]

    def _follow_up_suggestions_for_search(self, search_query: str) -> list[str]:
        return [
            f"'{search_query}' 관련 문서들의 공통점과 차이를 정리해 주세요.",
            f"'{search_query}' 결과를 바탕으로 실행 항목을 뽑아 주세요.",
            f"'{search_query}' 내용을 짧은 메모 형식으로 다시 써 주세요.",
        ]

    def _summarize_hint(self, text: str, max_chars: int = 240) -> str:
        compact = " ".join(text.split())
        if len(compact) <= max_chars:
            return compact
        return compact[:max_chars].rstrip() + "..."

    def _normalize_summary_source_type(self, source_type: str) -> str:
        return "search_results" if source_type == "search_results" else "local_document"

    def _build_individual_chunk_summary_prompt(
        self,
        *,
        source_label: str,
        chunk_text: str,
        summary_source_type: str = "local_document",
    ) -> str:
        normalized_summary_source_type = self._normalize_summary_source_type(summary_source_type)
        excerpt_label = "Selected search-result excerpt:" if normalized_summary_source_type == "search_results" else "Document excerpt:"
        lines = [
            "Summary mode: chunk_note",
            f"Summary source type: {normalized_summary_source_type}",
            f"Source label: {source_label}",
        ]
        if normalized_summary_source_type == "search_results":
            lines.extend(
                [
                    "Write one concise Korean chunk note from the selected search-result excerpt below.",
                    "Treat it as one source-backed evidence chunk within a larger search-result synthesis.",
                    "Prioritize source-backed facts, meaningful differences, and explicit actions or decisions visible in this excerpt.",
                    "Do not retell it like a narrative scene or describe the task itself.",
                ]
            )
        else:
            lines.extend(
                [
                    "Write one concise Korean chunk note from the document excerpt below.",
                    "Treat it as one part of a larger local document and preserve the relevant flow or state changes from this excerpt.",
                    "Prioritize what this part actually says or what happens over memorable wording.",
                    "If the text is narrative or fiction, summarize major characters or actors, key events, conflict changes, and the ending state of this part.",
                    "If the text is informational or argumentative, summarize the topic, main points, decisions or actions, and conclusion of this part.",
                    "STRICT: Only include events, facts, and conclusions that appear explicitly in the excerpt. Do not add events that did not happen, substitute different words for specific terms (e.g. replacing '전시' with '공연'), or state relationship outcomes or plot conclusions beyond what the text actually shows.",
                ]
            )
        lines.extend(
            [
                "Return only concise Korean plain text with no heading or bullet label.",
                "Do not mention chunk numbers.",
                "",
                excerpt_label,
                chunk_text.strip(),
            ]
        )
        return "\n".join(lines).strip()

    def _build_short_summary_prompt(
        self,
        *,
        source_label: str,
        text: str,
        summary_source_type: str = "local_document",
    ) -> str:
        normalized_summary_source_type = self._normalize_summary_source_type(summary_source_type)
        excerpt_label = "Selected search-result text:" if normalized_summary_source_type == "search_results" else "Document text:"
        lines = [
            "Summary mode: short_summary",
            f"Summary source type: {normalized_summary_source_type}",
            f"Source label: {source_label}",
        ]
        if normalized_summary_source_type == "search_results":
            lines.extend(
                [
                    "Write one concise Korean synthesis from the selected search-result text below.",
                    "Treat it as a summary of selected local search results, not as one narrative document.",
                    "Prioritize shared facts, meaningful differences, explicit actions or decisions, and the grounded conclusion supported by the selected results.",
                    "Do not retell it like a narrative scene or describe the task itself.",
                ]
            )
        else:
            lines.extend(
                [
                    "Write one concise Korean summary from the document text below.",
                    "Treat it as a local document summary and preserve the relevant document flow or state changes even when the text is short.",
                    "Prioritize what the document actually says or what happens over memorable wording.",
                    "If the text is narrative or fiction, summarize major characters or actors, key events, conflict changes, and the ending state in order.",
                    "If the text is informational or argumentative, summarize the topic, main points, decisions or actions, and conclusion.",
                    "STRICT: Only include events, facts, and conclusions that appear explicitly in the text. Do not add events that did not happen, substitute different words for specific terms (e.g. replacing '전시' with '공연'), or state relationship outcomes or plot conclusions beyond what the text actually shows.",
                ]
            )
        lines.extend(
            [
                "Return only concise Korean plain text with no heading or bullet label.",
                "Do not describe the task itself or mention an artificial mode.",
                "",
                excerpt_label,
                text.strip(),
            ]
        )
        return "\n".join(lines).strip()

    def _build_chunk_summary_reduce_prompt(
        self,
        *,
        source_label: str,
        chunk_summaries: list[dict[str, Any]],
        reduce_source_type: str = "local_document",
    ) -> str:
        normalized_reduce_source_type = self._normalize_summary_source_type(reduce_source_type)
        lines = [
            "Summary mode: merged_chunk_outline",
            f"Summary source type: {normalized_reduce_source_type}",
            f"Source label: {source_label}",
        ]
        if normalized_reduce_source_type == "search_results":
            lines.extend(
                [
                    "Write one concise Korean synthesis from the selected search-result notes below.",
                    "Prioritize shared facts, meaningful differences, key actions or decisions, and the grounded conclusion across the selected results.",
                    "Treat the notes as source-backed search findings, not as scenes in a narrative.",
                    "Prefer source-backed synthesis over vivid wording or isolated lines.",
                ]
            )
        else:
            lines.extend(
                [
                    "Write one concise Korean summary from the chunk notes below.",
                    "Prioritize what the document actually says or what happens over memorable wording.",
                    "If the text is narrative or fiction, summarize major characters or actors, key events, conflict changes, and the ending state in order.",
                    "If the text is informational or argumentative, summarize the topic, main points, decisions or actions, and conclusion.",
                    "STRICT: Only include events, facts, and conclusions that appear in the chunk notes. Do not add events that did not happen, substitute different words for specific terms, or state relationship outcomes or plot conclusions beyond what the notes actually contain.",
                ]
            )
        lines.extend(
            [
            "Do not mention chunk numbers or describe the task itself.",
            "",
            ]
        )

        added = 0
        for index, chunk_summary in enumerate(chunk_summaries, start=1):
            summary_text = str(chunk_summary.get("summary") or "").strip()
            if not summary_text:
                continue
            summary_text = re.sub(r"^\[[^\]]+\]\s*", "", summary_text)
            summary_text = re.sub(r"^[*-]\s*", "", summary_text)
            summary_text = self._summarize_hint(summary_text, max_chars=220)
            if not summary_text:
                continue
            lines.append(f"Chunk note {index}: {summary_text}")
            added += 1

        if not added:
            selected_entries = self._select_summary_chunk_entries(
                chunk_summaries=chunk_summaries,
                max_lines=4,
                summary_source_type=reduce_source_type,
            )
            for index, (line, _) in enumerate(selected_entries, start=1):
                cleaned = self._summarize_hint(line, max_chars=220)
                if cleaned:
                    lines.append(f"Chunk note {index}: {cleaned}")

        return "\n".join(lines).strip()

    def _chunk_text_for_retrieval(
        self,
        *,
        source_path: str,
        text: str,
        chunk_size: int = 900,
        overlap: int = 140,
        max_chunks: int = 40,
    ) -> list[dict[str, str]]:
        normalized = text.replace("\r\n", "\n")
        if not normalized.strip():
            return []

        step = max(1, chunk_size - overlap)
        chunks: list[dict[str, str]] = []
        for index, start in enumerate(range(0, len(normalized), step), start=1):
            chunk_text = normalized[start : start + chunk_size].strip()
            if not chunk_text:
                continue
            chunks.append(
                {
                    "chunk_id": f"chunk-{index}",
                    "source_path": source_path,
                    "text": chunk_text,
                }
            )
            if len(chunks) >= max_chunks:
                break
        return chunks

    def _chunk_text_for_summary(
        self,
        *,
        source_path: str,
        text: str,
        lines_per_chunk: int = 32,
        overlap_lines: int = 6,
        max_chunks: int = 12,
    ) -> list[dict[str, str]]:
        normalized = text.replace("\r\n", "\n")
        if not normalized.strip():
            return []

        prepared_lines: list[str] = []
        for line in normalized.splitlines():
            stripped = line.rstrip()
            if not stripped:
                prepared_lines.append("")
                continue
            if len(stripped) <= 420:
                prepared_lines.append(stripped)
                continue
            for start in range(0, len(stripped), 360):
                prepared_lines.append(stripped[start : start + 360])

        step = max(1, lines_per_chunk - overlap_lines)
        all_chunks: list[dict[str, str]] = []
        for index, start in enumerate(range(0, len(prepared_lines), step), start=1):
            chunk_text = "\n".join(prepared_lines[start : start + lines_per_chunk]).strip()
            if not chunk_text:
                continue
            all_chunks.append(
                {
                    "chunk_id": f"summary-chunk-{index}",
                    "source_path": source_path,
                    "text": chunk_text,
                }
            )
        if len(all_chunks) <= max_chunks:
            return all_chunks

        seen_indices: set[int] = set()
        forced_indices = [
            0,
            max(0, (len(all_chunks) // 2) - 1),
            len(all_chunks) // 2,
            len(all_chunks) - 1,
        ]
        for index in forced_indices:
            index = max(0, min(index, len(all_chunks) - 1))
            if index in seen_indices:
                continue
            seen_indices.add(index)
            if len(seen_indices) >= max_chunks:
                break

        step_size = max(1, (len(all_chunks) - 1) / max(max_chunks - 1, 1))
        for offset in range(max_chunks):
            if len(seen_indices) >= max_chunks:
                break
            index = round(offset * step_size)
            index = max(0, min(index, len(all_chunks) - 1))
            if index in seen_indices:
                continue
            seen_indices.add(index)

        if len(seen_indices) < max_chunks:
            for index, chunk in enumerate(all_chunks):
                if index in seen_indices:
                    continue
                seen_indices.add(index)
                if len(seen_indices) >= max_chunks:
                    break
        return [all_chunks[index] for index in sorted(seen_indices)]

    def _select_summary_chunk_entries(
        self,
        *,
        chunk_summaries: list[dict[str, Any]],
        max_lines: int = 4,
        summary_source_type: str = "local_document",
    ) -> list[tuple[str, dict[str, Any]]]:
        if not chunk_summaries:
            return []
        if len(chunk_summaries) == 1:
            summary_text = str(chunk_summaries[0].get("summary") or "").strip()
            if summary_text:
                return [(summary_text, chunk_summaries[0])]
            return []

        normalized_summary_source_type = self._normalize_summary_source_type(summary_source_type)
        selected_entries: list[tuple[str, dict[str, Any]]] = []
        seen: set[str] = set()
        preferred_indices = [0, len(chunk_summaries) // 2, len(chunk_summaries) - 1]
        priority_keywords = {
            "핵심": 6,
            "결정": 6,
            "원칙": 5,
            "목표": 5,
            "결론": 5,
            "승인": 5,
            "유지": 4,
            "로컬": 3,
            "해야": 3,
            "필요": 3,
            "권고": 3,
            "실행": 3,
            "다음": 2,
            "검토": 2,
            "확정": 2,
            "정리": 2,
            "구현": 2,
            "추가": 1,
        }
        if normalized_summary_source_type == "search_results":
            priority_keywords.update(
                {
                    "공통": 7,
                    "종합": 6,
                    "차이": 6,
                    "다르": 5,
                    "우선": 5,
                    "조정": 4,
                    "강조": 4,
                    "범위": 3,
                    "근거": 3,
                }
            )
            penalty_keywords = {
                "갈등": 2,
                "관계": 2,
                "감정": 1,
                "장면": 1,
            }
        else:
            priority_keywords.update(
                {
                    "갈등": 5,
                    "관계": 4,
                    "변화": 4,
                    "마지막": 4,
                    "끝": 4,
                    "신호": 3,
                    "감정": 3,
                    "사건": 3,
                    "인물": 2,
                    "말하": 2,
                    "드러": 2,
                }
            )
            penalty_keywords: dict[str, int] = {}

        def _evidence_lines(chunk_summary: dict[str, Any]) -> list[str]:
            lines: list[str] = []
            for item in chunk_summary.get("evidence", []) or []:
                if not isinstance(item, dict):
                    continue
                snippet = self._clean_evidence_line(str(item.get("snippet") or ""), max_chars=160)
                if len(snippet) < 6 or self._is_metadata_line(snippet):
                    continue
                lines.append(snippet)
            return lines

        def _candidate_lines(summary_text: str) -> list[str]:
            lines: list[str] = []
            for piece in re.split(r"\n+|(?<=[.!?])\s+", summary_text):
                cleaned = self._clean_evidence_line(piece, max_chars=160)
                if len(cleaned) < 6 or self._is_metadata_line(cleaned):
                    continue
                lines.append(cleaned)
            return lines

        def _line_priority(line: str) -> int:
            score = 0
            for keyword, weight in priority_keywords.items():
                if keyword in line:
                    score += weight
            for keyword, weight in penalty_keywords.items():
                if keyword in line:
                    score -= weight
            if len(line) >= 20:
                score += 1
            if any(keyword in line for keyword in ["도입", "마무리"]):
                score -= 1
            return score

        def _best_priority_line(lines: list[str]) -> str | None:
            scored = [
                (index, _line_priority(line), line)
                for index, line in enumerate(lines)
                if line.strip()
            ]
            if not scored:
                return None
            positive = [item for item in scored if item[1] > 0]
            if not positive:
                return None
            return max(positive, key=lambda item: (item[1], -item[0]))[2]

        def _ordered_lines(lines: list[str]) -> list[str]:
            scored = [(index, _line_priority(line), line) for index, line in enumerate(lines)]
            if not any(score > 0 for _, score, _ in scored):
                return lines
            return [
                line
                for _, _, line in sorted(
                    scored,
                    key=lambda item: (-item[1], item[0]),
                )
            ]

        def _push_line(line: str, chunk_summary: dict[str, Any]) -> None:
            normalized = line.strip().lower()
            if not normalized or normalized in seen:
                return
            selected_entries.append((line.strip(), chunk_summary))
            seen.add(normalized)

        for chunk in chunk_summaries:
            prioritized = _evidence_lines(chunk) + _candidate_lines(str(chunk.get("summary") or ""))
            priority_line = _best_priority_line(prioritized)
            if priority_line:
                _push_line(priority_line, chunk)
            if len(selected_entries) >= max_lines:
                break

        for index in preferred_indices:
            if index < 0 or index >= len(chunk_summaries):
                continue
            lines = _evidence_lines(chunk_summaries[index]) + _candidate_lines(str(chunk_summaries[index].get("summary") or ""))
            priority_line = _best_priority_line(lines)
            if priority_line:
                _push_line(priority_line, chunk_summaries[index])
            elif lines:
                _push_line(lines[0], chunk_summaries[index])

        for chunk in chunk_summaries:
            lines = _evidence_lines(chunk) + _candidate_lines(str(chunk.get("summary") or ""))
            for line in _ordered_lines(lines):
                _push_line(line, chunk)
                if len(selected_entries) >= max_lines:
                    break
            if len(selected_entries) >= max_lines:
                break

        if not selected_entries:
            fallback = [self._summarize_hint(str(item.get("summary") or ""), max_chars=120) for item in chunk_summaries]
            selected_entries = [
                (line, chunk_summaries[index])
                for index, line in enumerate(fallback)
                if line and index < len(chunk_summaries)
            ][:max_lines]

        return selected_entries[:max_lines]

    def _merge_chunk_summaries(
        self,
        *,
        chunk_summaries: list[dict[str, Any]],
        max_lines: int = 4,
        summary_source_type: str = "local_document",
    ) -> str:
        selected_entries = self._select_summary_chunk_entries(
            chunk_summaries=chunk_summaries,
            max_lines=max_lines,
            summary_source_type=summary_source_type,
        )
        if not selected_entries:
            return ""
        if len(chunk_summaries) == 1 and len(selected_entries) == 1:
            return selected_entries[0][0]
        selected_lines = [line for line, _ in selected_entries]
        return "\n".join(f"- {line}" for line in selected_lines[:max_lines])

    def _infer_summary_chunk_source_path(self, *, chunk_text: str, default_source_path: str) -> str:
        match = re.search(r"^Source path:\s*(.+)$", chunk_text, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
        return default_source_path

    def _build_summary_chunk_refs(
        self,
        *,
        chunk_summaries: list[dict[str, Any]],
        max_items: int = 3,
        summary_source_type: str = "local_document",
    ) -> list[dict[str, Any]]:
        selected_entries = self._select_summary_chunk_entries(
            chunk_summaries=chunk_summaries,
            max_lines=max(max_items + 1, 4),
            summary_source_type=summary_source_type,
        )
        if not selected_entries:
            return []

        refs: list[dict[str, Any]] = []
        seen_chunk_ids: set[str] = set()
        total_chunks = len(chunk_summaries)
        for line, chunk_summary in selected_entries:
            chunk_id = str(chunk_summary.get("chunk_id") or "")
            if chunk_id and chunk_id in seen_chunk_ids:
                continue
            source_path = str(chunk_summary.get("source_path") or "")
            refs.append(
                {
                    "chunk_id": chunk_id,
                    "chunk_index": int(chunk_summary.get("index") or 0),
                    "total_chunks": total_chunks,
                    "source_path": source_path,
                    "source_name": Path(source_path).name if source_path else "(출처 없음)",
                    "selected_line": line,
                }
            )
            if chunk_id:
                seen_chunk_ids.add(chunk_id)
            if len(refs) >= max_items:
                break
        return refs

    def _summarize_text_with_chunking(
        self,
        *,
        text: str,
        source_label: str,
        source_path: str | None = None,
        reduce_source_type: str = "local_document",
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
        phase_event_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
        chunk_threshold: int = 4200,
    ) -> tuple[str, list[dict[str, Any]]]:
        if len(text) <= chunk_threshold:
            short_summary_prompt = self._build_short_summary_prompt(
                source_label=source_label,
                text=text,
                summary_source_type=reduce_source_type,
            )
            return (
                self._collect_model_stream(
                    self.model.stream_summarize(short_summary_prompt),
                    stream_event_callback=stream_event_callback,
                    cancel_requested=cancel_requested,
                ),
                [],
            )

        summary_source_path = source_path or source_label
        chunks = self._chunk_text_for_summary(source_path=summary_source_path, text=text)
        if len(chunks) <= 1:
            short_summary_prompt = self._build_short_summary_prompt(
                source_label=source_label,
                text=text,
                summary_source_type=reduce_source_type,
            )
            return (
                self._collect_model_stream(
                    self.model.stream_summarize(short_summary_prompt),
                    stream_event_callback=stream_event_callback,
                    cancel_requested=cancel_requested,
                ),
                [],
            )

        chunk_summaries: list[dict[str, Any]] = []
        total_chunks = len(chunks)
        for index, chunk in enumerate(chunks, start=1):
            self._raise_if_cancelled(cancel_requested)
            self._emit_phase(
                phase_event_callback,
                phase="summarize_chunk_started",
                title="대용량 문서 구간 분석 중",
                detail=f"{source_label} 문서를 {total_chunks}개 구간으로 나눠 {index}번째 핵심을 정리하는 중입니다.",
                note="먼저 구간별 핵심을 추린 뒤, 마지막에 하나의 요약으로 합칩니다.",
            )
            chunk_summary_prompt = self._build_individual_chunk_summary_prompt(
                source_label=source_label,
                chunk_text=str(chunk.get("text") or ""),
                summary_source_type=reduce_source_type,
            )
            chunk_summary = self._collect_model_stream(
                self.model.stream_summarize(chunk_summary_prompt),
                cancel_requested=cancel_requested,
            )
            chunk_text = str(chunk.get("text") or "")
            resolved_source_path = self._infer_summary_chunk_source_path(
                chunk_text=chunk_text,
                default_source_path=str(chunk.get("source_path") or summary_source_path),
            )
            chunk_summaries.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "index": index,
                    "summary": self._summarize_hint(chunk_summary, max_chars=180),
                    "source_path": resolved_source_path,
                    "evidence": self._extract_text_evidence_items(
                        source_path=resolved_source_path,
                        text=chunk_text,
                        max_items=2,
                    ),
                }
            )

        self._raise_if_cancelled(cancel_requested)
        self._emit_phase(
            phase_event_callback,
            phase="summarize_chunk_reduce",
            title="구간 요약 통합 중",
            detail=f"{source_label} 문서의 구간 요약 {total_chunks}개를 하나의 초안으로 합치는 중입니다.",
            note="문서 앞, 중간, 뒤에서 핵심이 빠지지 않도록 균형 있게 묶습니다.",
        )
        reduce_prompt = self._build_chunk_summary_reduce_prompt(
            source_label=source_label,
            chunk_summaries=chunk_summaries,
            reduce_source_type=reduce_source_type,
        )
        final_summary = ""
        if reduce_prompt:
            final_summary = self._collect_model_stream(
                self.model.stream_summarize(reduce_prompt),
                stream_event_callback=stream_event_callback,
                cancel_requested=cancel_requested,
            ).strip()
        if not final_summary:
            final_summary = self._merge_chunk_summaries(
                chunk_summaries=chunk_summaries,
                summary_source_type=reduce_source_type,
            )
        summary_chunks = self._build_summary_chunk_refs(
            chunk_summaries=chunk_summaries,
            summary_source_type=reduce_source_type,
        )
        if stream_event_callback:
            stream_event_callback({"event": StreamEventType.TEXT_REPLACE, "text": final_summary})
        return final_summary, summary_chunks

    def _collect_retrieval_chunks(self, *, read_results: list[Any], max_total_chunks: int = 36) -> list[dict[str, str]]:
        chunks: list[dict[str, str]] = []
        for read_result in read_results:
            per_source_chunks = self._chunk_text_for_retrieval(
                source_path=read_result.resolved_path,
                text=read_result.text,
                max_chunks=12,
            )
            chunks.extend(per_source_chunks)
            if len(chunks) >= max_total_chunks:
                break
        return chunks[:max_total_chunks]

    def _intent_keywords(self, intent: str) -> list[str]:
        mapping = {
            FOLLOW_UP_INTENT_KEY_POINTS: ["목표", "원칙", "핵심", "결론", "방향", "구조"],
            FOLLOW_UP_INTENT_ACTION_ITEMS: ["해야", "필요", "권고", "실행", "다음", "검토", "추가", "구현", "확정"],
            FOLLOW_UP_INTENT_MEMO: ["핵심", "실행", "다음", "정리", "메모"],
            FOLLOW_UP_INTENT_GENERAL: ["핵심", "요약", "설명"],
        }
        return mapping.get(intent, [])

    def _select_retrieval_chunks(
        self,
        *,
        active_context: dict[str, Any],
        intent: str,
        user_request: str,
        max_chunks: int = 4,
    ) -> list[dict[str, str]]:
        chunks = [
            dict(item)
            for item in active_context.get("retrieval_chunks", [])
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ]
        if not chunks:
            return []

        query_terms = []
        for keyword in self._intent_keywords(intent):
            if keyword not in query_terms:
                query_terms.append(keyword.lower())
        for keyword in self._request_keywords(user_request):
            if keyword not in query_terms:
                query_terms.append(keyword.lower())

        scored: list[tuple[int, int, dict[str, str]]] = []
        for index, chunk in enumerate(chunks):
            searchable = f"{chunk.get('source_path', '')} {chunk.get('text', '')}".lower()
            score = 0
            for term in query_terms:
                if not term:
                    continue
                occurrences = searchable.count(term)
                if occurrences:
                    score += min(occurrences, 3) * 3
            if intent == FOLLOW_UP_INTENT_ACTION_ITEMS and any(
                keyword in searchable for keyword in ["해야", "필요", "권고", "실행", "검토", "확정", "추가", "구현"]
            ):
                score += 5
            if intent == FOLLOW_UP_INTENT_KEY_POINTS and any(
                keyword in searchable for keyword in ["목표", "원칙", "핵심", "결론", "요약", "승인", "로컬"]
            ):
                score += 3
            scored.append((score, -index, chunk))

        if any(score > 0 for score, _, _ in scored):
            scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
            selected = [chunk for score, _, chunk in scored if score > 0][:max_chunks]
        else:
            selected = chunks[:max_chunks]
        return selected

    def _compose_retrieved_context_excerpt(
        self,
        *,
        chunks: list[dict[str, str]],
        fallback_excerpt: str,
    ) -> str:
        if not chunks:
            return fallback_excerpt

        sections: list[str] = []
        for chunk in chunks:
            sections.extend(
                [
                    f"Source: {chunk.get('source_path', '(출처 없음)')}",
                    str(chunk.get("text") or ""),
                    "",
                ]
            )
        return "\n".join(sections).strip() or fallback_excerpt

    def _compose_grounded_context_excerpt(
        self,
        *,
        evidence_items: list[dict[str, str]],
        chunks: list[dict[str, str]],
        fallback_excerpt: str,
        max_supporting_chunks: int = 2,
    ) -> str:
        if not evidence_items:
            return fallback_excerpt

        sections = ["선택된 근거 묶음:"]
        for index, item in enumerate(evidence_items, start=1):
            source_name = str(item.get("source_name") or item.get("source_path") or "(출처 없음)").strip()
            label = str(item.get("label") or "근거").strip()
            snippet = self._clean_evidence_line(str(item.get("snippet") or ""), max_chars=220)
            if not snippet:
                continue
            sections.extend(
                [
                    f"[{index}] 출처: {source_name}",
                    f"[{index}] 라벨: {label}",
                    f"[{index}] 근거: {snippet}",
                    "",
                ]
            )

        supporting_source_paths = {
            str(item.get("source_path") or "").strip()
            for item in evidence_items
            if isinstance(item, dict) and str(item.get("source_path") or "").strip()
        }
        supporting_chunks: list[dict[str, str]] = []
        for chunk in chunks:
            chunk_source = str(chunk.get("source_path") or "").strip()
            if supporting_source_paths and chunk_source not in supporting_source_paths:
                continue
            supporting_chunks.append(chunk)
            if len(supporting_chunks) >= max_supporting_chunks:
                break

        if supporting_chunks:
            sections.append("짧은 보조 문맥:")
            for index, chunk in enumerate(supporting_chunks, start=1):
                source_name = str(chunk.get("source_name") or chunk.get("source_path") or "(출처 없음)").strip()
                excerpt = self._supporting_chunk_excerpt(
                    source_path=str(chunk.get("source_path") or ""),
                    text=str(chunk.get("text") or ""),
                )
                if not excerpt:
                    continue
                sections.extend(
                    [
                        f"- 보조 문맥 {index} ({source_name})",
                        f"  {excerpt}",
                    ]
                )

        grounded_excerpt = "\n".join(sections).strip()
        return grounded_excerpt or fallback_excerpt

    def _build_retry_policy(
        self,
        *,
        retry_feedback_label: str | None,
        retry_feedback_reason: str | None,
        active_context: dict[str, Any],
    ) -> dict[str, Any]:
        policy = {
            "max_evidence_items": 4,
            "max_supporting_chunks": 2,
            "suppress_summary_hint": bool(retry_feedback_label in {"unclear", "incorrect"}),
        }
        if retry_feedback_reason == "factual_error":
            policy.update(
                {
                    "max_evidence_items": 2,
                    "max_supporting_chunks": 1,
                    "prefer_web_original_evidence": active_context.get("kind") == "web_search",
                }
            )
        elif retry_feedback_reason == "irrelevant_result":
            policy.update(
                {
                    "max_evidence_items": 2,
                    "max_supporting_chunks": 1,
                    "prefer_web_original_evidence": active_context.get("kind") == "web_search",
                }
            )
        elif retry_feedback_reason == "awkward_tone":
            policy.update({"max_supporting_chunks": 1})
        return policy

    def _filter_evidence_pool_for_retry(
        self,
        *,
        evidence_pool: list[dict[str, str]],
        active_context: dict[str, Any],
        retry_feedback_reason: str | None,
        policy: dict[str, Any],
    ) -> list[dict[str, str]]:
        filtered_pool = list(evidence_pool)
        if policy.get("prefer_web_original_evidence"):
            web_only = [item for item in filtered_pool if str(item.get("label") or "") == "웹 원문 근거"]
            if web_only:
                filtered_pool = web_only
        if retry_feedback_reason == "irrelevant_result":
            without_search_snippets = [item for item in filtered_pool if str(item.get("label") or "") != "검색 발췌"]
            if without_search_snippets:
                filtered_pool = without_search_snippets
        return filtered_pool or evidence_pool

    def _augment_retry_request(
        self,
        *,
        user_request: str,
        retry_feedback_label: str | None,
        retry_feedback_reason: str | None,
    ) -> str:
        if retry_feedback_label not in {"unclear", "incorrect"}:
            return user_request
        guidance_lines = []
        if retry_feedback_reason == "factual_error":
            guidance_lines.append(
                "추가 제약: 제공된 근거 문장에 직접 보이는 사실만 답해 주세요. 확인되지 않은 내용은 '제공된 근거만으로는 확인되지 않습니다.'라고 적어 주세요."
            )
            guidance_lines.append("가능하면 답변 마지막에 '근거:' 한 줄로 사용한 문장을 짧게 붙여 주세요.")
        elif retry_feedback_reason == "irrelevant_result":
            guidance_lines.append("추가 제약: 질문과 직접 관련된 근거만 사용하고, 무관한 검색 결과나 주변 설명은 답변에서 빼 주세요.")
        elif retry_feedback_reason == "context_miss":
            guidance_lines.append("추가 제약: 현재 선택된 문서나 검색 기록 문맥 안에서만 다시 답해 주세요.")
        elif retry_feedback_reason == "awkward_tone":
            guidance_lines.append("추가 제약: 사실은 그대로 유지하고, 더 자연스럽고 명확한 한국어로 다시 써 주세요.")
        else:
            guidance_lines.append("추가 제약: 같은 근거 범위 안에서 더 정확하고 관련성 높게 다시 답해 주세요.")

        return f"{user_request}\n\n" + "\n".join(guidance_lines)

    def _supporting_chunk_excerpt(self, *, source_path: str, text: str) -> str:
        raw_text = str(text or "").strip()
        if not raw_text:
            return ""
        if source_path.startswith(("http://", "https://")):
            clean_segments = [
                segment
                for segment in self._split_web_page_segments(raw_text)
                if not self._looks_like_noisy_web_segment(segment)
            ]
            if clean_segments:
                return self._summarize_hint(" ".join(clean_segments[:2]), max_chars=320)
        return self._summarize_hint(raw_text, max_chars=320)

    def _extract_evidence_from_chunks(
        self,
        *,
        chunks: list[dict[str, str]],
        max_items: int = 6,
    ) -> list[dict[str, str]]:
        evidence_items: list[dict[str, str]] = []
        for chunk in chunks:
            source_path = str(chunk.get("source_path") or "")
            text = str(chunk.get("text") or "")
            if not text:
                continue
            for item in self._extract_text_evidence_items(
                source_path=source_path,
                text=text,
                max_items=2,
            ):
                if source_path.startswith(("http://", "https://")):
                    item["label"] = "웹 원문 근거"
                evidence_items.append(item)
        return self._dedupe_evidence_items(evidence_items, max_items=max_items)

    def _build_active_context(
        self,
        *,
        kind: str,
        label: str,
        source_paths: list[str],
        excerpt: str,
        summary_hint: str,
        suggested_prompts: list[str],
        evidence_pool: list[dict[str, str]] | None = None,
        retrieval_chunks: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        return {
            "kind": kind,
            "label": label,
            "source_paths": list(source_paths),
            "excerpt": excerpt,
            "summary_hint": self._summarize_hint(summary_hint),
            "suggested_prompts": [prompt for prompt in suggested_prompts if isinstance(prompt, str)],
            "evidence_pool": [dict(item) for item in (evidence_pool or []) if isinstance(item, dict)],
            "retrieval_chunks": [dict(item) for item in (retrieval_chunks or []) if isinstance(item, dict)],
        }

    def _clean_evidence_line(self, line: str, *, max_chars: int = 220) -> str:
        cleaned = line.strip()
        cleaned = re.sub(r"^[#>\-\*\d\.\)\s]+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = cleaned.strip(" |")
        if len(cleaned) <= max_chars:
            return cleaned
        return cleaned[:max_chars].rstrip() + "..."

    def _is_metadata_line(self, line: str) -> bool:
        lowered = line.strip().lower()
        if not lowered:
            return True
        if lowered.startswith(
            (
                "source:",
                "match:",
                "snippet:",
                "source path:",
                "search query:",
                "intent:",
                "context label:",
                "원본 파일:",
                "원본 경로:",
                "검색어:",
                "출처:",
                "일치 방식:",
                "발췌:",
            )
        ):
            return True
        if re.match(r"^(title|version|author|date|path|작성일|버전|제목)\b", lowered):
            return True
        if re.match(r"^v?\d+\.\d+(\.\d+)?$", lowered):
            return True
        return False

    def _make_evidence_item(self, *, source_path: str, label: str, snippet: str) -> dict[str, str] | None:
        cleaned = self._clean_evidence_line(snippet)
        if len(cleaned) < 4 or self._is_metadata_line(cleaned) or re.fullmatch(r"[\d\W_]+", cleaned):
            return None
        return {
            "source_path": source_path,
            "source_name": Path(source_path).name if source_path else "(출처 없음)",
            "label": label,
            "snippet": cleaned,
        }

    def _dedupe_evidence_items(self, items: list[dict[str, str]], *, max_items: int) -> list[dict[str, str]]:
        deduped: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for item in items:
            source_path = str(item.get("source_path") or "")
            snippet = str(item.get("snippet") or "").strip()
            if not snippet:
                continue
            key = (source_path, snippet.lower())
            if key in seen:
                continue
            deduped.append(
                {
                    "source_path": source_path,
                    "source_name": str(item.get("source_name") or Path(source_path).name or "(출처 없음)"),
                    "label": str(item.get("label") or "문서 근거"),
                    "snippet": snippet,
                }
            )
            seen.add(key)
            if len(deduped) >= max_items:
                break
        return deduped

    def _extract_text_evidence_items(
        self,
        *,
        source_path: str,
        text: str,
        max_items: int = 6,
    ) -> list[dict[str, str]]:
        heading_items: list[dict[str, str]] = []
        action_items: list[dict[str, str]] = []
        bullet_items: list[dict[str, str]] = []
        sentence_items: list[dict[str, str]] = []
        action_keywords = ["해야", "필요", "권고", "실행", "다음", "검토", "확정", "추가", "정리", "구현", "결정"]

        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue

            cleaned = self._clean_evidence_line(stripped)
            if len(cleaned) < 6 or self._is_metadata_line(cleaned):
                continue
            if source_path.startswith(("http://", "https://")) and self._looks_like_noisy_web_segment(cleaned):
                continue

            item: dict[str, str] | None = None
            if stripped.startswith("#"):
                item = self._make_evidence_item(source_path=source_path, label="문서 핵심", snippet=cleaned)
                if item:
                    heading_items.append(item)
                continue

            if any(keyword in cleaned for keyword in action_keywords):
                item = self._make_evidence_item(source_path=source_path, label="실행 후보", snippet=cleaned)
                if item:
                    action_items.append(item)
                    continue

            if stripped.startswith(("-", "*")) or re.match(r"^\d+\.", stripped):
                item = self._make_evidence_item(source_path=source_path, label="핵심 항목", snippet=cleaned)
                if item:
                    bullet_items.append(item)
                    continue

            if len(cleaned) >= 10:
                item = self._make_evidence_item(source_path=source_path, label="본문 근거", snippet=cleaned)
                if item:
                    sentence_items.append(item)

        return self._dedupe_evidence_items(
            [*heading_items, *action_items, *bullet_items, *sentence_items],
            max_items=max_items,
        )

    def _extract_search_evidence_items(
        self,
        *,
        selected_results: list[FileSearchResult],
        read_results: list[Any],
        max_items: int = 8,
    ) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for search_result, read_result in zip(selected_results, read_results):
            if search_result.snippet:
                item = self._make_evidence_item(
                    source_path=read_result.resolved_path,
                    label="검색 발췌",
                    snippet=search_result.snippet,
                )
                if item:
                    items.append(item)
            items.extend(
                self._extract_text_evidence_items(
                    source_path=read_result.resolved_path,
                    text=read_result.text,
                    max_items=2,
                )
            )
        return self._dedupe_evidence_items(items, max_items=max_items)

    def _request_keywords(self, user_request: str) -> list[str]:
        stopwords = {
            "현재",
            "문서",
            "다시",
            "정리",
            "형식",
            "내용",
            "주세요",
            "해줘",
            "요약",
            "메모",
            "실행",
            "항목",
            "뽑아",
            "다음",
            "질문",
            "관련",
            "결과",
        }
        keywords: list[str] = []
        for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", user_request):
            lowered = token.lower()
            if lowered in stopwords:
                continue
            keywords.append(lowered)
        return keywords

    def _looks_like_action_evidence(self, text: str) -> bool:
        action_keywords = ["해야", "필요", "권고", "실행", "다음", "검토", "추가", "구현", "확정", "정리", "도입"]
        return any(keyword in text for keyword in action_keywords)

    def _looks_like_actionable_decision_evidence(self, text: str) -> bool:
        decision_keywords = ["결정", "확정", "검토", "도입", "추가", "유지", "정리", "구현", "필요", "권고", "다음", "우선"]
        return any(keyword in text for keyword in decision_keywords)

    def _select_evidence_items(
        self,
        *,
        evidence_pool: list[dict[str, str]],
        intent: str,
        user_request: str,
        max_items: int = 3,
    ) -> list[dict[str, str]]:
        if not evidence_pool:
            return []

        intent_keywords = {
            FOLLOW_UP_INTENT_KEY_POINTS: ["목표", "원칙", "핵심", "결론", "방향", "구조"],
            FOLLOW_UP_INTENT_ACTION_ITEMS: ["해야", "필요", "권고", "실행", "다음", "검토", "추가", "구현", "확정"],
            FOLLOW_UP_INTENT_MEMO: ["핵심", "실행", "다음", "정리", "메모"],
            FOLLOW_UP_INTENT_GENERAL: ["핵심", "요약", "설명"],
        }
        request_keywords = self._request_keywords(user_request)
        scored: list[tuple[int, int, dict[str, str]]] = []
        for index, item in enumerate(evidence_pool):
            snippet = str(item.get("snippet") or "")
            label = str(item.get("label") or "")
            searchable = f"{label} {snippet}".lower()
            score = 0
            if label == "검색 발췌":
                score += 2
            if label == "실행 후보":
                score += 4 if intent == FOLLOW_UP_INTENT_ACTION_ITEMS else 1
            if label in {"문서 핵심", "핵심 항목"}:
                score += 3 if intent in {FOLLOW_UP_INTENT_KEY_POINTS, FOLLOW_UP_INTENT_MEMO} else 1
            if intent == FOLLOW_UP_INTENT_ACTION_ITEMS and not (
                self._looks_like_action_evidence(snippet)
                or self._looks_like_actionable_decision_evidence(snippet)
                or label == "실행 후보"
            ):
                score -= 5
            for keyword in intent_keywords.get(intent, []):
                if keyword.lower() in searchable:
                    score += 2
            for keyword in request_keywords:
                if keyword in searchable:
                    score += 3
            if intent == FOLLOW_UP_INTENT_GENERAL and label == "본문 근거":
                score += 1
            scored.append((score, -index, item))

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return self._dedupe_evidence_items([item for _, _, item in scored], max_items=max_items)

    def _build_context_excerpt_from_text(self, text: str, *, head_chars: int = 3500, tail_chars: int = 2500) -> str:
        if len(text) <= head_chars + tail_chars + 200:
            return text
        return "\n".join(
            [
                text[:head_chars].rstrip(),
                "",
                "...[중략]...",
                "",
                text[-tail_chars:].lstrip(),
            ]
        )

    def _detect_follow_up_intent(self, user_request: str) -> str:
        lowered = user_request.lower()
        if any(keyword in user_request for keyword in ["핵심 3줄", "핵심 3문장", "핵심만", "세 줄", "세문장"]):
            return FOLLOW_UP_INTENT_KEY_POINTS
        if any(keyword in user_request for keyword in ["실행할 일", "액션 아이템", "해야 할 일", "다음 할 일"]):
            return FOLLOW_UP_INTENT_ACTION_ITEMS
        if any(keyword in user_request for keyword in ["메모 형식", "메모로", "메모 형태", "메모 형식으로"]):
            return FOLLOW_UP_INTENT_MEMO
        if any(keyword in lowered for keyword in ["key points", "action items", "memo"]):
            if "key points" in lowered:
                return FOLLOW_UP_INTENT_KEY_POINTS
            if "action items" in lowered:
                return FOLLOW_UP_INTENT_ACTION_ITEMS
            if "memo" in lowered:
                return FOLLOW_UP_INTENT_MEMO
        return FOLLOW_UP_INTENT_GENERAL

    def _contains_small_talk_signal(self, user_request: str) -> bool:
        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return False

        lowered = normalized.lower()
        signal_keywords = [
            "안녕",
            "반갑",
            "고마워",
            "고맙",
            "감사",
            "좋아",
            "좋네",
            "좋아요",
            "좋네요",
            "오케이",
            "okay",
            "ok",
            "알겠",
            "알겠습니다",
            "하이",
            "hello",
            "hi",
            "hey",
            "thanks",
            "thank you",
            "잘 지내",
            "뭐해",
            "날씨",
            "점심",
            "저녁",
            "피곤",
            "심심",
        ]
        return any(keyword in lowered or keyword in normalized for keyword in signal_keywords)

    def _small_talk_prefix(self, user_request: str) -> str:
        normalized = " ".join(user_request.strip().split())
        if any(keyword in normalized for keyword in ["감사", "고마워", "고맙"]):
            return "감사합니다."
        if any(keyword in normalized for keyword in ["안녕", "반갑", "하이", "hello", "hi", "hey"]):
            return "반갑습니다."
        if any(keyword in normalized for keyword in ["좋아", "좋네", "좋아요", "좋네요", "오케이", "okay", "ok", "알겠"]):
            return "좋습니다."
        return "좋습니다."

    def _contains_context_follow_up_cue(self, user_request: str) -> bool:
        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return False

        follow_up_keywords = [
            "이거",
            "그거",
            "방금",
            "다시",
            "그럼 다음엔",
            "다음엔 뭘",
            "뭘 하면 돼",
            "뭐부터",
            "다음 단계",
            "조금 더",
            "더 짧게",
            "짧게",
            "간단히",
            "쉽게",
            "부드럽게",
            "풀어서",
            "한 줄",
            "한줄",
            "한 문장",
            "한문장",
            "뭐가 제일 중요",
            "가장 중요",
            "중요한 것만",
            "요점만",
            "줄여",
            "다듬",
            "바꿔",
            "다시 써",
            "재작성",
            "메모처럼",
            "정리본",
            "할 일만",
            "다시 보여",
            "보여 줘",
            "보여줘",
            "풀어 줘",
            "풀어줘",
            "더 자세히",
            "조금 더 자세히",
        ]
        return any(keyword in normalized for keyword in follow_up_keywords)

    def _looks_like_unverified_external_fact_request(self, user_request: str) -> bool:
        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return False

        if any(
            keyword in normalized
            for keyword in [
                "이 문서",
                "현재 문서",
                "이 파일",
                "문서",
                "파일",
                "요약",
                "본문",
                "출처",
                "근거",
                "검색 결과",
                "로컬 파일",
            ]
        ):
            return False

        if any(keyword in normalized for keyword in ["너 누구", "넌 누구", "너는 누구", "이 비서", "어시스턴트", "assistant"]):
            return False

        fact_keywords = [
            "누구야",
            "누군데",
            "누군지",
            "뭐야",
            "뭔데",
            "알아",
            "아나요",
            "정체",
            "실존",
            "맞아",
            "맞나요",
            "유명해",
            "공식",
            "진짜",
            "어떤 사람이",
            "무슨 채널",
            "무슨 제품",
            "무슨 브랜드",
            "유튜버",
            "채널",
            "브랜드",
            "제품",
            "사이트",
            "서비스",
            "앱",
            "플랫폼",
            "포털",
            "쇼핑몰",
            "회사",
            "인물",
            "사람",
        ]
        return any(keyword in normalized for keyword in fact_keywords)

    def _extract_web_search_permission(self, request: UserRequest) -> str:
        value = request.metadata.get("web_search_permission")
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"disabled", "approval", "enabled"}:
                return normalized
        return "disabled"

    def _web_search_permission_phrase(self, permission: str) -> str:
        normalized = (permission or "disabled").strip().lower()
        if normalized == "approval":
            return "현재 세션에서는 웹 검색을 승인 후에만 허용하도록 설정해 두었지만"
        if normalized == "enabled":
            return "현재 세션에서는 웹 검색을 허용한 상태지만"
        return "현재 세션에서는 웹 검색 권한이 차단되어 있고"

    def _build_unverified_external_fact_response(self) -> AgentResponse:
        return self._build_unverified_external_fact_response_for_permission("disabled")

    def _build_unverified_external_fact_response_for_permission(self, permission: str) -> AgentResponse:
        normalized = (permission or "disabled").strip().lower()
        if normalized == "enabled":
            text = (
                "현재 세션에서는 웹 검색을 허용한 상태지만, 이 질문을 자동 검색 대상으로 아직 정확히 분류하지 못했고 "
                "로컬 문서 근거도 없어서 외부 인물·채널·사이트·서비스·제품 정보를 바로 확인해 드릴 수 없습니다. "
                "질문을 조금 더 구체적으로 쓰거나 '검색해봐'처럼 요청해 주시면 검색 기반으로 다시 확인하겠습니다."
            )
        elif normalized == "approval":
            text = (
                "현재 세션에서는 웹 검색을 승인 후에만 허용하도록 설정해 두었고 로컬 문서 근거도 없어서 외부 인물·채널·사이트·서비스·제품 정보를 "
                "바로 확인해 드릴 수 없습니다. 질문을 조금 더 구체적으로 쓰거나 웹 검색 승인 후 다시 요청해 주시면 검색 기반으로 확인하겠습니다."
            )
        else:
            text = (
                "현재 세션에서는 웹 검색 권한이 차단되어 있고 로컬 문서 근거도 없어서 외부 인물·채널·사이트·서비스·제품 정보를 "
                "확인해 드릴 수 없습니다. 관련 문서, 설명 텍스트, 메모를 주시면 그 범위 안에서 정리해 드리겠습니다."
            )
        return AgentResponse(
            text=text,
            status=ResponseStatus.ANSWER,
            actions_taken=["respond_with_limitations"],
            response_origin={
                "provider": "system",
                "badge": "SYSTEM",
                "label": "시스템 안내",
                "model": None,
                "kind": "assistant",
            },
        )

    def _looks_like_personal_experience_request(self, user_request: str) -> bool:
        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return False
        experience_keywords = [
            "봤어",
            "봐봤어",
            "읽어봤어",
            "들어봤어",
            "써봤어",
            "해봤어",
            "가봤어",
            "먹어봤어",
            "본 적 있어",
            "본적 있어",
        ]
        return any(keyword in normalized for keyword in experience_keywords)

    def _build_personal_experience_response(self) -> AgentResponse:
        return AgentResponse(
            text=(
                "저는 직접 봤다거나 써 봤다거나 다녀온 경험이 있는 것처럼 말할 수는 없습니다. "
                "대신 작품 소개, 줄거리, 리뷰, 제품 설명 같은 텍스트를 주시면 그 내용만 기준으로 정리해 드릴 수 있습니다."
            ),
            status=ResponseStatus.ANSWER,
            actions_taken=["respond_with_limitations"],
            response_origin={
                "provider": "system",
                "badge": "SYSTEM",
                "label": "시스템 안내",
                "model": None,
                "kind": "assistant",
            },
        )

    def _looks_like_live_info_request(self, user_request: str) -> bool:
        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return False
        live_keywords = [
            "날씨",
            "기온",
            "비 와",
            "비와",
            "눈 와",
            "눈와",
            "실시간",
            "지금 뉴스",
            "속보",
            "오늘 뉴스",
            "환율",
            "주가",
        ]
        return any(keyword in normalized for keyword in live_keywords)

    def _build_live_info_response(self) -> AgentResponse:
        return self._build_live_info_response_for_permission("disabled")

    def _build_live_info_response_for_permission(self, permission: str) -> AgentResponse:
        return AgentResponse(
            text=(
                f"{self._web_search_permission_phrase(permission)} 실시간 날씨나 뉴스 같은 외부 조회 도구가 아직 연결되어 있지 않습니다. "
                "그래서 지금 바로 조회해 드릴 수는 없습니다. 지역명과 함께 메모나 관련 텍스트를 주시면 그 범위 안에서 정리해 드릴 수 있습니다."
            ),
            status=ResponseStatus.ANSWER,
            actions_taken=["respond_with_limitations"],
            response_origin={
                "provider": "system",
                "badge": "SYSTEM",
                "label": "시스템 안내",
                "model": None,
                "kind": "assistant",
            },
        )

    def _classify_search_intent(self, user_request: str):
        return classify_search_intent(user_request)

    def _build_web_search_permission_response(self, permission: str, *, query: str) -> AgentResponse:
        normalized = (permission or "disabled").strip().lower()
        if normalized == "approval":
            text = (
                f"현재 세션에서는 웹 검색을 승인 후에만 허용하도록 설정해 두었습니다. 다만 이번 단계에서는 "
                f"웹 검색 승인 카드가 아직 연결되지 않아 '{query}' 검색을 바로 실행하지 못합니다. "
                "지금 바로 검색하려면 외부 웹 검색 권한을 '허용'으로 바꾸어 주세요."
            )
        else:
            text = (
                f"현재 세션에서는 외부 웹 검색이 차단되어 있어 '{query}' 검색을 실행하지 않았습니다. "
                "고급 설정에서 외부 웹 검색 권한을 '허용'으로 바꾸면 읽기 전용 검색을 실행할 수 있습니다."
            )
        return AgentResponse(
            text=text,
            status=ResponseStatus.ANSWER,
            actions_taken=["respond_with_limitations"],
            response_origin={
                "provider": "system",
                "badge": "SYSTEM",
                "label": "시스템 안내",
                "model": None,
                "kind": "assistant",
            },
        )

    def _build_web_search_suggestion_response(self, permission: str, *, query: str) -> AgentResponse:
        normalized = (permission or "disabled").strip().lower()
        if normalized == "enabled":
            text = (
                f"질문 의도는 어느 정도 이해했지만 아직 자동 웹 검색으로 바로 넘길 확신은 낮습니다. "
                f"원하시면 아래 제안으로 '{query}'를 바로 검색해 보겠습니다."
            )
            suggestions = [f"{query} 검색해봐"]
        elif normalized == "approval":
            text = (
                f"'{query}' 쪽으로 찾아보려는 질문으로 보이지만, 현재 세션은 웹 검색을 승인 후에만 허용합니다. "
                "이번 단계에서는 승인 카드가 아직 연결되지 않아 자동 실행 대신 명시적 검색 요청으로만 이어갈 수 있습니다."
            )
            suggestions = [f"{query} 검색해봐"]
        else:
            text = (
                f"'{query}' 쪽으로 찾아보려는 질문으로 보이지만 현재 세션에서는 외부 웹 검색이 차단되어 있습니다. "
                "고급 설정에서 웹 검색 권한을 허용으로 바꾸면 바로 검색할 수 있습니다."
            )
            suggestions = []
        return AgentResponse(
            text=text,
            status=ResponseStatus.ANSWER,
            actions_taken=["suggest_web_search"],
            follow_up_suggestions=suggestions,
            response_origin={
                "provider": "system",
                "badge": "SYSTEM",
                "label": "시스템 안내",
                "model": None,
                "kind": "assistant",
            },
        )

    def _build_entity_reinvestigation_suggestions(
        self,
        *,
        query: str,
        claim_coverage: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        slot_prompt_map = {
            "개발": f"{query} 개발사 검색해봐",
            "서비스/배급": f"{query} 서비스 공식 검색해봐",
            "장르/성격": f"{query} 장르 검색해봐",
            "상태": f"{query} 출시 상태 검색해봐",
            "이용 형태": f"{query} 공식 플랫폼 검색해봐",
        }
        status_priority = {CoverageStatus.MISSING: 0, CoverageStatus.WEAK: 1}
        candidates: list[tuple[int, int, str]] = []
        for index, item in enumerate(claim_coverage or []):
            if not isinstance(item, dict):
                continue
            slot = str(item.get("slot") or "").strip()
            status = str(item.get("status") or "").strip()
            prompt = slot_prompt_map.get(slot)
            if not prompt or status not in status_priority:
                continue
            candidates.append((status_priority[status], index, prompt))

        candidates.sort(key=lambda item: (item[0], item[1]))
        suggestions: list[str] = []
        seen: set[str] = set()
        for _, _, prompt in candidates:
            if prompt in seen:
                continue
            seen.add(prompt)
            suggestions.append(prompt)
            if len(suggestions) >= 3:
                break
        return suggestions

    def _follow_up_suggestions_for_web_search(
        self,
        query: str,
        *,
        answer_mode: str | None = None,
        claim_coverage: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        suggestions: list[str] = []
        if answer_mode == AnswerMode.ENTITY_CARD:
            suggestions.extend(
                self._build_entity_reinvestigation_suggestions(
                    query=query,
                    claim_coverage=claim_coverage,
                )
            )
        suggestions.extend(
            [
                f"{query} 검색 결과 핵심 3줄만 다시 정리해 주세요.",
                f"{query} 검색 결과에서 가장 믿을 만한 출처만 추려 주세요.",
                f"{query} 검색 결과를 메모 형식으로 다시 써 주세요.",
            ]
        )
        deduped: list[str] = []
        seen: set[str] = set()
        for prompt in suggestions:
            normalized = str(prompt).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped

    def _extract_load_web_search_record_id(self, request: UserRequest) -> str | None:
        value = request.metadata.get("load_web_search_record_id")
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _looks_like_web_search_record_recall(self, user_request: str) -> bool:
        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return False
        direct_phrases = [
            "방금 검색한 결과",
            "아까 검색한 결과",
            "이전 검색 결과",
            "직전 검색 결과",
            "최근 검색 결과",
            "검색 기록 다시",
            "검색 기록 보여",
            "검색 기록 불러",
            "검색 기록 꺼내",
        ]
        if any(phrase in normalized for phrase in direct_phrases):
            return True
        if "검색" not in normalized:
            return False
        recall_markers = ["방금", "아까", "이전", "직전", "최근", "기록", "다시", "불러", "보여", "꺼내"]
        return any(marker in normalized for marker in recall_markers)

    def _extract_web_query_terms(self, query: str) -> list[str]:
        tokens = [token.strip().lower() for token in re.findall(r"[A-Za-z0-9가-힣]+", query or "")]
        stopwords = {
            "검색", "검색해", "검색해봐", "검색해줘", "검색좀", "알려줘", "알려주세요", "봐줘", "볼래",
            "관련", "관련해서", "대해", "대한", "좀", "조금", "해줘", "해봐", "뭐야", "누구야", "최신",
            "최근", "소식", "정보", "오늘", "요즘", "실시간", "어때", "어때요", "알아봐", "찾아와",
        }
        filtered: list[str] = []
        for token in tokens:
            if len(token) < 2 or token in stopwords:
                continue
            if token not in filtered:
                filtered.append(token)
        squashed = "".join(filtered)
        if len(squashed) >= 2 and squashed not in filtered:
            filtered.append(squashed)
        return filtered

    def _query_prefers_video_platform_results(self, query: str) -> bool:
        normalized = " ".join(str(query or "").split()).lower()
        if not normalized:
            return False
        return any(
            marker in normalized
            for marker in [
                "youtube",
                "유튜브",
                "채널",
                "영상",
                "동영상",
                "뮤비",
                "mv",
                "shorts",
                "쇼츠",
            ]
        )

    def _looks_like_js_heavy_web_url(self, url: str) -> bool:
        hostname = urlparse(str(url or "").strip()).netloc.lower()
        if not hostname:
            return False
        heavy_hosts = (
            "youtube.com",
            "youtu.be",
            "instagram.com",
            "facebook.com",
            "x.com",
            "twitter.com",
            "tiktok.com",
        )
        return any(hostname == host or hostname.endswith(f".{host}") for host in heavy_hosts)

    def _looks_like_contact_or_legal_web_segment(self, segment: str) -> bool:
        normalized = " ".join(segment.split())
        lowered = normalized.lower()
        legal_markers = [
            "대표이사",
            "사업자등록번호",
            "통신판매업",
            "고객센터",
            "개인정보처리방침",
            "청소년보호정책",
            "이메일무단수집거부",
            "e-mail",
            "email",
            "팩스",
            "fax",
            "전화",
            "tel",
            "contact",
            "corp.",
            "co., ltd",
            "(주)",
        ]
        marker_count = sum(1 for marker in legal_markers if marker in normalized or marker in lowered)
        has_email = bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", normalized))
        has_phone = bool(re.search(r"\b\d{2,4}-\d{3,4}-\d{4}\b", normalized))
        has_business_number = bool(re.search(r"\b\d{3}-\d{2}-\d{5}\b", normalized))
        if marker_count >= 2:
            return True
        if marker_count >= 1 and (has_email or has_phone or has_business_number):
            return True
        if sum(1 for flag in [has_email, has_phone, has_business_number] if flag) >= 2:
            return True
        return False

    def _looks_like_noisy_web_segment(self, segment: str) -> bool:
        normalized = " ".join(segment.split())
        lowered = normalized.lower()
        if len(normalized) < 14:
            return True
        if self._looks_like_contact_or_legal_web_segment(normalized):
            return True
        boilerplate_hints = [
            "로그인", "로그아웃", "회원가입", "구독", "광고", "전체메뉴", "기사제보", "제보", "pdf보기",
            "이용약관", "개인정보", "쿠키", "all rights reserved", "copyright", "facebook", "twitter",
            "instagram", "youtube", "threads", "line", "카카오톡", "네이버", "다음", "언론사", "rss",
            "언어", "english", "japanese", "deutsch", "русский", "tiếng", "nederlands", "italiano",
            "함께 이용해 보세요", "지금 다운로드", "바로가기", "play now", "download now",
        ]
        hint_count = sum(1 for hint in boilerplate_hints if hint in lowered or hint in normalized)
        if hint_count >= 2:
            return True
        if normalized.count("/") >= 5 or normalized.count("|") >= 3:
            return True
        if re.search(r"(?:\b[A-Za-z]{2,}\b\s+){8,}", normalized) and "." not in normalized:
            return True
        if len(re.findall(r"[·|/]", normalized)) >= 6:
            return True
        return False

    def _split_web_page_segments(self, text: str) -> list[str]:
        segments: list[str] = []
        for raw_line in text.splitlines():
            line = " ".join(raw_line.split()).strip()
            if not line:
                continue
            split_parts = re.split(r"(?<=[\.\!\?])\s+", line)
            usable_parts = split_parts if len(split_parts) > 1 else [line]
            for part in usable_parts:
                cleaned = " ".join(part.split()).strip()
                if cleaned:
                    segments.append(cleaned)
        deduped: list[str] = []
        seen: set[str] = set()
        for segment in segments:
            key = segment.lower()
            if key in seen:
                continue
            deduped.append(segment)
            seen.add(key)
        return deduped

    def _score_web_segment(self, *, segment: str, query_terms: list[str], title: str, snippet: str) -> int:
        normalized = " ".join(segment.split())
        lowered = normalized.lower()
        title_lowered = title.lower()
        snippet_lowered = snippet.lower()

        score = 0
        if not self._looks_like_noisy_web_segment(normalized):
            score += 2

        for term in query_terms:
            if term in lowered:
                score += 5
            if term in title_lowered:
                score += 1
            if term in snippet_lowered:
                score += 1

        if 30 <= len(normalized) <= 180:
            score += 3
        elif len(normalized) <= 260:
            score += 1

        if any(marker in normalized for marker in ["이다", "입니다", "했다", "됐다", "발표", "출시", "예정", "공개"]):
            score += 2
        if any(marker in normalized for marker in ["특징", "소개된다", "소개됩니다", "배경", "싱글 플레이", "멀티플레이"]):
            score += 4
        if any(marker in normalized for marker in ["기온", "날씨", "강수", "미세먼지", "바람"]):
            score += 2
        if "|" in normalized:
            score -= 8
        if self._looks_like_contact_or_legal_web_segment(normalized):
            score -= 12

        if self._looks_like_noisy_web_segment(normalized):
            score -= 8
        return score

    def _build_web_page_focus(self, *, query: str, title: str, snippet: str, text: str) -> tuple[str, str]:
        query_terms = self._extract_web_query_terms(query)
        query_profile = self._infer_web_query_profile(query=query)
        segments = self._split_web_page_segments(text)
        if not segments:
            fallback_excerpt = snippet.strip() or self._summarize_hint(text, max_chars=340)
            fallback_text = self._summarize_hint(text, max_chars=320)
            return fallback_excerpt, fallback_text

        scored: list[tuple[int, int, str]] = []
        for index, segment in enumerate(segments):
            score = self._score_web_segment(
                segment=segment,
                query_terms=query_terms,
                title=title,
                snippet=snippet,
            )
            scored.append((score, -index, segment))

        positive_segments = [item for item in scored if item[0] > 0]
        preferred_positive_segments = [
            item for item in positive_segments if not self._looks_like_noisy_web_segment(item[2])
        ]
        usable_segments = [item for item in scored if not self._looks_like_noisy_web_segment(item[2])]
        if preferred_positive_segments:
            chosen_segments = preferred_positive_segments
        elif positive_segments:
            chosen_segments = positive_segments
        elif usable_segments:
            chosen_segments = usable_segments
        else:
            fallback_excerpt = snippet.strip() or self._summarize_hint(text, max_chars=340)
            return fallback_excerpt, ""
        chosen_segments.sort(key=lambda item: (item[0], item[1]), reverse=True)
        segment_limit = 5 if query_profile == "entity" else 3
        excerpt_limit = 460 if query_profile == "entity" else 340
        top_segments = [segment for _, _, segment in chosen_segments[:segment_limit]]

        ordered_top_segments = [segment for segment in segments if segment in top_segments]
        focused_text = "\n".join(ordered_top_segments).strip()
        if not focused_text:
            focused_text = "\n".join(segments[:2]).strip()

        excerpt_source = focused_text or snippet.strip() or text
        excerpt = self._summarize_hint(excerpt_source, max_chars=excerpt_limit)
        return excerpt, focused_text

    def _infer_web_query_profile(
        self,
        *,
        query: str,
        intent_kind: str | None = None,
        answer_mode: str | None = None,
        freshness_risk: str | None = None,
    ) -> str:
        normalized = " ".join(str(query or "").split()).lower()
        query_terms = self._extract_web_query_terms(query)
        if answer_mode == AnswerMode.ENTITY_CARD:
            return "entity"
        if answer_mode == AnswerMode.LATEST_UPDATE or freshness_risk == FreshnessRisk.HIGH:
            return "live"
        live_markers = {
            "날씨",
            "기온",
            "환율",
            "주가",
            "시세",
            "실시간",
            "속보",
            "뉴스",
            "오늘",
            "지금",
            "요즘",
            "최근",
            "최신",
            "소식",
            "근황",
            "개봉",
            "예매",
            "일정",
            "신곡",
            "앨범",
            "콘서트",
            "공연",
            "투어",
        }
        broad_topic_markers = {
            "후기",
            "리뷰",
            "비교",
            "공략",
            "가이드",
            "방법",
            "사용법",
            "문제",
            "오류",
            "이슈",
            "논란",
            "평가",
            "반응",
            "행사",
            "이벤트",
            "협업",
        }
        if intent_kind == SearchIntentKind.LIVE_LATEST or any(marker in normalized for marker in live_markers):
            return "live"
        if intent_kind == SearchIntentKind.EXTERNAL_FACT:
            return "entity"
        if 1 <= len(query_terms) <= 3 and not any(marker in normalized for marker in broad_topic_markers):
            return "entity"
        return "general"

    def _expand_web_search_queries(
        self,
        *,
        query: str,
        intent_kind: str | None = None,
        answer_mode: str | None = None,
        freshness_risk: str | None = None,
    ) -> list[str]:
        normalized_query = " ".join(str(query or "").split()).strip()
        if not normalized_query:
            return []
        query_profile = self._infer_web_query_profile(
            query=normalized_query,
            intent_kind=intent_kind,
            answer_mode=answer_mode,
            freshness_risk=freshness_risk,
        )
        variants = [normalized_query]
        if query_profile == "entity":
            variants.extend(
                [
                    f"{normalized_query} 소개",
                    f"{normalized_query} 설명",
                    f"{normalized_query} 위키",
                    f"{normalized_query} 공식",
                ]
            )
        elif query_profile == "live":
            if "날씨" in normalized_query:
                variants.extend([f"{normalized_query} 예보", f"{normalized_query} 기상"])
            elif any(marker in normalized_query for marker in ["뉴스", "속보", "소식", "근황"]):
                variants.extend([f"{normalized_query} 뉴스", f"{normalized_query} 최신"])
        deduped: list[str] = []
        seen: set[str] = set()
        for variant in variants:
            compact = " ".join(variant.split()).strip()
            if not compact:
                continue
            key = compact.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(compact)
        return deduped[:4]

    def _build_source_policy_decision(
        self,
        *,
        query: str,
        url: str,
        title: str,
        summary_text: str,
    ):
        descriptive_source = self._looks_like_descriptive_web_source(
            query=query,
            title=title,
            summary_text=summary_text,
        )
        return build_source_policy(
            url=url,
            descriptive_source=descriptive_source,
            official_domain=self._looks_like_official_product_domain(url),
            opinion_or_blog=self._looks_like_opinion_or_blog_source(title=title, summary_text=summary_text),
            event_or_campaign=self._looks_like_event_or_campaign_source(title=title, summary_text=summary_text),
            operational_noise=(
                self._looks_like_operational_entity_noise(summary_text)
                or self._looks_like_noisy_web_segment(summary_text)
            ),
            community_domain=self._looks_like_game_portal_or_community_domain(url),
        )

    def _classify_web_source_kind(self, url: str) -> str:
        hostname = urlparse(str(url or "").strip()).netloc.lower()
        if not hostname:
            return "unknown"
        if any(
            hostname == host or hostname.endswith(f".{host}")
            for host in ("naver.com", "daum.net", "inven.co.kr")
        ):
            return "portal"
        if any(
            hostname == host or hostname.endswith(f".{host}")
            for host in ("namu.wiki", "wikipedia.org", "encykorea.aks.ac.kr", "britannica.com")
        ):
            return "encyclopedia"
        if any(
            hostname == host or hostname.endswith(f".{host}")
            for host in (
                "youtube.com",
                "youtu.be",
                "instagram.com",
                "facebook.com",
                "x.com",
                "twitter.com",
                "tiktok.com",
            )
        ):
            return "video"
        if any(
            hostname == host or hostname.endswith(f".{host}")
            for host in ("tistory.com", "blog.naver.com", "velog.io", "brunch.co.kr", "medium.com")
        ):
            return "blog"
        if hostname.startswith("search.") or hostname in {"www.google.com", "google.com", "search.naver.com"}:
            return "portal"
        news_domain_hosts = (
            "chosun.com",
            "joongang.co.kr",
            "donga.com",
            "yna.co.kr",
            "dt.co.kr",
            "edaily.co.kr",
            "etoday.co.kr",
            "hani.co.kr",
            "hankyung.com",
            "heraldcorp.com",
            "khan.co.kr",
            "mk.co.kr",
            "moneytoday.co.kr",
            "newdaily.co.kr",
            "sedaily.com",
            "seoul.co.kr",
            "mt.co.kr",
            "sportsseoul.com",
            "sportschosun.com",
            "newsen.com",
            "xportsnews.com",
            "zdnet.co.kr",
            "dispatch.co.kr",
            "segye.com",
            "sisajournal.com",
            "kyeonggi.com",
            "sisafocus.co.kr",
            "ikbc.co.kr",
            "kado.net",
            "ggilbo.com",
            "idaegu.com",
            "kyeongin.com",
            "yeongnam.com",
            "jemin.com",
            "jeonmae.co.kr",
            "gndomin.com",
            "kwangju.co.kr",
            "ksilbo.co.kr",
            "imaeil.com",
            "kookje.co.kr",
            "jnilbo.com",
            "jjan.kr",
            "iusm.co.kr",
            "mdilbo.com",
            "idaebae.com",
            "kbsm.net",
            "incheonilbo.com",
            "daejonilbo.com",
            "kihoilbo.co.kr",
            "kyeongbuk.co.kr",
            "goodmorningcc.com",
            "cctoday.co.kr",
            "chungnamilbo.co.kr",
            "daejeonilbo.com",
            "joongdo.co.kr",
            "dynews.co.kr",
            "ccdailynews.com",
            "jbnews.com",
            "gjdream.com",
            "jejunews.com",
            "headlinejeju.co.kr",
            "ohmynews.com",
            "pressian.com",
            "nocutnews.co.kr",
            "newsis.com",
            "news1.kr",
            "mbn.co.kr",
            "sbs.co.kr",
            "kbs.co.kr",
            "ytn.co.kr",
            "jtbc.co.kr",
            "ichannela.com",
            "tvchosun.com",
            "etnews.com",
            "bloter.net",
            "news.naver.com",
            "v.daum.net",
            "news.daum.net",
            "news.nate.com",
            "news.zum.com",
        )
        if any(
            hostname == host or hostname.endswith(f".{host}")
            for host in news_domain_hosts
        ):
            return "news"
        return "general"

    def _source_hostname(self, url: str) -> str:
        return urlparse(str(url or "").strip()).netloc.lower()

    def _looks_like_game_portal_or_community_domain(self, url: str) -> bool:
        hostname = urlparse(str(url or "").strip()).netloc.lower()
        if not hostname:
            return False
        community_hosts = (
            "inven.co.kr",
            "arca.live",
            "ruliweb.com",
            "dcinside.com",
            "thisisgame.com",
            "bbs.ruliweb.com",
            "m.inven.co.kr",
            "game.naver.com",
        )
        return any(hostname == host or hostname.endswith(f".{host}") for host in community_hosts)

    def _looks_like_official_product_domain(self, url: str) -> bool:
        hostname = urlparse(str(url or "").strip()).netloc.lower()
        if not hostname:
            return False
        official_hosts = (
            "nexon.com",
            "pearlabyss.com",
            "plaync.com",
            "ncsoft.com",
            "netmarble.com",
            "netmarble.net",
            "krafton.com",
            "blizzard.com",
            "riotgames.com",
            "mihoyo.com",
            "hoyoverse.com",
            "epicgames.com",
            "steampowered.com",
        )
        if any(hostname == host or hostname.endswith(f".{host}") for host in official_hosts):
            return True
        return "official" in hostname

    def _looks_like_descriptive_web_source(self, *, query: str, title: str, summary_text: str) -> bool:
        normalized_title = re.sub(r"[\s\-–—|:·]+", " ", str(title or "").lower()).strip()
        normalized_summary = " ".join(str(summary_text or "").lower().split()).strip()
        query_terms = self._extract_web_query_terms(query)
        joined_query = " ".join(query_terms).strip()
        squashed_query = "".join(query_terms).strip()
        if joined_query and (
            normalized_title == joined_query
            or normalized_title.startswith(f"{joined_query} ")
            or normalized_title.endswith(f" {joined_query}")
        ):
            return True
        if squashed_query and (
            normalized_title == squashed_query
            or normalized_title.startswith(f"{squashed_query} ")
            or normalized_title.endswith(f" {squashed_query}")
        ):
            return True
        descriptive_markers = [
            "는 대한민국의",
            "는 한국의",
            "은 대한민국의",
            "은 한국의",
            "서비스하는",
            "온라인 액션 rpg",
            "온라인 rpg",
            "보이 그룹",
            "가수이자 배우",
            "게임이다",
            "서비스이다",
            "브랜드이다",
            "사이트이다",
            "개발 중인",
            "배경으로",
            "특징으로 소개",
            "설명하는",
        ]
        if any(marker in normalized_summary for marker in descriptive_markers):
            return True
        if any(marker in normalized_title for marker in ["위키백과", "나무위키", "백과"]):
            return True
        return False

    def _looks_like_opinion_or_blog_source(self, *, title: str, summary_text: str) -> bool:
        combined = " ".join(f"{title} {summary_text}".split()).lower()
        markers = [
            "블로그",
            "후기",
            "리뷰",
            "공략",
            "팁",
            "체험기",
            "소감",
            "평이 있다",
            "평이 많",
            "평가된다",
            "라는 평",
            "느낌",
        ]
        return any(marker in combined for marker in markers)

    def _looks_like_event_or_campaign_source(self, *, title: str, summary_text: str) -> bool:
        combined = " ".join(f"{title} {summary_text}".split()).lower()
        markers = [
            "이벤트",
            "협업",
            "콜라보",
            "프로모션",
            "사전예약",
            "쿠폰",
            "혜택",
            "기념",
            "행사",
            "반응",
            "논란",
            "비판",
            "후기",
            "리뷰",
            "공략",
            "기사",
            "뉴스",
            "예매",
            "공연",
            "콘서트",
            "투어",
            "신곡",
            "앨범",
        ]
        return any(marker in combined for marker in markers)

    def _looks_like_operational_entity_noise(self, text: str) -> bool:
        normalized = " ".join(str(text or "").split()).lower()
        if not normalized:
            return False
        markers = [
            "업데이트",
            "점검",
            "패치",
            "영상 더보기",
            "구매",
            "예약",
            "설치",
            "다운로드",
            "권장 사양",
            "최소 사양",
            "쿠폰",
            "이벤트",
            "협업",
            "콜라보",
            "스킨",
            "패시브",
            "어빌리티",
            "코강",
            "보상",
            "출석",
            "게시판",
            "커뮤니티",
            "공식 카페",
            "인벤",
            "갤러리",
            "팬아트",
            "season pass",
            "battle pass",
            "플레이를 막기 위해",
            "출시일 전",
        ]
        marker_count = sum(1 for marker in markers if marker in normalized)
        if marker_count >= 2:
            return True
        if marker_count >= 1 and bool(re.search(r"\b20\d{2}\b|\bver\.\d", normalized)):
            return True
        return False

    def _looks_like_narrative_entity_line(self, text: str) -> bool:
        normalized = " ".join(str(text or "").split()).strip()
        if not normalized:
            return False
        markers = [
            "여러분은",
            "떠나게 됩니다",
            "세상을 구하기",
            "과제는",
            "주변 정보",
            "게임 정보를",
            "찾아내야 하는",
            "읽어주는 랜턴",
            "빛 반사",
            "필요한 것이",
            "그중에서도",
            "스스로 비춰서",
            "대부분이다",
            "위험으로부터",
            "모든 것을 되찾고",
            "여정을 떠나",
            "모험을 펼칠 수 있습니다",
            "평이 있다",
            "평가된다",
            "느낌이",
        ]
        if any(marker in normalized for marker in markers):
            return True
        if "|" in normalized and not any(marker in normalized for marker in ["이다", "입니다", "특징", "배경"]):
            return True
        if bool(re.search(r"\bpearl abyss\b|\bnexon\b|\bkrafton\b", normalized.lower())) and "|" in normalized:
            return True
        return False

    def _extract_entity_fact_bullets(
        self,
        *,
        query: str,
        candidate_lines: list[tuple[int, str]],
    ) -> list[str]:
        bullets: list[str] = []
        seen: set[str] = set()

        def add_bullet(label: str, value: str) -> None:
            compact = " ".join(str(value or "").split()).strip(" .")
            if not compact:
                return
            for index, existing in enumerate(list(bullets)):
                parsed = self._split_entity_fact_bullet(existing)
                if not parsed or parsed[0] != label:
                    continue
                existing_value = parsed[1]
                if compact == existing_value or compact in existing_value:
                    return
                if existing_value in compact:
                    replacement = f"{label}: {compact}"
                    seen.discard(existing)
                    seen.add(replacement)
                    bullets[index] = replacement
                    return
            bullet = f"{label}: {compact}"
            if bullet in seen:
                return
            seen.add(bullet)
            bullets.append(bullet)

        for score, line in candidate_lines:
            if score < 6:
                continue
            normalized = " ".join(str(line or "").split()).strip()
            if not normalized:
                continue
            if self._looks_like_narrative_entity_line(normalized):
                continue
            lowered = normalized.lower()

            developer_match = (
                re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)가\s+개발\s+중인", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)가\s+개발한", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)가\s+개발하는", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)에서\s+개발\s+중인", normalized)
            )
            if developer_match:
                add_bullet("개발", developer_match.group(1))

            service_match = (
                re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)이\s+서비스하는", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)가\s+서비스하는", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)이\s+운영하는", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)가\s+운영하는", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)이\s+배급하는", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)가\s+배급하는", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)이\s+제공하는", normalized)
                or re.search(rf"{re.escape(query)}(?:는|은)\s+(.+?)가\s+제공하는", normalized)
            )
            if service_match:
                add_bullet("서비스/배급", service_match.group(1))

            if "개발 중" in normalized:
                add_bullet("상태", "개발 중")
            elif "출시 예정" in normalized:
                add_bullet("상태", "출시 예정")
            elif "서비스 중" in normalized or "운영 중" in normalized:
                add_bullet("상태", "서비스 중")
            elif "정식 출시" in normalized:
                add_bullet("상태", "정식 출시")

            genre_markers = [
                "오픈월드",
                "액션",
                "어드벤처",
                "rpg",
                "mmorpg",
                "fps",
                "전략",
                "시뮬레이션",
                "서바이벌",
                "싱글 플레이",
                "멀티플레이",
            ]
            genre_display_map = {
                "rpg": "RPG",
                "mmorpg": "MMORPG",
                "fps": "FPS",
            }
            matched_genres = [genre_display_map.get(marker, marker) for marker in genre_markers if marker in lowered]
            if "게임" in normalized and matched_genres:
                ordered_genres: list[str] = []
                for marker in matched_genres:
                    if marker not in ordered_genres:
                        ordered_genres.append(marker)
                add_bullet("장르/성격", " ".join(ordered_genres) + " 게임")

            access_markers = []
            for marker in ["온라인", "모바일", "pc", "콘솔"]:
                if marker in lowered:
                    access_markers.append("PC" if marker == "pc" else marker)
            if access_markers:
                ordered_access: list[str] = []
                for marker in access_markers:
                    if marker not in ordered_access:
                        ordered_access.append(marker)
                add_bullet("이용 형태", " / ".join(ordered_access))

            setting_match = re.search(r"(.+?)을 배경으로\s+(.+)", normalized)
            if setting_match:
                setting_subject = " ".join(setting_match.group(1).split()).strip()
                setting_rest = " ".join(setting_match.group(2).split()).strip(" .")
                if setting_subject and setting_rest:
                    add_bullet("배경", f"{setting_subject}을 배경으로 {setting_rest}")
                    continue

            if any(marker in normalized for marker in ["특징", "소개된다", "소개됩니다"]):
                add_bullet("특징", normalized.rstrip("."))
            elif "배경으로" not in normalized and any(marker in normalized for marker in ["싱글 플레이", "멀티플레이", "전투", "탐험"]):
                add_bullet("플레이 특징", normalized.rstrip("."))

            if len(bullets) >= 5:
                break

        if not any(
            bullet.startswith("특징:") or bullet.startswith("플레이 특징:")
            for bullet in bullets
        ):
            for score, line in candidate_lines:
                if score < 6:
                    continue
                normalized = " ".join(str(line or "").split()).strip()
                if not normalized:
                    continue
                if self._looks_like_narrative_entity_line(normalized):
                    continue
                if self._looks_like_operational_entity_noise(normalized):
                    continue
                if "|" in normalized:
                    continue
                if any(marker in normalized for marker in ["특징", "소개된다", "소개됩니다"]):
                    add_bullet("특징", normalized.rstrip("."))
                    break
                if "배경으로" not in normalized and any(marker in normalized for marker in ["싱글 플레이", "멀티플레이", "전투", "탐험"]):
                    add_bullet("플레이 특징", normalized.rstrip("."))
                    break

        return bullets[:5]

    def _score_entity_fact_line(self, *, line: str, query: str, source_title: str) -> int:
        normalized = " ".join(str(line or "").split()).strip()
        lowered = normalized.lower()
        query_terms = self._extract_web_query_terms(query)
        score = 0
        if not normalized:
            return -99
        if self._looks_like_noisy_web_segment(normalized):
            score -= 12
        if self._looks_like_contact_or_legal_web_segment(normalized):
            score -= 14
        if self._looks_like_operational_entity_noise(normalized):
            score -= 10
        if self._looks_like_narrative_entity_line(normalized):
            score -= 12
        if 20 <= len(normalized) <= 180:
            score += 4
        elif len(normalized) <= 260:
            score += 2
        else:
            score -= 2
        for term in query_terms:
            if term in lowered:
                score += 4
        descriptive_markers = [
            "대한민국의",
            "한국의",
            "온라인",
            "오픈월드",
            "액션",
            "어드벤처",
            "rpg",
            "게임",
            "가수",
            "배우",
            "그룹",
            "기업",
            "브랜드",
            "서비스",
            "플랫폼",
            "작품",
            "세계관",
            "배경",
            "주인공",
            "특징",
            "서비스하는",
            "개발한",
            "배급한",
            "출시 예정",
        ]
        marker_count = sum(1 for marker in descriptive_markers if marker in lowered)
        score += marker_count * 2
        if "|" in normalized:
            score -= 9
        if re.search(r"\bpearl abyss\b|\bnexon\b|\bkrafton\b", lowered):
            score -= 4
        if any(marker in normalized for marker in ["가이드", "공략", "팁", "팁과", "방법", "추천"]):
            score -= 5
        if any(marker in lowered for marker in ["이다", "입니다", "작품이다", "게임이다", "서비스이다"]):
            score += 3
        if any(marker in str(source_title or "") for marker in ["위키", "백과", "공식"]):
            score += 2
        if re.search(r"\b20\d{2}\b|\bver\.\d", lowered):
            score -= 2
        return score

    def _extract_entity_context_lines(
        self,
        *,
        candidate_lines: list[tuple[int, str]],
        intro_line: str,
        detail_lines: list[str],
        max_items: int = 4,
    ) -> list[str]:
        def _normalize(line: str) -> str:
            compact = " ".join(str(line or "").split()).strip().lower()
            compact = re.sub(r"^[^:]+:\s*", "", compact)
            compact = compact.rstrip(".")
            return compact

        def _overlaps(line: str, existing: set[str]) -> bool:
            normalized = _normalize(line)
            if not normalized:
                return True
            for item in existing:
                if not item:
                    continue
                if normalized == item or normalized in item or item in normalized:
                    return True
            return False

        seen = {_normalize(intro_line), *[_normalize(detail) for detail in detail_lines]}
        context_lines: list[str] = []
        for score, line in candidate_lines[1:20]:
            cleaned = " ".join(str(line or "").split()).strip()
            if score < 6 or not cleaned:
                continue
            if self._looks_like_narrative_entity_line(cleaned):
                continue
            if self._looks_like_operational_entity_noise(cleaned):
                continue
            if "|" in cleaned:
                continue
            if " - " in cleaned and len(cleaned) <= 60:
                continue
            if _overlaps(cleaned, seen):
                continue
            context_lines.append(cleaned.rstrip("."))
            seen.add(_normalize(cleaned))
            if len(context_lines) >= max_items:
                break
        return context_lines

    def _select_korean_particle(self, text: str, pair: str) -> str:
        compact = " ".join(str(text or "").split()).strip()
        if len(pair) != 2 or not compact:
            return pair[-1:] or ""
        last_char = compact[-1]
        if "가" <= last_char <= "힣":
            has_final = (ord(last_char) - 0xAC00) % 28 != 0
            return pair[0] if has_final else pair[1]
        return pair[1]

    def _web_source_role_label(self, *, query: str, source: dict[str, Any]) -> str:
        url = str(source.get("url") or "").strip()
        title = str(source.get("title") or source.get("result_title") or "").strip()
        summary_text = str(source.get("summary_text") or source.get("snippet") or title).strip()
        source_policy = self._build_source_policy_decision(
            query=query,
            url=url,
            title=title,
            summary_text=summary_text,
        )
        return source_policy.role_label

    def _entity_source_role_label(self, *, query: str, source: dict[str, Any]) -> str:
        return self._web_source_role_label(query=query, source=source)

    def _split_entity_fact_bullet(self, bullet: str) -> tuple[str, str] | None:
        if ":" not in str(bullet or ""):
            return None
        label, value = str(bullet).split(":", 1)
        compact_label = " ".join(label.split()).strip()
        compact_value = " ".join(value.split()).strip().rstrip(".")
        if not compact_label or not compact_value:
            return None
        return compact_label, compact_value

    def _preferred_entity_source_segments(self, source: dict[str, Any]) -> list[str]:
        candidates: list[str] = []
        snippet_text = str(source.get("snippet") or "").strip()
        summary_text = str(source.get("summary_text") or "").strip()
        context_text = str(source.get("context_text") or "").strip()
        if snippet_text:
            candidates.extend(self._split_web_page_segments(snippet_text))
        if summary_text and not (
            self._looks_like_noisy_web_segment(summary_text)
            or self._looks_like_contact_or_legal_web_segment(summary_text)
            or self._looks_like_operational_entity_noise(summary_text)
        ):
            candidates.extend(self._split_web_page_segments(summary_text))
        if context_text:
            for segment in self._split_web_page_segments(context_text):
                if (
                    self._looks_like_noisy_web_segment(segment)
                    or self._looks_like_contact_or_legal_web_segment(segment)
                    or self._looks_like_operational_entity_noise(segment)
                ):
                    continue
                candidates.append(segment)
        deduped: list[str] = []
        seen_segments: set[str] = set()
        for candidate in candidates:
            compact = " ".join(candidate.split()).strip()
            if not compact:
                continue
            key = compact.lower()
            if key in seen_segments:
                continue
            seen_segments.add(key)
            deduped.append(compact)
        return deduped

    def _extract_entity_source_fact_bullets(self, *, query: str, source: dict[str, Any]) -> list[str]:
        source_title = str(source.get("title") or source.get("result_title") or "").strip()
        candidate_lines: list[tuple[int, str]] = []
        for segment in self._preferred_entity_source_segments(source):
            score = self._score_entity_fact_line(
                line=segment,
                query=query,
                source_title=source_title,
            )
            if score > 0:
                candidate_lines.append((score, segment))
        if not candidate_lines:
            return []
        candidate_lines.sort(reverse=True)
        return self._extract_entity_fact_bullets(
            query=query,
            candidate_lines=candidate_lines,
        )

    def _entity_fact_values_overlap(self, left: str, right: str) -> bool:
        normalized_left = " ".join(str(left or "").split()).strip().lower().rstrip(".")
        normalized_right = " ".join(str(right or "").split()).strip().lower().rstrip(".")
        if not normalized_left or not normalized_right:
            return False
        return (
            normalized_left == normalized_right
            or normalized_left in normalized_right
            or normalized_right in normalized_left
        )

    def _collect_entity_source_fact_bullets(
        self,
        *,
        query: str,
        sources: list[dict[str, Any]],
    ) -> list[tuple[str, list[str]]]:
        collected: list[tuple[str, list[str]]] = []
        for source in sources:
            source_url = str(source.get("url") or "").strip()
            bullets = self._extract_entity_source_fact_bullets(query=query, source=source)
            if bullets:
                collected.append((source_url, bullets))
        return collected

    def _build_entity_claim_confirmation_queries(
        self,
        *,
        query: str,
        slot: str,
        claim_value: str,
    ) -> list[str]:
        compact_value = " ".join(str(claim_value or "").split()).strip().rstrip(".")
        if not compact_value or len(compact_value) > 48:
            return []

        query_map: dict[str, list[str]] = {
            "개발": [f"{query} {compact_value} 개발", f"{query} 개발사 {compact_value}"],
            "서비스/배급": [f"{query} {compact_value} 서비스", f"{query} {compact_value} 배급"],
            "장르/성격": [f"{query} {compact_value}", f"{query} 장르 {compact_value}"],
            "상태": [f"{query} {compact_value}", f"{query} 상태 {compact_value}"],
            "이용 형태": [f"{query} {compact_value} 플랫폼", f"{query} {compact_value}"],
        }
        return query_map.get(slot, [])

    def _build_entity_slot_probe_queries(
        self,
        *,
        query: str,
        slot: str,
        status: str,
        primary_claim: ClaimRecord | None,
    ) -> list[str]:
        compact_value = " ".join(str(getattr(primary_claim, "value", "") or "").split()).strip().rstrip(".")
        if status == CoverageStatus.WEAK and compact_value:
            query_map: dict[str, list[str]] = {
                "개발": [f"{query} {compact_value} 개발사 공식", f"{query} {compact_value} 개발사 위키"],
                "서비스/배급": [f"{query} {compact_value} 서비스 공식", f"{query} {compact_value} 운영 공식"],
                "장르/성격": [f"{query} {compact_value} 장르 위키", f"{query} {compact_value} 소개"],
                "상태": [f"{query} {compact_value} 공식", f"{query} {compact_value} 출시 상태"],
                "이용 형태": [f"{query} {compact_value} 플랫폼 공식", f"{query} {compact_value} 플랫폼"],
            }
            return query_map.get(slot, [])

        query_map = {
            "개발": [f"{query} 개발사 공식", f"{query} 개발사 위키", f"{query} 개발사"],
            "서비스/배급": [f"{query} 서비스 공식", f"{query} 운영사 공식", f"{query} 배급"],
            "장르/성격": [f"{query} 장르 위키", f"{query} 소개", f"{query} 설명"],
            "상태": [f"{query} 출시 상태 공식", f"{query} 공식 출시", f"{query} 개발 중"],
            "이용 형태": [f"{query} 공식 플랫폼", f"{query} 플랫폼 위키", f"{query} 플랫폼"],
        }
        return query_map.get(slot, [])

    def _extract_entity_fact_labels(self, *, bullets: list[str]) -> set[str]:
        labels: set[str] = set()
        for bullet in bullets:
            parsed = self._split_entity_fact_bullet(bullet)
            if not parsed:
                continue
            labels.add(parsed[0])
        return labels

    def _build_entity_second_pass_queries(
        self,
        *,
        query: str,
        selected_sources: list[dict[str, Any]],
        existing_queries: list[str],
    ) -> list[str]:
        claim_records = self._build_entity_claim_records(
            query=query,
            selected_sources=selected_sources,
        )
        coverage = summarize_slot_coverage(claim_records, slots=CORE_ENTITY_SLOTS)
        strong_slots = {slot for slot, item in coverage.items() if item.status == CoverageStatus.STRONG}
        has_distribution_or_access = bool({"서비스/배급", "이용 형태"} & strong_slots)
        if (
            len(strong_slots) >= 4
            and {"개발", "장르/성격"} <= strong_slots
            and has_distribution_or_access
        ):
            return []

        slot_priority = {
            "개발": 0,
            "서비스/배급": 1,
            "장르/성격": 2,
            "이용 형태": 3,
            "상태": 4,
        }
        seen_queries = {" ".join(str(item or "").split()).strip().lower() for item in existing_queries}
        second_pass_queries: list[str] = []
        prior_slot_probe_counts: dict[str, int] = {}
        for existing_query in existing_queries:
            probed_slot = self._entity_slot_from_search_query(query=query, matched_query=existing_query)
            if not probed_slot:
                continue
            prior_slot_probe_counts[probed_slot] = prior_slot_probe_counts.get(probed_slot, 0) + 1

        pending_slots = [
            (slot, slot_coverage)
            for slot, slot_coverage in coverage.items()
            if slot_coverage.status != CoverageStatus.STRONG
        ]
        pending_slots.sort(
            key=lambda item: (
                0
                if item[1].status == CoverageStatus.MISSING and prior_slot_probe_counts.get(item[0], 0) >= 1
                else 1
                if item[1].status == CoverageStatus.MISSING
                else 2
                if prior_slot_probe_counts.get(item[0], 0) >= 1
                else 3,
                -prior_slot_probe_counts.get(item[0], 0),
                slot_priority.get(item[0], 99),
            )
        )
        for label, slot_coverage in pending_slots:
            confirmation_variants: list[str] = []
            if slot_coverage.primary_claim is not None:
                confirmation_variants = self._build_entity_claim_confirmation_queries(
                    query=query,
                    slot=label,
                    claim_value=slot_coverage.primary_claim.value,
                )
            probe_variants = self._build_entity_slot_probe_queries(
                query=query,
                slot=label,
                status=slot_coverage.status,
                primary_claim=slot_coverage.primary_claim,
            )
            prior_probe_count = prior_slot_probe_counts.get(label, 0)
            source_role = (
                str(getattr(slot_coverage.primary_claim, "source_role", "") or "").strip()
                if slot_coverage.primary_claim is not None
                else ""
            )
            prefer_probe_first = (
                slot_coverage.status == CoverageStatus.MISSING
                or prior_probe_count >= 1
                or (slot_coverage.status == CoverageStatus.WEAK and source_role != SourceRole.OFFICIAL)
            )
            ordered_variants = (
                [*probe_variants, *confirmation_variants]
                if prefer_probe_first
                else [*confirmation_variants, *probe_variants]
            )
            added_for_slot = 0
            max_queries_for_slot = (
                2
                if slot_coverage.status == CoverageStatus.WEAK and (prior_probe_count >= 1 or source_role != SourceRole.OFFICIAL)
                else 1
            )
            for variant in ordered_variants:
                normalized = " ".join(str(variant or "").split()).strip()
                key = normalized.lower()
                if not normalized or key in seen_queries:
                    continue
                seen_queries.add(key)
                second_pass_queries.append(normalized)
                added_for_slot += 1
                if added_for_slot >= max_queries_for_slot:
                    break
            if len(second_pass_queries) >= 4:
                break
        return second_pass_queries

    def _entity_source_fact_agreement_score(
        self,
        *,
        source_index: int,
        sources: list[dict[str, Any]],
        fact_bullets_by_index: dict[int, list[str]],
        trust_score_by_index: dict[int, int] | None = None,
    ) -> int:
        source_bullets = fact_bullets_by_index.get(source_index) or []
        if not source_bullets:
            return 0
        peers_by_label: dict[str, list[int]] = {}
        parsed_source = [self._split_entity_fact_bullet(bullet) for bullet in source_bullets]
        parsed_source = [item for item in parsed_source if item]
        for peer_index, peer_source in enumerate(sources):
            if peer_index == source_index:
                continue
            peer_bullets = fact_bullets_by_index.get(peer_index) or []
            parsed_peer = [self._split_entity_fact_bullet(bullet) for bullet in peer_bullets]
            parsed_peer = [item for item in parsed_peer if item]
            if not parsed_peer:
                continue
            matched_labels: set[str] = set()
            for source_label, source_value in parsed_source:
                for peer_label, peer_value in parsed_peer:
                    if source_label != peer_label:
                        continue
                    if not self._entity_fact_values_overlap(source_value, peer_value):
                        continue
                    matched_labels.add(source_label)
                    break
            for label in matched_labels:
                if label not in peers_by_label:
                    peers_by_label[label] = []
                peers_by_label[label].append(peer_index)
        if not peers_by_label:
            return 0
        agreement_score = 0
        for label, peer_indices in peers_by_label.items():
            count = len(peer_indices)
            agreement_score += 4
            if trust_score_by_index:
                best_peer_trust = max(trust_score_by_index.get(idx, 0) for idx in peer_indices)
                if best_peer_trust >= 7:
                    agreement_score += 2
            if count >= 2:
                agreement_score += 2
            if self._entity_fact_sort_key(label)[0] <= 4:
                agreement_score += 1
        if len(peers_by_label) >= 2:
            agreement_score += 3
        return agreement_score

    def _entity_slot_from_probe_text(self, text: str) -> str | None:
        normalized_text = " ".join(str(text or "").split()).strip().lower()
        if not normalized_text:
            return None
        slot_keywords = [
            ("이용 형태", ["플랫폼", "pc", "콘솔", "모바일", "온라인"]),
            ("서비스/배급", ["서비스", "운영사", "운영", "배급"]),
            ("개발", ["개발사", "개발"]),
            ("상태", ["출시 상태", "공식 출시", "개발 중", "출시"]),
            ("장르/성격", ["장르"]),
        ]
        for slot, keywords in slot_keywords:
            if any(keyword in normalized_text for keyword in keywords):
                return slot
        return None

    def _entity_slot_from_search_query(self, *, query: str, matched_query: str) -> str | None:
        normalized_query = " ".join(str(query or "").split()).strip().lower()
        normalized_matched_query = " ".join(str(matched_query or "").split()).strip().lower()
        if not normalized_matched_query or normalized_matched_query == normalized_query:
            return None
        return self._entity_slot_from_probe_text(normalized_matched_query)

    def _entity_source_probe_bonus(
        self,
        *,
        query: str,
        source: dict[str, Any],
        fact_bullets: list[str] | None = None,
    ) -> int:
        matched_query = str(source.get("matched_query") or "").strip()
        slot = self._entity_slot_from_search_query(query=query, matched_query=matched_query)
        if not slot:
            return 0

        parsed_bullets = [
            parsed
            for parsed in (
                self._split_entity_fact_bullet(bullet)
                for bullet in (fact_bullets or self._extract_entity_source_fact_bullets(query=query, source=source))
            )
            if parsed
        ]
        if not any(label == slot for label, _ in parsed_bullets):
            return 0

        source_role = self._entity_source_role_label(query=query, source=source)
        bonus = 6
        if source_role in TRUSTED_CLAIM_SOURCE_ROLES:
            bonus += 2
        normalized_matched_query = " ".join(matched_query.split()).strip().lower()
        if "공식" in normalized_matched_query and source_role == SourceRole.OFFICIAL:
            bonus += 2
        return bonus

    def _entity_fact_sort_key(self, label: str) -> tuple[int, str]:
        priority = {
            "개발": 0,
            "서비스/배급": 1,
            "상태": 2,
            "장르/성격": 3,
            "이용 형태": 4,
            "배경": 5,
            "특징": 6,
            "플레이 특징": 7,
        }
        return (priority.get(label, 99), label)

    def _merge_entity_fact_consensus(
        self,
        *,
        query: str,
        fact_groups: dict[str, list[dict[str, Any]]],
        label: str,
        value: str,
        source_url: str,
    ) -> None:
        compact_value = " ".join(str(value or "").split()).strip().rstrip(".")
        if not compact_value:
            return

        label_items = fact_groups.setdefault(label, [])
        normalized_value = compact_value.lower()
        for item in label_items:
            existing_value = str(item.get("value") or "")
            existing_normalized = existing_value.lower()
            if (
                normalized_value == existing_normalized
                or normalized_value in existing_normalized
                or existing_normalized in normalized_value
            ):
                if len(compact_value) > len(existing_value):
                    item["value"] = compact_value
                if source_url:
                    item.setdefault("sources", set()).add(source_url)
                item["count"] = len(item.get("sources") or set())
                return

        sources: set[str] = set()
        if source_url:
            sources.add(source_url)
        label_items.append(
            {
                "value": compact_value,
                "sources": sources,
                "count": len(sources),
            }
        )

    def _build_consensus_entity_fact_bullets(
        self,
        *,
        query: str,
        source_fact_bullets: list[tuple[str, list[str]]],
    ) -> list[str]:
        fact_groups: dict[str, list[dict[str, Any]]] = {}
        for source_url, bullets in source_fact_bullets:
            for bullet in bullets:
                parsed = self._split_entity_fact_bullet(bullet)
                if not parsed:
                    continue
                label, value = parsed
                self._merge_entity_fact_consensus(
                    query=query,
                    fact_groups=fact_groups,
                    label=label,
                    value=value,
                    source_url=source_url,
                )

        bullet_items: list[tuple[int, str, str]] = []
        for label, items in fact_groups.items():
            for item in items:
                support_count = int(item.get("count") or 0)
                value = str(item.get("value") or "").strip()
                if not value:
                    continue
                bullet_items.append((support_count, label, value))

        if not bullet_items:
            return []

        core_labels = {"개발", "서비스/배급", "상태", "장르/성격", "이용 형태"}
        consensus_items = [item for item in bullet_items if item[0] >= 2]
        preferred_items = list(consensus_items)

        if consensus_items:
            for support_count, label, value in bullet_items:
                if len(preferred_items) >= 6:
                    break
                if support_count >= 2:
                    continue
                if label not in core_labels:
                    continue
                preferred_items.append((support_count, label, value))
        else:
            preferred_items = list(bullet_items)

        scored_bullets: list[tuple[int, int, int, str]] = []
        for support_count, label, value in preferred_items:
            scored_bullets.append(
                (
                    support_count,
                    -self._entity_fact_sort_key(label)[0],
                    len(value),
                    f"{label}: {value}",
                )
            )

        scored_bullets.sort(reverse=True)
        return [bullet for _, _, _, bullet in scored_bullets[:6]]

    def _build_entity_claim_records(
        self,
        *,
        query: str,
        selected_sources: list[dict[str, Any]],
    ) -> list[ClaimRecord]:
        records: list[ClaimRecord] = []
        for source in selected_sources:
            source_url = str(source.get("url") or "").strip()
            source_title = str(source.get("title") or source.get("result_title") or "").strip()
            source_role = self._entity_source_role_label(query=query, source=source)
            role_confidence = {
                SourceRole.WIKI: 0.95,
                SourceRole.OFFICIAL: 0.9,
                SourceRole.DESCRIPTIVE: 0.75,
                SourceRole.NEWS: 0.55,
                SourceRole.PORTAL: 0.45,
                SourceRole.BLOG: 0.35,
                SourceRole.AUXILIARY: 0.4,
            }.get(source_role, 0.4)
            for bullet in self._extract_entity_source_fact_bullets(query=query, source=source):
                parsed = self._split_entity_fact_bullet(bullet)
                if not parsed:
                    continue
                slot, value = parsed
                records.append(
                    ClaimRecord(
                        slot=slot,
                        value=value,
                        source_url=source_url,
                        source_title=source_title,
                        source_role=source_role,
                        support_count=1,
                        confidence=role_confidence,
                    )
                )
        return merge_claim_records(records)

    def _entity_claim_sort_key(self, claim: ClaimRecord) -> tuple[int, int, int, int, str]:
        role_priority = {
            SourceRole.WIKI: 4,
            SourceRole.OFFICIAL: 3,
            SourceRole.DESCRIPTIVE: 2,
            SourceRole.NEWS: 1,
            SourceRole.AUXILIARY: 1,
            SourceRole.PORTAL: 0,
            SourceRole.BLOG: 0,
        }
        return (
            claim.support_count,
            role_priority.get(claim.source_role, 0),
            int(claim.confidence * 1000),
            len(claim.value),
            claim.value,
        )

    def _select_entity_fact_card_claims(
        self,
        *,
        query: str,
        claim_records: list[ClaimRecord],
    ) -> tuple[list[ClaimRecord], list[ClaimRecord], list[ClaimRecord], list[str]]:
        grouped: dict[str, list[ClaimRecord]] = {}
        for claim in claim_records:
            grouped.setdefault(claim.slot, []).append(claim)

        core_slots = ["개발", "서비스/배급", "장르/성격", "상태", "이용 형태"]
        supporting_slots = ["배경", "특징", "플레이 특징"]
        coverage = summarize_slot_coverage(claim_records, slots=core_slots)

        strong_selected: list[ClaimRecord] = []
        weak_selected: list[ClaimRecord] = []
        for slot in core_slots:
            items = grouped.get(slot) or []
            if not items:
                continue
            best = max(items, key=self._entity_claim_sort_key)
            slot_coverage = coverage.get(slot)
            if not slot_coverage:
                continue
            if slot_coverage.status == CoverageStatus.STRONG:
                strong_selected.append(best)
                continue
            if best.source_role in TRUSTED_CLAIM_SOURCE_ROLES:
                weak_selected.append(best)

        supporting: list[ClaimRecord] = []
        for slot in supporting_slots:
            items = grouped.get(slot) or []
            if not items:
                continue
            best = max(items, key=self._entity_claim_sort_key)
            if slot in {"배경", "특징"}:
                if best.support_count < 2 and best.source_role not in TRUSTED_CLAIM_SOURCE_ROLES:
                    continue
            elif best.support_count < 2:
                continue
            if self._looks_like_narrative_entity_line(best.value):
                continue
            if self._looks_like_operational_entity_noise(best.value):
                continue
            if len(best.value) > 120:
                continue
            supporting.append(best)

        strong_selected.sort(key=lambda item: self._entity_fact_sort_key(item.slot))
        weak_selected.sort(key=lambda item: self._entity_fact_sort_key(item.slot))
        supporting.sort(key=lambda item: (self._entity_fact_sort_key(item.slot), -item.support_count))
        covered_slots = {claim.slot for claim in [*strong_selected, *weak_selected]}
        unresolved_slots = [
            slot
            for slot in core_slots
            if coverage.get(slot) and coverage[slot].status != CoverageStatus.STRONG and slot not in covered_slots
        ]
        return strong_selected[:5], weak_selected[:5], supporting[:2], unresolved_slots[:3]

    def _build_entity_claim_coverage_items(
        self,
        *,
        core_coverage: dict[str, Any],
        primary_claims: list[ClaimRecord],
        weak_claims: list[ClaimRecord],
    ) -> list[dict[str, Any]]:
        strong_slots = {claim.slot for claim in primary_claims}
        weak_slots = {claim.slot for claim in weak_claims}
        coverage_items: list[dict[str, Any]] = []

        for slot in CORE_ENTITY_SLOTS:
            slot_coverage = core_coverage.get(slot)
            primary_claim = getattr(slot_coverage, "primary_claim", None)
            if primary_claim is None:
                coverage_items.append(
                    {
                        "slot": slot,
                        "status": CoverageStatus.MISSING,
                        "status_label": "미확인",
                        "support_count": 0,
                        "candidate_count": 0,
                        "value": "",
                        "source_role": "",
                        "rendered_as": "not_rendered",
                    }
                )
                continue

            if slot in strong_slots:
                rendered_as = "fact_card"
            elif slot in weak_slots:
                rendered_as = "uncertain"
            else:
                rendered_as = "not_rendered"

            status = str(getattr(slot_coverage, "status", CoverageStatus.WEAK) or CoverageStatus.WEAK)
            coverage_items.append(
                {
                    "slot": slot,
                    "status": status,
                    "status_label": "교차 확인" if status == CoverageStatus.STRONG else "단일 출처",
                    "support_count": int(getattr(primary_claim, "support_count", 0) or 0),
                    "candidate_count": int(getattr(slot_coverage, "candidate_count", 0) or 0),
                    "value": str(getattr(primary_claim, "value", "") or ""),
                    "source_role": str(getattr(primary_claim, "source_role", "") or ""),
                    "rendered_as": rendered_as,
                }
            )

        return coverage_items

    def _annotate_claim_coverage_progress(
        self,
        *,
        previous_claim_coverage: list[dict[str, Any]] | None,
        current_claim_coverage: list[dict[str, Any]] | None,
        query: str,
    ) -> list[dict[str, Any]]:
        items = [dict(item) for item in current_claim_coverage or [] if isinstance(item, dict)]
        if not items:
            return []

        previous_map = {
            str(item.get("slot") or "").strip(): str(item.get("status") or "").strip()
            for item in previous_claim_coverage or []
            if isinstance(item, dict) and str(item.get("slot") or "").strip()
        }
        focus_slot = self._entity_slot_from_probe_text(query)

        annotated: list[dict[str, Any]] = []
        for item in items:
            slot = str(item.get("slot") or "").strip()
            current_status = str(item.get("status") or "").strip() or CoverageStatus.MISSING
            previous_status = previous_map.get(slot, CoverageStatus.MISSING)
            previous_rank = self._claim_coverage_status_rank(previous_status)
            current_rank = self._claim_coverage_status_rank(current_status)
            progress_state = ""
            progress_label = ""
            if current_rank > previous_rank:
                progress_state = "improved"
                progress_label = "보강됨"
            elif current_rank < previous_rank:
                progress_state = "regressed"
                progress_label = "약해짐"
            elif previous_map:
                progress_state = "unchanged"
                progress_label = "유지"

            updated = dict(item)
            updated["previous_status"] = previous_status
            updated["previous_status_label"] = self._claim_coverage_status_label(previous_status)
            updated["progress_state"] = progress_state
            updated["progress_label"] = progress_label
            updated["is_focus_slot"] = bool(focus_slot and slot == focus_slot)
            annotated.append(updated)
        return annotated

    def _claim_coverage_status_rank(self, status: str) -> int:
        normalized = str(status or "").strip()
        if normalized == CoverageStatus.STRONG:
            return 2
        if normalized == CoverageStatus.WEAK:
            return 1
        return 0

    def _claim_coverage_status_label(self, status: str) -> str:
        normalized = str(status or "").strip()
        if normalized == CoverageStatus.STRONG:
            return "교차 확인"
        if normalized == CoverageStatus.WEAK:
            return "단일 출처"
        return "미확인"

    def _looks_like_related_entity_query(self, previous_query: str | None, current_query: str | None) -> bool:
        previous = " ".join(str(previous_query or "").split()).strip().lower()
        current = " ".join(str(current_query or "").split()).strip().lower()
        if not previous or not current:
            return False
        return previous in current or current in previous

    def _should_treat_as_entity_reinvestigation(
        self,
        *,
        active_context: dict[str, Any] | None,
        query: str,
    ) -> bool:
        if not isinstance(active_context, dict) or active_context.get("kind") != "web_search":
            return False
        previous_query = self._extract_web_search_query_from_context(active_context)
        if not self._looks_like_related_entity_query(previous_query, query):
            return False
        slot = self._entity_slot_from_probe_text(query)
        return bool(slot)

    def _build_claim_coverage_progress_summary(
        self,
        *,
        previous_claim_coverage: list[dict[str, Any]] | None,
        current_claim_coverage: list[dict[str, Any]] | None,
        query: str,
    ) -> str | None:
        previous_map = {
            str(item.get("slot") or "").strip(): str(item.get("status") or "").strip()
            for item in previous_claim_coverage or []
            if isinstance(item, dict) and str(item.get("slot") or "").strip()
        }
        current_map = {
            str(item.get("slot") or "").strip(): str(item.get("status") or "").strip()
            for item in current_claim_coverage or []
            if isinstance(item, dict) and str(item.get("slot") or "").strip()
        }
        if not previous_map or not current_map:
            return None

        focus_slot = self._entity_slot_from_probe_text(query)
        improved_slots: list[tuple[str, str, str]] = []
        regressed_slots: list[tuple[str, str, str]] = []
        unresolved_slots: list[tuple[str, str]] = []
        for slot in CORE_ENTITY_SLOTS:
            current_status = current_map.get(slot, "")
            if not current_status:
                continue
            previous_status = previous_map.get(slot, CoverageStatus.MISSING)
            previous_rank = self._claim_coverage_status_rank(previous_status)
            current_rank = self._claim_coverage_status_rank(current_status)
            if current_rank > previous_rank:
                improved_slots.append(
                    (
                        slot,
                        self._claim_coverage_status_label(previous_status),
                        self._claim_coverage_status_label(current_status),
                    )
                )
            elif current_rank < previous_rank:
                regressed_slots.append(
                    (
                        slot,
                        self._claim_coverage_status_label(previous_status),
                        self._claim_coverage_status_label(current_status),
                    )
                )
            if current_status in {CoverageStatus.WEAK, CoverageStatus.MISSING}:
                unresolved_slots.append((slot, self._claim_coverage_status_label(current_status)))

        if focus_slot:
            focus_particle = self._select_korean_particle(focus_slot, "은는")
            for slot, previous_label, current_label in improved_slots:
                if slot == focus_slot:
                    return f"재조사 결과 {slot}{focus_particle} {previous_label}에서 {current_label}로 보강되었습니다."
            for slot, previous_label, current_label in regressed_slots:
                if slot == focus_slot:
                    return f"재조사 결과 {slot}{focus_particle} {previous_label}에서 {current_label}로 약해졌습니다."
            for slot, current_label in unresolved_slots:
                if slot == focus_slot:
                    return f"재조사했지만 {slot}{focus_particle} 아직 {current_label} 상태입니다."

        if improved_slots:
            improved_summary = ", ".join(
                f"{slot} {before}->{after}" for slot, before, after in improved_slots[:3]
            )
            if unresolved_slots:
                unresolved_summary = ", ".join(
                    f"{slot} {label}" for slot, label in unresolved_slots[:2]
                )
                return f"재조사 결과 {improved_summary}로 보강되었습니다. 아직 {unresolved_summary} 상태의 슬롯이 남아 있습니다."
            return f"재조사 결과 {improved_summary}로 보강되었습니다."

        if unresolved_slots:
            unresolved_summary = ", ".join(
                f"{slot} {label}" for slot, label in unresolved_slots[:3]
            )
            return f"재조사했지만 아직 {unresolved_summary} 상태입니다."
        return None

    def _build_entity_claim_source_lines(
        self,
        *,
        query: str,
        selected_sources: list[dict[str, Any]],
        primary_claims: list[ClaimRecord],
        weak_claims: list[ClaimRecord],
        supplemental_claims: list[ClaimRecord],
    ) -> list[str]:
        support_refs: list[tuple[str, str, str]] = []
        seen_support_refs: set[tuple[str, str, str]] = set()
        for claim in [*primary_claims, *weak_claims, *supplemental_claims]:
            refs = claim.supporting_sources or ((claim.source_url, claim.source_title, claim.source_role),)
            for url, title, role in refs:
                compact_url = str(url or "").strip()
                compact_title = str(title or "(출처 없음)").strip()
                compact_role = str(role or "").strip()
                ref = (compact_url, compact_title, compact_role)
                if not compact_url or ref in seen_support_refs:
                    continue
                seen_support_refs.add(ref)
                support_refs.append(ref)

        lines: list[str] = []
        seen_urls: set[str] = set()
        role_priority = {
            SourceRole.WIKI: 4,
            SourceRole.OFFICIAL: 3,
            SourceRole.DESCRIPTIVE: 2,
            SourceRole.NEWS: 1,
            SourceRole.AUXILIARY: 1,
            SourceRole.PORTAL: 0,
            SourceRole.BLOG: 0,
        }
        support_refs.sort(key=lambda item: (role_priority.get(item[2], 0), len(item[1])), reverse=True)
        for url, title, role_label in support_refs:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            lines.append(f"- {title} [{role_label}]")
            lines.append(f"  링크: {url}")
            if len(lines) >= 6:
                break

        if lines:
            return lines

        fallback_lines: list[str] = []
        for source in selected_sources[:3]:
            title = str(source.get("title") or source.get("result_title") or "(출처 없음)").strip()
            url = str(source.get("url") or "").strip()
            role_label = self._entity_source_role_label(query=query, source=source)
            fallback_lines.append(f"- {title} [{role_label}]")
            if url:
                fallback_lines.append(f"  링크: {url}")
        return fallback_lines

    def _compose_entity_intro_line(self, *, query: str, detail_lines: list[str], fallback_intro: str) -> str:
        facts: dict[str, str] = {}
        for detail in detail_lines:
            parsed = self._split_entity_fact_bullet(detail)
            if not parsed:
                continue
            label, value = parsed
            facts.setdefault(label, value)

        developer = facts.get("개발")
        service = facts.get("서비스/배급")
        genre = facts.get("장르/성격")
        status = facts.get("상태")
        access = facts.get("이용 형태")
        background = facts.get("배경")
        feature = facts.get("특징") or facts.get("플레이 특징")
        subject_particle = self._select_korean_particle(query, "은는")

        lead: str | None = None
        if developer and status and genre:
            developer_particle = self._select_korean_particle(developer, "이가")
            lead = f"{query}{subject_particle} {developer}{developer_particle} {status}인 {genre}입니다."
        elif service and genre:
            service_particle = self._select_korean_particle(service, "이가")
            lead = f"{query}{subject_particle} {service}{service_particle} 서비스하거나 배급하는 {genre}입니다."
        elif developer and genre:
            developer_particle = self._select_korean_particle(developer, "이가")
            lead = f"{query}{subject_particle} {developer}{developer_particle} 개발한 {genre}입니다."
        elif service and status:
            service_particle = self._select_korean_particle(service, "이가")
            lead = f"{query}{subject_particle} {service}{service_particle} 서비스하거나 배급하며 현재 {status} 상태인 콘텐츠입니다."
        elif genre:
            lead = f"{query}{subject_particle} {genre}입니다."

        if not lead:
            return fallback_intro

        supplement: str | None = None
        if access:
            supplement = f"이용 형태는 {access}입니다."
        elif background:
            compact_background = background.rstrip(".")
            if len(compact_background) > 84:
                compact_background = self._summarize_hint(compact_background, max_chars=84).rstrip(".")
            if "배경으로" in compact_background:
                supplement = f"{compact_background}."
            else:
                supplement = f"배경은 {compact_background}입니다."
        elif feature:
            compact_feature = feature.rstrip(".")
            if len(compact_feature) > 84:
                compact_feature = self._summarize_hint(compact_feature, max_chars=84).rstrip(".")
            supplement = f"대표 특징은 {compact_feature}입니다."

        if supplement:
            return f"{lead} {supplement}"
        return lead

    def _build_entity_web_summary(
        self,
        *,
        query: str,
        selected_sources: list[dict[str, Any]],
        ranked_sources: list[dict[str, Any]] | None = None,
        pages: list[dict[str, Any]] | None = None,
    ) -> str:
        lines = [f"웹 검색 요약: {query}", ""]
        candidate_lines: list[tuple[int, int, str, str, str]] = []
        seen_lines: set[str] = set()
        source_counter = 0
        candidate_sources = list(selected_sources or ranked_sources or [])
        for source in candidate_sources[:5]:
            source_counter += 1
            title = str(source.get("title") or source.get("result_title") or "").strip()
            url = str(source.get("url") or "").strip()
            raw_candidates: list[str] = []
            summary_text = str(source.get("summary_text") or "").strip()
            snippet_text = str(source.get("snippet") or "").strip()
            if snippet_text and (
                not summary_text
                or self._looks_like_noisy_web_segment(summary_text)
                or self._looks_like_contact_or_legal_web_segment(summary_text)
                or self._looks_like_operational_entity_noise(summary_text)
            ):
                raw_candidates.extend(self._split_web_page_segments(snippet_text))
            if summary_text:
                raw_candidates.extend(self._split_web_page_segments(summary_text))
            context_text = str(source.get("context_text") or "").strip()
            if context_text:
                raw_candidates.extend(self._split_web_page_segments(context_text))
            if not raw_candidates and title:
                raw_candidates.append(title)
            source_candidate_lines: list[tuple[int, str]] = []
            local_index = 0
            for candidate in raw_candidates:
                local_index += 1
                compact = " ".join(candidate.split()).strip()
                if not compact:
                    continue
                score = self._score_entity_fact_line(line=compact, query=query, source_title=title)
                source_candidate_lines.append((score, compact))
                key = compact.lower()
                if key in seen_lines:
                    continue
                seen_lines.add(key)
                candidate_lines.append((score, -source_counter, -local_index, compact, url))
        candidate_lines.sort(reverse=True)
        chosen_lines_with_scores = [(score, line) for score, _, _, line, _ in candidate_lines if score > 0]
        chosen_lines = [line for _, line in chosen_lines_with_scores[:5]]
        if not chosen_lines:
            fallback_line = ""
            for source in selected_sources:
                preferred_segments = self._preferred_entity_source_segments(source)
                if preferred_segments:
                    fallback_line = preferred_segments[0]
                    break
            if not fallback_line and selected_sources:
                fallback_line = str(selected_sources[0].get("snippet") or selected_sources[0].get("summary_text") or "").strip()
            chosen_lines = [fallback_line] if fallback_line else ["설명할 만한 검색 근거를 충분히 모으지 못했습니다."]

        intro_line = chosen_lines[0]
        claim_records = self._build_entity_claim_records(
            query=query,
            selected_sources=selected_sources,
        )
        core_coverage = summarize_slot_coverage(claim_records, slots=CORE_ENTITY_SLOTS)
        primary_claims, weak_claims, supplemental_claims, unresolved_slots = self._select_entity_fact_card_claims(
            query=query,
            claim_records=claim_records,
        )
        detail_lines = [f"{claim.slot}: {claim.value}" for claim in primary_claims] or [
            f"{claim.slot}: {claim.value}" for claim in weak_claims
        ]
        intro_line = self._compose_entity_intro_line(
            query=query,
            detail_lines=detail_lines,
            fallback_intro=intro_line,
        )
        if self._looks_like_noisy_web_segment(intro_line) or self._looks_like_operational_entity_noise(intro_line):
            for source in selected_sources:
                preferred_segments = self._preferred_entity_source_segments(source)
                if not preferred_segments:
                    continue
                intro_line = preferred_segments[0]
                break
        lines.append("한 줄 정의:")
        lines.append(f"- {intro_line}")
        if primary_claims:
            lines.append("")
            lines.append("사실 카드:")
            for claim in primary_claims:
                support_suffix = f" (교차 확인 {claim.support_count}건)" if claim.support_count >= 2 else ""
                lines.append(f"- {claim.slot}: {claim.value}{support_suffix}")
        if weak_claims:
            lines.append("")
            lines.append("단일 출처 확인 정보:")
            for claim in weak_claims:
                role_label = core_coverage.get(claim.slot).primary_claim.source_role if core_coverage.get(claim.slot) and core_coverage.get(claim.slot).primary_claim else claim.source_role
                lines.append(f"- {claim.slot}: {claim.value} (단일 출처, {role_label})")
        if supplemental_claims:
            lines.append("")
            lines.append("보조 사실:")
            for claim in supplemental_claims:
                lines.append(f"- {claim.slot}: {claim.value} (교차 확인 {claim.support_count}건)")
        if unresolved_slots:
            lines.append("")
            lines.append("아직 확인되지 않은 항목:")
            for slot in unresolved_slots:
                lines.append(f"- {slot}: 교차 확인 가능한 근거를 찾지 못했습니다.")
        lines.append("")
        lines.append("근거 출처:")
        lines.extend(
            self._build_entity_claim_source_lines(
                query=query,
                selected_sources=selected_sources,
                primary_claims=primary_claims,
                weak_claims=weak_claims,
                supplemental_claims=supplemental_claims,
            )
        )
        failed_pages = [page for page in pages or [] if str(page.get("fetch_status") or "") != "ok"]
        if failed_pages and not [page for page in pages or [] if str(page.get("fetch_status") or "") == "ok"]:
            lines.append("")
            lines.append("참고: 원문을 직접 읽지 못한 링크는 검색 결과 설명을 우선 사용했습니다.")
        return "\n".join(lines)

    def _score_ranked_web_source(
        self,
        *,
        query: str,
        intent_kind: str | None,
        answer_mode: str | None,
        freshness_risk: str | None,
        query_terms: list[str],
        title: str,
        snippet: str,
        url: str,
        summary_text: str,
        prefer_page: bool,
        fetch_ok: bool,
    ) -> int:
        title_lowered = title.lower()
        snippet_lowered = snippet.lower()
        summary_lowered = summary_text.lower()
        url_lowered = url.lower()
        query_profile = self._infer_web_query_profile(
            query=query,
            intent_kind=intent_kind,
            answer_mode=answer_mode,
            freshness_risk=freshness_risk,
        )
        source_policy = self._build_source_policy_decision(
            query=query,
            url=url,
            title=title,
            summary_text=summary_text or snippet or title,
        )
        resolved_answer_mode = answer_mode or (
            AnswerMode.ENTITY_CARD if query_profile == "entity" else AnswerMode.LATEST_UPDATE if query_profile == "live" else AnswerMode.GENERAL
        )
        resolved_freshness_risk = freshness_risk or (FreshnessRisk.HIGH if query_profile == "live" else FreshnessRisk.LOW)

        score = 0
        for term in query_terms:
            if term in title_lowered:
                score += 7
            if term in summary_lowered:
                score += 6
            if term in snippet_lowered and term not in summary_lowered:
                score += 3
            if term in url_lowered:
                score += 2

        if summary_text and not self._looks_like_noisy_web_segment(summary_text):
            score += 3
        if self._looks_like_noisy_web_segment(summary_text):
            score -= 10

        if 20 <= len(summary_text) <= 240:
            score += 2
        elif len(summary_text) < 12:
            score -= 2

        if prefer_page:
            score += 4
        elif fetch_ok:
            score -= 1

        if any(marker in summary_text for marker in ["이다", "입니다", "그룹", "밴드", "가수", "배우", "기업", "브랜드", "서비스", "발표", "출시", "예정", "공개", "날씨", "기온"]):
            score += 2

        score += score_source_for_mode(
            source_policy,
            answer_mode=resolved_answer_mode,
            freshness_risk=resolved_freshness_risk,
        )

        if query_profile == "entity":
            if self._looks_like_official_product_domain(url):
                if self._looks_like_operational_entity_noise(summary_text) or self._looks_like_noisy_web_segment(summary_text):
                    score -= 8
            if any(
                marker in f"{title_lowered} {summary_lowered}"
                for marker in ["업데이트", "패치", "이벤트", "쿠폰", "사전예약", "게시판", "인벤", "공식 카페"]
            ):
                score -= 5
        elif query_profile == "live":
            if "날씨" in query and any(marker in summary_text for marker in ["기온", "강수", "미세먼지", "바람"]):
                score += 4

        video_intent = self._query_prefers_video_platform_results(query)
        if self._looks_like_js_heavy_web_url(url) and not video_intent:
            score -= 8
        if not video_intent and any(marker in f"{title_lowered} {summary_lowered}" for marker in ["youtube", "유튜브", "채널", "shorts", "쇼츠"]):
            score -= 4
        return score

    def _should_prefer_web_page_text(
        self,
        *,
        query: str,
        intent_kind: str | None,
        answer_mode: str | None,
        freshness_risk: str | None,
        url: str,
        title: str,
        snippet: str,
        excerpt: str,
        focused_text: str,
    ) -> bool:
        normalized_excerpt = " ".join(str(excerpt or "").split()).strip()
        normalized_text = str(focused_text or "").strip()
        if not normalized_text:
            return False
        if self._looks_like_js_heavy_web_url(url) and not self._query_prefers_video_platform_results(query):
            return False
        if normalized_excerpt and self._looks_like_noisy_web_segment(normalized_excerpt):
            return False

        query_terms = self._extract_web_query_terms(query)
        page_score = self._score_ranked_web_source(
            query=query,
            intent_kind=intent_kind,
            answer_mode=answer_mode,
            freshness_risk=freshness_risk,
            query_terms=query_terms,
            title=title,
            snippet=snippet,
            url=url,
            summary_text=normalized_excerpt or self._summarize_hint(normalized_text, max_chars=280),
            prefer_page=True,
            fetch_ok=True,
        )
        snippet_score = self._score_ranked_web_source(
            query=query,
            intent_kind=intent_kind,
            answer_mode=answer_mode,
            freshness_risk=freshness_risk,
            query_terms=query_terms,
            title=title,
            snippet=snippet,
            url=url,
            summary_text=snippet.strip() or title,
            prefer_page=False,
            fetch_ok=True,
        )
        return page_score >= max(snippet_score, 1)

    def _rank_web_search_sources(
        self,
        *,
        query: str,
        intent_kind: str | None = None,
        answer_mode: str | None = None,
        freshness_risk: str | None = None,
        results: list[dict[str, str]],
        pages: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        pages_by_url = {
            str(page.get("url") or "").strip(): page
            for page in pages or []
            if isinstance(page, dict) and str(page.get("url") or "").strip()
        }
        query_terms = self._extract_web_query_terms(query)
        ranked: list[dict[str, Any]] = []

        for index, result in enumerate(results, start=1):
            url = str(result.get("url") or "").strip()
            result_title = str(result.get("title") or f"결과 {index}").strip()
            snippet = str(result.get("snippet") or "").strip()
            page = pages_by_url.get(url)
            fetch_ok = bool(
                page
                and str(page.get("fetch_status") or "") == "ok"
                and str(page.get("text") or "").strip()
            )
            page_title = str((page or {}).get("title") or (page or {}).get("source_title") or result_title).strip()
            page_excerpt = str((page or {}).get("excerpt") or "").strip()
            focused_text = str((page or {}).get("focused_text") or "").strip()

            prefer_page = fetch_ok and self._should_prefer_web_page_text(
                query=query,
                intent_kind=intent_kind,
                answer_mode=answer_mode,
                freshness_risk=freshness_risk,
                url=url,
                title=page_title or result_title,
                snippet=snippet,
                excerpt=page_excerpt,
                focused_text=focused_text,
            )
            summary_text = (
                page_excerpt
                if prefer_page and page_excerpt
                else snippet or page_excerpt or result_title
            ).strip()
            context_text = (
                focused_text
                if prefer_page and focused_text
                else f"{result_title}\n{snippet}".strip()
            ).strip() or summary_text
            display_title = (page_title if prefer_page else result_title or page_title).strip() or url or f"결과 {index}"
            score = self._score_ranked_web_source(
                query=query,
                intent_kind=intent_kind,
                answer_mode=answer_mode,
                freshness_risk=freshness_risk,
                query_terms=query_terms,
                title=display_title,
                snippet=snippet,
                url=url,
                summary_text=summary_text,
                prefer_page=prefer_page,
                fetch_ok=fetch_ok,
            )
            ranked.append(
                {
                    "index": index,
                    "url": url,
                    "title": display_title,
                    "result_title": result_title,
                    "snippet": snippet,
                    "matched_query": str(result.get("matched_query") or "").strip(),
                    "summary_text": summary_text,
                    "context_text": context_text,
                    "page_preferred": prefer_page,
                    "fetch_ok": fetch_ok,
                    "score": score,
                }
            )

        ranked.sort(key=lambda item: (-int(item.get("score") or 0), int(item.get("index") or 0)))
        return ranked

    def _select_ranked_web_sources(
        self,
        *,
        query: str,
        intent_kind: str | None = None,
        answer_mode: str | None = None,
        freshness_risk: str | None = None,
        ranked_sources: list[dict[str, Any]],
        max_items: int,
    ) -> list[dict[str, Any]]:
        if not ranked_sources:
            return []
        query_profile = self._infer_web_query_profile(
            query=query,
            intent_kind=intent_kind,
            answer_mode=answer_mode,
            freshness_risk=freshness_risk,
        )
        top_score = int(ranked_sources[0].get("score") or 0)
        if query_profile == "entity":
            threshold = max(4, top_score - 7)
        elif query_profile == "live":
            threshold = max(2, top_score - 12)
        else:
            threshold = max(1, top_score - 8)

        selected = [
            source
            for source in ranked_sources
            if int(source.get("score") or 0) >= threshold
        ]
        if query_profile == "entity" and selected:
            filtered = [
                source
                for source in selected
                if not (
                    self._classify_web_source_kind(str(source.get("url") or "").strip()) in {"video", "portal"}
                    and int(source.get("score") or 0) < top_score
                )
            ]
            if filtered:
                selected = filtered
        if query_profile != "entity":
            return (selected or ranked_sources)[:max_items]

        def _entity_trust_score(source: dict[str, Any]) -> int:
            url = str(source.get("url") or "").strip()
            title = str(source.get("title") or source.get("result_title") or "").strip()
            summary_text = str(source.get("summary_text") or source.get("snippet") or title).strip()
            source_policy = self._build_source_policy_decision(
                query=query,
                url=url,
                title=title,
                summary_text=summary_text,
            )
            return score_source_for_mode(
                source_policy,
                answer_mode=AnswerMode.ENTITY_CARD,
                freshness_risk=freshness_risk or FreshnessRisk.LOW,
            )

        candidates = list(selected)
        for source in ranked_sources:
            if source in candidates:
                continue
            matched_query = str(source.get("matched_query") or "").strip()
            if self._entity_slot_from_search_query(query=query, matched_query=matched_query):
                candidates.append(source)
        for source in ranked_sources:
            if source in candidates:
                continue
            candidates.append(source)
        if not candidates:
            return []

        fact_bullets_by_index = {
            index: self._extract_entity_source_fact_bullets(query=query, source=source)
            for index, source in enumerate(candidates)
        }

        probe_bonus_by_index = {
            index: self._entity_source_probe_bonus(
                query=query,
                source=source,
                fact_bullets=fact_bullets_by_index.get(index) or [],
            )
            for index, source in enumerate(candidates)
        }
        probe_bonus_by_source_id = {
            id(source): probe_bonus_by_index.get(index, 0)
            for index, source in enumerate(candidates)
        }

        trust_score_by_index = {
            index: _entity_trust_score(source)
            for index, source in enumerate(candidates)
        }

        decorated: list[tuple[int, int, int, int, int, dict[str, Any]]] = []
        for index, source in enumerate(candidates):
            trust_score = trust_score_by_index.get(index, 0)
            agreement_score = self._entity_source_fact_agreement_score(
                source_index=index,
                sources=candidates,
                fact_bullets_by_index=fact_bullets_by_index,
                trust_score_by_index=trust_score_by_index,
            )
            probe_bonus = probe_bonus_by_index.get(index, 0)
            rank_score = int(source.get("score") or 0)
            decorated.append(
                (
                    trust_score + agreement_score + probe_bonus,
                    probe_bonus,
                    agreement_score,
                    rank_score,
                    -index,
                    source,
                )
            )
        decorated.sort(key=lambda item: (item[0], item[1], item[2], item[3], item[4]), reverse=True)

        chosen: list[dict[str, Any]] = []
        seen_domains: set[str] = set()
        source_kind_counts: dict[str, int] = {}
        evicted_source_ids: set[int] = set()

        def _push(source: dict[str, Any]) -> bool:
            hostname = self._source_hostname(str(source.get("url") or "").strip())
            source_url = str(source.get("url") or "").strip()
            source_policy = self._build_source_policy_decision(
                query=query,
                url=source_url,
                title=str(source.get("title") or source.get("result_title") or "").strip(),
                summary_text=str(source.get("summary_text") or source.get("snippet") or "").strip(),
            )
            source_title = str(source.get("title") or source.get("result_title") or "").strip()
            source_summary = str(source.get("summary_text") or source.get("snippet") or source_title).strip()
            trust_score = _entity_trust_score(source)
            probe_bonus = probe_bonus_by_source_id.get(id(source), 0)
            if hostname and hostname in seen_domains:
                if probe_bonus <= 0:
                    domain_has_probe = any(
                        self._source_hostname(str(item.get("url") or "").strip()) == hostname
                        and probe_bonus_by_source_id.get(id(item), 0) > 0
                        for item in chosen
                    )
                    if domain_has_probe:
                        evicted_source_ids.add(id(source))
                    return False
                existing = [item for item in chosen if self._source_hostname(str(item.get("url") or "").strip()) == hostname]
                if existing and all(probe_bonus_by_source_id.get(id(item), 0) <= 0 for item in existing):
                    for item in existing:
                        evicted_source_ids.add(id(item))
                    chosen[:] = [item for item in chosen if item not in existing]
                    for item in existing:
                        item_hostname = self._source_hostname(str(item.get("url") or "").strip())
                        if item_hostname:
                            seen_domains.discard(item_hostname)
                        item_policy = self._build_source_policy_decision(
                            query=query,
                            url=str(item.get("url") or "").strip(),
                            title=str(item.get("title") or item.get("result_title") or "").strip(),
                            summary_text=str(item.get("summary_text") or item.get("snippet") or "").strip(),
                        )
                        source_kind_counts[item_policy.source_type] = max(0, source_kind_counts.get(item_policy.source_type, 1) - 1)
                else:
                    new_slot = self._entity_slot_from_search_query(
                        query=query,
                        matched_query=str(source.get("matched_query") or "").strip(),
                    )
                    if new_slot:
                        existing_slots = {
                            self._entity_slot_from_search_query(
                                query=query,
                                matched_query=str(item.get("matched_query") or "").strip(),
                            )
                            for item in existing
                            if probe_bonus_by_source_id.get(id(item), 0) > 0
                        }
                        if new_slot not in existing_slots:
                            pass
                        else:
                            return False
                    else:
                        return False
            if any(_entity_trust_score(item) >= 7 for item in chosen) and trust_score < 4 and probe_bonus <= 0:
                return False
            if source_policy.source_type == "community" and source_kind_counts.get(source_policy.source_type, 0) >= 1:
                return False
            if source_kind_counts.get(source_policy.source_type, 0) >= 2:
                return False
            if (
                self._looks_like_event_or_campaign_source(title=source_title, summary_text=source_summary)
                and any(_entity_trust_score(item) >= 7 for item in chosen)
                and trust_score < 7
                and probe_bonus <= 0
            ):
                return False
            if (
                source_policy.source_type == "news"
                and any(_entity_trust_score(item) >= 7 for item in chosen)
                and trust_score < 7
                and probe_bonus <= 0
            ):
                return False
            chosen.append(source)
            if hostname:
                seen_domains.add(hostname)
            source_kind_counts[source_policy.source_type] = source_kind_counts.get(source_policy.source_type, 0) + 1
            return True

        for trust_score, _, _, _, _, source in decorated:
            if len(chosen) >= max_items:
                break
            if trust_score >= 4:
                _push(source)

        for _, _, _, _, _, source in decorated:
            if len(chosen) >= max_items:
                break
            _push(source)

        if len(chosen) < max_items:
            for source in candidates:
                if len(chosen) >= max_items:
                    break
                if source in chosen or id(source) in evicted_source_ids:
                    continue
                trust_score = _entity_trust_score(source)
                source_url = str(source.get("url") or "").strip()
                source_policy = self._build_source_policy_decision(
                    query=query,
                    url=source_url,
                    title=str(source.get("title") or source.get("result_title") or "").strip(),
                    summary_text=str(source.get("summary_text") or source.get("snippet") or "").strip(),
                )
                source_title = str(source.get("title") or source.get("result_title") or "").strip()
                source_summary = str(source.get("summary_text") or source.get("snippet") or source_title).strip()
                probe_bonus = probe_bonus_by_source_id.get(id(source), 0)
                if (
                    any(_entity_trust_score(item) >= 7 for item in chosen)
                    and trust_score < 4
                    and probe_bonus <= 0
                ):
                    continue
                if (
                    any(_entity_trust_score(item) >= 7 for item in chosen)
                    and (
                        source_policy.source_type == "news"
                        or self._looks_like_event_or_campaign_source(title=source_title, summary_text=source_summary)
                    )
                    and probe_bonus <= 0
                ):
                    continue
                chosen.append(source)

        return chosen[:max_items]

    def _fetch_web_page_records(
        self,
        *,
        query: str,
        search_tool: Any,
        results: list[dict[str, str]],
        intent_kind: str | None = None,
        answer_mode: str | None = None,
        freshness_risk: str | None = None,
        phase_event_callback: Callable[[dict[str, Any]], None] | None = None,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        fetch_page = getattr(search_tool, "fetch_page", None)
        if not callable(fetch_page):
            return []

        fetched_pages: list[dict[str, Any]] = []
        query_terms = self._extract_web_query_terms(query)
        fetch_candidates = [item for item in results if str(item.get("url") or "").strip()]
        fetch_candidates.sort(
            key=lambda item: (
                self._looks_like_js_heavy_web_url(str(item.get("url") or "").strip()),
                -self._score_ranked_web_source(
                    query=query,
                    intent_kind=intent_kind,
                    answer_mode=answer_mode,
                    freshness_risk=freshness_risk,
                    query_terms=query_terms,
                    title=str(item.get("title") or "").strip(),
                    snippet=str(item.get("snippet") or "").strip(),
                    url=str(item.get("url") or "").strip(),
                    summary_text=str(item.get("snippet") or item.get("title") or "").strip(),
                    prefer_page=False,
                    fetch_ok=False,
                ),
            )
        )
        fetch_candidates = fetch_candidates[:max_pages]
        if not fetch_candidates:
            return []

        self._emit_phase(
            phase_event_callback,
            phase="web_pages_fetch_started",
            title="검색 결과 원문 읽는 중",
            detail=f"상위 검색 결과 {len(fetch_candidates)}건의 원문 페이지를 읽어 근거를 보강하는 중입니다.",
            note="읽기 전용으로만 가져오고, 읽은 내용은 로컬 검색 기록에 함께 저장합니다.",
        )

        for index, result in enumerate(fetch_candidates, start=1):
            url = str(result.get("url") or "").strip()
            source_title = str(result.get("title") or f"검색 결과 {index}").strip()
            snippet = str(result.get("snippet") or "").strip()
            self._emit_phase(
                phase_event_callback,
                phase="web_page_fetching",
                title="원문 페이지 확인 중",
                detail=f"{index}번째 링크 '{source_title}' 원문을 읽는 중입니다.",
                note="페이지를 읽지 못하면 기존 검색 snippet만 사용합니다.",
            )
            try:
                page = fetch_page(url=url)
                page_text = str(getattr(page, "text", "") or "").strip()
                if not page_text:
                    raise ValueError("본문이 비어 있습니다.")
                page_title = str(getattr(page, "title", "") or source_title).strip() or source_title
                excerpt, focused_text = self._build_web_page_focus(
                    query=query,
                    title=page_title,
                    snippet=snippet,
                    text=page_text,
                )
                fetched_pages.append(
                    {
                        "url": url,
                        "source_title": source_title,
                        "title": page_title,
                        "content_type": str(getattr(page, "content_type", "") or "").strip(),
                        "text": page_text,
                        "excerpt": excerpt,
                        "focused_text": focused_text,
                        "char_count": len(page_text),
                        "fetch_status": "ok",
                    }
                )
            except Exception as exc:
                fetched_pages.append(
                    {
                        "url": url,
                        "source_title": source_title,
                        "title": source_title,
                        "content_type": "",
                        "text": "",
                        "excerpt": snippet,
                        "char_count": 0,
                        "fetch_status": "error",
                        "error": str(exc),
                    }
                )
        return fetched_pages

    def _build_web_search_evidence(
        self,
        results: list[dict[str, str]],
        *,
        pages: list[dict[str, Any]] | None = None,
        ranked_sources: list[dict[str, Any]] | None = None,
        query: str | None = None,
        intent_kind: str | None = None,
        answer_mode: str | None = None,
        freshness_risk: str | None = None,
        limit: int = 3,
    ) -> list[dict[str, str]]:
        if ranked_sources:
            evidence: list[dict[str, str]] = []
            selected_sources = self._select_ranked_web_sources(
                query=query or "",
                intent_kind=intent_kind,
                answer_mode=answer_mode,
                freshness_risk=freshness_risk,
                ranked_sources=ranked_sources,
                max_items=limit,
            )
            for source in selected_sources:
                url = str(source.get("url") or "").strip()
                title = str(source.get("title") or source.get("result_title") or url or "(출처 없음)").strip()
                source_role = self._web_source_role_label(query=query or title, source=source)
                if bool(source.get("page_preferred")) and str(source.get("context_text") or "").strip():
                    for item in self._extract_text_evidence_items(
                        source_path=url,
                        text=str(source.get("context_text") or ""),
                        max_items=2,
                    ):
                        item["label"] = "웹 원문 근거"
                        item["source_name"] = title
                        item["source_role"] = source_role
                        evidence.append(item)
                else:
                    evidence.append(
                        {
                            "label": "웹 검색 결과",
                            "source_name": title,
                            "source_path": url,
                            "snippet": str(source.get("summary_text") or source.get("snippet") or title).strip(),
                            "source_role": source_role,
                        }
                    )
            return self._dedupe_evidence_items(evidence, max_items=limit)

        page_evidence: list[dict[str, str]] = []
        for page in pages or []:
            if str(page.get("fetch_status") or "") != "ok":
                continue
            page_text = str(page.get("focused_text") or page.get("text") or "").strip()
            if not page_text:
                continue
            url = str(page.get("url") or "").strip()
            title = str(page.get("title") or page.get("source_title") or url or "(출처 없음)").strip()
            for item in self._extract_text_evidence_items(source_path=url, text=page_text, max_items=2):
                item["label"] = "웹 원문 근거"
                item["source_name"] = title
                item["source_role"] = self._web_source_role_label(
                    query=query or title,
                    source={
                        "url": url,
                        "title": title,
                        "summary_text": str(page.get("excerpt") or page_text).strip(),
                    },
                )
                page_evidence.append(item)
        if page_evidence:
            return self._dedupe_evidence_items(page_evidence, max_items=limit)

        evidence: list[dict[str, str]] = []
        for item in results[:limit]:
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            evidence.append(
                {
                    "label": "웹 검색 결과",
                    "source_name": title,
                    "source_path": str(item.get("url") or "").strip(),
                    "snippet": str(item.get("snippet") or title).strip(),
                    "source_role": self._web_source_role_label(query=query or title, source=item),
                }
            )
        return evidence

    def _build_web_search_origin(
        self,
        *,
        answer_mode: str | None = None,
        selected_sources: list[dict[str, Any]] | None = None,
        query: str | None = None,
        claim_coverage: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        mode_label = "웹 검색 결과"
        if answer_mode == AnswerMode.ENTITY_CARD:
            mode_label = "외부 웹 설명 카드"
        elif answer_mode == AnswerMode.LATEST_UPDATE:
            mode_label = "외부 웹 최신 확인"
        role_sources = list(selected_sources or [])
        if answer_mode == AnswerMode.ENTITY_CARD and role_sources:
            role_sources = [
                s for s in role_sources
                if self._extract_entity_source_fact_bullets(query=query or "", source=s)
            ]
            if not role_sources:
                role_sources = list(selected_sources or [])
        elif answer_mode == AnswerMode.LATEST_UPDATE and role_sources:
            role_sources = [
                s for s in role_sources
                if not self._looks_like_noisy_web_segment(
                    str(s.get("summary_text") or s.get("snippet") or "").strip()
                )
            ]
            if not role_sources:
                role_sources = list(selected_sources or [])
        source_roles = self._summarize_web_source_roles(query=query or "", sources=role_sources)
        verification_label = self._build_web_verification_label(
            query=query or "",
            sources=role_sources,
            answer_mode=answer_mode,
            claim_coverage=claim_coverage,
        )
        return {
            "provider": "web",
            "badge": "WEB",
            "label": mode_label,
            "model": None,
            "kind": "assistant",
            "answer_mode": str(answer_mode or AnswerMode.GENERAL),
            "source_roles": source_roles,
            "verification_label": verification_label,
        }

    def _summarize_web_source_roles(self, *, query: str, sources: list[dict[str, Any]]) -> list[str]:
        seen: list[str] = []
        for source in sources:
            role = self._web_source_role_label(query=query or str(source.get("title") or ""), source=source)
            if role and role not in seen:
                seen.append(role)
        return seen[:3]

    def _build_web_verification_label(
        self,
        *,
        query: str,
        sources: list[dict[str, Any]],
        answer_mode: str | None,
        claim_coverage: list[dict[str, Any]] | None = None,
    ) -> str:
        if not sources:
            return ""

        type_counts: dict[str, int] = {}
        for source in sources:
            url = str(source.get("url") or "").strip()
            title = str(source.get("title") or source.get("result_title") or "").strip()
            summary_text = str(source.get("summary_text") or source.get("snippet") or title).strip()
            policy = self._build_source_policy_decision(
                query=query or title,
                url=url,
                title=title,
                summary_text=summary_text,
            )
            source_type = str(policy.source_type or SourceType.GENERAL)
            type_counts[source_type] = type_counts.get(source_type, 0) + 1

        official_count = type_counts.get(SourceType.OFFICIAL, 0)
        news_count = type_counts.get(SourceType.NEWS, 0)
        wiki_count = type_counts.get(SourceType.WIKI, 0)
        database_count = type_counts.get(SourceType.DATABASE, 0)
        strong_reference_count = official_count + wiki_count + database_count
        total = len(sources)

        if answer_mode == AnswerMode.LATEST_UPDATE:
            if official_count >= 1 and news_count >= 1:
                return "공식+기사 교차 확인"
            if official_count >= 1 and total >= 2:
                return "공식 확인 중심"
            if news_count >= 2:
                return "기사 교차 확인"
            if official_count >= 1:
                return "공식 단일 출처"
            if total >= 2:
                return "다중 출처 참고"
            return "단일 출처 참고"

        if answer_mode == AnswerMode.ENTITY_CARD:
            has_strong_slot = any(
                str(item.get("status") or "").strip() == CoverageStatus.STRONG
                for item in (claim_coverage or [])
                if isinstance(item, dict)
            )
            if strong_reference_count >= 2 and has_strong_slot:
                return "설명형 다중 출처 합의"
            if official_count >= 1:
                return "공식 단일 출처"
            if wiki_count >= 1 or database_count >= 1:
                return "설명형 단일 출처"
            if total >= 2:
                return "다중 출처 참고"
            return "단일 출처 참고"

        return "다중 출처 참고" if total >= 2 else "단일 출처 참고"

    def _build_latest_update_web_summary(
        self,
        *,
        query: str,
        selected_sources: list[dict[str, Any]],
        pages: list[dict[str, Any]] | None = None,
    ) -> str:
        verification_label = self._build_web_verification_label(
            query=query,
            sources=selected_sources,
            answer_mode=AnswerMode.LATEST_UPDATE,
        )
        non_noisy_sources = [
            s for s in selected_sources
            if not self._looks_like_noisy_web_segment(
                str(s.get("summary_text") or s.get("snippet") or "").strip()
            )
        ] or selected_sources
        source_roles = self._summarize_web_source_roles(query=query, sources=non_noisy_sources)
        lines = [
            f"웹 최신 확인: {query}",
            "",
            "현재 확인된 최신 정보:",
        ]

        added_points = 0
        for source in selected_sources[:3]:
            title = str(source.get("title") or source.get("result_title") or "(출처 없음)").strip()
            summary_text = str(source.get("summary_text") or source.get("snippet") or "").strip()
            if not summary_text:
                continue
            compact = self._clean_evidence_line(summary_text).rstrip(".")
            if not compact or self._looks_like_noisy_web_segment(compact):
                continue
            role_label = self._web_source_role_label(query=query, source=source)
            lines.append(f"- {compact}.")
            lines.append(f"  출처: {title} [{role_label}]")
            url = str(source.get("url") or "").strip()
            if url:
                lines.append(f"  링크: {url}")
            added_points += 1

        if added_points == 0:
            lines.append("- 최신 정보를 설명할 만한 검색 결과를 충분히 모으지 못했습니다.")

        lines.append("")
        lines.append("기준:")
        lines.append("- 최신성 민감 질문이라 공식 발표나 기사형 출처를 우선 확인했습니다.")
        if verification_label:
            lines.append(f"- 확인 강도: {verification_label}")
        if source_roles:
            lines.append(f"- 출처 성격: {', '.join(source_roles)}")
        ok_pages = [page for page in pages or [] if str(page.get("fetch_status") or "") == "ok"]
        if ok_pages:
            lines.append(f"- 읽을 수 있었던 원문 {len(ok_pages)}건과 검색 결과를 함께 정리했습니다.")
        else:
            lines.append("- 원문을 바로 읽지 못한 링크는 검색 결과 설명을 기준으로 정리했습니다.")
        return "\n".join(lines)

    def _extract_web_search_query_from_context(self, active_context: dict[str, Any]) -> str | None:
        label = str(active_context.get("label") or "").strip()
        prefix = "웹 검색: "
        if label.startswith(prefix):
            query = label[len(prefix) :].strip()
            return query or None
        return None

    def _build_web_search_active_context(
        self,
        *,
        query: str,
        results: list[dict[str, str]],
        summary_text: str,
        pages: list[dict[str, Any]] | None = None,
        ranked_sources: list[dict[str, Any]] | None = None,
        pre_selected_sources: list[dict[str, Any]] | None = None,
        intent_kind: str | None = None,
        answer_mode: str | None = None,
        freshness_risk: str | None = None,
        claim_coverage: list[dict[str, Any]] | None = None,
        claim_coverage_progress_summary: str | None = None,
        record_path: str | None = None,
    ) -> dict[str, Any]:
        sections: list[str] = []
        evidence_pool: list[dict[str, str]] = []
        retrieval_chunks: list[dict[str, str]] = []
        source_paths: list[str] = []
        if pre_selected_sources is not None:
            selected_sources = list(pre_selected_sources)
        else:
            ranked = list(
                ranked_sources
                or self._rank_web_search_sources(
                    query=query,
                    intent_kind=intent_kind,
                    answer_mode=answer_mode,
                    freshness_risk=freshness_risk,
                    results=results,
                    pages=pages,
                )
            )
            selected_sources = self._select_ranked_web_sources(
                query=query,
                intent_kind=intent_kind,
                answer_mode=answer_mode,
                freshness_risk=freshness_risk,
                ranked_sources=ranked,
                max_items=5,
            )
        total_chunks = 0
        for source in selected_sources:
            context_text = str(source.get("context_text") or "").strip()
            if bool(source.get("page_preferred")) and context_text:
                total_chunks += len(
                    self._chunk_text_for_retrieval(
                        source_path=str(source.get("url") or ""),
                        text=context_text,
                        max_chunks=4,
                    )
                )
            elif context_text:
                total_chunks += 1

        chunk_index = 0
        for index, source in enumerate(selected_sources, start=1):
            title = str(source.get("title") or source.get("result_title") or f"결과 {index}").strip()
            url = str(source.get("url") or "").strip()
            summary_excerpt = str(source.get("summary_text") or "").strip()
            context_text = str(source.get("context_text") or "").strip()
            page_preferred = bool(source.get("page_preferred"))
            if url:
                source_paths.append(url)
            sections.extend(
                [
                    f"{'원문 확인' if page_preferred else '검색 결과'} {index}: {title}",
                    f"링크: {url}",
                    f"발췌: {summary_excerpt or '(발췌 없음)'}",
                    "",
                ]
            )
            if page_preferred and context_text:
                for item in self._extract_text_evidence_items(source_path=url, text=context_text, max_items=3):
                    item["label"] = "웹 원문 근거"
                    item["source_name"] = title
                    evidence_pool.append(item)
                for chunk in self._chunk_text_for_retrieval(source_path=url, text=context_text, max_chunks=4):
                    chunk_index += 1
                    retrieval_chunks.append(
                        {
                            "chunk_id": f"web-page-{index}-{chunk_index}",
                            "chunk_index": chunk_index,
                            "total_chunks": total_chunks or 1,
                            "source_path": url,
                            "source_name": title,
                            "text": str(chunk.get("text") or "").strip(),
                        }
                    )
            else:
                item = self._make_evidence_item(
                    source_path=url,
                    label="웹 검색 결과",
                    snippet=summary_excerpt or context_text or title,
                )
                if item:
                    item["source_name"] = title
                    evidence_pool.append(item)
                if context_text:
                    chunk_index += 1
                    retrieval_chunks.append(
                        {
                            "chunk_id": f"web-result-{index}",
                            "chunk_index": chunk_index,
                            "total_chunks": total_chunks or max(len(selected_sources), 1),
                            "source_path": url,
                            "source_name": title,
                            "text": context_text,
                        }
                    )
        return self._build_active_context(
            kind="web_search",
            label=f"웹 검색: {query}",
            source_paths=source_paths,
            excerpt="\n".join(sections)[:9000],
            summary_hint=summary_text,
            suggested_prompts=self._follow_up_suggestions_for_web_search(
                query,
                answer_mode=answer_mode,
                claim_coverage=claim_coverage,
            ),
            evidence_pool=evidence_pool,
            retrieval_chunks=retrieval_chunks,
        ) | {
            "record_path": record_path,
            "claim_coverage": [dict(item) for item in claim_coverage or [] if isinstance(item, dict)],
            "claim_coverage_progress_summary": str(claim_coverage_progress_summary or "").strip(),
        }

    def _summarize_web_search_results(
        self,
        *,
        query: str,
        results: list[dict[str, str]],
        pages: list[dict[str, Any]] | None = None,
        ranked_sources: list[dict[str, Any]] | None = None,
        intent_kind: str | None = None,
        answer_mode: str | None = None,
        freshness_risk: str | None = None,
    ) -> str:
        lines = [
            f"웹 검색 요약: {query}",
            "",
        ]
        ranked = list(
            ranked_sources
            or self._rank_web_search_sources(
                query=query,
                intent_kind=intent_kind,
                answer_mode=answer_mode,
                freshness_risk=freshness_risk,
                results=results,
                pages=pages,
            )
        )
        selected_sources = self._select_ranked_web_sources(
            query=query,
            intent_kind=intent_kind,
            answer_mode=answer_mode,
            freshness_risk=freshness_risk,
            ranked_sources=ranked,
            max_items=3,
        )
        query_profile = self._infer_web_query_profile(
            query=query,
            intent_kind=intent_kind,
            answer_mode=answer_mode,
            freshness_risk=freshness_risk,
        )
        ok_pages = [page for page in pages or [] if str(page.get("fetch_status") or "") == "ok" and str(page.get("text") or "").strip()]
        if ok_pages and query_profile != "entity":
            lines.append(f"원문 확인: {len(ok_pages)}건")
            lines.append("")
        if selected_sources:
            if query_profile == "entity" and intent_kind == SearchIntentKind.EXTERNAL_FACT:
                return self._build_entity_web_summary(
                    query=query,
                    selected_sources=selected_sources,
                    ranked_sources=ranked,
                    pages=pages,
                )
            if answer_mode == AnswerMode.LATEST_UPDATE or query_profile == "live":
                return self._build_latest_update_web_summary(
                    query=query,
                    selected_sources=selected_sources,
                    pages=pages,
                )
            for index, source in enumerate(selected_sources, start=1):
                title = str(source.get("title") or source.get("result_title") or f"결과 {index}").strip()
                url = str(source.get("url") or "").strip()
                summary_text = str(source.get("summary_text") or "").strip() or "검색 결과 요약을 만들지 못했습니다."
                source_label = "원문" if bool(source.get("page_preferred")) else "검색 결과"
                lines.append(f"{index}. [{source_label}] {title}")
                lines.append(f"   요약: {summary_text}")
                if url:
                    lines.append(f"   링크: {url}")
            failed_pages = [page for page in pages or [] if str(page.get("fetch_status") or "") != "ok"]
            if failed_pages:
                lines.append("")
                lines.append(f"참고: 원문을 바로 읽지 못한 링크 {len(failed_pages)}건은 검색 결과 요약만 기록했습니다.")
            return "\n".join(lines)

        for index, result in enumerate(results[:3], start=1):
            title = str(result.get("title") or f"결과 {index}").strip()
            url = str(result.get("url") or "").strip()
            snippet = str(result.get("snippet") or "").strip() or "검색 결과 요약이 없습니다."
            lines.append(f"{index}. {title}")
            lines.append(f"   요약: {snippet}")
            if url:
                lines.append(f"   링크: {url}")
        return "\n".join(lines)

    def _run_web_search(
        self,
        *,
        request: UserRequest,
        query: str,
        intent_kind: str | None = None,
        answer_mode: str | None = None,
        freshness_risk: str | None = None,
        phase_event_callback: Callable[[dict[str, Any]], None] | None = None,
        deprioritized_urls: set[str] | None = None,
        seed_queries: list[str] | None = None,
        progress_query: str | None = None,
        response_action: str = "web_search",
        log_action: str = "web_search_executed",
    ) -> AgentResponse:
        search_tool = self.tools.get("search_web")
        if search_tool is None or self.web_search_store is None:
            return AgentResponse(
                text=(
                    f"현재 세션에서는 웹 검색을 허용한 상태지만 검색 도구가 아직 연결되지 않았습니다. "
                    f"그래서 '{query}' 검색을 실행하지 못했습니다."
                ),
                status=ResponseStatus.ANSWER,
                actions_taken=["respond_with_limitations"],
                response_origin={
                    "provider": "system",
                    "badge": "SYSTEM",
                    "label": "시스템 안내",
                    "model": None,
                    "kind": "assistant",
                },
            )

        self._emit_phase(
            phase_event_callback,
            phase="web_search_started",
            title="웹 검색 실행 중",
            detail=f"'{query}'에 대한 외부 웹 검색 결과를 읽는 중입니다.",
            note="읽기 전용 검색만 수행하고, 결과는 로컬 기록으로 남깁니다.",
        )
        query_profile = self._infer_web_query_profile(
            query=query,
            intent_kind=intent_kind,
            answer_mode=answer_mode,
            freshness_risk=freshness_risk,
        )
        effective_answer_mode = answer_mode
        if intent_kind == SearchIntentKind.EXTERNAL_FACT and query_profile == "entity":
            effective_answer_mode = AnswerMode.ENTITY_CARD
        elif intent_kind == SearchIntentKind.LIVE_LATEST and query_profile == "live":
            effective_answer_mode = AnswerMode.LATEST_UPDATE
        search_queries: list[str] = []
        seen_search_queries: set[str] = set()
        for candidate in [*(seed_queries or []), *self._expand_web_search_queries(
            query=query,
            intent_kind=intent_kind,
            answer_mode=effective_answer_mode,
            freshness_risk=freshness_risk,
        )]:
            normalized_candidate = " ".join(str(candidate or "").split()).strip()
            key = normalized_candidate.lower()
            if not normalized_candidate or key in seen_search_queries:
                continue
            seen_search_queries.add(key)
            search_queries.append(normalized_candidate)
        serialized_results: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        search_errors: list[str] = []
        for search_query in search_queries:
            try:
                raw_results = search_tool.search(
                    query=search_query,
                    max_results=8 if deprioritized_urls else 5,
                )
            except Exception as exc:
                search_errors.append(f"{search_query}: {exc}")
                continue
            for result in raw_results:
                url = str(result.url)
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                serialized_results.append(
                    {
                        "title": str(result.title),
                        "url": url,
                        "snippet": str(result.snippet),
                        "source": str(getattr(result, "source", "web")),
                        "matched_query": search_query,
                    }
                )
        if not serialized_results:
            error_text = search_errors[0] if search_errors else "검색 결과를 찾지 못했습니다."
            return AgentResponse(
                text=f"웹 검색을 시도했지만 실패했습니다: {error_text}",
                status=ResponseStatus.ERROR,
                actions_taken=["web_search_error"],
                response_origin={
                    "provider": "system",
                    "badge": "SYSTEM",
                    "label": "시스템 안내",
                    "model": None,
                    "kind": "assistant",
                },
            )
        if deprioritized_urls:
            prioritized = [
                item for item in serialized_results if str(item.get("url") or "").strip() not in deprioritized_urls
            ]
            fallback = [
                item for item in serialized_results if str(item.get("url") or "").strip() in deprioritized_urls
            ]
            serialized_results = prioritized + fallback
        serialized_results = serialized_results[:5]
        previous_active_context = self.session_store.get_active_context(request.session_id)
        previous_query = None
        previous_claim_coverage: list[dict[str, Any]] = []
        if isinstance(previous_active_context, dict) and previous_active_context.get("kind") == "web_search":
            previous_query = self._extract_web_search_query_from_context(previous_active_context)
            previous_claim_coverage = [
                dict(item)
                for item in previous_active_context.get("claim_coverage", [])
                if isinstance(item, dict)
            ]
        fetched_pages = self._fetch_web_page_records(
            query=query,
            search_tool=search_tool,
            intent_kind=intent_kind,
            answer_mode=effective_answer_mode,
            freshness_risk=freshness_risk,
            results=serialized_results,
            phase_event_callback=phase_event_callback,
        )
        ranked_sources = self._rank_web_search_sources(
            query=query,
            intent_kind=intent_kind,
            answer_mode=effective_answer_mode,
            freshness_risk=freshness_risk,
            results=serialized_results,
            pages=fetched_pages,
        )
        if intent_kind == SearchIntentKind.EXTERNAL_FACT and self._infer_web_query_profile(
            query=query,
            intent_kind=intent_kind,
            answer_mode=effective_answer_mode,
            freshness_risk=freshness_risk,
        ) == "entity":
            round_labels = [
                (
                    "web_search_second_pass",
                    "부족한 핵심 정보 다시 찾는 중",
                    "설명형 슬롯이 비었거나 단일 출처만 있을 때 보조 검색을 다시 실행합니다.",
                ),
                (
                    "web_search_confirmation_pass",
                    "약한 정보 다시 검증하는 중",
                    "단일 출처 정보는 공식/위키 성격의 질의로 한 번 더 교차 확인합니다.",
                ),
                (
                    "web_search_targeted_completion_pass",
                    "남은 핵심 슬롯 추가 확인 중",
                    "앞선 조사로도 비어 있거나 약한 슬롯만 남았을 때, 남은 슬롯 전용 질의를 한 번 더 실행합니다.",
                ),
            ]
            for round_index, (phase_name, phase_title, phase_note) in enumerate(round_labels, start=1):
                selected_sources = self._select_ranked_web_sources(
                    query=query,
                    intent_kind=intent_kind,
                    answer_mode=effective_answer_mode,
                    freshness_risk=freshness_risk,
                    ranked_sources=ranked_sources,
                    max_items=3,
                )
                second_pass_queries = self._build_entity_second_pass_queries(
                    query=query,
                    selected_sources=selected_sources,
                    existing_queries=search_queries,
                )
                if not second_pass_queries:
                    break
                self._emit_phase(
                    phase_event_callback,
                    phase=phase_name,
                    title=phase_title,
                    detail=f"'{query}' 설명에 비어 있거나 약한 핵심 정보를 보완하기 위해 {round_index + 1}차 조사를 실행하는 중입니다.",
                    note=phase_note,
                )
                new_results: list[dict[str, str]] = []
                for search_query in second_pass_queries:
                    search_queries.append(search_query)
                    try:
                        raw_results = search_tool.search(query=search_query, max_results=4)
                    except Exception as exc:
                        search_errors.append(f"{search_query}: {exc}")
                        continue
                    for result in raw_results:
                        url = str(result.url)
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)
                        item = {
                            "title": str(result.title),
                            "url": url,
                            "snippet": str(result.snippet),
                            "source": str(getattr(result, "source", "web")),
                            "matched_query": search_query,
                        }
                        serialized_results.append(item)
                        new_results.append(item)
                if not new_results:
                    continue
                new_pages = self._fetch_web_page_records(
                    query=query,
                    search_tool=search_tool,
                    intent_kind=intent_kind,
                    answer_mode=effective_answer_mode,
                    freshness_risk=freshness_risk,
                    results=new_results,
                    phase_event_callback=phase_event_callback,
                    max_pages=2,
                )
                fetched_pages.extend(new_pages)
                ranked_sources = self._rank_web_search_sources(
                    query=query,
                    intent_kind=intent_kind,
                    answer_mode=effective_answer_mode,
                    freshness_risk=freshness_risk,
                    results=serialized_results[:8],
                    pages=fetched_pages,
                )
        claim_coverage: list[dict[str, Any]] = []
        entity_sources: list[dict[str, Any]] | None = None
        query_profile = self._infer_web_query_profile(
            query=query,
            intent_kind=intent_kind,
            answer_mode=effective_answer_mode,
            freshness_risk=freshness_risk,
        )
        if intent_kind == SearchIntentKind.EXTERNAL_FACT and query_profile == "entity":
            entity_sources = self._select_ranked_web_sources(
                query=query,
                intent_kind=intent_kind,
                answer_mode=answer_mode,
                freshness_risk=freshness_risk,
                ranked_sources=ranked_sources,
                max_items=3,
            )
            entity_claim_records = self._build_entity_claim_records(
                query=query,
                selected_sources=entity_sources,
            )
            entity_core_coverage = summarize_slot_coverage(entity_claim_records, slots=CORE_ENTITY_SLOTS)
            primary_claims, weak_claims, _, _ = self._select_entity_fact_card_claims(
                query=query,
                claim_records=entity_claim_records,
            )
            claim_coverage = self._build_entity_claim_coverage_items(
                core_coverage=entity_core_coverage,
                primary_claims=primary_claims,
                weak_claims=weak_claims,
            )
            if previous_claim_coverage and self._looks_like_related_entity_query(previous_query, query):
                claim_coverage = self._annotate_claim_coverage_progress(
                    previous_claim_coverage=previous_claim_coverage,
                    current_claim_coverage=claim_coverage,
                    query=progress_query or query,
                )
        claim_coverage_progress_summary: str | None = None
        if (
            effective_answer_mode == AnswerMode.ENTITY_CARD
            and previous_claim_coverage
            and claim_coverage
            and self._looks_like_related_entity_query(previous_query, query)
        ):
            claim_coverage_progress_summary = self._build_claim_coverage_progress_summary(
                previous_claim_coverage=previous_claim_coverage,
                current_claim_coverage=claim_coverage,
                query=progress_query or query,
            )
        summary_text = self._summarize_web_search_results(
            query=query,
            intent_kind=intent_kind,
            answer_mode=effective_answer_mode,
            freshness_risk=freshness_risk,
            results=serialized_results[:8],
            pages=fetched_pages,
            ranked_sources=ranked_sources,
        )
        response_origin = self._build_web_search_origin(
            answer_mode=effective_answer_mode,
            selected_sources=self._select_ranked_web_sources(
                query=query,
                intent_kind=intent_kind,
                answer_mode=effective_answer_mode,
                freshness_risk=freshness_risk,
                ranked_sources=ranked_sources,
                max_items=3,
            ),
            query=query,
            claim_coverage=claim_coverage,
        )
        record_info = self.web_search_store.save(
            session_id=request.session_id,
            query=query,
            permission=self._extract_web_search_permission(request),
            results=serialized_results[:8],
            summary_text=summary_text,
            pages=fetched_pages,
            response_origin=response_origin,
            claim_coverage=claim_coverage,
            claim_coverage_progress_summary=claim_coverage_progress_summary,
        )
        record_path = str(record_info["record_path"])
        active_context = self._build_web_search_active_context(
            query=query,
            results=serialized_results[:8],
            summary_text=summary_text,
            pages=fetched_pages,
            ranked_sources=ranked_sources,
            pre_selected_sources=entity_sources,
            intent_kind=intent_kind,
            answer_mode=effective_answer_mode,
            freshness_risk=freshness_risk,
            claim_coverage=claim_coverage,
            claim_coverage_progress_summary=claim_coverage_progress_summary,
            record_path=record_path,
        )
        self.session_store.set_active_context(request.session_id, active_context)
        self.task_logger.log(
            session_id=request.session_id,
            action=log_action,
            detail={
                "query": query,
                "result_count": len(serialized_results[:8]),
                "page_count": len([page for page in fetched_pages if str(page.get("fetch_status") or "") == "ok"]),
                "record_path": record_path,
                "urls": [item["url"] for item in serialized_results[:8]],
                "search_queries": search_queries,
                "deprioritized_urls": sorted(deprioritized_urls or []),
            },
        )
        return AgentResponse(
            text=summary_text,
            status=ResponseStatus.ANSWER,
            actions_taken=[response_action],
            selected_source_paths=[item["url"] for item in serialized_results[:8] if item.get("url")],
            active_context=self._public_active_context(active_context),
            follow_up_suggestions=[str(prompt) for prompt in active_context["suggested_prompts"]],
            evidence=self._build_web_search_evidence(
                serialized_results[:8],
                pages=fetched_pages,
                ranked_sources=ranked_sources,
                query=query,
                intent_kind=intent_kind,
                answer_mode=effective_answer_mode,
                freshness_risk=freshness_risk,
            ),
            claim_coverage=claim_coverage,
            claim_coverage_progress_summary=claim_coverage_progress_summary,
            response_origin=response_origin,
            web_search_record_path=record_path,
        )

    def _retry_web_search_after_irrelevant_feedback(
        self,
        *,
        request: UserRequest,
        active_context: dict[str, Any],
        retry_feedback_reason: str | None,
        phase_event_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> AgentResponse | None:
        if active_context.get("kind") != "web_search":
            return None
        if self._extract_web_search_permission(request) != "enabled":
            return None
        if retry_feedback_reason not in {"irrelevant_result", "factual_error"}:
            return None

        query = self._extract_web_search_query_from_context(active_context)
        if not query:
            return None

        previous_urls = {
            str(url).strip()
            for url in active_context.get("source_paths", [])
            if isinstance(url, str) and str(url).strip()
        }
        self._emit_phase(
            phase_event_callback,
            phase="web_search_retry_started",
            title="웹 검색 결과 다시 추리는 중",
            detail=f"'{query}'에 대해 기존 상위 링크 우선순위를 낮춰 다시 확인하는 중입니다.",
            note="질문과 어긋나거나 사실이 다른 결과를 줄이기 위해 새 결과와 기존 결과를 다시 섞어 정렬합니다.",
        )
        search_intent = self._classify_search_intent(request.user_text)
        response = self._run_web_search(
            request=request,
            query=query,
            intent_kind=search_intent.kind,
            answer_mode=search_intent.answer_mode,
            freshness_risk=search_intent.freshness_risk,
            phase_event_callback=phase_event_callback,
            deprioritized_urls=previous_urls or None,
            response_action="web_search_retry",
            log_action="web_search_retried",
        )
        if response.status == ResponseStatus.ANSWER:
            response.text = (
                "기존 검색 결과가 질문과 어긋나거나 사실 확인이 더 필요해 보여, 상위 링크 우선순위를 낮춰 다시 찾아봤습니다.\n\n"
                + response.text
            )
            response.actions_taken = ["feedback_retry", *response.actions_taken]
        return response

    def _reuse_web_search_record(
        self,
        *,
        request: UserRequest,
        record_id: str | None = None,
        phase_event_callback: Callable[[dict[str, Any]], None] | None = None,
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AgentResponse:
        if self.web_search_store is None:
            return AgentResponse(
                text="이 세션에서 다시 불러올 웹 검색 기록 저장소가 아직 연결되지 않았습니다.",
                status=ResponseStatus.ANSWER,
                actions_taken=["respond_with_limitations"],
                response_origin={
                    "provider": "system",
                    "badge": "SYSTEM",
                    "label": "시스템 안내",
                    "model": None,
                    "kind": "assistant",
                },
            )

        self._emit_phase(
            phase_event_callback,
            phase="web_search_history_load",
            title="최근 웹 검색 기록 불러오는 중",
            detail="같은 세션에 저장된 최근 웹 검색 기록을 다시 읽는 중입니다.",
            note="이미 저장된 로컬 JSON 기록만 읽습니다.",
        )
        record = (
            self.web_search_store.get_session_record(request.session_id, record_id)
            if record_id
            else self.web_search_store.get_latest_session_record(request.session_id)
        )
        if record is None:
            return AgentResponse(
                text=(
                    "이 세션에는 아직 다시 불러올 웹 검색 기록이 없습니다. "
                    "먼저 '검색해봐'로 검색을 한 번 실행해 주세요."
                    if not record_id
                    else "선택한 웹 검색 기록을 찾지 못했습니다. 목록을 새로고침한 뒤 다시 선택해 주세요."
                ),
                status=ResponseStatus.ANSWER,
                actions_taken=["respond_with_limitations"],
                response_origin={
                    "provider": "system",
                    "badge": "SYSTEM",
                    "label": "시스템 안내",
                    "model": None,
                    "kind": "assistant",
                },
            )

        query = str(record.get("query") or "최근 검색").strip()
        stored_origin = record.get("response_origin") or {}
        stored_answer_mode = str(stored_origin.get("answer_mode") or "").strip()
        results = [dict(item) for item in record.get("results", []) if isinstance(item, dict)]
        pages = [dict(item) for item in record.get("pages", []) if isinstance(item, dict)]
        ranked_sources = self._rank_web_search_sources(
            query=query,
            results=results,
            pages=pages,
        )
        stored_summary_text = str(record.get("summary_text") or "").strip()
        if stored_summary_text:
            summary_text = stored_summary_text
        else:
            stored_intent_kind = SearchIntentKind.EXTERNAL_FACT if stored_answer_mode == AnswerMode.ENTITY_CARD else None
            summary_text = self._summarize_web_search_results(
                query=query,
                results=results,
                pages=pages,
                ranked_sources=ranked_sources,
                intent_kind=stored_intent_kind,
                answer_mode=stored_answer_mode or None,
            )
        stored_claim_coverage = [
            dict(item) for item in record.get("claim_coverage", []) if isinstance(item, dict)
        ]
        stored_progress_summary = str(record.get("claim_coverage_progress_summary") or "").strip()
        claim_coverage: list[dict[str, Any]] = []
        claim_coverage_progress_summary: str | None = None
        entity_sources: list[dict[str, Any]] | None = None
        if stored_claim_coverage:
            claim_coverage = stored_claim_coverage
            claim_coverage_progress_summary = stored_progress_summary or None
        else:
            query_profile = self._infer_web_query_profile(query=query)
            if query_profile == "entity":
                entity_sources = self._select_ranked_web_sources(
                    query=query,
                    ranked_sources=ranked_sources,
                    max_items=3,
                )
                entity_claim_records = self._build_entity_claim_records(
                    query=query,
                    selected_sources=entity_sources,
                )
                entity_core_coverage = summarize_slot_coverage(entity_claim_records, slots=CORE_ENTITY_SLOTS)
                primary_claims, weak_claims, _, _ = self._select_entity_fact_card_claims(
                    query=query,
                    claim_records=entity_claim_records,
                )
                claim_coverage = self._build_entity_claim_coverage_items(
                    core_coverage=entity_core_coverage,
                    primary_claims=primary_claims,
                    weak_claims=weak_claims,
                )

        def _infer_reloaded_answer_mode() -> str:
            if claim_coverage:
                return AnswerMode.ENTITY_CARD
            if stored_answer_mode in (AnswerMode.ENTITY_CARD, AnswerMode.LATEST_UPDATE):
                return stored_answer_mode
            if summary_text.startswith("웹 최신 확인:"):
                return AnswerMode.LATEST_UPDATE
            return AnswerMode.GENERAL

        reloaded_answer_mode = _infer_reloaded_answer_mode()
        record_path = str(record.get("record_path") or "").strip()
        active_context = self._build_web_search_active_context(
            query=query,
            results=results,
            summary_text=summary_text,
            pages=pages,
            ranked_sources=ranked_sources,
            pre_selected_sources=entity_sources,
            answer_mode=reloaded_answer_mode,
            claim_coverage=claim_coverage,
            claim_coverage_progress_summary=claim_coverage_progress_summary,
            record_path=record_path or None,
        )
        self.session_store.set_active_context(request.session_id, active_context)
        self.task_logger.log(
            session_id=request.session_id,
            action="web_search_record_loaded",
            detail={
                "query": query,
                "record_id": str(record.get("record_id") or ""),
                "record_path": record_path,
                "result_count": len(results),
            },
        )

        normalized = " ".join(request.user_text.strip().split())
        show_only = any(
            phrase in normalized
            for phrase in [
                "다시 보여",
                "다시 보여줘",
                "보여줘",
                "보여 주세요",
                "불러와",
                "불러 와",
                "꺼내",
                "기록 보여",
                "기록 다시",
            ]
        )
        if show_only:
            reload_origin: dict[str, Any]
            if stored_origin and stored_origin.get("answer_mode"):
                reload_origin = dict(stored_origin)
            else:
                reload_origin = self._build_web_search_origin(
                    answer_mode=reloaded_answer_mode,
                    selected_sources=ranked_sources[:3],
                    query=query,
                    claim_coverage=claim_coverage,
                )
            return AgentResponse(
                text=f"최근 웹 검색 기록을 다시 불러왔습니다.\n\n{summary_text}",
                status=ResponseStatus.ANSWER,
                actions_taken=["load_web_search_record"],
                selected_source_paths=[item.get("url", "") for item in results[:5] if item.get("url")],
                active_context=self._public_active_context(active_context),
                follow_up_suggestions=[str(prompt) for prompt in active_context["suggested_prompts"]],
                evidence=self._build_web_search_evidence(
                    results,
                    pages=pages,
                    ranked_sources=ranked_sources,
                ),
                claim_coverage=claim_coverage,
                response_origin=reload_origin,
                web_search_record_path=record_path or None,
            )

        response = self._respond_with_active_context(
            request=request,
            active_context=active_context,
            conversation_mode="document",
            stream_event_callback=stream_event_callback,
            phase_event_callback=phase_event_callback,
            cancel_requested=cancel_requested,
        )
        response.actions_taken = ["load_web_search_record", *response.actions_taken]
        response.web_search_record_path = record_path or None
        if stored_origin and stored_origin.get("answer_mode") and response.response_origin is None:
            response.response_origin = dict(stored_origin)
        return response

    def _looks_like_underspecified_next_step_request(self, user_request: str) -> bool:
        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return False
        next_step_keywords = [
            "다음엔 뭘 하면 돼",
            "다음엔 뭐 하면 돼",
            "다음에 뭘 하면 돼",
            "다음에 뭐 하면 돼",
            "그다음은",
            "다음은 뭐야",
            "어떻게 하면 돼",
            "뭐부터 하면 돼",
        ]
        return any(keyword in normalized for keyword in next_step_keywords)

    def _build_underspecified_next_step_response(self) -> AgentResponse:
        return AgentResponse(
            text=(
                "어떤 작업의 다음 단계인지 맥락이 조금 더 필요합니다. "
                "문서 요약 다음인지, 메모 저장 다음인지, 검색 결과 다음인지 한 줄만 더 알려주시면 "
                "그 흐름에 맞춰 바로 이어서 정리해 드리겠습니다."
            ),
            status=ResponseStatus.ANSWER,
            actions_taken=["respond_with_limitations"],
            response_origin={
                "provider": "system",
                "badge": "SYSTEM",
                "label": "시스템 안내",
                "model": None,
                "kind": "assistant",
            },
        )

    def _refine_follow_up_intent_with_context(self, user_request: str, base_intent: str) -> str:
        if base_intent != FOLLOW_UP_INTENT_GENERAL:
            return base_intent

        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return base_intent

        if any(keyword in normalized for keyword in ["메모처럼", "메모 형식", "메모로 다시", "정리본", "회의 메모"]):
            return FOLLOW_UP_INTENT_MEMO
        if any(keyword in normalized for keyword in ["할 일만", "todo", "투두", "다음엔 뭘", "뭘 하면 돼", "뭐부터", "다음 단계"]):
            return FOLLOW_UP_INTENT_ACTION_ITEMS
        if any(
            keyword in normalized
            for keyword in [
                "한 줄",
                "한줄",
                "한 문장",
                "한문장",
                "짧게",
                "간단히",
                "요점만",
                "짧은 요약",
                "뭐가 제일 중요",
                "가장 중요",
                "중요한 것만",
            ]
        ):
            return FOLLOW_UP_INTENT_KEY_POINTS
        return base_intent

    def _request_has_active_context_signal(self, *, user_request: str, active_context: dict[str, Any]) -> bool:
        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return False

        intent = self._detect_follow_up_intent(normalized)
        if intent != FOLLOW_UP_INTENT_GENERAL:
            return True

        label = str(active_context.get("label") or "").strip()
        source_paths = [str(path) for path in active_context.get("source_paths", []) if isinstance(path, str)]
        context_keywords = [
            "이 문서",
            "현재 문서",
            "이 파일",
            "이 내용",
            "문서",
            "파일",
            "요약",
            "검색 결과",
            "본문",
            "출처",
            "근거",
            "핵심",
            "정리",
            "설명",
            "내용",
            "메모",
            "실행할 일",
            "액션",
        ]

        if any(keyword in normalized for keyword in context_keywords):
            return True
        if self._contains_context_follow_up_cue(normalized):
            return True
        if label and label in normalized:
            return True
        if any(Path(path).name and Path(path).name in normalized for path in source_paths):
            return True
        return False

    def _is_small_talk_request(self, user_request: str) -> bool:
        normalized = " ".join(user_request.strip().split())
        if not normalized:
            return False
        doc_keywords = [
            "문서",
            "파일",
            "요약",
            "검색",
            "출처",
            "근거",
            "메모",
            "정리",
            "설명",
            "내용",
            "본문",
            "핵심",
            "실행할 일",
            "액션",
            "저장",
            "승인",
        ]

        if any(keyword in normalized for keyword in doc_keywords):
            return False
        if any(keyword in normalized.lower() for keyword in ["source:", "snippet:", "match:"]):
            return False

        if self._contains_small_talk_signal(normalized):
            return len(normalized) <= 24
        return False

    def _classify_active_context_request(
        self,
        *,
        request: UserRequest,
        active_context: dict[str, Any] | None,
        has_search_request: bool,
        has_explicit_source_path: bool,
        uploaded_file: dict[str, Any] | None,
    ) -> str:
        if not active_context:
            return "none"
        if not request.user_text.strip():
            return "none"
        if uploaded_file is not None or has_explicit_source_path or has_search_request:
            return "none"

        has_context_signal = self._request_has_active_context_signal(
            user_request=request.user_text,
            active_context=active_context,
        )
        has_small_talk_signal = self._contains_small_talk_signal(request.user_text)

        if has_context_signal and has_small_talk_signal:
            return "mixed"
        if has_context_signal:
            return "document"
        return "general"

    def _mixed_context_intro(self, *, user_request: str, intent: str) -> str:
        prefix = self._small_talk_prefix(user_request)
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return f"{prefix} 이어서 현재 문서 기준으로 핵심만 정리해 드릴게요."
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return f"{prefix} 이어서 현재 문서 기준으로 실행할 일을 추려보겠습니다."
        if intent == FOLLOW_UP_INTENT_MEMO:
            return f"{prefix} 이어서 현재 문서 내용을 메모 형식으로 정리해 드릴게요."
        return f"{prefix} 이어서 현재 문서를 기준으로 말씀드리겠습니다."

    def _apply_context_conversation_mode(
        self,
        *,
        answer: str,
        user_request: str,
        intent: str,
        conversation_mode: str,
    ) -> str:
        if conversation_mode != "mixed":
            return answer

        intro = self._mixed_context_intro(user_request=user_request, intent=intent)
        trimmed = answer.strip()
        if not trimmed:
            return intro
        if trimmed.startswith(intro):
            return trimmed
        separator = "\n\n" if "\n" in trimmed else " "
        return f"{intro}{separator}{trimmed}"

    def _public_active_context(self, context: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(context, dict):
            return None
        return {
            "kind": context.get("kind"),
            "label": context.get("label"),
            "source_paths": [str(path) for path in context.get("source_paths", [])],
            "summary_hint": context.get("summary_hint"),
            "suggested_prompts": [str(prompt) for prompt in context.get("suggested_prompts", [])],
            "record_path": context.get("record_path"),
            "claim_coverage_progress_summary": str(context.get("claim_coverage_progress_summary") or "").strip(),
        }

    def _build_file_active_context(self, *, resolved_path: str, text: str, summary: str) -> dict[str, Any]:
        return self._build_active_context(
            kind="document",
            label=Path(resolved_path).name,
            source_paths=[resolved_path],
            excerpt=self._build_context_excerpt_from_text(text),
            summary_hint=summary,
            suggested_prompts=self._follow_up_suggestions_for_file(resolved_path),
            evidence_pool=self._extract_text_evidence_items(source_path=resolved_path, text=text),
            retrieval_chunks=self._chunk_text_for_retrieval(source_path=resolved_path, text=text),
        )

    def _build_search_active_context(
        self,
        *,
        search_query: str,
        selected_results: list[FileSearchResult],
        read_results: list[Any],
        summary: str,
    ) -> dict[str, Any]:
        sections: list[str] = []
        for search_result, read_result in zip(selected_results, read_results):
            sections.extend(
                [
                    f"Source: {read_result.resolved_path}",
                    f"Match: {search_result.matched_on}",
                    f"Snippet: {search_result.snippet or '(no snippet)'}",
                    read_result.text[:2500],
                    "",
                ]
            )
        return self._build_active_context(
            kind="search",
            label=f"'{search_query}' 검색 결과",
            source_paths=[item.path for item in selected_results],
            excerpt="\n".join(sections)[:9000],
            summary_hint=summary,
            suggested_prompts=self._follow_up_suggestions_for_search(search_query),
            evidence_pool=self._extract_search_evidence_items(
                selected_results=selected_results,
                read_results=read_results,
            ),
            retrieval_chunks=self._collect_retrieval_chunks(read_results=read_results),
        )

    def _respond_with_active_context(
        self,
        *,
        request: UserRequest,
        active_context: dict[str, Any],
        conversation_mode: str = "document",
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
        phase_event_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AgentResponse:
        intent = self._refine_follow_up_intent_with_context(
            request.user_text,
            self._detect_follow_up_intent(request.user_text),
        )
        retry_feedback_label = self._extract_retry_feedback_label(request)
        retry_feedback_reason = self._extract_retry_feedback_reason(request)
        retry_target_message_id = self._extract_retry_target_message_id(request)
        if retry_feedback_reason in {"irrelevant_result", "factual_error"}:
            web_retry_response = self._retry_web_search_after_irrelevant_feedback(
                request=request,
                active_context=active_context,
                retry_feedback_reason=retry_feedback_reason,
                phase_event_callback=phase_event_callback,
            )
            if web_retry_response is not None:
                return web_retry_response
        retry_policy = self._build_retry_policy(
            retry_feedback_label=retry_feedback_label,
            retry_feedback_reason=retry_feedback_reason,
            active_context=active_context,
        )
        retrieved_chunks = self._select_retrieval_chunks(
            active_context=active_context,
            intent=intent,
            user_request=request.user_text,
        )
        retrieved_excerpt = self._compose_retrieved_context_excerpt(
            chunks=retrieved_chunks,
            fallback_excerpt=str(active_context.get("excerpt") or ""),
        )
        candidate_evidence_pool = self._dedupe_evidence_items(
            self._extract_evidence_from_chunks(chunks=retrieved_chunks)
            + [dict(item) for item in active_context.get("evidence_pool", []) if isinstance(item, dict)],
            max_items=12,
        )
        candidate_evidence_pool = self._filter_evidence_pool_for_retry(
            evidence_pool=candidate_evidence_pool,
            active_context=active_context,
            retry_feedback_reason=retry_feedback_reason,
            policy=retry_policy,
        )
        selected_evidence = self._select_evidence_items(
            evidence_pool=candidate_evidence_pool,
            intent=intent,
            user_request=request.user_text,
            max_items=int(retry_policy.get("max_evidence_items") or 4),
        )
        grounded_excerpt = self._compose_grounded_context_excerpt(
            evidence_items=selected_evidence,
            chunks=retrieved_chunks,
            fallback_excerpt=retrieved_excerpt,
            max_supporting_chunks=int(retry_policy.get("max_supporting_chunks") or 2),
        )
        model_user_request = self._augment_retry_request(
            user_request=request.user_text,
            retry_feedback_label=retry_feedback_label,
            retry_feedback_reason=retry_feedback_reason,
        )
        self._emit_phase(
            phase_event_callback,
            phase="context_retrieval_started",
            title="관련 문맥 추리는 중",
            detail=(
                f"현재 문서에서 질문과 관련된 chunk {len(retrieved_chunks) or 1}개와 "
                f"핵심 근거 {len(selected_evidence) or 1}개를 고르는 중입니다."
            ),
            note="모델에는 선택된 근거와 짧은 보조 문맥만 넘겨 추측을 줄입니다.",
        )
        answer = self._collect_model_stream(
            self.model.stream_answer_with_context(
                intent=intent,
                user_request=model_user_request,
                context_label=str(active_context.get("label") or "현재 문서"),
                source_paths=[str(path) for path in active_context.get("source_paths", [])],
                context_excerpt=grounded_excerpt,
                summary_hint=(
                    None
                    if selected_evidence or retry_policy.get("suppress_summary_hint")
                    else str(active_context.get("summary_hint") or "")
                ),
                evidence_items=selected_evidence,
            ),
            stream_event_callback=stream_event_callback,
            cancel_requested=cancel_requested,
        )
        answer = self._apply_context_conversation_mode(
            answer=answer,
            user_request=request.user_text,
            intent=intent,
            conversation_mode=conversation_mode,
        )
        self.task_logger.log(
            session_id=request.session_id,
            action="answer_with_active_context",
            detail={
                "label": active_context.get("label"),
                "source_paths": active_context.get("source_paths", []),
                "intent": intent,
                "conversation_mode": conversation_mode,
                "retrieved_chunk_count": len(retrieved_chunks),
                "selected_evidence_count": len(selected_evidence),
                "retry_feedback_label": retry_feedback_label,
                "retry_feedback_reason": retry_feedback_reason,
                "retry_target_message_id": retry_target_message_id,
            },
        )
        actions_taken = ["answer_with_active_context"]
        if retry_feedback_label in {"unclear", "incorrect"}:
            actions_taken.insert(0, "feedback_retry")
        return AgentResponse(
            text=answer,
            status=ResponseStatus.ANSWER,
            actions_taken=actions_taken,
            selected_source_paths=[str(path) for path in active_context.get("source_paths", [])],
            active_context=self._public_active_context(active_context),
            follow_up_suggestions=[str(prompt) for prompt in active_context.get("suggested_prompts", [])],
            evidence=selected_evidence,
            web_search_record_path=str(active_context.get("record_path") or "") or None,
        )

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

    def _build_multi_file_summary(
        self,
        *,
        search_query: str,
        selected_results: list[FileSearchResult],
        read_results: list[Any],
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
        phase_event_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> tuple[str, str, list[dict[str, Any]]]:
        source_lines: list[str] = []
        combined_sections = [f"Search query: {search_query}", "", "Selected sources:"]
        for search_result, read_result in zip(selected_results, read_results):
            source_lines.extend(
                [
                    f"### {read_result.resolved_path}",
                    f"- 일치 방식: {search_result.matched_on}",
                    f"- 발췌: {search_result.snippet or '(발췌 없음)'}",
                ]
            )
            combined_sections.extend(
                [
                    f"Source path: {read_result.resolved_path}",
                    f"Match type: {search_result.matched_on}",
                    f"Snippet: {search_result.snippet or '(no snippet)'}",
                    "",
                ]
            )

        combined_sections.append("")
        for search_result, read_result in zip(selected_results, read_results):
            combined_sections.extend(
                [
                    f"## Source: {read_result.resolved_path}",
                    f"Match type: {search_result.matched_on}",
                    f"Snippet: {search_result.snippet or '(no snippet)'}",
                    read_result.text[:4000],
                    "",
                ]
            )

        summary_input = "\n".join(combined_sections)[:12000]
        summary, summary_chunks = self._summarize_text_with_chunking(
            text=summary_input,
            source_label=f"'{search_query}' 검색 결과",
            source_path=f"'{search_query}' 검색 결과",
            reduce_source_type="search_results",
            stream_event_callback=stream_event_callback,
            phase_event_callback=phase_event_callback,
            cancel_requested=cancel_requested,
        )
        note_body = "\n".join(
            [
                f"# '{search_query}' 검색 요약",
                "",
                f"- 검색어: {search_query}",
                "",
                "## 출처 참고",
                *source_lines,
                "",
                "## 요약",
                summary,
            ]
        )
        return summary, note_body, summary_chunks

    def _collect_model_stream(
        self,
        events,
        *,
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> str:
        text = ""
        iterator = iter(events)
        try:
            for event in iterator:
                if cancel_requested and cancel_requested():
                    raise RequestCancelledError("stream_cancelled")
                if event.kind == StreamEventType.TEXT_REPLACE:
                    text = event.text
                    if stream_event_callback:
                        stream_event_callback({"event": StreamEventType.TEXT_REPLACE, "text": event.text})
                    continue
                text += event.text
                if stream_event_callback:
                    stream_event_callback({"event": StreamEventType.TEXT_DELTA, "delta": event.text})
        finally:
            close = getattr(iterator, "close", None)
            if callable(close):
                close()
        return text

    def _raise_if_cancelled(self, cancel_requested: Callable[[], bool] | None) -> None:
        if cancel_requested and cancel_requested():
            raise RequestCancelledError("stream_cancelled")

    def _build_save_note_approval(
        self,
        *,
        note_path: str,
        note_body: str,
        source_paths: list[str],
        artifact_id: str | None = None,
        source_message_id: str | None = None,
        save_content_source: str = SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT,
    ) -> ApprovalRequest:
        writer = self.tools.get("write_note")
        overwrite = False
        if writer is not None and hasattr(writer, "inspect_target"):
            target_info = writer.inspect_target(path=note_path)
            overwrite = bool(target_info.get("overwrite", False))
        else:
            overwrite = Path(note_path).expanduser().resolve().exists()

        return ApprovalRequest.create_save_note(
            requested_path=note_path,
            overwrite=overwrite,
            preview_markdown=self._build_note_preview(note_body),
            source_paths=source_paths,
            note_text=note_body,
            artifact_id=artifact_id,
            source_message_id=source_message_id,
            save_content_source=save_content_source,
        )

    def _request_save_note_approval(
        self,
        *,
        session_id: str,
        note_path: str,
        note_body: str,
        source_paths: list[str],
        artifact_id: str | None = None,
        source_message_id: str | None = None,
        save_content_source: str = SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT,
        approval_request_detail: dict[str, Any] | None = None,
    ) -> ApprovalRequest:
        approval = self._build_save_note_approval(
            note_path=note_path,
            note_body=note_body,
            source_paths=source_paths,
            artifact_id=artifact_id,
            source_message_id=source_message_id,
            save_content_source=save_content_source,
        )
        self.session_store.add_pending_approval(session_id, approval.to_record())
        detail = {
            "approval_id": approval.approval_id,
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "note_path": approval.requested_path,
            "overwrite": approval.overwrite,
            "save_content_source": approval.save_content_source,
        }
        if approval_request_detail:
            detail.update({key: value for key, value in approval_request_detail.items() if value is not None})
        self.task_logger.log(
            session_id=session_id,
            action="approval_requested",
            detail=detail,
        )
        return approval

    def _execute_save_note_write(
        self,
        *,
        session_id: str,
        note_path: str,
        note_body: str,
        artifact_id: str | None = None,
        source_message_id: str | None = None,
        approval_id: str | None = None,
        source_paths: list[str] | None = None,
        save_content_source: str = SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT,
        write_detail: dict[str, Any] | None = None,
        record_accepted_as_is: bool = False,
        preserve_existing_corrected_outcome: bool = False,
        allow_overwrite: bool = False,
    ) -> tuple[str, dict[str, Any] | None]:
        saved_path = self.tools["write_note"].run(
            path=note_path,
            text=note_body,
            approved=True,
            allow_overwrite=allow_overwrite,
        )
        detail = {
            "artifact_id": artifact_id,
            "source_message_id": source_message_id,
            "note_path": saved_path,
            "save_content_source": save_content_source,
        }
        if approval_id:
            detail["approval_id"] = approval_id
        if source_paths is not None:
            detail["source_paths"] = list(source_paths)
        if write_detail:
            detail.update({key: value for key, value in write_detail.items() if value is not None})
        self.task_logger.log(
            session_id=session_id,
            action="write_note",
            detail=detail,
        )

        corrected_outcome: dict[str, Any] | None = None
        if record_accepted_as_is:
            updated_source_message = self.session_store.record_corrected_outcome_for_artifact(
                session_id,
                artifact_id=artifact_id,
                outcome="accepted_as_is",
                approval_id=approval_id,
                saved_note_path=saved_path,
            )
            if updated_source_message is not None:
                outcome = updated_source_message.get("corrected_outcome")
                if isinstance(outcome, dict):
                    corrected_outcome = dict(outcome)
                    self._log_corrected_outcome_recorded(session_id, corrected_outcome)
        elif preserve_existing_corrected_outcome:
            updated_source_message = self.session_store.record_corrected_outcome_for_artifact(
                session_id,
                artifact_id=artifact_id,
                outcome="corrected",
                approval_id=approval_id,
                saved_note_path=saved_path,
                preserve_existing=True,
            )
            if updated_source_message is not None:
                outcome = updated_source_message.get("corrected_outcome")
                if isinstance(outcome, dict):
                    corrected_outcome = dict(outcome)
                    self._log_corrected_outcome_recorded(session_id, corrected_outcome)
        return saved_path, corrected_outcome

    def _build_grounded_brief_source_response_fields(
        self,
        *,
        artifact_id: str | None,
        source_message_id: str | None,
        saved_note_path: str | None = None,
        save_content_source: str | None = None,
        corrected_outcome: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fields: dict[str, Any] = {}
        if artifact_id:
            fields["artifact_id"] = artifact_id
            fields["artifact_kind"] = ArtifactKind.GROUNDED_BRIEF
        if source_message_id:
            fields["message_id"] = source_message_id
            fields["source_message_id"] = source_message_id
        if saved_note_path:
            fields["saved_note_path"] = saved_note_path
        if save_content_source:
            fields["save_content_source"] = save_content_source
        if corrected_outcome:
            fields["corrected_outcome"] = dict(corrected_outcome)
        return fields

    def _execute_pending_approval(self, request: UserRequest) -> AgentResponse:
        approval_id = request.approved_approval_id
        if not approval_id:
            return AgentResponse(
                text="승인할 작업 ID가 없습니다.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        approval_record = self.session_store.pop_pending_approval(request.session_id, approval_id)
        if approval_record is None:
            return AgentResponse(
                text="승인 대상을 찾지 못했습니다. 이미 처리되었거나 만료되었을 수 있습니다.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        approval = ApprovalRequest.from_record(approval_record)
        if approval.kind != "save_note":
            return AgentResponse(
                text=f"지원하지 않는 승인 작업입니다: {approval.kind}",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        self.task_logger.log(
            session_id=request.session_id,
            action="approval_granted",
            detail={
                "approval_id": approval.approval_id,
                "kind": approval.kind,
                "requested_path": approval.requested_path,
                "overwrite": approval.overwrite,
                "artifact_id": approval.artifact_id,
                "source_message_id": approval.source_message_id,
                "save_content_source": approval.save_content_source,
            },
        )

        saved_path, _ = self._execute_save_note_write(
            session_id=request.session_id,
            note_path=approval.requested_path,
            note_body=approval.note_text,
            artifact_id=approval.artifact_id,
            source_message_id=approval.source_message_id,
            approval_id=approval.approval_id,
            source_paths=approval.source_paths,
            save_content_source=approval.save_content_source or SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT,
            record_accepted_as_is=(
                (approval.save_content_source or SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT)
                == SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT
            ),
            preserve_existing_corrected_outcome=(
                (approval.save_content_source or "").strip() == SAVE_CONTENT_SOURCE_CORRECTED_TEXT
            ),
            allow_overwrite=approval.overwrite,
        )
        saved_text = f"요약 노트를 {saved_path}에 저장했습니다."
        if approval.overwrite:
            saved_text = f"기존 파일을 덮어쓰고 {saved_path}에 저장했습니다."
        if (approval.save_content_source or "").strip() == SAVE_CONTENT_SOURCE_CORRECTED_TEXT:
            saved_text = (
                f"승인 시점에 고정된 수정본을 {saved_path}에 저장했습니다. "
                "더 새 수정본을 저장하려면 다시 저장 요청해 주세요."
            )
        return AgentResponse(
            text=saved_text,
            status=ResponseStatus.SAVED,
            actions_taken=["approval_granted", "write_note"],
            saved_note_path=saved_path,
            selected_source_paths=list(approval.source_paths),
            artifact_id=approval.artifact_id,
            artifact_kind=ArtifactKind.GROUNDED_BRIEF if approval.artifact_id else None,
            source_message_id=approval.source_message_id,
            save_content_source=approval.save_content_source,
        )

    def _reissue_pending_approval(self, request: UserRequest) -> AgentResponse:
        approval_id = request.reissue_approval_id
        note_path = str(request.metadata.get("note_path") or "").strip()
        if not approval_id:
            return AgentResponse(
                text="다시 발급할 승인 작업 ID가 없습니다.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )
        if not note_path:
            return AgentResponse(
                text="새 저장 경로를 입력해 주세요.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        approval_record = self.session_store.get_pending_approval(request.session_id, approval_id)
        if approval_record is None:
            return AgentResponse(
                text="다시 발급할 승인 대상을 찾지 못했습니다. 이미 처리되었거나 만료되었을 수 있습니다.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        approval = ApprovalRequest.from_record(approval_record)
        if approval.kind != "save_note":
            return AgentResponse(
                text=f"지원하지 않는 승인 작업입니다: {approval.kind}",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        try:
            reissued = self._build_save_note_approval(
                note_path=note_path,
                note_body=approval.note_text,
                source_paths=list(approval.source_paths),
                artifact_id=approval.artifact_id,
                source_message_id=approval.source_message_id,
                save_content_source=approval.save_content_source or SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT,
            )
        except (PermissionError, OSError) as exc:
            return AgentResponse(
                text=str(exc),
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
                selected_source_paths=list(approval.source_paths),
            )
        approval_reason_record = self._build_approval_reason_record(
            session_id=request.session_id,
            artifact_id=reissued.artifact_id,
            approval_id=reissued.approval_id,
            source_message_id=reissued.source_message_id,
            reason_scope="approval_reissue",
            reason_label="path_change",
        )
        reissued.approval_reason_record = approval_reason_record
        self.session_store.pop_pending_approval(request.session_id, approval.approval_id)
        self.session_store.add_pending_approval(request.session_id, reissued.to_record())

        self.task_logger.log(
            session_id=request.session_id,
            action="approval_reissued",
            detail={
                "old_approval_id": approval.approval_id,
                "new_approval_id": reissued.approval_id,
                "old_requested_path": approval.requested_path,
                "new_requested_path": reissued.requested_path,
                "overwrite": reissued.overwrite,
                "source_paths": reissued.source_paths,
                "artifact_id": reissued.artifact_id,
                "source_message_id": reissued.source_message_id,
                "save_content_source": reissued.save_content_source,
                "approval_reason_record": approval_reason_record,
            },
        )

        if reissued.overwrite:
            text = (
                f"저장 경로를 {reissued.requested_path}로 바꿨습니다. "
                "하지만 현재 경로에는 이미 파일이 있으므로 다른 저장 경로로 다시 요청해 주세요."
            )
        else:
            text = (
                f"저장 경로를 {reissued.requested_path}로 바꿨습니다. "
                "새 경로로 저장하려면 다시 승인해 주세요."
            )

        return AgentResponse(
            text=text,
            status=ResponseStatus.NEEDS_APPROVAL,
            actions_taken=["approval_reissued"],
            requires_approval=True,
            proposed_note_path=reissued.requested_path,
            selected_source_paths=list(reissued.source_paths),
            note_preview=reissued.preview_markdown,
            approval=reissued.to_public_dict(),
            artifact_id=reissued.artifact_id,
            artifact_kind=ArtifactKind.GROUNDED_BRIEF if reissued.artifact_id else None,
            source_message_id=reissued.source_message_id,
            approval_reason_record=approval_reason_record,
            save_content_source=reissued.save_content_source,
        )

    def _reject_pending_approval(self, request: UserRequest) -> AgentResponse:
        approval_id = request.rejected_approval_id
        if not approval_id:
            return AgentResponse(
                text="취소할 승인 작업 ID가 없습니다.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        approval_record = self.session_store.pop_pending_approval(request.session_id, approval_id)
        if approval_record is None:
            return AgentResponse(
                text="취소 대상을 찾지 못했습니다. 이미 처리되었거나 만료되었을 수 있습니다.",
                status=ResponseStatus.ERROR,
                actions_taken=["approval_error"],
            )

        approval = ApprovalRequest.from_record(approval_record)
        approval_reason_record = self._build_approval_reason_record(
            session_id=request.session_id,
            artifact_id=approval.artifact_id,
            approval_id=approval.approval_id,
            source_message_id=approval.source_message_id,
            reason_scope="approval_reject",
            reason_label="explicit_rejection",
        )
        self.task_logger.log(
            session_id=request.session_id,
            action="approval_rejected",
            detail={
                "approval_id": approval.approval_id,
                "kind": approval.kind,
                "requested_path": approval.requested_path,
                "artifact_id": approval.artifact_id,
                "source_message_id": approval.source_message_id,
                "save_content_source": approval.save_content_source,
                "approval_reason_record": approval_reason_record,
            },
        )
        return AgentResponse(
            text="저장 승인을 취소했습니다.",
            status=ResponseStatus.ANSWER,
            actions_taken=["approval_rejected"],
            selected_source_paths=list(approval.source_paths),
            artifact_id=approval.artifact_id,
            artifact_kind=ArtifactKind.GROUNDED_BRIEF if approval.artifact_id else None,
            source_message_id=approval.source_message_id,
            approval_reason_record=approval_reason_record,
            save_content_source=approval.save_content_source,
        )

    def _assistant_message(self, response: AgentResponse) -> Dict[str, Any]:
        message: Dict[str, Any] = {"role": "assistant", "text": response.text, "status": response.status}
        if response.message_id:
            message["message_id"] = response.message_id
        if response.artifact_id:
            message["artifact_id"] = response.artifact_id
        if response.artifact_kind:
            message["artifact_kind"] = response.artifact_kind
        if response.source_message_id:
            message["source_message_id"] = response.source_message_id
        if response.requires_approval:
            message["requires_approval"] = True
        if response.proposed_note_path:
            message["proposed_note_path"] = response.proposed_note_path
        if response.saved_note_path:
            message["saved_note_path"] = response.saved_note_path
        if response.web_search_record_path:
            message["web_search_record_path"] = response.web_search_record_path
        if response.selected_source_paths:
            message["selected_source_paths"] = response.selected_source_paths
        if response.note_preview:
            message["note_preview"] = response.note_preview
        if response.approval:
            message["approval"] = dict(response.approval)
            approval_id = response.approval.get("approval_id")
            if isinstance(approval_id, str) and approval_id:
                message["approval_id"] = approval_id
        if response.active_context:
            message["active_context"] = dict(response.active_context)
        if response.follow_up_suggestions:
            message["follow_up_suggestions"] = list(response.follow_up_suggestions)
        if response.response_origin:
            message["response_origin"] = dict(response.response_origin)
        if response.evidence:
            message["evidence"] = [dict(item) for item in response.evidence if isinstance(item, dict)]
        if response.summary_chunks:
            message["summary_chunks"] = [dict(item) for item in response.summary_chunks if isinstance(item, dict)]
        if response.claim_coverage:
            message["claim_coverage"] = [dict(item) for item in response.claim_coverage if isinstance(item, dict)]
        if response.claim_coverage_progress_summary:
            message["claim_coverage_progress_summary"] = response.claim_coverage_progress_summary
        if response.original_response_snapshot:
            message["original_response_snapshot"] = dict(response.original_response_snapshot)
        if response.corrected_outcome:
            message["corrected_outcome"] = dict(response.corrected_outcome)
        if response.approval_reason_record:
            message["approval_reason_record"] = dict(response.approval_reason_record)
        if response.save_content_source:
            message["save_content_source"] = response.save_content_source
        return message

    def _agent_response_log_detail(self, response: AgentResponse) -> dict[str, Any]:
        approval_save_content_source = None
        approval_source_message_id = None
        if isinstance(response.approval, dict):
            approval_save_content_source = response.approval.get("save_content_source")
            approval_source_message_id = response.approval.get("source_message_id")
        return {
            "status": response.status,
            "actions": response.actions_taken,
            "requires_approval": response.requires_approval,
            "proposed_note_path": response.proposed_note_path,
            "saved_note_path": response.saved_note_path,
            "selected_source_paths": response.selected_source_paths,
            "has_note_preview": bool(response.note_preview),
            "approval_id": response.approval["approval_id"] if response.approval else None,
            "artifact_id": response.artifact_id,
            "artifact_kind": response.artifact_kind,
            "source_message_id": response.source_message_id or approval_source_message_id,
            "save_content_source": response.save_content_source or approval_save_content_source,
            "approval_reason_record": dict(response.approval_reason_record) if response.approval_reason_record else None,
            "active_context_label": response.active_context.get("label") if response.active_context else None,
            "evidence_count": len(response.evidence),
            "summary_chunk_count": len(response.summary_chunks),
        }

    def handle(
        self,
        request: UserRequest,
        *,
        stream_event_callback: Callable[[dict[str, Any]], None] | None = None,
        phase_event_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> AgentResponse:
        self.task_logger.log(
            session_id=request.session_id,
            action="request_received",
            detail={
                "user_text": request.user_text,
                "source_path": request.metadata.get("source_path"),
                "search_root": request.metadata.get("search_root"),
                "search_query": request.metadata.get("search_query"),
                "save_summary": bool(request.metadata.get("save_summary")),
                "approved": request.approved,
                "approved_approval_id": request.approved_approval_id,
                "rejected_approval_id": request.rejected_approval_id,
                "reissue_approval_id": request.reissue_approval_id,
                "corrected_save_message_id": request.metadata.get("corrected_save_message_id"),
                "note_path": request.metadata.get("note_path"),
                "retry_feedback_label": request.metadata.get("retry_feedback_label"),
                "retry_feedback_reason": request.metadata.get("retry_feedback_reason"),
                "retry_target_message_id": request.metadata.get("retry_target_message_id"),
            },
        )
        if request.metadata.get("corrected_save_message_id"):
            self._emit_phase(
                phase_event_callback,
                phase="approval_prepared",
                title="수정본 저장 승인 카드 준비 중",
                detail="기록된 수정본으로 새 저장 승인 스냅샷을 만드는 중입니다.",
                note="현재 편집 중인 텍스트는 포함되지 않으며, 승인 미리보기는 요청 시점 그대로 고정됩니다.",
            )
            response = self._request_corrected_save_bridge(request)
            self._append_response_message(request.session_id, response)
            self.task_logger.log(
                session_id=request.session_id,
                action="agent_response",
                detail=self._agent_response_log_detail(response),
            )
            return response

        if request.reissue_approval_id:
            self._emit_phase(
                phase_event_callback,
                phase="approval_reissue",
                title="저장 승인 경로 다시 준비 중",
                detail="기존 승인 요청의 본문과 출처를 유지한 채 새 저장 경로로 승인 객체를 다시 만드는 중입니다.",
                note="실제 파일은 아직 저장하지 않습니다.",
            )
            response = self._reissue_pending_approval(request)
            self._append_response_message(request.session_id, response)
            self.task_logger.log(
                session_id=request.session_id,
                action="agent_response",
                detail=self._agent_response_log_detail(response),
            )
            return response

        if request.approved_approval_id:
            self._emit_phase(
                phase_event_callback,
                phase="approval_execute",
                title="승인된 작업 실행 중",
                detail="승인된 저장 작업을 확인하고 실제 파일 쓰기를 준비하는 중입니다.",
                note="기존 승인 객체만 실행합니다.",
            )
            response = self._execute_pending_approval(request)
            self._append_response_message(request.session_id, response)
            self.task_logger.log(
                session_id=request.session_id,
                action="agent_response",
                detail=self._agent_response_log_detail(response),
            )
            return response

        if request.rejected_approval_id:
            self._emit_phase(
                phase_event_callback,
                phase="approval_reject",
                title="승인 취소 처리 중",
                detail="승인 대기 중인 저장 작업을 취소하는 중입니다.",
                note="파일은 저장되지 않습니다.",
            )
            response = self._reject_pending_approval(request)
            self._append_response_message(request.session_id, response)
            self.task_logger.log(
                session_id=request.session_id,
                action="agent_response",
                detail=self._agent_response_log_detail(response),
            )
            return response

        self.session_store.append_message(request.session_id, {"role": "user", "text": request.user_text})
        requested_web_search_permission = self._extract_web_search_permission(request)
        existing_permissions = self.session_store.get_permissions(request.session_id)
        if existing_permissions.get("web_search") != requested_web_search_permission:
            self.session_store.set_permissions(
                request.session_id,
                {"web_search": requested_web_search_permission},
            )
            self.task_logger.log(
                session_id=request.session_id,
                action="permissions_updated",
                detail={"web_search": requested_web_search_permission},
            )

        try:
            search_query = self._extract_search_query(request)
            search_root = self._extract_search_root(request)
            uploaded_search_files = self._extract_uploaded_search_files(request)
            has_search_request = bool(search_query and (search_root or uploaded_search_files))
            active_context = self.session_store.get_active_context(request.session_id)
            has_explicit_source_path = self._has_explicit_source_path(request)
            source_path = self._extract_source_path(request)
            uploaded_file = self._extract_uploaded_file(request)
            search_intent = self._classify_search_intent(request.user_text)
            explicit_web_search_query = (
                search_intent.query if search_intent.kind == SearchIntentKind.EXPLICIT_WEB else None
            )
            explicit_web_search_effective_query = explicit_web_search_query
            explicit_web_search_probe_query: str | None = None
            explicit_web_search_intent_kind = search_intent.kind
            explicit_web_search_answer_mode = search_intent.answer_mode
            explicit_web_search_freshness_risk = search_intent.freshness_risk
            implicit_web_search_query = (
                search_intent.query
                if requested_web_search_permission == "enabled" and search_intent.kind == SearchIntentKind.LIVE_LATEST
                else None
            )
            external_fact_query = search_intent.query if search_intent.kind == SearchIntentKind.EXTERNAL_FACT else None
            retry_feedback_reason = self._extract_retry_feedback_reason(request)
            load_web_search_record_id = self._extract_load_web_search_record_id(request)
            wants_web_search_record_recall = self._looks_like_web_search_record_recall(request.user_text)
            follow_up_intent = self._detect_follow_up_intent(request.user_text) if request.user_text.strip() else FOLLOW_UP_INTENT_GENERAL
            active_context_mode = self._classify_active_context_request(
                request=request,
                active_context=active_context,
                has_search_request=has_search_request,
                has_explicit_source_path=has_explicit_source_path,
                uploaded_file=uploaded_file,
            )
            if explicit_web_search_query and self._should_treat_as_entity_reinvestigation(
                active_context=active_context,
                query=explicit_web_search_query,
            ):
                explicit_web_search_intent_kind = SearchIntentKind.EXTERNAL_FACT
                explicit_web_search_answer_mode = AnswerMode.ENTITY_CARD
                explicit_web_search_freshness_risk = FreshnessRisk.LOW
                explicit_web_search_probe_query = explicit_web_search_query
                explicit_web_search_effective_query = (
                    self._extract_web_search_query_from_context(active_context) or explicit_web_search_query
                )
            self.task_logger.log(
                session_id=request.session_id,
                action="request_intent_classified",
                detail={
                    "kind": search_intent.kind,
                    "query": search_intent.query,
                    "score": search_intent.score,
                    "reasons": list(search_intent.reasons),
                    "freshness_risk": search_intent.freshness_risk,
                    "answer_mode": search_intent.answer_mode,
                    "suggestion_kind": search_intent.suggestion_kind,
                    "suggestion_query": search_intent.suggestion_query,
                    "suggestion_score": search_intent.suggestion_score,
                    "suggestion_reasons": list(search_intent.suggestion_reasons),
                    "suggestion_freshness_risk": search_intent.suggestion_freshness_risk,
                    "suggestion_answer_mode": search_intent.suggestion_answer_mode,
                },
            )

            if (
                retry_feedback_reason in {"irrelevant_result", "factual_error"}
                and active_context is not None
                and not has_search_request
                and uploaded_file is None
                and not has_explicit_source_path
            ):
                retry_response = self._retry_web_search_after_irrelevant_feedback(
                    request=request,
                    active_context=active_context,
                    retry_feedback_reason=retry_feedback_reason,
                    phase_event_callback=phase_event_callback,
                )
                if retry_response is not None:
                    response = retry_response
                else:
                    response = None
            else:
                response = None

            if response is not None:
                pass
            elif (
                (wants_web_search_record_recall or load_web_search_record_id)
                and not has_search_request
                and uploaded_file is None
                and not has_explicit_source_path
            ):
                response = self._reuse_web_search_record(
                    request=request,
                    record_id=load_web_search_record_id,
                    phase_event_callback=phase_event_callback,
                    stream_event_callback=stream_event_callback,
                    cancel_requested=cancel_requested,
                )
            elif (
                search_intent.kind == SearchIntentKind.NONE
                and search_intent.suggestion_query
                and active_context_mode not in {"document", "mixed"}
                and not has_search_request
                and uploaded_file is None
                and not has_explicit_source_path
            ):
                self._emit_phase(
                    phase_event_callback,
                    phase="web_search_suggestion",
                    title="검색 제안 준비 중",
                    detail=f"'{search_intent.suggestion_query}' 쪽으로 검색하면 도움이 될 수 있어 제안 버튼을 준비하는 중입니다.",
                    note="확신이 낮은 질문은 자동 검색 대신 명시적 제안으로 먼저 보여드립니다.",
                )
                response = self._build_web_search_suggestion_response(
                    requested_web_search_permission,
                    query=search_intent.suggestion_query,
                )
            elif (
                explicit_web_search_query
                and not has_search_request
                and uploaded_file is None
                and not has_explicit_source_path
            ):
                if requested_web_search_permission != "enabled":
                    self._emit_phase(
                        phase_event_callback,
                        phase="web_search_blocked",
                        title="웹 검색 권한 확인 중",
                        detail="명시적으로 웹 검색을 요청했지만 현재 세션 권한으로는 바로 실행할 수 없습니다.",
                        note="고급 설정의 외부 웹 검색 권한을 확인해 주세요.",
                    )
                    response = self._build_web_search_permission_response(
                        requested_web_search_permission,
                        query=explicit_web_search_query,
                    )
                else:
                    response = self._run_web_search(
                        request=request,
                        query=explicit_web_search_effective_query or explicit_web_search_query,
                        intent_kind=explicit_web_search_intent_kind,
                        answer_mode=explicit_web_search_answer_mode,
                        freshness_risk=explicit_web_search_freshness_risk,
                        phase_event_callback=phase_event_callback,
                        seed_queries=[explicit_web_search_probe_query] if explicit_web_search_probe_query else None,
                        progress_query=explicit_web_search_probe_query,
                    )
            elif (
                external_fact_query
                and active_context_mode not in {"document", "mixed"}
                and not has_search_request
                and uploaded_file is None
                and not has_explicit_source_path
            ):
                if requested_web_search_permission != "enabled":
                    self._emit_phase(
                        phase_event_callback,
                        phase="web_search_blocked",
                        title="외부 사실 확인 경로 안내 중",
                        detail="외부 사실 설명 요청이지만 현재 세션 권한으로는 읽기 전용 웹 검색을 바로 실행할 수 없습니다.",
                        note="고급 설정에서 외부 웹 검색 권한을 허용으로 바꾸면 검색 기반으로 답할 수 있습니다.",
                    )
                    response = self._build_web_search_permission_response(
                        requested_web_search_permission,
                        query=external_fact_query,
                    )
                else:
                    self._emit_phase(
                        phase_event_callback,
                        phase="web_search_auto",
                        title="외부 사실 확인 검색으로 전환 중",
                        detail=f"'{external_fact_query}' 설명 요청이어서 웹 검색으로 근거를 먼저 확인하는 중입니다.",
                        note="로컬 문서 근거가 없을 때는 외부 사실을 모델이 추측하지 않도록 읽기 전용 검색을 우선 사용합니다.",
                    )
                    response = self._run_web_search(
                        request=request,
                        query=external_fact_query,
                        intent_kind=search_intent.kind,
                        answer_mode=search_intent.answer_mode,
                        freshness_risk=search_intent.freshness_risk,
                        phase_event_callback=phase_event_callback,
                    )
            elif (
                implicit_web_search_query
                and active_context_mode not in {"document", "mixed"}
                and not has_search_request
                and uploaded_file is None
                and not has_explicit_source_path
            ):
                self._emit_phase(
                    phase_event_callback,
                    phase="web_search_auto",
                    title="최신 정보 질문을 웹 검색으로 전환 중",
                    detail=f"'{implicit_web_search_query}' 관련 최신성 질문이라 읽기 전용 웹 검색을 먼저 실행합니다.",
                    note="웹 검색 권한이 허용된 세션에서만 자동으로 전환합니다.",
                )
                response = self._run_web_search(
                    request=request,
                    query=implicit_web_search_query,
                    intent_kind=search_intent.kind,
                    answer_mode=search_intent.answer_mode,
                    freshness_risk=search_intent.freshness_risk,
                    phase_event_callback=phase_event_callback,
                )
            elif active_context_mode in {"document", "mixed"}:
                if active_context_mode == "mixed":
                    detail = (
                        f"현재 문서 '{active_context.get('label') or '문서'}'를 바탕으로 "
                        "가벼운 인사와 문서 질문을 함께 정리하는 중입니다."
                    )
                    note = "짧은 대화 톤은 유지하되, 답변 본문은 현재 문서 근거를 우선 사용합니다."
                else:
                    detail = (
                        f"현재 문서 '{active_context.get('label') or '문서'}' 문맥으로 "
                        "후속 질문을 정리하는 중입니다."
                    )
                    note = "문서 요약과 핵심 라인을 바탕으로 응답을 만듭니다."
                self._emit_phase(
                    phase_event_callback,
                    phase="context_answer_started",
                    title="문서 문맥 응답 준비 중",
                    detail=detail,
                    note=note,
                )
                response = self._respond_with_active_context(
                    request=request,
                    active_context=active_context,
                    conversation_mode=active_context_mode,
                    stream_event_callback=stream_event_callback,
                    phase_event_callback=phase_event_callback,
                    cancel_requested=cancel_requested,
                )
            elif (
                not active_context
                and follow_up_intent != FOLLOW_UP_INTENT_GENERAL
                and uploaded_file is None
                and not has_explicit_source_path
                and not has_search_request
            ):
                if self._contains_small_talk_signal(request.user_text):
                    prefix = self._small_talk_prefix(request.user_text)
                    text = (
                        f"{prefix} 다만 아직 참고할 현재 문서 문맥이 없습니다. "
                        "파일 요약 모드에서 문서를 먼저 읽거나 파일 경로를 직접 입력해 주세요."
                    )
                else:
                    text = "현재 문서 문맥이 없습니다. 파일 요약 모드에서 문서를 먼저 읽거나 파일 경로를 직접 입력해 주세요."
                response = AgentResponse(
                    text=text,
                    status=ResponseStatus.ERROR,
                    actions_taken=["missing_active_context"],
                )
            elif search_query and (search_root or uploaded_search_files) and "read_file" in self.tools:
                search_target_label = search_root or self._format_uploaded_search_root_label(uploaded_search_files)
                search_action_name = "search_uploaded_files" if uploaded_search_files else "search_files"
                self._raise_if_cancelled(cancel_requested)
                self._emit_phase(
                    phase_event_callback,
                    phase="search_started",
                    title="문서 검색 중",
                    detail=(
                        f"'{search_query}' 검색어로 {search_target_label} 아래 문서를 찾는 중입니다."
                        if search_root
                        else f"선택한 폴더 파일들에서 '{search_query}' 검색어를 찾는 중입니다."
                    ),
                    note="검색 결과 수와 OCR 미지원 파일 여부를 먼저 확인합니다.",
                )
                uploaded_read_results_by_path: dict[str, Any] = {}
                skipped_ocr_paths: list[str] = []
                failed_uploaded_paths: list[str] = []
                if uploaded_search_files:
                    matches, uploaded_read_results_by_path, skipped_ocr_paths, failed_uploaded_paths = self._search_uploaded_files(
                        uploaded_files=uploaded_search_files,
                        query=search_query,
                        max_results=self._search_result_limit(request),
                    )
                else:
                    matches = self.tools["search_files"].run(
                        root=search_root,
                        query=search_query,
                        max_results=self._search_result_limit(request),
                    )
                    skipped_ocr_paths = self._extract_skipped_ocr_paths()
                self._raise_if_cancelled(cancel_requested)
                self.task_logger.log(
                    session_id=request.session_id,
                    action=search_action_name,
                    detail={
                        "search_root": search_root,
                        "uploaded_root_label": uploaded_search_files[0].get("root_label") if uploaded_search_files else None,
                        "search_query": search_query,
                        "match_count": len(matches),
                        "skipped_ocr_paths": skipped_ocr_paths,
                        "failed_uploaded_paths": failed_uploaded_paths,
                        "matches": [
                            {
                                "path": item.path,
                                "matched_on": item.matched_on,
                                "snippet": item.snippet,
                            }
                            for item in matches
                        ],
                    },
                )
                search_notice = self._format_search_ocr_notice(skipped_ocr_paths)
                if failed_uploaded_paths:
                    failed_notice = f"일부 파일({len(failed_uploaded_paths)}건)을 읽지 못해 검색에서 제외되었습니다."
                    search_notice = f"{search_notice}\n{failed_notice}".strip() if search_notice else failed_notice

                if not matches:
                    response = AgentResponse(
                        text=self._append_notice(
                            f"{search_target_label} 아래에서 '{search_query}' 검색 결과를 찾지 못했습니다.",
                            search_notice,
                        ),
                        actions_taken=[search_action_name],
                    )
                elif self._wants_search_only(request):
                    response = AgentResponse(
                        text=self._append_notice(self._format_search_results(matches), search_notice),
                        actions_taken=[search_action_name],
                        selected_source_paths=[item.path for item in matches],
                        search_results=[
                            {"path": item.path, "matched_on": item.matched_on, "snippet": item.snippet}
                            for item in matches
                        ],
                    )
                else:
                    self._emit_phase(
                        phase_event_callback,
                        phase="search_results_selected",
                        title="검색 결과 정리 중",
                        detail=f"검색 결과 {len(matches)}개 중 요약할 출처를 고르는 중입니다.",
                        note="선택 경로나 검색 순번이 있으면 그 기준으로 추립니다.",
                    )
                    selected_results = self._select_search_results(results=matches, request=request)
                    self._raise_if_cancelled(cancel_requested)
                    self._emit_phase(
                        phase_event_callback,
                        phase="read_sources_started",
                        title="선택 문서 읽는 중",
                        detail=f"선택된 문서 {len(selected_results)}개를 열어 요약 준비를 하는 중입니다.",
                        note="PDF나 큰 문서는 여기서 시간이 조금 걸릴 수 있습니다.",
                    )
                    read_results = []
                    for result in selected_results:
                        self._raise_if_cancelled(cancel_requested)
                        if uploaded_search_files:
                            read_result = uploaded_read_results_by_path.get(result.path)
                            if read_result is None:
                                raise FileNotFoundError(f"선택한 폴더 검색 결과를 다시 찾지 못했습니다: {result.path}")
                            read_results.append(read_result)
                        else:
                            read_results.append(self.tools["read_file"].run(path=result.path))
                    self._raise_if_cancelled(cancel_requested)

                    self.task_logger.log(
                        session_id=request.session_id,
                        action="read_search_results",
                        detail={
                            "search_query": search_query,
                            "selected_match_count": len(selected_results),
                            "selected_paths": [item.resolved_path for item in read_results],
                            "selected_file_metadata": [
                                {
                                    "resolved_path": item.resolved_path,
                                    "content_format": item.content_format,
                                    "extraction_method": item.extraction_method,
                                    "encoding_used": item.encoding_used,
                                }
                                for item in read_results
                            ],
                        },
                    )

                    self._emit_phase(
                        phase_event_callback,
                        phase="summarize_started",
                        title="검색 결과 요약 생성 중",
                        detail=f"선택된 문서 {len(read_results)}개를 묶어 하나의 요약으로 정리하는 중입니다.",
                        note="실제 로컬 모델 응답은 이 단계부터 조금씩 도착할 수 있습니다.",
                    )
                    summary, note_body, summary_chunks = self._build_multi_file_summary(
                        search_query=search_query,
                        selected_results=selected_results,
                        read_results=read_results,
                        stream_event_callback=stream_event_callback,
                        phase_event_callback=phase_event_callback,
                        cancel_requested=cancel_requested,
                    )
                    self._raise_if_cancelled(cancel_requested)
                    new_active_context = self._build_search_active_context(
                        search_query=search_query,
                        selected_results=selected_results,
                        read_results=read_results,
                        summary=summary,
                    )
                    self.session_store.set_active_context(request.session_id, new_active_context)
                    self.task_logger.log(
                        session_id=request.session_id,
                        action="document_context_updated",
                        detail={
                            "kind": new_active_context["kind"],
                            "label": new_active_context["label"],
                            "source_paths": new_active_context["source_paths"],
                        },
                    )
                    selected_sources_text = self._format_selected_sources(selected_results)
                    self.task_logger.log(
                        session_id=request.session_id,
                        action="summarize_search_results",
                        detail={
                            "search_query": search_query,
                            "source_count": len(read_results),
                        },
                    )
                    selected_evidence = self._select_evidence_items(
                        evidence_pool=[
                            dict(item)
                            for item in new_active_context.get("evidence_pool", [])
                            if isinstance(item, dict)
                        ],
                        intent=FOLLOW_UP_INTENT_GENERAL,
                        user_request=request.user_text or search_query,
                    )
                    artifact_id = self._new_grounded_brief_artifact_id()
                    source_message_id = self._new_message_id()

                    if self._wants_summary_save(request) and "write_note" in self.tools:
                        note_path = self._build_search_note_path(request, search_query)
                        if not request.approved:
                            self._emit_phase(
                                phase_event_callback,
                                phase="approval_prepared",
                                title="저장 승인 카드 준비 중",
                                detail=f"검색 요약 노트를 {note_path}에 저장할 수 있도록 승인 미리보기를 만드는 중입니다.",
                                note="승인 전에는 실제 파일을 쓰지 않습니다.",
                            )
                            approval = self._request_save_note_approval(
                                session_id=request.session_id,
                                note_path=note_path,
                                note_body=note_body,
                                source_paths=[item.path for item in selected_results],
                                artifact_id=artifact_id,
                                source_message_id=source_message_id,
                                approval_request_detail={
                                    "search_query": search_query,
                                    "source_paths": [item.resolved_path for item in read_results],
                                },
                            )
                            response = self._build_grounded_brief_response(
                                text=self._append_notice(
                                    (
                                        f"{summary}\n\n{selected_sources_text}\n\n"
                                        f"검색 요약 노트를 {approval.requested_path}에 저장하려면 승인이 필요합니다."
                                    ),
                                    search_notice,
                                ),
                                status=ResponseStatus.NEEDS_APPROVAL,
                                actions_taken=[
                                    "search_uploaded_files" if uploaded_search_files else "search_files",
                                    "read_file",
                                    "summarize_search_results",
                                    "approval_requested",
                                ],
                                requires_approval=True,
                                proposed_note_path=approval.requested_path,
                                selected_source_paths=[item.path for item in selected_results],
                                note_preview=approval.preview_markdown,
                                approval=approval.to_public_dict(),
                                active_context=self._public_active_context(new_active_context),
                                follow_up_suggestions=[str(prompt) for prompt in new_active_context["suggested_prompts"]],
                                evidence=selected_evidence,
                                summary_chunks=summary_chunks,
                                search_results=[
                                    {"path": item.path, "matched_on": item.matched_on, "snippet": item.snippet}
                                    for item in matches
                                ],
                                **self._build_grounded_brief_source_response_fields(
                                    artifact_id=artifact_id,
                                    source_message_id=source_message_id,
                                ),
                            )
                        else:
                            self._emit_phase(
                                phase_event_callback,
                                phase="write_started",
                                title="검색 요약 노트 저장 중",
                                detail=f"{note_path} 경로에 검색 요약 노트를 쓰는 중입니다.",
                                note="승인된 경로에만 새 파일을 만듭니다.",
                            )
                            saved_path, _ = self._execute_save_note_write(
                                session_id=request.session_id,
                                note_path=note_path,
                                note_body=note_body,
                                artifact_id=artifact_id,
                                source_message_id=source_message_id,
                                write_detail={"search_query": search_query},
                            )
                            corrected_outcome = self._build_accepted_as_is_outcome(
                                artifact_id=artifact_id,
                                saved_note_path=saved_path,
                            )
                            response = self._build_grounded_brief_response(
                                text=self._append_notice(
                                    (
                                        f"{summary}\n\n{selected_sources_text}\n\n"
                                        f"검색 요약 노트를 {saved_path}에 저장했습니다."
                                    ),
                                    search_notice,
                                ),
                                status=ResponseStatus.SAVED,
                                actions_taken=[
                                    "search_uploaded_files" if uploaded_search_files else "search_files",
                                    "read_file",
                                    "summarize_search_results",
                                    "write_note",
                                ],
                                selected_source_paths=[item.path for item in selected_results],
                                active_context=self._public_active_context(new_active_context),
                                follow_up_suggestions=[str(prompt) for prompt in new_active_context["suggested_prompts"]],
                                evidence=selected_evidence,
                                summary_chunks=summary_chunks,
                                search_results=[
                                    {"path": item.path, "matched_on": item.matched_on, "snippet": item.snippet}
                                    for item in matches
                                ],
                                **self._build_grounded_brief_source_response_fields(
                                    artifact_id=artifact_id,
                                    source_message_id=source_message_id,
                                    saved_note_path=saved_path,
                                    save_content_source=SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT,
                                    corrected_outcome=corrected_outcome,
                                ),
                            )
                    else:
                        response = self._build_grounded_brief_response(
                            text=self._append_notice(
                                f"{summary}\n\n{selected_sources_text}",
                                search_notice,
                            ),
                            status=ResponseStatus.ANSWER,
                            actions_taken=["search_uploaded_files", "read_file", "summarize_search_results"] if uploaded_search_files else ["search_files", "read_file", "summarize_search_results"],
                            selected_source_paths=[item.path for item in selected_results],
                            active_context=self._public_active_context(new_active_context),
                            follow_up_suggestions=[str(prompt) for prompt in new_active_context["suggested_prompts"]],
                            evidence=selected_evidence,
                            summary_chunks=summary_chunks,
                            search_results=[
                                {"path": item.path, "matched_on": item.matched_on, "snippet": item.snippet}
                                for item in matches
                            ],
                            artifact_id=artifact_id,
                            artifact_kind=ArtifactKind.GROUNDED_BRIEF,
                        )
            elif uploaded_file and "read_file" in self.tools:
                uploaded_name = str(uploaded_file.get("name") or "selected-file")
                self._raise_if_cancelled(cancel_requested)
                self._emit_phase(
                    phase_event_callback,
                    phase="read_uploaded_file_started",
                    title="선택 파일 읽는 중",
                    detail=f"{uploaded_name} 선택 파일을 브라우저에서 받아 텍스트를 추출하는 중입니다.",
                    note="사용자가 직접 고른 파일만 로컬 서버로 전달합니다.",
                )
                read_result = self.tools["read_file"].run_uploaded(
                    name=uploaded_name,
                    content_bytes=bytes(uploaded_file.get("content_bytes") or b""),
                    mime_type=str(uploaded_file.get("mime_type") or ""),
                )
                self._raise_if_cancelled(cancel_requested)
                self.task_logger.log(
                    session_id=request.session_id,
                    action="read_uploaded_file",
                    detail={
                        "requested_name": uploaded_name,
                        "resolved_path": read_result.resolved_path,
                        "size_bytes": read_result.size_bytes,
                        "content_format": read_result.content_format,
                        "extraction_method": read_result.extraction_method,
                        "encoding_used": read_result.encoding_used,
                    },
                )

                self._emit_phase(
                    phase_event_callback,
                    phase="summarize_started",
                    title="문서 요약 생성 중",
                    detail=f"{Path(read_result.resolved_path).name} 내용을 요약하는 중입니다.",
                    note="실제 로컬 모델 응답은 이 단계부터 조금씩 도착할 수 있습니다.",
                )
                summary, summary_chunks = self._summarize_text_with_chunking(
                    text=read_result.text,
                    source_label=Path(read_result.resolved_path).name,
                    source_path=read_result.resolved_path,
                    stream_event_callback=stream_event_callback,
                    phase_event_callback=phase_event_callback,
                    cancel_requested=cancel_requested,
                )
                self._raise_if_cancelled(cancel_requested)
                title = f"{Path(read_result.resolved_path).name} 요약"
                note_body = "\n".join(
                    [
                        f"# {title}",
                        "",
                        f"원본 파일: {read_result.resolved_path}",
                        "",
                        "## 요약",
                        summary,
                    ]
                )
                note_draft = SummaryNoteDraft(title=title, summary=summary, note_body=note_body)
                new_active_context = self._build_file_active_context(
                    resolved_path=read_result.resolved_path,
                    text=read_result.text,
                    summary=note_draft.summary,
                )
                self.session_store.set_active_context(request.session_id, new_active_context)
                self.task_logger.log(
                    session_id=request.session_id,
                    action="document_context_updated",
                    detail={
                        "kind": new_active_context["kind"],
                        "label": new_active_context["label"],
                        "source_paths": new_active_context["source_paths"],
                    },
                )
                self.task_logger.log(
                    session_id=request.session_id,
                    action="summarize_uploaded_file",
                    detail={
                        "source_name": read_result.resolved_path,
                        "title": note_draft.title,
                    },
                )
                document_evidence = self._select_evidence_items(
                    evidence_pool=self._extract_text_evidence_items(
                        source_path=read_result.resolved_path,
                        text=read_result.text,
                    ),
                    intent=FOLLOW_UP_INTENT_GENERAL,
                    user_request=request.user_text or read_result.resolved_path,
                )
                artifact_id = self._new_grounded_brief_artifact_id()
                source_message_id = self._new_message_id()

                if self._wants_summary_save(request) and "write_note" in self.tools:
                    note_path = self._build_note_path(request, read_result.resolved_path)
                    if not request.approved:
                        self._emit_phase(
                            phase_event_callback,
                            phase="approval_prepared",
                            title="저장 승인 카드 준비 중",
                            detail=f"요약 노트를 {note_path}에 저장할 수 있도록 승인 미리보기를 만드는 중입니다.",
                            note="승인 전에는 실제 파일을 쓰지 않습니다.",
                        )
                        approval = self._request_save_note_approval(
                            session_id=request.session_id,
                            note_path=note_path,
                            note_body=note_draft.note_body,
                            source_paths=[read_result.resolved_path],
                            artifact_id=artifact_id,
                            source_message_id=source_message_id,
                            approval_request_detail={"source_path": read_result.resolved_path},
                        )
                        response = self._build_grounded_brief_response(
                            text=(
                                f"{note_draft.summary}\n\n"
                                f"요약 노트를 {approval.requested_path}에 저장하려면 승인이 필요합니다."
                            ),
                            status=ResponseStatus.NEEDS_APPROVAL,
                            actions_taken=["read_uploaded_file", "summarize", "approval_requested"],
                            requires_approval=True,
                            proposed_note_path=approval.requested_path,
                            selected_source_paths=[read_result.resolved_path],
                            note_preview=approval.preview_markdown,
                            approval=approval.to_public_dict(),
                            active_context=self._public_active_context(new_active_context),
                            follow_up_suggestions=[str(prompt) for prompt in new_active_context["suggested_prompts"]],
                            evidence=document_evidence,
                            summary_chunks=summary_chunks,
                            **self._build_grounded_brief_source_response_fields(
                                artifact_id=artifact_id,
                                source_message_id=source_message_id,
                            ),
                        )
                    else:
                        self._emit_phase(
                            phase_event_callback,
                            phase="write_started",
                            title="요약 노트 저장 중",
                            detail=f"{note_path} 경로에 요약 노트를 쓰는 중입니다.",
                            note="승인된 경로에만 새 파일을 만듭니다.",
                        )
                        saved_path, _ = self._execute_save_note_write(
                            session_id=request.session_id,
                            note_path=note_path,
                            note_body=note_draft.note_body,
                            artifact_id=artifact_id,
                            source_message_id=source_message_id,
                            write_detail={"source_path": read_result.resolved_path},
                        )
                        corrected_outcome = self._build_accepted_as_is_outcome(
                            artifact_id=artifact_id,
                            saved_note_path=saved_path,
                        )
                        response = self._build_grounded_brief_response(
                            text=f"{note_draft.summary}\n\n요약 노트를 {saved_path}에 저장했습니다.",
                            status=ResponseStatus.SAVED,
                            actions_taken=["read_uploaded_file", "summarize", "write_note"],
                            selected_source_paths=[read_result.resolved_path],
                            active_context=self._public_active_context(new_active_context),
                            follow_up_suggestions=[str(prompt) for prompt in new_active_context["suggested_prompts"]],
                            evidence=document_evidence,
                            summary_chunks=summary_chunks,
                            **self._build_grounded_brief_source_response_fields(
                                artifact_id=artifact_id,
                                source_message_id=source_message_id,
                                saved_note_path=saved_path,
                                save_content_source=SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT,
                                corrected_outcome=corrected_outcome,
                            ),
                        )
                else:
                    response = self._build_grounded_brief_response(
                        text=note_draft.summary,
                        status=ResponseStatus.ANSWER,
                        actions_taken=["read_uploaded_file", "summarize"],
                        selected_source_paths=[read_result.resolved_path],
                        active_context=self._public_active_context(new_active_context),
                        follow_up_suggestions=[str(prompt) for prompt in new_active_context["suggested_prompts"]],
                        evidence=document_evidence,
                        summary_chunks=summary_chunks,
                        artifact_id=artifact_id,
                        artifact_kind=ArtifactKind.GROUNDED_BRIEF,
                    )
            elif source_path and "read_file" in self.tools:
                self._raise_if_cancelled(cancel_requested)
                self._emit_phase(
                    phase_event_callback,
                    phase="read_file_started",
                    title="파일 읽는 중",
                    detail=f"{source_path} 파일을 열어 텍스트를 추출하는 중입니다.",
                    note="PDF나 인코딩 자동 판별이 필요한 문서는 시간이 더 걸릴 수 있습니다.",
                )
                read_result = self.tools["read_file"].run(path=source_path)
                self._raise_if_cancelled(cancel_requested)
                self.task_logger.log(
                    session_id=request.session_id,
                    action="read_file",
                    detail={
                        "requested_path": read_result.requested_path,
                        "resolved_path": read_result.resolved_path,
                        "size_bytes": read_result.size_bytes,
                        "content_format": read_result.content_format,
                        "extraction_method": read_result.extraction_method,
                        "encoding_used": read_result.encoding_used,
                    },
                )

                self._emit_phase(
                    phase_event_callback,
                    phase="summarize_started",
                    title="문서 요약 생성 중",
                    detail=f"{Path(read_result.resolved_path).name} 내용을 요약하는 중입니다.",
                    note="실제 로컬 모델 응답은 이 단계부터 조금씩 도착할 수 있습니다.",
                )
                summary, summary_chunks = self._summarize_text_with_chunking(
                    text=read_result.text,
                    source_label=Path(read_result.resolved_path).name,
                    source_path=read_result.resolved_path,
                    stream_event_callback=stream_event_callback,
                    phase_event_callback=phase_event_callback,
                    cancel_requested=cancel_requested,
                )
                self._raise_if_cancelled(cancel_requested)
                title = f"{Path(read_result.resolved_path).name} 요약"
                note_body = "\n".join(
                    [
                        f"# {title}",
                        "",
                        f"원본 파일: {read_result.resolved_path}",
                        "",
                        "## 요약",
                        summary,
                    ]
                )
                note_draft = SummaryNoteDraft(title=title, summary=summary, note_body=note_body)
                new_active_context = self._build_file_active_context(
                    resolved_path=read_result.resolved_path,
                    text=read_result.text,
                    summary=note_draft.summary,
                )
                self.session_store.set_active_context(request.session_id, new_active_context)
                self.task_logger.log(
                    session_id=request.session_id,
                    action="document_context_updated",
                    detail={
                        "kind": new_active_context["kind"],
                        "label": new_active_context["label"],
                        "source_paths": new_active_context["source_paths"],
                    },
                )
                self.task_logger.log(
                    session_id=request.session_id,
                    action="summarize_file",
                    detail={
                        "source_path": read_result.resolved_path,
                        "title": note_draft.title,
                    },
                )
                document_evidence = self._select_evidence_items(
                    evidence_pool=self._extract_text_evidence_items(
                        source_path=read_result.resolved_path,
                        text=read_result.text,
                    ),
                    intent=FOLLOW_UP_INTENT_GENERAL,
                    user_request=request.user_text or read_result.resolved_path,
                )
                artifact_id = self._new_grounded_brief_artifact_id()
                source_message_id = self._new_message_id()

                if self._wants_summary_save(request) and "write_note" in self.tools:
                    note_path = self._build_note_path(request, read_result.resolved_path)
                    if not request.approved:
                        self._emit_phase(
                            phase_event_callback,
                            phase="approval_prepared",
                            title="저장 승인 카드 준비 중",
                            detail=f"요약 노트를 {note_path}에 저장할 수 있도록 승인 미리보기를 만드는 중입니다.",
                            note="승인 전에는 실제 파일을 쓰지 않습니다.",
                        )
                        approval = self._request_save_note_approval(
                            session_id=request.session_id,
                            note_path=note_path,
                            note_body=note_draft.note_body,
                            source_paths=[read_result.resolved_path],
                            artifact_id=artifact_id,
                            source_message_id=source_message_id,
                            approval_request_detail={"source_path": read_result.resolved_path},
                        )
                        response = self._build_grounded_brief_response(
                            text=(
                                f"{note_draft.summary}\n\n"
                                f"요약 노트를 {approval.requested_path}에 저장하려면 승인이 필요합니다."
                            ),
                            status=ResponseStatus.NEEDS_APPROVAL,
                            actions_taken=["read_file", "summarize", "approval_requested"],
                            requires_approval=True,
                            proposed_note_path=approval.requested_path,
                            selected_source_paths=[read_result.resolved_path],
                            note_preview=approval.preview_markdown,
                            approval=approval.to_public_dict(),
                            active_context=self._public_active_context(new_active_context),
                            follow_up_suggestions=[str(prompt) for prompt in new_active_context["suggested_prompts"]],
                            evidence=document_evidence,
                            summary_chunks=summary_chunks,
                            **self._build_grounded_brief_source_response_fields(
                                artifact_id=artifact_id,
                                source_message_id=source_message_id,
                            ),
                        )
                    else:
                        self._emit_phase(
                            phase_event_callback,
                            phase="write_started",
                            title="요약 노트 저장 중",
                            detail=f"{note_path} 경로에 요약 노트를 쓰는 중입니다.",
                            note="승인된 경로에만 새 파일을 만듭니다.",
                        )
                        saved_path, _ = self._execute_save_note_write(
                            session_id=request.session_id,
                            note_path=note_path,
                            note_body=note_draft.note_body,
                            artifact_id=artifact_id,
                            source_message_id=source_message_id,
                            write_detail={"source_path": read_result.resolved_path},
                        )
                        corrected_outcome = self._build_accepted_as_is_outcome(
                            artifact_id=artifact_id,
                            saved_note_path=saved_path,
                        )
                        response = self._build_grounded_brief_response(
                            text=f"{note_draft.summary}\n\n요약 노트를 {saved_path}에 저장했습니다.",
                            status=ResponseStatus.SAVED,
                            actions_taken=["read_file", "summarize", "write_note"],
                            selected_source_paths=[read_result.resolved_path],
                            active_context=self._public_active_context(new_active_context),
                            follow_up_suggestions=[str(prompt) for prompt in new_active_context["suggested_prompts"]],
                            evidence=document_evidence,
                            summary_chunks=summary_chunks,
                            **self._build_grounded_brief_source_response_fields(
                                artifact_id=artifact_id,
                                source_message_id=source_message_id,
                                saved_note_path=saved_path,
                                save_content_source=SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT,
                                corrected_outcome=corrected_outcome,
                            ),
                        )
                else:
                    response = self._build_grounded_brief_response(
                        text=note_draft.summary,
                        status=ResponseStatus.ANSWER,
                        actions_taken=["read_file", "summarize"],
                        selected_source_paths=[read_result.resolved_path],
                        active_context=self._public_active_context(new_active_context),
                        follow_up_suggestions=[str(prompt) for prompt in new_active_context["suggested_prompts"]],
                        evidence=document_evidence,
                        summary_chunks=summary_chunks,
                        artifact_id=artifact_id,
                        artifact_kind=ArtifactKind.GROUNDED_BRIEF,
                    )
            elif active_context_mode in {"document", "mixed"}:
                if active_context_mode == "mixed":
                    detail = (
                        f"현재 문서 '{active_context.get('label') or '문서'}'를 바탕으로 "
                        "가벼운 대화와 문서 답변을 함께 정리하는 중입니다."
                    )
                    note = "대화 톤은 유지하되, 답변 핵심은 현재 문서 근거로 제한합니다."
                else:
                    detail = f"현재 문서 '{active_context.get('label') or '문서'}'를 바탕으로 답변하는 중입니다."
                    note = "후속 질문 의도에 맞춰 요약이나 액션 항목 형식으로 정리합니다."
                self._emit_phase(
                    phase_event_callback,
                    phase="context_answer_started",
                    title="문서 문맥 응답 준비 중",
                    detail=detail,
                    note=note,
                )
                response = self._respond_with_active_context(
                    request=request,
                    active_context=active_context,
                    conversation_mode=active_context_mode,
                    stream_event_callback=stream_event_callback,
                    phase_event_callback=phase_event_callback,
                    cancel_requested=cancel_requested,
                )
            else:
                if self._looks_like_unverified_external_fact_request(request.user_text):
                    self._emit_phase(
                        phase_event_callback,
                        phase="respond_limited",
                        title="확인 범위 안내 중",
                        detail="외부 사실 확인이 필요한 질문이라 로컬 문서 근거 범위를 먼저 안내합니다.",
                        note="관련 문서나 텍스트를 주시면 그 범위에서 다시 정리할 수 있습니다.",
                    )
                    response = self._build_unverified_external_fact_response_for_permission(
                        self._extract_web_search_permission(request)
                    )
                elif self._looks_like_personal_experience_request(request.user_text):
                    self._emit_phase(
                        phase_event_callback,
                        phase="respond_limited",
                        title="경험 기반 질문 안내 중",
                        detail="직접 경험 여부를 묻는 질문이라 시스템 한계를 먼저 안내합니다.",
                        note="관련 텍스트나 문서를 주시면 그 범위에서 설명할 수 있습니다.",
                    )
                    response = self._build_personal_experience_response()
                elif self._looks_like_live_info_request(request.user_text):
                    self._emit_phase(
                        phase_event_callback,
                        phase="respond_limited",
                        title="실시간 정보 범위 안내 중",
                        detail="실시간 외부 조회가 필요한 질문이라 현재 연결 범위를 먼저 안내합니다.",
                        note="실시간 API나 관련 텍스트가 연결되면 그 범위에서 다시 정리할 수 있습니다.",
                    )
                    response = self._build_live_info_response_for_permission(
                        self._extract_web_search_permission(request)
                    )
                elif self._looks_like_underspecified_next_step_request(request.user_text):
                    self._emit_phase(
                        phase_event_callback,
                        phase="respond_limited",
                        title="맥락 확인 안내 중",
                        detail="다음 단계 질문이지만 어떤 흐름인지 아직 부족해서 맥락을 먼저 요청합니다.",
                        note="문서 요약, 검색, 메모 저장 중 어느 흐름인지 알려주시면 바로 이어집니다.",
                    )
                    response = self._build_underspecified_next_step_response()
                else:
                    self._emit_phase(
                        phase_event_callback,
                        phase="respond_started",
                        title="일반 응답 생성 중",
                        detail="일반 질문에 대한 응답을 생성하는 중입니다.",
                        note="선택된 문맥이 없으면 일반 대화 응답으로 처리합니다.",
                    )
                    response = AgentResponse(
                        text=self._collect_model_stream(
                            self.model.stream_respond(request.user_text),
                            stream_event_callback=stream_event_callback,
                            cancel_requested=cancel_requested,
                        ),
                        status=ResponseStatus.ANSWER,
                        actions_taken=["respond"],
                    )
        except RequestCancelledError:
            uploaded_file = self._extract_uploaded_file(request)
            self.task_logger.log(
                session_id=request.session_id,
                action="request_cancelled",
                detail={
                    "user_text": request.user_text,
                    "source_path": request.metadata.get("source_path"),
                    "uploaded_file_name": uploaded_file.get("name") if uploaded_file else None,
                    "search_root": request.metadata.get("search_root"),
                    "search_query": request.metadata.get("search_query"),
                },
            )
            raise
        except OcrRequiredError as exc:
            source_path = self._extract_source_path(request)
            uploaded_file = self._extract_uploaded_file(request)
            source_label = source_path or (uploaded_file.get("name") if uploaded_file else None)
            response = AgentResponse(
                text=self._format_ocr_guidance(source_label, str(exc)),
                status=ResponseStatus.ERROR,
                actions_taken=["ocr_not_supported"],
                selected_source_paths=[source_label] if source_label else [],
            )
            self.task_logger.log(
                session_id=request.session_id,
                action="ocr_not_supported",
                detail={
                    "source_path": source_label,
                    "error": str(exc),
                },
            )
        except Exception as exc:
            response = AgentResponse(
                text=f"요청을 완료하지 못했습니다: {exc}",
                status=ResponseStatus.ERROR,
                actions_taken=["error"],
            )
            self.task_logger.log(
                session_id=request.session_id,
                action="agent_error",
                detail={"error": str(exc)},
            )

        self._append_response_message(request.session_id, response)
        self.task_logger.log(
            session_id=request.session_id,
            action="agent_response",
            detail=self._agent_response_log_detail(response),
        )
        return response
