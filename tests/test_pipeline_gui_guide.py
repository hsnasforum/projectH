"""Regression tests for pipeline_gui.guide — stage-3 control semantics."""

import unittest

from pipeline_gui.guide import DEFAULT_GUIDE


class TestGuideNewestValidControl(unittest.TestCase):
    """Guide text must reflect newest-valid-control dispatch semantics."""

    def test_newest_valid_control_mentioned(self):
        self.assertIn("newest-valid-control", DEFAULT_GUIDE)

    def test_control_seq_mentioned(self):
        self.assertIn("CONTROL_SEQ", DEFAULT_GUIDE)

    def test_inactive_stale_wording(self):
        lower = DEFAULT_GUIDE.lower()
        self.assertTrue(
            "inactive" in lower or "stale" in lower or "비활성" in lower,
            "Guide must mention inactive/stale control files",
        )

    def test_implement_blocked_mentioned(self):
        self.assertIn("implement_blocked", DEFAULT_GUIDE)

    def test_implement_blocked_auto_routes_to_verify_owner(self):
        """implement_blocked should auto-route to verify/handoff owner triage, not operator."""
        idx_blocked = DEFAULT_GUIDE.find("implement_blocked")
        self.assertNotEqual(idx_blocked, -1)
        self.assertIn("verify/handoff owner triage", DEFAULT_GUIDE)

    def test_turbo_lite_wrapper_order_is_documented(self):
        self.assertIn("turbo-lite wrapper 순서", DEFAULT_GUIDE)
        self.assertIn("`onboard-lite`", DEFAULT_GUIDE)
        self.assertIn("`finalize-lite`", DEFAULT_GUIDE)
        self.assertIn("`round-handoff`", DEFAULT_GUIDE)
        self.assertIn("`next-slice-triage`", DEFAULT_GUIDE)


if __name__ == "__main__":
    unittest.main()
