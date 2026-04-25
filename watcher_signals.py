from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Optional

from pipeline_runtime.operator_autonomy import normalize_reason_code
from pipeline_runtime.role_routes import (
    VERIFY_TRIAGE_ESCALATION,
    VERIFY_TRIAGE_ONLY_REASON,
    is_verify_triage_escalation,
    normalize_verify_triage_escalation,
)


_LIVE_SESSION_ESCALATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "context_exhaustion",
        re.compile(
            r"context window|context exhausted|window nearly full|maximum context|conversation too long|컨텍스트\s*window|컨텍스트.*가득",
            re.IGNORECASE,
        ),
    ),
    (
        "session_rollover",
        re.compile(
            r"new session recommended|session rollover|start a new session|fresh session|new thread|새 세션|새로.*세션",
            re.IGNORECASE,
        ),
    ),
    (
        "continue_vs_switch",
        re.compile(
            r"continue\?|should i continue|continue here|handoff and continue|진행할까요|이어가시는 것을 강하게 권고|이어서 진행",
            re.IGNORECASE,
        ),
    ),
)

_LIVE_SESSION_ESCALATION_FALLBACK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "context_exhaustion": (
        "context", "window", "full", "exhaust", "too long", "maximum context",
        "token", "limit", "컨텍스트", "가득", "소진", "길어",
    ),
    "session_rollover": (
        "new session", "fresh session", "new thread", "start over", "restart session",
        "open a new", "새 세션", "새로", "다음 세션", "새 thread",
    ),
    "continue_vs_switch": (
        "continue", "keep going", "handoff", "switch", "continue here",
        "진행", "이어서", "계속", "이어갈", "이어가",
    ),
}

_IMPLEMENT_BLOCKED_STATUS_RE = re.compile(r"^\s*(?:[-*•]\s+)?STATUS:\s*(.*?)\s*$", re.IGNORECASE)
_IMPLEMENT_BLOCKED_FIELD_RE = re.compile(r"^\s*(?:[-*•]\s+)?([A-Z_]+):\s*(.*?)\s*$")
_IMPLEMENT_BLOCKED_WRAP_KEYS = {"BLOCK_REASON", "HANDOFF", "HANDOFF_SHA", "BLOCK_ID"}
_IMPLEMENT_BLOCKED_TEMPLATE_MARKERS = (
    "blocked_sentinel:",
    "emit the exact sentinel below",
)
_IMPLEMENT_ALREADY_DONE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\balready completed\b", re.IGNORECASE),
    re.compile(r"\balready addressed\b", re.IGNORECASE),
    re.compile(r"\bthe work described in the handoff was already completed\b", re.IGNORECASE),
    re.compile(r"\bthe handoff was already completed\b", re.IGNORECASE),
    re.compile(r"핸드오프.*이미.*완료", re.IGNORECASE),
    re.compile(r"슬라이스.*이미.*완료", re.IGNORECASE),
    re.compile(r"이미 완료된 상태", re.IGNORECASE),
)
_IMPLEMENT_NO_CHANGE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bno uncommitted changes\b", re.IGNORECASE),
    re.compile(r"\bno remaining\b", re.IGNORECASE),
    re.compile(r"\bno generic instances remain\b", re.IGNORECASE),
    re.compile(r"추가로 변경할 파일이 없", re.IGNORECASE),
    re.compile(r"변경할 파일이 없", re.IGNORECASE),
    re.compile(r"잔존 없음", re.IGNORECASE),
)
_IMPLEMENT_FORBIDDEN_MENU_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"다음\s+중\s+하나를\s+선택", re.IGNORECASE),
    re.compile(r"choose one of the following", re.IGNORECASE),
    re.compile(r"which option should i", re.IGNORECASE),
    re.compile(r"select (?:one|an option)", re.IGNORECASE),
    re.compile(r"operator.*choose", re.IGNORECASE),
)
_HANDOFF_MARKDOWN_BULLET_LITERAL_RE = re.compile(r"^\s*-\s+`(.*)`\s*$")
_MATERIALIZED_BLOCK_REASON_CODES = {
    "already_implemented",
    "duplicate_handoff",
    "handoff_already_applied",
}
_MATERIALIZED_BLOCK_REASONS = {
    "handoff_already_completed",
    "slice_already_materialized",
}


