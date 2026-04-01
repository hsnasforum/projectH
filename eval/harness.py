"""Eval harness: orchestrates scenario runs against a ModelAdapter."""

from __future__ import annotations

import time
from typing import Any

from model_adapter.base import ModelAdapter
from eval.scenarios import EvalScenario, BUILTIN_SCENARIOS
from eval.metrics import measure_adherence, measure_ab_delta
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
        else:
            raise ValueError(f"Unknown eval_mode: {scenario.eval_mode}")

    def run_scenario(self, scenario: EvalScenario) -> ScenarioResult:
        start = time.monotonic()
        response = self._call_adapter(scenario, scenario.preferences)
        elapsed = time.monotonic() - start
        adherence = measure_adherence(response, scenario.expected)
        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            description=scenario.description,
            response=response,
            adherence=adherence,
            elapsed_seconds=round(elapsed, 4),
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
    ) -> EvalReport:
        if scenarios is None:
            scenarios = BUILTIN_SCENARIOS

        if provider_filter:
            scenarios = [s for s in scenarios if s.scenario_id.startswith(provider_filter)]

        report = EvalReport(adapter_provider=self.provider_name)

        for scenario in scenarios:
            result = self.run_scenario(scenario)
            report.scenario_results.append(result)

            if ab and scenario.preferences:
                ab_result = self.run_ab_scenario(scenario)
                report.ab_results.append(ab_result)

        return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run preference eval harness")
    parser.add_argument("--provider", default="mock", choices=["mock", "ollama"])
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--filter", default=None, help="Scenario ID prefix filter (e.g., 'mock' or 'ollama')")
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
    report = harness.run_all(
        provider_filter=args.filter or args.provider,
        ab=not args.no_ab,
    )

    print(report.to_text())
    print()
    if args.save:
        path = report.save()
        print(f"Results saved to: {path}")


if __name__ == "__main__":
    main()
