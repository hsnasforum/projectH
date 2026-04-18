from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import time
from collections import deque
from pathlib import Path
from typing import Any

CONTROL_SLOT_STATUSES: dict[str, str] = {
    "claude_handoff.md": "implement",
    "gemini_request.md": "request_open",
    "gemini_advice.md": "advice_ready",
    "operator_request.md": "needs_operator",
}

CONTROL_SLOT_LABELS: dict[str, str] = {
    "claude_handoff.md": "Claude 실행",
    "gemini_request.md": "Gemini 실행",
    "gemini_advice.md": "Codex follow-up",
    "operator_request.md": "operator 대기",
}

RUNTIME_LANE_ORDER = ("Claude", "Codex", "Gemini")
_CONTROL_HEADER_LINE_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]*):\s*(.*?)\s*$")
ROUND_NOTE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")
WORK_PATH_RE = re.compile(r"(work/\d+/\d+/[^\s`]+\.md)")

# `.pipeline/state/` 안에는 watcher/supervisor가 함께 쓰는 공용 상태 파일(`turn_state.json`,
# `autonomy_state.json`)이 루트에 남고, JobState JSON은 전용 하위 디렉터리 `jobs/`를 primary
# 경로로 씁니다. owner boundary는 디렉터리 path 자체로 강제되며, name filter는 migration
# 기간 동안 루트 fallback 해석에만 좁게 남습니다.
#
# - primary job state path : `<state_dir>/jobs/<job_id>.json` (jobs_state_dir 참조)
# - shared state path      : `<state_dir>/turn_state.json`, `<state_dir>/autonomy_state.json`
# - fallback read only     : `<state_dir>/<job_id>.json` (기존 구조 호환을 위한 읽기 전용)
#
# `STATE_DIR_SHARED_FILES`는 fallback read 경로에서 공용 상태 파일을 배제할 때만 쓰고,
# primary `jobs/` 경로는 path 자체로 JobState 전용이므로 별도 name 필터가 필요 없습니다.
STATE_DIR_SHARED_FILES: frozenset[str] = frozenset(
    {"turn_state.json", "autonomy_state.json"}
)

JOB_STATE_DIR_NAME: str = "jobs"


def jobs_state_dir(state_dir: Path) -> Path:
    """Return the primary JobState directory under ``state_dir``.

    Writes and future reads are owned by this path. Root-level JSON under
    ``state_dir`` is preserved only as a migration-window fallback.
    """
    return state_dir / JOB_STATE_DIR_NAME


def iter_job_state_paths(state_dir: Path) -> list[Path]:
    """Yield JobState JSON paths under ``state_dir``, primary first then root fallback.

    - Primary path scan: ``state_dir/jobs/*.json`` (no name filter — path is the owner).
    - Fallback path scan: ``state_dir/*.json`` excluding :data:`STATE_DIR_SHARED_FILES`
      and any stem already seen in the primary scan (so primary writes always win).

    Returns a list so callers can iterate multiple times deterministically.
    """
    paths: list[Path] = []
    seen_stems: set[str] = set()
    primary_dir = jobs_state_dir(state_dir)
    if primary_dir.exists():
        for path in sorted(primary_dir.glob("*.json")):
            if path.is_file():
                paths.append(path)
                seen_stems.add(path.stem)
    if state_dir.exists():
        for path in sorted(state_dir.glob("*.json")):
            if not path.is_file():
                continue
            if path.name in STATE_DIR_SHARED_FILES:
                continue
            if path.stem in seen_stems:
                continue
            paths.append(path)
    return paths


def iso_utc(ts: float | None = None) -> str:
    value = time.time() if ts is None else ts
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def process_starttime_fingerprint(pid: int) -> str:
    """Return a stable per-process-instance fingerprint for ``pid``.

    Both the supervisor's ``current_run.json`` writer and the watcher exporter
    embed this string into the pointer so supervisor restart can refuse to
    inherit a prior ``run_id`` whenever the live watcher is no longer the same
    process instance the pointer was written for.

    Source fallback order:

    1. ``/proc/<pid>/stat`` field 22 (starttime in clock ticks since boot) on
       Linux.
    2. POSIX ``ps -p <pid> -o lstart=`` start-time string, for hosts where
       ``/proc/<pid>/stat`` parsing or read fails but ``ps`` is available.
    3. ``os.stat(f"/proc/{pid}")`` ctime (serialized as ``st_ctime_ns``) as a
       narrow third fallback for the case where ``/proc/<pid>/stat`` is not
       readable/parseable and ``ps -p <pid> -o lstart=`` does not produce a
       usable fingerprint, but ``/proc/<pid>`` itself is still stat-able. This
       does not help hosts where ``/proc`` is entirely unavailable.

    Returns ``""`` when the pid is non-positive or all three sources fail;
    callers must treat that as "do not inherit" rather than as a successful
    match.
    """
    if pid <= 0:
        return ""
    fingerprint = _proc_starttime_fingerprint(pid)
    if fingerprint:
        return fingerprint
    fingerprint = _ps_lstart_fingerprint(pid)
    if fingerprint:
        return fingerprint
    return _proc_ctime_fingerprint(pid)


