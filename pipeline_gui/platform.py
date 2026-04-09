"""Platform detection, WSL path conversion, and subprocess wrappers."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path, PurePosixPath

IS_WINDOWS = sys.platform == "win32"
WSL_DISTRO = os.environ.get("WSL_DISTRO", "Ubuntu")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[/\\]")
CREATE_NO_WINDOW = 0x08000000
TMUX_QUERY_TIMEOUT = 5.0 if IS_WINDOWS else 2.0
FILE_QUERY_TIMEOUT = 10.0 if IS_WINDOWS else 5.0
GUI_RUNTIME_SUBDIR = PurePosixPath(".pipeline") / "gui-runtime" / "_data"
_STAGED_RUNTIME_KEYS: set[str] = set()
_STAGED_RUNTIME_LOCK = threading.Lock()
_RUNTIME_STAGE_REQUIRED = (
    "start-pipeline.sh",
    "stop-pipeline.sh",
    "watcher_core.py",
    "token_collector.py",
    "token_schema.sql",
    "token_usage_shared.py",
    "token_dashboard_shared.py",
)

# PyInstaller onefile exe: runtime assets under sys._MEIPASS/_data/
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    APP_ROOT = Path(sys._MEIPASS) / "_data"
else:
    APP_ROOT = Path(__file__).resolve().parent.parent


def _normalize_token_runtime_asset_path(path: Path | str) -> Path:
    raw = _path_str(path).replace("\\", "/")
    prefix = ""
    body = raw
    if raw.startswith("//"):
        prefix = "//"
        body = raw[2:]
    elif raw.startswith("/"):
        prefix = "/"
        body = raw[1:]
    parts = [part for part in body.split("/") if part]
    collapsed: list[str] = []
    for part in parts:
        if part == "_data" and collapsed and collapsed[-1] == "_data":
            continue
        collapsed.append(part)
    normalized = prefix + "/".join(collapsed)
    return Path(normalized or raw)


def _packaged_file_candidates(name: str) -> list[Path]:
    module_dir = Path(__file__).resolve().parent
    candidates: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        meipass_root = Path(meipass)
        candidates.extend([
            meipass_root / "_data" / name,
            meipass_root / name,
        ])
    candidates.extend([
        module_dir / "_data" / name,
        module_dir / name,
        module_dir.parent / "_data" / name,
        module_dir.parent / name,
    ])
    seen: set[str] = set()
    ordered: list[Path] = []
    for path in candidates:
        path = _normalize_token_runtime_asset_path(path)
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(path)
    return ordered


def resolve_packaged_file(name: str) -> Path:
    candidates = _packaged_file_candidates(name)
    for path in candidates:
        if path.exists():
            return path
    tried = "\n".join(str(path) for path in candidates)
    raise FileNotFoundError(f"{name} not found. tried:\n{tried}")


def _wsl_to_windows_unc(path: Path | str) -> Path:
    raw = _wsl_path_str(path)
    if _windows_native_path(raw) or raw.startswith("\\\\"):
        return Path(raw)
    if not raw.startswith("/"):
        return Path(raw)
    parts = [part for part in raw.split("/") if part]
    unc = "\\\\wsl.localhost\\" + WSL_DISTRO
    if parts:
        unc += "\\" + "\\".join(parts)
    return Path(unc)


def _project_runtime_root(project: Path | str) -> PurePosixPath:
    return PurePosixPath(_wsl_path_str(project)) / GUI_RUNTIME_SUBDIR


def _staged_runtime_complete(runtime_root: Path) -> bool:
    return all((runtime_root / rel).exists() for rel in _RUNTIME_STAGE_REQUIRED)


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _files_match(source: Path, dest: Path) -> bool:
    source_sig = _file_sha256(source)
    if not source_sig:
        return False
    return source_sig == _file_sha256(dest)


def _staged_runtime_matches_packaged_assets(runtime_root: Path) -> bool:
    for name in _RUNTIME_STAGE_REQUIRED:
        staged = runtime_root / name
        if not staged.exists():
            return False
        try:
            source = resolve_packaged_file(name)
        except FileNotFoundError:
            return False
        if not _files_match(source, staged):
            return False
    return True


def ensure_staged_runtime_root(project: Path | str) -> Path:
    project_key = _wsl_path_str(project)
    runtime_root_wsl = _project_runtime_root(project)
    runtime_root_win = _wsl_to_windows_unc(str(runtime_root_wsl))

    with _STAGED_RUNTIME_LOCK:
        # Need to stage: copy from packaged bundle
        try:
            source_root = resolve_packaged_file("start-pipeline.sh").parent
        except FileNotFoundError:
            # If packaged files are missing, check if staged dir is partially usable
            if runtime_root_win.exists():
                _STAGED_RUNTIME_KEYS.add(project_key)
                return Path(str(runtime_root_wsl))
            raise

        if runtime_root_win.exists() and _staged_runtime_complete(runtime_root_win):
            if _staged_runtime_matches_packaged_assets(runtime_root_win):
                _STAGED_RUNTIME_KEYS.add(project_key)
                return Path(str(runtime_root_wsl))

        runtime_root_win.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_root, runtime_root_win, dirs_exist_ok=True)

        # Copy helper scripts that live outside the main _data/ tree
        for helper_name in ("token_usage_shared.py", "token_dashboard_shared.py"):
            try:
                helper_src = resolve_packaged_file(helper_name)
            except FileNotFoundError:
                pass  # Best-effort: may already be in staged dir from copytree
                continue
            helper_dst = runtime_root_win / helper_name
            if _files_match(helper_src, helper_dst):
                continue
            helper_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(helper_src, helper_dst)

        if not _staged_runtime_complete(runtime_root_win):
            missing = [name for name in _RUNTIME_STAGE_REQUIRED if not (runtime_root_win / name).exists()]
            raise FileNotFoundError(
                f"staged runtime incomplete at {runtime_root_wsl}: missing {', '.join(missing)}"
            )

        _STAGED_RUNTIME_KEYS.add(project_key)
        return Path(str(runtime_root_wsl))


def resolve_project_runtime_file(project: Path | str, name: str) -> Path:
    if IS_WINDOWS and getattr(sys, "frozen", False):
        return ensure_staged_runtime_root(project) / name
    return resolve_packaged_file(name)


def _token_runtime_asset_candidates(name: str, base_root: Path | None = None) -> list[Path]:
    """Candidate paths for token runtime assets across source and packaged layouts."""
    if base_root is None:
        return _packaged_file_candidates(name)
    root = _normalize_token_runtime_asset_path(base_root)
    source_tree_candidate = (root / "_data" / name) if root.name != "_data" else (root / name)
    candidates = [
        root / name,
        root.parent / name,
        source_tree_candidate,
    ]
    seen: set[str] = set()
    ordered: list[Path] = []
    for path in candidates:
        path = _normalize_token_runtime_asset_path(path)
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(path)
    return ordered


def _token_runtime_asset_path(name: str, base_root: Path | None = None) -> Path:
    if base_root is None:
        return resolve_packaged_file(name)
    candidates = _token_runtime_asset_candidates(name, base_root)
    if IS_WINDOWS:
        for path in candidates:
            mounted = _windows_to_wsl_mount(path)
            code, _ = _run(["test", "-e", mounted], timeout=3.0)
            if code == 0:
                return path
    else:
        for path in candidates:
            if path.exists():
                return path
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


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
    """Wrap command for WSL execution on Windows.

    For 'bash -c/-lc <string>' patterns, the shell string is kept as
    a single argument to bash. For simple commands, each argument is
    individually single-quoted to protect shell metacharacters from
    Windows command-line and bash interpretation.
    """
    if not IS_WINDOWS:
        return cmd
    if not cmd:
        return ["wsl.exe", "-d", WSL_DISTRO, "--", "true"]

    def _sq(s: str) -> str:
        """single-quote escape: abc → 'abc', it's → 'it'\\''s'"""
        return "'" + s.replace("'", "'\\''") + "'"

    # bash -c/-lc <shell_string>: pass shell string directly (already a shell command)
    if len(cmd) >= 3 and cmd[0] == "bash" and cmd[1] in ("-c", "-lc"):
        flags = cmd[1]
        shell_string = cmd[2]
        return ["wsl.exe", "-d", WSL_DISTRO, "--", "bash", flags, shell_string]

    # Simple commands: wrap in bash -c with single-quoted args
    shell_cmd = cmd[0] + (" " + " ".join(_sq(a) for a in cmd[1:]) if len(cmd) > 1 else "")
    return ["wsl.exe", "-d", WSL_DISTRO, "--", "bash", "-c", shell_cmd]


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
