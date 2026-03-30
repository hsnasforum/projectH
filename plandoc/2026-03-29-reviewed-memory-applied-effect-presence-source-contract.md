# 2026-03-29 Reviewed-Memory Applied-Effect-Presence Source Contract

## Goal

Fix the first exact truthful contract for the later local effect-presence source beneath the current internal `reviewed_memory_applied_effect_target` helper.

This source layer sits:

- above the current read-only `reviewed_memory_rollback_contract` and `reviewed_memory_disable_contract`
- above the current exact-scope-validated but unresolved `rollback_source_ref`
- below the current internal `reviewed_memory_applied_effect_target` helper that still resolves no result
- below the current internal `reviewed_memory_reversible_effect_handle` helper that still resolves no result
- below the future full internal `reviewed_memory_capability_source_refs` family
- well below any later `reviewed_memory_capability_basis`, `unblocked_all_required`, emitted `reviewed_memory_transition_record`, reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory

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
- current internal helper truth remains:
  - `boundary_source_ref` now resolves for the same exact aggregate against the blocked trigger affordance
  - `rollback_source_ref` is exact-scope-validated against the same exact aggregate, exact supporting refs, and current `reviewed_memory_rollback_contract`, but it still resolves no result
  - one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper is now also evaluated for that same exact aggregate, but it still resolves no result because no truthful same-aggregate local proof boundary exists in the repo yet
  - one internal `reviewed_memory_local_effect_presence_fact_source` helper is now also evaluated for that same exact aggregate, and it now probes that fact-source-instance helper while still resolving no result because no truthful same-aggregate local proof boundary exists beneath that helper yet
  - one internal `reviewed_memory_local_effect_presence_event` helper is now also evaluated for that same exact aggregate, but it still resolves no result because no truthful same-aggregate local effect-presence fact source exists in the repo yet
  - one internal `reviewed_memory_local_effect_presence_event_producer` helper is now also evaluated for that same exact aggregate, but it still resolves no result because no truthful same-aggregate local effect-presence event exists above that fact source yet
  - one internal `reviewed_memory_local_effect_presence_event_source` helper is now also evaluated for that same exact aggregate, and it now probes that producer helper while still resolving no result because no truthful same-aggregate local effect event exists yet
  - one internal `reviewed_memory_local_effect_presence_record` helper is now also evaluated for that same exact aggregate, and it now probes that event-source helper while still resolving no result because no truthful same-aggregate event-source helper result exists yet
  - one internal `reviewed_memory_applied_effect_target` helper is now also evaluated for that same exact aggregate, and it now probes that source-consumer helper while still resolving no result because no truthful same-aggregate source-consumer helper result exists yet
  - one internal `reviewed_memory_reversible_effect_handle` helper is now evaluated for that same exact aggregate, and it now probes that target helper while still resolving no result because no truthful target exists yet
  - `disable_source_ref`, `conflict_source_ref`, and `transition_audit_source_ref` still remain unresolved
  - the full internal source family still resolves no result
- current payload truth remains:
  - no `reviewed_memory_capability_basis`
  - no `reviewed_memory_transition_record`

## Decision

### 1. Exact Meaning Of The Local Effect-Presence Source

Future truthful local effect-presence source means:

- one later local source that proves one reviewed-memory effect is locally present for one exact `same_session_exact_recurrence_aggregate_only`
- one source that can later justify materializing one shared internal `reviewed_memory_applied_effect_target`
- one source that remains smaller than full source-family resolution, `reviewed_memory_capability_basis`, `unblocked_all_required`, emitted transition record, reviewed-memory apply result, repeated-signal promotion, or user-level memory

It does not mean:

- current `reviewed_memory_rollback_contract` alone
- current `reviewed_memory_disable_contract` alone
- current `reviewed_memory_applied_effect_target` helper alone
- current `reviewed_memory_reversible_effect_handle` helper alone
- current blocked aggregate trigger affordance
- emitted transition record
- reviewed-memory apply result
- `task_log` replay

