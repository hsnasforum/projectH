# 2026-03-29 Reviewed-Memory Apply Trigger-Source Contract

## Goal

Fix the first exact operator-visible trigger-source contract for future `future_reviewed_memory_apply`.

This contract sits:

- above the current same-session `recurrence_aggregate_candidates` and their shipped reviewed-memory contract chain
- below the later canonical `reviewed_memory_transition_record`
- well below any later reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory

This document does not describe reviewed-memory store writes, reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory.

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
  - earlier duplicated target echo fields are no longer current schema
- current shipped transition-audit contract remains contract-only:
  - `audit_version = first_reviewed_memory_transition_identity_v1`
  - `transition_action_vocabulary` already includes `future_reviewed_memory_apply`
  - `transition_identity_requirement = canonical_local_transition_id_required`
  - `operator_visible_reason_boundary = explicit_reason_or_note_required`
  - `audit_stage = contract_only_not_emitted`
  - `audit_store_boundary = canonical_transition_record_separate_from_task_log`
- current emitted-record truth remains:
  - aggregate serialization now probes a future `reviewed_memory_transition_record` layer
  - current payload still emits no such object
  - current implementation preserves that absence
- current same-session capability truth remains:
  - `reviewed_memory_unblock_contract.unblock_status = blocked_all_required`
  - `reviewed_memory_capability_status.capability_outcome = blocked_all_required`
- current shell truth remains:
  - one source-message `검토 후보` section fed only by `review_queue_items`
  - that surface records only source-message `candidate_review_record` through `accept`
  - one separate aggregate-level `검토 메모 적용 후보` section now appears only when `recurrence_aggregate_candidates` exist
  - that aggregate surface stays adjacent to `검토 후보`, shows one disabled `검토 메모 적용 시작` control per aggregate card, and remains blocked-only

## Decision

### 1. Where The First Trigger Source Lives

Choose `Option A`.

The first operator-visible `future_reviewed_memory_apply` trigger source lives on one separate aggregate-level surface fed only by `recurrence_aggregate_candidates`.

It does not live on:

- source-message response cards
- `review_queue_items`
- the current `검토 후보` section
- source-message `candidate_review_record`

The smallest future shell placement is:

- one separate aggregate section inside the existing session stack
- placed adjacent to but separate from `검토 후보`
- specifically, one new aggregate card list directly below `검토 후보` and above the transcript
- no modal
- no new dashboard
- no new workspace

Why `Option A` is the honest current-MVP choice:

- `future_reviewed_memory_apply` is scoped to one exact same-session recurrence aggregate, not to one source-message candidate
- current `review_queue_items` is already a source-message candidate review surface and should stay that way
- placing the trigger source inside `review_queue_items` would blur source-message review with aggregate-level reviewed-memory transition
- current shell truth already lacks any aggregate-level control surface, so adding one small separate aggregate surface is cleaner than overloading the existing queue

### 2. Hidden Vs Disabled While Blocked

Choose `operator-visible but disabled`.

When the future aggregate surface exists and the aggregate is still blocked:

- the aggregate card should remain visible
- the action should remain visible
- the action should remain disabled
- the card should keep showing the current blocked truth from:
  - `reviewed_memory_capability_status.capability_outcome = blocked_all_required`
  - `reviewed_memory_transition_audit_contract.audit_stage = contract_only_not_emitted`

The disabled state must not:

- render an active note form
- mint a `canonical_transition_id`
- mint an `emitted_at`
- imply `unblocked_all_required`
- imply emitted transition record existence

Why disabled is more honest than hidden:

- hidden would collapse “no aggregate-level trigger surface rendered yet” and “aggregate is still blocked” into the same absence
- a visible disabled affordance teaches the operator that this boundary belongs to the aggregate layer, not to `review_queue_items`
- the disabled state can stay explicit about `blocked_all_required` without pretending the repo is more ready than it is

### 3. Exact Meaning Of The Trigger Source

The trigger source means:

- one later operator-visible initiation boundary for `future_reviewed_memory_apply`
- one initiation boundary tied to one exact same-session recurrence aggregate
- one boundary where later canonical transition identity, explicit operator note, and local emission time can be created honestly
- one layer between the shipped transition-audit contract and the later emitted transition record

It does not mean:

- `reviewed_memory_transition_record` already emitted
- reviewed-memory apply result
- repeated-signal promotion
- cross-session counting
- user-level memory
- `review_queue_items` accept action
- `candidate_review_record`

Keep the meaning chain exact:

- trigger source != emitted record
- emitted record != apply result
- review accept != reviewed-memory apply trigger

### 4. Minimum Future UX And Payload Boundary

The smallest future trigger-source shape is:

- aggregate-level, not source-message-level
- one separate existing-shell aggregate card list fed only by `session.recurrence_aggregate_candidates`
- one control row on each aggregate card for the later `future_reviewed_memory_apply` path

Exact operator-visible action label:

- `검토 메모 적용 시작`

Blocked state contract:

