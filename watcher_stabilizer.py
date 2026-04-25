from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def compute_file_sha256(path: Path) -> str:
    """파일 내용 기준 sha256 hex. 읽을 수 없으면 빈 문자열."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


@dataclass
class StabilizeSnapshot:
    hash:  str
    size:  int
    mtime: float


class ArtifactStabilizer:
    """hash + mtime + size 3중 비교로 연속 N회 동일할 때만 안정화 완료 판정."""

    def __init__(self, settle_sec: float = 3.0, required_stable: int = 2) -> None:
        self.settle_sec      = settle_sec
        self.required_stable = required_stable
        self._snapshots: dict[str, list[StabilizeSnapshot]] = {}

    def _snapshot(self, path: Path) -> Optional[StabilizeSnapshot]:
        try:
            stat = path.stat()
            h    = hashlib.sha256(path.read_bytes()).hexdigest()
            return StabilizeSnapshot(hash=h, size=stat.st_size, mtime=stat.st_mtime)
        except OSError:
            return None

    def check(self, job_id: str, artifact_path: str) -> bool:
        path = Path(artifact_path)
        snap = self._snapshot(path)
        if snap is None:
            self._snapshots.pop(job_id, None)
            return False

        if time.time() - snap.mtime < self.settle_sec:
            self._snapshots.pop(job_id, None)
            return False

        history = self._snapshots.setdefault(job_id, [])

        # hash + size + mtime 3중 비교 — touch처럼 내용 동일 mtime 변경도 리셋
        if history and history[-1] != snap:
            self._snapshots[job_id] = []
            history = self._snapshots[job_id]

        history.append(snap)
        return len(history) >= self.required_stable

    def clear(self, job_id: str) -> None:
        self._snapshots.pop(job_id, None)
