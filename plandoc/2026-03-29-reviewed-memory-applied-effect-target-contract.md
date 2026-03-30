# 2026-03-29 Reviewed-Memory Applied-Effect Target Contract

## Goal

Fix the first exact truthful contract for the later local applied reviewed-memory effect target that the current internal `reviewed_memory_reversible_effect_handle` should eventually point to.

This target layer sits:

- above the current read-only `reviewed_memory_rollback_contract` and `reviewed_memory_disable_contract`
- above the current exact-scope-validated but unresolved `rollback_source_ref`
- above the current internal `reviewed_memory_reversible_effect_handle` helper only as the later local target it must reference
- below the future full internal `reviewed_memory_capability_source_refs` family
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
  - `boundary_source_ref` now resolves for the same exact aggregate against the blocked trigger affordance
  - `rollback_source_ref` is exact-scope-validated against the same exact aggregate, exact supporting refs, and current `reviewed_memory_rollback_contract`, and it now resolves one exact ref only to the same exact rollback-side handle materialized for that aggregate
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

### 1. Exact Meaning Of The Applied Reviewed-Memory Effect Target

Future truthful applied reviewed-memory effect target means:

- one later local target that exists only after one reviewed-memory effect becomes locally present for one exact `same_session_exact_recurrence_aggregate_only`
- one target that the current internal `reviewed_memory_reversible_effect_handle` can point to without implying emitted transition record or reviewed-memory apply result is already shipped
- one target that remains smaller than the full source family, `reviewed_memory_capability_basis`, `unblocked_all_required`, emitted transition record, reviewed-memory apply result, repeated-signal promotion, or user-level memory

It does not mean:

- current `reviewed_memory_rollback_contract` alone
- current `reviewed_memory_disable_contract` alone
- current `reviewed_memory_reversible_effect_handle` helper alone
- current blocked aggregate trigger affordance
- emitted transition record
- reviewed-memory apply result
- `task_log` replay

Keep the meaning chain exact:

- rollback contract exists != applied-effect target exists
- handle helper exists != applied-effect target exists
- applied-effect target exists != full source family resolved
- full source family resolved != basis object emitted
- basis object emitted != `unblocked_all_required`
- `unblocked_all_required` != emitted record

### 2. Exact Target Shape

The exact later local target should stay one shared internal `reviewed_memory_applied_effect_target`.

Minimum truthful shape:

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
- the exact later local proof boundary beneath the current fact-source-instance helper is now fixed separately as one shared internal `reviewed_memory_local_effect_presence_proof_boundary`
- the exact later local fact source beneath that raw helper is now fixed separately as one shared internal `reviewed_memory_local_effect_presence_fact_source`
- the exact later local effect-presence event above that fact source and beneath that producer helper should stay one shared internal `reviewed_memory_local_effect_presence_event`
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
- the exact local effect-presence event source above that producer-helper result and beneath that target should stay one shared internal `reviewed_memory_local_effect_presence_event_source`
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

Exact relation rules:

- the target itself must not carry `rollback_contract_ref`
- the current rollback handle must later bind this shared target back to one matching `rollback_contract_ref`
- a later disable-side handle may reuse this same target through one separate matching `disable_contract_ref`
- the current source-consumer helper `reviewed_memory_local_effect_presence_record` should later materialize only from one exact matching `reviewed_memory_local_effect_presence_event_source`
- the current target helper now materializes only from that exact matching source-consumer helper result
- deterministic timestamp rule should stay one local `present_locally_at`; if the first truthful scaffold has no finer-grained local time, it may reuse `aggregate.last_seen_at` only when that value is exactly the first local target-presence instant

Why this exact shared target is the truthful minimum:

- both shipped contracts already point at `future_applied_reviewed_memory_effect_only`
- the shared target keeps rollback and disable semantics separate while avoiding two fake target families for the same later local effect presence
- it stays smaller than capability-source resolution, basis materialization, or any emitted transition layer

### 3. Relationship To The Current Handle Helper

Current `reviewed_memory_reversible_effect_handle` helper now materializes because:

