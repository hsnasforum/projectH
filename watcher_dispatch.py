from __future__ import annotations

import json
import logging
import re
import shlex
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from pipeline_runtime.lane_surface import (
    busy_markers_for_lane as _shared_busy_markers_for_lane,
    capture_pane_text as _shared_capture_pane_text,
    pane_text_has_busy_indicator,
    pane_text_has_codex_activity as _shared_pane_text_has_codex_activity,
    pane_text_has_gemini_activity as _shared_pane_text_has_gemini_activity,
    pane_text_has_input_cursor,
    pane_text_has_input_cursor as _shared_pane_text_has_input_cursor,
    pane_text_has_working_indicator as _shared_pane_text_has_working_indicator,
    pane_text_is_idle,
    pane_text_is_idle as _shared_pane_text_is_idle,
    text_matches_markers as _shared_text_matches_markers,
    wait_for_pane_settle as _shared_wait_for_pane_settle,
)
from pipeline_runtime.schema import control_filenames_equivalent, control_slot_id_for_filename
from pipeline_runtime.role_routes import (
    IMPLEMENT_HANDOFF_NOTIFY,
    LEGACY_CLAUDE_HANDOFF_NOTIFY,
    normalize_notify_kind,
)

SIGNAL_MISMATCH_DROP_NOTIFY_KINDS = frozenset({
    IMPLEMENT_HANDOFF_NOTIFY,
    LEGACY_CLAUDE_HANDOFF_NOTIFY,
})
log = logging.getLogger(__name__)

_DISPATCH_LOCKS_GUARD = threading.Lock()
_DISPATCH_LOCKS: dict[str, threading.Lock] = {}
_DISPATCH_LOCK_TIMEOUT_SEC = 30.0
_GEMINI_GIT_PERMISSION_PROMPT_RE = re.compile(
    r"Allow execution of\s*\[git\]\?",
    re.IGNORECASE,
)
_GEMINI_ALLOW_FOR_SESSION_RE = re.compile(
    r"\b2\.\s*Allow for this session\b",
    re.IGNORECASE,
)
_GEMINI_SHELL_COMMAND_RE = re.compile(r"\bShell\s+(.+)$", re.IGNORECASE)
_GEMINI_GIT_COMMAND_RE = re.compile(r"\bgit(?:\s+|$).*$", re.IGNORECASE)
_GEMINI_PROMPT_BORDER_CHARS = "|│┃┆╎┊"
_READONLY_GIT_SUBCOMMANDS = frozenset(
    {
        "describe",
        "diff",
        "for-each-ref",
        "log",
        "ls-files",
        "ls-tree",
        "merge-base",
        "rev-list",
        "rev-parse",
        "show",
        "status",
    }
)
_BRANCH_MUTATING_OPTIONS = frozenset(
    {
        "-c",
        "-C",
        "-d",
        "-D",
        "-m",
        "-M",
        "--copy",
        "--delete",
        "--edit-description",
        "--move",
        "--set-upstream-to",
        "--unset-upstream",
    }
)


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
    expected_control_slot: str = ""
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
            "expected_control_slot": intent.expected_control_slot,
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
            expected_control_slot=str(pending.get("expected_control_slot") or ""),
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
        expected_control_slot = str(pending.get("expected_control_slot") or "").strip()
        expected_status = str(pending.get("expected_status") or "").strip()
        expected_control_seq = int(pending.get("expected_control_seq") or -1)
        if not expected_control_path and not expected_control_slot and not expected_status and expected_control_seq < 0:
            return None
        if active_control is None:
            return "active_control_missing"
        active_slot_id = str(getattr(active_control, "slot_id", "") or "").strip()
        if not active_slot_id:
            active_slot_id = control_slot_id_for_filename(getattr(active_control, "path", None))
        if expected_control_slot and active_slot_id != expected_control_slot:
            return "control_file_drift"
        if (
            expected_control_path
            and active_control.path.name != expected_control_path
            and not control_filenames_equivalent(active_control.path.name, expected_control_path)
        ):
            return "control_file_drift"
        if expected_status and active_control.status != expected_status:
            return "control_status_drift"
        if expected_control_seq >= 0 and active_control.control_seq != expected_control_seq:
            return "control_seq_drift"
        if self._pending_signal_mismatch_reason(pending) is not None:
            return "signal_mismatch"
        return None

    def _pending_signal_mismatch_reason(self, pending: dict[str, object]) -> str | None:
        notify_kind = normalize_notify_kind(pending.get("notify_kind"))
        if notify_kind not in SIGNAL_MISMATCH_DROP_NOTIFY_KINDS:
            return None

        prompt_path_raw = str(pending.get("prompt_path") or "").strip()
        if not prompt_path_raw:
            return None
        control_seq = int(pending.get("expected_control_seq") or pending.get("control_seq") or -1)
        if control_seq < 0:
            return None

        role_name = str(pending.get("functional_role") or pending.get("lane_role") or "").strip()
        lane_name = str(self._role_owner(role_name) or "").strip()
        if not lane_name:
            lane_hint = str(pending.get("agent_kind") or "").strip()
            lane_name = lane_hint[:1].upper() + lane_hint[1:] if lane_hint else ""
        if not lane_name:
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


