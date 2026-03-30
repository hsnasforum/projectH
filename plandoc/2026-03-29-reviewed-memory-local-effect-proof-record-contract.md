# 2026-03-29 Reviewed-Memory Local-Effect Proof-Record Contract

## Goal

Fix the first exact truthful contract for the canonical local proof record/store beneath the current internal `reviewed_memory_local_effect_presence_proof_boundary` helper.

This canonical proof-record layer sits:

- below the current internal `reviewed_memory_local_effect_presence_proof_boundary` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_fact_source_instance` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_fact_source` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_event` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_event_producer` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_event_source` helper that still resolves no result
- below the current internal `reviewed_memory_local_effect_presence_record` helper that still resolves no result
- below the current internal `reviewed_memory_applied_effect_target` helper that still resolves no result
- below the current internal `reviewed_memory_reversible_effect_handle` helper that still resolves no result
- well below the future full internal `reviewed_memory_capability_source_refs` family, any later `reviewed_memory_capability_basis`, any later `unblocked_all_required`, any emitted `reviewed_memory_transition_record`, any reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory

This document does not describe proof-boundary helper materialization, fact-source-instance helper materialization, fact-source helper materialization, raw-event helper materialization, producer-helper materialization, event-source helper materialization, source-consumer helper materialization, target helper materialization, handle helper materialization, enabled submit UI, note input, emitted transition-record materialization, reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory.

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
  - one internal `reviewed_memory_local_effect_presence_proof_record` helper is now also evaluated for that same exact aggregate, and current implementation now also truthfully mints one exact payload-hidden canonical local proof-record/store entry for the current exact aggregate state inside the same-session `reviewed_memory_local_effect_presence_proof_record_store` boundary; that helper still keeps `first_seen_at` alone, source-message review acceptance, review-queue presence, approval-backed save support, historical adjuncts, and `task_log` replay outside that lower proof-record layer
  - one internal `reviewed_memory_local_effect_presence_proof_boundary` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate proof boundary above that canonical local proof record/store entry while reusing the same `applied_effect_id` and `present_locally_at`; it still requires the aggregate's exact `first_seen_at` anchor before any later higher proof can mint `present_locally_at`
  - one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper is now also evaluated for that same exact aggregate, and it now materializes one internal same-aggregate fact-source-instance result only from that exact proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`
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

### 1. Exact Meaning Of The Canonical Local Proof Record

Future truthful canonical local proof record means:

- one exact local internal record/store entry that can first justify one same-aggregate `applied_effect_id` plus one same-instant `present_locally_at` for `same_session_exact_recurrence_aggregate_only`
- one record that the current `reviewed_memory_local_effect_presence_proof_boundary` helper can materialize from without implying fact-source-instance helper materialization, higher helper materialization, emitted record, or reviewed-memory apply result
- one record that remains smaller than `reviewed_memory_local_effect_presence_proof_boundary`, `reviewed_memory_local_effect_presence_fact_source_instance`, `reviewed_memory_local_effect_presence_fact_source`, `reviewed_memory_local_effect_presence_event`, `reviewed_memory_local_effect_presence_event_producer`, `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, the full `reviewed_memory_capability_source_refs` family, `reviewed_memory_capability_basis`, `unblocked_all_required`, emitted transition record, reviewed-memory apply result, repeated-signal promotion, or user-level memory

It does not mean:

- current `reviewed_memory_rollback_contract` alone
- current `reviewed_memory_disable_contract` alone
- current `reviewed_memory_local_effect_presence_proof_boundary` helper alone
- current exact `first_seen_at` anchor alone
- current blocked aggregate trigger affordance
- `candidate_review_record`
- `review_queue_items`
- approval-backed save support
- historical adjunct
- `task_log` replay
- emitted transition record
- reviewed-memory apply result

Keep the meaning chain exact:

- contract exists != canonical local proof record exists
- helper exists != canonical local proof record exists
- `first_seen_at` exists != canonical local proof record exists
- canonical local proof record exists != proof-boundary helper already materialized
- proof-boundary helper materialized != fact-source-instance helper materialized
- fact-source-instance helper materialized != fact-source helper materialized
- fact-source helper materialized != raw-event helper materialized
- raw-event helper materialized != producer helper materialized
- producer helper materialized != event-source helper materialized
- event-source helper materialized != source-consumer helper materialized
- source-consumer helper materialized != target helper materialized
- target helper materialized != basis object
- basis object != `unblocked_all_required`
- `unblocked_all_required` != emitted record

### 2. Exact Canonical Local Proof-Record Shape

The exact later canonical local proof record should stay one internal `reviewed_memory_local_effect_presence_proof_record`.

Minimum truthful shape:

- `proof_record_version = first_same_session_reviewed_memory_local_effect_presence_proof_record_v1`
- `proof_record_scope = same_session_exact_recurrence_aggregate_only`
- one `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- one matching `boundary_source_ref`
- `effect_target_kind = applied_reviewed_memory_effect`
- `proof_capability_boundary = local_effect_presence_only`
- `proof_record_stage = canonical_presence_recorded_local_only`
- one local `applied_effect_id`
- `present_locally_at`

