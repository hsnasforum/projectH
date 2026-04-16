from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any


class TmuxAdapter:
    LANE_INDEX = {"Claude": 0, "Codex": 1, "Gemini": 2}
    DEFAULT_SESSION_COLS = 420
    DEFAULT_SESSION_ROWS = 72

    def __init__(self, project_root: Path, session_name: str, *, run_id: str = "") -> None:
        self.project_root = project_root
        self.session_name = session_name
        self.run_id = run_id

    def _run(self, cmd: list[str], *, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def _pane_pid(self, pane_id: str) -> int | None:
        result = self._run(["tmux", "display-message", "-p", "-t", pane_id, "#{pane_pid}"], timeout=5.0)
        text = result.stdout.strip()
        if result.returncode != 0 or not text.isdigit():
            return None
        return int(text)

    def session_exists(self) -> bool:
        result = self._run(["tmux", "has-session", "-t", self.session_name], timeout=3.0)
        return result.returncode == 0

    def kill_session(self) -> bool:
        if not self.session_exists():
            return True
        result = self._run(["tmux", "kill-session", "-t", self.session_name], timeout=8.0)
        return result.returncode == 0

    def create_scaffold(self) -> dict[str, str]:
        self.kill_session()
        result = self._run(
            [
                "tmux",
                "new-session",
                "-d",
                "-x",
                str(self.DEFAULT_SESSION_COLS),
                "-y",
                str(self.DEFAULT_SESSION_ROWS),
                "-s",
                self.session_name,
                "-c",
                str(self.project_root),
                "bash",
            ],
            timeout=10.0,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "tmux new-session failed")

        session_options = [
            ["tmux", "set-option", "-g", "destroy-unattached", "off"],
            ["tmux", "set-option", "-g", "exit-empty", "off"],
            ["tmux", "set-option", "-t", self.session_name, "destroy-unattached", "off"],
            ["tmux", "set-option", "-t", self.session_name, "mouse", "on"],
            ["tmux", "set-option", "-t", self.session_name, "status-position", "bottom"],
            ["tmux", "set-option", "-t", self.session_name, "status-style", "bg=colour235,fg=colour250"],
            ["tmux", "set-option", "-t", self.session_name, "message-style", "bg=colour235,fg=colour250"],
            ["tmux", "set-option", "-t", self.session_name, "mode-style", "bg=colour238,fg=colour255"],
            ["tmux", "set-option", "-t", self.session_name, "pane-border-style", "fg=colour238"],
            ["tmux", "set-option", "-t", self.session_name, "pane-active-border-style", "fg=colour45"],
            ["tmux", "set-option", "-t", self.session_name, "status-left", "[#S] "],
            [
                "tmux",
                "set-option",
                "-t",
                self.session_name,
                "status-right",
                "#{window_index}:#{window_name} · %H:%M %d-%b-%y",
            ],
            [
                "tmux",
                "set-option",
                "-t",
                self.session_name,
                "status-format[0]",
                "#[align=left]#{status-left}#[default] #[align=right]#{status-right}",
            ],
            ["tmux", "set-window-option", "-t", self.session_name, "window-status-format", "#I:#W"],
            ["tmux", "set-window-option", "-t", self.session_name, "window-status-current-format", "#[bold]#I:#W"],
            ["tmux", "set-window-option", "-t", f"{self.session_name}:0", "remain-on-exit", "on"],
            ["tmux", "set-window-option", "-t", f"{self.session_name}:0", "window-size", "manual"],
        ]
        for cmd in session_options:
            self._run(cmd, timeout=5.0)
        self._run(["tmux", "set-option", "-u", "-t", self.session_name, "status-format[1]"], timeout=5.0)

        claude_pane = self._run(
            ["tmux", "display-message", "-t", f"{self.session_name}:0.0", "-p", "#{pane_id}"],
            timeout=5.0,
        ).stdout.strip()
        codex_pane = self._run(
            [
                "tmux",
                "split-window",
                "-P",
                "-F",
                "#{pane_id}",
                "-h",
                "-t",
                claude_pane,
                "-c",
                str(self.project_root),
                "bash",
            ],
            timeout=5.0,
        ).stdout.strip()
        gemini_pane = self._run(
            [
                "tmux",
                "split-window",
                "-P",
                "-F",
                "#{pane_id}",
                "-h",
                "-t",
                codex_pane,
                "-c",
                str(self.project_root),
                "bash",
            ],
            timeout=5.0,
        ).stdout.strip()
        self._run(["tmux", "select-layout", "-t", f"{self.session_name}:0", "even-horizontal"], timeout=5.0)
        return {"Claude": claude_pane, "Codex": codex_pane, "Gemini": gemini_pane}

    def list_panes(self) -> list[dict[str, Any]]:
        if not self.session_exists():
            return []
        result = self._run(
            [
                "tmux",
                "list-panes",
                "-t",
                f"{self.session_name}:0",
                "-F",
                "#{pane_index}\t#{pane_id}\t#{pane_pid}\t#{pane_dead}",
            ]
        )
        if result.returncode != 0:
            return []
        panes: list[dict[str, Any]] = []
        for raw in result.stdout.splitlines():
            parts = raw.split("\t")
            if len(parts) != 4:
                continue
            try:
                pane_index = int(parts[0])
            except ValueError:
                continue
            panes.append(
                {
                    "pane_index": pane_index,
                    "pane_id": parts[1],
                    "pid": int(parts[2]) if parts[2].isdigit() else 0,
                    "dead": parts[3] == "1",
                }
            )
        return panes

    def pane_for_lane(self, lane_name: str) -> dict[str, Any] | None:
        pane_index = self.LANE_INDEX.get(lane_name)
        if pane_index is None:
            return None
        return next((pane for pane in self.list_panes() if pane["pane_index"] == pane_index), None)

    def lane_health(self, lane_name: str) -> dict[str, Any]:
        pane = self.pane_for_lane(lane_name)
        if pane is None:
            return {"name": lane_name, "alive": False, "pid": None, "attachable": False, "pane_id": None}
        return {
            "name": lane_name,
            "alive": not bool(pane["dead"]),
            "pid": int(pane["pid"]) if pane["pid"] else None,
            "attachable": not bool(pane["dead"]),
            "pane_id": str(pane["pane_id"]),
        }

    def _respawn_pane(self, pane_id: str, shell_command: str) -> bool:
        result = self._run(
            [
                "tmux",
                "respawn-pane",
                "-k",
                "-t",
                pane_id,
                "-c",
                str(self.project_root),
                shell_command,
            ],
            timeout=12.0,
        )
        return result.returncode == 0

    def spawn_lane(self, lane_name: str, shell_command: str) -> bool:
        pane = self.pane_for_lane(lane_name)
        if pane is None:
            return False
        return self._respawn_pane(str(pane["pane_id"]), shell_command)

    def restart_lane(self, lane_name: str, shell_command: str) -> bool:
        return self.spawn_lane(lane_name, shell_command)

    def terminate_lane(self, lane_name: str) -> bool:
        pane = self.pane_for_lane(lane_name)
        if pane is None:
            return False
        return self._respawn_pane(str(pane["pane_id"]), "exec bash")

    def spawn_watcher(self, *, window_name: str, shell_command: str) -> dict[str, Any]:
        result = self._run(
            [
                "tmux",
                "new-window",
                "-d",
                "-P",
                "-F",
                "#{pane_id}",
                "-t",
                self.session_name,
                "-n",
                window_name,
                "-c",
                str(self.project_root),
                shell_command,
            ],
            timeout=12.0,
        )
        pane_id = result.stdout.strip()
        if result.returncode != 0 or not pane_id:
            raise RuntimeError(result.stderr.strip() or f"tmux new-window failed for {window_name}")
        return {
            "pane_id": pane_id,
            "pid": self._pane_pid(pane_id),
            "window_name": window_name,
        }

    def send_input(self, lane_name: str, payload: str) -> bool:
        pane = self.pane_for_lane(lane_name)
        if pane is None:
            return False
        result = self._run(["tmux", "send-keys", "-t", str(pane["pane_id"]), payload, "C-m"], timeout=5.0)
        return result.returncode == 0

    def capture_tail(self, lane_name: str, lines: int = 100) -> str:
        pane = self.pane_for_lane(lane_name)
        if pane is None:
            return ""
        result = self._run(
            ["tmux", "capture-pane", "-J", "-p", "-t", str(pane["pane_id"]), "-S", f"-{lines}"],
            timeout=5.0,
        )
        return result.stdout if result.returncode == 0 else ""

    def health(self) -> dict[str, Any]:
        return {
            "session": self.session_exists(),
            "lanes": {
                lane_name: self.lane_health(lane_name)
                for lane_name in ("Claude", "Codex", "Gemini")
            },
        }

    def _attach_shell_command(self, lane_name: str | None = None) -> str | None:
        if not self.session_exists():
            return None
        if lane_name:
            pane = self.pane_for_lane(lane_name)
            if pane is not None and not bool(pane.get("dead")):
                target = str(pane["pane_id"])
                return f"tmux select-pane -t {shlex.quote(target)} \\; attach -t {shlex.quote(self.session_name)}"
        return f"tmux attach -t {shlex.quote(self.session_name)}"

    def attach(self, lane_name: str | None = None) -> int:
        command = self._attach_shell_command(lane_name)
        if not command:
            return -1
        process = subprocess.Popen(
            ["bash", "-lc", command],
            start_new_session=True,
        )
        return int(process.pid)

    def attach_blocking(self, lane_name: str | None = None) -> int:
        command = self._attach_shell_command(lane_name)
        if not command:
            return 1
        result = subprocess.run(
            ["bash", "-lc", command],
            text=True,
        )
        return int(result.returncode)
