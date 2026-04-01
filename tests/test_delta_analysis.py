"""Tests for core.delta_analysis."""

from __future__ import annotations

import unittest

from core.delta_analysis import compute_correction_delta


class DeltaAnalysisTest(unittest.TestCase):

    def test_identical_returns_none(self) -> None:
        self.assertIsNone(compute_correction_delta("hello world", "hello world"))

    def test_simple_replacement(self) -> None:
        delta = compute_correction_delta("좋은 날씨입니다", "좋은 날씨였습니다")
        self.assertIsNotNone(delta)
        self.assertTrue(delta.delta_fingerprint.startswith("sha256:"))
        self.assertGreater(len(delta.segments), 0)
        self.assertGreater(delta.similarity_score, 0.5)

    def test_addition(self) -> None:
        delta = compute_correction_delta("기본 텍스트", "기본 텍스트입니다. 추가 내용.")
        self.assertIsNotNone(delta)
        self.assertGreater(len(delta.delta_summary["additions"]), 0)

    def test_removal(self) -> None:
        delta = compute_correction_delta("삭제할 부분이 있는 텍스트", "텍스트")
        self.assertIsNotNone(delta)
        self.assertGreater(len(delta.delta_summary["removals"]), 0)

    def test_mixed_changes(self) -> None:
        delta = compute_correction_delta(
            "원본 문장입니다. 이 부분은 삭제됩니다.",
            "수정된 문장입니다. 새로 추가된 내용.",
        )
        self.assertIsNotNone(delta)
        # Should have replacements (since the text changed at multiple positions)
        self.assertTrue(
            delta.delta_summary["replacements"]
            or delta.delta_summary["additions"]
            or delta.delta_summary["removals"]
        )

    def test_fingerprint_deterministic(self) -> None:
        d1 = compute_correction_delta("a", "b")
        d2 = compute_correction_delta("a", "b")
        self.assertEqual(d1.delta_fingerprint, d2.delta_fingerprint)

    def test_different_changes_different_fingerprints(self) -> None:
        d1 = compute_correction_delta("hello", "world")
        d2 = compute_correction_delta("hello", "hi there")
        self.assertNotEqual(d1.delta_fingerprint, d2.delta_fingerprint)

    def test_similarity_identical_is_one(self) -> None:
        # Can't test with identical (returns None), so test near-identical
        delta = compute_correction_delta("hello world!", "hello world.")
        self.assertIsNotNone(delta)
        self.assertGreater(delta.similarity_score, 0.8)

    def test_similarity_completely_different(self) -> None:
        delta = compute_correction_delta("aaa", "zzz")
        self.assertIsNotNone(delta)
        self.assertLess(delta.similarity_score, 0.5)

    def test_rewrite_dimensions_structure(self) -> None:
        delta = compute_correction_delta("original text here", "modified text here now")
        self.assertIsNotNone(delta)
        dims = delta.rewrite_dimensions
        self.assertIn("change_types", dims)
        self.assertIn("changed_segment_count", dims)
        self.assertIn("line_count_delta", dims)
        self.assertIn("character_count_delta", dims)
        self.assertIsInstance(dims["change_types"], list)
        self.assertGreater(dims["changed_segment_count"], 0)

    def test_fingerprint_matches_web_py_algorithm(self) -> None:
        """Critical compatibility test: same algorithm as web.py."""
        import difflib
        import hashlib
        import json

        original = "프로젝트H는 로컬 퍼스트 문서 비서입니다."
        corrected = "프로젝트H는 로컬 퍼스트 문서 비서 웹 MVP입니다."

        # Replicate web.py algorithm exactly
        matcher = difflib.SequenceMatcher(a=original, b=corrected, autojunk=False)
        segments = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            from_text = original[i1:i2]
            to_text = corrected[j1:j2]
            if not from_text and not to_text:
                continue
            segments.append({"from": from_text, "op": tag, "to": to_text})
        payload = json.dumps(segments, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        expected_fp = f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"

        # Compare with new implementation
        delta = compute_correction_delta(original, corrected)
        self.assertIsNotNone(delta)
        self.assertEqual(delta.delta_fingerprint, expected_fp)
