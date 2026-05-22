from __future__ import annotations

import unittest

from watcher_lane_status import build_lane_statuses


class WatcherLaneStatusTest(unittest.TestCase):
    def test_active_lane_and_disabled_lane_statuses(self) -> None:
        heartbeat_iso = "2026-05-22T00:00:00Z"

        statuses = build_lane_statuses(
            heartbeat_iso=heartbeat_iso,
            active_lane="Codex",
            implement_lane="Claude",
            implement_live=False,
            lane_configs=[
                {"name": "Codex", "enabled": True},
                {"name": "Gemini", "enabled": False},
                {"name": "", "enabled": True},
            ],
        )

        self.assertEqual(
            statuses,
            [
                {
                    "name": "Codex",
                    "state": "WORKING",
                    "attachable": True,
                    "last_heartbeat_at": heartbeat_iso,
                },
                {
                    "name": "Gemini",
                    "state": "OFF",
                    "attachable": False,
                    "last_heartbeat_at": "",
                },
                {
                    "name": "Claude",
                    "state": "READY",
                    "attachable": True,
                    "last_heartbeat_at": heartbeat_iso,
                },
            ],
        )

    def test_implement_live_marks_implement_lane_working(self) -> None:
        heartbeat_iso = "2026-05-22T00:00:00Z"

        statuses = build_lane_statuses(
            heartbeat_iso=heartbeat_iso,
            active_lane="Codex",
            implement_lane="Claude",
            implement_live=True,
            lane_configs=[
                {"name": "Claude", "enabled": True},
                {"name": "Codex", "enabled": True},
            ],
        )

        by_name = {lane["name"]: lane for lane in statuses}
        self.assertEqual(by_name["Claude"]["state"], "WORKING")
        self.assertEqual(by_name["Codex"]["state"], "WORKING")
        self.assertEqual(by_name["Gemini"]["state"], "READY")

    def test_missing_config_adds_physical_fallback_lanes(self) -> None:
        heartbeat_iso = "2026-05-22T00:00:00Z"

        statuses = build_lane_statuses(
            heartbeat_iso=heartbeat_iso,
            active_lane="",
            implement_lane="",
            implement_live=False,
            lane_configs=[],
        )

        self.assertEqual([lane["name"] for lane in statuses], ["Claude", "Codex", "Gemini"])
        self.assertTrue(all(lane["state"] == "READY" for lane in statuses))
        self.assertTrue(all(lane["attachable"] is True for lane in statuses))
        self.assertTrue(all(lane["last_heartbeat_at"] == heartbeat_iso for lane in statuses))


if __name__ == "__main__":
    unittest.main()
