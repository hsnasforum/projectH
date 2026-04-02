from __future__ import annotations

from typing import Any

from app.errors import WebApiError


class PreferenceHandlerMixin:
    """Preference management methods extracted from WebAppService."""

    def list_preferences_payload(self) -> dict[str, Any]:
        all_prefs = self.preference_store.list_all()
        return {
            "ok": True,
            "preferences": all_prefs,
            "active_count": sum(1 for p in all_prefs if p.get("status") == "active"),
            "candidate_count": sum(1 for p in all_prefs if p.get("status") == "candidate"),
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
