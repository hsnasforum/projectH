from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from pipeline_runtime.lane_surface import (
    pane_text_has_busy_indicator,
    pane_text_has_input_cursor,
    pane_text_is_idle,
)


class WatcherDispatchQueue:
    def __init__(
        self,
        *,
        lane_input_defer_cooldown_sec: float,
        capture_pane_text: Callable[[str], str],
        send_keys: Callable[[str, str, str], bool],
        get_path_sig: Callable[[Path], str],
        role_owner: Callable[[str], str | None],
        log_raw: Callable[[str, str, str, dict[str, object]], None],
        append_runtime_event: Callable[[str, dict[str, object]], None],
        get_active_control_signal: Callable[[], Any],
        is_active_control: Callable[[Path, str], bool],
    ) -> None:
        self.pending_notifications: dict[str, dict[str, object]] = {}
        self.last_lane_input_defer_at: dict[str, float] = {}
        self.lane_input_defer_cooldown_sec = lane_input_defer_cooldown_sec
        self._capture_pane_text = capture_pane_text
        self._send_keys = send_keys
        self._get_path_sig = get_path_sig
        self._role_owner = role_owner
        self._log_raw = log_raw
        self._append_runtime_event = append_runtime_event
        self._get_active_control_signal = get_active_control_signal
        self._is_active_control = is_active_control

    def lane_prompt_readiness(self, target: str) -> tuple[bool, str]:
        try:
            snapshot = self._capture_pane_text(target)
        except Exception:
            return False, "pane_capture_failed"
        if pane_text_is_idle(snapshot):
            return True, ""
        if not snapshot.strip():
            return False, "pane_blank"
        if pane_text_has_busy_indicator(snapshot):
            return False, "lane_busy"
        if pane_text_has_input_cursor(snapshot):
            return False, "prompt_not_stable"
        return False, "prompt_not_visible"

    def emit_lane_input_deferred(
        self,
        *,
        key: str,
        lane: str,
        path: Path,
        reason: str,
        defer_reason: str,
        control_seq: int,
        notify_kind: str,
    ) -> None:
        now = time.time()
        if now - self.last_lane_input_defer_at.get(key, 0.0) < self.lane_input_defer_cooldown_sec:
            return
        self.last_lane_input_defer_at[key] = now
        payload = {
            "lane": lane,
            "reason": reason,
            "defer_reason": defer_reason,
            "control_file": str(path.name),
            "control_seq": control_seq,
            "notify_kind": notify_kind,
        }
        self._log_raw("lane_input_deferred", str(path), "turn_signal", payload)
        self._append_runtime_event("lane_input_deferred", payload)

    def dispatch_runtime_notification(
        self,
        *,
        pending_key: str,
        notify_kind: str,
        lane_role: str,
        reason: str,
        prompt: str,
        prompt_path: Path,
        target: str,
        pane_type: str,
        control_seq: int = -1,
        expected_status: str = "",
        expected_control_path: str = "",
        expected_control_seq: int = -1,
        require_active_control: bool = False,
        from_pending: bool = False,
    ) -> bool:
        ready, defer_reason = self.lane_prompt_readiness(target)
        if not ready:
            self.pending_notifications[pending_key] = {
                "notify_kind": notify_kind,
                "lane_role": lane_role,
                "reason": reason,
                "prompt": prompt,
                "prompt_path": str(prompt_path),
                "target": target,
                "pane_type": pane_type,
                "control_seq": control_seq,
                "expected_status": expected_status,
                "expected_control_path": expected_control_path,
                "expected_control_seq": expected_control_seq,
                "require_active_control": require_active_control,
                "sig": self._get_path_sig(prompt_path),
            }
            self.emit_lane_input_deferred(
                key=pending_key,
                lane=self._role_owner(lane_role) or lane_role,
                path=prompt_path,
                reason=reason,
                defer_reason=defer_reason,
                control_seq=control_seq,
                notify_kind=notify_kind,
            )
            return False

        ok = self._send_keys(target, prompt, pane_type)
        if ok:
            self.pending_notifications.pop(pending_key, None)
            self.last_lane_input_defer_at.pop(pending_key, None)
            return True

        if not from_pending:
            self.pending_notifications[pending_key] = {
                "notify_kind": notify_kind,
                "lane_role": lane_role,
                "reason": reason,
                "prompt": prompt,
                "prompt_path": str(prompt_path),
                "target": target,
                "pane_type": pane_type,
                "control_seq": control_seq,
                "expected_status": expected_status,
                "expected_control_path": expected_control_path,
                "expected_control_seq": expected_control_seq,
                "require_active_control": require_active_control,
                "sig": self._get_path_sig(prompt_path),
            }
        self.emit_lane_input_deferred(
            key=pending_key,
            lane=self._role_owner(lane_role) or lane_role,
            path=prompt_path,
            reason=reason,
            defer_reason="dispatch_window_blocked",
            control_seq=control_seq,
            notify_kind=notify_kind,
        )
        return False

    def pending_notification_matches_control(
        self,
        pending: dict[str, object],
        active_control: Any,
    ) -> bool:
        expected_control_path = str(pending.get("expected_control_path") or "").strip()
        expected_status = str(pending.get("expected_status") or "").strip()
        expected_control_seq = int(pending.get("expected_control_seq") or -1)
        if not expected_control_path and not expected_status and expected_control_seq < 0:
            return True
        if active_control is None:
            return False
        if expected_control_path and active_control.path.name != expected_control_path:
            return False
        if expected_status and active_control.status != expected_status:
            return False
        if expected_control_seq >= 0 and active_control.control_seq != expected_control_seq:
            return False
        return True

    def flush_pending_lane_notifications(self) -> None:
        if not self.pending_notifications:
            return
        active_control = self._get_active_control_signal()
        for pending_key, pending in list(self.pending_notifications.items()):
            prompt_path = Path(str(pending.get("prompt_path") or ""))
            if not prompt_path:
                self.pending_notifications.pop(pending_key, None)
                continue
            expected_sig = str(pending.get("sig") or "")
            if expected_sig and self._get_path_sig(prompt_path) != expected_sig:
                self.pending_notifications.pop(pending_key, None)
                self.last_lane_input_defer_at.pop(pending_key, None)
                continue
            expected_status = str(pending.get("expected_status") or "")
            require_active_control = bool(pending.get("require_active_control"))
            if not self.pending_notification_matches_control(pending, active_control):
                self.pending_notifications.pop(pending_key, None)
                self.last_lane_input_defer_at.pop(pending_key, None)
                self._log_raw(
                    "lane_input_deferred_dropped",
                    str(prompt_path),
                    "turn_signal",
                    {
                        "notify_kind": str(pending.get("notify_kind") or ""),
                        "reason": "control_mismatch",
                        "active_control": active_control.kind if active_control else "none",
                    },
                )
                continue
            if require_active_control and expected_status and not self._is_active_control(prompt_path, expected_status):
                self.pending_notifications.pop(pending_key, None)
                self.last_lane_input_defer_at.pop(pending_key, None)
                continue
            self.dispatch_runtime_notification(
                pending_key=pending_key,
                notify_kind=str(pending.get("notify_kind") or ""),
                lane_role=str(pending.get("lane_role") or ""),
                reason=str(pending.get("reason") or ""),
                prompt=str(pending.get("prompt") or ""),
                prompt_path=prompt_path,
                target=str(pending.get("target") or ""),
                pane_type=str(pending.get("pane_type") or "codex"),
                control_seq=int(pending.get("control_seq") or -1),
                expected_status=expected_status,
                expected_control_path=str(pending.get("expected_control_path") or ""),
                expected_control_seq=int(pending.get("expected_control_seq") or -1),
                require_active_control=require_active_control,
                from_pending=True,
            )
