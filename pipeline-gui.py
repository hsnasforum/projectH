#!/usr/bin/env python3
"""
pipeline-gui.py — 내부용 desktop GUI launcher (tkinter)

사용법:
  python3 pipeline-gui.py [project_path]
  python3 pipeline-gui.py .

project path 결정 순서:
  1. 명령줄 인자
  2. PROJECT_ROOT 환경변수
  3. ~/.pipeline-gui-last-project (마지막 성공 경로)
  4. 현재 디렉터리

GUI 내부에서 Browse… → Apply로 경로를 변경/저장할 수 있습니다.
target repo에 `.pipeline/`, `work/`, `verify/`가 없으면 launcher가 최소 런타임
디렉터리를 자동 bootstrap합니다.

exe 패키징 (Windows native):
  pip install pyinstaller
  pyinstaller --onefile --noconsole --name pipeline-gui pipeline-gui.py
  → scripts/PACKAGING.md 참고
"""

from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import sys
import time
import threading
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Text, Entry,
    StringVar, LEFT, RIGHT, TOP, BOTTOM, BOTH, X, Y, END, WORD, DISABLED, NORMAL,
    font as tkfont,
    filedialog,
    messagebox,
)
from tkinter.ttk import Scrollbar as TtkScrollbar, Style as TtkStyle

# ── 프로젝트 경로 ─────────────────────────────────────────────

_SAVED_PATH_FILE = Path.home() / ".pipeline-gui-last-project"

_DEFAULT_GUIDE = """\
# Pipeline Agent Orchestration Guide

## 이 문서의 목적

이 문서는 이 파이프라인에서 Claude, Codex, Gemini가 어떤 순서와 조건으로 호출되는지 설명합니다.
핵심은 "누가 언제 일하고, 어떤 파일을 읽고, 어떤 파일을 써야 하는지"를 분명히 하는 것입니다.

## 기본 실행 순서

Claude -> Codex -> (필요 시 Gemini -> Codex) -> Claude

1. Claude가 구현을 수행합니다.
2. Codex가 최신 구현 결과를 검증합니다.
3. Codex가 다음 작업을 명확히 정할 수 있으면 다시 Claude에게 넘깁니다.
4. Codex가 혼자 결정하기 어렵다면 Gemini에게 자문을 요청합니다.
5. Gemini가 advisory를 남기면 Codex가 다시 들어와 최종 결론을 내립니다.

Gemini는 항상 호출되는 기본 단계가 아닙니다.
Codex가 tie-break가 필요하다고 판단할 때만 호출됩니다.

## 시작 시 첫 에이전트 결정

파이프라인이 시작/재시작될 때 watcher는 아래 우선순위로 첫 agent를 결정합니다.

1. operator_request가 최신 pending이면 -> operator 대기
2. gemini_request가 최신 pending이면 -> Gemini
3. gemini_advice가 최신 pending이면 -> Codex follow-up
4. 최신 /work가 same-day /verify보다 새로우면 -> Codex
5. claude_handoff가 STATUS: implement이면 -> Claude
6. 모든 파일이 비어 있으면 -> Claude (초기 상태)
7. 그 외 -> Codex

implement handoff가 있어도 최신 /work가 아직 검증되지 않았다면 Codex가 먼저 들어갑니다.

## 에이전트별 역할과 호출 조건

### Claude (구현)

호출 조건:
- .pipeline/claude_handoff.md의 STATUS가 implement
- operator stop 상태가 아님
- 최신 /work가 /verify 없이 남아 있지 않음

역할:
- 지정된 정확한 슬라이스 구현
- 구현 closeout을 /work/...에 기록

쓰면 안 되는 파일:
- .pipeline/gemini_request.md
- .pipeline/gemini_advice.md
- .pipeline/operator_request.md

### Codex (검증)

호출 조건:
- Claude 구현 다음 (기본)
- 최신 /work가 /verify 없이 남아 있을 때
- Gemini advice 이후 follow-up이 필요할 때

역할:
- 최신 /work를 먼저 읽고, same-day /verify도 함께 읽음
- 검증 rerun 후 /verify/...를 남기거나 갱신
- 다음 Claude 슬라이스를 하나 정함
- 애매하면 Gemini 자문 요청
- 자동 진행 불가능하면 operator stop 선언

결정 출력 (셋 중 하나):
- .pipeline/claude_handoff.md
- .pipeline/gemini_request.md
- .pipeline/operator_request.md

### Gemini (조언)

호출 조건:
- .pipeline/gemini_request.md의 STATUS가 request_open이고
- operator stop 상태가 아닐 때

역할:
- tie-break용 분석과 자문 제공

쓸 수 있는 출력:
- .pipeline/gemini_advice.md
- report/gemini/...md

쓰면 안 되는 파일:
- .pipeline/claude_handoff.md
- .pipeline/operator_request.md

## Gemini advice 이후 흐름

Gemini가 .pipeline/gemini_advice.md를 STATUS: advice_ready로 갱신하면 watcher가 Codex follow-up을 재호출합니다.

Codex -> gemini_request.md -> Gemini -> gemini_advice.md -> watcher -> Codex follow-up

## control file 우선순위

- .pipeline/claude_handoff.md -> Claude 실행
- .pipeline/gemini_request.md -> Gemini 실행
- .pipeline/gemini_advice.md -> Codex follow-up
- .pipeline/operator_request.md -> 자동 진행 중단

.pipeline 내용과 /work, /verify가 충돌하면 /work와 /verify를 우선합니다.

## 파일 의미

### /work
Claude 구현 closeout의 persistent 기록.
무엇을 바꿨는지, 왜, 어떤 검증을 했는지, 남은 리스크.

### /verify
Codex 검증 기록.
/work 내용이 실제 코드와 맞는지, 검증 rerun 결과, 다음 슬라이스 선택 근거.

### report/gemini
Gemini advisory/mediation 로그.

### .pipeline 슬롯
rolling handoff 슬롯. persistent truth는 /work와 /verify에 있습니다.

주요 슬롯:
- claude_handoff.md, gemini_request.md, gemini_advice.md, operator_request.md

Legacy/optional:
- codex_feedback.md, gpt_prompt.md (현재 canonical path에서 사용 안 함)

## 슬라이스 선택 원칙

Codex 기본 우선순위:
1. 같은 계열 현재 리스크 감소
2. 같은 계열 사용자-visible 개선
3. 새로운 품질 축
4. 내부 cleanup

정말 애매할 때만 Gemini를 부르고, 그래도 위험하면 operator stop.

## 자동 중단 조건

.pipeline/operator_request.md는 반드시 STATUS: needs_operator를 포함해야 합니다.
이 STATUS가 없으면 watcher는 operator stop으로 인식하지 않습니다.

파일에는 최소한:
- 왜 멈추는지
- 어떤 /work, /verify 기준으로 멈췄는지
- operator가 무엇을 결정해야 하는지

## 운영 원칙

- Claude는 구현, Codex는 검증+다음 결정, Gemini는 advisory only.
- persistent truth는 /work와 /verify.
- .pipeline은 실행 슬롯이지 영구 기록이 아닙니다.
- 최신 /work가 미검증이면 implement handoff가 있어도 Codex가 먼저.
- 애매한 상태를 숨기지 말고 정직하게 기록합니다.
"""
_MAX_RECENT = 5

# PyInstaller onefile exe: 런타임 자산은 sys._MEIPASS 아래 _data/ 에 풀림
# source 실행: __file__의 부모 디렉터리 (repo root)
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    APP_ROOT = Path(sys._MEIPASS) / "_data"
else:
    APP_ROOT = Path(__file__).resolve().parent
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


def _load_recent_projects() -> list[str]:
    """Load recent project paths (newest first, max _MAX_RECENT)."""
    try:
        lines = _SAVED_PATH_FILE.read_text(encoding="utf-8").splitlines()
        return [l.strip() for l in lines if l.strip()][:_MAX_RECENT]
    except OSError:
        return []


def _load_saved_project() -> str:
    """Load the most recently used project path."""
    recent = _load_recent_projects()
    return recent[0] if recent else ""


