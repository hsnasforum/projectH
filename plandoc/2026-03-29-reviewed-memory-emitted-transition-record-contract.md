# 2026-03-29 Reviewed-Memory Emitted-Transition-Record Contract

## Goal

Fix the first exact contract for the future emitted transition-record layer above the already shipped same-session `reviewed_memory_transition_audit_contract`.

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
  - fixed `transition_action_vocabulary`:
    - `future_reviewed_memory_apply`
    - `future_reviewed_memory_stop_apply`
    - `future_reviewed_memory_reversal`
    - `future_reviewed_memory_conflict_visibility`
  - `transition_identity_requirement = canonical_local_transition_id_required`
  - `operator_visible_reason_boundary = explicit_reason_or_note_required`
  - `audit_stage = contract_only_not_emitted`
  - `audit_store_boundary = canonical_transition_record_separate_from_task_log`
  - `post_transition_invariants = aggregate_identity_and_contract_refs_retained`
  - `defined_at = aggregate.last_seen_at`
- current blocked truths remain:
  - `overall_status = blocked_all_required`
  - `unblock_status = blocked_all_required`
  - `capability_outcome = blocked_all_required`
- current contract objects still mean `contract exists` only and are not satisfaction by themselves

## Decision

### 1. Open A Future Emitted-Transition-Record Layer

Choose `Option A`.

Why this is the current MVP-safe choice:

- the shipped transition-audit contract already fixes canonical identity, action vocabulary, and the boundary that canonical transition records must stay separate from `task_log`
- leaving the first emitted surface undefined would keep canonical transition identity, append-only `task_log` mirror, and apply result too easy to blur together
- one emitted transition record is still narrower than reviewed-memory apply, so it is the smallest honest next layer above the current contract-only audit surface

Current shipped payload truth still remains:

- no emitted transition record object is currently serialized
- the shipped `reviewed_memory_transition_audit_contract` stays contract-only until later implementation work reopens emission
- the exact materialization trigger is now fixed separately in `plandoc/2026-03-29-reviewed-memory-transition-record-materialization-contract.md`
- current implementation now keeps that absence until a truthful trigger source exists

### 2. Exact Meaning Of An Emitted Transition Record

An emitted transition record means:

- one later same-session aggregate has one canonical local transition identity actually emitted
- the operator can inspect transition action, timing, same reviewed scope, same aggregate identity, exact supporting refs, and one explicit local reason or note
- that record is the canonical transition surface and remains separate from `task_log`

It does not mean:

- reviewed-memory apply result
- user-level memory
- repeated-signal promotion
- cross-session counting
- conflict resolution complete
- disable/apply/reversal success by itself

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

### 5. Minimum Future Transition-Record Shape

The smallest honest future surface is:

- one aggregate-level read-only `reviewed_memory_transition_record`

Recommended first shape:

- `transition_record_version = first_reviewed_memory_transition_record_v1`
- one `canonical_transition_id`
- one `transition_action`
- `reviewed_scope = same_session_exact_recurrence_aggregate_only`
- one `aggregate_identity_ref`
- exact `supporting_source_message_refs`
- exact `supporting_candidate_refs`
- optional `supporting_review_refs`
- one explicit `operator_reason_or_note`
- `record_stage = emitted_record_only_not_applied`
- `task_log_mirror_relation = mirror_allowed_not_canonical`
- one local `emitted_at`

Boundary notes:

- `transition_action` must come from the shipped fixed `transition_action_vocabulary`
- `canonical_transition_id` is the concrete emitted value that later satisfies `canonical_local_transition_id_required`
- `operator_reason_or_note` is the concrete emitted value that later satisfies `explicit_reason_or_note_required`
- `emitted_at` should record actual local transition emission time, not reuse aggregate `last_seen_at`

### 6. Relationship To Status / Satisfaction / Apply

Keep the layers separate:

- emitted transition record != `blocked_all_required`
- emitted transition record != `unblocked_all_required`
- emitted transition record != reviewed-memory apply result
- reviewed-memory apply result != user-level memory

Why this remains the honest order:

- blocked/satisfied vocabulary still belongs to the blocked threshold and capability outcome surfaces
- emitted transition record belongs to transition identity and operator-visible auditability
- apply result still belongs to later reviewed-memory effect machinery

### 7. Support And Mirror Boundary

Never treat these as emitted-transition-record basis:

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

Even after this contract is fixed, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session remains the honest boundary for the first emitted record.

## Recommended Next Slice

- one truthful operator-visible `future_reviewed_memory_apply` trigger-source implementation only

That slice should:

- keep the shipped `reviewed_memory_transition_audit_contract` unchanged and contract-only
- add no emitted record until the trigger source can create one real `canonical_transition_id`, one explicit `operator_reason_or_note`, and one local `emitted_at`
- keep `task_log` mirror-only and non-canonical
- stay smaller than reviewed-memory apply, repeated-signal promotion, cross-session counting, and user-level memory

Why this remains the smallest honest next step:

- planning-target wording, normalization, cleanup, and aftercare are already closed
- the next unresolved layer is transition emission, not planning-target compatibility
- widening directly into reviewed-memory apply, repeated-signal promotion, or cross-session counting would still overstate current machinery

## Open Questions

1. For later non-apply actions, should `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, and `future_reviewed_memory_conflict_visibility` keep the same record shape unchanged, or need later action-specific extensions?