def _proc_starttime_fingerprint(pid: int) -> str:
    try:
        stat_text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return ""
    end_paren = stat_text.rfind(")")
    if end_paren < 0:
        return ""
    rest = stat_text[end_paren + 1:].split()
    if len(rest) < 20:
        return ""
    return rest[19]


def _ps_lstart_fingerprint(pid: int) -> str:
    try:
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart="],
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if completed.returncode != 0:
        return ""
    return (completed.stdout or "").strip()


def _proc_ctime_fingerprint(pid: int) -> str:
    # Narrow third fallback: when /proc/<pid>/stat parsing/read fails and
    # `ps -p <pid> -o lstart=` also yields "", but /proc/<pid> itself is still
    # stat-able, use its directory inode ctime as a per-process-instance
    # fingerprint. Serialized as ``st_ctime_ns`` so the string stays
    # deterministic per process instance and regresses cleanly. Hosts where
    # /proc is not mounted at all still safe-degrade to "" here.
    try:
        stat_result = os.stat(f"/proc/{pid}")
    except OSError:
        return ""
    return str(stat_result.st_ctime_ns)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def read_jsonl_tail(path: Path, *, max_lines: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as handle:
            raw_lines = list(deque(handle, maxlen=max_lines))
    except OSError:
        return []
    records: list[dict[str, Any]] = []
    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            records.append(data)
    return records


def parse_iso_utc(value: str | None) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def repo_relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def latest_markdown(directory: Path) -> tuple[str, float]:
    best_path: Path | None = None
    best_mtime = 0.0
    if not directory.exists():
        return "—", 0.0
    for candidate in directory.rglob("*.md"):
        try:
            mtime = candidate.stat().st_mtime
        except OSError:
            continue
        if mtime > best_mtime:
            best_path = candidate
            best_mtime = mtime
    if best_path is None:
        return "—", 0.0
    try:
        rel = str(best_path.relative_to(directory))
    except ValueError:
        rel = best_path.name
    return rel, best_mtime


def latest_round_markdown(directory: Path) -> tuple[str, float]:
    best_path: Path | None = None
    best_mtime = 0.0
    if not directory.exists():
        return "—", 0.0
    for candidate in directory.rglob("*.md"):
        try:
            rel = candidate.relative_to(directory)
        except ValueError:
            continue
        if len(rel.parts) < 3 or not ROUND_NOTE_NAME_RE.match(candidate.name):
            continue
        try:
            mtime = candidate.stat().st_mtime
        except OSError:
            continue
        if mtime > best_mtime:
            best_path = candidate
            best_mtime = mtime
    if best_path is None:
        return "—", 0.0
    return str(best_path.relative_to(directory)), best_mtime


def normalize_repo_artifact_path(value: str | Path | None, repo_root: Path) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    path = Path(text)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(repo_root.resolve())
        except ValueError:
            return ""
        text = str(path)
    return text.replace("\\", "/")


def same_day_verify_dir_for_work(work_root: Path, verify_root: Path, work_path: Path) -> Path:
    try:
        rel = work_path.relative_to(work_root)
    except ValueError:
        return verify_root
    if len(rel.parts) >= 2:
        return verify_root / rel.parts[0] / rel.parts[1]
    return verify_root


def _canonical_round_note_min_depth(root: Path, *, work_root: Path, verify_root: Path) -> int:
    min_depth = 3
    for base in (work_root, verify_root):
        try:
            base_rel = root.relative_to(base)
        except ValueError:
            continue
        min_depth = max(1, 3 - len(base_rel.parts))
        break
    return min_depth


def is_canonical_round_note(root: Path, path: Path, *, work_root: Path, verify_root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    if len(rel.parts) < _canonical_round_note_min_depth(root, work_root=work_root, verify_root=verify_root):
        return False
    return bool(ROUND_NOTE_NAME_RE.match(path.name))


def note_referenced_work_paths(note_path: Path, *, repo_root: Path) -> set[str]:
    if not note_path.exists():
        return set()
    try:
        text = note_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    return {
        normalized
        for normalized in (
            normalize_repo_artifact_path(match.group(1), repo_root)
            for match in WORK_PATH_RE.finditer(text)
        )
        if normalized
    }


def latest_verify_note_for_work(
    work_root: Path,
    verify_root: Path,
    work_path: Path,
    *,
    repo_root: Path,
) -> Path | None:
    normalized_work = normalize_repo_artifact_path(work_path, repo_root)
    if not normalized_work:
        return None
    verify_dir = same_day_verify_dir_for_work(work_root, verify_root, work_path)
    if not verify_dir.exists():
        return None

    latest_any: Path | None = None
    latest_any_mtime = 0.0
    latest_referenced: Path | None = None
    latest_referenced_mtime = 0.0
    candidate_count = 0
    latest_any_refs: set[str] = set()
    for md in verify_dir.rglob("*.md"):
        if not is_canonical_round_note(verify_dir, md, work_root=work_root, verify_root=verify_root):
            continue
        try:
            mtime = md.stat().st_mtime
        except OSError:
            continue
        candidate_count += 1
        refs = note_referenced_work_paths(md, repo_root=repo_root)
        if mtime >= latest_any_mtime:
            latest_any = md
            latest_any_mtime = mtime
            latest_any_refs = refs
        if normalized_work not in refs:
            continue
        if mtime >= latest_referenced_mtime:
            latest_referenced = md
            latest_referenced_mtime = mtime

    if latest_referenced is not None:
        return latest_referenced
    if candidate_count == 1 and not latest_any_refs:
        return latest_any
    return None


def read_control_meta(path: Path, *, max_lines: int = 20) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    meta: dict[str, Any] = {}
    for line in text.splitlines()[:max_lines]:
        match = _CONTROL_HEADER_LINE_RE.match(line)
        if not match:
            continue
        key = match.group(1).strip().lower()
        if key in meta:
            continue
        raw_value = match.group(2).strip()
        if key == "control_seq":
            try:
                parsed = int(raw_value)
            except ValueError:
                continue
            meta[key] = parsed if parsed >= 0 else None
            continue
        meta[key] = raw_value
    return meta


def _read_control_header(path: Path) -> tuple[str | None, int | None]:
    meta = read_control_meta(path, max_lines=12)
    status = str(meta.get("status") or "").strip() or None
    control_seq = meta.get("control_seq")
    if not isinstance(control_seq, int) or control_seq < 0:
        control_seq = None
    return status, control_seq


def parse_control_slots(pipeline_dir: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for filename, expected_status in CONTROL_SLOT_STATUSES.items():
        slot_path = pipeline_dir / filename
        if not slot_path.exists():
            continue
        try:
            mtime = slot_path.stat().st_mtime
        except OSError:
            continue
        status, control_seq = _read_control_header(slot_path)
        if status != expected_status:
            continue
        entries.append(
            {
                "file": filename,
                "status": status,
                "label": CONTROL_SLOT_LABELS[filename],
                "mtime": mtime,
                "control_seq": control_seq,
            }
        )
    if not entries:
        return {"active": None, "stale": []}
    entries.sort(
        key=lambda entry: (
            entry["control_seq"] is not None,
            entry["control_seq"] if entry["control_seq"] is not None else -1,
            entry["mtime"],
        ),
        reverse=True,
    )
    return {"active": entries[0], "stale": entries[1:]}


def load_job_states(
    state_dir: Path,
    *,
    run_id: str | None = None,
    legacy_not_before: float = 0.0,
) -> list[dict[str, Any]]:
    job_states: list[dict[str, Any]] = []
    if not state_dir.exists():
        return job_states
    for path in iter_job_state_paths(state_dir):
        data = read_json(path)
        if not data:
            continue
        state_run_id = str(data.get("run_id") or "").strip()
        if run_id:
            if state_run_id:
                if state_run_id != run_id:
                    continue
            else:
                try:
                    state_mtime = path.stat().st_mtime
                except OSError:
                    state_mtime = 0.0
                updated_at = float(data.get("updated_at") or 0.0)
                if max(state_mtime, updated_at) < legacy_not_before:
                    continue
        data.setdefault("_path", str(path))
        job_states.append(data)
    return job_states


def latest_receipt(receipts_dir: Path) -> dict[str, Any] | None:
    best_entry: dict[str, Any] | None = None
    best_key: tuple[float, float, str] | None = None
    if not receipts_dir.exists():
        return None
    for path in receipts_dir.glob("*.json"):
        data = read_json(path)
        if not data:
            continue
        closed_at = str(data.get("closed_at") or "")
        try:
            closed_ts = dt.datetime.fromisoformat(closed_at.replace("Z", "+00:00")).timestamp() if closed_at else 0.0
        except ValueError:
            closed_ts = 0.0
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        key = (closed_ts, mtime, path.name)
        if best_key is None or key > best_key:
            best_key = key
            best_entry = data
    return best_entry
