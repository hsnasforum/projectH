from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .base import ParseResult, UsageEntry, compute_content_hash, iter_jsonl_lines


class ClaudeParser:
    kind = "claude"

    def parse_file(self, path: Path) -> ParseResult:
        result = ParseResult()
        for line_no, offset, raw_line, has_newline in iter_jsonl_lines(path):
            try:
                obj = json.loads(raw_line)
            except json.JSONDecodeError:
                if not has_newline:
                    result.trailing_incomplete = True
                    result.last_error = f"trailing_incomplete_jsonl:{path.name}:{line_no}"
                    break
                result.skipped_lines += 1
                result.last_error = f"skipped_invalid_jsonl:{path.name}:{line_no}"
                continue
            message = obj.get("message") or {}
            usage = message.get("usage") or {}
            if not usage:
                continue

            timestamp = str(obj.get("timestamp") or message.get("timestamp") or "")
            day = _iso_day(timestamp)
            result.entries.append(
                UsageEntry(
                    ts=timestamp,
                    day=day,
                    source="claude",
                    model=message.get("model"),
                    input_tokens=int(usage.get("input_tokens", 0) or 0),
                    output_tokens=int(usage.get("output_tokens", 0) or 0),
                    cache_read_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
                    cache_write_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
                    thinking_tokens=0,
                    web_search_requests=int(((usage.get("server_tool_use") or {}).get("web_search_requests", 0)) or 0),
                    actual_cost_usd=None,
                    estimated_cost_usd=None,
                    message_id=_first_non_empty(
                        obj.get("messageId"),
                        message.get("id"),
                        obj.get("uuid"),
                    ),
                    request_id=_first_non_empty(obj.get("requestId"), obj.get("request_id")),
                    raw_path=str(path),
                    raw_offset=offset,
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
        if value:
            return str(value)
    return None
