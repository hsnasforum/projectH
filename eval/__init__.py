"""Workflow-level eval harness for preference adherence testing."""

from core.eval_contracts import (
    ApprovalFrictionTrace,
    ConflictDeferTrace,
    CorrectionReuseTrace,
    EVAL_FAMILY_TRACE_CLASS,
    ExplicitVsSaveSupportTrace,
    ReviewabilityTrace,
    RollbackabilityTrace,
    ScopeSafetyTrace,
)
from eval.harness import EvalHarness
from eval.scenarios import EvalScenario, BUILTIN_SCENARIOS
from eval.report import EvalReport
from eval.fixture_loader import load_fixture

__all__ = [
    "ApprovalFrictionTrace",
    "BUILTIN_SCENARIOS",
    "ConflictDeferTrace",
    "CorrectionReuseTrace",
    "EVAL_FAMILY_TRACE_CLASS",
    "EvalHarness",
    "EvalReport",
    "EvalScenario",
    "ExplicitVsSaveSupportTrace",
    "ReviewabilityTrace",
    "RollbackabilityTrace",
    "ScopeSafetyTrace",
    "load_fixture",
]
