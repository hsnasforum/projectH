from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .base import ParseResult, UsageEntry, compute_content_hash, iter_jsonl_lines


class CodexParser:
    kind = "codex"

    def parse_file(self, path: Path) -> ParseResult:
        result = ParseResult()
        session_id = path.stem
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
            payload = obj.get("payload") or {}
            if obj.get("type") != "event_msg" or payload.get("type") != "token_count":
                continue
            info = payload.get("info") or {}
            last_usage = info.get("last_token_usage") or {}
            if not last_usage:
                continue
            timestamp = str(obj.get("timestamp") or "")
            day = _iso_day(timestamp)
            result.entries.append(
                UsageEntry(
                    ts=timestamp,
                    day=day,
                    source="codex",
                    model=None,
                    input_tokens=int(last_usage.get("input_tokens", 0) or 0),
                    output_tokens=int(last_usage.get("output_tokens", 0) or 0),
                    cache_read_tokens=int(last_usage.get("cached_input_tokens", 0) or 0),
                    cache_write_tokens=0,
                    thinking_tokens=int(last_usage.get("reasoning_output_tokens", 0) or 0),
                    web_search_requests=0,
                    actual_cost_usd=None,
                    estimated_cost_usd=None,
                    message_id=None,
                    request_id=session_id,
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
