"""tmux/watcher lifecycle, pipeline start/stop, file helpers."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from .platform import (
    IS_WINDOWS, WSL_DISTRO,
    CREATE_NO_WINDOW, FILE_QUERY_TIMEOUT,
    _wsl_path_str, _windows_to_wsl_mount, _run, _hidden_subprocess_kwargs,
    _normalize_token_runtime_asset_path, _wsl_wrap, resolve_packaged_file, resolve_project_runtime_file,
)
from .project import _session_name_for

DEFAULT_TOKEN_SINCE_DAYS = 7


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
    try:
        script = resolve_project_runtime_file(project, "start-pipeline.sh")
    except FileNotFoundError:
        return "start-pipeline.sh 없음"
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
    try:
        script = resolve_project_runtime_file(project, "stop-pipeline.sh")
    except FileNotFoundError:
        return "stop-pipeline.sh 없음"
    if IS_WINDOWS:
        wsl_script = _windows_to_wsl_mount(script)
        wsl_project = _wsl_path_str(project)
        result = subprocess.run(
            ["wsl.exe", "-d", WSL_DISTRO, "--cd", wsl_project, "--",
             "bash", wsl_script, wsl_project, "--session", sess],
            capture_output=True, timeout=15,
            **_hidden_subprocess_kwargs(),
        )
    else:
        result = subprocess.run(
            ["bash", str(script), str(project), "--session", sess],
            capture_output=True, timeout=15,
        )
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace") if isinstance(result.stderr, bytes) else str(result.stderr or "")
        stdout = (result.stdout or b"").decode("utf-8", errors="replace") if isinstance(result.stdout, bytes) else str(result.stdout or "")
        detail = (stderr.strip() or stdout.strip() or f"exit={result.returncode}").splitlines()[-1]
        raise RuntimeError(f"stop-pipeline.sh failed: {detail}")
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


# ---------------------------------------------------------------------------
# Control-slot parsing (newest-valid-control semantics)
# ---------------------------------------------------------------------------

_CONTROL_SLOTS = {
    "claude_handoff.md": "implement",
    "gemini_request.md": "request_open",
    "gemini_advice.md": "advice_ready",
    "operator_request.md": "needs_operator",
}

_SLOT_LABELS = {
    "claude_handoff.md": "Claude 실행",
    "gemini_request.md": "Gemini 실행",
    "gemini_advice.md": "Codex follow-up",
    "operator_request.md": "operator 대기",
}


def _read_slot_status(path: Path) -> str | None:
    """Return the STATUS value from a control slot file, or None."""
    if IS_WINDOWS:
        code, content = _run(["head", "-5", _wsl_path_str(path)], timeout=FILE_QUERY_TIMEOUT)
        if code != 0:
            return None
        text = content
    else:
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    for line in text.splitlines()[:10]:
        stripped = line.strip()
        if stripped.startswith("STATUS:"):
            return stripped.split(":", 1)[1].strip()
    return None


def parse_control_slots(project: Path) -> dict[str, object]:
    """Parse the four canonical control slots and return active/stale info.

    Returns a dict with:
      - ``active``: ``{"file": str, "status": str, "label": str, "mtime": float}`` or ``None``
      - ``stale``: list of ``{"file": str, "status": str, "label": str, "mtime": float}``
    """
    pipeline_dir = project / ".pipeline"
    entries: list[dict[str, object]] = []

    for filename, expected_status in _CONTROL_SLOTS.items():
        slot_path = pipeline_dir / filename
        if IS_WINDOWS:
            code, stat_out = _run(
                ["stat", "-c", "%Y", _wsl_path_str(slot_path)],
                timeout=FILE_QUERY_TIMEOUT,
            )
            if code != 0:
                continue
            try:
                mtime = float(stat_out.strip())
            except ValueError:
                continue
        else:
            if not slot_path.exists():
                continue
            try:
                mtime = slot_path.stat().st_mtime
            except OSError:
                continue

        status = _read_slot_status(slot_path)
        if status != expected_status:
            continue  # invalid status — not a valid control slot

        entries.append({
            "file": filename,
            "status": status,
            "label": _SLOT_LABELS[filename],
            "mtime": mtime,
        })

    if not entries:
        return {"active": None, "stale": []}

    entries.sort(key=lambda e: e["mtime"], reverse=True)  # type: ignore[arg-type]
    return {"active": entries[0], "stale": entries[1:]}


def format_control_summary(parsed: dict[str, object]) -> tuple[str, str]:
    """Return (active_text, stale_text) for display in the system card."""
    active = parsed.get("active")
    if active is None:
        active_text = "활성 제어: 없음"
    else:
        active_text = f"활성 제어: {active['label']} ({active['file']})"  # type: ignore[index]

    stale_list = parsed.get("stale", [])
    if not stale_list:
        stale_text = ""
    else:
        names = ", ".join(s["file"] for s in stale_list)  # type: ignore[index]
        stale_text = f"비활성: {names}"

    return active_text, stale_text


def token_usage_db_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "usage.db"


def token_collector_pid_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.pid"


def token_collector_log_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.log"


def token_collector_pane_id_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.pane_id"


def token_collector_window_name_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.window_name"


def token_collector_launch_mode_path(project: Path) -> Path:
    return project / ".pipeline" / "usage" / "collector.launch_mode"


def token_collector_alive(project: Path) -> tuple[bool, int | None]:
    pid_path = token_collector_pid_path(project)
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
    if not pid_path.exists():
        return False, None
    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, 0)
        return True, pid
    except (ValueError, OSError):
        return False, None


def token_collector_stop(project: Path) -> str:
    alive, pid = token_collector_alive(project)
    session = _session_name_for(project)
    launch_mode = _read_sidecar_text(token_collector_launch_mode_path(project))
    window_name = _read_sidecar_text(token_collector_window_name_path(project)) or "usage-collector"
    if pid is None:
        _remove_token_collector_metadata(project)
        return "token collector not running"
    if alive:
        if IS_WINDOWS:
            _run(["kill", "-TERM", str(pid)], timeout=5.0)
        else:
            try:
                os.kill(pid, 15)
            except OSError:
                pass
        for _ in range(20):
            time.sleep(0.1)
            still_alive, _ = token_collector_alive(project)
            if not still_alive:
                break
    if launch_mode == "tmux" and tmux_alive(session):
        _run(["tmux", "kill-window", "-t", f"{session}:{window_name}"], timeout=5.0)
    _remove_token_collector_metadata(project)
    return "token collector stopped"


def token_collector_start(project: Path, since_days: int = DEFAULT_TOKEN_SINCE_DAYS) -> str:
    session = _session_name_for(project)
    if tmux_alive(session):
        return _spawn_token_collector_tmux(project, session=session, since_days=since_days)
    return _spawn_token_collector_background(project, since_days=since_days)


def _spawn_token_collector_tmux(project: Path, *, session: str, since_days: int) -> str:
    usage_dir = project / ".pipeline" / "usage"
    usage_dir.mkdir(parents=True, exist_ok=True)
    log_path = token_collector_log_path(project)
    db_path = token_usage_db_path(project)
    script_path = _token_collector_script_path(project)
    _remove_token_collector_metadata(project)
    _run(["tmux", "kill-window", "-t", f"{session}:usage-collector"], timeout=5.0)
    collector_args = [
        "--project-root",
        _wsl_path_str(project) if IS_WINDOWS else str(project),
        "--db-path",
        _wsl_path_str(db_path) if IS_WINDOWS else str(db_path),
        "--poll-interval",
        "3.0",
        "--daemon",
        "--since-days",
        str(int(since_days)),
    ]
    command = (
        _token_collector_wsl_python_shell(script_path, collector_args)
        + f" >> {shlex.quote(_wsl_path_str(log_path) if IS_WINDOWS else str(log_path))} 2>&1"
    )
    code, pane_id = _run(
        [
            "tmux",
            "new-window",
            "-d",
            "-P",
            "-F",
            "#{pane_id}",
            "-t",
            session,
            "-n",
            "usage-collector",
            "-c",
            _wsl_path_str(project) if IS_WINDOWS else str(project),
            command,
        ],
        timeout=8.0,
    )
    if code != 0 or not pane_id:
        raise RuntimeError("token collector tmux window could not be created")
    code, pid_text = _run(["tmux", "display-message", "-p", "-t", pane_id, "#{pane_pid}"], timeout=5.0)
    if code != 0 or not pid_text.strip():
        raise RuntimeError("token collector pane PID could not be resolved")
    _write_token_collector_metadata(
        project,
        pid=pid_text.strip(),
        pane_id=pane_id.strip(),
        window_name="usage-collector",
        launch_mode="tmux",
    )
    alive, _pid = token_collector_alive(project)
    if not alive:
        raise RuntimeError("token collector daemon could not be started")
    return "token collector started"


def _spawn_token_collector_background(project: Path, *, since_days: int) -> str:
    usage_dir = project / ".pipeline" / "usage"
    usage_dir.mkdir(parents=True, exist_ok=True)
    log_path = token_collector_log_path(project)
    db_path = token_usage_db_path(project)
    script_path = _token_collector_script_path(project)
    _remove_token_collector_metadata(project)
    if IS_WINDOWS:
        wsl_project = _wsl_path_str(project)
        usage_dir_wsl = _wsl_path_str(usage_dir)
        log_wsl = _wsl_path_str(log_path)
        pid_wsl = _wsl_path_str(token_collector_pid_path(project))
        db_wsl = _wsl_path_str(db_path)
        collector_args = [
            "--project-root",
            wsl_project,
            "--db-path",
            db_wsl,
            "--poll-interval",
            "3.0",
            "--daemon",
            "--since-days",
            str(int(since_days)),
        ]
        command = (
            f"cd {shlex.quote(wsl_project)} && "
            f"mkdir -p {shlex.quote(usage_dir_wsl)} && "
            f"rm -f {shlex.quote(pid_wsl)} && "
            + _token_collector_wsl_python_shell(
                script_path,
                collector_args,
                daemon=True,
                log_path=log_wsl,
                pid_path=pid_wsl,
            )
        )
        result = subprocess.run(
            _wsl_wrap(["bash", "-lc", command]),
            capture_output=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
            **_hidden_subprocess_kwargs(),
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip() or f"exit {result.returncode}"
            raise RuntimeError(f"token collector background launch failed: {detail}")
        pid_text = _wait_for_sidecar_text(token_collector_pid_path(project))
    else:
        with log_path.open("a", encoding="utf-8") as logf:
            proc = subprocess.Popen(
                [
                    "python3",
                    "-u",
                    str(script_path),
                    "--project-root",
                    str(project),
                    "--db-path",
                    str(db_path),
                    "--poll-interval",
                    "3.0",
                    "--daemon",
                    "--since-days",
                    str(int(since_days)),
                ],
                cwd=str(project),
                stdout=logf,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        pid_text = str(proc.pid)
    if not pid_text.strip():
        detail = _token_collector_start_failure_detail(project) or "PID file was not written"
        raise RuntimeError(f"token collector background process could not be started: {detail}")
    _write_token_collector_metadata(
        project,
        pid=pid_text.strip(),
        pane_id="",
        window_name="",
        launch_mode="background",
    )
    alive = False
    _pid: int | None = None
    for _ in range(20):
        alive, _pid = token_collector_alive(project)
        if alive:
            break
        time.sleep(0.1)
    if not alive:
        detail = _token_collector_start_failure_detail(project)
        raise RuntimeError(
            f"token collector background process could not be started"
            + (f": {detail}" if detail else "")
        )
    return "token collector started"


def run_token_collector_once(
    project: Path,
    db_path: Path,
    *,
    since_days: int | None = None,
    force_rescan: bool = False,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    usage_dir = db_path.parent
    usage_dir.mkdir(parents=True, exist_ok=True)
    script_path = _token_collector_script_path(project)
    cmd = [
        "--project-root",
        _wsl_path_str(project) if IS_WINDOWS else str(project),
        "--db-path",
        _wsl_path_str(db_path) if IS_WINDOWS else str(db_path),
        "--once",
        "--progress",
    ]
    if since_days is not None:
        cmd.extend(["--since-days", str(int(since_days))])
    if force_rescan:
        cmd.append("--force-rescan")
    popen_kwargs: dict[str, object] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "bufsize": 1,
    }
    if IS_WINDOWS:
        popen_kwargs["text"] = True
        popen_kwargs["encoding"] = "utf-8"
        popen_kwargs["errors"] = "replace"
        popen_kwargs.update(_hidden_subprocess_kwargs())
        proc = subprocess.Popen(
            _wsl_wrap(["bash", "-lc", _token_collector_wsl_python_shell(script_path, cmd)]),
            **popen_kwargs,
        )
    else:
        popen_kwargs["text"] = True
        proc = subprocess.Popen(["python3", "-u", script_path, *cmd], cwd=str(project), **popen_kwargs)

    summary: dict[str, object] | None = None
    output_lines: list[str] = []
    assert proc.stdout is not None
    for raw_line in proc.stdout:
        line = raw_line.strip()
        if not line:
            continue
        output_lines.append(line)
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("event") == "progress":
            if progress_callback is not None:
                progress_callback(payload)
            continue
        if isinstance(payload, dict):
            summary = payload
    return_code = proc.wait()
    if return_code != 0 or summary is None:
        detail = output_lines[-1] if output_lines else f"exit={return_code}"
        raise RuntimeError(f"token collector failed: {detail}")
    return summary


def backfill_token_history(
    project: Path,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    db_path = token_usage_db_path(project)
    was_running, summary, restart_warn = _run_token_maintenance_once(
        project,
        db_path,
        progress_callback=progress_callback,
    )
    return _token_maintenance_result("backfill", summary, was_running, restart_warning=restart_warn)


def rebuild_token_db(
    project: Path,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    usage_dir = token_usage_db_path(project).parent
    usage_dir.mkdir(parents=True, exist_ok=True)
    db_path = token_usage_db_path(project)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    temp_db = usage_dir / f"usage.rebuild-{stamp}.db"
    backup_db = usage_dir / f"usage.backup-{stamp}.db"
    summary: dict[str, object] | None = None
    was_running = False
    action_error: Exception | None = None
    restart_error: Exception | None = None
    try:
        was_running, summary, _rw = _run_token_maintenance_once(
            project,
            temp_db,
            progress_callback=progress_callback,
            restart_collector=False,
        )
        if db_path.exists():
            os.replace(db_path, backup_db)
        os.replace(temp_db, db_path)
    except Exception as exc:
        action_error = exc
        try:
            temp_db.unlink(missing_ok=True)
        except OSError:
            pass
    finally:
        try:
            _restart_token_collector(project, progress_callback=progress_callback, summary=summary)
        except Exception as exc:
            restart_error = exc
    _raise_token_maintenance_errors(action_error, restart_error)
    restart_warn = str(restart_error) if restart_error is not None else ""
    return _token_maintenance_result(
        "rebuild",
        summary,
        was_running,
        backup_path=backup_db if backup_db.exists() else "",
        restart_warning=restart_warn,
    )


def _token_maintenance_result(
    action: str,
    summary: dict[str, object] | None,
    collector_was_running: bool,
    *,
    backup_path: Path | str = "",
    restart_warning: str = "",
) -> dict[str, object]:
    result: dict[str, object] = {
        "action": action,
        "summary": dict(summary or {}),
        "backup_path": str(backup_path) if backup_path else "",
        "collector_was_running": collector_was_running,
    }
    if restart_warning:
        result["restart_warning"] = restart_warning
    return result


def _raise_token_maintenance_errors(
    action_error: Exception | None,
    restart_error: Exception | None,
) -> None:
    """Raise if action failed. Collector restart failure alone is demoted to warning."""
    if action_error is not None and restart_error is not None:
        raise RuntimeError(f"{action_error}; collector restart failed: {restart_error}")
    if action_error is not None:
        raise action_error
    # restart_error alone: action succeeded, collector restart is best-effort
    # Don't raise — the caller should still report success with a warning


def _emit_token_progress(
    progress_callback: Callable[[dict[str, object]], None] | None,
    phase: str,
    *,
    progress_percent: int,
    summary: dict[str, object] | None = None,
) -> None:
    if progress_callback is None:
        return
    data = summary or {}
    progress_callback(
        {
            "event": "progress",
            "phase": phase,
            "progress_percent": progress_percent,
            "scanned_files": int(data.get("scanned_files") or 0),
            "parsed_files": int(data.get("parsed_files") or 0),
            "total_files": int(data.get("total_files") or 0),
            "usage_inserted": int(data.get("usage_inserted") or 0),
            "pipeline_inserted": int(data.get("pipeline_inserted") or 0),
            "duplicates": int(data.get("duplicates") or 0),
            "retry_later": int(data.get("retry_later") or 0),
            "elapsed_sec": float(data.get("elapsed_sec") or 0.0),
        }
    )


def _restart_token_collector(
    project: Path,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    summary: dict[str, object] | None = None,
) -> None:
    _emit_token_progress(progress_callback, "starting_collector", progress_percent=100, summary=summary)
    token_collector_start(project, since_days=DEFAULT_TOKEN_SINCE_DAYS)


def _run_token_maintenance_once(
    project: Path,
    db_path: Path,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    restart_collector: bool = True,
) -> tuple[bool, dict[str, object], str]:
    """Returns (was_running, summary, restart_warning)."""
    was_running, _pid = token_collector_alive(project)
    if was_running:
        _emit_token_progress(progress_callback, "stopping_collector", progress_percent=0)
        token_collector_stop(project)
    summary: dict[str, object] | None = None
    action_error: Exception | None = None
    restart_error: Exception | None = None
    try:
        summary = run_token_collector_once(
            project,
            db_path,
            force_rescan=True,
            progress_callback=progress_callback,
        )
    except Exception as exc:
        action_error = exc
    finally:
        if restart_collector:
            try:
                _restart_token_collector(project, progress_callback=progress_callback, summary=summary)
            except Exception as exc:
                restart_error = exc
    _raise_token_maintenance_errors(action_error, restart_error)
    restart_warning = str(restart_error) if restart_error is not None else ""
    return was_running, dict(summary or {}), restart_warning


def _token_collector_script_path(project: Path) -> str:
    script = _normalize_token_runtime_asset_path(
        resolve_project_runtime_file(project, "token_collector.py")
    )
    return _windows_to_wsl_mount(script) if IS_WINDOWS else str(script)


def _token_collector_wsl_candidates(script_path: str) -> list[str]:
    raw = script_path.replace("\\", "/")
    seen: set[str] = set()
    candidates: list[str] = []

    def _add(path: str) -> None:
        path = path.replace("\\", "/")
        while "/_data/_data/" in path:
            path = path.replace("/_data/_data/", "/_data/")
        if path in seen:
            return
        seen.add(path)
        candidates.append(path)

    _add(raw)
    path = PurePosixPath(raw)
    if path.name == "token_collector.py":
        parent = path.parent
        while parent.name == "_data":
            _add(str(parent / path.name))
            parent = parent.parent
            _add(str(parent / path.name))
    return candidates


def _token_collector_wsl_python_shell(
    script_path: str,
    collector_args: list[str],
    *,
    daemon: bool = False,
    log_path: str | None = None,
    pid_path: str | None = None,
) -> str:
    """Build a bash command string that runs token_collector.py.

    Uses the resolved script_path directly instead of multi-candidate probing
    to avoid Windows command-line escaping issues with wsl.exe -- bash -lc.
    """
    quoted_script = shlex.quote(script_path)
    quoted_args = " ".join(shlex.quote(arg) for arg in collector_args)

    # Verify the script exists, then run it
    command = (
        f"if [ ! -f {quoted_script} ]; then "
        f"echo 'token_collector.py not found: '{quoted_script} >&2; exit 127; "
        f"fi; "
    )
    if daemon:
        if not log_path or not pid_path:
            raise ValueError("daemon token collector launch requires log_path and pid_path")
        return (
            command
            + f"nohup python3 -u {quoted_script} {quoted_args} "
            + f">> {shlex.quote(log_path)} 2>&1 < /dev/null & echo $! > {shlex.quote(pid_path)}"
        )
    return command + f"exec python3 -u {quoted_script} {quoted_args}"


def _write_token_collector_metadata(
    project: Path,
    *,
    pid: str,
    pane_id: str,
    window_name: str,
    launch_mode: str,
) -> None:
    _write_sidecar_text(token_collector_pid_path(project), pid)
    _write_sidecar_text(token_collector_pane_id_path(project), pane_id)
    _write_sidecar_text(token_collector_window_name_path(project), window_name)
    _write_sidecar_text(token_collector_launch_mode_path(project), launch_mode)


def _remove_token_collector_metadata(project: Path) -> None:
    for path in (
        token_collector_pid_path(project),
        token_collector_pane_id_path(project),
        token_collector_window_name_path(project),
        token_collector_launch_mode_path(project),
    ):
        _remove_sidecar_file(path)


def _read_sidecar_text(path: Path) -> str:
    if IS_WINDOWS:
        code, output = _run(["cat", _wsl_path_str(path)], timeout=3.0)
        return output.strip() if code == 0 else ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _wait_for_sidecar_text(path: Path, timeout_sec: float = 2.0) -> str:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        content = _read_sidecar_text(path)
        if content.strip():
            return content
        time.sleep(0.1)
    return _read_sidecar_text(path)


def _token_collector_start_failure_detail(project: Path, lines: int = 12) -> str:
    log_path = token_collector_log_path(project)
    if IS_WINDOWS:
        code, output = _run(["tail", "-n", str(lines), _wsl_path_str(log_path)], timeout=3.0)
        if code == 0 and output.strip():
            return output.strip().splitlines()[-1]
        return ""
    if not log_path.exists():
        return ""
    try:
        lines_text = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""
    return lines_text[-1].strip() if lines_text else ""


def _write_sidecar_text(path: Path, value: str) -> None:
    if IS_WINDOWS:
        parent = _wsl_path_str(path.parent)
        target = _wsl_path_str(path)
        command = (
            f"mkdir -p {shlex.quote(parent)} && "
            f"printf %s {shlex.quote(value)} > {shlex.quote(target)}"
        )
        _run(["bash", "-lc", command], timeout=5.0)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _remove_sidecar_file(path: Path) -> None:
    if IS_WINDOWS:
        _run(["rm", "-f", _wsl_path_str(path)], timeout=3.0)
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
