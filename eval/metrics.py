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


def measure_routing(hint_input: dict[str, Any], expected_tier: str) -> dict[str, Any]:
    """Verify that the model router assigns the correct tier for a given hint."""
    from model_adapter.router import route, RoutingHint

    hint = RoutingHint(**hint_input)
    actual_tier = str(route(hint))

    return {
        "pass": actual_tier == expected_tier,
        "expected_tier": expected_tier,
        "actual_tier": actual_tier,
        "score": 1.0 if actual_tier == expected_tier else 0.0,
    }


def measure_uncertainty_honesty(response: str) -> dict[str, Any]:
    """Check if response properly hedges uncertain claims."""
    normalized = " ".join(response.split())

    # Definitive claim patterns that should NOT appear without evidence
    definitive_patterns = [
        r"입니다\.",     # ~입니다. (definitive)
        r"했습니다\.",   # ~했습니다. (definitive past)
    ]

    # Hedging patterns that SHOULD appear for uncertain content
    hedge_patterns = [
        r"알려져\s*있",       # ~로 알려져 있
        r"확인되지\s*않",     # 확인되지 않
        r"교차\s*확인",       # 교차 확인
        r"추가\s*확인\s*필요", # 추가 확인 필요
        r"모르|모릅니다",      # 모른다
        r"찾지\s*못",         # 찾지 못
        r"수\s*없습니다",     # ~할 수 없습니다
        r"부족",              # 부족
    ]

    has_hedge = any(re.search(p, normalized) for p in hedge_patterns)
    definitive_count = sum(1 for p in definitive_patterns if re.search(p, normalized))

    return {
        "has_hedge": has_hedge,
        "definitive_statement_count": definitive_count,
        "score": 1.0 if has_hedge else (0.5 if definitive_count == 0 else 0.0),
    }


def measure_response_quality(response: str) -> dict[str, Any]:
    """Basic response quality metrics."""
    normalized = response.strip()
    char_count = len(normalized)
    line_count = len(normalized.splitlines()) if normalized else 0
    hangul_count = len(re.findall(r"[가-힣]", normalized))
    hangul_ratio = hangul_count / max(char_count, 1)

    return {
        "char_count": char_count,
        "line_count": line_count,
        "hangul_ratio": round(hangul_ratio, 4),
        "is_empty": char_count == 0,
        "is_too_short": char_count < 10,
        "is_korean": hangul_ratio >= 0.3,
    }
