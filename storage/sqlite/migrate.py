"""JSON-to-SQLite migration utility."""

from __future__ import annotations

import json
from pathlib import Path

from storage.sqlite.artifact import SQLiteArtifactStore
from storage.sqlite.correction import SQLiteCorrectionStore
from storage.sqlite.database import SQLiteDatabase, _now_iso
from storage.sqlite.preference import SQLitePreferenceStore
from storage.sqlite.session import SQLiteSessionStore
from storage.sqlite.task_log import SQLiteTaskLogger


# ── Migration utility ─────────────────────────────────────────────

def migrate_json_to_sqlite(
    *,
    sessions_dir: str | None = "data/sessions",
    artifacts_dir: str | None = "data/artifacts",
    corrections_dir: str = "data/corrections",
    preferences_dir: str | None = "data/preferences",
    db_path: str = "data/projecth.db",
) -> dict[str, int]:
    """Migrate JSON file stores to SQLite. Returns counts per table.

    Pass None for an optional directory to skip that table family.
    """
    db = SQLiteDatabase(db_path)
    counts: dict[str, int] = {}
    errors: list[str] = []

    # Corrections
    corrections_path = Path(corrections_dir)
    count = 0
    if corrections_path.is_dir():
        for f in corrections_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                now = data.get("created_at", _now_iso())
                cursor = db.execute(
                    "INSERT OR IGNORE INTO corrections "
                    "(correction_id, artifact_id, session_id, delta_fingerprint, status, data, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        data["correction_id"],
                        data.get("artifact_id", ""),
                        data.get("session_id", ""),
                        data.get("delta_fingerprint", ""),
                        data.get("status", "recorded"),
                        json.dumps(data, ensure_ascii=False, default=str),
                        now,
                        data.get("updated_at", now),
                    ),
                )
                count += max(cursor.rowcount, 0)
            except Exception as exc:
                errors.append(f"correction {f.name}: {exc}")
                continue
    db.commit()
    counts["corrections"] = count

    # Sessions
    count = 0
    if sessions_dir is not None and (sessions_path := Path(sessions_dir)).is_dir():
        for f in sessions_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sid = data.get("session_id", f.stem)
                store = SQLiteSessionStore(db)
                store._save(sid, data)
                count += 1
            except Exception as exc:
                errors.append(f"session {f.name}: {exc}")
                continue
    counts["sessions"] = count

    # Artifacts
    count = 0
    if artifacts_dir is not None and (artifacts_path := Path(artifacts_dir)).is_dir():
        for f in artifacts_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                now = data.get("created_at", _now_iso())
                db.execute(
                    "INSERT OR IGNORE INTO artifacts (artifact_id, artifact_kind, session_id, source_message_id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (data["artifact_id"], data.get("artifact_kind", "grounded_brief"), data.get("session_id", ""), data.get("source_message_id", ""), json.dumps(data, ensure_ascii=False, default=str), now, now),
                )
                count += 1
            except Exception as exc:
                errors.append(f"artifact {f.name}: {exc}")
                continue
    db.commit()
    counts["artifacts"] = count

    # Preferences
    count = 0
    if preferences_dir is not None and (prefs_path := Path(preferences_dir)).is_dir():
        for f in prefs_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                now = data.get("created_at", _now_iso())
                db.execute(
                    "INSERT OR IGNORE INTO preferences (preference_id, delta_fingerprint, description, status, data, created_at, updated_at, activated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (data["preference_id"], data.get("delta_fingerprint", ""), data.get("description", ""), data.get("status", "candidate"), json.dumps(data, ensure_ascii=False, default=str), now, now, data.get("activated_at")),
                )
                count += 1
            except Exception as exc:
                errors.append(f"preference {f.name}: {exc}")
                continue
    db.commit()
    counts["preferences"] = count

    if errors:
        counts["_errors"] = errors  # type: ignore[assignment]

    db.close()
    return counts

