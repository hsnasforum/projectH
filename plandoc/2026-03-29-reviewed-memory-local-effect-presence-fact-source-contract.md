# 2026-03-29 Reviewed-Memory Local-Effect-Presence Fact-Source Contract

## Goal

Fix the first exact truthful contract for the later local fact source beneath the current internal `reviewed_memory_local_effect_presence_event` helper.

This fact-source layer sits:

- above the current read-only `reviewed_memory_rollback_contract` and `reviewed_memory_disable_contract`
- above the current exact-scope-validated but unresolved `rollback_source_ref`
- below the current internal `reviewed_memory_local_effect_presence_event` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_event_producer` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_event_source` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_record` helper that still resolves no result
- below the current internal `reviewed_memory_applied_effect_target` helper that still resolves no result
- below the current internal `reviewed_memory_reversible_effect_handle` helper that still resolves no result
- well below the future full internal `reviewed_memory_capability_source_refs` family, any later `reviewed_memory_capability_basis`, any later `unblocked_all_required`, any emitted `reviewed_memory_transition_record`, any reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory

This document does not describe raw-event helper materialization, producer-helper materialization, event-source helper materialization, source-consumer helper materialization, target helper materialization, handle helper materialization, enabled submit UI, note input, emitted transition-record materialization, reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory.

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
- current helper truth remains:
  - `boundary_source_ref` resolves for the same exact aggregate against the blocked trigger affordance
  - `rollback_source_ref` is exact-scope-validated against the same exact aggregate, exact supporting refs, and current `reviewed_memory_rollback_contract`, but it still resolves no result
  - one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate fact-source-instance result only from one exact matching proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`
- one internal `reviewed_memory_local_effect_presence_fact_source` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate fact-source result only from one exact matching fact-source-instance result while reusing the same `applied_effect_id` and `present_locally_at`
- one internal `reviewed_memory_local_effect_presence_event` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate event result only from one exact matching fact-source result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_event_producer` helper is now also evaluated for that same exact aggregate, but it still resolves no result because producer materialization itself remains closed above that truthful same-aggregate event result
  - one internal `reviewed_memory_local_effect_presence_event_source` helper is now also evaluated for that same exact aggregate, and it now probes that producer helper while still resolving no result because no truthful same-aggregate producer-helper result exists yet
  - one internal `reviewed_memory_local_effect_presence_record` helper is now also evaluated for that same exact aggregate, and it now probes that event-source helper while still resolving no result because no truthful same-aggregate event-source helper result exists yet
  - one internal `reviewed_memory_applied_effect_target` helper is now also evaluated for that same exact aggregate, and it now probes that source-consumer helper while still resolving no result because no truthful same-aggregate source-consumer helper result exists yet
  - one internal `reviewed_memory_reversible_effect_handle` helper is now also evaluated for that same exact aggregate, and it now probes that target helper while still resolving no result because no truthful target exists yet
  - `disable_source_ref`, `conflict_source_ref`, and `transition_audit_source_ref` still remain unresolved
  - the full internal source family still resolves no result
- current payload truth remains:
  - no `reviewed_memory_capability_basis`
  - no `reviewed_memory_transition_record`

## Decision

### 1. Exact Meaning Of The Local Fact Source

Future truthful local fact source means:

- one later local source that can prove one same-aggregate reviewed-memory effect-presence fact for `same_session_exact_recurrence_aggregate_only`
- one source that can let the current `reviewed_memory_local_effect_presence_event` helper materialize without implying higher helper materialization, emitted record, or reviewed-memory apply result
- one source that remains smaller than `reviewed_memory_local_effect_presence_event_producer`, `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, the full internal `reviewed_memory_capability_source_refs` family, `reviewed_memory_capability_basis`, `unblocked_all_required`, emitted transition record, reviewed-memory apply result, repeated-signal promotion, or user-level memory

It does not mean:

- current `reviewed_memory_rollback_contract` alone
- current `reviewed_memory_disable_contract` alone
- current `reviewed_memory_local_effect_presence_event` helper alone
- current `reviewed_memory_local_effect_presence_event_producer` helper alone
- current blocked aggregate trigger affordance
- emitted transition record
- reviewed-memory apply result
- `task_log` replay

Keep the meaning chain exact:

- contract exists != local fact source exists
- helper exists != local fact source exists
- local fact source exists != raw-event helper already materialized
- raw-event helper materialized != producer helper materialized
- producer helper materialized != event-source helper materialized
- event-source helper materialized != source-consumer helper materialized
- source-consumer helper materialized != target helper materialized
- target helper materialized != basis object
- basis object != `unblocked_all_required`
- `unblocked_all_required` != emitted record

### 2. Exact Local Fact Source Shape

The exact later canonical local proof record beneath the current proof-boundary helper is now fixed separately as one internal `reviewed_memory_local_effect_presence_proof_record`.

The exact later local proof boundary beneath the current fact-source-instance helper is now fixed separately as one shared internal `reviewed_memory_local_effect_presence_proof_boundary`.

The exact later local fact source should stay one shared internal `reviewed_memory_local_effect_presence_fact_source`.

Minimum truthful shape:

- `fact_source_version = first_same_session_reviewed_memory_local_effect_presence_fact_source_v1`
- `fact_source_scope = same_session_exact_recurrence_aggregate_only`
- one `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- one matching `boundary_source_ref`
- `effect_target_kind = applied_reviewed_memory_effect`
- `fact_capability_boundary = local_effect_presence_only`
- `fact_stage = presence_fact_available_local_only`
- one local `applied_effect_id`
- `present_locally_at`

Exact relation rules:

- the current `reviewed_memory_local_effect_presence_proof_boundary` helper should later materialize only from one exact matching canonical local proof record for the same aggregate and supporting refs
- the current `reviewed_memory_local_effect_presence_fact_source_instance` helper should later materialize only from one exact matching local proof boundary for the same aggregate and supporting refs
- the fact source should stay shared across later rollback and later disable consumption
- the fact source itself must not carry `rollback_contract_ref` or `disable_contract_ref`
- the current raw-event helper should later materialize only from one exact matching local fact source for the same aggregate and supporting refs
- the current producer helper should later materialize only from one exact matching raw-event helper result for the same aggregate and supporting refs
- the current event-source helper should later materialize only from one exact matching producer-helper result for the same aggregate and supporting refs
- the current source-consumer helper should later materialize only from one exact matching event-source helper result for the same aggregate and supporting refs
- the current target helper should later materialize only from one exact matching source-consumer helper result for the same aggregate and supporting refs

Local identity and timestamp rules:

- do not add a second fact id in the first contract
- reuse `applied_effect_id` as the first local identity minted exactly at the smaller truthful canonical proof-record instant and reused unchanged at the truthful local fact-source instant
- `present_locally_at` must be that same first truthful canonical local instant reused at the local fact-source layer
- `aggregate.last_seen_at` may be reused only when it is exactly that same first truthful local instant, not as a generic fallback

Why this fact source is the truthful minimum:

- it is smaller than raw-event helper materialization, producer-helper materialization, event-source helper materialization, source-consumer helper materialization, target helper materialization, handle helper materialization, source-family resolution, basis materialization, and any payload-visible readiness or apply layer
- it captures only one local effect-presence fact source, not rollback capability, disable capability, emitted record, or apply result
- it preserves the later shared-target-plus-separate-handle design without inventing current capability state

### 3. Relationship To The Current Raw Event Helper

Current `reviewed_memory_local_effect_presence_event` helper still remains absent because:

- it already validates the same exact aggregate identity, exact supporting refs, and current resolved `boundary_source_ref`
- current repo now also materializes one truthful same-aggregate fact-source result above that fact-source-instance layer while reusing the same exact `applied_effect_id` and `present_locally_at`
- therefore the raw-event helper still remains explicit absence only because raw-event materialization itself stays closed in the current round, not because the lower local fact-source layer is missing

When the fact source later exists:

- the raw-event helper should materialize one exact local event from that fact source only
- the raw-event helper should preserve the same exact `aggregate_identity_ref`, supporting refs, `boundary_source_ref`, `applied_effect_id`, and `present_locally_at`

Keep the layers separate:

- local fact source != raw event helper
- raw event helper != producer helper
- producer helper != event-source helper
- event-source helper != source-consumer helper
- source-consumer helper != target helper
- target helper != handle helper
- handle helper != `rollback_source_ref`

The honest sequencing is:

- current round: proof-boundary helper now materializes one truthful same-aggregate result
- current round: fact-source-instance helper now materializes one internal same-aggregate result
- current round: fact-source helper now materializes one internal same-aggregate result
- current round: raw-event helper exists but remains absent
- current round: producer helper exists but remains absent
- current round: event-source helper exists but remains absent
- current round: source-consumer helper exists but remains absent
- current round: target helper exists but remains absent
- current round: handle helper exists but remains unresolved
- current implementation round: one internal same-aggregate canonical local proof-record scaffold now exists beneath the current proof-boundary helper
- current implementation round: one truthful same-aggregate local proof boundary now materializes inside that helper above that canonical local proof record/store
- next implementation round: raw-event helper may materialize above that fact-source layer only
- later adjacent rounds: producer helper, event-source helper, source-consumer helper, target helper, and then handle helper may reopen in order

### 4. Relationship To Rollback And Disable Contracts

Keep current shipped contract-only layers unchanged:

- `reviewed_memory_rollback_contract`
  - still contract-only
  - still rollback target-kind draft only
- `reviewed_memory_disable_contract`
  - still contract-only
  - still stop-apply target-kind draft only

The future local fact source should stay shared, not rollback-first.

Why shared source is the honest choice:

- both shipped contracts already narrow to `future_applied_reviewed_memory_effect_only`
- the fact source describes only one local applied-effect-presence fact beneath any later handle semantics
- rollback and later disable should stay separate capabilities on separate later handles
- a rollback-first fact source would overstate current capability meaning before any later handle exists

### 5. Relationship To Current Trigger / Audit / Emission Layers

Keep twenty layers separate:

1. rollback / disable contracts exist
2. `rollback_source_ref` is exact-scope-validated but unresolved
3. `reviewed_memory_local_effect_presence_event` helper exists but absent
4. `reviewed_memory_local_effect_presence_event_producer` helper exists but absent
5. `reviewed_memory_local_effect_presence_event_source` helper exists but absent
6. `reviewed_memory_local_effect_presence_record` helper exists but absent
7. `reviewed_memory_applied_effect_target` helper exists but absent
8. `reviewed_memory_reversible_effect_handle` helper exists but unresolved
9. exact local fact source exists
10. raw-event helper materializes
11. producer helper materializes
12. event-source helper materializes
13. source-consumer helper materializes
14. target helper materializes
15. handle helper can truthfully point to that target
16. full source family resolves
17. `reviewed_memory_capability_basis` materializes
18. `capability_outcome = unblocked_all_required`
19. transition record emitted
20. reviewed-memory apply result

Why this matters:

- contract != unresolved resolver
- unresolved resolver != raw-event helper
- raw-event helper != local fact source
- local fact source != raw-event helper materialization
- raw-event helper != producer helper
- producer helper != event-source helper
- event-source helper != source-consumer helper
- source-consumer helper != target helper
- target helper != basis object
- basis object != emitted record
- emitted record != apply result

### 6. Support / Mirror Boundary

Never treat these as local fact source:

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
- future local fact source opening alone must not enable the card
- no note input
- no `canonical_transition_id`
- no `operator_reason_or_note`
- no `emitted_at`
- no emitted record

### 8. Cross-Session Boundary

Even after a truthful same-session local fact source exists, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules across session reloads
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session exact aggregate remains the honest boundary.

## Recommended Next Slice

- one truthful same-aggregate local event-producer materialization only

That slice should:

- consume the existing exact same-aggregate fact-source helper result that already sits above the current fact-source-instance helper and the smaller proof-boundary / proof-record layers
- keep the current fact-source helper materialized in the same round
- keep the current producer helper absent in the same round
- keep the current event-source helper absent in the same round
- keep the current source-consumer helper absent in the same round
- keep the current target helper absent in the same round
- keep the current handle helper unresolved in the same round
- keep `reviewed_memory_capability_basis` absent in the same round
- keep `reviewed_memory_capability_status.capability_outcome = blocked_all_required` in the same round
- keep the existing blocked aggregate-card affordance unchanged in the same round
- open no note input, `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, emitted transition record, or reviewed-memory apply result

Why this is the smallest honest next step:

- current repo already has the payload-hidden proof-record writer, the proof-boundary helper, the fact-source-instance helper, and the higher helper chain above it
- the next missing piece is the exact local event result that still cannot truthfully materialize above that existing fact-source layer
- reopening only that local event result is smaller than producer-helper materialization, event-source helper materialization, target materialization, basis object emission, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result, repeated-signal promotion, and cross-session counting

## Open Questions

1. Now that the first truthful fact-source result exists, should the raw-event helper reopen in its own adjacent round or stay absent for one verification round first?
2. Should the first canonical proof-record store stay session-persistent only, or reopen later as a separate reviewed-memory local store without widening into cross-session counting?
