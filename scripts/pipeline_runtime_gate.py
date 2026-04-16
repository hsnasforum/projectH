#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import signal
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline_gui.project import _session_name_for
from pipeline_runtime.control_writers import validate_operator_candidate_status
from pipeline_runtime.schema import parse_control_slots, read_json
from pipeline_runtime.tmux_adapter import TmuxAdapter

_CLASSIFICATION_FALLBACK_EVENT = "classification_fallback_detected"


def _project_root(value: str | None) -> Path:
    return Path(value).resolve() if value else Path.cwd().resolve()


def _status_path(project_root: Path) -> Path | None:
    current_run = read_json(project_root / ".pipeline" / "current_run.json")
    if not isinstance(current_run, dict):
        return None
    status_rel = str(current_run.get("status_path") or "").strip()
    if not status_rel:
        return None
    return project_root / status_rel


def _events_path(project_root: Path) -> Path | None:
    current_run = read_json(project_root / ".pipeline" / "current_run.json")
    if not isinstance(current_run, dict):
        return None
    events_rel = str(current_run.get("events_path") or "").strip()
    if not events_rel:
        return None
    return project_root / events_rel


def _read_status(project_root: Path) -> dict[str, Any] | None:
    path = _status_path(project_root)
    if path is None:
        return None
    data = read_json(path)
    return data if isinstance(data, dict) else None


def _read_events(project_root: Path) -> list[dict[str, Any]]:
    path = _events_path(project_root)
    if path is None or not path.exists():
        return []
    events: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return events
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            events.append(data)
    return events


def _operator_classification_gate_detail(status: dict[str, Any] | None) -> str:
    if not isinstance(status, dict):
        return ""
    try:
        validate_operator_candidate_status(status)
    except ValueError as exc:
        return f"{_CLASSIFICATION_FALLBACK_EVENT}: {exc}"
    return ""


def run_operator_classification_gate(project_root: Path) -> tuple[bool, str]:
    status = _read_status(project_root)
    detail = _operator_classification_gate_detail(status)
    if detail:
        return False, detail
    return True, "structured operator classification_source OK"


