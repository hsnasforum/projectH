"""Unit tests for eval.fixture_loader."""
from __future__ import annotations

import unittest

from core.eval_contracts import EvalFixtureFamily, EVAL_FIXTURE_FAMILY_AXES
from eval.fixture_loader import load_fixture, _validate


class TestLoadFixture(unittest.TestCase):

    def test_all_seven_families_load(self):
        names = [
            "correction_reuse_001",
            "scope_suggestion_safety_001",
            "approval_friction_001",
            "reviewed_vs_unreviewed_trace_001",
            "rollback_stop_apply_001",
            "conflict_defer_trace_001",
            "explicit_vs_save_support_001",
        ]
        for name in names:
            with self.subTest(fixture=name):
                d = load_fixture(name)
                family = d["fixture_family"]
                self.assertIn(family, {f.value for f in EvalFixtureFamily})
                expected = EVAL_FIXTURE_FAMILY_AXES[EvalFixtureFamily(family)]
                self.assertEqual(frozenset(d["eval_axes"]), expected)

    def test_required_fields_present(self):
        d = load_fixture("correction_reuse_001")
        for field in ("artifact_id", "session_id", "fixture_family",
                      "eval_axes", "trace_version", "recorded_at"):
            with self.subTest(field=field):
                self.assertIn(field, d)


class TestValidate(unittest.TestCase):

    def _base(self) -> dict:
        return {
            "artifact_id": "test_001",
            "session_id": "sess_001",
            "fixture_family": "correction_reuse",
            "eval_axes": ["correction_reuse", "trace_completeness"],
            "trace_version": "1.0",
            "recorded_at": "2026-04-22T00:00:00Z",
        }

    def test_valid_passes(self):
        _validate(self._base())

    def test_missing_field_raises(self):
        data = self._base()
        del data["artifact_id"]
        with self.assertRaises(ValueError):
            _validate(data)

    def test_unknown_family_raises(self):
        data = self._base()
        data["fixture_family"] = "not_a_real_family"
        with self.assertRaises(ValueError):
            _validate(data)

    def test_unknown_axis_raises(self):
        data = self._base()
        data["eval_axes"] = ["correction_reuse", "not_a_real_axis"]
        with self.assertRaises(ValueError):
            _validate(data)

    def test_axes_mismatch_raises(self):
        data = self._base()
        data["eval_axes"] = ["approval_friction", "trace_completeness"]
        with self.assertRaises(ValueError):
            _validate(data)


if __name__ == "__main__":
    unittest.main()
