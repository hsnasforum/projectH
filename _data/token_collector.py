#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import signal
import sqlite3
import sys
import time
from collections.abc import Callable
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if __package__ in (None, ""):
    sys.path.insert(0, str(SCRIPT_DIR))
    sys.path.insert(0, str(SCRIPT_DIR.parent))

try:
    from _data.job_linker import relink_jobs
    from _data.token_parsers import ClaudeParser, CodexParser, GeminiParser
    from _data.token_store import TokenStore
except ModuleNotFoundError:
    from job_linker import relink_jobs
    from token_parsers import ClaudeParser, CodexParser, GeminiParser
    from token_store import TokenStore


class TokenCollector:
    def __init__(
        self,
        project_root: Path,
        db_path: Path,
        poll_interval: float = 3.0,
        since_days: int | None = None,
        force_rescan: bool = False,
    ) -> None:
        self.project_root = project_root.resolve()
        self.poll_interval = poll_interval
        self.since_days = since_days
        self.force_rescan = force_rescan
        self.store = TokenStore(db_path)
        self.parsers = {
            "claude": (ClaudeParser(), Path.home() / ".claude" / "projects", "*.jsonl"),
            "codex": (CodexParser(), Path.home() / ".codex" / "sessions", "*.jsonl"),
            "gemini": (GeminiParser(), Path.home() / ".gemini" / "tmp", "logs.json"),
        }
        self.pipeline_log_specs = [
            (self.project_root / ".pipeline" / "logs" / "experimental" / "dispatch.jsonl", "experimental"),
            (self.project_root / ".pipeline" / "logs" / "experimental" / "raw.jsonl", "experimental"),
            (self.project_root / ".pipeline" / "logs" / "dispatch.jsonl", "default"),
            (self.project_root / ".pipeline" / "logs" / "raw.jsonl", "default"),
        ]
        self._running = True

    def run_forever(self) -> None:
        self.store.update_collector_status("starting", last_error="")
        while self._running:
            try:
                summary = self.run_once()
                print(json.dumps(summary, ensure_ascii=False), flush=True)
            except Exception as exc:
                self.store.update_collector_status("error", last_error=str(exc))
                print(json.dumps({"error": str(exc)}, ensure_ascii=False), flush=True)
            time.sleep(self.poll_interval)

    def stop(self, *_args) -> None:
        self._running = False

    def run_once(self) -> dict[str, int]:
        return self.run_once_with_progress()

    def run_once_with_progress(
        self,
        progress_callback: Callable[[dict[str, object]], None] | None = None,
    ) -> dict[str, object]:
        started = time.perf_counter()
        scan_started_at = _utc_now_iso()
        self.store.update_collector_status(
            "scanning",
            last_scan_started_at=scan_started_at,
            last_error="",
        )
        usage_inserted = 0
        pipeline_inserted = 0
        linked_jobs = 0
        scanned_files = 0
        parsed_files = 0
        parsed_events = 0
        usage_duplicates = 0
        pipeline_duplicates = 0
        retry_later = 0
        last_error = ""
        last_progress_emit = 0.0
        total_files = 0

        if progress_callback is not None:
            progress_callback(
                {
                    "event": "progress",
                    "phase": "preparing",
                    "usage_inserted": 0,
                    "pipeline_inserted": 0,
                    "linked_jobs": 0,
                    "scanned_files": 0,
                    "parsed_files": 0,
                    "total_files": 0,
                    "progress_percent": 0,
                    "parsed_events": 0,
                    "usage_duplicates": 0,
                    "pipeline_duplicates": 0,
                    "duplicates": 0,
                    "retry_later": 0,
                    "elapsed_sec": 0.0,
                }
            )
        usage_targets = self._collect_usage_targets()
        pipeline_targets = self._collect_pipeline_targets()
        total_files = len(usage_targets) + len(pipeline_targets)

        def _emit_progress(phase: str, force: bool = False) -> None:
            nonlocal last_progress_emit
            if progress_callback is None:
                return
            now = time.perf_counter()
            if not force and (now - last_progress_emit) < 0.35:
                return
            last_progress_emit = now
            progress_callback(
                {
                    "event": "progress",
                    "phase": phase,
                    "usage_inserted": usage_inserted,
                    "pipeline_inserted": pipeline_inserted,
                    "linked_jobs": linked_jobs,
                    "scanned_files": scanned_files,
                    "parsed_files": parsed_files,
                    "total_files": total_files,
                    "progress_percent": _progress_percent(scanned_files, total_files, phase),
                    "parsed_events": parsed_events,
                    "usage_duplicates": usage_duplicates,
                    "pipeline_duplicates": pipeline_duplicates,
                    "duplicates": usage_duplicates + pipeline_duplicates,
                    "retry_later": retry_later,
                    "elapsed_sec": round(time.perf_counter() - started, 3),
                }
            )

        _emit_progress("scanning", force=True)

        for parser_kind, path in usage_targets:
            parser = self.parsers[parser_kind][0]
            scanned_files += 1
            result = parser.parse_file(path)
            parsed_files += 1
            parsed_events += result.parsed_events
            if result.last_error:
                last_error = result.last_error
            inserted = self.store.insert_usage_entries(result.entries)
            usage_inserted += inserted
            usage_duplicates += max(0, len(result.entries) - inserted)
            if result.retry_later:
                retry_later += 1
            if not result.trailing_incomplete and not result.retry_later:
                self._update_file_state(path, parser_kind, result.entries)
            _emit_progress("scanning")

        pipeline_changed = False
        for path, log_family in pipeline_targets:
            scanned_files += 1
            parsed_files += 1
            events = self._parse_pipeline_event_file(path, log_family)
            inserted = self.store.insert_pipeline_events(events)
            pipeline_inserted += inserted
            pipeline_duplicates += max(0, len(events) - inserted)
            parsed_events += len(events)
            self._update_pipeline_state(path, events)
            pipeline_changed = True
            _emit_progress("scanning")

        if pipeline_changed or usage_inserted:
            with self.store.connect() as conn:
                linked_jobs = relink_jobs(conn)

        elapsed_sec = round(time.perf_counter() - started, 3)
        try:
            db_size_mb = round(self.store.db_path.stat().st_size / (1024 * 1024), 3)
        except OSError:
            db_size_mb = 0.0
        summary = {
            "usage_inserted": usage_inserted,
            "pipeline_inserted": pipeline_inserted,
            "linked_jobs": linked_jobs,
            "scanned_files": scanned_files,
            "parsed_files": parsed_files,
            "total_files": total_files,
            "progress_percent": _progress_percent(scanned_files, total_files, "idle"),
            "parsed_events": parsed_events,
            "usage_duplicates": usage_duplicates,
            "pipeline_duplicates": pipeline_duplicates,
            "duplicates": usage_duplicates + pipeline_duplicates,
            "retry_later": retry_later,
            "elapsed_sec": elapsed_sec,
            "db_size_mb": db_size_mb,
        }
        self.store.update_collector_status(
            "idle",
            last_scan_started_at=scan_started_at,
            last_scan_finished_at=_utc_now_iso(),
            scanned_files=scanned_files,
            parsed_events=parsed_events,
            last_error=last_error,
        )
        _emit_progress("idle", force=True)
        return summary

    def _collect_usage_targets(self) -> list[tuple[str, Path]]:
        targets: list[tuple[str, Path]] = []
        for parser_kind, (_parser, root, pattern) in self.parsers.items():
            if not root.exists():
                continue
            for path in root.rglob(pattern):
                if not path.is_file():
                    continue
                if not self._should_scan(path):
                    continue
                targets.append((parser_kind, path))
        return targets

    def _collect_pipeline_targets(self) -> list[tuple[Path, str]]:
        targets: list[tuple[Path, str]] = []
        for path, log_family in self.pipeline_log_specs:
            if not path.exists() or not path.is_file():
                continue
            if not self._should_scan(path):
                continue
            targets.append((path, log_family))
        return targets

    def _should_scan(self, path: Path) -> bool:
        try:
            stat = path.stat()
        except OSError:
            return False
        if self.force_rescan:
            if self.since_days is not None and self.since_days >= 0:
                cutoff = time.time() - (self.since_days * 86400)
                if stat.st_mtime < cutoff:
                    return False
            return True
        state = self.store.get_file_state(path)
        if state is None:
            if self.since_days is not None and self.since_days >= 0:
                cutoff = time.time() - (self.since_days * 86400)
                if stat.st_mtime < cutoff:
                    return False
            return True
        return int(state["mtime_ns"]) != stat.st_mtime_ns or int(state["size"]) != stat.st_size

    def _update_file_state(self, path: Path, parser_kind: str, entries) -> None:
        try:
            stat = path.stat()
        except OSError:
            return
        last_offset = None
        last_line_no = None
        if entries:
            last_offset = entries[-1].raw_offset
            last_line_no = entries[-1].raw_line_no
        self.store.upsert_file_state(
            path,
            parser_kind,
            stat.st_mtime_ns,
            stat.st_size,
            last_offset,
            last_line_no,
        )

    def _update_pipeline_state(self, path: Path, events: list[dict[str, object]]) -> None:
        try:
            stat = path.stat()
        except OSError:
            return
        last_line_no = events[-1]["raw_line_no"] if events else None
        self.store.upsert_file_state(
            path,
            "pipeline_event",
            stat.st_mtime_ns,
            stat.st_size,
            None,
            int(last_line_no) if last_line_no is not None else None,
        )

    def _parse_pipeline_event_file(self, path: Path, log_family: str) -> list[dict[str, object]]:
        events: list[dict[str, object]] = []
        with path.open(encoding="utf-8", errors="ignore") as handle:
            for line_no, raw_line in enumerate(handle, start=1):
                try:
                    obj = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                event_type = str(obj.get("event") or "")
                if not event_type:
                    continue
                job_id = str(obj.get("job_id") or "")
                if not job_id:
                    continue
                ts = _coerce_ts(obj.get("at"))
                slot = _first_non_empty(obj.get("target_slot"), obj.get("slot"))
                pane_target = _first_non_empty(obj.get("pane_target"))
                artifact_path = _first_non_empty(obj.get("artifact_path"), obj.get("path"))
                round_value = obj.get("round")
                event_key = f"{path}:{line_no}"
                events.append(
                    {
                        "event_key": event_key,
                        "ts": ts,
                        "job_id": job_id,
                        "round": int(round_value) if isinstance(round_value, (int, float)) else None,
                        "event_type": event_type,
                        "slot": slot,
                        "agent": _infer_agent(event_type, slot),
                        "pane_target": pane_target,
                        "artifact_path": artifact_path,
                        "raw_path": str(path),
                        "raw_line_no": line_no,
                        "log_family": log_family,
                        "payload_json": json.dumps(obj, ensure_ascii=False, sort_keys=True),
                    }
                )
        return events

    @staticmethod
    def rebuild_job_links(db_path: Path) -> int:
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            return relink_jobs(conn)
        finally:
            conn.close()


