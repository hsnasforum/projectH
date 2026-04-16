from __future__ import annotations

import argparse
import errno
import fcntl
import json
import os
import pty
import re
import selectors
import shlex
import signal
import struct
import subprocess
import sys
import termios
import threading
import time
import tty
from pathlib import Path

from pipeline_gui.project import _session_name_for

from .schema import read_json
from .supervisor import RuntimeSupervisor
from .tmux_adapter import TmuxAdapter
from .wrapper_events import append_wrapper_event

_BUSY_MARKERS = (
    "working (",
    "background terminal",
    "waiting for background",
    "waited for background",
    "cascading",
    "lollygagging",
    "hashing",
    "leavering",
    "without interrupting claude's current work",
    "thinking",
    "esc to cancel",
)

_ACTIVITY_MARKERS = _BUSY_MARKERS + (
    "now let me",
    "searching for",
    "searched for",
    "read ",
    "reading ",
    "bash(",
    "explored",
    "ideating",
    "gallivanting",
    "sautéed",
    "implemented",
    "updated ",
    "applied patch",
    "editing ",
    "edited ",
)

_TASK_DONE_SETTLE_SEC = 1.5

_READY_MARKERS = {
    "Claude": ("❯", "claude code", "bypass permissions"),
    "Codex": ("›", "openai codex"),
    "Gemini": ("type your message", "gemini cli", "workspace"),
}
_CODEX_UPDATE_SKIP_MARKERS = (
    "update available",
    "update now",
    "skip until next version",
)


def _project_root(value: str | None) -> Path:
    if value:
        return Path(value).resolve()
    return Path.cwd().resolve()


def _normalize_project_and_mode(args: argparse.Namespace) -> tuple[Path, str]:
    mode = str(getattr(args, "mode", "") or "experimental")
    first = str(getattr(args, "project_root", "") or "").strip()
    second = str(getattr(args, "legacy_mode", "") or "").strip()
    if first in {"baseline", "experimental", "both"} and not second:
        mode = first
        first = ""
    elif second in {"baseline", "experimental", "both"}:
        mode = second
    return _project_root(first or None), mode


def _supervisor_pid_path(project_root: Path) -> Path:
    return project_root / ".pipeline" / "supervisor.pid"


def _supervisor_running(project_root: Path) -> int | None:
    path = _supervisor_pid_path(project_root)
    if not path.exists():
        return None
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def _command_arg_value(argv: list[str], flag: str) -> str:
    for index, token in enumerate(argv):
        if token == flag and index + 1 < len(argv):
            return argv[index + 1]
        if token.startswith(f"{flag}="):
            return token.split("=", 1)[1]
    return ""


def _list_supervisor_pids(
    project_root: Path,
    session_name: str,
    *,
    proc_root: Path | None = None,
) -> list[int]:
    resolved_root = str(project_root.resolve())
    resolved_session = str(session_name or "").strip()
    root = proc_root or Path("/proc")
    if not root.exists():
        return []
    matched: list[int] = []
    for entry in root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        argv = [part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part]
        if not argv or "daemon" not in argv:
            continue
        joined = " ".join(argv)
        if "pipeline_runtime.cli" not in joined:
            continue
        if _command_arg_value(argv, "--project-root") != resolved_root:
            continue
        if resolved_session and _command_arg_value(argv, "--session") != resolved_session:
            continue
        matched.append(int(entry.name))
    return sorted(set(matched))


