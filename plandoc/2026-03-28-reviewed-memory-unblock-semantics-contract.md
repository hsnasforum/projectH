# 2026-03-28 Reviewed-Memory Unblock Semantics Contract

## Goal

Fix the first exact meaning of same-session unblock after the full blocked-only precondition surface has already been materialized.

This document does not describe implemented reviewed-memory store, reviewed-memory apply, emitted transition records, repeated-signal promotion, user-level memory, or cross-session counting.

## Current Shipped Truth

- current same-session `recurrence_aggregate_candidates` remain read-only and promotion-ineligible
- each current aggregate item may now also expose:
  - `aggregate_promotion_marker`
  - `reviewed_memory_precondition_status`
  - `reviewed_memory_boundary_draft`
  - `reviewed_memory_rollback_contract`
  - `reviewed_memory_disable_contract`
  - `reviewed_memory_conflict_contract`
  - `reviewed_memory_transition_audit_contract`
  - `reviewed_memory_unblock_contract`
- current `reviewed_memory_precondition_status` still stays:
  - `overall_status = blocked_all_required`
  - no per-precondition satisfied / unsatisfied booleans
  - no partial-unblock workflow
  - no eligibility transition

Those current shipped objects are contract-only surfaces. None of them is a reviewed-memory apply result or a canonical reviewed-memory transition record.

## Decision

### 1. Exact Meaning Of Same-Session Unblock

Same-session unblock means the current blocked-only contract layer above one exact same-session aggregate can truthfully move into reviewed-memory draft planning readiness.

It means:

- all required reviewed-memory preconditions are satisfied for one exact same-session aggregate scope
- the same aggregate identity and the same exact supporting refs remain the basis of the next layer
- the first future target is still only reviewed-memory draft planning

It does not mean:

- reviewed-memory apply already happened
- emitted transition record already exists for that aggregate
- repeated-signal promotion already happened
- cross-session counting opened
- user-level memory opened

### 2. `Contract Exists` vs `Satisfied`

Current shipped read-only objects mean only that the contract family is described for that aggregate.

- `reviewed_memory_boundary_draft`
  - `contract exists` = one fixed narrow reviewed scope is described
  - `satisfied` = later reviewed-memory draft planning can bind one canonical local boundary to that exact aggregate identity plus exact supporting refs
- `reviewed_memory_rollback_contract`
  - `contract exists` = rollback target rules are described
  - `satisfied` = one later applied reviewed-memory effect can actually be reversed while keeping aggregate identity, supporting refs, and boundary / contract refs intact
- `reviewed_memory_disable_contract`
  - `contract exists` = stop-apply target rules are described
  - `satisfied` = one later applied reviewed-memory effect can actually stop applying without claiming reversal
- `reviewed_memory_conflict_contract`
  - `contract exists` = conflict scope and fixed categories are described
  - `satisfied` = competing reviewed-memory targets can actually become visible inside that same exact reviewed scope before apply
- `reviewed_memory_transition_audit_contract`
  - `contract exists` = canonical local transition-identity requirements are described
  - `satisfied` = later reviewed-memory transitions can actually emit canonical local transition records separate from `task_log`

Therefore:

- current read-only contract object existence never counts as satisfied by itself
- `task_log` mirror existence never counts as transition-audit satisfaction
- approval-backed save support, historical adjuncts, review acceptance, and queue presence never count as satisfaction by themselves

### 3. First Unblock Threshold

The first threshold should stay binary and conservative.

- all five preconditions remain mandatory
- no partial subset is enough to unblock
- the first vocabulary should stay:
  - current shipped state = `blocked_all_required`
  - first future widened state = `unblocked_all_required`

Partial satisfaction may later be inspectable, but it should still remain blocked-only in the current phase.

### 4. First Unblocked Target Boundary

Keep the current target label:

- `future_transition_target = eligible_for_reviewed_memory_draft`

Interpret it narrowly:

- one exact same-session aggregate may become eligible for reviewed-memory draft planning only
- this is still smaller than emitted transition records
- this is still smaller than reviewed-memory apply
- this is still smaller than repeated-signal promotion
- this is still smaller than cross-session counting

Current boundary / rollback / disable / conflict / transition-audit contracts remain neighboring contract surfaces even after unblock. They do not become transition results or apply results.

### 5. Relationship To Source-Message Review, Save Support, And Task Log

- `candidate_review_record`
  - remains one source-message reviewed-but-not-applied trace
  - may support confidence only
  - does not replace aggregate-level satisfaction
- `review_queue_items`
  - remain source-message review queue only
  - queue presence does not mean readiness
- approval-backed save and historical adjuncts
  - remain supporting evidence only
  - they do not replace aggregate-level readiness
- `task_log`
  - remains mirror / appendix only
  - it does not become the canonical reviewed-memory transition source even after unblock semantics is defined

### 6. Cross-Session Boundary

Same-session unblock semantics still does not open cross-session counting.

Cross-session still needs extra machinery:

- explicit local store across session reloads
- stale-resolution across sessions
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session remains the honest boundary even after exact unblock semantics is defined.

## Current Shipped Unblock Shape

The smallest surface now stays separate from the current blocked-only status object:

- one read-only `reviewed_memory_unblock_contract`
  - `unblock_version = same_session_reviewed_memory_unblock_v1`
  - `readiness_target = eligible_for_reviewed_memory_draft`
  - exact `required_preconditions`
  - `unblock_status`
    - current shipped state = `blocked_all_required`
    - first future widened state = `unblocked_all_required`
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - `partial_state_policy = partial_states_not_materialized`
  - `evaluated_at`

This does not overwrite the current shipped `reviewed_memory_precondition_status`.
Current object existence still does not mean satisfied readiness.

## Recommended Next Implementation Slice

- one later read-only satisfaction surface only, if any widening is reopened

Why this remains the smallest honest next step:

- the repo now truthfully exposes the blocked readiness threshold contract
- it still does not truthfully expose satisfied vs unsatisfied capability outcomes
- widening into apply, emitted transition records, or cross-session counting would still overstate current machinery

## Open Questions

1. Should the shipped `reviewed_memory_unblock_contract` keep `readiness_target = eligible_for_reviewed_memory_draft`, or rename it to `eligible_for_reviewed_memory_draft_planning_only` in a later narrowing pass?
