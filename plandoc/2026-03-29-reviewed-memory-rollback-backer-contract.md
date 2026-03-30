# 2026-03-29 Reviewed-Memory Rollback Backer Contract

## Goal

Fix the first exact truthful contract for the real later local rollback-capability backer behind future `rollback_source_ref`.

This backer layer sits:

- above the current read-only `reviewed_memory_rollback_contract`
- above the current exact-scope-validated but unresolved `rollback_source_ref` resolver
- below the full internal `reviewed_memory_capability_source_refs` family
- below any later payload-visible `reviewed_memory_capability_basis`
- well below any later `unblocked_all_required`, emitted `reviewed_memory_transition_record`, reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory

This document does not describe enabled submit UI, note input, emitted transition record materialization, reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory.

## Current Shipped Truth

- current same-session `recurrence_aggregate_candidates` remain read-only and blocked
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
- current blocked truths remain:
  - `reviewed_memory_precondition_status.overall_status = blocked_all_required`
  - `reviewed_memory_unblock_contract.unblock_status = blocked_all_required`
  - `reviewed_memory_capability_status.capability_outcome = blocked_all_required`
  - `reviewed_memory_transition_audit_contract.audit_stage = contract_only_not_emitted`
- current shell truth remains:
  - one separate aggregate-level `검토 메모 적용 후보` section fed only by `recurrence_aggregate_candidates`
  - each aggregate card shows disabled `검토 메모 적용 시작`
  - no note input and no emitted record
- current capability-source truth remains:
  - one internal `boundary_source_ref` now resolves for the same exact aggregate against the blocked trigger affordance
  - `rollback_source_ref` is now exact-scope-validated against the same exact aggregate, exact supporting refs, and current `reviewed_memory_rollback_contract`, and it now resolves one exact ref only to the same exact rollback-side handle materialized for that aggregate
  - one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate fact-source-instance result only from one exact matching proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_fact_source` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate fact-source result only from one exact matching fact-source-instance result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_event` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate event result only from one exact matching fact-source result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_event_producer` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate producer result only from one exact matching event result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_event_source` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate event-source result only from one exact matching producer result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_record` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate source-consumer record only from one exact matching event-source helper result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_applied_effect_target` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate shared target only from one exact matching source-consumer helper result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_reversible_effect_handle` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate rollback-capability handle only from one exact matching shared target plus one exact matching rollback contract
  - `disable_source_ref`, `conflict_source_ref`, and `transition_audit_source_ref` still remain unresolved
  - the full internal source family still resolves no result
- current payload truth remains:
  - no `reviewed_memory_capability_basis`
  - no `reviewed_memory_transition_record`

## Decision

### 1. Exact Meaning Of A Rollback-Capability Backer

Future truthful rollback-capability backer means:

- one later local capability source that can reverse only later applied reviewed-memory influence for one exact `same_session_exact_recurrence_aggregate_only`
- one backer that preserves aggregate identity, supporting refs, boundary draft linkage, and later audit trace while changing only the later applied effect
- one backer that remains smaller than full source-family resolution, payload-visible basis materialization, `unblocked_all_required`, emitted transition record, or reviewed-memory apply result

It does not mean:

- current `reviewed_memory_rollback_contract` alone
- current blocked aggregate trigger affordance
- emitted transition record
- reviewed-memory apply result
- user-level memory
- `task_log` replay

Keep the meaning chain exact:

- rollback contract exists != rollback backer exists
- unresolved resolver != real backer
- real backer != full source family resolved
- full source family resolved != basis object emitted
- basis object emitted != `unblocked_all_required`
- `unblocked_all_required` != emitted record

### 2. What Counts As Truthful Backer

The exact later local rollback-capability backer should stay one internal local `reviewed_memory_reversible_effect_handle`.

Minimum truthful shape:

- `handle_version = first_same_session_reviewed_memory_reversible_effect_handle_v1`
- `reviewed_scope = same_session_exact_recurrence_aggregate_only`
- one `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- one matching `boundary_source_ref`
- one matching `rollback_contract_ref`
- `effect_target_kind = applied_reviewed_memory_effect`
- `effect_capability = reversible_local_only`
- `effect_invariant = retain_identity_supporting_refs_boundary_and_audit`
- `effect_stage = handle_defined_not_applied`
- one local `handle_id`
- `defined_at`

