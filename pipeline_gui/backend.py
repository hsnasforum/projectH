"""tmux/watcher lifecycle, pipeline start/stop, file helpers."""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from .platform import (
    IS_WINDOWS, WSL_DISTRO, APP_ROOT,
    CREATE_NO_WINDOW, FILE_QUERY_TIMEOUT,
    _wsl_path_str, _windows_to_wsl_mount, _run, _hidden_subprocess_kwargs,
)
from .project import _session_name_for


def tmux_alive(session: str = "") -> bool:
    code, _ = _run(["tmux", "has-session", "-t", session or "ai-pipeline"])
    return code == 0


def watcher_alive(project: Path) -> tuple[bool, int | None]:
    pid_path = project / ".pipeline" / "experimental.pid"
    if IS_WINDOWS:
        code, content = _run(["cat", _wsl_path_str(pid_path)])
        if code != 0 or not content.strip():
            return False, None
        try:
            pid = int(content.strip())
        except ValueError:
            return False, None
        check_code, _ = _run(["kill", "-0", str(pid)])
        return check_code == 0, pid
    else:
        if not pid_path.exists():
            return False, None
        try:
            pid = int(pid_path.read_text().strip())
            os.kill(pid, 0)
            return True, pid
        except (ValueError, OSError):
            return False, None


def latest_md(directory: Path) -> tuple[str, float]:
    if IS_WINDOWS:
        code, output = _run([
            "find", _wsl_path_str(directory), "-name", "*.md", "-type", "f",
            "-printf", "%T@\\t%P\\n",
        ], timeout=FILE_QUERY_TIMEOUT)
        if code != 0 or not output.strip():
            return "—", 0.0
        best_mtime = 0.0
        best_rel = ""
        for line in output.strip().splitlines():
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            try:
                mt = float(parts[0])
            except ValueError:
                continue
            if mt > best_mtime:
                best_mtime = mt
                best_rel = parts[1]
        return (best_rel or "—"), best_mtime
    else:
        best_path: Path | None = None
        best_mtime: float = 0.0
        if not directory.exists():
            return "—", 0.0
        for md in directory.rglob("*.md"):
            try:
                mt = md.stat().st_mtime
                if mt > best_mtime:
                    best_mtime = mt
                    best_path = md
            except OSError:
                continue
        if best_path is None:
            return "—", 0.0
        try:
            rel = str(best_path.relative_to(directory))
        except ValueError:
            rel = best_path.name
        return rel, best_mtime


def time_ago(mtime: float) -> str:
    if mtime == 0:
        return ""
    diff = int(time.time() - mtime)
    if diff < 60:
        return f"{diff}초 전"
    if diff < 3600:
        return f"{diff // 60}분 전"
    return f"{diff // 3600}시간 전"


def watcher_log_tail(project: Path, lines: int = 5) -> list[str]:
    log_path = project / ".pipeline" / "logs" / "experimental" / "watcher.log"
    if IS_WINDOWS:
        code, content = _run(["tail", "-n", str(max(lines * 8, 40)), _wsl_path_str(log_path)], timeout=FILE_QUERY_TIMEOUT)
        if code != 0:
            content = ""
        if not content:
            return ["(로그 없음)"]
        all_lines = content.splitlines()
    else:
        if not log_path.exists():
            return ["(로그 없음)"]
        try:
            all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return ["(읽기 실패)"]
    filtered = [l for l in all_lines if "suppressed" not in l and "A/B ratio" not in l]
    return filtered[-lines:] if filtered else ["(이벤트 없음)"]


def pipeline_start(project: Path, session: str = "") -> str:
    sess = session or _session_name_for(project)
    script = APP_ROOT / "start-pipeline.sh"
    if IS_WINDOWS:
        wsl_script = _windows_to_wsl_mount(script)
        wsl_project = _wsl_path_str(project)
        subprocess.Popen(
            ["wsl.exe", "-d", WSL_DISTRO, "--cd", wsl_project, "--",
             "bash", "-l", wsl_script, wsl_project,
             "--mode", "experimental", "--no-attach", "--session", sess],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
    else:
        if not script.exists():
            return "start-pipeline.sh 없음"
        log_path = project / ".pipeline" / "logs" / "experimental" / "pipeline-launcher-start.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as logf:
            subprocess.Popen(
                ["bash", "-l", str(script), str(project),
                 "--mode", "experimental", "--no-attach", "--session", sess],
                cwd=str(project), stdout=logf, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, start_new_session=True,
            )
    return "시작 요청됨"


def pipeline_stop(project: Path, session: str = "") -> str:
    sess = session or _session_name_for(project)
    script = APP_ROOT / "stop-pipeline.sh"
    if IS_WINDOWS:
        wsl_script = _windows_to_wsl_mount(script)
        wsl_project = _wsl_path_str(project)
        subprocess.run(
            ["wsl.exe", "-d", WSL_DISTRO, "--cd", wsl_project, "--",
             "bash", wsl_script, wsl_project, "--session", sess],
            capture_output=True, timeout=15,
            **_hidden_subprocess_kwargs(),
        )
    else:
        if not script.exists():
            return "stop-pipeline.sh 없음"
        subprocess.run(
            ["bash", str(script), str(project), "--session", sess],
            capture_output=True, timeout=15,
        )
    return "중지 완료"


def tmux_attach(session: str) -> None:
    if IS_WINDOWS:
        subprocess.Popen(
            ["cmd", "/c", "start", "wsl.exe", "-d", WSL_DISTRO, "--",
             "bash", "-lc", f"tmux attach -t {session}"],
            creationflags=CREATE_NO_WINDOW,
        )
    else:
        subprocess.Popen(
            ["bash", "-c", f"tmux attach -t {session}"],
            start_new_session=True,
        )