def _line_looks_like_input_prompt(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return (
        stripped == ">"
        or stripped == "›"
        or stripped == "❯"
        or stripped.startswith("> ")
        or stripped.startswith("› ")
        or stripped.startswith("❯ ")
        or stripped.endswith("$")
    )


def _normalize_escalation_line(line: str) -> str:
    normalized = line.strip().lower()
    normalized = re.sub(r"\d+[hmsp초분시간]+", "#", normalized)
    normalized = re.sub(r"\d+", "#", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _match_implement_blocked_status(
    recent_lines: list[str],
    idx: int,
) -> tuple[bool, int, list[str]]:
    line = recent_lines[idx]
    match = _IMPLEMENT_BLOCKED_STATUS_RE.match(line)
    if not match:
        return False, idx, []
    value = match.group(1).strip().lower()
    if value == "implement_blocked":
        return True, idx + 1, [f"STATUS: {value}"]
    if value:
        return False, idx, []
    if idx + 1 >= len(recent_lines):
        return False, idx, []
    next_line = recent_lines[idx + 1].strip().lower()
    if next_line != "implement_blocked":
        return False, idx, []
    return True, idx + 2, ["STATUS: implement_blocked"]


def _can_append_implement_blocked_wrap(key: str, stripped: str) -> bool:
    if not stripped or _line_looks_like_input_prompt(stripped):
        return False
    if key == "BLOCK_REASON":
        return True
    if key == "HANDOFF":
        return True
    if key == "HANDOFF_SHA":
        return bool(re.fullmatch(r"[0-9a-fA-F]+", stripped))
    if key == "BLOCK_ID":
        return bool(re.fullmatch(r"[0-9A-Za-z._:/-]+", stripped))
    return False


def _decode_handoff_markdown_literal(line: str) -> str:
    match = _HANDOFF_MARKDOWN_BULLET_LITERAL_RE.match(line)
    if not match:
        return ""
    return match.group(1).replace("\\`", "`").strip()


@dataclass(frozen=True)
class _HandoffSentenceReplacementTarget:
    path: str
    current_sentence: str
    replacement_sentence: str


def _parse_handoff_sentence_replacement_target(
    handoff_text: str,
) -> Optional[_HandoffSentenceReplacementTarget]:
    target_path = ""
    current_sentence = ""
    replacement_sentence = ""
    capture_mode = ""
    for raw_line in handoff_text.splitlines():
        line = raw_line.strip()
        if line == "EDIT EXACTLY ONE FILE:":
            capture_mode = "path"
            continue
        if line.startswith("CURRENT SENTENCE TO REPLACE"):
            capture_mode = "current"
            continue
        if line.startswith("REPLACEMENT SENTENCE"):
            capture_mode = "replacement"
            continue
        if not line.startswith("- "):
            continue
        literal = _decode_handoff_markdown_literal(line)
        if not literal:
            continue
        if capture_mode == "path" and not target_path:
            target_path = literal
        elif capture_mode == "current" and not current_sentence:
            current_sentence = literal
        elif capture_mode == "replacement" and not replacement_sentence:
            replacement_sentence = literal
        capture_mode = ""
        if target_path and current_sentence and replacement_sentence:
            return _HandoffSentenceReplacementTarget(
                path=target_path,
                current_sentence=current_sentence,
                replacement_sentence=replacement_sentence,
            )
    if not target_path or not current_sentence or not replacement_sentence:
        return None
    return _HandoffSentenceReplacementTarget(
        path=target_path,
        current_sentence=current_sentence,
        replacement_sentence=replacement_sentence,
    )


def _fallback_escalation_reasons(lines: list[str]) -> list[str]:
    window_text = " ".join(_normalize_escalation_line(line) for line in lines)
    matched: list[str] = []
    for reason, keywords in _LIVE_SESSION_ESCALATION_FALLBACK_KEYWORDS.items():
        if any(keyword in window_text for keyword in keywords):
            matched.append(reason)
    if len(matched) < 2:
        return []
    if "continue_vs_switch" in matched and any(
        reason in matched for reason in ("context_exhaustion", "session_rollover")
    ):
        return matched
    if {"context_exhaustion", "session_rollover"}.issubset(matched):
        return matched
    return []


def _extract_live_session_escalation(text: str) -> Optional[dict[str, object]]:
    """Return a normalized live-session escalation signal from pane text."""
    if not text.strip():
        return None

    recent_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not recent_lines:
        return None
    recent_lines = recent_lines[-60:]
    hot_window = recent_lines[-12:]

    matched_reasons: list[str] = []
    excerpt_lines: list[str] = []
    matched_in_hot_window = False
    for line in recent_lines:
        matched_here = False
        for reason, pattern in _LIVE_SESSION_ESCALATION_PATTERNS:
            if pattern.search(line):
                matched_here = True
                if reason not in matched_reasons:
                    matched_reasons.append(reason)
        if matched_here:
            excerpt_lines.append(line)
            if line in hot_window:
                matched_in_hot_window = True

    if not matched_reasons:
        fallback_reasons = _fallback_escalation_reasons(hot_window)
        if fallback_reasons:
            matched_reasons = fallback_reasons
            excerpt_lines = hot_window[-8:]
            matched_in_hot_window = True

    if not matched_reasons or not matched_in_hot_window:
        return None

    normalized_excerpt = [_normalize_escalation_line(line) for line in excerpt_lines[:8]]
    fingerprint_source = "|".join(matched_reasons + normalized_excerpt)
    fingerprint = hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest()
    return {
        "reasons": matched_reasons,
        "excerpt_lines": excerpt_lines[:8],
        "fingerprint": fingerprint,
    }


def _normalize_control_path_hint(path_hint: str) -> str:
    return path_hint.strip().lstrip("./").replace("\\", "/")


def _extract_implement_blocked_signal(
    text: str,
    active_handoff_path: str = "",
    active_handoff_sha: str = "",
) -> Optional[dict[str, object]]:
    """Return an explicit implement_blocked sentinel if present in recent implement-owner output."""
    if not text.strip():
        return None

    recent_lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not recent_lines:
        return None
    recent_lines = recent_lines[-80:]

    for idx in range(len(recent_lines) - 1, -1, -1):
        matched, field_start_idx, block_lines = _match_implement_blocked_status(recent_lines, idx)
        if not matched:
            continue

        template_context = "\n".join(line.strip().lower() for line in recent_lines[max(0, idx - 3):idx])
        if any(marker in template_context for marker in _IMPLEMENT_BLOCKED_TEMPLATE_MARKERS):
            continue

        fields: dict[str, str] = {}
        current_key = ""
        for line in recent_lines[field_start_idx: field_start_idx + 24]:
            stripped = line.strip()
            if _line_looks_like_input_prompt(stripped):
                break
            match = _IMPLEMENT_BLOCKED_FIELD_RE.match(line)
            if match:
                current_key = match.group(1).upper()
                fields[current_key] = match.group(2).strip()
                block_lines.append(f"{current_key}: {fields[current_key]}".rstrip())
                continue
            if (
                current_key in _IMPLEMENT_BLOCKED_WRAP_KEYS
                and _can_append_implement_blocked_wrap(current_key, stripped)
            ):
                prefix = fields.get(current_key, "")
                separator = " " if current_key == "BLOCK_REASON" and prefix else ""
                fields[current_key] = prefix + separator + stripped
                if block_lines:
                    block_lines[-1] = f"{current_key}: {fields[current_key]}".rstrip()
                continue
            if current_key == "BLOCK_ID":
                break
            if stripped:
                block_lines.append(stripped)

        request = normalize_verify_triage_escalation(fields.get("REQUEST", ""))
        escalation_class = fields.get("ESCALATION_CLASS", "").strip().lower()
        escalation_class = normalize_verify_triage_escalation(escalation_class)
        if request and not is_verify_triage_escalation(request):
            return None
        if escalation_class and not is_verify_triage_escalation(escalation_class):
            return None
        if escalation_class and request and escalation_class != request:
            return None
        request = escalation_class or request or VERIFY_TRIAGE_ESCALATION

        block_reason_code = normalize_reason_code(fields.get("BLOCK_REASON_CODE", ""))

        handoff_hint = fields.get("HANDOFF", "")
        if active_handoff_path and handoff_hint:
            if _normalize_control_path_hint(handoff_hint) != _normalize_control_path_hint(active_handoff_path):
                return None

        handoff_sig = fields.get("HANDOFF_SHA") or fields.get("HANDOFF_SIG") or ""
        if active_handoff_sha and handoff_sig and handoff_sig != active_handoff_sha:
            return None

        block_reason = fields.get("BLOCK_REASON", "implement_blocked").strip().lower() or "implement_blocked"
        if block_reason.startswith("<"):
            continue
        fingerprint_source = "|".join(
            [
                "sentinel",
                active_handoff_sha or handoff_sig,
                block_reason,
                "|".join(_normalize_escalation_line(line) for line in block_lines[:6]),
            ]
        )
        fingerprint = fields.get("BLOCK_ID", "").strip() or hashlib.sha1(
            fingerprint_source.encode("utf-8")
        ).hexdigest()
        if fingerprint.startswith("<") or "<short_reason" in fingerprint.lower():
            continue
        return {
            "source": "sentinel",
            "reason": block_reason,
            "reason_code": block_reason_code,
            "escalation_class": request,
            "request": request,
            "excerpt_lines": block_lines[:6],
            "fingerprint": fingerprint,
            "handoff_hint": handoff_hint,
        }
    return None


def _extract_implement_forbidden_menu_signal(text: str, active_handoff_sha: str = "") -> Optional[dict[str, object]]:
    """Detect forbidden operator-choice text in recent implement-owner output as a soft blocked signal."""
    if not text.strip():
        return None

    recent_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not recent_lines:
        return None
    hot_window = recent_lines[-16:]
    matched_lines = [
        line for line in hot_window
        if any(pattern.search(line) for pattern in _IMPLEMENT_FORBIDDEN_MENU_PATTERNS)
    ]
    if not matched_lines:
        return None

    fingerprint_source = "|".join(
        ["soft_blocked", active_handoff_sha, *(_normalize_escalation_line(line) for line in matched_lines[:6])]
    )
    return {
        "source": "soft_blocked",
        "reason": "forbidden_operator_menu",
        "reason_code": VERIFY_TRIAGE_ONLY_REASON,
        "escalation_class": VERIFY_TRIAGE_ESCALATION,
        "request": VERIFY_TRIAGE_ESCALATION,
        "excerpt_lines": matched_lines[:6],
        "fingerprint": hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest(),
        "handoff_hint": "",
    }


def _extract_implement_completed_handoff_signal(text: str, active_handoff_sha: str = "") -> Optional[dict[str, object]]:
    """Detect the implement owner saying the current handoff is already complete / no-op."""
    if not text.strip():
        return None

    recent_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not recent_lines:
        return None
    hot_window = recent_lines[-24:]
    done_lines = [
        line for line in hot_window
        if any(pattern.search(line) for pattern in _IMPLEMENT_ALREADY_DONE_PATTERNS)
    ]
    noop_lines = [
        line for line in hot_window
        if any(pattern.search(line) for pattern in _IMPLEMENT_NO_CHANGE_PATTERNS)
    ]
    if not done_lines:
        return None
    if not noop_lines and not any("handoff" in line.lower() for line in done_lines):
        return None

    excerpt_lines = (done_lines + noop_lines)[:6]
    fingerprint_source = "|".join(
        ["soft_completed", active_handoff_sha, *(_normalize_escalation_line(line) for line in excerpt_lines)]
    )
    return {
        "source": "soft_completed",
        "reason": "handoff_already_completed",
        "reason_code": "duplicate_handoff",
        "escalation_class": VERIFY_TRIAGE_ESCALATION,
        "request": VERIFY_TRIAGE_ESCALATION,
        "excerpt_lines": excerpt_lines,
        "fingerprint": hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest(),
        "handoff_hint": "",
    }
