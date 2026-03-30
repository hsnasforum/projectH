# 2026-03-28 Reviewed-Memory Preconditions Contract

## Goal

Fix the exact preconditions that must exist before any current same-session aggregate can stop being `blocked_pending_reviewed_memory_boundary`.

This document does not describe implemented reviewed-memory store, reviewed-memory apply, repeated-signal promotion, user-level memory, or cross-session counting.

## Current Shipped Truth

- grounded-brief source messages remain the canonical content/source trace
- current source-message surfaces remain separate:
  - `session_local_candidate`
  - `durable_candidate`
  - `candidate_review_record`
  - `candidate_recurrence_key`
- current session payload may expose:
  - pending `review_queue_items`
  - same-session-only read-only `recurrence_aggregate_candidates`
- each current aggregate item may also expose:
  - `confidence_marker = same_session_exact_key_match`
  - `aggregate_promotion_marker`
    - `promotion_basis = same_session_exact_recurrence_aggregate`
    - `promotion_eligibility = blocked_pending_reviewed_memory_boundary`
    - `reviewed_memory_boundary = not_open`
  - `reviewed_memory_precondition_status`
    - `status_version = same_session_reviewed_memory_preconditions_v1`
    - `overall_status = blocked_all_required`
    - `all_required = true`
    - ordered fixed `preconditions`
    - `future_transition_target = eligible_for_reviewed_memory_draft`
    - `evaluated_at = last_seen_at`

## Decision

- Keep `Option A`.
- Every current same-session aggregate remains promotion-ineligible.
- Leaving `blocked_pending_reviewed_memory_boundary` requires all mandatory reviewed-memory preconditions below.
- Partial satisfaction is still blocked.
- Same-session unblock does not automatically open cross-session counting.

## Exact Mandatory Preconditions

All of the following are required before the blocked marker vocabulary can widen:

1. `reviewed_memory_boundary_defined`
2. `rollback_ready_reviewed_memory_effect`
3. `disable_ready_reviewed_memory_effect`
4. `conflict_visible_reviewed_memory_scope`
5. `operator_auditable_reviewed_memory_transition`

## Meaning Of Each Precondition

### 1. `reviewed_memory_boundary_defined`

- Means:
  - one explicit local reviewed-memory persistence/apply boundary exists above source-message and aggregate surfaces
  - one explicit reviewed scope boundary exists for that later layer
  - the first reviewed scope may stay narrow
- Does not mean:
  - source-message correction history became reviewed memory
  - current aggregate marker already became a reviewed-memory store
  - user-level memory is open

### 2. `rollback_ready_reviewed_memory_effect`

- Means:
  - a later reviewed-memory effect can be reversed by explicit local operator action
  - rollback targets the later reviewed-memory effect, not the underlying source-message traces
  - rollback leaves audit-visible trace
- Does not mean:
  - undoing explicit `corrected_text`
  - deleting `candidate_recurrence_key`
  - rewriting aggregate identity history

### 3. `disable_ready_reviewed_memory_effect`

- Means:
  - a later reviewed-memory effect can be stopped from future application without deleting its trace bundle
  - stop-apply is explicit and auditable
- Does not mean:
  - candidate deletion
  - approval reject
  - source-message review dismissal

### 4. `conflict_visible_reviewed_memory_scope`

- Means:
  - conflicting reviewed aggregates or reviewed signals are visible inside the same reviewed scope before any later apply
  - unresolved conflict can keep a later reviewed-memory candidate blocked
- Does not mean:
  - only same-source-message edit mismatch
  - only queue-level pending/reviewed distinction

### 5. `operator_auditable_reviewed_memory_transition`

- Means:
  - any later transition above the blocked marker leaves explicit operator-visible local trace
  - that trace identifies basis refs, state transition, and later rollback / disable / conflict outcomes
- Does not mean:
  - append-only `task_log` becomes the canonical reviewed-memory store
  - current source-message review traces are enough by themselves

## Boundary From Current Shipped Surfaces

- `candidate_review_record`
  - one source-message reviewed-but-not-applied trace
  - confidence support only
- `review_queue_items`
  - current source-message pending review queue
  - not aggregate identity and not reviewed memory
- `candidate_recurrence_key`
  - one source-message recurrence primitive
