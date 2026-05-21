from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline_runtime.schema import iso_utc, process_starttime_fingerprint


def _watcher_repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


@dataclass
class WatcherRuntimeExporter:
    enabled: bool
    run_id: str
    run_dir: Path
    run_status_path: Path
    run_events_path: Path
    current_run_path: Path
    repo_root: Path
    _event_seq: int = field(default=0, init=False)

    def write_run_pointer(self) -> None:
        if not self.enabled:
            return
        # watcher가 자기 process identity(`watcher_pid` + `watcher_fingerprint`)를
        # current_run.json에 같이 남겨야, supervisor 재시작 inheritance가 watcher가
        # 직접 쓴 pointer를 보고도 같은 owner-match 계약 아래에서 prior run_id를
        # 이어받을 수 있다.
        watcher_pid = os.getpid()
        watcher_fingerprint = process_starttime_fingerprint(watcher_pid)
        data = {
            "run_id": self.run_id,
            "status_path": _watcher_repo_relative(self.run_status_path, self.repo_root),
            "events_path": _watcher_repo_relative(self.run_events_path, self.repo_root),
            "watcher_pid": watcher_pid,
            "watcher_fingerprint": watcher_fingerprint,
            "updated_at": iso_utc(),
        }
        tmp_path = self.current_run_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp_path.replace(self.current_run_path)

    def append_event(self, event_type: str, payload: dict[str, object]) -> None:
        if not self.enabled:
            return
        self._event_seq += 1
        entry: dict[str, Any] = {
            "seq": self._event_seq,
            "ts": iso_utc(),
            "run_id": self.run_id,
            "event_type": event_type,
            "source": "watcher-exporter",
            "payload": payload,
        }
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with self.run_events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
