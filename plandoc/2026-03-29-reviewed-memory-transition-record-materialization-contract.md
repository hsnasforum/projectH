# 2026-03-29 Reviewed-Memory Transition-Record Materialization Contract

## Goal

Fix the first exact contract for when a future `reviewed_memory_transition_record` may truthfully materialize above the already shipped same-session `reviewed_memory_transition_audit_contract`.

This document does not describe reviewed-memory apply, reviewed-memory store, repeated-signal promotion, cross-session counting, or user-level memory.

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
  - `reviewed_memory_planning_target_ref`
- current shipped planning-target truth remains shared-ref-only:
  - `reviewed_memory_planning_target_ref` is the only canonical planning-target source
  - the earlier duplicated target echo fields are no longer current schema
- current shipped transition-audit contract remains contract-only:
  - `audit_version = first_reviewed_memory_transition_identity_v1`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - one `aggregate_identity_ref`
  - exact supporting refs
  - fixed `transition_action_vocabulary`
  - `transition_identity_requirement = canonical_local_transition_id_required`
  - `operator_visible_reason_boundary = explicit_reason_or_note_required`
  - `audit_stage = contract_only_not_emitted`
  - `audit_store_boundary = canonical_transition_record_separate_from_task_log`
  - `post_transition_invariants = aggregate_identity_and_contract_refs_retained`
  - `defined_at = aggregate.last_seen_at`
- future emitted-record shape is already fixed separately:
  - one later aggregate-level read-only `reviewed_memory_transition_record`
  - `transition_record_version = first_reviewed_memory_transition_record_v1`
  - `canonical_transition_id`
  - `transition_action`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - `aggregate_identity_ref`
  - exact supporting refs
  - `operator_reason_or_note`
  - `record_stage = emitted_record_only_not_applied`
  - `task_log_mirror_relation = mirror_allowed_not_canonical`
  - `emitted_at`
- current shipped payload still emits no such object
- current implementation now keeps that absence until a truthful trigger source exists
- current blocked truths remain:
  - `overall_status = blocked_all_required`
  - `unblock_status = blocked_all_required`
  - `capability_outcome = blocked_all_required`
- current contract objects still mean `contract exists` only and are not satisfaction by themselves

## Decision

### 1. First Truthful Emission Trigger

Choose one exact future trigger and keep current absence truthful until then.

Current repo truth:

- no truthful emitted action exists yet

Future first materialization trigger:

- one explicit operator-visible `future_reviewed_memory_apply` transition only

Why this is the smallest honest choice:

- `future_reviewed_memory_apply` is the earliest transition action that can happen once one exact same-session aggregate becomes truthfully ready for reviewed-memory draft planning
- `future_reviewed_memory_stop_apply` and `future_reviewed_memory_reversal` both require a later applied reviewed-memory effect to already exist, so they cannot be the first emitted action
- `future_reviewed_memory_conflict_visibility` requires separate competing-target visibility machinery and is broader than the first action-specific emission slice

First truthful emitted record may materialize only when all of the following are true:

- one exact same-session aggregate already has truthful `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`
- one explicit operator-visible `future_reviewed_memory_apply` transition actually occurs for that same exact aggregate
- one real `canonical_transition_id` is created at that emission boundary
- one explicit `operator_reason_or_note` is recorded at that same emission boundary
- one local `emitted_at` exists for that same emission boundary

Anything smaller is not enough:

- contract existence alone is not enough
- aggregate serialization alone is not enough
- `task_log` replay alone is not enough
- fake `canonical_transition_id` is not enough
- fake `operator_reason_or_note` is not enough

### 2. Current-State Materialization Rule

Current shipped payload still truthfully emits no `reviewed_memory_transition_record`.

Why current absence is truthful:

- no aggregate can yet truthfully reach `unblocked_all_required`
- no action-specific transition emission machinery exists
- no real `canonical_transition_id` or explicit `operator_reason_or_note` exists yet

Current absence means:

- no emitted transition has happened yet

It does not mean:

- the transition-audit contract is missing
- the future emitted-record shape is undefined
- reviewed-memory apply has opened
- user-level memory has opened

### 3. Relationship To The Current Transition-Audit Contract

Keep three layers separate:

1. `transition-audit contract exists`
   - current shipped vocabulary and identity boundary only
2. `transition record emitted`
   - one later canonical local record exists for one exact same-session aggregate
3. `reviewed-memory apply result`
   - one later reviewed-memory effect result above that emitted record

Why the audit contract must stay separate:

- the shipped audit contract still truthfully describes current payload behavior
- later emitted records should satisfy the already-shipped audit boundary, not overwrite or reinterpret it
- apply result remains later effect machinery and must not collapse back into the record surface

### 4. Canonical Record Vs `task_log` Mirror

Keep the boundary exact:

- canonical emitted transition record is one aggregate-level read-only record in the reviewed-memory layer
- `task_log` may mirror that record as append-only evidence, export, or appendix
- replay from `task_log` alone must not define canonical current transition state
- `task_log` remains mirror / appendix only and must not become the canonical transition store

First implementation-round coupling rule:

- `task_log` mirroring is optional in the first emitted-record implementation round

Why optional is the honest first step:

- canonical emitted record is the state-bearing surface
- requiring `task_log` mirroring in the same first round would couple canonical state to an appendix surface too early
- later mirroring can still be added without changing canonical identity rules

### 5. Minimum Future Materialization Rule

The smallest honest materialization rule is:

- no object until one exact emitted action exists
- first allowed action = `future_reviewed_memory_apply` only

Minimum first-round rule:

- emit one `reviewed_memory_transition_record` only for one actual `future_reviewed_memory_apply` transition
- keep `transition_action` fixed to that one emitted action in the first implementation slice
- keep `record_stage = emitted_record_only_not_applied`
- keep `task_log_mirror_relation = mirror_allowed_not_canonical`
- keep `emitted_at` as the actual local emission time
- keep absence truthful until the trigger above actually happens

### 6. Relationship To Status / Satisfaction / Apply

Keep the layers separate:

- emitted record trigger != `blocked_all_required`
- emitted record trigger != `unblocked_all_required`
- emitted record != reviewed-memory apply result
- reviewed-memory apply result != user-level memory

Why this remains the honest order:

- blocked/satisfied vocabulary still belongs to the blocked threshold and capability outcome surfaces
- emitted record belongs to transition identity and operator-visible auditability
- apply result still belongs to later reviewed-memory effect machinery

### 7. Support And Mirror Boundary

Never treat these as emitted-record basis:

- `candidate_review_record`
- queue presence
- approval-backed save alone
- historical adjunct alone
- `task_log` replay alone
- contract-object existence alone

Therefore:

- approval-backed save remains supporting evidence only
- historical adjunct remains supporting context only
- review acceptance remains confidence support only
- `task_log` remains mirror / appendix only

### 8. Cross-Session Boundary

Even after this materialization rule is fixed, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session remains the honest boundary for first transition emission.

## Recommended Next Slice

- one truthful operator-visible `future_reviewed_memory_apply` trigger-source implementation only

That slice should:

- keep the shipped `reviewed_memory_transition_audit_contract` unchanged and contract-only
- add no emitted record until the trigger source can create one real `canonical_transition_id`, one explicit `operator_reason_or_note`, and one local `emitted_at`
- keep `task_log` mirroring optional and mirror-only
- stay smaller than reviewed-memory apply, repeated-signal promotion, cross-session counting, and user-level memory

Why this remains the smallest honest next step:

- it lets the repo gain one truthful emitted-action source before any record materialization reopens
- it does not require opening stop-apply, reversal, conflict-visibility emission, or reviewed-memory effect results
- widening directly into reviewed-memory apply, repeated-signal promotion, or cross-session counting would still overstate current machinery

## Open Questions

1. After the first `future_reviewed_memory_apply` record ships, should later non-apply actions reuse the same record shape unchanged or require later action-specific extensions?
