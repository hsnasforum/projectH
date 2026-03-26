from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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

    @classmethod
    def create_save_note(
        cls,
        *,
        requested_path: str,
        overwrite: bool,
        preview_markdown: str,
        source_paths: list[str],
        note_text: str,
    ) -> "ApprovalRequest":
        return cls(
            approval_id=f"approval-{uuid4().hex[:12]}",
            kind="save_note",
            requested_path=requested_path,
            overwrite=overwrite,
            preview_markdown=preview_markdown,
            source_paths=source_paths,
            created_at=utc_now_iso(),
            note_text=note_text,
        )

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "ApprovalRequest":
        return cls(
            approval_id=str(record["approval_id"]),
            kind=str(record["kind"]),
            requested_path=str(record["requested_path"]),
            overwrite=bool(record.get("overwrite", False)),
            preview_markdown=str(record.get("preview_markdown", "")),
            source_paths=[str(path) for path in record.get("source_paths", [])],
            created_at=str(record.get("created_at") or utc_now_iso()),
            note_text=str(record.get("note_text", "")),
        )

    def to_record(self) -> dict[str, Any]:
        record = self.to_public_dict()
        record["note_text"] = self.note_text
        return record

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "kind": self.kind,
            "requested_path": self.requested_path,
            "overwrite": self.overwrite,
            "preview_markdown": self.preview_markdown,
            "source_paths": list(self.source_paths),
            "created_at": self.created_at,
        }
