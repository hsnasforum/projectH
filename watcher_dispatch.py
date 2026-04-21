from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from pipeline_runtime.lane_surface import (
    pane_text_has_busy_indicator,
    pane_text_has_input_cursor,
    pane_text_is_idle,
)

SIGNAL_MISMATCH_DROP_NOTIFY_KINDS = frozenset({"claude_handoff"})


@dataclass(frozen=True)
class DispatchIntent:
    pending_key: str
    notify_kind: str
    lane_role: str
    reason: str
    prompt: str
    prompt_path: Path
    target: str
    pane_type: str
    functional_role: str = ""
    lane_id: str = ""
    agent_kind: str = ""
    model_alias: str | None = None
    control_seq: int = -1
    expected_status: str = ""
    expected_control_path: str = ""
    expected_control_seq: int = -1
    require_active_control: bool = False


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
        lane_id: str,
        functional_role: str,
        agent_kind: str,
        model_alias: str | None,
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
            "lane_id": lane_id,
            "functional_role": functional_role,
            "agent_kind": agent_kind,
            "model_alias": model_alias,
            "lane_role": functional_role,
            "reason": reason,
            "defer_reason": defer_reason,
            "control_file": str(path.name),
            "control_seq": control_seq,
            "notify_kind": notify_kind,
        }
        self._log_raw("lane_input_deferred", str(path), "turn_signal", payload)
        self._append_runtime_event("lane_input_deferred", payload)

    def _pending_record(self, intent: DispatchIntent) -> dict[str, object]:
        return {
            "notify_kind": intent.notify_kind,
            "lane_role": intent.lane_role,
            "functional_role": intent.functional_role or intent.lane_role,
            "lane_id": intent.lane_id,
            "agent_kind": intent.agent_kind,
            "model_alias": intent.model_alias,
            "reason": intent.reason,
            "prompt": intent.prompt,
            "prompt_path": str(intent.prompt_path),
            "target": intent.target,
            "pane_type": intent.pane_type,
            "control_seq": intent.control_seq,
            "expected_status": intent.expected_status,
            "expected_control_path": intent.expected_control_path,
            "expected_control_seq": intent.expected_control_seq,
            "require_active_control": intent.require_active_control,
            "sig": self._get_path_sig(intent.prompt_path),
        }

    def _intent_from_pending(
        self,
        pending_key: str,
        pending: dict[str, object],
    ) -> DispatchIntent:
        return DispatchIntent(
            pending_key=pending_key,
            notify_kind=str(pending.get("notify_kind") or ""),
            lane_role=str(pending.get("lane_role") or ""),
            functional_role=str(pending.get("functional_role") or pending.get("lane_role") or ""),
            lane_id=str(pending.get("lane_id") or ""),
            agent_kind=str(pending.get("agent_kind") or ""),
            model_alias=(
                str(pending.get("model_alias"))
                if pending.get("model_alias") is not None
                else None
            ),
            reason=str(pending.get("reason") or ""),
            prompt=str(pending.get("prompt") or ""),
            prompt_path=Path(str(pending.get("prompt_path") or "")),
            target=str(pending.get("target") or ""),
            pane_type=str(pending.get("pane_type") or "codex"),
            control_seq=int(pending.get("control_seq") or -1),
            expected_status=str(pending.get("expected_status") or ""),
            expected_control_path=str(pending.get("expected_control_path") or ""),
            expected_control_seq=int(pending.get("expected_control_seq") or -1),
            require_active_control=bool(pending.get("require_active_control")),
        )

    def dispatch(self, intent: DispatchIntent, *, from_pending: bool = False) -> bool:
        ready, defer_reason = self.lane_prompt_readiness(intent.target)
        if not ready:
            self.pending_notifications[intent.pending_key] = self._pending_record(intent)
            self.emit_lane_input_deferred(
                key=intent.pending_key,
                lane=self._role_owner(intent.functional_role or intent.lane_role) or intent.lane_role,
                lane_id=intent.lane_id,
                functional_role=intent.functional_role or intent.lane_role,
                agent_kind=intent.agent_kind,
                model_alias=intent.model_alias,
                path=intent.prompt_path,
                reason=intent.reason,
                defer_reason=defer_reason,
                control_seq=intent.control_seq,
                notify_kind=intent.notify_kind,
            )
            return False

        ok = self._send_keys(intent.target, intent.prompt, intent.pane_type)
        if ok:
            self.pending_notifications.pop(intent.pending_key, None)
            self.last_lane_input_defer_at.pop(intent.pending_key, None)
            return True

        if not from_pending:
            self.pending_notifications[intent.pending_key] = self._pending_record(intent)
        self.emit_lane_input_deferred(
            key=intent.pending_key,
            lane=self._role_owner(intent.functional_role or intent.lane_role) or intent.lane_role,
            lane_id=intent.lane_id,
            functional_role=intent.functional_role or intent.lane_role,
            agent_kind=intent.agent_kind,
            model_alias=intent.model_alias,
            path=intent.prompt_path,
            reason=intent.reason,
            defer_reason="dispatch_window_blocked",
            control_seq=intent.control_seq,
            notify_kind=intent.notify_kind,
        )
        return False

    def pending_notification_matches_control(
        self,
        pending: dict[str, object],
        active_control: Any,
    ) -> bool:
        return self.pending_notification_control_mismatch_reason(pending, active_control) is None

    def pending_notification_control_mismatch_reason(
        self,
        pending: dict[str, object],
        active_control: Any,
    ) -> str | None:
        expected_control_path = str(pending.get("expected_control_path") or "").strip()
        expected_status = str(pending.get("expected_status") or "").strip()
        expected_control_seq = int(pending.get("expected_control_seq") or -1)
        if not expected_control_path and not expected_status and expected_control_seq < 0:
            return None
        if active_control is None:
            return "active_control_missing"
        if expected_control_path and active_control.path.name != expected_control_path:
            return "control_file_drift"
        if expected_status and active_control.status != expected_status:
            return "control_status_drift"
        if expected_control_seq >= 0 and active_control.control_seq != expected_control_seq:
            return "control_seq_drift"
        if self._pending_signal_mismatch_reason(pending) is not None:
            return "signal_mismatch"
        return None

    def _pending_signal_mismatch_reason(self, pending: dict[str, object]) -> str | None:
        notify_kind = str(pending.get("notify_kind") or "").strip()
        if notify_kind not in SIGNAL_MISMATCH_DROP_NOTIFY_KINDS:
            return None

        prompt_path_raw = str(pending.get("prompt_path") or "").strip()
        if not prompt_path_raw:
            return None
        control_seq = int(pending.get("expected_control_seq") or pending.get("control_seq") or -1)
        if control_seq < 0:
            return None

        lane_hint = str(pending.get("agent_kind") or "").strip().lower()
        if not lane_hint:
            lane_hint = {
                "implement": "claude",
                "verify": "codex",
                "advisory": "gemini",
            }.get(str(pending.get("functional_role") or pending.get("lane_role") or "").strip(), "")
        if not lane_hint:
            return None

        prompt_path = Path(prompt_path_raw)
        base_dir = prompt_path.parent
        current_run_path = base_dir / "current_run.json"
        try:
            current_run = json.loads(current_run_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        events_path_raw = str(current_run.get("events_path") or "").strip()
        if not events_path_raw:
            return None
        events_path = Path(events_path_raw)
        if not events_path.is_absolute():
            events_path = base_dir.parent / events_path

        lane_name = lane_hint.capitalize()
        latest_lane_signal = ""
        lane_signal_at = ""
        try:
            event_lines = events_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return None
        for raw in reversed(event_lines):
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if str(event.get("source") or "") != "supervisor":
                continue
            payload = dict(event.get("payload") or {})
            if str(payload.get("lane") or "") != lane_name:
                continue
            event_type = str(event.get("event_type") or "")
            if event_type not in {
                "lane_working",
                "lane_ready",
                "lane_broken",
                "lane_booting",
                "lane_spawned",
            }:
                continue
            latest_lane_signal = event_type
            lane_signal_at = str(event.get("ts") or "")
            break
        if latest_lane_signal != "lane_working":
            return None

        wrapper_path = events_path.parent / "wrapper-events" / f"{lane_name.lower()}.jsonl"
        try:
            wrapper_lines = wrapper_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return None

        heartbeat_count = 0
        dispatch_seen_count = 0
        task_accepted_count = 0
        # Treat the current control_seq as the dispatch-cycle window for queue-side corroboration.
        for raw in wrapper_lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if str(event.get("lane") or lane_name) != lane_name:
                continue
            event_ts = str(event.get("ts") or "")
            if lane_signal_at and event_ts and event_ts < lane_signal_at:
                continue
            event_type = str(event.get("event_type") or "")
            if event_type == "HEARTBEAT":
                heartbeat_count += 1
                continue
            payload = dict(event.get("payload") or {})
            if int(payload.get("control_seq") or -1) != control_seq:
                continue
            if event_type == "DISPATCH_SEEN":
                dispatch_seen_count += 1
            elif event_type == "TASK_ACCEPTED":
                task_accepted_count += 1
        if heartbeat_count and dispatch_seen_count == 0 and task_accepted_count == 0:
            return "signal_mismatch"
        return None

    def _control_mismatch_payload(
        self,
        pending: dict[str, object],
        *,
        prompt_path: Path,
        active_control: Any,
        reason_code: str,
    ) -> dict[str, object]:
        return {
            "notify_kind": str(pending.get("notify_kind") or ""),
            "reason": "control_mismatch",
            "reason_code": reason_code,
            "functional_role": str(pending.get("functional_role") or pending.get("lane_role") or ""),
            "lane_role": str(pending.get("lane_role") or ""),
            "lane_id": str(pending.get("lane_id") or ""),
            "agent_kind": str(pending.get("agent_kind") or ""),
            "model_alias": pending.get("model_alias"),
            "expected_control_seq": int(pending.get("expected_control_seq") or -1),
            "active_control_seq": int(active_control.control_seq) if active_control else -1,
            "expected_prompt_path": str(prompt_path),
            "active_prompt_path": str(active_control.path) if active_control else "",
            "expected_status": str(pending.get("expected_status") or ""),
            "active_status": str(active_control.status) if active_control else "",
            "active_control": active_control.kind if active_control else "none",
        }

    def flush_pending(self) -> None:
        if not self.pending_notifications:
            return
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
            active_control = self._get_active_control_signal()
            expected_status = str(pending.get("expected_status") or "")
            require_active_control = bool(pending.get("require_active_control"))
            mismatch_reason = self.pending_notification_control_mismatch_reason(pending, active_control)
            if mismatch_reason is not None:
                self.pending_notifications.pop(pending_key, None)
                self.last_lane_input_defer_at.pop(pending_key, None)
                payload = self._control_mismatch_payload(
                    pending,
                    prompt_path=prompt_path,
                    active_control=active_control,
                    reason_code=mismatch_reason,
                )
                self._log_raw(
                    "lane_input_deferred_dropped",
                    str(prompt_path),
                    "turn_signal",
                    payload,
                )
                self._append_runtime_event("lane_input_deferred_dropped", payload)
                continue
            if require_active_control and expected_status and not self._is_active_control(prompt_path, expected_status):
                self.pending_notifications.pop(pending_key, None)
                self.last_lane_input_defer_at.pop(pending_key, None)
                continue
            self.dispatch(self._intent_from_pending(pending_key, pending), from_pending=True)
