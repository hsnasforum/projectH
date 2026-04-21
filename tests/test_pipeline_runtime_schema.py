from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from pipeline_runtime import schema as schema_module
from pipeline_runtime.schema import (
    JOB_STATE_DIR_NAME,
    STATE_DIR_SHARED_FILES,
    iter_job_state_paths,
    jobs_state_dir,
    latest_verify_note_for_work,
    latest_round_markdown,
    load_job_states,
    parse_control_slots,
    process_starttime_fingerprint,
    read_control_meta,
)


class RuntimeSchemaTest(unittest.TestCase):
    def test_read_control_meta_reads_extended_operator_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = Path(tmp) / "operator_request.md"
            slot.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 184",
                        "REASON_CODE: approval_required",
                        "OPERATOR_POLICY: immediate_publish",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: approve runtime auth refresh",
                        "BASED_ON_WORK: work/4/16/example.md",
                        "BASED_ON_VERIFY: verify/4/16/example.md",
                    ]
                ),
                encoding="utf-8",
            )

            meta = read_control_meta(slot)

            self.assertEqual(meta["status"], "needs_operator")
            self.assertEqual(meta["control_seq"], 184)
            self.assertEqual(meta["reason_code"], "approval_required")
            self.assertEqual(meta["operator_policy"], "immediate_publish")
            self.assertEqual(meta["decision_class"], "operator_only")
            self.assertEqual(meta["decision_required"], "approve runtime auth refresh")
            self.assertEqual(meta["based_on_work"], "work/4/16/example.md")
            self.assertEqual(meta["based_on_verify"], "verify/4/16/example.md")

    def test_parse_control_slots_ignores_extended_headers_for_active_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pipeline = Path(tmp)
            (pipeline / "operator_request.md").write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 184",
                        "REASON_CODE: approval_required",
                        "OPERATOR_POLICY: immediate_publish",
                    ]
                ),
                encoding="utf-8",
            )
            (pipeline / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 185\n",
                encoding="utf-8",
            )

            slots = parse_control_slots(pipeline)

            self.assertEqual(slots["active"]["file"], "claude_handoff.md")
            self.assertEqual(slots["stale"][0]["file"], "operator_request.md")

    def test_latest_round_markdown_ignores_root_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# metadata\n", encoding="utf-8")
            round_note = root / "4" / "16" / "2026-04-16-real-round.md"
            round_note.parent.mkdir(parents=True, exist_ok=True)
            round_note.write_text("# round\n", encoding="utf-8")

            round_mtime = round_note.stat().st_mtime + 1
            readme_mtime = round_mtime + 10
            os.utime(round_note, (round_mtime, round_mtime))
            os.utime(readme, (readme_mtime, readme_mtime))

            rel, mtime = latest_round_markdown(root)

            self.assertEqual(rel, "4/16/2026-04-16-real-round.md")
            self.assertEqual(mtime, round_mtime)

    def test_latest_round_markdown_prefers_newer_date_over_newer_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older_date = root / "4" / "18" / "2026-04-18-older-date.md"
            newer_date = root / "4" / "20" / "2026-04-20-newer-date.md"
            older_date.parent.mkdir(parents=True, exist_ok=True)
            newer_date.parent.mkdir(parents=True, exist_ok=True)
            older_date.write_text("# older\n", encoding="utf-8")
            newer_date.write_text("# newer\n", encoding="utf-8")

            newer_mtime = newer_date.stat().st_mtime
            spoofed_older_mtime = newer_mtime + 100.0
            os.utime(older_date, (spoofed_older_mtime, spoofed_older_mtime))
            os.utime(newer_date, (newer_mtime, newer_mtime))

            rel, mtime = latest_round_markdown(root)

            self.assertEqual(rel, "4/20/2026-04-20-newer-date.md")
            self.assertEqual(mtime, newer_mtime)


