from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class TaskLogger:
    def __init__(self, path: str = "logs/task_log.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, *, session_id: str, action: str, detail: Dict[str, Any]) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "action": action,
            "detail": detail,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def iter_session_records(self, session_id: str) -> list[Dict[str, Any]]:
        normalized = (session_id or "").strip() or None
        if normalized is None or not self.path.exists():
            return []
        records: list[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    loaded = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(loaded, dict):
                    continue
                if (loaded.get("session_id") or "").strip() != normalized:
                    continue
                records.append(loaded)
        return records
