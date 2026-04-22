"""Eval fixture loader for Milestone 8 service fixtures."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.eval_contracts import (
    EvalArtifactCoreTrace,
    EvalFixtureFamily,
    EVAL_FIXTURE_FAMILY_AXES,
    EVAL_QUALITY_AXES,
)

_FIXTURES_DIR = Path(__file__).parent.parent / "data" / "eval" / "fixtures"

_REQUIRED_FIELDS: frozenset[str] = frozenset({
    "artifact_id", "session_id", "fixture_family",
    "eval_axes", "trace_version", "recorded_at",
})


def load_fixture(name: str) -> EvalArtifactCoreTrace:
    """Load a named fixture JSON and return as EvalArtifactCoreTrace."""
    path = _FIXTURES_DIR / f"{name}.json"
    with path.open() as f:
        raw: dict[str, Any] = json.load(f)
    _validate(raw)
    return raw  # type: ignore[return-value]


def _validate(data: dict[str, Any]) -> None:
    missing = _REQUIRED_FIELDS - data.keys()
    if missing:
        raise ValueError(f"fixture missing fields: {missing}")
    try:
        family = EvalFixtureFamily(data["fixture_family"])
    except ValueError:
        raise ValueError(f"unknown fixture_family: {data['fixture_family']!r}")
    expected_axes = EVAL_FIXTURE_FAMILY_AXES[family]
    actual_axes = frozenset(data["eval_axes"])
    unknown = actual_axes - EVAL_QUALITY_AXES
    if unknown:
        raise ValueError(f"unknown eval_axes: {unknown}")
    if actual_axes != expected_axes:
        raise ValueError(
            f"eval_axes mismatch for {family}: expected {expected_axes}, got {actual_axes}"
        )
