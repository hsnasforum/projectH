from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from pipeline_runtime.cli import build_parser
from pipeline_runtime.operator_autonomy import (
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
    OPERATOR_APPROVAL_COMPLETED_REASON,
    SUPPORTED_DECISION_CLASSES,
    classify_operator_candidate,
)
from pipeline_runtime.supervisor import RuntimeSupervisor
from pipeline_runtime.wrapper_events import append_wrapper_event, build_lane_read_models


def _read_proc_starttime_fingerprint(pid: int) -> str:
    # Mirror RuntimeSupervisor._watcher_process_fingerprint so test fixtures
    # can build pointer payloads that match the live process instance.
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


def _write_active_profile(
    root: Path,
    *,
    selected_agents: list[str] | None = None,
    implement: str = "Claude",
    verify: str = "Codex",
    advisory: str = "Gemini",
    advisory_enabled: bool = True,
) -> None:
    active_path = root / ".pipeline" / "config" / "agent_profile.json"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    selected = list(selected_agents or ["Claude", "Codex", "Gemini"])
    active_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "selected_agents": selected,
                "role_bindings": {"implement": implement, "verify": verify, "advisory": advisory},
                "role_options": {
                    "advisory_enabled": advisory_enabled,
                    "operator_stop_enabled": True,
                    "session_arbitration_enabled": advisory_enabled,
                },
                "mode_flags": {
                    "single_agent_mode": len(selected) == 1,
                    "self_verify_allowed": False,
                    "self_advisory_allowed": False,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


class RuntimeSupervisorTest(unittest.TestCase):
    def test_cli_start_parser_accepts_legacy_mode_positionally(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["start", "/tmp/projectH", "baseline", "--no-attach"])
        self.assertEqual(args.project_root, "/tmp/projectH")
        self.assertEqual(args.legacy_mode, "baseline")
        self.assertTrue(args.no_attach)

    def test_build_active_round_skips_autonomy_state_pseudo_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "autonomy_state.json").write_text(
                json.dumps(
                    {
                        "fingerprint": "",
                        "mode": "normal",
                        "block_reason": "",
                        "reason_code": "",
                        "operator_policy": "",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps({"state": "IDLE", "entered_at": 0.0}, ensure_ascii=False),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            from pipeline_runtime.schema import load_job_states

            job_states = load_job_states(state_dir, run_id=supervisor.run_id)
            self.assertEqual(job_states, [])

            active_round = supervisor._build_active_round(job_states, last_receipt=None)
            self.assertIsNone(active_round)

    def test_build_active_round_prefers_live_verify_over_stale_real_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            last_receipt = {
                "job_id": "job-stale-closed",
                "round": 3,
                "artifact_hash": "stale-closed-hash",
            }
            job_states = [
                {
                    "job_id": "job-stale-closed",
                    "status": "VERIFY_DONE",
                    "artifact_path": "work/4/17/stale.md",
                    "artifact_hash": "stale-closed-hash",
                    "round": 3,
                    "updated_at": 999.0,
                    "last_activity_at": 999.0,
                    "verify_completed_at": 900.0,
                },
                {
                    "job_id": "job-live-verify",
                    "status": "VERIFY_PENDING",
                    "artifact_path": "work/4/18/live.md",
                    "artifact_hash": "live-hash",
                    "round": 4,
                    "updated_at": 200.0,
                    "last_activity_at": 200.0,
                },
            ]

            active_round = supervisor._build_active_round(job_states, last_receipt=last_receipt)

            self.assertIsNotNone(active_round)
            self.assertEqual(active_round["job_id"], "job-live-verify")
            self.assertEqual(active_round["round"], 4)
            self.assertEqual(active_round["state"], "VERIFY_PENDING")

    def test_build_active_round_prefers_receipt_pending_over_stale_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            last_receipt = {
                "job_id": "job-closed",
                "round": 1,
                "artifact_hash": "closed-hash",
            }
            job_states = [
                {
                    "job_id": "job-closed",
                    "status": "VERIFY_DONE",
                    "artifact_path": "work/4/17/closed.md",
                    "artifact_hash": "closed-hash",
                    "round": 1,
                    "updated_at": 500.0,
                    "last_activity_at": 500.0,
                    "verify_completed_at": 400.0,
                },
                {
                    "job_id": "job-receipt-pending",
                    "status": "VERIFY_DONE",
                    "artifact_path": "work/4/18/receipt-pending.md",
                    "artifact_hash": "receipt-pending-hash",
                    "round": 2,
                    "updated_at": 100.0,
                    "last_activity_at": 100.0,
                    "verify_completed_at": 100.0,
                },
            ]

            active_round = supervisor._build_active_round(job_states, last_receipt=last_receipt)

            self.assertIsNotNone(active_round)
            self.assertEqual(active_round["job_id"], "job-receipt-pending")
            self.assertEqual(active_round["round"], 2)
            self.assertEqual(active_round["state"], "RECEIPT_PENDING")

    def test_build_artifacts_uses_canonical_round_notes_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            work_readme = root / "work" / "README.md"
            verify_readme = root / "verify" / "README.md"
            work_note = root / "work" / "4" / "16" / "2026-04-16-real-round.md"
            verify_note = root / "verify" / "4" / "16" / "2026-04-16-real-verify.md"
            work_note.parent.mkdir(parents=True, exist_ok=True)
            verify_note.parent.mkdir(parents=True, exist_ok=True)
            work_readme.parent.mkdir(parents=True, exist_ok=True)
            verify_readme.parent.mkdir(parents=True, exist_ok=True)
            work_note.write_text("# work\n", encoding="utf-8")
            verify_note.write_text(
                "Based on `work/4/16/2026-04-16-real-round.md`\n",
                encoding="utf-8",
            )
            work_readme.write_text("# metadata\n", encoding="utf-8")
            verify_readme.write_text("# metadata\n", encoding="utf-8")

            os.utime(work_note, (100.0, 100.0))
            os.utime(verify_note, (200.0, 200.0))
            os.utime(work_readme, (300.0, 300.0))
            os.utime(verify_readme, (400.0, 400.0))

            supervisor = RuntimeSupervisor(root, start_runtime=False)

            artifacts = supervisor._build_artifacts()

            self.assertEqual(artifacts["latest_work"]["path"], "4/16/2026-04-16-real-round.md")
            self.assertEqual(artifacts["latest_verify"]["path"], "4/16/2026-04-16-real-verify.md")

    def test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            work_note = root / "work" / "4" / "18" / "2026-04-18-real-round.md"
            matching_verify = root / "verify" / "4" / "18" / "2026-04-18-real-verify.md"
            unrelated_verify = root / "verify" / "4" / "18" / "2026-04-18-unrelated-verify.md"
            work_note.parent.mkdir(parents=True, exist_ok=True)
            matching_verify.parent.mkdir(parents=True, exist_ok=True)
            work_note.write_text("# work\n", encoding="utf-8")
            matching_verify.write_text(
                "Based on `work/4/18/2026-04-18-real-round.md`\n",
                encoding="utf-8",
            )
            unrelated_verify.write_text(
                "Based on `work/4/18/2026-04-18-other-round.md`\n",
                encoding="utf-8",
            )

            now = time.time()
            os.utime(work_note, (now, now))
            os.utime(matching_verify, (now - 10, now - 10))
            os.utime(unrelated_verify, (now + 10, now + 10))

            supervisor = RuntimeSupervisor(root, start_runtime=False)

            artifacts = supervisor._build_artifacts()

            self.assertEqual(artifacts["latest_work"]["path"], "4/18/2026-04-18-real-round.md")
            self.assertEqual(artifacts["latest_verify"]["path"], "4/18/2026-04-18-real-verify.md")

    def test_build_artifacts_prefers_manifest_feedback_path_over_verify_body_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            work_note = root / "work" / "4" / "20" / "2026-04-20-real-round.md"
            verify_note = root / "verify" / "4" / "20" / "2026-04-20-real-verify.md"
            manifest_dir = root / ".pipeline" / "manifests" / "job-manifest-feedback"
            work_note.parent.mkdir(parents=True, exist_ok=True)
            verify_note.parent.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            work_note.write_text("# work\n", encoding="utf-8")
            verify_note.write_text("# verify without explicit work reference\n", encoding="utf-8")
            manifest_path = manifest_dir / "round-1.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-manifest-feedback",
                        "round": 1,
                        "role": "verify",
                        "artifact_hash": "artifact-manifest-feedback",
                        "feedback_path": "verify/4/20/2026-04-20-real-verify.md",
                        "created_at": "2026-04-20T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )

            now = time.time()
            os.utime(work_note, (now, now))
            os.utime(verify_note, (now - 10, now - 10))

            supervisor = RuntimeSupervisor(root, start_runtime=False)

            artifacts = supervisor._build_artifacts(
                job_states=[
                    {
                        "job_id": "job-manifest-feedback",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/20/2026-04-20-real-round.md",
                        "artifact_hash": "artifact-manifest-feedback",
                        "round": 1,
                        "verify_manifest_path": str(manifest_path),
                        "updated_at": now,
                        "verify_completed_at": now,
                    }
                ]
            )

            self.assertEqual(artifacts["latest_work"]["path"], "4/20/2026-04-20-real-round.md")
            self.assertEqual(artifacts["latest_verify"]["path"], "4/20/2026-04-20-real-verify.md")

    def test_build_artifacts_emits_dispatch_selection_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            work_note = root / "work" / "4" / "20" / "2026-04-20-observable-round.md"
            verify_note = root / "verify" / "4" / "20" / "2026-04-20-observable-verify.md"
            work_note.parent.mkdir(parents=True, exist_ok=True)
            verify_note.parent.mkdir(parents=True, exist_ok=True)
            work_note.write_text("# work\n", encoding="utf-8")
            verify_note.write_text(
                "Based on `work/4/20/2026-04-20-observable-round.md`\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)

            artifacts = supervisor._build_artifacts()

            self.assertEqual(artifacts["latest_work"]["path"], "4/20/2026-04-20-observable-round.md")
            self.assertEqual(artifacts["latest_verify"]["path"], "4/20/2026-04-20-observable-verify.md")

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line
            ]
            dispatch_events = [
                event for event in events if event.get("event_type") == "dispatch_selection"
            ]
            self.assertEqual(len(dispatch_events), 1)
            expected_work_mtime = work_note.stat().st_mtime
            expected_verify_mtime = verify_note.stat().st_mtime
            self.assertEqual(
                dispatch_events[0]["payload"],
                {
                    "latest_work": "4/20/2026-04-20-observable-round.md",
                    "latest_verify": "4/20/2026-04-20-observable-verify.md",
                    "date_key": "2026-04-20",
                    "latest_work_mtime": expected_work_mtime,
                    "latest_verify_date_key": "2026-04-20",
                    "latest_verify_mtime": expected_verify_mtime,
                },
            )
            self.assertEqual(dispatch_events[0]["source"], "supervisor")

    def test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            older_date_note = root / "work" / "4" / "18" / "2026-04-18-older-round.md"
            newer_date_note = root / "work" / "4" / "20" / "2026-04-20-newer-round.md"
            older_date_note.parent.mkdir(parents=True, exist_ok=True)
            newer_date_note.parent.mkdir(parents=True, exist_ok=True)

            supervisor = RuntimeSupervisor(root, start_runtime=False)

            older_date_note.write_text("# older\n", encoding="utf-8")
            first = supervisor._build_artifacts()

            newer_date_note.write_text("# newer\n", encoding="utf-8")
            older_mtime = older_date_note.stat().st_mtime
            spoofed_newer_mtime = older_mtime - 100.0
            os.utime(newer_date_note, (spoofed_newer_mtime, spoofed_newer_mtime))

            second = supervisor._build_artifacts()

            self.assertEqual(first["latest_work"]["path"], "4/18/2026-04-18-older-round.md")
            self.assertEqual(second["latest_work"]["path"], "4/20/2026-04-20-newer-round.md")

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line
            ]
            dispatch_events = [
                event for event in events if event.get("event_type") == "dispatch_selection"
            ]
            date_keys = [
                Path(event["payload"]["latest_work"]).name[:10]
                for event in dispatch_events
                if isinstance(event.get("payload"), dict)
                and isinstance(event["payload"].get("latest_work"), str)
                and event["payload"]["latest_work"] != "—"
            ]

            self.assertEqual(len(dispatch_events), 2)
            self.assertEqual(date_keys, ["2026-04-18", "2026-04-20"])
            self.assertEqual(date_keys, sorted(date_keys))
            for event in dispatch_events:
                payload = event["payload"]
                self.assertEqual(
                    payload["date_key"],
                    Path(payload["latest_work"]).name[:10],
                )
                work_file = root / "work" / payload["latest_work"]
                self.assertAlmostEqual(
                    payload["latest_work_mtime"],
                    work_file.stat().st_mtime,
                    places=3,
                )
                self.assertEqual(payload["latest_verify"], "—")
                self.assertEqual(payload["latest_verify_date_key"], "")
                self.assertEqual(payload["latest_verify_mtime"], 0.0)

    def test_dispatch_selection_payload_key_stability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            work_note = root / "work" / "4" / "20" / "2026-04-20-key-stability-round.md"
            work_note.parent.mkdir(parents=True, exist_ok=True)
            work_note.write_text("# work\n", encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._build_artifacts()

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line
            ]
            dispatch_events = [
                event for event in events if event.get("event_type") == "dispatch_selection"
            ]
            self.assertGreaterEqual(len(dispatch_events), 1)
            payload = dispatch_events[0]["payload"]
            self.assertEqual(len(payload), 6)
            self.assertEqual(
                list(payload),
                [
                    "latest_work",
                    "latest_verify",
                    "date_key",
                    "latest_work_mtime",
                    "latest_verify_date_key",
                    "latest_verify_mtime",
                ],
            )

    def test_write_status_emits_receipt_and_control_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-1"
            verify_dir = root / "verify" / "4" / "11"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 17\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "VERIFY_ACTIVE",
                        "legacy_state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 17,
                        "active_role": "verify",
                        "active_lane": "Claude",
                        "verify_job_id": "job-1",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-2.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-1",
                        "round": 2,
                        "role": "verify",
                        "artifact_hash": "artifact-hash-1",
                        "created_at": "2026-04-11T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-1.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-1",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/11/work-note.md",
                        "artifact_hash": "artifact-hash-1",
                        "round": 2,
                        "verify_manifest_path": str(manifest_path),
                        "verify_result": "passed_by_feedback",
                        "updated_at": 100.0,
                        "verify_completed_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )
            verify_path = verify_dir / "2026-04-11-verify.md"
            verify_path.write_text(
                "Based on `work/4/11/work-note.md`\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["control"]["active_control_file"], ".pipeline/claude_handoff.md")
            self.assertEqual(status["control"]["active_control_seq"], 17)
            self.assertEqual(status["active_round"]["job_id"], "job-1")
            self.assertTrue(status["last_receipt_id"])
            receipt_path = supervisor.receipts_dir / f"{status['last_receipt_id']}.json"
            self.assertTrue(receipt_path.exists())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["job_id"], "job-1")
            self.assertEqual(receipt["control_seq"], 17)
            self.assertEqual(receipt["verify_result"], "passed_by_feedback")

    def test_write_status_receipt_uses_verify_matching_job_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-verify-match"
            verify_dir = root / "verify" / "4" / "18"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 29\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 29,
                        "verify_job_id": "job-verify-match",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-1.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-verify-match",
                        "round": 1,
                        "role": "verify",
                        "artifact_hash": "artifact-match",
                        "created_at": "2026-04-18T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-verify-match.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-verify-match",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/18/2026-04-18-real-round.md",
                        "artifact_hash": "artifact-match",
                        "round": 1,
                        "verify_manifest_path": str(manifest_path),
                        "verify_result": "passed_by_feedback",
                        "updated_at": 100.0,
                        "verify_completed_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )
            matching_verify = verify_dir / "2026-04-18-real-verify.md"
            unrelated_verify = verify_dir / "2026-04-18-unrelated-verify.md"
            matching_verify.write_text(
                "Based on `work/4/18/2026-04-18-real-round.md`\n",
                encoding="utf-8",
            )
            unrelated_verify.write_text(
                "Based on `work/4/18/2026-04-18-other-round.md`\n",
                encoding="utf-8",
            )
            now = time.time()
            os.utime(matching_verify, (now - 10, now - 10))
            os.utime(unrelated_verify, (now, now))

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            receipt_path = supervisor.receipts_dir / f"{status['last_receipt_id']}.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["artifact_path"],
                str(matching_verify),
            )

    def test_write_status_receipt_prefers_manifest_feedback_path_when_verify_body_drifted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-manifest-feedback"
            verify_dir = root / "verify" / "4" / "20"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 41\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "VERIFY_ACTIVE",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 41,
                        "verify_job_id": "job-manifest-feedback",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-1.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-manifest-feedback",
                        "round": 1,
                        "role": "verify",
                        "artifact_hash": "artifact-manifest-feedback",
                        "feedback_path": "verify/4/20/2026-04-20-real-verify.md",
                        "created_at": "2026-04-20T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-manifest-feedback.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-manifest-feedback",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/20/2026-04-20-real-round.md",
                        "artifact_hash": "artifact-manifest-feedback",
                        "round": 1,
                        "verify_manifest_path": str(manifest_path),
                        "verify_result": "passed_by_feedback",
                        "updated_at": 100.0,
                        "verify_completed_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )
            verify_note = verify_dir / "2026-04-20-real-verify.md"
            verify_note.write_text("# verify without explicit work reference\n", encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["degraded_reason"], "")
            self.assertTrue(status["last_receipt_id"])
            receipt_path = supervisor.receipts_dir / f"{status['last_receipt_id']}.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["artifact_path"], str(verify_note))

    def test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-verify-missing"
            verify_dir = root / "verify" / "4" / "18"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 31\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 31,
                        "verify_job_id": "job-verify-missing",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-1.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-verify-missing",
                        "round": 1,
                        "role": "verify",
                        "artifact_hash": "artifact-missing",
                        "created_at": "2026-04-18T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-verify-missing.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-verify-missing",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/18/2026-04-18-real-round.md",
                        "artifact_hash": "artifact-missing",
                        "round": 1,
                        "verify_manifest_path": str(manifest_path),
                        "verify_result": "passed_by_feedback",
                        "updated_at": 100.0,
                        "verify_completed_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )
            (verify_dir / "2026-04-18-unrelated-a.md").write_text("# verify a\n", encoding="utf-8")
            (verify_dir / "2026-04-18-unrelated-b.md").write_text("# verify b\n", encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["degraded_reason"], "receipt_verify_missing:job-verify-missing")
            self.assertFalse(status["last_receipt_id"])

    def test_write_status_clears_live_fields_when_runtime_has_stopped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 17\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 17,
                        "verify_job_id": "job-stop-1",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-stop-1.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-stop-1",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/16/work-note.md",
                        "artifact_hash": "artifact-hash-stop-1",
                        "round": 1,
                        "updated_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            supervisor.enabled_lanes = set()
            supervisor.runtime_lane_configs = []
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "OFF", "attachable": False, "pid": None, "note": "stopped"},
                            {"name": "Codex", "state": "OFF", "attachable": False, "pid": None, "note": "stopped"},
                        ],
                        {"Claude": {}, "Codex": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "STOPPED")
            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["control"]["active_control_seq"], -1)
            self.assertIsNone(status["active_round"])
            self.assertEqual(status["watcher"]["alive"], False)
            self.assertEqual([lane["state"] for lane in status["lanes"]], ["OFF", "OFF"])
            self.assertEqual([lane["pid"] for lane in status["lanes"]], [None, None])
            self.assertEqual([lane["attachable"] for lane in status["lanes"]], [False, False])
            self.assertEqual([lane["note"] for lane in status["lanes"]], ["stopped", "stopped"])

    def test_current_run_pointer_tracks_run_scoped_status_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, run_id="20260415T010203Z-p123", start_runtime=False)

            supervisor._write_current_run_pointer()

            current_run = json.loads((root / ".pipeline" / "current_run.json").read_text(encoding="utf-8"))
            self.assertEqual(current_run["run_id"], "20260415T010203Z-p123")
            self.assertEqual(current_run["status_path"], ".pipeline/runs/20260415T010203Z-p123/status.json")
            self.assertEqual(current_run["events_path"], ".pipeline/runs/20260415T010203Z-p123/events.jsonl")

    def test_write_status_clears_stale_degraded_reason_after_runtime_has_stopped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 18\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 18,
                        "verify_job_id": "job-stop-2",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-stop-2.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-stop-2",
                        "status": "VERIFY_PENDING",
                        "artifact_path": "work/4/17/work-note.md",
                        "artifact_hash": "artifact-hash-stop-2",
                        "round": 2,
                        "updated_at": 120.0,
                        "degraded_reason": "dispatch_stall",
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = False
            supervisor.enabled_lanes = set()
            supervisor.runtime_lane_configs = []
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "OFF", "attachable": False, "pid": None, "note": "stopped"},
                            {"name": "Codex", "state": "OFF", "attachable": False, "pid": None, "note": "stopped"},
                        ],
                        {"Claude": {}, "Codex": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "STOPPED")
            self.assertEqual(status["degraded_reason"], "")
            self.assertEqual(status["degraded_reasons"], [])
            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertIsNone(status["active_round"])

    def test_write_status_force_stopped_surface_clears_receipt_pending_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-stop-final"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 546\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "IMPLEMENT_ACTIVE",
                        "legacy_state": "CLAUDE_ACTIVE",
                        "entered_at": 1.0,
                        "reason": "claude_handoff_updated",
                        "active_control_file": "claude_handoff.md",
                        "active_control_seq": 546,
                        "active_role": "implement",
                        "active_lane": "Codex",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-1.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-stop-final",
                        "round": 1,
                        "role": "verify",
                        "artifact_hash": "artifact-hash-stop-final",
                        "created_at": "2026-04-20T11:43:33Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-stop-final.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-stop-final",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/20/2026-04-20-stop-final.md",
                        "artifact_hash": "artifact-hash-stop-final",
                        "round": 1,
                        "verify_manifest_path": str(manifest_path),
                        "verify_result": "passed_by_feedback",
                        "updated_at": 120.0,
                        "verify_completed_at": 120.0,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = False
            supervisor._force_stopped_surface = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "OFF", "attachable": False, "pid": None, "note": "stopped"},
                            {"name": "Codex", "state": "OFF", "attachable": False, "pid": None, "note": "stopped"},
                            {"name": "Gemini", "state": "OFF", "attachable": False, "pid": None, "note": "stopped"},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "STOPPED")
            self.assertEqual(status["degraded_reason"], "")
            self.assertEqual(status["degraded_reasons"], [])
            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["control"]["active_control_seq"], -1)
            self.assertIsNone(status["active_round"])
            self.assertEqual(status["watcher"], {"alive": False, "pid": None})
            self.assertEqual(status["turn_state"]["state"], "IDLE")
            self.assertEqual(status["turn_state"]["reason"], "runtime_stopped")
            self.assertEqual(status["turn_state"]["active_role"], "")
            self.assertEqual(status["turn_state"]["active_lane"], "")

    def test_force_stopped_surface_overrides_status_to_stopped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            (root / ".pipeline" / "state").mkdir(parents=True, exist_ok=True)

            def write_status(force_stopped_surface: bool) -> dict[str, object]:
                supervisor = RuntimeSupervisor(root, start_runtime=False)
                supervisor._runtime_started = True
                supervisor._force_stopped_surface = force_stopped_surface
                with (
                    mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                    mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                    mock.patch.object(
                        supervisor,
                        "_build_lane_statuses",
                        return_value=(
                            [
                                {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                                {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                                {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                            ],
                            {"Claude": {}, "Codex": {}, "Gemini": {}},
                        ),
                    ),
                    mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                    mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
                ):
                    return supervisor._write_status()

            normal_status = write_status(False)
            forced_status = write_status(True)

            self.assertEqual(normal_status["runtime_state"], "RUNNING")
            self.assertEqual(normal_status["watcher"], {"alive": True, "pid": 4242})
            self.assertEqual(
                [lane["state"] for lane in normal_status["lanes"]],
                ["READY", "READY", "READY"],
            )
            self.assertEqual(forced_status["runtime_state"], "STOPPED")
            self.assertEqual(forced_status["watcher"], {"alive": False, "pid": None})
            self.assertEqual(
                [lane["state"] for lane in forced_status["lanes"]],
                ["OFF", "OFF", "OFF"],
            )

    def test_write_status_activates_codex_task_hint_for_verify_round_without_control_slot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": "",
                        "active_control_seq": -1,
                        "verify_job_id": "job-verify-258",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-verify-258.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-verify-258",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/17/current.md",
                        "artifact_hash": "artifact-hash-258",
                        "round": 1,
                        "updated_at": 100.0,
                        "dispatch_id": "dispatch-258",
                        "dispatch_control_seq": 258,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            codex_hint = json.loads(supervisor._task_hint_path("Codex").read_text(encoding="utf-8"))
            claude_hint = json.loads(supervisor._task_hint_path("Claude").read_text(encoding="utf-8"))
            self.assertTrue(codex_hint["active"])
            self.assertEqual(codex_hint["job_id"], "job-verify-258")
            self.assertEqual(codex_hint["dispatch_id"], "dispatch-258")
            self.assertEqual(codex_hint["control_seq"], 258)
            self.assertFalse(claude_hint["active"])
            self.assertEqual(status["active_round"]["job_id"], "job-verify-258")
            self.assertEqual(status["active_round"]["dispatch_control_seq"], 258)

    def test_write_status_clears_stale_verify_round_from_codex_followup_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "gemini_advice.md").write_text(
                "STATUS: advice_ready\nCONTROL_SEQ: 262\n\nRecommendation:\n- continue with next slice\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_FOLLOWUP",
                        "entered_at": 1.0,
                        "reason": "gemini_advice_updated",
                        "active_control_file": "gemini_advice.md",
                        "active_control_seq": 262,
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-stale-verify.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-stale-verify",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/16/stale.md",
                        "artifact_hash": "artifact-stale",
                        "round": 1,
                        "updated_at": 100.0,
                        "dispatch_id": "dispatch-stale",
                        "dispatch_control_seq": 260,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            codex_hint = json.loads(supervisor._task_hint_path("Codex").read_text(encoding="utf-8"))
            self.assertEqual(status["control"]["active_control_status"], "advice_ready")
            self.assertEqual(status["control"]["active_control_seq"], 262)
            self.assertIsNone(status["active_round"])
            self.assertTrue(codex_hint["active"])
            self.assertEqual(codex_hint["job_id"], "")
            self.assertEqual(codex_hint["dispatch_id"], "")
            self.assertEqual(codex_hint["control_seq"], 262)

    def test_write_task_hints_implement_lane_has_dispatch_fields_when_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root, implement="Codex", verify="Claude")
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            supervisor._write_task_hints(
                active_lane="Codex",
                active_round={"job_id": None, "dispatch_id": None},
                turn_state={"state": "IMPLEMENT_ACTIVE"},
                control={"active_control_status": "implement", "active_control_seq": 42},
            )

            codex_hint = json.loads(supervisor._task_hint_path("Codex").read_text(encoding="utf-8"))
            claude_hint = json.loads(supervisor._task_hint_path("Claude").read_text(encoding="utf-8"))
            gemini_hint = json.loads(supervisor._task_hint_path("Gemini").read_text(encoding="utf-8"))

            self.assertTrue(codex_hint["active"])
            self.assertEqual(codex_hint["control_seq"], 42)
            self.assertEqual(codex_hint["job_id"], "ctrl-42")
            self.assertEqual(codex_hint["dispatch_id"], "seq-42")
            self.assertFalse(claude_hint["active"])
            self.assertEqual(claude_hint["job_id"], "")
            self.assertEqual(claude_hint["dispatch_id"], "")
            self.assertFalse(gemini_hint["active"])
            self.assertEqual(gemini_hint["job_id"], "")
            self.assertEqual(gemini_hint["dispatch_id"], "")

    def test_write_status_clears_stale_autonomy_when_active_round_targets_newer_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 33",
                        "REASON_CODE: slice_ambiguity",
                        "OPERATOR_POLICY: gate_24h",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: choose exact next slice",
                        "BASED_ON_WORK: work/4/17/older.md",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/operator_request.md",
                        "active_control_seq": 33,
                        "verify_job_id": "job-newer-work",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-newer-work.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-newer-work",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/17/newer.md",
                        "artifact_hash": "artifact-newer",
                        "round": 1,
                        "updated_at": 100.0,
                        "dispatch_id": "dispatch-newer",
                        "dispatch_control_seq": 44,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["active_round"]["artifact_path"], "work/4/17/newer.md")
            self.assertEqual(status["autonomy"]["mode"], "normal")
            self.assertEqual(status["autonomy"]["based_on_work"], "")
            self.assertEqual(status["autonomy"]["reason_code"], "")

    def test_write_status_ignores_dispatch_stall_from_non_active_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "job-old.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-old",
                        "status": "VERIFY_PENDING",
                        "artifact_path": "work/4/17/old.md",
                        "artifact_hash": "old-hash",
                        "round": 1,
                        "updated_at": 100.0,
                        "dispatch_stall_detected_at": 100.0,
                        "dispatch_stall_fingerprint": "old-fingerprint",
                        "dispatch_stall_count": 2,
                        "dispatch_stall_stage": "dispatch_seen_missing",
                        "degraded_reason": "dispatch_stall",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-new.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-new",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/17/new.md",
                        "artifact_hash": "new-hash",
                        "round": 2,
                        "updated_at": 200.0,
                        "dispatch_id": "dispatch-new",
                        "dispatch_control_seq": 52,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [{"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""}],
                        {"Codex": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["active_round"]["job_id"], "job-new")
            self.assertEqual(status["degraded_reason"], "")
            self.assertNotIn("dispatch_stall", list(status.get("degraded_reasons") or []))

    def test_write_status_suppresses_stale_verify_dispatch_stall_during_implement_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root, implement="Codex", verify="Claude", advisory="Gemini")
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "job-stale-verify.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-stale-verify",
                        "status": "VERIFY_PENDING",
                        "artifact_path": "work/4/21/stale.md",
                        "artifact_hash": "stale-hash",
                        "round": 1,
                        "updated_at": 100.0,
                        "dispatch_control_seq": 600,
                        "dispatch_stall_detected_at": 100.0,
                        "dispatch_stall_fingerprint": "stall-fingerprint-1",
                        "dispatch_stall_count": 2,
                        "dispatch_stall_stage": "dispatch_seen_missing",
                        "degraded_reason": "dispatch_stall",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "IMPLEMENT_ACTIVE",
                        "legacy_state": "CLAUDE_ACTIVE",
                        "entered_at": 1.0,
                        "reason": "claude_handoff_updated",
                        "active_control_file": "claude_handoff.md",
                        "active_control_seq": 605,
                        "active_role": "implement",
                        "active_lane": "Codex",
                    }
                ),
                encoding="utf-8",
            )
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 605\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": "dispatch_seen seq 600"},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": "prompt_visible"},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": "prompt_visible"},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "RUNNING")
            self.assertEqual(status["degraded_reason"], "")
            self.assertEqual(list(status.get("degraded_reasons") or []), [])
            self.assertIsNone(status["active_round"])

    def test_manifest_mismatch_blocks_receipt_and_marks_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-2"
            verify_dir = root / "verify" / "4" / "11"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 23\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 23,
                        "verify_job_id": "job-2",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-1.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-2",
                        "round": 1,
                        "role": "verify",
                        "artifact_hash": "expected-hash",
                        "created_at": "2026-04-11T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-2.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-2",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/11/work-note.md",
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
            (verify_dir / "2026-04-11-verify.md").write_text("# verify\n", encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertIn("receipt_manifest:job-2", status["degraded_reason"])
            self.assertEqual(status["last_receipt_id"], "")

    def test_slot_verify_manifest_role_is_accepted_for_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            manifest_dir = pipeline_dir / "manifests" / "job-slot-verify"
            verify_dir = root / "verify" / "4" / "11"
            state_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 31\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_VERIFY",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 31,
                        "verify_job_id": "job-slot-verify",
                    }
                ),
                encoding="utf-8",
            )
            manifest_path = manifest_dir / "round-1.verify.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "job_id": "job-slot-verify",
                        "round": 1,
                        "role": "slot_verify",
                        "artifact_hash": "artifact-hash-slot-verify",
                        "created_at": "2026-04-11T01:02:03Z",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-slot-verify.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-slot-verify",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/11/work-note.md",
                        "artifact_hash": "artifact-hash-slot-verify",
                        "round": 1,
                        "verify_manifest_path": str(manifest_path),
                        "verify_result": "passed_by_feedback",
                        "updated_at": 100.0,
                        "verify_completed_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )
            (verify_dir / "2026-04-11-verify.md").write_text(
                "Based on `work/4/11/work-note.md`\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "STOPPED")
            self.assertEqual(status["degraded_reason"], "")
            self.assertTrue(status["last_receipt_id"])

    def test_stale_verify_done_does_not_degrade_when_newer_round_is_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "job-old.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-old",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/11/old.md",
                        "artifact_hash": "old-hash",
                        "round": 1,
                        "verify_manifest_path": "",
                        "verify_result": "passed",
                        "updated_at": 10.0,
                        "verify_completed_at": 10.0,
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-new.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-new",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/11/new.md",
                        "artifact_hash": "new-hash",
                        "round": 2,
                        "verify_manifest_path": "",
                        "updated_at": 20.0,
                        "verify_completed_at": 0.0,
                    }
                ),
                encoding="utf-8",
            )
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 101}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [{"name": "Claude", "state": "READY", "attachable": True, "pid": 11}],
                        {"Claude": {"state": "READY", "note": ""}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "RUNNING")
            self.assertEqual(status["degraded_reason"], "")
            self.assertEqual(list(status.get("degraded_reasons") or []), [])

    def test_verify_done_without_receipt_stays_receipt_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "job-receipt-pending.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-receipt-pending",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/15/work-note.md",
                        "artifact_hash": "artifact-hash-pending",
                        "round": 4,
                        "verify_manifest_path": "",
                        "verify_result": "passed",
                        "updated_at": 50.0,
                        "verify_completed_at": 50.0,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            status = supervisor._write_status()

            self.assertEqual(status["active_round"]["job_id"], "job-receipt-pending")
            self.assertEqual(status["active_round"]["state"], "RECEIPT_PENDING")
            self.assertEqual(status["last_receipt_id"], "")
            self.assertNotEqual(status["active_round"]["state"], "CLOSED")

    def test_build_lane_read_models_marks_working_and_heartbeat_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wrapper_dir = Path(tmp)
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "READY",
                {"reason": "prompt_visible"},
                source="wrapper",
                derived_from="vendor_output",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "HEARTBEAT",
                {},
                source="wrapper",
                derived_from="process_alive",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "DISPATCH_SEEN",
                {"job_id": "job-42", "dispatch_id": "dispatch-42", "control_seq": 19, "attempt": 1},
                source="wrapper",
                derived_from="task_hint",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_ACCEPTED",
                {"job_id": "job-42", "dispatch_id": "dispatch-42", "control_seq": 19, "attempt": 1},
                source="wrapper",
                derived_from="vendor_output",
            )
            models = build_lane_read_models(wrapper_dir, heartbeat_timeout_sec=3600.0, now_ts=1.0)
            self.assertEqual(models["Codex"]["state"], "WORKING")
            self.assertEqual(models["Codex"]["seen_task"]["job_id"], "job-42")
            self.assertEqual(models["Codex"]["accepted_task"]["job_id"], "job-42")
            self.assertEqual(models["Codex"]["accepted_task"]["dispatch_id"], "dispatch-42")

            stale_models = build_lane_read_models(wrapper_dir, heartbeat_timeout_sec=0.0, now_ts=9999999999.0)
            self.assertEqual(stale_models["Codex"]["state"], "BROKEN")
            self.assertEqual(stale_models["Codex"]["note"], "heartbeat_timeout")

    def test_build_lane_read_models_tracks_task_done_dispatch_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wrapper_dir = Path(tmp)
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_ACCEPTED",
                {"job_id": "job-42", "dispatch_id": "dispatch-42", "control_seq": 19, "attempt": 1},
                source="wrapper",
                derived_from="vendor_output",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_DONE",
                {
                    "job_id": "job-42",
                    "dispatch_id": "dispatch-42",
                    "control_seq": 19,
                    "reason": "duplicate_handoff",
                },
                source="wrapper",
                derived_from="vendor_output",
            )

            models = build_lane_read_models(wrapper_dir, heartbeat_timeout_sec=3600.0, now_ts=1.0)

            self.assertEqual(models["Codex"]["state"], "READY")
            self.assertIsNone(models["Codex"]["accepted_task"])
            self.assertEqual(models["Codex"]["done_task"]["job_id"], "job-42")
            self.assertEqual(models["Codex"]["done_task"]["dispatch_id"], "dispatch-42")
            self.assertEqual(models["Codex"]["done_task"]["reason"], "duplicate_handoff")
            self.assertTrue(models["Codex"]["done_at"])
            self.assertEqual(models["Codex"]["note"], "waiting_next_control")

    def test_supervisor_mirrors_task_wrapper_events_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            wrapper_dir = supervisor.wrapper_events_dir
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "HEARTBEAT",
                {},
                source="wrapper",
                derived_from="process_alive",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "DISPATCH_SEEN",
                {"job_id": "ctrl-628", "dispatch_id": "seq-628", "control_seq": 628, "attempt": 1},
                source="wrapper",
                derived_from="task_hint",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_ACCEPTED",
                {"job_id": "ctrl-628", "dispatch_id": "seq-628", "control_seq": 628, "attempt": 1},
                source="wrapper",
                derived_from="vendor_output",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_DONE",
                {"job_id": "ctrl-628", "dispatch_id": "seq-628", "control_seq": 628},
                source="wrapper",
                derived_from="vendor_output",
            )

            supervisor._mirror_wrapper_task_events()
            supervisor._mirror_wrapper_task_events()

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual([event["event_type"] for event in events], ["DISPATCH_SEEN", "TASK_ACCEPTED", "TASK_DONE"])
            self.assertTrue(all(event["source"] == "wrapper" for event in events))
            self.assertEqual(events[0]["payload"]["lane"], "Codex")
            self.assertEqual(events[0]["payload"]["job_id"], "ctrl-628")
            self.assertEqual(events[0]["payload"]["dispatch_id"], "seq-628")
            self.assertEqual(events[0]["payload"]["control_seq"], 628)
            self.assertEqual(events[0]["payload"]["attempt"], 1)
            self.assertEqual(events[0]["payload"]["derived_from"], "task_hint")
            self.assertTrue(events[0]["payload"]["wrapper_ts"])

            restarted = RuntimeSupervisor(root, run_id=supervisor.run_id, start_runtime=False)
            restarted._mirror_wrapper_task_events()
            after_restart_events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(
                [event["event_type"] for event in after_restart_events],
                ["DISPATCH_SEEN", "TASK_ACCEPTED", "TASK_DONE"],
            )

    def test_mirror_wrapper_task_events_appends_to_events_jsonl(self) -> None:
        """_mirror_wrapper_task_events가 wrapper-events/*.jsonl 이벤트를
        supervisor events.jsonl에 source='wrapper'로 실제 기록해야 함"""
        import json
        import tempfile
        from pathlib import Path

        from pipeline_runtime.supervisor import RuntimeSupervisor
        from pipeline_runtime.wrapper_events import append_wrapper_event

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run_id = "test-run-001"
            run_dir = base / "runs" / run_id
            run_dir.mkdir(parents=True)
            wrapper_dir = run_dir / "wrapper-events"
            wrapper_dir.mkdir()

            # Write a DISPATCH_SEEN event into wrapper-events/codex.jsonl
            append_wrapper_event(
                wrapper_dir,
                "codex",
                "DISPATCH_SEEN",
                {
                    "job_id": "ctrl-1",
                    "dispatch_id": "seq-1",
                    "control_seq": 1,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="task_hint",
            )

            sup = RuntimeSupervisor.__new__(RuntimeSupervisor)
            sup.base_dir = base
            sup.run_id = run_id
            sup.run_dir = run_dir
            sup.wrapper_events_dir = wrapper_dir
            sup.events_path = run_dir / "events.jsonl"
            sup._mirrored_wrapper_event_keys = set()
            sup._mirrored_wrapper_event_keys_seeded = False
            sup._event_seq = 0

            sup._mirror_wrapper_task_events()

            # events.jsonl must contain exactly one wrapper-source entry
            assert sup.events_path.exists(), "events.jsonl was not created"
            lines = [json.loads(l) for l in sup.events_path.read_text().splitlines()]
            wrapper_entries = [e for e in lines if e.get("source") == "wrapper"]
            self.assertEqual(len(wrapper_entries), 1)
            self.assertEqual(wrapper_entries[0]["event_type"], "DISPATCH_SEEN")
            payload = wrapper_entries[0].get("payload", {})
            self.assertEqual(payload.get("job_id"), "ctrl-1")

    def test_progress_hint_marks_verify_note_written_next_control_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor.runtime_state = "RUNNING"

            progress = supervisor._build_progress_hint(
                active_lane="Claude",
                active_round={"state": "VERIFYING", "job_id": "job-1"},
                turn_state={
                    "state": "VERIFY_ACTIVE",
                    "entered_at": 100.0,
                    "active_role": "verify",
                    "active_lane": "Claude",
                },
                control={"active_control_status": "none", "active_control_file": ""},
                autonomy={"mode": "normal"},
                artifacts={
                    "latest_work": {"path": "work.md", "mtime": 90.0},
                    "latest_verify": {"path": "verify.md", "mtime": 101.0},
                },
            )
            lanes = [{"name": "Claude", "state": "WORKING", "note": "followup"}]
            supervisor._annotate_lane_progress(lanes, progress)

            self.assertEqual(progress["phase"], "verify_note_written_next_control_pending")
            self.assertEqual(progress["lane"], "Claude")
            self.assertEqual(lanes[0]["progress_phase"], "verify_note_written_next_control_pending")

    def test_progress_hint_marks_operator_gate_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor.runtime_state = "RUNNING"

            progress = supervisor._build_progress_hint(
                active_lane="Claude",
                active_round=None,
                turn_state={
                    "state": "VERIFY_FOLLOWUP",
                    "entered_at": 100.0,
                    "active_role": "verify",
                    "active_lane": "Claude",
                },
                control={"active_control_status": "none", "active_control_file": ""},
                autonomy={"mode": "pending_operator", "reason_code": "approval_required"},
                artifacts={
                    "latest_work": {"path": "work.md", "mtime": 90.0},
                    "latest_verify": {"path": "verify.md", "mtime": 95.0},
                },
            )

            self.assertEqual(progress["phase"], "operator_gate_followup")
            self.assertEqual(progress["reason"], "approval_required")

    def test_progress_hint_marks_operator_approval_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor.runtime_state = "RUNNING"

            progress = supervisor._build_progress_hint(
                active_lane="Codex",
                active_round=None,
                turn_state={
                    "state": "VERIFY_FOLLOWUP",
                    "entered_at": 100.0,
                    "active_role": "verify",
                    "active_lane": "Codex",
                },
                control={"active_control_status": "none", "active_control_file": ""},
                autonomy={"mode": "recovery", "reason_code": OPERATOR_APPROVAL_COMPLETED_REASON},
                artifacts={
                    "latest_work": {"path": "work.md", "mtime": 90.0},
                    "latest_verify": {"path": "verify.md", "mtime": 95.0},
                },
            )

            self.assertEqual(progress["phase"], OPERATOR_APPROVAL_COMPLETED_REASON)
            self.assertEqual(progress["reason"], OPERATOR_APPROVAL_COMPLETED_REASON)

    def test_operator_approval_completed_turn_suppresses_active_operator_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            base_dir = root / ".pipeline"
            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 44\n"
                "REASON_CODE: approval_required\n"
                "DECISION_REQUIRED: approve completed commit and remote push follow-up\n",
                encoding="utf-8",
            )
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            marker = supervisor._stale_operator_control_marker(
                {
                    "active_control_file": ".pipeline/operator_request.md",
                    "active_control_status": "needs_operator",
                    "active_control_seq": 44,
                },
                [],
                {
                    "state": "VERIFY_FOLLOWUP",
                    "reason": OPERATOR_APPROVAL_COMPLETED_REASON,
                    "active_control_seq": 44,
                },
            )

            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], OPERATOR_APPROVAL_COMPLETED_REASON)
            self.assertEqual(marker["control_seq"], 44)

    def test_commit_push_bundle_authorization_operator_gate_routes_to_triage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            operator_path = pipeline_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 713\n"
                f"REASON_CODE: {COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON}\n"
                "OPERATOR_POLICY: internal_only\n"
                "DECISION_CLASS: release_gate\n"
                "DECISION_REQUIRED: automation axis commit and push authorization\n",
                encoding="utf-8",
            )
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            marker, autonomy = supervisor._operator_gate_marker(
                {
                    "active_control_file": ".pipeline/operator_request.md",
                    "active_control_status": "needs_operator",
                    "active_control_seq": 713,
                    "mtime": operator_path.stat().st_mtime,
                },
                turn_state={"state": "IDLE", "reason": "operator_request_updated"},
                active_round={"state": "CLOSED"},
                wrapper_models={},
            )

            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON)
            self.assertEqual(marker["mode"], "triage")
            self.assertEqual(marker["routed_to"], "codex_followup")
            self.assertEqual(autonomy["mode"], "triage")
            self.assertEqual(autonomy["decision_class"], "release_gate")

    def test_active_verify_round_keeps_codex_surface_working_even_if_wrapper_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 4242, "attachable": True, "pane_id": "%2"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "• Working (22s • esc to interrupt)\n"
                        if lane_name == "Codex"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-15T08:33:21.218699Z",
                            "last_heartbeat_at": "2026-04-15T08:33:27.312433Z",
                        }
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-42",
                        "state": "VERIFYING",
                        "status": "VERIFY_RUNNING",
                    },
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "WORKING")
            self.assertEqual(codex["note"], "verifying")

    def test_write_status_surfaces_dispatch_stall_degraded_reason_and_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "job-dispatch-stall.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-dispatch-stall",
                        "status": "VERIFY_PENDING",
                        "artifact_path": "work/4/17/work-note.md",
                        "artifact_hash": "artifact-hash-dispatch-stall",
                        "round": 2,
                        "updated_at": 200.0,
                        "dispatch_stall_fingerprint": "stall-fingerprint-1",
                        "dispatch_stall_count": 2,
                        "dispatch_stall_detected_at": 210.0,
                        "dispatch_stall_stage": "task_accept_missing",
                        "degraded_reason": "dispatch_stall",
                        "lane_note": "waiting_task_accept_after_dispatch",
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    side_effect=lambda lane_name: {
                        "name": lane_name,
                        "alive": True,
                        "pid": {"Claude": 11, "Codex": 12, "Gemini": 13}[lane_name],
                        "attachable": True,
                        "pane_id": "%2",
                    },
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "› Use /skills to list available skills\n\n"
                        "gpt-5.4 xhigh fast · ~/code/projectH\n"
                        if lane_name == "Codex"
                        else ""
                    ),
                ),
                mock.patch(
                    "pipeline_runtime.supervisor.build_lane_read_models",
                    return_value={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T03:30:00Z",
                            "last_heartbeat_at": "2026-04-17T03:30:05Z",
                        },
                        "Claude": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T03:30:00Z",
                            "last_heartbeat_at": "2026-04-17T03:30:05Z",
                        },
                        "Gemini": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T03:30:00Z",
                            "last_heartbeat_at": "2026-04-17T03:30:05Z",
                        },
                    },
                ),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            codex = next(lane for lane in status["lanes"] if lane["name"] == "Codex")
            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            stall_events = [event for event in events if event.get("event_type") == "dispatch_stall_detected"]
            automation_events = [event for event in events if event.get("event_type") == "automation_incident"]

            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertEqual(status["degraded_reason"], "dispatch_stall")
            self.assertIn("dispatch_stall", list(status.get("degraded_reasons") or []))
            self.assertEqual(status["automation_health"], "attention")
            self.assertEqual(status["automation_reason_code"], "dispatch_stall")
            self.assertEqual(status["automation_incident_family"], "dispatch_stall")
            self.assertEqual(status["automation_next_action"], "verify_followup")
            self.assertEqual(status["active_round"]["state"], "VERIFY_PENDING")
            self.assertEqual(status["active_round"]["note"], "waiting_task_accept_after_dispatch")
            self.assertEqual(status["active_round"]["dispatch_stage"], "task_accept_missing")
            self.assertEqual(codex["state"], "READY")
            self.assertEqual(codex["note"], "waiting_task_accept_after_dispatch")
            self.assertEqual(len(stall_events), 1)
            self.assertEqual(stall_events[0]["payload"]["action"], "degraded")
            self.assertEqual(stall_events[0]["payload"]["lane"], "Codex")
            self.assertEqual(stall_events[0]["payload"]["stage"], "task_accept_missing")
            self.assertEqual(len(automation_events), 1)
            self.assertEqual(automation_events[0]["payload"]["automation_health"], "attention")
            self.assertEqual(automation_events[0]["payload"]["reason_code"], "dispatch_stall")
            self.assertEqual(automation_events[0]["payload"]["incident_family"], "dispatch_stall")
            self.assertEqual(automation_events[0]["payload"]["next_action"], "verify_followup")

    def test_write_status_ignores_old_legacy_dispatch_stall_from_previous_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            stale_state = state_dir / "job-old-stall.json"
            stale_state.write_text(
                json.dumps(
                    {
                        "job_id": "job-old-stall",
                        "status": "VERIFY_PENDING",
                        "artifact_path": "work/4/17/stale-work.md",
                        "artifact_hash": "artifact-hash-old-stall",
                        "round": 1,
                        "updated_at": 100.0,
                        "dispatch_stall_fingerprint": "legacy-stall",
                        "dispatch_stall_count": 2,
                        "dispatch_stall_detected_at": 110.0,
                        "degraded_reason": "dispatch_stall",
                        "lane_note": "waiting_task_accept_after_dispatch",
                    }
                ),
                encoding="utf-8",
            )
            old_ts = time.time() - 60.0
            os.utime(stale_state, (old_ts, old_ts))

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": "prompt_visible"},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": "prompt_visible"},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": "prompt_visible"},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "RUNNING")
            self.assertEqual(status["degraded_reason"], "")
            self.assertEqual(status["degraded_reasons"], [])

    def test_write_status_keeps_current_run_dispatch_stall_even_when_state_file_is_old(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            current_state = state_dir / "job-current-stall.json"
            current_state.write_text(
                json.dumps(
                    {
                        "job_id": "job-current-stall",
                        "run_id": supervisor.run_id,
                        "status": "VERIFY_PENDING",
                        "artifact_path": "work/4/17/current-work.md",
                        "artifact_hash": "artifact-hash-current-stall",
                        "round": 1,
                        "updated_at": 100.0,
                        "dispatch_stall_fingerprint": "current-stall",
                        "dispatch_stall_count": 2,
                        "dispatch_stall_detected_at": 110.0,
                        "degraded_reason": "dispatch_stall",
                        "lane_note": "waiting_task_accept_after_dispatch",
                    }
                ),
                encoding="utf-8",
            )
            old_ts = time.time() - 60.0
            os.utime(current_state, (old_ts, old_ts))
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": "prompt_visible"},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": "prompt_visible"},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": "prompt_visible"},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertEqual(status["degraded_reason"], "dispatch_stall")
            self.assertIn("dispatch_stall", list(status.get("degraded_reasons") or []))

    def test_write_status_surfaces_completion_stall_degraded_reason_and_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            state_dir = root / ".pipeline" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "job-completion-stall.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-completion-stall",
                        "status": "VERIFY_PENDING",
                        "artifact_path": "work/4/17/work-note.md",
                        "artifact_hash": "artifact-hash-completion-stall",
                        "round": 4,
                        "updated_at": 220.0,
                        "dispatch_id": "dispatch-44",
                        "accepted_dispatch_id": "dispatch-44",
                        "done_dispatch_id": "",
                        "completion_stall_fingerprint": "completion-fingerprint-1",
                        "completion_stall_count": 2,
                        "completion_stall_detected_at": 225.0,
                        "completion_stall_stage": "task_done_missing",
                        "degraded_reason": "post_accept_completion_stall",
                        "lane_note": "waiting_task_done_after_accept",
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    side_effect=lambda lane_name: {
                        "name": lane_name,
                        "alive": True,
                        "pid": {"Claude": 11, "Codex": 12, "Gemini": 13}[lane_name],
                        "attachable": True,
                        "pane_id": "%2",
                    },
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "› Use /skills to list available skills\n\n"
                        "gpt-5.4 xhigh fast · ~/code/projectH\n"
                        if lane_name == "Codex"
                        else ""
                    ),
                ),
                mock.patch(
                    "pipeline_runtime.supervisor.build_lane_read_models",
                    return_value={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T03:30:00Z",
                            "last_heartbeat_at": "2026-04-17T03:30:05Z",
                        },
                        "Claude": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T03:30:00Z",
                            "last_heartbeat_at": "2026-04-17T03:30:05Z",
                        },
                        "Gemini": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T03:30:00Z",
                            "last_heartbeat_at": "2026-04-17T03:30:05Z",
                        },
                    },
                ),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            codex = next(lane for lane in status["lanes"] if lane["name"] == "Codex")
            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            stall_events = [event for event in events if event.get("event_type") == "completion_stall_detected"]
            automation_events = [event for event in events if event.get("event_type") == "automation_incident"]

            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertEqual(status["degraded_reason"], "post_accept_completion_stall")
            self.assertIn("post_accept_completion_stall", list(status.get("degraded_reasons") or []))
            self.assertEqual(status["automation_health"], "attention")
            self.assertEqual(status["automation_reason_code"], "post_accept_completion_stall")
            self.assertEqual(status["automation_incident_family"], "completion_stall")
            self.assertEqual(status["automation_next_action"], "verify_followup")
            self.assertEqual(status["active_round"]["state"], "VERIFY_PENDING")
            self.assertEqual(status["active_round"]["note"], "waiting_task_done_after_accept")
            self.assertEqual(status["active_round"]["completion_stage"], "task_done_missing")
            self.assertEqual(codex["state"], "READY")
            self.assertEqual(codex["note"], "waiting_task_done_after_accept")
            self.assertEqual(len(stall_events), 1)
            self.assertEqual(stall_events[0]["payload"]["action"], "degraded")
            self.assertEqual(stall_events[0]["payload"]["lane"], "Codex")
            self.assertEqual(stall_events[0]["payload"]["stage"], "task_done_missing")
            self.assertEqual(len(automation_events), 1)
            self.assertEqual(automation_events[0]["payload"]["automation_health"], "attention")
            self.assertEqual(automation_events[0]["payload"]["reason_code"], "post_accept_completion_stall")
            self.assertEqual(automation_events[0]["payload"]["incident_family"], "completion_stall")
            self.assertEqual(automation_events[0]["payload"]["next_action"], "verify_followup")

    def test_idle_verify_round_keeps_codex_ready_even_if_round_is_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 4242, "attachable": True, "pane_id": "%2"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "› \n"
                        "───────────────────────────────────────────────────────────────────────────────\n"
                        "  ⏵⏵ bypass permissions on (shift+tab to cycle)\n"
                        if lane_name == "Codex"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-15T08:33:21.218699Z",
                            "last_heartbeat_at": "2026-04-15T08:33:27.312433Z",
                        }
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-42",
                        "state": "VERIFYING",
                        "status": "VERIFY_RUNNING",
                    },
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "READY")
            self.assertEqual(codex["note"], "verifying")

    def test_prompt_visible_verify_pending_keeps_codex_working_while_task_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 4242, "attachable": True, "pane_id": "%2"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "› Use /skills to list available skills\n\n"
                        "gpt-5.4 xhigh fast · ~/code/projectH\n"
                        if lane_name == "Codex"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "WORKING",
                            "note": "seq 205",
                            "accepted_task": {"job_id": "job-42", "control_seq": 205, "attempt": 1},
                            "last_event_at": "2026-04-16T12:38:57.552104Z",
                            "last_heartbeat_at": "2026-04-16T12:38:57.552104Z",
                        }
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-42",
                        "state": "VERIFY_PENDING",
                        "status": "VERIFY_PENDING",
                    },
                    turn_state={"state": "IDLE"},
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "WORKING")
            self.assertEqual(codex["note"], "verify_pending")

    def test_dispatch_stall_active_round_surfaces_machine_note_on_codex_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 4242, "attachable": True, "pane_id": "%2"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "› Use /skills to list available skills\n\n"
                        "gpt-5.4 xhigh fast · ~/code/projectH\n"
                        if lane_name == "Codex"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T02:40:01.000000Z",
                            "last_heartbeat_at": "2026-04-17T02:40:05.000000Z",
                        }
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-77",
                        "state": "VERIFY_PENDING",
                        "status": "VERIFY_PENDING",
                        "note": "waiting_task_accept_after_dispatch",
                        "degraded_reason": "dispatch_stall",
                    },
                    turn_state={"state": "IDLE"},
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "READY")
            self.assertEqual(codex["note"], "waiting_task_accept_after_dispatch")

    def test_active_implement_turn_keeps_claude_surface_working_even_if_wrapper_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with mock.patch.object(
                supervisor.adapter,
                "lane_health",
                return_value={"alive": True, "pid": 31337, "attachable": True, "pane_id": "%1"},
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Claude": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-16T07:02:45.265662Z",
                            "last_heartbeat_at": "2026-04-16T07:02:51.125129Z",
                        }
                    },
                    active_lane="Claude",
                    active_round=None,
                    turn_state={"state": "CLAUDE_ACTIVE"},
                    control={"active_control_status": "implement"},
                )
            claude = next(lane for lane in lanes if lane["name"] == "Claude")
            self.assertEqual(claude["state"], "WORKING")
            self.assertEqual(claude["note"], "implement")

    def test_prompt_visible_implement_owner_downgrades_claude_from_working_to_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 31337, "attachable": True, "pane_id": "%1"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "How is Claude doing this session? (optional)\n"
                        "❯ \n"
                        "  ⏵⏵ bypass permissions on (shift+tab to cycle)\n"
                        if lane_name == "Claude"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Claude": {
                            "state": "WORKING",
                            "note": "implement",
                            "last_event_at": "2026-04-17T08:00:00.000000Z",
                            "last_heartbeat_at": "2026-04-17T08:00:01.000000Z",
                        }
                    },
                    active_lane="Claude",
                    active_round=None,
                    turn_state={"state": "CLAUDE_ACTIVE"},
                    control={"active_control_status": "implement"},
                )
            claude = next(lane for lane in lanes if lane["name"] == "Claude")
            self.assertEqual(claude["state"], "READY")
            self.assertEqual(claude["note"], "prompt_visible")

    def test_ready_tail_clears_stale_dispatch_seen_note_for_inactive_ready_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root, implement="Codex", verify="Claude", advisory="Gemini")
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            ready_tail = (
                "How is Claude doing this session? (optional)\n"
                "❯ \n"
                "  ⏵⏵ bypass permissions on (shift+tab to cycle)\n"
            )
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    side_effect=lambda lane_name: {
                        "alive": True,
                        "pid": {"Claude": 11, "Codex": 12, "Gemini": 13}.get(lane_name),
                        "attachable": True,
                        "pane_id": "%1",
                    },
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: ready_tail if lane_name in {"Claude", "Codex"} else "",
                ),
                mock.patch.object(
                    supervisor,
                    "_tail_surface_state",
                    side_effect=lambda lane_name, text: "READY" if lane_name in {"Claude", "Codex"} else "",
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Claude": {
                            "state": "READY",
                            "note": "dispatch_seen seq 600",
                            "seen_task": {"job_id": "job-600", "control_seq": 600, "attempt": 1},
                            "last_event_at": "2026-04-20T17:03:28.166177Z",
                            "last_heartbeat_at": "2026-04-20T17:03:28.166177Z",
                        },
                        "Codex": {
                            "state": "READY",
                            "note": "dispatch_seen seq 602",
                            "seen_task": {"job_id": "job-602", "control_seq": 602, "attempt": 1},
                            "last_event_at": "2026-04-20T17:03:23.480503Z",
                            "last_heartbeat_at": "2026-04-20T17:03:23.480503Z",
                        },
                        "Gemini": {
                            "state": "WORKING",
                            "note": "working",
                            "last_event_at": "2026-04-20T17:03:26.661341Z",
                            "last_heartbeat_at": "2026-04-20T17:03:26.661341Z",
                        },
                    },
                    active_lane="Gemini",
                    active_round=None,
                    turn_state={
                        "state": "ADVISORY_ACTIVE",
                        "legacy_state": "GEMINI_ADVISORY",
                        "active_role": "advisory",
                        "active_lane": "Gemini",
                    },
                    control={"active_control_status": "request_open", "active_control_seq": 603},
                )
            claude = next(lane for lane in lanes if lane["name"] == "Claude")
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(claude["state"], "READY")
            self.assertEqual(claude["note"], "prompt_visible")
            self.assertEqual(codex["state"], "READY")
            self.assertEqual(codex["note"], "prompt_visible")

    def test_busy_tail_wins_over_prompt_footer_for_active_claude_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 31337, "attachable": True, "pane_id": "%1"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "● Bash(npx playwright test ...)\n"
                        "* Discombobulating… (58s · ↓ 723 tokens · thinking with high effort)\n"
                        "❯ \n"
                        "  ⏵⏵ bypass permissions on (shift+tab to cycle) · esc to interrupt\n"
                        if lane_name == "Claude"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Claude": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T08:20:00.000000Z",
                            "last_heartbeat_at": "2026-04-17T08:20:01.000000Z",
                        }
                    },
                    active_lane="Claude",
                    active_round=None,
                    turn_state={"state": "CLAUDE_ACTIVE"},
                    control={"active_control_status": "implement"},
                )
            claude = next(lane for lane in lanes if lane["name"] == "Claude")
            self.assertEqual(claude["state"], "WORKING")
            self.assertEqual(claude["note"], "implement")

    def test_build_lane_statuses_defers_working_on_signal_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root, implement="Codex", verify="Claude")
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 31337, "attachable": True, "pane_id": "%1"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "• Working (12s • esc to interrupt)\n"
                        if lane_name == "Codex"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "WORKING",
                            "note": "implement",
                            "last_event_at": "2026-04-21T09:00:00.000000Z",
                            "last_heartbeat_at": "2026-04-21T09:00:01.000000Z",
                        }
                    },
                    active_lane="",
                    active_round=None,
                    turn_state={"state": "IDLE"},
                    control={"active_control_status": "implement", "active_control_seq": 205},
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "READY")
            self.assertEqual(codex["note"], "signal_mismatch")

    def test_build_lane_statuses_uses_matching_task_done_over_stale_busy_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root, implement="Codex", verify="Claude")
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 31337, "attachable": True, "pane_id": "%1"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "• Working (12s • esc to interrupt)\n"
                        if lane_name == "Codex"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "READY",
                            "note": "",
                            "done_task": {
                                "job_id": "ctrl-205",
                                "dispatch_id": "seq-205",
                                "control_seq": 205,
                            },
                            "last_event_at": "2026-04-21T09:00:00.000000Z",
                            "last_heartbeat_at": "2026-04-21T09:00:01.000000Z",
                        }
                    },
                    active_lane="",
                    active_round=None,
                    turn_state={"state": "IDLE"},
                    control={"active_control_status": "implement", "active_control_seq": 205},
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "READY")
            self.assertEqual(codex["note"], "waiting_next_control")

    def test_active_implement_control_keeps_claude_working_even_during_verify_follow_on(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 31337, "attachable": True, "pane_id": "%1"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "• Working (12s • esc to interrupt)\n"
                        if lane_name == "Claude"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Claude": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-16T07:07:03.432725Z",
                            "last_heartbeat_at": "2026-04-16T07:07:03.432725Z",
                        },
                        "Codex": {
                            "state": "WORKING",
                            "note": "verifying",
                            "last_event_at": "2026-04-16T07:07:03.557365Z",
                            "last_heartbeat_at": "2026-04-16T07:07:03.557365Z",
                        },
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-42",
                        "state": "VERIFYING",
                        "status": "VERIFY_RUNNING",
                    },
                    turn_state={"state": "IDLE", "reason": "claude_activity_detected"},
                    control={"active_control_status": "implement", "active_control_seq": 180},
                )
            claude = next(lane for lane in lanes if lane["name"] == "Claude")
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(claude["state"], "WORKING")
            self.assertEqual(claude["note"], "implement")
            self.assertEqual(codex["state"], "WORKING")
            self.assertEqual(codex["note"], "verifying")

    def test_idle_implement_owner_stays_ready_during_verify_follow_on(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 31337, "attachable": True, "pane_id": "%1"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "❯ \n"
                        "───────────────────────────────────────────────────────────────────────────────\n"
                        "  ⏵⏵ bypass permissions on (shift+tab to cycle) · esc to interrupt\n"
                        if lane_name == "Claude"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Claude": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-16T07:07:03.432725Z",
                            "last_heartbeat_at": "2026-04-16T07:07:03.432725Z",
                        },
                        "Codex": {
                            "state": "WORKING",
                            "note": "verifying",
                            "last_event_at": "2026-04-16T07:07:03.557365Z",
                            "last_heartbeat_at": "2026-04-16T07:07:03.557365Z",
                        },
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-42",
                        "state": "VERIFYING",
                        "status": "VERIFY_RUNNING",
                    },
                    turn_state={"state": "IDLE", "reason": "verify_running"},
                    control={"active_control_status": "implement", "active_control_seq": 180},
                )
            claude = next(lane for lane in lanes if lane["name"] == "Claude")
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(claude["state"], "READY")
            self.assertEqual(claude["note"], "prompt_visible")
            self.assertEqual(codex["state"], "WORKING")
            self.assertEqual(codex["note"], "verifying")

    def test_verify_lane_background_terminal_wait_surfaces_working(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 31337, "attachable": True, "pane_id": "%2"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    return_value=(
                        "Waiting for background terminal (3m 33s) · 1 background terminal running /ps to view /stop to close\n"
                        "› Type your message\n"
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T07:33:00.805605Z",
                            "last_heartbeat_at": "2026-04-17T07:33:00.805605Z",
                        },
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-42",
                        "state": "VERIFYING",
                        "status": "VERIFY_RUNNING",
                        "note": "waiting_task_done_after_accept",
                    },
                    turn_state={"state": "CODEX_VERIFY", "reason": "verify_running"},
                    control={"active_control_status": "none", "active_control_seq": -1},
                )

            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "WORKING")
            self.assertEqual(codex["note"], "waiting_task_done_after_accept")

    def test_active_lane_auth_failure_marks_lane_broken(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 4242, "attachable": True, "pane_id": "%2"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    return_value=(
                        "API Error: 401\n"
                        '{"error":{"type":"authentication_error","message":"Invalid authentication credentials"}}\n'
                        "Please run /login\n"
                    ),
                ),
            ):
                lanes, models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Claude": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-15T08:33:21.218699Z",
                            "last_heartbeat_at": "2026-04-15T08:33:27.312433Z",
                        }
                    },
                    active_lane="Claude",
                    active_round=None,
                    control={"active_control_status": "implement"},
                )
            claude = next(lane for lane in lanes if lane["name"] == "Claude")
            self.assertEqual(claude["state"], "BROKEN")
            self.assertEqual(claude["note"], "auth_login_required")
            self.assertEqual(models["Claude"]["failure_reason"], "auth_login_required")

    def test_codex_followup_turn_surfaces_working_even_without_active_control_seq(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with mock.patch.object(
                supervisor.adapter,
                "lane_health",
                return_value={"alive": True, "pid": 5252, "attachable": True, "pane_id": "%5"},
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-15T08:33:21.218699Z",
                            "last_heartbeat_at": "2026-04-15T08:33:27.312433Z",
                        }
                    },
                    active_lane="Codex",
                    active_round={
                        "job_id": "job-closed",
                        "state": "CLOSED",
                        "status": "VERIFY_DONE",
                    },
                    turn_state={"state": "CODEX_FOLLOWUP"},
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "WORKING")
            self.assertEqual(codex["note"], "followup")

    def test_codex_tail_activity_promotes_stale_ready_surface_to_working(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    return_value={"alive": True, "pid": 5252, "attachable": True, "pane_id": "%5"},
                ),
                mock.patch.object(
                    supervisor.adapter,
                    "capture_tail",
                    side_effect=lambda lane_name, lines=80: (
                        "• Working (18s • esc to interrupt)\n"
                        "tab to queue message\n"
                        "55% context left\n"
                        if lane_name == "Codex"
                        else ""
                    ),
                ),
            ):
                lanes, _models = supervisor._build_lane_statuses(
                    wrapper_models={
                        "Codex": {
                            "state": "READY",
                            "note": "prompt_visible",
                            "last_event_at": "2026-04-17T08:10:00.000000Z",
                            "last_heartbeat_at": "2026-04-17T08:10:01.000000Z",
                        }
                    },
                    active_lane="",
                    active_round=None,
                    turn_state={"state": "IDLE"},
                )
            codex = next(lane for lane in lanes if lane["name"] == "Codex")
            self.assertEqual(codex["state"], "WORKING")
            self.assertEqual(codex["note"], "working")

    def test_active_verify_round_falls_back_to_codex_when_turn_state_is_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "IDLE"},
                {
                    "job_id": "job-42",
                    "state": "VERIFYING",
                    "status": "VERIFY_RUNNING",
                },
                control={},
            )

            self.assertEqual(active_lane, "Codex")

    def test_operator_wait_blocks_verify_fallback_active_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "OPERATOR_WAIT"},
                {
                    "job_id": "job-42",
                    "state": "VERIFYING",
                    "status": "VERIFY_RUNNING",
                },
                control={},
            )

            self.assertEqual(active_lane, "")

    def test_operator_wait_allows_verify_fallback_when_stale_operator_stop_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "OPERATOR_WAIT"},
                {
                    "job_id": "job-42",
                    "state": "VERIFYING",
                    "status": "VERIFY_RUNNING",
                },
                control={},
                stale_operator_control={"reason": "verified_blockers_resolved"},
            )

            self.assertEqual(active_lane, "Codex")

    def test_receipt_pending_does_not_keep_codex_active_lane_when_turn_is_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "IDLE"},
                {
                    "job_id": "job-42",
                    "state": "RECEIPT_PENDING",
                    "status": "VERIFY_DONE",
                    "completion_stage": "receipt_close_pending",
                },
                control={},
            )

            self.assertEqual(active_lane, "")

    def test_receipt_pending_keeps_codex_active_lane_during_codex_followup_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "CODEX_FOLLOWUP"},
                {
                    "job_id": "job-42",
                    "state": "RECEIPT_PENDING",
                    "status": "VERIFY_DONE",
                    "completion_stage": "receipt_close_pending",
                },
                control={},
            )

            self.assertEqual(active_lane, "Codex")

    def test_write_status_suppresses_operator_stop_during_idle_retriage_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 143\n\nReason:\n- still pending\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CODEX_FOLLOWUP",
                        "entered_at": 1.0,
                        "reason": "operator_wait_idle_retriage",
                        "active_control_file": "operator_request.md",
                        "active_control_seq": 143,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["control"]["active_control_seq"], -1)
            self.assertEqual(
                status["compat"]["control_slots"]["active"]["status"],
                "needs_operator",
            )

    def test_active_lane_for_runtime_ignores_stale_claude_active_when_control_seq_is_already_receipted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "CLAUDE_ACTIVE"},
                {"job_id": "job-42", "state": "CLOSED", "status": "VERIFY_DONE"},
                control={
                    "active_control_file": ".pipeline/claude_handoff.md",
                    "active_control_seq": 154,
                    "active_control_status": "implement",
                },
                last_receipt={"control_seq": 154},
                duplicate_control=None,
            )

            self.assertEqual(active_lane, "")

    def test_active_lane_for_runtime_follows_implement_owner_under_nondefault_role_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(
                root,
                selected_agents=["Claude", "Codex", "Gemini"],
                implement="Codex",
                verify="Claude",
                advisory="Gemini",
                advisory_enabled=True,
            )
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            active_lane = supervisor._active_lane_for_runtime(
                {"state": "CLAUDE_ACTIVE"},
                None,
                control={
                    "active_control_file": ".pipeline/claude_handoff.md",
                    "active_control_seq": 201,
                    "active_control_status": "implement",
                },
            )

            self.assertEqual(active_lane, "Codex")

    def test_write_status_clears_codex_task_hint_during_operator_wait(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 142\n"
                "REASON_CODE: slice_ambiguity\n"
                "OPERATOR_POLICY: gate_24h\n"
                "DECISION_CLASS: operator_only\n"
                "DECISION_REQUIRED: choose exact next slice\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "OPERATOR_WAIT",
                        "entered_at": 1.0,
                        "reason": "operator_request_updated",
                        "active_control_file": "operator_request.md",
                        "active_control_seq": 142,
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-42.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-42",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/15/work-note.md",
                        "round": 1,
                        "updated_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            codex_hint = json.loads(supervisor._task_hint_path("Codex").read_text(encoding="utf-8"))
            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["turn_state"]["state"], "OPERATOR_WAIT")
            self.assertEqual(status["compat"]["turn_state"]["state"], "OPERATOR_WAIT")
            self.assertEqual(status["autonomy"]["mode"], "triage")
            self.assertIsNone(status["active_round"])
            self.assertEqual(next(lane for lane in status["lanes"] if lane["name"] == "Codex")["state"], "READY")
            self.assertFalse(codex_hint["active"])
            self.assertEqual(codex_hint["job_id"], "")
            self.assertEqual(codex_hint["control_seq"], -1)

    def test_write_status_clears_verify_task_hint_when_runtime_is_stopped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "IDLE",
                        "entered_at": 1.0,
                        "reason": "test_setup",
                        "active_control_file": "",
                        "active_control_seq": -1,
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-42.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-42",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/17/work-note.md",
                        "round": 1,
                        "dispatch_id": "dispatch-42",
                        "dispatch_control_seq": 264,
                        "updated_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = False

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            codex_hint = json.loads(supervisor._task_hint_path("Codex").read_text(encoding="utf-8"))
            self.assertEqual(status["runtime_state"], "STOPPED")
            self.assertIsNone(status["active_round"])
            self.assertFalse(codex_hint["active"])
            self.assertEqual(codex_hint["job_id"], "")
            self.assertEqual(codex_hint["dispatch_id"], "")
            self.assertEqual(codex_hint["control_seq"], -1)

    def test_write_status_suppresses_stale_verify_round_during_operator_gated_hibernate_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "IDLE",
                        "entered_at": 1.0,
                        "reason": "operator_request_gated_hibernate",
                        "active_control_file": "",
                        "active_control_seq": -1,
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-77.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-77",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": "work/4/17/work-note.md",
                        "round": 1,
                        "updated_at": 100.0,
                        "dispatch_id": "dispatch-77",
                        "dispatch_control_seq": 266,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12},
                            {"name": "Gemini", "state": "OFF", "attachable": False, "pid": None},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "RUNNING")
            self.assertIsNone(status["active_round"])

    def test_write_status_gates_slice_ambiguity_operator_stop_for_24h(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 188\n"
                "REASON_CODE: slice_ambiguity\n"
                "OPERATOR_POLICY: gate_24h\n"
                "DECISION_CLASS: operator_only\n"
                "DECISION_REQUIRED: choose exact next slice\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            gated_events = [event for event in events if event.get("event_type") == "control_operator_gated"]

            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["compat"]["control_slots"]["active"]["status"], "needs_operator")
            self.assertEqual(status["autonomy"]["mode"], "triage")
            self.assertEqual(status["autonomy"]["block_reason"], "slice_ambiguity")
            self.assertEqual(status["autonomy"]["reason_code"], "slice_ambiguity")
            self.assertEqual(status["autonomy"]["operator_policy"], "gate_24h")
            self.assertTrue(status["autonomy"]["suppress_operator_until"])
            self.assertEqual(len(gated_events), 1)
            self.assertEqual(gated_events[0]["payload"]["reason"], "slice_ambiguity")

    def test_write_status_preserves_operator_gate_first_seen_across_seq_only_bump(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            operator_path = pipeline_dir / "operator_request.md"

            def write_operator_request(seq: int, mtime: float) -> None:
                operator_path.write_text(
                    "STATUS: needs_operator\n"
                    f"CONTROL_SEQ: {seq}\n"
                    "REASON_CODE: slice_ambiguity\n"
                    "OPERATOR_POLICY: gate_24h\n"
                    "DECISION_CLASS: operator_only\n"
                    "DECISION_REQUIRED: choose exact next slice\n",
                    encoding="utf-8",
                )
                os.utime(operator_path, (mtime, mtime))

            base_now = time.time()
            write_operator_request(188, base_now)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            def write_status() -> dict[str, object]:
                with (
                    mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                    mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                    mock.patch.object(
                        supervisor,
                        "_build_lane_statuses",
                        return_value=(
                            [
                                {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                                {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                                {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                            ],
                            {"Claude": {}, "Codex": {}, "Gemini": {}},
                        ),
                    ),
                    mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                    mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
                ):
                    return supervisor._write_status()

            first_status = write_status()
            first_autonomy = first_status["autonomy"]

            write_operator_request(189, base_now + 10.0)
            second_status = write_status()
            second_autonomy = second_status["autonomy"]

            self.assertEqual(second_autonomy["mode"], "triage")
            self.assertEqual(second_autonomy["block_reason"], "slice_ambiguity")
            self.assertEqual(second_autonomy["first_seen_at"], first_autonomy["first_seen_at"])
            self.assertEqual(
                second_autonomy["suppress_operator_until"],
                first_autonomy["suppress_operator_until"],
            )

    def test_write_status_normalizes_next_slice_aliases_to_gated_operator_stop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 188\n"
                "REASON_CODE: gemini_axis_switch_without_exact_slice\n"
                "OPERATOR_POLICY: stop_until_exact_slice_selected\n"
                "DECISION_CLASS: next_slice_selection\n"
                "DECISION_REQUIRED: choose exact next slice\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            gated_events = [event for event in events if event.get("event_type") == "control_operator_gated"]

            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["autonomy"]["mode"], "triage")
            self.assertEqual(status["autonomy"]["block_reason"], "slice_ambiguity")
            self.assertEqual(status["autonomy"]["reason_code"], "slice_ambiguity")
            self.assertEqual(status["autonomy"]["operator_policy"], "gate_24h")
            self.assertEqual(status["autonomy"]["classification_source"], "operator_policy")
            self.assertTrue(status["autonomy"]["suppress_operator_until"])
            self.assertEqual(len(gated_events), 1)
            self.assertEqual(gated_events[0]["payload"]["reason"], "slice_ambiguity")

    def test_write_status_routes_waiting_next_control_internal_only_to_triage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 189\n"
                "REASON_CODE: waiting_next_control\n"
                "OPERATOR_POLICY: internal_only\n"
                "DECISION_CLASS: next_slice_selection\n"
                "DECISION_REQUIRED: choose exact next slice\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            gated_events = [event for event in events if event.get("event_type") == "control_operator_gated"]

            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["autonomy"]["mode"], "triage")
            self.assertEqual(status["autonomy"]["block_reason"], "waiting_next_control")
            self.assertEqual(status["autonomy"]["reason_code"], "waiting_next_control")
            self.assertEqual(status["autonomy"]["operator_policy"], "internal_only")
            self.assertEqual(status["autonomy"]["classification_source"], "operator_policy")
            self.assertEqual(len(gated_events), 1)
            self.assertEqual(gated_events[0]["payload"]["reason"], "waiting_next_control")
            self.assertEqual(gated_events[0]["payload"]["mode"], "triage")
            self.assertEqual(gated_events[0]["payload"]["routed_to"], "codex_followup")

    def test_write_status_keeps_slice_ambiguity_operator_stop_gated_when_based_work_is_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 188\n"
                "REASON_CODE: slice_ambiguity\n"
                "OPERATOR_POLICY: gate_24h\n"
                "DECISION_CLASS: next_slice_selection\n"
                "DECISION_REQUIRED: choose exact next slice\n"
                "BASED_ON_WORK: work/4/19/2026-04-19-legacy-active-context-summary-hint-basis-backfill.md\n",
                encoding="utf-8",
            )
            (state_dir / "job-188.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-188",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/19/2026-04-19-legacy-active-context-summary-hint-basis-backfill.md",
                        "artifact_hash": "hash-188",
                        "round": 1,
                        "verify_result": "passed_by_feedback",
                        "updated_at": 100.0,
                        "verify_completed_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            gated_events = [event for event in events if event.get("event_type") == "control_operator_gated"]
            stale_events = [event for event in events if event.get("event_type") == "control_operator_stale_ignored"]

            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["autonomy"]["mode"], "triage")
            self.assertEqual(status["autonomy"]["block_reason"], "slice_ambiguity")
            self.assertEqual(len(gated_events), 1)
            self.assertEqual(len(stale_events), 0)

    def test_write_status_keeps_truth_sync_operator_stop_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 189\n"
                "REASON_CODE: truth_sync_required\n"
                "OPERATOR_POLICY: immediate_publish\n"
                "DECISION_CLASS: operator_only\n"
                "DECISION_REQUIRED: confirm truth sync\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["control"]["active_control_status"], "needs_operator")
            self.assertEqual(status["control"]["active_control_seq"], 189)
            self.assertEqual(status["autonomy"]["mode"], "needs_operator")
            self.assertEqual(status["autonomy"]["block_reason"], "truth_sync_required")
            self.assertEqual(status["autonomy"]["operator_policy"], "immediate_publish")

    def test_write_status_missing_structured_operator_metadata_stays_fail_safe_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 190\n\nReason:\n- slice_ambiguity\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["control"]["active_control_status"], "needs_operator")
            self.assertEqual(status["autonomy"]["mode"], "needs_operator")
            self.assertEqual(status["autonomy"]["classification_source"], "metadata_missing_fallback")

    def test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            logs_dir = pipeline_dir / "logs" / "experimental"
            state_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)
            handoff_path = pipeline_dir / "claude_handoff.md"
            handoff_path.write_text(
                "STATUS: implement\nCONTROL_SEQ: 154\n",
                encoding="utf-8",
            )
            handoff_sha = hashlib.sha256(handoff_path.read_bytes()).hexdigest()
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CLAUDE_ACTIVE",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 154,
                    }
                ),
                encoding="utf-8",
            )
            handoff_logged_at = time.time()
            os.utime(handoff_path, (handoff_logged_at - 5.0, handoff_logged_at - 5.0))
            (logs_dir / "raw.jsonl").write_text(
                json.dumps(
                    {
                        "event": "codex_blocked_triage_notify",
                        "path": str(handoff_path),
                        "blocked_reason": "handoff_already_completed",
                        "blocked_fingerprint": "dup-154",
                        "handoff_sha": handoff_sha,
                        "at": handoff_logged_at,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    side_effect=lambda lane_name: {
                        "alive": True,
                        "pid": {"Claude": 11, "Codex": 12, "Gemini": 13}.get(lane_name),
                        "attachable": True,
                        "pane_id": "%1",
                    },
                ),
                mock.patch(
                    "pipeline_runtime.supervisor.build_lane_read_models",
                    return_value={
                        "Claude": {
                            "state": "WORKING",
                            "note": "seq 154",
                            "accepted_task": {"job_id": "job-42", "control_seq": 154, "attempt": 1},
                            "last_event_at": "2026-04-15T13:22:16.919339Z",
                            "last_heartbeat_at": "2026-04-15T13:22:16.919339Z",
                        }
                    },
                ),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            claude = next(lane for lane in status["lanes"] if lane["name"] == "Claude")
            claude_hint = json.loads(supervisor._task_hint_path("Claude").read_text(encoding="utf-8"))
            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(claude["state"], "READY")
            self.assertEqual(claude["note"], "waiting_next_control")
            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["control"]["active_control_seq"], -1)
            self.assertEqual(
                status["compat"]["control_slots"]["active"]["status"],
                "implement",
            )
            self.assertFalse(claude_hint["active"])
            self.assertEqual(claude_hint["inactive_reason"], "duplicate_handoff")
            duplicate_events = [event for event in events if event.get("event_type") == "control_duplicate_ignored"]
            self.assertEqual(len(duplicate_events), 1)
            self.assertEqual(duplicate_events[0]["payload"]["control_seq"], 154)
            self.assertEqual(duplicate_events[0]["payload"]["routed_to"], "codex_triage")

    def test_write_status_surfaces_duplicate_handoff_from_canonical_blocked_triage_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            logs_dir = pipeline_dir / "logs" / "experimental"
            state_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)
            handoff_path = pipeline_dir / "claude_handoff.md"
            handoff_path.write_text(
                "STATUS: implement\nCONTROL_SEQ: 154\n",
                encoding="utf-8",
            )
            handoff_sha = hashlib.sha256(handoff_path.read_bytes()).hexdigest()
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CLAUDE_ACTIVE",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 154,
                    }
                ),
                encoding="utf-8",
            )
            handoff_logged_at = time.time()
            os.utime(handoff_path, (handoff_logged_at - 5.0, handoff_logged_at - 5.0))
            (logs_dir / "raw.jsonl").write_text(
                json.dumps(
                    {
                        "event": "verify_blocked_triage_notify",
                        "path": str(handoff_path),
                        "blocked_reason": "handoff_already_completed",
                        "blocked_fingerprint": "dup-154",
                        "handoff_sha": handoff_sha,
                        "at": handoff_logged_at,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor.adapter,
                    "lane_health",
                    side_effect=lambda lane_name: {
                        "alive": True,
                        "pid": {"Claude": 11, "Codex": 12, "Gemini": 13}.get(lane_name),
                        "attachable": True,
                        "pane_id": "%1",
                    },
                ),
                mock.patch(
                    "pipeline_runtime.supervisor.build_lane_read_models",
                    return_value={
                        "Claude": {
                            "state": "WORKING",
                            "note": "seq 154",
                            "accepted_task": {"job_id": "job-42", "control_seq": 154, "attempt": 1},
                            "last_event_at": "2026-04-15T13:22:16.919339Z",
                            "last_heartbeat_at": "2026-04-15T13:22:16.919339Z",
                        }
                    },
                ),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            claude = next(lane for lane in status["lanes"] if lane["name"] == "Claude")
            claude_hint = json.loads(supervisor._task_hint_path("Claude").read_text(encoding="utf-8"))
            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(claude["state"], "READY")
            self.assertEqual(claude["note"], "waiting_next_control")
            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["control"]["active_control_seq"], -1)
            self.assertEqual(
                status["compat"]["control_slots"]["active"]["status"],
                "implement",
            )
            self.assertFalse(claude_hint["active"])
            self.assertEqual(claude_hint["inactive_reason"], "duplicate_handoff")
            duplicate_events = [event for event in events if event.get("event_type") == "control_duplicate_ignored"]
            self.assertEqual(len(duplicate_events), 1)
            self.assertEqual(duplicate_events[0]["payload"]["control_seq"], 154)
            self.assertEqual(duplicate_events[0]["payload"]["routed_to"], "codex_triage")

    def test_write_status_ignores_operator_stop_when_referenced_work_is_already_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "operator_request.md").write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 155",
                        "",
                        "- work/4/15/2026-04-15-review-queue-action-vocabulary-reject-defer.md",
                        "- work/4/15/2026-04-15-review-queue-source-message-review-outcome-visibility.md",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "OPERATOR_WAIT",
                        "entered_at": 1.0,
                        "reason": "operator_request_updated",
                        "active_control_file": "operator_request.md",
                        "active_control_seq": 155,
                    }
                ),
                encoding="utf-8",
            )
            for job_id, artifact_path, updated_at in [
                (
                    "job-reject-defer",
                    str(root / "work" / "4" / "15" / "2026-04-15-review-queue-action-vocabulary-reject-defer.md"),
                    100.0,
                ),
                (
                    "job-source-message",
                    str(root / "work" / "4" / "15" / "2026-04-15-review-queue-source-message-review-outcome-visibility.md"),
                    110.0,
                ),
            ]:
                artifact = Path(artifact_path)
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text("# work\n", encoding="utf-8")
                (state_dir / f"{job_id}.json").write_text(
                    json.dumps(
                        {
                            "job_id": job_id,
                            "status": "VERIFY_DONE",
                            "artifact_path": artifact_path,
                            "artifact_hash": f"hash-{job_id}",
                            "round": 1,
                            "verify_result": "passed_by_feedback",
                            "updated_at": updated_at,
                            "verify_completed_at": updated_at,
                        }
                    ),
                    encoding="utf-8",
                )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 4242}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
                supervisor._record_status_events(status)

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            stale_events = [event for event in events if event.get("event_type") == "control_operator_stale_ignored"]

            self.assertEqual(status["control"]["active_control_status"], "none")
            self.assertEqual(status["control"]["active_control_seq"], -1)
            self.assertEqual(status["compat"]["control_slots"]["active"]["file"], "operator_request.md")
            self.assertEqual(len(stale_events), 1)
            self.assertEqual(stale_events[0]["payload"]["control_seq"], 155)
            self.assertEqual(stale_events[0]["payload"]["reason"], "verified_blockers_resolved")

    def test_launch_runtime_spawns_lanes_and_watcher_directly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with (
                mock.patch.object(supervisor, "_find_cli_bin", side_effect=lambda name: f"/usr/bin/{name}"),
                mock.patch.object(supervisor.adapter, "kill_session", return_value=True),
                mock.patch.object(supervisor.adapter, "create_scaffold", return_value={"Claude": "%1", "Codex": "%2", "Gemini": "%3"}),
                mock.patch.object(supervisor.adapter, "spawn_lane", return_value=True) as spawn_lane,
                mock.patch.object(supervisor.adapter, "pane_for_lane", side_effect=lambda lane: {"pane_id": {"Claude": "%1", "Codex": "%2", "Gemini": "%3"}[lane]}),
                mock.patch.object(supervisor.adapter, "spawn_watcher", return_value={"pane_id": "%9", "pid": 12345, "window_name": "watcher-exp"}) as spawn_watcher,
                mock.patch("pipeline_runtime.supervisor.resolve_project_runtime_file", side_effect=lambda _project, name: root / name),
                mock.patch.object(supervisor, "_start_token_collector"),
                mock.patch.object(supervisor, "_terminate_repo_watchers"),
            ):
                for helper in ("watcher_core.py", "pipeline-watcher-v3-logged.sh", "token_collector.py"):
                    (root / helper).write_text("#!/bin/bash\n", encoding="utf-8")
                supervisor._launch_runtime()

            self.assertTrue(supervisor._runtime_started)
            self.assertGreaterEqual(spawn_lane.call_count, 3)
            self.assertTrue(any("lane-wrapper" in str(call.args[1]) for call in spawn_lane.call_args_list))
            spawn_watcher.assert_called()
            self.assertIn(
                "PIPELINE_RUNTIME_DISABLE_EXPORTER=1",
                str(spawn_watcher.call_args.kwargs.get("shell_command") or ""),
            )
            self.assertIn(
                f"PIPELINE_RUNTIME_RUN_ID={supervisor.run_id}",
                str(spawn_watcher.call_args.kwargs.get("shell_command") or ""),
            )
            experimental_pid = root / ".pipeline" / "experimental.pid"
            self.assertTrue(experimental_pid.exists())

    def test_runtime_stays_starting_until_all_enabled_lanes_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 101}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11},
                            {"name": "Codex", "state": "BOOTING", "attachable": True, "pid": 12},
                        ],
                        {
                            "Claude": {"state": "READY", "note": ""},
                            "Codex": {"state": "BOOTING", "note": ""},
                        },
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
            self.assertEqual(status["runtime_state"], "STARTING")

    def test_verify_prompt_prefers_gemini_before_operator_for_slice_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            prompt = supervisor._prompt_templates()["verify"]

            self.assertIn("next-slice ambiguity", prompt)
            self.assertIn(".pipeline/gemini_request.md before .pipeline/operator_request.md", prompt)
            self.assertIn("real operator-only decision", prompt)
            self.assertIn("after 3+ same-day same-family docs-only truth-sync rounds", prompt)

    def test_followup_prompt_only_uses_operator_after_inconclusive_gemini_advice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            prompt = supervisor._prompt_templates()["followup"]

            self.assertIn("after Gemini advice", prompt)
            self.assertIn(".pipeline/operator_request.md", prompt)
            self.assertIn("no truthful exact slice", prompt)

    def test_prompt_templates_follow_role_bound_prompt_owners_when_lanes_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(
                root,
                selected_agents=["Claude", "Codex", "Gemini"],
                implement="Codex",
                verify="Claude",
                advisory="Gemini",
                advisory_enabled=True,
            )
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            implement_prompt = supervisor._prompt_templates()["implement"]
            verify_prompt = supervisor._prompt_templates()["verify"]
            advisory_prompt = supervisor._prompt_templates()["advisory"]
            followup_prompt = supervisor._prompt_templates()["followup"]

            self.assertIn("OWNER: Codex", implement_prompt)
            self.assertIn("- AGENTS.md", implement_prompt)
            self.assertNotIn("work/README.md", implement_prompt)
            self.assertNotIn("OWNER: Claude", implement_prompt)
            self.assertIn("do only the handoff; if done, leave one `/work` closeout and stop", implement_prompt)
            self.assertIn("no commit, push, branch/PR publish, or next-slice choice", implement_prompt)
            self.assertIn("OWNER: Claude", verify_prompt)
            self.assertIn("- CLAUDE.md", verify_prompt)
            self.assertIn("keep `READ_FIRST` to the listed verify-owner root doc only", verify_prompt)
            self.assertIn("keep its `READ_FIRST` to the implement-owner root doc only", verify_prompt)
            self.assertIn("verify the latest `/work`, update `/verify`, then write exactly one next control", verify_prompt)
            self.assertNotIn("work/README.md", verify_prompt)
            self.assertNotIn("verify/README.md", verify_prompt)
            self.assertIn("OWNER: Claude", followup_prompt)
            self.assertIn("- CLAUDE.md", followup_prompt)
            self.assertIn("keep `READ_FIRST` to the listed verify-owner root doc only", followup_prompt)
            self.assertIn("keep its `READ_FIRST` to the implement-owner root doc only", followup_prompt)
            self.assertIn("turn the advisory into exactly one next control", followup_prompt)
            self.assertNotIn("verify/README.md", followup_prompt)
            self.assertIn("OWNER: Gemini", advisory_prompt)
            self.assertIn("- @GEMINI.md", advisory_prompt)
            self.assertIn("keep `READ_FIRST` to the listed advisory-owner root doc only", advisory_prompt)
            self.assertIn("if the request cites exact shipped docs or a current runtime-doc family", advisory_prompt)
            self.assertIn("do not widen to `docs/superpowers/**`, `plandoc/**`, or historical planning docs", advisory_prompt)

    def test_session_loss_transitions_runtime_to_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": True, "pid": 101}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [{"name": "Claude", "state": "READY", "attachable": True, "pid": 11}],
                        {"Claude": {"state": "READY", "note": ""}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertEqual(status["degraded_reason"], "session_missing")
            self.assertIn("session_missing", list(status.get("degraded_reasons") or []))

    def test_session_loss_stays_degraded_even_when_watcher_is_also_gone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [{"name": "Claude", "state": "READY", "attachable": True, "pid": 11}],
                        {"Claude": {"state": "READY", "note": ""}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertEqual(status["degraded_reason"], "session_missing")
            self.assertIn("session_missing", list(status.get("degraded_reasons") or []))

    def test_session_loss_keeps_session_missing_as_representative_reason_over_lane_recovery_failures(self) -> None:
        """When the tmux session disappears and lane recovery also fails for every
        enabled lane, `session_missing` is the root cause and must stay the
        representative `degraded_reason`. The per-lane `*_recovery_failed` entries
        are secondary evidence and must remain visible in `degraded_reasons`."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(supervisor.adapter, "kill_session", return_value=True),
                mock.patch.object(
                    supervisor.adapter,
                    "create_scaffold",
                    side_effect=RuntimeError("tmux create_scaffold failed"),
                ),
                mock.patch.object(supervisor.adapter, "restart_lane", return_value=False),
                mock.patch.object(supervisor, "_terminate_repo_watchers"),
                mock.patch.object(supervisor, "_lane_shell_command", return_value="run-lane"),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "BROKEN", "attachable": False, "pid": None, "note": "exit:-15"},
                            {"name": "Codex", "state": "BROKEN", "attachable": False, "pid": None, "note": "exit:-15"},
                            {"name": "Gemini", "state": "BROKEN", "attachable": False, "pid": None, "note": "exit:-15"},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertEqual(status["degraded_reason"], "session_missing")
            reasons = list(status.get("degraded_reasons") or [])
            self.assertEqual(reasons[0], "session_missing")
            for lane_failure in ("claude_recovery_failed", "codex_recovery_failed", "gemini_recovery_failed"):
                self.assertIn(lane_failure, reasons)

    def test_session_loss_recreates_scaffold_once_before_lane_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            pane_ids = {"Claude": "%1", "Codex": "%2", "Gemini": "%3"}
            with (
                mock.patch.object(supervisor, "_find_cli_bin", side_effect=lambda name: f"/usr/bin/{name}"),
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(supervisor.adapter, "kill_session", return_value=True),
                mock.patch.object(supervisor.adapter, "create_scaffold", return_value=pane_ids) as create_scaffold,
                mock.patch.object(supervisor.adapter, "spawn_lane", return_value=True) as spawn_lane,
                mock.patch.object(supervisor.adapter, "pane_for_lane", side_effect=lambda lane: {"pane_id": pane_ids[lane]}),
                mock.patch.object(
                    supervisor.adapter,
                    "spawn_watcher",
                    return_value={"pane_id": "%9", "pid": 12345, "window_name": "watcher-exp"},
                ) as spawn_watcher,
                mock.patch.object(supervisor.adapter, "restart_lane", return_value=True) as restart_lane,
                mock.patch.object(supervisor, "_start_token_collector"),
                mock.patch.object(supervisor, "_terminate_repo_watchers"),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "BROKEN", "attachable": False, "pid": None, "note": "pane_dead"},
                            {"name": "Codex", "state": "BROKEN", "attachable": False, "pid": None, "note": "pane_dead"},
                            {"name": "Gemini", "state": "BROKEN", "attachable": False, "pid": None, "note": "pane_dead"},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
                mock.patch("pipeline_runtime.supervisor.resolve_project_runtime_file", side_effect=lambda _project, name: root / name),
            ):
                status = supervisor._write_status()

            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertEqual(status["degraded_reason"], "session_missing")
            create_scaffold.assert_called_once()
            self.assertGreaterEqual(spawn_lane.call_count, 3)
            spawn_watcher.assert_called_once()
            restart_lane.assert_not_called()
            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            event_types = [event.get("event_type") for event in events]
            self.assertIn("session_recovery_started", event_types)
            self.assertIn("session_recovery_completed", event_types)

    def test_session_recovery_budget_resets_only_after_stable_alive_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._session_recovery_attempts = 1
            supervisor._session_recovery_last_started_at = 100.0

            with mock.patch("pipeline_runtime.supervisor.time.time", return_value=399.0):
                supervisor._maybe_reset_session_recovery_budget(True)

            self.assertEqual(supervisor._session_recovery_attempts, 1)

            with mock.patch("pipeline_runtime.supervisor.time.time", return_value=401.0):
                supervisor._maybe_reset_session_recovery_budget(True)

            self.assertEqual(supervisor._session_recovery_attempts, 0)
            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(events[-1]["event_type"], "session_recovery_budget_reset")

    def test_session_loss_does_not_recreate_scaffold_after_brief_alive_budget_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            pane_ids = {"Claude": "%1", "Codex": "%2", "Gemini": "%3"}
            broken_lanes = (
                [
                    {"name": "Claude", "state": "BROKEN", "attachable": False, "pid": None, "note": "pane_dead"},
                    {"name": "Codex", "state": "BROKEN", "attachable": False, "pid": None, "note": "pane_dead"},
                    {"name": "Gemini", "state": "BROKEN", "attachable": False, "pid": None, "note": "pane_dead"},
                ],
                {"Claude": {}, "Codex": {}, "Gemini": {}},
            )
            ready_lanes = (
                [
                    {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                    {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                    {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                ],
                {"Claude": {}, "Codex": {}, "Gemini": {}},
            )
            with (
                mock.patch.object(supervisor, "_find_cli_bin", side_effect=lambda name: f"/usr/bin/{name}"),
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", side_effect=[False, True, False]),
                mock.patch.object(supervisor.adapter, "kill_session", return_value=True),
                mock.patch.object(supervisor.adapter, "create_scaffold", return_value=pane_ids) as create_scaffold,
                mock.patch.object(supervisor.adapter, "spawn_lane", return_value=True),
                mock.patch.object(supervisor.adapter, "pane_for_lane", side_effect=lambda lane: {"pane_id": pane_ids[lane]}),
                mock.patch.object(
                    supervisor.adapter,
                    "spawn_watcher",
                    return_value={"pane_id": "%9", "pid": 12345, "window_name": "watcher-exp"},
                ),
                mock.patch.object(supervisor.adapter, "restart_lane", return_value=False),
                mock.patch.object(supervisor, "_start_token_collector"),
                mock.patch.object(supervisor, "_terminate_repo_watchers"),
                mock.patch.object(supervisor, "_build_lane_statuses", side_effect=[broken_lanes, ready_lanes, broken_lanes]),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
                mock.patch(
                    "pipeline_runtime.supervisor.resolve_project_runtime_file",
                    side_effect=lambda _project, name: root / name,
                ),
            ):
                first_status = supervisor._write_status()
                alive_status = supervisor._write_status()
                second_missing_status = supervisor._write_status()

            self.assertEqual(first_status["degraded_reason"], "session_missing")
            self.assertEqual(alive_status["degraded_reason"], "")
            self.assertEqual(second_missing_status["degraded_reason"], "session_missing")
            self.assertIn("session_recovery_exhausted", list(second_missing_status.get("degraded_reasons") or []))
            self.assertEqual(second_missing_status["automation_health"], "needs_operator")
            create_scaffold.assert_called_once()
            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            event_types = [event.get("event_type") for event in events]
            self.assertEqual(event_types.count("session_recovery_started"), 1)
            self.assertEqual(event_types.count("session_recovery_completed"), 1)
            self.assertEqual(event_types.count("session_recovery_exhausted"), 1)

    def test_session_loss_failed_recovery_is_bounded_without_lane_restart_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(supervisor.adapter, "kill_session", return_value=True),
                mock.patch.object(
                    supervisor.adapter,
                    "create_scaffold",
                    side_effect=RuntimeError("tmux create_scaffold failed"),
                ) as create_scaffold,
                mock.patch.object(supervisor.adapter, "restart_lane", return_value=False) as restart_lane,
                mock.patch.object(supervisor, "_terminate_repo_watchers"),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "BROKEN", "attachable": False, "pid": None, "note": "pane_dead"},
                            {"name": "Codex", "state": "BROKEN", "attachable": False, "pid": None, "note": "pane_dead"},
                            {"name": "Gemini", "state": "BROKEN", "attachable": False, "pid": None, "note": "pane_dead"},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                first_status = supervisor._write_status()
                second_status = supervisor._write_status()

            self.assertEqual(first_status["degraded_reason"], "session_missing")
            self.assertEqual(second_status["degraded_reason"], "session_missing")
            create_scaffold.assert_called_once()
            self.assertEqual(restart_lane.call_count, 5)
            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            event_types = [event.get("event_type") for event in events]
            self.assertEqual(event_types.count("session_recovery_started"), 1)
            self.assertEqual(event_types.count("session_recovery_failed"), 1)

    def test_session_loss_degrades_even_if_lane_health_has_already_dropped_to_off(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True
            with (
                mock.patch.object(supervisor, "_watcher_status", return_value={"alive": False, "pid": None}),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "OFF", "attachable": False, "pid": None},
                            {"name": "Codex", "state": "OFF", "attachable": False, "pid": None},
                        ],
                        {"Claude": {}, "Codex": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(supervisor, "_build_artifacts", return_value={"latest_work": {}, "latest_verify": {}}),
            ):
                status = supervisor._write_status()
            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertIn("session_missing", list(status.get("degraded_reasons") or []))

    def test_claude_post_accept_breakage_blocks_blind_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            lane = {"name": "Claude", "state": "BROKEN"}
            lane_model = {
                "accepted_task": {"job_id": "job-7", "control_seq": 21, "attempt": 1},
            }
            with mock.patch.object(supervisor.adapter, "restart_lane") as restart_lane:
                reason = supervisor._maybe_recover_lane(
                    lane,
                    lane_model=lane_model,
                    active_round={"job_id": "job-7", "state": "VERIFYING"},
                )
            self.assertEqual(reason, "claude_interrupted_post_accept")
            restart_lane.assert_not_called()

    def test_pre_accept_wrapper_exit_note_consumes_retry_budget_and_restarts(self) -> None:
        """Wrapper-surfaced pre-accept breakage (``exit:<code>``, ``pane_dead``,
        ``heartbeat_timeout``) must fall through to the bounded restart path and
        emit ``recovery_started``/``recovery_completed`` so the fault-check gate's
        synthetic Claude kill recovers within retry budget."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            lane = {"name": "Claude", "state": "BROKEN", "note": "exit:-15"}
            lane_model = {"accepted_task": None}
            with (
                mock.patch.object(supervisor.adapter, "restart_lane", return_value=True) as restart_lane,
                mock.patch.object(supervisor, "_lane_shell_command", return_value="run-claude") as lane_shell_command,
                mock.patch.object(supervisor, "_append_event") as append_event,
            ):
                reason = supervisor._maybe_recover_lane(
                    lane,
                    lane_model=lane_model,
                    active_round=None,
                )
            self.assertEqual(reason, "")
            lane_shell_command.assert_called_once_with("Claude")
            restart_lane.assert_called_once_with("Claude", "run-claude")
            self.assertEqual(supervisor._lane_restart_counts["Claude"], 1)
            event_types = [call.args[0] for call in append_event.call_args_list]
            self.assertIn("recovery_started", event_types)
            self.assertIn("recovery_completed", event_types)

    def test_failed_pre_accept_restart_consumes_retry_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            lane = {"name": "Claude", "state": "BROKEN", "note": "exit:-15"}
            lane_model = {"accepted_task": None}
            with (
                mock.patch.object(supervisor.adapter, "restart_lane", return_value=False) as restart_lane,
                mock.patch.object(supervisor, "_lane_shell_command", return_value="run-claude"),
            ):
                first_reason = supervisor._maybe_recover_lane(
                    lane,
                    lane_model=lane_model,
                    active_round=None,
                )
                second_reason = supervisor._maybe_recover_lane(
                    lane,
                    lane_model=lane_model,
                    active_round=None,
                )
            self.assertEqual(first_reason, "claude_recovery_failed")
            self.assertEqual(second_reason, "claude_broken")
            restart_lane.assert_called_once_with("Claude", "run-claude")

    def test_auth_failure_breakage_blocks_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            lane = {"name": "Claude", "state": "BROKEN", "note": "auth_login_required"}
            lane_model = {"accepted_task": None, "failure_reason": "auth_login_required"}
            with mock.patch.object(supervisor.adapter, "restart_lane") as restart_lane:
                reason = supervisor._maybe_recover_lane(
                    lane,
                    lane_model=lane_model,
                    active_round=None,
                )
            self.assertEqual(reason, "claude_auth_login_required")
            restart_lane.assert_not_called()

    def test_write_status_marks_runtime_degraded_on_active_lane_auth_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 17\n",
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps(
                    {
                        "state": "CLAUDE_ACTIVE",
                        "entered_at": 1.0,
                        "active_control_file": ".pipeline/claude_handoff.md",
                        "active_control_seq": 17,
                    }
                ),
                encoding="utf-8",
            )
            supervisor = RuntimeSupervisor(root, start_runtime=False)

            def lane_health(lane_name: str) -> dict[str, object]:
                return {"alive": True, "pid": 5000, "attachable": True, "pane_id": f"%{lane_name}"}

            def capture_tail(lane_name: str, lines: int = 60) -> str:
                if lane_name == "Claude":
                    return (
                        "API Error: 401\n"
                        '{"error":{"type":"authentication_error","message":"Invalid authentication credentials"}}\n'
                        "Please run /login\n"
                    )
                return ""

            with (
                mock.patch.object(supervisor.adapter, "lane_health", side_effect=lane_health),
                mock.patch.object(supervisor.adapter, "capture_tail", side_effect=capture_tail),
                mock.patch.object(supervisor.adapter, "session_exists", return_value=True),
            ):
                status = supervisor._write_status()

            claude = next(lane for lane in status["lanes"] if lane["name"] == "Claude")
            self.assertEqual(claude["state"], "BROKEN")
            self.assertEqual(claude["note"], "auth_login_required")
            self.assertEqual(status["runtime_state"], "DEGRADED")
            self.assertIn("claude_auth_login_required", list(status.get("degraded_reasons") or []))

    def test_codex_pre_completion_breakage_restarts_within_retry_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            lane = {"name": "Codex", "state": "BROKEN"}
            lane_model = {"accepted_task": None}
            with (
                mock.patch.object(supervisor.adapter, "restart_lane", return_value=True) as restart_lane,
                mock.patch.object(supervisor, "_lane_shell_command", return_value="run-codex") as lane_shell_command,
            ):
                reason = supervisor._maybe_recover_lane(
                    lane,
                    lane_model=lane_model,
                    active_round={"job_id": "job-8", "state": "VERIFY_PENDING"},
                )
            self.assertEqual(reason, "")
            lane_shell_command.assert_called_once_with("Codex")
            restart_lane.assert_called_once_with("Codex", "run-codex")
            self.assertEqual(supervisor._lane_restart_counts["Codex"], 1)

    def test_codex_breakage_stops_after_retry_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._lane_restart_counts["Codex"] = 2
            reason = supervisor._maybe_recover_lane(
                {"name": "Codex", "state": "BROKEN"},
                lane_model={"accepted_task": None},
                active_round={"job_id": "job-9", "state": "VERIFY_PENDING"},
            )
            self.assertEqual(reason, "codex_broken")

    def test_lane_vendor_command_prefers_env_override_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, run_id="run-123", start_runtime=False)
            with mock.patch.dict(
                "os.environ",
                {
                    "PIPELINE_RUNTIME_LANE_COMMAND_CODEX": "python3 fake.py --project-root {project_root_shlex} --lane {lane} --run {run_id}",
                },
                clear=False,
            ):
                command = supervisor._lane_vendor_command("Codex")
            self.assertIn("python3 fake.py", command)
            self.assertIn("--project-root", command)
            self.assertIn(str(root), command)
            self.assertIn("--lane Codex", command)
            self.assertIn("--run run-123", command)

    def test_lane_vendor_command_uses_yolo_for_gemini(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, start_runtime=False)
            with mock.patch.object(supervisor, "_find_cli_bin", side_effect=lambda name: f"/usr/bin/{name}"):
                command = supervisor._lane_vendor_command("Gemini")
            self.assertEqual(command, 'exec "/usr/bin/gemini" --yolo')

    def test_lane_shell_command_carries_pythonpath_into_tmux_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            supervisor = RuntimeSupervisor(root, run_id="run-456", start_runtime=False)
            with mock.patch.dict("os.environ", {"PYTHONPATH": "/tmp/fake-path"}, clear=False):
                command = supervisor._lane_shell_command("Codex")
            self.assertIn("env PYTHONPATH=/tmp/fake-path", command)
            self.assertIn(f"PROJECT_ROOT={root}", command)
            self.assertIn("pipeline_runtime.cli lane-wrapper", command)

    def test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            state_dir = pipeline_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            old_run_id = "20260418T010203Z-p999"
            old_run_dir = pipeline_dir / "runs" / old_run_id
            old_run_dir.mkdir(parents=True, exist_ok=True)
            # canonical surface from the prior supervisor still says STOPPED.
            (old_run_dir / "status.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "run_id": old_run_id,
                        "current_run_id": old_run_id,
                        "runtime_state": "STOPPED",
                        "active_round": None,
                    }
                ),
                encoding="utf-8",
            )
            current_pid = os.getpid()
            current_fingerprint = _read_proc_starttime_fingerprint(current_pid)
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": old_run_id,
                        "status_path": f".pipeline/runs/{old_run_id}/status.json",
                        "events_path": f".pipeline/runs/{old_run_id}/events.jsonl",
                        "watcher_pid": current_pid,
                        "watcher_fingerprint": current_fingerprint,
                    }
                ),
                encoding="utf-8",
            )
            # mark the watcher alive via the current python pid so _watcher_status
            # and the supervisor's run_id inheritance both observe a live owner.
            (pipeline_dir / "experimental.pid").write_text(str(current_pid), encoding="utf-8")
            (state_dir / "job-replay-1.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-replay-1",
                        "run_id": old_run_id,
                        "status": "VERIFY_PENDING",
                        "artifact_path": "work/4/18/replay.md",
                        "artifact_hash": "replay-hash",
                        "round": 5,
                        "updated_at": 200.0,
                        "last_activity_at": 200.0,
                    }
                ),
                encoding="utf-8",
            )

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            self.assertEqual(supervisor.run_id, old_run_id)
            self.assertEqual(supervisor.status_path, old_run_dir / "status.json")

            with (
                mock.patch.object(supervisor.adapter, "session_exists", return_value=False),
                mock.patch.object(
                    supervisor,
                    "_build_lane_statuses",
                    return_value=(
                        [
                            {"name": "Claude", "state": "READY", "attachable": True, "pid": 11, "note": ""},
                            {"name": "Codex", "state": "READY", "attachable": True, "pid": 12, "note": ""},
                            {"name": "Gemini", "state": "READY", "attachable": True, "pid": 13, "note": ""},
                        ],
                        {"Claude": {}, "Codex": {}, "Gemini": {}},
                    ),
                ),
                mock.patch("pipeline_runtime.supervisor.build_lane_read_models", return_value={}),
                mock.patch.object(
                    supervisor,
                    "_build_artifacts",
                    return_value={"latest_work": {}, "latest_verify": {}},
                ),
            ):
                status = supervisor._write_status()

            self.assertNotEqual(status["runtime_state"], "STOPPED")
            self.assertEqual(status["run_id"], old_run_id)
            self.assertIsNotNone(status["active_round"])
            self.assertEqual(status["active_round"]["state"], "VERIFY_PENDING")
            self.assertEqual(status["active_round"]["job_id"], "job-replay-1")
            canonical_status = json.loads((old_run_dir / "status.json").read_text(encoding="utf-8"))
            self.assertNotEqual(canonical_status["runtime_state"], "STOPPED")
            self.assertEqual(
                canonical_status["active_round"]["state"], "VERIFY_PENDING"
            )

    def test_watcher_source_change_restarts_watcher_without_operator_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            pid_path = pipeline_dir / "experimental.pid"
            pid_path.write_text(str(os.getpid()), encoding="utf-8")
            os.utime(pid_path, (1.0, 1.0))

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            supervisor._runtime_started = True

            with (
                mock.patch.object(supervisor, "_terminate_pid_file") as terminate_pid,
                mock.patch.object(
                    supervisor,
                    "_spawn_experimental_watcher",
                    return_value={"pid": 9999, "pane_id": "%99", "window_name": "watcher-exp"},
                ) as spawn_watcher,
                mock.patch.object(supervisor, "_write_current_run_pointer") as write_pointer,
            ):
                self.assertTrue(supervisor._maybe_restart_watcher_for_source_change())
                self.assertFalse(supervisor._maybe_restart_watcher_for_source_change())

            terminate_pid.assert_called_once_with(pid_path)
            spawn_watcher.assert_called_once()
            write_pointer.assert_called_once()

            events = [
                json.loads(line)
                for line in supervisor.events_path.read_text(encoding="utf-8").splitlines()
            ]
            event_types = [event.get("event_type") for event in events]
            self.assertIn("watcher_self_restart_started", event_types)
            self.assertIn("watcher_self_restart_completed", event_types)
            completed = next(
                event for event in events if event.get("event_type") == "watcher_self_restart_completed"
            )
            self.assertEqual(completed["payload"]["reason"], "watcher_source_updated")
            self.assertEqual(completed["payload"]["new_pid"], 9999)

    def test_supervisor_skips_run_id_inheritance_when_watcher_pid_is_dead(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            old_run_id = "20260418T010203Z-p888"
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": old_run_id,
                        "status_path": f".pipeline/runs/{old_run_id}/status.json",
                        "watcher_pid": os.getpid(),
                    }
                ),
                encoding="utf-8",
            )
            # experimental.pid points to a pid that is not alive so inheritance
            # must fall back to a freshly generated run_id.
            (pipeline_dir / "experimental.pid").write_text("0", encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            self.assertNotEqual(supervisor.run_id, old_run_id)

    def test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            old_run_id = "20260418T010203Z-p777"
            # legacy pointer with no owner field must NOT trigger inheritance,
            # even when experimental.pid is alive — the owner-match gate is
            # the new minimum bar for adopting a prior run id.
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": old_run_id,
                        "status_path": f".pipeline/runs/{old_run_id}/status.json",
                    }
                ),
                encoding="utf-8",
            )
            (pipeline_dir / "experimental.pid").write_text(str(os.getpid()), encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            self.assertNotEqual(supervisor.run_id, old_run_id)

    def test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_mismatches_live_watcher(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            old_run_id = "20260418T010203Z-p666"
            current_pid = os.getpid()
            # current_run.json claims a different owner pid than the live
            # experimental.pid, which means the pointer belongs to a stale
            # watcher process that is no longer the current owner. Supervisor
            # must refuse to inherit and fall back to a fresh run id.
            other_pid = current_pid + 1 if current_pid > 1 else current_pid + 2
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": old_run_id,
                        "status_path": f".pipeline/runs/{old_run_id}/status.json",
                        "watcher_pid": other_pid,
                        "watcher_fingerprint": _read_proc_starttime_fingerprint(current_pid),
                    }
                ),
                encoding="utf-8",
            )
            (pipeline_dir / "experimental.pid").write_text(str(current_pid), encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            self.assertNotEqual(supervisor.run_id, old_run_id)

    def test_supervisor_skips_run_id_inheritance_when_pointer_fingerprint_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            old_run_id = "20260418T010203Z-p444"
            # pid matches the live watcher exactly, but the pointer omits the
            # watcher_fingerprint field. supervisor must still refuse to
            # inherit because the same pid alone cannot prove the live
            # watcher is the same process instance the pointer was written
            # for.
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": old_run_id,
                        "status_path": f".pipeline/runs/{old_run_id}/status.json",
                        "watcher_pid": os.getpid(),
                    }
                ),
                encoding="utf-8",
            )
            (pipeline_dir / "experimental.pid").write_text(str(os.getpid()), encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            self.assertNotEqual(supervisor.run_id, old_run_id)

    def test_supervisor_skips_run_id_inheritance_when_pointer_fingerprint_mismatches_live_watcher(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            old_run_id = "20260418T010203Z-p333"
            current_pid = os.getpid()
            real_fingerprint = _read_proc_starttime_fingerprint(current_pid)
            # pointer claims a fingerprint from an older process instance
            # that happened to recycle the same pid. supervisor must not
            # inherit even though the pid lookup currently matches.
            stale_fingerprint = "0" if real_fingerprint != "0" else "1"
            (pipeline_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": old_run_id,
                        "status_path": f".pipeline/runs/{old_run_id}/status.json",
                        "watcher_pid": current_pid,
                        "watcher_fingerprint": stale_fingerprint,
                    }
                ),
                encoding="utf-8",
            )
            (pipeline_dir / "experimental.pid").write_text(str(current_pid), encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            self.assertNotEqual(supervisor.run_id, old_run_id)

    def test_supervisor_write_current_run_pointer_records_live_watcher_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "experimental.pid").write_text(str(os.getpid()), encoding="utf-8")

            supervisor = RuntimeSupervisor(root, run_id="20260418T010203Z-p555", start_runtime=False)
            supervisor._write_current_run_pointer()

            current_run = json.loads((pipeline_dir / "current_run.json").read_text(encoding="utf-8"))
            self.assertEqual(current_run["run_id"], "20260418T010203Z-p555")
            self.assertEqual(current_run["watcher_pid"], os.getpid())

    def test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback(self) -> None:
        import watcher_core
        from pipeline_runtime import schema as schema_module

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)

            # Force the shared fingerprint helper through its `/proc`-missing
            # fallback by stubbing the primary `/proc` reader to "" and the
            # POSIX `ps -o lstart=` fallback to a stable string. The watcher
            # exporter and supervisor inheritance must still agree on the
            # same fingerprint via the same shared helper.
            fallback_value = "Mon Apr 18 12:34:56 2026"
            watcher_owned_run_id = "ps-fallback-run-id-20260418T010203Z-p999"
            with (
                mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
                mock.patch.object(schema_module, "_ps_lstart_fingerprint", return_value=fallback_value),
                mock.patch.dict(
                    "os.environ",
                    {"PIPELINE_RUNTIME_RUN_ID": watcher_owned_run_id},
                    clear=False,
                ),
            ):
                core = watcher_core.WatcherCore({
                    "watch_dir": str(watch_dir),
                    "base_dir": str(pipeline_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                })
                self.assertEqual(core.run_id, watcher_owned_run_id)
                core._write_current_run_pointer()

                (pipeline_dir / "experimental.pid").write_text(str(os.getpid()), encoding="utf-8")
                supervisor = RuntimeSupervisor(root, start_runtime=False)

            current_run = json.loads((pipeline_dir / "current_run.json").read_text(encoding="utf-8"))
            self.assertEqual(current_run["watcher_fingerprint"], fallback_value)
            self.assertEqual(supervisor.run_id, watcher_owned_run_id)

    def test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_proc_ctime_fallback(self) -> None:
        import watcher_core
        from pipeline_runtime import schema as schema_module

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)

            # Force the shared fingerprint helper through its narrow third
            # fallback by stubbing both the /proc/<pid>/stat reader and the
            # POSIX `ps -p <pid> -o lstart=` helper to "" while returning a
            # stable ctime string from _proc_ctime_fingerprint. The watcher
            # exporter and supervisor inheritance must still agree on the
            # same fingerprint via the same shared helper, so a supervisor
            # restart can still adopt the live watcher's run_id on hosts
            # where /proc/<pid>/stat parsing/read fails and `ps` does not
            # produce a usable lstart string but /proc/<pid> itself is still
            # stat-able.
            fallback_value = "1712345678901234567"
            watcher_owned_run_id = "proc-ctime-fallback-run-id-20260418T010203Z-p999"
            with (
                mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
                mock.patch.object(schema_module, "_ps_lstart_fingerprint", return_value=""),
                mock.patch.object(schema_module, "_proc_ctime_fingerprint", return_value=fallback_value),
                mock.patch.dict(
                    "os.environ",
                    {"PIPELINE_RUNTIME_RUN_ID": watcher_owned_run_id},
                    clear=False,
                ),
            ):
                core = watcher_core.WatcherCore({
                    "watch_dir": str(watch_dir),
                    "base_dir": str(pipeline_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                })
                self.assertEqual(core.run_id, watcher_owned_run_id)
                core._write_current_run_pointer()

                (pipeline_dir / "experimental.pid").write_text(str(os.getpid()), encoding="utf-8")
                supervisor = RuntimeSupervisor(root, start_runtime=False)

            current_run = json.loads((pipeline_dir / "current_run.json").read_text(encoding="utf-8"))
            self.assertEqual(current_run["watcher_fingerprint"], fallback_value)
            self.assertEqual(supervisor.run_id, watcher_owned_run_id)

    def test_supervisor_skips_run_id_inheritance_when_fingerprint_helper_returns_empty_for_live_watcher(self) -> None:
        import watcher_core
        from pipeline_runtime import schema as schema_module

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)

            # On a minimal host where /proc/<pid>/stat, `ps -p <pid> -o
            # lstart=`, and os.stat(f"/proc/{pid}") all fail, the watcher
            # exporter writes watcher_fingerprint="" and the supervisor's own
            # _watcher_process_fingerprint also returns "". Inheritance must
            # refuse to adopt the prior run_id in this safe-degradation path
            # so a stale pointer cannot bind a fresh supervisor to a watcher
            # whose process identity cannot be proven.
            watcher_owned_run_id = "empty-fp-run-id-20260418T010203Z-p999"
            with (
                mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
                mock.patch.object(schema_module, "_ps_lstart_fingerprint", return_value=""),
                mock.patch.object(schema_module, "_proc_ctime_fingerprint", return_value=""),
                mock.patch.dict(
                    "os.environ",
                    {"PIPELINE_RUNTIME_RUN_ID": watcher_owned_run_id},
                    clear=False,
                ),
            ):
                core = watcher_core.WatcherCore({
                    "watch_dir": str(watch_dir),
                    "base_dir": str(pipeline_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                })
                self.assertEqual(core.run_id, watcher_owned_run_id)
                core._write_current_run_pointer()

                (pipeline_dir / "experimental.pid").write_text(str(os.getpid()), encoding="utf-8")
                supervisor = RuntimeSupervisor(root, start_runtime=False)

            current_run = json.loads((pipeline_dir / "current_run.json").read_text(encoding="utf-8"))
            self.assertEqual(current_run["watcher_fingerprint"], "")
            self.assertNotEqual(supervisor.run_id, watcher_owned_run_id)

    def test_supervisor_restart_inherits_run_id_after_watcher_exporter_writes_pointer(self) -> None:
        import watcher_core

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)

            # The watcher exporter is the only writer of current_run.json in
            # this scenario; it must preserve the same owner contract that
            # supervisor inheritance now requires so a supervisor restart can
            # adopt the live watcher's run_id end-to-end. Use an explicit
            # watcher-owned run_id so this test stays discriminating even
            # when the supervisor's fresh _make_run_id() lands inside the
            # same second/pid as the watcher's auto-generated run_id.
            watcher_owned_run_id = "watcher-owned-run-id-20260418T010203Z-p999"
            with mock.patch.dict(
                "os.environ",
                {"PIPELINE_RUNTIME_RUN_ID": watcher_owned_run_id},
                clear=False,
            ):
                core = watcher_core.WatcherCore({
                    "watch_dir": str(watch_dir),
                    "base_dir": str(pipeline_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                })
            self.assertEqual(core.run_id, watcher_owned_run_id)
            core._write_current_run_pointer()

            (pipeline_dir / "experimental.pid").write_text(str(os.getpid()), encoding="utf-8")

            supervisor = RuntimeSupervisor(root, start_runtime=False)
            self.assertEqual(supervisor.run_id, watcher_owned_run_id)

    def test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint(self) -> None:
        from pipeline_runtime import schema as schema_module

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "experimental.pid").write_text(str(os.getpid()), encoding="utf-8")

            supervisor = RuntimeSupervisor(root, run_id="20260418T010203Z-p222", start_runtime=False)

            # Use the same shared-helper stub seam as the empty-path
            # regression so this positive supervisor writer assertion no
            # longer depends on the host actually exposing /proc/<pid>/stat.
            # watcher_pid keeps coming from the live experimental.pid lookup,
            # which is independent of the fingerprint helper.
            non_empty_fingerprint = "Mon Apr 18 12:34:56 2026"
            with (
                mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
                mock.patch.object(
                    schema_module,
                    "_ps_lstart_fingerprint",
                    return_value=non_empty_fingerprint,
                ),
            ):
                supervisor._write_current_run_pointer()

            current_run = json.loads((pipeline_dir / "current_run.json").read_text(encoding="utf-8"))
            self.assertEqual(current_run["watcher_pid"], os.getpid())
            self.assertEqual(current_run["watcher_fingerprint"], non_empty_fingerprint)

    def test_supervisor_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail(self) -> None:
        from pipeline_runtime import schema as schema_module

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_active_profile(root)
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            (pipeline_dir / "experimental.pid").write_text(str(os.getpid()), encoding="utf-8")

            supervisor = RuntimeSupervisor(root, run_id="20260418T010203Z-p333", start_runtime=False)

            # The watcher exporter and the supervisor are both writers of
            # current_run.json. On a minimal host where none of the shared
            # fingerprint helper sources are usable the supervisor writer
            # must serialize the same explicit empty-string
            # watcher_fingerprint as the watcher exporter, never silently
            # omit the field. Otherwise a later supervisor restart would see
            # a legacy-shaped pointer instead of the safe-degradation pointer
            # the previous writer actually intended.
            with (
                mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
                mock.patch.object(schema_module, "_ps_lstart_fingerprint", return_value=""),
                mock.patch.object(schema_module, "_proc_ctime_fingerprint", return_value=""),
            ):
                supervisor._write_current_run_pointer()

            current_run = json.loads((pipeline_dir / "current_run.json").read_text(encoding="utf-8"))
            self.assertEqual(current_run["run_id"], "20260418T010203Z-p333")
            self.assertEqual(current_run["watcher_pid"], os.getpid())
            self.assertIn("watcher_fingerprint", current_run)
            self.assertEqual(current_run["watcher_fingerprint"], "")

    # origin: seq 593 dispatch_intent/lane-identity default decision-class guard (출처 work note 미기록)
    def test_classify_operator_candidate_defaults_decision_class_per_visible_mode(self) -> None:
        scenarios = [
            (
                "needs_operator",
                {"reason_code": "truth_sync_required"},
                "operator_only",
            ),
            (
                "triage",
                {"reason_code": "slice_ambiguity"},
                "next_slice_selection",
            ),
            (
                "hibernate",
                {"reason_code": "waiting_next_control"},
                "internal_only",
            ),
            (
                "needs_operator",
                {"reason_code": "safety_stop", "operator_policy": "gate_24h"},
                "operator_only",
            ),
        ]

        for expected_mode, control_meta, expected_decision_class in scenarios:
            with self.subTest(mode=expected_mode):
                result = classify_operator_candidate(
                    "",
                    control_meta=control_meta,
                    now_ts=1_000.0,
                )

                self.assertEqual(result["mode"], expected_mode)
                self.assertIn(result["decision_class"], SUPPORTED_DECISION_CLASSES)
                self.assertEqual(result["decision_class"], expected_decision_class)

    def test_classify_operator_candidate_seq617_raw_metadata_is_canonical(self) -> None:
        result = classify_operator_candidate(
            "",
            control_meta={
                "reason_code": "branch_complete_pending_milestone_transition",
                "operator_policy": "stop_until_operator_decision",
                "decision_class": "branch_closure_and_milestone_transition",
                "decision_required": "close branch and decide milestone transition",
                "based_on_work": "work/4/21/2026-04-21-axis-g15-watcher-test-origin-annotations.md",
                "based_on_verify": "verify/4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral-verification.md",
            },
            now_ts=1_000.0,
        )

        self.assertEqual(result["mode"], "needs_operator")
        self.assertEqual(result["reason_code"], "approval_required")
        self.assertEqual(result["operator_policy"], "immediate_publish")
        self.assertEqual(result["decision_class"], "operator_only")
        self.assertEqual(result["classification_source"], "operator_policy")
        self.assertIn(result["decision_class"], SUPPORTED_DECISION_CLASSES)

    def test_classify_operator_candidate_branch_commit_gate_stays_operator_visible(self) -> None:
        result = classify_operator_candidate(
            "",
            control_meta={
                "reason_code": "branch_commit_and_milestone_transition",
                "operator_policy": "gate_24h",
                "decision_class": "operator_only",
                "decision_required": "approve branch commit and milestone transition",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        self.assertEqual(result["mode"], "needs_operator")
        self.assertEqual(result["reason_code"], "approval_required")
        self.assertEqual(result["operator_policy"], "gate_24h")
        self.assertEqual(result["decision_class"], "operator_only")
        self.assertEqual(result["classification_source"], "operator_policy")
        self.assertEqual(result["routed_to"], "operator")
        self.assertTrue(result["operator_eligible"])
        self.assertEqual(result["suppress_operator_until"], "")

    def test_classify_operator_candidate_choice_menu_routes_to_advisory_followup(self) -> None:
        control_text = "\n".join(
            [
                "STATUS: needs_operator",
                "CONTROL_SEQ: 623",
                "REASON_CODE: branch_commit_and_milestone_transition",
                "OPERATOR_POLICY: gate_24h",
                "DECISION_CLASS: operator_only",
                "",
                "**Operator decision A (choose one):** continue same-family runtime follow-up.",
                "**Operator decision B (choose one):** ask advisory owner to choose next slice.",
                "**Operator decision C (choose one):** pause for milestone transition.",
            ]
        )

        result = classify_operator_candidate(
            control_text,
            control_meta={
                "reason_code": "branch_commit_and_milestone_transition",
                "operator_policy": "gate_24h",
                "decision_class": "operator_only",
                "decision_required": "choose A/B/C from current docs and verification notes",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        self.assertEqual(result["mode"], "triage")
        self.assertEqual(result["suppressed_mode"], "triage")
        self.assertEqual(result["reason_code"], "slice_ambiguity")
        self.assertEqual(result["operator_policy"], "gate_24h")
        self.assertEqual(result["decision_class"], "next_slice_selection")
        self.assertEqual(result["classification_source"], "operator_policy")
        self.assertEqual(result["routed_to"], "codex_followup")
        self.assertFalse(result["operator_eligible"])

    def test_classify_operator_candidate_numbered_choice_menu_routes_to_advisory_followup(self) -> None:
        control_text = "\n".join(
            [
                "STATUS: needs_operator",
                "CONTROL_SEQ: 624",
                "REASON_CODE: branch_commit_and_milestone_transition",
                "OPERATOR_POLICY: gate_24h",
                "DECISION_CLASS: operator_only",
                "",
                "1안: continue same-family runtime follow-up.",
                "2안: ask advisory owner to choose next slice.",
                "3안: pause for milestone transition.",
            ]
        )

        result = classify_operator_candidate(
            control_text,
            control_meta={
                "reason_code": "branch_commit_and_milestone_transition",
                "operator_policy": "gate_24h",
                "decision_class": "operator_only",
                "decision_required": "선택지 1/2/3 중 current docs and verification notes로 고르기",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        self.assertEqual(result["mode"], "triage")
        self.assertEqual(result["reason_code"], "slice_ambiguity")
        self.assertEqual(result["operator_policy"], "gate_24h")
        self.assertEqual(result["decision_class"], "next_slice_selection")
        self.assertEqual(result["routed_to"], "codex_followup")

    # origin: choice-menu inline parenthesized advisory follow-up guard (출처 work note 미기록)
    def test_classify_operator_candidate_inline_parenthesized_choices_route_to_advisory_followup(self) -> None:
        result = classify_operator_candidate(
            "",
            control_meta={
                "reason_code": "approval_required",
                "operator_policy": "gate_24h",
                "decision_class": "operator_only",
                "decision_required": (
                    "(B) pipeline runtime live validation; "
                    "(C) evidence follow-up; "
                    "(D) docs reconciliation"
                ),
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        self.assertEqual(result["mode"], "triage")
        self.assertEqual(result["reason_code"], "slice_ambiguity")
        self.assertEqual(result["decision_class"], "next_slice_selection")
        self.assertEqual(result["routed_to"], "codex_followup")

    # origin: choice-menu explanatory blocker marker scope guard (출처 work note 미기록)
    def test_classify_operator_candidate_body_marker_docs_do_not_block_choice_menu(self) -> None:
        control_text = "\n".join(
            [
                "STATUS: needs_operator",
                "CONTROL_SEQ: 625",
                "REASON_CODE: approval_required",
                "OPERATOR_POLICY: gate_24h",
                "DECISION_CLASS: operator_only",
                (
                    "DECISION_REQUIRED: (B) live validation; "
                    "(C) evidence check; "
                    "(D) docs sync"
                ),
                "",
                "---",
                "",
                "- approval_record/safety/destructive/auth/credential/git/milestone marker docs are explanatory.",
            ]
        )

        result = classify_operator_candidate(
            control_text,
            control_meta={
                "reason_code": "approval_required",
                "operator_policy": "gate_24h",
                "decision_class": "operator_only",
                "decision_required": "(B) live validation; (C) evidence check; (D) docs sync",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        self.assertEqual(result["mode"], "triage")
        self.assertEqual(result["reason_code"], "slice_ambiguity")
        self.assertEqual(result["decision_class"], "next_slice_selection")

    def test_classify_operator_candidate_seq_only_bump_keeps_semantic_fingerprint(self) -> None:
        control_text_template = "\n".join(
            [
                "STATUS: needs_operator",
                "CONTROL_SEQ: {seq}",
                "REASON_CODE: approval_required",
                "OPERATOR_POLICY: gate_24h",
                "DECISION_CLASS: operator_only",
                "DECISION_REQUIRED: (B) live validation; (C) commit approval",
                "",
                "- Runtime validation and commit approval remain the same menu.",
            ]
        )
        control_meta = {
            "reason_code": "approval_required",
            "operator_policy": "gate_24h",
            "decision_class": "operator_only",
            "decision_required": "(B) live validation; (C) commit approval",
        }

        first = classify_operator_candidate(
            control_text_template.format(seq=644),
            control_meta=control_meta,
            control_seq=644,
            control_mtime=2_000.0,
            first_seen_ts=1_000.0,
            now_ts=2_100.0,
        )
        bumped = classify_operator_candidate(
            control_text_template.format(seq=645),
            control_meta=control_meta,
            control_seq=645,
            control_mtime=3_000.0,
            first_seen_ts=1_000.0,
            now_ts=2_100.0,
        )

        self.assertEqual(bumped["fingerprint"], first["fingerprint"])
        self.assertEqual(bumped["first_seen_at"], first["first_seen_at"])
        self.assertEqual(bumped["suppress_operator_until"], first["suppress_operator_until"])

    def test_classify_operator_candidate_sequential_gate_not_misrouted(self) -> None:
        content = (
            "DECISION_REQUIRED: (B) runtime 재시작 승인; (C) B 통과 후 commit/push/PR 승인; "
            "(D) C 완료 후 Milestone 5 진입 승인"
        )
        control_meta = {
            "OPERATOR_POLICY": "gate_24h",
            "REASON_CODE": "approval_required",
            "DECISION_CLASS": "operator_only",
        }
        result = classify_operator_candidate(content, control_meta=control_meta)
        self.assertNotEqual(result.get("reason_code"), "slice_ambiguity")
        self.assertNotEqual(result.get("decision_class"), "next_slice_selection")

    def test_classify_operator_candidate_choice_menu_keeps_approval_record_blocker(self) -> None:
        result = classify_operator_candidate(
            "A: rewrite approval record\nB: continue without approval record repair",
            control_meta={
                "reason_code": "approval_required",
                "operator_policy": "gate_24h",
                "decision_class": "operator_only",
                "decision_required": "approval-record repair must happen before new work",
            },
            idle_stable=True,
            control_mtime=1_000.0,
            now_ts=1_000.0,
        )

        self.assertEqual(result["mode"], "needs_operator")
        self.assertEqual(result["reason_code"], "approval_required")
        self.assertEqual(result["decision_class"], "operator_only")
        self.assertEqual(result["routed_to"], "operator")

    # origin: seq 593 dispatch_intent/lane-identity payload stability guard (출처 work note 미기록)
    def test_classify_operator_candidate_payload_stability(self) -> None:
        expected_keys = [
            "mode",
            "suppressed_mode",
            "block_reason",
            "reason_code",
            "operator_policy",
            "decision_class",
            "decision_required",
            "based_on_work",
            "based_on_verify",
            "classification_source",
            "first_seen_at",
            "suppress_operator_until",
            "operator_eligible",
            "publish_immediately",
            "routed_to",
            "fingerprint",
        ]

        shape_result = classify_operator_candidate(
            "",
            control_meta={"reason_code": "truth_sync_required"},
            now_ts=1_000.0,
        )
        self.assertEqual(len(shape_result), 16)
        self.assertEqual(list(shape_result), expected_keys)

        invariant_scenarios = [
            ("needs_operator", {"reason_code": "truth_sync_required"}),
            (
                "needs_operator",
                {"reason_code": "safety_stop", "operator_policy": "gate_24h"},
            ),
            ("triage", {"reason_code": "slice_ambiguity"}),
            ("hibernate", {"reason_code": "waiting_next_control"}),
            (
                "recovery",
                {
                    "reason_code": "newer_unverified_work_present",
                    "operator_policy": "gate_24h",
                },
            ),
        ]

        for expected_mode, control_meta in invariant_scenarios:
            with self.subTest(mode=expected_mode):
                result = classify_operator_candidate(
                    "",
                    control_meta=control_meta,
                    now_ts=1_000.0,
                )
                self.assertEqual(result["mode"], expected_mode)
                decision_class = result["decision_class"]
                self.assertTrue(
                    decision_class == ""
                    or decision_class in SUPPORTED_DECISION_CLASSES,
                    f"decision_class must be empty or canonical (got {decision_class!r})",
                )


if __name__ == "__main__":
    unittest.main()
