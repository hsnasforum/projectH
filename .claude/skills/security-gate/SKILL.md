---
name: security-gate
description: Use before or after changes that touch approvals, file writes, networked web investigation, shell execution, permissions, logs, or stored session/search records.
---

# Security Gate Skill

Use this skill whenever a change touches risky behavior or its documentation.

## When To Use
- approval/save flow changes
- overwrite/delete/move behavior
- external web search or page fetch behavior
- session or search-history persistence changes
- log payload changes
- shell execution or runtime control changes

## Expected Input
- files changed
- affected action or flow
- whether the action is read-only or write-capable

## Expected Output
1. risk summary
2. approval requirement
3. path/audit boundary
4. logging requirement
5. rollback/reversibility note
6. required docs/tests to update

## Repo-Specific Checklist
- Is the action still local-first by default?
- Does write behavior remain approval-based?
- Is overwrite still blocked unless explicitly designed otherwise?
- Is web search still read-only, permission-gated, and logged?
- Does PDF/OCR behavior still fail explicitly rather than silently?
- Are session/search records stored locally and described honestly in docs?

## Document Update Range
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `AGENTS.md` if operator rules changed
