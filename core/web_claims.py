from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    slot: str
    value: str
    source_url: str
    source_title: str
    source_role: str
    support_count: int = 1
    confidence: float = 0.0
    supporting_sources: tuple[tuple[str, str, str], ...] = ()


_ROLE_PRIORITY = {
    "백과 기반": 4,
    "공식 기반": 3,
    "설명형 출처": 2,
    "보조 기사": 1,
    "보조 출처": 1,
    "보조 포털": 0,
    "보조 블로그": 0,
}


def normalize_claim_value(value: str) -> str:
    return " ".join(str(value or "").split()).strip().lower().rstrip(".")


def claim_values_overlap(left: str, right: str) -> bool:
    normalized_left = normalize_claim_value(left)
    normalized_right = normalize_claim_value(right)
    if not normalized_left or not normalized_right:
        return False
    return (
        normalized_left == normalized_right
        or normalized_left in normalized_right
        or normalized_right in normalized_left
    )


def _claim_sort_key(record: ClaimRecord) -> tuple[int, int, int, int, str]:
    return (
        record.support_count,
        _ROLE_PRIORITY.get(record.source_role, 0),
        int(record.confidence * 1000),
        len(record.value),
        record.value,
    )


def merge_claim_records(records: Iterable[ClaimRecord]) -> list[ClaimRecord]:
    merged_by_slot: dict[str, list[ClaimRecord]] = {}

    for record in records:
        slot = " ".join(str(record.slot or "").split()).strip()
        value = " ".join(str(record.value or "").split()).strip().rstrip(".")
        if not slot or not value:
            continue

        current = ClaimRecord(
            slot=slot,
            value=value,
            source_url=str(record.source_url or "").strip(),
            source_title=str(record.source_title or "").strip(),
            source_role=str(record.source_role or "").strip(),
            support_count=max(int(record.support_count or 1), 1),
            confidence=float(record.confidence or 0.0),
            supporting_sources=record.supporting_sources
            or ((
                str(record.source_url or "").strip(),
                str(record.source_title or "").strip(),
                str(record.source_role or "").strip(),
            ),),
        )
        slot_items = merged_by_slot.setdefault(slot, [])

        for index, existing in enumerate(slot_items):
            if not claim_values_overlap(existing.value, current.value):
                continue
            combined_support = max(existing.support_count, current.support_count)
            if current.source_url and current.source_url != existing.source_url:
                combined_support += 1
            supporting_sources = list(existing.supporting_sources)
            seen_refs = {(url, title, role) for url, title, role in supporting_sources}
            for ref in current.supporting_sources:
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)
                supporting_sources.append(ref)
            winner = max([existing, current], key=_claim_sort_key)
            slot_items[index] = ClaimRecord(
                slot=slot,
                value=winner.value,
                source_url=winner.source_url,
                source_title=winner.source_title,
                source_role=winner.source_role,
                support_count=combined_support,
                confidence=max(existing.confidence, current.confidence),
                supporting_sources=tuple(supporting_sources),
            )
            break
        else:
            slot_items.append(current)

    merged: list[ClaimRecord] = []
    for slot_items in merged_by_slot.values():
        merged.extend(slot_items)
    return merged
