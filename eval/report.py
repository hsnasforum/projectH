"""Eval report formatting and persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass
class ScenarioResult:
    scenario_id: str
    description: str
    response: str
    adherence: dict[str, Any]
    elapsed_seconds: float
    category: str = "general"
    quality: dict[str, Any] | None = None
    uncertainty: dict[str, Any] | None = None


@dataclass
class ABResult:
    scenario_id: str
    description: str
    response_with: str
    response_without: str
    ab_delta: dict[str, Any]
    elapsed_seconds: float


@dataclass
class EvalReport:
    run_id: str = field(default_factory=lambda: uuid4().hex[:12])
    run_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    adapter_provider: str = "mock"
    scenario_results: list[ScenarioResult] = field(default_factory=list)
    ab_results: list[ABResult] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, Any]:
        total = len(self.scenario_results)
        passed = sum(1 for r in self.scenario_results if r.adherence.get("pass"))
        # Category breakdown
        categories: dict[str, dict[str, int]] = {}
        for r in self.scenario_results:
            cat = r.category
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if r.adherence.get("pass"):
                categories[cat]["passed"] += 1
        # Average quality metrics
        quality_results = [r.quality for r in self.scenario_results if r.quality]
        avg_hangul_ratio = (
            round(sum(q["hangul_ratio"] for q in quality_results) / len(quality_results), 4)
            if quality_results else None
        )
        empty_count = sum(1 for q in quality_results if q.get("is_empty"))
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 4) if total > 0 else 0.0,
            "ab_comparisons": len(self.ab_results),
            "ab_improved": sum(1 for r in self.ab_results if r.ab_delta.get("preference_improved")),
            "categories": categories,
            "avg_hangul_ratio": avg_hangul_ratio,
            "empty_responses": empty_count,
        }

    def to_json(self) -> str:
        data = {
            "run_id": self.run_id,
            "run_at": self.run_at,
            "adapter_provider": self.adapter_provider,
            "summary": self.summary,
            "scenarios": [asdict(r) for r in self.scenario_results],
            "ab_comparisons": [asdict(r) for r in self.ab_results],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def to_text(self) -> str:
        lines = [
            f"=== Eval Report {self.run_id} ===",
            f"Provider: {self.adapter_provider}",
            f"Run at:   {self.run_at}",
            "",
        ]
        s = self.summary
        lines.append(f"Results: {s['passed']}/{s['total']} passed ({s['pass_rate']:.0%})")
        if s["ab_comparisons"]:
            lines.append(f"A/B:     {s['ab_improved']}/{s['ab_comparisons']} improved with preferences")
        if s.get("avg_hangul_ratio") is not None:
            lines.append(f"Korean:  {s['avg_hangul_ratio']:.0%} average hangul ratio")
        if s.get("empty_responses"):
            lines.append(f"Empty:   {s['empty_responses']} empty responses")
        lines.append("")

        # Category breakdown
        categories = s.get("categories", {})
        if categories:
            lines.append("Categories:")
            for cat, counts in sorted(categories.items()):
                status = "OK" if counts["passed"] == counts["total"] else "FAIL"
                lines.append(f"  [{status}] {cat}: {counts['passed']}/{counts['total']}")
            lines.append("")

        # Individual results
        for r in self.scenario_results:
            status = "PASS" if r.adherence.get("pass") else "FAIL"
            lines.append(f"  [{status}] {r.scenario_id} ({r.elapsed_seconds:.2f}s)")
            if not r.adherence.get("pass"):
                for c in r.adherence.get("should_contain_results", []):
                    if not c["found"]:
                        lines.append(f"         missing: '{c['phrase']}'")
                for c in r.adherence.get("should_not_contain_results", []):
                    if c["found"]:
                        lines.append(f"         unexpected: '{c['phrase']}'")
                if r.adherence.get("expected_tier") and r.adherence.get("actual_tier"):
                    lines.append(f"         expected tier: {r.adherence['expected_tier']}, actual: {r.adherence['actual_tier']}")

        return "\n".join(lines)

    def save(self, results_dir: str = "eval/results") -> str:
        path = Path(results_dir)
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / f"{self.run_id}.json"
        file_path.write_text(self.to_json(), encoding="utf-8")
        return str(file_path)