Why this is the truthful minimum:

- it gives `rollback_source_ref` one real later local rollback-capability layer above the shipped contract without pretending any reviewed-memory effect is already applied
- it stays aggregate-scoped and exact-ref-bound instead of promoting support-only traces into rollback state
- it keeps reversal capability narrower than emitted transition identity, note collection, and apply result

The exact later local target beneath that handle should stay one shared internal `reviewed_memory_applied_effect_target`.

Minimum truthful target shape:

- `target_version = first_same_session_reviewed_memory_applied_effect_target_v1`
- `target_scope = same_session_exact_recurrence_aggregate_only`
- one `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- one matching `boundary_source_ref`
- `effect_target_kind = applied_reviewed_memory_effect`
- `target_capability_boundary = local_effect_presence_only`
- `target_stage = effect_present_local_only`
- one local `applied_effect_id`
- `present_locally_at`

The exact local effect-presence source beneath that target should stay one internal `reviewed_memory_local_effect_presence_event_source`.

Minimum truthful source shape:

- `event_source_version = first_same_session_reviewed_memory_local_effect_presence_event_source_v1`
- `event_source_scope = same_session_exact_recurrence_aggregate_only`
- one `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- one matching `boundary_source_ref`
- `effect_target_kind = applied_reviewed_memory_effect`
- `event_capability_boundary = local_effect_presence_only`
- `event_stage = presence_event_recorded_local_only`
- one local `applied_effect_id`
- `present_locally_at`

The exact later local proof boundary beneath the current fact-source-instance helper is now fixed separately as one shared internal `reviewed_memory_local_effect_presence_proof_boundary`.

The exact later local fact source beneath the current raw helper is now fixed separately as one shared internal `reviewed_memory_local_effect_presence_fact_source`.

The current `reviewed_memory_local_effect_presence_fact_source_instance` helper now materializes only from one exact matching local proof boundary for the same aggregate and supporting refs.

The current raw-event helper now materializes only from one exact matching local fact source for the same aggregate and supporting refs.

The exact later local event above that fact source and beneath the current producer helper should stay one shared internal `reviewed_memory_local_effect_presence_event`.

Minimum truthful event shape:

