from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from pipeline_runtime.schema import jobs_state_dir
from verify_fsm import JobState, JobStatus
from watcher_job_state import JobStateManager


def _archive_dir_fn(base_dir: Path):
    def _archive_dir(source_run_id: str = "") -> Path:
        if source_run_id:
            return base_dir / "runs" / source_run_id / "state-archive"
        return base_dir / "state-archive" / "legacy"

    return _archive_dir


class JobStateManagerTest(unittest.TestCase):
    def test_archive_job_state_file_moves_to_run_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            path = jobs_state_dir(state_dir) / "job-old.json"
            path.parent.mkdir(parents=True)
            path.write_text("{}", encoding="utf-8")
            manager = JobStateManager(
                state_dir=state_dir,
                run_id="run-current",
                archive_dir_fn=_archive_dir_fn(root),
                started_at=time.time(),
                state_cleanup_legacy_grace_sec=300.0,
            )

            manager.archive_job_state_file(path, source_run_id="run-old", reason="unit_test")

            archived = root / "runs" / "run-old" / "state-archive" / "job-old.json"
            self.assertFalse(path.exists())
            self.assertTrue(archived.exists())

    def test_archive_stale_job_states_preserves_current_and_terminal_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            now = time.time()
            manager = JobStateManager(
                state_dir=state_dir,
                run_id="run-current",
                archive_dir_fn=_archive_dir_fn(root),
                started_at=now,
                state_cleanup_legacy_grace_sec=1.0,
            )
            previous = JobState(
                job_id="job-previous",
                status=JobStatus.VERIFY_RUNNING,
                artifact_path="work/previous.md",
                run_id="run-previous",
            )
            current = JobState(
                job_id="job-current",
                status=JobStatus.VERIFY_RUNNING,
                artifact_path="work/current.md",
                run_id="run-current",
            )
            done = JobState(
                job_id="job-done",
                status=JobStatus.VERIFY_DONE,
                artifact_path="work/done.md",
                run_id="run-previous",
            )
            legacy = JobState(
                job_id="job-legacy",
                status=JobStatus.VERIFY_RUNNING,
                artifact_path="work/legacy.md",
                run_id="",
                updated_at=now - 20.0,
            )
            for job in (previous, current, done, legacy):
                job.save(state_dir)
            legacy_path = jobs_state_dir(state_dir) / "job-legacy.json"
            old_ts = now - 20.0
            os.utime(legacy_path, (old_ts, old_ts))

            manager.archive_stale_job_states()

            self.assertTrue((jobs_state_dir(state_dir) / "job-current.json").exists())
            self.assertTrue((jobs_state_dir(state_dir) / "job-done.json").exists())
            self.assertFalse((jobs_state_dir(state_dir) / "job-previous.json").exists())
            self.assertFalse(legacy_path.exists())
            self.assertTrue(
                (root / "runs" / "run-previous" / "state-archive" / "job-previous.json").exists()
            )
            self.assertTrue((root / "state-archive" / "legacy" / "job-legacy.json").exists())

    def test_get_current_run_jobs_filters_status_and_sorts_latest_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            jobs = [
                JobState(
                    job_id="job-current-pending",
                    status=JobStatus.VERIFY_PENDING,
                    artifact_path="work/current-pending.md",
                    run_id="run-current",
                    last_dispatch_at=10.0,
                ),
                JobState(
                    job_id="job-blank-pending",
                    status=JobStatus.VERIFY_PENDING,
                    artifact_path="work/blank-pending.md",
                    run_id="",
                    last_dispatch_at=20.0,
                ),
                JobState(
                    job_id="job-current-running",
                    status=JobStatus.VERIFY_RUNNING,
                    artifact_path="work/current-running.md",
                    run_id="run-current",
                    last_dispatch_at=30.0,
                ),
                JobState(
                    job_id="job-old-pending",
                    status=JobStatus.VERIFY_PENDING,
                    artifact_path="work/old-pending.md",
                    run_id="run-old",
                    last_dispatch_at=40.0,
                ),
            ]
            for job in jobs:
                job.save(state_dir)
            manager = JobStateManager(
                state_dir=state_dir,
                run_id="run-current",
                archive_dir_fn=_archive_dir_fn(root),
                started_at=time.time(),
                state_cleanup_legacy_grace_sec=300.0,
            )

            current_pending = manager.get_current_run_jobs(statuses={JobStatus.VERIFY_PENDING})

            self.assertEqual(
                [job.job_id for job in current_pending],
                ["job-blank-pending", "job-current-pending"],
            )

    def test_archive_current_run_job_archives_matching_state_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            job = JobState(
                job_id="job-current",
                status=JobStatus.VERIFY_PENDING,
                artifact_path="work/current.md",
                run_id="run-current",
            )
            job.save(state_dir)
            manager = JobStateManager(
                state_dir=state_dir,
                run_id="run-current",
                archive_dir_fn=_archive_dir_fn(root),
                started_at=time.time(),
                state_cleanup_legacy_grace_sec=300.0,
            )

            archived = manager.archive_current_run_job(job, reason="unit_test")

            self.assertTrue(archived)
            self.assertFalse((jobs_state_dir(state_dir) / "job-current.json").exists())
            self.assertTrue(
                (root / "runs" / "run-current" / "state-archive" / "job-current.json").exists()
            )