- show the aggregate card
- show the `검토 메모 적용 시작` control as disabled
- show helper text from the current blocked contract chain:
  - blocked because capability outcome is still `blocked_all_required`
  - transition audit is still `contract_only_not_emitted`
- do not show the `operator_reason_or_note` input yet

Future unblocked state contract:

- keep the same aggregate card
- keep the same action label `검토 메모 적용 시작`
- reveal one required inline `operator_reason_or_note` input on that same card
- keep submission inside the same card
- do not require a modal or separate workspace

Exact creation boundary:

- `operator_reason_or_note` is collected only from that inline aggregate-card submission
- `canonical_transition_id` is created only when the operator submits that enabled aggregate-card action with a non-empty note
- `emitted_at` is created only at that same local submission boundary
- aggregate serialization, `review_queue_items` accept, approval-backed save, historical adjuncts, and `task_log` replay must not pre-create those values

### 5. Relationship To The Current Transition-Audit Contract

Keep four layers separate:

1. `transition-audit contract exists`
   - current shipped vocabulary and identity boundary only
2. `operator-visible trigger-source layer exists`
   - one aggregate-level card surface exists, possibly disabled while blocked
3. `transition record emitted`
   - one later canonical local record exists for one exact aggregate
4. `reviewed-memory apply result`
   - one later effect result above the emitted record

Why the audit contract must stay separate:

- the shipped audit contract still truthfully describes current payload behavior
- the future trigger-source layer consumes that contract but does not overwrite it
- later emitted records satisfy the audit boundary; they do not replace the contract itself
- apply result remains later effect machinery and must not collapse into either the trigger-source layer or the emitted record

### 6. Canonical Record Vs `task_log` Mirror

Keep the boundary exact:

- trigger-source layer is not `task_log`
- canonical emitted transition record is not `task_log`
- `task_log` may later mirror the action as append-only evidence or appendix
- `task_log` replay alone must never define current trigger or emission state
- first trigger-source implementation round may keep `task_log` mirroring optional

Therefore:

- `task_log` is evidence / appendix only
- `task_log` is not the canonical state source
- canonical transition identity still belongs to the separate reviewed-memory transition layer

### 7. Review Queue Boundary

Keep current queue truth unchanged:

- `review_queue_items` remains source-message candidate review surface only
- `candidate_review_record` remains one source-message reviewed-but-not-applied trace only
- `candidate_review_record` may later appear only as optional aggregate `supporting_review_refs`
- `accept` must not be reinterpreted as reviewed-memory apply trigger
- `candidate_review_record` must not become emitted-transition-record basis

Therefore:

- source-message candidate review stays source-message-scoped
- aggregate-level reviewed-memory transition initiation stays aggregate-scoped

### 8. Current Absence Policy

Fixing this trigger-source contract does not change current payload truth.

Current payload still emits no `reviewed_memory_transition_record`.

Current absence means:

- no truthful operator-visible `future_reviewed_memory_apply` emission has happened yet

It does not mean:

- missing trigger-source contract
- missing transition-audit contract
- missing emitted-record shape
- opened reviewed-memory apply

Even after the future disabled aggregate affordance later ships:

- blocked disabled visibility alone still must not emit a transition record

### 9. Cross-Session Boundary

Even after the trigger-source layer exists, cross-session counting stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules
- conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session exact aggregate remains the honest boundary for the trigger-source layer.

## Current Implementation Status

- one separate aggregate-level blocked-but-visible disabled trigger affordance is now implemented
- the existing shell now adds one aggregate section below `검토 후보`, fed only by `recurrence_aggregate_candidates`
- each aggregate card renders one disabled `검토 메모 적용 시작` control and blocked helper text using current `blocked_all_required` / `contract_only_not_emitted` truth
- the shipped surface keeps `operator_reason_or_note` input hidden while blocked
- the shipped surface emits no `reviewed_memory_transition_record`
- the shipped surface keeps `review_queue_items` and `candidate_review_record` semantics unchanged

## Recommended Next Slice

- one truthful `unblocked_all_required` capability path only

That slice should:

- keep the shipped aggregate section and disabled `검토 메모 적용 시작` control exactly where they already are
- open no note input, `canonical_transition_id`, `emitted_at`, or emitted transition record in the same round
- define the smallest truthful basis that can later flip `reviewed_memory_capability_status.capability_outcome` from `blocked_all_required` to `unblocked_all_required`
- keep `review_queue_items` and `candidate_review_record` semantics unchanged while that capability layer is defined

Why this is the smallest honest next step:

- current repo still has no truthful `unblocked_all_required` path
- the blocked-but-visible separate affordance already establishes the aggregate-level boundary without confusing it with source-message review
- enabling the trigger before the capability layer would still overstate readiness
- it stays smaller than emitted-record materialization, reviewed-memory apply result, repeated-signal promotion, and cross-session counting

## Open Questions

1. After the blocked-but-visible aggregate affordance lands, should the first enabled submission and the first emitted transition record ship together in one round or as two adjacent rounds?
2. For later non-apply actions, should the same card shape be reused unchanged or need action-specific extensions?
