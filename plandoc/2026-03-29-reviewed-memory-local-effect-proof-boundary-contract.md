# 2026-03-29 Reviewed-Memory Local-Effect Proof-Boundary Contract

## Goal

Fix the first exact truthful contract for the later local proof boundary beneath the current internal `reviewed_memory_local_effect_presence_fact_source_instance` helper.

This proof-boundary layer sits:

- above the current read-only `reviewed_memory_rollback_contract` and `reviewed_memory_disable_contract`
- above the current exact-scope-validated but unresolved `rollback_source_ref`
- below the current internal `reviewed_memory_local_effect_presence_fact_source_instance` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_fact_source` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_event` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_event_producer` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_event_source` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_record` helper that still resolves no result
- below the current internal `reviewed_memory_applied_effect_target` helper that still resolves no result
- below the current internal `reviewed_memory_reversible_effect_handle` helper that still resolves no result
- well below the future full internal `reviewed_memory_capability_source_refs` family, any later `reviewed_memory_capability_basis`, any later `unblocked_all_required`, any emitted `reviewed_memory_transition_record`, any reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory

This document does not describe fact-source-instance helper materialization, fact-source helper materialization, raw-event helper materialization, producer-helper materialization, event-source helper materialization, source-consumer helper materialization, target helper materialization, handle helper materialization, enabled submit UI, note input, emitted transition-record materialization, reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory.

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
  - one internal `reviewed_memory_local_effect_presence_proof_record` helper is now also evaluated for that same exact aggregate, and current implementation now also truthfully mints one exact payload-hidden canonical local proof-record/store entry for the current exact aggregate state inside the same-session `reviewed_memory_local_effect_presence_proof_record_store` boundary while still keeping source-message review acceptance, review-queue presence, approval-backed save support, historical adjuncts, and `task_log` replay outside that lower proof-record layer
  - one internal `reviewed_memory_local_effect_presence_proof_boundary` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate proof boundary only from one exact matching canonical local proof record/store entry while reusing the same `applied_effect_id` and `present_locally_at`; it still requires the aggregate's exact `first_seen_at` anchor before any later higher proof can mint `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate fact-source-instance result only from one exact matching proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_fact_source` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate fact-source result only from one exact matching fact-source-instance result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_event` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate event result only from one exact matching fact-source result while reusing the same `applied_effect_id` and `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_event_producer` helper is now also evaluated for that same exact aggregate, but it still resolves no result because producer materialization itself remains closed above that truthful same-aggregate event result
  - one internal `reviewed_memory_local_effect_presence_event_source` helper is now also evaluated for that same exact aggregate, and it now probes that producer helper while still resolving no result because no truthful same-aggregate local effect event exists yet
  - one internal `reviewed_memory_local_effect_presence_record` helper is now also evaluated for that same exact aggregate, and it now probes that event-source helper while still resolving no result because no truthful same-aggregate event-source helper result exists yet
  - one internal `reviewed_memory_applied_effect_target` helper is now also evaluated for that same exact aggregate, and it now probes that source-consumer helper while still resolving no result because no truthful same-aggregate source-consumer helper result exists yet
  - one internal `reviewed_memory_reversible_effect_handle` helper is now also evaluated for that same exact aggregate, and it now probes that target helper while still resolving no result because no truthful target exists yet
  - `disable_source_ref`, `conflict_source_ref`, and `transition_audit_source_ref` still remain unresolved
  - the full internal source family still resolves no result
- current payload truth remains:
  - no `reviewed_memory_capability_basis`
  - no `reviewed_memory_transition_record`

## Decision

### 1. Exact Meaning Of The Local Proof Boundary

Future truthful local proof boundary means:

