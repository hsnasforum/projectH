from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from watcher_control_signals import (
    ControlSignalReader,
    control_signal_for_slot,
    control_signal_matches,
    newest_control_signal,
)
from watcher_state import ControlSignal


class ControlSignalReaderTest(unittest.TestCase):
    def _write_control(self, path: Path, status: str, seq: int) -> None:
        path.write_text(f"STATUS: {status}\nCONTROL_SEQ: {seq}\n", encoding="utf-8")

    def test_iter_valid_filters_disabled_advisory_and_operator_slots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pipeline_dir = Path(tmp) / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            self._write_control(pipeline_dir / "implement_handoff.md", "implement", 11)
            self._write_control(pipeline_dir / "advisory_request.md", "request_open", 12)
            self._write_control(pipeline_dir / "operator_request.md", "needs_operator", 13)

            reader = ControlSignalReader(
                pipeline_dir=pipeline_dir,
                advisory_enabled=False,
                operator_stop_enabled=False,
                path_sig_fn=lambda path: f"sig:{path.name}",
            )

            signals = reader.iter_valid()

            self.assertEqual([signal.slot_id for signal in signals], ["implement_handoff"])
            self.assertEqual(signals[0].sig, "sig:implement_handoff.md")

    def test_iter_valid_can_exclude_advisory_advice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pipeline_dir = Path(tmp) / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            self._write_control(pipeline_dir / "implement_handoff.md", "implement", 11)
            self._write_control(pipeline_dir / "advisory_advice.md", "advice_ready", 12)

            reader = ControlSignalReader(
                pipeline_dir=pipeline_dir,
                advisory_enabled=True,
                operator_stop_enabled=True,
                path_sig_fn=lambda path: f"sig:{path.name}",
            )

            signals = reader.iter_valid(include_advisory_advice=False)

            self.assertEqual([signal.slot_id for signal in signals], ["implement_handoff"])

    def test_for_slot_and_pure_helpers_preserve_legacy_alias_matching(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pipeline_dir = Path(tmp) / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            canonical = pipeline_dir / "implement_handoff.md"
            legacy = pipeline_dir / "claude_handoff.md"
            self._write_control(legacy, "implement", 21)
            os.utime(legacy, None)
            reader = ControlSignalReader(
                pipeline_dir=pipeline_dir,
                advisory_enabled=True,
                operator_stop_enabled=True,
                path_sig_fn=lambda path: f"sig:{path.name}",
            )

            signal = reader.for_slot("implement_handoff", "implement")

            self.assertIsNotNone(signal)
            self.assertTrue(control_signal_matches(signal, canonical, "implement"))
            self.assertIs(control_signal_for_slot(signal, "implement_handoff", "implement"), signal)
            self.assertIs(newest_control_signal([signal]), signal)

    def test_default_path_signature_uses_mtime_ns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pipeline_dir = Path(tmp) / ".pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            path = pipeline_dir / "implement_handoff.md"
            self._write_control(path, "implement", 31)
            reader = ControlSignalReader(
                pipeline_dir=pipeline_dir,
                advisory_enabled=True,
                operator_stop_enabled=True,
            )

            signal = reader.for_slot("implement_handoff", "implement")

            self.assertIsNotNone(signal)
            self.assertEqual(signal.sig, str(path.stat().st_mtime_ns))


if __name__ == "__main__":
    unittest.main()
