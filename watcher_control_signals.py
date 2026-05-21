from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pipeline_runtime.schema import (
    control_filenames_equivalent,
    control_seq_value,
    control_slot_spec_for_filename,
    read_pipeline_control_snapshot,
)
from watcher_state import ControlSignal


def _default_path_sig(path: Path) -> str:
    try:
        return str(path.stat().st_mtime_ns)
    except OSError:
        return ""


def newest_control_signal(signals: list[ControlSignal]) -> Optional[ControlSignal]:
    if not signals:
        return None
    return signals[0]


def control_signal_matches(
    signal: Optional[ControlSignal],
    path: Path,
    expected_status: str,
) -> bool:
    if signal is None or signal.status != expected_status:
        return False
    if signal.path == path:
        return True
    return control_filenames_equivalent(signal.path.name, path.name)


def control_signal_for_slot(
    signal: Optional[ControlSignal],
    slot_id: str,
    expected_status: str,
) -> Optional[ControlSignal]:
    if signal is None or signal.status != expected_status:
        return None
    if signal.slot_id == slot_id:
        return signal
    spec = control_slot_spec_for_filename(signal.path.name)
    if spec is not None and spec.slot_id == slot_id:
        return signal
    return None


@dataclass
class ControlSignalReader:
    pipeline_dir: Path
    advisory_enabled: bool
    operator_stop_enabled: bool
    path_sig_fn: Callable[[Path], str] = _default_path_sig

    def from_entry(self, entry: dict[str, object]) -> Optional[ControlSignal]:
        slot_id = str(entry.get("slot_id") or "").strip()
        if slot_id in {"advisory_request", "advisory_advice"} and not self.advisory_enabled:
            return None
        if slot_id == "operator_request" and not self.operator_stop_enabled:
            return None
        filename = str(entry.get("file") or "").strip()
        status = str(entry.get("status") or "").strip()
        if not filename or not status:
            return None
        path = self.pipeline_dir / filename
        try:
            mtime = float(entry.get("mtime") or 0.0)
        except (TypeError, ValueError):
            mtime = 0.0
        if mtime == 0.0:
            return None
        control_seq = control_seq_value(entry.get("control_seq"), default=-1)
        return ControlSignal(
            kind=slot_id or filename,
            path=path,
            status=status,
            mtime=mtime,
            sig=self.path_sig_fn(path),
            control_seq=control_seq,
            slot_id=slot_id,
            canonical_file=str(entry.get("canonical_file") or filename),
            is_legacy_alias=bool(entry.get("is_legacy_alias")),
        )

    def iter_valid(self, *, include_advisory_advice: bool = True) -> list[ControlSignal]:
        snapshot = read_pipeline_control_snapshot(self.pipeline_dir)
        entries: list[dict[str, object]] = []
        active_entry = snapshot.get("active_entry")
        if isinstance(active_entry, dict):
            entries.append(active_entry)
        entries.extend(
            entry
            for entry in list(snapshot.get("stale_entries") or [])
            if isinstance(entry, dict)
        )
        candidates: list[ControlSignal] = []
        for entry in entries:
            if not include_advisory_advice and str(entry.get("slot_id") or "") == "advisory_advice":
                continue
            signal = self.from_entry(entry)
            if signal is not None:
                candidates.append(signal)
        return candidates

    def newest(self, signals: list[ControlSignal]) -> Optional[ControlSignal]:
        return newest_control_signal(signals)

    def for_slot(self, slot_id: str, expected_status: str) -> Optional[ControlSignal]:
        signals = [
            signal
            for signal in self.iter_valid()
            if signal.slot_id == slot_id and signal.status == expected_status
        ]
        return newest_control_signal(signals)
