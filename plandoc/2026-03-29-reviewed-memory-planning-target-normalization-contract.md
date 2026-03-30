# 2026-03-29 Reviewed-Memory Planning-Target Normalization Contract

## Goal

Fix the first exact contract for the additive shared planning-target normalization pass that shipped one aggregate-level `reviewed_memory_planning_target_ref` and stayed smaller than blocked/satisfied outcome, emitted transition records, and reviewed-memory apply.

This document does not describe implemented reviewed-memory store, reviewed-memory apply, emitted transition records, repeated-signal promotion, cross-session counting, or user-level memory.

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
- the additive normalization round originally kept three duplicated target fields with the same narrowed label before cleanup opened
- current shipped meaning is already narrow:
  - one exact same-session aggregate may enter reviewed-memory draft planning only
  - that label does not mean blocked/satisfied outcome, emitted transition record, reviewed-memory apply, repeated-signal promotion, cross-session counting, or user-level memory
- current shipped shared planning-target ref is now:
  - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
  - `target_label = eligible_for_reviewed_memory_draft_planning_only`
  - `target_scope = same_session_exact_recurrence_aggregate_only`
  - `target_boundary = reviewed_memory_draft_planning_only`
  - `defined_at = aggregate.last_seen_at`
- the later cleanup-only pass has now removed:
  - `reviewed_memory_precondition_status.future_transition_target`
  - `reviewed_memory_unblock_contract.readiness_target`
  - `reviewed_memory_capability_status.readiness_target`
- current payloads now read planning-target meaning only from `reviewed_memory_planning_target_ref.target_label`
- current blocked truths remain:
  - `overall_status = blocked_all_required`
  - `unblock_status = blocked_all_required`
  - `capability_outcome = blocked_all_required`

## Decision

### 1. Ship One Additive Shared Planning-Target Ref

Choose `Option B`.

Why this is the current MVP-safe choice:

- it keeps one exact planning-only semantic target visible without pretending that blocked/satisfied outcome or transition/apply state has widened
- it avoids keeping three independent target strings as if they were separate semantic sources
- it remains smaller than emitted transition records, reviewed-memory apply, repeated-signal promotion, and cross-session counting

### 2. Exact Meaning Of The Shared Planning Target

The shared planning target means:

- one exact same-session aggregate above the current blocked layer
- one reviewed-memory draft planning only semantic target
- one shared semantic source for the same planning-only meaning currently duplicated across the three target fields

It does not mean:

- `blocked_all_required`
- `unblocked_all_required`
- emitted transition record
- reviewed-memory apply
- repeated-signal promotion
- cross-session counting
- user-level memory

### 3. Minimum Shipped Normalization Shape

The smallest honest shipped surface is:

- one additive read-only `reviewed_memory_planning_target_ref`
  - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
  - `target_label = eligible_for_reviewed_memory_draft_planning_only`
  - `target_scope = same_session_exact_recurrence_aggregate_only`
  - `target_boundary = reviewed_memory_draft_planning_only`
  - `defined_at = aggregate.last_seen_at`

Why this stays narrow:

- it names the shared planning-only target only
- it does not report blocked/satisfied outcome
- it does not emit transition identity
- it does not apply reviewed memory

### 4. Relationship To The Former Three Fields

The shipped normalization stayed additive-first.

Normalization-round rule:

- add one aggregate-level sibling `reviewed_memory_planning_target_ref`
- keep all three current target fields present in that same pass as exact derived echoes
- avoid changing blocked/satisfied, emitted-transition, or apply semantics

Cleanup-round rule:

- after the compatibility window, remove all three duplicated fields together:
  - `reviewed_memory_precondition_status.future_transition_target`
  - `reviewed_memory_unblock_contract.readiness_target`
  - `reviewed_memory_capability_status.readiness_target`
- keep `reviewed_memory_planning_target_ref` unchanged
- synchronize docs, payload, and tests in the same round
- current shipped truth now keeps only the shared ref as the planning-target source

### 5. Relationship To Status / Satisfaction / Transition / Apply

Keep the layers separate:

- shared planning-target ref != `blocked_all_required`
- shared planning-target ref != `unblocked_all_required`
- blocked/satisfied outcome != emitted transition record
- emitted transition record != reviewed-memory apply result

Why this remains the honest order:

- planning-target normalization only collapses one duplicated semantic target
- blocked/satisfied outcome still belongs to status/unblock/capability surfaces
- transition emitted still belongs to later transition-record machinery
- apply result still belongs to later reviewed-memory effect machinery

### 6. Support And Mirror Boundary

Never treat these as planning-target basis:

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

### 7. Cross-Session Boundary

Even after shared planning-target normalization, cross-session counting still stays closed.

It still needs:

- explicit cross-session local store
- stale-resolution rules
- cross-session conflict-repair rules
- operator-visible repair semantics above cross-session scope

So same-session remains the honest boundary.

## Recommended Next Implementation Slice

- one emitted-transition-record contract only

That slice should:

- keep the shipped read-only `reviewed_memory_planning_target_ref`
- keep the duplicated target strings removed
- define the first exact emitted transition-record boundary above the already shipped transition-audit contract
- avoid changing blocked/satisfied outcome, reviewed-memory apply/store state, or cross-session counting

Why this remains the smallest honest next step:

- the normalization and cleanup passes are already shipped
- the post-cleanup compatibility-note question is now also closed with no extra aftercare note
- the remaining gap is the later emitted-transition-record boundary, not planning-target wording
- widening directly into reviewed-memory apply, repeated-signal promotion, or cross-session counting would still overstate current machinery

## Open Questions

1. When emitted transition records reopen, should the first shipped surface be one aggregate-level read-only canonical transition record plus `task_log` mirror, or remain contract-only until later apply machinery exists?