- one later local boundary result that can materialize only after one smaller canonical local proof record/store first mints one same-aggregate `applied_effect_id` plus one same-instant `present_locally_at` for `same_session_exact_recurrence_aggregate_only`
- one boundary that can let the current `reviewed_memory_local_effect_presence_fact_source_instance` helper materialize without implying higher helper materialization, emitted record, or reviewed-memory apply result
- one boundary that remains smaller than `reviewed_memory_local_effect_presence_fact_source`, `reviewed_memory_local_effect_presence_event`, `reviewed_memory_local_effect_presence_event_producer`, `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, the full `reviewed_memory_capability_source_refs` family, `reviewed_memory_capability_basis`, `unblocked_all_required`, emitted transition record, reviewed-memory apply result, repeated-signal promotion, or user-level memory

It does not mean:

- current `reviewed_memory_rollback_contract` alone
- current `reviewed_memory_disable_contract` alone
- current `reviewed_memory_local_effect_presence_fact_source_instance` helper alone
- current `reviewed_memory_local_effect_presence_fact_source` helper alone
- current blocked aggregate trigger affordance
- emitted transition record
- reviewed-memory apply result
- `task_log` replay

Keep the meaning chain exact:

- contract exists != local proof boundary exists
- helper exists != local proof boundary exists
- local proof boundary exists != fact-source-instance helper already materialized
- fact-source-instance helper materialized != fact-source helper materialized
- fact-source helper materialized != raw-event helper materialized
- raw-event helper materialized != producer helper materialized
- producer helper materialized != event-source helper materialized
- event-source helper materialized != source-consumer helper materialized
- source-consumer helper materialized != target helper materialized
- target helper materialized != basis object
- basis object != `unblocked_all_required`
- `unblocked_all_required` != emitted record

### 2. Exact Local Proof-Boundary Shape

The exact later local proof boundary should stay one shared internal `reviewed_memory_local_effect_presence_proof_boundary`.

Minimum truthful shape:

- `proof_boundary_version = first_same_session_reviewed_memory_local_effect_presence_proof_boundary_v1`
- `proof_boundary_scope = same_session_exact_recurrence_aggregate_only`
- one `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- one matching `boundary_source_ref`
- `effect_target_kind = applied_reviewed_memory_effect`
- `proof_capability_boundary = local_effect_presence_only`
- `proof_stage = first_presence_proved_local_only`
- one local `applied_effect_id`
- `present_locally_at`

Exact relation rules:

- the proof boundary should later materialize only from one exact matching canonical local proof record/store for the same aggregate and supporting refs
- the proof boundary should stay shared across later rollback and later disable consumption
- the proof boundary itself must not carry `rollback_contract_ref` or `disable_contract_ref`
- the current `reviewed_memory_local_effect_presence_fact_source_instance` helper should later materialize only from one exact matching local proof boundary for the same aggregate and supporting refs
- the current `reviewed_memory_local_effect_presence_fact_source` helper should later materialize only from one exact matching fact-source-instance helper result for the same aggregate and supporting refs
- the current raw-event helper should later materialize only from one exact matching fact-source helper result for the same aggregate and supporting refs
- the current producer helper should later materialize only from one exact matching raw-event helper result for the same aggregate and supporting refs
- the current event-source helper should later materialize only from one exact matching producer-helper result for the same aggregate and supporting refs
- the current source-consumer helper should later materialize only from one exact matching event-source helper result for the same aggregate and supporting refs
- the current target helper should later materialize only from one exact matching source-consumer helper result for the same aggregate and supporting refs

Local identity and timestamp rules:

- do not add a second proof id in the first contract
- reuse `applied_effect_id` as the first local identity minted exactly at the smaller truthful canonical proof-record instant and reused unchanged at the truthful proof-boundary instant
- `present_locally_at` must be that same first truthful canonical local instant reused at the proof-boundary layer
- `aggregate.last_seen_at` may be reused only when it is exactly that same first truthful local instant, not as a generic fallback

Why this proof boundary is the truthful minimum:

