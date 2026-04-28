from __future__ import annotations

from typing import Any

from app.errors import WebApiError
from core.contracts import CandidateFamily
from storage.preference_utils import (
    enrich_preference_reliability,
    is_highly_reliable_preference,
)


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


def _as_nonempty_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _adopted_correction_description(correction: dict[str, Any], fingerprint: str) -> str:
    delta_summary = correction.get("delta_summary")
    if isinstance(delta_summary, str):
        summary = delta_summary.strip()
        if summary:
            return summary
    if isinstance(delta_summary, dict):
        for key in ("summary", "description", "statement"):
            summary = _as_nonempty_text(delta_summary.get(key))
            if summary:
                return summary
        replacements = delta_summary.get("replacements")
        if isinstance(replacements, list):
            for replacement in replacements:
                if not isinstance(replacement, dict):
                    continue
                replacement_text = _as_nonempty_text(replacement.get("to"))
                if replacement_text:
                    return replacement_text

    corrected_text = _as_nonempty_text(correction.get("corrected_text"))
    if corrected_text:
        return corrected_text
    return fingerprint[:60]


def _adopted_correction_source_refs(correction: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    correction_id = _as_nonempty_text(correction.get("correction_id")) or fingerprint
    return {
        "candidate_id": f"adopted-correction:{correction_id}",
        "correction_id": correction_id,
        "delta_fingerprint": fingerprint,
        "source": "adopted_correction",
        "artifact_id": _as_nonempty_text(correction.get("artifact_id")) or "",
        "source_message_id": _as_nonempty_text(correction.get("source_message_id")) or "",
        "session_id": _as_nonempty_text(correction.get("session_id")) or "",
        "activated_at": _as_nonempty_text(correction.get("activated_at")) or "",
    }


def _preference_review_source_ref(preference: dict[str, Any]) -> dict[str, Any] | None:
    refs = preference.get("reviewed_candidate_source_refs")
    if isinstance(refs, list):
        dict_refs = [ref for ref in refs if isinstance(ref, dict)]
        for ref in reversed(dict_refs):
            if _as_nonempty_text(ref.get("reason_note")) or _as_nonempty_text(ref.get("session_title")):
                return ref
        if dict_refs:
            return dict_refs[-1]

    source_refs = preference.get("source_refs")
    if isinstance(source_refs, dict):
        return source_refs
    return None


def _preference_exists_for_fingerprint(preference_store: Any, fingerprint: str) -> bool:
    find_by_fingerprint = getattr(preference_store, "find_by_fingerprint", None)
    if callable(find_by_fingerprint):
        existing = find_by_fingerprint(fingerprint)
        if isinstance(existing, list):
            return bool(existing)
        return existing is not None

    list_all = getattr(preference_store, "list_all", None)
    if not callable(list_all):
        return False
    try:
        preferences = list_all(limit=1000)
    except TypeError:
        preferences = list_all()
    return any(
        str(preference.get("delta_fingerprint") or "") == fingerprint
        for preference in preferences
        if isinstance(preference, dict)
    )


def _is_highly_reliable_preference(preference: dict[str, Any]) -> bool:
    return is_highly_reliable_preference(preference)


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
            pref_copy = enrich_preference_reliability(pref, per_pref_stats)
            source_ref = _preference_review_source_ref(pref_copy)
            if source_ref is not None:
                review_reason_note = _as_nonempty_text(source_ref.get("reason_note"))
                source_session_title = _as_nonempty_text(source_ref.get("session_title"))
                if review_reason_note:
                    pref_copy["review_reason_note"] = review_reason_note
                if source_session_title:
                    pref_copy["source_session_title"] = source_session_title
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

        highly_reliable_by_pref_id = {
            str(pref_copy.get("preference_id", "")): pref_copy.get("is_highly_reliable") is True
            for pref_copy in enriched
        }
        for pref_copy in enriched:
            pref_id = str(pref_copy.get("preference_id", ""))
            conflicting = conflict_map.get(pref_id, [])
            has_conflict = len(conflicting) > 0
            if not has_conflict:
                conflict_severity = "none"
            elif highly_reliable_by_pref_id.get(pref_id, False) or any(
                highly_reliable_by_pref_id.get(conflicting_pref_id, False)
                for conflicting_pref_id in conflicting
            ):
                conflict_severity = "high"
            else:
                conflict_severity = "normal"
            pref_copy["conflict_info"] = {
                "has_conflict": has_conflict,
                "conflicting_preference_ids": conflicting,
                "conflict_severity": conflict_severity,
            }

        transition_actions = {"preference_activated", "preference_paused", "preference_rejected"}
        try:
            system_records = self.task_logger.iter_session_records("system")
            latest_reason: dict[str, str] = {}
            for record in system_records:
                if record.get("action") not in transition_actions:
                    continue
                detail = record.get("detail") or {}
                preference_id = detail.get("preference_id") if isinstance(detail, dict) else None
                transition_reason = _as_nonempty_text(detail.get("transition_reason")) if isinstance(detail, dict) else None
                if preference_id and transition_reason:
                    latest_reason[str(preference_id)] = transition_reason
        except Exception:
            latest_reason = {}
        for pref_copy in enriched:
            preference_id = pref_copy.get("preference_id")
            if preference_id and str(preference_id) in latest_reason:
                pref_copy["last_transition_reason"] = latest_reason[str(preference_id)]

        total_applied = 0
        total_corrected = 0
        high_quality_active_count = 0
        highly_reliable_active_count = 0
        high_severity_conflict_count = 0
        low_reliability_active_count = 0
        for pref_copy in enriched:
            if pref_copy.get("status") != "active":
                continue
            quality_info = pref_copy.get("quality_info")
            if isinstance(quality_info, dict) and quality_info.get("is_high_quality") is True:
                high_quality_active_count += 1
            if pref_copy.get("is_highly_reliable") is True:
                highly_reliable_active_count += 1
            conflict_info = pref_copy.get("conflict_info")
            if isinstance(conflict_info, dict) and conflict_info.get("conflict_severity") == "high":
                high_severity_conflict_count += 1
            reliability_stats_for_lr = pref_copy.get("reliability_stats")
            if isinstance(reliability_stats_for_lr, dict):
                lr_applied = reliability_stats_for_lr.get("applied_count", 0)
                if (
                    isinstance(lr_applied, int)
                    and lr_applied >= 3
                    and pref_copy.get("is_highly_reliable") is not True
                ):
                    low_reliability_active_count += 1
            reliability_stats = pref_copy.get("reliability_stats")
            if not isinstance(reliability_stats, dict):
                continue
            applied_count = reliability_stats.get("applied_count", 0)
            corrected_count = reliability_stats.get("corrected_count", 0)
            total_applied += applied_count if isinstance(applied_count, int) else 0
            total_corrected += corrected_count if isinstance(corrected_count, int) else 0

        return {
            "ok": True,
            "preferences": enriched,
            "active_count": sum(1 for p in enriched if p.get("status") == "active"),
            "candidate_count": sum(1 for p in enriched if p.get("status") == "candidate"),
            "paused_count": sum(1 for p in enriched if p.get("status") == "paused"),
            "total_applied": total_applied,
            "total_corrected": total_corrected,
            "high_quality_active_count": high_quality_active_count,
            "highly_reliable_active_count": highly_reliable_active_count,
            "high_severity_conflict_count": high_severity_conflict_count,
            "low_reliability_active_count": low_reliability_active_count,
        }

    def get_preference_audit(self) -> dict[str, Any]:
        all_prefs = self.preference_store.list_all()
        counts: dict[str, int] = {}
        for pref in all_prefs:
            status = str(pref.get("status") or "unknown")
            counts[status] = counts.get(status, 0) + 1
        active_prefs = [
            p for p in all_prefs
            if p.get("status") == "active" and str(p.get("description") or "").strip()
        ]
        conflict_pair_count = 0
        for i, preference_a in enumerate(active_prefs):
            for preference_b in active_prefs[i + 1:]:
                description_a = str(preference_a.get("description") or "").strip()
                description_b = str(preference_b.get("description") or "").strip()
                if _jaccard_word_similarity(description_a, description_b) > 0.7:
                    conflict_pair_count += 1
        adopted_corrections = self.correction_store.find_adopted_corrections()
        available_to_sync_count = 0
        for correction in adopted_corrections:
            fingerprint = _as_nonempty_text(correction.get("delta_fingerprint"))
            if fingerprint is None:
                continue
            if not _preference_exists_for_fingerprint(self.preference_store, fingerprint):
                available_to_sync_count += 1
        return {
            "total": len(all_prefs),
            "by_status": counts,
            "conflict_pair_count": conflict_pair_count,
            "adopted_corrections_count": len(adopted_corrections),
            "available_to_sync_count": available_to_sync_count,
        }

    def sync_adopted_corrections_to_candidates(self) -> dict[str, Any]:
        adopted_corrections = self.correction_store.find_adopted_corrections()
        synced_count = 0
        skipped_count = 0

        for correction in adopted_corrections:
            fingerprint = _as_nonempty_text(correction.get("delta_fingerprint"))
            if fingerprint is None:
                skipped_count += 1
                continue
            if _preference_exists_for_fingerprint(self.preference_store, fingerprint):
                skipped_count += 1
                continue

            self.preference_store.record_reviewed_candidate_preference(
                delta_fingerprint=fingerprint,
                candidate_family=str(correction.get("pattern_family") or CandidateFamily.CORRECTION_REWRITE),
                description=_adopted_correction_description(correction, fingerprint),
                source_refs=_adopted_correction_source_refs(correction, fingerprint),
                original_snippet=_as_nonempty_text(correction.get("original_text")),
                corrected_snippet=_as_nonempty_text(correction.get("corrected_text")),
            )
            synced_count += 1

        task_logger = getattr(self, "task_logger", None)
        log = getattr(task_logger, "log", None)
        if callable(log):
            log(
                session_id="system",
                action="adopted_corrections_synced_to_candidates",
                detail={
                    "synced_count": synced_count,
                    "skipped_count": skipped_count,
                },
            )
        return {"ok": True, "synced_count": synced_count, "skipped_count": skipped_count}

    def activate_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        preference_id = self._normalize_optional_text(payload.get("preference_id"))
        if not preference_id:
            raise WebApiError(400, "활성화할 선호 ID가 필요합니다.")
        transition_reason = self._normalize_optional_text(payload.get("transition_reason"))
        result = self.preference_store.activate_preference(preference_id)
        if result is None:
            raise WebApiError(404, "해당 선호를 찾을 수 없습니다.")
        detail: dict[str, Any] = {"preference_id": preference_id}
        if transition_reason:
            detail["transition_reason"] = transition_reason
        self.task_logger.log(session_id="system", action="preference_activated", detail=detail)
        return {"ok": True, "preference": result}

    def pause_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        preference_id = self._normalize_optional_text(payload.get("preference_id"))
        if not preference_id:
            raise WebApiError(400, "일시중지할 선호 ID가 필요합니다.")
        transition_reason = self._normalize_optional_text(payload.get("transition_reason"))
        result = self.preference_store.pause_preference(preference_id)
        if result is None:
            raise WebApiError(404, "해당 선호를 찾을 수 없습니다.")
        detail: dict[str, Any] = {"preference_id": preference_id}
        if transition_reason:
            detail["transition_reason"] = transition_reason
        self.task_logger.log(session_id="system", action="preference_paused", detail=detail)
        return {"ok": True, "preference": result}

    def reject_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        preference_id = self._normalize_optional_text(payload.get("preference_id"))
        if not preference_id:
            raise WebApiError(400, "거부할 선호 ID가 필요합니다.")
        transition_reason = self._normalize_optional_text(payload.get("transition_reason"))
        result = self.preference_store.reject_preference(preference_id)
        if result is None:
            raise WebApiError(404, "해당 선호를 찾을 수 없습니다.")
        detail: dict[str, Any] = {"preference_id": preference_id}
        if transition_reason:
            detail["transition_reason"] = transition_reason
        self.task_logger.log(session_id="system", action="preference_rejected", detail=detail)
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

    def record_explicit_preference_correction(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = str(payload.get("session_id") or "").strip()
        message_id = str(payload.get("message_id") or "").strip()
        fingerprint = str(payload.get("fingerprint") or "").strip()
        if not session_id or not message_id or not fingerprint:
            return {"ok": False, "error": "session_id, message_id, fingerprint 필수"}
        recorded = self.session_store.record_preference_explicit_correction(
            session_id,
            message_id=message_id,
            fingerprint=fingerprint,
        )
        return {"ok": recorded}