def _extract_gemini_git_permission_commands(text: str) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        shell_match = _GEMINI_SHELL_COMMAND_RE.search(line)
        if shell_match:
            candidate = shell_match.group(1).strip()
        else:
            git_match = _GEMINI_GIT_COMMAND_RE.search(line)
            if git_match is None:
                continue
            candidate = git_match.group(0).strip()
        candidate = candidate.strip(f" {_GEMINI_PROMPT_BORDER_CHARS}")
        candidate = candidate.translate(str.maketrans({char: " " for char in _GEMINI_PROMPT_BORDER_CHARS}))
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if not candidate.lower().startswith("git "):
            continue
        if candidate not in seen:
            seen.add(candidate)
            commands.append(candidate)
    return commands


def _git_branch_invocation_is_readonly(args: list[str]) -> bool:
    for token in args:
        lowered = token.lower()
        if lowered in _BRANCH_MUTATING_OPTIONS:
            return False
        if lowered.startswith("--set-upstream-to="):
            return False
        if not token.startswith("-"):
            return False
    return True


def _git_segment_is_readonly(segment: str) -> bool:
    try:
        tokens = shlex.split(segment)
    except ValueError:
        return False
    if len(tokens) < 2:
        return False
    if tokens[0] != "git":
        return False
    subcommand = tokens[1].lower()
    if subcommand == "branch":
        return _git_branch_invocation_is_readonly(tokens[2:])
    if subcommand not in _READONLY_GIT_SUBCOMMANDS:
        return False
    if any(token.startswith("--output") or token == "--ext-diff" for token in tokens[2:]):
        return False
    return True


def _git_shell_command_is_readonly(command: str) -> bool:
    command_text = str(command or "").strip()
    if not command_text:
        return False
    if re.search(r"[`$<>;|]", command_text):
        return False
    if re.search(r"(?<!&)&(?!&)", command_text):
        return False
    segments = [segment.strip() for segment in command_text.split("&&")]
    if not segments or any(not segment for segment in segments):
        return False
    return all(_git_segment_is_readonly(segment) for segment in segments)


def gemini_git_permission_prompt_needs_session_allow(text: str) -> bool:
    if _GEMINI_GIT_PERMISSION_PROMPT_RE.search(str(text or "")) is None:
        return False
    if _GEMINI_ALLOW_FOR_SESSION_RE.search(str(text or "")) is None:
        return False
    commands = _extract_gemini_git_permission_commands(text)
    if not commands:
        return False
    return all(_git_shell_command_is_readonly(command) for command in commands)


def maybe_answer_gemini_git_permission_prompt(
    pane_target: str,
    *,
    dry_run: bool = False,
) -> bool:
    if not pane_target:
        return False
    snapshot = _shared_capture_pane_text(pane_target)
    if not gemini_git_permission_prompt_needs_session_allow(snapshot):
        return False
    log.info(
        "answering Gemini readonly git permission prompt target=%s dry_run=%s",
        pane_target,
        dry_run,
    )
    if dry_run:
        return True
    dispatch_lock = _dispatch_lock_for(pane_target)
    if not dispatch_lock.acquire(timeout=_DISPATCH_LOCK_TIMEOUT_SEC):
        log.warning(
            "Gemini git permission prompt answer skipped: pane dispatch busy target=%s",
            pane_target,
        )
        return False
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_target, "2", "Enter"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        log.error("Gemini git permission prompt answer failed: %s", e.stderr.decode().strip())
        return False
    finally:
        dispatch_lock.release()


def tmux_send_escape(
    pane_target: str,
    *,
    dry_run: bool = False,
) -> bool:
    """Send Escape to a tmux pane through the shared dispatch lock."""
    if not pane_target:
        return False
    log.info("send Escape target=%s dry_run=%s", pane_target, dry_run)
    if dry_run:
        return True
    dispatch_lock = _dispatch_lock_for(pane_target)
    if not dispatch_lock.acquire(timeout=_DISPATCH_LOCK_TIMEOUT_SEC):
        log.warning("send Escape skipped: pane dispatch busy target=%s", pane_target)
        return False
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_target, "Escape"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        log.error("send Escape failed: %s", e.stderr.decode().strip())
        return False
    finally:
        dispatch_lock.release()


