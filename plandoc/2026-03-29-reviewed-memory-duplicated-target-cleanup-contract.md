# 2026-03-29 Reviewed-Memory Duplicated-Target Cleanup Contract

## Goal

Fix the first exact cleanup-only contract for when and how the duplicated planning-target echo fields are removed after the shared planning-target ref has already shipped.

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
- current shipped shared ref is:
  - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
  - `target_label = eligible_for_reviewed_memory_draft_planning_only`
  - `target_scope = same_session_exact_recurrence_aggregate_only`
  - `target_boundary = reviewed_memory_draft_planning_only`
  - `defined_at = aggregate.last_seen_at`
- the duplicated planning-target echo fields have now been removed together:
  - `reviewed_memory_precondition_status.future_transition_target`
  - `reviewed_memory_unblock_contract.readiness_target`
  - `reviewed_memory_capability_status.readiness_target`
- current payloads now read planning-target meaning only from `reviewed_memory_planning_target_ref.target_label`
- current blocked truths remain:
  - `overall_status = blocked_all_required`
  - `unblock_status = blocked_all_required`
  - `capability_outcome = blocked_all_required`
- current contract objects still mean `contract exists` only and are not satisfaction by themselves

## Decision

### 1. Keep One Compatibility Release Window First

Choose `Option A`.

Why this is the current MVP-safe choice:

- the shared ref already carries the canonical planning-only meaning, so the remaining question is cleanup timing, not readiness widening
- one compatibility release window prevented a same-day additive-ref ship plus field-removal collapse from looking like hidden semantic churn
- it kept docs, payload, and tests on one stable coexisting truth before removal opened

### 2. Exact Meaning Of Cleanup-Only Pass

The cleanup-only pass means:

- keep the current shared ref as the canonical planning-target source
- remove the three duplicated target echo fields only after the compatibility window has passed
- reduce one duplicated structural layer without changing the planning-only meaning

It does not mean:

- `blocked_all_required` / `unblocked_all_required` widening
- emitted transition record
- reviewed-memory apply
- repeated-signal promotion
- cross-session counting
- user-level memory

### 3. Relationship To The Current Four Planning-Target Surfaces

Current shipped planning-target surface is:

- `reviewed_memory_planning_target_ref.target_label`

Current canonical rule:

- `reviewed_memory_planning_target_ref.target_label` is the canonical planning-target source
- the three earlier string fields are no longer shipped

Implemented cleanup rule:

- remove these three duplicated echo fields together:
  - `reviewed_memory_precondition_status.future_transition_target`
  - `reviewed_memory_unblock_contract.readiness_target`
  - `reviewed_memory_capability_status.readiness_target`
- keep `reviewed_memory_planning_target_ref` unchanged in that pass
- do not leave one or two echo fields behind
- do not replace one field early while others remain

### 4. Exact Compatibility Window And Migration Boundary

One compatibility release window was required first.

Define it as:

- the next explicit shipped round after the shared ref implementation round
- docs, payload, and tests must still expose the shared ref plus all three duplicated echoes unchanged in that round

Only after that window could the cleanup pass open.

When cleanup opened:

- remove all three duplicated echo fields together
- change docs, payload, and tests in the same round
- do not do payload-only cleanup
- do not do docs-only cleanup
- do not do staggered or partial removal
- require consumers to read `reviewed_memory_planning_target_ref.target_label` before the removal round

### 5. Minimum Future Cleanup Shape

The smallest honest cleanup shape is:

- keep `reviewed_memory_planning_target_ref` only as the remaining planning-target source
- remove all three duplicated echo fields together in one cleanup-only pass

Why this remains narrow:

- it changes structure only
- it does not change blocked/satisfied outcome
- it does not emit transition records
- it does not apply reviewed memory

### 6. Relationship To Status / Satisfaction / Transition / Apply

Keep the layers separate:

- duplicated-target cleanup != `blocked_all_required`
- duplicated-target cleanup != `unblocked_all_required`
- blocked/satisfied outcome != emitted transition record
- emitted transition record != reviewed-memory apply result

Why this remains the honest order:

- cleanup only removes redundant planning-target echoes
- blocked/satisfied outcome still belongs to status/unblock/capability surfaces
- transition emitted still belongs to later transition-record machinery
- apply result still belongs to later reviewed-memory effect machinery

### 7. Support And Mirror Boundary

Never treat these as cleanup basis:

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

Even after duplicated-target cleanup, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session remains the honest boundary.

## Recommended Next Implementation Slice

- one emitted-transition-record contract only

That slice should:

- keep `reviewed_memory_planning_target_ref` unchanged
- keep the three duplicated target echo fields removed
- define the first exact emitted transition-record boundary above the already shipped transition-audit contract
- avoid changing blocked/satisfied outcome, reviewed-memory apply/store state, or cross-session counting

Why this remains the smallest honest next step:

- structural redundancy is already gone
- the post-cleanup compatibility-note question is now also closed with no extra aftercare note
- the remaining question is later emitted-transition-record shape only
- widening directly into reviewed-memory apply, repeated-signal promotion, or cross-session counting would still overstate current machinery

## Open Questions

1. When emitted transition records reopen, should the first shipped surface be one aggregate-level read-only canonical transition record plus `task_log` mirror, or remain contract-only until later apply machinery exists?
