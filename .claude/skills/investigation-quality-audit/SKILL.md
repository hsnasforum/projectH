---
name: investigation-quality-audit
description: Use when web investigation ranking, source-role weighting, claim coverage, retry/reload flow, or entity-card versus latest-update behavior changes.
---

# Investigation Quality Audit Skill

Use this skill for repo changes touching evidence-backed web investigation.

## When To Use
- request-intent or answer-mode changes
- source policy / source-role weighting changes
- claim extraction or slot coverage changes
- entity-card or latest-update rendering changes
- feedback retry / history reload changes
- noisy source filtering or web-page extraction changes

## Expected Input
- changed investigation-related files
- affected query type or answer mode
- expected trust / uncertainty behavior

## Expected Output
1. affected investigation modes
2. ranking or evidence risks
3. uncertainty / claim-coverage invariants
4. tests that must move with the change
5. docs that must move with the change

## Required Invariants
- web investigation remains secondary, read-only, permission-gated, and logged
- entity-card answers prefer multi-source agreement and trusted descriptive sources
- latest-update answers favor freshness and official/news sources over stale descriptive sources
- weak or missing slots remain visible as uncertainty instead of being silently promoted
- retry and reload flows preserve auditability, session context, and source visibility

## Document Update Range
- `README.md` when visible answer cards or history UI change
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md` or `docs/TASK_BACKLOG.md`

## Test Update Range
- `tests/test_request_intents.py`
- `tests/test_source_policy.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `tests/test_web_search_tool.py`
