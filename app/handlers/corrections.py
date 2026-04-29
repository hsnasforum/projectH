"""Correction pattern handler methods extracted from AggregateHandlerMixin."""
from __future__ import annotations

from typing import Any

from app.errors import WebApiError
from core.contracts import CandidateFamily


def _first_correction_snippets(
    corrections: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    for correction in corrections:
        original_text = correction.get("original_text") or ""
        corrected_text = correction.get("corrected_text") or ""
        if original_text and corrected_text:
            return str(original_text)[:400], str(corrected_text)[:400]
    return None, None


class CorrectionHandlerMixin:
    """Correction pattern CRUD and summary methods."""

    def get_correction_summary(self) -> dict[str, Any]:
        """전체 correction store의 요약 통계를 반환한다."""
        all_corrections = self.correction_store._scan_all()
        total = len(all_corrections)
        by_status: dict[str, int] = {}
        for record in all_corrections:
            status = str(record.get("status") or "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        recurring = self.correction_store.find_recurring_patterns()
        top_raw = sorted(
            recurring,
            key=lambda x: int(x.get("recurrence_count") or 1),
            reverse=True,
        )[:5]
        top_fps: list[dict[str, Any]] = []
        for rec in top_raw:
            fp = str(rec.get("delta_fingerprint") or "")
            if not fp:
                continue
            orig, corr = _first_correction_snippets(rec.get("corrections") or [])
            entry: dict[str, Any] = {
                "delta_fingerprint": fp,
                "recurrence_count": int(rec.get("recurrence_count") or 1),
            }
            if orig:
                entry["original_snippet"] = orig
            if corr:
                entry["corrected_snippet"] = corr
            top_fps.append(entry)

        return {
            "ok": True,
            "total": total,
            "by_status": by_status,
            "top_recurring_fingerprints": top_fps,
        }

    def get_correction_list(
        self,
        query: str | None = None,
        status: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        corrections = self.correction_store.list_filtered(
            query=query, status=status, limit=limit
        )
        preference_store = getattr(self, "preference_store", None)
        active_preferences = (
            preference_store.get_active_preferences()
            if preference_store is not None
            else []
        )
        active_fps = {
            p.get("delta_fingerprint")
            for p in active_preferences
            if p.get("delta_fingerprint")
        }
        result = []
        for c in corrections:
            item = dict(c)
            if c.get("delta_fingerprint") in active_fps:
                item["has_active_preference"] = True
            result.append(item)
        return {"ok": True, "corrections": result}

    def confirm_correction_pattern(self, payload: dict[str, Any]) -> dict[str, Any]:
        delta_fingerprint = str(payload.get("delta_fingerprint") or "").strip()
        if not delta_fingerprint:
            raise WebApiError(400, "delta_fingerprint 값이 필요합니다.")
        confirmed = self.correction_store.confirm_by_fingerprint(delta_fingerprint)
        return {"ok": True, "confirmed_count": len(confirmed)}

    def dismiss_correction_pattern(self, payload: dict[str, Any]) -> dict[str, Any]:
        delta_fingerprint = str(payload.get("delta_fingerprint") or "").strip()
        if not delta_fingerprint:
            raise WebApiError(400, "delta_fingerprint 값이 필요합니다.")
        dismissed = self.correction_store.dismiss_by_fingerprint(delta_fingerprint)
        return {"ok": True, "dismissed_count": len(dismissed)}

    def promote_correction_pattern(self, payload: dict[str, Any]) -> dict[str, Any]:
        delta_fingerprint = str(payload.get("delta_fingerprint") or "").strip()
        if not delta_fingerprint:
            raise WebApiError(400, "delta_fingerprint 값이 필요합니다.")
        promoted = self.correction_store.promote_by_fingerprint(delta_fingerprint)
        for correction in promoted:
            first_original, first_corrected = _first_correction_snippets([correction])
            self.preference_store.record_reviewed_candidate_preference(
                delta_fingerprint=delta_fingerprint,
                candidate_family=str(
                    correction.get("pattern_family") or CandidateFamily.CORRECTION_REWRITE
                ),
                description=delta_fingerprint[:60],
                source_refs={
                    "correction_id": str(correction.get("correction_id") or ""),
                    "artifact_id": str(correction.get("artifact_id") or ""),
                    "session_id": str(correction.get("session_id") or ""),
                    "source_message_id": str(
                        correction.get("source_message_id") or "global"
                    ),
                    "promotion_source": "promote_pattern",
                },
                original_snippet=first_original,
                corrected_snippet=first_corrected,
            )
        return {"ok": True, "promoted_count": len(promoted)}
