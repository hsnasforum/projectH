from __future__ import annotations

import errno
import os
import pty
import signal
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Any


class PtyLane:
    def __init__(self, lane_name: str, shell_command: str, project_root: Path) -> None:
        self.lane_name = lane_name
        self.shell_command = shell_command
        self.project_root = Path(project_root)
        self._buffer: deque[str] = deque(maxlen=200)
        self._lock = threading.Lock()
        self._child: subprocess.Popen[Any] | None = None
        self._master_fd: int | None = None
        self._reader_thread: threading.Thread | None = None
        self._alive = False

    def spawn(self) -> bool:
        if self.is_alive():
            return True

        master_fd: int | None = None
        slave_fd: int | None = None
        try:
            master_fd, slave_fd = pty.openpty()
            child = subprocess.Popen(
                self.shell_command,
                shell=True,
                executable="/bin/bash",
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=str(self.project_root),
                preexec_fn=os.setsid,
            )
        except OSError:
            if master_fd is not None:
                self._close_fd(master_fd)
            if slave_fd is not None:
                self._close_fd(slave_fd)
            return False
        except Exception:
            if master_fd is not None:
                self._close_fd(master_fd)
            if slave_fd is not None:
                self._close_fd(slave_fd)
            return False
        finally:
            if slave_fd is not None:
                self._close_fd(slave_fd)

        with self._lock:
            self._buffer.clear()
            self._child = child
            self._master_fd = master_fd
            self._alive = True

        thread = threading.Thread(target=self._reader_loop, name=f"pty-lane-{self.lane_name}", daemon=True)
        with self._lock:
            self._reader_thread = thread
        thread.start()
        return True

    def send(self, text: str) -> bool:
        with self._lock:
            master_fd = self._master_fd
        if master_fd is None or not self.is_alive():
            return False
        try:
            os.write(master_fd, text.encode("utf-8"))
            return True
        except OSError:
            return False

    def capture(self, lines: int = 100) -> str:
        if lines <= 0:
            return ""
        with self._lock:
            return "\n".join(list(self._buffer)[-lines:])

    def is_alive(self) -> bool:
        with self._lock:
            child = self._child
            alive = self._alive
        return bool(alive and child is not None and child.poll() is None)

    def kill(self) -> bool:
        with self._lock:
            child = self._child
            master_fd = self._master_fd
            thread = self._reader_thread
            self._alive = False
            self._master_fd = None

        if child is None and master_fd is None:
            return False

        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except OSError:
                pass
            try:
                child.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except OSError:
                    pass
                try:
                    child.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    pass

        if master_fd is not None:
            self._close_fd(master_fd)
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)
        return True

    def health(self) -> dict[str, Any]:
        with self._lock:
            child = self._child
        exit_code = child.poll() if child is not None else None
        return {
            "name": self.lane_name,
            "alive": self.is_alive(),
            "pid": child.pid if child is not None else None,
            "exit_code": exit_code,
        }

    def _reader_loop(self) -> None:
        pending = ""
        while True:
            with self._lock:
                master_fd = self._master_fd
            if master_fd is None:
                break
            try:
                chunk = os.read(master_fd, 4096)
            except OSError as exc:
                if exc.errno in {errno.EBADF, errno.EIO}:
                    break
                break
            if not chunk:
                break
            pending += chunk.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
            pending = self._append_complete_lines(pending)

        if pending:
            with self._lock:
                self._buffer.append(pending)
        with self._lock:
            self._alive = False

    def _append_complete_lines(self, pending: str) -> str:
        while "\n" in pending:
            line, pending = pending.split("\n", 1)
            with self._lock:
                self._buffer.append(line)
        return pending

    @staticmethod
    def _close_fd(fd: int) -> None:
        try:
            os.close(fd)
        except OSError:
            pass


class PtyAdapter:
    def __init__(self, project_root: Path, session_name: str) -> None:
        self.project_root = Path(project_root)
        self.session_name = session_name
        self._lanes: dict[str, PtyLane] = {}

    def spawn_lane(self, lane_name: str, shell_command: str) -> bool:
        existing = self._lanes.get(lane_name)
        if existing is not None:
            existing.kill()

        lane = PtyLane(lane_name, shell_command, self.project_root)
        if not lane.spawn():
            self._lanes.pop(lane_name, None)
            return False
        self._lanes[lane_name] = lane
        return True

    def kill_lane(self, lane_name: str) -> bool:
        lane = self._lanes.get(lane_name)
        if lane is None:
            return False
        return lane.kill()

    def terminate_lane(self, lane_name: str) -> bool:
        return self.kill_lane(lane_name)

    def restart_lane(self, lane_name: str, shell_command: str) -> bool:
        if not self.kill_lane(lane_name):
            return False
        return self.spawn_lane(lane_name, shell_command)

    def send_input(self, lane_name: str, payload: str) -> bool:
        lane = self._lanes.get(lane_name)
        if lane is None:
            return False
        return lane.send(payload)

    def capture_tail(self, lane_name: str, lines: int = 100) -> str:
        lane = self._lanes.get(lane_name)
        if lane is None:
            return ""
        return lane.capture(lines)

    def lane_health(self, lane_name: str) -> dict[str, Any]:
        lane = self._lanes.get(lane_name)
        if lane is None:
            return {"name": lane_name, "alive": False, "pid": None, "exit_code": None}
        return lane.health()

    def session_exists(self) -> bool:
        return any(lane.is_alive() for lane in self._lanes.values())

    def health(self) -> dict[str, Any]:
        return {
            "session": self.session_exists(),
            "lanes": {lane_name: lane.health() for lane_name, lane in self._lanes.items()},
        }


class PtyLaneBridge:
    def __init__(self) -> None:
        self._lanes_by_target: dict[str, PtyLane] = {}

    def register(self, pane_target: str, lane_name: str, shell_command: str, project_root: Path) -> bool:
        target = str(pane_target or "").strip()
        name = str(lane_name or "").strip()
        command = str(shell_command or "").strip()
        if not target or not name or not command:
            return False

        existing = self._lanes_by_target.get(target)
        if existing is not None:
            existing.kill()

        lane = PtyLane(name, command, Path(project_root))
        if not lane.spawn():
            self._lanes_by_target.pop(target, None)
            return False
        self._lanes_by_target[target] = lane
        return True

    def capture(self, target: str) -> str | None:
        lane = self._lanes_by_target.get(str(target or "").strip())
        if lane is None or not lane.is_alive():
            return None
        return lane.capture()

    def send(self, target: str, text: str) -> bool | None:
        lane = self._lanes_by_target.get(str(target or "").strip())
        if lane is None or not lane.is_alive():
            return None
        return lane.send(text)

    def teardown(self) -> None:
        for lane in list(self._lanes_by_target.values()):
            lane.kill()
        self._lanes_by_target.clear()
