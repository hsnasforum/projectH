from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from pipeline_runtime.role_routes import ADVISORY_RECOVERY_NOTIFY, normalize_notify_kind
from pipeline_runtime.schema import atomic_write_text, control_seq_value
from watcher_state import WatcherTurnState

log = logging.getLogger("watcher")

ADVISORY_RECOVERY_FOLLOWUP_LIMIT = 2


class ControlSignalLike(Protocol):
    path: Path
    sig: str
    mtime: float
    control_seq: int


@dataclass
class StaleAdvisoryRecovery:
    advisory_request_path: Path
    run_events_path: Path
    current_turn_state: Callable[[], WatcherTurnState]
    turn_entered_at: Callable[[], float]
    turn_active_control_seq: Callable[[], int]
    advisory_retry_sec: Callable[[], float]
    advisory_recovery_sec: Callable[[], float]
    dry_run: Callable[[], bool]
    advisory_enabled: Callable[[], bool]
    get_pending_operator_mtime: Callable[[], float]
    get_active_control: Callable[[], ControlSignalLike | None]
    control_signal_for_slot: Callable[[ControlSignalLike | None, str, str], ControlSignalLike | None]
    advisory_advice_is_current_for_request: Callable[[int], bool]
    prompt_owner: Callable[[str], Optional[str]]
    prompt_pane_target: Callable[[str], str]
    lane_prompt_readiness: Callable[[str], tuple[bool, str]]
    pending_notifications: Callable[[], Iterable[Mapping[str, object]]]
    log_raw: Callable[[str, str, str, dict[str, object]], None]
    emit_event: Callable[[str, dict[str, object]], None]
    notify_advisory_owner: Callable[[str], None]
    notify_verify_advisory_recovery: Callable[[str, dict[str, object]], None]
    cancel_advisory_lane_if_busy: Callable[..., bool]
    clear_implement_blocked: Callable[[str], None]
    transition_turn: Callable[..., None]
    read_control_seq_from_path: Callable[[Path], int]
    read_status_from_path: Callable[[Path], Optional[str]]
    get_path_sig: Callable[[Path], str]
    set_last_advisory_request_sig: Callable[[str], None]
    capture_pane_text: Callable[[str], str]
    pane_text_has_busy_indicator: Callable[[str, str], bool]
    pane_text_busy_age_seconds: Callable[[str, str], Optional[int]]
    now_fn: Callable[[], float]
    last_retry_sig: str = ""
    last_retry_at: float = 0.0
    last_recovery_sig: str = ""
    last_recovery_at: float = 0.0

    def retry_if_idle(self) -> None:
        if self.current_turn_state() != WatcherTurnState.ADVISORY_ACTIVE:
            return
        if not self.advisory_enabled():
            return
        if self.get_pending_operator_mtime() > 0.0:
            return
        active_control = self.get_active_control()
        request_control = self.control_signal_for_slot(
            active_control,
            "advisory_request",
            "request_open",
        )
        if request_control is None:
            return

        request_sig = request_control.sig
        if not request_sig:
            return
        request_seq = request_control.control_seq
        if request_seq >= 0 and request_seq < self.turn_active_control_seq():
            return
        if self.advisory_advice_is_current_for_request(request_seq):
            return

        now = self.now_fn()
        if request_sig == self.last_retry_sig:
            if now - self.last_retry_at < self.advisory_retry_sec():
                return
        else:
            request_started_at = max(self.turn_entered_at(), request_control.mtime)
            if now - request_started_at < self.advisory_retry_sec():
                return

        target = self.prompt_pane_target("advisory")
        if not target:
            return
        ready, _defer_reason = self.lane_prompt_readiness(target)
        if not ready:
            return

        payload = {
            "reason": "advisory_idle_retry",
            "control_file": str(request_control.path.name),
            "control_seq": request_seq,
            "turn_state": self.current_turn_state().value,
            "target": target,
        }
        self.log_raw("advisory_idle_retry", str(request_control.path), "turn_signal", payload)
        self.emit_event("advisory_idle_retry", payload)
        self.last_retry_sig = request_sig
        self.last_retry_at = now
        self.notify_advisory_owner("advisory_idle_retry")

    def stale_recovery_marker(self) -> Optional[dict[str, object]]:
        if self.current_turn_state() != WatcherTurnState.ADVISORY_ACTIVE:
            return None
        if self.get_pending_operator_mtime() > 0.0:
            return None
        active_control = self.get_active_control()
        request_control = self.control_signal_for_slot(
            active_control,
            "advisory_request",
            "request_open",
        )
        if request_control is None:
            return None

        request_sig = request_control.sig
        if not request_sig:
            return None
        if request_sig == self.last_recovery_sig:
            return None

        request_seq = request_control.control_seq
        if request_seq >= 0 and request_seq < self.turn_active_control_seq():
            return None
        if self.advisory_advice_is_current_for_request(request_seq):
            return None

        now = self.now_fn()
        request_started_at = max(self.turn_entered_at(), request_control.mtime)
        pending_age = now - request_started_at
        advisory_target = self.prompt_pane_target("advisory")
        advisory_lane = self.prompt_owner("advisory") or "Gemini"
        advisory_lane_busy = False
        advisory_busy_age_sec: Optional[int] = None
        if advisory_target:
            advisory_snapshot = self.capture_pane_text(advisory_target)
            advisory_lane_busy = self.pane_text_has_busy_indicator(advisory_snapshot, advisory_lane)
            if advisory_lane_busy:
                advisory_busy_age_sec = self.pane_text_busy_age_seconds(advisory_snapshot, advisory_lane)
                if advisory_busy_age_sec is not None:
                    pending_age = max(pending_age, float(advisory_busy_age_sec))
        if pending_age < self.advisory_recovery_sec():
            return None

        if any(
            normalize_notify_kind(pending.get("notify_kind")) == ADVISORY_RECOVERY_NOTIFY
            for pending in self.pending_notifications()
        ):
            return None

        target = self.prompt_pane_target("verify")
        if not target:
            return None
        ready, defer_reason = self.lane_prompt_readiness(target)
        if not ready:
            return None

        recovery_attempt = self.advisory_recovery_attempt_for_request(request_control)
        advisory_followup_allowed = recovery_attempt < ADVISORY_RECOVERY_FOLLOWUP_LIMIT
        if advisory_followup_allowed:
            next_controls = (
                ".pipeline/implement_handoff.md [implement] | "
                ".pipeline/advisory_request.md [request_open] | "
                ".pipeline/operator_request.md [needs_operator]"
            )
            repeat_rule = (
                "First stale advisory recovery: advisory follow-up is allowed only if it has "
                "materially narrower new evidence; otherwise choose implement/operator."
            )
        else:
            next_controls = (
                ".pipeline/implement_handoff.md [implement] | "
                ".pipeline/operator_request.md [needs_operator]"
            )
            repeat_rule = (
                "Repeated stale advisory recovery: do not write another "
                "`.pipeline/advisory_request.md`; choose a bounded implement handoff from "
                "current evidence, or write an operator stop only for a real operator-only "
                "boundary."
            )

        return {
            "reason": "advisory_recovery",
            "control_file": request_control.path.name,
            "control_seq": request_seq,
            "request_sig": request_sig,
            "advisory_pending_age_sec": int(pending_age),
            "advisory_recovery_attempt": recovery_attempt,
            "advisory_followup_allowed": advisory_followup_allowed,
            "advisory_recovery_next_controls": next_controls,
            "advisory_recovery_repeat_rule": repeat_rule,
            "advisory_lane_target": advisory_target,
            "advisory_lane_busy": advisory_lane_busy,
            "advisory_lane_busy_age_sec": advisory_busy_age_sec,
            "verify_lane_ready": True,
            "verify_lane_ready_reason": defer_reason,
        }

    def advisory_recovery_attempt_for_request(self, request_control: ControlSignalLike) -> int:
        chain_count = self.prior_recovery_chain_count_from_request(request_control.path)
        prior_attempts = chain_count
        if chain_count > 0:
            prior_attempts = max(
                prior_attempts,
                self.prior_recovery_event_count(request_control.control_seq),
            )
        return max(1, prior_attempts + 1)

    @staticmethod
    def prior_recovery_chain_count_from_request(request_path: Path) -> int:
        try:
            request_text = request_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return 0
        count = 0
        for raw_line in request_text.splitlines():
            line = raw_line.strip().lower()
            if not line.startswith("supersedes:"):
                continue
            if "advisory_request.md" in line and "stale_advisory_recovery" in line:
                count += 1
        return count

    def prior_recovery_event_count(self, current_control_seq: int) -> int:
        try:
            lines = self.run_events_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return 0

        count = 0
        for line in reversed(lines[-200:]):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event_type") != "advisory_recovery":
                continue
            payload = event.get("payload")
            if not isinstance(payload, dict):
                continue
            seq = control_seq_value(payload.get("control_seq"), default=-1)
            if current_control_seq >= 0 and seq >= current_control_seq:
                continue
            if payload.get("control_file") not in {"advisory_request.md", None}:
                continue
            count += 1
        return count

    def supersede_request_for_recovery(self, marker: dict[str, object]) -> bool:
        request_seq = control_seq_value(marker.get("control_seq"), default=-1)
        if self.read_status_from_path(self.advisory_request_path) != "request_open":
            return False
        slot_seq = self.read_control_seq_from_path(self.advisory_request_path)
        if request_seq >= 0 and slot_seq != request_seq:
            return False
        try:
            original_text = self.advisory_request_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False

        supersede_lines = [
            "SUPERSEDED_BY: advisory_recovery",
            f"SUPERSEDED_BY_SEQ: {request_seq}",
            "SUPERSEDED_REASON: stale_advisory_recovery",
        ]
        output_lines: list[str] = []
        status_written = False
        supersede_written = False
        for raw_line in original_text.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith(("SUPERSEDED_BY:", "SUPERSEDED_BY_SEQ:", "SUPERSEDED_REASON:")):
                continue
            if stripped.startswith("STATUS:") and not status_written:
                output_lines.append("STATUS: superseded")
                status_written = True
                continue
            output_lines.append(raw_line)
            if stripped.startswith("CONTROL_SEQ:") and not supersede_written:
                output_lines.extend(supersede_lines)
                supersede_written = True

        if not status_written:
            output_lines.insert(0, "STATUS: superseded")
        if not supersede_written:
            insert_at = 1 if output_lines and output_lines[0].strip().startswith("STATUS:") else 0
            output_lines[insert_at:insert_at] = supersede_lines

        atomic_write_text(self.advisory_request_path, "\n".join(output_lines).rstrip() + "\n")
        self.set_last_advisory_request_sig(self.get_path_sig(self.advisory_request_path))
        payload = {
            "reason": "advisory_recovery",
            "control_file": self.advisory_request_path.name,
            "control_seq": slot_seq,
            "superseded_by": "advisory_recovery",
        }
        marker["advisory_request_superseded"] = True
        self.log_raw("advisory_request_superseded", str(self.advisory_request_path), "turn_signal", payload)
        self.emit_event("advisory_request_superseded", payload)
        return True

    def recover_stale(self) -> bool:
        marker = self.stale_recovery_marker()
        if marker is None:
            return False

        request_seq = control_seq_value(marker.get("control_seq"), default=-1)
        request_sig = str(marker.get("request_sig") or "")
        self.last_recovery_sig = request_sig
        self.last_recovery_at = self.now_fn()
        cancelled = self.cancel_advisory_lane_if_busy(
            reason="advisory_recovery",
            payload_extra={
                "request_control_seq": request_seq,
                "advisory_pending_age_sec": marker.get("advisory_pending_age_sec", 0),
                "advisory_lane_busy_age_sec": marker.get("advisory_lane_busy_age_sec"),
            },
        )
        if cancelled:
            marker["advisory_lane_cancelled"] = True
            marker["advisory_lane_cancel_dry_run"] = bool(self.dry_run())
        self.supersede_request_for_recovery(marker)
        self.clear_implement_blocked("advisory_recovery")
        self.log_raw("advisory_recovery", str(self.advisory_request_path), "turn_signal", marker)
        self.emit_event("advisory_recovery", marker)
        self.transition_turn(
            WatcherTurnState.VERIFY_FOLLOWUP,
            "advisory_recovery",
            active_control_file="advisory_request.md",
            active_control_seq=request_seq,
        )
        self.notify_verify_advisory_recovery("advisory_recovery", marker)
        return True


