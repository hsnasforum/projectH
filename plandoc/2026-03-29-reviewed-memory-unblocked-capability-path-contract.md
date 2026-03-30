# 2026-03-29 Reviewed-Memory Unblocked Capability-Path Contract

## Goal

Fix the first exact truthful contract for a future same-session `unblocked_all_required` capability path.

This capability-path layer sits:

- above the current blocked contract chain and the already-shipped blocked trigger affordance
- below any later emitted `reviewed_memory_transition_record`
- well below any reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory

This document does not describe enabled submit UI, emitted transition record materialization, reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory.

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
- the exact later rollback-capability backer should stay one internal local `reviewed_memory_reversible_effect_handle` above the current rollback contract and below any later basis object, emitted transition record, or reviewed-memory apply result
- the remaining three refs still remain unresolved, so the full helper family still resolves no result
  - aggregate serialization may now probe one future `reviewed_memory_capability_basis`
  - current payload still emits no such object because the full matching capability-basis source family still does not exist

## Decision

### 1. Exact Meaning Of First `unblocked_all_required`

Future truthful `unblocked_all_required` means:

- one exact same-session aggregate now has all-required reviewed-memory capability basis truthfully satisfied
- the existing aggregate-card boundary may later become enableable without yet claiming emitted transition record or apply result
- this layer remains smaller than emitted transition record and reviewed-memory apply

It does not mean:

- emitted transition record already exists
- reviewed-memory apply result already exists
- user-level memory exists
- repeated-signal promotion opened
- cross-session counting opened

Keep the meaning chain exact:

- `unblocked_all_required` != emitted record
- emitted record != apply result
- apply result != user-level memory

### 2. What Counts As Truthful Capability Basis

Current shipped contract-object existence remains insufficient.

Why it is insufficient:

- the current contract chain still means only `contract exists`
- current `reviewed_memory_capability_status.capability_outcome = blocked_all_required` is the truthful emitted outcome
- approval-backed save support, historical adjuncts, source-message review acceptance, queue presence, and `task_log` replay remain outside canonical capability satisfaction

The first truthful future basis should require one separate later internal source family plus one later read-only object:

- one later internal `reviewed_memory_capability_source_refs`
  - `source_version = same_session_reviewed_memory_capability_source_refs_v1`
  - `source_scope = same_session_exact_recurrence_aggregate_only`
  - one `aggregate_identity_ref`
  - exact supporting refs
  - exact `required_preconditions`
  - one `capability_source_refs`
    - `boundary_source_ref`
    - `rollback_source_ref`
    - `disable_source_ref`
    - `conflict_source_ref`
    - `transition_audit_source_ref`
  - `source_status = all_required_sources_present`
  - `evaluated_at`
  - this source family stays internal and additive, not a payload surface

- `reviewed_memory_capability_basis`
  - `basis_version = same_session_reviewed_memory_capability_basis_v1`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - one `aggregate_identity_ref`
  - exact supporting refs
  - exact `required_preconditions`
  - `basis_status = all_required_capabilities_present`
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - `evaluated_at`

That future object may be truthful only when all five required capabilities actually exist for the same exact aggregate scope:

- `reviewed_memory_boundary_defined`
- `rollback_ready_reviewed_memory_effect`
- `disable_ready_reviewed_memory_effect`
- `conflict_visible_reviewed_memory_scope`
- `operator_auditable_reviewed_memory_transition`

Therefore:

- do not backfill `unblocked_all_required` from current contract existence
- do not backfill it from approval-backed save support
- do not backfill it from queue presence or source-message review acceptance
- do not backfill it from `task_log` replay

Future `reviewed_memory_capability_status.capability_outcome = unblocked_all_required` may become truthful only when:

- the same exact aggregate still matches the current contract chain
- the same exact aggregate also resolves one matching internal `reviewed_memory_capability_source_refs`
- the same exact aggregate also exposes one matching `reviewed_memory_capability_basis`

### 3. Relationship To The Existing Blocked Trigger Affordance

Current shipped trigger affordance remains:

- aggregate card visible
- action label `검토 메모 적용 시작`
- action disabled
- no note input
- no emitted record

