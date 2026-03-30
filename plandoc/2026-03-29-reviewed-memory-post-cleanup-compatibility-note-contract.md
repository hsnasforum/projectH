# 2026-03-29 Reviewed-Memory Post-Cleanup Compatibility-Note Contract

## Goal

Fix the first exact contract for whether any short compatibility note should remain after the shared-ref-only planning-target cleanup has already shipped.

This document does not describe reviewed-memory store, reviewed-memory apply, emitted transition records, repeated-signal promotion, cross-session counting, or user-level memory.

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
- current shipped shared ref is unchanged and canonical:
  - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
  - `target_label = eligible_for_reviewed_memory_draft_planning_only`
  - `target_scope = same_session_exact_recurrence_aggregate_only`
  - `target_boundary = reviewed_memory_draft_planning_only`
  - `defined_at = aggregate.last_seen_at`
- the three duplicated planning-target echo fields are no longer current truth:
  - `reviewed_memory_precondition_status.future_transition_target`
  - `reviewed_memory_unblock_contract.readiness_target`
  - `reviewed_memory_capability_status.readiness_target`
- current payloads, tests, and root docs now read planning-target meaning only from `reviewed_memory_planning_target_ref.target_label`
- current blocked truths remain:
  - `overall_status = blocked_all_required`
  - `unblock_status = blocked_all_required`
  - `capability_outcome = blocked_all_required`
- current contract objects still mean `contract exists` only and are not satisfaction by themselves

## Decision

### 1. Drop The Compatibility Note

Choose `Option B`.

Why this is the current MVP-safe choice:

- current shared-ref-only truth is already explicit across payload, tests, and root docs
- one extra compatibility note would add operator wording without changing current behavior
- that wording would risk making removed echo fields look like fallback schema or current truth
- the cleanup implementation closeout already preserves the one necessary historical handoff context

### 2. Exact Meaning Of No Post-Cleanup Compatibility Note

No post-cleanup compatibility note means:

- there is no separate docs-only or `/work`-only aftercare layer beyond ordinary current-truth documentation
- root docs should describe only the current shared-ref-only planning-target source
- later `/work` notes may mention removed echo fields only as historical context when directly relevant to a new round

It does not mean:

- removed field reintroduction
- payload fallback
- UI fallback
- `blocked_all_required` / `unblocked_all_required` widening
- emitted transition record
- reviewed-memory apply
- repeated-signal promotion
- cross-session counting
- user-level memory

### 3. Exact Placement And Duration

The smallest honest aftercare shape is:

- no dedicated compatibility note in root spec docs
- no required extra compatibility note in the next `/work` closeout after cleanup
- no one-round operator reminder surface beyond ordinary closeout context

Define `one more operator handoff round` as:

- the first meaningful `/work` closeout after the cleanup implementation round

Chosen contract:

- zero additional compatibility-note rounds

If a later round needs historical mention:

- keep it to one short `/work` sentence only
- keep it explicitly historical
- do not restate removed field names as active schema

### 4. Relationship To Current Shared-Ref-Only Truth

Current shipped truth remains:

- `reviewed_memory_planning_target_ref` is the only canonical planning-target source
- removed echo fields are no longer part of current payload truth
- current blocked-only status, unblock contract, and capability status remain unchanged

Therefore:

- a compatibility note must not override payload truth, because no separate compatibility note remains
- historical wording must not make current schema look reverted

### 5. Minimum Future Aftercare Shape

The smallest honest future aftercare shape is:

- no compatibility note needed

Ordinary handling is enough:

- keep current truth in root docs
- keep historical context only in the relevant cleanup closeout
- let later rounds mention that history only when directly relevant

### 6. Relationship To Status / Satisfaction / Transition / Apply

Keep the layers separate:

- no compatibility note != `blocked_all_required`
- no compatibility note != `unblocked_all_required`
- blocked/satisfied outcome != emitted transition record
- emitted transition record != reviewed-memory apply result

Why this remains the honest order:

- note policy is operator wording only
- blocked/satisfied outcome still belongs to status/unblock/capability surfaces
- transition emission still belongs to later transition-record machinery
- apply result still belongs to later reviewed-memory effect machinery

### 7. Support And Mirror Boundary

Never treat these as compatibility-note basis:

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

Even after this note decision, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session remains the honest boundary.

## Recommended Next Slice

- one emitted-transition-record contract only

That slice should:

- keep the shipped shared-ref-only planning-target truth unchanged
- stay smaller than reviewed-memory apply
- define the first exact emitted transition-record boundary above the already shipped transition-audit contract
- avoid reopening duplicated planning-target fields, aftercare notes, or cross-session counting

Why this remains the smallest honest next step:

- planning-target wording, normalization, cleanup, and post-cleanup aftercare are now all closed
- the next unresolved layer is transition emission, not planning-target compatibility
- widening directly into reviewed-memory apply, repeated-signal promotion, or cross-session counting would still overstate current machinery

## Open Questions

1. When emitted transition records reopen, should the first shipped surface be one aggregate-level read-only canonical transition record plus `task_log` mirror, or remain contract-only until later apply machinery exists?
