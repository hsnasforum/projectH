# 2026-03-29 Reviewed-Memory Capability-Basis Source Contract

## Goal

Fix the first exact truthful contract for the later local source that can justify future `reviewed_memory_capability_basis` materialization.

This source layer sits:

- above the current blocked contract chain and the already-shipped blocked aggregate trigger affordance
- below any later `reviewed_memory_capability_basis`
- below any later `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`
- well below any later emitted `reviewed_memory_transition_record`, reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory

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
  - one source-message `검토 후보` section fed only by `review_queue_items`
  - one separate aggregate-level `검토 메모 적용 후보` section fed only by `recurrence_aggregate_candidates`
  - each aggregate card shows disabled `검토 메모 적용 시작`
  - the blocked affordance shows no note input and emits no `reviewed_memory_transition_record`
- current emitted-record truth remains:
  - aggregate serialization probes a future `reviewed_memory_transition_record`
  - current payload still emits no such object
- current capability-basis truth also remains:
  - current implementation now also evaluates one internal `reviewed_memory_capability_source_refs` helper family
  - that helper family can now resolve one real `boundary_source_ref` backer against the same exact aggregate's blocked `검토 메모 적용 시작` trigger affordance
  - current implementation now also resolves one internal `rollback_source_ref` only as one exact ref to the same exact rollback-side handle materialized for that aggregate
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source-instance result only from one exact matching proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source result only from one exact matching fact-source-instance result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event` helper for that same exact aggregate, and it now materializes one internal same-aggregate event result only from one exact matching fact-source result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event_producer` helper for that same exact aggregate, and it now materializes one internal same-aggregate producer result only from one exact matching event result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate event-source result only from one exact matching producer result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_record` helper for that same exact aggregate, and it now materializes one internal same-aggregate source-consumer record only from one exact matching event-source helper result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_applied_effect_target` helper for that same exact aggregate, and it now materializes one internal same-aggregate shared target only from one exact matching source-consumer helper result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_reversible_effect_handle` helper for that same exact aggregate, and it now materializes one internal same-aggregate rollback-capability handle only from one exact matching shared target plus one exact matching rollback contract
  - the remaining three refs still remain unresolved, so the full helper family still resolves no result
  - aggregate serialization may now probe one future `reviewed_memory_capability_basis`
  - current payload still emits no such object because the full matching capability-basis source family still does not exist

## Decision

### 1. Exact Meaning Of Capability-Basis Source

Future truthful capability-basis source means:

- one exact later local capability source that proves the full all-required capability family is actually present for one exact same-session aggregate
- one source layer that is narrower than `reviewed_memory_capability_basis`, `unblocked_all_required`, emitted transition record, and reviewed-memory apply result
- one source layer that can later justify `reviewed_memory_capability_basis` materialization only for that same exact aggregate

It does not mean:

- `reviewed_memory_capability_basis` is already emitted now
- `reviewed_memory_capability_status.capability_outcome = unblocked_all_required` is already truthful now
- emitted transition record already exists
- reviewed-memory apply result already exists
- user-level memory exists

Keep the meaning chain exact:

- source exists != basis object emitted
- basis object emitted != `unblocked_all_required` unless the same exact aggregate still matches
- `unblocked_all_required` != emitted record
- emitted record != apply result

### 2. What Can Count As Truthful Source

The exact later source should be one additive internal aggregate-scoped helper family:

- `reviewed_memory_capability_source_refs`
  - `source_version = same_session_reviewed_memory_capability_source_refs_v1`
  - `source_scope = same_session_exact_recurrence_aggregate_only`
  - one `aggregate_identity_ref`
  - `supporting_source_message_refs`
  - `supporting_candidate_refs`
  - optional `supporting_review_refs`
  - exact `required_preconditions`
  - one `capability_source_refs`
    - `boundary_source_ref`
    - `rollback_source_ref`
    - `disable_source_ref`
    - `conflict_source_ref`
    - `transition_audit_source_ref`
  - `source_status = all_required_sources_present`
  - `evaluated_at`

Why this source family is the truthful minimum:

- it stays smaller than any later operator-visible payload object
- it proves actual later local capability presence instead of reinterpreting current read-only contract objects
- it keeps one exact same-session aggregate identity plus exact supporting refs as the canonical match boundary

Actual later presence means:

- `reviewed_memory_boundary_defined` counts only when `boundary_source_ref` can point to one canonical local reviewed-memory boundary source above the current boundary draft
  - current first resolved backer may point only to the same exact aggregate's blocked trigger affordance with the fixed action label `검토 메모 적용 시작`
- `rollback_ready_reviewed_memory_effect` counts only when `rollback_source_ref` can point to one later local rollback-capability source above the current rollback contract
  - that exact later source should stay one internal local `reviewed_memory_reversible_effect_handle`
  - minimum truthful shape:
    - `handle_version = first_same_session_reviewed_memory_reversible_effect_handle_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - one matching `boundary_source_ref`
    - one matching `rollback_contract_ref`
    - `effect_target_kind = applied_reviewed_memory_effect`
    - `effect_capability = reversible_local_only`
    - `effect_invariant = retain_identity_supporting_refs_boundary_and_audit`
    - `effect_stage = handle_defined_not_applied`
    - one local `handle_id`
    - `defined_at`
  - that handle must later point to one shared internal `reviewed_memory_applied_effect_target`
  - minimum truthful target shape:
    - `target_version = first_same_session_reviewed_memory_applied_effect_target_v1`
    - `target_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - one matching `boundary_source_ref`
    - `effect_target_kind = applied_reviewed_memory_effect`
    - `target_capability_boundary = local_effect_presence_only`
    - `target_stage = effect_present_local_only`
    - one local `applied_effect_id`
    - `present_locally_at`
  - that target must later materialize only from one shared internal `reviewed_memory_local_effect_presence_record`
  - that source-consumer helper must later materialize only from one shared internal `reviewed_memory_local_effect_presence_event_source`
  - that producer helper must later materialize only from one shared internal `reviewed_memory_local_effect_presence_event`
  - that raw-event helper must later materialize only from one shared internal `reviewed_memory_local_effect_presence_fact_source`
  - the exact later canonical local proof record beneath the current proof-boundary helper is now fixed separately as one internal `reviewed_memory_local_effect_presence_proof_record`
  - the exact later local proof boundary beneath the current fact-source-instance helper is now fixed separately as one shared internal `reviewed_memory_local_effect_presence_proof_boundary`
  - the current `reviewed_memory_local_effect_presence_proof_boundary` helper should later materialize only from one exact matching canonical local proof record for the same aggregate and supporting refs
  - the current `reviewed_memory_local_effect_presence_fact_source_instance` helper should later materialize only from one exact matching local proof boundary for the same aggregate and supporting refs
  - minimum truthful fact-source shape:
    - `fact_source_version = first_same_session_reviewed_memory_local_effect_presence_fact_source_v1`
    - `fact_source_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - one matching `boundary_source_ref`
    - `effect_target_kind = applied_reviewed_memory_effect`
    - `fact_capability_boundary = local_effect_presence_only`
    - `fact_stage = presence_fact_available_local_only`
    - one local `applied_effect_id`
    - `present_locally_at`
  - minimum truthful event shape:
    - `event_version = first_same_session_reviewed_memory_local_effect_presence_event_v1`
    - `event_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - one matching `boundary_source_ref`
    - `effect_target_kind = applied_reviewed_memory_effect`
    - `event_capability_boundary = local_effect_presence_only`
    - `event_stage = presence_observed_local_only`
    - one local `applied_effect_id`
    - `present_locally_at`
  - minimum truthful source shape:
    - `event_source_version = first_same_session_reviewed_memory_local_effect_presence_event_source_v1`
    - `event_source_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - one matching `boundary_source_ref`
    - `effect_target_kind = applied_reviewed_memory_effect`
    - `event_capability_boundary = local_effect_presence_only`
    - `event_stage = presence_event_recorded_local_only`
    - one local `applied_effect_id`
    - `present_locally_at`
  - the target should stay shared by later rollback and later disable handles while each handle still keeps its own matching contract ref