@dataclass
class OperatorRetrageTracker:
    operator_request_path: Path
    current_turn_state: Callable[[], WatcherTurnState]
    turn_active_control_seq: Callable[[], int]
    operator_wait_retriage_sec: Callable[[], float]
    is_active_control: Callable[[Path, str], bool]
    get_path_mtime: Callable[[Path], float]
    read_control_seq_from_path: Callable[[Path], int]
    get_active_control: Callable[[], ControlSignalLike | None]
    control_signal_for_slot: Callable[[ControlSignalLike | None, str, str], ControlSignalLike | None]
    satisfied_operator_approval_marker: Callable[[], Optional[dict[str, object]]]
    stale_operator_control_marker: Callable[[], Optional[dict[str, object]]]
    get_path_sig: Callable[[Path], str]
    read_status_from_path: Callable[[Path], Optional[str]]
    clear_implement_blocked: Callable[[str], None]
    transition_turn: Callable[..., None]
    record_operator_recovery_marker: Callable[..., str]
    notify_verify_operator_retriage: Callable[[str, dict[str, object]], None]
    notify_verify_control_recovery: Callable[[str, dict[str, object]], None]
    set_last_operator_request_sig: Callable[[str], None]
    now_fn: Callable[[], float]
    last_retriage_sig: str = ""
    last_retriage_fingerprint: str = ""
    retriage_started_at: float = 0.0
    last_recovery_key: str = ""
    recovery_started_at: float = 0.0

    def mark_retriage_started(self, operator_sig: str, marker: dict[str, object]) -> None:
        fingerprint = str(marker.get("fingerprint") or "")
        if (
            fingerprint
            and fingerprint == self.last_retriage_fingerprint
            and self.retriage_started_at > 0.0
        ):
            self.last_retriage_sig = operator_sig
            return
        self.last_retriage_sig = operator_sig
        self.last_retriage_fingerprint = fingerprint
        self.retriage_started_at = self.now_fn()

    def is_same_semantic_bump(self, marker: dict[str, object]) -> bool:
        fingerprint = str(marker.get("fingerprint") or "")
        return (
            self.current_turn_state() == WatcherTurnState.VERIFY_FOLLOWUP
            and bool(fingerprint)
            and fingerprint == self.last_retriage_fingerprint
            and self.retriage_started_at > 0.0
        )

    def idle_retriage_marker(self) -> Optional[dict[str, object]]:
        if not self.is_active_control(self.operator_request_path, "needs_operator"):
            return None
        control_mtime = self.get_path_mtime(self.operator_request_path)
        if control_mtime <= 0:
            return None
        age_sec = max(0.0, self.now_fn() - control_mtime)
        if age_sec < self.operator_wait_retriage_sec():
            return None
        return {
            "control_file": "operator_request.md",
            "control_seq": self.read_control_seq_from_path(self.operator_request_path),
            "reason": "operator_wait_idle_retriage",
            "resolved_work_paths": [],
            "operator_wait_age_sec": int(age_sec),
        }

    def control_recovery_marker(self) -> Optional[dict[str, object]]:
        satisfied = self.satisfied_operator_approval_marker()
        if satisfied is not None:
            return satisfied
        stale = self.stale_operator_control_marker()
        if stale is not None:
            return stale
        return self.idle_retriage_marker()

    def recovery_without_idle_marker(self) -> Optional[dict[str, object]]:
        satisfied = self.satisfied_operator_approval_marker()
        if satisfied is not None:
            return satisfied
        return self.stale_operator_control_marker()

    @staticmethod
    def recovery_key(operator_sig: str, marker: Mapping[str, object]) -> str:
        resolved_work = ",".join(str(item) for item in list(marker.get("resolved_work_paths") or []))
        resolved_prs = ",".join(str(item) for item in list(marker.get("resolved_pr_numbers") or []))
        return "|".join(
            [
                operator_sig,
                str(marker.get("control_seq") or ""),
                str(marker.get("reason") or ""),
                resolved_work,
                resolved_prs,
            ]
        )

    def route_recovery(
        self,
        *,
        operator_sig: str,
        operator_path: Path,
        status: str,
        marker: dict[str, object],
        source: str,
    ) -> bool:
        recovery_reason = str(marker.get("reason") or "verified_blockers_resolved")
        control_seq = control_seq_value(marker.get("control_seq"), default=-1)
        recovery_key = self.recovery_key(operator_sig, marker)
        if (
            recovery_key
            and recovery_key == self.last_recovery_key
            and self.current_turn_state() == WatcherTurnState.VERIFY_FOLLOWUP
            and control_seq == self.turn_active_control_seq()
        ):
            return True
        self.last_recovery_key = recovery_key
        self.recovery_started_at = self.now_fn()
        if operator_sig:
            self.set_last_operator_request_sig(operator_sig)
        log.info("operator request recoverable without operator action: verify follow-up resumes (%s)", recovery_reason)
        self.clear_implement_blocked(recovery_reason)
        self.transition_turn(
            WatcherTurnState.VERIFY_FOLLOWUP,
            recovery_reason,
            active_control_file=operator_path.name,
            active_control_seq=control_seq,
        )
        if recovery_reason == "operator_wait_idle_retriage":
            self.mark_retriage_started(operator_sig, marker)
        recovery_event = self.record_operator_recovery_marker(
            recovery_reason=recovery_reason,
            status=status,
            marker=marker,
            source=source,
        )
        if recovery_reason == "operator_wait_idle_retriage":
            self.notify_verify_operator_retriage(recovery_reason, marker)
        else:
            self.notify_verify_control_recovery(recovery_event, marker)
        return True

    def check_recovery_without_signal(self) -> bool:
        active_control = self.get_active_control()
        operator_control = self.control_signal_for_slot(
            active_control,
            "operator_request",
            "needs_operator",
        )
        if operator_control is None:
            return False
        if operator_control.control_seq < self.turn_active_control_seq():
            return False
        marker = self.recovery_without_idle_marker()
        if marker is None:
            return False
        operator_sig = operator_control.sig or self.get_path_sig(operator_control.path)
        status = self.read_status_from_path(operator_control.path) or "missing"
        return self.route_recovery(
            operator_sig=operator_sig,
            operator_path=operator_control.path,
            status=status,
            marker=marker,
            source="turn_signal",
        )


OperatorRetriageTracker = OperatorRetrageTracker

__all__ = [
    "ADVISORY_RECOVERY_FOLLOWUP_LIMIT",
    "OperatorRetrageTracker",
    "OperatorRetriageTracker",
    "StaleAdvisoryRecovery",
]
