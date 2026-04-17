from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
from collections import deque
from pathlib import Path
from typing import Any

CONTROL_SLOT_STATUSES: dict[str, str] = {
    "claude_handoff.md": "implement",
    "gemini_request.md": "request_open",
    "gemini_advice.md": "advice_ready",
    "operator_request.md": "needs_operator",
}

CONTROL_SLOT_LABELS: dict[str, str] = {
    "claude_handoff.md": "Claude 실행",
    "gemini_request.md": "Gemini 실행",
    "gemini_advice.md": "Codex follow-up",
    "operator_request.md": "operator 대기",
}

RUNTIME_LANE_ORDER = ("Claude", "Codex", "Gemini")
_CONTROL_HEADER_LINE_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]*):\s*(.*?)\s*$")
ROUND_NOTE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")


def iso_utc(ts: float | None = None) -> str:
    value = time.time() if ts is None else ts
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def read_jsonl_tail(path: Path, *, max_lines: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as handle:
            raw_lines = list(deque(handle, maxlen=max_lines))
    except OSError:
        return []
    records: list[dict[str, Any]] = []
    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            records.append(data)
    return records


def parse_iso_utc(value: str | None) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def repo_relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def latest_markdown(directory: Path) -> tuple[str, float]:
    best_path: Path | None = None
    best_mtime = 0.0
    if not directory.exists():
        return "—", 0.0
    for candidate in directory.rglob("*.md"):
        try:
            mtime = candidate.stat().st_mtime
        except OSError:
            continue
        if mtime > best_mtime:
            best_path = candidate
            best_mtime = mtime
    if best_path is None:
        return "—", 0.0
    try:
        rel = str(best_path.relative_to(directory))
    except ValueError:
        rel = best_path.name
    return rel, best_mtime


def latest_round_markdown(directory: Path) -> tuple[str, float]:
    best_path: Path | None = None
    best_mtime = 0.0
    if not directory.exists():
        return "—", 0.0
    for candidate in directory.rglob("*.md"):
        try:
            rel = candidate.relative_to(directory)
        except ValueError:
            continue
        if len(rel.parts) < 3 or not ROUND_NOTE_NAME_RE.match(candidate.name):
            continue
        try:
            mtime = candidate.stat().st_mtime
        except OSError:
            continue
        if mtime > best_mtime:
            best_path = candidate
            best_mtime = mtime
    if best_path is None:
        return "—", 0.0
    return str(best_path.relative_to(directory)), best_mtime


def read_control_meta(path: Path, *, max_lines: int = 20) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    meta: dict[str, Any] = {}
    for line in text.splitlines()[:max_lines]:
        match = _CONTROL_HEADER_LINE_RE.match(line)
        if not match:
            continue
        key = match.group(1).strip().lower()
        if key in meta:
            continue
        raw_value = match.group(2).strip()
        if key == "control_seq":
            try:
                parsed = int(raw_value)
            except ValueError:
                continue
            meta[key] = parsed if parsed >= 0 else None
            continue
        meta[key] = raw_value
    return meta


def _read_control_header(path: Path) -> tuple[str | None, int | None]:
    meta = read_control_meta(path, max_lines=12)
    status = str(meta.get("status") or "").strip() or None
    control_seq = meta.get("control_seq")
    if not isinstance(control_seq, int) or control_seq < 0:
        control_seq = None
    return status, control_seq


def parse_control_slots(pipeline_dir: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for filename, expected_status in CONTROL_SLOT_STATUSES.items():
        slot_path = pipeline_dir / filename
        if not slot_path.exists():
            continue
        try:
            mtime = slot_path.stat().st_mtime
        except OSError:
            continue
        status, control_seq = _read_control_header(slot_path)
        if status != expected_status:
            continue
        entries.append(
            {
                "file": filename,
                "status": status,
                "label": CONTROL_SLOT_LABELS[filename],
                "mtime": mtime,
                "control_seq": control_seq,
            }
        )
    if not entries:
        return {"active": None, "stale": []}
    entries.sort(
        key=lambda entry: (
            entry["control_seq"] is not None,
            entry["control_seq"] if entry["control_seq"] is not None else -1,
            entry["mtime"],
        ),
        reverse=True,
    )
    return {"active": entries[0], "stale": entries[1:]}


def load_job_states(
    state_dir: Path,
    *,
    run_id: str | None = None,
    legacy_not_before: float = 0.0,
) -> list[dict[str, Any]]:
    job_states: list[dict[str, Any]] = []
    if not state_dir.exists():
        return job_states
    for path in sorted(state_dir.glob("*.json")):
        if path.name == "turn_state.json":
            continue
        data = read_json(path)
        if not data:
            continue
        state_run_id = str(data.get("run_id") or "").strip()
        if run_id:
            if state_run_id:
                if state_run_id != run_id:
                    continue
            else:
                try:
                    state_mtime = path.stat().st_mtime
                except OSError:
                    state_mtime = 0.0
                updated_at = float(data.get("updated_at") or 0.0)
                if max(state_mtime, updated_at) < legacy_not_before:
                    continue
        data.setdefault("_path", str(path))
        job_states.append(data)
    return job_states


def latest_receipt(receipts_dir: Path) -> dict[str, Any] | None:
    best_entry: dict[str, Any] | None = None
    best_key: tuple[float, float, str] | None = None
    if not receipts_dir.exists():
        return None
    for path in receipts_dir.glob("*.json"):
        data = read_json(path)
        if not data:
            continue
        closed_at = str(data.get("closed_at") or "")
        try:
            closed_ts = dt.datetime.fromisoformat(closed_at.replace("Z", "+00:00")).timestamp() if closed_at else 0.0
        except ValueError:
            closed_ts = 0.0
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        key = (closed_ts, mtime, path.name)
        if best_key is None or key > best_key:
            best_key = key
            best_entry = data
    return best_entry
