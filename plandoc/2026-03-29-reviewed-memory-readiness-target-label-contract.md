# 2026-03-29 Reviewed-Memory Readiness-Target Label Contract

## Goal

Fix the first exact contract for the shipped planning-only readiness-target label after the synchronized docs-and-payload rename-only pass.

This document does not describe implemented reviewed-memory store, reviewed-memory apply, emitted transition records, repeated-signal promotion, cross-session counting, or user-level memory.

## Current Shipped Truth

- current same-session `recurrence_aggregate_candidates` remain read-only and promotion-ineligible
- each current aggregate item may expose:
  - `aggregate_promotion_marker`
  - `reviewed_memory_precondition_status`
  - `reviewed_memory_boundary_draft`
  - `reviewed_memory_rollback_contract`
  - `reviewed_memory_disable_contract`
  - `reviewed_memory_conflict_contract`
  - `reviewed_memory_transition_audit_contract`
  - `reviewed_memory_unblock_contract`
  - `reviewed_memory_capability_status`
- current shipped target fields now use the same narrowed label:
  - `reviewed_memory_precondition_status.future_transition_target = eligible_for_reviewed_memory_draft_planning_only`
  - `reviewed_memory_unblock_contract.readiness_target = eligible_for_reviewed_memory_draft_planning_only`
  - `reviewed_memory_capability_status.readiness_target = eligible_for_reviewed_memory_draft_planning_only`
- current shipped meaning is already narrow:
  - one exact same-session aggregate may enter reviewed-memory draft planning only
  - that label does not mean reviewed-memory apply, emitted transition record, repeated-signal promotion, cross-session counting, or user-level memory

## Decision

### 1. Keep The Narrowed Shipped Label

The synchronized rename-only pass is now the shipped truth.

Why this is the current MVP-safe choice:

- it makes the planning-only boundary explicit in both payloads and docs
- it keeps blocked threshold, capability outcome, emitted transition, and apply/result layers separate
- it stays smaller than emitted transition records, reviewed-memory apply, repeated-signal promotion, and cross-session counting

### 2. Current Shipped Truth Vs Future Normalization

Current shipped truth is:

- `eligible_for_reviewed_memory_draft_planning_only`

If a later clarification pass reopens, it should discuss normalization only, not a second target rename.

### 3. Exact Meaning Of The Label

The current shipped label points to one semantic target:

- one exact same-session aggregate above the current blocked layer
- reviewed-memory draft planning only

They do not mean:

- reviewed-memory apply
- emitted transition record
- repeated-signal promotion
- cross-session counting
- user-level memory

### 4. Surface Coupling Rule

The three target fields stay coupled:

- `reviewed_memory_precondition_status.future_transition_target`
- `reviewed_memory_unblock_contract.readiness_target`
- `reviewed_memory_capability_status.readiness_target`

Current rule:

- keep the current shipped label identical across all three fields

Future normalization rule:

- do not rename only one or two fields
- do not let a ref-collapse or normalization patch hide semantic widening
- if one shared planning-target ref ever replaces the three fields, it must preserve the same planning-only meaning

### 5. Relationship To Contract Exists / Satisfaction / Transition / Apply

Keep the layers separate:

- target label != `blocked_all_required`
- target label != `unblocked_all_required`
- satisfaction outcome != emitted transition record
- emitted transition record != reviewed-memory apply result

Why this remains the honest order:

- the target label only names where draft planning could later point
- satisfaction outcome only says the capability family is actually satisfied
- emitted transition record only says one later reviewed-memory transition was recorded
- apply result only says one later reviewed-memory effect was actually applied

### 6. Boundary Recap

- `session_local_candidate`
  - source-message current draft
- `durable_candidate`
  - same-source explicit-confirmation projection
- `candidate_review_record`
  - source-message reviewed-but-not-applied trace
- `candidate_recurrence_key`
  - source-message recurrence primitive
- `recurrence_aggregate_candidates`
  - same-session grouping surface
- `aggregate_promotion_marker`
  - blocked marker only
- `reviewed_memory_precondition_status`
  - blocked-only status plus current shipped target label
- boundary / rollback / disable / conflict / transition-audit contracts
  - current contract-exists-only chain
- `reviewed_memory_unblock_contract`
  - blocked-threshold contract only
- `reviewed_memory_capability_status`
  - satisfied-capability outcome surface with current emitted `blocked_all_required` only
- current narrowed planning-target label
  - shipped planning-only clarification layer
- future emitted transition record
  - later than label clarification and later than satisfaction
- future reviewed-memory apply
  - later than emitted transition record

### 7. Support And Mirror Boundary

Never treat these as target-label or capability-satisfaction basis:

- `candidate_review_record`
- queue presence
- approval-backed save alone
- historical adjunct alone
- `task_log` replay alone
- fixed statement alone

Therefore:

- approval-backed save remains supporting evidence only
- historical adjunct remains supporting context only
- review acceptance remains confidence support only
- `task_log` remains mirror / appendix only

### 8. Cross-Session Boundary

Even after the future label narrows, cross-session counting still stays closed.

It still needs:

- explicit local store across sessions
- stale-resolution rules
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session remains the honest boundary.

## Recommended Next Implementation Slice

- one smaller shared-planning-target normalization pass only

That pass should:

- preserve the shipped `eligible_for_reviewed_memory_draft_planning_only` meaning
- keep all three current target fields semantically aligned
- avoid changing blocked/satisfied semantics, emitted transition behavior, or apply/store state

Why this remains the smallest honest next step:

- the rename-only clarification is already shipped
- any next change should be smaller than readiness widening, emitted transition records, or apply

## Open Questions

1. Should the three target fields keep duplicating the same planning-only label, or later normalize to one shared planning-target ref?
