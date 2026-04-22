from __future__ import annotations

from datetime import datetime
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
        is_reversible = bool(record.get("is_reversible"))
        backup_path: str | None = None
        if is_reversible and path.exists():
            backup_dir = Path("backup") / "operator"
            backup_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_name = f"{path.stem}_{ts}{path.suffix}"
            backup_file = backup_dir / backup_name
            backup_file.write_text(
                path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
            )
            backup_path = str(backup_file)
        path.write_text(write_content, encoding="utf-8")
        bytes_written = len(write_content.encode("utf-8"))
        result: dict = {
            "preview": f"파일 쓰기 완료: {target_id} ({bytes_written}바이트)",
            "written": True,
            "action_kind": action_kind,
            "target_id": target_id,
        }
        if backup_path is not None:
            result["backup_path"] = backup_path
        return result
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


def rollback_operator_action(record: dict) -> dict:
    action_kind = str(record.get("action_kind") or "").strip()
    if action_kind != OperatorActionKind.LOCAL_FILE_EDIT:
        raise ValueError(f"Rollback unsupported for action kind: {action_kind!r}")
    backup_path = str(record.get("backup_path") or "").strip()
    if not backup_path:
        raise ValueError("backup_path is required for rollback")
    target_id = str(record.get("target_id") or "").strip()
    if not target_id:
        raise ValueError("target_id is required for rollback")
    backup = Path(backup_path)
    if not backup.exists():
        return {
            "restored": False,
            "error": f"[백업 파일 없음: {backup_path}]",
            "action_kind": action_kind,
            "target_id": target_id,
        }
    original_content = backup.read_text(encoding="utf-8", errors="replace")
    Path(target_id).write_text(original_content, encoding="utf-8")
    return {
        "restored": True,
        "action_kind": action_kind,
        "target_id": target_id,
        "backup_path": backup_path,
    }