def _coerce_ts(raw: object) -> str:
    if isinstance(raw, (int, float)):
        return dt.datetime.fromtimestamp(float(raw), tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(raw, str):
        return raw
    return ""


def _infer_agent(event_type: str, slot: str | None) -> str | None:
    if slot == "slot_verify":
        return "codex"
    if "gemini" in event_type:
        return "gemini"
    if "claude" in event_type:
        return "claude"
    return None


def _first_non_empty(*values: object) -> str | None:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return None


def _progress_percent(scanned_files: int, total_files: int, phase: str) -> int:
    if total_files <= 0:
        return 100 if phase == "idle" else 0
    if phase == "idle":
        return 100
    return max(0, min(99, int((scanned_files / total_files) * 100)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect local CLI token usage into SQLite.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--poll-interval", type=float, default=3.0)
    parser.add_argument("--since-days", type=int)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--force-rescan", action="store_true")
    args = parser.parse_args(argv)

    if args.once and args.daemon:
        parser.error("--once and --daemon cannot be used together")

    collector = TokenCollector(
        project_root=Path(args.project_root),
        db_path=Path(args.db_path),
        poll_interval=args.poll_interval,
        since_days=args.since_days,
        force_rescan=args.force_rescan,
    )
    signal.signal(signal.SIGTERM, collector.stop)
    signal.signal(signal.SIGINT, collector.stop)

    if args.once:
        summary = collector.run_once_with_progress(
            progress_callback=(lambda payload: print(json.dumps(payload, ensure_ascii=False), flush=True))
            if args.progress
            else None
        )
        print(json.dumps(summary, ensure_ascii=False), flush=True)
        return 0

    collector.run_forever()
    return 0


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
