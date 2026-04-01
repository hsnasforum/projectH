from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.contracts import (
    ALLOWED_APPROVAL_REASON_LABELS,
    ALLOWED_SAVE_CONTENT_SOURCES,
    ArtifactKind,
    ApprovalKind,
    SaveContentSource,
)

# Re-export for backward compatibility with existing importers
SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT = SaveContentSource.ORIGINAL_DRAFT
SAVE_CONTENT_SOURCE_CORRECTED_TEXT = SaveContentSource.CORRECTED_TEXT


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_save_content_source(value: Any) -> str | None:
    normalized = str(value or "").strip().lower()
    if normalized in ALLOWED_SAVE_CONTENT_SOURCES:
        return normalized
    return None


def normalize_source_message_id(value: Any) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def default_save_content_source_for_approval_kind(kind: Any) -> str | None:
    normalized_kind = str(kind or "").strip().lower()
    if normalized_kind == ApprovalKind.SAVE_NOTE:
        return SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT
    return None


def normalize_approval_reason_record(
    record: Any,
    *,
    fallback_artifact_id: str | None = None,
    fallback_artifact_kind: str | None = None,
    fallback_source_message_id: str | None = None,
    fallback_approval_id: str | None = None,
) -> dict[str, Any] | None:
    if not isinstance(record, dict):
        return None

    reason_scope = str(record.get("reason_scope") or "").strip().lower()
    allowed_labels = ALLOWED_APPROVAL_REASON_LABELS.get(reason_scope)
    if not allowed_labels:
        return None

    reason_label = str(record.get("reason_label") or "").strip().lower()
    if reason_label not in allowed_labels:
        return None

    artifact_id = str(record.get("artifact_id") or fallback_artifact_id or "").strip()
    artifact_kind = str(record.get("artifact_kind") or fallback_artifact_kind or "").strip()
    source_message_id = str(record.get("source_message_id") or fallback_source_message_id or "").strip()
    approval_id = str(record.get("approval_id") or fallback_approval_id or "").strip()
    if not artifact_id or not artifact_kind or not source_message_id or not approval_id:
        return None

    normalized = {
        "reason_scope": reason_scope,
        "reason_label": reason_label,
        "recorded_at": str(record.get("recorded_at") or utc_now_iso()),
        "artifact_id": artifact_id,
        "artifact_kind": artifact_kind,
        "source_message_id": source_message_id,
        "approval_id": approval_id,
    }
    reason_note = str(record.get("reason_note") or "").strip()
    if reason_note:
        normalized["reason_note"] = reason_note
    return normalized


def build_approval_reason_record(
    *,
    reason_scope: str,
    reason_label: str,
    artifact_id: str,
    artifact_kind: str,
    source_message_id: str,
    approval_id: str,
    reason_note: str | None = None,
    recorded_at: str | None = None,
) -> dict[str, Any] | None:
    return normalize_approval_reason_record(
        {
            "reason_scope": reason_scope,
            "reason_label": reason_label,
            "reason_note": reason_note,
            "recorded_at": recorded_at,
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "source_message_id": source_message_id,
            "approval_id": approval_id,
        }
    )


@dataclass(slots=True)
class ApprovalRequest:
    approval_id: str
    kind: str
    requested_path: str
    overwrite: bool
    preview_markdown: str
    source_paths: list[str]
    created_at: str
    note_text: str
    artifact_id: str | None = None
    source_message_id: str | None = None
    save_content_source: str | None = None
    approval_reason_record: dict[str, Any] | None = None

    @classmethod
    def create_save_note(
        cls,
        *,
        requested_path: str,
        overwrite: bool,
        preview_markdown: str,
        source_paths: list[str],
        note_text: str,
        artifact_id: str | None = None,
        source_message_id: str | None = None,
        save_content_source: str | None = None,
        approval_reason_record: dict[str, Any] | None = None,
    ) -> "ApprovalRequest":
        normalized_source_message_id = normalize_source_message_id(source_message_id)
        return cls(
            approval_id=f"approval-{uuid4().hex[:12]}",
            kind="save_note",
            requested_path=requested_path,
            overwrite=overwrite,
            preview_markdown=preview_markdown,
            source_paths=source_paths,
            created_at=utc_now_iso(),
            note_text=note_text,
            artifact_id=artifact_id,
            source_message_id=normalized_source_message_id,
            save_content_source=normalize_save_content_source(save_content_source)
            or default_save_content_source_for_approval_kind("save_note"),
            approval_reason_record=normalize_approval_reason_record(
                approval_reason_record,
                fallback_artifact_id=artifact_id,
                fallback_artifact_kind=ArtifactKind.GROUNDED_BRIEF if artifact_id else None,
                fallback_source_message_id=normalized_source_message_id,
            ),
        )

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "ApprovalRequest":
        approval_id = str(record["approval_id"])
        artifact_id = str(record.get("artifact_id") or "").strip() or None
        source_message_id = normalize_source_message_id(record.get("source_message_id"))
        kind = str(record["kind"])
        return cls(
            approval_id=approval_id,
            kind=kind,
            requested_path=str(record["requested_path"]),
            overwrite=bool(record.get("overwrite", False)),
            preview_markdown=str(record.get("preview_markdown", "")),
            source_paths=[str(path) for path in record.get("source_paths", [])],
            created_at=str(record.get("created_at") or utc_now_iso()),
            note_text=str(record.get("note_text", "")),
            artifact_id=artifact_id,
            source_message_id=source_message_id,
            save_content_source=normalize_save_content_source(record.get("save_content_source"))
            or default_save_content_source_for_approval_kind(kind),
            approval_reason_record=normalize_approval_reason_record(
                record.get("approval_reason_record"),
                fallback_artifact_id=artifact_id,
                fallback_artifact_kind=ArtifactKind.GROUNDED_BRIEF if artifact_id else None,
                fallback_source_message_id=source_message_id,
                fallback_approval_id=approval_id,
            ),
        )

    def to_record(self) -> dict[str, Any]:
        record = self.to_public_dict()
        record["note_text"] = self.note_text
        return record

    def to_public_dict(self) -> dict[str, Any]:
        record = {
            "approval_id": self.approval_id,
            "kind": self.kind,
            "requested_path": self.requested_path,
            "overwrite": self.overwrite,
            "preview_markdown": self.preview_markdown,
            "source_paths": list(self.source_paths),
            "created_at": self.created_at,
        }
        if self.artifact_id:
            record["artifact_id"] = self.artifact_id
        if self.source_message_id:
            record["source_message_id"] = self.source_message_id
        if self.save_content_source:
            record["save_content_source"] = self.save_content_source
        if self.approval_reason_record:
            record["approval_reason_record"] = dict(self.approval_reason_record)
        return record
