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
from pipeline_runtime.automation_health import derive_automation_health
from pipeline_runtime.control_writers import validate_operator_candidate_status
from pipeline_runtime.lane_catalog import (
    build_agent_profile_payload,
    default_role_bindings,
    physical_lane_order,
)
from pipeline_runtime.schema import parse_control_slots, read_json
from pipeline_runtime.supervisor import RuntimeSupervisor
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


def _status_readiness_snapshot(status: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(status, dict):
        return {}
    watcher = dict(status.get("watcher") or {})
    control = dict(status.get("control") or {})
    active_round = dict(status.get("active_round") or {})
    lanes: list[dict[str, Any]] = []
    for lane in list(status.get("lanes") or []):
        if not isinstance(lane, dict):
            continue
        lanes.append(
            {
                "name": str(lane.get("name") or ""),
                "state": str(lane.get("state") or ""),
                "attachable": bool(lane.get("attachable")),
                "pid": lane.get("pid"),
                "note": str(lane.get("note") or ""),
                "last_event_at": str(lane.get("last_event_at") or ""),
                "last_heartbeat_at": str(lane.get("last_heartbeat_at") or ""),
            }
        )
    return {
        "runtime_state": str(status.get("runtime_state") or ""),
        "automation_health": str(status.get("automation_health") or ""),
        "automation_reason_code": str(status.get("automation_reason_code") or ""),
        "automation_incident_family": str(status.get("automation_incident_family") or ""),
        "automation_next_action": str(status.get("automation_next_action") or ""),
        "watcher": {
            "alive": bool(watcher.get("alive")),
            "pid": watcher.get("pid"),
        },
        "lanes": lanes,
        "control": {
            "active_control_status": str(control.get("active_control_status") or ""),
        },
        "active_round": {
            "state": str(active_round.get("state") or ""),
        },
    }


def _soak_runtime_context(project_root: Path, status: dict[str, Any] | None) -> dict[str, Any]:
    snapshot = dict(status or _read_status(project_root) or {})
    if snapshot:
        snapshot.update(derive_automation_health(snapshot))
    control = dict(snapshot.get("control") or {})
    active_round = dict(snapshot.get("active_round") or {})
    events = _read_events(project_root)[-12:]
    return {
        "current_run_id": str(snapshot.get("current_run_id") or snapshot.get("run_id") or ""),
        "automation_health": str(snapshot.get("automation_health") or ""),
        "automation_reason_code": str(snapshot.get("automation_reason_code") or ""),
        "automation_incident_family": str(snapshot.get("automation_incident_family") or ""),
        "automation_next_action": str(snapshot.get("automation_next_action") or ""),
        "open_control": {
            "active_control_file": str(control.get("active_control_file") or ""),
            "active_control_seq": int(control.get("active_control_seq") or -1),
            "active_control_status": str(control.get("active_control_status") or "none"),
        },
        "active_round": active_round,
        "latest_status": _status_readiness_snapshot(snapshot),
        "recent_events": events,
    }


def _wait_for_runtime_readiness(
    project_root: Path,
    *,
    timeout_sec: float,
    interval_sec: float = 0.5,
) -> tuple[bool, dict[str, Any] | None, float]:
    started_at = time.time()
    deadline = started_at + timeout_sec
    last_status: dict[str, Any] | None = None
    while time.time() < deadline:
        status = _read_status(project_root)
        if isinstance(status, dict):
            last_status = status
            if _status_ready_for_faults(status):
                return True, status, time.time() - started_at
        time.sleep(interval_sec)
    status = _read_status(project_root)
    if isinstance(status, dict):
        last_status = status
    return False, last_status, time.time() - started_at


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


def _report_json_sidecar_path(report_path: Path) -> Path:
    """Return the JSON sidecar path paired with a given markdown report path.
    Uses ``with_suffix(".json")`` so ``/tmp/foo.md`` pairs with ``/tmp/foo.json``
    and suffix-less paths simply gain a ``.json`` suffix. Shared across
    ``fault-check``, ``synthetic-soak``, and plain ``soak`` report writers."""
    return report_path.with_suffix(".json")


def _write_report_json_sidecar(
    json_path: Path,
    *,
    title: str,
    ok: bool,
    summary_fields: dict[str, Any],
    checks: list[dict[str, Any]],
) -> None:
    """Write a machine-readable JSON sidecar whose ``checks`` list mirrors the
    same structured payloads the report writer already builds in memory so
    consumers outside of Python do not have to scrape the markdown report.
    Shared between the three gate reports to keep a single artifact shape."""
    payload = {
        "title": title,
        "ok": bool(ok),
        "summary": dict(summary_fields),
        "checks": list(checks),
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _soak_summary_fields(summary: dict[str, Any], *, base: dict[str, Any]) -> dict[str, Any]:
    """Build a JSON-safe structured summary dict for ``soak``/``synthetic-soak``
    report sidecars. ``base`` carries path-specific keys (e.g. ``project``,
    ``session``, ``workspace_retained``) that the CLI resolves. All other fields
    are sourced from ``run_soak()``'s summary dict so the sidecar shape stays a
    direct projection of the in-memory summary."""
    fields: dict[str, Any] = dict(base)
    fields.update(
        {
            "duration_sec": summary.get("duration_sec"),
            "ready_ok": bool(summary.get("ready_ok")),
            "ready_wait_sec": summary.get("ready_wait_sec"),
            "ready_timeout_sec": summary.get("ready_timeout_sec"),
            "samples": summary.get("samples"),
            "state_counts": dict(summary.get("state_counts") or {}),
            "degraded_counts": dict(summary.get("degraded_counts") or {}),
            "receipt_count": summary.get("receipt_count"),
            "control_change_count": summary.get("control_change_count"),
            "duplicate_dispatch_count": summary.get("duplicate_dispatch_count"),
            "control_mismatch_samples": summary.get("control_mismatch_samples"),
            "control_mismatch_max_streak": summary.get("control_mismatch_max_streak"),
            "receipt_pending_samples": summary.get("receipt_pending_samples"),
            "classification_gate_failures": summary.get("classification_gate_failures"),
            "classification_gate_details": list(summary.get("classification_gate_details") or []),
            "orphan_session": bool(summary.get("orphan_session")),
            "broken_seen": bool(summary.get("broken_seen")),
            "degraded_seen": bool(summary.get("degraded_seen")),
        }
    )
    if summary.get("readiness_snapshot"):
        fields["readiness_snapshot"] = summary.get("readiness_snapshot")
    runtime_context = dict(summary.get("runtime_context") or {})
    if runtime_context:
        fields["runtime_context"] = runtime_context
        fields["incident_family"] = str(runtime_context.get("automation_incident_family") or "")
        fields["automation_health"] = str(runtime_context.get("automation_health") or "")
        fields["automation_reason_code"] = str(runtime_context.get("automation_reason_code") or "")
        fields["automation_next_action"] = str(runtime_context.get("automation_next_action") or "")
        fields["current_run_id"] = str(runtime_context.get("current_run_id") or "")
    return fields


def _default_report_path(project_root: Path, slug: str) -> Path:
    date_prefix = dt.datetime.now().strftime("%Y-%m-%d")
    return project_root / "report" / "pipeline_runtime" / "verification" / f"{date_prefix}-{slug}.md"


def _synthetic_soak_report_slug(duration_sec: float) -> str:
    if duration_sec >= 24 * 60 * 60:
        return "24h-synthetic-soak"
    if duration_sec >= 6 * 60 * 60:
        return "6h-synthetic-soak"
    return "pipeline-runtime-synthetic-soak"


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


_RECEIPT_MANIFEST_PROBE_REASON_PREFIX = "receipt_manifest:job-fault-manifest"
_ACTIVE_AUTH_PROBE_EXPECTED_REASON = "claude_auth_login_required"


def _probe_receipt_manifest_mismatch_degraded_precedence() -> tuple[bool, str, dict[str, Any]]:
    """Synthetic fault probe: a VERIFY_DONE job with a mismatched artifact_hash against
    its receipt manifest must surface `runtime_state = DEGRADED` with a
    `receipt_manifest:<job>` entry even when `_runtime_started` is false. Regression
    of the just-fixed boundary would silently fall back to STOPPED."""
    with tempfile.TemporaryDirectory(prefix="projecth-fault-manifest-") as tmp:
        root = Path(tmp)
        _write_active_profile(root)
        pipeline_dir = root / ".pipeline"
        state_dir = pipeline_dir / "state"
        manifest_dir = pipeline_dir / "manifests" / "job-fault-manifest"
        state_dir.mkdir(parents=True, exist_ok=True)
        manifest_dir.mkdir(parents=True, exist_ok=True)
        (pipeline_dir / "claude_handoff.md").write_text(
            "STATUS: implement\nCONTROL_SEQ: 91\n",
            encoding="utf-8",
        )
        (state_dir / "turn_state.json").write_text(
            json.dumps(
                {
                    "state": "VERIFY_ACTIVE",
                    "legacy_state": "CODEX_VERIFY",
                    "entered_at": 1.0,
                    "active_control_file": ".pipeline/claude_handoff.md",
                    "active_control_seq": 91,
                    "active_role": "verify",
                    "active_lane": "Claude",
                    "verify_job_id": "job-fault-manifest",
                }
            ),
            encoding="utf-8",
        )
        manifest_path = manifest_dir / "round-1.verify.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "job_id": "job-fault-manifest",
                    "round": 1,
                    "role": "verify",
                    "artifact_hash": "expected-hash",
                    "created_at": "2026-04-18T00:00:00Z",
                }
            ),
            encoding="utf-8",
        )
        (state_dir / "job-fault-manifest.json").write_text(
            json.dumps(
                {
                    "job_id": "job-fault-manifest",
                    "status": "VERIFY_DONE",
                    "artifact_path": "work/4/18/work-note.md",
                    "artifact_hash": "mismatched-hash",
                    "round": 1,
                    "verify_manifest_path": str(manifest_path),
                    "verify_result": "failed",
                    "updated_at": 100.0,
                    "verify_completed_at": 100.0,
                }
            ),
            encoding="utf-8",
        )
        verify_dir = root / "verify" / "4" / "18"
        verify_dir.mkdir(parents=True, exist_ok=True)
        (verify_dir / "2026-04-18-verify.md").write_text("# verify\n", encoding="utf-8")

        supervisor = RuntimeSupervisor(root, start_runtime=False)
        status = supervisor._write_status()
    runtime_state = str((status or {}).get("runtime_state") or "")
    reasons = list((status or {}).get("degraded_reasons") or [])
    matched_reason = next(
        (reason for reason in reasons if reason.startswith(_RECEIPT_MANIFEST_PROBE_REASON_PREFIX)),
        "",
    )
    ok = runtime_state == "DEGRADED" and bool(matched_reason)
    data: dict[str, Any] = {
        "runtime_state": runtime_state,
        "degraded_reasons": reasons,
        "expected_reason_prefix": _RECEIPT_MANIFEST_PROBE_REASON_PREFIX,
        "matched_reason": matched_reason,
    }
    detail = (
        f"runtime_state={runtime_state}, "
        f"reasons={json.dumps(reasons, ensure_ascii=False)}"
    )
    return ok, detail, data


