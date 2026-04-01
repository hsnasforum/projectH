"""Tests for the eval harness framework."""

from __future__ import annotations

import json
import unittest
from tempfile import TemporaryDirectory

from model_adapter.mock import MockModelAdapter
from eval.scenarios import EvalScenario, BUILTIN_SCENARIOS
from eval.metrics import measure_adherence, measure_ab_delta, measure_consistency
from eval.harness import EvalHarness
from eval.report import EvalReport


class MetricsTest(unittest.TestCase):

    def test_adherence_all_pass(self) -> None:
        result = measure_adherence(
            "이것은 좋은 응답입니다",
            {"should_contain": ["좋은"], "should_not_contain": ["나쁜"]},
        )
        self.assertTrue(result["pass"])
        self.assertEqual(result["score"], 1.0)

    def test_adherence_missing_phrase(self) -> None:
        result = measure_adherence(
            "이것은 응답입니다",
            {"should_contain": ["없는단어"]},
        )
        self.assertFalse(result["pass"])
        self.assertEqual(result["score"], 0.0)

    def test_adherence_unwanted_phrase_present(self) -> None:
        result = measure_adherence(
            "이것은 나쁜 응답입니다",
            {"should_not_contain": ["나쁜"]},
        )
        self.assertFalse(result["pass"])

    def test_adherence_pattern_match(self) -> None:
        result = measure_adherence(
            "로컬 퍼스트 문서 비서",
            {"expected_pattern": r"로컬|local"},
        )
        self.assertTrue(result["pass"])
        self.assertTrue(result["pattern_match"])

    def test_adherence_pattern_no_match(self) -> None:
        result = measure_adherence(
            "일반 문서 비서",
            {"expected_pattern": r"로컬|local"},
        )
        self.assertFalse(result["pass"])

    def test_adherence_empty_expected(self) -> None:
        result = measure_adherence("anything", {})
        self.assertTrue(result["pass"])
        self.assertEqual(result["score"], 1.0)

    def test_ab_delta_improvement(self) -> None:
        result = measure_ab_delta(
            response_with="선호 1건 반영된 좋은 응답",
            response_without="일반 응답",
            expected={"should_contain": ["선호"]},
        )
        self.assertTrue(result["preference_improved"])
        self.assertGreater(result["delta_score"], 0)

    def test_ab_delta_no_improvement(self) -> None:
        result = measure_ab_delta(
            response_with="일반 응답",
            response_without="일반 응답",
            expected={"should_contain": ["선호"]},
        )
        self.assertFalse(result["preference_improved"])

    def test_consistency_all_pass(self) -> None:
        result = measure_consistency(
            ["좋은 응답", "좋은 응답", "좋은 응답"],
            {"should_contain": ["좋은"]},
        )
        self.assertEqual(result["consistency_rate"], 1.0)

    def test_consistency_partial(self) -> None:
        result = measure_consistency(
            ["좋은 응답", "나쁜 응답", "좋은 응답"],
            {"should_contain": ["좋은"]},
        )
        self.assertAlmostEqual(result["consistency_rate"], 2 / 3, places=3)


class HarnessTest(unittest.TestCase):

    def test_run_mock_scenario(self) -> None:
        adapter = MockModelAdapter()
        harness = EvalHarness(adapter, provider_name="mock")
        scenario = BUILTIN_SCENARIOS[0]  # mock-preference-plumbing
        result = harness.run_scenario(scenario)
        self.assertTrue(result.adherence["pass"])
        self.assertIn("선호 1건 반영", result.response)

    def test_run_mock_baseline(self) -> None:
        adapter = MockModelAdapter()
        harness = EvalHarness(adapter, provider_name="mock")
        scenario = BUILTIN_SCENARIOS[1]  # mock-no-preference-baseline
        result = harness.run_scenario(scenario)
        self.assertTrue(result.adherence["pass"])

    def test_run_ab_scenario(self) -> None:
        adapter = MockModelAdapter()
        harness = EvalHarness(adapter, provider_name="mock")
        scenario = BUILTIN_SCENARIOS[0]
        ab = harness.run_ab_scenario(scenario)
        self.assertIn("선호 1건 반영", ab.response_with)
        self.assertNotIn("선호", ab.response_without)

    def test_run_all_mock(self) -> None:
        adapter = MockModelAdapter()
        harness = EvalHarness(adapter, provider_name="mock")
        report = harness.run_all(provider_filter="mock")
        self.assertGreater(len(report.scenario_results), 0)
        self.assertEqual(report.summary["failed"], 0)

    def test_run_context_scenario(self) -> None:
        adapter = MockModelAdapter()
        harness = EvalHarness(adapter, provider_name="mock")
        scenario = BUILTIN_SCENARIOS[3]  # mock-context-preference
        result = harness.run_scenario(scenario)
        self.assertTrue(result.adherence["pass"])


class ReportTest(unittest.TestCase):

    def test_to_json_roundtrip(self) -> None:
        report = EvalReport(adapter_provider="mock")
        json_str = report.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["adapter_provider"], "mock")
        self.assertIn("summary", parsed)

    def test_to_text_readable(self) -> None:
        report = EvalReport(adapter_provider="mock")
        text = report.to_text()
        self.assertIn("Eval Report", text)
        self.assertIn("mock", text)

    def test_save_creates_file(self) -> None:
        with TemporaryDirectory() as tmp:
            report = EvalReport(adapter_provider="mock")
            path = report.save(results_dir=tmp)
            self.assertTrue(path.endswith(".json"))
            content = json.loads(open(path, encoding="utf-8").read())
            self.assertEqual(content["adapter_provider"], "mock")

    def test_summary_counts(self) -> None:
        adapter = MockModelAdapter()
        harness = EvalHarness(adapter, provider_name="mock")
        report = harness.run_all(provider_filter="mock")
        s = report.summary
        self.assertEqual(s["total"], len(report.scenario_results))
        self.assertEqual(s["passed"] + s["failed"], s["total"])
