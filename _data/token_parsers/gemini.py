from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .base import ParseResult, UsageEntry, compute_content_hash


class GeminiParser:
    kind = "gemini"

    def parse_file(self, path: Path) -> ParseResult:
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, json.JSONDecodeError):
            return ParseResult(
                retry_later=True,
                last_error=f"retry_json_payload:{path.name}",
            )
        if not isinstance(payload, list):
            return ParseResult(last_error=f"unexpected_payload_shape:{path.name}")
        result = ParseResult()
        for line_no, obj in enumerate(payload, start=1):
            if not isinstance(obj, dict):
                result.skipped_lines += 1
                result.last_error = f"skipped_non_object:{path.name}:{line_no}"
                continue
            usage = obj.get("usageMetadata")
            if not isinstance(usage, dict):
                continue
            raw_line = json.dumps(obj, ensure_ascii=False, sort_keys=True)
            timestamp = str(obj.get("timestamp") or "")
            day = _iso_day(timestamp)
            result.entries.append(
                UsageEntry(
                    ts=timestamp,
                    day=day,
                    source="gemini",
                    model=None,
                    input_tokens=int(usage.get("promptTokenCount", 0) or 0)
                    + int(usage.get("toolUsePromptTokenCount", 0) or 0),
                    output_tokens=int(usage.get("candidatesTokenCount", 0) or 0),
                    cache_read_tokens=int(usage.get("cachedContentTokenCount", 0) or 0),
                    cache_write_tokens=0,
                    thinking_tokens=int(usage.get("thoughtsTokenCount", 0) or 0),
                    web_search_requests=0,
                    actual_cost_usd=None,
                    estimated_cost_usd=None,
                    message_id=_first_non_empty(obj.get("messageId")),
                    request_id=_first_non_empty(obj.get("sessionId")),
                    raw_path=str(path),
                    raw_offset=None,
                    raw_line_no=line_no,
                    content_hash=compute_content_hash(raw_line),
                )
            )
        result.parsed_events = len(result.entries)
        return result


def _iso_day(raw: str) -> str:
    if not raw:
        return ""
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return ""


def _first_non_empty(*values: object) -> str | None:
    for value in values:
        if value is not None and value != "":
            return str(value)
    return None
