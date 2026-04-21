---
name: onboard-lite
description: Use when entering an unfamiliar repo or work area and you need a narrow projectH-style onboarding pass that finds run/test entrypoints, ownership boundaries, and current risks without widening into full audit or implementation.
---

# Onboard Lite

Use this skill as a lightweight turbo-lite onboarding wrapper for a new repo, a new subsystem, or a newly inherited work area.

## When To Use
- when the repo or subsystem is unfamiliar
- when you need the minimum facts before planning or implementation
- when you need run commands, test commands, key ownership boundaries, and current risks gathered in one pass
- when a full audit would be too broad

## Expected Input
- repo root or target work area
- user goal or theme if known
- any obvious entrypoints already provided by the user

## Expected Output
1. current run/start entrypoints
2. current test/verification entrypoints
3. key files or docs to read first
4. ownership boundaries or workflow contracts that matter immediately
5. current risks or unknowns that block safe implementation

## Required Workflow
1. Read the top-level guidance first: `AGENTS.md`, and the nearest relevant root memory or local docs if they exist.
2. Find the actual run/start commands, test commands, and key repo entrypoints from the repo instead of guessing.
3. Identify the minimum ownership boundaries that matter for the requested area: runtime role contract, approval boundary, doc-sync boundary, or other local workflow guards.
4. Summarize only the facts needed to start work safely. Do not widen into whole-project diagnosis.
5. If important ambiguity remains after exploration, state exactly what is still unknown and why it matters.
6. Stop at orientation. Do not implement, do not rewrite docs, and do not turn onboarding into a release claim.

## Repo-Specific Guardrails
- This wrapper is for fast orientation, not broad audit.
- Prefer current shipped contract over roadmap or historical drafts when they conflict.
- Keep current shipped contract, next phase, and long-term north star clearly separated.
- Reuse existing repo docs and skills instead of inventing a new onboarding process.
- If the repo already has active `/work` and `/verify` history for the area, include the newest relevant notes in the reading order.

## Not In Scope
- implementation edits
- `/work` or `/verify` writing by default
- whole-project audit
- release / ready claims
- commit / push / PR

## Related Skills
- `next-slice-triage` for choosing one exact next slice after truth is current
- `finalize-lite` for implementation-side wrap-up
- `round-handoff` for verification-backed handoff