- it validates the same exact aggregate, exact supporting refs, current resolved `boundary_source_ref`, and current `reviewed_memory_rollback_contract`
- current repo now also materializes one exact same-aggregate shared target beneath that handle
- the handle can therefore point to that target while separately keeping one matching `rollback_contract_ref`

Keep the layers separate:

- handle helper != target
- target != `rollback_source_ref`
- `rollback_source_ref` != basis object
- basis object != emitted record

The honest sequencing is:

- current round: handle helper now materializes
- current round: producer helper exists and now materializes
- current round: event-source helper exists and now materializes
- current round: source-consumer helper now materializes
- current round: target helper now materializes
- current implementation round: one internal same-aggregate canonical local proof-record scaffold now exists beneath the current proof-boundary helper
- current implementation round: one truthful same-aggregate local proof boundary now materializes inside the current proof-boundary helper above that canonical local proof record/store
- current implementation round: one shared source-consumer helper now materializes above that event-source layer only
- current implementation round: one shared `reviewed_memory_applied_effect_target` now materializes from that source
- current round: `rollback_source_ref` now resolves only as one exact ref to that same handle

### 4. Relationship To Rollback And Disable Contracts

Keep current shipped contract-only layers unchanged:

- `reviewed_memory_rollback_contract`
  - still contract-only
  - still rollback target-kind draft only
- `reviewed_memory_disable_contract`
  - still contract-only
  - still stop-apply target-kind draft only

The future applied-effect target should stay shared across those two later handles.

Why shared reuse is the honest choice:

- both contracts already narrow to the same later applied reviewed-memory effect boundary
- rollback and disable remain different capabilities that should live on different later handles
- duplicating the target would overstate current readiness and create fake divergence before any applied effect exists

### 5. Relationship To Current Trigger / Audit / Emission Layers

Keep ten layers separate:

1. `reviewed_memory_rollback_contract` exists
2. `rollback_source_ref` resolves one exact ref to that same handle only
3. `reviewed_memory_reversible_effect_handle` helper exists
4. real later local applied-effect target exists
5. handle can truthfully point to that target
6. full source family resolves
7. `reviewed_memory_capability_basis` materializes
8. `capability_outcome = unblocked_all_required`
9. transition record emitted
10. reviewed-memory apply result

Why this matters:

- contract != unresolved resolver
- unresolved resolver != handle helper result
- handle helper result != applied-effect target
- applied-effect target != basis object
- basis object != emitted record
- emitted record != apply result

### 6. Support / Mirror Boundary

Never treat these as applied-effect target basis:

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
- future applied-effect target opening alone must not enable the card
- no note input
- no `canonical_transition_id`
- no `operator_reason_or_note`
- no `emitted_at`
- no emitted record

### 8. Cross-Session Boundary

Even after a truthful same-session applied-effect target exists, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules across session reloads
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session exact aggregate remains the honest boundary.

## Recommended Next Slice

- one truthful same-aggregate local `disable_source_ref` materialization only

That slice should:

- consume the existing exact same-aggregate shared target and the current exact `reviewed_memory_disable_contract` before reopening any full source-family materialization
- reopen only one truthful same-aggregate disable-side source in the same round
- keep `reviewed_memory_capability_basis` absent in the same round
- keep `reviewed_memory_capability_status.capability_outcome = blocked_all_required` in the same round
- keep the existing blocked aggregate-card affordance unchanged in the same round
- open no note input, `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, emitted transition record, or reviewed-memory apply result

Why this is the smallest honest next step:

- current repo already has the payload-hidden proof-record writer, the proof-boundary helper, the internal fact-source-instance helper, the internal fact-source helper, the internal raw-event helper, the internal producer helper, the internal event-source helper, the internal source-consumer helper, the internal target helper, the internal handle helper, and one resolved internal `rollback_source_ref`
- the next missing piece is the first truthful same-aggregate disable-side source that can sit above the current `reviewed_memory_disable_contract` without widening into the full source family
- it stays smaller than basis object materialization, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result, repeated-signal promotion, and cross-session counting

## Open Questions

1. Should the first truthful disable-side source round reuse the existing shared target immediately, or land one extra verification pass before `disable_source_ref` starts consuming it?
