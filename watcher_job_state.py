from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pipeline_runtime.schema import iter_job_state_paths
from verify_fsm import JobState, JobStatus, TERMINAL_STATES

log = logging.getLogger(__name__)


@dataclass
class JobStateManager:
    state_dir: Path
    run_id: str
    archive_dir_fn: Callable[[str], Path]
    started_at: float
    state_cleanup_legacy_grace_sec: float

    def archive_job_state_file(
        self,
        path: Path,
        *,
        source_run_id: str = "",
        reason: str,
    ) -> None:
        archive_dir = self.archive_dir_fn(source_run_id)
        archive_dir.mkdir(parents=True, exist_ok=True)
        target = archive_dir / path.name
        if target.exists():
            target = archive_dir / f"{path.stem}-{int(time.time())}{path.suffix}"
        try:
            path.replace(target)
        except OSError as exc:
            log.warning("failed to archive stale job state: %s (%s)", path, exc)
            return
        log.info("archived stale job state: %s -> %s (%s)", path, target, reason)

    def archive_stale_job_states(self) -> None:
        if not self.state_dir.exists():
            return
        terminal_values = {status.value for status in TERMINAL_STATES}
        archived = 0
        legacy_cutoff = self.started_at - self.state_cleanup_legacy_grace_sec
        for path in iter_job_state_paths(self.state_dir):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            status = str(data.get("status") or "").strip()
            if status in terminal_values:
                continue
            state_run_id = str(data.get("run_id") or "").strip()
            if state_run_id:
                if state_run_id == self.run_id:
                    continue
                self.archive_job_state_file(
                    path,
                    source_run_id=state_run_id,
                    reason="previous_run_nonterminal",
                )
                archived += 1
                continue
            try:
                state_mtime = path.stat().st_mtime
            except OSError:
                state_mtime = 0.0
            updated_at = float(data.get("updated_at") or 0.0)
            if max(state_mtime, updated_at) >= legacy_cutoff:
                continue
            self.archive_job_state_file(
                path,
                reason="legacy_nonterminal_before_startup",
            )
            archived += 1
        if archived:
            log.info("archived %d stale job state files before startup", archived)

    def get_current_run_jobs(
        self,
        *,
        statuses: Optional[set[JobStatus]] = None,
    ) -> list[JobState]:
        """Load current-run watcher jobs from shared state.

        Blank run_id is tolerated for test scaffolds and legacy local state.
        """
        if not self.state_dir.exists():
            return []
        jobs: list[JobState] = []
        seen_job_ids: set[str] = set()
        for path in iter_job_state_paths(self.state_dir):
            if path.stem in seen_job_ids:
                continue
            seen_job_ids.add(path.stem)
            job = JobState.load(self.state_dir, path.stem)
            if job is None:
                continue
            if job.run_id and job.run_id != self.run_id:
                continue
            if statuses is not None and job.status not in statuses:
                continue
            jobs.append(job)
        jobs.sort(
            key=lambda job: (
                float(job.last_dispatch_at or 0.0),
                float(job.updated_at or 0.0),
                str(job.job_id),
            ),
            reverse=True,
        )
        return jobs

    def archive_current_run_job(self, job: JobState, *, reason: str) -> bool:
        archived = False
        source_run_id = job.run_id or self.run_id
        for path in iter_job_state_paths(self.state_dir):
            if path.stem != job.job_id:
                continue
            self.archive_job_state_file(path, source_run_id=source_run_id, reason=reason)
            archived = True
        return archived
