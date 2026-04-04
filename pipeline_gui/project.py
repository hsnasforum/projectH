"""Project path resolution, validation, bootstrap, session naming, and recent projects."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from .platform import (
    IS_WINDOWS, APP_ROOT, FILE_QUERY_TIMEOUT,
    _path_str, _wsl_path_str, _windows_native_path, _run,
)

_SAVED_PATH_FILE = Path.home() / ".pipeline-gui-last-project"
_MAX_RECENT = 5

BOOTSTRAP_PIPELINE_README = """# .pipeline

이 디렉터리는 pipeline launcher가 사용하는 런타임 제어 슬롯과 로그를 저장합니다.

- `claude_handoff.md`
- `gemini_request.md`
- `gemini_advice.md`
- `operator_request.md`
- `logs/`
- `state/`
- `locks/`
- `manifests/`
"""

_SESSION_PREFIX = "aip"


def _load_recent_projects() -> list[str]:
    """Load recent project paths (newest first, max _MAX_RECENT)."""
    try:
        lines = _SAVED_PATH_FILE.read_text(encoding="utf-8").splitlines()
        return [l.strip() for l in lines if l.strip()][:_MAX_RECENT]
    except OSError:
        return []


def _load_saved_project() -> str:
    recent = _load_recent_projects()
    return recent[0] if recent else ""


def _save_project_path(path_str: str) -> None:
    path_str = path_str.strip()
    if not path_str:
        return
    recent = _load_recent_projects()
    recent = [p for p in recent if p != path_str]
    recent.insert(0, path_str)
    recent = recent[:_MAX_RECENT]
    try:
        _SAVED_PATH_FILE.write_text("\n".join(recent) + "\n", encoding="utf-8")
    except OSError:
        pass


def resolve_project_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    env = os.environ.get("PROJECT_ROOT")
    if env:
        return Path(env)
    saved = _load_saved_project()
    if saved:
        return Path(saved)
    return Path.cwd().resolve()


def validate_project_root(project: Path) -> tuple[bool, str]:
    raw_path = _path_str(project)
    path_str = _wsl_path_str(project)

    if IS_WINDOWS and _windows_native_path(raw_path):
        return False, (
            f"Windows 경로가 project root로 설정되었습니다: {raw_path}\n\n"
            "WSL 내부 경로를 인자로 전달해야 합니다.\n"
            "예: pipeline-gui.exe /home/사용자/code/projectH\n"
            "또는 windows-launchers/pipeline-gui.cmd를 사용하세요."
        )
    if IS_WINDOWS and not path_str.startswith("/"):
        return False, (
            f"WSL 경로 형식이 아닙니다: {raw_path}\n\n"
            "예: pipeline-gui.exe /home/사용자/code/projectH"
        )
    if IS_WINDOWS:
        code, _ = _run(["test", "-d", path_str])
        if code != 0:
            return False, f"프로젝트 경로가 존재하지 않습니다: {path_str}"
        code, _ = _run(["test", "-f", f"{path_str}/AGENTS.md"])
        if code != 0:
            return False, f"프로젝트 경로에 AGENTS.md가 없습니다: {path_str}"
    else:
        if not project.exists() or not project.is_dir():
            return False, f"프로젝트 경로가 존재하지 않습니다: {path_str}"
        markers = ["AGENTS.md"]
        missing = [m for m in markers if not (project / m).exists()]
        if missing:
            return False, f"프로젝트 경로에 필수 파일이 없습니다: {', '.join(missing)}\n경로: {path_str}"
    return True, ""


def bootstrap_project_root(project: Path) -> tuple[bool, str]:
    path_str = _wsl_path_str(project)
    runtime_dirs = [
        f"{path_str}/.pipeline", f"{path_str}/.pipeline/logs",
        f"{path_str}/.pipeline/logs/baseline", f"{path_str}/.pipeline/logs/experimental",
        f"{path_str}/.pipeline/state", f"{path_str}/.pipeline/locks",
        f"{path_str}/.pipeline/manifests", f"{path_str}/work", f"{path_str}/verify",
    ]
    if IS_WINDOWS:
        code, _ = _run(["mkdir", "-p", *runtime_dirs], timeout=FILE_QUERY_TIMEOUT)
        if code != 0:
            return False, f"프로젝트 bootstrap 디렉터리 생성 실패: {path_str}"
        readme_path = f"{path_str}/.pipeline/README.md"
        code, _ = _run(["test", "-f", readme_path], timeout=FILE_QUERY_TIMEOUT)
        if code != 0:
            src = _wsl_path_str(APP_ROOT / ".pipeline" / "README.md")
            _run(["cp", src, readme_path], timeout=FILE_QUERY_TIMEOUT)
        return True, ""
    try:
        for d in runtime_dirs:
            Path(d).mkdir(parents=True, exist_ok=True)
        readme = project / ".pipeline" / "README.md"
        if not readme.exists():
            source = APP_ROOT / ".pipeline" / "README.md"
            if source.exists():
                readme.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                readme.write_text(BOOTSTRAP_PIPELINE_README, encoding="utf-8")
    except OSError:
        return False, f"프로젝트 bootstrap 디렉터리 생성 실패: {path_str}"
    return True, ""


def _session_name_for(project: Path) -> str:
    name = Path(_wsl_path_str(project) if IS_WINDOWS else str(project)).name or "default"
    safe = re.sub(r"[^A-Za-z0-9_-]", "", name)
    return f"{_SESSION_PREFIX}-{safe}" if safe else f"{_SESSION_PREFIX}-default"