def _wait_for_input_ready(
    pane_target: str,
    timeout_sec: float = 30.0,
    poll_sec: float = 0.5,
    stable_sec: float = 2.0,
) -> bool:
    """
    Wait until the pane shows a stable input prompt.

    For fresh Codex startup, the prompt may briefly appear while MCP boot/logging is
    still settling. Requiring a short continuous ready window makes the first
    dispatch less likely to land during that unstable startup phase.
    """
    deadline = time.time() + timeout_sec
    ready_since: float | None = None
    while time.time() < deadline:
        snapshot = _shared_capture_pane_text(pane_target)
        if _shared_pane_text_has_input_cursor(snapshot):
            if ready_since is None:
                ready_since = time.time()
            elif time.time() - ready_since >= stable_sec:
                return True
        else:
            ready_since = None
        time.sleep(poll_sec)
    return False


def _wait_for_dispatch_window(
    pane_target: str,
    pane_type: str,
    timeout_sec: float = 10.0,
) -> bool:
    """
    Dispatch 직전 pane이 실제 입력을 받을 준비가 됐는지 기다린다.
    MCP 문자열 기반 장기 대기 대신, 고정된 짧은 readiness 확인만 수행한다.
    """
    if _is_pane_dead(pane_target):
        _respawn_pane(pane_target)

    if not _wait_for_input_ready(
        pane_target,
        timeout_sec=timeout_sec,
        poll_sec=0.5,
        stable_sec=2.0,
    ):
        log.warning(
            "%s pane not ready for dispatch (timeout=%.1fs)",
            pane_type,
            timeout_sec,
        )
        return False

    _shared_wait_for_pane_settle(
        pane_target,
        timeout_sec=3.0,
        quiet_sec=0.75,
        poll_sec=0.25,
    )
    return True


def _is_pane_dead(pane_target: str) -> bool:
    """Check if a tmux pane is in dead (exited) state."""
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-t", pane_target, "-p", "#{pane_dead}"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() == "1"
    except subprocess.CalledProcessError:
        return True


def _respawn_pane(pane_target: str) -> None:
    """Respawn a dead tmux pane back to a bash shell."""
    log.info("respawning dead pane: %s", pane_target)
    subprocess.run(
        ["tmux", "respawn-pane", "-k", "-t", pane_target],
        check=False,
        capture_output=True,
    )
    time.sleep(1.0)


def _clear_prompt_input_line(pane_target: str) -> None:
    """Clear any stale unsent text before an automated dispatch."""
    subprocess.run(
        ["tmux", "send-keys", "-t", pane_target, "C-u"],
        check=True,
        capture_output=True,
    )
    time.sleep(0.1)


def _dispatch_lock_for(pane_target: str) -> threading.Lock:
    with _DISPATCH_LOCKS_GUARD:
        lock = _DISPATCH_LOCKS.get(pane_target)
        if lock is None:
            lock = threading.Lock()
            _DISPATCH_LOCKS[pane_target] = lock
        return lock


def tmux_send_keys(
    pane_target: str,
    command: str,
    dry_run: bool = False,
    pane_type: str = "claude",
) -> bool:
    """Send a prompt to a tmux pane.

    pane_type: "codex" — paste-buffer + Enter retry with working-indicator check
               "claude" — paste-buffer + Enter retry
               "gemini" — paste-buffer + Enter retry
    """
    log.info("send-keys target=%s pane_type=%s dry_run=%s", pane_target, pane_type, dry_run)
    if dry_run:
        return True
    dispatch_lock = _dispatch_lock_for(pane_target)
    if not dispatch_lock.acquire(timeout=_DISPATCH_LOCK_TIMEOUT_SEC):
        log.warning(
            "send-keys skipped: pane dispatch busy target=%s pane_type=%s",
            pane_target,
            pane_type,
        )
        return False
    try:
        if not _wait_for_dispatch_window(
            pane_target,
            pane_type,
        ):
            return False
        if pane_type == "codex":
            return _dispatch_codex(pane_target, command)
        if pane_type == "gemini":
            return _dispatch_gemini(pane_target, command)
        return _dispatch_claude(pane_target, command)
    except subprocess.CalledProcessError as e:
        log.error("send-keys failed: %s", e.stderr.decode().strip())
        return False
    finally:
        dispatch_lock.release()