- it is smaller than fact-source-instance helper materialization, fact-source helper materialization, raw-event helper materialization, producer-helper materialization, event-source helper materialization, source-consumer helper materialization, target helper materialization, handle helper materialization, source-family resolution, basis materialization, and any payload-visible readiness or apply layer
- it captures only one first local proof boundary for effect presence, not rollback capability, disable capability, emitted record, or apply result
- it preserves the later shared-target-plus-separate-handle design without inventing current capability state

### 3. Relationship To The Current Fact-Source-Instance Helper

Current `reviewed_memory_local_effect_presence_fact_source_instance` helper now materializes because:

- it validates the same exact aggregate identity, exact supporting refs, current resolved `boundary_source_ref`, and the aggregate's exact `first_seen_at` anchor
- the exact later local proof boundary beneath it is now fixed, and current implementation now also has one truthful same-aggregate canonical local proof record/store entry that first carries `applied_effect_id` and `present_locally_at` for the current exact aggregate state
- therefore the fact-source-instance helper can now reopen as one smaller internal result without widening the fact-source helper, raw-event helper, basis, or UI readiness

Now that the proof boundary and fact-source-instance exist:

- the fact-source-instance helper may later materialize one exact local fact-source instance from that proof boundary only
- the helper should preserve the same exact `aggregate_identity_ref`, supporting refs, `boundary_source_ref`, `applied_effect_id`, and `present_locally_at`

Keep the layers separate:

- local proof boundary != fact-source-instance helper
- fact-source-instance helper != fact-source helper
- fact-source helper != raw-event helper
- raw-event helper != producer helper
- producer helper != event-source helper
- event-source helper != source-consumer helper
- source-consumer helper != target helper
- target helper != handle helper
- handle helper != `rollback_source_ref`

The honest sequencing is:

- current round: proof-boundary contract is fixed and one internal proof-boundary helper now materializes one truthful same-aggregate result
- current round: fact-source-instance helper now materializes one internal same-aggregate result
- current round: fact-source helper exists but remains absent
- current round: raw-event helper exists but remains absent
- current round: producer helper exists but remains absent
- current round: event-source helper exists but remains absent
- current round: source-consumer helper exists but remains absent
- current round: target helper exists but remains absent
- current round: handle helper exists but remains unresolved
- current implementation round: one truthful same-aggregate canonical local proof-record writer now mints one exact payload-hidden store entry beneath the current proof-boundary helper
- current implementation round: one truthful same-aggregate local proof boundary now materializes inside that helper above that canonical local proof record/store
- current implementation round: fact-source-instance helper now materializes above that proof boundary
- later adjacent rounds: fact-source helper, raw-event helper, producer helper, event-source helper, source-consumer helper, target helper, and then handle helper may reopen in order

The honest implementation sequencing should stay separate:

- local proof-boundary contract round = already completed
- first proof-boundary helper round = current implementation round
- truthful canonical proof-record round = current implementation round
- truthful proof-boundary materialization round = current implementation round
- fact-source-instance helper materialization round = current implementation round

### 4. Relationship To Rollback And Disable Contracts

Keep current shipped contract-only layers unchanged:

- `reviewed_memory_rollback_contract`
  - still contract-only
  - still rollback target-kind draft only
- `reviewed_memory_disable_contract`
  - still contract-only
  - still stop-apply target-kind draft only

The future local proof boundary should stay shared, not rollback-first.

Why shared boundary is the honest choice:

- both shipped contracts already narrow to `future_applied_reviewed_memory_effect_only`
- the proof boundary describes only the first local applied-effect-presence proof, not rollback or disable capability
- rollback and later disable should stay separate capabilities on separate later handles
- a rollback-first proof boundary would overstate current capability meaning before any later handle exists

### 5. Relationship To Current Trigger / Audit / Emission Layers

Keep twenty-six layers separate:

