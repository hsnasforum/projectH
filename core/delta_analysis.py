"""Pure delta analysis for correction pairs.

The fingerprint algorithm is identical to WebAppService._derive_normalized_rewrite_delta
for backward compatibility.
"""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CorrectionDelta:
    delta_fingerprint: str
    segments: tuple[dict[str, str], ...]
    delta_summary: dict[str, Any]
    similarity_score: float
    rewrite_dimensions: dict[str, Any]


def compute_correction_delta(
    original_text: str,
    corrected_text: str,
) -> CorrectionDelta | None:
    """Compute structured delta from original -> corrected text.

    Returns None if texts are identical (no diff segments).
    The fingerprint matches the existing web.py algorithm exactly.
    """
    matcher = difflib.SequenceMatcher(a=original_text, b=corrected_text, autojunk=False)
    segments: list[dict[str, str]] = []
    change_types: list[str] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        from_text = original_text[i1:i2]
        to_text = corrected_text[j1:j2]
        if not from_text and not to_text:
            continue
        segments.append({"from": from_text, "op": tag, "to": to_text})
        change_types.append(tag)

    if not segments:
        return None

    fingerprint = _compute_fingerprint(segments)
    similarity = matcher.ratio()
    summary = _extract_delta_summary(segments)
    dimensions = _compute_rewrite_dimensions(original_text, corrected_text, change_types, len(segments))

    return CorrectionDelta(
        delta_fingerprint=fingerprint,
        segments=tuple(segments),
        delta_summary=summary,
        similarity_score=round(similarity, 4),
        rewrite_dimensions=dimensions,
    )


def _compute_fingerprint(segments: list[dict[str, str]]) -> str:
    """SHA-256 fingerprint. Must match web.py exactly."""
    payload = json.dumps(
        segments,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _extract_delta_summary(segments: list[dict[str, str]]) -> dict[str, Any]:
    additions: list[str] = []
    removals: list[str] = []
    replacements: list[dict[str, str]] = []

    for seg in segments:
        op = seg.get("op", "")
        from_text = seg.get("from", "").strip()
        to_text = seg.get("to", "").strip()

        if op == "insert" and to_text:
            additions.append(to_text)
        elif op == "delete" and from_text:
            removals.append(from_text)
        elif op == "replace":
            if from_text or to_text:
                replacements.append({"from": from_text, "to": to_text})

    return {
        "additions": additions,
        "removals": removals,
        "replacements": replacements,
    }


def _compute_rewrite_dimensions(
    original: str,
    corrected: str,
    change_types: list[str],
    segment_count: int,
) -> dict[str, Any]:
    """Compatible with existing rewrite_dimensions format."""
    return {
        "change_types": sorted(set(change_types)),
        "changed_segment_count": segment_count,
        "line_count_delta": corrected.count("\n") - original.count("\n"),
        "character_count_delta": len(corrected) - len(original),
    }
