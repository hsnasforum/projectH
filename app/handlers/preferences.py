from __future__ import annotations

from typing import Any

from app.errors import WebApiError
from core.delta_analysis import is_high_quality


def _jaccard_word_similarity(a: str, b: str) -> float:
    """Return word-token Jaccard similarity between two strings (0.0-1.0)."""
    a_tokens = set(a.lower().split())
    b_tokens = set(b.lower().split())
    if not a_tokens and not b_tokens:
        return 1.0
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    return intersection / union


class PreferenceHandlerMixin:
    """Preference management methods extracted from WebAppService."""

    def list_preferences_payload(self) -> dict[str, Any]:
        all_prefs = self.preference_store.list_all()
        get_summary = getattr(self.session_store, "get_global_audit_summary", None)
        summary = get_summary() if callable(get_summary) else {}
        per_pref_stats = summary.get("per_preference_stats", {}) if isinstance(summary, dict) else {}
        if not isinstance(per_pref_stats, dict):
            per_pref_stats = {}

        enriched = []
        for pref in all_prefs:
            pref_copy = dict(pref)
            fingerprint = str(pref_copy.get("fingerprint") or pref_copy.get("delta_fingerprint") or "")
            stats = per_pref_stats.get(fingerprint, {})
            if not isinstance(stats, dict):
                stats = {}
            applied_count = stats.get("applied_count", 0)
            corrected_count = stats.get("corrected_count", 0)
            pref_copy["reliability_stats"] = {
                "applied_count": applied_count if isinstance(applied_count, int) else 0,
                "corrected_count": corrected_count if isinstance(corrected_count, int) else 0,
            }
            avg_score = pref_copy.get("avg_similarity_score")
            if avg_score is not None:
                try:
                    avg_score_float = float(avg_score)
                    quality_info = {
                        "avg_similarity_score": avg_score_float,
                        "is_high_quality": is_high_quality(avg_score_float),
                    }
                except (TypeError, ValueError):
                    quality_info = {"avg_similarity_score": None, "is_high_quality": None}
            else:
                quality_info = {"avg_similarity_score": None, "is_high_quality": None}
            pref_copy["quality_info"] = quality_info
            enriched.append(pref_copy)

        active_preferences = [
            p for p in enriched
            if p.get("status") == "active" and str(p.get("description") or "").strip()
        ]
        conflict_map: dict[str, list[str]] = {}
        for index, preference_a in enumerate(active_preferences):
            for preference_b in active_preferences[index + 1:]:
                description_a = str(preference_a.get("description") or "").strip()
                description_b = str(preference_b.get("description") or "").strip()
                if _jaccard_word_similarity(description_a, description_b) > 0.7:
                    preference_a_id = str(preference_a["preference_id"])
                    preference_b_id = str(preference_b["preference_id"])
                    conflict_map.setdefault(preference_a_id, []).append(preference_b_id)
                    conflict_map.setdefault(preference_b_id, []).append(preference_a_id)

        for pref_copy in enriched:
            pref_id = str(pref_copy.get("preference_id", ""))
            conflicting = conflict_map.get(pref_id, [])
            pref_copy["conflict_info"] = {
                "has_conflict": len(conflicting) > 0,
                "conflicting_preference_ids": conflicting,
            }

        return {
            "ok": True,
            "preferences": enriched,
            "active_count": sum(1 for p in enriched if p.get("status") == "active"),
            "candidate_count": sum(1 for p in enriched if p.get("status") == "candidate"),
        }

    def activate_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        preference_id = self._normalize_optional_text(payload.get("preference_id"))
        if not preference_id:
            raise WebApiError(400, "활성화할 선호 ID가 필요합니다.")
        result = self.preference_store.activate_preference(preference_id)
        if result is None:
            raise WebApiError(404, "해당 선호를 찾을 수 없습니다.")
        self.task_logger.log(session_id="system", action="preference_activated", detail={"preference_id": preference_id})
        return {"ok": True, "preference": result}

    def pause_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        preference_id = self._normalize_optional_text(payload.get("preference_id"))
        if not preference_id:
            raise WebApiError(400, "일시중지할 선호 ID가 필요합니다.")
        result = self.preference_store.pause_preference(preference_id)
        if result is None:
            raise WebApiError(404, "해당 선호를 찾을 수 없습니다.")
        self.task_logger.log(session_id="system", action="preference_paused", detail={"preference_id": preference_id})
        return {"ok": True, "preference": result}

    def reject_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        preference_id = self._normalize_optional_text(payload.get("preference_id"))
        if not preference_id:
            raise WebApiError(400, "거부할 선호 ID가 필요합니다.")
        result = self.preference_store.reject_preference(preference_id)
        if result is None:
            raise WebApiError(404, "해당 선호를 찾을 수 없습니다.")
        self.task_logger.log(session_id="system", action="preference_rejected", detail={"preference_id": preference_id})
        return {"ok": True, "preference": result}

    def update_preference_description(self, payload: dict[str, Any]) -> dict[str, Any]:
        preference_id = self._normalize_optional_text(payload.get("preference_id"))
        description = self._normalize_optional_text(payload.get("description"))
        if not preference_id:
            raise WebApiError(400, "설명을 수정할 선호 ID가 필요합니다.")
        if not description:
            raise WebApiError(400, "새 설명이 필요합니다.")
        result = self.preference_store.update_description(preference_id, description)
        if result is None:
            raise WebApiError(404, "해당 선호를 찾을 수 없습니다.")
        self.task_logger.log(
            session_id="system",
            action="preference_description_updated",
            detail={"preference_id": preference_id},
        )
        return {"ok": True, "preference": result}