def _probe_active_lane_auth_failure_degraded_precedence() -> tuple[bool, str, dict[str, Any]]:
    """Synthetic fault probe for the legacy Claude-implement topology.

    The auth-failure degraded reason currently exercised here is the
    Claude-specific `claude_auth_login_required` lane surface. Keep the
    probe explicit about that legacy role binding so swapped-topology
    synthetic defaults can still be the gate baseline without weakening
    this focused degraded-precedence check.
    """
    from unittest import mock

    with tempfile.TemporaryDirectory(prefix="projecth-fault-auth-") as tmp:
        root = Path(tmp)
        _write_active_profile(
            root,
            role_bindings={"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
        )
        pipeline_dir = root / ".pipeline"
        state_dir = pipeline_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (pipeline_dir / "claude_handoff.md").write_text(
            "STATUS: implement\nCONTROL_SEQ: 88\n",
            encoding="utf-8",
        )
        (state_dir / "turn_state.json").write_text(
            json.dumps(
                {
                    "state": "IMPLEMENT_ACTIVE",
                    "legacy_state": "CLAUDE_ACTIVE",
                    "entered_at": 1.0,
                    "active_control_file": ".pipeline/claude_handoff.md",
                    "active_control_seq": 88,
                    "active_role": "implement",
                    "active_lane": "Claude",
                }
            ),
            encoding="utf-8",
        )
        supervisor = RuntimeSupervisor(root, start_runtime=False)

        def _lane_health(lane_name: str) -> dict[str, object]:
            return {
                "alive": True,
                "pid": 5000,
                "attachable": True,
                "pane_id": f"%{lane_name}",
            }

        def _capture_tail(lane_name: str, lines: int = 60) -> str:
            if lane_name == "Claude":
                return (
                    "API Error: 401\n"
                    '{"error":{"type":"authentication_error","message":"Invalid authentication credentials"}}\n'
                    "Please run /login\n"
                )
            return ""

        with (
            mock.patch.object(supervisor.adapter, "lane_health", side_effect=_lane_health),
            mock.patch.object(supervisor.adapter, "capture_tail", side_effect=_capture_tail),
            mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
        ):
            status = supervisor._write_status()
    runtime_state = str((status or {}).get("runtime_state") or "")
    reasons = list((status or {}).get("degraded_reasons") or [])
    matched_reason = (
        _ACTIVE_AUTH_PROBE_EXPECTED_REASON
        if _ACTIVE_AUTH_PROBE_EXPECTED_REASON in reasons
        else ""
    )
    ok = runtime_state == "DEGRADED" and bool(matched_reason)
    data: dict[str, Any] = {
        "runtime_state": runtime_state,
        "degraded_reasons": reasons,
        "expected_reason": _ACTIVE_AUTH_PROBE_EXPECTED_REASON,
        "matched_reason": matched_reason,
    }
    detail = (
        f"runtime_state={runtime_state}, "
        f"reasons={json.dumps(reasons, ensure_ascii=False)}"
    )
    return ok, detail, data


def run_fault_check(
    project_root: Path,
    *,
    mode: str,
    session: str,
    extra_env: dict[str, str] | None = None,
) -> tuple[bool, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    adapter = TmuxAdapter(project_root, session)

    precedence_ok, precedence_detail, precedence_data = _probe_receipt_manifest_mismatch_degraded_precedence()
    checks.append(
        {
            "name": "receipt manifest mismatch degraded precedence",
            "ok": precedence_ok,
            "detail": precedence_detail,
            "data": precedence_data,
        }
    )
    auth_ok, auth_detail, auth_data = _probe_active_lane_auth_failure_degraded_precedence()
    checks.append(
        {
            "name": "active lane auth failure degraded precedence",
            "ok": auth_ok,
            "detail": auth_detail,
            "data": auth_data,
        }
    )

    try:
        started, detail = _start_runtime(project_root, mode=mode, session=session, extra_env=extra_env)
        checks.append(
            {
                "name": "runtime start",
                "ok": started,
                "detail": detail,
                # Stable machine-readable shape for the lifecycle action so automation
                # does not have to scrape the literal ``started`` / ``stopped`` string.
                "data": {
                    "action": "start",
                    "succeeded": bool(started),
                    "result": detail,
                },
            }
        )
        if not started:
            return False, checks

        ready_ok, status, ready_wait_sec = _wait_for_runtime_readiness(
            project_root,
            timeout_sec=30.0,
        )
        snapshot = _status_readiness_snapshot(status)
        snapshot_lanes = list(snapshot.get("lanes") or [])
        ready_lane_names = [
            str(lane.get("name") or "")
            for lane in snapshot_lanes
            if str(lane.get("state") or "") in {"READY", "WORKING"}
        ]
        ready_data = {
            "wait_sec": round(float(ready_wait_sec), 3),
            "ready": bool(ready_ok),
            "runtime_state": str(snapshot.get("runtime_state") or ""),
            "watcher_alive": bool((snapshot.get("watcher") or {}).get("alive")),
            "active_control_status": str((snapshot.get("control") or {}).get("active_control_status") or ""),
            "ready_lane_names": ready_lane_names,
            "ready_lane_count": len(ready_lane_names),
            "snapshot": snapshot,
        }
        checks.append(
            {
                "name": "status surface ready",
                "ok": ready_ok,
                "detail": (
                    f"wait_sec={ready_wait_sec:.1f}, "
                    + json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
                ),
                "data": ready_data,
            }
        )
        if not ready_ok or not isinstance(status, dict):
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
        degraded_reasons_list = list((degraded or {}).get("degraded_reasons") or [])
        representative_reason = str((degraded or {}).get("degraded_reason") or "")
        secondary_recovery_failures = [
            reason for reason in degraded_reasons_list if reason.endswith("_recovery_failed")
        ]
        # Supervisor contract: bounded session recovery is attempted when the
        # degraded snapshot shows both ``session_missing`` as representative
        # root cause and at least one lane in ``BROKEN`` state. Mirror that
        # decision here so the gate can assert terminal
        # ``session_recovery_completed`` / ``session_recovery_failed`` evidence
        # instead of passing through on the representative reason alone.
        degraded_lanes = list((degraded or {}).get("lanes") or [])
        broken_lane_names = [
            str(lane.get("name") or "")
            for lane in degraded_lanes
            if str(lane.get("state") or "") == "BROKEN"
        ]
        recovery_expected = (
            isinstance(degraded, dict)
            and representative_reason == "session_missing"
            and bool(broken_lane_names)
        )
        recovery_event: dict[str, Any] | None = None
        if recovery_expected:
            recovery_event = _wait_until(
                lambda: next(
                    (
                        event
                        for event in reversed(_read_events(project_root))
                        if str(event.get("event_type") or "")
                        in {"session_recovery_completed", "session_recovery_failed"}
                    ),
                    None,
                ),
                timeout_sec=20.0,
            )
        event_observed = isinstance(recovery_event, dict)
        recovery_payload = dict((recovery_event or {}).get("payload") or {})
        session_recovery_data = {
            "recovery_expected": recovery_expected,
            "broken_lane_names": broken_lane_names,
            "event_observed": event_observed,
            "event_type": str((recovery_event or {}).get("event_type") or ""),
            "attempt": int(recovery_payload.get("attempt") or 0),
            "result": str(recovery_payload.get("result") or ""),
            "error": str(recovery_payload.get("error") or ""),
            "event": dict(recovery_event or {}),
        }
        # Representative degraded_reason must stay on the session-missing root cause
        # even when per-lane ``*_recovery_failed`` entries coexist as secondary
        # evidence. Secondary entries are preserved inside degraded_reasons as-is;
        # their presence is evidence-only and is not required to fail the gate.
        # Additionally, when the supervisor contract expected a bounded session
        # recovery attempt, a terminal ``session_recovery_completed`` or
        # ``session_recovery_failed`` event must be observed — otherwise the gate
        # would mask a regression where the supervisor stops attempting session
        # recovery but still surfaces ``session_missing`` as representative.
        session_loss_ok = (
            isinstance(degraded, dict)
            and representative_reason == "session_missing"
            and (not recovery_expected or event_observed)
        )
        session_loss_data = {
            "runtime_state": str((degraded or {}).get("runtime_state") or ""),
            "representative_reason": representative_reason,
            "degraded_reasons": degraded_reasons_list,
            "secondary_recovery_failures": secondary_recovery_failures,
            "session_recovery": session_recovery_data,
        }
        checks.append(
            {
                "name": "session loss degraded",
                "ok": session_loss_ok,
                # Derive the human-readable detail from the structured ``data`` payload
                # so automation (CI, launcher tooling) can read the same evidence
                # without string scraping.
                "detail": (
                    f"runtime_state={session_loss_data['runtime_state']}, "
                    f"reason={session_loss_data['representative_reason']}, "
                    f"reasons={json.dumps(session_loss_data['degraded_reasons'], ensure_ascii=False)}, "
                    f"secondary_recovery_failures={json.dumps(session_loss_data['secondary_recovery_failures'], ensure_ascii=False)}, "
                    f"session_recovery={json.dumps({k: session_recovery_data[k] for k in ('recovery_expected', 'event_observed', 'event_type', 'attempt', 'result', 'error')}, ensure_ascii=False)}"
                ),
                "data": session_loss_data,
            }
        )
        stop_ok, stop_detail = _stop_runtime(project_root, session=session, extra_env=extra_env)
        checks.append(
            {
                "name": "runtime stop after session loss",
                "ok": stop_ok,
                "detail": stop_detail,
                "data": {
                    "action": "stop",
                    "succeeded": bool(stop_ok),
                    "result": stop_detail,
                },
            }
        )
        time.sleep(1.0)

        started, detail = _start_runtime(project_root, mode=mode, session=session, extra_env=extra_env)
        checks.append(
            {
                "name": "runtime restart",
                "ok": started,
                "detail": detail,
                "data": {
                    "action": "restart",
                    "succeeded": bool(started),
                    "result": detail,
                },
            }
        )
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
        lane_pid_data = {
            "lane": str(lane_name or ""),
            "pid": int(lane_pid or 0),
            "pid_available": bool(lane_pid),
        }
        checks.append(
            {
                "name": "recoverable lane pid observed",
                "ok": lane_pid_data["pid_available"],
                # Detail and data carry the same evidence; automation reads ``data``
                # directly instead of scraping the formatted string.
                "detail": (
                    f"lane={lane_pid_data['lane'] or '-'}, pid={lane_pid_data['pid']}"
                ),
                "data": lane_pid_data,
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
            event_payload = dict((recovery_event or {}).get("payload") or {})
            recovery_data = {
                "event_observed": isinstance(recovery_event, dict),
                "event_type": str((recovery_event or {}).get("event_type") or ""),
                "lane": str(event_payload.get("lane") or ""),
                "attempt": int(event_payload.get("attempt") or 0),
                "result": str(event_payload.get("result") or ""),
                "event": dict(recovery_event or {}),
            }
            checks.append(
                {
                    "name": "lane recovery",
                    "ok": recovery_data["event_observed"],
                    # Preserve the raw event JSON for readability; the same fields
                    # live in ``data`` for automation.
                    "detail": json.dumps(recovery_event or {}, ensure_ascii=False),
                    "data": recovery_data,
                }
            )
        else:
            recovery_data = {
                "event_observed": False,
                "event_type": "",
                "lane": "",
                "attempt": 0,
                "result": "",
                "event": {},
                "reason": "lane_pid_unavailable_before_fault_injection",
            }
            checks.append(
                {
                    "name": "lane recovery",
                    "ok": False,
                    "detail": "lane pid unavailable before fault injection",
                    "data": recovery_data,
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
    ready_timeout_sec: float = 45.0,
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
    latest_status: dict[str, Any] | None = None
    try:
        if not started:
            return False, {
                "start_detail": detail,
                "ready_ok": False,
                "ready_wait_sec": 0.0,
                "ready_timeout_sec": ready_timeout_sec,
                "samples": 0,
                "state_counts": {},
                "degraded_counts": {},
                "degraded_seen": False,
                "broken_seen": False,
                "duration_sec": duration_sec,
                "receipt_count": 0,
                "control_change_count": 0,
                "control_mismatch_samples": 0,
                "control_mismatch_max_streak": 0,
                "receipt_pending_samples": 0,
                "classification_gate_failures": 0,
                "classification_gate_details": [],
                "dispatch_count": 0,
                "duplicate_dispatch_count": 0,
                "orphan_session": False,
                "runtime_context": _soak_runtime_context(project_root, None),
            }
        ready_ok, ready_status, ready_wait_sec = _wait_for_runtime_readiness(
            project_root,
            timeout_sec=ready_timeout_sec,
        )
        latest_status = ready_status if isinstance(ready_status, dict) else None
        readiness_snapshot = _status_readiness_snapshot(ready_status)
        if not ready_ok:
            return False, {
                "start_detail": detail,
                "ready_ok": False,
                "ready_wait_sec": round(ready_wait_sec, 3),
                "ready_timeout_sec": ready_timeout_sec,
                "readiness_snapshot": readiness_snapshot,
                "samples": 0,
                "state_counts": {},
                "degraded_counts": {},
                "degraded_seen": False,
                "broken_seen": False,
                "duration_sec": duration_sec,
                "receipt_count": 0,
                "control_change_count": 0,
                "control_mismatch_samples": 0,
                "control_mismatch_max_streak": 0,
                "receipt_pending_samples": 0,
                "classification_gate_failures": 0,
                "classification_gate_details": [],
                "dispatch_count": 0,
                "duplicate_dispatch_count": 0,
                "orphan_session": False,
                "runtime_context": _soak_runtime_context(project_root, latest_status),
            }
        deadline = time.time() + duration_sec
        while time.time() < deadline:
            status = _read_status(project_root)
            if isinstance(status, dict):
                latest_status = status
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
    runtime_context = _soak_runtime_context(project_root, latest_status)
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
        "ready_ok": True,
        "ready_wait_sec": round(ready_wait_sec, 3),
        "ready_timeout_sec": ready_timeout_sec,
        "readiness_snapshot": readiness_snapshot,
        "receipt_count": receipt_count,
        "control_change_count": len(control_keys),
        "control_mismatch_samples": control_mismatch_samples,
        "control_mismatch_max_streak": control_mismatch_max_streak,
        "receipt_pending_samples": receipt_pending_samples,
        "classification_gate_failures": classification_gate_failures,
        "classification_gate_details": sorted(classification_gate_details),
        "runtime_context": runtime_context,
        **artifact_summary,
    }


def _write_active_profile(
    project_root: Path,
    *,
    role_bindings: dict[str, str] | None = None,
) -> None:
    active_path = project_root / ".pipeline" / "config" / "agent_profile.json"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    bindings = default_role_bindings()
    if isinstance(role_bindings, dict):
        bindings.update(
            {
                key: str(value).strip()
                for key, value in role_bindings.items()
                if key in {"implement", "verify", "advisory"} and str(value).strip()
            }
        )
    payload = build_agent_profile_payload(
        selected_agents=None,
        role_bindings=bindings,
        advisory_enabled=True,
        operator_stop_enabled=True,
        session_arbitration_enabled=True,
        single_agent_mode=False,
        self_verify_allowed=False,
        self_advisory_allowed=False,
    )
    active_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _seed_synthetic_workspace(
    project_root: Path,
    *,
    role_bindings: dict[str, str] | None = None,
) -> Path:
    (project_root / ".pipeline").mkdir(parents=True, exist_ok=True)
    _write_active_profile(project_root, role_bindings=role_bindings)
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
    command_suffixes = {
        "Claude": "--action-delay-sec 0.2",
        "Codex": "--gemini-every 5 --action-delay-sec 5.0",
        "Gemini": "--gemini-every 5 --action-delay-sec 5.0",
    }
    env = {"PIPELINE_RUNTIME_DISABLE_TOKEN_COLLECTOR": "1"}
    for lane_name in physical_lane_order():
        suffix = command_suffixes.get(lane_name, "")
        env[f"PIPELINE_RUNTIME_LANE_COMMAND_{lane_name.upper()}"] = (
            f"{common} --lane {lane_name}{(' ' + suffix) if suffix else ''}"
        )
    return env


def prepare_synthetic_workspace(
    base_root: Path | None = None,
    *,
    role_bindings: dict[str, str] | None = None,
) -> tuple[Path, dict[str, str]]:
    workspace = Path(
        tempfile.mkdtemp(
            prefix="projecth-pipeline-runtime-synthetic-",
            dir=str(base_root) if base_root else None,
        )
    ).resolve()
    _seed_synthetic_workspace(workspace, role_bindings=role_bindings)
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
    soak.add_argument("--ready-timeout-sec", type=float, default=45.0)
    soak.add_argument("--report", default="")

    gate = sub.add_parser("check-operator-classification")
    gate.add_argument("--report", default="")

    synthetic = sub.add_parser("synthetic-soak")
    synthetic.add_argument("--duration-sec", type=float, default=60.0)
    synthetic.add_argument("--sample-interval-sec", type=float, default=2.0)
    synthetic.add_argument("--ready-timeout-sec", type=float, default=45.0)
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
        summary_fields: dict[str, Any] = {
            "source_project": str(project_root),
            "project": str(synthetic_root),
            "session": str(synthetic_session),
            "mode": str(args.mode),
            "workspace_retained": bool(workspace_retained),
            "workspace_cleanup": str(cleanup_mode),
        }
        summary = [f"{key}={value}" for key, value in summary_fields.items()]
        report_title = "Pipeline Runtime fault check"
        report_text = _markdown_report(
            title=report_title,
            summary=summary,
            checks=checks,
        )
        report_path = Path(args.report).resolve() if args.report else _default_report_path(project_root, "pipeline-runtime-live-fault-check")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")
        _write_report_json_sidecar(
            _report_json_sidecar_path(report_path),
            title=report_title,
            ok=bool(ok),
            summary_fields=summary_fields,
            checks=checks,
        )
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
            ready_timeout_sec=float(args.ready_timeout_sec),
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
            f"ready_ok={bool(summary.get('ready_ok'))}",
            f"ready_wait_sec={summary.get('ready_wait_sec')}",
            f"ready_timeout_sec={summary.get('ready_timeout_sec')}",
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
        runtime_context = dict(summary.get("runtime_context") or {})
        if runtime_context:
            lines.extend(
                [
                    f"current_run_id={runtime_context.get('current_run_id') or ''}",
                    f"automation_health={runtime_context.get('automation_health') or ''}",
                    f"automation_reason_code={runtime_context.get('automation_reason_code') or ''}",
                    f"incident_family={runtime_context.get('automation_incident_family') or ''}",
                    f"automation_next_action={runtime_context.get('automation_next_action') or ''}",
                    "open_control="
                    + json.dumps(runtime_context.get("open_control") or {}, ensure_ascii=False, sort_keys=True),
                ]
            )
        if summary.get("readiness_snapshot"):
            lines.append(
                "readiness_snapshot="
                + json.dumps(summary.get("readiness_snapshot") or {}, ensure_ascii=False, sort_keys=True)
            )
        checks = [
            {
                "name": "runtime start",
                "ok": bool(summary.get("start_detail")),
                "detail": str(summary.get("start_detail") or ""),
            },
            {
                "name": "runtime ready barrier",
                "ok": bool(summary.get("ready_ok")),
                "detail": (
                    f"wait_sec={summary.get('ready_wait_sec')}, "
                    f"timeout_sec={summary.get('ready_timeout_sec')}, "
                    + json.dumps(summary.get("readiness_snapshot") or {}, ensure_ascii=False, sort_keys=True)
                ),
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
        synthetic_report_title = "Pipeline Runtime synthetic soak sample"
        report_text = _markdown_report(
            title=synthetic_report_title,
            summary=lines,
            checks=checks,
        )
        report_slug = _synthetic_soak_report_slug(float(args.duration_sec))
        report_path = Path(args.report).resolve() if args.report else _default_report_path(project_root, report_slug)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")
        synthetic_summary_fields = _soak_summary_fields(
            summary,
            base={
                "project": str(synthetic_root),
                "session": str(synthetic_session),
                "mode": str(args.mode),
                "workspace_retained": bool(workspace_retained),
                "workspace_cleanup": str(cleanup_mode),
            },
        )
        _write_report_json_sidecar(
            _report_json_sidecar_path(report_path),
            title=synthetic_report_title,
            ok=bool(ok),
            summary_fields=synthetic_summary_fields,
            checks=checks,
        )
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
        ready_timeout_sec=float(args.ready_timeout_sec),
    )
    lines = [
        f"project={project_root}",
        f"session={session}",
        f"mode={args.mode}",
        f"duration_sec={summary.get('duration_sec')}",
        f"ready_ok={bool(summary.get('ready_ok'))}",
        f"ready_wait_sec={summary.get('ready_wait_sec')}",
        f"ready_timeout_sec={summary.get('ready_timeout_sec')}",
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
    runtime_context = dict(summary.get("runtime_context") or {})
    if runtime_context:
        lines.extend(
            [
                f"current_run_id={runtime_context.get('current_run_id') or ''}",
                f"automation_health={runtime_context.get('automation_health') or ''}",
                f"automation_reason_code={runtime_context.get('automation_reason_code') or ''}",
                f"incident_family={runtime_context.get('automation_incident_family') or ''}",
                f"automation_next_action={runtime_context.get('automation_next_action') or ''}",
                "open_control="
                + json.dumps(runtime_context.get("open_control") or {}, ensure_ascii=False, sort_keys=True),
            ]
        )
    if summary.get("readiness_snapshot"):
        lines.append(
            "readiness_snapshot="
            + json.dumps(summary.get("readiness_snapshot") or {}, ensure_ascii=False, sort_keys=True)
        )
    checks = [
        {
            "name": "runtime start",
            "ok": bool(summary.get("start_detail")),
            "detail": str(summary.get("start_detail") or ""),
        },
        {
            "name": "runtime ready barrier",
            "ok": bool(summary.get("ready_ok")),
            "detail": (
                f"wait_sec={summary.get('ready_wait_sec')}, "
                f"timeout_sec={summary.get('ready_timeout_sec')}, "
                + json.dumps(summary.get("readiness_snapshot") or {}, ensure_ascii=False, sort_keys=True)
            ),
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
    soak_report_title = "Pipeline Runtime soak sample"
    report_text = _markdown_report(
        title=soak_report_title,
        summary=lines,
        checks=checks,
    )
    report_path = Path(args.report).resolve() if args.report else _default_report_path(project_root, "pipeline-runtime-soak-sample")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")
    soak_summary_fields = _soak_summary_fields(
        summary,
        base={
            "project": str(project_root),
            "session": str(session),
            "mode": str(args.mode),
        },
    )
    _write_report_json_sidecar(
        _report_json_sidecar_path(report_path),
        title=soak_report_title,
        ok=bool(ok),
        summary_fields=soak_summary_fields,
        checks=checks,
    )
    sys.stdout.write(report_text)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
