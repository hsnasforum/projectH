from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.base import Tool
from tools.path_utils import normalize_local_path_input


class WriteNoteTool(Tool):
    name = "write_note"

    def __init__(self, *, allowed_roots: list[str] | None = None) -> None:
        self.allowed_roots = [
            normalize_local_path_input(root).resolve()
            for root in (allowed_roots or [])
        ]

    def inspect_target(self, *, path: str) -> dict[str, Any]:
        requested_path = normalize_local_path_input(path)
        resolved_path = requested_path.resolve()
        self._ensure_allowed(resolved_path)
        return {
            "requested_path": str(requested_path),
            "resolved_path": str(resolved_path),
            "overwrite": resolved_path.exists(),
        }

    def run(self, *, path: str, text: str, approved: bool = False, allow_overwrite: bool = False) -> str:
        if not approved:
            raise PermissionError("Explicit approval is required before writing a note.")

        output_path = normalize_local_path_input(path).resolve()
        self._ensure_allowed(output_path)
        if output_path.exists() and not allow_overwrite:
            raise FileExistsError("Refusing to overwrite an existing file by default.")
        if output_path.suffix == "":
            raise IsADirectoryError("A file path with an extension is required for note output.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        return str(output_path)

    def _ensure_allowed(self, path: Path) -> None:
        if not self.allowed_roots:
            return
        for root in self.allowed_roots:
            try:
                path.relative_to(root)
                return
            except ValueError:
                continue
        raise PermissionError(f"Refusing to write outside approved roots: {path}")
