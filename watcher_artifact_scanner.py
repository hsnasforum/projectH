from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pipeline_runtime.schema import (
    is_canonical_round_note,
    latest_verify_note_for_work,
    normalize_repo_artifact_path,
    same_day_verify_dir_for_work,
)
from verify_fsm import JobState, compute_file_sig, compute_md_tree_sig, compute_multi_file_sig

ROUND_NOTE_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
ROUND_NOTE_PATH_RE = re.compile(r"(?<!@)(?:\./)?([A-Za-z0-9_.\-/]+?\.[A-Za-z0-9]+)")
ROUND_NOTE_METADATA_ONLY_PREFIXES = ("work/", "verify/", "report/", ".pipeline/", "pipeline/")


@dataclass
class ArtifactScanner:
    watch_dir: Path
    verify_dir: Path
    repo_root: Path
    completion_paths: tuple[Path, ...] = ()

    def _repo_relative(self, path: Optional[Path]) -> str:
        if path is None:
            return ""
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)

    def _path_mtime(self, path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    def normalize_artifact_path(self, value: str | Path | None) -> str:
        return normalize_repo_artifact_path(value, self.repo_root)

    def is_canonical_round_note(self, root: Path, path: Path) -> bool:
        return is_canonical_round_note(
            root,
            path,
            work_root=self.watch_dir,
            verify_root=self.verify_dir,
        )

    def extract_changed_file_paths_from_round_note(self, work_path: Optional[Path]) -> list[str]:
        if work_path is None or not work_path.exists():
            return []
        try:
            lines = work_path.read_text().splitlines()
        except OSError:
            return []

        in_changed_files = False
        collected: list[str] = []
        for raw_line in lines:
            line = raw_line.rstrip()
            section = ROUND_NOTE_SECTION_RE.match(line.strip())
            if section:
                in_changed_files = section.group(1).strip() == "변경 파일"
                continue
            if not in_changed_files:
                continue
            if not line.strip():
                continue
            if line.lstrip().startswith("-"):
                bullet = line.lstrip()[1:].strip()
                if bullet == "없음":
                    continue
                for match in ROUND_NOTE_PATH_RE.finditer(bullet):
                    collected.append(match.group(1).lstrip("./"))
        return collected

    def is_metadata_only_work_note(self, work_path: Path) -> bool:
        if not self.is_canonical_round_note(self.watch_dir, work_path):
            return False
        changed_paths = [
            path.lstrip("./")
            for path in self.extract_changed_file_paths_from_round_note(work_path)
        ]
        if not changed_paths:
            return True
        work_rel = self._repo_relative(work_path)
        return all(
            path == work_rel or path.startswith(ROUND_NOTE_METADATA_ONLY_PREFIXES)
            for path in changed_paths
        )

    def is_dispatchable_work_note(self, work_path: Path) -> bool:
        return (
            self.is_canonical_round_note(self.watch_dir, work_path)
            and not self.is_metadata_only_work_note(work_path)
        )

    def find_latest_md(self, root: Path) -> Optional[Path]:
        latest_path: Optional[Path] = None
        latest_mtime = 0.0
        if not root.exists():
            return None
        for md in root.rglob("*.md"):
            if root == self.watch_dir:
                if not self.is_dispatchable_work_note(md):
                    continue
            elif not self.is_canonical_round_note(root, md):
                continue
            try:
                mt = md.stat().st_mtime
            except OSError:
                continue
            if mt >= latest_mtime:
                latest_path = md
                latest_mtime = mt
        return latest_path

    def get_latest_work_path(self) -> Optional[Path]:
        return self.find_latest_md(self.watch_dir)

    def find_latest_md_broad(self, root: Path) -> Optional[Path]:
        """Find latest canonical round note without metadata-only filtering."""
        latest_path: Optional[Path] = None
        latest_mtime = 0.0
        if not root.exists():
            return None
        for md in root.rglob("*.md"):
            if not self.is_canonical_round_note(root, md):
                continue
            try:
                mt = md.stat().st_mtime
            except OSError:
                continue
            if mt >= latest_mtime:
                latest_path = md
                latest_mtime = mt
        return latest_path

    def get_latest_work_path_broad(self) -> Optional[Path]:
        return self.find_latest_md_broad(self.watch_dir)

    def get_latest_same_day_verify_path(self, work_path: Optional[Path]) -> Optional[Path]:
        if work_path is None:
            return self.find_latest_md(self.verify_dir)

        try:
            rel = work_path.relative_to(self.watch_dir)
        except ValueError:
            return self.find_latest_md(self.verify_dir)

        if len(rel.parts) >= 2:
            same_day_dir = self.verify_dir / rel.parts[0] / rel.parts[1]
            latest_same_day = self.find_latest_md(same_day_dir)
            if latest_same_day is not None:
                return latest_same_day

        return self.find_latest_md(self.verify_dir)

    def get_latest_same_day_verify_path_for_work(self, work_path: Optional[Path]) -> Optional[Path]:
        if work_path is None:
            return None
        return latest_verify_note_for_work(
            self.watch_dir,
            self.verify_dir,
            work_path,
            repo_root=self.repo_root,
        )

    def get_same_day_verify_dir(self, work_path: Optional[Path]) -> Path:
        if work_path is None:
            return self.verify_dir
        return same_day_verify_dir_for_work(self.watch_dir, self.verify_dir, work_path)

    def build_verify_feedback_sigs(self, job: JobState) -> tuple[str, str]:
        del job
        control_sig = compute_multi_file_sig(list(self.completion_paths))
        verify_sig = compute_md_tree_sig(self.verify_dir)
        return control_sig, verify_sig

    def build_verify_receipt_state(self, job: JobState) -> tuple[str, float]:
        work_path = Path(job.artifact_path)
        latest_verify = (
            self.get_latest_same_day_verify_path_for_work(work_path)
            or self.get_latest_same_day_verify_path(work_path)
        )
        if latest_verify is None:
            return "", 0.0
        return self._repo_relative(latest_verify), self._path_mtime(latest_verify)

    def get_work_tree_snapshot(self) -> dict[str, str]:
        """work/ 전체 .md 스냅샷 반환."""
        snapshot: dict[str, str] = {}
        if not self.watch_dir.exists():
            return snapshot
        for md in self.watch_dir.rglob("*.md"):
            if not self.is_dispatchable_work_note(md):
                continue
            sig = compute_file_sig(md)
            if not sig:
                continue
            try:
                rel = str(md.relative_to(self.watch_dir))
            except ValueError:
                rel = str(md)
            snapshot[rel] = sig
        return snapshot

    def get_work_tree_snapshot_broad(self) -> dict[str, str]:
        """work/ 전체 canonical round-note 스냅샷 반환 (metadata-only 포함)."""
        snapshot: dict[str, str] = {}
        if not self.watch_dir.exists():
            return snapshot
        for md in self.watch_dir.rglob("*.md"):
            if not self.is_canonical_round_note(self.watch_dir, md):
                continue
            sig = compute_file_sig(md)
            if not sig:
                continue
            try:
                rel = str(md.relative_to(self.watch_dir))
            except ValueError:
                rel = str(md)
            snapshot[rel] = sig
        return snapshot

    def get_latest_work_mtime(self) -> float:
        """work/ 내 최신 .md 파일의 mtime 반환. 없으면 0.0."""
        latest = 0.0
        for md in self.watch_dir.rglob("*.md"):
            if not self.is_dispatchable_work_note(md):
                continue
            try:
                mt = md.stat().st_mtime
                if mt > latest:
                    latest = mt
            except OSError:
                continue
        return latest

    def work_has_matching_verify(
        self,
        work_path: Optional[Path],
        *,
        verified_work_paths: Optional[set[str]] = None,
    ) -> bool:
        if work_path is None:
            return False
        normalized_work = self.normalize_artifact_path(work_path)
        if not normalized_work:
            return False
        verified_paths = verified_work_paths or set()
        if normalized_work in verified_paths:
            return True
        latest_verify = self.get_latest_same_day_verify_path_for_work(work_path)
        if latest_verify is None:
            return False
        return self._path_mtime(latest_verify) >= self._path_mtime(work_path)

    def get_latest_unverified_work_path(
        self,
        *,
        include_metadata_only: bool,
        newer_than_mtime: float = 0.0,
        verified_work_paths: Optional[set[str]] = None,
    ) -> Optional[Path]:
        if not self.watch_dir.exists():
            return None
        candidates: list[tuple[float, Path]] = []
        for md in self.watch_dir.rglob("*.md"):
            if include_metadata_only:
                if not self.is_canonical_round_note(self.watch_dir, md):
                    continue
            elif not self.is_dispatchable_work_note(md):
                continue
            try:
                mt = md.stat().st_mtime
            except OSError:
                continue
            if newer_than_mtime > 0.0 and mt < newer_than_mtime:
                continue
            candidates.append((mt, md))
        for _, md in sorted(candidates, key=lambda item: item[0], reverse=True):
            if self.work_has_matching_verify(md, verified_work_paths=verified_work_paths):
                continue
            return md
        return None

    def latest_work_needs_verify(
        self,
        *,
        verified_work_paths: Optional[set[str]] = None,
    ) -> bool:
        latest_work = self.get_latest_work_path()
        if latest_work is None:
            return False
        return not self.work_has_matching_verify(
            latest_work,
            verified_work_paths=verified_work_paths,
        )

    def latest_work_needs_verify_broad(
        self,
        *,
        verified_work_paths: Optional[set[str]] = None,
    ) -> bool:
        """Like latest_work_needs_verify but includes metadata-only notes for the latest round only."""
        latest_work = self.get_latest_work_path_broad()
        if latest_work is None:
            return False
        return not self.work_has_matching_verify(
            latest_work,
            verified_work_paths=verified_work_paths,
        )

    def get_latest_verify_candidate_path(
        self,
        *,
        verified_work_paths: Optional[set[str]] = None,
    ) -> Optional[Path]:
        """Latest canonical work note that should drive automatic verify/handoff rerun.

        Historical unmatched backlog is not reopened by fresh scans; only the newest canonical
        round note may open a new automatic verify job. Older notes can still continue when a
        current-run VERIFY_PENDING / VERIFY_RUNNING job already exists.
        """
        latest_work = self.get_latest_work_path_broad()
        if latest_work is None:
            return None
        if self.work_has_matching_verify(
            latest_work,
            verified_work_paths=verified_work_paths,
        ):
            return None
        return latest_work
