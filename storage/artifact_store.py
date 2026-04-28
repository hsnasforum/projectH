"""Grounded Brief artifact store.

Persists artifact records as individual JSON files under data/artifacts/.
Each artifact tracks its full lifecycle: creation, corrections, saves, outcomes.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from core.contracts import ArtifactRecord

from .json_store_base import utc_now_iso, json_path, atomic_write, read_json, scan_json_dir


class ArtifactStore:
    def __init__(self, base_dir: str = "data/artifacts") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, artifact_id: str) -> Path:
        return json_path(self.base_dir, artifact_id)

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
    ) -> ArtifactRecord:
        with self._lock:
            now = utc_now_iso()
            record: ArtifactRecord = {
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
            atomic_write(self._path(artifact_id), record)
            return record

    def get(self, artifact_id: str) -> ArtifactRecord | None:
        with self._lock:
            return read_json(self._path(artifact_id))

    def append_correction(
        self,
        artifact_id: str,
        *,
        corrected_text: str,
        outcome: str = "corrected",
    ) -> ArtifactRecord | None:
        with self._lock:
            record = self.get(artifact_id)
            if record is None:
                return None
            now = utc_now_iso()
            record["corrections"].append({
                "corrected_text": corrected_text,
                "outcome": outcome,
                "recorded_at": now,
            })
            record["latest_corrected_text"] = corrected_text
            record["latest_outcome"] = outcome
            record["updated_at"] = now
            atomic_write(self._path(artifact_id), record)
            return record

    def append_save(
        self,
        artifact_id: str,
        *,
        saved_note_path: str,
        save_content_source: str,
        approval_id: str | None = None,
    ) -> ArtifactRecord | None:
        with self._lock:
            record = self.get(artifact_id)
            if record is None:
                return None
            now = utc_now_iso()
            record["saves"].append({
                "saved_note_path": saved_note_path,
                "save_content_source": save_content_source,
                "approval_id": approval_id,
                "saved_at": now,
            })
            record["updated_at"] = now
            atomic_write(self._path(artifact_id), record)
            return record

    def record_outcome(
        self,
        artifact_id: str,
        *,
        outcome: str,
        content_verdict: str | None = None,
    ) -> ArtifactRecord | None:
        with self._lock:
            record = self.get(artifact_id)
            if record is None:
                return None
            record["latest_outcome"] = outcome
            if content_verdict is not None:
                record["content_verdict"] = content_verdict
            record["updated_at"] = utc_now_iso()
            atomic_write(self._path(artifact_id), record)
            return record

    # -- Queries --

    def list_by_session(self, session_id: str) -> list[ArtifactRecord]:
        with self._lock:
            results = [d for d in scan_json_dir(self.base_dir) if d.get("session_id") == session_id]
            return sorted(results, key=lambda d: d.get("created_at", ""), reverse=True)

    def list_recent(self, limit: int = 20) -> list[ArtifactRecord]:
        with self._lock:
            all_records = scan_json_dir(self.base_dir)
            all_records.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
            return all_records[:limit]