Exact relation rules:

- the current `reviewed_memory_local_effect_presence_proof_boundary` helper should later materialize only from one exact matching canonical local proof record for the same aggregate and supporting refs
- the proof record should stay shared across later rollback and later disable consumption
- the proof record itself must not carry `rollback_contract_ref` or `disable_contract_ref`
- the current proof-boundary helper remains above that record
- the current fact-source-instance helper remains above the proof-boundary helper
- the current fact-source helper remains above the fact-source-instance helper
- the current raw-event helper remains above the fact-source helper
- the current producer helper remains above the raw-event helper
- the current event-source helper remains above the producer helper
- the current source-consumer helper remains above the event-source helper
- the current target helper remains above the source-consumer helper

Local identity and deterministic timestamp rules:

- do not add a second proof id in the first contract
- reuse `applied_effect_id` as the first local identity minted exactly at the truthful canonical proof-record instant
- `present_locally_at` must be that same first truthful canonical local instant
- do not add a second `recorded_at` field in the first contract; the record should stay one-id-plus-one-instant minimal
- `aggregate.last_seen_at` may be reused only when it is exactly that same first truthful canonical local instant, not as a generic fallback
- `first_seen_at` must already exist before any canonical local proof record may materialize, but `first_seen_at` alone must not become the record
- equality `present_locally_at == first_seen_at` is truthful only when the record is actually minted at that exact instant, not when the anchor is promoted without a separate record

Canonical store boundary rule:

- the record must live only inside one internal same-session `reviewed_memory_local_effect_presence_proof_record_store` boundary, not inside aggregate payload fields
- that store boundary must remain distinct from `task_log`, approval/save support traces, review-queue traces, emitted transition records, and reviewed-memory apply result
- the store key must stay same-session-only and exact-aggregate-scoped through `aggregate_identity_ref`, exact supporting refs, the matching `boundary_source_ref`, and the minted `applied_effect_id`

### 3. Relationship To The Current Proof-Boundary Helper

Current `reviewed_memory_local_effect_presence_proof_boundary` helper still remains absent because:

- it already validates the same exact aggregate identity, exact supporting refs, and current resolved `boundary_source_ref`
- the aggregate's exact `first_seen_at` is now only a necessary anchor, not a sufficient proof
- current implementation now truthfully mints one exact same-aggregate canonical local proof record/store entry that first carries `applied_effect_id` and same-instant `present_locally_at` for the current exact aggregate state
- therefore the helper's remaining absence is now about proof-boundary materialization itself, not about missing lower canonical record/store entry

When the canonical proof record later exists:

- the proof-boundary helper should materialize one exact local proof-boundary result from that record only
- the helper should preserve the same exact `aggregate_identity_ref`, supporting refs, `boundary_source_ref`, `applied_effect_id`, and `present_locally_at`

Keep the layers separate:

- canonical local proof record != proof-boundary helper
- `first_seen_at` != canonical local proof record
- proof-boundary helper != fact-source-instance helper
- fact-source-instance helper != fact-source helper
- fact-source helper != raw-event helper
- raw-event helper != producer helper
- producer helper != event-source helper
- event-source helper != source-consumer helper
- source-consumer helper != target helper
- target helper != handle helper
- handle helper != `rollback_source_ref`