- `event_version = first_same_session_reviewed_memory_local_effect_presence_event_v1`
- `event_scope = same_session_exact_recurrence_aggregate_only`
- one `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- one matching `boundary_source_ref`
- `effect_target_kind = applied_reviewed_memory_effect`
- `event_capability_boundary = local_effect_presence_only`
- `event_stage = presence_observed_local_only`
- one local `applied_effect_id`
- `present_locally_at`

Why the target must stay separate from the handle:

- the handle is the rollback-side capability layer
- the target is the later local applied-effect-presence layer
- the event source is the exact later local effect-presence fact beneath the source-consumer helper and that target
- the source-consumer helper stays the exact later local normalization layer above that event source and below the target
- the handle should later point to that target while separately keeping one matching `rollback_contract_ref`
- the same target may later be reused by a disable-side handle without collapsing rollback and disable semantics into one contract

Why the current shipped `reviewed_memory_rollback_contract` remains insufficient:

- it is still contract-only
- it still keeps `rollback_target_kind = future_applied_reviewed_memory_effect_only`
- it does not provide any local reversible handle, local target id, or later effect-capability descriptor by itself

Never treat these as rollback backer:

- `candidate_review_record`
- queue presence
- approval-backed save alone
- historical adjunct alone
- `task_log` replay alone
- contract object existence alone

### 3. Relationship To Current Boundary Backer

Keep the two backers separate:

- current `boundary_source_ref` is already resolved current truth
- future real `rollback_source_ref` backer is the second backer only

Even after a truthful rollback-capability backer later exists:

- `disable_source_ref`, `conflict_source_ref`, and `transition_audit_source_ref` may still remain unresolved
- the full internal `reviewed_memory_capability_source_refs` family may still remain incomplete
- `reviewed_memory_capability_basis` may still remain absent
- `reviewed_memory_capability_status.capability_outcome` may still remain `blocked_all_required`

One or two backers must not be read as near-ready payload state.

The earlier rollback-only versus disable-reuse question is now closed:

- the first truthful later target should stay one shared `reviewed_memory_applied_effect_target`
- rollback and later disable should reuse that same target through separate later handles and separate matching contract refs
- shared target reuse is the smaller truthful boundary because both shipped contracts already point at `future_applied_reviewed_memory_effect_only`

### 4. Relationship To Current Rollback Contract

Keep these two layers separate:

- current shipped `reviewed_memory_rollback_contract`
  - still contract-only
  - still one rollback target-kind draft above the aggregate
- future real `reviewed_memory_reversible_effect_handle`
  - actual later local rollback capability only
  - not emitted record
  - not apply result
  - not rollback state machine
- future real `reviewed_memory_applied_effect_target`
  - actual later local applied-effect-presence target only
  - not rollback contract
  - not disable contract
  - not emitted record
  - not apply result

Why this separation matters:

- the contract says what later reversal must preserve
- the handle says one exact same-session aggregate finally has one rollback-capability layer that could honor that contract
- the shared target says one exact same-session aggregate later has one local applied-effect-presence target that rollback or disable handles may point to

### 5. Relationship To Trigger / Audit / Emission

Keep eight layers separate:

1. `reviewed_memory_rollback_contract` exists
2. `rollback_source_ref` now resolves one exact ref to that same handle only
3. real later local rollback-capability backer exists
4. full source family resolves
5. `reviewed_memory_capability_basis` materializes
6. `capability_outcome = unblocked_all_required`
7. transition record emitted
8. reviewed-memory apply result

Why this matters:

- contract != unresolved resolver
- unresolved resolver != real backer
- real backer != basis object
- basis object != emitted record
- emitted record != apply result

### 6. Support / Mirror Boundary

Keep support-only and mirror-only layers exact:

- approval-backed save remains supporting evidence only
- historical adjunct remains supporting context only
- review acceptance remains confidence support only
- `task_log` remains mirror / appendix only

None of them may become rollback backer by themselves.

### 7. UI Boundary

Current UI truth remains unchanged:

- aggregate card remains visible-but-disabled
- `검토 메모 적용 시작` remains disabled
- no note input
- no `canonical_transition_id`
- no `operator_reason_or_note`
- no `emitted_at`
- no emitted record

Future rollback-capability backer opening alone must not enable the card or change visible readiness.

### 8. Cross-Session Boundary

Even after a truthful same-session rollback-capability backer exists, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules across session reloads
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session exact aggregate remains the honest boundary.

## Recommended Next Slice

- one truthful same-aggregate local `disable_source_ref` materialization only

That slice should:

- consume the existing exact same-aggregate shared target plus the current exact `reviewed_memory_disable_contract` before reopening any new capability-source family materialization
- reopen only one truthful same-aggregate disable-side source in the same round
- keep `reviewed_memory_capability_basis` absent in the same round
- keep `reviewed_memory_capability_status.capability_outcome = blocked_all_required` in the same round
- keep the blocked aggregate-card affordance unchanged in the same round
- open no note input, `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, emitted record, or reviewed-memory apply result

Why this is the smallest honest next step:

- current repo already has the payload-hidden proof-record writer, the proof-boundary helper, the raw-event helper, the producer helper, the event-source helper, the source-consumer helper, the target helper, the handle helper, and one resolved internal `rollback_source_ref`
- the next missing piece is the exact later local disable-side source above the current `reviewed_memory_disable_contract` before the full internal source family can move forward
- it stays smaller than basis materialization, capability-status widening, enabled trigger, emitted transition record, reviewed-memory apply result, repeated-signal promotion, and cross-session counting

## Open Questions

1. After the rollback-side handle now exists, should the first truthful disable-side source round reuse the shared target immediately or keep one verification pass first?
2. After the second source ref exists, should the next round still keep the full source family internal-only for one verification pass before any basis object materializes?
