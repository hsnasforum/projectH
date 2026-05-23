from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from watcher_recovery import OperatorRetrageTracker, StaleAdvisoryRecovery
from watcher_state import WatcherTurnState


def _read_status(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("STATUS:"):
                return line.split(":", 1)[1].strip().lower()
    except OSError:
        return None
    return None


def _read_control_seq(path: Path) -> int:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("CONTROL_SEQ:"):
                return int(line.split(":", 1)[1].strip())
    except (OSError, ValueError):
        return -1
    return -1


class StaleAdvisoryRecoveryTest(unittest.TestCase):
    def _recovery(
        self,
        *,
        request_path: Path,
        events_path: Path,
        signal: SimpleNamespace,
        now: float = 100.0,
        active_seq: int = 18,
        recovery_sec: float = 5.0,
        cancel_result: bool = False,
    ) -> tuple[StaleAdvisoryRecovery, dict[str, object]]:
        calls: dict[str, object] = {
            "events": [],
            "logs": [],
            "notifications": [],
            "transitions": [],
            "last_request_sig": "",
        }

        recovery = StaleAdvisoryRecovery(
            advisory_request_path=request_path,
            run_events_path=events_path,
            current_turn_state=lambda: WatcherTurnState.ADVISORY_ACTIVE,
            turn_entered_at=lambda: 0.0,
            turn_active_control_seq=lambda: active_seq,
            advisory_retry_sec=lambda: 5.0,
            advisory_recovery_sec=lambda: recovery_sec,
            dry_run=lambda: True,
            advisory_enabled=lambda: True,
            get_pending_operator_mtime=lambda: 0.0,
            get_active_control=lambda: signal,
            control_signal_for_slot=lambda active, slot, status: active
            if slot == "advisory_request" and status == "request_open"
            else None,
            advisory_advice_is_current_for_request=lambda _seq: False,
            prompt_owner=lambda role: "Gemini" if role == "advisory" else "Codex",
            prompt_pane_target=lambda role: {"advisory": "gemini-pane", "verify": "codex-pane"}.get(role, ""),
            lane_prompt_readiness=lambda _target: (True, ""),
            pending_notifications=lambda: [],
            log_raw=lambda *args: calls["logs"].append(args),  # type: ignore[union-attr]
            emit_event=lambda event, payload: calls["events"].append((event, dict(payload))),  # type: ignore[union-attr]
            notify_advisory_owner=lambda reason: calls["notifications"].append(("advisory", reason)),  # type: ignore[union-attr]
            notify_verify_advisory_recovery=lambda reason, marker: calls["notifications"].append(
                ("verify", reason, dict(marker))
            ),  # type: ignore[union-attr]
            cancel_advisory_lane_if_busy=lambda **_kwargs: cancel_result,
            clear_implement_blocked=lambda reason: calls["logs"].append(("clear", reason)),  # type: ignore[union-attr]
            transition_turn=lambda *args, **kwargs: calls["transitions"].append((args, kwargs)),  # type: ignore[union-attr]
            read_control_seq_from_path=_read_control_seq,
            read_status_from_path=_read_status,
            get_path_sig=lambda path: f"sig:{path.read_text(encoding='utf-8')}",
            set_last_advisory_request_sig=lambda sig: calls.__setitem__("last_request_sig", sig),
            capture_pane_text=lambda _target: "",
            pane_text_has_busy_indicator=lambda _text, _lane: False,
            pane_text_busy_age_seconds=lambda _text, _lane: None,
            now_fn=lambda: now,
        )
        return recovery, calls

    def test_repeated_stale_advisory_marker_disallows_advisory_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "advisory_request.md"
            events_path = root / "events.jsonl"
            request_path.write_text(
                "\n".join(
                    [
                        "STATUS: request_open",
                        "CONTROL_SEQ: 19",
                        "SUPERSEDES: .pipeline/advisory_request.md CONTROL_SEQ 18 (superseded: stale_advisory_recovery)",
                    ]
                ),
                encoding="utf-8",
            )
            signal = SimpleNamespace(path=request_path, sig="request-sig", mtime=80.0, control_seq=19)
            recovery, _calls = self._recovery(
                request_path=request_path,
                events_path=events_path,
                signal=signal,
                active_seq=19,
            )

            marker = recovery.stale_recovery_marker()

            self.assertIsNotNone(marker)
            self.assertEqual(marker["advisory_recovery_attempt"], 2)
            self.assertFalse(marker["advisory_followup_allowed"])
            self.assertNotIn("advisory_request.md [request_open]", marker["advisory_recovery_next_controls"])

    def test_recover_stale_advisory_supersedes_request_and_notifies_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "advisory_request.md"
            events_path = root / "events.jsonl"
            request_path.write_text("STATUS: request_open\nCONTROL_SEQ: 18\n", encoding="utf-8")
            signal = SimpleNamespace(path=request_path, sig="request-sig", mtime=80.0, control_seq=18)
            recovery, calls = self._recovery(
                request_path=request_path,
                events_path=events_path,
                signal=signal,
                cancel_result=True,
            )

            self.assertTrue(recovery.recover_stale())

            request_text = request_path.read_text(encoding="utf-8")
            self.assertIn("STATUS: superseded", request_text)
            self.assertIn("SUPERSEDED_BY: advisory_recovery", request_text)
            events = [event for event, _payload in calls["events"]]
            self.assertIn("advisory_request_superseded", events)
            self.assertIn("advisory_recovery", events)
            self.assertEqual(calls["transitions"][0][0][0], WatcherTurnState.VERIFY_FOLLOWUP)
            self.assertTrue(any(item[0] == "verify" for item in calls["notifications"]))


class OperatorRetrageTrackerTest(unittest.TestCase):
    def test_idle_retriage_marker_uses_age_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            operator_path = Path(tmp) / "operator_request.md"
            operator_path.write_text("STATUS: needs_operator\nCONTROL_SEQ: 23\n", encoding="utf-8")
            tracker = OperatorRetrageTracker(
                operator_request_path=operator_path,
                current_turn_state=lambda: WatcherTurnState.OPERATOR_WAIT,
                turn_active_control_seq=lambda: 23,
                operator_wait_retriage_sec=lambda: 30.0,
                is_active_control=lambda path, status: path == operator_path and status == "needs_operator",
                get_path_mtime=lambda _path: 50.0,
                read_control_seq_from_path=_read_control_seq,
                get_active_control=lambda: None,
                control_signal_for_slot=lambda _active, _slot, _status: None,
                satisfied_operator_approval_marker=lambda: None,
                stale_operator_control_marker=lambda: None,
                get_path_sig=lambda _path: "operator-sig",
                read_status_from_path=_read_status,
                clear_implement_blocked=lambda _reason: None,
                transition_turn=lambda *_args, **_kwargs: None,
                record_operator_recovery_marker=lambda **_kwargs: "operator_request_stale_ignored",
                notify_verify_operator_retriage=lambda _reason, _marker: None,
                notify_verify_control_recovery=lambda _reason, _marker: None,
                set_last_operator_request_sig=lambda _sig: None,
                now_fn=lambda: 100.0,
            )

            marker = tracker.idle_retriage_marker()

            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "operator_wait_idle_retriage")
            self.assertEqual(marker["control_seq"], 23)
            self.assertEqual(marker["operator_wait_age_sec"], 50)

    def test_route_operator_recovery_suppresses_duplicate_notification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            operator_path = Path(tmp) / "operator_request.md"
            operator_path.write_text("STATUS: needs_operator\nCONTROL_SEQ: 44\n", encoding="utf-8")
            state = {"turn": WatcherTurnState.OPERATOR_WAIT, "seq": 44, "last_sig": ""}
            notifications: list[tuple[str, dict[str, object]]] = []
            records: list[dict[str, object]] = []

            def transition(turn: WatcherTurnState, _reason: str, **kwargs: object) -> None:
                state["turn"] = turn
                state["seq"] = int(kwargs.get("active_control_seq", -1))

            tracker = OperatorRetrageTracker(
                operator_request_path=operator_path,
                current_turn_state=lambda: state["turn"],
                turn_active_control_seq=lambda: int(state["seq"]),
                operator_wait_retriage_sec=lambda: 30.0,
                is_active_control=lambda _path, _status: True,
                get_path_mtime=lambda _path: 0.0,
                read_control_seq_from_path=_read_control_seq,
                get_active_control=lambda: None,
                control_signal_for_slot=lambda _active, _slot, _status: None,
                satisfied_operator_approval_marker=lambda: None,
                stale_operator_control_marker=lambda: None,
                get_path_sig=lambda _path: "operator-sig",
                read_status_from_path=_read_status,
                clear_implement_blocked=lambda _reason: None,
                transition_turn=transition,
                record_operator_recovery_marker=lambda **kwargs: records.append(kwargs) or "operator_request_stale_ignored",
                notify_verify_operator_retriage=lambda reason, marker: notifications.append((reason, dict(marker))),
                notify_verify_control_recovery=lambda reason, marker: notifications.append((reason, dict(marker))),
                set_last_operator_request_sig=lambda sig: state.__setitem__("last_sig", sig),
                now_fn=lambda: 100.0,
            )
            marker = {"reason": "pr_merge_completed", "control_seq": 44, "resolved_pr_numbers": [27]}

            self.assertTrue(
                tracker.route_recovery(
                    operator_sig="operator-sig",
                    operator_path=operator_path,
                    status="needs_operator",
                    marker=marker,
                    source="turn_signal",
                )
            )
            self.assertTrue(
                tracker.route_recovery(
                    operator_sig="operator-sig",
                    operator_path=operator_path,
                    status="needs_operator",
                    marker=marker,
                    source="turn_signal",
                )
            )

            self.assertEqual(state["turn"], WatcherTurnState.VERIFY_FOLLOWUP)
            self.assertEqual(state["last_sig"], "operator-sig")
            self.assertEqual(len(records), 1)
            self.assertEqual(len(notifications), 1)


if __name__ == "__main__":
    unittest.main()