The honest implementation sequencing should stay separate:

- current implementation round: proof-record helper can now materialize only from one exact same-session internal `reviewed_memory_local_effect_presence_proof_record_store` entry, and current implementation now also mints one exact payload-hidden same-aggregate entry for the current exact aggregate state inside that boundary
- current implementation round: proof-boundary helper now materializes one truthful same-aggregate result
- current round: fact-source-instance helper now materializes one truthful same-aggregate result
- current round: fact-source helper exists but remains absent
- current round: raw-event helper exists but remains absent
- current round: producer helper exists but remains absent
- current round: event-source helper exists but remains absent
- current round: source-consumer helper exists but remains absent
- current round: target helper exists but remains absent
- current round: handle helper exists but remains unresolved
- next implementation round: one truthful same-aggregate fact-source result may materialize from that existing fact-source-instance layer only
- later adjacent rounds: raw-event helper, producer helper, event-source helper, source-consumer helper, target helper, and then handle helper may reopen in order

### 4. Relationship To Rollback And Disable Contracts

Keep current shipped contract-only layers unchanged:

- `reviewed_memory_rollback_contract`
  - still contract-only
  - still rollback target-kind draft only
- `reviewed_memory_disable_contract`
  - still contract-only
  - still stop-apply target-kind draft only

The future canonical local proof record should stay shared, not rollback-first.

Why shared lower record is the honest choice:

- both shipped contracts already narrow to `future_applied_reviewed_memory_effect_only`
- the canonical record describes only the first local applied-effect-presence proof, not rollback or disable capability
- rollback and later disable should stay separate capabilities on separate later handles
- a rollback-first lower record would overstate current capability meaning before any later handle exists

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

### 6. Support / Mirror Boundary

Never canonical local proof record:

- `candidate_review_record`
- queue presence
- approval-backed save alone
- historical adjunct alone
- `task_log` replay alone
- contract object existence alone
- `first_seen_at` alone

Keep supporting roles exact:

- approval-backed save remains supporting evidence only
- historical adjunct remains supporting context only
- review acceptance remains confidence support only
- `task_log` remains mirror / appendix only
- `first_seen_at` remains necessary anchor only

### 7. UI Boundary

- current aggregate card remains visible-but-disabled
- future canonical local proof record opening alone must not enable the card
- no note input
- no `canonical_transition_id`
- no `operator_reason_or_note`
- no `emitted_at`
- no emitted record

### 8. Cross-Session Boundary

- even after a truthful same-session canonical local proof record exists, cross-session counting still stays closed
- later cross-session widening still requires:
  - explicit local-store identity rules across session reloads
  - stale-resolution rules for reopened aggregates
  - conflict-repair rules when later proof records disagree across sessions
  - operator-visible repair semantics above cross-session scope

So same-session exact aggregate remains the honest boundary after this contract.

## Recommended Next Slice

- one truthful same-aggregate local event-producer materialization only

That slice should:

- consume the existing exact same-aggregate fact-source helper result that already sits above the current fact-source-instance helper, the current proof-boundary helper, and the payload-hidden canonical local proof-record/store entry
- keep the current fact-source-instance helper materialized in the same round
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

- current repo already has the proof-record writer, the payload-hidden canonical store entry, the proof-boundary helper, the fact-source-instance helper, and the higher helper chain above them
- the next missing piece is the exact local event result that still returns `None` above that truthful same-aggregate fact-source layer
- reopening only that local event result is smaller than producer-helper materialization, event-source helper materialization, target materialization, basis object emission, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result, repeated-signal promotion, and cross-session counting

## Open Questions

1. Should the first canonical proof-record store live in session persistence only, or in one separate reviewed-memory local store that is still session-scoped but survives shell refresh independently from aggregate serialization?
2. Now that the fact-source helper also materializes truthfully, should the raw-event helper consume that fact-source result in the very next adjacent round or stay absent for one more verification round first?