class LoadJobStatesSharedFilesTest(unittest.TestCase):
    def test_shared_state_files_cover_turn_and_autonomy(self) -> None:
        self.assertIn("turn_state.json", STATE_DIR_SHARED_FILES)
        self.assertIn("autonomy_state.json", STATE_DIR_SHARED_FILES)

    def test_load_job_states_skips_autonomy_state_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            autonomy_payload = {
                "fingerprint": "",
                "mode": "normal",
                "block_reason": "",
                "reason_code": "",
                "operator_policy": "",
            }
            (state_dir / "autonomy_state.json").write_text(
                json.dumps(autonomy_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            turn_payload = {
                "state": "CLAUDE_ACTIVE",
                "entered_at": 0.0,
                "reason": "test",
            }
            (state_dir / "turn_state.json").write_text(
                json.dumps(turn_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            job_payload = {
                "job_id": "job-current",
                "status": "VERIFY_RUNNING",
                "artifact_path": "work/4/18/current.md",
                "run_id": "run-current",
                "round": 1,
                "updated_at": 123.0,
            }
            job_path = state_dir / "20260418-job-current.json"
            job_path.write_text(
                json.dumps(job_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            jobs = load_job_states(state_dir)

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["job_id"], "job-current")

            filtered = load_job_states(state_dir, run_id="run-current")
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]["job_id"], "job-current")

    def test_load_job_states_with_no_real_jobs_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            (state_dir / "autonomy_state.json").write_text(
                json.dumps({"mode": "normal"}, ensure_ascii=False),
                encoding="utf-8",
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps({"state": "IDLE"}, ensure_ascii=False),
                encoding="utf-8",
            )

            jobs = load_job_states(state_dir)

            self.assertEqual(jobs, [])


class PathEnforcedJobStateOwnershipTest(unittest.TestCase):
    def test_jobs_state_dir_is_primary_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            primary = jobs_state_dir(state_dir)
            self.assertEqual(primary, state_dir / JOB_STATE_DIR_NAME)
            self.assertEqual(primary.name, "jobs")

    def test_iter_job_state_paths_prefers_primary_over_root_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            primary_dir = jobs_state_dir(state_dir)
            primary_dir.mkdir(parents=True)
            (primary_dir / "job-shared.json").write_text(
                json.dumps({"job_id": "job-shared", "where": "primary"}), encoding="utf-8"
            )
            (state_dir / "job-shared.json").write_text(
                json.dumps({"job_id": "job-shared", "where": "fallback"}), encoding="utf-8"
            )
            (state_dir / "job-only-root.json").write_text(
                json.dumps({"job_id": "job-only-root", "where": "fallback"}), encoding="utf-8"
            )
            (state_dir / "autonomy_state.json").write_text(
                json.dumps({"mode": "normal"}), encoding="utf-8"
            )
            (state_dir / "turn_state.json").write_text(
                json.dumps({"state": "IDLE"}), encoding="utf-8"
            )

            paths = iter_job_state_paths(state_dir)

            names = {p.name for p in paths}
            self.assertEqual(names, {"job-shared.json", "job-only-root.json"})

            data_by_id: dict[str, str] = {}
            for p in paths:
                payload = json.loads(p.read_text(encoding="utf-8"))
                data_by_id[payload["job_id"]] = payload["where"]
            self.assertEqual(data_by_id["job-shared"], "primary")
            self.assertEqual(data_by_id["job-only-root"], "fallback")

    def test_iter_job_state_paths_skips_shared_files_in_root_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            for name in STATE_DIR_SHARED_FILES:
                (state_dir / name).write_text("{}", encoding="utf-8")
            paths = iter_job_state_paths(state_dir)
            self.assertEqual(paths, [])

    def test_iter_job_state_paths_handles_missing_primary_gracefully(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            (state_dir / "job-legacy.json").write_text(
                json.dumps({"job_id": "job-legacy"}), encoding="utf-8"
            )
            paths = iter_job_state_paths(state_dir)
            self.assertEqual([p.name for p in paths], ["job-legacy.json"])

    def test_load_job_states_merges_primary_and_fallback_and_prefers_primary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            primary_dir = jobs_state_dir(state_dir)
            primary_dir.mkdir(parents=True)
            (primary_dir / "job-shared.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-shared",
                        "run_id": "run-current",
                        "status": "VERIFY_RUNNING",
                        "updated_at": 200.0,
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-shared.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-shared",
                        "run_id": "run-old",
                        "status": "VERIFY_PENDING",
                        "updated_at": 100.0,
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "job-legacy.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-legacy",
                        "run_id": "run-current",
                        "status": "VERIFY_PENDING",
                        "updated_at": 150.0,
                    }
                ),
                encoding="utf-8",
            )

            jobs = load_job_states(state_dir, run_id="run-current")

            statuses = {row["job_id"]: row["status"] for row in jobs}
            self.assertEqual(
                statuses, {"job-shared": "VERIFY_RUNNING", "job-legacy": "VERIFY_PENDING"}
            )

    def test_job_state_save_writes_to_primary_jobs_subdirectory(self) -> None:
        # Guard against regression: JobState.save must land in the primary jobs/ path,
        # not the legacy root. The root is read-only fallback during migration.
        from verify_fsm import JobState, JobStatus

        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            job = JobState(
                job_id="job-save-primary",
                status=JobStatus.VERIFY_PENDING,
                artifact_path="work/4/18/some.md",
            )
            job.save(state_dir)

            primary_path = jobs_state_dir(state_dir) / "job-save-primary.json"
            root_path = state_dir / "job-save-primary.json"
            self.assertTrue(primary_path.exists())
            self.assertFalse(root_path.exists())

    def test_job_state_load_reads_primary_first_then_root_fallback(self) -> None:
        from verify_fsm import JobState, JobStatus

        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            # Only a root-level legacy file — reader must still find it via fallback.
            (state_dir / "job-legacy-only.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-legacy-only",
                        "status": JobStatus.VERIFY_PENDING.value,
                        "artifact_path": "work/4/18/legacy.md",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )

            loaded = JobState.load(state_dir, "job-legacy-only")
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.job_id, "job-legacy-only")
            self.assertEqual(loaded.status, JobStatus.VERIFY_PENDING)

            # Primary copy written later must win over the root fallback.
            primary_dir = jobs_state_dir(state_dir)
            primary_dir.mkdir(parents=True, exist_ok=True)
            (primary_dir / "job-legacy-only.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-legacy-only",
                        "status": JobStatus.VERIFY_DONE.value,
                        "artifact_path": "work/4/18/legacy.md",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )
            reloaded = JobState.load(state_dir, "job-legacy-only")
            self.assertIsNotNone(reloaded)
            assert reloaded is not None
            self.assertEqual(reloaded.status, JobStatus.VERIFY_DONE)


class LatestVerifyNoteForWorkTest(unittest.TestCase):
    def test_prefers_explicit_work_reference_over_newer_unrelated_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_root = root / "work"
            verify_root = root / "verify"
            work_path = work_root / "4" / "18" / "2026-04-18-slice.md"
            matching_verify = verify_root / "4" / "18" / "2026-04-18-slice-verification.md"
            unrelated_verify = verify_root / "4" / "18" / "2026-04-18-unrelated-verification.md"
            work_path.parent.mkdir(parents=True, exist_ok=True)
            matching_verify.parent.mkdir(parents=True, exist_ok=True)
            work_path.write_text("# work\n", encoding="utf-8")
            matching_verify.write_text(
                "Based on `work/4/18/2026-04-18-slice.md`\n",
                encoding="utf-8",
            )
            unrelated_verify.write_text(
                "Based on `work/4/18/2026-04-18-other.md`\n",
                encoding="utf-8",
            )

            now = time.time()
            os.utime(matching_verify, (now - 10, now - 10))
            os.utime(unrelated_verify, (now, now))

            resolved = latest_verify_note_for_work(
                work_root,
                verify_root,
                work_path,
                repo_root=root,
            )

            self.assertEqual(resolved, matching_verify)

    def test_accepts_cross_day_verify_when_note_explicitly_references_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_root = root / "work"
            verify_root = root / "verify"
            work_path = work_root / "4" / "19" / "2026-04-19-slice.md"
            same_day_verify = verify_root / "4" / "19" / "2026-04-19-unrelated-verification.md"
            cross_day_verify = verify_root / "4" / "20" / "2026-04-20-slice-verification.md"
            work_path.parent.mkdir(parents=True, exist_ok=True)
            same_day_verify.parent.mkdir(parents=True, exist_ok=True)
            cross_day_verify.parent.mkdir(parents=True, exist_ok=True)
            work_path.write_text("# work\n", encoding="utf-8")
            same_day_verify.write_text("# verify\n", encoding="utf-8")
            cross_day_verify.write_text(
                "Based on `work/4/19/2026-04-19-slice.md`\n",
                encoding="utf-8",
            )

            now = time.time()
            os.utime(same_day_verify, (now - 20, now - 20))
            os.utime(cross_day_verify, (now - 10, now - 10))

            resolved = latest_verify_note_for_work(
                work_root,
                verify_root,
                work_path,
                repo_root=root,
            )

            self.assertEqual(resolved, cross_day_verify)

    def test_returns_none_when_single_same_day_verify_has_no_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_root = root / "work"
            verify_root = root / "verify"
            work_path = work_root / "4" / "18" / "2026-04-18-slice.md"
            verify_path = verify_root / "4" / "18" / "2026-04-18-slice-verification.md"
            work_path.parent.mkdir(parents=True, exist_ok=True)
            verify_path.parent.mkdir(parents=True, exist_ok=True)
            work_path.write_text("# work\n", encoding="utf-8")
            verify_path.write_text("# verify\n", encoding="utf-8")

            resolved = latest_verify_note_for_work(
                work_root,
                verify_root,
                work_path,
                repo_root=root,
            )

            self.assertIsNone(resolved)

    def test_returns_none_when_multiple_same_day_verifies_do_not_reference_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_root = root / "work"
            verify_root = root / "verify"
            work_path = work_root / "4" / "18" / "2026-04-18-slice.md"
            verify_a = verify_root / "4" / "18" / "2026-04-18-a-verification.md"
            verify_b = verify_root / "4" / "18" / "2026-04-18-b-verification.md"
            work_path.parent.mkdir(parents=True, exist_ok=True)
            verify_a.parent.mkdir(parents=True, exist_ok=True)
            work_path.write_text("# work\n", encoding="utf-8")
            verify_a.write_text("# verify a\n", encoding="utf-8")
            verify_b.write_text("# verify b\n", encoding="utf-8")

            resolved = latest_verify_note_for_work(
                work_root,
                verify_root,
                work_path,
                repo_root=root,
            )

            self.assertIsNone(resolved)

    def test_returns_none_when_same_day_unreferenced_and_cross_day_unrelated_both_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_root = root / "work"
            verify_root = root / "verify"
            work_path = work_root / "4" / "19" / "2026-04-19-slice.md"
            same_day_verify = verify_root / "4" / "19" / "2026-04-19-slice-verification.md"
            cross_day_verify = verify_root / "4" / "20" / "2026-04-20-unrelated-verification.md"
            work_path.parent.mkdir(parents=True, exist_ok=True)
            same_day_verify.parent.mkdir(parents=True, exist_ok=True)
            cross_day_verify.parent.mkdir(parents=True, exist_ok=True)
            work_path.write_text("# work\n", encoding="utf-8")
            same_day_verify.write_text("# verify\n", encoding="utf-8")
            cross_day_verify.write_text(
                "Based on `work/4/20/2026-04-20-other.md`\n",
                encoding="utf-8",
            )

            resolved = latest_verify_note_for_work(
                work_root,
                verify_root,
                work_path,
                repo_root=root,
            )

            self.assertIsNone(resolved)

    def test_returns_none_when_single_same_day_verify_references_other_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_root = root / "work"
            verify_root = root / "verify"
            work_path = work_root / "4" / "18" / "2026-04-18-slice.md"
            verify_path = verify_root / "4" / "18" / "2026-04-18-other-verification.md"
            work_path.parent.mkdir(parents=True, exist_ok=True)
            verify_path.parent.mkdir(parents=True, exist_ok=True)
            work_path.write_text("# work\n", encoding="utf-8")
            verify_path.write_text(
                "Based on `work/4/18/2026-04-18-other.md`\n",
                encoding="utf-8",
            )

            resolved = latest_verify_note_for_work(
                work_root,
                verify_root,
                work_path,
                repo_root=root,
            )

            self.assertIsNone(resolved)

    def test_returns_none_when_lone_unrelated_same_day_verify_mimics_manual_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_root = root / "work"
            verify_root = root / "verify"
            work_path = work_root / "4" / "18" / "2026-04-18-slice.md"
            manual_cleanup = (
                verify_root
                / "4"
                / "18"
                / "2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md"
            )
            work_path.parent.mkdir(parents=True, exist_ok=True)
            manual_cleanup.parent.mkdir(parents=True, exist_ok=True)
            work_path.write_text("# work\n", encoding="utf-8")
            manual_cleanup.write_text(
                "Based on `work/4/18/2026-04-18-other-slice.md`\n",
                encoding="utf-8",
            )

            resolved = latest_verify_note_for_work(
                work_root,
                verify_root,
                work_path,
                repo_root=root,
            )

            self.assertIsNone(resolved)


class ProcessStarttimeFingerprintTest(unittest.TestCase):
    def test_process_starttime_fingerprint_returns_empty_for_non_positive_pid(self) -> None:
        # The non-positive pid short-circuit must skip every source helper
        # entirely. Otherwise a stray /proc read, `ps` invocation, or
        # /proc/<pid> stat could surface for pid 0/-1 callers (e.g.
        # supervisor inheritance when no live watcher pid is available)
        # instead of the intended "do not inherit" empty fingerprint.
        with (
            mock.patch.object(schema_module, "_proc_starttime_fingerprint") as proc_mock,
            mock.patch.object(schema_module, "_ps_lstart_fingerprint") as ps_mock,
            mock.patch.object(schema_module, "_proc_ctime_fingerprint") as ctime_mock,
        ):
            self.assertEqual(process_starttime_fingerprint(0), "")
            self.assertEqual(process_starttime_fingerprint(-1), "")
        proc_mock.assert_not_called()
        ps_mock.assert_not_called()
        ctime_mock.assert_not_called()

    def test_process_starttime_fingerprint_uses_proc_when_available(self) -> None:
        # When the primary /proc source returns a non-empty fingerprint the
        # helper must keep using it without falling back to the slower ps
        # invocation or the /proc/<pid> ctime fallback. All three sources are
        # stubbed so the assertion holds on hosts that do not expose
        # /proc/<pid>/stat (non-Linux POSIX, restricted containers) just as
        # well as on a standard Linux host.
        with (
            mock.patch.object(
                schema_module,
                "_proc_starttime_fingerprint",
                return_value="proc-source-fingerprint",
            ) as proc_mock,
            mock.patch.object(schema_module, "_ps_lstart_fingerprint") as ps_mock,
            mock.patch.object(schema_module, "_proc_ctime_fingerprint") as ctime_mock,
        ):
            fingerprint = process_starttime_fingerprint(12345)
        self.assertEqual(fingerprint, "proc-source-fingerprint")
        proc_mock.assert_called_once_with(12345)
        ps_mock.assert_not_called()
        ctime_mock.assert_not_called()

    def test_process_starttime_fingerprint_falls_back_to_ps_when_proc_missing(self) -> None:
        # With /proc/<pid>/stat empty but `ps -p <pid> -o lstart=` producing a
        # usable string, the helper must return the ps fallback without
        # touching the narrower /proc/<pid> ctime fallback.
        with (
            mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
            mock.patch.object(
                schema_module,
                "_ps_lstart_fingerprint",
                return_value="Mon Apr 18 12:34:56 2026",
            ) as ps_mock,
            mock.patch.object(schema_module, "_proc_ctime_fingerprint") as ctime_mock,
        ):
            fingerprint = process_starttime_fingerprint(12345)
        self.assertEqual(fingerprint, "Mon Apr 18 12:34:56 2026")
        ps_mock.assert_called_once_with(12345)
        ctime_mock.assert_not_called()

    def test_process_starttime_fingerprint_falls_back_to_proc_ctime_when_proc_and_ps_both_fail(self) -> None:
        # /proc/<pid>/stat parsing/read fails and `ps -p <pid> -o lstart=`
        # also yields "", but /proc/<pid> itself is still stat-able. The
        # helper must thread that narrow case through the new
        # os.stat(f"/proc/{pid}") ctime fallback rather than giving up so
        # supervisor restart inheritance can still prove the watcher is the
        # same process instance the pointer was written for.
        with (
            mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
            mock.patch.object(schema_module, "_ps_lstart_fingerprint", return_value=""),
            mock.patch.object(
                schema_module,
                "_proc_ctime_fingerprint",
                return_value="1712345678901234567",
            ) as ctime_mock,
        ):
            fingerprint = process_starttime_fingerprint(12345)
        self.assertEqual(fingerprint, "1712345678901234567")
        ctime_mock.assert_called_once_with(12345)

    def test_process_starttime_fingerprint_returns_empty_when_all_sources_fail(self) -> None:
        # Preserve the prior both-sources-fail contract once the third
        # fallback also fails: when /proc/<pid>/stat parsing, `ps -p <pid>
        # -o lstart=`, and os.stat(f"/proc/{pid}") all safe-degrade to "",
        # the helper must return "" so inheritance falls through to a fresh
        # _make_run_id() instead of falsely adopting a prior run_id.
        with (
            mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
            mock.patch.object(schema_module, "_ps_lstart_fingerprint", return_value=""),
            mock.patch.object(schema_module, "_proc_ctime_fingerprint", return_value=""),
        ):
            self.assertEqual(process_starttime_fingerprint(12345), "")

    def test_proc_starttime_fingerprint_extracts_starttime_field_from_well_formed_stat(self) -> None:
        # The Linux `/proc/<pid>/stat` line embeds the comm field inside
        # parens which may themselves contain spaces and inner parens. The
        # parser uses `rfind(")")` to skip the comm field once, then splits
        # the tail on whitespace and reads the starttime token at index 19
        # (field 22 of the original stat line). Build a fixture with a comm
        # that has both spaces and an inner ')' so the regression proves
        # `rfind(")")` lands on the outer closing paren and the tail split
        # still surfaces the intended starttime.
        tail_fields = [
            "S", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "10", "11", "12", "13", "14", "15", "16", "17", "18",
            "9876543210",  # rest[19] -> starttime token
            "20", "21", "22", "23", "24", "25",
        ]
        stat_payload = "12345 (my (weird) cmd with spaces) " + " ".join(tail_fields) + "\n"
        fake_path = mock.Mock()
        fake_path.read_text.return_value = stat_payload
        with mock.patch.object(schema_module, "Path", return_value=fake_path) as path_mock:
            value = schema_module._proc_starttime_fingerprint(99999)
        self.assertEqual(value, "9876543210")
        path_mock.assert_called_once_with("/proc/99999/stat")

    def test_proc_starttime_fingerprint_returns_empty_when_stat_read_raises_oserror(self) -> None:
        # `/proc/<pid>/stat` may be missing (non-Linux POSIX, restricted
        # containers) or unreadable. The helper must catch any OSError
        # subclass — including FileNotFoundError — and return "" so the
        # caller falls through to the ps fallback rather than seeing the
        # exception escape.
        fake_path = mock.Mock()
        fake_path.read_text.side_effect = FileNotFoundError("stat")
        with mock.patch.object(schema_module, "Path", return_value=fake_path) as path_mock:
            self.assertEqual(schema_module._proc_starttime_fingerprint(99999), "")
        path_mock.assert_called_once_with("/proc/99999/stat")

    def test_proc_starttime_fingerprint_returns_empty_when_stat_payload_has_no_closing_paren(self) -> None:
        # The Linux `/proc/<pid>/stat` line embeds the comm field inside
        # parens; the parser locates the last ')' to skip past it. A payload
        # with no ')' at all must be treated as unparseable rather than
        # producing a partial fingerprint.
        fake_path = mock.Mock()
        fake_path.read_text.return_value = "12345 cmd_no_paren S 1 1 1 1 1\n"
        with mock.patch.object(schema_module, "Path", return_value=fake_path):
            self.assertEqual(schema_module._proc_starttime_fingerprint(99999), "")

    def test_proc_starttime_fingerprint_returns_empty_when_stat_tail_has_fewer_than_twenty_fields(self) -> None:
        # After skipping past the last ')', field 22 (starttime) sits at
        # rest[19]. A truncated stat line that produces fewer than 20 tail
        # fields must safe-degrade to "" instead of raising IndexError.
        fake_path = mock.Mock()
        fake_path.read_text.return_value = "12345 (cmd) S 1 2 3 4 5 6 7 8 9 10\n"
        with mock.patch.object(schema_module, "Path", return_value=fake_path):
            self.assertEqual(schema_module._proc_starttime_fingerprint(99999), "")

    def test_ps_lstart_fingerprint_returns_stripped_stdout_on_success(self) -> None:
        completed = mock.Mock(returncode=0, stdout="Mon Apr 18 12:34:56 2026\n", stderr="")
        with mock.patch.object(schema_module.subprocess, "run", return_value=completed) as run_mock:
            value = schema_module._ps_lstart_fingerprint(99999)
        self.assertEqual(value, "Mon Apr 18 12:34:56 2026")
        called_cmd = run_mock.call_args.args[0]
        self.assertEqual(called_cmd[:1], ["ps"])
        self.assertIn("-p", called_cmd)
        self.assertIn("99999", called_cmd)
        # Pin the subprocess kwargs that matter to safety and parsing:
        # capture_output=True keeps stdout/stderr off the inheriting tty,
        # text=True returns str so the helper can `.strip()` directly, and
        # timeout=2.0 bounds a hung `ps` so the safe-degradation path
        # (TimeoutExpired -> "") can actually trigger.
        called_kwargs = run_mock.call_args.kwargs
        self.assertIs(called_kwargs.get("capture_output"), True)
        self.assertIs(called_kwargs.get("text"), True)
        self.assertEqual(called_kwargs.get("timeout"), 2.0)

    def test_ps_lstart_fingerprint_returns_empty_when_ps_fails(self) -> None:
        completed = mock.Mock(returncode=1, stdout="", stderr="no such process")
        with mock.patch.object(schema_module.subprocess, "run", return_value=completed):
            self.assertEqual(schema_module._ps_lstart_fingerprint(99999), "")

    def test_ps_lstart_fingerprint_returns_empty_when_ps_binary_missing(self) -> None:
        with mock.patch.object(schema_module.subprocess, "run", side_effect=FileNotFoundError("ps")):
            self.assertEqual(schema_module._ps_lstart_fingerprint(99999), "")

    def test_ps_lstart_fingerprint_returns_empty_when_ps_times_out(self) -> None:
        # subprocess.TimeoutExpired is a SubprocessError subclass and the
        # helper already passes timeout=2.0 to subprocess.run. Pin the
        # safe-degradation contract so a hung `ps` invocation cannot leak a
        # partial value or escape the helper as an exception; callers must
        # see "" and treat it as "do not inherit".
        timeout_exc = subprocess.TimeoutExpired(cmd=["ps"], timeout=2.0)
        with mock.patch.object(schema_module.subprocess, "run", side_effect=timeout_exc):
            self.assertEqual(schema_module._ps_lstart_fingerprint(99999), "")

    def test_proc_ctime_fingerprint_returns_stringified_ctime_ns_on_success(self) -> None:
        # The third fallback is pinned to /proc/<pid>'s st_ctime_ns so the
        # fingerprint stays deterministic per process instance. Callers embed
        # this string into current_run.json; serializing ctime_ns as str keeps
        # the JSON stable regardless of integer size.
        fake_stat = mock.Mock()
        fake_stat.st_ctime_ns = 1712345678901234567
        with mock.patch.object(schema_module.os, "stat", return_value=fake_stat) as stat_mock:
            value = schema_module._proc_ctime_fingerprint(99999)
        self.assertEqual(value, "1712345678901234567")
        stat_mock.assert_called_once_with("/proc/99999")

    def test_proc_ctime_fingerprint_returns_empty_when_stat_raises_oserror(self) -> None:
        # /proc/<pid> itself may be missing (pid died between ps fallback and
        # this probe, restricted container, non-Linux POSIX host without
        # /proc). The helper must catch any OSError subclass and return ""
        # so the caller returns "" and inheritance falls through to a fresh
        # _make_run_id() rather than seeing the exception escape.
        with mock.patch.object(
            schema_module.os,
            "stat",
            side_effect=FileNotFoundError("/proc/99999"),
        ) as stat_mock:
            self.assertEqual(schema_module._proc_ctime_fingerprint(99999), "")
        stat_mock.assert_called_once_with("/proc/99999")


if __name__ == "__main__":
    unittest.main()
