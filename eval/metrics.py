"""Eval metric functions."""

from __future__ import annotations

import re
from typing import Any


def measure_adherence(response: str, expected: dict[str, Any]) -> dict[str, Any]:
    """Check should_contain, should_not_contain, and expected_pattern.

    Returns a dict with pass/fail, detailed results, and a 0-1 score.
    """
    normalized = " ".join(response.split())
    checks = 0
    passed = 0

    contain_results = []
    for phrase in expected.get("should_contain", []):
        found = phrase in normalized
        contain_results.append({"phrase": phrase, "found": found})
        checks += 1
        if found:
            passed += 1

    not_contain_results = []
    for phrase in expected.get("should_not_contain", []):
        found = phrase in normalized
        not_contain_results.append({"phrase": phrase, "found": found})
        checks += 1
        if not found:
            passed += 1

    pattern = expected.get("expected_pattern")
    pattern_match = None
    if pattern:
        pattern_match = bool(re.search(pattern, normalized, re.IGNORECASE))
        checks += 1
        if pattern_match:
            passed += 1

    score = passed / checks if checks > 0 else 1.0

    return {
        "pass": score == 1.0,
        "should_contain_results": contain_results,
        "should_not_contain_results": not_contain_results,
        "pattern_match": pattern_match,
        "score": round(score, 4),
        "checks": checks,
        "passed": passed,
    }


def measure_ab_delta(
    response_with: str,
    response_without: str,
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Compare response WITH preferences vs WITHOUT."""
    with_adherence = measure_adherence(response_with, expected)
    without_adherence = measure_adherence(response_without, expected)

    return {
        "with_adherence": with_adherence,
        "without_adherence": without_adherence,
        "preference_improved": with_adherence["score"] > without_adherence["score"],
        "delta_score": round(with_adherence["score"] - without_adherence["score"], 4),
    }


def measure_consistency(
    responses: list[str],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Run adherence check on multiple responses and measure consistency."""
    results = [measure_adherence(r, expected) for r in responses]
    pass_count = sum(1 for r in results if r["pass"])

    return {
        "run_count": len(responses),
        "pass_count": pass_count,
        "consistency_rate": round(pass_count / len(responses), 4) if responses else 0.0,
    }