def _kill_pid(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    deadline = time.time() + 3.0
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass


def _signal_pid(pid: int, sig: int) -> None:
    try:
        os.kill(pid, sig)
    except OSError:
        return


def _wait_for_supervisors_exit(
    project_root: Path,
    session_name: str,
    *,
    proc_root: Path | None = None,
    timeout: float = 30.0,
) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _list_supervisor_pids(project_root, session_name, proc_root=proc_root):
            return True
        time.sleep(0.25)
    return False


def _current_runtime_status(project_root: Path) -> dict[str, object] | None:
    current_run = read_json(project_root / ".pipeline" / "current_run.json")
    if not isinstance(current_run, dict):
        return None
    status_path_value = str(current_run.get("status_path") or "").strip()
    if status_path_value:
        status = read_json(project_root / status_path_value)
        if isinstance(status, dict):
            return status
    run_id = str(current_run.get("run_id") or "").strip()
    if not run_id:
        return None
    status = read_json(project_root / ".pipeline" / "runs" / run_id / "status.json")
    return status if isinstance(status, dict) else None


def _stop_status_flushed(project_root: Path) -> bool:
    status = _current_runtime_status(project_root)
    if not isinstance(status, dict):
        return False
    runtime_state = str(status.get("runtime_state") or "").upper()
    control_status = str(((status.get("control") or {}).get("active_control_status") or "none"))
    active_round = status.get("active_round")
    watcher_alive = bool(((status.get("watcher") or {}).get("alive")))
    lanes = [lane for lane in list(status.get("lanes") or []) if isinstance(lane, dict)]
    lanes_stopped = all(str(lane.get("state") or "OFF").upper() == "OFF" for lane in lanes)
    return (
        runtime_state == "STOPPED"
        and control_status == "none"
        and active_round is None
        and not watcher_alive
        and lanes_stopped
    )


def _wait_for_stop_completion(
    project_root: Path,
    session_name: str,
    *,
    proc_root: Path | None = None,
    timeout: float = 12.0,
) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        supervisors_gone = not _list_supervisor_pids(project_root, session_name, proc_root=proc_root)
        if supervisors_gone and _stop_status_flushed(project_root):
            return True
        time.sleep(0.25)
    return False


def _reconcile_supervisors(
    project_root: Path,
    session_name: str,
    *,
    proc_root: Path | None = None,
) -> int | None:
    pid_path = _supervisor_pid_path(project_root)
    pidfile_pid = _supervisor_running(project_root)
    live_pids = _list_supervisor_pids(project_root, session_name, proc_root=proc_root)
    if not live_pids:
        try:
            pid_path.unlink()
        except FileNotFoundError:
            pass
        return None
    if len(live_pids) == 1:
        live_pid = live_pids[0]
        if pidfile_pid != live_pid:
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text(str(live_pid), encoding="utf-8")
        return live_pid
    for pid in live_pids:
        _kill_pid(pid)
    _wait_for_supervisors_exit(project_root, session_name, proc_root=proc_root, timeout=5.0)
    try:
        pid_path.unlink()
    except FileNotFoundError:
        pass
    return None


def _spawn_supervisor(args: argparse.Namespace) -> int:
    project_root, mode = _normalize_project_and_mode(args)
    session_name = args.session or _session_name_for(project_root)
    pid = _reconcile_supervisors(project_root, session_name)
    if pid is not None:
        return 0
    run_id = RuntimeSupervisor(project_root, session_name=args.session, mode=mode, start_runtime=False).run_id
    log_dir = project_root / ".pipeline" / "runs" / run_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "supervisor.log"
    with log_path.open("a", encoding="utf-8") as handle:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "pipeline_runtime.cli",
                "daemon",
                "--project-root",
                str(project_root),
                "--session",
                session_name,
                "--mode",
                mode,
                "--run-id",
                run_id,
            ],
            cwd=str(project_root),
            stdout=handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    deadline = time.time() + 20.0
    while time.time() < deadline:
        current_run = read_json(project_root / ".pipeline" / "current_run.json")
        status = read_json(project_root / ".pipeline" / "runs" / run_id / "status.json")
        if current_run and status:
            return 0
        if process.poll() is not None:
            return process.returncode or 1
        time.sleep(0.25)
    return 1


def _stop_supervisor(args: argparse.Namespace) -> int:
    project_root, _mode = _normalize_project_and_mode(args)
    session_name = args.session or _session_name_for(project_root)
    pids = set(_list_supervisor_pids(project_root, session_name))
    pid = _supervisor_running(project_root)
    if pid is not None:
        pids.add(pid)
    if not pids:
        try:
            _supervisor_pid_path(project_root).unlink()
        except FileNotFoundError:
            pass
        return 0
    for live_pid in sorted(pids):
        _signal_pid(live_pid, signal.SIGTERM)
    if not _wait_for_stop_completion(project_root, session_name):
        remaining = _list_supervisor_pids(project_root, session_name)
        for live_pid in sorted(remaining):
            _kill_pid(live_pid)
        _wait_for_supervisors_exit(project_root, session_name, timeout=5.0)
        try:
            _supervisor_pid_path(project_root).unlink()
        except FileNotFoundError:
            pass
        return 1
    try:
        _supervisor_pid_path(project_root).unlink()
    except FileNotFoundError:
        pass
    return 0