1. rollback / disable contracts exist
2. `rollback_source_ref` is exact-scope-validated but unresolved
3. `reviewed_memory_local_effect_presence_proof_boundary` helper materializes one internal same-aggregate result
4. `reviewed_memory_local_effect_presence_fact_source_instance` helper materializes one internal same-aggregate result
5. `reviewed_memory_local_effect_presence_fact_source` helper exists but absent
6. `reviewed_memory_local_effect_presence_event` helper exists but absent
7. `reviewed_memory_local_effect_presence_event_producer` helper exists but absent
8. `reviewed_memory_local_effect_presence_event_source` helper exists but absent
9. `reviewed_memory_local_effect_presence_record` helper exists but absent
10. `reviewed_memory_applied_effect_target` helper exists but absent
11. `reviewed_memory_reversible_effect_handle` helper exists but unresolved
12. exact canonical local proof record exists
13. proof-boundary helper materializes
14. fact-source-instance helper materializes
15. fact-source helper materializes
16. raw-event helper materializes
17. producer helper materializes
18. event-source helper materializes
19. source-consumer helper materializes
20. target helper materializes
21. handle helper can truthfully point to that target
22. full source family resolves
23. `reviewed_memory_capability_basis` materializes
24. `capability_outcome = unblocked_all_required`
25. transition record emitted
26. reviewed-memory apply result

Why this matters:

- contract != unresolved resolver
- unresolved resolver != proof-boundary helper
- proof-boundary helper != canonical local proof record
- canonical local proof record != fact-source-instance helper materialization
- fact-source-instance helper != fact-source helper materialization
- fact-source helper != raw-event helper
- raw-event helper != producer helper
- producer helper != event-source helper
- event-source helper != source-consumer helper
- source-consumer helper != target helper
- target helper != basis object
- basis object != emitted record
- emitted record != apply result

### 6. Support / Mirror Boundary

Never treat these as local proof boundary:

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
- future local proof boundary opening alone must not enable the card
- no note input
- no `canonical_transition_id`
- no `operator_reason_or_note`
- no `emitted_at`
- no emitted record

### 8. Cross-Session Boundary

Even after a truthful same-session local proof boundary exists, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules across session reloads
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session exact aggregate remains the honest boundary.

## Recommended Next Slice

- one truthful same-aggregate local event-producer materialization only

That slice should:

- consume the existing exact same-aggregate fact-source helper result that already sits above the current `reviewed_memory_local_effect_presence_fact_source_instance` helper and the current `reviewed_memory_local_effect_presence_proof_boundary` helper
- keep the aggregate's exact `first_seen_at` as a necessary anchor only, not a sufficient canonical proof record by itself
- keep the current fact-source-instance helper materialized in the same round
- keep the current fact-source helper materialized in the same round
- keep the current producer helper absent in the same round
- keep the current event-source helper absent in the same round
- keep the current source-consumer helper absent in the same round
- keep the current target helper absent in the same round
- keep the current handle helper unresolved in the same round

Why this is the smallest honest next step:

- current repo already has the proof-record writer, the payload-hidden canonical store entry, the proof-boundary helper, and the higher helper chain above it
- the next missing piece is the exact local event result that still cannot materialize above that truthful fact-source layer
- reopening only that local event result is smaller than producer-helper materialization, event-source helper materialization, target materialization, basis object emission, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result, repeated-signal promotion, and cross-session counting
- keep `reviewed_memory_capability_basis` absent in the same round
- keep `reviewed_memory_capability_status.capability_outcome = blocked_all_required` in the same round
- keep the existing blocked aggregate-card affordance unchanged in the same round
- open no note input, `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, emitted transition record, or reviewed-memory apply result

## Open Questions

1. Now that the exact payload-hidden canonical local proof-record/store entry exists, should the current `reviewed_memory_local_effect_presence_proof_boundary` helper consume only session-persisted entries or also tolerate one later separate reviewed-memory local store that remains same-session-scoped?
2. After the first truthful fact-source-instance result landed, should the fact-source helper consume it in the same adjacent round or stay absent for one verification round first?
