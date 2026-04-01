from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.contracts import CoverageStatus, SourceRole, TRUSTED_SOURCE_ROLES

CORE_ENTITY_SLOTS = ("개발", "서비스/배급", "장르/성격", "상태", "이용 형태")
TRUSTED_CLAIM_SOURCE_ROLES = TRUSTED_SOURCE_ROLES


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


@dataclass(frozen=True, slots=True)
class SlotCoverage:
    slot: str
    status: str
    primary_claim: ClaimRecord | None = None
    candidate_count: int = 0


_ROLE_PRIORITY = {
    SourceRole.WIKI: 4,
    SourceRole.OFFICIAL: 3,
    SourceRole.DATABASE: 3,
    SourceRole.DESCRIPTIVE: 2,
    SourceRole.NEWS: 1,
    SourceRole.AUXILIARY: 1,
    SourceRole.COMMUNITY: 0,
    SourceRole.PORTAL: 0,
    SourceRole.BLOG: 0,
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


def summarize_slot_coverage(
    records: Iterable[ClaimRecord],
    *,
    slots: Iterable[str] = CORE_ENTITY_SLOTS,
) -> dict[str, SlotCoverage]:
    grouped: dict[str, list[ClaimRecord]] = {}
    for record in records:
        slot = " ".join(str(record.slot or "").split()).strip()
        if not slot:
            continue
        grouped.setdefault(slot, []).append(record)

    coverage: dict[str, SlotCoverage] = {}
    for slot in slots:
        items = grouped.get(slot) or []
        if not items:
            coverage[slot] = SlotCoverage(slot=slot, status=CoverageStatus.MISSING, primary_claim=None, candidate_count=0)
            continue
        primary = max(items, key=_claim_sort_key)
        status = CoverageStatus.STRONG if primary.support_count >= 2 else CoverageStatus.WEAK
        coverage[slot] = SlotCoverage(
            slot=slot,
            status=status,
            primary_claim=primary,
            candidate_count=len(items),
        )
    return coverage
