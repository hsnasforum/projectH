"""Eval harness: orchestrates scenario runs against a ModelAdapter.

Usage:
  python -m eval --provider mock              # mock plumbing tests
  python -m eval --provider mock --gate       # release gate (mock + routing)
  python -m eval --provider ollama --gate     # release gate (all categories)
  python -m eval --category uncertainty       # specific category
"""

from __future__ import annotations

import time
from typing import Any

from model_adapter.base import ModelAdapter
from eval.scenarios import EvalScenario, BUILTIN_SCENARIOS
from eval.metrics import (
    measure_adherence,
    measure_ab_delta,
    measure_routing,
    measure_uncertainty_honesty,
    measure_response_quality,
)
from eval.report import EvalReport, ScenarioResult, ABResult


class EvalHarness:
    def __init__(self, adapter: ModelAdapter, *, provider_name: str = "mock") -> None:
        self.adapter = adapter
        self.provider_name = provider_name

    def _call_adapter(self, scenario: EvalScenario, preferences: list[dict[str, str]] | None) -> str:
        prefs = preferences if preferences else None
        if scenario.eval_mode == "respond":
            return self.adapter.respond(
                scenario.input["user_text"],
                active_preferences=prefs,
            )
        elif scenario.eval_mode == "answer_with_context":
            return self.adapter.answer_with_context(
                intent=scenario.input.get("intent", "general"),
                user_request=scenario.input.get("user_request", ""),
                context_label=scenario.input.get("context_label", ""),
                source_paths=scenario.input.get("source_paths", []),
                context_excerpt=scenario.input.get("context_excerpt", ""),
                summary_hint=scenario.input.get("summary_hint"),
                evidence_items=scenario.input.get("evidence_items"),
                active_preferences=prefs,
            )
        elif scenario.eval_mode == "routing":
            # Routing scenarios don't call the adapter
            return ""
        else:
            raise ValueError(f"Unknown eval_mode: {scenario.eval_mode}")

    def run_scenario(self, scenario: EvalScenario) -> ScenarioResult:
        start = time.monotonic()

        # Routing verification — no adapter call needed
        if scenario.eval_mode == "routing":
            routing_result = measure_routing(scenario.input, scenario.expected_tier)
            elapsed = time.monotonic() - start
            return ScenarioResult(
                scenario_id=scenario.scenario_id,
                description=scenario.description,
                response=f"routed to: {routing_result['actual_tier']}",
                adherence=routing_result,
                elapsed_seconds=round(elapsed, 4),
                category=scenario.category,
                quality=None,
                uncertainty=None,
            )

        response = self._call_adapter(scenario, scenario.preferences)
        elapsed = time.monotonic() - start

        adherence = measure_adherence(response, scenario.expected)
        quality = measure_response_quality(response)

        uncertainty = None
        if scenario.category == "uncertainty":
            uncertainty = measure_uncertainty_honesty(response)
            # Merge uncertainty into adherence pass
            if not uncertainty.get("has_hedge") and uncertainty.get("score", 1.0) < 0.5:
                adherence["pass"] = False
                adherence["score"] = min(adherence["score"], uncertainty["score"])

        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            description=scenario.description,
            response=response,
            adherence=adherence,
            elapsed_seconds=round(elapsed, 4),
            category=scenario.category,
            quality=quality,
            uncertainty=uncertainty,
        )

    def run_ab_scenario(self, scenario: EvalScenario) -> ABResult:
        start = time.monotonic()
        response_with = self._call_adapter(scenario, scenario.preferences)
        response_without = self._call_adapter(scenario, [])
        elapsed = time.monotonic() - start
        ab_delta = measure_ab_delta(response_with, response_without, scenario.expected)
        return ABResult(
            scenario_id=scenario.scenario_id,
            description=scenario.description,
            response_with=response_with,
            response_without=response_without,
            ab_delta=ab_delta,
            elapsed_seconds=round(elapsed, 4),
        )

    def run_all(
        self,
        scenarios: list[EvalScenario] | None = None,
        *,
        ab: bool = True,
        provider_filter: str | None = None,
        category_filter: str | None = None,
        tag_filter: str | None = None,
        release_gate: bool = False,
    ) -> EvalReport:
        if scenarios is None:
            scenarios = BUILTIN_SCENARIOS

        # Apply filters
        if release_gate:
            scenarios = [s for s in scenarios if "release-gate" in s.tags or s.eval_mode == "routing"]
        if provider_filter:
            scenarios = [s for s in scenarios if s.scenario_id.startswith(provider_filter) or provider_filter in s.tags]
        if category_filter:
            scenarios = [s for s in scenarios if s.category == category_filter]
        if tag_filter:
            scenarios = [s for s in scenarios if tag_filter in s.tags]

        report = EvalReport(adapter_provider=self.provider_name)

        for scenario in scenarios:
            result = self.run_scenario(scenario)
            report.scenario_results.append(result)

            if ab and scenario.preferences and scenario.eval_mode != "routing":
                ab_result = self.run_ab_scenario(scenario)
                report.ab_results.append(ab_result)

        return report

    def run_release_gate(self) -> tuple[bool, EvalReport]:
        """Run all release-gate scenarios. Returns (passed, report)."""
        # Mock scenarios (always fast)
        mock_scenarios = [s for s in BUILTIN_SCENARIOS if "mock" in s.tags]
        # Release-gate scenarios appropriate for this provider
        gate_scenarios = [s for s in BUILTIN_SCENARIOS if "release-gate" in s.tags]
        if self.provider_name == "mock":
            gate_scenarios = [s for s in gate_scenarios if "ollama" not in s.tags]

        all_scenarios = mock_scenarios + gate_scenarios
        # Deduplicate by scenario_id
        seen = set()
        unique = []
        for s in all_scenarios:
            if s.scenario_id not in seen:
                seen.add(s.scenario_id)
                unique.append(s)

        report = self.run_all(scenarios=unique, ab=False, release_gate=False)
        gate_passed = all(r.adherence.get("pass", False) for r in report.scenario_results)
        return gate_passed, report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run eval harness")
    parser.add_argument("--provider", default="mock", choices=["mock", "ollama"])
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--filter", default=None, help="Scenario ID prefix filter")
    parser.add_argument("--category", default=None, help="Category filter")
    parser.add_argument("--tag", default=None, help="Tag filter")
    parser.add_argument("--gate", action="store_true", help="Run release gate check")
    parser.add_argument("--save", action="store_true", help="Save results to eval/results/")
    parser.add_argument("--no-ab", action="store_true", help="Skip A/B comparisons")
    args = parser.parse_args()

    if args.provider == "ollama":
        from model_adapter.ollama import OllamaModelAdapter
        adapter = OllamaModelAdapter(base_url=args.base_url, model=args.model)
    else:
        from model_adapter.mock import MockModelAdapter
        adapter = MockModelAdapter()

    harness = EvalHarness(adapter, provider_name=args.provider)

    if args.gate:
        passed, report = harness.run_release_gate()
        print(report.to_text())
        print()
        gate_status = "PASSED" if passed else "FAILED"
        print(f"Release gate: {gate_status}")
        if args.save:
            path = report.save()
            print(f"Results saved to: {path}")
        raise SystemExit(0 if passed else 1)

    report = harness.run_all(
        provider_filter=args.filter or args.provider,
        category_filter=args.category,
        tag_filter=args.tag,
        ab=not args.no_ab,
    )

    print(report.to_text())
    print()
    if args.save:
        path = report.save()
        print(f"Results saved to: {path}")


if __name__ == "__main__":
    main()
