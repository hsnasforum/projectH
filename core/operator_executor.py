from __future__ import annotations

from pathlib import Path

from core.contracts import OperatorActionKind


def execute_operator_action(record: dict) -> dict:
    action_kind = str(record.get("action_kind") or "").strip()
    if action_kind != OperatorActionKind.LOCAL_FILE_EDIT:
        raise ValueError(f"Unsupported action kind: {action_kind!r}")
    target_id = str(record.get("target_id") or "").strip()
    if not target_id:
        raise ValueError("target_id is required for local_file_edit")
    path = Path(target_id)
    content = record.get("content")
    if content is not None:
        write_content = str(content)
        path.write_text(write_content, encoding="utf-8")
        bytes_written = len(write_content.encode("utf-8"))
        return {
            "preview": f"파일 쓰기 완료: {target_id} ({bytes_written}바이트)",
            "written": True,
            "action_kind": action_kind,
            "target_id": target_id,
        }
    if not path.exists():
        return {
            "preview": f"[파일 없음: {target_id}]",
            "action_kind": action_kind,
            "target_id": target_id,
        }
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {
        "preview": "\n".join(lines[:10]),
        "action_kind": action_kind,
        "target_id": target_id,
    }
