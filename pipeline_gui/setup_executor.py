"""Setup executor adapters for launcher setup mode."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable, Collection, Protocol

# Setup executor staged files are ephemeral scratch artifacts, not persistent truth.
# Keep current/in-flight setup ids protected, and delete old non-current staged files
# after a short retention window instead of archiving them.
DEFAULT_STAGED_RETENTION_SEC = 600.0

SetupPayload = dict[str, object]
WriteJsonFn = Callable[[Path, SetupPayload], None]
BuildPayloadFn = Callable[[], SetupPayload]
ShouldPromoteFn = Callable[[str], bool]
ProtectedSetupIdsFn = Callable[[], set[str]]
OnCompleteFn = Callable[[], None]


class SetupExecutorAdapter(Protocol):
    """Async materialization boundary for setup preview/apply flows."""

    name: str

    def dispatch_preview(
        self,
        *,
        destination: Path,
        build_payload: BuildPayloadFn,
        write_json: WriteJsonFn,
        should_promote: ShouldPromoteFn,
        protected_setup_ids: ProtectedSetupIdsFn | None = None,
        on_complete: OnCompleteFn | None = None,
    ) -> None:
        ...

    def dispatch_result(
        self,
        *,
        destination: Path,
        build_payload: BuildPayloadFn,
        write_json: WriteJsonFn,
        should_promote: ShouldPromoteFn,
        protected_setup_ids: ProtectedSetupIdsFn | None = None,
        on_complete: OnCompleteFn | None = None,
    ) -> None:
        ...

    def cleanup_staged_files(
        self,
        *,
        setup_dir: Path,
        protected_setup_ids: Collection[str],
    ) -> list[Path]:
        ...


def cleanup_staged_setup_files(
    setup_dir: Path,
    *,
    protected_setup_ids: Collection[str],
    retention_sec: float = DEFAULT_STAGED_RETENTION_SEC,
    now: float | None = None,
) -> list[Path]:
    removed: list[Path] = []
    if not setup_dir.exists():
        return removed
    protected = {str(item).strip() for item in protected_setup_ids if str(item).strip()}
    current = time.time() if now is None else now
    for path in setup_dir.glob("*.staged.json"):
        parts = path.name.split(".")
        if len(parts) < 4:
            continue
        setup_id = parts[-3]
        if not setup_id or setup_id in protected:
            continue
        try:
            age = current - path.stat().st_mtime
        except OSError:
            continue
        if age < retention_sec:
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError:
            continue
        removed.append(path)
    return removed


class LocalSetupExecutorAdapter:
    """Default launcher-local async adapter used until agent-driven setup lands."""

    name = "local"

    def __init__(
        self,
        *,
        preview_delay_sec: float = 0.15,
        result_delay_sec: float = 0.15,
        staged_retention_sec: float = DEFAULT_STAGED_RETENTION_SEC,
    ) -> None:
        self.preview_delay_sec = preview_delay_sec
        self.result_delay_sec = result_delay_sec
        self.staged_retention_sec = staged_retention_sec
        self._active_threads: set[threading.Thread] = set()
        self._active_threads_lock = threading.Lock()

    def _materialize_payload(self, *, phase: str, payload: SetupPayload) -> SetupPayload:
        del phase
        return dict(payload)

    def cleanup_staged_files(
        self,
        *,
        setup_dir: Path,
        protected_setup_ids: Collection[str],
    ) -> list[Path]:
        return cleanup_staged_setup_files(
            setup_dir,
            protected_setup_ids=protected_setup_ids,
            retention_sec=self.staged_retention_sec,
        )

    def _dispatch_async(
        self,
        *,
        phase: str,
        delay_sec: float,
        destination: Path,
        build_payload: BuildPayloadFn,
        write_json: WriteJsonFn,
        should_promote: ShouldPromoteFn,
        protected_setup_ids: ProtectedSetupIdsFn | None = None,
        on_complete: OnCompleteFn | None = None,
    ) -> None:
        def _worker() -> None:
            if delay_sec > 0:
                time.sleep(delay_sec)
            payload = self._materialize_payload(phase=phase, payload=build_payload())
            setup_id = str(payload.get("setup_id") or "")
            staged_destination = destination.with_name(
                f"{destination.stem}.{setup_id or 'unknown'}.staged{destination.suffix}"
            )
            write_json(staged_destination, payload)
            if setup_id and should_promote(setup_id):
                write_json(destination, payload)
            keep_ids = {setup_id} if setup_id else set()
            if protected_setup_ids is not None:
                keep_ids.update(protected_setup_ids())
            self.cleanup_staged_files(
                setup_dir=destination.parent,
                protected_setup_ids=keep_ids,
            )
            if on_complete is not None:
                on_complete()

        def _worker_with_tracking() -> None:
            try:
                _worker()
            finally:
                with self._active_threads_lock:
                    self._active_threads.discard(threading.current_thread())

        thread = threading.Thread(target=_worker_with_tracking, daemon=True)
        with self._active_threads_lock:
            self._active_threads.add(thread)
        thread.start()

    def wait_for_idle(self, *, timeout_sec: float = 1.0) -> bool:
        deadline = time.time() + max(0.0, timeout_sec)
        while True:
            with self._active_threads_lock:
                threads = [thread for thread in self._active_threads if thread.is_alive()]
                self._active_threads = set(threads)
            if not threads:
                return True
            remaining = deadline - time.time()
            if remaining <= 0:
                return False
            for thread in threads:
                thread.join(min(0.02, max(0.0, remaining)))

    def dispatch_preview(
        self,
        *,
        destination: Path,
        build_payload: BuildPayloadFn,
        write_json: WriteJsonFn,
        should_promote: ShouldPromoteFn,
        protected_setup_ids: ProtectedSetupIdsFn | None = None,
        on_complete: OnCompleteFn | None = None,
    ) -> None:
        self._dispatch_async(
            phase="preview",
            delay_sec=self.preview_delay_sec,
            destination=destination,
            build_payload=build_payload,
            write_json=write_json,
            should_promote=should_promote,
            protected_setup_ids=protected_setup_ids,
            on_complete=on_complete,
        )

    def dispatch_result(
        self,
        *,
        destination: Path,
        build_payload: BuildPayloadFn,
        write_json: WriteJsonFn,
        should_promote: ShouldPromoteFn,
        protected_setup_ids: ProtectedSetupIdsFn | None = None,
        on_complete: OnCompleteFn | None = None,
    ) -> None:
        self._dispatch_async(
            phase="result",
            delay_sec=self.result_delay_sec,
            destination=destination,
            build_payload=build_payload,
            write_json=write_json,
            should_promote=should_promote,
            protected_setup_ids=protected_setup_ids,
            on_complete=on_complete,
        )


class FaultInjectingSetupExecutorAdapter(LocalSetupExecutorAdapter):
    """Launcher-local adapter variant that can synthesize failed preview/result payloads."""

    name = "local_fault_injection"

    def __init__(
        self,
        *,
        preview_delay_sec: float = 0.15,
        result_delay_sec: float = 0.15,
        staged_retention_sec: float = DEFAULT_STAGED_RETENTION_SEC,
        preview_patch: SetupPayload | None = None,
        result_patch: SetupPayload | None = None,
    ) -> None:
        super().__init__(
            preview_delay_sec=preview_delay_sec,
            result_delay_sec=result_delay_sec,
            staged_retention_sec=staged_retention_sec,
        )
        self.preview_patch = dict(preview_patch or {})
        self.result_patch = dict(result_patch or {})

    def _materialize_payload(self, *, phase: str, payload: SetupPayload) -> SetupPayload:
        materialized = dict(payload)
        patch = self.preview_patch if phase == "preview" else self.result_patch
        if patch:
            materialized.update(patch)
            if phase == "result" and "status" not in patch:
                materialized["status"] = "apply_failed"
        return materialized