def _restart_supervisor(args: argparse.Namespace) -> int:
    stop_code = _stop_supervisor(args)
    if stop_code != 0:
        return stop_code
    time.sleep(1.0)
    return _spawn_supervisor(args)


def _attach(args: argparse.Namespace) -> int:
    project_root = _project_root(args.project_root)
    adapter = TmuxAdapter(project_root, args.session or _session_name_for(project_root))
    adapter.attach(args.lane)
    return 0


def _load_task_hint(task_hint_dir: Path | None, lane_name: str) -> dict[str, object]:
    if task_hint_dir is None:
        return {}
    path = task_hint_dir / f"{lane_name.strip().lower()}.json"
    data = read_json(path)
    return data if isinstance(data, dict) else {}


def _text_is_busy(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in _BUSY_MARKERS)


def _is_codex_update_prompt(text: str) -> bool:
    lower = text.lower()
    return all(marker in lower for marker in _CODEX_UPDATE_SKIP_MARKERS)


def _text_is_ready(lane_name: str, text: str) -> bool:
    if lane_name == "Codex" and _is_codex_update_prompt(text):
        return False
    markers = _READY_MARKERS.get(lane_name, ())
    lower = text.lower()
    return any(marker.lower() in lower for marker in markers)


def _lines_match_markers(lines: list[str], markers: tuple[str, ...]) -> bool:
    if not lines:
        return False
    lowered = "\n".join(lines).lower()
    return any(marker.lower() in lowered for marker in markers)