def _save_project_path(path_str: str) -> None:
    """Prepend path to recent list, deduplicate, limit to _MAX_RECENT."""
    path_str = path_str.strip()
    if not path_str:
        return
    recent = _load_recent_projects()
    # Remove duplicates of this path, then prepend
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
    """프로젝트 경로가 유효한 agent repo 후보인지 확인합니다.

    Returns: (valid, reason)
    """
    raw_path = _path_str(project)
    path_str = _wsl_path_str(project)

    # Windows 경로가 WSL project path로 착각되지 않게
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

    # WSL 경로라도 실제 agent repo 후보인지 확인
    if IS_WINDOWS:
        code, _ = _run(["test", "-d", path_str])
        if code != 0:
            return False, f"프로젝트 경로가 존재하지 않습니다: {path_str}"
        # 현재 pipeline은 repo별 지침 파일을 전제로 한다.
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
    """pipeline 런타임에 필요한 최소 디렉터리를 생성합니다."""
    path_str = _wsl_path_str(project)
    runtime_dirs = [
        f"{path_str}/.pipeline",
        f"{path_str}/.pipeline/logs",
        f"{path_str}/.pipeline/logs/baseline",
        f"{path_str}/.pipeline/logs/experimental",
        f"{path_str}/.pipeline/state",
        f"{path_str}/.pipeline/locks",
        f"{path_str}/.pipeline/manifests",
        f"{path_str}/work",
        f"{path_str}/verify",
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
        for directory in runtime_dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
        pipeline_readme = project / ".pipeline" / "README.md"
        if not pipeline_readme.exists():
            source = APP_ROOT / ".pipeline" / "README.md"
            if source.exists():
                pipeline_readme.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                pipeline_readme.write_text(BOOTSTRAP_PIPELINE_README, encoding="utf-8")
    except OSError:
        return False, f"프로젝트 bootstrap 디렉터리 생성 실패: {path_str}"
    return True, ""


_SESSION_PREFIX = "aip"


def _session_name_for(project: Path) -> str:
    """Project path에서 deterministic한 tmux session 이름을 생성합니다.

    /home/user/code/projectH → aip-projectH
    /home/user/code/finance  → aip-finance
    """
    name = Path(_wsl_path_str(project) if IS_WINDOWS else str(project)).name or "default"
    # tmux session 이름에 허용되지 않는 문자 제거
    safe = re.sub(r"[^A-Za-z0-9_-]", "", name)
    return f"{_SESSION_PREFIX}-{safe}" if safe else f"{_SESSION_PREFIX}-default"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
BOX_DRAWING_ONLY_RE = re.compile(r"^[\s\-_=~│┃┆┊┌┐└┘├┤┬┴┼╭╮╯╰•·●○■□▶◀▸▹▾▿▴▵>*]+$")
FOCUS_ENTRY_START_RE = re.compile(
    r"^(?:"
    r"[•●◦○▪*-]\s+|"
    r"bash\(|read\b|search(?:ing|ed)?\b|ran\b|updated plan\b|working\b|"
    r"cascading\b|lollygagging\b|hashing\b|thinking\b|goal:|목표:|변경|검증|결과:|"
    r"wait(?:ed|ing)\b|without interrupting\b|role:|state:|handoff:|read_first:|"
    r"claude code\b|openai codex\b|gemini cli\b"
    r")",
    re.IGNORECASE,
)
POLL_MS = 1000
IS_WINDOWS = sys.platform == "win32"
WSL_DISTRO = os.environ.get("WSL_DISTRO", "Ubuntu")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[/\\]")
CREATE_NO_WINDOW = 0x08000000
TMUX_QUERY_TIMEOUT = 5.0 if IS_WINDOWS else 2.0
FILE_QUERY_TIMEOUT = 10.0 if IS_WINDOWS else 5.0


def _path_str(path: Path | str) -> str:
    return str(path)


def _windows_native_path(path: Path | str) -> bool:
    raw = _path_str(path)
    return raw.startswith("\\\\") or bool(WINDOWS_DRIVE_RE.match(raw))


def _wsl_path_str(path: Path | str) -> str:
    """WSL 내부 경로(/home/...) 표시용. Windows native path는 변환 안 함."""
    raw = _path_str(path)
    if not IS_WINDOWS:
        return raw
    if _windows_native_path(raw):
        return raw
    return raw.replace("\\", "/")


def _windows_to_wsl_mount(path: Path | str) -> str:
    """Windows native path → WSL /mnt/... 경로로 변환.

    C:\\Users\\foo\\bar → /mnt/c/Users/foo/bar
    /home/user/proj    → /home/user/proj  (passthrough)

    PyInstaller frozen exe에서 번들 자산 경로를 WSL bash에 넘길 때 사용.
    """
    raw = _path_str(path).replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/(.*)$", raw)
    if m:
        drive = m.group(1).lower()
        rest = m.group(2)
        return f"/mnt/{drive}/{rest}"
    return raw


# WSL UNC paths — both backslash and forward-slash forms:
#   \\wsl.localhost\Ubuntu\home\...   (standard Windows UNC)
#   //wsl.localhost/Ubuntu/home/...   (tkinter filedialog on some platforms)
#   \\wsl$\Ubuntu\home\...            (older WSL UNC)
#   //wsl$/Ubuntu/home/...
_WSL_UNC_RE = re.compile(
    r"^(?:\\\\|//)(?:wsl\.localhost|wsl\$)[/\\]([^/\\]+)[/\\]?(.*)",
    re.IGNORECASE,
)


def _normalize_picked_path(raw: str) -> str:
    """Convert a Windows/tkinter file-picker path to a WSL-internal path.

    \\\\wsl.localhost\\Ubuntu\\home\\user\\proj → /home/user/proj
    //wsl.localhost/Ubuntu/home/user/proj       → /home/user/proj
    \\\\wsl$\\Ubuntu\\home\\user\\proj         → /home/user/proj
    //wsl$/Ubuntu/home/user/proj               → /home/user/proj
    /home/user/proj                             → /home/user/proj  (passthrough)
    C:\\Users\\...                              → C:\\Users\\...   (unchanged, will fail validation)
    """
    m = _WSL_UNC_RE.match(raw)
    if m:
        remainder = m.group(2).replace("\\", "/")
        return "/" + remainder if remainder else "/"
    return raw


# ── Platform-aware command execution ──────────────────────────

def _wsl_wrap(cmd: list[str]) -> list[str]:
    """Windows에서는 wsl.exe로 감싸서 WSL 내부 명령을 실행합니다.

    wsl.exe -- cmd 형태는 내부적으로 bash로 실행되므로
    #{}, %, \\t 등 특수 문자가 bash에서 해석됩니다.
    이를 방지하기 위해 bash -c '...'로 감싸서 single-quote 인용합니다.
    """
    if IS_WINDOWS:
        # wsl.exe -- 형태는 인자를 bash에 그대로 넘기므로
        # #{}, %, *, \t 등이 bash에서 해석됨.
        # 각 인자를 single-quote로 개별 감싸서 bash 해석을 방지.
        def _sq(s: str) -> str:
            """single-quote escape: abc → 'abc', it's → 'it'\''s'"""
            return "'" + s.replace("'", "'\\''") + "'"
        # 첫 인자(명령)는 quote 불필요, 나머지는 quote
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
            # WSL output is always UTF-8; Windows locale (cp949/cp1252) mismatches.
            # Explicit utf-8 prevents garbled text or UnicodeDecodeError on Korean pane content.
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


def tmux_alive(session: str = "") -> bool:
    code, _ = _run(["tmux", "has-session", "-t", session or "ai-pipeline"])
    return code == 0


def watcher_alive(project: Path) -> tuple[bool, int | None]:
    pid_path = project / ".pipeline" / "experimental.pid"
    if IS_WINDOWS:
        # Windows에서는 WSL 파일시스템을 직접 읽을 수 없으므로 wsl cat으로 읽기
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


def _wsl_read_file(path: str) -> str:
    """Windows에서 WSL 내부 파일을 읽습니다."""
    code, content = _run(["cat", _wsl_path_str(path)])
    return content if code == 0 else ""


def _wsl_file_exists(path: str) -> bool:
    """Windows에서 WSL 내부 파일 존재 여부를 확인합니다."""
    code, _ = _run(["test", "-e", _wsl_path_str(path)])
    return code == 0


def latest_md(directory: Path) -> tuple[str, float]:
    if IS_WINDOWS:
        # WSL find로 최신 .md 파일 찾기
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


WATCHER_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")
_JOB_ID_RE = re.compile(r"new job:\s*(\S+)")
_STATE_TRANS_RE = re.compile(r"state\s+\S+\s+(\S+)\s*→\s*(\S+)")


def _extract_run_summary(log_lines: list[str]) -> dict[str, str]:
    """watcher log에서 current run summary를 추출합니다.

    Returns: {"job": str, "phase": str, "turn": str, "ts": str}
    """
    job = ""
    phase = ""
    turn = ""
    ts = ""

    for line in log_lines:
        # job
        m = _JOB_ID_RE.search(line)
        if m:
            job = m.group(1)
            ts_m = WATCHER_TS_RE.match(line)
            if ts_m:
                ts = ts_m.group(1)[-8:]  # HH:MM:SS

        # phase transition
        m = _STATE_TRANS_RE.search(line)
        if m:
            phase = m.group(2)  # 최신 도착 상태

        # turn
        if "notify_claude" in line or "Claude 차례" in line:
            turn = "Claude"
        elif "lease acquired" in line or "dispatching codex" in line:
            turn = "Codex"
        elif "notify_gemini" in line or "Gemini 차례" in line:
            turn = "Gemini"
        elif "initial turn:" in line:
            t = line.split("initial turn:", 1)[1].strip()
            turn = t.capitalize() if t else turn
        elif "codex_followup" in line:
            turn = "Codex (follow-up)"

    return {"job": job, "phase": phase, "turn": turn, "ts": ts}


def format_elapsed(seconds: float) -> str:
    total = max(0, int(seconds))
    mins, secs = divmod(total, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


_ELAPSED_RE = re.compile(r"(\d+)\s*(h|m|s)")


def _parse_elapsed(note: str) -> float:
    """'3m 22s' / '36s' / '1h 5m' → seconds.  Returns 0 if unparseable."""
    total = 0.0
    for m in _ELAPSED_RE.finditer(note):
        val = int(m.group(1))
        unit = m.group(2)
        if unit == "h":
            total += val * 3600
        elif unit == "m":
            total += val * 60
        else:
            total += val
    return total


def extract_working_note(lines: list[str]) -> str:
    """pane 출력에서 Working 경과시간/상태 노트 추출."""
    for line in reversed(lines[-80:]):
        match = re.search(r"Working \(([^)]*)", line, re.IGNORECASE)
        if match:
            note = match.group(1).split("•", 1)[0].strip(" )…")
            if note:
                return note
        match = re.search(r"Cascading(?:…|\.{3})\s*\(([^)]*)", line, re.IGNORECASE)
        if match:
            return match.group(1).strip(" )…")
        match = re.search(r"Lollygagging(?:…|\.{3})\s*\(([^)]*)", line, re.IGNORECASE)
        if match:
            return match.group(1).strip(" )…")
        lowered = line.lower()
        if "background terminal" in lowered or "waiting for background" in lowered:
            return "bg-task"
    return ""


def extract_quota_note(pane_text: str) -> str:
    text = " ".join(line.strip() for line in pane_text.splitlines() if line.strip())

    match = re.search(r"(\d+%)\s+lef", text, re.IGNORECASE)
    if match:
        return f"{match.group(1)} left"

    match = re.search(r"you['’]ve used\s+(\d+%)", text, re.IGNORECASE)
    if match:
        return f"used {match.group(1)}"

    match = re.search(r"new 2x rate limits until ([^.]+)", text, re.IGNORECASE)
    if match:
        return f"2x until {match.group(1).strip()}"

    return ""


def detect_agent_status(label: str, pane_text: str) -> tuple[str, str]:
    """(status, note) — launcher 수준 판정."""
    lines = [l.strip() for l in pane_text.splitlines() if l.strip()]
    if not lines:
        return "DEAD", ""

    lower = pane_text.lower()

    # Working indicators — launcher와 동일한 10+ 패턴
    if (
        "working (" in lower
        or "background terminal" in lower
        or "waiting for background" in lower
        or "waited for background" in lower
        or "cascading" in lower
        or "lollygagging" in lower
        or "hashing" in lower
        or "leavering" in lower
        or "without interrupting claude's current work" in lower
        or "flumoxing" in lower
        or "philosophising" in lower
        or "sautéed" in lower
    ):
        note = extract_working_note(lines)
        return "WORKING", note

    # Gemini-specific working: "Thinking..." spinner with "esc to cancel" in recent output
    # (checked before READY because Gemini keeps the prompt bar during thinking;
    #  only recent lines to avoid matching old scrollback after work completes)
    if label == "Gemini":
        recent_lower = "\n".join(lines[-15:]).lower()
        if "esc to cancel" in recent_lower:
            return "WORKING", ""

    # Ready indicators
    if label == "Codex" and ("› " in pane_text or "openai codex" in lower):
        return "READY", ""
    if label == "Claude" and ("❯" in pane_text or "claude code" in lower or "bypass permissions" in lower):
        return "READY", ""
    if label == "Gemini" and ("type your message" in lower or "gemini cli" in lower or "workspace" in lower):
        return "READY", ""

    return "BOOTING", ""


def capture_agent_panes(project: Path, history_lines: int = 180, session: str = "") -> dict[str, str]:
    """agent label -> cleaned pane text."""
    sess = session or _session_name_for(project)
    code, output = _run(
        ["tmux", "list-panes", "-t", f"{sess}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
        timeout=TMUX_QUERY_TIMEOUT,
    )
    names = {0: "Claude", 1: "Codex", 2: "Gemini"}
    results: dict[str, str] = {}
    if code != 0 or not output:
        return results

    for raw in output.splitlines():
        try:
            idx_s, pane_id, dead = raw.split("|", 2)
            idx = int(idx_s)
        except ValueError:
            continue
        label = names.get(idx, f"Pane {idx}")
        if dead == "1":
            results[label] = ""
            continue
        cap_code, captured = _run(
            ["tmux", "capture-pane", "-J", "-p", "-t", pane_id, "-S", f"-{history_lines}"],
            timeout=TMUX_QUERY_TIMEOUT,
        )
        if cap_code != 0 or not captured:
            results[label] = ""
            continue
        cleaned = ANSI_RE.sub("", captured)
        results[label] = rejoin_wrapped_pane_lines(cleaned)
    return results


def _is_interesting_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if BOX_DRAWING_ONLY_RE.match(stripped):
        return False
    lowered = stripped.lower()
    if (
        "bypass" in lowered
        or "sandbox disabled" in lowered
        or "claude code has switc" in lowered
        or lowered in {"/effort", "high · /effort", "high /effort"}
        or lowered.startswith("workspace /")
        or lowered.startswith("type your message")
        or lowered == "workspace"
        or lowered.endswith("skills")
    ):
        return False
    return True


def rejoin_wrapped_pane_lines(text: str) -> str:
    """좁은 tmux pane에서 mid-sentence로 하드 래핑된 줄을 최대한 다시 붙입니다.

    controller/server.py의 wide-display 보정과 같은 계열 로직입니다.
    """
    if not text:
        return text

    result_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.rstrip()
        if not result_lines:
            result_lines.append(stripped)
            continue

        prev = result_lines[-1]
        is_natural_break = (
            not prev
            or prev.endswith((".", "!", "?", ":", ")", "]", "}", "─", "│", "┘", "┐", "┤", "┴"))
            or stripped.startswith(("•", "─", "│", "┌", "└", "├", "›", ">", "$", "#", "-", "*", "✓", "✗"))
            or stripped.startswith(("  •", "  -", "  *", "  ✓"))
            or not stripped
        )
        if is_natural_break:
            result_lines.append(stripped)
        else:
            result_lines[-1] = prev + " " + stripped.lstrip()

    return "\n".join(result_lines)


def _normalize_focus_line(line: str) -> str:
    line = line.rstrip()
    line = re.sub(r"\s+", " ", line.strip())
    return line


def _focus_line_starts_new_entry(line: str) -> bool:
    return bool(FOCUS_ENTRY_START_RE.match(line))


def format_focus_output(pane_text: str, max_lines: int = 40, max_chars: int = 300) -> str:
    """선택 agent pane을 최근 문맥 중심으로 보여준다."""
    if not pane_text.strip():
        return "(출력 없음)"

    lines = [line.rstrip() for line in pane_text.splitlines()]
    # 최소 필터만 — 완전 빈 줄과 box drawing만 제거, 나머지는 보존
    filtered = [line for line in lines if line.strip() and not BOX_DRAWING_ONLY_RE.match(line.strip())]
    if not filtered:
        return "(표시할 출력 없음)"

    interesting_markers = (
        "working", "cascading", "lollygagging", "hashing", "leavering",
        "read", "search", "searched", "bash(", "ran ", "updated plan",
        "goal:", "목표:", "변경", "검증", "thinking", "without interrupting",
        "background", "role:", "handoff:", "state:", "explored", "waiting",
        "write", "edit", "create", "error", "fail", "success", "complete",
    )

    anchor = max(0, len(filtered) - max_lines)
    for idx in range(len(filtered) - 1, -1, -1):
        lowered = filtered[idx].lower()
        if any(marker in lowered for marker in interesting_markers):
            anchor = max(0, idx - (max_lines - 8))
            break

    tail = filtered[anchor:]

    rendered: list[str] = []
    previous_blank = False
    for raw in tail:
        line = _normalize_focus_line(raw)
        if not line:
            if not previous_blank:
                rendered.append("")
            previous_blank = True
            continue
        previous_blank = False

        if len(line) > max_chars:
            rendered.append(line[: max_chars - 3] + "...")
        else:
            rendered.append(line)

    rendered = rendered[-max_lines:]
    if not rendered:
        return "(표시할 출력 없음)"
    return "\n".join(rendered)


def watcher_runtime_hints(project: Path) -> dict[str, tuple[str, str]]:
    """watcher.log에서 agent별 WORKING/READY 힌트와 경과시간 추출."""
    log_path = project / ".pipeline" / "logs" / "experimental" / "watcher.log"
    if IS_WINDOWS:
        code, content = _run(["tail", "-n", "300", _wsl_path_str(log_path)], timeout=FILE_QUERY_TIMEOUT)
        if code != 0:
            content = ""
        if not content:
            return {}
        lines = content.splitlines()[-300:]
    else:
        if not log_path.exists():
            return {}
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-300:]
        except OSError:
            return {}

    claude_started_at: float | None = None
    claude_done = False
    codex_started_at: float | None = None
    codex_done = False
    gemini_started_at: float | None = None
    gemini_done = False

    for line in lines:
        ts_match = WATCHER_TS_RE.match(line)
        if not ts_match:
            continue
        try:
            timestamp = dt.datetime.fromisoformat(ts_match.group(1)).timestamp()
        except ValueError:
            continue

        if "notify_claude" in line or ("send-keys" in line and "pane_type=claude" in line) or "waiting_for_claude" in line:
            claude_started_at = timestamp
            claude_done = False
        elif "claude activity detected" in line or ("new job:" in line and claude_started_at is not None):
            claude_done = True

        if "lease acquired: slot=slot_verify" in line or "VERIFY_PENDING → VERIFY_RUNNING" in line:
            codex_started_at = timestamp
            codex_done = False
        elif "codex task completed" in line or "lease released: slot=slot_verify" in line or "VERIFY_RUNNING → VERIFY_DONE" in line:
            codex_done = True

        if "notify_gemini" in line or "gemini response activity" in line:
            gemini_started_at = timestamp
            gemini_done = False
        elif "gemini advice updated" in line:
            gemini_done = True

    hints: dict[str, tuple[str, str]] = {}
    now = time.time()
    if claude_started_at is not None and not claude_done:
        hints["Claude"] = ("WORKING", format_elapsed(now - claude_started_at))
    elif claude_done:
        hints["Claude"] = ("READY", "")
    if codex_started_at is not None and not codex_done:
        hints["Codex"] = ("WORKING", format_elapsed(now - codex_started_at))
    elif codex_done:
        hints["Codex"] = ("READY", "")
    if gemini_started_at is not None and not gemini_done:
        hints["Gemini"] = ("WORKING", format_elapsed(now - gemini_started_at))
    elif gemini_done:
        hints["Gemini"] = ("READY", "")
    return hints


def agent_snapshots(project: Path, session: str = "") -> list[tuple[str, str, str, str]]:
    """[(label, status, note, quota), ...] — launcher 수준 truth."""
    sess = session or _session_name_for(project)
    code, output = _run(
        ["tmux", "list-panes", "-t", f"{sess}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
        timeout=TMUX_QUERY_TIMEOUT,
    )
    if code != 0 or not output:
        return [("Claude", "OFF", "", ""), ("Codex", "OFF", "", ""), ("Gemini", "OFF", "", "")]

    names = {0: "Claude", 1: "Codex", 2: "Gemini"}
    hints = watcher_runtime_hints(project)
    results: list[tuple[str, str, str, str]] = []

    for raw in output.splitlines():
        try:
            idx_s, pane_id, dead = raw.split("|", 2)
            idx = int(idx_s)
        except ValueError:
            continue
        label = names.get(idx, f"Pane {idx}")
        if dead == "1":
            results.append((label, "DEAD", "", ""))
            continue
        cap_code, captured = _run(["tmux", "capture-pane", "-p", "-t", pane_id, "-S", "-60"], timeout=TMUX_QUERY_TIMEOUT)
        if cap_code != 0 or not captured:
            results.append((label, "BOOTING", "", ""))
            continue
        cleaned = ANSI_RE.sub("", captured)
        status, note = detect_agent_status(label, cleaned)
        quota = extract_quota_note(cleaned)

        # watcher 힌트로 보정 (launcher와 동일 로직)
        hint = hints.get(label)
        if hint:
            hint_status, hint_note = hint
            if hint_status == "WORKING":
                status = "WORKING"
                if not note:
                    note = hint_note
            elif hint_status == "READY" and status == "BOOTING":
                status = "READY"
                note = ""

        results.append((label, status, note, quota))
    return results


# ── 파이프라인 전제 확인 ────────────────────────────────────────

# ── Setup preflight ────────────────────────────────────────────
# Hard blockers: 없으면 Start 불가
# (label, check_type, target, install_hint)
#   check_type: "cli" = _find_cli_bin, "launcher_file" = APP_ROOT 기준, "repo_file" = project 기준
_HARD_BLOCKERS: list[tuple[str, str, str, str]] = [
    ("tmux",               "cli",  "tmux",                "sudo apt install tmux"),
    ("python3",            "cli",  "python3",             "sudo apt install python3"),
    ("claude",             "cli",  "claude",              "npm install -g @anthropic-ai/claude-code"),
    ("codex",              "cli",  "codex",               "npm install -g codex"),
    ("gemini",             "cli",  "gemini",              "npm install -g @google/gemini-cli"),
    ("start-pipeline.sh",  "launcher_file", "start-pipeline.sh",  ""),
    ("stop-pipeline.sh",   "launcher_file", "stop-pipeline.sh",   ""),
    ("watcher_core.py",    "launcher_file", "watcher_core.py",    ""),
    ("AGENTS.md",          "repo_file",     "AGENTS.md",          ""),
]

# Soft warnings: 없어도 Start 가능하지만 품질/관찰성에 영향
_SOFT_WARNINGS: list[tuple[str, str, str]] = [
    ("agent_manifest.schema.json", "launcher_file", "schemas/agent_manifest.schema.json"),
    ("job_state.schema.json",      "launcher_file", "schemas/job_state.schema.json"),
]

# start-pipeline.sh의 _find_cli_bin()과 동일한 3단계 탐색
_FIND_CLI_SH = r"""
_find() {
  command -v "$1" 2>/dev/null && return
  [ -s "$HOME/.nvm/nvm.sh" ] && . "$HOME/.nvm/nvm.sh" 2>/dev/null && command -v "$1" 2>/dev/null && return
  for d in "$HOME/.nvm/versions/node"/*/bin "$HOME/.local/bin" /usr/local/bin; do
    [ -x "$d/$1" ] && echo "$d/$1" && return
  done
  return 1
}
"""


def _find_cli_bin(name: str) -> bool:
    """start-pipeline.sh의 _find_cli_bin과 동일한 3단계 탐색으로 CLI 존재 여부 확인."""
    script = _FIND_CLI_SH + f'_find "{name}"'
    code, _ = _run(["bash", "-c", script], timeout=8.0)
    return code == 0


def _file_exists(base: Path, rel: str) -> bool:
    """파일 존재 확인.

    base가 APP_ROOT(exe 번들 또는 로컬 repo)이면 로컬 filesystem 체크.
    base가 target project(WSL 경로)이면 Windows에서는 wsl test 사용.
    """
    local = base / rel
    if local.exists():
        return True
    # Windows에서 WSL 경로를 대상으로 하는 경우 wsl test fallback
    if IS_WINDOWS:
        full = f"{_wsl_path_str(base)}/{rel}"
        code, _ = _run(["test", "-e", full], timeout=5.0)
        return code == 0
    return False


def _check_hard_blockers(project: Path) -> list[tuple[str, str]]:
    """Return list of (label, install_hint) for missing hard blockers."""
    missing: list[tuple[str, str]] = []
    for label, check_type, target, hint in _HARD_BLOCKERS:
        if check_type == "cli":
            ok = _find_cli_bin(target)
        elif check_type == "launcher_file":
            ok = _file_exists(APP_ROOT, target)
        elif check_type == "repo_file":
            ok = _file_exists(project, target)
        else:
            ok = True
        if not ok:
            missing.append((label, hint))
    return missing


def _check_soft_warnings(project: Path) -> list[str]:
    """Return list of labels for soft warning items."""
    warnings: list[str] = []
    for label, check_type, target in _SOFT_WARNINGS:
        if check_type == "launcher_file":
            ok = _file_exists(APP_ROOT, target)
        elif check_type == "repo_file":
            ok = _file_exists(project, target)
        else:
            ok = True
        if not ok:
            warnings.append(label)
    return warnings


# Guide files that can be generated for target repos on approval
_TMPL_AGENTS = """\
# Agents

## Default Rules

- Prefer read operations over write operations.
- Read existing code before suggesting modifications.
- Keep changes small and focused — one concern per commit.
- Do not add features, refactor, or "improve" beyond what was asked.
- Do not overwrite files without explicit approval.
- Report verification results honestly — never claim success without evidence.
- Avoid destructive commands (rm -rf, force push, drop table) unless explicitly requested.

## Roles

| Role | Agent | Responsibility |
|------|-------|---------------|
| Implementer | Claude | Code changes, bug fixes, feature work |
| Verifier | Codex | Review, test rerun, truth reconciliation |
| Arbiter | Gemini | Tie-breaking, advisory when verifier cannot resolve |

## Work Flow

1. Claude implements based on handoff instructions
2. Codex verifies the implementation against current tree
3. If Codex cannot resolve, Gemini provides advisory
4. Operator makes final decisions on ambiguous cases
"""

_TMPL_CLAUDE = """\
# Claude Project Instructions

## Working Principles

- Read the codebase before making changes.
- Prefer editing existing files over creating new ones.
- Make the smallest change that solves the problem.
- Do not add comments, docstrings, or type annotations to code you did not change.
- Do not create documentation files unless explicitly requested.

## Verification

- Run relevant tests after making changes.
- Report only what you actually executed and observed.
- If you did not run a verification step, say so explicitly.

## Safety

- Do not run destructive commands without confirmation.
- Do not modify files outside the current task scope.
- Do not commit or push unless explicitly asked.
- Treat .env, credentials, and secret files as off-limits.
"""

_TMPL_GEMINI = """\
# Gemini Instructions

## Role

You serve as an advisory arbiter for this project.
Your primary function is analysis and recommendation, not direct implementation.

## Principles

- Distinguish facts from assumptions in every response.
- When reviewing code or decisions, cite specific file paths and line numbers.
- Prefer the smallest correct recommendation over broad suggestions.
- Do not modify repo files directly unless explicitly asked with edit/write tools.
- Write advisory output only to designated slots (.pipeline/gemini_advice.md).

## Output Format

When providing advisory:
1. State the question or conflict clearly
2. List evidence from the codebase
3. Give a specific, actionable recommendation
4. Note any uncertainty or missing information
"""

_GUIDE_TEMPLATES: list[tuple[str, str]] = [
    ("AGENTS.md", _TMPL_AGENTS),
    ("CLAUDE.md", _TMPL_CLAUDE),
    ("GEMINI.md", _TMPL_GEMINI),
]


def _check_missing_guides(project: Path) -> list[str]:
    """Return list of guide filenames missing from the target repo."""
    return [name for name, _ in _GUIDE_TEMPLATES if not _file_exists(project, name)]


def _create_guide_file(project: Path, name: str, content: str) -> bool:
    """Create a guide file in the target repo. Returns True on success."""
    if IS_WINDOWS:
        full = f"{_wsl_path_str(project)}/{name}"
        # Don't overwrite
        code, _ = _run(["test", "-e", full], timeout=5.0)
        if code == 0:
            return True  # already exists
        code, _ = _run(["bash", "-c", f"cat > '{full}' << 'GUIDEEOF'\n{content}\nGUIDEEOF"], timeout=5.0)
        return code == 0
    path = project / name
    if path.exists():
        return True
    try:
        path.write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False


# ── 파이프라인 제어 ────────────────────────────────────────────

def pipeline_start(project: Path, session: str = "") -> str:
    sess = session or _session_name_for(project)
    script = APP_ROOT / "start-pipeline.sh"
    if IS_WINDOWS:
        # Bundled asset path → /mnt/c/... 로 변환 (WSL bash가 읽을 수 있게)
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
    """별도 터미널에서 tmux attach 실행."""
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


# ── GUI ────────────────────────────────────────────────────────

STATUS_COLORS = {
    "WORKING": "#4ade80",
    "READY": "#5b9cf6",
    "DEAD": "#f87171",
    "BOOTING": "#e0a040",
    "OFF": "#404058",
}


class PipelineGUI:
    def __init__(self, project: Path) -> None:
        self.project = project
        self._session_name = _session_name_for(project)
        self.selected_agent = "Claude"
        self._auto_focus_agent = True
        self._poll_in_flight = False
        self._last_snapshot: dict[str, object] | None = None
        self._working_since: dict[str, float] = {}  # agent label → epoch when WORKING started
        self._poll_after_id: str | None = None
        self._tick_after_id: str | None = None
        self._validate_after_id: str | None = None
        self._setup_state: str = "unknown"  # unknown / checking / ready / missing / failed
        self._project_valid, self._project_error = validate_project_root(project)
        if self._project_valid:
            boot_ok, boot_error = bootstrap_project_root(project)
            if not boot_ok:
                self._project_valid = False
                self._project_error = boot_error
        self.root = Tk()
        self.root.title("Pipeline Launcher")
        self.root.configure(bg="#0f0f0f")
        self.root.resizable(True, True)
        self._set_initial_window_geometry()
        self.root.minsize(900, 600)

        self._build_ui()

        if not self._project_valid:
            self._show_project_error()
        else:
            _save_project_path(_wsl_path_str(self.project) if IS_WINDOWS else str(self.project))
            self._schedule_poll()
            self._tick_after_id = self.root.after(1000, self._tick_elapsed)
            # 초기 setup 자동 점검 (bg thread)
            self.root.after(500, lambda: threading.Thread(
                target=self._run_setup_check_silent, daemon=True).start())

    def _set_initial_window_geometry(self) -> None:
        screen_w = max(1280, self.root.winfo_screenwidth())
        screen_h = max(900, self.root.winfo_screenheight())

        width = min(900, screen_w - 40)
        height = min(900, screen_h - 60)

        x = max(20, (screen_w - width) // 2)
        y = max(20, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        # ── ttk Scrollbar dark style ──
        _ttk_style = TtkStyle()
        _ttk_style.theme_use("clam")
        _ttk_style.configure("Dark.Vertical.TScrollbar",
                             background="#20202e", troughcolor="#0c0c10",
                             borderwidth=0, relief="flat",
                             arrowcolor="#40405a")
        _ttk_style.map("Dark.Vertical.TScrollbar",
                        background=[("active", "#30304a"), ("pressed", "#3a3a50")])

        # ── Ops Console 색상 체계 ──
        bg = "#101014"
        fg = "#d8dae0"
        accent = "#5b9cf6"
        sub_fg = "#6b7280"
        btn_bg = "#1c1c24"
        btn_fg = "#b0b4c0"
        card_bg = "#16161e"
        card_border = "#26263a"
        log_bg = "#0c0c10"
        header_bg = "#0a0a10"

        title_font = tkfont.Font(family="Consolas", size=14, weight="bold")
        body_font = tkfont.Font(family="Consolas", size=10)
        small_font = tkfont.Font(family="Consolas", size=9)
        status_font = tkfont.Font(family="Consolas", size=11, weight="bold")
        section_font = tkfont.Font(family="Consolas", size=9, weight="bold")
        ctrl_font = tkfont.Font(family="Consolas", size=10, weight="bold")

        def make_card(parent: Frame, padx: int = 12, pady: int = 10) -> Frame:
            card = Frame(
                parent,
                bg=card_bg,
                padx=padx,
                pady=pady,
                highlightthickness=1,
                highlightbackground=card_border,
            )
            return card

        def _lighten(hex_color: str, amount: int = 20) -> str:
            """Hex 색상을 약간 밝게."""
            hex_color = hex_color.lstrip("#")
            r = min(255, int(hex_color[0:2], 16) + amount)
            g = min(255, int(hex_color[2:4], 16) + amount)
            b = min(255, int(hex_color[4:6], 16) + amount)
            return f"#{r:02x}{g:02x}{b:02x}"

        # ── 상단 헤더 (콘솔 바) ──
        top = Frame(self.root, bg=header_bg, padx=16, pady=8)
        top.pack(fill=X)
        # 좌측 세로선 accent
        Frame(top, bg=accent, width=3).pack(side=LEFT, fill=Y, padx=(0, 10))

        Label(top, text="PIPELINE OPS", font=title_font, bg=header_bg, fg="#8090b0").pack(side=LEFT)

        # ── Home / Guide 모드 전환 ──
        mode_frame = Frame(top, bg=header_bg)
        mode_frame.pack(side=LEFT, padx=(24, 0))
        self._mode = "home"
        self._mode_btn_home = Button(
            mode_frame, text="OPS", font=ctrl_font,
            bg="#2a2a3a", fg="#d8dae0", activebackground="#3a3a4e", activeforeground="#ffffff",
            bd=0, padx=12, pady=3, highlightthickness=0, cursor="hand2",
            command=lambda: self._switch_mode("home"),
        )
        self._mode_btn_home.bind("<Enter>", lambda e: self._mode_btn_home.configure(bg="#363648"))
        self._mode_btn_home.bind("<Leave>", lambda e: self._mode_btn_home.configure(
            bg="#2a2a3a" if self._mode == "home" else "#18182a"))
        self._mode_btn_home.pack(side=LEFT, padx=(0, 2))
        self._mode_btn_guide = Button(
            mode_frame, text="GUIDE", font=ctrl_font,
            bg="#18182a", fg="#6b7280", activebackground="#2a2a3a", activeforeground="#ffffff",
            bd=0, padx=12, pady=3, highlightthickness=0, cursor="hand2",
            command=lambda: self._switch_mode("guide"),
        )
        self._mode_btn_guide.bind("<Enter>", lambda e: self._mode_btn_guide.configure(bg="#363648"))
        self._mode_btn_guide.bind("<Leave>", lambda e: self._mode_btn_guide.configure(
            bg="#2a2a3a" if self._mode == "guide" else "#18182a"))
        self._mode_btn_guide.pack(side=LEFT)

        self.status_var = StringVar(value="STOPPED")
        self.status_label = Label(
            top,
            textvariable=self.status_var,
            font=ctrl_font,
            bg="#2a1015",
            fg="#f87171",
            padx=12,
            pady=3,
        )
        self.status_label.pack(side=RIGHT)

        # ── 메인 컨텐츠 컨테이너 ──
        self._content_container = Frame(self.root, bg=bg)
        self._content_container.pack(fill=BOTH, expand=True)

        # Home 모드 프레임
        content = Frame(self._content_container, bg=bg, padx=14, pady=12)
        self._home_frame = content
        content.pack(fill=BOTH, expand=True)

        # Guide 모드 프레임 (나중에 채움)
        self._guide_frame = Frame(self._content_container, bg=bg, padx=14, pady=12)

        # ── 프로젝트 경로 (Entry + Browse + Apply) ──
        proj_card = make_card(content)
        proj_card.pack(fill=X, pady=(0, 10))
        Label(proj_card, text="Project", font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")

        path_row = Frame(proj_card, bg=card_bg)
        path_row.pack(fill=X, pady=(4, 0))

        self._path_var = StringVar(
            value=_wsl_path_str(self.project) if IS_WINDOWS else str(self.project),
        )
        self._path_entry = Entry(
            path_row,
            textvariable=self._path_var,
            font=body_font,
            bg="#1a1a1a",
            fg="#f59e0b",
            insertbackground="#f59e0b",
            bd=0,
            highlightthickness=1,
            highlightbackground="#444444",
            highlightcolor="#f59e0b",
        )
        self._path_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 6))
        self._path_entry.bind("<Return>", lambda _e: self._apply_project_path())

        _browse_bg = btn_bg
        self._path_browse_btn = Button(
            path_row,
            text="Browse…",
            command=self._on_browse,
            font=small_font,
            bg=_browse_bg,
            fg=btn_fg,
            activebackground=_lighten(_browse_bg, 30),
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=4,
            highlightthickness=1,
            highlightbackground="#444444",
            cursor="hand2",
        )
        self._path_browse_btn.bind("<Enter>", lambda e: self._path_browse_btn.configure(bg=_lighten(_browse_bg, 18)))
        self._path_browse_btn.bind("<Leave>", lambda e: self._path_browse_btn.configure(bg=_browse_bg))
        self._path_browse_btn.pack(side=RIGHT, padx=(4, 0))

        _apply_bg = btn_bg
        self._path_apply_btn = Button(
            path_row,
            text="Apply",
            command=self._apply_project_path,
            font=small_font,
            bg=_apply_bg,
            fg=btn_fg,
            activebackground=_lighten(_apply_bg, 30),
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=4,
            highlightthickness=1,
            highlightbackground="#444444",
            disabledforeground="#555555",
        )
        self._path_apply_btn.bind("<Enter>", lambda e: self._path_apply_btn.configure(bg=_lighten(_apply_bg, 18)) if str(self._path_apply_btn["state"]) != "disabled" else None)
        self._path_apply_btn.bind("<Leave>", lambda e: self._path_apply_btn.configure(bg=_apply_bg))
        self._path_apply_btn.pack(side=RIGHT)

        # Apply 버튼 활성/비활성: Entry가 비어있으면 비활성
        self._path_var.trace_add("write", self._on_path_var_change)
        self._on_path_var_change()  # 초기 상태 설정

        # ── 최근 프로젝트 quick select ──
        self._recent_row = Frame(proj_card, bg=card_bg)
        self._recent_row.pack(fill=X, pady=(4, 0))
        self._refresh_recent_buttons()

        # ── 제어 패널 ──
        ctrl_bar = Frame(content, bg="#0e0e14")
        ctrl_bar.pack(fill=X, pady=(0, 8))

        def make_ctrl_btn(parent: Frame, text: str, cmd, color: str = btn_bg,
                          fg_color: str = btn_fg) -> Button:
            hover_bg = _lighten(color, 18)
            press_bg = _lighten(color, 30)
            btn = Button(
                parent, text=text, command=cmd, font=ctrl_font,
                bg=color, fg=fg_color, activebackground=press_bg,
                activeforeground="#ffffff", bd=0, padx=14, pady=6,
                highlightthickness=1, highlightbackground="#36364a",
                disabledforeground="#404050", cursor="hand2",
            )
            # hover 피드백
            btn.bind("<Enter>", lambda e, b=btn, h=hover_bg: b.configure(bg=h) if str(b["state"]) != "disabled" else None)
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c) if str(b["state"]) != "disabled" else None)
            return btn

        self.btn_setup = make_ctrl_btn(ctrl_bar, "⚙ SETUP", self._on_setup_check)
        self.btn_setup.pack(side=LEFT, padx=(0, 4))
        self.btn_start = make_ctrl_btn(ctrl_bar, "▶ START", self._on_start, "#1a3a1a", "#4ade80")
        self.btn_start.pack(side=LEFT, padx=4)
        self.btn_stop = make_ctrl_btn(ctrl_bar, "■ STOP", self._on_stop, "#3a1a1a", "#f87171")
        self.btn_stop.pack(side=LEFT, padx=4)
        self.btn_restart = make_ctrl_btn(ctrl_bar, "↻ RESTART", self._on_restart)
        self.btn_restart.pack(side=LEFT, padx=4)
        self.btn_attach = make_ctrl_btn(ctrl_bar, "⬜ ATTACH", self._on_attach)
        self.btn_attach.pack(side=LEFT, padx=4)

        self._action_in_progress = False

        # ── 상태 개요 + 최신 파일 ──
        overview = Frame(content, bg=bg)
        overview.pack(fill=X, pady=(0, 10))

        system_card = make_card(overview)
        system_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 6))
        Label(system_card, text="SYSTEM", font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")
        self.pipeline_var = StringVar(value="Pipeline: —")
        self.watcher_var = StringVar(value="Watcher: —")
        self.setup_var = StringVar(value="Setup: … Checking")
        self.pipeline_state_label = Label(system_card, textvariable=self.pipeline_var, font=body_font, bg=card_bg, fg=fg, anchor="w")
        self.pipeline_state_label.pack(anchor="w", pady=(6, 2))
        self.watcher_state_label = Label(system_card, textvariable=self.watcher_var, font=body_font, bg=card_bg, fg=fg, anchor="w")
        self.watcher_state_label.pack(anchor="w", pady=(0, 2))
        self.setup_state_label = Label(system_card, textvariable=self.setup_var, font=body_font, bg=card_bg, fg="#e0a040", anchor="w")
        self.setup_state_label.pack(anchor="w")

        file_card = make_card(overview)
        file_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(6, 0))
        self._artifacts_title_var = StringVar(value="ARTIFACTS")
        Label(file_card, textvariable=self._artifacts_title_var, font=section_font, bg=card_bg, fg=sub_fg).pack(anchor="w")
        self.work_var = StringVar(value="Latest work: —")
        self.verify_var = StringVar(value="Latest verify: —")
        # current run context
        self._run_context_var = StringVar(value="")
        self._run_context_label = Label(file_card, textvariable=self._run_context_var, font=small_font,
                                         bg=card_bg, fg="#5b9cf6", anchor="w", justify=LEFT, wraplength=400)
        self._run_context_label.pack(anchor="w", pady=(4, 4))
        self._work_label = Label(file_card, textvariable=self.work_var, font=body_font, bg=card_bg, fg="#c0a060", anchor="w", justify=LEFT, wraplength=400)
        self._work_label.pack(anchor="w", pady=(0, 2))
        self._verify_label = Label(file_card, textvariable=self.verify_var, font=body_font, bg=card_bg, fg="#c0a060", anchor="w", justify=LEFT, wraplength=400)
        self._verify_label.pack(anchor="w")

        # ── Agent 상태 ──
        agent_section = Frame(content, bg=bg)
        agent_section.pack(fill=X, pady=(0, 8))
        Label(agent_section, text="AGENTS", font=section_font, bg=bg, fg=sub_fg).pack(anchor="w", pady=(0, 4))

        cards_row = Frame(agent_section, bg=bg)
        cards_row.pack(fill=X)

        agent_card_bg = "#12121a"
        self.agent_labels: list[tuple[Frame, Label, Label, Label, Label]] = []
        for idx, name in enumerate(["Claude", "Codex", "Gemini"]):
            card = Frame(
                cards_row,
                bg=agent_card_bg,
                padx=10,
                pady=8,
                highlightthickness=2,
                highlightbackground="#1e1e2e",
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 3, 0 if idx == 2 else 3))
            cards_row.grid_columnconfigure(idx, weight=1, uniform="agents")

            name_row = Frame(card, bg=agent_card_bg)
            name_row.pack(fill=X)
            dot = Label(name_row, text="●", font=body_font, bg=agent_card_bg, fg="#404058")
            dot.pack(side=LEFT)
            name_lbl = Label(name_row, text=name.upper(), font=section_font, bg=agent_card_bg, fg="#8890a8")
            name_lbl.pack(side=LEFT, padx=(6, 0))

            status_lbl = Label(card, text="—", font=status_font, bg=agent_card_bg, fg="#505068", anchor="w")
            status_lbl.pack(anchor="w", pady=(4, 1))
            note_lbl = Label(card, text="", font=small_font, bg=agent_card_bg, fg="#606878", anchor="w", justify=LEFT, wraplength=250)
            note_lbl.pack(anchor="w")
            quota_lbl = Label(card, text="", font=small_font, bg=agent_card_bg, fg="#505868", anchor="w", justify=LEFT, wraplength=250)
            quota_lbl.pack(anchor="w", pady=(2, 0))
            self.agent_labels.append((card, dot, status_lbl, note_lbl, quota_lbl))

            for widget in (card, name_row, dot, name_lbl, status_lbl, note_lbl, quota_lbl):
                widget.bind("<Button-1>", lambda _event, agent=name: self._select_agent(agent))
                widget.configure(cursor="hand2")

        # ── 하단 2영역: agent output + watcher log ──
        from tkinter import PanedWindow, VERTICAL

        paned = PanedWindow(content, orient=VERTICAL, bg="#222222", sashwidth=4, sashrelief="flat")
        paned.pack(fill=BOTH, expand=True)
        self.paned = paned

        # ── 선택 agent 상세 출력 (콘솔 패널) ──
        focus_frame = Frame(paned, bg=log_bg, padx=0, pady=0,
                            highlightthickness=1, highlightbackground="#1e1e30")

        focus_header = Frame(focus_frame, bg="#12121c", padx=10, pady=5)
        focus_header.pack(fill=X)
        Label(focus_header, text="AGENT OUTPUT", font=section_font, bg="#12121c", fg="#5060a0").pack(side=LEFT)
        self.focus_title_var = StringVar(value="CLAUDE • pane tail")
        Label(focus_header, textvariable=self.focus_title_var, font=small_font, bg="#12121c", fg="#4a5070").pack(side=RIGHT)

        focus_font = tkfont.Font(family="Consolas", size=9)
        self.focus_text = Text(
            focus_frame, font=focus_font, bg=log_bg, fg="#a0a8c0",
            wrap=WORD, bd=0, highlightthickness=0, padx=12, pady=8,
            state=DISABLED, spacing1=0, spacing3=1,
        )
        focus_scroll = TtkScrollbar(focus_frame, command=self.focus_text.yview, style="Dark.Vertical.TScrollbar")
        self.focus_text.configure(yscrollcommand=focus_scroll.set)
        focus_scroll.pack(side=RIGHT, fill=Y)
        self.focus_text.pack(side=LEFT, fill=BOTH, expand=True)

        paned.add(focus_frame, minsize=140, stretch="always")

        # ── Watcher log (콘솔 패널) ──
        log_frame = Frame(paned, bg=log_bg, padx=0, pady=0,
                          highlightthickness=1, highlightbackground="#1e1e30")

        log_header = Frame(log_frame, bg="#12121c", padx=10, pady=5)
        log_header.pack(fill=X)
        self._log_title_var = StringVar(value="WATCHER LOG")
        Label(log_header, textvariable=self._log_title_var, font=section_font, bg="#12121c", fg="#5060a0").pack(side=LEFT)

        self.log_text = Text(log_frame, font=small_font, bg=log_bg, fg="#707898",
                             wrap=WORD, bd=0, highlightthickness=0, padx=12, pady=6,
                             state=DISABLED)
        scrollbar = TtkScrollbar(log_frame, command=self.log_text.yview, style="Dark.Vertical.TScrollbar")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        paned.add(log_frame, minsize=100, stretch="never")
        # 초기 sash: focus 75% / log 25%
        self.root.update_idletasks()
        paned_h = paned.winfo_height()
        if paned_h > 240:
            paned.sash_place(0, 0, int(paned_h * 0.75))

        # ── Guide 모드 화면 (상단 Home/Guide 전환으로 표시) ──
        gf = self._guide_frame

        guide_header = Frame(gf, bg=card_bg, padx=12, pady=8,
                             highlightthickness=1, highlightbackground=card_border)
        guide_header.pack(fill=X, pady=(0, 10))
        Label(guide_header, text="Project Guide", font=section_font, bg=card_bg, fg=sub_fg).pack(side=LEFT)
        self._guide_status_var = StringVar(value="")
        Label(guide_header, textvariable=self._guide_status_var, font=small_font,
              bg=card_bg, fg="#34d399").pack(side=RIGHT)
        _export_bg = "#2563eb"
        _export_btn = Button(
            guide_header, text="  Export .md  ", command=self._export_guide_md,
            font=tkfont.Font(family="Consolas", size=10, weight="bold"),
            bg=_export_bg, fg="#ffffff",
            activebackground="#1d4ed8", activeforeground="#ffffff",
            bd=0, padx=14, pady=5,
            highlightthickness=1, highlightbackground="#3b82f6",
            cursor="hand2",
        )
        _export_btn.bind("<Enter>", lambda e: _export_btn.configure(bg=_lighten(_export_bg, 20)))
        _export_btn.bind("<Leave>", lambda e: _export_btn.configure(bg=_export_bg))
        _export_btn.pack(side=RIGHT, padx=(0, 8))

        guide_body = Frame(gf, bg=bg)
        guide_body.pack(fill=BOTH, expand=True)

        self._guide_text = Text(
            guide_body, font=body_font, bg="#1a1a1a", fg="#d4d4d8",
            wrap=WORD, bd=0,
            highlightthickness=1, highlightbackground="#333333",
            padx=10, pady=8, state=DISABLED,
            cursor="arrow",
        )
        guide_scroll = TtkScrollbar(guide_body, command=self._guide_text.yview, style="Dark.Vertical.TScrollbar")
        self._guide_text.configure(yscrollcommand=guide_scroll.set)
        guide_scroll.pack(side=RIGHT, fill=Y)
        self._guide_text.pack(side=LEFT, fill=BOTH, expand=True)

        # canonical guide 로드
        self._load_project_guide()

        # ── 상단 overlay toast banner ──
        self._toast_font = tkfont.Font(family="Consolas", size=10, weight="bold")
        self.msg_var = StringVar(value="")
        self.msg_label = Label(
            self.root,
            textvariable=self.msg_var,
            font=self._toast_font,
            bg="#1e3a5f",
            fg="#93c5fd",
            pady=8,
            padx=18,
            anchor="center",
            wraplength=700,
        )
        # 초기엔 숨김 — _show_toast에서 place로 표시
        self.msg_var.trace_add("write", self._on_toast_change)
        self.root.after(120, self._set_initial_pane_split)

    def _set_initial_pane_split(self) -> None:
        try:
            total_h = self.paned.winfo_height()
            if total_h > 240:
                self.paned.sash_place(0, 0, int(total_h * 0.62))
        except Exception:
            pass

    def _ensure_log_pane_visible(self) -> None:
        try:
            total_h = self.paned.winfo_height()
            if total_h <= 240:
                return
            _x, sash_y = self.paned.sash_coord(0)
            lower_h = total_h - sash_y
            if lower_h < 150:
                self.paned.sash_place(0, 0, int(total_h * 0.62))
        except Exception:
            pass

    # ── 데이터 수집 (tmux 호출 통합) ──

    _prev_focus_text: str = ""
    _prev_log_text: str = ""

    def _collect_all_agent_data(self) -> tuple[list[tuple[str, str, str, str]], dict[str, str]]:
        """list-panes 1회 + capture-pane x3 = 4회 subprocess로 status + output 둘 다 반환."""
        code, output = _run(
            ["tmux", "list-panes", "-t", f"{self._session_name}:0", "-F", "#{pane_index}|#{pane_id}|#{pane_dead}"],
            timeout=TMUX_QUERY_TIMEOUT,
        )
        if code != 0 or not output:
            return (
                [("Claude", "OFF", "", ""), ("Codex", "OFF", "", ""), ("Gemini", "OFF", "", "")],
                {},
            )

        names = {0: "Claude", 1: "Codex", 2: "Gemini"}
        hints = watcher_runtime_hints(self.project)
        agents: list[tuple[str, str, str, str]] = []
        pane_map: dict[str, str] = {}

        for raw in output.splitlines():
            try:
                idx_s, pane_id, dead = raw.split("|", 2)
                idx = int(idx_s)
            except ValueError:
                continue
            label = names.get(idx, f"Pane {idx}")
            if dead == "1":
                agents.append((label, "DEAD", "", ""))
                pane_map[label] = ""
                continue

            # 한 번만 capture — 긴 history로 가져와서 status와 output 양쪽에 사용
            cap_code, captured = _run(
                ["tmux", "capture-pane", "-J", "-p", "-t", pane_id, "-S", "-180"],
                timeout=TMUX_QUERY_TIMEOUT,
            )
            if cap_code != 0 or not captured:
                agents.append((label, "BOOTING", "", ""))
                pane_map[label] = ""
                continue

            cleaned = ANSI_RE.sub("", captured)

            # status 판정 (agent_snapshots 로직)
            status, note = detect_agent_status(label, cleaned)
            quota = extract_quota_note(cleaned)
            hint = hints.get(label)
            if hint:
                hint_status, hint_note = hint
                if hint_status == "WORKING":
                    status = "WORKING"
                    if not note:
                        note = hint_note
                elif hint_status == "READY" and status == "BOOTING":
                    status = "READY"
                    note = ""
            agents.append((label, status, note, quota))

            # output (capture_agent_panes 로직)
            pane_map[label] = rejoin_wrapped_pane_lines(cleaned)

        return agents, pane_map

    def _update_text_if_changed(self, widget: Text, new_text: str) -> None:
        """Text 위젯의 내용이 바뀌었을 때만 갱신합니다."""
        widget.configure(state=NORMAL)
        current = widget.get("1.0", f"{END}-1c")
        if current == new_text:
            widget.configure(state=DISABLED)
            return
        at_bottom = widget.yview()[1] >= 0.95
        widget.delete("1.0", END)
        widget.insert(END, new_text)
        # Windows Tk에서 disabled Text의 fg가 무시되는 문제 우회:
        # tag로 전체 텍스트에 fg 색상을 강제 적용
        fg_color = widget.cget("fg") or widget.cget("foreground")
        if fg_color:
            widget.tag_configure("visible", foreground=fg_color)
            widget.tag_add("visible", "1.0", END)
        widget.configure(state=DISABLED)
        if at_bottom:
            widget.see(END)

    def _select_agent(self, agent: str) -> None:
        self.selected_agent = agent
        self._auto_focus_agent = False
        if self._last_snapshot is not None:
            self._apply_snapshot(self._last_snapshot)
        else:
            self._start_poll_worker()

    # ── 폴링 ──

    def _show_project_error(self) -> None:
        """invalid project root일 때 GUI를 에러 상태로 표시합니다."""
        self.status_var.set("Invalid Project")
        self.status_label.configure(fg="#ef4444", bg="#351717")
        self.pipeline_var.set("Pipeline: — (invalid project root)")
        self.pipeline_state_label.configure(fg="#ef4444")
        self.watcher_var.set("Watcher: —")
        self.watcher_state_label.configure(fg="#888888")
        self.work_var.set("Latest work: —")
        self.verify_var.set("Latest verify: —")
        self._set_toast_style("error")
        self.msg_var.set(self._project_error)
        self.setup_var.set("Setup: —")
        self.setup_state_label.configure(fg="#888888")
        # 모든 버튼 비활성
        self.btn_setup.configure(state=DISABLED)
        self.btn_start.configure(state=DISABLED)
        self.btn_stop.configure(state=DISABLED)
        self.btn_restart.configure(state=DISABLED)
        self.btn_attach.configure(state=DISABLED)

    def _tick_elapsed(self) -> None:
        """Lightweight tick — updates WORKING elapsed note aligned to second boundaries."""
        now = time.time()
        for i, name in enumerate(("Claude", "Codex", "Gemini")):
            since = self._working_since.get(name)
            if since is not None and i < len(self.agent_labels):
                new_text = format_elapsed(now - since)
                _, _, _, note_lbl, _ = self.agent_labels[i]
                if note_lbl.cget("text") != new_text:
                    note_lbl.configure(text=new_text)
        # Align to next whole-second boundary for metronomic rhythm
        frac_ms = int((now % 1.0) * 1000)
        self._tick_after_id = self.root.after(max(50, 1000 - frac_ms), self._tick_elapsed)

    def _schedule_poll(self) -> None:
        self._start_poll_worker()
        self._poll_after_id = self.root.after(POLL_MS, self._schedule_poll)

    def _stop_all_timers(self) -> None:
        """Cancel active poll and tick chains."""
        if self._poll_after_id is not None:
            self.root.after_cancel(self._poll_after_id)
            self._poll_after_id = None
        if self._tick_after_id is not None:
            self.root.after_cancel(self._tick_after_id)
            self._tick_after_id = None

    _VALIDATE_DEBOUNCE_MS = 600

    def _refresh_recent_buttons(self) -> None:
        """최근 프로젝트 목록에서 quick-select 버튼을 재생성합니다."""
        if not hasattr(self, "_recent_row"):
            return  # _build_ui에서 아직 생성 전 (trace_add 조기 발화 방어)
        for child in self._recent_row.winfo_children():
            child.destroy()

        recent = _load_recent_projects()
        current = self._path_var.get().strip()

        if current:
            current_short = Path(current).name or current
            current_lbl = Label(
                self._recent_row,
                text=f"현재: {current_short}",
                font=tkfont.Font(family="Consolas", size=8),
                bg="#141414",
                fg="#f59e0b",
                padx=6,
                pady=2,
                highlightthickness=1,
                highlightbackground="#444444",
            )
            current_lbl.pack(side=LEFT, padx=(0, 6))

        other_recent = [path_str for path_str in recent if path_str != current]
        if not other_recent:
            empty_lbl = Label(
                self._recent_row,
                text="최근 경로 없음",
                font=tkfont.Font(family="Consolas", size=8),
                bg="#171717",
                fg="#6b7280",
                padx=2,
                pady=2,
            )
            empty_lbl.pack(side=LEFT)
            return

        recent_lbl = Label(
            self._recent_row,
            text="최근:",
            font=tkfont.Font(family="Consolas", size=8),
            bg="#171717",
            fg="#9ca3af",
            padx=2,
            pady=2,
        )
        recent_lbl.pack(side=LEFT, padx=(0, 4))

        for path_str in other_recent:
            short = Path(path_str).name or path_str
            btn = Button(
                self._recent_row,
                text=short,
                command=lambda p=path_str: self._on_recent_select(p),
                font=tkfont.Font(family="Consolas", size=8),
                bg="#1a1a1a",
                fg="#9ca3af",
                activebackground="#333333",
                activeforeground="#f59e0b",
                bd=0,
                padx=6,
                pady=2,
                highlightthickness=1,
                highlightbackground="#333333",
            )
            btn.pack(side=LEFT, padx=(0, 4))

    def _on_recent_select(self, path_str: str) -> None:
        """Quick-select 클릭 시 Entry에 경로를 채웁니다."""
        self._path_var.set(path_str)
        self._refresh_recent_buttons()

    def _switch_mode(self, mode: str) -> None:
        """Home/Guide 모드 전환."""
        if mode == self._mode:
            return
        self._mode = mode
        if mode == "home":
            self._guide_frame.pack_forget()
            self._home_frame.pack(fill=BOTH, expand=True)
            self._mode_btn_home.configure(bg="#2a2a3a", fg="#d8dae0")
            self._mode_btn_guide.configure(bg="#18182a", fg="#6b7280")
        else:
            self._home_frame.pack_forget()
            self._guide_frame.pack(fill=BOTH, expand=True)
            self._mode_btn_guide.configure(bg="#2a2a3a", fg="#d8dae0")
            self._mode_btn_home.configure(bg="#18182a", fg="#6b7280")

    def _load_project_guide(self) -> None:
        """canonical guide를 read-only 텍스트 위젯에 로드합니다."""
        if not hasattr(self, "_guide_text"):
            return
        self._guide_text.configure(state=NORMAL)
        self._guide_text.delete("1.0", END)
        self._guide_text.insert("1.0", _DEFAULT_GUIDE)
        fg_color = self._guide_text.cget("fg") or self._guide_text.cget("foreground")
        if fg_color:
            self._guide_text.tag_configure("visible", foreground=fg_color)
            self._guide_text.tag_add("visible", "1.0", END)
        self._guide_text.configure(state=DISABLED)
        self._guide_status_var.set("")

    def _export_guide_md(self) -> None:
        """현재 guide 내용을 .md 파일로 내보냅니다."""
        project_name = Path(_wsl_path_str(self.project) if IS_WINDOWS else str(self.project)).name or "project"
        default_name = f"{project_name}-pipeline-guide.md"
        path = filedialog.asksaveasfilename(
            title="Export Pipeline Guide",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not path:
            return
        text = self._guide_text.get("1.0", f"{END}-1c")
        try:
            Path(path).write_text(text, encoding="utf-8")
            self._guide_status_var.set(f"Exported: {Path(path).name}")
            self.root.after(3000, lambda: self._guide_status_var.set(""))
        except OSError as e:
            self._guide_status_var.set(f"Export failed: {e}")
            self.root.after(5000, lambda: self._guide_status_var.set(""))

    def _on_path_var_change(self, *_args: object) -> None:
        """Entry 변경 시 cheap precheck + debounced marker 검증으로 Apply 활성/비활성."""
        # Cancel pending debounced check
        if self._validate_after_id is not None:
            self.root.after_cancel(self._validate_after_id)
            self._validate_after_id = None

        raw = self._path_var.get().strip()

        # Tier 1: instant cheap precheck
        if not raw:
            self._path_apply_btn.configure(state=DISABLED)
            return
        normalized = _normalize_picked_path(raw)
        if not normalized.startswith("/"):
            self._path_apply_btn.configure(state=DISABLED)
            self._refresh_recent_buttons()
            return

        # Format OK — disable while waiting for debounced marker check
        self._path_apply_btn.configure(state=DISABLED)
        self._refresh_recent_buttons()
        self._validate_after_id = self.root.after(
            self._VALIDATE_DEBOUNCE_MS,
            lambda: self._check_path_markers(normalized),
        )

    def _check_path_markers(self, path_str: str) -> None:
        """Debounced marker validation — lightweight check for repo markers."""
        self._validate_after_id = None

        def _apply(valid: bool) -> None:
            # Only apply if entry still matches this check
            current = _normalize_picked_path(self._path_var.get().strip())
            if current == path_str:
                self._path_apply_btn.configure(state=NORMAL if valid else DISABLED)

        if IS_WINDOWS:
            # Run wsl test in background thread to avoid blocking GUI
            def _worker() -> None:
                code, _ = _run(["test", "-f", f"{path_str}/AGENTS.md"], timeout=3.0)
                valid = code == 0
                try:
                    self.root.after(0, lambda: _apply(valid))
                except Exception:
                    pass
            threading.Thread(target=_worker, daemon=True).start()
        else:
            # Linux: instant filesystem check
            p = Path(path_str)
            _apply((p / "AGENTS.md").exists())

    def _on_browse(self) -> None:
        """폴더 선택기를 열어 project root를 선택합니다."""
        if IS_WINDOWS:
            initial = f"\\\\wsl.localhost\\{WSL_DISTRO}"
        else:
            initial = str(Path.home())
        picked = filedialog.askdirectory(
            title="Select project root",
            initialdir=initial,
        )
        if not picked:
            return  # 취소됨
        normalized = _normalize_picked_path(picked)
        self._path_var.set(normalized)
        # Browse gave us a real directory — skip debounce, validate immediately
        if self._validate_after_id is not None:
            self.root.after_cancel(self._validate_after_id)
            self._validate_after_id = None
        self._check_path_markers(normalized)

    def _apply_project_path(self) -> None:
        """Entry에서 입력한 경로를 검증하고 적용합니다."""
        new_path_str = self._path_var.get().strip()
        if not new_path_str:
            return
        # Normalize in case user pasted a UNC path directly
        new_path_str = _normalize_picked_path(new_path_str)
        self._path_var.set(new_path_str)
        new_path = Path(new_path_str)
        valid, error = validate_project_root(new_path)
        if valid:
            boot_ok, boot_error = bootstrap_project_root(new_path)
            if not boot_ok:
                self._stop_all_timers()
                self._project_valid = False
                self._project_error = boot_error
                self._show_project_error()
                return
            self._stop_all_timers()
            self.project = new_path
            self._session_name = _session_name_for(new_path)
            self._project_valid = True
            self._project_error = ""
            self._working_since.clear()
            self._last_snapshot = None
            _save_project_path(new_path_str)
            self._refresh_recent_buttons()
            self._load_project_guide()
            self._set_toast_style("success")
            self.msg_var.set(f"Project applied: {new_path_str}")
            self._clear_msg_later()
            self._schedule_poll()
            self._tick_after_id = self.root.after(1000, self._tick_elapsed)
        else:
            self._stop_all_timers()
            self._project_valid = False
            self._project_error = error
            self._show_project_error()

    def _start_poll_worker(self) -> None:
        if self._poll_in_flight:
            return
        self._poll_in_flight = True
        threading.Thread(target=self._poll_worker, daemon=True).start()

    def _poll_worker(self) -> None:
        snapshot: dict[str, object] | None = None
        try:
            snapshot = self._build_snapshot()
        except Exception:
            snapshot = None

        def _finish() -> None:
            self._poll_in_flight = False
            if snapshot is not None:
                self._apply_snapshot(snapshot)

        try:
            self.root.after(0, _finish)
        except Exception:
            self._poll_in_flight = False

    def _build_snapshot(self) -> dict[str, object]:
        session_ok = tmux_alive(self._session_name)
        w_alive, w_pid = watcher_alive(self.project)
        agents, pane_map = self._collect_all_agent_data()
        work_name, work_mtime = latest_md(self.project / "work")
        verify_name, verify_mtime = latest_md(self.project / "verify")
        log_lines = watcher_log_tail(self.project, lines=14)
        # run summary는 더 넓은 범위에서 추출 (최근 50줄)
        summary_lines = watcher_log_tail(self.project, lines=50)
        run_summary = _extract_run_summary(summary_lines)

        return {
            "session_ok": session_ok,
            "watcher_alive": w_alive,
            "watcher_pid": w_pid,
            "agents": agents,
            "pane_map": pane_map,
            "work_name": work_name,
            "work_mtime": work_mtime,
            "verify_name": verify_name,
            "verify_mtime": verify_mtime,
            "log_lines": log_lines,
            "run_summary": run_summary,
        }

    def _apply_snapshot(self, snapshot: dict[str, object]) -> None:
        self._last_snapshot = snapshot
        session_ok = bool(snapshot["session_ok"])
        w_alive = bool(snapshot["watcher_alive"])
        w_pid = snapshot["watcher_pid"]
        agents = snapshot["agents"]
        pane_map = snapshot["pane_map"]
        work_name = snapshot["work_name"]
        work_mtime = float(snapshot["work_mtime"])
        verify_name = snapshot["verify_name"]
        verify_mtime = float(snapshot["verify_mtime"])
        log_lines = snapshot["log_lines"]
        run = snapshot.get("run_summary", {})

        # Pipeline status
        if session_ok:
            self.pipeline_var.set("Pipeline: ● RUNNING")
            self.status_var.set("RUNNING")
            self.status_label.configure(fg="#4ade80", bg="#0a2a18")
            self.pipeline_state_label.configure(fg="#4ade80")
        else:
            self.pipeline_var.set("Pipeline: ■ STOPPED")
            self.status_var.set("STOPPED")
            self.status_label.configure(fg="#f87171", bg="#2a1015")
            self.pipeline_state_label.configure(fg="#f87171")

        # Watcher
        if w_alive:
            self.watcher_var.set(f"Watcher: ● Alive (PID:{w_pid})")
            self.watcher_state_label.configure(fg="#34d399")
        else:
            self.watcher_var.set("Watcher: ✗ Dead")
            self.watcher_state_label.configure(fg="#ef4444")

        working_labels = [label for label, status, _note, _quota in agents if status == "WORKING"]
        if self.selected_agent not in {label for label, _s, _n, _q in agents}:
            self.selected_agent = working_labels[0] if working_labels else "Claude"
        elif self._auto_focus_agent and working_labels:
            self.selected_agent = working_labels[0]

        now = time.time()
        for i, (card, dot_lbl, status_lbl, note_lbl, quota_lbl) in enumerate(self.agent_labels):
            if i < len(agents):
                label, status, note, quota = agents[i]
                color = STATUS_COLORS.get(status, "#666666")
                dot_lbl.configure(fg=color)
                status_lbl.configure(text=status, fg=color)
                # Track working_since for smooth 1s elapsed ticks
                if status == "WORKING":
                    if label not in self._working_since:
                        # First detection — anchor and set initial note
                        elapsed = _parse_elapsed(note)
                        self._working_since[label] = now - elapsed if elapsed > 0 else now
                        note_lbl.configure(text=note or format_elapsed(0), fg="#9ca3af")
                    else:
                        # Already ticking — only re-anchor on large drift (>5s),
                        # do NOT touch note_lbl (tick handles it to avoid stutter)
                        elapsed = _parse_elapsed(note)
                        if elapsed > 0:
                            computed = now - self._working_since[label]
                            if abs(computed - elapsed) > 5:
                                self._working_since[label] = now - elapsed
                else:
                    self._working_since.pop(label, None)
                    note_lbl.configure(text=note or "대기 중", fg="#9ca3af")
                quota_lbl.configure(text=f"Quota: {quota}" if quota else "Quota: —", fg="#7c8798")
                if label == self.selected_agent:
                    # Selected: 굵은 밝은 파란 보더 + 밝은 배경
                    sel_bg = "#1a1a30"
                    card.configure(highlightbackground="#6ea8ff", highlightthickness=3, bg=sel_bg)
                    for child in card.winfo_children():
                        try:
                            child.configure(bg=sel_bg)
                        except Exception:
                            pass
                else:
                    if status == "WORKING":
                        # WORKING (not selected): 녹색 보더 + 녹색 tint
                        card.configure(highlightbackground="#4ade80", highlightthickness=2, bg="#0e2a18")
                        for child in card.winfo_children():
                            try:
                                child.configure(bg="#0e2a18")
                            except Exception:
                                pass
                    else:
                        # 기본: 얇은 어두운 보더
                        card.configure(highlightbackground="#1e1e2e", highlightthickness=1, bg="#12121a")
                        for child in card.winfo_children():
                            try:
                                child.configure(bg="#12121a")
                            except Exception:
                                pass
            else:
                dot_lbl.configure(fg="#666666")
                status_lbl.configure(text="—", fg="#666666")
                note_lbl.configure(text="", fg="#666666")
                quota_lbl.configure(text="Quota: —", fg="#666666")
                card.configure(highlightbackground="#2a2a2a")

        # running vs stopped 구분 — 아래 title/color에서 사용
        is_live = session_ok and w_alive

        selected_text = format_focus_output(pane_map.get(self.selected_agent, ""))

        # 빈 출력이면 run context를 fallback으로 표시
        if selected_text in ("(출력 없음)", "(표시할 출력 없음)") and is_live:
            fallback_parts = []
            run_turn = run.get("turn", "")
            run_phase = run.get("phase", "")
            run_job = run.get("job", "")
            if run_turn:
                fallback_parts.append(f"Current turn: {run_turn}")
            if run_phase:
                fallback_parts.append(f"Phase: {run_phase}")
            if run_job:
                fallback_parts.append(f"Job: {run_job}")
            # agent별 watcher 힌트 추가
            for label, status, note, _quota in agents:
                if label == self.selected_agent and status == "WORKING" and note:
                    fallback_parts.append(f"{label}: WORKING ({note})")
                elif label == self.selected_agent and status != "OFF":
                    fallback_parts.append(f"{label}: {status}")
            if fallback_parts:
                selected_text = "\n".join(fallback_parts)

        if is_live:
            title_suffix = "pane tail" if selected_text not in ("(출력 없음)", "(표시할 출력 없음)") else "run context"
            self.focus_title_var.set(f"{self.selected_agent.upper()} • {title_suffix}")
        else:
            self.focus_title_var.set(f"{self.selected_agent.upper()} • pane tail (last run)")
        self._update_text_if_changed(self.focus_text, selected_text)

        # Artifacts / log: stale label + dim color
        stale_tag = "" if is_live else " (last run)"
        artifact_color = "#c0a060" if is_live else "#505868"

        self._artifacts_title_var.set("ARTIFACTS" if is_live else "ARTIFACTS (last run)")
        self._work_label.configure(fg=artifact_color)
        self._verify_label.configure(fg=artifact_color)

        # current run context
        run_job = run.get("job", "")
        run_phase = run.get("phase", "")
        run_turn = run.get("turn", "")
        if is_live and (run_job or run_phase or run_turn):
            parts = []
            if run_turn:
                parts.append(f"Turn: {run_turn}")
            if run_phase:
                parts.append(f"Phase: {run_phase}")
            if run_job:
                # job ID에서 날짜 이후 의미 부분만 추출
                short_job = run_job.split("-", 1)[1][:50] if "-" in run_job else run_job[:50]
                parts.append(f"Job: {short_job}")
            self._run_context_var.set(" │ ".join(parts))
            self._run_context_label.configure(fg="#5b9cf6")
        elif not is_live and run_job:
            self._run_context_var.set(f"Last job: {run_job.split('-', 1)[1][:50] if '-' in run_job else run_job[:50]}")
            self._run_context_label.configure(fg="#404058")
        else:
            self._run_context_var.set("")

        work_display = f"Latest work:   {work_name}"
        if work_mtime:
            work_display += f" ({time_ago(work_mtime)})"
        verify_display = f"Latest verify: {verify_name}"
        if verify_mtime:
            verify_display += f" ({time_ago(verify_mtime)})"
        self.work_var.set(work_display)
        self.verify_var.set(verify_display)

        # watcher log title에 run summary 반영
        log_hint_parts = []
        if run_turn:
            log_hint_parts.append(run_turn)
        if run_phase:
            log_hint_parts.append(run_phase)
        log_hint = f" • {' → '.join(log_hint_parts)}" if log_hint_parts else ""
        if is_live:
            self._log_title_var.set(f"WATCHER LOG{log_hint}")
        else:
            self._log_title_var.set(f"WATCHER LOG (last run){log_hint}")

        log_text = "\n".join(
            (l.strip()[:140] + "…" if len(l.strip()) > 143 else l.strip())
            for l in log_lines
        )
        self._update_text_if_changed(self.log_text, log_text)

        # 버튼 enable/disable — 작업 중이면 전부 비활성
        if self._action_in_progress:
            self.btn_setup.configure(state=DISABLED)
            self.btn_start.configure(state=DISABLED)
            self.btn_stop.configure(state=DISABLED)
            self.btn_restart.configure(state=DISABLED)
            self.btn_attach.configure(state=DISABLED)
        else:
            self.btn_setup.configure(state=NORMAL)
            can_start = not session_ok and self._setup_state == "ready"
            self.btn_start.configure(state=NORMAL if can_start else DISABLED)
            self.btn_stop.configure(state=NORMAL if session_ok else DISABLED)
            self.btn_restart.configure(state=NORMAL if session_ok else DISABLED)
            self.btn_attach.configure(state=NORMAL if session_ok else DISABLED)

    # ── 제어 ──

    def _on_toast_change(self, *_args: object) -> None:
        """Toast 텍스트 변경 시 표시/숨김 전환."""
        text = self.msg_var.get().strip()
        if text:
            self.msg_label.place(relx=0.5, rely=0.0, anchor="n", y=4)
            self.msg_label.lift()
        else:
            self.msg_label.place_forget()

    def _set_toast_style(self, level: str) -> None:
        """Toast 색상을 level에 따라 설정."""
        if level == "progress":
            self.msg_label.configure(bg="#141830", fg="#7090d0")
        elif level == "success":
            self.msg_label.configure(bg="#0a2a18", fg="#4ade80")
        elif level == "error":
            self.msg_label.configure(bg="#2a1015", fg="#f87171")
        else:
            self.msg_label.configure(bg="#141830", fg="#7090d0")

    def _lock_buttons(self, label: str) -> None:
        self._action_in_progress = True
        self._set_toast_style("progress")
        self.msg_var.set(label)

    def _unlock_buttons(self, msg: str, is_error: bool = False) -> None:
        self._action_in_progress = False
        self._set_toast_style("error" if is_error else "success")
        self.msg_var.set(msg)

    def _clear_msg_later(self, delay_ms: int = 6000) -> None:
        self.root.after(delay_ms, lambda: self.msg_var.set("") if not self._action_in_progress else None)

    # ── Setup state ──

    def _set_setup_state(self, state: str, detail: str = "") -> None:
        """Setup 상태 UI를 갱신합니다. main thread에서 호출해야 합니다."""
        self._setup_state = state
        if state == "ready":
            self.setup_var.set("Setup: ● Ready")
            self.setup_state_label.configure(fg="#34d399")
        elif state == "ready_warn":
            self.setup_var.set(f"Setup: ● Ready ({detail})")
            self.setup_state_label.configure(fg="#f59e0b")
        elif state == "checking":
            self.setup_var.set(f"Setup: … {detail or 'Checking'}")
            self.setup_state_label.configure(fg="#f59e0b")
        elif state == "missing":
            self.setup_var.set(f"Setup: ■ Missing {detail}")
            self.setup_state_label.configure(fg="#ef4444")
        elif state == "failed":
            self.setup_var.set(f"Setup: ■ {detail or 'Install failed'}")
            self.setup_state_label.configure(fg="#ef4444")
        else:
            self.setup_var.set("Setup: — Unknown")
            self.setup_state_label.configure(fg="#888888")
        self._sync_start_button_state()

    def _sync_start_button_state(self) -> None:
        """Setup 상태에 따라 Start 버튼 활성/비활성."""
        if self._action_in_progress:
            return
        can_start = self._setup_state in ("ready", "ready_warn")
        self.btn_start.configure(state=NORMAL if can_start else DISABLED)

    def _msg(self, text: str) -> None:
        """Background thread에서 안전하게 하단 메시지 갱신."""
        self.root.after(0, lambda: self.msg_var.set(text))

    def _ask_yn(self, title: str, msg: str, icon: str = "warning") -> bool:
        """Background thread에서 main-thread messagebox를 호출하고 결과 대기."""
        result: list[bool | None] = [None]
        def _ask() -> None:
            result[0] = messagebox.askyesno(title, msg, icon=icon)
        self.root.after(0, _ask)
        while result[0] is None:
            time.sleep(0.1)
        return bool(result[0])

    # ── Setup/Check ──

    def _run_setup_check_silent(self) -> None:
        """앱 시작 시 자동 점검 — dialog 없이 상태만 갱신."""
        self.root.after(0, lambda: self._set_setup_state("checking"))
        total = len(_HARD_BLOCKERS) + len(_SOFT_WARNINGS)
        step = 0

        # Hard blockers
        missing_hard: list[tuple[str, str]] = []
        for label, check_type, target, hint in _HARD_BLOCKERS:
            step += 1
            self.root.after(0, lambda n=label, s=step: self._set_setup_state(
                "checking", f"({s}/{total}) {n}"))
            try:
                if check_type == "cli":
                    ok = _find_cli_bin(target)
                elif check_type == "launcher_file":
                    ok = _file_exists(APP_ROOT, target)
                elif check_type == "repo_file":
                    ok = _file_exists(self.project, target)
                else:
                    ok = True
            except Exception:
                ok = False
            if not ok:
                missing_hard.append((label, hint))

        if missing_hard:
            names = ", ".join(n for n, _ in missing_hard)
            self.root.after(0, lambda: self._set_setup_state("missing", names))
            return

        # Soft warnings
        warns: list[str] = []
        for label, check_type, target in _SOFT_WARNINGS:
            step += 1
            self.root.after(0, lambda n=label, s=step: self._set_setup_state(
                "checking", f"({s}/{total}) {n}"))
            try:
                if check_type == "launcher_file":
                    ok = _file_exists(APP_ROOT, target)
                elif check_type == "repo_file":
                    ok = _file_exists(self.project, target)
                else:
                    ok = True
            except Exception:
                ok = True  # soft — assume ok on error
            if not ok:
                warns.append(label)

        if warns:
            detail = ", ".join(warns) + " 없음"
            self.root.after(0, lambda: self._set_setup_state("ready_warn", detail))
        else:
            self.root.after(0, lambda: self._set_setup_state("ready"))

    def _on_setup_check(self) -> None:
        """Setup/Check 버튼 — 점검 + 설치 제안."""
        if self._action_in_progress:
            return
        self._lock_buttons("⚙ Checking dependencies...")
        threading.Thread(target=self._do_setup_check, daemon=True).start()

    def _do_setup_check(self) -> None:
        """Hard blocker + soft warning 점검 → 누락 guide 승인 생성 → 설치 제안."""
        total = len(_HARD_BLOCKERS) + len(_SOFT_WARNINGS)
        step = 0

        # ── 1. Hard blockers 점검 ──
        missing_hard: list[tuple[str, str]] = []
        for label, check_type, target, hint in _HARD_BLOCKERS:
            step += 1
            self._msg(f"⚙ 점검 ({step}/{total}) {label}...")
            self.root.after(0, lambda n=label, s=step: self._set_setup_state(
                "checking", f"({s}/{total}) {n}"))
            try:
                if check_type == "cli":
                    ok = _find_cli_bin(target)
                elif check_type == "launcher_file":
                    ok = _file_exists(APP_ROOT, target)
                elif check_type == "repo_file":
                    ok = _file_exists(self.project, target)
                else:
                    ok = True
            except Exception:
                ok = False
            if not ok:
                missing_hard.append((label, hint))

        # ── 2. Soft warnings 점검 ──
        warns: list[str] = []
        for label, check_type, target in _SOFT_WARNINGS:
            step += 1
            self._msg(f"⚙ 점검 ({step}/{total}) {label}...")
            try:
                if check_type == "launcher_file":
                    ok = _file_exists(APP_ROOT, target)
                elif check_type == "repo_file":
                    ok = _file_exists(self.project, target)
                else:
                    ok = True
            except Exception:
                ok = True
            if not ok:
                warns.append(label)

        # ── 3. Missing guide 파일 승인 생성 (2순위) ──
        missing_guides = _check_missing_guides(self.project)
        if missing_guides:
            guide_list = ", ".join(missing_guides)
            if self._ask_yn(
                "Missing Guide Files",
                f"target repo에 다음 guide 파일이 없습니다:\n\n"
                f"  {guide_list}\n\n"
                f"기본 템플릿을 생성할까요?\n(기존 파일은 덮어쓰지 않습니다)",
                icon="question",
            ):
                created: list[str] = []
                failed: list[str] = []
                for name, content in _GUIDE_TEMPLATES:
                    if name in missing_guides:
                        self._msg(f"⚙ 생성 중: {name}...")
                        if _create_guide_file(self.project, name, content):
                            created.append(name)
                        else:
                            failed.append(name)
                if created:
                    self._msg(f"⚙ Guide 생성 완료: {', '.join(created)}")
                if failed:
                    self._msg(f"⚙ Guide 생성 실패: {', '.join(failed)}")
                # AGENTS.md가 hard blocker이므로 재점검
                missing_hard = [(l, h) for l, h in missing_hard if not _file_exists(
                    self.project if l == "AGENTS.md" else APP_ROOT,
                    next((t for la, _, t, _ in _HARD_BLOCKERS if la == l), l))]

        # ── 4. Hard blocker 결과 처리 ──
        installable = [(n, h) for n, h in missing_hard if h]
        non_installable = [(n, h) for n, h in missing_hard if not h]

        if non_installable:
            names = ", ".join(n for n, _ in non_installable)
            self.root.after(0, lambda: self._set_setup_state("missing", names))
            self.root.after(0, lambda: self._unlock_buttons(
                f"⚙ Missing (수동 확인 필요): {names}", is_error=True))
            self.root.after(0, lambda: self._clear_msg_later(10000))
            return

        if not installable:
            # 모든 hard blocker OK
            if warns:
                detail = ", ".join(warns) + " 없음"
                self.root.after(0, lambda: self._set_setup_state("ready_warn", detail))
            else:
                self.root.after(0, lambda: self._set_setup_state("ready"))
            self.root.after(0, lambda: self._unlock_buttons("⚙ Setup ready"))
            self.root.after(0, lambda: self._clear_msg_later())
            return

        # ── 5. 설치 가능한 hard blocker → 설치 제안 ──
        names = ", ".join(n for n, _ in installable)
        self.root.after(0, lambda: self._set_setup_state("missing", names))
        hints = "\n".join(f"  • {n}: {h}" for n, h in installable)
        if not self._ask_yn(
            "Missing Dependencies",
            f"다음 실행 전제가 WSL에 없습니다:\n\n{hints}\n\n설치를 시도할까요?",
        ):
            self.root.after(0, lambda: self._unlock_buttons(
                f"⚙ Setup: missing {names}", is_error=True))
            self.root.after(0, lambda: self._clear_msg_later(8000))
            return

        # ── 6. 설치 진행 ──
        install_failures: list[str] = []
        for i, (name, hint) in enumerate(installable, 1):
            self._msg(f"⚙ 설치 ({i}/{len(installable)}) {name}...")
            code, output = _run(["bash", "-c", hint], timeout=120.0)
            if code != 0:
                install_failures.append(f"{name}: {output[:80]}" if output else name)

        if install_failures:
            fail_text = "\n".join(install_failures)
            def _show_fail() -> None:
                self._set_setup_state("failed", "Install failed")
                messagebox.showerror(
                    "Install Failed",
                    f"설치 실패:\n\n{fail_text}\n\n수동으로 설치한 뒤 Setup/Check를 다시 누르세요.",
                )
                self._unlock_buttons("⚙ Install failed", is_error=True)
                self._clear_msg_later(10000)
            self.root.after(0, _show_fail)
            return

        # ── 7. 설치 성공 ──
        if warns:
            detail = ", ".join(warns) + " 없음"
            self.root.after(0, lambda: self._set_setup_state("ready_warn", detail))
        else:
            self.root.after(0, lambda: self._set_setup_state("ready"))

        if self._ask_yn(
            "Setup Complete",
            "설치가 완료되었습니다.\n지금 파이프라인을 실행하시겠습니까?",
            icon="info",
        ):
            self._msg("▶ 시작 중...")
            self.root.after(0, lambda: self._unlock_buttons(""))
            self._do_start()
        else:
            self.root.after(0, lambda: self._unlock_buttons("⚙ Setup 완료 — Start 준비됨"))
            self.root.after(0, lambda: self._clear_msg_later(8000))

    # ── Start (setup ready일 때만) ──

    def _on_start(self) -> None:
        if self._action_in_progress:
            return
        if self._setup_state not in ("ready", "ready_warn"):
            self._set_toast_style("error")
            self.msg_var.set("Setup이 완료되지 않았습니다. Setup/Check를 먼저 실행하세요.")
            self._clear_msg_later(5000)
            return
        self._lock_buttons("▶ Starting pipeline...")
        threading.Thread(target=self._do_start, daemon=True).start()

    def _do_start(self) -> None:
        try:
            # Pre-check: launcher script 접근 가능 여부
            script = APP_ROOT / "start-pipeline.sh"
            if not script.exists() and not IS_WINDOWS:
                self.root.after(0, lambda: self._unlock_buttons(
                    "▶ Start failed: start-pipeline.sh not found", is_error=True))
                self.root.after(0, lambda: self._clear_msg_later(10000))
                return
            if IS_WINDOWS:
                wsl_script = _windows_to_wsl_mount(script)
                code, _ = _run(["test", "-f", wsl_script], timeout=5.0)
                if code != 0:
                    self.root.after(0, lambda: self._unlock_buttons(
                        f"▶ Start failed: {wsl_script} not accessible from WSL", is_error=True))
                    self.root.after(0, lambda: self._clear_msg_later(10000))
                    return

            self.root.after(0, lambda: self.msg_var.set("▶ Starting pipeline..."))
            pipeline_start(self.project, self._session_name)

            # 최대 15초 대기 — 단계별 진단
            for sec in range(15):
                time.sleep(1)
                if tmux_alive(self._session_name):
                    # tmux OK — watcher도 확인
                    w_alive, w_pid = watcher_alive(self.project)
                    if w_alive:
                        self.root.after(0, lambda: self._unlock_buttons("▶ Pipeline started"))
                        self.root.after(0, lambda: self._clear_msg_later())
                        return
                    if sec >= 10:
                        self.root.after(0, lambda: self._unlock_buttons(
                            f"▶ Start incomplete: tmux session exists but watcher not detected "
                            f"— check .pipeline/logs/experimental/ for errors", is_error=True))
                        self.root.after(0, lambda: self._clear_msg_later(12000))
                        return
                    # watcher 아직 안 뜸 — 조금 더 대기
                    self.root.after(0, lambda s=sec: self.msg_var.set(
                        f"▶ Starting... tmux OK, waiting for watcher ({s+1}s)"))
                    continue
                # tmux도 아직 없음
                if sec >= 5:
                    self.root.after(0, lambda s=sec: self.msg_var.set(
                        f"▶ Starting... waiting for tmux session ({s+1}s)"))

            # 15초 후에도 tmux 없음
            self.root.after(0, lambda: self._unlock_buttons(
                f"▶ Start failed: tmux session '{self._session_name}' not detected after 15s "
                f"— launcher script may have exited with an error", is_error=True))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"▶ Start failed: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later(10000))

    def _on_stop(self) -> None:
        if self._action_in_progress:
            return
        self._lock_buttons("■ Stopping pipeline...")
        threading.Thread(target=self._do_stop, daemon=True).start()

    def _do_stop(self) -> None:
        try:
            msg = pipeline_stop(self.project, self._session_name)
            self.root.after(0, lambda: self._unlock_buttons(f"■ {msg}"))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"■ Stop failed: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later())

    def _on_restart(self) -> None:
        if self._action_in_progress:
            return
        self._lock_buttons("↻ Restarting pipeline...")
        threading.Thread(target=self._do_restart, daemon=True).start()

    def _do_restart(self) -> None:
        try:
            # ── Stop 단계 ──
            self.root.after(0, lambda: self.msg_var.set("↻ Stopping pipeline..."))
            pipeline_stop(self.project, self._session_name)
            # stop 확인 (최대 5초)
            for sec in range(5):
                time.sleep(1)
                if not tmux_alive(self._session_name):
                    break
                self.root.after(0, lambda s=sec: self.msg_var.set(
                    f"↻ Stopping... ({s+2}s)"))
            if tmux_alive(self._session_name):
                self.root.after(0, lambda: self._unlock_buttons(
                    "↻ Restart failed: could not stop existing session", is_error=True))
                self.root.after(0, lambda: self._clear_msg_later(10000))
                return
            self.root.after(0, lambda: self.msg_var.set("↻ Stopped — starting..."))
            time.sleep(1)

            # ── Start 단계 (Start와 동일한 진단) ──
            pipeline_start(self.project, self._session_name)
            for sec in range(15):
                time.sleep(1)
                if tmux_alive(self._session_name):
                    w_alive, w_pid = watcher_alive(self.project)
                    if w_alive:
                        self.root.after(0, lambda: self._unlock_buttons("↻ Pipeline restarted"))
                        self.root.after(0, lambda: self._clear_msg_later())
                        return
                    if sec >= 10:
                        self.root.after(0, lambda: self._unlock_buttons(
                            "↻ Restart incomplete: tmux exists but watcher not detected "
                            "— check .pipeline/logs/experimental/", is_error=True))
                        self.root.after(0, lambda: self._clear_msg_later(12000))
                        return
                    self.root.after(0, lambda s=sec: self.msg_var.set(
                        f"↻ Restarting... tmux OK, waiting for watcher ({s+1}s)"))
                    continue
                if sec >= 5:
                    self.root.after(0, lambda s=sec: self.msg_var.set(
                        f"↻ Restarting... waiting for tmux session ({s+1}s)"))

            self.root.after(0, lambda: self._unlock_buttons(
                f"↻ Restart failed: tmux session '{self._session_name}' not detected after 15s",
                is_error=True))
        except Exception as e:
            self.root.after(0, lambda: self._unlock_buttons(f"↻ Restart failed: {e}", is_error=True))
        self.root.after(0, lambda: self._clear_msg_later(10000))

    def _on_attach(self) -> None:
        if tmux_alive(self._session_name):
            tmux_attach(self._session_name)
            self._set_toast_style("success")
            self.msg_var.set("tmux attach 실행됨")
            self._clear_msg_later()
        else:
            self._set_toast_style("error")
            self.msg_var.set("tmux 세션이 없습니다. 먼저 Start하세요.")
            self._clear_msg_later()

    # ── 실행 ──

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    project = resolve_project_root()
    app = PipelineGUI(project)
    app.run()


if __name__ == "__main__":
    main()