Keep the meaning chain exact:

- contract exists != effect-presence source exists
- helper exists != effect-presence source exists
- effect-presence source exists != target helper already emits result
- target helper result != basis object
- basis object != `unblocked_all_required`
- `unblocked_all_required` != emitted record

### 2. What Counts As Truthful Source

The exact later local source should stay one shared internal `reviewed_memory_local_effect_presence_event_source`.

The exact later local proof boundary beneath the current fact-source-instance helper is now fixed separately as one shared internal `reviewed_memory_local_effect_presence_proof_boundary`.

The exact later local fact source beneath the current raw helper is now fixed separately as one shared internal `reviewed_memory_local_effect_presence_fact_source`.

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

Minimum truthful shape:

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

Exact relation rules:

- the source should stay shared across later rollback and later disable consumption
- the event should stay shared across later rollback and later disable consumption before any later handle semantics split
- the current `reviewed_memory_local_effect_presence_fact_source_instance` helper should later materialize only from one exact matching local proof boundary for the same aggregate and supporting refs
- the current raw-event helper `reviewed_memory_local_effect_presence_event` should later materialize only from one exact matching local fact source for the same aggregate and supporting refs
- the current producer helper `reviewed_memory_local_effect_presence_event_producer` should later materialize only from one exact matching local event for the same aggregate and supporting refs
- the source itself must not carry `rollback_contract_ref` or `disable_contract_ref`
- later rollback and later disable handles must bind that shared source-derived target back to the matching contract ref separately
- the current source-consumer helper `reviewed_memory_local_effect_presence_record` should later consume only one exact matching event source for the same aggregate and supporting refs
- the current target helper should later consume only that exact matching source-consumer helper result for the same aggregate and supporting refs

Local identity and timestamp rules:

- `applied_effect_id` must be minted only from one later local fact source for that same exact aggregate and then preserved unchanged through the later raw-event helper and later source layers
- `applied_effect_id` must not be derived from current contract existence, queue presence, review acceptance, approval-backed save support, historical adjuncts, or `task_log` replay
- `present_locally_at` must be one local timestamp minted at the first truthful local effect-presence instant
- `aggregate.last_seen_at` may be reused only when it is exactly the first truthful local effect-presence instant, not as a generic fallback

Why this exact shared source is the truthful minimum:

- it stays smaller than target materialization, handle materialization, full source-family resolution, and any payload-visible readiness layer
- it captures only local effect presence, not rollback capability or stop-apply capability
- it lets later rollback and later disable paths reuse one shared presence fact without collapsing their separate handle and contract semantics

### 3. Relationship To The Current Target Helper

Current `reviewed_memory_applied_effect_target` helper still remains absent because:

- it already validates the same exact aggregate, exact supporting refs, current resolved `boundary_source_ref`, and current blocked contract chain
- but current repo still has no truthful `reviewed_memory_local_effect_presence_event_source` result to consume

When the source later exists:

- the target helper should consume one exact matching source record
- the target helper should then project one shared internal `reviewed_memory_applied_effect_target` with the same `aggregate_identity_ref`, supporting refs, `boundary_source_ref`, `applied_effect_id`, and `present_locally_at`

Keep the layers separate:

- source != target helper
- target helper != handle helper
- handle helper != `rollback_source_ref`
- `rollback_source_ref` != basis object

The honest sequencing is:

- current round: one internal `reviewed_memory_local_effect_presence_event` helper exists but still remains absent
- current round: one internal `reviewed_memory_local_effect_presence_event_producer` helper exists but still remains absent
- current round: one internal `reviewed_memory_local_effect_presence_event_source` helper exists but still remains absent
- current round: one internal `reviewed_memory_local_effect_presence_record` helper now probes that event-source helper but still remains absent
- next proof-boundary scaffold round: one internal same-aggregate local proof-boundary scaffold may land beneath the fact-source-instance helper
- later adjacent round: the existing raw-event helper, the producer helper, and then the existing target helper may reopen in order

