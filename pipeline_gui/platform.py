"""Platform detection, WSL path conversion, and subprocess wrappers."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"
WSL_DISTRO = os.environ.get("WSL_DISTRO", "Ubuntu")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[/\\]")
CREATE_NO_WINDOW = 0x08000000
TMUX_QUERY_TIMEOUT = 5.0 if IS_WINDOWS else 2.0
FILE_QUERY_TIMEOUT = 10.0 if IS_WINDOWS else 5.0

# PyInstaller onefile exe: runtime assets under sys._MEIPASS/_data/
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    APP_ROOT = Path(sys._MEIPASS) / "_data"
else:
    APP_ROOT = Path(__file__).resolve().parent.parent


def _path_str(path: Path | str) -> str:
    return str(path)


def _windows_native_path(path: Path | str) -> bool:
    raw = _path_str(path)
    return raw.startswith("\\\\") or bool(WINDOWS_DRIVE_RE.match(raw))


def _wsl_path_str(path: Path | str) -> str:
    """WSL internal path display. Leaves Windows native paths unchanged."""
    raw = _path_str(path)
    if not IS_WINDOWS:
        return raw
    if _windows_native_path(raw):
        return raw
    return raw.replace("\\", "/")


def _windows_to_wsl_mount(path: Path | str) -> str:
    """Convert Windows native path to WSL /mnt/... path.

    C:\\Users\\foo\\bar → /mnt/c/Users/foo/bar
    /home/user/proj    → /home/user/proj  (passthrough)
    """
    raw = _path_str(path).replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/(.*)$", raw)
    if m:
        drive = m.group(1).lower()
        rest = m.group(2)
        return f"/mnt/{drive}/{rest}"
    return raw


# WSL UNC paths — both backslash and forward-slash forms
_WSL_UNC_RE = re.compile(
    r"^(?:\\\\|//)(?:wsl\.localhost|wsl\$)[/\\]([^/\\]+)[/\\]?(.*)",
    re.IGNORECASE,
)


def _normalize_picked_path(raw: str) -> str:
    """Convert Windows/tkinter file-picker path to WSL-internal path."""
    m = _WSL_UNC_RE.match(raw)
    if m:
        remainder = m.group(2).replace("\\", "/")
        return "/" + remainder if remainder else "/"
    return raw


def _wsl_wrap(cmd: list[str]) -> list[str]:
    """Wrap command for WSL execution on Windows."""
    if IS_WINDOWS:
        def _sq(s: str) -> str:
            return "'" + s.replace("'", "'\\''") + "'"
        if not cmd:
            return ["wsl.exe", "-d", WSL_DISTRO, "--", "true"]
        shell_cmd = cmd[0] + " " + " ".join(_sq(a) for a in cmd[1:]) if len(cmd) > 1 else cmd[0]
        return ["wsl.exe", "-d", WSL_DISTRO, "--", "bash", "-c", shell_cmd]
    return cmd


def _hidden_subprocess_kwargs() -> dict[str, object]:
    if not IS_WINDOWS:
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return {
        "creationflags": CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }


def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str]:
    try:
        run_kwargs: dict[str, object] = {
            "capture_output": True,
            "timeout": timeout,
        }
        if IS_WINDOWS:
            run_kwargs["encoding"] = "utf-8"
            run_kwargs["errors"] = "replace"
        else:
            run_kwargs["text"] = True
        run_kwargs.update(_hidden_subprocess_kwargs())
        r = subprocess.run(_wsl_wrap(cmd), **run_kwargs)
        stdout = r.stdout if isinstance(r.stdout, str) else ""
        stderr = r.stderr if isinstance(r.stderr, str) else ""
        output = stdout.strip()
        if not output and r.returncode != 0:
            output = stderr.strip()
        return r.returncode, output
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return -1, ""
