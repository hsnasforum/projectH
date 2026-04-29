"""Shared helpers for preference quality and reliability projections."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.delta_analysis import is_high_quality
from core.contracts import PerPreferenceStats


def preference_fingerprint(preference: Mapping[str, Any]) -> str:
    return str(preference.get("fingerprint") or preference.get("delta_fingerprint") or "")


def seed_reliability_from_recurrence(recurrence_count: int) -> dict[str, int]:
    if recurrence_count < 1:
        return {}
    return {"applied_count": recurrence_count, "corrected_count": 0}


def _normalized_reliability_stats(stats: Any) -> dict[str, int]:
    if not isinstance(stats, Mapping):
        return {"applied_count": 0, "corrected_count": 0}
    applied_count = stats.get("applied_count", 0)
    corrected_count = stats.get("corrected_count", 0)
    return {
        "applied_count": applied_count if isinstance(applied_count, int) else 0,
        "corrected_count": corrected_count if isinstance(corrected_count, int) else 0,
    }


def _quality_info_from_existing(existing_quality_info: Any) -> dict[str, float | bool | None] | None:
    if not isinstance(existing_quality_info, Mapping):
        return None
    if "is_high_quality" not in existing_quality_info:
        return None
    avg_score = existing_quality_info.get("avg_similarity_score")
    try:
        avg_score_float = float(avg_score) if avg_score is not None else None
    except (TypeError, ValueError):
        avg_score_float = None
    is_high = existing_quality_info.get("is_high_quality")
    return {
        "avg_similarity_score": avg_score_float,
        "is_high_quality": is_high if isinstance(is_high, bool) else None,
    }


def _quality_info_from_score(avg_score: Any) -> dict[str, float | bool | None]:
    if avg_score is None:
        return {"avg_similarity_score": None, "is_high_quality": None}
    try:
        avg_score_float = float(avg_score)
    except (TypeError, ValueError):
        return {"avg_similarity_score": None, "is_high_quality": None}
    return {
        "avg_similarity_score": avg_score_float,
        "is_high_quality": is_high_quality(avg_score_float),
    }


def enrich_preference_reliability(
    preference: Mapping[str, Any],
    per_preference_stats: Mapping[str, PerPreferenceStats] | None = None,
) -> dict[str, Any]:
    pref_copy = dict(preference)
    fingerprint = preference_fingerprint(pref_copy)
    stats = None
    if isinstance(per_preference_stats, Mapping):
        stats = per_preference_stats.get(fingerprint)
    if stats is None:
        stats = pref_copy.get("reliability_stats")
    pref_copy["reliability_stats"] = _normalized_reliability_stats(stats)
    pref_copy["quality_info"] = (
        _quality_info_from_existing(pref_copy.get("quality_info"))
        or _quality_info_from_score(pref_copy.get("avg_similarity_score"))
    )
    pref_copy["is_highly_reliable"] = is_highly_reliable_preference(pref_copy)
    return pref_copy


def is_highly_reliable_preference(preference: Mapping[str, Any]) -> bool:
    quality_info = preference.get("quality_info")
    if not isinstance(quality_info, Mapping) or quality_info.get("is_high_quality") is not True:
        return False

    reliability_stats = preference.get("reliability_stats")
    if not isinstance(reliability_stats, Mapping):
        return False

    applied_count = reliability_stats.get("applied_count", 0)
    corrected_count = reliability_stats.get("corrected_count", 0)
    if not isinstance(applied_count, int) or not isinstance(corrected_count, int):
        return False
    if applied_count < 3:
        return False
    return corrected_count / applied_count < 0.15