### 4. Relationship To Rollback And Disable Contracts

Keep current shipped contract-only layers unchanged:

- `reviewed_memory_rollback_contract`
  - still contract-only
  - still rollback target-kind draft only
- `reviewed_memory_disable_contract`
  - still contract-only
  - still stop-apply target-kind draft only

The future local effect-presence source should stay shared, not rollback-only.

Why shared source is the honest choice:

- both contracts already narrow to `future_applied_reviewed_memory_effect_only`
- the source describes only one local applied-effect presence fact
- rollback and later disable should remain separate capabilities on separate later handles
- a rollback-first source would overstate current knowledge before any local effect-presence event exists

### 5. Relationship To Current Trigger / Audit / Emission Layers

Keep twelve layers separate:

1. rollback / disable contracts exist
2. `rollback_source_ref` is exact-scope-validated but unresolved
3. `reviewed_memory_applied_effect_target` helper exists but resolves no result
4. `reviewed_memory_reversible_effect_handle` helper exists but resolves no result
5. exact local effect-presence source exists
6. target helper materializes
7. handle helper can truthfully point to that target
8. full source family resolves
9. `reviewed_memory_capability_basis` materializes
10. `capability_outcome = unblocked_all_required`
11. transition record emitted
12. reviewed-memory apply result

Why this matters:

- contract != unresolved resolver
- unresolved resolver != target helper
- target helper != source
- source != target materialization
- target materialization != basis object
- basis object != emitted record
- emitted record != apply result

### 6. Support / Mirror Boundary

Never treat these as effect-presence source:

- `candidate_review_record`
- queue presence
- approval-backed save alone
- historical adjunct alone
- `task_log` replay alone
- contract object existence alone

Therefore:

- approval-backed save remains supporting evidence only
- historical adjunct remains supporting context only
- review acceptance remains confidence support only
- `task_log` remains mirror / appendix only

### 7. UI Boundary

Current UI truth remains unchanged:

- aggregate card remains visible-but-disabled
- future local effect-presence source opening alone must not enable the card
- no note input
- no `canonical_transition_id`
- no `operator_reason_or_note`
- no `emitted_at`
- no emitted record

### 8. Cross-Session Boundary

Even after a truthful same-session local effect-presence source exists, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules across session reloads
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session exact aggregate remains the honest boundary.

## Recommended Next Slice

- one internal same-aggregate local proof-boundary scaffold only

That slice should:

- add one exact local proof-boundary scaffold beneath the internal `reviewed_memory_local_effect_presence_fact_source_instance` helper only
- keep the internal `reviewed_memory_local_effect_presence_event` helper absent in the same round
- keep the producer helper itself absent unless one truthful same-aggregate local event can already be sourced in that round
- keep the current source-consumer helper absent unless one truthful same-aggregate event source actually exists
- keep the current target helper absent unless one truthful same-aggregate source-consumer result actually exists
- keep the current handle helper unresolved in the same round
- keep `reviewed_memory_capability_basis` absent in the same round
- keep `reviewed_memory_capability_status.capability_outcome = blocked_all_required` in the same round
- keep the existing blocked aggregate-card affordance unchanged in the same round
- open no note input, `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, emitted transition record, or reviewed-memory apply result

Why this is the smallest honest next step:

- current repo already has the unresolved rollback resolver, the internal raw-event helper, the internal producer helper, the internal event-source helper, the internal source-consumer helper, the internal target helper, and the internal handle helper
- the next missing piece is the exact local fact source the raw-event helper still cannot truthfully materialize from
- it stays smaller than target materialization, basis object emission, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result, repeated-signal promotion, and cross-session counting

## Open Questions

1. Which exact later local event boundary should first mint `applied_effect_id` and `present_locally_at` without implying emitted transition record or reviewed-memory apply?
2. When later disable-side machinery opens, should it consume the shared source immediately or land one separate verification round first before a disable-side handle starts using it?