def _pane_has_working_indicator(pane_target: str) -> bool:
    """Check whether the recent pane output shows Codex has started working."""
    text = _shared_capture_pane_text(pane_target)
    return _shared_pane_text_has_working_indicator(text)


def _dispatch_codex(pane_target: str, command: str) -> bool:
    """Dispatch to Codex pane.

    Codex interactive session is kept alive (started by start-pipeline.sh).
    Always paste-buffer into the running session — never re-launch codex.
    """
    log.info("dispatching codex prompt: chars=%d", len(command))
    _clear_prompt_input_line(pane_target)
    subprocess.run(["tmux", "set-buffer", command], check=True, capture_output=True)
    subprocess.run(["tmux", "paste-buffer", "-t", pane_target], check=True, capture_output=True)
    pasted_snapshot = _shared_capture_pane_text(pane_target)
    time.sleep(1.0)
    for attempt in range(3):
        subprocess.run(["tmux", "send-keys", "-t", pane_target, "Enter"], check=True, capture_output=True)
        time.sleep(1.5)
        snapshot = _shared_capture_pane_text(pane_target)
        if not _shared_pane_text_has_input_cursor(snapshot):
            log.info("codex prompt consumed: attempt %d", attempt + 1)
            deadline = time.time() + 6.0
            while time.time() < deadline:
                if _pane_has_working_indicator(pane_target):
                    log.info("codex working indicator detected")
                    return True
                current_snapshot = _shared_capture_pane_text(pane_target)
                if current_snapshot != snapshot and _shared_pane_text_has_codex_activity(current_snapshot):
                    log.info("codex response activity detected after consume: attempt %d", attempt + 1)
                    return True
                time.sleep(0.5)
            log.info(
                "codex dispatch consumed without immediate confirmation: defer acceptance to wrapper events"
            )
            return True
        if snapshot != pasted_snapshot and _shared_pane_text_has_codex_activity(snapshot):
            log.info("codex response activity detected: attempt %d", attempt + 1)
            return True
    log.info("codex prompt still visible or unconfirmed after retries")
    return False


def _dispatch_claude(pane_target: str, command: str) -> bool:
    """Dispatch to Claude pane via paste-buffer + Enter."""
    _clear_prompt_input_line(pane_target)
    subprocess.run(["tmux", "set-buffer", command], check=True, capture_output=True)
    subprocess.run(["tmux", "paste-buffer", "-t", pane_target], check=True, capture_output=True)
    pasted_snapshot = _shared_capture_pane_text(pane_target)
    time.sleep(1.0)
    for attempt in range(3):
        subprocess.run(["tmux", "send-keys", "-t", pane_target, "Enter"], check=True, capture_output=True)
        time.sleep(1.5)
        snapshot = _shared_capture_pane_text(pane_target)
        if not _shared_pane_text_has_input_cursor(snapshot):
            log.info("claude prompt consumed: attempt %d", attempt + 1)
            return True
        if snapshot != pasted_snapshot:
            if _shared_text_matches_markers(snapshot, _shared_busy_markers_for_lane("Claude")):
                log.info("claude busy output detected after dispatch: attempt %d", attempt + 1)
                return True
            if _shared_pane_text_is_idle(snapshot):
                log.info("claude ready output detected after dispatch: attempt %d", attempt + 1)
                return True
    log.info("claude prompt still visible or unconfirmed after retries")
    return False


def _dispatch_gemini(pane_target: str, command: str) -> bool:
    """Dispatch to Gemini pane via paste-buffer + Enter."""
    _clear_prompt_input_line(pane_target)
    subprocess.run(["tmux", "set-buffer", command], check=True, capture_output=True)
    subprocess.run(["tmux", "paste-buffer", "-t", pane_target], check=True, capture_output=True)
    pasted_snapshot = _shared_capture_pane_text(pane_target)
    time.sleep(1.0)
    for attempt in range(3):
        subprocess.run(["tmux", "send-keys", "-t", pane_target, "Enter"], check=True, capture_output=True)
        time.sleep(1.5)
        snapshot = _shared_capture_pane_text(pane_target)
        if not _shared_pane_text_has_input_cursor(snapshot):
            log.info("gemini prompt consumed: attempt %d", attempt + 1)
            return True
        if snapshot != pasted_snapshot and _shared_pane_text_has_gemini_activity(snapshot):
            log.info("gemini response activity detected: attempt %d", attempt + 1)
            return True
    log.info("gemini prompt still visible or unconfirmed after retries")
    return False