class _WrapperEmitter:
    def __init__(
        self,
        *,
        wrapper_dir: Path,
        lane_name: str,
        task_hint_dir: Path | None,
        child_pid: int,
        send_child_bytes,
    ) -> None:
        self.wrapper_dir = wrapper_dir
        self.lane_name = lane_name
        self.task_hint_dir = task_hint_dir
        self.child_pid = child_pid
        self.send_child_bytes = send_child_bytes
        self.partial = ""
        self.recent_lines: list[str] = []
        self.ready_emitted = False
        self.busy_state = False
        self.accepted_key = ""
        self.accepted_payload: dict[str, object] | None = None
        self._auto_actions_sent: set[str] = set()
        self._last_activity_at = 0.0
        self._task_inactive_since = 0.0

    def append(self, event_type: str, payload: dict[str, object], *, derived_from: str) -> None:
        append_wrapper_event(
            self.wrapper_dir,
            self.lane_name,
            event_type,
            {"pid": self.child_pid, **payload},
            source="wrapper",
            derived_from=derived_from,
        )

    def feed(self, text: str, *, now: float | None = None) -> None:
        if not text:
            return
        combined = self.partial + text
        lines = combined.splitlines(keepends=False)
        if combined and not combined.endswith(("\n", "\r")):
            self.partial = lines.pop() if lines else combined
        else:
            self.partial = ""
        new_lines: list[str] = []
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            self.recent_lines.append(cleaned)
            new_lines.append(cleaned)
        self.recent_lines = self.recent_lines[-120:]
        self._evaluate(new_lines, now=now)

    def tick(self, *, now: float | None = None) -> None:
        self._evaluate([], now=now)

    def _emit_task_done(self, reason: str = "") -> None:
        if not self.accepted_key or not self.accepted_payload:
            return
        payload = {
            "job_id": str(self.accepted_payload.get("job_id") or ""),
            "control_seq": int(self.accepted_payload.get("control_seq") or -1),
        }
        if reason:
            payload["reason"] = reason
        self.append(
            "TASK_DONE",
            payload,
            derived_from="vendor_output",
        )
        self.accepted_key = ""
        self.accepted_payload = None
        self._task_inactive_since = 0.0

    def _emit_ready(self) -> None:
        if not self.ready_emitted or self.busy_state:
            self.append("READY", {"reason": "prompt_visible"}, derived_from="vendor_output")
        self.ready_emitted = True
        self.busy_state = False

    def _evaluate(self, new_lines: list[str], *, now: float | None = None) -> None:
        if not self.recent_lines:
            return
        now_value = float(now) if now is not None else time.monotonic()
        text = "\n".join(self.recent_lines[-40:])
        if self._maybe_auto_dismiss_blocking_prompt(text):
            return
        activity_detected = _lines_match_markers(new_lines, _ACTIVITY_MARKERS)
        ready_detected = _lines_match_markers(new_lines, _READY_MARKERS.get(self.lane_name, ()))
        task_hint = _load_task_hint(self.task_hint_dir, self.lane_name)
        job_id = str(task_hint.get("job_id") or "")
        control_seq = int(task_hint.get("control_seq") or -1)
        attempt = int(task_hint.get("attempt") or 0)
        inactive_reason = str(task_hint.get("inactive_reason") or "")
        task_active = bool(task_hint.get("active")) and bool(job_id) and control_seq >= 0
        task_key = f"{job_id}|{control_seq}" if task_active else ""

        if activity_detected and task_active:
            if self.accepted_key != task_key:
                self.accepted_key = task_key
                self.accepted_payload = {
                    "job_id": job_id,
                    "control_seq": control_seq,
                    "attempt": attempt,
                }
                self.append("TASK_ACCEPTED", dict(self.accepted_payload), derived_from="vendor_output")
                self._task_inactive_since = 0.0
            self._last_activity_at = now_value
            self.busy_state = True

        if self.accepted_key and self.accepted_payload:
            current_task_still_active = task_active and task_key == self.accepted_key
            if current_task_still_active:
                self._task_inactive_since = 0.0
                return
            if not self._task_inactive_since:
                self._task_inactive_since = now_value
            if (
                (ready_detected or _text_is_ready(self.lane_name, text))
                and self._task_inactive_since
                and (now_value - self._last_activity_at) >= _TASK_DONE_SETTLE_SEC
                and (now_value - self._task_inactive_since) >= _TASK_DONE_SETTLE_SEC
            ):
                self._emit_task_done(inactive_reason or "task_hint_cleared")
                self._emit_ready()
            return

        if ready_detected or (_text_is_ready(self.lane_name, text) and not activity_detected):
            self._emit_ready()

    def _maybe_auto_dismiss_blocking_prompt(self, text: str) -> bool:
        if self.lane_name != "Codex":
            return False
        if not _is_codex_update_prompt(text):
            return False
        action_key = "codex_update_skip_until_next_version"
        if action_key in self._auto_actions_sent:
            return True
        # Choose "Skip until next version" instead of Enter, because Enter would
        # accept the default update action and make unattended runtime startup depend on npm/network.
        self.send_child_bytes(b"3\r")
        self._auto_actions_sent.add(action_key)
        return True


def _set_pty_size_from_stdin(slave_fd: int) -> None:
    if not sys.stdin.isatty():
        return
    try:
        packed = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, packed)
    except OSError:
        return