- `disable_ready_reviewed_memory_effect` counts only when `disable_source_ref` can point to one later local stop-apply-capability source above the current disable contract
- `conflict_visible_reviewed_memory_scope` counts only when `conflict_source_ref` can point to one later local competing-target visibility source above the current conflict contract
- `operator_auditable_reviewed_memory_transition` counts only when `transition_audit_source_ref` can point to one later local canonical transition-audit source above the current transition-audit contract

Current contract-object existence alone remains insufficient because:

- the shipped chain still means only `contract exists`
- the shipped aggregate affordance still remains blocked and disabled
- the shipped capability outcome still remains `blocked_all_required`

Never treat these as basis source:

- `candidate_review_record`
- queue presence
- approval-backed save alone
- historical adjunct alone
- `task_log` replay alone
- contract object existence alone

### 3. Relationship To Future `reviewed_memory_capability_basis`

Keep the source layer and basis object conceptually separate.

Exact order:

1. one truthful internal `reviewed_memory_capability_source_refs` exists for one exact aggregate
2. one later `reviewed_memory_capability_basis` may materialize for that same exact aggregate only
3. one later `reviewed_memory_capability_status.capability_outcome = unblocked_all_required` may become truthful only when that same matching basis object also exists

Future `reviewed_memory_capability_basis` should stay:

- aggregate-level
- read-only
- payload-visible
- derived only from the matching source family plus the matching current contract chain

Exact matching rule:

- `aggregate_identity_ref` must still match the same exact current aggregate
- `supporting_source_message_refs`, `supporting_candidate_refs`, and optional `supporting_review_refs` must still match that same exact aggregate
- the current blocked contract chain must still belong to that same exact aggregate

Current serializer truth remains unchanged:

- it may probe the future basis layer
- it must keep returning absence while no truthful source family exists

### 4. Relationship To Current Blocked Trigger Affordance

Current shipped trigger affordance remains:

- aggregate card visible
- action label `검토 메모 적용 시작`
- action disabled
- no note input
- no emitted record

Future basis-source layer remains separate from that UI truth.

Exact later condition for any later enablement eligibility:

- the same aggregate still matches the current blocked contract chain
- the same aggregate also resolves one matching internal `reviewed_memory_capability_source_refs`
- the same aggregate later materializes one matching `reviewed_memory_capability_basis`
- the same aggregate later exposes `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`

Even after the source layer later opens:

- the current card may still remain disabled
- enabled card behavior should remain separate from emitted record and note input
- source opening alone must not be presented as apply, submit, or transition emission

### 5. Relationship To Current Transition-Audit Contract

Keep seven layers separate:

1. `transition-audit contract exists`
2. `operator-visible trigger affordance exists`
3. `truthful capability-basis source exists`
4. `reviewed_memory_capability_basis` materializes
5. `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`
6. `transition record emitted`
7. `reviewed-memory apply result`

Why this matters:

- contract != trigger affordance
- trigger affordance != basis source
- basis source != basis object
- basis object != `unblocked_all_required`
- `unblocked_all_required` != emitted record
- emitted record != apply result

### 6. Review Queue Boundary

Keep current queue truth unchanged:

- `review_queue_items` remains source-message candidate review surface only
- `candidate_review_record` remains one source-message reviewed-but-not-applied trace only
- blocked aggregate trigger affordance remains aggregate transition-initiation boundary only
- future capability-basis source remains aggregate-level capability layer only

Therefore:

- source-message `accept` must not become capability-basis source
- `candidate_review_record` must not become basis object source
- `candidate_review_record` must not become emitted-record source by itself

### 7. Canonical Record / Note / Timestamp Boundary

Even when the capability-basis source later opens truthfully:

- `canonical_transition_id` is still not created there
- `operator_reason_or_note` is still not collected there
- `emitted_at` is still not created there

Why this remains smaller than emitted transition record:

- basis-source opening only says the aggregate now has later local capability proofs
- canonical transition identity, operator note collection, and emitted timestamp belong to the later emitted-record submit boundary

So:

- basis-source opening alone must not mint transition identity
- basis-source opening alone must not mint emitted timestamp
- basis-source opening alone must not require `task_log` mirror

### 8. Support / Mirror Boundary

Keep support-only layers exact:

- approval-backed save remains supporting evidence only
- historical adjunct remains supporting context only
- review acceptance remains confidence support only
- `task_log` remains mirror / appendix only

None of them may become capability-basis source by themselves.

### 9. Cross-Session Boundary

Even after a truthful same-session capability-basis source exists, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules across session reloads
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session exact aggregate remains the honest boundary.

## Recommended Next Slice

- one truthful same-aggregate `reviewed_memory_capability_basis` materialization only

All five capability source refs are now resolved (shipped 2026-03-30):
- `boundary_source_ref` backed by the aggregate trigger affordance
- `rollback_source_ref` backed by the `reviewed_memory_reversible_effect_handle`
- `disable_source_ref` backed by the `reviewed_memory_disable_contract` plus the shared `reviewed_memory_applied_effect_target`
- `conflict_source_ref` backed by the `reviewed_memory_conflict_contract` plus the shared `reviewed_memory_applied_effect_target`
- `transition_audit_source_ref` backed by the `reviewed_memory_transition_audit_contract` plus the shared `reviewed_memory_applied_effect_target`

The internal `reviewed_memory_capability_source_refs` family now materializes with `source_status = all_required_sources_present` in the store-backed path.

That next slice should:

- consume the now-complete internal source family and materialize one truthful `reviewed_memory_capability_basis` object
- keep `reviewed_memory_capability_status.capability_outcome = blocked_all_required` in the same round
- keep the existing blocked aggregate-card affordance unchanged in the same round
- open no note input, `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, or emitted transition record
- keep `unblocked_all_required` later than basis materialization

Why this is the smallest honest next step:

- current repo already has the complete internal source family with all five refs resolved
- the next missing piece is the exact basis object that should sit above that source family and below any `unblocked_all_required` or emitted transition record
- it stays smaller than status widening, emitted transition record, reviewed-memory apply result, repeated-signal promotion, and cross-session counting

## Open Questions

1. Should the basis object carry a snapshot of all five source refs or just a validated reference to the source family version?
2. Should basis materialization happen in the same round as `unblocked_all_required` widening, or should they stay separate?
