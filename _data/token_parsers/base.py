from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class UsageEntry:
    ts: str
    day: str
    source: str
    model: str | None
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    thinking_tokens: int
    web_search_requests: int
    actual_cost_usd: float | None
    estimated_cost_usd: float | None
    message_id: str | None
    request_id: str | None
    raw_path: str
    raw_offset: int | None
    raw_line_no: int | None
    content_hash: str

    def dedup_key(self) -> str:
        if self.message_id and self.request_id:
            return f"{self.source}|mid:{self.message_id}|rid:{self.request_id}"
        if self.raw_offset is not None:
            return f"{self.source}|path:{self.raw_path}|off:{self.raw_offset}"
        if self.raw_line_no is not None:
            return f"{self.source}|path:{self.raw_path}|line:{self.raw_line_no}"
        return (
            f"{self.source}|ts:{self.ts}|model:{self.model or ''}|"
            f"in:{self.input_tokens}|out:{self.output_tokens}|hash:{self.content_hash}"
        )


@dataclass(slots=True)
class ParseResult:
    entries: list[UsageEntry] = field(default_factory=list)
    parsed_events: int = 0
    skipped_lines: int = 0
    trailing_incomplete: bool = False
    retry_later: bool = False
    last_error: str | None = None


def compute_content_hash(raw_line: str) -> str:
    return hashlib.sha1(raw_line.encode("utf-8", errors="ignore")).hexdigest()


def iter_jsonl_lines(path: Path):
    with path.open(encoding="utf-8", errors="ignore") as handle:
        offset = 0
        for line_no, line in enumerate(handle, start=1):
            yield line_no, offset, line, line.endswith("\n")
            offset += len(line.encode("utf-8", errors="ignore"))
