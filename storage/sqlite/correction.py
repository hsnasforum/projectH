"""SQLite-backed correction store."""

from __future__ import annotations

import json
import threading
from typing import Any

from core.contracts import (
    CandidateFamily,
    CORRECTION_STATUS_TRANSITIONS,
    CorrectionRecord,
    CorrectionStatus,
)
from storage.correction_store import _is_valid_correction_record
from storage.sqlite.database import SQLiteDatabase, _new_id, _now_iso


# ── SQLite Correction Store ───────────────────────────────────────

class SQLiteCorrectionStore:
    """Core CorrectionStore lookup parity, backed by SQLite."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db
        self._lock = threading.RLock()

    def record_correction(
        self,
        *,
        artifact_id: str,
        session_id: str,
        source_message_id: str,
        original_text: str,
        corrected_text: str,
        pattern_family: str = CandidateFamily.CORRECTION_REWRITE,
        applied_preference_ids: list[str] | None = None,
    ) -> CorrectionRecord | None:
        """Record a correction and compute its delta. Returns None if no delta."""
        from core.delta_analysis import compute_correction_delta

        delta = compute_correction_delta(original_text, corrected_text)
        if delta is None:
            return None

        with self._lock:
            duplicate_rows = self._db.fetchall(
                "SELECT * FROM corrections WHERE delta_fingerprint = ? AND artifact_id = ? AND session_id = ?",
                (delta.delta_fingerprint, artifact_id, session_id),
            )
            for row in duplicate_rows:
                existing = self._row_to_dict(row)
                if existing.get("source_message_id") == source_message_id:
                    return existing

            existing_rows = self._db.fetchall(
                "SELECT * FROM corrections WHERE delta_fingerprint = ? ORDER BY created_at",
                (delta.delta_fingerprint,),
            )
            recurrence_count = len(existing_rows) + 1
            now = _now_iso()

            for row in existing_rows:
                existing = self._row_to_dict(row)
                existing["recurrence_count"] = recurrence_count
                existing["last_seen_at"] = now
                existing["updated_at"] = now
                self._db.execute(
                    "UPDATE corrections SET data = ?, updated_at = ? WHERE correction_id = ?",
                    (
                        json.dumps(existing, ensure_ascii=False, default=str),
                        now,
                        row["correction_id"],
                    ),
                )

            correction_id = f"correction-{_new_id()}"
            record: dict[str, Any] = {
                "correction_id": correction_id,
                "artifact_id": artifact_id,
                "session_id": session_id,
                "source_message_id": source_message_id,
                "original_text": original_text,
                "corrected_text": corrected_text,
                "delta_fingerprint": delta.delta_fingerprint,
                "delta_summary": delta.delta_summary,
                "similarity_score": delta.similarity_score,
                "rewrite_dimensions": delta.rewrite_dimensions,
                "pattern_family": pattern_family,
                "applied_preference_ids": applied_preference_ids,
                "recurrence_count": recurrence_count,
                "first_seen_at": now,
                "last_seen_at": now,
                "status": CorrectionStatus.RECORDED,
                "confirmed_at": None,
                "promoted_at": None,
                "activated_at": None,
                "stopped_at": None,
                "created_at": now,
                "updated_at": now,
            }
            self._db.execute(
                "INSERT INTO corrections "
                "(correction_id, artifact_id, session_id, delta_fingerprint, status, data, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    correction_id,
                    artifact_id,
                    session_id,
                    delta.delta_fingerprint,
                    record["status"],
                    json.dumps(record, ensure_ascii=False, default=str),
                    record["created_at"],
                    record["updated_at"],
                ),
            )
            self._db.commit()
            return record

    def get(self, correction_id: str) -> CorrectionRecord | None:
        row = self._db.fetchone("SELECT * FROM corrections WHERE correction_id = ?", (correction_id,))
        if not row:
            return None
        return self._row_to_dict(row)

    def find_by_fingerprint(self, delta_fingerprint: str) -> list[CorrectionRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM corrections WHERE delta_fingerprint = ? ORDER BY created_at",
            (delta_fingerprint,),
        )
        return [self._row_to_dict(row) for row in rows]

    def find_by_artifact(self, artifact_id: str) -> list[CorrectionRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM corrections WHERE artifact_id = ? ORDER BY created_at",
            (artifact_id,),
        )
        return [self._row_to_dict(row) for row in rows]

    def find_by_session(self, session_id: str) -> list[CorrectionRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM corrections WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        )
        return [self._row_to_dict(row) for row in rows]

    def list_recent(self, limit: int = 20) -> list[CorrectionRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM corrections ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [
            record
            for record in (self._row_to_dict(row) for row in rows)
            if _is_valid_correction_record(record)
        ]

    def list_filtered(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[CorrectionRecord]:
        clauses: list[str] = []
        params: list[object] = []
        if query:
            clauses.append(
                "(COALESCE(json_extract(data, '$.original_text'), '') LIKE ? "
                "OR COALESCE(json_extract(data, '$.corrected_text'), '') LIKE ?)"
            )
            like = f"%{query}%"
            params.extend([like, like])
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        rows = self._db.fetchall(
            f"SELECT * FROM corrections {where} ORDER BY updated_at DESC LIMIT ?",
            tuple(params),
        )
        return [
            record
            for record in (self._row_to_dict(row) for row in rows)
            if _is_valid_correction_record(record)
        ]

    def list_incomplete_corrections(self) -> list[CorrectionRecord]:
        with self._lock:
            rows = self._db.fetchall(
                "SELECT * FROM corrections WHERE status IN (?, ?, ?) ORDER BY created_at ASC",
                (
                    CorrectionStatus.RECORDED,
                    CorrectionStatus.CONFIRMED,
                    CorrectionStatus.PROMOTED,
                ),
            )
            return [self._row_to_dict(row) for row in rows]

    def find_adopted_corrections(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._db.fetchall(
                "SELECT * FROM corrections WHERE status = ?",
                (CorrectionStatus.ACTIVE,),
            )
            records = [self._row_to_dict(row) for row in rows]
            records.sort(key=lambda r: r.get("activated_at") or "")
            return records

    def find_recurring_patterns(self, *, session_id: str | None = None) -> list[dict[str, Any]]:
        """Return correction groups with recurrence_count >= 2, matching CorrectionStore contract."""
        if session_id:
            fp_rows = self._db.fetchall(
                "SELECT delta_fingerprint FROM corrections WHERE session_id = ? "
                "GROUP BY delta_fingerprint HAVING COUNT(*) >= 2",
                (session_id,),
            )
        else:
            fp_rows = self._db.fetchall(
                "SELECT delta_fingerprint FROM corrections "
                "GROUP BY delta_fingerprint HAVING COUNT(DISTINCT session_id) >= 2"
            )

        patterns: list[dict[str, Any]] = []
        for fp_row in fp_rows:
            fp = fp_row["delta_fingerprint"]
            if not fp:
                continue
            if session_id:
                rows = self._db.fetchall(
                    "SELECT * FROM corrections WHERE delta_fingerprint = ? AND session_id = ? "
                    "ORDER BY created_at",
                    (fp, session_id),
                )
            else:
                rows = self._db.fetchall(
                    "SELECT * FROM corrections WHERE delta_fingerprint = ? ORDER BY created_at",
                    (fp,),
                )
            records = [self._row_to_dict(row) for row in rows]
            if len(records) < 2:
                continue
            patterns.append({
                "delta_fingerprint": fp,
                "pattern_family": records[0].get("pattern_family", ""),
                "recurrence_count": len(records),
                "corrections": records,
                "first_seen_at": min(
                    (record.get("first_seen_at") or record.get("created_at") or "")
                    for record in records
                ),
                "last_seen_at": max(
                    (record.get("last_seen_at") or record.get("updated_at") or "")
                    for record in records
                ),
            })
        return patterns

    def _row_to_dict(self, row: dict[str, Any]) -> dict[str, Any]:
        data = json.loads(row["data"]) if isinstance(row.get("data"), str) else {}
        data.update({
            "correction_id": row["correction_id"],
            "artifact_id": row["artifact_id"],
            "session_id": row["session_id"],
            "delta_fingerprint": row["delta_fingerprint"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        })
        return data

    def _transition(self, correction_id: str, status: str, timestamp_field: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.fetchone("SELECT * FROM corrections WHERE correction_id = ?", (correction_id,))
            if not row:
                return None
            record = self._row_to_dict(row)
            current_status = record.get("status")
            allowed = CORRECTION_STATUS_TRANSITIONS.get(current_status, ())
            if status not in allowed:
                return None
            now = _now_iso()
            record["status"] = status
            record[timestamp_field] = now
            record["updated_at"] = now
            self._db.execute(
                "UPDATE corrections SET status = ?, data = ?, updated_at = ? WHERE correction_id = ?",
                (
                    status,
                    json.dumps(record, ensure_ascii=False, default=str),
                    now,
                    correction_id,
                ),
            )
            self._db.commit()
            return record

    def confirm_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.CONFIRMED, "confirmed_at")

    def promote_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.PROMOTED, "promoted_at")

    def activate_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.ACTIVE, "activated_at")

    def stop_correction(self, correction_id: str) -> dict[str, Any] | None:
        return self._transition(correction_id, CorrectionStatus.STOPPED, "stopped_at")

    def _scan_all(self) -> list[CorrectionRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM corrections ORDER BY created_at",
        )
        return [self._row_to_dict(row) for row in rows]

    def confirm_by_fingerprint(self, delta_fingerprint: str) -> list[CorrectionRecord]:
        records = self.find_by_fingerprint(delta_fingerprint)
        confirmed: list[CorrectionRecord] = []
        for r in records:
            result = self.confirm_correction(str(r.get("correction_id") or ""))
            if result is not None:
                confirmed.append(result)
        return confirmed

    def promote_by_fingerprint(self, delta_fingerprint: str) -> list[CorrectionRecord]:
        records = self.find_by_fingerprint(delta_fingerprint)
        promoted: list[CorrectionRecord] = []
        for r in records:
            if r.get("status") != CorrectionStatus.CONFIRMED:
                continue
            result = self.promote_correction(str(r.get("correction_id") or ""))
            if result is not None:
                promoted.append(result)
        return promoted

    def dismiss_by_fingerprint(self, delta_fingerprint: str) -> list[CorrectionRecord]:
        records = self.find_by_fingerprint(delta_fingerprint)
        dismissed: list[CorrectionRecord] = []
        for r in records:
            result = self.stop_correction(str(r.get("correction_id") or ""))
            if result is not None:
                dismissed.append(result)
        return dismissed