def _runtime_env(extra_env: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    py_parts: list[str] = [str(REPO_ROOT)]
    existing = str(env.get("PYTHONPATH") or "").strip()
    if existing:
        py_parts.append(existing)
    env["PYTHONPATH"] = ":".join(dict.fromkeys(part for part in py_parts if part))
    if extra_env:
        env.update(extra_env)
    return env


def _run_runtime_cli(
    project_root: Path,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pipeline_runtime.cli", *args, str(project_root)],
        cwd=str(project_root),
        env=_runtime_env(extra_env),
        capture_output=True,
        text=True,
        timeout=120.0,
    )


def _start_runtime(
    project_root: Path,
    *,
    mode: str,
    session: str,
    extra_env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    cmd = [
        sys.executable,
        "-m",
        "pipeline_runtime.cli",
        "start",
        str(project_root),
        "--mode",
        mode,
        "--session",
        session,
        "--no-attach",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        env=_runtime_env(extra_env),
        capture_output=True,
        text=True,
        timeout=120.0,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit {result.returncode}"
        return False, detail
    return True, (result.stdout or result.stderr or "started").strip()


def _stop_runtime(
    project_root: Path,
    *,
    session: str,
    extra_env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    cmd = [
        sys.executable,
        "-m",
        "pipeline_runtime.cli",
        "stop",
        str(project_root),
        "--session",
        session,
    ]
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        env=_runtime_env(extra_env),
        capture_output=True,
        text=True,
        timeout=120.0,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit {result.returncode}"
        return False, detail
    return True, (result.stdout or result.stderr or "stopped").strip()


def _wait_until(
    predicate,
    *,
    timeout_sec: float,
    interval_sec: float = 0.5,
):
    deadline = time.time() + timeout_sec
    last_value = None
    while time.time() < deadline:
        last_value = predicate()
        if last_value:
            return last_value
        time.sleep(interval_sec)
    return predicate() or last_value


def _kill_pid(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return


def _wrapper_pid(project_root: Path, lane_name: str) -> int | None:
    status_path = _status_path(project_root)
    if status_path is None:
        return None
    wrapper_path = status_path.parent / "wrapper-events" / f"{lane_name.strip().lower()}.jsonl"
    if not wrapper_path.exists():
        return None
    for raw in reversed(wrapper_path.read_text(encoding="utf-8").splitlines()):
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        event_payload = dict(payload.get("payload") or {})
        pid = event_payload.get("pid")
        if isinstance(pid, int) or str(pid).isdigit():
            return int(pid)
    return None


def _pick_fault_lane(project_root: Path, status: dict[str, Any]) -> tuple[str, int | None]:
    for lane in list(status.get("lanes") or []):
        name = str(lane.get("name") or "")
        state = str(lane.get("state") or "")
        pid = _wrapper_pid(project_root, name)
        if name and state not in {"OFF"} and pid:
            return name, pid
    return "", None


def _status_ready_for_faults(status: dict[str, Any] | None) -> bool:
    if not isinstance(status, dict):
        return False
    if str(status.get("runtime_state") or "") not in {"RUNNING", "DEGRADED"}:
        return False
    for lane in list(status.get("lanes") or []):
        if bool(lane.get("attachable")) and str(lane.get("state") or "") in {"READY", "WORKING"}:
            return True
    return False


def _markdown_report(
    *,
    title: str,
    summary: list[str],
    checks: list[dict[str, Any]],
) -> str:
    lines = [f"# {title}", "", "## 요약"]
    lines.extend(f"- {line}" for line in summary)
    lines.extend(["", "## 체크 결과"])
    for check in checks:
        status = "PASS" if check.get("ok") else "FAIL"
        lines.append(f"- `{status}` {check.get('name')}")
        detail = str(check.get("detail") or "").strip()
        if detail:
            lines.append(f"  - {detail}")
    return "\n".join(lines) + "\n"


def _default_report_path(project_root: Path, slug: str) -> Path:
    date_prefix = dt.datetime.now().strftime("%Y-%m-%d")
    return project_root / "report" / "pipeline_runtime" / "verification" / f"{date_prefix}-{slug}.md"


def _schedule_workspace_cleanup(workspace: Path) -> tuple[bool, str]:
    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import shutil, sys; "
                    "shutil.rmtree(sys.argv[1], ignore_errors=True)"
                ),
                str(workspace),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        return False, f"background_delete_failed:{type(exc).__name__}"
    return True, f"background_delete_requested(pid={proc.pid})"


def _finalize_synthetic_workspace(*, workspace: Path, keep_workspace: bool, ok: bool) -> tuple[bool, str]:
    if keep_workspace:
        return True, "retained_by_flag"
    if not ok:
        return True, "retained_for_failure"
    cleanup_ok, cleanup_detail = _schedule_workspace_cleanup(workspace)
    return (not cleanup_ok), cleanup_detail


def _current_run_metadata(project_root: Path) -> dict[str, Any]:
    current_run = read_json(project_root / ".pipeline" / "current_run.json")
    return current_run if isinstance(current_run, dict) else {}


def _dispatch_log_path(project_root: Path) -> Path:
    return project_root / ".pipeline" / "logs" / "experimental" / "dispatch.jsonl"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return records
    for raw in lines:
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


def _analyze_run_artifacts(project_root: Path, session: str) -> dict[str, Any]:
    dispatch_records = _read_jsonl(_dispatch_log_path(project_root))
    dispatch_keys = [str(item.get("key") or "") for item in dispatch_records if str(item.get("key") or "")]
    duplicate_dispatch_count = max(0, len(dispatch_keys) - len(set(dispatch_keys)))
    adapter = TmuxAdapter(project_root, session)
    return {
        "dispatch_count": len(dispatch_keys),
        "duplicate_dispatch_count": duplicate_dispatch_count,
        "orphan_session": adapter.session_exists(),
    }


def run_fault_check(
    project_root: Path,
    *,
    mode: str,
    session: str,
    extra_env: dict[str, str] | None = None,
) -> tuple[bool, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    adapter = TmuxAdapter(project_root, session)

    try:
        started, detail = _start_runtime(project_root, mode=mode, session=session, extra_env=extra_env)
        checks.append({"name": "runtime start", "ok": started, "detail": detail})
        if not started:
            return False, checks

        status = _wait_until(
            lambda: (
                payload
                if _status_ready_for_faults(payload := _read_status(project_root))
                else None
            ),
            timeout_sec=30.0,
        )
        checks.append(
            {
                "name": "status surface ready",
                "ok": isinstance(status, dict),
                "detail": f"runtime_state={str((status or {}).get('runtime_state') or '')}",
            }
        )
        if not isinstance(status, dict):
            return False, checks

        adapter.kill_session()
        degraded = _wait_until(
            lambda: (
                (payload := _read_status(project_root))
                and str(payload.get("runtime_state") or "") == "DEGRADED"
                and "session_missing" in list(payload.get("degraded_reasons") or [])
                and payload
            ),
            timeout_sec=20.0,
        )
        checks.append(
            {
                "name": "session loss degraded",
                "ok": isinstance(degraded, dict),
                "detail": (
                    f"runtime_state={str((degraded or {}).get('runtime_state') or '')}, "
                    f"reason={str((degraded or {}).get('degraded_reason') or '')}, "
                    f"reasons={json.dumps(list((degraded or {}).get('degraded_reasons') or []), ensure_ascii=False)}"
                ),
            }
        )
        stop_ok, stop_detail = _stop_runtime(project_root, session=session, extra_env=extra_env)
        checks.append({"name": "runtime stop after session loss", "ok": stop_ok, "detail": stop_detail})
        time.sleep(1.0)

        started, detail = _start_runtime(project_root, mode=mode, session=session, extra_env=extra_env)
        checks.append({"name": "runtime restart", "ok": started, "detail": detail})
        if not started:
            return False, checks

        live_status = _wait_until(
            lambda: (
                (payload := _read_status(project_root))
                if isinstance(payload := _read_status(project_root), dict)
                and _pick_fault_lane(project_root, payload)[1]
                else None
            ),
            timeout_sec=30.0,
        )
        lane_name, lane_pid = _pick_fault_lane(project_root, live_status or {})
        checks.append(
            {
                "name": "recoverable lane pid observed",
                "ok": bool(lane_pid),
                "detail": f"lane={lane_name or '-'}, pid={lane_pid or 0}",
            }
        )
        if lane_pid:
            _kill_pid(lane_pid)
            recovery_event = _wait_until(
                lambda: next(
                    (
                        event
                        for event in reversed(_read_events(project_root))
                        if str(event.get("event_type") or "") == "recovery_completed"
                        and str((event.get("payload") or {}).get("lane") or "") == lane_name
                    ),
                    None,
                ),
                timeout_sec=30.0,
            )
            checks.append(
                {
                    "name": "lane recovery",
                    "ok": isinstance(recovery_event, dict),
                    "detail": json.dumps(recovery_event or {}, ensure_ascii=False),
                }
            )
        else:
            checks.append(
                {
                    "name": "lane recovery",
                    "ok": False,
                    "detail": "lane pid unavailable before fault injection",
                }
            )
    finally:
        _stop_runtime(project_root, session=session, extra_env=extra_env)

    return all(bool(item.get("ok")) for item in checks), checks


def run_soak(
    project_root: Path,
    *,
    mode: str,
    session: str,
    duration_sec: float,
    sample_interval_sec: float,
    extra_env: dict[str, str] | None = None,
    min_receipts: int = 0,
) -> tuple[bool, dict[str, Any]]:
    started, detail = _start_runtime(project_root, mode=mode, session=session, extra_env=extra_env)
    state_counts: dict[str, int] = {}
    degraded_counts: dict[str, int] = {}
    receipt_ids: set[str] = set()
    control_keys: set[str] = set()
    samples = 0
    broken_seen = False
    control_mismatch_samples = 0
    control_mismatch_streak = 0
    control_mismatch_max_streak = 0
    receipt_pending_samples = 0
    classification_gate_failures = 0
    classification_gate_details: set[str] = set()
    try:
        if not started:
            return False, {"start_detail": detail, "samples": 0, "state_counts": {}, "degraded_counts": {}}
        deadline = time.time() + duration_sec
        while time.time() < deadline:
            status = _read_status(project_root)
            if isinstance(status, dict):
                samples += 1
                gate_detail = _operator_classification_gate_detail(status)
                if gate_detail:
                    classification_gate_failures += 1
                    classification_gate_details.add(gate_detail)
                runtime_state = str(status.get("runtime_state") or "unknown")
                degraded_reason = str(status.get("degraded_reason") or "")
                state_counts[runtime_state] = state_counts.get(runtime_state, 0) + 1
                if degraded_reason:
                    degraded_counts[degraded_reason] = degraded_counts.get(degraded_reason, 0) + 1
                if runtime_state == "BROKEN":
                    broken_seen = True
                receipt_id = str(status.get("last_receipt_id") or "").strip()
                if receipt_id:
                    receipt_ids.add(receipt_id)
                control = dict(status.get("control") or {})
                control_file = str(control.get("active_control_file") or "").strip()
                control_seq = int(control.get("active_control_seq") or -1)
                control_status = str(control.get("active_control_status") or "").strip()
                if control_file or control_seq >= 0 or control_status:
                    control_keys.add(f"{control_file}|{control_seq}|{control_status}")
                slot_state = parse_control_slots(project_root / ".pipeline")
                active_slot = dict(slot_state.get("active") or {})
                expected_file = f".pipeline/{active_slot.get('file')}" if active_slot.get("file") else ""
                expected_seq = int(active_slot.get("control_seq") or -1) if active_slot else -1
                expected_status = str(active_slot.get("status") or "none")
                if (control_file, control_seq, control_status) != (expected_file, expected_seq, expected_status):
                    control_mismatch_samples += 1
                    control_mismatch_streak += 1
                    control_mismatch_max_streak = max(control_mismatch_max_streak, control_mismatch_streak)
                else:
                    control_mismatch_streak = 0
                active_round = dict(status.get("active_round") or {})
                if str(active_round.get("state") or "") == "RECEIPT_PENDING":
                    receipt_pending_samples += 1
            time.sleep(max(0.5, sample_interval_sec))
    finally:
        _stop_runtime(project_root, session=session, extra_env=extra_env)

    degraded_seen = bool(degraded_counts)
    artifact_summary = _analyze_run_artifacts(project_root, session)
    receipt_count = len(receipt_ids)
    return (
        (not broken_seen)
        and (not degraded_seen)
        and control_mismatch_max_streak <= 1
        and artifact_summary["duplicate_dispatch_count"] == 0
        and not artifact_summary["orphan_session"]
        and receipt_count >= min_receipts
        and classification_gate_failures == 0
    ), {
        "start_detail": detail,
        "samples": samples,
        "state_counts": state_counts,
        "degraded_counts": degraded_counts,
        "degraded_seen": degraded_seen,
        "broken_seen": broken_seen,
        "duration_sec": duration_sec,
        "receipt_count": receipt_count,
        "control_change_count": len(control_keys),
        "control_mismatch_samples": control_mismatch_samples,
        "control_mismatch_max_streak": control_mismatch_max_streak,
        "receipt_pending_samples": receipt_pending_samples,
        "classification_gate_failures": classification_gate_failures,
        "classification_gate_details": sorted(classification_gate_details),
        **artifact_summary,
    }


def _write_active_profile(project_root: Path) -> None:
    active_path = project_root / ".pipeline" / "config" / "agent_profile.json"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "selected_agents": ["Claude", "Codex", "Gemini"],
                "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
                "role_options": {
                    "advisory_enabled": True,
                    "operator_stop_enabled": True,
                    "session_arbitration_enabled": True,
                },
                "mode_flags": {
                    "single_agent_mode": False,
                    "self_verify_allowed": False,
                    "self_advisory_allowed": False,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _seed_synthetic_workspace(project_root: Path) -> Path:
    (project_root / ".pipeline").mkdir(parents=True, exist_ok=True)
    _write_active_profile(project_root)
    (project_root / "work").mkdir(parents=True, exist_ok=True)
    (project_root / "verify").mkdir(parents=True, exist_ok=True)
    (project_root / "report" / "gemini").mkdir(parents=True, exist_ok=True)
    payload_rel = "synthetic_payloads/seed-0001.txt"
    payload_path = project_root / payload_rel
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text("synthetic seed payload\n", encoding="utf-8")
    (project_root / "work" / "README.md").write_text("synthetic workspace work root\n", encoding="utf-8")
    (project_root / "verify" / "README.md").write_text("synthetic workspace verify root\n", encoding="utf-8")
    today = dt.datetime.now()
    month = str(today.month)
    day = str(today.day)
    date_prefix = today.strftime("%Y-%m-%d")
    seed_path = project_root / "work" / month / day / f"{date_prefix}-synthetic-runtime-seed.md"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(
        "## 변경 파일\n"
        f"- {payload_rel}\n\n"
        "## 사용 skill\n"
        "- 없음\n\n"
        "## 변경 이유\n"
        "- supervisor synthetic soak 시작용 seed artifact입니다.\n\n"
        "## 핵심 변경\n"
        "- runtime가 첫 verify round를 열 수 있도록 synthetic work note를 남겼습니다.\n\n"
        "## 검증\n"
        "- synthetic seed created\n\n"
        "## 남은 리스크\n"
        "- synthetic workspace 전용 artifact입니다.\n",
        encoding="utf-8",
    )
    return seed_path


def _synthetic_lane_env() -> dict[str, str]:
    fake_lane = REPO_ROOT / "scripts" / "pipeline_runtime_fake_lane.py"
    python_bin = shlex.quote(sys.executable)
    fake_lane_path = shlex.quote(str(fake_lane))
    common = f"{python_bin} {fake_lane_path} --project-root {{project_root_shlex}}"
    return {
        "PIPELINE_RUNTIME_DISABLE_TOKEN_COLLECTOR": "1",
        "PIPELINE_RUNTIME_LANE_COMMAND_CLAUDE": f"{common} --lane Claude --action-delay-sec 0.2",
        "PIPELINE_RUNTIME_LANE_COMMAND_CODEX": f"{common} --lane Codex --gemini-every 5 --action-delay-sec 5.0",
        "PIPELINE_RUNTIME_LANE_COMMAND_GEMINI": f"{common} --lane Gemini --gemini-every 5 --action-delay-sec 5.0",
    }


def prepare_synthetic_workspace(base_root: Path | None = None) -> tuple[Path, dict[str, str]]:
    workspace = Path(
        tempfile.mkdtemp(
            prefix="projecth-pipeline-runtime-synthetic-",
            dir=str(base_root) if base_root else None,
        )
    ).resolve()
    _seed_synthetic_workspace(workspace)
    return workspace, _synthetic_lane_env()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline_runtime_gate")
    parser.add_argument("--project-root", default="")
    parser.add_argument("--mode", default="experimental")
    parser.add_argument("--session", default="")
    sub = parser.add_subparsers(dest="command", required=True)

    fault = sub.add_parser("fault-check")
    fault.add_argument("--report", default="")
    fault.add_argument("--workspace-root", default="")
    fault.add_argument("--keep-workspace", action="store_true")

    soak = sub.add_parser("soak")
    soak.add_argument("--duration-sec", type=float, default=60.0)
    soak.add_argument("--sample-interval-sec", type=float, default=2.0)
    soak.add_argument("--report", default="")

    gate = sub.add_parser("check-operator-classification")
    gate.add_argument("--report", default="")

    synthetic = sub.add_parser("synthetic-soak")
    synthetic.add_argument("--duration-sec", type=float, default=60.0)
    synthetic.add_argument("--sample-interval-sec", type=float, default=2.0)
    synthetic.add_argument("--report", default="")
    synthetic.add_argument("--workspace-root", default="")
    synthetic.add_argument("--keep-workspace", action="store_true")
    synthetic.add_argument("--min-receipts", type=int, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = _project_root(args.project_root or None)
    session = args.session or _session_name_for(project_root)

    if args.command == "fault-check":
        workspace_root = Path(args.workspace_root).resolve() if str(args.workspace_root or "").strip() else None
        synthetic_root, extra_env = prepare_synthetic_workspace(workspace_root)
        synthetic_session = args.session or _session_name_for(synthetic_root)
        ok, checks = run_fault_check(synthetic_root, mode=args.mode, session=synthetic_session, extra_env=extra_env)
        workspace_retained, cleanup_mode = _finalize_synthetic_workspace(
            workspace=synthetic_root,
            keep_workspace=bool(args.keep_workspace),
            ok=ok,
        )
        summary = [
            f"source_project={project_root}",
            f"project={synthetic_root}",
            f"session={synthetic_session}",
            f"mode={args.mode}",
            f"workspace_retained={workspace_retained}",
            f"workspace_cleanup={cleanup_mode}",
        ]
        report_text = _markdown_report(
            title="Pipeline Runtime fault check",
            summary=summary,
            checks=checks,
        )
        report_path = Path(args.report).resolve() if args.report else _default_report_path(project_root, "pipeline-runtime-live-fault-check")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")
        sys.stdout.write(report_text)
        return 0 if ok else 1

    if args.command == "synthetic-soak":
        workspace_root = Path(args.workspace_root).resolve() if str(args.workspace_root or "").strip() else None
        synthetic_root, extra_env = prepare_synthetic_workspace(workspace_root)
        synthetic_session = args.session or _session_name_for(synthetic_root)
        ok, summary = run_soak(
            synthetic_root,
            mode=args.mode,
            session=synthetic_session,
            duration_sec=float(args.duration_sec),
            sample_interval_sec=float(args.sample_interval_sec),
            extra_env=extra_env,
            min_receipts=max(0, int(args.min_receipts)),
        )
        workspace_retained, cleanup_mode = _finalize_synthetic_workspace(
            workspace=synthetic_root,
            keep_workspace=bool(args.keep_workspace),
            ok=ok,
        )
        lines = [
            f"project={synthetic_root}",
            f"session={synthetic_session}",
            f"mode={args.mode}",
            f"duration_sec={summary.get('duration_sec')}",
            f"samples={summary.get('samples')}",
            f"state_counts={json.dumps(summary.get('state_counts') or {}, ensure_ascii=False, sort_keys=True)}",
            f"degraded_counts={json.dumps(summary.get('degraded_counts') or {}, ensure_ascii=False, sort_keys=True)}",
            f"receipt_count={summary.get('receipt_count')}",
            f"control_change_count={summary.get('control_change_count')}",
            f"duplicate_dispatch_count={summary.get('duplicate_dispatch_count')}",
            f"control_mismatch_samples={summary.get('control_mismatch_samples')}",
            f"control_mismatch_max_streak={summary.get('control_mismatch_max_streak')}",
            f"receipt_pending_samples={summary.get('receipt_pending_samples')}",
            f"classification_gate_failures={summary.get('classification_gate_failures')}",
            "classification_gate_details="
            + json.dumps(summary.get("classification_gate_details") or [], ensure_ascii=False, sort_keys=True),
            f"orphan_session={bool(summary.get('orphan_session'))}",
            f"broken_seen={bool(summary.get('broken_seen'))}",
            f"workspace_retained={workspace_retained}",
            f"workspace_cleanup={cleanup_mode}",
        ]
        checks = [
            {
                "name": "runtime start",
                "ok": bool(summary.get("start_detail")),
                "detail": str(summary.get("start_detail") or ""),
            },
            {
                "name": "synthetic workload produced receipts",
                "ok": int(summary.get("receipt_count") or 0) >= max(0, int(args.min_receipts)),
                "detail": f"receipt_count={summary.get('receipt_count')}",
            },
            {
                "name": "soak completed without BROKEN",
                "ok": not bool(summary.get("broken_seen")),
                "detail": f"broken_seen={bool(summary.get('broken_seen'))}",
            },
            {
                "name": "soak completed without DEGRADED",
                "ok": not bool(summary.get("degraded_seen")),
                "detail": f"degraded_seen={bool(summary.get('degraded_seen'))}",
            },
            {
                "name": "duplicate dispatch stayed at zero",
                "ok": int(summary.get("duplicate_dispatch_count") or 0) == 0,
                "detail": f"duplicate_dispatch_count={summary.get('duplicate_dispatch_count')}",
            },
            {
                "name": "control surface stayed free of persistent mismatch",
                "ok": int(summary.get("control_mismatch_max_streak") or 0) <= 1,
                "detail": (
                    f"control_mismatch_samples={summary.get('control_mismatch_samples')}, "
                    f"max_streak={summary.get('control_mismatch_max_streak')}"
                ),
            },
            {
                "name": "classification_fallback_detected",
                "ok": int(summary.get("classification_gate_failures") or 0) == 0,
                "detail": json.dumps(summary.get("classification_gate_details") or [], ensure_ascii=False),
            },
            {
                "name": "stop left no orphan session",
                "ok": not bool(summary.get("orphan_session")),
                "detail": f"orphan_session={bool(summary.get('orphan_session'))}",
            },
        ]
        report_text = _markdown_report(
            title="Pipeline Runtime synthetic soak sample",
            summary=lines,
            checks=checks,
        )
        report_path = Path(args.report).resolve() if args.report else _default_report_path(project_root, "pipeline-runtime-synthetic-soak")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")
        sys.stdout.write(report_text)
        return 0 if ok else 1

    if args.command == "check-operator-classification":
        ok, detail = run_operator_classification_gate(project_root)
        lines = [
            f"project={project_root}",
            f"session={session}",
            f"result={'ok' if ok else 'failed'}",
            f"detail={detail}",
        ]
        checks = [
            {
                "name": "classification_fallback_detected",
                "ok": ok,
                "detail": detail,
            }
        ]
        report_text = _markdown_report(
            title="Pipeline Runtime operator classification gate",
            summary=lines,
            checks=checks,
        )
        report_path = Path(args.report).resolve() if args.report else None
        if report_path is not None:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_text, encoding="utf-8")
        sys.stdout.write(report_text)
        return 0 if ok else 1

    ok, summary = run_soak(
        project_root,
        mode=args.mode,
        session=session,
        duration_sec=float(args.duration_sec),
        sample_interval_sec=float(args.sample_interval_sec),
    )
    lines = [
        f"project={project_root}",
        f"session={session}",
        f"mode={args.mode}",
        f"duration_sec={summary.get('duration_sec')}",
        f"samples={summary.get('samples')}",
        f"state_counts={json.dumps(summary.get('state_counts') or {}, ensure_ascii=False, sort_keys=True)}",
        f"degraded_counts={json.dumps(summary.get('degraded_counts') or {}, ensure_ascii=False, sort_keys=True)}",
        f"receipt_count={summary.get('receipt_count')}",
        f"control_change_count={summary.get('control_change_count')}",
        f"duplicate_dispatch_count={summary.get('duplicate_dispatch_count')}",
        f"control_mismatch_samples={summary.get('control_mismatch_samples')}",
        f"control_mismatch_max_streak={summary.get('control_mismatch_max_streak')}",
        f"receipt_pending_samples={summary.get('receipt_pending_samples')}",
        f"classification_gate_failures={summary.get('classification_gate_failures')}",
        "classification_gate_details="
        + json.dumps(summary.get("classification_gate_details") or [], ensure_ascii=False, sort_keys=True),
        f"orphan_session={bool(summary.get('orphan_session'))}",
        f"broken_seen={bool(summary.get('broken_seen'))}",
    ]
    checks = [
        {
            "name": "runtime start",
            "ok": bool(summary.get("start_detail")),
            "detail": str(summary.get("start_detail") or ""),
        },
        {
            "name": "soak completed without BROKEN",
            "ok": not bool(summary.get("broken_seen")),
            "detail": f"broken_seen={bool(summary.get('broken_seen'))}",
        },
        {
            "name": "soak completed without DEGRADED",
            "ok": not bool(summary.get("degraded_seen")),
            "detail": f"degraded_seen={bool(summary.get('degraded_seen'))}",
        },
        {
            "name": "duplicate dispatch stayed at zero",
            "ok": int(summary.get("duplicate_dispatch_count") or 0) == 0,
            "detail": f"duplicate_dispatch_count={summary.get('duplicate_dispatch_count')}",
        },
        {
            "name": "control surface stayed free of persistent mismatch",
            "ok": int(summary.get("control_mismatch_max_streak") or 0) <= 1,
            "detail": (
                f"control_mismatch_samples={summary.get('control_mismatch_samples')}, "
                f"max_streak={summary.get('control_mismatch_max_streak')}"
            ),
        },
        {
            "name": "classification_fallback_detected",
            "ok": int(summary.get("classification_gate_failures") or 0) == 0,
            "detail": json.dumps(summary.get("classification_gate_details") or [], ensure_ascii=False),
        },
        {
            "name": "stop left no orphan session",
            "ok": not bool(summary.get("orphan_session")),
            "detail": f"orphan_session={bool(summary.get('orphan_session'))}",
        },
    ]
    report_text = _markdown_report(
        title="Pipeline Runtime soak sample",
        summary=lines,
        checks=checks,
    )
    report_path = Path(args.report).resolve() if args.report else _default_report_path(project_root, "pipeline-runtime-soak-sample")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")
    sys.stdout.write(report_text)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
