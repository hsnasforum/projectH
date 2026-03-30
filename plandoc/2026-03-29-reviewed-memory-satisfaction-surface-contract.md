# 2026-03-29 Reviewed-Memory Satisfaction Surface Contract

## Goal

Fix the first exact future satisfaction surface above the shipped same-session blocked threshold contract.

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
- current `reviewed_memory_unblock_contract` stays:
  - `unblock_version = same_session_reviewed_memory_unblock_v1`
  - `readiness_target = eligible_for_reviewed_memory_draft_planning_only`
  - exact `required_preconditions`
  - `unblock_status = blocked_all_required`
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - `partial_state_policy = partial_states_not_materialized`
  - `evaluated_at = aggregate.last_seen_at`

Current shipped contract objects are still `contract exists` only. Current object existence alone is never `satisfied`.

## Decision

### 1. A Separate Satisfaction Surface Should Exist

Choose `Option B`.

Keep one separate read-only satisfaction surface rather than reinterpreting the shipped `reviewed_memory_unblock_contract`.

Why this is the current MVP-safe choice:

- it preserves three distinct meanings:
  - `contract exists`
  - `blocked threshold`
  - `future satisfied capability outcome`
- it keeps the shipped `reviewed_memory_unblock_contract` truthful as a blocked-threshold contract only
- it avoids hiding meaning drift behind a reused field name
- it stays smaller than emitted transition records, reviewed-memory apply, repeated-signal promotion, and cross-session counting

### 2. Exact Meaning Of Future `unblocked_all_required`

Future `unblocked_all_required` means:

- one exact same-session aggregate now has the full required capability family actually satisfied
- reviewed-memory draft planning may truthfully open above that same exact aggregate identity plus its exact supporting refs
- the capability outcome remains local-first and same-session-scoped

It does not mean:

- reviewed-memory apply already happened
- emitted transition record already exists
- repeated-signal promotion already happened
- cross-session counting opened
- user-level memory opened

### 3. Relationship To The Shipped `reviewed_memory_unblock_contract`

Keep the current shipped `reviewed_memory_unblock_contract` as:

- blocked-threshold contract only
- current `blocked_all_required` surface only
- one read-only contract that describes what must be satisfied before draft planning can open

Current shipped rule:

- do not overwrite the shipped `reviewed_memory_unblock_contract`
- keep one separate read-only satisfaction surface for actual capability outcome
- keep the three-stage boundary explicit:
  - current contract objects = `contract exists`
  - shipped unblock contract = blocked threshold
  - shipped capability-status surface = current actual capability outcome

Keep the current label for now:

- `readiness_target = eligible_for_reviewed_memory_draft_planning_only`

Interpret it narrowly:

- reviewed-memory draft planning only

Whether the three target fields should later normalize to one shared planning-target ref remains an open question.

### 4. Satisfaction Basis Boundary

Future satisfaction basis must require later canonical reviewed-memory-layer capabilities for the same exact aggregate scope:

- later canonical reviewed-memory boundary capability
- later rollback capability
- later disable capability
- later conflict-visibility capability
- later transition-audit capability

Never count these as satisfaction basis:

- contract object existence alone
- `candidate_review_record`
- queue presence
- approval-backed save alone
- historical adjunct alone
- `task_log` replay alone
- fixed statement alone

Therefore:

- approval-backed save remains supporting evidence only
- historical adjunct remains supporting context only
- review acceptance remains support only and never replaces aggregate-level capability satisfaction
- `task_log` remains mirror / appendix only and never becomes canonical satisfaction source

### 5. Minimum Future Satisfaction Shape

The smallest honest shipped surface is:

- one read-only `reviewed_memory_capability_status`
  - `capability_version = same_session_reviewed_memory_capabilities_v1`
  - `readiness_target = eligible_for_reviewed_memory_draft_planning_only`
  - exact `required_preconditions`
  - `capability_outcome`
    - current shipped state = `blocked_all_required`
    - first future widened state = `unblocked_all_required`
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - `partial_state_policy = partial_states_not_materialized`
  - `evaluated_at`

Emission rule:

- keep the current emitted value fixed at `capability_outcome = blocked_all_required`
- do not backfill `unblocked_all_required` from current shipped contract-object existence

### 6. Relationship To Transition Record And Apply

Keep the layers separate:

- satisfaction surface != emitted transition record
- emitted transition record != reviewed-memory apply result
- reviewed-memory apply result != user-level memory

Why this remains the honest order:

- capability satisfaction only says draft planning can truthfully open
- emitted transition record says one later transition was actually recorded
- apply result says one later reviewed-memory effect was actually applied

### 7. Boundary Recap

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
  - blocked-only status only
- boundary / rollback / disable / conflict / transition-audit contracts
  - current contract-exists-only layer
- `reviewed_memory_unblock_contract`
  - current blocked-threshold layer
- `reviewed_memory_capability_status`
  - current satisfied-capability outcome surface with current emitted `blocked_all_required` only
- future emitted transition record
  - later than satisfaction
- future reviewed-memory apply
  - later than emitted transition record

### 8. Cross-Session Boundary

Even after a future satisfaction surface is defined, cross-session counting still stays closed.

It still needs:

- explicit local store across sessions
- stale-resolution rules across session reloads
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session remains the honest boundary.

## Recommended Next Implementation Slice

- one smaller shared-planning-target normalization pass only

Why this remains the smallest honest next step:

- the repo now already ships the narrowed planning-only label across the three coupled target fields
- the next smallest clarification is normalization, not emitted transition records or apply
- widening directly into emitted transition record, apply, repeated-signal promotion, or cross-session counting would still overstate current machinery

## Open Questions

1. After the shipped narrowed label is in place, should the three target fields keep duplicating the same planning-only label, or later normalize to one shared planning-target ref?
