"""Read-only runtime monitor state for the controller Office View."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


DEFAULT_AGENT_NAMES = ("Claude", "Codex", "Gemini")
DEFAULT_USAGE_SOURCE_BY_AGENT = {
    "Claude": "claude",
    "Codex": "codex",
    "Gemini": "gemini",
}
LOG_FILE_GLOBS = ("*.jsonl", "*.log", "*.txt")
MAX_WATCHED_EXTRA_LOGS = 60
MAX_INITIAL_TAIL_BYTES = 64 * 1024
MAX_INCREMENTAL_READ_BYTES = 128 * 1024
MAX_COMMUNICATION_EVENTS = 80
TEAM_COLORS = ("#6aa7c9", "#5c9a4a", "#e0a93b", "#a88cc5", "#c98a6a")


@dataclass(slots=True)
class LogCursor:
    path: Path
    offset: int = 0
    initialized: bool = False
    last_mtime_ns: int = 0


@dataclass(slots=True)
class ParsedLogEvent:
    agent_id: str
    state: str = ""
    tokens: int = 0
    prompt: str = ""
    message: str = ""
    source_path: str = ""
    event_type: str = ""
    team_id: str = ""
    parent_id: str = ""
    target_agent_id: str = ""
    approval_wait: bool = False


@dataclass(slots=True)
class InputPortPollResult:
    port_name: str
    events: list[ParsedLogEvent] = field(default_factory=list)
    changed_paths: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AgentMonitorState:
    agent_id: str
    state: str = ""
    tokens: int = 0
    prompt: str = ""
    conversation: list[str] = field(default_factory=list)
    last_source_path: str = ""
    event_type: str = ""
    team_id: str = ""
    parent_id: str = ""
    target_agent_id: str = ""
    approval_wait: bool = False
    updated_at_ms: int = 0


def now_epoch_ms() -> int:
    return int(time.time() * 1000)


def token_total(row: dict) -> int:
    return (
        int(row.get("input_tokens") or 0)
        + int(row.get("output_tokens") or 0)
        + int(row.get("cache_read_tokens") or 0)
        + int(row.get("cache_write_tokens") or 0)
        + int(row.get("thinking_tokens") or 0)
    )


def cache_hit_rate(row: dict) -> float | None:
    cache_read = int(row.get("cache_read_tokens") or 0)
    input_tokens = int(row.get("input_tokens") or 0)
    cache_write = int(row.get("cache_write_tokens") or 0)
    denominator = input_tokens + cache_read + cache_write
    if denominator <= 0:
        return None
    return round(cache_read / denominator, 4)


class AgentLogParser:
    """Small parser for controller-visible agent log lines.

    The controller still treats supervisor status and the usage DB as the
    authoritative sources. This parser only turns appended local log lines into
    monitor hints for inspector freshness and future custom session directories.
    """

    _AGENT_RE = re.compile(r"\b(Claude|Codex|Gemini|claude|codex|gemini)\b")
    _STATE_RE = re.compile(r"\b(?:state|status)\s*[:=]\s*([A-Za-z_-]+)", re.IGNORECASE)
    _TOKENS_RE = re.compile(r"\b(?:tokens?|tok|total_tokens)\s*[:=]\s*([0-9][0-9_,]*)", re.IGNORECASE)
    _PROMPT_RE = re.compile(r"\b(?:prompt|request|task)\s*[:=]\s*(.+)$", re.IGNORECASE)
    _TEAM_RE = re.compile(r"\b(?:team|team_id|group|group_id|job|job_id)\s*[:=]\s*([A-Za-z0-9_.:/-]+)", re.IGNORECASE)
    _TARGET_RE = re.compile(r"\b(?:to|target|target_agent|target_agent_id|recipient)\s*[:=]\s*(Claude|Codex|Gemini|claude|codex|gemini)\b", re.IGNORECASE)
    _EVENT_RE = re.compile(r"\b(?:event_type|event|type|action)\s*[:=]\s*([A-Za-z_-]+)", re.IGNORECASE)
    _APPROVAL_WAIT_RE = re.compile(r"(approval[_ -]?wait|waiting[_ -]?approval|needs[_ -]?operator|approval_required|승인)", re.IGNORECASE)
    _STATE_ALIASES = {
        "active": "working",
        "busy": "working",
        "running": "working",
        "work": "working",
        "working": "working",
        "idle": "ready",
        "ready": "ready",
        "waiting": "ready",
        "waiting_approval": "ready",
        "approval_wait": "ready",
        "needs_operator": "ready",
        "standby": "ready",
        "stopped": "off",
        "off": "off",
        "error": "broken",
        "failed": "broken",
        "broken": "broken",
        "dead": "dead",
    }

    def __init__(self, agent_names: Iterable[str] = DEFAULT_AGENT_NAMES) -> None:
        self.agent_names = tuple(agent_names)
        self._canonical = {name.lower(): name for name in self.agent_names}

    def parse_line(self, line: str, *, source_path: str = "") -> ParsedLogEvent | None:
        text = str(line or "").strip()
        if not text:
            return None
        payload = self._decode_json_line(text)
        agent_id = self._extract_agent(payload, text)
        if not agent_id:
            return None
        state = self._extract_state(payload, text)
        tokens = self._extract_tokens(payload, text)
        prompt = self._extract_prompt(payload, text)
        message = self._extract_message(payload, text)
        event_type = self._extract_event_type(payload, text)
        team_id = self._extract_team_id(payload, text)
        parent_id = self._extract_parent_id(payload)
        target_agent_id = self._extract_target_agent(payload, text)
        approval_wait = self._extract_approval_wait(payload, text, event_type=event_type, state=state)
        if not any([state, tokens, prompt, message, event_type, team_id, parent_id, target_agent_id, approval_wait]):
            return None
        return ParsedLogEvent(
            agent_id=agent_id,
            state=state,
            tokens=tokens,
            prompt=prompt,
            message=message,
            source_path=source_path,
            event_type=event_type,
            team_id=team_id,
            parent_id=parent_id,
            target_agent_id=target_agent_id,
            approval_wait=approval_wait,
        )

    @staticmethod
    def _decode_json_line(text: str) -> dict:
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def _extract_agent(self, payload: dict, text: str) -> str:
        for key in ("agent_id", "agent", "name", "lane", "source"):
            raw = str(payload.get(key) or "").strip()
            canonical = self._canonical_agent(raw)
            if canonical:
                return canonical
        match = self._AGENT_RE.search(text)
        return self._canonical.get(match.group(1).lower(), "") if match else ""

    def _canonical_agent(self, raw: str) -> str:
        value = str(raw or "").strip().lower()
        return self._canonical.get(value, "")

    def _extract_state(self, payload: dict, text: str) -> str:
        raw = str(payload.get("state") or payload.get("status") or "").strip().lower()
        if not raw:
            match = self._STATE_RE.search(text)
            raw = match.group(1).strip().lower() if match else ""
        return self._STATE_ALIASES.get(raw, raw if raw in self._STATE_ALIASES.values() else "")

    def _extract_tokens(self, payload: dict, text: str) -> int:
        for key in ("total_tokens", "tokens", "token_count"):
            if key not in payload:
                continue
            try:
                return max(0, int(payload.get(key) or 0))
            except (TypeError, ValueError):
                continue
        total = 0
        for key in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens", "thinking_tokens"):
            try:
                total += max(0, int(payload.get(key) or 0))
            except (TypeError, ValueError):
                continue
        if total:
            return total
        match = self._TOKENS_RE.search(text)
        if not match:
            return 0
        return int(match.group(1).replace(",", "").replace("_", ""))

    @staticmethod
    def _extract_prompt(payload: dict, text: str) -> str:
        for key in ("prompt", "current_prompt", "request", "task"):
            raw = str(payload.get(key) or "").strip()
            if raw:
                return raw
        match = AgentLogParser._PROMPT_RE.search(text)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_message(payload: dict, text: str) -> str:
        for key in ("message", "text", "summary", "event"):
            raw = str(payload.get(key) or "").strip()
            if raw:
                return raw
        return text[:500]

    @staticmethod
    def _extract_event_type(payload: dict, text: str) -> str:
        raw = ""
        for key in ("event_type", "type", "action", "event"):
            raw = str(payload.get(key) or "").strip().lower()
            if raw:
                break
        if not raw:
            match = AgentLogParser._EVENT_RE.search(text)
            raw = match.group(1).strip().lower() if match else ""
        aliases = {
            "send": "handoff",
            "sent": "handoff",
            "message": "handoff",
            "transfer": "handoff",
            "handoff": "handoff",
            "delegate": "handoff",
            "approval": "approval_wait",
            "approval_required": "approval_wait",
            "waiting_approval": "approval_wait",
            "needs_operator": "approval_wait",
        }
        return aliases.get(raw, raw)

    @staticmethod
    def _extract_team_id(payload: dict, text: str) -> str:
        for key in ("team_id", "team", "group_id", "group", "job_id", "parent_prompt_id", "parent_id"):
            raw = str(payload.get(key) or "").strip()
            if raw:
                return raw[:120]
        match = AgentLogParser._TEAM_RE.search(text)
        return match.group(1).strip()[:120] if match else ""

    @staticmethod
    def _extract_parent_id(payload: dict) -> str:
        for key in ("parent_prompt_id", "parent_id", "parent", "root_prompt_id", "job_id"):
            raw = str(payload.get(key) or "").strip()
            if raw:
                return raw[:120]
        return ""

    def _extract_target_agent(self, payload: dict, text: str) -> str:
        for key in ("target_agent_id", "target_agent", "target", "to", "recipient"):
            canonical = self._canonical_agent(str(payload.get(key) or ""))
            if canonical:
                return canonical
        match = self._TARGET_RE.search(text)
        return self._canonical.get(match.group(1).lower(), "") if match else ""

    @staticmethod
    def _extract_approval_wait(payload: dict, text: str, *, event_type: str, state: str) -> bool:
        for key in ("approval_wait", "waiting_for_approval", "needs_approval"):
            if key in payload:
                raw = payload.get(key)
                if isinstance(raw, str):
                    return raw.strip().lower() in {"1", "true", "yes", "y", "required", "waiting"}
                return bool(raw)
        approval = payload.get("approval")
        if isinstance(approval, dict):
            return bool(approval.get("waiting") or approval.get("required"))
        raw_status = " ".join(
            str(payload.get(key) or "")
            for key in ("status", "state", "event_type", "type", "action", "reason_code")
        )
        return (
            event_type == "approval_wait"
            or state == "needs_operator"
            or bool(AgentLogParser._APPROVAL_WAIT_RE.search(raw_status))
            or bool(AgentLogParser._APPROVAL_WAIT_RE.search(text))
        )


class FileMonitorInputPort:
    """Read appended local log files and normalize lines into monitor events."""

    name = "file_watch"

    def __init__(self, project_root: Path, parser: AgentLogParser, *, extra_log_roots: Iterable[Path] | None = None) -> None:
        self.project_root = Path(project_root)
        self.parser = parser
        self.cursors: dict[Path, LogCursor] = {}
        self.extra_log_roots = [Path(root) for root in (extra_log_roots or [])]

    def poll(self, runtime_status: dict) -> InputPortPollResult:
        changed_paths: list[str] = []
        events: list[ParsedLogEvent] = []
        for path in self.watched_paths(runtime_status):
            path_events, changed = self._read_new_events(path)
            if changed:
                changed_paths.append(str(path))
            events.extend(path_events)
        return InputPortPollResult(port_name=self.name, events=events, changed_paths=changed_paths)

    def watched_paths(self, runtime_status: dict) -> list[Path]:
        paths: list[Path] = []
        run_id = str(runtime_status.get("current_run_id") or runtime_status.get("run_id") or "").strip()
        if run_id:
            run_dir = self.project_root / ".pipeline" / "runs" / run_id
            paths.extend([run_dir / "events.jsonl", run_dir / "status.json"])
        paths.append(self.project_root / ".pipeline" / "usage" / "collector.log")
        for root in self.extra_log_roots:
            paths.extend(self._discover_extra_logs(root))
        deduped: list[Path] = []
        seen: set[Path] = set()
        for path in paths:
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            deduped.append(resolved)
        return deduped

    def _discover_extra_logs(self, root: Path) -> list[Path]:
        if not root.exists():
            return []
        if root.is_file():
            return [root]
        files: list[Path] = []
        for pattern in LOG_FILE_GLOBS:
            files.extend(path for path in root.rglob(pattern) if path.is_file())
        files.sort(key=lambda path: path.stat().st_mtime_ns if path.exists() else 0, reverse=True)
        return files[:MAX_WATCHED_EXTRA_LOGS]

    def _read_new_events(self, path: Path) -> tuple[list[ParsedLogEvent], bool]:
        try:
            stat = path.stat()
        except OSError:
            return [], False
        cursor = self.cursors.setdefault(path, LogCursor(path=path))
        changed = stat.st_mtime_ns != cursor.last_mtime_ns
        if not changed and cursor.initialized:
            return [], False
        if stat.st_size < cursor.offset:
            cursor.offset = 0
        if not cursor.initialized and stat.st_size > MAX_INITIAL_TAIL_BYTES:
            cursor.offset = stat.st_size - MAX_INITIAL_TAIL_BYTES
        read_size = min(MAX_INCREMENTAL_READ_BYTES, max(0, stat.st_size - cursor.offset))
        events: list[ParsedLogEvent] = []
        try:
            with path.open("rb") as handle:
                handle.seek(cursor.offset)
                raw = handle.read(read_size)
                cursor.offset = handle.tell()
        except OSError:
            return [], changed
        cursor.initialized = True
        cursor.last_mtime_ns = stat.st_mtime_ns
        for line in raw.decode("utf-8", errors="replace").splitlines():
            event = self.parser.parse_line(line, source_path=str(path))
            if event is not None:
                events.append(event)
        return events, changed


class InMemoryMonitorInputPort:
    """Queue for future local REST or socket adapters without adding a network writer here."""

    name = "memory_port"

    def __init__(self) -> None:
        self._events: list[ParsedLogEvent] = []

    def submit(self, event: ParsedLogEvent) -> None:
        self._events.append(event)

    def poll(self, _runtime_status: dict) -> InputPortPollResult:
        events = list(self._events)
        self._events.clear()
        return InputPortPollResult(port_name=self.name, events=events)

    @staticmethod
    def watched_paths(_runtime_status: dict) -> list[Path]:
        return []


class RuntimeMonitorStateManager:
    """Central read-only state manager for controller monitor snapshots."""

    def __init__(
        self,
        project_root: Path,
        *,
        agent_names: Iterable[str] = DEFAULT_AGENT_NAMES,
        source_by_agent: dict[str, str] | None = None,
        extra_log_roots: Iterable[Path] | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.agent_names = tuple(agent_names)
        self.source_by_agent = dict(source_by_agent or DEFAULT_USAGE_SOURCE_BY_AGENT)
        self.agent_by_source = {source: agent for agent, source in self.source_by_agent.items()}
        self.parser = AgentLogParser(self.agent_names)
        self.extra_log_roots = [Path(root) for root in (extra_log_roots or self._env_extra_log_roots())]
        self.file_input_port = FileMonitorInputPort(self.project_root, self.parser, extra_log_roots=self.extra_log_roots)
        self.external_input_port = InMemoryMonitorInputPort()
        self.input_ports = [self.file_input_port, self.external_input_port]
        self.cursors = self.file_input_port.cursors
        self.agent_state: dict[str, AgentMonitorState] = {}
        self.communication_events: list[dict] = []
        self.communication_sequence = 0
        self.sequence = 0
        self.last_change_at_ms = 0
        self._lock = threading.Lock()

    @staticmethod
    def _env_extra_log_roots() -> list[Path]:
        raw = os.environ.get("CONTROLLER_MONITOR_LOG_DIRS", "")
        return [Path(item) for item in raw.split(os.pathsep) if item.strip()]

    def snapshot(self, *, runtime_status: dict, dashboard_payload: dict, usage_error: str = "") -> dict:
        with self._lock:
            changes = self._refresh_from_inputs_unlocked(runtime_status)
            hud = self.monitor_hud(runtime_status, dashboard_payload)
            return {
                "ok": True,
                "schema_version": 1,
                "transport": "websocket",
                "updated_at_ms": now_epoch_ms(),
                "runtime": runtime_status,
                "usage": dashboard_payload,
                "hud": hud,
                "log_state": self.log_state_payload(),
                "coordination_state": self.coordination_state_payload(),
                "teams": self.team_groups(runtime_status),
                "communications": list(self.communication_events[-20:]),
                "state_manager": {
                    "sequence": self.sequence,
                    "watched_paths": [str(path) for path in self._watch_files(runtime_status)],
                    "changed_paths": changes["changed_paths"],
                    "parsed_events": changes["parsed_events"],
                    "input_ports": [port.name for port in self.input_ports],
                    "last_change_at_ms": self.last_change_at_ms,
                },
                "source": {
                    "runtime_status": ".pipeline/current_run.json + .pipeline/runs/<run_id>/status.json",
                    "usage_db": str(self.project_root / ".pipeline" / "usage" / "usage.db"),
                    "extra_log_roots": [str(path) for path in self.extra_log_roots],
                    "read_only": True,
                },
                "usage_error": usage_error,
            }

    def refresh_from_logs(self, runtime_status: dict) -> dict:
        with self._lock:
            return self._refresh_from_inputs_unlocked(runtime_status)

    def _refresh_from_inputs_unlocked(self, runtime_status: dict) -> dict:
        changed_paths: list[str] = []
        parsed_events = 0
        ports_polled: list[str] = []
        for port in self.input_ports:
            result = port.poll(runtime_status)
            ports_polled.append(result.port_name)
            changed_paths.extend(result.changed_paths)
            parsed_events += self._ingest_events_unlocked(result.events)
        if changed_paths or parsed_events:
            self.sequence += 1
            self.last_change_at_ms = now_epoch_ms()
        return {"changed_paths": changed_paths, "parsed_events": parsed_events, "ports_polled": ports_polled}

    def ingest_events(self, events: Iterable[ParsedLogEvent]) -> dict:
        with self._lock:
            parsed_events = self._ingest_events_unlocked(events)
            if parsed_events:
                self.sequence += 1
                self.last_change_at_ms = now_epoch_ms()
            return {"changed_paths": [], "parsed_events": parsed_events}

    def submit_external_event(self, payload: ParsedLogEvent | dict | str, *, source_name: str = "memory_port") -> dict:
        event = self._event_from_external_payload(payload, source_name=source_name)
        if event is None:
            return {"changed_paths": [], "parsed_events": 0}
        with self._lock:
            self.external_input_port.submit(event)
            result = self.external_input_port.poll({})
            parsed_events = self._ingest_events_unlocked(result.events)
            if parsed_events:
                self.sequence += 1
                self.last_change_at_ms = now_epoch_ms()
            return {"changed_paths": [], "parsed_events": parsed_events}

    def _event_from_external_payload(self, payload: ParsedLogEvent | dict | str, *, source_name: str) -> ParsedLogEvent | None:
        if isinstance(payload, ParsedLogEvent):
            if not payload.source_path:
                payload.source_path = source_name
            return payload
        if isinstance(payload, dict):
            text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        else:
            text = str(payload or "")
        return self.parser.parse_line(text, source_path=source_name)

    def _ingest_events_unlocked(self, events: Iterable[ParsedLogEvent]) -> int:
        parsed_events = 0
        for event in events:
            self._apply_event(event)
            parsed_events += 1
        return parsed_events

    def _watch_files(self, runtime_status: dict) -> list[Path]:
        return self.file_input_port.watched_paths(runtime_status)

    def _apply_event(self, event: ParsedLogEvent) -> None:
        state = self.agent_state.setdefault(event.agent_id, AgentMonitorState(agent_id=event.agent_id))
        if event.state:
            state.state = event.state
        if event.tokens:
            state.tokens = max(state.tokens, event.tokens)
        if event.prompt:
            state.prompt = event.prompt
        if event.message:
            state.conversation.append(event.message)
            state.conversation = state.conversation[-8:]
        if event.event_type:
            state.event_type = event.event_type
        if event.team_id:
            state.team_id = event.team_id
        if event.parent_id:
            state.parent_id = event.parent_id
        if event.target_agent_id:
            state.target_agent_id = event.target_agent_id
            self._record_communication(event)
        if event.approval_wait:
            state.approval_wait = True
        elif event.state in {"working", "off", "dead", "broken"} or event.event_type in {"handoff", "resume", "approval_granted"}:
            state.approval_wait = False
        state.last_source_path = event.source_path
        state.updated_at_ms = now_epoch_ms()

    def _record_communication(self, event: ParsedLogEvent) -> None:
        if not event.target_agent_id or event.target_agent_id == event.agent_id:
            return
        self.communication_sequence += 1
        self.communication_events.append(
            {
                "sequence": self.communication_sequence,
                "time_ms": now_epoch_ms(),
                "from": event.agent_id,
                "to": event.target_agent_id,
                "event_type": event.event_type or "handoff",
                "message": event.message or event.prompt or event.event_type or "handoff",
                "team_id": event.team_id,
                "parent_id": event.parent_id,
                "source_path": event.source_path,
            }
        )
        self.communication_events = self.communication_events[-MAX_COMMUNICATION_EVENTS:]

    def log_state_payload(self) -> dict:
        return {
            name: {
                "agent_id": state.agent_id,
                "state": state.state,
                "tokens": state.tokens,
                "prompt": state.prompt,
                "conversation": list(state.conversation),
                "last_source_path": state.last_source_path,
                "event_type": state.event_type,
                "team_id": state.team_id,
                "parent_id": state.parent_id,
                "target_agent_id": state.target_agent_id,
                "approval_wait": state.approval_wait,
                "updated_at_ms": state.updated_at_ms,
            }
            for name, state in self.agent_state.items()
        }

    def coordination_state_payload(self) -> dict:
        return {
            name: {
                "team_id": state.team_id,
                "parent_id": state.parent_id,
                "event_type": state.event_type,
                "target_agent_id": state.target_agent_id,
                "approval_wait": state.approval_wait,
                "source_path": state.last_source_path,
                "updated_at_ms": state.updated_at_ms,
            }
            for name, state in self.agent_state.items()
            if state.team_id or state.parent_id or state.event_type or state.target_agent_id or state.approval_wait
        }

    def team_groups(self, runtime_status: dict) -> list[dict]:
        groups: dict[str, dict] = {}
        for name, state in self.agent_state.items():
            if not state.team_id:
                continue
            group = groups.setdefault(
                state.team_id,
                {
                    "id": state.team_id,
                    "label": f"Team {state.team_id}",
                    "agents": [],
                    "parent_id": state.parent_id,
                    "source": "log",
                },
            )
            group["agents"].append(name)
            if state.parent_id and not group.get("parent_id"):
                group["parent_id"] = state.parent_id

        runtime_group_id = self._runtime_team_id(runtime_status)
        if runtime_group_id:
            runtime_group = groups.setdefault(
                runtime_group_id,
                {
                    "id": runtime_group_id,
                    "label": f"Round {runtime_group_id}",
                    "agents": [],
                    "parent_id": str((runtime_status.get("active_round") or {}).get("job_id") or ""),
                    "source": "runtime",
                },
            )
            lanes = runtime_status.get("lanes") if isinstance(runtime_status.get("lanes"), list) else []
            for lane in lanes:
                if not isinstance(lane, dict):
                    continue
                name = str(lane.get("name") or "").strip()
                lane_state = str(lane.get("state") or "").strip().lower()
                if name and lane_state not in {"", "off", "dead", "missing"}:
                    runtime_group["agents"].append(name)

        output: list[dict] = []
        for index, group in enumerate(groups.values()):
            agents = sorted(dict.fromkeys(group.get("agents") or []))
            if len(agents) < 2:
                continue
            output.append(
                {
                    "id": group["id"],
                    "label": group.get("label") or group["id"],
                    "agents": agents,
                    "color": TEAM_COLORS[index % len(TEAM_COLORS)],
                    "parent_id": group.get("parent_id") or "",
                    "source": group.get("source") or "log",
                }
            )
        return output

    @staticmethod
    def _runtime_team_id(runtime_status: dict) -> str:
        active_round = runtime_status.get("active_round") if isinstance(runtime_status.get("active_round"), dict) else {}
        control = runtime_status.get("control") if isinstance(runtime_status.get("control"), dict) else {}
        for raw in (
            active_round.get("job_id"),
            active_round.get("round_id"),
            runtime_status.get("current_run_id"),
            runtime_status.get("run_id"),
            control.get("active_control_seq"),
        ):
            value = str(raw).strip() if raw is not None else ""
            if value and value != "-1":
                return value
        return ""

    def monitor_hud(self, runtime_status: dict, dashboard_payload: dict) -> dict:
        totals = dashboard_payload.get("today_totals") if isinstance(dashboard_payload.get("today_totals"), dict) else {}
        collector = dashboard_payload.get("collector_status") if isinstance(dashboard_payload.get("collector_status"), dict) else {}
        raw_agents = dashboard_payload.get("agent_totals") if isinstance(dashboard_payload.get("agent_totals"), list) else []
        agents_by_source = {
            str(row.get("source") or "").strip().lower(): row
            for row in raw_agents
            if isinstance(row, dict) and str(row.get("source") or "").strip()
        }
        lanes_by_name = self.agent_state_by_name(runtime_status)
        ordered_names: list[str] = list(self.agent_names)
        for source in agents_by_source:
            name = self.agent_by_source.get(source) or source.title()
            if name not in ordered_names:
                ordered_names.append(name)

        agent_rows = []
        for name in ordered_names:
            source = self.source_by_agent.get(name, name.lower())
            row = agents_by_source.get(source, {})
            lane = lanes_by_name.get(name, {})
            parsed = self.agent_state.get(name)
            state = str(lane.get("state") or (parsed.state if parsed else "") or ("ready" if row else "off")).lower()
            input_tokens = int(row.get("input_tokens") or 0)
            output_tokens = int(row.get("output_tokens") or 0)
            parsed_tokens = int(parsed.tokens if parsed else 0)
            if not lane and not row and not parsed:
                continue
            agent_rows.append(
                {
                    "name": name,
                    "source": source,
                    "state": state,
                    "active": bool(lane) and state not in {"off", "dead", "missing"},
                    "events": int(row.get("events") or 0),
                    "linked_events": int(row.get("linked_events") or 0),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_read_tokens": int(row.get("cache_read_tokens") or 0),
                    "cache_write_tokens": int(row.get("cache_write_tokens") or 0),
                    "thinking_tokens": int(row.get("thinking_tokens") or 0),
                    "total_tokens": max(token_total(row) or input_tokens + output_tokens, parsed_tokens),
                    "cache_hit_rate": cache_hit_rate(row),
                    "total_cost_usd": round(float(row.get("total_cost_usd") or 0.0), 6),
                    "prompt": parsed.prompt if parsed else "",
                    "team_id": parsed.team_id if parsed else "",
                    "parent_id": parsed.parent_id if parsed else "",
                    "approval_wait": bool(parsed.approval_wait) if parsed else False,
                }
            )

        total_cost = float(totals.get("actual_cost_usd_sum") or 0.0) + float(totals.get("estimated_only_cost_usd_sum") or 0.0)
        return {
            "display_day": str(dashboard_payload.get("display_day") or ""),
            "collector": collector,
            "totals": {
                "input_tokens": int(totals.get("input_tokens") or 0),
                "output_tokens": int(totals.get("output_tokens") or 0),
                "cache_read_tokens": int(totals.get("cache_read_tokens") or 0),
                "cache_write_tokens": int(totals.get("cache_write_tokens") or 0),
                "thinking_tokens": int(totals.get("thinking_tokens") or 0),
                "total_tokens": token_total(totals),
                "cache_hit_rate": cache_hit_rate(totals),
                "total_cost_usd": round(total_cost, 6),
            },
            "agents": agent_rows,
        }

    @staticmethod
    def agent_state_by_name(runtime_status: dict) -> dict[str, dict]:
        lanes = runtime_status.get("lanes") if isinstance(runtime_status.get("lanes"), list) else []
        return {
            str(lane.get("name") or "").strip(): lane
            for lane in lanes
            if isinstance(lane, dict) and str(lane.get("name") or "").strip()
        }

    def inspector_payload(self, *, agent_name: str, runtime_status: dict, dashboard_payload: dict, tail_text: str) -> dict:
        with self._lock:
            lanes_by_name = self.agent_state_by_name(runtime_status)
            lane = lanes_by_name.get(agent_name, {})
            role = self.role_for_agent(agent_name, runtime_status)
            hud_agent = next((item for item in self.monitor_hud(runtime_status, dashboard_payload).get("agents", []) if item.get("name") == agent_name), {})
            parsed = self.agent_state.get(agent_name)
            tail_summary = summarize_agent_tail(tail_text)
            current_prompt = tail_summary["current_prompt"] or str(lane.get("note") or "") or (parsed.prompt if parsed else "")
            return {
                "ok": True,
                "agent": {
                    "id": agent_name,
                    "role": role,
                    "state": str(lane.get("state") or hud_agent.get("state") or (parsed.state if parsed else "") or "off"),
                    "note": str(lane.get("note") or lane.get("status_note") or ""),
                    "pid": lane.get("pid"),
                    "last_event_at": str(lane.get("last_event_at") or ""),
                },
                "metrics": hud_agent,
                "coordination": {
                    "team_id": parsed.team_id if parsed else "",
                    "parent_id": parsed.parent_id if parsed else "",
                    "event_type": parsed.event_type if parsed else "",
                    "target_agent_id": parsed.target_agent_id if parsed else "",
                    "approval_wait": bool(parsed.approval_wait) if parsed else False,
                },
                "current_prompt": current_prompt,
                "conversation": tail_summary["conversation"],
                "tail": tail_text,
                "source": {
                    "tail_lines": tail_summary["line_count"],
                    "parsed_log_path": parsed.last_source_path if parsed else "",
                    "read_only": True,
                },
            }

    @staticmethod
    def role_for_agent(agent_name: str, runtime_status: dict) -> str:
        owners = runtime_status.get("role_owners") if isinstance(runtime_status.get("role_owners"), dict) else {}
        for role in ("implement", "verify", "advisory"):
            if owners.get(role) == agent_name:
                return role
        return {
            "Claude": "implement",
            "Codex": "verify",
            "Gemini": "advisory",
        }.get(agent_name, "")


def summarize_agent_tail(tail_text: str, *, max_lines: int = 12) -> dict:
    lines = [line.rstrip() for line in str(tail_text or "").splitlines() if line.strip()]
    prompt = ""
    for line in reversed(lines):
        if re.search(r"\b(prompt|request|task|사용자|user)\b", line, re.IGNORECASE):
            prompt = line.strip()
            break
    if not prompt and lines:
        prompt = lines[-1].strip()
    return {
        "current_prompt": prompt[:1200],
        "conversation": lines[-max_lines:],
        "line_count": len(lines),
    }
