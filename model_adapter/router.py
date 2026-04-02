"""Model router: decides which model tier to use per task.

Tier mapping (qwen2.5 family):
  light  → 3b  : classification, short rewrite, formatting, titles, approval text
  medium → 7b  : document Q&A, grounded brief, memo, action_items, single-doc follow-up
  heavy  → 14b : web investigation synthesis, conflicting sources, freshness-sensitive,
                  correction-heavy answers, final save candidate
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ModelTier(StrEnum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


@dataclass(frozen=True, slots=True)
class RoutingHint:
    """Signals collected from agent_loop to inform model selection."""
    task: str = "respond"            # respond, summarize, answer_context, rewrite, format
    answer_mode: str = "general"     # general, entity_card, latest_update
    intent: str = "general"          # general, key_points, action_items, memo
    source_count: int = 0            # number of sources / evidence items
    has_web_sources: bool = False     # involves web investigation
    has_conflicting_sources: bool = False
    freshness_sensitive: bool = False
    correction_count: int = 0        # active corrections being applied
    is_save_candidate: bool = False   # answer may be saved as note
    claim_coverage_weak: bool = False # claim coverage has weak/missing slots


# ── Preference budget per tier ────────────────────────────────────

PREFERENCE_BUDGET = {
    ModelTier.LIGHT: 2,
    ModelTier.MEDIUM: 5,
    ModelTier.HEAVY: 10,
}


def route(hint: RoutingHint) -> ModelTier:
    """Determine the model tier for a given task context."""

    # ── Always LIGHT (3B) ─────────────────────────────────────────
    if hint.task in ("rewrite", "format"):
        return ModelTier.LIGHT

    # ── Always HEAVY (14B) ────────────────────────────────────────
    if hint.has_conflicting_sources:
        return ModelTier.HEAVY
    if hint.freshness_sensitive:
        return ModelTier.HEAVY
    if hint.answer_mode in ("entity_card", "latest_update"):
        return ModelTier.HEAVY
    if hint.has_web_sources and hint.source_count >= 3:
        return ModelTier.HEAVY
    if hint.is_save_candidate:
        return ModelTier.HEAVY
    if hint.claim_coverage_weak and hint.has_web_sources:
        return ModelTier.HEAVY
    if hint.correction_count >= 3:
        return ModelTier.HEAVY

    # ── MEDIUM (7B) for standard document work ────────────────────
    if hint.task in ("summarize", "answer_context"):
        return ModelTier.MEDIUM
    if hint.intent in ("key_points", "action_items", "memo"):
        return ModelTier.MEDIUM
    if hint.source_count >= 1:
        return ModelTier.MEDIUM

    # ── Default: MEDIUM for general chat ──────────────────────────
    if hint.task == "respond":
        return ModelTier.MEDIUM

    return ModelTier.MEDIUM


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """Maps tiers to concrete model names."""
    light: str = "qwen2.5:3b"
    medium: str = "qwen2.5:7b"
    heavy: str = "qwen2.5:14b"

    def resolve(self, tier: ModelTier) -> str:
        if tier == ModelTier.LIGHT:
            return self.light
        if tier == ModelTier.HEAVY:
            return self.heavy
        return self.medium

    def preference_budget(self, tier: ModelTier) -> int:
        return PREFERENCE_BUDGET.get(tier, 5)
