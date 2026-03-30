---
name: approval-flow-audit
description: Use when approval payloads, save behavior, reissue flows, pending approvals, overwrite handling, or approval UI contracts change.
---

# Approval Flow Audit Skill

Use this skill for repo changes touching save approval behavior.

## When To Use
- approval object changes
- `approved_approval_id` / `reissue_approval_id` logic changes
- approval card UI changes
- overwrite policy changes
- pending approval session storage changes

## Expected Input
- changed approval-related files
- current intended save/write behavior

## Expected Output
1. current approval contract summary
2. safety risks
3. approval invariants that must still hold
4. tests that must cover the change
5. docs that must be updated

## Required Invariants
- writes require explicit approval
- reissue does not silently write
- overwrite stays explicit and blocked by default unless scope changed
- pending approvals remain auditable in session storage

## Document Update Range
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- approval-related sections of `README.md`