- `recurrence_aggregate_candidates`
  - one same-session cross-source grouping surface
  - still read-only and still non-promoting
- `aggregate_promotion_marker`
  - current blocked-state marker only
  - not a reviewed-memory candidate store
- future reviewed-memory layer
  - separate later layer above source-message and aggregate surfaces
  - requires all five mandatory preconditions
  - remains smaller than user-level memory

## Basis Boundary Above Current Aggregate

### Basis

- one current same-session `recurrence_aggregate_candidates` item
- exact aggregate identity from:
  - `candidate_family`
  - `key_scope`
  - `key_version`
  - `derivation_source`
  - `normalized_delta_fingerprint`
- distinct grounded-brief source-message anchors only
- current source-message version refs only when they still match:
  - `durable_candidate`
  - `candidate_review_record`

### Supporting Context Only

- `session_local_memory_signal`
- `superseded_reject_signal`
- `historical_save_identity_signal`
- approval-backed save support

### Never Basis

- `candidate_family` alone
- fixed statement text alone
- review acceptance alone
- queue presence alone
- approval-backed save alone
- historical adjunct alone
- task-log replay alone

## Minimum Future Unblock Shape

Current shipped behavior now also emits one blocked-only status object beside the blocked marker.

Current shipped read-only status shape:

- `reviewed_memory_precondition_status`
  - `status_version = same_session_reviewed_memory_preconditions_v1`
  - `overall_status = blocked_all_required`
  - `all_required = true`
  - `preconditions`
    - `reviewed_memory_boundary_defined`
    - `rollback_ready_reviewed_memory_effect`
    - `disable_ready_reviewed_memory_effect`
    - `conflict_visible_reviewed_memory_scope`
    - `operator_auditable_reviewed_memory_transition`
  - `future_transition_target = eligible_for_reviewed_memory_draft`
  - `evaluated_at = last_seen_at`

Rules:

- partial satisfaction may surface read-only only
- partial satisfaction must not apply memory
- partial satisfaction must not lift the current blocked marker by itself
- do not overwrite `aggregate_promotion_marker`
- do not create a reviewed-memory store in that slice

## Relationship To Cross-Session Counting

- Cross-session counting remains later.
- Same-session unblock and cross-session counting are related, but not the same decision.
- Cross-session counting needs this same precondition family plus extra cross-session work:
  - explicit local reviewed-memory/store choice across session reloads
  - stale or superseded-candidate handling across sessions
  - conflict visibility across sessions
  - operator-visible repair of mistaken cross-session grouping
- Therefore, same-session unblock does not automatically open cross-session counting.

## Confidence Marker And Threshold

- Current `confidence_marker = same_session_exact_key_match` remains enough for now.
- Reason:
  - it states only what the repo already proves
  - it does not pretend that review acceptance, save support, or blocked-marker presence already means reviewed memory
- A later second conservative level should be considered only after:
  - the read-only precondition-status surface exists
  - reviewed-memory boundary rules are explicit
  - the stronger label can be explained without overclaiming
- Default threshold stays `2` grounded briefs for now.
- Category-specific threshold tuning remains later than the current family and later than the reviewed-memory boundary.

## Recommended Next Implementation Slice

- Keep the shipped read-only aggregate-level `reviewed_memory_precondition_status` object fixed at overall blocked-only and do not widen it into per-precondition satisfaction or eligibility transition yet.

Why this is the smallest next slice:

- it preserves the current truthful local-only projection without inventing readiness the repo cannot actually evaluate
- it stays read-only and local-first
- it does not pretend reviewed-memory apply or repeated-signal promotion is ready
- it comes before repeated-signal promotion, reviewed-memory apply, and cross-session counting because those would still overclaim behavior the repo cannot yet roll back, disable, surface as conflict, or audit

## Open Questions

1. Should the first read-only `reviewed_memory_precondition_status` surface expose only one overall blocked state or per-precondition statuses as well?
2. Should the first reviewed-memory boundary keep one fixed narrow reviewed scope or expose a small scope enum when that later layer opens?
3. Which extra local-store and stale-resolution rules should be mandatory before cross-session counting opens?
4. Should the current fixed `confidence_marker = same_session_exact_key_match` remain enough until the precondition-status surface exists, or should a later second conservative level be added after that?
