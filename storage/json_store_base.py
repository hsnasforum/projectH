"""Shared helpers for JSON file-based stores.

All JSON stores (artifact, correction, preference, session) share the same
pattern: base_dir, _path, _now, _atomic_write, _read.  This module provides
a single implementation so the per-store files don't each carry a copy.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    """UTC ISO 8601 timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def safe_id(raw_id: str) -> str:
    """Sanitise an identifier for use as a filename component."""
    return raw_id.replace("/", "-").replace("\\", "-").strip()


def json_path(base_dir: Path, item_id: str, *, sanitise: bool = True) -> Path:
    """Return the JSON file path for *item_id* under *base_dir*."""
    name = safe_id(item_id) if sanitise else item_id
    return base_dir / f"{name}.json"


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    """Write *data* as JSON to *path* via atomic rename."""
    temp_path = path.with_name(f"{path.name}.{uuid4().hex[:8]}.tmp")
    encoded = json.dumps(data, ensure_ascii=False, indent=2)
    try:
        temp_path.write_text(encoded, encoding="utf-8")
        temp_path.replace(path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def read_json(path: Path) -> dict[str, Any] | None:
    """Read and parse a JSON file, returning *None* on any error."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (JSONDecodeError, OSError):
        return None


def scan_json_dir(base_dir: Path) -> list[dict[str, Any]]:
    """Read all ``*.json`` files under *base_dir* and return a list of parsed dicts."""
    results: list[dict[str, Any]] = []
    if not base_dir.exists():
        return results
    for path in sorted(base_dir.glob("*.json")):
        data = read_json(path)
        if data is not None:
            results.append(data)
    return results
