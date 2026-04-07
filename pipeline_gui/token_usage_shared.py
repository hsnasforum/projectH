"""Shared token usage readers for local and WSL launcher paths."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


def empty_summary(source: str = "") -> dict[str, object]:
    return {
        "available": False,
        "source": source,
        "session_tokens": 0,
        "today_tokens": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_tokens": 0,
        "reasoning_tokens": 0,
        "used_percent": None,
        "reset_at": "",
        "last_seen": 0.0,
    }


def parse_iso_date(raw: str) -> dt.date | None:
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def format_reset_time(raw: int | float | str | None) -> str:
    if raw in (None, "", 0):
        return ""
    try:
        ts = float(raw)
    except (TypeError, ValueError):
        return ""
    return dt.datetime.fromtimestamp(ts).strftime("%H:%M")


def extract_usage_metadata(obj: Any) -> list[dict[str, int]]:
    found: list[dict[str, int]] = []
    if isinstance(obj, dict):
        usage = obj.get("usageMetadata")
        if isinstance(usage, dict):
            found.append(
                {
                    "input_tokens": int(usage.get("promptTokenCount", 0) or 0),
                    "output_tokens": int(usage.get("candidatesTokenCount", 0) or 0),
                    "cached_tokens": int(usage.get("cachedContentTokenCount", 0) or 0),
                    "reasoning_tokens": int(usage.get("thoughtsTokenCount", 0) or 0),
                    "tool_tokens": int(usage.get("toolUsePromptTokenCount", 0) or 0),
                }
            )
        for value in obj.values():
            found.extend(extract_usage_metadata(value))
    elif isinstance(obj, list):
        for value in obj:
            found.extend(extract_usage_metadata(value))
    return found


def iter_jsonl_objects(path: Path):
    try:
        with path.open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def safe_iso_timestamp(raw: str) -> float:
    if not raw:
        return 0.0
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def collect_claude_usage(
    root: Path | None = None,
    today: dt.date | None = None,
) -> dict[str, object]:
    today = today or dt.date.today()
    root = root or (Path.home() / ".claude" / "projects")
    summary = empty_summary(str(root))
    if not root.exists():
        return summary

    latest_mtime = -1.0
    latest_session: dict[str, int] | None = None
    latest_seen = 0.0
    today_tokens = 0

    for path in root.glob("**/*.jsonl"):
        session_usage = {
            "session_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
        }
        matched = False
        last_seen = 0.0
        for obj in iter_jsonl_objects(path):
            message = obj.get("message") or {}
            usage = message.get("usage") or {}
            if not usage:
                continue
            matched = True
            input_tokens = int(usage.get("input_tokens", 0) or 0)
            output_tokens = int(usage.get("output_tokens", 0) or 0)
            cached_tokens = int(usage.get("cache_creation_input_tokens", 0) or 0) + int(
                usage.get("cache_read_input_tokens", 0) or 0
            )
            total = input_tokens + output_tokens
            session_usage["session_tokens"] += total
            session_usage["input_tokens"] += input_tokens
            session_usage["output_tokens"] += output_tokens
            session_usage["cached_tokens"] += cached_tokens
            ts = obj.get("timestamp") or message.get("timestamp") or ""
            last_seen = max(last_seen, safe_iso_timestamp(ts))
            if parse_iso_date(ts) == today:
                today_tokens += total

        if matched:
            mtime = safe_mtime(path)
            if mtime >= latest_mtime:
                latest_mtime = mtime
                latest_session = session_usage
                latest_seen = last_seen

    if latest_session:
        summary.update(latest_session)
        summary["today_tokens"] = today_tokens
        summary["available"] = True
        summary["last_seen"] = latest_seen
    return summary


def collect_codex_usage(
    root: Path | None = None,
    today: dt.date | None = None,
) -> dict[str, object]:
    today = today or dt.date.today()
    root = root or (Path.home() / ".codex" / "sessions")
    summary = empty_summary(str(root))
    if not root.exists():
        return summary

    latest_mtime = -1.0
    latest_total: dict[str, object] | None = None
    today_tokens = 0

    for path in root.glob("**/*.jsonl"):
        matched = False
        file_latest: dict[str, object] | None = None
        for obj in iter_jsonl_objects(path):
            payload = obj.get("payload") or {}
            if obj.get("type") != "event_msg" or payload.get("type") != "token_count":
                continue
            matched = True
            info = payload.get("info") or {}
            total_usage = info.get("total_token_usage") or {}
            last_usage = info.get("last_token_usage") or {}
            rate_limits = payload.get("rate_limits") or {}
            primary = rate_limits.get("primary") or {}
            if total_usage:
                file_latest = {
                    "session_tokens": int(total_usage.get("total_tokens", 0) or 0),
                    "input_tokens": int(total_usage.get("input_tokens", 0) or 0),
                    "output_tokens": int(total_usage.get("output_tokens", 0) or 0),
                    "cached_tokens": int(total_usage.get("cached_input_tokens", 0) or 0),
                    "reasoning_tokens": int(total_usage.get("reasoning_output_tokens", 0) or 0),
                    "used_percent": primary.get("used_percent"),
                    "reset_at": format_reset_time(primary.get("resets_at")),
                    "last_seen": 0.0,
                }
            ts = obj.get("timestamp") or ""
            if last_usage and parse_iso_date(ts) == today:
                today_tokens += int(last_usage.get("total_tokens", 0) or 0)
            if file_latest is not None:
                file_latest["last_seen"] = safe_iso_timestamp(ts)

        if matched and file_latest is not None:
            mtime = safe_mtime(path)
            if mtime >= latest_mtime:
                latest_mtime = mtime
                latest_total = file_latest

    if latest_total:
        summary.update(latest_total)
        summary["today_tokens"] = today_tokens
        summary["available"] = True
    return summary


def collect_gemini_usage(root: Path | None = None) -> dict[str, object]:
    root = root or (Path.home() / ".gemini" / "tmp")
    summary = empty_summary(str(root))
    if not root.exists():
        return summary

    latest_mtime = -1.0
    latest_total: dict[str, object] | None = None
    for session_dir in root.iterdir():
        if not session_dir.is_dir():
            continue
        logs_path = session_dir / "logs.json"
        if not logs_path.exists():
            continue
        try:
            payload = json.loads(logs_path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, json.JSONDecodeError):
            continue
        usages = extract_usage_metadata(payload)
        if not usages:
            continue
        total = {
            "session_tokens": 0,
            "today_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
            "used_percent": None,
            "reset_at": "",
            "last_seen": 0.0,
        }
        for usage in usages:
            session_tokens = (
                usage["input_tokens"]
                + usage["output_tokens"]
                + usage["reasoning_tokens"]
                + usage["tool_tokens"]
            )
            total["session_tokens"] += session_tokens
            total["today_tokens"] += session_tokens
            total["input_tokens"] += usage["input_tokens"] + usage["tool_tokens"]
            total["output_tokens"] += usage["output_tokens"]
            total["cached_tokens"] += usage["cached_tokens"]
            total["reasoning_tokens"] += usage["reasoning_tokens"]
        total["last_seen"] = safe_mtime(logs_path)
        if total["last_seen"] >= latest_mtime:
            latest_mtime = float(total["last_seen"])
            latest_total = total

    if latest_total:
        summary.update(latest_total)
        summary["available"] = True
    return summary


def collect_all_token_usage(today: dt.date | None = None) -> dict[str, dict[str, object]]:
    return {
        "Claude": collect_claude_usage(today=today),
        "Codex": collect_codex_usage(today=today),
        "Gemini": collect_gemini_usage(),
    }


def main() -> int:
    print(json.dumps(collect_all_token_usage()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