def _lane_wrapper(args: argparse.Namespace) -> int:
    project_root = _project_root(args.project_root)
    wrapper_dir = project_root / ".pipeline" / "runs" / args.run_id / "wrapper-events"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    task_hint_dir = Path(args.task_hint_dir).resolve() if args.task_hint_dir else None

    master_fd, slave_fd = pty.openpty()
    _set_pty_size_from_stdin(slave_fd)
    child = subprocess.Popen(
        args.shell_command,
        shell=True,
        executable="/bin/bash",
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=str(project_root),
        preexec_fn=os.setsid,
    )
    os.close(slave_fd)

    emitter = _WrapperEmitter(
        wrapper_dir=wrapper_dir,
        lane_name=args.lane,
        task_hint_dir=task_hint_dir,
        child_pid=child.pid,
        send_child_bytes=lambda data: os.write(master_fd, data),
    )

    stop_requested = False
    saved_tty = termios.tcgetattr(sys.stdin.fileno()) if sys.stdin.isatty() else None
    if saved_tty is not None:
        tty.setraw(sys.stdin.fileno())

    def _forward(signum: int, _frame) -> None:
        nonlocal stop_requested
        stop_requested = True
        try:
            os.killpg(child.pid, signum)
        except OSError:
            pass

    signal.signal(signal.SIGTERM, _forward)
    signal.signal(signal.SIGINT, _forward)

    selector = selectors.DefaultSelector()
    selector.register(master_fd, selectors.EVENT_READ)
    stdin_fd = sys.stdin.fileno()
    if os.isatty(stdin_fd):
        selector.register(stdin_fd, selectors.EVENT_READ)

    last_heartbeat = 0.0
    try:
        while True:
            now = time.time()
            if (now - last_heartbeat) >= max(1.0, float(args.heartbeat_interval)):
                append_wrapper_event(
                    wrapper_dir,
                    args.lane,
                    "HEARTBEAT",
                    {"pid": child.pid},
                    source="wrapper",
                    derived_from="process_alive",
                )
                last_heartbeat = now
                emitter.tick(now=now)

            for key, _mask in selector.select(timeout=0.25):
                fd = key.fd
                if fd == master_fd:
                    try:
                        chunk = os.read(master_fd, 4096)
                    except OSError as exc:
                        if exc.errno == errno.EIO:
                            chunk = b""
                        else:
                            raise
                    if chunk:
                        os.write(sys.stdout.fileno(), chunk)
                        sys.stdout.flush()
                        emitter.feed(chunk.decode("utf-8", errors="replace"))
                elif fd == stdin_fd:
                    data = os.read(stdin_fd, 1024)
                    if data:
                        os.write(master_fd, data)

            if child.poll() is not None:
                try:
                    while True:
                        chunk = os.read(master_fd, 4096)
                        if not chunk:
                            break
                        os.write(sys.stdout.fileno(), chunk)
                        sys.stdout.flush()
                        emitter.feed(chunk.decode("utf-8", errors="replace"))
                except OSError:
                    pass
                break
            if stop_requested:
                break
    finally:
        if saved_tty is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, saved_tty)
        try:
            selector.close()
        except Exception:
            pass
        try:
            os.close(master_fd)
        except OSError:
            pass

    returncode = child.wait()
    append_wrapper_event(
        wrapper_dir,
        args.lane,
        "BROKEN",
        {"pid": child.pid, "reason": f"exit:{returncode}"},
        source="wrapper",
        derived_from="process_exit",
    )
    return returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline_runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start")
    start.add_argument("project_root", nargs="?")
    start.add_argument("legacy_mode", nargs="?")
    start.add_argument("--mode", default="experimental")
    start.add_argument("--session", default="")
    start.add_argument("--no-attach", action="store_true")

    stop = sub.add_parser("stop")
    stop.add_argument("project_root", nargs="?")
    stop.add_argument("legacy_mode", nargs="?")
    stop.add_argument("--session", default="")

    restart = sub.add_parser("restart")
    restart.add_argument("project_root", nargs="?")
    restart.add_argument("legacy_mode", nargs="?")
    restart.add_argument("--mode", default="experimental")
    restart.add_argument("--session", default="")
    restart.add_argument("--no-attach", action="store_true")

    daemon = sub.add_parser("daemon")
    daemon.add_argument("--project-root", default="")
    daemon.add_argument("--mode", default="experimental")
    daemon.add_argument("--session", default="")
    daemon.add_argument("--run-id", default="")

    attach = sub.add_parser("attach")
    attach.add_argument("--project-root", default="")
    attach.add_argument("--session", default="")
    attach.add_argument("--lane", default=None)

    lane_wrapper = sub.add_parser("lane-wrapper")
    lane_wrapper.add_argument("--project-root", default="")
    lane_wrapper.add_argument("--run-id", required=True)
    lane_wrapper.add_argument("--lane", required=True)
    lane_wrapper.add_argument("--shell-command", required=True)
    lane_wrapper.add_argument("--task-hint-dir", default="")
    lane_wrapper.add_argument("--heartbeat-interval", type=float, default=5.0)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "start":
        return _spawn_supervisor(args)
    if args.command == "stop":
        return _stop_supervisor(args)
    if args.command == "restart":
        return _restart_supervisor(args)
    if args.command == "daemon":
        project_root = _project_root(args.project_root)
        supervisor = RuntimeSupervisor(
            project_root,
            session_name=args.session or _session_name_for(project_root),
            run_id=args.run_id or None,
            mode=args.mode,
            start_runtime=True,
        )
        return supervisor.run()
    if args.command == "attach":
        return _attach(args)
    if args.command == "lane-wrapper":
        return _lane_wrapper(args)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
