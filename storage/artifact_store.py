"""Grounded Brief artifact store.

Persists artifact records as individual JSON files under data/artifacts/.
Each artifact tracks its full lifecycle: creation, corrections, saves, outcomes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
import threading
from typing import Any
from uuid import uuid4


class ArtifactStore:
    def __init__(self, base_dir: str = "data/artifacts") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, artifact_id: str) -> Path:
        safe_id = artifact_id.replace("/", "-").replace("\\", "-").strip()
        return self.base_dir / f"{safe_id}.json"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _atomic_write(self, path: Path, data: dict[str, Any]) -> None:
        temp_path = path.with_name(f"{path.name}.{uuid4().hex[:8]}.tmp")
        encoded = json.dumps(data, ensure_ascii=False, indent=2)
        try:
            temp_path.write_text(encoded, encoding="utf-8")
            temp_path.replace(path)
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise

    # -- CRUD --

    def create(
        self,
        *,
        artifact_id: str,
        artifact_kind: str,
        session_id: str,
        source_message_id: str,
        draft_text: str,
        source_paths: list[str] | None = None,
        response_origin: dict[str, Any] | None = None,
        summary_chunks: list[dict[str, Any]] | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            now = self._now()
            record: dict[str, Any] = {
                "artifact_id": artifact_id,
                "artifact_kind": artifact_kind,
                "session_id": session_id,
                "source_message_id": source_message_id,
                "created_at": now,
                "updated_at": now,
                "draft_text": draft_text,
                "source_paths": source_paths or [],
                "response_origin": response_origin,
                "summary_chunks": summary_chunks or [],
                "evidence": evidence or [],
                "corrections": [],
                "saves": [],
                "latest_corrected_text": None,
                "latest_outcome": None,
                "content_verdict": None,
            }
            self._atomic_write(self._path(artifact_id), record)
            return record

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        with self._lock:
            path = self._path(artifact_id)
            if not path.exists():
                return None
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (JSONDecodeError, OSError):
                return None

    def append_correction(
        self,
        artifact_id: str,
        *,
        corrected_text: str,
        outcome: str = "corrected",
    ) -> dict[str, Any] | None:
        with self._lock:
            record = self.get(artifact_id)
            if record is None:
                return None
            now = self._now()
            record["corrections"].append({
                "corrected_text": corrected_text,
                "outcome": outcome,
                "recorded_at": now,
            })
            record["latest_corrected_text"] = corrected_text
            record["latest_outcome"] = outcome
            record["updated_at"] = now
            self._atomic_write(self._path(artifact_id), record)
            return record

    def append_save(
        self,
        artifact_id: str,
        *,
        saved_note_path: str,
        save_content_source: str,
        approval_id: str | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            record = self.get(artifact_id)
            if record is None:
                return None
            now = self._now()
            record["saves"].append({
                "saved_note_path": saved_note_path,
                "save_content_source": save_content_source,
                "approval_id": approval_id,
                "saved_at": now,
            })
            record["updated_at"] = now
            self._atomic_write(self._path(artifact_id), record)
            return record

    def record_outcome(
        self,
        artifact_id: str,
        *,
        outcome: str,
        content_verdict: str | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            record = self.get(artifact_id)
            if record is None:
                return None
            record["latest_outcome"] = outcome
            if content_verdict is not None:
                record["content_verdict"] = content_verdict
            record["updated_at"] = self._now()
            self._atomic_write(self._path(artifact_id), record)
            return record

    # -- Queries --

    def list_by_session(self, session_id: str) -> list[dict[str, Any]]:
        with self._lock:
            results: list[dict[str, Any]] = []
            for path in self.base_dir.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if data.get("session_id") == session_id:
                        results.append(data)
                except (JSONDecodeError, OSError):
                    continue
            return sorted(results, key=lambda d: d.get("created_at", ""), reverse=True)

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            all_records: list[dict[str, Any]] = []
            for path in self.base_dir.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    all_records.append(data)
                except (JSONDecodeError, OSError):
                    continue
            all_records.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
            return all_records[:limit]