Future capability-path layer remains separate from that current UI truth.

Exact later flip condition:

- the same aggregate card may flip from disabled to enabled only when:
  - `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`
  - the same exact aggregate also exposes one matching `reviewed_memory_capability_basis`

Capability-path opening alone should still remain smaller than submission:

- keep `operator_reason_or_note` hidden in the first capability-path round
- keep `canonical_transition_id` uncreated in the first capability-path round
- keep `emitted_at` uncreated in the first capability-path round
- keep `reviewed_memory_transition_record` absent in the first capability-path round

Enabled submit and emitted-record trigger should ship as adjacent later rounds, not inside the first capability-path round.

### 4. Relationship To The Current Transition-Audit Contract

Keep five layers separate:

1. `transition-audit contract exists`
2. `operator-visible trigger affordance exists`
3. `truthful unblocked capability path exists`
4. `transition record emitted`
5. `reviewed-memory apply result`

Why this matters:

- contract != trigger affordance
- trigger affordance != unblocked capability path
- unblocked capability path != emitted record
- emitted record != apply result

### 5. Review Queue Boundary

Keep current queue truth unchanged:

- `review_queue_items` remains source-message candidate review surface only
- `candidate_review_record` remains one source-message reviewed-but-not-applied trace only
- aggregate-level blocked trigger affordance remains aggregate transition-initiation boundary only
- future truthful `unblocked_all_required` remains aggregate-level capability layer only

Therefore:

- source-message `accept` must not become capability basis
- `candidate_review_record` must not become emitted-record basis
- `candidate_review_record` must not become unblocked basis by itself

### 6. Canonical Record / Note / Timestamp Boundary

Even when the capability path later opens truthfully:

- `canonical_transition_id` is still not created there
- `operator_reason_or_note` is still not collected there
- `emitted_at` is still not created there

Why this remains smaller than emitted transition record:

- capability-path opening only says the aggregate is now truthfully ready for a later operator-visible transition boundary
- transition identity, note collection, and emission timestamp belong to the later emitted-record submission boundary

So:

- capability-path opening alone must not mint transition identity
- capability-path opening alone must not mint emitted timestamp
- capability-path opening alone must not require `task_log` mirror

### 7. Support / Mirror Boundary

Never treat these as truthful unblocked basis:

- `candidate_review_record`
- queue presence
- approval-backed save alone
- historical adjunct alone
- `task_log` replay alone
- contract object existence alone

Therefore:

- approval-backed save remains supporting evidence only
- historical adjunct remains supporting context only
- source-message review acceptance remains confidence support only
- `task_log` remains mirror / appendix only

### 8. Cross-Session Boundary

Even after a truthful same-session `unblocked_all_required` path exists, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules across session reloads
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session exact aggregate remains the honest boundary.

## Recommended Next Slice

- one truthful same-aggregate local `disable_source_ref` materialization only

That slice should:

- consume the existing exact same-aggregate shared target plus the current exact `reviewed_memory_disable_contract` before reopening any unblocked-capability-path materialization
- reopen only one truthful same-aggregate disable-side source in the same round
- keep `reviewed_memory_capability_basis` absent until a later adjacent round materializes it from that same exact source family
- keep `reviewed_memory_capability_status.capability_outcome = blocked_all_required` until that later matching basis object exists
- keep the existing blocked aggregate-card affordance unchanged in the same round
- open no note input, `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, or emitted transition record

Why this is the smallest honest next step:

- current repo still has no truthful `unblocked_all_required` path
- the internal helper family, the payload-hidden proof-record writer, the proof-boundary helper, the fact-source-instance helper, the fact-source helper, the raw-event helper, the producer helper, the event-source helper, the source-consumer helper, the target helper, the rollback-side handle helper, and one resolved internal `rollback_source_ref` already exist, so the next missing piece is the exact local disable-side source that still cannot materialize above the current `reviewed_memory_disable_contract`
- it stays smaller than emitted transition record, reviewed-memory apply result, repeated-signal promotion, and cross-session counting

## Open Questions

1. After the capability basis becomes truthful, should the first enabled aggregate-card UI round keep the button-only affordance or ship together with the first inline note field?
